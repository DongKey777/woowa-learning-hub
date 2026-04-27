# Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택

> 한 줄 요약: `@Qualifier`는 "컨테이너가 이 주입 지점에 어떤 bean을 꽂을지"를 정하는 장치이고, `Map<String, Bean>`/router 패턴은 "애플리케이션 코드가 요청마다 어떤 전략을 실행할지"를 정하는 장치다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 "주입할 때 후보를 고르는 문제"와 "실행 중 전략을 고르는 문제"를 결제/알림 예제로 분리해 주는 **beginner boundary primer**를 담당한다.

**난이도: 🟢 Beginner**

## 먼저 용어를 한국어로 바꿔 읽기

처음 읽을 때 영어 느낌이 강하면 아래처럼 바꿔 잡아도 된다.

| 문서에서 보이는 말 | 처음엔 이렇게 읽어도 된다 | 여기서 뜻하는 것 |
|---|---|---|
| disambiguation | 후보 하나로 좁히기 | 같은 타입 bean이 여러 개일 때 어떤 bean을 쓸지 정함 |
| injection-time | 주입할 때, 앱이 뜰 때 | Spring이 bean을 연결하는 시점 |
| runtime | 실행 중, 요청 처리 중 | 실제 메서드 호출과 요청마다 값이 달라질 수 있는 시점 |

한 줄 감각: **앱이 뜰 때 미리 꽂아 두면 `@Qualifier`, 실행 중에 매번 고르면 router**다.

처음 배우는데 같은 `@Qualifier` 문자열이 서비스마다 반복돼서 "이걸 계속 붙이는 게 맞나?" 싶다면, 이 문서를 읽기 전에 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)를 먼저 보면 큰 그림이 더 빨리 잡힌다. 반복 qualifier는 custom qualifier primer로 보내고, 요청마다 구현체가 바뀌는 경우만 이 문서에서 router 경계로 자르면 된다.

## 먼저 어디로 갈지 고르기

관련 문서:

- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](../design-pattern/bean-name-vs-domain-key-lookup.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)

retrieval-anchor-keywords: spring router vs qualifier, router 언제 쓰는지, qualifier 언제 쓰는지, 처음 배우는데 router qualifier 차이, 요청마다 구현체 선택, enum 분기 구현체 선택, map string bean router, 고정 wiring vs runtime selection, 역할 annotation vs router, 반복 qualifier vs router, external input bean name warning, router key bean name mapping, channel to bean name caution, 외부 입력 bean 이름 매핑 주의, bean name vs domain key

## 먼저 갈림길: 여기서 끝내고 다음 문서로 가야 하는 경우

아래 두 경우는 이 문서를 길게 읽기보다 갈림길만 잡고 바로 옮기는 편이 빠르다.

- 서비스가 항상 같은 구현체를 쓰는데 `@Qualifier("...")` 문자열만 반복된다면 router보다 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)로 먼저 간다.
- 후보 bean 자체가 안 떠서 `NoSuchBeanDefinitionException`이 난다면 router보다 `scan`/조건 등록 문제를 먼저 확인한다.

한 줄 분기: **반복된 고정 선택이면 custom qualifier, 호출마다 달라지는 선택이면 router, 후보 자체가 없으면 등록 경로부터 본다.**

## 이 문서 다음에 보면 좋은 문서

- 단일 후보 기본값, 명시 선택, 전체 수집을 먼저 표로 나누고 싶다면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어진다.
- bean 이름 문자열과 역할 annotation의 경계를 보고 싶다면 [Spring 커스텀 `@Qualifier` 입문: bean 이름 문자열 대신 역할 annotation으로 고르기](./spring-custom-qualifier-primer.md)로 이어진다.
- `Map<String, T>`가 컨테이너에서 어떻게 주입되는지까지 같이 보려면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)를 본다.
- `Map<String, Bean>`의 key를 외부 API 값과 바로 묶어도 되는지 헷갈리면 [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](../design-pattern/bean-name-vs-domain-key-lookup.md)로 이어진다.

