# Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문

> 한 줄 요약: DevTools `Status`에 `(blocked)`, `canceled`, `(failed)`가 보이면 먼저 "서버가 준 HTTP 에러 응답"이 아니라 "브라우저가 붙인 결과 메모"로 읽어야 응답 헤더와 서버 body를 찾느라 헤매지 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: browser devtools blocked canceled failed, devtools status without response headers, blocked canceled failed 뭐예요, response headers 없어요, browser-side row primer, devtools special status memo, canceled vs failed basics, blocked 브라우저가 막았어요, failed network error beginner, 처음 devtools status, why no response headers, what is blocked in devtools, what is canceled in devtools, what is failed in devtools

## 핵심 개념

이 세 표시는 서버가 `404`, `500`처럼 **숫자 상태 코드를 응답한 장면**과 다르다. 초급자는 row가 빨갛게 보이면 바로 "서버 에러"라고 읽기 쉬운데, `(blocked)`, `canceled`, `(failed)`는 먼저 **브라우저가 요청을 끝까지 정상적인 HTTP 응답 줄로 만들지 못했다는 메모**로 보는 편이 안전하다.

그래서 첫 질문도 달라진다.

- `404`를 보면 "서버가 왜 이 숫자를 줬지?"를 묻는다
- `(blocked)`/`canceled`/`(failed)`를 보면 "브라우저가 왜 응답 줄을 완성하지 못했지?"를 먼저 묻는다

핵심은 "response headers가 비어 있다"는 사실이 이상한 것이 아니라, **아직 헤더를 읽을 단계가 아니었을 수 있다**는 점이다.

## 한눈에 보기

| DevTools `Status` | 초급자 첫 해석 | 응답 헤더를 기대해도 되나 | 먼저 볼 다음 단서 |
|---|---|---|---|
| `(blocked)` | 브라우저 정책이나 환경이 요청을 막았을 수 있다 | 보통 기대하지 않는다 | 콘솔 메시지, CORS/mixed content, 확장 프로그램 |
| `canceled` | 브라우저나 JS가 중간에 요청을 취소했을 수 있다 | 보통 기대하지 않는다 | 페이지 이동, 새로고침, `AbortController`, 중복 요청 |
| `(failed)` | 전송 중 네트워크/보안/브라우저 오류로 숫자 응답을 못 받았을 수 있다 | 보통 기대하지 않는다 | DNS, TLS, offline, 연결 실패 |
| `404` / `500` | 서버가 숫자 상태 코드를 응답했다 | 기대한다 | response headers, body, `Server`, `Via` |

짧게 외우면 이렇게 보면 된다.

```text
숫자 status -> 서버 응답 해석
특수 status 메모 -> 브라우저/전송 단계 해석
```

## 셋을 어떻게 가르면 되나

### `(blocked)`

브라우저가 "이 요청은 정책상 보내면 안 되거나, 보내더라도 정상 응답으로 다루지 않겠다"는 쪽에 가깝다. 초급자 눈에는 서버가 거절한 것처럼 보일 수 있지만, 실제로는 요청이 네트워크로 충분히 나가지 못했을 수도 있다.

처음에는 이 정도만 기억하면 된다.

- CORS 정책 위반
- mixed content처럼 HTTPS 페이지에서 HTTP 자원을 막는 경우
- 광고 차단기나 보안 확장 프로그램이 막는 경우

즉 `(blocked)`를 보면 app의 `404` body를 찾기보다 브라우저 정책과 콘솔 메시지를 먼저 본다.

초급자가 특히 많이 헷갈리는 두 갈래는 아래다.

- `Mixed Content ... requested an insecure resource 'http://...'`
- `... has been blocked by CORS policy`

둘 다 `(blocked)`처럼 보여도 앞은 **HTTPS 페이지가 HTTP 자원을 부른 장면**, 뒤는 **cross-origin 응답 읽기 정책 장면**이다. 이 둘을 짧게 가르고 싶으면 [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)를 먼저 보면 된다.

### `canceled`

요청이 시작되었더라도 **중간에 취소**될 수 있다. 이때 초급자는 "서버가 에러를 냈나?"로 오해하기 쉽지만, 실제로는 사용자가 페이지를 떠났거나 JS가 직접 끊었을 수 있다.

자주 보는 장면은 이렇다.

- 링크를 눌러 다른 페이지로 이동했다
- 새로고침하면서 이전 요청이 정리됐다
- 프론트 코드가 `AbortController`로 이전 검색 요청을 취소했다

그래서 `canceled`는 "누가 요청을 끊었나"를 먼저 보는 상태다.

### `(failed)`

