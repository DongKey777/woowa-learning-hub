---
schema_version: 3
title: Vacuum / Purge Debt Forensics and Symptom Map
concept_id: database/vacuum-purge-debt-forensics-symptom-map
canonical: true
category: database
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- vacuum-vs-freeze-debt
- purge-backlog-vs-bloat
- cleanup-debt-signal-mapping
aliases:
- vacuum debt
- purge debt
- mvcc cleanup lag
- bloat forensics
- history list length
- autovacuum lag
- dead tuple growth
- index only scan regression
- backend db cleanup debt
- freeze debt
- xid age
- cleanup debt triage
- runbook routing
symptoms:
- autovacuum이 못 따라오고 dead tuple이 계속 늘어난다
- history list length가 줄지 않고 undo tablespace가 계속 커진다
- index only scan이 갑자기 약해지고 heap fetch가 늘어난다
- purge backlog와 bloat가 같이 보여서 어디부터 봐야 할지 헷갈린다
intents:
- definition
prerequisites:
- database/transaction-isolation-locking
- database/redo-undo-checkpoint-crash-recovery
next_docs:
- database/vacuum-purge-freeze-risk-runbook-routing
- database/mvcc-history-list-snapshot-too-old
- database/purge-backlog-remediation-throttle-playbook
linked_paths:
- contents/database/vacuum-purge-freeze-risk-runbook-routing.md
- contents/database/mvcc-history-list-snapshot-too-old.md
- contents/database/undo-tablespace-truncation-purge-debt.md
- contents/database/change-buffer-purge-history-length.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/autovacuum-freeze-debt-wraparound-playbook.md
- contents/database/purge-backlog-remediation-throttle-playbook.md
confusable_with:
- database/vacuum-purge-freeze-risk-runbook-routing
- database/mvcc-history-list-snapshot-too-old
- database/autovacuum-freeze-debt-wraparound-playbook
forbidden_neighbors:
- contents/database/autovacuum-freeze-debt-wraparound-playbook.md
expected_queries:
- vacuum debt가 뭐야
- purge debt가 쌓이면 어디부터 봐야 해
- dead tuple 늘고 autovacuum이 못 따라오면 무슨 문제야
- history list length가 계속 커질 때 원인 후보가 뭐야
- index only scan이 갑자기 느려졌는데 cleanup debt 때문일 수 있어
- undo tablespace가 줄지 않을 때 purge backlog를 의심해야 하나
contextual_chunk_prefix: |
  이 문서는 운영 중인 데이터베이스에서 vacuum debt와 purge debt가 어떤 증상으로
  드러나는지 처음 잡는 primer다. 청소가 밀린 것 같아, dead tuple이 늘어,
  history list length가 커져, index only scan이 갑자기 약해져, autovacuum이
  못 따라와, undo가 안 줄어, purge backlog가 쌓여, write amplification이 커져
  같은 자연어 paraphrase가 본 문서의 forensic map에 매핑된다.
---
# Vacuum / Purge Debt Forensics and Symptom Map

> 한 줄 요약: vacuum debt와 purge debt는 "청소가 밀렸다"는 같은 문제의 엔진별 표현이며, 증상은 디스크 증가보다 먼저 query plan 왜곡·bloat·history backlog·write amplification으로 드러난다.

**난이도: 🔴 Advanced**

관련 문서:

- [Vacuum / Purge / Freeze Risk Triage and Runbook Routing](./vacuum-purge-freeze-risk-runbook-routing.md)
- [MVCC History List Growth와 Snapshot Too Old](./mvcc-history-list-snapshot-too-old.md)
- [Undo Tablespace Truncation and Purge Debt](./undo-tablespace-truncation-purge-debt.md)
- [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md)
- [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)

retrieval-anchor-keywords: vacuum debt, purge debt, mvcc cleanup lag, bloat forensics, history list length, autovacuum lag, dead tuple growth, index only scan regression, backend db cleanup debt, freeze debt, xid age, cleanup debt triage, runbook routing

## 핵심 개념

MVCC 엔진은 과거 버전을 남기고 나중에 치운다.  
이 청소가 밀리면 엔진마다 이름은 달라도 같은 부채가 쌓인다.

- PostgreSQL 계열
  - dead tuple 증가
  - autovacuum lag
  - table/index bloat
- InnoDB 계열
  - history list length 증가
  - purge lag
  - undo debt / purge backlog

즉 vacuum/purge debt는 스토리지 housekeeping이 아니라, **현재 쿼리와 쓰기 성능을 직접 흔드는 운영 지표**다.

## 깊이 들어가기

### 1. debt는 "공간"보다 "정리되지 않은 과거"를 뜻한다

겉으로는 디스크 증가처럼 보여도 본질은:

- 아직 참조 가능한 old version이 남아 있거나
- dead row/index entry가 정리되지 않았거나
- cleanup worker가 현재 변경 속도를 못 따라간다

는 의미다.

그래서 증상은 디스크 사용량보다 먼저:

- rows scanned 증가
- heap fetch 증가
- index-only 효과 저하
- background IO 증가

로 나타날 수 있다.

### 2. PostgreSQL의 vacuum debt와 InnoDB의 purge debt는 증상 지도가 다르다

