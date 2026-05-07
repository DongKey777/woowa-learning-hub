---
schema_version: 3
title: TCP Backlog somaxconn Listen Queue
concept_id: operating-system/tcp-backlog-somaxconn-listen-queue
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- tcp-backlog-somaxconn
- listen-queue
- accept-queue-saturation
- syn-backlog
aliases:
- TCP backlog somaxconn listen queue
- accept queue saturation
- SYN backlog
- listen queue overflow
- accept rate bottleneck
- server cannot accept connections
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/reuseport-shard-watermark-tuning.md
- contents/operating-system/tcp-abort-on-overflow-fast-fail-policy.md
- contents/operating-system/thundering-herd-accept-wakeup.md
- contents/operating-system/ephemeral-ports-time-wait-reuse-recovery.md
- contents/operating-system/socket-buffer-autotuning-backpressure.md
symptoms:
- network bandwidth보다 backlog, listen queue, accept rate에서 connection failure가 먼저 터진다.
- somaxconn이나 application backlog 값을 올렸지만 worker accept throughput이 따라오지 않는다.
- SYN backlog와 accept queue overflow를 구분해야 한다.
expected_queries:
- TCP backlog, somaxconn, listen queue는 서버가 connection을 못 받는 문제에서 어떻게 봐?
- accept queue saturation과 network bandwidth 문제를 어떻게 구분해?
- backlog를 늘리면 항상 connection failure가 해결돼?
- SYN backlog와 accept queue, accept rate bottleneck을 설명해줘
contextual_chunk_prefix: |
  이 문서는 server가 connection을 못 받는 문제가 network bandwidth보다 backlog, listen queue,
  accept rate, worker scheduling에서 먼저 터질 수 있음을 설명하는 TCP accept path playbook이다.
---
# TCP Backlog, somaxconn, Listen Queue

