# 브라우저 직접 호출 vs 서버 프록시 결정 트리

> 한 줄 요약: `CORS 때문에 프론트에서 직접 붙일까?`라는 질문은 보통 CORS 질문이 아니라 `누가 시크릿을 들고 외부 API를 호출해야 하나`라는 경계 질문이다.

**난이도: 🟢 Beginner**

관련 문서:

- [API 키 기초](./api-key-basics.md)
- [CORS 기초](./cors-basics.md)
- [OAuth2 기초](./oauth2-basics.md)
- [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
- [Security README 기본 primer 묶음](./README.md#기본-primer)

retrieval-anchor-keywords: 브라우저 직접 호출 vs 서버 프록시, 브라우저 직접 호출 vs 서버 대리 호출, cors 때문에 프론트에서 직접 호출, cors 때문에 bff, cors 때문에 proxy, api key browser or server, api key 프론트에 넣어도 되나, secret key 브라우저 금지, public key browser allowed, publishable key browser allowed, 서버 프록시 decision tree, bff decision tree, beginner api key cors, beginner browser proxy branch, 외부 api 직접 호출 여부, 프론트에서 외부 api 바로 호출, 브라우저에서 secret key 쓰면 안 되는 이유, server-side only meaning, do not expose in client 뜻, cors 에러인데 왜 서버 프록시, browser direct call quick decision, proxy or direct api call, browser third party api call beginner, backend for frontend beginner, bff beginner quick branch, 브라우저에서 호출하려고 할 때

## 먼저 잡을 mental model

초보자에게는 아래 한 줄이 가장 중요하다.

> CORS는 "브라우저가 응답을 읽어도 되나"를 묻는 규칙이고, 서버 프록시/BFF는 "누가 시크릿과 외부 호출 책임을 가지나"를 정하는 구조다.

그래서 `CORS 에러가 나니까 프론트에서 secret key를 넣고 직접 붙이자`는 해결책이 아니다.

- CORS를 열어도 secret key를 브라우저에 넣는 문제는 그대로 남는다.
- preflight를 통과해도 브라우저에 서버 전용 키가 보이면 설계는 이미 틀린 것이다.
- 반대로 브라우저 직접 호출이 가능한 경우도 있지만, 그때는 provider가 처음부터 `public`/`publishable` 사용을 허용한 경우여야 한다.

## 30초 결정 트리

아래 4단계만 순서대로 보면 대부분 바로 갈린다.

### 1. provider 문서에 `server-side only` 또는 `secret key`라고 적혀 있는가

- `Yes`면 바로 서버 프록시/BFF다.
- 이유: 브라우저 번들, DevTools, 네트워크 패널에서 결국 노출된다.

### 2. 지금 직접 붙이려는 이유가 `CORS 때문에 브라우저에서 안 붙는다`인가

- `Yes`여도 결론은 그대로 서버 프록시/BFF가 기본값이다.
- 이유: CORS를 우회하려고 브라우저에 시크릿을 넣으면 문제를 옮기는 것뿐이다.

### 3. 이 호출이 `우리 서버 작업`이 아니라 `사용자 자신의 외부 데이터`를 읽는 장면인가

- `Yes`면 API 키보다 OAuth를 먼저 본다.
- 예: 사용자의 Google Drive, Calendar, GitHub 데이터 조회.

### 4. provider가 `public`/`publishable` 키의 브라우저 사용을 명시하고, origin/referrer/기능 제한도 제공하는가

- `Yes`면 제한된 브라우저 직접 호출을 검토할 수 있다.
- 아니면 서버 프록시/BFF로 간다.

## 한 장 표로 보면

| 질문 | `Yes`면 | `No`면 |
|---|---|---|
| `secret`, `server-side only`, `do not expose in client` 문구가 보이나 | 서버 프록시/BFF | 다음 질문 |
| 직접 호출 이유가 단지 `CORS가 막혀서`인가 | 그래도 서버 프록시/BFF | 다음 질문 |
| 특정 사용자 동의/자원 접근인가 | OAuth 우선 | 다음 질문 |
| `public`/`publishable` 키 + origin 제한 + 제한된 기능이 함께 보이나 | 브라우저 직접 호출 검토 가능 | 서버 프록시/BFF |

짧게 외우면:

- `secret`이면 서버.
- `CORS 때문에`여도 서버.
- `사용자 데이터`면 OAuth.
- `public + 제한`일 때만 브라우저 직접 호출을 검토한다.

## 가장 흔한 장면 3개

| 실제 장면 | 빠른 결론 | 왜 그런가 |
|---|---|---|
| 프론트에서 OpenAI/결제/내부 SaaS API를 직접 붙이고 싶다. 브라우저 콘솔에는 CORS 에러가 뜬다 | 서버 프록시/BFF | secret key를 브라우저에 두면 안 된다. CORS는 원인처럼 보여도 핵심 문제는 시크릿 경계다 |
| 사용자가 자기 Google Calendar 일정을 우리 서비스에서 읽게 한다 | OAuth | 앱 고정 신분증(API 키)보다 사용자 위임이 필요하다 |
| provider가 `publishable key`, `safe to embed`, `allowed origins`를 같이 제공한다 | 제한된 브라우저 직접 호출 가능 | 노출을 전제로 기능과 출처를 줄여 둔 키일 수 있다 |

## common confusion

- `CORS만 열면 되지 않나?`
  - CORS 허용은 응답 읽기 규칙이다. 브라우저에 server secret을 넣어도 된다는 허가가 아니다.
- `Postman에서는 되는데 브라우저만 안 된다`
  - Postman은 CORS를 검사하지 않는다. 그래서 이 증상은 종종 `브라우저 경계 설계` 문제를 드러낸다.
- `public key도 그냥 secret key랑 같은 거 아닌가`
  - 아니다. provider가 노출을 전제로 권한, 도메인, 기능을 강하게 제한했을 때만 다르다.
- `브라우저 직접 호출이 더 단순하니 항상 낫지 않나`
  - 초보자 관점에서는 디버깅은 쉬워 보여도, 키 노출, 에러 바디 노출, 호출량 통제, 로깅, 재시도 정책이 더 어려워진다.

## 첫 행동 체크리스트

- provider 문서에서 `public/publishable`인지 `secret/server-side only`인지 먼저 확인한다.
- `CORS 때문에`라는 이유만으로 브라우저 직접 호출로 가지 않는다.
- 사용자 외부 자원 접근이면 API 키 대신 [OAuth2 기초](./oauth2-basics.md)로 먼저 간다.
- server secret이면 [API 키 기초](./api-key-basics.md)의 서버 대리 호출 예시를 따라 서버 프록시/BFF로 잡는다.
- 브라우저와 서버 토큰 경계를 더 깊게 보려면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 내려간다.

## 이 문서 다음에 보면 좋은 문서

- 서버 대리 호출 예시와 배포 체크리스트가 바로 필요하면 [API 키 기초](./api-key-basics.md)
- CORS 자체를 먼저 분리하고 싶으면 [CORS 기초](./cors-basics.md)
- 사용자 위임 호출인지 헷갈리면 [OAuth2 기초](./oauth2-basics.md)
- BFF/session translation까지 이어지는 경계를 깊게 보려면 [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)

## 한 줄 정리

`CORS 때문에 프론트에서 직접 붙일까?`라는 질문의 기본 답은 `먼저 시크릿 경계부터 보자`이고, 기본값은 서버 프록시/BFF다.
