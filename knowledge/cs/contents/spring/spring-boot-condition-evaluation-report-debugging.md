# Spring Boot Condition Evaluation Report Debugging

> 한 줄 요약: ConditionEvaluationReport는 Spring Boot 자동 구성이 왜 켜지고 꺼졌는지 설명해 주는 디버깅 창구이며, 자동 구성 문제의 첫 번째 증거다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)

retrieval-anchor-keywords: ConditionEvaluationReport, auto-configuration report, --debug, conditional beans, auto configuration debugging, positive matches, negative matches, classpath conditions

## 핵심 개념

Spring Boot 자동 구성은 조건부로 동작한다.

- 클래스패스에 있는지
- 특정 Bean이 이미 있는지
- 프로퍼티가 맞는지
- 웹/배치/리액티브 환경인지

이 조건 평가 결과를 요약해 보여 주는 것이 ConditionEvaluationReport다.

즉, 이 리포트는 "왜 이 Bean이 생겼지?"가 아니라 **"왜 이 Bean이 안 생겼지?"**를 설명하는 도구다.

## 깊이 들어가기

### 1. ConditionEvaluationReport는 자동 구성의 판정 로그다

Boot는 자동 구성 후보를 모두 살펴보고, 각 조건의 통과 여부를 기록한다.

- positive matches
- negative matches
- unconditional classes

이 정보가 있어야 자동 구성 문제를 추측이 아니라 사실로 볼 수 있다.

### 2. `--debug`는 가장 빠른 진입점이다

```bash
java -jar app.jar --debug
```

또는 로그 레벨을 통해 조건 평가를 볼 수 있다.

```properties
logging.level.org.springframework.boot.autoconfigure=DEBUG
logging.level.org.springframework.boot.autoconfigure.condition=TRACE
```

이렇게 하면 어떤 조건이 통과했고 어떤 조건이 실패했는지 확인할 수 있다.

### 3. 조건 실패는 보통 네 가지다

- 필요한 클래스가 없었다
- 사용자가 이미 같은 Bean을 등록했다
- 프로퍼티 값이 기대와 달랐다
- web application type이 달랐다

실무에서는 클래스패스 누락보다 `@ConditionalOnMissingBean` 충돌이 더 흔하다.

### 4. 리포트는 "왜 빠졌는지"를 보여 준다

자동 구성은 보통 `@ConditionalOn...`으로 둘러싸여 있다.

조건이 하나라도 맞지 않으면 해당 설정은 제외된다.

그런데 이게 잘못된 설정인지, 의도된 제외인지 구분해야 한다.

- 의도된 제외: 사용자가 직접 Bean을 등록
- 잘못된 제외: 클래스패스나 환경값이 틀림

### 5. 테스트와 운영에서 보는 방식이 다르다

테스트에서는 `@SpringBootTest`로 전체를 올리면서 리포트를 보면 원인을 쉽게 찾을 수 있다.
운영에서는 `--debug`를 항상 켜기보다, Actuator와 로그로 최소한의 힌트를 남기는 편이 낫다.

## 실전 시나리오

### 시나리오 1: 분명 스타터를 넣었는데 Bean이 없다

원인 후보:

- 조건 클래스가 클래스패스에 없다
- 이미 사용자가 같은 타입의 Bean을 등록했다
- Boot 버전이 달라 자동 구성 메타데이터 경로가 다르다

### 시나리오 2: 로컬에서는 되는데 CI에서 자동 구성이 빠진다

대개 환경 차이 때문이다.

- 테스트 프로필
- property override
- 다른 JDK or dependency resolution

### 시나리오 3: 어떤 자동 구성은 켜지고 어떤 것은 꺼진다

이럴 때 리포트에서 positive/negative match를 나눠 보면 된다.

- 어떤 조건이 살아 있는지
- 어떤 조건이 막는지

이 분리가 디버깅 시간을 크게 줄인다.

## 코드로 보기

### 리포트 출력

```java
@Bean
ApplicationRunner reportRunner(ApplicationContext context) {
    return args -> {
        ConfigurableApplicationContext configurableContext =
            (ConfigurableApplicationContext) context;
        ConditionEvaluationReport report =
            ConditionEvaluationReport.get(configurableContext.getBeanFactory());

        report.getConditionAndOutcomesBySource().forEach((source, outcomes) -> {
            System.out.println(source + " -> " + outcomes);
        });
    };
}
```

### debug 로그 사용

```properties
debug=true
```

### 조건부 자동 구성 예

```java
@AutoConfiguration
@ConditionalOnClass(RestClient.class)
@ConditionalOnMissingBean
public class MyRestClientAutoConfiguration {
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `--debug` | 빠르게 조건을 본다 | 로그가 많다 | 로컬/CI 문제 추적 |
| Actuator `conditions` | 운영 중 확인이 쉽다 | 보안 노출을 조심해야 한다 | 운영 진단 |
| 코드에서 직접 출력 | 가장 명시적이다 | 임시 디버깅용이다 | 깊은 조사 |
| 추측으로 수정 | 빠르다 | 재발한다 | 권장하지 않음 |

핵심은 리포트를 "보조 정보"가 아니라, **자동 구성 실패의 1차 증거**로 보는 것이다.

## 꼬리질문

> Q: ConditionEvaluationReport는 무엇을 해결하는가?
> 의도: 자동 구성 디버깅 목적 이해 확인
> 핵심: 왜 어떤 Bean이 생성/비생성됐는지 보여 준다.

> Q: `@ConditionalOnMissingBean` 디버깅에서 가장 먼저 볼 것은 무엇인가?
> 의도: Bean 충돌 원인 이해 확인
> 핵심: 같은 타입의 사용자가 만든 Bean이 있는지 본다.

> Q: `--debug`를 켜면 무엇이 달라지는가?
> 의도: Boot 진단 모드 이해 확인
> 핵심: 자동 구성 조건 평가 로그가 더 많이 나온다.

> Q: 운영에서 리포트를 그대로 노출하면 왜 위험한가?
> 의도: 정보 노출과 보안 인식 확인
> 핵심: 내부 클래스패스와 설정 정보가 드러날 수 있다.

## 한 줄 정리

ConditionEvaluationReport는 Spring Boot 자동 구성의 성공/실패 이유를 가장 직접적으로 보여 주는 디버깅 도구다.