---

<a id="runtime-router-path"></a>

## 초보자 질문을 먼저 번역하기

처음 배우는데 아래처럼 묻고 있다면, 질문을 먼저 `고정 wiring`과 `요청마다 분기`로 번역하면 된다.

| 초보자 질문 | 먼저 번역할 문장 | 더 가까운 선택 |
|---|---|---|
| `요청마다 구현체를 바꿔야 하나요?` | 호출마다 선택이 달라진다 | router |
| `enum 값에 따라 구현체를 고르면 되나요?` | enum 분기 기반 runtime 선택이다 | router |
| `이 서비스는 항상 같은 구현체만 쓰는데요?` | 앱이 뜰 때 한 번 고정하면 된다 | `@Qualifier` |
| `역할 annotation으로 고정해 두고 싶어요` | 매 호출 분기가 아니라 역할별 고정 wiring이다 | custom qualifier 검토 |
| `qualifier가 반복되는데 다 router로 바꿔야 하나요?` | 반복된 고정 선택인지 먼저 본다 | custom qualifier 검토 |

## 먼저 큰 그림

처음 배우는데 `Map<String, Bean>`과 `@Qualifier`가 둘 다 "여러 구현체 중 하나를 고른다"처럼 보여서 헷갈리면, 어려운 용어보다 "언제 고르느냐"를 먼저 자르면 된다.

- 애플리케이션이 뜰 때 한 번 고정할 선택이면 `@Qualifier`
- 요청 값이나 enum에 따라 매번 달라질 선택이면 router
- `Map<String, Bean>`은 후보를 모아 두는 출발점이지, 그 자체가 `@Qualifier`의 대체품은 아니다

한 줄로 줄이면 **고정 wiring은 qualifier, 호출마다 달라지는 분기는 router**다.

> 주의: `channel`, `pgCode` 같은 외부 입력값을 bean 이름에 바로 붙이지 말자. 초급자 실수로 `paymentClients.get(channel)`를 곧바로 `emailSender`, `kakaoPaymentClient` 같은 bean 이름 계약에 묶으면, API 값 변경이 wiring 이름 변경으로 번진다. 먼저 외부 값을 enum이나 별도 domain key로 정규화하고, 그 다음 router 내부에서 전략을 찾는 편이 안전하다. 더 길게 보면 [Bean Name vs Domain Key Lookup](../design-pattern/bean-name-vs-domain-key-lookup.md)로 이어진다.

---

## 핵심 구분

헷갈릴 때는 아래 세 질문만 먼저 나누면 된다.

| 질문 | `@Qualifier` | `Map<String, Bean>` / router |
|---|---|---|
| 누가 고르나 | Spring 컨테이너 | 애플리케이션 코드 |
| 언제 고르나 | bean 주입 시점 | 메서드 호출마다, 요청마다 |
| 무엇을 기준으로 고르나 | wiring 의도, 역할, 고정된 선택 규칙 | 사용자 입력, enum, 파트너사, 채널 같은 실행 중 값 |

즉, 둘 다 "여러 구현체 중 하나를 쓴다"는 점은 비슷하지만, **선택 주체와 선택 시점이 다르다**.

- `@Qualifier`는 "이 서비스는 처음부터 이 구현체를 써야 한다"에 가깝다.
- router는 "이번 호출에서는 이 구현체를 써야 한다"에 가깝다.

---

## 결제 예제: `@Qualifier`

결제 클라이언트가 두 개 있다고 가정한다.

```java
public interface PaymentClient {
    void pay(PaymentCommand command);
}

@Component("tossPaymentClient")
public class TossPaymentClient implements PaymentClient {
}

@Component("kakaoPaymentClient")
public class KakaoPaymentClient implements PaymentClient {
}
```

```java
@Service
public class SettlementService {
    private final PaymentClient paymentClient;

    public SettlementService(
            @Qualifier("kakaoPaymentClient") PaymentClient paymentClient) {
        this.paymentClient = paymentClient;
    }

    public void settle(PaymentCommand command) {
        paymentClient.pay(command);
    }
}
```

