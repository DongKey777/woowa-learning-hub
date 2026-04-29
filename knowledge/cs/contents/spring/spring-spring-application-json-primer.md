# Spring `SPRING_APPLICATION_JSON` Primer: plain env var보다 나은 순간

> 한 줄 요약: 값 하나 둘 바꾸는 정도면 일반 환경 변수가 더 단순하지만, nested object/list/map key처럼 이름 모양이 깨지기 쉬운 설정은 `SPRING_APPLICATION_JSON`으로 한 번에 넣는 편이 안전하다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `SPRING_APPLICATION_JSON`을 beginner가 "언제 일반 env var 대신 꺼내야 하는지" 빠르게 고르는 **configuration primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)
> - 공식 기준: [Spring Boot Externalized Configuration - JSON Application Properties](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.json)
> - 공식 기준: [Spring Boot Externalized Configuration - Binding Maps](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.relaxed-binding.maps)

retrieval-anchor-keywords: spring application json primer, spring_application_json, spring application json 뭐예요, spring application json 처음 배우는데, spring application json 언제 써요, spring application json 큰 그림, spring application json vs env var, plain env var vs spring application json, nested configuration env var spring boot, complex map key spring boot, map key slash dot env var, properties 많은데 env var 너무 길어요, 리스트 설정 env var 헷갈려요, beginner property configuration primer, what is spring application json

## 핵심 개념

초보자 기준으로는 이렇게 생각하면 된다.

```text
일반 env var = key를 한 줄씩 평평하게 펴서 넣기
SPRING_APPLICATION_JSON = 설정 객체를 JSON 한 덩어리로 넣기
```

그래서 질문도 단순하다.

- key 몇 개가 단순한가? 그러면 일반 env var가 낫다.
- nested 구조를 그대로 넣고 싶은가? 그러면 `SPRING_APPLICATION_JSON`이 낫다.
- map key에 `/`, `.`, 대문자, `*` 같은 문자가 섞여 shape가 깨질 수 있는가? 그러면 `SPRING_APPLICATION_JSON` 쪽이 더 안전하다.

`SPRING_APPLICATION_JSON`은 "새로운 바인딩 규칙"이 아니라, **JSON을 property source로 먼저 풀어 주는 입구**다.
즉 바인딩은 그대로 Spring Boot가 하지만, 운영체제 환경 변수 이름 제약을 한 번 우회할 수 있다.

### 처음 많이 나오는 질문

- "`SPRING_APPLICATION_JSON`이 뭐예요?" -> 복잡한 설정을 env var 하나에 담는 입구다.
- "처음 배우는데 언제 써요?" -> nested object, list, map key shape 보존이 필요할 때 꺼낸다.
- "큰 그림에서 일반 env var랑 뭐가 달라요?" -> 일반 env var는 key를 펼쳐 적고, `SPRING_APPLICATION_JSON`은 구조를 통째로 넣는다.

---

## 1. 먼저 이 표로 고른다

| 상황 | 먼저 고를 것 | 이유 |
|---|---|---|
| `server.port`, `SPRING_PROFILES_ACTIVE`, feature flag 몇 개만 바꾼다 | 일반 env var | 가장 짧고 읽기 쉽다 |
| list, nested object를 한 번에 넣어야 한다 | `SPRING_APPLICATION_JSON` | 구조를 JSON으로 그대로 적을 수 있다 |
| map key에 `/internal/**`, `tenant.alpha`, `X-Trace-Id` 같은 이름이 들어간다 | `SPRING_APPLICATION_JSON` | env var 이름으로 평평하게 펴는 과정에서 key shape가 깨지기 쉽다 |
| 같은 prefix 아래 key가 너무 많아 env var가 여러 줄로 흩어진다 | `SPRING_APPLICATION_JSON` | 한 블록으로 모아 보여 줄 수 있다 |

한 줄로 줄이면 이렇다.

- 단순 key 몇 개면 일반 env var
- 구조 보존이 중요하면 `SPRING_APPLICATION_JSON`

---

## 2. 왜 일반 env var에서 shape가 깨지나

운영체제 환경 변수는 보통 대문자, 숫자, underscore 중심으로 이름을 만든다.
그래서 Spring property key를 env var로 옮길 때는 relaxed binding 규칙에 맞춰 **평평하게 펼치는 과정**이 필요하다.

예를 들어 이 정도는 괜찮다.

```text
app.cache.enabled -> APP_CACHE_ENABLED
app.payment-timeout -> APP_PAYMENTTIMEOUT
```

하지만 구조가 깊어질수록 눈으로도 헷갈린다.

