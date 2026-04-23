# Alt-Svc Cache Lifecycle Basics

> `Alt-Svc`가 첫 방문을 즉시 HTTP/3로 바꾸는 마법이 아니라, browser가 다음 새 connection에서 쓸 수 있는 H3 힌트를 cache하고 만료시키는 흐름이라는 점을 초급자 눈높이로 설명하는 primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
> - [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)

retrieval-anchor-keywords: Alt-Svc cache lifecycle, Alt-Svc cache warming, Alt-Svc expiry, Alt-Svc stale hint, stale Alt-Svc cache, first visit vs repeat visit H3, first request h2 next request h3, repeat visit HTTP/3, Alt-Svc ma max age, Alt-Svc cache invalidation, browser Alt-Svc cache, H3 cache warmup, Alt-Svc fallback, expired Alt-Svc fallback, stale h3 endpoint, junior Alt-Svc primer

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [Alt-Svc cache가 기억하는 것](#alt-svc-cache가-기억하는-것)
- [첫 방문과 반복 방문은 왜 다르게 보이나](#첫-방문과-반복-방문은-왜-다르게-보이나)
- [warming, expiry, stale hint를 타임라인으로 보기](#warming-expiry-stale-hint를-타임라인으로-보기)
- [짧은 비교표](#짧은-비교표)
- [구체적인 예시](#구체적인-예시)
- [흔한 오해](#흔한-오해)
- [관찰할 때 볼 것](#관찰할-때-볼-것)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 먼저 잡는 mental model

`Alt-Svc` cache는 browser 안의 작은 메모장처럼 생각하면 된다.

처음 `https://www.example.com`에 갔을 때 서버가 이렇게 말할 수 있다.

```http
Alt-Svc: h3=":443"; ma=86400
```

browser는 이것을 이렇게 적어 둔다.

```text
www.example.com은 다음 새 connection에서 h3도 시도해 볼 수 있다.
이 메모는 최대 86400초 동안 유효하다.
```

중요한 감각은 세 가지다.

- `Alt-Svc`는 보통 **이번 응답의 protocol을 바꾸지 않는다**
- 대신 browser가 **다음 새 connection**에서 H3를 시도할 근거를 만든다
- 시간이 지나거나 실패가 반복되면 그 힌트는 만료되거나 덜 신뢰될 수 있다

그래서 입문자가 보는 "첫 방문은 H2, 다음 방문은 H3" 현상은 자연스러운 결과다.

### Retrieval Anchors

- `Alt-Svc cache lifecycle`
- `Alt-Svc cache warming`
- `Alt-Svc expiry`
- `Alt-Svc stale hint`
- `first visit vs repeat visit H3`
- `first request h2 next request h3`
- `repeat visit HTTP/3`

---

## Alt-Svc cache가 기억하는 것

`Alt-Svc` cache는 HTTP 응답 body를 저장하는 일반 HTTP cache와 다르다.
이미지나 HTML을 저장하는 것이 아니라, **다음 연결 후보**를 기억한다.

| 기억하는 항목 | 예시 | 의미 |
|---|---|---|
| 원래 origin | `https://www.example.com` | 이 힌트가 적용되는 사이트 이름 |
| alternative protocol | `h3` | 다음에 HTTP/3를 시도할 수 있음 |
| alternative endpoint | `:443` 또는 `edge.example.net:443` | QUIC/H3로 가 볼 위치 |
| 유효 시간 | `ma=86400` | 이 힌트를 얼마 동안 기억할 수 있는지 |

예를 들어 아래 header는:

```http
Alt-Svc: h3="edge.example.net:443"; ma=3600
```

초급자 관점에서 이렇게 읽으면 된다.

- "`www.example.com` 요청을 다음에 새로 연결할 때"
- "`edge.example.net:443`의 H3 경로도 후보로 삼을 수 있다"
- "이 힌트는 최대 1시간 정도 기억할 수 있다"

단, 이 정보는 **시도 후보**다.
H3 성공, cross-origin connection 공유, certificate/routing 허가는 별도 단계다.

---

## 첫 방문과 반복 방문은 왜 다르게 보이나

가장 흔한 흐름은 아래처럼 보인다.

| 시점 | browser가 아는 것 | 흔한 protocol 결과 |
|---|---|---|
| 첫 방문 전 | 아직 `Alt-Svc` cache가 비어 있음 | H2 또는 H1.1로 시작 |
| 첫 응답 후 | `Alt-Svc: h3=...; ma=...`를 배움 | 아직 이번 응답은 원래 protocol |
| 다음 새 connection | H3 후보를 알고 있음 | H3 시도, 성공하면 H3 |
| H3 실패 | UDP 차단/edge 문제 등을 경험 | H2/H1.1 fallback |
| `ma` 만료 후 | 힌트를 더 이상 신뢰하지 않음 | 다시 H2/H1.1로 시작할 수 있음 |

여기서 "다음 요청"과 "다음 새 connection"은 다를 수 있다.

- 이미 열려 있는 H2 connection이 건강하면 browser가 그대로 재사용할 수 있다
- 그래서 `Alt-Svc`를 배운 직후의 같은 탭 요청이 반드시 H3로 바뀌지는 않는다
- 새 탭, 일정 시간 후, 기존 connection 종료 후에야 차이가 보일 수 있다

큰 흐름은 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)에서 이어서 보면 된다.

---

## warming, expiry, stale hint를 타임라인으로 보기

### 1. Cache warming: 힌트를 처음 배움

```text
1. browser -> https://www.example.com
2. 첫 connection은 H2로 성립
3. response header에 Alt-Svc: h3=":443"; ma=86400
4. browser가 Alt-Svc cache에 H3 후보를 저장
```

이것을 cache warming이라고 볼 수 있다.
아직 "H3 성공"이 아니라, **다음에 H3를 시도할 준비가 됨**에 가깝다.

### 2. Repeat visit: warm cache가 H3 시도를 앞당김

```text
1. 같은 origin에 새 connection이 필요해짐
2. browser가 Alt-Svc cache를 확인
3. h3 후보가 아직 유효함
4. QUIC/H3 시도
5. 성공하면 이번 connection은 H3
```

그래서 같은 사이트라도 clean profile 첫 방문과 평소 방문이 다르게 보일 수 있다.

- clean profile: H2로 시작한 뒤 `Alt-Svc`를 배움
- 평소 profile: 이미 warm cache가 있어 H3를 먼저 시도할 수 있음

### 3. Expiry: `ma`가 지나면 힌트를 잊음

`ma`는 max age다.

```http
Alt-Svc: h3=":443"; ma=60
```

이 경우 browser는 이 힌트를 짧게만 기억할 수 있다.
만료 후 새 connection에서는 H3 후보를 모르는 상태처럼 행동할 수 있다.

입문 감각으로는:

- warm cache가 있을 때: "전에 배운 H3 길이 아직 유효하니 먼저 시도"
- expired cache일 때: "예전 메모는 낡았으니 기본 경로부터 다시 확인"

### 4. Stale hint: 메모는 남았지만 현실이 바뀜

stale hint는 "browser가 아직 힌트를 기억하는데, 실제 서버/네트워크 상태가 바뀐" 상황이다.

예를 들면:

- CDN 설정에서 H3 listener를 내렸는데 browser cache에는 예전 `h3=":443"`가 남아 있음
- 회사망에 들어와 UDP 443이 막혔는데 집에서 배운 H3 힌트가 남아 있음
- edge endpoint가 바뀌었는데 일부 client가 예전 alternative endpoint를 계속 시도함

이때 정상적인 browser는 보통 사용자에게 바로 에러를 보여 주기보다 fallback을 시도한다.

```text
stale Alt-Svc hint로 H3 시도
        ↓
QUIC 연결 실패 또는 timeout
        ↓
TCP+TLS로 fallback
        ↓
ALPN 결과에 따라 H2/H1.1 사용
```

운영자가 볼 때는 "가끔 첫 요청이 느리다", "특정 네트워크에서만 H3 비율이 낮다"처럼 보일 수 있다.
이 더 깊은 운영 판독은 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)에서 다룬다.

---

## 짧은 비교표

| 상태 | browser 안의 감각 | first/repeat behavior | 주의할 점 |
|---|---|---|---|
| Cold | 아직 H3 힌트를 모름 | 첫 방문은 H2/H1.1일 수 있음 | response의 `Alt-Svc`는 다음을 위한 힌트 |
| Warm | 유효한 H3 힌트를 기억함 | 새 connection에서 H3를 더 빨리 시도 | 기존 H2 connection 재사용이면 바로 안 보일 수 있음 |
| Expired | `ma`가 지나 힌트를 신뢰하지 않음 | 다시 기본 경로로 시작할 수 있음 | 만료 후 새 응답에서 다시 배울 수 있음 |
| Stale | 힌트는 남았지만 현실이 바뀜 | H3 시도 후 fallback 가능 | 짧은 지연이나 H3 비율 하락으로 보일 수 있음 |
| Cleared | profile/cache가 지워짐 | clean first visit처럼 보임 | DevTools의 HTTP cache 끄기와 같다고 단정하지 않음 |

---

## 구체적인 예시

### 예시 1: 첫 방문은 H2, 두 번째 방문은 H3

1. 새 browser profile로 `https://shop.example.com`에 접속한다.
2. 첫 main document는 `Protocol = h2`로 보인다.
3. response header에 `Alt-Svc: h3=":443"; ma=86400`가 있다.
4. browser를 다시 열거나 새 connection이 필요해진다.
5. 같은 origin 요청이 `Protocol = h3`로 보인다.

이것은 이상한 downgrade/upgrade가 아니라 `Alt-Svc` cache warming의 흔한 모습이다.

### 예시 2: 어제는 H3였는데 오늘은 H2

가능한 beginner 해석은 여러 개다.

| 가능성 | 확인 방향 |
|---|---|
| `Alt-Svc` hint가 만료됨 | response에 새 `Alt-Svc`가 다시 오는지 확인 |
| UDP 443이 막힌 네트워크로 이동 | 다른 네트워크와 protocol 분포 비교 |
| server/edge가 H3 광고를 중단 | response header와 CDN 설정 확인 |
| browser가 실패 후 잠시 H3 시도를 줄임 | 같은 조건에서 시간이 지난 뒤 재확인 |

단정하기보다 "cache 만료", "stale hint fallback", "네트워크별 UDP 차단"을 나눠 본다.

### 예시 3: DevTools에서 `Disable cache`를 켰는데도 결과가 애매함

DevTools의 `Disable cache`는 주로 HTTP response cache 관찰에 쓰인다.
`Alt-Svc` cache, DNS cache, socket pool까지 모두 같은 방식으로 깨끗해진다고 단정하면 안 된다.

초급자용 실험에서는 아래처럼 조건을 분리한다.

- 새 browser profile 또는 시크릿 창으로 cold 상태를 만든다
- 기존 탭과 열린 connection을 닫는다
- 첫 request와 이후 새 connection을 따로 본다
- response `Alt-Svc`, DevTools `Protocol`, DNS HTTPS RR을 함께 본다

관측 절차는 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)에서 이어서 보면 된다.

---

## 흔한 오해

### `Alt-Svc`가 있으면 이번 응답이 이미 H3인가

아니다.
`Alt-Svc`는 response header로 보일 수 있지만, 그 response 자체가 H2로 온 것일 수 있다.
핵심은 "다음 새 connection의 후보"다.

### `ma=86400`이면 반드시 24시간 동안 H3를 쓰나

아니다.
`ma`는 힌트의 유효 시간이지 성공 보장이 아니다.
UDP 차단, QUIC 실패, browser policy, edge 설정에 따라 H2/H1.1로 fallback될 수 있다.

### `Alt-Svc` cache는 HTTP cache와 같은가

아니다.
HTTP cache는 response body나 validator를 다루고, `Alt-Svc` cache는 alternative service 힌트를 다룬다.
`Cache-Control`과 같은 문서 캐시 규칙으로만 설명하면 헷갈린다.

### 오래된 `Alt-Svc` hint가 있으면 장애가 바로 난다는 뜻인가

보통은 아니다.
대부분 client는 실패하면 fallback한다.
다만 fallback까지 걸리는 시간 때문에 첫 요청 latency가 늘거나 H3 성공률이 낮아질 수 있다.

### HTTPS RR이 있으면 Alt-Svc cache lifecycle은 안 봐도 되나

아니다.
두 discovery 입력이 함께 있을 수 있다.
HTTPS RR은 DNS에서 먼저 오는 힌트이고, `Alt-Svc`는 HTTP response 후 cache되는 힌트다.
둘을 구분하는 bridge는 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)에서 다룬다.

---

## 관찰할 때 볼 것

입문 단계에서는 한 화면의 `h3`만 보고 결론 내리지 않는다.

| 질문 | 볼 단서 |
|---|---|
| cold 상태인가 warm 상태인가 | 새 profile인지, 기존 방문 이력이 있는지 |
| 첫 응답이 무엇을 광고했나 | response header의 `Alt-Svc` |
| 실제 요청 protocol은 무엇인가 | DevTools `Protocol` column |
| DNS가 먼저 H3 힌트를 줬나 | `dig HTTPS`의 `alpn="h3"` |
| fallback이 일어났나 | H3 힌트는 있는데 결과가 H2/H1.1인지 |

실험 문장은 이렇게 조심스럽게 쓰는 편이 좋다.

| 표현 | 더 안전한 이유 |
|---|---|
| "첫 clean request는 H2였고, response에서 `Alt-Svc`를 배운 뒤 이후 새 connection이 H3였다" | 시간 순서가 드러남 |
| "`Alt-Svc` driven으로 보이지만 HTTPS RR 여부도 확인해야 한다" | DNS 기반 discovery 가능성을 남김 |
| "H3 힌트는 있지만 이 네트워크에서는 fallback되는 것으로 보인다" | UDP 차단/정책 가능성을 포함 |

---

## 다음에 이어서 볼 문서

- H1/H2/H3 선택 흐름 전체는 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- `Alt-Svc`와 DNS HTTPS RR/SVCB를 나눠 보려면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- DevTools, DNS, curl trace로 확인하려면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
- H3 힌트는 있는데 H2로 내려가는 운영 해석은 [HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block](./http2-http3-downgrade-attribution-alt-svc-udp-block.md)
- H3 connection을 다른 origin과 공유해도 되는지는 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)

## 한 줄 정리

`Alt-Svc` cache lifecycle은 "처음 배움(warming) -> 다음 새 connection에서 활용 -> `ma`가 지나 만료 -> 현실이 바뀌면 stale hint로 H3 시도 후 fallback"의 흐름으로 보면 된다. 그래서 첫 방문과 반복 방문의 protocol이 달라질 수 있고, 오래된 힌트가 있어도 browser는 보통 H2/H1.1 fallback으로 서비스를 계속 이용하게 만든다.
