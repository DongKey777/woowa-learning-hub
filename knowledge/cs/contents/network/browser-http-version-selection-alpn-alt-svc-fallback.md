# 브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문

> 브라우저가 실제로 언제 HTTP/1.1, HTTP/2, HTTP/3를 고르고, 왜 첫 요청과 다음 요청의 버전이 달라질 수 있는지 ALPN과 `Alt-Svc` 중심으로 설명하는 beginner primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
> - [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [QUIC Version Negotiation, Fallback Behavior](./quic-version-negotiation-fallback.md)

retrieval-anchor-keywords: browser protocol negotiation, browser HTTP version selection, ALPN vs Alt-Svc, HTTP/1.1 fallback, HTTP/2 fallback, HTTP/3 fallback, browser protocol fallback, first request vs next request, TLS ALPN, Alt-Svc cache, h3 upgrade, h2 downgrade, UDP blocked H3, QUIC fallback, browser chooses h2 or http/1.1, browser chooses h3

<details>
<summary>Table of Contents</summary>

- [왜 헷갈리나](#왜-헷갈리나)
- [먼저 구분: ALPN과 Alt-Svc는 무엇이 다른가](#먼저-구분-alpn과-alt-svc는-무엇이-다른가)
- [브라우저는 실제로 어떤 순서로 고르나](#브라우저는-실제로-어떤-순서로-고르나)
- [HTTP/1.1, HTTP/2, HTTP/3는 각각 언제 선택되나](#http11-http2-http3는-각각-언제-선택되나)
- [fallback은 언제 생기나](#fallback은-언제-생기나)
- [자주 보는 타임라인](#자주-보는-타임라인)
- [관찰 포인트](#관찰-포인트)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 헷갈리나

브라우저는 요청마다 "버전을 다시 뽑기"보다, **연결을 만들 때 어떤 경로와 프로토콜을 쓸지 결정**한다.

그래서 입문자가 흔히 헷갈리는 장면이 생긴다.

- 첫 요청은 HTTP/2였는데 다음 요청은 HTTP/3일 수 있다
- 같은 URL인데 회사망에서는 HTTP/2, 집에서는 HTTP/3일 수 있다
- 서버는 HTTP/2를 지원하는데도 어떤 구간에서는 HTTP/1.1로 내려갈 수 있다

핵심은 브라우저가 한 가지 신호만 보는 게 아니라는 점이다.

- 이미 열려 있는 연결이 있는가
- `Alt-Svc` 같은 "다음엔 다른 경로를 시도해도 된다"는 힌트가 있는가
- 새 연결을 만들 때 ALPN 협상 결과가 무엇인가
- QUIC/UDP 경로가 실제로 통하는가

### Retrieval Anchors

- `browser protocol negotiation`
- `browser HTTP version selection`
- `ALPN vs Alt-Svc`
- `HTTP/1.1 fallback`
- `HTTP/2 fallback`
- `HTTP/3 fallback`
- `first request vs next request`
- `Alt-Svc cache`

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
이 문서는 beginner용 기본 흐름인 **ALPN + `Alt-Svc` mental model**에 집중한다.

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

---

## 관찰 포인트

브라우저나 운영 환경을 볼 때 아래를 같이 보면 좋다.

- DevTools의 protocol column에서 `h1`, `h2`, `h3`가 어떻게 보이는가
- 첫 요청과 다음 요청의 protocol이 다른가
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

## 꼬리질문

> Q: HTTP/3는 ALPN이 아니라 `Alt-Svc`로만 정해지나요?
> 핵심: 아니다. `Alt-Svc`는 H3를 시도할 이유를 알려 주고, 실제 `h3` 선택은 QUIC handshake 안의 ALPN이 맡는다.

> Q: `Alt-Svc`를 받으면 바로 그 응답부터 H3로 바뀌나요?
> 핵심: 보통 아니다. 대개 이후 새 연결부터 영향을 준다.

> Q: H3가 실패하면 항상 HTTP/2로만 내려가나요?
> 핵심: 대개 H2가 먼저 후보지만, `h2`가 안 되면 HTTP/1.1까지 내려갈 수 있다.

> Q: 브라우저가 매 요청마다 버전을 완전히 새로 고르나요?
> 핵심: 보통은 먼저 기존 연결 재사용 여부를 본다. 그래서 버전 선택은 연결 생성 시점에 더 가깝다.

## 한 줄 정리

브라우저는 먼저 재사용할 연결이 있는지 보고, H3를 시도할 근거가 있으면 QUIC+ALPN으로 `h3`를 맞추고, 그렇지 않으면 TCP+TLS ALPN으로 `h2` 또는 `http/1.1`을 고른다. fallback은 이 과정 어디서든 조용히 일어나며, 그래서 첫 요청과 다음 요청의 버전이 달라질 수 있다.
