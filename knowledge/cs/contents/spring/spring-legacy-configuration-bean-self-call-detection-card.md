# Spring Legacy Self-invocation(내부 호출) 탐지 카드: `@Configuration`의 위험한 `@Bean` 직접 호출 빠른 점검

> 한 줄 요약: `@Configuration`에서 `@Bean` 메서드가 다른 `@Bean` 메서드를 직접 호출하면, 특히 `proxyBeanMethods = false`일 때 컨테이너가 관리하지 않는 객체가 섞일 수 있다. 이 카드는 self-invocation(내부 호출) 후보를 `rg`로 빠르게 좁히고 리뷰에서 바로 확인할 체크를 제공한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)

retrieval-anchor-keywords: spring legacy self invocation detection card, spring legacy self-call detection card, configuration bean self invocation, configuration bean internal call, configuration bean self call, @Configuration @Bean self-invocation, @Configuration @Bean self-call, proxyBeanMethods false self invocation, proxyBeanMethods false internal call, proxyBeanMethods false self call, rg bean self invocation pattern, spring review checklist self invocation, spring review checklist self call, lite configuration unmanaged object, spring true false check, spring beginner self-check quiz, parameter injection safe pattern, assertSame assertNotSame self invocation verification, assertSame assertNotSame self call verification, spring self invocation test guide, spring self call test guide, kotlin bean detection, kotlin top-level bean function, kotlin fun bean rg, kotlin file level bean function, kotlin configuration class detection

## 먼저 mental model 한 줄

`@Bean` 메서드는 "일반 유틸 메서드"가 아니라 "컨테이너에 등록할 객체를 만드는 entrypoint"다.
같은 클래스에서 `otherBean()`을 직접 호출하면, 코드가 짧아도 **컨테이너 조회가 아닌 일반 메서드 호출**이 될 수 있다.

이 카드에서는 이 상황을 `self-invocation(내부 호출)`으로 통일해 부른다. 기존 문서나 코드 리뷰에서 보던 `self-call`은 같은 뜻으로 보면 된다.

## 30초 비교표

| 패턴 | 초보자 해석 | 위험도 |
|---|---|---|
| `@Bean A a(B b)` (파라미터 주입) | 컨테이너가 `B`를 넣어 준다 | 낮음 |
| `@Bean A a() { return new A(b()); }` | 설정 클래스가 `b()`를 직접 호출한다 | 높음 (`proxyBeanMethods=false`면 특히 위험) |

## `rg`로 빠르게 찾기 (오탐 허용)

### 1) 우선순위 높은 파일: `proxyBeanMethods = false`

```bash
rg -n --glob '*.{java,kt}' '@Configuration\(.*proxyBeanMethods\s*=\s*false'
```

이 파일들은 self-invocation(내부 호출)이 있으면 바로 위험해지기 쉬운 후보군이다.

### 2) 설정 클래스 안 `@Bean` 메서드에서 no-arg 메서드 호출 흔적 찾기

```bash
rg -n -P --glob '*.{java,kt}' '@Bean[\s\S]{0,260}\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\)'
```

`@Bean` 메서드 바디 근처의 `someMethod()` 패턴을 넓게 잡는다. 오탐이 나와도 괜찮다.
핵심은 후보를 빠르게 좁히는 것이다.

### 3) self-invocation(내부 호출)에서 자주 보이는 생성 패턴 추가 탐지

```bash
rg -n --glob '*.{java,kt}' 'return\s+new\s+.*\(.*\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\).*$'
```

`new Service(otherBean())` 형태를 먼저 모아 두면 리뷰 시간이 줄어든다.

## Kotlin에서 `rg`가 놓치기 쉬운 포인트

Java 기준 패턴만 들고 가면 Kotlin 설정 파일에서 후보를 빠뜨리기 쉽다.
초보자 기준 mental model은 이 한 줄이면 충분하다.

**Kotlin은 `new` 대신 생성자 호출을 바로 쓰고, `fun`이 클래스 안에도 파일 바깥에도 올 수 있다.**

### 먼저 비교표로 고정

| 보고 싶은 것 | Java에서 자주 잡는 모양 | Kotlin에서 놓치기 쉬운 모양 |
|---|---|---|
| Bean 생성 | `return new AuditService(...)` | `return AuditService(...)` 또는 `= AuditService(...)` |
| Bean 메서드 선언 | `Type beanName()` | `fun beanName(): Type` |
| 설정 위치 | 보통 클래스 안 | `object`/class 안 + 파일 top-level `fun`까지 가능 |

### Kotlin 후보를 따로 한 번 더 긁는 패턴

1. Kotlin `@Bean fun` 선언 자체를 먼저 모은다.

```bash
rg -n -U --glob '*.kt' '@Bean\\s*(?:\\n\\s*)*(?:public\\s+|internal\\s+|private\\s+)?fun\\s+'
```

`@Bean`과 `fun` 사이에 annotation이나 개행이 끼어도 같이 잡으려는 패턴이다.

2. expression body Bean을 놓치지 않는다.

```bash
rg -n -U --glob '*.kt' '@Bean\\s*(?:\\n\\s*)*(?:public\\s+|internal\\s+|private\\s+)?fun\\s+\\w+\\s*\\([^)]*\\)\\s*[:=]'
```

