---
schema_version: 3
title: Projection Canary Cohort Selection
concept_id: design-pattern/projection-canary-cohort-selection
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- projection-canary-cohort
- fingerprint-bucket-coverage
- strict-path-cohort
aliases:
- projection canary cohort selection
- projection cutover cohort ladder
- low risk cohort
- representative cohort
- strict path cohort
- strict screen cohort
- query fingerprint bucket selection
- canary routing cohort
- stage cohort matrix
- fingerprint bucket quota
symptoms:
- projection canary를 1%, 10%, 50% 같은 traffic percentage로만 정의해 어떤 endpoint, actor scope, fingerprint bucket을 태웠는지 설명하지 못한다
- low-risk traffic만 serve하고 strict-path와 tail bucket은 observe-only에도 넣지 않아 correctness bug를 늦게 발견한다
- top volume bucket coverage만 보고 non-default sort, large page size, legacy cursor family, hot tenant 같은 risk sentinel을 놓친다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- design-pattern/read-model-cutover-guardrails
- design-pattern/dual-read-pagination-parity-sample-packet-schema
- design-pattern/canary-promotion-thresholds-projection-cutover
next_docs:
- design-pattern/cursor-compatibility-sampling-cutover
- design-pattern/projection-rollback-window-exit-criteria
- design-pattern/fallback-capacity-and-headroom-contracts
linked_paths:
- contents/design-pattern/read-model-cutover-guardrails.md
- contents/design-pattern/canary-promotion-thresholds-projection-cutover.md
- contents/design-pattern/projection-rollback-window-exit-criteria.md
- contents/design-pattern/dual-read-pagination-parity-sample-packet-schema.md
- contents/design-pattern/search-normalization-query-pattern.md
- contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md
- contents/design-pattern/strict-read-fallback-contracts.md
- contents/design-pattern/strict-pagination-fallback-contracts.md
- contents/design-pattern/projection-freshness-slo-pattern.md
- contents/design-pattern/projection-lag-budgeting-pattern.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
confusable_with:
- design-pattern/canary-promotion-thresholds-projection-cutover
- design-pattern/dual-read-pagination-parity-sample-packet-schema
- design-pattern/cursor-compatibility-sampling-cutover
- design-pattern/projection-rollback-window-exit-criteria
forbidden_neighbors: []
expected_queries:
- Projection canary cohort selection은 몇 퍼센트보다 어떤 low-risk, representative, strict-path bucket을 태우는지가 중요한 이유가 뭐야?
- CANARY 1%에서 low-risk cohort만 serve하고 representative와 strict-path를 observe-only로 유지하는 이유가 뭐야?
- query fingerprint bucket coverage는 raw URL이 아니라 canonical packet의 fingerprint_bucket을 base unit으로 삼아야 하는 이유가 뭐야?
- LOW_RISK_SEED, REP_CORE, STRICT_SENTINEL, TAIL_SENTINEL bucket을 stage별로 확장하는 기준은 뭐야?
- canary cohort 확장은 랜덤 추가보다 endpoint, actor scope, tenant tier, page size, cursor family 같은 빠진 축을 채우는 게 안전한 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Projection Canary Cohort Selection playbook으로, projection cutover canary를
  단순 traffic percentage가 아니라 low-risk seed, representative core, strict sentinel,
  tail sentinel cohort와 canonical fingerprint bucket coverage로 구성하고 stage별 serve/observe-only
  surface를 확장하는 방법을 설명한다.
---
# Projection Canary Cohort Selection

> 한 줄 요약: projection cutover canary는 "몇 %"보다 "누구를 태우는가"가 먼저이고, stage마다 low-risk, representative, strict-path cohort를 분리해 고정해야 query-fingerprint bucket coverage와 strict correctness를 함께 지킬 수 있다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Read Model Cutover Guardrails](./read-model-cutover-guardrails.md)
> - [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)
> - [Rollback Window Exit Criteria](./projection-rollback-window-exit-criteria.md)
> - [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)
> - [Search Normalization and Query Pattern](./search-normalization-query-pattern.md)
> - [Session Pinning vs Version-Gated Strict Reads](./session-pinning-vs-version-gated-strict-reads.md)
> - [Strict Read Fallback Contracts](./strict-read-fallback-contracts.md)
> - [Strict Pagination Fallback Contracts](./strict-pagination-fallback-contracts.md)
> - [Projection Freshness SLO Pattern](./projection-freshness-slo-pattern.md)
> - [Projection Lag Budgeting Pattern](./projection-lag-budgeting-pattern.md)
> - [Traffic Shadowing / Progressive Cutover 설계](../system-design/traffic-shadowing-progressive-cutover-design.md)

