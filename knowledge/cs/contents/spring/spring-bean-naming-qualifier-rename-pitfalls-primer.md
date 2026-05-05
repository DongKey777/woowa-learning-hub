---
schema_version: 3
title: 'Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가'
concept_id: spring/bean-naming-qualifier-rename-pitfalls-primer
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/lotto
- missions/shopping-cart
review_feedback_tags:
- qualifier-string-contract
- bean-rename-ripple
- bean-name-vs-qualifier
aliases:
- spring bean naming
- bean rename pitfall
- default bean name
- bean alias
- qualifier string rename
- router vs qualifier confusion
- resource vs qualifier
- name driven injection
- type driven injection
- kotlin bean rename
- nosuchbeandefinitionexception
- 처음 배우는데 bean 이름이 왜 바뀌어요
- qualifier 문자열이 왜 깨져요
- spring bean naming qualifier rename pitfalls primer basics
- spring bean naming qualifier rename pitfalls primer beginner
symptoms:
- 클래스 이름이나 `@Bean` 메서드 이름을 바꿨더니 주입이 갑자기 깨졌어요
- `@Qualifier` 문자열이 어디서 온 이름인지 몰라서 rename이 무서워요
- bean 이름, alias, qualifier 값이 같은 건지 다른 건지 헷갈려요
intents:
- definition
prerequisites:
- spring/bean-di-basics
next_docs:
- spring/primary-qualifier-collection-injection
- spring/spring-custom-qualifier-primer
- spring/di-exception-quick-triage
linked_paths:
- contents/spring/spring-bean-di-basics.md
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md
- contents/spring/spring-custom-qualifier-primer.md
- contents/spring/spring-di-exception-quick-triage.md
- contents/design-pattern/bean-name-vs-domain-key-lookup.md
confusable_with:
- spring/primary-qualifier-collection-injection
- spring/spring-custom-qualifier-primer
- spring/di-exception-quick-triage
forbidden_neighbors:
- contents/spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md
expected_queries:
- 클래스 이름 바꿨더니 왜 예전 qualifier 문자열이 계속 문제를 일으켜?
- `@Component` 기본 bean 이름이 실제로 어떻게 정해지는지 처음부터 알고 싶어
- `@Bean` 메서드명을 바꾸면 주입 지점까지 왜 같이 깨질 수 있어?
- bean 이름이랑 qualifier 값이 같은 규칙으로 이어지는지 헷갈릴 때 어디서 정리해?
- 문자열 기반 주입이 rename에 약한 이유를 스프링 기준으로 설명해줘
- alias를 붙이면 rename 충격을 줄일 수 있는지 감이 안 와
contextual_chunk_prefix: |
  이 문서는 스프링 학습자가 component bean 기본 이름, `@Bean` 메서드 이름,
  alias, `@Qualifier` 문자열이 어떤 계약으로 이어지는지 처음 정리하는
  primer다. 클래스 이름을 바꿨더니 qualifier가 깨진다, bean 이름과 qualifier
  값이 같은 건지 헷갈린다, alias를 붙이면 rename 충격을 줄일 수 있는지
  모르겠다 같은 자연어 질문을 이름 계약과 주입 계약 분리로 연결한다.
---
# Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가

> 한 줄 요약: `@Qualifier("name")`가 안전한지 보려면 먼저 그 문자열이 bean 이름인지, alias인지, 별도 qualifier 값인지부터 구분해야 한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 component bean 이름, `@Bean` 메서드 이름, 문자열 qualifier가 서로 어떻게 연결되는지와 rename 때 어디서 깨지는지를 beginner 기준으로 묶어 주는 **bean naming primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
- [Bean Name vs Domain Key Lookup](../design-pattern/bean-name-vs-domain-key-lookup.md)

retrieval-anchor-keywords: spring bean naming, bean rename pitfall, default bean name, bean alias, qualifier string rename, router vs qualifier confusion, resource vs qualifier, name driven injection, type driven injection, kotlin bean rename, nosuchbeandefinitionexception, 처음 배우는데 bean 이름이 왜 바뀌어요, qualifier 문자열이 왜 깨져요, spring bean naming qualifier rename pitfalls primer basics, spring bean naming qualifier rename pitfalls primer beginner

