# Cache-Aware Data Structure Layouts

> 한 줄 요약: cache-aware layout은 자료구조의 빅오보다 메모리 접근 패턴을 먼저 설계해, pointer chasing과 cache miss로 무너지는 실제 성능을 줄이려는 구조적 접근이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Heap Variants](./heap-variants.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)
> - [Robin Hood Hashing](./robin-hood-hashing.md)
> - [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md)
> - [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md)
> - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
> - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)
> - [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)

> retrieval-anchor-keywords: cache-aware layout, cache-friendly data structure, pointer chasing, locality, false sharing, array layout, eytzinger layout, branch prediction, cache line, memory hierarchy aware structure, static search layout, blocked search layout, binary search layout, hot cold splitting, memory access pattern, prefetch friendly layout, eytzinger vs blocked layout, search locality tradeoff, van emde boas layout, cache-oblivious ordered search, lower_bound scan-heavy path

## 핵심 개념

실전 성능은 종종 `O(log n)`보다 cache miss 횟수가 더 많이 좌우한다.  
특히 backend hot path에서는 "몇 번 비교했는가"보다 "몇 개의 cache line을 건드렸는가"가 더 중요하다.

cache-aware layout은 이 질문을 먼저 한다.

- 데이터를 배열로 붙일 수 있는가
- 자주 같이 읽는 필드를 같은 line에 둘 수 있는가
- 서로 다른 코어가 같은 line을 두드리지 않게 할 수 있는가

즉 알고리즘이 아니라 **메모리 계층과 함께 설계하는 자료구조 감각**이다.

## 깊이 들어가기

### 1. pointer chasing은 빅오에 안 보이는 비용이다

linked structure는 이론상 깔끔해도 실제론 비쌀 수 있다.

- next node가 어디 있을지 모름
- prefetch가 어렵다
- branch prediction도 불리할 수 있다

반면 contiguous array는:

- 다음 데이터가 가까이 있다
- CPU prefetch에 유리하다
- cache line 활용이 좋다

그래서 array heap, ring buffer, open addressing hash가  
실전에서 자주 강한 이유가 여기 있다.

### 2. node 크기와 fan-out도 layout 문제다

ART나 B-Tree 계열은 단순히 "트리인가"가 아니라  
node 하나에 무엇을 얼마나 담을지가 더 중요하다.

- 작은 node: cache miss는 적지만 depth가 늘어날 수 있다
- 큰 node: depth는 줄지만 line 활용이 나빠질 수 있다

즉 fan-out 자체가 cache-aware tuning 파라미터가 된다.

### 3. 같은 `O(log n)` search라도 layout마다 miss budget이 다르다

정적 ordered search는 자료구조보다 배치가 더 큰 차이를 만들 때가 많다.

- plain sorted array + binary search: 구현은 가장 단순하지만 mid jump가 넓다
- Eytzinger layout: 상위 레벨을 앞쪽에 모아 point lookup locality를 개선한다
- blocked/B-Tree형 배열 배치: fan-out을 키워 cache miss 횟수를 줄이고 range scan 연결도 더 자연스럽게 만든다

즉 "배열인가 트리인가"보다  
"한 번의 lookup이 몇 개의 cache line과 page를 건드리게 할 것인가"가 더 본질적인 질문이다.

| layout | locality 모양 | 특히 잘 맞는 경우 | 아쉬운 점 |
|---|---|---|---|
| Plain sorted array + binary search | mid가 넓게 튄다 | 구현 단순성, 정렬 순회, 유지보수 비용 최소화 | 상위 비교값 재사용과 prefetch 이점이 약하다 |
| Eytzinger | 상위 레벨이 앞쪽에 촘촘히 모인다 | immutable point lookup, `contains`, `lower_bound` hot path | 정렬 순회 시작점 복구와 range scan 연결은 덜 자연스럽다 |
| Blocked/B-Tree형 배열 | 한 block에 여러 pivot을 넣어 page touch를 줄인다 | page/block-aware search, fence pointer, search 후 scan 연계 | fan-out과 block 크기 tuning reasoning이 더 어렵다 |

즉 선택지는 "비교 횟수 몇 번"보다  
"깊이를 따라 많이 miss할 것인가, 아니면 block 하나에 비교를 몰아 넣을 것인가"의 차이다.

여기에 vEB-style cache-oblivious layout까지 넣으면  
block 크기를 박지 않고도 재귀 subtree locality를 노리는 제3의 축이 생긴다.  
특히 `lower_bound` 중심인지, 그 뒤 scan-heavy path가 붙는지에 따라  
Eytzinger, blocked array, vEB의 우선순위가 달라진다.  
비교는 [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](./van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)에 정리했다.

### 4. false sharing은 동시성 구조의 layout 문제다

queue나 counter는 값 자체보다 필드 배치가 병목일 수 있다.

