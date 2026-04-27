# Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant

> 한 줄 요약: 같은 URL이라도 언어, 압축, 표현 형식이 달라질 수 있다. `Vary`는 서버가 어떤 request 헤더를 보고 응답 variant를 골랐는지 cache에 알려 주는 표지판이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 관련 문서:
> - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
> - [Cache-Control 실전](./cache-control-practical.md)
> - [CDN Cache Key와 Invalidation](./cdn-cache-key-invalidation.md)
> - [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

retrieval-anchor-keywords: vary basics, content negotiation basics, response variant, representation selection, language variant cache, compression variant cache, accept-language vary, accept-encoding vary, beginner vary primer, cache key by representation, vary content negotiation basics language compression basics, vary content negotiation basics language compression beginner, vary content negotiation basics language compression intro, network basics, beginner network

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [Content Negotiation은 무엇인가](#content-negotiation은-무엇인가)
- [Vary는 무엇을 알려주나](#vary는-무엇을-알려주나)
- [언어 variant: `Accept-Language`](#언어-variant-accept-language)
- [압축 variant: `Accept-Encoding`](#압축-variant-accept-encoding)
- [다른 response variant는 어떻게 보나](#다른-response-variant는-어떻게-보나)
- [`Cache-Control`, validator와는 어떻게 연결되나](#cache-control-validator와는-어떻게-연결되나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 문서가 필요한가

입문 단계에서는 cache를 "응답을 저장하는 기능"으로만 이해하기 쉽다.

하지만 실제 HTTP 응답은 URL 하나에 딱 하나만 있는 것이 아니다.

- 한국어 페이지와 영어 페이지
- gzip 응답과 brotli 응답
- JSON 응답과 HTML 응답

처럼 **같은 URL인데도 다른 representation(응답 variant)** 이 존재할 수 있다.

문제는 cache가 이 차이를 모르면 한 사용자를 위해 만든 응답을 다른 사용자에게 재사용할 수 있다는 점이다.

- 한국어 사용자가 영어 페이지를 받음
- 압축을 기대하지 않는 클라이언트가 gzip body를 받음
- API client가 HTML fallback 페이지를 받음

이 문서는 그 차이를 설명하는 가장 기본적인 계약이 `content negotiation`과 `Vary`라는 점을 먼저 잡아 준다.

### Retrieval Anchors

- `Vary basics`
- `content negotiation basics`
- `response variant`
- `representation selection`
- `Accept-Language Vary`
- `Accept-Encoding Vary`
- `beginner vary primer`

---

## Content Negotiation은 무엇인가

content negotiation은 클라이언트와 서버가 "어떤 표현의 응답을 주고받을지" 맞추는 과정이다.

클라이언트는 보통 request header로 선호나 지원 범위를 알린다.

- `Accept`: 어떤 미디어 타입을 원하는가
- `Accept-Language`: 어떤 언어를 선호하는가
- `Accept-Encoding`: 어떤 압축을 풀 수 있는가

서버는 이 정보를 보고 representation 하나를 고른 뒤 response header와 body로 결과를 돌려준다.

```text
1. 클라이언트가 선호/지원 정보를 보낸다
2. 서버가 가능한 representation 중 하나를 선택한다
3. 서버가 body와 함께 선택 결과를 응답한다
4. cache가 있다면 어떤 request 헤더가 선택에 영향을 줬는지 알아야 한다
```

응답 쪽에서 자주 같이 보이는 헤더는 아래와 같다.

- `Content-Type`: 어떤 형식인지
- `Content-Language`: 어떤 언어인지
- `Content-Encoding`: 어떤 압축이 적용됐는지

핵심은 이 헤더들이 "선택 결과"를 보여 준다는 점이다.
반면 `Vary`는 "선택 근거가 된 request 헤더"를 보여 준다.

---

## Vary는 무엇을 알려주나

`Vary`는 서버가 응답 variant를 고를 때 참고한 **request header 이름 목록**이다.

예를 들어 서버가 언어와 압축을 보고 응답을 정했다면 이렇게 말할 수 있다.

```http
Vary: Accept-Language, Accept-Encoding
```

이 말의 뜻은 "같은 URL이라도 `Accept-Language`, `Accept-Encoding` 값이 다르면 다른 representation일 수 있으니 cache가 구분해서 저장하라"에 가깝다.

즉 `Vary`는:

- 클라이언트에게 새 요청 방법을 지시하는 헤더가 아니고
- cache에게 variant 경계를 알려 주는 헤더다

가장 단순한 감각으로 보면 역할이 이렇게 나뉜다.

- request header: 클라이언트의 선호/지원
- response body와 `Content-*`: 서버가 실제로 고른 표현
- `Vary`: 어떤 request header가 그 선택에 영향을 줬는지

---

## 언어 variant: `Accept-Language`

다국어 페이지를 예로 들면 직관적이다.

한국어를 선호하는 브라우저:

```http
GET /guide HTTP/1.1
Host: example.com
Accept-Language: ko-KR,ko;q=0.9,en;q=0.8
```

서버 응답:

```http
HTTP/1.1 200 OK
Content-Language: ko
Vary: Accept-Language
Content-Type: text/html; charset=UTF-8

<html>안내 페이지...</html>
```

영어를 선호하는 브라우저가 같은 URL을 요청하면 body는 달라질 수 있다.

```http
GET /guide HTTP/1.1
Host: example.com
Accept-Language: en-US,en;q=0.9
```

```http
HTTP/1.1 200 OK
Content-Language: en
Vary: Accept-Language
Content-Type: text/html; charset=UTF-8

<html>Guide page...</html>
```

여기서 `Vary: Accept-Language`가 없으면 shared cache는 첫 번째 한국어 응답을 영어 사용자에게도 그대로 재사용할 수 있다.

입문 단계에서는 아래 정도만 기억하면 충분하다.

- 언어가 바뀌면 body도 바뀐다
- body가 바뀌면 cache는 같은 응답으로 취급하면 안 된다
- 그 차이를 cache에 알려 주는 표지가 `Vary`다

실무에서는 raw `Accept-Language` 값이 너무 다양할 수 있어서 지원 언어 집합으로 정규화하는 경우가 많다. 그 운영 세부는 뒤의 고급 문서에서 다룬다.

---

## 압축 variant: `Accept-Encoding`

압축도 같은 원리다.

클라이언트가 brotli와 gzip을 풀 수 있다고 알리면:

```http
GET /app.js HTTP/1.1
Host: example.com
Accept-Encoding: br, gzip
```

서버나 CDN은 압축된 representation을 선택할 수 있다.

```http
HTTP/1.1 200 OK
Content-Encoding: br
Vary: Accept-Encoding
Content-Type: application/javascript
```

다른 클라이언트가 압축을 지원하지 않으면:

```http
GET /app.js HTTP/1.1
Host: example.com
Accept-Encoding: identity
```

```http
HTTP/1.1 200 OK
Vary: Accept-Encoding
Content-Type: application/javascript
```

두 응답은 같은 URL이지만 body bytes가 다르다.
그래서 cache는 두 representation을 따로 봐야 한다.

`Vary: Accept-Encoding`가 빠지면 생길 수 있는 직관적인 문제는 아래와 같다.

- 압축되지 않은 클라이언트가 압축 body를 받는다
- `Content-Encoding`와 body bytes가 어긋난다
- 일부 브라우저나 프록시에서만 응답이 깨져 보인다

이 주제의 운영형 함정은 이후 [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)과 [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)으로 이어진다.

---

## 다른 response variant는 어떻게 보나

언어와 압축 외에도 응답은 여러 축으로 달라질 수 있다.

| 어떤 request 정보가 바뀌나 | 무엇이 달라지나 | 보통 같이 보는 헤더/정책 |
|---|---|---|
| `Accept-Language` | 언어별 body | `Content-Language`, `Vary: Accept-Language` |
| `Accept-Encoding` | 압축 여부와 body bytes | `Content-Encoding`, `Vary: Accept-Encoding` |
| `Accept` | JSON / HTML / 다른 미디어 타입 | `Content-Type`, 필요 시 `Vary: Accept` |
| 정규화된 device/experiment header | 모바일/데스크톱 또는 실험 버전 | bounded custom header + `Vary` |
| cookie / auth / tenant | 사용자별 personalized body | 대개 `private` 또는 `no-store`, `Vary`만으로 해결하지 않음 |

여기서 중요한 구분이 하나 있다.

- **공유 가능한 몇 가지 variant** 라면 `Vary`로 구분하는 전략이 가능하다
- **사용자별 personalized 응답** 이라면 shared cache를 피하고 `private`/`no-store`를 먼저 검토해야 한다

즉 `Vary`는 "모든 다른 응답을 안전하게 캐시해 준다"가 아니라, **공유 가능한 representation 차원을 cache에 정확히 알려 주는 도구**다.

---

## `Cache-Control`, validator와는 어떻게 연결되나

세 헤더 그룹의 역할은 겹치지 않는다.

| 헤더/개념 | 질문 | 역할 |
|---|---|---|
| `Cache-Control` | 이 응답을 저장하거나 재사용해도 되는가 | freshness와 저장 정책 |
| `Vary` | 어떤 request 차원이 representation을 바꾸는가 | variant 분리 기준 |
| `ETag`, `Last-Modified`, `304` | 내가 가진 같은 representation이 아직 최신인가 | 재검증 기준 |

짧게 연결하면 이런 흐름이다.

```text
1. Cache-Control이 저장/재사용 정책을 정한다
2. Vary가 어떤 request 값별로 나눠 저장할지 정한다
3. ETag/Last-Modified가 같은 variant를 다시 확인하는 기준이 된다
```

그래서 `304 Not Modified`를 이해했다고 해서 variant 문제가 끝나는 것은 아니다.
애초에 잘못된 variant를 cache가 들고 있으면 재검증도 잘못된 representation을 기준으로 진행될 수 있다.

---

## 자주 헷갈리는 포인트

### `Vary`만 넣으면 personalized 응답도 안전한가요?

아니다.
사용자별 응답은 보통 shared cache에 태우지 않는 편이 안전하다.
`Vary: Cookie`처럼 너무 넓은 축은 hit rate를 거의 없애거나 운영을 더 불안하게 만들 수 있다.

### `Vary`는 브라우저보다 CDN에서만 중요하나요?

아니다.
shared cache에서 특히 중요하지만, cache가 있는 곳이라면 variant 경계를 이해해야 한다는 점은 같다.

### `Content-Language`나 `Content-Encoding`만 있으면 충분한가요?

부족하다.
그 헤더는 "무엇을 골랐는지"를 보여 줄 뿐이고, cache는 "무엇을 보고 골랐는지"도 알아야 한다.
그 역할이 `Vary`다.

### `Vary: User-Agent`를 바로 쓰면 되나요?

가능은 하지만 너무 넓은 경우가 많다.
실무에서는 가능한 capability 기반 또는 정규화된 custom header로 차원을 좁히는 편이 낫다.

---

## 면접에서 자주 나오는 질문

### Q. `Vary`는 왜 필요한가요?

- 같은 URL이라도 request header에 따라 다른 representation이 나올 수 있고, cache가 그 차이를 구분하게 해 주기 때문이다.

### Q. `Accept-Language`와 `Accept-Encoding`는 왜 자주 같이 언급되나요?

- 둘 다 content negotiation의 대표 입력이며, 응답 body를 실제로 바꾸는 대표적인 variant 축이기 때문이다.

### Q. `Cache-Control`과 `Vary`의 차이는 무엇인가요?

- `Cache-Control`은 저장/재사용 정책이고, `Vary`는 어떤 request 차원별로 representation을 나눠 저장해야 하는지 알려 주는 계약이다.

### Q. `Vary`가 있으면 항상 shared cache에 올려도 되나요?

- 아니다. 공유 가능한 소수의 variant에는 유효하지만, 사용자별 personalization은 `private`/`no-store`가 먼저다.

## 한 줄 정리

같은 URL이라도 언어, 압축, 표현 형식이 달라질 수 있다. `Vary`는 서버가 어떤 request 헤더를 보고 응답 variant를 골랐는지 cache에 알려 주는 표지판이다.
