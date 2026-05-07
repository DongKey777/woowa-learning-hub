---
schema_version: 3
title: Bounded Context Relationship Patterns
concept_id: design-pattern/bounded-context-relationship-patterns
canonical: true
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- bounded-context
- context-map
- anti-corruption-layer
- published-language
aliases:
- bounded context relationship patterns
- context map relationship
- bounded context relationship
- context mapping patterns
- shared kernel
- customer supplier
- conformist relationship
- open host service
- published language
- 바운디드 컨텍스트 관계
- 컨텍스트 맵
symptoms:
- context를 나눈 뒤 API 호출 방향만 보고 협업 관계와 번역 책임을 결정하려 한다
- Shared Kernel, Conformist, Anti-Corruption Layer, Published Language를 코드 공유 방식 정도로만 이해한다
- 외부 시스템이나 상류 팀 모델이 하류 도메인 언어를 오염시키는데 ACL 비용을 판단하지 못한다
intents:
- comparison
- design
- deep_dive
prerequisites:
- design-pattern/anti-corruption-adapter-layering
- design-pattern/domain-events-vs-integration-events
- design-pattern/hexagonal-ports-pattern-language
next_docs:
- design-pattern/anti-corruption-layer-operational-pattern
- design-pattern/anti-corruption-translation-map-pattern
- design-pattern/domain-event-translation-pipeline
- design-pattern/saga-coordinator-pattern-language
linked_paths:
- contents/design-pattern/anti-corruption-adapter-layering.md
- contents/design-pattern/anti-corruption-translation-map-pattern.md
- contents/design-pattern/domain-event-translation-pipeline.md
- contents/design-pattern/facade-anti-corruption-seam.md
- contents/design-pattern/hexagonal-ports-pattern-language.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/saga-coordinator-pattern-language.md
confusable_with:
- design-pattern/anti-corruption-adapter-layering
- design-pattern/domain-events-vs-integration-events
- design-pattern/hexagonal-ports-pattern-language
- design-pattern/facade-anti-corruption-seam
forbidden_neighbors: []
expected_queries:
- Bounded Context 사이 관계를 Shared Kernel, Customer Supplier, Conformist, ACL 중 무엇으로 골라야 해?
- 외부 SaaS 모델을 내부 도메인에 그대로 맞추는 Conformist와 번역층을 두는 ACL은 언제 갈라져?
- Published Language와 Open Host Service는 context 간 계약에서 어떤 역할 차이가 있어?
- Shared Kernel이 단순 공용 라이브러리와 다른 이유와 남용 위험은 뭐야?
- context map을 API 호출 방향이 아니라 협업 권력과 번역 책임으로 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Bounded Context Relationship Patterns chooser로, context map에서 Partnership,
  Shared Kernel, Customer/Supplier, Conformist, Anti-Corruption Layer, Open Host Service,
  Published Language를 협업 권력, 번역 책임, coupling budget 기준으로 선택하는 방법을 설명한다.
---
# Bounded Context Relationship Patterns

