---
schema_version: 3
title: Temporary Table Engine Choice and Spill Behavior
concept_id: database/temp-table-engine-spill-behavior
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- temporary-table
- spill
- using-temporary
- filesort
- query-tuning
aliases:
- temporary table engine
- internal temp table
- temp table spill
- in-memory temp table
- on-disk temp table
- TempTable engine
- Created_tmp_disk_tables
- tmp_table_size
- max_heap_table_size
- Using temporary
symptoms:
- EXPLAIN에 Using temporary가 보이고 Created_tmp_disk_tables가 늘어 disk spill을 의심해야 해
- row 수는 많지 않은데 SELECT width가 넓어 temp table이 메모리에서 디스크로 떨어져
- GROUP BY, DISTINCT, derived table materialization 중 어떤 internal temp table 경로가 spill을 만들었는지 봐야 해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- database/sort-buffer-temp-table-spill
- database/index-condition-pushdown-filesort-temporary-table
next_docs:
- database/statistics-histograms-cardinality-estimation
- database/hash-join-materialization-join-buffer
- database/slow-query-analysis-playbook
linked_paths:
- contents/database/sort-buffer-temp-table-spill.md
- contents/database/index-condition-pushdown-filesort-temporary-table.md
- contents/database/query-tuning-checklist.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/hash-join-materialization-join-buffer.md
- contents/database/statistics-histograms-cardinality-estimation.md
confusable_with:
- database/sort-buffer-temp-table-spill
- database/index-condition-pushdown-filesort-temporary-table
- database/hash-join-materialization-join-buffer
forbidden_neighbors: []
expected_queries:
- Using temporary와 Created_tmp_disk_tables가 같이 늘면 temp table spill을 어떻게 분석해야 해?
- row 수는 작아도 row width가 넓으면 internal temp table이 disk로 떨어지는 이유가 뭐야?
- GROUP BY, DISTINCT, derived table materialization이 어떤 임시 테이블 경로를 만들 수 있어?
- tmp_table_size와 max_heap_table_size는 temp table memory/disk fallback에 어떻게 영향을 줘?
- Using filesort가 주증상인지 Using temporary spill이 주증상인지 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 temporary table engine choice와 spill behavior를 internal temp table, Created_tmp_disk_tables, tmp_table_size, GROUP BY/DISTINCT materialization 관점으로 설명하는 advanced deep dive다.
  Using temporary, temp table disk fallback, row width spill, Created_tmp_disk_tables 질문이 본 문서에 매핑된다.
---
# Temporary Table Engine Choice and Spill Behavior

> 한 줄 요약: temp table은 내부 작업공간이고, 어떤 엔진을 쓰느냐보다 언제 디스크로 spill 되느냐가 성능을 가른다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: temporary table engine, in-memory temp table, on-disk temp table, spill behavior, internal temp table, TempTable engine, using temporary, using temporary using filesort, Created_tmp_tables, Created_tmp_disk_tables, temp table spill, group by temp table, distinct temp table, derived table materialization spill, tmp_table_size, max_heap_table_size, internal_tmp_mem_storage_engine, explain extra using temporary, rows are not huge but temp table spills, temp table disk fallback, 임시 테이블 엔진, 임시 테이블 spill

## 핵심 개념

- 관련 문서:
  - [Sort Buffer, Temporary Table, and Spill Behavior](./sort-buffer-temp-table-spill.md)
  - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
  - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [Hash Join, Materialization, Join Buffer](./hash-join-materialization-join-buffer.md)

## 이 문서가 맡는 EXPLAIN 범위

이 문서는 `Using temporary`가 보일 때 "임시 테이블이 생긴다"를 넘어서 **어떤 internal temp table 경로가 spill을 만들었는가**를 읽는 세부 entry다.

