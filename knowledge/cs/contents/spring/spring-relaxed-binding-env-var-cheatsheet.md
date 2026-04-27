# Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기

> 한 줄 요약: Spring Boot 환경 변수 이름은 "property key를 대문자 underscore 이름으로 옮긴 것"이지만, `.`은 `_`로 바꾸고 `-`는 제거한다. list index는 `_0_`처럼 감싸고, map key는 단순 소문자 key부터 안전하게 시작한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `application.yml`의 dotted/dashed/list/map key를 운영/CI 환경 변수 이름으로 바꾸는 방법을 beginner가 바로 확인하는 **relaxed binding env var cheatsheet**를 담당한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Spring `@Value` vs `@ConfigurationProperties` Env Guide](./spring-value-vs-configurationproperties-env-guide.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring Docker Compose and Kubernetes Env Injection Basics: property 이름과 플랫폼 주입 실수 분리하기](./spring-docker-compose-k8s-env-injection-basics-primer.md)
> - [Spring `SPRING_APPLICATION_JSON` Primer: plain env var보다 나은 순간](./spring-spring-application-json-primer.md)
> - [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)
> - [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ: classpath 조건, property, override, scan boundary](./spring-starter-added-but-bean-missing-faq.md)
> - 공식 기준: [Spring Boot Externalized Configuration - Binding From Environment Variables](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.relaxed-binding.environment-variables)

retrieval-anchor-keywords: spring relaxed binding env var cheatsheet, relaxed binding environment variables, Spring Boot env var mapping, property key to environment variable, dotted property env var, dashed property env var, list property env var, map property env var, dotted dashed list map beginner, kebab case env var spring boot, property path segment env var, environment variable key mismatch, env var mismatch bean missing, app push notification env var, APP_PUSHNOTIFICATION_ENABLED, APP_CLIENTS_0_BASEURL, APP_TENANTS_ADMIN_BASEURL, MY_SERVICE_0_OTHER, SPRING_MAIN_LOGSTARTUPINFO, SPRING_APPLICATION_JSON, spring application json primer, @ConfigurationProperties env var binding, ConditionalOnProperty env var mismatch, beginner property configuration primer

## 핵심 개념

초보자 기준으로는 "환경 변수 이름은 다른 언어"라고 생각하면 편하다.

```text
application.yml / properties에서 쓰는 이름:
app.push-notification.enabled

운영/CI 환경 변수에서 쓰는 이름:
APP_PUSHNOTIFICATION_ENABLED
```

Spring Boot는 `Environment`와 `@ConfigurationProperties` 바인딩에서 이 둘을 맞춰 주는 relaxed binding 규칙을 쓴다.
하지만 relaxed라고 해서 아무 이름이나 같은 key로 보는 것은 아니다.

먼저 이 세 줄만 외운다.

```text
1. 점(.)은 underscore(_)로 바꾼다.
2. dash(-)는 underscore로 바꾸지 말고 제거한다.
3. 전체를 대문자로 쓴다.
```

## 네 가지 모양 먼저 보기

beginner는 key의 "모양"부터 보면 훨씬 덜 헷갈린다.

- `.`은 path를 나누는 경계다
- `-`는 같은 segment 안 철자다
- list index는 숫자 segment다
- map key는 사용자 정의 segment다

| 모양 | property key | 맞는 env var | 흔한 오답 | mental model |
|---|---|---|---|---|
| dotted | `server.port` | `SERVER_PORT` | `SERVERPORT` | `.`만 path 경계라 `_` 하나가 생긴다 |
| dashed | `app.push-notification.enabled` | `APP_PUSHNOTIFICATION_ENABLED` | `APP_PUSH_NOTIFICATION_ENABLED` | `push-notification`은 한 segment라 dash만 지운다 |
| list | `app.clients[0].base-url` | `APP_CLIENTS_0_BASEURL` | `APP_CLIENTS0_BASE_URL` | index는 `_0_`, dash는 제거한다 |
| map | `app.tenants.admin.base-url` | `APP_TENANTS_ADMIN_BASEURL` | `APP_TENANTS_ADMIN_BASE_URL` | 단순 map key `admin`이 한 segment로 들어간다 |

path를 먼저 쪼개서 보면 왜 오답이 틀렸는지 더 빨리 보인다.

```text
app.push-notification.enabled
= app / push-notification / enabled

APP_PUSHNOTIFICATION_ENABLED
= APP / PUSHNOTIFICATION / ENABLED

APP_PUSH_NOTIFICATION_ENABLED
= APP / PUSH / NOTIFICATION / ENABLED   # 다른 path처럼 보일 수 있음
```

그래서 가장 중요한 차이는 아래다.

| 원하는 Spring key | 맞는 env var | 헷갈리기 쉬운 env var |
|---|---|---|
| `spring.main.log-startup-info` | `SPRING_MAIN_LOGSTARTUPINFO` | `SPRING_MAIN_LOG_STARTUP_INFO` |
| `app.push-notification.enabled` | `APP_PUSHNOTIFICATION_ENABLED` | `APP_PUSH_NOTIFICATION_ENABLED` |