여기서 중요한 점은 `SettlementService`가 실행될 때마다 컨테이너가 다시 고르지 않는다는 것이다.

- 애플리케이션 시작 시점에 `SettlementService`는 `kakaoPaymentClient`로 wiring된다
- 이후 요청이 100번 와도 같은 `PaymentClient`를 쓴다
- 즉, 이 문제는 "이번 서비스는 어떤 bean을 써야 하는가"라는 **구성 문제**다

## 결제 예제: router

```java
@Service
public class PaymentRouter {
    private final Map<String, PaymentClient> paymentClients;

    public PaymentRouter(Map<String, PaymentClient> paymentClients) {
        this.paymentClients = paymentClients;
    }

    public void pay(String pgCode, PaymentCommand command) {
        PaymentClient paymentClient = paymentClients.get(pgCode);
        if (paymentClient == null) {
            throw new IllegalArgumentException("Unknown pgCode: " + pgCode);
        }
        paymentClient.pay(command);
    }
}
```

여기서 컨테이너는 `PaymentRouter`에 후보를 **전부 주입**할 뿐이다.

- `paymentClients`에는 `tossPaymentClient`, `kakaoPaymentClient`가 모두 들어간다
- 실제 선택은 `pay()`가 호출될 때 `pgCode`로 결정된다
- 즉, 이 문제는 "이번 결제 요청은 어느 PG로 보낼까"라는 **실행 중 분기 문제(runtime dispatch)** 다.

초보자 기준으로는 아래처럼 외우면 된다.

- `SettlementService(@Qualifier(...))` -> 서비스 wiring을 고정
- `PaymentRouter(Map<String, PaymentClient>)` -> 요청마다 전략을 선택

---

## 알림 예제로 한 번 더 보기

알림 채널도 같은 방식으로 갈린다.

```java
public interface NotificationSender {
    void send(NotificationMessage message);
}

@Component("emailSender")
public class EmailNotificationSender implements NotificationSender {
}

@Component("smsSender")
public class SmsNotificationSender implements NotificationSender {
}
```

### 특정 용도의 서비스가 항상 같은 채널을 쓴다면 qualifier가 맞다

```java
@Service
public class ReceiptSender {
    private final NotificationSender notificationSender;

    public ReceiptSender(
            @Qualifier("emailSender") NotificationSender notificationSender) {
        this.notificationSender = notificationSender;
    }

    public void sendReceipt(NotificationMessage message) {
        notificationSender.send(message);
    }
}
```

영수증은 항상 이메일로 보낸다는 정책이라면, 이건 runtime 선택이 아니라 고정 wiring이다.

### 사용자 선호 채널에 따라 달라지면 router가 맞다

```java
@Service
public class NotificationRouter {
    private final Map<String, NotificationSender> senders;

    public NotificationRouter(Map<String, NotificationSender> senders) {
        this.senders = senders;
    }

    public void send(String channel, NotificationMessage message) {
        NotificationSender sender = senders.get(channel);
        if (sender == null) {
            throw new IllegalArgumentException("Unknown channel: " + channel);
        }
        sender.send(message);
    }
}
```

사용자 설정이 `email`일 수도 있고 `sms`일 수도 있다면, 이건 `@Qualifier`로 못 푼다.

## 알림 예제로 한 번 더 보기 (계속 2)

- `@Qualifier`는 파라미터에 박아 두는 값이다
- 사용자별 채널 선호는 요청마다 바뀔 수 있다
- 따라서 router나 strategy registry 쪽이 자연스럽다

---

## 자주 섞이는 오해

### 1. `Map<String, Bean>`도 결국 bean 하나를 고르는 것이니 qualifier와 같다고 생각한다

같지 않다.

- `@Qualifier`는 컨테이너의 후보 해석 규칙이다
- router는 이미 주입된 후보들 중에서 애플리케이션이 직접 dispatch하는 규칙이다

