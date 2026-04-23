# Eytzinger Layout and Cache-Friendly Search

> 한 줄 요약: Eytzinger layout은 정렬된 배열을 완전 이진트리 순서로 재배치해, binary search의 분기와 메모리 접근 패턴을 더 cache-friendly하게 만들려는 배열 레이아웃 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [Ordered Search Workload Matrix](./ordered-search-workload-matrix.md)
> - [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md)
> - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
> - [Heap Variants](./heap-variants.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)

> retrieval-anchor-keywords: eytzinger layout, cache-friendly binary search, implicit binary tree array, branch-friendly search, array search layout, binary search locality, heap order array layout, cache-aware search, search layout optimization, static search structure, branchless lower bound, eytzinger vs binary search, blocked search layout, eytzinger lower_bound, point lookup layout, prefetch friendly search, eytzinger vs van emde boas, lower_bound scan-heavy path, ordered search layout comparison, ordered search workload matrix

## 핵심 개념

정렬된 배열에 대한 binary search는 빅오로 보면 이미 좋다.  
하지만 실제 CPU에서는 mid jump가 메모리와 branch prediction 측면에서 늘 최선은 아니다.

Eytzinger layout은 배열을 다음처럼 다시 놓는다.

- 값 자체는 정렬 집합을 표현하지만
- 메모리 배치는 완전 이진트리의 level-order

즉 binary search의 "계산 순서"보다  
**CPU가 밟게 될 메모리 순서**를 더 유리하게 재배치하려는 기법이다.

## 깊이 들어가기

### 1. 왜 plain binary search가 실전에서 아쉬울 수 있나

plain binary search는 비교 횟수는 적다.  
문제는 access pattern이 넓게 뛰어다닌다는 점이다.

- mid
- left mid
- right mid
- 그다음 mid

이 점프 패턴은 prefetch와 cache locality에 불리할 수 있다.

### 2. Eytzinger는 배열을 implicit tree처럼 쓴다

보통 인덱스 관계는 heap과 비슷하다.

- root: 1
- left child: `2i`
- right child: `2i + 1`

즉 이미 정렬된 데이터를 "찾기 쉬운 비교 순서"가 아니라  
"메모리에서 예측 가능한 tree walk"에 맞게 다시 놓는다.

### 3. 왜 cache-friendly가 될 수 있나

상위 레벨 노드들이 앞쪽에 촘촘히 모이므로  
탐색 초반에 자주 보는 값들이 같은 cache line 근처에 놓이기 쉽다.

특히 상위 1~3 레벨은 거의 모든 질의가 공통으로 밟기 때문에  
작은 working set으로 앞부분을 재사용하기 쉽다.

또 일부 구현은 speculative prefetch와 잘 맞는다.  
즉 단순한 binary search보다 실제 하드웨어에서 더 좋은 locality를 낼 수 있다.

### 4. 실전 구현은 `contains`보다 `lower_bound` 감각이 중요하다

교재 예시는 `contains`에서 멈추지만 실전 검색은 다음이 더 자주 나온다.

- `lower_bound`
- predecessor / successor
- block boundary 찾기

Eytzinger는 `i -> 2i`, `2i + 1` 전개가 단순해서  
branchless compare-update나 다음 자식 prefetch 같은 미세 최적화와 잘 맞는다.  
즉 핵심은 "힙처럼 저장한다"가 아니라  
**정적 ordered search 경로를 CPU가 다루기 쉬운 패턴으로 만든다**는 데 있다.

### 5. `lower_bound` 이후의 다음 행동이 Eytzinger 적합도를 가른다

실전 API는 대개 "찾았나?"에서 끝나지 않는다.

- 첫 `>= target` 위치를 찾고
- 그 뒤 몇 개 원소를 더 읽거나
- predecessor / successor를 이어서 계산한다

이때 Eytzinger는 **검색 경로**는 매우 잘 다루지만,  
정렬 순서가 메모리에 그대로 놓여 있지 않아서 scan 시작점을 복구하는 감각은 plain array보다 덜 직선적이다.

