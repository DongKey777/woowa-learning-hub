# Tolerant Reader for Event Contracts

> 한 줄 요약: Tolerant Reader 패턴은 이벤트 소비자가 계약의 비본질적 변화에 깨지지 않도록 optional field, unknown enum, forward-compatible parsing을 허용하는 소비자 측 호환성 전략이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Event Upcaster Compatibility Patterns](./event-upcaster-compatibility-patterns.md)
> - [Anti-Corruption Contract Test Pattern](./anti-corruption-contract-test-pattern.md)
> - [Event Envelope Pattern](./event-envelope-pattern.md)
> - [Bounded Context Relationship Patterns](./bounded-context-relationship-patterns.md)

---

## 핵심 개념

이벤트 계약 호환성을 말할 때 많은 팀이 producer 쪽 버전 관리만 생각한다.  
하지만 실제 장애는 consumer가 예상보다 엄격해서 터지는 경우가 많다.

- 모르는 필드가 들어오면 역직렬화 실패
- 새 enum 값이 오면 consumer 중단
- 순서만 조금 바뀌어도 파서가 깨짐

Tolerant Reader 패턴은 consumer가 **본질적으로 필요한 의미만 엄격히 보고, 나머지 변화에는 덜 민감하도록** 만드는 전략이다.

### Retrieval Anchors

- `tolerant reader`
- `forward compatible consumer`
- `unknown enum handling`
- `optional field parsing`
- `event consumer compatibility`
- `contract looseness`
- `contract fixture`

---

## 깊이 들어가기

### 1. 엄격한 writer와 엄격한 reader가 만나면 진화가 막힌다

Producer는 계약을 안정적으로 내보내고 싶어 한다.  
Consumer는 입력을 믿고 싶어 한다.

문제는 양쪽이 모두 지나치게 엄격해지면 작은 진화도 배포 순서를 강하게 묶는다는 점이다.

- field 하나 추가
- metadata 확장
- enum 값 확장
- 메시지 순서 변경

Tolerant Reader는 이 결합을 줄이기 위한 consumer 쪽 완충지대다.

### 2. 무엇이 본질 필드인지 먼저 정의해야 한다

모든 걸 느슨하게 읽으라는 뜻은 아니다.

- 필수 비즈니스 식별자
- 반드시 있어야 하는 상태 값
- 없으면 잘못된 처리로 이어지는 금액/수량

이런 본질 필드는 계속 엄격해야 한다.  
대신 부가 필드와 미래 확장 포인트는 느슨하게 읽을 수 있다.

### 3. unknown enum은 실패 전략이 있어야 한다

새 enum이 들어올 때 무조건 exception을 던지면 전체 consumer가 멈출 수 있다.

대안은 다음과 같다.

- `UNKNOWN` 상태로 매핑
- 지원 불가 계약으로 dead-letter
- 본질 처리만 건너뛰고 관측성 기록

중요한 건 "모르면 그냥 크래시" 외의 전략을 미리 정하는 것이다.

### 4. tolerant reader는 upcaster와 역할이 다르다

- tolerant reader: 소비자가 입력을 덜 깨지게 읽는다
- upcaster: 과거/legacy 이벤트를 현재 모델로 끌어올린다

둘은 함께 쓸 수 있다.  
producer 측 진화와 consumer 측 견고함을 동시에 챙겨야 하기 때문이다.

### 5. 지나치게 느슨하면 silent corruption이 생길 수 있다

모르는 필드를 무조건 무시하거나, 없는 값을 자동 기본값으로 채우면 다음 문제가 생긴다.

- 중요한 의미 변화가 숨어 버림
- 잘못된 처리지만 장애는 안 남
- 나중에 데이터 불일치로 드러남

그래서 tolerant reader는 "무조건 관대함"이 아니라 **본질 필드 엄격 + 비본질 필드 관용 + 관측성** 조합에 가깝다.

---

## 실전 시나리오

### 시나리오 1: 새 metadata 필드 추가

producer가 tracing 용 metadata를 추가해도 consumer가 깨질 필요는 없다.  
이런 경우 tolerant reader가 배포 순서 결합을 줄여 준다.

### 시나리오 2: enum 확장

`SHIPPED`, `DELIVERED`만 알던 consumer에게 `PARTIALLY_DELIVERED`가 도착할 수 있다.  
즉시 장애 대신 `UNKNOWN_DELIVERY_STATE`로 수용하고 알람을 남길 수 있다.

### 시나리오 3: 외부 플랫폼 이벤트 소비

우리가 producer를 통제하지 못하는 SaaS 이벤트는 계약 변화가 더 흔하다.  
이때 consumer가 지나치게 엄격하면 운영이 금방 불안정해진다.

---

## 코드로 보기

### tolerant parser 감각

```java
public class PaymentEventReader {
    public PaymentEvent read(JsonNode node) {
        String paymentId = requiredText(node, "paymentId");
        String rawStatus = requiredText(node, "status");

        PaymentStatus status = switch (rawStatus) {
            case "AUTHORIZED" -> PaymentStatus.AUTHORIZED;
            case "CAPTURED" -> PaymentStatus.CAPTURED;
            default -> PaymentStatus.UNKNOWN;
        };

        String optionalChannel = optionalText(node, "channel").orElse("UNKNOWN");
        return new PaymentEvent(paymentId, status, optionalChannel);
    }
}
```

### strict vs tolerant boundary

```java
// paymentId, status는 strict
// channel, metadata는 tolerant
```

### observability

```java
if (status == PaymentStatus.UNKNOWN) {
    metrics.increment("payment_event.unknown_status");
    logger.warn("Unknown payment status: {}", rawStatus);
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 엄격한 consumer | 잘못된 계약을 빨리 드러낸다 | 사소한 진화에도 쉽게 깨진다 | 내부 실험 단계, 강한 동시 배포 |
| Tolerant Reader | 배포 결합을 낮추고 운영 안정성이 높다 | silent corruption을 조심해야 한다 | 오래 사는 이벤트 계약, 외부 producer 소비 |
| 무조건 느슨한 파서 | 장애는 줄어 보인다 | 의미 손실과 잘못된 처리 위험 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- 본질 필드는 엄격하게
- 비본질 필드는 관용적으로
- unknown 수용 시 metrics/log/dead-letter 정책을 함께 둔다

---

## 꼬리질문

> Q: tolerant reader면 schema validation이 필요 없나요?
> 의도: 관용성과 무검증을 혼동하지 않는지 본다.
> 핵심: 아니다. 본질 필드는 계속 엄격하게 검증해야 한다.

> Q: unknown enum을 그냥 무시해도 되나요?
> 의도: silent corruption을 경계하는지 본다.
> 핵심: 보통은 안 된다. UNKNOWN 매핑과 관측성, 혹은 격리 전략이 필요하다.

> Q: upcaster가 있으면 tolerant reader는 필요 없나요?
> 의도: producer-side compatibility와 consumer-side robustness를 구분하는지 본다.
> 핵심: 둘은 다르다. upcaster는 legacy replay, tolerant reader는 live consumer 견고성에 더 가깝다.

## 한 줄 정리

Tolerant Reader는 이벤트 소비자가 비본질적 계약 변화에 덜 깨지도록 만들되, 본질 필드와 unknown 상태에 대한 명시적 정책을 같이 가지게 해주는 패턴이다.
