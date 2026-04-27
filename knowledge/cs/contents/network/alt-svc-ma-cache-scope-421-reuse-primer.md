# Alt-Svc `ma`, Cache Scope, 421 Reuse Primer

> 한 줄 요약: `Alt-Svc`의 `ma`는 "이 H3 힌트를 얼마나 기억할까"를 뜻하고, cache scope는 "어느 origin의 메모인가"를 뜻하며, `421`은 "그 메모가 있어도 이 connection reuse는 틀렸다"는 교정 신호다.

**난이도: 🟢 Beginner**

관련 문서:

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [Alt-Svc Cache vs Per-Origin 421 Recovery](./alt-svc-cache-vs-per-origin-421-recovery.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [HTTPS / TLS 입문](../security/https-tls-beginner.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: alt-svc ma meaning, alt-svc cache scope, alt-svc origin scope, alt-svc host scope, alt-svc shared cache misunderstanding, alt-svc max age beginner, alt-svc basics, alt-svc alternative service cache, 421 misdirected request alt-svc, alt-svc 421 reuse, h3 alternative service reuse, alt-svc cache not http cache, what does alt-svc ma mean, why 421 after alt-svc, alt-svc beginner triage, alt-svc follow-up quick routing, alt-svc 421 question routing, alt-svc wrong interpretation, alt-svc misconception table, ma ttl vs connection lifetime, alt-svc self check, alt-svc mini quiz, ma is not connection lifetime, alt-svc beginner quiz, alt-svc scope vs reuse, cache scope vs cross-origin reuse, hint scope vs shared connection, alt-svc scope primer, reuse guardrail primer handoff, devtools alt-svc scope checklist, protocol remote address connection id alt-svc, per-origin alt-svc scope vs cross-origin reuse, alt-svc devtools checklist beginner

## 헷갈리면 이 문장으로 먼저 가르기

- 질문이 "`이 힌트가 어느 origin의 메모인가`"면 이 문서에서 `ma`와 cache scope를 먼저 본다.
- 질문이 "`이미 열린 connection을 다른 origin에도 같이 써도 되나`"면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)로 간다.
- 질문이 "`그 H3 endpoint를 어디서 배웠나`"면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)로 간다.

## 핵심 개념

`Alt-Svc` cache는 브라우저가 적어 두는 "origin별 우회 경로 메모"다. `ma`는 그 메모의 유효 시간이고, `421`은 "그 메모가 있더라도 이 shared connection으로 그 origin을 보내지는 마"라는 교정 신호다.

짧게 기억하면 된다.

- `ma`: 힌트의 신선도
- cache scope: 그 힌트를 배운 origin의 범위
- `421`: 잘못된 reuse를 끊고 다른 connection을 고르게 만드는 신호

## 한눈에 보기

| 항목 | beginner 해석 | 아닌 것 |
|---|---|---|
| `ma=3600` | "이 Alt-Svc 힌트를 최대 1시간 기억" | connection을 1시간 유지하라는 뜻 |
| cache scope | "`www.example.com`이 배운 메모" | `api.example.com`까지 자동 공유 |
| `421` | "이 origin은 이 connection으로 받지 않겠다" | `403/404` 같은 앱 권한/리소스 결과 |

`Alt-Svc` cache와 connection reuse는 연결되어 있지만 같은 단계는 아니다. 메모를 배웠다고 해서 모든 sibling host가 같은 H3 connection에 자동 탑승하지는 않는다.

## 자주 나오는 오해 3개: 잘못된 해석 vs 올바른 해석

| 잘못된 해석 | 올바른 해석 |
|---|---|
| "`ma=3600`이면 connection도 1시간 고정된다" | `ma`는 Alt-Svc 힌트 TTL이다. connection 수명은 별도 정책/상태로 결정된다. |
| "`www`가 배운 Alt-Svc는 `api`도 자동으로 같은 cache를 쓴다" | cache scope는 기본적으로 origin 단위다. cross-origin reuse는 인증서/authority/정책 검증을 따로 통과해야 한다. |
| "`421`이면 앱 권한이나 리소스가 틀렸다는 뜻이다" | 먼저 봐야 할 것은 app 권한이 아니라 connection reuse 문맥이다. `403/404`는 맞는 서버에 도착한 뒤의 app 결과이고, `421`은 그보다 앞단에서 "이 connection으로는 받지 않겠다"는 교정 신호다. |

