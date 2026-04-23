# t-Digest

> 한 줄 요약: t-Digest는 tail percentile 근처에서 더 세밀한 해상도를 남기도록 centroid를 압축하는 quantile sketch로, p99 같은 극단 분위수 관측에 특히 강하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HDR Histogram](./hdr-histogram.md)
> - [DDSketch](./ddsketch.md)
> - [KLL Sketch](./kll-sketch.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)

> retrieval-anchor-keywords: t-digest, tdigest, quantile sketch, tail percentile, p99 telemetry, centroid sketch, weighted quantile summary, mergeable percentile, latency tail analysis, approximate percentile

## 핵심 개념

모든 quantile sketch가 분포 전체를 동일하게 다루는 것은 아니다.  
t-Digest는 특히 분포 양 끝, 즉 **tail percentile** 근처를 더 정밀하게 남기려는 구조다.

핵심 아이디어는 이렇다.

- 값들을 centroid 묶음으로 압축한다
- 중앙부는 더 크게 뭉칠 수 있다
- 양 끝 tail은 더 잘게 남긴다

즉 메모리를 일정하게 쓰면서도,  
평균이나 median보다 p99/p999 같은 극단 분위수에 더 민감한 요약을 만들려는 발상이다.

## 깊이 들어가기

### 1. 왜 tail percentile이 별도로 어렵나

latency observability에서는 흔히 평균보다 p99가 더 중요하다.  
문제는 tail은 샘플 수가 적고 변동성이 크다는 점이다.

- 중앙부는 많은 샘플이 몰려 평균적 특성이 잘 보인다
- tail은 드문 큰 값 몇 개가 의미를 크게 바꾼다

그래서 전체를 균등하게 압축하면 tail 정보가 쉽게 뭉개진다.  
t-Digest는 이걸 완화하려고 tail에 더 많은 표현력을 할당한다.

### 2. centroid와 compression 파라미터가 핵심이다

t-Digest는 개별 raw sample을 전부 남기지 않고 centroid로 요약한다.

- centroid는 평균값 근처 대표점
- weight는 해당 centroid가 대표하는 샘플 수

새 값이 들어오면 인접 centroid에 흡수되거나,  
압축 규칙에 따라 새로운 centroid가 만들어진다.

compression이 클수록:

- centroid 수가 늘 수 있고
- 메모리와 merge 비용이 커지지만
- tail quantile이 더 안정적일 수 있다

### 3. KLL / DDSketch와 어디서 갈리나

셋 다 quantile을 다루지만 성격이 꽤 다르다.

- KLL: rank-error 중심 compact summary
- DDSketch: 상대 값 오차를 설명하기 쉬움
- t-Digest: tail percentile 표현에 특히 민감

즉 "무엇을 잘 맞추고 싶은가"에 따라 선택이 갈린다.

- 전체 quantile rank 안정성
- wide-range 상대 오차
- 극단 tail percentile

### 4. merge-friendly하지만 순서 민감성도 고려해야 한다

t-Digest도 merge가 가능해서 분산 telemetry에 적합하다.  
다만 구현에 따라 입력 순서나 merge 전략이 결과에 영향을 줄 수 있다.

즉 "merge 가능"과 "항상 완전히 동일한 결과"는 다르다.  
실무에서는 라이브러리의 merge 안정성과 empirical accuracy를 같이 봐야 한다.

### 5. backend에서 어디에 맞나

tail latency가 운영 목표와 직접 연결되는 시스템에서 매력적이다.

- RPC p99/p999
- storage tail wait
- queue lag spike
- batch completion tail analysis

반대로 histogram 형태의 bucket 시각화가 중요하면  
HDR Histogram 쪽이 더 자연스럽다.

## 실전 시나리오

### 시나리오 1: API gateway p99

route별 p99를 강하게 보고 싶은데 raw sample을 다 중앙화하기 어렵다면  
t-Digest를 로컬에서 유지 후 merge하는 방식이 잘 맞을 수 있다.

### 시나리오 2: tail-heavy storage latency

