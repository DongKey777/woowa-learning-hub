---
schema_version: 3
title: DSL Object Model Pattern
concept_id: design-pattern/dsl-object-model-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- dsl-object-model
- rule-ast
- expression-tree
- rule-validation
aliases:
- dsl object model
- expression object tree
- rule ast
- domain language model
- parse evaluate serialize
- object model dsl
- rule object tree
- expression tree model
- DSL 객체 모델
- 규칙 AST
symptoms:
- 운영 규칙이나 검색 조건을 문자열로만 저장해 검증, 리팩토링, 에러 위치 표시가 어렵다
- Interpreter, Composite, Visitor가 필요한지 헷갈리지만 실제 요구는 규칙 표현의 저장과 검증이다
- 규칙을 실행하기 전에 schema validation, compatibility, visualization이 필요해졌다
intents:
- deep_dive
- design
- comparison
prerequisites:
- design-pattern/interpreter-pattern-rules
- design-pattern/composite-query-rule-trees
- design-pattern/specification-pattern
next_docs:
- design-pattern/visitor-pattern-tradeoffs
- design-pattern/cqrs-command-query-separation-pattern-language
- design-pattern/event-upcaster-compatibility-patterns
linked_paths:
- contents/design-pattern/interpreter-pattern-rules.md
- contents/design-pattern/composite-query-rule-trees.md
- contents/design-pattern/specification-pattern.md
- contents/design-pattern/visitor-pattern-tradeoffs.md
- contents/design-pattern/cqrs-command-query-separation-pattern-language.md
- contents/design-pattern/event-upcaster-compatibility-patterns.md
confusable_with:
- design-pattern/interpreter-pattern-rules
- design-pattern/composite-query-rule-trees
- design-pattern/specification-pattern
- design-pattern/visitor-pattern-tradeoffs
forbidden_neighbors: []
expected_queries:
- DSL Object Model은 문자열 규칙을 객체 트리로 저장해 검증과 해석을 분리하는 패턴이야?
- Interpreter와 DSL Object Model은 evaluator 중심인지 expression model 중심인지 어떻게 달라?
- 운영자가 만든 승인 규칙을 실행 전에 검증하고 시각화하려면 rule AST를 어떻게 설계해?
- 검색 필터 DSL을 문자열로만 저장하면 리팩토링과 에러 위치 표시가 어려운 이유가 뭐야?
- rule object tree를 저장할 때 parse evaluate serialize와 version compatibility를 어떻게 봐야 해?
contextual_chunk_prefix: |
  이 문서는 DSL Object Model Pattern deep dive로, 문자열 DSL 대신 rule AST/expression object tree를
  남겨 parse, validate, evaluate, serialize, visualize, version compatibility를 다루는 설계 기준과
  Interpreter, Composite, Specification, Visitor와의 차이를 설명한다.
---
# DSL Object Model Pattern: 규칙 언어를 객체 모델로 옮기기

> 한 줄 요약: DSL Object Model은 문자열 규칙을 객체 트리로 바꿔, 해석과 검증과 재사용을 동시에 가능하게 만드는 패턴 언어다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Interpreter Pattern: 규칙 언어를 코드로 해석하기](./interpreter-pattern-rules.md)
> - [Composite Pattern: 쿼리 트리와 규칙 트리를 조립하는 방법](./composite-query-rule-trees.md)
> - [Specification Pattern](./specification-pattern.md)
> - [Visitor Pattern Trade-offs](./visitor-pattern-tradeoffs.md)

---

## 핵심 개념

DSL Object Model은 작은 도메인 언어를 **문자열이 아니라 객체 모델로 표현**하는 접근이다.  
문법을 직접 파싱하든, 코드로 조립하든, 핵심은 표현식을 객체로 남기는 것이다.

이 패턴은 다음과 잘 맞는다.

- 승인 규칙 DSL
- 검색 필터 DSL
- 정책 표현식
- 계산식 트리

### Retrieval Anchors

- `dsl object model`
- `expression object tree`
- `rule ast`
- `domain language model`
- `parse evaluate serialize`