dash를 `_`로 바꾸면 단어가 하나 더 깊은 path처럼 보일 수 있다.
이 때문에 운영에 값을 넣었는데도 `@ConditionalOnProperty`가 missing으로 탈락하는 일이 생긴다.

---

## 1. 기본 변환 규칙

| property key | env var | 왜 이렇게 되나 |
|---|---|---|
| `server.port` | `SERVER_PORT` | `.` -> `_`, 대문자 |
| `spring.profiles.active` | `SPRING_PROFILES_ACTIVE` | path 구분자만 `_`로 변경 |
| `app.message` | `APP_MESSAGE` | 가장 단순한 dotted key |
| `app.payment-timeout` | `APP_PAYMENTTIMEOUT` | `-` 제거 |
| `app.oauth.client-id` | `APP_OAUTH_CLIENTID` | `.`은 `_`, `-`는 제거 |
| `my.main-project.person.first-name` | `MY_MAINPROJECT_PERSON_FIRSTNAME` | dashed segment마다 dash 제거 |

beginner가 실수하는 지점은 거의 항상 dashed key다.

```text
app.payment-timeout
```

위 key는 아래처럼 바뀐다.

```text
APP_PAYMENTTIMEOUT
```

아래처럼 쓰는 것은 다른 path로 해석될 수 있다.

```text
APP_PAYMENT_TIMEOUT
```

즉 "kebab-case 단어를 underscore 단어로 옮긴다"가 아니라, **canonical property key에서 dash만 지운다**고 기억하는 편이 안전하다.

---

## 2. `@ConditionalOnProperty` feature flag 예시

local 파일에서는 흔히 이렇게 쓴다.

```yaml
app:
  sms:
    enabled: true
```

조건은 이렇게 생겼다고 하자.

```java
@ConditionalOnProperty(
        prefix = "app.sms",
        name = "enabled",
        havingValue = "true"
)
```

운영 환경 변수는 아래가 맞다.

```text
APP_SMS_ENABLED=true
```

이번에는 dashed key가 들어간다.

```yaml
app:
  push-notification:
    enabled: true
```

조건이 아래라면:

```java
@ConditionalOnProperty(
        prefix = "app.push-notification",
        name = "enabled",
        havingValue = "true"
)
```

운영 환경 변수는 아래처럼 쓴다.

```text
APP_PUSHNOTIFICATION_ENABLED=true
```

아래는 직관적이지만 위험하다.

```text
APP_PUSH_NOTIFICATION_ENABLED=true
```

Spring이 찾는 key가 `app.push-notification.enabled`인데 env var가 `app.push.notification.enabled` 쪽으로 들어오면, 조건 입장에서는 property가 없는 것처럼 보일 수 있다.

---

## 3. list key는 index를 underscore로 감싼다

YAML list는 flattened key로 보면 index가 들어간 property다.

```yaml
app:
  clients:
    - name: payment
      base-url: https://pay.example.com
    - name: order
      base-url: https://order.example.com
```

flat key는 대략 이렇게 생각할 수 있다.

```text
app.clients[0].name
app.clients[0].base-url
app.clients[1].name
app.clients[1].base-url
```

환경 변수에서는 list index를 `_0_`, `_1_`처럼 감싼다.

| property key | env var |
|---|---|
| `app.clients[0].name` | `APP_CLIENTS_0_NAME` |
| `app.clients[0].base-url` | `APP_CLIENTS_0_BASEURL` |
| `app.clients[1].name` | `APP_CLIENTS_1_NAME` |
| `app.clients[1].base-url` | `APP_CLIENTS_1_BASEURL` |

기억할 포인트는 두 개다.

- `[0]`은 `_0_`가 된다
- `base-url`의 dash는 여전히 제거되어 `BASEURL`이 된다

그래서 아래 둘은 다르다.

```text
APP_CLIENTS_0_BASEURL     # app.clients[0].base-url
APP_CLIENTS_0_BASE_URL    # app.clients[0].base.url 쪽으로 보일 수 있음
```

---

## 4. map key는 단순 key부터 안전하게 시작한다

map은 beginner 단계에서 더 조심해야 한다.
환경 변수 이름은 보통 대문자와 underscore로만 쓰기 때문에, map key의 원래 대소문자나 특수문자를 보존하기 어렵다.

아래처럼 단순한 key부터 시작하면 안전하다.

```java
@ConfigurationProperties("app")
public record AppProperties(
        Map<String, ClientProperties> tenants
) {
}
```

```yaml
app:
  tenants:
    admin:
      base-url: https://admin.example.com
    user:
      base-url: https://user.example.com
```

환경 변수는 이렇게 잡는다.

| property key | env var | bound map key |
|---|---|---|
| `app.tenants.admin.base-url` | `APP_TENANTS_ADMIN_BASEURL` | `admin` |
| `app.tenants.user.base-url` | `APP_TENANTS_USER_BASEURL` | `user` |

