---
schema_version: 3
title: Policy Registry Pattern
concept_id: design-pattern/policy-registry-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- policy-registry
- policy-selection
- runtime-rule-selection
aliases:
- policy registry
- policy lookup
- policy selection
- runtime rule selection
- strategy registry
- refund policy registry
- approval policy registry
- policy object registry
- 정책 registry
- 정책 선택
symptoms:
- 환불, 배송, 승인 정책이 늘어나는데 if-else로 직접 분기하며 정책 객체 선택 기준이 흩어진다
- Policy Registry가 단순 key lookup을 넘어 복잡한 decision engine처럼 커지는데 Specification이나 decision table로 분리하지 않는다
- policy와 strategy를 모두 같은 registry에 넣어 허용/판정 규칙과 실행 알고리즘 선택 의미가 섞인다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- design-pattern/registry-pattern
- design-pattern/policy-object-pattern
- design-pattern/specification-pattern
next_docs:
- design-pattern/specification-combinator-libraries
- design-pattern/domain-service-vs-pattern-abuse
- design-pattern/factory-misnaming-checklist
linked_paths:
- contents/design-pattern/registry-pattern.md
- contents/design-pattern/policy-object-pattern.md
- contents/design-pattern/strategy-pattern.md
- contents/design-pattern/specification-pattern.md
- contents/design-pattern/specification-combinator-libraries.md
confusable_with:
- design-pattern/registry-pattern
- design-pattern/strategy-pattern
- design-pattern/specification-pattern
- design-pattern/policy-object-pattern
forbidden_neighbors: []
expected_queries:
- Policy Registry는 여러 Policy Object를 key나 context로 찾아 적용하는 구조야?
- RefundPolicy, ShippingPolicy, ApprovalPolicy가 많아질 때 Policy Registry로 if else를 줄이는 기준은 뭐야?
- policy는 허용 여부나 판정 의미가 강하고 strategy는 실행 방법 의미가 강하다는 차이가 뭐야?
- policy selection이 복잡해지면 Registry 안에 숨은 if else 대신 Specification이나 decision table로 분리해야 하는 이유가 뭐야?
- Policy Registry와 일반 Registry Pattern은 lookup 구조는 같지만 도메인 정책 선택에 특화된다는 점이 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 Policy Registry Pattern playbook으로, 환불/배송/승인/과금 같은 Policy Object를
  key나 context로 등록해 런타임에 찾아 적용하고, policy selection이 복잡해질 때 Specification,
  decision table, Policy Object 경계로 나누는 기준을 설명한다.
---
# Policy Registry Pattern: 정책 객체를 키로 찾아 조합하기

> 한 줄 요약: Policy Registry 패턴은 여러 정책 객체를 키나 조건으로 등록해두고, 런타임에 적절한 정책을 선택하게 만든다.

**난이도: 🔴 Advanced**

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
