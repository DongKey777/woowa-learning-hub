# Anti-Corruption Translation Map Pattern: 외부 코드값을 도메인 언어로 매핑하기

> 한 줄 요약: Translation Map은 외부 시스템의 코드와 상태값을 내부 도메인 언어로 고정 매핑해 모델 오염을 막는다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Adapter (어댑터) 패턴](./adapter.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)

---

## 핵심 개념

외부 API는 종종 우리 도메인과 다른 코드값을 쓴다.  
Translation Map은 그 코드들을 내부 언어로 한 번만 번역하는 표를 둔다.

- 외부 status code
- 내부 enum
- 에러 코드
- 공급자별 상태값

### Retrieval Anchors

- `translation map`
- `anti corruption map`
- `external code mapping`
- `status code translation`
- `domain enum mapping`

---

## 깊이 들어가기

### 1. switch문보다 map이 낫다

코드값 번역을 `switch`로만 두면 흩어지기 쉽다.  
고정된 map 또는 dedicated translator로 두면 더 선명하다.

### 2. 외부 상태와 내부 상태를 섞지 않는다

외부 provider의 `PENDING_AUTH`, `AUTH_OK`, `AUTHORIZED`를 내부에서 그대로 쓰면 도메인이 오염된다.

내부에는 `PAYMENT_PENDING`, `AUTHORIZED`, `CAPTURED`처럼 우리 언어를 써야 한다.

### 3. 단방향 번역이 좋다

외부 -> 내부는 명시적으로, 내부 -> 외부는 다른 translator로 분리하는 편이 안전하다.

---

## 실전 시나리오

### 시나리오 1: 결제 상태 매핑

PG 상태값을 내부 결제 상태로 번역한다.

### 시나리오 2: 배송 상태 매핑

물류 업체별 코드값을 내부 상태로 통일한다.

### 시나리오 3: 오류 코드 매핑

외부 에러를 내부 예외 타입으로 바꾼다.

---

## 코드로 보기

### Translation map

```java
public class PaymentStatusTranslator {
    private static final Map<String, PaymentStatus> MAP = Map.of(
        "PENDING_AUTH", PaymentStatus.PENDING,
        "AUTH_OK", PaymentStatus.AUTHORIZED,
        "CAPTURED", PaymentStatus.CAPTURED
    );

    public PaymentStatus translate(String externalCode) {
        return MAP.getOrDefault(externalCode, PaymentStatus.UNKNOWN);
    }
}
```

### Using it in adapter

```java
public class PgPaymentAdapter implements PaymentPort {
    private final PaymentStatusTranslator translator;

    public PaymentResult pay(PaymentRequest request) {
        String externalCode = "AUTH_OK";
        return new PaymentResult(translator.translate(externalCode));
    }
}
```

### Boundary rule

```java
// 외부 코드를 domain enum으로 바로 노출하지 않는다.
```

Translation map은 anti-corruption layer의 가장 작은 단위다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| inline switch | 빠르다 | 분산되기 쉽다 | 잠깐의 대응 |
| Translation Map | 단방향 번역이 쉽다 | 매핑 관리가 필요하다 | 외부 코드값이 고정될 때 |
| full translator layer | 책임 분리가 좋다 | 코드가 늘어난다 | 외부 모델이 복잡할 때 |

판단 기준은 다음과 같다.

- 코드값이 여러 곳에서 반복되면 map으로 모은다
- 도메인 언어를 지키는 게 핵심이다
- 외부 상태를 그대로 노출하지 않는다

---

## 꼬리질문

> Q: translation map과 adapter는 어떻게 다른가요?
> 의도: 작은 번역 표와 객체 수준 연결을 구분하는지 확인한다.
> 핵심: map은 번역 데이터, adapter는 연결 책임이다.

> Q: 왜 외부 코드값을 그대로 쓰면 안 되나요?
> 의도: 도메인 오염의 위험을 아는지 확인한다.
> 핵심: provider 변경이 내부로 바로 전파된다.

> Q: unknown 값을 어떻게 다루나요?
> 의도: 안전한 디폴트와 실패 정책을 아는지 확인한다.
> 핵심: UNKNOWN 또는 예외 정책을 명시해야 한다.

## 한 줄 정리

Anti-corruption Translation Map은 외부 코드값을 내부 도메인 언어로 고정 번역해 모델 오염을 막는다.

