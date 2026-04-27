# Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이

> 한 줄 요약: `@ConditionalOnProperty`는 "property가 있는가, 값이 기대와 같은가, 없으면 missing을 허용할까"를 순서대로 보므로, missing property와 `false`, 환경별 key/value 차이를 분리해야 bean 누락 원인이 보인다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `@ConditionalOnProperty` 때문에 bean이 빠지는 대표 사례를 `havingValue`, `matchIfMissing`, 환경별 property 차이 기준으로 풀어주는 **beginner troubleshooting primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)

retrieval-anchor-keywords: ConditionalOnProperty pitfalls, @ConditionalOnProperty havingValue, @ConditionalOnProperty matchIfMissing, property missing bean, feature flag bean missing, conditional bean missing because property absent, property missing vs false, property source precedence, application yml override order, profile file override, env var key mismatch, application yml vs environment variable property, command-line property override, test property override, starter bean missing property flag, bean missing in CI because property override, relaxed binding env var cheatsheet, APP_PUSHNOTIFICATION_ENABLED, dashed property env var mismatch, spring conditional bean beginner, havingValue true matchIfMissing true, condition evaluation report ConditionalOnProperty, did not find property, found different value in property, matchIfMissing report example

## 핵심 개념

초보자 기준으로는 용어보다 아래 그림을 먼저 잡으면 된다.

```text
1. 이 key가 지금 Environment에 있는가?
2. 있으면 값이 havingValue 조건을 통과하는가?
3. 없으면 matchIfMissing=true 인가?
```

즉 `@ConditionalOnProperty`는 "boolean default"를 읽는 장치라기보다, **현재 Environment에 들어온 property 문자열을 조건으로 보는 문**이다.

여기서 beginner가 가장 많이 놓치는 기본값은 두 개다.

- `havingValue`를 안 쓰면 기본 규칙은 **"property가 존재하고 값이 `false`가 아니면 match"**다
- `matchIfMissing` 기본값은 `false`라서 **property가 아예 없으면 기본적으로 match하지 않는다**

그래서 bean이 빠질 때는 아래 셋을 따로 봐야 한다.

1. key가 아예 없나?
2. key는 있는데 값이 기대와 다르나?
3. 다른 환경에서 같은 key라고 믿었지만 실제 입력 방식이 달랐나?

---

## 1. 기본값 함정 한 장 요약

예시 조건:

```java
@ConditionalOnProperty(prefix = "app.sms", name = "enabled")
```

아래 표를 먼저 머리에 넣으면 `havingValue`와 `matchIfMissing` 착시를 거의 줄일 수 있다.

| 선언 | property 없음 | `true` | `false` | `foo` | 기억할 포인트 |
|---|---|---|---|---|---|
| `@ConditionalOnProperty(name = "enabled")` | no | yes | no | yes | 기본값은 "`false`만 아니면 통과"다 |
| `@ConditionalOnProperty(name = "enabled", havingValue = "true")` | no | yes | no | no | `true`를 명시해야만 통과한다 |
| `@ConditionalOnProperty(name = "enabled", havingValue = "true", matchIfMissing = true)` | yes | yes | no | no | missing만 허용할 뿐, 잘못된 값까지 허용하지는 않는다 |

핵심은 이것이다.

- `havingValue = "true"`는 **엄격 비교**
- `matchIfMissing = true`는 **missing일 때만 예외 허용**
- 둘을 헷갈리면 "왜 local에서는 되고 prod에서는 bean이 없지?"가 반복된다

---

## 2. 대표 사례 1: `havingValue = "true"`인데 운영에서 bean이 빠진다

```java
@Configuration
public class SmsConfig {

    @Bean
    @ConditionalOnProperty(
            prefix = "app.sms",
            name = "enabled",
            havingValue = "true"
    )
    public SmsSender smsSender() {
        return new SmsSender();
    }
}
```

local에서는 아래처럼 잘 된다.

```yaml
app:
  sms:
    enabled: true
```

그런데 prod에서 `APP_SMS_ENABLED`를 아예 주지 않으면 `SmsSender` bean은 빠진다.

왜냐하면 이 조건은 아래 순서로 읽히기 때문이다.

