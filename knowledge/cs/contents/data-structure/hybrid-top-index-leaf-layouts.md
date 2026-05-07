---
schema_version: 3
title: Hybrid Top-Index Leaf Layouts
concept_id: data-structure/hybrid-top-index-leaf-layouts
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- hybrid-search-layout
- guide-index-leaf-block
- lower-bound-scan-locality
aliases:
- hybrid top index leaf layout
- guide index plus contiguous leaves
- Eytzinger top index leaf blocks
- lower_bound then scan continuation
- leaf packed hybrid ordered search
- fence key array leaf blocks
- sampled separators over leaves
symptoms:
- lower_bound 경로 locality와 그 뒤 range scan continuation locality를 한 레이아웃 하나로만 해결하려 한다
- pure Eytzinger나 pure vEB layout이 point search에는 좋지만 긴 ordered scan에는 아쉬울 수 있다는 점을 놓친다
- separator guide index와 contiguous leaf block을 분리해 top search와 leaf scan을 각각 최적화하는 절충을 고려하지 않는다
intents:
- comparison
- design
prerequisites:
- data-structure/ordered-search-workload-matrix
- data-structure/eytzinger-layout-and-cache-friendly-search
next_docs:
- data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
- data-structure/cache-oblivious-vs-cache-aware-layouts
- data-structure/lsm-friendly-index-structures
linked_paths:
- contents/data-structure/ordered-search-workload-matrix.md
- contents/data-structure/eytzinger-layout-and-cache-friendly-search.md
- contents/data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md
- contents/data-structure/cache-oblivious-b-tree-vs-plain-veb-layout.md
- contents/data-structure/cache-oblivious-vs-cache-aware-layouts.md
- contents/data-structure/lsm-friendly-index-structures.md
confusable_with:
- data-structure/eytzinger-layout-and-cache-friendly-search
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
- data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays
- data-structure/lsm-friendly-index-structures
forbidden_neighbors: []
expected_queries:
- Hybrid top-index leaf layout은 lower_bound와 scan continuation을 어떻게 나눠 최적화해?
- guide index와 packed contiguous leaves를 같이 쓰는 ordered index 설계는?
- Eytzinger top index와 leaf block 구조를 언제 쓰면 좋아?
- pure search layout이 range scan workload에서 부족한 이유는?
- fence key separator로 leaf 후보를 찾고 그 뒤 sequential scan하는 구조를 설명해줘
contextual_chunk_prefix: |
  이 문서는 ordered search workload에서 top guide index는 lower_bound search
  path locality를, contiguous leaf blocks는 scan continuation locality를 맡는
  hybrid layout chooser다. Eytzinger top index, separator/fence key, packed
  leaves, range iterator locality를 다룬다.
---
# Hybrid Top-Index / Leaf Layouts

> 한 줄 요약: hybrid top-index / leaf layout은 상단에는 Eytzinger나 재귀 guide index를 두고, 하단에는 정렬 순서의 contiguous leaf block을 유지해서 `lower_bound`와 scan continuation locality를 분리해 챙기는 절충안이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Ordered Search Workload Matrix](./ordered-search-workload-matrix.md)
> - [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md)
> - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
> - [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)
> - [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)

> retrieval-anchor-keywords: hybrid top index leaf layout, guide index plus contiguous leaves, eytzinger top index leaf blocks, recursive guide index packed leaves, lower_bound then scan continuation, scan-friendly ordered index, fence key array with leaf blocks, implicit top index contiguous leaf blocks, leaf-packed hybrid ordered search, range iterator locality, sampled separators over leaf slabs, cache-aware guide index, cache-oblivious guide index, ordered merge leaf continuation

## 핵심 개념

이 hybrid의 핵심은 "정렬 검색 전체를 한 레이아웃으로 해결하려고 하지 않는다"는 데 있다.

- 상단 top index는 search path locality를 담당한다
- 하단 leaf block은 ordered scan locality를 담당한다
- 둘 사이는 separator, fence key, block max/min 같은 요약값으로 연결된다

즉 pure Eytzinger나 pure vEB처럼  
모든 원소를 implicit tree로 재배치하지 않고,  
**안내판 역할의 상위 index**와 **정렬 payload 역할의 연속 leaf**를 분리한다.

## 깊이 들어가기

### 1. 왜 pure search layout만으로는 부족한가

ordered workload는 자주 두 단계로 나뉜다.

1. `lower_bound`로 경계를 찾는다
2. 그 뒤 인접 key나 record를 계속 읽는다

