# Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`

> 한 줄 요약: Spring Boot 기본 Bean이 안 뜨거나 갑자기 빠졌다면, 먼저 `--debug`나 Actuator `conditions`로 조건 평가를 보고 `@ConditionalOnMissingBean`에 막힌 것인지부터 확인하면 된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 configuration/autoconfiguration primer 다음 단계의 **ConditionEvaluationReport beginner bridge**이자 **first-debug checklist**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)
> - [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)

retrieval-anchor-keywords: ConditionEvaluationReport beginner, condition evaluation report checklist, boot condition report first debug, --debug first checklist, debug=true, actuator conditions endpoint, conditions endpoint beginner, @ConditionalOnMissingBean miss, existing bean found, user bean wins, boot default bean skipped, auto-configuration first debug, why boot bean missing, starter bean not created, spring boot conditions report beginner route, @ConditionalOnProperty havingValue, @ConditionalOnProperty matchIfMissing, property missing vs false, @ConditionalOnMissingBean vs @Primary, primary is not auto-configuration override

## 이 문서 다음에 보면 좋은 문서

- `@Configuration`과 Boot auto-configuration의 큰 그림이 아직 흐리면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)를 먼저 본다.
- 자동 구성 자체의 동작 원리를 더 넓게 보려면 [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)으로 이어진다.
- report에서 `existing bean found`를 봤는데 `@Primary`와 무엇이 다른지 헷갈리면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리: auto-configuration back-off와 bean 선택은 다르다](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이어진다.
- report 구조와 조건 종류를 더 깊게 파고들려면 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)으로 이어진다.
- `conditions` endpoint를 운영에서 어떻게 안전하게 열지 고민되면 [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)를 같이 본다.

---

## 핵심 개념

초반에는 아래 세 문장만 잡으면 된다.

- Boot auto-configuration은 항상 조건부다.
- `--debug`와 Actuator `conditions`는 그 조건 평가를 가장 빨리 보여 주는 창구다.
- `@ConditionalOnMissingBean`이 막혔다면 "Boot가 고장 났다"보다 **"이미 같은 역할의 Bean이 있었다"** 쪽이 더 흔하다.

즉, 증상을 이렇게 바꿔 말하면 된다.

- 전: "`ObjectMapper`가 왜 안 떠?"
- 후: "`JacksonAutoConfiguration`이 negative match였나, 아니면 `@ConditionalOnMissingBean` 때문에 물러났나?"

이 질문 전환이 되면 디버깅이 추측에서 조건 확인으로 바뀐다.

---

## 1. 언제 이 체크리스트로 들어가나

아래 셋 중 하나면 이 문서의 범위다.

- 스타터를 넣었는데 기대한 Boot Bean이 안 생긴다.
- 내가 `@Bean`을 하나 추가했더니 원래 있던 Boot 기본 Bean이 사라진다.
- 로컬에서는 되는데 테스트, CI, 다른 profile에서는 자동 구성이 달라진다.

반대로 아래라면 다른 문서가 더 먼저다.

- 내 `@Configuration`이나 `@Component`가 아예 로드되지 않는다.  
  이 경우는 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md) 쪽이 더 가깝다.
- startup 전체가 `BeanCreationException`, binding failure, circular reference로 무너진다.  
  이 경우는 [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)로 올라간다.

---

## 2. first-debug checklist

### 1. 타깃 Bean과 자동 구성 이름을 먼저 적는다

로그가 시끄러운 이유는 대개 타깃이 없기 때문이다.

처음에는 아래 두 개만 적으면 충분하다.

- 찾고 싶은 Bean 타입 또는 이름  
  예: `ObjectMapper`, `DataSource`, `TaskExecutor`
- 의심되는 auto-configuration 클래스  
  예: `JacksonAutoConfiguration`, `DataSourceAutoConfiguration`

이렇게 적어 두면 `--debug`를 켰을 때 어디를 찾아야 하는지가 바로 생긴다.

### 2. 재시작 가능한 환경이면 `--debug`부터 본다

