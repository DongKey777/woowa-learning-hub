# HTTP 상태 코드 기초

> 한 줄 요약: HTTP 상태 코드는 서버가 요청을 어떻게 처리했는지 알려 주는 숫자이고, beginner는 먼저 `누가 다음 행동을 해야 하는가`로 읽으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md)
- [`403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법](./http-403-vs-404-concealment-beginner-bridge.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: http status codes basics, status code basics, http status beginner, 상태 코드 뭐예요, 처음 status code, 404 뭔가요, 500 에러 왜 나요, 2xx 3xx 4xx 5xx 차이, 302 303 304 401 basics, 왜 post 다음 get, 왜 새로고침하니 304, what is http status code, beginner http response code

## 핵심 개념

상태 코드는 서버가 "요청을 받았고, 이제 다음에 무엇이 일어나야 하는지"를 짧게 알려 주는 신호다.

| 계열 | 먼저 읽는 질문 | 초보자용 감각 |
|---|---|---|
| `2xx` | 요청이 끝났나 | 성공했다 |
| `3xx` | 다른 URL로 가거나 cache를 다시 써야 하나 | 다음 동작이 바뀐다 |
| `4xx` | 내가 보낸 요청부터 다시 봐야 하나 | 요청/인증/권한 문제다 |
| `5xx` | 서버 쪽이 처리하다 막혔나 | 서버 쪽 확인이 필요하다 |

처음에는 세부 정의를 외우기보다 "`누가 다음 행동을 해야 하나`"만 잡아도 충분하다.

## 처음 보는 trace에서 먼저 자를 3가지

상태 코드 숫자만 보면 `302`/`303`/`304`가 금방 섞인다. beginner는 아래 3가지를 같이 보면 훨씬 덜 헷갈린다.

| 먼저 볼 것 | 질문 | 예시 해석 |
|---|---|---|
| URL이 바뀌는가 | 다른 목적지로 이동했나 | `302`, `303` 쪽 후보 |
| HTTP 메서드가 바뀌는가 | `POST` 결과를 `GET`으로 다시 열었나 | `303` 쪽 후보 |
| 같은 URL body를 다시 쓰는가 | 화면 내용만 재사용했나 | `304` 쪽 후보 |

한 줄로 줄이면 이렇다.

- URL이 바뀌면 먼저 redirect를 의심한다.
- `POST` 뒤 `GET`이 보이면 PRG(`303`) 가능성을 먼저 본다.
- 같은 URL에서 body만 안 다시 받으면 cache(`304`) 질문이다.

## 처음 헷갈리는 네 숫자

beginner가 가장 자주 섞는 것은 `302`, `303`, `304`, `401`이다.

| 지금 보이는 장면 | 먼저 읽을 코드 | 핵심 질문 | 다음 문서 |
|---|---|---|---|
| 다른 URL로 한 번 더 이동한다 | `302` | 목적지 URL이 바뀌는가 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| 폼 제출 뒤 결과 화면이 `GET`으로 열린다 | `303` | 마지막 요청을 `GET`으로 바꾸는가 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 같은 URL인데 body를 다시 안 받는다 | `304` | 같은 URL의 body만 재사용하는가 | [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) |
| API 호출이 그 자리에서 인증 실패로 멈춘다 | `401` | 이동 문제가 아니라 인증 부재인가 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |

짧게 고정하면 이렇다.

- `302`: 다른 URL로 이동
- `303`: `POST` 결과를 다른 URL의 `GET`으로 보기
- `304`: 같은 URL의 body 재사용
- `401`: 지금 인증 안 됨

## 자주 보는 코드 한 표

| 코드 | 초보자용 한 줄 의미 | 흔한 장면 |
|---|---|---|
| `200 OK` | 요청이 정상 처리됐다 | 조회 화면, API 성공 |
| `201 Created` | 새 리소스를 만들었다 | 생성 API |
| `204 No Content` | 성공했지만 body는 없다 | 삭제/토글 API |
| `302 Found` | 다른 URL로 가라 | 로그인 화면 이동, 페이지 이동 |
| `303 See Other` | 결과는 다른 URL의 `GET`으로 다시 열어라 | PRG, form submit 완료 |
| `304 Not Modified` | body를 다시 보내지 않고 cache를 써라 | 새로고침, 정적 자원 재검증 |
| `401 Unauthorized` | 인증이 안 됐다 | 토큰 없음, 세션 만료 |
| `403 Forbidden` | 인증은 됐지만 권한이 없다 | 관리자 화면 접근 거절 |
| `404 Not Found` | 경로나 자원이 없다 | 잘못된 URL, 없는 id |
| `500 Internal Server Error` | 서버 내부 처리 실패다 | 예외 누락, 서버 버그 |

## `POST -> 303 -> GET -> 304`는 같이 보여도 정상이다

이 흐름이 beginner를 가장 자주 멈추게 한다.

| 순서 | trace에서 보이는 것 | 초보자용 해석 |
|---|---|---|
| 1 | `POST /orders -> 303 See Other` | 결과 화면은 다른 URL의 `GET`으로 열어라 |
| 2 | `GET /orders/42 -> 200 OK` | 브라우저가 redirect를 따라가 결과 화면을 열었다 |
| 3 | 새로고침 뒤 `GET /orders/42 -> 304 Not Modified` | 같은 결과 화면 body를 cache 재검증 뒤 재사용했다 |

핵심은 질문 축이 다르다는 점이다.

- `303`은 "다음 목적지 URL이 바뀌는가"를 다룬다.
- `304`는 "같은 URL body를 다시 받을까"를 다룬다.
- `401`은 "지금 요청을 인증 없이 보냈는가"를 다룬다.

즉 둘은 경쟁하는 해석이 아니라, 한 브라우저 흐름에서 연달아 나타날 수 있다.

## 증상으로 바로 고르기

| learner 질문 | 먼저 볼 코드/문서 | 이유 |
|---|---|---|
| "`왜 POST 다음에 GET이 보여요?`" | `303` / [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) | 브라우저 결과 화면을 `GET`으로 분리한 흐름일 수 있다 |
| "`왜 새로고침하니 304예요?`" | `304` / [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md) | 같은 URL body 재사용 여부를 먼저 봐야 한다 |
| "`왜 로그인하다가 /login으로 또 가요?`" | `302` 또는 `401` / [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) | 이동 문제인지 인증 부재인지 먼저 갈라야 한다 |
| "`403`이랑 `404`가 왜 둘 다 보여요?`" | `403` / [`403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법](./http-403-vs-404-concealment-beginner-bridge.md) | 권한 거절과 존재 숨김을 섞지 않게 한다 |

## 흔한 오해

- `401`과 `403`을 같은 뜻으로 읽는다. `401`은 인증 부재, `403`은 권한 부족이다.
- `304`를 실패라고 오해한다. `304`는 cache 재검증 결과이지 서버 오류가 아니다.
- `302`를 권한 에러 코드라고 읽는다. page login UX에서는 인증 문제가 `302 -> /login`처럼 보일 수 있다.
- `5xx`를 보면 클라이언트부터 고쳐야 한다고 생각한다. beginner 단계에서는 먼저 서버 쪽 실패 신호로 읽는 편이 안전하다.

## 여기서는 깊게 안 다루는 것

이 문서는 상태 코드를 처음 읽는 사람용 entry다. 아래 주제는 본문에서 길게 파지 않고 연결만 건다.

- `403`과 concealment `404`의 정책 차이: [`403` vs `404` Concealment](./http-403-vs-404-concealment-beginner-bridge.md)
- gateway `502`/`504`와 프록시 계층 해석: [HTTP 요청-응답 기본 흐름](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- `421`, H2/H3 connection reuse 같은 고급 상태 코드: [network 카테고리 인덱스](./README.md)

처음에는 `302`, `303`, `304`, `401`, `403`, `404`, `500`만 안정적으로 읽어도 충분하다.

## 한 줄 정리

상태 코드는 숫자 암기보다 "`누가 다음 행동을 해야 하나`"로 읽으면 beginner가 가장 자주 헷갈리는 `302`/`303`/`304`/`401`을 빠르게 구분할 수 있다.
