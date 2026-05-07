---
schema_version: 3
title: "CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기"
concept_id: network/cdn-vendor-header-crosswalk-cloudfront-cloudflare-mini-card
canonical: true
category: network
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- cdn-vendor-header-crosswalk
- cloudfront-cloudflare-devtools
- edge-ownership-first-pass
aliases:
- cloudfront header clue
- cloudflare header clue
- cdn vendor header crosswalk
- cf-cache-status
- cf-ray
- x-cache cloudfront
symptoms:
- Server CloudFront나 CF-Ray가 보이면 CDN이 최종 원인이라고 단정한다
- CF-Cache-Status HIT와 DYNAMIC을 owner 확정표처럼 읽는다
- X-Cache Miss를 origin app이 직접 에러를 만들었다는 뜻으로 확정한다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- network/browser-devtools-gateway-error-header-clue-card
- network/browser-devtools-x-cache-age-ownership-1minute-card
next_docs:
- network/cdn-error-html-vs-app-json-decision-card
- network/cdn-cache-key-invalidation
- system-design/cdn-basics
linked_paths:
- contents/network/browser-devtools-gateway-error-header-clue-card.md
- contents/network/browser-devtools-x-cache-age-ownership-1minute-card.md
- contents/network/browser-devtools-response-body-ownership-checklist.md
- contents/network/cdn-cache-key-invalidation.md
- contents/system-design/cdn-basics.md
confusable_with:
- network/browser-devtools-x-cache-age-ownership-1minute-card
- network/cdn-error-html-vs-app-json-decision-card
- network/browser-devtools-gateway-error-header-clue-card
- system-design/cdn-basics
forbidden_neighbors: []
expected_queries:
- "CloudFront Cloudflare 헤더를 DevTools에서 처음 볼 때 어떻게 번역해?"
- "CF-Ray가 있으면 Cloudflare가 직접 에러를 만든 증거야?"
- "X-Cache Hit from cloudfront와 Miss from cloudfront를 app owner와 어떻게 분리해?"
- "CF-Cache-Status HIT DYNAMIC MISS를 초급 기준으로 설명해줘"
- "CDN vendor header는 범인 확정이 아니라 edge 문맥을 여는 단서라는 점을 설명해줘"
contextual_chunk_prefix: |
  이 문서는 Server: CloudFront/cloudflare, X-Cache, CF-Cache-Status,
  CF-Ray, Via 같은 CDN vendor header를 app direct response, CDN pass-through,
  edge cached response, edge generated error 후보로 번역하는 beginner primer다.
---
# CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기

