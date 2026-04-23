# Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입

> 한 줄 요약: full configuration은 `@Bean` self-call을 컨테이너 조회로 보정하고, lite configuration은 그 호출을 그냥 자바 메서드 호출로 처리한다. lite mode를 안전하게 쓰려면 다른 Bean을 메서드 파라미터로 받아야 한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 full configuration, lite configuration, method-parameter injection을 한 번에 비교하는 **focused example note**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)

retrieval-anchor-keywords: full configuration, lite configuration, full vs lite configuration example, proxyBeanMethods example, proxyBeanMethods false safe pattern, method parameter injection bean, @Bean self call, inter-bean reference, configuration class enhancement, @Configuration proxyBeanMethods false, lite mode @Bean, full mode @Bean, auto configuration proxyBeanMethods false, bean self invocation config

## 이 문서 다음에 보면 좋은 문서

- beginner mental model이 먼저 필요하면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)를 먼저 본다.
- `@Configuration` enhancement와 post-processor 체인을 더 깊게 보려면 [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)으로 이어진다.
- Boot가 왜 `proxyBeanMethods = false`를 자주 쓰는지 조건부 등록과 함께 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.
- BeanDefinition, lifecycle, post-processor 관점의 배경은 [IoC 컨테이너와 DI](./ioc-di-container.md)에서 보강한다.

---

## 먼저 용어를 맞춘다

| 용어 | 실제 의미 | 이 문서에서 기억할 한 줄 |
|---|---|---|
| full configuration | `@Configuration(proxyBeanMethods = true)` | `@Bean` self-call을 컨테이너 조회로 보정한다 |
| lite configuration | full enhancement 없이 `@Bean` 메서드가 동작하는 모드 | self-call은 그냥 자바 메서드 호출이다 |
| method-parameter injection | `@Bean` 메서드가 다른 Bean을 파라미터로 받는 패턴 | proxy 없이도 컨테이너 Bean을 안전하게 받는다 |

`@Configuration(proxyBeanMethods = false)`는 inter-bean reference 관점에서 lite mode처럼 동작한다.  
엄밀히는 `@Component` 같은 비-`@Configuration` 클래스의 `@Bean` 메서드도 lite mode다. 이 문서는 Boot 코드에서 가장 자주 마주치는 `@Configuration(proxyBeanMethods = false)`를 대표 예제로 쓴다.

---

## 한눈에 보는 결과

| 패턴 | `auditService()` 안의 의존성 연결 방식 | `context.getBean(AuditClock.class) == context.getBean(AuditService.class).clock()` | 해석 |
|---|---|---|---|
| full configuration | `auditClock()` 직접 호출 | `true` | 프록시가 self-call을 가로채 같은 Bean을 돌려준다 |
| lite configuration + self-call | `auditClock()` 직접 호출 | `false` | 새 객체가 만들어져 managed Bean과 다른 인스턴스가 섞인다 |
| lite configuration + method-parameter injection | `AuditClock auditClock` 파라미터 | `true` | 컨테이너가 Bean을 주입하므로 proxy 없이도 안전하다 |

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

## 1. full configuration: self-call이 있어도 같은 Bean을 쓴다

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
- 그래서 self-call이 있어도 singleton 의미가 유지된다.

이 모드는 기존 설정이 self-call에 기대고 있을 때 안전한 기본값이다.  
대신 설정 클래스 enhancement가 들어가고, 호출 의미가 코드만 보고는 덜 드러난다.

---

## 2. lite configuration + self-call: 보기엔 같아도 다른 객체가 들어간다

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
- `auditService()` 안의 `auditClock()`는 plain Java self-call이라 새 객체를 또 만든다.
- 그 추가 객체는 BeanPostProcessor, lifecycle callback, proxy wrapping의 대상이 아니다.

즉, lite mode에서 self-call을 남겨 두면 깨지는 것은 singleton 의미만이 아니다.

- 관리 대상 Bean과 실제 주입된 객체가 어긋날 수 있다.
- 후처리나 프록시 적용 결과를 기대하면 더 위험하다.
- 코드는 짧아 보여도 동작은 더 덜 명시적이다.

---

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

- self-call 숨은 규칙이 없다.
- refactor 시 어떤 Bean에 의존하는지 IDE와 코드 리뷰에서 바로 보인다.
- Boot auto-configuration이 `proxyBeanMethods = false`를 자주 써도 안전한 이유가 바로 이 패턴이다.

---

## 4. `proxyBeanMethods`보다 먼저 봐야 할 질문

많은 경우 핵심 질문은 "`true`가 더 안전한가?"가 아니라 아래다.

**이 `@Bean` 메서드가 다른 `@Bean` 메서드를 직접 호출하고 있는가?**

- 직접 호출이 있으면 full configuration이 필요하거나, 먼저 method-parameter injection으로 리팩터링해야 한다.
- 직접 호출이 없으면 lite configuration으로 가볍게 두기 쉽다.

즉, `proxyBeanMethods`는 마법 옵션이 아니라 **inter-bean reference 방식을 어떻게 쓸지에 대한 결과값**이다.

```text
직접 호출 self-call
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
| 기존 설정에 self-call이 이미 많다 | full configuration 유지 후 점진 리팩터링 | 동작을 먼저 안전하게 지킨다 |
| 새 설정을 작성한다 | lite configuration + method-parameter injection | 의존성이 명시적이고 가볍다 |
| Boot auto-configuration을 읽고 있다 | lite configuration + method-parameter injection으로 읽는다 | Boot가 보통 이 계약을 전제로 설계한다 |
| `@Component` 안에 `@Bean`을 두었다 | inter-bean self-call을 피한다 | 그 클래스도 lite mode 규칙을 따른다 |

코드 리뷰에서는 아래 한 줄 체크가 가장 싸고 효과적이다.

**`proxyBeanMethods = false`인데 같은 클래스의 다른 `@Bean` 메서드를 직접 호출하면 바로 멈춰서 본다.**

---

## 꼬리질문

> Q: lite configuration에서 문제가 되는 것은 "객체가 두 번 생성된다"뿐인가?
> 의도: singleton semantics보다 더 큰 위험 인식
> 핵심: direct self-call로 만든 객체는 컨테이너 관리 밖에 있어 post-processing, proxy, lifecycle 적용도 어긋날 수 있다.

> Q: method-parameter injection은 full configuration에서도 써도 되는가?
> 의도: 패턴 일반성 확인
> 핵심: 된다. 다만 lite configuration에서도 안전하게 동작하게 만들어 주는 점이 특히 중요하다.

> Q: Boot auto-configuration이 `proxyBeanMethods = false`를 자주 써도 왜 괜찮은가?
> 의도: Boot 스타일과 연결
> 핵심: self-call 대신 메서드 파라미터 주입으로 inter-bean reference를 풀기 때문이다.

## 한 줄 정리

full configuration은 self-call을 보정해 주는 안전장치이고, lite configuration은 그 보정을 포기하는 대신 더 단순한 계약을 요구한다. 그 계약을 가장 안전하게 지키는 방법이 `@Bean` 메서드의 method-parameter injection이다.
