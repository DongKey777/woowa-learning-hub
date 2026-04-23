# `tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection

> 한 줄 요약: `listen` backlog는 짧고 회복 가능한 burst를 흡수하는 완충재다. 하지만 session-init가 계속 포화되면, 기다림을 kernel accept queue에 남길지, `tcp_abort_on_overflow`로 overflow 시점에 바로 RST할지, `accept()` 직후 user space에서 빠르게 거절할지 failure boundary를 다시 정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Listener Overload Thresholds and Accept Pause Policy](./listener-overload-thresholds-accept-pause-policy.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Socket Accept Queue, Kernel Diagnostics](./socket-accept-queue-kernel-diagnostics.md)
> - [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)
> - [SO_REUSEPORT Shard Imbalance and Per-Listener Pause Watermark Tuning](./reuseport-shard-watermark-tuning.md)
> - [io_uring Multishot Cancel, Rearm, Drain, Shutdown](./io-uring-multishot-cancel-rearm-drain-shutdown.md)

> retrieval-anchor-keywords: tcp_abort_on_overflow, backlog buffering, accept overflow fast fail, listener overflow fast fail, immediate post-accept rejection, post-accept reject, kernel-side fast fail, user-space fast fail, accept queue overflow reset, RST on accept overflow, session-init saturation, session initialization queue, session-init queue, effective backlog, ListenOverflows, ListenDrops, accept admission boundary, overload failure boundary, overload 503, protocol-aware reject, somaxconn clamp, backlog absorption time, accept queue latency vs reset

## 핵심 개념

listener overload에서 실제 선택지는 "연결을 받느냐 마느냐"보다 **어디서 기다리게 하고, 어디서 실패시키느냐**다.

- backlog buffering: 연결을 kernel accept queue에 잠시 두고, 앱이 따라잡을 시간을 번다
- `tcp_abort_on_overflow=1`: accept queue가 넘치는 순간 kernel이 바로 reset해서 기다림 자체를 줄인다
- immediate post-accept rejection: 앱이 `accept()`는 하되, 값비싼 session-init로 넘기지 않고 가장 싼 reject path로 바로 돌린다
- `session-init`: TLS handshake, 인증, 프로토콜 preface, 라우팅 context 로딩처럼 accept 직후에 붙는 초기화 단계다

왜 중요한가:

- kernel backlog slot은 열린 fd와 half-initialized session보다 훨씬 싸다
- 하지만 session-init가 계속 포화된 상태에서 accept를 이어 가면, 싼 kernel 버퍼를 비싼 user-space state로 바꿔 버린다
- 반대로 `tcp_abort_on_overflow`는 coarse한 host-level sysctl이라, transient burst까지 hard fail로 바꿔 버릴 수 있다

즉 올바른 정책은 "`ListenOverflows`가 보였으니 바로 reset"이 아니라, **이 burst가 backlog 안에서 회복 가능한가**와 **accept 후 거절할 만큼의 user-space budget이 남아 있는가**를 먼저 가르는 것이다.

## 깊이 들어가기

### 1. 먼저 backlog가 회복 시간을 벌 수 있는지 본다

backlog buffering이 맞는지 보려면, "커널이 지금 남은 headroom으로 얼마나 버틸 수 있는가"와 "session-init가 얼마나 빨리 low-water 아래로 내려오는가"를 비교해야 한다.

거칠게는 다음처럼 본다.

```text
free_backlog     = effective_backlog - ack_backlog
excess_arrival   = max(conn_arrival_rate - accept_drain_rate, 0)
burst_budget_sec = free_backlog / max(excess_arrival, 1)

recovery_sec ~= (session_init_depth - init_low)
                / max(init_dequeue_rate - new_init_admit_rate, 1)
```

해석:

- `recovery_sec < burst_budget_sec`이고 `ListenOverflows` delta가 0 또는 단발성이라면 backlog buffering이 여전히 유효하다
- session-init depth가 high-water에 붙은 채 여러 sample 동안 안 내려오고, `recovery_sec > burst_budget_sec`라면 buffering은 회복이 아니라 지연 누적에 가깝다

