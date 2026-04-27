# H3 Stale Alt-Svc 421 Recovery Primer

> 한 줄 요약: 예전에 배운 `Alt-Svc`나 예전 endpoint authority를 브라우저가 아직 믿고 H3로 먼저 갔다가 `421`을 받고, 새 connection 또는 기본 경로의 fresh path에서 바로 성공하는 패턴을 초급자 눈높이로 설명하는 primer

**난이도: 🟢 Beginner**

관련 문서:

- [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- [Alt-Svc Cache vs Per-Origin 421 Recovery](./alt-svc-cache-vs-per-origin-421-recovery.md)
- [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)
- [421 Retry Path Mini Guide: Fresh H3 Connection vs H2 Fallback](./421-retry-path-mini-guide-fresh-h3-vs-h2-fallback.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [network 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: h3 stale alt-svc 421 recovery, stale alt-svc 421, stale alt-svc fresh path, stale h3 endpoint authority, h3 421 then success, same url 421 then 200 h3, old alt-svc wrong endpoint, misdirected request stale alt-svc, stale alternative service recovery, fresh path retry after 421, stale authority h3 primer, alt-svc endpoint moved 421, stale alt-svc beginner, first request 421 second request 200, h3 421 beginner triage

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 잡는 mental model](#먼저-잡는-mental-model)
- [공통 혼동 질문 미니 FAQ](#공통-혼동-질문-미니-faq)
- [여기서 말하는 fresh path는 무엇인가](#여기서-말하는-fresh-path는-무엇인가)
- [한 표로 먼저 구분하기](#한-표로-먼저-구분하기)
- [초급자용 질문별 빠른 라우팅](#초급자용-질문별-빠른-라우팅)
- [타임라인으로 보는 stale Alt-Svc 421 recovery](#타임라인으로-보는-stale-alt-svc-421-recovery)
- [회사망에서 집망으로 바꿨을 때 타임라인 예시](#회사망에서-집망으로-바꿨을-때-타임라인-예시)
- [구체적인 예시](#구체적인-예시)
- [DevTools 첫 확인 순서 박스](#devtools-첫-확인-순서-박스)
- [DevTools에서 먼저 볼 신호](#devtools에서-먼저-볼-신호)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 primer가 필요한가

기존 `Alt-Svc`와 `421` 문서를 읽은 초보자는 아래 장면에서 다시 흔들리기 쉽다.

- 어제까지 H3가 잘 되던 origin이 오늘 첫 시도에서만 `421`을 준다.
- 같은 URL이 `421` 뒤 바로 성공하는데, 프런트엔드 중복 호출인지 브라우저 복구인지 헷갈린다.
- `Alt-Svc`가 stale해진 것인지, endpoint authority가 바뀐 것인지, 그냥 app `403/404`인지 구분이 어렵다.

이 문서는 그중에서도 가장 자주 보이는 beginner 패턴 하나만 고정한다.

- 브라우저가 예전에 배운 H3 길을 먼저 믿는다.
- 그런데 그 길이 이제 그 origin에 authoritative하지 않다.
- 서버나 edge가 `421`로 "그 길은 이제 아니다"라고 알려 준다.
- 브라우저가 fresh path로 다시 가면 바로 성공할 수 있다.

### Retrieval Anchors

- `h3 stale alt-svc 421 recovery`
- `stale Alt-Svc 421`
- `same url 421 then 200 h3`
- `fresh path retry after 421`
- `stale h3 endpoint authority`

---

## 먼저 잡는 mental model

아주 짧게는 이렇게 기억하면 된다.

- `Alt-Svc` cache: 브라우저의 "다음에 이 H3 길도 써 볼 수 있음" 메모
- stale hint: 메모는 남았는데 현실의 endpoint 책임 범위가 바뀐 상태
- `421`: "그 origin을 그 H3 path로 보내면 안 된다"는 교정 신호
- fresh path success: 브라우저가 새 판단으로 다른 connection 또는 기본 경로를 고르자 바로 성공

비유하면:

- 예전에는 A 출입문으로 들어가도 맞았다.
- 브라우저는 그 기억을 가지고 오늘도 A 문으로 먼저 간다.
- 안내판이 "`421`: 지금은 이 문이 아님"이라고 돌려보낸다.
- 브라우저가 기본 출입구나 새 문으로 다시 가면 들어간다.

핵심은 `421`이 URL 자체보다 **path/connection 문맥이 낡았음**을 알려 줄 수 있다는 점이다.

"왜 브라우저가 예전 힌트를 아직 갖고 있었는가"부터 먼저 잡고 싶다면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)의 stale hint 단계와 같이 읽으면 회사망/집망 전환 예시가 더 덜 튄다.

---

## 공통 혼동 질문 미니 FAQ

> 체크리스트:
> 1. 같은 URL 두 줄이 보여도 첫 줄이 `421`이고 둘째 줄의 `Connection ID`나 `Remote Address`가 바뀌면 프런트 중복 호출보다 브라우저 recovery를 먼저 의심한다.
> 2. 첫 줄 `421` 뒤 둘째 줄이 `200`이면 "같은 요청을 다른 길로 다시 보냈다"에 가깝다.
> 3. 첫 줄 `421` 뒤 둘째 줄이 `403` 또는 `404`면 첫 줄은 connection/path 교정 신호, 둘째 줄은 그다음에 드러난 app 결과로 읽는다.
> 4. 그래서 `421 -> 403/404`를 보면 첫 줄만 보고 권한/리소스 문제로 단정하지 말고, 둘째 줄만 보고 `421`를 무시하지도 않는다.
> 5. `Status`, `Protocol`, `Connection ID`, `Remote Address`를 같이 본 뒤 `403/404` 판독은 [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)로 이어간다.

---

## 여기서 말하는 fresh path는 무엇인가

이 문서에서 fresh path는 "브라우저가 낡은 힌트 대신 다시 고른 현재 유효한 경로"를 뜻한다.

꼭 새 protocol이라는 뜻은 아니다.

| fresh path가 될 수 있는 것 | beginner 해석 |
|---|---|
| 새 H3 connection | 같은 H3라도 새 QUIC connection과 새 authority 판단으로 다시 감 |
| 다른 H3 endpoint | 예전 alternative service 대신 현재 맞는 H3 edge를 탐 |
| 기본 origin path의 H2/H1.1 | H3 힌트를 덜 믿고 원래 경로로 돌아가 다시 감 |

초보자는 "fresh path = 새 길" 정도로 기억하면 충분하다.

- protocol이 같아도 fresh path일 수 있다
- remote address가 같아도 connection이 새로 열렸으면 fresh path일 수 있다
- 반대로 protocol만 바뀌고 같은 잘못된 문맥이면 복구라고 단정하면 안 된다

---

## 한 표로 먼저 구분하기

| 장면 | 무엇이 stale하거나 틀렸나 | 첫 실패 | 다시 성공하는 이유 |
|---|---|---|---|
| 예전 `Alt-Svc` endpoint를 그대로 믿음 | alternative service 힌트 | `421` | 브라우저가 다른 endpoint 또는 기본 경로로 재선택 |
| 같은 H3 connection에 예전 authority 감각으로 다른 origin을 실음 | endpoint authority / reuse 판단 | `421` | 새 connection에서 그 origin 전용 판단을 다시 함 |
| 진짜 app 권한/리소스 문제 | path가 아니라 app 상태 | `403` / `404` | fresh path를 가도 그대로 실패할 수 있음 |

한 줄로 줄이면:

- stale `Alt-Svc` / wrong authority면 첫 줄이 `421`, 둘째 줄은 성공 가능
- app 문제면 fresh path를 가도 status가 그대로 남는 경우가 많다

초급자용 오해 방지 한 줄도 같이 붙여 두면 좋다.

- `421`은 앱 권한/리소스 결과를 바로 뜻하지 않는다
- 먼저 봐야 할 것은 "예전 H3 path나 wrong connection을 탔나?"다

---

## 초급자용 질문별 빠른 라우팅

| 지금 보이는 장면 | 먼저 잡는 짧은 해석 | 바로 다음 문서 |
|---|---|---|
| 같은 URL이 `421 -> 200`으로 이어진다 | 프런트 중복 호출 결론보다 브라우저 retry recovery를 먼저 의심 | [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md), [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |
| 첫 줄 `421`, 둘째 줄 `403/404`가 연달아 나온다 | 첫 줄은 path/connection 교정, 둘째 줄은 app 결과일 수 있다 | [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) |
| 배포 직후 특정 origin의 첫 H3 시도만 `421`이 잦다 | stale `Alt-Svc` 또는 endpoint authority 변경 가능성을 본다 | [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md), [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md) |
| discovery 문제인지 reuse 문제인지 계속 헷갈린다 | "어디서 endpoint를 배웠나"와 "그 connection을 공유해도 되나"를 분리한다 | [Alt-Svc와 HTTPS RR, SVCB: H3 discovery와 coalescing bridge](./alt-svc-https-rr-h3-discovery-coalescing-bridge.md), [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md) |
| 주니어에게 5분 재현 절차를 알려줘야 한다 | `GET` 기준으로 DevTools에서 Status/Protocol/Connection ID 변화를 먼저 캡처한다 | [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) |

이 라우팅 표는 stale hint 복구를 "한 번의 짧은 판별 질문"으로 시작하게 만들어, 용어 암기보다 먼저 triage 순서를 잡아 준다.

---

## 타임라인으로 보는 stale Alt-Svc 421 recovery

가장 단순한 타임라인은 이렇다.

```text
1. 어제 www.example.com이 Alt-Svc: h3="edge-a.example.net:443" 를 광고
2. 브라우저는 그 메모를 아직 기억
3. 오늘 운영 변경으로 admin.example.com은 edge-b 또는 기본 경로만 authoritative
4. 브라우저가 예전 기억으로 admin 요청을 edge-a 쪽 H3 path에 먼저 실음
5. edge가 421 Misdirected Request 반환
6. 브라우저가 "이 origin은 이 path로 보내면 안 됨"을 학습
7. 새 connection 또는 기본 경로의 fresh path로 재시도
8. 200 또는 원래 app 결과로 성공
```

이 흐름에서 초보자가 기억할 것은 두 가지다.

- 첫 시도 실패 이유는 URL이 틀려서가 아니라 path authority가 낡아서일 수 있다
- 둘째 시도 성공은 "브라우저가 다른 판단으로 다시 갔다"는 뜻에 가깝다

---

## 회사망에서 집망으로 바꿨을 때 타임라인 예시

초급자가 가장 자주 보는 현실 예시를 하나로 고정하면 아래와 같다.

```text
1. 오전(회사망): 브라우저가 Alt-Svc로 h3 edge-office 힌트를 학습
2. 점심 후(집망): 같은 노트북으로 동일 URL 재접속
3. 브라우저는 아직 예전 힌트(edge-office)를 먼저 시도
4. 집망 경로에서는 그 힌트가 더 이상 맞지 않아 첫 요청 421
5. 브라우저가 해당 path를 교정하고 fresh path(기본 경로 또는 다른 h3 endpoint)로 재시도
6. 둘째 요청은 200(또는 원래 app 응답)으로 회복
```

같은 장면을 DevTools 관찰 신호로 줄이면:

| 시점 | Status/Protocol의 흔한 모양 | beginner 해석 |
|---|---|---|
| 전환 직후 첫 줄 | `421` + `h3` | 예전 네트워크에서 배운 stale hint를 먼저 썼을 가능성 |
| 바로 다음 줄 | `200` + `h3` 또는 `h2` | fresh path fallback/recovery가 동작했을 가능성 |

핵심은 "네트워크를 바꿨다" 자체가 문제가 아니라, **브라우저가 잠깐 예전 힌트를 먼저 재사용했다가 교정되는 구간**이 보인다는 점이다.

이 장면의 앞단 lifecycle 설명이 필요하면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)에서 warm -> stale로 넘어가는 흐름부터 먼저 고정하면 된다.

---

## 구체적인 예시

어제는 `www.shop.test`와 `admin.shop.test`가 둘 다 `edge-a.shop-cdn.test`에서 H3를 받았다고 하자.

```http
Alt-Svc: h3="edge-a.shop-cdn.test:443"; ma=86400
```

오늘 운영팀이 `admin.shop.test`를 별도 보안 edge로 분리했다.

- `www.shop.test` -> 여전히 `edge-a`
- `admin.shop.test` -> 이제 `edge-b` 또는 기본 origin path

하지만 브라우저는 아직 예전 메모를 기억한다.

| 순서 | 브라우저가 믿은 것 | 실제 현실 | 결과 |
|---|---|---|---|
| 첫 시도 | "`admin`도 `edge-a` H3 path로 가도 되겠지" | `admin`은 더 이상 `edge-a`가 authoritative하지 않음 | `421` |
| 둘째 시도 | "그 path는 아니구나, 새 길로 다시 가자" | `edge-b` 또는 기본 경로가 맞음 | `200` 또는 정상 app 응답 |

DevTools에서 입문자가 볼 수 있는 축약 장면은 아래와 비슷하다.

| URL | Status | Protocol | Connection ID | Remote Address | 읽는 법 |
|---|---:|---|---:|---|---|
| `https://admin.shop.test/api/me` | `421` | `h3` | `42` | `198.51.100.30:443` | 예전 H3 path 또는 잘못된 authority로 먼저 갔을 수 있음 |
| `https://admin.shop.test/api/me` | `200` | `h3` | `57` | `198.51.100.44:443` | 새 H3 connection과 새 path 판단으로 recovery했을 수 있음 |
| `https://admin.shop.test/api/me` | `200` | `h2` | `71` | `198.51.100.44:443` | 브라우저가 더 보수적으로 기본 경로 H2 fallback을 택했을 수도 있음 |

여기서 중요한 것은 둘째 줄이 꼭 `h3`일 필요가 없다는 점이다.

---

## DevTools 첫 확인 순서 박스

> 초급자용 첫 순서:
> 1. 같은 URL이 두 줄로 보이는지 먼저 본다.
> 2. 둘째 줄이 새 connection인지 `Connection ID`부터 본다.
> 3. 그다음에 첫 줄 `421`, 둘째 줄 성공(`200/204/403/404`)을 읽는다.
> 4. 마지막으로 `Protocol`과 `Remote Address`를 붙여 fresh path 여부를 보강한다.

`421 -> fresh path success` 장면에서 초급자가 가장 먼저 놓치는 것은 용어가 아니라 **순서**다.

- 먼저 같은 URL 두 줄이 있는지 본다.
- 그다음 둘째 줄이 새 connection인지 본다.
- 그 뒤에야 `h3 -> h3`, `h3 -> h2`, IP 변화 여부를 읽는다.

이 순서를 고정하면 "둘째 줄이 성공했네, 그냥 앱이 잠깐 흔들렸나?" 같은 오판이 줄어든다.

| 먼저 보는 칸 | 초급자 질문 | 이 문서에서의 1차 해석 |
|---|---|---|
| URL | 같은 클릭인데 같은 URL이 두 줄인가? | 브라우저 recovery 후보를 먼저 연다 |
| Connection ID | 둘째 줄이 새 연결인가? | fresh path 가능성을 가장 먼저 올린다 |
| Status | 첫 줄 `421`, 둘째 줄 성공인가? | wrong path 교정 뒤 재시도 성공 흐름과 맞는다 |
| Protocol / Remote Address | `h3 -> h3(new)`인가, `h3 -> h2`인가, edge가 바뀌었나? | recovery가 어떤 길로 끝났는지 보강한다 |

짧게 기억하면:

- `같은 URL 두 줄`
- `새 connection 먼저`
- `그다음 status`

이 세 줄만 먼저 봐도 초급자는 `421 -> fresh path success`를 중복 호출과 덜 헷갈린다.

관련 관측 확장 문서:

- DevTools 필드 의미를 더 자세히 보면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- 같은 URL 재시도 장면 자체를 더 넓게 보면 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)

---

## DevTools에서 먼저 볼 신호

초보자는 아래 네 가지만 먼저 보면 된다.

| 먼저 볼 것 | 기대하는 신호 | 왜 중요한가 |
|---|---|---|
| 같은 URL이 두 줄 이상 보이는가 | 첫 줄 `421`, 뒤 줄 `200` 또는 다른 app 결과 | retry recovery인지 확인 |
| `Connection ID`가 바뀌었는가 | 같은 URL인데 다른 connection | 새 판단으로 다시 갔는지 확인 |
| `Remote Address`가 바뀌었는가 | 다른 edge/front door | stale endpoint 가능성 확인 |
| `Protocol`이 바뀌었는가 | `h3 -> h2` 또는 `h3 -> h3(new)` | fresh path가 꼭 같은 protocol이 아님을 확인 |

입문 단계에서는 이 순서로 읽으면 된다.

1. 같은 URL이 다시 나왔나?
2. 둘째 줄이 다른 connection인가?
3. 첫 줄이 `421`인가?
4. 둘째 줄이 성공했나?

처음 보는 사람은 2번과 3번의 순서를 바꾸지 않는 편이 낫다.

- 같은 URL 두 줄이 있어도 같은 connection이면 브라우저 recovery라고 바로 단정하기 어렵다.
- 반대로 둘째 줄이 새 connection이면 `421 -> fresh path success` 읽기가 훨씬 쉬워진다.

이 네 가지가 맞으면 "stale path -> `421` -> fresh path recovery" 가설이 꽤 강하다.

---

## 자주 헷갈리는 포인트

### `421`이면 H3가 완전히 깨졌다는 뜻인가

아니다.

- 특정 origin에 대해
- 특정 stale path 또는 wrong authority가
- 더 이상 맞지 않는다는 뜻일 수 있다

그래서 fresh path에서는 같은 H3가 다시 성공할 수도 있다.

### 같은 URL이 두 번 보이면 프런트엔드 중복 호출인가

그럴 수도 있지만 `421` 직후라면 먼저 브라우저 복구를 본다.

- 첫 줄 `421`
- 둘째 줄 새 connection

이면 retry 가능성이 높다.

### fresh path면 항상 remote address가 바뀌나

꼭 그렇지는 않다.

- 같은 IP라도 새 connection이면 fresh path일 수 있다
- 반대로 다른 IP여도 authority가 같은 논리 경로일 수 있다

초보자는 `Connection ID`와 `Status`의 연속성을 함께 본다.

### 둘째 줄이 `403`이나 `404`면 첫 `421`은 무시해도 되나

아니다.

- 첫 줄 `421`은 transport/edge 쪽의 wrong-connection 교정
- 둘째 줄 `403/404`는 맞는 path로 간 뒤 app 층에서 나온 결과

둘 다 같은 클릭 안에서 연달아 나타날 수 있다.

### 모든 요청이 자동으로 다시 보내지나

이 primer의 예시는 side effect가 없는 `GET` 기준으로 보는 편이 안전하다.

`421`이 새 path retry의 근거를 주더라도 실제 자동 재시도 여부는 client 구현과 요청 성격에 따라 달라질 수 있다.

---

## 다음에 이어서 볼 문서

- `Alt-Svc`가 왜 stale해지는지 lifecycle부터 다시 보려면 [Alt-Svc Cache Lifecycle Basics](./alt-svc-cache-lifecycle-basics.md)
- `ma`, cache scope, `421`을 한 번 더 짧게 묶어 보려면 [Alt-Svc `ma`, Cache Scope, 421 Reuse Primer](./alt-svc-ma-cache-scope-421-reuse-primer.md)
- H3에서 endpoint authority와 `421` guardrail을 더 보려면 [HTTP/3 Cross-Origin Reuse Guardrails Primer](./http3-cross-origin-reuse-guardrails-primer.md)
- DevTools와 edge log 관측을 더 자세히 보려면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- same-URL retry 장면을 H2/H3 공통 흐름으로 다시 보려면 [421 Retry After Wrong Coalescing: H2/H3 브라우저 재시도 입문](./http2-http3-421-retry-after-wrong-coalescing.md)

---

## 한 줄 정리

H3에서 stale `Alt-Svc`나 예전 endpoint authority를 브라우저가 먼저 믿으면 첫 시도는 `421`로 튕길 수 있지만, 브라우저가 fresh path로 다시 고르면 같은 URL이 바로 성공하는 패턴이 자연스럽게 나타날 수 있다.
