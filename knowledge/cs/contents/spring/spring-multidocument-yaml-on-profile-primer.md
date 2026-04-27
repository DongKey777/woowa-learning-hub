# Spring Multi-Document `application.yml` and `spring.config.activate.on-profile` Primer

> 한 줄 요약: 한 파일 안 `---`로 나눈 여러 YAML 문서는 **위에서 아래로 차례대로 읽히고**, 그중 `spring.config.activate.on-profile` 조건에 맞는 문서만 최종 merge에 참여한다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 multi-document `application.yml`과 `spring.config.activate.on-profile`의 관계를 초보자가 "한 파일 안의 여러 장 메모" 관점으로 이해하도록 돕는 **beginner config activation primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring External Config File Precedence Primer: packaged `application.yml`, external file, `spring.config.location`, `spring.config.import`](./spring-external-config-file-precedence-primer.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring `spring.config.additional-location` Primer: 기본값은 유지하고, 배포별 override만 더 얹고 싶을 때](./spring-config-additional-location-primer.md)
> - [Spring `@ActiveProfiles` vs test override primer: `application-test.yml`, `@TestPropertySource`, annotation `properties`](./spring-activeprofiles-vs-test-overrides-primer.md)

retrieval-anchor-keywords: spring multi document yaml primer, multi-document application.yml, spring.config.activate.on-profile beginner, yaml document separator spring boot, application yml three hyphens spring, on-profile does not activate profile, active profile matches document, document merge order top to bottom spring boot, later document overrides earlier document, inactive yaml document ignored, application.yml multi document vs application-prod.yml, spring activate on profile expression, spring config activate on-profile comma expression, spring profiles active invalid inside activated document, spring multi document yaml beginner

## 핵심 개념

초보자는 아래 그림으로 먼저 이해하면 된다.

```text
application.yml 한 파일
= 메모 1장 아님
= `---` 로 나뉜 여러 장 메모 묶음

Spring Boot는
1. 위에서 아래로 문서를 본다
2. on-profile 조건이 맞는 문서만 남긴다
3. 남은 문서끼리는 아래쪽 문서가 위쪽 값을 덮을 수 있다
```

즉 `spring.config.activate.on-profile`은 profile을 "켜는" 스위치가 아니라,
**이미 active인 profile을 보고 이 문서를 포함할지 말지 고르는 조건문**에 가깝다.

이 문서에서는 config server, Kubernetes config tree, profile group 운영 설계 같은 확장 주제는 다루지 않는다.
한 파일 안 multi-document YAML과 profile 조건의 기본 상호작용만 정리한다.

---

## 1. `---`는 파일 분할이 아니라 문서 분할이다

예를 들어 아래 `application.yml`은 파일 하나지만 논리적으로는 문서 세 개다.

```yaml
server:
  port: 8080

app:
  message: base
---
spring:
  config:
    activate:
      on-profile: local

server:
  port: 8081
---
spring:
  config:
    activate:
      on-profile: prod

server:
  port: 80
  shutdown: graceful
```

이 파일을 beginner 감각으로 읽으면 아래와 같다.

| 문서 | 조건 | 의미 |
|---|---|---|
| 1번 | 없음 | 항상 후보 |
| 2번 | `local` active일 때 | local용 override |
| 3번 | `prod` active일 때 | prod용 override |

중요한 점은 이것이다.

- 문서는 **위에서 아래 순서로 처리**된다
- 나중 문서가 앞 문서와 같은 key를 가지면 덮어쓸 수 있다
- 단, **조건이 맞아 활성화된 문서끼리만** merge 대상이다

즉 `prod`가 active가 아니면 3번 문서는 아예 최종 merge에 참여하지 않는다.

---

## 2. `spring.config.activate.on-profile`은 무엇을 하나

이 속성은 "이 문서가 언제 살아남는가"를 정한다.

```yaml
spring:
  config:
    activate:
      on-profile: prod
```

이 문서는 아래처럼 이해하면 된다.

```text
지금 active profile 집합에 prod가 있으면 이 문서를 포함한다
없으면 이 문서를 버린다
```

여기서 초보자가 자주 섞는 두 문장을 분리해야 한다.

| 문장 | 맞나 | 설명 |
|---|---|---|
| `on-profile: prod`가 `prod` profile을 활성화한다 | 아니다 | 활성화가 아니라 조건 검사다 |
| `prod` profile이 이미 active면 이 문서가 적용될 수 있다 | 맞다 | 조건이 맞으면 merge 대상이 된다 |

즉 active profile은 보통 `spring.profiles.active`, env var, command-line, 테스트 설정 같은 **바깥쪽 source**가 정하고,
`on-profile`은 그 결과를 보고 "이 문서를 넣을까?"만 판단한다.

---

## 3. 실제로 어떤 값이 남는가

아래 파일을 보자.

```yaml
app:
  mode: base
  cache: false
---
spring:
  config:
    activate:
      on-profile: local

app:
  mode: local
---
spring:
  config:
    activate:
      on-profile: prod

app:
  mode: prod
  cache: true
```

실행 결과는 이렇게 읽으면 된다.

| active profile | 포함되는 문서 | 최종 `app.mode` | 최종 `app.cache` |
|---|---|---|---|
| 없음 | 1번 | `base` | `false` |
| `local` | 1번, 2번 | `local` | `false` |
| `prod` | 1번, 3번 | `prod` | `true` |

`local`일 때 `cache`가 `false`로 남는 이유는 간단하다.

- 1번 문서가 `cache=false`를 제공한다
- 2번 문서는 `cache`를 다시 쓰지 않는다
- 따라서 base 문서 값이 그대로 남는다

즉 inactive 문서는 영향이 없고, active 문서도 **적은 key만 덮는다**.

