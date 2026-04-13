# Top-k Streaming and Heavy Hitters

> 한 줄 요약: Top-k streaming과 heavy hitters는 스트림에서 자주 나오는 항목만 작은 메모리로 추적하는 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Reservoir Sampling](./reservoir-sampling.md)
> - [Heap Variants](../data-structure/heap-variants.md)
> - [Fenwick Tree (Binary Indexed Tree)](../data-structure/fenwick-tree.md)

> retrieval-anchor-keywords: top-k streaming, heavy hitters, frequent items, space saving, count min sketch, approximate frequency, hot keys, streaming analytics, sketch, cardinality

## 핵심 개념

Top-k streaming은 데이터가 계속 들어오는 상황에서 가장 많이 등장한 항목 상위 k개를 유지하는 문제다.  
heavy hitters는 그중 특히 자주 등장하는 항목들을 의미한다.

핵심은 전체를 저장하지 않고도 "자주 나오는 것"을 근사하거나 추적하는 것이다.

- 로그 상 hot endpoint
- 인기 검색어
- 급격히 몰리는 사용자/상품
- 장애를 일으키는 hot key

이건 reservoir sampling과 다르다.

- Reservoir Sampling: 균등 샘플
- Heavy Hitters: 빈도 상위 항목

## 깊이 들어가기

### 1. 왜 어려운가

스트림은 길이가 길고, 항목 종류도 많다.  
정확한 카운트를 전부 저장하면 메모리가 터질 수 있다.

그래서 보통 다음 중 하나를 쓴다.

- 작은 힙으로 top-k 후보만 유지
- counter를 일부만 유지하는 Misra-Gries/Space-Saving
- 확률적 스케치로 빈도를 근사

### 2. heap 기반 top-k

가장 직관적인 방식은 `count`를 해시맵에 쌓고, top-k는 최소 힙으로 관리하는 것이다.

장점:

- 구현이 쉽다
- 정확한 top-k를 얻을 수 있다

단점:

- 고유 항목 수가 너무 많으면 hash map이 커진다

### 3. heavy hitter 근사

빈도가 아주 높은 항목은 근사 알고리즘으로도 잘 잡힌다.

- Misra-Gries: k-1개 후보를 유지
- Space-Saving: 교체 전략을 더 공격적으로 사용
- Count-Min Sketch: 빈도를 빠르게 근사

실무에서는 정확도보다 메모리와 처리량이 더 중요한 경우가 많다.

### 4. backend에서의 중요성

heavy hitters는 observability와 직결된다.

- 어떤 API가 가장 많이 호출되는가
- 어떤 key가 캐시를 오염시키는가
- 어떤 tenant가 리소스를 독식하는가
- 어떤 상품이 순간적으로 폭발했는가

## 실전 시나리오

### 시나리오 1: top-k endpoint

실시간 API 로그에서 가장 많이 호출된 endpoint를 상위 k개만 보고 싶을 때 유용하다.

### 시나리오 2: hot key 탐지

분산 캐시나 저장소에서 특정 key가 너무 많이 읽히면 병목이 된다.  
heavy hitters로 이를 빠르게 찾을 수 있다.

### 시나리오 3: 트래픽 급증 분석

짧은 시간에 몰리는 이벤트를 추적하면 어떤 항목이 시스템을 흔드는지 볼 수 있다.

### 시나리오 4: 오판

균등 샘플링으로는 heavy hitter를 안정적으로 찾을 수 없다.  
목적이 다르기 때문에 도구를 구분해야 한다.

## 코드로 보기

```java
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

public class TopKStream {
    private final int k;
    private final Map<String, Long> counts = new HashMap<>();

    public TopKStream(int k) {
        this.k = k;
    }

    public void accept(String item) {
        counts.put(item, counts.getOrDefault(item, 0L) + 1);
    }

    public Map<String, Long> snapshot() {
        PriorityQueue<Entry> heap = new PriorityQueue<>((a, b) -> Long.compare(a.count, b.count));
        for (Map.Entry<String, Long> entry : counts.entrySet()) {
            heap.offer(new Entry(entry.getKey(), entry.getValue()));
            if (heap.size() > k) {
                heap.poll();
            }
        }

        Map<String, Long> result = new HashMap<>();
        for (Entry entry : heap) {
            result.put(entry.item, entry.count);
        }
        return result;
    }

    private static final class Entry {
        final String item;
        final long count;

        Entry(String item, long count) {
            this.item = item;
            this.count = count;
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 정확한 top-k + heap | 결과가 명확하다 | 메모리 사용이 커질 수 있다 | 고유 항목 수가 제한적일 때 |
| Misra-Gries / Space-Saving | 메모리 효율이 좋다 | 근사 결과다 | 스트림이 크고 대략적 top-k면 충분할 때 |
| Count-Min Sketch | 빠르고 작다 | 충돌 때문에 오차가 있다 | 빈도 근사가 중요할 때 |

heavy hitters는 "정확도 조금"과 "운영 가능성 크게" 사이의 선택이다.

## 꼬리질문

> Q: top-k streaming과 reservoir sampling의 차이는?
> 의도: 샘플링과 빈도 추적 구분 확인
> 핵심: top-k는 많이 나온 것을 찾고, reservoir는 무작위 대표본을 만든다.

> Q: 왜 heap이 잘 맞나?
> 의도: 실시간 상위 후보 유지 감각 확인
> 핵심: 작은 k개만 계속 갱신하면 되기 때문이다.

> Q: hot key 탐지에 왜 중요한가?
> 의도: 분산 시스템 병목과 연결되는지 확인
> 핵심: 가장 자주 접근되는 key가 전체 성능을 좌우할 수 있다.

## 한 줄 정리

Top-k streaming과 heavy hitters는 스트림에서 자주 등장하는 항목을 작은 메모리로 추적하는 실전형 빈도 분석 기법이다.
