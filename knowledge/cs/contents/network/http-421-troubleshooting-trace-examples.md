# HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기

> `421 Misdirected Request`를 `403 Forbidden`, `404 Not Found`와 섞지 않도록 Browser DevTools, curl, proxy log에서 보이는 작은 trace 차이를 먼저 잡고, 특히 `421 -> 403`와 `421 -> 200` mixed trace를 한눈에 가르는 beginner troubleshooting primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md)
> - [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
> - [421 Non-Idempotent Retry Guardrail Primer](./http-421-non-idempotent-retry-guardrail-primer.md)
> - [Vendor Edge 421 Field Map](./vendor-edge-421-field-map.md)
> - [HTTP 상태 코드 기초](./http-status-codes-basics.md)
> - [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

retrieval-anchor-keywords: 421 troubleshooting trace, 421 vs 403 vs 404, 421 Misdirected Request DevTools, browser devtools 421, curl 421 misdirected request, proxy log 421, wrong connection failure, wrong authority connection, SNI Host mismatch 421, authority mismatch 421, coalescing retry trace, junior 421 primer, beginner 421 troubleshooting, browser retry after 421, same url retried after 421, wrong connection retry trace, 421 403 mixed trace, 421 200 mixed trace, 421 then 403, 421 then 200, misdirected request then forbidden, misdirected request then success, 421 post retry, 421 non idempotent retry, vendor edge 421 field map, nginx 421 log, envoy 421 log

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [403, 404, 421 빠른 비교](#403-404-421-빠른-비교)
- [예시 상황](#예시-상황)
- [Browser DevTools에서 보는 trace](#browser-devtools에서-보는-trace)
- [혼합 trace 캡처 체크: `421 -> 403` vs `421 -> 200`](#혼합-trace-캡처-체크-421---403-vs-421---200)
- [curl에서 보는 trace](#curl에서-보는-trace)
- [proxy log에서 보는 trace](#proxy-log에서-보는-trace)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [실전 확인 순서](#실전-확인-순서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 중요한가

`421`, `403`, `404`는 모두 4xx라서 처음 보면 "클라이언트 요청이 뭔가 잘못됐나 보다"로 뭉뚱그리기 쉽다.

하지만 고칠 곳이 다르다.

- `403`은 보통 authz, role, policy를 본다
- `404`는 URL path, route, resource 존재 여부를 본다
- `421`은 먼저 **그 요청이 맞는 connection으로 갔는지**를 본다

즉 `421`을 `403`처럼 권한 문제로만 파면 시간을 낭비할 수 있다.
반대로 `403`이나 `404`를 `421`처럼 connection 문제로 보면 app route와 권한 설정을 놓칠 수 있다.

### Retrieval Anchors

- `421 troubleshooting trace`
- `421 vs 403 vs 404`
- `browser devtools 421`
- `curl 421 misdirected request`
- `proxy log 421`
- `wrong connection failure`
- `authority mismatch 421`

---

## 먼저 잡는 mental model

가장 쉬운 구분은 "서버 문 앞까지는 제대로 갔나?"다.

- `403`: 맞는 문으로 갔고, 문지기가 "들어오면 안 된다"고 했다
- `404`: 맞는 문으로 갔고, 안에 찾는 방이나 물건이 없었다
- `421`: 애초에 **다른 문으로 와야 하는 요청이 이 connection으로 들어왔다**

HTTP/2, HTTP/3에서는 connection 하나가 여러 origin 요청을 같이 실을 수 있다.
이 최적화가 잘못되면 서버는 "이 connection 문맥에서 이 `Host`/`:authority`는 처리하지 않겠다"는 뜻으로 `421`을 보낼 수 있다.

짧게 말하면:

```text
403/404: request target 안에서 생긴 거절/부재
421: request target보다 앞단의 connection/authority 문맥 문제
```

---

## 403, 404, 421 빠른 비교

처음 10초 판단만 필요하면 아래 2행만 먼저 본다.

| 첫 질문 | `421` 먼저 의심 | `403/404` 먼저 의심 |
|---|---|---|
| 어디가 어긋났나 | connection/authority 문맥 | 권한, path, resource |
| 첫 확인 위치 | `Protocol`, `Remote Address`, `Connection ID`, `Host`/`:authority` | auth/session, role, route, resource id |

| status | 초보자 감각 | 먼저 볼 곳 | trace에서 자주 보이는 신호 |
|---|---|---|---|
| `403 Forbidden` | 맞는 서버가 권한 때문에 거절 | 로그인 상태, role, ACL, WAF/auth policy | app 또는 auth layer가 body를 만들고, 같은 connection으로 retry해도 대개 그대로 `403` |
| `404 Not Found` | 맞는 서버가 리소스를 못 찾음 | URL path, route mapping, resource id | route/app 로그에 `not found` 계열 흔적, connection을 새로 열어도 대개 그대로 `404` |
| `421 Misdirected Request` | 요청이 틀린 connection 문맥에 실림 | `Host`/`:authority`, SNI, protocol, connection reuse, coalescing, edge routing | proxy/edge가 짧게 거절, 다른 connection으로 재시도하면 사라질 수 있음 |

중요한 차이는 `421`의 다음 행동이다.

- `403`, `404`: 보통 같은 URL을 새 connection으로 다시 보내도 의미가 거의 같다
- `421`: client가 **다른 connection**으로 다시 보내면 성공하거나 다른 status로 바뀔 수 있다

---

## 예시 상황

아래처럼 세 hostname이 있다고 하자.

```text
www.example.test    -> 공개 페이지
static.example.test -> 정적 파일
admin.example.test  -> 관리자 API
```

인증서는 세 hostname을 모두 커버한다.
브라우저는 이미 열린 H2/H3 connection을 재사용하려고 할 수 있다.
그런데 운영 정책상 `admin.example.test`는 `www/static`과 같은 connection으로 받으면 안 된다고 하자.

이때 `admin` 요청이 `www/static`용 connection에 잘못 실리면 edge나 origin은 `421`을 보낼 수 있다.

---

## Browser DevTools에서 보는 trace

DevTools Network 탭에서는 status 숫자 하나만 보지 말고 아래 컬럼을 같이 본다.

- `Status`
- `Protocol`
- `Remote Address`
- `Size`
- `Time` / `Waterfall`
- 가능하면 `Connection ID` 또는 유사한 connection 식별 컬럼
- row를 눌렀을 때 `Headers`의 `Host` 또는 HTTP/2, HTTP/3의 `:authority`

### 421 trace 예시

아래는 실제 화면 그대로가 아니라, DevTools에서 초보자가 읽어야 하는 신호를 줄인 예시다.

| URL | Status | Protocol | Remote Address | 읽는 법 |
|---|---:|---|---|---|
| `https://admin.example.test/api/me` | `421` | `h2` | `203.0.113.10:443` | `admin` 요청이 기존 shared H2 connection에 잘못 실렸을 수 있음 |
| `https://admin.example.test/api/me` | `200` | `h2` | `203.0.113.20:443` | browser가 다른 connection 또는 다른 edge로 다시 시도해 성공했을 수 있음 |

이런 모양이면 "권한이 없어서 `403`"보다 먼저 아래를 의심한다.

- 첫 row의 `:authority`는 `admin.example.test`인데 connection은 `www/static` 쪽 edge에 붙어 있었나
- protocol이 `h2` 또는 `h3`라서 connection reuse/coalescing 가능성이 있었나
- `421` 뒤에 같은 URL 또는 같은 origin으로 새 요청이 바로 이어졌나
- 두 번째 요청의 `Remote Address`, protocol, connection id가 달라졌나

### 403 trace 예시

| URL | Status | Protocol | Remote Address | 읽는 법 |
|---|---:|---|---|---|
| `https://admin.example.test/api/me` | `403` | `h2` | `203.0.113.20:443` | 맞는 `admin` endpoint가 요청을 받았지만 권한 정책으로 거절 |

`403`에서는 보통 아래가 더 중요하다.

- response body가 `{"error":"forbidden"}`처럼 app/auth layer에서 만든 모양인가
- request에 cookie, session, bearer token이 있었나
- 같은 connection으로 다른 admin API도 일관되게 `403`인가
- app log 또는 auth log에 denied event가 남았나

### 404 trace 예시

| URL | Status | Protocol | Remote Address | 읽는 법 |
|---|---:|---|---|---|
| `https://admin.example.test/api/members/9999` | `404` | `h2` | `203.0.113.20:443` | 맞는 `admin` endpoint에서 path 또는 resource를 못 찾음 |

`404`에서는 connection보다 먼저 아래를 본다.

- path가 정확한가
- route prefix가 빠졌나
- resource id가 실제로 존재하나
- app router나 controller까지 도착했나

---

## 혼합 trace 캡처 체크: `421 -> 403` vs `421 -> 200`

beginner가 가장 자주 헷갈리는 장면은 이것이다.

- 첫 row가 `421`
- 바로 다음 row에 같은 URL이 다시 뜸
- 그런데 둘째 row가 `200`일 때도 있고 `403`일 때도 있음

이때 핵심은 **둘 다 먼저는 wrong connection 복구**라는 점이다.
둘째 row가 무엇이냐에 따라 "복구 후 최종 app 결과"만 달라진다.

### 먼저 잡는 2단계 mental model

1. 첫 줄 `421`: "이 요청은 방금 connection을 잘못 탔다."
2. 둘째 줄 `200` 또는 `403`: "새 connection으로 다시 간 뒤, 그다음엔 app/auth 결과가 나왔다."

즉 `421 -> 403`을 보면 `403`만 보고 "처음부터 권한 문제였다"고 단정하면 안 된다.
반대로 `421 -> 200`을 보면 `200`만 보고 "처음 요청도 정상"이었다고 읽으면 안 된다.

### 한눈에 보는 비교 캡처

| 캡처 패턴 | 먼저 읽을 한 줄 | 둘째 줄의 뜻 | 초보자 첫 행동 |
|---|---|---|---|
| `421 -> 200` | wrong connection을 고치니 정상 응답이 나왔다 | 새 connection에서는 라우팅/authority가 맞았다 | coalescing, `Remote Address`, `Connection ID`, edge route를 먼저 본다 |
| `421 -> 403` | wrong connection을 고친 뒤에도 권한에서 막혔다 | connection 문제는 복구됐지만 authz 문제는 남아 있다 | 먼저 connection 교정 trace를 확인하고, 그다음 auth/session/policy를 본다 |

같은 URL 기준 축약 캡처를 그리면 아래처럼 읽으면 된다.

| URL | Status | Protocol | Connection ID | Remote Address | beginner 판독 |
|---|---:|---|---:|---|---|
| `https://admin.example.test/api/me` | `421` | `h2` | `17` | `203.0.113.10:443` | 첫 시도는 shared connection 오탑승 |
| `https://admin.example.test/api/me` | `200` | `h2` | `24` | `203.0.113.20:443` | 새 connection에서는 정상 처리 |

| URL | Status | Protocol | Connection ID | Remote Address | beginner 판독 |
|---|---:|---|---:|---|---|
| `https://admin.example.test/api/me` | `421` | `h2` | `17` | `203.0.113.10:443` | 첫 시도는 shared connection 오탑승 |
| `https://admin.example.test/api/me` | `403` | `h2` | `24` | `203.0.113.20:443` | 새 connection으로는 맞게 갔지만 권한 정책에서 거절 |

### `421 -> 403`를 `403` 단독 실패와 구분하는 법

아래 둘은 겉보기엔 둘 다 마지막 줄이 `403`이라 헷갈린다.

| 장면 | 읽는 법 | 먼저 볼 곳 |
|---|---|---|
| `403` 한 줄만 있음 | 처음부터 맞는 서버가 권한 거절 | token, cookie, role, policy |
| `421 -> 403` 두 줄이 있음 | 먼저 wrong connection, 그다음 auth 거절 | `Connection ID`/`Remote Address` 변화 후 auth 확인 |

한 문장으로 줄이면:

- `403 only`: auth 문제부터 본다
- `421 -> 403`: connection 교정이 있었는지 먼저 확인하고, auth 문제를 이어서 본다

### 캡처할 때 꼭 남길 4필드

스크린샷이나 문서 캡처에는 아래 4개를 같이 남기면 오분류가 많이 줄어든다.

| 필드 | 이유 |
|---|---|
| `Status` | `421` 뒤 최종 status가 `200`인지 `403`인지 보기 위해 |
| `Protocol` | `h2`/`h3` reuse 맥락인지 보기 위해 |
| `Connection ID` | 새 connection으로 갈아탔는지 확인하기 위해 |
| `Remote Address` | 다른 edge/front door로 갔는지 보기 위해 |

`421 -> 403`와 `421 -> 200`를 비교하는 beginner 캡처는 이 4필드만 보여도 충분하다.
body 전문이나 긴 waterfall보다, 같은 URL 두 줄과 connection 변화가 먼저 보이게 잡는 편이 좋다.

---

## curl에서 보는 trace

`curl`은 브라우저만큼 자동 coalescing trace를 예쁘게 보여 주지는 않는다.
그래도 status line, protocol, `Host`/`:authority`, connection reuse 로그를 같이 보면 421 감각을 잡을 수 있다.

### 421 예시

```bash
curl --http2 -v https://admin.example.test/api/me
```

줄여서 보면 이런 모양이다.

```text
* ALPN: server accepted h2
> GET /api/me HTTP/2
> Host: admin.example.test
< HTTP/2 421
< content-type: text/plain

Misdirected Request
```

이때 바로 권한 문제로 가지 말고 먼저 질문을 바꾼다.

- `Host`는 `admin.example.test`인데 TLS SNI나 edge routing은 다른 vhost로 잡힌 것은 아닌가
- 같은 IP/edge에서 여러 hostname을 공유하고 있나
- H2/H3 connection reuse를 끄거나 새 connection으로 보내면 status가 바뀌는가

여러 URL을 한 번에 호출해 connection reuse 흔적을 볼 수도 있다.

```bash
curl --http2 -v https://www.example.test/ https://admin.example.test/api/me
```

verbose log에서 같은 연결 재사용 또는 multiplexing 흔적이 보이고 두 번째 요청만 `421`이면, wrong-connection 가설이 강해진다.
반대로 새 connection으로 보내도 계속 `421`이면 edge route, SNI, certificate, vhost 설정을 더 직접적으로 확인해야 한다.

### 403 예시

```bash
curl -i https://admin.example.test/api/me
```

```text
HTTP/2 403
content-type: application/json

{"error":"forbidden","reason":"missing_admin_role"}
```

이 모양이면 connection보다 authz를 먼저 본다.
cookie, bearer token, role claim, policy rule, WAF rule 같은 단서가 우선이다.

### 404 예시

```bash
curl -i https://admin.example.test/api/members/9999
```

```text
HTTP/2 404
content-type: application/json

{"error":"not_found","resource":"member"}
```

이 모양이면 path, route, resource id를 먼저 본다.
특히 같은 base URL의 다른 resource는 `200`인데 특정 id만 `404`면 connection 문제일 가능성은 낮다.

---

## proxy log에서 보는 trace

proxy log는 `421`을 가장 빨리 알아보게 해 줄 수 있다.
다만 기본 access log만으로는 부족할 때가 많다.

초보자도 아래 필드는 이름만이라도 익혀 두면 좋다.

실제 로그 제품명이 Nginx, Envoy, managed edge로 갈라져 헷갈리면 [Vendor Edge 421 Field Map](./vendor-edge-421-field-map.md)에서 field 이름 번역표를 먼저 본다.

| 필드 | 왜 필요한가 |
|---|---|
| `status` | 최종 사용자에게 보인 HTTP status |
| `host` 또는 `:authority` | 요청이 가리킨 origin |
| `sni` | TLS handshake에서 client가 말한 hostname |
| `server_name` / `vhost` / `route` | proxy가 매칭한 가상 서버나 route |
| `protocol` | `h1`, `h2`, `h3` 중 무엇인지 |
| `connection_id` | 같은 connection에 여러 요청이 실렸는지 보기 위함 |
| `upstream_status` / `upstream_cluster` | app까지 갔는지, proxy가 local reply로 끝냈는지 보기 위함 |
| `response_code_details` | Envoy 같은 proxy에서 local reply 이유를 더 좁히기 위함 |

### 421 log 예시

아래는 vendor별 실제 기본 포맷이 아니라, incident 때 보기 좋은 normalized log 예시다.

```text
status=421 protocol=h2 host=admin.example.test sni=www.example.test \
server_name=www-vhost route=- upstream_status=- upstream_cluster=- \
connection_id=c-7 response_code_details=misdirected_request
```

읽는 법:

- `host=admin.example.test`인데 `sni=www.example.test` 또는 `server_name=www-vhost`처럼 connection 문맥이 다르다
- `upstream_status=-`라서 app까지 가지 않았을 수 있다
- `response_code_details`가 misdirected, authority mismatch, route mismatch 계열이면 `421` 가설이 강하다

### 403 log 예시

```text
status=403 protocol=h2 host=admin.example.test sni=admin.example.test \
server_name=admin-vhost route=admin-api upstream_status=403 \
upstream_cluster=admin-service response_code_details=authz_denied
```

읽는 법:

- `host`, `sni`, `server_name`이 같은 admin 문맥으로 맞다
- `upstream_status=403`이면 app 또는 auth upstream이 실제로 거절했을 가능성이 있다
- route가 잡혔으므로 connection mismatch보다 권한 정책을 먼저 본다

### 404 log 예시

```text
status=404 protocol=h2 host=admin.example.test sni=admin.example.test \
server_name=admin-vhost route=admin-api upstream_status=404 \
upstream_cluster=admin-service path=/api/members/9999
```

읽는 법:

- admin route와 upstream까지 갔다
- status owner가 app 쪽이면 path/resource 문제일 가능성이 높다
- wrong connection보다 route mapping과 resource 존재 여부를 확인한다

---

## 초보자가 자주 헷갈리는 포인트

### 421도 4xx니까 클라이언트가 URL을 틀린 건가

꼭 그렇지는 않다.

`421`은 URL path가 틀렸다는 뜻보다, request가 실린 connection 또는 authority 문맥이 틀렸다는 뜻에 가깝다.
URL 자체가 맞아도 H2/H3 coalescing, SNI, vhost, edge routing이 어긋나면 발생할 수 있다.

### `421 -> 403`이면 결국 403이니까 421은 무시해도 되나

안 된다.

이 trace는 보통 두 문제가 시간순서로 붙어 있는 것이다.

- 첫 번째 문제: wrong connection이라서 `421`
- 두 번째 문제: 새 connection으로는 갔지만 authz가 부족해서 `403`

즉 최종 실패 원인은 `403`일 수 있어도, 첫 row의 `421`은 "왜 같은 URL이 두 번 보였는가"를 설명하는 중요한 단서다.

### 421을 보면 무조건 HTTP/2 문제인가

아니다.

`421`은 HTTP status code이고 HTTP/3에서도 wrong connection recovery 신호로 볼 수 있다.
다만 실전에서 H2/H3 connection reuse와 함께 자주 설명되기 때문에 protocol 컬럼을 같이 보는 것이다.

### 421을 403으로 바꿔도 되나

대개 좋은 해결이 아니다.

정말 권한 문제면 `403`이 맞지만, connection 문맥이 틀린 요청이면 `421`이 더 정확하다.
`403`으로 숨기면 client가 다른 connection으로 retry할 힌트를 잃고, 운영자는 auth 문제로 오해하기 쉽다.

### DevTools에 421 row가 안 보이면 421이 없었던 건가

항상 그렇지는 않다.

브라우저가 내부 retry를 하거나, log 보존 설정이 꺼져 있거나, cache/redirect trace가 섞이면 첫 실패 row를 놓칠 수 있다.
재현할 때는 `Preserve log`를 켜고, Network row의 protocol과 remote address를 같이 본다.

---

## 실전 확인 순서

1. DevTools에서 `Status`, `Protocol`, `Remote Address`, `Headers`를 같이 본다.
2. `421` 뒤 같은 origin으로 새 요청이 이어졌는지 확인한다.
3. `curl -v --http2` 또는 필요한 경우 HTTP/3 client trace로 status line과 `Host`/`:authority`를 확인한다.
4. proxy log에서 `host`, `sni`, `server_name`, `route`, `upstream_status`를 비교한다.
5. app log에 요청이 없고 proxy가 `421` local reply를 만들었다면 connection/authority mismatch부터 본다.
6. app까지 도착해 `403`/`404`를 만들었다면 authz, route, resource 문제로 좁힌다.

---

## 한 줄 정리

`403`과 `404`는 대체로 맞는 origin 안에서의 거절/부재이고, `421`은 요청이 잘못된 connection 또는 authority 문맥에 실렸다는 신호라서 DevTools, curl, proxy log에서 protocol, remote address, `Host`/`:authority`, SNI, upstream 도착 여부를 함께 봐야 한다.
