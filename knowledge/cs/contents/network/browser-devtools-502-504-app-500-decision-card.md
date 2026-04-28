# Browser DevTools `502` vs `504` vs App `500` 분기 카드

> 한 줄 요약: 브라우저에서 `500`은 보통 origin app이 직접 만든 에러 payload 후보이고, `502`/`504`는 proxy나 gateway가 만든 기본 HTML/body/header 패턴 후보로 먼저 읽으면 첫 분기 실수가 크게 줄어든다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: 502 vs 504 vs 500, gateway default html, app-owned error payload, browser devtools 502 504 500, devtools response header clue, server via x-cache clue, bad gateway vs gateway timeout, 500 에러 왜 502로 보여요, gateway timeout 뭐예요, bad gateway 뭐예요, 502 504 차이 처음, nginx envoy cloudfront error page, what is bad gateway, 처음 devtools gateway error, 헷갈리는 502 504 500

## 핵심 개념

처음에는 복잡하게 보지 말고 "누가 말하고 있나"만 먼저 나누면 된다.

- `500`: 보통 **origin application**이 "요청은 받았는데 처리하다 실패했다"라고 직접 말한 장면이다.
- `502`: 보통 **proxy/gateway**가 "upstream과의 연결이나 응답 형식이 이상했다"라고 바깥에서 대신 말한 장면이다.
- `504`: 보통 **proxy/gateway**가 "upstream을 기다렸는데 timeout이 났다"라고 대신 말한 장면이다.

즉 `500`은 app 내부 예외에 더 가깝고, `502`/`504`는 app 앞단 hop의 관찰일 수 있다. 초급자가 가장 자주 하는 실수는 `502`나 `504`를 보고 바로 "컨트롤러가 502를 반환했구나"라고 읽는 것이다.

## 한눈에 보기

| 브라우저에서 보인 것 | 초급자 첫 해석 | DevTools에서 먼저 볼 것 | 안전한 다음 행동 |
|---|---|---|---|
| `500 Internal Server Error` | app이 직접 실패를 응답했을 가능성이 크다 | `Status`, 응답 body 형식, app 공통 에러 JSON/HTML | app 로그와 예외 trace를 먼저 본다 |
| `502 Bad Gateway` | proxy가 upstream 응답/연결 문제를 대신 표현했을 가능성이 크다 | `Status`, body가 gateway 기본 에러 페이지인지, `Server`/`Via` 계열 header | proxy/LB 로그와 upstream 연결 실패를 같이 본다 |
| `504 Gateway Timeout` | proxy가 upstream 대기 timeout을 낸 장면일 가능성이 크다 | `Status`, waterfall의 `waiting`, retry 흔적 | timeout budget, 느린 upstream, app은 뒤늦게 성공했는지도 같이 본다 |

짧은 decision card:

```text
500  -> app이 직접 실패했나?
502  -> app 앞단이 upstream 연결/응답 문제를 대신 말했나?
504  -> app 앞단이 upstream 기다리다 timeout 났나?
```

## gateway 기본 페이지 vs app 에러 payload 빠른 구분

초급자에게 가장 실용적인 질문은 "지금 body와 header가 누구 말투인가"다.

| 관찰 포인트 | gateway가 만든 기본 에러 페이지 후보 | app이 직접 만든 에러 payload 후보 |
|---|---|---|
| body 형태 | 아주 짧은 `Bad Gateway`, `Gateway Timeout` HTML, 흰 배경 기본 페이지 | 서비스 JSON 에러 포맷, 서비스 템플릿 HTML, 도메인 문맥이 드러나는 문구 |
| `Content-Type` | `text/html`인 경우가 많다 | `application/json` 또는 서비스가 원래 쓰는 HTML/JSON 포맷 |
| header 단서 | `Server`, `Via`, `X-Cache` 같은 proxy 흔적이 먼저 눈에 띈다 | `X-Request-Id`, 서비스 공통 tracing/header 규칙이 더 눈에 띈다 |
| DevTools 첫 해석 | "app 앞단이 대신 말했나?" | "app이 자기 에러 형식으로 답했나?" |

이 표의 핵심은 "HTML이면 무조건 gateway"가 아니라, `status + body + header`를 같이 묶어 보라는 뜻이다.

## 상세 분해

### `500`: app이 말을 끝낸 경우가 많다

`500`은 서버 코드가 요청을 실제로 처리하다 예외를 만난 장면으로 먼저 읽는다. 예를 들면 null 처리 실패, DB 예외, 검증 누락 뒤 예상 못 한 분기 같은 경우다.

브라우저에서는 아래처럼 보일 수 있다.

- 응답 body가 서비스 공통 에러 JSON이다
- HTML 에러 페이지여도 app 템플릿 냄새가 난다
- gateway 기본 문구보다 서비스 이름, 요청 ID, 도메인 문맥이 더 눈에 띈다

물론 proxy가 `500`을 만들 수도 있지만, beginner 1차 분기로는 "`500`이면 app 응답 후보"라고 두는 편이 안전하다.

### `502`: upstream과 대화가 어긋난 경우가 많다

`502 Bad Gateway`는 브라우저와 app 사이에 proxy/gateway가 있고, 그 proxy가 upstream에서 기대한 응답을 못 받았을 때 자주 보인다.

초급자용으로는 이렇게 읽으면 된다.

- app이 아예 죽어 있거나 연결이 거절됨
- upstream이 응답을 중간에 비정상 종료함
- proxy가 이해할 수 없는 응답을 받음

DevTools `Headers`와 `Response`에서는 이런 단서가 자주 같이 붙는다.

