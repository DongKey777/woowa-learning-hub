---
schema_version: 3
title: gh-ost / pt-online-schema-change Cutover Precheck Runbook
concept_id: database/gh-ost-pt-osc-cutover-precheck-runbook
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- online-schema-cutover-precheck
- metadata-lock-preflight
- gh-ost-pt-osc-readiness
aliases:
- gh-ost precheck
- pt-online-schema-change precheck
- pt-osc cutover
- gh-ost cutover
- online schema cutover checklist
- metadata lock preflight
- ddl cutover readiness
- cutover runbook
- gh-ost pt-osc cutover
- 온라인 스키마 변경 cutover
symptoms:
- gh-ost나 pt-online-schema-change copy는 끝났지만 cutover 직전 long transaction과 MDL blocker를 확인하지 않았어
- online schema change가 안전하다고 믿고 replica lag, app compatibility, p99 guardrail 없이 swap하려 해
- cutover precheck에 abort 기준이 없어 metadata lock 대기와 latency spike를 장애로 맞고 있어
intents:
- troubleshooting
- design
prerequisites:
- database/online-schema-change-strategies
- database/metadata-lock-ddl-blocking
next_docs:
- database/metadata-lock-outage-triage-cancel-recovery
- database/index-maintenance-window-rollout-playbook
- database/replication-lag-forensics-root-cause-playbook
- database/destructive-schema-cleanup-column-retirement
linked_paths:
- contents/database/online-schema-change-strategies.md
- contents/database/metadata-lock-ddl-blocking.md
- contents/database/metadata-lock-outage-triage-cancel-recovery.md
- contents/database/index-maintenance-window-rollout-playbook.md
- contents/database/replication-lag-forensics-root-cause-playbook.md
- contents/database/destructive-schema-cleanup-column-retirement.md
- contents/database/online-backfill-verification-cutover-gates.md
confusable_with:
- database/metadata-lock-ddl-blocking
- database/online-schema-change-strategies
- database/index-maintenance-window-rollout-playbook
forbidden_neighbors: []
expected_queries:
- gh-ost나 pt-online-schema-change cutover 전에 어떤 precheck와 abort 기준이 필요해?
- online schema change copy는 끝났는데 cutover에서 metadata lock 대기를 피하려면 무엇을 봐야 해?
- long transaction, replica lag, app p99, compatibility를 cutover readiness로 어떻게 점검해?
- gh-ost와 pt-osc는 copy 방식은 달라도 cutover에서 왜 둘 다 MDL에 민감해?
- cutover 직전 old app new schema와 new app old replica compatibility를 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 gh-ost와 pt-online-schema-change의 마지막 cutover 전 long transaction, metadata lock, replica lag, app compatibility, abort criteria를 확인하는 advanced playbook이다.
  gh-ost precheck, pt-online-schema-change precheck, metadata lock preflight, online schema cutover checklist 같은 자연어 운영 질문이 본 문서에 매핑된다.
---
# gh-ost / pt-online-schema-change Cutover Precheck Runbook

> 한 줄 요약: `gh-ost`와 `pt-online-schema-change`의 위험 구간은 복사보다 cutover이며, 직전 precheck가 부실하면 metadata lock 대기와 app latency spike를 장애처럼 맞게 된다.

**난이도: 🔴 Advanced**

관련 문서:

- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
- [Metadata Lock Outage Triage, Cancel, and Recovery Runbook](./metadata-lock-outage-triage-cancel-recovery.md)
- [Index Maintenance Window, Rollout, and Fallback Playbook](./index-maintenance-window-rollout-playbook.md)
- [Replication Lag Forensics and Root-Cause Playbook](./replication-lag-forensics-root-cause-playbook.md)

retrieval-anchor-keywords: gh-ost precheck, pt-online-schema-change precheck, cutover runbook, metadata lock preflight, online schema cutover checklist, ddl cutover readiness, backend migration ops

## 핵심 개념

온라인 스키마 변경 도구는 대부분 "copy/sync" 단계보다 "마지막 cutover" 단계가 더 위험하다.

왜냐하면 cutover 순간에는:

- metadata lock 확보
- rename/swap
- application compatibility
- replica lag 상태

를 동시에 만족해야 하기 때문이다.

그래서 cutover 직전엔 별도 precheck가 필요하다.

## 깊이 들어가기

### 1. precheck의 목적은 "지금 눌러도 되는가"를 숫자로 판단하는 것이다

단순 체크리스트가 아니라, 실제 guardrail을 본다.

- long transaction 없음
- pending MDL 없음
- replica lag budget 이하
- app p95/p99 안정적
- rollback/fallback 소유자 명확

즉 precheck는 진행 의식이 아니라 **중단 조건이 명확한 운영 계약**이다.

