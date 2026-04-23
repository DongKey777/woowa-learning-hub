# 테스트 전략 기초 (Test Strategy Basics)

> 한 줄 요약: 테스트는 단위/통합/E2E로 범위가 나뉘고, 비용과 신뢰도의 트레이드오프를 이해하면 어느 계층에 어떤 테스트를 얼마나 쓸지 판단할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [design-pattern 카테고리 인덱스](../design-pattern/README.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: test strategy basics, 테스트 전략 입문, unit test 설명, integration test 설명, e2e test 뭐예요, test pyramid, 테스트 피라미드, mock stub 차이, 테스트 더블 설명, 단위 테스트 왜 쓰나요, 테스트 어디서 써요, beginner testing, junit 기초

## 핵심 개념

테스트는 코드가 의도대로 동작하는지 자동으로 확인하는 수단이다. 범위에 따라 세 단계로 나뉜다.

- **단위 테스트(Unit Test)** — 하나의 클래스나 메서드를 격리해서 검증한다. 빠르고 저렴하다.
- **통합 테스트(Integration Test)** — 여러 컴포넌트(DB, 서비스, 레포지토리)를 묶어서 검증한다. 느리지만 실제 협력을 확인한다.
- **E2E 테스트** — 실제 HTTP 요청을 보내 전체 흐름을 검증한다. 가장 느리고 비용이 크다.

입문자가 헷갈리는 포인트는 "외부 의존을 어떻게 처리하느냐"다. 단위 테스트에서는 실제 DB 대신 가짜 객체(Mock/Stub)를 쓰는 경우가 많다.

## 한눈에 보기

```
E2E         ▲ 적게
Integration ▌▌
Unit        ▌▌▌▌▌ 많이
```

| 종류 | 속도 | 신뢰도 | 권장 비율 |
|---|---|---|---|
| 단위 테스트 | 빠름 | 격리된 로직 검증 | 많이 |
| 통합 테스트 | 보통 | 협력 검증 | 적당히 |
| E2E 테스트 | 느림 | 전체 흐름 검증 | 소수 |

## 상세 분해

**단위 테스트의 범위**

단위 테스트는 보통 외부 의존(DB, 외부 API)을 Mock으로 대체하고 순수 로직만 검증한다.

```java
@Test
void 주문_금액이_0원이면_예외() {
    OrderService service = new OrderService(mockRepository);
    assertThrows(InvalidOrderException.class,
        () -> service.create(new CreateOrderRequest(0)));
}
```

**테스트 더블(Test Double)**

- **Mock** — 호출 여부와 횟수를 검증한다. `verify(mock.send()).wasCalled(1)`.
- **Stub** — 특정 입력에 정해진 값을 반환한다. `when(repo.find(id)).thenReturn(order)`.
- **Fake** — 실제 동작을 단순하게 흉내낸다. 메모리 저장소 등.

입문 단계에서는 Mock과 Stub의 차이보다, "실제 의존을 교체해서 빠르게 테스트한다"는 개념을 먼저 잡으면 충분하다.

**통합 테스트 범위**

Spring에서 `@SpringBootTest`를 쓰면 전체 컨텍스트를 올려서 실제 DB와 함께 테스트할 수 있다. `@DataJpaTest`는 JPA 관련 빈만 올려 더 빠르다.

## 흔한 오해와 함정

- "테스트가 많으면 많을수록 좋다"는 오해가 있다. 테스트가 구현 세부에 강하게 묶이면 리팩토링할 때 테스트도 같이 고쳐야 해서 오히려 비용이 커진다. 인터페이스와 동작을 테스트하는 편이 낫다.
- `@SpringBootTest`를 단위 테스트처럼 쓰면 전체 컨텍스트 로딩 비용이 쌓여 빌드가 느려진다.
- Mock을 너무 많이 쓰면 실제 협력에서 발생하는 버그를 잡지 못한다. 핵심 통합 경로는 통합 테스트로 커버해야 한다.

## 실무에서 쓰는 모습

대부분의 백엔드 프로젝트에서는 도메인/서비스 로직은 단위 테스트로 빠르게 커버하고, Repository나 외부 연동이 포함된 경로는 슬라이스 테스트(`@DataJpaTest`, `@WebMvcTest`)로 검증하며, 핵심 시나리오 2~3개만 `@SpringBootTest` E2E 테스트로 잡는 패턴이 흔하다.

## 더 깊이 가려면

- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md) — Spy, Stub, Mock, Fake의 정밀한 구분과 선택 기준
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md) — 포트/어댑터 구조가 테스트 격리를 어떻게 도와주는지

## 면접/시니어 질문 미리보기

- "단위 테스트와 통합 테스트를 어떻게 구분하나요?" — 외부 의존(DB, 네트워크)이 실제로 연결되는지 여부가 가장 실용적인 기준이다. 외부가 Mock이면 단위, 실제 연결이면 통합이다.
- "Mock을 쓰면 어떤 장단점이 있나요?" — 장점: 빠르고 격리된 검증 가능. 단점: 실제 의존 구현이 바뀌면 Mock이 현실을 반영하지 못해 거짓 통과가 생길 수 있다.
- "테스트가 많으면 리팩토링이 어려워지는 이유가 뭔가요?" — 테스트가 구현 내부(메서드 이름, 호출 순서)에 묶여 있으면 구현을 바꿀 때 테스트도 같이 바꿔야 한다. 동작(결과)을 테스트하면 이 문제가 줄어든다.

## 한 줄 정리

테스트는 단위·통합·E2E를 적절히 섞되, 많은 단위 테스트로 빠른 피드백을 잡고 소수의 통합 테스트로 실제 협력을 검증하는 것이 기본 전략이다.
