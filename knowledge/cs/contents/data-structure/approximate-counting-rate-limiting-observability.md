---
schema_version: 3
title: Approximate Counting for Rate Limiting and Observability
concept_id: data-structure/approximate-counting-rate-limiting-observability
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- approximate-counting
- rate-limit-hot-key
- observability-high-cardinality
aliases:
- approximate counting rate limiting
- approximate counting observability
- Count-Min Sketch rate limiter
- heavy hitter detection
- hot key observability
- sketch exact fallback
- soft limiter sketch signal
symptoms:
- tenant, user, endpoint, token, ip 조합별 exact counter가 너무 많아져 메모리와 eviction 정책이 먼저 무너진다
- Count-Min Sketch 추정값을 그대로 429 차단 근거로 써도 되는지 헷갈린다
- hot key 후보와 point query 빈도 추정을 분리하지 않아 관측은 되지만 운영 액션이 나오지 않는다
intents:
- design
- troubleshooting
prerequisites:
- data-structure/count-min-sketch
- data-structure/space-saving-heavy-hitters
next_docs:
- data-structure/count-min-sketch
- data-structure/space-saving-heavy-hitters
- data-structure/count-min-vs-hyperloglog
- data-structure/sketch-filter-selection-playbook
- algorithm/top-k-streaming-heavy-hitters
linked_paths:
- contents/data-structure/count-min-sketch.md
- contents/data-structure/space-saving-heavy-hitters.md
- contents/data-structure/count-min-vs-hyperloglog.md
- contents/data-structure/sketch-filter-selection-playbook.md
- contents/algorithm/top-k-streaming-heavy-hitters.md
confusable_with:
- data-structure/count-min-sketch
- data-structure/count-min-vs-hyperloglog
- data-structure/space-saving-heavy-hitters
- algorithm/top-k-streaming-heavy-hitters
forbidden_neighbors: []
expected_queries:
- rate limiting에서 Count-Min Sketch를 exact counter 대신 바로 써도 돼?
- 고카디널리티 key별 카운터가 터질 때 approximate counting을 어떻게 붙여?
- hot key observability에서 sketch와 heavy hitter 후보 추적은 어떻게 역할이 달라?
- approximate counting을 soft signal과 exact fallback으로 나누는 이유를 알려줘
- Count-Min Sketch와 HyperLogLog 중 rate limiting에는 무엇이 맞아?
contextual_chunk_prefix: |
  이 문서는 high-cardinality backend에서 exact per-key counter가 어려울 때
  Count-Min Sketch, heavy hitter 후보 추적, exact fallback을 조합해 rate
  limiting과 observability를 설계하는 playbook이다. sketch는 hard block이
  아니라 수상한 key를 깨우는 soft signal이라는 경계를 강조한다.
---
# Approximate Counting for Rate Limiting and Observability

> 한 줄 요약: approximate counting은 Count-Min Sketch와 heavy-hitter 후보 추적을 이용해, backend에서 정확한 per-key 카운터를 전부 들고 있지 않고도 rate limiting과 hot key 관측을 가능하게 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Count-Min Sketch](./count-min-sketch.md)
> - [Space-Saving Heavy Hitters](./space-saving-heavy-hitters.md)
> - [Count-Min Sketch vs HyperLogLog](./count-min-vs-hyperloglog.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)

> retrieval-anchor-keywords: approximate counting, rate limiting, observability, count-min sketch, heavy hitter detection, hot key, soft limit, exact fallback, sliding window sketch, backend telemetry

## 핵심 개념

대규모 backend에서는 `tenant + user + endpoint + token + ip` 조합별로 정확한 카운터를 전부 유지하기 어렵다.  
문제는 단순한 QPS가 아니라 **고카디널리티 key 공간**이다.

이때 approximate counting은 "정확한 truth store"가 아니라 "작고 빠른 운영 센서"로 동작한다.

- Count-Min Sketch로 빈도를 싸게 추정한다.
- heavy hitter 후보만 좁게 추린다.
- 임계치 근처에서만 정확한 카운터로 승격한다.

즉 모든 key를 정밀 추적하지 않고, **위험해 보이는 key만 비싸게 본다**.

