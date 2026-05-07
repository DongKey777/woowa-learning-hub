---
schema_version: 3
title: Space-Saving Heavy Hitters
concept_id: data-structure/space-saving-heavy-hitters
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- heavy-hitters
- stream-summary
- observability-hot-key
aliases:
- Space-Saving heavy hitters
- heavy hitter sketch
- top-k streaming
- frequent items summary
- hot key detection
- noisy tenant detection
- bounded counter summary
symptoms:
- Count-Min Sketch로 임의 key 빈도는 추정하면서도 현재 top offender 후보군을 직접 유지하지 못한다
- high-cardinality observability에서 모든 key를 exact counter로 세려다 메모리와 label cardinality 비용을 키운다
- Space-Saving의 min counter replacement가 overestimate error를 만든다는 점을 모른 채 과금이나 정산 truth로 사용하려 한다
intents:
- definition
- design
prerequisites:
- data-structure/count-min-sketch
- data-structure/approximate-counting-rate-limiting-observability
next_docs:
- data-structure/count-min-vs-hyperloglog
- data-structure/hdr-histogram
- data-structure/sketch-filter-selection-playbook
linked_paths:
- contents/data-structure/count-min-sketch.md
- contents/data-structure/approximate-counting-rate-limiting-observability.md
- contents/data-structure/hdr-histogram.md
- contents/data-structure/sketch-filter-selection-playbook.md
confusable_with:
- data-structure/count-min-sketch
- data-structure/hyperloglog
- data-structure/approximate-counting-rate-limiting-observability
- data-structure/sketch-filter-selection-playbook
forbidden_neighbors: []
expected_queries:
- Space-Saving heavy hitters는 Count-Min Sketch와 어떤 운영 질문이 달라?
- top-k streaming에서 noisy tenant 후보를 제한된 슬롯으로 유지하는 방법은?
- hot key detection에 exact counter map 대신 Space-Saving을 쓰는 이유는?
- Space-Saving의 min counter replacement가 왜 overestimate error를 만들 수 있어?
- high-cardinality observability에서 현재 top offender를 빠르게 찾는 자료구조는?
contextual_chunk_prefix: |
  이 문서는 Space-Saving을 스트림에서 heavy hitter와 top offender 후보를 직접
  유지하는 bounded summary로 설명한다. Count-Min Sketch의 point query와
  Space-Saving의 top-k candidate tracking을 구분한다.
---
# Space-Saving Heavy Hitters

> 한 줄 요약: Space-Saving은 제한된 슬롯으로 스트림의 상위 빈도 항목을 직접 유지해, Count-Min Sketch보다 더 곧바로 heavy hitter 후보를 뽑고 싶은 운영용 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Count-Min Sketch](./count-min-sketch.md)
> - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)
> - [HDR Histogram](./hdr-histogram.md)

> retrieval-anchor-keywords: space-saving, heavy hitters, top-k streaming, frequent items, hot key detection, stream summary, approximate top k, observability sketch, noisy tenant, bounded counter summary

## 핵심 개념

Count-Min Sketch는 "이 key가 얼마나 많이 나왔나"를 묻는 point query에 강하다.  
하지만 "지금 가장 시끄러운 key가 누구인가"를 바로 유지해주진 않는다.

Space-Saving은 애초에 목적이 다르다.

- 제한된 슬롯 수 `k`만 유지한다
- 각 슬롯은 `key + count`를 가진다
- 새 항목이 오면 빈 슬롯을 쓰거나, 최소 카운터를 대체한다

즉 모든 key를 대략 세는 구조가 아니라,  
**상위 빈도 후보군 자체를 유지하는 bounded summary**다.

## 깊이 들어가기

### 1. point query와 heavy hitter 추적은 다른 문제다

운영 질문은 보통 둘로 나뉜다.

- "이 tenant가 많이 보였나?"
- "지금 가장 noisy한 tenant는 누구인가?"

Count-Min Sketch는 첫 번째에 강하고,  
Space-Saving은 두 번째에 더 직접적이다.

즉 CMS만으로 top offender를 바로 뽑기보다는,  
Space-Saving처럼 후보군을 유지하는 구조가 더 자연스럽다.

### 2. 최소 카운터 대체가 핵심 동작이다

Space-Saving은 슬롯이 가득 찼을 때 새 key를 다음처럼 처리한다.

- 현재 최소 count를 가진 슬롯을 찾는다
- 그 슬롯을 새 key로 바꾼다
- count는 `min + 1`로 시작한다

그래서 새 key는 실제보다 과대 추정된 count를 가질 수 있다.  
하지만 자주 나타나는 key는 계속 살아남고, 드문 key는 밀려난다.

이 구조 덕분에 매우 작은 메모리로도 top-k 후보를 유지할 수 있다.

### 3. 왜 운영 시스템에서 유용한가

high-cardinality 환경에서 모든 key를 exact counter로 들고 있긴 어렵다.

