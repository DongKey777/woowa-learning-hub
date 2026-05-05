---
schema_version: 3
title: Spring Boot 자동 구성 기초
concept_id: spring/boot-autoconfiguration-basics
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- starter-magic-mental-model
- configuration-vs-autoconfiguration
- conditional-backoff-first-check
aliases:
- spring boot autoconfiguration basics
- spring boot auto-configuration primer
- spring starter bean registration
- starter bean auto registration
- implicit bean registration
- spring boot autoconfiguration
- spring boot automatic configuration
- spring boot starter default wiring
symptoms:
- starter만 추가했는데 bean이 왜 바로 생기는지 감이 안 와요
- 내가 설정 클래스를 안 만들었는데 DataSource나 ObjectMapper가 보여서 누가 등록했는지 모르겠어요
- auto-configuration과 내가 직접 쓰는 @Configuration을 같은 개념으로 이해하고 있어요
intents:
- definition
- troubleshooting
prerequisites:
- spring/ioc-di-basics
next_docs:
- spring/boot-autoconfiguration-internals
linked_paths:
- contents/spring/spring-boot-autoconfiguration.md
- contents/spring/spring-boot-condition-evaluation-report-first-debug-checklist.md
- contents/spring/spring-configuration-vs-autoconfiguration-primer.md
- contents/spring/spring-conditionalonmissingbean-vs-primary-primer.md
confusable_with:
- spring/boot-autoconfiguration-internals
- spring/spring-configuration-vs-autoconfiguration-primer
- spring/spring-conditionalonmissingbean-vs-primary-primer
forbidden_neighbors: []
expected_queries:
- spring boot 자동구성이 뭐예요?
- starter 추가했는데 왜 bean이 바로 생겨요?
- 설정 안 했는데 spring boot가 bean을 왜 만들어요?
- auto-configuration이랑 configuration은 뭐가 달라요?
- 처음 배우는데 spring boot starter가 왜 동작하는지 모르겠어요
contextual_chunk_prefix: |
  이 문서는 Spring Boot starter를 추가했는데 왜 bean이 바로 생기는지,
  auto-configuration이 뭐인지, configuration과는 뭐가 다른지 처음 묻는
  학습자에게 큰 그림을 먼저 주는 canonical primer다. starter 추가했는데
  바로 동작함, 설정 안 했는데 bean이 생김, spring boot 자동구성 뭐예요,
  자동 설정은 누가 해줘요, 조건이 맞을 때만 bean 등록, classpath 보고
  기본 설정 붙음 같은 자연어 paraphrase를 조건부 bean 등록이라는 mental
  model로 연결한다.
---

# Spring Boot 자동 구성 기초: starter를 추가하면 왜 바로 동작하나

> 한 줄 요약: Spring Boot 자동 구성(Auto-configuration)은 classpath에 라이브러리가 있을 때 미리 만들어둔 Bean 설정을 조건부로 자동 등록해, 개발자가 반복적인 설정을 직접 쓰지 않아도 되게 해준다.
>
> 문서 역할: 이 문서는 "starter를 추가했는데 왜 Bean이 바로 생겨요?", "자동 구성/자동 설정이 뭐예요?" 같은 첫 질문이 깊은 내부 문서보다 먼저 이 입문 문서로 오게 하는 primer entrypoint다.

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

retrieval-anchor-keywords: spring boot autoconfiguration basics, spring boot auto-configuration primer, 스프링 부트 자동 설정 처음, spring starter 왜 동작해요, starter 추가했는데 왜 bean 이 생겨요, starter 넣으면 왜 빈이 자동으로 등록돼요, 설정 안 했는데 왜 bean이 생겨요, spring boot 자동구성 뭐예요, spring boot 자동 설정 뭐예요, 자동 구성 큰 그림, 자동 구성 처음 배우는데, 처음 배우는데 starter auto-configuration 헷갈려요, configuration 이랑 auto-configuration 차이 뭐예요, spring boot starter 뭐예요, what is spring boot autoconfiguration

## 핵심 개념

이 문서는 특히 아래처럼 묻는 초급 질문을 빠르게 받쳐 주는 용도다.

- "starter 추가했는데 왜 바로 동작해요?"
- "자동 설정이 뭐예요?"
- "내가 Bean 등록 안 했는데 왜 생겨요?"

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

