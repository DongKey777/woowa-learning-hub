# Beginner Guide to Auth Failure Responses: `401` / `403` / `404`

> 한 줄 요약: 먼저 `인증이 성립했는가?`를 보고, 그다음 `권한이 충분한가?`를 보고, 마지막으로 `존재를 숨길 정책인가?`를 보면 `401`, `403`, `404`를 초보자도 일관되게 구분할 수 있다.

**난이도: 🟢 Beginner**

> 문서 역할: 이 문서는 security 카테고리 안에서 `401` / `403` / `404`를 처음 분리할 때 여는 beginner `primer`다. browser redirect 혼선은 `[primer bridge]`로, concealment `404`는 beginner용 `[primer bridge]`를 한 번 거친 뒤 `deep dive`로, stale deny/cache 수렴 문제는 별도 `[primer bridge]`로 handoff한다.

> `1차 질문(고정)`: Network에서 `OPTIONS`만 실패하고 actual `GET`/`POST`가 없나, 아니면 actual request가 실제로 보이나?

관련 문서:
- [인증과 인가의 차이](./authentication-vs-authorization.md)
- [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md)
- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [Preflight Debug Checklist](./preflight-debug-checklist.md#symptom-first-branch-table-cors-vs-auth)
- [Error-Path CORS Primer](./error-path-cors-primer.md)
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)
- [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)
- [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)
- [Spring ProblemDetail / Error Response Design](../spring/spring-problemdetail-error-response-design.md)

retrieval-anchor-keywords: 401 403 404 beginner guide, 401 vs 403 vs 404, auth failure response, response code primer, actual request vs preflight, browser 401 vs 302, concealment 404, stale deny 403, 로그인 됐는데 왜 403, token valid but 403, 남의 주문인데 왜 404, 권한 줬는데 404 계속, auth failure response 401 403 404 basics, auth failure response 401 403 404 beginner, auth failure response 401 403 404 intro

## 이 문서 다음에 보면 좋은 문서

- `[catalog]` 응답 코드 질문에서 시작했지만 다른 auth 증상으로 다시 고르고 싶으면 [Security README: 증상별 바로 가기](./README.md#증상별-바로-가기)로 돌아가 category route를 다시 잡으면 된다.
- `[primer bridge]` 브라우저 콘솔이 CORS라고 말하고 Network에는 `OPTIONS`만 실패한 채 actual request가 안 보이면, 이 문서의 `401` / `403` / `404` 의미를 읽기 전에 [Preflight Debug Checklist](./preflight-debug-checklist.md)에서 preflight failure와 actual auth failure를 먼저 분리하는 편이 안전하다.
- `[primer]` 아직 `인증`과 `인가`의 차이가 흐리면 [인증과 인가의 차이](./authentication-vs-authorization.md)로 돌아가 `principal`, `session`, `permission model`부터 다시 맞추면 된다.
- `[primer bridge]` raw `401`을 기대했는데 브라우저에서는 `302 -> /login`이나 login HTML이 보여 더 헷갈리면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)로 가서 browser redirect와 API 계약을 먼저 분리하면 된다.
- `[primer bridge]` 권한을 방금 줬는데 `404`가 계속 남아 cached concealment처럼 보이면, deep dive로 바로 내려가기 전에 이 문서의 [Symptom-First Branch Table (CORS vs Auth)](#symptom-first-branch-table-cors-vs-auth)와 `beginner route handoff map`에서 먼저 `actual request` 여부와 stale deny branch를 다시 고정한 뒤 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 간다.

## concealment와 설계로 내려갈 때

- `[primer bridge]` `404`가 `진짜 없음`, `숨김 404`, `grant 직후 stale deny` 중 무엇인지부터 먼저 가르고 싶으면 [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)로 이어 간다.
- `[deep dive]` "다른 사람 리소스에 왜 `403`이 아니라 `404`를 줄 수 있지?"가 더 궁금하면 [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)에서 entry cue를 먼저 잡은 뒤 [IDOR / BOLA Patterns and Fixes: `403` vs 의도적 `404` 30초 분기표](./idor-bola-patterns-and-fixes.md#30초-분기표-idor에서-403-vs-의도적-404)로 바로 내려가 객체 단위 concealment 기준만 먼저 본다.
- `[deep dive]` gateway, filter, app이 각각 어디서 `401` / `403` / `404`를 내야 하는지 설계로 보고 싶으면 [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)로 이어진다.

## stale deny와 운영 심화로 내려갈 때

- `[primer bridge]` 권한을 방금 줬는데도 `403`이나 concealment `404`가 남는 운영 문제는 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)에서 claim refresh와 stale deny cache를 먼저 나눈다.
- `[deep dive]` cache/convergence까지 직접 파고들어야 하면 바로 이어서 [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) -> [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md) 순으로 내려간다.
- `[deep dive]` 특정 tenant에서만 `403`이 반복되거나 같은 실패가 `401`/`404` 사이에서 흔들리면 이 문서로 응답 의미를 먼저 고정한 뒤, beginner route는 그대로 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) 순으로 이어 보면 된다.

## AuthZ / Tenant survey로 안전하게 복귀하는 20초 출구

이 문서는 응답 코드 의미를 고정하는 `[primer]`다. side detour를 끝냈다면 아래처럼 `main chain`에 다시 붙이면 된다.

