# Randomized vs Deterministic Quickselect

> 한 줄 요약: Quickselect는 k번째 원소를 찾는 선택 알고리즘이고, randomized는 평균 성능이 좋고 deterministic은 최악 보장을 노린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Quick Sort](./sort.md)
> - [Binary Search Patterns](./binary-search-patterns.md)
> - [Greedy 알고리즘](./greedy.md)

> retrieval-anchor-keywords: quickselect, randomized quickselect, deterministic selection, median of medians, kth element, selection algorithm, pivot, expected linear time, worst-case linear time

## 핵심 개념

Quickselect는 배열에서 k번째로 작은 원소를 찾는 알고리즘이다.

- randomized quickselect: pivot을 랜덤 선택
- deterministic quickselect: pivot을 일정한 규칙으로 선택해 최악 보장을 강화

목표는 정렬 전체가 아니라 **한 원소의 순위만** 찾는 것이다.

## 깊이 들어가기

### 1. randomized가 왜 실용적인가

랜덤 pivot을 쓰면 평균적으로 균형 잡힌 분할을 기대할 수 있다.

장점:

- 구현이 쉽다
- 기대 시간복잡도가 좋다

단점:

- 최악 경우는 여전히 나쁠 수 있다

### 2. deterministic quickselect는 무엇이 다르나

median of medians 같은 pivot 선택을 쓰면 최악 보장을 얻을 수 있다.

장점:

- worst-case가 안정적이다

단점:

- 상수가 크고 구현이 더 복잡하다

### 3. backend에서의 감각

top-k 임계값, 분위수, percentile 계산의 일부에서 select가 쓰일 수 있다.

- median
- p95 근사 전 단계
- threshold filtering

정렬 전체보다 k번째 값만 필요할 때 유용하다.

### 4. quicksort와 구분

quicksort는 양쪽을 모두 정렬하고, quickselect는 한쪽만 계속 따라간다.  
그래서 quickselect가 더 가볍다.

## 실전 시나리오

### 시나리오 1: k번째 임계값

상위 10%만 뽑기 전에 경계값을 찾을 때 쓸 수 있다.

### 시나리오 2: 분위수 계산

정렬 비용이 부담될 때, 필요한 순위 원소만 찾아낸다.

### 시나리오 3: 오판

전체 정렬이 필요한데 select를 쓰면 문제가 해결되지 않는다.

### 시나리오 4: 안정성

실시간/배치에서 worst-case를 더 신경 쓰면 deterministic 쪽을 고려할 수 있다.

## 코드로 보기

```java
import java.util.Random;

public class QuickSelect {
    private final Random random = new Random();

    public int kthSmallest(int[] arr, int k) {
        return select(arr, 0, arr.length - 1, k);
    }

    private int select(int[] arr, int left, int right, int k) {
        if (left == right) return arr[left];

        int pivotIndex = left + random.nextInt(right - left + 1);
        pivotIndex = partition(arr, left, right, pivotIndex);

        if (k == pivotIndex) return arr[k];
        if (k < pivotIndex) return select(arr, left, pivotIndex - 1, k);
        return select(arr, pivotIndex + 1, right, k);
    }

    private int partition(int[] arr, int left, int right, int pivotIndex) {
        int pivot = arr[pivotIndex];
        swap(arr, pivotIndex, right);
        int store = left;
        for (int i = left; i < right; i++) {
            if (arr[i] < pivot) swap(arr, store++, i);
        }
        swap(arr, store, right);
        return store;
    }

    private void swap(int[] arr, int a, int b) {
        int tmp = arr[a];
        arr[a] = arr[b];
        arr[b] = tmp;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Randomized Quickselect | 평균적으로 빠르고 간단하다 | 최악 보장이 없다 | 대부분의 실무/코테 |
| Deterministic Quickselect | 최악 보장을 노릴 수 있다 | 구현과 상수가 무겁다 | 안정성이 중요한 경우 |
| Full Sort | 결과가 명확하다 | 불필요하게 비싸다 | 전체 순서가 필요할 때 |

## 꼬리질문

> Q: quickselect와 quicksort의 차이는?
> 의도: 선택과 정렬의 차이를 아는지 확인
> 핵심: quickselect는 한 순위만 찾고, quicksort는 전체를 정렬한다.

> Q: randomized pivot이 왜 좋나?
> 의도: 평균 성능의 직관을 보는지 확인
> 핵심: 분할이 한쪽으로 치우칠 확률을 줄이기 때문이다.

> Q: deterministic은 왜 복잡한가?
> 의도: worst-case 보장 비용을 이해하는지 확인
> 핵심: 좋은 pivot을 고르기 위한 전처리와 상수가 필요하기 때문이다.

## 한 줄 정리

Quickselect는 k번째 원소만 빠르게 찾는 선택 알고리즘이고, randomized는 평균 성능, deterministic은 최악 보장을 노린다.
