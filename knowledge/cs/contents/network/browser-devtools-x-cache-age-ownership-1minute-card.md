# Browser DevTools `X-Cache` / `Age` 1분 헤더 카드

> 한 줄 요약: DevTools 응답 헤더에서 `X-Cache`, `Age`, `CF-Cache-Status` 같은 cache 단서가 보이면 초급자는 먼저 "이번 body가 app 실시간 계산보다 CDN/cache 재사용 후보인가"를 읽고, app ownership 확정은 잠시 보류하는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- [CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기](./cdn-vendor-header-crosswalk-cloudfront-cloudflare-mini-card.md)
- [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [network 카테고리 인덱스](./README.md)
- [CDN 기초 (CDN Basics)](../system-design/cdn-basics.md)

retrieval-anchor-keywords: x-cache age header, x-cache 뭐예요, age header 뭐예요, cf-cache-status hit meaning, devtools cache ownership first pass, cdn cache ownership beginner, app ownership vs edge cache, cache hit header beginner, why x-cache hit but app not called, age header first check, 처음 devtools cache header, cache header 보고 누가 응답했나, what is x-cache, what is age header, cache ownership 헷갈려요

## 핵심 개념

`X-Cache`, `Age`, `CF-Cache-Status`는 보통 "cache를 거쳤다"는 단서다.  
초급자 first pass에서는 이걸 보고 바로 "`app이 응답했다`"보다 "`edge/CDN cache가 이번 body를 재사용했을 수도 있다`"로 번역하면 덜 틀린다.

한 줄 멘탈 모델:

```text
X-Cache / Age 보임 -> app 실시간 계산 확정이 아니라 edge cache 재사용 후보 먼저
```

중요한 점은 이것이다.

- 이 헤더들은 **cache ownership 단서**다
- 이 헤더들만으로 **최종 원인**을 확정하진 않는다
- 하지만 첫 DevTools pass에서는 "`이번 응답을 app가 바로 만든 건가?`"를 잠시 보류하게 도와준다

## 한눈에 보기

| DevTools에서 먼저 보인 단서 | 초급자용 안전한 번역 | 아직 확정하면 안 되는 것 | 바로 다음 질문 |
|---|---|---|---|
| `X-Cache: Hit ...` | edge/CDN cache 재사용 후보 | app이 이번 요청을 실시간 처리했다 | body가 정적 파일인지, cached API 응답인지 |
| `Age: 120` 같은 값 | 이 응답이 cache에 머문 시간이 보인다 | app이 방금 계산한 fresh 응답이다 | cache 대상 리소스인가, 다른 vendor header도 있나 |
| `CF-Cache-Status: HIT` | Cloudflare edge cache 재사용 후보 | origin app이 이번에 직접 만들었다 | `Server`, `CF-Ray`, body 타입이 무엇인가 |
| `X-Cache: Miss ...` | cache 계층을 거쳤지만 origin 확인이 있었을 수 있다 | 무조건 app owner다 | status, body owner, 다른 gateway/CDN 단서가 있나 |
| `Age`가 없고 cache hit 표기도 약하다 | cache ownership 단서가 약하다 | cache를 안 썼다 | `Server`/`Via`/`Content-Type`으로 다른 owner를 본다 |

짧게 외우면 이렇다.

```text
cache hit 표기 -> edge cache 후보 먼저
age 값 -> 이전에 저장된 응답 후보 먼저
miss 표기 -> cache 계층은 있었지만 owner는 더 봐야 함
```

## 왜 첫 pass에서 app ownership을 보류하나

초급자가 자주 하는 실수는 "`200 OK`니까 app이 잘 준 거다`" 또는 "`X-Cache`가 있어도 body는 app 응답이다`"처럼 너무 빨리 app ownership으로 붙이는 것이다.

하지만 cache 관련 헤더가 강하면 질문 순서가 바뀐다.

1. 이 body가 **이번 요청에서 app가 새로 계산한 것인가**
2. 아니면 **edge/CDN/cache가 기존 사본을 재사용한 것인가**

예를 들어 아래처럼 보인다면:

```http
HTTP/1.1 200 OK
X-Cache: Hit from cloudfront
Age: 120
Content-Type: text/css
```

초급자 메모는 이 정도면 충분하다.

- "app 실시간 계산보다 edge cache 재사용 후보"
- "이번 row만으로 app code path를 바로 파지 않는다"

즉 이 헤더들은 "app이 틀렸다"보다 "이번 body owner를 cache 쪽으로 먼저 기울게 하는 명찰"에 가깝다.

## 30초 분리표: 언제 cache ownership 후보로 읽나

| 장면 | first pass에서 붙일 라벨 | 이유 |
|---|---|---|
| `X-Cache: Hit`, `Age > 0`, 정적 파일 | edge/cache ownership 후보 강함 | 이미 저장된 응답을 재사용했을 가능성이 크다 |
| `CF-Cache-Status: HIT`, `Age > 0`, `200` | CDN cache ownership 후보 강함 | origin 직답보다 edge hit 신호가 더 강하다 |
| `X-Cache: Miss`, `200` 또는 `5xx` | cache 계층 경유, owner 보류 | cache를 거쳤지만 이번 body를 누가 만들었는지는 더 봐야 한다 |
| `X-Cache: Hit`인데 body가 branded HTML error | edge/CDN 응답 후보 강함 | app business HTML보다 edge 에러 페이지 후보가 더 크다 |
| `X-Cache: Hit`인데 JSON API | cached API 응답 또는 intermediary JSON 후보 | app 실시간 처리라고 바로 단정하면 빠르다 |

초급자용 한 줄 규칙:

- `hit + age`가 같이 보이면 app ownership 확정을 늦춘다
- `miss`면 cache 경유 사실만 적고 owner는 body/header를 더 본다

## 흔한 오해와 함정

- `Age`를 보고 "응답 시간이 120ms"라고 읽는다. `Age`는 보통 cache에 머문 시간(초) 쪽 단서다.
- `X-Cache: Hit`를 보고 "원본 app은 완전히 무관하다"고 단정한다. 원본 정책과 이전 origin 응답이 바탕일 수 있다.
- `X-Cache: Miss`를 보고 "그러면 무조건 app이 직접 응답했다"고 단정한다. gateway나 CDN error translation도 가능하다.
- cache 관련 헤더가 보이는데도 body owner를 먼저 app JSON/app HTML로 고정한다. 첫 pass에서는 cache ownership 후보를 먼저 적는 편이 안전하다.
- `304`와 `Age`를 같은 뜻으로 읽는다. `304`는 재검증 결과이고, `Age`는 cache된 응답의 나이 단서다.

## 실무에서 쓰는 모습

| 보인 헤더 조합 | 초급자 incident 메모 |
|---|---|
| `X-Cache: Hit`, `Age: 300`, `Content-Type: text/css` | "정적 파일 edge cache hit 후보, app 실시간 처리 증거 약함" |
| `CF-Cache-Status: HIT`, `Age: 45`, `Content-Type: application/json` | "Cloudflare cache 재사용 후보, API도 cached path 가능성 열어 둠" |
| `X-Cache: Miss`, `Server: CloudFront`, `502` | "CloudFront 경유는 보이지만 이번 owner는 edge/origin 추가 확인 필요" |
| `X-Cache: Hit`, `text/html`, branded error body | "CDN/edge가 직접 보여 준 cached/error page 후보" |

실무에서는 아래 순서로 적으면 충분하다.

1. cache hit/miss 표기가 있는가
2. `Age`가 있는가
3. body 타입이 정적 파일/JSON/HTML 중 무엇인가
4. owner 메모를 `app 확정` 대신 `edge cache 후보` 또는 `owner 보류`로 남긴다

## 더 깊이 가려면

- `Server`/`Via`/`X-Request-Id`까지 묶어 첫 헤더 분기를 보고 싶으면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- CloudFront/Cloudflare vendor별 표기를 더 구체적으로 읽고 싶으면 [CDN Vendor Header Crosswalk Mini Card: CloudFront / Cloudflare 단서 읽기](./cdn-vendor-header-crosswalk-cloudfront-cloudflare-mini-card.md)
- body가 app JSON인지 gateway HTML인지도 같이 잘라야 하면 [Browser DevTools Response Body Ownership 체크리스트](./browser-devtools-response-body-ownership-checklist.md)
- browser cache `304`/`memory cache`와 CDN cache 헤더를 분리하고 싶으면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- CDN 역할 자체가 아직 낯설면 [CDN 기초 (CDN Basics)](../system-design/cdn-basics.md)

## 면접/시니어 질문 미리보기

**Q. `X-Cache: Hit`이면 app은 아예 호출되지 않았다고 봐도 되나요?**  
이번 요청 처리에서는 edge 재사용일 수 있지만, 어떤 응답이 cache에 들어갔는지는 origin 정책과 이전 fetch가 결정했으므로 app과 완전히 무관하다고 단정하긴 이르다.

**Q. `Age`는 왜 first pass에서 중요하나요?**  
`Age`가 보이면 "지금 막 app이 계산한 응답"보다 "이미 cache에 있던 응답" 후보를 먼저 떠올릴 수 있어서 owner 오판을 줄인다.

## 한 줄 정리

DevTools 첫 pass에서 `X-Cache`, `Age`, `CF-Cache-Status`가 보이면 app ownership을 서둘러 확정하지 말고, 먼저 `edge/CDN cache 재사용 후보`로 읽어 두는 편이 초급자에게 가장 안전하다.