즉:

- point lookup, exact boundary hit: Eytzinger가 강하다
- `lower_bound` 뒤에 인접 원소를 길게 읽음: blocked/B-Tree형 배열이나 plain sorted array가 더 자연스러울 수 있다

중요한 질문은 "lookup 직후에 끝나는가, 아니면 scan이 이어지는가"다.

이 선택축을 vEB-style cache-oblivious layout까지 포함해 비교하면  
Eytzinger는 search path 단순성과 prefetch friendliness가 강점이고,  
blocked array와 vEB는 scan 연계 또는 계층 독립 locality에서 다른 답을 준다.  
빠른 triage 표는 [Ordered Search Workload Matrix](./ordered-search-workload-matrix.md)에 따로 정리했다.  
자세한 비교는 [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)에서 이어 볼 수 있다.

### 6. 상위 레벨 재사용과 speculative prefetch가 실제 이득의 핵심이다

Eytzinger의 장점은 leaf까지 다 도달한 뒤가 아니라  
거의 모든 질의가 공통으로 밟는 상위 레벨에 있다.

- root와 상위 비교값이 앞부분 working set에 모인다
- 다음 자식 인덱스가 단순해서 prefetch hint를 걸기 쉽다
- binary search보다 branchless compare-update와 궁합이 좋다

그래서 전체 비교 횟수는 비슷해도,  
초반 몇 단계의 cache line 재사용과 miss overlap에서 차이가 날 수 있다.

반대로 데이터가 아주 작아 L1에 다 들어가거나,  
lookup 뒤에 정렬 순회가 길게 이어지면 이 이점은 빠르게 줄어든다.

### 7. Eytzinger가 항상 종착점은 아니다

선택축은 보통 이렇게 나뉜다.

- plain sorted array + binary search: 정렬 순서 그대로 순회하거나 구현 단순성이 가장 중요할 때
- Eytzinger: point lookup이 hot이고 read-mostly라서 재배치를 감당할 수 있을 때
- blocked/B-Tree형 배열 배치: fan-out과 page/block locality, range scan 연결도 함께 중요할 때
- pointer tree / skip list: 업데이트가 잦고 ordered mutation이 중요한 경우

즉 Eytzinger는 "정적 검색 최적화의 강한 후보"이지  
모든 ordered index의 종착점은 아니다.

### 8. 언제 잘 맞고 언제 안 맞나

잘 맞는 경우:

- immutable / read-mostly 정적 배열
- point lookup/search
- rebuild 비용을 감당할 수 있음

안 맞는 경우:

- 삽입/삭제가 잦은 구조
- range update가 많은 구조
- 정렬 배열을 그대로 유지해야 하는 경우

즉 dynamic structure가 아니라  
**정적 검색 레이아웃 최적화**에 가깝다.

### 9. backend에서 어디에 맞나

read-heavy dictionary나 static search table에 잘 어울린다.

- immutable config key table
- block boundary search
- prefix dictionary 보조 인덱스
- static routing table

즉 "트리는 아닌데 검색 성능을 더 짜고 싶다"는 곳에서 가치가 있다.

## 실전 시나리오

### 시나리오 1: immutable boundary table

block boundary, fence pointer, bucket threshold 같은 정적 경계값 탐색에서  
plain binary search보다 나은 locality를 기대할 수 있다.

### 시나리오 2: compact in-memory lookup table

포인터 기반 tree는 과하고,  
정렬 배열 search를 더 빠르게 만들고 싶다면 검토할 수 있다.

### 시나리오 3: page/block 단위 index에는 다른 layout이 나을 수 있다

LSM fence pointer나 큰 boundary table처럼  
fan-out과 range scan 연결이 함께 중요하면 blocked search array나 B-Tree형 layout이 더 현실적일 수 있다.

### 시나리오 4: 부적합한 update-heavy table

