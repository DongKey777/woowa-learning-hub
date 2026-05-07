---
schema_version: 3
title: DDSketch
concept_id: data-structure/ddsketch
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- ddsketch
- quantile-sketch
- latency-p99-observability
aliases:
- DDSketch
- relative error quantile sketch
- latency p99 sketch
- mergeable percentile telemetry
- log bucket sketch
- wide range latency quantile
- approximate percentile
symptoms:
- latency p99를 raw sample 없이 근사해야 하는데 absolute error와 relative error 보장 차이를 구분하지 못한다
- wide dynamic range telemetry에서 작은 값과 큰 값을 같은 절대 오차로 다루어 percentile 해석이 왜곡된다
- DDSketch, HDR Histogram, KLL, t-Digest를 모두 quantile sketch로만 묶고 merge와 error model 차이를 놓친다
intents:
- comparison
- deep_dive
prerequisites:
- data-structure/sketch-filter-selection-playbook
next_docs:
- data-structure/hdr-histogram
- data-structure/kll-sketch
- data-structure/t-digest
- data-structure/sketch-filter-selection-playbook
linked_paths:
- contents/data-structure/hdr-histogram.md
- contents/data-structure/kll-sketch.md
- contents/data-structure/t-digest.md
- contents/data-structure/sketch-filter-selection-playbook.md
- contents/data-structure/hyperloglog.md
- contents/data-structure/approximate-counting-rate-limiting-observability.md
confusable_with:
- data-structure/hdr-histogram
- data-structure/kll-sketch
- data-structure/t-digest
- data-structure/hyperloglog
forbidden_neighbors: []
expected_queries:
- DDSketch는 latency p99에서 relative error를 어떻게 보장해?
- wide range latency telemetry에서 absolute error보다 relative error가 중요한 이유는?
- DDSketch와 HDR Histogram KLL t-Digest를 어떤 기준으로 비교해?
- log bucket quantile sketch가 merge-friendly하다는 뜻은?
- p99 observability에서 raw sample 없이 percentile을 근사하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 DDSketch를 로그 버킷과 상대 오차 보장을 사용하는 merge-friendly
  quantile sketch로 설명한다. latency p99, wide dynamic range telemetry,
  relative error, HDR Histogram, KLL, t-Digest와의 선택 기준을 다룬다.
---
# DDSketch

> 한 줄 요약: DDSketch는 값 크기에 비례한 상대 오차를 보장하면서 quantile을 근사하는 merge-friendly telemetry sketch로, wide-range latency p99 관측에 특히 잘 맞는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HDR Histogram](./hdr-histogram.md)
> - [KLL Sketch](./kll-sketch.md)
> - [t-Digest](./t-digest.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [HyperLogLog](./hyperloglog.md)
> - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)

> retrieval-anchor-keywords: ddsketch, relative error quantile sketch, quantile sketch, kll sketch, latency p99, mergeable sketch, percentile telemetry, log bucket sketch, wide-range latency, observability sketch, approximate percentile

## 핵심 개념

percentile telemetry에서 어려운 점은 두 가지다.

- 값 범위가 매우 넓다
- raw sample을 다 저장할 수 없다

DDSketch는 값을 로그 스케일 버킷에 매핑해,  
`x`라는 값에 대해 대략 `x * (1 ± alpha)` 수준의 **상대 오차**를 유지하려고 한다.

즉 작은 값과 큰 값 모두에서 "비슷한 비율의 정확도"를 지키는 quantile sketch다.

## 깊이 들어가기

### 1. 왜 percentile에 상대 오차가 중요한가

tail latency는 `2ms`와 `200ms`를 같은 절대 오차로 다루면 의미가 달라진다.

- `2ms`에서 1ms 오차는 치명적
- `200s`에서 1ms 오차는 사실상 무의미

DDSketch는 bucket 폭을 로그적으로 키워  
값이 커져도 비슷한 상대 정밀도를 유지하려 한다.

### 2. log mapping이 핵심이다

값 `v`를 bucket index로 바꾸는 기본 감각은 이렇다.

- `index = floor(log_gamma(v))`
- `gamma`는 허용 상대 오차에 따라 정해짐

그래서 값이 커질수록 bucket 간 간격도 커진다.  
하지만 비율 기준으로 보면 오차 통제가 일정하다.

이 구조의 장점:

- wide dynamic range에 강하다
- merge가 단순하다
- quantile 질의가 빠르다

### 3. HDR Histogram과 어떻게 다른가

둘 다 wide-range telemetry에 쓰이지만 결이 다르다.

- HDR Histogram: histogram 레이아웃이 더 명시적이고 percentile 계산이 직관적
- DDSketch: 상대 오차 보장 관점이 더 직접적

실무 판단은 보통 다음 질문으로 갈린다.

- percentile 오차를 어떤 방식으로 설명하고 싶은가
- range 상한을 얼마나 명시적으로 정하고 싶은가
- 기존 observability stack이 무엇을 지원하는가

