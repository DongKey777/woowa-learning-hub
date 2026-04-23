# Strong vs Weak ETag: validator 정밀도와 cache correctness

> 한 줄 요약: weak ETag는 "틀린 ETag"가 아니라 비교 강도가 낮은 validator다. `GET`/`HEAD` 재검증에는 쓸 수 있지만, `If-Match`, `If-Range`, compressed variant처럼 byte identity가 필요한 경계에서는 strong semantics가 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
> - [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
> - [Cache-Control 실전](./cache-control-practical.md)
> - [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
> - [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)
> - [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)

retrieval-anchor-keywords: strong ETag, weak ETag, validator precision, strong validator, weak validator, ETag comparison, weak comparison, strong comparison, If-None-Match weak comparison, If-Match strong comparison, If-Range strong validator, range request validator, compressed variant ETag, gzip identity ETag, cache correctness validator, weak Last-Modified, entity-tag semantics

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [Strong vs Weak ETag를 먼저 구분하기](#strong-vs-weak-etag를-먼저-구분하기)
- [validator 정밀도는 왜 중요한가](#validator-정밀도는-왜-중요한가)
- [어떤 조건부 요청이 어떤 비교를 쓰나](#어떤-조건부-요청이-어떤-비교를-쓰나)
- [weak ETag가 괜찮은 경우](#weak-etag가-괜찮은-경우)
- [cache correctness가 실제로 깨지는 경우](#cache-correctness가-실제로-깨지는-경우)
- [compressed variant와 shared ETag가 왜 위험한가](#compressed-variant와-shared-etag가-왜-위험한가)
- [실전 판단 체크리스트](#실전-판단-체크리스트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 문서가 필요한가

입문 단계에서는 `ETag`를 그냥 "버전 문자열"로 외우기 쉽다.

하지만 실무에서는 다음 차이가 중요하다.

- 이 validator가 byte-level로 정확한가
- 아니면 "대충 같은 것으로 취급해도 된다"는 약한 동등성인가
- 이 validator를 cache revalidation에 쓰는가
- 아니면 write 보호나 range resume에도 쓰는가

즉 같은 `ETag`라도 **어떤 정밀도로 무엇을 보호하려는지**가 다르면 의미가 달라진다.

### Retrieval Anchors

- `strong ETag`
- `weak ETag`
- `validator precision`
- `weak comparison`
- `strong comparison`
- `If-None-Match weak comparison`
- `If-Match strong comparison`
- `If-Range strong validator`
- `compressed variant ETag`
- `cache correctness validator`

---

## Strong vs Weak ETag를 먼저 구분하기

형식 차이는 단순하다.

- strong ETag: `ETag: "article-42-v18"`
- weak ETag: `ETag: W/"article-42-v18"`

핵심 차이는 prefix가 아니라 **무엇을 같은 것으로 보겠다고 약속하느냐**다.

### strong ETag

- representation data가 바뀌면 바뀌어야 한다
- byte identity가 필요한 연산에 쓸 수 있다
- partial response, lost update 방지, cache update 충돌에 더 안전하다

### weak ETag

- representation data가 조금 달라도 같은 것으로 묶을 수 있다
- 서버가 "이 정도 차이는 같은 버전으로 봐도 된다"고 선언한 셈이다
- full-response revalidation에는 유용하지만 byte-sensitive 연산에는 부적합할 수 있다

비교 방식 차이도 중요하다.

| 비교 | `"abc"` vs `"abc"` | `W/"abc"` vs `"abc"` | `W/"abc"` vs `W/"abc"` |
|---|---|---|---|
| strong comparison | match | no match | no match |
| weak comparison | match | match | match |

즉 **weak ETag는 weak comparison에서는 맞을 수 있지만, strong comparison에서는 절대 strong match가 되지 않는다.**

---

## validator 정밀도는 왜 중요한가

validator의 정밀도는 "서로 다른 representation을 얼마나 잘 구분하느냐"다.

정밀도가 낮으면 cache hit는 잘 나올 수 있다.
대신 아래 두 문제가 생긴다.

- 실제로는 다른 응답을 같은 것으로 재사용한다
- partial/range/update 같은 정밀한 연산에 잘못된 전제를 공급한다

### `Last-Modified`가 약한 validator가 될 수 있는 이유

`Last-Modified`는 시간 기반이라 이해는 쉽지만 보통 초 단위 해상도에 묶인다.

즉 같은 1초 안에 리소스가 두 번 바뀌면:

- 클라이언트는 둘을 구분하지 못할 수 있고
- `If-Modified-Since`는 실제 변경을 놓칠 수 있다

그래서 `Last-Modified`는 흔히 **약한 validator**로 취급된다.

### 같은 ETag를 여러 representation에 공유하면 왜 약한가

예를 들어 같은 URL에 대해 동시에:

- identity body
- gzip body
- brotli body

를 제공하는데 모두 같은 `ETag`를 쓰면, 그 validator는 정밀하지 않다.

왜냐하면 content coding이 다르면 representation data 자체가 다르기 때문이다.

따라서:

- `Vary`로 variant key를 나눴더라도
- validator가 representation을 충분히 구분하지 못하면
- `304`, cache update, range resume 해석이 흐려질 수 있다

중요한 포인트는 이것이다.

- weak validator는 "잘못된 구현"이 아니라 "낮은 정밀도"
- 문제는 그 낮은 정밀도가 **현재 연산의 correctness 요구와 맞느냐**다

---

## 어떤 조건부 요청이 어떤 비교를 쓰나

`ETag` 의미는 헤더마다 다르게 소비된다.

| 상황 | 주로 쓰는 헤더 | 비교 방식 | weak ETag로 충분한가 | 이유 |
|---|---|---|---|---|
| cached `GET`/`HEAD` 재검증 | `If-None-Match` | weak comparison | 대체로 yes | 서버가 "기존 full representation 계속 써도 된다"를 판단하면 되기 때문 |
| write 전 충돌 방지 | `If-Match` | strong comparison | no | 작은 변경도 놓치면 lost update가 생길 수 있기 때문 |
| resume download / partial fetch | `Range` + `If-Range` | strong comparison | no | byte range는 정확히 같은 representation 위에서만 안전하기 때문 |
| date 기반 재검증 | `If-Modified-Since` | 시간 비교 | 제한적 | 시계 해상도와 clock skew 때문에 정밀도가 낮기 때문 |

실무 감각으로 줄이면:

- `If-None-Match`는 "내 사본을 계속 써도 되나?"
- `If-Match`는 "아무도 안 바꿨을 때만 수정해라"
- `If-Range`는 "이 byte 이어받기가 정확히 같은 파일일 때만 허용해라"

여기서 마지막 두 질문은 weak semantics로는 부족하다.

---

## weak ETag가 괜찮은 경우

weak ETag는 아래 같은 상황에서 유용할 수 있다.

### 1. full-response revalidation만 필요한 동적 문서

예:

- 뉴스 메인
- 날씨 요약
- 집계 dashboard

처럼 자주 바뀌지만, 매 변경마다 byte-exact invalidation이 꼭 필요하지 않은 경우다.

서버는 여러 근접 상태를 하나의 약한 버전으로 묶어:

- revalidation 비용을 줄이고
- 불필요한 `200` body 재전송을 줄일 수 있다

### 2. 미세한 표현 차이를 동일하게 보아도 되는 경우

예:

- whitespace만 바뀐 HTML
- 광고 slot 순서처럼 서버가 동등하다고 보는 변화
- 내부 timestamp는 달라도 사용자 의미가 같다고 보는 snapshot

다만 이 판단은 서버가 책임져야 한다.
사용자에게 실제로 다른 의미를 주는 응답을 weak ETag로 묶으면 안 된다.

### 3. expensive render 결과를 의미 단위로 묶고 싶은 경우

매 요청마다 비싼 렌더링을 수행하는 resource에서:

- 아주 작은 내부 변화마다 strong tag를 바꾸면
- cache revalidation 효율이 나빠질 수 있다

이때 weak ETag는 "semantic snapshot id"처럼 쓸 수 있다.

단, 이것이 허용되는 전제는 **resume, partial update, optimistic locking 용도로 쓰지 않는다는 점**이다.

---

## cache correctness가 실제로 깨지는 경우

weak ETag가 문제를 만드는 대표 상황은 아래다.

### 1. `If-Match`로 write 충돌을 막으려는 경우

`PUT`, `PATCH`, `DELETE` 전에:

```http
If-Match: "article-42-v18"
```

처럼 "정확히 이 버전일 때만 수정"하고 싶다면 strong semantics가 필요하다.

weak validator로는:

- 중간 변경을 놓칠 수 있고
- lost update 방지가 무너진다

즉 write concurrency control에서는 weak ETag가 아니라 **strong validator**가 기준이어야 한다.

### 2. `Range` resume가 있는 다운로드

대용량 파일 다운로드는 흔히 중간부터 이어받는다.

이때 byte range는 **정확히 같은 representation** 위에서만 의미가 있다.

예를 들어 이전에 받은 첫 1MB가 old representation인데, 이어받은 뒷부분이 new representation이면:

- 파일이 조용히 섞이고
- checksum mismatch나 media corruption으로 이어질 수 있다

그래서 `If-Range`는 strong validator 경계를 요구한다.
weak ETag는 여기서 안전한 기준이 아니다.

### 3. representation이 자주 바뀌는데 validator는 초 단위로만 바뀌는 경우

예:

- 1초 안에 두 번 발행되는 API snapshot
- 높은 write rate를 가진 HTML/JSON 문서

이런 resource에서 `Last-Modified`만 믿으면 재검증 precision이 부족할 수 있다.

겉으로는 "304가 잘 나온다"처럼 보일 수 있지만, 실제로는 최신 body 교체를 놓친다.

### 4. per-user 또는 nonce-bearing body를 약하게 묶는 경우

응답 안에:

- 사용자별 이름
- 권한별 버튼
- CSRF token
- 1회성 signed URL

같은 값이 들어 있으면 weak grouping은 위험하다.

이 경우 weak ETag는 단순 성능 튜닝이 아니라 correctness 또는 security 문제를 만들 수 있다.

즉 weak validator는 "조금 stale해도 되는 공개 리소스"에 가까울수록 안전하다.
"정확히 그 bytes여야 하는 응답"에 가까울수록 위험해진다.

---

## compressed variant와 shared ETag가 왜 위험한가

이 부분이 cache correctness에서 가장 자주 헷갈린다.

같은 `/app.js`라도:

- identity bytes
- gzip bytes
- br bytes

는 서로 다른 representation이다.

따라서 strong validator를 쓸 거라면 보통 variant별로 달라야 한다.

```http
HTTP/1.1 200 OK
Content-Encoding: gzip
Vary: Accept-Encoding
ETag: "app-js-v18-gzip"
```

```http
HTTP/1.1 200 OK
Vary: Accept-Encoding
ETag: "app-js-v18-identity"
```

반대로 아래처럼 같은 `ETag`를 공유하면:

```http
ETag: "app-js-v18"
```

문제가 생길 수 있다.

- `Vary`는 맞지만 validator가 variant를 충분히 못 가른다
- `304` 재검증 뒤에 cache가 이전 encoding body를 재사용한다
- range request가 encoded sequence 기준인지 identity 기준인지 헷갈린다
- CDN/origin이 서로 다른 representation을 같은 object처럼 다룬다

즉 `Vary`는 cache key 문제를 풀고, `ETag`는 revalidation precision 문제를 푼다.
둘 중 하나만 맞아도 충분하지 않다.

이 케이스는 [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)과 [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)에서 운영형 증상으로 이어진다.

---

## 실전 판단 체크리스트

아래 질문에 `yes`가 많을수록 strong validator 쪽으로 기울어야 한다.

1. 이 응답을 `Range`/resume download에 쓸 수 있는가
2. 이 resource를 `If-Match`로 보호하고 싶은가
3. gzip/br/identity 같은 multiple representation이 동시에 존재하는가
4. 1초 안에 여러 번 바뀔 수 있는가
5. body 안에 personalization, nonce, token, signed URL이 들어가는가
6. CDN, proxy, browser cache가 모두 이 응답을 재검증하는가

반대로 아래 조건이면 weak ETag를 고려할 여지가 있다.

- `GET`/`HEAD` full-body 재검증만 한다
- 약간의 표현 차이를 서버가 같은 것으로 봐도 된다
- public content이고 사용자별 민감 데이터가 없다
- partial/range/write precondition과 섞이지 않는다

한 줄 규칙으로 줄이면:

- **semantic reuse가 목적이면 weak**
- **byte correctness가 목적이면 strong**

---

## 면접에서 자주 나오는 질문

### Q. weak ETag는 언제 써도 되나요?

- `GET`/`HEAD` 재검증처럼 full representation reuse 여부만 판단하면 되는 경우에 적합하다.

### Q. weak ETag와 `If-Match`를 같이 써도 되나요?

- 부적합하다. `If-Match`는 strong comparison을 전제로 lost update를 막는 용도라서 weak validator로는 보호 수준이 부족하다.

### Q. `Last-Modified`도 validator인데 왜 부족할 수 있나요?

- 보통 시간 해상도가 낮아서, 짧은 간격의 연속 변경이나 clock skew를 정확히 구분하지 못할 수 있기 때문이다.

### Q. `Vary: Accept-Encoding`만 있으면 gzip/identity correctness가 해결되나요?

- 아니다. `Vary`는 cache key를 나누는 계약이고, `ETag`는 revalidation precision을 정하는 계약이라서 compressed variant마다 validator semantics도 함께 맞아야 한다.
