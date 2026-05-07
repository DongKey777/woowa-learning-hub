---
schema_version: 3
title: Rollback Window Exit Criteria
concept_id: design-pattern/projection-rollback-window-exit-criteria
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- rollback-window-exit
- old-projection-decommission
- latent-bug-audit
aliases:
- rollback window exit criteria
- projection rollback window
- old projection decommission
- old path retirement
- rollback command verification
- rollback rehearsal
- post-primary audit cadence
- latent bug audit
- business cycle coverage
- final rollback verification
symptoms:
- primary promotion 직후 일정 시간이 지났다는 이유만으로 old projection을 제거해 rollback window와 forensic 비교 지점을 잃는다
- average mismatch가 낮다는 이유로 strict sentinel, tail bucket, legacy cursor 같은 latent-bug audit를 생략한다
- rollback command가 문서에 있다는 것만 확인하고 종료 직전 실제 switch, 권한, old projection warm 상태를 검증하지 않는다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/read-model-cutover-guardrails
- design-pattern/canary-promotion-thresholds-projection-cutover
- design-pattern/projection-rebuild-backfill-cutover-pattern
next_docs:
- design-pattern/cursor-rollback-packet
- design-pattern/dual-read-pagination-parity-sample-packet-schema
- design-pattern/projection-freshness-slo-pattern
linked_paths:
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/canary-promotion-thresholds-projection-cutover.md
- contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md
- contents/design-pattern/projection-canary-cohort-selection.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/design-pattern/strict-pagination-fallback-contracts.md
- contents/design-pattern/cursor-pagination-parity-read-model-migration.md
- contents/design-pattern/cursor-rollback-packet.md
confusable_with:
- design-pattern/canary-promotion-thresholds-projection-cutover
- design-pattern/read-model-cutover-guardrails
- design-pattern/projection-rebuild-evidence-packet
- design-pattern/cursor-rollback-packet
forbidden_neighbors: []
expected_queries:
- Rollback window exit은 primary promotion과 old projection decommission을 왜 별도 승인으로 봐야 해?
- old projection을 지우기 전에 business-cycle coverage, audit cadence, latent-bug sweep, final rollback verification을 왜 봐야 해?
- rollback command verification은 runbook 존재가 아니라 topology, auth, old projection warm, RTO를 실제로 확인해야 하는 이유가 뭐야?
- low-QPS 서비스에서 evidence 기준을 낮추기보다 rollback window를 늘려야 하는 이유가 뭐야?
- 전체 mismatch rate가 낮아도 strict sentinel이나 tail bucket audit가 남으면 old path 제거를 보류해야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Rollback Window Exit Criteria playbook으로, projection primary promotion 후
  old projection 제거를 시간 경과가 아니라 business-cycle coverage, audit cadence, latent-bug
  bucket sweep, final rollback command verification, old projection warm state, measured RTO가 모두
  green인 별도 decommission approval로 다루는 방법을 설명한다.
---
# Rollback Window Exit Criteria

> 한 줄 요약: primary promotion 뒤 old projection을 제거하는 시점은 단순 시간 경과가 아니라 audit cadence 완료, latent-bug bucket 재검증, rollback command 최종 green, business-cycle coverage가 모두 증명됐을 때다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Projection Rebuild, Backfill, and Cutover Pattern](./projection-rebuild-backfill-cutover-pattern.md)
> - [Projection Canary Cohort Selection](./projection-canary-cohort-selection.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Cursor and Pagination Parity During Read-Model Migration](./cursor-pagination-parity-read-model-migration.md)
> - [Cursor Rollback Packet](./cursor-rollback-packet.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Traffic Shadowing / Progressive Cutover 설계](../system-design/traffic-shadowing-progressive-cutover-design.md)

retrieval-anchor-keywords: rollback window exit criteria, projection rollback window, old projection decommission, old path retirement, rollback command verification, rollback rehearsal, post-primary audit cadence, latent bug audit, latent mismatch sweep, strict audit bucket, business cycle coverage, projection decommission checklist, cutover exit criteria, final rollback verification, old projection teardown gate, cursor rollback packet, rollback cursor verification, rollback cursor reason code

---

## 핵심 개념

primary promotion은 "새 projection을 기본값으로 serve한다"는 뜻이고, rollback window exit는 "old projection을 치워도 된다"는 뜻이다.  
이 둘을 같은 승인으로 묶으면 두 가지 오판이 반복된다.

- 승격 직후 수치가 잠깐 좋아 보인다는 이유로 old path를 너무 빨리 제거함
- old path 유지 비용이 아깝다는 이유로 latent bug 확인을 생략함

