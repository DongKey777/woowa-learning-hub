# Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나

> 한 줄 요약: Spring Boot 자동 구성(Auto-configuration)은 classpath에 라이브러리가 있을 때 미리 만들어둔 Bean 설정을 조건부로 자동 등록해, 개발자가 반복적인 설정을 직접 쓰지 않아도 되게 해준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring Boot 설정 3단계 입문: properties -> customizer -> bean replacement](./spring-boot-properties-vs-customizer-vs-bean-replacement-primer.md)
- [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
- [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)
- [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring boot autoconfiguration basics, 스프링 부트 자동 설정 처음, spring starter 왜 동작해요, auto-configuration 입문, @springbootapplication 역할 입문, @enableautoconfiguration beginner, spring boot starter 뭐예요, 자동 빈 등록 입문, conditional bean 입문, spring.factories 입문, spring boot 설정 안 해도 되는 이유, classpath condition beginner, boot customizer beginner, objectmapper customizer beginner, webclient builder customizer beginner

## 핵심 개념

Spring Boot 이전에는 `DataSource`, `JdbcTemplate`, `TransactionManager` 등 기본 인프라 Bean을 개발자가 XML이나 `@Configuration` 클래스에 직접 등록해야 했다. Spring Boot의 자동 구성은 이 과정을 자동화한다.

핵심 원리는 "**classpath에 무엇이 있으면 어떤 Bean을 자동으로 만들겠다**"는 조건부 등록이다. `spring-boot-starter-data-jpa`를 추가하면 `EntityManagerFactory`, `JpaTransactionManager` 등이 자동으로 등록되는 이유가 여기에 있다.

## 한눈에 보기

```text
build.gradle에 starter 추가
        ↓
classpath에 JPA 관련 라이브러리 포함
        ↓
Spring Boot가 @ConditionalOnClass(JPA 클래스 존재 여부) 평가
        ↓
조건 충족 → JpaAutoConfiguration이 Bean 자동 등록
        ↓
개발자는 application.properties만 채우면 됨
```

| 조건 애노테이션 | 의미 |
|---|---|
| `@ConditionalOnClass` | 특정 클래스가 classpath에 있을 때만 Bean 등록 |
| `@ConditionalOnMissingBean` | 같은 타입의 Bean이 이미 없을 때만 등록 |
| `@ConditionalOnProperty` | 특정 프로퍼티가 설정돼 있을 때만 등록 |

> **오해 분리 3줄**
> `@ConditionalOnMissingBean`은 "Boot 기본 bean을 만들까?"를 묻는다.
> `@Primary`는 "이미 등록된 bean 중 무엇을 먼저 주입할까?"를 묻는다.
> 그래서 `@Primary`를 붙여도 빠진 Boot 기본 bean이 다시 생기지는 않는다.

## `proxyBeanMethods` 30초 연결 (Boot 입문용)

Boot auto-configuration 코드에서 `proxyBeanMethods = false`를 자주 봐도, 초반에는 아래 두 줄만 기억하면 된다.

| 질문 | 빠른 선택 |
|---|---|
| 같은 설정 클래스에서 `@Bean` 메서드를 직접 호출(self-call)하는가? | 일단 `true`로 안전하게 두고, 메서드 파라미터 주입으로 바꾼다 |
| `@Bean` 의존성을 메서드 파라미터로만 연결하는가? | `false`를 써도 안전하다 |

**금지 규칙(초급자용): `@Configuration(proxyBeanMethods = false)`에서 같은 클래스의 다른 `@Bean` 메서드를 직접 호출하지 않는다.**

- 표 전체 판단 흐름은 [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)의 `proxyBeanMethods` 30초 결정표를 본다.
- 왜 self-call이 위험한지 예제로 확인하려면 [Spring Full vs Lite Configuration 예제](./spring-full-vs-lite-configuration-examples.md#lite-self-call-trap)로 바로 이어진다.

## 상세 분해

- **`@SpringBootApplication`**: `@EnableAutoConfiguration`, `@ComponentScan`, `@SpringBootConfiguration` 세 가지를 합친 편의 애노테이션이다.
- **`@EnableAutoConfiguration`**: `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (구버전은 `spring.factories`) 파일에 열거된 자동 구성 클래스를 읽어 조건을 평가하고 Bean으로 등록한다.
- **Starter란**: 자동 구성 클래스 + 관련 라이브러리 의존성을 한 번에 묶은 의존성 패키지다. `spring-boot-starter-web`은 Tomcat, Spring MVC, Jackson 등을 한꺼번에 가져온다.
- **`@ConditionalOnMissingBean`**: 개발자가 동일 타입 Bean을 직접 등록하면 자동 구성은 물러선다. 이 덕분에 필요한 설정만 오버라이드할 수 있다.
- **조건 평가 순서**: 모든 자동 구성 클래스는 일반 `@Configuration` 보다 나중에 처리된다. 개발자 Bean이 먼저 등록되어야 `@ConditionalOnMissingBean`이 올바르게 동작한다.

`@Primary`와 여기의 `@ConditionalOnMissingBean`을 같은 축으로 읽으면 초반에 가장 많이 헷갈린다. 전자는 주입 우선순위, 후자는 자동 구성 back-off 조건이므로 둘을 짧은 비교표로 다시 보고 싶다면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이어진다.

## 흔한 오해와 함정

**오해 1: starter를 추가하면 무조건 모든 Bean이 등록된다**
`@ConditionalOn*` 조건이 하나라도 실패하면 해당 자동 구성은 건너뛴다. Bean이 뜨지 않으면 `--debug` 옵션으로 실행해 Condition Evaluation Report를 확인한다.

| `ConditionEvaluationReport` 첫 확인 3단계 | 초급자용 질문 | 로그에서 기대하는 단서 |
|---|---|---|
| 1. 어떤 자동 구성이 후보였나? | 내가 기대한 `XxxAutoConfiguration`이 아예 평가 대상에 들어왔나? | `Positive matches` 또는 `Negative matches`에 해당 자동 구성 클래스가 보인다 |
| 2. 왜 통과/실패했나? | classpath, property, bean 존재 조건 중 무엇이 걸렸나? | `found required class`, `did not find required class`, `matched`, `did not match` 같은 조건 문구가 보인다 |
| 3. 누가 기본 bean을 밀어냈나? | Boot가 못 만든 건지, 내가 만든 bean 때문에 back-off한 건지? | `@ConditionalOnMissingBean` 관련 `found existing bean` 또는 기존 bean 이름 단서가 보인다 |

- 초반 해석 규칙은 단순하다: "후보였는지" -> "어느 조건에서 멈췄는지" -> "기존 bean 때문에 물러선 것인지" 순서로 본다.
- 표를 한 단계씩 따라가고 싶다면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 이어진다.

**오해 2: `application.properties`를 채우지 않아도 된다**
`spring.datasource.url` 같은 필수 프로퍼티가 없으면 자동 구성이 조건에서 실패하거나 예외가 발생한다. Starter가 요구하는 최소 프로퍼티는 확인해야 한다.

**오해 3: 자동 구성을 이해하지 않아도 된다**
자동 구성된 Bean과 직접 등록한 Bean이 충돌하거나, 특정 설정을 오버라이드해야 할 때 조건 평가 흐름을 모르면 원인을 찾기 어렵다.

## 실무에서 쓰는 모습

가장 흔한 패턴은 Boot가 만든 기본 bean을 통째로 갈아끼우는 것보다, **customizer bean으로 기본 조립 위에 옵션을 얹는 것**이다. 초보자 기준으로는 아래 두 줄을 먼저 떠올리면 된다.

### `ObjectMapper` 미니 비교표

처음에는 코드를 길게 읽기보다 아래 2열만 먼저 기억하면 된다.

| 내가 원하는 것 | 먼저 고를 것 |
|---|---|
| Boot가 만든 기본 `ObjectMapper`는 유지하고 JSON 옵션만 조금 바꾸기 | `Jackson2ObjectMapperBuilderCustomizer` |
| Boot 기본 `ObjectMapper`를 빼고 내가 생성 책임을 직접 가져가기 | top-level `ObjectMapper` `@Bean` 직접 등록 |

즉 "`ObjectMapper`를 건드린다"가 아니라 "`기본 조립 유지`인지, `생성 책임 인수`인지"를 먼저 고르면 초반 오해가 줄어든다.

| 대상 | 옵션만 조금 바꾸고 싶을 때 | 생성 책임까지 직접 가져갈 때 |
|---|---|---|
| `ObjectMapper` | `Jackson2ObjectMapperBuilderCustomizer`로 feature/module/naming 규칙을 덧칠 | top-level `ObjectMapper` bean을 직접 등록해 Boot 기본 조립을 대체 |
| `WebClient.Builder` | `WebClientCustomizer`로 공용 header/filter/baseline을 덧칠 | top-level `WebClient.Builder` bean을 직접 등록해 shared builder owner를 가져감 |

즉 질문은 "`ObjectMapper`를 만질까?"가 아니라 "`ObjectMapper`의 **옵션만 얹을까**, 아니면 **기본 조립 owner가 될까**?"에 가깝다. `WebClient.Builder`도 같은 축으로 읽으면 된다.

예를 들어 JSON 옵션 하나만 바꾸고 싶다면 top-level `ObjectMapper` bean을 직접 등록하기보다 customizer가 더 안전한 기본 선택이다.

```java
@Configuration
public class JacksonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
        return builder -> builder.featuresToDisable(
            DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES
        );
    }
}
```

이 방식은 Boot가 조립하는 기본 `ObjectMapper` 생성 흐름을 유지한 채 필요한 옵션만 추가한다. 반대로 `ObjectMapper` 자체를 `@Bean`으로 등록하면 자동 구성의 기본 bean은 `@ConditionalOnMissingBean` 때문에 물러설 수 있다.

## 실무에서 쓰는 모습 (계속 2)

즉 초보자 기준으로는 이렇게 기억하면 된다.

- 기본 조립 유지 + 옵션 추가: customizer
- 생성 책임 전체 인수: top-level bean 교체

자주 하는 오해도 같이 분리하면 더 안전하다.

- `@Primary`를 붙인다고 Boot 기본 `ObjectMapper`나 shared `WebClient.Builder`가 자동으로 "둘 다 공존"하는 것은 아니다.
- 같은 타입 bean을 직접 등록하면 먼저 `@ConditionalOnMissingBean` back-off가 일어날 수 있고, 그 다음에야 후보 선택 문제가 생긴다.

`ObjectMapper`, `WebClient.Builder`에서 이 경계를 더 짧은 표와 예제로 보고 싶다면 [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)로 이어진다.

## 더 깊이 가려면

- 조건 평가 순서, `proxyBeanMethods`, `@Import` 전략은 [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)에서 이어서 본다.
- Bean이 뜨지 않는 상황 진단 방법은 [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)을 참고한다.

## 면접/시니어 질문 미리보기

> Q: Spring Boot에서 `@SpringBootApplication`이 하는 일을 설명하면?
> 의도: Spring Boot 시작점 이해 확인
> 핵심: `@EnableAutoConfiguration`(자동 구성 활성화), `@ComponentScan`(Bean 스캔), `@SpringBootConfiguration`(설정 클래스) 세 가지를 합친 복합 애노테이션이다.

> Q: `@ConditionalOnMissingBean`이 왜 유용한가?
> 의도: 자동 구성 오버라이드 원리 이해
> 핵심: 개발자가 같은 타입 Bean을 직접 등록하면 자동 구성이 물러서, 필요한 부분만 선택적으로 커스터마이즈할 수 있다.

> Q: Starter와 Auto-configuration의 관계는?
> 의도: 개념 구분 확인
> 핵심: Starter는 의존성 묶음이고, Auto-configuration은 조건부 Bean 등록 로직이다. Starter가 classpath에 라이브러리를 추가하면 Auto-configuration의 조건이 충족되어 Bean이 자동 등록된다.

## 한 줄 정리

Spring Boot 자동 구성은 classpath 조건을 평가해 반복적인 인프라 Bean을 자동으로 등록하고, 개발자가 직접 Bean을 등록하면 자동 구성이 물러서는 방식으로 유연한 오버라이드를 지원한다.
