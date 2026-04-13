# Interpreter Pattern: 규칙 언어를 코드로 해석하기

> 한 줄 요약: Interpreter 패턴은 작은 문법과 해석 규칙을 객체로 표현해, 정책식이나 필터식을 코드 안에서 조합 가능하게 만든다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Specification Pattern](./specification-pattern.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

---

## 핵심 개념

Interpreter 패턴은 **간단한 언어의 문법을 객체로 표현하고, 해석기를 통해 의미를 계산**하는 패턴이다.  
backend에서는 SQL 같은 큰 언어를 직접 만들기보다, 제한된 규칙 언어를 만드는 경우에 의미가 있다.

대표적인 예는 다음과 같다.

- 검색 필터 DSL
- 승인 규칙 표현식
- 정책 조건 트리
- 접근 허용 규칙

### Retrieval Anchors

- `interpreter pattern`
- `rule expression tree`
- `mini language`
- `domain specific language`
- `boolean grammar`

---

## 깊이 들어가기

### 1. Interpreter는 작은 문법에만 맞는다

Interpreter는 문법 규칙이 아주 많아지는 순간 부담이 커진다.

- 문법 객체가 늘어난다
- 파싱과 평가가 분리된다
- 디버깅이 까다로워진다

그래서 실전에서는 "진짜 언어"보다 **작은 규칙식**에 더 적합하다.

### 2. Specification과의 경계

Specification은 "조건을 만족하는가"에 집중한다.  
Interpreter는 "조건식을 어떻게 읽고 계산할 것인가"에 더 가깝다.

| 구분 | Specification | Interpreter |
|---|---|---|
| 초점 | 조건 조합 | 문법 해석 |
| 형태 | predicate 객체 | expression tree |
| 강점 | 재사용과 합성 | 규칙식 표현력 |

### 3. 너무 빨리 만들면 SQL 파서가 된다

작은 규칙식을 넘어 복잡한 문법을 만들기 시작하면, 이미 다른 문제가 된다.

- 파서 버전 관리
- 보안
- 에러 메시지
- 최적화

이쯤 되면 외부 DSL이나 규칙 엔진을 검토하는 편이 낫다.

---

## 실전 시나리오

### 시나리오 1: 할인 규칙

`VIP AND NOT(CANCELLED) AND (WEEKEND OR CAMPAIGN)` 같은 식을 해석할 때 유용하다.

### 시나리오 2: 승인 정책 DSL

운영자가 "금액 10만원 이상이고, 등급이 GOLD 이상이면 관리자 승인 필요" 같은 규칙을 관리할 때 쓸 수 있다.

### 시나리오 3: 필터 조건 생성

화면에서 만든 조건식을 서버가 해석해 안전하게 평가할 때 사용할 수 있다.

---

## 코드로 보기

### 표현식 인터페이스

```java
public interface RuleExpression {
    boolean interpret(RuleContext context);
}
```

### 리터럴과 연산자

```java
public class VipExpression implements RuleExpression {
    @Override
    public boolean interpret(RuleContext context) {
        return context.grade() == MemberGrade.VIP;
    }
}

public class AndExpression implements RuleExpression {
    private final RuleExpression left;
    private final RuleExpression right;

    public AndExpression(RuleExpression left, RuleExpression right) {
        this.left = left;
        this.right = right;
    }

    @Override
    public boolean interpret(RuleContext context) {
        return left.interpret(context) && right.interpret(context);
    }
}
```

### 조합

```java
RuleExpression expression =
    new AndExpression(
        new VipExpression(),
        new NotExpression(new CancelledExpression())
    );
```

### 대안

```java
Specification<RuleContext> rule =
    context -> context.grade() == MemberGrade.VIP && !context.cancelled();
```

간단한 규칙이면 Specification이 더 낫다. 문법이 의미를 가지는 순간 Interpreter를 본다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if/switch | 빠르고 직관적이다 | 규칙이 늘면 난잡하다 | 단순 조건 |
| Specification | 조합이 쉽다 | 문법 표현력은 제한적이다 | 조건 만족 여부 |
| Interpreter | 규칙 언어를 표현한다 | 문법이 커지면 무겁다 | 작은 DSL |

판단 기준은 다음과 같다.

- 규칙 자체를 사용자나 운영자가 읽는다면 Interpreter를 검토한다
- 조건 조합이면 Specification이 더 단순하다
- 언어를 설계할 자신이 없으면 Interpreter를 만들지 않는다

---

## 꼬리질문

> Q: Interpreter와 Specification의 차이는 무엇인가요?
> 의도: 조건 조합과 문법 해석을 분리하는지 확인한다.
> 핵심: Interpreter는 문법을 해석하고, Specification은 조건을 조합한다.

> Q: 왜 Interpreter는 작은 규칙에만 맞나요?
> 의도: 문법 폭발과 유지보수 비용을 아는지 확인한다.
> 핵심: 문법 객체와 해석기 수가 급격히 늘기 때문이다.

> Q: DSL이 이미 있는데도 Interpreter가 필요한가요?
> 의도: 직접 구현과 외부 도구의 선택 기준을 아는지 확인한다.
> 핵심: 아주 제한된 도메인 언어를 코드 안에서 다뤄야 할 때만 고려한다.

## 한 줄 정리

Interpreter 패턴은 작은 규칙 언어를 객체로 해석하는 방법이지만, 문법이 커지면 빠르게 비용이 커진다.