## 이 문서 다음에 보면 좋은 문서

- Bean 등록과 DI 전체 흐름을 먼저 한 장으로 보고 싶다면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)로 이어진다.
- 여러 후보 중 하나를 고르는 `@Primary`/`@Qualifier`/컬렉션 주입 선택은 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어진다.
- `rename` 문제를 보다가 "이거 router로 풀어야 하나?"가 먼저 떠오르면 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)로 바로 빠져나가 `고정 wiring`과 `runtime 분기`를 먼저 자른다.
- 문자열 qualifier가 반복될 때 역할 annotation으로 올리는 기준은 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)에서 본다.
- startup 에러가 이미 `NoSuchBeanDefinitionException`, `NoUniqueBeanDefinitionException`로 터졌다면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)로 바로 이어진다.
- 특히 `NoUniqueBeanDefinitionException`가 먼저 보이면 rename보다 "여러 후보 중 하나를 어떻게 고를지"가 핵심일 수 있으니 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 역방향 안내한다.

---

## 30초 분기표: 지금 rename부터 의심해도 되는가

처음에는 에러 전문을 길게 읽기보다, **예외 이름과 최근 변경 종류**만 보고 먼저 갈라 타면 된다.

| 먼저 보이는 신호 | 첫 판단 | 바로 다음 행동 |
|---|---|---|
| `NoSuchBeanDefinitionException` + 방금 클래스명/`@Bean` 메서드명/`@Qualifier` 문자열을 바꿨다 | `rename` 때문에 **이름 계약이 끊겼을 가능성**이 크다 | 아래 1, 2, 5장을 보고 기본 bean 이름이 바뀌었는지와 old qualifier 문자열이 남았는지 확인한다 |
| `NoUniqueBeanDefinitionException` | rename보다 **같은 타입 후보가 여러 개라 선택 실패**했을 가능성이 크다 | 이 문서보다 먼저 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 간다 |
| `qualifier` 문자열이 반복돼서 "이거 router 문제 아닌가?"가 먼저 든다 | rename보다 **고정 wiring과 runtime 분기를 섞어 읽는 중**일 수 있다 | [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)로 먼저 가서 router 경계를 자른다 |
| `NoSuchBeanDefinitionException`인데 rename은 안 했고 starter/scan/config를 건드렸다 | rename보다 **bean 자체가 안 올라왔을 가능성**이 크다 | [Spring DI 예외 빠른 판별](./spring-di-exception-quick-triage.md)이나 scan/condition 문서로 가서 등록 누락부터 본다 |

한 줄로 줄이면 이렇다.

- `NoUnique`면 먼저 "무엇을 고를지" 문제다.
- `NoSuch` + rename 직후면 "이름이 바뀌었는지" 문제다.
- `NoSuch` + 등록 경로 변경 직후면 "bean이 아예 생겼는지" 문제다.

---

## 먼저 이 다섯 줄만 잡기

- 이름 없는 `@Component` 계열 bean은 **기본 bean 이름이 클래스명에서 만들어진다**
- 이름 없는 `@Bean`은 **기본 bean 이름이 메서드명이다**
- `@Component("name")`, `@Bean(name = "name")`는 **rename과 분리된 명시적 이름 계약**이다
- `@Bean(name = {"newName", "oldName"})`는 **하나의 bean에 여러 이름(alias)** 을 붙인다
- `@Qualifier("name")`는 보통 **같은 타입 후보 안에서 이름이나 qualifier 값으로 더 좁히는 장치**다

beginner가 자주 헷갈리는 지점은 "`@Qualifier(\"name\")`면 무조건 bean id를 집는 것 아닌가?"인데, Spring은 먼저 **타입 후보를 모은 뒤** 그 안에서 qualifier와 bean 이름을 본다.

> 역방향 안내:
> `NoUniqueBeanDefinitionException`는 보통 "이름이 깨졌다"보다 "타입 후보가 여러 개라 하나를 못 골랐다"에 가깝다.
> 이 경우 rename 추적보다 먼저 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)에서 선택 규칙을 고른다.

---