Eytzinger와 plain vEB binary layout은 1번에 강하다.  
하지만 2번이 길어지면 정렬 이웃이 메모리 이웃으로 이어지지 않아  
scan continuation 감각이 급격히 나빠질 수 있다.

반대로 plain sorted array는 2번이 아주 단순하지만,  
상단 비교 경로를 더 공격적으로 다듬을 여지가 적다.

hybrid top-index / leaf layout은 이 둘을 나눈다.

- top index는 "어느 leaf로 갈지"만 빠르게 결정한다
- leaf block은 "찾은 뒤 어떻게 이어 읽을지"를 단순하게 만든다

### 2. 기본 형태는 `guide index + packed leaves`다

가장 흔한 모양은 다음과 같다.

- leaf `L0, L1, L2, ...`는 key order대로 contiguous하게 놓는다
- 각 leaf마다 대표 separator 하나를 뽑는다
- separator 배열을 top index로 재배치한다

대표 separator는 보통 이 중 하나다.

- leaf의 최대 key
- leaf의 최소 key
- leaf 시작 위치를 대표하는 sampled pivot

쿼리 `x`는:

1. top index에서 `x`가 속할 leaf 후보를 찾고
2. 해당 leaf 내부에서 다시 `lower_bound`를 수행한 뒤
3. 같은 leaf 안을 sequential하게 읽고
4. 필요하면 바로 다음 leaf로 넘어간다

즉 top index는 원소 전체가 아니라  
**leaf boundary directory**에 가깝다.

### 3. 상단 guide index는 보통 두 부류다

#### Eytzinger top index

- separator 배열 자체를 Eytzinger로 놓는다
- 상위 레벨 reuse와 prefetch-friendly search path가 강점이다
- guide index가 작고 rebuild 가능한 immutable segment와 잘 맞는다

이 경우 bottom leaf는 굳이 tree 모양일 필요가 없다.  
단순 sorted block이면 충분하다.

#### Recursive / vEB-style top index

- separator directory를 재귀적으로 배치한다
- 특정 block 크기를 박지 않고 multi-level locality를 노린다
- top guide가 크고 하드웨어별 tuning을 덜 박고 싶을 때 유리하다

핵심은 여기서도 재귀 layout을 leaf payload 전체에 강제하지 않고  
**상위 안내 구조에만 국한한다**는 점이다.

### 4. scan continuation locality는 leaf의 물리 배치가 만든다

이 hybrid가 성립하려면 leaf block이 실제로 scan-friendly해야 한다.

- leaf 내부 원소가 sorted contiguous array여야 한다
- 다음 leaf가 key order대로 이어져야 한다
- leaf metadata가 scan path를 깨지 않아야 한다

구현 형태는 여러 가지가 가능하다.

- 모든 leaf를 하나의 큰 배열 안에 back-to-back으로 저장
- fixed-size leaf slab을 동일 stride로 저장
- variable-size leaf를 두되 offset table로 다음 leaf를 찾음

중요한 점은 `next leaf`가 pointer chasing이 아니라  
단순 offset 증가나 인접 block 접근으로 설명되어야 한다는 것이다.

### 5. leaf 크기와 separator 선택이 성능 모양을 바꾼다

hybrid layout의 주된 tuning knob는 이 둘이다.

| knob | 너무 작을 때 | 너무 클 때 | 실전 감각 |
|---|---|---|---|
| leaf block size | top index hit 수와 leaf 전환 수가 늘어난다 | leaf 내부 search와 wasteful scan이 늘어난다 | `lower_bound` 뒤 평균 scan 길이와 cache/page 단위에 맞춰 잡는다 |
| separator sampling | top index depth가 깊어진다 | leaf 후보가 거칠어져 내부 search 부담이 커진다 | leaf max/min, fence key, block head 중 하나로 단순하게 유지한다 |

즉 이 구조는 "search를 빠르게"가 아니라  
**top search 비용과 leaf scan 비용을 어디서 나눌지**를 설계하는 문제다.

### 6. 어떤 workload에서 특히 잘 맞나

이 hybrid는 이런 질문에 "예"일 때 설득력이 커진다.

- `lower_bound` 뒤 8개 이상 이웃 접근이 자주 붙는가
- point lookup도 적지 않아서 top search path를 무시하기 어려운가
- 구조가 immutable 또는 batched rebuild 가능한가
- full B-tree 구현까지는 과하고, plain array만으로는 아쉬운가

대표 예시는 이렇다.

- SSTable / segment의 fence-key guide + contiguous data block
- posting list directory + packed leaf chunk
- 정적 in-memory range index에서 top sampled index + sorted leaf slabs
- dictionary boundary table에서 top guide와 bottom payload를 분리한 경우

