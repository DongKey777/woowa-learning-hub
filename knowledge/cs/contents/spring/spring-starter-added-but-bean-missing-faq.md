---
schema_version: 3
title: Spring Starter Added But Bean Missing FAQ
concept_id: spring/starter-added-but-bean-missing-faq
canonical: true
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 78
review_feedback_tags:
- starter-added-but
- bean-missing-faq
- bean-missing
- boot-starter-bean
aliases:
- starter added but bean missing
- Spring Boot starter bean not created
- auto configuration negative match
- ConditionalOnClass property existing bean
- component scan boundary starter
- bean missing after dependency added
intents:
- troubleshooting
- definition
linked_paths:
- contents/spring/spring-starter-condition-report-starter-drill.md
- contents/spring/spring-starter-dependency-map-primer.md
- contents/spring/spring-boot-condition-evaluation-report-debugging.md
- contents/spring/spring-boot-autoconfiguration-basics.md
- contents/spring/spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md
- contents/spring/spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md
- contents/spring/spring-scanbasepackages-vs-import-autoconfiguration-selection.md
symptoms:
- starter dependency를 추가했는데 기대한 bean이 ApplicationContext에 없다.
- Condition Evaluation Report에서 negative match가 나왔지만 원인을 읽기 어렵다.
- classpath, property, existing bean, scan boundary 중 무엇이 막았는지 구분이 안 된다.
confusable_with:
- spring/starter-condition-report-starter-drill
- spring/starter-dependency-map-primer
- spring/boot-condition-evaluation-report-debugging
- spring/boot-autoconfiguration-basics
expected_queries:
- Spring Boot starter를 넣었는데 왜 bean이 안 떠?
- dependency 추가만으로 auto-configuration bean이 생성되지 않는 이유는?
- Condition Evaluation Report에서 negative match를 어떻게 읽어야 해?
- starter bean missing 문제를 classpath property override scan boundary로 나눠줘
contextual_chunk_prefix: |
  이 문서는 Spring Boot starter를 추가했다는 사실이 auto-configuration 후보를 classpath에
  올렸다는 뜻일 뿐 실제 bean 생성은 ConditionalOnClass, property, existing bean,
  scan/import boundary가 모두 맞아야 한다는 점을 FAQ로 라우팅한다.
---
# Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary

> 한 줄 요약: starter를 추가했다는 사실은 "자동 구성 후보를 classpath에 올렸다"는 뜻일 뿐이고, 실제 bean 생성은 classpath 조건, property, 기존 bean 존재, scan/import 경계가 모두 맞아야 일어난다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 흔한 "starter added but bean not created" 상황을 classpath/property/override/scan boundary로 빠르게 분기하는 **beginner troubleshooting FAQ**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [Spring Starter Condition Report Starter Drill: `spring-boot-starter-data-jpa` 하나를 positive/negative match로 읽는 법](./spring-starter-condition-report-starter-drill.md)
- [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)
- [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
- [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)
- [Shared Module Guardrails](../software-engineering/shared-module-guardrails.md)

retrieval-anchor-keywords: starter bean missing, starter 넣었는데 bean이 없어요, bean이 왜 안 떠요, spring starter bean missing, starter added but bean missing, why starter bean not created, conditionalonclass classpath trap, conditionalonproperty property missing, existing bean back off, scan boundary bean missing, test slice auto-configuration missing, starter bean troubleshooting basics

## 이 문서 다음에 보면 좋은 문서

- `@Configuration`과 Boot auto-configuration의 큰 그림이 먼저 필요하면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)로 간다.
- starter dependency 한 줄을 positive/negative match 예시와 바로 연결해 보고 싶으면 [Spring Starter Condition Report Starter Drill: `spring-boot-starter-data-jpa` 하나를 positive/negative match로 읽는 법](./spring-starter-condition-report-starter-drill.md)을 먼저 본다.
- 조건 평가를 실제로 보는 첫 진입점은 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)다.
- "`@Primary`를 붙였는데 왜 Boot 기본 bean은 안 돌아오지?"처럼 back-off와 주입 우선순위가 섞이면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 간다.
- "`ObjectMapper` 옵션 하나 바꿨는데 왜 기본 bean 로그가 사라졌지?"처럼 customizer와 직접 bean 등록이 섞이면 [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)로 간다.

## 이 문서 다음에 보면 좋은 문서 (계속 2)

