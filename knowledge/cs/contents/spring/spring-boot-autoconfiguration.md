# Spring Boot 자동 구성 (Auto-configuration)

> 한 줄 요약: Spring Boot 자동 구성은 애플리케이션 컨텍스트에 필요한 기본 빈을 조건부로 채워 넣어, 개발자가 반복 설정 대신 도메인 코드에 집중하게 만드는 장치다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 **Boot 자동 구성과 조건부 빈 등록의 primer**를 담당한다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Startup / Bean Graph Debugging](./spring-startup-bean-graph-debugging-playbook.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)

retrieval-anchor-keywords: spring boot autoconfiguration, conditional bean registration, enable autoconfiguration, AutoConfiguration.imports, condition evaluation report, boot starter, bean override, spring application context, configuration vs autoconfiguration, @Configuration vs auto-configuration, proxyBeanMethods mental model, --debug first checklist, actuator conditions endpoint, @ConditionalOnMissingBean miss, boot default bean skipped

## 이 문서 다음에 보면 좋은 문서

- 입문 mental model이 먼저 필요하면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)를 먼저 본다.
- 처음 `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean` miss만 빠르게 잡고 싶다면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 이어진다.
- 조건 판단 디버깅은 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)으로 이어진다.
- startup phase와 bean graph는 [Spring Startup / Bean Graph Debugging](./spring-startup-bean-graph-debugging-playbook.md), [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)와 연결된다.

---

## 핵심 개념

`@SpringBootApplication`은 단일 어노테이션처럼 보이지만 실제로는 세 가지를 묶은 조합이다.

- `@SpringBootConfiguration`
- `@EnableAutoConfiguration`
- `@ComponentScan`

이 중 자동 구성의 핵심은 `@EnableAutoConfiguration`이다. Spring Boot는 클래스패스와 현재 Bean 상태를 보고, “지금 이 프로젝트에 필요한 기본 설정”만 골라서 등록한다.

자동 구성은 다음 질문에 답하는 방식으로 동작한다.

1. 이 라이브러리가 클래스패스에 존재하는가?
2. 사용자가 이미 같은 타입의 Bean을 직접 등록했는가?
3. 웹 애플리케이션인가, 배치 애플리케이션인가, 리액티브 애플리케이션인가?

이 기준을 통과한 것만 실제 Bean으로 등록된다.  
즉, 자동 구성은 마법이 아니라 **조건부 Bean 등록 시스템**이다.

`IoC 컨테이너` 관점의 배경은 [IoC 컨테이너와 DI](./ioc-di-container.md)를 먼저 보면 이해가 빠르다.

---

## 깊이 들어가기

### 1. `@SpringBootApplication`은 무엇을 합친 것인가

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan
public @interface SpringBootApplication {
}
```

의미는 단순하다.

- `@ComponentScan`: 현재 패키지와 하위 패키지에서 `@Component`, `@Service`, `@Controller`를 찾는다.
- `@EnableAutoConfiguration`: Boot가 제공하는 기본 설정을 조건부로 가져온다.
- `@SpringBootConfiguration`: 설정 클래스임을 표시한다.

### 2. 자동 구성은 어떻게 import 되는가

Spring Boot는 자동 구성 후보를 별도 메타데이터에서 읽는다.

Boot 3 계열에서는 주로 아래 파일이 기준이다.

```text
META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
```

이 파일에 나열된 자동 구성 클래스들이 후보가 된다.  
실제 등록은 `AutoConfigurationImportSelector`가 담당하고, 이 과정에서 조건을 다시 평가한다.

흐름을 단순화하면 이렇다.

```text
@SpringBootApplication
  -> @EnableAutoConfiguration
    -> AutoConfigurationImportSelector
      -> AutoConfiguration.imports 읽기
      -> 조건 검사
      -> 통과한 설정만 Bean 등록
