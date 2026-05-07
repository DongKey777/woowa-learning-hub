---
schema_version: 3
title: Vacuum / Purge / Freeze Risk Triage and Runbook Routing
concept_id: database/vacuum-purge-freeze-risk-runbook-routing
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- vacuum
- purge
- freeze
- cleanup-debt
- runbook
aliases:
- vacuum purge freeze risk
- cleanup debt triage
- autovacuum routing
- wraparound risk playbook
- history list length incident
- purge backlog routing
- index only scan vacuum debt
- freeze debt escalation
- vacuum debt vs freeze debt
- purge debt runbook
symptoms:
- PostgreSQL vacuum debt, freeze debt, InnoDB purge debt를 cleanup backlog로만 묶어 같은 런북을 보려 해
- heap fetch 증가와 dead tuple은 성능 debt이고 XID age wraparound는 safety debt라는 분기를 해야 해
- InnoDB history list length, undo growth, purge lag가 보일 때 purge blocker와 throttling 런북으로 연결해야 해
intents:
- symptom
- troubleshooting
- deep_dive
prerequisites:
- database/vacuum-purge-debt-forensics-symptom-map
- database/undo-tablespace-truncation-purge-debt
next_docs:
- database/autovacuum-freeze-debt-wraparound-playbook
- database/purge-backlog-remediation-throttle-playbook
- database/replication-lag-forensics-root-cause-playbook
linked_paths:
- contents/database/vacuum-purge-debt-forensics-symptom-map.md
- contents/database/autovacuum-freeze-debt-wraparound-playbook.md
- contents/database/purge-backlog-remediation-throttle-playbook.md
- contents/database/purge-thread-scheduling-lag-control.md
- contents/database/undo-tablespace-truncation-purge-debt.md
- contents/database/covering-index-vs-index-only-scan.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/replication-lag-forensics-root-cause-playbook.md
confusable_with:
- database/vacuum-purge-debt-forensics-symptom-map
- database/autovacuum-freeze-debt-wraparound-playbook
- database/undo-tablespace-truncation-purge-debt
forbidden_neighbors: []
expected_queries:
- vacuum debt, freeze debt, InnoDB purge debt는 모두 cleanup backlog지만 왜 서로 다른 런북으로 라우팅해야 해?
- PostgreSQL heap fetch 증가와 dead tuple은 performance debt이고 XID wraparound는 safety debt라는 차이를 설명해줘
- InnoDB history list length와 undo growth가 보이면 purge backlog remediation으로 어떻게 내려가?
- autovacuum freeze age 경고를 단순 bloat 청소 문제로 보면 왜 위험해?
- cleanup debt triage에서 첫 5분에 엔진별로 어떤 신호를 봐야 해?
contextual_chunk_prefix: |
  이 문서는 vacuum, purge, freeze cleanup debt를 PostgreSQL vacuum debt, freeze/wraparound safety risk, InnoDB purge debt로 라우팅하는 advanced symptom router다.
  cleanup debt triage, autovacuum routing, history list length incident, wraparound risk 질문이 본 문서에 매핑된다.
---
# Vacuum / Purge / Freeze Risk Triage and Runbook Routing

> 한 줄 요약: vacuum debt, purge debt, freeze debt는 모두 cleanup backlog 계열이지만, 성능 저하를 다루는 사고와 wraparound 안전성 사고는 같은 런북으로 다루면 안 된다.

**난이도: 🔴 Advanced**

관련 문서:

- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)
- [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md)
- [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)
- [Purge Thread Scheduling and Lag Control](./purge-thread-scheduling-lag-control.md)
- [Undo Tablespace Truncation and Purge Debt](./undo-tablespace-truncation-purge-debt.md)
- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
- [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md)

retrieval-anchor-keywords: vacuum purge freeze risk, cleanup debt triage, autovacuum routing, wraparound risk playbook, history list length incident, purge backlog routing, index only scan vacuum debt, freeze debt escalation, backend db maintenance runbook

## 핵심 개념

운영에서 cleanup debt 계열 신호를 보면 먼저 "청소가 밀렸다"라고 묶기 쉽다.  
하지만 실제 대응은 다음 셋으로 갈라서 봐야 한다.

- PostgreSQL vacuum debt
  - dead tuple, bloat, visibility map 지연, index-only scan 회귀 같은 **성능 중심 문제**
- PostgreSQL freeze debt
  - XID age 상승, anti-wraparound 압박 같은 **가용성 안전 문제**
- InnoDB purge debt
  - history list length, undo growth, purge lag 같은 **write-path backlog 문제**

