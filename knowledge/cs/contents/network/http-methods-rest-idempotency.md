# HTTP 메서드, REST, 멱등성

**난이도: 🟡 Intermediate**

> 신입 백엔드 개발자가 API 설계를 설명할 때 필요한 핵심 정리

> 관련 문서:
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [API Gateway Auth Rate Limit Chain](./api-gateway-auth-rate-limit-chain.md)

retrieval-anchor-keywords: HTTP methods, REST, idempotency, safe method, GET POST PUT PATCH DELETE, resource design, retry safety, API semantics, idempotent request, RESTful API

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [HTTP 메서드의 의미](#http-메서드의-의미)
- [Safe와 Idempotent](#safe와-idempotent)
- [REST를 어떻게 이해해야 하나](#rest를-어떻게-이해해야-하나)
- [Idempotency가 중요한 이유](#idempotency가-중요한-이유)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

백엔드 개발자는 단순히 API를 만들기만 하는 게 아니라,

- 이 요청이 조회인지 변경인지
- 재시도해도 안전한지
- 어떤 메서드가 더 적절한지

를 설명할 수 있어야 한다.

### Retrieval Anchors

- `HTTP methods`
- `REST`
- `idempotency`
- `safe method`
- `GET POST PUT PATCH DELETE`
- `retry safety`
- `API semantics`
- `idempotent request`

---

## HTTP 메서드의 의미

대표 메서드:

- `GET`
  - 조회
- `POST`
  - 생성 / 처리 요청
- `PUT`
  - 전체 교체
- `PATCH`
  - 부분 수정
- `DELETE`
  - 삭제

중요한 건 “이 메서드를 쓰는 관례”가 아니라 **의미**다.

---

## Safe와 Idempotent

### Safe

Safe 메서드는 **서버 상태를 바꾸지 않는 요청**이다.

대표:

- `GET`
- `HEAD`

### Idempotent

멱등적이라는 것은 **같은 요청을 여러 번 보내도 서버의 최종 상태가 같음**을 뜻한다.

예:

- `PUT`
- `DELETE`

는 보통 멱등적이라고 본다.

반면 `POST`는 보통 멱등적이지 않다.

---

## REST를 어떻게 이해해야 하나

REST는 단순히 URL 예쁘게 짓는 규칙이 아니다.

핵심은:

- 리소스를 식별하고
- HTTP 메서드 의미를 지키고
- 상태 전이를 일관되게 표현하는 것

즉 REST스럽다는 것은
“경로 모양”보다 **HTTP 의미를 잘 지키는가**가 더 중요하다.

---

## Idempotency가 중요한 이유

네트워크는 언제든지

- 응답이 늦거나
- 연결이 끊기거나
- 클라이언트가 재시도

할 수 있다.

이때 요청이 멱등적이면 같은 요청을 다시 보내도 안전하다.

예:

- `DELETE /orders/1`
  - 한 번 지우든 두 번 지우든 최종 상태는 “없음”

하지만 `POST /payments`
는 그대로 재시도하면 중복 결제가 생길 수 있다.

그래서 실무에서는 `idempotency key` 같은 개념도 많이 쓴다.

---

## 추천 공식 자료

- MDN HTTP Methods:
  - https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
- MDN Idempotent:
  - https://developer.mozilla.org/en-US/docs/Glossary/Idempotent
- HTTP Semantics RFC:
  - https://httpwg.org/specs/rfc9110.html

---

## 면접에서 자주 나오는 질문

### Q. `PUT`과 `PATCH` 차이는 무엇인가요?

- `PUT`은 리소스 전체 교체 의미에 가깝고,
- `PATCH`는 부분 수정 의미에 가깝다.

### Q. `GET`과 `POST` 차이는 무엇인가요?

- `GET`은 조회 중심, `POST`는 상태 변경이나 처리 요청에 더 자주 사용된다.

### Q. 멱등성이 왜 중요한가요?

- 네트워크 재시도 상황에서 같은 요청을 다시 보내도 안전한지 판단하는 기준이 되기 때문이다.

### Q. RESTful API란 무엇인가요?

- 단순히 URL 모양이 아니라, 리소스와 HTTP 메서드 의미를 일관되게 사용해 상태를 표현하는 API라고 설명할 수 있다.
