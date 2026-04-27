# Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기

**난이도: 🟢 Beginner**

> 한 줄 요약: 브라우저 Network 탭에서 `memory cache`, `disk cache`, `revalidation`, `304 Not Modified`를 실제 요청 trace 기준으로 구분하고, `304`인데도 DevTools에 body가 보이는 이유를 cached body 재사용 관점으로 읽는 실전 primer

관련 문서:

- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)
- [Browser DevTools `Protocol` 열 표기 차이 보조노트](./browser-devtools-protocol-column-labels-primer.md)
- [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)
- [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)
- [Cache-Control 실전](./cache-control-practical.md)
- [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)

retrieval-anchor-keywords: browser devtools cache trace, memory cache, disk cache, browser cache revalidation, 304 devtools, conditional request trace, from memory cache, from disk cache, if-none-match, if-modified-since, 304 vs memory cache, 304 response body devtools, protocol vs cache signal, 처음 배우는데 h3랑 304, 처음 배우는데 memory cache 뭐예요

> [!TIP]
> `Protocol h3`를 보고 있는 순간에도 질문은 두 개다.
>
> - 전송 경로 질문: "`h3`로 갔나, `h2`로 갔나"
> - body 출처 질문: "서버에서 다시 받았나, browser cache를 썼나"
>
> 이 문서는 두 번째 질문을 푼다. 첫 번째 질문에서 `Alt-Svc`/HTTPS RR/SVCB를 같이 읽어야 하면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)로 간다.

<details>
<summary>Table of Contents</summary>

