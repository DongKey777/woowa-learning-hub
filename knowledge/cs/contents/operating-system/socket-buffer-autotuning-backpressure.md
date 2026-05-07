---
schema_version: 3
title: Socket Buffer Autotuning Backpressure
concept_id: operating-system/socket-buffer-autotuning-backpressure
canonical: true
category: operating-system
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
review_feedback_tags:
- socket-buffer-autotuning
- backpressure
- tcp-receive-send
- buffer-backpressure
aliases:
- socket buffer autotuning
- TCP receive send buffer backpressure
- ss -m socket memory
- network backpressure
- kernel socket buffer
- bufferbloat latency
intents:
- troubleshooting
- deep_dive
- design
linked_paths:
- contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md
- contents/operating-system/ephemeral-ports-time-wait-reuse-recovery.md
- contents/operating-system/tcp-backlog-somaxconn-listen-queue.md
- contents/operating-system/softirq-hardirq-latency-server-debugging.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
symptoms:
- socket buffer가 커져 throughput은 유지되지만 latency와 memory usage가 커진다.
- send/receive buffer가 network speed mismatch를 흡수하면서 application backpressure가 늦게 전달된다.
- ss -m에서 socket memory growth를 보고 buffer autotuning과 pressure를 해석해야 한다.
expected_queries:
- socket buffer는 단순 저장 공간이 아니라 backpressure를 전달하는 장치야?
- TCP send/receive buffer autotuning은 throughput과 latency에 어떤 tradeoff가 있어?
- ss -m으로 socket memory와 backpressure를 어떻게 확인해?
- buffer가 너무 크면 network latency와 memory pressure가 커질 수 있어?
contextual_chunk_prefix: |
  이 문서는 socket buffer를 단순 저장 공간이 아니라 kernel이 network speed mismatch를 흡수하며
  backpressure를 전달하는 buffer로 설명한다. autotuning, latency, memory pressure, ss -m을 함께 본다.
---
# Socket Buffer Autotuning, Backpressure

> 한 줄 요약: socket buffer는 단순 저장 공간이 아니라, 커널이 네트워크 속도 차를 흡수하면서 backpressure를 전달하는 핵심 완충 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: SO_RCVBUF, SO_SNDBUF, tcp_rmem, tcp_wmem, autotuning, skbuff, backpressure, send buffer, receive buffer, tcp_mem

## 핵심 개념

TCP socket buffer는 송수신 데이터의 속도 차를 완충한다. Linux는 다양한 기준으로 buffer 크기를 자동 조정할 수 있고, 이를 `autotuning`이라고 부른다.

- `SO_RCVBUF`: 수신 버퍼 크기 힌트다
- `SO_SNDBUF`: 송신 버퍼 크기 힌트다
- `tcp_rmem`, `tcp_wmem`: TCP 자동 조정 범위에 영향을 준다
- `backpressure`: 상대나 커널이 더 이상 빨리 못 받는 신호다

왜 중요한가:

- 버퍼가 너무 작으면 throughput이 떨어진다
- 버퍼가 너무 크면 메모리를 먹고 지연을 숨길 수 있다
- backpressure를 무시하면 큐가 서버 내부에서만 커질 수 있다

이 문서는 [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)와 [TCP Backlog, somaxconn, Listen Queue](./tcp-backlog-somaxconn-listen-queue.md)를 buffer 관점으로 잇는다.

## 깊이 들어가기

### 1. socket buffer는 큐잉 모델의 일부다

socket buffer는 네트워크가 즉시 처리되지 못할 때 데이터를 보관한다.

- 송신 버퍼가 차면 `send()`가 block되거나 `EAGAIN`이 난다
- 수신 버퍼가 차면 상대가 더 보내는 속도를 줄여야 한다
- buffer는 네트워크 RTT와 앱 처리 속도의 차를 흡수한다

### 2. autotuning은 편하지만 만능이 아니다

Linux는 상황에 맞춰 buffer를 자동으로 키우려 한다.

