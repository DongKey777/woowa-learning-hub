# 브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문

> 한 줄 요약: 브라우저는 보통 현재 연결은 ALPN으로, 다음 새 연결의 H3 후보는 `Alt-Svc`로 배워서 고르므로 첫 요청은 `h2`, 나중 새 연결은 `h3`가 될 수 있다.

**난이도: 🟢 Beginner**

> 이 문서는 HTTP 버전 주제의 **선택 문서(entrypoint follow-up)** 다. 3분 방향 잡기가 먼저 필요하면 [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md), 버전 차이의 큰 그림부터 잡고 싶으면 [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)를 먼저 보고 다시 들어오면 된다.
>
> | 지금 상태 | 먼저 읽을 문서 | 이 문서로 돌아오는 타이밍 |
> |---|---|---|
> | 아직 H1/H2/H3 차이도 헷갈린다 | [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md) | "왜 첫 요청은 H2인데 다음은 H3지?"가 궁금해졌을 때 |
> | 버전 차이는 아는데 선택 과정이 헷갈린다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | 버전 비교 다음 단계로 ALPN/`Alt-Svc`/`fallback`을 묶어 보고 싶을 때 |
> | 이미 선택 과정이 궁금하다 | 이 문서 | `첫 요청` vs `다음 새 연결(재요청)` 흐름을 읽기 시작하면 된다 |
>
관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Alt-Svc Header Reading Micro-Note](./alt-svc-header-reading-micro-note.md)
- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기](./h3-discovery-observability-primer.md)
- [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [HTTPS / TLS 입문](../security/https-tls-beginner.md)

retrieval-anchor-keywords: browser protocol negotiation, alpn vs alt-svc, browser http version selection, http/3 basics, first request vs next request, first visit h2 repeat visit h3, 첫 요청이 왜 h2예요, first visit repeat visit confusion, alt-svc cache, alt-svc cache vs http cache, 304 vs h3 fallback, quic fallback, udp blocked h3, devtools first visit checklist, http header vs dns record

<details>
<summary>Table of Contents</summary>

- [왜 헷갈리나](#왜-헷갈리나)
- [첫 읽기 5줄 판별 카드](#첫-읽기-5줄-판별-카드)
- [용어 먼저 고정하기](#용어-먼저-고정하기)
- [먼저 구분: ALPN과 Alt-Svc는 무엇이 다른가](#먼저-구분-alpn과-alt-svc는-무엇이-다른가)
- [헷갈리면 먼저 가르기: HTTP header vs DNS record](#헷갈리면-먼저-가르기-http-header-vs-dns-record)
- [Protocol-vs-Cache Boundary Bridge](#protocol-vs-cache-boundary-bridge)
- [브라우저는 실제로 어떤 순서로 고르나](#브라우저는-실제로-어떤-순서로-고르나)
- [HTTP/1.1, HTTP/2, HTTP/3는 각각 언제 선택되나](#http11-http2-http3는-각각-언제-선택되나)
- [fallback은 언제 생기나](#fallback은-언제-생기나)
- [자주 보는 타임라인](#자주-보는-타임라인)
- [초급자용 빠른 판단표](#초급자용-빠른-판단표)
- [DevTools first-visit 3단계 체크리스트](#devtools-first-visit-3단계-체크리스트)
- [관찰 포인트](#관찰-포인트)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [꼬리질문](#꼬리질문)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 헷갈리나

브라우저는 요청마다 "버전을 다시 뽑기"보다, **연결을 만들 때 어떤 경로와 프로토콜을 쓸지 결정**한다.

그래서 입문자가 흔히 헷갈리는 장면이 생긴다.

- 첫 요청은 HTTP/2였는데 다음 새 연결(재요청)은 HTTP/3일 수 있다
- 같은 URL인데 회사망에서는 HTTP/2, 집에서는 HTTP/3일 수 있다
- 서버는 HTTP/2를 지원하는데도 어떤 구간에서는 HTTP/1.1로 내려갈 수 있다

핵심은 브라우저가 한 가지 신호만 보는 게 아니라는 점이다.

- 이미 열려 있는 연결이 있는가
- `Alt-Svc` 같은 "다음엔 다른 경로를 시도해도 된다"는 힌트가 있는가
- 새 연결을 만들 때 ALPN 협상 결과가 무엇인가
- QUIC/UDP 경로가 실제로 통하는가

## 첫 읽기 5줄 판별 카드

1. "`지금 이 연결에서 무슨 버전을 쓰나`"가 질문이면 먼저 ALPN을 떠올린다.
2. "`다음 새 연결(재요청)에서는 H3를 시도해도 되나`"가 질문이면 `Alt-Svc`나 HTTPS RR 같은 discovery 힌트를 본다.
3. 첫 요청이 `h2`고 다음 새 연결(재요청)이 `h3`면 보통은 정상 학습 패턴이지, 바로 fallback이 아니다.
4. 최종 `Protocol=h2`만 보이면 "`H3를 안 썼다`"까지는 말할 수 있지만, "`H3를 시도했다가 실패했다`"는 아직 확정이 아니다.
5. 한 줄 기억법: ALPN은 `지금 연결`, `Alt-Svc`는 `다음 연결`, fallback은 `H3 시도 후 조용히 하향`.

## 용어 먼저 고정하기

이 H3 입문 문서 묶음에서는 아래 3개 표현을 먼저 같은 뜻으로 고정한다.

| 문구 | 이 문서군에서의 뜻 | 초급자 메모 |
|---|---|---|
| `첫 요청` | 브라우저가 아직 H3 힌트를 배우기 전, 처음 보게 되는 요청 | 보통 `h2`나 `http/1.1`로 시작할 수 있다 |
| `다음 새 연결(재요청)` | `Alt-Svc`나 DNS 힌트를 알고 난 뒤, **새 connection이 다시 필요해서** 나가는 요청 | "그냥 다음 클릭"이 아니라 "새 연결이 생긴 다음 요청"에 가깝다 |
| `fallback` | H3를 시도했지만 실패해 H2/H1.1로 **조용히 내려가는 것** | 에러 화면보다 protocol 분포 변화로 더 자주 보인다 |

같이 외우면:

- `첫 요청` -> 아직 배우기 전
- `다음 새 연결(재요청)` -> 배운 뒤 새 connection에서 다시 시도
- `fallback` -> H3 시도 실패 후 조용히 내려감

### Retrieval Anchors

- `browser protocol negotiation`
- `browser HTTP version selection`
- `ALPN vs Alt-Svc`
- `HTTP/1.1 fallback`
- `HTTP/2 fallback`
- `HTTP/3 fallback`
- `first request vs next request`
- `Alt-Svc cache`
- `protocol signal vs cache signal`
- `Alt-Svc cache vs HTTP cache`
- `304 vs h3 fallback`

---

## 먼저 구분: ALPN과 Alt-Svc는 무엇이 다른가

둘은 비슷해 보이지만 역할이 다르다.

| 항목 | ALPN | `Alt-Svc` |
|---|---|---|
| 어디서 보나 | handshake 중 | HTTP 응답 header |
| 하는 일 | **이 연결에서** 어떤 애플리케이션 프로토콜을 쓸지 합의 | **다음 연결에서** 다른 프로토콜/endpoint를 시도해도 된다는 힌트 제공 |
| 주로 고르는 것 | `h2`, `http/1.1`, `h3` 같은 protocol id | `h3=":443"` 같은 대체 서비스 정보 |
| 감각 | "지금 만든 연결 위에서 무엇을 말할까?" | "다음엔 다른 길로 가도 된다" |

입문 감각으로 외우면:

- ALPN은 **현재 연결의 protocol 선택**
- `Alt-Svc`는 **미래 연결의 대체 경로 힌트**

중요한 포인트 하나 더:

- HTTP/2는 보통 TCP+TLS 연결에서 ALPN으로 `h2`를 고른다
- HTTP/3도 QUIC 안의 TLS handshake에서 ALPN으로 `h3`를 고른다
- 하지만 브라우저가 애초에 QUIC/H3를 시도할지 말지는 보통 `Alt-Svc` 같은 사전 힌트가 좌우한다

즉, `Alt-Svc`가 H3를 "직접 협상"하는 것은 아니다.
`Alt-Svc`는 H3를 시도할 이유를 알려 주고, 실제 `h3` 선택은 handshake 안의 ALPN이 맡는다.

`Alt-Svc: h3=":443"; ma=86400` 같은 값 자체를 읽는 법이 먼저 필요하면 [Alt-Svc Header Reading Micro-Note](./alt-svc-header-reading-micro-note.md)를 먼저 보고 오는 편이 빠르다.

---

## 헷갈리면 먼저 가르기: HTTP header vs DNS record

이 문서에서 가장 많이 섞이는 질문을 먼저 둘로 가른다.

> `Headers` 화면에서 본 힌트인가?
> 그러면 `Alt-Svc` 같은 **HTTP header 기반 discovery**를 먼저 본다.
>
> `dig`나 DNS trace에서 본 힌트인가?
> 그러면 HTTPS RR/SVCB 같은 **DNS record 기반 discovery**를 먼저 본다.

| 내가 본 단서 | 먼저 떠올릴 것 | 아직 섞지 말아야 할 것 |
|---|---|---|
| Response Headers의 `Alt-Svc: h3=":443"` | "다음 새 연결용 H3 후보를 HTTP 응답에서 배웠다" | 이것만 보고 현재 row의 protocol이 바로 바뀐다고 생각하지 않기 |
| DNS의 `HTTPS` record | "첫 요청 전에도 H3 시도 근거를 DNS에서 미리 알 수 있다" | 이것만 보고 실제 `h3` 성립까지 끝났다고 생각하지 않기 |
| DevTools `Protocol = h2/h3` | "이미 선택 결과가 화면에 보인다" | discovery source가 HTTP였는지 DNS였는지와 같은 질문으로 바로 합치지 않기 |

한 줄로 묶으면:

- discovery source는 "`어디서 H3 후보를 배웠나`"의 질문이다.
- protocol 선택은 "`그 후보로 실제 어떤 연결이 성립했나`"의 질문이다.

DNS 기반 discovery까지 같이 읽어야 하면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)로 바로 이어서 보면 된다.

---

## Discovery source 분기 상자: HTTP header vs DNS record

ALPN/`Alt-Svc`/fallback을 읽다가 헷갈리면, 먼저 **"어디서 H3 후보를 배웠나"**를 분리한다.

| 지금 본 증거 | discovery source 판독 | 여기서 바로 결론 내리면 안 되는 것 |
|---|---|---|
| Response Headers의 `Alt-Svc` | HTTP header에서 다음 새 연결용 H3 후보를 배웠다 | "그러니 이 row가 바로 `h3`다" |
| DNS trace의 `HTTPS` RR / `SVCB` | DNS record에서 첫 연결 전 H3 후보를 미리 알 수 있다 | "그러니 H3 handshake까지 이미 성공했다" |
| DevTools `Protocol = h2/h3` | 후보를 써 본 **결과**가 화면에 보인다 | "후보를 어디서 배웠는지까지 이 칸 하나로 확정" |

짧게 가르면:

- `Alt-Svc` 질문이면 `HTTP header 기반 discovery`
- HTTPS RR/SVCB 질문이면 `DNS record 기반 discovery`
- `Protocol` 질문이면 `실제 연결 선택 결과`

즉 초급자에게는 순서가 중요하다.

1. 먼저 discovery source를 고른다. "`HTTP header였나, DNS record였나?`"
2. 그다음 protocol 선택을 본다. "`실제로 `h3`가 성립했나?`"
3. 마지막에 fallback을 본다. "`시도했지만 `h2`/`http/1.1`로 내려왔나?`"

이 순서만 지켜도 "`Alt-Svc`를 봤으니 이미 H3다", "`DNS에 HTTPS RR이 있으니 fallback은 아니다`" 같은 혼선을 크게 줄일 수 있다.

---

## Protocol-vs-Cache Boundary Bridge

먼저 한 줄 감각부터 잡자.

- protocol 신호는 **연결 위에서 어떤 말(`h1`/`h2`/`h3`)을 할지**를 정한다.
- cache 신호는 **이전에 본 정보(대체 경로 힌트/응답 본문)를 재사용할지**를 정한다.

| 지금 궁금한 질문 | protocol 쪽 신호 | cache 쪽 신호 | 먼저 내릴 해석 |
|---|---|---|---|
| 왜 이번 요청이 `h2`/`h3`/`h1`인가? | ALPN 결과, QUIC/UDP 성공 여부 | 기존 연결 재사용 여부, `Alt-Svc` 힌트 보유 여부 | "요청 시점"보다 "연결 생성/재사용 시점"부터 본다 |
| 왜 첫 요청은 `h2`인데 다음은 `h3`인가? | 새 QUIC 연결에서 ALPN `h3` 성립 | 앞선 응답에서 배운 `Alt-Svc` cache | 보통 정상 패턴이다 (`first h2 -> next h3`) |
| 왜 갑자기 매우 빠르거나 `304`가 보이나? | 기존 프로토콜 유지인 경우가 많음 | HTTP cache hit 또는 revalidation(`ETag`, `Last-Modified`) | cache 동작과 protocol fallback을 분리해서 본다 |

자주 섞이는 오해:

- `Alt-Svc` cache와 HTTP 응답 cache는 같은 캐시가 아니다.
- `304 Not Modified`는 콘텐츠 재검증 결과지, `h3 -> h2` fallback 신호가 아니다.
- `h3 -> h2` fallback이 있어도 HTTP cache hit/miss와 1:1로 대응하지 않는다.
- DevTools에서 `h1`과 `http/1.1`이 섞여 보여도 첫 판독은 같은 H1 버킷으로 읽는다.

입문자용 한 줄 역링크:

- `304는 캐시 신호`라는 감각을 먼저 굳히고 싶다면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)의 `304와 프로토콜 fallback은 다른 질문이다 (bridge)` 절부터 이어서 보면 된다.

관련 흐름을 이어서 보면:

- `Alt-Svc` hint 관점: [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- HTTP response cache 관점: [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- DevTools 판독 관점: [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)

---

## 브라우저는 실제로 어떤 순서로 고르나

세부 타이머와 재시도 정책은 브라우저마다 다르지만, beginner용 큰 흐름은 아래처럼 잡으면 된다.

### 1. 먼저 기존 연결을 재사용할 수 있는지 본다

브라우저는 이미 열려 있고 건강한 연결이 있으면 그 연결을 먼저 쓰려 한다.

- 이미 H2 연결이 열려 있으면 새 요청도 그 H2 연결로 갈 수 있다
- 그래서 `Alt-Svc`를 방금 배웠더라도 **같은 응답이 갑자기 H3로 바뀌는 것처럼 생각하면 안 된다**
- 버전 선택은 종종 "요청 시점"이 아니라 "새 연결 생성 시점"에 일어난다

같은 연결을 다른 origin까지 확장해서 공유하는 규칙은 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)에서 이어서 보면 된다.

### 2. 새 연결이 필요하면, H3로 갈 근거가 있는지 본다

브라우저가 이전 응답에서 `Alt-Svc`를 캐시했다면:

- "이 origin은 다음엔 H3도 시도할 수 있구나"라고 기억한다
- 이후 새 연결이 필요할 때 QUIC/UDP 기반 H3 경로를 시도할 수 있다

이 단계가 없으면 많은 경우 첫 연결은 그냥 TCP+TLS로 간다.

참고로 최신 browser/CDN 조합에서는 `Alt-Svc` 말고 HTTPS RR/SVCB 같은 DNS 힌트로 H3 가능성을 먼저 아는 경우도 있다.
이 문서는 beginner용 기본 흐름인 **ALPN + `Alt-Svc` mental model**에 집중하고, DNS 기반 discovery가 coalescing 입력으로 이어지는 다리는 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)에서 이어서 본다.

### 3. H3를 시도하면, 그 안에서 다시 ALPN으로 `h3`를 맞춘다

QUIC 경로가 열리면 handshake 안에서 다시 protocol id를 맞춘다.

- client는 `h3`를 제안한다
- server가 받아들이면 HTTP/3를 쓴다
- QUIC 자체가 실패하거나 `h3`가 성립하지 않으면 fallback된다

### 4. H3를 못 쓰거나 아직 시도하지 않았다면 TCP+TLS로 간다

이 경우 브라우저는 보통 ALPN으로 다음 둘을 제안한다.

- `h2`
- `http/1.1`

서버가 `h2`를 고르면 HTTP/2, 그렇지 않으면 보통 HTTP/1.1로 간다.

### 5. 응답에서 `Alt-Svc`를 배우면 다음 연결의 선택지가 바뀐다

그래서 실제 현장에서는 이런 현상이 흔하다.

- 첫 요청: HTTP/2
- 응답 header: `Alt-Svc: h3=":443"; ma=86400`
- 다음 새 연결: HTTP/3 시도

즉 `Alt-Svc`는 보통 **같은 응답의 프로토콜을 바꾸는 장치가 아니라, 이후 연결의 선택지를 넓히는 장치**다.

---

## HTTP/1.1, HTTP/2, HTTP/3는 각각 언제 선택되나

### HTTP/1.1

브라우저가 HTTP/1.1을 쓰는 대표 경우는:

- TLS ALPN에서 `h2`가 성립하지 않았다
- 서버나 LB가 HTTP/2를 지원하지 않는다
- 중간 TLS 종료 지점이 HTTP/1.1만 처리한다
- plaintext HTTP라서 브라우저가 일반적인 웹 경로에서 그냥 HTTP/1.1을 쓴다

초보자 관점에서는 "더 좋은 걸 못 써서 맨 아래로 떨어진 것"처럼 보이기 쉽지만, 호환성 때문에 의도적으로 HTTP/1.1을 유지하는 경우도 많다.

### HTTP/2

브라우저가 HTTP/2를 쓰는 대표 경우는:

- HTTPS 연결을 새로 만들었다
- ALPN에서 `h2`가 성공했다
- 아직 H3 사전 힌트가 없거나, H3를 시도할 이유가 없다
- H3를 시도했지만 실패해서 TCP+TLS 경로로 돌아왔다

실무 감각으로는 HTTP/2가 "현대 웹의 기본 경로"로 보이는 경우가 많다.

### HTTP/3

브라우저가 HTTP/3를 쓰는 대표 경우는:

- 브라우저가 해당 origin의 H3 가능성을 이미 알고 있다
- `Alt-Svc` cache 같은 사전 정보가 있다
- QUIC/UDP 경로가 실제로 통한다
- QUIC handshake 안에서 `h3`가 성립한다

즉 H3는 단순히 "서버가 지원하니 무조건 바로 붙는 최신 버전"이 아니다.
브라우저가 **시도할 근거와 성공할 경로**를 둘 다 가져야 한다.

---

## fallback은 언제 생기나

아래 표가 beginner에게 가장 실용적인 감각이다.

| 상황 | 브라우저가 실제로 하는 일 | 결과 |
|---|---|---|
| 첫 방문이라 H3 정보를 아직 모른다 | TCP+TLS를 열고 ALPN으로 `h2`/`http/1.1` 협상 | 보통 H2, 아니면 H1.1 |
| `Alt-Svc`는 배웠지만 UDP 443이 막혀 있다 | H3 시도 후 실패, TCP+TLS 경로로 되돌아감 | H2 또는 H1.1 |
| 서버/LB가 `h2`를 제안받아도 못 받는다 | ALPN에서 `h2` 불성립 | H1.1 |
| 이미 건강한 H2 연결이 열려 있다 | 새로 H3를 만들지 않고 기존 H2 연결 재사용 | 계속 H2 |
| H3를 여러 번 실패했다 | 브라우저가 한동안 H3 시도를 줄이거나 멈춤 | H2/H1.1 쪽으로 backoff |

여기서 중요한 점:

- fallback은 보통 "에러 화면"보다 "조용한 하향 선택"으로 보인다
- 사용자는 실패보다 "조금 느림"만 느낄 수 있다
- 그래서 protocol 분포를 안 보면 H3 실패를 놓치기 쉽다

---

## 자주 보는 타임라인

### 타임라인 1: 평범한 첫 접속

1. 브라우저는 아직 이 사이트의 H3 정보를 모른다.
2. TCP+TLS 연결을 연다.
3. ALPN으로 `h2`, `http/1.1`을 제안한다.
4. 서버가 `h2`를 고른다.
5. 첫 요청은 HTTP/2로 끝난다.

### 타임라인 2: 다음 접속에서 H3로 올라감

1. 이전 응답에 `Alt-Svc: h3=":443"; ma=86400`가 있었다.
2. 브라우저가 이 힌트를 cache에 기억한다.
3. 다음 새 연결에서 QUIC/H3를 시도한다.
4. QUIC 안의 handshake에서 ALPN `h3`가 성립한다.
5. 이번에는 HTTP/3를 쓴다.

### 타임라인 3: 회사망에서 다시 H2로 내려감

1. 브라우저는 H3를 시도할 근거를 이미 알고 있다.
2. 하지만 회사망이나 프록시가 UDP 443을 막는다.
3. QUIC/H3 시도가 실패하거나 timeout 난다.
4. 브라우저는 TCP+TLS로 fallback한다.
5. ALPN 결과에 따라 HTTP/2 또는 HTTP/1.1을 쓴다.

그래서 같은 URL이라도:

- 집에서는 HTTP/3
- 회사망에서는 HTTP/2

가 충분히 가능하다.

### 타임라인 4: `첫 요청` vs `다음 새 연결(재요청)` trace를 한 번에 읽는 예시

같은 URL `https://shop.example.com`을 DevTools에서 연속으로 본다고 가정하자.

| 순서 | 타임라인 라벨 | 관찰한 단서 | 초급자 해석 |
|---|---|---|---|
| 1 | 첫 요청 | `Protocol = h2`, response header에 `Alt-Svc: h3=":443"; ma=86400` | "첫 연결은 ALPN으로 h2가 되었고, 다음 새 연결용 H3 힌트를 지금 배웠다" |
| 2 | 다음 새 연결(재요청) | `Protocol = h3` | "새 connection에서 QUIC+ALPN `h3`가 성립했다" |
| 3 | 기존 연결 재사용 | 계속 `Protocol = h3` 또는 기존 `h2`로 유지 | "요청마다 버전을 새로 뽑는 게 아니라, 연결 재사용이 먼저 작동한다" |

같은 장면을 더 짧게 타임라인으로 접으면 아래처럼 읽는다.

| 시점 | protocol | cache 쪽에서 바뀐 것 |
|---|---|---|
| 첫 HTML 요청 | `h2` | HTTP cache 의미는 그대로이고, `Alt-Svc` cache만 cold -> warm |
| 몇 초 뒤 새 이미지 요청 | `h3` | HTTP cache 규칙은 그대로, H3 힌트를 배운 새 connection만 생김 |

여기서 핵심은 "`h2`였다가 `h3`가 됐으니 캐시 의미가 바뀌었다"가 아니라는 점이다.

- 바뀐 것은 `Alt-Svc` 힌트를 배운 상태다.
- 안 바뀐 것은 `Cache-Control`, `ETag`, `304`로 읽는 HTTP cache semantics다.

핵심은 이 한 줄이다.

## 자주 보는 타임라인 (계속 2)

- `Alt-Svc`는 보통 `첫 요청` 응답에서 배우고, `다음 새 연결(재요청)`에서 영향이 보인다.

---

## 초급자용 빠른 판단표

| 지금 보이는 장면 | 첫 해석 | 먼저 확인할 것 |
|---|---|---|
| 첫 요청은 `h2`, 다음 새 연결(재요청)은 `h3` | `Alt-Svc`를 배운 뒤 새 connection에서 H3를 시도한 정상 패턴 | response의 `Alt-Svc`와 "새 connection이 생긴 시점" |
| `Alt-Svc`가 보이는데 계속 `h2` | 기존 H2 connection 재사용 또는 UDP 경로 이슈 가능성 | 기존 socket 재사용 여부, 네트워크(집/회사망) 비교 |
| 집에서는 `h3`, 회사에서는 `h2` | UDP 443 경로 차이로 H3 fallback 가능성 | 같은 브라우저/같은 URL로 네트워크만 바꿔 분포 비교 |
| 가끔 `http/1.1`까지 내려감 | ALPN에서 `h2`가 성립하지 않았을 수 있음 | TLS 종료 지점/LB 설정, `h2` 지원 여부 |

이 표는 "왜 버전이 달라졌는가"를 한 번에 단정하지 않고, connection 재사용과 fallback을 먼저 분리하게 만든다.

---

## DevTools first-visit 3단계 체크리스트

초급자는 `first h2 -> next h3`를 한 번에 증명하려고 하기보다, **첫 row에서 배움 -> 다음 row에서 새 연결 -> 그 새 연결에서 h3** 순서로 본다.

- "`이 패턴을 어디서 확인하나요?`"가 바로 다음 질문이면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)로 가면 된다. 이 문서는 lifecycle을, 그 문서는 DevTools/`dig`/`curl` 확인 순서를 맡는다.

### 1. 첫 row에서 `Protocol`과 `Alt-Svc`를 같이 본다

- Network 탭에서 같은 origin의 첫 문서를 하나 고른다.
- `Protocol`이 `h2`나 `http/1.1`인지 본다.
- Response Headers에 `Alt-Svc: h3=...`가 있는지 본다.

이 장면의 뜻:

- "지금 row는 아직 H3가 아니라도 괜찮다"
- "브라우저가 다음 새 연결용 H3 힌트를 지금 배웠다"

### 2. 다음 row가 정말 `새 연결`인지 먼저 확인한다

같은 origin에서 이어진 row를 볼 때는 "다음 요청"보다 "다음 새 연결"인지가 더 중요하다.

| DevTools에서 볼 것 | 이렇게 읽는다 |
|---|---|
| `Connection ID`가 바뀜 | 기존 연결 재사용이 아니라 새 연결 후보 |
| `Remote Address`가 같거나 달라도 됨 | 주소보다 먼저 "새 connection인가"를 본다 |
| 바로 다음 클릭인데도 `Connection ID`가 안 바뀜 | 아직 기존 H2 연결을 재사용 중일 수 있다 |

초급자용 한 줄:

- `Alt-Svc`를 배웠다고 바로 다음 row가 H3여야 하는 것은 아니다.
- 기존 H2 연결을 계속 쓰면 warm 상태여도 화면은 계속 `h2`일 수 있다.

### 3. 새 연결 row에서 `Protocol = h3`가 보이면 `first h2 -> next h3`로 읽는다

아래 3칸이 연결되면 초급자 판독은 끝난다.

| 순서 | DevTools 단서 | 초급자 해석 |
|---|---|---|
| 첫 row | `Protocol = h2` + response header `Alt-Svc: h3=...` | H3 힌트를 배운 첫 방문 |
| 다음 새 연결 row | `Connection ID` 변경 | 이제 새 길을 시도할 타이밍 |
| 그 row의 protocol | `Protocol = h3` | `first h2 -> next h3` 정상 관찰 완료 |

만약 새 연결 row에서도 계속 `h2`라면 먼저 두 가지만 의심하면 된다.

- 아직 QUIC/UDP 경로를 못 써서 H3가 fallback됐을 수 있다
- 브라우저가 보수적으로 계속 H2를 선택했을 수 있다

## DevTools first-visit 3단계 체크리스트 (계속 2)

이 경우 lifecycle 쪽 confusion이면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), 관측 절차 자체가 더 필요하면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)로 이어서 보면 된다.

---

## 관찰 포인트

브라우저나 운영 환경을 볼 때 아래를 같이 보면 좋다.

- DevTools의 protocol column에서 `h1`, `h2`, `h3`가 어떻게 보이는가
- 첫 요청과 다음 새 연결(재요청)의 protocol이 다른가
- response header에 `Alt-Svc`가 보이는가
- 회사망, 모바일망, 집 Wi-Fi에서 protocol 분포가 달라지는가

간단한 확인 감각:

```bash
curl -I https://example.com
curl -I --http2 https://example.com
curl -I --http3 https://example.com
```

헤더에서 특히 볼 것:

```text
Alt-Svc: h3=":443"; ma=86400
```

이 값은 "지금 응답이 이미 H3"라는 뜻이 아니라, **이후 새 연결에서 H3를 시도할 수 있다**는 힌트에 가깝다.

---

## 자주 헷갈리는 포인트

- `Alt-Svc`는 보통 **다음 새 connection** 힌트지, 현재 응답의 protocol 즉시 전환 스위치가 아니다.
- ALPN은 **현재 연결**에서 쓸 protocol(`h2`/`h3`/`http/1.1`)을 handshake 중에 정한다.
- `304`를 보면 먼저 "캐시 재검증이 있었구나"라고 읽고, 그다음 `Protocol` 열에서 `h2`/`h3`를 따로 본다.
- fallback은 자주 "에러 화면"이 아니라 조용한 하향 선택(`h3` -> `h2`)으로 보인다.
- `다음 새 연결(재요청)`은 항상 "다음 클릭"과 같지 않다. 기존 연결 재사용이면 버전 선택보다 connection 재사용이 먼저 보인다.

---

## 꼬리질문

> Q: HTTP/3는 ALPN이 아니라 `Alt-Svc`로만 정해지나요?
> 핵심: 아니다. `Alt-Svc`는 H3를 시도할 이유를 알려 주고, 실제 `h3` 선택은 QUIC handshake 안의 ALPN이 맡는다.

> Q: `Alt-Svc`를 받으면 바로 그 응답부터 H3로 바뀌나요?
> 핵심: 보통 아니다. 대개 이후 새 연결부터 영향을 준다.

> Q: H3가 실패하면 항상 HTTP/2로만 내려가나요?
> 핵심: 대개 H2가 먼저 후보지만, `h2`가 안 되면 HTTP/1.1까지 내려갈 수 있다.

> Q: 브라우저가 매 요청마다 버전을 완전히 새로 고르나요?
> 핵심: 보통은 먼저 기존 연결 재사용 여부를 본다. 그래서 버전 선택은 연결 생성 시점에 더 가깝다.

## 다음에 이어서 볼 문서

- `304는 캐시 신호`라는 감각부터 단단히 잡으려면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `첫 방문은 h2인데 repeat visit은 h3인가요?`, `같은 탭 새로고침인데 왜 계속 h2인가요?`처럼 **첫 방문/반복 방문 confusion**이 핵심이면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)로 먼저 점프한다.
- `첫 요청`/`다음 새 연결(재요청)`, `ma` 만료, stale hint를 더 단단히 잡으려면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- DNS HTTPS RR/SVCB와 `Alt-Svc` discovery 차이를 이어서 보려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- H3 hint는 있는데 실제로 H2/H1.1로 내려가는 운영 해석을 하려면 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
- 이미 열린 H2/H3 connection을 다른 origin과 공유해도 되는지 보려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)

## 한 줄 정리

브라우저는 먼저 재사용할 연결이 있는지 보고, H3를 시도할 근거가 있으면 QUIC+ALPN으로 `h3`를 맞추고, 그렇지 않으면 TCP+TLS ALPN으로 `h2` 또는 `http/1.1`을 고른다. fallback은 이 과정 어디서든 조용히 일어나며, 그래서 `첫 요청`과 `다음 새 연결(재요청)`의 버전이 달라질 수 있다.
