# Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나

> 한 줄 요약: Spring Boot 자동 구성(Auto-configuration)은 classpath에 라이브러리가 있을 때 미리 만들어둔 Bean 설정을 조건부로 자동 등록해, 개발자가 반복적인 설정을 직접 쓰지 않아도 되게 해준다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)
- [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)
- [IoC와 DI 기초](./spring-ioc-di-basics.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring boot autoconfiguration basics, 스프링 부트 자동 설정 처음, spring starter 왜 동작해요, auto-configuration 입문, @springbootapplication 역할 입문, @enableautoconfiguration beginner, spring boot starter 뭐예요, 자동 빈 등록 입문, conditional bean 입문, spring.factories 입문, spring boot 설정 안 해도 되는 이유, classpath condition beginner

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

## 상세 분해

- **`@SpringBootApplication`**: `@EnableAutoConfiguration`, `@ComponentScan`, `@SpringBootConfiguration` 세 가지를 합친 편의 애노테이션이다.
- **`@EnableAutoConfiguration`**: `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (구버전은 `spring.factories`) 파일에 열거된 자동 구성 클래스를 읽어 조건을 평가하고 Bean으로 등록한다.
- **Starter란**: 자동 구성 클래스 + 관련 라이브러리 의존성을 한 번에 묶은 의존성 패키지다. `spring-boot-starter-web`은 Tomcat, Spring MVC, Jackson 등을 한꺼번에 가져온다.
- **`@ConditionalOnMissingBean`**: 개발자가 동일 타입 Bean을 직접 등록하면 자동 구성은 물러선다. 이 덕분에 필요한 설정만 오버라이드할 수 있다.
- **조건 평가 순서**: 모든 자동 구성 클래스는 일반 `@Configuration` 보다 나중에 처리된다. 개발자 Bean이 먼저 등록되어야 `@ConditionalOnMissingBean`이 올바르게 동작한다.

## 흔한 오해와 함정

**오해 1: starter를 추가하면 무조건 모든 Bean이 등록된다**
`@ConditionalOn*` 조건이 하나라도 실패하면 해당 자동 구성은 건너뛴다. Bean이 뜨지 않으면 `--debug` 옵션으로 실행해 Condition Evaluation Report를 확인한다.

**오해 2: `application.properties`를 채우지 않아도 된다**
`spring.datasource.url` 같은 필수 프로퍼티가 없으면 자동 구성이 조건에서 실패하거나 예외가 발생한다. Starter가 요구하는 최소 프로퍼티는 확인해야 한다.

**오해 3: 자동 구성을 이해하지 않아도 된다**
자동 구성된 Bean과 직접 등록한 Bean이 충돌하거나, 특정 설정을 오버라이드해야 할 때 조건 평가 흐름을 모르면 원인을 찾기 어렵다.

## 실무에서 쓰는 모습

가장 흔한 패턴은 자동 구성 Bean을 커스터마이즈하는 것이다. 예를 들어 `ObjectMapper` 설정을 바꾸고 싶으면 직접 Bean을 등록하면 자동 구성의 기본 `ObjectMapper`가 물러선다.

```java
@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }
}
```

`@ConditionalOnMissingBean` 덕분에 커스텀 Bean이 있으면 자동 구성의 기본 Bean은 등록되지 않는다.

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
