# BFF Boundaries and Client-Specific Aggregation

> 한 줄 요약: BFF는 API를 한 번 더 감싸는 층이 아니라, 각 클라이언트의 화면, latency, auth, payload shape에 맞게 경계를 재배치하는 전용 적응층이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [gRPC vs REST](../network/grpc-vs-rest.md)
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

> retrieval-anchor-keywords:
> - BFF
> - backend for frontend
> - client-specific aggregation
> - API gateway boundary
> - screen-level composition
> - mobile payload shaping
> - auth context
> - anti-corruption layer

## 핵심 개념

BFF(Backend for Frontend)는 클라이언트 종류마다 다른 요구를 흡수하기 위한 **전용 오케스트레이션 계층**이다.

중요한 점은 BFF를 "프론트엔드용 백엔드"라고만 부르면 절반만 맞는다는 것이다.

- 모바일은 네트워크 왕복을 줄여야 한다
- 웹은 화면 전환 단위로 데이터를 모아야 한다
- 관리자 화면은 조회보다 조작 권한과 감사 로그가 더 중요하다
- 외부 파트너 화면은 내부 도메인보다 계약 안정성이 우선이다

BFF의 가치는 이 차이를 숨기지 않고, 오히려 **클라이언트별로 다른 경계가 필요함을 인정하는 것**에 있다.

---

## 깊이 들어가기

### 1. BFF는 API Gateway와 다르다

API Gateway는 공통 진입점과 횡단 관심사를 담당한다.

- 인증
- 라우팅
- rate limit
- TLS termination
- 공통 로깅

BFF는 그보다 더 화면과 상호작용에 가깝다.

- 화면 조합
- 필드 축약
- 비동기 호출 묶기
- 클라이언트별 에러 재구성

즉 Gateway는 "모든 트래픽의 문지기"이고, BFF는 **클라이언트별 해석기**에 가깝다.

### 2. BFF는 도메인 로직을 소유하면 안 된다

BFF가 편해 보인다고 해서 비즈니스 규칙까지 넣기 시작하면 경계가 무너진다.

좋은 BFF:

- 주문 상세에서 결제, 배송, 쿠폰 상태를 모아 보여준다
- 모바일에 필요한 필드만 골라 응답한다
- 외부 시스템의 느린 응답을 합성한다

나쁜 BFF:

- 주문 할인 정책을 직접 계산한다
- 결제 가능 여부를 BFF 안에서 판정한다
- 도메인 상태를 BFF가 원천 데이터처럼 관리한다

도메인 규칙은 원 서비스에 남기고, BFF는 **읽기/조합/번역**에 집중해야 한다.

### 3. 클라이언트별 응답 shape는 다를 수 있다

같은 주문 데이터라도 클라이언트마다 필요한 모양이 다르다.

| 클라이언트 | 필요한 것 | 불필요한 것 |
|---|---|---|
| 모바일 앱 | 최소 payload, 빠른 응답 | 상세 내부 상태, 관리자용 메타데이터 |
| 웹 앱 | 화면 단위 조합, 인터랙션 정보 | 저수준 시스템 필드 |
| 관리자 콘솔 | 감사, 필터, 운영 정보 | 과도한 캐싱 가정 |

여기서 핵심은 "모든 클라이언트가 같은 DTO를 써야 한다"는 가정이 오히려 결합도를 높인다는 점이다.

### 4. BFF는 ACL과 겹치지만 같은 것은 아니다

ACL은 외부 모델이 내부를 오염시키지 못하게 막는다.
BFF는 클라이언트 요청을 화면 단위로 맞춘다.

겹치는 순간:

- 외부 파트너 API를 BFF가 대신 호출한다
- 클라이언트 요구를 내부 도메인 언어로 번역한다

차이점:

- ACL의 중심은 도메인 보호
- BFF의 중심은 클라이언트 경험

둘을 섞으면 번역 계층이 너무 많아지거나, 반대로 경계가 너무 넓어질 수 있다.

