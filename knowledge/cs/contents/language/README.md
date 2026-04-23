# Language

**난이도: 🔴 Advanced**

> 이 README는 language category `navigator`다. 언어별 `primer`와 Java 중심 `deep dive catalog`를 묶고, 학습 순서용 `survey`는 루트 roadmap으로 보낸다.

> retrieval-anchor-keywords: language readme, language navigator, language primer, language deep dive catalog, language survey, language roadmap, language playbook, java playbook, java runtime playbook, java diagnostics, java troubleshooting guide, java basics, java internals, java runtime catalog, java concurrency catalog, java async catalog, async quick links, concurrency quick links, executor cluster, executor common pool, common-pool cluster, completablefuture, cancellation propagation, cancellation context propagation, context propagation cluster, thread dump interpretation, jcmd cheat sheet, async-profiler vs JFR, flamegraph, safepoint diagnostics, jcstress, happens-before verification, common pool, executor sizing, structured concurrency, structured concurrency cluster, virtual threads, loom cluster, scoped value, threadlocal propagation, partial success fan-in, remote bulkhead metrics, bulkhead observability, permit contention, retry storm, upstream saturation, degraded response contract, aggregate error report, java serialization catalog, java boundary design, jvm primer, JFR Loom incident map, virtual thread diagnostics, JDBC cancel confirmation, DB-side cancel verification, java beginner oop, java class object primer, java package basics, java import basics, java package import boundary basics, java source file structure basics, java one public class per file, java public class file name rule, java top level class file convention, java package private boundary basics, java same package no import, java default package avoid, java wildcard import subpackage, java access modifier basics, java member model basics, instance vs static member basics, java instance vs static methods, java static utility method basics, java static factory method basics, java factory method basics, java of from valueOf basics, final field method class basics, java method basics, java constructor basics, java constructor chaining basics, java initialization order basics, java this super basics, java instance initializer block basics, java static initializer block basics, java parameter return type basics, java parameter passing basics, java pass by value basics, java reference type pass by value, java parameter reassignment basics, java side effect basics, java object state tracking, java aliasing basics, java method overloading basics, java inheritance basics, java extends basics, java overriding basics, java @Override basics, java dynamic dispatch basics, java overloading vs overriding, java overload override difference, java compile time vs runtime method selection, java parent reference child object method call, java object state change basics, interface vs abstract class basics, java equality basics, java identity basics, java string comparison basics, java hashCode basics, java record equality basics, java record equals hashCode, record component equality, record value object equality, immutable value object basics, mutable entity equality hazard, java array equality basics, java arrays equals, java arrays deepEquals, java nested array comparison, java multidimensional array equality, java array debug printing basics, java array print weird output, java array toString basics, java array deepToString basics, java nested array reference-like output, java array default toString, java `[I@` output meaning, java `[Ljava.lang.String;@` output meaning, java array copy basics, java array clone basics, java array assignment vs clone, java Arrays.copyOf basics, java shallow copy deep copy array, java nested array copy, java multidimensional array copy, java Arrays.sort basics, java Arrays.binarySearch basics, java array sorting basics, java array searching basics, java binarySearch insertion point, java binarySearch same comparator, java comparable basics, java comparator basics, natural ordering basics, custom comparator basics, compareTo basics, HashSet duplicate rule, TreeSet duplicate rule, HashSet vs TreeSet duplicate semantics, equals hashCode vs compare == 0, TreeSet compareTo 0 duplicate, TreeSet comparator equals consistency, TreeMap comparator equals consistency, sorted set duplicate surprise, coroutine basics, c++ basics, language index, what to read next

## 빠른 탐색

- 학습 순서 `survey`가 먼저 필요하면:
  - [루트 README](../../README.md)
  - [Advanced Backend Roadmap](../../ADVANCED-BACKEND-ROADMAP.md)