- "`existing bean`이 떠서 기본 bean이 물러난 건지, 아니면 `found 2`처럼 후보가 많아 주입이 애매한 건지"부터 나누고 싶으면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md), [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드: 기본값, 명시 선택, 다중 후보 수집](./spring-primary-qualifier-collection-injection-decision-guide.md)로 이어진다.
- classpath 조건이 왜 환경마다 달라지는지 scope/optional/test slice 기준으로 먼저 나누고 싶으면 [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)로 간다.
- property 조건은 보이는데 운영 env var 이름이 맞는지부터 의심되면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)에서 dotted/dashed/list/map 변환을 먼저 맞춘다.
- "누가 기존 bean으로 간주됐는가"를 더 정확히 보려면 [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)로 이어진다.
- 내 설정 클래스나 shared module 자체가 안 읽힌 것 같으면 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md), [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)으로 넘어간다.

## 이 문서 다음에 보면 좋은 문서 (계속 3)

- `@WebMvcTest`나 `@DataJpaTest`에서만 starter bean이 안 보이면 full context 문제가 아니라 slice 경계 문제일 수 있으니 [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md), [Spring Test Slice `@Import` / `@TestConfiguration` Boundary Leaks](./spring-test-slice-import-testconfiguration-boundaries.md)로 바로 이어간다.

---

## 핵심 개념

초반에는 아래 네 줄만 잡으면 된다.

- starter는 보통 **의존성과 auto-configuration 후보**를 추가한다.
- bean은 후보가 생겼다고 자동으로 확정되지 않고, **조건이 통과해야** 실제 등록된다.
- Boot 기본 bean은 흔히 `@ConditionalOnMissingBean`이라서 **이미 비슷한 bean이 있으면 물러난다**.
- starter가 붙어도 **내 `@Configuration`/`@Component`는 scan/import 경계 밖이면 여전히 안 읽힌다**.

즉 "`starter`를 넣었다"는 말만으로는 원인을 못 정한다.
실제 질문은 아래처럼 바뀌어야 한다.

1. auto-configuration이 classpath 조건에서 탈락했나?
2. property나 profile이 기능을 껐나?
3. 기존 bean 때문에 Boot 기본값이 back off 했나?
4. 내가 기대한 설정 클래스가 scan/import 경계 밖에 있나?

---

## starter가 해 주는 일과 해 주지 않는 일

| starter를 넣으면 보통 생기는 일 | starter를 넣어도 보장되지 않는 일 |
|---|---|
| 관련 라이브러리와 auto-configuration 후보가 classpath에 올라간다 | 조건이 안 맞는데 bean이 강제로 생성되지는 않는다 |
| Boot가 `@ConditionalOnClass`, `@ConditionalOnProperty`, `@ConditionalOnMissingBean`를 평가할 기회를 얻는다 | 내 앱의 임의 package를 대신 scan해 주지 않는다 |
| 소비자 앱이 의존성 하나로 기본 설정을 받을 준비를 한다 | 같은 역할의 사용자 bean이 있어도 Boot 기본 bean을 억지로 유지해 주지 않는다 |

여기서 제일 흔한 오해는 이것이다.

```text
starter 추가 = bean 확정
```

실제 의미는 아래에 더 가깝다.

```text
starter 추가 = auto-configuration 후보 등록 + 조건 평가 시작
```

---

## 30초 분기표

| 먼저 묻는 질문 | 보통 뜻하는 것 | 가장 먼저 확인할 증거 | 다음 문서 |
|---|---|---|---|
| target auto-configuration이 아예 negative match인가? | classpath 조건 또는 웹 타입 조건이 안 맞는다 | `--debug`, Actuator `conditions`, `@ConditionalOnClass`, `@ConditionalOnWebApplication` | [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md) |
| auto-configuration은 보이는데 property 조건에서 꺼졌나? | profile/env/property가 기능을 껐다 | `@ConditionalOnProperty`, active profile, env override | [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md) |
| report에 `@ConditionalOnMissingBean` miss나 `existing bean`이 보이나? | 이미 사용자 bean 또는 다른 starter bean이 있어 기본값이 물러났다 | 내 `@Bean`, `@Import`, test config, 다른 starter | [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md) |
| Boot 쪽은 positive match인데 내 설정 클래스나 커스텀 bean만 안 보이나? | scan/import boundary 문제다 | `@SpringBootApplication` package, `scanBasePackages`, `@Import` 여부 | [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md) |