단순 `Map<String, String>`도 마찬가지다.

```java
@ConfigurationProperties("app")
public record AppProperties(
        Map<String, String> labels
) {
}
```

```text
APP_LABELS_REGION=ap-northeast-2
APP_LABELS_TIER=prod
```

바인딩 결과는 이런 느낌이다.

```text
labels["region"] = "ap-northeast-2"
labels["tier"] = "prod"
```

주의할 점은 env var 이름이 바인딩 과정에서 lower-case로 처리된다는 것이다.
값은 그대로지만, map key는 보통 소문자로 본다.

```text
APP_LABELS_REGION=SEOUL
```

이 경우 key는 `region`, value는 `SEOUL`이다.

---

## 5. map key에 대문자, slash, dot, 특수문자가 필요하면

아래 같은 map key를 env var 하나로 보존하려고 하면 초보자에게는 위험하다.

```text
X-Trace-Id
/internal/**
tenant.alpha
```

이런 key는 환경 변수 이름으로 옮기면서 대소문자, dash, slash, dot 의미가 깨지기 쉽다.

그럴 때는 보통 env var 이름 변환으로 버티기보다 아래 중 하나를 고른다.

- `application.yml`에서 bracket notation을 쓴다
- [`SPRING_APPLICATION_JSON`](./spring-spring-application-json-primer.md)처럼 구조를 보존하는 source를 쓴다
- Kubernetes ConfigMap/Secret file, config tree처럼 key를 파일명/내용으로 분리한다

이 문서는 beginner cheatsheet라서 복잡한 map key 보존 규칙을 깊게 다루지 않는다.
실제 바인딩 파이프라인과 map bracket notation은 [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)에서 이어서 본다.

---

## 6. 30초 변환 연습

| 내가 가진 key | 머릿속 변환 | 최종 env var |
|---|---|---|
| `app.cache.enabled` | `.`만 `_` | `APP_CACHE_ENABLED` |
| `app.cache.ttl-seconds` | `.` -> `_`, `-` 제거 | `APP_CACHE_TTLSECONDS` |
| `management.endpoints.web.exposure.include` | `.` -> `_` | `MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE` |
| `spring.main.lazy-initialization` | `.` -> `_`, `-` 제거 | `SPRING_MAIN_LAZYINITIALIZATION` |
| `app.servers[0].host-name` | `[0]` -> `_0_`, `-` 제거 | `APP_SERVERS_0_HOSTNAME` |
| `app.routes.admin.timeout-ms` | map key `admin`, `-` 제거 | `APP_ROUTES_ADMIN_TIMEOUTMS` |

눈으로 변환할 때는 아래 순서가 제일 덜 헷갈린다.

1. 먼저 full property key를 한 줄로 쓴다.
2. `.`을 `_`로 바꾼다.
3. `[0]`, `[1]` 같은 index를 `_0_`, `_1_`로 바꾼다.
4. `-`를 제거한다.
5. 전체를 대문자로 바꾼다.

---

## 흔한 오해

### 1. dash는 underscore로 바꾸면 된다

아니다. env var 변환에서는 dash를 제거한다.

```text
spring.main.log-startup-info -> SPRING_MAIN_LOGSTARTUPINFO
```

### 2. `_0_` 대신 `0`만 붙여도 list로 잡힌다

그렇게 기대하지 않는 편이 안전하다. list index는 underscore로 감싸서 segment로 드러낸다.

```text
app.clients[0].name -> APP_CLIENTS_0_NAME
```

### 3. map key의 대소문자는 env var에서 그대로 보존된다

아니다. env var 이름은 바인딩 중 lower-case로 처리될 수 있다. key 대소문자가 의미라면 env var 단일 이름보다 구조를 보존하는 설정 source를 검토한다.

### 4. `.env` 파일에 쓰면 Spring Boot가 자동으로 읽는다

기본적으로 아니다. Docker Compose, IDE, 배포 플랫폼이 `.env` 내용을 process environment로 주입해 줘야 Spring Boot의 환경 변수 source에 올라온다.

### 5. `System.getenv("APP_CACHE_ENABLED")`도 relaxed binding이다

아니다. relaxed binding은 Spring Boot의 `Environment`/Binder 쪽 규칙이다. 직접 `System.getenv(...)`를 호출하면 OS 환경 변수 이름을 그대로 조회한다.

---

## 다음에 바로 이어서 볼 문서

- 같은 key가 env var로 잘 들어왔는데도 파일/profile/command-line/test property 중 누가 최종 값을 덮었는지 헷갈리면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)로 간다.
- env var 이름이 틀려서 `@ConditionalOnProperty` 조건이 missing처럼 보이는 상황이면 [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)로 이어진다.
- list/map을 Java 설정 객체로 묶는 전체 파이프라인이 필요하면 [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)로 이어진다.
