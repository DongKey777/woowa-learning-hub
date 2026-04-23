# Socket Accept Queue, Kernel Diagnostics

> 한 줄 요약: accept queue 문제는 애플리케이션의 `accept()` 속도만 볼 게 아니라, 커널이 백로그를 어떻게 쌓고 버리는지를 같이 봐야 정확히 진단된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Listener Overload Thresholds and Accept Pause Policy](./listener-overload-thresholds-accept-pause-policy.md)
> - [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)
> - [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: accept queue, sk_ack_backlog, sk_max_ack_backlog, effective backlog, ListenOverflows, ListenDrops, tcp_abort_on_overflow, SYN backlog, ss -ltn, /proc/net/netstat, listener overload, accept pause threshold, session-init queue, accept overload observability playbook, backlog fill ratio, kernel queue vs CQ queue, immediate post-accept rejection, accept overflow fast fail, kernel-side fast fail

## 핵심 개념

TCP listen socket은 handshake를 마친 연결을 accept queue에 쌓는다. 이 큐가 넘치면 새 연결은 지연되거나 드랍된다.

- `sk_ack_backlog`: 현재 accept queue에 쌓인 연결 수다
- `sk_max_ack_backlog`: accept queue의 최대치다
- `ListenOverflows`, `ListenDrops`: 커널이 backlog를 못 받아낸 흔적이다

왜 중요한가:

- 애플리케이션의 `accept()`가 느려도 문제가 생긴다
- SYN backlog와 accept queue는 다른 병목이다
- softirq와 scheduler 지연이 accept queue를 간접적으로 망가뜨릴 수 있다

이 문서는 [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)를 커널 관측 지표 중심으로 더 좁힌다. `ss -ltn`, `ListenOverflows`/`ListenDrops`, `io_uring` CQ를 같은 시간축에서 묶는 step-oriented 흐름은 [Accept Overload Observability Playbook](./accept-overload-observability-playbook.md)에서 이어서 본다.

## 깊이 들어가기

### 1. accept queue는 handshake 이후의 대기열이다

클라이언트가 3-way handshake를 끝냈다고 바로 앱이 받는 것은 아니다.

- 커널이 먼저 큐에 둔다
- 앱이 `accept()`해야 user space로 넘어간다
- 큐가 꽉 차면 연결이 밀린다

### 2. 커널 카운터를 같이 봐야 한다

- `ListenOverflows`
- `ListenDrops`
- `Syncookies`

이 지표들은 backlog가 실제로 압박받는지 알려준다.

### 3. 단순 accept 속도만의 문제가 아닐 수 있다

- IRQ/softirq가 밀린다
- worker가 CPU를 못 받는다
- fd exhaustion이 먼저 온다

### 4. backlog overflow는 클라이언트 체감 장애다

앱 로그보다 먼저 클라이언트 timeout, 재전송, connection reset으로 나타날 수 있다.

이 지점에서 중요한 운영 질문은 "overflow를 잠깐 버스트로 흡수할지", "`tcp_abort_on_overflow`로 바로 reset할지", "`accept()` 직후 user space에서 빠르게 거절할지"다. 그 failure boundary 선택 자체는 [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)에서 따로 다룬다.

## 실전 시나리오

### 시나리오 1: connect timeout이 증가한다

가능한 원인:

- accept queue가 꽉 찼다
- 앱의 accept loop가 느리다
- backlog가 너무 작다

진단:

```bash
ss -ltnp
cat /proc/net/netstat | grep -E 'ListenOverflows|ListenDrops|Syncookies'
```

### 시나리오 2: 배포 직후만 연결이 흔들린다

가능한 원인:

- cold start로 accept 속도가 낮다
- thundering herd가 일어난다
- readiness가 너무 빨리 올라간다

### 시나리오 3: CPU는 멀쩡한데 listen 큐만 가득 찬다

가능한 원인:

- wakeup/softirq 지연
- connection burst
- accept path에서 fd 생성이 늦다

## 코드로 보기

### listen socket 상태 확인

```bash
ss -ltnp
```

### 커널 카운터 확인

```bash
cat /proc/net/netstat | grep -E 'ListenOverflows|ListenDrops|Syncookies'
```

### 단순 모델

```text
handshake completes
  -> kernel enqueues to accept queue
  -> app accept() drains queue
  -> if drain is slow, overflows appear
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| backlog 상향 | 버스트 흡수에 좋다 | 메모리와 지연이 늘 수 있다 | 피크 트래픽 |
| accept loop 최적화 | 큐 드레인을 빠르게 한다 | 구현 복잡도 증가 | 고성능 서버 |
| `SO_REUSEPORT` | 경합을 줄인다 | 배치와 운영이 복잡하다 | 멀티워커 |

## 꼬리질문

> Q: `ListenDrops`는 무엇을 의미하나요?
> 핵심: 커널이 accept queue나 관련 경로에서 연결을 버렸다는 신호다.

> Q: accept queue와 SYN backlog는 같나요?
> 핵심: 아니다. handshake 이전과 이후의 다른 큐다.

> Q: accept queue 문제를 어떻게 구분하나요?
> 핵심: `ss -ltnp`와 `/proc/net/netstat`를 같이 본다.

## 한 줄 정리

accept queue 장애는 커널 큐 지표와 함께 봐야 하며, `accept()` 속도와 softirq/IRQ 지연이 함께 병목을 만든다.