### 2. runtime 선택 문제인데 `@Qualifier`를 늘려서 해결하려고 한다

예를 들어 `@Qualifier("kakaoPaymentClient")`, `@Qualifier("tossPaymentClient")`를 여러 서비스에 퍼뜨리면 "고정 wiring"만 늘어난다.

사용자 입력이나 enum에 따라 바뀌는 선택은 router로 올려야 한다.

### 3. router의 key로 외부 입력을 bean 이름에 바로 묶는다

`Map<String, Bean>`의 key는 기본적으로 bean 이름이다.

이때 `"email"` 같은 외부 API 값을 바로 `"emailSender"` bean 이름에 결합해 버리면, wiring 이름이 외부 계약으로 새어 나간다.

beginner 기준으로는 아래가 더 안전하다.

- 외부 입력은 `NotificationChannel.EMAIL` 같은 enum으로 먼저 정규화한다
- router 내부에서 bean 이름 또는 별도 registry key로 매핑한다

즉, `Map<String, Bean>`를 쓰더라도 **bean 이름을 곧바로 API 계약으로 만들지는 않는 편이 낫다**.

### 4. qualifier가 반복된다고 바로 router로 가려고 한다

qualifier 반복은 대개 "같은 역할을 여러 곳에서 고정 선택한다"는 신호다.

이때는 먼저 [커스텀 `@Qualifier`](./spring-custom-qualifier-primer.md)를 검토한다.
router는 "반복된 고정 선택"이 아니라 "호출마다 달라지는 선택"일 때 맞다.

---

## 빠른 선택 기준

| 상황 | 더 맞는 선택 | 이유 |
|---|---|---|
| 정산 서비스는 항상 카카오 PG만 써야 한다 | `@Qualifier` | wiring이 고정돼 있다 |
| 주문마다 PG사를 다르게 골라야 한다 | router | 요청 값마다 달라진다 |
| 영수증은 항상 이메일로 보낸다 | `@Qualifier` | 채널 정책이 고정이다 |
| 사용자 선호 채널에 따라 이메일/SMS를 바꾼다 | router | 실행 시점 입력이 필요하다 |
| 외부 `channel` 값을 bean 이름과 바로 연결하고 싶다 | router + domain key 정규화 | bean 이름은 컨테이너 key이고 API 계약은 따로 두는 편이 안전하다 |
| 같은 qualifier가 여러 서비스에 반복된다 | 커스텀 qualifier 검토 | runtime 선택이 아니라 의미 계약일 수 있다 |

---

## 꼬리질문

> Q: `@Qualifier`와 router의 가장 큰 차이는 무엇인가?
> 의도: 선택 주체와 시점을 구분하는지 확인
> 핵심: `@Qualifier`는 컨테이너가 주입 시점에 고르고, router는 애플리케이션이 실행 시점에 고른다.

> Q: `Map<String, PaymentClient>`를 주입받으면 Spring이 요청마다 다시 bean을 고르는가?
> 의도: collection 주입과 runtime dispatch를 구분하는지 확인
> 핵심: 아니다. Spring은 후보 전체를 한 번 주입하고, 이후 선택은 router 코드가 한다.

> Q: 결제 수단이 주문마다 달라질 수 있는데 `@Qualifier("kakaoPaymentClient")`로 해결해도 되는가?
> 의도: 고정 wiring과 per-request 선택을 구분하는지 확인
> 핵심: 아니다. 그건 runtime 전략 선택이므로 router가 더 맞다.

> Q: qualifier가 여러 서비스에 반복되면 바로 router로 가야 하는가?
> 의도: 반복된 고정 선택과 runtime 선택을 구분하는지 확인
> 핵심: 아니다. 먼저 커스텀 qualifier로 역할 계약을 올릴지 본다.

---

## 한 줄 정리

`@Qualifier`는 "이 서비스에 어떤 bean을 꽂을까"를 정하고, `Map<String, Bean>`/router는 "이번 호출에 어떤 전략을 실행할까"를 정한다.
