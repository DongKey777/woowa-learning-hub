# CSRF in SPA + BFF Architecture

> 한 줄 요약: SPA라도 BFF 뒤에서 쿠키 기반 인증을 쓰면 CSRF가 사라지지 않는다. 저장 위치보다 브라우저가 자동으로 보내는 credential의 경계를 먼저 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [JWT 깊이 파기](./jwt-deep-dive.md)
> - [BFF Boundaries and Client-Specific Aggregation](../software-engineering/bff-boundaries-client-specific-aggregation.md)

retrieval-anchor-keywords: CSRF, SPA, BFF, SameSite, HttpOnly cookie, double submit, origin check, anti-CSRF token, state-changing request, browser credential, backend for frontend

---

## 핵심 개념

SPA + BFF 구조에서는 브라우저가 직접 도메인 API를 때리는 대신 BFF를 통해 요청을 보낸다.  
이 구조는 인증과 응답 shape를 단순화해 주지만, CSRF를 자동으로 없애주지는 않는다.

핵심은 인증 수단이 무엇으로 전송되느냐다.

- `cookie-based auth`: CSRF에 취약해질 수 있다
- `Authorization header`: 브라우저가 자동으로 붙이지 않으므로 CSRF 면적이 달라진다
- `BFF`: 브라우저와 내부 API 사이의 중간층이라 CSRF 경계를 다시 설계해야 한다

즉 SPA라는 이름만 보고 CSRF를 생략하면 안 된다.  
실제 위험은 "브라우저가 자동으로 실어 보내는 credential"이 있는지에 달려 있다.

---

## 깊이 들어가기

### 1. SPA + BFF에서 CSRF가 생기는 이유

SPA가 BFF를 호출할 때 보통 이런 패턴을 쓴다.

- 브라우저가 HttpOnly cookie로 세션을 보낸다
- BFF가 그 세션을 신뢰한다
- BFF가 내부 API를 대신 호출한다

이때 외부 사이트가 사용자의 브라우저를 이용해 BFF로 요청을 보내면 CSRF가 된다.

- 사용자는 클릭하지 않았다
- 브라우저는 cookie를 자동으로 붙인다
- 서버는 정상 사용자 요청처럼 보게 된다

### 2. BFF는 CSRF 면적을 줄이기도 하지만, 새로 만들기도 한다

BFF의 장점:

- 브라우저가 내부 API를 직접 알 필요가 없다
- token storage를 단순화할 수 있다
- internal auth policy를 중앙화할 수 있다

하지만 다음 상황에서는 CSRF가 살아 있다.

- BFF가 cookie 세션을 쓴다
- 상태 변경 endpoint가 존재한다
- `SameSite=None` 또는 cross-site 요청이 허용된다

### 3. 방어는 token 하나로 끝나지 않는다

SPA + BFF에서 자주 쓰는 방어:

- CSRF token
- `SameSite=Lax` 또는 `Strict`
- `Origin` / `Referer` 검증
- 상태 변경 요청에만 엄격한 검증
- CORS와 CSRF를 분리해서 설계

중요한 점은 `CORS`는 응답 읽기 제어이고, `CSRF`는 요청 위조 방어라는 것이다.

### 4. double submit cookie는 언제 유용한가

double submit 패턴은 브라우저가 읽을 수 있는 쿠키 값과 헤더 값을 맞춰서 제출하는 방식이다.

- cookie에 CSRF token을 둔다
- JS가 같은 값을 header로 보낸다
- 서버는 둘이 일치하는지 본다

하지만 이것도 XSS가 있으면 약해진다.  
그래서 CSRF 방어는 XSS 방어와 분리된 별도 축으로 봐야 한다.

### 5. BFF에서 상태 변경과 읽기 요청을 다르게 다뤄야 한다

모든 요청에 똑같은 방어를 걸면 UX가 깨질 수 있다.

- GET은 읽기 전용으로 간주하고 상대적으로 완화
- POST/PUT/PATCH/DELETE는 강하게 검증
- transfer, revoke, update settings 같은 민감 작업은 추가 확인

즉 "SPA니까 다 같은 AJAX"로 보면 안 되고, 실제 위험한 요청만 더 단단히 잠가야 한다.

---

## 실전 시나리오

### 시나리오 1: 외부 사이트에서 BFF의 송금 API를 호출함

