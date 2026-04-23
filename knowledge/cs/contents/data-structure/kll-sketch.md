# KLL Sketch

> 한 줄 요약: KLL Sketch는 적은 메모리로 quantile을 근사하기 위해 표본을 계층적으로 압축하는 merge-friendly 구조로, percentile telemetry와 분포 비교에 잘 맞는 rank-error 기반 요약 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HDR Histogram](./hdr-histogram.md)
> - [DDSketch](./ddsketch.md)
> - [t-Digest](./t-digest.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)

> retrieval-anchor-keywords: kll sketch, quantile sketch, rank error, percentile approximation, mergeable sketch, latency percentile, compact quantile summary, streaming quantile, telemetry sketch, approximate median

## 핵심 개념

percentile을 보고 싶다고 해서 값을 전부 정렬해 둘 수는 없다.  
스트림이 길고 key cardinality가 높아질수록 메모리가 먼저 무너진다.

KLL Sketch는 값을 레벨별 buffer에 모아 두고,  
가득 차면 일부만 남기며 위 레벨로 올리는 방식으로 분포를 요약한다.

핵심 감각은 이렇다.

- raw sample 전체는 저장하지 않는다
- 대신 quantile 계산에 필요한 대표 표본만 남긴다
- merge가 가능해 분산 집계에 잘 맞는다

즉 정확한 값 재현이 아니라 **정렬 순서상 대략 어느 위치인지**를 싸게 추정하는 구조다.

## 깊이 들어가기

### 1. KLL이 보장하는 것은 value error보다 rank error에 가깝다

KLL은 보통 "이 값이 전체에서 몇 번째쯤인가"를 잘 맞추는 구조다.

- p50 근처인지
- p95 근처인지
- median보다 위/아래인지

즉 `100ms`를 `102ms`로 맞추는 절대값 정확도보다  
**전체 정렬에서의 위치(rank)** 를 얼마나 잘 보존하는지가 더 중요하다.

이 관점이 중요한 이유는 DDSketch와 결이 다르기 때문이다.

- DDSketch: 값 크기에 대한 상대 오차를 설명하기 쉽다
- KLL: quantile 순위 오차를 설명하기 쉽다

### 2. compaction이 구조의 핵심이다

각 레벨 buffer에 값이 쌓이다가 임계치를 넘으면 compaction이 일어난다.

- 값을 정렬한다
- 절반 정도만 남긴다
- 남긴 값은 더 큰 가중치를 갖고 위 레벨로 이동한다

이렇게 레벨이 올라갈수록 표본 수는 줄지만, 각 값이 대표하는 범위는 넓어진다.

즉 공간을 아끼는 대가로 일부 정보는 버리되,  
quantile 질의에 필요한 순서 정보는 최대한 유지하려는 발상이다.

### 3. 왜 merge-friendly한가

분산 시스템은 shard별, instance별로 latency를 측정하고 나중에 합친다.  
KLL Sketch는 같은 설정이라면 각 레벨 buffer를 합쳐 다시 compaction할 수 있다.

- process local sketch
- shard aggregator
- minute/hour rollup

이 성질 덕분에 raw sample을 중앙에 모두 모으지 않고도  
approximate percentile을 재계산할 수 있다.

### 4. HDR Histogram / DDSketch와 어디서 갈리나

셋 다 percentile 관측에 쓰일 수 있지만 사고방식이 다르다.

- HDR Histogram: histogram bucket 기반
- DDSketch: 상대 오차 bucket 기반
- KLL: compaction 기반 quantile summary

KLL은 특히 다음 질문에 잘 맞는다.

- "rank 오차를 작게 유지하고 싶은가?"
- "분포 모양을 요약하고 싶은가?"
- "정확한 bucket 경계를 설계하고 싶지 않은가?"

### 5. backend에서의 함정

KLL도 측정 의미를 자동으로 정리해주진 않는다.

- timeout 샘플을 어떻게 넣는가
- retry 전/후 latency를 분리했는가
- coordinated omission이 있는가

또 low-latency hot path에서는 buffer 정렬/compaction 비용이 있으므로,  
per-request path에 무분별하게 넣기보다 batch/telemetry thread에서 다루는 편이 낫다.

