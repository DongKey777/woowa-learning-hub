---
schema_version: 3
title: Spring Full vs Lite Configuration Examples
concept_id: spring/full-vs-lite-configuration-examples
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 84
review_feedback_tags:
- full-vs-lite
- configuration
- full-configuration
- lite-configuration
aliases:
- full configuration
- lite configuration
- proxyBeanMethods example
- proxyBeanMethods false safe pattern
- @Bean self invocation
- method parameter injection bean
- inter-bean reference
intents:
- definition
- comparison
linked_paths:
- contents/spring/spring-configuration-vs-autoconfiguration-primer.md
- contents/spring/spring-configuration-proxybeanmethods-beanpostprocessor-chain.md
- contents/spring/spring-bean-di-basics.md
- contents/spring/spring-boot-autoconfiguration.md
- contents/spring/ioc-di-container.md
expected_queries:
- Spring full configuration과 lite configuration 차이를 예제로 설명해줘.
- proxyBeanMethods=false에서 @Bean 메서드 self-invocation이 왜 위험해?
- @Bean 메서드 파라미터 주입은 proxyBeanMethods=false에서도 왜 안전해?
- inter-bean reference를 직접 호출과 파라미터 주입 중 어떻게 골라?
contextual_chunk_prefix: |
  이 문서는 Spring full configuration과 lite configuration을 proxyBeanMethods,
  @Bean self-invocation, method parameter injection 예제로 비교한다.
  proxyBeanMethods=true는 inter-bean self-call을 컨테이너 조회로 보정하고,
  proxyBeanMethods=false에서는 파라미터 주입이 안전 패턴이라는 beginner primer다.
---
# Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입

> mini guide로 돌아가기: [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)

> 한 줄 요약: full configuration은 `@Bean` self-invocation(내부 호출)을 컨테이너 조회로 보정하고, lite configuration은 그 호출을 그냥 자바 메서드 호출로 처리한다. lite mode를 안전하게 쓰려면 다른 Bean을 메서드 파라미터로 받아야 한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 full configuration, lite configuration, method-parameter injection을 한 번에 비교하는 **focused example note**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)

retrieval-anchor-keywords: full configuration, lite configuration, full vs lite configuration example, proxybeanmethods example, proxybeanmethods decision map, proxybeanmethods 30초 결정표, proxybeanmethods false safe pattern, method parameter injection bean, @bean self invocation, @bean internal call, @bean self call, inter-bean reference, configuration class enhancement, spring full vs lite configuration examples basics, spring full vs lite configuration examples beginner

## 이 문서 다음에 보면 좋은 문서

- beginner mental model이 먼저 필요하면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)를 먼저 본다.
- `@Configuration` enhancement와 post-processor 체인을 더 깊게 보려면 [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)으로 이어진다.
- Boot가 왜 `proxyBeanMethods = false`를 자주 쓰는지 조건부 등록과 함께 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.
- BeanDefinition, lifecycle, post-processor 관점의 배경은 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 보강한다.

입문 문서의 `proxyBeanMethods` 30초 결정표와 이 문서의 예제는 아래처럼 1:1 대응된다.

