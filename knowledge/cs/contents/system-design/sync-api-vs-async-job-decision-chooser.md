---
schema_version: 3
title: 'Sync API vs Async Job — 지금 응답할 일과 뒤로 넘길 일 결정'
concept_id: system-design/sync-api-vs-async-job-decision-chooser
canonical: false
category: system-design
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- sync-vs-async-boundary
- queue-job-handoff
- user-visible-consistency
aliases:
- sync api vs async job
- 동기 API 비동기 작업 선택
- queue로 넘길 일
- 지금 응답할 일
- background job decision
symptoms:
- API 응답이 느려서 큐로 넘기고 싶은데 어디까지 동기로 처리할지 모르겠다
- 주문 저장, 결제, 알림, 이미지 처리 중 무엇을 같은 요청에서 끝낼지 헷갈린다
- 큐로 넘긴 뒤 사용자가 어떤 상태를 봐야 하는지 정하지 못했다
intents:
- comparison
- design
prerequisites:
- system-design/queue-vs-cache-vs-db-decision-drill
- system-design/message-queue-basics
next_docs:
- system-design/per-key-queue-vs-direct-api-primer
- system-design/job-queue-design
- system-design/consistency-idempotency-async-workflow-foundations
linked_paths:
- contents/system-design/queue-vs-cache-vs-db-decision-drill.md
- contents/system-design/message-queue-basics.md
- contents/system-design/job-queue-design.md
- contents/system-design/per-key-queue-vs-direct-api-primer.md
- contents/system-design/consistency-idempotency-async-workflow-foundations.md
- contents/database/transaction-case-studies.md
- contents/database/idempotency-key-and-deduplication.md
confusable_with:
- system-design/per-key-queue-vs-direct-api-primer
- system-design/job-queue-design
- system-design/message-queue-basics
forbidden_neighbors:
- contents/system-design/caching-basics.md
expected_queries:
- 어떤 작업은 API에서 바로 끝내고 어떤 작업은 queue로 넘겨야 해?
- 주문 저장과 알림 발송을 같은 요청에서 처리해도 되는지 어떻게 판단해?
- 비동기 job으로 넘기면 사용자에게 어떤 상태를 반환해야 해?
- sync API와 async job 선택 기준을 실무 예시로 비교해줘
contextual_chunk_prefix: |
  이 문서는 system-design에서 sync API로 즉시 끝낼 일과 async job/queue로
  넘길 일을 고르는 chooser다. 주문 저장, 결제 승인, 알림 발송, 이미지 처리,
  background job, 사용자에게 보일 pending 상태 같은 질의를 latency, consistency,
  retry, user-visible contract 기준으로 연결한다.
---
# Sync API vs Async Job — 지금 응답할 일과 뒤로 넘길 일 결정

> 한 줄 요약: 사용자에게 즉시 확정해줘야 하는 핵심 상태는 sync API 안에서 끝내고, 오래 걸리거나 재시도 가능한 부가 작업은 async job으로 넘긴다. 대신 비동기화하면 pending 상태와 재시도/중복 방지 계약이 필요하다.

**난이도: 🟡 Intermediate**

## 먼저 나누는 네 가지 질문

| 질문 | Sync API 쪽 | Async job 쪽 |
|---|---|---|
| 사용자가 지금 결과를 알아야 하나 | 주문 생성 성공/실패, 결제 승인 결과 | 이메일, 푸시, 이미지 변환 |
| 실패하면 요청 전체를 실패시켜야 하나 | 재고 차감 실패, 결제 승인 실패 | 알림 발송 실패 |
| 오래 걸려도 사용자 흐름을 막아야 하나 | 본인 인증, 결제 승인 | 리포트 생성, 추천 계산 |
| 재시도해도 안전한가 | idempotency key 필요 | queue dedup / retry key 필요 |

## 예시 1. 주문 생성과 알림 발송

주문 row 생성, 재고 차감, 결제 승인 기록은 사용자가 즉시 알아야 하는 핵심 상태다. 이 부분은 transaction과 idempotency key로 보호한다.

알림 발송은 실패해도 주문 자체를 되돌릴 필요가 없다. outbox나 queue로 넘기고, 발송 실패는 재시도한다.

## 예시 2. 이미지 업로드와 썸네일 생성

원본 업로드 성공 여부는 sync 응답으로 알려준다. 썸네일 생성은 시간이 오래 걸릴 수 있으므로 job으로 넘긴다.

사용자 계약:

```text
201 Created
status=PROCESSING
thumbnailUrl=null
```

이 계약이 없으면 사용자는 성공인지 실패인지 모르는 빈 화면을 보게 된다.

## 비동기로 넘길 때 빠지기 쉬운 조건

- job이 두 번 실행돼도 안전한가
- 상태가 `PENDING`, `PROCESSING`, `FAILED`, `DONE`으로 관찰되는가
- 사용자가 새로고침했을 때 같은 작업을 또 만들지 않는가
- 큐가 밀렸을 때 SLA를 어떻게 보여줄 것인가

## 한 줄 정리

비동기화는 느린 일을 숨기는 기술이 아니라, 핵심 상태와 부가 작업의 완료 계약을 분리하는 설계다.
