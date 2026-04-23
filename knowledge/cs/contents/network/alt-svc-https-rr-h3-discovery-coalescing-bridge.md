# Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge

> 브라우저가 H3 endpoint를 언제 HTTP 응답의 `Alt-Svc`로 배우고, 언제 DNS의 HTTPS RR/SVCB로 먼저 아는지, 그리고 이 discovery가 왜 coalescing 판단의 입력일 뿐인지 이어 주는 beginner bridge

**난이도: 🟢 Beginner**

> 관련 문서:
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [DNS 기초](./dns-basics.md)

retrieval-anchor-keywords: Alt-Svc vs HTTPS RR, HTTPS RR, HTTPS resource record, SVCB, browser H3 discovery, H3 endpoint discovery, DNS H3 hint, Alt-Svc cache, discovery before coalescing, Alt-Svc endpoint authority, alternative service authority, HTTP/3 no ORIGIN frame, H3 discovery bridge, HTTPS RR coalescing, SVCB coalescing, first request H3, browser service binding, alt-authority, authoritative H3 endpoint

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [용어를 짧게 정리하면](#용어를-짧게-정리하면)
- [Alt-Svc와 HTTPS RR는 무엇이 다른가](#alt-svc와-https-rr는-무엇이-다른가)
- [브라우저 타임라인에 끼워 넣어 보면](#브라우저-타임라인에-끼워-넣어-보면)
- [discovery와 coalescing은 어떻게 이어지나](#discovery와-coalescing은-어떻게-이어지나)
- [작은 예시로 보기](#작은-예시로-보기)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

입문자가 자주 섞는 질문은 사실 둘이다.

- 브라우저는 **H3로 어디를 시도할지** 언제 아는가
- 이미 열린 H2/H3 connection을 **다른 origin과 같이 써도 되는지** 언제 판단하는가

이 둘은 같은 단계가 아니다.

- `Alt-Svc`와 HTTPS RR/SVCB는 주로 **발견(discovery)** 문제를 푼다
- connection coalescing은 그다음 **재사용 허가(permission)** 문제를 푼다

즉 먼저 "H3로 갈 후보 endpoint"를 알아야 하고, 그다음에야 "이 connection을 다른 origin까지 묶어도 되나"를 따질 수 있다.

### Retrieval Anchors

- `Alt-Svc vs HTTPS RR`
- `HTTPS RR`
- `SVCB`
- `browser H3 discovery`
- `discovery before coalescing`
- `DNS H3 hint`

---

## 먼저 잡는 mental model

한 줄씩만 잡으면 이렇게 기억하면 된다.

- `Alt-Svc`: 서버가 **HTTP 응답으로** "다음 연결은 저 H3 endpoint도 시도해 봐"라고 알려 준다
- HTTPS RR: DNS가 **HTTP 응답보다 먼저** "이 이름은 이런 웹 endpoint/H3 힌트를 갖고 있다"라고 알려 준다
- coalescing: 이미 열린 connection이 생긴 뒤, "이 연결을 다른 origin도 같이 써도 안전한가"를 본다

즉 흐름은 보통 이렇게 이어진다.

```text
DNS 또는 이전 응답에서 H3 후보 endpoint를 배움
          ↓
QUIC + TLS(ALPN)로 실제 h3가 성립하는지 확인
          ↓
이미 열린 H3 connection이 생김
          ↓
그 connection을 다른 origin도 같이 써도 되는지 coalescing 판단
```

핵심은 discovery가 곧 permission은 아니라는 점이다.

- H3 endpoint를 아는 것
- 그 H3 connection이 다른 origin에도 authoritative한 것

이 둘은 별도 판단이다.

---

## 용어를 짧게 정리하면

| 용어 | 뜻 | 입문 감각 |
|---|---|---|
| `Alt-Svc` | HTTP 응답 header의 alternative service 힌트 | "이번에 응답한 서버가 다음에는 다른 endpoint도 시도해 보라고 말해 준다" |
| HTTPS RR | 웹용 DNS resource record | "DNS 단계에서 이 이름의 웹 service binding 힌트를 미리 준다" |
| `SVCB` | service binding record family | HTTPS RR은 웹 트래픽에서 자주 보는 SVCB 계열이라고 보면 된다 |
| ALPN | handshake 안에서 실제 protocol id를 맞추는 절차 | `h2`, `h3`, `http/1.1` 중 지금 연결에서 무엇을 쓸지 정한다 |
| coalescing | 여러 origin이 한 connection을 공유하는 판단 | "이 연결을 다른 간판 요청에도 같이 써도 되나?" |

입문 감각으로는:

- `SVCB`는 record family 이름
- 웹 브라우징에서는 HTTPS RR을 주로 떠올리면 된다

---

## Alt-Svc와 HTTPS RR는 무엇이 다른가

둘 다 H3 discovery에 쓰일 수 있지만, 들어오는 타이밍이 다르다.

| 항목 | `Alt-Svc` | HTTPS RR |
|---|---|---|
| 어디서 배우나 | HTTP 응답 header | DNS 응답 |
| 언제 배우나 | 보통 **첫 HTTP 응답 이후** | 보통 **첫 HTTP 요청 전** |
| beginner 감각 | "이번 서버가 다음엔 이 대체 경로도 써 보라" | "DNS가 이 이름의 웹 연결 힌트를 먼저 준다" |
| 첫 방문 H3에 미치는 영향 | 대개 바로는 약하고, 다음 연결에 더 잘 반영 | 첫 방문에서도 H3 시도 근거가 될 수 있음 |
| 실제 `h3` 확정 | QUIC handshake 안의 ALPN | QUIC handshake 안의 ALPN |

여기서 가장 중요한 줄은 마지막 줄이다.

- `Alt-Svc`가 `h3`를 직접 협상하지는 않는다
- HTTPS RR도 `h3`를 직접 협상하지는 않는다
- 실제 `h3` 성립은 handshake 안의 ALPN이 맡는다

둘은 모두 "시도할 후보를 알려 주는 힌트"에 가깝다.

---

## 브라우저 타임라인에 끼워 넣어 보면

### 경우 1: HTTPS RR이 없고 `Alt-Svc`로 나중에 배움

1. 브라우저는 DNS에서 일반 주소 정보만 얻는다.
2. 아직 H3 candidate를 확실히 모르니 TCP+TLS로 가기 쉽다.
3. ALPN 결과로 첫 요청이 H2가 된다.
4. 응답에서 `Alt-Svc: h3=":443"` 같은 값을 배운다.
5. 다음에 새 connection이 필요할 때 H3를 시도할 수 있다.

이 경우 입문자가 자주 보는 장면이 바로:

- 첫 요청은 H2
- 다음 요청 또는 다음 접속은 H3

다.

### 경우 2: HTTPS RR로 먼저 배워서 첫 요청부터 H3를 시도함

1. 브라우저는 DNS에서 HTTPS RR을 받는다.
2. "이 origin은 H3 가능성이 있구나"라는 힌트를 먼저 안다.
3. 첫 HTTP 응답을 보기 전부터 QUIC/H3를 시도할 근거가 생긴다.
4. QUIC handshake와 ALPN `h3`가 성공하면 첫 요청부터 H3가 된다.

즉 beginner 관점에서:

- `Alt-Svc`는 **응답을 받고 나서 배우는 경로**
- HTTPS RR는 **응답 전에 DNS에서 먼저 배우는 경로**

라고 잡으면 충분하다.

### 경우 3: 둘 다 있어도 fallback은 여전히 가능하다

아래 상황이면 discovery 힌트가 있어도 H3가 반드시 되지는 않는다.

- UDP 443이 막혀 있다
- 브라우저 policy가 H3 시도를 잠시 줄인다
- edge 설정과 실제 QUIC listener가 어긋난다

즉 "알고 있다"와 "성공한다"는 또 다르다.

---

## discovery와 coalescing은 어떻게 이어지나

이 문서의 핵심 bridge는 아래 표다.

| 단계 | 브라우저의 질문 | 주로 보는 것 |
|---|---|---|
| discovery | H3로 어디를 시도하지? | HTTPS RR, `Alt-Svc`, 이전 cache |
| handshake | 이 연결에서 실제로 `h3`가 되나? | QUIC 경로, TLS, ALPN |
| coalescing | 이미 열린 이 H3 connection을 다른 origin도 같이 써도 되나? | certificate, endpoint, authority, routing, `421` |

즉 coalescing은 **H3를 어떻게 찾았는가**와 완전히 분리되지는 않지만, 같은 문제도 아니다.

- discovery는 connection 후보를 만든다
- coalescing은 그 connection의 공유 범위를 판단한다

그래서 아래 둘은 다른 문장이다.

- "브라우저가 `www.example.com`의 H3 endpoint를 안다"
- "브라우저가 그 H3 connection을 `static.example.com`에도 써도 된다고 본다"

두 번째 문장에는 아직 certificate, authoritative endpoint, routing, `421` 같은 검사가 더 남아 있다.

특히 H3에서 H2의 `ORIGIN` frame 없이 이 검사들을 어떻게 가드레일로 묶는지는 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)에서 이어서 보면 된다.

---

## 작은 예시로 보기

### 예시 1: `Alt-Svc`가 먼저 보이는 전형적인 흐름

- `https://www.example.com` 첫 접속은 H2
- 응답에서 `Alt-Svc: h3=":443"`를 받음
- 다음 접속에서 H3 connection 생성
- 그 뒤 `static.example.com` 요청이 나올 때 coalescing 조건을 따로 확인

여기서 중요한 점:

- `Alt-Svc`는 H3 후보를 알려 줌
- `static`까지 같은 connection을 쓰는지는 별도 판단

### 예시 2: HTTPS RR 덕분에 첫 요청부터 H3

- DNS가 `www.example.com`에 대한 HTTPS RR을 줌
- 브라우저가 첫 요청부터 H3를 시도
- H3 connection은 빨리 생김
- 하지만 `api.example.com`을 같은 connection에 태울지는 cert/routing을 다시 봐야 함

즉 HTTPS RR이 있어도 "cross-origin reuse 허가"가 자동으로 따라오지는 않는다.

### 예시 3: discovery는 맞았지만 coalescing은 거절됨

- 브라우저는 H3 endpoint를 잘 찾아 연결도 성공
- 그런데 `admin.example.com`은 별도 보안 경계라 같은 connection을 쓰면 안 됨
- 서버가 `421 Misdirected Request`로 거절하거나 브라우저가 보수적으로 새 connection을 엶

이 장면이 바로 "discovery 성공 != coalescing 성공"의 대표 예다.

---

## 자주 헷갈리는 포인트

### `Alt-Svc`와 HTTPS RR는 경쟁 관계인가

아니다.

- 둘 다 함께 존재할 수 있다
- 다만 브라우저가 배우는 타이밍이 다르다

### HTTPS RR이 있으면 무조건 첫 요청부터 H3인가

아니다.

- 브라우저 구현
- 네트워크 정책
- UDP 경로 상태

에 따라 H2/H1.1로 fallback될 수 있다.

### H3 endpoint를 알면 coalescing도 자동인가

아니다.

coalescing에는 여전히 아래가 필요하다.

- certificate가 새 origin도 커버하는가
- endpoint가 그 origin에도 authoritative한가
- routing이 실제로 맞는가

### `Alt-Svc`나 HTTPS RR이 다른 host를 가리키면 바로 cross-origin 공유 허가인가

아니다.

그건 "어디를 시도할지"에 대한 힌트일 뿐이고, 그 connection을 다른 origin과 공유하는지는 별도다.

### `SVCB`와 HTTPS RR는 완전히 다른 기술인가

입문 단계에서는 이렇게 기억하면 된다.

- `SVCB`는 큰 우산 이름
- HTTPS RR은 웹 브라우징에서 자주 보는 그 계열의 한 형태

---

## 다음에 이어서 볼 문서

- discovery와 fallback 큰 흐름을 먼저 다지려면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- 여러 origin이 한 H2/H3 connection을 공유하는 조건까지 이어 보려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- 잘못된 공유를 `421`과 `ORIGIN` frame으로 어떻게 제어하는지 보려면 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- H3가 실제 운영에서 왜 조용히 downgrade되는지 보려면 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## 한 줄 정리

`Alt-Svc`와 HTTPS RR/SVCB는 브라우저가 H3 endpoint를 **언제, 어디서 배우는지**를 설명하고, connection coalescing은 그렇게 얻은 H3 connection을 **다른 origin도 같이 써도 되는지**를 설명한다. discovery와 공유 허가는 이어지지만 같은 단계는 아니다.