브라우저가 요청을 시도했지만 숫자 응답을 안정적으로 받기 전에 실패한 장면에 가깝다. 이 경우는 서버가 `500`을 보냈다기보다, **응답 줄이 오기 전에 전송 자체가 무너진 경우**를 먼저 의심한다.

자주 붙는 첫 후보는 아래와 같다.

- DNS 조회 실패
- TLS handshake 실패
- 네트워크 단절, offline, connection refused

즉 `(failed)`는 헤더 판독보다 연결 실패 문맥이 먼저다.

## 응답 헤더가 없을 때 읽는 순서

`Headers` 탭에 response headers가 거의 없다고 해서 DevTools가 고장 난 것은 아니다. 아래 순서로 읽으면 된다.

1. `Status`가 숫자인지 특수 메모인지 먼저 본다.
2. 특수 메모면 response body나 `Server` 헤더를 찾기 전에 browser-side 이유를 적는다.
3. `Console`에 정책 에러가 있는지 본다.
4. 숫자 응답이 나오는 다른 row가 함께 생겼는지 비교한다.

작은 비교 예시:

| 장면 | 보이는 것 | 초급자 첫 문장 |
|---|---|---|
| A | `Status: (blocked)`, response headers 거의 없음 | "서버 `403`보다 브라우저 정책 차단 후보를 먼저 본다" |
| B | `Status: canceled`, 같은 URL의 다음 row는 `200` | "이전 요청이 취소되고 새 요청이 이어졌을 수 있다" |
| C | `Status: (failed)`, response headers 없음 | "HTTP body 해석보다 DNS/TLS/연결 실패를 먼저 본다" |
| D | `Status: 500`, `Server: nginx`, JSON body 있음 | "이 줄은 서버 응답이므로 헤더와 body를 읽는다" |

## 흔한 오해와 함정

- 빨간 row면 전부 서버 에러라고 생각한다. 특수 status는 브라우저 메모일 수 있다.
- response headers가 비어 있으니 서버가 헤더를 잘못 내려줬다고 단정한다. 아예 정상 응답 줄이 없었을 수 있다.
- `(blocked)`를 `403`과 같은 뜻으로 읽는다. `403`은 서버 응답이고 `(blocked)`는 브라우저 차단 메모다.
- `canceled`를 곧바로 백엔드 timeout으로 읽는다. 사용자의 이동이나 프론트 abort가 더 흔하다.
- `(failed)`를 무조건 서버 다운으로 읽는다. DNS, TLS, 로컬 네트워크 문제도 많다.

헷갈릴 때는 이렇게 문장을 고치면 된다.

- "서버가 막았어요" 대신 "브라우저가 막았을 수 있어요"
- "서버가 취소했어요" 대신 "브라우저나 JS가 취소했을 수 있어요"
- "서버가 500을 줬어요" 대신 "숫자 응답을 받기 전에 실패했을 수 있어요"

## 실무에서 쓰는 모습

검색 자동완성 API를 예로 들면, 사용자가 `a`, `ab`, `abc`를 빠르게 입력할 때 프론트는 이전 요청을 취소하고 마지막 요청만 남길 수 있다.

```text
/search?q=a    -> canceled
/search?q=ab   -> canceled
/search?q=abc  -> 200
```

이 장면에서 앞의 두 줄을 "서버 에러"로 읽으면 잘못이다. 초급자 첫 해석은 "낡은 요청을 프론트가 정리했고, 마지막 요청만 정상 완료됐다"가 더 가깝다.

반대로 `(blocked)` row라면 같은 URL이어도 CORS, mixed content, 확장 프로그램 차단 여부를 먼저 봐야 하고, `(failed)` row라면 사내 VPN, DNS, 인증서, 네트워크 상태를 먼저 확인하는 편이 빠르다.

## 더 깊이 가려면

- DevTools 첫 판독 순서를 1분 카드로 다시 잡으려면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- 숫자 응답이 있을 때만 헤더 3칸으로 browser/proxy/app을 가르려면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- body owner를 app/gateway/login HTML로 가르고 싶다면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- CORS와 브라우저 정책 차단을 더 또렷하게 보고 싶다면 [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)
- `(blocked)` 안에서 mixed content와 CORS를 콘솔 문구로 더 빨리 가르고 싶다면 [Browser DevTools `(blocked)` Mixed Content vs CORS 미니 카드](./browser-devtools-blocked-mixed-content-vs-cors-mini-card.md)
- request/response header 자체가 아직 낯설다면 [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)

## 한 줄 정리

DevTools의 `(blocked)`, `canceled`, `(failed)`는 먼저 서버 에러 코드가 아니라 브라우저가 붙인 결과 메모로 읽고, response headers보다 정책·취소·연결 실패 단서를 먼저 보는 것이 안전하다.
