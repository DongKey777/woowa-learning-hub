# H3 Discovery Observability Primer: Alt-Svc vs HTTPS RR 확인하기

> Browser DevTools, DNS `HTTPS` RR/SVCB answer, simple `curl`/`dig` trace를 함께 보며 H3 discovery가 `Alt-Svc` 기반인지 DNS HTTPS RR 기반인지 입문 수준에서 구분하는 primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [DNS 기초](./dns-basics.md)

retrieval-anchor-keywords: H3 discovery observability, Alt-Svc vs HTTPS RR trace, DevTools H3 discovery, browser DevTools Alt-Svc h3, DNS HTTPS RR h3, SVCB h3 answer, dig HTTPS RR, curl Alt-Svc h3 trace, curl http3 trace, first request h3, subsequent request h3, Alt-Svc driven H3, HTTPS RR driven H3, browser H3 discovery verification, junior H3 observability primer

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [한눈에 보는 구분표](#한눈에-보는-구분표)
- [DevTools에서 먼저 볼 것](#devtools에서-먼저-볼-것)
- [DNS answer를 `dig`로 확인하기](#dns-answer를-dig로-확인하기)
- [`curl`로 작은 trace 만들기](#curl로-작은-trace-만들기)
- [판단 순서](#판단-순서)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 중요한가

브라우저 Network 탭에서 `h3`를 보면 "HTTP/3가 붙었다"는 사실은 알 수 있다.
하지만 그것만으로는 브라우저가 **어떻게 H3 endpoint를 알았는지**까지 알 수 없다.

입문자가 나눠야 할 질문은 세 개다.

- 이 요청이 실제로 `h3`로 갔나?
- 브라우저가 H3 후보를 `Alt-Svc` 응답으로 배웠나?
- 아니면 DNS의 HTTPS RR/SVCB answer에서 먼저 배웠나?

이 구분이 중요한 이유는 고칠 곳이 다르기 때문이다.

- `Alt-Svc` 기반이면 response header, edge 광고, browser Alt-Svc cache를 본다
- HTTPS RR 기반이면 DNS answer, resolver 차이, SVCB/HTTPS record 설정을 본다
- 둘 다 있어도 UDP path나 browser policy 때문에 H2로 fallback될 수 있다

### Retrieval Anchors

- `H3 discovery observability`
- `Alt-Svc vs HTTPS RR trace`
- `DevTools H3 discovery`
- `DNS HTTPS RR h3`
- `dig HTTPS RR`
- `curl Alt-Svc h3 trace`
- `first request h3`

---

## 먼저 잡는 mental model

H3 discovery는 "브라우저가 H3로 갈 수 있는 문을 어떻게 알았나"를 보는 문제다.

두 가지 길을 이렇게 기억하면 쉽다.

| 길 | 비유 | 언제 알게 되나 | 관찰 단서 |
|---|---|---|---|
| `Alt-Svc` | 서버에 한 번 다녀온 뒤 받은 다음 길 안내 | HTTP response 이후 | response header에 `Alt-Svc: h3=...` |
| HTTPS RR/SVCB | 출발 전에 DNS가 준 웹 연결 힌트 | HTTP response 이전 | `dig HTTPS` answer에 `alpn="h3..."` |

즉 가장 단순한 감각은 이렇다.

```text
Alt-Svc driven:
첫 연결은 H2/H1 -> response에서 Alt-Svc를 봄 -> 다음 새 연결에서 H3 시도

HTTPS RR driven:
DNS answer에서 H3 힌트를 먼저 봄 -> 첫 HTTP response 전부터 H3 시도 가능
```

여기서 주의할 점은 discovery가 success를 보장하지 않는다는 것이다.

- H3 후보를 알아도 UDP 443이 막히면 H2로 fallback될 수 있다
- H3 connection이 생겨도 다른 origin과 같이 써도 되는지는 coalescing에서 따로 판단한다

---

## 한눈에 보는 구분표

| 관찰된 모습 | 가장 그럴듯한 해석 | 더 확인할 것 |
|---|---|---|
| 첫 clean request는 `h2`, response에 `Alt-Svc: h3=":443"`가 있고 이후 새 연결이 `h3` | `Alt-Svc` driven 가능성이 큼 | 기존 browser Alt-Svc cache가 없었는지, DNS HTTPS RR에 `h3`가 없는지 |
| 첫 clean request부터 `h3`, `dig HTTPS`에 `alpn="h3..."`가 있음 | HTTPS RR driven 가능성이 큼 | 이전 방문 cache가 없었는지, 같은 resolver answer인지 |
| response에도 `Alt-Svc`가 있고 DNS HTTPS RR에도 `h3`가 있음 | 둘 다 discovery 입력일 수 있음 | 단일 원인으로 단정하지 말고 browser NetLog/실험 조건을 더 좁힘 |
| `Alt-Svc`와 HTTPS RR이 모두 보이지만 DevTools는 `h2` | discovery는 있었지만 H3 성공 실패 또는 fallback | UDP 443, QUIC support, browser policy, edge listener |
| `curl --http3`는 성공하지만 browser 첫 요청은 `h2` | 강제 테스트와 browser 자연 선택이 다름 | browser cache, HTTPS RR, Alt-Svc, enterprise policy |

입문 단계에서는 "하나의 화면에서 증명"하려고 하지 말고, DevTools + DNS answer + 작은 curl trace를 맞춰서 본다.

---

## DevTools에서 먼저 볼 것

Chrome/Edge 계열 DevTools 기준으로 아래 순서가 가장 안전하다.
브라우저 버전마다 UI 이름은 조금 달라도 읽는 원리는 같다.

### 1. Protocol column을 켠다

Network 탭에서 `Protocol` column을 보이게 둔다.
요청 row에서 보통 아래처럼 보인다.

| Protocol | 의미 |
|---|---|
| `h3` | 이 요청은 HTTP/3 connection으로 갔다 |
| `h2` | 이 요청은 HTTP/2 connection으로 갔다 |
| `http/1.1` 또는 유사 표기 | 이 요청은 HTTP/1.1 connection으로 갔다 |

중요한 점:

- `Protocol = h3`는 "H3 사용"을 말한다
- 하지만 "Alt-Svc로 배웠는지, HTTPS RR로 배웠는지"를 혼자 증명하지는 않는다

### 2. 첫 요청과 이후 요청을 나눠 본다

`Alt-Svc` driven인지 보려면 시간 순서가 중요하다.

| 시점 | 볼 것 | 읽는 법 |
|---|---|---|
| 첫 clean navigation | main document의 `Protocol` | 처음부터 `h3`인지, 먼저 `h2`인지 |
| 첫 response headers | `Alt-Svc` header | 서버가 다음 H3 endpoint를 광고했는지 |
| 이후 새 connection | 같은 origin의 `Protocol` | `Alt-Svc`를 배운 뒤 `h3`로 바뀌는지 |

"clean"에 가까운 조건을 만들려면 새 browser profile이나 시크릿 창을 쓰고, 기존 탭을 닫은 뒤 다시 본다.
엄밀한 검증에서는 browser DNS cache, socket pool, Alt-Svc cache가 남을 수 있으므로 NetLog 같은 도구가 필요하지만, 입문 단계에서는 먼저 시간 순서를 분리하는 것만으로도 오해를 많이 줄일 수 있다.

### 3. Response Headers에서 `Alt-Svc`를 찾는다

row를 누르고 `Headers`에서 response headers를 본다.

```http
Alt-Svc: h3=":443"; ma=86400
```

이 header는 입문 감각으로 아래처럼 읽는다.

- `h3=":443"`: 같은 host의 443번에서 H3도 시도할 수 있다는 힌트
- `ma=86400`: 이 힌트를 일정 시간 cache할 수 있다는 힌트

다른 endpoint를 가리킬 수도 있다.

```http
Alt-Svc: h3="edge.example.net:443"; ma=3600
```

이 경우 "이 origin의 H3 후보 endpoint가 `edge.example.net:443`일 수 있다" 정도로 읽는다.
다만 이것도 다른 origin까지 자동 공유하라는 뜻은 아니다.

---

## DNS answer를 `dig`로 확인하기

HTTPS RR/SVCB 기반 discovery는 DevTools Network row만으로는 보기 어렵다.
터미널에서 DNS answer를 따로 확인한다.

```bash
dig +noall +answer www.example.com HTTPS
```

예시 answer:

```text
www.example.com. 300 IN HTTPS 1 . alpn="h3,h2" ipv4hint=203.0.113.10
```

입문자가 먼저 볼 부분은 두 곳이다.

| answer 조각 | 읽는 법 |
|---|---|
| `HTTPS 1 ...` | HTTPS RR/SVCB 계열 answer가 있다 |
| `alpn="h3,h2"` | DNS 단계에서 H3를 시도할 힌트가 있다 |

다른 endpoint target이 보일 수도 있다.

```text
www.example.com. 300 IN HTTPS 1 edge.example.net. alpn="h3"
```

이 경우는 "DNS가 `www.example.com`의 웹 endpoint 후보로 `edge.example.net`과 H3 힌트를 줬다"로 읽는다.

### 구버전 도구에서는 TYPE65도 시도한다

일부 환경에서는 `HTTPS` 이름 대신 type number로 확인해야 할 수 있다.

```bash
dig +noall +answer www.example.com TYPE65
```

### resolver 차이를 조심한다

브라우저와 터미널 `dig`가 같은 resolver를 쓰지 않을 수 있다.

- 브라우저는 DoH를 쓸 수 있다
- OS resolver와 터미널 지정 resolver가 다를 수 있다
- 회사망 DNS가 HTTPS RR을 숨기거나 바꿀 수 있다

그래서 비교가 필요하면 resolver를 명시해서 본다.

```bash
dig @1.1.1.1 +noall +answer www.example.com HTTPS
dig @8.8.8.8 +noall +answer www.example.com HTTPS
```

`dig` 결과는 "브라우저가 반드시 이 answer를 봤다"가 아니라, "DNS 쪽에 H3 discovery 힌트가 존재하는지"를 확인하는 근거로 쓴다.

---

## `curl`로 작은 trace 만들기

`curl`은 browser DevTools를 대체하지 않는다.
하지만 response header, 강제 H3 가능 여부, Alt-Svc cache 감각을 빠르게 분리하는 데 좋다.

### 1. Response의 `Alt-Svc` 확인

```bash
curl -sS -D - -o /dev/null https://www.example.com | grep -i '^alt-svc:'
```

예상 신호:

```text
alt-svc: h3=":443"; ma=86400
```

이 값이 보이면 서버나 edge가 HTTP response로 H3 후보를 광고한다는 뜻이다.
다만 이 한 줄만으로 브라우저가 실제로 H3를 성공했다는 뜻은 아니다.

### 2. 현재 curl이 어떤 HTTP version으로 끝났는지 보기

```bash
curl -sS -o /dev/null -w 'http_version=%{http_version}\n' https://www.example.com
```

예시:

```text
http_version=2
```

강제로 H3를 시도해 볼 수도 있다.

```bash
curl --http3 -sS -o /dev/null -w 'http_version=%{http_version}\n' https://www.example.com
```

예시:

```text
http_version=3
```

해석은 조심해야 한다.

- `curl --http3` 성공: 해당 환경에서 H3가 가능하다는 강한 신호
- browser가 자연스럽게 H3를 선택했다는 증명은 아님
- curl build가 HTTP/3를 지원하지 않으면 이 명령 자체가 실패할 수 있음

### 3. curl의 Alt-Svc cache 감각 보기

browser와 완전히 같지는 않지만, `Alt-Svc`가 "첫 응답 이후 다음 연결에 영향을 준다"는 감각을 볼 수 있다.

```bash
rm -f /tmp/h3-altsvc.txt
curl -sS -D - -o /dev/null --alt-svc /tmp/h3-altsvc.txt https://www.example.com
cat /tmp/h3-altsvc.txt
curl -v --alt-svc /tmp/h3-altsvc.txt -o /dev/null https://www.example.com
```

볼 것:

- 첫 command의 response header에 `Alt-Svc`가 있었는가
- `/tmp/h3-altsvc.txt`에 h3 alternative service가 저장됐는가
- 다음 command의 verbose log에서 alternative service를 쓰려는 흔적이 있는가

이 trace는 `Alt-Svc`가 "현재 response를 즉시 바꾸는 header"가 아니라 "다음 connection 후보를 cache하게 하는 힌트"라는 감각을 잡는 데 유용하다.

---

## 판단 순서

실전에서는 아래 순서대로 좁힌다.

### 1. DevTools에서 실제 protocol을 확인한다

- `Protocol`이 `h3`인지 본다
- 첫 요청인지, 이후 요청인지 분리한다
- response header에 `Alt-Svc`가 있는지 본다

### 2. DNS HTTPS RR answer를 확인한다

```bash
dig +noall +answer www.example.com HTTPS
```

- `alpn="h3"` 계열이 있으면 DNS 기반 discovery 가능성이 있다
- answer가 없으면 `Alt-Svc` 또는 이전 cache 쪽 가능성이 상대적으로 커진다

### 3. curl로 서버 광고와 H3 가능성을 분리한다

```bash
curl -sS -D - -o /dev/null https://www.example.com | grep -i '^alt-svc:'
curl --http3 -sS -o /dev/null -w 'http_version=%{http_version}\n' https://www.example.com
```

- 첫 줄은 `Alt-Svc` 광고 확인
- 둘째 줄은 현재 client path에서 H3 가능성 확인

### 4. 결론은 확률로 말한다

입문 단계에서 안전한 표현은 아래처럼 쓴다.

| 결론 표현 | 필요한 근거 |
|---|---|
| "`Alt-Svc` driven으로 보인다" | 첫 clean request는 H2/H1, response에 `Alt-Svc`, 이후 새 connection에서 H3, DNS HTTPS RR에 H3 힌트 없음 |
| "HTTPS RR driven으로 보인다" | first clean request부터 H3, `dig HTTPS`에 `alpn=h3`, 이전 방문 cache 가능성 낮음 |
| "둘 다 후보라 단정 어렵다" | response `Alt-Svc`와 DNS HTTPS RR `h3`가 모두 있음 |
| "discovery는 있지만 H3 성공은 안 된다" | `Alt-Svc`/HTTPS RR은 보이는데 DevTools/curl protocol이 H2로 끝남 |

---

## 자주 헷갈리는 포인트

### DevTools의 `h3`만 보면 원인을 알 수 있나

아니다.
`h3`는 결과 protocol이고, discovery source는 아니다.
`Alt-Svc` header와 DNS HTTPS RR answer를 같이 봐야 한다.

### `Alt-Svc`가 보이면 이번 요청이 Alt-Svc로 H3가 된 것인가

꼭 그렇지 않다.
`Alt-Svc`는 보통 response에서 배워 다음 새 connection에 영향을 준다.
이미 `h3`로 온 response에 `Alt-Svc`가 다시 붙어 있을 수도 있다.

### HTTPS RR에 `alpn="h3"`가 있으면 무조건 H3인가

아니다.
DNS answer는 후보를 알려 줄 뿐이다.
UDP 443 차단, QUIC listener 문제, browser policy 때문에 H2로 fallback될 수 있다.

### `curl --http3` 성공이면 browser도 같은 방식으로 H3를 찾은 것인가

아니다.
`curl --http3`는 강제 시도에 가깝다.
browser의 자연 선택은 cache, DNS, policy, 기존 connection 영향을 더 많이 받는다.

### DevTools의 `Disable cache`를 켜면 Alt-Svc cache도 깨끗해지나

그렇게 단정하지 않는다.
`Disable cache`는 주로 HTTP cache 관찰에 영향을 준다.
H3 discovery를 엄밀히 보려면 새 profile, cache clearing, browser NetLog 같은 조건 통제가 더 필요할 수 있다.

---

## 다음에 이어서 볼 문서

- discovery와 coalescing의 개념 차이를 잡으려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- 브라우저가 H1/H2/H3를 고르는 큰 흐름은 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- discovery는 됐는데 H3가 조용히 H2로 내려가는 운영 문제는 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
- H3 connection을 다른 origin과 공유해도 되는지는 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)

## 한 줄 정리

H3 discovery 관측은 DevTools의 `Protocol=h3` 하나로 끝나지 않는다. 첫 요청과 이후 요청의 시간 순서, response의 `Alt-Svc`, DNS의 HTTPS RR/SVCB answer, `curl`의 H3 가능성 trace를 함께 봐야 `Alt-Svc` driven인지 HTTPS RR driven인지 조심스럽게 구분할 수 있다.
