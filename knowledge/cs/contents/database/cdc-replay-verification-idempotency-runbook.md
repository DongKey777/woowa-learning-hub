---
schema_version: 3
title: CDC Replay Verification, Idempotency, and Acceptance Runbook
concept_id: database/cdc-replay-verification-idempotency-runbook
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- cdc-replay
- replay-verification
- idempotency
- acceptance-runbook
aliases:
- cdc replay verification
- replay acceptance
- replay idempotency
- bounded repair fence
- replay cutoff
- projection replay check
- dedup replay validation
- replay checksum
- replay shadow compare
- backend repair runbook
symptoms:
- CDC replay를 다시 흘렸다는 실행 사실로만 끝내고 count, checksum, sample diff, shadow compare acceptance를 남기지 않는다
- idempotency guard 없이 replay해 search index, summary table, webhook 같은 downstream side effect가 중복된다
- upper fence와 repair manifest 없이 live traffic과 replay traffic을 섞어 mismatch 해석이 불가능해진다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- database/cdc-gap-repair-reconciliation-playbook
- database/cdc-backpressure-binlog-retention-replay
- database/idempotency-key-and-deduplication
next_docs:
- database/online-backfill-verification-cutover-gates
- database/summary-drift-detection-bounded-rebuild
- system-design/dual-read-comparison-verification-platform-design
linked_paths:
- contents/database/cdc-gap-repair-reconciliation-playbook.md
- contents/database/cdc-backpressure-binlog-retention-replay.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/database/online-backfill-verification-cutover-gates.md
- contents/database/summary-drift-detection-bounded-rebuild.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
- contents/system-design/reconciliation-window-cutoff-control-design.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
confusable_with:
- database/cdc-gap-repair-reconciliation-playbook
- database/online-backfill-verification-cutover-gates
- database/idempotency-key-and-deduplication
- system-design/replay-repair-orchestration-control-plane-design
forbidden_neighbors: []
expected_queries:
- CDC replay는 다시 흘리는 것으로 끝이 아니라 idempotency guard와 acceptance verification이 필요한 이유가 뭐야?
- replay 후 count checksum sample diff shadow compare로 복구 완료를 증명하는 기준을 알려줘
- CDC replay 중 webhook, email, cache invalidation 같은 external side effect를 mute하거나 분리해야 하는 이유가 뭐야?
- repair manifest에 lower upper fence, scope, expected cardinality, acceptance query를 남기는 절차를 설명해줘
- replay-safe consumer에서 event dedup, effect idempotency, repair-run journal을 세 겹으로 보는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 CDC Replay Verification, Idempotency, and Acceptance Runbook playbook으로,
  bounded replay가 duplicate side effect 없이 충분히 복구됐음을 event dedup, side-effect mute,
  repair manifest, count/checksum/sample diff/shadow compare acceptance로 검증하는 절차를 설명한다.
---
# CDC Replay Verification, Idempotency, and Acceptance Runbook

> 한 줄 요약: CDC replay는 "다시 흘렸다"로 끝나는 작업이 아니라, 중복 side effect 없이 scope가 충분히 복구됐음을 count/checksum/shadow compare로 확인하는 검증 절차가 함께 있어야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](./cdc-gap-repair-reconciliation-playbook.md)
- [CDC Backpressure, Binlog/WAL Retention, and Replay Safety](./cdc-backpressure-binlog-retention-replay.md)
- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [Idempotent Transaction Retry Envelope](./idempotent-transaction-retry-envelopes.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)
- [Summary Drift Detection, Invalidation, and Bounded Rebuild](./summary-drift-detection-bounded-rebuild.md)
- [Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md)
- [Historical Backfill / Replay Platform 설계](../system-design/historical-backfill-replay-platform-design.md)
- [Dual-Read Comparison / Verification Platform 설계](../system-design/dual-read-comparison-verification-platform-design.md)
- [Replay / Repair Orchestration Control Plane 설계](../system-design/replay-repair-orchestration-control-plane-design.md)
- [Reconciliation Window / Cutoff Control 설계](../system-design/reconciliation-window-cutoff-control-design.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)

retrieval-anchor-keywords: cdc replay verification, replay acceptance, replay idempotency, bounded repair fence, replay cutoff, projection replay check, dedup replay validation, replay checksum, replay shadow compare, repair manifest, backend repair runbook

## 핵심 개념

CDC replay 작업의 위험은 두 방향이다.

- replay가 부족해서 일부 데이터가 여전히 비어 있음
- replay가 과해서 중복 side effect나 overcount가 생김

