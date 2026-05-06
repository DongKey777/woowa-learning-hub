---
schema_version: 3
title: Rate Limiter Algorithms
concept_id: algorithm/rate-limiter-algorithms
canonical: false
category: algorithm
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- fixed-window-boundary-burst
- token-bucket-vs-leaky-bucket
- sliding-window-accuracy-vs-cost
aliases:
- token bucket throttling
- leaky bucket shaping
- sliding window counter limiter
- sliding window log limiter
- fixed window quota limiter
- burst control algorithm
- api throttling limiter choice
- request rate shaping
- 요청 폭주 제어 알고리즘
- 버스트 허용 rate limit
symptoms:
- rate limit은 걸어야 하는데 burst를 너무 딱딱하게 막는 것 같아
- fixed window를 썼더니 창 경계에서 요청이 몰려도 통과돼
- sliding log가 정확하긴 한데 메모리가 너무 많이 드는 이유가 궁금해
- token bucket이랑 leaky bucket이 둘 다 비슷해 보여서 어떤 상황에 써야 할지 모르겠어
intents:
- troubleshooting
- comparison
prerequisites:
- algorithm/amortized-analysis-pitfalls
next_docs:
- algorithm/top-k-streaming-heavy-hitters
- algorithm/monotone-deque-proof-intuition
linked_paths:
- contents/algorithm/amortized-analysis-pitfalls.md
- contents/algorithm/monotone-deque-proof-intuition.md
- contents/algorithm/top-k-streaming-heavy-hitters.md
confusable_with:
- algorithm/top-k-streaming-heavy-hitters
- algorithm/monotone-deque-proof-intuition
forbidden_neighbors:
expected_queries:
- burst는 조금 허용하면서 평균 요청 수만 제한하고 싶을 때 어떤 rate limit 방식이 맞아?
- 고정 윈도우로 막았더니 경계 시점에 요청이 두 배처럼 몰리는 이유를 설명해줘
- sliding window log랑 counter 중에 정확도와 메모리 비용을 어떻게 비교해야 해?
- 로그인 시도 제한처럼 짧은 시간 반복 요청을 막을 때 어떤 limiter가 자연스러워?
- token bucket과 leaky bucket을 실무에서 어떤 기준으로 골라야 하는지 감이 안 와
- API throttling에서 순간 버스트 허용이 필요하면 어떤 시간 모델로 생각해야 해?
contextual_chunk_prefix: |
  이 문서는 요청 제한을 붙였는데 순간 몰림을 어디까지 허용할지, 창 경계에서
  quota가 새는 이유가 뭔지 같은 증상에서 출발해 시간 모델별 원인으로 이어지는
  symptom router다. 평균만 제한하고 싶다, 두 구간 끝에서 한꺼번에 통과한다,
  최근 기록을 많이 들고 있는 게 부담된다, 일정한 배출 속도로 평탄화하고
  싶다 같은 자연어 paraphrase가 본 문서의 limiter 선택 기준에 매핑된다.
---
# Rate Limiter Algorithms

