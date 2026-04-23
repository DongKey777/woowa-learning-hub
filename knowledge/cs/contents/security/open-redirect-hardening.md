# Open Redirect Hardening

> 한 줄 요약: open redirect는 단순 UX 버그가 아니라 OAuth, phishing, token leak의 발판이 될 수 있으므로 redirect 대상 allowlist와 exact match가 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
> - [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
> - [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)
> - [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
> - [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
> - [CORS, SameSite, Preflight](./cors-samesite-preflight.md)
> - [CSP Nonces / Hashes / Script Policy](./csp-nonces-vs-hashes-script-policy.md)
> - [Security README: Browser / Server Boundary deep dive catalog](./README.md#browser--server-boundary-deep-dive-catalog)

retrieval-anchor-keywords: open redirect, redirect hardening, login redirect hardening, post-login redirect, callback hardening, allowlist, exact match, phishing, OAuth redirect_uri, token leak, navigation abuse, URL validation, local redirect, browser server boundary, federated login redirect, nested redirect, redirect destination validation, absolute redirect behind load balancer, post-login redirect wrong origin, X-Forwarded-Host redirect, browser server boundary catalog, security readme browser server boundary

---

## 핵심 개념

open redirect는 사용자가 입력한 URL로 서버가 그대로 redirect해 버리는 문제다.  
겉으로는 편의 기능이지만, 보안에서는 강력한 악용 경로가 된다.

load balancer 뒤에서 앱이 자기 public origin을 잘못 알아 absolute URL을 틀리게 만드는 문제는 [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)에서 먼저 분리한다. 이 문서는 그다음 단계인 "사용자가 준 destination을 그대로 믿어도 되는가"를 다룬다.

위험:

- phishing 링크가 우리 도메인처럼 보인다
- OAuth callback이나 state 흐름이 꼬일 수 있다
- token이나 code가 잘못된 location으로 전달될 수 있다

즉 redirect는 "어디로 보내도 되는가"를 엄격하게 통제해야 한다.

---

## 깊이 들어가기

### 1. 어떤 패턴이 위험한가

위험한 예:

- `next=https://evil.com`
- `returnUrl=//evil.com`
- `redirect=/login?next=https://evil.com`
- prefix match로만 검사하는 구현

문제는 URL 파싱과 인코딩 차이로 우회가 가능하다는 점이다.

### 2. exact allowlist가 기본이다

가장 안전한 방식은 exact match다.

- 사전 등록된 path만 허용한다
- host를 자유롭게 받지 않는다
- scheme을 제한한다

### 3. relative path만 허용하는 것도 유용하다

외부 URL이 필요 없는 경우:

- 상대 경로만 허용
- 내부 route만 허용
- query를 재검증

### 4. OAuth와 결합하면 더 위험해진다

open redirect는 authorization code나 token leak의 보조 통로가 될 수 있다.

- redirect_uri가 느슨하면 code가 새어 나간다
- login completion이 외부로 튈 수 있다
- phishing page가 우리 사이트처럼 보인다

redirect를 막았다고 로그인 경계가 끝나는 것은 아니다. callback 이후 기존 세션을 그대로 재사용하면 fixation은 별도 축으로 남으므로, post-login hardening은 [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)과 함께 보는 편이 안전하다.

### 5. 검증은 문자열 비교만으로 끝나지 않는다

- URL decode 후 검사
- normalize 후 검사
- scheme, host, port, path 모두 검증
- nested redirect도 다시 검증

---

## 실전 시나리오

### 시나리오 1: `next` 파라미터가 악용됨

대응:

- allowlist를 둔다
- 상대 경로만 허용한다
- 외부 URL은 거부한다

### 시나리오 2: 로그인 후 redirect가 외부로 튐

대응:

- OAuth callback과 일반 redirect를 분리한다
- exact match만 허용한다
- redirect destination을 서버에서 결정한다

### 시나리오 3: nested redirect로 우회함

대응:

- 최종 destination을 다시 검사한다
- redirect chain 길이를 제한한다
- URL normalize를 적용한다

---

## 코드로 보기

### 1. 안전한 redirect 검증

```java
public URI safeRedirect(String target) {
    URI uri = URI.create(target);
    if (uri.isAbsolute()) {
        throw new IllegalArgumentException("absolute redirect not allowed");
    }
    if (!allowedPaths.contains(uri.getPath())) {
        throw new IllegalArgumentException("redirect target not allowed");
    }
    return uri;
}
```

### 2. exact allowlist

```java
public boolean isAllowedRedirect(String target) {
    return allowedRedirects.contains(normalize(target));
}
```

### 3. nested redirect 방어

```text
1. 상대 경로만 허용한다
2. normalize 후 exact match를 한다
3. redirect chain을 짧게 제한한다
4. OAuth callback의 redirect_uri는 특히 엄격하게 관리한다
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| exact allowlist | 안전하다 | 운영 관리가 필요하다 | 대부분의 서비스 |
| relative only | 단순하다 | 외부 연동이 제한된다 | 내부 앱 |
| prefix match | 구현이 쉬워 보인다 | 우회가 쉽다 | 피해야 함 |
| redirect reflection | 유연해 보인다 | 매우 위험하다 | 피해야 함 |

판단 기준은 이렇다.

- 외부 URL로 redirect해야 하는가
- OAuth callback과 결합되는가
- nested redirect가 가능한가
- exact match를 운영할 수 있는가

---

## 꼬리질문

> Q: open redirect가 왜 위험한가요?
> 의도: phishing과 OAuth 악용을 아는지 확인
> 핵심: 악성 링크와 토큰/code 유출 경로가 될 수 있기 때문이다.

> Q: exact match가 왜 중요한가요?
> 의도: prefix/partial match의 위험을 아는지 확인
> 핵심: 느슨한 비교는 우회되기 쉽기 때문이다.

> Q: nested redirect는 왜 다시 검사해야 하나요?
> 의도: 중간 redirect 우회를 아는지 확인
> 핵심: 첫 목적지가 안전해 보여도 최종 목적지는 다를 수 있기 때문이다.

> Q: OAuth와 open redirect가 만나면 왜 더 위험한가요?
> 의도: code/token leak 경로를 아는지 확인
> 핵심: authorization code가 잘못된 곳으로 전달될 수 있기 때문이다.

## 한 줄 정리

open redirect hardening은 redirect destination을 exact allowlist와 normalize로 엄격히 제한하는 일이다.
