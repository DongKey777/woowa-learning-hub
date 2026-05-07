---
schema_version: 3
title: Factory Switch Registry Smell
concept_id: design-pattern/factory-switch-registry-smell
canonical: false
category: design-pattern
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
  - factory-vs-registry
  - service-locator-drift
  - switch-factory-smell
aliases:
  - factory switch smell
  - registry refactor
  - registry backed factory
  - switch heavy factory refactor
  - factory vs registry vs service locator
  - strategy selection
  - creation selection explosion
  - factory branching
  - hidden dependency registry
symptoms:
  - 팩토리 switch가 계속 길어지는데 어디까지가 팩토리고 어디서 구조를 갈라야 할지 모르겠어
  - switch를 Map으로 바꿨더니 이번에는 전역 registry 조회가 퍼지고 있어
  - 구현체 추가할 때마다 factory와 호출부 규칙이 같이 커져서 책임이 안 보여
intents:
  - symptom
  - design
  - troubleshooting
prerequisites:
  - design-pattern/factory
  - design-pattern/registry-pattern
next_docs:
  - design-pattern/registry-vs-factory-injected-handler-maps
  - design-pattern/injected-registry-vs-service-locator-checklist
  - design-pattern/service-locator-antipattern
linked_paths:
  - contents/design-pattern/factory.md
  - contents/design-pattern/registry-pattern.md
  - contents/design-pattern/strategy-pattern.md
  - contents/design-pattern/registry-vs-factory-injected-handler-maps.md
  - contents/design-pattern/injected-registry-vs-service-locator-checklist.md
  - contents/design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist.md
  - contents/design-pattern/service-locator-antipattern.md
  - contents/design-pattern/pattern-selection.md
confusable_with:
  - design-pattern/registry-pattern
  - design-pattern/service-locator-antipattern
  - design-pattern/strategy-pattern
forbidden_neighbors:
  - contents/design-pattern/registry-vs-factory-injected-handler-maps.md
  - contents/design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist.md
expected_queries:
  - factory switch가 점점 커질 때 registry로 옮겨야 하는 기준을 알고 싶어
  - 문자열 key로 구현체를 고르는 factory를 리팩터링하다가 service locator가 되는 걸 어떻게 피하지?
  - 생성 로직과 구현 선택 로직이 한 클래스에 몰렸을 때 어떤 패턴으로 분리해야 해?
  - switch factory를 Map으로 바꿨는데 의존성이 더 숨겨지는 구조인지 점검하고 싶어
  - registry backed factory와 strategy selection을 언제 다르게 봐야 하는지 헷갈려
contextual_chunk_prefix: |
  이 문서는 구현체 선택용 switch가 계속 커지는 factory를 어떻게 줄여야 하는지,
  registry backed factory로 옮기다가 service locator로 미끄러지는 상황을
  겪는 학습자를 위한 symptom_router다. 문자열 key 분기, Map lookup,
  생성 책임과 선택 책임 분리, 숨은 의존성, 전역 registry 조회 냄새를
  어떻게 구분할지 묻는 검색을 이 문서로 보낸다.
---
# Factory Switch Registry Smell

