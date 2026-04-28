# Browser DevTools `Protocol`, `Remote Address`, Connection Reuse 단서 입문

**난이도: 🟢 Beginner**

> 한 줄 요약: DevTools에서 `h3`가 같아 보여도 `Connection ID`가 같으면 기존 연결 재사용, 다르면 새 연결 가능성부터 먼저 본다.

> `Protocol` 열만 따로 읽지 말고, 같은 URL 두 줄에서 `Connection ID`와 `Status`를 붙여 보면 "버전 문제"와 "새 연결 recovery"를 더 빨리 분리할 수 있다.

관련 문서:

- [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) (main comparison primer)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md) (selection follow-up primer)
- [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)

retrieval-anchor-keywords: devtools protocol column, har export http/1.1, connection id reuse, h3 same connection, h3 new connection, remote address clue, protocol vs cache, copy paste protocol mismatch, browser network tab, http2 http3 basics, same url two rows, connection reuse checklist, beginner devtools reading, remote address connection id first check, reused connection first clue

<details>
<summary>Table of Contents</summary>

- [README에서 여기까지 오는 가장 짧은 길](#readme에서-여기까지-오는-가장-짧은-길)
- [먼저 잡는 멘탈 모델](#먼저-잡는-멘탈-모델)
- [먼저 외우는 4칸 역할](#먼저-외우는-4칸-역할)
- [가장 짧은 비교표](#가장-짧은-비교표)
- [같은 `h3`라도 다르게 읽는 미니 체크리스트](#같은-h3라도-다르게-읽는-미니-체크리스트)
- [브라우저별로 왜 달라 보이나](#브라우저별로-왜-달라-보이나)
- [짧은 incident 읽기 예시](#짧은-incident-읽기-예시)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)

</details>

## README에서 여기까지 오는 가장 짧은 길

README에서 네트워크 입문 흐름을 따라오다가 "H2/H3 비교는 알겠는데, DevTools에서 같은 `h3` 두 줄이 왜 다르게 보이지?"에서 멈추면 이 문서가 바로 다음 다리다.

가장 짧은 연결은 아래처럼 잡으면 된다.

| 지금 막힌 질문 | 먼저 볼 문서 | 여기로 돌아오는 이유 |
|---|---|---|
| Network 탭에서 뭘 먼저 봐야 할지 모르겠다 | [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md) | `Status`/`Protocol`/`Remote Address`/`Connection ID` 4칸을 먼저 익힌 뒤, 여기서 reused connection 단서를 더 촘촘히 읽는다 |
| H1/H2/H3 큰 차이가 아직 흐릿하다 | [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) | 버전 큰 그림을 잡은 뒤, 여기서 "같은 버전인데도 새 연결일 수 있다"를 읽는다 |
| `421 -> 200` trace를 바로 판독하고 싶다 | [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md) | 이 문서에서 `Connection ID` 감각을 잡고 내려가면 recovery 판독이 훨씬 쉬워진다 |

짧게 요약하면:

- README의 버전 route와 DevTools route 사이에서
- 이 문서는 "`Protocol`만 보지 말고 `Remote Address`와 `Connection ID`를 같이 보라"는 초급자용 미니 브리지다
- 특히 reused connection 단서는 `Connection ID`가 주신호이고, `Remote Address`는 보조 신호라는 감각을 먼저 심어 준다

## 먼저 잡는 멘탈 모델

Network 탭 1행은 "이번 요청이 어떤 길로, 어느 목적지로, 같은 연결을 재사용했는가"를 압축해서 보여 주는 한 줄 카드에 가깝다.

초급자는 먼저 아래 세 질문만 분리하면 된다.

1. `Protocol`: H1/H2/H3 중 어떤 길로 갔나
2. `Remote Address`: 어느 edge/IP:port로 붙었나
3. `Connection ID`: 같은 연결을 다시 썼나, 새 연결인가

이 세 칸을 함께 보면 HTTP/2/HTTP/3 incident 초입에서 아래를 빨리 가를 수 있다.

```text
버전 차이인가?
기존 연결 재사용인가?
421 뒤 새 연결 recovery인가?
```

한 줄 요약:

- `Protocol`은 길
- `Remote Address`는 목적지
- `Connection ID`는 같은 차편인지 새 차편인지
- cache hit, `304`, Service Worker 여부는 여전히 **다른 신호**다

초급자 메모 한 줄:

- 같은 `h3` 두 줄을 봤다면 "`버전은 이미 같다`"를 먼저 적고, 그다음 질문을 "`reused connection인가, 새 연결인가`"로 바꾸면 읽기가 빨라진다

---

## 먼저 외우는 4칸 역할

> [!IMPORTANT]
> 초급자 첫 판독에서는 아래 4칸만 먼저 외우면 incident 분기가 훨씬 빨라진다.
>
> - `Status`는 결과 종류
> - `Protocol`은 HTTP 길
> - `Remote Address`는 붙은 목적지
> - `Connection ID`는 같은 연결 재사용 여부

같은 row에서 질문을 둘로 나누면 더 안전하다.

| 지금 보는 신호 | 먼저 답하는 질문 | 초급자 첫 결론 |
|---|---|---|
| `Status 421` / `200` / `304` | 어떤 장면인가 | connection recovery, 정상 응답, cache 재검증 중 무엇인지 가른다 |
| `Protocol h2` / `Protocol h3` | 어떤 길로 갔나 | 전송 경로 차이다 |
| `Remote Address 203.0.113.10:443` | 어느 목적지로 붙었나 | 같은 URL 두 줄이 같은 edge인지 다른 edge인지 힌트를 준다 |
| `Connection ID 18` | 같은 연결인가 | 같은 ID면 재사용 후보, 다른 ID면 새 연결 후보다 |

작은 우선순위 규칙:

- connection reuse 여부는 `Connection ID`가 주신호다
- `Remote Address`는 보조 신호다
- `Protocol`이 바뀌지 않아도 `Connection ID`가 바뀌면 새 연결일 수 있다
- `Status 304`가 붙어 있으면 먼저 "`어느 길로 재검증했나`"로 읽고 cache body 질문은 분리한다

이 문서에서 계속 쓰는 가장 짧은 판독 문장은 이것이다.

```text
같은 Protocol -> Connection ID 먼저 -> Remote Address로 보강
```

---

## 가장 짧은 비교표

| 칸 | 보이는 예 | 먼저 읽는 뜻 | incident 초입 메모 |
|---|---|---|---|
| `Protocol` | `h1`, `http/1.1`, `h2`, `h3` | 어떤 HTTP 버전 길인가 | `h1 ≈ http/1.1`, `h2`와 `h3`는 실제 버전 차이 |
| `Remote Address` | `203.0.113.10:443` | 어느 edge/IP:port에 붙었나 | 주소가 바뀌면 recovery 근거가 강해진다 |
| `Connection ID` | `18`, `24` | 같은 연결 재사용인가 | 바뀌면 새 연결 재시도 후보 |
| `Status` | `200`, `304`, `421` | 어떤 장면인가 | `304`는 cache 재검증, `421`은 wrong-connection 후보 |

초독해 규칙은 이것만 먼저 기억하면 된다.

- `h1` vs `http/1.1`은 **표기 차이 먼저**
- `h2` vs `h3`는 **실제 버전 차이**
- `Connection ID`가 같으면 reuse 쪽, 다르면 recovery 쪽을 먼저 본다
- `Remote Address`는 바뀌면 읽기 쉬워지지만, 안 바뀌어도 recovery가 부정되진 않는다

---

## 같은 `h3`라도 다르게 읽는 미니 체크리스트

같은 `h3`라는 표기만으로는 "새 연결"인지 "기존 연결 재사용"인지 결정할 수 없다. 초급자는 아래 3줄만 먼저 확인하면 된다.

| 보이는 장면 | 먼저 볼 칸 | 초급자 1차 결론 |
|---|---|---|
| 두 줄 모두 `Protocol = h3` | `Connection ID` | 같으면 기존 H3 연결 재사용 후보 |
| 두 줄 모두 `Protocol = h3` | `Connection ID` | 다르면 새 H3 연결 또는 retry 후보 |
| `Connection ID`도 다름 | `Status`, `Remote Address` | `421 -> 200`이면 recovery 쪽 가설이 강해진다 |

짧게 외우면 이 순서다.

1. `Protocol`로 H2/H3 큰 버킷을 본다.
2. `Connection ID`로 같은 연결인지 새 연결인지 고정한다.
3. `Status`, `Remote Address`는 recovery 설명을 보강하는 증거로 붙인다.

작은 예시:

| URL | Status | Protocol | Connection ID | 첫 해석 |
|---|---:|---|---:|---|
| `/api/me` | `421` | `h3` | `18` | 첫 H3 연결이 거절된 장면 후보 |
| `/api/me` | `200` | `h3` | `24` | 같은 `h3`라도 새 연결 recovery 후보 |

핵심은 "`h3`가 같다"보다 "`Connection ID`가 같은가"가 더 직접적인 질문이라는 점이다.

그래서 README에서 이 문서를 만났다면 초급자는 먼저 아래 한 줄만 챙기면 된다.

- "`Protocol`은 버전 큰 그림, `Connection ID`는 reused connection 첫 단서, `Remote Address`는 보강 근거"

---

## 브라우저별로 왜 달라 보이나

브라우저가 다르다기보다, **DevTools UI가 어떤 약칭을 쓰는지**가 먼저 다를 수 있다.

| 브라우저/도구 계열 | 흔한 첫 표기 감각 | beginner가 내릴 첫 결론 |
|---|---|---|
| Chromium 계열 DevTools(Chrome/Edge) | `h2`, `h3`처럼 짧은 약칭을 자주 본다 | 약칭이어도 정식 버전 이름으로 읽으면 된다 |
| 다른 브라우저 DevTools/내보내기 뷰 | `http/1.1`처럼 풀 표기가 섞일 수 있다 | 풀 표기여도 `h1`과 같은 버킷으로 먼저 묶는다 |
| 브라우저/버전별 UI 차이 | 같은 버전이라도 컬럼 표시나 문자열이 조금 달라질 수 있다 | **철자 차이보다 의미 묶음**을 먼저 본다 |

복붙 비교에서 가장 많이 헷갈리는 장면은 이 조합이다.

| 보는 곳 | 흔한 표기 | 초급자 첫 해석 |
|---|---|---|
| DevTools `Protocol` 열 | `h1`, `h2`, `h3` | 화면용 짧은 약칭일 수 있다 |
| HAR export / 일부 access log | `http/1.1`, `h2`, `h3` | 저장용 풀 표기일 수 있다 |

즉 `h1`과 `http/1.1`이 나란히 보여도 먼저 "서로 다른 결과"가 아니라 "같은 HTTP/1.1을 다른 화면에서 적은 것"인지 확인하는 편이 안전하다.

핵심은 브라우저별 표기 차이를 "새로운 프로토콜이 또 있나?"로 읽지 않는 것이다.

- `h1`과 `http/1.1`이 따로 경쟁하는 개념은 아니다
- `h2`와 `h3`는 실제로 다른 프로토콜 버전이다
- 표기가 예상과 달라도 먼저 `HTTP/1.x / HTTP/2 / HTTP/3` 세 버킷으로 정리하면 초독해가 쉬워진다

---

## 짧은 incident 읽기 예시

같은 사이트를 보다가 아래처럼 보였다고 하자.

| URL | Status | Protocol | Remote Address | Connection ID | 첫 판독 |
|---|---:|---|---|---:|---|
| `/api/me` | `421` | `h3` | `203.0.113.10:443` | `18` | 첫 줄은 wrong-connection 거절 후보 |
| `/api/me` | `200` | `h3` | `203.0.113.25:443` | `24` | 둘째 줄은 새 연결 recovery 뒤 성공 후보 |

이때 초급자는 먼저 이렇게 말하면 된다.

- `Protocol`이 둘 다 `h3`여도 `Connection ID`가 바뀌었으니 같은 연결 재사용은 아니다
- `Remote Address`도 바뀌었으니 다른 edge/경로로 복구됐을 가능성이 더 강하다
- 이 장면의 핵심은 "`h3냐 h2냐`"보다 "`421 뒤 새 연결인가`"다

반대로 아래 장면이면 읽는 법이 다르다.

| URL | Status | Protocol | Remote Address | Connection ID | 첫 판독 |
|---|---:|---|---|---:|---|
| `/feed` | `304` | `h2` | `203.0.113.25:443` | `24` | HTTP/2로 재검증했다 |
| `/feed` | `200` | `h2` | `203.0.113.25:443` | `24` | 기존 H2 연결 재사용 후보 |

여기서는 먼저 이렇게 읽는다.

- `304`는 cache 재검증 신호다
- `Protocol h2`는 "HTTP/2로 재검증했다"는 뜻이지 cache hit 자체를 말하지 않는다
- 같은 `Connection ID`면 기존 H2 연결 재사용 쪽이 자연스럽다

---

## 자주 헷갈리는 포인트

### `h1`과 `http/1.1`을 다른 개념처럼 본다

초독해 단계에서는 같은 버킷으로 읽어도 된다.

### `Protocol` 열을 cache 신호로 읽는다

아니다.

- `h2`/`h3`/`http/1.1`은 전송 경로 신호
- `from memory cache`/`from disk cache`/validator/`304`는 cache 신호
- `Alt-Svc`는 다음 연결 힌트일 수 있지만, 이번 row의 body 출처를 단독으로 설명하지는 않는다

### `Remote Address`가 같으면 무조건 같은 연결이라고 생각한다

아니다.

- 주소가 같아도 새 연결일 수 있다
- 같은 URL 두 줄에서 **주신호는 `Connection ID`**, 주소는 보조 단서다

### 같은 사이트인데 어떤 줄은 `h2`, 어떤 줄은 `h3`라서 이상하다고 느낀다

기존 연결 재사용, 새 연결 생성, `Alt-Svc`, fallback 때문에 요청마다 다른 버전을 탈 수 있다. 이 자체가 바로 오류를 뜻하지는 않는다.

### `Connection ID`가 없으면 아무것도 못 읽는다고 생각한다

그렇지 않다.

1. 같은 URL 두 줄인지 본다
2. `Status` 순서를 본다
3. `Remote Address`가 바뀌는지 본다
4. 필요하면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)로 내려간다

### 표기가 달라 보이면 바로 브라우저 버그로 결론 낸다

먼저 아래 순서로 읽는 편이 안전하다.

1. `h1 ≈ http/1.1`로 묶기
2. cache 신호와 protocol 신호 분리하기
3. 정말 중요한 질문이 version change인지 cache change인지 고르기

### HAR와 DevTools를 복붙 비교하다가 `h1` vs `http/1.1`에서 멈춘다

이때는 문자열 자체보다 "같은 요청을 같은 버킷으로 묶었는가"를 먼저 본다.

- DevTools의 `h1`은 HAR의 `http/1.1`과 먼저 대응시킨다
- `h2`, `h3`는 보통 그대로 비교해도 된다
- 그다음에야 `Status`, `Connection ID`, `Remote Address` 비교로 넘어간다

---

## 다음에 이어서 볼 문서

- 4칸을 1분 순서로 바로 읽고 싶으면 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)
- README에서 바로 넘어온 상태라면 먼저 [Browser DevTools 첫 확인 체크리스트 1분판](./browser-devtools-first-checklist-1minute-card.md)에서 4칸 순서를 익히고, 다시 이 문서로 돌아와 `Connection ID` 우선순위만 고정하면 된다
- version 선택 자체가 궁금하면 [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- H1/H2/H3 차이를 큰 그림으로 먼저 잡으려면 [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
- connection reuse/coalescing 자체가 궁금하면 [HTTP/2와 HTTP/3 Connection Coalescing 입문](./http2-http3-connection-reuse-coalescing.md)
- `421 -> 200` / `421 -> 403` trace 판독은 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- DevTools에서 cache와 protocol을 같이 읽는 법은 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)

## 한 줄 정리

`Protocol`은 길을, `Connection ID`는 같은 연결인지 새 연결인지를 말하므로, 같은 `h3`라도 먼저 `Connection ID`를 같이 읽어야 초급자 오판이 줄어든다.
