---
schema_version: 3
title: 페이지네이션 중복/누락 원인 라우터
concept_id: database/pagination-duplicates-missing-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
- missions/roomescape
review_feedback_tags:
- unstable-order-by
- offset-vs-seek-choice
- replica-list-freshness
aliases:
- pagination duplicates missing
- cursor page drift
- 페이지 넘기면 같은 row가 또 나옴
- 다음 페이지에서 일부 row가 사라짐
- offset pagination drift
- 페이지네이션 중복 누락
symptoms:
- 1페이지에서 본 row가 2페이지에 또 나온다
- 스크롤을 내리면 어떤 row는 건너뛰고 어떤 row는 중복해서 보인다
- 새 글이 들어오면 다음 페이지 결과가 밀리거나 빠진다
- 같은 조건인데 새로고침할 때마다 페이지 구성원이 조금씩 달라진다
intents:
- symptom
- troubleshooting
prerequisites:
- database/sql-relational-modeling-basics
- database/database-first-step-bridge
next_docs:
- database/replica-lag-read-after-write-strategies
- database/read-your-writes-session-pinning
- database/cache-replica-split-read-inconsistency
linked_paths:
- contents/database/pagination-offset-vs-seek.md
- contents/database/covering-index-composite-ordering.md
- contents/database/replica-read-routing-anomalies.md
- contents/database/read-your-writes-session-pinning.md
- contents/database/replica-lag-read-after-write-strategies.md
- contents/database/cache-replica-split-read-inconsistency.md
confusable_with:
- database/replica-lag-read-after-write-strategies
- database/cache-replica-split-read-inconsistency
- database/read-your-writes-session-pinning
forbidden_neighbors:
- contents/database/pagination-offset-vs-seek.md
- contents/database/replica-read-routing-anomalies.md
expected_queries:
- 페이지네이션에서 같은 row가 다음 페이지에 또 나오면 어디부터 의심해?
- 무한 스크롤에서 row가 빠지거나 중복될 때 원인을 어떻게 나눠?
- OFFSET 페이지네이션이 중간에 밀리는 이유가 뭐야?
- cursor pagination인데도 어떤 row가 사라지면 뭘 확인해야 해?
- 새로고침할 때마다 페이지 결과가 조금씩 바뀌면 정렬 문제야 replica 문제야?
contextual_chunk_prefix: |
  이 문서는 페이지네이션과 무한 스크롤에서 목록이 흔들릴 때 학습자 증상을
  정렬 tie-breaker 누락, OFFSET window drift, replica나 cache 경로 차이,
  cursor 계약 불일치로 이어 주는 symptom_router다. 다음 장에서 또 보임,
  중간 항목이 건너뜀, 새 글이 끼면 순서가 밀림, 새로고침마다 구성원이
  달라짐, seek인데도 빠지는 이유가 뭐지 같은 자연어 표현이 이 문서의 원인
  분기에 매핑된다.
---

# 페이지네이션 중복/누락 원인 라우터

## 한 줄 요약

> 페이지네이션에서 row가 다시 나오거나 빠지는 건 보통 DB가 "랜덤"해서가 아니라, 정렬 기준이 안정적이지 않거나, `OFFSET`과 동시 쓰기가 섞였거나, 페이지마다 읽는 데이터 소스가 달라졌기 때문이다.

## 가능한 원인

1. `ORDER BY created_at`처럼 동률을 깨는 고유 key가 없다. 같은 timestamp 묶음 안에서 row 순서가 바뀌면 1페이지 끝과 2페이지 시작이 매번 흔들린다. 먼저 [Pagination: Offset vs Seek](./pagination-offset-vs-seek.md)와 [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)를 본다.
2. `LIMIT/OFFSET`으로 페이지를 넘기는 동안 중간에 insert/delete가 일어났다. page 2의 `OFFSET 20`은 "아까 본 20개 다음"이 아니라 "지금 시점의 20개를 건너뛴 뒤"라서 밀림과 누락이 생길 수 있다. 이 분기는 [Pagination: Offset vs Seek](./pagination-offset-vs-seek.md)로 바로 이어진다.
3. page 1과 page 2가 서로 다른 replica, cache miss path, 다른 세션 보장 정책을 탔다. 정렬은 같아도 관측 시점이 달라지면 사용자는 중복이나 누락처럼 느낀다. 이때는 [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)과 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)를 본다.
4. cursor가 정렬 축을 다 담지 못한다. 쿼리는 `(created_at, id)`로 정렬하는데 cursor는 `created_at`만 들고 있거나, 다음 페이지에서 filter가 달라지면 seek pagination이어도 row가 건너뛴다. 이 경우 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)보다 먼저 cursor 계약과 정렬 key를 맞춘다.

## 빠른 자기 진단

1. `ORDER BY`가 정말 유일한가부터 본다. `created_at DESC`만 있으면 `id DESC` 같은 tie-breaker를 같이 넣어야 하는 경우가 많다.
2. page 1을 본 뒤 데이터가 계속 추가/삭제되는 화면인지 확인한다. 그렇다면 `OFFSET` 기반에서는 window drift가 기본 위험이다.
3. page 1과 page 2가 같은 primary/replica, 같은 cache policy를 타는지 확인한다. 요청 경로가 다르면 "같은 정렬인데 결과가 다름"이 생긴다.
4. cursor가 정렬 key와 filter 조건을 모두 포함하는지 확인한다. 정렬은 두 컬럼인데 cursor는 한 컬럼만 담으면 seek도 안정적이지 않다.

## 다음 학습

- write 직후 freshness와 replica 시점 차이가 pagination에 섞이는 경우는 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)로 이어서 본다.
- 같은 사용자가 본 페이지 흐름을 세션 단위로 고정해야 한다면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 간다.
- cache hit/miss와 replica 경로가 섞여 목록 구성원이 흔들린다면 [Cache와 Replica가 갈라질 때의 Read Inconsistency](./cache-replica-split-read-inconsistency.md)를 함께 본다.
