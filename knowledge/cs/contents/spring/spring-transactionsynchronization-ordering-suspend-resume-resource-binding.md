---
schema_version: 3
title: Spring TransactionSynchronization Ordering Suspend Resume Resource Binding
concept_id: spring/transactionsynchronization-ordering-suspend-resume-resource-binding
canonical: true
category: spring
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- transactionsynchronization-ordering-suspend
- resume-resource-binding
- transactionsynchronization-ordering
- suspend-resume-resource
aliases:
- TransactionSynchronization ordering
- suspend resume resource binding
- transaction synchronization lifecycle
- afterCommit ordering
- nested propagation resource cleanup
- transaction callback chain
intents:
- deep_dive
- troubleshooting
linked_paths:
- contents/spring/spring-transaction-synchronization-aftercommit-pitfalls.md
- contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md
- contents/spring/spring-transactiontemplate-programmatic-transaction-boundaries.md
- contents/spring/transactional-deep-dive.md
- contents/spring/spring-delivery-reliability-retryable-resilience4j-outbox-relay.md
- contents/spring/spring-transaction-debugging-playbook.md
expected_queries:
- TransactionSynchronization ordering과 suspend resume은 어떤 lifecycle로 동작해?
- resource binding cleanup 시점을 모르면 nested propagation에서 어떤 side effect가 생겨?
- afterCommit hook만이 아니라 beforeCommit afterCompletion ordering은 어떻게 봐야 해?
- TransactionSynchronization과 TransactionTemplate, REQUIRES_NEW는 어떻게 연결돼?
contextual_chunk_prefix: |
  이 문서는 TransactionSynchronization을 단순 afterCommit hook이 아니라 transaction lifecycle,
  ordering, resource binding, suspend/resume, cleanup까지 포함한 계약으로 설명한다.
  nested propagation과 callback chain side effect를 함께 다룬다.
---
# Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding

> 한 줄 요약: `TransactionSynchronization`는 단순 `afterCommit` 훅이 아니라 자원 바인딩과 suspend/resume까지 포함한 lifecycle 계약이므로, ordering과 resource cleanup 감각이 없으면 nested propagation이나 callback 체인에서 이상한 side effect가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Transaction Synchronization Callbacks and `afterCommit` Pitfalls](./spring-transaction-synchronization-aftercommit-pitfalls.md)
> - [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./spring-transaction-propagation-nested-requires-new-case-studies.md)
> - [Spring `TransactionTemplate` and Programmatic Transaction Boundaries](./spring-transactiontemplate-programmatic-transaction-boundaries.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](./spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

retrieval-anchor-keywords: TransactionSynchronization ordering, suspend resume, resource binding, TransactionSynchronizationManager, afterCompletion cleanup, synchronization callback order, REQUIRES_NEW suspend, thread-bound resource

## 핵심 개념

기존 `afterCommit` 감각만으로는 `TransactionSynchronization`을 절반만 이해한 것이다.

실제로 이 계약은 다음까지 포함한다.

- callback ordering
- resource binding
- suspend / resume
- completion cleanup

즉 synchronization은 "커밋 뒤에 뭐 하나 하기"보다, **트랜잭션에 묶인 자원과 후처리의 전체 lifecycle을 제어하는 훅**에 가깝다.

이걸 모르면 특히 아래에서 헷갈린다.

- `REQUIRES_NEW`로 안쪽 트랜잭션을 열 때
- thread-bound resource가 어떤 시점에 바뀌는지 볼 때
- cleanup이 왜 누락되면 안 되는지 이해할 때

## 깊이 들어가기

### 1. synchronization은 자원 바인딩 위에 올라간다

Spring 트랜잭션은 보통 현재 스레드에 다음 같은 자원을 바인딩한다.

- JDBC Connection
- Hibernate Session / JPA EntityManager
- custom resource holder

`TransactionSynchronizationManager`는 이런 자원과 callback을 함께 관리한다.

즉 synchronization callback은 이벤트성 알림이 아니라, **현재 트랜잭션 자원과 엮인 lifecycle hook**이다.

### 2. ordering이 중요하다

여러 synchronization이 등록되면 순서가 의미를 갖는다.

예를 들어:

- 먼저 flush/validation
- 그다음 cache evict 예약
- 마지막에 metric/cleanup

순서를 의식하지 않으면 다음이 생길 수 있다.

- cleanup이 너무 일찍 실행됨
- metric은 성공처럼 찍혔는데 실제 후속 작업은 실패
- 후행 callback이 기대한 resource state가 이미 정리됨

즉 callback은 있어 보이는 대로 나열하는 것이 아니라, **어느 시점의 자원 상태를 전제로 하는지**를 맞춰야 한다.

### 3. `suspend` / `resume`은 `REQUIRES_NEW` 감각을 선명하게 만든다

바깥 트랜잭션이 있고 안쪽에서 `REQUIRES_NEW`가 열리면, 보통 바깥 자원은 suspend되고 안쪽 자원이 새로 바인딩된다.

그리고 안쪽이 끝나면 바깥 자원이 resume된다.

이 흐름을 모르면 다음이 헷갈린다.

- 왜 같은 스레드인데 자원이 달라 보이는가
- 왜 바깥 트랜잭션 컨텍스트가 잠깐 사라진 것처럼 느껴지는가
- 안쪽에서 등록한 synchronization과 바깥 synchronization이 왜 운명이 다른가

즉 `REQUIRES_NEW`는 전파 수준만의 문제가 아니라, **자원 바인딩 세트가 한 번 바뀌는 것**이다.

### 4. cleanup은 성공/실패보다 "항상"의 의미가 중요하다

`afterCompletion`이 중요한 이유는 commit/rollback 여부보다, 자원 정리를 확실히 할 수 있기 때문이다.

특히 custom thread-bound resource를 썼다면:

- 성공했을 때도
- 실패했을 때도
- 예외가 중간에 났을 때도

정리 경로가 필요하다.

이 감각이 없으면 `ThreadLocal` 오염과 비슷한 종류의 트랜잭션 자원 오염이 생길 수 있다.

### 5. custom synchronization은 side effect보다 lifecycle 의식을 먼저 가져야 한다

많은 예제가 `afterCommit` 알림에만 집중하지만,
실제로 custom synchronization을 만들 때 더 중요한 질문은 다음이다.

- 이 callback은 어떤 자원 상태를 전제하는가
- suspend/resume 시 무엇을 함께 멈추거나 복원해야 하는가
- cleanup이 누락되면 어떤 오염이 남는가

즉 synchronization을 side effect 훅으로만 보면, **자원 lifecycle 관리라는 본질**을 놓치기 쉽다.

### 6. transaction synchronization과 이벤트/아웃박스는 역할이 다르다

synchronization은 현재 트랜잭션 lifecycle 내부에 밀착한 도구다.

반면 이벤트/아웃박스는 트랜잭션 사실을 바깥 경계로 넘기는 도구다.

즉 resource ordering/cleanup이 중요하면 synchronization이 맞고,
전달 신뢰성/재시도가 중요하면 이벤트나 outbox가 더 맞다.

## 실전 시나리오

### 시나리오 1: `REQUIRES_NEW` 안쪽 작업 후 바깥 컨텍스트가 이상하게 느껴진다

suspend/resume 과정에서 자원 바인딩이 바뀌는 감각을 놓쳤을 수 있다.

### 시나리오 2: custom ThreadLocal/resource holder가 트랜잭션 후에도 남는다

`afterCompletion` cleanup 누락을 의심해야 한다.

### 시나리오 3: 여러 synchronization이 등록됐는데 metric과 cleanup 순서가 뒤엉킨다

ordering을 명시적으로 보지 않고 side effect만 추가한 결과일 수 있다.

### 시나리오 4: `afterCommit`만 생각하고 custom synchronization을 만들었다가 nested propagation에서 꼬인다

callback이 현재 어떤 자원 세트에 붙어 있는지 먼저 봐야 한다.

## 코드로 보기

### synchronization 등록

```java
TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
    @Override
    public void suspend() {
    }

    @Override
    public void resume() {
    }

    @Override
    public void afterCompletion(int status) {
    }
});
```

### 자원 바인딩 확인

```java
boolean active = TransactionSynchronizationManager.isSynchronizationActive();
boolean actualTx = TransactionSynchronizationManager.isActualTransactionActive();
```

### cleanup 의식

```java
TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
    @Override
    public void afterCompletion(int status) {
        CustomResourceHolder.clear();
    }
});
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 `afterCommit` 사용 | 이해가 쉽다 | ordering/resource lifecycle 감각이 약해질 수 있다 | 단순 후속 처리 |
| full synchronization lifecycle 의식 | nested propagation과 자원 정리가 선명해진다 | 개념 부담이 높다 | custom tx integration, resource binding |
| 이벤트/아웃박스 사용 | 전달 신뢰성과 분리가 좋다 | 현재 tx 자원 lifecycle 제어엔 맞지 않는다 | 외부 전송, 재시도 |
| custom thread-bound resource 사용 | 편할 수 있다 | cleanup 누락 시 오염 위험이 크다 | 아주 제한적으로 |

핵심은 `TransactionSynchronization`을 `afterCommit` 별칭으로 보지 말고, **자원 바인딩과 suspend/resume까지 포함한 lifecycle 계약**으로 보는 것이다.

## 꼬리질문

> Q: `TransactionSynchronization`에서 ordering이 왜 중요한가?
> 의도: callback dependency 이해 확인
> 핵심: 각 callback이 기대하는 자원 상태와 정리 시점이 다르기 때문이다.

> Q: `REQUIRES_NEW`와 suspend/resume은 어떤 관계인가?
> 의도: 자원 바인딩 전환 이해 확인
> 핵심: 바깥 자원을 잠시 내려놓고 안쪽 자원 세트로 교체한 뒤 다시 복원하는 감각이다.

> Q: `afterCompletion` cleanup이 왜 중요한가?
> 의도: 자원 오염 방지 이해 확인
> 핵심: 성공/실패와 무관하게 thread-bound resource를 정리해야 하기 때문이다.

> Q: synchronization과 outbox의 역할 차이는 무엇인가?
> 의도: lifecycle vs 전달 신뢰성 구분 확인
> 핵심: 전자는 현재 tx lifecycle 제어, 후자는 바깥 경계로의 신뢰성 있는 전달이다.

## 한 줄 정리

`TransactionSynchronization`의 본질은 콜백 몇 개가 아니라, 트랜잭션 자원과 후처리의 ordering·suspend/resume·cleanup을 함께 다루는 lifecycle 계약이다.