헷갈릴 때는 먼저 이렇게 나누면 된다: "`ma` 질문인지(힌트 수명)", "`이 힌트가 누구 메모인지` 묻는 scope 질문인지", "`이미 열린 connection을 같이 써도 되는지` 묻는 reuse 질문인지".

## 초급자용 질문별 빠른 라우팅

| 지금 막힌 질문 | 여기서의 짧은 답 | 바로 다음 문서 |
|---|---|---|
| "`ma`가 길면 connection도 길게 고정되나?" | 아니다. `ma`는 hint TTL이지 connection lifetime이 아니다 | [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) |
| "`www`가 배운 `Alt-Svc`를 `api`도 바로 써도 되나?" | 보통 아니다. cache scope는 origin 단위고 cross-origin reuse 허가는 별도다 | [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md), [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md) |
| "`421`을 받았으면 `Alt-Svc`가 전부 깨진 건가?" | 전부가 아니라, 해당 origin의 reuse 경로를 좁히는 교정 신호일 때가 많다 | [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md), [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |
| "같은 URL이 `421` 뒤 바로 성공하면 중복 호출인가?" | 중복 호출일 수도 있지만 stale path에서 fresh path로 retry recovery일 가능성을 먼저 본다 | [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md), [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |
| "discovery와 reuse를 자꾸 섞는다" | endpoint를 어디서 배웠는지(discovery)와 connection 공유 허가(reuse)는 다른 단계다 | [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md) |

이 표는 `ma`/scope/`421` 질문이 섞였을 때 "지금 내 질문이 discovery인지, reuse 경계인지, recovery인지"를 30초 안에 가르는 용도다.

## DevTools Alt-Svc Scope 체크리스트

초보자는 `Alt-Svc` scope와 cross-origin connection reuse를 같은 장면으로 섞기 쉽다.
DevTools에서는 "`누가 힌트를 배웠나`"와 "`누가 같은 connection을 같이 탔나`"를 따로 읽어야 한다.

먼저 아주 짧게 구분하면 이렇다.

- per-origin `Alt-Svc` scope: "`www.example.com`이 자기용 H3 힌트를 배웠는가"
- cross-origin connection reuse: "`api.example.com` 요청이 이미 열려 있던 `www` connection에 같이 실렸는가"

### 30초 체크 순서

| 순서 | DevTools에서 보는 칸 | 초보자 질문 | 안전한 해석 |
|---|---|---|---|
| 1 | `Protocol` | 이 요청이 `h2`인가 `h3`인가 | `h3`라고 해서 곧바로 cross-origin reuse 성공을 뜻하지는 않는다. 일단 H3 path를 탔다는 뜻에 가깝다 |
| 2 | `Remote Address` | 어느 edge/IP:port로 붙었나 | 같은 주소는 같은 목적지 힌트일 뿐이다. 같은 connection 증거는 아니다 |
| 3 | `Connection ID` | 같은 connection을 재사용했나 | 같은 ID면 reuse 후보, 다른 ID면 새 connection 후보다 |

이 세 칸을 함께 읽으면 질문이 둘로 갈라진다.

| 지금 보이는 장면 | 먼저 내릴 결론 |
|---|---|
| `www` 요청이 `h3`로 성공함 | `www` origin의 `Alt-Svc` hint가 쓰였을 가능성을 본다 |
| 바로 뒤 `api` 요청도 `h3`지만 `Connection ID`가 다름 | `api`가 H3를 썼더라도 `www` connection reuse라고 단정하지 않는다. origin별로 따로 connection을 열었을 수 있다 |
| `api` 요청이 `www`와 같은 `Connection ID`를 쓰다가 `421`을 받음 | 이건 per-origin hint scope보다 cross-origin reuse 거절 신호를 먼저 읽는다 |
| `api` 요청이 다른 `Connection ID`로 곧바로 성공 | `Alt-Svc` hint는 살아 있어도 shared connection reuse 범위는 좁혀졌다고 본다 |

### 아주 작은 예시

| URL | Status | Protocol | Remote Address | Connection ID | 초보자 판독 |
|---|---:|---|---|---:|---|
| `https://www.example.com/` | `200` | `h3` | `203.0.113.10:443` | `18` | `www`가 자기 origin용 H3 path를 썼다 |
| `https://api.example.com/me` | `200` | `h3` | `203.0.113.10:443` | `24` | 같은 edge일 수는 있어도 같은 connection reuse라고는 아직 못 말한다 |
| `https://api.example.com/me` | `421` | `h3` | `203.0.113.10:443` | `18` | `api`가 `www` connection에 잘못 실린 cross-origin reuse 거절 후보 |

여기서 핵심은 아래 두 문장을 분리하는 것이다.

- "`www`가 `Alt-Svc`를 배웠다"는 origin별 힌트 이야기다.
- "`api`가 `www`의 connection을 같이 썼다"는 connection reuse 이야기다.

같은 `Remote Address`만으로는 둘을 합치면 안 된다.
cross-origin reuse 여부는 `Connection ID`가 더 직접적인 증거이고, `421`은 그 reuse가 틀렸다는 교정 신호다.

### 흔한 오해 방지 한 줄

- `Protocol`이 둘 다 `h3`여도 per-origin hint scope와 shared connection reuse는 다른 질문이다.
- `Remote Address`가 같아도 새 connection일 수 있다.
- 같은 `Connection ID`에서 다른 origin이 `421`을 받으면 "`Alt-Svc`가 전 origin에 공유됐다"보다 "그 shared connection reuse가 거절됐다"를 먼저 본다.

실제 칼럼 읽는 법이 더 필요하면 [Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문](./browser-devtools-protocol-column-labels-primer.md), `421` trace 흐름까지 같이 보면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)를 바로 이어서 본다.

## `421` 오해 방지 한 줄

초급자 기준으로는 아래 한 줄을 먼저 고정하면 된다.

- `421`: 앱 권한/리소스 오류를 직접 뜻하는 status가 아니라, 먼저 connection reuse 문맥이 맞는지 보라는 신호
- `403/404`: 맞는 서버와 path로 간 뒤 app 층에서 나온 결과

그래서 `421`을 봤을 때 첫 질문은 "권한이 왜 없지?"보다 "이 요청이 wrong connection에 실렸나?"가 더 안전하다.

## 상세 분해

```http
Alt-Svc: h3="edge.example.net:443"; ma=3600
```

이 header를 초급자 관점에서 읽으면 아래와 같다.

- `h3="edge.example.net:443"`: 다음 새 connection에서 시도할 H3 후보
- `ma=3600`: 그 후보를 최대 3600초 동안 신선한 힌트로 취급
- cache key 감각: "누가 이 힌트를 광고했는가"가 먼저다. `www.example.com`이 보낸 메모는 기본적으로 `www.example.com`의 메모다
- 그 뒤에야 reuse 판단이 온다. 다른 host가 같은 certificate를 쓰더라도 authority, routing, policy가 맞는지 별도 확인해야 한다

즉 `ma`는 수명, cache scope는 소유자, reuse는 그 다음 단계다.

## 흔한 오해와 함정

- `ma=86400`이면 하루 종일 무조건 H3라는 뜻이 아니다. QUIC 실패나 정책 때문에 H2로 fallback할 수 있다.
- `www`가 `Alt-Svc`를 광고했으면 `static`이나 `admin`도 같은 cache entry를 쓴다고 보면 안 된다.
- wildcard certificate가 넓어도 cache scope가 넓어지는 것은 아니다. certificate는 후보를 넓히는 조건일 뿐이다.
- `421`을 `403/404`처럼 앱 권한/리소스 결과로 읽으면 안 된다. 먼저 봐야 할 것은 authz나 route보다 connection reuse 문맥이다.
- `421`이 나왔다고 `Alt-Svc`가 전부 깨졌다고 단정하면 안 된다. 보통은 "이 origin을 이 reuse 경로에 싣지 말라"는 쪽에 더 가깝다.

## 실무에서 쓰는 모습

`www.shop.test`가 아래를 광고했다고 하자.

```http
Alt-Svc: h3="edge.shop-cdn.test:443"; ma=86400
```

짧은 흐름은 이렇다.

| 단계 | 브라우저가 배운 것 | 안전한 해석 |
|---|---|---|
| `www` 첫 응답 | `www`용 H3 후보를 배움 | `www` origin의 Alt-Svc cache가 warm 됨 |
| 이후 `www` 새 connection | H3 시도 가능 | `ma` 안이면 H3를 먼저 시도할 수 있음 |
| `static` 요청 | 같은 H3 connection 재사용 후보가 됨 | cache scope 공유가 아니라 reuse 검토 단계 |
| `admin` 요청이 잘못 실림 | edge가 `421` 반환 | 이 alternative-service/connection 조합은 `admin`에 맞지 않음 |
| 재시도 | 브라우저가 새 connection 또는 H2 fallback 선택 | `www`의 Alt-Svc hint가 살아 있어도 `admin` reuse는 좁혀질 수 있음 |

여기서 핵심은 `421`이 "메모를 지운다"보다 "재사용 범위를 다시 좁힌다"에 가깝다는 점이다.

## 3문항 셀프체크: `ma`를 connection 수명으로 읽지 않았는지 확인

아래 3문항은 초급자가 가장 자주 섞는 포인트만 다시 확인하는 용도다.

### Q1. `Alt-Svc: h3="edge.example.net:443"; ma=3600`를 보고 가장 안전한 해석은?

| 선택지 | 내용 |
|---|---|
| A | H3 connection을 정확히 1시간 유지하라는 뜻이다 |
| B | 이 H3 힌트를 최대 1시간 동안 기억할 수 있다는 뜻이다 |
| C | 1시간 동안 모든 sibling host가 자동으로 같은 H3 connection을 공유한다 |

정답: `B`

- `ma`는 hint TTL이다.
- 실제 connection은 idle timeout, network 상태, 브라우저 정책, 재시도 결과에 따라 더 빨리 닫힐 수 있다.

### Q2. `www.example.com`이 `Alt-Svc`를 광고했다. 그다음 `api.example.com` 요청도 같은 H3 connection으로 바로 보내도 될까?

| 선택지 | 내용 |
|---|---|
| A | 된다. 같은 도메인 계열이면 `ma` 동안 자동 공유된다 |
| B | 안 된다. `ma`가 0이 아니면 cross-origin reuse는 금지다 |
| C | 바로 단정하면 안 된다. cache scope와 cross-origin reuse 허가는 다른 판단이다 |

정답: `C`

- `www`가 배운 메모와 `api` reuse 허가는 같은 질문이 아니다.
- certificate, authority, routing, client 정책이 따로 맞아야 reuse가 가능하다.

### Q3. `admin.example.com` 요청이 기존 H3 connection에서 `421`을 받았다. 먼저 고쳐야 할 해석은?

| 선택지 | 내용 |
|---|---|
| A | `ma`가 만료됐으니 connection lifetime을 늘려야 한다 |
| B | 이 origin에는 이 reuse 경로가 맞는지 먼저 봐야 한다 |
| C | 앱 권한 오류이므로 `403` 처리 코드를 먼저 본다 |

정답: `B`

- `421`은 우선적으로 wrong connection reuse 가능성을 보게 만든다.
- 이것만으로 `Alt-Svc` 전체가 깨졌다고 단정하지 않는다.

## 셀프체크 한 줄 채점표

세 문항을 다 풀고 아래처럼 말할 수 있으면 이번 문서의 핵심은 잡은 것이다.

- "`ma`는 connection lifetime이 아니라 hint TTL이다."
- "`www`가 배운 Alt-Svc와 `api` reuse 허가는 같은 판단이 아니다."
- "`421`을 보면 먼저 app 권한보다 wrong connection reuse를 의심한다."

## 더 깊이 가려면

- `Alt-Svc` warming, expiry, stale hint 흐름부터 다시 보면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- discovery와 reuse를 분리해서 보면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- H3에서 certificate scope, endpoint authority, `421` guardrail을 더 보면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- browser에서 same-URL retry가 어떻게 보이는지는 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- `421`을 `403/404`와 구분하는 trace는 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)

## 면접/시니어 질문 미리보기

- "`ma`는 무엇의 TTL인가?"
  힌트의 TTL이지 connection lifetime이나 H3 성공 보장이 아니다.
- "`www`가 광고한 Alt-Svc를 `api`도 바로 써도 되나?"
  아니다. cache scope와 cross-origin reuse 허가는 분리해서 봐야 한다.
- "`421`을 받으면 클라이언트는 무엇을 배워야 하나?"
  그 origin을 그 shared connection 또는 alternative-service reuse 경로에 계속 싣지 말아야 한다는 점이다.

## 한 줄 정리

`Alt-Svc`에서 `ma`는 힌트의 수명, cache scope는 그 힌트를 배운 origin의 범위, `421`은 그 힌트를 들고도 잘못한 connection reuse를 교정하는 신호로 보면 된다.
