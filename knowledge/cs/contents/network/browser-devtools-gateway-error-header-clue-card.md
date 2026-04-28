# Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드

> 한 줄 요약: DevTools 응답 헤더에서 `Server`, `Via`, `X-Request-Id` 세 칸만 먼저 읽어도 "브라우저가 막은 건지, proxy가 대신 응답한 건지, app까지 들어간 건지"를 초급자 1차 분기로 빠르게 가를 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: server via x-request-id, devtools response header first pass, x-request-id 뭐예요, via 헤더 뭐예요, server 헤더 뭐예요, browser proxy app attribution, gateway error first check, response header who made this, 처음 devtools header, proxy 흔적 헤더, what is x-request-id, devtools 502 header clue

## 핵심 개념

처음에는 헤더를 많이 보지 말고, 이 세 개를 **명찰**처럼 읽으면 된다.

- `Server`: 누가 응답을 만든 것처럼 보이는가
- `Via`: 중간 proxy나 gateway를 거쳤는가
- `X-Request-Id`: 이 요청을 로그에서 다시 찾을 실마리가 있는가

초급자 첫 질문은 "정확한 근본 원인"이 아니라 "브라우저 / proxy / app 중 어디부터 봐야 하나"다. 이 세 헤더는 그 1차 분기에 도움을 준다.

## 한눈에 보기

| DevTools에서 먼저 보인 것 | 초급자 첫 해석 | 먼저 붙일 다음 질문 |
|---|---|---|
| 응답 헤더 자체가 거의 없다 | 브라우저 차단, 취소, 전송 실패처럼 HTTP 응답 전 단계일 수 있다 | `Status`가 `(blocked)`/`canceled`/`(failed)`인가 |
| `Server: nginx` 같은 값이 눈에 띈다 | proxy나 web server가 응답을 만든 장면 후보다 | body가 gateway 기본 HTML인가 |
| `Via: 1.1 varnish` 같은 값이 있다 | 중간 hop을 거쳤다는 뜻이다 | 이 응답이 app 원본인지, intermediary가 만든 응답인지 |
| `X-Request-Id`가 있다 | 적어도 추적용 식별자를 남길 만큼 서버 체인을 탔을 가능성이 크다 | app/log/trace에서 같은 ID를 찾을 수 있는가 |

짧게 외우면 이렇게 보면 된다.

```text
헤더 없음 -> 브라우저/전송 단계 의심
Server/Via 강함 -> proxy 문맥 먼저
X-Request-Id 있음 -> 서버 체인 추적 가능성 먼저
```

## 상세 분해

### `Server`

`Server`는 응답을 만든 소프트웨어 이름이 보일 때가 많다. 예를 들면 `nginx`, `envoy`, `cloudfront`, `Apache` 같은 값이 보일 수 있다.

초급자 1차 해석은 이 정도면 충분하다.

- proxy나 CDN 이름이 먼저 보이면 "앞단이 대신 말한 장면인가?"를 먼저 본다
- app이 늘 주는 JSON 에러 형식보다 기본 HTML 페이지가 더 강하면 proxy 응답 후보가 커진다

다만 `Server`는 최종 진실표가 아니다. 보안 정책 때문에 지워지거나, app server 이름과 reverse proxy 이름이 섞여 보일 수도 있다.

### `Via`

`Via`는 "이 응답이 중간 proxy를 거쳤다"는 흔적이다. 예를 들면 CDN, gateway, caching proxy가 응답을 전달하면서 붙일 수 있다.

초급자에게 중요한 해석은 하나다.

- `Via`가 보이면 browser와 app 사이에 intermediary가 있다는 뜻이므로, `502`/`504` 같은 응답을 app 코드만으로 바로 설명하지 않는다

즉 `Via`는 "누가 최종 에러를 만들었는가"를 100% 확정해 주지는 않지만, **proxy 문맥을 먼저 열어 주는 스위치**다.

### `X-Request-Id`

`X-Request-Id`는 요청 추적용 식별자다. gateway가 만들 수도 있고, app이 그대로 이어 받을 수도 있다.