## 지금은 지나가도 되는 가지

Boot 문서를 읽다 보면 `proxyBeanMethods = false` 같은 표현이 보일 수 있다.
하지만 "`starter를 추가했는데 왜 Bean이 생겨요?`"를 이해하는 첫 읽기에서는 **필수 축이 아니다.**

초급자는 아래 한 줄만 남기고 지나가면 충분하다.

```text
자동 구성의 핵심은 "어떤 설정 클래스가 로딩되고, 어떤 조건에서 Bean이 생기느냐"이지,
설정 클래스 내부 self-call 최적화 규칙이 아니다.
```

- `proxyBeanMethods`, self-call, lite/full configuration 차이가 궁금할 때만 [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)으로 내려간다.
- 예제로 직접 보고 싶으면 [Spring Full vs Lite Configuration 예제: `proxyBeanMethods`, self-call, 메서드 파라미터 주입](./spring-full-vs-lite-configuration-examples.md)에서 이어서 본다.

## 상세 분해

- **`@SpringBootApplication`**: 앱 시작점이다. 자동 구성 활성화와 component scan 같은 기본 부팅 규칙을 함께 켠다.
- **자동 구성**: Boot가 미리 준비해 둔 설정 묶음을 읽고, classpath와 property 조건이 맞으면 Bean을 등록한다.
- **Starter**: 그 자동 구성이 작동하도록 관련 라이브러리를 한 번에 가져오는 의존성 묶음이다. `spring-boot-starter-web`을 넣으면 Tomcat, Spring MVC, Jackson 같은 웹 기본 재료가 같이 들어온다.
- **`@ConditionalOnMissingBean`**: 개발자가 같은 역할의 Bean을 직접 등록하면 Boot 기본 Bean은 물러선다. 초급자는 이것을 "기본값은 Boot가 주되, 내가 owner가 되겠다고 하면 양보한다" 정도로 이해하면 충분하다.

자동 구성 내부가 실제로 어떤 import 파일을 읽는지, 조건 평가 순서가 어떻게 세밀하게 섞이는지는 첫 입문 범위를 넘는다.
그 갈래는 [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)이나 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)에서 이어서 보면 된다.

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

가장 흔한 패턴은 Boot가 만든 기본 bean을 통째로 갈아끼우는 것보다, **customizer bean으로 기본 조립 위에 옵션을 얹는 것**이다. 이 문서에서는 세부 문법보다 아래 3행 결정표만 먼저 기억하면 충분하다.

| 지금 하려는 변화 | 먼저 고를 것 | 왜 이 선택이 beginner-safe 한가 |
|---|---|---|
| Boot가 만든 기본 `ObjectMapper`는 유지하고 JSON 옵션만 조금 바꾸기 | `Jackson2ObjectMapperBuilderCustomizer` | 기본 조립은 Boot에 두고 feature/module 규칙만 덧칠한다 |
| 공용 `WebClient.Builder`에 header/filter 같은 baseline만 추가하기 | `WebClientCustomizer` | shared builder owner는 유지한 채 공용 기본값만 얹는다 |
| `ObjectMapper`나 `WebClient.Builder`의 생성 책임 자체를 내가 가져가기 | top-level `@Bean` 직접 등록 | 이제는 옵션 추가가 아니라 owner 교체라서 back-off 이후 책임도 직접 진다 |

짧게 말하면 "`ObjectMapper`를 건드릴까?"가 아니라 "**옵션만 얹는가, 아니면 기본 조립 owner가 되는가**"를 먼저 고르는 문제다. `WebClient.Builder`도 같은 축으로 읽으면 된다.

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

## 더 깊이 가려면

- 조건 평가 순서, `proxyBeanMethods`, `@Import` 전략은 [Spring Boot 자동 구성](./spring-boot-autoconfiguration.md)에서 이어서 본다.
- Bean이 뜨지 않는 상황 진단 방법은 [Spring Configuration vs Auto-configuration 입문](./spring-configuration-vs-autoconfiguration-primer.md)을 참고한다.
- `ObjectMapper`, `WebClient.Builder`에서 "옵션만 덧칠"과 "owner 교체" 경계를 더 짧은 표로 다시 보고 싶다면 [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)로 이어진다.

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
