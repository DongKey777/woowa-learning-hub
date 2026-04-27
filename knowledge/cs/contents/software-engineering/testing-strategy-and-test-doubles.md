# 테스트 전략과 테스트 더블

> 한 줄 요약: 테스트 전략은 단위/통합/E2E를 나누는 분류가 아니라, 어디에서 빠르게 신뢰를 얻고 어디에서 시스템 경계를 검증할지 정하는 설계다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: testing strategy and test doubles basics, testing strategy and test doubles beginner, testing strategy and test doubles intro, software engineering basics, beginner software engineering, 처음 배우는데 testing strategy and test doubles, testing strategy and test doubles 입문, testing strategy and test doubles 기초, what is testing strategy and test doubles, how to testing strategy and test doubles
> 관련 문서:
> - [Software Engineering README: 테스트 전략과 테스트 더블](./README.md#테스트-전략과-테스트-더블)
> - [테스트 전략 기초](./test-strategy-basics.md)
> - [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Repository Fake Design Guide](./repository-fake-design-guide.md)
> - [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [Backward Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Test Data Strategy Across Environments](./test-data-strategy-cross-environment.md)
> - [Production Readiness Review](./production-readiness-review.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)

> retrieval-anchor-keywords:
> - test strategy
> - test pyramid
> - unit test
> - integration test
> - e2e test
> - test double
> - mock
> - stub
> - fake
> - contract test
> - hexagonal testing seam
> - fake outbound port
> - first test checklist follow-up
> - webmvctest datajpatest next document
> - beginner test checklist reverse link

`테스트 전략 기초`에서 첫 테스트를 고른 뒤 "왜 그 테스트가 맞는지", "mock 대신 fake를 언제 써야 하는지"가 더 궁금할 때 이 문서로 올라오면 된다. 특히 `@WebMvcTest` 경계는 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md), `@DataJpaTest`에서 H2와 운영 DB 차이가 먼저 의심되면 [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)로 바로 내려가면 된다.

## 핵심 개념

테스트는 "많이 쓰면 좋은 것"이 아니라, 목적이 다른 안전장치를 층별로 배치하는 것이다.

- unit test는 작은 로직의 빠른 검증
- integration test는 실제 연결점의 검증
- contract test는 경계 의미의 검증
- e2e test는 사용자 흐름 전체의 마지막 검증

즉 좋은 테스트 전략은 **피드백 속도와 신뢰도 사이의 균형**이다.

---

## 깊이 들어가기

### 1. 테스트 피라미드는 원칙이지, 절대 규칙은 아니다

전통적인 피라미드는 단위 테스트가 많고, E2E는 적어야 한다고 말한다.

하지만 실제 서비스는:

- 복잡한 통합이 많고
- 계약이 자주 바뀌고
- 데이터 조건이 중요할 수 있다

그래서 모양보다 중요한 것은 테스트가 주는 **신뢰의 종류**다.

### 2. 테스트는 시스템 경계에 맞춰야 한다

경계별로 적절한 테스트가 다르다.

| 경계 | 적합한 테스트 |
|---|---|
| 메서드/객체 | unit test |
| 저장소/DB | integration test |
| 서비스 간 계약 | contract test |
| 사용자 시나리오 | E2E test |

이 문맥은 [Architectural Fitness Functions](./architectural-fitness-functions.md)과도 연결된다.

### 3. test double은 실제 의존성을 통제하는 도구다

대표적인 테스트 더블:

- Dummy: 자리만 채움
- Stub: 고정 응답 제공
- Fake: 단순하지만 동작하는 구현
- Spy: 호출 기록
- Mock: 상호작용 검증

중요한 건 이름 암기가 아니라 **어떤 의존성을 왜 대체하는가**다.
Ports and Adapters 구조에서 이 질문을 더 좁히면 "유스케이스는 어떤 outbound port를 fake로 대체하고, 어떤 adapter는 통합 환경에서 검증해야 하는가"가 된다. 이 흐름은 [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)에서 이어서 다룬다.

### 4. Mock은 유용하지만 남발하면 설계를 망칠 수 있다

Mock이 많아지면:

- 구현 상세에 테스트가 묶이고
- 리팩터링 내성이 떨어지고
- 행동보다 호출 순서에 집착한다

행위 검증이 꼭 필요한 경계에서만 mock을 쓰는 것이 좋다.

### 5. 테스트 전략은 배포 전략과 연결돼야 한다

테스트는 개발 로컬에서 끝나지 않는다.

다음과 연결된다.

- PR gate
- contract gate
- canary rollout
- rollback 판단
- production readiness review

즉 테스트는 품질 검증이면서 **출시 안전 장치**다.

---

## 실전 시나리오

### 시나리오 1: 계산 로직이 복잡하다

단위 테스트로 빠르게 로직을 잡고, 핵심 경계는 contract test로 보강한다.

### 시나리오 2: 외부 API가 자주 바뀐다

mock만으로는 부족하고, 실제 계약 검증과 stub 서버를 같이 써야 한다.

### 시나리오 3: 결제/주문 흐름을 검증한다

E2E는 최소 핵심 시나리오만 두고, 나머지는 contract/integration으로 분해한다.

---

## 코드로 보기

```java
@Test
void calculates_discount_correctly() {
    Order order = new Order(...);
    Money discount = discountPolicy.calculate(order);
    assertThat(discount).isEqualTo(Money.of(1000));
}
```

좋은 테스트는 구현 세부보다 시나리오와 기대 결과를 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| unit 중심 | 빠르다 | 통합 문제가 늦게 보일 수 있다 | 로직이 복잡할 때 |
| integration 중심 | 실제와 가깝다 | 느릴 수 있다 | DB/브로커 의존이 중요할 때 |
| contract + minimal E2E | 경계를 잘 잡는다 | 설계가 필요하다 | 서비스가 여러 개일 때 |

테스트 전략은 "어떤 테스트를 쓸까"보다 **어느 수준에서 실패를 잡을까**의 문제다.

---

## 꼬리질문

- unit test와 integration test의 경계를 어디에 둘 것인가?
- mock 대신 fake를 쓰는 것이 더 나은 곳은 어디인가?
- contract test를 어떤 경계에 적용할 것인가?
- E2E를 최소화하면서도 충분한 신뢰를 얻을 수 있는가?

## 한 줄 정리

테스트 전략과 테스트 더블은 빠른 피드백과 높은 신뢰를 동시에 얻기 위해, 각 경계에 맞는 검증 계층과 대체 구현을 배치하는 설계다.