- Java `primer`부터 읽고 싶다면:
  - [자바 언어의 구조와 기본 문법](./java/java-language-basics.md)
  - [Java package와 import 경계 입문](./java/java-package-import-boundary-basics.md)
  - [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md)
  - [Java 메서드와 생성자 실전 입문](./java/java-methods-constructors-practice-primer.md)
  - [Java parameter 전달, pass-by-value, side effect 입문](./java/java-parameter-passing-pass-by-value-side-effects-primer.md)
  - [Java 오버로딩 vs 오버라이딩 입문](./java/java-overloading-vs-overriding-beginner-primer.md)
  - [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md)
  - [Java 생성자와 초기화 순서 입문](./java/java-constructors-initialization-order-basics.md)
  - [Java 접근 제한자와 멤버 모델 입문](./java/java-access-modifiers-member-model-basics.md)
  - [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java/java-instance-static-factory-methods-primer.md)
  - [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)
  - [Record and Value Object Equality](./java/record-value-object-equality-basics.md)
  - [Java Array Equality Basics](./java/java-array-equality-basics.md)
  - [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md)
  - [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md)
  - [Comparable and Comparator Basics](./java/java-comparable-comparator-basics.md)
  - [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md)
  - [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md)
  - [객체지향 핵심 원리](./java/object-oriented-core-principles.md)
  - [불변 객체와 방어적 복사 입문](./java/java-immutable-object-basics.md)
  - [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md)
  - [Java 예외 처리 기초](./java/java-exception-handling-basics.md)
  - [Java 제네릭 입문](./java/java-generics-basics.md)
  - [Java 스트림과 람다 입문](./java/java-stream-lambda-basics.md)
  - [Java String 기초](./java/java-string-basics.md)
  - [Java enum 기초](./java/java-enum-basics.md)
  - [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md)
  - [Java Optional 입문](./java/java-optional-basics.md)
  - [Java 스레드와 동기화 기초](./java/java-thread-basics.md)
  - [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md)