핵심은 "`bean이 없다`"를 한 문장으로 끝내지 말고, **조건 실패 / property off / back-off / scan miss** 중 어디인지 먼저 가르는 것이다.

## report 문구를 바로 다음 행동으로 바꾸는 phrase router

조건 report를 처음 보면 문장이 길어서 멈추기 쉽다.
초반에는 문장 전체를 해석하려 하지 말고, **눈에 띄는 phrase 하나를 다음 행동 하나에 연결**하면 된다.

| report에서 먼저 잡을 phrase | beginner 해석 | 바로 할 다음 행동 | 연결 문서 |
|---|---|---|---|
| `@ConditionalOnClass did not find required class` | starter는 들어왔지만 필요한 라이브러리나 웹 스택이 classpath에 없다 | dependency scope, optional/provided 설정, test slice 때문에 빠진 클래스가 없는지 본다 | [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md) |
| `did not find property '...'` | 기능 스위치나 필수 설정값이 아직 안 들어왔다 | `application.yml`, active profile, env var 이름이 실제 키로 바인딩됐는지 확인한다 | [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md), [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md) |
| `found beans of type ...` 또는 `@ConditionalOnMissingBean did not match` | Boot가 고장 난 게 아니라 이미 같은 역할 bean이 있어서 기본값이 물러났다 | 내 `@Bean`, `@Import`, test config, 다른 starter가 먼저 같은 타입을 만들었는지 찾는다 | [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md), [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md) |

아주 짧게 외우면 아래처럼 된다.

## report 문구를 바로 다음 행동으로 바꾸는 phrase router (계속 2)

- `did not find class` -> classpath 확인
- `did not find property` -> profile/env/property 확인
- `found beans of type` -> 기존 bean 선점 확인

이 표는 beginner용 첫 라우터다.
문장이 더 길어 보여도, 처음엔 **class / property / existing bean** 세 갈래로만 자르면 충분하다.

## 먼저 갈라야 하는 두 증상: `existing bean` vs `ambiguous bean`

초보자는 둘 다 "`bean 때문에 꼬였다`"로 읽기 쉽지만, 실제 질문이 다르다.

| 먼저 보이는 신호 | 뜻 | 지금 막힌 단계 | 첫 대응 |
|---|---|---|---|
| condition report에 `@ConditionalOnMissingBean` miss, `existing bean`, `found bean 'foo'` | 이미 다른 bean이 있어서 **Boot 기본 bean이 아예 생성되지 않음** | 등록 단계 | 내 `@Bean`, 다른 starter, test config 중 누가 선점했는지 찾는다 |
| startup 예외에 `NoUniqueBeanDefinitionException`, `expected single matching bean`, `found 2` | bean들은 생성됐지만 **주입할 대상을 하나로 못 고름** | 주입 단계 | `@Primary`, `@Qualifier`, `List<T>`/`Map<String, T>` 중 맞는 선택 규칙을 정한다 |

한 줄로 줄이면 이렇다.

- `existing bean`: **Boot 기본값이 물러난 상황**
- `ambiguous bean`: **후보는 있는데 어느 것을 넣을지 못 정한 상황**

즉 `existing bean`은 "`왜 starter 기본 bean이 안 생겼지?`"에 가깝고, `ambiguous bean`은 "`bean은 생겼는데 왜 주입에서 터지지?`"에 가깝다.

자주 헷갈리는 포인트도 같이 본다.

- `existing bean`은 auto-configuration report에서 먼저 보이는 경우가 많다.
- `ambiguous bean`은 보통 예외 메시지 끝의 `found 2`, `found 3`로 드러난다.
- `@Primary`는 `ambiguous bean` 쪽 해법이지, `existing bean` 때문에 빠진 Boot 기본 bean을 되살리는 스위치는 아니다.

## beginner가 자주 만나는 실제 장면: customizer는 덧칠, 직접 bean 등록은 back-off 신호

초보자는 아래 두 코드를 둘 다 "`Jackson 설정을 조금 바꾼다`"로 읽기 쉽다.
하지만 Boot 입장에서는 의미가 다르다.

