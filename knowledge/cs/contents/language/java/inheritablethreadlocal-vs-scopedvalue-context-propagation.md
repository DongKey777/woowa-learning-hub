---
schema_version: 3
title: InheritableThreadLocal vs ScopedValue Context Propagation Boundaries
concept_id: language/inheritablethreadlocal-vs-scopedvalue-context-propagation
canonical: true
category: language
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids:
- missions/racingcar
- missions/payment
review_feedback_tags:
- context-propagation
- threadlocal
- virtual-thread
aliases:
- InheritableThreadLocal vs ScopedValue
- ScopedValue context propagation boundary
- InheritableThreadLocal executor propagation
- virtual thread context propagation Java
- thread-bound context vs scope-bound context
- 자바 ThreadLocal ScopedValue 컨텍스트 전파 차이
symptoms:
- InheritableThreadLocal이 executor task마다 현재 부모 값을 자동으로 전파한다고 기대해 pool worker 생성 시점 snapshot 문제를 놓쳐
- request id나 tenant id 같은 immutable context를 mutable ThreadLocal로 계속 덮어써 nested call restore 문제를 만들고도 원인을 찾지 못해
- virtual thread를 쓰면 context propagation 의미가 자동으로 해결된다고 생각해 scope lifetime과 thread lifetime을 구분하지 못해
intents:
- comparison
- design
- troubleshooting
prerequisites:
- language/threadlocal-leaks-context-propagation
- language/structured-concurrency-scopedvalue
- language/virtual-threads-project-loom
next_docs:
- language/virtual-thread-migration-pinning
- language/structured-concurrency-scopedvalue
- language/threadlocal-leaks-context-propagation
linked_paths:
- contents/language/java/threadlocal-leaks-context-propagation.md
- contents/language/java/structured-concurrency-scopedvalue.md
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
confusable_with:
- language/threadlocal-leaks-context-propagation
- language/structured-concurrency-scopedvalue
- language/virtual-thread-migration-pinning
forbidden_neighbors: []
expected_queries:
- InheritableThreadLocal과 ScopedValue는 context propagation 모델이 어떻게 달라?
- executor pool에서 InheritableThreadLocal 값이 기대처럼 안 넘어가는 이유를 설명해줘
- Java ScopedValue가 ThreadLocal 대안으로 적합한 경우와 아닌 경우를 비교해줘
- virtual thread에서 request id 같은 context를 어떤 방식으로 전달하는 게 안전해?
- thread-bound mutable state와 scope-bound read-only context를 어떻게 구분해야 해?
contextual_chunk_prefix: |
  이 문서는 InheritableThreadLocal의 child thread creation snapshot 모델과 ScopedValue의 scope-bound read-only context 모델을 비교하는 advanced chooser다.
  InheritableThreadLocal executor propagation, ScopedValue, ThreadLocal context leak, virtual thread context propagation 질문이 본 문서에 매핑된다.
---
# `InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries

> 한 줄 요약: `InheritableThreadLocal`은 thread 생성 시점 복사 모델이고, `ScopedValue`는 scope-bound 읽기 전용 context 모델이다. 둘을 같은 "자동 전파"로 이해하면 executor, virtual thread, structured concurrency 경계에서 기대와 실제가 어긋난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [Structured Concurrency and `ScopedValue`](./structured-concurrency-scopedvalue.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: InheritableThreadLocal, ScopedValue, context propagation, child thread copy, scope-bound context, thread-bound context, virtual thread context, structured concurrency context, immutable context, executor propagation

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

둘 다 "context를 옮긴다"처럼 보이지만 모델이 다르다.

- `InheritableThreadLocal`: 새 child thread를 만들 때 부모 값을 복사
- `ScopedValue`: 특정 코드 scope 안에서만 읽기 전용 값 노출

즉 차이는 thread inheritance와 scope binding이다.

## 깊이 들어가기

### 1. `InheritableThreadLocal`은 생성 시점 복사다

핵심은 "inherit"가 실행 중 전파가 아니라 생성 시점 snapshot이라는 점이다.

- thread 생성 후 부모 값 변경은 자동 반영되지 않는다
- 이미 만들어진 pool worker에는 기대한 대로 안 들어간다
- mutable 객체를 넣으면 참조 공유 오해가 생길 수 있다

즉 이 도구는 child thread bootstrap용에 가깝고, executor task propagation 만능키가 아니다.

### 2. `ScopedValue`는 scope-bound 읽기 전용 모델이다

`ScopedValue`는 thread에 state를 붙이는 대신  
특정 코드 scope 동안만 값을 바인딩한다.

장점:

- 읽기 전용이라 실수로 덮어쓰기 어렵다
- structured concurrency와 개념이 맞는다
- "누가 언제까지 이 값을 볼 수 있나"가 더 선명하다

즉 ThreadLocal-like storage보다 lexical lifetime에 가깝다.

### 3. writeable ambient state와 read-only ambient context는 다른 문제다

`ThreadLocal`/`InheritableThreadLocal`은 mutable ambient state를 만들기 쉽다.  
반면 `ScopedValue`는 읽기 전용 context를 더 잘 표현한다.

따라서 용도가 다르다.

- MDC 같이 mutation이 섞이는 임시 호환 경로
- request id, tenant id 같은 immutable context

를 같은 방식으로 다루면 안 된다.

### 4. structured concurrency에선 `ScopedValue`가 더 자연스럽다

scope 안에서 하위 task를 만들고, 그 scope lifetime 동안만 context를 공유하는 모델은  
`ScopedValue`와 잘 맞는다.

반대로 `InheritableThreadLocal`은 "child thread 생성" 모델에 더 기대므로,  
task scope와 의미 축이 다르다.

### 5. virtual thread 도입이 둘의 차이를 더 드러낸다

virtual thread는 생성 비용이 낮아 `InheritableThreadLocal`이 예전보다 "동작하는 것처럼" 보일 수 있다.  
하지만 여전히 질문은 남는다.

- 복사가 필요한가
- 읽기 전용이면 충분한가
- context lifetime이 thread 수명과 일치하는가

즉 virtual thread가 context semantics를 해결해주진 않는다.

## 실전 시나리오

### 시나리오 1: pool 기반 executor에 `InheritableThreadLocal`을 기대한다

worker가 이미 떠 있으면 값이 안 들어가거나 오래된 값을 볼 수 있다.  
문제는 API가 아니라 생성 시점 모델 오해다.

### 시나리오 2: request id는 immutable인데 `ThreadLocal`로 계속 덮어쓴다

실수로 nested call이 값을 바꾸고 restore를 잊으면 문맥이 흐려진다.  
이 경우는 `ScopedValue`가 더 자연스러울 수 있다.

### 시나리오 3: structured concurrency에서 하위 작업에 동일 context를 주고 싶다

scope lifetime과 함께 움직이는 읽기 전용 context라면 `ScopedValue`가 더 잘 맞는다.

## 코드로 보기

### 1. `InheritableThreadLocal` 감각

```java
private static final InheritableThreadLocal<String> REQUEST_ID = new InheritableThreadLocal<>();
```

이 값은 child thread 생성 시점 복사 모델을 따른다.

### 2. `ScopedValue` 감각

```java
// 특정 scope 동안만 읽기 전용 context를 노출한다.
```

### 3. 선택 질문

```java
// "이 값이 thread에 붙어야 하나?"
// 보다
// "이 값이 어떤 scope 동안만 보여야 하나?"
// 를 먼저 묻는 편이 안전하다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `InheritableThreadLocal` | child thread bootstrap엔 간단하다 | pool/async/task 경계에선 오해가 많다 |
| `ScopedValue` | scope-bound immutable context에 잘 맞는다 | 읽기 전용 모델로 사고를 바꿔야 한다 |
| explicit parameter passing | 가장 명확하다 | 시그니처가 길어진다 |

핵심은 "자동 전파"보다 context lifetime 모델이 무엇인지 먼저 정하는 것이다.

## 꼬리질문

> Q: `InheritableThreadLocal`이면 executor task에도 자동 전파되나요?
> 핵심: 아니다. thread 생성 시점 복사라 이미 존재하는 pool worker에는 기대한 대로 동작하지 않는다.

> Q: `ScopedValue`는 왜 ThreadLocal 대안처럼 보이나요?
> 핵심: ambient context를 제공하지만 thread-bound mutable state가 아니라 scope-bound read-only context이기 때문이다.

> Q: virtual thread를 쓰면 `InheritableThreadLocal`이면 충분한가요?
> 핵심: 아니다. 생성 비용과 context semantics는 다른 문제다.

## 한 줄 정리

`InheritableThreadLocal`은 thread inheritance 모델이고 `ScopedValue`는 scope binding 모델이므로, context lifetime이 어디에 붙어야 하는지부터 먼저 결정해야 한다.