그래서 replay runbook에는 항상 두 축이 필요하다.

1. bounded repair scope
2. idempotency guard
3. acceptance verification

즉 replay는 실행보다 **어디까지 다시 흘릴지 + 재실행해도 안전한가 + 정말 복구됐는가**가 더 중요하다.

## 깊이 들어가기

### 1. replay는 repair primitive이지 correctness 증명이 아니다

이벤트를 다시 흘렸다는 사실만으로는 다음을 알 수 없다.

- 필요한 범위를 다 포함했는가
- consumer dedup이 제대로 작동했는가
- projection이 정확히 같은 상태에 도달했는가

따라서 replay는 수리 수단이고, correctness는 별도 검증이 필요하다.

### 2. idempotency guard가 없으면 replay 자체가 위험하다

필수 장치:

- event id dedup table
- merge/upsert semantics
- side effect suppression
- replay mode에서 외부 emit 차단 또는 분리

특히 search index, summary table, webhook relay처럼 파생 effect가 많은 시스템은 replay mode를 별도 플래그로 두는 편이 안전하다.

### 3. acceptance는 count 하나로 끝나면 안 된다

최소 검증 계층:

- row count / event count
- checksum / aggregate hash
- sample diff
- shadow read compare

집계 projection이면 bucket checksum, row projection이면 key-level sample diff가 더 유용할 수 있다.

### 4. bounded repair는 lower/upper fence가 있어야 한다

replay 범위를 "어제 30분치쯤"으로 잡으면 live traffic과 repair traffic이 섞인다.

최소한 다음 경계가 필요하다.

- lower fence: 처음 suspect한 source offset 또는 event time
- upper fence: repair 시작 시점에 고정한 high watermark
- domain scope: tenant, aggregate type, bucket, shard
- effect policy: live emit 허용 여부, mute 여부, correction-only 여부

upper fence가 없으면 acceptance 시점의 mismatch가 "아직 repair 중인 과거 데이터"인지 "새로 들어온 현재 traffic"인지 구분하기 어렵다.

### 5. replay acceptance는 scope-aware 해야 한다

전체 파이프라인을 다시 본다고 생각하면 비용이 커진다.  
더 현실적인 기준:

- tenant 단위
- aggregate type 단위
- 시간 bucket 단위
- event sequence range 단위

즉 acceptance 기준도 repair scope에 맞춰 잘라야 한다.

### 6. repair manifest와 verification plan을 같이 남겨야 한다

bounded replay는 보통 실행 버튼보다 manifest가 더 중요하다.

남겨둘 항목:

- replay 사유와 장애 ticket
- source lower/upper fence
- projection/tenant/bucket 범위
- expected cardinality와 예상 dedup hit 비율
- acceptance query와 shadow compare 샘플 기준
- fail 시 전환할 repair mode(backfill, recompute, full rebuild)

이 manifest가 있어야 database runbook과 system-design 차원의 orchestration control plane이 같은 기준으로 움직인다.

### 7. idempotency는 consumer dedup 하나로 끝나지 않는다

실전 replay-safe 경로는 보통 세 겹으로 본다.

- event-level dedup: 같은 `event_id` 재수신 방지
- effect-level idempotency: 외부 webhook, cache invalidation, downstream emit 중복 방지
- repair-run journal: 어떤 repair run이 어떤 fence 안에서 무엇을 다시 흘렸는지 기록

즉 processed-event 테이블만 있어도 일부는 막을 수 있지만, repair run 자체를 추적하지 않으면 "이번 dedup hit가 정상적인 재처리인지, scope 밖 중복인지"를 해석하기 어렵다.

### 8. 외부 side effect는 replay와 분리해야 할 때가 많다

replay 중 위험한 것:

- webhook 재발송
- 이메일/알림 재발송
- 외부 API 재호출

이런 경로는 보통:

- replay mode에서 mute
- outbox emit 분리
- side effect는 별도 reconciliation

처럼 다루는 편이 낫다.

특히 마감된 정산 window나 이미 발송된 사용자 알림은 원본 기간을 조용히 덮어쓰기보다 correction-only flow로 보내는 편이 안전하다.

### 9. 끝낼 조건을 숫자로 정해야 한다

예시:

- scope row count mismatch = 0
- checksum mismatch bucket = 0
- sample diff = 0
- replay dedup reject rate expected range 내
- out-of-scope write count = 0
- replay fence 이후 late arrival는 correction queue로 우회됨

acceptance 기준이 없으면 replay는 끝났는지 아닌지도 사람마다 다르게 판단하게 된다.

