# HTTP 의미론과 캐싱 첫 원리 입문

> 한 줄 요약: HTTP는 "이 요청이 무슨 뜻인가"를 메서드로 표현하고, "이 응답 사본을 어디서 얼마나 다시 써도 되는가"를 캐시 헤더로 표현하는 계약이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [HTTP 캐시 재사용 vs 연결 재사용 vs 세션 유지 입문](./http-cache-reuse-vs-connection-reuse-vs-session-persistence-primer.md)
- [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [network 카테고리 인덱스](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: http semantics, http caching first principles, safe vs idempotent, browser cache vs server cache, browser cache vs server-side cache, shared cache basics, reverse proxy cache basics, cdn cache basics, conditional request first principles, cache-control primer, beginner http caching, beginner http semantics, get post cache semantics, 304 first principles, public private cache

<details>
<summary>Table of Contents</summary>

- [왜 함께 봐야 하나](#왜-함께-봐야-하나)
- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [메서드 의미: Safe와 Idempotent](#메서드-의미-safe와-idempotent)
- [캐시는 어디에 존재하나](#캐시는-어디에-존재하나)
- [Cache-Control과 validator는 무엇을 나누나](#cache-control과-validator는-무엇을-나누나)
- [조건부 요청은 어떻게 흐르나](#조건부-요청은-어떻게-흐르나)
- [브라우저 캐시와 서버 사이드 캐시는 무엇이 다른가](#브라우저-캐시와-서버-사이드-캐시는-무엇이-다른가)
- [CDN과 리버스 프록시는 어디에 끼나](#cdn과-리버스-프록시는-어디에-끼나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음 문서](#다음-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 함께 봐야 하나

HTTP를 처음 배울 때는 보통 메서드와 캐시를 따로 외운다.

- `GET`은 조회
- `POST`는 생성
- `Cache-Control`은 캐시 정책
- `ETag`는 재검증용 헤더

그런데 실제로는 이들이 한 묶음으로 움직인다.

- 메서드는 이 요청이 조회인지 변경인지 알려준다
- 캐시는 그 응답 사본을 다시 써도 되는지 알려준다
- 프록시와 CDN은 이 신호를 보고 재사용, 재검증, 전달 방식을 결정한다

입문자가 가장 자주 헷갈리는 장면은 "왜 `GET`은 캐시 얘기와 같이 나오고, 왜 `POST`는 재시도와 중복 생성 얘기와 같이 나오지?"이다.
답은 간단하다. **HTTP 의미론이 캐시와 재시도의 전제**이기 때문이다.

## 먼저 잡을 mental model

HTTP를 볼 때는 아래 네 질문을 순서대로 던지면 된다.

| 질문 | HTTP가 주는 신호 | 대표 예시 |
|---|---|---|
| 이 요청은 무엇을 하려는가 | 메서드 의미론 | `GET`, `POST`, `PUT`, `DELETE` |
| 이 응답을 지금 바로 다시 써도 되는가 | freshness 정책 | `Cache-Control: max-age=60` |
| 다시 확인해야 한다면 무엇을 비교하는가 | validator | `ETag`, `Last-Modified`, `If-None-Match`, `304` |
| 누가 그 사본을 들고 있는가 | 캐시 계층 | 브라우저, CDN/리버스 프록시, 서버 사이드 캐시 |

즉 HTTP는 "요청의 의도"와 "응답 사본의 재사용 규칙"을 함께 설명하는 프로토콜이다.

## 메서드 의미: Safe와 Idempotent

먼저 메서드가 무엇을 약속하는지 잡아야 한다.

| 메서드 | 기본 의도 | Safe | Idempotent | 입문 감각 |
|---|---|---|---|---|
| `GET` | 조회 | 그렇다 | 그렇다 | 캐시와 재검증의 중심 메서드 |
| `HEAD` | 헤더만 조회 | 그렇다 | 그렇다 | body 없이 메타데이터만 확인 |
| `POST` | 생성, 처리 요청 | 아니다 | 아니다 | 중복 생성 위험이 있다 |
| `PUT` | 전체 교체 | 아니다 | 그렇다 | 같은 요청을 다시 보내도 최종 상태는 같다 |
| `PATCH` | 부분 수정 | 아니다 | 상황에 따라 다르다 | 연산 의미에 따라 달라진다 |
| `DELETE` | 삭제 | 아니다 | 그렇다 | 두 번째 호출이 `404`여도 최종 상태는 같다 |

### Safe

`Safe`는 "요청한 동작이 서버 상태 변경을 목적으로 하지 않는다"는 뜻이다.
로그 적재나 메트릭 증가처럼 부수 효과가 있을 수는 있지만, **리소스를 바꾸는 요청으로 취급하지 않는다**.

### Idempotent

`Idempotent`는 "같은 요청을 여러 번 보내도 서버의 최종 상태가 같다"는 뜻이다.
응답 코드가 매번 같아야 한다는 뜻은 아니다.

예를 들어 `DELETE /orders/42`를 두 번 보내면:

- 첫 번째는 `204 No Content`
- 두 번째는 `404 Not Found`

가 될 수 있다. 그래도 최종 상태는 둘 다 "주문 42가 없다"이므로 멱등적이다.

### 캐시와 왜 이어지나

캐시는 주로 **조회 결과를 재사용**하는 장치다.
그래서 `GET`과 `HEAD`가 캐시 얘기의 중심에 놓인다.

반대로 `POST`처럼 상태 변경 가능성이 큰 요청은 브라우저, 프록시, CDN이 "이 응답을 일반적인 조회 결과처럼 재사용해도 된다"라고 쉽게 가정하지 않는다.

특히 `GET`으로 상태를 바꾸면 위험하다.

- 브라우저 새로고침
- 링크 미리보기
- crawler 접근
- 프록시 재시도

같은 평범한 동작이 의도치 않은 변경 요청으로 바뀔 수 있기 때문이다.

## 캐시는 어디에 존재하나

캐시는 하나가 아니다. 위치에 따라 역할이 달라진다.

| 계층 | 위치 | 누구와 공유하나 | 주로 저장하는 것 | 대표 목적 |
|---|---|---|---|---|
| 브라우저 캐시 | 사용자 브라우저 메모리/디스크 | 같은 사용자/기기 안 | HTTP 응답 사본 | 새로고침과 재방문을 빠르게 |
| 공유 캐시 | CDN, 캐싱 리버스 프록시 | 여러 사용자 사이 | 공개 가능한 HTTP 응답 사본 | origin 부하와 지연 감소 |
| 서버 사이드 캐시 | 애플리케이션 메모리, Redis 등 | 서비스 내부 | DB 조회 결과, 계산 결과, 렌더링 결과 | origin 내부 연산을 줄이기 |

핵심은 앞의 두 개는 **HTTP 응답 사본**을 다루고, 마지막 하나는 보통 **애플리케이션 내부 데이터**를 다룬다는 점이다.

## Cache-Control과 validator는 무엇을 나누나

캐싱 헤더는 역할이 둘로 나뉜다.

| 헤더/개념 | 답하는 질문 | 예시 |
|---|---|---|
| `Cache-Control` | 이 사본을 얼마나 바로 써도 되는가 | `max-age=60`, `public`, `private`, `no-cache`, `no-store` |
| `ETag`, `Last-Modified` | 다시 확인할 때 무엇을 비교하는가 | `"product-42-v7"`, `Tue, 14 Apr 2026 09:00:00 GMT` |
| `If-None-Match`, `If-Modified-Since` | 클라이언트가 어떤 사본을 들고 재검증하는가 | 조건부 요청 |
| `304 Not Modified` | 서버가 기존 사본을 계속 써도 된다고 답하는가 | body 없이 재사용 허용 |

### 자주 보는 `Cache-Control`

| 값 | 뜻 |
|---|---|
| `max-age=60` | 60초 동안은 fresh하다고 보고 바로 재사용 가능 |
| `no-cache` | 저장은 가능하지만 쓰기 전에 재검증해야 함 |
| `no-store` | 저장 자체를 하지 말아야 함 |
| `public` | 공유 캐시도 저장 가능 |
| `private` | 브라우저 같은 개인 캐시에만 두는 쪽이 안전 |

입문 관점에서는 이렇게 기억하면 된다.

- `Cache-Control`은 "지금 바로 써도 되나?"
- `ETag`, `Last-Modified`는 "다시 확인할 때 뭘 들고 가나?"

## 조건부 요청은 어떻게 흐르나

`GET /products/42`를 예로 보면 아래처럼 읽으면 된다.

```text
1. 브라우저 -> CDN/리버스 프록시 -> origin
   GET /products/42

2. origin -> 200 OK
   Cache-Control: public, max-age=60
   ETag: "product-42-v7"

3. 같은 사용자가 60초 안에 다시 보면
   브라우저 캐시가 바로 응답할 수 있다

4. 다른 사용자가 같은 URL을 60초 안에 요청하면
   CDN/리버스 프록시 캐시가 origin 대신 응답할 수 있다

5. 60초가 지나면 브라우저나 CDN이 재검증한다
   If-None-Match: "product-42-v7"

6-A. 안 바뀌었으면 origin이 304 Not Modified
   기존 body를 계속 사용

6-B. 바뀌었으면 origin이 200 OK + 새 body + 새 ETag
   캐시 사본을 교체
```

여기서 중요한 점은 세 가지다.

- `304`는 "네트워크 요청이 없었다"가 아니라 "서버가 body 재전송을 생략했다"는 뜻이다
- 브라우저 캐시 hit와 CDN 캐시 hit는 서로 다른 사건이다
- 둘 다 stale해지면 결국 origin에 재검증이나 새 요청이 간다

## 브라우저 캐시와 서버 사이드 캐시는 무엇이 다른가

이 구분은 초급 단계에서 반드시 분리해 두는 편이 좋다.

| 항목 | 브라우저 캐시 | 서버 사이드 캐시 |
|---|---|---|
| 위치 | 사용자 브라우저 | 애플리케이션 서버, Redis, 메모리 |
| 저장 단위 | HTTP 응답 사본 | DB 결과, 계산 결과, 객체, 템플릿 결과 |
| 제어 방법 | `Cache-Control`, `ETag`, `Last-Modified` 같은 HTTP 헤더 | 애플리케이션 코드와 캐시 라이브러리 |
| 사용자 간 공유 | 보통 사용자별 | 서비스 내부에서 공유 가능 |
| `304`와의 관계 | 직접 관련 있다 | 보통 직접 관련 없다 |
| DevTools에서 보이나 | 보인다 | 보이지 않는다 |

예를 들어:

- 브라우저 캐시는 `GET /products/42`의 HTML이나 JSON 응답을 다시 쓴다
- 서버 사이드 캐시는 origin이 그 응답을 만들기 전에 필요한 상품 조회 결과를 Redis에서 꺼낼 수 있다

즉 서버 사이드 캐시가 잘 되어 있어도 브라우저는 여전히 매번 네트워크를 탈 수 있고,
반대로 브라우저 캐시가 강하면 origin 내부 Redis를 건드리기 전에 응답이 끝날 수도 있다.

## CDN과 리버스 프록시는 어디에 끼나

리버스 프록시는 **서버 앞**에 서는 중간 계층이다.
TLS 종료, 라우팅, 압축, 로드밸런싱, 캐싱을 담당할 수 있다.

CDN은 쉽게 말해 **지리적으로 분산된 캐싱 리버스 프록시**에 가깝다.

| 구분 | 기본 위치 | 핵심 역할 | 캐시 관점 |
|---|---|---|---|
| 리버스 프록시 | origin 바로 앞 | TLS 종료, 라우팅, 보호, 캐싱 가능 | 서버 앞 공유 캐시가 될 수 있다 |
| CDN | 사용자와 origin 사이 여러 edge | 가까운 위치에서 전달, offload, 전 세계 분산 | edge 공유 캐시 역할이 강하다 |

입문 단계에서는 이렇게 이해하면 충분하다.

- 브라우저 캐시: 사용자 바로 앞
- CDN/리버스 프록시 캐시: 서버 바로 앞 또는 edge
- 서버 사이드 캐시: 서버 안쪽

그리고 항상 기억할 점:

- 모든 리버스 프록시가 캐시를 켜는 것은 아니다
- CDN도 `Cache-Control`과 별도 정책을 함께 본다
- 개인화 응답은 `public` shared cache에 태우면 사고가 날 수 있다

예를 들어 `GET /me` 같은 로그인 사용자 전용 응답은 보통 `private` 또는 `no-store`가 맞고,
`GET /products/42` 같은 공개 상품 조회는 `public` shared cache 후보가 된다.

## 자주 헷갈리는 포인트

- `no-cache`는 "저장 금지"가 아니다. 저장은 하되 재사용 전에 확인하라는 뜻이다.
- `304 Not Modified`는 브라우저 단독 판단이 아니라 서버와 재검증을 주고받은 결과다.
- 멱등성은 응답이 같다는 뜻이 아니라 최종 서버 상태가 같다는 뜻이다.
- 브라우저 캐시와 서버 사이드 캐시는 둘 다 "캐시"지만 저장 위치, 제어 신호, 관찰 도구가 다르다.
- CDN 캐시 hit가 나도 브라우저 캐시는 miss일 수 있고, 반대도 가능하다.
- `POST`도 특정 조건에서 캐시할 수는 있지만, 입문 단계에서는 `GET`/`HEAD`가 기본 캐시 대상이라고 이해하는 편이 안전하다.

## 다음 문서

- 메서드 의미를 더 분리해서 보고 싶다면: [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- `ETag`, `Last-Modified`, `304` 흐름을 더 자세히 보고 싶다면: [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- 브라우저 `memory cache`, `disk cache`, `304`를 실제 trace로 읽고 싶다면: [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- 프록시와 리버스 프록시 구도를 먼저 따로 보고 싶다면: [프록시와 리버스 프록시 기초](./proxy-reverse-proxy-basics.md)
- shared cache 정책과 무효화까지 이어 가려면: [Cache-Control 실전](./cache-control-practical.md) -> [CDN 캐시 키와 무효화 전략](./cdn-cache-key-invalidation.md)

## 한 줄 정리

HTTP 의미론은 요청의 의도를 정하고, 캐싱 의미론은 그 응답 사본을 브라우저·CDN·origin 중 어디서 얼마나 믿고 다시 쓸지 정한다.
