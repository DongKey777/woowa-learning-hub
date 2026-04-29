# HTTP 요청·응답 헤더 기초

> 한 줄 요약: HTTP 헤더는 요청과 응답에 붙는 메타데이터로, 콘텐츠 형식·인증 토큰·캐시 정책·보안 설정 같은 부가 정보를 전달하는 이름-값 쌍이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP와 HTTPS 기초](./http-https-basics.md)
- [HTTP 캐싱과 조건부 요청 기초](./http-caching-conditional-request-basics.md)
- [Browser DevTools `Accept` vs Response `Content-Type` 미니 카드](./browser-devtools-accept-vs-content-type-mini-card.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: http headers basics, 요청 헤더 뭐예요, 응답 헤더 뭐예요, content-type 이란, authorization 헤더, http 헤더 처음 배우는데, request response headers 입문, accept 헤더, 헤더가 왜 필요해요, beginner http headers, http request response headers basics basics, http request response headers basics beginner, http request response headers basics intro, network basics, beginner network

## 핵심 개념

HTTP 메시지는 크게 **헤더(header)** 와 **본문(body)** 으로 나뉜다. 헤더는 "이 메시지에 대한 설명서"다. 클라이언트는 요청 헤더로 자신이 받을 수 있는 형식을 알리고, 서버는 응답 헤더로 본문의 형식과 캐시 정책을 알린다. 입문자가 헷갈리는 점은 헤더가 본문 안에 있다고 생각하는 것이다. 헤더는 본문 앞에 별도로 위치하며 HTTP 프로토콜이 파싱한다.

## 한눈에 보기

| 방향 | 대표 헤더 | 역할 |
|---|---|---|
| 요청 | Content-Type | 요청 본문의 형식 (JSON, form 등) |
| 요청 | Authorization | 인증 토큰 (Bearer token, Basic auth) |
| 요청 | Accept | 클라이언트가 받을 수 있는 응답 형식 |
| 응답 | Content-Type | 응답 본문의 형식 |
| 응답 | Cache-Control | 캐시 정책 (max-age, no-cache 등) |
| 응답 | Set-Cookie | 클라이언트에 쿠키 저장 지시 |

## 상세 분해

### Content-Type

요청 또는 응답의 본문 형식을 알린다. 예: `Content-Type: application/json`은 본문이 JSON이라는 뜻이다. Spring Boot에서 `@RequestBody`가 JSON 파싱을 자동으로 해주는 것도 이 헤더를 보고 판단한다.

자주 쓰는 값:
- `application/json` — JSON 데이터
- `application/x-www-form-urlencoded` — HTML 폼 기본 전송 방식
- `multipart/form-data` — 파일 업로드 시

### Authorization

클라이언트가 서버에 인증 정보를 전달하는 헤더다.
- `Authorization: Bearer <JWT토큰>` — JWT 기반 API 인증에 가장 많이 쓰인다.
- `Authorization: Basic <base64>` — 사용자명:비밀번호를 base64로 인코딩한 방식.

### Accept

클라이언트가 응답으로 받고 싶은 형식을 서버에 알린다. `Accept: application/json`이면 "JSON을 선호한다"는 뜻에 가깝다. 실제 서비스에서는 redirect, 에러 페이지, 브라우저/라이브러리 기본값 같은 이유로 다른 형식이 올 수도 있고, 서버가 협상을 엄격히 적용하면 406 Not Acceptable을 반환할 수도 있다.

DevTools에서 초급자가 가장 먼저 붙이면 좋은 비교는 이것이다.

- request `Accept` = "내가 기대한 응답 형식"
- response `Content-Type` = "서버가 실제로 보낸 응답 형식"

즉 `Accept: application/json`인데 response `Content-Type: text/html`이면, body를 열기 전에도 JSON 기대와 HTML 실제 응답이 어긋났다는 사실부터 먼저 잡으면 된다.

## 흔한 오해와 함정

- Content-Type을 빠뜨리면 서버가 본문을 파싱하지 못한다. Spring Boot에서 POST 요청을 보낼 때 `Content-Type: application/json`을 안 붙이면 `@RequestBody`가 동작하지 않는다.
- Authorization 헤더에 담긴 JWT는 암호화된 게 아니라 서명(signature)만 있다. 페이로드를 base64로 디코딩하면 그대로 읽힌다. 민감한 데이터는 본문에 넣거나 HTTPS를 반드시 써야 한다.
- 헤더 이름은 대소문자를 구분하지 않는다. `content-type`과 `Content-Type`은 같다. 다만 관례상 Pascal-Case로 쓴다.

## 실무에서 쓰는 모습

클라이언트가 Spring Boot API를 호출할 때 `Content-Type: application/json`과 `Authorization: Bearer <token>`을 같이 보낸다. 서버는 Spring Security 필터가 Authorization 헤더를 먼저 검사하고, 통과하면 컨트롤러가 Content-Type을 보고 본문을 역직렬화한다. `@RestController`가 JSON 응답을 내보낼 때 자동으로 `Content-Type: application/json`을 응답 헤더에 추가한다.

## 더 깊이 가려면

- [HTTP 캐싱과 조건부 요청 기초](./http-caching-conditional-request-basics.md) — Cache-Control 헤더 상세
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. Content-Type과 Accept 헤더의 차이를 설명해 주세요.**
Content-Type은 보내는 메시지 본문의 형식을 알리는 헤더고, Accept는 응답으로 받고 싶은 형식을 서버에 알리는 헤더다. 요청에서 Content-Type은 요청 본문, Accept는 원하는 응답 형식이다.

**Q. Authorization 헤더에 JWT를 담을 때 왜 HTTPS가 필수인가요?**
JWT 페이로드는 base64 인코딩이라 암호화가 아니다. 평문 HTTP로 전송하면 토큰이 그대로 도청될 수 있고, 탈취된 토큰으로 요청을 위조할 수 있다. HTTPS로 전송 자체를 암호화해야 한다.

**Q. 헤더 수가 많아지면 성능에 영향이 있나요?**
있다. HTTP/1.1에서는 헤더가 평문으로 매 요청마다 전송된다. HTTP/2는 HPACK 압축으로 중복 헤더를 줄인다. 불필요한 대형 쿠키나 JWT를 모든 요청에 붙이면 헤더 크기가 커져 대역폭 낭비가 된다.

## 한 줄 정리

HTTP 헤더는 본문 앞에 붙는 메타데이터이고, Content-Type·Authorization·Cache-Control이 실무에서 가장 자주 만나는 헤더다.
