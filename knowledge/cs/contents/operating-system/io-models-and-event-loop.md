# I/O Models and Event Loop

> 한 줄 요약: blocking, non-blocking, synchronous, asynchronous는 서로 다른 축이고, event loop는 readiness와 backpressure를 하나의 흐름으로 다루는 운영 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [Timerfd, Epoll Timer Integration](./timerfd-epoll-timer-integration.md)
> - [Socket Accept Queue, Kernel Diagnostics](./socket-accept-queue-kernel-diagnostics.md)
> - [File Descriptor, Socket, Syscall Cost, and Server Impact](./file-descriptor-socket-syscall-cost-server-impact.md)
> - [Softirq, Hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)
> - [eBPF, perf, strace, and Production Tracing](./ebpf-perf-strace-production-tracing.md)

> retrieval-anchor-keywords: blocking I/O, non-blocking I/O, synchronous I/O, asynchronous I/O, event loop, readiness, backpressure, epoll_wait, timerfd, off-CPU

## 핵심 개념

I/O 모델은 "어떻게 기다릴 것인가"를 정하는 설계다. 서버에서는 단순한 API 스타일이 아니라, 스레드가 어디서 block되고 어디서 wakeup되는지가 성능을 결정한다.

- `blocking I/O`: 호출한 스레드가 I/O 완료까지 기다린다
- `non-blocking I/O`: 아직 준비되지 않았더라도 즉시 돌아온다
- `event loop`: readiness 이벤트를 모아 순차적으로 처리한다
- `backpressure`: 소비 속도보다 생산 속도가 빠를 때 속도를 낮추는 신호다

왜 중요한가:

- thread-per-request는 단순하지만 스레드와 context switch 비용이 든다
- event loop는 적은 스레드로 많은 연결을 다룰 수 있다
- 실제 병목은 I/O 자체보다 wakeup, backlog, timer, off-CPU 대기일 수 있다

이 문서는 [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md), [Timerfd, Epoll Timer Integration](./timerfd-epoll-timer-integration.md), [Socket Accept Queue, Kernel Diagnostics](./socket-accept-queue-kernel-diagnostics.md)와 함께 보면 좋다.

## 깊이 들어가기

### 1. blocking/non-blocking과 sync/async는 다르다

- blocking/non-blocking: 호출한 스레드가 기다리느냐
- synchronous/asynchronous: 완료 책임을 누가 지느냐

이 둘을 섞어 말하면 운영 모델을 잘못 이해하게 된다.

### 2. event loop는 readiness 기반이다

event loop는 "지금 읽을 수 있나/쓸 수 있나"를 기준으로 동작한다.

- `epoll_wait`로 준비된 이벤트를 받는다
- 준비되면 처리한다
- 아직 안 됐으면 다른 일을 한다

### 3. backpressure는 선택이 아니라 필요다

생산 속도가 소비 속도를 넘으면 큐가 무한히 커질 수 있다.

- socket send buffer
- internal job queue
- retry queue

이런 곳에 backpressure가 없으면 tail latency가 커진다.

### 4. timer는 event loop의 일부다

timeout과 periodic 작업은 timerfd로 같은 루프에 넣을 수 있다. 그러면 I/O와 타이머를 같은 상태 기계로 관리할 수 있다.

## 실전 시나리오

### 시나리오 1: 스레드를 늘렸더니 latency가 더 나빠진다

가능한 원인:

- blocking I/O 때문에 스레드가 많이 묶인다
- context switch와 run queue 압박이 커진다
- backpressure 없이 큐만 커진다

진단:

```bash
vmstat 1
top -H -p <pid>
strace -f -ttT -p <pid>
```

### 시나리오 2: event loop는 CPU가 낮은데도 느리다

가능한 원인:

- off-CPU wait가 길다
- backlog가 밀린다
- timer wakeup이나 softirq가 늦다

진단:

```bash
sudo offcputime-bpfcc -p <pid> 30
sudo runqlat-bpfcc -p <pid> 30
ss -ltnp
```

### 시나리오 3: non-blocking으로 바꿨는데 코드만 복잡해졌다

가능한 원인:

- readiness와 state machine을 분리하지 않았다
- retry/backpressure 설계가 없다
- timer와 I/O가 다른 경로로 흩어져 있다

이 경우는 [Timerfd, Epoll Timer Integration](./timerfd-epoll-timer-integration.md)과 같이 보면 좋다.

## 코드로 보기

### blocking I/O의 감각

```c
ssize_t n = read(fd, buf, sizeof(buf)); // may block until data arrives
```

### non-blocking I/O의 감각

```c
int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

### event loop의 감각

```c
for (;;) {
    int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);
    for (int i = 0; i < n; i++) {
        handle_ready_event(events[i]);
    }
}
```

### timerfd와 함께 쓰는 경우

```c
int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK);
epoll_ctl(epfd, EPOLL_CTL_ADD, tfd, &ev);
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| blocking I/O | 단순하다 | 스레드가 묶인다 | 작은 도구, 단순 서버 |
| non-blocking I/O | 스레드 효율이 좋다 | 상태 기계가 복잡하다 | 고동시성 서버 |
| event loop | 수만 연결에 적합 | 디버깅이 어렵다 | 네트워크 서버 |
| io_uring | syscall 비용을 줄인다 | 학습/호환성 비용 | 최신 Linux 고성능 서버 |

## 꼬리질문

> Q: blocking과 synchronous는 같은가요?
> 핵심: 아니다. 다른 축이다.

> Q: event loop가 왜 빠를 수 있나요?
> 핵심: 적은 스레드로 readiness를 처리하고 context switch를 줄이기 때문이다.

> Q: non-blocking I/O만으로 충분한가요?
> 핵심: 아니다. backpressure와 timer, 상태 기계 설계가 같이 필요하다.

## 한 줄 정리

I/O 모델은 waiting과 completion을 어떻게 다룰지 정하는 운영 설계이며, event loop는 readiness와 backpressure를 한 흐름으로 묶어 처리하는 방식이다.
