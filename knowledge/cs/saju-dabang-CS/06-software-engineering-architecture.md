# 06. 소프트웨어 공학: 설계와 분리

## CS-study와 연결

- 소프트웨어 공학: `/Users/idonghun/IdeaProjects/woowa-2026/knowledge/cs/CS-study/contents/software-engineering/README.md`
- 디자인 패턴: `/Users/idonghun/IdeaProjects/woowa-2026/knowledge/cs/CS-study/contents/design-pattern/README.md`

## 1. 왜 `app`과 `server-java`를 분리했나

사주다방은 프론트와 백엔드의 책임이 다르다.

- 프론트: 사주 계산, UI, 사용자 상호작용
- 백엔드: 인증, 결제, 영속화, 비동기 생성, 복구

이건 기본적인 **관심사 분리**다.

## 2. 계층 분리

Java 백엔드는 대략 이런 계층을 가진다.

- api/controller
- application service
- infra/persistence
- domain model

이 구조는 면접에서 말하는:

- layered architecture
- port and adapter
- dependency direction control

와 연결된다.

## 3. `BillingPort`는 왜 중요한가

사주다방은 reading과 billing이 연결되어 있다.

예:

- 운세 생성 전에 코인 reserve
- 성공 시 capture
- 실패 시 refund

하지만 reading 코드가 billing 내부 구현을 직접 알면 결합도가 높아진다.

그래서:

- `ReadingReservationApplicationService`
- `ReadingFinalizationApplicationService`
- `BillingPort`

같은 구조를 사용한다.

이건 DIP(의존성 역전 원칙)를 실제 코드에서 구현한 예다.

## 4. 왜 `transactions`와 `coin_ledger`를 따로 뒀나

이건 데이터 모델링이면서 동시에 소프트웨어 공학 문제다.

- 하나로 합치면 단순해 보이지만
- 역할이 다르면 결국 코드가 더 꼬인다

즉 “하나의 테이블/모듈이 너무 많은 책임을 가지지 않도록 나누는 것”은
SRP와도 연결된다.

## 5. 아카이브 전략 자체도 소프트웨어 공학이다

이번에 Node 백엔드를 바로 삭제하지 않고:

- `archive/legacy-node-api/`
- `archive/legacy-node-docs/`

로 옮겼다.

이건 실무적으로:

- 레거시를 참고 가능하게 남기고
- 현재 기준선을 명확히 하면서
- 한 번에 깨끗이 교체하는 방법

즉 **리팩터링/마이그레이션 전략**도 소프트웨어 공학이다.

## 6. 면접 답변 예시

**Q. 객체지향 설계를 어디에 적용했나요?**  
A. “사주다방 Java 백엔드에서는 controller, application service, persistence를 분리하고, reading과 billing은 `BillingPort`로 연결했습니다. 이렇게 해서 비즈니스 흐름은 유지하면서도 구현 결합도를 낮췄습니다.”

**Q. 좋은 설계란 무엇이라고 생각하나요?**  
A. “현재 요구사항뿐 아니라 실패, 재시도, 교체 가능성까지 버틸 수 있는 설계라고 생각합니다. 사주다방에선 결제, queue, 복구 때문에 이 점이 특히 중요했습니다.”