### 5. BFF가 많아질수록 중복도 관리해야 한다

클라이언트가 여러 개라고 해서 BFF를 무한히 늘리면 안 된다.

위험 신호:

- 동일한 조합 로직이 여러 BFF에 복붙된다
- 공통 인증/정책이 제각각 구현된다
- 어떤 화면이 어떤 BFF에 소속되는지 모호하다

이때 필요한 것은 "BFF를 더 만든다"가 아니라, **공통 경계와 개별 경계를 다시 나누는 작업**이다.

---

## 실전 시나리오

### 시나리오 1: 모바일 주문 상세 화면

모바일 앱은 주문 상세를 열 때 아래가 필요하다.

- 주문 기본 정보
- 결제 상태
- 배송 추적
- 쿠폰 사용 여부

원 서비스 4개를 각각 호출하면 왕복이 너무 많다.
이때 BFF는 한 번에 묶어서 응답한다.

### 시나리오 2: 관리자 화면과 고객 화면이 같은 API를 쓰려 한다

고객 화면은 "주문 완료"만 보여주면 된다.
관리자 화면은 취소 사유, 결제 실패 코드, 재처리 가능 여부까지 필요하다.

같은 API를 억지로 쓰면:

- 고객 화면에는 과도한 정보가 노출된다
- 관리자 화면은 불필요한 필터링을 BFF에 덧댄다

이 경우 BFF를 분리하는 편이 더 안전하다.

### 시나리오 3: 외부 파트너 포털

외부 파트너는 내부 도메인을 알 필요가 없다.

- 내부 `orderState=AWAITING_FULFILLMENT`
- 외부 `status=READY_TO_SHIP`

이런 매핑은 BFF가 하되, 내부 상태 모델은 그대로 유지한다.

---

## 코드로 보기

```java
public class OrderDetailBff {
    private final OrderQueryClient orderQueryClient;
    private final PaymentQueryClient paymentQueryClient;
    private final ShippingQueryClient shippingQueryClient;

    public OrderDetailView getOrderDetail(String orderId, ClientType clientType) {
        OrderSummary order = orderQueryClient.findById(orderId);
        PaymentSummary payment = paymentQueryClient.findByOrderId(orderId);
        ShippingSummary shipping = shippingQueryClient.findByOrderId(orderId);

        return switch (clientType) {
            case MOBILE -> OrderDetailView.mobile(order, payment, shipping);
            case WEB -> OrderDetailView.web(order, payment, shipping);
            case ADMIN -> OrderDetailView.admin(order, payment, shipping);
        };
    }
}
```

이 예제에서 BFF는 데이터를 모으고 표현을 바꾼다.
대신 결제 승인 판단, 배송 가능 여부 계산 같은 규칙은 넣지 않는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 공용 API 하나 | 구현이 단순하다 | 클라이언트가 내부 모델에 끌려간다 | 클라이언트가 거의 없을 때 |
| BFF 분리 | 화면 단위 최적화가 쉽다 | 운영/배포 단위가 늘어난다 | 클라이언트 경험이 다를 때 |
| BFF + ACL | 외부와 내부를 함께 보호한다 | 번역 계층이 늘어난다 | 외부 연동이 많고 도메인 보호가 중요할 때 |

BFF는 편의 기능이 아니라 **클라이언트 경계의 명시화**다.

---

## 꼬리질문

- BFF가 어디까지 조합하고, 어디서부터 도메인 서비스를 호출해야 하는가?
- 공통 응답 모델과 클라이언트별 응답 모델을 어떻게 분리할 것인가?
- BFF가 늘어날 때 중복 로직은 어디로 회수할 것인가?
- 화면 요구가 아니라 도메인 요구가 BFF를 끌고 오고 있지는 않은가?

## 한 줄 정리

BFF는 프론트엔드 편의 계층이 아니라, 클라이언트마다 다른 요구를 안전하게 흡수하기 위한 경계 재설계 장치다.
