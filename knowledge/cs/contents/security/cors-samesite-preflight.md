# CORS, SameSite, Preflight

> 한 줄 요약: 브라우저 보안 모델은 서버 간 호출과 다르다. CORS, SameSite, Preflight는 "누가 요청했는지"와 "쿠키를 같이 보낼지"를 분리해서 제어하는 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CORS 기초](./cors-basics.md)
> - [Preflight Debug Checklist](./preflight-debug-checklist.md)
> - [Spring Security OPTIONS Primer](./spring-security-options-primer.md)
> - [인증과 인가의 차이](./authentication-vs-authorization.md)
> - [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
> - [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)
> - [TLS, 로드밸런싱, 프록시](../network/tls-loadbalancing-proxy.md)
> - [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: cors samesite preflight, preflight advanced, options preflight, preflight cache, preflight failure vs auth failure, options 401 not auth, options 403 before post, request never sent due to preflight, access-control-request-method, access-control-request-headers, access-control-allow-methods, access-control-allow-headers, access-control-allow-origin, reverse proxy blocks options, spring security options blocked, error response missing access-control-allow-origin, preflight passed then 401, preflight passed then 403, sameSite cors preflight, browser preflight deep dive, beginner preflight handoff, cors beginner primer return, return to security README

---

## 처음 읽는다면

- SOP/CORS 자체가 아직 낯설면 [CORS 기초](./cors-basics.md)부터 보고, `OPTIONS`만 실패하는 증상 분기부터 필요하면 [Preflight Debug Checklist](./preflight-debug-checklist.md)를 먼저 거치는 편이 덜 헷갈린다.
- 다른 입문 경로로 돌아가려면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 복귀하면 된다.

---

## 핵심 개념

브라우저는 기본적으로 다른 출처(origin)로의 요청을 제한한다. 이 제한을 우회하는 공식적인 방법이 CORS다.

- `Origin`: 스킴 + 호스트 + 포트
- `CORS`: 서버가 "이 출처는 허용"이라고 응답 헤더로 명시하는 규칙
- `SameSite`: 쿠키가 cross-site 요청에 함께 실릴지 정하는 속성
- `Preflight`: 실제 요청 전에 브라우저가 먼저 허용 여부를 확인하는 `OPTIONS` 요청

이 네 개를 분리하지 않으면 보통 다음 사고가 난다.

- API는 열렸는데 쿠키가 안 실린다
- 쿠키는 실렸는데 CSRF가 열린다
- `*`로 허용했는데 credential 요청이 막힌다
- Preflight가 실패해서 실제 요청이 아예 나가지 않는다

---

## 깊이 들어가기

### 1. Origin과 CORS는 다르다

같은 사이트처럼 보여도 origin이 다를 수 있다.

- `https://app.example.com`과 `https://api.example.com`은 다른 origin이다
- 포트가 다르면 다른 origin이다
- 프론트와 API가 분리되면 CORS가 필요한 경우가 많다

CORS는 서버가 브라우저에게 "이 origin의 스크립트가 응답을 읽어도 된다"라고 알려주는 메커니즘이다.

### 2. SameSite는 쿠키의 전송 규칙이다

`SameSite`는 브라우저가 쿠키를 언제 실어 보낼지 결정한다.

| 값 | 의미 | 실무 감각 |
|---|---|---|
| `Strict` | 거의 모든 cross-site 요청에 쿠키 미전송 | 가장 보수적 |
| `Lax` | top-level navigation 위주 허용 | 기본값으로 많이 고려 |
| `None` | cross-site에서도 전송 가능, `Secure` 필요 | SSO/외부 연동에 필요 |

중요한 점은 CORS와 SameSite가 서로 다른 층이라는 것이다.

- CORS: 응답을 읽을 수 있는가
- SameSite: 쿠키를 보낼 것인가

`auth.example.com`과 `app.example.com`처럼 sibling subdomain 사이에서 "cookie는 보이는데 login이 또 풀린다"면, `SameSite`보다 먼저 `Domain`/host-only cookie와 `Path` 범위를 확인하는 편이 안전하다. 이 beginner 분해는 [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md)에 따로 정리돼 있다.

### 3. Preflight가 필요한 이유

브라우저는 위험한 요청을 먼저 확인한다.

`OPTIONS`가 실제 auth failure인지 preflight 차단인지부터 헷갈리면, deep dive로 내려가기 전에 [Preflight Debug Checklist](./preflight-debug-checklist.md)에서 먼저 갈림길을 잡는 편이 안전하다.

- `Content-Type: application/json`
- custom header 사용
- `PUT`, `DELETE`, 일부 `PATCH`

이 경우 브라우저는 실제 요청 전에 `OPTIONS`로 허용 여부를 묻는다.

서버가 이 `OPTIONS`를 제대로 처리하지 않으면 다음이 생긴다.

- 프론트 콘솔에는 CORS 에러만 보임
- 실제 서버 로직은 아예 호출되지 않음
- 운영자는 500이 아닌데도 장애처럼 느낀다

### 4. credential 요청은 더 엄격하다

쿠키나 인증 헤더를 포함하는 요청은 주의가 필요하다.

- cross-origin `fetch`에서 cookie를 기대하면 request 쪽에는 보통 `credentials: "include"`가 필요하다
- `Access-Control-Allow-Origin: *`는 credential과 같이 쓰기 어렵다
- `Access-Control-Allow-Credentials: true`를 쓰면 origin을 명시해야 한다
- `Vary: Origin`이 없으면 캐시가 잘못된 응답을 재사용할 수 있다

단, `credentials: "include"`는 cookie scope를 무시하지 않는다. `Domain`, `Path`, `SameSite`, `Secure`까지 한꺼번에 헷갈리면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)를 먼저 읽고 이 문서로 돌아오면 된다.

이 지점은 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md)와 같이 보면 좋다.

