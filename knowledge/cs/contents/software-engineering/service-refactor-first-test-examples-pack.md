# Service Refactor First-Test Examples Pack

> 한 줄 요약: service 리팩터링에서 "`무엇을 먼저 보호할까?`"가 막히면, 변경을 `규칙 추출`, `계산 분리`, `협력/트랜잭션 재배치`로 나누고 각 장면마다 가장 싼 첫 failing test와 test double 1개를 같이 고르면 시작 비용이 크게 줄어든다.

**난이도: 🟡 Intermediate**

관련 문서:

- [리팩토링과 첫 failing test 연결 브리지](./refactoring-first-failing-test-bridge.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md)
- [Service 계층 기초](./service-layer-basics.md)
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: service refactor first test, service refactor examples pack, cheapest first failing test, service refactor fake mock spy, service 리팩터링 첫 테스트 예시, 처음 service refactor 뭐부터, 왜 springboottest 말고 unit test, first failing test service example, test double choice service, fake repository refactor, spy notifier refactor, transaction refactor test, 헷갈리는 service test, what is cheapest first test

## 핵심 개념

이 문서는 beginner primer 다음 단계 질문인 "`service를 정리하려는데, 이번 변경에서는 어떤 테스트와 어떤 double을 가장 먼저 붙여야 하지?`"를 다룬다.

핵심은 `service를 바꾼다`를 한 덩어리로 보지 않는 것이다. 보통은 아래 셋 중 하나다.

- 규칙을 더 읽히게 추출한다
- 계산 책임을 별도 collaborator로 분리한다
- 저장/알림/외부 호출 순서를 다시 배치한다

여기서 `가장 싼 first failing test`란 항상 단위 테스트라는 뜻이 아니다. **이번 위험을 가장 빨리 드러내는 최소 검증**이라는 뜻이다. 설계가 이미 framework에 강하게 묶여 있다면 더 넓은 테스트가 먼저일 수도 있다.

## 한눈에 보기

| 리팩터링 장면 | 먼저 보호할 질문 | 가장 싼 첫 failing test | 먼저 고를 double |
|---|---|---|---|
| 긴 service에서 중복 검사 규칙 추출 | `이미 있으면 저장이 막히는가` | `unit test` | fake repository |
| 할인 계산기를 분리 | `등급별 최종 금액이 그대로인가` | `unit test` | stub discount policy |
| 저장/알림/외부 승인 순서 재배치 | `실패 시 저장이 남지 않고 승인도 잘리는가` 또는 `성공 시 알림이 1번만 가는가` | `app integration test` 또는 `unit test` | fake external client 또는 spy notifier |

- 짧게 외우면 `규칙 결과면 fake/stub`, `호출 자체가 답이면 spy/mock`, `트랜잭션 경계면 넓혀서 붙인다`.
- 이 문서는 "예쁜 설계"보다 "첫 pass에서 무엇을 먼저 실패시킬까"를 빠르게 고르는 예시 팩이다.

## 시나리오 1: 중복 검사 규칙을 helper로 추출할 때

주문 service 안에 `if (repository.existsByOrderNumber(...))`가 길게 박혀 있고, 이를 `DuplicateOrderGuard` 같은 helper로 빼고 싶다고 해 보자.

| 항목 | 선택 |
|---|---|
| 바뀌는 것 | 중복 검사 코드 위치와 이름 |
| 먼저 보호할 질문 | `같은 주문번호가 이미 있으면 저장 전에 실패하는가` |
| 가장 싼 첫 failing test | `unit test` |
| 먼저 고를 double | fake repository |
| 처음 피할 선택 | mock repository로 `existsBy...` 호출 순서부터 검증 |

이 장면은 호출 순서보다 **결과 규칙**이 먼저다. fake repository에 이미 저장된 주문 하나를 넣고 `DuplicateOrderNumberException`만 먼저 잠그면, helper 추출과 메서드 이름 변경이 구현 상세에 덜 묶인다.

