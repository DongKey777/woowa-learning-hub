# Redirect vs Forward vs SPA Router Navigation 입문

> 한 줄 요약: 화면이 바뀌어도 이동 주체는 다를 수 있고, redirect는 브라우저의 새 요청, forward는 서버 내부 전달, SPA navigation은 자바스크립트 라우터 이동이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [network 카테고리 인덱스](./README.md)
- [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md)

retrieval-anchor-keywords: redirect vs forward basics, spa navigation basics, redirect forward 차이, 302 vs forward, why url changes after login, why url does not change after login, client side navigation beginner, login redirect confusion, browser new request redirect, spa router navigate basics, 처음 redirect 뭐예요, 헷갈려요 redirect forward, 왜 화면만 바뀌고 url은 그대로예요, what is redirect vs forward

## 핵심 개념

같은 "로그인 뒤 화면 이동"처럼 보여도 아래 셋은 다르다.

| 구분 | 누가 이동을 결정하나 | 브라우저 새 HTTP 요청 | 주소창 URL |
|---|---|---|---|
| redirect | 서버 응답의 `Location` | 있다 | 보통 바뀐다 |
| forward | 서버 내부 dispatcher/view | 없다 | 그대로인 경우가 많다 |
| SPA router navigation | 프론트엔드 JS/router | 페이지 이동 자체로는 없다 | 바뀔 수 있다 |

처음에는 "누가 이동을 결정했나"만 보면 된다.

## 10초 mental model

이동을 "택배 기사" 비유로 자르면 더 쉽다.

- redirect: 서버가 브라우저에게 "이 주소로 다시 가세요"라고 다시 심부름시킨다.
- forward: 서버가 받은 요청을 자기 안에서 다른 담당자에게 넘긴다.
- SPA navigation: 브라우저 안의 자바스크립트가 화면 전환을 정한다.

즉 beginner는 "`화면이 바뀌었다`"보다 "`누가 다시 움직였나`"를 먼저 묻는 편이 안전하다.

## 같은 장면을 세 칸으로 나눠 보기

| 겉으로 보이는 결과 | 실제 이동 주체 | DevTools에서 먼저 볼 단서 | 초보자용 해석 |
|---|---|---|---|
| 로그인 후 주소창이 `/home`으로 바뀌고 요청이 두 줄 보인다 | redirect | `302/303`, `Location`, 그다음 `GET /home` | 서버가 브라우저에게 다른 URL로 가라고 했다 |
| 화면은 홈처럼 보이는데 주소창이 여전히 `/login`이다 | forward | `3xx` 없이 요청 한 줄만 보인다 | 브라우저는 같은 요청 하나만 보냈다 |
| login API는 `200`인데 URL과 화면이 바뀐다 | SPA navigation | API 성공 뒤 라우터 이동 | 서버 redirect가 아니라 프론트가 이동시켰다 |

## redirect를 prg와 안 섞으려면 method 한 칸을 더 본다

beginner가 자주 묻는 "`왜 화면 이동인데 redirect랑 prg가 둘 다 나오죠?`"는 이동 주체 질문과 `post -> get` 질문이 섞인 경우가 많다. 이 문서에서는 이동 주체를 가르고, `method`가 같이 바뀌면 prg 문서로 한 칸 더 가면 된다.

| 지금 보인 변화 | 먼저 붙일 질문 | 여기서 답하는가 |
|---|---|---|
| `302/303`과 `Location`이 보인다 | 누가 브라우저를 다시 움직였는가 | 예, redirect 질문이다 |
| `post -> get`까지 같이 보인다 | 왜 결과 화면을 `get`으로 다시 열었는가 | 아니오, [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)로 이어진다 |
| `200` 뒤 프론트 라우터가 url을 바꾼다 | 서버가 아니라 js가 이동시켰는가 | 예, spa navigation 질문이다 |

짧게 말하면 이렇다.

- redirect 문서는 "`누가 이동시켰나`"를 답한다.
- prg 문서는 "`왜 `post` 뒤 `get`이 보이나`"를 답한다.

## 로그인 장면에서 가장 덜 헷갈리는 읽는 순서

처음에는 "`로그인 성공`"이라는 결과보다 `주소창`, `Network 줄 수`, `누가 이동을 시켰는가`를 이 순서로 보면 된다.

| 먼저 볼 것 | redirect 쪽 신호 | forward 쪽 신호 | SPA navigation 쪽 신호 |
|---|---|---|---|
| 주소창 | `/login`에서 `/home`으로 바뀐다 | 보통 `/login` 그대로다 | JS가 바꾸면 바뀔 수 있다 |
| Network 줄 수 | `POST /login` 뒤 `GET /home`이 한 줄 더 보인다 | 요청 한 줄만 보인다 | login API 한 줄 뒤 문서 이동 없이 화면만 바뀔 수 있다 |
| 이동 주체 | 서버 응답 `Location` | 서버 내부 dispatcher/view | 프론트 라우터 코드 |

