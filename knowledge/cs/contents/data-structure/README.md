# Data Structure (자료구조)

**난이도: 🔴 Advanced**

> retrieval-anchor-keywords: data structure readme, data structure navigator, data structure playbook, data structure routing guide, basic primer, mini prompt pack, mini prompt direct link, applied data structure mini prompt, 초미니 실전 프롬프트 팩, 초미니 실전 프롬프트 팩 바로가기, binary tree vs bst vs heap, binary tree traversal, tree traversal routing, preorder inorder postorder level order, preorder signal, inorder signal, postorder signal, level order queue, binary search tree basics, bst basics, question bank, queue vs deque vs priority queue, fifo queue, queue terminology bridge, queue api vs implementation, enqueue dequeue peek, front rear head tail, deque basics, plain deque, deque router, deque example pack, plain deque vs monotonic deque, monotonic deque vs 0-1 bfs, monotonic deque walkthrough, monotonic stack walkthrough, sliding window maximum trace, sliding window minimum trace, next greater element trace, histogram largest rectangle trace, priority queue basics, java priorityqueue pitfalls, priorityqueue comparator direction, priorityqueue tie breaker, priorityqueue stale entry, priorityqueue not sorted, scheduledexecutorservice vs delayqueue, scheduled executor service delayqueue bridge, scheduled executor deadline ticket queue, scheduledfuture cancel stale entry, scheduledfuture cancellation, scheduledthreadpoolexecutor removeoncancelpolicy, removeOnCancelPolicy, cancelled scheduled task queue retention, not one sleeping thread per task, fixed rate vs fixed delay queue mental model, fixed rate timeline trace, fixed delay timeline trace, scheduleAtFixedRate timeline, scheduleWithFixedDelay timeline, periodic task re-enqueue, repeating task requeue, delayqueue repeating task, delayqueue periodic task, self rescheduling job, stale ticket bug, java scheduled executor data structure, java timer clock choice, nanoTime vs currentTimeMillis, System.nanoTime vs currentTimeMillis, delayqueue nanotime, monotonic clock java, wall clock vs monotonic clock, relative delay java, deadlineNanos, delayqueue vs priorityqueue, java delayqueue, timer priority policy split, delayqueue business priority, due time gate, delayed compareTo business priority, scheduler priority after due, ready queue priority, priorityblockingqueue vs delayqueue, priorityblockingqueue timer misuse, priorityblockingqueue timer queue, timer cancellation stale entry, delayqueue generation flag, latest wins timer, lazy stale skip, top-k heap direction, top k heap direction, kth largest min heap, streaming top-k heap, median two heaps, java priorityqueue heap direction, circular queue, circular queue vs ring buffer, circular queue interview, ring buffer, circular buffer, ring buffer use case matrix, logging ring buffer, telemetry buffer routing, audio ring buffer, producer consumer pipeline routing, bounded queue policy, bounded buffer policy, reject policy, overwrite policy, blocking queue policy, backpressure primer, bounded mpmc queue, sequencer coordination, aba problem, reclamation, segment tree, segment tree not bst or heap, segment tree vs bst, segment tree vs heap, range aggregation tree, interval tree, disjoint interval set, dynamic interval query, online interval insert, booking conflict, overlap query, bloom filter, trie, skip list, timing wheel, delay queue, concurrent skip list, union find deep dive, union find component size, union find component count, union find metadata walkthrough, connected components, connected component query, connected component count, 연결 요소, 연결 요소 개수, 연결 컴포넌트, connectivity question router, same component vs path reconstruction vs shortest path, graph traversal vs union find, connectivity query boundary, path reconstruction router, edge deletion connectivity, friend network group count, friend network group size, subway transfer count, minimum transfers, transfer count bfs, 환승 횟수, 최소 환승 경로, 친구 네트워크 그룹 수, ordered workload, ordered search workload matrix, point lookup layout, lower_bound only layout, short scan layout, long scan layout, roaring bitmap, container transition, roaring set op result, roaring lazy union pipeline, bitmap-wide lazy union, roaring whole-bitmap repair, roaring lazy union repair cost, lazy OR materialization cost, roaring intermediate repair path, temporary container roaring, repairAfterLazy hotspot profiling, roaring query result ordering, roaring predicate ordering, repairAfterLazy debt reduction, roaring intermediate result reuse, shared bitmap base reuse, lazy xor temporary run, run-heavy warehouse bitmap, roaring andnot result, roaring difference heuristic, lazy cardinality repair, roaring runOptimize timing, query result runOptimize, bulk built bitmap compaction, bitmap-native set-op, row ordering bitmap, bitmap compression playbook, selection playbook, operations playbook, warehouse sort key bitmap, dictionary encoding bitmap, row group sizing bitmap, late arriving rows bitmap, bitmap maintenance, bitmap compaction, bitmap rebuild, warehouse reclustering bitmap, bitmap locality remediation, bitmap hotspot remediation, id remapping bitmap, runOptimize scheduling tradeoff, roaring run formation, chunk boundary roaring, 16-bit container boundary, interval list vs roaring, whole bitmap run codec, roaring production profiling, roaring run churn observability, chunk-local cardinality histogram, container churn hotspot, sorted ingest locality, bitmap id locality, roaring prometheus metrics, roaring opentelemetry metrics, roaring exemplar sampling, roaring metric naming, bit sliced bitmap sort key, bsi prefix locality, bit slice segment boundary, upper slice run length, eytzinger, cache-oblivious ordered search, van emde boas layout, blocked search array, cache-oblivious b-tree, leaf-packed ordered index, hybrid top index leaf layout, guide index plus contiguous leaves