비슷하지만 관찰 포인트가 다르다.

- PostgreSQL 쪽에서 보기 쉬운 것
  - dead tuples
  - bloat
  - autovacuum freeze pressure
  - index-only scan heap fetch 회귀
- InnoDB 쪽에서 보기 쉬운 것
  - history list length
  - undo tablespace bloat
  - purge threads backlog
  - change buffer / purge 상호 간섭

즉 "vacuum/purge debt"는 공통 개념이고, **진단 신호는 엔진별로 달라진다**.

### 3. debt가 쌓이는 root cause는 대부분 세 가지다

- 오래 열린 transaction/snapshot
- update/delete churn이 너무 높음
- cleanup worker capacity 부족 또는 scheduling 부적절

특히 긴 snapshot은 두 엔진 모두에서 강력한 blocker다.

### 4. index 성능 회귀가 사실은 cleanup debt일 수 있다

대표 오진:

- "인덱스가 갑자기 안 좋다"
- "커버링 인덱스인데 heap fetch가 많다"
- "rows examined가 계속 늘어난다"

실제 원인:

- dead tuple/dead version이 늘어남
- cleanup이 밀려 page density가 나빠짐
- visibility/cleanup 상태가 index-only path를 방해함

즉 plan regression처럼 보여도 사실은 **cleanup debt가 cost model과 physical locality를 동시에 악화**시킬 수 있다.

### 5. forensic 흐름은 debt 증상 -> blocker -> cleanup capacity 순서가 좋다

권장 순서:

1. debt가 실제로 증가 중인가
2. 어떤 long transaction/snapshot이 cleanup을 막는가
3. update/delete churn이 어떤 테이블에 몰리는가
4. cleanup worker/autovacuum/purge가 못 따라가는가

이 순서를 건너뛰고 vacuum/purge thread 수만 올리면, root cause는 남아 있을 수 있다.

### 6. debt를 줄이는 최선책은 cleanup tuning보다 workload shape 수정인 경우가 많다

실무에서 효과가 큰 것:

- 긴 transaction 제거
- batch chunk 축소
- soft delete 후 대량 정리 전략 재설계
- hot update churn 완화
- report/read path 분리

즉 tuning은 중요하지만, **cleanup debt를 만드는 write/read shape를 바꾸는 것**이 더 근본적일 때가 많다.

## 실전 시나리오

### 시나리오 1. PostgreSQL index-only scan이 갑자기 약해짐

증상:

- 같은 인덱스인데 heap fetch 증가
- autovacuum가 뒤처짐

의심:

- dead tuple 증가
- visibility map 갱신 지연

### 시나리오 2. InnoDB undo tablespace가 계속 커짐

증상:

- history list length 증가
- purge debt 지속

의심:

- 오래 열린 snapshot
- 대량 update/delete batch

### 시나리오 3. 느린 쿼리처럼 보였지만 cleanup debt가 원인

증상:

- rows examined 증가
- write latency와 read latency가 같이 나빠짐

의심:

- cleanup backlog가 physical locality와 background IO를 망침

## 코드로 보기

```text
forensic map
1. debt signal
   - dead tuples / bloat
   - history list length / undo growth
2. blocker
   - long snapshot
   - long transaction
3. churn source
   - heavy update/delete tables
4. cleanup path
   - autovacuum / purge progress
```

```sql
-- InnoDB 감각
SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW ENGINE INNODB STATUS\G
```

```sql
-- PostgreSQL 감각
VACUUM (ANALYZE) orders;
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

핵심은 도구 이름보다, "정리되어야 할 과거가 얼마나 남았고 누가 그 정리를 막는가"를 찾는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| cleanup worker 증설 | backlog를 줄일 수 있다 | IO/CPU를 더 쓴다 | root cause가 capacity 부족일 때 |
| 긴 transaction 제거 | debt root cause를 직접 줄인다 | 코드/배치 수정이 필요하다 | 대부분의 운영 사고 |
| batch chunk 축소 | cleanup pressure를 분산한다 | 총 시간이 늘 수 있다 | 대량 update/delete |
| report/read path 분리 | snapshot debt를 줄인다 | 구조가 복잡해진다 | 긴 분석성 조회 |

## 꼬리질문

> Q: vacuum debt와 purge debt는 같은 문제인가요?
> 의도: 엔진별 용어와 공통 원리를 연결하는지 확인
> 핵심: 이름은 다르지만 MVCC cleanup backlog라는 공통 원리를 가진다

> Q: cleanup debt가 왜 index-only scan이나 plan까지 흔들 수 있나요?
> 의도: 물리 정리 상태와 실행 경로를 연결하는지 확인
> 핵심: dead version/bloat가 scan 비용과 visibility/heap access를 바꾸기 때문이다

> Q: worker 수만 늘리면 항상 해결되나요?
> 의도: tuning과 root cause를 구분하는지 확인
> 핵심: 아니다. 긴 transaction이나 churn 구조가 그대로면 debt는 다시 쌓인다

## 한 줄 정리

vacuum/purge debt는 엔진이 아직 못 치운 과거의 양이고, 그 부채는 공간 사용량보다 먼저 query path와 write path를 동시에 무겁게 만드는 형태로 드러난다.
