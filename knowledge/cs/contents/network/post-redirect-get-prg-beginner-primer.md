# Post/Redirect/Get(PRG) 패턴 입문

> 한 줄 요약: PRG(Post/Redirect/Get)는 폼 제출 직후 결과 화면을 바로 `POST` 응답으로 끝내지 않고 `POST -> redirect -> GET`으로 바꿔, 새로고침이 같은 `POST`를 다시 보내지 않게 돕는 브라우저 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)
- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md)

retrieval-anchor-keywords: prg pattern beginner, post redirect get basics, redirect after post intro, duplicate form submit prevention, 새로고침하면 다시 제출돼요, form submit duplicate why, post 결과 새로고침 중복, 201 created vs 303 see other, form submit 201 or 303, 303 see other form submit, browser resubmit warning, login success redirect get, 로그인 후 왜 get 이 보여요, 처음 prg, 왜 post 다음 get

## 핵심 개념

PRG는 이름 그대로 `POST -> Redirect -> GET` 순서로 끝나는 브라우저 패턴이다. 초보자가 자주 겪는 문제는 "등록 버튼을 눌렀더니 완료 화면은 떴는데, 새로고침하니까 다시 등록됐다"는 것이다. 이건 브라우저가 마지막 요청이 `POST`였다고 기억하고 다시 보내려 하기 때문에 생긴다.

핵심 감각은 단순하다.

- 폼 제출 자체는 `POST`다.
- 제출 직후 보여 줄 화면은 `GET` 주소로 따로 둔다.
- 그래서 새로고침 대상이 `POST`가 아니라 `GET`이 된다.

즉 PRG는 "중복 생성 자체를 완벽히 막는 기술"이라기보다, **브라우저 새로고침이 같은 `POST`를 다시 보내지 않게 흐름을 바꾸는 패턴**이다.

## 언제 `201`과 `303`을 떠올리면 되나

입문자 질문을 증상으로 바꾸면 아래처럼 읽을 수 있다.

| 지금 헷갈리는 장면 | 먼저 떠올릴 코드 | 이유 | 안전한 다음 문서 |
|---|---|---|---|
| 폼 제출 뒤 완료 페이지를 새로고침하면 다시 전송될까 걱정된다 | `303 See Other` | 마지막 요청을 `GET`으로 바꾸는 흐름이 필요하다 | [HTTP 상태 코드 기초](./http-status-codes-basics.md) |
| JSON API가 생성 결과와 새 리소스 위치를 바로 돌려준다 | `201 Created` | 화면 redirect보다 생성 결과 계약 자체가 중심이다 | [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) |
| 로그인 뒤 `POST /login` 다음에 `GET /home`이 보여 헷갈린다 | `303 See Other` 또는 `302 Found` | 인증은 `POST`에서 끝나고, 화면은 redirect 뒤 `GET`으로 다시 열릴 수 있다 | [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) |

## 한눈에 보기

| 지금 보이는 증상 | PRG 없이 읽기 | PRG로 바꾸면 |
|---|---|---|
| `등록 완료` 페이지에서 새로고침이 무섭다 | 마지막 요청이 `POST`일 수 있다 | 마지막 요청이 `GET`이 되게 만든다 |
| 브라우저가 "양식 다시 제출" 경고를 띄운다 | 새로고침이 `POST` 재전송과 연결돼 있다 | redirect 뒤 `GET` 화면이면 이런 경고가 줄어든다 |
| 주문/댓글/문의가 두 번 생성됐다 | 같은 `POST`가 다시 간 흔적일 수 있다 | 브라우저 재전송 원인은 줄지만 서버 중복 방지는 별도 필요하다 |
| 로그인 성공 직후 왜 `GET /home`이 또 보이는지 헷갈린다 | `POST /login` 응답 뒤 redirect가 끼어 있을 수 있다 | "`POST`로 인증하고, 화면은 `GET`으로 다시 연다"로 읽는다 |

짧은 mental model:

- `POST`: "서버 상태를 바꿔라"
- `Redirect`: "결과 화면은 다른 URL로 다시 열어라"
- `GET`: "이제 보여 줄 결과를 조회하자"

## 왜 새로고침이 위험한가

가장 단순한 폼 처리 흐름은 이렇다.