| 여기서 막 고정한 것 | 안전한 다음 문서 | role cue |
|---|---|---|
| `401`은 authn failure라는 점 | `[primer]` [인증과 인가의 차이](./authentication-vs-authorization.md) | authn/authz 경계 primer로 복귀 |
| `403`인데 권한 부여 직후라 freshness가 의심되는 점 | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | beginner handoff bridge |
| `404`가 진짜 없음인지 concealment인지 헷갈리는 점 | `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) | concealment 분기 bridge |
| `403/404`가 tenant나 ownership 문맥에서만 흔들리는 점 | `[primer bridge]` [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md) | tenant branch bridge |
| 다음 갈래 자체를 다시 고르고 싶은 점 | `[survey]` [Security README: AuthZ / Tenant / Response Contracts](./README.md#authz--tenant--response-contracts-deep-dive-catalog) | main survey 복귀 |

짧게 기억하면:

- `401` detour 뒤에는 authn/authz primer로 복귀한다.
- `403` detour 뒤에는 grant-freshness bridge로 복귀한다.
- `404` detour 뒤에는 concealment bridge로 복귀한다.
- tenant 냄새가 나면 tenant/session bridge로 복귀한다.
- 갈래가 다시 넓어지면 survey anchor로 돌아간다.

## beginner route handoff map

| 지금 헷갈리는 것 | 여기서 먼저 고정할 것 | 다음 handoff |
|---|---|---|
| raw `401`을 기대했는데 browser에서는 `302 -> /login`이나 login HTML이 보임 | `401`은 authn failure이고, `302`는 그 실패를 browser UX로 감싼 것일 수 있다는 점 | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) -> `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) |
| `404`가 진짜 없음인지, 숨김 `404`인지, grant 직후 stale deny인지부터 헷갈림 | beginner는 외부 `404` 하나만 보고 내부 reason을 단정하지 말고 `없음 / 숨김 / stale` 세 갈래를 먼저 자른다는 점 | `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) |
| 권한을 방금 준 뒤인데 `404`가 계속 남아 "진짜 concealment 정책"인지 "stale cache"인지 헷갈림 | 권한 변경 직후 `404`는 concealment deep dive로 단정하지 말고, 먼저 이 문서의 `Symptom-First` 분기와 grant freshness 분기를 다시 확인해야 한다는 점 | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) |

## concealment와 stale deny handoff map

| 지금 헷갈리는 것 | 여기서 먼저 고정할 것 | 다음 handoff |
|---|---|---|
| 다른 사람 리소스에서 왜 `403`이 아니라 `404`를 줄 수 있는지 헷갈림 | 존재 concealment는 `404` body를 평평하게 유지하고 내부 reason만 숨기는 policy라는 점 | `[primer bridge]` [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) -> `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md) -> `[deep dive]` [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md) |
| 권한을 줬는데 still `403`, 특정 tenant에서만 `403`, cached concealment `404`가 남음 | `grant 저장`과 `현재 요청이 새 allow를 봄`은 다른 단계이고, stale deny가 남으면 tenant별로도 증상이 갈릴 수 있다는 점 | `[primer bridge]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) |

## graph deep dive로 바로 안 가는 기준

> [beginner escalation gate]
> 기본 승격 순서는 `[primer bridge]` stale-deny 분기 확인 -> `[deep dive]` runtime debugging -> `(증거가 명확할 때만)` graph deep dive다.
>
> `Authorization Graph Caching`으로 바로 점프하는 조건:
> - `decision log`나 trace에 `graph snapshot/version` mismatch가 직접 보인다
> - `relationship edge invalidation` 실패가 로그나 재현으로 확인된다
> - 같은 `principal + object`가 graph refresh 전후에만 다르게 판정되는 증거가 있다
>
> 아직 이런 증거가 없다면:
> - 문서 역할 기준으로 현재 필요한 것은 graph internals 설명이 아니라 `[deep dive]` runtime debugging이다
> - 초급 분기에서는 `cache 의심`과 `graph 원인 확정`을 같은 말로 취급하지 않는다

---

## 먼저 10초 분기표

이 표는 [Preflight Debug Checklist](./preflight-debug-checklist.md#먼저-10초-분기표)와 같은 질문 순서, 같은 용어로 유지한다.

### Symptom-First Branch Table (CORS vs Auth)

두 문서([Preflight Debug Checklist](./preflight-debug-checklist.md#symptom-first-branch-table-cors-vs-auth), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md#symptom-first-branch-table-cors-vs-auth))에서 같은 분기표를 유지한다.

`1차 질문(고정)`: Network에서 `OPTIONS`만 실패하고 actual `GET`/`POST`가 없나, 아니면 actual request가 실제로 보이나?

## 먼저 10초 분기표 (계속 2)

| Network에서 보이는 장면 | 먼저 읽는 뜻 | 첫 액션 | 다음 문서 |
|---|---|---|---|
| `OPTIONS /api/orders`만 있고 `POST /api/orders`가 없다 | preflight failure라서 actual request가 안 나갔다 | CORS/preflight 설정, `OPTIONS` 허용, proxy 차단부터 본다 | [Preflight Debug Checklist](./preflight-debug-checklist.md#먼저-10초-분기표) |
| `OPTIONS`는 `200`/`204`, 그 다음 `POST`가 `401` | preflight는 통과했고 actual auth failure가 났다 | token/session 유효성부터 확인한다 | 이 문서의 `actual request가 보일 때 읽는 10초 판별표` |
| `OPTIONS`는 `200`/`204`, 그 다음 `POST`가 `403` | actual request는 갔고 authz deny가 났다 | permission/ownership/scope를 확인한다 | 이 문서의 `actual request가 보일 때 읽는 10초 판별표` |
| 콘솔에는 CORS 에러인데 Network에는 actual `POST` `401`도 보인다 | 실제 auth failure가 CORS 누락으로 가려졌을 수 있다 | error path CORS header 누락과 auth 원인을 같이 본다 | [Error-Path CORS Primer](./error-path-cors-primer.md) |
| Postman/curl은 되는데 브라우저만 실패하고 Network에 `OPTIONS`가 보인다 | browser-only preflight/CORS 문제일 가능성이 높다 | 브라우저 preflight와 응답 헤더를 본다 | [Preflight Debug Checklist](./preflight-debug-checklist.md#먼저-10초-분기표) |

공통 오해 1개만 먼저 고정하면 분기 실수가 크게 줄어든다.

- `OPTIONS 401/403`은 보통 "preflight 차단"으로 먼저 읽는다.
- actual `GET/POST 401/403`이 확인될 때만 "auth failure"로 읽는다.

---

## 30초 DevTools Network 미니 예시 (공통)

아래 3칸만 보면 초보자도 preflight lane과 auth lane을 바로 분리할 수 있다.

> 30초 mental model:
> `status` 숫자를 먼저 읽지 말고 `요청 method` -> `실제 요청 존재 여부` -> actual request의 `status` 순서로 본다.

| 장면 | 요청 method | 실제 요청 존재 여부 | 지금 읽는 status | 1차 결론 |
|---|---|---|---|---|
| 예시 A | `OPTIONS` | 같은 path의 `POST /api/orders`가 없음 | `401` | actual API는 아직 안 나갔다. preflight 차단으로 먼저 읽는다 |
| 예시 B | `OPTIONS` 다음에 `POST /api/orders`가 있음 | actual request가 실제로 보임 | `POST`의 `401` | preflight는 통과했고 actual auth failure를 봐야 한다 |

초보자용 한 줄 해석:

- `OPTIONS 401`만 보고 인증 실패로 단정하지 않는다.
- 같은 path의 actual `GET`/`POST`가 실제로 보일 때만 그 요청의 `401`/`403`/`404`를 auth 의미로 읽는다.

헷갈리면 읽는 순서를 고정하면 된다.

1. `요청 method`가 `OPTIONS`인지 먼저 본다.
2. 같은 path의 actual `POST`/`GET`이 뒤에 실제로 생겼는지 본다.
3. actual request가 있을 때만 그 request의 `status`를 `401`/`403`/`404` 의미로 읽는다.

초보자가 가장 많이 하는 실수는 `status 401`만 먼저 보고 "`인증 실패네`"라고 단정하는 것이다.
이 문서와 [Preflight Debug Checklist](./preflight-debug-checklist.md#30초-devtools-network-미니-예시-공통)는 같은 3칸을 같은 순서로 보게 만들어 preflight와 actual auth failure를 덜 섞게 한다.

---

## 첫 읽기 90초 경로

문서가 길어서 처음에는 아래 3단계만 먼저 읽어도 된다.

1. `Symptom-First Branch Table (CORS vs Auth)`에서 `1차 질문(고정)`: Network에서 `OPTIONS`만 실패하고 actual `GET`/`POST`가 없나, 아니면 actual request가 실제로 보이나?
2. `같은 endpoint도 상태에 따라 코드가 바뀐다` 표로 "URL이 아니라 요청 맥락"이라는 점을 고정한다.
3. `실전에서 바로 쓰는 판단 체크리스트`로 구현 순서를 확정한다.

운영/설계 심화가 필요할 때만 아래로 내려간다.

- 외부 에러 body와 내부 로그 분리 설계는 `안전한 에러 body 예시와 내부 로그 매핑`
- gateway/app 일관성 같은 운영 contract는 `운영에서 놓치지 말아야 할 2가지`

---

## actual request가 보일 때 읽는 10초 판별표

| 먼저 확인할 질문 | 대표 예시 | 바깥 응답 | 클라이언트가 보통 해야 할 일 |
|---|---|---|---|
| 인증 정보가 없거나 깨졌나? | 로그인 안 함, 만료 토큰, 잘못된 서명, 깨진 세션 쿠키 | `401 Unauthorized` | 다시 로그인, 토큰 갱신, 인증 정보 재전송 |
| 누구인지는 알겠지만 권한이 부족한가? | 일반 사용자가 관리자 API 호출, scope 부족 | `403 Forbidden` | 권한 요청, role 확인, 요청 자체 중단 |
| 리소스가 없거나 존재를 숨겨야 하나? | 없는 주문 번호, 다른 사람 주문 번호, cross-tenant invoice | `404 Not Found` | ID 확인, concealment 정책인지 확인 |

초보자에게 가장 중요한 한 줄은 이것이다.

- `401`: `누구인지 다시 증명해라`
- `403`: `누구인지는 알겠는데 너는 안 된다`
- `404`: `없거나, 있다고 말해주지 않겠다`

`401 Unauthorized`라는 이름 때문에 `403`과 헷갈리기 쉽지만, 실무에서는 대체로 `인증 실패` 쪽에 쓴다고 기억하면 된다.
브라우저 page 요청에서는 이 `401` 상황이 raw 숫자 대신 `302 -> /login`으로 감싸져 보일 수 있는데, 그 차이는 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 따로 정리한다.

## 15초 결정 흐름: 무엇을 먼저 시도할까

| 현재 관찰 | 1차 행동 | 다음 분기 |
|---|---|---|
| `401` 또는 browser `302 -> /login` | 재로그인/토큰 갱신 먼저 | 계속 실패하면 credential 전달 경로(session cookie, bearer header) 점검 |
| `403` | 권한/역할/소유권 확인 먼저 | 권한 변경 직후라면 freshness/캐시 수렴 단계 점검 |
| `404` | ID 오타/리소스 부재 먼저 확인 | user-owned/tenant 리소스면 concealment policy 가능성 점검 |

초보자 기준에서는 "코드 해석"보다 "첫 행동"을 틀리지 않는 것이 더 중요하다.

## 자주 들어오는 한국어 질문으로 바로 연결하기

authz primer 문서들에서 자주 쓰는 질문 문장을 이 문서의 상태 코드 해석에 맞춰 먼저 정렬하면 초보자 진입이 훨씬 안정된다.

| 학습자가 실제로 자주 묻는 말 | 먼저 잡을 mental model | 이 문서에서 먼저 보는 위치 | 다음 문서 |
|---|---|---|---|
| `로그인 됐는데 왜 403` | 인증은 통과했고, role/permission/scope/ownership 중 하나가 막고 있을 가능성이 크다 | `30초 분기표: 4단계 gate로 401/403/404 고정하기` | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md) |
| `토큰은 유효한데 403이 나요` | `유효한 토큰`은 `401이 아니라는 뜻`에 가깝고, 아직 `허용된 요청`이라는 뜻은 아니다 | `actual request가 보일 때 읽는 10초 판별표`, `30초 분기표` | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md), [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `scope 있는데 왜 남의 주문을 못 봐요?` | scope는 API 범위이고, ownership은 특정 객체 접근 규칙이라서 `scope 있음`과 `이 객체 허용`은 같은 말이 아니다 | `30초 분기표`, `같은 endpoint도 상태에 따라 코드가 바뀐다` | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md), [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md), [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md) |

## 다른 사람 리소스와 stale deny 질문은 이렇게 다시 읽는다

| 학습자가 실제로 자주 묻는 말 | 먼저 잡을 mental model | 이 문서에서 먼저 보는 위치 | 다음 문서 |
|---|---|---|---|
| `내 것만 되는데 남의 것은 안 돼요` | authn은 됐고, object gate에서 ownership/tenant/context가 갈린다 | `30초 분기표`, `같은 endpoint도 상태에 따라 코드가 바뀐다` | [Permission Model Bridge: AuthN에서 Role/Scope/Ownership로 넘어가기](./permission-model-bridge-authn-to-role-scope-ownership.md), [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) |
| `남의 주문인데 왜 404` | 객체 맥락 deny를 외부에서 concealment `404`로 감쌀 수 있다 | `actual request가 보일 때 읽는 10초 판별표`, `같은 endpoint도 상태에 따라 코드가 바뀐다` | [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) -> [IDOR / BOLA Patterns and Fixes: `403` vs 의도적 `404` 30초 분기표](./idor-bola-patterns-and-fixes.md#30초-분기표-idor에서-403-vs-의도적-404) |
| `권한을 방금 줬는데 왜 아직 403/404죠?` | grant 저장과 현재 요청 경로가 새 권한을 반영하는 시점은 다를 수 있다 | `15초 결정 흐름`, `20초 선행 확인`, `30초 분기표` | [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) |

## 한국어 질문을 한 줄 규칙으로 다시 묶기

짧게 묶으면 아래처럼 기억하면 된다.

- `로그인 됐는데 403`이면 `401`이 아니라 authz gate를 본다.
- `유효한 토큰인데 403`이면 `토큰 검증`보다 `role/scope/ownership 중 어디가 막는지`를 먼저 본다.
- `scope 있는데 남의 주문 못 봄`이면 scope와 ownership을 분리한다.
- `내 것만 되는데 남의 것은 안 됨`이면 object gate가 살아 있다는 뜻으로 읽고 ownership/tenant/context를 본다.
- `남의 주문인데 왜 404`면 진짜 없음과 concealment policy 둘 다 열어 둔다.
- `없는 줄 알았는데 남의 리소스였다`처럼 들리면 먼저 [Concealment `404` Entry Cues](./concealment-404-entry-cues.md)에서 `진짜 없음 / 숨김 / stale` 세 갈래를 고정한 뒤 [IDOR / BOLA Patterns and Fixes: `403` vs 의도적 `404` 30초 분기표](./idor-bola-patterns-and-fixes.md#30초-분기표-idor에서-403-vs-의도적-404)로 바로 내려간다.

## 한 번에 고정하는 미니 비교: `유효한 토큰`과 `허용된 요청`은 다르다

초보자는 아래 두 문장을 같은 뜻으로 읽기 쉽다.

- `토큰이 유효하다`
- `이 요청이 허용된다`

하지만 auth failure guide와 authz primer들은 둘을 분리해서 쓴다.

| 지금 확인한 사실 | 아직 모르는 것 | 바깥에서 흔한 응답 |
|---|---|---|
| 토큰 서명/만료가 정상이라 principal을 만들 수 있다 | 이 principal이 필요한 role/permission을 가졌는가 | authz gate에서 막히면 `403` |
| `scope=orders.read`가 있다 | 이 사용자가 `orders/123` 같은 특정 객체를 읽어도 되는가 | ownership/concealment gate에서 `403` 또는 `404` |
| 로그인 세션이 살아 있다 | 현재 tenant/workspace 문맥이 맞는가 | tenant/context mismatch면 `403` 또는 concealment `404` |

한 줄로 줄이면:

- `유효한 토큰`은 보통 `401`을 넘겼다는 뜻이다.
- 그다음부터는 `허용 여부`를 role/scope/ownership 순서로 다시 봐야 한다.

## 30초 분기표: 4단계 gate로 `401` / `403` / `404` 고정하기

먼저 mental model을 한 줄로 고정한다.

- `인증(AuthN) -> 권한(Role/Permission) -> 위임 범위(Scope) -> 객체 맥락(Ownership/Tenant)` 순서로 본다.

아래 표에서 "처음 실패한 gate"를 찾으면 첫 진단 혼동이 크게 줄어든다.

| gate (30초 안에 보는 순서) | 실패 신호(초보자 체크 포인트) | 바깥 응답 기본값 | 첫 액션 |
|---|---|---|---|
| 1. AuthN gate (`누구인지 증명`) | token/session 없음, 만료/서명 오류, principal 생성 실패 | `401` | 재로그인, 토큰 갱신, credential 전달 경로 점검 |
| 2. Role/Permission gate (`이 기능을 할 자격`) | principal은 있는데 필요한 role/permission 없음 | `403` | 권한 요청 또는 권한 모델 확인 |
| 3. Scope gate (`이 토큰이 이 호출을 위임받았는가`) | 로그인은 됐지만 token scope 부족 (`read`만 있는데 `write` 호출) | `403` | 올바른 scope로 재발급/재인증 |
| 4. Ownership/Tenant gate (`이 객체를 다룰 수 있는가`) | 남의 리소스, tenant 불일치, 객체 단위 정책 불일치 | `403` 또는 concealment `404` | ID/tenant 확인 후 concealment 정책 문서 기준으로 판단 |

짧은 기억법:

- `1번에서 실패하면 바로 401`
- `2~4번에서 실패하면 기본 403`
- `4번(객체 맥락) 실패에서 존재 노출을 막는 정책이면 외부는 404`

## 20초 선행 확인: 이 코드가 actual 요청 결과인가

browser에서는 preflight/CORS나 login redirect 때문에 auth failure 코드가 왜곡되어 보일 수 있다.

| 관찰 | 의미 | 먼저 할 일 |
|---|---|---|
| Network에 `OPTIONS`만 있고 actual `GET/POST`가 없음 | auth 코드 해석 전 단계(CORS/preflight)에서 멈춘 것일 수 있음 | [Preflight Debug Checklist](./preflight-debug-checklist.md)부터 확인 |
| API client는 `401`인데 브라우저는 `/login` HTML | 같은 authn failure가 browser UX에서 `302`로 감싸진 것일 수 있음 | [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md) 확인 |
| gateway와 app에서 코드가 다름 | contract 불일치로 triage가 흔들림 | 이 문서의 response matrix 기준으로 한 곳에서 먼저 정규화 |

---

## 같은 실패가 browser와 API에서 다르게 보이는 20초 예시

같은 "인증 실패"라도 소비자가 browser인지 API client인지에 따라 겉모습이 달라질 수 있다.

| 실제 내부 상태 | API client에서 보이는 것 | browser page에서 보이는 것 | 초보자 해석 |
|---|---|---|---|
| session/token 없음 | `401` JSON body | `302 -> /login` 또는 login HTML | 둘 다 authn failure일 수 있다 |
| principal은 있으나 권한 없음 | `403` JSON body | `403` page 또는 권한 없음 UI | 재로그인보다 권한 경로를 본다 |
| concealment policy deny | `404` JSON body | `404` page | 진짜 없음/숨김을 외부에서 구분하지 않는다 |

즉 숫자 하나만 보지 말고, "현재 누가 소비하는 응답인가(API vs browser)"를 같이 확인해야 해석이 안정된다.

---

## 같은 endpoint도 상태에 따라 코드가 바뀐다

`/api/orders/ord_123/refund` 같은 동일 endpoint를 예로 들면, 코드 선택은 URL이 아니라 "현재 인증/인가 상태"에 따라 달라진다.

| 같은 요청이지만 현재 상태가 다름 | 내부 판단 | 외부 응답 |
|---|---|---|
| credential 없음 | `MISSING_CREDENTIAL` | `401` |
| principal은 있음, `refund.approve` 권한 없음 | `INSUFFICIENT_PERMISSION` | `403` |
| principal은 있지만 다른 tenant 주문이고 concealment policy 활성 | `OWNERSHIP_OR_TENANT_MISMATCH` | `404` |
| principal/권한/정책 모두 허용 | `ALLOW` | `200` 또는 `204` |

초보자에게 중요한 포인트는 하나다.

- `401`/`403`/`404`는 "엔드포인트 종류"가 아니라 "현재 요청 맥락"에 따라 달라진다.

---

## 인증(authn)과 인가(authz)를 HTTP 응답으로 연결하기

[인증과 인가의 차이](./authentication-vs-authorization.md)에서 본 흐름을 다시 가져오면 순서는 이렇다.

1. credential, session, token으로 `인증`을 시도한다.
2. 성공하면 현재 요청의 `principal`이 만들어진다.
3. principal과 resource, action을 가지고 `인가`를 판단한다.
4. 마지막으로 concealment policy가 있으면 외부 응답을 `404`로 바꿀 수 있다.

즉 질문 순서가 중요하다.

- 인증이 아직 안 됐으면 `403`까지 갈 수 없다.
- 인증은 됐는데 권한이 부족하면 `401`이 아니라 `403`에 가깝다.
- 권한 부족이라도 리소스 존재를 숨길 정책이면 외부에는 `404`를 줄 수 있다.

---

## 초보자용 예시 3개

### 1. `401`: 로그인 안 했거나 인증 정보가 깨졌다

예시:

- `Authorization` 헤더 없이 `GET /api/me` 호출
- 만료된 bearer token으로 `GET /api/orders`
- 세션 쿠키가 만료된 상태로 `POST /profile`

왜 `401`인가:

- 서버가 아직 `이 요청이 누구인지` 확정하지 못했다.
- 즉 principal을 만들 수 없거나, 기존 인증 상태를 신뢰할 수 없다.

클라이언트 힌트:

- 다시 로그인하거나 token refresh를 시도한다.
- API라면 `WWW-Authenticate: Bearer ...` 같은 challenge가 같이 갈 수 있다.

### 2. `403`: 로그인은 됐지만 허용되지 않는다

예시:

- `USER` role 계정이 `GET /admin/reports` 호출
- `read:orders`만 있는 token으로 `POST /orders/approve`
- 같은 tenant 사용자는 맞지만 `refund.approve` permission이 없음

왜 `403`인가:

- 서버는 principal을 알고 있다.
- 하지만 role, scope, policy, ownership 조건 중 하나가 허용되지 않았다.

클라이언트 힌트:

- 재로그인만으로 해결되지 않는 경우가 많다.
- 권한 요청, 관리자 승인, 더 높은 assurance step-up이 필요한지 봐야 한다.

### 3. `404`: 진짜 없거나, 있어도 있다고 말하지 않는다

예시:

- `GET /orders/999999`인데 진짜 없는 주문 번호
- 사용자 A가 사용자 B의 주문 `GET /orders/123` 시도
- 다른 tenant의 invoice id를 넣었고, 이 서비스는 객체 존재를 숨기기로 한 상태

왜 `404`인가:

- 진짜 없는 경우일 수도 있다.
- 또는 "있다/없다" 자체가 민감해서 존재를 숨기기로 한 security policy일 수도 있다.

클라이언트 힌트:

## 초보자용 예시 3개 (계속 2)

- 입력한 ID가 맞는지 먼저 본다.
- user-owned resource나 multi-tenant resource라면 concealment `404`일 가능성도 같이 본다.
- "남의 주문인데 왜 `403`이 아니라 `404`지?"가 바로 궁금하면 [Concealment `404` Entry Cues](./concealment-404-entry-cues.md) 다음에 [IDOR / BOLA Patterns and Fixes: `403` vs 의도적 `404` 30초 분기표](./idor-bola-patterns-and-fixes.md#30초-분기표-idor에서-403-vs-의도적-404)로 바로 간다.
- 권한 변경 직후에만 `404`가 남는다면 concealment deep dive보다 먼저 이 문서의 `Symptom-First Branch Table`로 되돌아가고, stale branch가 맞으면 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 이어 간다.

---

## 제일 자주 틀리는 판단 순서

### 1. token이나 session이 깨졌는데 `403`을 준다

문제:

- 사실은 인증 실패인데 권한 부족처럼 보인다.

왜 나쁜가:

- 클라이언트가 권한 요청 화면을 띄우거나, 운영자가 role 문제로 잘못 추적한다.

더 나은 기준:

- missing token
- expired token
- invalid signature
- malformed credential

위 네 가지는 보통 `401` bucket에 먼저 넣는다.

### 2. 로그인된 사용자의 권한 부족을 `401`로 준다

문제:

- principal은 이미 확인됐는데, 모든 deny를 `401`로 내려 버린다.

왜 나쁜가:

- 사용자는 계속 다시 로그인하지만 결과가 안 바뀐다.
- 브라우저 앱에서는 login loop처럼 보일 수 있다.

더 나은 기준:

- principal이 있고 policy deny라면 기본값은 `403`으로 본다.

### 3. 다른 사람 리소스 조회에 무조건 `403`을 준다

문제:

- 공격자가 "그 주문 번호는 실제로 존재한다"는 힌트를 얻는다.

더 나은 기준:

- user-owned resource, multi-tenant detail endpoint처럼 존재 노출이 민감하면 `404` concealment를 검토한다.
- 대신 내부 로그에는 실제 이유를 남긴다.

### 4. `404`를 아무 데나 섞어 쓴다

문제:

- 어떤 endpoint는 `403`, 어떤 endpoint는 `404`라서 클라이언트 계약이 흔들린다.

더 나은 기준:

- `404` concealment는 `리소스 클래스 단위 정책`으로 정한다.
- 예를 들어 "사용자 개인 주문 상세는 concealment `404`, 관리자 콘솔 privilege 부족은 `403`"처럼 문서화한다.

### 5. 외부 응답 본문에 너무 많은 정보를 넣는다

문제:

- `order 123 exists but belongs to user 42` 같은 메시지는 정보 노출이다.

더 나은 기준:

- 외부 응답은 짧고 표준화한다.
- 내부 로그에는 실제 deny reason을 남긴다.

### 6. personalized deny를 캐시해 버린다

문제:

- 사용자별 `403` / `404`가 다른 사람에게 재사용될 수 있다.
- stale deny 때문에 권한을 줬는데도 `403`이나 concealment `404`가 계속 남을 수 있다.

더 나은 기준:

- auth-dependent deny 응답은 cache policy를 보수적으로 둔다.
- 이 이슈는 운영 관점에서 [Authorization Caching / Staleness](./authorization-caching-staleness.md)로 이어서 본다.

---

## 실전에서 바로 쓰는 판단 체크리스트

1. credential이나 session이 유효한가?
2. principal이 실제로 만들어졌는가?
3. role, scope, ownership, tenant policy가 허용하는가?
4. 이 리소스 클래스는 존재를 숨기기로 했는가?

이 순서로 보면 대부분 정리된다.

- 1번에서 실패하면 `401`
- 1번은 통과했고 3번에서 실패하면 기본값은 `403`
- 3번에서 실패했더라도 4번 concealment policy가 있으면 외부에는 `404`

초보자는 특히 `1번에서 이미 실패했는데 3번까지 판단하려는 습관`을 끊는 것이 중요하다.

---

## response matrix 예시

| 상황 | 내부 판단 | 외부 응답 |
|---|---|---|
| bearer token 없음 | `MISSING_CREDENTIAL` | `401` |
| bearer token 만료 | `INVALID_CREDENTIAL` | `401` |
| 로그인은 됐지만 관리자 role 없음 | `ADMIN_ROLE_REQUIRED` | `403` |
| 로그인은 됐지만 `write:orders` scope 없음 | `INSUFFICIENT_SCOPE` | `403` |
| 다른 사람 주문 상세 접근, concealment policy 있음 | `OWNERSHIP_MISMATCH` | `404` |
| 요청한 리소스가 진짜 없음 | `RESOURCE_MISSING` | `404` |

핵심은 `외부 상태 코드보다 내부 reason taxonomy를 먼저 고정`하는 것이다.

---

## 안전한 에러 body 예시와 내부 로그 매핑

status code만 맞는다고 계약이 끝나는 것은 아니다.
외부 body는 `다음에 무엇을 해야 하는지`만 알려 주고,
실제 실패 원인 분류는 내부 log와 trace에서만 복원 가능하게 두는 편이 안전하다.

외부 body의 최소 공통 필드는 보통 이 정도면 충분하다.

- `type`: 문서화 가능한 stable problem type
- `title`: 사람이 읽는 짧은 제목
- `status`: HTTP status
- `code`: 클라이언트 계약용 stable application code
- `detail`: 복구 힌트는 주되 내부 판단 근거는 숨긴 짧은 설명
- `request_id`: 지원팀, log, trace와 조인할 키

내부 log는 최소한 아래 세 필드를 외부 body와 맞춰 두는 편이 좋다.

- `request_id`
- `http_status`
- `external_code`

그래야 support, SIEM, trace가 같은 실패를 한 번에 묶을 수 있다.

## 초급자용 최소 JSON 템플릿 카드

처음 만들 때는 "많이 넣는 것"보다 "같은 모양을 유지하는 것"이 더 중요하다.

- `401`은 다시 인증하라는 힌트만 남긴다.
- `403`은 권한이 부족하다는 사실만 남긴다.
- `404`는 진짜 없음과 숨김 `404`를 같은 몸체로 유지한다.

| 상태 | 언제 복붙하나 | 최소 JSON 템플릿 |
|---|---|---|
| `401` | 로그인 안 함, 만료 토큰, 깨진 세션처럼 `누구인지`를 못 믿을 때 | `{"type":"https://api.example.com/problems/authentication-required","title":"Authentication required","status":401,"code":"AUTHENTICATION_REQUIRED","detail":"Sign in again or refresh your credentials, then retry the request.","request_id":"req_7V1p4rM2"}` |
| `403` | 로그인은 됐지만 role, permission, scope, ownership 조건이 막을 때 | `{"type":"https://api.example.com/problems/insufficient-permission","title":"Forbidden","status":403,"code":"INSUFFICIENT_PERMISSION","detail":"This account cannot perform this action. Request access if you believe it is required.","request_id":"req_C83mP2Q9"}` |
| `404` | 진짜 리소스 없음이거나, 있어도 있다고 말하지 않기로 한 concealment 정책일 때 | `{"type":"https://api.example.com/problems/resource-not-found","title":"Not Found","status":404,"code":"RESOURCE_NOT_FOUND","detail":"The requested resource was not found. Verify the identifier or reopen it from a list you can access.","request_id":"req_N4m8L0T1"}` |

## stable code 네이밍 미니 규칙 카드

mental model은 단순하다.

- `code`는 화면 문구가 아니라 `클라이언트 계약용 라벨`이다.
- 그래서 문장이 아니라 `시간이 지나도 덜 바뀌는 이름`으로 잡아야 한다.

5줄로만 기억하면 아래면 충분하다.

| 규칙 | 왜 이렇게 두나 | 짧은 예시 |
|---|---|---|
| `UPPER_SNAKE_CASE`로 쓴다 | 로그, JSON, 문서에서 한눈에 같은 코드로 보인다 | `AUTHENTICATION_REQUIRED` |
| 현재 현상이 아니라 `안정적인 실패 종류`를 적는다 | 문구나 구현이 바뀌어도 계약은 덜 흔들린다 | `TOKEN_EXPIRED`보다 범용 `INVALID_CREDENTIAL`을 먼저 검토 |
| UI 문장 대신 `원인 축`을 짧게 적는다 | 번역/톤 변경과 계약을 분리할 수 있다 | `PLEASE_LOGIN_AGAIN` 대신 `AUTHENTICATION_REQUIRED` |
| status와 같은 말을 반복하지 말고 `왜 막혔는지`를 남긴다 | `403`만 보고는 원인 분류가 안 되기 때문이다 | `FORBIDDEN`보다 `INSUFFICIENT_PERMISSION` |
| 너무 세밀한 내부 사유는 빼고, 외부에 약속할 수준까지만 고정한다 | 내부 정책 변경이 code churn으로 번지는 것을 막는다 | `TENANT_POLICY_RULE_17_DENY` 대신 `OWNERSHIP_MISMATCH` |

처음엔 아래 비교만 피해도 품질이 크게 오른다.

| 덜 안정적 | 더 안정적 |
|---|---|
| `LOGIN_FAILED` | `AUTHENTICATION_REQUIRED` |
| `FORBIDDEN` | `INSUFFICIENT_PERMISSION` |
| `ORDER_OF_ANOTHER_USER` | `RESOURCE_NOT_FOUND` 또는 `OWNERSHIP_MISMATCH` |

자주 생기는 혼동:

- `title`을 그대로 `code`로 복사하지 않는다. `Forbidden`은 화면 제목이고, `INSUFFICIENT_PERMISSION`은 계약용 코드다.
- `detail`에서 보이는 복구 문구를 `code`에 넣지 않는다. `TRY_LOGIN_AGAIN` 같은 이름은 UI 문장에 가깝다.
- concealment `404`를 쓰는 API라면 `RESOURCE_NOT_FOUND`처럼 바깥 계약을 고정하고, 내부 로그에서만 실제 deny reason을 더 자세히 남긴다.

한 줄 비교:

| 상태 | body에서 말해도 되는 것 | body에서 숨겨야 하는 것 |
|---|---|---|
| `401` | 다시 로그인/재인증 필요 | 만료 시각, verifier 세부 실패 원인 |
| `403` | 이 계정은 이 작업을 할 수 없음 | 필요한 정확한 role/scope, tenant topology |
| `404` | 찾지 못했으니 ID를 다시 확인 | "실제로는 있는데 남의 것"이라는 사실 |

## `401` 헤더 최소 카드: `WWW-Authenticate`는 bearer와 session이 다르다

먼저 mental model 하나만 고정하면 된다.

- `401` body는 "다음 행동"을 말한다.
- `WWW-Authenticate` header는 "이 API가 어떤 인증 방식을 기대하는가"를 말한다.

초보자가 가장 많이 섞는 부분은 여기다.

- bearer token API인데 `WWW-Authenticate`를 빼먹는다.
- session/cookie 기반 API인데 표준이 아닌 `WWW-Authenticate: Session ...`을 만들어 붙인다.

짧게 정리하면 아래처럼 보면 된다.

| 현재 인증 계약 | `401`에서 보통 하는 일 | beginner용 최소 예시 | 바로 붙는 body 템플릿 |
|---|---|---|---|
| bearer token (`Authorization: Bearer ...`) | `WWW-Authenticate: Bearer ...` challenge를 보낸다 | `WWW-Authenticate: Bearer realm="api"` | 위 `401` JSON 템플릿 그대로 사용 |
| session/cookie (`Cookie: session=...`) | 보통 challenge header를 새로 만들지 않고, JSON body나 browser redirect 계약으로 설명한다 | header 없음 + `401` JSON body, 또는 browser라면 `302 -> /login` contract | 위 `401` JSON 템플릿 그대로 사용 |

핵심 비교 한 줄:

| 경우 | 기억할 문장 |
|---|---|
| bearer `401` | "이 API는 Bearer 인증을 기대한다"를 header로 말해 준다 |
| session `401` | "세션이 없거나 믿을 수 없다"를 body/redirect로 말하고, `Session` challenge를 새로 만들지는 않는 편이 보통이다 |

## bearer `401` 최소 예시

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/problem+json
```