retrieval-anchor-keywords: projection canary cohort selection, projection cutover cohort ladder, low risk cohort, representative cohort, strict path cohort, strict screen cohort, query fingerprint bucket selection, fingerprint bucket cohort, canary routing cohort, stage cohort matrix, hot shard exclusion, tenant canary slice, actor scoped canary, representative traffic slice, low blast radius cohort, query shape coverage, fingerprint bucket quota, strict read cohort, projection canary sampling, rollback audit bucket, old projection decommission audit

---

## 핵심 개념

projection canary를 `1%`, `10%`, `50%` 같은 비율로만 적어 두면 실제 운영에서 가장 중요한 질문이 비어 있다.

- 어떤 사용자/테넌트/화면을 먼저 태울 것인가
- 어떤 query fingerprint bucket을 stage별로 반드시 포함할 것인가
- strict path는 언제 observe-only에서 serve로 올릴 것인가

이 문서는 [Canary Promotion Thresholds for Projection Cutover](./canary-promotion-thresholds-projection-cutover.md)가 다루는 sample/dwell/rollback 계약보다 한 단계 앞에서, **stage별 cohort를 어떻게 구성할 것인가**를 설명한다.

같은 `10% canary`라도 cohort 설계가 다르면 위험도와 증거 품질이 완전히 달라진다.

### Retrieval Anchors

- `projection canary cohort selection`
- `low risk cohort`
- `representative cohort`
- `strict path cohort`
- `query fingerprint bucket selection`
- `canary routing cohort`
- `stage cohort ladder`
- `fingerprint bucket quota`

---

## 깊이 들어가기

### 1. cohort는 traffic percentage가 아니라 "의미 단위 묶음"이다

canary cohort는 보통 세 축을 같이 본다.

| 축 | 질문 | 왜 필요한가 |
|---|---|---|
| Low-risk | 먼저 태워도 blast radius가 제한적인가 | 첫 serving stage에서 큰 장애 반경을 줄인다 |
| Representative | steady-state 분포를 충분히 닮았는가 | stage 승격 판단이 실트래픽과 멀어지지 않게 한다 |
| Strict-path | read-your-writes, 상태판단, 후속 의사결정 경로를 포함하는가 | correctness bug를 늦게 발견하는 일을 막는다 |

즉 cohort는 단순 랜덤 샘플이 아니라, **위험도와 증거 품질을 함께 설계한 운영 단위**다.

### 2. stage마다 serve cohort와 observe-only cohort를 분리해야 한다

strict path를 너무 늦게 넣으면 correctness bug를 늦게 발견하고, 너무 빨리 전량으로 넣으면 blast radius가 커진다.  
그래서 stage별로 "serve로 태우는 cohort"와 "dual-read나 shadow로만 관찰하는 cohort"를 나누는 편이 안전하다.

| Stage | serve cohort | observe-only cohort | fingerprint bucket rule | 핵심 의도 |
|---|---|---|---|---|
| SHADOW SMOKE | 없음. 사용자 응답은 old path 유지 | low-risk, representative, strict-path를 모두 mirror | top volume bucket + strict sentinel bucket을 먼저 본다 | serving 전 blind spot 제거 |
| CANARY 1% | low-risk cohort만 serve | representative, strict-path는 shadow 또는 sampled dual-read 유지 | default sort / page1 / non-legacy cursor bucket 위주로 top coverage 30~40% 확보 | 첫 사용자 노출 blast radius 제한 |
| CANARY 10% | low-risk + representative core 일부 serve | strict-path는 screen별로 제한적 serve, 나머지는 observe-only | top bucket coverage 60~80% + strict bucket 최소 1개씩 포함 | steady-state와 가까운 분포 확보 |
| CANARY 25~50% | representative cohort를 region/tenant tier까지 확장 | 남은 strict-path edge case만 observe-only 유지 | top bucket 80~95% + tail sentinel + legacy cursor family 포함 | 분포 왜곡 없이 실전 운영 리스크 노출 |
| PRIMARY + ROLLBACK WINDOW | 전량 serve | historically bad bucket, strict-path audit bucket은 강제 verify 유지 | high-risk bucket을 별도 audit queue로 계속 추적 | latent issue를 old path 제거 전에 걸러냄 |

핵심은 stage 승격이 `퍼센트 상승`이 아니라 `cohort surface 확장`이어야 한다는 점이다.

### 3. low-risk cohort는 "안전한데도 실제 경로와 닮은" 집합이어야 한다

