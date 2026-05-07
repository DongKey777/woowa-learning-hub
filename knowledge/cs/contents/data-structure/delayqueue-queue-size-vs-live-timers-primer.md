---
schema_version: 3
title: DelayQueue Queue Size vs Live Timers Primer
concept_id: data-structure/delayqueue-queue-size-vs-live-timers-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 87
mission_ids:
- missions/roomescape
review_feedback_tags:
- delayqueue-observability
- queue-size-vs-live-work
- stale-timer-metrics
aliases:
- DelayQueue size live timers
- queue size not live work
- stale timer count
- cancelled timer queue size
- DelayQueue queue size overcount
- live scheduled work vs queue entries
- timer queue retention metrics
symptoms:
- DelayQueue.size가 커졌다고 실제로 실행될 live timer 수가 늘었다고 해석한다
- lazy cancellation이나 reschedule-via-new-ticket 때문에 stale entry가 queue size에 포함되는 것을 모니터링에서 놓친다
- queue entries, live timers, ready timers를 같은 대시보드 숫자로 보고 cleanup 정책과 alert를 잘못 잡는다
intents:
- symptom
- troubleshooting
prerequisites:
- data-structure/queue-basics
- data-structure/heap-basics
next_docs:
- data-structure/delayqueue-remove-cost-primer
- data-structure/scheduledfuture-cancel-stale-entries
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
- data-structure/timing-wheel-vs-delay-queue
linked_paths:
- contents/data-structure/queue-basics.md
- contents/data-structure/heap-basics.md
- contents/data-structure/delayqueue-delayed-contract-primer.md
- contents/data-structure/delayqueue-remove-cost-primer.md
- contents/data-structure/scheduledfuture-cancel-stale-entries.md
- contents/data-structure/timer-cancellation-reschedule-stale-entry-primer.md
- contents/data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
confusable_with:
- data-structure/delayqueue-remove-cost-primer
- data-structure/scheduledfuture-cancel-stale-entries
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
- data-structure/timing-wheel-vs-delay-queue
forbidden_neighbors: []
expected_queries:
- DelayQueue.size가 live timers 수보다 크게 보이는 이유는?
- lazy cancellation을 쓰면 cancelled timer가 queue size에 계속 잡히는 게 정상일 수 있어?
- queue entries와 live timers와 ready timers를 모니터링에서 어떻게 분리해?
- ScheduledExecutor queue size가 큰데 실제 실행 작업은 적을 때 무엇을 봐야 해?
- stale timer와 cancelled entry를 DelayQueue observability에서 어떻게 해석해?
contextual_chunk_prefix: |
  이 문서는 DelayQueue.size가 물리적으로 queue 안에 남은 entries를 세며,
  live timers나 ready timers 수와 다를 수 있다는 symptom router다. lazy
  cancellation, stale reschedule tickets, purge/removeOnCancelPolicy, timer
  retention metrics를 분리한다.
---
# DelayQueue Queue Size vs Live Timers Primer

