# Prototype Pattern Caveats: 복제의 편리함이 만드는 함정

> 한 줄 요약: Prototype 패턴은 객체를 복제해 빠르게 새 인스턴스를 만들게 하지만, 얕은 복사와 상태 공유가 쉽게 사고를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [빌더 (Builder)](./builder-pattern.md)
> - [Immutable Builder and Wither Patterns](./immutable-builder-wither-patterns.md)
> - [팩토리 (Factory)](./factory.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Prototype 패턴은 **기존 객체를 복제해 새 객체를 만드는 방식**이다.  
생성 비용이 큰 객체, 동일한 설정을 가진 객체, 템플릿 기반 인스턴스 생성에 유용하다.

하지만 backend에서 prototype은 생각보다 조심해서 써야 한다.

- 얕은 복사와 깊은 복사를 구분해야 한다
- 참조형 필드가 공유될 수 있다
- 복제 후 불변성 보장이 필요하다

### Retrieval Anchors

- `prototype pattern caveats`
- `clone semantics`
- `shallow copy deep copy`
- `copy constructor`
- `object snapshot`

---

## 깊이 들어가기

### 1. 복제가 빠르다고 안전한 건 아니다

Prototype은 초기화 비용을 줄이기 쉽다.
하지만 복제된 객체가 내부 참조를 공유하면 원본이 오염될 수 있다.

이건 특히 다음에서 위험하다.

- 설정 객체
- 컬렉션 필드
- mutable child object

### 2. clone보다 copy constructor가 낫기도 하다

Java의 `clone()`은 이해하기 어렵고, 예외와 깊은 복사 책임이 불명확하다.  
실무에서는 복사 생성자나 정적 팩토리가 더 명시적일 때가 많다.

### 3. 불변 객체와 함께 쓰면 안정적이다

불변 객체는 prototype과 궁합이 좋다.  
복사 후 바뀌지 않는다면 참조 공유의 위험이 훨씬 줄어든다.

---

## 실전 시나리오

### 시나리오 1: 템플릿 기반 주문 생성

기본 배송 설정, 기본 정책, 기본 라우팅 정보를 복제해 새 주문을 만든다.

### 시나리오 2: 테스트 픽스처 복제

비슷한 상태의 테스트 객체를 빠르게 만들 때 유용하다.

### 시나리오 3: 복잡한 설정 사본

외부 API 설정을 바탕으로 약간만 바꾼 인스턴스를 만들 수 있다.

---

## 코드로 보기

### Prototype 스타일

```java
public class PaymentConfig implements Cloneable {
    private String endpoint;
    private List<String> headers;

    @Override
    public PaymentConfig clone() {
        try {
            PaymentConfig copy = (PaymentConfig) super.clone();
            copy.headers = new ArrayList<>(this.headers);
            return copy;
        } catch (CloneNotSupportedException e) {
            throw new IllegalStateException(e);
        }
    }
}
```

### 복사 생성자

```java
public PaymentConfig(PaymentConfig source) {
    this.endpoint = source.endpoint;
    this.headers = new ArrayList<>(source.headers);
}
```

### Wither 대안

```java
public PaymentConfig withEndpoint(String endpoint) {
    return new PaymentConfig(endpoint, List.copyOf(this.headers));
}
```

Prototype보다 명시적인 복제가 더 안전한 경우가 많다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 새로 생성 | 가장 명확하다 | 초기화 비용이 크다 | 생성이 단순할 때 |
| Prototype | 빠르게 복제한다 | 공유 상태 위험이 있다 | 템플릿이 반복될 때 |
| Builder/Wither | 명시적이다 | 코드가 길어진다 | 부분 수정이 잦을 때 |

판단 기준은 다음과 같다.

- 복제 대상이 불변이면 Prototype이 덜 위험하다
- mutable 참조가 있으면 깊은 복사를 반드시 확인한다
- 생성이 복잡하면 Builder가 더 읽기 쉽다

---

## 꼬리질문

> Q: Prototype이 왜 위험하다고 하나요?
> 의도: 복제의 편의와 상태 공유 위험을 아는지 확인한다.
> 핵심: 얕은 복사로 인해 내부 참조가 공유될 수 있다.

> Q: clone보다 copy constructor가 나은가요?
> 의도: 명시성과 유지보수를 고려하는지 확인한다.
> 핵심: 대부분의 backend 코드에서는 더 낫다.

> Q: Prototype은 불변 객체와 어떤 관계인가요?
> 의도: 복제 안정성을 아는지 확인한다.
> 핵심: 불변 객체일수록 복제의 위험이 줄어든다.

## 한 줄 정리

Prototype 패턴은 복제를 쉽게 만들지만, 얕은 복사와 공유 상태 때문에 copy constructor나 Wither가 더 안전할 수 있다.

