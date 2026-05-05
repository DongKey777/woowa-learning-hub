---
schema_version: 3
title: 트랜잭션이 안 먹어요 원인 라우터
concept_id: spring/transactional-not-applied-cause-router
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
- transactional-self-invocation
- proxy-boundary
- rollback-expectation
aliases:
- 트랜잭션 안 먹는 이유
- transactional 적용 안 됨
- 왜 transactional이 안 먹지
- 스프링 트랜잭션이 안 걸림
- transactional 프록시 우회
- rollback이 안 되는 것 같음
symptoms:
- '@Transactional을 붙였는데 this.method()로 부르면 트랜잭션이 안 열리는 것 같아요'
- 서비스 메서드에 @Transactional이 있는데 예외가 나도 rollback이 안 된 것처럼 보여요
- 테스트에서는 service가 보이는데 실제로는 트랜잭션이 적용되지 않는 느낌이에요
- private 메서드나 직접 new 한 객체에 @Transactional을 붙였는데 변화가 없어요
intents:
- symptom
- troubleshooting
prerequisites:
- spring/transactional-basics
next_docs:
- spring/transactional-basics
- spring/self-invocation-proxy-misconception
- spring/aop-basics
- spring/aop-proxy-mechanism
linked_paths:
- contents/spring/spring-transactional-basics.md
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
- contents/spring/spring-aop-basics.md
- contents/spring/aop-proxy-mechanism.md
- contents/spring/spring-transactional-self-invocation-test-bridge-primer.md
- contents/spring/spring-transaction-propagation-required-requires-new-rollbackonly-primer.md
- contents/spring/spring-unexpectedrollbackexception-mini-debugging-card.md
- contents/spring/spring-test-slice-scan-boundaries.md
confusable_with:
- spring/self-invocation-proxy-misconception
- spring/aop-basics
- spring/transactional-basics
forbidden_neighbors:
- contents/spring/spring-self-invocation-transactional-only-misconception-primer.md
expected_queries:
- Spring에서 @Transactional을 붙였는데 왜 내부 호출에서는 효과가 없어요?
- private 메서드에 트랜잭션을 붙였는데 변화가 없는 이유를 어디서 봐야 해?
- 예외가 났는데도 rollback이 안 된 것처럼 보일 때 먼저 무엇을 의심해?
- 테스트에선 service가 있는데 transaction만 이상하면 어떤 축으로 나눠 봐야 해?
- 직접 생성한 객체에 @Transactional을 달았을 때 왜 기대대로 동작하지 않아?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring에서 "@Transactional을 붙였는데 안 먹어요",
  "rollback이 안 된 것 같아요", "this.method()에서는 왜 다르게 보여요",
  "private 메서드에 붙였는데 변화가 없어요", "직접 new 한 객체는 왜
  트랜잭션이 안 걸려요" 같은 자연어 증상을 프록시 우회 / Spring Bean
  경계 아님 / rollback 기대 해석 오류 / 테스트 slice와 runtime 혼동 네
  갈래로 나누는 symptom_router다. transactional 적용 안 됨, 트랜잭션이
  안 걸림, 예외가 나도 그대로 commit된 것 같음 같은 검색을 원인 문서로
  보내는 입구로 사용한다.
---

# 트랜잭션이 안 먹어요 원인 라우터

> 한 줄 요약: `@Transactional`이 안 먹는다는 말은 대개 옵션 부족보다 프록시를 안 탔거나, rollback 기대를 잘못 읽었거나, 테스트와 runtime 층위를 섞어 본 경우다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring `@Transactional` 기초](./spring-transactional-basics.md)
- [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)
- [Spring AOP 기초](./spring-aop-basics.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지](./spring-transactional-self-invocation-test-bridge-primer.md)
- [Spring Transaction Propagation Beginner Primer](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)
- [Transaction Basics](../database/transaction-basics.md)

retrieval-anchor-keywords: transactional 적용 안 됨, 왜 transactional 안 먹지, spring transaction not applied, this method 프록시 우회, private method transactional, rollback 안 되는 것 같음, requires new 언제, transaction proxy basics, 처음 transactional 헷갈림, what is self invocation

## 핵심 개념

`@Transactional`은 annotation 자체가 마법처럼 실행되는 기능이 아니라 Spring Bean 프록시를 통과할 때 적용되는 규칙이다. 그래서 초급 단계에서는 먼저 "프록시를 탔는가", "Spring이 관리하는 객체인가", "정말 rollback이 안 된 건가", "테스트 문제를 runtime 문제로 착각한 건가"를 나누는 편이 빠르다.

## 한눈에 보기

| 지금 보이는 장면 | 먼저 확인할 질문 | 다음 문서 |
| --- | --- | --- |
| `this.method()`나 `private` 호출 | 프록시 정문을 우회했는가? | [Self-Invocation 오해 카드](./spring-self-invocation-transactional-only-misconception-primer.md) |
| 직접 `new` 한 객체에 annotation | Spring Bean이 맞는가? | [Spring AOP 기초](./spring-aop-basics.md) |
| 예외가 났는데 commit된 것처럼 보임 | rollback 기대를 잘못 읽은 건가? | [Transaction Propagation Primer](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md) |
| 테스트에서만 이상해 보임 | test slice와 runtime을 섞었는가? | [Test Slice Scan Boundary](./spring-test-slice-scan-boundaries.md) |

## 빠른 분기

1. `this.method()`나 `private` 호출이 보이면 옵션보다 호출 경로 문제를 먼저 본다.
2. `new OrderService()`처럼 직접 만든 객체라면 `@Transactional`이 읽힐 자리가 없다.
3. "`예외는 잡았는데 마지막에 또 터진다`", "`REQUIRES_NEW`가 필요한가`"가 같이 보이면 rollback-only 축이다.
4. Bean 자체가 안 보이는 테스트라면 트랜잭션보다 test slice 범위 문제일 수 있다.

## 흔한 오해와 함정

- `@Transactional`을 메서드에 붙였으니 어떤 호출 방식에서도 적용된다고 생각하기 쉽다.
- rollback이 안 된 것처럼 보여도 실제로는 checked exception 처리, catch 후 swallow, rollback-only 누적이 원인일 수 있다.
- 테스트에서 service Bean이 없었던 경험과 runtime 트랜잭션 오해를 같은 문제로 묶으면 원인 분기가 흐려진다.
- 프록시 규칙은 `@Transactional`만의 특수 규칙이 아니라 AOP 전반의 공통 경계라는 점을 놓치기 쉽다.

## 다음 행동

- 프록시 경계를 가장 짧게 다시 잡으려면 [Spring `@Transactional` 기초](./spring-transactional-basics.md)를 먼저 본다.
- 내부 호출이 핵심이면 [Spring Self-Invocation 공통 오해 1페이지 카드](./spring-self-invocation-transactional-only-misconception-primer.md)로 바로 간다.
- rollback-only와 `REQUIRES_NEW`가 핵심이면 [Spring Transaction Propagation Beginner Primer](./spring-transaction-propagation-required-requires-new-rollbackonly-primer.md)를 잇는다.
- DB 트랜잭션 자체 개념이 헷갈리면 [Transaction Basics](../database/transaction-basics.md)를 같이 보면 용어 해석이 쉬워진다.

## 한 줄 정리

`@Transactional`이 안 먹는 것처럼 보이면 먼저 프록시 경계와 rollback 기대를 나누고, 그다음에 옵션이나 전파 설정을 봐야 헛수고가 줄어든다.