---

## 4. 여러 active 문서가 동시에 맞으면 아래쪽이 이길 수 있다

`on-profile` 문서는 하나만 살아남는 것이 아니다.
조건에 맞는 문서가 여러 개면 모두 포함되고, 아래 문서가 위 문서를 덮을 수 있다.

```yaml
app:
  banner: base
---
spring:
  config:
    activate:
      on-profile: prod

app:
  banner: prod
---
spring:
  config:
    activate:
      on-profile: prod & live

app:
  banner: prod-live
```

이때:

- active profile이 `prod`만 있으면 최종값은 `prod`
- active profile이 `prod,live`면 2번과 3번 문서가 둘 다 활성화되고, 더 아래인 3번이 이겨서 최종값은 `prod-live`

초보자 mental model은 이 한 줄이면 충분하다.

```text
조건에 맞는 문서가 여러 장이면, 살아남은 문서들끼리 아래쪽이 더 나중에 덮는다
```

Spring Boot 공식 문서 기준으로 `on-profile` 값은 profile expression을 받을 수 있다.
즉 `prod | staging`, `prod & live` 같은 표현도 가능하다.

---

## 5. `application-prod.yml`과는 무엇이 다른가

둘 다 profile에 따라 값이 달라진다는 점은 같지만, beginner 기준 감각은 다르다.

| 방식 | mental model | 장점 | 주의점 |
|---|---|---|---|
| `application-prod.yml` | 파일을 나눈다 | 파일별 역할이 선명하다 | 파일 수가 늘어난다 |
| multi-document `application.yml` + `on-profile` | 한 파일 안 문서를 나눈다 | 공통값과 분기값을 한 눈에 본다 | 문서 순서와 조건을 함께 읽어야 한다 |

초보자에게는 아래 기준이 실용적이다.

- 분기 수가 적고 공통값과 차이점을 한 페이지에서 보고 싶다 -> multi-document도 괜찮다
- 환경별 설정이 길고 책임이 확실히 갈린다 -> `application-prod.yml` 같은 분리 파일이 읽기 쉽다

둘은 경쟁 관계라기보다 **정리 방식의 차이**에 가깝다.

---

## 6. 자주 하는 오해

### 오해 1. `on-profile`이 profile을 켠다

아니다.
profile을 켜는 쪽과 문서를 조건부로 포함하는 쪽은 다르다.

- profile 활성화: `spring.profiles.active`, env var, command-line, test 설정
- 문서 조건부 포함: `spring.config.activate.on-profile`

### 오해 2. 아래 문서는 항상 위 문서를 덮는다

절반만 맞다.
**활성화된 문서끼리만** 아래쪽이 위쪽을 덮는다.
조건이 안 맞아 제외된 문서는 순서에 있어도 영향이 없다.

### 오해 3. 한 문서 안에서 `spring.profiles.active`를 다시 바꿔도 된다

이건 Spring Boot 기준으로 유효한 배치가 아니다.
`spring.profiles.active`, `spring.profiles.default`, `spring.profiles.include`, `spring.profiles.group`은
profile-specific 파일이나 `spring.config.activate.on-profile`로 활성화되는 문서 안에 두면 안 된다.

즉 이런 생각은 피하는 편이 좋다.

```text
prod 문서 안에서 다시 다른 profile을 켜서 다음 문서를 제어하자
```

초보자 기준에서는 active profile 결정은 바깥 레벨에서 하고,
문서 안에서는 그 결과를 읽기만 한다고 생각하면 안전하다.

### 오해 4. `@TestPropertySource`로 multi-document 파일을 그대로 읽일 수 있다

Spring Boot 공식 문서 기준으로 multi-document properties/YAML 파일은
`@PropertySource`나 `@TestPropertySource`로 로드하는 방식과는 맞지 않는다.

즉 multi-document `application.yml`은 보통 Boot의 config data 로딩 흐름에서 이해하는 편이 맞다.

---

## 7. beginner용 빠른 판별 순서

설정이 기대와 다를 때는 아래 순서로 보면 된다.

1. 지금 active profile이 무엇인지 먼저 확인한다.
2. `application.yml` 안에서 `---`로 나뉜 문서 중 어떤 문서가 그 profile과 매치되는지 본다.
3. 매치된 문서만 남겨서 위에서 아래로 다시 읽는다.
4. 같은 key가 여러 번 나오면 아래 문서 값을 최종값으로 본다.
5. 그래도 이상하면 env var, command-line, test property처럼 파일 바깥 source가 더 높은지 본다.

이 순서만 지켜도 아래 질문 대부분이 빨리 풀린다.

- "왜 prod 블록이 안 먹지?"
- "왜 base 값이 남아 있지?"
- "왜 아래쪽 문서가 무시된 것 같지?"

## 마무리

multi-document `application.yml`은 "한 파일 안에 조건부 메모 여러 장을 넣는 방식"으로 이해하면 쉽다.
`spring.config.activate.on-profile`은 그 메모를 켜는 스위치가 아니라, **이미 켜진 profile에 맞으면 포함하는 필터**다.

파일 위치 우선순위나 external override까지 같이 정리하고 싶다면 [Spring External Config File Precedence Primer: packaged `application.yml`, external file, `spring.config.location`, `spring.config.import`](./spring-external-config-file-precedence-primer.md)를,
전체 property source 우선순위까지 한 번에 보고 싶다면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)를 이어서 보면 된다.

## 한 줄 정리

한 파일 안 `---`로 나눈 여러 YAML 문서는 **위에서 아래로 차례대로 읽히고**, 그중 `spring.config.activate.on-profile` 조건에 맞는 문서만 최종 merge에 참여한다.