```http
GET /orders/new HTTP/1.1

HTTP/1.1 200 OK
```

```http
POST /orders HTTP/1.1
Content-Type: application/x-www-form-urlencoded

item=cola&qty=2

HTTP/1.1 200 OK
Content-Type: text/html

<html>주문 완료</html>
```

이 상태에서 브라우저 새로고침은 "완료 화면"이 아니라, 그 화면을 만든 마지막 요청 `POST /orders`를 다시 떠올릴 수 있다. 그래서 `새로고침 -> 같은 주문이 한 번 더 생성` 같은 문제가 생긴다.

핵심은 완료 HTML을 보여 줬다는 사실보다, **브라우저가 마지막으로 기억한 요청이 무엇인가**다. 그 마지막 요청이 `POST`면 새로고침이 불안해지고, `GET`이면 조회 재실행으로 읽기 쉬워진다.

## PRG는 마지막 요청을 `GET`으로 바꾼다

PRG 흐름은 중간에 redirect를 넣는다.

```http
POST /orders HTTP/1.1
Content-Type: application/x-www-form-urlencoded

item=cola&qty=2

HTTP/1.1 303 See Other
Location: /orders/42
```

```http
GET /orders/42 HTTP/1.1

HTTP/1.1 200 OK
Content-Type: text/html

<html>주문 완료 화면</html>
```

이제 브라우저가 마지막으로 보고 있는 것은 `GET /orders/42` 결과다. 그래서 새로고침은 보통 `GET /orders/42`를 다시 보내고, 같은 주문 생성 `POST`를 반복하지 않는다.

짧게 정리하면 이렇다.

| 단계 | 서버가 말하는 것 | 브라우저가 다음에 하는 일 |
|---|---|---|
| `POST /orders` | 생성 처리 완료 | 결과 화면 URL을 기다린다 |
| `303 See Other` + `Location: /orders/42` | 결과는 저 URL에서 다시 봐라 | `/orders/42`로 이동 준비 |
| `GET /orders/42` | 결과 화면 조회 | 새로고침해도 다시 조회한다 |

## 왜 `303`이 설명하기 쉬운가

PRG를 처음 배울 때는 `302`와 `303`이 같이 등장해서 헷갈린다.

| 코드 | 초보자용 해석 | PRG에서의 감각 |
|---|---|---|
| `302 Found` | 다른 URL로 가라 | 브라우저에서 `POST` 뒤 `GET`처럼 보일 때가 많지만 의도가 덜 또렷하다 |
| `303 See Other` | 결과는 다른 URL에서 `GET`으로 다시 봐라 | PRG 의도를 가장 또렷하게 보여 준다 |

즉 beginner 관점에서는 "`POST` 결과 페이지를 `GET`으로 다시 열고 싶다"면 `303`이 가장 읽기 쉽다.

많은 서비스는 여전히 `302`도 쓴다. 다만 초보자 mental model로는 `303`이 "`POST` 결과는 다른 URL의 `GET`으로 본다"를 가장 직접적으로 보여 준다. `307`처럼 메서드를 유지하는 redirect는 beginner PRG 본문에서 파지 말고, "왜 같은 `POST`가 유지되지?"라는 별도 질문이 생겼을 때 follow-up으로 보는 편이 안전하다.

## `201 Created`와 `303 See Other`는 언제 갈리나

이 둘은 "둘 중 하나만 옳다"가 아니라, **무엇을 응답으로 끝내고 싶은지**가 다르다.

| 서버가 지금 끝내고 싶은 일 | beginner 감각 | 더 잘 맞는 응답 |
|---|---|---|
| "새 리소스를 만들었고, 이 응답 자체가 생성 결과다" | API 호출 하나로 생성 사실을 바로 돌려준다 | `201 Created` |
| "생성은 끝났고, 사용자가 볼 화면은 다른 URL에서 다시 열어라" | 브라우저 폼 제출 뒤 결과 화면을 조회 URL로 분리한다 | `303 See Other` |

가장 단순하게 외우면 이렇다.

- `201 Created`: 생성 성공 자체를 응답으로 바로 알려 주는 API 쪽 감각
- `303 See Other`: 생성 후 보여 줄 화면을 다른 `GET` URL로 넘기는 브라우저 쪽 감각

