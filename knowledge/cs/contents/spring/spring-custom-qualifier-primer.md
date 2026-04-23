# Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기

> 한 줄 요약: `@Qualifier("beanName")`는 "이 bean을 정확히 집어라"라는 문자열 계약이고, 커스텀 qualifier annotation은 "이 역할의 bean을 집어라"라는 의미 계약이다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 bean 이름 문자열 qualifier에서 커스텀 qualifier annotation으로 넘어가는 시점을 잡아 주는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
> - [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
> - [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)
> - [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)

retrieval-anchor-keywords: custom qualifier, custom @Qualifier, qualifier annotation, bean name string qualifier, semantic qualifier, qualifier meta annotation, @Qualifier bean name vs custom annotation, spring qualifier beginner, NoUniqueBeanDefinitionException qualifier, role based bean selection, bean candidate selection, @Primary vs custom qualifier, @Primary vs @Qualifier vs collection injection, qualifier typo runtime, bean rename safe injection, runtime strategy selection, router pattern, Map<String, Bean> router, runtime dispatch vs qualifier

## 이 문서 다음에 보면 좋은 문서

- 후보 선택의 기본 감각이 먼저 필요하면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)를 먼저 본다.
- `@Primary`, 문자열 `@Qualifier`, `List<T>`/`Map<String, T>`를 먼저 빠르게 나누고 싶다면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)를 먼저 본다.
- 문자열 qualifier가 실제 bean 이름 규칙, alias, rename과 어떻게 얽히는지부터 분리하고 싶다면 [Spring Bean 이름 규칙과 rename 함정 입문: `@Component`, `@Bean`, `@Qualifier` 문자열이 어디서 이어지는가](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)를 먼저 본다.
- 호출마다 달라지는 runtime router와 injection-time qualifier 경계를 따로 보고 싶다면 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)로 이어진다.
- BeanDefinition과 후보 해석 규칙을 더 깊게 보려면 [IoC 컨테이너와 DI](./ioc-di-container.md)로 이어진다.
- qualifier가 transaction manager 경계 계약으로 커지는 사례는 [Spring Multiple Transaction Managers and Qualifier Boundaries](./spring-multiple-transaction-managers-qualifier-boundaries.md)에서 본다.

---

## 핵심 개념

초반에는 아래 두 문장을 같이 잡으면 된다.

- `@Qualifier("beanName")`: **bean id를 문자열로 직접 찍는 방식**
- 커스텀 qualifier annotation: **주입 의도를 역할 이름으로 붙이는 방식**

둘 다 "후보가 여러 개일 때 어느 bean을 고를지"를 말하지만, 표현하는 단위가 다르다.

- 문자열 qualifier는 구현체나 bean 이름에 더 가깝다
- 커스텀 qualifier는 역할, 용도, 정책 이름에 더 가깝다

즉, `@Qualifier("kakaoPaymentClient")`는 "카카오용 bean을 달라"보다 "이 이름의 bean을 달라"에 가깝고, 커스텀 annotation은 그 반대다.

---

## 1. bean 이름 문자열 qualifier는 언제까지 괜찮은가

처음에는 아래처럼 써도 충분하다.

```java
@Component("kakaoPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}

@Service
public class RefundService {
    private final PaymentClient paymentClient;

    public RefundService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }
}
```

이 방식이 괜찮은 상황은 단순하다.

- 같은 타입 bean이 둘인데, 한 곳에서만 특정 bean을 집어야 한다
- bean 이름이 이미 충분히 명확하다
- 아직 "역할 이름"보다 "구현체 이름"이 더 자연스럽다

즉, **일회성 disambiguation**이면 문자열 qualifier도 과하지 않다.

---

## 2. 언제 커스텀 qualifier annotation으로 올려야 하는가

문자열 대신 커스텀 qualifier를 고려할 시점은 아래 셋 중 하나가 보일 때다.

### 2-1. 같은 선택 규칙이 여러 주입 지점에 반복된다

`"kakaoPaymentClient"`가 서비스 여러 곳에 반복되면, 이제는 bean 이름보다 **공통 역할**이 중요해진다.

### 2-2. 구현체 이름보다 업무 의미가 더 중요하다

코드가 원하는 것은 "카카오 구현체"가 아니라 "주문 결제용 메인 결제 클라이언트"일 수 있다.

이럴 때 bean 이름 문자열은 인프라 이름이고, 커스텀 qualifier는 도메인 의미가 된다.

### 2-3. rename과 refactor에서 문자열 계약이 자꾸 새어 나온다

bean 이름 문자열은 오타와 rename에 취약하다.

- 클래스명을 바꿨다
- `@Bean` 메서드명을 바꿨다
- component name 전략을 바꿨다

이때 주입 지점의 문자열이 의미 없이 따라 흔들리면, 이미 역할 계약을 annotation으로 분리할 타이밍이다.

---

## 3. 작은 예제로 보기

상황은 이렇다.

- `PaymentClient` 구현체가 둘 있다
- `OrderService`, `RefundService`, `SettlementService`는 모두 "메인 결제 게이트웨이"를 원한다
- 구현체 이름은 바뀔 수 있지만, "메인 결제 게이트웨이"라는 역할은 유지된다

### 문자열 qualifier로 계속 가면

```java
@Service
public class OrderService {
    public OrderService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
    }
}

@Service
public class RefundService {
    public RefundService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
    }
}
```

주입 지점마다 bean 이름이 새어 나온다.

### 커스텀 qualifier로 올리면

먼저 역할 annotation을 만든다.

```java
@Target({ElementType.TYPE, ElementType.FIELD, ElementType.PARAMETER, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
public @interface MainGateway {
}
```

