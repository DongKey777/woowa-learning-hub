# HTTP 메서드와 REST 멱등성 입문

> 한 줄 요약: GET/POST/PUT/DELETE 등 HTTP 메서드는 리소스에 어떤 동작을 할지 의도를 표현하며, 멱등성은 같은 요청을 여러 번 보내도 결과가 달라지지 않는 성질이다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: http 메서드 기초, rest api 기초, http method 뭐가 있나요, get post put delete 차이, 멱등성이 뭐예요, idempotent 뜻, safe method 뜻, rest 란, rest api 설계 입문, 리소스 기반 api, http method beginner, http to spring mvc beginner route, http method spring controller mapping entry

## 핵심 개념

HTTP 메서드는 클라이언트가 서버에 "이 리소스에 무엇을 하고 싶다"는 의도를 전달하는 방법이다. 입문자가 흔히 헷갈리는 지점은 GET과 POST만 알고, PUT/PATCH/DELETE를 왜 구분해서 쓰는지 모르는 것이다. 메서드를 올바르게 쓰면 클라이언트·서버·프록시·캐시 모두가 같은 의도를 이해하고 더 예측 가능하게 동작한다.

## 한눈에 보기

| 메서드 | 주요 의도 | 안전(Safe) | 멱등(Idempotent) |
|---|---|---|---|
| GET | 조회 | 그렇다 | 그렇다 |
| HEAD | 헤더만 조회 | 그렇다 | 그렇다 |
| POST | 생성·처리 | 아니다 | 아니다 |
| PUT | 전체 교체 | 아니다 | 그렇다 |
| PATCH | 부분 수정 | 아니다 | 상황에 따라 다르다 |
| DELETE | 삭제 | 아니다 | 그렇다 |

## 상세 분해

### 안전(Safe) 메서드란

요청을 보내도 **서버 상태가 변하지 않는다는 보장**이 있는 메서드다. GET, HEAD가 여기 속한다. 브라우저와 프록시는 안전 메서드를 자유롭게 다시 보내도 된다고 가정한다.

### 멱등(Idempotent) 메서드란

**같은 요청을 여러 번 보내도 결과가 처음 한 번과 동일한** 메서드다. GET, PUT, DELETE가 멱등이다.

예: `DELETE /orders/42`를 두 번 보내면 두 번째는 이미 없어서 404가 나올 수 있지만, **서버 상태는 "주문 42가 없다"로 동일**하다.

### POST는 왜 멱등이 아닌가

`POST /orders`를 두 번 보내면 주문이 두 개 생길 수 있다. 매번 새 리소스가 생기거나 새 동작이 실행되기 때문이다.

### REST의 기본 발상

REST는 URI로 **리소스**를 표현하고, HTTP 메서드로 **동작**을 표현한다.

```
GET    /orders        → 주문 목록 조회
POST   /orders        → 새 주문 생성
GET    /orders/42     → 주문 42 조회
PUT    /orders/42     → 주문 42 전체 교체
DELETE /orders/42     → 주문 42 삭제
```

URI에 동사를 넣지 않는 것이 REST 설계의 기본 감각이다. `/getOrder`, `/deleteOrder` 대신 메서드로 동작을 표현한다.

## 흔한 오해와 함정

- "GET에는 body가 없다"는 규칙이 아니라 관례다. 실제로 GET body는 허용되지만 대부분의 서버·라이브러리가 무시한다.
- "POST는 생성, PUT은 수정"처럼 단순히 외우면 안 된다. PUT은 교체(대체), PATCH는 부분 수정이다. PUT으로 이미 없는 리소스를 만들 수도 있다.
- "REST = HTTP API"가 아니다. REST는 아키텍처 스타일이고, HTTP API가 REST를 완전히 따르지 않아도 잘 동작한다.

## 실무에서 쓰는 모습

Spring MVC에서 컨트롤러를 만들 때 메서드 어노테이션이 HTTP 메서드와 직접 대응한다.

```java
@GetMapping("/orders/{id}")    // GET
@PostMapping("/orders")        // POST
@PutMapping("/orders/{id}")    // PUT
@DeleteMapping("/orders/{id}") // DELETE
```

재시도 로직을 설계할 때도 멱등성이 중요하다. GET, PUT, DELETE는 안전하게 재시도할 수 있지만, POST는 중복 처리를 방지하는 추가 장치가 필요하다.

## 다음 단계로 이어 읽기 (Spring 입문 연결)

HTTP 메서드 의미를 잡았으면 바로 아래 순서로 이어 보면 컨텍스트 전환이 줄어든다.

1. [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](../spring/spring-mvc-controller-basics.md)
   `@GetMapping`, `@PostMapping`이 HTTP 메서드와 어떻게 대응되는지 본다.
2. [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](../spring/spring-ioc-di-basics.md)
   컨트롤러가 호출하는 `service`를 왜 `new`하지 않고 주입받는지 붙인다.
3. [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md)
   요청 흐름(MVC)과 객체 준비(Bean/DI)를 한 장으로 다시 정리한다.

## 더 깊이 가려면

- [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md) — PUT vs PATCH, 실전 멱등성 설계 패턴
- [network 카테고리 인덱스](./README.md) — 다음 단계 주제 탐색

## 면접/시니어 질문 미리보기

**Q. GET과 POST의 차이를 설명해 주세요.**
GET은 조회 목적이고 서버 상태를 바꾸지 않아 안전·멱등하며 캐시 대상이 된다. POST는 생성·처리 목적이고 매번 새 결과가 생길 수 있어 멱등하지 않다.

**Q. PUT과 PATCH의 차이는 무엇인가요?**
PUT은 리소스 전체를 교체하고, PATCH는 일부만 변경한다. PUT으로 일부 필드만 보내면 나머지가 사라질 수 있다.

**Q. 멱등성이 왜 중요한가요?**
네트워크 오류로 요청이 재시도될 때 안전하게 다시 보낼 수 있는지 판단 기준이 된다. 멱등한 메서드는 재시도해도 부작용이 없다.

## 한 줄 정리

HTTP 메서드는 리소스에 대한 의도를 선언하고, 멱등성은 그 요청을 안전하게 재시도할 수 있는지 알려주는 성질이다.
