---
schema_version: 3
title: 쿼리 튜닝 체크리스트
concept_id: database/query-tuning-checklist
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- query-tuning-verification-order
- sargable-predicate-check
- app-vs-db-bottleneck-split
aliases:
- query tuning checklist
- explain triage
- explain analyze
- type all
- key null
- rows estimate wrong
- using filesort
- using temporary
- index not used
- order by limit slow
- sargable predicate
- app vs db bottleneck
- 실행 계획 체크리스트
- 쿼리 튜닝 순서
symptoms:
- 느린 쿼리를 감으로 고치고 있는데 어떤 순서로 검증해야 할지 모르겠어
- type ALL, key NULL, Using filesort, rows 추정 이상 중 무엇을 먼저 볼지 헷갈려
- DB query time은 짧은데 API latency가 긴 경우 connection pool 문제인지 궁금해
intents:
- troubleshooting
- design
prerequisites:
- database/index-and-explain
next_docs:
- database/slow-query-analysis-playbook
- database/generated-columns-functional-index-migration
- database/covering-index-composite-ordering
- database/statistics-histograms-cardinality-estimation
- database/connection-pool-transaction-propagation-bulk-write
linked_paths:
- contents/database/index-and-explain.md
- contents/database/generated-columns-functional-index-migration.md
- contents/database/covering-index-composite-ordering.md
- contents/database/index-condition-pushdown-filesort-temporary-table.md
- contents/database/statistics-histograms-cardinality-estimation.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/connection-pool-transaction-propagation-bulk-write.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/covering-index-width-fanout-write-amplification.md
confusable_with:
- database/index-and-explain
- database/slow-query-analysis-playbook
- database/connection-pool-transaction-propagation-bulk-write
forbidden_neighbors: []
expected_queries:
- 쿼리가 느릴 때 인덱스부터 만들지 말고 어떤 순서로 확인해야 해?
- type ALL, key NULL, rows estimate wrong, Using filesort를 보고 다음 조치를 고르는 체크리스트가 필요해
- sargable predicate가 아니라서 인덱스를 못 타는 경우를 어떻게 찾아?
- DB 쿼리는 빠른데 API latency가 길면 connection pool과 transaction boundary를 어떻게 봐?
- 배치 insert/update는 성능이 좋아도 lock과 rollback 범위가 왜 위험할 수 있어?
contextual_chunk_prefix: |
  이 문서는 느린 쿼리를 감으로 고치지 않고 EXPLAIN, EXPLAIN ANALYZE, predicate sargability, index, sorting, cardinality, connection pool, transaction boundary, batch size 순서로 검증하는 advanced playbook이다.
  key null, type all, using filesort, using temporary, rows estimate wrong, app latency vs DB time mismatch, connection pool starvation 같은 자연어 증상 질문이 본 문서에 매핑된다.
---
# 쿼리 튜닝 체크리스트

**난이도: 🔴 Advanced**

> 쿼리 튜닝은 감으로 하는 작업이 아니라, 확인 순서가 있는 검증 작업이다.

