---
schema_version: 3
title: GoF Adapter vs Ports and Adapters vs Anti-Corruption Layer 결정 가이드
concept_id: design-pattern/gof-adapter-vs-ports-and-adapters-vs-anti-corruption-layer-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - adapter-term-overload
  - boundary-translation-vs-architecture
  - acl-vs-hexagonal-confusion
aliases:
  - gof adapter vs ports and adapters vs acl
  - 어댑터 패턴이랑 헥사고날이랑 acl 차이
  - 번역기 패턴이냐 경계 아키텍처냐 오염 방지층이냐
  - controller adapter랑 sdk adapter를 같은 말로 설명하고 있다
  - port adapter acl을 한 번에 구분하는 표
  - 외부 api 번역과 경계 보호를 어디서 갈라야 하는지
symptoms:
  - controller adapter와 classic adapter를 같은 층위로 설명하고 있어
  - 외부 sdk wrapper를 만들었는데 hexagonal이라고 부르고 있어
  - acl을 그냥 adapter 하나 더 만든 정도로 이해하고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/adapter-basics
  - design-pattern/object-oriented-design-pattern-basics
next_docs:
  - design-pattern/adapter-basics
  - design-pattern/hexagonal-ports-pattern-language
  - design-pattern/anti-corruption-adapter-layering
linked_paths:
  - contents/design-pattern/adapter-basics.md
  - contents/design-pattern/ports-and-adapters-vs-classic-patterns.md
  - contents/design-pattern/hexagonal-ports-pattern-language.md
  - contents/design-pattern/anti-corruption-adapter-layering.md
  - contents/design-pattern/facade-anti-corruption-seam.md
confusable_with:
  - design-pattern/adapter-basics
  - design-pattern/hexagonal-ports-pattern-language
  - design-pattern/anti-corruption-adapter-layering
forbidden_neighbors:
  - contents/design-pattern/adapter.md
  - contents/design-pattern/facade-vs-adapter-vs-proxy.md
expected_queries:
  - 메서드 시그니처를 맞추는 어댑터와 컨트롤러 어댑터는 왜 다른 개념이야?
  - 외부 시스템 연동에서 hexagonal 구조와 anti-corruption layer를 어떤 기준으로 나눠야 해?
  - sdk wrapper 하나 만들었는데 이걸 ports and adapters라고 부르면 과한 거야?
  - adapter, hexagonal, acl이 다 경계 이야기 같은데 먼저 무엇을 결정해야 해?
  - 외부 모델 번역과 의존성 역전과 도메인 오염 방지를 한 표로 비교해줘
contextual_chunk_prefix: |
  이 문서는 GoF Adapter, Ports and Adapters, Anti-Corruption Layer를
  한 번에 헷갈리는 학습자를 위한 chooser다. 메서드 시그니처 번역,
  inbound/outbound port 경계, controller adapter와 SDK adapter의 층위 차이,
  외부 모델을 도메인 언어로 격리하는 ACL, hexagonal과 boundary translation의
  구분 같은 자연어 paraphrase가 이 문서의 결정 기준에 매핑된다.
---

# GoF Adapter vs Ports and Adapters vs Anti-Corruption Layer 결정 가이드

## 한 줄 요약

> 인터페이스 하나를 번역하면 GoF Adapter, 애플리케이션 경계를 세우면 Ports and Adapters, 외부 모델 오염까지 막아야 하면 Anti-Corruption Layer다.

## 결정 매트릭스

| 지금 코드가 답하는 질문 | 먼저 볼 선택지 | 왜 그쪽이 맞는가 |
|---|---|---|
| 메서드 이름, 파라미터, 포맷이 안 맞는 객체 둘을 연결해야 하는가? | GoF Adapter | 클래스 수준 번역 문제라서 작은 변환기로 끝난다. |
| 컨트롤러, 배치, 메시지 컨슈머가 같은 유스케이스 포트를 호출하게 만들고 싶은가? | Ports and Adapters | 도메인과 기술의 의존성 방향을 고정하는 구조 문제다. |
| 외부 PG나 ERP의 상태값, 용어, 예외 의미가 내부 모델로 새어 들어오는가? | Anti-Corruption Layer | 단순 연결보다 도메인 언어 보호와 번역 격리가 핵심이다. |
| 어댑터라는 이름은 같지만 층위가 다른가? | GoF Adapter vs Ports and Adapters 구분 | 하나는 객체 번역, 다른 하나는 아키텍처 경계다. |
| 번역 실패를 quarantine, fallback, contract test까지 다뤄야 하는가? | Anti-Corruption Layer | 운영 가능한 경계 보호가 필요하므로 adapter 하나로는 부족하다. |

`XML -> JSON` 변환이면 GoF Adapter, `controller -> use case -> repository` 경계면 Ports and Adapters, `외부 승인 코드 AUTH_OK를 내부 AUTHORIZED로 고정 번역`하고 drift를 감시해야 하면 ACL 쪽 감각이다.

## 흔한 오선택

`controller adapter`를 보고 GoF Adapter라고만 설명하는 경우:
이때 핵심은 메서드 번역보다 유스케이스 경계와 의존성 방향이다. 학습자가 `inbound`, `outbound`, `port`를 말하면 Ports and Adapters로 먼저 잘라야 한다.

`외부 SDK wrapper` 하나를 만들고 곧바로 hexagonal이라고 부르는 경우:
호출부 한 군데의 시그니처를 맞춘 정도면 GoF Adapter로 충분하다. 구조 전체에서 도메인 중심 포트와 adapter 계층을 세웠는지 따로 확인해야 한다.

`ACL`을 `adapter 여러 개` 정도로 축소하는 경우:
외부 용어 격리, 상태값 번역, contract drift 감지까지 필요하면 이미 번역기 하나의 범위를 넘었다. `도메인 오염을 막아야 한다`는 표현이 나오면 ACL 관점으로 올려야 한다.

## 다음 학습

- 인터페이스 번역 문제를 먼저 단단히 잡으려면 [어댑터 패턴 기초](./adapter-basics.md)
- 경계 구조와 `controller adapter` 문맥을 분리해서 보려면 [Ports and Adapters vs GoF 패턴: 경계에서 책임을 자르는 법](./ports-and-adapters-vs-classic-patterns.md)
- port와 inbound/outbound 경계를 더 깊게 읽으려면 [Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](./hexagonal-ports-pattern-language.md)
- 외부 모델 오염 방지까지 내려가려면 [Anti-Corruption Adapter Layering: 경계 번역을 여러 층으로 나누기](./anti-corruption-adapter-layering.md)
