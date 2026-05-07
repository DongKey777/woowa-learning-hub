---
schema_version: 3
title: HyperLogLog
concept_id: data-structure/hyperloglog
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- hyperloglog
- approximate-cardinality
- distinct-count-observability
aliases:
- HyperLogLog
- HLL
- cardinality estimation
- distinct count
- approximate distinct
- leading zeros register
- unique visitors sketch
symptoms:
- distinct user나 unique tenant 수를 정확한 set으로 모두 들고 있으려다 memory가 먼저 커진다
- HyperLogLog가 frequency가 아니라 cardinality를 추정한다는 점을 Count-Min Sketch와 섞는다
- hash leading zeros와 register가 고유 원소 수의 통계적 흔적을 저장한다는 모델을 이해하지 못한다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/count-min-vs-hyperloglog
next_docs:
- data-structure/sketch-filter-selection-playbook
- data-structure/approximate-counting-rate-limiting-observability
- data-structure/count-min-sketch
linked_paths:
- contents/data-structure/count-min-vs-hyperloglog.md
- contents/data-structure/approximate-counting-rate-limiting-observability.md
- contents/data-structure/hdr-histogram.md
- contents/data-structure/sketch-filter-selection-playbook.md
- contents/data-structure/bloom-filter.md
- contents/data-structure/count-min-sketch.md
confusable_with:
- data-structure/count-min-vs-hyperloglog
- data-structure/count-min-sketch
- data-structure/bloom-filter
- data-structure/hdr-histogram
forbidden_neighbors: []
expected_queries:
- HyperLogLog는 서로 다른 원소 수를 어떻게 적은 메모리로 추정해?
- HLL에서 leading zeros와 register가 cardinality 추정에 쓰이는 이유는?
- unique visitors나 distinct tenant 수에는 HyperLogLog가 맞고 frequency에는 Count-Min Sketch가 맞는 이유는?
- approximate distinct count를 exact set 없이 관측하는 방법을 알려줘
- HyperLogLog를 observability dashboard에서 어떻게 merge해서 쓸 수 있어?
contextual_chunk_prefix: |
  이 문서는 HyperLogLog를 streaming cardinality estimation과 approximate
  distinct count를 위한 primer로 설명한다. hash leading zeros, registers,
  unique visitors, distinct tenant, Count-Min Sketch와의 frequency vs
  cardinality 차이를 다룬다.
---
# HyperLogLog

