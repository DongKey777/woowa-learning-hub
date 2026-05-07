---
schema_version: 3
title: Anti-Corruption Layer Integration Patterns
concept_id: software-engineering/anti-corruption-layer
canonical: true
category: software-engineering
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 89
mission_ids:
- missions/payment
review_feedback_tags:
- anti-corruption-layer
- external-integration
- domain-boundary
aliases:
- Anti-Corruption Layer Integration Patterns
- anti corruption layer
- ACL translation layer
- external DTO leak
- legacy integration boundary
- 외부 시스템 도메인 오염 방지
symptoms:
- 외부 API DTO, status code, error code를 내부 도메인 모델과 use case에 그대로 흘려보내
- Adapter, Facade, Translator, contract test, circuit breaker를 각각 따로 보느라 ACL이 도메인을 보호하는 번역 경계라는 점을 놓쳐
- 배송사, PG, ERP 같은 외부 시스템의 불안정한 용어와 실패 방식을 내부 정책 언어로 재분류하지 않아
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- software-engineering/api-versioning-contracts-acl
- software-engineering/ddd-hexagonal-consistency
next_docs:
- software-engineering/anti-corruption-drift
- software-engineering/contract-drift-governance
- software-engineering/bff-boundaries
linked_paths:
- contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md
- contents/software-engineering/ddd-hexagonal-consistency.md
- contents/software-engineering/ddd-bounded-context-failure-patterns.md
- contents/software-engineering/anti-corruption-mapping-drift.md
- contents/software-engineering/contract-drift-detection-rollout-governance.md
- contents/software-engineering/bff-boundaries-client-specific-aggregation.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
confusable_with:
- software-engineering/anti-corruption-drift
- software-engineering/api-versioning-contracts-acl
- software-engineering/bff-boundaries
forbidden_neighbors: []
expected_queries:
- Anti-Corruption Layer는 외부 DTO 변환기가 아니라 도메인 오염을 막는 번역 계층이라는 뜻을 설명해줘
- PG 배송사 ERP 같은 외부 API status와 error code를 내부 도메인 결과로 어떻게 재분류해야 해?
- ACL과 adapter facade translator contract test는 어떤 역할로 같이 쓰이는지 알려줘
- 외부 시스템 용어가 내부 도메인 용어와 다를 때 pass-through 통합이 왜 위험해?
- API contract testing과 ACL을 같이 두면 어떤 변경 충격을 흡수할 수 있어?
contextual_chunk_prefix: |
  이 문서는 Anti-Corruption Layer를 외부 시스템 DTO, status, error, schema mismatch가 내부 domain model로 스며들지 않게 막는 translation boundary로 설명하는 advanced deep dive다.
---
# Anti-Corruption Layer Integration Patterns

> 한 줄 요약: ACL은 외부 시스템의 개념이 우리 도메인으로 스며드는 것을 막는 번역 계층이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [DDD, Hexagonal Architecture, Consistency Boundary](./ddd-hexagonal-consistency.md)
> - [DDD Bounded Context Failure Patterns](./ddd-bounded-context-failure-patterns.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Contract Drift Detection and Rollout Governance](./contract-drift-detection-rollout-governance.md)
>
> retrieval-anchor-keywords: anti corruption layer, ACL, translation layer, legacy integration, external DTO leak, domain contamination, contract drift, adapter translator facade, schema mismatch, boundary translation

## 핵심 개념

Anti-Corruption Layer(ACL)는 외부 시스템과 우리 도메인 사이에 두는 **번역/격리 계층**이다.

외부 시스템이 다음과 같은 상태라면 특히 필요하다.

- 용어가 우리 도메인과 다르다
- 응답 형식이 불안정하다
- 실패 방식이 제멋대로다
- 버전 변경이 자주 일어난다

ACL이 없으면 외부 모델이 내부 도메인을 오염시킨다.

## 언제 필요한가

다음 상황이면 ACL이 강하게 필요하다.