평소엔 짧지만 가끔 크게 튀는 storage wait를 잡아야 하는 경우,  
tail 쪽 표현력이 중요한 sketch가 유리하다.

### 시나리오 3: percentile-only observability

버킷 histogram보다 p50/p95/p99/p999 값 자체가 중요하다면  
t-Digest는 compact summary로 실용적이다.

### 시나리오 4: 부적합한 경우

정확한 bucket distribution을 시각화해야 하거나  
relative error 보장을 명시해야 하는 경우엔 다른 구조가 더 적합할 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class TDigestSketch {
    private final List<Centroid> centroids = new ArrayList<>();
    private final int maxCentroids;

    public TDigestSketch(int maxCentroids) {
        this.maxCentroids = maxCentroids;
    }

    public void add(double value) {
        centroids.add(new Centroid(value, 1));
        if (centroids.size() > maxCentroids) {
            compress();
        }
    }

    public void merge(TDigestSketch other) {
        centroids.addAll(other.centroids);
        if (centroids.size() > maxCentroids) {
            compress();
        }
    }

    private void compress() {
        centroids.sort(Comparator.comparingDouble(c -> c.mean));
        List<Centroid> merged = new ArrayList<>();
        for (Centroid centroid : centroids) {
            if (merged.isEmpty()) {
                merged.add(centroid);
                continue;
            }
            Centroid last = merged.get(merged.size() - 1);
            if (merged.size() < maxCentroids) {
                merged.add(centroid);
                continue;
            }
            double totalWeight = last.weight + centroid.weight;
            last.mean = (last.mean * last.weight + centroid.mean * centroid.weight) / totalWeight;
            last.weight = totalWeight;
        }
        centroids.clear();
        centroids.addAll(merged);
    }

    private static final class Centroid {
        private double mean;
        private double weight;

        private Centroid(double mean, double weight) {
            this.mean = mean;
            this.weight = weight;
        }
    }
}
```

이 코드는 centroid 압축 감각만 보여준다.  
실제 t-Digest는 scale function, tail-aware merge 규칙, quantile interpolation이 더 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| t-Digest | tail percentile 표현력이 좋고 merge가 가능하다 | 구현/merge 세부에 따라 정확도 차이가 날 수 있다 | p99/p999 중심 observability |
| KLL Sketch | compact하고 rank-error 설명이 자연스럽다 | 극단 tail에 특화된 건 아니다 | 일반 percentile 요약 |
| DDSketch | 상대 값 오차를 설명하기 쉽다 | tail 중심 해상도 제어 방식은 다르다 | wide-range latency telemetry |
| HDR Histogram | bucket distribution을 함께 보기 좋다 | histogram layout 설정이 필요하다 | 분포와 percentile을 같이 보고 싶을 때 |

중요한 질문은 "어느 분위수 구간을 가장 잘 보고 싶은가"다.  
tail이 핵심이면 t-Digest가 강한 선택지가 된다.

## 꼬리질문

> Q: t-Digest가 tail percentile에 강한 이유는 무엇인가요?
> 의도: centroid 압축이 tail 표현력을 어떻게 바꾸는지 이해 확인
> 핵심: 양 끝 분포에서 더 작은 centroid를 유지해 극단 분위수 근처 해상도를 높이기 때문이다.

> Q: KLL과 가장 큰 차이는 무엇인가요?
> 의도: quantile sketch 종류를 구분하는지 확인
> 핵심: KLL은 compaction 기반 rank-summary이고, t-Digest는 centroid 기반 tail-aware summary다.

> Q: histogram 대신 t-Digest를 고르는 상황은 언제인가요?
> 의도: telemetry output 요구사항을 자료구조 선택과 연결하는지 확인
> 핵심: bucket 시각화보다 p99/p999 같은 percentile 값 자체가 더 중요할 때다.

## 한 줄 정리

t-Digest는 centroid 압축으로 tail percentile 해상도를 더 많이 남기는 quantile sketch라서, p99/p999 중심의 latency observability에 특히 잘 맞는다.
