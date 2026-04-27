# Embedded Login CSRF Bridge

> 한 줄 요약: iframe/embedded login 때문에 `SameSite=None; Secure`로 cross-site cookie 전송을 열었다면, 다음 질문은 "이제 브라우저가 자동으로 보내는 이 cookie를 어떤 요청까지 믿을 것인가?"다. beginner 기준 최소 답은 `상태 변경 요청에는 CSRF gate를 둔다`이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)

> 관련 문서:
> - `[entrypoint]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md)
> - `[entrypoint]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md)
> - `[primer]` [XSS와 CSRF 기초](./xss-csrf-basics.md)
> - `[follow-up]` [SameSite Login Callback Primer](./samesite-login-callback-primer.md)
> - `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
> - `[catalog]` [Security README: Browser / Session Troubleshooting Path](./README.md#browser--session-troubleshooting-path)

retrieval-anchor-keywords: embedded login csrf bridge, iframe login csrf beginner, cross-site cookie csrf minimum expectation, samesite none csrf bridge, embedded login first post 403, iframe cookie csrf token, social login callback success first post 403 beginner, cross-site session cookie state changing request, embedded auth csrf minimum checklist, cookie auto sent csrf beginner, partner portal iframe csrf primer, browser auto credential csrf bridge, cross-site cookie opened now what csrf, embedded login csrf mental model, embedded login csrf bridge basics

## 왜 이 문서가 필요한가

이 문서는 아래 장면의 짧은 bridge다.

- iframe/embedded login이라서 `SameSite=None; Secure`가 필요하다는 점은 이미 이해했다
- 또는 privacy-control 문서를 읽고 "embedded login이 되더라도 서버 쪽 최소 안전장치는 뭐죠?"가 궁금하다
- 그런데 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)는 지금 읽기엔 너무 깊다

초보자에게는 아래 한 줄이 먼저다.

> cross-site cookie를 여는 일과, 그 cookie가 붙은 상태 변경 요청을 믿는 일은 같은 문제가 아니다.

---

## 가장 중요한 mental model

| 질문 | 누가 결정하나 | 실패하면 보이는 장면 |
|---|---|---|
| iframe/cross-site 맥락에서도 cookie를 보낼 수 있나 | 브라우저의 `SameSite`, privacy 정책 | login callback, iframe 세션 유지가 안 된다 |
| 그 cookie가 붙은 `POST`/`PUT`/`DELETE`를 서버가 믿어도 되나 | 서버의 CSRF 방어 | 로그인은 됐는데 원치 않는 상태 변경 요청이 통과한다 |

핵심은 이것이다.

- `SameSite=None; Secure`는 **보내도 되는가**를 여는 설정이다.
- CSRF 방어는 **보내진 요청을 그대로 믿어도 되는가**를 묻는 설정이다.

그래서 embedded login이 필요해서 cross-site cookie를 열었다면,
보통 CSRF 질문은 더 중요해지고 덜 중요해지지 않는다.

---

## beginner용 최소 규칙

인증을 session cookie로 하고, 그 cookie가 브라우저에서 자동 전송된다면 아래처럼 생각하면 된다.

| 요청 종류 | beginner 기준 최소 기대치 |
|---|---|
| login 시작, callback correlation | `state`, one-time login transaction 검증 |
| 로그인 후 `GET` 조회 | 읽기 전용인지 먼저 확인 |
| 로그인 후 `POST`/`PUT`/`PATCH`/`DELETE` | CSRF token 또는 동급 gate + `Origin`/`Referer` 확인 |

여기서 초보자가 가장 자주 놓치는 점은 이것이다.

- OAuth/OIDC의 `state`는 "이 callback이 내가 시작한 login flow의 응답인가"를 보는 값이다
- app의 CSRF token은 "지금 이 상태 변경 요청이 내 화면에서 나온 정상 요청인가"를 보는 값이다

즉 `state`가 맞았다고 해서 이후 `POST /api/profile`까지 자동으로 안전해지는 것은 아니다.

---

## 딱 이 정도는 챙긴다

### 1. 상태 변경 요청은 CSRF gate를 둔다

beginner 기준 최소선은 아래 둘 중 하나다.

- 서버 프레임워크 기본 CSRF 보호를 그대로 쓴다
- 최소한 `Origin`/`Referer` 검증과 anti-CSRF token을 함께 둔다

특히 iframe/embedded login은 cross-site cookie를 일부러 여는 장면이므로,
"우리는 cookie를 자동 전송에 의존한다"는 사실을 더 명확하게 받아들여야 한다.

### 2. login callback 검증과 app mutation 검증을 섞지 않는다

짧게 분리하면 이렇다.

| 단계 | 주로 보는 것 |
|---|---|
| external IdP -> callback | `state`, PKCE, one-time login transaction |
| callback 성공 후 app API 호출 | session cookie, CSRF token, `Origin` |

이 둘을 한 문장으로 합치면 디버깅이 길어진다.

### 3. cross-site cookie는 필요한 범위만 연다

`SameSite=None`은 "모든 세션 정책 완화"가 아니다.

- callback이나 embedded login에 꼭 필요한 cookie만 연다
- 가능하면 읽기/로그인용 cookie와 일반 app session 책임을 섞지 않는다
- embedded login 이후 첫 상태 변경 요청은 특히 CSRF 관점에서 다시 본다

---

## 흔한 혼동 3개

### 1. "`SameSite=None; Secure`를 넣었으니 CSRF도 해결된 것 아닌가요?"

아니다.

- `SameSite=None`은 cross-site 전송 허용
- CSRF 방어는 위조 요청 차단

서로 다른 질문이다.

### 2. "`state`가 있으니 POST 요청도 안전한 것 아닌가요?"

아니다.

`state`는 login flow용이고, 로그인 뒤의 일반 mutation 요청까지 대신 보호하지 않는다.

### 3. "우리는 iframe login만 하고 위험한 API는 없어요"

이 판단은 쉽게 틀린다.

아래가 하나라도 있으면 상태 변경 API다.

- 프로필 수정
- 로그아웃
- 권한 승인/거절
- 연결 해제
- 즐겨찾기, 좋아요, 설정 저장

작아 보여도 CSRF 관점에서는 mutation이다.

---

## 30초 체크리스트

- 이 요청이 로그인 후 상태를 바꾸는 `POST`/`PUT`/`PATCH`/`DELETE`인가
- 인증이 브라우저가 자동으로 보내는 cookie에 의존하는가
- iframe/embedded flow 때문에 `SameSite=None; Secure`를 열었는가
- 그렇다면 CSRF token 또는 동급 gate와 `Origin` 검증이 있는가

위 네 줄 중 마지막 줄이 비어 있으면, beginner 기준으로는 아직 "최소 안전선" 전이다.

---

## 어디로 이어서 읽으면 되나

| 지금 남은 질문 | 다음 한 장만 읽기 | 이유 |
|---|---|---|
| cross-site cookie가 왜 필요한지부터 다시 흔들린다 | `[entrypoint]` [SameSite=None Cross-Site Login Primer](./samesite-none-cross-site-login-primer.md) | cookie 전송 축을 먼저 고정한다 |
| iframe 안에서만 실패하는 privacy-control 문제가 더 크다 | `[entrypoint]` [Embedded Login Privacy Primer](./iframe-login-privacy-controls-primer.md) | CSRF보다 브라우저 정책 축이 먼저일 수 있다 |
| `state`와 CSRF token 차이가 아직 헷갈린다 | `[primer]` [XSS와 CSRF 기초](./xss-csrf-basics.md) | 공격 목표와 방어 역할을 분리한다 |
| SPA/BFF, token bootstrap, first POST `403`까지 같이 봐야 한다 | `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) | 이 bridge 다음 심화 문서다 |

## 한 줄 정리

embedded login 때문에 cross-site cookie를 열었다면, 그 다음 최소 질문은 "이 cookie가 붙은 상태 변경 요청을 어떻게 구별할 것인가"다. beginner 기준 답은 `callback 검증`과 `app CSRF 검증`을 분리하고, mutation 요청에는 CSRF gate를 둔다는 것이다.
