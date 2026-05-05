---
schema_version: 3
title: Listener Overload Thresholds and Accept Pause Policy
concept_id: operating-system/listener-overload-thresholds-accept-pause-policy
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- effective-backlog-watermark
- multishot-accept-hysteresis
- cq-drain-reserve
aliases:
- listener overload thresholds accept pause policy
- accept pause policy
- multishot accept pause resume
- effective backlog watermark
- accept queue watermark
- session init queue watermark
- listener hysteresis
- reuseport pause watermark
- accept admission control
- accept overload thresholds
symptoms:
- pause와 resume threshold를 backlog 요청값 기준으로 잡아도 되는지 헷갈려요
- multishot accept를 멈출 때 CQ reserve를 왜 남겨야 하는지 감이 안 와요
- accept queue, CQ backlog, session-init queue를 어느 순서로 admission control에 묶어야 할지 모르겠어요
intents:
- design
- troubleshooting
prerequisites:
- operating-system/socket-accept-queue-kernel-diagnostics
- operating-system/io-uring-multishot-cancel-rearm-drain-shutdown
next_docs:
- operating-system/accept-overload-observability-playbook
- operating-system/reuseport-shard-watermark-tuning
linked_paths:
- contents/operating-system/accept-overload-observability-playbook.md
- contents/operating-system/io-uring-multishot-cancel-rearm-drain-shutdown.md
- contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md
- contents/operating-system/reuseport-shard-watermark-tuning.md
- contents/operating-system/tcp-backlog-somaxconn-listen-queue.md
- contents/operating-system/socket-accept-queue-kernel-diagnostics.md
- contents/operating-system/tcp-abort-on-overflow-fast-fail-policy.md
- contents/operating-system/thundering-herd-accept-wakeup.md
- contents/operating-system/socket-buffer-autotuning-backpressure.md
confusable_with:
- operating-system/accept-overload-observability-playbook
- operating-system/socket-accept-queue-kernel-diagnostics
- operating-system/reuseport-shard-watermark-tuning
forbidden_neighbors:
- contents/operating-system/accept-overload-observability-playbook.md
- contents/operating-system/socket-accept-queue-kernel-diagnostics.md
expected_queries:
- accept pause resume threshold를 effective backlog 기준으로 잡는 방법을 정리해줘
- multishot accept pause policy에서 CQ reserve가 왜 필요한지 설명해줘
- session-init queue와 accept queue watermark를 같이 보는 playbook이 필요해
- reuseport hot shard에서 listener별 pause watermark를 어떻게 잡아야 해?
- accept overload 대응에서 backlog buffering과 user-space fast fail 사이 기준이 뭐야?
contextual_chunk_prefix: |
  이 문서는 과부하가 걸린 listener에서 연결 받기를 언제 늦추고 언제 다시 열지,
  커널 backlog와 CQ drain 여유, session-init 대기열을 한 기준으로 묶어 전략으로
  막는 playbook이다. 새 연결은 계속 오는데 어디서 완충할지, pause가 너무 늦은지,
  hot shard만 먼저 막아야 하는지, downstream이 회복됐는지 같은 자연어
  paraphrase가 본 문서의 watermark 설계에 매핑된다.
---

# Listener Overload Thresholds and Accept Pause Policy