- 레거시 ERP/PG/배송사 API를 붙인다
- 마이크로서비스 간 계약이 자주 변한다
- 외부 데이터 품질이 낮다
- 외부 용어가 내부 용어와 충돌한다

즉, 외부가 안정적이지 않거나, 내부 도메인을 보호해야 할 때다.

## 깊이 들어가기

### 1. ACL의 역할

ACL은 단순 DTO 변환이 아니다.

- 외부 응답을 내부 모델로 번역
- 외부 실패를 내부 예외로 변환
- 외부 타입을 내부 타입으로 격리
- 계약 변경 충격을 흡수

### 2. 나쁜 ACL

나쁜 ACL은 그냥 pass-through다.

```java
// 나쁜 예: 외부 DTO를 내부에 그대로 흘려보냄
public OrderResponse callExternal(ExternalOrderDto dto) {
    return externalClient.send(dto);
}
```

이 구조는 번역이 아니라 노출이다.

### 3. 좋은 ACL

좋은 ACL은 외부 용어를 내부 용어로 바꾼다.

```java
public class ShippingGateway {
    public ShippingResult requestShipment(Order order) {
        ExternalShipmentRequest request = mapper.toExternal(order);
        ExternalShipmentResponse response = client.ship(request);
        return mapper.toInternal(response);
    }
}
```

### 4. 통합 패턴

자주 쓰는 패턴은 아래와 같다.

- Adapter: 형식 변환
- Facade: 복잡한 외부 API 단순화
- Translator: 용어/의미 번역
- Retry + Circuit Breaker: 외부 장애 완충
- Contract Test: 계약 유지 확인

ACL은 이 패턴들을 조합하는 경계다.

## 실전 시나리오

### 시나리오 1: 배송사 API

배송사는 `DELIVERED`, `IN_TRANSIT`, `ARRIVED_AT_HUB` 같은 상태를 준다.
우리 도메인은 `READY`, `SHIPPED`, `DELIVERED`만 원한다.

ACL이 없으면 내부 상태가 외부 상태에 맞춰 흔들린다.

### 시나리오 2: PG 결제 응답

결제사는 승인/대기/거절/재시도 가능/재시도 불가를 제각각 준다.
내부에서는 `Approved`, `Rejected`, `Pending`처럼 정리해야 한다.

### 시나리오 3: 레거시 ERP

레거시 ERP는 필드가 많고 의미가 불분명하다.
그 값을 그대로 도메인에 넣으면 모델이 무너진다.

## 코드로 보기

```java
public class PaymentAcl {
    private final PaymentClient client;

    public PaymentResult pay(Checkout checkout) {
        ExternalPaymentRequest request = new ExternalPaymentRequest(
            checkout.orderId(),
            checkout.amount()
        );

        ExternalPaymentResponse response = client.pay(request);

        return switch (response.status()) {
            case "APPROVED" -> PaymentResult.approved(response.transactionId());
            case "PENDING" -> PaymentResult.pending();
            default -> PaymentResult.rejected(response.reason());
        };
    }
}
```

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 직접 통합 | 단순, 빠름 | 내부 오염 위험 | 외부가 매우 안정적일 때 |
| ACL | 내부 보호, 변경 흡수 | 번역 비용 발생 | 외부가 불안정할 때 |
| 계약 테스트 + ACL | 충격 흡수와 검증 동시 확보 | 관리 포인트 증가 | 팀이 성숙했을 때 |

## 꼬리질문

- ACL과 Adapter의 차이를 어디서 끊을 것인가?
- 외부 API가 자주 바뀌면 ACL만으로 충분한가?
- 계약 테스트 없이 ACL을 유지할 수 있는가?
- 번역 로직이 많아져도 여전히 ACL이라고 부를 수 있는가?

## 한 줄 정리

ACL은 외부 시스템을 믿지 못해서가 아니라, 내부 도메인을 외부 변화로부터 보호하기 위해 두는 경계다.
