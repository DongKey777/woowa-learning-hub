---
schema_version: 3
title: Bounded Queue Policy Primer
concept_id: data-structure/bounded-queue-policy-primer
canonical: true
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- bounded-queue-full-policy
- backpressure-vs-blocking
- rejection-overwrite-buffer-contract
aliases:
- bounded queue policy
- bounded buffer policy
- full queue policy
- reject overwrite blocking backpressure
- queue가 꽉 찼을 때
- backpressure vs blocking
- fixed size queue policy
- ring buffer overwrite
symptoms:
- bounded queue를 만들면서 꽉 찼을 때 reject, overwrite, blocking, backpressure 계약을 정하지 않고 있어
- blocking과 backpressure를 같은 말처럼 이해하고 있어
- overwrite를 써도 FIFO 의미가 그대로 유지된다고 오해하고 있어
intents:
- definition
- comparison
- design
prerequisites:
- data-structure/queue-vs-deque-vs-priority-queue-primer
- operating-system/sync-async-blocking-nonblocking-basics
next_docs:
- data-structure/circular-queue-vs-ring-buffer
- data-structure/ring-buffer
- data-structure/bounded-mpmc-queue
- language/executor-sizing-queue-rejection-policy
linked_paths:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/circular-queue-vs-ring-buffer-primer.md
- contents/data-structure/ring-buffer.md
- contents/data-structure/lock-free-spsc-ring-buffer.md
- contents/data-structure/bounded-mpmc-queue.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
confusable_with:
- data-structure/circular-queue-vs-ring-buffer
- data-structure/ring-buffer
- system-design/job-queue-design
- language/executor-sizing-queue-rejection-policy
forbidden_neighbors: []
expected_queries:
- bounded queue가 꽉 찼을 때 reject, overwrite, blocking, backpressure 중 무엇을 골라야 해?
- blocking은 local thread가 기다리는 것이고 backpressure는 상류를 늦추는 계약인 이유가 뭐야?
- ring buffer overwrite 정책은 FIFO queue 의미를 어떻게 바꿔?
- queue full에서 새 항목과 오래된 항목 중 무엇을 버릴지 어떻게 결정해?
- Java ThreadPoolExecutor queue와 rejection policy는 bounded queue 정책과 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 bounded queue policy beginner primer로, full queue에서 reject, overwrite, blocking, backpressure 중 누가 양보하는지 계약을 먼저 정하게 돕는다.
  queue가 꽉 찼을 때, reject vs overwrite, blocking vs backpressure, fixed size buffer, ring buffer overwrite 같은 자연어 질문이 본 문서에 매핑된다.
---
# Bounded Queue Policy Primer

