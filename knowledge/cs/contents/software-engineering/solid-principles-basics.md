---
schema_version: 3
title: SOLID 원칙 기초 (SOLID Principles Basics)
concept_id: software-engineering/solid-principles-basics
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- mixed-responsibility
- open-closed-branch-growth
- dependency-inversion-basics
- interface-segregation
aliases:
- solid principles basics
- solid 원칙 입문
- single responsibility
- open closed
- liskov substitution
- interface segregation
- dependency inversion
- srp 뭐예요
- 의존 역전 원칙
- 인터페이스 분리 원칙
symptoms:
- SOLID 다섯 원칙이 각각 어떤 문제를 막는지 연결이 안 돼요
- DIP와 DI를 같은 말로 이해하고 있었어요
- 클래스가 많아지면 무조건 SOLID를 잘 지킨 건지 헷갈려요
intents:
- definition
- comparison
- design
prerequisites: []
next_docs:
- software-engineering/solid-failure-patterns
- software-engineering/architecture-layering-fundamentals
- design-pattern/strategy-pattern
linked_paths:
- contents/software-engineering/solid-failure-patterns.md
- contents/software-engineering/architecture-layering-fundamentals.md
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/dependency-injection-basics.md
- contents/design-pattern/strategy-pattern.md
confusable_with:
- software-engineering/dependency-injection-basics
- software-engineering/architecture-layering-fundamentals
- design-pattern/strategy-pattern
forbidden_neighbors: []
expected_queries:
- SOLID를 처음 배울 때 다섯 원칙을 각각 어떤 질문으로 이해하면 돼?
- DIP와 DI 차이를 초심자 기준으로 설명해 줘
- SRP를 메서드 하나짜리 클래스로 오해하지 않으려면 무엇을 봐야 해?
- 요구사항이 늘 때 if 분기가 계속 커지는 코드가 OCP 위반인지 어떻게 판단해?
- SOLID가 왜 변경 비용을 줄이는 이야기인지 예시로 연결해 줘
contextual_chunk_prefix: |
  이 문서는 SOLID를 암기표가 아니라 변경 이유를 분리하는 다섯 가지 진단
  질문으로 이해하려는 초심자를 위한 primer다. SRP, OCP, LSP, ISP, DIP가
  각각 어떤 코드 냄새와 연결되는지, DIP와 DI를 어떻게 구분하는지, 원칙을
  과하게 적용하면 왜 오히려 복잡해지는지 설명하는 문서라는 맥락을 각 청크
  앞에 붙인다.
---
# SOLID 원칙 기초 (SOLID Principles Basics)

> 한 줄 요약: SOLID는 코드가 커져도 바꾸기 쉽게 만들기 위한 다섯 가지 설계 지침이고, 각 글자가 "왜 이 구조가 필요한가"에 대한 독립적 답을 준다.

**난이도: 🟢 Beginner**

관련 문서:

- [SOLID Failure Patterns](./solid-failure-patterns.md)
- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
- [design-pattern 카테고리 인덱스](../design-pattern/README.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: solid principles basics, solid 원칙 입문, single responsibility, open closed, liskov substitution, interface segregation, dependency inversion, srp 뭐예요, solid 5원칙 설명, 의존 역전 원칙, 인터페이스 분리 원칙, beginner solid, solid 왜 쓰나요, solid principles basics basics, solid principles basics beginner

## 먼저 잡는 한 줄 멘탈 모델

SOLID는 원칙 이름 암기표가 아니라, **"변경 이유를 한곳에 모으기 위한 분리 체크리스트"**다.

## before / after 한눈 비교

| 상태 | 코드 신호 | 결과 |
|---|---|---|
| before: 책임이 섞인 설계 | 하나의 서비스가 검증/저장/알림/정책 분기까지 모두 처리 | 작은 요구 변경도 여러 곳 동시 수정이 필요해진다 |
| after: SOLID 기준 분리 | 규칙(도메인), 유스케이스 조합(서비스), 저장 구현(리포지토리/어댑터)을 나눔 | 정책 추가나 저장소 교체 시 수정 범위가 줄고 테스트가 빨라진다 |

## 핵심 개념

SOLID는 객체지향 설계에서 자주 쓰는 다섯 가지 원칙의 머릿글자다.

- **S** — Single Responsibility: 클래스는 하나의 변경 이유만 가져야 한다
- **O** — Open/Closed: 확장에는 열려 있고 수정에는 닫혀 있어야 한다
- **L** — Liskov Substitution: 하위 타입은 상위 타입을 대체할 수 있어야 한다
- **I** — Interface Segregation: 사용하지 않는 메서드를 강요해서는 안 된다
- **D** — Dependency Inversion: 추상에 의존하고, 구체에 직접 의존하지 않는다

이 다섯 개는 "외워야 하는 규칙"이 아니라, 코드가 커질수록 왜 불편해지는지를 설명하는 진단 언어다.

## 한눈에 보기

| 원칙 | 핵심 질문 | 위반 신호 |
|---|---|---|
| SRP | 이 클래스가 바뀌는 이유가 두 개 이상인가? | 서비스에 저장, 알림, 검증이 섞임 |
| OCP | 새 요구사항이 기존 코드 수정으로 이어지는가? | `if (type == A)` 분기가 계속 늘어남 |
| LSP | 하위 클래스가 상위 계약을 깨지 않는가? | override 후 예외 던지거나 동작 반전 |
| ISP | 이 인터페이스에 필요 없는 메서드가 있는가? | 구현 클래스가 빈 메서드를 억지로 채움 |
| DIP | 구체 구현에 직접 의존하는가? | `new JdbcOrderRepository()`를 서비스에서 직접 생성 |

## 상세 분해

**S — 단일 책임 원칙**

"주문 서비스"가 주문 저장, 이메일 발송, 재고 차감을 모두 담당하면, 이메일 발송 방식이 바뀔 때 주문 저장 코드를 같이 열어야 한다. 책임을 분리하면 변경 이유가 각자에게 모인다.

**O — 개방/폐쇄 원칙**

할인 정책이 늘어날 때마다 `if` 분기를 추가하는 대신, `DiscountPolicy` 인터페이스를 두고 새 정책을 새 클래스로 추가하면 기존 코드를 건드리지 않아도 된다.

**L — 리스코프 치환 원칙**

`List<Animal>`에 `Dog`와 `Cat`을 넣고 `makeSound()`를 호출할 때, 어떤 동물이 들어와도 계약이 깨지지 않아야 한다. 상위 타입에서 기대하는 동작을 하위 타입이 파괴하면 안 된다.

**I — 인터페이스 분리 원칙**

`Worker` 인터페이스에 `work()`와 `eat()` 메서드가 있는데, 로봇은 `eat()`이 필요 없다. 인터페이스를 용도별로 나누면 구현 클래스가 불필요한 계약에 묶이지 않는다.

**D — 의존 역전 원칙**

서비스가 `JdbcOrderRepository`를 직접 생성하면 DB를 바꿀 때 서비스 코드도 바꿔야 한다. `OrderRepository` 인터페이스를 사이에 두면, 서비스는 추상에 의존하고 구현은 외부에서 주입된다.

## 흔한 오해와 함정

- "SOLID는 처음부터 모두 지켜야 한다"는 오해가 있다. 작은 코드에서 억지로 인터페이스를 만들면 오히려 복잡해진다. 변경 압력이 생기는 지점에서 원칙을 도입하는 게 자연스럽다.
- SRP를 "클래스가 메서드를 하나만 가져야 한다"로 오해하기도 한다. 핵심은 메서드 수가 아니라 변경 이유가 하나인지다.
- DIP를 "인터페이스만 쓰면 된다"로 좁히는 경우도 많다. 핵심은 고수준 모듈이 저수준 구현에 의존하지 않도록 방향을 역전하는 것이다.

## 실무에서 쓰는 모습

Spring 애플리케이션을 예로 들면, `OrderService`가 `OrderRepository`(인터페이스)에 의존하고 실제 구현은 `JpaOrderRepository`로 주입되는 구조가 DIP의 전형적 모습이다.

OCP는 결제 수단 추가 시 자주 나타난다. `PaymentStrategy` 인터페이스를 두고 `CardPayment`, `AccountTransferPayment` 를 각각 구현하면, 새 수단을 추가할 때 기존 클래스를 수정하지 않아도 된다.

## 더 깊이 가려면

- [SOLID Failure Patterns](./solid-failure-patterns.md) — 각 원칙 위반이 실제 코드에서 어떤 모습으로 나타나는지
- [design-pattern 전략 패턴](../design-pattern/strategy-pattern.md) — OCP와 DIP를 코드로 연결하는 대표 패턴

## 면접/시니어 질문 미리보기

- "SRP와 OCP가 충돌하는 경우가 있나요?" — SRP를 지키면서 분리한 클래스가 많아지면 OCP 적용 기회가 오히려 늘어난다. 둘은 보완 관계다.
- "DIP와 DI(의존성 주입)은 같은 말인가요?" — DIP는 원칙(방향), DI는 그 원칙을 구현하는 기법 중 하나다. Spring IoC 컨테이너가 DI를 통해 DIP를 실현해준다.
- "인터페이스가 없는 클래스는 SOLID를 어기는 건가요?" — 꼭 그렇지 않다. 변경 이유가 하나이고 의존 역전 필요성이 없다면 인터페이스가 없어도 SOLID를 잘 지키는 설계일 수 있다.

## 한 줄 정리

SOLID는 "어떻게 나눌까"가 아니라 "왜 이 경계가 필요한가"를 묻는 다섯 가지 진단 기준이다.