---

## 실전 시나리오

### 시나리오 1: 프론트는 호출하는데 쿠키가 안 보냄

원인:

- `SameSite=Lax` 또는 `Strict`로 되어 있음
- cross-site XHR/fetch에서 쿠키 전송을 기대함

해결:

- SSO나 cross-site 인증이면 `SameSite=None; Secure`를 검토
- 정말 필요한 쿠키만 그렇게 설정
- CSRF 방어를 함께 설계

### 시나리오 2: CORS는 맞는데 preflight에서 실패

원인:

- `OPTIONS` 응답에 `Access-Control-Allow-Methods` 누락
- `Access-Control-Allow-Headers`에 실제 헤더가 없음
- reverse proxy가 `OPTIONS`를 차단

### 시나리오 3: `*`로 열었는데 credential 요청이 실패

원인:

- `Access-Control-Allow-Origin: *`
- `Allow-Credentials: true`

해결:

- 허용 origin을 명시
- allowlist 기반으로 응답 생성

### 시나리오 4: 캐시가 이상한 origin 응답을 재사용

원인:

- `Vary: Origin` 누락
- CDN이나 proxy가 origin별 응답을 분리하지 않음

---

## 코드로 보기

### Spring CORS 설정

```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.example.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("Authorization", "Content-Type", "X-Request-Id")
            .exposedHeaders("Location")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

### 서버 응답 헤더 예시

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: Authorization,Content-Type,X-Request-Id
Vary: Origin
```

### 쿠키 속성 예시

```http
Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=None
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `SameSite=Strict` | CSRF 위험이 낮다 | 외부 연동과 UX가 깨질 수 있다 | 내부 전용, 보수적 환경 |
| `SameSite=Lax` | 기본 UX와 보안 균형이 좋다 | 일부 cross-site 흐름은 제한된다 | 일반적인 브라우저 서비스 |
| `SameSite=None` | cross-site 인증에 유연하다 | `Secure`와 CSRF 대응이 필수다 | SSO, 외부 도메인 연동 |
| wide-open CORS | 편하다 | 오용 시 즉시 취약해진다 | 거의 없음 |
| allowlist CORS | 안전하다 | 설정과 운영이 필요하다 | 대부분의 실서비스 |

핵심 판단 기준은 "열면 편하다"가 아니라 **브라우저 보안 모델을 얼마나 노출할 것인가**다.

---

## 꼬리질문

> Q: CORS를 열면 CSRF도 자동으로 해결되나요?
> 의도: CORS와 CSRF의 층이 다르다는 점을 확인한다.
> 핵심: CORS는 응답 읽기 제어, CSRF는 요청 위조 방어다.

> Q: `SameSite=None`은 왜 `Secure`와 같이 써야 하나요?
> 의도: 브라우저 쿠키 정책과 전송 안전성을 이해하는지 본다.
> 핵심: cross-site 전송을 허용할수록 HTTPS가 필수다.

> Q: preflight는 왜 생기고 왜 장애처럼 보이나요?
> 의도: 브라우저가 실제 요청 전에 막는 구조를 아는지 확인한다.
> 핵심: 서버 로직이 호출되지 않기 때문에 네트워크/헤더 문제로 보인다.

## 한 줄 정리

CORS는 "응답을 읽을 수 있는가", SameSite는 "쿠키를 보낼 것인가", Preflight는 "실제 요청 전에 허용을 확인하는가"를 다룬다.
