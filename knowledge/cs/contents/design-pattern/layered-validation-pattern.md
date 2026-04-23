# Layered Validation Pattern: 입력, 도메인, 정책을 층별로 검증하기

> 한 줄 요약: Layered Validation은 형식 검증, 도메인 불변식, 정책 판정을 한 번에 섞지 않고 층별로 나눠 책임을 분리하는 패턴 언어다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Specification Pattern](./specification-pattern.md)
> - [Policy Object Pattern](./policy-object-pattern.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [Command Handler Pattern](./command-handler-pattern.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

검증은 보통 하나처럼 보이지만 실제로는 서로 다른 층의 문제다.

- 입력 검증: 타입, 형식, 길이, 필수값
- 도메인 검증: 불변식, 상태 전이, 관계 규칙
- 정책 검증: 권한, 한도, 요금, 운영 규칙

이 층을 섞으면 에러 메시지도, 책임도, 테스트도 흐려진다.

### Retrieval Anchors

- `layered validation`
- `input domain policy validation`
- `validation tiers`
- `invariant enforcement`
- `cross-cutting validation`

---

## 깊이 들어가기

### 1. 검증은 하나의 if문이 아니다

입력 형식이 맞는지, 도메인적으로 허용되는지, 현재 정책상 가능한지는 서로 다르다.

- 입력 검증은 요청을 거절할지 결정한다
- 도메인 검증은 객체 상태를 보호한다
- 정책 검증은 상황별 허용 여부를 결정한다

### 2. 각 층은 실패 의미가 다르다

같은 실패라도 의미가 다르면 응답도 다르게 다뤄야 한다.

- 입력 오류: 400 계열
- 도메인 불변식 위반: 서버 내부 규칙 오류
- 정책 위반: 403/409 같은 비즈니스 오류

### 3. Specification과 Policy Object가 잘 맞는다

조건 조합이 많으면 Specification, 결과와 사유가 필요하면 Policy Object가 유용하다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 API

DTO 검증, 주문 불변식, 쿠폰 정책을 분리하면 에러 응답이 명확해진다.

### 시나리오 2: 결제 승인

형식 검증, 금액 한도 검증, PG 정책 검증을 나눠야 운영이 쉽다.

### 시나리오 3: 관리자 기능

권한, 상태, 기간 조건이 섞이면 한 단계씩 분리해야 한다.

---

## 코드로 보기

### 입력 검증

```java
public class PlaceOrderRequestValidator {
    public void validate(PlaceOrderRequest request) {
        if (request.userId() == null) {
            throw new IllegalArgumentException("userId is required");
        }
    }
}
```

### 도메인 검증

```java
public class Order {
    public void addItem(OrderItem item) {
        if (item.quantity() <= 0) {
            throw new IllegalStateException("quantity must be positive");
        }
    }
}
```

### 정책 검증

```java
public interface OrderPolicy {
    boolean canPlace(Order order, PolicyContext context);
}
```

### 흐름

```java
validator.validate(request);
Order order = Order.place(request);
if (!policy.canPlace(order, context)) {
    throw new IllegalStateException("policy rejected");
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 검증 함수 | 짧다 | 의미가 섞인다 | 아주 단순할 때 |
| Layered Validation | 실패 의미가 분명하다 | 구조가 조금 길다 | 규칙이 여러 층일 때 |
| 전부 정책 객체 | 재사용이 쉽다 | 입력 형식까지 무겁다 | 정책 중심 시스템 |

판단 기준은 다음과 같다.

- 형식/도메인/정책이 다르면 층을 나눈다
- 에러 의미가 다르면 응답도 분리한다
- 도메인 불변식은 가장 안쪽에서 막는다

---

## 꼬리질문

> Q: 입력 검증과 도메인 검증은 왜 나눠야 하나요?
> 의도: 실패 의미와 책임 경계를 구분하는지 확인한다.
> 핵심: 입력은 외부 형식, 도메인은 내부 규칙이다.

> Q: 정책 검증은 어디에 두는 게 좋나요?
> 의도: 정책 객체와 유스케이스 계층의 역할을 아는지 확인한다.
> 핵심: 정책 객체나 application service 주변이 적절하다.

> Q: 검증 층이 많아지면 어떤 위험이 있나요?
> 의도: 분리와 파편화를 구분하는지 확인한다.
> 핵심: 과도하면 흐름이 보이지 않으니 꼭 필요한 층만 둔다.

## 한 줄 정리

Layered Validation은 형식, 도메인, 정책 검증을 분리해 실패 의미와 책임 경계를 명확하게 하는 패턴 언어다.