문제:

- 사용자가 우리 서비스에 로그인한 상태다
- 공격 사이트가 form submit이나 auto POST를 보낸다
- cookie가 자동으로 전송된다

대응:

- CSRF token을 필수화한다
- Origin 검증을 추가한다
- 민감 endpoint는 SameSite와 재인증을 함께 본다

### 시나리오 2: BFF가 쿠키 없이 bearer token만 쓰는 구조로 바뀜

문제:

- 저장 위치는 바뀌었지만 브라우저 자동 전송 문제가 줄어든다
- 대신 token storage와 XSS 위험이 커질 수 있다

대응:

- token 저장 전략을 다시 검토한다
- XSS와 CSRF를 분리해서 판단한다
- 토큰 전달 경로를 문서화한다

### 시나리오 3: SameSite=None을 써야 해서 CSRF가 다시 열림

문제:

- 외부 도메인 연동 때문에 cross-site cookie가 필요하다

대응:

- CSRF token을 반드시 둔다
- 가능한 경우 top-level navigation과 XHR을 분리한다
- 외부 연동 endpoint를 별도 origin으로 분리한다

---

## 코드로 보기

### 1. BFF에서 CSRF 보호 개념

```java
@PostMapping("/account/email")
public ResponseEntity<Void> changeEmail(
        @RequestHeader("X-CSRF-TOKEN") String csrfToken,
        HttpServletRequest request,
        @RequestBody ChangeEmailRequest body) {

    csrfService.verify(request.getSession().getId(), csrfToken, request);
    accountService.changeEmail(body.userId(), body.newEmail());
    return ResponseEntity.ok().build();
}
```

### 2. Origin 검사 개념

```java
public void verifyOrigin(HttpServletRequest request) {
    String origin = request.getHeader("Origin");
    if (!"https://app.example.com".equals(origin)) {
        throw new AccessDeniedException("invalid origin");
    }
}
```

### 3. 상태 변경과 읽기 분리

```text
1. GET/HEAD는 상대적으로 완화한다
2. POST/PUT/PATCH/DELETE는 CSRF token을 요구한다
3. 민감 작업은 재인증 또는 step-up auth를 붙인다
4. BFF와 browser storage 정책을 같이 문서화한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| cookie + CSRF token | 브라우저 UX가 좋다 | 구현과 검증이 늘어난다 | SPA + BFF 대부분 |
| bearer token in header | CSRF 면적이 줄어든다 | storage와 XSS가 더 중요해진다 | 일부 API client |
| SameSite=Strict | CSRF 위험이 낮다 | 외부 연동이 깨질 수 있다 | 내부 전용 앱 |
| SameSite=None + CSRF token | cross-site 연동이 가능하다 | 보안 설정이 복잡하다 | SSO, 외부 도메인 연동 |

판단 기준은 이렇다.

- 브라우저가 자동으로 credential을 보내는가
- 외부 도메인과 상호작용해야 하는가
- 상태 변경 요청이 많은가
- BFF가 cookie-based session을 유지하는가

---

## 꼬리질문

> Q: SPA인데도 왜 CSRF가 필요할 수 있나요?
> 의도: 브라우저 자동 전송 credential의 의미를 아는지 확인
> 핵심: cookie 기반 인증이면 브라우저가 자동으로 보내기 때문이다.

> Q: BFF가 있으면 CSRF가 더 쉬워지나요, 어려워지나요?
> 의도: BFF의 보안 면적 변화를 이해하는지 확인
> 핵심: 단순화는 되지만 cookie를 쓰면 여전히 CSRF가 필요하다.

> Q: CORS가 열려 있으면 CSRF도 해결되나요?
> 의도: CORS와 CSRF를 구분하는지 확인
> 핵심: 아니다. CORS는 응답 읽기, CSRF는 요청 위조다.

> Q: SameSite만으로 충분한가요?
> 의도: 브라우저 정책만으로의 한계를 아는지 확인
> 핵심: 외부 연동과 예외가 많아서 CSRF token과 같이 봐야 한다.

## 한 줄 정리

SPA + BFF의 CSRF 방어는 "프론트엔드가 현대적이냐"가 아니라 "브라우저가 어떤 credential을 자동으로 보내는가"를 중심으로 설계해야 한다.