### 4. merge 가능한 quantile sketch라는 점이 운영상 중요하다

분산 서비스는 shard별, instance별 sketch를 합쳐 전체 p99를 보고 싶어 한다.  
DDSketch는 같은 설정이면 bucket count를 단순 합산해 merge할 수 있다.

- per-process local sketch
- per-host aggregation
- per-minute rollup

즉 raw latency event를 다 옮기지 않고도,  
중앙 집계 계층에서 approximate percentile을 다시 만들 수 있다.

### 5. sketch가 측정 의미를 대신해주진 않는다

DDSketch는 저장/요약 구조다.  
무엇을 측정했는지, sampling bias가 있는지, coordinated omission이 있는지는 별개 문제다.

그래서 telemetry에서 꼭 같이 봐야 한다.

- client-perceived latency인지
- server handler latency인지
- retry 포함인지
- timeout된 요청을 어떻게 넣는지

## 실전 시나리오

### 시나리오 1: high-cardinality route latency

route, tenant, status별 latency를 모두 raw sample로 저장하기 어렵다면  
각 key마다 DDSketch를 유지해 p95/p99를 메모리 효율적으로 볼 수 있다.

### 시나리오 2: wide-range storage latency

정상 시에는 수백 us, 장애 시에는 수초까지 튀는 디스크/queue wait는  
상대 오차 기반 sketch가 특히 잘 맞는다.

### 시나리오 3: distributed percentile aggregation

edge, gateway, app instance에서 각각 스케치를 만든 뒤  
상위 집계 계층에서 합치면 raw stream을 중앙화하지 않아도 된다.

### 시나리오 4: 부적합한 경우

정확한 percentile 재현이 반드시 필요하거나, raw sample forensic이 중요하면  
sketch만으로는 부족하다.

## 코드로 보기

```java
import java.util.HashMap;
import java.util.Map;

public class DdSketch {
    private final double relativeAccuracy;
    private final double gamma;
    private final Map<Integer, Long> buckets = new HashMap<>();
    private long zeroCount = 0L;

    public DdSketch(double relativeAccuracy) {
        if (relativeAccuracy <= 0 || relativeAccuracy >= 1) {
            throw new IllegalArgumentException("relativeAccuracy must be between 0 and 1");
        }
        this.relativeAccuracy = relativeAccuracy;
        this.gamma = (1 + relativeAccuracy) / (1 - relativeAccuracy);
    }

    public void add(double value) {
        if (value <= 0) {
            zeroCount++;
            return;
        }
        int index = (int) Math.floor(Math.log(value) / Math.log(gamma));
        buckets.merge(index, 1L, Long::sum);
    }

    public void merge(DdSketch other) {
        if (Double.compare(relativeAccuracy, other.relativeAccuracy) != 0) {
            throw new IllegalArgumentException("incompatible DDSketch configuration");
        }
        zeroCount += other.zeroCount;
        other.buckets.forEach((index, count) -> buckets.merge(index, count, Long::sum));
    }
}
```

이 코드는 log bucket 감각만 보여준다.  
실전 DDSketch는 양수/음수 분리, dense store, collapsing policy, quantile 조회 로직이 더 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DDSketch | 상대 오차 기반 quantile 보장이 직관적이고 merge가 쉽다 | raw sample은 잃고 버킷 설계가 필요하다 | p99 latency telemetry, wide-range metric |
| HDR Histogram | histogram 기반 해석이 쉽고 널리 쓰인다 | precision/range 설정 감각이 필요하다 | mergeable latency histogram이 필요할 때 |
| Raw sample 저장 | 나중 분석 자유도가 가장 높다 | 비용이 크다 | 샘플 수가 작거나 forensic이 중요할 때 |
| HyperLogLog | distinct count에 특화되어 매우 가볍다 | quantile은 계산할 수 없다 | cardinality가 목적일 때 |

중요한 질문은 "몇 번째 백분위를 알고 싶은가"와 "그 정확도를 절대/상대 오차 중 무엇으로 설명할 것인가"다.

## 꼬리질문

> Q: DDSketch가 HDR Histogram보다 더 적합한 경우는 언제인가요?
> 의도: 상대 오차 개념을 percentile 관측과 연결하는지 확인
> 핵심: wide-range 값에서 상대 오차 보장을 직접 설명하고 싶을 때다.

> Q: 왜 log bucket을 쓰나요?
> 의도: wide dynamic range 처리 감각 확인
> 핵심: 값이 커질수록 bucket 폭도 같이 커져 상대 정밀도를 유지하기 쉽기 때문이다.

> Q: merge 가능한 sketch가 왜 중요한가요?
> 의도: 분산 telemetry 집계 감각 확인
> 핵심: raw event를 중앙으로 다 보내지 않고도 전체 percentile을 근사할 수 있기 때문이다.

## 한 줄 정리

DDSketch는 wide-range telemetry에서 값 크기에 비례한 상대 오차를 유지하며 percentile을 근사하고 합산할 수 있게 해주는 실전형 quantile sketch다.