Kotlin은 아래처럼 중괄호 없이 끝나는 Bean도 많다.

```kotlin
@Bean
fun auditService() = AuditService(auditClock())
```

3. `new` 없이 같은 파일의 no-arg 호출을 본다.

```bash
rg -n -P --glob '*.kt' '@Bean[\s\S]{0,220}\b[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\)'
```

Java/Kotlin 공용 패턴이지만, Kotlin에서는 특히 `AuditService(auditClock())`처럼 생성자 호출 안에 섞여 나오는 self-invocation 후보를 잡는 데 유용하다.

### top-level `fun`도 한 번 의심하기

Kotlin은 파일 top-level 함수가 있을 수 있어서, "설정 클래스 안만 보면 된다"라고 생각하면 검색 범위를 좁혀 버리기 쉽다.

```kotlin
@Bean
fun auditClock() = AuditClock()
```

이런 파일은 프로젝트 규칙상 드물 수 있지만, lane QA 목적에서는 **놓치지 않는 쪽**이 더 중요하다.
처음엔 `*.kt` 전체에서 `@Bean fun`을 모은 뒤, 그다음에 `@Configuration`/`object`/class 문맥을 좁히는 편이 안전하다.

### Kotlin에서 자주 생기는 검색 오해

- `return new ...` 패턴만 찾으면 Kotlin expression body Bean을 거의 전부 놓친다.
- `class ... { @Bean fun ... }`만 가정하면 top-level `fun` 후보를 못 본다.
- `@Bean fun service(clock: Clock)`는 안전 패턴일 수 있으니, **`fun service() = Service(otherBean())` 같은 no-arg self-invocation**을 먼저 본다.

## 리뷰 체크 5개

1. 호출된 메서드가 같은 클래스의 다른 `@Bean` 메서드인가?
2. 해당 클래스가 `@Configuration(proxyBeanMethods = false)`인가?
3. 안전한 대안인 메서드 파라미터 주입(`service(OtherBean otherBean)`)으로 바꿀 수 있는가?
4. self-invocation으로 생성된 객체가 BeanPostProcessor/AOP/lifecycle 적용에서 빠질 가능성은 없는가?
5. 변경 후 최소 검증을 했는가? (`getBean(OtherBean.class)`와 실제 주입 객체 동일성 확인, 필요하면 [`assertSame`/`assertNotSame` 미니 가이드](./spring-self-call-verification-test-mini-guide.md)로 바로 검증)

## 작은 예제

위험한 코드:

```java
@Configuration(proxyBeanMethods = false)
class LegacyConfig {

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

안전한 코드:

```java
@Configuration(proxyBeanMethods = false)
class SafeConfig {

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

## 자주 헷갈리는 포인트

- `proxyBeanMethods = true`면 항상 괜찮다는 뜻은 아니다. legacy 코드에서 의도를 감추기 쉬워 리뷰 난도가 올라간다.
- "동작하니까 괜찮다"가 아니다. self-invocation은 테스트 환경/후처리 체인에서 조용히 다른 객체를 섞을 수 있다.
- 이 카드는 탐지 카드다. 설계 배경이 필요하면 관련 문서(Full vs Lite, Configuration primer)로 바로 이동한다.

## 입문 확인용 미니 점검 (True / False)

아래 3문항은 첫 읽기 이해도 확인용이다. 먼저 스스로 T/F를 고른 뒤 정답을 확인해 보자.

1. `@Configuration(proxyBeanMethods = false)` 클래스에서 `@Bean` 메서드가 같은 클래스의 다른 `@Bean` 메서드를 직접 호출해도 항상 안전하다. (T/F)
2. `@Bean AuditService auditService(AuditClock auditClock)`처럼 메서드 파라미터 주입을 쓰면 self-invocation 위험을 줄이는 데 도움이 된다. (T/F)
3. self-invocation은 "당장 실행이 된다"는 이유만으로 안전하다고 판단해도 된다. (T/F)

정답:

- 1) F
  - 자주 틀리는 이유: `@Bean` 메서드도 "같은 Bean을 돌려주겠지"라고 일반 메서드처럼 생각해서, 직접 호출이 컨테이너 조회가 아니라는 점을 놓치기 쉽다.
- 2) T
  - 자주 틀리는 이유: 초보자는 파라미터 주입이 코드만 길게 만든다고 느끼지만, 실제로는 의존성을 컨테이너가 연결하게 만들어 self-invocation을 피하는 가장 쉬운 안전장치다.
- 3) F
  - 자주 틀리는 이유: 실행 성공을 곧 설정 안전성으로 오해해서, 후처리/AOP/lifecycle이 빠진 "조용한 오작동"은 바로 눈에 안 보인다는 점을 놓친다.

미니 점검이 끝났으면 바로 다음 순서로 [Spring Self-invocation(내부 호출) 검증 테스트 미니 가이드: `assertSame` / `assertNotSame`로 수정 전후를 바로 확인하기](./spring-self-call-verification-test-mini-guide.md) -> [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-invocation(내부 호출), 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)를 본다.
