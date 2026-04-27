# HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304

**난이도: 🟢 Beginner**

> 한 줄 요약: 브라우저가 응답을 저장하고 서버에 "다시 받아야 하나?"를 묻는 흐름을 Cache-Control, ETag, Last-Modified, 304를 중심으로 정리한 입문 primer

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md)
- [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
- [CDN 기초](../system-design/cdn-basics.md)
- [CORS 기초](../security/cors-basics.md)

retrieval-anchor-keywords: http caching basics, conditional request, cache-control, etag, last-modified, 304 not modified, if-none-match, cache revalidation, html vs app.js cache, static asset cache experiment, from disk cache vs 304, beginner http caching

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [한 번에 보는 전체 흐름](#한-번에-보는-전체-흐름)
- [왜 첫 실험은 HTML보다 `app.js`/`main.css`가 쉬운가](#왜-첫-실험은-html보다-appjsmaincss가-쉬운가)
- [Cache-Control은 무엇을 정하나](#cache-control은-무엇을-정하나)
- [ETag와 Last-Modified는 무엇을 하나](#etag와-last-modified는-무엇을-하나)
- [조건부 요청은 어떻게 오가나](#조건부-요청은-어떻게-오가나)
- [304 Not Modified는 무엇을 의미하나](#304-not-modified는-무엇을-의미하나)
- [304와 프로토콜 fallback은 다른 질문이다 (bridge)](#304와-프로토콜-fallback은-다른-질문이다-bridge)
- [브라우저와 서버는 각자 무엇을 하나](#브라우저와-서버는-각자-무엇을-하나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 중요한가

HTTP 캐시는 단순히 "응답을 저장한다"로 끝나지 않는다.

브라우저는 매 요청마다 다음 두 질문을 판단한다.

- 지금 캐시된 응답을 바로 써도 되는가
- 서버에 다시 확인해야 한다면 무엇을 기준으로 비교할 것인가

이 질문에 답하는 조합이 `Cache-Control`, `ETag`, `Last-Modified`, `304 Not Modified`다.

---

## 한 번에 보는 전체 흐름

브라우저와 서버 사이 흐름을 가장 단순하게 그리면 아래와 같다.

```text
1. 브라우저가 GET /articles/10 요청
2. 서버가 200 OK + Cache-Control + ETag + Last-Modified 응답
3. 브라우저가 body와 메타데이터를 함께 저장
4. 응답이 fresh하면 브라우저가 바로 캐시를 재사용
5. 응답이 stale하거나 no-cache면 브라우저가 조건부 요청 전송
6. 서버가 안 바뀌었으면 304 Not Modified
7. 브라우저가 기존 body를 다시 사용
8. 서버가 바뀌었으면 200 OK + 새 body + 새 validator
```

핵심은 역할이 나뉜다는 점이다.

- `Cache-Control`: 이 응답을 얼마나 오래 그냥 써도 되는지
- `ETag`, `Last-Modified`: 다시 확인할 때 무엇을 비교할지
- `304 Not Modified`: 서버가 "기존 사본 그대로 써도 된다"고 답하는 방식

처음 읽을 때 가장 헷갈리는 `from disk cache`와 `304`는 이 두 칸만 먼저 나눠도 된다.

| 장면 | 서버 왕복 | validator 사용 | body는 어디서 옴 |
|---|---|---|---|
| `from memory cache` / `from disk cache` | 보통 없음 | 보통 없음 | 브라우저가 저장해 둔 사본 |
| `304 Not Modified` | 있음 | 있음 (`If-None-Match`, `If-Modified-Since`) | 브라우저가 저장해 둔 사본 |

---

## 왜 첫 실험은 HTML보다 `app.js`/`main.css`가 쉬운가

초급자 첫 캐시 실험은 "같은 URL을 반복 요청했을 때 뭐가 바뀌는지"를 보는 일이다. 이때는 로그인 상태, 개인화, 서버 템플릿 변화가 섞이기 쉬운 HTML보다 정적 파일이 더 단순하다.

| 첫 실험 대상 | 초급자에게 어떻게 보이나 | 첫 실험용 적합도 |
|---|---|---|
| `index.html` 같은 HTML | redirect, cookie, 로그인 상태, SSR 템플릿 변화가 섞여 `200`/`304` 이유가 여러 갈래로 보일 수 있다 | 보통 |
| `app.js`, `main.css` 같은 정적 리소스 | 같은 URL을 반복 호출하기 쉽고, body 변화 유무가 단순해서 `from disk cache`나 `304`를 읽기 쉽다 | 높음 |

즉 "HTML은 캐시가 안 된다"가 아니라, **첫 관찰 대상을 더 조용한 정적 파일로 고르자**는 뜻이다.

가장 쉬운 순서는 이렇다.

1. DevTools `Network`를 열고 `Disable cache`를 끈다.
2. `app.js` 또는 `main.css` 한 개를 고른다.
3. `normal reload`를 두세 번 하며 `200 -> from disk cache` 또는 `200 -> 304` 변화를 본다.

HTML은 그다음 단계에서 "문서도 같은 원리로 캐시되지만 주변 조건이 더 많다"는 비교 대상으로 보면 된다.

---

## Cache-Control은 무엇을 정하나

`Cache-Control`은 캐시 정책 헤더다.

브라우저 입장에서는 주로 "이 응답이 아직 fresh한가"를 판단하는 기준이 된다.

### 자주 보는 값

### `max-age=60`

- 60초 동안은 fresh하다고 본다
- 브라우저는 그동안 서버에 다시 묻지 않고 재사용할 수 있다

### `no-cache`

- 저장은 가능하다
- 다만 재사용하기 전에 서버에 반드시 재검증해야 한다
- 이름 때문에 "캐시 금지"로 오해하기 쉽다

### `no-store`

- 저장 자체를 하지 말라는 뜻이다
- 민감한 응답이나 매번 완전히 새로 받아야 하는 응답에 쓴다

### `private`

- 브라우저 같은 개인 캐시에 저장하는 것은 괜찮다
- 공유 캐시에는 보수적으로 접근해야 한다

### `public`

- 공유 캐시도 저장 가능하다는 뜻이다
- CDN이나 프록시까지 함께 고려할 때 자주 본다

입문 감각으로 정리하면:

- `Cache-Control`은 "지금 바로 써도 되나?"를 정한다
- `ETag`, `Last-Modified`는 "다시 확인할 때 뭘 들고 갈까?"를 정한다

---

## ETag와 Last-Modified는 무엇을 하나

둘 다 **validator**다.

즉 브라우저가 서버에 "내가 가진 사본이 아직 최신인가?"를 물을 때 비교 기준으로 쓴다.

### `ETag`

- 서버가 응답 버전을 식별하기 위해 붙이는 값이다
- 예: `"article-10-v3"`
- 브라우저는 나중에 `If-None-Match`로 다시 보낸다

쉽게 말하면 `ETag`는 "이 응답의 버전표"에 가깝다.

### `Last-Modified`

- 서버가 이 리소스가 마지막으로 바뀐 시각을 알려준다
- 예: `Tue, 14 Apr 2026 09:00:00 GMT`
- 브라우저는 나중에 `If-Modified-Since`로 다시 보낸다

쉽게 말하면 `Last-Modified`는 "마지막 수정 시각"이다.

### 둘의 차이

- `ETag`는 보통 더 정밀하다
- `Last-Modified`는 시간 기반이라 이해하기 쉽다
- 같은 초 안에 여러 번 바뀌는 경우에는 `Last-Modified`만으로는 부족할 수 있다

실무에서는 둘을 함께 보내기도 하고, 비교는 `ETag`가 더 우선적인 validator로 쓰이는 경우가 많다.

그리고 `ETag` 안에서도 strong/weak 차이가 있다.

- byte-level correctness나 `If-Match`, `If-Range`까지 걸리면 strong semantics가 중요하다
- `GET`/`HEAD` 재검증처럼 full representation reuse만 보면 weak ETag도 쓸 수 있다

이 차이는 [Strong vs Weak ETag: validator 정밀도와 cache correctness](./strong-vs-weak-etag-validator-precision-cache-correctness.md)에서 이어서 본다.

---

## 조건부 요청은 어떻게 오가나

조건부 요청은 브라우저가 기존 사본을 들고 서버에 재확인하는 요청이다.

### 1. 첫 요청: 서버가 사본과 validator를 내려준다

```http
GET /articles/10 HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 200 OK
Cache-Control: max-age=60
ETag: "article-10-v3"
Last-Modified: Tue, 14 Apr 2026 09:00:00 GMT
Content-Type: text/html; charset=UTF-8

<html>...</html>
```

이 시점에 브라우저는:

- 응답 body
- `Cache-Control`
- `ETag`
- `Last-Modified`

를 함께 저장한다.

### 2. fresh 기간 안이라면 브라우저가 그대로 재사용한다

`max-age=60` 안쪽이라면 브라우저는 같은 리소스를 다시 요청할 때 서버에 바로 가지 않을 수 있다.

즉:

- 네트워크 왕복이 줄어든다
- 서버 부하가 줄어든다
- 브라우저 입장에서는 더 빠르게 렌더링할 수 있다

### 3. stale해지면 브라우저가 validator를 들고 다시 묻는다

60초가 지났거나, 응답이 `no-cache`였다면 브라우저는 조건부 요청을 보낼 수 있다.

```http
GET /articles/10 HTTP/1.1
Host: example.com
If-None-Match: "article-10-v3"
If-Modified-Since: Tue, 14 Apr 2026 09:00:00 GMT
```

브라우저가 서버에 묻는 뜻은 이렇다.

- 내가 가진 `ETag`가 아직 최신인가
- 내가 가진 수정 시각 이후로 바뀐 적이 없는가

### 4-A. 서버가 안 바뀌었다고 판단하면 304를 돌려준다

```http
HTTP/1.1 304 Not Modified
Cache-Control: max-age=60
ETag: "article-10-v3"
Last-Modified: Tue, 14 Apr 2026 09:00:00 GMT
```

이 응답에는 보통 body가 없다.

브라우저는:

- 기존에 저장해 둔 body를 다시 사용하고
- freshness 메타데이터를 갱신한다

### 4-B. 서버가 바뀌었다고 판단하면 새 200 응답을 준다

```http
HTTP/1.1 200 OK
Cache-Control: max-age=60
ETag: "article-10-v4"
Last-Modified: Tue, 14 Apr 2026 09:05:00 GMT
Content-Type: text/html; charset=UTF-8

<html>...new...</html>
```

브라우저는 새 body와 새 validator를 저장하고, 그다음부터는 새 사본 기준으로 움직인다.

---

## 304 Not Modified는 무엇을 의미하나

`304 Not Modified`는 서버가 "네가 이미 가진 사본을 계속 써도 된다"고 답한 것이다.

입문 단계에서 꼭 기억할 점:

- `304`는 리다이렉트가 아니다
- `304`는 캐시 재검증 결과이지, HTTP 버전 fallback/downgrade 신호가 아니다 (헷갈리면 [304와 프로토콜 fallback은 다른 질문이다 (bridge)](#304와-프로토콜-fallback은-다른-질문이다-bridge))
- 보통 response body가 없다
- 브라우저가 이미 갖고 있던 body를 재사용한다
- 네트워크 왕복은 있었지만, body 전체를 다시 받지는 않는다

즉 `304`의 핵심 가치는 "다시 다운로드하지 않아도 되는지"를 확인하는 데 있다.

---

## 304와 프로토콜 fallback은 다른 질문이다 (bridge)

먼저 한 줄로 구분하면:

- `304`는 "같은 리소스 본문을 다시 받을지"를 묻는 **캐시 재검증** 신호다.
- protocol fallback/downgrade는 "이번 요청을 HTTP/3 대신 HTTP/2(또는 HTTP/1.1)로 보낼지"를 묻는 **전송 경로** 신호다.

| 질문 | 대표 신호 |
| --- | --- |
| 본문을 다시 다운로드할까? | `ETag`/`If-None-Match`, `Last-Modified`/`If-Modified-Since`, `304` |
| 어떤 HTTP 버전으로 연결할까? | `Alt-Svc`, ALPN, UDP 차단 여부, H2/H1 fallback |

즉 `304`가 보여도 "프로토콜이 내려갔다"는 뜻은 아니다. 프로토콜 fallback 판단은 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)에서 따로 본다.

같은 browsing session 안에서도 두 판단은 독립적으로 일어날 수 있다.

| 시점 | 브라우저가 결정하는 것 | 결과 |
| --- | --- | --- |
| 첫 방문 | 아직 캐시 사본이 없고, 서버가 H2로 응답 | `200 OK over h2` + `ETag: "v1"` 저장 |
| 같은 탭에서 1분 뒤 재방문 | 이번엔 H3가 가능해서 H3로 연결, 하지만 리소스는 안 바뀜 | `304 Not Modified over h3`, body는 기존 캐시 재사용 |

이 예시의 핵심은 이렇다.

- `h2 -> h3`는 "어느 전송 경로로 갈까?"에 대한 답이다.
- `200 -> 304`는 "본문을 다시 받을까?"에 대한 답이다.
- 그래서 같은 세션에서 **프로토콜은 바뀌어도 캐시 재검증 결과는 그대로 `304`일 수 있다.**

---

## 브라우저와 서버는 각자 무엇을 하나

### 브라우저

- 응답의 `Cache-Control`을 보고 fresh/stale를 판단한다
- 저장된 `ETag`, `Last-Modified`를 기억한다
- stale하거나 재검증이 필요하면 `If-None-Match`, `If-Modified-Since`를 보낸다
- `304`를 받으면 기존 body를 꺼내 쓴다

### 서버

- 응답에 `Cache-Control`, `ETag`, `Last-Modified`를 넣어 준다
- 요청에 들어온 `If-None-Match`, `If-Modified-Since`를 현재 상태와 비교한다
- 안 바뀌었으면 `304`
- 바뀌었으면 `200`과 새 body를 보낸다

이 역할 분담을 이해하면 "왜 어떤 때는 서버 로그가 안 찍히고", "왜 어떤 때는 304만 찍히는지"를 해석하기 쉬워진다.

---

## 자주 헷갈리는 포인트

### `no-cache`는 캐시 금지가 아니다

- 저장은 가능하다
- 다만 재사용 전에 검증해야 한다

### `Cache-Control`과 `ETag`는 역할이 다르다

- `Cache-Control`: fresh 기간과 저장 정책
- `ETag`, `Last-Modified`: 재검증용 비교 기준

### `304`는 body를 나중에 보내겠다는 뜻이 아니다

- body는 브라우저가 자기 캐시에서 꺼낸다
- `304` 응답 자체는 보통 매우 작다

### `from disk cache`와 `304`는 같은 말이 아니다

- 둘 다 최종 body는 브라우저 캐시에서 꺼내 쓸 수 있다
- 하지만 `from disk cache`는 보통 서버에 안 간다
- `304`는 validator를 들고 서버에 다시 확인한 뒤 기존 body를 재사용한다

### `304`가 H2에서 보이다가 다음엔 H3에서 보여도 이상한 것이 아니다

- 같은 브라우징 세션에서도 첫 요청은 `h2`, 다음 요청은 `h3`가 될 수 있다
- 그와 별개로 리소스가 안 바뀌면 두 번째 요청은 `304`가 될 수 있다
- 즉 `304`는 캐시 판정이고, `h2`/`h3`는 연결 판정이다

### `Last-Modified`만으로는 세밀한 변경을 놓칠 수 있다

- 시간 단위 비교라 정밀도 한계가 있다
- 더 정교한 비교가 필요하면 `ETag`가 유리하다

### shared cache/CDN 문제는 여기서 더 복잡해진다

브라우저 단일 캐시를 넘어서 `Vary`, compression variant, CDN key가 섞이면 이야기가 더 어려워진다. 그때는 [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)과 [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)을 같이 본다.

---

## 한 줄 정리

`Cache-Control`로 fresh 기간을 정하고, `ETag`·`Last-Modified`로 재검증 기준을 제공하며, 서버가 변경이 없으면 `304 Not Modified`로 body 없이 응답해 브라우저가 기존 사본을 재사용하게 하는 것이 HTTP 캐싱의 핵심 흐름이다.
