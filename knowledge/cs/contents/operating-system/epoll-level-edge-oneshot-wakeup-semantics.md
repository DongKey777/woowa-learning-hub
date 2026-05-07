---
schema_version: 3
title: epoll Level Edge ONESHOT Wakeup Semantics
concept_id: operating-system/epoll-level-edge-oneshot-wakeup-semantics
canonical: true
category: operating-system
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- epoll-level-edge
- oneshot-wakeup-semantics
- epoll-level-triggered
- edge-triggered-oneshot
aliases:
- epoll level triggered edge triggered oneshot
- EPOLLET EPOLLONESHOT
- EAGAIN drain discipline
- epoll wakeup semantics
- handler ownership model
- ready queue wakeup reduction
intents:
- comparison
- deep_dive
- troubleshooting
linked_paths:
- contents/operating-system/epoll-kqueue-io-uring.md
- contents/operating-system/io-models-and-event-loop.md
- contents/operating-system/thundering-herd-accept-wakeup.md
- contents/operating-system/eventfd-signalfd-epoll-control-plane-integration.md
- contents/operating-system/scheduler-wakeup-latency-runqlat-debugging.md
- contents/operating-system/proc-pid-fdinfo-epoll-runtime-debugging.md
confusable_with:
- operating-system/epoll-kqueue-io-uring
- operating-system/eventfd-signalfd-epoll-control-plane-integration
- operating-system/thundering-herd-accept-wakeup
expected_queries:
- epoll level-triggered edge-triggered EPOLLONESHOT은 어떻게 선택해?
- EPOLLET를 쓰면 EAGAIN까지 drain해야 하는 이유는?
- EPOLLONESHOT은 handler ownership model을 어떻게 바꿔?
- epoll wakeup semantics와 thundering herd 가능성을 비교해줘
contextual_chunk_prefix: |
  이 문서는 epoll LT, ET, EPOLLONESHOT 선택을 단순 API option이 아니라 wakeup 수,
  ready queue semantics, herd 가능성, EAGAIN까지 drain하는 discipline, handler ownership
  model을 결정하는 설계 선택으로 설명한다.
---
# epoll Level-Triggered, Edge-Triggered, ONESHOT Wakeup Semantics

> 한 줄 요약: `epoll`의 LT, ET, `EPOLLONESHOT` 선택은 단순 API 옵션이 아니라 wakeup 수, herd 가능성, drain discipline, handler ownership 모델을 결정하는 설계 선택이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [epoll, kqueue, io_uring](./epoll-kqueue-io-uring.md)
> - [I/O Models and Event Loop](./io-models-and-event-loop.md)
> - [Thundering Herd, Accept, Wakeup](./thundering-herd-accept-wakeup.md)
> - [eventfd, signalfd, Epoll Control-Plane Integration](./eventfd-signalfd-epoll-control-plane-integration.md)
> - [Scheduler Wakeup Latency, runqlat, Queueing Debugging](./scheduler-wakeup-latency-runqlat-debugging.md)

> retrieval-anchor-keywords: epoll level triggered, epoll edge triggered, EPOLLONESHOT, EPOLLET, EAGAIN drain, wakeup semantics, handler ownership, ready queue, wakeup reduction, epoll bugs

## 핵심 개념

`epoll`을 쓴다고 해서 wakeup 모델이 자동으로 안전해지는 것은 아니다. level-triggered(LT), edge-triggered(ET), `EPOLLONESHOT`는 각각 "언제 다시 깨울 것인가", "누가 그 fd를 책임질 것인가", "어느 정도까지 drain해야 하는가"를 다르게 정의한다.

- `level-triggered`: 읽을 것이 남아 있으면 계속 readiness를 다시 보게 한다
- `edge-triggered`: 상태가 바뀌는 순간의 edge를 중심으로 알린다
- `EPOLLONESHOT`: 이벤트 한 번 전달 후 재등록 전까지 다시 주지 않는다

왜 중요한가:

- 잘못 쓰면 readiness가 남았는데도 worker가 다시 안 깨어나 stall이 생긴다
- 반대로 너무 자주 깨우면 herd와 wakeup churn이 생긴다
- multi-worker event loop에서 ownership 모델을 명확히 하지 않으면 race가 커진다

## 깊이 들어가기

### 1. LT는 단순하지만 반복 wakeup 비용을 감수한다

LT는 "아직 읽을 수 있으면 또 알려준다"는 감각이라 구현이 비교적 단순하다.

- drain을 덜 해도 다음에 다시 깨워 준다
- 부분 처리 코드가 있어도 복구 가능성이 높다
- 하지만 readiness가 오래 남으면 같은 fd로 반복 wakeup이 생길 수 있다

그래서 LT는 safety에 유리하지만, high-fd/high-burst 환경에서는 wakeup 비용이 커질 수 있다.

### 2. ET는 wakeup을 줄이는 대신 drain discipline이 필요하다

ET는 상태 변화 시점에만 이벤트를 주는 성격이라, 읽기/쓰기 가능한 구간을 최대한 소비해야 한다.