rollback window exit는 시간을 다 채웠는지보다, **늦게 드러나는 문제를 볼 증거가 충분한지**를 묻는 운영 gate다.

### Retrieval Anchors

- `rollback window exit criteria`
- `old projection decommission`
- `rollback command verification`
- `post-primary audit cadence`
- `latent bug audit`
- `strict audit bucket`
- `business cycle coverage`
- `projection decommission checklist`
- `old path retirement gate`
- `final rollback verification`

---

## 깊이 들어가기

### 1. primary promotion과 old projection 제거는 별도 승인으로 다뤄야 한다

primary 100% 승격은 보통 다음을 뜻한다.

- 새 projection이 기본 serve path가 됨
- old projection은 rollback/fallback 용도로 유지됨
- latent bug를 찾기 위한 audit가 계속 돌아감

반면 old projection 제거는 다음이 추가로 증명돼야 한다.

- 늦은 배치/refresh/traffic pulse까지 지나도 correctness가 유지됨
- high-risk bucket 재검증이 끝남
- rollback command가 마지막 시점까지 실제로 작동함

즉 `PRIMARY 100%`는 운영 단계이고, `DECOMMISSION OLD PROJECTION`은 종료 승인이다.

### 2. exit 기준은 단일 타이머가 아니라 4축 증거 packet이어야 한다

| 축 | 확인 질문 | green 신호 예시 | 왜 필요한가 |
|---|---|---|---|
| Coverage | 충분히 다양한 실트래픽이 지났는가 | 최소 1 business cycle, 1개 이상 batch/refresh cycle 통과 | 낮 시간에만 보이는 녹색과 야간/배치 시그널을 구분한다 |
| Audit cadence | 정해 둔 감사 주기를 빠짐없이 돌렸는가 | planned audit slot 100% 수행, `UNKNOWN` blind spot 허용치 이하 | "문제가 없었다"와 "안 봤다"를 구분한다 |
| Latent-bug sweep | 평균 지표 밖의 위험 bucket이 녹색인가 | strict/tail/hotspot bucket 재검증 완료, 새 mismatch cluster 0 | rare query, deep page chain, post-write bug는 늦게 드러난다 |
| Rollback verification | 되돌리는 명령이 지금도 살아 있는가 | final rehearsal green, old projection warm, RTO 예산 이내 | 지난번 rehearsal 기록만 믿고 old path를 지우는 실수를 막는다 |

운영 문서에는 최소한 이 네 축이 같은 exit packet 안에 있어야 한다.  
한 축이라도 빠지면 "시간은 지났는데 왜 못 닫느냐"는 질문에 다시 감으로 답하게 된다.

### 3. audit cadence는 초반 burst와 늦은 tail을 둘 다 덮어야 한다

rollback window audit는 한 번의 종합 점검보다 **여러 시계(clock)를 덮는 cadence**가 중요하다.

| 시점 | cadence 예시 | 반드시 보는 것 | 왜 이 타이밍인가 |
|---|---|---|---|
| `T+0 ~ T+30m` | 5~10분 간격 | fallback spike, strict correctness, backlog age, rollback command dry-run summary | cutover 직후 급성 장애와 misrouting을 빨리 잡는다 |
| `T+30m ~ T+4h` | 30~60분 간격 | top fingerprint, cursor verdict pair, strict screen audit, tail sentinel spot-check | 대표 트래픽과 초기 latent bug cluster를 본다 |
| business-cycle 경계 | cycle당 1회 | 지역/테넌트 skew, write-after-read, non-default sort, large page size, batch 영향 | 특정 시간대나 운영 이벤트에서만 깨지는 버그를 잡는다 |
| window close 직전 | 종료 전 최종 1회 | open incident 0, high-risk bucket 재검증, final rollback verification, archive packet | old path 제거 직전에 마지막 판단을 고정한다 |

cadence는 QPS가 낮다고 없애는 것이 아니라, 더 오래 유지해서 채우는 편이 안전하다.

### 4. latent bug audit는 평균 mismatch가 아니라 "늦게 드러나는 표본"을 다시 봐야 한다

rollback window에서 놓치기 쉬운 버그는 대개 전체 평균보다 특정 bucket에 숨어 있다.

