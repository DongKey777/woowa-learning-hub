# Anti-Corruption Adapter Layering: 경계 번역을 여러 층으로 나누기

> 한 줄 요약: Anti-corruption layering은 adapter, facade, port, translator를 분리해 외부 모델이 도메인에 침투하는 걸 막는 설계다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)

---

## 핵심 개념

외부 시스템을 붙일 때 번역 책임이 한 군데에 몰리면, 그 계층은 금방 비대해진다.  
Anti-corruption layering은 이 번역을 여러 층으로 나누어 도메인 순도를 지키는 접근이다.

- port: 경계 계약
- adapter: 기술 연결
- facade: 사용 흐름 정리
- translator: 외부 모델과 내부 모델 변환

### Retrieval Anchors

- `anti corruption layering`
- `adapter layering`
- `model translation`
- `boundary translation stack`
- `legacy system shielding`

---

## 깊이 들어가기

### 1. 한 번에 다 번역하려고 하지 않는다

외부 모델은 보통 도메인 개념과 다르다.

- field name
- error code
- state machine
- pagination semantics

이를 한 어댑터에서 다 처리하면 금방 복잡해진다.

### 2. 층을 나누면 책임이 선명해진다

- inbound adapter: 입력 형식 해석
- translator: 외부 모델 -> 내부 모델
- application facade: 유스케이스 정리
- outbound adapter: 외부 호출

이런 식으로 나누면 문제 지점을 찾기 쉽다.

### 3. 번역층은 도메인 언어를 지켜야 한다

외부 개념이 내부 코드 이름으로 그대로 남으면 경계가 깨진다.

---

## 실전 시나리오

### 시나리오 1: 레거시 결제 연동

레거시 응답을 파싱하는 adapter와 내부 결제 언어로 바꾸는 translator를 분리한다.

### 시나리오 2: 외부 ERP 연동

외부 코드값과 내부 enum을 직접 섞지 않도록 여러 층을 둔다.

### 시나리오 3: API 응답 정규화

외부 API의 이상한 구조를 한 군데에서만 흡수하고 내부는 단순하게 유지한다.

---

## 코드로 보기

### Translation layer

```java
public class LegacyPaymentTranslator {
    public PaymentCommand toCommand(LegacyPaymentResponse response) {
        return new PaymentCommand(response.transactionId(), response.amount());
    }
}
```

### Adapter

```java
public class LegacyPaymentAdapter implements PaymentPort {
    private final LegacyPaymentClient client;
    private final LegacyPaymentTranslator translator;

    @Override
    public PaymentResult pay(PaymentRequest request) {
        LegacyPaymentResponse response = client.pay(request);
        return translator.toResult(response);
    }
}
```

### Facade

```java
public class PaymentFacade {
    public PaymentResult authorizeAndCapture(PaymentRequest request) {
        // 외부 호출 순서를 정리
        return null;
    }
}
```

번역과 호출 순서를 분리하면 유지보수가 쉬워진다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 adapter | 단순하다 | 책임이 비대해진다 | 외부 모델이 단순할 때 |
| Layered anti-corruption | 책임이 분리된다 | 클래스 수가 늘어난다 | 외부 모델이 복잡할 때 |
| 직접 도메인 매핑 | 빠르다 | 외부 개념이 새기 쉽다 | 임시 통합 |

판단 기준은 다음과 같다.

- 외부 모델이 복잡하면 layering
- 외부 모델이 자주 바뀌면 번역층을 독립시킨다
- 외부 용어를 내부로 가져오지 않는다

---

## 꼬리질문

> Q: anti-corruption layer와 adapter는 어떻게 다른가요?
> 의도: 변환과 경계 보호를 구분하는지 확인한다.
> 핵심: adapter는 연결, layering은 경계 보호를 위한 여러 역할 분리다.

> Q: translator를 굳이 따로 두는 이유는 무엇인가요?
> 의도: 번역 책임 분리를 이해하는지 확인한다.
> 핵심: 외부 모델 변경이 도메인으로 바로 번지지 않게 하기 위해서다.

> Q: facade와 layering을 같이 써도 되나요?
> 의도: 패턴 조합을 자연스럽게 보는지 확인한다.
> 핵심: 된다. 보통 같이 쓰면 더 안전하다.

## 한 줄 정리

Anti-corruption adapter layering은 외부 모델을 여러 번역 층으로 흡수해 도메인 오염을 막는 설계다.

