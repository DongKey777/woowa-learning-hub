# Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge

> 브라우저가 H3 endpoint를 언제 HTTP 응답의 `Alt-Svc`로 배우고, 언제 DNS의 HTTPS RR/SVCB로 먼저 아는지, 그리고 이 discovery가 왜 coalescing 판단의 입력일 뿐인지 이어 주는 beginner bridge
> 한 줄 요약: `Alt-Svc`는 첫 응답 뒤에 배워 다음 새 연결에서 H3가 잘 보이고, HTTPS RR은 첫 요청 전에 배워 첫 요청부터 바로 H3일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)
- [Stale HTTPS RR H3 Fallback Primer](./stale-https-rr-h3-fallback-primer.md)
- [브라우저 DNS / TLS / 인증서 흐름 입문](../security/browser-dns-tls-certificate-flow-primer.md)

retrieval-anchor-keywords: alt-svc vs https rr, https rr, svcb, h3 discovery, first request h3, first request h2 next h3, alt-svc timeline, https rr timeline, discovery before coalescing, dns h3 hint, beginner h3 primer, what is alt-svc

## 헷갈리면 이 문장으로 먼저 가르기

- 처음 배우는데 "`왜 첫 요청은 h2인데 다음은 h3예요?`"면 `Alt-Svc` 쪽부터 본다.
- 처음 배우는데 "`왜 첫 요청부터 바로 h3일 수도 있나요?`"면 HTTPS RR 쪽부터 본다.
- 질문이 "`그 H3 endpoint를 어디서 배웠나`"면 이 문서에서 discovery를 먼저 본다.
- 질문이 "`이 힌트가 어느 origin의 메모인가`"면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)로 간다.
- 질문이 "`DNS TTL과 Alt-Svc `ma`가 어긋나면 first visit과 repeat visit이 왜 달라지나`"면 [Alt-Svc vs HTTPS RR Freshness Bridge](./alt-svc-vs-https-rr-freshness-bridge.md)로 간다.
- 질문이 "`DNS의 예전 H3 힌트를 믿고 갔다가 왜 `421`도 없이 `h2`로 끝나나`"면 [Stale HTTPS RR H3 Fallback Primer](./stale-https-rr-h3-fallback-primer.md)로 간다.
- 질문이 "`이미 열린 connection을 다른 origin에도 같이 써도 되나`"면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)로 간다.

## 첫 읽기 5줄 판별 카드

1. HTTP 응답 header에서 본 힌트면 `Alt-Svc`, DNS record에서 본 힌트면 HTTPS RR/SVCB부터 떠올린다.
2. `Alt-Svc`는 보통 `첫 응답 뒤 -> 다음 새 연결(재요청)`에 더 잘 반영된다.
3. HTTPS RR은 `첫 요청 전`에도 H3 시도 근거가 될 수 있지만, 실제 성공은 QUIC/TLS/ALPN이 정한다.
4. discovery 힌트를 배운 것과 다른 origin까지 같은 connection을 재사용해도 되는 것은 별도 질문이다.
5. 한 줄 기억법: `어디서 H3 후보를 배웠나`는 이 문서, `그 connection을 같이 써도 되나`는 coalescing 문서다.

## 먼저 보는 FAQ

처음 읽을 때 가장 많이 섞이는 질문 3개만 먼저 앞에 둔다.

| 질문 | 짧은 답 | 먼저 떠올릴 문장 |
|---|---|---|
| HTTPS RR이 있으면 항상 첫 요청이 H3인가? | 아니다 | DNS가 H3를 "시도해 볼 근거"를 먼저 줄 뿐, 실제 성공은 QUIC/TLS/ALPN과 경로 상태가 결정한다 |
| `Alt-Svc`를 봤으면 다른 origin도 바로 같은 connection을 써도 되나? | 아니다 | `Alt-Svc`는 discovery 힌트이고, cross-origin 재사용 허가는 coalescing 단계에서 따로 본다 |
| `421`이 뜨면 H3 discovery가 틀린 건가? | 꼭 그렇진 않다 | discovery는 맞았지만 잘못된 connection reuse라서 `421`로 복구될 수 있다 |

