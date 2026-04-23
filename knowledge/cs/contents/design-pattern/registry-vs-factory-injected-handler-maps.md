# 주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기

> 한 줄 요약: 프레임워크가 `List<Handler>`나 `Map<Key, Handler>`를 주입해 줬다면 대개 네 손에 들어온 것은 factory가 아니라 registry다. factory는 그 lookup 뒤에 "새로 만든다"가 붙을 때 등장한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
> - [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Strategy vs Function: lambda로 충분한가, 전략 타입이 필요한가](./strategy-vs-function-chooser.md)
> - [팩토리 패턴 기초](./factory-basics.md)
> - [Factory Switch Registry Smell](./factory-switch-registry-smell.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)

retrieval-anchor-keywords: registry vs factory injected handler map, spring handler map injection, list of handlers registry, bean collection injection registry, bean map injection factory, payment handler map not factory, registry lookup vs factory creation, injected handlers beginner, strategy map vs factory, policy selector vs factory, selector resolver registry strategy vs factory, factory naming smell, service locator vs injected registry, injected registry vs service locator checklist, explicit constructor injection registry, autowired map of handlers, List<Handler> registry, Map<String Handler> injection, runtime lookup vs object creation, collection injection registry, bean name vs domain key lookup, spring bean name handler map, domain key registry, bean name leak, registry vs factory 처음 배우는데, 주입된 handler map 큰 그림, 주입된 handler map 기초, handler map 처음 배우는데, handler map 큰 그림, handler map 언제 쓰는지, Map<String, Handler> 처음 배우는데, List<Handler> 주입 큰 그림, 스프링 handler map 주입 기초, 스프링에서 handler map 주입, 이미 있는 bean lookup vs 새 객체 생성, bean 이름으로 handler 찾기, 도메인 키 레지스트리, service locator 드리프트 체크리스트, factory vs registry in di collection injection, di collection injection beginner, spring list injection vs map injection, injected List and Map patterns, wiring lookup creation separation, spring collection injection lookup vs create, list vs map handler injection, factory registry spring beginner

---

## 핵심 개념

먼저 용어보다 그림으로 자르면 쉽다.

- 프레임워크가 `Handler`들을 미리 모아 준다
- 네 코드는 그중 맞는 하나를 **찾아 쓴다**
- 정말 새 객체가 필요하면, 찾은 creator/factory에게 **만들어 달라고 한다**

즉 질문은 두 개다.

- **Registry 질문**: "이미 있는 것 중 어떤 걸 꺼낼까?"
- **Factory 질문**: "지금 새로 무엇을 만들까?"

프레임워크가 컬렉션을 주입했다고 해서 자동으로 factory가 되는 것은 아니다.
그건 보통 **준비된 후보들을 모아 둔 registry**에 더 가깝다.

---

## handler map과 function map 질문을 먼저 나누기

처음 배우는데 `Map`이 같이 나오면 질문이 비슷해 보여도 실제로는 두 갈래다.

| 질문 모양 | 먼저 볼 문서 | 핵심 판단 |
|---|---|---|
| `Map<String, Handler>`나 `List<Handler>`를 주입받았는데 이게 factory인지 헷갈린다 | 이 문서 | 이미 있는 후보를 lookup하는지 본다 |
| `Map<String, Function>`이나 `lambda` 묶음으로 충분한지 헷갈린다 | [Strategy vs Function](./strategy-vs-function-chooser.md) | 작은 규칙인지, Strategy 타입까지 올려야 하는지 본다 |
| `Map<Key, Creator>`를 찾은 뒤 `create()`까지 호출한다 | 이 문서 | lookup 뒤에 creation이 붙는지 본다 |
| `Map<Key, Strategy>`가 너무 무거운지 묻는다 | [Strategy vs Function](./strategy-vs-function-chooser.md) | 함수 vs 이름 있는 규칙 객체 경계가 핵심이다 |

짧게 자르면 다음 두 문장이다.

- **이미 있는 bean을 찾는 질문**이면 registry/factory 경계다.
- **작은 규칙을 함수로 둘지 전략 객체로 둘지 묻는 질문**이면 strategy/function 경계다.

---

## 먼저 실행 순서를 나눠 보자

handler collection이 주입될 때는 세 단계를 분리해서 보면 거의 안 헷갈린다.

| 단계 | 누가 주로 맡나 | 그 단계의 질문 | 더 가까운 이름 |
|---|---|---|---|
| 애플리케이션 시작 시 `List<Handler>`나 `Map<String, Handler>`를 준비 | DI 컨테이너 | "어떤 객체 그래프를 연결해 둘까?" | wiring |
| 요청 시점에 key로 맞는 handler를 찾음 | 애플리케이션 코드 | "이미 있는 것 중 무엇을 꺼낼까?" | registry lookup |
| 요청 시점에 creator로 새 세션/명령 객체를 만듦 | 애플리케이션 코드 | "지금 무엇을 새로 만들까?" | factory creation |