## 1. `@Component` 기본 bean 이름은 클래스명에서 온다

component scan으로 발견되는 bean은 기본적으로 simple class name을 기준으로 이름이 만들어진다.

| 선언 | 실제 bean 이름 |
|---|---|
| `@Component class OrderService {}` | `orderService` |
| `@Service class PaymentFacade {}` | `paymentFacade` |
| `@Component("mainPaymentClient") class KakaoPaymentClient {}` | `mainPaymentClient` |

즉, 이름을 따로 주지 않으면 보통은 **클래스명의 첫 글자만 소문자**가 된다고 생각해도 초반 감각으로는 충분하다.

다만 아래 한 가지는 같이 기억해 두는 편이 좋다.

```java
@Component
public class URLParser {
}
```

이 경우 기본 bean 이름은 `uRLParser`가 아니라 `URLParser`다.
Spring이 기본 이름을 만들 때 Java `Introspector.decapitalize` 규칙을 따라가기 때문이다.

beginner 실수는 대개 여기서 나온다.

- 클래스 이름을 바꿨다
- explicit name은 안 붙였다
- 그런데 주입 지점 어딘가에 `@Qualifier("oldClassNameBasedBean")`가 남아 있다

그러면 bean은 살아 있는데 **이름 계약만 깨져서** 주입 실패가 난다.

---

## 2. `@Bean` 기본 bean 이름은 메서드명이다

`@Bean`은 규칙이 더 단순하다. 이름을 지정하지 않으면 **메서드명 그대로** bean 이름이 된다.

```java
@Configuration
public class PaymentConfig {

    @Bean
    public PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

위 bean 이름은 `kakaoPaymentClient`다.

이제 메서드명을 바꾸면 어떻게 되는지 보자.

```java
@Configuration
public class PaymentConfig {

    @Bean
    public PaymentClient primaryPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이제 bean 이름은 `primaryPaymentClient`가 된다.
즉, `@Bean` 메서드 rename은 생각보다 쉽게 qualifier 문자열을 깨뜨린다.

Kotlin도 규칙은 같다. `fun` 이름이 곧 기본 bean 이름이 된다.

| 선언 언어 | 이름 없는 `@Bean` 선언 | 실제 기본 bean 이름 |
|---|---|---|
| Java | `paymentClient()` | `paymentClient` |
| Kotlin | `fun paymentClient()` | `paymentClient` |

초보자 감각으로는 이렇게 보면 된다.

- `@Bean` 이름을 안 적었다
- 그러면 Java의 메서드명, Kotlin의 함수명이 bean 이름이 된다
- 그래서 **Kotlin에서 함수 rename도 bean rename**이다

이 위험을 줄이는 가장 쉬운 방법은 이름을 명시하는 것이다.

```java
@Configuration
public class PaymentConfig {

    @Bean(name = "mainPaymentClient")
    public PaymentClient primaryPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이제 메서드명을 `primaryPaymentClient`에서 `kakaoGatewayClient`로 바꿔도 bean 이름은 계속 `mainPaymentClient`다.

## 2-1. Kotlin 함수 rename은 bean rename일 수 있다

Kotlin 설정 코드에서 아래 패턴이 자주 나온다.

```kotlin
@Configuration
class PaymentConfig {

    @Bean
    fun kakaoPaymentClient(): PaymentClient {
        return KakaoPaymentClient()
    }
}

@Service
class BillingService(
    @Qualifier("kakaoPaymentClient")
    private val paymentClient: PaymentClient,
)
```

처음에는 "`@Qualifier` 문자열만 바꾸면 되겠지"라고 보기 쉬운데, 실제로는 반대 순서로 보는 편이 안전하다.

1. 이름 없는 `@Bean`인가?
2. 그렇다면 Kotlin `fun` 이름이 bean 이름인가?
3. 그 이름을 `@Qualifier("...")`가 기대하고 있는가?

예를 들어 함수명을 이렇게 바꾸면:

```kotlin
@Configuration
class PaymentConfig {

