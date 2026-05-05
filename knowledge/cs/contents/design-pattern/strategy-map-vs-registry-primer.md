---
schema_version: 3
title: 'Strategy Map vs Registry Primer: 같은 Map 모양인데 질문이 다르다'
concept_id: design-pattern/strategy-map-vs-registry-primer
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
aliases:
- strategy map vs registry
- Map<Key Strategy>
- strategy collection
- 행동 교체 vs keyed lookup
- 전략 맵 vs 레지스트리
intents:
- comparison
- design
linked_paths:
- contents/design-pattern/registry-primer-lookup-table-resolver-router-service-locator.md
- contents/design-pattern/factory-selector-resolver-beginner-entrypoint.md
- contents/design-pattern/strategy-pattern-basics.md
- contents/design-pattern/strategy-registry-vs-service-locator-drift.md
confusable_with:
- design-pattern/strategy-pattern-basics
- design-pattern/factory-selector-resolver-beginner-entrypoint
- design-pattern/registry-primer-lookup-table-resolver-router-service-locator
- design-pattern/policy-object-vs-strategy-map-beginner-bridge
expected_queries:
- Map<String, Strategy>는 registry야 strategy야?
- 같은 Map 모양인데 행동 교체와 단순 lookup을 어떻게 구분해?
- strategy map과 registry 차이를 처음 배우는데 어디서 봐?
- 전략 컬렉션을 selector라고 불러도 되는지 헷갈려
---

# Strategy Map vs Registry Primer: 같은 `Map` 모양인데 질문이 다르다

> 한 줄 요약: `Map<Key, ...>`를 쓴다고 다 같은 설계는 아니다. 같은 역할의 행동을 바꿔 끼우면 strategy collection이고, 이름표로 기존 객체나 정보를 찾기만 하면 plain registry다.

**난이도: 🟢 Beginner**

관련 문서:

