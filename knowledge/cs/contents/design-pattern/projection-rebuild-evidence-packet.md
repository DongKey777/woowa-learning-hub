# Projection Rebuild Evidence Packet

> 한 줄 요약: projection rebuild readiness와 cutover approval은 dashboard 캡처 몇 장이 아니라, replay completeness, parity artifacts, rollback proof를 같은 시점 기준으로 묶은 versioned evidence packet으로 판단해야 흔들리지 않는다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Rollback Window Exit Criteria](./projection-rollback-window-exit-criteria.md)
> - [Poison Event and Replay Failure Handling in Projection Rebuilds](./projection-rebuild-poison-event-replay-failure-handling.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Cursor Rollback Packet](./cursor-rollback-packet.md)
> - [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)
> - [System Design: Dual-Read Comparison / Verification Platform](../system-design/dual-read-comparison-verification-platform-design.md)

retrieval-anchor-keywords: projection rebuild evidence packet, rebuild readiness packet, cutover approval packet, projection cutover evidence bundle, projection signoff packet, replay completeness evidence, parity artifact bundle, dual read evidence packet, pagination parity artifact, rollback proof packet, rollback rehearsal proof, cutover rollback proof, rebuild readiness metrics, cutover decision packet, canonical evidence packet, projection approval artifact, rollback readiness proof

---

## 핵심 개념

projection rebuild 판단이 흔들리는 이유는 보통 증거가 흩어져 있기 때문이다.

- replay 진행률은 batch dashboard에 있음
- parity 결과는 dual-read report에 흩어져 있음
- rollback 가능성은 runbook 문장으로만 남아 있음
- 승인 근거는 채팅이나 회의 메모에 섞여 있음

이 상태에서는 "같은 시도(attempt)를 보고 있는가", "같은 watermark 기준인가", "같은 topology에서 검증했는가"가 자꾸 엇갈린다.

Projection Rebuild Evidence Packet은 이 전환을 **한 번의 승격 시도에 대한 canonical approval artifact**로 고정한다.  
packet 하나는 최소한 아래 네 질문에 같은 답을 줘야 한다.

1. rebuild가 목표 replay boundary를 실제로 따라잡았는가
2. old/new projection이 사용자 의미 기준으로 충분히 같았는가
3. 지금 즉시 rollback해도 예산 안에 복구된다는 증거가 있는가
4. 현재 허용된 결정이 `HOLD`, `READY_FOR_CANARY`, `READY_FOR_PRIMARY`, `ROLLBACK_ONLY` 중 무엇인가

### Retrieval Anchors

- `projection rebuild evidence packet`
- `rebuild readiness packet`
- `cutover approval packet`
- `replay completeness evidence`
- `parity artifact bundle`
- `rollback proof packet`
- `cutover rollback proof`
- `projection signoff packet`
- `canonical evidence packet`

---

## 깊이 들어가기

### 1. packet은 "한 번의 승격 시도" 단위로 고정해야 한다

evidence packet은 주간 상태 보고서가 아니라 **특정 candidate projection을 특정 boundary까지 올린 뒤 내리는 승인 문서**다.

최소 header는 아래 필드를 고정해야 한다.

| 필드 | 의미 | 왜 필요한가 |
|---|---|---|
| `packet_id` | 이번 rebuild/cutover 시도의 고유 식별자 | retry 후 이전 증거와 섞이지 않게 한다 |
| `requested_action` | `READY_FOR_CANARY`, `READY_FOR_PRIMARY`, `ROLLBACK_ONLY` 등 | 지금 이 packet이 무엇을 승인받으려는지 분명히 한다 |
| `candidate_projection_id` | 새 projection/table/index identity | 어떤 world를 승인하는지 고정한다 |
| `baseline_projection_id` | 비교 기준 old projection identity | parity 기준점을 고정한다 |
| `target_watermark` | rebuild가 따라잡아야 할 boundary | replay completeness의 기준점을 만든다 |
| `evaluation_window` | metrics/artifact를 채집한 시간 구간 | 서로 다른 시각의 dashboard를 한 packet으로 섞지 않게 한다 |
| `schema_contracts` | projector build, normalization version, cursor version 등 | data drift와 contract drift를 구분한다 |

핵심은 retry를 덮어쓰지 않는 것이다.  
poison event fix나 projector 재배포 뒤 다시 측정했다면 `packet_id`를 새로 만들고, 이전 packet은 archive로 남기는 편이 맞다.

### 2. required metrics는 gate별로 묶어야 해석이 흔들리지 않는다