- RTT가 길고 대역폭이 큰 링크에서 유리하다
- burst traffic에서 도움이 된다
- 하지만 과도하면 메모리와 지연이 숨겨질 수 있다

### 3. backpressure는 좋은 신호다

backpressure는 나쁜 현상이 아니라, 시스템이 더 느려져야 한다는 신호다.

- sender가 너무 빨리 밀어 넣는다
- receiver가 처리 속도를 못 따라간다
- 커널이 큐를 통해 양쪽 속도를 맞춘다

이 신호를 무시하면 앱 내부 큐, GC, 메모리 사용량만 커진다.

### 4. 작은 buffer는 latency, 큰 buffer는 memory를 건드린다

버퍼 크기와 지연은 단순 비례가 아니다.

- 작으면 throughput이 떨어질 수 있다
- 크면 큐가 길어져 hidden latency가 생길 수 있다
- 네트워크가 느린 것이 아니라 앱이 backpressure를 못 읽는 경우가 많다

## 실전 시나리오

### 시나리오 1: 전송량은 늘지 않았는데 memory 사용량이 커진다

가능한 원인:

- send buffer가 과도하게 커진다
- connection 수가 늘면서 per-socket buffer가 누적된다
- autotuning이 큰 링크 기준으로 확대된다

진단:

```bash
cat /proc/sys/net/ipv4/tcp_rmem
cat /proc/sys/net/ipv4/tcp_wmem
ss -m
```

### 시나리오 2: 느린 클라이언트가 전체 서버를 밀어낸다

가능한 원인:

- 송신 버퍼가 꽉 차고 워커가 막힌다
- backpressure를 무시한 채 write를 계속한다
- 비동기라도 큐가 무한히 커진다

대응:

- per-connection cap을 둔다
- `EAGAIN`을 정상 흐름으로 다룬다
- slow consumer를 분리한다

### 시나리오 3: 대역폭은 충분한데 p99가 튄다

가능한 원인:

- buffer가 너무 작아 syscall이 많다
- buffer가 너무 커서 queueing delay가 길다
- softirq와 wakeup 지연이 섞인다

이 경우는 [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)도 같이 본다.

## 코드로 보기

### 소켓 버퍼 힌트 주기

```c
int size = 1 << 20;
setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size));
setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));
```

### 현재 소켓 buffer 상태 보기

```bash
ss -m
```

### TCP 자동 조정 범위 확인

```bash
sysctl net.ipv4.tcp_rmem
sysctl net.ipv4.tcp_wmem
sysctl net.ipv4.tcp_mem
```

### backpressure를 읽는 의사 코드

```c
ssize_t n = send(fd, buf, len, MSG_NOSIGNAL);
if (n < 0 && errno == EAGAIN) {
    // socket buffer full, stop producing
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 작은 buffer | 메모리 절약 | throughput이 떨어질 수 있다 | low-latency, small payload |
| 큰 buffer | burst 흡수에 유리 | queueing delay가 숨는다 | high throughput |
| autotuning | 운영이 편하다 | 예측이 어려울 수 있다 | 일반 TCP 서버 |
| 명시적 backpressure | 큐 폭주를 막는다 | 구현이 어렵다 | 고부하 비동기 서버 |

## 꼬리질문

> Q: socket buffer를 키우면 항상 더 좋아지나요?
> 핵심: 아니다. 큐가 길어져 지연이 숨을 수 있다.

> Q: backpressure는 왜 중요한가요?
> 핵심: 생산 속도를 소비 속도에 맞추지 않으면 내부 큐가 터지기 때문이다.

> Q: autotuning은 무엇을 해주나요?
> 핵심: 상황에 맞게 수신/송신 버퍼를 조정해 throughput을 돕는다.

> Q: `EAGAIN`은 실패인가요?
> 핵심: 비동기/논블로킹 흐름에서는 정상적인 흐름 신호다.

## 한 줄 정리

socket buffer autotuning은 네트워크 속도 차를 완충하지만, 운영에서는 backpressure를 읽고 큐가 과도하게 커지지 않도록 제어하는 것이 더 중요하다.