    @Bean
    fun mainPaymentClient(): PaymentClient {
        return KakaoPaymentClient()
    }
}
```

bean 이름도 같이 `mainPaymentClient`로 바뀐다.
하지만 주입 쪽이 아직 `@Qualifier("kakaoPaymentClient")`면 `NoSuchBeanDefinitionException` 경로로 깨질 수 있다.

짧게 비교하면 이렇다.

| Kotlin 변경 | bean 이름 변화 | 문자열 주입 영향 |
|---|---|---|
| `fun kakaoPaymentClient()` -> `fun mainPaymentClient()` | 바뀜 | `@Qualifier("kakaoPaymentClient")`가 깨질 수 있음 |
| `@Bean("mainPaymentClient") fun kakaoPaymentClient()` -> 함수명만 rename | 안 바뀜 | `@Qualifier("mainPaymentClient")`는 유지 가능 |
| `@Bean("mainPaymentClient", "kakaoPaymentClient")`로 잠깐 alias 운영 | 새 이름과 옛 이름 둘 다 허용 | 점진 migration 가능 |

즉, Kotlin에서 rename 안전성을 높이고 싶다면 "함수명을 예쁘게 바꾼다"보다 **bean 이름 계약을 먼저 분리한다**가 핵심이다.

---

## 3. `@Bean(name = ...)`의 배열은 alias까지 만든다

`@Bean(name = ...)`는 문자열 하나만 받는 것이 아니라 여러 이름도 받을 수 있다.

```java
@Configuration
public class PaymentConfig {