low-risk cohort를 내부 직원이나 테스트 계정으로만 잡으면 실제 traffic shape를 거의 못 본다.  
반대로 hot tenant, 대형 page size, 복잡 검색을 초반부터 넣으면 첫 serving stage의 blast radius가 너무 커진다.

보통 low-risk cohort는 다음 특징을 가진다.

| 포함 신호 | 제외 신호 |
|---|---|
| default sort / default page size | large page size, deep page chain |
| page 1 위주의 조회 | legacy cursor decode가 필요한 요청 |
| 최근 write 직후가 아닌 browse read | post-write strict read, 상태판단 화면 |
| 표준 tenant tier, 표준 region | hot shard, burst tenant, 신규 onboarding tenant |
| baseline에서 fallback / mismatch 이력이 적은 bucket | 과거 mismatch hotspot bucket |

좋은 low-risk cohort는 "의미 없는 내부 traffic"이 아니라, **실제 사용자 surface 중에서 복잡도와 blast radius를 낮춘 부분집합**이다.

### 4. representative cohort는 random 10%가 아니라 strata를 채워야 한다

대표성은 단순 무작위 표본보다 **운영 축별 분포 보존**에 더 가깝다.

최소한 아래 축은 따로 본다.

| 분포 축 | 왜 나눠야 하는가 |
|---|---|
| `endpoint_id` | 같은 projection이라도 화면별 query shape가 다르다 |
| `actor_scope` (`self`, `tenant`, `global`) | strictness와 cache/fallback 정책이 달라진다 |
| tenant tier / region | hot shard, 데이터 skew, locale 특성이 다르다 |
| sort family | stable sort / tie-breaker failure가 가족별로 다르다 |
| page size bucket | page boundary와 latency 문제가 크기별로 다르다 |
| cursor policy family | `ACCEPT`, `REISSUE`, `REJECT` 분포가 다르다 |
| recent-write density | read-your-writes 압력이 있는지 없는지 달라진다 |

그래서 representative cohort는 보통 최근 7~14일 observe packet에서 strata를 만들고,

1. 각 축의 top traffic 분포를 계산하고
2. 각 strata에서 대표 bucket을 뽑고
3. 총 coverage가 목표 비율에 도달할 때까지 확장한다

는 식으로 고른다.

즉 `user_id hash % 10 == 0` 같은 무작위 규칙만으로는 representative cohort를 대신하기 어렵다.

### 5. strict-path cohort는 volume이 아니라 correctness 의미 단위로 잡아야 한다

strict path는 보통 다음에 해당한다.

- write 직후 동일 화면 또는 인접 화면 조회
- 주문/결제/재고/상태 전이처럼 잘못 읽으면 후속 판단이 틀어지는 화면
- actor-scoped pinning 또는 expected-version gating이 있는 경로
- fallback이 있어도 stale read를 허용하면 안 되는 경로

strict-path cohort는 `트래픽이 적어서 나중에 보자`가 아니라, **화면 또는 의사결정 단위로 최소 1개 bucket씩 보장**하는 편이 좋다.

예를 들면:

- `주문 상세 x self scope x write-after-read 5분 이내`
- `결제 상태 x tenant scope x expectedVersion strict read`
- `재고 가용성 x global scope x fallback 금지`

strict-path cohort를 stage별로 다루는 안전한 기본값은 다음에 가깝다.

- SHADOW: 모든 strict path를 mirror
- CANARY 1%: strict path는 observe-only 또는 page/screen 단위 sampled serve
- CANARY 10%: screen/action pair별로 최소 1개 strict bucket serve
- CANARY 25~50%: strict path 대부분을 serve로 확장
- PRIMARY: 전량 serve하되 rollback window 동안 strict audit bucket을 따로 유지

이 strict audit bucket과 `TAIL_SENTINEL`이 언제 충분히 닫혔는지는 [Rollback Window Exit Criteria](./projection-rollback-window-exit-criteria.md)처럼 post-primary exit gate에서 별도로 판정하는 편이 안전하다.

### 6. query-fingerprint bucket은 canonical packet을 base unit으로 삼아야 한다

query-fingerprint bucket selection은 raw URL hash를 고르는 일이 아니다.  
우선 [Dual-Read Pagination Parity Sample Packet Schema](./dual-read-pagination-parity-sample-packet-schema.md)의 canonical `fingerprint_bucket`을 base unit으로 고정하는 편이 좋다.

즉 selection의 출발점은 보통 아래 필드를 함께 본다.

- `endpoint_id`
- `actor_scope`
- canonical `fingerprint_bucket`
- `cursor_verdict_pair`
- tenant tier / region
- recent-write flag 또는 strict-path flag

