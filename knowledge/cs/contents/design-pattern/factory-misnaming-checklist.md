---
schema_version: 3
title: Factory Misnaming Checklist
concept_id: design-pattern/factory-misnaming-checklist
canonical: true
category: design-pattern
difficulty: beginner
doc_role: playbook
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- factory-misnaming
- selector-registry-resolver
- naming-review
aliases:
- factory misnaming checklist
- create free factory
- factory without create
- factory naming smell checklist
- code review factory name
- selector vs factory review checklist
- registry vs factory review checklist
- resolver vs factory review checklist
- 생성 없는 factory
- factory 이름 오해
symptoms:
- Factory라는 이름을 붙였지만 실제 public 책임은 새 객체 생성이 아니라 이미 등록된 구현 lookup이다
- 런타임에 후보를 고른다는 이유만으로 Selector, Registry, Resolver 책임까지 모두 Factory라고 부른다
- create 책임과 select/get/resolve 책임이 한 클래스에 섞여 code review에서 이름만으로 기대가 어긋난다
intents:
- troubleshooting
- design
- definition
prerequisites:
- design-pattern/factory
- design-pattern/strategy-pattern
- design-pattern/registry-pattern
next_docs:
- design-pattern/router-dispatcher-handlermapping-vs-selector-factory
- design-pattern/bridge-strategy-vs-factory-runtime-selection
- design-pattern/policy-registry-pattern
linked_paths:
- contents/design-pattern/factory.md
- contents/design-pattern/strategy-pattern.md
- contents/design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist.md
- contents/design-pattern/factory-basics.md
- contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
- contents/design-pattern/bean-name-vs-domain-key-lookup.md
- contents/design-pattern/router-dispatcher-handlermapping-vs-selector-factory.md
- contents/design-pattern/registry-pattern.md
confusable_with:
- design-pattern/router-dispatcher-handlermapping-vs-selector-factory
- design-pattern/bridge-strategy-vs-factory-runtime-selection
- design-pattern/registry-pattern
- design-pattern/strategy-pattern
forbidden_neighbors: []
expected_queries:
- create 없는 Factory 이름은 왜 Selector, Registry, Resolver 중 하나로 바꾸는 게 더 정확할 수 있어?
- Map에서 이미 주입된 PaymentPolicy를 꺼내는 클래스는 Factory보다 Registry나 Selector에 가까운 이유가 뭐야?
- 런타임 선택이 있다고 해서 항상 Factory가 아닌 이유를 code review checklist로 설명해줘
- Factory, Selector, Registry, Resolver는 만들기, 고르기, 찾기, 해석하기 관점에서 어떻게 달라?
- public method가 새 객체를 생성하는지 이미 있는 객체를 반환하는지 Factory naming에서 왜 중요해?
contextual_chunk_prefix: |
  이 문서는 Factory Misnaming Checklist playbook으로, Factory라는 이름이 새 객체 생성 책임을
  약속한다는 전제에서 create가 없는 lookup/selection/resolution 클래스를 Selector, Registry,
  Resolver로 가르는 code review 질문을 제공한다.
---
# Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기

