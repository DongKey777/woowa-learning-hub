# Sort Buffer, Temporary Table, and Spill Behavior

> 한 줄 요약: 정렬과 집계가 느린 이유는 알고리즘보다 메모리 경계에 먼저 걸리기 때문이고, spill이 시작되면 디스크가 비용을 대신 치른다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: sort buffer, temporary table, spill, filesort, using filesort, using temporary, using temporary using filesort, internal temp table, sort buffer spill, sort spill, group by spill, distinct spill, order by spill, sort_merge_passes, Created_tmp_tables, Created_tmp_disk_tables, tmp_table_size, max_heap_table_size, key used but still filesort, key used but temporary, explain extra using filesort, explain extra using temporary, rows are small but sort is slow, disk spill during order by, disk spill during group by, 정렬 spill, 임시 테이블 spill, filesort인데 왜 느린가

## 핵심 개념

- 관련 문서:
  - [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md)
  - [Temporary Table Engine Choice and Spill Behavior](./temp-table-engine-choice-spill-behavior.md)
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)

## 이 문서가 맡는 EXPLAIN 범위

이 문서는 `Using filesort`, `Using temporary`를 봤을 때 "인덱스가 안 맞는다"에서 한 걸음 더 들어가 **메모리 경계와 disk spill**을 해석하는 follow-up entry다.

