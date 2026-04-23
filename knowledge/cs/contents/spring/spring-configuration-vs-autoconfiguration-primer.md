# Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`

> 한 줄 요약: `@Configuration`은 "내가 직접 적는 빈 조립 설명서"이고, Boot auto-configuration은 "조건이 맞을 때 Boot가 대신 가져오는 기본 설명서"다. `proxyBeanMethods`는 그 설명서 안의 `@Bean` 메서드 직접 호출을 안전하게 보정할지 정하는 스위치다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@Configuration`, `@Bean`, Boot auto-configuration, `proxyBeanMethods`를 한 번에 연결하는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)

retrieval-anchor-keywords: configuration vs autoconfiguration, @Configuration vs auto-configuration, @Configuration @Bean difference, spring configuration beginner, boot auto configuration beginner, proxyBeanMethods beginner, full configuration vs lite configuration, method parameter injection bean, inter-bean reference, @Bean method call singleton, @ConditionalOnMissingBean mental model, user configuration wins, boot default bean registration, @AutoConfiguration primer, condition evaluation report beginner, --debug first checklist, actuator conditions endpoint, boot bean missing first debug

## 이 문서 다음에 보면 좋은 문서

- Boot 조건부 등록을 더 자세히 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.
- 내 설정이 있을 때 Boot 기본값이 왜 빠지는지 처음 디버깅하려면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 이어진다.
- full configuration, lite configuration, method-parameter injection을 예제로 바로 비교하려면 [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)으로 이어진다.
- `proxyBeanMethods`와 post-processor 체인을 더 깊게 보려면 [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)으로 이어진다.
- BeanDefinition과 컨테이너 생명주기 자체를 더 보려면 [IoC 컨테이너와 DI](./ioc-di-container.md)를 같이 본다.

---

## 핵심 개념

초반에는 이 네 줄만 잡으면 된다.

- `@Bean`: "이 객체는 이렇게 만들어라"라고 적는 팩토리 메서드
- `@Configuration`: 여러 `@Bean` 메서드를 묶어 둔 설정 클래스
- auto-configuration: Boot가 조건이 맞을 때 추가로 가져오는 설정 클래스
- `proxyBeanMethods`: 설정 클래스 안에서 다른 `@Bean` 메서드를 직접 부를 때 singleton 의미를 지켜 줄지 정하는 옵션

핵심은 **메커니즘은 비슷하고, 소유자와 활성화 조건이 다르다**는 점이다.

- 내 코드의 `@Configuration`은 내가 직접 켠다
- Boot auto-configuration은 Boot가 조건을 보고 켠다
- 둘 다 결국 컨테이너에 `BeanDefinition`을 등록한다

즉, auto-configuration은 Spring과 다른 별도 마법이 아니라, **Boot가 제공하는 조건부 `@Configuration` 묶음**이다.

---

## 큰 그림 한 번에 보기

```text
내 애플리케이션 시작
-> 내가 만든 @Configuration / @Bean 등록
-> Boot가 auto-configuration 후보를 읽음
-> 클래스패스/프로퍼티/기존 Bean 유무로 조건 검사
-> 비어 있는 자리에 기본 Bean 채움
-> 컨테이너가 실제 Bean 생성
-> 필요하면 프록시 적용
```

이 흐름을 beginner 관점으로 줄이면 이렇게 기억하면 된다.

**내 설정이 먼저 의도를 말하고, Boot가 남은 빈칸을 채운다.**

---

## 1. `@Bean`과 `@Configuration`은 무엇이 다른가

`@Bean`은 개별 객체 생성 규칙이고, `@Configuration`은 그 규칙들을 담는 클래스다.

```java
@Configuration
public class AppConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }

    @Bean
    public OrderService orderService(OrderRepository orderRepository, Clock systemClock) {
        return new OrderService(orderRepository, systemClock);
    }
}
```

이 코드를 beginner 감각으로 읽으면 된다.

- `AppConfig`는 "조립 설명서"
- `systemClock()`과 `orderService()`는 "부품 만드는 함수"
- Spring은 이 메서드 정보를 읽어 Bean으로 등록한다

여기서 중요한 점은 `@Configuration` 자체가 Bean을 직접 쓰는 곳이 아니라, **Bean을 어떻게 만들지 선언하는 곳**이라는 점이다.

---

## 2. auto-configuration은 무엇이 다른가

auto-configuration도 결국 설정 클래스다. 차이는 "누가 쓰고, 언제 활성화하느냐"다.

| 항목 | 일반 `@Configuration` | Boot auto-configuration |
|---|---|---|
| 작성자 | 애플리케이션 개발자 | Boot / starter 작성자 |
| 활성화 방식 | 내가 직접 클래스에 둠 | Boot가 조건을 보고 import |
| 기본 목적 | 우리 앱 의도를 명시 | 빠진 기본값 채우기 |
| 대표 조건 | 보통 항상 적용 | 클래스패스, 프로퍼티, Bean 유무 |

간단한 mental model은 이렇다.

- 일반 `@Configuration`: "나는 이 Bean이 꼭 필요해"
- auto-configuration: "아직 없으면 내가 기본값을 넣어 줄게"

그래서 둘은 경쟁 관계라기보다 **explicit config + default config** 관계다.

### 왜 사용자 설정이 Boot 기본값보다 먼저 느껴지는가

Boot auto-configuration은 흔히 이런 조건을 건다.

```java
@Bean
@ConditionalOnMissingBean
public ObjectMapper objectMapper() {
    return new ObjectMapper();
}
```

뜻은 단순하다.

- 같은 타입 Bean을 사용자가 이미 등록했으면 Boot 기본값은 물러난다
- 사용자가 안 만들었으면 Boot가 기본값을 채운다

즉, 초반에 외워 둘 규칙은 하나다.

**내가 직접 등록한 Bean은 의도이고, Boot Bean은 결손 보충이다.**

---

## 3. `proxyBeanMethods`는 왜 갑자기 등장하는가

`@Configuration`을 배우다가 `proxyBeanMethods`를 보면 맥락이 끊기기 쉽다.  
이 옵션은 auto-configuration 자체보다, **설정 클래스 내부의 `@Bean` 메서드 호출 방식**을 다룬다.

예를 들어:

```java
@Configuration
public class AppConfig {