- [전략 패턴 기초](./strategy-pattern-basics.md)
- [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
- [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
- [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: strategy map vs registry, map<string, strategy> beginner, strategy> registry인가요, strategy> selector인가요, 처음 배우는데 strategy map 큰 그림, strategy map 언제 쓰는지, strategy collection vs plain registry, 행동 교체 vs keyed lookup, 전략 맵 vs 레지스트리, 전략 컬렉션 vs 레지스트리, 등록된 것을 찾아온다 vs 어떻게 처리할지 고른다, strategy selector registry 차이, strategy map vs registry primer basics, strategy map vs registry primer beginner

---

## 이 문서는 언제 읽으면 좋은가

아래 질문이 나오면 이 비교 노트를 먼저 보면 된다.

- "`Map<PaymentMethod, PaymentStrategy>`도 결국 registry 아닌가요?"
- "`Map<String, Strategy>`인데 이걸 registry라고 불러야 해요, selector라고 불러야 해요?"
- "코드는 `get()`으로 꺼내는데 왜 strategy라고 부르죠?"
- "같은 `Map` 모양인데 어떤 때는 행동 교체고 어떤 때는 단순 lookup인지 헷갈립니다"
- "리뷰에서 strategy map, strategy registry, plain registry라는 말이 섞여서 나온다"

핵심은 자료구조보다 **무슨 질문에 답하고 있는가**다.

---

## 먼저 머릿속 그림을 자르자

같은 `Map<Key, X>`라도 질문이 다르면 이름도 달라진다.

- **Strategy collection 질문**: "이번 요청은 어떤 방식으로 처리할까?"
- **Plain registry 질문**: "이 key에 대응하는 기존 정보나 객체는 무엇일까?"

짧게 외우면 다음 두 줄이면 충분하다.

- **행동을 바꿔 끼우면 strategy**
- **이름표로 찾기만 하면 registry**

즉 `Map`은 겉모양일 뿐이고, 설계의 중심은 **behavior swapping인지, keyed lookup인지**다.

이 문서의 범위도 여기까지다. bootstrap fail-fast, 전역 locator drift, 운영 규칙 같은 다음 단계는 관련 문서로 넘기고, 여기서는 "지금 보이는 `Map`이 행동 교체용인지 lookup용인지"만 판별한다.

---

## 30초 구분표

| 구분 질문 | Strategy collection | Plain registry |
|---|---|---|
| 무엇을 고르는가 | 같은 역할의 다른 행동/정책 | key에 대응하는 기존 객체나 정보 |
| 값들의 공통점 | 모두 같은 인터페이스나 역할을 공유한다 | 꼭 같은 행동 계약일 필요는 없다 |
| 꺼낸 뒤 보통 무엇을 하나 | 같은 메서드를 바로 실행한다 | 읽어 오거나 다른 곳에 넘긴다 |
| 새 항목을 추가하는 이유 | 새로운 처리 방식이 생겼다 | 새로운 key나 리소스가 생겼다 |
| 떠올릴 이름 | `Strategy`, `Policy`, `Selector` | `Registry`, `Catalog`, `Resolver` |
| 처음 배우는데 한마디로 | "어떻게 처리할지 고른다" | "등록된 것을 찾아온다" |

한 문장으로 다시 정리하면:

- strategy collection은 **"어떻게 처리할지"를 바꾸는 후보 모음**
- plain registry는 **"무엇이 등록되어 있는지"를 찾는 lookup table**

---

## 예시 1: strategy collection

아래는 배송비 계산 방식을 바꿔 끼우는 구조다.

```java
public interface ShippingStrategy {
    int calculateFee(int distance);
}

public final class ShippingStrategySelector {
    private final Map<ShippingType, ShippingStrategy> strategies;

    public ShippingStrategySelector(Map<ShippingType, ShippingStrategy> strategies) {
        this.strategies = strategies;
    }

    public int calculate(ShippingType type, int distance) {
        ShippingStrategy strategy = strategies.get(type);
        if (strategy == null) {
            throw new IllegalArgumentException("unknown type: " + type);
        }
        return strategy.calculateFee(distance);
    }
}
```

여기서 중요한 점은 `Map` 그 자체보다 값들의 의미다.

- 값들은 모두 `ShippingStrategy`라는 **같은 역할**을 가진다
- lookup 직후 `calculateFee(...)`라는 **같은 행동**을 실행한다
- 새 항목은 "새 배송 정책"을 추가한다는 뜻이다

즉 이 구조는 `Map`을 쓰고 있지만, 설계 질문의 중심은 **행동 교체**다.
그래서 "strategy collection" 또는 "registry-backed strategy selection"이라고 보는 편이 맞다.

---

## 예시 2: plain registry

이번에는 결제 수단별 안내 문구와 endpoint 정보만 찾는다고 하자.

```java
public record PaymentChannelInfo(String displayName, URI endpoint) {}

public final class PaymentChannelRegistry {
    private final Map<PaymentMethod, PaymentChannelInfo> channels;

    public PaymentChannelRegistry(Map<PaymentMethod, PaymentChannelInfo> channels) {
        this.channels = channels;
    }

    public PaymentChannelInfo get(PaymentMethod method) {
        PaymentChannelInfo channel = channels.get(method);
        if (channel == null) {
            throw new IllegalArgumentException("unknown method: " + method);
        }
        return channel;
    }
}
```

여기서는 다른 질문에 답한다.

- key로 **등록된 정보**를 찾는다
- lookup 뒤에 공통 행동을 실행하지 않는다
- 새 항목은 "새 정책"보다 "새 등록 정보"에 가깝다

즉 이 구조의 중심은 behavior swapping이 아니라 **keyed lookup**이다.
그래서 plain registry라고 부르는 편이 더 정확하다.

---

## 같은 코드에 둘 다 들어갈 수도 있다

초보자가 가장 많이 헷갈리는 지점은 이것이다.

```java
PaymentStrategy strategy = strategies.get(order.getPaymentMethod());
return strategy.pay(order);
```

이 코드는 두 층으로 읽을 수 있다.

- **자료구조 층**: `Map`으로 lookup하니 registry 같은 모양이 있다
- **설계 의도 층**: 꺼낸 뒤 같은 `pay(...)`를 실행하니 strategy selection이 핵심이다

그래서 "이건 registry다"와 "이건 strategy다"가 둘 다 부분적으로 맞을 수 있다.
더 정확한 표현은 보통 이것이다.

- `Map`은 **strategy를 찾는 lookup 메커니즘**
- 전체 구조의 중심 질문은 **어떤 strategy를 실행할까**

즉 `Map<Key, Strategy>`를 봤을 때는 먼저 "자료구조 이름"보다 **값들이 정말 교체 가능한 행동인가**를 확인하면 된다.

한 번 더 짧게 자르면 아래 표로 바로 판별할 수 있다.

| 코드에서 지금 먼저 읽히는 동사 | 더 먼저 떠올릴 개념 | 짧은 예시 |
|---|---|---|
| `select`, `choose`, `pay`, `calculate` | strategy selection | `strategy.pay(order)` |
| `get`, `lookup`, `findByKey` | plain registry | `channelRegistry.get(method)` |
| `create`, `new`, `assemble` | factory | `clientFactory.create(provider)` |

---

## 헷갈릴 때 바로 쓰는 체크리스트

- 값들이 모두 **같은 역할의 인터페이스**를 구현하는가
- lookup 직후 **같은 메서드**를 실행하는가
- 새 key가 늘어나는 이유가 **새 행동 추가**인가, **새 등록 정보 추가**인가
- 클래스 이름이 `Factory`인데 실제로는 `get()`만 하는가
- 코드 대화의 중심이 "찾기"인가, "바꿔 끼우기"인가

판단은 이렇게 하면 된다.

- 위 세 줄이 behavior 쪽이면 strategy collection
- 그냥 key로 찾아 돌려주는 게 중심이면 plain registry

---

## 흔한 오해 4가지

- **"`Map<Key, Strategy>`면 그냥 registry 아닌가요?"**
  - 자료구조만 보면 registry-like lookup이 맞다. 하지만 설계 의도가 행동 교체라면 중심 개념은 strategy다.
- **"`get()` 메서드가 있으니 strategy일 수 없지 않나요?"**
  - 아니다. strategy를 고르는 과정이 `get()` 모양일 수 있다. 중요한 것은 꺼낸 뒤 같은 역할의 행동을 실행하는지다.
- **"`Registry`와 `Selector`를 같이 두면 중복 아닌가요?"**
  - 아니다. registry는 등록 lookup을 맡고, selector는 주문 상태나 조건을 보고 어떤 후보를 쓸지 고를 수 있다. lookup과 selection은 같은 단계가 아니다.
- **"registry 값도 메서드를 가지면 바로 strategy인가요?"**
  - 아니다. 값이 메서드를 가진다고 끝이 아니다. 그 값들이 같은 행동 계약을 공유하고, 교체 대상인지가 핵심이다.
- **"`Map<String, Strategy>`면 이름을 `Registry`로 해야 하나요, `Selector`로 해야 하나요?"**
  - 문자열 key로 꺼내더라도 호출자가 기대하는 public 책임이 "어떤 전략을 실행할지 골라 준다"면 `Selector` 쪽이 더 직접적이다. 그냥 등록된 전략 객체를 찾아 돌려주는 도구만 드러내고 싶다면 `Registry`라고 부를 수 있다.
- **"둘 중 하나만 맞아야 하나요?"**
  - 아니다. registry가 strategy selection을 구현하는 도구로 들어갈 수 있다. 질문 층위를 섞지 않는 것이 중요하다.

---

## 다음에 이어서 보면 좋은 문서

- strategy 자체를 처음부터 다시 보고 싶다면 [전략 패턴 기초](./strategy-pattern-basics.md)
- `Map<String, Strategy>` 이름을 `Selector`/`Registry` 중 무엇으로 둘지 더 직접적으로 정리하려면 [Map-backed 클래스 네이밍 체크리스트](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
- `Map<String, Handler>`가 factory인지 registry인지 헷갈리면 [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md)
- strategy lookup helper가 전역 조회소처럼 커지는 냄새는 [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)
- registry를 전역 조회로 오남용하는 위험은 [Service Locator Antipattern](./service-locator-antipattern.md)에서 이어서 보면 된다

처음 읽는 단계라면 순서를 이렇게 잡으면 된다.

- 이름만 헷갈리면 이 문서에서 멈춘다.
- 클래스 이름까지 정하고 싶으면 `Map-backed 네이밍 체크리스트`로 간다.
- 전역 조회, Spring bean name, locator 냄새가 보일 때만 service locator 쪽 follow-up으로 내려간다.

## 한 줄 정리

같은 `Map<Key, ...>`라도 **같은 행동을 바꿔 끼우는 후보 모음이면 strategy collection**, **key로 기존 객체나 정보를 찾기만 하면 plain registry**다.
