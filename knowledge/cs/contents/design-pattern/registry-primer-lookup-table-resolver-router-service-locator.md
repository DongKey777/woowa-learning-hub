---
schema_version: 3
title: 'Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기'
concept_id: design-pattern/registry-primer-lookup-table-resolver-router-service-locator
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
review_feedback_tags:
- registry-lookup-table
- resolver-service-locator
- registry
- lookup-table-vs
aliases:
- registry primer
- lookup table vs registry
- resolver vs registry
- router vs registry
- service locator vs registry
intents:
- comparison
- design
linked_paths:
- contents/design-pattern/factory-selector-resolver-beginner-entrypoint.md
- contents/design-pattern/service-locator-antipattern.md
- contents/design-pattern/strategy-map-vs-registry-primer.md
- contents/design-pattern/injected-registry-vs-service-locator-checklist.md
confusable_with:
- design-pattern/strategy-map-vs-registry-primer
- design-pattern/injected-registry-vs-service-locator-checklist
- design-pattern/factory-selector-resolver-beginner-entrypoint
expected_queries:
- registry랑 lookup table, resolver, router는 어떻게 달라?
- service locator랑 registry가 왜 다른 냄새야?
- resolver router registry를 처음 구분하려면 어디서 봐야 해?
- 이미 등록된 객체를 key로 찾는 코드는 무슨 이름이 좋아?
contextual_chunk_prefix: |
  이 문서는 학습자가 등록된 것들 중에 키로 찾아 쓰는 패턴(registry / lookup
  table / resolver / router)과 객체가 자기 의존성을 키로 꺼내가는 패턴
  (service locator)을 처음 구분하는 chooser다. 등록된 것 중 키로 찾기,
  자기 의존성을 키로 꺼내가기, lookup table 패턴, resolver 라우터 차이
  같은 자연어 paraphrase가 본 문서의 분기에 매핑된다.
---
# Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기

