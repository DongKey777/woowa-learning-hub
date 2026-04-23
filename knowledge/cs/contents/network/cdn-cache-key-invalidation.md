# CDN Cache Key와 Invalidation

> 한 줄 요약: CDN은 캐시를 빨리 쓰는 기술이 아니라, 캐시 키와 무효화 규칙을 얼마나 정확히 설계하느냐의 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cache-Control 실전](./cache-control-practical.md)
> - [HTTP의 무상태성과 쿠키, 세션, 캐시](./http-state-session-cache.md)
> - [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)
> - [System Design](../system-design/README.md)

retrieval-anchor-keywords: CDN cache key, invalidation, purge, vary, Accept-Language cache key, content negotiation key, cache busting, query string cache, edge cache, personalized response, surrogate key, cache segmentation

---

## 핵심 개념

CDN 캐시는 보통 다음 질문으로 결정된다.

- 어떤 응답을 저장할 것인가
- 어떤 키로 저장할 것인가
- 언제까지 유효한가
- 언제 무효화할 것인가

실무에서 캐시 사고는 대개 키 설계보다 무효화에서 터진다.  
같은 URL인데 사용자/언어/권한/압축 여부가 다르면 같은 캐시를 쓰면 안 된다.

### Retrieval Anchors

- `CDN cache key`
- `invalidation`
- `purge`
- `vary`
- `cache busting`
- `edge cache`
- `surrogate key`
- `cache segmentation`

---

## 깊이 들어가기

### 1. Cache Key는 무엇으로 구성되는가

기본적으로 키는 URL만이 아니다.

자주 고려하는 요소:

- path
- query string
- `Accept-Encoding`
- `Accept-Language`
- `Authorization` 유무
- cookie
- device type

키를 너무 넓게 잡으면 캐시 적중률이 떨어지고, 너무 좁게 잡으면 데이터가 섞인다.

### 2. Invalidation이 어려운 이유

CDN은 "오래된 것을 빨리 지우는" 시스템이 아니라, **분산된 복사본을 일관되게 갱신하는 문제**를 가진다.

대표 전략:

- TTL 만료를 기다린다
- purge API로 특정 URL을 제거한다
- versioned URL을 사용한다
- stale-while-revalidate를 쓴다

### 3. Purge의 함정

무작정 purge하면 다음 문제가 생긴다.

- 캐시 미스가 한꺼번에 몰린다
- origin 서버가 갑자기 때려 맞는다
- purge 전파 지연으로 일부 엣지에서 옛 값이 남는다

그래서 purge는 종종 "정확하지만 느린 삭제"다.

### 4. Versioned URL이 강한 이유

정적 자산에서는 파일명이 바뀌면 키도 바뀌게 만드는 방식이 실용적이다.

예:

- `app.js?v=123`
- `app.9f3a1c.js`

이 방식은 purge 부담을 줄이지만, 동적 응답에는 그대로 적용하기 어렵다.

---

## 실전 시나리오

### 시나리오 1: 잘못된 키로 로그인 사용자 응답이 섞임

`/profile`을 `public`처럼 캐시하면 다른 사용자의 프로필이 노출될 수 있다.  
문제는 캐시 서버가 아니라 **key와 header 설계**다.

### 시나리오 2: 배포 후 purge가 폭주

수백만 개의 URL을 purge하면 CDN과 origin이 동시에 흔들린다.  
이때는 versioned asset, TTL 분산, stale-while-revalidate가 더 현실적이다.

### 시나리오 3: 언어별 응답이 섞임

`Accept-Language`를 키에 넣지 않으면 한 언어 응답이 다른 언어 사용자에게 나갈 수 있다.

---

## 코드로 보기

### 캐시 키 정책 예시

```text
key = host + path + normalized_query + accept-encoding + accept-language
```

### 무효화 전략 예시

```bash
# 특정 경로 purge
curl -X POST https://cdn.example.com/purge \
  -H 'Authorization: Bearer ...' \
  -d '{"paths":["/assets/app.9f3a1c.js"]}'
```

### 설계 감각

```text
정적 자산 -> versioned URL + long TTL
개인화 응답 -> private/no-store
공개 API -> 짧은 TTL + ETag + revalidation
핫 콘텐츠 -> purge + stale-while-revalidate 혼합
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| TTL 기반 | 단순하다 | 오래된 데이터가 남는다 | 변경이 드문 콘텐츠 |
| purge 기반 | 정확하다 | 전파 지연과 폭주가 있다 | 즉시 정합성이 중요한 콘텐츠 |
| versioned URL | 운영이 편하다 | 동적 응답에 적용이 어렵다 | 정적 자산 |
| stale-while-revalidate | 빠르고 안정적이다 | 잠깐 옛 값을 허용한다 | 사용자 체감이 더 중요할 때 |

---

## 꼬리질문

> Q: 캐시 키에 cookie를 넣으면 왜 적중률이 떨어지는가?
> 의도: 키 설계가 캐시 효율을 좌우한다는 점을 이해하는지 확인
> 핵심: 사용자별로 키가 갈라져 같은 응답도 재사용이 안 된다

> Q: purge와 TTL 중 무엇이 더 낫나?
> 의도: 운영 절차 관점의 판단 능력 확인
> 핵심: 즉시 정합성, 트래픽, 전파 지연을 함께 봐야 한다

## 한 줄 정리

CDN 캐시는 저장보다도 키 설계와 무효화 전략이 핵심이며, 잘못 잡으면 성능보다 장애를 먼저 만든다.
