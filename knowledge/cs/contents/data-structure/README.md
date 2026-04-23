# Data Structure (자료구조)

**난이도: 🔴 Advanced**

> retrieval-anchor-keywords: data structure readme, data structure navigator, data structure playbook, data structure routing guide, basic primer, binary tree vs bst vs heap, binary tree traversal, tree traversal routing, preorder inorder postorder level order, preorder signal, inorder signal, postorder signal, level order queue, binary search tree basics, bst basics, question bank, queue vs deque vs priority queue, fifo queue, queue terminology bridge, queue api vs implementation, enqueue dequeue peek, front rear head tail, deque basics, plain deque, deque router, deque example pack, plain deque vs monotonic deque, monotonic deque vs 0-1 bfs, monotonic deque walkthrough, monotonic stack walkthrough, sliding window maximum trace, sliding window minimum trace, next greater element trace, histogram largest rectangle trace, priority queue basics, java priorityqueue pitfalls, priorityqueue comparator direction, priorityqueue tie breaker, priorityqueue stale entry, priorityqueue not sorted, circular queue, circular queue vs ring buffer, circular queue interview, ring buffer, circular buffer, ring buffer use case matrix, logging ring buffer, telemetry buffer routing, audio ring buffer, producer consumer pipeline routing, bounded queue policy, bounded buffer policy, reject policy, overwrite policy, blocking queue policy, backpressure primer, bounded mpmc queue, sequencer coordination, aba problem, reclamation, segment tree, segment tree not bst or heap, segment tree vs bst, segment tree vs heap, range aggregation tree, interval tree, disjoint interval set, dynamic interval query, online interval insert, booking conflict, overlap query, bloom filter, trie, skip list, timing wheel, delay queue, concurrent skip list, union find deep dive, union find component size, union find component count, union find metadata walkthrough, connectivity question router, same component vs path reconstruction vs shortest path, graph traversal vs union find, connectivity query boundary, path reconstruction router, edge deletion connectivity, ordered workload, ordered search workload matrix, point lookup layout, lower_bound only layout, short scan layout, long scan layout, roaring bitmap, container transition, roaring set op result, roaring lazy union pipeline, bitmap-wide lazy union, roaring whole-bitmap repair, roaring lazy union repair cost, lazy OR materialization cost, roaring intermediate repair path, temporary container roaring, repairAfterLazy hotspot profiling, roaring query result ordering, roaring predicate ordering, repairAfterLazy debt reduction, roaring intermediate result reuse, shared bitmap base reuse, lazy xor temporary run, run-heavy warehouse bitmap, roaring andnot result, roaring difference heuristic, lazy cardinality repair, roaring runOptimize timing, query result runOptimize, bulk built bitmap compaction, bitmap-native set-op, row ordering bitmap, bitmap compression playbook, selection playbook, operations playbook, warehouse sort key bitmap, dictionary encoding bitmap, row group sizing bitmap, late arriving rows bitmap, bitmap maintenance, bitmap compaction, bitmap rebuild, warehouse reclustering bitmap, bitmap locality remediation, bitmap hotspot remediation, id remapping bitmap, runOptimize scheduling tradeoff, roaring run formation, chunk boundary roaring, 16-bit container boundary, interval list vs roaring, whole bitmap run codec, roaring production profiling, roaring run churn observability, chunk-local cardinality histogram, container churn hotspot, sorted ingest locality, bitmap id locality, roaring prometheus metrics, roaring opentelemetry metrics, roaring exemplar sampling, roaring metric naming, bit sliced bitmap sort key, bsi prefix locality, bit slice segment boundary, upper slice run length, eytzinger, cache-oblivious ordered search, van emde boas layout, blocked search array, cache-oblivious b-tree, leaf-packed ordered index, range-scan-friendly ordered index, hybrid top index leaf layout, guide index plus contiguous leaves

## 빠른 탐색

이 `README`는 기본 개념 `primer`, 응용 주제 `catalog`, 아래쪽 `question bank`를 함께 묶는 **navigator 문서**다.
mixed catalog에서 `[playbook]` 라벨은 선택 기준이나 연산 순서가 먼저 필요한 step-oriented 문서라는 뜻이고, 라벨이 없는 항목은 trade-off 중심 `deep dive`다.