이 3개를 한 줄로 묶으면 이 문서는 "`어디로 H3를 시도할지`"와 "`그 connection을 어디까지 같이 써도 되는지`"를 갈라 읽게 만드는 bridge다.

## Discovery vs Reuse Guardrail 용어 고정 박스

### 3줄 정의

- Discovery: 브라우저가 "`H3로 어디에 연결을 시도할지`" 후보를 찾는 단계다 (`Alt-Svc`, HTTPS RR/SVCB).
- Reuse guardrail: 이미 열린 연결을 "`다른 origin까지 같이 써도 되는지`" 가르는 단계다 (coalescing 조건, `421` 복구).
- 관계: Discovery가 먼저이고 reuse guardrail이 다음이다. Discovery가 맞아도 reuse guardrail에서 거절될 수 있다.

여기서 말하는 guardrail은 앱 권한(authz)이 아니다.

- 앱 권한/리소스 오류는 보통 `403`/`404` 쪽 질문이다.
- 이 문서의 `421`은 그보다 앞단의 **connection reuse 경계**를 다룬다.

## 이 문서에서 쓰는 시간 표현

`첫 요청`, `다음 새 연결(재요청)`, `fallback`을 같은 뜻으로 고정해 두면 첫 요청 차이를 더 짧게 읽을 수 있다.

### 타임라인 표기와 `fallback`도 같이 고정

| 문구 | 이 문서에서의 뜻 |
|---|---|
| `첫 요청` | 브라우저가 H3 힌트를 배우기 전 처음 나가는 요청 |
| `다음 새 연결(재요청)` | H3 힌트를 안 뒤, 새 connection이 필요해서 다시 나가는 요청 |
| `fallback` | H3를 시도했지만 실패해 H2/H1.1로 조용히 내려가는 것 |

## 자주 생기는 오해 먼저 끊기

아래 3개만 먼저 끊어 두면 "`첫 요청이 왜 바로 h3일 수도 있지?`"를 읽다가 다른 질문으로 새지 않는다.

### 자주 생기는 오해 2개

- 오해 1: `Alt-Svc`나 HTTPS RR을 보면 곧바로 다른 origin 재사용까지 허가된 것이다.
  - 정정: 둘 다 "`어디를 시도할지`"를 알려 주는 힌트다. cross-origin 재사용 허가는 coalescing 단계에서 따로 본다.
- 오해 2: `421`이 뜨면 discovery가 틀린 것이다.
  - 정정: discovery는 맞았지만 잘못된 재사용(허가 실패)이라 `421`로 되돌릴 수 있다.
- 오해 3: 여기서 말하는 "허가"가 앱 권한 검사라는 뜻이다.
  - 정정: 아니다. 여기서의 허가는 `403`/`404` 같은 app 결과가 아니라, shared connection을 계속 써도 되는지에 대한 네트워크 경계다.

<details>
<summary>Table of Contents</summary>

