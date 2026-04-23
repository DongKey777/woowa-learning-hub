# Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property

> 한 줄 요약: 같은 key가 여러 곳에 있으면 Spring Boot `Environment`에서는 더 높은 `PropertySource`의 값 하나만 보인다. beginner 기준으로는 **test property > command-line > env var > profile 파일 > 기본 `application.yml`** 순서부터 잡으면 대부분의 "왜 이 설정이 먹지?"를 빠르게 가를 수 있다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `application.yml`, profile 파일, 환경 변수, command-line argument, 테스트 property가 같은 key를 어떻게 덮어쓰는지 한 장 표와 작은 사례로 정리하는 **beginner troubleshooting primer**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
> - [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트: `--debug`, Actuator `conditions`, `@ConditionalOnMissingBean`](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

retrieval-anchor-keywords: spring property source precedence, spring property source priority, spring boot externalized configuration beginner, application.yml override order, application-prod.yml precedence, profile file override application yml, multiple profile last wins, spring.profiles.active order, environment variable overrides yaml, command line args override env var, test property override, @SpringBootTest properties precedence, @TestPropertySource precedence, DynamicPropertySource precedence, why application.yml ignored, same key property override, relaxed binding env var cheatsheet, env var property key mapping, dashed property env var, list property env var, map property env var, property source 우선순위, application yml 덮어쓰기, profile 설정 덮어쓰기, env var 설정 우선순위, command-line property 우선순위, test property 우선순위, 설정값이 왜 다르게 들어오지

## 핵심 개념

초보자 기준으로는 `PropertySource`, `ConfigData`, `Environment` 같은 용어보다 아래 mental model을 먼저 잡으면 된다.

```text
같은 key를 적은 투명 필름 여러 장을 위로 겹친다.
Spring은 가장 위에 보이는 값 하나를 읽는다.
아래쪽 값은 사라진 게 아니라, 더 높은 값에 가려진 것이다.
```

예를 들어 `app.message`가 네 곳에 있으면 Spring은 값을 네 개 합치지 않는다.  
현재 실행에서 가장 높은 source의 `app.message` 하나만 보인다.

그래서 설정 문제를 볼 때 질문은 이것이다.

```text
"이 key가 어디에 있지?"보다
"이 key를 가진 source 중 지금 가장 높은 source가 무엇이지?"
```

이 문서는 beginner가 자주 만나는 다섯 가지 source만 다룬다.

- 기본 `application.yml`
- profile 파일: `application-local.yml`, `application-prod.yml`
- 환경 변수: `APP_MESSAGE=...`
- command-line argument: `--app.message=...`
- test property: `@SpringBootTest(properties = ...)`, `@TestPropertySource`, `@DynamicPropertySource`

Java system property, `SPRING_APPLICATION_JSON`, devtools global settings, config server 같은 확장 source는 여기서 중심으로 다루지 않는다.

---

## 1. 한 장 표: 일반 실행에서 누가 이기나

테스트가 아닌 일반 애플리케이션 실행에서는 먼저 이 표를 외우면 된다.

| 우선순위 | source | 예시 | 같은 key가 있으면 |
|---|---|---|---|
| 높음 | command-line argument | `java -jar app.jar --app.message=cli` | env var와 파일 값을 덮어쓴다 |
| 중간 | 환경 변수 | `APP_MESSAGE=env` | profile/base 파일 값을 덮어쓴다 |
| 중간 | active profile 파일 | `application-prod.yml` | 기본 `application.yml`을 덮어쓴다 |
| 낮음 | 기본 config 파일 | `application.yml` | 기본값 역할을 한다 |

핵심은 "나중에 만든 파일"이 이기는 게 아니라 **Spring Boot가 정한 source 우선순위**가 이긴다는 점이다.

예를 들어 아래 파일이 있다고 하자.

```yaml
# application.yml
app:
  message: base
```

```yaml
# application-prod.yml
app:
  message: profile
```

실행별 결과는 이렇게 달라진다.

| 실행 상황 | 최종 `app.message` | 이유 |
|---|---|---|
| profile 없음 | `base` | 기본 파일만 있다 |
| `prod` profile 활성화 | `profile` | profile 파일이 기본 파일보다 높다 |
| `prod` profile + `APP_MESSAGE=env` | `env` | env var가 profile 파일보다 높다 |
| `prod` profile + `APP_MESSAGE=env` + `--app.message=cli` | `cli` | command-line이 일반 실행에서 가장 높다 |

즉 `application-prod.yml`에 값이 있어도 운영 환경 변수나 command-line argument가 같은 key를 주면 profile 값은 가려진다.

---

## 2. 테스트에서는 test property가 더 위에 올라온다

테스트에서는 test annotation이 만든 property source가 일반 실행 source보다 위에 놓인다.

대표 순서만 압축하면 아래와 같다.

| 우선순위 | source | 예시 | 기억할 점 |
|---|---|---|---|
| 높음 | `@TestPropertySource` | `@TestPropertySource(properties = "app.message=test-source")` | 테스트에서 가장 명시적인 override로 보는 편이 쉽다 |
| 높음 | `@DynamicPropertySource` | Testcontainers port를 런타임에 주입 | 동적으로 계산한 테스트 값 |
| 높음 | test annotation `properties` | `@SpringBootTest(properties = "app.message=test")` | `@WebMvcTest(properties = ...)` 같은 slice test도 포함 |
| 중간 | command-line argument | `--app.message=cli` | test property가 있으면 가려질 수 있다 |
| 중간 | 환경 변수 | `APP_MESSAGE=env` | test property/command-line보다 낮다 |
| 낮음 | profile 파일 | `application-test.yml` | active profile일 때만 기본 파일을 덮는다 |
| 낮음 | 기본 config 파일 | `application.yml` | 테스트에서도 기본값 역할을 한다 |

예를 들어:

```java
@SpringBootTest(properties = "app.message=test")
class MessageTest {
}
```

그리고 파일과 환경이 아래처럼 있어도:

```yaml
# application.yml
app:
  message: base
```

```yaml
# application-test.yml
app:
  message: profile
```

```text
APP_MESSAGE=env
```

테스트 안에서 `app.message`는 보통 `test`다.  
테스트 annotation의 property가 env var와 config 파일보다 위에 있기 때문이다.

그래서 beginner가 자주 겪는 착시는 이것이다.

```text
"운영에서는 env var가 이기니까 테스트에서도 env var가 이기겠지"
```

아니다. 테스트에서는 테스트용 property가 더 높은 source로 들어올 수 있다.

---

## 3. profile 파일은 "profile이 켜졌을 때만" 후보가 된다

`application-prod.yml`은 파일명이 prod라고 해서 항상 읽히는 override가 아니다.  
`prod` profile이 active일 때만 의미가 있다.

```yaml
# application.yml
spring:
  profiles:
    active: local

app:
  cache:
    enabled: false
```

```yaml
# application-prod.yml
app:
  cache:
    enabled: true
```

이 상태에서 active profile이 `local`이면 `application-prod.yml`의 `app.cache.enabled=true`는 후보가 아니다.  
최종 값은 기본 파일의 `false` 쪽으로 남을 수 있다.

반대로 command-line으로 profile을 바꾸면:

```text
java -jar app.jar --spring.profiles.active=prod
```

`application-prod.yml`이 로드되어 `app.cache.enabled=true`가 기본 파일을 덮는다.

주의할 점은 두 단계가 분리된다는 것이다.

1. 어떤 profile이 active인지 결정한다.
2. 그 profile 파일 안의 key가 기본 파일 key를 덮는다.

즉 "prod 파일에 값이 있다"와 "지금 prod 파일이 적용됐다"는 같은 말이 아니다.

여러 profile을 한 번에 켜면 profile 파일끼리도 순서가 생긴다.

```text
java -jar app.jar --spring.profiles.active=prod,blue
```

이 경우 같은 key가 `application-prod.yml`과 `application-blue.yml`에 모두 있으면 뒤쪽 profile인 `blue` 쪽 값이 더 위에 있다고 보면 된다.  
beginner 단계에서는 "active profile 목록에서 오른쪽에 있는 profile이 같은 key를 더 나중에 덮을 수 있다" 정도만 기억하면 충분하다.

---

## 4. env var는 key 이름이 맞아야 같은 key로 덮는다

환경 변수는 운영/CI에서 자주 쓰지만, key 표기법 때문에 "넣었는데 안 먹는" 일이 많다.

가장 단순한 규칙은 이렇게 잡는다.

| Spring key | 환경 변수 예시 |
|---|---|
| `app.message` | `APP_MESSAGE` |
| `server.port` | `SERVER_PORT` |
| `spring.profiles.active` | `SPRING_PROFILES_ACTIVE` |
| `app.payment-timeout` | `APP_PAYMENTTIMEOUT` |

기본 감각은 이렇다.

- `.`은 `_`로 바꾼다
- `-`는 보통 제거한다
- 대문자로 쓴다

list index, map key, dashed segment가 섞인 이름은 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)에서 먼저 변환표로 확인한다. dashed key가 많으면 감으로 이름을 만들지 말고, 실제 실행 환경에서 `Environment`나 `/actuator/env`로 들어온 key/value를 확인하는 편이 빠르다.