---

## 깊이 들어가기

### 1. 문자열 DSL은 쉽게 무너진다

문자열로만 규칙을 다루면 다음 문제가 생긴다.

- 검증이 어렵다
- 리팩토링이 어렵다
- 문법 오류가 늦게 발견된다

객체 모델은 이 문제를 줄인다.

### 2. Interpreter보다 넓은 개념이다

Interpreter는 해석기를 중심으로 본다.  
DSL Object Model은 그보다 더 넓게, 표현/검증/직렬화를 포함한 구조로 볼 수 있다.

### 3. 검증과 시각화가 쉬워진다

객체 트리로 남기면 다음이 쉬워진다.

- 규칙 검증
- 트리 시각화
- 재사용
- Visitor 기반 분석

### 4. 저장되는 순간 compatibility 문제가 된다

DSL Object Model이 runtime 내부에서만 쓰이면 비교적 단순하다.  
하지만 DB에 저장되거나 운영 UI가 편집하기 시작하면 버전 호환이 핵심이 된다.

- unknown node type을 만났을 때 안전하게 거절하는가?
- deprecated operator를 읽고 새 모델로 변환할 수 있는가?
- evaluator가 지원하지 않는 version을 조용히 실행하지 않는가?

이 지점에서는 단순 객체 트리보다 schema와 migration 전략까지 함께 설계해야 한다.

---

## 실전 시나리오

### 시나리오 1: 승인 규칙 편집기

운영자가 만든 규칙을 객체로 저장하면, 실행 전에 검증할 수 있다.

### 시나리오 2: 검색 조건 빌더

UI에서 만든 조건을 객체 트리로 보관하면 재사용이 쉽다.

### 시나리오 3: 과금식 표현

계산식이 복잡할수록 AST 형태가 유리하다.

---

## 코드로 보기

### Object model

```java
public interface Expression {
    Object evaluate(Context context);
}

public class AndExpression implements Expression {
    private final List<Expression> children;

    @Override
    public Object evaluate(Context context) {
        return children.stream().allMatch(child -> (Boolean) child.evaluate(context));
    }
}
```

### Leaf

```java
public class EqualsExpression implements Expression {
    private final String field;
    private final Object expected;

    @Override
    public Object evaluate(Context context) {
        return expected.equals(context.valueOf(field));
    }
}
```

### Serialization thought

```java
// 객체 트리는 저장, 로딩, 검증, 시각화에 모두 유리하다.
```

DSL Object Model은 단순 표현식보다 도메인 친화적이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 문자열 DSL | 간단하다 | 검증이 어렵다 | 매우 단순한 규칙 |
| DSL Object Model | 구조가 선명하다 | 모델링 비용이 있다 | 규칙이 중요할 때 |
| Interpreter | 해석이 명시적이다 | 문법이 커지면 무겁다 | 작은 언어 |

판단 기준은 다음과 같다.

- 규칙을 저장하고 검증해야 하면 object model
- 단순 계산이면 Specification이나 함수형으로도 충분하다
- 언어가 커지면 파서와 버전 관리가 필요하다

---

## 꼬리질문

> Q: DSL Object Model과 Interpreter의 차이는 무엇인가요?
> 의도: 표현 모델과 해석기를 구분하는지 확인한다.
> 핵심: object model은 구조, interpreter는 계산 방식에 더 가깝다.

> Q: 문자열 DSL 대신 객체 모델을 쓰는 이유는 무엇인가요?
> 의도: 검증과 리팩토링 가능성을 아는지 확인한다.
> 핵심: 타입 안정성과 재사용성이 좋아진다.

> Q: Visitor가 DSL Object Model에 왜 자주 붙나요?
> 의도: 트리 순회 분석을 이해하는지 확인한다.
> 핵심: AST 분석과 변환에 잘 맞기 때문이다.

## 한 줄 정리

DSL Object Model은 규칙 언어를 객체 트리로 만들어 검증, 해석, 시각화를 쉽게 하는 패턴 언어다.