- [스크롤 없이 보는 4단계 판독 체크리스트](#스크롤-없이-보는-4단계-판독-체크리스트)
- [왜 중요한가](#왜-중요한가)
- [먼저 기억할 핵심 구분](#먼저-기억할-핵심-구분)
- [DevTools에서 먼저 켜 둘 것](#devtools에서-먼저-켜-둘-것)
- [한 번에 보는 trace 판독표](#한-번에-보는-trace-판독표)
- [DevTools 듀얼-시그널 미니 체크리스트](#devtools-듀얼-시그널-미니-체크리스트)
- [1분 분리 체크리스트: `Protocol=h3` vs `from memory cache` vs `304`](#1분-분리-체크리스트-protocolh3-vs-from-memory-cache-vs-304)
- [memory cache 읽는 법](#memory-cache-읽는-법)
- [disk cache 읽는 법](#disk-cache-읽는-법)
- [revalidation과 304 읽는 법](#revalidation과-304-읽는-법)
- [왜 304인데 Response 탭에 body가 보이나](#왜-304인데-response-탭에-body가-보이나)
- [2분 실험 예시](#2분-실험-예시)
- [Disable cache ON/OFF를 따로 봐야 하는 이유](#disable-cache-onoff를-따로-봐야-하는-이유)
- [실전 추적 순서](#실전-추적-순서)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

> [!TIP]
> **스크롤 없이 보는 4단계 판독 체크리스트**
>
> 같은 URL을 볼 때는 `첫 방문`과 `반복 방문`을 섞지 말고 아래 4단계만 먼저 확인하면 된다.
>
> 1. **지금이 첫 방문인가, 반복 방문인가**
>    - 첫 방문이면 기준선으로 `200 + 실제 다운로드`를 먼저 기대한다.
>    - 반복 방문이면 cache hit, `304`, 새 `200` 중 하나를 비교한다.
> 2. **body를 어디서 썼나**
>    - `from memory cache` / `from disk cache`면 브라우저가 이미 가진 사본을 바로 쓴다.
>    - cache 표기가 없으면 서버 재검증이나 새 다운로드 가능성을 본다.
> 3. **서버에 다시 물어봤나**
>    - request에 `If-None-Match` / `If-Modified-Since`가 있으면 재검증이다.
>    - 이때 `304`면 기존 body 유지, `200`이면 새 body 교체다.
> 4. **실험 스위치가 결과를 바꿨나**
>    - `Disable cache`, hard reload, query string 변경이 켜져 있으면 자연 반복 방문 결과로 단정하지 않는다.
>
> | 장면 | 첫 결론 |
> |---|---|
> | 첫 방문 + `200` | 정상 기준선이다. 아직 cache 성향 판정 단계가 아니다. |
> | 반복 방문 + `from memory cache`/`from disk cache` | 서버에 안 갔을 가능성을 먼저 본다. |
> | 반복 방문 + validator + `304` | 서버에 다시 물어본 뒤 기존 body를 재사용한 것이다. |
> | 반복 방문 + validator + `200` | 재검증했지만 리소스가 바뀌어 새 body를 받은 것이다. |
>
> 자주 하는 오해:
> - `304`를 `memory cache`와 같은 종류의 hit로 본다.
> - `Disable cache` ON 결과를 평소 사용자 반복 방문 결과처럼 말한다.
> - `Protocol h2/h3`를 body 출처 신호로 읽는다.

## 스크롤 없이 보는 4단계 판독 체크리스트

초급자에게 가장 안전한 시작점은 "지금 이 row가 첫 방문인지, 반복 방문인지"부터 분리하는 것이다.

```text
첫 방문이면: 기준선 확인
반복 방문이면: cache 재사용 / 재검증 / 새 다운로드 중 무엇인지 판독
```

이 문서는 아래 4단계를 계속 반복하는 구조다.

1. 첫 방문인지 반복 방문인지 먼저 나눈다.
2. body 출처가 브라우저 cache인지, 서버 응답인지 본다.
3. validator가 있으면 `304`인지 `200`인지 확인한다.
4. `Disable cache` 같은 실험 스위치가 켜졌는지 마지막에 확인한다.

아주 짧게 기억하면 이렇게 읽으면 된다.

| 질문 | 예/아니오에 따라 바로 내릴 결론 |
|---|---|
| 첫 방문인가 | `200` 기준선을 먼저 본다. cache 성향 결론은 보류한다. |
| 반복 방문인가 | `from memory cache`/`from disk cache`/validator+`304`/validator+`200` 중 하나로 좁힌다. |
| validator가 있나 | 있으면 서버 재검증이다. 없으면 local cache reuse 가능성이 더 크다. |
| 실험 스위치가 켜졌나 | 켜졌으면 자연 사용자 흐름 판정과 분리한다. |

## 왜 중요한가

브라우저 Network 탭을 보다 보면 비슷해 보이는데 의미가 완전히 다른 네 가지가 섞여 나온다.

- 브라우저가 `memory cache`에서 바로 꺼낸 경우
- 브라우저가 `disk cache`에서 바로 꺼낸 경우
- 브라우저가 서버에 재확인만 한 경우
- 서버가 실제로 새 body를 다시 내려준 경우

여기서 가장 자주 생기는 오해는 두 가지다.

- `304 Not Modified`를 "캐시에서 그냥 꺼낸 것"으로 뭉뚱그린다
- `memory cache`/`disk cache`와 HTTP `304`를 같은 종류의 신호로 본다

하지만 실제로는 다르다.

- `memory cache`, `disk cache`는 브라우저 저장 계층
- `304 Not Modified`는 조건부 요청에 대한 서버 응답

즉 `304`는 서버 왕복이 있었고, `memory cache`/`disk cache`는 아예 서버에 안 갔을 수 있다.

### Retrieval Anchors

- `browser devtools cache trace`
- `memory cache`
- `disk cache`
- `browser cache revalidation`
- `304 devtools`
- `conditional request trace`
- `from memory cache`
- `from disk cache`

---

## 먼저 기억할 핵심 구분

가장 먼저 아래 흐름을 머리에 고정하면 Network 탭이 훨씬 잘 읽힌다.

```text
1. fresh cache hit
   -> 브라우저가 memory cache 또는 disk cache에서 바로 재사용
   -> 서버 요청이 없을 수 있다

2. stale cache 또는 no-cache 정책
   -> 브라우저가 조건부 요청(If-None-Match / If-Modified-Since) 전송
   -> 서버가 안 바뀌었으면 304
   -> body는 기존 cache 사본을 다시 사용

3. stale cache인데 리소스가 바뀜
   -> 조건부 요청 전송
   -> 서버가 200 + 새 body + 새 validator 응답
   -> 브라우저가 새 사본으로 교체
```

핵심은 이 한 줄이다.

- `memory cache` / `disk cache` = 브라우저가 이미 가진 body를 즉시 사용
- `304` = 서버가 기존 body를 계속 써도 된다고 확인

---

## DevTools에서 먼저 켜 둘 것

Chrome/Edge DevTools 기준으로 실전에서 먼저 보는 포인트는 아래다. 브라우저 버전에 따라 표시는 조금 달라질 수 있지만 해석 순서는 거의 같다.

- `Network` 탭을 열고 `Preserve log`를 켠다
- `Disable cache`는 자연스러운 캐시 동작을 볼 때는 끈다
- 컬럼은 `Status`, `Size`, `Time`, `Waterfall`, `Initiator`를 보이게 둔다
- 같은 row를 눌러 `Headers`에서 request/response header를 직접 본다

특히 `Disable cache`는 함정이다.

- 이 옵션을 켜면 DevTools가 열린 동안 브라우저 cache를 우회한다
- 즉 cache 동작을 관찰하려는데 이 옵션이 켜져 있으면 관찰 자체가 틀어진다

---

## 한 번에 보는 trace 판독표

| 관찰 신호 | 서버 요청 | body 출처 | DevTools에서 먼저 볼 것 | 의미 |
|---|---|---|---|---|
| `from memory cache` 계열 표기 | 보통 없음 | 프로세스 메모리 | `Size`, 짧은 waterfall, validator request 부재 | fresh한 사본을 메모리에서 즉시 재사용 |
| `from disk cache` 계열 표기 | 보통 없음 | 로컬 디스크 | `Size`, 짧은 waterfall, validator request 부재 | fresh한 사본을 디스크 cache에서 재사용 |
| request에 `If-None-Match` 또는 `If-Modified-Since`가 있음 | 있음 | 기존 cache body | request header + `304` status | 재검증 후 cached body 재사용 |
| `200 OK`와 새 body가 내려옴 | 있음 | 네트워크 새 응답 | response header/body, transfer size | cache miss이거나 재검증 결과 변경됨 |

실전에서 row 하나를 읽을 때는 아래 순서가 가장 빠르다.

1. `Size`나 row badge가 cache hit 계열인지 본다
2. request header에 validator가 실렸는지 본다
3. status가 `304`인지 `200`인지 본다
4. waterfall이 네트워크 왕복처럼 보이는지, 즉시 종료처럼 보이는지 본다

## DevTools 듀얼-시그널 미니 체크리스트

초급자 오분류를 줄이는 핵심은 한 신호만 보지 않고 아래 두 신호를 같이 읽는 것이다.

- 신호 A: `Protocol` 열(`h1`/`h2`/`h3`)
- 신호 B: cache 표기(`from memory cache`/`from disk cache`) 또는 validator+`304`

| `Protocol` 열 | cache 신호 | 첫 분류(먼저 내릴 결론) | 자주 하는 오해 |
|---|---|---|---|
| `h2`/`h3`/`http/1.1` | `from memory cache` 또는 `from disk cache` | 네트워크 전송보다 cache 재사용 판독을 우선 | protocol이 보이니 이번에도 서버 왕복했다고 단정 |
| `h2`/`h3`/`http/1.1` | request에 validator + status `304` | 서버 재검증 후 기존 body 재사용 | `304`를 memory/disk hit와 같은 등급으로 묶음 |
| `h2`/`h3` + fallback 흔적 | cache hit 신호 없음, status `200` | 우선 protocol 협상/경로 이슈, cache 이슈는 2순위 | 모든 `200`을 cache miss 하나로만 설명 |

한 줄 규칙:

- `Protocol`은 "어떤 전송 경로였는지"를 말한다.
- cache 표기는 "body를 어디서 썼는지"를 말한다.
- 둘을 합쳐야 첫 판독이 틀어지지 않는다.

`Protocol` 열에 `h1` 대신 `http/1.1`이 보여도 초독해 기준에서는 같은 H1 버킷으로 먼저 묶어 읽으면 된다.
표기 차이 자체가 헷갈리면 [Browser DevTools `Protocol` 열 표기 차이 보조노트](./browser-devtools-protocol-column-labels-primer.md)를 먼저 보고 돌아오면 된다.

3줄 예시:

- `Status 304` + `Protocol h2` -> HTTP/2로 서버에 재검증까지 갔다.
- `Status 304` + `Protocol h3` -> HTTP/3로 서버에 재검증까지 갔다.
- 둘 다 결론은 같다: `h2`/`h3`는 전송 경로 차이이고, `304`는 "기존 cache body를 계속 써도 된다"는 확인이다.

---

## 1분 분리 체크리스트: `Protocol=h3` vs `from memory cache` vs `304`

이 장면에서 초급자가 가장 많이 섞는 것은 "길"과 "body 출처"다.

```text
Protocol=h3        -> 어떤 길로 갔는가
from memory cache  -> body를 브라우저 메모리에서 바로 썼는가
304 Not Modified   -> 서버에 다시 물어본 뒤 기존 body를 써도 된다고 확인받았는가
```

같은 층위로 읽지 않으려면 아래 3문장만 먼저 확인하면 된다.

1. `Protocol` 열은 body 출처가 아니라 전송 경로다.
2. `from memory cache`/`from disk cache`는 body 출처다.
3. `304`는 cache 저장 위치가 아니라 서버 재검증 결과다.

| 보이는 신호 | 먼저 답하는 질문 | 바로 내려도 되는 결론 | 아직 모르는 것 |
|---|---|---|---|
| `Protocol = h3` | 이번 요청이 어떤 HTTP 길로 갔나 | HTTP/3 경로를 탔다 | body를 서버에서 다시 받았는지 |
| `from memory cache` | body를 어디서 꺼냈나 | 브라우저 메모리 사본을 썼다 | 이번 row에서 서버 재검증이 있었는지 |
| `304 Not Modified` | 서버에 다시 물어본 결과가 무엇인가 | 기존 body를 계속 써도 된다고 확인받았다 | memory cache였는지 disk cache였는지 |

가장 짧은 판독 순서:

1. `Protocol`은 옆에 잠깐 두고 `Size`/badge에 `from memory cache`나 `from disk cache`가 있는지 먼저 본다.
2. cache 표기가 없으면 `Headers`에서 `If-None-Match`/`If-Modified-Since`와 `304`를 본다.
3. 마지막에 "`그 재사용 또는 재검증이 h2였나 h3였나`"를 `Protocol`로 붙인다.

짧은 예시:

| 장면 | 첫 해석 |
|---|---|
| `Protocol=h3` + `from memory cache` | H3가 보여도 body는 로컬 메모리 사본이다 |
| `Protocol=h3` + `304` | H3로 서버 재검증까지 갔고 body는 기존 cache 사본을 다시 쓴다 |
| `Protocol=h3` + `200` | H3로 실제 새 body를 내려받았을 가능성을 먼저 본다 |

자주 하는 오해:

- `Protocol=h3`를 보고 "`이번에도 서버가 body를 줬다`"라고 단정한다.
- `from memory cache`와 `304`를 둘 다 "cache hit" 한 단어로 뭉뚱그린다.
- `304`를 memory cache의 하위 종류처럼 설명한다.

이 세 줄을 분리해 읽으면 `Protocol=h3`와 `from memory cache`/`304`를 같은 칸에서 비교하는 실수를 크게 줄일 수 있다.

---

## memory cache 읽는 법

`memory cache`는 브라우저가 이미 메모리에 들고 있는 응답 사본을 다시 쓰는 경우다.

실전 해석 포인트:

- row에 `from memory cache` 같은 표기가 보인다
- request가 네트워크로 실제 전송되지 않은 것처럼 보일 수 있다
- waterfall이 매우 짧거나 사실상 즉시 끝난다
- `If-None-Match`, `If-Modified-Since` 같은 validator request가 없다

이때 중요한 점:

- 브라우저가 "이건 아직 fresh하다"고 판단했기 때문에 바로 재사용한 것이다
- 즉 이 순간은 `304`가 아니라 재검증 자체를 생략한 cache hit다

대체로 memory cache는 최근 탐색, 같은 renderer/process 경로에서 더 자주 보인다. 다만 정확한 저장 tier 선택은 브라우저 구현 세부사항이라, HTTP spec 자체가 memory/disk를 직접 구분하는 것은 아니다.

---

## disk cache 읽는 법

`disk cache`는 브라우저가 로컬 디스크에 저장한 사본을 다시 쓰는 경우다.

실전 해석 포인트:

- row에 `from disk cache` 같은 표기가 보인다
- waterfall은 네트워크 왕복보다 훨씬 짧지만, memory cache보다는 약간 다르게 보일 수 있다
- request header에 validator가 없고, 서버에 재검증한 흔적도 없다

이 경우도 본질은 같다.

- 브라우저가 fresh 판단을 내렸기 때문에
- 서버에 묻지 않고 저장된 body를 바로 사용한다

즉 `disk cache`도 `304`와 다르다.
`disk cache`는 서버 미도달 재사용, `304`는 서버 왕복 후 재사용이다.

---

## revalidation과 304 읽는 법

이 구간이 가장 실무적이다.

브라우저는 cached response가 stale해졌거나, `Cache-Control: no-cache`처럼 재검증이 필요한 정책이면 조건부 요청을 보낸다.

대표 request header:

- `If-None-Match`
- `If-Modified-Since`

대표 response:

- 변경 없음: `304 Not Modified`
- 변경 있음: `200 OK` + 새 body

### 조건부 요청 trace 모양

```http
GET /app.js HTTP/1.1
If-None-Match: "app-v12"
If-Modified-Since: Tue, 14 Apr 2026 09:00:00 GMT
```

```http
HTTP/1.1 304 Not Modified
ETag: "app-v12"
Cache-Control: max-age=60
```

이때 읽는 법은 단순하다.

- request가 나갔다 = 서버 왕복이 있었다
- status가 `304`다 = 서버가 "네 캐시 사본 계속 써라"라고 확인했다
- body는 `304` 응답 body가 아니라 예전 cache body를 쓴다

즉 `304`는 body 다운로드를 줄인 것이지, 네트워크를 완전히 없앤 것은 아니다.

### DevTools에서 확인할 신호

- `Headers`의 request 쪽에 `If-None-Match` / `If-Modified-Since`가 보인다
- response status가 `304`다
- transfer size는 작아도, 최종 렌더링에 쓰인 body는 기존 cache 사본이다

### 304와 200을 가르는 질문

브라우저가 재검증을 보낸 뒤 결과는 둘 중 하나다.

- 리소스가 안 바뀌었으면 `304`
- 리소스가 바뀌었으면 `200` + 새 body

따라서 `304`는 cache correctness를 유지하면서 body 전송을 줄이는 경로라고 읽으면 된다.

---

## 왜 304인데 Response 탭에 body가 보이나

초급자 혼선은 보통 여기서 생긴다.

- wire에서 온 `304` 응답 자체는 보통 body가 없다
- 하지만 브라우저는 예전에 저장해 둔 body를 이미 가지고 있다
- DevTools는 "이번 status line"과 "최종 렌더링에 쓰인 body"를 같이 보여 줄 수 있다

즉 DevTools가 body를 보여 줘도, 그 body가 이번 `304` 응답에서 새로 내려온 것은 아닐 수 있다.

가장 쉬운 멘탈 모델은 아래 두 칸이다.

| 지금 보는 것 | 실제 의미 |
|---|---|
| `Status = 304` | 서버가 "네가 가진 사본 계속 써라"라고 확인 |
| `Response` 탭의 내용 | 브라우저가 저장해 둔 기존 body를 펼쳐 보여 준 것일 수 있음 |

짧은 예시:

1. 첫 요청에서 `/app.js`를 `200`으로 받고 body를 cache에 저장한다.
2. 다음 요청에서 브라우저가 `If-None-Match`를 붙여 재검증한다.
3. 서버는 `304 Not Modified`만 돌려준다.
4. 브라우저는 방금 받은 `304`를 렌더링하지 않고, 예전에 저장한 `/app.js` body를 다시 쓴다.
5. 그래서 DevTools `Response` 탭에는 내용이 보일 수 있다.

이 장면에서는 "body가 보인다"와 "이번 응답에 body가 실렸다"를 분리해야 한다.

- 궁금한 질문 A: 서버가 새 body를 보냈나
- 궁금한 질문 B: 브라우저가 화면에 어떤 body를 썼나

`304`에서는 보통 A는 아니고, B는 예전 cached body다.

---

## 2분 실험 예시

같은 `app.js` 하나만으로도 memory/disk/304/200을 분리해 볼 수 있다.

| 순서 | 내가 한 동작 | 예상 신호 | 초급자 해석 |
|---|---|---|---|
| 1 | 첫 접속 | `200 OK` + body download | 원본을 네트워크에서 처음 받음 |
| 2 | 일반 reload | `from memory cache` 또는 `from disk cache` | fresh hit라 서버 재확인을 생략 |
| 3 | 재검증이 필요한 상태에서 재요청 | request validator + `304` | 서버 확인 후 기존 body 재사용 |
| 4 | 서버 배포 후 재요청 | `200 OK` + 새 validator | 재검증 결과가 바뀌어 새 사본으로 교체 |

핵심은 동작별로 질문을 분리하는 것이다.

- "서버에 갔나?" -> request validator(`If-None-Match`/`If-Modified-Since`) 유무
- "body를 다시 받았나?" -> `304` vs `200`

---

## Disable cache ON/OFF를 따로 봐야 하는 이유

초급자 재현 실수는 여기서 가장 많이 생긴다.

- `Disable cache` OFF는 자연 cache 동작을 보는 모드다
- `Disable cache` ON은 cache 재사용을 일부러 꺼 보는 실험 모드다

즉 같은 URL이라도 아래 두 문장은 전혀 다르다.

- "평소에는 `memory cache`로 재사용된다"
- "`Disable cache`를 켜서 이번에는 네트워크로 다시 갔다"

실험 순서를 짧게 고정하면 덜 헷갈린다.

1. OFF에서 첫 요청을 본다
2. OFF에서 같은 URL을 한 번 더 봐서 natural hit/`304`를 확인한다
3. ON으로 바꿔 cache hit 표기가 어떻게 사라지는지 본다

이 3단계만 따로 정리한 카드가 필요하면 [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)를 먼저 보고 오면 된다.

---

## 실전 추적 순서

아래 순서로 보면 브라우저 cache trace를 빠르게 분해할 수 있다.

### 1. 자연 상태 먼저 본다

- DevTools를 열고 `Disable cache`는 끈다
- 첫 요청, 일반 reload, hard reload를 분리해서 본다

### 2. 같은 URL row를 2~3회 비교한다

질문은 네 가지면 충분하다.

- 두 번째 요청이 아예 서버에 안 갔는가
- validator request가 붙었는가
- `304`가 왔는가
- 아니면 다시 `200` body를 받았는가

### 3. Headers에서 freshness와 validator를 같이 본다

response 쪽:

- `Cache-Control`
- `ETag`
- `Last-Modified`
- `Age`
- `Vary`

request 쪽:

- `If-None-Match`
- `If-Modified-Since`
- `Cache-Control` request override가 있는지

### 4. 서버 로그 유무와 같이 대조한다

- `memory cache` / `disk cache`면 서버 access log가 없을 수 있다
- `304`면 서버 로그가 남아야 한다
- `200 revalidation miss`면 서버가 새 body를 다시 보냈다

### 5. 강제 우회와 자연 동작을 섞지 않는다

- `Disable cache` 켠 상태
- hard reload
- query string 바꾸기

이 셋은 모두 cache 동작을 크게 바꾼다. 문제 재현 중에는 "자연 hit", "강제 bypass", "재검증"을 서로 다른 실험으로 분리해야 한다.

---

## 자주 헷갈리는 포인트

### `304`는 cache hit지만, 서버 미도달 hit는 아니다

`304`는 cached body를 재사용하므로 넓게 보면 cache 활용이다.
하지만 서버까지 갔다 왔다는 점에서 `memory cache`/`disk cache`와 다르다.

### `memory cache`와 `disk cache`는 HTTP 헤더 이름이 아니다

이 둘은 브라우저 구현 계층 이름이다.
HTTP spec이 `memory cache`/`disk cache` 헤더를 주는 것은 아니다.

### DevTools의 `Response` 탭이 body를 보여 줘도 304 body라고 단정하면 안 된다

`304` 자체는 보통 body가 없다.
DevTools가 보여 주는 내용은 기존 cache 사본을 렌더링한 결과일 수 있다.
그래서 `Status`는 이번 서버 확인 결과로, `Response` 탭 내용은 브라우저가 재사용한 기존 body로 따로 읽는 습관이 필요하다.

### `Protocol=h3`를 보고 cache 원인까지 단정하면 안 된다

- `Protocol=h3`는 "`이번 요청이 H3 경로를 탔다`"는 뜻이다.
- 하지만 그 row가 새 body 다운로드였는지, `304` 재검증이었는지, local cache reuse였는지는 별도 판독이다.
- `Alt-Svc`, HTTPS RR/SVCB, 첫 요청/다음 새 연결 타임라인까지 읽어야 하면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)로 이어 본다.

### `no-cache`는 저장 금지가 아니다

저장은 해도 되지만, 사용 전에 재검증해야 한다.
그래서 `no-cache` 응답은 DevTools에서 반복적으로 `304` 패턴을 만들 수 있다.

### hard reload는 자연스러운 사용자 흐름이 아니다

hard reload는 cache를 우회하거나 재검증 방식을 바꿔 버릴 수 있다.
실사용자 체감과 같은 현상을 보고 싶다면 일반 탐색/일반 reload를 먼저 본다.

### Service Worker 경로와 브라우저 HTTP cache를 혼동하지 않는다

row가 `from ServiceWorker` 같은 표면을 보이면 이 문서의 memory/disk/304 해석과는 다른 계층이 개입했을 수 있다.

첫 분기만 빠르게 잡고 싶다면 [Service Worker 혼선 1분 분기표: `from ServiceWorker` vs HTTP cache](./service-worker-vs-http-cache-devtools-primer.md)를 먼저 보고 돌아오면 된다.

---

## 다음에 이어서 볼 문서

- freshness/validator 기본을 다시 묶어 보고 싶다면 [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `Disable cache` ON/OFF를 같은 URL 기준 3단계로 재현하고 싶다면 [Browser DevTools `Disable cache` ON/OFF 실험 카드](./browser-devtools-disable-cache-on-off-experiment-card.md)
- `max-age`, `no-cache`, `immutable` 같은 directive 차이를 더 보고 싶다면 [Cache-Control 실전](./cache-control-practical.md)
- `Vary`나 언어/압축 variant 때문에 trace가 갈라지면 [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
- 운영형 edge case까지 확장하려면 [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)
- H3 discovery/Alt-Svc 관찰과 cache trace가 섞여 헷갈리면 [H3 Discovery Observability Primer](./h3-discovery-observability-primer.md)

---

## 면접에서 자주 나오는 질문

### Q. `memory cache`와 `304 Not Modified`의 차이는 무엇인가요?

- `memory cache`는 브라우저가 서버에 가지 않고 메모리 사본을 바로 재사용한 경우다.
- `304 Not Modified`는 브라우저가 조건부 요청을 보내고, 서버가 기존 사본을 계속 써도 된다고 확인한 경우다.

### Q. DevTools에서 어떤 신호를 보면 재검증 여부를 알 수 있나요?

- request header에 `If-None-Match`나 `If-Modified-Since`가 있는지 본다.
- 있으면 재검증 경로고, response가 `304`면 cached body 재사용이다.

### Q. `disk cache`와 `memory cache` 차이는 HTTP semantics 차이인가요?

- 아니다. 둘 다 브라우저 cache tier 차이에 가깝다.
- HTTP 관점에서 더 중요한 것은 fresh hit인지, 재검증이 필요한지, validator가 무엇인지다.

### Q. 왜 `304`인데도 서버 로그가 남나요?

- 브라우저가 조건부 요청을 실제로 서버로 보냈기 때문이다.
- 서버는 body 대신 "안 바뀜"만 응답했을 뿐, 요청은 처리했다.

## 한 줄 정리

`Protocol=h3`는 "어떤 길로 갔나", `from memory cache`는 "body를 어디서 꺼냈나", `304`는 "서버가 기존 body 재사용을 확인했나"를 말한다.