| 내가 한 일 | Boot가 읽는 의미 | 실제로 보일 수 있는 증상 |
|---|---|---|
| `Jackson2ObjectMapperBuilderCustomizer` 추가 | Boot 기본 `ObjectMapper` 조립은 유지하고 옵션만 덧칠 | 기본 `ObjectMapper`는 계속 Boot 쪽에서 만들어지고, customizer가 그 위에 적용된다 |
| `@Bean ObjectMapper` 직접 등록 | 이미 `ObjectMapper`가 있으니 Boot 기본 `ObjectMapper`는 `@ConditionalOnMissingBean`으로 back off | condition report에 `found beans of type 'ObjectMapper'`가 찍히고 Boot 기본 bean이 안 보인다 |

핵심 mental model은 한 줄이다.

```text
customizer = 기존 Boot 조립에 옵션 추가
직접 bean 등록 = 같은 역할 bean을 먼저 선점해서 Boot 기본값을 물러나게 할 수 있음
```

### 예시 1. customizer를 쓴 경우

```java
@Configuration
public class JsonConfig {

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jsonCustomizer() {
        return builder -> builder.failOnUnknownProperties(false);
    }
}
```

이 경우 beginner는 이렇게 읽으면 된다.

- `ObjectMapper`를 내가 직접 만든 것이 아니다
- Boot 기본 조립은 그대로 있다
- 그래서 "`starter 넣었는데 기본 `ObjectMapper`가 왜 안 보이지?`" 같은 질문과는 거리가 있다

### 예시 2. `ObjectMapper`를 직접 등록한 경우

```java
@Configuration
public class JsonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper().findAndRegisterModules();
    }
}
```

이 경우에는 질문이 달라진다.

- "Jackson 설정을 조금 바꿨다"가 아니라 **`ObjectMapper` 생성 책임을 내가 가져왔다**
- Boot auto-configuration은 "`이미 `ObjectMapper`가 있네`"라고 읽고 물러날 수 있다
- 그래서 condition report에 `@ConditionalOnMissingBean` miss나 `found beans of type 'ObjectMapper'`가 보이면 정상적인 back-off 해석이 먼저다

처음엔 아래처럼 짧게 외우면 충분하다.

## beginner가 자주 만나는 실제 장면: customizer는 덧칠, 직접 bean 등록은 back-off 신호 (계속 2)

| 보이는 증상 | beginner 해석 | 먼저 볼 문서 |
|---|---|---|
| customizer bean만 추가했는데도 기본 `ObjectMapper`가 그대로 있음 | 이상이 아니라 의도된 동작이다 | [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md) |
| `ObjectMapper`를 직접 등록했더니 Boot 기본 bean 관련 match가 사라짐 | 직접 등록한 bean 때문에 auto-configuration이 back off했을 가능성이 크다 | [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md) |

`WebClient.Builder`도 감각은 같다.

- `WebClientCustomizer`: Boot가 만든 shared builder에 기본 헤더나 filter를 덧칠
- `@Bean WebClient.Builder`: shared builder owner를 직접 가져가서 Boot 기본 흐름이 back off될 수 있음

즉 starter를 넣은 뒤 "`내가 옵션만 추가한 건지, 같은 타입 bean을 먼저 등록한 건지`"를 먼저 갈라야 `@ConditionalOnMissingBean` back-off를 실제 증상과 연결할 수 있다.

## 로그 한 토막을 표에 연결해 읽는 법

초보자에게 가장 중요한 감각은 "`report 문장 한 줄`을 보면 `30초 분기표`의 어느 칸인지 바로 떠오르는 것"이다.

먼저 아주 짧게 연결하면 이렇다.

| 로그에서 먼저 보이는 문장 | 표에서 연결할 칸 | beginner 해석 |
|---|---|---|
| `did not match` + `did not find property 'spring.datasource.url'` | property off / 필수 설정 없음 | starter는 올라왔지만 DataSource 조건이 아직 완성되지 않았다 |
| `@ConditionalOnMissingBean ... found beans of type 'ObjectMapper' objectMapper` | back-off / existing bean | Boot가 Jackson 기본값을 못 만든 게 아니라 이미 사용자 bean이 있어서 물러났다 |

### 예시 1. `DataSourceAutoConfiguration`이 property 조건에서 멈춘 경우

아래처럼 `--debug`에서 한 토막이 보였다고 하자.

```text
DataSourceAutoConfiguration:
   Did not match:
      - @ConditionalOnProperty (spring.datasource.url) did not find property 'spring.datasource.url' (OnPropertyCondition)
```

이 로그를 처음 읽을 때는 길게 해석하지 말고 세 줄만 붙이면 된다.