정밀한 수치보다 중요한 건 slope다.

- accept queue는 잠깐 높아져도 session-init queue가 내려오기 시작하면 버스트 흡수 중일 가능성이 높다
- accept queue와 session-init queue가 둘 다 평평하게 높은 plateau를 만들면, 이제는 buffering이 아니라 fail-fast 경계를 정해야 한다

### 2. backlog buffering은 "짧고 회복 가능한 burst"에 쓰는 기본값이다

기본적으로 Linux는 `tcp_abort_on_overflow=0`일 때 overflow가 burst라면 연결이 회복될 수 있는 쪽에 가깝게 동작한다. 그래서 다음 조건이면 backlog buffering을 먼저 믿는 편이 낫다.

- 배포 직후 warm-up, cache miss, 짧은 GC pause, worker handoff처럼 **원인이 일시적**이다
- `ListenOverflows`/`ListenDrops` delta가 잠깐 보이더라도 바로 0으로 돌아온다
- session-init depth가 pause 이후 low-water 쪽으로 실제로 내려오기 시작한다
- fd 수, socket memory, CQ backlog가 같이 폭주하지 않는다

이때의 핵심 규칙:

- `tcp_abort_on_overflow`는 끄고 둔다
- [Listener Overload Thresholds and Accept Pause Policy](./listener-overload-thresholds-accept-pause-policy.md)처럼 pause/resume hysteresis로 kernel backlog를 짧은 완충재로 쓴다
- backlog를 "영구 queue"가 아니라 "회복 시간 확보용 shock absorber"로 본다

클라이언트는 connect latency가 늘 수 있지만, 결국 성공할 가능성이 높다. 이 구간을 hard fail로 바꾸면 recoverable burst를 불필요한 장애로 바꿀 수 있다.

### 3. `tcp_abort_on_overflow`는 "accept 이전에 실패시켜야 할 때"만 쓴다

`tcp_abort_on_overflow=1`은 accept queue overflow 순간의 대기 대신 **즉시 reset**을 택하는 정책이다. 이 선택이 맞는 경우는 제한적이다.

적합한 조건:

- session-init 포화가 짧은 burst가 아니라 **지속 상태**다
- `accept()` 후 바로 닫는 것조차 부담이다. 즉 fd 수, socket memory, epoll/CQ budget, reactor turn budget이 이미 절벽에 가깝다
- 프로토콜-aware reject를 만들기 전에 비용이 너무 크다. 예를 들어 TLS handshake 자체가 비싸거나, app dispatch에 도달하기 전부터 메모리 압박이 심하다
- node가 사실상 단일 workload이거나, 이 host-level sysctl이 다른 listener를 놀라게 하지 않는다

장점:

- 가장 이른 지점에서 실패하므로 user-space state 폭증을 막기 쉽다
- "기다리다 timeout"보다 빠르게 실패를 드러내고, upstream load balancer가 빨리 다른 backend로 보낼 여지를 준다

함정:

- host-level knob라 세밀한 listener별 정책이 어렵다
- transient burst까지 hard fail로 바꾸므로 클라이언트 체감이 더 나빠질 수 있다
- 공격적인 재시도 클라이언트가 많으면 RST가 reconnect storm을 더 자극할 수 있다
- root cause를 해결하지는 않는다. `ListenOverflows`가 계속 늘면 여전히 용량이 부족한 상태다

즉 `tcp_abort_on_overflow`는 "accept path를 더 튜닝할 수 없고, 기다리게 두는 것보다 즉시 실패가 덜 해롭다"는 판단이 있을 때만 맞다.

### 4. immediate post-accept rejection은 "accept는 감당되지만 session-init는 못 받는" 구간에 맞다

user space fast fail은 실패 경계를 accept 뒤로 한 칸 옮기는 정책이다.

적합한 조건:

- 앱이 `accept()`와 최소한의 분류는 감당할 수 있다
- 하지만 TLS/auth/backend admission처럼 비싼 session-init는 더 못 받는다
- listener별, route별, shard별로 다르게 반응하고 싶다
- 프로토콜-aware overload 응답이 가치 있다. 예를 들어 HTTP `503`/`Retry-After`, proxy-level overload close, 앱 내부 reject counter 집계 같은 것들이다

이 방식이 좋은 이유:

- `tcp_abort_on_overflow`와 달리 host 전체가 아니라 **서비스/리스너 단위 정책**으로 만들 수 있다
- `SO_REUSEPORT` hot shard만 reject path로 돌리는 식의 세밀한 제어가 가능하다
- backlog는 여전히 microburst 완충재로 두고, 지속 포화 구간만 빠르게 잘라낼 수 있다

하지만 비용은 분명히 있다.

- 소켓 하나를 user space까지 끌어오므로 fd와 socket state를 실제로 만든다
- reject path가 느리면 오히려 overload를 악화시킨다
- TLS handshake 자체가 병목이라면, "post-accept" 시점에는 이미 너무 늦었을 수 있다

그래서 user-space reject path는 반드시 **bounded fast path**여야 한다.

- full session-init queue에 다시 enqueue하지 않는다
- 동기 logging, DB lookup, 복잡한 auth branch를 태우지 않는다
- "빠른 overload 응답 또는 즉시 close" 이상을 욕심내지 않는다

### 5. 실제 운영에서는 세 정책을 계단식으로 쓴다

| 상태 | 우선 정책 | 이유 |
|------|------|------|
| 짧은 burst, 회복 slope가 보임 | backlog buffering + pause/resume | 성공률을 보존하면서 가장 싼 queue를 쓴다 |
| session-init가 high-water에 붙었지만 `accept()+reject`는 아직 싸다 | immediate post-accept rejection | user-space state를 제한하면서 protocol-aware fail이 가능하다 |
| fd/memory/CQ 절벽이라 `accept()+reject`도 위험하다 | `tcp_abort_on_overflow` 또는 upstream shed | 실패를 accept 이전으로 당겨야 한다 |
| `SO_REUSEPORT` hot shard만 문제다 | shard-local pause/reject 우선 | host-wide sysctl보다 국소 조치가 덜 파괴적이다 |

핵심은 `tcp_abort_on_overflow`와 post-accept rejection을 대체재로 보지 않는 것이다.

- backlog buffering은 **recoverable burst**에 대한 기본 전략
- post-accept rejection은 **accept는 가능한데 init가 불가능한** 중간 단계
- `tcp_abort_on_overflow`는 **accept 자체가 더는 안전하지 않은** 마지막 단계에 가깝다

### 6. 어떤 신호가 어떤 경계를 가리키는가

#### backlog buffering을 계속 믿어도 되는 신호

- `ListenOverflows`/`ListenDrops` delta가 0이거나 단발성이다
- session-init depth가 high-water를 찍고도 곧 내려온다
- open fd, socket memory, CQ backlog가 안정적이다
- pause 후 low-water 복귀가 실제로 관측된다

#### immediate post-accept rejection으로 넘어가야 하는 신호

- session-init depth가 high-water에 붙은 채 내려오지 않는다
- init p95/p99가 budget 밖인데, accept/CQ 쪽은 아직 bounded하게 돌릴 수 있다
- kernel backlog는 microburst를 버틸 headroom이 있지만, user-space init budget은 없다
- overload 응답을 남기는 편이 운영상 유리하다

#### `tcp_abort_on_overflow`까지 고려해야 하는 신호

- `ListenOverflows`/`ListenDrops` delta가 여러 window에서 계속 증가한다
- reject path를 켜도 fd 수, memory, CQ pressure가 줄지 않는다
- accept queue와 session-init queue가 동시에 포화되어 plateau를 만든다
- 프로세스가 `RLIMIT_NOFILE`, socket memory, reactor turn budget 근처라 `accept()` 자체가 위험하다

