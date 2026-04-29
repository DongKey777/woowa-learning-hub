# 인증·인가·세션 기초 흐름

> 한 줄 요약: 인증은 `누구인가`를 확인하고 principal을 만들며, 세션·쿠키·JWT·BFF는 그 결과를 다음 요청으로 이어 가고, 인가는 permission model을 기준으로 `이 행동을 허용할까`를 다시 판단하는 단계다.

**난이도: 🟢 Beginner**


관련 문서:

- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)
- [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
- [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
- [카테고리 README](./README.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 문서 역할: 이 문서는 security 카테고리에서 browser page, SPA + BFF, bearer API 흐름을 한 장으로 먼저 연결하는 beginner `primer`다. authn / authz, session / cookie / JWT, login / logout, permission check가 따로따로 보일 때 가장 먼저 읽는 entrypoint로 쓴다.

retrieval-anchor-keywords: authentication authorization session foundations, auth foundation primer, authn authz session primer, principal session permission model basics, principal meaning beginner, session이 뭐예요, principal이 뭐예요, permission model 뭐예요, authentication vs authorization what is, 로그인 됐는데 왜 403, token valid but 403 basics, browser api auth flow primer, browser page auth flow, spa bff auth basics, login logout permission check primer

## 10초 선택표

이 문서는 `인증 -> 세션 전달 -> 인가`를 한 장으로 연결하는 entrypoint다. 아래 질문이 더 직접적이면 해당 문서로 먼저 가도 된다.

| 지금 더 궁금한 것 | 먼저 볼 문서 | 이 문서를 먼저 볼 필요가 없는 경우 |
|---|---|---|
| `인증이랑 인가가 정확히 뭐가 달라요` | [인증과 인가의 차이](./authentication-vs-authorization.md) | authn/authz 용어 차이만 빠르게 확인하면 될 때 |
| `쿠키, 세션, JWT가 뭐예요` | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md) | 저장/전달 방식만 먼저 잡으면 될 때 |
| `웹 보안을 어디서부터 공부해요` | [백엔드 주니어를 위한 웹 보안 스타터 팩](./web-security-starter-pack-backend-juniors.md) | 로그인 흐름보다 HTTPS/XSS/CSRF/CORS 큰 그림이 먼저일 때 |

## 이 문서 다음에 보면 좋은 문서

- authn / authz 차이와 `principal`, `permission model`을 더 또렷하게 보고 싶으면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 이어 가면 된다.
- 쿠키, 세션, JWT의 기본 정의가 아직 흐리면 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md)에서 한 단계 더 천천히 다시 잡으면 된다.
- browser에 무엇을 두고 BFF가 무엇을 맡는지 더 깊게 보려면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 내려간다.
- `401`, `403`, concealment `404`를 응답 코드로 연결하고 싶으면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)를 바로 보면 된다.
- role, scope, ownership이 같은 "권한"처럼 들리면 [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)로 이어 가는 편이 안전하다.
- social login, external IdP, authorization code, callback이 섞이면 [OAuth2 기초](./oauth2-basics.md)와 [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) 순으로 이어 가면 된다.
- browser login loop나 callback 뒤 anonymous처럼 session 쪽 증상이 보이면 같은 split vocabulary로 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)로 돌아간다. `SavedRequest`면 `redirect / navigation memory`, request `Cookie` header가 비면 `cookie-missing`, cookie는 실렸는데도 익명이면 `server-anonymous`다.

---

## 먼저 4가지 질문만 기억하기

초보자에게 가장 안전한 mental model은 용어를 외우기 전에 질문 4개를 고정하는 것이다.

| 질문 | 답하는 단계 | 대표 답 |
|---|---|---|
| `누구인가?` | 인증(authentication) | 비밀번호 검증 성공, 세션 복원 성공, JWT 서명 검증 성공 |
| `그 인증 결과를 다음 요청에 어떻게 이어 가는가?` | 세션 전달 방식 | session cookie, bearer token, BFF session |
| `민감한 토큰을 누가 직접 들고 있는가?` | trust boundary | browser, BFF, mobile app, API client |
| `이 행동을 허용할까?` | 인가(authorization) | role, scope, ownership, tenant, 정책 평가 |

한 줄로 줄이면 이렇다.

`login -> 인증 결과 보관/전달 -> 요청마다 인가 판단 -> logout/revoke`