예를 들어 JSON API라면 이런 응답이 자연스럽다.

```http
POST /api/orders HTTP/1.1
Content-Type: application/json

{"item":"cola","qty":2}

HTTP/1.1 201 Created
Location: /api/orders/42
Content-Type: application/json

{"id":42,"item":"cola","qty":2}
```

이 경우 클라이언트는 이미 생성 결과를 받았다. 따라서 꼭 redirect로 한 번 더 화면 조회를 시킬 이유가 없다.

반대로 브라우저 form submit이라면 이런 흐름이 더 읽기 쉽다.

```http
POST /orders HTTP/1.1
Content-Type: application/x-www-form-urlencoded

item=cola&qty=2

HTTP/1.1 303 See Other
Location: /orders/42
```

여기서는 생성 사실보다도 "`주문 완료 화면은 /orders/42에서 GET으로 다시 열어라`"가 더 중요하다. 브라우저 새로고침 대상도 결국 `GET /orders/42`가 된다.

즉 초보자용 판단 기준은 이것이다.

1. 응답을 받는 쪽이 브라우저 폼인가, API 클라이언트인가?
2. 지금 응답에서 생성 결과를 바로 끝낼 건가, 결과 화면 URL로 넘길 건가?
3. 새로고침 시 같은 `POST` 재전송 위험을 줄여야 하나?

브라우저 폼 완료 화면까지 한 번에 책임질 때는 `303`이 더 잘 맞고, API가 "생성 성공 + 생성된 리소스 정보"를 계약으로 돌려줄 때는 `201`이 더 잘 맞는다.

## PRG가 해결하는 것과 해결하지 않는 것

입문자가 가장 자주 하는 오해는 "PRG를 쓰면 중복 생성이 완전히 끝난다"는 생각이다. PRG는 browser refresh UX를 다루고, 서버 중복 방지는 별도 층이다.

| 질문 | PRG가 직접 다루는가 | 초보자용 설명 |
|---|---|---|
| 새로고침할 때 같은 `POST`가 다시 갈까 | 예 | 마지막 요청을 `GET`으로 바꿔 위험을 줄인다 |
| 브라우저의 "양식 다시 제출" 경고를 줄일까 | 예 | 완료 화면을 redirect 뒤 `GET`으로 분리한다 |
| 사용자가 더블클릭해 같은 주문을 두 번 보낼까 | 아니오 | 서버 dedup, 멱등성 키, 비즈니스 방어가 따로 필요하다 |
| 모바일 재시도나 네트워크 재전송까지 막을까 | 아니오 | 브라우저 UX 바깥의 재시도는 서버 계약이 맡는다 |

짧은 기억법:

- PRG는 "브라우저가 마지막에 무엇을 기억하나"를 바꾸는 패턴이다.
- 멱등성/중복 방지는 "서버가 같은 요청을 어떻게 받아들일까"를 바꾸는 설계다.

## 로그인은 왜 `POST -> 303 -> GET`처럼 끝날까

form login도 PRG 관점으로 읽으면 덜 헷갈린다.

```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=neo&password=secret

HTTP/1.1 303 See Other
Location: /home
Set-Cookie: JSESSIONID=def456; Path=/; HttpOnly
```

```http
GET /home HTTP/1.1
Cookie: JSESSIONID=def456

HTTP/1.1 200 OK
```

여기서 중요한 감각은 두 가지다.

- 인증 자체는 `POST /login`에서 끝난다.
- 사용자가 보게 되는 화면은 redirect 뒤 `GET /home`이나 `GET /orders/42` 같은 page 요청이다.

그래서 네트워크 탭에서 `POST /login` 다음에 `GET`이 보인다고 해서 이상한 것이 아니다. 오히려 브라우저 form login에서는 아주 흔한 마무리다.

또 redirect 응답에 `Set-Cookie`가 함께 올 수 있다. 브라우저는 그 cookie를 저장한 뒤, 다음 `GET` 요청에서 다시 실어 보내면서 로그인 상태를 이어 간다.

## PRG가 잘 맞는 장면