## 빠른 탐색

이 `README`는 기본 개념 `primer`, 응용 주제 `catalog`, 아래쪽 `question bank`를 함께 묶는 **navigator 문서**다.
mixed catalog에서 `[playbook]` 라벨은 선택 기준이나 연산 순서가 먼저 필요한 step-oriented 문서라는 뜻이고, 라벨이 없는 항목은 trade-off 중심 `deep dive`다.

- 기본 primer부터 읽고 싶다면:
  - 설명이 붙은 링크는 `무슨 질문에서 여길 여나`만 짧게 적었다.
  - [기본 자료 구조](basic.md)
  - [스택 기초](stack-basics.md) 🟢
  - [연결 리스트 기초](linked-list-basics.md) 🟢
  - [배열 vs 연결 리스트](array-vs-linked-list.md) 🟢
  - [Backend Data-Structure Starter Pack](backend-data-structure-starter-pack.md) 🟢
  - [복잡도와 알고리즘 패턴 기초](complexity-and-algorithm-pattern-foundations-backend-juniors.md) 🟢
  - [해시 테이블 기초](hash-table-basics.md) 🟢
  - [LRU 캐시 설계 입문](lru-cache-basics.md) 🟢
  - [큐 기초](queue-basics.md) 🟢
  - [트리 기초](tree-basics.md) 🟢
  - [힙 기초](heap-basics.md) 🟢
  - [그래프 기초](graph-basics.md) 🟢
  - [덱 기초](deque-basics.md) 🟢
  - [Deque Router Example Pack](deque-router-example-pack.md) (`plain deque` vs `monotonic deque` vs `0-1 BFS`)
  - [Connectivity Question Router](connectivity-question-router.md) (`same group` vs `actual path` vs `minimum path`)
  - [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (`same?`가 `size/count`까지 커질 때)
  - [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
  - [Heap vs Priority Queue vs Ordered Map Beginner Bridge](heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
  - [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md) (`online interval insert`와 `offline interval merge`를 첫 표에서 바로 가르는 예약 입문)
  - [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md) (`stable-order` 오해, duplicate priority, tie-breaker)
  - [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md)
  - [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md)
  - [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md)
  - [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md)
  - [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md)
  - [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md)
  - [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md)
  - [Timer Priority Policy Split](timer-priority-policy-split.md)
  - [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md)
  - [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md)
  - [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md) (`sliding window max/min` 손추적, duplicate tie-break)
  - [Sliding Window Duplicate Extrema Index Drill](sliding-window-duplicate-extrema-index-drill.md) (`왼쪽 index 유지` vs `오른쪽 index 대체`)
  - [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md) (`next/previous`, `strict vs equal`, flush 규칙)
  - [Monotonic Duplicate Rule Micro-Drill](monotonic-duplicate-rule-micro-drill.md) (`<` vs `<=`, `>` vs `>=` 1문장 규칙)
  - [Monotonic Strict-vs-Equal Translation Card](monotonic-strict-vs-equal-translation-card.md) (문장 신호 -> pop 조건 번역)
  - [Deque vs Stack Signal Card](deque-vs-stack-signal-card.md) (`window answer read` vs `index answer finalize`)
  - [Monotonic Operator Boundary Cheat Sheet](monotonic-operator-boundary-cheat-sheet.md) (`window/recent k -> deque`, `next/previous -> stack`)
  - [Monotonic Deque vs Monotonic Stack Shared-Input Drill](monotonic-deque-vs-stack-shared-input-drill.md) (같은 입력으로 `deque` vs `stack`)
  - [Monotonic Structure Router Quiz](monotonic-structure-router-quiz.md) (`deque` vs `stack` vs `neither`)
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
  - [응용 자료 구조 개요](applied-data-structures-overview.md) (`문제 문장 -> 연산 -> 구조` 30초 입문)
  - [초미니 실전 프롬프트 팩 바로가기](applied-data-structures-overview.md#초미니-실전-프롬프트-팩) (상황별 `처음 볼 문서`와 `다음 문서 1개`, 그리고 `온라인/윈도우/근사/배치` 같은 한 단어 오답 경고 힌트가 붙은 첫 분기 오독 방지 카드)
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
- [Backend Data-Structure Starter Pack](backend-data-structure-starter-pack.md)
- [복잡도와 알고리즘 패턴 기초](complexity-and-algorithm-pattern-foundations-backend-juniors.md)
- [Stack](basic.md#stack-스택)
- [Queue](basic.md#queue-큐) (`enqueue/dequeue` vs `front/rear/head/tail` 브리지 포함)
- [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
- [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md) (중복 priority trace, stable-order 오해, `(priority, sequence)` tie-breaker)
- [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md)
- [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md)
- [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md)
- [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md)
- [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md)
- [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md)
- [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md)
- [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md)
- [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md)
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
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (`same?` 질문이 `size/count`까지 확장될 때)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)

## 응용 catalog

### 응용 자료 구조 [▶︎ 🗒](applied-data-structures-overview.md)

개별 deep dive 전에, [응용 자료 구조 개요](applied-data-structures-overview.md)에서 `문제 문장 -> 필요한 연산 -> 자료 구조` 흐름과 30초 선택 플로우만 먼저 잡아두면 첫 진입이 훨씬 빨라진다.
아래 mixed catalog에서는 `[playbook]` 라벨로 step-oriented selection / operation 문서를 따로 튀게 했다.

### 큐와 작업 흐름

`FIFO queue`, `deque`, `priority queue` 구분이 먼저 헷갈리면 [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)에서 `도착 순서`, `양쪽 끝 제어`, `우선순위` 축을 먼저 나누고, `A(2) -> B(1) -> C(1)` 한 입력으로 `FIFO poll`과 `duplicate-priority poll`을 바로 비교한 초급 trace, 그리고 `먼저 도착한 요청`, `비용 0은 앞`, `상위 3개만 유지` 같은 자연어 문장을 핵심 연산으로 번역하는 짧은 bridge 예시까지 보고 아래 deep dive로 내려가면 된다.
같은 `deque`라도 `양끝 시뮬레이션`, `sliding window extrema`, `0-1 shortest path`가 서로 다른 패턴이라는 감각을 빨리 잡고 싶다면 [Deque Router Example Pack](deque-router-example-pack.md)으로 바로 가는 편이 빠르다.
`enqueue/dequeue/peek` 같은 FIFO API와 `front/rear/head/tail` 같은 구현 용어를 가장 얕게 이어 주는 입문 정리는 [Queue](basic.md#queue-큐) 섹션이다.
Java `PriorityQueue`를 쓰다가 comparator 방향, tie-breaker, stale entry, sorted iteration 오해가 자주 섞이면 [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md)에서 중복 priority trace와 `(priority, sequence)` 패턴까지 함께 정리하는 편이 빠르다.
Java timer executor를 떠올리며 `PriorityBlockingQueue`면 thread safety와 timer 대기가 한 번에 해결된다고 느껴지면 [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md)에서 `empty blocking`과 `deadline blocking` 차이를 먼저 분리해두는 편이 좋다.
`ScheduledExecutorService`를 쓰면서 내부에서 작업이 어떻게 기다리는지 자료구조 그림이 안 잡히거나, `scheduleAtFixedRate()`와 `scheduleWithFixedDelay()`가 왜 다른 박자로 다시 queue에 들어가는지 헷갈리면 [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md)에서 `deadline ticket -> delayed work queue -> worker -> periodic re-enqueue` 흐름을 먼저 잡아두면 좋다.
직접 `DelayQueue`로 반복 작업을 만들면서 fixed-rate와 fixed-delay를 어떤 수식으로 다시 넣는지, 그리고 self-rescheduling 코드에서 stale ticket이 어디서 생기는지 같이 보고 싶다면 [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md)가 가장 바로 맞는 진입점이다.
상대 지연을 queue 내부 deadline으로 저장할 때 `currentTimeMillis()`와 `nanoTime()` 중 무엇이 더 자연스러운지 막히면 [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md)에서 `벽시계 vs 스톱워치` 감각을 먼저 잡고 가면 이후 `DelayQueue` 문서가 훨씬 덜 헷갈린다.
`ScheduledFuture.cancel()`을 호출했는데 `true`가 나와도 왜 queue size가 안 줄 수 있는지, 취소된 작업이 왜 내부에서 stale ticket처럼 남는지, 이 API를 `DelayQueue` 쪽 invalidation으로 어떻게 번역해 읽어야 하는지, `removeOnCancelPolicy`를 언제 켜야 하는지 헷갈리면 [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md)에서 future 상태 전환과 DelayQueue-style stale-entry mental model을 한 그림으로 먼저 붙여두면 좋다.
heap-backed timer queue에서 `remove(ticket)`가 왜 `poll()`처럼 바로 끝나지 않는지, exact handle과 `equals()` 기반 제거가 왜 다른 함정으로 이어지는지 헷갈리면 [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md)에서 `head pop vs middle search`, `handle vs equality`, `latest generation` 함정을 먼저 분리해두면 좋다.
`DelayQueue`를 직접 구현해 보며 `Delayed.compareTo()`와 `getDelay()`가 왜 같은 deadline을 봐야 하는지 헷갈리면 [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md)에서 `head ordering`과 `expired head` 계약을 먼저 확인하는 편이 안전하다.
`Delayed.compareTo()`에 business priority까지 넣고 싶어질 때는 [Timer Priority Policy Split](timer-priority-policy-split.md)에서 `due-time gate`와 `ready priority ordering`을 먼저 분리하는 편이 안전하다.
`DelayQueue`를 이미 골랐는데 취소나 재예약 때문에 오래된 timer ticket이 왜 남는지 막히면 [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md)에서 `즉시 제거`, `lazy stale skip`, `generation` 플래그, latest-wins 검사를 먼저 분리해두는 편이 좋다.
Java timer executor나 delayed task queue를 만들 때 `PriorityQueue`로 끝내도 되는지, `DelayQueue`가 필요한지 헷갈리면 [DelayQueue vs PriorityQueue Timer Pitfalls](delayqueue-vs-priorityqueue-timer-pitfalls.md)에서 `정렬`과 `delay-aware blocking`, cancellation stale-entry trade-off를 먼저 분리해두는 편이 안전하다. 같은 문서의 non-timer 분기에서 stable-order 요구를 `(priority, sequence)` comparator 패턴으로 바로 라우팅해 준다.
`kth-largest`, `streaming top-k`, `median`에서 min-heap / max-heap 방향 선택이 이름과 다르게 느껴질 때는 [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md)로 바로 이어 보면 "루트가 어떤 경계값을 대표해야 하는가" 기준이 정리된다.
원형 배열 queue 구현과 시스템 문맥 `ring buffer` 용어가 자꾸 섞이면 [Circular Queue vs Ring Buffer Primer](circular-queue-vs-ring-buffer-primer.md)에서 `면접형 queue 설계`와 `시스템형 bounded buffer`를 먼저 분리해두는 편이 좋다.
고정 크기 queue가 꽉 찼을 때 `reject`, `overwrite`, `blocking`, `backpressure` 중 무엇이 맞는지 먼저 잡고 싶다면 [Bounded Queue Policy Primer](bounded-queue-policy-primer.md)로 내려가면 `누가 양보하나` 축이 빨리 정리된다.
`logging`, `telemetry`, `audio`, `producer-consumer pipeline`처럼 같은 ring buffer 계열이어도 `유실 허용`, `callback 실시간성`, `fan-in/out`, `stage dependency` 축이 다르면 다음 문서 라우팅이 달라지므로 [Ring Buffer](ring-buffer.md)의 use-case matrix까지 같이 보면 빠르다.

timer 구조를 고를 때는 [Timing Wheel vs Delay Queue](timing-wheel-vs-delay-queue.md)에서 `earliest deadline`과 `timer churn` 축을 먼저 잡고, 이어서 [Concurrent Skip List Internals](concurrent-skiplist-internals.md)에서 `ordered range scan`이 왜 별도 요구인지 보면 읽기 흐름이 자연스럽다.

동시성 큐 internals를 한 축으로 읽고 싶다면 `Ring Buffer -> Lock-Free SPSC Ring Buffer -> Bounded MPMC Queue -> Sequencer-Based Ring Buffer Coordination -> ABA Problem and Tagged Pointers -> Hazard Pointers vs Epoch-Based Reclamation -> Reclamation Cost Trade-offs` 순서가 좋다.
앞쪽은 bounded ring의 slot/state machine과 backpressure를, 뒤쪽은 pointer reuse와 safe reclamation을 이어서 설명한다.

연속 구간을 한 칸씩 밀되 `최대/최소`를 바로 답해야 하면 먼저 [Deque](applied-data-structures-overview.md#deque-덱)에서 `sliding window maximum/minimum`, `recent k extrema` 라우팅을 잡고, 중복값에서 `<`와 `<=`가 왜 갈리는지부터 짧게 고정하고 싶다면 [Sliding Window Duplicate Extrema Index Drill](sliding-window-duplicate-extrema-index-drill.md)이나 [Monotonic Duplicate Rule Micro-Drill](monotonic-duplicate-rule-micro-drill.md)로 `왼쪽 index 유지 vs 오른쪽 index 대체`, `이전 값 유지 vs 새 값 대체` 한 문장을 먼저 적는 편이 안전하다. 그다음 `deque vs stack` 선택이 막히면 [Monotonic Deque vs Monotonic Stack Shared-Input Drill](monotonic-deque-vs-stack-shared-input-drill.md)로 `window 만료`와 `pop 시점 답 확정` 차이를 한 입력에서 빠르게 잡고, 이어서 [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md)로 plain deque가 언제 monotonic deque로 바뀌는지 손으로 따라가면 된다. 이후 [Monotonic Deque vs Heap for Window Extrema](monotonic-deque-vs-heap-for-window-extrema.md)에서 문서 첫머리 6줄 라우터 박스로 `deque부터 볼지`, `heap lazy deletion으로 갈지`, `사실 다른 구조를 봐야 할지`를 먼저 자르고, duplicate에서 `대표를 먼저 정하는 deque`와 `복사본을 일단 넣고 stale top만 치우는 heap`이 어떻게 갈리는지까지 비교 표로 이어 보면 초입 판단이 훨씬 빨라진다. 마지막에 [슬라이딩 윈도우 패턴](../algorithm/sliding-window-patterns.md), [Monotonic Queue / Stack](monotonic-queue-and-stack.md) 순서로 일반화하는 편이 빠르다. 반대로 `next greater element`, `오큰수`, `histogram largest rectangle`처럼 window 만료 없이 stack top에서만 답이 정해지는 문제라면 [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md)로 바로 가는 편이 더 직관적이다.

- [Deque](applied-data-structures-overview.md#deque-덱) (monotonic deque routing for sliding window maximum/minimum, recent `k` extrema)
- [Deque Router Example Pack](deque-router-example-pack.md) (plain deque vs monotonic deque vs 0-1 BFS quick split)
- [Queue vs Deque vs Priority Queue Primer](queue-vs-deque-vs-priority-queue-primer.md)
- [Java PriorityQueue Pitfalls](java-priorityqueue-pitfalls.md) (comparator direction, duplicate-priority stable-order misconception, `(priority, sequence)` tie-breaker, stale entry, heap is not a sorted list)
- [PriorityBlockingQueue Timer Misuse Primer](priorityblockingqueue-timer-misuse-primer.md) (`BlockingQueue`의 empty wait와 timer deadline wait 차이)
- [ScheduledExecutorService vs DelayQueue Bridge](scheduledexecutorservice-vs-delayqueue-bridge.md) (`DelayQueue` head/deadline 감각, scheduled executor worker queue, fixed-rate vs fixed-delay 재등록 timeline)
- [DelayQueue Repeating Task Primer](delayqueue-repeating-task-primer.md) (`fixed-rate` vs `fixed-delay` 재등록 수식, self-rescheduling job, stale-ticket bug 진입점)
- [Java Timer Clock Choice Primer](java-timer-clock-choice-primer.md) (`currentTimeMillis()`와 `nanoTime()`의 역할 분리, relative deadline clock 감각)
- [ScheduledFuture Cancellation Bridge](scheduledfuture-cancel-stale-entries.md) (`cancel()` 반환값, DelayQueue-style invalidation, stale ticket mental model, `queue.size()` 착시, `removeOnCancelPolicy` queue-cost trade-off)
- [DelayQueue Remove Cost Primer](delayqueue-remove-cost-primer.md) (heap의 head pop vs arbitrary remove, `handle`/`equals()` cancellation caveat)
- [DelayQueue Delayed Contract Primer](delayqueue-delayed-contract-primer.md) (`Delayed.compareTo()`와 `getDelay()` deadline alignment)
- [Timer Priority Policy Split](timer-priority-policy-split.md) (`Delayed.compareTo()`를 business priority로 오버로딩하지 않고 due-time gate와 ready queue 정책 분리)
- [Timer Cancellation and Reschedule Stale Entry Primer](timer-cancellation-reschedule-stale-entry-primer.md) (`DelayQueue` 이후 generation flag, lazy stale skip, latest-wins cancellation/reschedule 정책)
- [DelayQueue vs PriorityQueue Timer Pitfalls](delayqueue-vs-priorityqueue-timer-pitfalls.md) (delay-aware blocking, cancellation, stale-entry timer trade-off, non-timer stable-order -> `(priority, sequence)` route)
- [Top-K Heap Direction Patterns](top-k-heap-direction-patterns.md) (`kth-largest`, streaming top-k, median에서 min-heap / max-heap 방향 선택)
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
- [Monotonic Deque Walkthrough](monotonic-deque-walkthrough.md) (plain deque -> monotonic deque trace, sliding window maximum/minimum step-by-step, 값만 출력 vs index 출력에서 `<`/`<=`, `>`/`>=`가 갈리는 duplicate tie-break 미니 박스와 4문항 strict/or-equal 퀴즈 + 4문항 duplicate 대표자 퀴즈)
- [Sliding Window Duplicate Extrema Index Drill](sliding-window-duplicate-extrema-index-drill.md) (sliding-window max/min에서 duplicate extrema index tie-break만 따로 분리해 `왼쪽 index`와 `오른쪽 index` 규칙을 작은 표와 예제로 먼저 고정하는 초급 드릴)
- [Monotonic Deque vs Heap for Window Extrema](monotonic-deque-vs-heap-for-window-extrema.md) (6-line beginner router box for `deque vs heap vs other`, duplicate vs stale-entry comparison table, worst-case heap growth)
- [Monotonic Stack Walkthrough](monotonic-stack-walkthrough.md) (첫머리 `strictly` 번역 체크 1줄, next greater element, histogram largest rectangle, index vs value, `previous/next smaller/greater` while 조건 템플릿 표, `previous vs next`와 `strict/or-equal`을 한 번에 자르는 compact 미니 퀴즈, 연산자/flush 기준)
- [Monotonic Duplicate Rule Micro-Drill](monotonic-duplicate-rule-micro-drill.md) (`<` vs `<=`, `>` vs `>=`를 `이전 값 유지 vs 새 값 대체` 규칙과 작은 duplicate 예제로 바로 고정하는 초급 드릴)
- [Monotonic Strict-vs-Equal Translation Card](monotonic-strict-vs-equal-translation-card.md) (`first greater`, `greater or equal`, `leftmost max`, `rightmost min`을 바로 pop 조건으로 번역하는 한 화면 카드)
- [Deque vs Stack Signal Card](deque-vs-stack-signal-card.md) (`window answer read`와 `index answer finalize`를 2행 비교표와 fresh 예시 2개로 끊어 보는 초소형 beginner 카드)
- [Monotonic Operator Boundary Cheat Sheet](monotonic-operator-boundary-cheat-sheet.md) (`window/recent k -> deque`, `next/previous -> stack` 1페이지 결정표로 먼저 분기한 뒤, `값만 구함 vs 왼쪽 index tie-break`와 duplicate deque 입력 1개를 바로 이어 보는 초급 치트시트)
- [Monotonic Deque vs Monotonic Stack Shared-Input Drill](monotonic-deque-vs-stack-shared-input-drill.md) (먼저 [Monotonic Structure Router Quiz](monotonic-structure-router-quiz.md)로 `deque vs stack vs neither`를 고른 뒤, 같은 입력에서 `window max/min`과 `NGE/PSE`를 함께 비교하고 duplicate add-on으로 `<` vs `<=`, `>` vs `>=` 차이까지 짧게 고정하는 초급 손추적 드릴)
- [Monotonic Structure Router Quiz](monotonic-structure-router-quiz.md) (`signal -> 선택 구조` 1페이지 표와 6문항으로 `deque vs stack vs neither` 첫 분기를 빠르게 잡고, `neither` 안의 `map/freq sliding window` vs `interval overlap`도 짧은 handoff 예제로 나눠 주는 첫 독서용 라우팅 퀴즈)
- [Monotonic Queue / Stack](monotonic-queue-and-stack.md) (상단 초급 5줄 멘탈 모델 박스로 `좋은 후보만 남긴다` 감각부터 잡고, sliding window maximum/minimum과 recent `k` extrema로 내려가는 브리지)

### 순서 유지, 범위 질의, 캐시

트리 문제에서 "루트를 먼저 기록하나, 자식 결과를 모아 부모를 계산하나, 아니면 레벨별로 보나"가 먼저 막히면 [Binary Tree Traversal Routing Guide](binary-tree-traversal-routing-guide.md)에서 `preorder/inorder/postorder/level-order` signal을 먼저 분리한 뒤 BST/heap/segment tree 문서로 내려가면 된다.

plain `BST`가 왜 입력 순서에 따라 `O(n)`까지 무너지는지부터 헷갈리면 [Balanced BST vs Unbalanced BST Primer](balanced-bst-vs-unbalanced-bst-primer.md)에서 `높이` 관점을 먼저 잡고, 이어서 [TreeMap, HashMap, LinkedHashMap 비교](treemap-vs-hashmap-vs-linkedhashmap.md)와 [Skip List](skip-list.md)로 내려가면 ordered set/map 선택 이유가 훨씬 또렷해진다. 이번 정리에는 `lower/floor/ceiling/higher`가 범위를 벗어날 때 `null`을 돌려주는 한 줄 경계표도 추가되어, `TreeMap` 첫 사용에서 나오는 NPE 실수를 바로 잡기 쉽다.

예약/캘린더/gap-check 문제에서 `floorKey`/`ceilingKey`/`subMap`이 왜 자연스럽게 나오는지부터 잡고 싶다면 [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md)로 먼저 들어가 `online interval insert`와 `offline interval merge`를 2열 표로 자른 뒤, `왼쪽 예약`, `오른쪽 예약`, `시간창 view` 감각을 익히고 [Disjoint Interval Set](disjoint-interval-set.md)이나 [Interval Tree](interval-tree.md)로 내려가면 혼선이 적다.

정적 ordered search locality를 비교하려면 `Cache-Aware Data Structure Layouts -> Ordered Search Workload Matrix -> Eytzinger Layout and Cache-Friendly Search -> van Emde Boas Layout vs Eytzinger vs Blocked Arrays -> Cache-Oblivious B-Tree / Leaf-Packed Variants vs Plain vEB Layout -> Hybrid Top-Index / Leaf Layouts -> Cache-Oblivious vs Cache-Aware Layouts` 순서로 읽으면 workload triage, point lookup, `lower_bound` 뒤 scan 연결, pure vEB binary와 scan-friendly leaf layout의 차이, top guide와 contiguous leaf의 역할 분리, 재귀 배치의 선택축이 함께 잡힌다.

interval이 처음부터 전부 주어져 한 번 계산하면 끝나는 문제가 아니라, 새 interval이 계속 들어오며 `insert -> overlap query`가 섞이면 `segment tree`보다 [Interval Tree](interval-tree.md)나 [Disjoint Interval Set](disjoint-interval-set.md)을 먼저 보는 편이 맞다.
`segment tree`라는 이름 때문에 ordered tree나 priority tree처럼 읽히면 먼저 [Segment Tree Is Not BST or Heap](segment-tree-not-bst-or-heap-bridge.md)에서 역할을 분리하고, 그다음 [Fenwick Tree vs Segment Tree](fenwick-vs-segment-tree.md)와 [Segment Tree Lazy Propagation](segment-tree-lazy-propagation.md)으로 내려가면 혼선이 적다.
연결성에서 매번 헷갈리면 아래 3줄만 먼저 잡아도 된다.
1. `같은 그룹인가?`, `갈 수 있나?`처럼 yes/no만 필요하면 union-find 쪽으로 먼저 간다.
2. `실제 경로 하나`를 보여 달라는 말이면 DFS/BFS로 `parent`를 남겨 복원한다. 이 경로가 shortest일 필요는 없다.
3. `가장 짧은/가장 싼 경로`를 묻는 순간 shortest-path 문제다. 알고리즘을 먼저 고르고 predecessor로 경로를 복원한다.
`같은 컴포넌트인가`, `connected components(연결 요소)가 몇 개인가`, `경로 하나를 복원하라`, `최단 경로를 구하라`가 한데 섞이면 [Connectivity Question Router](connectivity-question-router.md)에서 먼저 답의 모양을 `yes/no vs actual path vs minimum path`로 분리한 뒤 union-find / BFS / shortest-path 문서로 내려가면 된다. 이번 버전에는 `같은 팀이야?`, `이어져 있어?`, `연결요소가 몇 개야?`처럼 초급자가 실제로 던지는 질문 문장 pack도 함께 들어 있어 첫 분기 정확도를 바로 잡기 쉽다. 이때 yes/no에 `그룹 크기`, `전체 그룹 수`, `connected components(연결 요소) 수`가 붙으면 [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md)로 바로 넘기는 것이 가장 빠르다.
간선 추가만 있는 연결성은 [Union-Find Deep Dive](union-find-deep-dive.md)로 충분하지만, 삭제가 섞이는 순간은 [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md)에서 `왜 plain DSU가 안 되고 DSU rollback / dynamic connectivity로 넘어가는지`를 먼저 분리한 뒤 [DSU Rollback](../algorithm/dsu-rollback.md)로 이어 가면 된다.

- [Heap Variants](heap-variants.md) (`extract-min` 반복 루프 감각, heap vs ordered map 경계 한 줄)
- [Heap vs Priority Queue vs Ordered Map Beginner Bridge](heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md) (`top 1` 반복 추출 vs `floor/ceiling/subMap` 분기)
- [TreeMap Interval Entry Primer](treemap-interval-entry-primer.md) (`online interval insert` vs `offline interval merge` 첫 분기 표, `reservation/calendar/gap-check`를 `floorEntry`/`ceilingEntry`/`subMap`으로 읽는 입문, 초반에 neighbor-query 워크시트로 바로 점프 가능)
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
- [Connectivity Question Router](connectivity-question-router.md) (same-component yes/no, `같은 팀인지`/`연결요소 몇 개인지` 같은 beginner query phrase pack, `무가중치 BFS vs 가중치 Dijkstra` shortest-path handoff)
- [Union-Find Deep Dive](union-find-deep-dive.md) (same-component yes/no, BFS/DFS traversal boundary, edge-addition-only connectivity)
- [Deletion-Aware Connectivity Bridge](deletion-aware-connectivity-bridge.md) (edge deletion handoff, DSU rollback/dynamic connectivity threshold)
- [Union-Find Component Metadata Walkthrough](union-find-component-metadata-walkthrough.md) (component size, component count, redundant union guard, `size[find(x)]` 기준)

### 근사 집계와 압축 표현

exact bitmap 계열은 `Roaring Bitmap -> Roaring Container Transition Heuristics -> Chunk-Boundary Pathologies In Roaring -> Roaring Set-Op Result Heuristics -> Roaring Bitmap-Wide Lazy Union Pipeline -> Roaring Lazy Union And Repair Costs -> Roaring Intermediate Repair Path Guide -> Roaring Query Result Ordering Guide -> Roaring ANDNOT Result Heuristics -> Roaring runOptimize Timing Guide -> Roaring Run Formation and Row Ordering -> Roaring Production Profiling Checklist -> Roaring Run-Churn Observability Guide -> [playbook] Bitmap Locality Remediation Playbook -> Roaring Instrumentation Schema Examples -> [playbook] Roaring Bitmap Selection Playbook -> Compressed Bitmap Families: WAH, EWAH, CONCISE -> [playbook] Row-Ordering and Bitmap Compression Playbook -> Warehouse Sort-Key Co-Design for Bitmap Indexes -> Late-Arriving Rows and Bitmap Maintenance -> Bit-Sliced Bitmap Index -> Bit-Sliced Bitmap Sort-Key Sensitivity` 순서로 읽으면 chunk-local 임계값, 16-bit seam이 interval/range workload에서 언제 extra header와 extra run restart로 바뀌는지, set-op 결과 container 선택, per-container lazy union이 bitmap-level repair boundary로 어떻게 누적되는지, run-heavy warehouse bitmap에서 lazy OR savings가 exact count·serialize·`runOptimize()` 경계에서 언제 다시 비용으로 돌아오는지, temporary bitmap/run이 intermediate repair path에서 어떤 rewrite를 만드는지, selective predicate ordering과 shared intermediate reuse가 wide `OR`의 `repairAfterLazy()` debt를 언제 실질적으로 줄이는지, difference가 lazy repair 대신 direct demotion으로 끝나는 지점, bitmap-native set-op 뒤 언제 `runOptimize()`를 cold path handoff에 거는지, sorted ingest가 active chunk 수와 run 수를 어떻게 바꾸는지, profiling 뒤 row ordering·batch compaction·ID remapping·cold-path optimize를 어떤 순서로 써야 하는지, Java `RoaringBitmap` bridge와 CRoaring wrapper에서 chunk/run/transition metric schema를 어떻게 맞추고 Prometheus/OpenTelemetry 이름·adaptive sampling을 어떻게 나눌지, warehouse sort key가 dictionary encoding과 row-group reset 비용을 어떻게 함께 흔드는지, late data와 upsert/delete가 run locality를 언제 무너뜨려 compact나 rebuild 판단으로 이어지는지, 그리고 BSI slice가 sort-key prefix locality와 segment boundary에 따라 bit position별로 다르게 반응하는 지점까지 한 흐름으로 정리할 수 있다.

- [Bloom Filter](bloom-filter.md) (`exact membership` 정답 경로와 `approximate prefilter` 선필터를 초반 decision box로 분리)
- [Cuckoo Filter](cuckoo-filter.md) (`exact membership` 정답 경로와 `deletion 가능한 approximate prefilter` 선필터를 초반 decision box로 분리)
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