즉 첫 질문은 "얼마나 밀렸나"보다, **지금 다루는 것이 성능 debt인지 safety debt인지**다.

## 깊이 들어가기

### 1. 첫 분류를 잘못하면 런북이 틀어진다

대표적인 오진:

- PostgreSQL heap fetch 증가를 보고 인덱스만 고친다
- freeze age 경고를 bloat 청소 문제로 취급한다
- InnoDB undo growth를 디스크 증설 문제로만 본다

하지만 실제로는:

- 성능 회귀면 vacuum/purge debt forensic과 slow query 흐름이 필요하고
- wraparound 위험이면 autovacuum freeze 대응이 먼저이며
- history backlog면 purge blocker 제거와 throttling 순서가 중요하다

즉 cleanup debt는 하나의 개념이지만, **운영 의사결정은 다른 런북으로 분기**된다.

### 2. 첫 5분 triage는 엔진별로 따로 잡아야 한다

PostgreSQL에서 먼저 볼 것:

- age가 가장 큰 database / relation
- 최근 autovacuum와 freeze 관련 activity
- dead tuple과 heap fetch 증가 여부
- 오래 열린 transaction / snapshot 존재

InnoDB에서 먼저 볼 것:

- `Innodb_history_list_length` 추세
- undo tablespace growth
- 오래 열린 transaction 존재
- purge throttling / purge thread 설정과 현재 backlog

공통으로 중요한 건 절대값 하나가 아니라:

- backlog가 지금도 증가 중인가
- blocker가 명확한가
- worker가 못 도는가, 아니면 돌아도 못 따라가는가

### 3. 관측된 신호를 바로 런북으로 연결해야 한다

