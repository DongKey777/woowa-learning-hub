---
schema_version: 3
title: Branch by Abstraction Feature Flag Strangler Fig
concept_id: software-engineering/migration-pattern-chooser
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 90
mission_ids:
- missions/payment
review_feedback_tags:
- migration-patterns
- feature-flag
- strangler-fig
aliases:
- Branch by Abstraction Feature Flag Strangler Fig
- branch by abstraction vs feature flag vs strangler
- migration pattern chooser
- rollout vs refactor vs cutover
- feature flag strangler branch by abstraction
- 점진 전환 패턴 비교
symptoms:
- 코드 내부 구현 교체가 필요한데 feature flag만 붙여 구조 부채를 남기거나, 기능 노출 제어만 필요한데 Strangler 라우팅을 과하게 만들어
- Branch by Abstraction, Feature Flag, Strangler Fig를 모두 점진 전환이라는 말로 뭉쳐 코드 레벨, 운영 레벨, 시스템 레벨을 구분하지 못해
- cutover, rollback, contract test 없이 Strangler 전환을 진행해 새 시스템 검증과 legacy fallback 기준이 흐려져
intents:
- comparison
- design
- troubleshooting
prerequisites:
- software-engineering/feature-flag-dependency-management
- software-engineering/strangler-fig-migration-contract-cutover
next_docs:
- software-engineering/feature-flag-cleanup-expiration
- software-engineering/strangler-verification-shadow-traffic-metrics
- software-engineering/architecture-runway
linked_paths:
- contents/software-engineering/feature-flags-rollout-dependency-management.md
- contents/software-engineering/feature-flag-cleanup-expiration.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md
- contents/software-engineering/technical-debt-refactoring-timing.md
- contents/software-engineering/monolith-to-msa-failure-patterns.md
- contents/software-engineering/strangler-verification-shadow-traffic-metrics.md
confusable_with:
- software-engineering/feature-flag-dependency-management
- software-engineering/strangler-fig-migration-contract-cutover
- software-engineering/deployment-rollout-strategy
forbidden_neighbors: []
expected_queries:
- Branch by Abstraction, Feature Flag, Strangler Fig는 각각 코드 내부, 기능 노출, 시스템 전환 중 무엇을 푸는 패턴이야?
- 결제 PG 교체에서 PaymentPort, feature flag, old/new adapter를 어떤 순서로 조합해?
- 기능을 사용자에게 늦게 켜는 문제와 레거시 트래픽을 새 서비스로 옮기는 문제는 왜 다른 패턴이 필요해?
- feature flag만 남발하면 왜 cleanup debt가 생기고 branch by abstraction만으로는 rollout risk가 남아?
- Strangler Fig migration에서 contract test, shadow compare, rollback path가 필요한 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 Branch by Abstraction, Feature Flag, Strangler Fig를 code refactor boundary, feature exposure control, system cutover migration 관점에서 비교하는 advanced chooser다.
---
# Branch by Abstraction, Feature Flag, Strangler Fig

> 한 줄 요약: 기존 시스템을 안전하게 바꾸려면 "코드 경로를 숨기는 추상화", "기능 노출을 제어하는 플래그", "레거시 트래픽을 흡수하며 잘라내는 전환"을 구분해서 써야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Feature Flag Cleanup, Expiration](./feature-flag-cleanup-expiration.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)

> retrieval-anchor-keywords:
> - branch by abstraction
> - feature flag
> - strangler fig
> - rollout
> - cutover
> - migration
> - refactor
> - rollout strategy
> - dependency injection
> - contract testing

## 핵심 개념

세 가지는 모두 "바꾸되, 한 번에 다 바꾸지 않는다"는 공통점을 가진다. 하지만 해결하려는 문제가 다르다.

- **Branch by Abstraction**은 구현을 감싸는 추상화를 두고 내부 구현을 새것으로 바꾸는 패턴이다.
- **Feature Flag**는 기능을 배포와 분리해서 켜고 끄는 운영 장치다.
- **Strangler Fig**는 레거시의 일부 트래픽과 책임을 새 시스템이 점점 흡수하도록 만드는 전환 패턴이다.

이 차이를 못 나누면 자주 이런 실수를 한다.

- 코드 리팩터링이 필요한데 플래그만 붙여서 구조 부채가 남는다
- 기능 노출 제어가 필요한데 Strangler처럼 과한 라우팅을 만든다
- 시스템 전환이 필요한데 추상화만 만들고 전환 경로를 못 닫는다

즉 이 셋은 비슷해 보여도 담당 레벨이 다르다.

- Branch by Abstraction: **코드 내부**
- Feature Flag: **기능 노출**
- Strangler Fig: **시스템 전환**

---

## 깊이 들어가기

### 1. Branch by Abstraction은 "교체 가능한 틀"을 먼저 만드는 일이다

레거시 구현을 바로 지우지 말고, 먼저 추상화를 둔다.

예를 들면 결제 연동을 바꾸고 싶을 때, 비즈니스 코드는 직접 외부 PG SDK를 호출하지 않는다.