> 한 줄 요약: Rate limiter는 고정 창, 슬라이딩 창, 토큰 버킷, 리키 버킷처럼 서로 다른 시간 모델로 요청 폭주를 제어한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ring Buffer](../data-structure/ring-buffer.md)
> - [Monotone Deque Proof Intuition](./monotone-deque-proof-intuition.md)
> - [Amortized Analysis Pitfalls](./amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: rate limiter, token bucket, leaky bucket, sliding window log, fixed window, sliding window counter, API gateway, throttling, burst control, quota

## 핵심 개념

Rate limiter는 요청이 너무 많이 몰릴 때 시스템을 보호하는 제어 장치다.

대표 알고리즘은 다음과 같다.

- Fixed window
- Sliding window log
- Sliding window counter
- Token bucket
- Leaky bucket

각 방식은 "언제 허용하고 언제 거절할까"에 대한 시간 모델이 다르다.

## 깊이 들어가기

### 1. Fixed window

가장 단순한 방식이다.  
예를 들어 1분에 100개까지 허용한다.

장점:

- 구현이 쉽다

단점:

- 창 경계에서 burst가 몰릴 수 있다

### 2. Sliding window log

각 요청 시간을 로그처럼 저장하고, 최근 window 밖의 기록을 버린다.

정확하지만 저장 비용이 든다.

### 3. Sliding window counter

최근 두 개의 창을 부분 가중치로 섞어 근사한다.

log보다 가볍고 fixed window보다 부드럽다.

### 4. Token bucket

토큰이 일정 속도로 채워지고, 요청이 오면 토큰을 하나 사용한다.

토큰이 남아 있으면 burst를 허용하고, 없으면 거절한다.

이 방식은 실무에서 매우 자주 쓰인다.

### 5. Leaky bucket

요청을 일정 속도로 흘려보내는 관점이다.

burst를 평탄화하는 데 강하다.

## 실전 시나리오

### 시나리오 1: API gateway

테넌트별 요청량을 제어할 때 token bucket이 자연스럽다.

### 시나리오 2: 로그인 시도 보호

짧은 시간에 반복되는 실패를 막을 때 fixed window나 sliding window가 유용하다.

### 시나리오 3: 백엔드 배치 큐

처리량을 일정하게 유지하려면 leaky bucket 감각이 잘 맞는다.

### 시나리오 4: 오판

정확한 분당 제한만 보면 fixed window가 충분할 수 있지만, burst 패턴이 있으면 더 부드러운 알고리즘이 필요하다.

## 코드로 보기

```java
public class TokenBucket {
    private final long capacity;
    private final long refillPerSecond;
    private double tokens;
    private long lastRefillMillis;

    public TokenBucket(long capacity, long refillPerSecond) {
        this.capacity = capacity;
        this.refillPerSecond = refillPerSecond;
        this.tokens = capacity;
        this.lastRefillMillis = System.currentTimeMillis();
    }

    public synchronized boolean allow() {
        refill();
        if (tokens < 1.0) {
            return false;
        }
        tokens -= 1.0;
        return true;
    }

    private void refill() {
        long now = System.currentTimeMillis();
        long elapsed = now - lastRefillMillis;
        if (elapsed <= 0) return;
        tokens = Math.min(capacity, tokens + (elapsed / 1000.0) * refillPerSecond);
        lastRefillMillis = now;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Fixed window | 가장 단순하다 | 경계 burst가 있다 | 단순 quota |
| Sliding log | 가장 정확하다 | 메모리를 더 쓴다 | 정확한 최근 카운트 |
| Sliding counter | 부드럽고 가볍다 | 근사치다 | 실무적 균형 |
| Token bucket | burst 허용이 자연스럽다 | 구현에 시간 개념이 필요하다 | API throttling |
| Leaky bucket | 출력 속도를 일정하게 만든다 | burst 대응이 덜 유연하다 | 평탄한 처리량 |

핵심은 "막을 것인가, 완만하게 조절할 것인가"다.

## 꼬리질문

> Q: token bucket이 실무에서 인기 있는 이유는?
> 의도: burst 허용과 제어를 이해하는지 확인
> 핵심: 순간 폭주는 허용하되 평균 속도는 제한할 수 있기 때문이다.

> Q: sliding log가 정확한데 왜 항상 쓰지 않나?
> 의도: 정확도와 메모리 trade-off 이해 확인
> 핵심: 최근 요청 수를 전부 저장해야 하므로 비용이 더 든다.

> Q: rate limiter와 circuit breaker는 같은가?
> 의도: 보호 장치의 목적 구분 확인
> 핵심: rate limiter는 속도 제어, circuit breaker는 장애 전파 차단이다.

## 한 줄 정리

Rate limiter는 고정 창, 슬라이딩 창, 토큰 버킷, 리키 버킷 같은 시간 모델로 요청 폭주를 제어하는 알고리즘 모음이다.
