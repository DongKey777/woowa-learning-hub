# API Gateway 기초 (API Gateway Basics)

> 한 줄 요약: API Gateway는 클라이언트와 백엔드 서비스 사이에 앉아 인증, 라우팅, 속도 제한, 로깅을 한 곳에서 처리하는 관문 역할을 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md)
- [API 설계와 예외 처리](../software-engineering/api-design-error-handling.md)
- [system-design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: api gateway basics, api gateway 뭐예요, api gateway 입문, reverse proxy vs api gateway, gateway 역할, 인증 게이트웨이, 라우팅 기초, rate limiting gateway, api 관문, beginner api gateway, 백엔드 요청 흐름, gateway 와 로드밸런서 차이, api gateway basics basics, api gateway basics beginner, api gateway basics intro

---

## 핵심 개념

API Gateway는 "API 호출을 받아 적절한 백엔드로 전달하는 중간 서버"다.
입문자가 자주 헷갈리는 지점은 **로드밸런서와 어떻게 다른가**이다.

- 로드밸런서: 같은 서비스의 여러 인스턴스로 트래픽을 분산한다.
- API Gateway: 다른 백엔드 서비스들을 하나의 엔드포인트로 묶고, 공통 처리를 한곳에서 맡는다.

예를 들어 클라이언트가 `/users/me`와 `/orders/recent`를 각각 다른 마이크로서비스에서 받아야 한다면, API Gateway가 적절한 서비스로 라우팅한다.

---

## 한눈에 보기

```text
클라이언트
  -> API Gateway
       [인증 확인]
       [속도 제한 적용]
       [요청 로깅]
       -> 사용자 서비스 (GET /users/me)
       -> 주문 서비스 (GET /orders/recent)
       -> 상품 서비스 (GET /products/123)
```

Gateway가 처리하는 대표적인 공통 기능:

| 기능 | 설명 |
|---|---|
| 인증/인가 | 토큰 검증을 한곳에서 처리 |
| Rate Limiting | IP/사용자별 요청 수 제한 |
| 라우팅 | URL 패턴에 따라 서비스 분기 |
| 로깅/추적 | 모든 요청의 공통 로그 수집 |
| 프로토콜 변환 | HTTP ↔ gRPC 등 변환 |

---

## 상세 분해

API Gateway가 처리하는 주요 역할을 나눠 보면:

- **인증 처리**: 모든 서비스가 각자 토큰 검증 코드를 갖지 않아도 된다. Gateway 한 곳에서 검증하고 통과한 요청만 내부로 보낸다.
- **라우팅**: `/api/v1/users/*`는 사용자 서비스, `/api/v1/orders/*`는 주문 서비스처럼 경로 기반으로 분기한다.
- **속도 제한**: 악의적인 요청이나 과도한 호출을 Gateway에서 차단해 백엔드 서비스를 보호한다.
- **응답 집계**: 여러 서비스 결과를 하나로 합쳐 반환하는 경우도 있다 (BFF 패턴에서 자주 쓰인다).

---

## 흔한 오해와 함정

- **"API Gateway를 넣으면 모든 문제가 해결된다"**: Gateway는 관통 경로를 단순화하지만, 단일 장애점이 될 수 있다. Gateway 자체의 고가용성 설계가 필요하다.
- **"Gateway는 로드밸런서 대체재다"**: 둘은 협력 관계다. 보통 로드밸런서 뒤에 Gateway를 두거나, Gateway 뒤에 각 서비스의 로드밸런서를 둔다.
- **"Gateway에 비즈니스 로직을 넣어도 된다"**: Gateway는 인프라 레이어다. 비즈니스 판단은 백엔드 서비스가 담당해야 한다. Gateway에 도메인 로직이 쌓이면 관리가 어려워진다.

---

## 실무에서 쓰는 모습

가장 흔한 시나리오는 모바일/웹 클라이언트가 여러 마이크로서비스를 호출할 때다.

1. 앱이 `POST /api/v1/orders`를 호출한다.
2. Gateway가 Authorization 헤더를 검증한다.
3. 초당 요청 수가 허용 범위 안인지 확인한다.
4. 주문 서비스로 라우팅하고 응답을 클라이언트에 돌려준다.
5. 요청 ID, 지연 시간, 상태 코드를 로그에 기록한다.

이 흐름에서 각 서비스는 인증 코드나 rate limit 코드를 갖지 않아도 된다.

---

## 더 깊이 가려면

- [API Gateway Control Plane 설계](./api-gateway-control-plane-design.md) — 구성 변경, 정책 배포, 동적 라우팅까지
- [API 설계와 예외 처리](../software-engineering/api-design-error-handling.md) — Gateway 뒤 서비스의 API 설계 원칙

---

## 면접/시니어 질문 미리보기

> Q: API Gateway와 로드밸런서의 차이는 무엇인가요?
> 의도: 두 컴포넌트의 책임 범위를 구분하는지 확인
> 핵심: 로드밸런서는 같은 서비스의 여러 인스턴스 사이 분산, Gateway는 여러 서비스로의 라우팅과 공통 정책 적용이 주 역할이다.

> Q: API Gateway에 비즈니스 로직을 넣으면 어떤 문제가 생기나요?
> 의도: 인프라와 도메인 레이어 분리 감각 확인
> 핵심: Gateway가 도메인 로직을 알게 되면 서비스별 정책이 Gateway에 분산되고, 변경 시 Gateway를 배포해야 해서 병목이 생긴다.

> Q: API Gateway가 없으면 어떤 일이 생기나요?
> 의도: Gateway 도입 동기 이해 확인
> 핵심: 각 서비스가 인증, 로깅, rate limit을 중복 구현하고, 클라이언트는 모든 서비스 주소를 알아야 한다.

---

## 한 줄 정리

API Gateway는 클라이언트와 여러 백엔드 서비스 사이에서 인증, 라우팅, 속도 제한, 로깅을 한곳에서 처리하는 관문이며, 각 서비스가 공통 인프라 코드를 갖지 않아도 되게 해준다.
