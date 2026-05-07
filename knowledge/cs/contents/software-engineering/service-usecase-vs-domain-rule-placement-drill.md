---
schema_version: 3
title: Service Use Case vs Domain Rule Placement Drill
concept_id: software-engineering/service-usecase-vs-domain-rule-placement-drill
canonical: false
category: software-engineering
difficulty: beginner
doc_role: drill
level: beginner
language: mixed
source_priority: 74
mission_ids:
- missions/baseball
- missions/blackjack
- missions/lotto
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- service-domain-boundary
- usecase-orchestration
- domain-rule-placement
- review-drill
aliases:
- service usecase domain rule drill
- 서비스 도메인 규칙 배치 드릴
- service bloat domain rule placement
- 계층 책임 분리 문제
- domain invariant placement drill
symptoms:
- service가 모든 if문과 domain rule을 직접 들고 비대해진다
- domain 객체가 단순 getter/setter 묶음이 되고 규칙이 service에 흩어진다
- use case 순서 조합과 domain invariant를 같은 책임으로 본다
intents:
- drill
- troubleshooting
- design
prerequisites:
- software-engineering/service-layer-basics
- software-engineering/controller-service-domain-responsibility-split-drill
next_docs:
- software-engineering/domain-invariants-as-contracts
- software-engineering/roomescape-reservation-flow-service-layer-bridge
- software-engineering/shopping-cart-checkout-service-layer-bridge
linked_paths:
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/controller-service-domain-responsibility-split-drill.md
- contents/software-engineering/domain-invariants-as-contracts.md
- contents/software-engineering/roomescape-reservation-flow-service-layer-bridge.md
- contents/software-engineering/shopping-cart-checkout-service-layer-bridge.md
- contents/software-engineering/lotto-domain-invariant-bridge.md
confusable_with:
- software-engineering/controller-service-domain-responsibility-split-drill
- software-engineering/service-layer-basics
- software-engineering/domain-invariants-as-contracts
forbidden_neighbors:
- contents/spring/spring-mvc-controller-basics.md
expected_queries:
- service와 domain 중 어디에 규칙을 둬야 하는지 드릴로 풀어줘
- service bloat 리뷰를 미션 예제로 연습하고 싶어
- use case orchestration과 domain invariant를 구분하는 문제를 내줘
- 계층 책임 분리에서 도메인 규칙 배치 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 service use case vs domain rule placement drill이다. service
  bloat, domain anemic model, invariant placement, use case orchestration,
  controller-service-domain responsibility split 같은 리뷰 문장을 짧은
  판별 문제로 매핑한다.
---
# Service Use Case vs Domain Rule Placement Drill

> 한 줄 요약: service는 "유스케이스 순서를 조합"하고, domain은 "항상 지켜야 하는 규칙을 자기 상태와 함께 보호"한다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "서비스에 if문이 많으면 전부 domain으로 옮겨야 하나요?" | roomescape 예약 생성 service가 조회, 검증, 저장, 응답 조립을 모두 들고 있는 코드 | use case 순서와 domain invariant를 먼저 나눈다 |
| "도메인은 getter/setter만 있어도 되나요?" | lotto 번호 중복/범위 규칙이 service static helper에 흩어진 구조 | 객체가 자기 불변식을 지킬 수 있는지 본다 |
| "결제 흐름 순서는 도메인 규칙인가요?" | shopping-cart checkout에서 재고 확인, 주문 저장, 결제 요청, 후속 작업이 이어지는 흐름 | workflow orchestration은 service, 상태 규칙은 domain 후보로 본다 |

**난이도: Beginner**

## 문제 1

상황:

```text
LottoService가 숫자 6개, 중복 없음, 1..45 범위를 모두 if문으로 검사한다.
```

답:

domain rule 후보가 강하다. `Lotto` 값이 만들어진 뒤 항상 지켜야 하는 불변식이면 생성 시점에 domain 객체가 막는 편이 자연스럽다.

## 문제 2

상황:

```text
ReservationService.create()가 member 조회, time 조회, 중복 확인, reservation 저장 순서를 조합한다.
```

답:

service use case 조합에 가깝다. 여러 repository와 domain 객체를 연결하는 흐름은 service가 맡고, 각 객체의 불변식은 domain으로 밀어 넣는다.

## 문제 3

상황:

```text
CartItem.changeQuantity(-1)이 내부에서 음수 수량을 막는다.
```

답:

domain rule에 가깝다. 수량은 어떤 use case에서 바뀌어도 음수가 되면 안 되는 invariant다.

## 빠른 체크

| 질문 | 가까운 위치 |
|---|---|
| 여러 저장소와 외부 port를 순서대로 호출하는가 | service |
| 객체가 어떤 경로로 오든 지켜야 하는가 | domain |
| HTTP status나 request body를 아는가 | controller |
| DB row, SQL, JPA를 아는가 | repository/adapter |