- [먼저 보는 FAQ](#먼저-보는-faq)
- [Discovery vs Reuse Guardrail 용어 고정 박스](#discovery-vs-reuse-guardrail-용어-고정-박스)
- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [용어를 짧게 정리하면](#용어를-짧게-정리하면)
- [Alt-Svc와 HTTPS RR는 무엇이 다른가](#alt-svc와-https-rr는-무엇이-다른가)
- [한눈 비교표: discovery 소스와 관찰 위치](#한눈-비교표-discovery-소스와-관찰-위치)
- [브라우저 타임라인에 끼워 넣어 보면](#브라우저-타임라인에-끼워-넣어-보면)
- [첫 방문 vs warmed 반복 방문 decision table](#첫-방문-vs-warmed-반복-방문-decision-table)
- [discovery와 coalescing은 어떻게 이어지나](#discovery와-coalescing은-어떻게-이어지나)
- [작은 예시로 보기](#작은-예시로-보기)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [초급자용 질문별 라우팅](#초급자용-질문별-라우팅)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

입문자가 자주 섞는 질문은 사실 둘이다.

- 브라우저는 **H3로 어디를 시도할지** 언제 아는가
- 이미 열린 H2/H3 connection을 **다른 origin과 같이 써도 되는지** 언제 판단하는가

이 둘은 같은 단계가 아니다.

- `Alt-Svc`와 HTTPS RR/SVCB는 주로 **발견(discovery)** 문제를 푼다
- connection coalescing은 그다음 **재사용 경계(reuse guardrail)** 문제를 푼다

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

핵심은 discovery가 곧 reuse guardrail 통과는 아니라는 점이다.

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

## 한눈 비교표: discovery 소스와 관찰 위치

초급자가 가장 빨리 헷갈리는 지점은 이것이다.

- `Alt-Svc`는 **HTTP header**에서 본다
- HTTPS RR은 **DNS record**에서 본다
- 그래서 관찰 화면도 보통 다르다

| 구분 | `Alt-Svc` | HTTPS RR |
|---|---|---|
| discovery 소스 | HTTP 응답 header | DNS `HTTPS` record |
| 처음 보이는 타이밍 | 첫 응답을 받은 뒤 | 첫 HTTP 요청 전에 DNS 조회 단계 |
| 주 관찰 위치 | Browser DevTools `Headers`, `curl -D -` | `dig ... HTTPS`, DNS trace |
| 초급자 질문 | "서버가 다음 연결용 H3 힌트를 줬나?" | "DNS가 출발 전에 H3 힌트를 줬나?" |
| 바로 떠올릴 문장 | "응답에서 배운다" | "DNS에서 미리 배운다" |

한 줄로 줄이면:

- `Alt-Svc`를 찾을 때는 **HTTP 응답 화면**으로 간다
- HTTPS RR을 찾을 때는 **DNS 응답 화면**으로 간다

이 표는 "어느 쪽이 더 좋다"를 비교하는 표가 아니다.
먼저 봐야 할 **증거 위치가 다르다**는 점을 고정하는 표다.

---

## 브라우저 타임라인에 끼워 넣어 보면

첫 읽기에서는 아래 4줄 타임라인 2개만 비교해도 충분하다.
차이는 "`첫 요청 전에 힌트를 이미 알았나`" 한 줄로 먼저 잡으면 된다.

| 구분 | `첫 요청` / `다음 새 연결(재요청)` 4줄 타임라인 |
|---|---|
| `Alt-Svc` driven | 1) 첫 요청 전에는 H3 힌트가 없어서 첫 연결이 보통 H2/H1.1로 시작된다.<br>2) 첫 응답에서 `Alt-Svc: h3=":443"`를 배운다.<br>3) 그다음 새 연결(재요청)에서 QUIC + ALPN `h3`를 시도한다.<br>4) 성공하면 그때부터 H3가 보인다. |
| HTTPS RR driven | 1) 첫 요청 전에 DNS HTTPS RR로 H3 힌트를 먼저 안다.<br>2) 그래서 첫 연결부터 QUIC + ALPN `h3`를 시도할 수 있다.<br>3) handshake가 성립하면 첫 요청부터 바로 H3로 간다.<br>4) 성립하지 않으면 H2/H1.1로 fallback되고 다음 새 연결에서 다시 시도할 수 있다. |

`Alt-Svc` 경로는 "응답 후 학습 -> 다음 연결 반영", HTTPS RR 경로는 "요청 전 학습 -> 첫 요청부터 H3 가능"이라는 차이만 먼저 잡으면 된다.

추가로 둘 다 공통인 한 줄:

- discovery 힌트가 있어도 UDP 경로/정책/handshake 상태 때문에 H3가 항상 성공하는 것은 아니다.

## 첫 방문 vs warmed 반복 방문 decision table

이 표는 초급자가 가장 많이 묻는 "`첫 방문에서 바로 H3가 되나?`", "`반복 방문에서 왜 H3가 되나?`"를 한 번에 가르는 작은 지도다.
여기서 `반복 방문`은 "다시 온 요청" 정도의 뜻일 뿐, **새 connection이 이미 만들어졌다는 뜻은 아니다**.

| 지금 보이는 장면 | 브라우저가 이미 가진 힌트 | 먼저 떠올릴 discovery 소스 | 흔한 protocol 결과 | 초급자 한 줄 해석 |
|---|---|---|---|---|
| 첫 방문인데 바로 `h3` | 첫 요청 전에 H3 근거가 있음 | HTTPS RR/SVCB | 첫 연결부터 H3 가능 | DNS가 출발 전에 H3 후보를 알려 준 경우다 |
| 첫 방문인데 `h2`/`http/1.1` | 아직 H3 힌트가 없음 | 없음 또는 HTTPS RR 미사용/미적용 | H2/H1.1로 시작 | 아직 응답을 받아 봐야 `Alt-Svc`를 배울 수 있다 |
| 첫 방문 응답 뒤 다음 새 연결에서 `h3` | 직전 응답에서 힌트를 배움 | `Alt-Svc` | 다음 새 연결에서 H3 시도 | 첫 방문은 학습, 반복 방문은 반영으로 읽되 "새 connection이 필요해졌을 때"라는 조건을 같이 붙인다 |
| 반복 방문인데 여전히 `h2` | `Alt-Svc`는 warm일 수 있음 | `Alt-Svc` cache | 기존 H2 재사용 또는 H3 fallback | repeat visit이어도 새 connection이 아니면 H3가 안 보일 수 있다 |
| 반복 방문인데 다시 `h2`로 내려감 | 예전 H3 힌트는 있었음 | HTTPS RR 또는 `Alt-Svc` cache | H3 시도 후 fallback | 힌트가 있어도 UDP/경로/정책이 막으면 내려간다 |

이 표를 줄여 외우면:

- HTTPS RR 쪽은 "`첫 방문 전`에 배우는 힌트"라서 first visit H3 설명에 강하다.
- `Alt-Svc` 쪽은 "`첫 응답 후`에 배우는 힌트"라서 warmed repeat visit H3 설명에 강하다.
- 둘 다 최종 확정은 QUIC/TLS/ALPN에서 난다.

짧은 혼동 방지:

- repeat visit = 새 connection 보장 아님
- warm `Alt-Svc` = 언젠가 배운 힌트가 남아 있다는 뜻이지, 현재 요청이 이미 H3로 갈 차례라는 뜻은 아님

반복 방문인데도 계속 `h2`로 보이는 장면을 더 좁혀 보고 싶으면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)를 같이 읽는 편이 빠르다.

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