    @Bean
    public Client client() {
        return new Client();
    }

    @Bean
    public ClientService clientService() {
        return new ClientService(client());
    }
}
```

여기서 `clientService()` 안의 `client()`는 겉보기에는 평범한 자바 메서드 호출이다.  
그런데 Spring은 singleton Bean 의미를 지키기 위해 이 호출을 특별하게 다룰 수 있다.

### `proxyBeanMethods = true`

```java
@Configuration(proxyBeanMethods = true)
```

- 설정 클래스를 프록시로 감싼다
- `clientService()` 안에서 `client()`를 직접 불러도
- 그냥 새 객체를 만드는 대신, 컨테이너에 등록된 같은 Bean을 돌려주게 보정한다

초보자용 한 줄 감각:

**설정 클래스 안의 `@Bean` 메서드 직접 호출을 컨테이너 조회처럼 바꿔 주는 안전장치**

### `proxyBeanMethods = false`

```java
@Configuration(proxyBeanMethods = false)
```

- 설정 클래스를 그런 방식으로 프록시하지 않는다
- `client()`를 직접 부르면 그냥 자바 메서드 호출처럼 실행된다
- 따라서 여러 인스턴스를 실수로 만들 수 있다

초보자용 규칙은 간단하다.

- 다른 `@Bean` 메서드를 직접 부르는 설정이면 `true` 쪽이 안전하다
- Boot 스타일처럼 메서드 파라미터 주입으로 연결하면 `false`도 안전하다

---

## 4. 왜 Boot auto-configuration은 `proxyBeanMethods = false`를 자주 쓰는가

Boot의 auto-configuration은 대개 설정 클래스를 "가벼운 팩토리 모음"처럼 설계한다.

```java
@AutoConfiguration
public class MyFeatureAutoConfiguration {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }

    @Bean
    public AuditService auditService(Clock systemClock) {
        return new AuditService(systemClock);
    }
}
```

이 패턴에서는 `auditService()`가 `systemClock()`를 직접 부르지 않고, 파라미터로 받는다.

- 내부 self-call이 없다
- singleton 보정을 위한 프록시 필요성이 낮다
- 그래서 `proxyBeanMethods = false`로 가볍게 가져가도 된다

즉, Boot가 `false`를 자주 쓴다는 사실은 "프록시가 필요 없다"기보다,
**설정 클래스를 self-call 없이 쓰도록 설계했다**는 뜻에 가깝다.

---

## 5. beginner가 가장 헷갈리는 지점 세 가지

### 1. "`@Configuration`이 있으면 auto-configuration은 안 쓰는 건가?"

아니다. 둘은 함께 동작한다.

- 내 `@Configuration`은 내 의도를 등록한다
- Boot auto-configuration은 남은 기본값을 조건부로 채운다

실제 애플리케이션은 둘이 섞여 돌아가는 경우가 대부분이다.

### 2. "내가 `@Bean`으로 등록했는데 Boot Bean도 같이 생기나?"

경우에 따라 다르지만, 많은 Boot 기본 설정은 `@ConditionalOnMissingBean`을 써서 중복을 피한다.  
그래서 보통은 **내 Bean이 있으면 Boot 기본값이 빠진다**고 이해하면 출발점으로 충분하다.

### 3. "`proxyBeanMethods = false`면 무조건 위험한가?"

아니다. 아래처럼 쓰면 안전하다.

```java
@Configuration(proxyBeanMethods = false)
public class AppConfig {