- Java `deep dive catalog`에서 bucket을 바로 고르려면:
  - [Java Runtime and Diagnostics](#java-runtime-and-diagnostics)
  - [Java Concurrency and Async](#java-concurrency-and-async)
  - [Java Serialization and Payload Contracts](#java-serialization-and-payload-contracts)
  - [Java Language and Boundary Design](#java-language-and-boundary-design)
- Java concurrency / async `subcluster`로 바로 들어가려면:
  - [Executor / Common Pool Cluster](#java-concurrency-executor--common-pool-cluster)
  - [Cancellation / Context Propagation Cluster](#java-concurrency-cancellation--context-propagation-cluster)
  - [Loom / Structured Concurrency Cluster](#java-concurrency-loom--structured-concurrency-cluster)
- 운영/진단 절차가 먼저 필요한 `[playbook]`으로 가려면:
  - `[playbook]` [JFR, JMC Performance Playbook](./java/jfr-jmc-performance-playbook.md)
  - `[playbook]` [OOM Heap Dump Playbook](./java/oom-heap-dump-playbook.md)
  - `[playbook]` [ClassLoader Memory Leak Playbook](./java/classloader-memory-leak-playbook.md)
  - `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- Java runtime symptom으로 바로 들어가려면:
  - [Thread Dump State Interpretation](./java/thread-dump-state-interpretation.md)
  - [`jcmd` Diagnostic Command Cheat Sheet](./java/jcmd-diagnostic-command-cheatsheet.md)
  - [Async-profiler vs JFR](./java/async-profiler-vs-jfr-comparison.md)
  - [Safepoint and Stop-the-World Diagnostics](./java/safepoint-stop-the-world-diagnostics.md)
- JMM / concurrency 검증 도구로 바로 들어가려면:
  - [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)
- coroutine / other-language `primer` entrypoint로 가려면:
  - [코루틴](./coroutine.md)
  - 아래 `C++ primer` 구간
- cross-category bridge로 확장하려면:
  - 아래 `교차 카테고리 브리지` 구간
- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## Java

Java 구간은 `primer -> deep dive catalog -> cross-category bridge` 순서로 읽도록 정리했다.

### Java primer

- [자바 언어의 구조와 기본 문법](./java/java-language-basics.md)
- [Java package와 import 경계 입문](./java/java-package-import-boundary-basics.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md)
- [Java 메서드와 생성자 실전 입문](./java/java-methods-constructors-practice-primer.md)
- [Java parameter 전달, pass-by-value, side effect 입문](./java/java-parameter-passing-pass-by-value-side-effects-primer.md)
- [Java 오버로딩 vs 오버라이딩 입문](./java/java-overloading-vs-overriding-beginner-primer.md)
- [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md)
- [Java 생성자와 초기화 순서 입문](./java/java-constructors-initialization-order-basics.md)
- [Java 접근 제한자와 멤버 모델 입문](./java/java-access-modifiers-member-model-basics.md)
- [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java/java-instance-static-factory-methods-primer.md)
- [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)
- [Record and Value Object Equality](./java/record-value-object-equality-basics.md)
- [Java Array Equality Basics](./java/java-array-equality-basics.md)
- [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md)
- [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md)
- [Comparable and Comparator Basics](./java/java-comparable-comparator-basics.md)
- [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md)
- [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md)
- [객체지향 핵심 원리](./java/object-oriented-core-principles.md)
- [불변 객체와 방어적 복사 입문](./java/java-immutable-object-basics.md)
- [불변 객체와 방어적 복사](./java/immutable-objects-and-defensive-copying.md)
- [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md)
- [추상 클래스 vs 인터페이스](./java/abstract-class-vs-interface.md)
- [Java 예외 처리 기초](./java/java-exception-handling-basics.md)
- [Java 제네릭 입문](./java/java-generics-basics.md)
- [Java 스트림과 람다 입문](./java/java-stream-lambda-basics.md)
- [Java String 기초](./java/java-string-basics.md)
- [Java enum 기초](./java/java-enum-basics.md)
- [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md)
- [Java Optional 입문](./java/java-optional-basics.md)
- [Java 스레드와 동기화 기초](./java/java-thread-basics.md)
- [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md)
- [Java 동시성 유틸리티](./java/java-concurrency-utilities.md)
- [ClassLoader, Exception 경계, 객체 계약](./java/classloader-exception-boundaries-object-contracts.md)
- [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./java/optional-stream-immutable-collections-memory-leak-patterns.md)

### Java deep dive catalog

긴 목록은 아래 네 bucket으로 쪼개서 찾기 쉽게 유지한다.
mixed catalog에서 `[playbook]` 라벨은 step-oriented diagnostics / troubleshooting entrypoint라는 뜻이고, 라벨이 없는 항목은 개념/경계 중심 `deep dive`다.

#### Java Runtime and Diagnostics

- [G1 GC vs ZGC](./java/g1-vs-zgc.md)
- [JIT Warmup and Deoptimization](./java/jit-warmup-deoptimization.md)
- `[playbook]` [JFR, JMC Performance Playbook](./java/jfr-jmc-performance-playbook.md)
- [JFR Event Interpretation](./java/jfr-event-interpretation.md)
- [Thread Dump State Interpretation](./java/thread-dump-state-interpretation.md)
- [`jcmd` Diagnostic Command Cheat Sheet](./java/jcmd-diagnostic-command-cheatsheet.md)
- [Async-profiler vs JFR](./java/async-profiler-vs-jfr-comparison.md)
- [Safepoint and Stop-the-World Diagnostics](./java/safepoint-stop-the-world-diagnostics.md)
- [Safepoint Polling Mechanics](./java/safepoint-polling-mechanics.md)
- `[playbook]` [OOM Heap Dump Playbook](./java/oom-heap-dump-playbook.md)
- [Direct Buffer, Off-Heap, Native Memory Troubleshooting](./java/direct-buffer-offheap-memory-troubleshooting.md)
- `[playbook]` [ClassLoader Memory Leak Playbook](./java/classloader-memory-leak-playbook.md)
- [Java Binary Compatibility and Runtime Linkage Errors](./java/java-binary-compatibility-linkage-errors.md)
- [Escape Analysis, Stack Allocation, Benchmarking, and Object Reuse Misconceptions](./java/escape-analysis-stack-allocation-benchmark-misconceptions.md)
- [Java Collections 성능 감각](./java/collections-performance.md)

#### Java Concurrency and Async

긴 bucket이므로 아래 세 `subcluster` quick link를 먼저 둔다. executor saturation / common pool 공유, cancellation / context handoff, Loom migration / structured fan-out처럼 질문 모양이 갈릴 때 바로 내려가기 위한 entrypoint다.

<a id="java-concurrency-executor--common-pool-cluster"></a>
##### Executor / Common Pool Cluster

executor saturation, `ForkJoinPool` 공유, `CompletableFuture` default executor, scheduler hop, partial fan-in backlog를 같이 따라갈 때 쓰는 subcluster다.

- [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md)
- [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md)
- [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md)
- [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
- [Partial Success Fan-in Patterns](./java/partial-success-fan-in-patterns.md)

<a id="java-concurrency-cancellation--context-propagation-cluster"></a>
##### Cancellation / Context Propagation Cluster

interrupt, cooperative cancellation, `ThreadLocal` leakage, `ScopedValue` handoff, timeout-to-deadline propagation과 async cleanup ownership을 함께 볼 때 쓰는 subcluster다.

- `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md)
- [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)
- [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
- [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md)
- [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md)

<a id="java-concurrency-loom--structured-concurrency-cluster"></a>
##### Loom / Structured Concurrency Cluster

virtual-thread adoption, pinning, `ScopedValue`, structured fan-out, framework boundary, Loom incident signal을 묶어 찾을 때 쓰는 subcluster다.

- [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md)
- [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
- [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md)
- [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md)
- [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md)
- [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md)

- [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
- [Java Memory Model, happens-before, volatile, final](./java-memory-model-happens-before-volatile-final.md)
- [VarHandle, Unsafe, Atomics](./java/varhandle-unsafe-atomics.md)
- [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)
- [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./java/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
- `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./java/concurrenthashmap-compound-actions-hot-key-contention.md)
- [`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs](./java/concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs.md)
- [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
- [ABA Problem, `AtomicStampedReference`, and `AtomicMarkableReference`](./java/aba-problem-atomicstampedreference-markable-reference.md)
- [`CopyOnWriteArrayList` Snapshot Iteration and Write Amplification](./java/copyonwritearraylist-snapshot-iteration-write-amplification.md)
- [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./java/wait-notify-condition-spurious-wakeup-lost-signal.md)
- [`StampedLock` Optimistic Read and Conversion Pitfalls](./java/stampedlock-optimistic-read-conversion-pitfalls.md)
- [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./java/locksupport-park-unpark-permit-semantics.md)
- [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md)
- [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)
- [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md)
- [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md)
- [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md)
- [`CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards](./java/completablefuture-allof-join-timeout-exception-handling-hazards.md)
- [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
- [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md)
- [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
- [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md)
- [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md)
- [Idempotency Keys and Safe HTTP Retries](./java/httpclient-idempotency-keys-safe-http-retries.md)
- [Partial Success Fan-in Patterns](./java/partial-success-fan-in-patterns.md)
- [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md)
- [Virtual-Thread MVC Async Executor Boundaries](./java/virtual-thread-mvc-async-executor-boundaries.md)
- [Connection Budget Alignment After Loom](./java/connection-budget-alignment-after-loom.md)
- [Remote Bulkhead Metrics Under Virtual Threads](./java/remote-bulkhead-metrics-under-virtual-threads.md)
- [Virtual-Thread JDBC Cancel Semantics](./java/virtual-thread-jdbc-cancel-semantics.md)
- `[playbook]` [DB-Side Cancel Confirmation Playbook](./java/jdbc-db-side-cancel-confirmation-playbook.md)
- [Spring JDBC Timeout Propagation Boundaries](./java/spring-jdbc-timeout-propagation-boundaries.md)
- [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
- [JDBC Observability Under Virtual Threads](./java/jdbc-observability-under-virtual-threads.md)
- [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md)
- [Virtual Thread vs Reactive DB Observability](./java/virtual-thread-vs-reactive-db-observability.md)
- [Servlet `REQUEST` / `ASYNC` / `ERROR` Redispatch Ordering for Filters and Interceptors](./java/servlet-async-redispatch-filter-interceptor-ordering.md)
- [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
- [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md)
- [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./java/streaming-response-abort-surfaces-servlet-virtual-threads.md)
- [JDBC Cursor Cleanup on Download Abort](./java/jdbc-cursor-cleanup-download-abort.md)
- [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
- [SSE `Last-Event-ID`, Replay Window, and Reconnect Ownership With `SseEmitter`](./java/sse-last-event-id-replay-reconnect-ownership.md)
- [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md)

#### Java Serialization and Payload Contracts

- [Primitive vs Wrapper Fields in JSON Payload Semantics](./java/primitive-vs-wrapper-fields-json-payload-semantics.md)
- [Empty String, Blank, `null`, and Missing Payload Semantics](./java/empty-string-blank-null-missing-payload-semantics.md)
- [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./java/floating-point-precision-nan-infinity-serialization-pitfalls.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./java/bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [Java IO, NIO, Serialization, JSON Mapping](./java/io-nio-serialization.md)
- [Charset, UTF-8 BOM, Malformed Input, and Decoder Policy](./java/charset-utf8-bom-malformed-input-decoder-policy.md)
- [Serialization Compatibility, `serialVersionUID`, and Evolution Strategy](./java/serialization-compatibility-serial-version-uid.md)
- [Serialization Proxy Pattern and Invariant Preservation](./java/serialization-proxy-pattern-invariant-preservation.md)
- [`serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches](./java/serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)
- [Enum Persistence, JSON, and Unknown Value Evolution](./java/enum-persistence-json-unknown-value-evolution.md)
- [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./java/json-null-missing-unknown-field-schema-evolution.md)
- [Record Serialization Evolution](./java/record-serialization-evolution.md)
- [Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility](./java/record-sealed-hierarchy-evolution-pattern-matching-compatibility.md)

#### Java Language and Boundary Design

- [Value Object Invariants, Canonicalization, and Boundary Design](./java/value-object-invariants-canonicalization-boundary-design.md)
- [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)
- [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md)
- [Record and Value Object Equality](./java/record-value-object-equality-basics.md)
- [Java Array Equality Basics](./java/java-array-equality-basics.md)
- [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md)
- [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md)
- [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md)
- [equals, hashCode, Comparable 계약](./java-equals-hashcode-comparable-contracts.md)
- [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./java/autoboxing-integercache-null-unboxing-pitfalls.md)
- [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
- [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./java/biginteger-unsigned-parsing-boundaries.md)
- [`BigInteger` Parser Radix, Leading Zero, Sign, and Boundary Contracts](./java/biginteger-radix-leading-zero-sign-policies.md)
- [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./java/parser-overflow-boundaries-parseint-parselong-tointexact.md)
- [Saturating Arithmetic, Clamping, and Domain Contracts](./java/saturating-arithmetic-clamping-domain-contracts.md)
- [`BigDecimal` `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
- [Reflection, Generics, Annotations](./java/reflection-generics-annotations.md)
- [Generic Type Erasure Workarounds](./java/generic-type-erasure-workarounds.md)
- [Reflection 비용과 대안](./java/reflection-cost-and-alternatives.md)
- [Records, Sealed Classes, Pattern Matching](./java/records-sealed-pattern-matching.md)
- [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java/java-time-instant-localdatetime-boundaries.md)
- [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./java/locale-root-case-mapping-unicode-normalization.md)
- [Annotation Processing](./java/annotation-processing.md)

### 교차 카테고리 브리지

- 이벤트 계약 진화와 replay 호환성은 [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./java/json-null-missing-unknown-field-schema-evolution.md), [Design Pattern: Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md), [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)을 묶어 보면 좋다.
- 객체 계약과 경계 설계는 [ClassLoader, Exception 경계, 객체 계약](./java/classloader-exception-boundaries-object-contracts.md), [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md), [Database: Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md)으로 이어 보면 더 선명하다.
- JVM/동시성 감각은 [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md), [Java 동시성 유틸리티](./java/java-concurrency-utilities.md), `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)의 장애 해석 감각과도 연결된다.
- 숫자 parsing/canonicalization 경계는 [`BigInteger` Parser Radix, Leading Zero, Sign, and Boundary Contracts](./java/biginteger-radix-leading-zero-sign-policies.md), [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./java/parser-overflow-boundaries-parseint-parselong-tointexact.md), [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./java/biginteger-unsigned-parsing-boundaries.md), [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)를 함께 보면 `문자열 문법 -> parse -> exact/narrowing -> domain max` 흐름이 한 번에 연결된다.
- 비동기 orchestration 감각은 [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md), [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md), [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md), [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md), [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md), [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)를 함께 보면 common pool 공유, timer hop, retry/backoff, cancellation, `CallerRunsPolicy`, context 전파가 한 그림으로 묶인다.
- outbound `POST` retry와 duplicate suppression 감각은 [Idempotency Keys and Safe HTTP Retries](./java/httpclient-idempotency-keys-safe-http-retries.md), [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md), [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md), [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)를 함께 보면 `transport retry 가능성 -> request fingerprint -> dedup window -> response replay` 흐름이 한 번에 연결된다.
- virtual thread 도입 감각은 [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md), [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md), [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md), [Remote Bulkhead Metrics Under Virtual Threads](./java/remote-bulkhead-metrics-under-virtual-threads.md), [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md), [Virtual-Thread MVC Async Executor Boundaries](./java/virtual-thread-mvc-async-executor-boundaries.md), [Virtual-Thread JDBC Cancel Semantics](./java/virtual-thread-jdbc-cancel-semantics.md), [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md), [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md), [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md), [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md), [Spring `@Transactional` and `@Async` Composition Traps](../spring/spring-transactional-async-composition-traps.md), [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](../spring/spring-async-context-propagation-restclient-http-interface-clients.md)를 함께 보면 request thread, MVC async executor, direct emitter producer, servlet request lifetime, detached task, structured task scope, transaction `ThreadLocal`, async timeout을 parent deadline으로 삼는 방법, outbound HTTP cancel ownership, JDBC query cancel ownership, remote fan-out budget과 permit contention 관측이 같은 경계 문제로 묶인다.
- 스트리밍 abort와 late write failure 해석은 [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./java/streaming-response-abort-surfaces-servlet-virtual-threads.md), [JDBC Cursor Cleanup on Download Abort](./java/jdbc-cursor-cleanup-download-abort.md), [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md), [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md), [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md), [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)을 함께 보면 `first byte commit -> 다음 write/flush에서 disconnect 관측 -> fetch-size cursor ownership -> statement cancel/rollback -> late write suppression` 흐름이 한 번에 연결된다.
- SSE resume/reconnect ownership 감각은 [SSE `Last-Event-ID`, Replay Window, and Reconnect Ownership With `SseEmitter`](./java/sse-last-event-id-replay-reconnect-ownership.md), [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](../spring/spring-sse-replay-buffer-last-event-id-recovery-patterns.md), [Spring SSE Disconnect Observability Patterns](../spring/spring-sse-disconnect-observability-patterns.md), [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)을 함께 보면 `logical stream cursor -> replay window -> high-water-mark handoff -> reconnect storm -> old emitter cleanup ownership` 흐름이 한 번에 연결된다.
- virtual thread 이후 JDBC 병목 관측은 [JDBC Observability Under Virtual Threads](./java/jdbc-observability-under-virtual-threads.md), [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md), [HikariCP 튜닝](../database/hikari-connection-pool-tuning.md), `[playbook]` [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)를 함께 보면 `pool wait -> stuck socket/read -> connection churn -> DB lock wait` 흐름까지 한 번에 연결된다.
- virtual thread JDBC와 reactive DB의 장애 해석 차이는 [Virtual Thread vs Reactive DB Observability](./java/virtual-thread-vs-reactive-db-observability.md), [Spring WebFlux vs MVC](../spring/spring-webflux-vs-mvc.md), [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)를 함께 보면 `thread timeline vs signal timeline`, `pool wait vs operator backlog`, `caller 예외 vs stream cancel` 차이가 한 그림으로 연결된다.
- 큐 포화와 handoff 계약은 [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md), [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md), [Bounded MPMC Queue](../data-structure/bounded-mpmc-queue.md)를 함께 보면 `offer`/`put`/`transfer`, `SynchronousQueue`, bounded ring backpressure가 같은 축으로 연결된다.

## C++ primer

이 구간은 C++ 기초/중급 `primer` entrypoint다. 세부 구현 trade-off는 다른 카테고리 deep dive와 함께 확장해서 읽는 편이 좋다.

- [C++ STL](./c++/STL.md)
- [Modern C++](./c++/moderncpp.md)
- [멀티스레드 프로그래밍](./c++/multithread-programming.md)
