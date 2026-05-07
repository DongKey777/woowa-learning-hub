---
schema_version: 3
title: Virtual Thread Migration Pinning ThreadLocal Pool Boundaries
concept_id: language/virtual-thread-migration-pinning
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 94
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- virtual-thread
- pinning
- context-propagation
aliases:
- Virtual Thread Migration Pinning ThreadLocal Pool Boundaries
- Loom migration checklist
- virtual thread pinning ThreadLocal pool
- carrier thread pinning migration
- MDC ThreadLocal virtual thread migration
- virtual thread 전환 체크리스트
symptoms:
- virtual thread 도입을 executor 교체로만 보고 pinning, ThreadLocal, MDC, downstream pool, timeout 경계를 함께 보지 않아
- DB connection pool이나 HTTP client max connection이 그대로인데 thread만 늘려 병목 위치가 pool wait로 이동한 것을 놓쳐
- synchronized I/O, native/JNI, ThreadLocal cleanup 문제를 JFR pinning과 context propagation 증거 없이 추정해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/virtual-threads-project-loom
- language/threadlocal-leaks-context-propagation
- language/jfr-loom-incident-signal-map
next_docs:
- language/virtual-thread-framework-integration
- language/jdbc-observability-under-virtual-threads
- language/connection-budget-alignment-after-loom
linked_paths:
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/jfr-loom-incident-signal-map.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/jdbc-observability-under-virtual-threads.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/threadlocal-leaks-context-propagation.md
- contents/language/java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
confusable_with:
- language/virtual-threads-project-loom
- language/virtual-thread-framework-integration
- language/jdbc-observability-under-virtual-threads
forbidden_neighbors: []
expected_queries:
- virtual thread migration에서 pinning ThreadLocal MDC datasource pool을 어떤 순서로 점검해야 해?
- Loom으로 executor만 바꾸면 왜 DB connection pool이나 HTTP client pool 병목이 그대로 남아?
- synchronized 안에서 blocking I/O를 하면 virtual thread pinning이 왜 문제가 돼?
- virtual thread 전환 후 ThreadLocal과 InheritableThreadLocal context propagation은 어떻게 다시 설계해야 해?
- JFR에서 VirtualThreadPinned Thread Park Socket Read를 보고 migration 위험을 어떻게 좁혀?
contextual_chunk_prefix: |
  이 문서는 Java virtual thread migration을 executor 교체가 아니라 pinning, ThreadLocal/MDC context, downstream pool, timeout/cancel boundary, JFR 관측을 함께 재설계하는 advanced playbook으로 다룬다.
  Loom migration, carrier pinning, ThreadLocal, MDC, connection pool bottleneck, JFR VirtualThreadPinned 질문이 본 문서에 매핑된다.
---
# Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy

> 한 줄 요약: virtual thread 전환은 executor 교체 작업이 아니라 runtime contract 재설계다. pinning, `ThreadLocal` 의존, JDBC/HTTP pool, MDC/context propagation, synchronized I/O를 함께 보지 않으면 "스레드는 가벼워졌는데 시스템은 그대로 답답한" 상태가 남는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [JFR Loom Incident Signal Map](./jfr-loom-incident-signal-map.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)

> retrieval-anchor-keywords: virtual thread migration, Loom adoption, pinning, carrier thread, ThreadLocal migration, MDC propagation, connection pool bottleneck, synchronized I/O, blocking style migration, per task executor, virtual thread readiness, Spring integration, JDBC, HttpClient, servlet timeout boundary, request cancellation propagation, async timeout, JDBC observability under virtual threads, long transaction diagnosis, lock contention after loom, JFR Loom incident map, Java Thread Park, VirtualThreadPinned, Socket Read, Java Monitor Blocked

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

virtual thread 전환의 진짜 질문은 "스레드 수를 늘릴 수 있나"가 아니다.

- blocking이 정말 병목이었나
- pinning 구간이 어디 있나
- 기존 `ThreadLocal`/MDC는 어떻게 다룰 건가
- downstream pool과 timeout이 그대로면 어디서 막히나

즉 virtual thread migration은 thread API 교체보다 boundary audit에 가깝다.

## 깊이 들어가기

### 1. carrier thread를 아끼는 것과 downstream을 확장하는 것은 다르다

virtual thread는 waiting 동안 carrier를 덜 점유하게 도와줄 수 있다.  
하지만 다음 자원은 그대로일 수 있다.

- DB connection pool
- HTTP client max connections
- rate limiter
- remote server concurrency