짧게 고정하면 이렇다.

- 주소창과 요청이 둘 다 한 번 더 바뀌면 redirect부터 의심한다.
- 주소창이 그대로인데 화면만 달라지면 forward 가능성을 먼저 본다.
- API는 `200`인데 프론트가 알아서 넘기면 SPA navigation 질문이다.

## 처음 보는 사람용 10초 판별표

| 먼저 던질 질문 | `예`면 더 가까운 쪽 | `아니오`면 다음 질문 |
|---|---|---|
| 네트워크 탭에 `302/303`과 `Location`이 보이는가 | redirect | 주소창이 그대로인지 본다 |
| 주소창은 그대로인데 화면만 바뀌는가 | forward 가능성 | API 성공 뒤 JS가 이동했는지 본다 |
| login API는 `200`인데 새로고침 없이 URL이 바뀌는가 | SPA navigation | SSR/forward 문서로 한 칸 되돌아간다 |

## 새로고침이 왜 다르게 느껴질까

| 구분 | 브라우저가 마지막에 기억하는 것 | 새로고침 때 초보자용 해석 |
|---|---|---|
| redirect | redirect 뒤 도착한 `GET` | 보통 도착한 URL을 다시 연다 |
| forward | 처음 보낸 원래 요청 | 주소창은 그대로인데 같은 요청 결과를 다시 볼 수 있다 |
| SPA navigation | 현재 문서와 앱 상태 | 문서 새로고침이면 앱 상태가 다시 초기화될 수 있다 |

특히 "`POST` 다음에 왜 `GET`이 보여요?"가 같이 붙으면 이동 방식보다 [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)으로 먼저 가는 편이 안전하다.

## 자주 나오는 symptom 문장으로 바로 고르기

| learner 문장 | 먼저 볼 쪽 | 이유 |
|---|---|---|
| "`주소창도 바뀌고 Network에 두 줄이 보여요`" | redirect | 새 요청이 실제로 한 번 더 갔을 가능성이 높다 |
| "`화면은 바뀌었는데 주소창이 그대로예요`" | forward | 서버 안에서 같은 요청을 넘겼을 가능성이 있다 |
| "`API는 200인데 프론트가 알아서 페이지를 바꿔요`" | SPA navigation | 서버 redirect보다 프론트 라우터 질문일 가능성이 높다 |
| "`왜 POST 다음 GET이 보여요?`" | PRG | 이동 주체보다 form submit 흐름 질문일 수 있다 |
| "`왜 302도 보이고 화면도 성공처럼 떠요?`" | redirect | `302`는 중간 안내이고 최종 화면은 이어진 `get -> 200`일 수 있다 |

## 한 번에 보는 예시

| 시나리오 | 브라우저에서 보이는 것 | 먼저 붙일 이름 |
|---|---|---|
| `POST /login -> 303 -> GET /home` | 요청이 두 줄이고 URL도 바뀐다 | redirect |
| `POST /login -> 200` 한 줄인데 화면만 홈처럼 바뀐다 | 서버 안에서 view만 바뀌었다 | forward |
| `POST /api/login -> 200` 뒤 `router.push('/home')` | API 성공 후 JS가 이동했다 | SPA navigation |

여기서 "`왜 `POST` 다음에 `GET`이 보여요?`"까지 같이 붙으면 이동 방식 질문만으로는 부족하다. 그때는 이 문서에서 멈추지 말고 [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)으로 바로 넘어가 "`결과 화면을 왜 `GET`으로 다시 여는가`"를 같이 잡는 편이 더 빠르다.

## 흔한 오해

- URL이 바뀌면 무조건 redirect라고 생각한다. SPA router도 URL을 바꾼다.
- `200 OK`면 이동이 없다고 생각한다. SPA는 `200` 뒤에 JS가 이동할 수 있다.
- 화면이 바뀌었다고 항상 새 문서 요청이 간다고 생각한다. forward와 SPA는 그렇지 않을 수 있다.
- redirect와 PRG를 같은 질문으로 읽는다. redirect는 "누가 이동을 결정했나", PRG는 "왜 `POST` 뒤 결과를 `GET`으로 다시 여나"를 다룬다.

## 여기서 끊고 다음으로 갈 곳

이 문서는 이동 방식만 분리하는 beginner entry다. 아래 주제는 follow-up으로 넘긴다.

- 로그인 redirect와 `SavedRequest`, `Set-Cookie`: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- `POST -> redirect -> GET` 새로고침 안전성: [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- page 렌더링과 JSON API 응답 차이: [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)

## 한 줄 정리

redirect는 서버가 브라우저에게 새 요청을 시키는 것이고, forward는 서버 안에서 같은 요청의 목적지만 바꾸는 것이며, SPA navigation은 자바스크립트 라우터가 화면과 URL을 바꾸는 것이다.