이때 body는 위 `401` 템플릿을 그대로 붙이면 된다.

```json
{
  "type": "https://api.example.com/problems/authentication-required",
  "title": "Authentication required",
  "status": 401,
  "code": "AUTHENTICATION_REQUIRED",
  "detail": "Sign in again or refresh your credentials, then retry the request.",
  "request_id": "req_7V1p4rM2"
}
```

## session `401` 최소 예시

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/problem+json
```

```json
{
  "type": "https://api.example.com/problems/authentication-required",
  "title": "Authentication required",
  "status": 401,
  "code": "AUTHENTICATION_REQUIRED",
  "detail": "Sign in again or refresh your credentials, then retry the request.",
  "request_id": "req_7V1p4rM2"
}
```

같은 `401`이어도 차이는 body보다 header 쪽에 있다.

- bearer는 `WWW-Authenticate`가 자연스럽다.
- session은 보통 `session expired` 같은 복구 힌트를 body에 두고, browser page 요청이면 아예 `302 -> /login`으로 UX를 감쌀 수 있다.

## `401` 헤더에서 흔한 오해 3개

- `401`이면 무조건 `WWW-Authenticate`가 꼭 있어야 한다: bearer API라면 강하게 기대되지만, session/cookie 계약까지 같은 모양으로 맞출 필요는 없다.
- session 기반이니 `WWW-Authenticate: Session realm="web"`를 만들면 된다: 초보자용 기준에서는 이렇게 임의 scheme를 만들지 않는 편이 안전하다.
- bearer와 session을 둘 다 받는 route면 header도 둘 다 항상 같이 보내야 한다: 먼저 "이 route의 대표 credential contract가 무엇인지"를 문서로 고정하는 편이 낫다.

## 1. `401` 예시: 다시 인증하라는 힌트만 준다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/authentication-required",
  "title": "Authentication required",
  "status": 401,
  "code": "AUTHENTICATION_REQUIRED",
  "detail": "Sign in again or refresh your credentials, then retry the request.",
  "request_id": "req_7V1p4rM2"
}
```