또 하나의 beginner 함정은 `.env` 파일이다.

```text
.env 파일에 적었다
= Spring Boot가 자동으로 읽었다
```

이 등식은 기본적으로 성립하지 않는다. Docker Compose, IDE run configuration, 배포 플랫폼이 `.env`를 process environment로 주입해 줘야 Spring Boot의 환경 변수 source에 올라온다.

---

## 5. command-line은 `--key=value` 형태가 property다

Spring Boot에서 command-line property는 보통 아래처럼 넘긴다.

```text
java -jar app.jar --app.message=cli --server.port=9090
```

이 값은 일반 실행에서 파일/env var보다 높다.

아래처럼 값이 다 있으면:

```yaml
# application.yml
app:
  message: base
```

```text
APP_MESSAGE=env
java -jar app.jar --app.message=cli
```

최종 값은 `cli`다.

다만 모든 command-line 문자열이 property가 되는 것은 아니다.  
Spring Boot가 property로 올리는 것은 `--app.message=cli` 같은 option argument다.

```text
java -jar app.jar cli
```

이런 positional argument는 같은 방식으로 `app.message`를 덮지 않는다.

---

## 6. 실전 사례: "local은 되는데 CI에서만 꺼진다"

기능 flag가 있다고 하자.

```yaml
# application.yml
app:
  sms:
    enabled: false
```