> 한 줄 요약: 서버가 연결을 못 받는 문제는 네트워크 대역폭보다 backlog, listen queue, accept 속도에서 먼저 터지는 경우가 많다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [Listener Overload Thresholds and Accept Pause Policy](./listener-overload-thresholds-accept-pause-policy.md)
> - [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [OOM Killer, cgroup Memory Pressure](./oom-killer-cgroup-memory-pressure.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: somaxconn, tcp_max_syn_backlog, listen backlog, effective backlog, accept queue, SYN queue, ListenOverflows, ListenDrops, ss -ltn, backlog saturation, listener overload, accept pause watermark, session-init queue, tcp_abort_on_overflow, backlog buffering, immediate post-accept rejection, accept overflow fast fail

## 핵심 개념

TCP 서버는 연결을 받는 순간부터 두 개의 큐를 의식해야 한다.

- `SYN backlog`: 아직 3-way handshake가 끝나지 않은 연결을 관리한다
- `accept queue`: handshake가 끝났지만 애플리케이션이 `accept()`하지 않은 연결을 둔다

그리고 Linux에는 backlog를 가로채는 전역 상한도 있다.

- `listen(fd, backlog)`: 애플리케이션이 원하는 대기 큐 크기
- `net.core.somaxconn`: 실제 `accept queue` 상한을 제한하는 전역 값
- `net.ipv4.tcp_max_syn_backlog`: SYN backlog 크기와 관련된 값

왜 중요한가:

- 연결이 몰릴 때 먼저 떨어지는 것은 데이터가 아니라 연결일 수 있다
- `accept()`가 느리면 backlog가 차고, 새 요청은 지연되거나 버려진다
- `thundering herd`와 섞이면 연결 수용 비용이 폭증한다

이 문서는 [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)에서 본 accept 경합을, 실제 큐와 sysctl 기준으로 풀어본다.

## 깊이 들어가기

### 1. backlog는 "대기 가능한 연결 수"의 약속이다

애플리케이션은 `listen(fd, backlog)`로 대기 큐 크기를 요청한다. 하지만 커널은 그 값을 그대로 믿지 않고, 전역 상한과 내부 정책으로 조정한다.

즉 backlog는 단순한 숫자가 아니라, **커널이 허용하는 연결 흡수 완충재**다.

### 2. SYN queue와 accept queue는 다르다

연결은 보통 다음 흐름을 거친다.

1. 클라이언트가 SYN을 보낸다
2. 서버가 SYN-ACK을 보낸다
3. 최종 ACK이 오면 handshake가 끝난다
4. 그 뒤에야 accept queue로 넘어간다
5. 애플리케이션이 `accept()`한다

그래서 `listen()` backlog만 키운다고 끝나지 않는다. handshake 이전과 이후가 각각 병목이 될 수 있다.

### 3. backlog overflow는 "서버가 죽었다"가 아니다

overflow는 종종 조용히 발생한다.

- 연결 지연
- SYN drop
- 재전송 증가
- 클라이언트 측 timeout

즉 서버 프로세스가 살아 있어도 수용 큐가 포화되면 사용자 체감은 장애다.

### 4. `somaxconn`은 무시하면 안 되는 상한이다

애플리케이션이 4096을 원해도 `somaxconn`이 4096보다 작으면 실제 상한은 더 낮아질 수 있다.

운영에서 흔한 착각:

- 코드에서 backlog를 충분히 크게 줬으니 안심한다
- 그러나 sysctl 상한이 더 낮아 실제 효과가 없다

이 때문에 앱 코드와 노드 설정을 같이 봐야 한다.

또 한 가지 헷갈리기 쉬운 점은 overflow 이후 정책이다. backlog는 기본적으로 burst 회복 시간을 사는 완충재고, `tcp_abort_on_overflow`는 그 대기 대신 즉시 reset을 택하는 쪽이다. sustained session-init saturation에서 backlog buffering을 계속 믿을지, kernel fast fail이나 post-accept reject로 failure boundary를 옮길지는 [`tcp_abort_on_overflow`, Backlog Buffering, and Immediate Post-Accept Rejection](./tcp-abort-on-overflow-fast-fail-policy.md)에서 이어서 본다.

## 실전 시나리오

### 시나리오 1: 배포 직후 connect timeout과 5xx가 함께 늘어난다

가능한 원인:

- cold start 시 `accept()`가 느려 backlog가 빨리 찬다
- readiness가 너무 빨리 올라와 연결 폭주를 받는다
- `SO_REUSEPORT` 없이 여러 워커가 accept 경쟁을 한다

진단:

```bash
ss -ltnp
cat /proc/net/netstat | grep -E 'ListenOverflows|ListenDrops'
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

판단 포인트:

- LISTEN 소켓의 `Recv-Q`와 `Send-Q`를 본다
- `ListenOverflows`가 증가하는지 확인한다

### 시나리오 2: 트래픽 버스트 때만 새 연결이 늦어진다

가능한 원인:

- accept queue가 burst를 흡수하지 못한다
- accept loop가 느리거나 이벤트 루프가 막힌다
- TLS handshake가 accept 뒤에서 병목을 만든다

진단:

```bash
watch -n 1 'ss -ltnp; echo; cat /proc/net/netstat | grep -E "ListenOverflows|ListenDrops"'
```

### 시나리오 3: SYN flood가 아닌데도 연결이 드랍된다

가능한 원인:

- backlog가 너무 작다
- `accept()` 처리 속도가 부족하다
- softirq나 CPU pressure 때문에 handshake 완료 처리가 늦는다

이 경우는 backlog만 늘리는 것이 아니라, [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)으로 accept path와 scheduler 지연을 같이 봐야 한다.

## 코드로 보기

### listen backlog의 실제 의미

```c
int fd = socket(AF_INET, SOCK_STREAM, 0);
bind(fd, ...);
listen(fd, 4096);
```

이 코드가 "4096개의 연결을 무조건 버퍼링한다"는 뜻은 아니다. 커널 상한과 TCP handshake 단계의 상태가 함께 작동한다.

### 서버의 listen 상태 확인

```bash
ss -ltnp
```

LISTEN 소켓에 대해 `Recv-Q`는 보통 아직 `accept()`되지 않은 연결 수, `Send-Q`는 backlog 상한 쪽으로 읽는 것이 유용하다.

### 커널 카운터 확인

```bash
cat /proc/net/netstat | grep -E 'ListenOverflows|ListenDrops|Syncookies'
cat /proc/net/snmp | grep -E 'Tcp:'
```

### sysctl 확인

```bash
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
sysctl net.ipv4.tcp_syncookies
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| backlog 증가 | 버스트를 더 잘 흡수한다 | 메모리와 지연이 늘 수 있다 | 순간 트래픽이 큰 서버 |
| `SO_REUSEPORT` | accept 경합을 줄인다 | 설계와 배치가 필요하다 | 멀티워커 TCP 서버 |
| accept loop 최적화 | 수용 속도를 높인다 | 구현이 복잡할 수 있다 | 이벤트 루프 서버 |
| sysctl 조정 | 전역 상한을 맞출 수 있다 | 전체 노드에 영향 | 플랫폼 운영 |

backlog는 "더 크게"가 정답이 아니라, **연결 유입 패턴과 accept 속도에 맞게** 잡아야 한다.

## 꼬리질문

> Q: `listen(backlog)`만 키우면 왜 안 되나요?
> 핵심: `somaxconn`, SYN backlog, accept 속도까지 함께 봐야 하기 때문이다.

> Q: LISTEN 소켓의 `ss -ltn` 값은 무엇을 의미하나요?
> 핵심: 수용 대기 중인 연결과 큐 상한을 간접적으로 읽는 힌트다.

> Q: backlog overflow는 어느 층에서 먼저 보이나요?
> 핵심: 클라이언트 timeout, 재전송, 서버의 `ListenOverflows`로 나타난다.

> Q: `SO_REUSEPORT`는 왜 도움이 되나요?
> 핵심: 같은 큐를 여러 워커가 함께 보는 경합을 줄여주기 때문이다.

## 한 줄 정리

TCP 장애는 네트워크가 아니라 backlog와 accept queue에서 먼저 터질 수 있으므로, `somaxconn`, SYN backlog, `accept()` 속도를 같이 봐야 한다.