초급자 첫 판단은 아래 두 줄이면 된다.

- 값이 있으면 "이 요청을 서버 로그에서 다시 찾을 실마리"가 있다
- 값이 app 로그와 같게 이어지면 "요청이 app까지 들어갔는지"를 확인하기 쉬워진다

그래서 `500`이나 `404`를 볼 때 `X-Request-Id`가 있으면, "브라우저가 혼자 실패했다"보다 "서버 체인 안에서 처리된 요청" 쪽으로 먼저 기운다.

### 세 헤더가 없을 때

이 경우는 오히려 해석이 쉬워질 때가 있다.

- `Status`가 `(blocked)`면 브라우저 정책/확장 프로그램/CORS 같은 browser-side 차단 후보
- `canceled`면 페이지 이동, 새로고침, JS abort 후보
- `(failed)`면 DNS, TLS, 네트워크 실패처럼 HTTP 응답 전에 끊긴 장면 후보

즉 **응답 헤더가 없다는 사실 자체**가 "app 에러 body를 읽는 단계가 아니었다"는 힌트가 될 수 있다.

## 흔한 오해와 함정

- `Server` 값 하나만 보고 "범인은 nginx다"라고 확정한다. `Server`는 힌트이지 판결문이 아니다.
- `Via`가 없으면 proxy가 없다고 단정한다. 일부 서비스는 `Via`를 숨기거나 다른 헤더만 남긴다.
- `X-Request-Id`가 없으면 app에 절대 도달하지 않았다고 말한다. 추적 헤더를 안 쓰는 서비스도 있다.
- `X-Request-Id`가 있으면 무조건 app이 직접 에러를 만들었다고 생각한다. gateway가 만든 응답에도 request ID는 붙을 수 있다.
- 브라우저 에러 장면에서 응답 헤더를 찾느라 시간을 쓴다. `(blocked)`·`canceled`·`(failed)`는 헤더보다 `Status` 판독이 먼저다.

## 실무에서 쓰는 모습

아래처럼 3장면만 구분해도 첫 DevTools pass 품질이 좋아진다.

| 장면 | DevTools에서 보이는 것 | 초급자 첫 문장 |
|---|---|---|
| A | `Status: 502`, `Server: nginx`, `Via: 1.1 varnish`, 짧은 HTML | "app JSON 에러보다 proxy/gateway 기본 응답 후보를 먼저 본다" |
| B | `Status: 500`, `Content-Type: application/json`, `X-Request-Id: 8f...` | "요청은 서버 체인으로 들어갔고 app 로그/trace를 먼저 찾는다" |
| C | `Status: (blocked)`, 응답 헤더 거의 없음 | "서버 에러보다 브라우저 차단 장면을 먼저 본다" |

실무에서 가장 안전한 3단계는 이렇다.

1. `Status`가 숫자인지, `(blocked)` 같은 브라우저 메모인지 먼저 가른다.
2. 숫자 응답이면 `Server`와 `Via`로 proxy 문맥을 본다.
3. `X-Request-Id`가 있으면 그 값을 incident 메모에 적고 로그 탐색 키로 쓴다.

## 더 깊이 가려면

- DevTools 첫 판독 순서 전체가 필요하면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- `500`/`502`/`504`를 첫 분기로 나누려면 [Browser DevTools `502` vs `504` vs App `500` 분기 카드](./browser-devtools-502-504-app-500-decision-card.md)
- header 기초가 아직 약하면 [HTTP 요청·응답 헤더 기초](./http-request-response-headers-basics.md)
- local reply인지 upstream 실패 번역인지 더 엄밀하게 가르려면 [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
- `X-Request-Id`가 실제 서버 처리 흐름에서 어디에 걸리는지 보려면 [Spring MVC 요청 생명주기 기초](../spring/spring-mvc-request-lifecycle-basics.md)

## 한 줄 정리

DevTools 첫 pass에서는 `Server`와 `Via`로 proxy 문맥을 먼저 열고, `X-Request-Id`로 서버 추적 가능성을 확인하며, 헤더가 거의 없으면 브라우저/전송 단계 실패를 먼저 의심하면 된다.
