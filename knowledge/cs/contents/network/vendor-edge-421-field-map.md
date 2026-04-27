# Vendor Edge 421 Field Map

> normalized `421 Misdirected Request` 예시를 Nginx, Envoy, managed edge 로그의 실제 필드 이름으로 번역해, 초보자가 "wrong connection/local reply" 단서를 로그에서 바로 찾도록 돕는 beginner primer

**난이도: 🟢 Beginner**

> 관련 문서:
> - [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
> - [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
> - [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
> - [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
> - [421 Trace Mini-Lab: Wildcard Cert Coalescing Rejection Walkthrough](./421-trace-mini-lab-wildcard-cert-coalescing.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)

retrieval-anchor-keywords: vendor edge 421 field map, nginx 421 log, envoy 421 log, misdirected_request field map, local reply 421, 421 upstream_status dash, 421 wrong connection log clues, authority sni mismatch 421, server_name mismatch 421, nginx host ssl_server_name 421, envoy response_code_details misdirected_request, envoy requested_server_name 421, managed edge 421 origin_status empty, 421 local reply vs upstream 421, 421 edge-generated vs origin-generated, 421 field translation, edge log 421 primer, beginner 421 vendor map, h3 421 vendor clue, coalescing rejection logs, edge route wrong authority

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 따로 필요한가](#왜-이-문서가-따로-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [정규화된 421 예시를 먼저 하나 고정하기](#정규화된-421-예시를-먼저-하나-고정하기)
- [필드 번역표: Nginx, Envoy, Managed Edge](#필드-번역표-nginx-envoy-managed-edge)
- [스택별로 어떻게 읽나](#스택별로-어떻게-읽나)
- [한 장으로 읽는 빠른 비교](#한-장으로-읽는-빠른-비교)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 따로 필요한가

`421` 입문 문서를 읽은 뒤 초보자는 실제 로그에서 여기서 다시 막힌다.

- 예시에서는 `response_code_details=misdirected_request`라고 했는데 우리 Nginx access log에는 그런 필드가 없다.
- 어떤 edge는 `upstream_status=-`라고 보이는데, 어떤 곳은 `target_status_code=-`처럼 다르게 적힌다.
- "local reply"라고 쓰는 곳도 있고, 그냥 `421`만 남는 곳도 있다.

그래서 이 문서의 목적은 간단하다.

- normalized example을 하나 먼저 고정한다.
- 그 예시를 Nginx, Envoy, managed edge 표면으로 번역한다.
- 초보자가 "이 요청이 app까지 갔는가"와 "왜 wrong connection으로 읽는가"를 30초 안에 찾게 만든다.

### Retrieval Anchors

- `vendor edge 421 field map`
- `nginx 421 log`
- `envoy 421 log`
- `local reply 421`
- `421 edge-generated vs origin-generated`

---

## 먼저 잡는 mental model

이 문서에서 찾고 싶은 것은 status 숫자 하나가 아니다.
아래 두 질문의 답이다.

1. 이 `421`를 **edge가 local reply로 만든 것인가**
2. 아니면 **origin/app이 upstream response로 만든 것인가**

초보자용 한 줄:

- edge-generated `421`: "틀린 connection 문맥이라 app까지 보내기 전에 edge가 돌려보냄"
- origin-generated `421`: "요청은 upstream까지 갔고, upstream이 `421`을 냄"

즉 field map의 핵심은 `421` 그 자체보다 **upstream이 비었는지**, **connection 문맥 단서가 있는지**다.

---

## 정규화된 421 예시를 먼저 하나 고정하기

문서마다 vendor 이름이 달라도, 초보자는 아래 normalized story 하나만 기억하면 된다.

```text
status=421
authority=admin.example.test
connection_context=www.example.test
upstream=-
detail=misdirected/local-reply
```

읽는 법은 이렇다.

- 요청 target은 `admin.example.test`였다.
- 하지만 이 요청이 실린 connection 문맥은 `www.example.test` 쪽이었다.
- edge가 app까지 보내지 않고 그 자리에서 `421`을 만들었다.

이제 로그 스택마다 해야 할 일은 각 줄을 아래 다섯 칸에 대응시키는 것이다.

| normalized clue | 초보자 질문 |
|---|---|
| `status=421` | 사용자에게 보인 첫 결과가 정말 `421`인가 |
| `authority=...` | 요청이 가려던 host/origin은 어디인가 |
| `connection_context=...` | 실제 connection 문맥은 어느 host/vhost/listener였나 |
| `upstream=-` | app/origin까지 가지 않았는가 |
| `detail=misdirected/local-reply` | wrong connection/local reply라고 읽을 근거가 있는가 |

---

## 필드 번역표: Nginx, Envoy, Managed Edge

| normalized clue | Nginx/OpenResty 계열에서 흔한 표면 | Envoy/mesh 계열에서 흔한 표면 | Managed edge/CDN/LB에서 흔한 표면 |
|---|---|---|---|
| request target | `host`, `:authority`, `$host` | `host`, `:authority`, authority field | `host`, `cs-host`, request authority |
| connection context | `server_name`, `$ssl_server_name`, 매칭된 vhost/listener 이름 | `requested_server_name`, SNI, route name, virtual host | listener, edge route, front door, hostname rule |
| local reply 여부 | access log만으로는 이유가 생략될 수 있음. 대신 `421`와 빈 upstream을 본다 | `response_code_details=misdirected_request` 같은 detail이 직접 보일 수 있다 | `detailed_result`, `classification`, `edge_result` 같은 유사 필드가 있으면 local reply 쪽으로 좁힌다 |
| upstream 도달 여부 | `upstream_status=-`, `upstream_addr=-`, upstream time 비어 있음 | `upstream_cluster=-`, `upstream_host=-`, upstream 관련 필드 비어 있음 | `origin_status=-`, `target_status_code=-`, origin/target host 비어 있음 |
| wrong connection 근거 | `host`와 `ssl_server_name` 또는 `server_name`이 어긋남 | authority와 `requested_server_name` 또는 route/vhost가 어긋남 | request host와 선택된 edge route/listener가 어긋남 |
| app이 직접 낸 `421`와 구분 | `upstream_status=421`면 origin-generated 가능성이 커진다 | `response_code_details=via_upstream` 또는 upstream status `421`면 origin-generated 쪽 | `origin_status=421` 또는 `target_status_code=421`면 edge local이 아니라 origin phase를 의심 |

이 표에서 중요한 점은 하나다.

- Envoy는 **이유를 직접 적어 주는 편**
- Nginx는 **이유를 간접 단서로 읽는 편**
- managed edge는 **field 이름이 제각각이지만 empty upstream/target 축은 비슷한 편**

---

## 스택별로 어떻게 읽나

### 1. Nginx/OpenResty 계열

Nginx 계열은 초보자가 가장 당황하기 쉽다.
`421`는 보이는데 `misdirected_request` 같은 친절한 라벨이 없을 수 있기 때문이다.

먼저 보는 조합은 아래다.

| 먼저 볼 것 | wrong-connection/local-reply 쪽 읽기 |
|---|---|
| `status` | `421`이면 첫 분기는 맞다 |
| `host` / `:authority` | 요청 target이 무엇이었는지 잡는다 |
| `$ssl_server_name` 또는 매칭된 `server_name` | 실제 TLS/SNI 문맥이 어느 host였는지 본다 |
| `upstream_status` / `upstream_addr` | `-`면 app 미도달 가능성이 크다 |

예시:

```text
status=421 host=admin.example.test ssl_server_name=www.example.test \
server_name=public-edge upstream_status=- upstream_addr=-
```

초보자 판독:

- 요청은 `admin`으로 왔다.
- 하지만 TLS/SNI와 vhost 문맥은 `www/public-edge` 쪽이다.
- upstream이 비어 있으니 edge local reply로 읽는 쪽이 안전하다.

Nginx에서 기억할 한 줄:

- **Nginx는 "왜 421인가"를 직접 말하지 않을 수 있으니, `421 + wrong vhost/SNI + empty upstream` 조합으로 읽는다.**

### 2. Envoy/mesh 계열

Envoy는 `421` 문맥을 가장 직접적으로 보여 주는 편이다.

먼저 보는 조합은 아래다.

| 먼저 볼 것 | wrong-connection/local-reply 쪽 읽기 |
|---|---|
| `response_code` | `421` 확인 |
| `response_code_details` | `misdirected_request`면 강한 직접 증거 |
| authority | 요청 target 확인 |
| `requested_server_name`, route, virtual host | connection 문맥 확인 |
| `upstream_cluster` / `upstream_host` | `-`면 app 미도달 가능성 큼 |

예시:

```text
response_code=421 response_code_details=misdirected_request \
authority=admin.example.test requested_server_name=www.example.test \
route_name=public-edge upstream_cluster=-
```

초보자 판독:

- Envoy가 wrong connection/local reply를 거의 직접 말해 주고 있다.
- authority는 `admin`인데 route/SNI 문맥은 `public-edge/www`다.
- upstream이 비어 있으니 app보다 edge ownership이 먼저다.

Envoy에서 기억할 한 줄:

- **`response_code_details=misdirected_request`가 보이면, auth/route보다 먼저 wrong connection local reply를 본다.**

### 3. Managed edge/CDN/LB 계열

managed edge는 제품마다 필드 이름이 제각각이다.
그래도 초보자는 아래 두 축으로 충분히 번역할 수 있다.

1. request host와 선택된 edge route가 맞는가
2. origin/target status가 비었는가

예시:

```text
status=421 host=admin.example.test edge_route=public-edge \
origin_status=- detailed_result=local_reply.misdirected
```

또는:

```text
elb_status_code=421 host=admin.example.test target_status_code=- \
actions_executed=fixed-response edge_rule=public-edge
```

초보자 판독:

- field 이름은 달라도 `target/origin=-`면 app 미도달 쪽이다.
- `edge_route=public-edge`처럼 request host와 맞지 않는 front door가 잡히면 wrong boundary 근거가 된다.

Managed edge에서 기억할 한 줄:

- **field 이름보다 "origin/target이 비었는가"와 "선택된 edge rule이 요청 host와 맞는가"를 먼저 본다.**

---

## 한 장으로 읽는 빠른 비교

| 장면 | edge-generated `421` 쪽 신호 | origin-generated `421` 쪽 신호 |
|---|---|---|
| upstream 필드 | `-`, 비어 있음 | `421` 또는 origin/target 값이 채워짐 |
| detail 필드 | `misdirected`, `local_reply`, fixed-response 성격 | `via_upstream`, target/origin response 성격 |
| host vs connection context | 자주 어긋남 | 대체로 맞음 |
| 첫 owner | edge / gateway / mesh | origin / app / upstream service |

아주 짧게 외우면 이렇다.

- `421 + empty upstream`이면 edge local reply를 먼저 본다.
- `421 + upstream=421`면 origin이 직접 낸 `421` 가능성을 먼저 본다.

---

## 자주 헷갈리는 포인트

- `421`만 있다고 모두 edge local reply는 아니다. upstream 필드가 `421`로 차면 origin-generated일 수 있다.
- Nginx에서 `misdirected_request` 라벨이 안 보여도 이상한 것이 아니다. Nginx는 간접 단서 조합으로 읽는 경우가 많다.
- Envoy에서 `421`가 보여도 `response_code_details=via_upstream`이면 edge local reply보다 upstream ownership 쪽을 먼저 본다.
- managed edge는 vendor마다 이름이 달라도 `target/origin status`, `edge rule`, `detailed_result` 축으로 번역하면 된다.
- `403/404`와 섞인 mixed trace에서는 첫 줄 `421`의 owner와 둘째 줄 app result owner를 분리해서 읽어야 한다.

---

## 다음에 이어서 볼 문서

- DevTools row와 edge log를 한 장으로 붙여 읽으려면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- `421 -> 403`와 `421 -> 200` mixed trace를 더 보려면 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- vendor general symptom translation을 더 넓게 보려면 [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)

## 한 줄 정리

Vendor마다 field 이름은 달라도 초보자가 잡아야 할 순서는 같다: `421` 확인 -> request host 확인 -> connection 문맥 확인 -> upstream이 비었는지 확인 -> misdirected/local-reply 단서를 vendor 표면으로 번역한다.
