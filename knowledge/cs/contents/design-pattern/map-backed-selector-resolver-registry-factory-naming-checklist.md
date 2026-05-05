---
schema_version: 3
title: 'Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`'
concept_id: design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist
canonical: false
category: design-pattern
difficulty: beginner
doc_role: bridge
level: beginner
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- naming-responsibility-drift
- factory-overuse
aliases:
- map backed naming checklist
- selector resolver registry factory naming
- map class naming checklist
- factory or registry naming checklist
- 맵 기반 클래스 이름
- handler map 이름 짓기
- selector resolver registry factory 차이
intents:
- comparison
- design
symptoms:
- map으로 구현했는데 클래스 이름을 뭘로 지어야 할지 모르겠어요
- 새로 안 만드는데 factory라고 불러도 되는지 헷갈려요
prerequisites:
- design-pattern/factory-selector-resolver-beginner-entrypoint
next_docs:
- design-pattern/strategy-policy-selector-naming
linked_paths:
  - contents/design-pattern/strategy-policy-selector-naming.md
  - contents/design-pattern/registry-primer-lookup-table-resolver-router-service-locator.md
  - contents/design-pattern/registry-vs-factory-injected-handler-maps.md
  - contents/design-pattern/factory-vs-di-container-wiring.md
  - contents/design-pattern/bean-name-vs-domain-key-lookup.md
  - contents/design-pattern/injected-registry-vs-service-locator-checklist.md
  - contents/software-engineering/dependency-injection-basics.md
confusable_with:
  - design-pattern/strategy-policy-selector-naming
  - design-pattern/registry-vs-factory-injected-handler-maps
forbidden_neighbors: []
expected_queries:
- map 기반 클래스 이름을 selector resolver registry factory 중 뭐로 지어야 해?
- 새로 안 만드는데 factory라고 불러도 돼?
- handler map 이름 짓기 기준을 체크리스트로 보고 싶어
- selector와 registry가 둘 다 map lookup처럼 보일 때 어떻게 구분해?
- Map<String, Handler> 같은 클래스 이름을 Registry로 볼지 Selector로 볼지 판단 기준이 궁금해
- create 없이 주입된 객체만 고르는 클래스에 Factory 이름을 쓰면 왜 어색한지 설명해줘
contextual_chunk_prefix: |
  이 문서는 학습자가 Map<Key, ...> 형태의 클래스를 만났을 때 공개 책임을
  기준으로 selector, resolver, registry, factory 이름을 고르게 돕는 beginner
  bridge다. map naming checklist, 새로 안 만드는데 factory, lookup만 하는데
  registry인가, 문자열 해석이면 resolver인가 같은 자연어 질문이 본 문서의
  비교표와 체크리스트에 매핑된다.
---

# Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`

> 한 줄 요약: 같은 `Map<Key, ...>`를 써도 이름은 자료구조가 아니라 **공개 책임**으로 붙인다. 입력을 풀면 `Resolver`, 후보를 고르면 `Selector`, 이미 있는 것을 찾으면 `Registry`, 새로 만들면 `Factory`다.

**난이도: 🟢 Beginner**

관련 문서:

- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
- [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
- [Bean Name vs Domain Key Lookup](./bean-name-vs-domain-key-lookup.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: map backed naming checklist, map class naming beginner, factory or registry naming, selector or resolver naming, 처음 배우는데 이름 뭘로 지어야 해, 이름 뭘로 지어야 해, factory로 불러도 돼, 새로 안 만드는데 factory, lookup만 하는데 registry인가요, 문자열 해석이면 resolver인가요, 조건 보고 고르면 selector인가요, 처음 배우는데 factory 언제 써요, 맵 기반 클래스 이름, handler map 이름 짓기, selector resolver registry factory 차이

---

## 먼저 머릿속 그림

`Map`은 그냥 선반이다.
이름은 선반 모양이 아니라 **그 선반 앞에서 무슨 질문에 답하느냐**로 정한다.

- **Resolver**: "이 입력을 무슨 의미로 해석해야 하지?"
- **Selector**: "후보들 중 지금 무엇을 써야 하지?"
- **Registry**: "이 key에 등록된 것은 무엇이지?"
- **Factory**: "지금 새로 무엇을 만들어야 하지?"

짧게 외우면 이 한 줄이면 된다.

**풀면 `Resolver`, 고르면 `Selector`, 찾으면 `Registry`, 만들면 `Factory`.**

---

## 30초 비교표

| 클래스가 주로 답하는 질문 | 더 자연스러운 이름 | 흔한 코드 모양 | `Factory`가 아닌 이유 |
|---|---|---|---|
| `"card"`, `"CARD"`, `"credit-card"`를 무엇으로 볼까 | `PaymentMethodResolver` | `resolve(rawCode)` | 새 객체 생성보다 입력 해석이 중심이다 |
| 주문 조건을 보고 어떤 정책을 써야 할까 | `DiscountPolicySelector` | `select(order)` | 후보 선택 규칙이 중심이다 |
| `PaymentMethod.CARD`에 등록된 핸들러는 무엇일까 | `PaymentHandlerRegistry` | `get(method)` | 이미 있는 객체를 key로 lookup한다 |
| provider별 client를 지금 새로 조립할까 | `PaymentClientFactory` | `create(provider)` | creator lookup 뒤에 실제 생성이 붙는다 |

핵심은 메서드 이름보다도 **호출자가 무엇을 기대하는가**다.

- "`입력을 해석해 줘`"를 기대하면 `Resolver`
- "`조건을 보고 골라 줘`"를 기대하면 `Selector`
- "`등록된 것 꺼내 줘`"를 기대하면 `Registry`
- "`새로 만들어 줘`"를 기대하면 `Factory`

---

## 예시 1. 입력 alias를 정규화하면 `Resolver`

```java
public final class PaymentMethodResolver {
    private final Map<String, PaymentMethod> aliases;

    public PaymentMethod resolve(String rawCode) {
        PaymentMethod method = aliases.get(rawCode.toLowerCase());
        if (method == null) {
            throw new IllegalArgumentException("unknown method: " + rawCode);
        }
        return method;
    }
}
```

여기서 중심은 lookup 그 자체보다도 `"credit-card"`를 `PaymentMethod.CARD`로 **풀어내는 규칙**이다.

## 예시 2. 최종 key로 기존 handler를 꺼내면 `Registry`

```java
public final class PaymentHandlerRegistry {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandler get(PaymentMethod method) {
        PaymentHandler handler = handlers.get(method);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return handler;
    }
}
```

여기서는 `method`가 이미 정리된 key다.
클래스는 그냥 **등록된 후보를 찾는 책임**만 가진다.

## 예시 3. 여러 조건으로 후보를 고르면 `Selector`

```java
public final class DiscountPolicySelector {
    private final DiscountPolicyRegistry registry;

    public DiscountPolicy select(Order order) {
        if (order.isVip()) {
            return registry.get(DiscountPolicyKey.VIP);
        }
        if (order.totalPrice() >= 100_000) {
            return registry.get(DiscountPolicyKey.BULK);
        }
        return registry.get(DiscountPolicyKey.DEFAULT);
    }
}
```

이 클래스는 key를 이미 받지 않는다.
주문 조건을 보고 **어떤 후보를 써야 할지 결정**하므로 `Selector`가 더 자연스럽다.

## 예시 4. creator를 고른 뒤 새 객체를 만들면 `Factory`

```java
public final class PaymentClientFactory {
    private final Map<PaymentProvider, Supplier<PaymentClient>> creators;

    public PaymentClient create(PaymentProvider provider) {
        Supplier<PaymentClient> creator = creators.get(provider);
        if (creator == null) {
            throw new IllegalArgumentException("unsupported provider: " + provider);
        }
        return creator.get();
    }
}
```

안쪽에 `Map` lookup이 있어도, 바깥 public 책임은 `PaymentClient`를 **새로 만드는 것**이다.
그래서 이때는 `Factory`가 맞다.

---

## 이름이 헷갈릴 때 바로 보는 체크리스트

아래 다섯 질문에 순서대로 답하면 대부분 바로 정리된다.

1. 호출자가 넘기는 값이 아직 지저분한 raw input인가?
2. 클래스가 여러 조건을 보고 "어떤 후보를 쓸지" 직접 판단하는가?
3. 호출자가 이미 최종 key를 알고 있고, 클래스는 등록된 값을 꺼내기만 하는가?
4. public 메서드의 최종 결과가 기존 객체 반환인가, 새 객체 생성인가?
5. `Map` 안의 값이 완성된 객체인가, `Supplier`/creator 같은 생성기인가?

판단은 이렇게 내리면 된다.

- raw input 해석이 중심이면 `Resolver`
- 조건 판단으로 후보 선택이 중심이면 `Selector`
- final key 기반 lookup이 중심이면 `Registry`
- creator lookup 뒤 새 객체 반환이 중심이면 `Factory`

---

## 흔한 혼동

- **"이름 뭘로 지어야 해요?"**
  - 먼저 `Map` 자체를 보지 말고, 호출자가 이 클래스에 기대하는 한 문장을 적는다. "해석해 줘"면 `Resolver`, "골라 줘"면 `Selector`, "꺼내 줘"면 `Registry`, "새로 만들어 줘"면 `Factory`다.
- **"런타임에 고르니까 `Factory` 아닌가요?"**
  - 아니다. 런타임 선택은 `Selector`, `Resolver`, `Registry`에서도 일어난다. `Factory` 여부는 생성 책임으로 본다.
- **"`Map.get(...)`을 쓰니까 무조건 `Registry` 아닌가요?"**
  - 아니다. 그 `Map`이 alias 해석에 쓰이면 `Resolver`, 조건 분기에 쓰이면 `Selector`가 더 정확할 수 있다.
- **"새로 안 만드는데 `Factory`로 불러도 돼요?"**
  - 보통은 아니다. 기존 객체를 key로 찾아 꺼내는 책임이면 `Registry` 쪽이 더 읽기 쉽다. `Factory`는 호출자가 "새 객체를 받겠다"라고 기대할 때 쓴다.
- **"`Map<Key, Supplier<T>>`면 무조건 `Factory`인가요?"**
  - 바깥 API가 `Supplier<T>`를 넘기기만 하면 creator registry일 수 있다. public API가 `T`를 새로 반환하면 `Factory`로 보는 편이 자연스럽다.
- **"`Selector`와 `Registry`는 왜 같이 두나요?"**
  - `Selector`는 "어떤 key를 쓸지"를 결정하고, `Registry`는 "그 key로 무엇이 등록됐는지"를 찾는다. 둘을 나누면 조건 판단과 단순 lookup이 섞이지 않는다.

## 한 줄 정리

`Map`은 구현 도구일 뿐이다. 이름은 `Map`의 존재가 아니라 **입력 해석(`Resolver`) / 후보 선택(`Selector`) / 등록 조회(`Registry`) / 새 객체 생성(`Factory`) 중 무엇을 public 책임으로 드러내야 하는가**로 정한다.
