---
schema_version: 3
title: Consistency Repair / Anti-Entropy Platform 설계
concept_id: system-design/consistency-repair-anti-entropy-platform-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- consistency repair
- anti-entropy
- drift detection
- merkle tree
aliases:
- consistency repair
- anti-entropy
- drift detection
- merkle tree
- repair queue
- correction workflow
- checksum bucket
- source of truth
- invariant scan
- repair ledger
- reconciliation repair
- repair campaign
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/change-data-capture-outbox-relay-design.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/search-indexing-pipeline-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/backup-restore-disaster-recovery-drill-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
- contents/system-design/read-write-quorum-staleness-budget-design.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/design-pattern/projection-freshness-slo-pattern.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Consistency Repair / Anti-Entropy Platform 설계 설계 핵심을 설명해줘
- consistency repair가 왜 필요한지 알려줘
- Consistency Repair / Anti-Entropy Platform 설계 실무 트레이드오프는 뭐야?
- consistency repair 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Consistency Repair / Anti-Entropy Platform 설계를 다루는 deep_dive 문서다. consistency repair와 anti-entropy 플랫폼은 source of truth와 replica, cache, index, derived store 사이의 drift를 탐지하고, 안전한 보정 작업으로 정합성을 회복하는 운영 복구 시스템이다. 검색 질의가 consistency repair, anti-entropy, drift detection, merkle tree처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Consistency Repair / Anti-Entropy Platform 설계

> 한 줄 요약: consistency repair와 anti-entropy 플랫폼은 source of truth와 replica, cache, index, derived store 사이의 drift를 탐지하고, 안전한 보정 작업으로 정합성을 회복하는 운영 복구 시스템이다.

retrieval-anchor-keywords: consistency repair, anti-entropy, drift detection, merkle tree, repair queue, correction workflow, checksum bucket, source of truth, invariant scan, repair ledger, reconciliation repair, repair campaign, read repair, staleness budget

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Change Data Capture / Outbox Relay 설계](./change-data-capture-outbox-relay-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Backup, Restore, Disaster Recovery Drill 설계](./backup-restore-disaster-recovery-drill-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)
> - [Read / Write Quorum & Staleness Budget 설계](./read-write-quorum-staleness-budget-design.md)
> - [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)
> - [Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)

## 핵심 개념

분산 시스템은 시간이 지나면 반드시 drift가 생긴다.

- cache invalidation 누락
- CDC 유실
- 일부 shard의 replay 실패
- 외부 provider 상태와 내부 상태 불일치
- 사람의 수동 보정 실수

이때 단순 retry로는 해결되지 않는다.
어디가 진실인지 판단하고, 어떤 범위를 어떻게 복구할지 제어해야 한다.

즉, consistency repair는 버그 수정이 아니라 **정합성 회복을 위한 운영 제품**이다.

## 깊이 들어가기

### 1. 무엇이 drift인가

drift는 "값이 다르다"만이 아니다.
실전에서는 다음이 다 포함된다.

- source row는 있는데 index 문서가 없음
- replica는 값이 있지만 version이 뒤처짐
- aggregate count가 source 합계와 다름
- 상태 전이는 맞지만 timestamp ordering이 깨짐
- derived projection은 같아 보여도 business invariant가 위반됨

그래서 repair 시스템은 단순 row diff보다 domain invariant를 같이 알아야 한다.

### 2. Capacity Estimation

예:

- 원본 row 300억 건
- derived index 20개
- drift suspect 비율 0.02%
- 하루 repair budget 5천만 건

이때 봐야 할 숫자:

- scan coverage
- suspect hit ratio
- verification cost
- repair throughput
- false positive rate
- repair-induced load

anti-entropy는 대부분 정상 데이터를 훑어야 하므로, 탐지 비용을 어떻게 낮출지가 중요하다.

### 3. Drift detection 모델

탐지는 보통 층을 나눠서 한다.

- coarse checksum bucket
- range count compare
- Merkle tree 비교
- sample verify
- record-level diff

처음부터 row-by-row compare를 하면 너무 비싸다.
보통은 넓게 의심 범위를 찾고, 좁혀 가며 검증한다.

### 4. Authoritative source를 먼저 고정해야 한다

repair에서 가장 위험한 질문은 "무엇을 기준으로 맞출 것인가"다.

예:

- 검색 인덱스는 DB가 source of truth
- billing ledger는 ledger + provider statement를 함께 봐야 함
- cache는 rebuild가 더 안전함

authoritative source를 명시하지 않으면 repair가 오히려 오염을 퍼뜨린다.

### 5. Repair action은 재처리와 보정으로 나뉜다

대표 접근:

- projection rebuild
- missing event replay
- correction record append
- manual approval repair
- quarantine and hold

특히 금전, 권한, 감사 영역은 원본 row update보다 correction event append가 더 안전할 때가 많다.