### 2. `gh-ost`와 `pt-osc`는 copy 방식이 달라도 cutover는 둘 다 MDL에 민감하다

차이는 분명하다.

- `pt-osc`
  - 트리거 기반 변경 추적
- `gh-ost`
  - binlog 기반 변경 추적

하지만 마지막 cutover에서 필요한 건 둘 다 비슷하다.

- blocker-free window
- 짧은 metadata swap
- app/query compatibility

즉 도구 선택과 별개로 **cutover preflight discipline**은 공통으로 필요하다.

### 3. precheck에서 가장 위험한 건 "조용한 long transaction"이다

위험 세션:

- idle in transaction
- report SELECT with open transaction
- batch cursor pagination
- app bug로 닫히지 않은 transaction

이런 세션은 평소엔 티가 안 나다가 cutover 시점에 MDL blocker가 된다.

### 4. lag budget 초과 상태에서 cutover하면 failover성 읽기 문제까지 겹칠 수 있다

schema cutover 중 replica lag가 이미 높다면:

- app가 새 schema 기대
- replica는 아직 old state
- read path에서 compatibility mismatch

가 생길 수 있다.

그래서 cutover precheck는 MDL뿐 아니라 **replica visibility budget**도 같이 봐야 한다.

### 5. app compatibility precheck를 빼면 "DDL은 성공했는데 서비스는 깨짐"이 된다

질문:

- old app가 new schema를 봐도 안전한가
- new app가 old replica를 봐도 안전한가
- generated column / dropped column / renamed field가 섞인 상태를 허용하는가

즉 cutover readiness는 DB 툴 readiness + app contract readiness다.

### 6. cutover precheck는 cancel 기준이 있어야 의미가 있다

예시:

- pending long transaction > 0 -> abort
- replica lag > 5s -> abort
- p99 > baseline * 2 -> abort
- metadata lock pending detected -> abort

이 기준이 없으면 precheck는 형식이 된다.

## 실전 시나리오

### 시나리오 1. copy는 끝났는데 cutover에서 15분 멈춤

원인:

- idle transaction blocker

교훈:

- copy 성공 여부보다 cutover preflight가 중요

### 시나리오 2. `gh-ost`는 안전할 줄 알았는데 read 오류 발생

원인:

- replica lag가 이미 높았고 app가 new schema를 가정

교훈:

- binlog 기반 도구여도 visibility budget 확인이 필요

### 시나리오 3. `pt-osc` cutover 직전 app p99 상승

원인:

- metadata swap 순간 queueing
- 이미 traffic burst 시간대였음

교훈:

- maintenance window와 cutover precheck는 분리해서 보면 안 된다

## 코드로 보기

```text
cutover precheck
1. no idle/long transaction on target table
2. no pending metadata lock
3. replica lag under threshold
4. app schema compatibility confirmed
5. fallback decision owner present
6. abort threshold documented
```

```sql
SELECT *
FROM performance_schema.metadata_locks
WHERE LOCK_STATUS = 'PENDING';
```

```sql
SHOW FULL PROCESSLIST;
SHOW REPLICA STATUS\G
```

핵심은 도구 명령보다, cutover 직전의 운영 상태를 "go / no-go"로 판정할 수 있게 만드는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 즉시 cutover | 빠르다 | blocker/lag에 취약하다 | 작은 테이블 |
| strict precheck | 실패 확률이 낮다 | 준비 시간이 필요하다 | 대부분의 운영 cutover |
| delay cutover | 더 안전할 수 있다 | migration 시간이 늘어난다 | guardrail 위반 시 |
| abort on threshold | 앱 보호가 쉽다 | 일정이 다시 밀린다 | 중요 서비스 |

## 꼬리질문

> Q: `gh-ost`와 `pt-osc`에서 cutover precheck가 왜 중요한가요?
> 의도: copy와 cutover 위험을 구분하는지 확인
> 핵심: 마지막 metadata swap과 app compatibility는 둘 다 별도 위험 구간이기 때문이다

> Q: cutover 직전 가장 먼저 볼 blocker는 무엇인가요?
> 의도: long transaction이 MDL을 막는다는 감각 확인
> 핵심: idle/long transaction과 pending metadata lock이다

> Q: replica lag도 precheck에 포함해야 하나요?
> 의도: DDL 성공과 read visibility를 같이 보는지 확인
> 핵심: 그렇다. lag가 크면 schema compatibility 문제가 read path에서 드러날 수 있다

## 한 줄 정리

`gh-ost`와 `pt-osc` cutover의 안정성은 도구보다, long transaction·MDL·replica lag·app compatibility를 마지막 순간에 go/no-go로 판정하는 precheck discipline에 달려 있다.
