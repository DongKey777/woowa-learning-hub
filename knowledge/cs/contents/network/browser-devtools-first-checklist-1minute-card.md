# Browser DevTools 첫 확인 체크리스트 1분판

**난이도: 🟢 Beginner**

> 한 줄 요약: DevTools 첫 화면에서는 `Status`를 장면 분류표처럼 먼저 읽고, `(failed)`·`(blocked)`·`canceled`는 "HTTP 상태코드가 아니라 브라우저가 붙인 짧은 메모"로 한 묶음 처리하면 첫 판독 혼동이 줄어든다.

> Network 탭에서 처음부터 모든 컬럼을 보지 않고, `Status`/`Protocol`/`Remote Address`/`Connection ID` 4개를 먼저 본 뒤 `421`/H3 장면에서만 `Response Alt-Svc` 한 칸을 작게 덧붙여 "지금은 cache 질문인지, 버전 질문인지, connection 재시도 질문인지"를 1분 안에 가르는 초급 미니 카드

관련 문서:

- [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- [Browser DevTools `Protocol` 열 표기 차이 보조노트](./browser-devtools-protocol-column-labels-primer.md)
- [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md)
- [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
- [CORS, SameSite, Preflight](../security/cors-samesite-preflight.md)

retrieval-anchor-keywords: devtools first checklist, browser devtools first check, status protocol remote address connection id, response alt-svc checklist, devtools 4 field checklist, network tab first read, beginner devtools card, same url two rows checklist, 421 beginner capture, protocol remote address quick check, connection id quick read, devtools one minute checklist, status special labels devtools, 304 h3 devtools, 304 over h3 duplicate fetch

<details>
<summary>Table of Contents</summary>

- [먼저 잡는 멘탈 모델](#먼저-잡는-멘탈-모델)
- [1분 관찰 순서](#1분-관찰-순서)
- [Status 특수 표기 먼저 묶기](#status-특수-표기-먼저-묶기)
- [4칸이 각각 답하는 질문](#4칸이-각각-답하는-질문)
- [`304`와 `Protocol`을 같이 읽는 미니 카드](#304와-protocol을-같이-읽는-미니-카드)
- [H3/421에서만 붙이는 미니 체크](#h3421에서만-붙이는-미니-체크)
- [아주 작은 예시](#아주-작은-예시)
- [자주 헷갈리는 포인트](#자주-헷갈리는-포인트)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)

</details>

## 먼저 잡는 멘탈 모델

처음부터 header 전체를 파지 말고, Network 탭을 **공항 전광판**처럼 보면 된다.

- `Status`는 "이번 줄 결과가 성공/재검증/거절 중 무엇인가"
- `Protocol`은 "어떤 길로 갔는가"
- `Remote Address`는 "어느 목적지로 붙었는가"
- `Connection ID`는 "같은 연결을 다시 썼는가, 새 연결인가"

초보자 첫 판독은 이 4개만으로도 충분하다.

```text
결과(Status) -> 길(Protocol) -> 목적지(Remote Address) -> 같은 차편인가(Connection ID)
```

한 줄 요약:

- 지금 줄의 의미를 먼저 가르고
- 자세한 header/body는 그 다음에 본다

## 1분 관찰 순서

### 1. `Status`부터 본다

첫 질문은 "무슨 종류의 장면인가"다.

| `Status`에서 먼저 보이는 것 | 초급자 첫 결론 |
|---|---|
| `200` | 일단 정상 응답 줄이다 |
| `304` | cache 재검증 줄일 수 있다 |
| `403`/`404` | app/auth/route 질문일 수 있다 |
| `421` | connection 재사용 질문일 수 있다 |

브라우저가 HTTP 숫자 대신 짧은 메모를 붙이는 줄도 있다.
이때는 "서버 응답 코드"보다 "브라우저가 요청을 끝내지 못한 장면"으로 먼저 묶는 편이 안전하다.

## `Status` 특수 표기 먼저 묶기

| `Status` 표기 | 초급자용 첫 묶음 | 첫 질문 |
|---|---|---|
| `(failed)` | 요청 실패 메모 | 네트워크/취소/브라우저 오류로 응답 숫자를 못 받은 것인가 |
| `(blocked)` | 브라우저 차단 메모 | 확장 프로그램, mixed content, CORS/정책 차단인가 |
| `canceled` | 요청 취소 메모 | 페이지 이동, 새로고침, JS abort로 중간에 끊겼나 |

짧게 외우면 이렇게 보면 된다.

- 괄호가 붙은 `(failed)`·`(blocked)`는 HTTP `404` 같은 서버 숫자와 다른 부류다
- `canceled`도 보통 "서버가 에러 코드를 줬다"보다 "브라우저 쪽에서 중간 종료됐다"에 가깝다
- 그래서 이 셋을 보면 app status 해석보다 취소·차단·브라우저 실패 문맥을 먼저 본다

작은 비교 한 줄:

| 보이는 값 | 먼저 읽는 법 |
|---|---|
| `404` | 서버가 `404`를 응답했다 |
| `(blocked)` | 브라우저가 요청을 막아서 숫자 응답을 못 봤을 수 있다 |

### 2. `Protocol`을 붙여 본다

둘째 질문은 "어떤 HTTP 길을 탔는가"다.

| `Protocol`에서 먼저 보이는 것 | 초급자 첫 결론 |
|---|---|
| `h1`/`http/1.1` | H1 계열로 읽는다 |
| `h2` | HTTP/2로 읽는다 |
| `h3` | HTTP/3로 읽는다 |

여기서 중요한 점:

- `Protocol`은 cache 여부를 말하지 않는다
- `Status 304`와 `Protocol h2/h3`는 같이 볼 수 있다

### 3. `Remote Address`를 본다

셋째 질문은 "같은 URL이라도 어디로 붙었는가"다.

| `Remote Address` 관찰 | 초급자 첫 결론 |
|---|---|
| 같은 URL 두 줄의 주소가 같다 | 같은 목적지일 가능성이 크다 |
| 같은 URL 두 줄의 주소가 다르다 | 다른 edge/backend/path로 다시 간 것일 수 있다 |

### 4. `Connection ID`를 마지막에 본다

넷째 질문은 "같은 connection 재사용인가, 새 connection인가"다.

| `Connection ID` 관찰 | 초급자 첫 결론 |
|---|---|
| 같은 값 | 같은 연결 재사용 가능성이 크다 |
| 다른 값 | 새 연결 재시도나 recovery 가능성이 있다 |
| 브라우저에 컬럼이 없다 | `Remote Address`와 시간 순서를 대신 본다 |

## 4칸이 각각 답하는 질문

| 칸 | 답하는 질문 | 여기서 바로 내릴 수 있는 1차 판단 |
|---|---|---|
| `Status` | 성공인가, 재검증인가, 거절인가 | cache/app/connection 중 어디부터 볼지 고른다 |
| `Protocol` | H1/H2/H3 중 어느 길인가 | 버전 전환 질문인지 아닌지 고른다 |
| `Remote Address` | 어느 목적지에 붙었나 | 같은 URL 두 줄이 같은 서버 문맥인지 본다 |
| `Connection ID` | 같은 연결을 다시 썼나 | 브라우저 recovery와 중복 호출을 가르는 근거로 쓴다 |

초보자용 가장 짧은 순서는 아래처럼 외우면 된다.

1. `Status`로 장면 종류를 고른다.
2. `Protocol`로 길을 붙인다.
3. `Remote Address`로 목적지 변화를 본다.
4. `Connection ID`로 같은 연결인지 새 연결인지 본다.

## `304`와 `Protocol`을 같이 읽는 미니 카드

초보자가 자주 틀리는 장면이 `Status = 304`, `Protocol = h3` 한 줄이다.

먼저 이렇게 분리해서 읽으면 된다.

- `304`는 "서버가 기존 body를 계속 써도 된다고 답했다"는 뜻이다.
- `h3`는 "그 재검증 요청이 HTTP/3 길로 갔다"는 뜻이다.

즉 `304 over h3`는 보통 아래 둘을 **같이** 말할 뿐이다.

1. 서버에 재검증 요청은 갔다.
2. 그 길이 HTTP/3였다.

이 한 줄만으로 바로 결론 내리면 안 되는 것:

- `h3`라서 `h2`에서 `h3`로 downgrade/upgrade가 일어났다고 단정
- 같은 URL이 두 줄 보인다고 duplicate fetch라고 단정

짧은 비교표:

| 보이는 조합 | 먼저 내릴 결론 | 아직 모르는 것 |
|---|---|---|
| `304` + `h3` | H3로 재검증했다 | 같은 연결 재사용인지, 새 연결인지 |
| `304` + `h2` | H2로 재검증했다 | duplicate fetch인지 |
| `200` + `h3` | H3로 실제 응답을 받았다 | cache miss인지, resource 변경 때문인지 |

한 줄 체크 순서:

1. `Status 304`면 먼저 cache 재검증 장면으로 묶는다.
2. `Protocol h3`는 그다음에 "어느 길로 재검증했는가"만 덧붙인다.
3. duplicate fetch나 recovery 판단은 `Connection ID`, 시간 순서, 같은 URL 반복 여부로 따로 본다.

## H3/421에서만 붙이는 미니 체크

기본은 4칸으로 충분하다.
다만 같은 URL에서 `421 -> 200/403/404`가 보이면 `Headers`에서 아래 3개만 한 번 더 확인하면 오분류가 크게 줄어든다.

| 추가 확인 칸 | 초급자 질문 | 빠른 읽는 법 |
|---|---|---|
| `Protocol` | H3/H2 중 어떤 길로 복구됐나 | 첫 줄과 둘째 줄의 protocol이 같아도 `Connection ID`가 바뀌면 recovery일 수 있다 |
| `Connection ID` | 진짜 새 연결로 갈아탔나 | 같으면 같은 연결 재사용 후보, 다르면 recovery 근거가 강해진다 |
| `Response Alt-Svc` | 서버가 다음 H3 길 안내를 광고했나 | `Alt-Svc: h3=\"...\"`가 보이면 discovery 힌트가 있었는지 같이 적어 둔다 |

한 줄 메모 템플릿:

- "`Protocol`/`Connection ID`는 trace 표에서 보고, `Response Alt-Svc`는 row 상세 `Headers`에서 확인한다."
- "`Alt-Svc`가 있으면 discovery 힌트가 있었다는 뜻이지, 그 줄 자체가 recovery 성공이라는 뜻은 아니다."

## 아주 작은 예시

같은 URL이 두 줄 보였다고 하자.

| URL | Status | Protocol | Remote Address | Connection ID | 첫 판독 |
|---|---:|---|---|---:|---|
| `/api/me` | `421` | `h3` | `203.0.113.10:443` | `18` | 첫 줄은 wrong-connection 거절 후보 |
| `/api/me` | `200` | `h3` | `203.0.113.25:443` | `24` | 둘째 줄은 새 connection recovery 뒤 성공 후보 |

이 표에서 초보자가 바로 말할 수 있는 것은 두 가지다.

- `421` 다음 줄이므로 app 권한보다 connection 질문을 먼저 본다
- `Remote Address`와 `Connection ID`가 둘 다 바뀌었으니 그냥 같은 줄 반복 표기보다 새 연결 재시도 쪽 근거가 강하다

반대로 아래 장면이면 읽는 법이 달라진다.

| URL | Status | Protocol | Remote Address | Connection ID | 첫 판독 |
|---|---:|---|---|---:|---|
| `/api/me` | `200` | `h2` | `203.0.113.25:443` | `24` | 정상 응답 |
| `/api/me` | `200` | `h2` | `203.0.113.25:443` | `24` | 중복 호출 가능성을 먼저 본다 |

즉 같은 URL 두 줄이라도, 먼저 보는 것은 "두 줄이 있다는 사실"이 아니라 **4칸 조합**이다.

## 자주 헷갈리는 포인트

### `(failed)`·`(blocked)`·`canceled`를 `404` 같은 HTTP 상태코드처럼 읽는다

아니다.

- 이 셋은 초급자 기준으로 먼저 "브라우저 메모"로 묶는다
- 숫자 status가 없으면 서버 business 응답보다 차단/취소/전송 실패를 먼저 본다
- 특히 `(blocked)`는 policy나 browser-side block 가능성을 먼저 의심하는 편이 빠르다

### `Protocol`을 cache 신호처럼 읽는다

아니다.

- `Protocol`은 길
- cache는 `304`, `from memory cache`, `from disk cache` 쪽 신호다
- 그래서 `304 over h3`는 "H3로 재검증"이지, `h3` 자체가 cache 종류를 뜻하는 것은 아니다

### `421`을 보면 바로 auth 문제라고 생각한다

초급자 첫 분기는 보통 반대다.

- `421`은 connection 문맥 질문을 먼저 본다
- `403`/`404`는 app/auth/route 질문을 먼저 본다

### `Connection ID`가 없으면 아무것도 못 본다고 생각한다

아니다. 아래 순서로 대체하면 된다.

1. 같은 URL 두 줄인지 본다
2. `Status` 순서를 본다
3. `Remote Address`가 바뀌는지 본다
4. 필요하면 관련 deep dive로 내려간다

## 다음에 이어서 볼 문서

- response headers가 비는 `(blocked)`/`canceled`/`(failed)` 줄을 따로 읽고 싶다면 [Browser DevTools `(blocked)` / `canceled` / `(failed)` 입문](./browser-devtools-blocked-canceled-failed-primer.md)
- 응답 헤더의 `Server`/`Via`/`X-Request-Id`로 browser/proxy/app 1차 분기를 더 빨리 하고 싶다면 [Browser DevTools `Server` / `Via` / `X-Request-Id` 1분 헤더 카드](./browser-devtools-gateway-error-header-clue-card.md)
- `Protocol` 표기 자체가 헷갈리면 [Browser DevTools `Protocol` 열 표기 차이 보조노트](./browser-devtools-protocol-column-labels-primer.md)
- `304`와 cache 판독이 먼저 필요하면 [Browser DevTools Cache Trace Primer: memory cache, disk cache, revalidation, 304 읽기](./browser-devtools-cache-trace-primer.md)
- 같은 URL `421 -> 200`/`421 -> 403` 판독으로 바로 이어 가려면 [HTTP/3 421 Observability Primer: DevTools와 Edge Log로 Coalescing Recovery 읽기](./http3-421-observability-primer.md)

## 한 줄 정리

DevTools 첫 판독에서는 `Status`를 장면 분류표처럼 먼저 읽고, `(failed)`·`(blocked)`·`canceled`는 HTTP 상태코드가 아니라 브라우저 메모로 한 묶음 처리한 뒤 `Protocol`/`Remote Address`/`Connection ID`를 붙이면 초급자 오독이 크게 줄어든다.
