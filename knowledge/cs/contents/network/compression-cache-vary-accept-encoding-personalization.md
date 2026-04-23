# Compression, Cache, Vary, Accept-Encoding, Personalization

> 한 줄 요약: 압축과 캐시는 따로 튜닝하는 기능이 아니다. `Accept-Encoding`, personalization, CDN key, `Vary`를 제대로 맞추지 않으면 gzip/br 효율보다 잘못된 캐시 혼합이 더 큰 장애를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
> - [Cache-Control 실전](./cache-control-practical.md)
> - [CDN Cache Key와 Invalidation](./cdn-cache-key-invalidation.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

retrieval-anchor-keywords: Vary, Accept-Encoding, Accept-Language vary, content negotiation cache, response variant cache, compression cache, personalized cache, content-encoding, gzip cache key, brotli cache, shared cache safety, CDN vary, cache poisoning by variant mix

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

같은 URL이라도 응답 variant가 달라질 수 있다.

- gzip vs br vs uncompressed
- language variant
- authenticated vs anonymous
- mobile vs desktop

이때 shared cache가 어떤 차원을 키로 볼지 알려 주는 핵심 도구가 `Vary`다.

### Retrieval Anchors

- `Vary`
- `Accept-Encoding`
- `compression cache`
- `personalized cache`
- `content-encoding`
- `gzip cache key`
- `brotli cache`
- `CDN vary`

## 깊이 들어가기

### 1. 압축은 content variant를 늘린다

압축을 켜면 응답은 더 이상 하나가 아니다.

- same URL
- different `Content-Encoding`
- different body bytes

shared cache가 이 차이를 모르고 한 variant를 다른 client에 주면:

- 압축 안 되는 client에 gzip body 전달
- 잘못된 ETag/length mismatch
- hit rate는 높아 보여도 correctness가 망가짐

### 2. `Vary: Accept-Encoding`는 보통 필수다

공유 캐시가 응답 variant를 구분하려면 최소한:

```http
Vary: Accept-Encoding
```

가 필요하다.

하지만 여기서 끝이 아니다.

- personalization이 있으면 cookie/auth도 문제
- language/content negotiation이 있으면 `Accept-Language`도 문제
- CDN이 header normalization을 따로 할 수도 있다

### 3. personalization과 compression이 섞이면 더 위험하다

로그인/권한별 응답인데:

- `public` 캐시
- weak key
- `Vary` 누락

이면 variant 혼합이 일어난다.

즉 compression 문제처럼 보여도 실제론 **personalization leak**가 더 큰 사고일 수 있다.

### 4. proxy/CDN가 app과 다른 위치에서 압축할 수도 있다

가능한 패턴:

- app은 uncompressed origin response 반환
- CDN/edge가 `Accept-Encoding` 보고 압축
- cache key는 edge 정책이 결정

이 경우 app는 정상이라도 edge에서 variant mix가 날 수 있다.  
그래서 cache correctness는 app header와 CDN policy를 같이 봐야 한다.

### 5. `Vary`를 너무 넓히면 hit rate가 무너진다

`Vary`는 correctness를 지키지만 과하면 조각난다.

- `User-Agent`
- large Cookie set
- noisy custom header

를 그대로 key 차원에 넣으면 shared cache 효과가 사실상 사라질 수 있다.

핵심은 필요한 variant만 남기고 정규화하는 것이다.

### 6. observability는 variant correctness와 hit rate를 같이 봐야 한다

중요한 지표:

- cache hit ratio
- variant count per URL
- `Content-Encoding` 분포
- anonymous vs personalized cache separation
- cache correctness incidents

hit rate만 보면 variant leakage는 숨어 버린다.

## 실전 시나리오

### 시나리오 1: 어떤 브라우저에서만 응답이 깨져 보인다

`Accept-Encoding` variant mix나 edge compression policy mismatch일 수 있다.

### 시나리오 2: 로그인 사용자 응답이 드물게 다른 사람 것처럼 보인다

compression 문제처럼 보여도 실제론 personalization과 cache key 설계 문제일 수 있다.

### 시나리오 3: brotli를 켰더니 CDN hit rate가 갑자기 떨어졌다

variant 수가 늘었거나 `Vary` 차원이 과하게 넓어졌을 수 있다.

### 시나리오 4: app은 `no-cache`라고 했는데 edge는 여전히 변형된 응답을 재사용한다

CDN policy, surrogate cache key, revalidation 설정이 따로 적용되고 있을 수 있다.

## 코드로 보기

### 헤더 감각

```http
Cache-Control: public, max-age=60
Vary: Accept-Encoding
Content-Encoding: br
```

### 관찰 포인트

```text
- Vary dimensions
- content-encoding distribution
- shared cache hit ratio by variant
- personalized response accidentally cached?
- app header vs CDN key policy aligned?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| narrow cache key | hit rate가 좋다 | variant mix 위험이 있다 | 단순 공개 콘텐츠 |
| explicit Vary | correctness가 좋다 | variant 수가 늘 수 있다 | 다중 encoding/language |
| edge-only compression | origin 단순화 | edge key/policy 복잡도가 커진다 | CDN 중심 서비스 |
| per-user no-store | 안전하다 | shared cache 이점을 잃는다 | 민감한 personalization |

핵심은 압축과 캐시를 따로 튜닝하지 않고 **variant correctness 문제**로 함께 보는 것이다.

## 꼬리질문

> Q: 왜 `Vary: Accept-Encoding`가 중요한가요?
> 핵심: gzip/br/uncompressed variant를 shared cache가 구분하게 해 주기 때문이다.

> Q: 압축과 personalization이 같이 있으면 왜 더 위험한가요?
> 핵심: variant mix가 단순 encoding mismatch를 넘어 다른 사용자 데이터 노출로 이어질 수 있기 때문이다.

> Q: `Vary`를 많이 넣으면 항상 안전한가요?
> 핵심: correctness는 좋아지지만 hit rate가 크게 떨어질 수 있어 필요한 차원만 써야 한다.

## 한 줄 정리

compression과 cache는 `Accept-Encoding`과 `Vary`로 연결된 하나의 variant 문제라서, correctness와 hit rate를 함께 보며 키를 설계해야 한다.
