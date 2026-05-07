---
schema_version: 3
title: io_uring Provided Buffers Fixed Buffers Memory Pressure
concept_id: operating-system/io-uring-provided-buffers-fixed-buffers-memory-pressure
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
review_feedback_tags:
- io-uring-provided
- buffers-fixed-buffers
- memory-pressure
- receive-side-admission
aliases:
- io_uring provided buffers fixed buffers
- receive-side admission control
- fixed buffer pinning memory pressure
- low-water resume-water
- ENOBUFS reclaim stall OOM
- cgroup memory cap io_uring
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md
- contents/operating-system/io-uring-multishot-cancel-rearm-drain-shutdown.md
- contents/operating-system/io-uring-provided-buffer-group-sharding-size-cpu-numa.md
- contents/operating-system/io-uring-provided-buffer-bid-leak-enobufs-diagnostics.md
- contents/operating-system/io-uring-send-bundle-zerocopy-fixed-buffer-completion-accounting.md
- contents/operating-system/memory-high-vs-memory-max-cgroup-behavior.md
symptoms:
- sustained recv load에서 provided buffer pool이 부족해 -ENOBUFS, reclaim stall, OOM이 이어진다.
- fixed buffer pinning과 cgroup memory limit을 계산하지 않아 memory pressure가 누적된다.
- low-water와 resume-water 없이 receive admission을 열어 buffer exhaustion을 뒤늦게 본다.
expected_queries:
- io_uring provided buffer ring은 allocator 최적화가 아니라 receive-side admission control이야?
- fixed buffer pinning과 cgroup memory cap을 함께 계산해야 하는 이유는?
- low-water resume-water 없이 운영하면 ENOBUFS reclaim stall OOM이 이어질 수 있어?
- multishot recv와 provided buffer pool sizing을 어떻게 잡아야 해?
contextual_chunk_prefix: |
  이 문서는 sustained receive load에서 provided buffer ring이 단순 allocator 최적화가 아니라
  receive-side admission control이라는 점을 설명한다. fixed buffer pinning, cgroup memory cap,
  low-water/resume-water 없이 운영하면 ENOBUFS, reclaim stall, OOM이 이어진다.
---
# io_uring Provided Buffer Rings, Fixed Buffers, Memory Pressure

> 한 줄 요약: sustained receive load에서 `io_uring` provided buffer ring은 단순한 allocator 최적화가 아니라 **receive-side admission control**이다. multishot recv는 이 풀에서만 버퍼를 가져가므로, fixed buffer pinning과 cgroup 메모리 상한을 같이 계산한 low-water / resume-water 없이 운영하면 `-ENOBUFS`, reclaim stall, OOM이 한 줄로 이어진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [io_uring CQ Overflow, Multishot, Provided Buffers, IOWQ Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring Provided Buffer Group Sharding by Payload Size, CPU Shard, NUMA Node](./io-uring-provided-buffer-group-sharding-size-cpu-numa.md)
> - [io_uring Provided-Buffer Bid Leak, ENOBUFS, Recycle Diagnostics](./io-uring-provided-buffer-bid-leak-enobufs-diagnostics.md)
> - [io_uring send bundle, zerocopy notification, fixed-buffer completion accounting](./io-uring-send-bundle-zerocopy-fixed-buffer-completion-accounting.md)
> - [io_uring Operational Hazards, Registered Resources, SQPOLL](./io-uring-operational-hazards-registered-resources-sqpoll.md)
> - [io_uring Provided Buffer Exhaustion Observability Playbook](./io-uring-provided-buffer-exhaustion-observability-playbook.md)
> - [io_uring Completion Observability Playbook](./io-uring-completion-observability-playbook.md)
> - [Socket Buffer Autotuning, Backpressure](./socket-buffer-autotuning-backpressure.md)
> - [memory.high vs memory.max, Cgroup Behavior](./memory-high-vs-memory-max-cgroup-behavior.md)
> - [memory.low, memory.min, Reclaim Protection](./memory-low-min-reclaim-protection.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)