| 보이는 신호 | 여기서 바로 보는 것 | 먼저 돌아갈 문서 |
| --- | --- | --- |
| `Using filesort`가 보이고 정렬 단계에서 갑자기 느려짐 | sort buffer, row width, sort pass, spill 여부 | [Index Condition Pushdown, Filesort, Temporary Table](./index-condition-pushdown-filesort-temporary-table.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `Using temporary`와 `Created_tmp_disk_tables`가 같이 튐 | internal temp table이 memory에서 disk로 떨어지는 경계 | [Temporary Table Engine Choice and Spill Behavior](./temp-table-engine-choice-spill-behavior.md) |
| `type = ALL`, `key = NULL`이라 정렬 이전에 읽는 row 수부터 과함 | spill 이전의 접근 경로 문제 | [인덱스와 실행 계획](./index-and-explain.md), [쿼리 튜닝 체크리스트](./query-tuning-checklist.md) |
| `rows` 추정치와 actual rows가 어긋나서 sort 비용 계산이 흔들림 | spill보다 통계와 cardinality 해석이 먼저 | [Statistics, Histograms, and Cardinality Estimation](./statistics-histograms-cardinality-estimation.md) |

`ORDER BY`, `GROUP BY`, `DISTINCT`는 겉으로는 SQL 문법 문제처럼 보이지만,  
실제로는 메모리 안에서 끝나느냐, 디스크로 spill 되느냐의 문제로 바뀐다.

핵심 장치는 두 개다.

- sort buffer: 정렬을 위한 per-thread 메모리
- temporary table: 중간 결과를 담는 내부 테이블

이 둘이 경계를 넘으면 디스크 I/O가 늘고, 쿼리는 갑자기 무거워진다.

## 깊이 들어가기

### 1. sort buffer는 per-thread라서 작게 봐야 한다

sort buffer를 크게 잡으면 한 번의 정렬은 유리해질 수 있다.  
하지만 커넥션이 많으면 각 세션이 각자 버퍼를 잡을 수 있어 메모리 사용이 폭증한다.

즉 sort buffer는 "크면 좋다"가 아니라 **동시성 곱을 곱해 봐야 하는 값**이다.

### 2. filesort는 항상 디스크 정렬이 아니다

`Using filesort`는 이름 때문에 헷갈리지만, 반드시 디스크 파일을 뜻하지 않는다.  
핵심은 인덱스 순서로 바로 정렬하지 못해 별도 정렬 경로를 탔다는 의미다.

작은 결과는 메모리에서 끝날 수 있지만,

- 정렬 대상이 크거나
- row width가 넓거나
- limit 없이 많이 가져오면

spill 가능성이 커진다.

### 3. temporary table은 중간 결과의 보관소다

MySQL 내부 임시 테이블은 `GROUP BY`, `DISTINCT`, 파생 테이블, 복잡한 조인에서 자주 생긴다.  
메모리에서 끝나면 괜찮지만, 조건을 넘으면 on-disk temp table로 떨어진다.

이때 자주 보는 신호는 다음이다.

- `Using temporary`
- `Created_tmp_disk_tables`
- `Sort_merge_passes`

### 4. 어떤 쿼리가 spill을 유발하는가

대표적인 예시는 다음과 같다.

- 넓은 `SELECT *`와 함께 정렬
- 인덱스와 맞지 않는 `ORDER BY`
- 큰 `GROUP BY`
- `DISTINCT`와 `ORDER BY`의 조합

즉 쿼리가 느린 이유는 정렬 알고리즘이 나빠서가 아니라, **정렬을 메모리에 다 못 올려서**일 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `sort buffer`
- `temporary table`
- `spill`
- `filesort`
- `internal temp table`
- `Created_tmp_disk_tables`
- `sort_merge_passes`

## 실전 시나리오

### 시나리오 1. LIMIT이 있는데도 느리다

`LIMIT 100`인데도 느리면 정렬 전에 이미 많은 row를 읽고 있을 수 있다.  
정렬 대상 row가 크면 메모리 buffer를 넘어 spill이 발생한다.

### 시나리오 2. GROUP BY가 갑자기 disk I/O를 만든다

집계 결과가 커지고, 그룹 키가 인덱스와 맞지 않으면 temporary table이 디스크로 내려갈 수 있다.  
이때는 집계 전에 필터를 좁히거나, 인덱스 순서를 다시 봐야 한다.

### 시나리오 3. sort buffer를 키웠는데 전체가 느려졌다

한 쿼리는 좋아졌지만, 동시 커넥션이 많아지면서 메모리 압박이 커질 수 있다.  
정렬 최적화는 per-query만 보면 실패하기 쉽다.

## 코드로 보기

### 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'sort_buffer_size';
SHOW VARIABLES LIKE 'tmp_table_size';
SHOW VARIABLES LIKE 'max_heap_table_size';
SHOW VARIABLES LIKE 'internal_tmp_mem_storage_engine';
```

### spill 징후 확인

```sql
SHOW STATUS LIKE 'Created_tmp_disk_tables';
SHOW STATUS LIKE 'Sort_merge_passes';
```

### 실행 계획 확인

```sql
EXPLAIN ANALYZE
SELECT user_id, status, COUNT(*)
FROM orders
WHERE created_at >= '2026-04-01'
GROUP BY user_id, status
ORDER BY COUNT(*) DESC
LIMIT 20;
```

### 정렬을 인덱스로 바꾸는 예시

```sql
CREATE INDEX idx_orders_created_at_user_status
ON orders (created_at, user_id, status);
```

인덱스가 정렬과 맞으면 filesort와 spill을 줄일 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| sort buffer 증가 | 일부 정렬이 빨라질 수 있다 | 세션 수만큼 메모리를 먹는다 | 동시성이 낮고 정렬이 큰 경우 |
| tmp table 한도 증가 | memory temp table 유지가 길어진다 | 메모리 압박과 OOM 위험이 늘 수 있다 | 중간 결과가 자주 약간만 넘을 때 |
| 인덱스 순서 재설계 | spill 자체를 줄일 수 있다 | DDL이 필요하다 | 자주 반복되는 정렬/집계일 때 |
| 쿼리 재작성 | 범위를 줄일 수 있다 | 코드 변경이 필요하다 | 불필요한 row width가 클 때 |

핵심은 버퍼를 늘려서 버티는 게 아니라, **정렬/집계가 spill 전에 끝나도록 쿼리와 인덱스를 맞추는 것**이다.

## 꼬리질문

> Q: `Using filesort`가 보이면 무조건 나쁜가요?
> 의도: 실행 계획 신호를 단순화하지 않는지 확인
> 핵심: 메모리에서 끝나는 filesort도 있고, 인덱스로 못 끝내는 신호일 뿐이다

> Q: sort buffer를 크게 잡으면 왜 위험할 수 있나요?
> 의도: per-thread 메모리 모델 이해 여부 확인
> 핵심: 동시 세션 수만큼 메모리가 누적될 수 있다

> Q: temporary table이 있다고 해서 항상 문제인가요?
> 의도: 임시 테이블을 무조건 악으로 보지 않는지 확인
> 핵심: 중간 결과를 관리하는 정상 경로일 수도 있다

## 한 줄 정리

정렬과 집계의 성패는 알고리즘보다 메모리 경계와 spill 여부에 달려 있고, spill이 나면 temp table과 디스크 I/O가 성능을 결정한다.
