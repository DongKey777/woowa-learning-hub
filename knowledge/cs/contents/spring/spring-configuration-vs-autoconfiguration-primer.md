# Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`

> 한 줄 요약: 초급자 기준으로는 "`service`/`repository` 같은 우리 코드면 component scan, 외부 객체 조립이면 `@Bean`, Boot가 대신 채우는 기본값이면 auto-configuration"으로 먼저 자르면 된다. `@Configuration`은 그 `@Bean` 규칙을 담는 설명서이고, `proxyBeanMethods`는 이 설명서 안에서 `@Bean` 메서드를 직접 부를 때만 신경 쓰면 되는 안전 스위치다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Bean 등록 기초에서 Boot 설정 문서로 넘어갈 때 "`언제 scan / `@Bean` / auto-configuration을 고르나`"를 먼저 연결해 주는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)
- [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
- [Spring Legacy Self-invocation(내부 호출) 탐지 카드: `@Configuration`의 위험한 `@Bean` 직접 호출 빠른 점검](./spring-legacy-configuration-bean-self-call-detection-card.md)
- [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: configuration vs autoconfiguration, @configuration @bean difference, component scan vs bean registration, spring configuration beginner, boot auto configuration beginner, 언제 @bean 써요, 언제 configuration 써요, configuration 뭐예요, auto configuration 뭐예요, 처음 spring 설정 헷갈, proxybeanmethods beginner, self-invocation internal call, self invocation vs parameter injection, @conditionalonmissingbean mental model, boot default bean registration

## 이 문서 다음에 보면 좋은 문서

- Bean 등록 자체가 아직 흐리다면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)로 한 칸 돌아가서 "`우리 코드 scan / 외부 객체 `@Bean` / Boot 기본값 auto-configuration`" 3갈래를 먼저 다시 붙인다.
- starter를 넣으면 왜 기본 Bean이 바로 생기는지부터 짧게 보고 싶다면 [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)로 먼저 간다.
- Boot 조건부 등록을 더 자세히 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.
- 내 설정이 있을 때 Boot 기본값이 왜 빠지는지 처음 디버깅하려면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 이어진다.
- "`@Primary`와 `@ConditionalOnMissingBean`이 같은 문제인가?"를 짧은 표로 먼저 분리하고 싶다면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이어진다.
- full configuration, lite configuration, method-parameter injection을 예제로 바로 비교하려면 [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)으로 이어진다.
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

## 30초 선택 사다리

이 문서를 찾는 초급자는 보통 "`@Configuration`이랑 `@Bean`이 뭐가 다르고, Boot는 또 언제 끼어들지?"에서 멈춘다.
그때는 어노테이션 이름보다 아래 질문 순서로 자르는 편이 훨씬 덜 헷갈린다.

| 순서 | 먼저 물을 질문 | 바로 고를 첫 선택 |
|---|---|---|
| 1 | 이 객체가 `OrderService`, `OrderRepository`처럼 우리 애플리케이션 역할 클래스인가? | component scan |
| 2 | 이 객체가 `Clock`, `ObjectMapper`, 외부 SDK client처럼 내가 조립 규칙을 적어야 하는가? | `@Configuration` + `@Bean` |
| 3 | 이 객체가 starter가 보통 대신 채워 주는 공용 기본값인가? | Boot auto-configuration을 먼저 믿고, 필요하면 customizer나 사용자 Bean으로 개입 |

헷갈릴 때는 아래처럼 짧게 읽으면 된다.

- `@Bean`은 "객체 하나를 이렇게 만들겠다"는 등록 규칙이다.
- `@Configuration`은 그 `@Bean` 규칙을 묶어 두는 설명서다.
- auto-configuration은 Boot가 들고 오는 기본 설명서다.

즉 비교 축은 "`@Configuration` vs `@Bean`"이 아니라, **"`@Bean`은 규칙 하나, `@Configuration`은 그 규칙 묶음, auto-configuration은 Boot가 가져오는 기본 묶음`"**에 가깝다.

---

## 1. 처음엔 "`어떤 등록 방식을 고르나`"부터 자른다

`@Configuration`, `@Bean`, auto-configuration을 어노테이션 이름으로 외우기 시작하면 금방 섞인다.
초급자에게는 "**이 객체를 누가 소유하고, 누가 만들고, 기본값인지 명시 설정인지**"를 먼저 묻는 편이 더 안전하다.

| 지금 만들려는 것 | 먼저 떠올릴 방식 | 왜 그 선택이 자연스러운가 |
|---|---|---|
| `OrderService`, `OrderRepository`, `OrderController` 같은 우리 레이어 객체 | component scan | 역할이 클래스에 이미 드러나고, Spring이 찾아 올리는 편이 가장 단순하다 |
| `Clock`, `ObjectMapper`, 외부 SDK client 같은 라이브러리 객체 | `@Configuration` + `@Bean` | 내 소유 타입이 아니라 stereotype을 붙일 수 없고, 조립 규칙을 내가 직접 적어야 한다 |
| starter가 채워 주는 기본 `ObjectMapper`, `DataSource`, `WebClient.Builder` 같은 공용 기본값 | Boot auto-configuration | 앱이 안 적은 빈칸을 조건부 기본값으로 채우는 역할이라 Boot 계약을 먼저 탄다 |

한 줄로 줄이면 이렇다.

- 우리 코드 역할 객체면 scan
- 외부 객체 조립이면 `@Bean`
- Boot 기본값이면 auto-configuration

여기서 `@Configuration`이 안 보이는 이유는 `@Configuration`이 경쟁 후보가 아니라,
**`@Bean`을 어디에 모아 둘지 정하는 껍데기**이기 때문이다.
초반 오해는 대부분 "`@Configuration`도 bean 등록 방식 하나인가?"에서 시작하는데,
실제로는 "`@Bean`을 어떤 설명서에 담았나`"로 읽는 쪽이 더 정확하다.

이 문서는 여기서 한 칸 더 가서, 왜 `@Configuration`과 auto-configuration이 사실 같은 메커니즘 위에 있는지도 붙여 준다.

---

## 2. `@Bean`과 `@Configuration`은 무엇이 다른가

`@Bean`은 개별 객체 생성 규칙이고, `@Configuration`은 그 규칙들을 담는 클래스다.

초보자에게는 아래 한 줄로 먼저 잡는 편이 좋다.

- `@Bean` = "이 객체 하나는 이렇게 만든다"
- `@Configuration` = "그 규칙들을 한 파일에 모아 둔다"

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

그래서 "`@Configuration`을 붙였는데 왜 Bean이 안 생기죠?"보다
"그 안에 실제 `@Bean` 메서드가 있는가, 또는 component scan 대상이 맞는가?"를 먼저 보는 편이 정확하다.

여기서 중요한 점은 `@Configuration` 자체가 Bean을 직접 쓰는 곳이 아니라, **Bean을 어떻게 만들지 선언하는 곳**이라는 점이다.

---

## 3. auto-configuration은 무엇이 다른가

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

## 4. `proxyBeanMethods`는 왜 갑자기 등장하는가

`@Configuration`을 배우다가 `proxyBeanMethods`를 보면 맥락이 끊기기 쉽다.
이 옵션은 auto-configuration 자체보다, **설정 클래스 내부의 `@Bean` 메서드 호출 방식**을 다룬다.
이 문서에서는 `self-invocation(내부 호출)`과 "`@Bean` 메서드 직접 호출"을 같은 뜻으로 쓴다.

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

**설정 클래스 안의 `@Bean` self-invocation(내부 호출)을 컨테이너 조회처럼 바꿔 주는 안전장치**

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

## 5. `proxyBeanMethods`를 읽을 때 먼저 보는 표

먼저 이 한 문장만 확인한다.
**"이 설정 클래스에서 `@Bean` 메서드끼리 self-invocation(내부 호출)하고 있는가?"**

| 지금 코드 모습 | 빠른 선택 | 바로 확인할 대응 예제 |
|---|---|---|
| `@Bean` 메서드 안에서 다른 `@Bean` 메서드를 직접 부른다 | 우선 `proxyBeanMethods = true`로 안전하게 유지하고, 이후 파라미터 주입으로 리팩터링 | [full configuration: self-invocation(내부 호출)이 있어도 같은 Bean을 쓴다](./spring-full-vs-lite-configuration-examples.md#full-config-self-invocation) |
| self-invocation(내부 호출)을 유지한 채 `proxyBeanMethods = false`를 쓰고 있다 | 위험 신호다. 같은 패턴이 있는지 먼저 찾고 중단점으로 본다 | [lite configuration + self-invocation(내부 호출): 보기엔 같아도 다른 객체가 들어간다](./spring-full-vs-lite-configuration-examples.md#lite-self-invocation-trap) |
| `@Bean` 의존성을 메서드 파라미터로 받는다 | `proxyBeanMethods = false`를 기본 선택으로 써도 안전하다 | [lite configuration + method-parameter injection: proxy 없이도 안전하다](./spring-full-vs-lite-configuration-examples.md#lite-parameter-safe) |

### self-invocation(내부 호출) 오해 비교표

탐지 카드에서 이 문서로 넘어오는 독자는 보통 "둘 다 `client()`를 쓰는데 뭐가 다르지?"에서 멈춘다.
아래 표는 **호출 모양보다 호출 경로**가 핵심이라는 점만 빠르게 잡아 준다.

## 5. `proxyBeanMethods`를 읽을 때 먼저 보는 표 (계속 2)

| 비교 포인트 | self-invocation(내부 호출) + `proxyBeanMethods = true` | self-invocation(내부 호출) + `proxyBeanMethods = false` | 파라미터 주입 + `proxyBeanMethods = false` |
|---|---|---|---|
| `clientService()` 안에서 무엇을 하나 | `client()`를 직접 호출 | `client()`를 직접 호출 | `Client client`를 파라미터로 받음 |
| 실제로 가져오는 대상 | 컨테이너 Bean으로 보정된 같은 인스턴스 | 그냥 메서드가 만든 새 객체일 수 있음 | 컨테이너가 넣어 준 같은 Bean |
| beginner가 읽을 때 해석 | "직접 호출처럼 보여도 Spring이 중간에서 잡아준다" | "보이는 그대로 자바 호출이라 헷갈리면 위험하다" | "의존성을 시그니처로 받으니 가장 덜 헷갈린다" |
| 초급 추천도 | 레거시 유지 시 허용 | 피해야 할 혼동 구간 | 기본 추천 패턴 |

## 6. 여기서 자주 생기는 오해 두 가지

- `false`는 "무조건 성능 최적화 정답"이 아니라, self-invocation(내부 호출)이 없다는 전제가 있어야 안전하다.
- `true`는 "구식 옵션"이 아니라, self-invocation(내부 호출) 기반 코드를 보호하는 안전 모드다.

---

## 7. 왜 Boot auto-configuration은 `proxyBeanMethods = false`를 자주 쓰는가

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

- 내부 self-invocation(내부 호출)이 없다
- singleton 보정을 위한 프록시 필요성이 낮다
- 그래서 `proxyBeanMethods = false`로 가볍게 가져가도 된다

즉, Boot가 `false`를 자주 쓴다는 사실은 "프록시가 필요 없다"기보다,
**설정 클래스를 self-invocation(내부 호출) 없이 쓰도록 설계했다**는 뜻에 가깝다.

---

## 8. beginner가 가장 헷갈리는 지점 세 가지

### 1. "`@Configuration`이 있으면 auto-configuration은 안 쓰는 건가?"

아니다. 둘은 함께 동작한다.

- 내 `@Configuration`은 내 의도를 등록한다
- Boot auto-configuration은 남은 기본값을 조건부로 채운다

실제 애플리케이션은 둘이 섞여 돌아가는 경우가 대부분이다.

여기서 한 번 더 짧게 구분하면:

- component scan은 "우리 클래스 후보를 찾는 과정"
- `@Configuration` + `@Bean`은 "내가 직접 조립 규칙을 적는 과정"
- auto-configuration은 "Boot가 조건부 기본 조립 규칙을 추가하는 과정"

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

위 코드는 `Client`를 메서드 파라미터로 주입받으므로 self-invocation(내부 호출)이 없다.
반대로 `clientService()` 안에서 `client()`를 직접 부르면 그때는 의미가 달라진다.

---

## 9. 실전에서 이렇게 기억하면 덜 헷갈린다

### mental model: 설명서 두 장 + 안전 스위치

- `@Configuration`: 내가 적는 설명서
- auto-configuration: Boot가 들고 오는 기본 설명서
- `@Bean`: 설명서 안의 부품 생성 규칙
- `proxyBeanMethods`: 설명서 안에서 다른 부품 규칙을 self-invocation(내부 호출)할 때 켜는 안전 스위치

이렇게 놓으면 아래도 자연스럽게 연결된다.

- starter를 추가하면 기본 설명서가 늘어난다
- 같은 Bean을 내가 만들면 Boot 기본 설명서는 양보한다
- 설정 클래스 내부 self-invocation(내부 호출)이 있으면 `proxyBeanMethods`가 중요해진다

---

## 10. 코드로 비교하기

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

### 패턴 2. self-invocation(내부 호출)에 기대는 구성

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

## 11. 트레이드오프

### 등록 방식 선택표

| 선택 | 장점 | 주의점 | beginner 기준 언제 고르나 |
|---|---|---|---|
| component scan | 우리 코드에서 가장 짧고 자연스럽다 | 패키지 경계가 틀리면 bean 자체가 안 뜰 수 있다 | `service`/`repository`/`controller`처럼 역할 클래스일 때 |
| `@Configuration` + `@Bean` | 외부 객체 조립 의도를 코드에 명시하기 쉽다 | 설정 클래스가 커지면 self-invocation(내부 호출) 여부를 같이 봐야 한다 | `Clock`, `ObjectMapper`, 외부 SDK client처럼 직접 조립이 필요할 때 |
| Boot auto-configuration | 반복 설정을 줄이고 공용 기본값을 바로 쓸 수 있다 | 왜 안 켜졌는지는 조건 보고서를 봐야 할 수 있다 | starter 기본 계약을 먼저 타고, 필요할 때만 사용자 Bean이나 customizer로 덮을 때 |

| 선택 | 장점 | 주의점 | beginner 기준 |
|---|---|---|---|
| 일반 `@Configuration` | 의도를 명시하기 쉽다 | 빈이 많아지면 구조가 커진다 | 직접 등록이 필요할 때 사용 |
| Boot auto-configuration | 반복 설정을 줄여 준다 | 조건을 모르면 "왜 안 생기지?"가 된다 | 기본값 제공 장치로 이해 |
| `proxyBeanMethods = true` | self-invocation(내부 호출)이 있어도 안전하다 | 프록시 비용과 숨은 동작이 있다 | self-invocation(내부 호출)이 있으면 안전한 기본값 |
| `proxyBeanMethods = false` | 더 단순하고 가볍다 | 직접 메서드 호출 실수를 막지 못한다 | 파라미터 주입 패턴일 때 사용 |

beginner에게 가장 실용적인 기준은 이것이다.

- **`@Bean`끼리는 메서드 파라미터로 연결한다**
- 그러면 `proxyBeanMethods`를 나중에 보더라도 덜 헷갈린다

작게 다음 단계까지 붙이면 이렇다.

- "언제 Boot 기본값이 빠지나?"가 궁금하면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리](./spring-conditionalonmissingbean-vs-primary-primer.md)로 간다.
- "starter를 넣으면 왜 기본 bean이 생기나?"가 궁금하면 [Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나](./spring-boot-autoconfiguration-basics.md)로 간다.

---

## 12. 꼬리질문

> Q: `@Configuration`과 auto-configuration의 가장 큰 차이는 무엇인가?
> 의도: 메커니즘과 소유자 차이 구분
> 핵심: 둘 다 설정 클래스지만, auto-configuration은 Boot가 조건부로 가져오는 기본 설정이다.

> Q: `@Bean`은 무엇을 하는가?
> 의도: 설정 클래스와 개별 팩토리 메서드 구분
> 핵심: 컨테이너에 등록할 객체 생성 규칙을 선언한다.

> Q: `proxyBeanMethods`는 무엇을 지키려는 옵션인가?
> 의도: self-invocation(내부 호출)과 singleton 의미 연결
> 핵심: 설정 클래스 안의 `@Bean` 메서드 self-invocation(내부 호출)이 같은 컨테이너 Bean을 가리키게 보정할지 정한다.

> Q: Boot auto-configuration이 `proxyBeanMethods = false`를 자주 쓰는 이유는 무엇인가?
> 의도: Boot 스타일 이해 확인
> 핵심: 내부 self-invocation(내부 호출) 없이 메서드 파라미터 주입으로 설계해 프록시 필요성을 낮추기 때문이다.

## 한 줄 정리

`@Configuration`과 auto-configuration은 같은 컨테이너 메커니즘 위에서 움직인다. 차이는 누가 설정을 쓰고 어떤 조건에서 켜지느냐이며, `proxyBeanMethods`는 그 설정 클래스 내부 호출을 어떻게 다룰지 정하는 로컬 규칙이다.