> 한 줄 요약: 고정 크기 queue/buffer가 꽉 찼을 때는 `reject`, `overwrite`, `blocking`, `backpressure` 중 어떤 계약을 택하는지가 구조 선택만큼 중요하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: bounded queue policy, bounded buffer policy, queue가 꽉 찼을 때, 버퍼가 가득 찼을 때, bounded queue 처음 배우는데, bounded queue 큰 그림, reject overwrite blocking backpressure 차이, blocking vs backpressure, reject vs overwrite, queue full when to reject, overwrite 언제 쓰는지, backpressure가 뭐예요
> 관련 문서:
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
> - [Ring Buffer](./ring-buffer.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
> - [Bounded MPMC Queue](./bounded-mpmc-queue.md)
> - [Executor Sizing, Queue, Rejection Policy](../language/java/executor-sizing-queue-rejection-policy.md)
>
> retrieval-anchor-keywords: bounded queue policy, full queue policy, reject policy, overwrite policy, blocking queue policy, backpressure policy, bounded queue first question, queue full mental model, 왜 bounded queue policy를 정해야 하나요, 언제 reject를 쓰나요, 언제 blocking을 쓰나요, 언제 backpressure를 거나요, 처음 큐 정책이 헷갈릴 때, 고정 크기 큐 정책

## 먼저 그림부터 잡기

처음 배우는 단계라면 이 문서는 "bounded queue가 뭐예요?"보다
"**큐가 꽉 찼을 때 왜 정책을 먼저 정해야 해요?**"라는 질문에 답하는 입문 엔트리로 보면 된다.

고정 크기 queue는 언젠가 반드시 찬다.
그때 질문은 "더 넣을 수 있나?"가 아니라 **"누가 양보하나?"**다.

- 새로 들어온 요청이 양보하면 `reject`
- 이미 들어 있던 오래된 항목이 양보하면 `overwrite`
- producer가 기다리면 `blocking`
- producer보다 더 위 단계가 속도를 늦추면 `backpressure`

같은 capacity `3`짜리 queue가 `[A, B, C]`로 가득 찬 상태에서 새 항목 `D`가 오면 결과는 이렇게 갈린다.

| 정책 | 즉시 무슨 일이 일어나나 | 결과 예시 |
|---|---|---|
| Reject | `D`를 받지 않는다 | queue는 `[A, B, C]`, `D` 실패 |
| Overwrite | 보통 가장 오래된 항목을 지우고 `D`를 넣는다 | queue는 `[B, C, D]` |
| Blocking | 빈 칸이 생길 때까지 `D`를 넣는 쪽이 기다린다 | 소비 후 `[B, C, D]` 같은 상태로 진행 |
| Backpressure | 상류에 "지금 더 보내지 말라"는 신호를 준다 | `D` 생산 자체가 늦춰지거나 배치가 줄어듦 |

## 빠른 비교표

| 정책 | 데이터 유실 | producer 대기 | FIFO 보존감 | 잘 맞는 상황 |
|---|---|---|---|---|
| Reject | 새 항목 유실 가능 | 없음 | 기존 queue는 그대로 유지 | caller가 retry/drop을 직접 결정할 수 있을 때 |
| Overwrite | 기존 오래된 항목 유실 가능 | 없음 | 오래된 순서 보존이 깨질 수 있음 | 최신 `N`개가 더 중요한 상태/샘플 버퍼 |
| Blocking | 원칙적으로 없음 | 있음 | 비교적 잘 유지 | 유실이 어렵고 producer thread가 기다려도 될 때 |
| Backpressure | 구현에 따라 다름 | 선택적 | queue 밖의 흐름 제어가 핵심 | 여러 stage가 연결된 파이프라인, 스트리밍, 네트워크 ingress |

초보자가 제일 많이 헷갈리는 한 줄은 이것이다.

> `blocking`은 queue 한 칸 앞에서 기다리는 **로컬 동작**이고,
> `backpressure`는 상류 전체에 속도 조절을 전파하는 **시스템 계약**이다.

## 1. Reject: "지금은 못 받는다"

`reject`는 full이면 새 항목을 그냥 받지 않는다.
구현에서는 `offer()`가 `false`를 반환하거나 예외를 던지는 식이 많다.

이 정책이 맞는 이유는 단순하다.

- 이미 queue 안에 들어온 일감을 더 우선시한다
- producer를 멈추고 싶지는 않다
- caller가 retry, drop, sampling 중 무엇을 할지 결정할 수 있다

잘 맞는 예시는 다음과 같다.

- best-effort telemetry
- 로그 샘플링 버퍼
- 상위 호출자가 재시도 budget을 따로 가진 ingress

주의할 점:

- reject는 "아무 일도 안 일어났다"가 아니다
- drop counter, reject rate, queue fill ratio를 같이 보지 않으면 유실이 숨어버린다

## 2. Overwrite: "가장 오래된 것을 밀어낸다"

`overwrite`는 새 항목을 받는 대신 기존 항목 하나를 포기한다.
ring buffer에서는 보통 **가장 오래된 항목을 덮어쓰는 정책**으로 설명한다.

이 정책이 맞는 상황은 명확하다.

- 최신 상태가 오래된 상태보다 더 중요하다
- "최근 `N`개"만 유지하면 된다
- 오래된 샘플이 조금 사라져도 전체 의미가 크게 깨지지 않는다

잘 맞는 예시는 다음과 같다.

- 센서 최신값 버퍼
- UI 최근 상태 스냅샷
- 디버그용 최근 이벤트 tail

주의할 점:

- strict FIFO queue라는 감각은 약해진다
- 무엇을 덮어쓰는지 반드시 계약으로 써야 한다
- 결제 이벤트, 주문, 감사 로그처럼 빠지면 안 되는 데이터에는 위험하다

## 3. Blocking: "빈 칸이 생길 때까지 기다린다"

`blocking`은 full이면 producer가 멈춰서 space가 생기길 기다린다.

이 정책이 자연스러운 경우는 이렇다.

- 데이터 유실이 어려운 handoff다
- producer thread가 기다려도 시스템이 버틸 수 있다
- queue 길이 자체가 시스템 속도를 자연스럽게 제한해야 한다

잘 맞는 예시는 다음과 같다.

- 내부 worker handoff queue
- 배치 쓰기 큐
- 한 단계가 느려지면 앞 단계도 함께 늦어져야 하는 파이프라인

하지만 `blocking`은 공짜가 아니다.

- thread pool 안에서 막히면 starvation이 생길 수 있다
- lock 순서가 나쁘면 deadlock 위험이 생긴다
- tail latency가 중요하면 긴 대기가 시스템 전체를 흔들 수 있다

즉 "유실이 싫다"만으로 blocking을 고르면 부족하다.
**producer가 진짜로 기다려도 되는 실행 문맥인지**를 같이 봐야 한다.

## 4. Backpressure: "상류가 덜 밀어 넣게 만든다"

`backpressure`는 full queue 앞에서만 처리하는 정책이 아니다.
더 위 단계에 "`consumer`가 따라가지 못하니 생산 속도를 낮춰라"라고 알려 주는 흐름 제어다.

형태는 여러 가지다.

- credit / permit 기반 생산량 제한
- 읽기 자체를 잠시 멈춤
- 배치 크기 축소
- `reject` 후 caller가 재시도 간격을 늘림
- async await나 rate limit으로 상류를 늦춤

핵심은 이것이다.

- `blocking`은 보통 한 thread가 멈춘다
- `backpressure`는 시스템 전체가 덜 만든다

그래서 네트워크 ingress, 스트리밍 파이프라인, 비동기 stage 연결에서는
local queue 하나만 막기보다 backpressure를 먼저 설계하는 편이 자연스럽다.

## 무엇을 먼저 고를까

아래 질문 네 개면 대부분 빠르게 좁혀진다.

1. 새 항목이나 오래된 항목이 일부 사라져도 되는가?
2. 사라져도 된다면 최신값이 더 중요한가, 이미 받은 항목이 더 중요한가?
3. producer가 기다려도 안전한 thread / coroutine 문맥인가?
4. 문제를 queue 하나에서 끝낼 것인가, 상류 생산 속도까지 제어할 것인가?

짧게 매핑하면 이렇다.

| 질문에 대한 답 | 먼저 의심할 정책 |
|---|---|
| 이미 받은 항목은 지키고 새 요청은 caller가 판단해야 한다 | Reject |
| 최근 상태만 남기면 된다 | Overwrite |
| 유실이 어렵고 producer가 기다려도 된다 | Blocking |
| 여러 stage를 함께 늦춰야 한다 | Backpressure |

## 자주 하는 오해

1. `backpressure = blocking`이라고 외운다.
   blocking은 구현 한 방식일 뿐이고, backpressure는 더 넓은 흐름 제어 개념이다.

2. `overwrite`를 써도 queue semantics가 그대로라고 생각한다.
   오래된 항목을 버리는 순간 strict FIFO 보존은 깨질 수 있다.

3. `reject`는 실패한 구현이라고 생각한다.
   아니다. drop을 caller에 명시적으로 노출하는 것도 하나의 계약이다.

4. `blocking`이면 데이터가 절대 안 사라진다고 생각한다.
   timeout, cancellation, process crash가 끼면 결국 다른 층위에서 유실 처리가 필요할 수 있다.

## 다음 문서로 이어가기

- 원형 배열 queue 구현과 시스템형 ring buffer 문맥을 먼저 분리하고 싶다면 [Circular Queue vs Ring Buffer Primer](./circular-queue-vs-ring-buffer-primer.md)
- 일반적인 bounded buffer 감각과 운영 제약을 더 보고 싶다면 [Ring Buffer](./ring-buffer.md)
- producer 1개 / consumer 1개 저지연 경로로 내려가려면 [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
- 다중 producer / consumer에서 capacity와 backpressure를 어떻게 구조화하는지 보려면 [Bounded MPMC Queue](./bounded-mpmc-queue.md)
- Java 서비스에서 이 개념이 `ThreadPoolExecutor`의 queue와 rejection policy로 어떻게 이어지는지 보려면 [Executor Sizing, Queue, Rejection Policy](../language/java/executor-sizing-queue-rejection-policy.md)

## 한 줄 정리

고정 크기 queue의 핵심 질문은 "언제 차는가"가 아니라 **"꽉 찼을 때 새 항목, 오래된 항목, producer, 상류 중 누가 양보하나"**다.