핵심은 이것이다.

- 프레임워크가 컬렉션을 주입하는 일은 보통 **1단계**
- 네 코드가 `get()`이나 `resolve()`만 하면 **2단계**
- 네 코드가 `create()`나 `build()`까지 책임지면 **3단계**

즉 주입된 handler map 자체를 factory라고 부르기보다,
**"컨테이너가 준비한 후보 집합 위에서 registry lookup을 하고 있는가, 아니면 그다음 factory creation까지 맡는가"**로 보는 편이 정확하다.

---

## `List` 주입과 `Map` 주입은 같은 질문이 아니다

둘 다 collection injection이지만, 초보자가 실제로 판단해야 하는 포인트는 조금 다르다.

| 주입 모양 | 컨테이너가 바로 준 것 | 네 코드가 추가로 결정하는 것 | 초보자 기본 해석 |
|---|---|---|---|
| `List<Handler>` | "후보 전부" | 어떤 domain key로 묶을지 | registry bootstrap |
| `Map<String, Handler>` | bean name -> handler | bean name을 그대로 쓸지, domain key로 감쌀지 | bean-name map input |
| `Map<Key, Handler>` | 이미 keyed lookup 가능한 후보 | 꺼내서 바로 실행할지 | registry lookup |
| `Map<Key, Creator>` | 어떤 creator를 고를지 | 고른 뒤 `create()`까지 호출할지 | factory + 내부 registry |

짧게 읽으면 이렇다.

- `List<Handler>`를 받았다면 먼저 "이 목록을 어떤 key 기준 registry로 바꿀까?"를 본다.
- `Map<String, Handler>`를 받았다면 먼저 "이 `String`이 domain key인가, bean name인가?"를 본다.
- `Map<Key, Creator>`를 받았다면 "lookup으로 끝나는가, `create()`까지 가는가?"를 본다.

즉 `List`와 `Map`을 하나로 뭉뚱그려 "Spring이 factory를 주입했다"라고 생각하면 wiring, lookup, creation이 한꺼번에 섞인다.

---

## 30초 구분표

| 코드 모양 | 보통 뭐라고 부르나 | 이유 |
|---|---|---|
| `Map<PaymentMethod, PaymentHandler>`에서 꺼내 바로 `handle()` 호출 | Registry | 이미 만들어진 handler를 lookup한다 |
| `List<PaymentHandler>`를 받아 시작 시점에 map으로 묶음 | DI + Registry bootstrap | 컨테이너가 wiring했고, 코드는 lookup table만 만든다 |
| `Map<PaymentMethod, PaymentSessionCreator>`를 찾은 뒤 `create(order)` 호출 | Factory + 내부 Registry | creator를 lookup한 다음 새 객체를 만든다 |
| `ApplicationContext.getBean(name)`을 서비스 여기저기서 호출 | Service Locator smell | 명시적 주입 대신 전역 조회로 흘러간다 |

짧게 외우면 이렇다.

**"기존 bean을 꺼내 쓰면 registry, 새 객체를 만들면 factory."**

---

## 예시 1: injected handler map은 대개 registry다

아래 코드는 Spring이 여러 `PaymentHandler` bean을 모아 주고, 애플리케이션이 그중 하나를 찾는 구조다.

```java
@Component
public class PaymentHandlerRegistry {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandlerRegistry(List<PaymentHandler> handlers) {
        this.handlers = handlers.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentHandler::supports,
                handler -> handler
            ));
    }

    public PaymentHandler get(PaymentMethod method) {
        PaymentHandler handler = handlers.get(method);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return handler;
    }
}
```

```java
PaymentHandler handler = registry.get(order.getPaymentMethod());
handler.handle(order);
```

여기서 일어난 일은 둘뿐이다.

- 컨테이너가 handler bean들을 준비했다
- `registry.get(...)`가 그중 하나를 골랐다

`new`가 없다. 새 객체도 안 만든다.
그래서 핵심 책임은 **creation이 아니라 lookup**이다.

Spring이 `Map<String, PaymentHandler>`를 bean name 기준으로 바로 주입해 줘도 lookup 자체는 여전히 registry 쪽이다.
다만 그 `String` key는 컨테이너의 bean name이다.
서비스가 `PaymentMethod` 같은 domain key로 handler를 골라야 한다면, bean name map을 그대로 넘기지 말고 [Bean Name vs Domain Key Lookup](./bean-name-vs-domain-key-lookup.md)처럼 시작 시점에 domain-key registry로 감싸는 편이 안전하다.

---

## 예시 2: factory는 lookup 뒤에 creation이 붙는다

이번에는 map 안에 handler 자체가 아니라 "만드는 역할"이 들어 있다고 하자.