> 한 줄 요약: `io_uring` multishot accept의 pause/resume은 cancel 타이밍만의 문제가 아니라, `listen(backlog)`와 `net.core.somaxconn`이 만든 실제 accept queue headroom, CQ drain budget, 세션 초기화 queue watermarks를 하나의 admission-control 규칙으로 묶는 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)
> - [io_uring CQ Overflow, Multishot, Provided Buffers, IOWQ Placement](./io-uring-cq-overflow-provided-buffers-iowq-placement.md)
> - [SO_REUSEPORT Shard Imbalance and Per-Listener Pause Watermark Tuning](./reuseport-shard-watermark-tuning.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Socket Accept Queue, Kernel Diagnostics](./socket-accept-queue-kernel-diagnostics.md)
> - [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [Socket Buffer Autotuning, Backpressure](./socket-buffer-autotuning-backpressure.md)

> retrieval-anchor-keywords: listener overload thresholds, accept pause policy, multishot accept pause, multishot accept resume, effective backlog, somaxconn clamp, listen backlog, accept queue watermark, session initialization queue, session-init queue, init queue watermark, io_uring accept backpressure, CQ backlog watermark, accept admission control, listener hysteresis, ListenOverflows, ListenDrops, drain reserve, accept overload observability playbook, ss -ltn, /proc/net/netstat, CqHead CqTail CQEs, SO_REUSEPORT shard imbalance, reuseport pause watermark, per-listener backlog threshold, hot shard fill ratio, tcp_abort_on_overflow, immediate post-accept rejection, kernel-side fast fail, user-space fast fail

## 핵심 개념

listener overload 대응은 "연결을 받느냐 마느냐"의 문제가 아니라, 어느 큐에서 버스트를 흡수할지 정하는 문제다.

- `effective backlog`: 애플리케이션이 요청한 `listen(backlog)`와 `net.core.somaxconn` 중 더 작은 값이다
- `accept queue watermark`: 현재 `sk_ack_backlog`가 effective backlog 대비 얼마나 찼는지 보는 경계다
- `session initialization queue`: `accept()` 뒤에 TLS handshake, 인증, 프로토콜 preface, 라우팅 컨텍스트 로딩 같은 초기화 작업을 기다리는 앱 내부 큐다
- `high-water / low-water`: pause와 resume을 같은 숫자로 하지 않고, 히스테리시스를 둬 thrash를 막는 규칙이다
- `drain reserve`: multishot accept cancel 후에도 이미 도착한 CQE와 마지막 terminal CQE를 처리할 수 있도록 남겨 두는 슬롯 수다

왜 중요한가:

- session-init queue가 포화된 상태에서 accept를 계속하면, 커널 backlog의 "싼 버퍼"를 user-space의 "비싼 half-open session"으로 바꿔 버린다
- `somaxconn`이 backlog를 더 작게 clamp하는데도 앱이 요청값 기준으로 threshold를 잡으면 pause가 너무 늦다
- multishot accept는 cancel 직후 즉시 멈추지 않으므로, reserve 없는 정책은 pause 순간에 오히려 queue overflow를 만든다

정책을 세운 뒤 현장에서 `ss -ltn`, `/proc/net/netstat`, `io_uring` CQ를 어떤 순서로 묶어 읽을지 필요하면 [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)으로 바로 내려가면 된다.

## 깊이 들어가기

### 1. listener overload는 하나의 큐가 아니라 큐 사슬 전체를 봐야 한다

연결 유입은 대략 다음 순서로 압력이 전파된다.

```text
SYN queue
  -> accept queue (sk_ack_backlog / effective backlog)
  -> io_uring multishot accept CQE stream
  -> session-init queue (TLS/auth/preface/warmup)
  -> active connection set
```

이때 pause/resume의 본질은 pressure boundary를 어디에 둘지 정하는 것이다.

- session-init이 건강하면 accept queue를 적극적으로 drain해도 된다
- session-init이 꽉 찼다면 listener는 열어 두고 accept drain만 멈춰서 커널 backlog가 짧은 burst를 흡수하게 하는 편이 낫다
- backlog까지 이미 꽉 찼는데도 session-init이 회복되지 않으면, 그때는 "더 많이 accept"가 아니라 upstream shed 또는 빠른 실패가 필요하다. backlog buffering, `tcp_abort_on_overflow`, immediate post-accept rejection 중 어디에 failure boundary를 둘지는 [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)에서 따로 정리한다.

즉 listener pause는 "연결 거부"보다 먼저 쓰는 admission-control 레버고, backlog는 그 레버를 당긴 뒤 남는 완충재다.

### 2. threshold의 기준은 요청 backlog가 아니라 effective backlog다

실제 accept queue 상한은 보통 다음처럼 생각해야 한다.

```text
effective_backlog = min(configured_listen_backlog, net.core.somaxconn)
```

예를 들어:

- 앱 코드: `listen(fd, 4096)`
- 노드 설정: `net.core.somaxconn = 512`

이 경우 실제 accept queue 상한은 4096이 아니라 512에 가깝다. 그런데 pause high-water를 3000 근처에 두면, policy가 아예 발동하기 전에 `ListenOverflows`가 먼저 증가한다.

운영 규칙:

- accept queue 관련 watermark는 항상 effective backlog를 기준으로 계산한다
- `ss -ltn`에서 보는 LISTEN `Recv-Q`/`Send-Q`도 이 effective backlog 관점으로 읽는다
- 노드별 `somaxconn` 차이가 있으면 same binary라도 shard마다 pause 지점이 달라질 수 있다
- `SO_REUSEPORT`라면 "포트 전체 backlog"가 아니라 listener별 `effective_backlog_i`와 `sk_ack_backlog_i`를 기준으로 계산해야 한다. port aggregate는 hot shard overflow를 숨길 수 있으므로, shard skew와 local high/low-water 설계는 [SO_REUSEPORT Shard Imbalance and Per-Listener Pause Watermark Tuning](./reuseport-shard-watermark-tuning.md)에서 이어서 본다.

### 3. pause는 backlog 포화 하나만이 아니라 downstream saturation과 같이 봐야 한다

accept queue가 높다고 항상 pause해야 하는 것은 아니다.

- burst가 짧고 session-init queue가 비어 있다면, pause보다 빠른 drain이 맞다
- 반대로 accept queue가 아직 여유 있어도 session-init queue와 CQ backlog가 함께 차면, 그 시점부터는 새 fd를 user-space로 끌어오는 것이 손해다

실무에서는 보통 다음 세 축을 같이 본다.

| 축 | 대표 지표 | pause 판단 이유 |
|------|------|------|
| kernel intake | `sk_ack_backlog / effective_backlog`, `ListenOverflows`, `ListenDrops` | 커널 완충재가 얼마나 남았는지 본다 |
| completion side | CQ depth, CQ overflow 카운터, reactor turn당 accept CQE 수 | cancel 이후에도 이미 도착한 CQE를 감당할 수 있는지 본다 |
| downstream init | session-init depth, init worker busy, init p95 latency | accept 뒤 비용을 실제로 소화할 수 있는지 본다 |

핵심은 backlog가 아니라 **더 작은 downstream budget**이 listener policy를 결정한다는 점이다.

### 4. watermarks는 reserve와 hysteresis를 같이 가져야 한다

출발점으로 쓸 수 있는 규칙은 다음과 같다.

```text
effective_backlog = min(configured_backlog, somaxconn)

accept_high = min(floor(effective_backlog * 0.70), effective_backlog - drain_reserve)
accept_low  = floor(effective_backlog * 0.40)

init_high = min(floor(session_init_capacity * 0.80), session_init_capacity - drain_reserve)
init_low  = floor(session_init_capacity * 0.50)
```

여기서 `drain_reserve`는 다음을 흡수할 만큼 남겨 둔다.

- cancel 전에 이미 CQ에 게시된 accept CQE
- cancel 이후 도착하는 terminal CQE(`!IORING_CQE_F_MORE`)
- 한 reactor turn 안에서 아직 session-init queue로 넘겨야 할 in-flight accept batch

이 규칙의 의미:

- `high-water`: 이 지점을 넘기기 전에 multishot accept를 멈춰 downstream을 보호한다
- `low-water`: 이 지점 아래로 충분히 내려오기 전에는 resume하지 않는다
- high와 low를 분리해 pause/resume flap을 줄인다

정확한 수치는 workload마다 다르지만, reserve 없이 90% 이상에서 멈추는 정책은 대개 너무 늦다.

### 5. session-init queue는 backlog보다 작은 편이 자연스럽다

많은 서버에서 session-init 단계는 accept queue보다 더 비싸다.

- fd가 하나 더 열린다
- socket buffer와 프로토콜 state가 붙는다
- TLS handshake, auth, routing lookup이 CPU와 메모리를 먹는다

그래서 다음 구조는 흔하다.

- effective backlog: 512~2048
- session-init capacity: 64~256

이 구조에서 중요한 판단은 "backlog를 다 비우는 것"이 아니다. 더 중요한 것은 **session-init queue를 넘기지 않는 것**이다.

예를 들어 session-init capacity가 128인데 queue가 이미 110이고, cancel 후 in-flight accept 16개를 더 받아야 한다면:

- 이 시점의 실질 free slots는 18이 아니라 2다
- accept queue가 아직 50%여도 pause를 걸어야 한다
- resume은 init queue가 60 안팎까지 내려온 뒤에야 하는 편이 안전하다

즉 listener pause threshold는 "kernel queue가 얼마나 남았나"보다 "user-space가 얼마나 더 초기화할 수 있나"에 더 크게 묶인다.

### 6. multishot accept pause/resume은 cancel-drain-rearm 상태 기계여야 한다

multishot accept는 `accept_paused=true`만 세운다고 바로 멈추지 않는다. 현재 generation을 끝까지 정리해야 한다.

권장 상태 기계:

1. pause 조건을 감지하면 `accept_paused=true`
2. active multishot accept generation을 cancel한다
3. old generation의 `!IORING_CQE_F_MORE` terminal CQE까지 drain한다
4. drain reserve 안에서만 session-init queue로 handoff한다
5. listener fd는 계속 열어 둔다
6. 모든 low-water가 만족되면 새 generation으로 rearm한다

의사 코드:

```text
effective_backlog = min(cfg.listen_backlog, metrics.somaxconn)

should_pause =
  session_init_depth >= init_high ||
  cq_depth >= cq_high ||
  (accept_q_depth >= accept_high && init_latency_p95 >= init_latency_budget)

should_resume =
  accept_paused &&
  accept_q_depth <= accept_low &&
  session_init_depth <= init_low &&
  cq_depth <= cq_low &&
  listen_overflows_delta == 0

if should_pause and accept_generation.active:
  accept_paused = true
  cancel(accept_generation.user_data)

on_accept_cqe(cqe):
  handoff_to_init_queue_if_reserved_slot_exists(cqe.fd)
  if cqe.user_data == accept_generation.user_data and !cqe.more:
    accept_generation.active = false

if should_resume and !accept_generation.active:
  accept_paused = false
  arm_multishot_accept(new_generation())
```

중요한 점:

- pause는 listener close가 아니다
- rearm은 old generation drain 완료 후에만 한다
- reserve를 초과한 in-flight accept는 무한 enqueue 대신 빠른 실패 경로를 준비해야 한다

### 7. 관측은 큐 깊이뿐 아니라 "증가 속도"도 같이 봐야 한다

다음 조합이 유용하다.

| 대상 | 지표 예시 | 왜 같이 봐야 하나 |
|------|------|------|
| listen socket | `ss -ltn`, `Recv-Q`, `Send-Q` | 현재 accept queue 압력을 본다 |
| kernel counters | `/proc/net/netstat`의 `ListenOverflows`, `ListenDrops` | threshold가 늦었는지 본다 |
| io_uring | CQ depth, overflow 카운터, turn당 accept CQE | cancel-drain window의 실제 burst를 본다 |
| app queue | session-init depth, dequeue rate, init p95/p99 | resume를 해도 되는지 본다 |

특히 `ListenOverflows`가 0이더라도 session-init queue가 계속 상승 중이면 pause를 늦춘 것이다. 반대로 accept queue가 높아도 session-init dequeue rate가 충분히 크고 latency budget 안에 있으면 backlog/somaxconn 튜닝이 우선일 수 있다.

## 실전 시나리오

### 시나리오 1: `listen(4096)`인데도 배포 직후만 새 연결이 밀린다

가능한 원인:

- 실제 노드 `somaxconn`이 512라 effective backlog가 작다
- 앱은 4096 기준으로 pause threshold를 계산했다
- cold start로 session-init latency가 길어져 pause가 더 늦어졌다

대응:

- threshold 계산을 effective backlog 기준으로 바꾼다
- `somaxconn`과 session-init warmup budget을 같이 점검한다
- 배포 직후 readiness/ramp-up과 연결해 본다

### 시나리오 2: accept queue는 비지 않았는데 fd 수와 메모리만 급증한다

가능한 원인:

- listener는 열심히 accept를 drain했지만 session-init queue가 포화됐다
- backlog의 싼 버퍼를 user-space half-open session으로 옮겨 버렸다

대응:

- pause 조건에 session-init depth와 init latency를 넣는다
- init capacity보다 큰 accept burst를 user-space에 들이지 않도록 reserve를 둔다

### 시나리오 3: pause는 잘 걸리는데 resume 후 바로 다시 pause된다

가능한 원인:

- high-water와 low-water가 사실상 같은 값이다
- old generation drain 이후 backlog가 아직 남아 있는데 바로 rearm한다

대응:

- low-water를 더 낮춰 hysteresis를 만든다
- `ListenOverflows` delta, init dequeue rate, CQ low-water까지 함께 만족할 때만 resume한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| backlog/somaxconn 상향 | 짧은 burst를 더 흡수한다 | 늦은 pause를 가리기 쉽다 | downstream이 건강하고 burst만 큰 경우 |
| pause를 일찍 건다 | session-init, fd, 메모리 보호에 좋다 | 클라이언트 대기가 backlog 쪽으로 이동한다 | init 비용이 비싼 TLS/auth-heavy 서버 |
| pause를 늦게 건다 | 순간 연결 수용량은 커 보인다 | user-space queue와 tail latency가 폭발한다 | init 비용이 매우 작고 burst가 짧을 때만 제한적으로 |
| hysteresis를 크게 둔다 | flap을 줄인다 | resume가 보수적일 수 있다 | backlog와 init queue가 동시에 흔들리는 서버 |

## 꼬리질문

> Q: pause threshold는 backlog 퍼센트만 보면 안 되나요?
> 핵심: 안 된다. `somaxconn` clamp와 session-init capacity 중 더 작은 예산이 실제 상한을 정하기 때문이다.

> Q: 왜 pause 중에도 listener를 닫지 않나요?
> 핵심: pause는 intake 조절이지 teardown이 아니기 때문이다. close는 다른 오류 경계와 fd lifecycle까지 바꿔 버린다.

> Q: resume는 accept queue가 조금만 비면 바로 하면 되나요?
> 핵심: 아니다. CQ backlog와 session-init low-water까지 내려와야 old burst를 다시 먹지 않는다.

## 한 줄 정리

listener overload 정책은 multishot accept cancel 규칙 하나로 끝나지 않으며, effective backlog(`listen` backlog + `somaxconn`), CQ drain reserve, session-init queue watermarks를 함께 묶은 hysteresis 기반 admission-control로 설계해야 한다.