## 시나리오 2: 할인 계산기를 service 밖으로 분리할 때

`OrderService` 안에서 VIP, 신규회원, 쿠폰 조건이 한 메서드에 섞여 있어 `DiscountPolicy`나 `PriceCalculator`로 빼고 싶을 수 있다.

| 항목 | 선택 |
|---|---|
| 바뀌는 것 | 계산 책임의 위치 |
| 먼저 보호할 질문 | `같은 입력이면 최종 금액이 그대로 계산되는가` |
| 가장 싼 첫 failing test | `unit test` |
| 먼저 고를 double | stub discount policy 또는 stub membership grade source |
| 처음 피할 선택 | spy/mock으로 내부 helper 호출 횟수까지 고정 |

이 장면에서 읽고 싶은 것은 "`VIP면 15%`" 같은 **값 결과**다. 그래서 collaborator가 복잡해도 먼저는 고정된 답을 돌려주는 stub이 싸다. spy나 mock으로 `calculate()` 호출 횟수까지 잠가 버리면, 계산기 추출 뒤 작은 구조 변경에도 테스트가 불필요하게 흔들린다.

## 시나리오 3: 저장, 승인, 알림 순서를 다시 배치할 때

처음에는 `save -> approve -> notify`였는데, 승인 실패 시 저장이 남는 문제가 있어 `approve -> save -> notify` 또는 `save + tx -> after-commit notify`로 재배치하는 경우가 있다.

| 항목 | 선택 |
|---|---|
| 바뀌는 것 | 협력 순서와 트랜잭션 경계 |
| 먼저 보호할 질문 | `승인 실패 시 주문이 남지 않는가` 또는 `성공 시 알림이 1번만 나가는가` |
| 가장 싼 첫 failing test | 롤백 위험이 크면 `app integration test`, 알림 1회 보장이 핵심이면 `unit test` |
| 먼저 고를 double | fake payment client 또는 spy notifier |
| 처음 피할 선택 | mock repository만으로 롤백을 대신 증명 |

여기서는 "service라서 통합 테스트"가 아니라 **실패가 어디서 보이는가**가 기준이다. 저장 잔존 여부는 실제 트랜잭션과 repository 협력을 붙여야 드러나는 경우가 많아서 integration이 먼저일 수 있다. 반대로 `after-commit 뒤 notifier가 한 번만 호출되나`가 질문이면 spy notifier를 둔 unit/integration 보조 테스트가 더 싸다.

## 흔한 오해와 함정

- "`service refactor`니까 항상 `unit test`부터죠?"  
  아니다. 트랜잭션 경계가 위험의 핵심이면 integration이 더 싸다.
- "double은 하나만 정답인가요?"  
  아니다. 같은 service 안에서도 repository 질문은 fake, notifier 질문은 spy가 더 자연스러울 수 있다.
- "mock으로 더 자세히 검증하면 더 안전한가요?"  
  보통은 아니다. 첫 failing test는 구조 자유도를 남겨야 하므로, 결과를 읽을 수 있으면 상호작용 고정부터 하지 않는 편이 낫다.

## 더 깊이 가려면

- [리팩토링과 첫 failing test 연결 브리지](./refactoring-first-failing-test-bridge.md): 리뷰 문장을 `질문 1개`로 줄이는 starter가 먼저 필요할 때
- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md): 결과 질문과 호출 질문을 더 짧게 가를 때
- [테스트 전략 기초](./test-strategy-basics.md): unit, `@WebMvcTest`, `@DataJpaTest`, `@SpringBootTest` 중 어디까지 넓힐지 다시 고를 때
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md): integration test를 언제 실제로 붙여야 하는지 프레임워크 관점까지 이어 볼 때

## 한 줄 정리

service 리팩터링의 첫 pass는 "`바뀐 장면 1개 -> 먼저 보호할 질문 1개 -> 가장 싼 테스트 1개 -> 그 질문에 맞는 double 1개`"로 줄일수록 안전해진다.