```text
OrderService -> PaymentPort -> OldPgAdapter / NewPgAdapter
```

이렇게 하면 바깥 코드는 그대로 두고 내부 구현만 교체할 수 있다.

핵심은 "새 구현을 만들었다"가 아니라 **바꾸기 쉬운 경계**를 만든다는 점이다.

Branch by Abstraction이 필요한 순간:

- 외부 API 클라이언트를 교체할 때
- DB 접근 로직을 새 저장소로 옮길 때
- 복잡한 if-else를 전략 객체로 바꿔야 할 때
- 새 구현을 점진적으로 검증해야 할 때

### 2. Feature Flag는 "언제 사용자에게 보이게 할지"를 분리하는 장치다

Feature Flag는 코드 교체가 아니라 **활성화 제어**다.

```java
if (featureFlags.isEnabled("new_checkout")) {
    return newCheckoutService.checkout(command);
}
return legacyCheckoutService.checkout(command);
```

이 패턴의 핵심은 배포가 아니라 릴리스 제어다.

- 코드는 먼저 배포한다
- 기능은 나중에 켠다
- 문제가 생기면 바로 끈다

하지만 이건 경계 자체를 바꾸지 않는다. 플래그는 분기만 만들 뿐이고, 구조가 잘못되면 기술 부채가 쌓인다.

### 3. Strangler Fig는 "레거시를 덮어쓰는 전환 경로"다

Strangler Fig는 새 시스템이 레거시 기능을 하나씩 흡수해 가는 방식이다.

```text
Client -> Router -> New Service -> Legacy Service
                      \-> Legacy fallback
```

이 패턴은 단순 리팩터링이 아니라 **시스템 전환**에 가깝다.

필요한 이유:

- 기존 시스템을 한 번에 재작성하면 실패 비용이 너무 크다
- 기능별로 전환 속도를 다르게 가져가야 한다
- 데이터, API, 배치, 운영 도구가 함께 옮겨져야 한다

Strangler Fig의 핵심은 "새 시스템이 살아남는가"보다 **전환 중에도 서비스가 계속 돌아가는가**다.

### 4. 세 패턴은 서로 대체재가 아니라 조합재다

실전에서는 보통 이렇게 같이 쓴다.

1. Branch by Abstraction으로 내부 구현 경계를 만든다
2. Feature Flag로 새 경로를 일부 사용자에게만 열어본다
3. Strangler Fig로 트래픽과 책임을 새 시스템으로 옮긴다

즉 추상화는 코드 레벨, 플래그는 운영 레벨, strangler는 시스템 레벨의 전환 도구다.

### 5. 잘못 쓰면 생기는 실패

- Branch by Abstraction만 하고 플래그 없이 새 구현을 바로 바꾸면 롤아웃 리스크가 크다
- Feature Flag만 남발하면 조건문이 늘고, 플래그가 기술 부채가 된다
- Strangler Fig를 하면서 계약 테스트와 롤백 경로가 없으면 cutover가 도박이 된다

이 문서의 핵심은 "뭘 쓸까"가 아니라 **어디까지 바꾸고, 어디는 남겨 둘 것인가**다.

---

## 실전 시나리오

### 시나리오 1: 결제 PG 교체

외부 결제사를 교체해야 하는데, 주문/정산/취소 로직이 모두 기존 SDK에 묶여 있다.

이때는 다음 순서가 자연스럽다.

1. `PaymentPort`를 먼저 만든다
2. 기존 SDK 호출을 `OldPgAdapter`로 감싼다
3. 새 SDK를 `NewPgAdapter`로 붙인다
4. Feature Flag로 일부 요청만 새 경로로 보낸다
5. 결과가 안정적이면 플래그를 확장하고 old adapter를 삭제한다

이 시나리오는 Branch by Abstraction + Feature Flag 조합이다.

### 시나리오 2: 레거시 주문 조회를 새 서비스로 옮김

주문 조회 API가 느리고, 내부 테이블 구조도 엉켜 있다.

이 경우는 Strangler Fig가 맞다.

- `/orders/{id}` 조회만 새 서비스로 우회한다
- 응답은 shadow compare로 기존과 비교한다
- 계약 테스트로 필드 호환성을 고정한다
- 점진적으로 읽기와 쓰기를 분리한다

여기서 플래그는 일부 사용자만 노출하는 데 보조적으로 쓰인다.

### 시나리오 3: 내부 계산 로직 리팩터링

할인 계산, 세금 계산, 배송비 계산이 한 메서드에 몰려 있다.

이때는 Strangler까지 갈 필요가 없다.

- 계산 전략을 인터페이스로 분리한다
- 새 정책 구현을 Branch by Abstraction으로 교체한다
- Feature Flag는 새 정책 노출이 필요할 때만 쓴다

즉 시스템 전환이 아니라 구조 개선이면 Strangler는 과하다.

### 시나리오 4: 배포는 안전하지만 릴리스가 위험함

