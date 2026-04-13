# Heap Variants

> 한 줄 요약: Heap은 "가장 큰 것" 또는 "가장 작은 것"을 빨리 꺼내는 구조이고, 변형마다 삽입·삭제·갱신의 균형이 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [우선순위 기반 정렬 개념](../algorithm/sort.md)
> - [Greedy 알고리즘](../algorithm/greedy.md)
> - [LRU Cache Design](./lru-cache-design.md)

> retrieval-anchor-keywords: heap variants, binary heap, d-ary heap, pairing heap, min heap, max heap, priority queue, top-k, scheduler, decrease-key

## 핵심 개념

Heap은 완전 이진 트리를 바탕으로 한 **우선순위 저장 구조**다.  
정렬 전체를 유지하는 게 아니라, 루트에서 가장 우선순위가 높은 값만 빠르게 꺼낸다.

실무적으로 heap은 다음 문제에 자주 붙는다.

- 작업 스케줄링
- top-k 유지
- 타이머/이벤트 관리
- Dijkstra open set
- 메모리나 캐시 eviction 후보 관리

## 깊이 들어가기

### 1. binary heap이 기본인 이유

binary heap은 구현이 가장 단순하고, `insert`와 `poll`이 모두 `O(log n)`이다.

- 배열 기반으로 구현한다.
- 부모/자식 위치 계산이 쉽다.
- Java의 `PriorityQueue`도 사실상 이 계열이다.

### 2. d-ary heap은 왜 쓰나

자식이 2개가 아니라 `d`개인 heap이다.

장점:

- 트리 높이가 낮아진다.
- 삽입이나 반복적인 `decrease-key` 패턴에서 유리할 수 있다.

단점:

- `poll` 시 자식 비교가 많아진다.

즉, 연산 비율에 따라 `d`를 조정하는 구조다.

### 3. pairing heap / Fibonacci heap은 왜 등장했나

이론적으로는 `decrease-key`가 중요한 알고리즘에서 강력한 heap 변형이 있다.

하지만 실무에서는 구현 복잡도, 상수 비용, GC 압박 때문에 binary heap이 더 자주 쓰인다.

핵심은 "이론상 빠름"과 "현실에서 빠름"이 다를 수 있다는 점이다.

### 4. max heap과 min heap의 선택

- min heap: 가장 작은 값부터 뽑는다
- max heap: 가장 큰 값부터 뽑는다

문제의 방향이 달라질 뿐, 구조는 거의 같다.
top-k, 예약 스케줄, 임계값 관리에서는 어느 쪽이 루트가 되어야 하는지 먼저 정해야 한다.

## 실전 시나리오

### 시나리오 1: top-k hot items

조회수 상위 k개, 최근 클릭 상위 k개 같은 문제는 min heap을 써서 상위 k개만 유지하면 메모리를 아낄 수 있다.

### 시나리오 2: 작업 스케줄러

가장 빨리 실행해야 할 작업이나 deadline이 임박한 작업을 먼저 꺼내려면 priority queue가 잘 맞는다.

### 시나리오 3: 스트리밍 중간값

작은 값용 max heap과 큰 값용 min heap 두 개를 써서 median을 유지하는 패턴이 자주 나온다.

### 시나리오 4: 실무에서의 함정

heap은 "정렬된 자료구조"가 아니다.  
전체를 정렬해서 순회해야 하면 heap보다 다른 구조가 더 맞을 수 있다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class BinaryMinHeap {
    private final List<Integer> heap = new ArrayList<>();

    public void offer(int value) {
        heap.add(value);
        siftUp(heap.size() - 1);
    }

    public int poll() {
        if (heap.isEmpty()) {
            throw new IllegalStateException("empty heap");
        }
        int root = heap.get(0);
        int last = heap.remove(heap.size() - 1);
        if (!heap.isEmpty()) {
            heap.set(0, last);
            siftDown(0);
        }
        return root;
    }

    private void siftUp(int index) {
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (heap.get(parent) <= heap.get(index)) {
                return;
            }
            swap(parent, index);
            index = parent;
        }
    }

    private void siftDown(int index) {
        while (true) {
            int left = index * 2 + 1;
            int right = index * 2 + 2;
            int smallest = index;

            if (left < heap.size() && heap.get(left) < heap.get(smallest)) {
                smallest = left;
            }
            if (right < heap.size() && heap.get(right) < heap.get(smallest)) {
                smallest = right;
            }
            if (smallest == index) {
                return;
            }
            swap(index, smallest);
            index = smallest;
        }
    }

    private void swap(int a, int b) {
        int tmp = heap.get(a);
        heap.set(a, heap.get(b));
        heap.set(b, tmp);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Binary Heap | 구현이 쉽고 상수가 작다 | decrease-key가 약하다 | 일반적인 priority queue |
| d-ary Heap | 높이가 낮아질 수 있다 | poll 시 자식 비교가 많다 | 갱신 비율이 높은 우선순위 큐 |
| Pairing/Fibonacci Heap | 이론상 특정 연산이 강하다 | 구현과 실전 상수가 부담된다 | 이론 연구나 특수한 경우 |

실무에서는 "복잡한 heap"보다 "예측 가능한 heap"이 더 자주 이긴다.

## 꼬리질문

> Q: heap은 왜 전체 정렬이 아닌가?
> 의도: root만 빠른 구조라는 점을 이해하는지 확인
> 핵심: 루트만 보장되고, 나머지 순서는 부분적으로만 정렬된다.

> Q: d-ary heap은 언제 유리한가?
> 의도: 연산 패턴과 branching factor 균형을 이해하는지 확인
> 핵심: 높이를 줄이는 이득이 자식 비교 증가보다 클 때다.

> Q: top-k 문제에서 heap이 잘 맞는 이유는?
> 의도: streaming memory bound 감각 확인
> 핵심: 전체를 저장하지 않고 k개만 유지할 수 있기 때문이다.

## 한 줄 정리

Heap 변형은 모두 우선순위 접근을 빠르게 하지만, binary heap부터 d-ary heap까지 연산 패턴에 따라 실전 적합성이 달라진다.