숫자는 많을수록 좋은 것이 아니라, 승인 질문에 직접 답하는 최소 세트를 고정하는 편이 낫다.

| Gate | 필수 metric | green 의미 | false green 방지 포인트 |
|---|---|---|---|
| Replay completeness | `target_watermark`, `applied_watermark`, `backlog_age_p95/p99`, `failed_shard_count`, `quarantine_open_count`, `partial_gap_count` | history backfill과 tail catch-up이 기준선 안에 들어옴 | progress 100%인데 shard 누락이나 quarantine 미해결이 숨는 경우를 막는다 |
| User-visible parity | `mismatch_rate`, `strict_path_mismatch_count`, `fingerprint_bucket_coverage`, `unknown_sample_rate` | 대표 query/strict path에서 의미 차이가 허용치 이내 | row count만 같고 상태/정렬/strict path가 깨지는 경우를 막는다 |
| Pagination parity `if applicable` | `first_page_parity_floor`, `second_page_continuity_floor`, `cursor_verdict_floor`, `reason_code_drift_count` | 목록 first page, next page, cursor policy가 함께 녹색 | first page만 맞고 page 2 또는 cursor verdict가 흔들리는 false green을 막는다 |
| Operational safety | `fallback_rate`, `remaining_error_budget_ratio`, `lag_reserve_ratio`, `p95/p99_latency_regression` | cutover 실험과 rollback window를 버틸 headroom이 남음 | parity는 맞지만 fallback spike나 budget burn으로 실험을 감당 못 하는 상황을 막는다 |
| Rollback readiness | `rollback_rto_seconds`, `rollback_rto_budget_seconds`, `old_projection_warm`, `rollback_command_green` | old path 복귀가 실제로 가능하고 예산 안이다 | runbook 존재만 있고 실제 switch가 안 되는 상태를 막는다 |

pagination endpoint가 아니더라도 `User-visible parity`와 `Rollback readiness`는 빠질 수 없다.  
반대로 목록/search endpoint라면 pagination metrics를 optional note가 아니라 **conditional mandatory**로 취급하는 편이 맞다.

### 3. 숫자만 있으면 packet이 아니라 scoreboard가 된다

approval packet에는 metric과 함께 **같은 세계를 증명하는 artifact link**가 들어 있어야 한다.

| Artifact | 필수 여부 | 무엇을 증명하나 |
|---|---|---|
| Replay boundary manifest | 필수 | 어떤 shard/range/watermark를 대상으로 rebuild했는지 고정한다 |
| Quarantine / retry ledger | 필수 | poison event, partial gap, last verified watermark, restart plan을 설명한다 |
| Dual-read parity summary | 필수 | baseline/candidate compare window와 mismatch 분포를 고정한다 |
| Mismatch drilldown sample | 필수 | low-rate mismatch가 어떤 종류인지 사람 눈으로 검증하게 한다 |
| Strict-path freshness / fallback snapshot | strict path가 있으면 필수 | read-your-writes, fallback rate, freshness breach를 같은 packet에서 읽게 한다 |
| Pagination parity rollup | paginated endpoint면 필수 | `fingerprint_bucket`, `cursor_verdict_pair`, `continuity_outcome`를 승인 근거로 묶는다 |
| Rollback rehearsal log | 필수 | 실제 switch, warm check, measured RTO가 green인지 증명한다 |
| Cursor rollback packet | paginated/versioned cursor endpoint면 필수 | rollback 뒤 어떤 cursor world를 canonical로 볼지 설명한다 |
| Approval record | 필수 | owner/on-call/who/when/why를 packet에 남긴다 |

즉 packet은 "지표 이름 + 수치"만 적는 표가 아니라, **해당 수치를 재현할 수 있는 artifact bundle**이어야 한다.  
artifact link가 빠진 metric은 설명 가능한 근거가 아니라 참고 수치에 가깝다.

### 4. parity artifact는 "대표성"과 "drilldown 가능성"을 둘 다 가져야 한다

parity green을 주장하려면 두 층이 동시에 보여야 한다.

| 층 | 최소 포함물 | 왜 필요한가 |
|---|---|---|
| Rollup | mismatch rate, fingerprint coverage, strict-path summary, pagination outcome distribution | 승인 회의에서 빠르게 green/red를 읽게 한다 |
| Drilldown | top mismatch bucket, sampled record diff, offending query fingerprint, reason-code drift sample | "왜 틀렸는가"를 바로 파고들 수 있게 한다 |

특히 paginated endpoint는 아래 세 artifact가 같이 있어야 한다.

1. `fingerprint_bucket` coverage snapshot
2. `cursor_verdict_pair` / `requested -> emitted version` matrix
3. `page1 -> page2` continuity outcome rollup

