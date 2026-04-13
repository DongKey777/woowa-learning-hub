# Modular Monolith Boundary Enforcement

> 한 줄 요약: 모듈러 모놀리스는 "하나의 배포"가 아니라, 도메인 경계를 코드로 강제해 분산 모놀리스로 무너지는 걸 막는 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Clean Architecture vs Layered Architecture, Modular Monolith](./clean-architecture-layered-modular-monolith.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Monolith → MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Anti-Corruption Layer Integration Patterns](./anti-corruption-layer-integration-patterns.md)

## 핵심 개념

모듈러 모놀리스는 코드와 패키지를 기준으로 도메인 경계를 분리하지만, 배포는 하나로 유지하는 구조다.
핵심은 분리 자체가 아니라 **경계를 강제하는 방식**이다.

경계가 약하면:

- 다른 모듈의 내부 클래스를 직접 참조한다
- 서비스 간 순환 의존이 생긴다
- 결국 "패키지만 나뉜 큰 클래스들"이 된다

즉, 모듈러 모놀리스는 **분할된 설계의 규칙을 강제하는 구조**다.

## 깊이 들어가기

### 1. 패키지 분리만으로는 부족하다

```text
order/
payment/
delivery/
```

이렇게 폴더만 나눠서는 경계가 생기지 않는다.
경계를 강제하려면:

- 모듈 간 직접 참조를 금지한다
- 외부는 공개 인터페이스만 보게 한다
- 내부 도메인 객체를 외부로 새지 않게 한다
- 테스트도 경계를 넘지 않도록 한다

### 2. 경계 enforcement 수단

| 수단 | 효과 |
|------|------|
| 패키지 접근 제한 | 내부 구현 은닉 |
| 인터페이스/포트 분리 | 외부 의존 축소 |
| 모듈 테스트 분리 | 경계 침범 조기 발견 |
| 정적 분석/아키텍처 테스트 | 의존 방향 강제 |

### 3. MSA 전환 전 단계로서의 가치

모듈러 모놀리스는 보통 MSA 직전이 아니라, **아직 쪼개면 안 되는 팀이 경계를 연습하는 단계**로 유용하다.
경계를 먼저 강제해두면 나중에 서비스 분리가 훨씬 쉽다.

## 실전 시나리오

### 시나리오 1: 결제 모듈이 주문의 내부 엔티티를 직접 참조

처음엔 편하다.
하지만 주문 엔티티 변경이 결제 모듈까지 확장되고, 결국 두 팀이 같은 모델을 공유하게 된다.

이건 모듈러 모놀리스가 아니라 분산 모놀리스의 전조다.

### 시나리오 2: 순환 의존

- `order`가 `payment`를 호출
- `payment`가 `inventory`를 호출
- `inventory`가 다시 `order`를 참조

이 구조는 작은 시스템에서는 돌아가도, 변경 비용이 급격히 커진다.

### 시나리오 3: ACL 없이 외부 시스템을 직접 연결

외부 API 스펙이 바뀔 때 내부 도메인이 같이 흔들린다.
모듈러 경계와 ACL이 있으면 외부 변경을 흡수할 수 있다.

## 코드로 보기

```java
// order 모듈이 제공하는 공개 인터페이스
public interface OrderQuery {
    OrderSummary findSummary(long orderId);
}

// payment 모듈은 order 내부 엔티티를 보지 않고 인터페이스만 의존한다
public class PaymentService {
    private final OrderQuery orderQuery;

    public PaymentService(OrderQuery orderQuery) {
        this.orderQuery = orderQuery;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 단일 패키지 모놀리스 | 단순하다 | 경계가 없다 | 아주 작은 팀 |
| 패키지 분리만 | 구조는 나뉜다 | enforcement가 약하다 | 초반 실험 단계 |
| 모듈러 모놀리스 | 경계 강제 가능 | 규칙이 필요하다 | 성장하는 팀 |
| 바로 MSA | 독립 배포 가능 | 운영 복잡도 높다 | 경계가 이미 증명된 경우 |

## 꼬리질문

- 패키지 분리와 모듈 경계 강제는 왜 다른가?
- 모듈러 모놀리스가 분산 모놀리스로 변하는 신호는 무엇인가?
- 아키텍처 테스트를 어디까지 자동화할 것인가?
- 모듈 간 데이터 복사는 언제 허용하고 언제 금지할 것인가?

## 한 줄 정리

모듈러 모놀리스는 패키지 나눔이 아니라, 도메인 경계와 의존 방향을 코드로 강제하는 구조다.