새 기능이 이미 배포되어 있지만, 운영 리스크 때문에 아직 사용자에게 열면 안 된다.

이때는 Feature Flag가 정답이다.

- 코드 배포는 진행
- 기능 활성화만 차단
- 모니터링 후 점진 공개

이 상황에서 Strangler를 쓰면 라우팅과 데이터 전환 부담이 불필요하게 커진다.

---

## 코드로 보기

### 1. Branch by Abstraction

```java
public interface PaymentPort {
    PaymentResult pay(PaymentCommand command);
}

public final class LegacyPaymentAdapter implements PaymentPort {
    @Override
    public PaymentResult pay(PaymentCommand command) {
        return legacySdk.charge(command);
    }
}

public final class NewPaymentAdapter implements PaymentPort {
    @Override
    public PaymentResult pay(PaymentCommand command) {
        return newSdk.charge(command);
    }
}
```

비즈니스 코드는 `PaymentPort`만 바라보면 된다.

```java
public class OrderService {
    private final PaymentPort paymentPort;

    public OrderResult placeOrder(OrderCommand command) {
        return paymentPort.pay(command.toPaymentCommand());
    }
}
```

### 2. Feature Flag

```java
public PaymentResult pay(PaymentCommand command) {
    if (featureFlags.isEnabled("new_payment_flow")) {
        return newPaymentAdapter.pay(command);
    }
    return legacyPaymentAdapter.pay(command);
}
```

이 코드는 활성화 여부만 바꾼다.
구조 교체가 아니라 노출 제어다.

### 3. Strangler Fig Router

```java
public HttpResponse route(HttpRequest request) {
    if (request.path().startsWith("/orders") && canaryPolicy.allow(request.user())) {
        return newOrderService.handle(request);
    }
    return legacyOrderService.handle(request);
}
```

전환 초반에는 새 시스템이 일부 트래픽만 받는다.
문제가 생기면 라우터를 되돌리면 된다.

### 4. rollout + shadow compare

```bash
./deploy-new-payment.sh --canary 5
./compare-shadow-traffic.sh --window 30m
./toggle-flag.sh new_payment_flow on
./switch-route.sh --target new --percent 50
```

실전에서는 코드 패턴 하나로 끝나지 않고, 배포/관측/롤백 장치와 같이 써야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| Branch by Abstraction | 내부 구현을 안전하게 교체할 수 있다 | 추상화가 과하면 구조가 무거워진다 | 구현체 교체, 클라이언트 SDK 교체, 내부 리팩터링 |
| Feature Flag | 코드 배포와 릴리스를 분리할 수 있다 | 플래그가 누적되면 복잡도가 폭증한다 | 점진 공개, 실험, 긴급 차단, 기능 온오프 |
| Strangler Fig | 레거시를 안전하게 흡수하며 전환할 수 있다 | 라우팅, 계약, 데이터 전환이 복잡하다 | 모놀리스 전환, 큰 기능 단위 분리, 점진적 cutover |
| Big Bang Rewrite | 경계를 새로 설계할 수 있다 | 실패 비용이 가장 크다 | 매우 작고 단순한 시스템일 때만 |

판단 기준은 간단하다.

- 문제는 구현 교체인가
- 기능 노출 제어인가
- 시스템 전환인가

이 셋을 먼저 구분해야 한다.

---

## 꼬리질문

> Q: Branch by Abstraction과 Feature Flag는 어떻게 다르죠?
> 의도: 코드 구조 변경과 릴리스 제어를 구분하는지 확인
> 핵심: Branch by Abstraction은 구현 경계, Feature Flag는 노출 경계다

> Q: Strangler Fig를 쓸 때 가장 먼저 챙겨야 하는 것은 무엇인가요?
> 의도: 전환 패턴을 배포가 아니라 운영 전환으로 이해하는지 확인
> 핵심: 라우팅 경로, 계약 호환성, 롤백 경로를 먼저 확보해야 한다

> Q: Feature Flag만으로 점진 전환이 충분하지 않나요?
> 의도: 플래그의 한계를 이해하는지 확인
> 핵심: 플래그는 켜고 끄는 장치일 뿐, 데이터 전환과 책임 분리는 해결하지 못한다

> Q: Branch by Abstraction은 언제 과한가요?
> 의도: 과도한 추상화를 경계할 수 있는지 확인
> 핵심: 단순한 기능 토글이나 일회성 변경에까지 추상화를 만들면 오히려 유지비가 커진다

> Q: Strangler Fig와 Canary는 같은 건가요?
> 의도: 시스템 전환과 트래픽 전환을 분리해서 이해하는지 확인
> 핵심: Canary는 배포 전략이고, Strangler Fig는 시스템 전환 전략이다

---

## 한 줄 정리

Branch by Abstraction은 구현 교체, Feature Flag는 기능 노출, Strangler Fig는 시스템 전환을 위한 도구이고, 실전에서는 이 셋을 순서대로 조합해야 안전하게 바꿀 수 있다.