셋 중 하나라도 빠지면 "row는 거의 맞는다"와 "pagination contract가 안전하다"를 혼동하기 쉽다.  
이 packet vocabulary는 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)와 같은 필드 이름을 그대로 쓰는 편이 안전하다.

### 5. rollback proof는 선언이 아니라 실행 증거여야 한다

rollback proof가 약해지는 가장 흔한 이유는 "되돌릴 수 있음"을 runbook 문장으로만 적어 두는 것이다.

| Proof item | minimum proof | 이것만으로는 부족하다 |
|---|---|---|
| Switch primitive | 실제 feature flag, alias, routing target, owner | "old로 되돌리면 된다"는 추상 설명 |
| Rehearsal freshness | 같은 topology와 권한 상태에서 최근에 실행한 rehearsal 시각 | 지난주 성공 로그 |
| Old projection health | old index/table warm 상태, lag/오류율 정상 | 단순히 리소스가 남아 있다는 사실 |
| Measured rollback RTO | 실제 측정된 복귀 시간과 budget 비교 | 감으로 적은 예상 시간 |
| Cursor / fallback contract | rollback 뒤 cursor reason code, restart 방식, strict fallback routing | "client가 알아서 새로고침한다"는 가정 |

운영 기본값은 아래처럼 두는 편이 안전하다.

- rollback rehearsal이 stale이면 `READY_FOR_PRIMARY`를 주지 않는다
- old projection이 cold면 `ROLLBACK_ONLY`도 강한 조건부로 해석한다
- paginated endpoint인데 cursor rollback packet이 없으면 rollback proof를 incomplete로 본다

즉 rollback proof는 "옛 path가 존재한다"가 아니라 **지금 되돌리면 얼마 만에 어떤 계약으로 복구되는지 입증됐다**는 뜻이다.

### 6. verdict vocabulary는 작고 단정해야 한다

packet verdict를 길게 서술하면 팀마다 다른 표현을 쓰게 된다.  
실무에서는 아래 네 값 정도로 고정하는 편이 운영 해석이 빠르다.

| Verdict | 의미 | 언제 쓰는가 |
|---|---|---|
| `HOLD` | 증거가 부족하거나 일부 gate가 red | replay/parity/rollback 중 하나라도 미완료일 때 |
| `READY_FOR_CANARY` | rebuild readiness는 green, 아직 primary 증거는 아님 | baseline compare와 rollback proof가 준비돼 canary admission 가능할 때 |
| `READY_FOR_PRIMARY` | canary evidence까지 포함해 full cutover 승인 가능 | stage floor, dwell, budget, rollback window entry 조건이 모두 green일 때 |
| `ROLLBACK_ONLY` | correctness 또는 budget이 red라 candidate 승격은 불가, 복귀 준비만 허용 | hard mismatch, strict-path regression, budget stop 상황일 때 |

중요한 점은 `READY_FOR_CANARY`와 `READY_FOR_PRIMARY`를 같은 green으로 묶지 않는 것이다.  
rebuild readiness packet은 admission gate를, canary 확장 packet은 promotion gate를 설명한다.

### 7. packet 예시는 artifact link와 decision을 함께 가져야 한다

```json
{
  "packet_id": "orders.search/rebuild-2026-04-14T09:30:00+09:00",
  "requested_action": "READY_FOR_CANARY",
  "candidate_projection_id": "orders_search_v2",
  "baseline_projection_id": "orders_search_v1",
  "target_watermark": "kafka:orders:*:1823901",
  "evaluation_window": {
    "compare_started_at": "2026-04-14T08:30:00+09:00",
    "compare_ended_at": "2026-04-14T09:20:00+09:00"
  },
  "schema_contracts": {
    "projector_build": "2026.04.14-rc3",
    "normalization_version": 4,
    "cursor_versions": [1, 2]
  },
  "replay_metrics": {
    "applied_watermark": "kafka:orders:*:1823901",
    "backlog_age_p99_seconds": 18,
    "failed_shard_count": 0,
    "quarantine_open_count": 0,
    "partial_gap_count": 0
  },
  "parity_metrics": {
    "mismatch_rate": 0.0006,
    "strict_path_mismatch_count": 0,
    "fingerprint_bucket_coverage": 42,
    "unknown_sample_rate": 0.0
  },
  "pagination_metrics": {
    "required": true,
    "first_page_parity_floor_met": true,
    "second_page_continuity_floor_met": true,
    "cursor_verdict_floor_met": true,
    "reason_code_drift_count": 0
  },
  "safety_metrics": {
    "fallback_rate": 0.003,
    "remaining_error_budget_ratio": 0.74,
    "lag_reserve_ratio": 0.61,
    "p99_latency_regression_ratio": 1.06
  },
  "rollback_proof": {
    "rollback_rehearsed_at": "2026-04-14T09:05:00+09:00",
    "rollback_command_green": true,
    "old_projection_warm": true,
    "rollback_rto_seconds": 84,
    "rollback_rto_budget_seconds": 120,
    "cursor_packet_id": "orders.search/rollback-world-v1"
  },
  "artifacts": {
    "replay_boundary_manifest": "artifacts/orders-search/replay-boundary.json",
    "quarantine_ledger": "artifacts/orders-search/quarantine-ledger.json",
    "dual_read_summary": "artifacts/orders-search/dual-read-summary.json",
    "pagination_rollup": "artifacts/orders-search/pagination-rollup.json",
    "rollback_rehearsal_log": "artifacts/orders-search/rollback-rehearsal.txt"
  },
  "decision": {
    "verdict": "READY_FOR_CANARY",
    "blocking_reasons": [],
    "approved_by": [
      "projection-owner",
      "oncall"
    ]
  }
}
```

