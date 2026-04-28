# 테스트 전략과 테스트 더블

> 한 줄 요약: 이 문서는 `첫 테스트를 고른 뒤 왜 그 선택이 맞는지`와 `mock/stub/fake 중 무엇을 왜 쓰는지`를 한 단계 더 설명하는 follow-up이다.

**난이도: 🟡 Intermediate**


관련 문서:

- [테스트 전략 기초](./test-strategy-basics.md)
- [Hexagonal Testing Seams Primer](./hexagonal-testing-seams-primer.md)
- [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
- [Repository Fake Design Guide](./repository-fake-design-guide.md)
- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
- [Spring MVC Request Lifecycle Basics](../spring/spring-mvc-request-lifecycle-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: test strategy follow-up, test double basics, mock stub fake difference, first test checklist follow-up, unit slice integration e2e balance, springboottest not e2e, webmvctest datajpatest next step, fake outbound port, contract test basics, hexagonal testing seam, beginner test routing follow-up

`테스트 전략 기초`에서 첫 테스트를 고른 뒤 "왜 그 테스트가 맞는지", "mock 대신 fake를 언제 써야 하는지"가 더 궁금할 때 이 문서로 올라오면 된다. 특히 `@WebMvcTest` 경계는 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md), `@DataJpaTest`에서 테스트 DB 차이가 먼저 의심되면 [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)로 바로 내려가면 된다.

처음 읽는 초심자라면 이 문서 전체를 다 읽기보다 아래 두 질문만 먼저 잡으면 충분하다.

| 지금 막힌 질문 | 여기서 먼저 볼 곳 |
|---|---|
| "왜 단위 테스트로 시작하지?" | `테스트는 시스템 경계에 맞춰야 한다` |
| "mock 대신 fake가 더 낫다는 말이 왜 나오지?" | `test double은 실제 의존성을 통제하는 도구다` |

- stop rule: `첫 테스트 1개`를 아직 못 골랐다면 [테스트 전략 기초](./test-strategy-basics.md)로 먼저 돌아간다.
- 운영/배포 질문은 이 문서 본문보다 [Backend Delivery and Observability Foundations Primer](./backend-delivery-observability-foundations-primer.md) 같은 follow-up 문서에서 따로 보는 편이 beginner 동선에 맞다.

## 핵심 개념

테스트는 "많이 쓰면 좋은 것"이 아니라, 목적이 다른 안전장치를 층별로 배치하는 것이다. 이 문서에서는 beginner primer와 같은 용어를 그대로 쓴다.

- unit test는 작은 로직의 빠른 검증
- slice test는 MVC/JPA 같은 특정 기술 경계의 검증
- app integration test는 `@SpringBootTest` 계열의 실제 연결점 검증
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
| 웹/JPA 같은 특정 프레임워크 경계 | slice test |
| 저장소/DB/트랜잭션 협력 | app integration test |
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

### 5. 테스트 전략은 검증 질문 순서와 연결돼야 한다

초심자에게 더 중요한 기준은 "운영 장치 이름"보다 **지금 실패를 어디서 가장 빨리 다시 만들 수 있느냐**다.

보통은 아래 순서로 생각하면 충분하다.

- 규칙이 바뀌었나
- HTTP 입력/응답 계약이 바뀌었나
- DB/JPA 동작이 바뀌었나
- 여러 컴포넌트 협력 흐름이 바뀌었나

이 순서가 잡힌 뒤에야 PR gate, contract gate, rollout 같은 운영 질문을 더 얹을 수 있다. 이 문서에서는 그 운영 확장을 중심으로 다루지 않고, 먼저 **검증 질문과 테스트 종류를 맞추는 감각**에 집중한다.

---

## 실전 시나리오

### 시나리오 1: 계산 로직이 복잡하다

단위 테스트로 빠르게 로직을 잡고, 핵심 경계는 contract test로 보강한다.

### 시나리오 2: 외부 API가 자주 바뀐다

mock만으로는 부족하고, 실제 계약 검증과 stub 서버를 같이 써야 한다.

### 시나리오 3: 결제/주문 흐름을 검증한다

E2E는 최소 핵심 시나리오만 두고, 나머지는 contract/app integration으로 분해한다.

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
| unit 중심 | 빠르다 | 협력 문제가 늦게 보일 수 있다 | 로직이 복잡할 때 |
| slice + app integration | 웹/JPA 경계와 실제 협력을 분리해 읽기 쉽다 | 경계 설계가 필요하다 | Spring 테스트 범위를 나눌 때 |
| contract + minimal E2E | 경계를 잘 잡는다 | 설계가 필요하다 | 서비스가 여러 개일 때 |

테스트 전략은 "어떤 테스트를 쓸까"보다 **어느 수준에서 실패를 잡을까**의 문제다.

---

## 꼬리질문

- unit test와 slice/app integration test의 경계를 어디에 둘 것인가?
- mock 대신 fake를 쓰는 것이 더 나은 곳은 어디인가?
- contract test를 어떤 경계에 적용할 것인가?
- E2E를 최소화하면서도 충분한 신뢰를 얻을 수 있는가?

## 한 줄 정리

테스트 전략과 테스트 더블은 빠른 피드백과 높은 신뢰를 동시에 얻기 위해, unit/slice/app integration/E2E 각 경계에 맞는 검증 계층과 대체 구현을 배치하는 설계다.
