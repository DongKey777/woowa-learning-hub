# 421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문

> 한 줄 요약: 잘못된 H2/H3 connection reuse는 `421 Misdirected Request`를 부르고, 브라우저에서는 같은 URL이 새 connection에서 다시 보이는 흐름으로 나타날 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- [421 Retry Path Mini Guide: Fresh H3 Connection vs H2 Fallback](./421-retry-path-mini-guide-fresh-h3-vs-h2-fallback.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [421 Non-Idempotent Retry Guardrail Primer](./http-421-non-idempotent-retry-guardrail-primer.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [Chrome NetLog H3 421 Drilldown: DevTools로 부족할 때 Coalescing Rejection과 Retry Decision 읽기](./chrome-netlog-h3-421-drilldown.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

retrieval-anchor-keywords: 421 retry after wrong coalescing, wrong connection reuse, wrong h2 connection retry, wrong h3 connection retry, browser 421 retry, connection coalescing retry, devtools same url retried, new connection after 421, http/2 421 retry example, http/3 421 retry example, alt-svc wrong h3 reuse, 421 browser flow, 421이 왜 떠요, 같은 url이 두 번 떠요, 421 basics

<details>
<summary>Table of Contents</summary>

- [왜 이 follow-up이 필요한가](#왜-이-follow-up이-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [같은 URL 두 줄일 때 421 recovery와 304 revalidation 먼저 가르기](#같은-url-두-줄일-때-421-recovery와-304-revalidation-먼저-가르기)
- [H2와 H3를 한 표로 보면](#h2와-h3를-한-표로-보면)
- [브라우저 예시 1: H2에서 잘못 공유된 연결](#브라우저-예시-1-h2에서-잘못-공유된-연결)
- [브라우저 예시 2: H3에서 잘못 재사용된 QUIC 연결](#브라우저-예시-2-h3에서-잘못-재사용된-quic-연결)
- [DevTools에서 무엇을 먼저 보면 되나](#devtools에서-무엇을-먼저-보면-되나)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 follow-up이 필요한가

[HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)과 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)을 읽고 나면 초보자는 이런 장면에서 다시 막힌다.

- `421`이 뜨면 그냥 실패한 것인가?
- 왜 같은 URL이 브라우저에서 한 번 더 보이기도 하나?
- H2와 H3 모두 "잘못된 connection reuse -> `421` -> 새 connection retry"로 보면 되나?

이 문서는 그 질문에만 집중한다.

- H2에서는 `ORIGIN` frame이나 authority 경계와 안 맞는 reuse가 `421`로 되돌아올 수 있다.
- H3에서는 certificate와 endpoint authority를 잘못 믿고 같은 QUIC connection을 재사용하면 `421`이 복구 신호가 될 수 있다.
- 브라우저 화면에서는 "같은 URL이 짧게 `421` 후 새 connection에서 다시 뜨는 흐름"으로 보일 수 있다.

### Retrieval Anchors

- `421 retry after wrong coalescing`
- `wrong connection reuse`
- `browser 421 retry`
- `devtools same url retried`
- `http/2 421 retry example`
- `http/3 421 retry example`

---

## 먼저 잡는 mental model

아주 짧게는 이렇게 기억하면 된다.

- wrong coalescing: 브라우저가 "이 connection도 같이 써도 되겠다"라고 보고 다른 origin 요청을 실었다.
- `421`: 서버가 "그 요청은 이 connection으로 받지 않겠다"라고 답했다.
- retry: 브라우저가 같은 URL을 **다른 connection**으로 다시 보낼 근거를 얻었다.

비유하면:

- 첫 시도는 "익숙한 문으로 일단 들어가 보기"
- `421`은 "그 문 말고 옆문으로 오세요"
- retry는 "같은 손님이 옆문으로 다시 입장"

중요한 점은 `421`이 URL 자체가 틀렸다는 뜻이 아니라, **connection 문맥이 틀렸다는 뜻**에 가깝다는 점이다.

초급자용 오해 방지 한 줄:

- `421`은 앱 권한/리소스 결과를 직접 뜻하지 않는다
- 먼저 봐야 할 것은 "같은 URL이 다른 connection에서 다시 보였나?"다

### 3줄로 보는 `421 -> 200` 빠른 예시

```text
1) GET /api/me -> 421  (기존 shared connection이 거절됨)
2) GET /api/me -> 200  (같은 URL을 새 connection으로 다시 보냄)
3) 따라서 같은 URL 두 줄만 보고 "프런트가 중복 호출했다"라고 바로 단정하지 않는다
```

이 3줄 예시는 beginner가 가장 먼저 버려야 할 오해 하나를 겨냥한다.

- `421 -> 200`은 "같은 요청이 recovery된 장면"일 수 있다.
- 즉 같은 URL 두 줄이 보여도 원인이 항상 중복 호출은 아니다.

---

## 같은 URL 두 줄일 때 421 recovery와 304 revalidation 먼저 가르기

초급자는 "같은 URL이 두 번 보였다"는 표면만 보고 둘을 섞기 쉽다.

- `421 recovery`는 **잘못 탄 connection을 갈아타는 장면**
- `304 revalidation`은 **같은 URL을 서버에 다시 확인하고 기존 body를 계속 쓰는 장면**

먼저 이 한 표로 자르면 Network 탭 첫 판독이 빨라진다.

| 구분 | `421 recovery` | `304 revalidation` |
|---|---|---|
| 먼저 떠오를 질문 | "잘못된 connection으로 갔나?" | "브라우저가 cache를 다시 확인했나?" |
| 첫 줄 status | `421` | 보통 첫 줄 `200`, 반복 방문 줄에서 `304` |
| 둘째 줄이 다시 보이는 이유 | 브라우저가 **다른 connection**으로 retry | 브라우저가 validator를 보내고 **기존 body** 재사용 |
| DevTools에서 먼저 볼 것 | `Connection ID`, `Remote Address`, `Protocol` 변화 | request의 `If-None-Match`/`If-Modified-Since`, status `304` |
| body를 어디서 쓰나 | retry 후 새 응답이 올 수 있음 | 기존 cache body를 계속 씀 |
| 초급자 한 줄 결론 | cache보다 **wrong connection 복구**를 먼저 본다 | retry보다 **cache 재검증**을 먼저 본다 |

가장 짧은 판별 규칙은 아래 3줄이다.

1. 첫 줄이 `421`이면 cache보다 connection 교정 신호를 먼저 본다.
2. request header에 validator가 있고 status가 `304`면 wrong connection보다 재검증을 먼저 본다.
3. 같은 URL 두 줄이어도 `Connection ID`가 바뀌면 `421 recovery` 쪽, validator + `304`가 보이면 `304 revalidation` 쪽이다.

작게 그려 보면 이렇게 읽으면 된다.

```text
421 recovery:
같은 URL -> 421 -> 새 connection -> 200/403/404...

304 revalidation:
같은 URL 반복 방문 -> If-None-Match/If-Modified-Since -> 304 -> 기존 cache body 사용
```

자주 하는 오해:

- 같은 URL이 두 줄이면 무조건 프런트 중복 호출이라고 단정한다.
- `304`도 "다시 갔으니 retry"라고 부른다.
- `421 -> 200` 장면을 cache hit처럼 말한다.

## 같은 URL 두 줄일 때 421 recovery와 304 revalidation 먼저 가르기 (계속 2)

이 문서는 `421 recovery`를 설명하는 entrypoint다.
같은 URL trace에서 `304` 판독이 더 궁금하면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)를 먼저 같이 보면 된다.

---

## H2와 H3를 한 표로 보면

| 항목 | HTTP/2 | HTTP/3 |
|---|---|---|
| 잘못 재사용한 대상 | 기존 TLS/H2 connection | 기존 QUIC/H3 connection |
| 브라우저가 처음 믿은 근거 | certificate, 기존 edge, coalescing 후보 판단 | certificate, `Alt-Svc`/HTTPS RR로 배운 endpoint, 기존 QUIC connection |
| 서버가 주로 거절하는 이유 | `:authority`가 이 connection의 origin set과 맞지 않음 | 이 H3 endpoint가 그 origin에 authoritative하지 않음 |
| 브라우저 화면에서 흔한 모습 | 같은 URL이 `421` 뒤 새 H2 connection에서 다시 뜸 | 같은 URL이 `421` 뒤 새 H3 connection 또는 H2 fallback으로 다시 뜸 |
| beginner 한 줄 | "잘못 탄 shared H2 connection에서 내려서 다시 탄다" | "잘못 탄 shared QUIC connection에서 내려서 다시 탄다" |

핵심은 둘 다 같다.

- 첫 요청이 **wrong connection**
- 서버가 `421`
- 브라우저가 **new connection retry**

다만 H3는 retry 결과가 꼭 H3일 필요는 없다.
브라우저가 그 origin에 대해 기존 alternative service를 덜 믿게 되면 H2로 돌아갈 수도 있다.

---

## 브라우저 예시 1: H2에서 잘못 공유된 연결

상황을 단순하게 잡아 보자.

- `www.shop.test`와 `static.shop.test`는 같은 front door다.
- `admin.shop.test`는 별도 보안 경계다.
- 인증서는 세 host를 모두 커버한다.
- 브라우저는 이미 `www.shop.test`용 H2 connection을 하나 열어 둔 상태다.

이때 브라우저가 `admin.shop.test` 요청까지 그 connection에 태우면 아래처럼 흘러갈 수 있다.

1. 브라우저가 기존 H2 connection에 `GET https://admin.shop.test/api/me`를 실는다.
2. 서버는 "이 connection은 `admin`용이 아니다"라고 본다.
3. 서버가 `421 Misdirected Request`를 보낸다.
4. 브라우저는 `admin` 전용 새 connection을 연다.
5. 같은 `GET /api/me`를 새 connection에서 다시 보낸다.

DevTools에서 입문자가 보는 모습은 대략 이런 표에 가깝다.

| URL | Status | Protocol | Connection ID | Remote Address | 읽는 법 |
|---|---:|---|---:|---|---|
| `https://admin.shop.test/api/me` | `421` | `h2` | `17` | `203.0.113.10:443` | `admin` 요청이 `www/static` 쪽 shared H2 connection에 잘못 실렸을 수 있음 |
| `https://admin.shop.test/api/me` | `200` | `h2` | `24` | `203.0.113.20:443` | 브라우저가 새 H2 connection으로 retry했고 이번에는 맞는 front door에 도착했을 수 있음 |

여기서 초보자가 읽어야 할 포인트는 세 개다.

- URL은 같다.
- 첫 row와 두 번째 row의 connection id나 remote address가 다르다.
- `403/404` 같은 app 결과처럼 같은 connection에서 그대로 실패한 것이 아니라, **connection을 갈아탄 뒤 결과가 바뀐다**.

이 흐름은 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)의 "사전 범위 제한 + 사후 `421`"이 브라우저 화면에서 어떻게 보이는지에 가깝다.

---

## 브라우저 예시 2: H3에서 잘못 재사용된 QUIC 연결

이번에는 H3 쪽 예시다.

- `www.shop.test`가 `Alt-Svc: h3="edge.shop-cdn.test:443"`를 광고했다.
- 브라우저는 그 덕분에 H3/QUIC connection을 이미 하나 열어 둔 상태다.
- certificate는 `www`, `static`, `admin`을 모두 커버한다.
- 하지만 `admin.shop.test`는 같은 H3 endpoint에서 받으면 안 된다.

이때 브라우저가 `admin` 요청을 기존 QUIC connection에 태우면 아래처럼 보일 수 있다.

1. 브라우저가 `GET https://admin.shop.test/api/me`를 기존 H3 connection으로 보낸다.
2. 서버 또는 edge는 "이 endpoint는 `admin`에 authoritative하지 않다"라고 판단한다.
3. `421`을 돌려준다.
4. 브라우저는 그 origin에 대해 다른 connection을 선택한다.
5. 새 H3 connection으로 다시 가거나, 더 보수적으로 H2로 fallback해서 다시 간다.

DevTools에서 볼 수 있는 축약 예시는 이렇다.

| URL | Status | Protocol | Connection ID | Remote Address | 읽는 법 |
|---|---:|---|---:|---|---|
| `https://admin.shop.test/api/me` | `421` | `h3` | `42` | `198.51.100.30:443` | `admin` 요청이 기존 shared QUIC connection에 잘못 실렸을 수 있음 |
| `https://admin.shop.test/api/me` | `200` | `h3` | `51` | `198.51.100.44:443` | 브라우저가 `admin`용 새 H3 connection으로 retry했을 수 있음 |
| `https://admin.shop.test/api/me` | `200` | `h2` | `63` | `198.51.100.44:443` | 브라우저가 더 보수적으로 H2 fallback을 택했을 수도 있음 |

H3에서 초보자가 특히 기억할 점은 이것이다.

- retry가 꼭 "같은 H3 connection 재시도"는 아니다.
- 같은 H3라도 **새 QUIC connection**이어야 의미가 있다.
- 경우에 따라 브라우저는 그 origin에 대해 H3 대신 H2를 다시 선택할 수 있다.

즉 H3에서 보는 `421 retry`는 "same URL, different connection, sometimes different protocol"이라고 읽는 편이 안전하다.

---

## DevTools에서 무엇을 먼저 보면 되나

이 문서는 trace deep dive가 아니라 entrypoint다.
그래도 `421 retry` 흐름을 빠르게 잡으려면 아래 네 가지만 먼저 보면 된다.

| 먼저 볼 것 | 왜 보나 | 기대하는 신호 |
|---|---|---|
| 같은 URL row가 연속으로 있는가 | retry 여부 확인 | 첫 row는 `421`, 뒤 row는 `200/403/404` 등으로 바뀔 수 있음 |
| `Protocol`이 바뀌었는가 | H3 -> H2 fallback 여부 확인 | `h3` 뒤 `h2`가 보이면 connection 전략이 바뀐 것 |
| `Connection ID` 또는 connection 식별값이 바뀌었는가 | 새 connection인지 확인 | 같은 URL인데 다른 connection id |
| `Remote Address`가 바뀌었는가 | 다른 edge/front door로 갔는지 확인 | 첫 row와 두 번째 row의 주소가 다를 수 있음 |

입문 단계에서는 이 순서만 기억해도 충분하다.

1. 같은 URL이 두 번 보였나?
2. 첫 번째는 `421`인가?
3. 두 번째는 다른 connection인가?
4. 결과가 `200` 또는 다른 status로 바뀌었나?

더 자세한 DevTools, `curl`, proxy log 판독은 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)로 이어서 보면 된다.

---

## 자주 헷갈리는 포인트

### `421`이면 URL이 틀렸다는 뜻인가

보통 그보다는 **connection이 틀렸다는 뜻**에 가깝다.

- 같은 URL이
- 다른 connection에서
- 바로 성공할 수 있기 때문이다.

### 같은 URL이 두 번 보이면 프런트엔드가 중복 호출한 것인가

그럴 수도 있지만, `421` 직후라면 먼저 retry 흐름을 의심한다.

- 첫 row가 `421`
- 둘째 row가 새 connection

이면 브라우저의 재시도일 가능성이 있다.

아주 짧게 다시 쓰면:

- `421 -> 200` + 새 connection: recovery 쪽을 먼저 본다
- `200 -> 200` + 같은 connection: 중복 호출 쪽을 더 의심한다

### H3에서 `421` 뒤 retry면 항상 다시 `h3`인가

아니다.

- 새 H3 connection일 수도 있고
- H2 fallback일 수도 있다.

중요한 것은 "같은 프로토콜 유지"보다 **다른 connection으로 다시 갔는가**다.

### 모든 요청이 자동으로 다시 보내지나

이 beginner primer의 예시는 side effect가 없는 `GET` 기준으로 보는 편이 안전하다.

`421`은 다른 connection retry의 근거가 되지만, 실제 자동 재시도 여부는 client 구현과 요청 성격에 따라 달라질 수 있다.

---

## 다음에 이어서 볼 문서

- H2/H3 connection reuse 조건부터 다시 보려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- H2에서 `ORIGIN` frame과 `421`의 역할을 먼저 정리하려면 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- H3에서 certificate, `Alt-Svc`, endpoint authority를 더 보려면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- stale `Alt-Svc` 때문에 첫 시도만 `421`이고 fresh path에서 성공하는 H3 패턴은 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- 같은 URL trace에서 `304`, validator, cache body 재사용을 먼저 분리하려면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- `ETag`, `Last-Modified`, 조건부 요청 기본을 먼저 묶으려면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- DevTools, `curl`, proxy log 기준으로 `421`을 더 자세히 읽으려면 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)

---

## 한 줄 정리

wrong coalescing으로 잘못된 H2/H3 connection에 실린 요청은 `421 Misdirected Request`를 만나고, 브라우저에서는 같은 URL이 **새 connection**으로 다시 시도되는 흐름으로 보일 수 있다.