> retrieval-anchor-keywords: io_uring provided buffer ring, provided buffers under memory pressure, fixed buffers, registered buffers, RLIMIT_MEMLOCK, memory.high, memory.max, memory.current, low-water mark, resume-water mark, recv multishot, IOSQE_BUFFER_SELECT, IORING_CQE_F_BUFFER, ENOBUFS, terminal ENOBUFS CQE, buffer group, bgid, bid, buffer id leak, io_uring_buf_ring_available, IORING_REGISTER_PBUF_STATUS, IORING_RECVSEND_BUNDLE, buffer recycle lag, socket receive memory, parser backlog, receive headroom, memory.events.local, memory.pressure, provided buffer exhaustion observability, CQ backlog ratio, ss -m skmem, buffer group sharding, bgid sharding, size class buffer group, per shard buffer group, per NUMA buffer group

## 핵심 개념

provided buffer ring과 fixed buffers는 둘 다 "`io_uring`이 미리 잡아 두는 메모리"처럼 보여서 한데 묶어 생각하기 쉽다. 하지만 receive-heavy 서비스에서는 역할이 다르다.

- `provided buffer ring`: recv/read가 **실제로 데이터를 받을 시점**에 커널이 골라 쓰는 버퍼 풀이다
- `fixed buffers`: `IORING_REGISTER_BUFFERS`로 미리 등록한 장기 참조 버퍼 집합이다
- `memory cap`: `RLIMIT_MEMLOCK`, `memory.high`, `memory.max`, socket receive memory, 앱 내부 큐 상한처럼 서로 다른 경계를 뜻한다
- `low-water mark`: free provided buffer가 위험 수위 아래로 내려가기 전에 intake를 늦추는 앱 내부 규칙이다

왜 중요한가:

- `io_uring_prep_recv_multishot()`은 `len=0`과 `IOSQE_BUFFER_SELECT`를 요구하므로, multishot recv의 실제 수신 버퍼는 provided buffer pool에서만 나온다
- fixed buffers는 별도 등록 자원이라, receive path가 provided buffer를 쓴다고 해서 고정 버퍼 비용이 사라지지 않는다
- sustained load에서는 "버퍼 개수 부족"보다 먼저 `memory.high` reclaim, socket buffer 누적, app queue 지연이 p99를 흔든다
- low-water를 단순히 "남은 bid 개수"로만 잡으면 CQ lag, bundle burst, parser backlog를 놓쳐서 `-ENOBUFS`를 늦게 본다

## 깊이 들어가기

### 1. multishot recv에서 provided buffers는 선택 옵션이 아니라 receive-side 예산이다

공식 liburing man page 기준으로 `io_uring_prep_recv_multishot()`은:

- `len=0`
- `IOSQE_BUFFER_SELECT` 필수
- `MSG_WAITALL` 금지

를 요구한다. 즉 multishot recv는 "미리 정한 버퍼 하나"가 아니라, **CQE마다 provided buffer pool에서 새 버퍼를 가져가는 모델**이다.

이 성질 때문에 provided buffer ring은 사실상 receive concurrency cap이 된다.

- pool에 free bid가 충분하면 intake를 계속 받을 수 있다
- recycle이 intake를 못 따라가면 free bid가 줄어든다
- 바닥나면 multishot generation은 `-ENOBUFS`를 내고 끝날 수 있다

좋은 점도 있다.

- 요청 수보다 버퍼 수를 적게 두어도 된다
- readiness 모델처럼 "모든 연결마다 미리 recv 버퍼를 붙여 두는" 메모리 낭비를 줄인다

하지만 운영 해석은 바뀐다.

- free provided buffer 수는 단순 상태값이 아니라 **남은 수신 headroom**이다
- free bid가 줄어드는 속도는 parser/app queue가 payload를 얼마나 오래 잡고 있는지의 간접 지표다
- `-ENOBUFS`는 "커널이 이상하다"가 아니라 **앱이 recycle보다 intake를 더 오래 유지했다**는 뜻에 가깝다

### 2. fixed buffers는 provided pool의 대체재가 아니라 별도 장기 부채다

`IORING_REGISTER_BUFFERS`로 등록한 fixed buffers는:

- 커널이 장기 참조할 수 있게 잡아 두는 버퍼다
- `RLIMIT_MEMLOCK`에 걸릴 수 있다
- unregister/update를 호출해도 inflight request가 끝날 때까지 바로 풀리지 않을 수 있다

즉 fixed buffers는 "필요할 때마다 다시 얻는 버퍼"가 아니라, 서비스 시작부터 메모리 예산을 먹고 들어가는 **장기 debt**다.

provided buffers와의 관계를 정리하면:

| 항목 | provided buffer ring | fixed buffers |
|------|----------------------|---------------|
| 주 용도 | recv/read 시점에 buffer selection | 고정 인덱스 기반 fast path |
| lifetime 기준 | CQE 후 앱이 recycle할 때까지 | unregister/update 이후에도 inflight가 끝날 때까지 유지 가능 |
| 운영 비용 | free bid 고갈, recycle lag | memlock 소진, 장기 pinning |
| receive multishot와의 관계 | 사실상 필수 | 같은 request의 수신 버퍼 역할이 아니라 별도 자원 |

실무 감각:

- multishot recv hot path는 provided ring으로 다룬다
- fixed buffers는 send/read/write 같은 **안정된 크기와 수명의 fast path**에만 최소량 등록한다
- "어차피 fixed buffers가 있으니 provided ring은 공격적으로 크게 잡아도 된다"는 사고가 가장 위험하다

둘은 서로 상쇄되지 않는다. 같은 프로세스와 같은 cgroup 안에서 **예산이 누적**된다.

### 3. memory cap은 하나가 아니라 여러 층이다

provided buffers under memory pressure를 이해할 때, cap을 하나의 숫자로 보면 안 된다.

| 경계 | 실제로 막는 것 | receive path에서 보이는 현상 |
|------|----------------|------------------------------|
| `RLIMIT_MEMLOCK` | fixed buffer 등록 같은 장기 pinning | ring은 살아 있어도 새 fixed buffer 등록/교체가 실패한다 |
| `memory.high` | reclaim / throttling 압박 | free bid가 아직 남아도 p99와 PSI가 먼저 튄다 |
| `memory.max` | 하드 cgroup 상한 | payload retention이 길면 결국 OOM으로 간다 |
| socket receive memory | 커널 쪽 수신 대기열 | 앱이 늦게 throttle하면 커널 큐까지 같이 커진다 |
| app queue cap | userspace 후속 처리 backlog | CQE는 받았지만 buffer recycle이 멈춘다 |

중요한 점:

- provided buffer ring 메타데이터 자체는 작다
- 실제 비용은 `buffers_per_group * buffer_size * group_count`인 **backing buffer memory**다
- 이 backing buffer는 fixed buffer처럼 등록 자원은 아니어도, 앱이 보유하는 동안 RSS / cgroup memory footprint를 차지한다
- 따라서 receive pool sizing은 "ring entry 수"가 아니라 **payload retention time과 함께** 계산해야 한다

### 4. low-water는 "남은 개수"가 아니라 "다음 loop가 소비할 headroom"으로 잡아야 한다

`io_uring_buf_ring_available()`은 6.8+에서 현재 unconsumed entry 수를 알려 준다. 하지만 inflight I/O가 있으면 이 값은 본질적으로 racy하다. 그래서 low-water는 단일 API 결과 하나로 정하면 안 된다.

운영적으로는 최소한 다음 네 덩어리를 같이 봐야 한다.

- `kernel-visible free`: 현재 커널이 소비할 수 있는 free bid
- `inflight consume reserve`: 다음 CQ drain 전에 추가로 소비될 수 있는 bid 수
- `app-owned buffers`: parser/decoder/business queue가 아직 들고 있는 bid 수
- `replenish lag`: free list로 돌아왔지만 아직 ring tail에 commit되지 않은 bid 수

실전 공식은 보통 이런 식이 된다.

```text
effective_headroom
  = kernel_visible_free
  - next_loop_consume_budget
  - app_owned_peak
  - replenish_jitter_margin
```

여기서 `next_loop_consume_budget`에는 다음이 들어간다.

