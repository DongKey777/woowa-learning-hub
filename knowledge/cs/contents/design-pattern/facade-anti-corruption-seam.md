# Facade as Anti-Corruption Seam: 복잡한 외부 세계를 내부로 번지지 않게 막기

> 한 줄 요약: Facade는 단순한 진입점을 제공할 뿐 아니라, 외부 시스템의 개념과 내부 도메인의 경계를 지키는 anti-corruption seam이 될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
> - [Anti-Corruption Layer Operational Pattern](./anti-corruption-layer-operational-pattern.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)
> - [전략 패턴](./strategy-pattern.md)

> retrieval-anchor-keywords: facade anti corruption seam, anti corruption seam, boundary translation, translation quarantine, concept quarantine, legacy concept quarantine, external term quarantine, domain language preservation, legacy integration seam, subsystem orchestration, workflow simplification seam, external model shielding, facade vs adapter, facade vs bridge, interface translation vs concept translation, provider-specific concept quarantine

---

## 핵심 개념

Facade는 복잡한 서브시스템을 하나의 단순한 입구로 묶는 패턴이다.  
backend에서 더 중요한 건, 이 Facade가 단순히 편의 API가 아니라 **외부 개념을 내부 모델로 번역하는 경계**가 될 수 있다는 점이다.

이때 Facade는 anti-corruption seam 역할을 한다.

- 외부 PG 용어를 내부 결제 도메인 언어로 변환
- 레거시 응답 구조를 우리 시스템의 응답 모델로 정리
- 여러 API 호출 순서를 내부 서비스가 알 필요 없게 감춘다

### 질문 분기

- `외부 용어를 내부 도메인 언어로 감춘다`, `legacy concept quarantine`, `boundary translation`, `호출 순서 정리`가 핵심이면 이 문서가 맞다.
- `시그니처 mismatch`, `SDK wrapper`, `XML -> JSON`, `인터페이스를 맞춘다`가 핵심이면 [Adapter (어댑터) 패턴](./adapter.md)으로 간다.
- `S3/GCS/local` 같은 구현 축과 `image/document` 같은 추상화 축을 독립적으로 늘리는 게 핵심이면 [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)로 간다.

---

## 깊이 들어가기

### 1. Facade는 단순화이자 번역기다

Facade는 외부를 숨길 뿐 아니라, 내부 의미를 지키는 데도 쓸 수 있다.

좋은 Seam은 다음을 한다.

- 외부 용어를 내부 용어로 바꾼다
- 예외와 상태를 정리한다
- 복잡한 호출 순서를 하나의 의미 있는 동작으로 묶는다

### 2. Adapter와의 차이

Adapter는 인터페이스가 맞지 않을 때 맞춰주는 데 더 가깝다.  
Facade는 사용자가 알아야 할 복잡도를 줄이는 데 더 가깝다.

하지만 실전에서는 둘이 섞인다.

- 기술 호환은 Adapter
- 개념 정리와 경계 보호는 Facade
- 둘을 함께 쓰면 anti-corruption layer가 된다

Bridge는 또 다른 축이다.

- 변화 축 분리와 구현 조합 폭발 억제는 Bridge
- wire format, 메서드 시그니처 번역은 Adapter
- 외부 개념을 내부 의미로 격리하고 호출 흐름을 정리하는 건 Facade seam

### 3. 경계를 못 지키면 레거시가 번진다

Facade 없이 외부 API를 바로 호출하면 다음 문제가 생긴다.

- 외부 응답 구조가 도메인 곳곳에 새어 나온다
- 에러 처리 규칙이 흩어진다
- 외부 용어가 내부 코드에 남는다

---

## 실전 시나리오

### 시나리오 1: PG 통합

외부 결제 게이트웨이의 승인, 캡처, 취소 흐름을 내부 `PaymentFacade`가 감싸면 도메인 코드가 외부 API의 세부를 몰라도 된다.

### 시나리오 2: 레거시 ERP 연동

ERP의 복잡한 단계 호출을 하나의 업무 명령으로 묶을 수 있다.

### 시나리오 3: 외부 시스템의 예외 정규화

외부 에러코드를 내부 예외 타입으로 바꾸면 정책 처리와 알림이 단순해진다.

---

## 코드로 보기

### Facade

```java
public class PaymentFacade {
    private final PgClient pgClient;
    private final RefundClient refundClient;

    public PaymentResult authorizeAndCapture(PaymentRequest request) {
        PgAuthResponse auth = pgClient.authorize(request);
        return pgClient.capture(auth.transactionId());
    }

    public RefundResult refund(RefundRequest request) {
        return refundClient.refund(request);
    }
}
```

### 내부에서는 도메인 언어를 유지

```java
@Service
public class CheckoutService {
    private final PaymentFacade paymentFacade;

    public void checkout(Order order) {
        PaymentResult result = paymentFacade.authorizeAndCapture(order.paymentRequest());
        order.markPaid(result);
    }
}
```

### Seam의 역할

```java
public class LegacyOrderFacade {
    public InternalOrder toInternal(LegacyOrder legacyOrder) {
        // 외부 용어를 내부 도메인으로 변환
        return new InternalOrder();
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 호출 | 간단하다 | 외부 개념이 퍼진다 | 작은 연동 |
| Adapter | 호환성이 좋아진다 | 의미 정리는 약하다 | 시그니처 차이 해결 |
| Bridge | provider/abstraction 축을 분리한다 | 경계 번역까지 해결하진 않는다 | 구현 축과 추상화 축이 함께 늘 때 |
| Facade as seam | 경계 보호와 단순화가 된다 | 두꺼워질 수 있다 | 외부 시스템이 복잡하고 용어 격리가 필요할 때 |

판단 기준은 다음과 같다.

- 호출 순서만 복잡하면 Facade
- 인터페이스 변환이 핵심이면 Adapter
- provider/abstraction 조합 폭발이 핵심이면 Bridge
- 외부 용어가 내부로 침투하면 seam이 필요하다

---

## 꼬리질문

> Q: Facade와 anti-corruption layer는 같은가요?
> 의도: 경계 보호 개념과 단순화 개념을 연결하는지 확인한다.
> 핵심: 완전히 같진 않지만, Facade가 anti-corruption seam 역할을 할 수 있다.

> Q: 왜 외부 용어가 내부로 퍼지면 안 되나요?
> 의도: 도메인 언어 보존의 중요성을 아는지 확인한다.
> 핵심: 외부 시스템 변경이 내부 모델에 직접 전파되기 때문이다.

> Q: Facade가 너무 커지면 어떻게 하나요?
> 의도: Facade가 또 다른 God Object가 되는 위험을 아는지 확인한다.
> 핵심: 하위 기능별로 분리하고 포트/어댑터로 나눈다.

## 한 줄 정리

Facade는 복잡한 외부 시스템을 단순화할 뿐 아니라, 내부 도메인을 외부 개념으로부터 보호하는 경계가 될 수 있다.