- `read`/`accept`/`recv`는 보통 `EAGAIN`까지 반복한다
- 일부만 읽고 빠지면 남은 readiness가 묻힐 수 있다
- 버그가 나면 "가끔 요청이 멈춘다"는 형태로 보인다

즉 ET의 핵심은 옵션이 아니라 "handler가 끝까지 비우는가"다.

### 3. `EPOLLONESHOT`는 ownership transfer 모델이다

`EPOLLONESHOT`는 그 fd의 이벤트를 한 worker가 받아 처리한 뒤, 끝나면 다시 `epoll_ctl(...MOD...)`로 arm하는 모델에 가깝다.

- 동시에 여러 worker가 같은 fd를 건드리는 것을 줄일 수 있다
- per-connection ownership을 명확히 하기에 좋다
- 하지만 rearm 누락이 치명적이다

그래서 `EPOLLONESHOT`는 "중복 wakeup 줄이기"보다 "한 시점의 owner를 명확히 정하기"로 이해하는 편이 정확하다.

### 4. wakeup semantics는 scheduler 비용과 바로 연결된다

어떤 모드를 택하든 결국 질문은 같다.

- 불필요하게 많이 깨우는가
- 깬 worker가 실제 일을 끝까지 처리하는가
- 같은 fd를 두 worker가 번갈아 만지는가

즉 epoll 옵션은 단순 I/O 옵션이 아니라 scheduler wakeup 설계다.

## 실전 시나리오

### 시나리오 1: ET로 바꾼 뒤 가끔 연결이 멈춘다

가능한 원인:

- handler가 `EAGAIN`까지 drain하지 않았다
- partial write/read 후 재arm 조건이 모호하다
- accept loop도 한 번만 돌고 빠진다

진단:

```bash
strace -ff -ttT -e trace=epoll_wait,read,write,accept4 -p <pid>
sudo offcputime-bpfcc -p <pid> 15
```

판단 포인트:

- `epoll_wait`는 깨웠는데 남은 data를 못 비우는가
- `EAGAIN` 전까지 loop하지 않는 경로가 있는가
- ready fd가 ownership 없이 여러 worker로 흔들리는가

### 시나리오 2: LT에서는 안전한데 burst 때 CPU가 wakeup에 많이 쓴다

가능한 원인:

- readiness가 남아 같은 fd를 반복 보고 있다
- multi-worker가 같은 ready set을 공유한다
- partial handling과 requeue가 잦다

대응 감각:

- ET 또는 `EPOLLONESHOT` 전환을 검토한다
- 단, drain discipline과 rearm discipline을 먼저 준비한다

### 시나리오 3: `EPOLLONESHOT` 도입 후 가끔 영원히 조용한 소켓이 생긴다

가능한 원인:

- rearm 누락
- error/timeout branch에서 `epoll_ctl(...MOD...)`를 안 했다
- owner handoff 상태 기계가 복잡하다

이 경우는 "epoll 버그"보다 ownership lifecycle bug인 경우가 많다.

## 코드로 보기

### LT 감각

```c
ev.events = EPOLLIN;
```

### ET 감각

```c
ev.events = EPOLLIN | EPOLLET;
// handler must drain until EAGAIN
```

### ONESHOT 감각

```c
ev.events = EPOLLIN | EPOLLONESHOT;
// after handling, rearm with EPOLL_CTL_MOD
```

### mental model

```text
LT
  -> keep telling while ready remains

ET
  -> tell only when state changes
  -> handler must drain

ONESHOT
  -> tell one owner once
  -> owner must rearm
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| LT | 구현이 단순하고 복원력이 있다 | wakeup churn이 커질 수 있다 | simple or lower-risk loops |
| ET | wakeup 수를 줄이기 좋다 | drain discipline 실패 시 stall이 생긴다 | high-concurrency servers |
| `EPOLLONESHOT` | fd ownership을 명확히 하기에 좋다 | rearm 누락이 치명적이다 | multi-worker per-fd ownership |
| shared LT + many workers | 단순해 보인다 | herd와 duplicate handling 가능성이 크다 | 피하는 편이 좋다 |

## 꼬리질문

> Q: ET에서 왜 `EAGAIN`까지 읽으라고 하나요?
> 핵심: edge 이후 readiness가 남아도 다시 안 알려 줄 수 있으므로, 가능한 데이터를 끝까지 소비해야 하기 때문이다.

> Q: `EPOLLONESHOT`는 왜 쓰나요?
> 핵심: 한 시점에 한 worker가 해당 fd를 책임지게 만들어 duplicate handling과 ownership race를 줄이기 위해서다.

> Q: LT가 더 안전하면 ET는 왜 쓰나요?
> 핵심: burst 환경에서 readiness 반복 wakeup을 줄여 wakeup churn과 herd를 완화하려는 목적이 크기 때문이다.

## 한 줄 정리

`epoll` 모드 선택은 I/O API 취향이 아니라, "누가 언제 얼마나 자주 깨어나고 누가 fd를 소유하는가"를 정하는 wakeup 설계다.
