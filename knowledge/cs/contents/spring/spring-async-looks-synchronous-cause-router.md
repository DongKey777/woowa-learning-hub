---
schema_version: 3
title: 비동기가 동기처럼 보여요 원인 라우터
concept_id: spring/async-looks-synchronous-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- async-proxy-bypass
- enableasync-misread
- async-context-boundary
aliases:
- async가 동기처럼 보임
- async 같은 스레드 실행
- '@Async 안 먹는 이유'
- 비동기 메서드가 바로 실행됨
- async 설정 문제인가
- async 같은 thread 로그
symptoms:
- '@Async를 붙였는데 caller 로그와 worker 로그가 같은 스레드에서 찍혀요'
- 비동기로 넘겼다고 생각했는데 응답이 끝날 때까지 메서드가 같이 붙어 있어요
- '@EnableAsync도 붙였는데 왜 동기처럼 보여요?'
- 같은 메서드를 다른 Bean으로 빼니까 갑자기 비동기처럼 동작해요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/aop-basics
next_docs:
- spring/self-invocation-proxy-misconception
- spring/spring-scheduler-async-boundaries
- spring/spring-transactional-async-composition-traps
- spring/spring-async-context-propagation-restclient-http-interface-clients
linked_paths:
- contents/spring/spring-async-self-invocation-same-thread-symptom-card.md
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
- contents/spring/spring-self-invocation-proxy-annotation-matrix.md
- contents/spring/spring-scheduler-async-boundaries.md
- contents/spring/spring-transactional-async-composition-traps.md
- contents/spring/spring-async-context-propagation-restclient-http-interface-clients.md
confusable_with:
- spring/self-invocation-proxy-misconception
- spring/spring-scheduler-async-boundaries
- spring/spring-transactional-async-composition-traps
forbidden_neighbors: []
expected_queries:
- 'Spring에서 @Async를 붙였는데 왜 호출한 쪽과 같은 스레드 이름이 찍혀요?'
- '@EnableAsync까지 켰는데 비동기 메서드가 동기처럼 실행될 때 어디부터 나눠서 봐야 해?'
- 같은 코드를 다른 Bean으로 옮기니 async가 되는데 원래는 왜 안 됐어?
- 비동기 작업인데 응답이 끝날 때까지 같이 붙어 있으면 설정 문제 말고 무엇을 의심해?
- '@Async가 안 먹는 것처럼 보일 때 프록시 문제와 executor 문제를 어떻게 구분해?'
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring에서 "@Async를 붙였는데 같은 스레드에서
  찍혀요", "비동기라더니 동기처럼 보여요", "@EnableAsync도 있는데 왜
  안 먹어요", "다른 Bean으로 빼니 갑자기 async가 돼요" 같은 자연어
  증상을 프록시 우회 / Bean 경계 바깥 호출 / executor 설정과 관측 착시 /
  async 뒤 트랜잭션·컨텍스트 기대 혼동 네 갈래로 나누는 symptom_router다.
  async 안 먹음, 같은 thread 로그, 비동기 메서드가 바로 실행됨 같은 검색을
  원인 문서로 보내는 입구로 사용한다.
---

# 비동기가 동기처럼 보여요 원인 라우터

## 한 줄 요약

> `@Async`가 동기처럼 보일 때는 설정 한 줄보다 먼저 호출이 프록시를 탔는지, 그리고 "다른 스레드"를 무엇으로 확인했는지부터 갈라야 한다.

## 가능한 원인

1. **같은 클래스 내부 호출이라 프록시를 우회했다.** `this.send()`처럼 부르면 `@Async`가 붙어 있어도 worker thread로 넘길 기회를 못 얻는다. 이 갈래는 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)와 [Spring `@Async` 내부 호출 증상 카드](./spring-async-self-invocation-same-thread-symptom-card.md)로 바로 이어진다.
2. **Spring Bean 경계 밖에서 호출했다.** 직접 `new` 한 객체, `private` 메서드, 테스트 대역처럼 프록시가 설 자리가 없으면 "비동기 설정이 무시된 것처럼" 보일 수 있다. 이 경우는 [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)에서 프록시 정문 3문항으로 먼저 자른다.
3. **실제로는 비동기인데 관측 기준을 잘못 잡았다.** executor thread 이름, 로그 flush 시점, `CompletableFuture.join()` 호출 때문에 다시 기다린 흐름을 "동기 실행"으로 읽는 경우가 있다. 이 갈래는 [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)에서 스레드 경계와 관측 포인트를 다시 잡는다.
4. **비동기 이후의 트랜잭션·컨텍스트 기대를 같은 문제로 묶었다.** 다른 스레드로 넘어간 뒤 `SecurityContext`, 트랜잭션, MDC가 안 이어져도 학습자는 "`@Async`가 안 됐다"고 느끼기 쉽다. 이때는 [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)와 [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)로 내려간다.

## 빠른 자기 진단

1. caller와 `@Async` 메서드 안 로그가 완전히 같은 스레드 이름이면 설정 추가 전에 `this.method()`, `private`, 직접 `new`가 있는지 먼저 본다.
2. 다른 Bean으로 분리하자마자 동작이 달라졌다면 환경 차이보다 프록시 경유 여부가 바뀐 것이다. 이 경우는 [Spring `@Async` 내부 호출 증상 카드](./spring-async-self-invocation-same-thread-symptom-card.md)를 먼저 읽는다.
3. 다른 스레드 이름이 보이는데도 "왜 응답이 느리지?"가 남으면 비동기 실패가 아니라 `join()`, 큐 포화, `CallerRunsPolicy` 같은 관측 착시일 수 있다. 이때는 [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)로 간다.
4. "비동기로 넘겼는데 트랜잭션이 안 이어져요", "인증 정보가 사라져요"가 핵심이면 실행 자체보다 경계 이후 전파 문제다. 그때는 [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md)와 [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md)를 고른다.

## 다음 학습

- 가장 짧게 원인을 좁히려면 [Spring `@Async` 내부 호출 증상 카드](./spring-async-self-invocation-same-thread-symptom-card.md)와 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)를 한 쌍으로 본다.
- "`@Async`만의 규칙이 아니라 프록시 공통 문제인가?"를 확인하려면 [Spring Self-Invocation Proxy Trap Matrix](./spring-self-invocation-proxy-annotation-matrix.md)로 이어간다.
- 비동기 자체는 맞는데 트랜잭션, 컨텍스트, 응답 지연이 남으면 [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md), [Spring `@Transactional` and `@Async` Composition Traps](./spring-transactional-async-composition-traps.md), [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](./spring-async-context-propagation-restclient-http-interface-clients.md) 순으로 내려간다.
