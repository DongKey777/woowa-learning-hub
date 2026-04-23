# Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기

**난이도: 🟢 Beginner**

> 브라우저 Network 탭에서 `memory cache`, `disk cache`, `revalidation`, `304 Not Modified`를 실제 요청 trace 기준으로 구분해 읽는 실전 primer

> 관련 문서:
> - [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
> - [Cache-Control 실전](./cache-control-practical.md)
> - [Vary와 Content Negotiation 기초: 언어, 압축, 응답 variant](./vary-content-negotiation-basics-language-compression.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

retrieval-anchor-keywords: browser devtools cache trace, chrome devtools cache, memory cache, disk cache, browser cache revalidation, 304 devtools, conditional request trace, from memory cache, from disk cache, disable cache, hard reload, if-none-match, if-modified-since

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [먼저 기억할 핵심 구분](#먼저-기억할-핵심-구분)
- [DevTools에서 먼저 켜 둘 것](#devtools에서-먼저-켜-둘-것)
- [한 번에 보는 trace 판독표](#한-번에-보는-trace-판독표)
- [memory cache 읽는 법](#memory-cache-읽는-법)
- [disk cache 읽는 법](#disk-cache-읽는-법)
- [revalidation과 304 읽는 법](#revalidation과-304-읽는-법)
- [실전 추적 순서](#실전-추적-순서)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

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

### `no-cache`는 저장 금지가 아니다

저장은 해도 되지만, 사용 전에 재검증해야 한다.  
그래서 `no-cache` 응답은 DevTools에서 반복적으로 `304` 패턴을 만들 수 있다.

### hard reload는 자연스러운 사용자 흐름이 아니다

hard reload는 cache를 우회하거나 재검증 방식을 바꿔 버릴 수 있다.  
실사용자 체감과 같은 현상을 보고 싶다면 일반 탐색/일반 reload를 먼저 본다.

### Service Worker 경로와 브라우저 HTTP cache를 혼동하지 않는다

row가 `from ServiceWorker` 같은 표면을 보이면 이 문서의 memory/disk/304 해석과는 다른 계층이 개입했을 수 있다.

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
