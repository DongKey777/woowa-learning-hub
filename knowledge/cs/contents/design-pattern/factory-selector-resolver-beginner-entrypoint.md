---
schema_version: 3
title: 'Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림'
concept_id: design-pattern/factory-selector-resolver-beginner-entrypoint
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- factory selector resolver
- Factory vs Selector vs Resolver
- 생성 vs 선택 네이밍
- selector naming
- factory 이름 언제 쓰나
intents:
- comparison
- design
linked_paths:
- contents/design-pattern/registry-primer-lookup-table-resolver-router-service-locator.md
- contents/design-pattern/strategy-map-vs-registry-primer.md
- contents/design-pattern/factory-vs-di-container-wiring.md
- contents/design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist.md
confusable_with:
- design-pattern/strategy-pattern-basics
- design-pattern/registry-pattern
expected_queries:
- Factory랑 Selector, Resolver 이름은 어떻게 구분해?
- 새 객체를 만들지 않는데 Factory라고 불러도 돼?
- selector naming이 헷갈릴 때 처음 어디서 봐야 해?
- Map으로 하나 고르는 코드가 factory인지 selector인지 모르겠어
contextual_chunk_prefix: |
  이 문서는 객체를 새로 만드는 책임(Factory)과 이미 등록된 것 중 하나를
  고르는 책임(Selector / Resolver)이 이름에서 헷갈릴 때 학습자가 어느
  네이밍을 골라야 하는지 처음 만나는 chooser다. 새로 만들기 vs 고르기,
  생성 책임 vs 선택 책임, Factory vs Selector vs Resolver, Map<String,
  Strategy>를 selector라 불러야 하나 strategy라 불러야 하나 같은 자연어
  paraphrase가 본 문서의 분기 질문에 매핑된다.
---

# Factory vs Selector vs Resolver: 처음 배우는 네이밍 큰 그림

