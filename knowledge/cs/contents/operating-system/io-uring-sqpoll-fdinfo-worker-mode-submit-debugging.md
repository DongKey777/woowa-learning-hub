# io_uring SQPOLL fdinfo Matrix and Worker-Mode Submit-Side Debugging

> 한 줄 요약: `SqTail - SqHead`가 크다고 해서 같은 submit 병목은 아니다. 일반 ring에서는 submitter 태스크가 `SqHead`를 밀고, `SQPOLL` ring에서는 `io_uring-sq` 커널 스레드가 민다. `iou-wrk`는 그 뒤 async offload 신호일 뿐 submit-side stall의 1차 주인은 아니다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring IOWQ Affinity and Max-Workers Tuning Decision Guide](./io-uring-iowq-affinity-max-workers-decision-guide.md)
> - [io_uring SQ, CQ Basics](./io-uring-sq-cq-basics.md)
> - [/proc/<pid>/fdinfo, Epoll Runtime Debugging](./proc-pid-fdinfo-epoll-runtime-debugging.md)
> - [schedstat, /proc/<pid>/sched, Runtime Debugging](./schedstat-proc-sched-runtime-debugging.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)
> - [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: sqpoll observability matrix, io_uring sqpoll fdinfo, io_uring submit-side debugging, worker-mode ring, regular ring vs sqpoll, SqHead SqTail SQEs, SqThread, SqThreadCpu, io_uring-sq, iou-wrk, IORING_SQ_NEED_WAKEUP, io_uring_enter submit path, io_uring_submit sqpoll count, submitter tid sched, io_uring queue async work

## 핵심 개념

이 문서는 `CQ backlog`가 아니라 `submit-side` 정체를 구분하는 companion note다. 여기서 `regular worker-mode ring`은 `IORING_SETUP_SQPOLL` 없이 만든 일반 ring을 뜻한다. 이 경우 일부 작업이 나중에 `IOWQ`로 punt될 수는 있어도, `SqHead`를 실제로 전진시키는 1차 주체는 여전히 애플리케이션 submitter 태스크다.

- 공통 snapshot: `SqHead`, `SqTail`, `SQEs`는 두 모드 모두에서 submit backlog의 1차 단서다
- `SQPOLL` 전용 identity: `SqThread`, `SqThreadCpu`는 poll thread를 ring과 직접 연결하는 필드다
- async worker 주의: `iou-wrk`는 `io_uring_queue_async_work` 이후 completion 이전 단계를 설명할 뿐, submit queue owner를 대신하지 않는다

핵심 질문은 하나다. "지금 `SqHead`를 누가 움직여야 하는가?" 이 질문에 답하지 않고 scheduler 신호를 보면 regular ring에서도 `iou-wrk`를 뒤쫓고, SQPOLL ring에서도 잘못 submitter 사용자 스레드만 보게 된다.

## 관측 매트릭스

| 관측 축 | regular ring (`!IORING_SETUP_SQPOLL`) | `SQPOLL` ring |
|------|--------------------------------------|---------------|
| 누가 `SqHead`를 전진시키나 | submitter 태스크가 `io_uring_enter` 경로에서 민다 | `io_uring-sq` 커널 thread가 SQ를 polling하며 민다 |
| `fdinfo`에서 먼저 볼 것 | `SqHead`, `SqTail`, `SQEs` | `SqHead`, `SqTail`, `SQEs`, `SqThread`, `SqThreadCpu` |
| `SqThread`/`SqThreadCpu` 의미 | 없거나 `-1`이면 정상이다 | 유효한 PID/CPU면 해당 kthread를 바로 추적한다 |
| 첫 scheduler target | `io_uring_submit`/`io_uring_enter`를 호출하는 submitter TID | `fdinfo`의 `SqThread` PID |
| `SqTail - SqHead`가 오래 유지될 때 | submitter가 kernel entry를 못 하거나 scheduler에 밀린다 | SQ poll thread가 굶거나, 잘못된 CPU에 있거나, idle wakeup이 필요하다 |
| `iou-wrk`가 바빠 보일 때 의미 | submit은 이미 kernel에 들어갔고 이후 async offload가 밀릴 수 있다는 뜻이다 | 마찬가지다. `iou-wrk`는 SQ poll thread를 대체하지 않는다 |
| 가장 흔한 오판 | `SqHead` 정체를 바로 IOWQ 포화로 읽는다 | `io_uring_submit()` 반환값이나 worker 수만 보고 SQ thread starvation을 놓친다 |

읽는 감각:

- regular ring에서 `SqHead`가 안 움직이면 먼저 submitter thread의 scheduler 상태와 `io_uring_enter` 진입률을 본다
- `SQPOLL` ring에서 `SqHead`가 안 움직이면 먼저 `SqThread` PID의 `/proc/<pid>/sched`와 `SqThreadCpu` placement를 본다
- 어느 모드든 `SqHead`가 정상적으로 움직인 뒤에야 `iou-wrk` runqlat/off-CPU를 2차 문제로 본다

## 필드별 해석 포인트

### 1. `SqHead`, `SqTail`, `SQEs`는 공통 backlog 축이다

둘 다 먼저 보는 이유는 같다.

- `SqTail`은 userspace가 새 SQE를 얼마나 밀어 넣었는지 보여 준다
- `SqHead`는 kernel 쪽 submit 소비가 어디까지 갔는지 보여 준다
- `SQEs`는 시점상 backlog 크기를 빠르게 읽게 해 준다

따라서 `SqTail - SqHead`가 커졌다는 사실 자체는 두 모드 모두에서 중요하다. 다만 그 차이를 해소해야 하는 scheduler actor가 다르다.

### 2. `SqThread`, `SqThreadCpu`는 SQPOLL ring에서만 ring owner를 드러낸다

`fdinfo`의 `SqThread`, `SqThreadCpu`는 `SQPOLL`을 쓸 때 submit-side triage를 훨씬 짧게 만든다.

- `SqThread`: 해당 ring을 대신 submit하는 `io_uring-sq` 커널 thread PID
- `SqThreadCpu`: snapshot 시점에 그 thread가 관측된 CPU

주의:

- `SqThreadCpu`는 placement 힌트이지 영구 affinity 자체는 아니다
- `IORING_SETUP_SQ_AFF`를 쓴 경우에는 기대 CPU가 더 안정적이지만, cpuset 변경이나 일반 스케줄링 상황에서는 이동할 수 있다
- regular ring에서 `SqThread`가 없거나 `-1`처럼 보이는 것은 이상 징후가 아니라 "submit owner가 userspace다"라는 뜻이다

### 3. `io_uring_submit()` 반환값은 SQPOLL triage의 주 신호가 아니다

`io_uring_submit(3)` man page 기준으로 `SQPOLL`에서는 반환값이 실제 submit 완료 개수보다 크게 보일 수 있다. 그래서 submit-side stall을 볼 때는 반환 카운트보다 다음을 우선한다.

- `fdinfo`의 `SqHead` delta
- `SqThread`의 scheduler 상태
- 필요하면 userspace가 보는 SQ ring flags의 `IORING_SQ_NEED_WAKEUP`

즉 `submit()`이 양수를 돌려줬다고 해서 poll thread가 실제로 backlog를 충분히 소화했다고 단정하면 안 된다.

### 4. `IORING_SQ_NEED_WAKEUP`은 fdinfo 밖에 있다

`SQPOLL`에서 poll thread가 idle timeout 뒤 잠들면 kernel은 SQ ring flags에 `IORING_SQ_NEED_WAKEUP`를 세운다. 이 비트는 `fdinfo` 필드가 아니라 shared SQ ring 상태라서, 운영 triage에서는 다음처럼 읽는 편이 안전하다.

- `fdinfo`는 "어느 `SqThread`를 봐야 하는가"를 알려 준다
- ring flags는 "그 thread가 지금 explicit wakeup이 필요한가"를 알려 준다
- 둘을 함께 못 본다면, `SqHead` flat + 한가하거나 sleeping인 `SqThread` 조합으로 간접 추론한다

## 디버깅 순서

### 1. 먼저 ring 모드를 고정한다

```bash
ls -l /proc/<pid>/fd | rg 'anon_inode:\\[io_uring\\]'
cat /proc/<pid>/fdinfo/<ring-fd>
```

질문:

- `SqThread`가 유효한 PID인가
- `SqTail - SqHead`가 지금도 큰가
- `SQEs`가 backlog와 같은 방향으로 커졌는가

### 2. regular ring이면 submitter TID를 본다

```bash
cat /proc/<submit-tid>/sched
sudo perf stat -e syscalls:sys_enter_io_uring_enter -p <submit-pid> -- sleep 10
sudo perf sched timehist -p <submit-pid> -- sleep 10
```

이때의 해석:

- `SqTail - SqHead`가 큰데 `io_uring_enter` 진입률이 낮다
  - submitter가 충분히 kernel entry를 못 하고 있을 수 있다
- submitter의 `/proc/<tid>/sched`에서 run delay가 크다
  - submit loop 자체가 scheduler에 밀린다
- `iou-wrk`가 조용하다
  - 오히려 submit 이전 단계 문제라는 뜻일 수 있다

### 3. SQPOLL ring이면 `SqThread`를 본다

```bash
cat /proc/<sqthread-pid>/sched
ps -o pid,psr,comm -p <sqthread-pid>
sudo perf sched timehist -p <sqthread-pid> -- sleep 10
```

이때의 해석:

- `SqTail - SqHead`가 큰데 `SqThread` run queue 지연이 높다
  - poll thread starvation 또는 잘못된 CPU placement 가능성이 높다
- `SqThreadCpu`가 hot CPU에 고정돼 있고 migration이 거의 없다
  - `SQ_AFF` 또는 affinity 설계가 나쁘게 묶였을 수 있다
- `SqThread`는 멀쩡한데 backlog가 간헐적으로만 튄다
  - idle/wakeup 경계나 batching 정책, `IORING_SQ_NEED_WAKEUP` 처리 여부를 본다

### 4. `iou-wrk`는 submit-owner가 아니라 2차 분기다

```bash
ps -eLo pid,tid,psr,comm | rg 'iou-wrk|io_uring-sq'
sudo perf stat -e io_uring:io_uring_queue_async_work,io_uring:io_uring_complete -a -- sleep 10
```

판단 기준:

- `SqHead`가 이미 잘 움직이고 `io_uring_queue_async_work`만 늘어난다
  - 이제는 submit stall이 아니라 async offload 이후 병목이다
- `iou-wrk` runqlat/off-CPU가 길다
  - [io_uring IOWQ Affinity and Max-Workers Tuning Decision Guide](./io-uring-iowq-affinity-max-workers-decision-guide.md)로 넘어간다

## 실전 시나리오

### 시나리오 1: `SQEs`는 쌓이는데 `iou-wrk`는 조용하다

해석:

- regular ring이면 submitter가 kernel entry를 충분히 못 하고 있는 그림이 더 가깝다
- SQPOLL ring이면 `SqThread` starvation 또는 wakeup 문제를 더 먼저 본다

즉 `worker가 안 바쁘다 = 문제 없다`가 아니다. submit owner가 아직 일을 못 받아 간 것일 수 있다.

### 시나리오 2: `SqThreadCpu`가 특정 바쁜 코어에 고정돼 있다

해석:

- SQ poll thread가 noisy CPU와 경쟁할 수 있다
- 이 경우 `SqTail - SqHead`가 completion 병목처럼 보이더라도 실제로는 submit-side queueing이다

이때는 [CPU Affinity, IRQ Affinity, Core Locality](./cpu-affinity-irq-affinity-core-locality.md)와 [CPU Migration, Load Balancing, Locality Debugging](./cpu-migration-load-balancing-locality-debugging.md)을 같이 보는 편이 맞다.

### 시나리오 3: latency는 큰데 `SqHead`는 꾸준히 전진한다

해석:

- submit-side stall 근거는 약하다
- `io_uring_queue_async_work`, `io_uring_complete`, `iou-wrk` scheduler pressure로 넘어가야 한다

즉 이 문서의 매트릭스는 "submit actor를 틀리게 잡지 않기 위한 1차 분기"다. 그 다음 단계는 completion 관측이나 IOWQ tuning 문서가 맡는다.

## 꼬리질문

> Q: regular ring에서도 `iou-wrk`를 보면 submit 병목을 알 수 있나요?
> 핵심: 직접적으로는 어렵다. `iou-wrk`는 async offload 이후 신호라서 `SqHead`를 누가 밀고 있는지부터 분리해야 한다.

> Q: SQPOLL ring에서 `SqThreadCpu`가 보이면 그 CPU에 영구 고정된 건가요?
> 핵심: 아니다. snapshot 시점의 CPU 힌트다. `SQ_AFF`를 쓴 경우 더 안정적일 뿐, 항상 불변은 아니다.

> Q: `io_uring_submit()`가 양수를 반환했는데도 submit이 밀릴 수 있나요?
> 핵심: SQPOLL에서는 그럴 수 있다. 반환값보다 `SqHead` delta와 `SqThread` 상태를 더 믿는 편이 안전하다.

## 참고 자료

- [`io_uring_setup(2)`](https://man7.org/linux/man-pages/man2/io_uring_setup.2.html)
- [`io_uring_submit(3)`](https://man7.org/linux/man-pages/man3/io_uring_submit.3.html)
- [`proc_pid_fdinfo(5)`](https://man7.org/linux/man-pages/man5/proc_pid_fdinfo.5.html)
- [`include/trace/events/io_uring.h`](https://github.com/torvalds/linux/blob/master/include/trace/events/io_uring.h)

## 한 줄 정리

submit-side `io_uring` triage의 핵심은 backlog 자체가 아니라 `SqHead` owner를 먼저 맞히는 것이다. regular ring은 submitter 태스크, `SQPOLL` ring은 `io_uring-sq`, `iou-wrk`는 그 다음 단계다.
