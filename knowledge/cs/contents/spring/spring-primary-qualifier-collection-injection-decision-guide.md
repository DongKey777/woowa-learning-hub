# Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집

> 한 줄 요약: 같은 타입 bean이 여러 개일 때 `@Primary`는 "기본으로 하나", `@Qualifier`는 "이번 주입에서 이걸", `List<T>`/`Map<String, T>`는 "후보를 전부 달라"에 가깝다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 단일 후보 기본값, 명시 선택, 다중 후보 수집을 한 표와 짧은 예제로 먼저 구분하게 돕는 **beginner quick decision guide**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
> - [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
> - [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
> - [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
> - [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
> - [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)

retrieval-anchor-keywords: @Primary vs @Qualifier vs collection injection, spring multiple bean decision guide, spring bean candidate selection, single default bean, explicit bean pick, multiple bean collect, list injection, map injection, List<T> injection, Map<String, T> injection, NoUniqueBeanDefinitionException choice, default candidate vs qualifier, qualifier beats primary, primary not applied to list, bean name map key, runtime strategy selection, router pattern, Map<String, Bean> router, runtime dispatch vs qualifier, @ConditionalOnMissingBean vs @Primary, primary is not auto-configuration override

## 이 문서 다음에 보면 좋은 문서

- 같은 타입 후보가 여러 개인 이유와 `ObjectProvider`까지 같이 보고 싶다면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)로 이어진다.
- 문자열 `@Qualifier("beanName")`가 실제로 어떤 bean naming 규칙과 alias에 묶이는지 먼저 분리하고 싶다면 [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)로 이어진다.
- 문자열 `@Qualifier("beanName")`를 언제 커스텀 역할 annotation으로 올려야 하는지는 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)로 이어진다.
- collection 주입 다음 단계로 runtime router까지 이어서 보고 싶다면 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)로 이어진다.
- startup 로그에서 `found 2`가 보여서 이 문제를 디버깅 중이라면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)로 이어진다.
- "`@Primary`를 붙였는데 Boot 기본 bean은 왜 안 돌아오지?"처럼 auto-configuration back-off와 후보 선택이 섞이면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이어진다.

---

## 핵심 결정표

같은 타입 bean이 여러 개일 때는 먼저 "하나를 기본값으로 받고 싶은가, 특정 하나를 찍고 싶은가, 전부 모으고 싶은가"부터 나눈다.

| 내가 원하는 것 | 고를 도구 | 주입 선언 예시 | 기억할 포인트 |
|---|---|---|---|
| 보통은 하나를 쓰되 기본값이 있으면 된다 | `@Primary` | `CheckoutService(PaymentClient paymentClient)` | 단일 bean 주입에서만 기본 우선순위가 생긴다 |
| 이번 주입 지점은 특정 후보여야 한다 | `@Qualifier` | `RefundService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient)` | 주입 지점의 선택 규칙이 `@Primary`보다 더 구체적이다 |
| 후보를 전부 받아 직접 고르거나 순회해야 한다 | `List<T>` / `Map<String, T>` | `PaymentRouter(List<PaymentClient> clients, Map<String, PaymentClient> clientMap)` | `@Primary`가 있어도 matching bean이 전부 들어간다 |

초보자 기준으로는 아래 세 줄로 외우면 된다.

- 기본 후보 하나 정하기 -> `@Primary`
- 이번 파라미터에서 특정 후보 찍기 -> `@Qualifier`
- 여러 구현체를 다 모아 직접 고르기 -> 컬렉션 주입

---

## 짧은 예제 하나로 끝내기

아래처럼 `PaymentClient` 구현체가 둘 있다고 가정한다.

```java
public interface PaymentClient {
    void pay();
}

@Component
@Primary
public class TossPaymentClient implements PaymentClient {
}

@Component("kakaoPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}
```

이제 주입 방식에 따라 의미가 갈린다.

### 1. `@Primary`: "기본값으로 하나"

```java
@Service
public class CheckoutService {
    private final PaymentClient paymentClient;

    public CheckoutService(PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }
}
```

이 경우 `CheckoutService`는 기본적으로 `TossPaymentClient`를 받는다.

### 2. `@Qualifier`: "이번 주입은 이 후보"

```java
@Service
public class RefundService {
    private final PaymentClient paymentClient;

    public RefundService(
            @Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }
}
```

이 경우 `@Primary`가 있어도 `RefundService`는 `KakaoPaymentClient`를 받는다.

### 3. 컬렉션 주입: "후보를 전부 달라"