여기서 중요한 점은:

- packet의 canonical `fingerprint_bucket` 정의는 바꾸지 않는다
- cohort selection ledger가 그 위에 actor/tenant/strictness 차원을 덧붙인다

그래야 canary selection, promotion dashboard, rollback audit가 같은 sample identity를 공유한다.

### 7. bucket selection은 top volume + risk sentinel을 같이 가져가야 한다

top query만 보면 edge risk를 놓치고, rare edge case만 보면 steady-state를 놓친다.  
그래서 bucket은 보통 네 부류로 분류해 stage별로 합친다.

| bucket class | 선택 기준 | 어느 stage에서 쓰나 |
|---|---|---|
| `LOW_RISK_SEED` | default sort/page1, low write density, low hotspot, low historical mismatch | CANARY 1% 첫 serving |
| `REP_CORE` | top traffic share를 차지하는 steady-state bucket | CANARY 10% 이후 대표성 확보 |
| `STRICT_SENTINEL` | strict screen, post-write read, decision-critical query | SHADOW부터 관찰, 10% 이후 serve 확대 |
| `TAIL_SENTINEL` | low volume이지만 legacy cursor, non-default sort, large page size, global scope 같은 위험 축 포함 | 25~50% 이후와 rollback window audit |

안전한 기본 규칙은 다음과 비슷하다.

- CANARY 1%: `LOW_RISK_SEED`만 serve
- CANARY 10%: `LOW_RISK_SEED + REP_CORE + strict 진입 대상 STRICT_SENTINEL`
- CANARY 25~50%: `REP_CORE` 대부분 + 남은 `STRICT_SENTINEL` + `TAIL_SENTINEL`
- PRIMARY VERIFY: 전체 bucket serve, historically bad `STRICT_SENTINEL` / `TAIL_SENTINEL`은 강제 audit

### 8. bucket coverage 목표는 "전체 비율"이 아니라 "축별 빈칸이 없는가"를 봐야 한다

대표적인 잘못은 `top 20 bucket = 80% traffic`을 만족했다는 이유로 승격하는 것이다.  
그런데 그 20개가 모두 같은 endpoint, 같은 sort family, 같은 tenant tier일 수 있다.

bucket selection 체크리스트는 보통 이렇게 잡는다.

- 각 serving endpoint마다 최소 1개 `LOW_RISK_SEED`가 있는가
- strict screen/action pair마다 최소 1개 `STRICT_SENTINEL`이 있는가
- non-default sort family가 최소 1개 이상 관찰되었는가
- page size bucket이 `20`, `50`, `100+`처럼 주요 family를 덮는가
- tenant tier / region 분포가 steady-state와 크게 어긋나지 않는가
- historical hotspot bucket이 observe-only로라도 빠지지 않았는가

즉 coverage는 `상위 N개 봤다`가 아니라, **운영상 중요한 축에 빈칸이 없다**로 해석하는 편이 맞다.

### 9. cohort 확장은 "랜덤 추가"보다 "빠진 축 채우기" 우선이 안전하다

다음 stage로 갈 때는 남은 퍼센트를 무작위로 더하는 것보다,

1. 아직 비어 있는 endpoint / actor_scope / tenant tier를 채우고
2. strict-path serve 범위를 늘리고
3. tail sentinel bucket을 편입하는 순서

로 가는 편이 해석이 선명하다.

이렇게 해야 mismatch나 fallback 상승이 생겼을 때 `어떤 새 축을 추가한 뒤에 깨졌는지`를 설명할 수 있다.

---

## 실전 시나리오

### 시나리오 1: 검색 projection 1% canary

검색 목록은 top keyword 몇 개만 보면 대표성이 왜곡되기 쉽다.

- serve cohort는 default sort / page1 / 일반 tenant의 `LOW_RISK_SEED`
- observe-only cohort는 non-default sort, large page size, legacy cursor bucket
- strict-path는 "방금 필터를 저장한 직후 다시 보는 관리자 화면"처럼 post-write screen을 mirror only

즉 1% stage의 목적은 검색 전체를 대표하는 게 아니라, **첫 serving surface의 blast radius를 줄이면서도 canonical bucket 계약을 검증하는 것**이다.

### 시나리오 2: 주문 상세 projection 10% canary

주문 상세는 strict path라서 browse traffic보다 correctness가 먼저다.

- representative cohort에 일반 상세 조회를 넣되
- strict-path cohort에 `주문 생성 직후 상세`, `상태 변경 직후 상세` bucket을 별도로 둔다
- stage 승격 전에는 strict bucket마다 최소 샘플과 fallback green을 확인한다