같이 갈 수 있는 header 예시:

- `WWW-Authenticate: Bearer realm="api"`

이 body는 복구 방향은 주지만, 아래 정보는 숨긴다.

- token이 만료됐는지
- 서명이 깨졌는지
- issuer가 맞지 않는지
- session cookie가 조작됐는지

matching internal log 예시:

```json
{
  "event": "auth.failure",
  "request_id": "req_7V1p4rM2",
  "trace_id": "8f3a0d7d5fb1a0e2",
  "http_status": 401,
  "external_code": "AUTHENTICATION_REQUIRED",
  "internal_reason": "EXPIRED_TOKEN",
  "credential_kind": "bearer",
  "principal_id": null,
  "issuer": "https://id.example.com",
  "route": "GET /api/orders/{id}",
  "resource_type": "order",
  "resource_lookup_key_hash": "sha256:8bbf2a4b...",
  "client_id": "web-frontend"
}
```

핵심은 `expired`, `invalid signature`, `issuer mismatch`를 외부 body에 직접 쓰지 않고,
내부에서는 failure bucket으로 구분해 alert와 triage에 쓰는 것이다.

## 2. `403` 예시: 권한 부족이라는 사실만 알려 준다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/insufficient-permission",
  "title": "Forbidden",
  "status": 403,
  "code": "INSUFFICIENT_PERMISSION",
  "detail": "This account cannot perform this action. Request access if you believe it is required.",
  "request_id": "req_C83mP2Q9"
}
```

이 body는 아래 정보는 감춘다.

- 정확히 어떤 role이 없는지
- 어떤 scope가 빠졌는지
- tenant mismatch인지
- step-up이 필요한지

matching internal log 예시:

```json
{
  "event": "authz.deny",
  "request_id": "req_C83mP2Q9",
  "trace_id": "ae71f0bfe0219c61",
  "http_status": 403,
  "external_code": "INSUFFICIENT_PERMISSION",
  "principal_id": "user_12345",
  "tenant_id": "tenant_a",
  "action": "orders.approve",
  "resource_type": "order",
  "resource_id": "ord_1024",
  "decision": "deny",
  "internal_reason": "SCOPE_MISSING",
  "policy_version": "authz-2026-04-14",
  "auth_assurance_level": "aal1",
  "step_up_required": false,
  "cache_result": "miss"
}
```

여기서 외부 body는 "권한이 없다"까지만 말하고,
내부 log는 실제 remediation에 필요한 `internal_reason`, `policy_version`, `step_up_required`를 따로 남긴다.

## 3. `404` 예시: 진짜 없음과 concealment를 같은 몸체로 보낸다

외부 body 예시:

```json
{
  "type": "https://api.example.com/problems/resource-not-found",
  "title": "Not Found",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "detail": "The requested resource was not found. Verify the identifier or reopen it from a list you can access.",
  "request_id": "req_N4m8L0T1"
}
```

이 body는 아래 정보를 끝까지 숨긴다.

- 리소스가 실제로 존재하는지
- 존재한다면 누구 소유인지
- cross-tenant mismatch인지
- concealment policy가 발동됐는지

matching internal log 예시:

```json
{
  "event": "resource.lookup",
  "request_id": "req_N4m8L0T1",
  "trace_id": "2b966a9f89d6d834",
  "http_status": 404,
  "external_code": "RESOURCE_NOT_FOUND",
  "principal_id": "user_12345",
  "tenant_id": "tenant_a",
  "action": "orders.read",
  "resource_type": "order",
  "resource_lookup_key_hash": "sha256:5f9df4a1...",
  "lookup_outcome": "FOUND_BUT_CONCEALED",
  "internal_reason": "OWNERSHIP_MISMATCH",
  "concealment_applied": true,
  "policy_version": "authz-2026-04-14"
}
```

중요한 포인트는 진짜 missing이든 concealment deny든 외부 body를 거의 동일하게 유지하는 것이다.
차이는 내부 `lookup_outcome`, `internal_reason`, `concealment_applied`에서만 복원한다.

## 작은 비교 카드: 바깥 `404`와 내부 deny evidence는 같은 칸이 아니다

초보자가 가장 많이 섞는 지점은 "`404`면 audit에도 not found만 남겨야 하나?"다.
아니다. 바깥 응답 의미와 내부 증거는 분리해도 된다.

| 보는 곳 | copy-safe 예시 | 왜 이렇게 나누나 |
|---|---|---|
| 외부 API 응답 | `404` + `RESOURCE_NOT_FOUND` + `request_id` | caller에게는 존재 여부 단서를 더 주지 않는다 |
| 내부 deny/audit log | `lookup_outcome=FOUND_BUT_CONCEALED`, `internal_reason=OWNERSHIP_MISMATCH`, `concealment_applied=true`, `principal_id=user_12345`, `resource_type=order` | 운영자는 "진짜 없음"과 "숨김 404"를 나중에 복원할 수 있어야 한다 |

짧은 한 쌍으로 보면 이렇게 된다.

```json
{"status":404,"code":"RESOURCE_NOT_FOUND","request_id":"req_N4m8L0T1"}
```

```json
{"request_id":"req_N4m8L0T1","http_status":404,"external_code":"RESOURCE_NOT_FOUND","lookup_outcome":"FOUND_BUT_CONCEALED","internal_reason":"OWNERSHIP_MISMATCH","concealment_applied":true}
```

핵심은 `request_id`는 같게 두고, 의미는 다르게 두는 것이다.
응답은 "무엇을 숨길지"를 위한 계약이고, 내부 로그는 [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)와 [AuthZ Decision Logging Design](./authz-decision-logging-design.md)에서 이어지는 증거 레이어다.

## 외부 provider 에러 body는 그대로 pass-through 하지 않는다

초보자용 mental model 하나만 먼저 잡으면 된다.

- 외부 provider 에러 body는 `운영자가 디버깅할 영수증`이지, `사용자에게 그대로 보여 줄 대본`이 아니다.

예를 들어 결제/로그인 provider가 아래처럼 응답했다고 해 보자.

```json
{
  "error": "invalid_token",
  "error_description": "JWT expired at 2026-04-24T09:41:02Z, tenant=prod-finance, keyId=kid-42",
  "trace_id": "upstream-9f2c"
}
```

이 body를 그대로 사용자에게 내리면 안 된다. 대신 우리 서비스 계약으로 짧게 번역한다.

| 방식 | 사용자에게 내려가는 응답 | 왜 이쪽이 안전한가 |
|---|---|---|
| 나쁜 예: pass-through | `JWT expired at ... tenant=prod-finance, keyId=kid-42` | provider 내부 구조, 만료 시각, tenant 정보, key 식별자가 한 번에 노출된다 |
| 좋은 예: sanitize 후 변환 | `Sign in again and retry the request.` + `request_id` | 사용자는 다음 행동만 알고, 상세 원인은 내부 로그에서만 본다 |

짧은 변환 예시는 아래처럼 생각하면 된다.

```json
{
  "type": "https://api.example.com/problems/authentication-required",
  "title": "Authentication required",
  "status": 401,
  "code": "AUTHENTICATION_REQUIRED",
  "detail": "Sign in again and retry the request.",
  "request_id": "req_7V1p4rM2"
}
```

내부 로그에는 원본 provider 응답을 그대로 남겨도 되지만, 바깥 응답에는 아래만 남기는 쪽이 beginner-safe하다.

- 사용자 다음 행동
- stable `code`
- 지원팀이 추적할 `request_id`

## body에 넣지 말아야 할 문장 예시

| status | 피해야 할 외부 문장 | 왜 나쁜가 |
|---|---|---|
| `401` | `token expired at 2026-04-14T10:03:11Z`, `kid abc123 not found` | validation surface와 verifier 상태를 너무 자세히 드러낸다 |
| `401` | `provider said invalid_token: tenant=prod-finance, keyId=kid-42` | 외부 provider 상세 body를 그대로 pass-through 하며 내부 연동 정보를 노출한다 |
| `403` | `requires role=SUPER_ADMIN`, `tenant=finance-prod only` | 내부 권한 모델과 tenant topology를 노출한다 |
| `404` | `order 123 exists but belongs to another user` | concealment policy를 완전히 무너뜨린다 |

복구 힌트는 괜찮다.
하지만 힌트는 `다시 로그인`, `접근 권한 요청`, `ID 확인 후 안전한 목록에서 다시 열기` 정도로 멈추는 편이 좋다.

---

## 코드로 보면 더 쉬운 기준

```java
public HttpStatus toExternalStatus(DenyReason reason, boolean concealExistence) {
    return switch (reason) {
        case MISSING_CREDENTIAL, INVALID_CREDENTIAL -> HttpStatus.UNAUTHORIZED;
        case INSUFFICIENT_SCOPE, ADMIN_ROLE_REQUIRED -> HttpStatus.FORBIDDEN;
        case OWNERSHIP_MISMATCH -> concealExistence
                ? HttpStatus.NOT_FOUND
                : HttpStatus.FORBIDDEN;
        case RESOURCE_MISSING -> HttpStatus.NOT_FOUND;
    };
}
```

이 예시는 한 가지를 보여 준다.

- `ownership mismatch` 같은 내부 reason은 서비스 정책에 따라 `403`도 될 수 있고 `404`도 될 수 있다.
- 반면 `missing credential`은 보통 `401` bucket을 벗어나지 않는다.

---

## 운영에서 놓치지 말아야 할 2가지

### 1. 외부 응답과 내부 로그는 분리한다

외부가 `404`여도 내부에는 남겨야 한다.

- request id
- http status
- external code
- internal reason
- principal id
- resource type
- resource lookup key 또는 hash
- concealment applied 여부
- policy version
- correlation / trace id

그래야 운영자가 `진짜 없음`과 `concealment deny`를 구분할 수 있다.
이 필드 묶음은 [AuthZ Decision Logging Design](./authz-decision-logging-design.md)과 [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)에서 보는 decision log, bucketed metric과도 바로 이어진다.

### 2. gateway와 app이 같은 계약을 써야 한다

예를 들어:

- gateway는 만료 token에 `401`
- 앱은 같은 경로에서 scope 부족에 `403`
- 어떤 bypass route는 예외 매핑 실수로 `500`

이렇게 섞이면 클라이언트는 재로그인해야 하는지, 권한을 요청해야 하는지, 버그인지 알 수 없다.
그래서 `401` / `403` / `404`는 controller 한 군데의 취향이 아니라 edge-to-service contract다.

---

## 꼬리질문 5문 5답

먼저 아주 짧게 기억하면 된다.

| 내가 지금 묻는 것 | 먼저 떠올릴 코드 | 첫 행동 |
|---|---|---|
| "나 누구인지 다시 확인해야 하나?" | `401` | 재로그인, 토큰/세션 갱신 |
| "누구인지는 아는데 권한이 없나?" | `403` | role, permission, scope 확인 |
| "없나, 아니면 숨기나?" | `404` | ID 확인, concealment 정책 확인 |

> Q: `401`과 `403`의 가장 큰 차이는 무엇인가요?
> A: `401`은 아직 `누구인지`를 못 믿는 상태이고, `403`은 `누구인지는 알지만 허용되지 않는` 상태다. 그래서 `401`은 재인증 쪽, `403`은 권한 확인 쪽으로 먼저 간다.

> Q: `401 Unauthorized`라는 이름인데 왜 권한 부족이 아니라 인증 실패 쪽인가요?
> A: 이름만 보면 헷갈리지만, 초보자는 `401 = 다시 인증해라`로 외우는 편이 안전하다. 실무에서는 missing token, expired session, invalid signature처럼 credential 자체가 성립하지 않을 때 주로 쓴다.

> Q: 로그인은 했는데 관리자 페이지가 안 열립니다. `401`일까요 `403`일까요?
> A: 보통 `403`이다. 이미 principal은 만들어졌고, 그다음 role, permission, scope, ownership 중 어디선가 막힌 경우가 많다. 이때는 재로그인보다 권한 모델을 먼저 본다.

> Q: 왜 다른 사람 주문 조회에 `404`를 줄 수 있나요? 없는 것도 아닌데요.
> A: 바깥에는 `없다`고 보이게 해서 리소스 존재 여부를 숨기려는 concealment 정책일 수 있다. 초보자 기준에서는 `404 = 진짜 없음`으로 단정하지 말고, user-owned 또는 tenant 리소스면 `숨김 404` 가능성도 같이 떠올리면 된다.

> Q: 권한을 방금 줬는데도 `403`이나 `404`가 그대로면 서버가 아직 틀린 건가요?
> A: 꼭 그렇지는 않다. source of truth에는 grant가 저장됐어도, 현재 요청 경로가 old claim이나 stale deny cache를 아직 보고 있으면 잠깐 `403`이나 concealment `404`가 남을 수 있다. 이때는 "권한 부여가 실패했다"로 바로 단정하지 말고 [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)로 이어서 freshness를 먼저 확인한다.

## 한 줄 정리

`401 = 다시 인증`, `403 = 권한 부족`, `404 = 진짜 없음 또는 존재 은닉`으로 먼저 외우고, 실제 구현에서는 `인증 -> 인가 -> concealment policy` 순서로 판단하면 된다.
