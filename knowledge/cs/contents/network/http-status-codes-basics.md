# HTTP 상태 코드 기초

> 한 줄 요약: HTTP 상태 코드는 서버가 요청을 어떻게 처리했는지 세 자리 숫자로 알려주는 신호이고, 앞 자리 하나가 성공/실패/리다이렉션을 결정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 메서드, REST, 멱등성 기초](./http-methods-rest-idempotency-basics.md)
- [HTTP와 HTTPS 기초](./http-https-basics.md)
- [network 카테고리 인덱스](./README.md)
- [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle-basics.md)

retrieval-anchor-keywords: http status codes basics, 상태 코드 뭐예요, 404 뭔가요, 500 에러 왜 나요, http 응답 코드 입문, 2xx 3xx 4xx 5xx 차이, 상태 코드 처음 배우는데, 200 ok, 201 created, beginner status code

## 핵심 개념

브라우저나 앱이 서버에 요청을 보내면, 서버는 응답의 첫 줄에 세 자리 숫자를 담아 결과를 알려준다. 이게 **HTTP 상태 코드**다. 앞 자리 숫자가 1이면 정보, 2이면 성공, 3이면 리다이렉션, 4이면 클라이언트 오류, 5이면 서버 오류다. 입문자가 헷갈리는 지점은 4xx와 5xx를 구분하지 못하는 것이다. 4xx는 요청 자체가 잘못됐고, 5xx는 요청은 맞지만 서버가 처리하다 실패한 상황이다.

## 한눈에 보기

| 계열 | 의미 | 대표 코드 |
|---|---|---|
| 2xx | 성공 | 200 OK, 201 Created, 204 No Content |
| 3xx | 리다이렉션 | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | 클라이언트 오류 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | 서버 오류 | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

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

## 흔한 오해와 함정

- 401과 403을 혼동한다. 401은 "누구냐"를 모르는 상태, 403은 "누군지 알지만 허용 안 함"이다.
- 200만 성공이라고 생각하지만, 201·204도 성공이다. REST API에서는 생성·삭제 후 응답 코드를 올바르게 설정해야 클라이언트가 결과를 해석할 수 있다.
- 5xx가 나오면 클라이언트 코드를 고쳐야 한다고 오해한다. 5xx는 서버 쪽 문제다. 서버 로그를 봐야 원인을 찾을 수 있다.

## 실무에서 쓰는 모습

Spring Boot REST 컨트롤러에서 `@ResponseStatus(HttpStatus.CREATED)`를 붙이거나 `ResponseEntity.created(uri).build()`를 반환하면 201이 내려간다. 클라이언트는 이 코드를 보고 "리소스가 만들어졌구나"를 알 수 있다. 404가 자주 발생한다면 클라이언트와 서버의 URL 경로 계약이 맞지 않다는 신호다.

## 더 깊이 가려면

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