여기서 흔한 오해를 먼저 끊어야 한다.

- 로그인 성공은 `신원 확인`일 뿐이고, 관리자 API 허용까지 보장하지 않는다.
- JWT는 `권한 시스템 전체`가 아니라 인증/주체 정보를 담는 한 방법이다.
- BFF는 보안을 자동으로 해결하는 마법이 아니라, browser와 server 사이의 credential 경계를 다시 나누는 패턴이다.
- 로그아웃 버튼은 단순히 화면 전환이 아니라 session/token 상태를 실제로 끊는 작업이어야 한다.

## 용어 5개를 한 줄로 붙이기

용어를 따로 외우면 금방 섞인다. 초보자에게는 아래처럼 `한 요청 안에서 어떤 역할을 하느냐`로 붙여서 보는 편이 더 안전하다.

| 용어 | 한 줄 뜻 | 이 문서에서 기억할 핵심 |
|---|---|---|
| authentication | 증명 정보를 검사해 `누구인지` 확인 | 비밀번호, 세션 복원, JWT 검증이 여기에 속한다 |
| principal | 현재 요청을 대표하는 주체 정보 | `userId`만이 아니라 tenant, role 힌트, 인증 시각이 함께 갈 수 있다 |
| session | 인증 결과를 다음 요청에도 이어 주는 장치 | 서버 세션일 수도 있고, 토큰 기반 복원일 수도 있다 |
| authorization | 지금 이 action을 허용할지 결정 | 같은 principal이어도 resource/action에 따라 결과가 달라진다 |
| permission model | 허용 규칙을 표현하는 문법 | role, scope, ownership, tenant 같은 축을 어떤 조합으로 볼지 정한다 |

`입장권` 비유는 여기까지는 유용하지만, 실제 서비스에서는 같은 사람이어도 `어떤 자원인지`, `어떤 행동인지`, `어느 tenant인지`에 따라 매 요청 결론이 달라진다는 점에서 비유가 멈춘다.

## 30초 분리표: 인증 성공 신호 vs 인가 성공 신호

`로그인 성공`과 `요청 허용`을 같은 의미로 읽는 실수를 줄이기 위해, 성공 신호를 둘로 분리해서 본다.

| 확인하려는 것 | 성공 신호 예시 | 아직 이 단계만으로는 모르는 것 |
|---|---|---|
| 인증(authn) 성공 | session 복원 성공, JWT 검증 성공, principal 생성됨 | 해당 API/action을 실제로 해도 되는지 |
| 인가(authz) 성공 | role/scope/ownership/tenant 검사 통과 | 다음 요청에서도 계속 허용되는지(freshness) |

즉 "`token valid` = `권한 허용`"이 아니다. 인증 성공 뒤에 인가 검사가 별도로 남아 있다.

## 초보자 디버깅 시작점 20초 버전

같은 증상에서도 시작 질문을 고정하면 헤매는 시간을 줄일 수 있다.

| 보이는 증상 | 먼저 확인할 질문 | 다음 문서 |
|---|---|---|
| `로그인은 성공했는데 왜 403이지?` | 인증은 됐고 인가에서 막힌 것인가? | [인증과 인가의 차이](./authentication-vs-authorization.md), [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `쿠키는 있는데 왜 다시 로그인하지?` | browser가 보낸 증거를 server가 다시 복원했는가? | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| `JWT는 valid라는데 왜 API는 거부하지?` | 토큰 검증과 permission check를 섞어 보고 있지 않은가? | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md), [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md) |

1. 지금 실패 요청에서 credential(`Cookie` 또는 `Authorization`)이 실제로 전송됐는가.
2. 서버가 그 credential로 principal 복원에 성공했는가.
3. principal은 있는데 권한 조건(role/scope/ownership/tenant)에서 막혔는가.

이 3줄은 `전송 실패 -> 인증 복원 실패 -> 인가 실패`를 분리하기 위한 최소 질문이다.

## 30초 레이어 판별표: 지금 어디가 깨졌나

입문자에게 가장 도움이 되는 습관은 "에러 코드를 보기 전에 실패 단계를 먼저 찍는 것"이다.