```

Boot 2.x 시절에는 `spring.factories`가 더 중심적이었고, Boot 3에서는 더 명시적인 자동 구성 메타데이터로 이동했다.  
실무에서는 “어떤 버전의 Boot를 쓰는가”에 따라 디버깅 포인트가 달라진다.

### 3. 조건부 등록의 핵심 어노테이션

자동 구성은 보통 다음 조건 어노테이션을 조합한다.

| 어노테이션 | 의미 |
|---|---|
| `@ConditionalOnClass` | 특정 클래스가 클래스패스에 있을 때만 활성화 |
| `@ConditionalOnMissingBean` | 사용자가 같은 타입의 Bean을 직접 정의하지 않았을 때만 활성화 |
| `@ConditionalOnProperty` | 설정값이 특정 조건일 때만 활성화 |
| `@ConditionalOnWebApplication` | 웹 환경일 때만 활성화 |
| `@ConditionalOnBean` | 다른 Bean이 존재할 때만 활성화 |

예를 들어 JDBC 스타터는 `DataSource` 관련 클래스가 있고, 사용자가 직접 `DataSource`를 안 만들었을 때 기본 구현을 제공한다.

### 4. 왜 자동 구성이 필요한가

자동 구성이 없으면 모든 프로젝트에서 반복적으로 아래를 직접 써야 한다.

- `DataSource`
- `JdbcTemplate`
- `ObjectMapper`
- `MessageConverter`
- `ViewResolver`
- `RestTemplateBuilder` / `WebClient.Builder`

이런 설정은 “한 번만 쓰는 코드”가 아니라, 수십 개 프로젝트에서 반복되는 보일러플레이트다.  
Boot는 이 반복을 줄이고, 사용자가 정말 바꾸고 싶은 부분만 오버라이드하게 만든다.

### 5. Override와 Customization의 원리

자동 구성은 사용자의 Bean보다 우선하지 않는다.  
대부분의 자동 구성은 `@ConditionalOnMissingBean`을 사용하기 때문에, 사용자가 같은 타입의 Bean을 직접 등록하면 Boot 기본값이 빠진다.

즉, 커스터마이징의 핵심은 “자동 구성과 싸우는 것”이 아니라, **내 Bean을 더 먼저 등록해서 기본값을 대체하는 것**이다.

---

## 실전 시나리오

### 시나리오 1: 기본 설정이 있는데도 내가 만든 Bean이 안 쓰이는 경우

```java
@Configuration
public class JacksonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
                .findAndRegisterModules()
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }
}
```

이 경우 Boot의 기본 `ObjectMapper` 대신 내 Bean이 들어가야 한다.  
그런데 `@Bean` 이름 충돌, `@Primary` 설정, 혹은 조건부 구성 타이밍 때문에 의도와 다르게 보일 수 있다.

확인 순서:

1. 같은 타입의 Bean이 여러 개인가
2. `@Primary`가 붙어 있는가
3. 자동 구성 Bean이 `@ConditionalOnMissingBean`으로 빠졌는가
4. 내가 올린 설정 클래스가 스캔 대상인가

### 시나리오 2: 라이브러리를 추가했는데 Bean이 생기지 않는 경우

`spring-boot-starter-web`을 넣었는데도 웹 관련 Bean이 안 보이면 보통 아래를 본다.

- 실제로 `spring-boot-starter-web`이 들어갔는가
- `spring.main.web-application-type`이 `none`으로 강제되지 않았는가
- `DispatcherServlet` 관련 클래스가 클래스패스에 존재하는가
- 내 프로젝트가 web 환경으로 시작했는가

즉, “스타터를 넣었다”는 사실만으로 모든 Bean이 무조건 생기는 게 아니다.  
조건이 맞아야 자동 구성이 활성화된다.

### 시나리오 3: 커스텀 starter를 만들고 싶은 경우

여러 서비스에서 공통으로 쓰는 설정을 묶고 싶다면 커스텀 starter를 만든다.

- `my-company-spring-boot-autoconfigure`
- `my-company-spring-boot-starter`

구성은 보통 두 단계다.

1. 자동 구성 모듈에서 `@Configuration`과 조건부 Bean 정의를 만든다.
2. starter 모듈에서 그 자동 구성 모듈과 필요한 의존성을 모은다.

이렇게 하면 소비자는 의존성 하나만 추가해도 기본 설정을 얻는다.

---

## 코드로 보기

### 자동 구성의 전형적인 형태

```java
@AutoConfiguration
@ConditionalOnClass(JdbcTemplate.class)
public class MyJdbcAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public MyQueryLogger myQueryLogger(JdbcTemplate jdbcTemplate) {
        return new MyQueryLogger(jdbcTemplate);
    }
}
```

이 코드는 다음 뜻을 가진다.

- `JdbcTemplate`이 있을 때만 활성화한다.
- 사용자가 `MyQueryLogger`를 직접 등록하지 않았을 때만 기본 구현을 제공한다.

### 직접 오버라이드하는 예시

```java
@Configuration
public class CustomWebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new LoggingInterceptor());
    }
}
```

Boot의 기본 MVC 설정 위에 내 설정을 얹는 방식이다.  
자동 구성은 “기본값 제공”, 개발자는 “의미 있는 부분만 변경”이 목표다.

### 디버깅용 출력 예시

```java
@Bean
ApplicationRunner runner(ApplicationContext context) {
    return args -> {
        System.out.println(context.getBeanNamesForType(ObjectMapper.class).length);
        System.out.println(Arrays.toString(context.getBeanDefinitionNames()));
    };
}
```

실제 서비스에서는 이런 식으로 Bean 목록을 직접 출력하기보다, 아래 도구를 우선 쓴다.

- `--debug`
- Actuator의 `conditions` 엔드포인트
- `ConditionEvaluationReport`

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 자동 구성 사용 | 설정이 빠르고 일관성이 높다 | 내부 동작이 안 보이면 디버깅이 어렵다 | 대부분의 일반 서비스 |
| 수동 설정 | 동작이 명확하고 통제가 쉽다 | 중복 코드가 늘고 유지보수가 무거워진다 | 특수한 요구사항이 있는 경우 |
| 커스텀 starter | 조직 표준을 재사용할 수 있다 | 초기에 구조 설계가 필요하다 | 여러 서비스에서 같은 기본값을 쓸 때 |

자동 구성은 무조건 좋은 게 아니다.  
프로젝트가 작고 설정 포인트가 거의 없으면, 오히려 수동 설정이 더 이해하기 쉬울 수 있다.  
반대로 서비스가 커질수록 자동 구성은 “표준화된 시작점”으로 강해진다.

---

## 꼬리질문

> Q: `@SpringBootApplication`이 `@EnableAutoConfiguration` 없이도 동작하는 이유는 무엇인가?
> 의도: 메타 어노테이션과 Boot 시작 구조를 이해하는지 확인
> 핵심: `@SpringBootApplication` 자체가 `@EnableAutoConfiguration`을 포함한다.

> Q: `@ConditionalOnMissingBean`이 있으면 내가 정의한 Bean이 항상 이기는가?
> 의도: Bean 등록 순서와 후보 충돌을 아는지 확인
> 핵심: 타입, 이름, `@Primary`, 조건 평가 시점까지 같이 봐야 한다.

> Q: 자동 구성 문제를 디버깅할 때 가장 먼저 무엇을 보나?
> 의도: 실전에서 문제를 좁히는 순서를 아는지 확인
> 핵심: `--debug`, 조건 평가 보고서, 클래스패스, Bean 충돌을 순서대로 본다.

> Q: 커스텀 starter를 왜 `starter`와 `autoconfigure`로 분리하나?
> 의도: 의존성 전파와 자동 구성 책임 분리를 이해하는지 확인
> 핵심: 소비자 편의성과 구현 책임을 분리하려는 구조다.

---

## 한 줄 정리

Spring Boot 자동 구성은 클래스패스와 Bean 상태를 기준으로 기본 설정을 조건부로 제공하고, 개발자가 필요한 부분만 덮어쓰게 만드는 표준화된 IoC 확장 방식이다.
