# Composite Pattern: 쿼리 트리와 규칙 트리를 조립하는 방법

> 한 줄 요약: Composite 패턴은 부분과 전체를 같은 인터페이스로 다뤄, 쿼리 트리와 규칙 트리를 재귀적으로 조합하게 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Specification Pattern](./specification-pattern.md)
> - [Interpreter Pattern: 규칙 언어를 코드로 해석하기](./interpreter-pattern-rules.md)
> - [Visitor Pattern Trade-offs](./visitor-pattern-tradeoffs.md)
> - [CQRS: Command와 Query를 분리하는 패턴 언어](./cqrs-command-query-separation-pattern-language.md)

---

## 핵심 개념

Composite 패턴은 **개별 객체와 객체 집합을 동일한 인터페이스로 다루는 구조 패턴**이다.  
backend에서는 UI 트리보다도 오히려 쿼리 조건, 정책 규칙, 승인 조건 같은 재귀 구조에서 더 자주 보인다.

예를 들면 이런 경우다.

- 검색 조건을 `AND/OR` 트리로 조합할 때
- 정책 룰을 그룹과 리프 노드로 표현할 때
- 필터 조건을 중첩 가능한 DSL로 만들 때

### Retrieval Anchors

- `composite pattern`
- `rule tree`
- `query tree`
- `recursive composition`
- `logical operator tree`

---

## 깊이 들어가기

### 1. 부분과 전체가 같은 계약을 가진다

Composite의 핵심은 leaf와 composite가 같은 인터페이스를 제공한다는 점이다.

- leaf: 더 이상 쪼개지지 않는 조건
- composite: 조건들을 묶는 그룹

이 구조 덕분에 호출부는 "지금 leaf인가 그룹인가"를 모르고도 재귀적으로 처리할 수 있다.

### 2. 쿼리 트리와 규칙 트리에 잘 맞는다

복잡한 검색이나 승인 규칙은 트리 형태가 자연스럽다.

- `AND`
- `OR`
- `NOT`
- 그룹 안의 그룹

Specification과 함께 쓰면 조건 표현이 더 명확해진다.  
Interpreter와 함께 쓰면 작은 규칙 언어가 된다.

### 3. 반대로 엔티티 집합에는 과할 수 있다

Composite는 구조를 통일하지만, 실제로는 조립이 어려워질 수 있다.

- leaf와 composite의 책임이 섞인다
- 지나치게 일반화되면 규칙 의미가 흐려진다
- 재귀 순회가 복잡해질 수 있다

---

## 실전 시나리오

### 시나리오 1: 주문 검색 조건

`status = PAID AND (createdAt >= X OR refunded = false)` 같은 조건을 트리로 표현한다.

### 시나리오 2: 승인 규칙

고위험 거래는 여러 조건 그룹을 만족해야만 승인되는 트리 구조를 가진다.

### 시나리오 3: 카테고리/세그먼트 분류

계층형 분류와 조건 집합을 동시에 다룰 때 유용하다.

---

## 코드로 보기

### Composite 인터페이스

```java
public interface RuleNode {
    boolean evaluate(RuleContext context);
}
```

### Leaf와 그룹

```java
public class EqualsRule implements RuleNode {
    private final String field;
    private final Object expected;

    @Override
    public boolean evaluate(RuleContext context) {
        return expected.equals(context.valueOf(field));
    }
}

public class AndGroup implements RuleNode {
    private final List<RuleNode> children;

    @Override
    public boolean evaluate(RuleContext context) {
        return children.stream().allMatch(child -> child.evaluate(context));
    }
}
```

### 조합

```java
RuleNode rule =
    new AndGroup(List.of(
        new EqualsRule("status", "PAID"),
        new OrGroup(List.of(
            new EqualsRule("refunded", false),
            new GreaterThanRule("amount", 100000)
        ))
    ));
```

Composite는 조건 자체보다 **조립 방식**을 통일한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if/switch | 가장 단순하다 | 중첩이 깊어지기 쉽다 | 조건이 적을 때 |
| Specification | 조합이 쉽다 | 트리 구조 표현은 제한적이다 | 논리 조건 위주 |
| Composite | 구조를 재귀적으로 표현한다 | 너무 일반화되기 쉽다 | 중첩 규칙/트리 |
| Interpreter | 작은 언어를 만든다 | 무겁고 복잡하다 | 규칙 문법이 있을 때 |

판단 기준은 다음과 같다.

- 조건이 재귀적으로 중첩되면 Composite
- 조건 의미가 더 중요하면 Specification
- 규칙 문법이 필요하면 Interpreter

---

## 꼬리질문

> Q: Composite와 Specification의 차이는 무엇인가요?
> 의도: 구조 재귀와 조건 조합을 구분하는지 확인한다.
> 핵심: Composite는 트리 구조를, Specification은 조건 의미를 강조한다.

> Q: Composite가 쿼리 빌더에 왜 유용한가요?
> 의도: 중첩 조건 표현을 이해하는지 확인한다.
> 핵심: AND/OR 그룹을 재귀적으로 다루기 쉽기 때문이다.

> Q: Composite를 엔티티 트리에 그냥 써도 되나요?
> 의도: 구조와 도메인 의미를 섞지 않는지 확인한다.
> 핵심: 구조만 통일하고 의미가 흐려지면 과하다.

## 한 줄 정리

Composite 패턴은 쿼리 트리와 규칙 트리를 재귀적으로 조립하게 해 주지만, 의미가 흐려지면 Specification이나 Interpreter가 더 낫다.

