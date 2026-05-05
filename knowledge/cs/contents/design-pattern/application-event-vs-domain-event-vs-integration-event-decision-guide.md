---
schema_version: 3
title: Application Event vs Domain Event vs Integration Event 결정 가이드
concept_id: design-pattern/application-event-vs-domain-event-vs-integration-event-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - spring-event-boundary
  - domain-event-contract-separation
  - outbox-translation-timing
aliases:
  - application event vs domain event vs integration event
  - 스프링 이벤트 도메인 이벤트 통합 이벤트 차이
  - same process 알림과 도메인 사실과 외부 계약 구분
  - 이벤트 클래스 하나로 내부와 외부를 같이 쓰는 문제
  - applicationevent kafka contract boundary
  - 내부 알림 이벤트와 외부 메시지 계약 구분
symptoms:
  - Spring ApplicationEvent를 도메인 이벤트랑 같은 말로 쓰고 있어
  - 도메인 이벤트를 그대로 Kafka에 내보내도 된다고 느껴
  - 내부 알림, 도메인 사실, 외부 계약을 한 이벤트 클래스로 다 처리하고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
  - design-pattern/object-oriented-design-pattern-basics
next_docs:
  - design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
  - design-pattern/domain-events-vs-integration-events
  - design-pattern/domain-event-translation-pipeline
linked_paths:
  - contents/design-pattern/observer-pubsub-application-events.md
  - contents/design-pattern/domain-events-vs-integration-events.md
  - contents/design-pattern/domain-event-translation-pipeline.md
  - contents/design-pattern/outbox-relay-idempotent-publisher.md
  - contents/spring/spring-eventlistener-transaction-phase-outbox.md
confusable_with:
  - design-pattern/observer-pubsub-application-events
  - design-pattern/domain-events-vs-integration-events
  - design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
forbidden_neighbors: []
expected_queries:
  - Spring ApplicationEvent는 도메인 이벤트랑 뭐가 다르고 언제 그냥 내부 알림으로 보면 돼?
  - 주문 완료 같은 사실을 표현하는 클래스와 외부로 발행하는 메시지를 왜 분리해야 해?
  - 같은 이벤트 객체를 listener에도 쓰고 Kafka 발행에도 쓰면 어떤 경계가 무너져?
  - 애플리케이션 이벤트, 도메인 이벤트, 통합 이벤트를 설계 순서 기준으로 비교해줘
  - outbox를 붙일 때 먼저 내부 사실과 외부 계약 중 무엇을 나눠야 하는지 헷갈려
contextual_chunk_prefix: |
  이 문서는 Spring ApplicationEvent, Domain Event, Integration Event를 한
  번에 헷갈리는 학습자를 위한 chooser다. 같은 프로세스 내부 알림인지,
  주문 완료 같은 도메인 사실의 이름인지, Kafka나 외부 시스템에 공개할
  계약 메시지인지 구분하려는 질문, 이벤트 클래스를 하나로 재사용하다 경계가
  무너지는 상황, outbox 번역 시점을 설명해야 하는 문맥에 매핑된다.
---

# Application Event vs Domain Event vs Integration Event 결정 가이드

## 한 줄 요약

> 같은 프로세스 후속 알림이면 Application Event, 도메인 안에서 일어난 사실을 이름 붙이면 Domain Event, 경계 밖에 공개하는 메시지 계약이면 Integration Event다.

## 결정 매트릭스

| 지금 먼저 답해야 할 질문 | 먼저 볼 선택 | 왜 그쪽이 맞는가 |
|---|---|---|
| 같은 트랜잭션 주변에서 listener 여러 개가 반응하는가? | Application Event | same-process fan-out과 실행 타이밍이 핵심이다. |
| `OrderPlaced`처럼 우리 도메인에서 무슨 일이 일어났는지 표현하는가? | Domain Event | 전달 방식보다 내부 의미와 유비쿼터스 언어가 먼저다. |
| 다른 서비스가 오래 소비할 공개 메시지를 정의하는가? | Integration Event | 버전, 호환성, 재시도 같은 외부 계약이 중심이다. |
| DB commit 후 outbox를 거쳐 외부로 내보낼 계획인가? | Domain Event -> Integration Event 순서 | 내부 사실과 외부 계약을 분리해야 진화가 쉬워진다. |
| 한 이벤트 클래스가 listener 호출과 Kafka payload를 모두 맡는가? | 분리 신호로 본다 | same-process 알림 책임과 외부 계약 책임이 섞였다는 뜻이다. |

## 흔한 오선택

`ApplicationEvent`를 곧바로 분산 메시지처럼 이해하는 경우:
Spring `ApplicationEvent`는 기본적으로 같은 프로세스 안 listener fan-out에 가깝다. 학습자가 "왜 발행했는데 소비 재시도가 없지?"라고 말하면 broker 계약이 아니라 내부 이벤트 경계부터 다시 봐야 한다.

도메인 이벤트를 외부 계약이라고 바로 생각하는 경우:
`OrderPlaced` 같은 이름은 내부 도메인 사실을 설명하는 데는 좋지만, 외부 계약은 소비자 안정성까지 책임져야 한다. 필드 추가나 이름 변경이 자주 일어날 수 있다면 Integration Event로 번역층을 두는 편이 안전하다.

한 이벤트 클래스로 내부 알림과 외부 발행을 동시에 처리하는 경우:
처음에는 편해 보여도 commit 타이밍, 재시도 정책, 공개 필드 책임이 한데 묶인다. listener 추가와 메시지 버전 관리가 서로 발목을 잡기 시작하면 세 층을 분리해야 한다.

## 다음 학습

- same-process observer와 broker pub/sub 경계를 먼저 다시 세우려면 [Observer vs Pub/Sub vs Domain Event 결정 가이드](./observer-vs-pubsub-vs-domain-event-decision-guide.md)
- 내부 사실과 외부 계약 메시지의 번역 책임을 더 깊게 보려면 [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
- outbox와 translator로 실제 발행 경계를 설계하려면 [Domain Event Translation Pipeline](./domain-event-translation-pipeline.md)
- Spring commit 타이밍과 outbox 연결이 헷갈리면 [Spring EventListener, TransactionalEventListener, and Outbox](../spring/spring-eventlistener-transaction-phase-outbox.md)