```text
app.clients[0].base-url -> APP_CLIENTS_0_BASEURL
app.tenants.admin.base-url -> APP_TENANTS_ADMIN_BASEURL
```

여기서 더 복잡한 map key가 나오면 문제가 커진다.

```text
app.routes.[/internal/**]
app.headers.[X-Trace-Id]
app.tenants.[tenant.alpha]
```

이런 key는 env var 이름으로 만들면서 아래 위험이 생긴다.

- slash와 star를 env var 이름에 자연스럽게 담기 어렵다
- dot이 path 구분처럼 보일 수 있다
- 대소문자 의미를 잃기 쉽다
- 팀원이 key를 평평하게 펴는 규칙을 다르게 기억할 수 있다

즉 "값을 못 넣는다"보다 **원래 의도한 key 모양을 잃기 쉽다**가 핵심이다.

---

## 3. `SPRING_APPLICATION_JSON`은 무엇이 편해지나

`SPRING_APPLICATION_JSON`은 JSON 한 덩어리를 Spring Boot가 읽어서 `Environment`에 넣는 방식이다.

예를 들어:

```bash
SPRING_APPLICATION_JSON='{"app":{"name":"demo"}}' java -jar app.jar
```

이 값은 Spring 안에서 대략 아래와 같은 property처럼 보인다.

```text
app.name=demo
```

초보자에게 중요한 포인트는 두 개다.

1. JSON 안에서는 nested 구조를 그대로 적을 수 있다.
2. map key를 문자열로 적을 수 있어서 env var 이름 제약을 덜 받는다.

즉 `SPRING_APPLICATION_JSON`은 "복잡한 설정을 env var 하나에 포장해서 넣는 방법"으로 보면 된다.

---

## 4. plain env var가 더 나은 경우

항상 JSON이 더 좋은 것은 아니다.
아래처럼 단순하고 독립적인 값은 일반 env var가 더 읽기 쉽다.

| 설정 의도 | 일반 env var 예시 | 왜 이쪽이 단순한가 |
|---|---|---|
| 포트 하나 바꾸기 | `SERVER_PORT=8081` | 운영 화면과 로그에서 바로 읽힌다 |
| profile 바꾸기 | `SPRING_PROFILES_ACTIVE=prod` | 팀이 익숙한 표기다 |
| feature flag 하나 켜기 | `APP_SMS_ENABLED=true` | JSON quoting 걱정이 적다 |
| timeout 하나 조정 | `APP_TIMEOUT=2s` | 한 줄 diff가 분명하다 |

즉 key 하나가 짧고, 구조를 잃을 걱정이 없으면 일반 env var가 기본 선택이다.

---

## 5. `SPRING_APPLICATION_JSON`을 prefer하는 대표 장면

### 1. nested object를 한 번에 넣고 싶을 때

`@ConfigurationProperties`가 아래처럼 생겼다고 하자.

```java
@ConfigurationProperties("app")
public record AppProperties(
        Retry retry
) {
    public record Retry(boolean enabled, int maxAttempts, Duration backoff) {
    }
}
```

일반 env var로도 가능은 하다.

```text
APP_RETRY_ENABLED=true
APP_RETRY_MAXATTEMPTS=3
APP_RETRY_BACKOFF=2s
```

하지만 key가 더 많아지면 흩어진다.
이럴 때는 JSON이 의도를 더 한 번에 보여 준다.

```bash
SPRING_APPLICATION_JSON='{"app":{"retry":{"enabled":true,"max-attempts":3,"backoff":"2s"}}}'
```

이 경우는 "값 몇 개"보다 **구성 블록 하나**를 전달하는 느낌이 강하다.

### 2. list를 한 번에 넣고 싶을 때

일반 env var는 index를 직접 펼쳐야 한다.

```text
APP_CLIENTS_0_NAME=payment
APP_CLIENTS_0_BASEURL=https://pay.example.com
APP_CLIENTS_1_NAME=order
APP_CLIENTS_1_BASEURL=https://order.example.com
```

JSON은 list shape를 그대로 적을 수 있다.

```bash
SPRING_APPLICATION_JSON='{"app":{"clients":[{"name":"payment","base-url":"https://pay.example.com"},{"name":"order","base-url":"https://order.example.com"}]}}'
```

초보자 기준에서는 index를 손으로 맞추는 실수를 줄이는 장점이 크다.

### 3. map key 자체가 중요한 때

아래처럼 route pattern이나 header name을 key로 쓰는 경우가 있다.

```java
@ConfigurationProperties("app")
public record AppProperties(
        Map<String, String> routes,
        Map<String, String> headers
) {
}
```

여기서 key가 아래처럼 생기면 일반 env var는 금방 어색해진다.

```text
routes["/internal/**"]
headers["X-Trace-Id"]
```