위 FAQ에서 첫 분기를 잡았다면, 아래는 읽다가 다시 섞일 때 보는 보충 메모다.

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

## 초급자용 질문별 라우팅

| 지금 질문 | 여기서의 짧은 답 | 다음 단계 |
|---|---|---|
| "왜 첫 요청은 H2인데 다음 새 연결에서는 H3지?" | `Alt-Svc`는 응답 뒤에 배워져 다음 새 connection에 반영되기 쉽다 | [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) |
| "DNS에서 HTTPS RR을 봤는데 왜 H3가 아니지?" | discovery 힌트와 실제 성공은 다르다. UDP/정책/handshake가 막으면 fallback된다 | [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md) |
| "H3 connection이 열렸으면 다른 origin도 자동 재사용되나?" | 아니다. coalescing은 certificate/authority/routing을 별도 확인한다 | [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |
| "`421`이 뜨면 discovery가 틀린 건가?" | discovery가 맞아도 wrong-connection reuse라면 `421`로 되돌릴 수 있다 | [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md), [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |

이 라우팅 표는 "발견(discovery)" 질문과 "재사용 경계(reuse guardrail)" 질문을 섞지 않게 도와준다.

---

## 다음에 이어서 볼 문서

- discovery와 fallback 큰 흐름을 먼저 다지려면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- 여러 origin이 한 H2/H3 connection을 공유하는 조건까지 이어 보려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- 잘못된 공유를 `421`과 `ORIGIN` frame으로 어떻게 제어하는지 보려면 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- H3가 실제 운영에서 왜 조용히 downgrade되는지 보려면 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)

## 한 줄 정리

`Alt-Svc`와 HTTPS RR/SVCB는 브라우저가 H3 endpoint를 **언제, 어디서 배우는지**를 설명하고, connection coalescing은 그렇게 얻은 H3 connection을 **다른 origin도 같이 써도 되는지**를 설명한다. discovery와 공유 허가는 이어지지만 같은 단계는 아니다.