- tenant
- api key
- endpoint
- cache key
- user agent 조합

이때 Space-Saving은 "상위 몇 개 suspect만 뽑아라" 같은 운영 목적에 딱 맞는다.

즉 관측의 목표가 truth store가 아니라  
**빠른 설명력**이라면 매우 실용적이다.

### 4. Count-Min Sketch와 함께 쓰면 더 좋다

실무에서는 둘을 조합하기도 한다.

- CMS: 임의 key point query 빈도 추정
- Space-Saving: 현재 top offender 후보 유지

이 조합이면:

- 특정 key가 수상한지 즉석 질의 가능
- 동시에 noisy key 랭킹도 유지 가능

즉 한 구조가 다른 구조를 대체한다기보다,  
관측 질문이 다르므로 함께 붙을 수 있다.

### 5. backend에서의 함정

Space-Saving도 완전한 truth는 아니다.

- 경계선 key는 순위가 흔들릴 수 있다
- 동일 빈도군이 많으면 후보가 바뀔 수 있다
- 작은 `k`로는 중간권 noisy key를 놓칠 수 있다

그래서 알람/탐지 구조로는 좋지만,  
정산/과금 기준으로 쓰면 안 된다.

## 실전 시나리오

### 시나리오 1: hot key / hot tenant 탐지

cache key나 tenant별 요청이 몰리는 순간  
상위 offending key를 빠르게 뽑아 설명할 수 있다.

### 시나리오 2: rate limiting pre-investigation

429를 치기 전에 어떤 API key가 top offender인지  
운영 대시보드에서 빠르게 파악할 수 있다.

### 시나리오 3: observability cardinality guard

모든 label 조합을 저장하지 않고  
상위 noisy label 조합만 먼저 유지해 비용을 통제할 수 있다.

### 시나리오 4: 부적합한 경우

임의 key 정확 count가 중요하거나  
하위권 key까지 전부 알고 싶다면 exact counter나 다른 구조가 필요하다.

## 코드로 보기

```java
import java.util.HashMap;
import java.util.Map;

public class SpaceSaving {
    private final int capacity;
    private final Map<String, Counter> counters = new HashMap<>();

    public SpaceSaving(int capacity) {
        this.capacity = capacity;
    }

    public void add(String key) {
        Counter existing = counters.get(key);
        if (existing != null) {
            existing.count++;
            return;
        }

        if (counters.size() < capacity) {
            counters.put(key, new Counter(key, 1, 0));
            return;
        }

        Counter min = counters.values().stream()
                .min((a, b) -> Integer.compare(a.count, b.count))
                .orElseThrow();

        counters.remove(min.key);
        counters.put(key, new Counter(key, min.count + 1, min.count));
    }

    private static final class Counter {
        private final String key;
        private int count;
        private final int error;

        private Counter(String key, int count, int error) {
            this.key = key;
            this.count = count;
            this.error = error;
        }
    }
}
```

이 코드는 최소 카운터 대체 감각만 보여준다.  
실전 구현은 min-heap 보조 구조와 snapshot export가 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Space-Saving | 상위 noisy key 후보를 직접 유지하기 쉽다 | 임의 key point query에는 약하다 | hot key ranking, top offender 탐지 |
| Count-Min Sketch | 임의 key 빈도 추정이 가능하다 | top-k 후보를 직접 들고 있지 않는다 | point query, frequency sketch |
| Exact Counter Map | 결과가 명확하다 | high-cardinality에서 비용이 커진다 | key 수가 작고 정확성이 중요할 때 |
| Sampling | 구현이 단순하다 | 드문데 중요한 heavy hitter를 놓칠 수 있다 | 대략적 추세만 보면 될 때 |

중요한 질문은 "모든 key를 세고 싶은가"가 아니라  
"상위 noisy key 몇 개만 빠르게 알고 싶은가"다.

## 꼬리질문

> Q: Space-Saving이 CMS보다 더 직접적인 문제는 무엇인가요?
> 의도: point query와 ranking 문제를 구분하는지 확인
> 핵심: 지금 가장 빈도가 높은 heavy hitter 후보를 유지하는 문제다.

> Q: 왜 새 key가 최소 슬롯을 대체하나요?
> 의도: bounded summary의 자원 배분 감각 확인
> 핵심: 자주 나오지 않는 key를 버리고 상위 후보군만 유지하려는 구조이기 때문이다.

> Q: 왜 과금/정산에는 부적합한가요?
> 의도: 운영 센서와 truth store를 구분하는지 확인
> 핵심: bounded approximation이라 경계선 항목의 정확한 count/순위는 보장하지 않기 때문이다.

## 한 줄 정리

Space-Saving은 제한된 슬롯 안에서 heavy hitter 후보를 직접 유지하는 bounded stream summary라서, hot key와 noisy tenant를 운영적으로 빠르게 드러내는 데 강하다.
