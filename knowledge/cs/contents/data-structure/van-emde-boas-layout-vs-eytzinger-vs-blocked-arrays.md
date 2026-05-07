---
schema_version: 3
title: van Emde Boas Layout vs Eytzinger vs Blocked Arrays
concept_id: data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- ordered-search-layout
- cache-oblivious-vs-cache-aware
- lower-bound-scan-locality
aliases:
- van Emde Boas layout vs Eytzinger
- vEB layout
- Eytzinger vs blocked array
- cache-oblivious ordered search
- lower_bound layout comparison
- scan-heavy ordered search
- blocked search array
symptoms:
- lower_bound만 뜨거운지 lower_bound 뒤 scan이 이어지는지 구분하지 않고 Eytzinger, vEB, blocked layout을 고른다
- vEB layout이 cache-oblivious라서 Eytzinger나 blocked array보다 항상 낫다고 오해한다
- ordered scan locality가 search path locality와 다른 문제라는 점을 놓쳐 Eytzinger search 이득을 scan-heavy workload에도 그대로 기대한다
intents:
- comparison
- design
prerequisites:
- data-structure/cache-aware-data-structure-layouts
- data-structure/cache-oblivious-vs-cache-aware-layouts
next_docs:
- data-structure/ordered-search-workload-matrix
- data-structure/eytzinger-layout-and-cache-friendly-search
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
linked_paths:
- contents/data-structure/cache-aware-data-structure-layouts.md
- contents/data-structure/cache-oblivious-vs-cache-aware-layouts.md
- contents/data-structure/ordered-search-workload-matrix.md
- contents/data-structure/eytzinger-layout-and-cache-friendly-search.md
- contents/data-structure/cache-oblivious-b-tree-vs-plain-veb-layout.md
- contents/data-structure/hybrid-top-index-leaf-layouts.md
- contents/data-structure/lsm-friendly-index-structures.md
confusable_with:
- data-structure/cache-oblivious-vs-cache-aware-layouts
- data-structure/eytzinger-layout-and-cache-friendly-search
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
- data-structure/hybrid-top-index-leaf-layouts
- data-structure/ordered-search-workload-matrix
forbidden_neighbors: []
expected_queries:
- vEB layout Eytzinger blocked array는 lower_bound와 scan locality 관점에서 어떻게 골라?
- Eytzinger는 search path에는 좋지만 ordered scan에는 덜 자연스러운 이유는?
- cache-oblivious vEB layout이 항상 blocked array보다 좋은 선택은 아닌 이유는?
- lower_bound 뒤에 range scan이 이어지면 blocked array나 B-Tree형 layout이 유리한 이유는?
- immutable ordered index에서 search path locality와 scan continuation locality를 분리해 설명해줘
contextual_chunk_prefix: |
  이 문서는 immutable ordered search layout에서 van Emde Boas layout, Eytzinger,
  blocked arrays를 비교하는 chooser다. lower_bound hot path, scan continuation locality,
  cache-oblivious vs cache-aware block reasoning, hybrid leaf layout을 다룬다.
---
# van Emde Boas Layout vs Eytzinger vs Blocked Arrays

> 한 줄 요약: vEB-style cache-oblivious layout은 여러 메모리 계층에서 root-to-leaf locality를 고르게 노리고, Eytzinger는 단순한 search path와 prefetch friendliness를, blocked array는 `lower_bound` 뒤 scan 연결을 가장 직접적으로 챙긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md)
> - [Ordered Search Workload Matrix](./ordered-search-workload-matrix.md)
> - [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md)
> - [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)
> - [Hybrid Top-Index / Leaf Layouts](./hybrid-top-index-leaf-layouts.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)

> retrieval-anchor-keywords: van emde boas layout, vEB layout, cache-oblivious ordered search, cache-oblivious binary search tree layout, eytzinger vs blocked array, lower_bound layout comparison, scan-heavy ordered search, cache-aware vs cache-oblivious search layout, blocked search array, b-tree style array layout, immutable ordered index, recursive layout locality, lower_bound after scan, cache-oblivious b-tree, leaf-packed ordered index, hybrid top index leaf layout, guide index plus contiguous leaves, range-scan-friendly ordered index, ordered search workload matrix

## 핵심 개념

정적 ordered search layout을 고를 때 자주 놓치는 질문은  
`lower_bound`를 찾은 **바로 다음에 무엇을 하느냐**다.

- 찾고 바로 끝나면 search path locality가 중요하다
- 찾은 뒤 인접 원소를 계속 읽으면 leaf/scan locality가 중요하다
- 하드웨어 block 크기를 명시적으로 맞출 수 있는지도 선택을 바꾼다

즉 vEB, Eytzinger, blocked array는 모두 `O(log n)` search를 하더라도  
**어떤 locality를 먼저 산다**가 다르다.

## 깊이 들어가기

### 1. 세 레이아웃은 "가까움"을 다르게 정의한다

