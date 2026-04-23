# Cache-Oblivious vs Cache-Aware Layouts

> 한 줄 요약: cache-aware는 cache line과 block 크기를 의식해 레이아웃을 잡고, cache-oblivious는 특정 계층 크기를 박지 않고도 여러 메모리 계층에서 locality를 얻으려는 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md)
> - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
> - [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)
> - [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)

> retrieval-anchor-keywords: cache oblivious vs cache aware, cache-aware layout, cache-oblivious layout, memory hierarchy, van emde boas layout, locality design, block size agnostic structure, hardware conscious data structure, cache line layout, data structure layout tradeoff, cache-oblivious ordered search, veb vs eytzinger vs blocked array, lower_bound scan-heavy path, cache-oblivious b-tree, leaf-packed ordered index, range-scan-friendly ordered index

## 핵심 개념

layout 최적화는 두 철학으로 나뉜다.

- cache-aware: "cache line / page / block 크기를 알고 그에 맞게 배치"
- cache-oblivious: "특정 크기를 하드코딩하지 않아도 여러 계층에서 locality를 얻도록 배치"

즉 둘의 차이는 "locality를 보나 안 보나"가 아니라  
**hardware parameter를 코드/구조에 직접 넣느냐**에 가깝다.

## 깊이 들어가기

### 1. cache-aware는 튜닝이 직접적이다

cache-aware 설계는 보통 이런 질문을 한다.

- node 하나를 cache line 안에 넣을 수 있는가
- block index 크기를 page size에 맞출 수 있는가
- false sharing을 피하도록 field를 나눌 수 있는가

장점:

- 특정 플랫폼에서 강한 성능을 내기 쉽다
- reasoning이 직접적이다

단점:

- 하드웨어 가정이 코드에 스며든다
- 다른 환경에선 tuning이 깨질 수 있다

### 2. cache-oblivious는 계층 독립적 locality를 노린다

cache-oblivious 구조는 특정 block 크기 `B`를 몰라도  
재귀 배치나 분할 방식으로 locality를 얻으려 한다.

대표 감각:

- van Emde Boas layout
- recursive partitioning
- divide-and-conquer scan locality

즉 "cache line이 64B인지 128B인지 모르더라도"  
상대적으로 좋은 locality를 얻도록 설계하는 쪽이다.

### 3. 왜 실무에서는 cache-aware가 더 많이 보이나

backend 실무는 하드웨어와 workload가 꽤 구체적이다.

- x86 cache line
- page size
- SSD block
- JVM object layout

그래서 cache-aware tuning이 더 직접적으로 먹히는 경우가 많다.  
반면 cache-oblivious는 우아하지만 구현과 디버깅이 더 어렵고,  
효과가 구조 전체에 숨어 있는 경우가 많다.

### 4. 둘은 경쟁보다 계층이다

실제로는 둘을 섞기도 한다.

- 상위 구조는 cache-oblivious 재귀 배치
- 하위 node/block은 cache-aware packing

즉 둘 중 하나만 "정답"인 경우보다,  
문제 크기와 제어 가능한 계층에 따라 섞이는 경우가 많다.

### 5. backend에서 어디에 맞나

cache-aware:

- queue field padding
- hash table slot packing
- block index page fitting

cache-oblivious:

- 재귀 배열 배치
- immutable search structure
- multi-level hierarchy scan

즉 runtime-tuned hot path는 cache-aware,  
more general immutable search layout은 cache-oblivious 쪽이 자주 거론된다.

ordered search만 좁혀 보면 여기서 다시 선택축이 갈린다.  
vEB-style layout은 계층 독립 root-to-leaf locality를,  
Eytzinger는 단순한 `lower_bound` hot path를,  
blocked array는 `lower_bound` 뒤 scan continuation을 더 직접적으로 챙긴다.  
이 비교는 [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)에서 따로 정리했다.

여기서 range scan 친화적 ordered index까지 확장하면  
leaf block을 연속화한 cache-oblivious B-tree / leaf-packed hybrid가 별도 축으로 나타난다.  
이 follow-up은 [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](./cache-oblivious-b-tree-vs-plain-veb-layout.md)에 정리했다.

## 실전 시나리오

### 시나리오 1: low-latency queue

head/tail false sharing을 피해야 하는 queue는  
거의 항상 cache-aware 쪽이 더 직접적이다.

### 시나리오 2: immutable search array/tree

재귀 배치가 여러 메모리 계층에서 두루 좋은 locality를 줄 수 있다면  
cache-oblivious layout을 검토할 수 있다.

### 시나리오 3: LSM block index

page/block 크기가 명확한 저장 경로에서는  
cache-aware가 실무적으로 더 직접적이다.

### 시나리오 4: 부적합한 경우

hot path도 아니고 데이터 크기도 작다면  
둘 다 과한 최적화일 수 있다.

## 비교 표

| 축 | Cache-Aware | Cache-Oblivious |
|---|---|---|
| 전제 | block/cache 크기를 안다 | block/cache 크기를 모른다 |
| 최적화 방식 | explicit packing/tuning | recursive locality |
| 장점 | 직접적이고 실무 튜닝이 쉽다 | 계층 독립적 locality를 노린다 |
| 단점 | 환경 종속적이다 | 구현과 reasoning이 더 어렵다 |

## 꼬리질문

> Q: cache-oblivious가 cache-aware보다 항상 더 일반적이니 좋은가요?
> 의도: 이론적 우아함과 실무 tuning을 구분하는지 확인
> 핵심: 아니다. 실무에선 제어 가능한 하드웨어 파라미터가 많아 cache-aware가 더 직접적으로 먹히는 경우가 많다.

> Q: queue padding은 어느 쪽에 가까운가요?
> 의도: 개념을 concrete example과 연결하는지 확인
> 핵심: cache line 크기를 의식한 cache-aware 최적화다.

> Q: 왜 immutable search structure에서 cache-oblivious가 자주 언급되나요?
> 의도: update-heavy와 layout optimization의 궁합을 이해하는지 확인
> 핵심: 재귀 배치를 미리 만들어 여러 계층에서 locality를 얻기 쉬워서다.

## 한 줄 정리

cache-aware와 cache-oblivious는 모두 locality를 노리지만, 하나는 하드웨어 파라미터를 직접 쓰고 다른 하나는 모르더라도 좋은 재귀 배치를 만들려는 설계 철학이다.
