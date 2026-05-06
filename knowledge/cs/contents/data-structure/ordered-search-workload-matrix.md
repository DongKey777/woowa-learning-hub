---
schema_version: 3
title: Ordered Search Workload Matrix
concept_id: data-structure/ordered-search-workload-matrix
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- search-layout-vs-scan-shape
- lower-bound-after-scan
- eytzinger-vs-veb-vs-blocked-array
aliases:
- ordered search workload matrix
- point lookup layout choice
- lower bound scan layout
- eytzinger vs blocked array
- plain veb vs sorted array
- ordered index layout selection
- range iterator locality choice
- immutable search layout matrix
symptoms:
- 정적 ordered index를 고를 때 O(log n)만 보다가 scan 길이에 따른 차이를 놓친다
- lower_bound 뒤에 몇 개를 더 읽는지가 중요한데 layout 선택 기준이 머리에 안 잡힌다
- Eytzinger가 빠르다는 말만 듣고 iterator workload에도 그대로 들이밀게 된다
intents:
- comparison
- design
- deep_dive
prerequisites:
- data-structure/cache-aware-data-structure-layouts
- data-structure/cache-oblivious-vs-cache-aware-layouts
next_docs:
- data-structure/eytzinger-layout-and-cache-friendly-search
- data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
linked_paths:
- contents/data-structure/cache-aware-data-structure-layouts.md
- contents/data-structure/eytzinger-layout-and-cache-friendly-search.md
- contents/data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md
- contents/data-structure/cache-oblivious-b-tree-vs-plain-veb-layout.md
- contents/data-structure/cache-oblivious-vs-cache-aware-layouts.md
- contents/data-structure/hybrid-top-index-leaf-layouts.md
confusable_with:
- data-structure/cache-aware-data-structure-layouts
- data-structure/van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays
- data-structure/cache-oblivious-b-tree-vs-plain-veb-layout
forbidden_neighbors:
- contents/data-structure/eytzinger-layout-and-cache-friendly-search.md
expected_queries:
- 정적 ordered search에서 point lookup 위주인지 range scan 위주인지에 따라 array layout을 어떻게 나눠야 해
- lower_bound만 하고 끝나는 경우와 찾은 뒤 몇 개 더 읽는 경우를 구조 선택으로 비교해줘
- Eytzinger가 빠를 때와 blocked array가 더 맞을 때를 workload 기준으로 설명해줘
- immutable ordered index에서 plain sorted array와 plain vEB를 어떤 질문으로 갈라야 해
- range iterator가 길게 붙는 경로에서 왜 search 벤치만 보면 안 되는지 알고 싶어
- ordered map 비슷한 정적 검색 구조를 scan 길이 기준으로 고르는 표가 필요해
contextual_chunk_prefix: |
  이 문서는 정적 ordered search workload에서 point lookup, lower_bound only,
  short scan, long scan을 먼저 구분해 plain sorted array, Eytzinger,
  blocked array, plain vEB 중 무엇이 기본값인지 고르게 돕는 chooser다.
  경계 뒤 몇 개를 더 읽는지, iterator locality, search는 빠른데 scan은
  느린 layout, immutable ordered index 배치 선택 같은 자연어 paraphrase가
  본 문서의 선택 기준에 매핑된다.
---
# Ordered Search Workload Matrix

> 한 줄 요약: 정적 ordered search에서는 `O(log n)`보다 `찾고 끝나는지`, `lower_bound` 뒤에 몇 개를 더 읽는지가 plain sorted array, Eytzinger, blocked array, plain vEB의 우선순위를 더 크게 바꾼다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md)
> - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
> - [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)
> - [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md)

> retrieval-anchor-keywords: ordered search workload matrix, point lookup layout, lower_bound only layout, short scan layout, long scan layout, plain sorted array vs eytzinger, blocked array vs veb, ordered search layout selection, scan-heavy ordered search, lower_bound after scan, point lookup hot path, immutable ordered index layout, range iterator locality, plain array vs blocked array, eytzinger vs plain veb, layout selection matrix

## 핵심 개념

정적 ordered index를 고를 때는 먼저 이 질문을 해야 한다.

- 찾고 바로 끝나는가
- `lower_bound`만 구하고 끝나는가
- 경계 뒤 4~32개 정도만 더 읽는가
- 경계 뒤 수십~수백 개를 길게 읽는가

