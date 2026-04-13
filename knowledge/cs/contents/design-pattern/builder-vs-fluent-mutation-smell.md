# Builder vs Fluent Mutation Smell

> 한 줄 요약: Builder는 객체를 안전하게 조립하는 도구지만, fluent setter가 기존 객체를 바꾸기 시작하면 결국 mutable mutation smell이 된다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [빌더 패턴](./builder-pattern.md)
> - [Immutable Builder and Wither Patterns](./immutable-builder-wither-patterns.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Builder는 복잡한 객체를 단계적으로 만드는 패턴이다.  
문제는 "builder처럼 보이지만 실제로는 객체를 계속 수정하는 fluent API"가 등장할 때다.

이때 코드는 빌더가 아니라 **mutating fluent API**가 된다.

- `setX().setY().setZ()`처럼 계속 바뀐다
- 중간 상태가 외부로 노출된다
- build 시점 이전에도 객체 상태가 흔들린다

### Retrieval Anchors

- `builder vs fluent mutation`
- `mutable fluent api`
- `chainable setters`
- `mutation smell`
- `immutable construction`

---

## 깊이 들어가기

### 1. Builder는 조립이고 fluent mutation은 변경이다

Builder의 핵심은 최종 객체를 한 번에 완성하는 것이다.  
반면 fluent mutation은 메서드 체이닝을 이용해 기존 객체를 바꾼다.

둘은 문법이 비슷해 보여도 의미가 다르다.

### 2. 왜 smell이 되는가

fluent setter가 mutable 객체를 다루면 다음 문제가 생긴다.

- 호출 순서 의존성이 생긴다
- 중간 객체 상태가 모호해진다
- 테스트가 깨지기 쉽다
- 체이닝이 읽기 좋다는 착각이 생긴다

### 3. toBuilder와 wither는 괜찮다

기존 객체를 바탕으로 새 객체를 만드는 `toBuilder()`와 `withX()`는 안전한 편이다.  
문제는 기존 객체를 직접 바꾸는 fluent mutation이다.

---

## 실전 시나리오

### 시나리오 1: 요청 DTO 조립

옵션이 많으면 builder가 적합하다.  
하지만 내부 setter 체인이 mutable 객체를 바꾸면 smell이다.

### 시나리오 2: 설정 객체 업데이트

설정 변경이 필요하면 새 객체를 만드는 방식이 더 안전하다.

### 시나리오 3: 테스트 헬퍼

테스트에서만 쓰는 fluent helper가 실제 도메인 API로 퍼지면 경계가 무너진다.

---

## 코드로 보기

### Bad: fluent mutation

```java
public class OrderConfig {
    private String couponCode;

    public OrderConfig couponCode(String couponCode) {
        this.couponCode = couponCode;
        return this;
    }
}
```

### Better: immutable builder

```java
public class OrderConfig {
    private final String couponCode;

    private OrderConfig(Builder builder) {
        this.couponCode = builder.couponCode;
    }
}
```

### Wither 대안

```java
public OrderConfig withCouponCode(String couponCode) {
    return new OrderConfig(couponCode);
}
```

Builder처럼 보이지만 mutable setter면 결국 변경 API다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| mutable fluent API | 호출이 짧다 | 상태가 불안정하다 | 아주 단순한 내부 코드 |
| Builder | 조립 의도가 드러난다 | 클래스가 늘어난다 | 복잡한 생성 |
| Wither | 불변성을 유지한다 | 객체 복사가 발생한다 | 부분 수정 |

판단 기준은 다음과 같다.

- 객체를 "만드는지" "바꾸는지"를 먼저 구분한다
- 체인이 길다고 Builder는 아니다
- 불변 객체면 builder/wither가 더 안전하다

---

## 꼬리질문

> Q: fluent API와 builder는 같은 건가요?
> 의도: 문법만 보고 구조를 오해하지 않는지 확인한다.
> 핵심: 아니다. fluent API는 스타일이고 builder는 의도다.

> Q: mutable fluent API가 왜 위험한가요?
> 의도: 체이닝의 편의와 상태 변경의 위험을 구분하는지 확인한다.
> 핵심: 중간 상태가 계속 바뀌어 예측이 어려워진다.

> Q: toBuilder는 왜 괜찮다고 하나요?
> 의도: 복사 기반 수정과 직접 변경을 구분하는지 확인한다.
> 핵심: 기존 객체를 유지하면서 새 객체를 만든다.

## 한 줄 정리

Builder처럼 보이지만 실제로는 객체를 바꾸는 fluent API는 mutation smell일 가능성이 높다.

