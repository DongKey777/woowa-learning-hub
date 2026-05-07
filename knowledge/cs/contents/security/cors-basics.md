---
schema_version: 3
title: CORS 기초
concept_id: security/cors-basics
canonical: true
category: security
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/spring-roomescape
- missions/shopping-cart
- missions/backend
review_feedback_tags:
- cors-response-read-vs-cookie-send
- preflight-options-first
- credentials-allow-origin-boundary
aliases:
- cors basics
- CORS 기초
- cors가 뭐예요
- cross origin 오류
- cors 에러 브라우저
- preflight란 무엇인가
- access-control-allow-origin
- same origin policy beginner
- cors allow headers
- credentials include cookie not sent
- access-control-allow-credentials beginner
- fetch credentials vs cors
symptoms:
- 브라우저 콘솔에는 CORS 에러가 뜨는데 서버 로그는 정상이라 헷갈려
- OPTIONS만 보이고 실제 GET이나 POST가 안 나가는 이유가 궁금해
- cookie가 안 붙은 문제와 CORS 응답 읽기 문제가 섞여 보여
intents:
- definition
- troubleshooting
prerequisites:
- network/http-https-basics
next_docs:
- security/preflight-debug-checklist
- security/error-path-cors-primer
- security/fetch-credentials-vs-cookie-scope
- security/cors-samesite-preflight
- network/cross-origin-cookie-credentials-cors-primer
linked_paths:
- contents/network/cross-origin-cookie-credentials-cors-primer.md
- contents/security/preflight-debug-checklist.md
- contents/security/error-path-cors-primer.md
- contents/security/fetch-credentials-vs-cookie-scope.md
- contents/security/cors-samesite-preflight.md
- contents/security/api-security-headers-beyond-csp.md
- contents/network/http-https-basics.md
confusable_with:
- security/preflight-debug-checklist
- security/error-path-cors-primer
- security/fetch-credentials-vs-cookie-scope
- network/cross-origin-cookie-credentials-cors-primer
forbidden_neighbors: []
expected_queries:
- CORS는 서버가 응답했는데도 브라우저 JS가 왜 못 읽게 막는 거야?
- OPTIONS preflight만 있고 actual request가 없으면 무엇을 봐야 해?
- request Cookie가 비어 있는 문제와 CORS response header 문제를 어떻게 구분해?
- Access-Control-Allow-Origin과 Allow-Credentials를 왜 서버가 내려줘야 해?
- Postman에서는 되는데 브라우저에서 CORS 에러가 나는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 CORS를 브라우저 same-origin policy와 서버의 Access-Control-Allow-Origin 허용 응답으로 설명하고, preflight OPTIONS, actual request, request Cookie header, response read blocking을 구분하는 beginner primer다.
  Postman에서는 되는데 browser만 실패, OPTIONS-only, credentials include, cookie not sent, error response CORS header missing 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# CORS 기초

> 한 줄 요약: CORS는 브라우저가 "다른 출처의 리소스를 요청해도 되는가"를 서버에게 물어보는 메커니즘이고, 서버가 허용 응답 헤더를 내려줘야 브라우저가 응답을 자바스크립트에 넘긴다.

**난이도: 🟢 Beginner**

## 미션 진입 증상

| browser/API 장면 | 먼저 볼 증거 |
|---|---|
| OPTIONS만 보이고 실제 GET/POST가 없다 | preflight에서 막혔는가 |
| actual request는 갔는데 JS가 응답을 못 읽는다 | CORS response header가 맞는가 |
| request Cookie header가 비어 있다 | CORS보다 credentials/cookie scope 문제인가 |
| Postman은 되는데 브라우저만 실패한다 | browser same-origin policy 경계인가 |

관련 문서:

- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)
- [Preflight Debug Checklist](./preflight-debug-checklist.md)
- [Error-Path CORS Primer](./error-path-cors-primer.md)
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)
- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md)
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)
- [HTTP와 HTTPS 기초](../network/http-https-basics.md)