| 로그 조각 | 바로 붙이는 해석 | 다음 행동 |
|---|---|---|
| `DataSourceAutoConfiguration` | 지금 추적하는 target auto-configuration이 맞다 | 다른 클래스 말고 이 블록을 계속 본다 |
| `Did not match` | Boot가 고장 난 게 아니라 **조건이 false**다 | classpath보다 property 쪽을 먼저 본다 |
| `did not find property 'spring.datasource.url'` | starter는 있어도 DB 연결 정보가 없어 DataSource를 안 만들었다 | `application.yml`, profile, env var에 `spring.datasource.url`이 실제로 들어왔는지 확인한다 |

즉 이 예시는 "`bean이 왜 없지?`"보다 **"`property 조건에서 멈췄구나`**"로 읽으면 된다.

### 예시 2. `JacksonAutoConfiguration`이 기존 `ObjectMapper`를 보고 물러난 경우

이번에는 아래 같은 토막을 보자.

## 로그 한 토막을 표에 연결해 읽는 법 (계속 2)

```text
JacksonAutoConfiguration.JacksonObjectMapperConfiguration#jacksonObjectMapper:
   Did not match:
      - @ConditionalOnMissingBean (types: com.fasterxml.jackson.databind.ObjectMapper; SearchStrategy: all)
        found beans of type 'com.fasterxml.jackson.databind.ObjectMapper' objectMapper (OnBeanCondition)
```

이 로그는 `DataSourceAutoConfiguration` 예시와 질문이 다르다.

| 로그 조각 | 바로 붙이는 해석 | 다음 행동 |
|---|---|---|
| `Did not match` | 겉보기에는 똑같이 negative match다 | 하지만 이유가 property/classpath가 아니라 bean 존재 조건인지 본다 |
| `@ConditionalOnMissingBean` | Boot 기본값은 "없을 때만" 만든다 | 누가 먼저 `ObjectMapper`를 등록했는지 찾는다 |
| `found beans of type ... objectMapper` | 이미 사용자 또는 다른 설정이 `ObjectMapper`를 올렸다 | 내 `@Bean`, test config, 다른 starter 중 선점 경로를 확인한다 |

즉 이 예시는 "`Jackson`이 안 떠서 실패"가 아니라 **"기본 `ObjectMapper`는 의도적으로 back off 했다"**에 가깝다.

자주 하는 오해도 같이 끊어 두면 좋다.

- `DataSourceAutoConfiguration` 예시는 property 칸에 넣는다. `@Primary`와는 무관하다.
- `JacksonAutoConfiguration` 예시는 existing bean/back-off 칸에 넣는다. 여기서도 `@Primary`는 빠진 기본 bean을 되살리지 못한다.
- 둘 다 `Did not match`로 시작해도, **뒤에 따라오는 조건 문장**이 실제 분기 기준이다.

## 미니 카드: `@WebMvcTest`와 `@DataJpaTest`에서 starter bean이 빠져 보이는 대표 장면

초보자가 가장 많이 헷갈리는 지점은 "`starter`를 넣었는데 왜 테스트에서만 bean이 안 보이지?"다.
이때는 production app 전체가 아니라 **test slice가 일부 auto-configuration과 bean 종류만 허용한다**는 점부터 떠올리면 된다.

| 테스트 어노테이션 | 초보자가 기대하는 것 | 실제로 자주 빠지는 것 | 왜 그렇게 보이나 | 첫 대응 |
|---|---|---|---|---|
| `@WebMvcTest` | `spring-boot-starter-web`이나 security starter를 넣었으니 service/client/helper bean도 같이 보일 것 | `@Service`, `@Repository`, 외부 API client, 일반 `@Component`, 일부 custom starter bean | MVC slice는 controller와 web 관련 bean 중심으로만 컨텍스트를 자른다 | controller 계약만 볼 테스트인지 확인하고, 필요한 협력자는 `@MockBean` 또는 좁은 `@Import`로 넣는다 |
| `@DataJpaTest` | `spring-boot-starter-data-jpa`를 넣었으니 service나 웹 쪽 starter bean도 같이 보일 것 | `@Service`, MVC/security bean, 일반 application service, web starter bean | JPA slice는 entity/repository/JPA infra만 남기고 나머지 레이어를 뺀다 | repository/JPA 검증이 목적이면 그대로 두고, service까지 봐야 하면 `@SpringBootTest` 또는 다른 테스트 경계로 올린다 |