### 7. 무엇과 어떻게 다른가

| 구조 | 잘하는 일 | 약한 지점 | hybrid와의 차이 |
|---|---|---|---|
| Pure Eytzinger | point lookup, `lower_bound` hot path | 긴 ordered scan | hybrid는 Eytzinger를 top guide에만 쓰고 leaf는 정렬 순서를 유지한다 |
| Plain vEB binary layout | recursive root-to-leaf locality | in-order scan continuation | hybrid는 재귀성을 top index에만 남기고 leaf를 contiguous하게 둔다 |
| Plain sorted array | 긴 sequential scan, 단순성 | search path locality 튜닝 폭이 작다 | hybrid는 leaf scan 장점을 유지하면서 guide index를 추가한다 |
| Blocked/B-Tree형 배열 | block-aware search와 scan 연계 | node packing reasoning, full-tree 복잡도 | hybrid는 상단만 implicit/recursive로 단순화해 실전 구현 부담을 줄인다 |

즉 hybrid는 pure 구조들의 "중간 평균"이 아니라,  
**search path와 scan path를 다른 층에 맡기는 역할 분리형 설계**다.

### 8. 자주 나오는 오해

**오해 1: leaf가 contiguous면 결국 plain sorted array 아닌가**

아니다. leaf 전체가 하나의 flat array일 수도 있지만,  
보통은 상단 guide index가 block boundary 탐색을 대신해서  
plain binary search보다 더 예측 가능한 top path를 만든다.

**오해 2: top index가 implicit tree면 leaf도 같은 순서로 재배치해야 한다**

아니다. 이 문서의 핵심은 오히려 그 반대다.  
상단만 implicit/recursive로 두고, leaf는 정렬 순서 그대로 두는 것이 목적이다.

**오해 3: 이건 결국 full B-tree와 같다**

부분적으로 닮았지만 실전 감각은 다르다.

- top index는 종종 immutable array-based guide다
- leaf도 page/node object가 아니라 단순 packed block일 수 있다
- balancing이나 mutation invariants보다 rebuild simplicity가 더 중요하다

## 실전 시나리오

### 시나리오 1: top Eytzinger over fence keys

leaf마다 최대 key를 뽑아 작은 guide array를 만들고,  
그 guide array만 Eytzinger로 배치한다.  
`lower_bound`는 top guide에서 leaf를 찾고, 실제 payload scan은 leaf block에서 이어진다.

이 형태는 "guide는 hot, payload는 scan-heavy"인 read-mostly segment에 잘 맞는다.

### 시나리오 2: recursive guide over immutable leaf slabs

separator directory가 꽤 커서 여러 cache 계층의 locality를 신경 써야 하면  
top guide만 recursive/vEB-style로 두고 leaf slab은 그대로 contiguous하게 둔다.

이 경우 pure vEB보다 scan continuation 설명이 훨씬 단순하다.

### 시나리오 3: 부적합한 경우

leaf split/merge가 자주 일어나는 update-heavy ordered map이면  
rebuild나 block maintenance 비용이 커져 hybrid 장점이 줄어든다.  
이때는 일반 B-tree나 mutable skip list 쪽이 더 자연스럽다.

## 꼬리질문

> Q: 왜 top index와 leaf payload를 분리하나요?
> 의도: search path locality와 ordered scan locality를 별도 문제로 보는지 확인
> 핵심: 상단은 경계 찾기에, 하단은 경계 뒤 연속 읽기에 최적화 목표가 다르기 때문이다.

> Q: Eytzinger top index를 쓰면 leaf도 Eytzinger여야 하나요?
> 의도: hybrid의 핵심이 "부분 적용"임을 이해하는지 확인
> 핵심: 아니다. 오히려 top guide만 Eytzinger로 두고 leaf는 contiguous sorted block으로 두는 것이 보통이다.

> Q: 이 hybrid가 full B-tree보다 쉬운 이유는 무엇인가요?
> 의도: practical hybrid의 의의를 설명하는지 확인
> 핵심: 상단 guide가 immutable array 형태일 수 있어 pointer-rich node invariants와 balancing 부담이 줄기 때문이다.

## 한 줄 정리

hybrid top-index / leaf layout은 상단의 implicit or recursive guide index로 경계 탐색을 빠르게 하고, 하단의 contiguous leaf block으로 scan continuation을 단순하게 만들어 `lower_bound`와 range walk를 동시에 다루는 실전형 ordered index 절충안이다.
