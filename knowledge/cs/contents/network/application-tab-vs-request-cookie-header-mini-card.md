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

retrieval-anchor-keywords: application tab cookie but no request cookie, request cookie header empty, cookie stored but not sent, application cookies vs network cookie, devtools cookie stored vs sent, why cookie header is empty, application cookies 있는데 요청에는 없음, cookie header 왜 비어요, browser cookie debug basics, stored vs sent cookie beginner, fetch credentials cookie missing, domain path samesite secure cookie

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

## 30초 디버깅 순서

1. 실패한 **같은 요청 row**를 연다.
2. `Application > Cookies`에서 cookie 이름과 `Domain`/`Path`/`SameSite`/`Secure`를 본다.
3. `Network > Request Headers > Cookie`가 비었는지 본다.
4. 비어 있으면 요청 URL, 스킴, 서브도메인, `fetch credentials`를 cookie 속성과 비교한다.
5. `Cookie`가 실렸다면 그다음부터는 브라우저 문제가 아니라 서버 세션 복원이나 인증 매핑 문제로 본다.

포인트는 "저장소 화면"과 "실패한 실제 요청"을 반드시 같은 턴에 맞춰 보는 것이다. `Application` 탭만 보고 있으면 과거에 저장된 cookie row 때문에 오진하기 쉽다.

## 흔한 오해와 함정

- `HttpOnly`라서 request `Cookie`가 비는 것은 아니다. `HttpOnly`는 JS 읽기만 막는다.
- `Application > Cookies`에 보인다고 그 요청에 자동 전송되는 것은 아니다.
- request `Cookie`가 비어 있으면 CORS 응답 읽기보다 먼저 cookie scope와 `credentials`를 본다.
- request `Cookie`가 이미 있다면 `SameSite` 추측을 멈추고 서버 쪽 인증 복원으로 넘어가는 편이 빠르다.

## 더 깊이 가려면

- 저장소 화면 전체를 먼저 읽고 싶으면 [Browser DevTools Application 탭 저장소 읽기 1분 카드](./browser-devtools-application-storage-1minute-card.md)
- cookie 자동 전송 흐름 자체를 다시 잡으려면 [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- `SameSite`, `Domain`, `Path`, `Secure` 의미를 속성별로 보려면 [Cookie Attribute Matrix: SameSite, HttpOnly, Secure, Domain, Path](./cookie-attribute-matrix-samesite-httponly-secure-domain-path.md)
- cross-origin `fetch`에서 `credentials`와 scope를 같이 보려면 [Fetch Credentials vs Cookie Scope](../security/fetch-credentials-vs-cookie-scope.md)
- 실전 증상 분기를 더 자세히 타려면 [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)

## 한 줄 정리

`Application > Cookies`는 저장 성공, request `Cookie` header는 전송 성공이므로 "cookie는 보이는데 요청에는 없다"면 cookie가 없어진 게 아니라 전송 조건이 안 맞는지부터 봐야 한다.