입력값이 자주 바뀌면 재배치 비용이 커져  
레이아웃 이득이 쉽게 상쇄된다.

### 시나리오 5: 부적합한 경우

정렬 순회와 삽입이 동시에 중요한 구조에는  
plain sorted array, tree나 skip list가 더 현실적일 수 있다.

## 코드로 보기

```java
public class EytzingerSearch {
    private final int[] tree; // 1-indexed

    public EytzingerSearch(int[] sorted) {
        this.tree = new int[sorted.length + 1];
        build(sorted, 1, 0, sorted.length);
    }

    private int build(int[] sorted, int index, int start, int end) {
        if (index >= tree.length || start >= end) {
            return start;
        }
        int next = build(sorted, index * 2, start, end);
        tree[index] = sorted[next++];
        return build(sorted, index * 2 + 1, next, end);
    }

    public boolean contains(int target) {
        int index = 1;
        while (index < tree.length) {
            if (tree[index] == target) {
                return true;
            }
            index = target < tree[index] ? index * 2 : index * 2 + 1;
        }
        return false;
    }
}
```

이 코드는 Eytzinger 배치 감각만 보여준다.  
실전 구현은 prefetch hint와 branchless search 최적화가 더 중요할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Eytzinger Layout | 정적 검색에서 locality와 branch 동작이 좋아질 수 있다 | 업데이트에 약하고 정렬 순서 scan 시작점 복구가 덜 자연스럽다 | immutable search table, point lookup hot path |
| Plain Sorted Array + Binary Search | 단순하고 구현이 쉽다 | 메모리 접근 패턴이 덜 locality-friendly할 수 있다 | 일반적인 정적 search |
| Blocked Search Array / B-Tree형 Layout | fan-out을 키워 miss 수를 줄이고 range scan 연결도 좋다 | node packing과 tuning reasoning이 더 어렵다 | page/block-aware ordered index |
| Pointer Tree | update와 ordered semantics가 자연스럽다 | pointer chasing이 비싸다 | mutable ordered structure |
| Cache-Oblivious Layout | 더 일반적인 계층 독립 locality를 노린다 | reasoning과 구현이 더 어렵다 | recursive immutable layout |

중요한 질문은 "정렬 배열을 유지하느냐"보다  
"정적 검색에서 CPU가 어떤 순서로 메모리를 밟게 할 것이냐"다.

## 꼬리질문

> Q: Eytzinger layout이 heap 배열과 비슷하다는 말은 무슨 뜻인가요?
> 의도: implicit binary tree array 배치를 이해하는지 확인
> 핵심: 정렬 원소를 level-order 형태의 트리 배열로 재배치해 parent/child를 인덱스로 계산한다는 뜻이다.

> Q: 왜 업데이트가 잦으면 안 맞나요?
> 의도: 정적 레이아웃 최적화의 한계를 이해하는지 확인
> 핵심: 재배치 비용이 커서 layout 이득보다 유지비가 더 커질 수 있기 때문이다.

> Q: plain binary search보다 항상 빠른가요?
> 의도: cache-aware 최적화의 적용 경계를 이해하는지 확인
> 핵심: 아니다. 하드웨어와 데이터 크기, 구현 세부에 따라 달라지며 정적 read-mostly 환경에서 더 유력하다.

> Q: range scan도 중요하면 왜 Eytzinger가 최선이 아닐 수 있나요?
> 의도: point lookup 최적화와 ordered scan 요구를 분리하는지 확인
> 핵심: Eytzinger는 검색 경로 locality에 초점을 둔 배치라서, 정렬 순서 유지나 block 단위 fan-out이 중요한 경우 plain array나 blocked layout이 더 자연스럽다.

## 한 줄 정리

Eytzinger layout은 정렬된 데이터를 heap 같은 배열 트리로 재배치해, 정적 검색 경로의 locality와 branch 동작을 개선하려는 cache-aware 검색 레이아웃이다.