| 겉으로 보이는 증상 | 먼저 실패를 의심할 레이어 | 첫 확인 포인트 | 가장 먼저 볼 문서 |
|---|---|---|---|
| 로그인 전/로그아웃 후 API가 거절됨 | 인증 복원(authn) | credential/session이 아예 없거나 만료됐는지 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| 로그인은 됐는데 특정 기능만 계속 막힘 | 인가(authz) | principal은 복원됐고 role/scope/ownership 중 무엇이 deny인지 | [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| 브라우저에서만 `/login`으로 튀거나 loop | 세션 전달/redirect 경계 | 다음 요청의 `Cookie` header가 실제로 실렸는지 | 먼저 [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)에서 `redirect / navigation memory`, `cookie-missing`, `server-anonymous` 중 같은 증상 이름을 고른다. 그다음 [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 내려간다 |
| 토큰은 valid한데 운영에서 권한 반영이 늦음 | freshness/전파 | claim/session/cache가 최신 grant를 봤는지 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) -> [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) |

이 표의 목적은 "토큰 종류를 더 외우는 것"이 아니라 "디버깅 시작점을 틀리지 않는 것"이다.

## 한 장으로 보는 세 가지 대표 흐름

| 장면 | 브라우저/클라이언트가 주로 보내는 것 | 서버가 주로 저장하거나 확인하는 것 | permission check 입력 | logout 때 같이 끊어야 하는 것 |
|---|---|---|---|---|
| 전통적인 웹앱 + 서버 세션 | session id cookie | server session, principal, 만료 시각 | role, ownership, tenant, 최신 세션 상태 | browser cookie + server session |
| SPA + BFF | opaque session cookie, CSRF token | BFF session, provider token, downstream token mapping | local session, internal permission, downstream audience | browser session + BFF session + server-side token cache |
| mobile / public API + bearer token | `Authorization: Bearer ...` | token signature, expiry, audience, 필요 시 refresh/revoke 상태 | scope, role, ownership, tenant | access token 저장소 + refresh token/revoke 상태 |

핵심은 `무엇을 보내는가`와 `무엇을 허용하는가`를 분리해서 보는 것이다.

- cookie, session, JWT, BFF는 주로 `인증 결과 전달 방식`이다.
- role, scope, ownership, tenant rule은 주로 `인가 판단 재료`다.

## 로그인부터 권한 검사까지 실제 순서

요청 하나를 서버 기준으로 보면 순서는 거의 항상 같다.

1. 클라이언트가 credential을 보낸다.
2. 서버가 credential을 검증해서 principal을 만든다.
3. 서버가 현재 요청의 session/token 상태를 복원한다.
4. 서버가 resource와 action을 보고 permission check를 한다.
5. 허용하면 처리하고, 아니면 `401` 또는 `403`, 경우에 따라 concealment `404`를 낸다.

여기서 중요한 점은 `3단계와 4단계가 다르다`는 것이다.

- 3단계는 "이 요청이 누구인지 다시 찾는 단계"다.
- 4단계는 "그 사람이 이 행동을 해도 되는지 보는 단계"다.

즉 `valid token`이나 `session exists`만으로는 아직 끝이 아니다.

## 한 요청을 끝까지 따라가는 concrete example

아래처럼 같은 사용자라도 "어느 단계에서 실패했는지"에 따라 결과가 달라진다.

| 시점 | 클라이언트가 보낸 것 | 서버가 본 핵심 | 결과 |
|---|---|---|---|
| 로그인 전 `GET /api/orders/123` | credential 없음 | principal 생성 실패 | `401` 또는 browser에서는 `302 -> /login` |
| 로그인 직후 `GET /api/orders/123` | session cookie / bearer token 있음 | principal 복원 성공, ownership/tenant 검사 통과 | `200` |
| 같은 로그인 상태로 `POST /api/orders/123/refund` | 동일 credential | principal은 있으나 `refund.approve` 권한 없음 | `403` |
| 관리자에서 role 부여 직후 곧바로 재시도 | credential은 같음 | claim/session freshness가 아직 갱신 전일 수 있음 | 일시적 `403` 가능 (freshness 확인 필요) |
| 로그아웃 후 같은 API 재호출 | 무효화된 cookie/token | principal 복원 불가 | 다시 `401` 계열 |

이 표를 기억하면 "로그인됐는데 왜 `403`?", "토큰은 valid인데 왜 실패?" 같은 질문을 단계별로 분해하기 쉽다.

## 브라우저 웹앱에서는 어떻게 보이나

### 1. 로그인

브라우저 기반 웹앱에서는 보통 이런 흐름이 많다.

1. 사용자가 아이디/비밀번호나 social login으로 로그인한다.
2. 서버가 인증에 성공하면 session을 만들고 `Set-Cookie`를 내려보낸다.
3. 브라우저는 다음 요청마다 그 cookie를 자동으로 보낸다.
4. 서버는 session을 읽어 principal을 복원한다.
5. 그다음 route 권한, resource ownership, tenant 경계를 검사한다.

예를 들어 `/admin/users` 요청은 아래 두 검사가 모두 필요하다.

- session이 유효한가
- 그 session의 principal이 관리자 권한을 가졌는가

둘 중 하나라도 빠지면 문제가 된다.

### 2. 로그아웃

브라우저 웹앱에서 logout는 "cookie를 지우면 끝"으로 생각하기 쉽지만, 최소 두 곳을 같이 봐야 한다.

| 끊어야 할 것 | 이유 | 흔한 실수 |
|---|---|---|
| browser cookie | 다음 요청에 옛 session id가 다시 안 가게 해야 함 | 화면만 `/login`으로 보내고 cookie를 안 지움 |
| server session | cookie가 남거나 재사용돼도 principal이 복원되지 않게 해야 함 | cookie만 지우고 서버 session을 남김 |

그래서 browser에서는 로그인 증거가 `자동 전송`된다는 점을 항상 의식해야 한다.

## API와 bearer token 흐름은 어떻게 다른가

브라우저 page 요청과 달리 API client는 보통 token을 직접 붙인다.

1. client가 access token을 발급받는다.
2. 요청마다 `Authorization: Bearer <token>`을 붙인다.
3. API는 서명, 만료, `aud`, issuer를 검증한다.
4. 그다음 scope, role, ownership 같은 application permission을 다시 본다.

여기서 제일 자주 섞이는 오해는 이것이다.

- `token이 valid`하다
- `이 API를 호출해도 된다`

이 둘은 같은 말이 아니다.

예를 들어 `scope=orders.read`가 있어도:

- 모든 주문을 읽을 수 있다는 뜻은 아닐 수 있다.
- 같은 tenant 주문만 허용될 수 있다.
- 본인 주문만 허용되는 ownership rule이 붙을 수 있다.

즉 bearer token은 "누구인지와 기본 권한 힌트"를 전달할 수는 있지만, object-level authorization까지 자동으로 끝내 주지는 않는다.

## SPA + BFF에서는 어디가 달라지나

BFF를 처음 볼 때는 "JWT 대신 cookie를 쓴다" 정도로만 이해하기 쉬운데, 실제 핵심은 `browser에 무엇을 안 보여 줄 것인가`다.

### 가장 단순한 mental model

- browser는 보통 `opaque session cookie`만 본다.
- BFF는 server-side에서 provider token이나 downstream token을 보관한다.
- browser의 요청이 오면 BFF가 local session을 확인하고, 필요하면 서버 측 token으로 downstream API를 대신 호출한다.

즉 BFF는 `세션 번역기`에 가깝다.

| 누가 직접 들고 있나 | 브라우저 직접 token 보관 패턴 | SPA + BFF 패턴 |
|---|---|---|
| access token | browser | 주로 BFF/server |
| refresh token | browser에 두면 위험이 커짐 | 주로 BFF/server |
| app session | 없음 또는 약함 | opaque cookie 기반으로 명확함 |

그래서 BFF를 쓰면 좋아지는 점도 있지만 새 책임도 생긴다.

- browser-visible token surface를 줄일 수 있다.
- 대신 cookie 기반이므로 CSRF, logout propagation, session mapping을 더 엄격하게 설계해야 한다.

초보자 기준에서는 여기까지만 정확히 잡아도 충분하다. 세부 token exchange나 downstream audience 설계는 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 넘기면 된다.

## permission check는 결국 무엇을 보나

로그인과 세션 복원이 끝난 뒤에도 서버는 보통 아래 항목을 조합해 판단한다.

| 검사 항목 | 예시 질문 | 왜 별도로 봐야 하나 |
|---|---|---|
| role | `ADMIN`인가? | 큰 권한 묶음이기 때문이다 |
| scope | `orders.read`가 있는가? | token이 허용한 API 범위일 수 있기 때문이다 |
| ownership | 이 주문의 주인인가? | role/scope만으로 객체 소유권이 해결되지 않기 때문이다 |
| tenant | 같은 조직 데이터인가? | 멀티테넌트 경계는 따로 확인해야 하기 때문이다 |
| freshness | 최근 권한 변경이 반영됐는가? | 로그인 뒤 role이 바뀌었을 수 있기 때문이다 |

이 표에서 가장 중요한 beginner 포인트는 이것이다.

- 인증은 보통 "입장권 확인"이다.
- 인가는 "좌석 구역, 관람 권한, 본인 좌석인지"까지 다시 보는 단계다.

아래처럼 같은 주문 API라도 어떤 축에서 막히는지 이유가 다를 수 있다.

| 요청 | 통과에 필요한 대표 조건 | 왜 하나만으로 부족한가 |
|---|---|---|
| `GET /orders/123` | `order.read` + 같은 tenant + 본인 주문이거나 허용된 지원 관계 | `role`이나 `scope`만으로는 객체 소유권을 설명하지 못한다 |
| `POST /orders/123/refund` | `refund.approve` + 같은 tenant + 필요 시 step-up/MFA | 읽기 권한과 환불 승인 권한은 보통 분리된다 |
| `GET /admin/users` | 관리자 role/permission + 내부 관리 경로 허용 정책 | owner 규칙이 없어도 관리자 기능 여부를 따로 봐야 한다 |

특히 `scope`는 공급자나 게이트웨이 설계에 따라 "API 진입 범위"로만 쓰일 때가 많다. 그래서 `scope가 있다 = 앱 내부 모든 permission check가 끝났다`로 읽으면 위험하다.

## 제일 많이 헷갈리는 문장 6개

- `로그인했으니 관리자 API도 되겠지` -> 아니다. 인증 성공과 관리자 권한은 별도다.
- `cookie가 있으니 로그인 상태다` -> 아니다. cookie가 가도 server session이 없거나 복원에 실패할 수 있다.
- `JWT를 쓰니 세션이 없다` -> 완전히 그렇지 않다. refresh, revoke, claim freshness 때문에 서버 상태가 일부 필요할 수 있다.
- `BFF를 쓰니 CSRF는 사라진다` -> 아니다. browser가 cookie를 자동 전송하면 CSRF 경계는 다시 봐야 한다.
- `scope가 있으니 모든 리소스 접근이 된다` -> 아니다. ownership, tenant, business rule이 남아 있다.
- `logout 버튼을 눌렀으니 어디서나 끝났다` -> 아니다. cookie, server session, refresh family, token cache를 어떤 범위까지 끊는지 봐야 한다.

## browser와 API에서 증상이 다르게 보일 수 있다

| 겉으로 보이는 현상 | 먼저 의심할 것 | 다음 문서 |
|---|---|---|
| 브라우저가 `/login`으로 다시 튄다 | session cookie 미전송, session 만료, redirect UX | [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md), [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) |
| API가 `401`을 준다 | token/session 자체가 없거나 깨짐 | [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| API가 `403`을 준다 | principal은 있지만 권한 부족 | [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| cookie는 있는데 서버가 계속 anonymous다 | cookie scope mismatch, server session miss, BFF mapping 실패 | [Cookie Scope Mismatch Guide](./cookie-scope-mismatch-guide.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) |

## 초보자 체크리스트

인증/세션 설계를 볼 때는 아래 네 줄만 먼저 확인해도 흐름이 많이 정리된다.

1. 로그인 성공 후 클라이언트가 다음 요청에 무엇을 보내는가.
2. 서버는 그 값으로 무엇을 복원하는가.
3. 권한 검사는 role만 보는지, ownership/tenant까지 보는지.
4. logout 시 browser 상태와 server 상태를 어디까지 같이 끊는가.

이 네 줄이 답이 안 나오면 설계가 흐린 경우가 많다.

## 한 줄 정리

인증은 `누구인지 확인`, 세션·쿠키·JWT·BFF는 `그 결과를 다음 요청에 전달하는 경계`, 인가는 `그 요청을 허용할지 판단`이며, login과 logout도 결국 이 세 층을 어디까지 연결하고 끊는지의 문제다.
