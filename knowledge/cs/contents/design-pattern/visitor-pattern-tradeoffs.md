# Visitor Pattern Trade-offs: 구조는 남기고 연산을 바꾸기

> 한 줄 요약: Visitor 패턴은 객체 구조는 고정하고 연산을 외부로 분리하지만, 구조가 자주 바뀌는 도메인에서는 오히려 비용이 커진다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

Visitor는 **객체 구조와 수행할 연산을 분리**하는 패턴이다.  
객체 종류가 여러 개이고, 그 객체들에 대해 자주 다른 연산을 추가해야 할 때 유용하다.

하지만 backend 설계에서는 Visitor를 들고 나와야 할 이유와, 들고 나오면 안 되는 이유가 둘 다 분명하다.

- 잘 맞는 경우: AST, 규칙 트리, 정적 구조 순회, 리포트/검사 작업
- 덜 맞는 경우: 엔티티가 자주 바뀌고, 새로운 타입이 계속 추가되는 도메인

### Retrieval Anchors

- `visitor pattern trade-offs`
- `double dispatch`
- `object structure traversal`
- `open closed on operations`
- `entity model evolution`

---

## 깊이 들어가기

### 1. Visitor는 연산 추가에 강하다

객체 구조가 안정적이면 Visitor는 강력하다.

- 컴파일러 AST에 정적 분석 추가
- 승인 규칙 트리를 순회하며 위반 항목 수집
- 문서 노드 구조에 대해 여러 리포트 생성

연산을 객체 바깥으로 빼기 때문에, 구조 클래스가 얇아진다.

### 2. 하지만 타입이 늘면 방문자도 늘어난다

Visitor는 새로운 타입이 추가될 때 모든 visitor를 수정해야 한다.

이게 장점이자 단점이다.

- 연산 추가는 쉽다
- 구조 추가는 비싸다

즉 Visitor는 OCP를 "연산 축"에 대해 최적화한 패턴이다.

### 3. backend 엔티티에는 과할 수 있다

주문, 결제, 회원 같은 엔티티는 타입이 자주 바뀐다.
이런 곳에 Visitor를 얹으면 다음 문제가 생긴다.

- 방문자 수가 급격히 늘어난다
- 비즈니스 규칙이 구조와 연산으로 둘로 찢어진다
- 작은 변경에도 컴파일 범위가 넓어진다

---

## 실전 시나리오

### 시나리오 1: 규칙 트리 검사

정책 노드들을 순회하며 금지 조건, 누락 조건, 중복 조건을 검사할 때 Visitor가 잘 맞는다.

### 시나리오 2: 리포트 생성

같은 도메인 트리로 요약 리포트, 상세 리포트, 감사 리포트를 각각 만들 때 유용하다.

### 시나리오 3: 엔티티가 자주 진화하는 시스템

여기서는 Visitor보다 Specification, Policy Object, 상태 객체가 더 자연스러운 경우가 많다.

---

## 코드로 보기

### Visitor 구조

```java
public interface OrderNode {
    void accept(OrderNodeVisitor visitor);
}

public interface OrderNodeVisitor {
    void visit(LineItemNode node);
    void visit(DiscountNode node);
    void visit(ShippingNode node);
}
```

### 구체 노드

```java
public class LineItemNode implements OrderNode {
    @Override
    public void accept(OrderNodeVisitor visitor) {
        visitor.visit(this);
    }
}
```

### 구체 Visitor

```java
public class ValidationVisitor implements OrderNodeVisitor {
    @Override
    public void visit(LineItemNode node) {
        // 검증
    }

    @Override
    public void visit(DiscountNode node) {
        // 검증
    }

    @Override
    public void visit(ShippingNode node) {
        // 검증
    }
}
```

### 대안

```java
public class OrderPolicy {
    public List<String> validate(Order order) {
        List<String> errors = new ArrayList<>();
        // 명세나 정책 객체로 순회 로직을 단순화할 수 있다
        return errors;
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if/switch | 가장 직접적이다 | 구조가 커지면 지저분하다 | 타입 수가 적을 때 |
| Visitor | 연산 추가가 쉽다 | 구조 변경에 약하다 | 구조 안정성이 높을 때 |
| Specification/Policy | 도메인 규칙에 자연스럽다 | 순회 제어는 직접 해야 한다 | 규칙 중심일 때 |

판단 기준은 다음과 같다.

- 새 연산이 계속 붙는다면 Visitor를 본다
- 새 타입이 계속 붙는다면 Visitor를 의심한다
- 도메인 엔티티라면 Visitor보다 정책 객체를 먼저 본다

---

## 꼬리질문

> Q: Visitor와 Strategy는 어떻게 다르나요?
> 의도: 연산 선택과 구조 순회를 구분하는지 확인한다.
> 핵심: 전략은 행동을 교체하고, Visitor는 구조를 순회하며 연산을 분리한다.

> Q: Visitor가 왜 backend 엔티티에 자주 과한가요?
> 의도: 엔티티 진화 비용을 보는지 확인한다.
> 핵심: 타입 변경이 잦으면 visitor 메서드가 계속 늘어난다.

> Q: Visitor 대신 무엇을 먼저 생각해야 하나요?
> 의도: 패턴 과사용을 경계하는지 확인한다.
> 핵심: Specification, Policy Object, 상태 객체가 더 자연스러운 경우가 많다.

## 한 줄 정리

Visitor 패턴은 구조는 고정하고 연산을 늘릴 때 유용하지만, 타입이 자주 바뀌는 backend 모델에서는 유지비가 빠르게 커진다.

