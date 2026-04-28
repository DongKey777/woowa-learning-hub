# HTTP 상태 코드 기초

> 한 줄 요약: HTTP 상태 코드는 서버가 요청을 어떻게 처리했는지 세 자리 숫자로 알려주는 신호이고, 앞 자리 하나가 성공/실패/리다이렉션을 결정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 메서드, REST, 멱등성 기초](./http-methods-rest-idempotency-basics.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md)
- [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md)
- [`403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법](./http-403-vs-404-concealment-beginner-bridge.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [HTTP와 HTTPS 기초](./http-https-basics.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: http status codes basics, 상태 코드 뭐예요, 404 뭔가요, 500 에러 왜 나요, http 응답 코드 입문, 2xx 3xx 4xx 5xx 차이, 상태 코드 처음 배우는데, 201 created, 302 303 304 차이, 302 vs 303 basics, prg redirect basics, 304 왜 떠요, 왜 post 다음 get 이 보여요, 왜 새로고침하니 304 가 떠요, browser login redirect vs api 401

## 핵심 개념

브라우저나 앱이 서버에 요청을 보내면, 서버는 응답의 첫 줄에 세 자리 숫자를 담아 결과를 알려준다. 이게 **HTTP 상태 코드**다. 앞 자리 숫자가 1이면 정보, 2이면 성공, 3이면 리다이렉션, 4이면 클라이언트 오류, 5이면 서버 오류다. 입문자가 헷갈리는 지점은 4xx와 5xx를 구분하지 못하는 것이다. 4xx는 요청 자체가 잘못됐고, 5xx는 요청은 맞지만 서버가 처리하다 실패한 상황이다.

처음에는 "누가 다음 행동을 해야 하느냐"로 읽어도 충분하다.

| 계열 | 누가 다음 행동을 주로 하나 | 초급자용 감각 |
|---|---|---|
| 2xx | 클라이언트가 정상 흐름을 이어 간다 | 성공했다 |
| 3xx | 브라우저가 다른 위치로 이동하거나 캐시를 재사용한다 | 다음 목적지가 바뀐다 |
| 4xx | 클라이언트가 요청, 인증, 경로를 다시 본다 | 내가 보낸 쪽부터 확인한다 |
| 5xx | 서버/프록시 운영 측이 원인을 찾는다 | 서버 쪽이 처리하다 막혔다 |

## 증상으로 먼저 읽는 15초 분기

상태 코드를 처음 볼 때는 숫자 정의를 외우기보다 "지금 브라우저나 클라이언트가 무엇을 하게 됐는가"부터 잡는 편이 빠르다.

| 지금 보이는 장면 | 먼저 읽는 상태 코드 | 왜 그렇게 읽나 | 다음 문서 |
|---|---|---|---|
| 로그인하려는데 `/login` 화면으로 한 번 더 이동한다 | `302` 또는 `303` | 서버가 다른 URL로 가라고 지시한 장면일 수 있다 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |
| 폼 제출 뒤 새로고침이 무섭다 | `303`을 먼저 의심 | 마지막 요청을 `GET`으로 바꾸는 PRG 흐름이 필요한 장면일 수 있다 | [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) |
| 같은 파일을 다시 받지 않았는데 `304`가 보인다 | `304 Not Modified` | 실패가 아니라 cache 재검증 뒤 기존 body 재사용일 수 있다 | [Browser `302` vs `304` vs `401` 새로고침 분기표](./browser-302-304-401-reload-decision-table-primer.md) |
| API 호출이 바로 `401`로 끝난다 | `401 Unauthorized` | redirect보다 raw 인증 실패일 가능성이 크다 | [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) |
| 프록시 앞단에서 갑자기 `502`나 `504`가 보인다 | `5xx` gateway 계열 | 앱 코드만이 아니라 proxy/upstream timeout도 함께 봐야 한다 | [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) |

## `302` `303` `304` `401`이 왜 한 덩어리로 헷갈릴까

처음 보면 넷 다 "뭔가 다시 이동하거나 다시 확인하는 숫자"처럼 보인다. 하지만 실제 질문은 서로 다르다.

| 코드 | 브라우저가 받는 핵심 지시 | 초보자용 질문 |
|---|---|---|
| `302` | 다른 URL로 이동하라 | "지금 목적지 URL이 바뀌는가?" |
| `303` | 방금 `POST`한 결과는 다른 URL의 `GET`으로 열어라 | "마지막 요청을 `GET`으로 바꿔야 하는가?" |
| `304` | 같은 URL의 body는 다시 안 보내고 cache를 써라 | "목적지는 그대로인데 body만 재사용하는가?" |
| `401` | 지금 인증이 안 됐다 | "이동 문제가 아니라 로그인/토큰 문제인가?" |

짧게 고정하면 이렇다.

- `302`와 `303`은 "어디로 다시 갈지"가 중심이다.
- `304`는 "같은 곳에서 body를 다시 받을지"가 중심이다.
- `401`은 "다시 갈지"보다 "지금 인증됐는지"가 중심이다.

그래서 `302`, `303`, `304`, `401`은 모두 브라우저의 다음 행동에 영향을 주지만, 같은 종류의 질문에 답하는 코드는 아니다.

## `403`과 `404`를 너무 단순하게 외우면 생기는 예외

상태 코드를 처음 배울 때는 이렇게 외우는 것이 맞다.

- `403`: 권한이 없다
- `404`: 없다

그런데 보안이 섞이면 앱이 의도적으로 `404`를 선택하는 경우가 있다.  
특히 다른 사람 주문, 다른 tenant 자원처럼 **존재 자체를 알려 주면 안 되는 리소스**는 내부적으로는 인가 실패여도 바깥에는 `404`를 줄 수 있다.

중요한 점은 이것이다.

- `403`의 의미가 틀린 것이 아니다.
- `404`의 의미가 사라진 것도 아니다.
- 앱이 "존재 여부를 드러내지 않겠다"는 정책 때문에 바깥 응답을 `404`로 더 보수적으로 고른 것이다.

짧은 비교:

| 코드 | 초보자용 안전한 설명 |
|---|---|
| `403` | `있다는 사실은 알려도 되지만, 너는 못 한다` |
| concealment `404` | `없다`와 `있지만 말하지 않음`을 외부에서 구분하기 어렵게 만든다 |

예시:

- 관리자 화면 권한 부족 -> 보통 `403`
- 남의 주문 상세 접근 -> concealment 정책이면 `404`

이 주제를 beginner 관점에서 따로 끊어 읽고 싶다면 [`403` vs `404` Concealment: 존재를 숨길 때 초보자가 읽는 법](./http-403-vs-404-concealment-beginner-bridge.md)으로 이어 가면 된다.

## 한눈에 보기

| 계열 | 의미 | 대표 코드 |
|---|---|---|
| 2xx | 성공 | 200 OK, 201 Created, 204 No Content |
| 3xx | 리다이렉션/재검증 | 302 Found, 303 See Other, 304 Not Modified |
| 4xx | 클라이언트 오류 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | 서버 오류 | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

## beginner 범위를 잠깐 넘는 코드: `421`

입문 단계에서는 `403`, `404`, `302`, `303`, `304`, `401`, `502`, `504` 정도만 먼저 구분해도 충분하다.  
`421 Misdirected Request`는 HTTP/2·HTTP/3 connection reuse 문맥이 섞여서 읽기 난도가 갑자기 올라가므로, 여기서는 "상태 코드 기초의 핵심 묶음 밖에 있는 follow-up"으로만 기억해 두면 된다.

- 지금은 `421`을 외우기보다 `403/404`와 redirect, `304`, `401`을 먼저 안정적으로 읽는 쪽이 더 중요하다.
- DevTools에서 같은 URL이 `421 -> 200` 또는 `421 -> 403`처럼 이어지는 trace를 본 뒤에만 follow-up 문서로 내려가면 된다.

## 상세 분해

### 자주 보는 2xx

- **200 OK**: 요청이 성공했고 응답 본문에 결과가 있다.
- **201 Created**: 리소스 생성 성공. POST 요청 후 서버가 새 리소스를 만들었을 때 쓴다.
- **204 No Content**: 성공했지만 응답 본문이 없다. DELETE 요청 처리 후 자주 쓴다.

### 자주 보는 4xx

- **400 Bad Request**: 요청 형식이 잘못됐다. JSON 파싱 오류, 필수 파라미터 누락 등.
- **401 Unauthorized**: 인증이 안 됐다. 로그인이 필요하다.
- **403 Forbidden**: 인증은 됐지만 권한이 없다. 로그인했어도 접근 불가.
- **404 Not Found**: 요청한 경로에 리소스가 없다.

### 자주 보는 5xx

- **500 Internal Server Error**: 서버 내부에서 예상치 못한 오류가 발생했다.
- **502 Bad Gateway**: 게이트웨이(예: Nginx)가 upstream 서버로부터 잘못된 응답을 받았다.
- **503 Service Unavailable**: 서버가 현재 요청을 처리할 수 없다. 일시적 과부하 또는 점검 중.

## 어디서 막혔는지 빠르게 가르는 미니 표

처음 장애를 읽을 때는 숫자를 외우기보다 "어느 질문부터 다시 볼지"를 고정하는 편이 빠르다.

| 코드 | 먼저 떠올릴 질문 | 첫 확인 대상 |
|---|---|---|
| `302 Found` | 브라우저가 다른 URL로 이동하라는 뜻인가 | `Location`, 로그인 redirect |
| `303 See Other` | `POST` 결과를 다른 URL의 `GET`으로 다시 열라는 뜻인가 | `Location`, form submit, PRG |
| `304 Not Modified` | body를 다시 받지 않고 캐시를 재사용하라는 뜻인가 | `ETag`, `If-None-Match`, 브라우저 cache |
| `401 Unauthorized` | 로그인/토큰이 없거나 만료됐나 | `Authorization`, `Cookie`, 로그인 상태 |
| `403 Forbidden` | 인증은 됐지만 권한이 부족한가 | 역할, 접근 정책 |
| `404 Not Found` | 경로나 자원 id가 틀렸나 | URL path, resource id |
| `502 Bad Gateway` | 앞단 프록시가 upstream 응답을 정상 처리하지 못했나 | Nginx/LB, upstream 로그 |
| `504 Gateway Timeout` | 프록시가 upstream을 기다리다 timeout 났나 | timeout 설정, 느린 upstream |

특히 `502`와 `504`는 "애플리케이션이 500을 냈다"와 다르다. 브라우저와 앱 사이에 프록시가 있으면, 바깥에서 보이는 실패 코드는 프록시가 대신 표현할 수 있다.

## 한 번에 묶어 보는 예시: `POST -> 303 -> GET -> 304`

처음에는 `302`, `303`, `304`가 모두 "뭔가 다시 간다"로 보여 헷갈린다. 아래처럼 한 흐름으로 붙여 보면 역할이 분리된다.

| 순서 | 브라우저에 보이는 것 | 초보자용 해석 |
|---|---|---|
| 1 | `POST /orders -> 303 See Other` | 서버가 "결과 화면은 다른 URL의 `GET`으로 다시 열어라"라고 말했다 |
| 2 | `GET /orders/42 -> 200 OK` | 브라우저가 redirect를 따라가 결과 화면을 받았다 |
| 3 | 새로고침 후 `GET /orders/42` + `If-None-Match` | 이제 마지막 요청은 `POST`가 아니라 `GET`이다 |
| 4 | `304 Not Modified` | 서버가 body를 다시 보내지 않고 기존 cache를 재사용하게 했다 |

이 예시에서 `303`은 **어디로 다시 갈지**를 바꾸고, `304`는 **같은 URL의 body를 다시 받을지**를 바꾼다. 둘 다 브라우저의 다음 행동에 영향을 주지만 질문이 다르다.

- `303`: "다음 목적지 URL이 바뀌나?"
- `304`: "같은 목적지에서 body를 다시 받나?"

그래서 form submit 뒤 `303`이 보이는 장면과, 결과 화면을 새로고침했더니 `304`가 보이는 장면은 서로 경쟁하는 해석이 아니라 한 흐름 안에서 연달아 나타날 수 있다.

## `302` vs `303` vs `401` vs `403`: browser와 API를 먼저 나눠 읽기

입문자가 가장 자주 섞는 네 숫자는 `302`, `303`, `401`, `403`다. 이 넷은 "redirect/auth failure" 한 덩어리가 아니라, **요청 종류**와 **다음 행동 주체**가 다르다.

| 지금 보는 장면 | 먼저 읽는 뜻 | 흔한 호출자 | 다음 행동 |
|---|---|---|---|
| `302 Found` + `Location: /login` | 브라우저를 로그인 화면으로 이동시키는 UX일 수 있다 | 주소창 navigation, 보호된 HTML page | redirect 뒤 login page와 cookie/session 흐름 확인 |
| `303 See Other` + `Location: /orders/42` | `POST` 결과 화면은 다른 `GET` URL에서 다시 열어라 | form submit, login success redirect, PRG | 새로고침 대상이 `POST`가 아니라 `GET`인지 확인 |
| raw `401 Unauthorized` | 서버가 "지금 인증 안 됨"을 직접 말했다 | XHR, `fetch`, REST API, 모바일 앱 | 토큰/세션이 없는지, 만료됐는지 확인 |
| raw `403 Forbidden` | 인증은 됐지만 이 자원은 허용되지 않았다 | page, API 둘 다 가능 | 역할/권한 정책 확인 |

짧게 외우면:

- `302`: "다른 URL로 이동해라"
- `303`: "`POST` 결과는 다른 URL의 `GET`으로 다시 봐라"
- `401`: "누구냐"를 아직 모르거나 인증이 끝나지 않음
- `403`: "누군지는 알지만 여기까지는 안 됨"

특히 `302`와 `303`은 둘 다 redirect지만 초급자용 해석이 다르다.

| 코드 | 초급자용 한 줄 의미 | 자주 붙는 장면 |
|---|---|---|
| `302 Found` | 다른 URL로 이동하라 | login redirect, page 이동 |
| `303 See Other` | 방금 `POST`한 결과는 다른 URL의 `GET`으로 보라 | PRG, form submit 완료 화면 |

같은 인증 실패라도 page와 API는 기대 계약이 다르다.

| 요청 종류 | 더 자연스러운 실패 표현 | 초보자가 오해하기 쉬운 장면 |
|---|---|---|
| 브라우저 page navigation | `302 -> /login` 후 login page 이동 | `302` 자체를 권한 에러 코드라고 읽음 |
| XHR / `fetch` / REST API | 보통 raw `401` 또는 raw `403` | redirect를 따라가 login HTML `200`만 보고 성공으로 오해 |

예를 들어 `fetch('/api/me')`가 JSON `401` 대신 login HTML `200`을 받으면, 실제 의미는 "정상 응답"이 아니라 "API 경계에 browser redirect 정책이 섞였다"에 더 가깝다.

## 흔한 오해와 함정

- 401과 403을 혼동한다. 401은 "누구냐"를 모르는 상태, 403은 "누군지 알지만 허용 안 함"이다.
- 302도 auth failure code라고 오해한다. `302`는 보통 브라우저를 다른 URL로 보내는 지시이고, page login UX에서 `401` 상황을 감싸는 겉모습일 수 있다.
- 303과 304를 둘 다 "다시 요청한다"로만 읽는다. `303`은 결과 화면 URL을 바꾸는 redirect이고, `304`는 같은 URL에서 cache body를 재사용하는 재검증 결과다.
- 200만 성공이라고 생각하지만, 201·204도 성공이다. REST API에서는 생성·삭제 후 응답 코드를 올바르게 설정해야 클라이언트가 결과를 해석할 수 있다.
- 5xx가 나오면 클라이언트 코드를 고쳐야 한다고 오해한다. 5xx는 서버 쪽 문제다. 서버 로그를 봐야 원인을 찾을 수 있다.

## 실무에서 쓰는 모습

Spring Boot REST 컨트롤러에서 `@ResponseStatus(HttpStatus.CREATED)`를 붙이거나 `ResponseEntity.created(uri).build()`를 반환하면 201이 내려간다. 클라이언트는 이 코드를 보고 "리소스가 만들어졌구나"를 알 수 있다. 404가 자주 발생한다면 클라이언트와 서버의 URL 경로 계약이 맞지 않다는 신호다.

브라우저 기준으로는 아래처럼 읽으면 된다.

1. 로그인 직후 `302`와 `Set-Cookie`가 보이면 브라우저가 다음 URL로 이동하면서 인증 상태를 이어 가려는 흐름일 수 있다.
2. 폼 제출 직후 `303`과 `Location`이 보이면 `POST -> redirect -> GET`으로 끝나는 PRG 흐름일 수 있다.
3. 같은 정적 파일이 `304`를 반환하면 실패가 아니라 cache 재검증 성공일 수 있다.
4. API가 raw `401`이면 인증 정보 부재/만료를 먼저 보고, raw `403`이면 권한 정책을 먼저 본다.
5. API가 `302 -> /login` 뒤 login HTML `200`으로 끝나면 성공이 아니라 page redirect 정책이 API 계약에 섞인 장면일 수 있다.
6. API가 `502`나 `504`를 반환하면 컨트롤러 코드만 보지 말고 프록시와 upstream timeout도 같이 확인해야 한다.

## 더 깊이 가려면

- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md) — 상태 코드가 브라우저 전체 요청 사이클 어디쯤 오는지 다시 잡는 primer
- [Post/Redirect/Get(PRG) 패턴 입문](./post-redirect-get-prg-beginner-primer.md) — `303 See Other`와 브라우저 새로고침/중복 제출 감각을 따로 고정하는 follow-up
- [HTTP 421 Troubleshooting Trace Examples: 403/404와 구분하기](./http-421-troubleshooting-trace-examples.md) — beginner 범위를 넘는 `421` trace는 여기서 별도로 읽기
- [HTTP/2 ORIGIN Frame와 421 입문](./http2-origin-frame-421-primer.md) — `421`이 왜 connection reuse 문맥에서 생기는지 follow-up
- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md) — 메서드별 예상 상태 코드 패턴
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. 401과 403의 차이를 설명해 주세요.**
401은 인증(authentication) 실패로 서버가 요청자를 식별하지 못한 상태다. 403은 인가(authorization) 실패로 신원은 확인됐지만 해당 리소스에 접근할 권한이 없다.

**Q. 클라이언트에서 발생하는 오류와 서버에서 발생하는 오류를 상태 코드로 어떻게 구분하나요?**
4xx는 요청 자체가 잘못된 클라이언트 오류이고, 5xx는 서버가 정상 요청을 처리하다 실패한 서버 오류다. 일반적으로 4xx는 클라이언트 코드 수정이 필요하고, 5xx는 서버 로그 확인이 필요하다.

**Q. REST API에서 리소스 생성 후 200 대신 201을 반환해야 하는 이유는?**
201은 새 리소스가 만들어졌다는 의미를 명확히 전달하고, Location 헤더에 새 리소스 URL을 담을 수 있다. 클라이언트는 이를 보고 후속 요청 경로를 알 수 있다.

## 한 줄 정리

상태 코드 앞 자리가 2면 성공, 3면 리다이렉션, 4면 클라이언트 잘못, 5면 서버 잘못이다.