**Eytzinger**는 level-order 배치다.

- root와 상위 레벨이 앞쪽에 모인다
- `i -> 2i`, `2i + 1` 이동이 단순하다
- search path prefetch와 branchless update에 잘 맞는다

**Blocked array / B-Tree형 배열**은 block 안에 여러 pivot이나 leaf chunk를 묶는다.

- 한 번 block을 읽으면 비교를 여러 개 몰아서 처리한다
- leaf block에서 바로 다음 원소를 이어 읽기 쉽다
- fan-out과 block 크기를 하드웨어나 page 단위에 맞춰 조정할 수 있다

**vEB-style layout**은 subtree를 재귀적으로 반씩 쪼개며 배치한다.

- 특정 cache line이나 page 크기를 박지 않는다
- 작은 계층에서도, 큰 계층에서도 subtree locality를 노린다
- 대신 자식 위치 계산, 구현, prefetch reasoning은 Eytzinger보다 덜 직선적이다

### 2. `lower_bound` hot path만 보면 누가 유리한가

`lower_bound`만 단독 hot path라면 세 구조 모두 후보가 될 수 있지만  
이득의 모양은 다르다.

| layout | `lower_bound`에서 강한 점 | 아쉬운 점 |
|---|---|---|
| Eytzinger | 상위 레벨 재사용, 단순 인덱스 계산, prefetch hint, branchless 구현 감각이 좋다 | 정렬 순서상 이웃 원소가 메모리에서 바로 옆이 아니다 |
| Blocked array | fan-out으로 깊이를 줄이고, 한 block 안에서 여러 비교를 처리한다 | block 크기와 packing을 잘못 잡으면 이점이 흐려진다 |
| vEB layout | 특정 `B`를 몰라도 여러 계층에서 root-to-leaf locality를 노린다 | 미세 최적화와 디버깅, index mapping reasoning이 더 어렵다 |

실무 감각으로 줄이면:

- 구현 단순성과 prefetch-friendly `lower_bound`: Eytzinger
- 명시적 block/page reasoning이 가능한 `lower_bound`: blocked array
- 플랫폼별 block 크기를 박고 싶지 않은 immutable search: vEB

### 3. scan-heavy path가 붙으면 질문이 바뀐다

`lower_bound` 뒤에 바로 몇 개, 몇십 개, 몇백 개 원소를 읽는 순간  
우세 후보가 자주 바뀐다.

**Blocked array는 여기서 가장 직선적이다.**

- boundary를 찾은 leaf block이 이미 정렬 순서 chunk다
- 같은 block 안에서 sequential scan이 바로 이어진다
- block을 넘겨도 다음 leaf block으로 자연스럽게 이동할 수 있다

반면 **Eytzinger**는 search path는 좋지만  
정렬 순서상 이웃이 메모리 이웃이 아니라서 scan 시작점 복구가 별도 문제다.

**vEB-style binary layout**도 순수 search에는 locality를 주지만  
긴 in-order scan에서는 재귀 cut을 계속 넘게 된다.  
즉 subtree 내부의 짧은 locality는 얻어도,  
길게 이어지는 ordered scan을 leaf block처럼 다루지는 못한다.

핵심은 이 문장이다.

- `lower_bound`에서 끝나면 Eytzinger/vEB가 강한 후보
- `lower_bound` 다음 scan이 중요하면 blocked array가 더 자주 이긴다

### 4. vEB가 scan-heavy에서 밀리는 이유를 더 정확히 보자

vEB는 "모든 스케일에서 subtree가 뭉치게" 만드는 재귀 배치다.  
그래서 root-to-leaf path에는 좋은 locality를 준다.

하지만 ordered scan은 subtree path가 아니라  
**정렬 순서 이웃을 연속으로 밟는 작업**이다.

이때 단순 binary-tree vEB layout은:

- 탐색 경로 locality에는 강함
- in-order 이웃의 긴 선형성에는 덜 직접적임
- scan이 핵심이면 별도 leaf packing이나 cache-oblivious B-Tree 계열로 내려가야 함

즉 `vEB binary layout`과 `scan-friendly cache-oblivious ordered index`는  
같은 말이 아니다.

이 차이를 leaf block 관점까지 좁혀서 보면  
[Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)이 바로 다음 읽기다.

### 5. 그래서 실전 선택축은 이렇게 정리된다

| workload 질문 | 더 유력한 선택 |
|---|---|
| point lookup / `lower_bound`만 뜨겁고 read-mostly인가 | Eytzinger |
| 여러 cache 계층에서 block 크기 의존을 줄이고 싶은 immutable search인가 | vEB-style layout |
| `lower_bound` 뒤에 neighbor read, range scan, merge가 자주 이어지는가 | blocked array / B-Tree형 배열 |
| search와 scan을 둘 다 원하지만 구현 복잡도를 너무 올리기 싫은가 | blocked leaf + 단순 상위 index 같은 hybrid |

