# Timerfd, Epoll Timer Integration

> 한 줄 요약: timerfd를 epoll에 넣으면 I/O와 timer를 같은 이벤트 루프로 다룰 수 있어 timeout, periodic task, backoff를 한 경로로 통합하기 쉽다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Clocksource, Timer Resolution, Jitter](./clocksource-timer-resolution-jitter.md)
> - [monotonic clock, wall clock, timeout, deadline](./monotonic-clock-wall-clock-timeout-deadline.md)
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [Run Queue, Load Average, CPU Saturation](./run-queue-load-average-cpu-saturation.md)
> - [softirq, hardirq, Latency Server Debugging](./softirq-hardirq-latency-server-debugging.md)

> retrieval-anchor-keywords: timerfd, epoll timer, CLOCK_MONOTONIC, EPOLLIN, one-shot timer, periodic timer, event loop integration, timeout wheel

## 핵심 개념

`timerfd`는 타이머 만료를 file descriptor로 표현하는 장치다. 이를 `epoll`에 등록하면 I/O 이벤트와 timer 이벤트를 같은 루프로 처리할 수 있다.

- `timerfd`: 타이머를 fd로 표현한다
- `epoll`: I/O와 timer 이벤트를 함께 기다릴 수 있다
- `CLOCK_MONOTONIC`: timeout에 주로 쓰는 기준이다

왜 중요한가:

- timer와 I/O 경로를 분리하지 않아도 된다
- event loop 설계가 단순해진다
- periodic job, retry, timeout을 한 구조로 묶을 수 있다

이 문서는 [Clocksource, Timer Resolution, Jitter](./clocksource-timer-resolution-jitter.md)와 [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)를 이벤트 루프 관점에서 연결한다.

## 깊이 들어가기

### 1. timerfd는 timer를 event로 바꾼다

- timer expiration이 readable event처럼 보인다
- epoll loop에서 동일하게 처리할 수 있다
- timeout과 I/O completion을 같은 모델로 볼 수 있다

### 2. one-shot과 periodic을 같이 다룰 수 있다

- timeout 처리
- heartbeat
- retry backoff
- scheduled maintenance

### 3. event loop와 잘 맞는다

같은 thread에서 socket, timer, shutdown signal을 묶으면 상태 기계가 단순해진다.

### 4. jitter는 결국 wakeup 문제다

timerfd가 있어도 scheduler, IRQ, run queue 압박이 있으면 만료 시점과 실제 실행 시점이 어긋난다.

## 실전 시나리오

### 시나리오 1: timeout 관리가 여기저기 흩어져 있다

가능한 원인:

- timer와 I/O가 다른 경로로 처리된다
- retry logic이 복잡하다
- 종료 경로와 timeout 경로가 다르다

### 시나리오 2: periodic task가 drift한다

가능한 원인:

- event loop가 바쁘다
- wakeup jitter가 있다
- timerfd 만료 후 처리 지연이 있다

### 시나리오 3: timer를 넣었더니 epoll이 더 깔끔해졌다

가능한 원인:

- 동일한 반응 모델로 통합되었다
- timeout, I/O, shutdown을 한 루프에서 관리한다

## 코드로 보기

### timerfd 생성 감각

```c
int tfd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK);
```

### epoll 등록 모델

```c
epoll_ctl(epfd, EPOLL_CTL_ADD, tfd, &ev);
```

### 개념적 흐름

```text
timer expires
  -> timerfd becomes readable
  -> epoll wakes up
  -> event loop handles timer and I/O uniformly
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| timerfd + epoll | 루프가 단순하다 | jitter는 여전히 있다 | event loop server |
| 별도 timer thread | 구현이 분리된다 | 동기화가 복잡하다 | 특수 케이스 |
| busy polling timer | 반응이 빠르다 | CPU 비용이 높다 | 극저지연 |

## 꼬리질문

> Q: timerfd를 왜 epoll에 넣나요?
> 핵심: timer와 I/O를 같은 이벤트 모델로 통합할 수 있기 때문이다.

> Q: periodic task의 drift는 왜 생기나요?
> 핵심: 만료 시점과 실제 처리 시점이 scheduler와 pressure에 의해 어긋나기 때문이다.

> Q: CLOCK_MONOTONIC을 왜 쓰나요?
> 핵심: wall clock 변동에 덜 흔들리기 때문이다.

## 한 줄 정리

timerfd와 epoll을 결합하면 timeout과 주기 작업을 I/O와 같은 이벤트 모델로 처리할 수 있지만, 실제 wakeup jitter는 여전히 고려해야 한다.
