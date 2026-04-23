# io_uring IOWQ Affinity and Max-Workers Tuning Decision Guide

> 한 줄 요약: `IOWQ` 포화가 확인된 뒤에는 먼저 `iou-wrk`가 CPU/NUMA placement 때문에 밀리는지, worker ceiling 때문에 밀리는지 나눠야 하고, 전자면 affinity/cpuset을, 후자면 `max-workers`를 건드려야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [io_uring CQ Overflow, Multishot, Provided Buffers, IOWQ Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [Cpuset Isolation, Noisy Neighbors](./cpuset-isolation-noisy-neighbors.md)
> - [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [NUMA First-Touch, Remote Memory, Locality Debugging](./numa-first-touch-remote-memory-locality-debugging.md)
> - [AutoNUMA vs Manual Locality Trade-offs](./autonuma-vs-manual-locality-tradeoffs.md)
> - [NUMA Production Debugging](./numa-production-debugging.md)

> retrieval-anchor-keywords: io_uring iowq tuning, iowq tuning guide, iowq affinity, iowq max workers, io_uring_register_iowq_aff, io_uring_register_iowq_max_workers, IORING_REGISTER_IOWQ_AFF, IORING_REGISTER_IOWQ_MAX_WORKERS, iou-wrk saturation, iou-wrk runqlat, bounded worker, unbounded worker, per numa node worker count, cpuset.cpus.effective, cpuset.mems.effective, iowq cpuset, iowq numa placement, remote memory tail latency, worker ceiling tuning

## 핵심 개념

이 문서는 `IOWQ saturation`이 이미 확인된 뒤의 선택지를 정리한다. 아직 CQ backlog, eventfd coalescing 착시, 단순 downstream device saturation과 구분하지 못했다면 [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)부터 다시 보는 편이 맞다.

- `IOWQ affinity`: `io_uring_register(2)`의 `IORING_REGISTER_IOWQ_AFF`로 async worker CPU mask를 명시적으로 바꾸는 조정이다. 기본값은 parent task의 CPU mask 상속이다.
- `max-workers`: `IORING_REGISTER_IOWQ_MAX_WORKERS`로 bounded/unbounded worker 최대치를 per-NUMA-node 기준으로 바꾸는 조정이다. 값은 `unsigned int[2]`로 전달하며 index 0은 bounded, index 1은 unbounded이고, 값 `0`은 현재 설정 조회 의미로 쓸 수 있다.
- `cpuset envelope`: `cpuset.cpus.effective`와 `cpuset.mems.effective`가 worker가 실제로 움직일 수 있는 공간 경계다.
- `NUMA locality`: worker가 CPU를 어디서 받는지뿐 아니라, completion 후속 처리와 page cache/buffer가 어느 node에 있는지가 tail latency를 결정한다.

왜 중요한가:

- `IOWQ` 포화는 "worker가 너무 적다"와 "worker가 잘못된 곳에서 돈다"가 같은 증상으로 보일 수 있다
- `max-workers`를 올려도 CPU/NUMA placement가 틀리면 run queue와 remote memory만 더 커질 수 있다
- 반대로 affinity만 좁혀도 실제 병목이 blocking wait라면 queue 유입 속도를 못 따라간다

## 먼저 고를 축

| 관측 신호 | 더 가까운 원인 | 먼저 볼 조정 |
|------|---------------|-------------|
| `iou-wrk` runqlat 상승, CPU migration 증가, remote memory 증가 | CPU/NUMA placement가 틀렸다 | `cpuset` 정렬, 그다음 `IOWQ_AFF` |
| `io_uring_queue_async_work`가 `io_uring_complete`보다 빨리 늘고, worker off-CPU가 길며 target CPU는 아직 여유가 있다 | worker ceiling이 낮거나 legitimate blocking I/O가 많다 | `MAX_WORKERS` |
| `CQEs`와 `CqOverflowList`가 높다 | completion consumer가 늦다 | 둘 다 아니다. CQ drain 문제다 |
| `cpuset.mems`가 넓거나 first-touch가 다른 node에 몰렸다 | affinity만으로는 고칠 수 없는 memory placement 문제다 | `cpuset.mems`, warm-up, NUMA 배치 |

핵심은 "worker가 CPU를 못 받는가"와 "worker 수가 모자라는가"를 분리하는 것이다.

## 1. 포화 확정 전에는 knob부터 돌리지 않는다

다음이 확인되지 않았다면 tuning부터 시작하면 안 된다.

- `fdinfo`에서 CQ backlog가 주범이 아님
- `perf`에서 `io_uring_queue_async_work`와 `io_uring_complete` 관계가 실제로 `IOWQ` 정체를 가리킴
- `perf sched`, `runqlat`, `offcputime`로 `iou-wrk`가 CPU 대기인지 blocking wait인지 분리됨
- 같은 부하에서 반복 재현됨

실전에서는 아래 4개를 한 묶음으로 저장해 두는 편이 좋다.

```bash
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
sudo perf stat -e io_uring:io_uring_queue_async_work,io_uring:io_uring_complete -a -- sleep 10
sudo perf sched timehist -p <iou-wrk-pid>
```

## 2. `IOWQ_AFF`는 worker가 "어디서" CPU를 받을지 틀릴 때 쓴다

`IOWQ_AFF`는 concurrency를 늘리는 knob가 아니다. inherited mask가 서비스 의도와 다를 때 worker placement를 다듬는 knob다.

먼저 떠올릴 상황:

- ring creator가 넓은 CPU mask를 가지고 있어 `iou-wrk`가 hot path와 다른 socket까지 떠돈다
- event loop와 `iou-wrk`가 같은 core set에서 경쟁해 `runqlat`이 커진다
- worker migration이 많고 completion 후속 처리 버퍼가 다른 NUMA node에 있어 remote memory tax가 보인다
- cpuset은 충분히 넓지만, 그 안에서 foreground와 async worker를 다른 core subset으로 나누고 싶다

바로 쓰지 말아야 할 상황:

- worker 대부분이 storage/socket/lock wait로 off-CPU 상태다
- `cpuset.mems`가 넓거나 first-touch가 틀려 CPU pinning만으로는 memory locality를 못 맞춘다
- parent mask 자체가 이미 node-aligned이고 안정적이라 상속만으로 충분하다

운영 감각:

- `IOWQ_AFF`는 잘못된 CPU 상속을 바로잡는 용도다
- `cpuset`이 잘못됐는데 affinity만 좁히면 compute placement만 좋아지고 memory는 remote로 남을 수 있다
- affinity를 너무 좁히면 locality는 좋아져도 burst 흡수력이 줄고 hot core가 생긴다

## 3. `MAX_WORKERS`는 worker ceiling이 실제 병목일 때 쓴다

`MAX_WORKERS`는 "worker가 너무 적어서 queue가 밀린다"는 증거가 있을 때만 의미가 있다. 이 ceiling도 per-NUMA-node로 적용된다는 점을 같이 봐야 한다. 기본값도 이미 bounded는 SQ ring 크기와 CPU 수의 함수고, unbounded는 `RLIMIT_NPROC` 제약을 받는다. 따라서 무작정 올리면 대개 증상만 다른 곳으로 옮긴다.

올릴 쪽에 가까운 신호:

- `io_uring_queue_async_work`가 계속 누적되는데 `iou-wrk`는 주로 blocking I/O에서 잠든다
- target cpuset 안의 CPU와 device queue depth에 아직 headroom이 있다
- worker를 더 돌려도 remote memory나 migration churn이 주된 비용으로 보이지 않는다

내릴 쪽에 가까운 신호:

- worker 수가 늘수록 run queue와 cache/LLC 간섭이 먼저 커진다
- 같은 socket 안에서 foreground tail latency가 더 나빠진다
- device나 downstream lock이 이미 포화라 더 많은 worker가 throughput을 못 올린다

특히 조심할 점:

- bounded 값을 올리는 것은 "병렬로 처리 가능한 정상적인 blocking offload"가 더 필요한지 확인한 뒤에만 한다
- unbounded 값을 올리는 것은 더 위험하다. 오래 막히는 경로를 숨기거나 `RLIMIT_NPROC` 근처에서 다른 태스크까지 압박할 수 있다
- 값 `0, 0`으로 현재 ceiling을 읽어 baseline을 먼저 적어 두는 습관이 안전하다

## 4. cpuset과 NUMA trade-off를 먼저 정렬해야 한다

`IOWQ_AFF`와 `MAX_WORKERS`는 둘 다 `cpuset`과 NUMA envelope 바깥의 현실을 무시할 수 없다.

- `cpuset.cpus.effective`가 좁으면 max-workers를 올려도 결국 같은 코어 안에서 queueing만 커진다
- `cpuset.mems.effective`가 넓거나 first-touch가 다른 node에 몰리면 affinity를 잘 맞춰도 remote memory가 남는다
- worker를 cross-node로 넓히면 burst 흡수력은 오르지만 cache locality, page cache locality, noisy-neighbor 간섭이 나빠질 수 있다
- node-aligned 배치는 p99를 안정화하지만, 너무 좁히면 background flush나 burst traffic을 흡수할 완충이 줄어든다

현실적인 선택 순서:

1. `cpuset.cpus.effective`와 `cpuset.mems.effective`가 같은 NUMA 의도를 가지는지 본다
2. `numastat -p <pid>`와 `/proc/<pid>/numa_maps`로 remote memory가 이미 굳어졌는지 본다
3. 그다음에야 `IOWQ_AFF`로 CPU subset을 좁힐지, `MAX_WORKERS`로 concurrency ceiling을 바꿀지 고른다

즉 affinity는 placement 미세조정이고, cpuset/NUMA는 placement 경계다.

## 5. 실전 적용 순서

### 시나리오 1: `iou-wrk` runqlat이 길고 migration이 많다

가능한 해석:

- worker가 foreground와 같은 코어에 섞여 있다
- ring creator의 inherited mask가 너무 넓다
- completion 후속 처리 데이터와 worker CPU가 다른 node에 있다

대응 감각:

- 먼저 `cpuset`과 memory node 정렬을 확인한다
- 그다음 `IOWQ_AFF`로 worker를 node-aligned subset에 붙인다
- worker 수를 늘리기 전에 migration과 remote memory가 줄어드는지 본다

### 시나리오 2: worker는 mostly off-CPU인데 async queue backlog가 는다

가능한 해석:

- concurrency ceiling이 실제 병목이다
- bounded 또는 unbounded bucket 하나가 너무 낮다
- underlying I/O는 막히지만 CPU는 아직 남아 있다

대응 감각:

- 현재 bounded/unbounded ceiling을 먼저 읽는다
- 어느 bucket이 pressure를 받는지 구분한 뒤 작은 폭으로만 조정한다
- 조정 뒤에는 `queue_async_work`, `io_uring_complete`, p99, runqlat을 같이 비교한다

### 시나리오 3: max-workers를 올렸더니 평균은 오르지만 p99와 remote memory가 나빠진다

가능한 해석:

- concurrency 증가는 있었지만 locality 비용을 같이 키웠다
- 같은 cpuset/socket 안에서 foreground와 `iou-wrk` 간섭이 심해졌다
- worker 증설이 device saturation을 해결한 것이 아니라 CPU/NUMA 교란을 키웠다

대응 감각:

- worker ceiling을 되돌리거나 줄인다
- node-aligned cpuset 또는 `IOWQ_AFF`로 간섭 범위를 다시 제한한다
- 평균 throughput보다 tail predictability가 중요한 서비스인지 우선순위를 다시 정한다

## 코드로 보기

### worker placement와 locality 확인

```bash
ps -eLo pid,tid,psr,comm | rg 'iou-wrk'
taskset -cp <submitter-pid>
cat /sys/fs/cgroup/<cgroup>/cpuset.cpus.effective
cat /sys/fs/cgroup/<cgroup>/cpuset.mems.effective
numastat -p <pid>
cat /proc/<pid>/numa_maps | head -n 40
```

### queue pressure와 scheduler pressure 확인

```bash
sudo perf stat \
  -e io_uring:io_uring_queue_async_work,io_uring:io_uring_complete \
  -a -- sleep 10

sudo perf sched timehist -p <iou-wrk-pid>
sudo offcputime-bpfcc -p <iou-wrk-pid> 10
sudo runqlat-bpfcc -P 10
```

### mental model

```text
confirmed IOWQ saturation
  ->
is it runnable pressure or blocking pressure?

runnable pressure
  -> fix cpuset / NUMA / IOWQ_AFF first

blocking pressure with spare headroom
  -> consider MAX_WORKERS

wrong knob
  -> more workers on the wrong node
  -> higher p99 and more remote memory
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| parent mask 상속 유지 | 운영 단순성이 높다 | worker placement가 거칠 수 있다 | creator CPU mask가 이미 의도와 맞을 때 |
| `IOWQ_AFF`로 subset 고정 | migration과 간섭을 줄여 locality를 높인다 | burst 흡수력과 유연성이 줄 수 있다 | hot path와 async worker를 분리하고 싶을 때 |
| bounded `max-workers` 증가 | 정상적인 blocking offload 병렬성을 늘린다 | CPU/LLC 경쟁과 downstream 포화를 키울 수 있다 | CPU 여유가 있고 bounded backlog가 분명할 때 |
| unbounded `max-workers` 증가 | 긴 blocking 경로의 대기를 줄일 수 있다 | runaway worker, `RLIMIT_NPROC` 압박, 원인 은폐 위험이 크다 | 정당한 long-blocking path가 많고 다른 증거가 맞을 때 |
| node-aligned cpuset + 보수적 worker 수 | p99 predictability가 좋다 | host 전체 throughput과 burst 흡수가 줄 수 있다 | latency-sensitive API, RPC, DB hot path |

## 꼬리질문

> Q: `IOWQ_AFF`를 먼저 쓰면 cpuset 문제도 같이 해결되나요?
> 핵심: 아니다. affinity는 CPU subset 미세조정이고, `cpuset.mems`나 first-touch가 틀리면 memory locality는 그대로일 수 있다.

> Q: `MAX_WORKERS`를 올리면 포화가 빨리 풀리지 않나요?
> 핵심: CPU/NUMA placement가 틀렸거나 downstream device가 이미 포화면 worker만 더 많아지고 tail latency가 악화될 수 있다.

> Q: bounded와 unbounded를 둘 다 같이 올려야 하나요?
> 핵심: 보통 아니다. pressure를 받는 bucket을 먼저 구분하고 한쪽만 작은 폭으로 조정하는 편이 안전하다.

## 참고 자료

- [`io_uring_register(2)`](https://man7.org/linux/man-pages/man2/io_uring_register.2.html)
- [`io_uring_register_iowq_aff(3)`](https://man7.org/linux/man-pages/man3/io_uring_register_iowq_aff.3.html)
- [`io_uring_register_iowq_max_workers(3)`](https://man7.org/linux/man-pages/man3/io_uring_register_iowq_max_workers.3.html)

## 한 줄 정리

`IOWQ` 포화 뒤의 첫 질문은 "worker가 적은가"가 아니라 "worker가 잘못된 곳에서 돌고 있는가"다. placement 문제면 `IOWQ_AFF`와 cpuset/NUMA를, ceiling 문제면 `MAX_WORKERS`를 택해야 한다.