관련 문서: [인덱스와 실행 계획](./index-and-explain.md), [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md), [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md), [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md), [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
retrieval-anchor-keywords: query tuning checklist, explain triage, explain analyze, type all, key null, rows estimate wrong, using filesort, using temporary, index not used, order by limit slow, sargable predicate, functional index, generated column, covering index, connection pool starvation, app vs db bottleneck, batch size tuning, 실행 계획 체크리스트, 쿼리 튜닝 순서

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [EXPLAIN symptom별 첫 라우트](#explain-symptom별-첫-라우트)
- [먼저 확인할 것](#먼저-확인할-것)
- [읽기 쿼리 체크리스트](#읽기-쿼리-체크리스트)
- [쓰기 경계와 connection pool](#쓰기-경계와-connection-pool)
- [Batch insert/update trade-off](#batch-insertupdate-trade-off)
- [실무 적용 순서](#실무-적용-순서)
- [시니어 관점 질문](#시니어-관점-질문)

</details>

## 왜 이 문서가 필요한가

쿼리가 느릴 때 가장 흔한 실수는 “인덱스를 하나 더 만들면 되겠지”라고 바로 결론 내리는 것이다.

실제로는 다음이 먼저다.

- 어떤 쿼리가 느린지
- 데이터량이 얼마나 되는지
- 실행 계획이 무엇을 선택했는지
- 느린 이유가 CPU, I/O, 락, 네트워크 중 무엇인지

쿼리 튜닝은 SQL 한 줄을 고치는 일이 아니라, 병목의 원인을 좁혀가는 일이다.

## EXPLAIN symptom별 첫 라우트

| 보이는 신호 | 먼저 물어볼 질문 | 먼저 볼 문서 | 이어서 볼 문서 |
| --- | --- | --- | --- |
| `type = ALL`, `key = NULL` | 인덱스 자체가 없거나 predicate가 sargable 하지 않은가 | [인덱스와 실행 계획](./index-and-explain.md) | [Generated Columns, Functional Indexes, and Query-Safe Migration](./generated-columns-functional-index-migration.md) |
| `Using filesort`, `ORDER BY ... LIMIT`에서 급격히 느려짐 | 정렬을 인덱스 순서로 끝낼 수 있는가 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) |
| `Using index`가 보이는데도 체감 성능이 약함 | 커버링은 됐지만 row 수, index 폭, heap/table 접근이 남는가 | [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md) | [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md), [Covering Index Width, Leaf Fanout, and Write Amplification](./covering-index-width-fanout-write-amplification.md) |
| `rows` 추정치가 이상하거나 배포 후 plan이 흔들림 | 통계가 오래됐거나 데이터 skew가 커졌는가 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |
| DB query time은 짧은데 API latency는 김 | 진짜 병목이 connection pool, transaction boundary, 외부 호출인가 | [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md) | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |

---

## 먼저 확인할 것

1. 느리다는 기준을 숫자로 잡는다.
2. 평균보다 p95, p99를 본다.
3. 실제 운영 데이터로 재현한다.
4. `EXPLAIN`과 실제 실행 시간을 함께 본다.

숫자 없이 시작하면, 개선인지 우연인지 구분하기 어렵다.

---

## 읽기 쿼리 체크리스트

### 1. 조건이 sargable 한가

인덱스를 쓸 수 있는 형태인지 확인한다.

예:

- `WHERE created_at >= ? AND created_at < ?`
- `WHERE email = ?`

반대로 아래는 인덱스를 못 타기 쉽다.

- 컬럼에 함수 적용
- 앞부분이 비어 있는 `LIKE`
- 암묵적 타입 변환

함수 적용이 꼭 필요한 조건이라면, 쿼리 rewrite가 가능한지 먼저 보고 그다음 generated column이나 functional index를 검토한다.

### 2. 필요한 컬럼만 읽는가

`SELECT *`는 편하지만, 실제로는 불필요한 I/O와 네트워크 전송을 만든다.

특히 목록 조회에서는 필요한 컬럼만 명시하는 편이 좋다.

### 3. 정렬과 페이징이 맞는가

큰 테이블에서 `OFFSET`이 커질수록 비용이 커진다.

가능하면 아래를 우선 검토한다.

- 커서 기반 페이징
- 정렬 컬럼에 맞는 복합 인덱스

### 4. 조인 순서와 카디널리티를 봤는가

조인은 단순히 문법 문제가 아니라, 어느 테이블을 먼저 줄일지가 중요하다.

`EXPLAIN`에서 예상 row 수가 과하게 크면, 먼저 필터링할 경로를 다시 봐야 한다.

### 5. 인덱스가 실제로 쓰이는가

인덱스를 추가한 뒤에는 반드시 확인해야 한다.

- optimizer가 그 인덱스를 선택하는가
- 더 좋은 인덱스가 따로 있는가
- 인덱스만으로 해결되는 문제인가

---

## 쓰기 경계와 connection pool

connection pool은 DB 연결을 재사용하기 위한 장치다.  
하지만 풀을 크게 잡는다고 시스템이 자동으로 빨라지지는 않는다.

중요한 점은 **커넥션을 오래 잡고 있으면 다른 요청이 기다린다**는 것이다.

### transaction boundary 기본 원칙

- 트랜잭션은 가능한 짧게 유지한다
- 비즈니스 유효성 검사는 트랜잭션 밖에서 최대한 끝낸다
- 외부 API 호출, 파일 처리, 긴 계산은 트랜잭션 안에 넣지 않는다
- 커넥션은 필요한 순간에만 확보하고 빨리 반환한다

### 흔한 실수

- HTTP 요청 전체를 하나의 DB 트랜잭션으로 묶는다
- 락을 잡은 채로 외부 결제를 기다린다
- 배치 작업이 커넥션을 장시간 점유한다

이렇게 되면 쿼리 자체는 빨라도 전체 시스템은 느려진다. 병목은 DB가 아니라 connection pool starvation일 수 있다.

---

## Batch insert/update trade-off

배치는 보통 성능을 올린다. 하지만 공짜는 아니다.

### 장점

- 네트워크 왕복 횟수가 줄어든다
- statement prepare/execute 오버헤드가 줄어든다
- 대량 적재에 유리하다

### 단점

- 한 번 실패하면 롤백 범위가 커질 수 있다
- 한 트랜잭션이 너무 길어질 수 있다
- 락과 undo, redo 부담이 커질 수 있다
- 에러가 났을 때 어느 row가 문제인지 추적이 어려울 수 있다

### 판단 기준

- 같은 SQL을 많이 반복하는가
- 한 번에 묶어도 락 경합이 감당 가능한가
- 실패 시 재시도 단위를 잘게 나눌 수 있는가
- 배치 크기를 조절할 수 있는가

실무에서는 보통 “아주 큰 배치 한 번”보다 “적당한 크기로 끊은 배치 여러 번”이 운영하기 쉽다.

---

## 실무 적용 순서

1. 느린 쿼리를 특정한다.
2. 실행 계획을 본다.
3. 조건, 인덱스, 정렬, 조인을 점검한다.
4. connection pool 점유 시간을 본다.
5. 배치 크기와 커밋 주기를 조정한다.
6. 변경 후 실제 데이터로 다시 확인한다.

순서가 중요하다. 인덱스부터 바꾸면 원인을 가릴 수 있다.

---

## 시니어 관점 질문

- 이 문제는 쿼리 최적화 문제인가, connection pool 문제인가?
- transaction boundary가 과도하게 넓지 않은가?
- batch size를 키웠을 때 얻는 이득과 잃는 것은 무엇인가?
- 현재 튜닝이 데이터 증가에도 계속 유효한가?
- 운영 중인 쿼리를 어떻게 안전하게 검증할 것인가?