> 한 줄 요약: 이름을 붙이기 전에 먼저 질문을 고정한다. **"지금 새로 만들고 있나?"**면 `Factory`, 아니면 선택/해석 책임을 먼저 본다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` 이 문서 -> `[beginner bridge]` [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md) -> `[checklist]` [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md) -> `[deep dive]` [팩토리 (Factory)](./factory.md)

관련 문서:

- [팩토리 패턴 기초](./factory-basics.md)
- [Registry Pattern: 객체를 찾는 lookup table](./registry-pattern.md)
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
- [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](./factory-misnaming-checklist.md)
- [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: factory selector resolver beginner, factory vs selector vs resolver, factory selector resolver 차이, selector naming entrypoint, selector naming first hit, selector 이름 뭐로 지어야 해, creation vs selection naming, 생성 vs 선택 네이밍, 생성 책임 vs 선택 책임, 생성이 아니면 factory 아님, 처음 배우는데 factory selector resolver, 처음 배우는데 selector naming, factory 이름 언제 쓰는지, selector 이름 언제 쓰는지, factory selector resolver beginner entrypoint basics

---

## 먼저 10초 질문

처음 배우는데 이름이 헷갈리면, 패턴 용어보다 이 질문 하나를 먼저 본다.

**"이 클래스가 호출 시점에 새 객체를 만들고 조립하나?"**

- 예: provider별 client를 credentials/timeout과 함께 새로 조립한다 -> `Factory`
- 아니면 대부분 `Selector`/`Resolver` 쪽 질문이다
- 그런데 질문이 "검색 DTO도 repository가 만들까요?", "저장/조회 책임을 어디까지 두나요?"라면 naming보다 [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md) route가 먼저다

이 문서는 여기서 멈춘다. `Factory`/`Selector`/`Resolver` 네이밍 경계까지만 다루고, service locator drift나 read model 운영 이야기는 follow-up 문서로 넘긴다.

## `selector`로 검색했다면 여기서 먼저 자르기

처음 배우는데 `selector`라는 단어만 떠올라도, 바로 strategy deep dive로 내려가기보다 아래 큰 그림부터 잡는 편이 안전하다.

- raw 입력을 뜻으로 바꾸는 중이면 `Resolver`
- 이미 뜻이 정해진 후보 중 하나를 고르는 중이면 `Selector`
- 새 객체를 조립하는 중이면 `Factory`

`selector naming`, `selector 이름 언제 쓰는지`, `factory selector 차이` 같은 검색은 이 문서에서 먼저 끊고, 그다음 [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md)으로 내려가면 된다.

---

## 30초 비교표

| 지금 코드가 답하는 질문 | 더 맞는 이름 | 왜 `Factory`가 아닌가 |
|---|---|---|
| "이 raw 입력 코드를 어떤 도메인 값으로 풀까?" | `Resolver` | 입력 해석이 중심이다 |
| "조건을 보고 후보 중 무엇을 쓸까?" | `Selector` | 후보 선택이 중심이다 |
| "이 key에 등록된 객체는 무엇이지?" | `Registry` | 등록 lookup이 중심이다 |
| "지금 새 객체를 만들어 반환할까?" | `Factory` | 생성/조립이 중심이므로 factory가 맞다 |

짧게 외우면 이 한 줄이면 충분하다.

**해석은 `Resolver`, 선택은 `Selector`, 등록 lookup은 `Registry`, 생성은 `Factory`다.**

여기서 한 번 더 잘라야 할 예외가 있다.

- "주문 aggregate를 저장하나, 화면 목록을 조합하나"처럼 **저장/조회 경계**가 중심이면 `Factory`/`Selector`보다 repository/read model 질문이다
- 이 경우 첫 문서는 [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md), 다음 문서는 [Repository Boundary: Aggregate Persistence vs Read Model](./repository-boundary-aggregate-vs-read-model.md) 순서가 안전하다

---

## 1분 예시: 결제 흐름 네이밍 쪼개기

```java
PaymentMethod method = paymentMethodResolver.resolve(request.getMethodCode());
PaymentPolicy policy = paymentPolicySelector.select(order, method);
PaymentClient client = paymentClientFactory.create(method.getProvider());
```

- `paymentMethodResolver`: raw code를 도메인 의미로 해석
- `paymentPolicySelector`: 조건을 보고 후보 정책 선택
- `paymentClientFactory`: 선택된 provider 기준으로 새 client 생성

같은 흐름에 registry가 들어오면 역할은 이렇게 끊는다.

`paymentHandlerRegistry.get(method)`는 **이미 등록된 handler를 찾는 일**이고, `paymentClientFactory.create(provider)`는 **새 client를 만드는 일**이다.

즉 `get()` 중심이면 registry 후보, `create()` 중심이면 factory 후보로 먼저 본다.

이렇게 쪼개면 "생성 문제"와 "선택/해석 문제"가 섞이지 않는다.

여기서 strategy까지 같이 보면 경계가 더 또렷해진다.

```java
PaymentPolicy policy = paymentPolicySelector.select(order, method);
policy.apply(order);
```

- `paymentPolicySelector`: 이번 주문에 어떤 규칙 객체를 쓸지 **고른다**
- `PaymentPolicy`: 선택된 규칙으로 실제 계산/판단을 **실행한다**
- `paymentClientFactory`: 외부 provider client를 **새로 만든다**

즉 **선택은 selector, 실행 방식은 strategy/policy, 생성은 factory**로 자르면 "런타임에 고른다 = 다 factory"라는 오해를 줄일 수 있다.

---

## 자주 헷갈리는 포인트

- "런타임에 고르니까 factory 아닌가요?"
  - 아니다. 런타임 선택은 `Selector`/`Resolver`에서도 일어난다. factory 여부는 생성 책임으로 본다.
- "`Selector`와 `Strategy`는 같은 말 아닌가요?"
  - 아니다. selector는 **무엇을 쓸지 고르는 쪽**, strategy는 **선택된 방식으로 행동하는 쪽**이다.
- "`Map.get(...)`을 쓰면 다 registry 아닌가요?"
  - 아니다. raw 입력을 정규화하면 `Resolver`, 조건 분기면 `Selector`, 등록 lookup이면 `Registry`다.
- "`Map<Key, Handler>`면 factory라고 불러도 되나요?"
  - 보통 아니다. 새 객체를 만들지 않고 등록된 handler를 찾기만 하면 registry가 더 정확하다.
- "`create()` 메서드가 있으면 factory인가요?"
  - 이름보다 실제 책임을 본다. 기존 객체를 고르기만 하면 factory가 아니다.

이 단계에서 더 복잡한 분기까지 한 번에 잡으려 하지 않는 편이 좋다.

- `Map<Key, Strategy>`처럼 lookup과 행동 교체가 같이 보이면 [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)로 한 칸만 더 내려간다.
- `ApplicationContext.getBean(...)` 같은 숨은 조회 냄새가 보일 때만 [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)를 이어서 본다.
- repository/read model, CQRS, projection 같은 저장-조회 경계 질문은 이 문서 밖 범위다. 그때는 [Repository Pattern vs Anti-Pattern](./repository-pattern-vs-antipattern.md)부터 다시 잡는다.

---

## 다음 읽기 (언제 쓰는지 빠르게 이어가기)

- `Factory`를 언제 쓰는지 기초부터: [팩토리 패턴 기초](./factory-basics.md)
- `Factory` 남용을 리뷰에서 자르는 방법: [Factory Misnaming Checklist](./factory-misnaming-checklist.md)
- `Selector`/`Resolver`/`Registry`를 더 촘촘히 가르는 표: [Map-backed 클래스 네이밍 체크리스트](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- 정적 팩토리와 패턴 factory까지 함께 정리: [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)

## 한 줄 정리

큰 그림은 단순하다. 생성 책임이면 `Factory`, 그 전 단계의 해석/선택 책임이면 `Resolver`/`Selector`를 먼저 붙인다.