```java
public interface PaymentSessionCreator {
    PaymentMethod supports();
    PaymentSession create(Order order);
}

@Component
public class PaymentSessionFactory {
    private final Map<PaymentMethod, PaymentSessionCreator> creators;

    public PaymentSessionFactory(List<PaymentSessionCreator> creators) {
        this.creators = creators.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentSessionCreator::supports,
                creator -> creator
            ));
    }

    public PaymentSession create(Order order) {
        PaymentSessionCreator creator = creators.get(order.getPaymentMethod());
        if (creator == null) {
            throw new IllegalArgumentException("unsupported method: " + order.getPaymentMethod());
        }
        return creator.create(order);
    }
}
```

여기서는 안쪽에 registry 성격이 있다.
하지만 바깥에서 보는 public 책임은 `create(...)`다.

- `creators` map: 어떤 creator를 쓸지 **lookup**
- `creator.create(order)`: 실제 **creation**

즉 **factory가 내부에서 registry를 사용할 수는 있지만, lookup만 하는 클래스와는 역할이 다르다.**

---

## Spring 스타일 코드에서 10초 판별 순서

PR 리뷰나 코드 읽기에서 빨리 자를 때는 아래 순서면 충분하다.

1. **누가 collection을 준비했는가?**
   - Spring이 시작 시점에 모아 줬다면 일단 wiring이다.
2. **호출부가 하는 일이 `get/find/resolve`까지인가?**
   - 그렇다면 registry lookup 쪽이다.
3. **lookup 뒤에 `create/build/new/of`가 붙는가?**
   - 그때부터 factory creation 책임이 등장한다.
4. **key가 `PaymentMethod` 같은 domain key인가, bean name 문자열인가?**
   - bean name이면 public 설계로 흘리지 말고 domain-key registry로 한 번 감싼다.
5. **요청 처리 중 `ApplicationContext.getBean(...)`을 다시 부르는가?**
   - 그건 collection injection을 잘 쓴 구조라기보다 service locator smell에 가깝다.

한 문장으로 압축하면:

**"컨테이너가 모아 주는 것은 wiring, 서비스가 고르는 것은 lookup, 선택 뒤에 새로 만드는 것이 factory."**

---

## 이름 붙일 때 자주 헷갈리는 지점

| 클래스가 실제로 하는 일 | 더 맞는 이름 |
|---|---|
| `get(key)`, `find(key)`, `resolve(key)`로 기존 handler 반환 | `Registry`, `Resolver`, `Router` |
| `create(...)`, `newSession(...)`으로 새 객체 반환 | `Factory` |
| `Map<Key, Handler>`를 받아 분기만 함 | 보통 `Registry` |
| `Map<Key, Creator>`를 받아 생성까지 마침 | 보통 `Factory` |

입문자가 많이 만드는 이름 충돌은 이것이다.

- 클래스 이름은 `PaymentHandlerFactory`
- 실제 구현은 `handlers.get(method)`만 함

이 경우는 factory보다 registry라고 부르는 편이 구조를 더 잘 설명한다.

---

## 흔한 오해 4가지

- **"Spring이 map을 주입했으니 factory를 대신해 준 거 아닌가요?"**
  - 아니다. Spring은 주로 bean **wiring**을 대신한다. 런타임 lookup과 생성 책임은 아직 네 코드에 남아 있다.
- **"handler를 고르는 것도 create의 일부 아닌가요?"**
  - 선택은 관련 있지만, 선택만 하고 기존 객체를 돌려주면 registry 쪽에 더 가깝다.
- **"주입된 map을 쓰면 바로 service locator인가요?"**
  - 아니다. 좁은 타입의 map을 생성자로 명시적으로 주입받는 것은 registry로 쓸 수 있다. 문제는 `ApplicationContext`나 전역 map에서 아무 타입이나 꺼내 쓰기 시작할 때다.
- **"그럼 factory와 registry 중 하나만 써야 하나요?"**
  - 아니다. factory가 내부에서 registry를 써도 된다. 중요한 것은 lookup과 creation을 머릿속에서 섞지 않는 것이다.

---

## 언제 이 문서를 바로 떠올리면 좋은가

- `List<Handler>`를 받아 `Map`으로 바꿨는데 이름을 `*Factory`로 붙이려는 순간
- `List<Handler>`와 `Map<String, Handler>`가 같은 질문이라고 느껴질 때
- 코드 리뷰에서 "이건 factory보다 registry 같아요"라는 말을 들었을 때
- Spring이 handler collection을 주입해 주는 구조에서 lookup 책임과 생성 책임이 섞일 때
- injected map을 쓰다가 [Service Locator Antipattern](./service-locator-antipattern.md)으로 미끄러지는지 걱정될 때

## 한 줄 정리

프레임워크가 모아 준 handler map은 보통 **registry**이고, 그 map에서 고른 creator로 새 객체를 만들 때 비로소 **factory**가 된다.