- body가 아주 짧은 기본 HTML이고 제목이 `502 Bad Gateway`에 가깝다
- `Content-Type`이 `text/html`인데 서비스 공통 JSON 포맷은 보이지 않는다
- `Server`, `Via`, `X-Cache` 같은 앞단 흔적이 먼저 눈에 띈다

이 조합이면 app 에러 화면보다 proxy 에러 화면일 가능성이 높다.

### `504`: upstream을 기다리다 proxy가 먼저 포기한 경우가 많다

`504 Gateway Timeout`은 app이 느렸다는 뜻일 수는 있지만, **브라우저가 본 응답 주체는 proxy**인 경우가 많다. 즉 app이 1.2초 뒤 `200`을 만들었더라도, gateway timeout이 1.0초면 사용자는 `504`를 본다.

DevTools waterfall에서는 `waiting`이 길게 보이는 장면과 자주 붙는다. 이때 초급자 첫 문장은 "`app이 504를 반환했다`"보다 "`proxy가 upstream을 기다리다 timeout 났다`"가 더 정확하다.

body와 header도 같이 보면 더 안전하다.

- body가 짧은 기본 HTML이고 `Gateway Timeout` 문구가 전면에 보인다
- app JSON 에러 스키마 대신 gateway 기본 문구가 먼저 보인다
- waterfall의 `waiting`이 길고, app 팀 로그에는 뒤늦은 성공이 남을 수도 있다

즉 `504`는 "느림" 정보이기도 하지만, 동시에 "누가 종료를 선언했는가" 정보이기도 하다.

## 흔한 오해와 함정

- `502`를 보면 "애플리케이션이 bad gateway를 반환했다"고 말한다. 보통은 gateway가 한 말이다.
- `504`를 보면 "무조건 DB가 느리다"고 단정한다. 실제로는 timeout budget mismatch나 앞단 proxy 정책일 수 있다.
- `500`과 `502`를 둘 다 그냥 서버 에러로 뭉갠다. 둘 다 5xx지만 실패 위치가 다를 수 있다.
- body만 보고 확정한다. body가 gateway 기본 페이지인지, 서비스 공통 에러 포맷인지 header와 함께 봐야 한다.
- HTML이면 무조건 gateway라고 단정한다. app도 HTML 에러 페이지를 반환할 수 있으니 서비스 문맥과 header를 같이 봐야 한다.
- `Server` header 하나만 보고 확정한다. CDN, gateway, app server가 섞일 수 있어 body와 status를 함께 묶어야 한다.
- DevTools `Status`만 보고 끝낸다. `waiting`이 길었는지, 응답 header에 `server`/`via` 단서가 있는지도 같이 봐야 한다.

## 실무에서 쓰는 모습

예를 들어 `GET /api/orders`를 눌렀는데 아래 세 장면이 보였다고 하자.

| 장면 | 브라우저에서 보이는 것 | 초급자 첫 판독 |
|---|---|---|
| A | `500`, body가 서비스 공통 JSON 에러 | app이 직접 실패했을 가능성이 크다 |
| B | `502`, body가 짧은 gateway HTML | proxy가 upstream 연결/응답 문제를 대신 말했을 가능성이 크다 |
| C | `504`, waterfall `waiting`이 길다 | proxy가 upstream 기다리다 먼저 timeout 났을 가능성이 크다 |

조금 더 구체적으로 보면 아래처럼 읽을 수 있다.

| DevTools 장면 | 더 안전한 첫 문장 |
|---|---|
| `500` + `application/json` + 서비스 공통 `errorCode` 필드 | "app이 자기 에러 형식으로 실패를 응답했다" |
| `502` + 짧은 HTML + `Server`/`Via` 흔적 | "gateway가 upstream 문제를 자기 기본 페이지로 대신 말했다" |
| `504` + 짧은 HTML + 긴 `waiting` | "gateway가 upstream 기다리다 먼저 timeout을 선언했다" |

특히 C 장면에서는 app 로그에 늦은 `200` 성공이 남을 수도 있다. 그래서 사용자는 `504`를 봤는데 app 팀은 "우린 성공했어요"라고 말하는 일이 생긴다. 이건 서로 거짓말하는 게 아니라 **종료 지점을 다르게 본 것**이다.

브라우저에서 바로 할 수 있는 최소 체크는 3개다.

1. `Status`가 `500`인지 `502/504`인지 나눈다.
2. body와 header가 app 스타일인지 gateway 기본 페이지 스타일인지 본다.
3. `504`면 waterfall에서 `waiting`이 길었는지 같이 본다.

## 더 깊이 가려면

- 상태 코드 큰 그림부터 다시 잡으려면 [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- DevTools에서 뭘 먼저 볼지 고정하려면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- `Server`/`Via`/`X-Request-Id`를 따로 떼어 browser/proxy/app 1차 분기로 읽고 싶다면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- `waiting`이 왜 길게 보였는지 timing으로 풀려면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
- `502/504`가 proxy local reply인지 upstream app 결과인지 더 정확히 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- hop별 timeout이 왜 `edge 504`와 `app 200`를 같이 만들 수 있는지 보려면 [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- app 내부 처리 흐름과 예외 surface를 다시 잇고 싶다면 [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

## 한 줄 정리

브라우저에서 `500`은 app 실패 후보로, `502`는 upstream 연결/응답 문제를 본 proxy 후보로, `504`는 upstream 대기 timeout을 낸 proxy 후보로 먼저 나누면 첫 원인 분기가 훨씬 정확해진다.
