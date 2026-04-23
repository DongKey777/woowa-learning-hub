# 응용 자료 구조 개요

**난이도: 🟢 Beginner**

> 작성자 : [서그림](https://github.com/Seogeurim), [정희재](https://github.com/Hee-Jae)

> retrieval-anchor-keywords: applied data structures, deque, monotonic deque, sliding window maximum, sliding window minimum, recent k maximum, recent k minimum, window extrema, ring buffer, lock-free queue, timing wheel, heap, segment tree, interval tree, disjoint interval set, dynamic interval query, online interval insert, booking conflict, overlap query, bloom filter, count-min sketch, hyperloglog, roaring bitmap, trie, radix tree, finite state transducer, cache eviction
> 상위 문서:
> - [Data Structure README](./README.md)
> - [기본 자료 구조](./basic.md)

응용 자료 구조는 기본 구조를 더 많이 외우는 영역이라기보다, 문제의 **접근 패턴과 제약 조건**을 기준으로 구조를 고르는 영역에 가깝다.  
이 문서는 개별 문서를 다시 풀어 쓰기보다, 어떤 문제에서 어떤 문서로 내려가면 좋은지 빠르게 라우팅하는 데 초점을 둔다.

<details>
<summary>Table of Contents</summary>

- [언제 응용 자료 구조를 고를까](#언제-응용-자료-구조를-고를까)
- [큐와 작업 흐름](#큐와-작업-흐름)
- [우선순위, 범위 질의, 연결성](#우선순위-범위-질의-연결성)
- [근사 집계와 압축 표현](#근사-집계와-압축-표현)
- [문자열과 Prefix 검색](#문자열과-prefix-검색)
- [읽는 순서 추천](#읽는-순서-추천)

</details>

---

## 언제 응용 자료 구조를 고를까

기본 자료 구조만으로도 많은 문제를 풀 수 있지만, 아래 신호가 보이면 응용 자료 구조를 먼저 의심하는 편이 좋다.

- 단순 FIFO/LIFO가 아니라 양끝 삽입/삭제, stealing, backpressure가 중요하다.
- 정확한 집계보다 메모리 상한과 처리량이 더 중요하다.
- prefix 검색, 자동완성, 압축 인덱스처럼 문자열 질의 패턴이 핵심이다.
- 범위 질의, 우선순위 유지, eviction 정책이 자료 구조 선택을 직접 좌우한다.

| 문제 패턴 | 먼저 볼 구조 | 이어서 볼 문서 |
|---|---|---|
| 양끝 삽입/삭제, 스케줄링 | `Deque` | Ring Buffer, Work-Stealing Deque |
| 다중 producer/consumer 저지연 큐 | lock-free queue | SPSC, MPSC, bounded MPMC, sequencer ring, Michael-Scott, Hazard Pointers vs EBR |
| 우선순위/시간 기반 작업 정렬 | heap, timing wheel | Heap Variants, Radix Heap, Hierarchical Timing Wheel, Timing Wheel Variants and Selection |
| 범위 합/최솟값 + 업데이트 | segment tree / fenwick | Lazy Propagation, Fenwick, Operations Playbook |
| online interval insert + overlap query | interval tree / disjoint interval set | Interval Tree, Disjoint Interval Set, TreeMap comparator docs |
| membership test를 메모리 적게 유지 | Bloom/Cuckoo 계열 | 비교 문서, Quotient/Xor Filter |
| 빈도/카디널리티/분위수 근사 | Count-Min, HyperLogLog, sketch | HLL, DDSketch, KLL, t-Digest |
| prefix 검색/자동완성 | trie 계열 | Trie Prefix Search, ART, Radix Tree, FST |

---

## 큐와 작업 흐름

### Deque (덱)

`Deque`는 양쪽 끝에서 삽입과 삭제가 가능해서, 단순한 큐보다 스케줄링과 상태 유지에 훨씬 유연하다.  
슬라이딩 윈도우, work-stealing, bounded buffer, time-based scheduling을 읽을 때 가장 먼저 연결되는 기본 구조다.

특히 `sliding window maximum`, `sliding window minimum`, `최근 k개 중 최대/최소`, `윈도우 극값`처럼 **앞에서는 만료를 제거하고 뒤에서는 의미 없는 후보를 제거**하는 문제가 보이면, 일반 queue보다 `monotonic deque` 라우트가 더 직접적이다.

| 문제 표현 | 덱에서 실제로 하는 일 | 먼저 볼 문서 |
|---|---|---|
| `sliding window maximum`, `max in every window` | index를 담은 **내림차순 monotonic deque**를 유지하고, 새 값보다 작은 후보는 뒤에서 제거한다. | [Monotonic Queue / Stack](./monotonic-queue-and-stack.md), [Sliding Window 패턴](../algorithm/sliding-window-patterns.md) |
| `sliding window minimum`, `min in every window` | index를 담은 **오름차순 monotonic deque**를 유지하고, 새 값보다 큰 후보는 뒤에서 제거한다. | [Monotonic Queue / Stack](./monotonic-queue-and-stack.md), [Sliding Window 패턴](../algorithm/sliding-window-patterns.md) |
| `최근 k개 중 최대/최소`, `recent-k extrema` | front에서 윈도우 밖 index를 제거하고, front를 현재 극값으로 읽는다. | [Monotonic Queue / Stack](./monotonic-queue-and-stack.md) |

덱을 단순히 "양쪽에서 넣고 빼는 queue"로만 기억하면 위 패턴을 놓치기 쉽다.  
이 계열 문제의 핵심은 값을 전부 저장하는 것이 아니라, **다음 질의에 절대 이기지 못할 후보를 뒤에서 미리 버리는 것**이다.

- [Ring Buffer](./ring-buffer.md): 고정 크기 버퍼로 producer/consumer 흐름을 매우 싸게 유지할 때 적합하다.
- [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md): producer 1개, consumer 1개가 확실할 때 가장 단순한 저지연 선택지다.
- [Lock-Free MPSC Queue](./lock-free-mpsc-queue.md): 여러 producer가 한 consumer로 몰리는 비동기 파이프라인에서 본다.
- [Bounded MPMC Queue](./bounded-mpmc-queue.md): 메모리 상한과 backpressure가 중요한 다중 producer/consumer handoff에 맞는다.
- [Sequencer-Based Ring Buffer Coordination](./sequencer-based-ring-buffer-coordination.md): bounded ring을 단순 queue가 아니라 staged pipeline으로 조율할 때 읽는다.
- [Michael-Scott Lock-Free Queue](./michael-scott-lock-free-queue.md): CAS 기반 non-blocking queue의 대표 패턴이다.
- [ABA Problem and Tagged Pointers](./aba-problem-and-tagged-pointers.md): lock-free pointer CAS가 왜 같은 값에도 속을 수 있는지 따로 본다.
- [Hazard Pointers vs Epoch-Based Reclamation](./hazard-pointers-vs-epoch-based-reclamation.md): lock-free queue를 production에서 안전하게 쓰려면 메모리 회수 전략도 같이 봐야 한다.
- [Reclamation Cost Trade-offs](./reclamation-cost-tradeoffs.md): correctness를 넘어서 reclaim 지연과 memory footprint 비용까지 같이 본다.
- [Concurrent Skip List Internals](./concurrent-skiplist-internals.md): ordered query와 ordered semantics가 필요한 동시성 map/set 축으로 이어진다.
- [Work-Stealing Deque](./work-stealing-deque.md): 스레드 풀과 태스크 스케줄러가 부하를 분산할 때 핵심이다.
- [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md): 타이머가 매우 많을 때 시간축 스케줄링 비용을 줄인다.
- [Calendar Queue](./calendar-queue.md): 시간 순 정렬 이벤트를 큐잉할 때 쓰는 변형 구조다.
- [Timing Wheel Variants and Selection](./timing-wheel-variants-and-selection.md): heap, wheel, calendar, radix heap 중 무엇이 맞는지 선택 관점으로 정리한다.
- [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md): blocking heap timer와 bucket timer를 언제 나눠 써야 하는지 운영 감각 기준으로 비교한다.
- [Monotonic Queue / Stack](./monotonic-queue-and-stack.md): 슬라이딩 윈도우 최대/최소, recent `k` extrema처럼 "의미 없는 후보를 버리는" 흐름에서 강하다.

---

## 우선순위, 범위 질의, 연결성

- [Heap Variants](./heap-variants.md): 우선순위 큐 계열을 비교할 때 기본 출발점이다.
- [Radix Heap](./radix-heap.md): key가 단조 증가하는 최단 경로/스케줄링 문제에서 특화된다.
- [HashMap 내부 구조](./hashmap-internals.md): 해시 분포, 충돌, resize 비용이 실제 성능과 correctness를 어떻게 흔드는지 본다.
- [Robin Hood Hashing](./robin-hood-hashing.md): open addressing에서 probe variance를 줄여 lookup tail latency를 평탄화하는 전략이다.
- [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md): 빅오보다 locality와 cache miss가 중요한 hot path에서 읽는다.
- [Cache-Oblivious vs Cache-Aware Layouts](./cache-oblivious-vs-cache-aware-layouts.md): 하드웨어 파라미터를 직접 쓰는 설계와 계층 독립 locality 설계를 비교한다.
- [Eytzinger Layout and Cache-Friendly Search](./eytzinger-layout-and-cache-friendly-search.md): 정적 search array를 heap 같은 배치로 재구성해 locality를 개선하는 대표 예시다.
- [LRU Cache Design](./lru-cache-design.md): eviction 정책이 자료 구조 설계에 직접 들어가는 대표 사례다.
- [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md): 정렬, 순서 보장, 평균 성능 중 무엇을 우선할지 고를 때 본다.
- [Skip List](./skip-list.md): balanced tree 대신 확률적 ordered set/map가 필요할 때 읽는다.
- [Union-Find Deep Dive](./union-find-deep-dive.md): 연결성 판정과 집합 병합이 핵심일 때 별도 축으로 꺼내 보는 구조다.
- [Fenwick Tree](./fenwick-tree.md): point update + prefix/range sum이 중심인 운영 집계에 가볍게 맞는다.
- [Fenwick Tree vs Segment Tree](./fenwick-vs-segment-tree.md): 둘의 경계를 빠르게 구분하고 싶을 때 본다.
- [Fenwick and Segment Tree Operations Playbook](./fenwick-segment-tree-operations-playbook.md): quota, bucket aggregation, sparse timeline 같은 운영 문맥으로 풀어쓴다.

### 세그먼트 트리 (Indexed Tree / Segment Tree)

세그먼트 트리는 "구간 질의는 자주 오고, 중간 값도 바뀐다"는 조건에서 선택한다.  
누적합보다 구현은 무겁지만, 업데이트와 질의를 둘 다 `O(log n)`으로 묶을 수 있다는 점이 핵심이다.

- 작성자 정희재 | [Segment Tree](./materials/세그먼트트리.pdf)
- [Segment Tree Lazy Propagation](./segment-tree-lazy-propagation.md): 구간 갱신까지 붙는 순간 같이 읽어야 하는 후속 문서다.

### 동적 interval insert/query

interval이 한 번에 주어져 `최대 몇 개 선택`이나 `최대 몇 개 겹침`을 묻는 문제는 알고리즘 쪽 routing이 먼저다.  
반대로 새 예약이 계속 들어오고 매번 `겹치나?`, `merge해야 하나?`, `빈 gap이 어디 있나?`를 물으면 자료구조 선택이 핵심이 된다.

- [Interval Tree](./interval-tree.md): overlap search와 dynamic query가 중심일 때 본다.
- [Disjoint Interval Set](./disjoint-interval-set.md): merge, reject, gap tracking처럼 canonical range state 유지가 중심일 때 본다.
- [구간 / Interval Greedy 패턴](../algorithm/interval-greedy-patterns.md): offline interval scheduling과의 경계를 확인할 때 같이 본다.
- [Sweep Line Overlap Counting](../algorithm/sweep-line-overlap-counting.md): offline max concurrency와의 경계를 확인할 때 같이 본다.

---

## 근사 집계와 압축 표현

이 영역은 "정확도 100%보다 메모리/처리량이 더 중요하다"는 전제를 깔고 읽는 편이 좋다.

- Membership filter:
  - [Bloom Filter](./bloom-filter.md)
  - [Cuckoo Filter](./cuckoo-filter.md)
  - [Quotient Filter](./quotient-filter.md)
  - [Xor Filter](./xor-filter.md)
  - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
- Frequency / cardinality / rate / quantile:
  - [Count-Min Sketch](./count-min-sketch.md)
  - [Space-Saving Heavy Hitters](./space-saving-heavy-hitters.md)
  - [HyperLogLog](./hyperloglog.md)
  - [Count-Min Sketch vs HyperLogLog](./count-min-vs-hyperloglog.md)
  - [Approximate Counting for Rate Limiting and Observability](./approximate-counting-rate-limiting-observability.md)
  - [HDR Histogram](./hdr-histogram.md)
  - [DDSketch](./ddsketch.md)
  - [KLL Sketch](./kll-sketch.md)
  - [t-Digest](./t-digest.md)
  - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
- Compressed index / bitmap:
- [Roaring Bitmap](./roaring-bitmap.md)
- [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
- [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
- [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)
  - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
  - [Elias-Fano Encoded Posting List](./elias-fano-encoded-posting-list.md)
  - [LSM-Friendly Index Structures](./lsm-friendly-index-structures.md)

---

## 문자열과 Prefix 검색

### Trie (트라이)

Trie는 문자열을 글자 단위 경로로 저장해 prefix 검색과 자동완성의 기본 구조가 된다.  
문자열 검색에서 "정렬된 배열을 스캔한다"가 아니라 "공통 접두사를 구조 자체에 녹인다"는 발상을 잡는 것이 핵심이다.

- [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md): 자동완성과 prefix 매칭 실전 문제를 바로 연결한다.
- [Adaptive Radix Tree](./adaptive-radix-tree.md): sparse node를 더 효율적으로 다루는 radix-tree 계열 확장이다.
- [Radix Tree](./radix-tree.md): compressed trie가 메모리와 깊이를 어떻게 줄이는지 본다.
- [Finite State Transducer](./finite-state-transducer.md): 사전/검색 엔진에서 prefix 구조를 더 압축적으로 운용할 때 이어서 읽는다.

---

## 읽는 순서 추천

1. [Deque](#deque-덱) -> [Ring Buffer](./ring-buffer.md) -> [Lock-Free SPSC Ring Buffer](./lock-free-spsc-ring-buffer.md)
2. [Heap Variants](./heap-variants.md) -> [HashMap 내부 구조](./hashmap-internals.md) -> [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
3. [Bloom Filter](./bloom-filter.md) -> [Count-Min Sketch](./count-min-sketch.md) -> [HyperLogLog](./hyperloglog.md) -> [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
4. [Trie](#trie-트라이) -> [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md) -> [Radix Tree](./radix-tree.md)