같은 `O(log n)` search라도  
이 질문에 따라 "좋은 layout"이 거의 바뀐다.

여기서 `short scan`은 대략 몇 개에서 몇십 개 초반까지의 이웃 접근,  
`long scan`은 range iterator, merge, posting walk처럼  
경계 뒤 ordered walk가 본체가 되는 경우를 뜻한다.

## 빠른 선택표

기호:

- `◎` 기본 1순위
- `○` 강한 대안
- `△` 조건부 후보
- `×` 보통은 잘못 고르는 기본값

| workload | Plain Sorted Array | Eytzinger | Blocked Array | Plain vEB Binary Layout |
|---|---|---|---|---|
| point lookup / exact membership | `○` | `◎` | `△` | `○` |
| `lower_bound`만 하고 끝남 | `○` | `◎` | `○` | `◎` |
| `lower_bound` 뒤 short scan | `○` | `△` | `◎` | `△` |
| `lower_bound` 뒤 long scan / iterator | `◎` | `×` | `○` | `×` |

## workload별 해석

### 1. point lookup

기본 출발점은 **Eytzinger**다.

- 상위 레벨이 앞쪽에 모여서 공통 search path 재사용이 쉽다
- branchless / prefetch tuning 감각이 좋다
- lookup 뒤 ordered continuation을 크게 신경 쓰지 않아도 된다

**Plain vEB**는 대안이다.

- 여러 cache 계층에서 block 크기를 박지 않고 search locality를 노릴 때 유리하다
- 대신 구현과 reasoning이 Eytzinger보다 덜 직선적이다

**Plain sorted array**는 충분히 작거나 단순성이 더 중요할 때 남는다.

### 2. `lower_bound`만 하고 끝나는 workload

이 경우는 **Eytzinger vs plain vEB**의 비교가 핵심이다.

- 단순 hot path, prefetch, 구현 용이성: Eytzinger
- block-size-agnostic multi-level locality: plain vEB

**Blocked array**도 가능하지만  
scan이 거의 안 붙는다면 leaf/block 설계 이점을 전부 쓰지 못할 수 있다.

### 3. `lower_bound` 뒤 short scan

여기서는 **blocked array**가 가장 자주 맞는다.

- 경계를 찾은 block이 곧 첫 scan chunk가 된다
- 한 block 안에서 여러 key를 amortize하기 쉽다
- 다음 block 이동도 ordered leaf walk로 설명된다

**Plain sorted array**도 여전히 괜찮다.  
다만 search path miss를 더 줄이고 싶고, scan이 짧게만 붙는다면  
blocked array가 middle ground가 되기 쉽다.

### 4. `lower_bound` 뒤 long scan

기본값은 **plain sorted array**다.

- 경계만 찾고 나면 나머지는 가장 단순한 sequential memory walk다
- ordered iterator, merge, posting scan에서 설명이 직선적이다
- 유지보수와 디버깅도 가장 쉽다

**Blocked array**는 long scan이 leaf/page 단위로 자연스럽게 끊기는 시스템에서 경쟁력이 있다.  
반면 **Eytzinger**와 **plain vEB binary layout**은 search benchmark가 좋아 보여도  
긴 ordered scan에는 자주 맞지 않는다.

## 헷갈릴 때 마지막 질문

| 질문 | 선택이 기우는 방향 |
|---|---|
| 검색 결과를 얻고 바로 끝나는가 | Eytzinger 또는 plain vEB |
| 다음 8개 정도만 더 읽는가 | blocked array |
| 다음 800개를 iterator처럼 읽는가 | plain sorted array |
| page/block 크기를 직접 맞추고 싶은가 | blocked array |
| block 크기를 하드코딩하고 싶지 않은가 | plain vEB |
| 구현 단순성이 가장 중요한가 | plain sorted array 또는 Eytzinger |

## 자주 하는 실수

- point lookup 벤치가 빨랐다고 Eytzinger를 scan-heavy path에 그대로 들고 간다
- cache-oblivious라는 이유만으로 plain vEB가 range iterator에도 좋다고 착각한다
- scan이 대부분인데도 `binary search가 예쁘다`는 이유로 plain sorted array를 먼저 지운다

## 한 줄 정리

정적 ordered search layout은 `누가 search를 더 빨리 하나`보다  
`경계 뒤 ordered walk가 얼마나 길게 이어지는가`를 먼저 보면 훨씬 빨리 고를 수 있다.
