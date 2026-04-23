# eventfd, signalfd, Epoll Control-Plane Integration

> 한 줄 요약: `eventfd`와 `signalfd`를 `epoll`에 넣으면 shutdown, reload, cross-thread wakeup 같은 제어 흐름을 소켓 I/O와 같은 이벤트 모델로 다룰 수 있어 event loop 운영이 단단해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [I/O Models and Event Loop](./io-models-and-event-loop.md)
> - [Timerfd, Epoll Timer Integration](./timerfd-epoll-timer-integration.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [pipe, socketpair, eventfd, memfd IPC Selection](./pipe-socketpair-eventfd-memfd-ipc-selection.md)
> - [Signals, Process Supervision](./signals-process-supervision.md)
> - [O_CLOEXEC, FD Inheritance, Exec-Time Leaks](./o-cloexec-fd-inheritance-exec-leaks.md)

> retrieval-anchor-keywords: eventfd, signalfd, epoll, wakeup fd, control plane event loop, signal fd, self-pipe alternative, event loop shutdown, cross-thread notification, EFD_CLOEXEC, SFD_CLOEXEC

## 핵심 개념

event loop 서버는 보통 소켓 read/write readiness만 처리한다고 생각하기 쉽다. 하지만 실제 운영에서는 종료 요청, 설정 리로드, worker wakeup, 큐에 새 일이 들어왔다는 알림도 같은 중요도를 가진다. `eventfd`와 `signalfd`는 이런 제어 신호를 file descriptor로 바꿔 `epoll`에서 함께 처리하게 해 준다.

- `eventfd`: 64비트 counter 기반의 notification fd다
- `signalfd`: signal delivery를 fd readable event로 받게 해 준다
- `epoll`: data plane I/O와 control plane 이벤트를 한 루프에서 기다릴 수 있다
- `timerfd`: 시간 기반 이벤트를 같은 모델로 넣는 도구다

왜 중요한가:

- async signal handler 복잡도를 줄이고 제어 경로를 loop 안으로 끌어들일 수 있다
- 다른 스레드가 event loop를 깨워야 할 때 pipe보다 단순한 경로를 만들 수 있다
- shutdown, reload, timeout, socket I/O를 하나의 상태 기계로 다루기 쉬워진다

## 깊이 들어가기

### 1. eventfd는 "일이 생겼다"를 fd readable로 바꾼다

다른 스레드나 프로세스가 event loop에게 "지금 깨어나서 큐를 봐라"라고 알려야 할 때 `eventfd`가 유용하다.

- work queue에 작업을 넣고 `eventfd`에 write한다
- epoll loop가 깨어나 queue를 drain한다
- self-pipe trick보다 의미가 분명하고 counter semantics가 있다

payload 자체를 실어 나를 channel이 필요하다면 `pipe`나 `socketpair`, 큰 공유 데이터가 필요하다면 `memfd`를 같이 고려하는 편이 맞다.

이 패턴은 thread pool과 single-threaded reactor를 섞을 때 특히 깔끔하다.

### 2. signalfd는 signal을 비동기 handler 밖으로 꺼내 준다

일반 signal handler는 언제 어디서 끼어들지 모르고, 안전하게 할 수 있는 일이 제한적이다. `signalfd`는 대상 signal을 block한 뒤, 그 signal이 fd 이벤트로 들어오게 만든다.

- `SIGTERM`, `SIGHUP`, `SIGCHLD` 같은 제어 signal을 loop 안에서 읽을 수 있다
- graceful shutdown, reload, child reap 경로를 한 루프에서 관리하기 쉬워진다
- signal handler 안에서 복잡한 로직을 돌리는 위험을 줄인다

핵심은 "signal을 없애는 것"이 아니라 "signal을 제어된 이벤트 채널로 받는 것"이다.

### 3. timerfd, eventfd, signalfd는 역할이 다르다

셋 다 fd지만 성격은 다르다.

- `timerfd`: 시간이 지났음을 알려준다
- `eventfd`: 사용자 공간이나 일부 커널 경로가 임의 wakeup을 보낸다
- `signalfd`: 프로세스 제어 signal을 읽기 가능한 이벤트로 바꾼다

셋을 같이 쓰면 event loop의 data plane과 control plane을 거의 모두 fd 모델로 통일할 수 있다.

### 4. 기본값은 non-blocking + cloexec가 안전하다

이 fd들도 결국 일반 descriptor이므로 lifecycle 관리가 필요하다.

- `EFD_NONBLOCK`, `SFD_NONBLOCK`으로 loop가 예기치 않게 막히지 않게 한다
- `EFD_CLOEXEC`, `SFD_CLOEXEC`로 helper process로 새지 않게 한다
- multi-process worker 구조라면 어느 프로세스가 어떤 control fd를 소유하는지 분명히 해야 한다

즉 제어 채널도 결국 fd hygiene 문제다.

## 실전 시나리오

### 시나리오 1: epoll 서버가 `SIGTERM` 처리만 되면 종료 구조가 훨씬 단순해진다

가능한 원인:

- 현재는 async signal handler에서 flag만 바꾸고 곳곳에서 폴링한다
- shutdown, drain, child reap, timeout 경로가 흩어져 있다
- loop 안에서 제어 이벤트를 직접 처리하고 싶다

대응 감각:

- 종료 대상 signal을 block한다
- `signalfd`를 epoll에 등록한다
- loop에서 읽어 graceful shutdown 상태 기계로 넘긴다

### 시나리오 2: 다른 스레드가 queue에 작업을 넣었는데 loop를 깨우기 어렵다

가능한 원인:

- 조건변수와 epoll loop가 따로 놀고 있다
- self-pipe를 쓰지만 의미가 불분명하고 관리가 지저분하다
- wakeup 경로가 많아지며 lost wakeup을 걱정한다

대응 감각:

- producer가 queue push 후 `eventfd`에 write한다
- consumer loop는 `eventfd` readable 시 queue를 drain한다
- wakeup과 queue semantics를 한 쌍으로 문서화한다

### 시나리오 3: timer, signal, socket, cross-thread wakeup이 모두 따로 논다

이 경우는 코드보다 운영이 먼저 무너진다.

- timeout은 timer thread
- shutdown은 signal handler
- queue wakeup은 pipe
- socket은 epoll

이렇게 흩어지면 race와 종료 순서 버그가 늘어난다. eventfd/signalfd/timerfd를 합치면 최소한 "이벤트를 어디서 받는가"는 하나로 모을 수 있다.

## 코드로 보기

### eventfd 등록 예시

```c
int efd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
epoll_ctl(epfd, EPOLL_CTL_ADD, efd, &ev);
```

### signalfd 등록 예시

```c
sigset_t mask;
sigemptyset(&mask);
sigaddset(&mask, SIGTERM);
sigaddset(&mask, SIGHUP);
sigprocmask(SIG_BLOCK, &mask, NULL);

int sfd = signalfd(-1, &mask, SFD_NONBLOCK | SFD_CLOEXEC);
epoll_ctl(epfd, EPOLL_CTL_ADD, sfd, &ev);
```

### mental model

```text
socket ready
timer expired
signal arrived
worker pushed work
  -> all become epoll-readable events
  -> one loop dispatches data plane and control plane together
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| `eventfd`/`signalfd`/`timerfd` 통합 | 제어 경로가 한 loop에 모인다 | 설계와 ownership 정리가 필요하다 | event loop 서버 |
| async signal handler + 별도 wakeup | 익숙한 구현이다 | race와 shutdown 복잡도가 커진다 | 작은 프로그램 |
| self-pipe trick | 널리 알려져 있다 | 의미가 덜 직접적이고 pipe 관리가 필요하다 | 레거시 호환 |
| dedicated control thread | 관심사를 나누기 쉽다 | 동기화와 lifecycle이 더 복잡해진다 | 특수 제어 경로 |

## 꼬리질문

> Q: `signalfd`를 쓰면 signal이 없어지나요?
> 핵심: 아니다. signal은 여전히 오지만, block된 signal을 fd 이벤트로 읽게 만드는 방식이다.

> Q: `eventfd`는 언제 유용한가요?
> 핵심: 다른 스레드나 프로세스가 event loop를 깨워서 queue나 제어 상태를 확인하게 할 때 유용하다.

> Q: `timerfd`와 `eventfd`는 같은 용도인가요?
> 핵심: 아니다. 전자는 시간 경과, 후자는 임의 wakeup/notification이라는 점에서 역할이 다르다.

## 한 줄 정리

`eventfd`와 `signalfd`는 event loop 서버의 제어 경로를 "특별한 예외 처리"가 아니라 "같은 fd 이벤트"로 끌어와 shutdown과 wakeup을 더 예측 가능하게 만든다.