## 실전 시나리오

### 시나리오 1: route별 latency percentile

모든 route와 tenant 조합의 raw latency를 오래 들고 있긴 어렵지만,  
KLL Sketch라면 key별로 compact한 분포 요약을 유지할 수 있다.

### 시나리오 2: 배치 분석에서 분포 비교

두 릴리즈의 latency 분포를 median, p95, p99 기준으로 비교하고 싶을 때  
정렬 전체 대신 KLL 요약끼리 비교할 수 있다.

### 시나리오 3: merge 중심 telemetry 파이프라인

에지, 앱 서버, 집계기에서 점진적으로 sketch를 합치는 구조라면  
KLL의 merge-friendly 특성이 유용하다.

### 시나리오 4: 부적합한 경우

절대/상대 값 오차를 직접 설명해야 하거나,  
bucket histogram 자체가 필요한 대시보드라면 HDR/DDSketch가 더 맞을 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class KllSketch {
    private final List<List<Double>> levels = new ArrayList<>();
    private final int capacityPerLevel;

    public KllSketch(int capacityPerLevel) {
        this.capacityPerLevel = capacityPerLevel;
        levels.add(new ArrayList<>());
    }

    public void add(double value) {
        levels.get(0).add(value);
        compactIfNeeded(0);
    }

    public void merge(KllSketch other) {
        while (levels.size() < other.levels.size()) {
            levels.add(new ArrayList<>());
        }
        for (int i = 0; i < other.levels.size(); i++) {
            levels.get(i).addAll(other.levels.get(i));
            compactIfNeeded(i);
        }
    }

    private void compactIfNeeded(int level) {
        if (levels.get(level).size() <= capacityPerLevel) {
            return;
        }
        Collections.sort(levels.get(level));
        if (levels.size() == level + 1) {
            levels.add(new ArrayList<>());
        }
        List<Double> next = levels.get(level + 1);
        List<Double> current = levels.get(level);
        for (int i = 1; i < current.size(); i += 2) {
            next.add(current.get(i));
        }
        current.clear();
        compactIfNeeded(level + 1);
    }
}
```

이 코드는 개념 스케치다.  
실제 KLL은 randomization, level size 조절, weighted query 계산까지 더 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| KLL Sketch | compact하고 merge-friendly하며 quantile rank 추정에 강하다 | raw sample과 exact value 오차 설명은 약하다 | percentile telemetry, 분포 비교, streaming quantile |
| DDSketch | 상대 값 오차 설명이 직관적이다 | log bucket 설정 감각이 필요하다 | wide-range p99 telemetry |
| HDR Histogram | bucket histogram 기반 해석이 쉽다 | precision/range 설정이 필요하다 | latency histogram과 percentile을 함께 보고 싶을 때 |
| Raw sample 저장 | 어떤 분석도 다시 할 수 있다 | 비용이 크다 | 샘플 수가 작거나 forensic 분석이 중요할 때 |

중요한 질문은 "값 오차를 설명할 것인가"보다 "quantile 위치 오차를 얼마나 작게 유지할 것인가"다.

## 꼬리질문

> Q: KLL Sketch는 무엇을 잘 보장하나요?
> 의도: rank-error와 value-error를 구분하는지 확인
> 핵심: 특정 값의 절대 오차보다 quantile 위치(rank) 오차를 작게 유지하는 데 강하다.

> Q: DDSketch와 가장 큰 차이는 무엇인가요?
> 의도: quantile sketch 종류를 섞지 않는지 확인
> 핵심: KLL은 compaction 기반 rank-summary이고, DDSketch는 log-bucket 기반 상대 오차 sketch다.

> Q: 왜 merge가 중요한가요?
> 의도: 분산 telemetry 집계 감각 확인
> 핵심: shard별 local sketch를 raw sample 없이 합쳐 전체 percentile을 근사할 수 있기 때문이다.

## 한 줄 정리

KLL Sketch는 적은 메모리로 분포의 rank 정보를 유지하며 percentile을 근사하는 compact quantile summary로, merge가 쉬워 분산 telemetry와 배치 분석에 잘 맞는다.
