# Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기

> 한 줄 요약: 초보자가 `lookup table`, `resolver`, `router`, `service locator`를 모두 "어딘가에서 찾아오는 코드"로 묶어 헷갈릴 때, 먼저 "단순 조회인지, 입력 해석인지, 요청 분기인지, 숨은 의존성 조회인지"로 나누면 된다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](./router-dispatcher-handlermapping-vs-selector-factory.md)
> - [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: registry primer lookup table resolver router service locator, lookup table vs registry beginner, resolver vs registry beginner, router vs registry beginner, service locator vs registry beginner, registry service locator difference, lookup table resolver router service locator difference, registry pattern beginner, registry 큰 그림, registry 기초, registry 언제 쓰는지, registry 처음 배우는데, lookup table 처음 배우는데, resolver router registry 처음 배우는데, service locator 처음 배우는데, lookup table 큰 그림, resolver 큰 그림, router 큰 그림, service locator 큰 그림, keyed lookup primer, named handler lookup primer, handler registry beginner, payment handler registry beginner, route to registry pattern, route to service locator antipattern, service locator anti pattern beginner, hidden dependency lookup beginner, 전역 조회소 안티패턴, 레지스트리 룩업 테이블, lookup table 레지스트리 차이, resolver 레지스트리 차이, router 레지스트리 차이, service locator 레지스트리 차이, 라우터 리졸버 레지스트리 차이, 서비스 로케이터 안티패턴 기초
retrieval-anchor-keywords: router vs selector naming, router vs dispatcher naming, request dispatch router handler mapping, handler mapping beginner, request routing naming bridge

---

## Quick check

- key에 이미 등록된 값을 찾으면 `lookup table` / `registry`
- 애매한 입력을 도메인 의미로 풀면 `resolver`
- 요청을 어느 처리 경로로 보낼지 고르면 `router`
- 코드 본문에서 전역 조회소로 의존성을 꺼내면 `service locator` 냄새

헷갈리면 먼저 "`무엇을 찾나`"보다 "`어떤 질문에 답하나`"로 자르면 된다.

## 먼저 큰 그림

처음 배우는데 네 단어가 전부 비슷해 보이는 이유는 모두 "무언가를 찾는다"는 모양을 갖기 때문이다.
하지만 설계 이름은 `Map.get(...)` 모양보다 **어떤 질문에 답하는가**로 정한다.

짧게 자르면 아래 네 줄이다.

- **Lookup table / Registry**: "이 key에 등록된 것은 무엇인가?"
- **Resolver**: "애매한 입력을 규칙으로 풀면 무엇인가?"
- **Router**: "이 요청은 어느 경로나 처리자로 보내야 하는가?"
- **Service Locator**: "내가 필요한 의존성을 전역 조회소에서 몰래 꺼내도 되는가?" 보통은 안티 패턴 신호다.

즉 `lookup table`은 [Registry Pattern](./registry-pattern.md) 쪽으로,
`service locator`는 [Service Locator Antipattern](./service-locator-antipattern.md) 쪽으로 먼저 보내면 된다.

---

## 먼저 10초 기준

처음 보면 아래 네 줄만 잡아도 절반은 끝난다.

- `lookup table` / `registry`: "이 key에 등록된 것은 무엇인가?"
- `resolver`: "이 입력을 해석하면 무엇인가?"
- `router`: "이 요청은 어디로 보내야 하나?"
- `service locator`: "필요한 의존성을 전역 조회소에서 꺼내고 있나?"

즉 **등록 lookup인지, 입력 해석인지, 요청 분기인지, 숨은 의존성 조회인지**로 먼저 자른다.

## 30초 비교표

| 단어 | 먼저 묻는 질문 | 좋은 예 | 헷갈리면 다음 문서 |
|---|---|---|---|
| lookup table | key로 이미 있는 값이나 객체를 찾는가 | `PaymentMethod -> PaymentInfo` | [Registry Pattern](./registry-pattern.md) |
| registry | 등록된 handler, strategy, converter를 key로 찾는가 | `PaymentMethod -> PaymentHandler` | [Registry Pattern](./registry-pattern.md) |
| resolver | 문자열, 요청값, 이름을 의미 있는 값으로 해석하는가 | `"CARD"` -> `PaymentMethod.CARD` | [Strategy vs Policy Selector Naming](./strategy-policy-selector-naming.md) |
| router | 요청을 어느 handler/path/queue로 보낼지 고르는가 | `/payments/card` -> payment controller | [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](./router-dispatcher-handlermapping-vs-selector-factory.md) |
| service locator | 필요한 의존성을 코드 본문에서 전역으로 꺼내는가 | `ApplicationContext.getBean(...)` | [Service Locator Antipattern](./service-locator-antipattern.md) |

가장 초보자 친화적인 기준은 이것이다.

**"작고 명시적인 key 조회는 registry, 넓고 숨은 의존성 조회는 service locator."**

---

## 1분 예시: 결제 요청 하나로 나누기

같은 결제 요청에서도 네 단어가 서로 다른 위치에 놓일 수 있다.

```text
POST /payments/card
```

1. **Router**
   요청 path와 method를 보고 결제 controller나 handler 흐름으로 보낸다.
2. **Resolver**
   `"card"` 문자열을 `PaymentMethod.CARD` 같은 도메인 값으로 해석한다.
3. **Registry**
   `PaymentMethod.CARD` key로 이미 등록된 `CardPaymentHandler`를 찾는다.
4. **Service Locator smell**
   `CheckoutService`가 메서드 안에서 `ApplicationContext.getBean("cardPaymentHandler")`를 직접 부르면 숨은 의존성 조회가 된다.

코드 모양으로 보면 차이가 더 선명하다.

```java
PaymentMethod method = paymentMethodResolver.resolve(pathVariable);
PaymentHandler handler = paymentHandlerRegistry.get(method);
handler.pay(order);
```

여기서는 resolver와 registry가 모두 보인다.
하지만 의존성은 생성자에 드러나 있고, registry 범위도 `PaymentHandler`로 좁다면 service locator가 아니다.

나쁜 방향은 아래처럼 넓은 컨테이너를 요청 처리 중에 직접 뒤지는 것이다.

```java
PaymentHandler handler = applicationContext.getBean(beanName, PaymentHandler.class);
```

이 코드는 "찾는다"는 점에서는 비슷하지만, 설계상으로는 [Service Locator Antipattern](./service-locator-antipattern.md)에 가깝다.

---

## 흔한 혼동

- **"`Map`으로 찾으면 전부 registry인가요?"**
  자료구조 모양만으로는 부족하다. key로 등록된 값을 찾는 것이 중심이면 registry이고, 입력 해석 규칙이 중심이면 resolver다.
- **"`resolve()`라는 메서드면 무조건 resolver인가요?"**
  아니다. 메서드 이름보다 책임을 본다. 단순 `key -> handler` 조회만 한다면 registry라고 설명하는 편이 더 쉽다.
- **"`router`도 handler를 고르니까 registry 아닌가요?"**
  router는 요청 흐름을 어느 경로로 보낼지가 중심이다. 내부에서 registry를 쓸 수는 있지만, 바깥 책임은 routing이다.
- **"registry와 service locator는 둘 다 찾아오는데 왜 하나는 안티 패턴인가요?"**
  registry는 좁은 대상과 domain key가 드러난다. service locator는 코드 본문에서 넓은 조회소를 뒤져 실제 의존성을 숨긴다.
- **"Spring이 `Map<String, Handler>`를 주입하면 바로 domain registry인가요?"**
  보통 `String` key는 bean name이다. 서비스 분기 기준으로 쓰려면 [Bean Name vs Domain Key Lookup](./bean-name-vs-domain-key-lookup.md)처럼 domain key registry로 감싼다.

---

## 검색어별 첫 문서

| 초보 검색어 | 먼저 열 문서 | 이유 |
|---|---|---|
| `lookup table pattern`, `key로 handler 찾기`, `registry 언제 쓰는지` | [Registry Pattern](./registry-pattern.md) | 등록된 객체를 key로 찾는 큰 그림이 핵심이다 |
| `resolver vs registry`, `router vs registry`, `이름이 헷갈림` | 이 문서 | 용어를 먼저 자르고 다음 문서로 보낸다 |
| `ApplicationContext getBean`, `전역 조회소`, `service locator 처음 배우는데` | [Service Locator Antipattern](./service-locator-antipattern.md) | 숨은 의존성 조회 문제를 바로 봐야 한다 |
| `주입된 registry가 locator인지 모르겠음` | [Injected Registry vs Service Locator Checklist](./injected-registry-vs-service-locator-checklist.md) | 생성자 주입과 숨은 lookup을 코드 리뷰 기준으로 자른다 |

## 한 줄 정리

처음에는 `lookup table`과 `registry`를 같은 기초 축으로 보고, `resolver`와 `router`는 그 주변의 해석/분기 이름으로 분리하며, `service locator`는 숨은 의존성 조회 안티 패턴으로 따로 경계하면 된다.
