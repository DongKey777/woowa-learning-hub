# Spring Docker Compose and Kubernetes Env Injection Basics: property 이름과 플랫폼 주입 실수 분리하기

> 한 줄 요약: Spring 설정 문제가 보일 때는 먼저 **Spring이 기대하는 canonical property key**를 적고, 그다음 **플랫폼이 실제로 컨테이너 process environment에 어떤 env var를 넣었는지**를 분리해서 보면 된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Spring property 이름과 Docker Compose/Kubernetes의 env injection 단계를 beginner가 한 번에 연결해 보는 **platform bridge primer**를 담당한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)
> - [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
> - [Spring `SPRING_APPLICATION_JSON` Primer: plain env var보다 나은 순간](./spring-spring-application-json-primer.md)
> - [Spring `@ConditionalOnProperty` 기본값 함정: `havingValue`, `matchIfMissing`, 환경별 property 차이](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)
> - 공식 기준: [Spring Boot Externalized Configuration - Binding From Environment Variables](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.relaxed-binding.environment-variables)
> - 공식 기준: [Docker Compose - Set environment variables within your container's environment](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
> - 공식 기준: [Docker Compose - Variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
> - 공식 기준: [Kubernetes - Configure a Pod to Use a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)

retrieval-anchor-keywords: spring docker compose kubernetes env injection basics, spring property key compose kubernetes bridge, spring env var naming vs platform injection, docker compose spring environment variables, kubernetes spring configmap env basics, app_payment_baseurl, app.payment.base-url, compose .env interpolation vs container environment, kubernetes env valuefrom configmapkeyref, kubernetes envfrom configmap spring boot, spring beginner configuration primer, docker compose env_file spring boot, configmap key vs env var name, container process environment spring boot, spring docker compose k8s env injection basics primer basics

## 핵심 개념

초보자 기준으로는 설정 경로를 세 층으로 나누면 제일 덜 헷갈린다.

```text
1. Spring property key
2. 컨테이너 process environment의 env var 이름
3. 그 env var를 Docker Compose / Kubernetes가 실제로 주입했는가
```

예를 들어 Spring에서 원하는 설정이 이것이라면:

```text
app.payment.base-url
```

먼저 Spring env var 이름으로 바꾼다.

```text
APP_PAYMENT_BASEURL
```

그다음 질문은 두 개로 분리된다.

- 이름이 맞는가: `APP_PAYMENT_BASEURL`로 넣었는가
- 주입이 되었는가: Compose나 Kubernetes가 그 이름을 컨테이너 환경 변수로 실제 전달했는가

이 둘을 섞으면 아래 같은 착시가 생긴다.

```text
"Spring이 env var를 못 읽는다"
```

실제로는 둘 중 하나인 경우가 많다.

- Spring 이름 변환이 틀렸다
- 플랫폼 주입이 안 됐다

---

## 1. 먼저 이 표로 구분한다

| 레이어 | 내가 확인할 것 | 실패 예시 | 실패 분류 |
|---|---|---|---|
| Spring key | canonical key가 무엇인가 | 사실 `app.payment.base-url`인데 `app.payment.base.url`로 착각 | property naming mistake |
| env var 이름 | Spring key를 어떤 env var로 바꿔야 하나 | `APP_PAYMENT_BASE_URL` 사용 | env-var naming mistake |
| 플랫폼 주입 | 그 env var가 컨테이너에 실제 들어갔나 | Compose `.env`에만 적고 `environment`/`env_file` 누락 | platform injection mistake |
| 최종 우선순위 | 더 높은 source가 덮었나 | env var는 맞게 들어왔지만 CLI/test property가 override | property source mistake |

beginner는 항상 위에서 아래 순서로 본다.

1. Spring key를 한 줄로 적는다.
2. 맞는 env var 이름으로 변환한다.
3. Compose/Kubernetes가 그 env var를 컨테이너에 넣는 구성을 확인한다.
4. 마지막으로 Spring 우선순위를 본다.

---

## 2. Docker Compose와 Kubernetes는 "Spring 이름 변환기"가 아니다

둘 다 Spring property key를 자동으로 이해하지 않는다.
그냥 **컨테이너 환경 변수**를 넣어 주는 플랫폼일 뿐이다.

즉 아래처럼 생각하면 안전하다.

```text
Spring Boot:
"APP_PAYMENT_BASEURL 이라는 env var가 있으면 app.payment.base-url로 바인딩해 볼게"

Docker Compose / Kubernetes:
"무슨 이름인지는 모르겠고, 네가 지정한 env var를 컨테이너에 넣어 줄게"
```

그래서 `app.payment.base-url`을 Compose나 Kubernetes에 그대로 적는다고 Spring용 이름으로 자동 변환되지 않는다.

---

## 3. Docker Compose에서 자주 헷갈리는 두 가지: `.env`와 `environment`

Compose beginner 함정은 거의 항상 아래 둘을 섞는 데서 나온다.

| 항목 | 역할 | Spring이 직접 보는가 |
|---|---|---|
| 프로젝트 루트 `.env` | Compose 파일 안 `${VAR}` 치환값 제공 | 보통 직접 안 본다 |
| `services.<name>.environment` | 컨테이너 env var를 직접 주입 | 본다 |
| `services.<name>.env_file` | 파일의 key/value를 컨테이너 env var로 주입 | 본다 |

Compose 공식 문서 기준으로 컨테이너 환경은 `environment`나 `env_file` 같은 **명시적 service 설정**이 있어야 잡힌다.

### 1. 되는 예시

```yaml
services:
  app:
    image: demo
    environment:
      APP_PAYMENT_BASEURL: https://pay.example.com
```

이 경우 Spring은 `APP_PAYMENT_BASEURL`을 보고 `app.payment.base-url`로 바인딩할 수 있다.

### 2. 많이 틀리는 예시

`.env`

```text
APP_PAYMENT_BASEURL=https://pay.example.com
```

`compose.yaml`

```yaml
services:
  app:
    image: demo
```

이 상태는 초보자가 기대하는 것과 다를 수 있다.

```text
.env에 값이 있다
!=
컨테이너 env var가 자동으로 생긴다
```

이 `.env`는 Compose 파일 치환에 쓰일 수는 있지만, 위 예시처럼 service의 `environment`나 `env_file` 연결이 없으면 컨테이너 내부 env var 주입과는 분리되어 있다.

### 3. 치환과 주입을 함께 쓰는 예시

`.env`

```text
PAYMENT_BASE_URL=https://pay.example.com
```

`compose.yaml`

```yaml
services:
  app:
    image: demo
    environment:
      APP_PAYMENT_BASEURL: ${PAYMENT_BASE_URL}
```

이 경우에는:

- `${PAYMENT_BASE_URL}`는 Compose 치환 단계
- `APP_PAYMENT_BASEURL`는 컨테이너에 들어가는 최종 env var 이름

즉 치환에 쓰는 이름과 Spring이 읽는 이름은 같을 수도 있고 다를 수도 있다.

---

## 4. Kubernetes에서는 `ConfigMap key`와 `env name`을 분리해서 봐야 한다

Kubernetes beginner 함정은 이것이다.

```text
ConfigMap에 key를 만들었다
=
Spring이 그 이름을 바로 읽는다
```

항상 그렇지는 않다. Pod spec이 어떤 방식으로 연결하느냐가 중요하다.

### 1. `env` + `configMapKeyRef`: "값의 출처"와 "최종 env var 이름"을 분리

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  payment.base-url: https://pay.example.com
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: demo
      env:
        - name: APP_PAYMENT_BASEURL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: payment.base-url
```

여기서 중요한 건 두 이름이 다르다는 점이다.

| 위치 | 의미 |
|---|---|
| `key: payment.base-url` | ConfigMap 안에서 값을 찾는 이름 |
| `name: APP_PAYMENT_BASEURL` | 컨테이너 내부 최종 env var 이름 |

Spring이 직접 보는 것은 `env.name` 쪽이다.

그래서 이 방식은 beginner에게 가장 안전하다.

- ConfigMap key는 사람이 읽기 좋은 이름으로 둔다
- Pod `env.name`은 Spring이 기대하는 env var 이름으로 맞춘다

### 2. `envFrom`: ConfigMap key가 곧 env var 이름

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_PAYMENT_BASEURL: https://pay.example.com
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: demo
      envFrom:
        - configMapRef:
            name: app-config
```

이 방식에서는 ConfigMap key가 그대로 env var 이름이 된다.

즉 `envFrom`을 쓸 때는 ConfigMap key 자체를 Spring용 env var 이름으로 만들어 두는 편이 단순하다.

## 4. Kubernetes에서는 `ConfigMap key`와 `env name`을 분리해서 봐야 한다 (계속 2)

아래처럼 key를 `payment.base-url`로 두고 `envFrom`만 쓰면, 초보자는 "ConfigMap에 값이 있는데 왜 Spring이 못 읽지?"라는 혼란을 겪기 쉽다. Kubernetes 공식 문서도 `envFrom`에서는 ConfigMap key가 Pod 안 env var 이름이 되며, env var 이름으로 유효하지 않은 key는 skip되고 이벤트에 기록된다고 설명한다.

그래서 Spring relaxed binding과 바로 맞추려면 `APP_PAYMENT_BASEURL`처럼 env-var-friendly key를 쓰는 쪽이 안전하다.

---

## 5. 같은 설정을 세 플랫폼으로 나란히 보기

원하는 Spring key:

```text
app.payment.base-url
```

맞는 env var:

```text
APP_PAYMENT_BASEURL
```

| 위치 | 올바른 예시 |
|---|---|
| `application.yml` | `app.payment.base-url: https://pay.example.com` |
| Docker Compose | `environment: { APP_PAYMENT_BASEURL: https://pay.example.com }` |
| Kubernetes `env` | `name: APP_PAYMENT_BASEURL` + `value: https://pay.example.com` |
| Kubernetes `envFrom` | ConfigMap key를 `APP_PAYMENT_BASEURL`로 두고 주입 |

즉 플랫폼이 달라도 중간 다리는 하나다.

```text
Spring canonical key
-> Spring용 env var 이름
-> 플랫폼이 그 이름을 실제 주입
```

---

## 6. 30초 디버깅 체크리스트

### 1. local `application.yml`은 되는데 Compose에서만 안 된다

먼저 아래를 본다.

- `app.payment.base-url`을 `APP_PAYMENT_BASEURL`로 바꿨는가
- 그 값이 `environment`나 `env_file`을 통해 컨테이너에 들어가게 했는가
- 단순히 프로젝트 루트 `.env`에만 적어 둔 것은 아닌가

### 2. Kubernetes ConfigMap은 있는데 Spring이 못 읽는다

먼저 아래를 본다.

- Pod spec에 `env` 또는 `envFrom` 연결이 있는가
- `env`를 썼다면 `env.name`이 `APP_PAYMENT_BASEURL`처럼 Spring용 이름인가
- `envFrom`을 썼다면 ConfigMap key 자체가 Spring이 읽을 env var 이름인가

### 3. env var는 분명 있는데 값이 이상하다

이 경우는 주입보다 우선순위 문제일 수 있다.

- command-line argument가 덮었는가
- profile 파일 값이 기대와 다르게 보이는가
- 테스트라면 test property가 더 위에 있는가

---

## 흔한 오해

### 1. Docker Compose `.env`는 Spring Boot가 자동으로 읽는다

기본적으로 아니다. Compose 치환용 `.env`와 컨테이너 환경 변수 주입은 분리해서 봐야 한다.

### 2. Kubernetes ConfigMap key 이름만 맞으면 Spring이 자동으로 읽는다

Pod의 `env`/`envFrom` wiring이 있어야 한다.

### 3. `configMapKeyRef.key`가 Spring env var 이름이다

아니다. `env.name`이 최종 env var 이름이고, `key`는 ConfigMap 내부에서 값을 찾는 이름이다.

### 4. Compose나 Kubernetes가 dotted key를 Spring용 env var로 자동 변환해 준다

아니다. `APP_PAYMENT_BASEURL` 같은 이름은 사용자가 명시적으로 정해야 한다.

### 5. 플랫폼 주입만 성공하면 끝이다

아니다. 같은 key를 command-line, test property, profile 파일이 더 높은 우선순위로 덮을 수도 있다.

---

## 다음에 바로 이어서 볼 문서

- env var 이름 변환 규칙 자체가 헷갈리면 [Spring Relaxed Binding Env Var Cheatsheet: dotted, dashed, list, map key 바꾸기](./spring-relaxed-binding-env-var-cheatsheet.md)로 간다.
- env var가 맞게 들어왔는데도 최종 값이 다르면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property`](./spring-property-source-precedence-quick-guide.md)로 이어진다.
- nested object/list/map이라서 env var 이름 만들기가 너무 불편하면 [Spring `SPRING_APPLICATION_JSON` Primer: plain env var보다 나은 순간](./spring-spring-application-json-primer.md)으로 간다.

## 한 줄 정리

Spring 설정 문제가 보일 때는 먼저 **Spring이 기대하는 canonical property key**를 적고, 그다음 **플랫폼이 실제로 컨테이너 process environment에 어떤 env var를 넣었는지**를 분리해서 보면 된다.
