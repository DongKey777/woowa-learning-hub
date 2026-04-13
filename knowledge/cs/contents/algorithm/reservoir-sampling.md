# Reservoir Sampling

> 한 줄 요약: Reservoir Sampling은 전체 크기를 모르는 스트림에서 모든 원소가 같은 확률로 뽑히도록 표본을 유지하는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Top-k Streaming and Heavy Hitters](./top-k-streaming-heavy-hitters.md)
> - [Heap Variants](../data-structure/heap-variants.md)
> - [상각 분석과 복잡도 함정](./amortized-analysis-pitfalls.md)

> retrieval-anchor-keywords: reservoir sampling, streaming sample, uniform sample, unknown stream length, random sampling, one pass, online sampling, unbiased sample, telemetry, log sampling

## 핵심 개념

Reservoir Sampling은 데이터가 스트림으로 들어올 때, 전체 길이를 모르는 상태에서도 `k`개의 샘플을 균등하게 유지하는 방법이다.

핵심 아이디어:

- 처음 `k`개는 그대로 담는다.
- `i`번째 원소가 오면 확률 `k / i`로 저장 후보가 된다.
- 저장되면 기존 reservoir 안의 원소 하나를 랜덤으로 교체한다.

이렇게 하면 마지막까지 각 원소가 뽑힐 확률이 동일해진다.

## 깊이 들어가기

### 1. 왜 스트림에서 필요하나

전체 데이터를 저장할 수 없거나, 저장해도 비용이 너무 큰 경우가 많다.

- 로그 샘플링
- 사용자 이벤트 추출
- 지표 계산용 대표 샘플
- A/B 분석의 사전 표본

전체를 다 보지 않아도 대표성을 가진 샘플이 필요할 때 유용하다.

### 2. 왜 균등한가

핵심은 "현재까지 본 모든 원소가 같은 생존 확률을 갖도록 설계하는 것"이다.

처음 `k`개는 유리해 보이지만, 뒤에 들어오는 원소가 점점 더 높은 확률로 교체를 시도하면서 전체 균형이 맞춰진다.

이건 수학적으로 증명할 수 있지만, 실전 감각으로는 "새 원소가 늦게 와도 충분히 들어올 기회를 갖게 만든다"라고 이해하면 된다.

### 3. backend에서의 활용

샘플링은 관측 가능성과 비용 사이의 균형이다.

- 대량 로그에서 일부만 남겨 디버깅
- 메트릭 분포를 대략적으로 추정
- 이상 이벤트의 축약본 확보

### 4. 주의할 점

Reservoir Sampling은 "자주 나타나는 원소를 더 많이 뽑는" 기법이 아니다.  
그건 heavy hitters 문제다.

즉 목적이 다르다.

## 실전 시나리오

### 시나리오 1: 로그 샘플링

초당 수십만 건의 로그에서 전체를 저장할 수 없을 때, 균등 샘플을 남기면 사후 분석이 쉬워진다.

### 시나리오 2: 사용자 이벤트 대표본

클릭 스트림에서 전체 분포를 그대로 저장하지 못할 때, reservoir sample로 대표 집합을 유지한다.

### 시나리오 3: 오판

핫한 키만 골라 보고 싶다면 reservoir sampling이 아니라 top-k/heavy hitters가 맞다.

### 시나리오 4: 온라인 실험

실험 그룹에서 임의 사용자 샘플을 실시간으로 유지해 후속 분석을 할 때 쓸 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

public class ReservoirSampler<T> {
    private final int k;
    private final List<T> reservoir = new ArrayList<>();
    private long seen = 0;

    public ReservoirSampler(int k) {
        this.k = k;
    }

    public void accept(T item) {
        seen++;
        if (reservoir.size() < k) {
            reservoir.add(item);
            return;
        }

        long pick = ThreadLocalRandom.current().nextLong(seen) + 1;
        if (pick <= k) {
            reservoir.set((int) (pick - 1), item);
        }
    }

    public List<T> sample() {
        return new ArrayList<>(reservoir);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Reservoir Sampling | 한 번만 보고도 균등 샘플을 만든다 | 빈도 기반 정보는 보존하지 않는다 | 대표 샘플이 필요할 때 |
| 랜덤 저장 | 구현이 쉽다 | 편향이 생길 수 있다 | 데이터가 작을 때 |
| 전체 저장 후 샘플링 | 단순하고 정확하다 | 메모리 비용이 크다 | 스트림이 작을 때 |

Reservoir Sampling은 "모든 원소를 공평하게 한 자리씩 시험해볼 기회"를 준다.

## 꼬리질문

> Q: 왜 전체 길이를 몰라도 되나?
> 의도: 온라인 알고리즘 감각 확인
> 핵심: 현재까지 본 개수 `i`만으로 교체 확률을 정하기 때문이다.

> Q: 균등 샘플과 heavy hitter의 차이는?
> 의도: 샘플링과 빈도 추적 구분 확인
> 핵심: 샘플링은 대표성, heavy hitter는 자주 나오는 항목 탐지다.

> Q: 실무에서 어디에 쓰나?
> 의도: 분석/관측 관점 연결 확인
> 핵심: 로그, 메트릭, A/B 분석, 품질 진단이다.

## 한 줄 정리

Reservoir Sampling은 스트림 전체를 모르는 상태에서도 균등한 확률로 샘플을 유지하는 온라인 샘플링 기법이다.