짧게 외우면 아래 한 줄이다.

- `@WebMvcTest`는 "web 관련 bean만 남긴다"
- `@DataJpaTest`는 "JPA 관련 bean만 남긴다"

즉 slice 테스트에서 starter bean이 빠진 것처럼 보여도, 먼저 "`조건 실패`"보다 **"`이 bean이 원래 이 slice에 포함되는 종류인가`"**를 본다.

---

## 자주 묻는 질문

### Q1. starter를 넣었는데 왜 bean이 안 생기나?

가장 흔한 답은 "starter가 틀렸다"가 아니라 **조건이 아직 다 맞지 않았다**다.

- 필요한 클래스가 classpath에 없을 수 있다
- property가 `false`거나 다른 profile에서 꺼졌을 수 있다
- 이미 같은 역할의 bean이 있어서 Boot 기본값이 빠졌을 수 있다
- 기대한 설정 클래스가 scan/import 경계 밖일 수 있다

예를 들어 `spring-boot-starter-web`이 있어도 아래처럼 강제로 non-web 문맥이면 servlet 계열 bean 기대가 깨질 수 있다.

```properties
spring.main.web-application-type=none
```

즉 starter는 기능 후보를 제공하지만, **현재 애플리케이션 문맥이 그 기능을 실제로 켜는지**는 별도다.

### Q2. `@Primary`를 붙였는데 왜 Boot 기본 bean이 다시 안 뜨나?

`@Primary`는 **주입 시점의 우선 선택 규칙**이지, auto-configuration back-off를 되돌리는 스위치가 아니다.

- `@ConditionalOnMissingBean`은 "이미 bean이 존재하는가"를 본다
- `@Primary`는 "여러 bean 중 무엇을 주입할까"를 본다

즉 이미 사용자 bean이 하나라도 존재해서 Boot 기본값이 물러났다면, `@Primary`를 붙여도 "빠진 auto-config bean을 다시 생성"하지는 않는다.

이 구분을 등록 단계와 주입 단계로 짧게 다시 잡고 싶다면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)를 바로 이어서 본다.

### Q2-1. `ObjectMapper` 옵션만 바꾸려 했는데 왜 starter 기본 bean 로그가 사라지나?

대개 `customizer`가 아니라 **같은 타입 bean을 직접 등록했기 때문**이다.

- `Jackson2ObjectMapperBuilderCustomizer`는 Boot 기본 조립을 유지한다
- 반면 `@Bean ObjectMapper`는 Boot가 보기엔 "`이미 `ObjectMapper` 있음`"이 된다
- 그래서 `@ConditionalOnMissingBean`이 붙은 기본 `ObjectMapper` 경로는 back off될 수 있다

처음에는 이렇게 구분하면 된다.

| 내가 원한 것 | 보통 더 맞는 선택 |
|---|---|
| Boot 기본 JSON 조립은 유지하고 옵션만 조금 바꾸기 | `Jackson2ObjectMapperBuilderCustomizer` |
| `ObjectMapper` 생성 규칙 자체를 내가 직접 책임지기 | `@Bean ObjectMapper` 직접 등록 |

## 자주 묻는 질문 (계속 2)

같은 패턴을 `WebClient.Builder`까지 한 번에 묶고 싶다면 [Spring Boot Customizer vs Top-Level Bean 교체 입문: `ObjectMapper`, `WebClient.Builder`는 언제 덧칠하고 언제 갈아끼울까](./spring-boot-customizer-vs-top-level-bean-replacement-primer.md)를 이어서 본다.

### Q3. `spring.main.allow-bean-definition-overriding=true`를 켜면 해결되나?

대개 아니다.

이 설정은 **같은 bean name 정의 충돌을 허용할지**에 가깝다.
반면 starter bean 누락의 흔한 원인은 아래 둘이다.

- 조건 실패로 auto-configuration이 애초에 실행되지 않음
- `@ConditionalOnMissingBean`이 기존 bean을 보고 back off 함

즉 override 허용은 **이미 충돌이 난 bean definition**의 문제이고, "`조건이 안 맞아 생성되지 않았다`"와는 별개다.

### Q4. starter를 넣었는데 내 `@Configuration`이 왜 안 읽히나?

starter와 component scan은 다른 경로다.

- starter auto-configuration은 metadata를 통해 import 된다
- 내 앱의 `@Configuration`/`@Component`는 여전히 scan 또는 `@Import`가 필요하다