### 6. Blast radius control

repair job도 운영 사고를 만들 수 있다.

대응:

- tenant / shard 단위 rate limit
- dry-run diff report
- approval workflow
- idempotent repair key
- rollback 또는 compensating repair plan

즉, repair는 "빨리 맞춘다"보다 "더 망치지 않는다"가 우선이다.
실무에서는 이 단계 자체를 campaign, dry-run, limited rollout, full execution으로 관리하는 orchestration control plane이 따로 있는 편이 안전하다.

### 7. Auditability와 사후 설명 가능성

repair는 나중에 반드시 설명해야 한다.

- 누가 repair를 시작했는가
- 어떤 기준으로 drift를 판단했는가
- 몇 건이 수정되었는가
- 자동 repair인지 수동 승인인지
- 어떤 원본과 어떤 결과를 비교했는가

그래서 repair job과 결과는 audit log, report, correction ledger를 남기는 편이 좋다.

## 실전 시나리오

### 시나리오 1: 검색 인덱스 일부 shard 손상

문제:

- source DB에는 문서가 있지만 검색 결과에 일부가 빠진다

해결:

- count mismatch와 checksum으로 suspect shard를 좁힌다
- 문서 범위만 targeted replay를 수행한다
- 전체 reindex 대신 부분 repair를 우선 시도한다

### 시나리오 2: 결제 상태 불일치

문제:

- 내부 ledger는 CAPTURED인데 provider statement는 AUTHORIZED에 머문다

해결:

- provider truth를 조회해 drift 유형을 분류한다
- 원장 덮어쓰기 대신 correction entry를 append한다
- 고객 영향이 있는 건은 hold queue로 보내 수동 검토한다

### 시나리오 3: object metadata와 blob store 불일치

문제:

- metadata row는 있는데 실제 object가 없거나, 반대로 orphan blob이 남아 있다

해결:

- scan 결과를 suspect queue에 적재한다
- 삭제 후보는 quarantine 기간을 둔다
- 필요한 경우 metadata rebuild와 blob cleanup을 분리한다

## 코드로 보기

```pseudo
function detect(range):
  sourceHash = source.checksum(range)
  targetHash = target.checksum(range)
  if sourceHash != targetHash:
    suspects.enqueue(range)

function repair(range):
  diffs = comparer.diff(source.read(range), target.read(range))
  for diff in diffs:
    action = planner.plan(diff)
    executor.apply(action, repairKey=diff.id)
    audit.record(diff, action)
```

```java
public RepairPlan plan(DriftRecord drift) {
    if (drift.requiresCorrectionLedger()) {
        return RepairPlan.appendCorrection(drift);
    }
    return RepairPlan.rebuildProjection(drift);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Full compare | 정확하다 | 비용이 매우 크다 | 작은 데이터셋, 중요 구간 |
| Checksum / Merkle compare | 탐지 비용이 낮다 | 세부 diff는 추가 단계가 필요하다 | 대규모 데이터 |
| Automatic repair | 대응이 빠르다 | 잘못 고치면 위험하다 | low-risk projection |
| Manual approval repair | 안전하다 | 느리다 | 결제, 권한, 감사 |
| Full rebuild | 단순하다 | 비용과 시간이 크다 | repair보다 rebuild가 더 안전할 때 |

핵심은 consistency repair가 "데이터 수정 스크립트"가 아니라 **drift 탐지, 권위 판단, 보정 실행, 감사 추적을 묶은 운영 복구 체계**라는 점이다.

## 꼬리질문

> Q: anti-entropy와 reconciliation은 같은 말인가요?
> 의도: 용어와 적용 범위 구분 확인
> 핵심: 비슷하지만 anti-entropy는 일반적 정합성 복구, reconciliation은 도메인 truth 비교와 정산 의미가 더 강하다.

> Q: drift가 보이면 바로 source로 overwrite하면 안 되나요?
> 의도: authoritative source와 correction semantics 이해 확인
> 핵심: 도메인에 따라 append-only correction이나 수동 검토가 더 안전할 수 있다.

> Q: checksum이 같으면 완전히 안전한가요?
> 의도: 탐지 기법의 한계 이해 확인
> 핵심: coarse checksum은 빠른 필터일 뿐이며, 충돌과 세부 불일치를 숨길 수 있어 추가 검증이 필요하다.

> Q: repair job의 가장 큰 위험은 무엇인가요?
> 의도: 운영 감각 확인
> 핵심: 잘못된 권위 판단이나 과도한 부하로 원래 문제보다 큰 사고를 만드는 것이다.

## 한 줄 정리

Consistency repair와 anti-entropy 플랫폼은 분산 시스템의 drift를 탐지하고, authoritative source와 blast-radius 제어를 바탕으로 안전하게 정합성을 회복하는 운영 복구 시스템이다.
