# Application 탭에는 Cookie가 보이는데 Request `Cookie` 헤더는 비는 이유 미니 카드

> 한 줄 요약: `Application > Cookies`는 "브라우저에 저장됐는가"를 보여 주고, request `Cookie` 헤더는 "이번 요청에 실제로 전송됐는가"를 보여 줘서, 같은 cookie라도 저장 성공과 전송 성공은 따로 확인해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Network README](./README.md#browser-devtools-application-vs-request-cookie-header-미니-카드)
- [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
- [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)
- [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

retrieval-anchor-keywords: application tab cookie but no request cookie, request cookie header empty, cookie stored but not sent, application cookies vs network cookie, devtools cookie stored vs sent, why cookie header is empty, application cookies 있는데 요청에는 없음, cookie header 왜 비어요, browser cookie debug basics, stored vs sent cookie beginner, fetch credentials cookie missing, domain path samesite secure cookie, credentials omit vs domain path mismatch, 왜 application 탭에는 있는데 요청 헤더는 없어요, cookie stored but header empty why

## 핵심 개념

이 장면에서 먼저 고정해야 할 문장은 하나다.

- `Application > Cookies` = 저장 확인
- `Network > Request Headers > Cookie` = 전송 확인

초급자가 자주 하는 오해는 `Application > Cookies`에 값이 보이는 순간 "cookie는 정상"이라고 끝내는 것이다. 하지만 브라우저는 cookie를 저장했다고 해서 모든 요청에 자동으로 붙이지 않는다.

## 한눈에 보기

| DevTools 위치 | 답하는 질문 | 여기서 바로 확정 못 하는 것 |
|---|---|---|
| `Application > Cookies` | 브라우저가 cookie를 저장했나 | 이번 요청에 cookie를 실제로 보냈나 |
| `Network > Headers > Request Headers > Cookie` | 이번 요청에 cookie가 실렸나 | 서버가 그 cookie로 로그인 상태를 복원했나 |

가장 흔한 분기표는 이렇다.

| 보이는 장면 | 첫 해석 | 다음 확인 |
|---|---|---|
| `Application > Cookies`에도 없음 | 저장 단계 실패일 수 있다 | login 응답의 `Set-Cookie`와 브라우저 차단 이유 |
| `Application > Cookies`에는 있음, request `Cookie`는 비어 있음 | 저장은 됐지만 전송 조건이 안 맞을 수 있다 | `Domain`, `Path`, `SameSite`, `Secure`, `credentials` |
| request `Cookie`까지 있음 | 브라우저 전송은 통과했다 | 서버 세션 복원 또는 인증 로직 |

## 왜 저장돼 보여도 전송은 안 될까

브라우저는 요청 URL과 cookie 속성을 비교한 뒤에만 `Cookie` 헤더를 만든다. 그래서 저장된 cookie가 있어도 아래 조건 중 하나가 틀리면 이번 요청에는 빠질 수 있다.

- `Domain`: 다른 host라서 안 맞음
- `Path`: 요청 경로가 cookie 범위 밖임
- `SameSite`: cross-site 문맥이라 차단됨
- `Secure`: HTTPS가 아니라 차단됨
- `fetch(..., { credentials })`: cross-origin 요청인데 `include`가 빠짐

짧은 예시:

- `api.example.com`에 저장된 host-only cookie는 `app.example.com` 요청에 안 붙을 수 있다.
- `SameSite=Lax` cookie는 cross-site `fetch`나 `POST`에서 안 붙을 수 있다.
- `Secure` cookie는 `http://` 요청에 안 붙는다.

## 상세 분해

이 증상은 보통 아래 다섯 칸 중 하나로 정리된다.

| 원인 칸 | Application 탭에서는 왜 보여요? | Request `Cookie` 헤더는 왜 비어요? | 지금 바로 볼 것 |
|---|---|---|---|
| `Domain` 불일치 | 브라우저 저장 자체는 가능하다 | 이번 요청 host가 cookie 범위 밖이다 | 요청 URL host vs cookie `Domain` |
| `Path` 불일치 | 같은 host라면 저장 row는 계속 남아 있다 | 요청 path가 cookie 범위 밖이다 | `/api` 요청인데 cookie `Path=/auth` 같은지 |
| `SameSite`/`Secure` | 속성은 저장 metadata라서 Application에 그대로 보인다 | 현재 문맥이 cross-site이거나 HTTPS가 아니다 | top-level 이동인지 `fetch`인지, `https://`인지 |
| `credentials` 누락 | cookie는 저장돼 있다 | cross-origin `fetch`에서 브라우저가 credential 전송을 안 한다 | `fetch(..., { credentials: "include" })` 여부 |
| `credentials` 누락 vs cookie scope mismatch 구분 | 둘 다 Application row는 그대로 남아 있을 수 있다 | cross-origin `fetch` 전체에서 빠지면 `credentials` 쪽, `include`도 있는데 특정 host/path/site에서만 빠지면 scope 쪽일 가능성이 크다 | 요청이 cross-origin인지, `include`가 있는지, 같은 cookie가 다른 path나 host에서는 붙는지 |

초급자에게 가장 중요한 감각은 "Application 탭 row는 과거 저장 사실이고, request `Cookie` 헤더는 이번 요청 판정 결과"라는 점이다.

## 30초 디버깅 순서

1. 실패한 **같은 요청 row**를 연다.
2. `Application > Cookies`에서 cookie 이름과 `Domain`/`Path`/`SameSite`/`Secure`를 본다.
3. `Network > Request Headers > Cookie`가 비었는지 본다.
4. 비어 있으면 먼저 cross-origin `fetch`인지와 `credentials: "include"` 유무를 확인하고, 그다음 요청 URL, 스킴, 서브도메인, cookie 속성을 비교한다.
5. `Cookie`가 실렸다면 그다음부터는 브라우저 문제가 아니라 서버 세션 복원이나 인증 매핑 문제로 본다.

포인트는 "저장소 화면"과 "실패한 실제 요청"을 반드시 같은 턴에 맞춰 보는 것이다. `Application` 탭만 보고 있으면 과거에 저장된 cookie row 때문에 오진하기 쉽다.

## 실무에서 쓰는 모습

예를 들어 프런트가 `https://app.example.com`, API가 `https://api.example.com`인 SPA를 보자.

1. 로그인 응답에서 `Set-Cookie: SID=...; SameSite=None; Secure`가 내려온다.
2. `Application > Cookies > https://api.example.com`에는 `SID`가 보인다.
3. 그런데 프런트 코드가 `fetch("https://api.example.com/me")`만 호출하고 `credentials: "include"`를 빼먹었다.
4. 그러면 저장 row는 남아 있어도 실제 `/me` 요청의 `Cookie` 헤더는 비어 있을 수 있다.

이 장면에서 "cookie가 저장 안 됐다"가 아니라 "cross-origin 요청 전송 조건이 빠졌다"가 맞는 첫 해석이다.

## 흔한 오해와 함정

- `HttpOnly`라서 request `Cookie`가 비는 것은 아니다. `HttpOnly`는 JS 읽기만 막는다.
- `Application > Cookies`에 보인다고 그 요청에 자동 전송되는 것은 아니다.
- request `Cookie`가 비어 있으면 CORS 응답 읽기보다 먼저 `credentials missing`과 `cookie scope mismatch`를 따로 본다.
- request `Cookie`가 이미 있다면 `SameSite` 추측을 멈추고 서버 쪽 인증 복원으로 넘어가는 편이 빠르다.

## 더 깊이 가려면

- 저장소 화면 전체를 먼저 읽고 싶으면 [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)
- cookie 자동 전송 흐름 자체를 다시 잡으려면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- `SameSite`, `Domain`, `Path`, `Secure` 의미를 속성별로 보려면 [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
- cross-origin `fetch`에서 먼저 `credentials missing`을 자르려면 [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)
- `include`도 있는데 비는 장면을 scope로 좁히려면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

## 한 줄 정리

`Application > Cookies`는 저장 성공, request `Cookie` header는 전송 성공이므로 "cookie는 보이는데 요청에는 없다"면 cookie가 없어진 게 아니라 전송 조건이 안 맞는지부터 봐야 한다.