    @Bean(name = {"mainPaymentClient", "legacyPaymentClient"})
    public PaymentClient paymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이 경우 핵심은 두 가지다.

- 메서드명 `paymentClient`는 bean 이름으로 쓰이지 않는다
- `mainPaymentClient`, `legacyPaymentClient` 둘 다 이 bean을 가리킨다

rename migration 관점에서는 꽤 유용하다.

- 새 이름은 `mainPaymentClient`로 옮기고 싶다
- 그런데 기존 `@Qualifier("legacyPaymentClient")`가 아직 남아 있다

이럴 때 alias로 잠깐 다리 놓고, 나중에 old name을 걷어내면 된다.

단, alias는 **영구 안전장치**가 아니라 **이행 단계의 빚**에 가깝다. 오래 남기면 오히려 어떤 이름이 표준인지 흐려진다.

---

## 4. 문자열 `@Qualifier`는 bean 이름과 어떻게 엮이는가

가장 자주 쓰는 beginner 예제는 아래다.

```java
public interface PaymentClient {
    void pay();
}

@Component("mainPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}

@Component("backupPaymentClient")
public class TestPaymentClient implements PaymentClient {
}

@Service
public class BillingService {
    private final PaymentClient paymentClient;

    public BillingService(@Qualifier("mainPaymentClient") PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }
}
```

여기서 `@Qualifier("mainPaymentClient")`는 `PaymentClient` 타입 후보들 중에서 `mainPaymentClient`와 맞는 후보를 고르게 돕는다.

초보자용으로는 아래처럼 이해하면 된다.

| 주입 지점 문자열 | 무엇과 연결될 수 있는가 |
|---|---|
| `@Qualifier("mainPaymentClient")` | bean 이름 `mainPaymentClient` |
| `@Qualifier("legacyPaymentClient")` | alias `legacyPaymentClient` |
| `@Qualifier("main")` | bean 쪽에 따로 붙인 qualifier 값 `@Qualifier("main")` |

즉, 문자열 qualifier는 "항상 bean 이름만 본다"가 아니라, **bean 이름과 alias는 fallback으로 엮일 수 있고, 별도 qualifier 메타데이터와도 엮일 수 있다**고 이해하는 편이 맞다.

그래서 아래 둘은 비슷해 보이지만 의미가 완전히 같지는 않다.

```java
@Component("mainPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}
```

```java
@Component
@Qualifier("main")
public class KakaoPaymentClient implements PaymentClient {
}
```

첫 번째는 bean 이름 계약에 가깝고, 두 번째는 의미 qualifier 계약에 가깝다.

---

## 5. rename 때 실제로 어디서 깨지는가

### 5-1. 이름 없는 `@Component` + 문자열 qualifier

```java
@Component
public class KakaoPaymentClient implements PaymentClient {
}

@Service
public class BillingService {
    public BillingService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
    }
}
```

여기서 클래스명을 `MainPaymentClient`로 바꾸면 기본 bean 이름도 `mainPaymentClient`로 바뀐다.
그런데 qualifier 문자열은 그대로 `kakaoPaymentClient`면 주입이 깨진다.

### 5-2. 이름 없는 `@Bean` + 문자열 qualifier

```java
@Configuration
public class PaymentConfig {

    @Bean
    public PaymentClient kakaoPaymentClient() {
        return new KakaoPaymentClient();
    }
}
```

이 상태에서 메서드명을 `mainPaymentClient()`로 바꾸면, bean 이름도 같이 바뀐다.
이미 `@Qualifier("kakaoPaymentClient")`가 퍼져 있으면 같이 깨진다.

Kotlin도 같은 식으로 읽으면 된다.

```kotlin
@Configuration
class PaymentConfig {

    @Bean
    fun kakaoPaymentClient(): PaymentClient {
        return KakaoPaymentClient()
    }
}
```

여기서 `fun kakaoPaymentClient()`를 `fun mainPaymentClient()`로 rename하면, Spring 입장에서는 bean 이름도 함께 rename한 셈이다.

여기서 바로 기억할 한 줄은 이것이다.

- **Kotlin `fun` rename != 코드 정리만 한 것**
- 이름 없는 `@Bean`이라면 **DI 이름 계약까지 바꾼 것**이다

### 5-3. 주입 파라미터명 fallback도 rename 함정이 될 수 있다

`@Qualifier`가 없어도 Spring은 비슷한 후보가 여러 개일 때 **필드명이나, 이름 정보가 보이는 생성자 파라미터명과 bean 이름이 같으면** 그 후보를 고를 수 있다.

```java
@Service
public class BillingService {
    public BillingService(PaymentClient mainPaymentClient) {
    }
}
```

이런 코드는 겉보기엔 qualifier가 없지만, 사실상 이름 계약이 숨어 있을 수 있다.
그래서 parameter rename만 해도 해석 결과가 달라질 수 있다.

beginner 기준으로는 아래만 기억하면 된다.

## 5. rename 때 실제로 어디서 깨지는가 (계속 2)

- 문자열 `@Qualifier`만 rename 함정이 아니다
- **기본 bean 이름 + 파라미터명 일치**도 숨어 있는 이름 계약이 될 수 있다

---

## 6. beginner가 바로 쓰기 좋은 안전한 선택지

| 상황 | 추천 선택 | 이유 |
|---|---|---|
| 클래스명 rename은 자유롭게 하고 싶다 | `@Component("stableName")` | 클래스명과 bean 이름 계약을 분리한다 |
| `@Bean` 메서드 rename은 자유롭게 하고 싶다 | `@Bean(name = "stableName")` | 메서드명 변경이 bean 이름을 흔들지 않는다 |
| old 이름과 new 이름을 잠깐 같이 받아야 한다 | `@Bean(name = {"newName", "oldName"})` | 점진 migration이 가능하다 |
| 같은 문자열 qualifier가 여러 군데 반복된다 | 커스텀 qualifier annotation | bean 이름 문자열 의존을 줄인다 |
| 정말 "이 이름의 bean"을 가리키는 의도가 중요하다 | `@Resource(name = "...")` 검토 | `@Autowired` + `@Qualifier`보다 by-name 의미가 더 직접적이다 |

마지막 줄은 살짝 고급 포인트지만, 감각만 잡아 두면 좋다.

- `@Autowired` + `@Qualifier`는 기본적으로 **type-driven injection**
- `@Resource(name = "...")`는 기본적으로 **name-driven injection**

## 6-1. `@Resource` vs `@Qualifier` 한 표로 끝내기

rename 문서에서 마지막 선택지가 자꾸 느리게 읽히면, 아래 표만 먼저 보면 된다.

| 비교 축 | `@Autowired` + `@Qualifier("mainPaymentClient")` | `@Resource(name = "mainPaymentClient")` |
|---|---|---|
| 초보자용 한 줄 감각 | "이 타입 후보들 중 이쪽을 더 좁힌다" | "이 이름의 bean을 바로 찾는다" |
| 기본 출발점 | 타입 후보 수집 | 이름 매칭 |
| rename에 민감한 지점 | bean 이름 문자열, qualifier 문자열 | bean 이름 문자열 |
| 잘 맞는 상황 | 생성자 주입에서 특정 후보 1개를 고정 | 필드/setter 주입에서 이름 계약 자체가 핵심 |
| 이 문서에서의 해석 | type-driven 주입 쪽 | name-driven 주입 쪽 |

처음엔 이렇게만 외우면 충분하다.

- "같은 타입 후보가 여러 개라서 이번 파라미터 하나만 고른다"면 `@Qualifier`
- "애초에 이 이름의 bean을 집는 게 의도다"면 `@Resource`
- 생성자 주입을 유지하고 싶다면 실무에서는 대체로 `@Qualifier`나 커스텀 qualifier가 더 자연스럽다

즉, "이 역할의 같은 타입 후보 중에서 좁힌다"면 qualifier 쪽이고, "유일한 이 이름을 집는다"가 핵심이면 `@Resource`가 더 의미상 가깝다.

다만 `@Resource`는 생성자 파라미터에 붙이는 도구가 아니므로, 생성자 주입에서는 explicit bean name + `@Qualifier`나 커스텀 qualifier 쪽이 현실적인 선택이다.

Kotlin 초급자에게는 아래 두 줄이 가장 실용적이다.

- 함수명 rename을 자주 할 것 같으면 `@Bean("stableName")`로 bean 이름을 먼저 고정한다
- 문자열 `@Qualifier`가 자꾸 따라다니면 [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md)으로 넘어가 역할 annotation으로 올린다

---

## 7. 문서 간 경계 한 번에 정리

| 질문 | 먼저 볼 문서 |
|---|---|
| bean이 어떻게 등록되고 주입되는지 전체 감각이 부족하다 | [Spring Bean과 DI 기초](./spring-bean-di-basics.md) |
| `NoUniqueBeanDefinitionException`가 떠서 rename 문제인지 헷갈린다 | [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md) |
| 같은 타입 후보가 여러 개일 때 `@Primary`/`@Qualifier`/컬렉션 중 뭘 써야 할지 헷갈린다 | [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md) |
| 문자열 qualifier를 역할 annotation으로 올려야 할지 고민된다 | [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md) |
| 에러가 이미 `NoSuchBeanDefinitionException`로 터졌다 | [Spring DI 예외 빠른 판별](./spring-di-exception-quick-triage.md) |

---

## 꼬리질문

> Q: `@Qualifier("beanName")`는 bean id를 직접 참조하는 것인가?
> 의도: qualifier와 by-name injection을 구분하는지 확인
> 핵심: 실무에서는 그렇게 보이기 쉽지만, Spring은 보통 타입 후보를 먼저 모으고 그 안에서 qualifier/bean 이름으로 좁힌다.

> Q: 이름 없는 `@Component`에서 클래스 rename이 왜 위험한가?
> 의도: 기본 bean 이름 생성 규칙이 class name에 묶인다는 점을 확인
> 핵심: 기본 bean 이름도 같이 바뀌기 때문에 문자열 qualifier나 이름 기반 fallback이 같이 깨질 수 있다.

> Q: `@Bean(name = "mainClient")`를 쓰면 메서드 rename은 안전한가?
> 의도: explicit bean name과 method name을 분리하는지 확인
> 핵심: 그렇다. `name`을 지정하면 메서드명은 bean 이름으로 쓰이지 않는다.

> Q: `@Bean(name = {"newName", "oldName"})`는 계속 오래 둬도 되는가?
> 의도: alias를 migration bridge로 보는지 확인
> 핵심: 가능은 하지만 old 이름 의존을 오래 숨기므로, transition이 끝나면 정리하는 편이 낫다.

---

## 한 줄 정리

이름 없는 `@Component`는 클래스명, 이름 없는 `@Bean`은 메서드명에 묶이고, 문자열 `@Qualifier`는 그 이름 계약에 기대기 쉽기 때문에 rename이 잦다면 explicit name이나 커스텀 qualifier로 계약을 분리하는 편이 안전하다.
