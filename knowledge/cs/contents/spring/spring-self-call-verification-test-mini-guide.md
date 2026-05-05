# Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기

> 한 줄 요약: `@Configuration`의 `@Bean` self-invocation(내부 호출)이 의심되면, "컨테이너의 Bean"과 "실제로 주입된 객체"가 같은 인스턴스인지 `assertSame` / `assertNotSame`으로 먼저 확인하면 된다. Java와 Kotlin 모두 같은 질문으로 검증한다.

**난이도: 🟢 Beginner**


관련 문서:

- [Spring Legacy Self-invocation(내부 호출) 탐지 카드: `@Configuration`의 위험한 `@Bean` 직접 호출 빠른 점검](./spring-legacy-configuration-bean-self-call-detection-card.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
- [Spring `@Transactional` Self-invocation 검증 테스트 브리지: `@Bean` self-call identity 테스트와 무엇이 다른가](./spring-transactional-self-invocation-test-bridge-primer.md)
- [트랜잭션 기초](../database/transaction-basics.md)

retrieval-anchor-keywords: spring self invocation verification, spring self call verification, assertsame assertnotsame spring bean, configuration bean identity test, proxybeanmethods false test, bean self invocation junit, spring bean identity check, kotlin self invocation test, spring self invocation basics, spring self invocation 처음, spring self invocation 왜 다르지, spring self invocation what is

## 먼저 mental model 한 줄

이 테스트의 질문은 하나다.

`컨테이너에서 꺼낸 Bean`과 `서비스 안에 들어간 의존성 객체`가 **진짜 같은 인스턴스인가?**

- 같으면 `assertSame`
- 다르면 `assertNotSame`

여기서는 `equals()`가 아니라 **객체 동일성(identity)** 을 본다.

이 가이드에서는 `self-invocation(내부 호출)`을 기본 표기로 쓰고, 기존 문서의 `self-call`은 같은 뜻으로 본다.

## 20초 비교표

| 지금 보고 싶은 것 | 어떤 단언을 쓰나 | 해석 |
|---|---|---|
| self-invocation이 실제로 다른 객체를 만들었는지 | `assertNotSame` | "수정 전 위험"을 재현 |
| 파라미터 주입으로 바꾼 뒤 같은 Bean이 들어가는지 | `assertSame` | "수정 후 안전"을 확인 |
| 값이 같은지만 보고 싶은지 | 이 가이드 대상 아님 | self-invocation 검증은 identity가 핵심 |

## Java와 Kotlin을 같이 볼 때 기억할 한 줄

질문은 언어가 아니라 패턴으로 같다.

- Java `new AuditService(auditClock())`와 Kotlin `AuditService(auditClock())`는 둘 다 self-invocation 후보다.
- Kotlin은 `new`가 없고 expression body를 자주 써서 더 짧아 보이지만, `auditClock()`를 직접 부르면 같은 위험이다.
- 수정 방향도 같다. 다른 `@Bean`을 직접 부르지 말고, `@Bean` 메서드 파라미터로 받는다.

## 가장 작은 테스트 템플릿

예제 클래스:

```java
final class AuditClock {
}

final class AuditService {
    private final AuditClock clock;

    AuditService(AuditClock clock) {
        this.clock = clock;
    }

    AuditClock clock() {
        return clock;
    }
}
```

### 1. 수정 전 재현: self-invocation이면 `assertNotSame`

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import static org.junit.jupiter.api.Assertions.assertNotSame;

class SelfCallBeforeFixTest {

    @Test
    void self_call_in_lite_configuration_creates_a_different_instance() {
        try (var context = new AnnotationConfigApplicationContext(BeforeFixConfig.class)) {
            var managedClock = context.getBean(AuditClock.class);
            var injectedClock = context.getBean(AuditService.class).clock();

            assertNotSame(managedClock, injectedClock);
        }
    }

    @Configuration(proxyBeanMethods = false)
    static class BeforeFixConfig {

        @Bean
        AuditClock auditClock() {
            return new AuditClock();
        }

        @Bean
        AuditService auditService() {
            return new AuditService(auditClock());
        }
    }
}
```

초급자 해석:

- `context.getBean(AuditClock.class)`는 컨테이너가 관리하는 Bean
- `auditService().clock()`는 `AuditService` 안에 실제로 들어간 객체
- 둘이 다르면 self-invocation이 plain Java 호출로 새 객체를 만들었다는 뜻

## 가장 작은 테스트 템플릿 (계속 2)

### 2. 수정 후 확인: 파라미터 주입이면 `assertSame`

```java
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import static org.junit.jupiter.api.Assertions.assertSame;

class SelfCallAfterFixTest {

    @Test
    void parameter_injection_reuses_the_managed_bean() {
        try (var context = new AnnotationConfigApplicationContext(AfterFixConfig.class)) {
            var managedClock = context.getBean(AuditClock.class);
            var injectedClock = context.getBean(AuditService.class).clock();

            assertSame(managedClock, injectedClock);
        }
    }

    @Configuration(proxyBeanMethods = false)
    static class AfterFixConfig {

        @Bean
        AuditClock auditClock() {
            return new AuditClock();
        }

        @Bean
        AuditService auditService(AuditClock auditClock) {
            return new AuditService(auditClock);
        }
    }
}
```

초급자 해석:

- self-invocation을 없애고 메서드 파라미터 주입으로 바꿨다
- 이제 `AuditService`는 컨테이너가 찾은 `AuditClock`을 그대로 받는다
- 그래서 같은 인스턴스여야 맞다

## Kotlin 복붙 예제: 읽는 규칙은 Java와 완전히 같다

### 1. 수정 전 재현: Kotlin self-invocation이면 `assertNotSame`

```kotlin
import org.junit.jupiter.api.Assertions.assertNotSame
import org.junit.jupiter.api.Test
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

class AuditClock

class AuditService(
    private val clock: AuditClock,
) {
    fun clock(): AuditClock = clock
}

class SelfCallBeforeFixKotlinTest {

    @Test
    fun `self call in lite configuration creates a different instance`() {
        AnnotationConfigApplicationContext(BeforeFixConfig::class.java).use { context ->
            val managedClock = context.getBean(AuditClock::class.java)
            val injectedClock = context.getBean(AuditService::class.java).clock()

            assertNotSame(managedClock, injectedClock)
        }
    }

    @Configuration(proxyBeanMethods = false)
    class BeforeFixConfig {

        @Bean
        fun auditClock(): AuditClock = AuditClock()

        @Bean
        fun auditService(): AuditService = AuditService(auditClock())
    }
}
```

초급자 해석:

- `auditService()`가 `auditClock()`를 직접 부른다
- Kotlin에서는 `new`가 없어서 덜 위험해 보이지만, 여전히 plain method call이다
- 그래서 컨테이너 Bean과 실제 주입 객체가 달라질 수 있다

### 2. 수정 후 확인: Kotlin도 파라미터 주입이면 `assertSame`

## Kotlin 복붙 예제: 읽는 규칙은 Java와 완전히 같다 (계속 2)

```kotlin
import org.junit.jupiter.api.Assertions.assertSame
import org.junit.jupiter.api.Test
import org.springframework.context.annotation.AnnotationConfigApplicationContext
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

class AuditClock

class AuditService(
    private val clock: AuditClock,
) {
    fun clock(): AuditClock = clock
}

class SelfCallAfterFixKotlinTest {

    @Test
    fun `parameter injection reuses the managed bean`() {
        AnnotationConfigApplicationContext(AfterFixConfig::class.java).use { context ->
            val managedClock = context.getBean(AuditClock::class.java)
            val injectedClock = context.getBean(AuditService::class.java).clock()

            assertSame(managedClock, injectedClock)
        }
    }

    @Configuration(proxyBeanMethods = false)
    class AfterFixConfig {

        @Bean
        fun auditClock(): AuditClock = AuditClock()

        @Bean
        fun auditService(auditClock: AuditClock): AuditService = AuditService(auditClock)
    }
}
```

초급자 해석:

- 수정 포인트는 "Kotlin 문법"이 아니라 "직접 호출 제거"다
- `auditService(auditClock: AuditClock)`처럼 받으면 컨테이너 Bean을 그대로 재사용한다
- 테스트 질문도 Java와 같아서 `assertSame`이면 충분하다

## Java vs Kotlin 한눈 비교

| 보고 싶은 것 | Java 예제 | Kotlin 예제 |
|---|---|---|
| 위험한 self-invocation | `new AuditService(auditClock())` | `AuditService(auditClock())` |
| 안전한 수정 | `auditService(AuditClock auditClock)` | `fun auditService(auditClock: AuditClock)` |
| 수정 전 확인 | `assertNotSame` | `assertNotSame` |
| 수정 후 확인 | `assertSame` | `assertSame` |

## 복붙용 미니 템플릿

아래 4줄만 바꿔도 대부분 바로 검증할 수 있다.

```java
var managedDependency = context.getBean(DependencyType.class);
var actualDependency = context.getBean(TargetBeanType.class).dependency();

assertNotSame(managedDependency, actualDependency); // 수정 전 재현
assertSame(managedDependency, actualDependency);    // 수정 후 확인
```

바꿔 넣을 자리:

- `DependencyType` -> 직접 호출된 `@Bean`의 타입
- `TargetBeanType` -> 그 의존성을 품는 상위 Bean 타입
- `dependency()` -> 실제 필드 getter
- `assertNotSame` / `assertSame` -> 수정 전후에 맞게 하나만 사용

Kotlin으로 바로 옮기면 아래처럼 생각하면 된다.

```kotlin
val managedDependency = context.getBean(DependencyType::class.java)
val actualDependency = context.getBean(TargetBeanType::class.java).dependency()

assertNotSame(managedDependency, actualDependency) // 수정 전 재현
assertSame(managedDependency, actualDependency)    // 수정 후 확인
```

## 자주 헷갈리는 포인트

- `assertEquals`로는 부족하다. 값이 같아도 다른 객체일 수 있다.
- Kotlin에서 `AuditService(auditClock())`처럼 `new` 없이 보여도 self-invocation 여부는 그대로 봐야 한다.
- Kotlin expression body `fun auditService() = AuditService(auditClock())`도 block body와 같은 위험 패턴이다.
- 이 가이드는 `@Configuration`의 `@Bean` self-invocation 검증용이다. `@Transactional`의 self-invocation 검증과는 질문이 다르다. 거기서는 identity가 아니라 동작 신호를 봐야 하므로 [검증 테스트 브리지](./spring-transactional-self-invocation-test-bridge-primer.md)로 바로 넘어가는 편이 빠르다.
- `proxyBeanMethods = true`인 full configuration에서는 self-invocation이어도 `assertSame`이 나올 수 있다. 그 경우는 "위험이 없다"가 아니라 "프록시가 보정했다"에 가깝다.
- getter가 없으면 테스트 전용 package-private accessor를 두거나, 생성자 주입 필드를 노출하는 최소 방법을 택한다. 리플렉션이 첫 선택은 아니다.

## 입문 확인용 self-check

먼저 T/F를 고르고, 바로 아래 1줄 해설로 왜 헷갈렸는지 같이 확인하자.

1. `assertEquals`만 통과하면 self-invocation 문제가 없는 것으로 봐도 된다. (T/F)
   - 오답 포인트: 값 비교가 통과해도 컨테이너 Bean과 주입 객체가 같은 인스턴스라는 뜻은 아니다.
2. `@Configuration(proxyBeanMethods = false)`에서 `AuditService(auditClock())`처럼 직접 호출했다면, 수정 전 재현 테스트는 보통 `assertNotSame`을 기대한다. (T/F)
   - 오답 포인트: `@Bean` 메서드니까 항상 같은 객체를 줄 것이라고 섞어 생각하면 lite configuration의 plain call을 놓치기 쉽다.
3. `auditService(AuditClock auditClock)`처럼 파라미터 주입으로 바꿨는데도 `assertSame` 대신 `assertNotSame`을 써야 컨테이너 개입 여부를 더 엄격하게 검증할 수 있다. (T/F)
   - 오답 포인트: 수정 후 목표는 "다름"을 잡는 강한 테스트가 아니라, 관리 Bean 재사용이 회복됐는지 확인하는 것이다.

정답:

- 1) F: `assertEquals`는 값만 보고, 이 가이드의 질문은 "컨테이너 Bean과 주입 객체가 같은 인스턴스인가"다.
- 2) T: lite configuration의 직접 호출은 컨테이너 조회가 아니라 plain method call이라 다른 인스턴스가 생길 수 있다.
- 3) F: 수정 후 검증은 "더 엄격하게 다름을 찾기"가 아니라, 관리 Bean 재사용이 회복됐는지 `assertSame`으로 확인하는 단계다.

## 언제 이 문서를 쓰면 빠른가

아래 순서면 초급자도 바로 따라가기 쉽다.

1. 탐지는 [Spring Legacy Self-invocation(내부 호출) 탐지 카드](./spring-legacy-configuration-bean-self-call-detection-card.md)에서 한다.
2. 재현은 이 문서의 `assertNotSame` 템플릿으로 한다.
3. 수정은 파라미터 주입으로 바꾼다.
4. 확인은 이 문서의 `assertSame` 템플릿으로 끝낸다.

미니 점검이 끝났으면 바로 다음 문서로 [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)를 본다.

## 한 줄 정리

`@Configuration`의 `@Bean` self-invocation(내부 호출)이 의심되면, "컨테이너의 Bean"과 "실제로 주입된 객체"가 같은 인스턴스인지 `assertSame` / `assertNotSame`으로 먼저 확인하면 된다. Java와 Kotlin 모두 같은 질문으로 검증한다.
