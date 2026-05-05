---
schema_version: 3
title: Registry vs Strategy Map vs Policy Object 결정 가이드
concept_id: design-pattern/registry-vs-strategy-map-vs-policy-object-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - map-naming-boundary
  - strategy-map-policy-upgrade
  - lookup-vs-decision-separation
aliases:
  - registry vs strategy map vs policy object
  - registry strategy map policy object chooser
  - map lookup 실행 선택 규칙 판정 차이
  - handler map과 refund policy 구분
  - map 기반 분기 이름 결정 가이드
  - strategy map 커질 때 policy object 신호
  - key lookup인지 정책 판정인지 구분
symptoms:
  - Map<Key, Handler>가 있는데 registry인지 strategy map인지 이름을 못 정하겠어
  - 할인 규칙 map이 커지는데 policy object로 올려야 하는지 모르겠어
  - key lookup과 도메인 판정을 같은 선택 문제로 보고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/registry-vs-factory-injected-handler-maps
  - design-pattern/policy-object-vs-strategy-map-beginner-bridge
next_docs:
  - design-pattern/registry-vs-factory-injected-handler-maps
  - design-pattern/policy-object-vs-strategy-map-beginner-bridge
  - design-pattern/strategy-state-policy-object-decision-guide
linked_paths:
  - contents/design-pattern/registry-vs-factory-injected-handler-maps.md
  - contents/design-pattern/policy-object-vs-strategy-map-beginner-bridge.md
  - contents/design-pattern/strategy-state-policy-object-decision-guide.md
  - contents/design-pattern/map-backed-selector-resolver-registry-factory-naming-checklist.md
  - contents/design-pattern/strategy-vs-function-chooser.md
confusable_with:
  - design-pattern/registry-vs-factory-injected-handler-maps
  - design-pattern/policy-object-vs-strategy-map-beginner-bridge
  - design-pattern/strategy-state-policy-object-decision-guide
forbidden_neighbors: []
expected_queries:
  - 핸들러를 map에서 꺼내는 코드와 할인 규칙을 판단하는 코드를 같은 패턴으로 봐도 돼?
  - registry, strategy map, policy object를 key 기준 코드에서 어떻게 갈라야 해?
  - 구현 선택 map이 언제 정책 객체로 승격돼야 하는지 표로 설명해줘
  - get으로 꺼내는 구조와 allowed를 판단하는 구조가 왜 다른지 감이 안 와
  - map 기반 분기에서 lookup, 실행 선택, 규칙 판정을 한 번에 구분하고 싶어
contextual_chunk_prefix: |
  이 문서는 Map<Key, ...> 형태의 코드를 보고 registry lookup, strategy map
  selection, policy object decision을 빠르게 가르게 돕는 chooser다. handler
  map 이름, discount/refund 규칙 객체 승격, key lookup인지 실행 방식 선택인지,
  허용 여부와 이유까지 내려야 하는지 같은 자연어 질문이 본 문서의 판단 기준에
  매핑된다.
---

# Registry vs Strategy Map vs Policy Object 결정 가이드

## 한 줄 요약

> 이미 등록된 대상을 key로 꺼내면 Registry, key로 실행 방식을 골라 바로 실행하면 Strategy Map, 상황을 판정해 허용 여부와 이유까지 내리면 Policy Object다.

## 결정 매트릭스

| 지금 코드가 답하는 질문 | 먼저 볼 선택 | 왜 그쪽이 맞는가 |
|---|---|---|
| `CARD`에 등록된 handler가 무엇인지 꺼내려는가? | Registry | 이미 준비된 후보를 key로 lookup하는 문제가 중심이다. |
| `CARD`면 카드 전략, `POINT`면 포인트 전략처럼 실행 방식을 고르려는가? | Strategy Map | 같은 역할의 구현 중 하나를 선택해 행동을 실행한다. |
| 환불 가능 여부, 거절 이유, 수수료처럼 판정 결과를 내려야 하는가? | Policy Object | 실행보다 도메인 규칙 판단과 설명 가능한 결과가 핵심이다. |
| 새 요구사항이 "새 handler 추가"에 가까운가? | Registry 또는 Strategy Map | 후보 집합을 늘리는 문제라서 lookup이나 선택 구조가 먼저다. |
| 새 요구사항이 "예외 규칙 추가"에 가까운가? | Policy Object | 조건과 사유가 늘어나는 순간 key 선택보다 규칙 모델이 중요해진다. |

`Map`을 쓴다는 사실만으로는 이름이 정해지지 않는다. 호출자가 기대하는 것이 "꺼내 주기"인지, "골라 실행하기"인지, "판정해 설명하기"인지가 먼저다.

## 흔한 오선택

`Map<Key, Handler>`를 전부 Strategy Map이라고 부르는 경우:
호출부가 `registry.get(method)`처럼 이미 있는 대상을 꺼내는 데서 끝나면 Registry가 더 정확하다. 선택 이후 실행은 handler의 책임이고, map 자체는 lookup 선반에 가깝다.

할인/환불 규칙을 Strategy Map으로만 밀어붙이는 경우:
결과가 금액 하나가 아니라 허용 여부, 거절 이유, 다음 액션까지 커지면 Strategy보다 Policy Object가 읽기 쉽다. 학습자가 "왜 안 되는지도 같이 내려야 해"라고 말하면 policy 신호다.

Policy Object가 필요한데 Registry로 감싸서 해결하려는 경우:
registry는 규칙을 저장하거나 찾을 수는 있어도 판정 의미를 대신하지 못한다. `get(tier)` 뒤에 복잡한 `if`가 다시 생기면 lookup 문제가 아니라 규칙 모델링 문제가 남아 있다.

## 다음 학습

- 주입된 handler map이 lookup인지 creation인지 먼저 자르고 싶으면 [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
- strategy map이 언제 규칙 객체로 올라가는지 더 또렷하게 보려면 [Policy Object vs Strategy Map: 커지는 전략 맵을 규칙 객체로 올릴 때](./policy-object-vs-strategy-map-beginner-bridge.md)
- policy object와 state까지 함께 가르고 싶으면 [Strategy vs State vs Policy Object 결정 가이드](./strategy-state-policy-object-decision-guide.md)
- map 기반 클래스 이름을 더 넓게 비교하려면 [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
