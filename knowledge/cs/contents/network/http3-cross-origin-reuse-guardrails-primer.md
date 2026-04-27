# HTTP/3 Cross-Origin Reuse Guardrails Primer

> HTTP/3에서 H2의 `ORIGIN` frame 없이 cross-origin connection reuse를 어떻게 안전하게 다루는지, certificate scope, `Alt-Svc` endpoint authority, `421 Misdirected Request` 복구 순서로 설명하는 beginner follow-up primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [Wildcard Certificate vs Routing Boundary Primer](./wildcard-cert-routing-boundary-primer.md)
> - [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
> - [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
> - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [SNI Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

retrieval-anchor-keywords: HTTP/3 cross-origin reuse guardrails, HTTP/3 no ORIGIN frame, H3 ORIGIN frame 없음, H3 coalescing without ORIGIN, HTTP/3 connection coalescing, cross-origin connection reuse, H3 certificate scope, certificate SAN reuse, wildcard certificate authority, Alt-Svc endpoint authority, alternative service authority, authoritative H3 endpoint, QUIC endpoint authority, 421 Misdirected Request H3, 421 retry recovery, Alt-Svc cache removal, wrong QUIC connection, beginner H3 coalescing primer, 421 troubleshooting trace, browser devtools 421, curl 421 misdirected request, wrong h3 connection retry, browser 421 retry, same url retried after 421, alt-svc scope vs reuse, cache scope vs connection reuse, who owns alt-svc hint vs who can share connection, reuse guardrail primer, scope primer handoff

## 헷갈리면 이 문장으로 먼저 가르기

- 질문이 "`이미 열린 connection을 다른 origin에도 같이 써도 되나`"면 이 문서에서 certificate scope, endpoint authority, `421`을 본다.
- 질문이 "`이 힌트가 어느 origin의 메모인가`"면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)로 간다.
- 질문이 "`그 H3 endpoint를 어디서 배웠나`"면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)로 간다.

<details>
<summary>Table of Contents</summary>

- [왜 이 follow-up이 필요한가](#왜-이-follow-up이-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [H2와 H3 guardrail을 한 표로 보면](#h2와-h3-guardrail을-한-표로-보면)
- [Guardrail 1: certificate scope](#guardrail-1-certificate-scope)
- [Guardrail 2: Alt-Svc endpoint authority](#guardrail-2-alt-svc-endpoint-authority)
- [Guardrail 3: 421 recovery](#guardrail-3-421-recovery)
- [타임라인으로 보기](#타임라인으로-보기)
- [작은 예시](#작은-예시)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 follow-up이 필요한가

[HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)을 읽고 나면 자연스럽게 다음 질문이 생긴다.

- HTTP/3에는 H2의 `ORIGIN` frame처럼 connection별 allow-list를 알려 주는 장치가 똑같이 있나?
- 같은 certificate가 여러 hostname을 커버하면 H3 connection도 자동으로 같이 써도 되나?
- `Alt-Svc`가 다른 endpoint를 알려 주면 그 endpoint는 모든 sibling origin에 대해 안전한가?
- 잘못 공유된 요청이 들어오면 H3에서는 무엇으로 복구하나?

초보자 관점에서는 이렇게 잡는 편이 안전하다.

- H2는 `ORIGIN` frame으로 "이 connection을 어디까지 같이 써도 되는지"를 미리 좁힐 수 있다.
- H3에서는 같은 역할의 표준 `ORIGIN` frame에 기대기보다, **certificate scope + endpoint authority + `421` recovery** 조합으로 생각한다.

### Retrieval Anchors

- `HTTP/3 no ORIGIN frame`
- `H3 coalescing without ORIGIN`
- `Alt-Svc endpoint authority`
- `certificate SAN reuse`
- `421 Misdirected Request H3`
- `wrong QUIC connection`

---

## 먼저 잡는 mental model

HTTP/3 cross-origin reuse는 "빠른 길을 같이 쓰되, 그 길이 정말 그 목적지까지 책임질 수 있는지 확인하는 문제"다.

여기서 일부 초급자가 섞는 "`scope`"는 cache scope와 같은 뜻이 아니다.

- cache scope는 "누가 이 `Alt-Svc` 힌트를 배웠는가"를 묻는다
- reuse guardrail은 "이미 열린 connection에 누구를 같이 태워도 되는가"를 묻는다

즉 scope는 메모의 소유자이고, reuse는 공유 허가다.

입문용으로는 세 문장만 먼저 기억하면 된다.

- certificate scope: "이 QUIC connection에서 본 certificate가 새 origin 이름에도 맞나?"
- `Alt-Svc` endpoint authority: "`Alt-Svc`로 배운 H3 endpoint가 그 origin도 실제로 맡을 수 있나?"
- `421`: "틀린 connection으로 온 요청이면 다른 connection으로 다시 보내라는 복구 신호를 줄 수 있나?"

짧게 말하면:

- H2 `ORIGIN`: **frame으로 미리 선 긋기**
- H3: **증거로 판단하고, 틀리면 `421`로 되돌리기**

여기서 "증거"는 certificate 하나만이 아니다. Certificate는 후보 범위를 넓혀 줄 뿐이고, 실제 H3 endpoint가 그 origin에 대해 authoritative해야 한다.

---

## H2와 H3 guardrail을 한 표로 보면

| 항목 | HTTP/2 | HTTP/3 |
|---|---|---|
| 공유하는 연결 | TCP + TLS connection | QUIC connection |
| 사전 좁히기 | `ORIGIN` frame으로 origin set을 줄일 수 있음 | 같은 표준 `ORIGIN` frame에 기대지 않음 |
| 필수 감각 | certificate + origin set + routing | certificate + H3 endpoint authority + routing |
| discovery 입력 | 이미 열린 TLS connection, DNS/IP, certificate | `Alt-Svc`, HTTPS RR/SVCB, QUIC endpoint, certificate |
| 사후 복구 | `421 Misdirected Request` | `421 Misdirected Request` |
| 초보자 한 줄 | "이 connection은 A, B만 받아" | "이 endpoint가 A, B를 정말 맡는지 확인하고 아니면 421" |

중요한 차이는 이것이다.

- H2의 `ORIGIN` frame은 재사용 범위를 connection 안에서 더 명시적으로 좁히는 힌트다.
- H3에서는 그 힌트가 없다고 보고, 브라우저가 더 보수적으로 certificate와 endpoint authority를 확인하며, 서버는 잘못 온 요청을 `421`로 밀어내야 한다.

---

## Guardrail 1: certificate scope

H3 connection을 다른 origin에도 재사용하려면, 먼저 그 connection에서 본 server certificate가 새 origin에도 유효해야 한다.

예를 들어 이미 열린 H3 connection의 certificate가 아래 이름을 모두 포함한다고 하자.

- `www.example.com`
- `static.example.com`
- `admin.example.com`

그러면 브라우저는 "이 connection이 저 이름들에 대해 인증될 가능성은 있구나"라고 볼 수 있다.

하지만 여기서 끝이 아니다.

| certificate가 말해 주는 것 | certificate가 말해 주지 않는 것 |
|---|---|
| 이 서버가 특정 hostname 이름으로 인증될 수 있음 | 그 hostname들이 같은 H3 endpoint와 routing 정책을 공유한다는 사실 |
| SAN / wildcard가 어떤 이름들을 커버하는지 | `admin`을 `www`와 같은 connection에 태워도 운영 정책상 안전한지 |
| cross-origin reuse 후보가 될 수 있는지 | 실제 backend가 `:authority`별로 올바르게 분기되는지 |

따라서 beginner용 결론은 간단하다.

- certificate scope는 **필요 조건**에 가깝다.
- certificate scope만으로 H3 coalescing이 **자동 허가**되지는 않는다.

---

## Guardrail 2: Alt-Svc endpoint authority

`Alt-Svc`는 H3에서 특히 자주 등장한다.

예를 들어 `www.example.com` 응답이 아래처럼 말할 수 있다.

```http
Alt-Svc: h3="edge.example.net:443"; ma=86400
```

입문 감각으로는 "다음에는 `edge.example.net:443`의 H3 endpoint도 시도해 봐"라는 힌트다.

하지만 `Alt-Svc`는 **endpoint discovery**이지 **모든 origin에 대한 coalescing 허가서**가 아니다.

| `Alt-Svc`가 하는 일 | `Alt-Svc`가 하지 않는 일 |
|---|---|
| 이 origin을 위한 대체 H3 endpoint 후보를 알려 줌 | sibling origin 전체를 같은 connection에 태우라고 강제 |
| 브라우저가 QUIC/H3를 시도할 위치를 알려 줌 | certificate 검증을 생략 |
| 첫 요청 이후 H3 전환 또는 재방문 H3 시도에 도움 | endpoint가 다른 origin에도 authoritative한지 자동 증명 |
| 특정 host/port로 트래픽을 보낼 수 있게 함 | 잘못된 공유를 `421` 없이 안전하게 복구 |

따라서 아래 둘은 다른 문장이다.

- "`www.example.com`이 `edge.example.net:443`을 H3 endpoint로 광고했다."
- "`edge.example.net:443`의 같은 QUIC connection을 `static.example.com`에도 재사용해도 된다."

두 번째 문장까지 가려면 다시 확인해야 한다.

- certificate가 `static.example.com`에도 유효한가?
- 그 H3 endpoint가 `static.example.com` 요청을 실제로 authoritative하게 처리할 수 있는가?
- routing이 `:authority` 기준으로 올바르게 분기되는가?
- 과거에 그 origin에 대해 `421`을 받은 적은 없는가?

즉 `Alt-Svc`는 "길 안내"이고, authority 판단은 별도다.

---

## Guardrail 3: 421 recovery

`421 Misdirected Request`는 H3에서도 핵심 복구 신호다.

서버가 아래처럼 판단하면 `421`을 돌려줄 수 있다.

- 이 request의 `:authority`는 이 QUIC connection에서 처리하면 안 된다.
- 이 H3 endpoint는 해당 origin에 대해 authoritative하지 않다.
- certificate는 넓지만, 실제 routing 또는 보안 정책상 같은 connection reuse를 허용하면 안 된다.

비슷해 보이는 status와 비교하면 더 쉽다.

| status | 입문 감각 | 클라이언트가 배우는 것 |
|---|---|---|
| `404` | 맞는 서버에 갔지만 리소스가 없음 | URL이나 리소스를 확인 |
| `403` | 맞는 서버에 갔지만 권한이 없음 | 인증/인가 정책을 확인 |
| `421` | 이 connection 문맥으로 오면 안 됨 | 이 origin은 다른 connection으로 다시 시도 |

특히 `Alt-Svc`로 배운 alternative service에서 `421`을 받으면, 브라우저는 그 origin에 대해 해당 alternative service를 더 이상 믿지 않고 다른 경로로 재시도할 근거를 얻는다.

초보자용 한 줄:

**`421`은 H3에서 "이 QUIC connection에 그 origin을 싣지 마"라고 알려 주는 복구 밸브다.**

---

## 타임라인으로 보기

### `www`와 `static`은 공유 가능, `admin`은 분리해야 하는 경우

1. 브라우저가 `https://www.example.com`으로 접속한다.
2. 응답에서 `Alt-Svc: h3="edge.example.net:443"`를 배운다.
3. 다음 연결 시점에 브라우저가 `edge.example.net:443`으로 QUIC/H3 connection을 연다.
4. 그 connection의 certificate는 `www`, `static`, `admin`을 모두 커버한다.
5. `static.example.com` 요청이 생기면 브라우저는 같은 H3 connection 재사용을 검토한다.
6. `edge.example.net:443`이 실제로 `static`도 authoritative하게 처리한다면 재사용할 수 있다.
7. `admin.example.com` 요청까지 같은 connection에 실리면, 서버는 보안 경계가 다르다고 판단한다.
8. 서버가 `421 Misdirected Request`를 보낸다.
9. 브라우저는 `admin`을 이 connection에 싣지 말아야 한다고 보고, 별도 connection으로 다시 시도한다.

이 타임라인에서 핵심은 4번이 끝이 아니라는 점이다.

- certificate가 넓어도
- `Alt-Svc` endpoint가 있어도
- 실제 authority와 routing이 맞아야 reuse가 안전하다

---

## 작은 예시

| 상황 | H3 reuse 감각 | 이유 |
|---|---|---|
| `www`와 `static`이 같은 CDN edge, 같은 certificate, 같은 routing 정책을 공유 | 가능 후보 | certificate와 endpoint authority가 함께 맞음 |
| wildcard certificate가 `admin`까지 커버하지만 `admin`은 별도 보안 edge | 피해야 함 | certificate는 맞아도 endpoint authority와 정책이 다름 |
| `api`가 별도 `Alt-Svc` endpoint를 광고 | 별도 connection 후보 | discovery endpoint가 다르면 같은 QUIC connection으로 묶지 않는 쪽이 자연스러움 |
| 잘못 coalescing된 `admin` 요청에 서버가 `421` 응답 | 복구 가능 | 클라이언트가 다른 connection으로 retry할 근거를 얻음 |

운영자 관점의 작은 규칙은 아래처럼 잡으면 된다.

- 같이 받을 origin만 같은 H3 endpoint로 광고한다.
- certificate가 넓을수록 `:authority` routing과 `421` 처리를 더 명확히 한다.
- `421` 로그는 단순 4xx가 아니라 "connection reuse 경계가 맞았나"를 보는 단서로 다룬다.

---

## 자주 헷갈리는 포인트

### H3에는 `ORIGIN` frame이 없으면 guardrail도 없나

아니다.

- 사전 allow-list를 H2처럼 frame으로 받는 감각이 약해질 뿐이다.
- certificate 검증, endpoint authority 판단, 보수적 reuse, `421` recovery가 여전히 guardrail이다.

### 같은 certificate면 무조건 같은 H3 connection을 써도 되나

아니다.

- certificate는 이름 인증 범위다.
- endpoint와 routing이 그 origin을 실제로 처리할 수 있는지는 별도다.

### `Alt-Svc` endpoint가 같으면 모든 origin을 묶어도 되나

아니다.

- `Alt-Svc`는 먼저 "어디로 H3를 시도할지"를 알려 준다.
- cross-origin reuse는 그다음에 certificate, authority, routing을 다시 보는 문제다.

### `421`은 H3 장애나 서버 에러인가

그렇게만 보면 놓친다.

- `421`은 "이 connection으로 온 것이 잘못됐다"는 신호에 가깝다.
- H3 coalescing 맥락에서는 새 connection으로 분리해 retry하라는 복구 힌트가 된다.

### HTTPS RR/SVCB로 H3 endpoint를 알았을 때도 같은가

큰 원리는 같다.

- HTTPS RR/SVCB도 discovery 입력이다.
- endpoint를 먼저 알았다고 해서 cross-origin reuse 권한이 자동으로 생기지는 않는다.

---

## 다음에 이어서 볼 문서

- 전체 coalescing 조건부터 다시 보려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- `ma`, cache scope, `421`이 reuse 결정을 어떻게 묶는지 짧게 다시 잡으려면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- stale `Alt-Svc`나 예전 authority 때문에 첫 H3 요청이 `421` 뒤 fresh path에서 성공하는 장면은 [H3 Stale Alt-Svc 421 Recovery Primer](./h3-stale-alt-svc-421-recovery-primer.md)
- H3 endpoint discovery와 permission 차이를 다시 보려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- H2의 `ORIGIN` frame과 `421` 조합을 보려면 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- certificate와 hostname routing mismatch를 운영 관점으로 보려면 [SNI Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

---

## 한 줄 정리

HTTP/3에서 cross-origin reuse는 H2의 `ORIGIN` frame 없이도 certificate가 새 origin을 커버하는지, `Alt-Svc`로 배운 H3 endpoint가 그 origin에도 authoritative한지, 잘못 왔을 때 `421`로 다른 connection retry를 유도할 수 있는지를 함께 봐야 안전하다.