    @Bean
    public Client client() {
        return new Client();
    }

    @Bean
    public ClientService clientService(Client client) {
        return new ClientService(client);
    }
}
```

위 코드는 `Client`를 메서드 파라미터로 주입받으므로 self-call이 없다.  
반대로 `clientService()` 안에서 `client()`를 직접 부르면 그때는 의미가 달라진다.

---

## 6. 실전에서 이렇게 기억하면 덜 헷갈린다

### mental model: 설명서 두 장 + 안전 스위치

- `@Configuration`: 내가 적는 설명서
- auto-configuration: Boot가 들고 오는 기본 설명서
- `@Bean`: 설명서 안의 부품 생성 규칙
- `proxyBeanMethods`: 설명서 안에서 다른 부품 규칙을 직접 부를 때 켜는 안전 스위치

이렇게 놓으면 아래도 자연스럽게 연결된다.

- starter를 추가하면 기본 설명서가 늘어난다
- 같은 Bean을 내가 만들면 Boot 기본 설명서는 양보한다
- 설정 클래스 내부 self-call이 있으면 `proxyBeanMethods`가 중요해진다

---

## 코드로 비교하기

### 패턴 1. beginner에게 가장 안전한 구성

```java
@Configuration
public class AppConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }

    @Bean
    public AuditService auditService(Clock systemClock) {
        return new AuditService(systemClock);
    }
}
```

- `@Bean` 간 직접 호출이 없다
- 의존성이 메서드 시그니처에 드러난다
- 이후 `proxyBeanMethods = false`로 바꾸기 쉬운 구조다

### 패턴 2. self-call에 기대는 구성

```java
@Configuration
public class AppConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }

    @Bean
    public AuditService auditService() {
        return new AuditService(systemClock());
    }
}
```

- 겉보기엔 짧다
- 하지만 `systemClock()` 호출 의미가 단순 자바 호출인지, 컨테이너 singleton 조회인지 헷갈리기 쉽다
- 이런 구조에서는 `proxyBeanMethods` 의미를 알고 있어야 한다

---

## 트레이드오프

| 선택 | 장점 | 주의점 | beginner 기준 |
|---|---|---|---|
| 일반 `@Configuration` | 의도를 명시하기 쉽다 | 빈이 많아지면 구조가 커진다 | 직접 등록이 필요할 때 사용 |
| Boot auto-configuration | 반복 설정을 줄여 준다 | 조건을 모르면 "왜 안 생기지?"가 된다 | 기본값 제공 장치로 이해 |
| `proxyBeanMethods = true` | self-call이 있어도 안전하다 | 프록시 비용과 숨은 동작이 있다 | self-call이 있으면 안전한 기본값 |
| `proxyBeanMethods = false` | 더 단순하고 가볍다 | 직접 메서드 호출 실수를 막지 못한다 | 파라미터 주입 패턴일 때 사용 |

beginner에게 가장 실용적인 기준은 이것이다.

- **`@Bean`끼리는 메서드 파라미터로 연결한다**
- 그러면 `proxyBeanMethods`를 나중에 보더라도 덜 헷갈린다

---

## 꼬리질문

> Q: `@Configuration`과 auto-configuration의 가장 큰 차이는 무엇인가?
> 의도: 메커니즘과 소유자 차이 구분
> 핵심: 둘 다 설정 클래스지만, auto-configuration은 Boot가 조건부로 가져오는 기본 설정이다.

> Q: `@Bean`은 무엇을 하는가?
> 의도: 설정 클래스와 개별 팩토리 메서드 구분
> 핵심: 컨테이너에 등록할 객체 생성 규칙을 선언한다.

> Q: `proxyBeanMethods`는 무엇을 지키려는 옵션인가?
> 의도: self-call과 singleton 의미 연결
> 핵심: 설정 클래스 안의 `@Bean` 메서드 직접 호출이 같은 컨테이너 Bean을 가리키게 보정할지 정한다.

> Q: Boot auto-configuration이 `proxyBeanMethods = false`를 자주 쓰는 이유는 무엇인가?
> 의도: Boot 스타일 이해 확인
> 핵심: 내부 self-call 없이 메서드 파라미터 주입으로 설계해 프록시 필요성을 낮추기 때문이다.

## 한 줄 정리

`@Configuration`과 auto-configuration은 같은 컨테이너 메커니즘 위에서 움직인다. 차이는 누가 설정을 쓰고 어떤 조건에서 켜지느냐이며, `proxyBeanMethods`는 그 설정 클래스 내부 호출을 어떻게 다룰지 정하는 로컬 규칙이다.
