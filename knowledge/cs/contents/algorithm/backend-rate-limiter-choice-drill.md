---
schema_version: 3
title: Backend Rate Limiter Choice Drill
concept_id: algorithm/backend-rate-limiter-choice-drill
canonical: false
category: algorithm
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 74
mission_ids:
- missions/payment
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- rate-limit
- token-bucket
- fixed-window
- sliding-window
aliases:
- backend rate limiter choice drill
- token bucket fixed window drill
- API throttling limiter exercise
- burst control rate limit drill
- 요청 제한 알고리즘 드릴
symptoms:
- 로그인, 결제, API 호출 제한에서 fixed window, sliding window, token bucket을 어떻게 고를지 모른다
- fixed window 경계 burst가 왜 생기는지 설명하지 못한다
- burst를 조금 허용해야 하는지 평탄하게 흘려야 하는지 요구사항을 먼저 자르지 않는다
intents:
- drill
- comparison
- design
prerequisites:
- algorithm/rate-limiter-algorithms
- algorithm/amortized-analysis-pitfalls
next_docs:
- data-structure/bounded-queue-policy-primer
- system-design/retry-amplification-and-backpressure-primer
- system-design/rate-limiter-design
linked_paths:
- contents/algorithm/rate-limiter-algorithms.md
- contents/algorithm/amortized-analysis-pitfalls.md
- contents/data-structure/bounded-queue-policy-primer.md
- contents/system-design/retry-amplification-and-backpressure-primer.md
- contents/system-design/rate-limiter-design.md
confusable_with:
- algorithm/rate-limiter-algorithms
- system-design/rate-limiter-design
- data-structure/bounded-queue-policy-primer
forbidden_neighbors:
- contents/system-design/circuit-breaker-basics.md
expected_queries:
- backend rate limiter에서 fixed window sliding window token bucket을 문제로 연습하고 싶어
- 로그인 시도 제한은 어떤 rate limiter가 맞는지 드릴해줘
- 결제 API burst를 조금 허용하려면 token bucket을 왜 보는지 설명해줘
- fixed window 경계에서 요청이 두 배처럼 통과하는 문제를 풀어줘
- rate limit과 circuit breaker를 헷갈리지 않는 선택 문제를 줘
contextual_chunk_prefix: |
  이 문서는 backend rate limiter choice drill이다. fixed window,
  sliding window log/counter, token bucket, leaky bucket, burst control,
  login attempts, payment API throttling 같은 미션 질문을 알고리즘 선택
  문제로 매핑한다.
---
# Backend Rate Limiter Choice Drill

> 한 줄 요약: rate limiter는 "몇 개까지"보다 "어떤 시간 모델로 burst를 허용하거나 평탄화할 것인가"를 먼저 정해야 한다.

**난이도: Intermediate**

## 문제 1

상황:

```text
1분에 100번 제한을 fixed window로 걸었는데 12:00:59에 100번, 12:01:00에 100번이 통과했다.
```

답:

fixed window boundary burst다. 구현은 쉽지만 창 경계에서 두 창 quota가 붙어 보일 수 있다.
경계 burst가 문제라면 sliding window 계열을 검토한다.

## 문제 2

상황:

```text
로그인 실패 시도를 사용자별로 정확히 최근 10분 기준으로 막고 싶다.
사용자 수는 아직 작다.
```

답:

sliding window log가 후보가 된다. 정확도가 중요하고 저장 비용을 감당할 수 있기 때문이다.
사용자 수가 커지면 counter 근사나 별도 저장소 비용을 다시 본다.

## 문제 3

상황:

```text
결제 승인 API는 평균 초당 10건만 원하지만 순간적으로 20건까지는 흡수해도 된다.
```

답:

token bucket이 자연스럽다. 일정 속도로 token을 채우되 bucket 크기만큼 burst를 허용할 수 있다.
burst를 평탄하게 흘려야 한다면 leaky bucket 쪽 질문으로 바뀐다.

## 빠른 체크

| 요구 | 후보 |
|---|---|
| 구현 단순, 경계 burst 허용 | fixed window |
| 최근 N분 정확도 | sliding window log |
| 가벼운 근사 | sliding window counter |
| 평균 제한 + burst 허용 | token bucket |
| 일정 속도 평탄화 | leaky bucket |
