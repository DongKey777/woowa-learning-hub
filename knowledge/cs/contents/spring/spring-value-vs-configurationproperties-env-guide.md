---
schema_version: 3
title: Spring Value vs ConfigurationProperties Env Guide
concept_id: spring/value-vs-configurationproperties-env-guide
canonical: true
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 74
review_feedback_tags:
- value-vs-configurationproperties
- env
- env-var-binding
- configurationproperties-prefix
aliases:
- @Value vs @ConfigurationProperties
- env var binding guide
- ConfigurationProperties prefix
- single property vs grouped config
- relaxed binding config bean
intents:
- comparison
- design
- troubleshooting
linked_paths:
- contents/spring/spring-configurationproperties-binding-internals.md
- contents/spring/spring-relaxed-binding-env-var-cheatsheet.md
- contents/spring/spring-spring-application-json-primer.md
- contents/spring/spring-property-source-precedence-quick-guide.md
- contents/spring/spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md
confusable_with:
- spring/configurationproperties-binding-internals
- spring/relaxed-binding-env-var-cheatsheet
- spring/spring-application-json-primer
expected_queries:
- Spring에서 @Value와 @ConfigurationProperties 중 무엇으로 env var를 읽어야 해?
- 설정 값 하나면 @Value, prefix 아래 여러 값이면 ConfigurationProperties가 맞아?
- ConfigurationProperties가 초급자에게 더 읽기 쉬운 기준은 무엇이야?
- 환경 변수 binding이 안 될 때 relaxed binding과 property source를 어디서 봐야 해?
contextual_chunk_prefix: |
  이 문서는 환경 변수 하나를 빠르게 읽을 때는 @Value도 충분하지만 같은 prefix 아래
  설정이 여러 개 모이면 @ConfigurationProperties로 묶는 편이 더 읽기 쉽고 type-safe하다는
  beginner chooser다.
---
# Spring `@Value` vs `@ConfigurationProperties` Env Guide