## 실전 시나리오

### 시나리오 1: 배포 직후 3~5초만 새 연결이 밀린다

관측:

- `Recv-Q`가 잠깐 치솟는다
- `ListenOverflows` delta가 1~2번 보이지만 바로 멈춘다
- session-init queue가 warm-up 뒤 곧 내려온다

판단:

- backlog buffering이 맞다
- `tcp_abort_on_overflow`는 과하다
- pause/resume hysteresis와 warm-up budget 조정이 우선이다

### 시나리오 2: auth worker queue가 계속 꽉 차지만 cheap 503은 보낼 수 있다

관측:

- accept/CQ는 아직 크게 흔들리지 않는다
- session-init depth와 init latency만 오래 높다
- backlog는 짧은 버스트를 버티지만, full init path는 이미 손해다

판단:

- immediate post-accept rejection이 맞다
- accept 뒤 가장 싼 overload 응답만 보내고 비싼 auth/init path는 태우지 않는다
- `tcp_abort_on_overflow`는 너무 거칠고, backlog-only는 tail latency만 늘린다

### 시나리오 3: TLS terminator가 fd와 socket memory 절벽에 가깝다

관측:

- `ListenOverflows`/`ListenDrops`가 계속 증가한다
- session-init는 TLS handshake 자체라 post-accept 뒤 savings가 작다
- 열린 socket 수와 메모리가 빠르게 치솟는다

판단:

- `accept()+close`도 이미 늦다
- `tcp_abort_on_overflow` 또는 upstream load shed처럼 accept 이전 실패 경계를 고려한다
- 단, 이는 "설정을 켜면 해결"이 아니라 **더 나쁜 user-space 붕괴를 막는 손실 제한**에 가깝다

## 트레이드오프

| 선택지 | 클라이언트 체감 | resource cost | 정책 granularity | 언제 맞는가 |
|------|------|------|------|-------------|
| backlog buffering | connect 지연이 늘 수 있지만 성공 가능성이 남는다 | 가장 싸다 | listener watermark 기준 | 짧고 회복 가능한 burst |
| `tcp_abort_on_overflow` | 즉시 RST로 빠르게 실패한다 | overflow 이후 가장 싸다 | host-level sysctl | accept 자체가 더는 안전하지 않을 때 |
| immediate post-accept rejection | `503` 또는 빠른 close처럼 의미 있는 실패를 줄 수 있다 | `accept()` 한 번 비용이 든다 | listener / route / shard별 가능 | accept는 가능하지만 session-init는 포화일 때 |

## 꼬리질문

> Q: `ListenOverflows`가 한 번이라도 늘면 바로 `tcp_abort_on_overflow`를 켜야 하나요?
> 핵심: 아니다. burst가 곧 회복되는 구간이면 backlog가 제 역할을 하는 중일 수 있다.

> Q: session-init가 포화되면 항상 post-accept rejection이 맞나요?
> 핵심: 아니다. fd/memory cliff가 더 가깝거나 TLS handshake 자체가 병목이면 accept 뒤 거절은 이미 너무 늦을 수 있다.

> Q: backlog buffering과 post-accept rejection을 같이 쓸 수 있나요?
> 핵심: 가능하다. backlog는 microburst 완충재로 두고, saturation이 오래 지속될 때만 reject path로 승격하면 된다.

> Q: `tcp_abort_on_overflow`는 튜닝 대신 써도 되나요?
> 핵심: 아니다. accept path, `somaxconn`, session-init budget, upstream shed를 먼저 맞춘 뒤에도 기다림보다 즉시 실패가 덜 해로울 때만 고려한다.

## 한 줄 정리

backlog는 짧은 회복 시간을 사는 데 쓰고, sustained session-init saturation에서는 "accept 후 거절이 아직 싼가"를 먼저 본 다음, 그것도 늦을 때만 `tcp_abort_on_overflow`처럼 accept 이전의 hard fail 경계를 택하는 것이 안전하다.