- multishot recv가 한 loop 동안 더 만들어 낼 CQE burst
- `IORING_RECVSEND_BUNDLE`을 쓰면 한 번에 먹을 수 있는 contiguous buffer 수
- `IORING_CQE_F_SOCK_NONEMPTY`가 자주 서는 소켓의 추가 intake 가능성

그래서 low-water / resume-water는 보통 히스테리시스를 둔다.

- `low_water`: 이 아래면 새 recv generation rearm 금지, 또는 shard별 soft pause
- `resume_water`: 이 위로 다시 올라오고 CQ / app queue / memory pressure가 함께 회복됐을 때만 재개

low-water를 너무 낮게 잡으면:

- free bid가 0 근처에서 출렁인다
- `-ENOBUFS`와 즉시 rearm이 반복된다
- app queue가 회복되기도 전에 intake만 다시 붙는다

반대로 너무 높게 잡으면:

- burst 흡수량은 줄어든다
- 하지만 memory.high 근처에서 흔들리는 tail latency는 훨씬 안정적이다

### 5. low-water는 cgroup `memory.low`와 이름만 비슷할 뿐 다른 장치다

둘 다 low-water처럼 들리지만 역할이 다르다.

- provided buffer `low_water`: 앱이 새 recv를 멈출지 결정하는 **admission control**
- cgroup `memory.low`: reclaim에서 덜 건드리게 하는 **kernel-side protection**

즉 `memory.low`를 높게 준다고 free bid가 늘어나지는 않는다. 반대로 provided buffer low-water를 잘 잡아도 reclaim protection이 자동으로 생기지는 않는다.

둘을 같이 쓰는 경우의 감각:

- provided buffer low-water는 intake를 늦춘다
- `memory.low`는 control-plane / parser heap이 너무 쉽게 reclaim되지 않게 도와준다

하지만 provided buffer recycle lag의 해결책은 어디까지나 **rearm / recycle / queue budget**이다.

### 6. sustained receive load에서는 고갈보다 먼저 "느린 붕괴"가 시작된다

receive-heavy 서비스에서 흔한 붕괴 순서는 이렇다.

1. multishot recv가 계속 CQE를 만든다
2. parser/app queue가 payload를 오래 잡으면서 recycle lag가 커진다
3. free bid가 줄지만 아직 0은 아니어서 문제가 가려진다
4. 그 사이 fixed buffers와 socket receive memory 때문에 cgroup headroom이 줄어 `memory.high` reclaim이 먼저 시작된다
5. CQ drain과 parser가 더 느려져 free bid 감소가 가속된다
6. 결국 `-ENOBUFS` 또는 `memory.max` / OOM으로 표면화된다

즉 `-ENOBUFS`는 종종 마지막 증상이다. 그 전에 이미:

- PSI memory pressure 상승
- CQ backlog 증가
- app queue tail 증가
- socket receive memory 확대

가 먼저 나타난다.

## 실전 시나리오

### 시나리오 1: free bid는 아직 남아 있는데 `memory.high` 이벤트와 p99가 먼저 튄다

가능한 원인:

- buffer pool backing memory와 parser queue가 같은 cgroup headroom을 먹고 있다
- fixed buffers가 이미 memlock / resident budget을 오래 잡고 있다
- socket receive autotuning이 커널 큐까지 같이 키운다

대응 감각:

- free bid 외에 `memory.current`, `memory.events`, PSI memory를 같이 본다
- fixed buffer footprint를 줄여 provided pool headroom을 되돌린다
- low-water를 "0 되기 직전"이 아니라 `memory.high` 전에 작동하게 올린다

### 시나리오 2: fixed buffer를 늘렸더니 recv path는 provided ring인데도 불안정해진다

가능한 원인:

- fixed buffers가 `RLIMIT_MEMLOCK` budget을 더 많이 차지한다
- unregister/update 후에도 inflight 때문에 즉시 해제되지 않는다
- 결국 새 등록 실패와 receive-side headroom 감소가 같이 나타난다

대응 감각:

- fixed buffer는 hot path 최소치만 남긴다
- receive pool sizing 전에 fixed buffer 총량을 먼저 뺀다
- "등록은 됐으니 비용은 끝났다"가 아니라 장기 점유로 본다