즉 thread bottleneck이 pool bottleneck으로 옮겨갈 뿐일 수 있다.

### 2. `ThreadLocal`/MDC 의존 코드는 migration 검토 대상이다

기존 platform thread + pool 모델에서 돌아가던 ambient context가  
virtual thread 전환 후에도 "그냥 될 것"이라 기대하면 위험하다.

특히 봐야 할 것:

- request-scoped context cleanup
- `InheritableThreadLocal` 가정
- logger MDC restore
- framework task decorator 의존

### 3. pinning은 migration에서 가장 비싼 surprise다

virtual thread가 carrier에 묶이는 대표 구간:

- `synchronized` 안의 blocking I/O
- 일부 native/JNI
- lock과 I/O가 섞인 큰 임계영역

즉 "blocking 코드를 유지할 수 있다"는 말은  
"아무 lock 구조나 그대로 둬도 된다"는 뜻이 아니다.

### 4. executor 경계와 API boundary를 같이 바꾸는 편이 안전하다

마이그레이션은 보통 한 번에 전체가 아니라 경계별로 가는 편이 낫다.

- HTTP layer
- background worker
- batch job
- async client wrapper

각 경계마다:

- blocking 비율
- context propagation
- timeout/cancel
- downstream pool

을 같이 점검해야 한다.

### 5. 관측은 thread count보다 pinning/park/queue/pool wait를 본다

JFR/JMC에서 virtual thread migration 후 먼저 볼 것:

- thread parking
- pinning
- socket read
- connection pool wait
- queue backlog

pool wait, long transaction, lock contention을 JDBC 경로에서 더 촘촘히 나누는 절차는 [JDBC Observability Under Virtual Threads](./jdbc-observability-under-virtual-threads.md)에서 별도로 정리한다.
`Thread Park`/`VirtualThreadPinned`/`Socket Read`/`Java Monitor Blocked` 조합을 incident fingerprint로 읽는 표는 [JFR Loom Incident Signal Map](./jfr-loom-incident-signal-map.md)에서 바로 참고할 수 있다.

즉 "virtual thread 개수"보다 wait reason이 더 중요하다.

## 실전 시나리오

### 시나리오 1: servlet executor를 virtual thread per task로 바꿨다

throughput은 나아졌지만 DB pool이 바로 포화된다.  
thread 문제를 줄였더니 원래 숨어 있던 pool 병목이 드러난 것이다.

### 시나리오 2: `synchronized` 캐시 갱신 안에서 외부 API를 부른다

기존에도 안 좋았지만, virtual thread에선 pinning으로 이득을 더 깎아먹는다.

### 시나리오 3: traceId가 일부 비동기 경로에서 사라진다

virtual thread 전환이 context propagation 문제를 자동 해결해주진 않는다.  
오히려 기존 `InheritableThreadLocal` 가정이 더 분명히 깨질 수 있다.

## 코드로 보기

### 1. per-task executor 진입점

```java
try (var executor = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(this::handleRequest);
}
```

### 2. pinning 냄새

```java
public synchronized Response load() {
    return blockingClient.call();
}
```

### 3. migration checklist 감각

```java
// 1. blocking path인가
// 2. lock 안에서 I/O 하나
// 3. context propagation이 ambient state에 의존하나
// 4. downstream pool이 진짜 병목인가
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| virtual thread 빠른 도입 | blocking 코드 유지가 쉽다 | pinning과 downstream pool 병목을 따로 봐야 한다 |
| selective migration | 위험을 경계별로 줄일 수 있다 | 운영/설정이 이중화될 수 있다 |
| 기존 pool 유지 | 예측 가능하다 | thread exhaustion 문제를 그대로 안고 갈 수 있다 |

핵심은 migration 성공 여부를 thread API가 아니라 **병목 위치가 어디로 이동했는가**로 판단하는 것이다.

## 꼬리질문

> Q: virtual thread로 바꾸면 DB 병목도 해결되나요?
> 핵심: 아니다. carrier 점유는 줄어들 수 있지만 connection pool과 downstream 처리량은 별개다.

> Q: migration에서 제일 먼저 뭘 보나요?
> 핵심: pinning, ThreadLocal/MDC 의존, downstream pool wait를 먼저 본다.

> Q: virtual thread면 `ThreadLocal` 문제도 끝인가요?
> 핵심: 아니다. lifecycle과 propagation 전략은 여전히 설계해야 한다.

## 한 줄 정리

virtual thread migration은 스레드 수를 바꾸는 작업이 아니라 pinning, context, pool 병목, cancellation 경계를 다시 정리하는 작업이다.