> 한 줄 요약: 초보자가 `lookup table`, `resolver`, `router`, `service locator`를 모두 "어딘가에서 찾아오는 코드"로 묶어 헷갈릴 때, 먼저 "단순 조회인지, 입력 해석인지, 요청 분기인지, 숨은 의존성 조회인지"로 나누면 된다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` 이 문서 -> `[bridge]` [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md) -> `[cross-category]` [의존성 주입 기초](../software-engineering/dependency-injection-basics.md) -> `[spring bridge]` [DispatcherServlet vs HandlerInterceptor](../spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)

관련 문서:

- [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
- [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)
- [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
- [Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때](./router-dispatcher-handlermapping-vs-selector-factory.md)
- [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [DispatcherServlet vs HandlerInterceptor](../spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: registry primer lookup table resolver router service locator, lookup table vs registry beginner, resolver vs registry beginner, router vs registry beginner, service locator vs registry beginner, registry service locator difference, lookup table resolver router service locator difference, registry pattern beginner, registry 언제 쓰는지, registry 처음 배우는데, lookup table 처음 배우는데, resolver router registry 처음 배우는데, service locator 처음 배우는데, router vs dispatcher naming, request routing naming bridge

---

## Quick check

- key에 이미 등록된 값을 찾으면 `lookup table` / `registry`
- 애매한 입력을 도메인 의미로 풀면 `resolver`
- 요청을 어느 처리 경로로 보낼지 고르면 `router`
- 코드 본문에서 전역 조회소로 의존성을 꺼내면 `service locator` 냄새

헷갈리면 먼저 "`무엇을 찾나`"보다 "`어떤 질문에 답하나`"로 자르면 된다.

처음 읽는 사람 기준으로는 아래 비유가 가장 빠르다.

- `registry`: 주소록에서 이름표를 보고 연락처를 찾는다.
- `resolver`: 줄임말이나 별명을 실제 사람 이름으로 풀어 준다.
- `router`: 이 손님을 어느 창구로 보낼지 정한다.
- `service locator`: 필요한 사람을 그때그때 몰래 사내 전체 주소록에서 찾아온다.

이 비유는 입문용이다. 실제 코드에서는 "찾는다"는 겉모양보다 **의존성이 드러나는지**, **입력 해석이 섞였는지**를 더 중요하게 본다.

이번 문서도 beginner scope까지만 다룬다. service locator를 운영 anti-pattern 전체로 확장하지 않고, 여기서는 "좁은 registry인지 숨은 전역 조회인지"를 가르는 경고 표지판 역할만 한다.

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

## 처음 보는 코드에서 10초 판단표

| 코드에서 먼저 보이는 것 | 먼저 붙일 이름 | 왜 그렇게 보나 |
|---|---|---|
| `registry.get(method)` 뒤에 바로 handler를 사용한다 | `registry` | domain key로 이미 등록된 대상을 찾는다 |
| `"CARD"`를 enum이나 도메인 값으로 바꾼다 | `resolver` | raw 입력을 의미 있는 값으로 해석한다 |
| `/payments/card`를 어느 controller로 보낼지 결정한다 | `router` | 요청 흐름 분기가 중심이다 |
| 메서드 안에서 `ApplicationContext.getBean(...)`을 직접 호출한다 | `service locator` 냄새 | 숨은 의존성 조회가 생긴다 |

처음에는 "같은 `Map`을 쓰는가"보다 "호출자가 지금 무엇을 부탁하고 있나"를 먼저 읽으면 된다.

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
- **"왜 `service locator`만 안 좋은 이름으로 따로 빼나요?"**
  registry, resolver, router는 책임이 드러나면 도구가 될 수 있다. 반대로 service locator는 호출 지점에서 실제 의존성이 숨어 버려 테스트와 리뷰가 어려워지는 점이 핵심 문제다.

---

## 검색어별 첫 문서

| 초보 검색어 | 먼저 열 문서 | 이유 |
|---|---|---|
| `lookup table pattern`, `key로 handler 찾기`, `registry 언제 쓰는지` | [Registry Pattern](./registry-pattern.md) | 등록된 객체를 key로 찾는 큰 그림이 핵심이다 |
| `resolver vs registry`, `router vs registry`, `이름이 헷갈림` | 이 문서 | 용어를 먼저 자르고 다음 문서로 보낸다 |
| `ApplicationContext getBean`, `전역 조회소`, `service locator 처음 배우는데` | [Service Locator Antipattern](./service-locator-antipattern.md) | 숨은 의존성 조회 문제를 바로 봐야 한다 |
| `주입된 registry가 locator인지 모르겠음` | [Injected Registry vs Service Locator Checklist](./injected-registry-vs-service-locator-checklist.md) | 생성자 주입과 숨은 lookup을 코드 리뷰 기준으로 자른다 |

다음 단계는 이렇게 잡으면 안전하다.

- "용어가 왜 갈리는지"가 아직 헷갈리면 이 문서를 한 번 더 보고, 바로 아래 체크리스트 문서로 내려간다.
- Spring 코드에서 실제로 어디가 router인지 보고 싶으면 [DispatcherServlet vs HandlerInterceptor](../spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)로 이어간다.
- `getBean()`이 왜 위험한지 감이 안 오면 [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)를 먼저 보고 다시 service locator 문서로 들어간다.

처음 읽는 사람 기준의 안전한 종료선은 이렇다.

- 용어만 구분되면 여기서 멈춘다.
- 생성자 주입과 숨은 lookup 리뷰 기준이 더 필요할 때만 `Injected Registry vs Service Locator Checklist`로 간다.
- request dispatch나 Spring lifecycle까지 함께 보려 할 때만 `DispatcherServlet vs HandlerInterceptor` 같은 framework bridge로 넘긴다.

## 한 줄 정리

처음에는 `lookup table`과 `registry`를 같은 기초 축으로 보고, `resolver`와 `router`는 그 주변의 해석/분기 이름으로 분리하며, `service locator`는 숨은 의존성 조회 안티 패턴으로 따로 경계하면 된다.