- 주문 생성 후 상세 페이지로 이동
- 댓글 작성 후 게시글 페이지로 복귀
- 문의 등록 후 완료 화면으로 이동
- 브라우저 폼 제출 후 목록/상세 화면을 다시 보여 주는 흐름

반대로 JSON API만 주고 SPA 라우터가 직접 이동하는 구조라면, redirect보다 프론트엔드 navigation과 서버 중복 방지 설계를 같이 봐야 한다.

## 생성 폼과 로그인 폼을 같은 틀로 읽어도 된다

| 장면 | 상태를 바꾸는 요청 | redirect가 알려 주는 다음 URL | 마지막에 보이는 `GET` |
|---|---|---|---|
| 주문 생성 | `POST /orders` | `/orders/42` | `GET /orders/42` |
| 댓글 작성 | `POST /comments` | `/posts/10` | `GET /posts/10` |
| form login 성공 | `POST /login` | `/home` 또는 원래 보호 URL | `GET /home` 또는 `GET /orders/42` |

초보자에게는 "로그인만 예외적인 특별 흐름"처럼 보이지만, 브라우저 입장에서는 이것도 결국 "`POST` 결과 화면을 `GET`으로 다시 여는 패턴"으로 읽을 수 있다.

## 자주 묻는 질문: 폼 제출 성공을 `201`로 주면 안 되나요

안 되는 것은 아니다. 다만 **브라우저가 바로 그 응답을 완료 화면으로 들고 있게 되면, 마지막 요청이 여전히 `POST`일 수 있다**는 점이 문제다.

| 선택 | 바로 얻는 장점 | 초보자가 놓치기 쉬운 점 |
|---|---|---|
| `201 Created` + 응답 body | API 계약이 단순하다. 생성된 id/location을 곧바로 돌려줄 수 있다 | 브라우저 폼 완료 화면까지 이 응답으로 끝내면 새로고침 시 `POST` 재전송 감각이 남는다 |
| `303 See Other` + `Location` | 완료 화면 URL이 분리되고 새로고침이 `GET`이 된다 | 응답이 한 번 더 왕복하므로 API 단독 호출보다 단계가 하나 늘어난다 |

그래서 beginner 기준으로는 이렇게 정리하면 된다.

- 브라우저 form submit UX를 설계한다면: `303`으로 완료 화면을 분리하는 쪽이 안전하다.
- JSON/REST API 응답을 설계한다면: `201`로 생성 사실과 resource location을 돌려주는 쪽이 자연스럽다.
- 둘을 함께 쓰는 구조도 가능하다: 내부적으로는 리소스를 생성하고, 브라우저 엔드포인트는 `303`으로 상세 페이지로 보내고, 별도 API 엔드포인트는 `201`을 돌려줄 수 있다.

## 여기서 잠깐 끊고, 서버 중복 방지는 다음 문서로 넘기기

PRG 본문에서 꼭 기억할 핵심은 하나다. **PRG는 브라우저 새로고침 때문에 같은 `POST`가 다시 가는 UX를 줄이는 패턴**이라는 점이다.

더블클릭, 모바일 재시도, 결제 중복처럼 서버 쪽 방어가 필요한 주제는 이 문서의 중심을 벗어난다. 그런 질문이 생기면 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)로 내려가면 된다.

## 흔한 오해와 함정

- PRG를 쓰면 중복 생성이 100% 사라진다고 오해한다. PRG는 **새로고침으로 인한 브라우저 재전송**을 줄여 주는 패턴이다.
- 완료 HTML을 `POST` 응답에서 바로 그려도 괜찮다고 생각한다. 화면은 보일 수 있지만, 이후 새로고침/뒤로가기 경험이 불안정해진다.
- PRG와 멱등성을 같은 개념으로 섞는다. PRG는 브라우저 흐름 패턴이고, 멱등성은 같은 요청을 여러 번 보내도 상태가 같아지는 성질이다.
- 로그인 성공 뒤 `GET /home`이 보이면 인증이 풀렸다고 오해한다. 실제로는 `POST /login` 성공 후 redirect로 page를 다시 여는 정상 흐름일 수 있다.

## 실무에서 쓰는 모습

브라우저 폼 기반 화면에서는 보통 아래처럼 생각하면 된다.