> 한 줄 요약: Bounded Context Relationship Patterns는 context 간 협업 방식을 Partnership, Shared Kernel, Customer/Supplier, Conformist, Anti-Corruption Layer, Open Host Service, Published Language로 나눠 coupling budget을 의식적으로 배치하게 해준다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Anti-Corruption Adapter Layering](./anti-corruption-adapter-layering.md)
> - [Anti-Corruption Translation Map Pattern](./anti-corruption-translation-map-pattern.md)
> - [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
> - [Facade as Anti-Corruption Seam](./facade-anti-corruption-seam.md)
> - [Hexagonal / Ports Pattern Language](./hexagonal-ports-pattern-language.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Saga / Coordinator: 분산 워크플로를 설계하는 패턴 언어](./saga-coordinator-pattern-language.md)

---

## 핵심 개념

DDD의 전략 설계에서 중요한 질문은 "context를 어떻게 나눌까"만이 아니다.  
나뉜 뒤에 **서로 어떤 관계로 살게 할까**도 못지않게 중요하다.

Bounded context 관계를 그냥 "API 호출 관계"로만 보면 다음 문제가 생긴다.

- 조직 권력 차이가 코드에 숨는다
- 어떤 팀이 누구의 모델을 따라야 하는지 모호해진다
- 번역 비용을 어디에 둘지 결정하지 못한다

이 패턴들은 기술 패턴이면서 동시에 협업 패턴이다.

### Retrieval Anchors

- `bounded context relationship`
- `shared kernel`
- `customer supplier`
- `conformist`
- `anti corruption layer`
- `open host service`
- `published language`
- `event contract evolution`

---

## 깊이 들어가기

### 1. 관계 패턴은 기술보다 힘의 방향을 먼저 본다

같은 "A가 B를 호출한다"여도 의미는 다를 수 있다.

- 두 팀이 함께 진화시킬 수 있는가
- 한 팀이 사실상 표준을 강제하는가
- 번역 비용을 누가 부담하는가
- 계약 변경을 누가 주도하는가

이 질문에 따라 관계 패턴이 갈린다.

### 2. 주요 관계 패턴

| 패턴 | 의미 | 장점 | 위험 |
|---|---|---|---|
| Partnership | 두 context가 긴밀히 함께 진화 | 협업 속도가 빠르다 | 경계가 흐려질 수 있다 |
| Shared Kernel | 일부 모델/코드를 공동 소유 | 중복을 줄인다 | 작은 공유가 큰 결합이 되기 쉽다 |
| Customer/Supplier | 상류가 하류 요구를 반영 | 계약 품질을 올리기 쉽다 | 우선순위 충돌 가능 |
| Conformist | 하류가 상류 모델을 그대로 따른다 | 빠르게 붙는다 | 하류 도메인이 오염된다 |
| Anti-Corruption Layer | 하류가 번역층으로 방어 | 도메인 순도가 높다 | 번역 비용이 든다 |
| Open Host Service | 상류가 공개 프로토콜 제공 | 재사용성과 일관성이 높다 | 표준 유지 비용이 필요 |
| Published Language | 공용 언어/스키마를 약속 | 다수 소비자와 협업이 쉽다 | 버전 관리가 필요하다 |

### 2-1. 선택 질문으로 줄이면 더 안전하다

패턴 이름을 먼저 고르면 대부분 "우리도 ACL 해야 하나?" 같은 추상 논쟁으로 흐른다. 먼저 아래 질문을 순서대로 둔다.

1. 이 하류 context가 상류 모델과 다른 언어를 지켜야 하는가?
2. 상류 contract 변경을 하류가 협상할 수 있는가?
3. 공유 모델을 함께 릴리스하고 함께 테스트할 조직 비용을 감당할 수 있는가?
4. 소비자가 하나인가, 여러 context가 재사용할 공개 contract가 필요한가?

답이 "하류 언어를 지켜야 하고 상류를 통제하기 어렵다"면 ACL 쪽으로 기운다.  
답이 "여러 소비자가 같은 안정 contract를 원한다"면 Open Host Service + Published Language를 먼저 검토한다.

### 3. Shared Kernel은 가장 쉽게 남용된다

Shared Kernel은 "공통 모듈"을 만들자는 말과 다르다.

- 정말 작은 핵심만 공유해야 한다
- 릴리스/테스트/버전 변경을 함께 책임져야 한다
- 팀 간 신뢰와 동기화 비용을 감당할 수 있어야 한다

편해서 공유한 enum, DTO, util이 시간이 지나며 사실상 거대 결합점이 되는 경우가 많다.

### 4. Conformist와 ACL은 선악 구도가 아니다

많은 자료가 Conformist를 나쁜 패턴처럼 설명하지만, 실무에서는 충분히 합리적일 수 있다.

- 작은 팀이 외부 SaaS를 빠르게 붙여야 한다
- 상류 모델이 사실상 업계 표준이다
- 도메인 차별화보다 속도가 더 중요하다

반대로 ACL은 항상 옳아 보이지만 다음 비용이 있다.

- 번역 코드 유지
- 테스트 데이터 이중화
- 장애 분석 시 경계 추적 비용

즉 도메인 차별화가 큰 곳에 ACL을 쓰고, 차별화가 작은 곳에 Conformist를 택하는 식의 판단이 필요하다.

### 5. Open Host Service와 Published Language는 함께 움직이는 경우가 많다

여러 하류 context가 상류 서비스를 소비한다면 상류 쪽에서 공개 인터페이스와 언어를 정제할 필요가 있다.

- REST/GraphQL/gRPC contract
- 이벤트 스키마
- 에러 코드 규약
- 용어집

이때 Open Host Service는 "제공 방식", Published Language는 "의미 계약"에 더 가깝다.

---

## 실전 시나리오

### 시나리오 1: 사내 결제 플랫폼과 주문 서비스

결제 플랫폼이 여러 도메인에서 재사용된다면 Open Host Service와 Published Language가 잘 맞는다.  
주문 서비스는 필요한 경우 ACL 없이도 이 계약을 직접 소비할 수 있다.

### 시나리오 2: 외부 물류 SaaS 연동

물류 SaaS 상태 코드와 운영 개념이 내부 주문 모델과 다르면 Conformist보다 ACL이 안전하다.  
배송 지연, 부분 출고, 반송 같은 의미를 내부 언어로 재해석해야 하기 때문이다.

### 시나리오 3: 같은 조직 안의 추천 도메인과 상품 도메인

두 팀이 작은 핵심 모델만 매우 자주 같이 바꾼다면 Shared Kernel이 가능하다.  
하지만 공용 모듈이 커지면 차라리 Published Language + 독립 진화가 낫다.

---

## 코드로 보기

### Conformist의 감각

```java
public class ExternalCatalogAdapter {
    public ExternalCatalogProduct load(String productId) {
        return catalogClient.fetch(productId);
    }
}
```

빠르지만 외부 모델이 내부까지 침투하기 쉽다.

### ACL의 감각

```java
public class CatalogTranslator {
    public ProductSnapshot toSnapshot(ExternalCatalogProduct external) {
        return new ProductSnapshot(
            external.id(),
            external.displayName(),
            Availability.from(external.stockState())
        );
    }
}
```

### Published Language의 감각

```java
public record PaymentAuthorizedV1(
    String paymentId,
    String orderId,
    long approvedAmount,
    String approvedAt
) {}
```

공개 언어는 내부 엔티티 구조가 아니라 외부 소비자 관점의 안정성을 가져야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Conformist | 속도가 빠르다 | 하류 도메인 오염 | 차별화가 작고 붙이는 속도가 중요할 때 |
| ACL | 도메인 경계가 선명하다 | 번역 비용과 코드량 증가 | 외부 모델이 내부와 의미가 다를 때 |
| Shared Kernel | 중복을 줄인다 | 강한 결합과 조율 비용 | 아주 작은 핵심을 공동 소유할 때 |
| Open Host Service + Published Language | 다수 소비자 협업에 유리 | 계약 유지/버전 관리 필요 | 플랫폼 팀이 표준 제공자일 때 |

판단 기준은 다음과 같다.

- 관계를 기술 호출이 아니라 협업 구조로 본다
- 번역 비용보다 도메인 오염 비용이 큰 곳에 ACL을 쓴다
- shared kernel은 가장 작은 범위로 제한한다

---

## 꼬리질문

> Q: Shared Kernel과 공용 라이브러리는 같은 건가요?
> 의도: 단순 코드 공유와 전략적 공동 소유를 구분하는지 본다.
> 핵심: 아니다. Shared Kernel은 모델과 변경 책임까지 함께 가진다.

> Q: Conformist는 나쁜 선택인가요?
> 의도: 패턴을 도덕화하지 않는지 본다.
> 핵심: 아니다. 속도와 차별화 수준에 따라 합리적인 선택일 수 있다.

> Q: Open Host Service와 Published Language는 어떻게 다른가요?
> 의도: 제공 방식과 의미 계약을 분리해 이해하는지 본다.
> 핵심: OHS는 공개 인터페이스, PL은 그 인터페이스가 사용하는 공용 언어다.

## 한 줄 정리

Bounded Context Relationship Patterns는 context 간 협업을 기술 연결이 아니라 결합 비용과 번역 책임의 배치 문제로 보게 해준다.
