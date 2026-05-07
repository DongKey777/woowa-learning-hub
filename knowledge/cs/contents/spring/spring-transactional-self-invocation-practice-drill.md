---
schema_version: 3
title: 'Spring @Transactional self-invocation 판별 드릴'
concept_id: spring/transactional-self-invocation-practice-drill
canonical: false
category: spring
difficulty: intermediate
doc_role: drill
level: intermediate
language: mixed
source_priority: 72
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- transactional-self-invocation
- proxy-boundary
- transaction-test-shape
aliases:
- transactional self invocation drill
- Spring self invocation 연습
- 같은 클래스 내부 호출 transaction
- 프록시 안 타는 호출
- transactional 적용 안 됨 드릴
symptoms:
- 같은 클래스 내부 메서드에 @Transactional을 붙였는데 트랜잭션이 적용되지 않는다
- 테스트에서는 rollback이 되는 것 같지만 운영 경로에서는 proxy를 타지 않는다
- public 메서드와 private/helper 메서드의 transaction boundary가 섞인다
intents:
- drill
- troubleshooting
prerequisites:
- spring/transactional-basics
- spring/self-invocation-proxy-annotation-matrix
next_docs:
- spring/transactional-not-applied-cause-router
- spring/self-call-verification-test-mini-guide
- spring/transactional-self-invocation-test-bridge-primer
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-self-invocation-proxy-annotation-matrix.md
- contents/spring/spring-transactional-not-applied-cause-router.md
- contents/spring/spring-self-call-verification-test-mini-guide.md
- contents/spring/spring-transactional-self-invocation-test-bridge-primer.md
- contents/spring/aop-proxy-mechanism.md
- contents/spring/transactional-deep-dive.md
confusable_with: []
forbidden_neighbors: []
confusable_with:
- spring/transactional-basics
- spring/self-invocation-proxy-annotation-matrix
- spring/transactional-not-applied-cause-router
- spring/self-call-verification-test-mini-guide
expected_queries:
- 같은 클래스 안에서 @Transactional 메서드를 호출하면 적용되는지 드릴로 확인하고 싶어
- Spring self invocation이 왜 proxy를 안 타는지 예제로 풀어줘
- Transactional이 안 먹는 코드를 보고 어디가 경계인지 맞춰보고 싶어
- self call 문제를 테스트로 검증하는 연습을 하고 싶어
contextual_chunk_prefix: |
  이 문서는 Spring @Transactional이 같은 클래스 내부 호출에서 왜 적용되지
  않는지 코드 조각으로 판별하는 drill이다. self-invocation, proxy boundary,
  내부 메서드 호출, rollback 안 됨, transactional not applied 같은 질의를
  AOP 프록시 경계와 테스트 모양 연습으로 연결한다.
---
# Spring @Transactional self-invocation 판별 드릴

> 한 줄 요약: `@Transactional`은 메서드에 붙은 마법이 아니라 proxy를 통과할 때 적용되는 advice다. 같은 객체 내부에서 `this.save()`처럼 부르면 proxy를 지나지 않는다.

**난이도: 🟡 Intermediate**

## 문제 1

```java
@Service
class ReservationService {
    public void reserve() {
        save();
    }

    @Transactional
    public void save() {
        // insert reservation
    }
}
```

질문: `reserve()`를 컨트롤러가 호출하면 `save()`의 transaction advice가 적용될까?

답: 보통 적용되지 않는다. `reserve()` 내부의 `save()`는 같은 인스턴스의 직접 호출이라 proxy를 통과하지 않는다.

## 문제 2

```java
@Service
class ReservationFacade {
    private final ReservationWriter writer;

    public void reserve() {
        writer.save();
    }
}

@Service
class ReservationWriter {
    @Transactional
    public void save() {
        // insert reservation
    }
}
```

질문: 이번에는 적용될까?

답: 적용된다. 다른 Spring bean인 `writer`를 주입받아 호출하므로 proxy를 통과할 수 있다.

## 문제 3

```java
@Transactional
private void save() {
    // insert reservation
}
```

질문: private 메서드에 붙이면 안전할까?

답: 안전하지 않다. proxy 기반 AOP는 외부에서 호출 가능한 메서드 경계에 걸린다고 생각해야 한다. private helper에는 transaction boundary를 두지 않는 편이 좋다.

## 점검 문장

```text
이 @Transactional 메서드는 Spring proxy 밖에서 들어오는 호출인가?
```

이 질문에 답하지 못하면 annotation 위치보다 호출 경로를 먼저 그린다.

## 한 줄 정리

self-invocation 문제는 annotation 유무가 아니라 호출이 Spring proxy를 통과했는지로 판단한다.