> 한 줄 요약: HyperLogLog는 스트림에서 서로 다른 원소 수를 매우 적은 메모리로 근사하는 cardinality 추정 구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Count-Min Sketch vs HyperLogLog](./count-min-vs-hyperloglog.md)
> - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)
> - [HDR Histogram](./hdr-histogram.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [Bloom Filter](./bloom-filter.md)
> - [Count-Min Sketch](./count-min-sketch.md)

> retrieval-anchor-keywords: hyperloglog, HLL, cardinality estimation, distinct count, approximate distinct, register, leading zeros, streaming analytics, observability, telemetry, high-cardinality metrics, unique visitors, sketch

## 핵심 개념

HyperLogLog는 "서로 다른 원소가 몇 개인가"를 추정하는 자료구조다.  
정확한 집합을 저장하지 않고, 해시값의 분포만 보고 cardinality를 계산한다.

실무적으로는 다음 상황에서 자주 나온다.

- DAU/MAU 대략 계산
- unique visitor 추정
- distinct tenant 수 추정
- 대량 로그의 중복 제거 전 상태 파악

## 깊이 들어가기

### 1. 왜 해시의 leading zeros를 보나

무작위 해시라면 어떤 비트 패턴이 얼마나 자주 나오는지 통계적으로 예측할 수 있다.

어떤 값이 매우 드물게 긴 0 prefix를 가진다면, 그건 대략 많은 고유 원소가 들어왔다는 신호다.  
HyperLogLog는 이 성질을 이용해 "희귀 패턴의 최대 길이"를 여러 bucket에서 관찰한다.

### 2. register가 핵심이다

HyperLogLog는 여러 개의 작은 register를 둔다.

- 해시를 bucket으로 나눈다.
- bucket마다 관찰된 leading zero 패턴의 최대치를 저장한다.
- 마지막에 이 register들을 합쳐 추정치를 만든다.

즉 "전체 원소를 세는 것"이 아니라 "분포의 흔적을 기록하는 것"이다.

### 3. 왜 메모리가 작나

register 하나가 아주 크지 않다.
고유 원소 수가 아무리 많아져도 register 수는 고정이므로 메모리가 안정적이다.

이게 대규모 분석에서 강력하다.

### 4. backend에서의 의미

정확한 distinct count는 무거울 수 있다.

- 대시보드의 unique users
- 분산 로그 시스템의 distinct request key
- 캐시나 샤드 운영에서 고유 엔터티 수 추정

HyperLogLog는 이걸 메모리 적게, 빠르게 보여준다.

## 실전 시나리오

### 시나리오 1: unique visitor 추정

웹 서비스에서 하루 동안 얼마나 많은 고유 사용자가 방문했는지 빠르게 보고 싶을 때 적합하다.

### 시나리오 2: 중복 이벤트 파악

같은 이벤트가 여러 번 들어오는 환경에서 고유 이벤트 수를 대략적으로 알고 싶을 때 쓴다.

### 시나리오 3: shard 규모 판단

테넌트 수나 key 공간의 대략 크기를 알아야 할 때, 정확한 set보다 HyperLogLog가 훨씬 가볍다.

### 시나리오 4: 오판

이 구조는 정확한 unique count가 필요할 때 쓰는 것이 아니다.  
청구/정산처럼 1건 오차도 치명적인 경우에는 부적합하다.

## 코드로 보기

```java
public class HyperLogLog {
    private final byte[] registers;
    private final int p;
    private final int m;

    public HyperLogLog(int p) {
        this.p = p;
        this.m = 1 << p;
        this.registers = new byte[m];
    }

    public void add(String value) {
        int hash = mix(value.hashCode());
        int bucket = hash >>> (32 - p);
        int w = hash << p;
        int leading = Integer.numberOfLeadingZeros(w) + 1;
        registers[bucket] = (byte) Math.max(registers[bucket], leading);
    }

    public double estimate() {
        double sum = 0.0;
        for (byte r : registers) {
            sum += 1.0 / (1L << r);
        }
        double alpha = 0.7213 / (1 + 1.079 / m);
        return alpha * m * m / sum;
    }

    private int mix(int x) {
        x ^= (x >>> 16);
        x *= 0x7feb352d;
        x ^= (x >>> 15);
        x *= 0x846ca68b;
        x ^= (x >>> 16);
        return x;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| HyperLogLog | distinct count에 매우 효율적이다 | 정확하지 않다 | 고유 수 추정 |
| HashSet | 정확하다 | 메모리를 많이 쓴다 | 소규모 데이터 |
| Bloom Filter | membership에 강하다 | cardinality를 직접 세지 못한다 | 존재 여부 필터링 |

HyperLogLog는 "얼마나 많은 서로 다른 값이 있는가"에만 초점을 맞춘다.

## 꼬리질문

> Q: 왜 register만으로 충분한가?
> 의도: 분포의 통계적 흔적을 이해하는지 확인
> 핵심: 전체 값을 저장하지 않아도 해시 패턴의 최대치가 cardinality를 암시한다.

> Q: Bloom Filter와 무슨 차이인가?
> 의도: membership과 distinct count의 차이를 아는지 확인
> 핵심: Bloom은 존재 여부, HLL은 고유 원소 수다.

> Q: 실무에서 어디에 쓰나?
> 의도: 분석 시스템 감각 확인
> 핵심: unique visitor, DAU, distinct tenants, 로그 집계다.

## 한 줄 정리

HyperLogLog는 고유 원소 수를 매우 작은 메모리로 근사하는 대표적인 cardinality sketch다.