1. `app.sms.enabled`가 있는가?
2. 있으면 값이 `"true"`인가?
3. 없으면 `matchIfMissing`을 보는데, 기본값이 `false`라서 탈락한다

즉 beginner가 자주 하는 착각은 이것이다.

```text
havingValue = "true"니까 property가 없으면 기본 true로 보겠지
```

아니다. `havingValue`는 **"있을 때 어떤 값이어야 하냐"**를 말할 뿐이고, missing 기본값을 바꾸지 않는다.

---

## 3. 대표 사례 2: `matchIfMissing = true`인데도 bean이 빠진다

이번에는 조건이 이렇게 바뀌었다고 하자.

```java
@ConditionalOnProperty(
        prefix = "app.sms",
        name = "enabled",
        havingValue = "true",
        matchIfMissing = true
)
```

이 설정은 흔히 "기본 on"처럼 쓰인다.
하지만 아래 둘은 결과가 다르다.

| 실제 입력 | 결과 | 이유 |
|---|---|---|
| property 없음 | bean 생성 | missing을 허용했기 때문이다 |
| `app.sms.enabled=false` | bean 없음 | property가 **존재**하므로 `matchIfMissing`이 아니라 값 비교가 적용된다 |

즉 `matchIfMissing = true`는 아래 뜻이다.

```text
없으면 일단 통과시켜라
```

아래 뜻이 아니다.

```text
false나 오타 값도 그냥 통과시켜라
```

그래서 test/CI에서 누군가 아래처럼 명시적으로 꺼 버리면 bean은 빠진다.

```properties
app.sms.enabled=false
```

이 경우는 "property가 없어서 빠진 것"이 아니라 **property가 존재하고 값이 조건과 달라서 빠진 것**이다.

---

## 4. 대표 사례 3: 환경별 property 이름이 달라서 사실상 missing이 된다

local 파일에서는 아래 key를 쓸 수 있다.

```properties
app.push-notification.enabled=true
```

하지만 environment variable로 넘길 때는 이름이 그대로 유지되지 않는다.
Spring Boot relaxed binding 기준으로 beginner가 먼저 기억할 규칙은 이 정도면 충분하다.

- `.`은 `_`로 바뀐다
- `-`는 제거된다
- 전체를 대문자로 쓴다

즉 위 key는 보통 이렇게 넘어간다.

```text
APP_PUSHNOTIFICATION_ENABLED=true
```

list index나 map key까지 섞인 변환표가 필요하면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)를 먼저 확인한다.

여기서 운영 환경에서 아래처럼 직관적으로 넣으면:

```text
APP_PUSH_NOTIFICATION_ENABLED=true
```

Spring이 기대한 key와 달라져서 실제로는 property가 없는 것처럼 보일 수 있다.
그러면 `matchIfMissing = false`인 조건에서는 bean이 빠진다.

자주 보는 착시는 이것이다.

| 내가 믿는 상황 | 실제 상황 |
|---|---|
| "운영에도 같은 flag를 넣었다" | env var 이름이 달라서 다른 key로 들어갔다 |
| "local 파일에서 true였으니 prod도 true일 것" | prod env var / profile file / command-line arg가 다른 값을 덮어썼다 |

즉 환경별 property 차이는 단순히 값만 다른 게 아니라, **key 표기법과 우선순위도 다를 수 있다**.

---

## 5. ConditionEvaluationReport에서 바로 읽는 짧은 스니펫

초보자는 report 전체를 해석하려 하지 말고, 아래처럼 **"missing인가, false/value mismatch인가, matchIfMissing 허용인가"**만 먼저 읽으면 된다.

예시 조건은 이것으로 통일하자.

```java
@ConditionalOnProperty(
        prefix = "app.sms",
        name = "enabled",
        havingValue = "true"
)
```

### 1. key가 아예 없을 때: negative

```text
SmsConfig#smsSender:
   Did not match:
      - @ConditionalOnProperty (app.sms.enabled=true) did not find property 'enabled'
```

이 스니펫은 한 줄로 이렇게 읽으면 된다.

- `did not find property`면 **값 비교까지 못 갔다**
- 즉 원인은 `false`가 아니라 **missing key**다

### 2. key는 있지만 `false`일 때: negative

```text
SmsConfig#smsSender:
   Did not match:
      - @ConditionalOnProperty (app.sms.enabled=true) found different value in property 'enabled'
```