가장 빠른 진입점은 여전히 `--debug`다.

```bash
java -jar app.jar --debug
```

또는 설정으로도 켤 수 있다.

```properties
debug=true
```

여기서 할 일은 많지 않다.

1. `CONDITIONS EVALUATION REPORT` 블록을 찾는다.
2. 타깃 auto-configuration 이름을 찾는다.
3. positive match인지 negative match인지 먼저 본다.
4. negative match라면 어떤 조건이 false였는지 한 줄로 적는다.

처음부터 전체 report를 이해하려고 하지 말고, **내가 찾는 auto-configuration 한 개만 따라간다**고 생각하면 된다.

### 3. 이미 떠 있는 앱이면 Actuator `conditions`를 본다

restart가 어렵거나 "운영 profile에서만 다르다" 같은 상황이면 `conditions` endpoint가 빠르다.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,conditions
```

이 endpoint는 ConditionEvaluationReport 계열 정보를 HTTP로 보여 주는 진단 창구다.

- restart 없이 확인할 수 있다
- 지금 떠 있는 profile / property / classpath 문맥을 본다
- 같은 auto-configuration을 positive/negative match로 나눠 볼 수 있다

다만 이건 운영 내부 정보다. 외부 공개용 endpoint로 취급하면 안 되고, exposure와 security를 같이 설계해야 한다. 이 부분은 [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)와 연결된다.

### 4. `@ConditionalOnMissingBean` miss면 기존 Bean부터 찾는다

beginner가 가장 자주 헷갈리는 지점이다.

`@ConditionalOnMissingBean` miss는 보통 이런 뜻이다.

- "필요한 Bean이 없어서 실패했다"가 아니다
- "이미 누군가 비슷한 Bean을 만들어서 Boot 기본값이 물러났다"에 가깝다

즉, 질문을 이렇게 바꿔야 한다.

- "`왜 기본 Bean이 안 떴지?`"가 아니라
- "`누가 먼저 같은 역할의 Bean을 올렸지?`"

먼저 볼 곳은 아래 순서면 충분하다.

1. 내 `@Configuration`의 `@Bean`
2. `@TestConfiguration`이나 test slice 전용 설정
3. `@Import`로 끌어온 설정 클래스
4. 다른 starter나 library가 등록한 Bean

핵심은 **Boot 기본값이 빠진 것 자체가 오류인지, 내가 의도한 override인지 먼저 판단하는 것**이다.

### 5. 기존 Bean이 아니라면 네 가지를 확인한다

`@ConditionalOnMissingBean`이 아니라면, 초반엔 아래 네 갈래만 보면 된다.

| 보이는 단서 | 보통 뜻하는 것 | 첫 확인 포인트 |
|---|---|---|
| class 조건 실패 | 필요한 라이브러리/클래스가 없다 | starter, dependency scope, classpath |
| property 조건 실패 | 설정값이 기대와 다르다 | active profile, env var, test property |
| web 조건 실패 | servlet/reactive/none 문맥이 다르다 | `spring.main.web-application-type`, starter 조합 |
| 같은 코드인데 환경별 결과가 다르다 | profile/property/classpath 차이 가능성 | 로컬 vs CI vs 운영 설정 diff |

특히 `@ConditionalOnProperty`면 "`false`인가?"만 보지 말고 **missing / `havingValue` 불일치 / env var key 차이**를 나눠 보는 게 빠르다. 이 부분은 [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)에서 바로 이어진다.

여기까지 보고도 방향이 안 나오면, 그때 advanced report 문서나 startup playbook으로 올라가면 된다.

---

## 3. 가장 흔한 예시: 내가 만든 `ObjectMapper` 때문에 Boot 기본값이 빠진다

Boot 쪽 기본 설정은 흔히 이런 식이다.

```java
@Bean
@ConditionalOnMissingBean
public ObjectMapper objectMapper() {
    return new ObjectMapper();
}
```

그런데 내가 아래처럼 Bean을 올리면:

```java
@Configuration
public class CustomJsonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper().findAndRegisterModules();
    }
}
```

이제 `--debug`나 `conditions`에서 봐야 할 해석은 단순하다.

- `ObjectMapper`가 "없어서" 실패한 것이 아니다
- 이미 사용자 Bean이 있으므로 Boot 기본값이 빠진 것이다
- 즉 현상은 "누락"처럼 보여도 실제 의미는 **override**다

이때 첫 판단 질문은 하나면 충분하다.

**"내가 진짜 전체 `ObjectMapper` 교체를 의도했나?"**

의도했다면 정상이고, 의도하지 않았다면 duplicate 등록 경로를 줄여야 한다.

---

## 4. report를 읽을 때 바로 쓰는 분기표

| report에서 먼저 찾는 신호 | beginner 해석 | 바로 할 일 |
|---|---|---|
| auto-configuration이 positive match | 조건은 통과했다 | 왜 다른 단계에서 bean 사용이 달라졌는지 본다 |
| auto-configuration이 negative match | 조건 중 하나가 false다 | 어떤 조건이 false였는지 적는다 |
| `@ConditionalOnMissingBean` 계열 miss | 기존 Bean이 이미 있다 | 누가 먼저 등록했는지 찾는다 |
| target auto-configuration 이름이 아예 안 보인다 | 보고 있는 대상이 다르거나 startup 범위가 더 크다 | target class 이름 재확인, 필요시 startup playbook으로 이동 |

핵심은 "로그가 많다"가 아니라, **target auto-configuration에 대해 positive인지 negative인지 먼저 갈라 보는 것**이다.

---

## 5. beginner가 자주 하는 오해

### 1. "`@ConditionalOnMissingBean` miss면 에러다"

아니다. 오히려 가장 흔한 정상 패턴이 "사용자 설정이 Boot 기본값을 밀어낸 상태"다.

### 2. "`conditions` endpoint가 편하니 그냥 열어 두자"

안 된다. `conditions`는 내부 구성 힌트를 많이 드러내므로 운영 내부 진단면으로 취급해야 한다.

### 3. "`--debug`를 켰는데 로그가 너무 많아서 못 읽겠다"

그래서 타깃 Bean과 auto-configuration 이름을 먼저 적어 두는 것이다.  
처음엔 report 전체를 읽지 말고 `JacksonAutoConfiguration` 같은 한 클래스만 따라간다.

### 4. "Bean이 안 뜨니 무조건 auto-configuration 문제다"

내 설정 클래스가 scan/import 범위 밖이면 auto-configuration 이전 문제다.  
그럴 때는 component scan 문서나 startup playbook이 더 맞다.

## 꼬리질문

> Q: `--debug`를 켰을 때 가장 먼저 찾을 것은 무엇인가?
> 의도: report 읽기 시작점 확인
> 핵심: 타깃 auto-configuration이 positive/negative match인지다.

> Q: Actuator `conditions`는 언제 특히 유용한가?
> 의도: restart 없이 보는 진단 창구 이해 확인
> 핵심: 운영 profile이나 재시작이 어려운 환경에서 현재 조건 평가를 보고 싶을 때다.

> Q: `@ConditionalOnMissingBean` miss는 보통 무엇을 뜻하는가?
> 의도: missing-bean 조건의 실제 의미 확인
> 핵심: 이미 같은 역할의 Bean이 있어서 Boot 기본값이 물러났다는 뜻인 경우가 많다.

> Q: 기존 Bean도 안 보이는데 자동 구성이 계속 안 맞으면 다음에 무엇을 볼까?
> 의도: 첫 체크리스트 다음 분기 확인
> 핵심: classpath, property, web type, profile 차이를 본다.

## 한 줄 정리

Spring Boot 자동 구성 디버깅의 첫걸음은 "`Bean`이 왜 없지?"가 아니라 "`어떤 조건이 false였지, 그리고 `@ConditionalOnMissingBean`이면 누가 먼저 Bean을 만들었지?`"로 질문을 바꾸는 것이다.