> 한 줄 요약: `Factory`라는 이름은 "새로 만들어 준다"는 약속이다. 그런데 코드가 이미 있는 객체를 고르거나 찾거나 해석만 한다면, 이름이 책임을 과장하고 있을 가능성이 크다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [팩토리 (Factory) 디자인 패턴](./factory.md)
> - [전략 패턴이란 무엇인가: 런타임에 구현을 바꾸는 방법](./strategy-pattern.md)
> - [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
> - [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
> - [팩토리 패턴 기초](./factory-basics.md)
> - [런타임 선택에서 Bridge vs Strategy vs Factory: 행동 축과 생성 축을 헷갈리지 않기](./bridge-strategy-vs-factory-runtime-selection.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](./router-dispatcher-handlermapping-vs-selector-factory.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: factory misnaming checklist, create free factory, factory without create, factory naming smell checklist, code review factory name, refactoring discussion factory rename, selector vs factory review checklist, registry vs factory review checklist, resolver vs factory review checklist, create 없는 factory, factory 이름 오해 체크리스트, factory 이름 잘못 붙였는지, 생성 없는 factory, beginner factory naming checklist, factory misnaming checklist basics

---

## 먼저 머릿속 그림

`Factory`는 공장이다.
읽는 사람은 이름만 보고도 "여기서 뭔가를 새로 만들겠구나"를 기대한다.

그래서 code review에서 제일 먼저 보는 질문은 하나다.

**이 클래스가 정말 새 객체를 만들고 있나, 아니면 이미 있는 것을 고르거나 찾기만 하나?**

짧게 외우면 이렇다.

- 새로 만들면 `Factory`
- 후보를 고르면 `Selector`
- 이미 등록된 것을 찾으면 `Registry`
- 입력을 뜻 있는 값으로 풀면 `Resolver`

---

## 30초 리뷰 표

| 코드에서 보이는 모습 | 더 의심해야 할 점 | 더 자연스러운 이름 |
|---|---|---|
| `Map<Key, Policy>`에서 꺼내 그대로 반환 | 새 객체 생성이 아니라 lookup이다 | `Registry`, `Selector` |
| injected bean 목록에서 조건에 맞는 구현을 고름 | creation보다 runtime 선택이 중심이다 | `Selector` |
| 문자열/코드값을 enum이나 handler key로 바꿈 | 입력 해석 규칙이 중심이다 | `Resolver` |
| `Map<Key, Supplier<T>>`를 찾은 뒤 `get()`으로 새 객체를 만듦 | creator lookup 뒤 실제 생성이 있다 | `Factory` |
| credentials, timeout, collaborator를 조립해 client를 만듦 | 조립과 생성 복잡도를 숨긴다 | `Factory` |

핵심은 내부 구현이 아니라 **public 책임**이다.
안에서 `Map`을 쓰든 `switch`를 쓰든, 바깥에서 보이는 일이 생성이 아니면 `Factory`는 과한 이름일 수 있다.

여기서 한 번 더 자르면 정리가 빨라진다.

- 선택된 정책을 실행하는 쪽이 중심이면 [전략 패턴](./strategy-pattern.md)
- 런타임 선택, 생성, 두 변화 축이 한꺼번에 섞이면 [Bridge vs Strategy vs Factory](./bridge-strategy-vs-factory-runtime-selection.md)
- request를 어느 handler로 넘길지 묻는 문제면 [Request Dispatch Naming](./router-dispatcher-handlermapping-vs-selector-factory.md)

---

## 빠른 리뷰 체크리스트

리뷰에서 아래 여섯 질문만 보면 대부분 바로 정리된다.

1. public 메서드가 매 호출마다 **새 객체**를 반환하는가?
2. 생성자 파라미터 조립, 의존성 연결, 초기화 같은 **생성 복잡도**를 이 클래스가 숨기는가?
3. 이미 주입되었거나 미리 만들어진 객체를 **그대로 골라서** 반환하는가?
4. raw input이나 alias를 domain key로 **해석**하는 일이 중심인가?
5. 주문 상태, 결제 수단, 요청 조건을 보고 **어떤 후보를 쓸지 결정**하는가?
6. key로 등록된 값을 **찾아오기만** 하는가?

판단은 이렇게 내리면 된다.

- `1`, `2`가 중심이면 `Factory`
- `3`, `5`가 중심이면 `Selector`
- `6`이 중심이면 `Registry`
- `4`가 중심이면 `Resolver`

리뷰 코멘트를 짧게 남기려면 이 한 줄이면 충분하다.

**"이 클래스는 create보다 select/get/resolve가 중심이라 `Factory`보다 다른 이름이 책임을 더 정확히 보여 줍니다."**

---

## 예시: `PaymentPolicyFactory`가 사실은 create-free인 경우

```java
public final class PaymentPolicyFactory {
    private final Map<PaymentMethod, PaymentPolicy> policies;

    public PaymentPolicy get(PaymentMethod method) {
        PaymentPolicy policy = policies.get(method);
        if (policy == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return policy;
    }
}
```

이 클래스는 이름과 달리 공장처럼 보이지 않는다.

- `new PaymentPolicy(...)`가 없다
- 조립 단계가 없다
- 이미 준비된 정책 중 하나를 key로 찾는다

그래서 보통은 아래 둘 중 하나가 더 맞다.

```java
public final class PaymentPolicyRegistry {
    private final Map<PaymentMethod, PaymentPolicy> policies;

    public PaymentPolicy get(PaymentMethod method) {
        PaymentPolicy policy = policies.get(method);
        if (policy == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return policy;
    }
}
```

```java
public final class PaymentPolicySelector {
    private final PaymentPolicyRegistry registry;

    public PaymentPolicy select(PaymentMethod method) {
        return registry.get(method);
    }
}
```

- key lookup만 드러내고 싶으면 `Registry`
- 조건 판단까지 드러내고 싶으면 `Selector`

---

## refactoring discussion에서 바로 쓰는 질문

이름을 바꿀지, 책임을 나눌지 애매할 때는 아래 질문을 던지면 대화가 빨라진다.

- "이 클래스가 새 객체를 만들지 않는데 `Factory`라는 이름이 호출자 기대를 과하게 만들지 않나요?"
- "이건 생성 책임인가요, 아니면 선택/조회 책임인가요?"
- "지금 필요한 건 rename만인가요, 아니면 `Selector`와 `Registry`를 분리해야 하나요?"
- "주입된 후보를 고르는 코드라면 `Factory`보다 `Selector`나 `Registry`가 테스트와 리뷰에서 더 읽기 쉽지 않나요?"

이 질문의 목적은 패턴 용어 맞히기가 아니다.
**이름 때문에 생성 문제와 선택 문제를 섞고 있지 않은지 빨리 드러내는 것**이다.

## 흔한 혼동

- **"런타임에 고르니까 Factory 아닌가요?"**
  - 아니다. 런타임 선택은 `Selector`, `Registry`, `Resolver`에서도 일어난다. `Factory` 여부는 생성 책임으로 본다.
- **"`get()`만 있어도 내부에서 복잡한 판단을 하면 Factory 아닌가요?"**
  - 판단이 복잡해도 새 객체를 만들지 않으면 보통 selection 문제에 더 가깝다.
- **"rename만 하면 끝인가요?"**
  - 이름만 틀린 경우도 있고, 선택과 조회가 한 클래스에 섞여 있으면 `Selector`와 `Registry`를 나누는 편이 더 낫다.

## 한 줄 정리

`Factory`라는 이름을 봤는데 create가 없다면, 먼저 "만드나 / 고르나 / 찾나 / 푸나"를 묻자. 그 네 질문만으로 대부분의 misnaming을 code review 단계에서 바로 잡을 수 있다.