1. `GET /orders/new`로 입력 폼을 보여 준다.
2. 사용자가 `POST /orders`로 제출한다.
3. 서버는 생성만 처리하고 완료 화면은 바로 그리지 않는다.
4. 대신 `Location: /orders/42` 같은 redirect를 돌려준다.
5. 브라우저가 `GET /orders/42`를 다시 보내 상세/완료 화면을 본다.

이 패턴의 장점은 "완료 화면 URL"이 생긴다는 점이기도 하다. 사용자는 상세 페이지를 북마크하거나 다시 방문할 수 있고, 새로고침도 조회 재실행으로 읽기 쉬워진다.

로그인도 비슷하다.

1. 브라우저가 `GET /login`으로 로그인 폼을 본다.
2. 사용자가 `POST /login`으로 자격 증명을 보낸다.
3. 서버는 성공 후 홈이나 원래 보호 URL로 redirect를 돌려준다.
4. 브라우저는 그 주소를 `GET`으로 다시 열고, 방금 받은 session cookie를 함께 보낼 수 있다.

이렇게 보면 login success redirect는 PRG와 따로 노는 개념이 아니라, PRG를 가장 자주 체감하는 브라우저 예시 중 하나다.

다만 결제나 주문처럼 정말 중복이 치명적인 작업은 PRG만으로 충분하지 않다. 서버 쪽 중복 방지는 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)에서 별도로 이어서 보면 된다.

## 더 깊이 가려면

- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md) — `POST`가 왜 멱등하지 않은지 먼저 고정
- [HTTP 상태 코드 기초](./http-status-codes-basics.md) — `302`/`303`/`307`을 상태 코드 관점에서 다시 읽기
- [SSR 뷰 렌더링 vs JSON API 응답 입문](./ssr-view-render-vs-json-api-response-basics.md) — 브라우저 HTML 응답 흐름과 JSON API 응답 흐름이 왜 `303`과 `201`로 갈리는지 이어 보기
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md) — redirect 응답의 `Set-Cookie`와 다음 `GET`의 `Cookie`를 같이 읽기
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md) — 로그인 후 원래 URL 복귀, 숨은 `JSESSIONID`, `SavedRequest`까지 이어 보기
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md) — redirect와 JS navigation이 어떻게 다른지 분리
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md) — 이 HTTP 흐름이 서버 코드에서 어디에 매핑되는지 연결
- [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md) — PRG 바깥의 서버 dedup 계층을 DB/저장소 관점에서 이어 보기

## 면접/시니어 질문 미리보기

**Q. PRG 패턴을 왜 쓰나요?**  
브라우저 폼 제출 뒤 결과 화면을 바로 `POST` 응답으로 끝내지 않고 `GET` 화면으로 분리해서, 새로고침 시 같은 `POST`가 재전송되는 일을 줄이기 위해 쓴다.

**Q. `302` 대신 `303`을 말하는 이유는 뭔가요?**  
`303`은 "`POST` 결과는 다른 URL의 `GET`으로 다시 보라"는 의도가 더 분명해서 PRG 설명에 적합하다.

**Q. 리소스를 만들었으면 항상 `201 Created`여야 하나요?**  
아니다. API가 생성 결과 자체를 응답으로 끝내면 `201`이 자연스럽고, 브라우저 폼 제출 뒤 결과 화면을 다른 URL의 `GET`으로 열게 하고 싶으면 `303`이 더 잘 맞는다.

**Q. 로그인 성공 뒤 왜 `POST /login` 다음에 `GET /home`이 보이나요?**  
브라우저 form login이 redirect로 마무리되면, 인증은 `POST /login`에서 끝나고 사용자가 보게 되는 화면은 redirect 뒤 `GET` 요청으로 다시 열리기 때문이다.

**Q. PRG가 있으면 중복 주문 문제가 완전히 해결되나요?**  
아니다. 이 문서에서 다루는 것은 브라우저 새로고침 재전송까지다. 서버 재시도·중복 방지는 별도 설계가 필요하다.

## 한 줄 정리

PRG는 브라우저 폼 제출을 `POST -> 303 -> GET`으로 바꿔 새로고침 재전송을 줄이는 패턴이고, `201 Created`는 생성 결과 자체를 바로 돌려주는 API 응답에 더 잘 맞는다.