따라서 shared module에 설정 클래스를 만들어 놓고 "starter를 넣었으니 소비자 앱이 알아서 scan하겠지"라고 기대하면 자주 빗나간다.
이 경우는 broad scan보다 `@Import` 또는 starter-style auto-configuration 계약이 더 맞을 수 있다.

### Q5. 다른 환경에서는 되는데 테스트나 CI에서만 bean이 사라진다

대개 코드보다 **환경 입력값 차이**를 먼저 의심한다.

- test slice가 전체 auto-configuration을 안 올릴 수 있다
- test property가 feature를 껐을 수 있다
- dependency scope나 optional dependency 차이로 classpath가 달라질 수 있다

특히 초반에는 "`starter`가 빠졌다"와 "`slice가 원래 그 bean 종류를 제외했다`"를 분리해야 한다.

## 자주 묻는 질문 (계속 3)

| 장면 | 먼저 붙일 해석 | 바로 다음 확인 |
|---|---|---|
| `@WebMvcTest`에서 service나 custom starter helper가 없음 | 대개 starter 고장보다 MVC slice 경계다 | [Spring Test Slice Scan Boundary 오해: `@WebMvcTest`, `@DataJpaTest`, custom test config는 full `@SpringBootTest`가 아니다](./spring-test-slice-scan-boundaries.md)에서 slice 포함 대상부터 본다 |
| `@DataJpaTest`에서 service/web/security bean이 없음 | 대개 JPA slice가 레이어를 잘랐다 | repository/JPA 확인이 목적이 맞는지 보고, 아니면 test 종류를 다시 고른다 |
| CI에서만 `did not find class`가 뜸 | slice가 아니라 dependency scope/classpath diff일 수 있다 | [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)로 간다 |

이 경우는 [Spring `@ConditionalOnClass` classpath 함정 입문: starter는 있는데 왜 환경마다 auto-configuration이 빠질까](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)에서 scope / optional / slice를 먼저 분리하면 빠르다.

즉 "같은 코드인데 다르게 보인다"면 우선 classpath/profile/property diff를 본다.

---

## 가장 흔한 예시 두 개

### 1. 사용자 bean 때문에 Boot 기본값이 물러나는 경우

```java
@Configuration
public class CustomClockConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }
}
```

Boot 쪽이 아래처럼 설계돼 있다면:

```java
@Bean
@ConditionalOnMissingBean
public Clock systemClock() {
    return Clock.systemDefaultZone();
}
```

이 상황은 "starter bean 생성 실패"라기보다 **사용자 bean이 이미 존재해서 기본값이 빠진 상태**다.

### 2. starter는 붙었지만 내 설정은 scan 경계 밖인 경우

```text
com.example.bootstrap.Application
com.example.feature.CustomFeatureConfig
com.shared.support.ExternalModuleConfig
```

`Application`이 `com.example.bootstrap` 아래에 있고 `ExternalModuleConfig`가 `com.shared.support`에 있다면, starter 유무와 별개로 그 설정 클래스는 기본 component scan에 잡히지 않을 수 있다.

즉 아래 두 문장을 분리해서 봐야 한다.

- starter auto-configuration 후보는 classpath에 올라왔다
- 내가 기대한 custom config는 scan/import 경계 밖이라 안 읽혔다

---

## 마지막 체크리스트

1. target bean 이름과 auto-configuration 클래스 이름을 먼저 적는다.
2. `--debug` 또는 Actuator `conditions`에서 positive/negative match를 확인한다.
3. negative match면 classpath 조건인지 property 조건인지 한 줄로 적는다.
4. `existing bean` 또는 `@ConditionalOnMissingBean` miss면 내 `@Bean`/`@Import`/다른 starter를 찾는다.
5. Boot 쪽은 positive인데 내 설정만 안 보이면 component scan 또는 `@Import` 경계를 본다.

이 순서로 보면 "`starter 넣었는데 bean이 안 떠요`"를 감으로 푸는 대신, **조건 평가 -> 기존 bean -> scan boundary** 순서로 좁힐 수 있다.

## 한 줄 정리

starter를 추가했다는 사실은 "자동 구성 후보를 classpath에 올렸다"는 뜻일 뿐이고, 실제 bean 생성은 classpath 조건, property, 기존 bean 존재, scan/import 경계가 모두 맞아야 일어난다.