- 기본 primer부터 읽고 싶다면:
  - [기본 자료 구조](basic.md)
  - [스택 기초](stack-basics.md) 🟢
  - [연결 리스트 기초](linked-list-basics.md) 🟢
  - [배열 vs 연결 리스트](array-vs-linked-list.md) 🟢
  - [해시 테이블 기초](hash-table-basics.md) 🟢
  - [LRU 캐시 설계 입문](lru-cache-basics.md) 🟢
  - [큐 기초](queue-basics.md) 🟢
  - [트리 기초](tree-basics.md) 🟢
  - [힙 기초](heap-basics.md) 🟢
  - [그래프 기초](graph-basics.md) 🟢
  - [덱 기초](deque-basics.md) 🟢
  - [Deque Router Example Pack](deque-router-example-pack.md)
  - [Connectivity Question Router](connectivity-question-router.md)
  - [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md)
  - [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
  - [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md)
  - [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md)
  - [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md)
  - [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)
  - [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)
  - [Binary Tree vs BST vs Heap Bridge](binary-tree-vs-bst-vs-heap-bridge.md)
  - [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)
  - [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)
  - [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)
  - [Array](basic.md#array-배열)
  - [Linked List](basic.md#linked-list-연결-리스트)
  - [Hash Table](basic.md#hash-table-해시-테이블)
  - [Heap](basic.md#heap-힙)
  - [Tree](basic.md#tree-트리)
  - [Graph](basic.md#graph-그래프)
  - [Union-Find](basic.md#union-find-유니온-파인드)
- 응용 catalog에서 문제 축을 먼저 고르려면:
  - [응용 자료 구조 개요](applied-data-structures-overview.md)
  - [Fenwick Tree vs Segment Tree](fenwick-vs-segment-tree.md)
  - [Bloom Filter vs Cuckoo Filter](bloom-filter-vs-cuckoo-filter.md)
  - [Trie Prefix Search / Autocomplete](trie-prefix-search-autocomplete.md)
- 특정 trade-off deep dive로 바로 들어가려면:
  - [Ring Buffer](ring-buffer.md)
  - [Michael-Scott Lock-Free Queue](michael-scott-lock-free-queue.md)
  - [Interval Tree](interval-tree.md)
  - [Disjoint Interval Set](disjoint-interval-set.md)
  - [Cache-Aware Data Structure Layouts](cache-aware-data-structure-layouts.md)
  - [Ordered Search Workload Matrix](ordered-search-workload-matrix.md)
  - [Eytzinger Layout and Cache-Friendly Search](eytzinger-layout-and-cache-friendly-search.md)
  - [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
  - [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](cache-oblivious-b-tree-vs-plain-veb-layout.md)
  - [Hybrid Top-Index / Leaf Layouts](hybrid-top-index-leaf-layouts.md)
  - [Roaring Container Transition Heuristics](roaring-container-transition-heuristics.md)
  - [Chunk-Boundary Pathologies In Roaring](chunk-boundary-pathologies-in-roaring.md)
  - [Roaring Set-Op Result Heuristics](roaring-set-op-result-heuristics.md)
  - [Roaring Bitmap-Wide Lazy Union Pipeline](roaring-bitmap-wide-lazy-union-pipeline.md)
  - [Roaring Lazy Union And Repair Costs](roaring-lazy-union-and-repair-costs.md)
  - [Roaring Intermediate Repair Path Guide](roaring-intermediate-repair-path-guide.md)
  - [Roaring Query Result Ordering Guide](roaring-query-result-ordering-guide.md)
  - [Roaring ANDNOT Result Heuristics](roaring-andnot-result-heuristics.md)
  - [Roaring runOptimize Timing Guide](roaring-run-optimize-timing-guide.md)
  - [Roaring Instrumentation Schema Examples](roaring-instrumentation-schema-examples.md) (Java/CRoaring bridge, Prometheus/OpenTelemetry naming, adaptive sampling)
  - `[playbook]` [Bitmap Locality Remediation Playbook](bitmap-locality-remediation-playbook.md)
  - `[playbook]` [Roaring Bitmap Selection Playbook](roaring-bitmap-selection-playbook.md)
  - [Compressed Bitmap Families: WAH, EWAH, CONCISE](compressed-bitmap-families-wah-ewah-concise.md)
  - `[playbook]` [Row-Ordering and Bitmap Compression Playbook](row-ordering-and-bitmap-compression-playbook.md)
  - [Warehouse Sort-Key Co-Design for Bitmap Indexes](warehouse-sort-key-co-design-for-bitmap-indexes.md)
  - [Late-Arriving Rows and Bitmap Maintenance](late-arriving-rows-and-bitmap-maintenance.md)
  - [Roaring Run Formation and Row Ordering](roaring-run-formation-and-row-ordering.md)
  - [Roaring Production Profiling Checklist](roaring-production-profiling-checklist.md)
  - [Roaring Run-Churn Observability Guide](roaring-run-churn-observability-guide.md)
  - [Bit-Sliced Bitmap Index](bit-sliced-bitmap-index.md)
  - [Bit-Sliced Bitmap Sort-Key Sensitivity](bit-sliced-bitmap-sort-key-sensitivity.md)
- 선택 기준이나 연산 절차가 먼저 필요하면:
  - `[playbook]` [Fenwick and Segment Tree Operations Playbook](fenwick-segment-tree-operations-playbook.md)
  - `[playbook]` [Sketch and Filter Selection Playbook](sketch-filter-selection-playbook.md)
  - `[playbook]` [Bitmap Locality Remediation Playbook](bitmap-locality-remediation-playbook.md)
  - `[playbook]` [Roaring Bitmap Selection Playbook](roaring-bitmap-selection-playbook.md)
  - `[playbook]` [Row-Ordering and Bitmap Compression Playbook](row-ordering-and-bitmap-compression-playbook.md)
- 면접형 self-check로 마무리하려면:
  - 이 README 아래 `질의응답` 구간
- 문서 역할 구분이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)

## 기본 primer

### 기본 자료 구조 [▶︎ 🗒](basic.md)

- [Array](basic.md#array-배열)
- [Linked List](basic.md#linked-list-연결-리스트)
- [Stack](basic.md#stack-스택)
- [Queue](basic.md#queue-큐) (`enqueue/dequeue` vs `front/rear/head/tail` 브리지 포함)
- [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
- [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md)
- [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)
- [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)
- [Hash Table](basic.md#hash-table-해시-테이블)
- [Heap](basic.md#heap-힙)
- [Tree](basic.md#tree-트리)
- [Binary Tree](basic.md#binary-tree-이진-트리)
- [Binary Tree vs BST vs Heap Bridge](binary-tree-vs-bst-vs-heap-bridge.md)
- [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)
- [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)
- [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)
- [Graph](basic.md#graph-그래프)
- [Union-Find](basic.md#union-find-유니온-파인드)
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)

## 응용 catalog

### 응용 자료 구조 [▶︎ 🗒](applied-data-structures-overview.md)

개별 deep dive로 바로 내려가기 전에, [응용 자료 구조 개요](applied-data-structures-overview.md)에서 문제 유형별 라우팅을 먼저 보면 탐색이 훨씬 수월하다.
아래 mixed catalog에서는 `[playbook]` 라벨로 step-oriented selection / operation 문서를 따로 튀게 했다.

### 큐와 작업 흐름

`FIFO queue`, `deque`, `priority queue` 구분이 먼저 헷갈리면 [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)에서 `도착 순서`, `양쪽 끝 제어`, `우선순위` 축을 먼저 나누고 아래 deep dive로 내려가면 된다.
같은 `deque`라도 `양끝 시뮬레이션`, `sliding window extrema`, `0-1 shortest path`가 서로 다른 패턴이라는 감각을 빨리 잡고 싶다면 [Deque Router Example Pack](deque-router-example-pack.md)으로 바로 가는 편이 빠르다.
`enqueue/dequeue/peek` 같은 FIFO API와 `front/rear/head/tail` 같은 구현 용어를 가장 얕게 이어 주는 입문 정리는 [Queue](basic.md#queue-큐) 섹션이다.
Java `PriorityQueue`를 쓰다가 comparator 방향, tie-breaker, stale entry, sorted iteration 오해가 자주 섞이면 [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md)에서 Java 런타임 기준의 함정을 먼저 정리하는 편이 빠르다.
원형 배열 queue 구현과 시스템 문맥 `ring buffer` 용어가 자꾸 섞이면 [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)에서 `면접형 queue 설계`와 `시스템형 bounded buffer`를 먼저 분리해두는 편이 좋다.
고정 크기 queue가 꽉 찼을 때 `reject`, `overwrite`, `blocking`, `backpressure` 중 무엇이 맞는지 먼저 잡고 싶다면 [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)로 내려가면 `누가 양보하나` 축이 빨리 정리된다.
`logging`, `telemetry`, `audio`, `producer-consumer pipeline`처럼 같은 ring buffer 계열이어도 `유실 허용`, `callback 실시간성`, `fan-in/out`, `stage dependency` 축이 다르면 다음 문서 라우팅이 달라지므로 [Ring Buffer](ring-buffer.md)의 use-case matrix까지 같이 보면 빠르다.

timer 구조를 고를 때는 [Timing Wheel vs Delay Queue](timing-wheel-vs-delay-queue.md)에서 `earliest deadline`과 `timer churn` 축을 먼저 잡고, 이어서 [Concurrent Skip List Internals](concurrent-skiplist-internals.md)에서 `ordered range scan`이 왜 별도 요구인지 보면 읽기 흐름이 자연스럽다.

동시성 큐 internals를 한 축으로 읽고 싶다면 `Ring Buffer -> Lock-Free SPSC Ring Buffer -> Bounded MPMC Queue -> Sequencer-Based Ring Buffer Coordination -> ABA Problem and Tagged Pointers -> Hazard Pointers vs Epoch-Based Reclamation -> Reclamation Cost Trade-offs` 순서가 좋다.
앞쪽은 bounded ring의 slot/state machine과 backpressure를, 뒤쪽은 pointer reuse와 safe reclamation을 이어서 설명한다.

연속 구간을 한 칸씩 밀되 `최대/최소`를 바로 답해야 하면 먼저 [Deque](applied-data-structures-overview.md#deque-덱)에서 `sliding window maximum/minimum`, `recent k extrema` 라우팅을 잡고, 처음 보는 학습자라면 [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md)로 plain deque가 언제 monotonic deque로 바뀌는지 손으로 따라간 뒤 [Monotonic Deque vs Heap for Window Extrema](monotonic-deque-vs-heap-for-window-extrema.md)에서 왜 heap lazy deletion이 차선책인지와 duplicate/stale-entry 함정을 먼저 분리하고, 마지막에 [슬라이딩 윈도우 패턴](../algorithm/sliding-window-patterns.md), [Monotonic Queue / Stack](monotonic-queue-and-stack.md) 순서로 일반화하는 편이 빠르다. 반대로 `next greater element`, `오큰수`, `histogram largest rectangle`처럼 window 만료 없이 stack top에서만 답이 정해지는 문제라면 [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md)로 바로 가는 편이 더 직관적이다.

- [Deque](applied-data-structures-overview.md#deque-덱) (monotonic deque routing for sliding window maximum/minimum, recent `k` extrema)
- [Deque Router Example Pack](deque-router-example-pack.md) (plain deque vs monotonic deque vs 0-1 BFS quick split)
- [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
- [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md) (comparator direction, tie-breaker, stale entry, heap is not a sorted list)
- [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)
- [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)
- [Ring Buffer](ring-buffer.md) (logging/telemetry/audio/pipeline use-case matrix, overwrite vs backpressure routing)
- [Lock-Free SPSC Ring Buffer](lock-free-spsc-ring-buffer.md)
- [Lock-Free MPSC Queue](lock-free-mpsc-queue.md)
- [Bounded MPMC Queue](bounded-mpmc-queue.md)
- [Sequencer-Based Ring Buffer Coordination](sequencer-based-ring-buffer-coordination.md)
- [Michael-Scott Lock-Free Queue](michael-scott-lock-free-queue.md)
- [ABA Problem and Tagged Pointers](aba-problem-and-tagged-pointers.md)
- [Hazard Pointers vs Epoch-Based Reclamation](hazard-pointers-vs-epoch-based-reclamation.md)
- [Reclamation Cost Trade-offs](reclamation-cost-tradeoffs.md)
- [Concurrent Skip List Internals](concurrent-skiplist-internals.md)
- [Work-Stealing Deque](work-stealing-deque.md)
- [Hierarchical Timing Wheel](hierarchical-timing-wheel.md)
- [Calendar Queue](calendar-queue.md)
- [Timing Wheel Variants and Selection](timing-wheel-variants-and-selection.md)
- [Timing Wheel vs Delay Queue](timing-wheel-vs-delay-queue.md)
- [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md) (plain deque -> monotonic deque trace, sliding window maximum/minimum step-by-step)
- [Monotonic Deque vs Heap for Window Extrema](monotonic-deque-vs-heap-for-window-extrema.md) (when deque beats heap lazy deletion, duplicate/stale-entry edge cases, worst-case heap growth)
- [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md) (next greater element, histogram largest rectangle, stack pop moment trace)
- [Monotonic Queue / Stack](monotonic-queue-and-stack.md) (sliding window maximum/minimum, recent `k` extrema)

### 순서 유지, 범위 질의, 캐시

트리 문제에서 "루트를 먼저 기록하나, 자식 결과를 모아 부모를 계산하나, 아니면 레벨별로 보나"가 먼저 막히면 [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)에서 `preorder/inorder/postorder/level-order` signal을 먼저 분리한 뒤 BST/heap/segment tree 문서로 내려가면 된다.

plain `BST`가 왜 입력 순서에 따라 `O(n)`까지 무너지는지부터 헷갈리면 [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)에서 `높이` 관점을 먼저 잡고, 이어서 [TreeMap, HashMap, LinkedHashMap 비교](treemap-vs-hashmap-vs-linkedhashmap.md)와 [Skip List](skip-list.md)로 내려가면 ordered set/map 선택 이유가 훨씬 또렷해진다.

정적 ordered search locality를 비교하려면 `Cache-Aware Data Structure Layouts -> Ordered Search Workload Matrix -> Eytzinger Layout and Cache-Friendly Search -> van Emde Boas Layout vs Eytzinger vs Blocked Arrays -> Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout -> Hybrid Top-Index / Leaf Layouts -> Cache-Oblivious vs Cache-Aware Layouts` 순서로 읽으면 workload triage, point lookup, `lower_bound` 뒤 scan 연결, pure vEB binary와 scan-friendly leaf layout의 차이, top guide와 contiguous leaf의 역할 분리, 재귀 배치의 선택축이 함께 잡힌다.

interval이 처음부터 전부 주어져 한 번 계산하면 끝나는 문제가 아니라, 새 interval이 계속 들어오며 `insert -> overlap query`가 섞이면 `segment tree`보다 [Interval Tree](interval-tree.md)나 [Disjoint Interval Set](disjoint-interval-set.md)을 먼저 보는 편이 맞다.
`segment tree`라는 이름 때문에 ordered tree나 priority tree처럼 읽히면 먼저 [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)에서 역할을 분리하고, 그다음 [Fenwick Tree vs Segment Tree](fenwick-vs-segment-tree.md)와 [Segment Tree Lazy Propagation](segment-tree-lazy-propagation.md)으로 내려가면 혼선이 적다.
`같은 컴포넌트인가`, `경로 하나를 복원하라`, `최단 경로를 구하라`가 한데 섞이면 [Connectivity Question Router](connectivity-question-router.md)에서 먼저 답의 모양을 `yes/no vs actual path vs minimum path`로 분리한 뒤 union-find / BFS / shortest-path 문서로 내려가면 된다.
간선 추가만 있는 연결성은 [Union-Find Deep Dive](union-find-deep-dive.md)로 충분하지만, 삭제가 섞이는 순간은 [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)에서 `왜 plain DSU가 안 되고 DSU rollback / dynamic connectivity로 넘어가는지`를 먼저 분리한 뒤 [DSU Rollback](../algorithm/dsu-rollback.md)로 이어 가면 된다.

- [Heap Variants](heap-variants.md)
- [Radix Heap](radix-heap.md)
- [HashMap 내부 구조](hashmap-internals.md)
- [Robin Hood Hashing](robin-hood-hashing.md)
- [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)
- [Cache-Aware Data Structure Layouts](cache-aware-data-structure-layouts.md)
- [Ordered Search Workload Matrix](ordered-search-workload-matrix.md)
- [Cache-Oblivious vs Cache-Aware Layouts](cache-oblivious-vs-cache-aware-layouts.md)
- [Eytzinger Layout and Cache-Friendly Search](eytzinger-layout-and-cache-friendly-search.md)
- [van Emde Boas Layout vs Eytzinger vs Blocked Arrays](van-emde-boas-layout-vs-eytzinger-vs-blocked-arrays.md)
- [Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout](cache-oblivious-b-tree-vs-plain-veb-layout.md)
- [Hybrid Top-Index / Leaf Layouts](hybrid-top-index-leaf-layouts.md)
- [LRU Cache Design](lru-cache-design.md)
- [TreeMap, HashMap, LinkedHashMap 비교](treemap-vs-hashmap-vs-linkedhashmap.md)
- [Fenwick Tree](fenwick-tree.md)
- [Fenwick Tree vs Segment Tree](fenwick-vs-segment-tree.md)
- `[playbook]` [Fenwick and Segment Tree Operations Playbook](fenwick-segment-tree-operations-playbook.md)
- [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)
- [Indexed Tree (Segment Tree)](applied-data-structures-overview.md#세그먼트-트리-indexed-tree--segment-tree)
- [Segment Tree Lazy Propagation](segment-tree-lazy-propagation.md)
- [Interval Tree](interval-tree.md)
- [Disjoint Interval Set](disjoint-interval-set.md)
- [Skip List](skip-list.md)
- [Connectivity Question Router](connectivity-question-router.md) (same-component yes/no, actual path reconstruction, shortest-path handoff)
- [Union-Find Deep Dive](union-find-deep-dive.md) (same-component yes/no, BFS/DFS traversal boundary, edge-addition-only connectivity)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md) (edge deletion handoff, DSU rollback/dynamic connectivity threshold)
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (component size, component count, redundant union metadata trace)

### 근사 집계와 압축 표현

exact bitmap 계열은 `Roaring Bitmap -> Roaring Container Transition Heuristics -> Chunk-Boundary Pathologies In Roaring -> Roaring Set-Op Result Heuristics -> Roaring Bitmap-Wide Lazy Union Pipeline -> Roaring Lazy Union And Repair Costs -> Roaring Intermediate Repair Path Guide -> Roaring Query Result Ordering Guide -> Roaring ANDNOT Result Heuristics -> Roaring runOptimize Timing Guide -> Roaring Run Formation and Row Ordering -> Roaring Production Profiling Checklist -> Roaring Run-Churn Observability Guide -> [playbook] Bitmap Locality Remediation Playbook -> Roaring Instrumentation Schema Examples -> [playbook] Roaring Bitmap Selection Playbook -> Compressed Bitmap Families: WAH, EWAH, CONCISE -> [playbook] Row-Ordering and Bitmap Compression Playbook -> Warehouse Sort-Key Co-Design for Bitmap Indexes -> Late-Arriving Rows and Bitmap Maintenance -> Bit-Sliced Bitmap Index -> Bit-Sliced Bitmap Sort-Key Sensitivity` 순서로 읽으면 chunk-local 임계값, 16-bit seam이 interval/range workload에서 언제 extra header와 extra run restart로 바뀌는지, set-op 결과 container 선택, per-container lazy union이 bitmap-level repair boundary로 어떻게 누적되는지, run-heavy warehouse bitmap에서 lazy OR savings가 exact count·serialize·`runOptimize()` 경계에서 언제 다시 비용으로 돌아오는지, temporary bitmap/run이 intermediate repair path에서 어떤 rewrite를 만드는지, selective predicate ordering과 shared intermediate reuse가 wide `OR`의 `repairAfterLazy()` debt를 언제 실질적으로 줄이는지, difference가 lazy repair 대신 direct demotion으로 끝나는 지점, bitmap-native set-op 뒤 언제 `runOptimize()`를 cold path handoff에 거는지, sorted ingest가 active chunk 수와 run 수를 어떻게 바꾸는지, profiling 뒤 row ordering·batch compaction·ID remapping·cold-path optimize를 어떤 순서로 써야 하는지, Java `RoaringBitmap` bridge와 CRoaring wrapper에서 chunk/run/transition metric schema를 어떻게 맞추고 Prometheus/OpenTelemetry 이름·adaptive sampling을 어떻게 나눌지, warehouse sort key가 dictionary encoding과 row-group reset 비용을 어떻게 함께 흔드는지, late data와 upsert/delete가 run locality를 언제 무너뜨려 compact나 rebuild 판단으로 이어지는지, 그리고 BSI slice가 sort-key prefix locality와 segment boundary에 따라 bit position별로 다르게 반응하는 지점까지 한 흐름으로 정리할 수 있다.

- [Bloom Filter](bloom-filter.md)
- [Cuckoo Filter](cuckoo-filter.md)
- [Quotient Filter](quotient-filter.md)
- [Xor Filter](xor-filter.md)
- [Bloom Filter vs Cuckoo Filter](bloom-filter-vs-cuckoo-filter.md)
- [Count-Min Sketch](count-min-sketch.md)
- [Space-Saving Heavy Hitters](space-saving-heavy-hitters.md)
- [HyperLogLog](hyperloglog.md)
- [HDR Histogram](hdr-histogram.md)
- [DDSketch](ddsketch.md)
- [KLL Sketch](kll-sketch.md)
- [t-Digest](t-digest.md)
- `[playbook]` [Sketch and Filter Selection Playbook](sketch-filter-selection-playbook.md)
- [Count-Min Sketch vs HyperLogLog](count-min-vs-hyperloglog.md)
- [Approximate Counting for Rate Limiting and Observability](approximate-counting-rate-limiting-observability.md)
- [Roaring Bitmap](roaring-bitmap.md)
- [Roaring Container Transition Heuristics](roaring-container-transition-heuristics.md)
- [Chunk-Boundary Pathologies In Roaring](chunk-boundary-pathologies-in-roaring.md)
- [Roaring Set-Op Result Heuristics](roaring-set-op-result-heuristics.md)
- [Roaring Bitmap-Wide Lazy Union Pipeline](roaring-bitmap-wide-lazy-union-pipeline.md)
- [Roaring Lazy Union And Repair Costs](roaring-lazy-union-and-repair-costs.md)
- [Roaring Intermediate Repair Path Guide](roaring-intermediate-repair-path-guide.md)
- [Roaring Query Result Ordering Guide](roaring-query-result-ordering-guide.md)
- [Roaring ANDNOT Result Heuristics](roaring-andnot-result-heuristics.md)
- [Roaring runOptimize Timing Guide](roaring-run-optimize-timing-guide.md)
- [Roaring Production Profiling Checklist](roaring-production-profiling-checklist.md)
- [Roaring Run-Churn Observability Guide](roaring-run-churn-observability-guide.md)
- `[playbook]` [Bitmap Locality Remediation Playbook](bitmap-locality-remediation-playbook.md)
- [Roaring Instrumentation Schema Examples](roaring-instrumentation-schema-examples.md) (Prometheus/OpenTelemetry naming, adaptive sampling, bridge patterns)
- `[playbook]` [Roaring Bitmap Selection Playbook](roaring-bitmap-selection-playbook.md)
- [Compressed Bitmap Families: WAH, EWAH, CONCISE](compressed-bitmap-families-wah-ewah-concise.md)
- `[playbook]` [Row-Ordering and Bitmap Compression Playbook](row-ordering-and-bitmap-compression-playbook.md)
- [Warehouse Sort-Key Co-Design for Bitmap Indexes](warehouse-sort-key-co-design-for-bitmap-indexes.md)
- [Late-Arriving Rows and Bitmap Maintenance](late-arriving-rows-and-bitmap-maintenance.md)
- [Roaring Run Formation and Row Ordering](roaring-run-formation-and-row-ordering.md)
- [Succinct Bitvector Rank/Select](succinct-bitvector-rank-select.md)
- [Bit-Sliced Bitmap Index](bit-sliced-bitmap-index.md)
- [Bit-Sliced Bitmap Sort-Key Sensitivity](bit-sliced-bitmap-sort-key-sensitivity.md)
- [Elias-Fano Encoded Posting List](elias-fano-encoded-posting-list.md)
- [LSM-Friendly Index Structures](lsm-friendly-index-structures.md)

### 문자열 / Prefix 검색

- [Trie](applied-data-structures-overview.md#trie-트라이)
- [Trie Prefix Search / Autocomplete](trie-prefix-search-autocomplete.md)
- [Adaptive Radix Tree](adaptive-radix-tree.md)
- [Radix Tree](radix-tree.md)
- [Finite State Transducer](finite-state-transducer.md)

---

## 면접형 question bank

아래 구간은 설명 본문이 아니라 self-check용 질문 묶음이다. 막히는 항목은 다시 위의 `primer`, `catalog`, 개별 `deep dive` 문서로 돌아가서 보강한다.

### 질의응답

<details>
<summary>자료구조가 무엇인지 말씀해주세요.</summary>
<p>
  
자료구조는 컴퓨터 과학에서 `효율적인 접근 및 수정`을 가능케 하는 자료의 조직, 관리, 저장을 의미한다.   
더 정확히 말해, 자료 구조는 데이터 값의 모임, 또 데이터 간의 관계, 그리고 데이터에 적용할 수 있는 함수나 명령을 의미한다.

</p>
</details>

<details>
<summary>선형 구조와 비선형 구조의 차이가 무엇인가요?</summary>
<p>

자료구조는 저장되는 데이터의 형태에 따라 구분된다. 선형 구조는 데이터가 일렬로 나열되어있고, 비선형 구조는 데이터가 특정한 형태를 띄고 있다.

</p>
</details>

<details>
<summary>배열과 연결 리스트의 차이점에 대해 설명해주세요.</summary>
<p>

배열은 동일한 자료형의 데이터를 일렬로 나열한 자료구조로서, 데이터 접근이 용이하나 데이터의 삽입과 삭제가 비효율적이다.

연결리스트는 각 노드가 데이터와 포인터를 가지고 일렬로 연결된 자료구조로서, 데이터의 접근이 O(n)으로 느리지만 데이터의 삽입과 삭제가 O(1)로 용이하다. 단, 데이터 삽입/삭제 연산 이전에 데이터에 접근하는 것이 선행되므로 배열보다 비효율적일 수 있다.

</p>
</details>

<details>
<summary>A-B-C-D 순서로 연결된 연결 리스트가 있습니다. C 노드 다음에 F 노드를 삽입할 때의 과정을 설명해주세요.</summary>
<p>

1. F의 next node를 C의 next node인 D로 설정한다.
   `A-B-C-D`
   `F-D`

2. C의 next node를 F로 설정한다.
   `A-B-C-F-D`

</p>
</details>

<details>
<summary>스택으로 큐를 구현할 수 있을까요?</summary>
<p>

네. 2개의 스택을 이용하여 구현할 수 있습니다. Enqueue 연산은 첫번째 스택에 원소를 추가하면 됩니다. Dequeue 연산은 두번째 스택을 이용합니다. 우선 두번째 스택이 비어있다면 첫번째 스택이 빌 때까지 첫번째 스택의 원소를 pop하고 두번째 스택에 push하는 것을 반복합니다. 그리고 두번째 스택이 비어있지 않다면 두번째 스택의 원소를 pop하면 됩니다.

</p>
</details>

<details>
<summary>큐로 스택을 구현할 수 있을까요?</summary>
<p>

네. 2개의 큐를 이용하여 구현할 수 있습니다. `push` 연산은 첫번째 큐에 원소를 추가하기 전에 첫번째 큐가 빌때까지 두번째 큐로 값을 옮겨줍니다. 그 후 첫번째 큐에 원소를 추가하고 두번째 큐에서 다시 첫번째 큐로 빌때까지 원소들을 전부 다시 옮겨줍니다. 쉽게 말하자면 원소를 추가할 때마다 원소들의 위치를 스택에 맞게 변경시키는 것입니다. `pop` 연산은 첫번째 큐에서 dequeue만 하면 됩니다.

</p>
</details>

<details>
<summary>큐와 덱의 차이점은 무엇일까요?</summary>
<p>
  
`큐` 는 front에서만 output이 발생하고 rear에서만 input이 발생하는 입출력의 방향이 제한되어 있는 자료구조이다. 반면 `덱` 은 양방향에서 입출력이 가능하다. 

</p>
</details>

<details>
<summary>큐보다 덱을 사용했을 때 더 효율적인 경우가 있을까요?</summary>
<p>
  
스케줄링 알고리즘을 수행할 때 스케줄링이 복잡해질수록 덱이 더 효율적으로 동작한다. 즉, 우선순위를 관리하는 데 있어 스택과 큐에 비해 이점을 갖는다.  
예를 들어 오래된 프로세스에 우선순위를 주고 싶다면 앞에 있는 프로세스를 빼내야하는데 이는 스택에서 불가능하고 최근에 들어온 프로세스에 우선순위를 두고 싶다면 큐에서 불가능하다. 반면 덱은 두 경우 모두에서 사용 가능하다.

</p>
</details>

<details>
<summary>트리라는 자료구조가 무엇인지 간략하게 한 줄로 설명해보세요.</summary>
<p>
  
자료들 사이의 계층적 관계를 나타내는데 사용하는 자료구조로 부모-자식관계로 표현합니다.

</p>
</details>

<details>
<summary>트리의 용어중 '깊이' 라는 용어의 정의는 무엇인가요?</summary>
<p>
  
루트 노드에서 해당노드까지 도달하는데 사용하는 간선의 개수며, 루트노드의 깊이는 0입니다.

</p>
</details>

<details>
<summary>포화 이진트리와 완전 이진트리의 차이점은 무엇인가요?</summary>
<p>
  
1. 포화 이진 트리(Perfect Binary Tree) : 정 이진트리(Full Binary Tree)에서 모든 단말 노드의 깊이가 같은 이진트리
2. 완전 이진 트리(Complete Binary Tree) : 마지막 레벨은 노드가 왼쪽에 몰려있고, 마지막 레벨을 제외하면 포화이진트리(Perfect Binary Tree) 구조를 띄고 있음

</p>
</details>

<details>
<summary>트리의 순회에 대해 알고있는 것 한 가지 말해주세요.</summary>
<p>
  
1. 전위 순회(Pre-order)  : __현재 노드 방문__ -> 왼쪽 자식 탐색 -> 오른쪽 자식 탐색
2. 중위 순회(In-order)   : 왼쪽 자식 탐색 -> __현재 노드 방문__ -> 오른쪽 자식 탐색
3. 후위 순회(Post-order) : 왼쪽 자식 탐색 -> 오른쪽 자식 탐색 -> __현재노드 방문__
4. 레벨 순회(Level-order): 같은 깊이의 노드를 왼쪽부터 차례대로 방문하며 보통 `queue/BFS`로 구현한다.
자세한 라우팅 기준은 [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)를 참고한다.

</p>
</details>

<details>
<summary>구간합 문제를 누적합으로 풀이한다면, 단점은 무엇이며 그에 비해 인덱스 트리가 갖는 장점은 무엇인지 시간복잡도를 들어 설명해주세요.</summary>
<p>
  
누적합으로 풀 경우 누적합을 구하는데 O(N), 이를 M번 수행하면 O(MN)이 걸린다. 하지만 인덱스 트리를 사용할 경우 누적합을 구하는데 O(logN)이 걸리므로, 이를 M번 수행하면 O(MlogN)이 걸리기에 구간합을 여러차례 구하는 중간에 배열의 값이 바뀌는 경우 인덱스 트리가 적합하다.

</p>
</details>

<details>
<summary>인덱스 트리에서 삽입이 일어날때의 시간복잡도는 몇인가요?</summary>
<p>
  
수행시간은 O(logN)이다.

</p>
</details>

<details>
<summary>힙이란 무엇일까요?</summary>
<p>
  
힙은 최댓값 및 최솟값을 찾아내는 연산을 빠르게 하기 위해 고안된 완전이진트리를 기본으로 한 자료구조로서 다음과 같은 힙 속성을 만족한다.  
A가 B의 부모노드 이면, A의 키값과 B의 키값 사이에는 대소관계가 성립한다.
최대 힙의 경우 `A > B`를 만족하고,  
최소 힙의 경우 `A < B`를 만족한다.

이렇게 힙은 부모와 자식노드 간의 대소관계를 만족하는 `느슨한 정렬 상태`를 가진 자료구조이다. 

</p>
</details>
  
<details>
<summary>그림의 힙 구조에서 삭제연산이 일어났을 때 힙의 변화를 서술하세요.</summary>
<p>
    
<img width="491" alt="스크린샷 2021-06-01 오전 11 47 16" src="https://user-images.githubusercontent.com/22493971/120898116-7b253f80-c664-11eb-9f84-39d795b36bff.png">

1. 루트 노드 값을 삭제한다. (44 삭제)  
2. 가장 마지막 리프노드를 루트 노드로 이동한다. (14가 루트 노드로 이동)  
3. Heapify 진행  
> Heapify란 루트노드부터 시작하여 힙의 구조를 만족할 때까지 부모/자식 노드 간 Swap연산을 하며 밑으로 내려가는 연산을 의미한다. 
    
     a. 현재 노드의 자식노드가 현재 노드보다 클 경우 SWAP한다. (14<->42) (14<->33)  

<img width="491" alt="ㅋㅋ" src="https://user-images.githubusercontent.com/22493971/120898448-defc3800-c665-11eb-95f1-76d75ad804fd.png">

</p>
</details>