이럴 때는 JSON key를 그대로 쓰는 편이 낫다.

## 5. `SPRING_APPLICATION_JSON`을 prefer하는 대표 장면 (계속 2)

```bash
SPRING_APPLICATION_JSON='{"app":{"routes":{"[/internal/**]":"admin"},"headers":{"[X-Trace-Id]":"trace-id"}}}'
```

bracket을 쓴 이유는 Spring map binding에서 **원래 key 모양을 보존하려는 의도**를 더 분명히 만들기 위해서다.

### 4. dot이 들어간 map key가 nested path로 오해될 때

아래 둘은 전혀 다를 수 있다.

```text
tenants["tenant.alpha"]
tenants["tenant"]["alpha"]
```

env var를 평평하게 만들다가 `tenant.alpha`를 path처럼 읽히게 만들면 의도와 다른 구조가 된다.
JSON에서는 key를 문자열로 적고, 필요하면 bracket으로 보존 의도를 드러낼 수 있다.

```bash
SPRING_APPLICATION_JSON='{"app":{"tenants":{"[tenant.alpha]":{"base-url":"https://alpha.example.com"}}}}'
```

---

## 6. 비교 예시: 언제 갈아타야 하나

| 하고 싶은 일 | 일반 env var | `SPRING_APPLICATION_JSON` | 추천 |
|---|---|---|---|
| `app.sms.enabled=true` 하나 넣기 | 매우 단순 | 오히려 장황함 | 일반 env var |
| client 2개를 list로 넣기 | index를 다 펼쳐야 함 | list 그대로 표현 가능 | JSON 쪽 우세 |
| route pattern map key 보존 | 이름 제약 때문에 어색함 | key를 문자열로 적을 수 있음 | JSON 권장 |
| header 이름 대소문자/특수문자 보존 | 실수 위험 큼 | key shape를 문서처럼 보존 가능 | JSON 권장 |

beginner가 기억할 기준은 이것이다.

```text
설정을 "한 줄 값"으로 보고 있으면 env var
설정을 "작은 JSON 문서"로 보고 있으면 SPRING_APPLICATION_JSON
```

---

## 흔한 오해

### 1. `SPRING_APPLICATION_JSON`은 env var보다 우선순위가 낮다

아니다. Spring Boot의 일반 실행 기준에서는 OS env var보다 위쪽 source로 들어간다.
그래서 같은 key가 일반 env var와 `SPRING_APPLICATION_JSON` 둘 다에 있으면 JSON 쪽이 이길 수 있다.

### 2. JSON이면 map key 보존 문제가 자동으로 모두 해결된다

반은 맞고 반은 틀리다. JSON은 구조를 적기 쉽지만, map key를 **정확히 보존**해야 하는 경우에는 Spring의 bracket notation 감각도 함께 알아야 한다.

### 3. `null`을 넣으면 아래 source 값을 지울 수 있다

그렇게 기대하면 안 된다. Spring Boot 문서 기준으로 JSON의 `null` 값은 property resolver에서 사실상 missing처럼 취급되어, 더 아래 source를 `null`로 덮어쓰는 용도로는 쓸 수 없다.

### 4. 복잡한 설정은 무조건 `SPRING_APPLICATION_JSON`으로 몰아넣는 게 좋다

아니다. 값 한두 개만 바꾸는 운영 플래그까지 전부 JSON으로 옮기면 오히려 diff와 운영 가독성이 나빠질 수 있다.

---

## 바로 적용하는 체크리스트

1. 바꾸려는 값이 1~3개의 단순 key인가?
2. list나 nested object를 통째로 전달하려는가?
3. map key에 `/`, `.`, `*`, 대소문자 같은 모양 보존 이슈가 있는가?
4. 팀원이 env var 이름 변환을 감으로 쓰다 실수할 가능성이 큰가?

`2`, `3`, `4`에 해당하면 `SPRING_APPLICATION_JSON`을 먼저 검토하는 편이 안전하다.

---

## 다음에 바로 이어서 볼 문서

- env var 이름을 직접 만들어야 하는 상황이면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)로 간다.
- `SPRING_APPLICATION_JSON`이 일반 env var, profile, command-line과 충돌할 때 누가 최종 값을 이기는지 헷갈리면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)로 이어진다.
- map key 보존과 binder 동작을 더 깊게 보려면 [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)로 이어진다.

## 한 줄 정리

값 하나 둘 바꾸는 정도면 일반 환경 변수가 더 단순하지만, nested object/list/map key처럼 이름 모양이 깨지기 쉬운 설정은 `SPRING_APPLICATION_JSON`으로 한 번에 넣는 편이 안전하다.