| 관측된 신호 | 먼저 물어볼 질문 | 1차 런북 | 다음 연결 |
|------|------|------|------|
| `Heap Fetches` 증가, dead tuple 증가, index-only scan 회귀 | 성능 debt가 visibility와 bloat를 흔드는가 | [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md) | [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md), [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |
| age 경고, anti-wraparound 압박, 큰 low-churn relation age 상승 | 지금은 성능보다 safety가 우선인가 | [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md) | [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md) |
| `Innodb_history_list_length` 증가, undo growth, purge lag | purge가 막혔나, 아니면 못 따라가나 | [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md) | [Purge Thread Scheduling and Lag Control](./purge-thread-scheduling-lag-control.md), [Undo Tablespace Truncation and Purge Debt](./undo-tablespace-truncation-purge-debt.md) |
| replica apply가 밀리는데 purge/vacuum debt 신호도 같이 보임 | 복제 지연의 root cause가 cleanup backlog인가 | [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md) | 엔진에 따라 [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md) 또는 [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md) |

### 4. freeze debt는 항상 별도 escalation lane으로 봐야 한다

vacuum debt와 freeze debt는 둘 다 PostgreSQL autovacuum 문맥에 있지만, 운영 우선순위는 다르다.

- vacuum debt
  - bloat, scan cost, visibility map, heap fetch 같은 성능 신호
- freeze debt
  - XID age, anti-wraparound pressure, 강제 vacuum window 확보 같은 안전 신호

그래서 둘이 동시에 보여도:

1. relation age와 wraparound 위험을 먼저 확인하고
2. 긴 transaction을 끊거나 maintenance window를 확보한 뒤
3. 그다음 bloat와 plan regression을 정리하는 편이 안전하다

즉 freeze debt는 cleanup debt의 하위 케이스가 아니라, **우선순위가 더 높은 운영 이벤트**다.

### 5. purge debt는 worker tuning보다 backlog 생성기 차단이 먼저다

InnoDB incident에서 흔한 실수는 다음이다.

- `innodb_purge_threads`만 올린다
- undo tablespace만 본다
- history list length 절대값만 보고 추세를 놓친다

보통 더 효과적인 순서는:

1. long transaction / snapshot 제거
2. batch pause 또는 chunk 축소
3. 필요 시 throttling
4. purge capacity 조정
5. 추세 반전 확인

즉 purge debt 대응은 worker 숫자보다, **누가 backlog를 만들고 있는지 먼저 끊는 운영 런북**이다.

### 6. 후속 운영은 dashboard와 handoff 기준까지 포함해야 한다

cleanup debt 문서를 읽고 끝내면 재발한다.  
운영 런북으로 연결하려면 최소한 다음 handoff가 있어야 한다.

- PostgreSQL
  - worst relation age dashboard
  - dead tuple / heap fetch / autovacuum lag 관찰
  - long transaction alert
- InnoDB
  - history list length trend
  - undo growth and long transaction count
  - purge throttling 발동 여부

핵심은 "느려졌다"는 티켓을 받았을 때 곧바로 SQL 튜닝으로 가지 않고,  
**cleanup debt 전용 관측 신호를 먼저 거쳐 적절한 런북으로 라우팅**하는 것이다.

## 실전 시나리오

### 시나리오 1. PostgreSQL 목록 API에서 index-only scan 효과가 사라짐

증상:

- `Index Only Scan`인데 `Heap Fetches`가 계속 높다
- dead tuple과 autovacuum lag가 같이 보인다

우선 라우팅:

- [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)

다음 확인:

- [Covering Index vs Index-Only Scan](./covering-index-vs-index-only-scan.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

### 시나리오 2. 잘 안 바뀌는 archive table이 갑자기 위험 relation이 됨

증상:

- low churn table인데 age 경고가 뜬다
- 일반 vacuum debt보다 freeze debt가 더 의심된다

우선 라우팅:

- [Autovacuum Freeze Debt, XID Age, and Wraparound Playbook](./autovacuum-freeze-debt-wraparound-playbook.md)

교훈:

- "잘 안 바뀌니 안전하다"는 가정은 freeze debt에선 틀릴 수 있다

### 시나리오 3. 야간 delete batch 뒤 InnoDB가 점점 무거워짐

증상:

- `Innodb_history_list_length` 상승
- undo growth 지속
- write latency와 replica apply가 같이 나빠진다

우선 라우팅:

- [Purge Backlog Remediation, Throttling, and Recovery Playbook](./purge-backlog-remediation-throttle-playbook.md)

다음 연결:

- [Purge Thread Scheduling and Lag Control](./purge-thread-scheduling-lag-control.md)
- [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md)

## 코드로 보기

```text
runbook routing order
1. identify engine
2. split performance debt vs safety debt
3. find blocker or backlog generator
4. open engine-specific playbook
5. only then tune worker count or maintenance parameters
```

```sql
-- PostgreSQL 감각
SELECT datname, age(datfrozenxid)
FROM pg_database
ORDER BY age(datfrozenxid) DESC;

SELECT relname, age(relfrozenxid)
FROM pg_class
WHERE relkind IN ('r', 'm', 't')
ORDER BY age(relfrozenxid) DESC
LIMIT 20;

SELECT pid, xact_start, state, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

```sql
-- InnoDB 감각
SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW ENGINE INNODB STATUS\G

SELECT trx_id, trx_started, trx_state, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

핵심은 특정 명령어보다, **어떤 위험 축으로 분류하고 어떤 런북으로 넘길지**를 먼저 정하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 느린 쿼리처럼 바로 접근 | 단순하다 | freeze/purge root cause를 놓칠 수 있다 | cleanup debt 신호가 약할 때만 |
| cleanup debt triage 먼저 수행 | 적절한 런북으로 빨리 갈 수 있다 | 엔진별 지표 이해가 필요하다 | bloat, age, undo incident 전반 |
| worker 수부터 조정 | 즉시 시도하기 쉽다 | blocker가 남으면 실패한다 | blocker 부재가 확인된 뒤 |
| 수동 freeze/purge 개입 | 위험을 빠르게 낮춘다 | maintenance 비용과 부하가 있다 | safety risk 또는 backlog 급증 시 |

## 꼬리질문

> Q: freeze debt를 일반 vacuum debt와 같은 런북으로 처리하면 왜 위험한가요?
> 의도: 성능 문제와 가용성 안전 문제를 분리하는지 확인
> 핵심: freeze debt는 wraparound 방지가 우선이라 성능 최적화보다 선제 개입이 먼저다

> Q: `Innodb_history_list_length`가 오를 때 가장 먼저 확인할 것은 무엇인가요?
> 의도: purge capacity보다 blocker를 먼저 보는지 확인
> 핵심: long transaction이나 giant batch가 purge를 막거나 backlog를 만들고 있는지 본다

> Q: index-only scan 회귀가 왜 vacuum debt 런북으로 이어질 수 있나요?
> 의도: 인덱스 설계와 cleanup 상태를 연결하는지 확인
> 핵심: visibility map과 dead tuple 상태가 heap fetch를 다시 늘릴 수 있기 때문이다

## 한 줄 정리

vacuum/purge/freeze incident는 모두 cleanup debt 계열이지만, 성능 debt인지 safety debt인지 먼저 가른 뒤 엔진별 런북으로 넘겨야 대응 순서가 흔들리지 않는다.