즉 `10% traffic`보다 `strict screen/action pair가 실제로 들어왔는가`가 더 중요하다.

### 시나리오 3: 25% canary에서 특정 region만 불안정한 경우

top fingerprint coverage는 충분했는데 특정 region tenant에서만 fallback이 튄다고 하자.  
이 경우 해석은 "25%가 커서 실패했다"가 아니라, representative cohort 확장에서 **새로 편입된 region strata**가 문제인 경우가 많다.

cohort ladder가 명시돼 있으면 어느 축을 추가한 뒤 문제가 생겼는지 빠르게 좁힐 수 있다.

---

## 코드로 보기

```java
public enum CohortClass {
    LOW_RISK_SEED,
    REP_CORE,
    STRICT_SENTINEL,
    TAIL_SENTINEL
}

public record FingerprintBucketStat(
    String endpointId,
    String actorScope,
    String fingerprintBucket,
    String tenantTier,
    String cursorVerdictPair,
    double trafficShare,
    double mismatchRate,
    double fallbackRate,
    double postWriteShare,
    boolean strictPath,
    boolean hotspot
) {
    public boolean eligibleLowRiskSeed() {
        return !strictPath
            && !hotspot
            && postWriteShare < 0.05
            && fallbackRate < 0.005
            && mismatchRate < 0.001;
    }
}

public record StageCohortPlan(
    String stage,
    Set<CohortClass> servingClasses,
    int minEndpointCoverage,
    int minStrictBuckets,
    double targetTrafficCoverage
) {}
```

이 코드의 핵심은 "랜덤 사용자 1%"가 아니라 **bucket class와 coverage rule을 먼저 선언한다**는 점이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| user hash 기반 랜덤 canary | 구현이 가장 단순하다 | strict-path 누락과 대표성 왜곡이 잦다 | 내부 전용, 단순 read cutover 정도 |
| low-risk cohort를 명시적으로 분리 | 초기 blast radius가 낮다 | cohort 분류용 계측이 필요하다 | 대부분의 projection serving 전환 |
| representative strata를 단계적으로 채움 | 승격 판단이 steady-state에 가깝다 | 운영 표와 packet rollup이 필요하다 | 검색/목록/멀티테넌트 projection |
| strict-path를 shadow부터 별도 관리 | correctness bug를 일찍 찾는다 | 초기에 표본 수집 시간이 더 걸린다 | 주문/결제/재고/상태판단 경로 |
| top volume bucket만 사용 | 준비가 빠르다 | tail risk, legacy cursor, hot shard를 놓친다 | 거의 권장하지 않음 |

판단 기준은 다음과 같다.

- cohort는 퍼센트가 아니라 의미 단위로 설계한다
- low-risk와 representative는 서로 대체재가 아니다
- strict-path는 volume이 아니라 correctness 중요도로 분리한다
- query-fingerprint bucket은 canonical packet을 base unit으로 재사용한다
- 다음 stage 확장은 랜덤 추가보다 빠진 축 채우기를 우선한다

## 꼬리질문

> Q: 1% canary면 그냥 사용자 해시 1%로 충분하지 않나요?
> 의도: percentage와 cohort를 구분하는지 본다.
> 핵심: 아니다. 해시 1%는 비율일 뿐이고, low-risk / representative / strict-path 축을 보장하지 못한다.

> Q: low-risk cohort를 내부 직원이나 테스트 계정으로만 잡으면 더 안전하지 않나요?
> 의도: low-risk가 실제 경로와 닮아야 한다는 점을 보는 질문.
> 핵심: blast radius는 낮아져도 실제 query shape와 tenant skew를 거의 못 봐서 promotion 근거가 약해진다.

> Q: representative bucket을 많이 넣으면 strict-path bucket은 굳이 따로 안 봐도 되지 않나요?
> 의도: volume 대표성과 correctness 중요도를 분리하는지 본다.
> 핵심: 아니다. strict-path는 트래픽 비중이 낮아도 별도 보장해야 한다.

> Q: query-fingerprint bucket만 고르면 actor scope나 tenant tier는 무시해도 되나요?
> 의도: canonical bucket과 routing strata를 구분하는지 본다.
> 핵심: 아니다. canonical fingerprint bucket은 base unit이고, cohort selection은 actor/tenant/strictness 차원을 추가로 본다.

## 한 줄 정리

Projection canary cohort selection은 stage별 canary를 단순 퍼센트가 아니라 low-risk, representative, strict-path bucket ladder로 바꿔서, 승격 전에 어떤 사용자 surface와 query shape를 실제로 검증했는지 설명 가능하게 만드는 패턴이다.