## 깊이 들어가기

### 1. 왜 exact per-key counter가 먼저 무너지나

정확한 rate limit를 위해 key별 카운터를 만들면 cardinality 폭증이 먼저 온다.

- `userId`
- `apiKey`
- `tenantId + endpoint`
- `ip + user-agent`
- 짧은 sliding window bucket

여기에 멀티 인스턴스와 region 복제까지 붙으면, 메모리보다도 동기화 비용과 eviction 정책이 더 어려워진다.

즉 병목은 "증가 연산이 느리다"가 아니라 "추적해야 할 key 수가 통제되지 않는다" 쪽이다.

### 2. Count-Min Sketch를 왜 바로 차단기에 쓰면 안 되나

Count-Min Sketch는 충돌 때문에 과대 추정한다.  
그래서 soft signal에는 좋지만 hard decision에는 위험하다.

- sketch estimate > threshold 라고 해서
- 실제 요청 수가 threshold를 넘었다는 뜻은 아니다

rate limiter가 이 값을 그대로 429 판단에 쓰면, 정상 사용자가 충돌 오차 때문에 억울하게 막힐 수 있다.

실무에서는 보통 이렇게 나눈다.

- sketch: "수상한가?"
- exact counter: "정말 넘었는가?"

즉 approximate counting은 차단의 근거가 아니라 **정확 카운터를 깨우는 전처리기**에 가깝다.

### 3. heavy hitter detection과 같이 써야 운영 가치가 커진다

임의 key의 대략 빈도만 아는 것으로는 운영 액션이 제한적이다.  
어떤 key들이 상위를 차지하는지 같이 봐야 hot shard, noisy tenant, abusive token을 잡을 수 있다.

대표 조합은 이렇다.

- Count-Min Sketch: point query 빈도 추정
- Space-Saving / 작은 top-k heap: 상위 후보 유지
- exact map or Redis: 승격된 후보만 정밀 추적

이 조합이 중요한 이유는 두 질문이 다르기 때문이다.

- "이 key가 많이 보였나?"
- "지금 가장 시끄러운 key는 누구인가?"

첫 번째는 sketch가 잘하고, 두 번째는 heavy hitter 후보 관리가 더 직접적이다.

### 4. observability에서는 window, merge, decay가 핵심이다

운영 대시보드에서 중요한 건 lifetime count가 아니라 **최근성**이다.

- 1분 bucket sketch를 여러 개 돌린다
- window가 지나면 통째로 폐기하거나 rotate한다
- 인스턴스별 sketch는 합산 가능하게 설계한다
- 알람은 절대값보다 기울기 변화에 걸기도 한다

Count-Min Sketch는 동일한 해시 설정을 공유하면 인스턴스 간 합산이 가능하다.  
이 성질 덕분에 중앙 저장소에 모든 raw event를 보내지 않고도 shard별 로컬 관측치를 모을 수 있다.

다만 merge가 가능하다고 해서 정확성이 생기는 것은 아니다.  
충돌 오차도 함께 합쳐지므로, 관측과 탐지에는 좋지만 정산/과금 truth로 쓰면 안 된다.

## 실전 시나리오

### 시나리오 1: endpoint별 soft prefilter rate limiting

`tenantId + endpoint` 조합이 매우 많아 exact counter를 전부 Redis에 올리면 비용이 커진다.  
먼저 sketch로 "threshold 근처인지"를 보고, 수상한 조합만 정확한 sliding window counter로 승격한다.

### 시나리오 2: hot key로 인한 cache/database 쏠림 탐지

같은 캐시 key나 row key로 요청이 몰리면 전체 latency가 무너질 수 있다.  
heavy hitter 후보군을 유지하면 상위 몇 개 hot key를 빠르게 찾아 shard skew를 설명할 수 있다.

### 시나리오 3: observability에서 고카디널리티 label 보호

모든 `tenant + route + status + caller` 조합을 정확 metric으로 내보내면 비용이 폭발한다.  
approximate counting은 어떤 label 조합이 폭증 중인지 먼저 감지하고, export 대상을 top suspect 위주로 제한하게 해준다.