- self-invocation이 이미 있는 설정을 안전하게 유지해야 한다 -> [`full configuration` 예제](#full-config-self-invocation)
- `proxyBeanMethods = false` + self-invocation 위험을 눈으로 확인하고 싶다 -> [`lite + self-invocation` 예제](#lite-self-invocation-trap)
- `proxyBeanMethods = false`를 안전하게 쓰는 기본 패턴이 필요하다 -> [`lite + method-parameter injection` 예제](#lite-parameter-safe)

---

## 먼저 mental model 한 장

이 문서는 설정 클래스를 아래처럼 보면 가장 빠르게 읽힌다.

- 설정 클래스 = Bean을 조립하는 factory 스크립트
- full configuration = 스크립트 안의 `@Bean` self-invocation도 컨테이너 조회로 보정
- lite configuration = 스크립트 안 self-invocation을 일반 자바 호출로 그대로 실행

즉 `proxyBeanMethods`의 핵심은 "성능 옵션"보다 **inter-bean reference를 self-invocation으로 둘지, 파라미터 주입으로 명시할지**에 가깝다.

---

## 먼저 용어를 맞춘다

| 용어 | 실제 의미 | 이 문서에서 기억할 한 줄 |
|---|---|---|
| full configuration | `@Configuration(proxyBeanMethods = true)` | `@Bean` self-invocation을 컨테이너 조회로 보정한다 |
| lite configuration | full enhancement 없이 `@Bean` 메서드가 동작하는 모드 | self-invocation은 그냥 자바 메서드 호출이다 |
| method-parameter injection | `@Bean` 메서드가 다른 Bean을 파라미터로 받는 패턴 | proxy 없이도 컨테이너 Bean을 안전하게 받는다 |

`@Configuration(proxyBeanMethods = false)`는 inter-bean reference 관점에서 lite mode처럼 동작한다.
엄밀히는 `@Component` 같은 비-`@Configuration` 클래스의 `@Bean` 메서드도 lite mode다. 이 문서는 Boot 코드에서 가장 자주 마주치는 `@Configuration(proxyBeanMethods = false)`를 대표 예제로 쓴다.

---

## 테스트에서 먼저 읽는 10초 요약표

초급자 기준으로는 아래 표만 먼저 잡아도 읽는 순서가 많이 짧아진다.

| `proxyBeanMethods` | `auditService()`가 의존성을 받는 방식 | `context.getBean(AuditClock.class) == context.getBean(AuditService.class).clock()` | 테스트에서 먼저 볼 assertion | 한 줄 해석 |
|---|---|---|---|---|
| `true` | 같은 클래스의 `auditClock()` 직접 호출 | `true` | `assertSame(...)` | self-invocation이 컨테이너 조회로 보정된다 |
| `false` | 같은 클래스의 `auditClock()` 직접 호출 | `false` | `assertNotSame(...)` | plain Java 호출이라 다른 객체가 들어간다 |
| `false` | `AuditClock auditClock` 파라미터 주입 | `true` | `assertSame(...)` | 컨테이너가 Bean을 넣어 주므로 proxy 없이도 안전하다 |

이 표는 아래 순서로 읽으면 된다.

- `proxyBeanMethods = false`인데 같은 클래스의 다른 `@Bean`을 직접 부르면 `assertNotSame(...)` 쪽을 먼저 의심한다.
- `proxyBeanMethods = false`여도 파라미터 주입이면 다시 `assertSame(...)` 쪽으로 돌아온다.
- 즉 초급자에게 중요한 분기점은 "`true/false` 자체"보다 "`직접 호출인가, 파라미터 주입인가`"다.

아래 예제 3개는 모두 이 표의 각 행을 그대로 코드로 펼쳐 놓은 버전이다.

예제에서 쓰는 단순 클래스는 아래와 같다.

```java
public final class AuditClock {
}

public final class AuditService {
    private final AuditClock clock;

    public AuditService(AuditClock clock) {
        this.clock = clock;
    }

    public AuditClock clock() {
        return clock;
    }
}
```

---

## Java/Kotlin을 나란히 보면 더 빨리 보이는 차이

초급자가 Kotlin에서 특히 많이 헷갈리는 지점은 `proxyBeanMethods = false` 자체보다,
expression body 때문에 "메서드 호출"과 "파라미터 주입"이 더 비슷하게 보인다는 점이다.

| 보고 싶은 것 | Java에서 눈에 띄는 부분 | Kotlin에서 눈에 띄는 부분 | 초급자 체크 포인트 |
|---|---|---|---|
| self-invocation 위험 패턴 | `return new AuditService(auditClock());` | `fun auditService() = AuditService(auditClock())` | 괄호로 같은 클래스 메서드를 직접 부르면 위험 신호다 |
| 안전 패턴 | `auditService(AuditClock auditClock)` | `fun auditService(auditClock: AuditClock)` | 파라미터 자리에 타입이 보이면 컨테이너 주입 경로다 |
| Kotlin expression body 인상 | Java보다 덜 숨는다 | 한 줄이라 더 "그냥 값 조립"처럼 보인다 | 짧아 보여도 `auditClock()` 직접 호출이면 plain call이다 |

아래 두 코드는 Kotlin에서 겉모습은 비슷하지만, Spring이 읽는 의미는 다르다.

```kotlin
@Bean
fun auditService() = AuditService(auditClock())
```

- 같은 클래스의 `auditClock()`를 직접 호출한다.
- `proxyBeanMethods = false`라면 plain Kotlin/Java 호출이다.

```kotlin
@Bean
fun auditService(auditClock: AuditClock) = AuditService(auditClock)
```

- `AuditClock`를 메서드 파라미터로 받는다.
- `proxyBeanMethods = false`여도 컨테이너가 Bean을 넣어 준다.

---

<a id="full-config-self-invocation"></a>

## 1. full configuration: self-invocation이 있어도 같은 Bean을 쓴다

```java
@Configuration(proxyBeanMethods = true)
class FullConfig {

    @Bean
    AuditClock auditClock() {
        return new AuditClock();
    }

    @Bean
    AuditService auditService() {
        return new AuditService(auditClock());
    }
}
```

```java
var context = new AnnotationConfigApplicationContext(FullConfig.class);

assertSame(
        context.getBean(AuditClock.class),
        context.getBean(AuditService.class).clock()
);
```

왜 `assertSame(...)`가 성립할까.

- `auditService()` 안의 `auditClock()` 호출이 plain Java call로 끝나지 않는다.
- Spring이 설정 클래스를 enhance해서, 그 호출을 컨테이너의 `AuditClock` 조회로 바꿔 준다.
- 그래서 self-invocation이 있어도 singleton 의미가 유지된다.

이 모드는 기존 설정이 self-invocation에 기대고 있을 때 안전한 기본값이다.
대신 설정 클래스 enhancement가 들어가고, 호출 의미가 코드만 보고는 덜 드러난다.

---

<a id="lite-self-invocation-trap"></a>

## 2. lite configuration + self-invocation: 보기엔 같아도 다른 객체가 들어간다

```java
@Configuration(proxyBeanMethods = false)
class LiteConfigWithSelfCall {

    @Bean
    AuditClock auditClock() {
        return new AuditClock();
    }

    @Bean
    AuditService auditService() {
        return new AuditService(auditClock());
    }
}
```

```kotlin
@Configuration(proxyBeanMethods = false)
class LiteConfigWithSelfCall {

    @Bean
    fun auditClock() = AuditClock()

    @Bean
    fun auditService() = AuditService(auditClock())
}
```

```java
var context = new AnnotationConfigApplicationContext(LiteConfigWithSelfCall.class);

assertNotSame(
        context.getBean(AuditClock.class),
        context.getBean(AuditService.class).clock()
);
```

여기서 가장 중요한 포인트는 "등록된 Bean이 하나 더 생긴다"가 아니라,
**`AuditService`가 컨테이너가 관리하지 않는 `AuditClock`을 품게 된다**는 점이다.

- `auditClock()`는 컨테이너의 `AuditClock` Bean을 만들 때 한 번 호출된다.
- `auditService()` 안의 `auditClock()`는 plain Java self-invocation이라 새 객체를 또 만든다.
- 그 추가 객체는 BeanPostProcessor, lifecycle callback, proxy wrapping의 대상이 아니다.

즉, lite mode에서 self-invocation을 남겨 두면 깨지는 것은 singleton 의미만이 아니다.

- 관리 대상 Bean과 실제 주입된 객체가 어긋날 수 있다.
- 후처리나 프록시 적용 결과를 기대하면 더 위험하다.
- 코드는 짧아 보여도 동작은 더 덜 명시적이다.

---

<a id="lite-parameter-safe"></a>

## 3. lite configuration + method-parameter injection: proxy 없이도 안전하다

```java
@Configuration(proxyBeanMethods = false)
class LiteConfigWithParameterInjection {

    @Bean
    AuditClock auditClock() {
        return new AuditClock();
    }

    @Bean
    AuditService auditService(AuditClock auditClock) {
        return new AuditService(auditClock);
    }
}
```

```kotlin
@Configuration(proxyBeanMethods = false)
class LiteConfigWithParameterInjection {

    @Bean
    fun auditClock() = AuditClock()

    @Bean
    fun auditService(auditClock: AuditClock) = AuditService(auditClock)
}
```

```java
var context = new AnnotationConfigApplicationContext(LiteConfigWithParameterInjection.class);

assertSame(
        context.getBean(AuditClock.class),
        context.getBean(AuditService.class).clock()
);
```

이번에는 `proxyBeanMethods = false`여도 안전하다.

- `auditService()`가 `auditClock()`를 직접 부르지 않는다.
- Spring이 `AuditClock` 파라미터를 컨테이너에서 찾아 넣어 준다.
- 설정 클래스 enhancement가 없어도 `AuditService`는 managed `AuditClock`을 받는다.

이 패턴이 실무에서 특히 좋은 이유는 의존성이 시그니처에 드러나기 때문이다.

- self-invocation 숨은 규칙이 없다.
- refactor 시 어떤 Bean에 의존하는지 IDE와 코드 리뷰에서 바로 보인다.
- Boot auto-configuration이 `proxyBeanMethods = false`를 자주 써도 안전한 이유가 바로 이 패턴이다.

Kotlin에서는 이 차이가 더 중요하다.

- expression body `=` 문법 때문에 두 코드가 더 비슷하게 보인다.
- 하지만 `auditClock()`처럼 괄호가 붙은 직접 호출과 `auditClock: AuditClock`처럼 파라미터로 받는 경우는 의미가 완전히 다르다.
- 초급자라면 Kotlin 설정에서 먼저 "`같은 클래스 메서드를 직접 부르는가, 아니면 파라미터로 받는가`"만 확인해도 대부분의 실수를 줄일 수 있다.

---

## 4. `proxyBeanMethods`보다 먼저 봐야 할 질문

많은 경우 핵심 질문은 "`true`가 더 안전한가?"가 아니라 아래다.

**이 `@Bean` 메서드가 다른 `@Bean` 메서드를 직접 호출하고 있는가?**

- 직접 호출이 있으면 full configuration이 필요하거나, 먼저 method-parameter injection으로 리팩터링해야 한다.
- 직접 호출이 없으면 lite configuration으로 가볍게 두기 쉽다.

즉, `proxyBeanMethods`는 마법 옵션이 아니라 **inter-bean reference 방식을 어떻게 쓸지에 대한 결과값**이다.

```text
직접 호출 self-invocation
-> full configuration이면 보정 가능
-> lite configuration이면 plain Java call

메서드 파라미터 주입
-> full/lite 모두 컨테이너가 인자를 해석
-> proxy 필요성이 크게 줄어듦
```

---

## 5. 선택 기준을 짧게 정리하면

| 상황 | 추천 패턴 | 이유 |
|---|---|---|
| 기존 설정에 self-invocation이 이미 많다 | full configuration 유지 후 점진 리팩터링 | 동작을 먼저 안전하게 지킨다 |
| 새 설정을 작성한다 | lite configuration + method-parameter injection | 의존성이 명시적이고 가볍다 |
| Boot auto-configuration을 읽고 있다 | lite configuration + method-parameter injection으로 읽는다 | Boot가 보통 이 계약을 전제로 설계한다 |
| `@Component` 안에 `@Bean`을 두었다 | inter-bean self-invocation을 피한다 | 그 클래스도 lite mode 규칙을 따른다 |

코드 리뷰에서는 아래 한 줄 체크가 가장 싸고 효과적이다.

**`proxyBeanMethods = false`인데 같은 클래스의 다른 `@Bean` 메서드를 직접 호출하면 바로 멈춰서 본다.**

---

## 흔한 혼동 3가지

- `proxyBeanMethods = false`면 해당 Bean이 prototype처럼 동작한다고 오해하기 쉽다. 스코프가 바뀌는 게 아니라 self-invocation 해석 방식이 바뀌는 것이다.
- "객체가 두 번 생성돼도 기능만 되면 괜찮다"라고 넘기기 쉽다. 하지만 컨테이너 밖 객체라 post-processing/proxy/lifecycle 적용이 어긋날 수 있다.
- method-parameter injection을 "수동 DI"로 오해하기 쉽다. 실제로는 컨테이너가 타입 기준으로 안전하게 해석해 주는 정식 Bean wiring이다.

테스트에서 특히 많이 헷갈리는 지점도 따로 붙잡아 두면 좋다.

- 이 문서의 `assertSame` / `assertNotSame`은 "`@Bean` self-invocation이 같은 인스턴스를 쓰는가"를 보는 identity 테스트다.
- 따라서 "`proxyBeanMethods = false`인데 왜 `assertSame`이 나오지?"라고 느껴지면 먼저 파라미터 주입 예제인지 확인한다.
- 반대로 `@Transactional` self-invocation 문제는 같은 identity 테스트로 바로 판별하지 않는다. 그 경우는 아래 테스트 브리지 문서로 연결하는 편이 안전하다.

> 더 이어서 보면 좋은 문서:
> - [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
> - [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)

---

## 꼬리질문

> Q: lite configuration에서 문제가 되는 것은 "객체가 두 번 생성된다"뿐인가?
> 의도: singleton semantics보다 더 큰 위험 인식
> 핵심: direct self-invocation으로 만든 객체는 컨테이너 관리 밖에 있어 post-processing, proxy, lifecycle 적용도 어긋날 수 있다.

> Q: method-parameter injection은 full configuration에서도 써도 되는가?
> 의도: 패턴 일반성 확인
> 핵심: 된다. 다만 lite configuration에서도 안전하게 동작하게 만들어 주는 점이 특히 중요하다.

> Q: Boot auto-configuration이 `proxyBeanMethods = false`를 자주 써도 왜 괜찮은가?
> 의도: Boot 스타일과 연결
> 핵심: self-invocation 대신 메서드 파라미터 주입으로 inter-bean reference를 풀기 때문이다.

## 한 줄 정리

full configuration은 self-invocation을 보정해 주는 안전장치이고, lite configuration은 그 보정을 포기하는 대신 더 단순한 계약을 요구한다. 그 계약을 가장 안전하게 지키는 방법이 `@Bean` 메서드의 method-parameter injection이다.