## 실전 시나리오

### 시나리오 1. search projection 30분 구간 replay

필요한 것:

- lower/upper source offset 확정
- document id dedup
- old/new doc sample compare
- missing document count = 0
- out-of-scope update count = 0

### 시나리오 2. summary bucket replay

주의:

- additive replay면 overcount 위험
- recompute overwrite가 더 안전할 수 있음
- close된 bucket이면 correction entry가 더 적합할 수 있음

따라서 replay acceptance 전에 projection 타입 자체를 재평가해야 한다.

### 시나리오 3. retention은 남아 있지만 live traffic이 계속 들어온다

이때는 replay 범위를 더 넓히는 것보다:

- high watermark를 먼저 고정하고
- 그 시점 이후 쓰기는 live path로 계속 받고
- fence 밖 late event는 correction queue로 분리

하는 편이 acceptance를 단순하게 만든다.

### 시나리오 4. replay 후 운영자는 "이제 됐나?"를 묻는다

이때 답은 작업 완료가 아니라:

- repair manifest 상 upper fence 검증 완료 여부
- acceptance gates 통과 여부
- remaining drift count
- side effect mute 상태

로 해야 한다.

## 코드로 보기

```sql
CREATE TABLE replay_verification_run (
  run_id BIGINT PRIMARY KEY,
  projection_name VARCHAR(100) NOT NULL,
  scope_key VARCHAR(255) NOT NULL,
  source_start_offset VARCHAR(255) NOT NULL,
  source_end_offset VARCHAR(255) NOT NULL,
  side_effect_mode VARCHAR(30) NOT NULL,
  replayed_count BIGINT NOT NULL,
  dedup_hit_count BIGINT NOT NULL,
  checksum_match BOOLEAN NOT NULL,
  sample_diff_count BIGINT NOT NULL,
  out_of_scope_write_count BIGINT NOT NULL,
  accepted BOOLEAN NOT NULL,
  verified_at TIMESTAMP NOT NULL
);
```

```text
replay acceptance gates
1. repair manifest approved
2. lower/upper fence fixed
3. dedup guard enabled
4. external side effects muted or isolated
5. count/checksum/sample diff gates pass
6. out-of-scope write count = 0
7. stale scope closed or correction queue attached
```

```java
if (!scopeFence.includes(event.sourcePosition())) {
    routeToCorrectionQueue(event);
    return;
}

if (processedEventRepository.exists(event.id())) {
    return;
}

projection.apply(event);

if (!verification.accepted()) {
    throw new ReplayAcceptanceFailedException();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| replay only | 빠르다 | correctness 증명이 약하다 | 임시 대응 |
| bounded replay + correction-only cutoff | live traffic와 repair traffic를 분리하기 쉽다 | fence/cutoff 설계가 필요하다 | close window나 지속 쓰기 환경 |
| replay + acceptance gates | 복구 신뢰도가 높다 | 준비가 더 필요하다 | 중요한 projection |
| side effect mute mode | replay가 안전해진다 | 운영 모드가 복잡해진다 | 외부 emit가 있는 replay |
| recompute instead of replay | 집계엔 더 단순할 수 있다 | row-level history 보존은 약하다 | summary projection |

## 꼬리질문

> Q: replay가 성공적으로 끝났다는 건 무엇을 의미하나요?
> 의도: 실행 완료와 correctness를 구분하는지 확인
> 핵심: 이벤트를 다시 흘린 것과 projection이 정상 상태에 도달한 것은 다른 말이다

> Q: replay에서 idempotency guard가 왜 중요한가요?
> 의도: replay가 수리이면서 동시에 중복 위험이라는 점을 이해하는지 확인
> 핵심: dedup과 side effect suppression이 없으면 replay가 새 오류를 만들 수 있다

> Q: acceptance를 어떻게 확인하나요?
> 의도: 정량적 검증 기준을 갖는지 확인
> 핵심: count, checksum, sample diff, shadow compare 같은 gate로 확인한다

> Q: replay 범위의 upper fence가 왜 필요한가요?
> 의도: bounded repair와 live traffic 분리를 이해하는지 확인
> 핵심: upper fence가 없으면 검증 mismatch가 과거 복구 누락인지 현재 유입 데이터인지 해석할 수 없다

## 한 줄 정리

CDC replay의 완성은 "다시 흘림"이 아니라, bounded repair fence 안에서 idempotency guard와 acceptance gate를 통과해 정말 복구됐음을 증명하는 것이다.
