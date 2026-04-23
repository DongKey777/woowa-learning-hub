# Wildcard Certificate vs Routing Boundary Primer

> wildcard certificate가 여러 host를 덮더라도 왜 CDN/LB 경계 때문에 일부 origin만 같은 connection을 공유해야 하는지, concrete CDN/LB examples로 설명하는 beginner primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

retrieval-anchor-keywords: wildcard certificate, wildcard cert, wildcard cert coalescing, wildcard cert routing boundary, wildcard certificate routing boundary, same certificate different backend, same wildcard cert different backend, CDN wildcard certificate, load balancer wildcard certificate, routing boundary vs certificate scope, certificate scope vs routing boundary, connection sharing boundary, wildcard cert authority boundary, admin separate edge, same cert different Alt-Svc endpoint, same cert different LB policy, wildcard SAN not enough, 421 misdirected request wildcard cert, ORIGIN frame allowlist wildcard cert

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [certificate scope와 routing boundary를 한 표로 보면](#certificate-scope와-routing-boundary를-한-표로-보면)
- [CDN 예시](#cdn-예시)
- [Load Balancer 예시](#load-balancer-예시)
- [빠른 판단표](#빠른-판단표)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 primer가 필요한가

입문자가 자주 하는 오해는 이것이다.

- wildcard certificate가 `*.example.com`을 커버한다
- 그러면 `www`, `static`, `api`, `admin`도 다 같은 connection으로 보내도 될 것 같다

하지만 certificate가 말해 주는 것은 **"이 이름으로 인증될 수 있는가"**까지다.
그 connection이 실제로 **"그 host를 여기서 받아야 하는가"**는 또 다른 질문이다.

초보자용으로는 아래 두 문장을 분리해서 기억하면 된다.

- certificate scope: "이 hostname을 인증서가 덮나?"
- routing boundary: "이 hostname을 이 CDN edge / LB / QUIC endpoint가 실제로 맡나?"

둘 다 맞을 때만 같은 connection 공유 후보가 된다.

### Retrieval Anchors

- `wildcard certificate`
- `wildcard cert routing boundary`
- `same certificate different backend`
- `CDN wildcard certificate`
- `load balancer wildcard certificate`
- `routing boundary vs certificate scope`

---

## 먼저 잡는 mental model

간단히 이렇게 생각하면 된다.

- certificate는 **이름표**다
- routing boundary는 **어느 프런트 데스크가 그 이름표 손님을 받아야 하는지**다

즉 wildcard certificate는 "이 손님 이름을 확인할 수 있다"를 말해 줄 뿐,
"이 손님을 지금 이 창구가 받아야 한다"까지 보장하지 않는다.

짧게 줄이면:

- certificate scope가 넓다 = 들어올 수 있는 이름 후보가 많다
- routing boundary가 좁다 = 실제로 같이 받아야 하는 이름은 일부일 수 있다

그래서 아래 조합이 가능하다.

- cert는 `www`, `static`, `api`, `admin`을 다 덮는다
- 하지만 같은 connection을 같이 써도 되는 것은 `www`, `static`뿐이다

이 감각이 바로 wildcard cert와 connection coalescing을 구분하는 출발점이다.

---

## certificate scope와 routing boundary를 한 표로 보면

| 질문 | certificate scope가 답하는 것 | routing boundary가 답하는 것 |
|---|---|---|
| 이 host 이름이 인증서와 맞는가 | 예/아니오 | 직접 답하지 않음 |
| 이 exact connection이 그 host까지 처리해도 되는가 | 직접 답하지 않음 | 예/아니오 |
| 같은 wildcard cert면 자동 공유인가 | 아니다 | 실제 공유 여부는 여기서 결정 |
| 잘못 공유되면 무엇으로 되돌리나 | certificate만으로는 복구 못 함 | `ORIGIN` frame, `421`, 별도 endpoint/LB로 경계 설정 |

초보자용 한 줄:

- certificate scope는 **이름 검증 범위**
- routing boundary는 **연결 공유 범위**

둘은 겹치기도 하지만, 항상 같지는 않다.

---

## CDN 예시

### 예시 1: `www`와 `static`은 같이 써도 되는 경우

상황:

- certificate: `*.example.com`
- host: `www.example.com`, `static.example.com`
- 둘 다 같은 CDN service와 같은 edge policy를 사용한다
- edge가 `:authority`를 보고 둘 다 올바른 origin group으로 보낸다

이 경우에는:

- cert도 두 host를 커버한다
- routing boundary도 사실상 같다
- 브라우저가 기존 H2/H3 connection을 둘이 공유하는 것이 자연스럽다

입문 감각으로는 "간판은 둘인데 같은 프런트 데스크가 둘 다 맡는 경우"다.

### 예시 2: wildcard cert는 같지만 `admin`은 분리해야 하는 경우

상황:

- certificate: `*.example.com`
- host: `www.example.com`, `admin.example.com`
- 둘 다 같은 CDN vendor를 쓰지만, `admin`은 별도 WAF 정책과 private origin을 탄다
- `www`는 캐시 가능한 public traffic이고, `admin`은 더 보수적인 auth/routing이 필요하다

이 경우에는:

- cert만 보면 둘 다 같은 edge에서 받아도 될 것처럼 보인다
- 하지만 routing boundary는 다르다
- `admin`은 같은 connection 공유 대상으로 보면 안 된다

운영 감각:

- `www`와 `admin`을 같은 certificate로 운영할 수는 있다
- 그래도 same connection share group에는 넣지 않을 수 있다
- 잘못 공유가 들어오면 `421 Misdirected Request`나 별도 endpoint 정책으로 분리한다

### 예시 3: 같은 CDN vendor지만 `api`는 다른 H3 endpoint를 쓰는 경우

상황:

- certificate: `*.example.com`
- `www.example.com`은 `Alt-Svc: h3="edge-a.example.net:443"`를 광고한다
- `api.example.com`은 별도 API edge인 `edge-api.example.net:443`를 광고한다

이 경우에는:

- cert는 두 host 모두 맞을 수 있다
- 하지만 H3 discovery endpoint부터 다르다
- 같은 QUIC connection으로 묶는 쪽보다, 각각 자기 endpoint로 가는 쪽이 자연스럽다

즉 CDN에서는 "**같은 회사의 edge**"보다 "**같은 service boundary / same advertised endpoint**"가 더 중요하다.

---

## Load Balancer 예시

### 예시 1: 하나의 L7 LB가 `www`와 `img`를 함께 받는 경우

상황:

- wildcard cert `*.example.com`
- 하나의 public L7 LB가 `www.example.com`, `img.example.com`을 모두 terminate한다
- LB 뒤에서 host-based routing으로 두 서비스를 나눈다
- 둘 다 같은 timeout, same front-door policy, same health model을 쓴다

이 경우에는:

- cert scope도 맞고
- routing boundary도 같은 front door 안에 있다
- connection 공유 후보로 보기 쉽다

### 예시 2: 같은 wildcard cert지만 `api`는 별도 보안 경계인 경우

상황:

- wildcard cert `*.example.com`
- 사용자는 겉으로 하나의 기업 도메인만 본다
- 하지만 `api.example.com`은 mTLS나 stricter rate limit이 걸린 별도 LB chain으로 간다
- `www.example.com`은 일반 public web LB로 간다

이 경우에는:

- wildcard cert는 두 host를 모두 커버할 수 있다
- 그래도 `api`와 `www`는 같은 connection share group이 아니다
- 특히 LB 뒤 정책, idle timeout, auth chain, upstream selection이 다르면 더 그렇다

초보자용 해석:

- certificate는 "같은 회사 도메인"을 보여 줄 수 있다
- LB boundary는 "같은 접수 창구인지"를 정한다

### 예시 3: 첫 SNI 기준으로 upstream이 사실상 고정되는 경우

상황:

- wildcard cert `*.example.com`
- 앞단 TLS terminator는 같은 cert를 준다
- 하지만 뒤 라우팅이 첫 handshake 문맥이나 특정 vhost bucket에 강하게 묶여 있다

이 경우에는:

- 두 번째 host가 cert에는 맞아도
- 그 connection을 그대로 재사용하면 wrong backend로 갈 수 있다

이런 유형에서는:

- H2의 `ORIGIN` frame으로 allow-list를 좁히거나
- 잘못 들어온 host에 `421`을 반환하거나
- 애초에 별도 LB endpoint를 쓰는 편이 안전하다

---

## 빠른 판단표

| 상황 | 같은 connection 공유 감각 | 이유 |
|---|---|---|
| 같은 wildcard cert + 같은 CDN/LB front door + host routing 검증됨 | 가능 후보 | certificate scope와 routing boundary가 함께 맞음 |
| 같은 wildcard cert + 같은 vendor지만 다른 CDN service / 다른 `Alt-Svc` endpoint | 분리 쪽이 자연스러움 | discovery와 authority boundary가 다름 |
| 같은 wildcard cert + `admin`/`api`만 별도 WAF, mTLS, auth chain | 분리해야 함 | 보안/운영 경계가 다름 |
| cert는 맞지만 backend selection이 first-SNI 문맥에 묶임 | 분리해야 함 | wrong connection risk가 큼 |
| 잘 모르겠고 운영 경계가 애매함 | 보수적으로 분리 | certificate만으로 share를 결정하면 안 됨 |

입문자용 규칙 하나만 남기면:

**같은 cert**보다 **같은 front door와 같은 routing policy**가 connection 공유 판단에 더 가깝다.

---

## 자주 헷갈리는 포인트

### wildcard cert면 모든 서브도메인이 자동으로 같은 connection을 쓰나

아니다.

- wildcard cert는 이름 범위를 넓힌다
- connection 공유 범위는 CDN/LB/endpoint 경계가 따로 정한다

### 같은 CDN vendor면 다 같은 routing boundary인가

아니다.

- distribution, service, `Alt-Svc` endpoint, origin group이 다를 수 있다
- 같은 vendor여도 share group은 여러 개일 수 있다

### `421`은 인증서가 틀렸다는 뜻인가

보통 그보다는 **이 connection 문맥이 틀렸다**에 가깝다.

- `421`: 다른 connection이나 endpoint로 다시 와라
- cert mismatch: handshake 단계부터 실패할 수 있다

### wildcard cert가 `example.com`도 덮나

보통 아니다.

- `*.example.com`은 보통 `www.example.com`, `api.example.com` 같은 하위 호스트를 덮는다
- apex `example.com`은 별도 SAN이 필요할 수 있다

이 포인트는 coalescing보다 certificate scope 자체의 기초지만, 초보자가 자주 같이 헷갈린다.

---

## 다음에 이어서 볼 문서

- wildcard cert와 connection coalescing 전체 감각을 먼저 넓히려면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- H2에서 allow-list를 더 명시적으로 좁히는 방법은 [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
- H3에서 `Alt-Svc` endpoint authority와 `421` recovery까지 이어 보려면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- discovery 단계와 coalescing 단계를 분리해서 보고 싶다면 [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md)
- TLS terminator와 host routing이 실제로 어떻게 어긋나는지는 [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md), [SNI, Routing Mismatch, Hostname Failure](./sni-routing-mismatch-hostname-failure.md)

---

## 한 줄 정리

wildcard certificate는 여러 hostname을 **인증할 수 있다**는 뜻이지, 그 hostname들이 모두 같은 CDN/LB connection을 **공유해야 한다**는 뜻은 아니다. 같은 cert보다 같은 routing boundary인지가 connection share 여부를 더 직접적으로 결정한다.