retrieval-anchor-keywords: cors 기초, cors가 뭐예요, cross origin 오류, cors 에러 브라우저, preflight란 무엇인가, access-control-allow-origin, same origin policy beginner, cors allow headers, cors 해결 방법, beginner cors, credentials include cookie not sent, access-control-allow-credentials beginner, fetch credentials vs cors, security readme cors primer, security beginner route

## 이 문서 다음에 보면 좋은 문서

| 문서 | 먼저 보는 증거 | 이 문서와의 차이 |
|---|---|---|
| [CORS 기초](./cors-basics.md) | actual request는 보이는데 응답 읽기 차단처럼 보인다 | CORS가 무엇을 막는지부터 짧게 잡는 baseline |
| [Preflight Debug Checklist](./preflight-debug-checklist.md) | `OPTIONS`만 있고 actual request가 없다 | preflight에서 멈췄는지부터 분리하는 첫 체크리스트 |
| [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) | actual request는 있는데 request `Cookie` header가 비어 있다 | cookie 전송 실패와 CORS 응답 읽기 실패를 분리하는 bridge |

- security 입문 문서 안에서 다른 primer를 다시 고르고 싶으면 [Security README 기본 primer 묶음](./README.md#기본-primer)으로 돌아가면 된다.
- `origin`, `site`, `credentials: "include"` 용어부터 낯설면 [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md)으로 먼저 들어가면 된다.
- 같은 cross-origin 요청에서 "CORS 응답 읽기 문제"와 "cookie scope 문제"가 한 덩어리처럼 보이면 [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md)로 먼저 갈라 보면 된다.
- `OPTIONS`만 실패하고 actual `GET`/`POST`가 안 보이면 [Preflight Debug Checklist](./preflight-debug-checklist.md)로 바로 이동하면 된다.
- actual `GET`/`POST`는 보이는데 콘솔은 계속 CORS만 말하면 [Error-Path CORS Primer](./error-path-cors-primer.md)로 들어가 `진짜 401/403`과 `브라우저 노출 실패`를 분리하면 된다.
- preflight 캐싱, SameSite, allowlist 설계를 더 깊게 보려면 [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md)로 이어 가면 된다.

## 먼저 잡을 mental model

입문자에게 가장 중요한 한 줄은 이것이다.

> `cookie가 요청에 안 붙은 문제`와 `응답이 왔지만 브라우저가 JS에 안 넘긴 문제`는 서로 다른 단계다.

둘 다 콘솔에서는 비슷하게 "안 된다"로 보이지만, DevTools에서 먼저 볼 칸이 다르다.

| 먼저 확인할 증거 | 뜻 | 바로 다음 문서 |
|---|---|---|
| actual request 자체가 없다 | preflight/CORS 사전 허용 단계에서 멈췄을 수 있다 | [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| actual request는 있는데 request `Cookie` header가 비어 있다 | CORS보다 앞 단계인 `credentials` 또는 cookie scope 문제일 가능성이 크다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| request `Cookie`는 실렸는데 콘솔에는 CORS 에러가 뜬다 | 요청은 갔고, 브라우저가 응답을 JS에 넘기지 않는 CORS 응답 읽기 문제일 가능성이 크다 | [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) |

짧게 외우면:

- request `Cookie`가 비어 있으면 먼저 cookie lane이다.
- request `Cookie`는 있는데 JS가 못 읽으면 CORS lane이다.
- actual request가 아예 없으면 preflight lane이다.

## 1분 체크 카드: `OPTIONS-only`인가, actual request가 있는가

브라우저 Network에서 가장 먼저 고정할 질문은 이것 하나다.

> 같은 path에 actual `GET`/`POST`가 실제로 보이는가?

| DevTools에서 보이는 장면 | 1차 해석 | 지금 바로 할 일 |
|---|---|---|
| `OPTIONS /api/orders -> 401`만 보이고 actual `POST /api/orders`가 없다 | `OPTIONS-only`다. preflight가 막혀 실제 API는 아직 안 나갔다 | auth 해석 전에 [Preflight Debug Checklist](./preflight-debug-checklist.md)로 간다 |
| `OPTIONS /api/orders -> 204` 뒤에 actual `POST /api/orders -> 401`이 보인다 | actual request가 실제로 나갔다. 이제 `POST`의 `401`을 읽어야 한다 | 이 문서를 계속 읽고, 필요하면 [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)로 간다 |

짧은 기억법:

- `OPTIONS-only`면 아직 "로그인 실패"라고 부르지 않는다.
- actual request가 보일 때만 그 요청의 `401`/`403`을 auth/authz 의미로 읽는다.

## 핵심 개념

CORS(Cross-Origin Resource Sharing)는 브라우저의 동일 출처 정책(Same-Origin Policy)이 가로막는 요청을 서버 측에서 명시적으로 허용하는 메커니즘이다. "출처(origin)"는 `프로토콜 + 도메인 + 포트` 세 가지가 모두 같아야 동일 출처로 본다. 입문자가 헷갈리는 이유는 CORS 에러가 브라우저 콘솔에만 보이고 서버 로그엔 아무 이상이 없어서, "서버가 잘 응답했는데 왜 실패하냐"는 혼란이 생기기 때문이다.

## 한눈에 보기

출처(origin)는 `프로토콜 + 도메인 + 포트`가 모두 같아야 동일 출처다. 하나라도 다르면 브라우저가 CORS 체크를 시작한다.

```
[출처 비교 예시]
https://app.example.com  (프론트엔드)
https://api.example.com  (백엔드 API)
→ 도메인이 달라서 "다른 출처" → 브라우저가 CORS 체크

[서버가 내려줘야 하는 헤더]
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Content-Type, Authorization
```

허용 헤더가 없으면 브라우저가 응답을 자바스크립트에 넘기지 않고 콘솔에 "CORS policy" 에러를 표시한다. 서버 응답은 도착했어도 JS에서는 읽을 수 없다.

## 30초 분기표: cookie 누락 vs CORS 차단

같은 증상처럼 보여도 초보자는 아래 순서로만 읽으면 된다.

| 장면 | Network에서 먼저 볼 것 | 1차 결론 | 다음 한 걸음 |
|---|---|---|---|
| `OPTIONS`만 있고 actual `GET`/`POST`가 없다 | actual request 존재 여부 | 아직 cookie/CORS 본게임 전이다 | [Preflight Debug Checklist](./preflight-debug-checklist.md) |
| actual request가 있고 request `Cookie` header가 비어 있다 | actual request의 `Cookie` header | `credentials`, `Domain`, `Path`, `SameSite` 쪽이 먼저다 | [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) |
| actual request에 `Cookie`가 실렸고 서버 로그도 찍히는데 콘솔이 CORS 에러를 낸다 | request `Cookie` + console error | 요청은 갔고 응답 읽기가 막힌 것이다 | [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) |

브라우저에서 읽는 순서는 이 셋이면 충분하다.

1. actual request가 있는가
2. 있으면 request `Cookie`가 비었는가
3. 안 비었는데 JS가 못 읽는가

여기서 1번을 더 단순하게 보면:

- `OPTIONS`만 있으면 preflight branch
- actual `GET`/`POST`가 보이면 그때부터 cookie/auth branch

## 상세 분해

- **Same-Origin Policy**: 브라우저는 기본적으로 다른 출처의 응답 내용을 자바스크립트가 읽지 못하게 막는다. 이것이 CORS 체크의 출발점이다.
- **Preflight 요청**: `PUT`, `DELETE`, `Content-Type: application/json` 등 "단순하지 않은" 요청은 실제 요청 전에 브라우저가 `OPTIONS` 메서드로 먼저 서버에게 허용 여부를 물어본다.
- **허용 응답 헤더**: 서버가 `Access-Control-Allow-Origin` 헤더를 응답에 포함해야 브라우저가 JS에게 응답을 전달한다. 누락하면 브라우저가 응답을 차단한다.
- **`*` 와일드카드의 한계**: `Access-Control-Allow-Origin: *`는 쿠키나 Authorization 헤더가 포함된 자격증명(credentials) 요청에는 사용할 수 없다. 쿠키가 필요하면 정확한 출처를 명시해야 한다.

## 흔한 오해와 함정

- **"CORS는 보안 취약점이다"** → CORS는 취약점이 아니라 보안 기능이다. 브라우저가 동일 출처 정책으로 막는 것을 서버가 선택적으로 열어주는 메커니즘이다.
- **"서버에서 안 된다고 하는데, Postman에서는 된다"** → CORS 체크는 브라우저만 한다. Postman, curl, 서버 간 통신은 CORS 제한을 받지 않는다.
- **"프론트엔드에서 헤더를 추가하면 해결된다"** → CORS 허용 헤더는 반드시 서버 응답에 있어야 한다. 프론트엔드 요청 헤더를 아무리 바꿔도 서버가 응답하지 않으면 소용없다.
- **"`Access-Control-Allow-Credentials: true`를 켰으니 이제 cookie도 자동으로 붙는다"** → 아니다. 그 헤더는 응답을 JS가 읽어도 되는지에 가깝고, request `Cookie` 전송 여부는 `fetch credentials`와 cookie scope가 먼저 결정한다.
- **"콘솔에 CORS 에러가 떴으니 request cookie도 안 갔을 것이다"** → 아니다. simple cross-origin 요청은 서버까지 간 뒤 응답만 브라우저가 막는 경우가 많다. request `Cookie` header를 직접 봐야 한다.
- **"`OPTIONS 401`을 봤으니 actual `POST`도 같은 이유로 실패했다"** → 아니다. same-path actual request가 아예 없으면 실제 API는 아직 출발하지 않은 것이다.
- **"preflight가 통과했으니 CORS는 완전히 끝났다"** → 꼭 그렇지는 않다. actual `401`/`403` error response에 CORS 헤더가 빠지면 브라우저에서는 여전히 CORS처럼 보일 수 있다.

## 실무에서 쓰는 모습

Spring Boot에서는 `@CrossOrigin` 어노테이션이나 `WebMvcConfigurer`의 `addCorsMappings()`로 허용 출처를 등록한다. 로컬 개발 시에는 프론트엔드 개발 서버 주소(예: `http://localhost:3000`)를 명시적으로 허용하고, 운영 환경에서는 실제 배포 도메인만 허용 목록에 넣는다. `allowedOrigins("*")`와 `allowCredentials(true)`를 동시에 쓰면 Spring이 에러를 내는데, 이것은 올바른 제약이다.

## 더 깊이 가려면

- [Cross-Origin Cookie, `fetch credentials`, CORS 입문](../network/cross-origin-cookie-credentials-cors-primer.md) — `origin`/`site`/`credentials` 용어 자체가 아직 헷갈릴 때 먼저 맞추는 primer
- [Preflight Debug Checklist](./preflight-debug-checklist.md) — actual request가 아예 없는지부터 분기하고 싶을 때 보는 첫 체크리스트
- [Fetch Credentials vs Cookie Scope](./fetch-credentials-vs-cookie-scope.md) — `credentials: "include"`와 `Access-Control-Allow-Credentials`, cookie scope가 섞여 보일 때 먼저 분리하는 bridge
- [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) — Preflight 캐싱, SameSite 쿠키와의 관계, allowlist 설계
- [API 보안 헤더 기초](./api-security-headers-beyond-csp.md) — CORS 외에 응답 헤더로 설정하는 다른 보안 정책들

## 면접/시니어 질문 미리보기

- **"CORS 에러를 서버에서만 해결할 수 있는 이유가 뭔가요?"** → 브라우저가 서버 응답의 `Access-Control-Allow-Origin` 헤더를 보고 허용 여부를 결정하기 때문에, 클라이언트(브라우저)가 아닌 서버가 허용 선언을 해야 한다.
- **"`allowedOrigins(*)`와 `allowCredentials(true)`를 동시에 쓰면 왜 안 되나요?"** → 자격증명 요청에 와일드카드 출처를 허용하면 어떤 사이트에서도 쿠키를 포함한 요청이 가능해져 보안 의미가 사라지기 때문이다.

## 한 줄 정리

CORS는 브라우저가 다른 출처 요청을 막는 동일 출처 정책을, 서버가 `Access-Control-Allow-Origin` 헤더로 선택적으로 여는 메커니즘이다.