> 한 줄 요약: 환경 변수 하나만 빠르게 읽을 때는 `@Value`로도 충분하지만, 같은 prefix 아래 설정이 2~3개 이상 모이기 시작하면 `@ConfigurationProperties`로 묶는 편이 초급자에게도 더 읽기 쉽고 덜 헷갈린다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 "env var를 Bean으로 어떻게 읽을까?"라는 beginner 질문에 대해 `@Value`와 `@ConfigurationProperties`의 선택 기준을 한 장 표와 작은 예제로 설명하는 **beginner env binding guide**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring `SPRING_APPLICATION_JSON` Primer: plain env var보다 나은 순간](./spring-spring-application-json-primer.md)
> - [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

retrieval-anchor-keywords: spring @value vs @configurationproperties, spring env guide beginner, single env var vs grouped config, spring property binding choice, spring env var one value, spring env var grouped properties, configurationproperties beginner primer, @value beginner env, grouped configuration bean, env var binding mental model, app payment timeout base url api key, spring config object vs single property, when to move from @value to configurationproperties, spring value vs configurationproperties env guide basics, spring value vs configurationproperties env guide beginner

## 핵심 개념

초급자 기준으로는 먼저 이렇게 나누면 된다.

```text
환경 변수 1개를 "값"으로 읽는다 -> @Value
관련 환경 변수 여러 개를 "설정 묶음"으로 읽는다 -> @ConfigurationProperties
```

즉 질문은 "`@Value`가 더 간단한가?"가 아니라 아래에 가깝다.

```text
지금 필요한 것이 값 1개인가,
아니면 이름이 붙은 설정 묶음 1개인가?
```

`@Value`는 주사기처럼 값을 한 곳에 꽂는 느낌이고,
`@ConfigurationProperties`는 작은 설정 전용 DTO를 하나 만드는 느낌이다.

---

## 1. 먼저 고르는 표

| 상황 | 먼저 선택 | 이유 |
|---|---|---|
| feature flag 하나가 필요하다 | `@Value` | 한 값만 읽으면 끝난다 |
| timeout 값 하나만 실험적으로 붙인다 | `@Value` | 코드가 짧고 빠르다 |
| `app.mail.host`, `app.mail.port`, `app.mail.from`처럼 같이 움직인다 | `@ConfigurationProperties` | 한 객체로 묶어 읽는 편이 구조가 선명하다 |
| 같은 prefix를 여러 클래스에서 반복해서 읽는다 | `@ConfigurationProperties` | 설정 이름이 흩어지는 것을 줄인다 |
| validation이 필요하다 | `@ConfigurationProperties` | 설정 객체에 규칙을 함께 둘 수 있다 |
| list/map/nested 구조가 있다 | `@ConfigurationProperties` | `@Value`보다 훨씬 자연스럽다 |

beginner가 실무 감각으로 기억할 규칙은 이 정도면 충분하다.

- 설정 1개면 `@Value`
- 설정 묶음이면 `@ConfigurationProperties`
- 같은 prefix가 반복되면 "이제 묶을 때가 됐나?"를 먼저 의심한다

---

## 2. `@Value`가 잘 맞는 순간

예를 들어 외부 API 호출 timeout 하나만 필요하다고 하자.

```yaml
app:
  payment-timeout-ms: 1500
```

운영 환경 변수는 대략 이렇게 둘 수 있다.

```text
APP_PAYMENTTIMEOUTMS=1500
```

코드는 아래처럼 읽을 수 있다.

```java
@Service
public class PaymentClient {

    private final long paymentTimeoutMs;

    public PaymentClient(@Value("${app.payment-timeout-ms}") long paymentTimeoutMs) {
        this.paymentTimeoutMs = paymentTimeoutMs;
    }
}
```

이 경우 `@Value`가 어색하지 않은 이유는 단순하다.

- 읽는 값이 하나다
- 이름이 짧다
- 다른 설정과 함께 모델링할 필요가 아직 없다

### 이런 경우까지는 `@Value`를 무리해서 바꾸지 않아도 된다

| 예시 | 판단 |
|---|---|
| `@Value("${feature.order-cache-enabled}")` | 괜찮다 |
| `@Value("${server.shutdown.grace-period}")` | 괜찮다 |
| 테스트용으로 잠깐 읽는 값 하나 | 괜찮다 |

---

## 3. `@ConfigurationProperties`로 옮겨야 할 순간

이번에는 메일 설정이 있다고 하자.

```yaml
app:
  mail:
    host: smtp.example.com
    port: 587
    from: no-reply@example.com
```

환경 변수로는 아래처럼 들어올 수 있다.

```text
APP_MAIL_HOST=smtp.example.com
APP_MAIL_PORT=587
APP_MAIL_FROM=no-reply@example.com
```

이걸 `@Value`로 읽으면 보통 이렇게 된다.

```java
@Service
public class MailService {

    public MailService(
            @Value("${app.mail.host}") String host,
            @Value("${app.mail.port}") int port,
            @Value("${app.mail.from}") String from
    ) {
    }
}
```

처음엔 동작해도, 초급자 기준으로는 금방 읽기 어려워진다.

- 생성자에서 "비즈니스 의존성"과 "설정 문자열"이 섞인다
- 같은 prefix `app.mail`이 여러 번 반복된다
- 나중에 `username`, `password`, `connect-timeout`이 추가되면 더 길어진다

이때는 설정을 객체로 빼는 편이 낫다.

```java
@ConfigurationProperties(prefix = "app.mail")
public record MailProperties(
        String host,
        int port,
        String from
) {
}
```

```java
@Service
public class MailService {

    private final MailProperties mailProperties;

    public MailService(MailProperties mailProperties) {
        this.mailProperties = mailProperties;
    }
}
```

이제 코드가 말하는 바가 훨씬 선명하다.

```text
MailService는 host/port/from 세 개의 흩어진 값이 아니라
"메일 설정"이라는 한 덩어리에 의존한다.
```

주의: 이 타입이 실제 Bean으로 등록되려면 보통 `@ConfigurationPropertiesScan` 또는 `@EnableConfigurationProperties(MailProperties.class)` 같은 등록 경로가 있어야 한다.

---

## 4. 한 장 비교: 무엇이 더 초급자에게 읽기 쉬운가

| 항목 | `@Value` | `@ConfigurationProperties` |
|---|---|---|
| mental model | 값 하나 주입 | 설정 객체 바인딩 |
| 잘 맞는 크기 | 1개, 많아도 2개 정도 | 관련 설정 묶음 |
| prefix 반복 | 많아질수록 피곤함 | prefix 한 번으로 끝남 |
| nested/list/map | 금방 불편해짐 | 자연스럽다 |
| validation | 따로 흩어지기 쉬움 | 객체에 함께 두기 쉽다 |
| beginner가 읽을 때 | 빠르게 시작 가능 | 구조가 커질수록 더 읽기 쉬움 |

`@Value`가 "나쁜 방식"은 아니다.
문제는 **설정이 커졌는데도 계속 단일 값 주입만 늘리는 것**이다.

---

## 5. 언제 리팩터링 신호로 보면 되나

아래 셋 중 둘 이상이면 `@ConfigurationProperties` 전환을 먼저 떠올리면 된다.

1. 같은 prefix를 세 번 이상 쓰고 있다
2. 같은 서비스 생성자에 설정값이 여러 개 들어온다
3. 설정 이름만 읽어도 하나의 도메인 묶음처럼 보인다

예를 들면 이런 식이다.

```text
app.client.base-url
app.client.connect-timeout
app.client.read-timeout
app.client.api-key
```

이건 사실상 "client 설정" 하나다.
이럴 때 `@Value` 네 개보다 `ClientProperties` 하나가 더 설명력이 높다.

---

## 6. 자주 하는 혼동

### 혼동 1. `@Value`가 더 쉬우니까 항상 더 좋은 선택이다

짧게 시작하기는 쉽다.
하지만 설정이 늘어나면 "쉬운 시작"이 "흩어진 설정"으로 바뀌기 쉽다.

### 혼동 2. env var를 쓰면 무조건 `@Value`를 써야 한다

아니다. env var는 값이 들어오는 **source**일 뿐이다.
그 값을 코드에서 단일 값으로 받을지, 설정 객체로 묶을지는 별도 선택이다.

### 혼동 3. `@ConfigurationProperties`는 무조건 거대한 고급 기능이다

초급자 기준으로는 그냥 "관련 설정을 담는 Bean" 정도로 이해해도 충분하다.
advanced 주제인 binder internals, metadata, validation 확장은 나중에 붙이면 된다.

### 혼동 4. `@Value` 여러 개와 `@ConfigurationProperties` 하나는 완전히 다른 세계다

둘 다 결국 외부 설정을 Bean 세계로 가져오는 방법이다.
차이는 "값 단위로 읽느냐"와 "객체 단위로 묶느냐"에 있다.

---

## 7. 선택 순서 추천

처음 보는 코드에서는 아래 순서로 보면 가장 덜 헷갈린다.

1. 필요한 설정이 한 값인지, 한 묶음인지 본다
2. env var 이름이 맞는지 확인한다
3. `@ConfigurationProperties`라면 등록 포인트까지 같이 찾는다

짧게 압축하면:

```text
값 하나면 @Value
설정 묶음이면 @ConfigurationProperties
```

env var 이름 자체가 헷갈리면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)로 바로 이어가고,
"왜 다른 값이 들어왔지?"가 핵심이면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)로 넘어가면 된다.

## 한 줄 정리

초급자 기준 최선의 기준은 단순하다. 단일 env var를 빠르게 읽을 때는 `@Value`, 같은 이름 아래 움직이는 설정 묶음을 읽을 때는 `@ConfigurationProperties`를 고른다.