```java
@Service
public class PaymentRouter {
    private final List<PaymentClient> paymentClients;
    private final Map<String, PaymentClient> paymentClientMap;

    public PaymentRouter(
            List<PaymentClient> paymentClients,
            Map<String, PaymentClient> paymentClientMap) {
        this.paymentClients = paymentClients;
        this.paymentClientMap = paymentClientMap;
    }
}
```

이 경우에는 둘 다 들어온다.

- `paymentClients`에는 `TossPaymentClient`, `KakaoPaymentClient`가 모두 담긴다
- `paymentClientMap`에는 `tossPaymentClient`, `kakaoPaymentClient` 같은 bean 이름 key로 둘 다 담긴다
- `@Primary`는 "하나만 골라야 할 때"만 의미가 있으므로 collection 주입에서는 후보를 지우지 않는다

---

## 헷갈릴 때 바로 쓰는 판단 기준

| 상황 | 가장 먼저 떠올릴 선택 |
|---|---|
| "대부분은 A를 쓰는데 가끔만 B를 쓴다" | A에 `@Primary`, B가 필요한 곳에 `@Qualifier` |
| "서비스 여러 곳에서 같은 역할을 반복해서 찍는다" | 문자열 `@Qualifier`에서 [커스텀 qualifier](./spring-custom-qualifier-primer.md)로 올릴지 검토 |
| "요청 값이나 enum에 따라 구현체를 바꿔야 한다" | [`Map<String, T>` 같은 registry/route 설계](./spring-runtime-strategy-router-vs-qualifier-boundaries.md) 검토 |
| "`found 2`가 뜨는데 사실 둘 다 필요하다" | 단일 주입을 collection 주입으로 바꿀지 먼저 본다 |

특히 마지막 두 줄이 중요하다.

- `@Primary`와 `@Qualifier`는 **컨테이너가 단일 bean을 고를 때** 쓰는 도구다
- 전략 패턴이나 runtime routing이 필요하면 **collection 주입 후 직접 선택**하는 쪽이 더 맞다

---

## 자주 틀리는 포인트

### 1. `@Primary`를 붙이면 다른 후보가 사라진다고 생각한다

아니다. bean은 그대로 여러 개 등록돼 있다. `@Primary`는 단지 단일 주입 시 기본 우선순위를 줄 뿐이다.

### 2. `@Qualifier`와 컬렉션 주입을 같은 문제로 본다

`@Qualifier`는 "이 하나를 달라"이고, 컬렉션 주입은 "다 모아 달라"다. 질문 자체가 다르다.

### 3. runtime 선택 문제를 `@Qualifier`로 해결하려고 한다

사용자 입력에 따라 PG사를 고르는 문제라면 injection 시점보다 runtime dispatch 문제다. 이때는 `Map<String, PaymentClient>`나 별도 router가 더 자연스럽다. 더 긴 예제는 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)에서 이어서 볼 수 있다.

### 4. 문자열 `@Qualifier`가 반복되는데도 계속 그대로 둔다

`@Qualifier("kakaoPaymentClient")`가 여기저기 반복되면 bean 이름보다 역할 의미가 중요해졌을 수 있다. 이때는 [Spring 커스텀 `@Qualifier` 입문](./spring-custom-qualifier-primer.md)으로 이어서 본다.

---

## 꼬리질문

> Q: `@Primary`와 `@Qualifier`를 한 줄로 나누면?
> 의도: 기본값과 명시 선택을 구분하는지 확인
> 핵심: `@Primary`는 기본 우선순위, `@Qualifier`는 주입 지점의 직접 선택이다.

> Q: `@Primary`가 있어도 `List<PaymentClient>`에는 왜 둘 다 들어가는가?
> 의도: 단일 선택과 다중 수집을 분리하는지 확인
> 핵심: collection 주입은 "하나를 고르는 규칙"이 아니라 "matching bean 전체 수집"이기 때문이다.

> Q: `@Qualifier("beanName")`가 여러 서비스에 반복되면 다음 단계는 무엇인가?
> 의도: 문자열 qualifier에서 의미 계약으로 넘어가는 시점을 확인
> 핵심: 커스텀 qualifier annotation으로 역할을 올리는 것을 검토한다.

> Q: `expected single matching bean but found 2`가 떴을 때 무조건 `@Primary`를 붙여야 하는가?
> 의도: 문제 정의를 다시 확인하는지 점검
> 핵심: 아니다. 한 개만 필요한지, 특정 하나가 필요한지, 여러 개가 필요한지부터 먼저 정한다.

---

## 한 줄 정리

`@Primary`는 기본값 하나, `@Qualifier`는 특정 하나, 컬렉션 주입은 전체 후보 수집이라는 세 감각만 먼저 분리하면 Spring DI 후보 선택에서 크게 덜 헷갈린다.