핵심은 `metrics`, `artifacts`, `decision`이 한 packet에서 떨어지지 않는다는 점이다.  
숫자만 있고 artifact가 없거나, artifact는 있는데 verdict가 없으면 approval packet으로 쓰기 어렵다.

### 8. review 순서를 고정하면 승인 회의가 짧아진다

evidence packet review는 보통 아래 순서가 가장 빠르다.

1. header가 이번 attempt와 target watermark를 정확히 고정하는가
2. replay completeness에서 `failed_shard`, `quarantine`, `partial_gap`가 남아 있지 않은가
3. parity rollup과 drilldown이 같은 결론을 말하는가
4. strict path와 pagination artifact가 실제 사용자 계약까지 덮는가
5. rollback rehearsal이 fresh하고 RTO가 budget 안인가
6. verdict가 `requested_action`과 모순되지 않는가

이 순서를 문서화해 두면, "대시보드 몇 개는 초록인데 왜 승인 보류냐"는 논쟁을 줄일 수 있다.

---

## 실전 시나리오

### 시나리오 1: 검색 projection은 parity green인데 rollback proof가 stale한 경우

- mismatch rate와 fingerprint coverage는 green
- pagination packet도 `PASS` 중심
- 하지만 rollback rehearsal은 이틀 전 topology에서만 실행됨

이 경우 packet verdict는 보통 `HOLD`가 맞다.  
cutover 승인은 정합성 alone이 아니라 rollback proof freshness까지 포함해야 한다.

### 시나리오 2: 상세 조회 projection이라 pagination artifact가 없는 경우

상세 조회만 serve하는 projection이라면 pagination packet 자체는 필요 없을 수 있다.  
대신 strict-path mismatch와 fallback snapshot은 더 강하게 들어가야 한다.

- `strict_path_mismatch_count = 0`
- read-your-writes fallback green
- rollback command green

즉 conditional artifact를 빼는 대신, 해당 endpoint의 사용자 계약을 증명하는 artifact는 더 선명해야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 채팅/회의 메모 중심 승인 | 빠르고 가볍다 | retry history, metric window, rollback proof가 쉽게 섞인다 | 사용자 영향이 거의 없는 소규모 projection일 때만 |
| 표준 evidence packet 기반 승인 | attempt별 근거와 verdict가 선명하다 | artifact 정리와 archive 비용이 든다 | 대부분의 user-visible projection cutover |
| packet을 너무 크게 확장 | forensic에 강하다 | 읽기 느리고 필수 gate가 흐려진다 | 규제/감사 요구가 강한 시스템에서만 |

판단 기준은 단순하다.

- packet은 작아도 필수 gate를 빠뜨리면 안 된다
- pagination, strict path, rollback proof는 endpoint 계약에 맞게 conditional mandatory로 다뤄야 한다
- 새 packet을 만드는 비용보다 잘못된 cutover 비용이 보통 더 크다

---

## 요약

- rebuild readiness와 cutover approval은 흩어진 dashboard가 아니라 versioned evidence packet으로 판단한다
- packet은 replay completeness, parity artifacts, rollback proof, explicit verdict를 함께 가져야 한다
- paginated endpoint는 `fingerprint_bucket`, `cursor_verdict_pair`, `continuity_outcome` artifact가 조건부 필수다
- rollback proof는 old path 존재가 아니라 fresh rehearsal과 measured RTO로 증명한다