이 경우는 아래처럼 해석한다.

- key는 들어왔다
- 하지만 값이 `havingValue = "true"`와 달랐다
- 즉 원인은 **missing이 아니라 false/value mismatch**다

### 3. `matchIfMissing = true`일 때 key가 없으면: positive

조건을 아래처럼 바꿨다고 하자.

```java
@ConditionalOnProperty(
        prefix = "app.sms",
        name = "enabled",
        havingValue = "true",
        matchIfMissing = true
)
```

그러면 report는 보통 이런 방향으로 읽힌다.

```text
SmsConfig#smsSender:
   Matched:
      - @ConditionalOnProperty (app.sms.enabled=true) matched because property 'enabled' was missing and matchIfMissing=true
```

핵심은 이것이다.

- `matchIfMissing=true`는 **missing일 때만 positive**
- 같은 조건이어도 `app.sms.enabled=false`가 실제로 들어오면 다시 negative가 된다

즉 report 한 줄만 봐도 아래 셋을 바로 나눌 수 있다.

| report 표현 | 먼저 붙일 라벨 |
|---|---|
| `did not find property` | key missing |
| `found different value` | key present but wrong value |
| `matched because ... missing and matchIfMissing=true` | missing 허용으로 생성됨 |

실제 문구는 Boot 버전마다 조금 달라질 수 있지만, 초보자 관점에서는 **"property를 못 찾았는가 / 찾았지만 값이 달랐는가 / missing을 예외 허용했는가"**만 읽어도 첫 판단이 된다.

조건 report를 어디서 여는지부터 헷갈리면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)를 먼저 같이 본다.

---

## 6. 로컬에서는 되는데 test/CI/prod에서만 bean이 빠질 때 30초 체크리스트

1. annotation에 `havingValue`, `matchIfMissing`가 실제로 어떻게 적혀 있는지 본다.
2. full key를 한 줄로 적는다.
   예: `app.sms.enabled`
3. 환경마다 실제 입력 소스를 분리해서 본다.
   예: `application.yml`, `application-prod.yml`, env var, command-line arg, test property
4. 현재 증상을 셋 중 하나로 라벨링한다.
   - key missing
   - key present but wrong value
   - key naming / override mismatch
5. `--debug` 또는 Actuator `conditions`에서 negative match 이유를 본다.

이 순서로 보면 "`property가 false인가?`"만 보다가 시간을 쓰지 않고, **missing / 값 불일치 / 환경 입력 차이**를 바로 나눌 수 있다.

---

## 흔한 오해

### 1. `havingValue = "true"`면 property가 없어도 기본 true다

아니다. missing을 바꾸는 스위치는 `matchIfMissing`이다.

### 2. `matchIfMissing = true`면 `false`도 허용된다

아니다. property가 존재하면 값 비교가 우선이다.

### 3. `application.yml` key를 env var로 바꿀 때 underscore만 넣으면 된다

항상 그렇지 않다. dashed key는 env var에서 `-`가 사라질 수 있다.

### 4. local 파일에 `true`가 있으니 다른 환경도 같을 것이다

그렇지 않다. profile file, env var, command-line arg, test property가 더 높은 우선순위로 덮어쓸 수 있다.

---

## 다음에 바로 이어서 볼 문서

- 같은 key가 파일/profile/env var/command-line/test property 중 어디에서 최종 값이 됐는지 먼저 가르고 싶으면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)로 간다.
- dotted/dashed/list/map key를 env var 이름으로 바꾸는 변환표가 먼저 필요하면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)로 간다.
- 조건이 실제로 왜 탈락했는지 runtime 증거부터 보고 싶으면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 간다.
- report 문구 구조를 더 깊게 보고 싶으면 [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)로 이어진다.
- starter bean 누락을 property/classpath/back-off/scan boundary까지 같이 가르고 싶으면 [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)로 이어진다.
- 지금 증상이 `NoSuchBeanDefinitionException`로만 보인다면 [Spring DI 예외 빠른 판별: `NoSuchBeanDefinitionException` vs `NoUniqueBeanDefinitionException`](./spring-di-exception-quick-triage.md)에서 scan 누락과 conditional 탈락을 먼저 분리한다.