| audit 대상 | 예시 | 왜 늦게 드러나는가 |
|---|---|---|
| `STRICT_SENTINEL` | write 직후 상세 조회, 상태판단 화면, expected-version read | 트래픽이 적고 correctness 민감도가 높다 |
| `TAIL_SENTINEL` | legacy cursor, non-default sort, large page size, global scope | canary 초반에는 coverage가 낮다 |
| hotspot / historically bad bucket | 과거 mismatch, fallback spike, shard skew가 있었던 bucket | 한 번 고쳤다고 바로 정상화됐다고 보기 어렵다 |
| background-cycle bucket | 정산/집계/refresh/compaction 직후 조회 | business cycle 경계에서만 차이가 난다 |
| cross-screen path | write 후 다른 화면에서 읽는 경로 | 한 화면만 보면 read-your-writes regression이 숨는다 |

안전한 기본 규칙은 다음과 비슷하다.

- top volume bucket만 녹색이어도 `STRICT_SENTINEL`이 남아 있으면 exit 불가
- historically bad bucket은 rollback window 동안 최소 1회 이상 강제 audit
- cursor/list endpoint는 `page1 -> page2` chain과 verdict drift를 다시 확인
- 새 mismatch가 `cluster`로 모이면 비율이 낮아도 exit 보류

즉 latent bug sweep는 "전체 rate가 괜찮다"보다 "남겨 둔 위험 bucket이 모두 닫혔다"를 증명하는 절차다.

### 5. rollback command는 존재가 아니라 실행 가능성을 검증해야 한다

runbook에 명령이 적혀 있다는 것과 실제 rollback이 가능한 것은 다르다.  
window를 닫기 전에 최소한 다음이 green이어야 한다.

| 확인 항목 | green 예시 | 실패 예시 |
|---|---|---|
| command target | old/new routing target, feature flag, alias가 현재 topology와 일치 | 이미 삭제된 alias, 이름만 남은 switch |
| auth / permission | operator 권한과 secret이 유효 | 만료된 토큰, role drift |
| old projection health | old index/table이 warm 상태, lag와 오류율이 허용 범위 안 | cold shard, disabled consumer, stale replica |
| cursor / fallback contract | old path로 되돌아가도 cursor/version/fallback 정책이 설명 가능 | old cursor decode 불가, cache namespace drift |
| rollback RTO | rehearsal 기준 복귀 시간 예산 이내 | 되돌릴 수는 있지만 너무 오래 걸림 |

실무적으로는 세 번의 검증이 유용하다.

1. primary 진입 직후: rollback rehearsal green
2. window 중간: 실제 traffic pulse나 batch 하나 지난 뒤 다시 확인
3. window 종료 직전: 마지막 15~30분 안에 final verification

어제 성공한 명령은 오늘의 exit 근거가 아니다.  
final verification이 오래된 상태라면 old projection 제거를 미루는 편이 맞다.

### 6. decommission 승인 표를 고정하면 종료 판단이 흔들리지 않는다

| Gate | 통과 기준 예시 | 보류 / 실패 예시 |
|---|---|---|
| Business-cycle coverage | 정상/피크/배치 중 최소 1개 cycle 통과 | 한가한 시간대만 지나고 종료 시도 |
| Audit cadence completion | planned audit slot 100% 수행, blind spot 허용치 이하 | metric 누락, compare pipeline 중단, skipped audit |
| Latent-bug sweep | strict, tail, hotspot bucket 전부 재검증 green | 특정 strict screen 미관측, new mismatch cluster 발생 |
| Steady-state recovery | fallback/lag/latency가 steady-state budget 안으로 복귀 | primary 이후 fallback이 계속 높음 |
| Rollback command verification | final rehearsal green, old projection warm, RTO green | command 실패, old path cold, switch 권한 불명 |
| Incident status | open correctness incident 0, owner sign-off 기록 | 조사 중인 correctness issue 존재 |
| Forensic archive | 마지막 watermark, schema/version, dashboard snapshot 저장 | old path 제거 후 비교 근거가 남지 않음 |

이 표에서 핵심은 `시간 경과`가 아니라 `증거 경과`다.  
24시간이 지나도 strict audit bucket이 비어 있으면 window를 연장하는 편이 맞다.

### 7. 종료 packet을 남기면 decommission 후에도 의사결정 근거가 남는다

```java
public record RollbackWindowExitObservation(
    Duration windowElapsed,
    boolean businessCycleCovered,
    int plannedAuditSlots,
    int completedAuditSlots,
    int pendingHighRiskBuckets,
    int openCorrectnessIncidents,
    boolean rollbackCommandGreen,
    boolean oldProjectionWarm,
    Duration rollbackRto,
    Duration rollbackRtoBudget,
    boolean archiveCaptured
) {
    public boolean canDecommission() {
        return businessCycleCovered
            && plannedAuditSlots > 0
            && completedAuditSlots >= plannedAuditSlots
            && pendingHighRiskBuckets == 0
            && openCorrectnessIncidents == 0
            && rollbackCommandGreen
            && oldProjectionWarm
            && rollbackRto.compareTo(rollbackRtoBudget) <= 0
            && archiveCaptured;
    }
}
```