> 한 줄 요약: `Server: CloudFront`, `CF-Cache-Status`, `CF-Ray`, `X-Cache` 같은 헤더는 "누가 최종 범인인가"를 확정하는 증거라기보다, 초급자가 응답 소유를 `app 직답` 대신 `edge/CDN 경유 또는 edge 응답 후보`로 안전하게 번역하게 돕는 명찰이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)
- [CDN 기초 (CDN Basics)](../system-design/cdn-basics.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: cloudfront header clue, cloudflare header clue, cf-cache-status 뭐예요, cf-ray 뭐예요, x-cache cloudfront 뜻, server cloudfront 뭐예요, cdn response ownership beginner, edge header first pass, via varnish what is, 처음 cdn 헤더, cdn vendor header crosswalk, browser devtools cdn clue, app 응답인지 cdn 응답인지, beginner cloudfront cloudflare

## 핵심 개념

처음에는 vendor 헤더를 보고 "범인이 CloudFront다"처럼 단정하지 말고, **응답 소유 후보를 더 안전한 한국어로 바꾸는 작업**만 하면 된다.

- app 직답 후보: app이 만든 JSON/HTML이 거의 그대로 보이는 장면
- edge/CDN 경유 후보: CDN이 앞단에 있다는 흔적은 보이지만, app 응답을 그냥 전달했을 수도 있는 장면
- edge/CDN 응답 후보: CDN이나 WAF가 바깥에서 직접 거절하거나 캐시된 응답을 준 장면

즉 vendor 헤더는 "누가 말했는지 100% 확정"이 아니라, "어디부터 읽으면 덜 틀리나"를 정하는 첫 힌트다.

## 한눈에 보기

| DevTools 헤더 단서 | 초급자용 안전한 번역 | 아직 확정하면 안 되는 것 | 다음 질문 |
|---|---|---|---|
| `Server: CloudFront` | CloudFront 같은 CDN 앞단이 보인다 | app이 절대 안 만들었다 | body가 app JSON인가, 짧은 edge 에러 HTML인가 |
| `X-Cache: Hit from cloudfront` | CloudFront cache에서 응답했을 가능성이 크다 | 원본 app이 이번 요청을 처리했다 | 지금 본 body가 캐시 재사용인지, app 실시간 계산인지 |
| `X-Cache: Miss from cloudfront` | CloudFront를 거쳤지만 이번엔 origin 쪽 확인이 있었을 수 있다 | 무조건 app 문제다 | status와 body owner가 app인지 gateway인지 |
| `CF-Cache-Status: HIT` | Cloudflare edge cache 재사용 후보다 | origin app이 이번에 직접 계산했다 | `Age`, body 타입, cache 대상 리소스인가 |
| `CF-Cache-Status: DYNAMIC` | Cloudflare를 거쳤지만 cache 재사용 장면은 아닐 수 있다 | Cloudflare가 직접 에러를 만들었다 | app JSON인지 edge 거절인지 다른 헤더와 body를 같이 보기 |
| `CF-Ray` | Cloudflare 경유 요청 추적 단서다 | 이 헤더 하나로 owner 확정 | `Server`, status, body preview도 같이 보기 |
| `Via: 1.1 varnish` | 중간 cache/proxy hop이 있었다 | varnish가 최종 owner다 | app 응답 전달인지 intermediary 응답인지 |

짧게 외우면 이렇게 보면 된다.

```text
vendor 헤더 보임 -> CDN/edge 문맥 먼저 열기
cache hit 표기 -> origin 직답보다 edge 재사용 후보 먼저
vendor 추적 id만 보임 -> 경유 흔적일 뿐 owner 확정 아님
```

## 헤더별 crosswalk

### `Server: CloudFront` / `Server: cloudflare`

이 값은 "응답 체인 앞단에 CDN vendor가 눈에 띈다"는 뜻으로 읽으면 충분하다.

초급자 첫 문장은 이 정도면 안전하다.

- "`app 서버 이름`보다 `edge/CDN 앞단 이름`이 먼저 보인다"
- "그래서 app 직답인지, edge가 대신 응답했는지 둘 다 열어 둔다"

특히 `403`, `429`, `502`, `503`, `504`와 같이 보이면 app business error보다 edge/gateway 문맥을 먼저 연다.

### `X-Cache: Hit from cloudfront` / `Miss from cloudfront`

CloudFront에서 많이 보는 초급 단서다.

- `Hit from cloudfront`: 이번 body가 edge cache에서 바로 나왔을 가능성이 크다
- `Miss from cloudfront`: CloudFront를 거쳤지만 origin 확인이나 fetch가 있었을 가능성이 크다

안전한 번역은 "`CloudFront가 앞에 있었다 + cache 재사용 여부 단서가 있다`" 정도다.

이 헤더만으로 하면 안 되는 오해:

- `Hit`라고 해서 무조건 app이 건강하다고 단정
- `Miss`라고 해서 무조건 app이 직접 에러를 만들었다고 단정

### `CF-Cache-Status` / `CF-Ray`

Cloudflare에서 초급자가 자주 보는 두 단서다.

- `CF-Cache-Status: HIT`: edge cache 재사용 후보
- `CF-Cache-Status: MISS`: origin 쪽 확인이 있었을 수 있는 후보
- `CF-Cache-Status: DYNAMIC`: cache된 정적 응답보다 동적 전달 문맥 후보
- `CF-Ray`: Cloudflare를 지난 요청을 다시 찾는 추적 단서

안전한 첫 문장은 이렇게 잡으면 된다.

- "`CF-Cache-Status`는 cache 재사용 힌트다"
- "`CF-Ray`는 Cloudflare 경유 추적 힌트다"
- "둘 다 owner 확정표가 아니라 edge 문맥을 여는 표지판이다"

## 흔한 오해와 함정

- `Server: CloudFront`를 보고 "app은 전혀 안 탔다"고 단정한다. CDN이 app 응답을 전달하면서 자기 이름을 보일 수도 있다.
- `CF-Ray`가 있으면 Cloudflare가 직접 에러를 만들었다고 생각한다. 이 값은 경유 추적 ID에 가깝다.
- `X-Cache: Hit from cloudfront`를 보고 "원본은 완전히 무관하다"고 말한다. 이번 요청 처리는 cache hit일 수 있어도, 원본 정책과 이전 응답이 기반일 수 있다.
- `CF-Cache-Status: DYNAMIC`을 "에러"로 읽는다. 이 값은 보통 cache 재사용이 아닌 동적 전달 문맥 힌트다.
- vendor 헤더만 보고 app 로그를 아예 안 찾는다. `X-Request-Id`, app 공통 JSON 형식, 최종 URL 같은 다른 단서도 같이 봐야 한다.

## 실무에서 쓰는 모습

### 예시 1. CloudFront cache 흔적

```http
HTTP/1.1 200 OK
Server: CloudFront
X-Cache: Hit from cloudfront
Age: 120
Content-Type: text/css
```

초급자 첫 메모는 이 정도면 충분하다.

- "CloudFront 앞단에서 cache 재사용된 정적 응답 후보"
- "이번 요청에서 origin app 실시간 처리 증거는 약하다"

### 예시 2. Cloudflare 경유지만 owner는 더 봐야 하는 장면

```http
HTTP/2 502
Server: cloudflare
CF-Ray: 8f3c...
CF-Cache-Status: DYNAMIC
Content-Type: text/html
```

이 장면의 초급자 첫 메모:

- "Cloudflare 경유 흔적은 강하다"
- "하지만 `CF-Ray`만으로 Cloudflare 직접 에러라고 확정하지 않는다"
- "`502`와 body preview를 같이 보고 edge 기본 페이지인지, upstream/gateway 번역인지 더 본다"

### 초급자 incident 메모 템플릿

| 보인 단서 | 메모 문장 |
|---|---|
| `Server: CloudFront` | "CloudFront 앞단 문맥이 보임" |
| `X-Cache: Hit from cloudfront` | "edge cache 재사용 후보" |
| `CF-Cache-Status: DYNAMIC` | "Cloudflare 경유지만 cache hit 장면은 아닐 수 있음" |
| `CF-Ray` | "Cloudflare 추적 단서 있음, owner 확정은 보류" |

## 더 깊이 가려면

- vendor 헤더보다 먼저 보는 3개 헤더 기준이 필요하면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- `X-Cache`, `Age`, `CF-Cache-Status`를 vendor 이름보다 먼저 읽는 초급 첫 pass 카드가 필요하면 [Browser DevTools `X-Cache` / `Age` 1분 헤더 카드](./browser-devtools-x-cache-age-ownership-1minute-card.md)
- body가 app JSON인지, CDN/gateway HTML인지 같이 가르려면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- CDN cache hit/miss와 invalidation 기초를 더 보려면 [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)
- CDN이 애초에 어떤 역할인지부터 다시 잡으려면 [CDN 기초 (CDN Basics)](../system-design/cdn-basics.md)

## 한 줄 정리

CloudFront와 Cloudflare 헤더는 "누가 최종 owner인가"를 바로 확정하는 판결문이 아니라, 초급자가 응답을 `app 직답`보다 `edge/CDN 경유 또는 edge 응답 후보`로 안전하게 번역하게 해 주는 첫 단서다.
