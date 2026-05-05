---
schema_version: 3
title: Observer vs Pub/Sub vs Domain Event 결정 가이드
concept_id: design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - event-boundary-confusion
  - application-event-vs-broker
  - domain-event-transport-mixup
aliases:
  - observer pubsub domain event chooser
  - 옵저버 pubsub 도메인 이벤트 차이
  - application event kafka domain event 구분
  - 같은 이벤트라는 말이 섞일 때 빠른 판단
  - 브로커 전파와 도메인 사실 표현 구분
  - listener 알림과 메시지 계약 차이
symptoms:
  - Spring 이벤트랑 Kafka 이벤트랑 domain event를 같은 개념으로 설명하고 있어
  - 주문 완료 이벤트를 말하는데 패턴인지 메시지 계약인지 대화가 계속 섞여
  - listener 알림 문제를 outbox나 broker 문제처럼 풀려고 해
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/observer-basics
  - software-engineering/layered-architecture-basics
next_docs:
  - design-pattern/observer-pubsub-application-events
  - design-pattern/domain-events-vs-integration-events
  - design-pattern/outbox-relay-idempotent-publisher
linked_paths:
  - contents/design-pattern/observer-pubsub-application-events.md
  - contents/design-pattern/observer-vs-pubsub-quick-bridge.md
  - contents/design-pattern/domain-events-vs-integration-events.md
  - contents/design-pattern/outbox-relay-idempotent-publisher.md
  - contents/spring/spring-eventlistener-transaction-phase-outbox.md
confusable_with:
  - design-pattern/observer-pubsub-application-events
  - design-pattern/observer-vs-pubsub-quick-bridge
  - design-pattern/domain-events-vs-integration-events
forbidden_neighbors: []
expected_queries:
  - Spring ApplicationEvent와 Kafka 이벤트와 도메인 이벤트를 한 표로 어떻게 나눠 봐야 해?
  - 주문 완료를 알리는 코드에서 observer, pubsub, domain event 중 무엇을 먼저 판단해야 해?
  - 이벤트라는 단어가 같아서 헷갈리는데 알림 방식과 메시지 의미를 어떻게 분리해?
  - 같은 프로세스 listener fan-out과 외부 브로커 발행, 도메인 사실 표현을 각각 뭐라고 불러?
  - domain event를 바로 Kafka로 보내면 observer나 pubsub랑 어떤 경계 차이가 남아?
contextual_chunk_prefix: |
  이 문서는 Observer, Pub/Sub, Domain Event를 한 문맥에서 동시에 헷갈리는
  학습자를 위한 chooser다. 같은 프로세스 listener 알림인지, broker/topic을
  통한 메시지 전파인지, 주문 완료 같은 도메인 사실을 어떻게 이름 붙이고 외부
  계약으로 번역할지 구분하려는 질문에서 검색된다.
---

# Observer vs Pub/Sub vs Domain Event 결정 가이드

## 한 줄 요약

> 같은 프로세스 후속 알림이면 Observer, broker나 bus로 전파하면 Pub/Sub, "무슨 일이 일어났는가"를 도메인 언어로 표현하면 Domain Event다.

## 결정 매트릭스

| 지금 먼저 답해야 할 질문 | 먼저 볼 선택 | 왜 그쪽이 맞는가 |
|---|---|---|
| 주문 완료 뒤에 같은 프로세스 리스너 여러 개가 반응하는가? | Observer | 등록된 listener fan-out과 실패 경계가 핵심이다. |
| 발행자와 소비자를 topic, broker, bus로 분리해야 하는가? | Pub/Sub | 전달 토폴로지와 운영 계약이 중심이다. |
| "주문이 완료됐다" 같은 도메인 사실을 이름 붙이는가? | Domain Event | 실행 방식보다 도메인 의미 표현이 먼저다. |
| 발행은 끝났는데 소비는 나중이어도 되는가? | Pub/Sub | publish와 consume를 분리하는 메시징 문제가 된다. |
| 내부 사실을 외부 시스템에 어떤 계약으로 내보낼지 고민하는가? | Domain Event부터 확인 | 먼저 내부 의미를 분리해야 integration event나 outbox 설계로 자연스럽게 이어진다. |

`OrderCompleted`라는 이름 하나만으로는 패턴이 정해지지 않는다. 같은 이름의 사실을 observer로 fan-out할 수도 있고, outbox를 거쳐 pub/sub로 내보낼 수도 있다. 먼저 "이건 실행 구조를 묻는가, 도메인 의미를 묻는가"를 자르는 편이 빠르다.

## 흔한 오선택

`도메인 이벤트면 자동으로 Pub/Sub다`라고 보는 경우:
Domain Event는 먼저 내부 도메인 사실의 이름이다. 브로커 발행은 그 사실을 외부 계약으로 번역해 내보내는 다음 단계일 수 있고, 같은 프로세스 observer로만 소비할 수도 있다.

`Spring ApplicationEvent`를 Kafka 같은 것으로 이해하는 경우:
publisher가 listener 구현을 몰라도 기본 해석은 same-process observer에 더 가깝다. 학습자가 "발행은 됐는데 왜 재시도가 없지?"라고 말하면 pub/sub가 아니라 observer 경계부터 다시 봐야 한다.

`listener fan-out 문제를 domain event naming 문제로 푸는 경우`:
핵심이 순서, 예외 전파, 동기 실행이면 먼저 observer 문제다. 이름을 `OrderCompletedEvent`로 바꿔도 fan-out의 실행 의미는 그대로 남는다.

## 다음 학습

- Spring 내부 이벤트와 broker 메시징 경계를 더 또렷하게 보려면 [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
- observer와 pub/sub를 가장 짧게 먼저 가르려면 [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](./observer-vs-pubsub-quick-bridge.md)
- domain event와 외부 계약 메시지를 나누려면 [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
- 외부 발행 안정성까지 이어서 보려면 [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