### 시나리오 3: low-water를 뒀는데도 `-ENOBUFS`와 즉시 rearm이 반복된다

가능한 원인:

- low-water가 bundle 폭이나 CQ lag reserve를 반영하지 않았다
- `io_uring_buf_ring_available()` 값만 믿고 inflight consume을 과소평가했다
- app-owned payload가 실제보다 빨리 recycle된다고 가정했다

대응 감각:

- low-water 계산에 `max_bundle_width`, `max_cq_lag`, `app_owned_peak`를 넣는다
- resume-water를 별도로 둬서 출렁임을 막는다
- 필요하면 같은 크기의 buffer group을 여러 개 두고 group swap으로 refill latency를 숨긴다

## 코드로 보기

### 예산 계산 스케치

```text
fixed_buffer_bytes
  = sum(registered_iovecs)

provided_pool_bytes
  = group_count * buffers_per_group * buffer_size

safe_receive_budget
  = cgroup_headroom_before_memory_high
  - fixed_buffer_bytes
  - socket_rcv_mem_peak
  - app_queue_peak
  - emergency_margin

require:
  provided_pool_bytes <= safe_receive_budget
```

핵심은 `memory.max`가 아니라 **`memory.high` 전에 남겨 둘 headroom**으로 계산하는 것이다.

### low-water / resume-water gate

```text
if free_bids <= low_water
   || memory_current >= memory_high_guard
   || cq_backlog >= cq_high_water
   || app_queue_depth >= app_queue_high_water:
  stop_rearming_recv()

if free_bids >= resume_water
   && memory_current < memory_high_guard
   && cq_backlog <= cq_low_water
   && app_queue_depth <= app_queue_low_water:
  rearm_recv_generation()
```

### 운영 체크 포인트

```bash
ulimit -l
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.high
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.pressure
ss -m
```

애플리케이션 메트릭으로는 최소한 아래가 필요하다.

- free provided bids
- app-owned bids
- recycle lag
- CQ backlog
- fixed buffer registered bytes
- `-ENOBUFS` count

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 provided pool | burst 흡수가 쉽다 | cgroup memory footprint가 커진다 | 짧은 burst가 크다 |
| 작은 provided pool | 메모리 상한이 명확하다 | recycle lag가 바로 `-ENOBUFS`로 드러난다 | 강한 bounded-memory 설계 |
| 큰 fixed buffer set | 일부 hot path가 빠르다 | memlock / resident headroom을 오래 점유한다 | 정말 안정된 size의 고정 경로 |
| 보수적 low-water | reclaim 전에 intake를 늦춘다 | peak throughput이 덜 나온다 | tail latency 우선 |
| 공격적 low-water | 순간 처리량이 높다 | oscillation과 late throttle 위험이 크다 | 짧은 benchmark burst |

## 꼬리질문

> Q: provided buffers를 쓰면 fixed buffers는 필요 없나요?
> 핵심: 아니다. 둘은 다른 용도다. 다만 예산은 누적되므로 fixed buffers를 늘릴수록 receive pool headroom은 줄어든다.

> Q: `io_uring_buf_ring_available()`만 보면 low-water를 정할 수 있나요?
> 핵심: 부족하다. inflight I/O가 있으면 그 값은 racy하므로 CQ lag와 app-owned bid를 같이 봐야 한다.

> Q: `memory.low`를 올리면 `-ENOBUFS`가 사라지나요?
> 핵심: 아니다. `memory.low`는 reclaim 보호일 뿐이고, provided buffer recycle lag 자체를 해결하지는 못한다.

> Q: `-ENOBUFS`가 뜨면 그냥 바로 rearm하면 되나요?
> 핵심: 보통 아니다. free bid, app queue, memory pressure가 회복됐는지 확인한 뒤에만 새 generation을 걸어야 한다.

## 한 줄 정리

provided buffer ring은 `io_uring` receive path의 bounded-memory 장치이고, fixed buffers는 별도 장기 부채다. sustained receive load에서는 두 예산을 합쳐 본 뒤, `memory.high` 전에 작동하는 low-water / resume-water로 intake를 제어해야 `-ENOBUFS`, reclaim stall, OOM을 한 번에 피할 수 있다.
