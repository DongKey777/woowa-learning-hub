# Service Worker 개입 여부 빠른 확인 카드: `from ServiceWorker` vs HTTP cache

**난이도: 🟢 Beginner**

> 한 줄 요약: 먼저 `첫 방문`인지 `같은 URL 재방문`인지 한 줄로 가른 뒤, `from ServiceWorker`가 보이면 `Disable cache` 실험보다 먼저 "이번 줄에 Service Worker가 개입했는가"를 1분 안에 분리해야 한다. 그다음에 Cache Storage, HTTP cache, cookie, `sessionStorage`/`localStorage`를 서로 다른 저장소로 떼어 읽는다.

관련 문서:

- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Cache-Control 실전](./cache-control-practical.md)
- [Browser DevTools 새로고침 분기표: normal reload, hard reload, `Disable cache`](./browser-devtools-reload-hard-reload-disable-cache-primer.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [CDN 기초](../system-design/cdn-basics.md)

retrieval-anchor-keywords: from serviceworker quick check, service worker first minute card, disable cache before service worker, service worker vs http cache, cache storage vs http cache, from serviceworker, service worker vs memory cache, service worker vs disk cache, service worker vs 304, cache storage vs cookie vs localstorage, sessionstorage localstorage cookie cache confusion, browser storage comparison beginner, who served the body, devtools service worker triage, service worker cache 뭐예요

<details>
<summary>Table of Contents</summary>

- [왜 먼저 갈라야 하나](#왜-먼저-갈라야-하나)
- [먼저 잡을 멘탈 모델](#먼저-잡을-멘탈-모델)
- [첫 방문인지 반복 방문인지 먼저 한 줄 체크](#첫-방문인지-반복-방문인지-먼저-한-줄-체크)
- [`Disable cache`보다 먼저 보는 1분 카드](#disable-cache보다-먼저-보는-1분-카드)
- [정말 먼저 볼 4가지](#정말-먼저-볼-4가지)
- [1분 분기표](#1분-분기표)
- [service worker, cache storage, http cache 한 줄 비교](#service-worker-cache-storage-http-cache-한-줄-비교)
- [브라우저 저장소 전체 지도](#브라우저-저장소-전체-지도)
- [짧은 예시](#짧은-예시)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [cookie와 Web Storage까지 섞일 때](#cookie와-web-storage까지-섞일-때)
- [전송 경로와 cache 질문을 섞지 않는 법](#전송-경로와-cache-질문을-섞지-않는-법)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 먼저 갈라야 하나

초급자가 DevTools를 읽을 때 가장 자주 섞는 신호가 이 네 가지다.

- `from ServiceWorker`
- `from memory cache`
- `from disk cache`
- `304 Not Modified`

겉으로는 모두 "뭔가 빨랐다" 혹은 "body를 다시 안 받은 것 같다"로 보이지만, 질문 자체가 다르다.

- `from ServiceWorker`는 "브라우저 안의 Service Worker가 응답 경로에 끼어들었나?"
- `memory cache` / `disk cache`는 "브라우저 HTTP cache를 바로 재사용했나?"
- `304`는 "서버에 다시 물어봤더니 기존 사본을 계속 써도 된다고 했나?"

첫 화면에서 이걸 못 가르면 뒤에서 `Cache-Control`, `ETag`, `Protocol(h2/h3)`, offline 대응까지 전부 한 덩어리로 오해하게 된다.

---

## 먼저 잡을 멘탈 모델

한 줄로 잡으면 이렇다.

```text
첫 질문은 "누가 body를 건넸나?"다.

- Service Worker 경로가 응답을 가로챘나
- 그 안에서 Cache Storage를 썼나
- 아니면 브라우저 HTTP cache를 바로 썼나
- 아니면 서버 재검증 뒤 기존 cache를 계속 썼나
```

초급 멘탈 모델은 이렇게 두면 된다.

- Service Worker: 문 앞에서 응답 경로를 고를 수 있는 "중간 담당자"
- Cache Storage: Service Worker가 필요하면 꺼내 쓰는 앱 쪽 저장 상자
- HTTP cache: 브라우저가 `Cache-Control`, `ETag`, `304` 규칙으로 관리하는 내장 저장소
- cookie: 브라우저가 요청에 자동으로 실어 보낼 수 있는 작은 상태 조각
- `sessionStorage` / `localStorage`: 자바스크립트가 읽고 쓰는 앱 저장 칸

즉 `from ServiceWorker`는 **Service Worker 경로** 신호이고, `memory cache`/`disk cache`/`304`는 **HTTP cache 경로** 신호다. Cache Storage는 Service Worker가 선택적으로 쓸 수 있는 저장소이지, `from ServiceWorker`와 완전히 같은 말은 아니다.

---

## 첫 방문인지 반복 방문인지 먼저 한 줄 체크

분기표를 읽기 전에 첫 줄 메모 하나만 붙이면 초급자 혼선이 더 줄어든다.

| 먼저 적을 한 줄 | 바로 얻는 초급 결론 | 아직 하지 말아야 할 점프 |
|---|---|---|
| 첫 방문: 이 URL을 지금 탭/흐름에서 처음 열었다 | 아직 `memory cache`/`disk cache`/`304` 같은 반복 방문 신호를 기대하지 않는다 | 첫 줄부터 HTTP cache 판독으로 들어가기 |
| 반복 방문: 같은 URL을 다시 열거나 새로고침했다 | 이제 `from ServiceWorker`, `memory cache`, `disk cache`, `304` 중 무엇이 보이는지 읽을 차례다 | 재방문이라는 이유만으로 곧바로 `304`나 cache hit로 단정하기 |

한 줄 규칙:

1. 먼저 `첫 방문`인지 `반복 방문`인지 적는다.
2. 그다음 `from ServiceWorker`가 보이면 SW 경로부터 본다.
3. SW 신호가 없을 때만 `memory cache`/`disk cache`/`304` 판독으로 내려간다.

이 가드는 "지금 내가 cache 종류를 읽을 차례인가, 방문 맥락부터 적을 차례인가"를 먼저 분리해 준다.

---

## `Disable cache`보다 먼저 보는 1분 카드

`from ServiceWorker`가 이미 보였다면, 그 줄은 먼저 "cache 실험"이 아니라 "응답 경로 판독"으로 읽는다.

| 1분 안에 볼 것 | 왜 먼저 보나 | 바로 내릴 수 있는 초급 결론 |
|---|---|---|
| Network row에 `from ServiceWorker`가 있는지 | 현재 줄에 SW 경로가 끼었는지 확인하는 첫 단서다 | 적어도 HTTP cache만으로 설명하는 장면은 아닐 수 있다 |
| Application > Service Workers에 등록된 SW가 있는지 | "실제로 이 origin에서 SW가 살아 있나"를 본다 | 등록이 없으면 다른 원인을 의심하고, 등록이 있으면 SW 경로를 계속 본다 |
| 같은 URL에서 `memory cache`/`disk cache`/`304` 표기가 같이 보이는지 | HTTP cache 신호와 SW 신호를 섞지 않기 위해서다 | `from ServiceWorker`와 `304`는 같은 종류의 라벨이 아니다 |
| 그다음에야 `Disable cache` 실험으로 넘어갈지 | SW 개입 여부를 모른 채 실험하면 관찰 질문이 뒤섞인다 | 먼저 "누가 body를 건넸나"를 정리한 뒤 ON/OFF 실험을 한다 |

가장 짧은 순서는 아래 4줄이면 된다.

1. 먼저 이 줄이 `첫 방문`인지 `반복 방문`인지 적는다.
2. row에 `from ServiceWorker`가 보이는지 본다.
3. Application 탭에서 SW 등록 여부를 본다.
4. 같은 줄을 `memory cache`/`disk cache`/`304`와 같은 bucket으로 읽지 않는다.
5. 그 뒤에만 [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)로 넘어간다.

즉 `Disable cache`는 첫 질문이 아니라, **SW 개입 여부를 분리한 뒤에 하는 비교 실험**이다.

---

## 정말 먼저 볼 4가지

`from ServiceWorker`가 보일 때 초급자가 1분 안에 확인할 포인트는 아래 4개면 충분하다.

| 바로 볼 곳 | 1분 질문 | 초급자 메모 |
|---|---|---|
| Network row | 지금 문제 삼는 URL 줄에 정말 `from ServiceWorker`가 찍혔나 | 다른 정적 파일 줄과 섞어 읽지 않는다 |
| Application > Service Workers | 등록된 SW가 있고 scope가 이 URL을 덮나 | 등록만 있고 scope가 다르면 이번 줄 설명이 안 될 수 있다 |
| Sources 또는 SW 코드 위치 메모 | fetch handler가 응답 경로를 바꿀 수 있는 구조인가 | "SW가 존재한다"와 "이번 요청을 실제로 가로챘다"를 분리한다 |
| Application > Cache Storage | key가 있더라도 이번 응답이 그 key에서 바로 나왔는지 아직 모른다 | entry 존재 = 현재 row의 원인 확정 아님 |

이 4개를 본 뒤에도 질문은 여전히 하나다.

- "이번 body를 누가 건넸나?"

여기까지 정리되면 그다음에만 `Disable cache` ON/OFF 실험으로 넘어간다.

---

## 1분 분기표

| DevTools 첫 신호 | 먼저 내릴 결론 | 바로 이어서 볼 것 | 아직 내리면 안 되는 결론 |
|---|---|---|---|
| row에 `from ServiceWorker`가 보임 | Service Worker가 응답 경로에 관여했을 가능성을 먼저 본다 | Application 탭의 Service Workers, SW fetch handler 유무, offline/cache storage 전략 | "이건 memory cache hit다", "304다" |
| row에 `from memory cache`가 보임 | 브라우저가 메모리 사본을 바로 썼을 가능성을 먼저 본다 | request header에 validator가 없는지, waterfall이 즉시 끝나는지 | "Service Worker가 준 응답이다", "서버 304였다" |
| row에 `from disk cache`가 보임 | 브라우저가 디스크 사본을 바로 썼을 가능성을 먼저 본다 | validator request 부재, 짧은 waterfall | "Service Worker가 준 응답이다", "재검증이 있었다" |
| status가 `304`이고 request에 `If-None-Match`/`If-Modified-Since`가 보임 | 서버 재검증 후 기존 cache body를 다시 쓴다 | request/response headers, transfer size, 서버 로그 | "서버에 안 갔다", "그냥 memory cache와 같다" |
| status `200` + cache 표기 없음 | 새 네트워크 응답일 가능성을 먼저 본다 | response headers, body, timing, protocol | "빠르니 무조건 cache hit다" |

가장 짧은 규칙:

1. `from ServiceWorker`가 먼저 보이면 Service Worker 경로부터 분리한다.
2. 그게 아니면 `memory cache` / `disk cache` / validator+`304` 중 어디인지 본다.
3. `Protocol(h2/h3)`은 전송 경로 신호이지, cache 종류 이름이 아니다.

한 문장으로 압축하면:

- `from ServiceWorker`는 "중간 담당자가 응답 경로에 끼어들었나"
- Cache Storage는 "그 담당자가 자기 저장 상자에서 꺼냈나"
- HTTP cache는 "브라우저가 `memory`/`disk`/`304` 규칙으로 재사용했나"

---

## Service Worker, Cache Storage, HTTP cache 한 줄 비교

| 질문 | Service Worker | Cache Storage | HTTP cache (`memory`/`disk`/`304`) |
|---|---|---|---|
| 역할 | 응답 경로에 개입할 수 있는 실행 주체 | Service Worker가 앱 코드로 관리하는 저장소 | 브라우저가 HTTP 규칙으로 관리하는 저장소/재검증 흐름 |
| DevTools 첫 신호 | row에 `from ServiceWorker` | Application > Cache Storage에서 key 확인 | row의 `from memory cache`/`from disk cache`, request validator, `304` |
| 주된 판단 자리 | fetch handler, offline 동작, SW 등록 상태 | Cache Storage key/entry, 앱이 붙인 이름 | response header, request validator, Network row |
| 서버 왕복 | 있을 수도, 없을 수도 있음 | 없을 수도 있지만 SW가 fetch를 같이 할 수도 있음 | `memory`/`disk`는 보통 없음, `304`는 있음 |
| 초급자 오해 | "곧바로 Cache Storage를 쓴 뜻이다" | "브라우저 HTTP cache랑 같은 저장소다" | "다 같은 cache hit 이름이다" |

---

## 브라우저 저장소 전체 지도

초급자 혼선은 보통 "브라우저 안에 저장된다"는 공통점 때문에 생긴다. 하지만 질문을 두 칸으로 나누면 정리가 빨라진다.

1. 이 저장소가 **HTTP 요청/응답 경로**를 바꾸는가?
2. 아니면 **앱 상태만 보관**하는가?

| 저장소/개념 | 주인 | 무엇을 넣나 | HTTP 요청에 자동으로 영향이 가나 | DevTools에서 먼저 볼 곳 | 가장 흔한 오해 |
|---|---|---|---|---|---|
| Service Worker | 브라우저 안의 SW 스크립트 | fetch 처리 로직 | 그럴 수 있다. 응답 경로를 가로챌 수 있다 | Network `from ServiceWorker`, Application > Service Workers | "저장소 이름이다" |
| Cache Storage | SW/앱 코드 | `Request`-`Response` 쌍 | 자동 아님. SW 코드가 꺼내 써야 한다 | Application > Cache Storage | "HTTP cache와 같은 상자다" |
| HTTP cache | 브라우저 | HTTP 응답 사본 | 그렇다. 브라우저가 `Cache-Control`, `ETag`, `304` 규칙으로 재사용한다 | Network `from memory cache`, `from disk cache`, `304` | "cookie나 localStorage랑 같은 층이다" |
| cookie | 브라우저 | session id, preference, token 같은 작은 값 | 그럴 수 있다. 조건이 맞는 요청에 `Cookie` 헤더로 자동 전송된다 | Application > Cookies, Network request headers | "cookie에 있으면 곧 cache hit다" |
| `sessionStorage` | 페이지 스크립트 | 탭 단위 앱 상태 | 아니다. JS가 직접 읽어 헤더/본문에 넣지 않으면 네트워크에 안 실린다 | Application > Session Storage | "브라우저가 다음 요청에 알아서 보낸다" |
| `localStorage` | 페이지 스크립트 | 브라우저에 남겨둘 앱 상태 | 아니다. JS가 직접 사용해야 한다 | Application > Local Storage | "cookie처럼 자동 전송된다" |

한 줄로 외우면:

- Cache Storage와 HTTP cache는 둘 다 "응답 사본" 쪽이다.
- cookie는 "자동 전송될 수 있는 상태" 쪽이다.
- `sessionStorage`/`localStorage`는 "JS가 직접 꺼내 쓰는 앱 상태" 쪽이다.

즉 `localStorage`에 토큰이 있어도 브라우저는 그 값을 보고 자동으로 `Authorization` 헤더를 만들지 않는다. 반대로 cookie는 JS가 안 만져도 조건이 맞으면 요청에 실릴 수 있다.

---

## 짧은 예시

### 예시 0. 가장 흔한 한 줄 혼동

상황:

- 같은 `app.js`를 다시 열었다
- DevTools에는 `from ServiceWorker`가 보인다
- Application 탭에는 Cache Storage key도 하나 보인다

첫 판독:

- 여기서 바로 확정할 수 있는 것은 "이번 응답 경로에 Service Worker가 관여했다"까지다.
- Cache Storage key가 있다고 해서 이번 응답이 반드시 그 key에서 나온 것은 아니다.
- Service Worker가 `fetch()`로 네트워크에 다시 갔을 수도 있으니, Cache Storage와 HTTP cache를 같은 상자로 읽으면 안 된다.
- 이 시점에는 `Disable cache`를 바로 켜기보다, 먼저 SW 등록 여부와 `304`/`memory cache`/`disk cache` 신호가 섞였는지부터 본다.

### 예시 1. `from ServiceWorker`

상황:

- Network row에 `from ServiceWorker`
- `Status 200`
- offline에서도 같은 응답이 계속 보임

첫 판독:

- 이건 먼저 Service Worker fetch handler나 Cache Storage 전략을 의심하는 케이스다.
- HTTP `304`/validator 문제로 바로 들어가면 첫 단추가 틀릴 수 있다.

### 예시 2. `304 Not Modified`

상황:

- request header에 `If-None-Match: "app-v12"`
- response status `304`
- `Protocol h2`

첫 판독:

- HTTP/2로 서버까지 재검증을 갔다.
- 최종 body는 기존 cache 사본을 썼다.
- 여기서 `h2`는 전송 경로고, `304`는 재검증 결과다.

### 예시 3. `from memory cache`

상황:

- row에 `from memory cache`
- validator request가 안 보임
- waterfall이 거의 즉시 끝남

첫 판독:

- 브라우저가 fresh한 사본을 메모리에서 바로 재사용했다.
- 서버 재검증이 아니라 local reuse에 더 가깝다.

### 예시 4. 같은 URL을 다시 봤는데 `from ServiceWorker`와 `304`가 번갈아 보인다

상황:

- 같은 `/feed` URL을 다시 방문했다
- 한 번은 row에 `from ServiceWorker`
- 다른 한 번은 request에 `If-None-Match`가 있고 status가 `304`

첫 판독:

## 짧은 예시 (계속 2)

- 둘 다 "같은 URL 재방문"이지만 질문이 다르다.
- `from ServiceWorker`가 보인 순간에는 먼저 "이번 body를 Service Worker가 건넸나?"를 본다.
- `304`가 보인 순간에는 먼저 "이번엔 서버 재검증까지 갔나?"를 본다.
- `304` 흐름 자체는 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)에서 이어서 읽으면 된다.

---

## 자주 헷갈리는 포인트

### `from ServiceWorker`는 `memory cache`의 다른 이름이 아니다

둘 다 브라우저 안쪽처럼 보이지만 계층이 다르다.

- `from ServiceWorker`는 Service Worker 스크립트가 응답 경로에 개입한 신호다.
- `memory cache`/`disk cache`는 브라우저 HTTP cache tier 신호다.

### `from ServiceWorker`가 보여도 Cache Storage를 썼다고 바로 단정하면 안 된다

Service Worker는 여러 선택을 할 수 있다.

- `caches.match()`로 Cache Storage에서 꺼낼 수 있다
- 그냥 `fetch()`로 네트워크에 다시 갈 수 있다
- 둘을 섞어 fallback할 수도 있다

그래서 `from ServiceWorker`는 "Service Worker가 관여했다"까지는 말해 주지만, "반드시 Cache Storage hit였다"까지 자동으로 말해 주지는 않는다.

### SW 등록과 scope 확인이 먼저인 이유

초급자가 가장 많이 놓치는 부분은 "SW가 있다"와 "이 URL이 그 SW scope 안에 있다"를 같은 말로 읽는 것이다.

- 등록된 SW가 있어도 scope 밖 URL이면 다른 설명을 찾아야 한다
- scope 안이어도 fetch handler가 단순 pass-through일 수 있다

그래서 `Disable cache`를 켜기 전에, 먼저 "등록됨", "scope 안", "응답 경로 개입 가능" 이 세 칸을 분리해 두는 편이 안전하다.

### Cache Storage와 HTTP cache는 "둘 다 cache"여도 관리 주체가 다르다

초급 단계에서는 이 한 줄만 확실히 잡으면 된다.

- Cache Storage: 앱 코드나 Service Worker가 key를 보고 직접 꺼내는 상자
- HTTP cache: 브라우저가 `Cache-Control`, `ETag`, `Last-Modified`, `304` 규칙으로 자동 관리하는 상자

즉 둘 다 저장은 하지만, 같은 규칙으로 움직이지 않는다.

### Application 탭과 Network 탭이 답하는 질문도 다르다

처음 읽을 때는 탭별 질문을 분리하면 덜 헷갈린다.

- Application > Cache Storage는 "저장 상자 안에 entry가 있나?"를 보여 준다
- Network row의 `from memory cache`/`from disk cache`/`304`는 "이번 요청 body를 어디서 가져왔나?"를 보여 준다

그래서 Application 탭에서 Cache Storage key를 봤다고 해서, 이번 Network row가 곧바로 그 entry를 썼다고 자동 확정되지는 않는다.

### `304`와 `from ServiceWorker`를 같은 줄에서 읽으면 질문이 섞인다

## 자주 헷갈리는 포인트 (계속 2)

`304`는 서버 재검증 결과이고, `from ServiceWorker`는 브라우저 앱 계층 개입 여부다.
둘을 같은 bucket으로 묶으면 "누가 응답했는가"와 "서버에 다시 물어봤는가"를 동시에 놓친다.

---

## cookie와 Web Storage까지 섞일 때

### cookie는 cache가 아니라 "자동 전송될 수 있는 상태"에 가깝다

- cookie는 브라우저가 `Cookie` 헤더로 다시 실어 보낼 수 있다
- HTTP cache는 body 재사용 여부를 다룬다

즉 cookie가 있다고 해서 응답 body가 reuse됐다는 뜻은 아니다. 반대로 `304`가 보여도 login cookie와는 다른 질문이다.

### `sessionStorage`와 `localStorage`는 네트워크 자동 저장소가 아니다

- 둘 다 브라우저의 Web Storage다
- JS가 직접 `getItem()` 해서 요청 헤더나 body에 넣어야 네트워크에 영향이 간다

그래서 Application 탭에서 `localStorage` 값이 보여도, Network request header에 아무 변화가 없을 수 있다. 이 경우 질문은 "값이 저장됐나?"이지 "브라우저가 자동 전송했나?"가 아니다.

### 초급자용 3문장 정리

- cookie는 "브라우저가 자동 전송할 수 있는 값"이다.
- `sessionStorage`/`localStorage`는 "JS가 직접 꺼내 써야 하는 값"이다.
- HTTP cache와 Cache Storage는 "응답 사본을 어디서 다시 쓰는가"를 보는 값이다.

---

## 전송 경로와 cache 질문을 섞지 않는 법

### `Protocol(h2/h3)`만 보고 cache 종류를 결정하면 안 된다

`h2`/`h3`는 전송 경로다.

- `304 + h2`일 수 있다
- `304 + h3`일 수 있다
- `from ServiceWorker`가 보여도 내부적으로 네트워크 fetch가 한 번 더 있었을 수 있다

즉 protocol 열만으로는 Service Worker / memory cache / disk cache / 304를 가를 수 없다.

### Service Worker가 있으면 HTTP cache가 완전히 사라지는 것은 아니다

Service Worker가 있어도 내부에서 네트워크 fetch를 하거나, 별도의 cache 전략을 쓸 수 있다.
초급 단계에서는 먼저 "`from ServiceWorker`가 보이면 HTTP cache primer와는 다른 갈래가 하나 더 열린다"까지만 잡으면 충분하다.

---

## 다음에 이어서 볼 문서

- `memory cache`, `disk cache`, `304` trace를 더 자세히 읽고 싶다면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- `Cache-Control`, `ETag`, `Last-Modified`, `304`의 의미를 처음부터 다시 묶고 싶다면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- cookie가 왜 자동 전송되고 `localStorage`는 왜 자동 전송되지 않는지 이어서 보려면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- directive 차이까지 올라가려면 [Cache-Control 실전](./cache-control-practical.md)
- `Protocol(h2/h3)` 열을 왜 cache 종류와 분리해서 읽어야 하는지 보려면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)

---

## 한 줄 정리

같은 브라우저 저장소처럼 보여도 `from ServiceWorker`는 응답 경로, Cache Storage와 HTTP cache는 응답 사본, cookie는 자동 전송 상태, `sessionStorage`/`localStorage`는 JS 앱 상태를 뜻하므로 먼저 "누가 자동으로 무엇을 하느냐"부터 분리해서 읽어야 한다.