즉 search-layout lane에서는 "cache-aware냐 cache-oblivious냐"보다  
`search path locality`와 `scan continuation locality`를 분리해서 보는 편이 훨씬 실전적이다.
빠른 workload 판정표는 [Ordered Search Workload Matrix](./ordered-search-workload-matrix.md)에서 바로 볼 수 있다.
마지막 줄의 hybrid를 구체적인 top-guide/contiguous-leaf 패턴으로 풀어 쓴 문서는
[Hybrid Top-Index / Leaf Layouts](./hybrid-top-index-leaf-layouts.md)다.

### 6. 자주 나오는 오해

**오해 1: vEB가 더 일반적이니 Eytzinger보다 항상 낫다**

아니다. vEB는 block size를 하드코딩하지 않는 대신  
구현 단순성과 prefetch friendliness를 일부 포기한다.  
핫한 `lower_bound` 경로를 아주 단순한 배열 연산으로 밀어붙이고 싶으면  
Eytzinger가 더 현실적일 수 있다.

**오해 2: Eytzinger가 binary search보다 좋았으니 scan에도 좋다**

아니다. Eytzinger의 핵심 이득은 search path다.  
ordered scan은 다른 문제다.

**오해 3: blocked array는 cache-oblivious보다 구식이다**

아니다. `lower_bound -> leaf scan -> 다음 leaf` 흐름이 핵심인 workload에서는  
오히려 blocked array가 가장 솔직한 모델일 수 있다.

## 실전 시나리오

### 시나리오 1: immutable routing / boundary table

찾고 바로 끝나는 질의가 대부분이면  
Eytzinger나 vEB-style layout을 검토할 가치가 있다.

### 시나리오 2: fence pointer 후 data block scan

SSTable fence pointer, posting-list boundary, range chunk 탐색처럼  
`lower_bound` 뒤에 실제 payload scan이 이어지면 blocked array가 더 자연스럽다.

### 시나리오 3: 여러 머신에서 같은 정적 index 배포

하드웨어 세부 튜닝을 덜 박고 싶고 search-only 성격이 강하면  
vEB-style cache-oblivious 배치가 설계상 더 매력적일 수 있다.

### 시나리오 4: 둘 다 필요한데 pure vEB binary layout이 애매함

이때는 상위 index만 재귀/implicit layout으로 두고,  
bottom leaf는 contiguous block으로 두는 hybrid가 더 실전적이다.

## 비교 표

| 축 | Eytzinger | Blocked Array / B-Tree형 배열 | vEB-Style Layout |
|---|---|---|---|
| 주된 최적화 대상 | search path 상위 레벨 재사용 | block/leaf 단위 비교와 scan 연계 | 여러 계층에서의 재귀 subtree locality |
| `lower_bound` 구현 감각 | 단순하고 미세 최적화가 쉽다 | block packing에 따라 달라진다 | 이론은 좋지만 구현이 더 어렵다 |
| `lower_bound` 뒤 scan | 덜 자연스럽다 | 가장 자연스럽다 | 짧은 subtree-local scan은 가능하지만 긴 ordered scan은 약하다 |
| block size 의존성 | 낮음 | 높음 | 낮음 |
| prefetch / branchless tuning | 좋음 | block 구조 의존 | Eytzinger보다 어렵다 |
| 가장 잘 맞는 곳 | immutable point lookup table | range scan 연결이 중요한 ordered index | immutable search-only index, multi-level locality |

## 꼬리질문

> Q: 왜 `lower_bound`와 range scan을 따로 봐야 하나요?
> 의도: search path와 ordered continuation을 같은 문제로 보지 않는지 확인
> 핵심: `lower_bound`는 경계 하나를 찾는 작업이고, range scan은 그 경계 이후 이웃 원소를 연속으로 읽는 작업이라 locality 요구가 다르다.

> Q: vEB가 cache-oblivious면 blocked array보다 항상 범용적인가요?
> 의도: 이론적 일반성과 practical fit를 구분하는지 확인
> 핵심: 아니다. scan-heavy path나 explicit page/block reasoning이 중요하면 blocked array가 더 직접적으로 맞는다.

> Q: Eytzinger와 vEB 중 무엇이 더 좋은 `lower_bound` 구조인가요?
> 의도: 단일 승자를 찾기보다 workload 조건을 먼저 보게 하는지 확인
> 핵심: 단순 구현과 prefetch-friendly hot path면 Eytzinger, block-size 독립 multi-level locality를 더 중시하면 vEB가 더 어울릴 수 있다.

## 한 줄 정리

정적 ordered search에서 vEB, Eytzinger, blocked array의 차이는 모두 `O(log n)`이라는 사실보다, `lower_bound` 뒤에 끝나는지 스캔이 이어지는지, 그리고 block 크기를 직접 다룰지 말지가 더 크게 가른다.
