# Post/Redirect/Get(PRG) 패턴 입문

> 한 줄 요약: PRG는 폼 제출을 `POST -> redirect -> GET`으로 끝내서, beginner가 헷갈리는 "`POST` 뒤 `504`", "`303` redirect", "`201 Created` JSON"을 서로 다른 흐름으로 분리하게 돕는 브라우저 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 상태 코드 기초](./http-status-codes-basics.md)
- [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)
- [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- [SSR View Render vs JSON API Response Basics](./ssr-view-render-vs-json-api-response-basics.md)
- [Cookie / Session / JWT 브라우저 흐름 입문](./cookie-session-jwt-browser-flow-primer.md)
- [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)

retrieval-anchor-keywords: prg pattern beginner, post redirect get basics, redirect after post intro, 504 after post timeout why, 303 see other form submit, 201 created vs 303 see other, form submit flow beginner, post timeout vs redirect vs json, 새로고침하면 다시 제출돼요, 왜 post 다음 get, 언제 303 언제 201, 처음 prg, 헷갈리는 form submit, what is post redirect get

## 핵심 개념

PRG는 이름 그대로 `POST -> Redirect -> GET`이다. beginner가 자주 겪는 증상은 이렇다.

- 등록 버튼을 눌렀다.
- 완료 화면은 떴다.
- 그런데 새로고침이 무섭다.

이때 핵심 질문은 "브라우저가 마지막에 기억하는 요청이 `POST`인가 `GET`인가"다.

| 마지막에 브라우저가 기억하는 것 | 새로고침 느낌 |
|---|---|
| `POST` | 같은 제출이 다시 갈까 불안하다 |
| `GET` | 결과 화면을 다시 조회한다고 읽기 쉽다 |

PRG는 이 마지막 요청을 `GET`으로 바꾸는 패턴이다.

## PRG를 볼 때 먼저 체크할 3칸

PRG는 이름이 길어서 복잡해 보이지만, trace에서는 아래 3칸만 보면 된다.

| 먼저 볼 칸 | 기대 신호 | 초보자용 해석 |
|---|---|---|
| 첫 요청 메서드 | `POST` | 무언가를 제출했다 |
| redirect 응답 | `303` + `Location` | 결과 화면 주소를 따로 알려 준다 |
| 마지막 도착 요청 | `GET` | 새로고침 대상이 이제 결과 조회다 |

이 3칸이 보이면 "`왜 POST 다음 GET이 보여요?`"는 이상 현상보다 PRG 정상 흐름일 가능성이 높다.

## 가장 작은 예시

| 순서 | trace에서 보이는 것 | 초보자용 해석 |
|---|---|---|
| 1 | `POST /orders` | 주문 생성 요청 |
| 2 | `303 See Other` + `Location: /orders/42` | 결과 화면은 저 URL에서 다시 열어라 |
| 3 | `GET /orders/42 -> 200 OK` | 브라우저가 결과 화면을 열었다 |

그래서 새로고침 대상은 `POST /orders`가 아니라 `GET /orders/42`가 된다.

## `201`과 `303`은 무엇이 다를까

이 문서에서는 "브라우저 결과 화면을 어떻게 끝낼까" 기준으로만 구분하면 충분하다.

| 지금 끝내고 싶은 것 | 더 잘 맞는 응답 | beginner 감각 |
|---|---|---|
| 생성 성공 자체를 API 응답으로 바로 돌려주기 | `201 Created` | API 계약 중심 |
| 폼 제출 뒤 결과 화면을 다른 URL의 `GET`으로 열기 | `303 See Other` | 브라우저 새로고침 안전성 중심 |

짧게 외우면 이렇다.

- `201`: 생성 결과를 지금 응답에서 끝낸다.
- `303`: 결과 화면을 다른 URL의 `GET`으로 넘긴다.

여기서 beginner가 놓치기 쉬운 한 줄은 이것이다.

- `201`은 API 응답 계약 질문이다.
- `303`은 브라우저 화면 이동 질문이다.

## 헷갈리는 세 장면을 먼저 자르기

form submit에서 beginner가 가장 많이 섞는 장면은 아래 세 개다. 셋 다 "`POST /orders`를 눌렀다"로 시작하지만, **브라우저가 지금 무엇을 받았는지**가 다르다.

| 장면 | Network에서 먼저 보이는 것 | 뜻 | 바로 다음 질문 |
|---|---|---|---|
| timeout 장면 | `POST /orders -> 504 Gateway Timeout` | 앞단이 기다리다 포기했다. 생성 성공/실패는 아직 분리되지 않았다 | 첫 `POST`가 서버에서 실제 처리됐는가 |
| PRG 장면 | `POST /orders -> 303 Location: /orders/42 -> GET /orders/42` | 브라우저가 결과 화면을 `GET`으로 다시 열었다 | 새로고침 대상이 이제 `GET`인가 |
| JSON API 장면 | `POST /api/orders -> 201 Created` + JSON body | 생성 결과를 API 응답으로 바로 돌려줬다 | 프론트 코드가 성공 후 화면을 어떻게 바꿀까 |

짧게 외우면 아래처럼 나눈다.

- `504`: "끝났는지 아직 확신 못 한다."
- `303`: "결과 화면은 다른 URL의 `GET`으로 보라."
- `201`: "생성 결과 데이터는 지금 JSON으로 받는다."

이 비교에서 중요한 점은 `504`가 `303`이나 `201`의 대체물이 아니라는 것이다.

- `504`는 **성공 후속 흐름**이 아니라 **timeout 관찰 결과**다.
- `303`은 브라우저용 **이동 방식**이다.
- `201`은 API용 **성공 응답 계약**이다.

그래서 "`POST` 뒤 `504`를 봤는데 원래 `201`이 나와야 하나요, `303`이 나와야 하나요?"라는 질문은 순서를 바꿔 읽어야 한다.

1. 첫 `POST`가 실제로 처리됐는지 확인한다.
2. 이 endpoint가 브라우저 폼 흐름인지 JSON API 흐름인지 구분한다.
3. 브라우저 폼이면 `303` 같은 PRG를, JSON API면 `201` 같은 API 계약을 기대한다.

## 왜 `303` 다음에 `304`가 보여도 정상일까

PRG를 이해한 뒤에도 "`새로고침했더니 왜 또 `304`가 보여요?`"에서 자주 멈춘다.

| 순서 | 보이는 것 | 질문 축 |
|---|---|---|
| `POST /orders -> 303` | 어디로 다시 갈까 | redirect 질문 |
| `GET /orders/42 -> 200` | 결과 화면을 열었다 | PRG 마무리 |
| 새로고침 뒤 `GET /orders/42 -> 304` | body를 다시 받을까 | cache 질문 |

즉 `303`은 목적지 URL을 바꾸고, `304`는 같은 URL의 body 재사용 여부를 말한다. 둘은 같은 trace에 같이 보여도 정상이다.

## PRG가 해결하는 것과 해결하지 않는 것

| 질문 | PRG가 직접 다루는가 | 초보자용 설명 |
|---|---|---|
| 새로고침할 때 같은 `POST`가 다시 갈까 | 예 | 마지막 요청을 `GET`으로 바꾼다 |
| 브라우저의 "양식 다시 제출" 경고를 줄일까 | 예 | 완료 화면을 `GET`으로 분리한다 |
| 더블클릭, 모바일 재시도, 서버 중복 생성까지 막을까 | 아니오 | 서버 중복 방지는 다른 층의 문제다 |

PRG는 브라우저 UX 범위의 패턴이지, 중복 방지 전체 설계가 아니다.

## redirect, forward와도 섞이지 않게 보기

PRG를 읽을 때 "`그럼 redirect랑 같은 말인가요?`"에서 다시 막히기도 한다.

| 지금 궁금한 것 | 먼저 붙일 이름 | 왜 |
|---|---|---|
| `POST` 뒤 결과 화면이 `GET`으로 열렸는가 | PRG | 새로고침 안전성 질문이다 |
| 누가 이동을 결정했는가 | redirect/forward/SPA navigation | 이동 주체 질문이다 |

즉 PRG는 보통 redirect를 사용하지만, redirect 전체와 같은 뜻은 아니다. 이동 방식 자체가 더 헷갈리면 [Redirect vs Forward vs SPA Router Navigation 입문](./redirect-vs-forward-vs-spa-navigation-basics.md)으로 한 칸 옮겨 읽으면 된다.

## 흔한 오해

- PRG를 쓰면 중복 생성이 완전히 끝난다고 생각한다.
- `POST` 직후 `GET`이 보이면 이상하다고 생각한다. 브라우저 form submit에서는 흔한 정상 흐름이다.
- `201`과 `303`을 둘 중 하나만 정답이라고 생각한다. 브라우저 화면 흐름과 API 계약의 질문이 다르다.
- `504`를 봤으니 결국 `303`이나 `201` 중 하나는 "안 나온 것"이라고 생각한다. 실제로는 timeout 때문에 관찰이 끊긴 것일 수 있고, app은 뒤늦게 성공했을 수도 있다.
- 로그인 성공 redirect까지 한꺼번에 깊게 파고든다. beginner는 먼저 "왜 `POST` 뒤 `GET`이 보이나"만 잡으면 된다.

## 여기서는 깊게 안 다루는 것

이 문서는 브라우저 폼 submit entry다. 아래는 follow-up으로 넘긴다.

- 로그인 redirect 세부와 `SavedRequest`: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](./login-redirect-hidden-jsessionid-savedrequest-primer.md)
- 서버 중복 방지와 멱등성 설계: [HTTP 메서드와 REST 멱등성 입문](./http-methods-rest-idempotency-basics.md)
- `304`, `from memory cache`, `Disable cache` 실험: [HTTP 캐싱과 조건부 요청 기초: Cache-Control, ETag, Last-Modified, 304](./http-caching-conditional-request-basics.md)
- `504`를 본 뒤 첫 `POST` 성공 여부와 중복 제출 위험을 더 직접적으로 가르려면 [Browser `504` 뒤 재시도 vs 새로고침 vs 중복 제출 Beginner Bridge](./browser-504-retry-vs-refresh-vs-duplicate-submit-beginner-bridge.md)
- SSR 폼 제출과 JSON API `201`이 응답 계약에서 어떻게 갈리는지 보려면 [SSR View Render vs JSON API Response Basics](./ssr-view-render-vs-json-api-response-basics.md)

## 한 줄 정리

PRG는 브라우저 폼 제출을 `POST -> 303 -> GET`으로 바꿔 새로고침 재전송을 줄이는 패턴이고, `504 timeout` 관찰이나 `201 JSON` API 성공 계약과는 다른 질문으로 읽어야 한다.
