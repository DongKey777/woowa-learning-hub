---
schema_version: 3
title: lock timeout != already exists 공통 오해 카드
concept_id: database/lock-timeout-not-already-exists-common-confusion-card
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 91
mission_ids: []
review_feedback_tags:
- lock-timeout-not-already-exists
- busy-not-winner
- duplicate-vs-lock-timeout
aliases:
- lock timeout not already exists
- lock timeout busy not winner
- duplicate key already exists vs lock timeout
- beginner lock timeout confusion
- busy vs already exists lock timeout
- lock wait timeout not duplicate
- 락 타임아웃 already exists 오해
- lock timeout 바쁨 신호
- 중복키와 락 타임아웃 차이
- timeout winner not known
symptoms:
- lock wait timeout을 이미 누가 만들었다는 already exists 신호로 오해하고 있어
- duplicate key와 lock timeout을 둘 다 같은 중복 처리로 닫으려 해
- lock timeout 뒤에 blocker 확인, 짧은 retry, fresh read 중 무엇을 해야 할지 헷갈려
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- database/three-bucket-terms-common
- database/deadlock-vs-lock-wait-timeout-primer
next_docs:
- database/busy-fail-fast-vs-one-short-retry-card
- database/lock-duplicate-three-bucket-mini-bridge
- database/insert-if-absent-retry-outcome-guide
linked_paths:
- contents/database/three-bucket-terms-common-card.md
- contents/database/busy-fail-fast-vs-one-short-retry-card.md
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
- contents/database/lock-duplicate-three-bucket-mini-bridge.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/insert-if-absent-retry-outcome-guide.md
confusable_with:
- database/lock-duplicate-three-bucket-mini-bridge
- database/duplicate-key-vs-busy-response-mapping
- database/deadlock-vs-lock-wait-timeout-primer
forbidden_neighbors: []
expected_queries:
- lock timeout은 이미 누가 만들었다는 already exists 신호가 아니라 busy 신호라는 걸 설명해줘
- duplicate key와 lock wait timeout은 서비스 결과 라벨이 어떻게 달라?
- lock timeout 뒤에 winner row가 확정됐다고 단정하면 왜 위험해?
- lock timeout은 blocker 확인과 짧은 retry/fresh read 중 어떤 흐름으로 가야 해?
- lock timeout not already exists를 초보자용 5줄 카드로 정리해줘
contextual_chunk_prefix: |
  이 문서는 lock timeout을 already exists가 아니라 busy, 즉 winner 확정 전 대기 포기 신호로 읽게 하는 beginner chooser다.
  lock timeout not already exists, busy not winner, duplicate key vs lock timeout 같은 자연어 질문이 본 문서에 매핑된다.
---
# `lock timeout` != `already exists` 공통 오해 카드

> 한 줄 요약: `lock timeout`은 "이미 누가 만들었다"가 아니라 "기다리다 이번 시도를 끝냈다"에 더 가깝다.

**난이도: 🟢 Beginner**

관련 문서:

- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md)
- [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: lock timeout not already exists, lock timeout busy not winner, duplicate key already exists vs lock timeout, beginner lock timeout confusion card, busy vs already exists lock timeout, lock wait timeout not duplicate, 락 타임아웃 already exists 오해, lock timeout 바쁨 신호, 중복키와 락 타임아웃 차이, 공통 오해 카드, beginner timeout misunderstanding, lock timeout not already exists common confusion card basics, lock timeout not already exists common confusion card beginner, lock timeout not already exists common confusion card intro, database basics

## 먼저 멘탈모델

초보자는 `lock timeout`을 "이미 자리가 찼다"보다 "줄이 안 빠져서 이번엔 못 들어갔다"로 읽으면 덜 헷갈린다.

## 5줄 카드

1. `lock timeout`은 winner 확정 신호가 아니라 **대기 포기 신호**다.
2. 그래서 기본 버킷은 `already exists`가 아니라 `busy`다.
3. `already exists`는 보통 `duplicate key`처럼 **이미 승자가 확정된 경우**에 붙인다.
4. `lock timeout` 뒤 기본 동작은 기존 결과 재사용보다 **blocker 확인, 짧은 retry, fresh read** 쪽이다.
5. 한 줄 기억법: `duplicate key` = 이미 자리 있음, `lock timeout` = 아직 줄이 안 빠짐.

## 바로 이어서 볼 곳

- `deadlock`과 `lock wait timeout`을 둘 다 락 경합 신호로 비교하고 싶으면 [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md)
- `busy`가 왜 기본은 fail fast이고, 언제 한 번만 짧게 retry할 수 있는지 보려면 [`busy`는 언제 즉시 실패하고, 언제 한 번만 짧게 재시도할까?](./busy-fail-fast-vs-one-short-retry-card.md)
- duplicate 경로와 lock 경로를 한 장 표로 비교하려면 [Lock 예외와 Unique 예외 통합 미니 브리지](./lock-duplicate-three-bucket-mini-bridge.md)
- `insert-if-absent`에서 `busy` / `retryable` / `already exists`를 같이 고정하려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)

## 빠른 확인 질문

- 이 문서의 핵심 용어를 한 문장으로 설명할 수 있는가?
- 실제 미션 코드에서 이 문제가 어디에 나타나는가?

## 한 줄 정리

`lock timeout`은 "이미 누가 만들었다"가 아니라 "기다리다 이번 시도를 끝냈다"에 더 가깝다.
