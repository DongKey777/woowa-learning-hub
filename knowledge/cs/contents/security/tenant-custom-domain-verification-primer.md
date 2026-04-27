# Tenant Custom Domain Verification Primer

> 한 줄 요약: tenant custom domain은 "고객이 입력한 문자열"이 아니라, DNS/HTTP proof로 소유를 검증한 뒤 별도 상태로 저장하고, auth email과 redirect에서는 그 검증된 매핑만 조회해서 써야 안전하다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Password Reset, Magic Link, Public Origin Guide](./password-reset-magic-link-public-origin-guide.md)
> - [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md)
> - [Open Redirect Hardening](./open-redirect-hardening.md)
> - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
> - [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md)
> - [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
> - [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)

retrieval-anchor-keywords: tenant custom domain verification, custom domain auth email, tenant redirect domain safety, verified custom domain mapping, domain ownership proof, tenant domain TXT verification, tenant domain CNAME verification, multi-tenant custom domain beginner, auth email custom domain selection, magic link tenant domain, password reset tenant domain, redirect domain allowlist, domain takeover prevention, stale verified domain, pending domain verification, verified domain status, tenant public origin mapping, custom domain onboarding auth, tenant-specific public origin, verified callback domain, domain registry auth flow

## 먼저 잡는 mental model

초보자는 custom domain을 자주 이렇게 생각한다.

- "tenant가 `login.customer.com`을 입력했다"
- "그럼 그 주소로 메일 링크를 보내면 되겠지"

하지만 보안 관점에서는 한 단계가 빠져 있다.

**입력된 도메인**과 **검증된 도메인**은 다르다.

| 상태 | 의미 | auth email / redirect에 바로 써도 되나 |
|---|---|---|
| 사용자가 입력한 domain | 아직 문자열일 뿐이다 | 안 된다 |
| 검증 중인 domain | proof를 기다리는 상태다 | 안 된다 |
| 검증 완료된 domain | 우리 서비스가 그 tenant 소유라고 확인했다 | 된다 |
| 비활성/만료된 domain | 예전에 맞았어도 지금은 쓰면 안 될 수 있다 | 안 된다 |

핵심은 이것이다.

- **verify**: 이 tenant가 이 도메인을 진짜 제어하는지 확인한다.
- **store**: 검증 상태와 선택 정책을 따로 저장한다.
- **select**: 이메일 링크와 redirect는 요청 host가 아니라 저장된 검증 완료 매핑에서 고른다.

## 왜 verification이 먼저 필요한가

verification 없이 tenant 입력값을 바로 쓰면 아래 문제가 생긴다.

- 다른 회사 도메인을 실수나 악의로 등록할 수 있다
- password reset, magic link, invite 링크가 다른 도메인으로 나갈 수 있다
- OAuth/OIDC callback 또는 post-login redirect가 잘못된 host로 튈 수 있다
- 탈퇴한 tenant가 예전에 쓰던 domain을 재활용해도 stale mapping이 남을 수 있다

짧게 말하면, custom domain은 브랜딩 설정이 아니라 **신뢰 경계 설정**이다.

## 가장 단순한 안전 패턴

1. tenant가 custom domain을 등록 요청한다.
2. 서비스가 랜덤 verification token을 발급한다.
3. tenant가 DNS TXT/CNAME 또는 정해진 HTTP 경로로 proof를 올린다.
4. 서비스가 proof를 확인하면 domain 상태를 `verified`로 바꾼다.
5. auth email과 redirect는 `verified` 상태인 domain만 사용한다.

예시:

```text
tenant = alpha
requested domain = login.alpha-example.com
verification token = woowa-verify=8f3c...

DNS TXT _woowa-verify.login.alpha-example.com = "woowa-verify=8f3c..."

verification success
stored mapping = tenant alpha -> https://login.alpha-example.com
```

이후 password reset 메일을 보낼 때는 request의 `Host`를 읽지 않고, 저장된 `tenant alpha`의 검증 완료 origin을 다시 조회한다.

## 어떤 방식으로 소유를 증명하나

| 방식 | 어떻게 증명하나 | 장점 | 주의점 |
|---|---|---|---|
| DNS TXT | 특정 TXT 레코드에 verification token 게시 | 가장 흔하고 명확하다 | DNS 전파 지연을 고려해야 한다 |
| DNS CNAME | 우리 서비스가 준 target으로 연결 | onboarding과 라우팅을 같이 묶기 쉽다 | CNAME만 보고 "누가 등록했는가"를 분리해서 해석해야 한다 |
| HTTP 파일/경로 | 정해진 URL에 token 응답 | 웹 호스팅 제어 증명에 직관적이다 | CDN/cache, redirect 개입을 조심해야 한다 |

beginner 기준 기본값은 보통 **DNS TXT verification**이다.
이유는 "누가 이 domain zone을 제어하는가"를 비교적 단순하게 보여 주기 때문이다.

## 저장은 문자열이 아니라 상태 머신으로 본다

안전한 저장 모델은 domain 하나를 단순 `varchar`로 끝내지 않는다.

| 필드 | 왜 필요한가 |
|---|---|
| `tenant_id` | 어떤 tenant의 domain인지 분리하기 위해 |
| `hostname` | 정확히 어떤 host를 검증했는지 남기기 위해 |
| `status` | `pending`, `verified`, `revoked` 같은 상태를 구분하기 위해 |
| `verification_method` | DNS TXT인지 HTTP proof인지 추적하기 위해 |
| `verification_token_hash` | raw token 노출 없이 비교하기 위해 |
| `verified_at` | 언제 성공했는지 기록하기 위해 |
| `last_checked_at` | stale 여부를 다시 확인하기 위해 |
| `is_primary_auth_origin` | 여러 verified domain 중 기본 선택값을 고르기 위해 |

실무 감각으로 외우면 이렇다.

- **requested domain** 테이블과
- **verified/active domain** 판단을
- 코드에서 명시적으로 분리한다

그래야 `pending` domain이 실수로 메일 발송 경로에 섞이지 않는다.

## selection은 어디서 해야 하나

가장 흔한 실수는 이메일/redirect 생성 코드가 현재 요청 값을 바로 쓰는 것이다.

```java
String link = "https://" + request.getHeader("Host") + "/reset?token=" + token;
```

tenant custom domain이 있으면 selection 기준은 아래 순서가 더 안전하다.

1. 현재 인증 대상 tenant를 식별한다.
2. DB/registry에서 그 tenant의 `verified` + `active` domain을 조회한다.
3. `is_primary_auth_origin=true` 같은 정책으로 하나를 고른다.
4. 없으면 서비스 기본 public origin으로 fallback한다.

즉 source of truth는:

- request host가 아니라
- user가 입력한 raw domain도 아니라
- **저장된 검증 완료 매핑**이다

## auth email과 browser redirect를 나눠서 생각하기

둘 다 URL을 만들지만 기준이 조금 다르다.

| 장면 | 더 안전한 기본값 |
|---|---|
| password reset / magic link / invite email | tenant의 verified primary auth origin |
| 로그인 후 내부 화면 이동 | 가능하면 relative path |
| OAuth `redirect_uri` | 사전 등록된 exact callback URL |
| tenant landing page redirect | verified domain allowlist에서 선택 |

혼동 포인트는 이것이다.

- email 링크는 "나중에 다른 환경에서 열리는 주소"라서 검증된 canonical origin이 중요하다
- browser 내부 이동은 relative path가 가능하면 그게 더 단순하다
- 사용자 입력 `returnUrl`은 custom domain 검증과 별개로 [Open Redirect Hardening](./open-redirect-hardening.md) 규칙이 필요하다

## 흔한 구현 실수

### 실수 1. `pending` domain도 일단 써 준다

"고객이 방금 입력했으니 onboarding 중에는 써도 되지 않을까?"라는 유혹이 있다.
하지만 이러면 오타나 악성 등록이 바로 auth 링크 표면으로 올라온다.

### 실수 2. tenant 없이 domain만 key로 삼는다

`customer.com`이 누구 것인지 tenant 문맥 없이 고르면 support tool이나 background job에서 잘못 선택될 수 있다.
선택은 항상 `tenant_id -> verified domain` 순서여야 한다.

### 실수 3. 검증 후 상태를 영원히 믿는다

도메인 소유권은 바뀔 수 있다.
DNS가 제거되거나 tenant가 해지될 수 있으므로 disable/reverify 흐름이 필요하다.

### 실수 4. callback allowlist와 email origin registry를 섞어 둔다

둘 다 "허용된 URL"처럼 보여도 목적이 다르다.

- callback allowlist는 exact redirect 검증용
- verified auth origin registry는 우리 서비스가 먼저 링크를 만들 때 쓰는 값

같은 저장소를 쓸 수는 있어도 의미는 분리해서 봐야 한다.

## beginner용 분기표

| 지금 보이는 증상 | 먼저 의심할 것 | 다음 문서 |
|---|---|---|
| password reset 메일이 다른 tenant 도메인으로 나감 | tenant-domain selection 오류 | [Password Reset, Magic Link, Public Origin Guide](./password-reset-magic-link-public-origin-guide.md) |
| 로그인 후 브라우저 redirect host가 internal/staging으로 뒤집힘 | proxy/public origin 복원 문제 | [Absolute Redirect URL Behind Load Balancer Guide](./absolute-redirect-url-behind-load-balancer-guide.md) |
| `returnUrl=https://evil.example`로 외부 redirect가 된다 | open redirect 검증 부족 | [Open Redirect Hardening](./open-redirect-hardening.md) |
| tenant는 맞는데 callback 단계에서 세션 연결이 어긋난다 | subdomain handoff/session boundary | [Subdomain Login Callback Boundaries](./subdomain-login-callback-boundaries.md) |

## 운영 체크리스트

- tenant가 입력한 raw domain과 `verified` domain 상태를 분리해서 저장한다
- verification token은 추측 불가한 랜덤 값으로 발급하고 raw 값 로그 노출을 줄인다
- domain selection은 background job, support 재발송, auth API 모두 같은 registry 함수를 쓰게 한다
- `verified`가 아니거나 `revoked`인 domain은 auth email과 redirect 선택에서 제외한다
- tenant 삭제/비활성화 시 custom domain도 함께 비활성화한다
- 같은 hostname을 두 tenant가 동시에 `active`로 잡지 못하게 uniqueness 규칙을 둔다
- request host와 최종 선택 origin이 다를 때는 debug/audit 신호를 남긴다

## 자주 하는 질문

> Q. tenant가 domain을 입력했는데 왜 바로 써 주면 안 되나요?
> 핵심: 그 값이 실제 소유 도메인인지 아직 모르기 때문이다.

> Q. verification이 끝났다면 request host는 안 봐도 되나요?
> 핵심: request host는 mismatch 탐지에는 쓸 수 있지만, 선택의 source of truth는 verified mapping이어야 한다.

> Q. 여러 custom domain을 한 tenant가 쓰면 어떻게 하나요?
> 핵심: 여러 개를 `verified`로 둘 수는 있지만, auth email용 primary origin 같은 선택 규칙은 하나로 고정하는 편이 안전하다.

> Q. verification은 한 번 성공하면 끝인가요?
> 핵심: 아니다. tenant 해지, DNS 제거, ownership 변경에 대비해 disable 또는 재검증 경로가 필요하다.

## 한 줄 정리

tenant custom domain은 "입력값 반사"가 아니라 "소유 검증 -> 상태 저장 -> 검증된 매핑만 선택"의 세 단계를 지켜야 auth email과 redirect를 안전하게 만들 수 있다.