| 보이는 신호 | 여기서 바로 보는 것 | 먼저 돌아갈 문서 |
| --- | --- | --- |
| `Using temporary`와 `Created_tmp_disk_tables`가 같이 문제로 보임 | memory temp table 한계, row width, disk fallback 조건 | [Sort Buffer, Temporary Table, and Spill Behavior](./sort-buffer-temp-table-spill.md) |
| `Using filesort`가 주증상이고 temp table은 부차적임 | 정렬 경로와 인덱스 순서 해석 | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md) |
| `type = ALL`, `key = NULL`이라 temp table 이전에 스캔 폭이 과함 | 접근 경로와 sargability부터 재확인 | [인덱스와 실행 계획](./index-and-explain.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `rows` 추정치나 plan drift 때문에 temp table 선택이 흔들림 | 통계와 cardinality 문제를 먼저 분리 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |

MySQL의 내부 temporary table은 `GROUP BY`, `DISTINCT`, 파생 테이블, 정렬 중간 결과 등을 위해 쓰인다.  
이때 핵심은 "temp table을 쓰는가"가 아니라, **어떤 엔진으로 유지되다가 언제 disk spill이 되는가**다.

메모리 temp table은 빠르지만 제한이 있고, 디스크 temp table은 느리지만 버틸 수 있다.

## 깊이 들어가기

### 1. temp table은 왜 필요한가

쿼리를 한 번에 결과로 못 만들면 중간 결과를 저장해야 한다.

- `GROUP BY` 결과를 합쳐야 할 때
- `DISTINCT` 중복 제거가 필요할 때
- 파생 테이블을 재사용할 때
- 조인/정렬 후 다시 정리해야 할 때

### 2. 메모리 temp table과 디스크 temp table의 차이

메모리 temp table은 빠르지만, row width와 row count가 커지면 한계를 넘는다.  
그 경계를 넘으면 디스크로 spill된다.

실무에서 볼 신호:

- `Using temporary`
- `Created_tmp_tables`
- `Created_tmp_disk_tables`

### 3. 엔진 선택이 항상 직접 드러나지는 않는다

MySQL 버전과 설정에 따라 internal temp table의 구현이 달라질 수 있다.  
하지만 운영 감각은 동일하다.

- 메모리 안에서 끝나면 좋다
- spill이 나면 디스크 I/O가 섞인다
- row가 넓으면 더 빨리 spill된다

### 4. 어떤 쿼리가 spill을 유발하나

- 넓은 `SELECT *`
- 큰 `GROUP BY`
- `ORDER BY`와 `DISTINCT`의 결합
- 조인 후 중간 결과가 큰 경우

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `temporary table engine`
- `internal temp table`
- `spill behavior`
- `Created_tmp_disk_tables`
- `tmp_table_size`
- `max_heap_table_size`

## 실전 시나리오

### 시나리오 1. 집계 쿼리가 작은 데이터에서도 느리다

row 수는 많지 않은데도 느리다면 row width가 넓어 temp table이 spill되고 있을 수 있다.  
필요 컬럼만 줄이는 것만으로도 효과가 크다.

### 시나리오 2. 평소엔 메모리에서 끝나는데 특정 날만 느리다

데이터 분포가 바뀌거나 특정 상태값이 몰리면 temp table이 디스크로 떨어질 수 있다.  
통계와 분포를 같이 봐야 한다.

### 시나리오 3. `DISTINCT`가 생각보다 무겁다

중복 제거는 단순 비교가 아니라 정리 작업이다.  
인덱스와 맞지 않으면 temp table이 커질 수 있다.

## 코드로 보기

### 설정 확인

```sql
SHOW VARIABLES LIKE 'tmp_table_size';
SHOW VARIABLES LIKE 'max_heap_table_size';
SHOW VARIABLES LIKE 'internal_tmp_mem_storage_engine';
```

### spill 관찰

```sql
SHOW STATUS LIKE 'Created_tmp_tables';
SHOW STATUS LIKE 'Created_tmp_disk_tables';
```

### 예시 쿼리

```sql
EXPLAIN ANALYZE
SELECT status, COUNT(*)
FROM orders
GROUP BY status
ORDER BY COUNT(*) DESC;
```

### row width 줄이기

```sql
SELECT status, COUNT(*)
FROM orders
WHERE created_at >= '2026-04-01'
GROUP BY status;
```

필요 없는 컬럼을 덜 들고 가면 spill 가능성이 줄어든다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| memory temp table 유지 | 빠르다 | 메모리 한계를 넘으면 spill된다 | 작은 중간 결과 |
| disk temp table 허용 | 큰 결과도 처리 가능 | I/O 비용이 증가한다 | 큰 집계/정렬 |
| row width 축소 | spill 가능성을 줄인다 | 쿼리 수정이 필요하다 | API 응답 컬럼이 많을 때 |
| tmp table 한도 증가 | 메모리 체류를 늘린다 | 전체 메모리 압박이 생길 수 있다 | 동시성이 낮고 여유 메모리가 있을 때 |

핵심은 temp table을 없애는 게 아니라, **spill 전에 끝내도록 결과 폭을 제어하는 것**이다.

## 꼬리질문

> Q: internal temp table이 왜 생기나요?
> 의도: 중간 결과가 필요한 이유를 이해하는지 확인
> 핵심: 한 번에 최종 결과를 만들 수 없을 때 쓰기 때문이다

> Q: spill이 왜 위험한가요?
> 의도: 메모리와 디스크 경계의 의미를 아는지 확인
> 핵심: 디스크 I/O가 섞이면서 latency가 급격히 늘 수 있다

> Q: temp table을 줄이려면 무엇부터 보나요?
> 의도: 쿼리 구조와 row width를 먼저 보는지 확인
> 핵심: 필요한 컬럼과 필터 범위를 먼저 줄인다

## 한 줄 정리

temporary table은 중간 결과를 관리하는 내부 작업공간이고, 메모리 한계를 넘는 순간 spill이 성능을 지배한다.
