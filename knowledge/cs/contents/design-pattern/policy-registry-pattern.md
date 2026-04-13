# Policy Registry Pattern: 정책 객체를 키로 찾아 조합하기

> 한 줄 요약: Policy Registry 패턴은 여러 정책 객체를 키나 조건으로 등록해두고, 런타임에 적절한 정책을 선택하게 만든다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Registry Pattern](./registry-pattern.md)
> - [Policy Object Pattern](./policy-object-pattern.md)
> - [전략 패턴](./strategy-pattern.md)
> - [Specification Pattern](./specification-pattern.md)

---

## 핵심 개념

Policy Registry는 정책 객체를 중앙에 모아두고, 상황에 맞는 정책을 골라 쓰는 패턴 언어다.  
정책이 많은 backend에서 if-else가 커지는 걸 막는 데 유용하다.

- 환불 정책
- 배송 정책
- 승인 정책
- 과금 정책

### Retrieval Anchors

- `policy registry`
- `policy lookup`
- `policy selection`
- `runtime rule selection`
- `strategy registry`

---

## 깊이 들어가기

### 1. policy는 strategy보다 도메인적이다

전략이 "어떻게 할 것인가"라면 정책은 "무엇을 허용할 것인가"에 가깝다.

Policy Registry는 이러한 정책을 키로 모아두고, 도메인 상황에 맞게 고른다.

### 2. registry와 조합될 때 효과가 커진다

정책 개수가 많아질수록 직접 주입보다 registry 조회가 편하다.

- `RefundPolicy`를 등급별로 분리
- `ShippingPolicy`를 지역별로 분리
- `ApprovalPolicy`를 금액대별로 분리

### 3. 과하면 숨은 if-else가 된다

registry는 분기문을 없애는 대신, 선택 규칙을 다른 곳으로 옮길 뿐이다.  
선택 기준이 복잡하면 결국 또 다른 decision engine이 된다.

---

## 실전 시나리오

### 시나리오 1: 회원 등급별 과금

등급에 따라 정책이 달라지는 billing 시스템에 잘 맞는다.

### 시나리오 2: 환불 규칙

결제 수단과 상태에 따라 다른 policy를 골라서 적용한다.

### 시나리오 3: 운영 정책 전환

환경 설정이나 feature flag로 정책을 바꿀 때 유용하다.

---

## 코드로 보기

### Registry

```java
public class PolicyRegistry {
    private final Map<String, PolicyObject> policies = new HashMap<>();

    public void register(String key, PolicyObject policy) {
        policies.put(key, policy);
    }

    public PolicyObject get(String key) {
        return policies.get(key);
    }
}
```

### Policy Object

```java
public interface PolicyObject {
    boolean allowed(Context context);
}
```

### Use

```java
PolicyObject policy = registry.get(order.grade());
if (!policy.allowed(context)) {
    throw new IllegalStateException("not allowed");
}
```

Policy Registry는 정책을 조건별로 선택하는 실전 구조다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if-else | 단순하다 | 정책이 늘면 지저분하다 | 정책이 적을 때 |
| Policy Registry | 런타임 선택이 쉽다 | 선택 기준이 분산될 수 있다 | 정책이 많을 때 |
| Specification | 조건 조합이 쉽다 | 결과 값이 제한적이다 | 허용 여부 중심 |

판단 기준은 다음과 같다.

- 정책 자체가 여러 개면 registry
- 조건만 합치면 specification
- 정책 선택 규칙을 문서화해야 한다

---

## 꼬리질문

> Q: Policy Registry와 Registry Pattern은 어떻게 다른가요?
> 의도: 일반 조회와 정책 선택을 구분하는지 확인한다.
> 핵심: Policy Registry는 registry를 정책 선택에 특화한 구조다.

> Q: policy selection이 너무 복잡해지면 어떻게 하나요?
> 의도: 선택 로직의 폭발을 아는지 확인한다.
> 핵심: Specification이나 decision table로 분리한다.

> Q: 정책 객체와 strategy를 혼동해도 되나요?
> 의도: 도메인 규칙과 알고리즘을 구분하는지 확인한다.
> 핵심: 겹치지만 policy는 허용/판정의 의미가 더 강하다.

## 한 줄 정리

Policy Registry는 여러 정책 객체를 런타임에 찾아 적용하는 구조로, 정책이 많은 도메인에서 if-else를 줄여준다.

