# Spring `@ConfigurationProperties` Binding Internals

> 한 줄 요약: `@ConfigurationProperties`는 단순 프로퍼티 주입이 아니라 binder, conversion, validation, metadata가 결합된 바인딩 파이프라인이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring ConversionService, Formatter, and Binder Pipeline](./spring-conversion-service-formatter-binder-pipeline.md)
> - [Spring Validation and Binding Error Pipeline](./spring-validation-binding-error-pipeline.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

retrieval-anchor-keywords: ConfigurationProperties, Binder, relaxed binding, metadata, immutable properties, constructor binding, validation, property source, bind handler, relaxed binding env var cheatsheet, env var property key mapping, list env var binding, map env var binding

## 핵심 개념

`@ConfigurationProperties`는 application.yml, application.properties, 환경 변수, command-line args 같은 property source를 타입 안전한 객체로 묶는다.

핵심은 단순 주입이 아니라 **바인딩**이다.

- 프로퍼티 소스에서 값 읽기
- 이름 정규화(relaxed binding)
- 타입 변환
- 검증
- 객체 생성

즉, 이 기능은 "값 하나 읽기"가 아니라, **구성 객체를 만들기 위한 전용 바인더**다.

## 깊이 들어가기

### 1. relaxed binding이 핵심이다

```yaml
app:
  max-connections: 20
  timeout-seconds: 3
```

이 값은 다음처럼 매핑될 수 있다.

- `app.max-connections`
- `app.maxConnections`
- `APP_MAX_CONNECTIONS`

이 느슨한 이름 매칭이 운영 환경에서 유용하다.

### 2. Binder가 property source를 읽는다

Spring Boot는 여러 property source를 순서대로 읽어 binder에 넘긴다.

- application.yml
- application.properties
- profile-specific properties
- environment variables
- system properties
- command line args

우선순위가 다르므로 같은 key라도 나중 소스가 이길 수 있다.

### 3. constructor binding은 immutable configuration에 맞다

```java
@ConfigurationProperties(prefix = "app")
public record AppProperties(
    int maxConnections,
    Duration timeoutSeconds
) {}
```

이런 형태는 불변 설정 객체에 잘 맞는다.

### 4. validation은 바인딩과 함께 걸린다

```java
@ConfigurationProperties(prefix = "app")
@Validated
public class AppProperties {

    @Min(1)
    private int maxConnections;
}
```

값이 들어오긴 했지만 규칙을 만족하지 않으면 startup 시점에 실패할 수 있다.

### 5. metadata는 개발자 경험을 높인다

`spring-configuration-metadata.json`은 자동완성, 설명, 힌트에 도움이 된다.

즉, `@ConfigurationProperties`는 런타임 기능이면서 동시에 IDE 친화적인 설계다.

## 실전 시나리오

### 시나리오 1: 값은 있는데 바인딩이 안 된다

대개 key 이름, prefix, 타입 변환이 문제다.

### 시나리오 2: YAML에서는 되는데 환경 변수에서는 안 된다

relaxed binding 규칙을 잘못 이해한 경우다.
먼저 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)에서 dashed key, list index, map key 변환을 확인한다.

### 시나리오 3: 바인딩은 됐는데 validation에서 시작이 막힌다

설정 객체가 잘못되면 애플리케이션이 빨리 fail fast할 수 있다.

### 시나리오 4: 여러 환경에서 다른 값이 들어온다

property source 우선순위를 확인해야 한다.

## 코드로 보기

### immutable properties

```java
@ConfigurationProperties(prefix = "web.client")
public record WebClientProperties(
    @NotNull URI baseUrl,
    Duration connectTimeout
) {}
```

### mutable properties

```java
@ConfigurationProperties(prefix = "db.pool")
@Validated
public class DbPoolProperties {
    private int maxSize;

    public int getMaxSize() {
        return maxSize;
    }

    public void setMaxSize(int maxSize) {
        this.maxSize = maxSize;
    }
}
```

### enable configuration properties

```java
@Configuration
@EnableConfigurationProperties(WebClientProperties.class)
public class ClientConfig {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@Value` | 간단하다 | 타입/구조가 흩어진다 | 한두 개 값 |
| `@ConfigurationProperties` | 구조화가 쉽다 | 초기 설계가 필요하다 | 설정 묶음 |
| constructor binding | immutable하다 | 복잡한 재바인딩이 어렵다 | 읽기 전용 설정 |
| setter binding | 유연하다 | mutable state가 된다 | legacy support |

핵심은 설정을 "값의 집합"이 아니라 **타입이 있는 계약 객체**로 보는 것이다.

## 꼬리질문

> Q: `@ConfigurationProperties`와 `@Value`의 차이는 무엇인가?
> 의도: 설정 모델링 이해 확인
> 핵심: 전자는 구조화, 후자는 단일 값 주입에 가깝다.

> Q: relaxed binding은 왜 중요한가?
> 의도: property source 호환성 이해 확인
> 핵심: 여러 이름 형식을 자연스럽게 매칭한다.

> Q: validation은 언제 일어나는가?
> 의도: startup fail-fast 이해 확인
> 핵심: 바인딩 직후 검증된다.

> Q: immutable properties를 선호하는 이유는 무엇인가?
> 의도: 설계 안정성 이해 확인
> 핵심: 설정 객체를 안전하게 유지하기 쉽다.

## 한 줄 정리

`@ConfigurationProperties`는 property source를 타입 안전한 계약 객체로 바꾸는 바인딩 파이프라인이다.