그다음 bean 쪽에 역할을 붙인다.

```java
@Component
@MainGateway
public class KakaoPaymentClient implements PaymentClient {
}

@Component
public class TestPaymentClient implements PaymentClient {
}
```

이제 주입 지점은 bean 이름 대신 역할을 말한다.

```java
@Service
public class RefundService {
    private final PaymentClient paymentClient;

    public RefundService(@MainGateway PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }
}
```

읽는 사람 입장에서는 `kakaoPaymentClient`보다 `@MainGateway`가 더 중요하다.

- 지금 필요한 것이 특정 클래스인가?
- 아니면 메인 결제 게이트웨이라는 역할인가?

커스텀 qualifier는 두 번째 질문에 답한다.

---

## 4. `@Bean` 등록에도 같은 방식으로 붙일 수 있다

component scan bean만 가능한 것은 아니다.

```java
@Configuration
public class PaymentConfig {

    @Bean
    @MainGateway
    public PaymentClient primaryGatewayClient() {
        return new KakaoPaymentClient();
    }

    @Bean
    public PaymentClient sandboxGatewayClient() {
        return new TestPaymentClient();
    }
}
```

즉, 커스텀 qualifier는 "클래스 기반 bean에만 쓰는 annotation"이 아니라, **bean 후보 선택 계약 자체**에 붙는다고 보면 된다.

---

## 5. `@Primary`와 역할 분담은 어떻게 다른가

`@Primary`와 커스텀 qualifier는 경쟁 관계가 아니다.

| 장치 | 의미 | 감각 |
|---|---|---|
| `@Primary` | 특별히 안 찍으면 기본으로 고를 후보 | default |
| `@Qualifier("beanName")` | 정확히 이 bean을 고른다 | named pick |
| 커스텀 qualifier | 이 역할의 bean을 고른다 | semantic pick |

beginner 기준으로는 이렇게 외우면 된다.

- 기본값 하나를 정하고 싶다 -> `@Primary`
- 이번 한 번 정확히 bean 이름을 찍고 싶다 -> 문자열 `@Qualifier`
- 같은 의미를 여러 곳에서 반복해서 말해야 한다 -> 커스텀 qualifier

---

## 6. 언제 굳이 커스텀 qualifier를 만들지 않아도 되는가

모든 중복 bean에 커스텀 annotation을 만드는 것은 오히려 과할 수 있다.

아래처럼 정리하면 된다.

| 상황 | 권장 선택 | 이유 |
|---|---|---|
| 주입 지점이 하나뿐이다 | 문자열 `@Qualifier` 또는 `@Primary` | 계약이 아직 작다 |
| bean 이름 자체가 도메인 용어다 | 문자열 `@Qualifier`도 충분 | 의미 손실이 적다 |
| 같은 역할이 여러 서비스에 반복된다 | 커스텀 qualifier | 의미를 한 곳에 모은다 |
| 요청 값에 따라 런타임에 구현체를 고른다 | qualifier보다 registry/map | injection 시점 문제가 아니다 |

특히 마지막 줄이 중요하다.

`@Qualifier`는 **컨테이너가 주입할 때** 후보를 고르는 장치다.  
요청 파라미터에 따라 매번 다른 구현체를 고르는 문제라면 `Map<String, PaymentClient>`나 별도 router가 더 맞다. 이 경계는 [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](./spring-runtime-strategy-router-vs-qualifier-boundaries.md)에서 예제로 이어진다.

---

## 7. 자주 하는 실수

### 7-1. "문자열이 보기 싫으니 전부 annotation으로 바꾸자"

한두 군데만 쓰는 qualifier까지 전부 커스텀 annotation으로 만들면 타입 수만 늘고 의미는 늘지 않는다.

### 7-2. 구현체 이름을 그대로 annotation 이름으로 옮긴다

`@KakaoPaymentClientQualifier`처럼 만들면 문자열을 annotation으로 감싼 것뿐이다.

역할 이름이 더 낫다.

- `@MainGateway`
- `@SettlementGateway`
- `@WriteDataSource`

### 7-3. runtime 선택 문제를 injection qualifier로 풀려고 한다

사용자 입력에 따라 PG사를 바꾸는 문제는 커스텀 qualifier보다 strategy registry 문제다.

---

## 꼬리질문

> Q: 문자열 `@Qualifier`와 커스텀 qualifier의 가장 큰 차이는 무엇인가?
> 의도: bean id와 역할 계약을 구분하는지 확인
> 핵심: 전자는 이름을 찍고, 후자는 의미를 찍는다.

> Q: 커스텀 qualifier를 만들기 좋은 신호는 무엇인가?
> 의도: 리팩터링 타이밍 감각 확인
> 핵심: 같은 선택 규칙이 여러 주입 지점에 반복될 때다.

> Q: `@Primary`가 있는데도 커스텀 qualifier가 왜 필요한가?
> 의도: default와 explicit contract를 구분하는지 확인
> 핵심: `@Primary`는 기본값이고, 커스텀 qualifier는 의도를 명시한다.

> Q: 요청 값에 따라 구현체를 바꾸는 문제에도 커스텀 qualifier가 답인가?
> 의도: injection 시점과 runtime dispatch를 구분하는지 확인
> 핵심: 아니다. 그때는 registry나 router 쪽이 더 맞다.

---

## 한 줄 정리

bean 이름 문자열이 여러 주입 지점에 반복되기 시작하면, 이제 Spring이 고를 대상을 "이 bean 이름"이 아니라 "이 역할"로 말하도록 커스텀 qualifier annotation으로 올릴 시점이다.