> 한 줄 요약: Factory의 switch가 계속 늘어나면 그건 더 이상 단순한 생성기가 아니라 Registry나 전략 선택기로 재설계해야 한다는 신호다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [팩토리 (Factory)](./factory.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Strategy Pattern](./strategy-pattern.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

팩토리의 `switch`나 `if-else`는 작은 규모에서는 괜찮다.  
문제는 선택지와 조건이 계속 늘어날 때다.

그 순간 팩토리는 다음 중 하나로 바뀌어야 한다.

- Registry: 키로 객체를 찾는다
- Strategy: 행동을 선택한다
- DI configuration: 생성 조합을 설정한다

### Retrieval Anchors

- `factory switch smell`
- `registry refactor`
- `registry backed factory`
- `switch heavy factory refactor`
- `factory vs registry vs service locator`
- `strategy selection`
- `creation selection explosion`
- `factory branching`
- `hidden dependency registry`

---

## 깊이 들어가기

### 1. switch가 길어지는 이유

factory가 하는 일이 하나에서 둘 이상으로 늘어난다.

- 구현 선택
- 생성 파라미터 조립
- 외부 설정 반영
- 예외 처리

이때 switch는 이미 선택기다.

### 2. smell의 신호

- case가 계속 늘어난다
- 문자열 키가 여기저기 반복된다
- factory 안에 비즈니스 규칙이 들어간다
- 새 구현을 추가할 때 factory만 수정하면 끝나지 않는다

### 3. 대안은 구조를 나누는 것이다

- 선택은 Registry
- 행동은 Strategy
- 생성은 Factory

이 셋을 분리하면 책임이 선명해진다.

### 4. Registry-backed factory로 옮길 때 경계를 고정한다

switch를 없앴다고 바로 설계가 좋아지는 것은 아니다.  
학습자가 가장 자주 미끄러지는 지점은 `registry.get(...)`를 아무 곳에서나 호출하게 만들어 **service locator**로 바꾸는 순간이다.

경계는 아래처럼 나눈다.

| 역할 | 맡아야 하는 일 | 넣지 말아야 하는 일 |
|---|---|---|
| Factory | `create(key)` 같은 공개 생성 진입점, fail-closed 예외 처리, 생성 직전 조립 | 전역 의존성 조회 API, 아무 타입이나 꺼내주는 `get(Class<?>)` |
| Registry | `key -> creator/handler` lookup, bootstrap 시점 등록, 좁은 타입의 명시적 맵 | 비즈니스 규칙 판단, 환경/권한/요금 정책 해석 |
| Selector / Policy | request를 보고 어떤 key를 쓸지 결정 | 객체 생성, 런타임 wiring |

즉 refactor의 핵심은 `switch`를 `Map`으로 바꾸는 것이 아니라  
**선택 key는 밖에서 결정하고, Registry는 그 key로 좁은 후보를 찾고, Factory가 최종 생성만 하게 만드는 것**이다.

### 5. 안전한 리팩터링 순서

1. 먼저 `String` 분기값을 enum이나 value object key로 승격해 분기 표면을 줄인다.
2. `case -> new Xxx()` 묶음을 `key -> Supplier<Xxx>` 또는 `key -> Creator`로 Registry에 옮긴다.
3. 호출부는 Registry를 직접 보지 말고 기존 Factory나 얇은 Selector를 통해서만 접근하게 둔다.
4. 알 수 없는 key는 기본 구현으로 몰래 fallback하지 말고 즉시 실패시킨다.
5. 테스트는 "새 구현 추가 시 registry 등록 + factory 동작"을 같이 검증해 lookup 누락을 잡는다.

---

## 실전 시나리오

### 시나리오 1: 결제 provider 선택

지역, 채널, 기능 플래그가 많아지면 switch factory는 급격히 비대해진다.

### 시나리오 2: storage client 생성

S3, GCS, local, mock이 섞이면 registry나 DI로 바꾸는 편이 낫다.

### 시나리오 3: 테스트 더블

테스트용 구현을 추가하기 시작하면 factory는 보통 과하게 커진다.

### 시나리오 4: refactor는 했는데 service locator가 된 경우

`ApplicationRegistry.get(PaymentPort.class)` 같은 전역 조회가 서비스 안으로 퍼지면 switch는 사라져도 냄새는 그대로다.  
호출부가 무엇을 의존하는지 시그니처에서 안 보이기 때문이다.

---

## 코드로 보기

### Bad

```java
public class PaymentFactory {
    public PaymentPort create(String type) {
        return switch (type) {
            case "CARD" -> new CardPaymentPort();
            case "POINT" -> new PointPaymentPort();
            case "BANK" -> new BankPaymentPort();
            default -> throw new IllegalArgumentException("unknown type");
        };
    }
}
```

### Better: Registry-backed factory

```java
public final class PaymentPortRegistry {
    private final Map<PaymentMethod, Supplier<PaymentPort>> creators;

    public PaymentPortRegistry(Map<PaymentMethod, Supplier<PaymentPort>> creators) {
        this.creators = creators;
    }

    public Supplier<PaymentPort> creatorFor(PaymentMethod method) {
        Supplier<PaymentPort> creator = creators.get(method);
        if (creator == null) {
            throw new IllegalArgumentException("unknown type: " + method);
        }
        return creator;
    }
}

public final class PaymentFactory {
    private final PaymentPortRegistry registry;

    public PaymentFactory(PaymentPortRegistry registry) {
        this.registry = registry;
    }

    public PaymentPort create(PaymentMethod method) {
        return registry.creatorFor(method).get();
    }
}
```

Factory는 여전히 생성 진입점이고, Registry는 좁은 creator lookup만 맡는다.

### Bad refactor: service locator drift

```java
public class CheckoutService {
    public void pay(PaymentMethod method, PaymentRequest request) {
        PaymentPort port = ApplicationRegistry.get(method.portType());
        port.pay(request);
    }
}
```

이 코드는 switch는 없앴지만 더 나빠졌다.

- 어떤 의존성이 필요한지 생성자에서 안 보인다
- registry가 점점 "모든 것을 꺼내는 전역 컨테이너"가 된다
- 테스트가 registry 초기화 순서에 묶인다

### Even better: selection and behavior split

```java
public interface PaymentStrategy {
    PaymentResult pay(PaymentRequest request);
}
```

냄새의 본질은 switch 자체가 아니라,  
**구현 선택 규칙이 factory 한 곳에 뭉치거나 반대로 전역 lookup으로 새어 나가 설계 전체를 지배하게 되는 것**이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| small switch factory | 가장 단순하다 | 커지면 유지보수 지옥 | 구현이 2~3개일 때 |
| Registry-backed factory | 선택 테이블이 명시적이고 추가 구현 확장이 쉽다 | 등록 누락과 key 관리가 필요하다 | 구현이 많지만 생성 진입점은 하나로 유지하고 싶을 때 |
| Strategy selection | 행동과 생성이 분리된다 | 구조가 더 필요하다 | 알고리즘이 바뀔 때 |
| Service Locator drift | 호출부가 짧아 보인다 | 숨은 의존성, 전역 상태, 테스트 악화 | 기본 선택지로는 피한다 |

판단 기준은 다음과 같다.

- case가 5개를 넘으면 재검토한다
- factory가 규칙을 판단하기 시작하면 smell이다
- 생성과 선택의 책임을 분리한다
- registry는 좁은 타입의 lookup만 맡기고 호출부에 직접 퍼뜨리지 않는다

---

## 꼬리질문

> Q: factory switch가 왜 smell인가요?
> 의도: 선택 로직 폭발을 아는지 확인한다.
> 핵심: 생성 규칙이 factory 하나에 몰리기 때문이다.

> Q: Registry로 바꾸면 무조건 좋아지나요?
> 의도: registry도 설계가 필요하다는 걸 아는지 확인한다.
> 핵심: 아닐 수 있고, 숨은 service locator가 되면 안 된다.

> Q: Registry-backed factory와 service locator의 경계는 어디인가요?
> 의도: refactor 후에도 의존성 노출 규칙을 지키는지 확인한다.
> 핵심: 호출부가 registry를 직접 뒤지지 않고, registry가 한 종류의 creator/handler lookup만 맡으면 안전하다.

> Q: provider 선택 규칙은 factory에 두나요 registry에 두나요?
> 의도: 생성 책임과 정책 판단을 섞지 않는지 확인한다.
> 핵심: key를 정하는 규칙은 selector/policy에 두고, registry는 key lookup만 맡긴다.

> Q: Strategy와 Factory를 같이 써도 되나요?
> 의도: 생성과 행동 분리를 이해하는지 확인한다.
> 핵심: 보통 같이 쓰면 더 선명해진다.

## 한 줄 정리

Factory의 switch가 커지면 Registry나 Strategy로 책임을 나누되, Registry를 전역 lookup으로 퍼뜨려 service locator로 만들지 않는 것이 핵심이다.