```yaml
# application-local.yml
app:
  sms:
    enabled: true
```

로컬에서는:

```text
java -jar app.jar --spring.profiles.active=local
```

최종 값은 `true`다.  
`application-local.yml`이 기본 `application.yml`을 덮었기 때문이다.

그런데 CI에서 이렇게 실행된다면:

```text
APP_SMS_ENABLED=false
java -jar app.jar --spring.profiles.active=local
```

최종 값은 `false`다.  
환경 변수가 profile 파일보다 높아서 `application-local.yml`의 `true`를 덮기 때문이다.

여기에 command-line까지 붙으면:

```text
APP_SMS_ENABLED=false
java -jar app.jar --spring.profiles.active=local --app.sms.enabled=true
```

최종 값은 다시 `true`다.  
command-line argument가 env var보다 높기 때문이다.

이제 `@ConditionalOnProperty(prefix = "app.sms", name = "enabled", havingValue = "true")` bean이 뜨거나 빠지는 이유도 같이 보인다.

- 최종 값이 `true`면 조건 통과
- 최종 값이 `false`면 조건 탈락
- key가 아예 없으면 `matchIfMissing` 기본값 때문에 보통 탈락

조건 자체의 `havingValue`, `matchIfMissing` 함정은 [Spring `@ConditionalOnProperty` 기본값 함정](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)에서 이어서 보면 된다.

---

## 7. 30초 판별 순서

설정값이 예상과 다르면 아래 순서로만 본다.

1. **canonical key를 한 줄로 적는다.**
   예: `app.sms.enabled`
2. **지금 active profile을 확인한다.**
   예: `local`, `test`, `prod`
3. **높은 source부터 같은 key가 있는지 찾는다.**
   테스트라면 test property부터, 일반 실행이라면 command-line부터 본다.
4. **가장 높은 source의 값을 최종 값으로 적는다.**
   아래 source 값은 가려진 값으로 표시한다.
5. **그 최종 값이 사용하는 곳과 맞는지 본다.**
   `@ConfigurationProperties` 바인딩인지, `@Value`인지, `@ConditionalOnProperty` 조건인지 분리한다.

메모 형태로 쓰면 이렇게 된다.

| source | 값 | 판정 |
|---|---|---|
| command-line | `--app.sms.enabled=true` | 최종 값 |
| env var | `APP_SMS_ENABLED=false` | command-line에 가려짐 |
| `application-local.yml` | `true` | command-line/env var에 가려짐 |
| `application.yml` | `false` | profile 파일에 가려짐 |

이 표를 만들면 "파일에는 true인데 왜 false지?"가 아니라 "더 높은 source에 false가 있나?"로 바로 바뀐다.

---

## 흔한 오해

### 1. `application-prod.yml`은 prod 파일이니까 항상 기본 파일보다 이긴다

아니다. `prod` profile이 active일 때만 후보가 된다.

### 2. `application.yml`에 있는 값은 env var가 없을 때만 쓴다

대체로 맞지만, profile 파일이 active이면 profile 파일도 기본 파일보다 높다.  
즉 `application.yml`은 가장 먼저 깔리는 기본값에 가깝다.

### 3. env var를 넣었으니 profile 파일 값은 절대 못 쓴다

같은 key라면 env var가 이긴다.  
하지만 env var 이름이 다른 key로 들어갔거나, profile 파일 key와 canonical key가 다르면 덮어쓰지 못한다.

### 4. 테스트에서 운영과 같은 property 우선순위가 적용된다

아니다. 테스트 annotation이 만든 property source는 일반 실행 source보다 위에 올라올 수 있다.

### 5. command-line으로 profile만 바꾸면 모든 값이 command-line 값이 된다

아니다. `--spring.profiles.active=prod`는 active profile을 바꾸는 값이고, `app.*` key 자체를 전부 command-line으로 바꾸는 것은 아니다.

---

## 다음에 바로 이어서 볼 문서

- 같은 key의 최종 값 때문에 conditional bean이 빠졌다면 [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)로 간다.
- 자동 구성 bean이 property 조건에서 왜 탈락했는지 runtime 증거를 보고 싶으면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 이어진다.
- 설정값을 객체로 묶는 바인딩 흐름이 궁금하면 [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)에서 `Binder`, relaxed binding, validation을 이어서 본다.

## 한 줄 정리

Spring 설정 우선순위는 "파일에 무엇이 적혔나"보다 "같은 key를 가진 source 중 어떤 source가 가장 위에 있나"로 판별한다.