- producer tail
- consumer head
- hot counter fields

이 값들이 같은 cache line에 있으면  
서로 다른 코어가 line ownership을 계속 뺏고 빼앗는다.

그래서 SPSC queue나 counter shard는 흔히:

- padding
- separated hot fields
- per-core local buffer

같은 기법을 쓴다.

### 5. cache-aware는 "무조건 배열"이 아니다

배열이 항상 답은 아니다.

- update가 잦고 resize 비용이 크면 문제가 된다
- sparse 데이터에선 포인터 구조가 낫기도 하다
- branchless scan이 유리한 경우도, 불리한 경우도 있다

즉 cache-aware 설계는 자료구조를 하드웨어에 맞추는 것이지,  
한 가지 레이아웃으로 통일하는 것이 아니다.

### 6. backend에서 어디에 맞나

hot path가 명확한 곳에서 특히 중요하다.

- in-memory index
- queue / mailbox / ring
- metrics counter
- routing table
- dictionary lookup
- immutable search table

이런 곳은 big-O가 이미 충분히 좋기 때문에  
남는 병목이 대부분 layout과 locality로 내려온다.

### 7. 측정도 compare count가 아니라 miss profile로 해야 한다

Eytzinger나 blocked layout을 고를 때 `비교 횟수`만 보면 종종 틀린 결론이 나온다.

- `L1/L2/L3 miss`
- `branch mispredict`
- `TLB/page touch`
- lookup 뒤에 이어지는 range scan 길이

를 함께 봐야 한다.

실무 감각으로 정리하면:

- point lookup만 뜨겁고 정적이면 Eytzinger가 유력하다
- `lower_bound` 뒤에 인접 원소를 계속 읽는다면 blocked/B-Tree형 배열이 더 자연스럽다
- 정렬 순서 순회와 유지보수 단순성이 더 중요하면 plain sorted array가 오히려 낫다

## 실전 시나리오

### 시나리오 1: queue는 맞는데 느린 경우

알고리즘은 맞지만 head/tail false sharing이나 allocation 때문에  
queue가 느릴 수 있다. 이때는 동시성 기법보다 layout을 먼저 봐야 한다.

### 시나리오 2: 정적 lookup table을 어떻게 깔 것인가

plain binary search, Eytzinger, blocked array는 모두 `O(log n)`이지만  
point lookup만 뜨거우면 Eytzinger, range scan과 block 단위 탐색도 중요하면 blocked layout이 더 잘 맞을 수 있다.

### 시나리오 3: compact dictionary

정적 dictionary는 FST 같은 압축 구조로  
메모리 resident footprint 자체를 줄이는 것이 locality 개선으로 이어진다.

### 시나리오 4: 부적합한 경우

hot path가 아니고 개발 복잡도만 크게 늘어난다면  
cache-aware 최적화는 과하다.

## 점검 프레임

| 질문 | 의미 |
|---|---|
| 이 구조의 다음 접근 위치를 CPU가 예측할 수 있는가 | prefetch / locality 감각 |
| 서로 다른 스레드가 같은 cache line을 두드리는가 | false sharing 감각 |
| pointer chasing 수가 너무 많은가 | tree/list 구조 비용 감각 |
| hot field와 cold field를 분리했는가 | line 효율 감각 |
| 배열/블록 단위로 재배치할 가치가 있는가 | layout 재설계 감각 |
| point lookup과 range scan 중 무엇이 hot한가 | Eytzinger vs blocked layout 선택 감각 |
| 재배치나 rebuild 비용을 감당할 수 있는가 | 정적 레이아웃 최적화 적용 가능성 |

## 꼬리질문

> Q: 왜 linked structure가 이론보다 느릴 수 있나요?
> 의도: pointer chasing과 cache miss 비용 이해 확인
> 핵심: 노드가 흩어져 있으면 비교보다 메모리 접근 지연이 더 커지기 때문이다.

> Q: false sharing은 어떤 종류의 문제인가요?
> 의도: 동시성 문제를 락만으로 보지 않는지 확인
> 핵심: 서로 다른 값이라도 같은 cache line에 있으면 코어 간 line invalidation 비용이 생기는 layout 문제다.

> Q: cache-aware 설계가 왜 빅오를 대체하지는 않나요?
> 의도: 알고리즘과 하드웨어 최적화의 역할 분리를 이해하는지 확인
> 핵심: 구조적 차수가 너무 나쁘면 layout만으로는 못 구하고, 반대로 차수가 좋아도 layout이 나쁘면 실전 성능이 무너질 수 있기 때문이다.

## 한 줄 정리

cache-aware layout은 자료구조를 "무슨 연산을 하나"뿐 아니라 "메모리를 어떤 순서와 단위로 밟나"까지 함께 설계해 실제 하드웨어에서의 성능을 끌어올리는 접근이다.
