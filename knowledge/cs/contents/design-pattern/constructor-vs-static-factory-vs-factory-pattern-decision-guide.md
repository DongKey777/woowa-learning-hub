---
schema_version: 3
title: 생성자 vs 정적 팩토리 메서드 vs Factory 패턴 결정 가이드
concept_id: design-pattern/constructor-vs-static-factory-vs-factory-pattern-decision-guide
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - object-creation-boundary
  - static-factory-naming
  - factory-pattern-overuse
aliases:
  - 생성자 정적 팩토리 팩토리 패턴 비교
  - new vs of vs factory chooser
  - 생성자냐 static factory냐 factory pattern이냐
  - 이름 있는 생성과 구현 선택 구분
  - java object creation chooser
  - constructor static factory factory pattern
  - create of from 차이
  - 값 객체 생성과 구현 선택 분리
  - 정적 팩토리 메서드 네이밍 기준
  - factory pattern overuse
symptoms:
  - new로 만들면 되는지 of 같은 정적 팩토리로 올려야 하는지 헷갈려
  - 정적 팩토리 메서드와 Factory 패턴을 둘 다 factory라고 불러서 같은 걸로 느껴져
  - 값 객체 생성 규칙과 구현체 선택 문제를 한 기준으로 설명하고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/factory
  - design-pattern/builder-pattern-basics
next_docs:
  - design-pattern/factory
  - design-pattern/factory-vs-abstract-factory-vs-builder
  - design-pattern/record-vs-builder-request-model-chooser
linked_paths:
  - contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md
  - contents/design-pattern/factory-basics.md
  - contents/design-pattern/factory-vs-abstract-factory-vs-builder.md
  - contents/design-pattern/record-vs-builder-request-model-chooser.md
  - contents/design-pattern/request-object-creation-vs-di-container.md
confusable_with:
  - design-pattern/factory
  - design-pattern/factory-vs-abstract-factory-vs-builder
  - design-pattern/record-vs-builder-request-model-chooser
forbidden_neighbors:
  - contents/design-pattern/request-object-creation-vs-di-container.md
expected_queries:
  - 필드가 몇 개 안 되는 값 객체는 생성자로 두고 언제 정적 팩토리로 올려야 해?
  - of나 from 같은 이름만 붙이면 정적 팩토리고 별도 Factory 클래스를 두면 뭐가 달라져?
  - 구현체 선택이 없는 생성 규칙인데 Factory 패턴이라고 부르면 왜 과한 거야?
  - 값 객체 생성, 캐싱, 구현 선택을 생성자 정적 팩토리 Factory 패턴으로 한 번에 비교해줘
  - new, 정적 팩토리 메서드, Factory 패턴을 무엇을 숨기느냐 기준으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 생성자, 정적 팩토리 메서드, Factory 패턴을 한 번에 헷갈리는
  학습자를 위한 chooser다. 작은 값 객체를 그냥 new로 만들지, 이름 있는
  생성으로 올릴지, 구현체 선택과 생성 책임을 별도 factory로 분리할지
  판단하는 문맥에서 검색된다. 값 객체 생성, 캐싱, of/from 네이밍, 구현
  선택, 외부 provider client 생성 같은 자연어 표현이 이 문서의 기준에
  매핑된다.
---

# 생성자 vs 정적 팩토리 메서드 vs Factory 패턴 결정 가이드

## 한 줄 요약

> 객체를 그냥 직접 만들면 생성자, 같은 타입에 이름 있는 생성 의미를 붙이면 정적 팩토리 메서드, 어떤 구현을 만들지 호출부에서 숨기면 Factory 패턴이다.

## 결정 매트릭스

| 지금 먼저 답해야 할 질문 | 선택 | 왜 그쪽이 맞는가 |
|---|---|---|
| 필드가 적고 호출부에서 값 의미가 바로 읽히는가? | 생성자 | 가장 짧고 직접적이라 과한 구조를 만들지 않는다. |
| 같은 타입을 `zero`, `from`, `parse`처럼 이름으로 구분하고 싶은가? | 정적 팩토리 메서드 | 같은 타입 안에서 생성 의도와 정규화를 드러낼 수 있다. |
| 호출부가 구체 구현이나 생성 규칙을 몰라도 되는가? | Factory 패턴 | 어떤 구현을 만들지 선택하는 책임을 별도 경계로 옮긴다. |
| 새 객체를 항상 만들 필요가 없고 캐싱이나 재사용 가능성이 있는가? | 정적 팩토리 메서드 | 생성자보다 반환 전략을 유연하게 가져갈 수 있다. |
| 환경, provider, 모드에 따라 구현체가 달라지는가? | Factory 패턴 | 생성보다 구현 선택과 조립 정책이 중심 문제다. |

생성자는 "그냥 만든다", 정적 팩토리는 "이름 붙여 만든다", Factory 패턴은 "무엇을 만들지 숨긴다"로 외우면 대부분의 첫 판단이 맞는다.

## 흔한 오선택

값 객체나 작은 요청 모델에 바로 Factory 클래스를 만드는 경우:
구현 선택이 없는데 `UserQueryFactory.create(...)` 같은 이름만 늘어나면 오히려 경계가 흐려진다. 학습자가 "그냥 `new`나 `of`면 되지 않나?"라고 느끼면 과설계 신호다.

정적 팩토리 메서드를 Factory 패턴이라고 부르는 경우:
`Money.of(...)`는 같은 타입 안에 이름 있는 생성 API를 둔 것이다. 별도 협력자가 구현 선택을 맡지 않는다면 보통 Factory 패턴보다는 정적 팩토리 메서드로 부르는 편이 정확하다.

외부 provider 선택 문제를 생성자나 정적 팩토리 안에 다 넣는 경우:
`StorageClient.of(provider)` 안에서 분기가 커지고 의존성이 늘어나면 생성 API보다 구현 선택 경계가 핵심이 된다. 이때는 별도 Factory로 빼야 테스트와 wiring 기준이 선다.

## 다음 학습

- Factory 패턴 자체를 먼저 굳히려면 [팩토리 패턴 기초 (Factory Pattern Basics)](./factory-basics.md)
- 여러 생성 패턴을 제품군 생성까지 넓혀 비교하려면 [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- 작은 요청 모델에서 builder까지 가는 경계를 보려면 [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
- 협력자 생성과 DI 경계까지 섞여 있다면 [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)