> 한 줄 요약: `DelayQueue.size()`는 "queue 안에 들어 있는 entry 수"를 세기 때문에, lazy cancellation이나 stale-entry reschedule 패턴을 쓰면 "앞으로 실제로 실행될 live timer 수"보다 더 크게 보일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Queue Basics](./queue-basics.md)
- [Heap Basics](./heap-basics.md)
- [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: delayqueue size live timers, delayqueue queue size overcount, delayqueue stale entry monitoring, delayqueue lazy cancellation metrics, scheduled executor queue size cancelled tasks, queue size not live work, delayqueue observability beginner, timer queue retention, stale timer count, cancelled timer queue size, removeoncancelpolicy queue size, purge queue size, delayqueue monitoring examples, live scheduled work vs queue entries, beginner timer observability

## 먼저 그림부터

`DelayQueue`를 "알람표 상자"라고 생각하면 쉽다.

- `size()`는 상자 안 종이 개수를 센다.
- 운영자가 궁금한 값은 보통 "아직 살아 있는 알람이 몇 개냐"다.

이 둘은 같은 숫자가 아닐 수 있다.

```text
queue 안 entry 수 = live timer + stale timer
```

여기서 stale timer는 이런 것이다.

- 이미 `cancel()`된 timeout
- 재예약 때문에 더 이상 최신이 아닌 예전 ticket
- worker가 아직 꺼내 버리지 못한 오래된 entry

즉 beginner용 핵심 문장은 이것이다.

> `queue.size()`는 "실행될 예정인 일 수"가 아니라 "queue에 남아 있는 종이 수"다.

## 가장 먼저 구분할 세 숫자

| 보고 싶은 값 | 초보자용 의미 | `queue.size()`와 같은가 |
|---|---|---|
| queue entries | queue 안에 물리적으로 남아 있는 entry 수 | 예 |
| live timers | 아직 유효하고 나중에 실행될 timer 수 | 아니다 |
| ready timers | 지금 당장 꺼내 실행 가능한 만료 timer 수 | 아니다 |

운영에서 혼동이 생기는 이유는 대시보드에 보통 첫 번째 숫자만 쉽게 잡히기 때문이다.

## 왜 `size()`가 커질까

`DelayQueue`는 기본적으로 "head가 됐을 때 꺼내기"에는 강하지만,
"queue 중간의 예전 timer를 즉시 지우기"는 싸지 않을 수 있다.

그래서 구현은 자주 이런 선택을 한다.

| 패턴 | 무슨 일이 생기나 | `size()`에 미치는 영향 |
|---|---|---|
| lazy cancellation | 취소 시 `cancelled`만 표시하고 나중에 버린다 | 취소된 timer가 한동안 포함된다 |
| reschedule via new ticket | 새 deadline ticket을 넣고 예전 ticket은 stale로 둔다 | 예전 ticket도 함께 센다 |
| batch cleanup | `purge()` 같은 시점까지 정리를 미룬다 | cleanup 전까지 크게 보인다 |
| immediate remove | 취소 시 queue에서 바로 제거를 시도한다 | live 수에 더 가까워진다 |

즉 `size()` 과대계산은 대개 버그라기보다 **cleanup 시점을 늦춘 설계 결과**다.

## 예시 1: 요청 timeout 취소

웹 서버가 요청마다 30초 timeout을 예약한다고 하자.

```text
t=0s   요청 100개가 들어와 timeout 100개 예약
t=1s   95개 요청이 정상 응답, timeout 95개 cancel
t=1s   queue에는 취소된 95개가 아직 남아 있을 수 있음
```

이때 숫자는 이렇게 갈릴 수 있다.

| metric | 값 예시 | 뜻 |
|---|---:|---|
| `queue.size()` | 100 | 상자 안 종이 100장 |
| live timeout count | 5 | 실제로 아직 필요한 timeout |
| cancelled/stale estimate | 95 | 실행되면 안 되는 오래된 종이 |

운영자가 `queue.size() = 100`만 보고 "timeout backlog가 심하다"고 읽으면 틀릴 수 있다.
실제로는 backlog가 아니라 **cancelled retention**일 수 있다.

## 예시 2: debounce / 재예약 패턴

같은 사용자 작업을 "마지막 입력 후 5초 뒤 저장"으로 구현했다고 하자.

```text
사용자가 1초마다 10번 입력
매번 "5초 뒤 저장"을 다시 예약
예전 9개 ticket은 stale
마지막 1개만 live
```

이 경우 `queue.size()`는 잠시 `10`처럼 보일 수 있지만,
실제로 유효한 save timer는 `1`개뿐이다.

| 항목 | 값 예시 |
|---|---:|
| queue entries | 10 |
| latest generation only live | 1 |
| stale reschedule tickets | 9 |

이런 workload에서는 `size()`만으로 "유저 활동량"이나 "실행 예정 작업 수"를 읽으면 과장된다.

## 초보자용 판단표: 무엇을 물어보는가

| 내가 알고 싶은 것 | 먼저 볼 값 | 이유 |
|---|---|---|
| 메모리/retention이 커졌나 | `queue.size()` | stale도 메모리를 먹기 때문이다 |
| 실제 실행 예정 작업이 많나 | live timer 추정치 | `size()`는 stale를 섞어 센다 |
| 지금 당장 처리할 일이 밀렸나 | ready/expired count, dequeue rate | 미래 timer와 stale timer를 빼야 한다 |
| 취소 cleanup이 늦나 | cancelled or stale count | retention 원인을 분리해야 한다 |
| 구조를 바꿔야 할 정도로 churn이 큰가 | schedule/cancel/reschedule 비율 | size 숫자 하나로는 부족하다 |

짧게 외우면 이렇게 정리된다.

```text
queue.size()   -> 보관량
live count     -> 실제 예정 작업 수
ready count    -> 즉시 실행 대기 수
```

## 모니터링 예시를 어떻게 붙일까

초보자에게는 "한 숫자"보다 "짝지은 숫자"가 안전하다.

### 1. timeout 서비스

| metric 이름 예시 | 왜 보나 |
|---|---|
| `timer_queue_entries` | queue 전체 보관량 |
| `timer_live_timeouts` | 실제 아직 살아 있는 timeout 수 |
| `timer_cancelled_retained` | cleanup이 밀린 stale 규모 |
| `timer_fired_total` | 실제 timeout 실행량 |
| `timer_cancel_total` | 취소 churn 크기 |

이 조합이면 아래 구분이 가능하다.

- `entries`만 크고 `live`는 작다: stale retention 의심
- `live`와 `fired`가 함께 오른다: 진짜로 예정 작업이 늘고 있음
- `cancel_total`이 매우 큰데 `entries`가 안 내려간다: lazy cleanup 영향이 큼

### 2. reschedule-heavy debounce 서비스

| metric 이름 예시 | 왜 보나 |
|---|---|
| `save_timer_entries` | queue에 남은 전체 ticket 수 |
| `save_timer_live_keys` | 최신 generation 기준 유효 key 수 |
| `save_timer_stale_skips_total` | worker가 stale를 얼마나 자주 버리는지 |
| `save_timer_execution_lag_ms` | 진짜 live timer가 늦게 실행되는지 |

여기서는 `stale_skips_total`이 중요하다.
`size()`가 커도 live 작업이 제때 처리되면 "느린 scheduler"가 아니라 "재예약이 많은 workload"일 수 있다.

## 흔한 오해

1. `queue.size()`가 크면 곧바로 실행 backlog라고 생각한다.
2. `cancel()`이 성공했으니 `size()`도 바로 줄어야 한다고 생각한다.
3. reschedule은 기존 entry 하나만 수정한다고 생각한다.
4. stale entry는 correctness 문제만 만들고 observability에는 영향이 없다고 생각한다.
5. `queue.size()` 하나만 보면 운영 판단이 충분하다고 생각한다.

특히 1번이 가장 위험하다.

> backlog는 "지금 처리 못 한 live work"이고, retention은 "queue 안에 남아 있는 흔적"이다.

둘은 같은 말이 아니다.

## 작은 비교표: 어떤 해석이 맞는가

| 관측된 현상 | 더 가능성 높은 해석 | 바로 할 질문 |
|---|---|---|
| `size()`는 큰데 실제 timer 실행은 적다 | stale retention | 취소/재예약 비율이 높은가 |
| `size()`와 live count가 함께 크다 | 진짜 예정 작업 증가 | schedule 유입이 갑자기 늘었는가 |
| `size()`는 큰데 ready count는 낮다 | 미래 timer 또는 stale가 많다 | long-delay 예약이 많은가 |
| `size()`는 안정적인데 stale skip이 급증한다 | 재예약 churn 증가 | debounce/coalescing 패턴이 바뀌었는가 |
| `size()`도 크고 execution lag도 크다 | 실제 backlog 가능성 | worker 수, dequeue rate, head blocking을 봤는가 |

## 초보자용 운영 체크 순서

1. `queue.size()`를 보고 "보관량이 크다"까지만 말한다.
2. live timer 추정치나 최신 generation key 수를 따로 본다.
3. cancel/reschedule 비율을 붙여 stale-entry 가능성을 확인한다.
4. execution lag나 fired rate를 같이 봐서 진짜 backlog인지 구분한다.

이 순서를 지키면 `size()` 하나로 과잉 해석하는 실수를 많이 줄일 수 있다.

## 언제 `size()`가 그래도 유용한가

`queue.size()`가 쓸모없다는 뜻은 아니다.

| 용도 | 왜 유용한가 |
|---|---|
| 메모리 압박 탐지 | stale를 포함한 실제 보관량을 보여 준다 |
| cleanup 정책 비교 | `removeOnCancelPolicy`, `purge()` 효과를 보기 좋다 |
| churn 이상 징후 감지 | reschedule/cancel 폭증 시 먼저 튄다 |
| 구조 선택 재검토 | heap queue retention이 감당 가능한지 판단하는 출발점이 된다 |

즉 `size()`는 **운영 센서**로 좋지만,
**live scheduled work의 정답 값**으로 쓰기엔 부족하다.

## 다음 문서로 이어가기

- 왜 cancel 뒤에도 queue 안 종이가 남는지부터 보려면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- 재예약과 generation stale skip 패턴을 먼저 잡으려면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- 즉시 제거가 왜 cancel hot path 비용을 올릴 수 있는지 보려면 [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- `purge()`와 `removeOnCancelPolicy(true)`가 retention 숫자에 어떤 차이를 내는지 보려면 [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- timeout churn 자체가 너무 크다면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

`DelayQueue.size()`는 live timer 수가 아니라 queue entry 수를 세므로, lazy cancellation과 stale-entry reschedule이 있는 시스템에서는 "앞으로 실제로 실행될 작업 수"를 과장해서 보여 줄 수 있다.