### 시나리오 4: 오판

approximate counter 하나로 바로 차단하거나 billing 근거를 만들면 위험하다.  
공격 트래픽이 충돌을 유도하는 방향으로 몰리거나, window rotation이 잘못되면 정상 key까지 noisy하게 보일 수 있다.

## 코드로 보기

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ApproximateRateLimiter {
    private final CountMinSketch sketch = new CountMinSketch(4, 1 << 15);
    private final Map<String, FixedWindowCounter> exactCounters = new ConcurrentHashMap<>();
    private final int softThreshold;
    private final int hardThreshold;

    public ApproximateRateLimiter(int softThreshold, int hardThreshold) {
        this.softThreshold = softThreshold;
        this.hardThreshold = hardThreshold;
    }

    public boolean allow(String tenantId, String endpoint, long nowMillis) {
        String key = tenantId + ":" + endpoint;
        sketch.add(key);

        int estimate = sketch.estimate(key);
        if (estimate < softThreshold) {
            return true;
        }

        // sketch가 수상하다고 말할 때만 정확 카운터를 깨운다.
        FixedWindowCounter counter =
                exactCounters.computeIfAbsent(key, ignored -> new FixedWindowCounter(hardThreshold, 60_000));

        return counter.allow(nowMillis);
    }

    static final class FixedWindowCounter {
        private final int limit;
        private final long windowMillis;
        private long windowStart;
        private int count;

        FixedWindowCounter(int limit, long windowMillis) {
            this.limit = limit;
            this.windowMillis = windowMillis;
            this.windowStart = 0L;
            this.count = 0;
        }

        synchronized boolean allow(long nowMillis) {
            if (nowMillis - windowStart >= windowMillis) {
                windowStart = nowMillis;
                count = 0;
            }

            if (count >= limit) {
                return false;
            }

            count++;
            return true;
        }
    }
}
```

이 코드는 핵심 아이디어만 보여준다.  
실전에서는 exact counter eviction, distributed merge, hash seed 관리, late event 처리까지 함께 설계해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Count-Min Sketch + exact fallback | 메모리를 고정하면서도 차단 정확도를 지킬 수 있다 | 2단계 파이프라인 운영이 필요하다 | 고카디널리티 rate limiting, hot key 탐지 |
| exact per-key counter only | 판단이 명확하다 | key 수가 폭증하면 비용이 급격히 커진다 | key 공간이 작고 정확성이 절대적일 때 |
| Space-Saving / top-k only | 상위 noisy key를 바로 뽑기 쉽다 | 임의 key point query에는 약하다 | 운영 대시보드에서 top offender가 중요할 때 |
| sampling only | 구현이 단순하고 싸다 | 경계선 burst나 특정 heavy hitter를 놓칠 수 있다 | 대략적 추세만 보면 될 때 |

중요한 질문은 "모든 key의 truth가 필요한가"가 아니라 "어떤 key만 비싸게 정확히 볼 것인가"다.

## 꼬리질문

> Q: Count-Min Sketch를 rate limiter의 최종 차단 근거로 바로 쓰면 왜 위험한가?
> 의도: 과대 추정 오차가 운영 결정에 미치는 영향 이해 확인
> 핵심: 충돌 때문에 정상 key가 threshold를 넘은 것처럼 보일 수 있기 때문이다.

> Q: heavy hitter 후보 관리가 sketch와 별도로 필요한 이유는?
> 의도: point query와 ranking 문제를 구분하는지 확인
> 핵심: sketch는 특정 key의 빈도 추정에는 강하지만, 지금 가장 시끄러운 key를 직접 유지해주진 않는다.

> Q: observability에서 approximate counting을 쓴다면 무엇을 export해야 하나?
> 의도: high-cardinality telemetry 설계 감각 확인
> 핵심: 모든 key의 raw count가 아니라 top suspect, burst 구간, 승격된 exact counter 위주로 내보내야 한다.

## 한 줄 정리

approximate counting은 rate limiter와 observability에서 모든 key를 정확히 세는 대신, 위험한 key만 빠르게 가려내고 그때만 정밀 추적으로 승격시키는 운영용 자료구조 전략이다.
