---
schema_version: 3
title: ALTER TABLE이 안 끝나요 원인 라우터
concept_id: database/alter-table-not-finishing-symptom-router
canonical: false
category: database
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- metadata-lock-blocker-first-check
- ddl-cutover-precheck
- long-transaction-misdiagnosis
aliases:
- alter table 안 끝남
- ddl 배포가 멈춤
- waiting for table metadata lock
- schema change stuck
- online ddl cutover hang
- alter table pending 상태
symptoms:
- ALTER TABLE 이 몇 분째 끝나지 않고 Waiting for table metadata lock 상태로 남아 있다
- 배포 직후부터 특정 테이블 관련 요청이 줄줄이 느려지고 DDL 세션만 계속 pending 으로 보인다
- gh-ost 나 pt-online-schema-change 는 거의 끝났는데 cutover 단계에서만 멈춘다
- row lock 화면에서는 안 보이는데 schema change 를 거는 순간 서비스가 같이 버벅인다
intents:
- symptom
- troubleshooting
prerequisites:
- database/transaction-basics
- database/lock-basics
next_docs:
- database/metadata-lock-ddl-blocking
- database/metadata-lock-outage-triage-cancel-recovery
- database/gh-ost-pt-osc-cutover-precheck-runbook
- database/online-schema-change-strategies
linked_paths:
- contents/database/metadata-lock-ddl-blocking.md
- contents/database/metadata-lock-outage-triage-cancel-recovery.md
- contents/database/gh-ost-pt-osc-cutover-precheck-runbook.md
- contents/database/online-schema-change-strategies.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
confusable_with:
- database/lock-wait-deadlock-latch-triage-playbook
- database/transaction-timeout-vs-lock-timeout
- database/online-schema-change-strategies
forbidden_neighbors:
expected_queries:
- ALTER TABLE 이 계속 안 끝날 때 row lock 말고 무엇부터 의심해야 해?
- Waiting for table metadata lock 이 보이면 원인을 어떤 갈래로 나눠 봐야 해?
- online schema change 가 cutover 단계에서만 멈추는 이유를 빠르게 진단하고 싶어
- DDL 배포를 걸자마자 서비스 요청까지 같이 느려질 때 어디부터 확인해야 해?
- metadata lock 장애인지 단순 lock timeout 인지 초반에 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 ALTER TABLE이 끝나지 않거나 online schema change cutover가 멈추고,
  Waiting for table metadata lock 상태가 보이거나 배포 직후 특정 테이블 요청까지
  같이 느려지는 상황을 증상에서 원인으로 가르는 symptom_router다. 장기
  트랜잭션이 MDL을 쥔 경우, cutover 전 precheck 부족, row lock/timeout 문제로
  잘못 분류한 경우, 배포 영향 범위를 과소평가한 경우를 나눠서 다음 문서로
  연결한다.
---

# ALTER TABLE이 안 끝나요 원인 라우터

## 한 줄 요약

> `ALTER TABLE`이 안 끝날 때는 "DDL이 원래 느린가?"보다 먼저, 장기 트랜잭션이 metadata lock을 쥐고 있는지, online schema change의 cutover 준비가 부족했는지, 사실은 row lock/timeout 문제를 DDL 문제로 착각한 것인지를 갈라야 한다.

## 가능한 원인

1. **장기 트랜잭션이나 오래 열린 세션이 metadata lock을 놓지 않고 있다.** `SELECT`만 했어도 트랜잭션이 오래 열려 있으면 DDL은 `Waiting for table metadata lock`에서 멈출 수 있다. 이 갈래는 [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)으로 가서 MDL과 row lock의 계층 차이부터 확인한다.
2. **online schema change는 거의 끝났지만 cutover 직전 precheck가 부족했다.** `gh-ost`나 `pt-online-schema-change`는 복사보다 rename/cutover 순간이 위험하므로, idle transaction 하나가 마지막 스위치를 막아 장애처럼 보일 수 있다. 이 경우 [gh-ost / pt-online-schema-change Cutover Precheck Runbook](./gh-ost-pt-osc-cutover-precheck-runbook.md)과 [온라인 스키마 변경 전략](./online-schema-change-strategies.md)으로 이어진다.
3. **문제의 본질은 DDL 자체보다 incident triage다.** 이미 pending DDL 뒤로 앱 요청까지 줄이 생기기 시작했다면, "계속 기다릴지"보다 blocker 탐색과 cancel/continue 판단이 먼저다. 이 분기는 [Metadata Lock Outage Triage, Cancel, and Recovery Runbook](./metadata-lock-outage-triage-cancel-recovery.md)로 연결한다.
4. **실제 병목은 row lock wait, deadlock, lock timeout인데 DDL 증상처럼 보였다.** 배포 직전 같은 테이블에 쓰기 경합이 심하면 "DB가 잠겼다"는 표현만으로 MDL로 오인하기 쉽다. 이때는 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)으로 가서 대기 유형을 먼저 분류한다.

## 빠른 자기 진단

1. DDL 세션 상태에 `Waiting for table metadata lock`이 보이는지 확인한다. 보인다면 row lock 화면만 보고 있지 말고 MDL 분기로 간다.
2. 같은 테이블을 읽거나 만지는 장기 트랜잭션, 리포트 쿼리, 배치 세션이 maintenance window와 겹쳤는지 본다. 있다면 blocker 후보가 가장 강하다.
3. `gh-ost`나 `pt-online-schema-change`를 썼다면 복사 단계가 아니라 cutover 단계에서 멈췄는지 확인한다. 그렇다면 데이터량보다 precheck와 blocker hygiene가 핵심이다.
4. 이미 앱 요청 지연이 같이 커졌다면 DDL 하나의 느림이 아니라 outage 분기다. 이 경우 즉시 blocker 탐색과 cancel 기준부터 잡아야 한다.

## 다음 학습

- MDL이 row lock과 왜 다르고 `ALTER TABLE`을 어떻게 막는지 보려면 [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)을 먼저 읽는다.
- 장애 대응 관점에서 cancel/continue 판단과 blast radius를 보려면 [Metadata Lock Outage Triage, Cancel, and Recovery Runbook](./metadata-lock-outage-triage-cancel-recovery.md)으로 이어간다.
- `gh-ost`나 `pt-online-schema-change` cutover 전 점검 항목이 필요하면 [gh-ost / pt-online-schema-change Cutover Precheck Runbook](./gh-ost-pt-osc-cutover-precheck-runbook.md)을 본다.
- MDL인지 row lock/deadlock/latch contention인지 큰 분기부터 다시 잡고 싶다면 [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)을 함께 본다.
