# 팩토리 패턴 기초 (Factory Pattern Basics)

> 한 줄 요약: 팩토리 패턴은 객체를 어떻게 만들지를 호출자로부터 숨기고, 생성 책임을 한 곳에 모아 변경이 생겨도 호출 측 코드를 건드리지 않게 해준다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md) -> `[primer]` 이 문서 -> `[bridge]` [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)

관련 문서:

- [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [팩토리 (Factory) 심화](./factory.md)
- [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [OOP 설계 원칙 기초](../software-engineering/oop-design-basics.md)

retrieval-anchor-keywords: factory pattern basics, 팩토리 패턴 기초, 팩토리가 뭔가요, 팩토리 큰 그림, 팩토리 언제 쓰는지, 처음 배우는데 factory, new 대신 팩토리, creation vs selection, 생성 vs 선택, 새로 만들기 vs 고르기, factory vs static factory vs selector, selector is not factory, 생성 책임 vs 선택 책임, factory vs di container, 팩토리 패턴 30초 비교표

---

## 핵심 개념

팩토리 패턴은 **객체를 직접 `new`로 만드는 대신, 생성 책임을 별도 메서드나 클래스에 위임**하는 패턴이다. 호출자는 어떤 구현 클래스가 만들어지는지 알 필요 없이 원하는 타입의 객체를 받을 수 있다.

입문자가 자주 헷갈리는 것은 "그냥 `new` 쓰면 되는데 왜 팩토리를?"이다. 핵심은 **변경점 격리**다. 생성 로직이 여러 곳에 흩어지면, 구현 클래스 이름이나 생성자 시그니처가 바뀔 때 모든 호출 측을 수정해야 한다.

## 처음 배우는데 큰 그림부터

처음 배우는데 `Factory`가 `Selector`와 자꾸 섞이면, 용어보다 이 멘탈 모델을 먼저 잡으면 된다.

- `Factory`: 지금 새 객체를 만들고 조립하는 쪽
- `Selector`: 이미 있는 후보 중 맞는 것을 고르는 쪽
- `Static Factory`: 같은 타입 안에 둔 이름 있는 생성 입구

| 지금 떠오르는 질문 | 먼저 볼 개념 | 한 줄 기준 |
|---|---|---|
| "언제 팩토리를 써요?" | `Factory` | 생성 규칙이 퍼져서 한 곳에 모으고 싶을 때 |
| "새로 만들지 않고 고르기만 하는데요?" | `Selector` | 후보 선택이 중심이면 생성 패턴보다 선택 패턴 질문이다 |
| "`of()`나 `from()`도 factory인가요?" | `Static Factory` | 같은 타입 안의 이름 있는 생성 입구면 정적 팩토리다 |

처음 질문이 "생성이냐, 선택이냐" 자체라면 이 문서보다 [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)을 먼저 열어도 된다.

## 빠른 진입: 10초/30초/1분

처음 읽을 때는 `10초 질문 -> 30초 비교표 -> 1분 예시` 순서로만 훑는다.

### 10초 질문

아래 3줄만 먼저 체크한다.

1. 호출자가 구현 클래스 이름을 몰라도 되게 하고 싶은가?
2. 생성 규칙이 여러 파일에 흩어져 수정 범위가 자주 커지는가?
3. 지금 문제의 중심이 "어떤 객체를 만들까"인가? (단순 선택/조회면 selector나 registry를 먼저 본다)

3줄 중 2개 이상이 "예"라면 팩토리 패턴 후보로 본다.

### 30초 비교표

아래 표에서 지금 문제에 더 가까운 쪽을 먼저 고른다.

| 질문 | 생성자/정적 팩토리만 사용 | 팩토리 패턴 사용 |
|---|---|---|
| 생성 로직 위치 | 호출자마다 흩어질 수 있다 | 팩토리 한 곳에 모인다 |
| 구현체 교체 영향 | 호출자 코드도 함께 수정될 수 있다 | 팩토리 수정으로 범위를 줄일 수 있다 |
| 잘 맞는 상황 | 생성 규칙이 단순하고 변경이 적다 | 구현체 추가/교체가 반복된다 |

### 1분 예시

결제 수단 추가:

아래처럼 호출자는 동일하게 두고, 생성 책임만 한 곳에 모으는지 보면 된다.

초기에는 `CARD`, `CASH`만 있다고 하자. 호출자는 아래 한 줄만 사용한다.

`Payment payment = paymentFactory.create(method);`

`TOSS` 수단이 추가될 때 변경은 팩토리의 매핑 한 곳에 모인다.

| 변경 항목 | 호출자 | 팩토리 |
|---|---|---|
| `TOSS` 추가 전 | `create(method)` 호출 | `CARD/CASH` 분기 |
| `TOSS` 추가 후 | 그대로 유지 | `TOSS -> TossPayment` 분기 추가 |

핵심은 "새 구현 추가 diff를 생성 책임 위치 한 곳으로 모은다"는 점이다.

### 자주 헷갈리는 포인트 3개

- `if/switch`가 있다고 팩토리가 아닌 건 아니다. 핵심은 생성 책임이 한 곳에 모였는지다.
- `*Factory`라는 이름만으로는 부족하다. 실제로 `new`/생성 규칙을 가지지 않으면 selector/registry가 더 정확할 수 있다.
- DI 컨테이너가 wiring을 맡는 영역과 도메인 생성 규칙은 다르다. 컨테이너가 해결할 문제인지 먼저 분리한다.

## 한눈에 보기

```
호출자
  │  createPayment("CARD")
  ▼
PaymentFactory ──→ CardPayment (implements Payment)
               ──→ CashPayment (implements Payment)
```

| 역할 | 설명 |
|------|------|
| 팩토리 메서드 | 객체를 만들어 반환하는 메서드 |
| 공통 인터페이스 | 호출자가 실제 구현을 몰라도 되게 해줌 |
| 구현 클래스 | 팩토리 안에서만 `new` 됨 |

## 상세 분해

팩토리 패턴은 세 가지 형태로 나뉜다.

- **정적 팩토리 메서드** — `Payment.of("CARD")` 처럼 같은 클래스 안의 정적 메서드로 생성. 가장 단순하며 Java의 `List.of()`, `Optional.of()`가 이 형태다.
- **팩토리 메서드 패턴** — 부모 클래스에 `createProduct()` 추상 메서드를 두고, 서브클래스가 어떤 객체를 만들지 결정한다.
- **추상 팩토리 패턴** — 연관된 객체 군(예: 버튼 + 다이얼로그)을 묶어 함께 생성하는 인터페이스. 팩토리 메서드보다 범위가 넓다.

입문 단계에서는 정적 팩토리 메서드와 기본 팩토리 메서드 패턴만 이해해도 충분하다.

## 흔한 오해와 함정

- **"팩토리 = 무조건 별도 클래스"** — 정적 팩토리 메서드처럼 같은 클래스 안에 둬도 팩토리 패턴이다. 복잡도에 맞게 형태를 선택한다.
- **"팩토리 쓰면 객체가 항상 새로 만들어진다"** — 팩토리는 캐싱이나 풀링된 객체를 반환할 수도 있다. 호출자는 신경 쓸 필요 없다.
- **"if/switch로 분기하면 팩토리가 아니다"** — 초기에는 if/switch도 충분하다. 분기가 폭증하면 레지스트리 기반으로 리팩터한다.

## 실무에서 쓰는 모습

결제 수단마다 다른 처리 객체가 필요할 때, 팩토리 메서드 하나로 수단 코드를 받아 알맞은 구현체를 반환한다. 호출 측은 `Payment payment = PaymentFactory.create(method)` 처럼 사용하고, 새 수단이 추가되면 팩토리만 수정한다.

Spring에서는 `@Bean` 메서드가 팩토리 메서드 역할을 한다. 설정 클래스에서 객체를 만들고, 컨테이너가 그 객체를 필요한 곳에 주입한다. 다만 애플리케이션 wiring이 핵심이면 손으로 `*ServiceFactory`를 늘리기보다 컨테이너에 맡기는 편이 자연스럽다. 이 경계는 [Factory와 DI 컨테이너 Wiring](./factory-vs-di-container-wiring.md)에서 예시로 이어서 볼 수 있다.

## 프라이머 마지막 3문항 미니 혼동 점검

읽고 나서 아래 3개를 10초 안에 구분되면 첫 단계는 충분하다.

| 이름 | 가장 짧은 멘탈 모델 | 이런 질문이면 가깝다 |
|---|---|---|
| Factory | "무엇을 새로 만들지"를 숨긴다 | "어떤 구현 객체를 생성해 줄까?" |
| Static Factory | 클래스 안에 둔 "이름 있는 생성 입구"다 | "생성자는 숨기고 의도를 이름으로 드러낼까?" |
| Selector | 이미 있는 후보 중 "무엇을 고를지"를 정한다 | "새로 만들지 않고 맞는 것을 선택만 할까?" |

작은 예시로 보면 더 쉽다.

- `Money.of("1000")`는 정적 팩토리다. `Money`를 만드는 이름 있는 입구다.
- `PaymentFactory.create(method)`는 팩토리다. `method`에 따라 `CardPayment`나 `CashPayment`를 새로 만든다.
- `DiscountPolicySelector.select(customerType)`는 셀렉터다. 이미 등록된 정책 후보 중 하나를 고른다.

헷갈릴 때는 이 한 줄로 다시 자른다.

- 새 객체를 만들면 `Factory` 쪽이다.
- 같은 클래스 안의 이름 있는 생성 입구면 `Static Factory`다.
- 이미 있는 후보를 고르기만 하면 `Selector`다.

더 헷갈리면 [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)과 [Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림](./factory-selector-resolver-beginner-entrypoint.md)을 바로 이어서 읽는다.

## 더 깊이 가려면

- [팩토리 (Factory) 심화](./factory.md) — 팩토리 메서드 vs 추상 팩토리 경계, 언제 정적 팩토리만으로 충분한지
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md) — 세 가지 생성 패턴의 선택 기준 비교

## Quick-Check

처음 읽고 아래 3개가 바로 갈리면 이 문서의 목표는 달성한 것이다.

| 질문 | `예`면 가까운 쪽 | `아니오`면 먼저 볼 것 |
|---|---|---|
| 새 구현이 늘 때 호출자 수정 범위를 줄이고 싶은가? | `Factory` | 생성자/정적 팩토리 |
| 같은 클래스 안의 이름 있는 생성 입구가 필요한가? | `Static Factory` | 일반 생성자 |
| 새로 만들지 않고 이미 있는 후보만 고르는가? | `Selector` | `Factory`가 아닐 수 있음 |

## 면접/시니어 질문 미리보기

> Q: 정적 팩토리 메서드와 생성자의 차이는?
> 의도: 팩토리의 장점을 이해하는지 확인한다.
> 핵심: 이름을 줄 수 있고, 반환 타입이 유연하며, 캐싱이 가능하다.

> Q: 팩토리 패턴이 필요한 시점은 언제인가?
> 의도: 무조건 적용이 아니라 트레이드오프를 아는지 확인한다.
> 핵심: 구현 클래스를 숨겨야 하거나, 생성 로직이 여러 곳에 흩어질 때다.

> Q: Spring `@Bean` 메서드가 팩토리 패턴과 어떤 관계인가?
> 의도: 패턴과 프레임워크를 연결하는지 확인한다.
> 핵심: `@Bean` 메서드가 팩토리 메서드이며, Spring 컨테이너가 그 반환 객체를 관리한다.

## Confusion Box

| 헷갈리는 쌍 | 먼저 던질 질문 | 빠른 기준 |
|---|---|---|
| Factory vs Static Factory | "같은 클래스 안의 생성 입구인가?" | 같은 타입 안이면 `Static Factory`, 별도 생성 책임이면 `Factory` |
| Factory vs Selector | "새 객체를 만드는가, 후보를 고르는가?" | 생성이면 `Factory`, 선택이면 `Selector` |
| Factory vs DI Container | "애플리케이션 wiring 문제인가, 도메인 생성 규칙 문제인가?" | bean 조립은 컨테이너, 도메인 생성 규칙은 factory 쪽 |

## 한 줄 정리

팩토리 패턴은 `new` 호출을 한 곳에 모아 호출자가 구현 클래스를 몰라도 되게 하며, 새 구현 추가 시 팩토리만 수정하면 되는 구조를 만든다.