핵심은 `windowElapsed`가 있어도 그 값 하나만으로는 `canDecommission()`가 `true`가 되지 않는다는 점이다.

### 8. low-QPS 서비스는 기준을 낮추기보다 window를 늘려야 한다

트래픽이 적다고 해서 strict audit나 rollback verification을 빼면, 사실상 가장 위험한 시점에 증거 없이 종료하게 된다.

보통 더 안전한 선택은 다음이다.

- audit slot 수는 유지하고 window 시간을 늘림
- sampled dual-read 또는 forced audit bucket 비율을 올림
- business cycle을 하루 더 기다림

즉 low-QPS 환경의 기본 대응은 `less evidence`가 아니라 `more time for the same evidence`다.

---

## 실전 시나리오

### 시나리오 1: 검색 projection을 primary로 올렸지만 old index 제거를 미루는 경우

상위 query는 모두 녹색인데 legacy cursor + non-default sort bucket에서 `REISSUE -> REJECT` drift가 business-cycle audit 때만 보인다고 하자.

- primary 승격은 유지 가능
- old index 제거는 보류
- high-risk bucket을 다시 샘플링하고 cursor contract를 수정한 뒤 재승인

즉 primary 성공이 곧 decommission 성공은 아니다.

### 시나리오 2: 주문 상세 strict path는 트래픽이 적어 window를 연장하는 경우

strict screen sample이 적어 latent-bug sweep가 덜 찼다면, sample floor를 낮추기보다 window를 더 유지하는 편이 안전하다.

- rollback command는 계속 검증 상태 유지
- write-after-read bucket을 강제 observe
- strict sample floor 충족 후에만 old projection 제거

### 시나리오 3: 모든 지표는 녹색인데 rollback command가 마지막에 실패하는 경우

fallback, lag, mismatch가 모두 정상이어도 final rollback verification이 red면 old projection을 제거하면 안 된다.

- switch alias drift
- 권한 만료
- old shard cold start

이 세 가지는 모두 "평상시엔 안 보이다가 정말 되돌릴 때만 터지는" 종류라서, 마지막 검증이 특히 중요하다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 시간 기반으로만 window 종료 | 운영이 단순하다 | latent bug와 rollback 불능을 놓치기 쉽다 | 사용자 영향이 매우 작고 되돌리기 비용이 극히 낮을 때만 |
| audit cadence + latent sweep + rollback verification으로 종료 | old path 제거 판단이 선명하다 | 계측, 운영 수고, 저장 비용이 든다 | 대부분의 사용자 영향 projection cutover |
| old projection을 과하게 오래 유지 | forensic과 rollback이 쉽다 | 비용과 복잡도가 계속 남는다 | correctness 불확실성이 큰 초기 전환 |

판단 기준은 다음과 같다.

- primary 승격과 decommission 승인을 분리한다
- average green보다 high-risk bucket closure를 우선 본다
- rollback command는 종료 직전에 다시 검증한다
- low-QPS라고 해서 audit 종류를 빼지 않는다

---

## 꼬리질문

> Q: 24시간 rollback window를 채웠으면 자동으로 old projection을 지워도 되나요?
> 의도: 시간 기반 종료와 증거 기반 종료를 구분하는지 본다.
> 핵심: 아니다. business-cycle coverage, latent-bug audit, final rollback verification이 모두 green이어야 한다.

> Q: 오전에 rollback rehearsal이 성공했는데 저녁에 old path를 지울 때 다시 확인해야 하나요?
> 의도: stale verification의 위험을 보는 질문이다.
> 핵심: 그렇다. window 종료 직전 verification이 더 중요하다.

> Q: 전체 mismatch rate가 낮으면 tail sentinel audit은 생략해도 되나요?
> 의도: 평균 지표와 bucket closure를 구분하는지 본다.
> 핵심: 아니다. latent bug는 대개 tail bucket이나 strict path에 숨어 있다.

> Q: 저QPS 서비스라 샘플이 잘 안 모이면 기준을 낮춰도 되나요?
> 의도: evidence floor와 dwell trade-off를 보는지 본다.
> 핵심: 보통은 기준을 낮추기보다 window를 늘리고 forced audit를 추가하는 편이 낫다.

## 한 줄 정리

Rollback window exit criteria는 old projection 제거를 타이머 기반 정리가 아니라 audit cadence, latent-bug sweep, rollback command verification이 모두 녹색인 별도 종료 승인으로 다루게 한다.
