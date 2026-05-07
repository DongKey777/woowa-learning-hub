---
schema_version: 3
title: Dual-Write Avoidance / Migration Bridge 설계
concept_id: system-design/dual-write-avoidance-migration-bridge-design
canonical: false
category: system-design
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 76
mission_ids: []
review_feedback_tags:
- dual write avoidance
- migration bridge
- write bridge
- old new system cutover
aliases:
- dual write avoidance
- migration bridge
- write bridge
- old new system cutover
- single source of truth
- change feed projection
- shadow write hazard
- write fence
- bridge outbox
- migration compatibility window
- bridge retirement
- authority transfer
symptoms: []
intents:
- comparison
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/change-data-capture-outbox-relay-design.md
- contents/system-design/zero-downtime-schema-migration-platform-design.md
- contents/system-design/database-security-identity-bridge-cutover-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/historical-backfill-replay-platform-design.md
- contents/system-design/deploy-rollback-safety-compatibility-envelope-design.md
- contents/system-design/cleanup-point-of-no-return-design.md
- contents/database/online-backfill-verification-cutover-gates.md
- contents/database/cdc-gap-repair-reconciliation-playbook.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Dual-Write Avoidance / Migration Bridge 설계 차이를 실무 기준으로 설명해줘
- dual write avoidance를 언제 선택해야 해?
- Dual-Write Avoidance / Migration Bridge 설계 설계 판단 기준이 뭐야?
- dual write avoidance에서 자주 헷갈리는 경계는?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Dual-Write Avoidance / Migration Bridge 설계를 다루는 bridge 문서다. dual-write avoidance와 migration bridge 설계는 old/new 시스템 전환 중 두 개의 source of truth를 동시에 쓰지 않도록 브리지 계층과 change feed를 두고, 읽기 검증과 점진 cutover로 상태 오염을 막는 마이그레이션 운영 설계다. 검색 질의가 dual write avoidance, migration bridge, write bridge, old new system cutover처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Dual-Write Avoidance / Migration Bridge 설계

> 한 줄 요약: dual-write avoidance와 migration bridge 설계는 old/new 시스템 전환 중 두 개의 source of truth를 동시에 쓰지 않도록 브리지 계층과 change feed를 두고, 읽기 검증과 점진 cutover로 상태 오염을 막는 마이그레이션 운영 설계다.

retrieval-anchor-keywords: dual write avoidance, migration bridge, write bridge, old new system cutover, single source of truth, change feed projection, shadow write hazard, write fence, bridge outbox, migration compatibility window, bridge retirement, authority transfer, cleanup gate, database security bridge, online backfill verification, cdc gap repair

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Change Data Capture / Outbox Relay 설계](./change-data-capture-outbox-relay-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
> - [Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 핵심 개념

시스템 migration에서 가장 위험한 유혹 중 하나는 old와 new에 동시에 write하는 것이다.
겉으로는 안전해 보이지만, 실전에서는 다음 문제가 생긴다.

- 한쪽만 성공하고 다른 쪽은 실패
- 두 시스템의 validation rule이 미묘하게 다름
- ordering 차이로 상태 전이가 달라짐
- rollback 시 어느 쪽이 진실인지 헷갈림

그래서 좋은 migration은 "둘 다 write"가 아니라 **하나의 source of truth에 쓰고, 다른 쪽은 브리지와 change feed로 따라가게 만드는 것**에 가깝다.

## 깊이 들어가기

### 1. 왜 dual write가 위험한가

예를 들어 주문 시스템을 old DB에서 new state store로 옮긴다고 하자.

```text
request -> write old DB
       -> write new store
```

이 구조에서 바로 깨지는 지점:

- old commit 성공, new timeout
- new commit 성공, old rollback
- retry 시 한쪽은 dedup, 다른 쪽은 신규 처리
- side effect가 한쪽에서만 발생

즉, dual write는 consistency 문제가 아니라 **진실의 출처가 둘이 되는 문제**다.

### 2. Capacity Estimation

예:

- write QPS 3만
- migration 대상 엔티티 20억 건
- bridge lag 허용 10초
- read cutover 전 dual-read 샘플 2%

이때 봐야 할 숫자:

- bridge emit lag
- projection freshness
- replay catch-up time
- write amplification
- compare mismatch ratio

dual write를 피하더라도 bridge와 projection이 충분히 빨라야 운영이 가능하다.

### 3. 대표 전략

보통 안전한 선택지는 아래 중 하나다.

- old가 source of truth, new는 projection
- new가 source of truth, old는 compatibility facade
- write bridge가 단일 입구가 되고, 내부적으로 한쪽만 진실로 취급

핵심은 언제나 하나다.

- **한 시점에 authoritative writer는 하나여야 한다**

### 4. Migration bridge의 역할

bridge는 단순 adapter가 아니다.
실전에서는 다음을 맡는다.

- write validation normalization
- idempotency key propagation
- outbox / change feed emit
- version stamping
- write fence
- cutover mode switch

즉, bridge는 전환기 동안 old/new 사이의 의미 차이를 흡수하는 제어층이다.

### 5. Read path와 write path를 분리해서 생각한다

많은 migration이 실패하는 이유는 read와 write를 한 번에 바꾸려 하기 때문이다.
권장 순서:

1. write는 기존 source 유지
2. new projection을 따라잡게 한다
3. dual-read verification으로 읽기 결과를 비교한다
4. read cutover를 먼저 한다
5. write authority를 나중에 옮긴다

이렇게 해야 blast radius를 줄일 수 있다.

### 6. Shadow write는 거의 항상 위험하다

read shadow는 비교적 안전하지만, write shadow는 다르다.

위험:

- 외부 webhook / billing / email이 중복 발생
- new path validation 차이로 poison state 생성
- hidden data divergence

필요하다면:

- side effect를 noop 처리
- sink를 sandbox로 분리
- write fence로 candidate commit을 막음

즉, "write도 한번 보내 보자"는 대부분 실수에 가깝다.

### 7. Authority transfer와 rollback

진짜 어려운 순간은 source of truth를 바꾸는 시점이다.

필요한 것:

- explicit authority flag
- write fence token
- cutover timestamp
- rollback boundary
- old/new compatibility window

권한 이관 이후에는 rollback이 급격히 어려워지므로, cleanup은 항상 늦게 한다.

## 실전 시나리오

### 시나리오 1: legacy order DB에서 new projection store로 이전

문제:

- 쓰기는 아직 legacy가 담당하지만, 새 조회 경로를 열고 싶다

해결:

- legacy write + outbox를 유지한다
- new store는 projection으로만 채운다
- dual-read 비교가 안정화된 뒤 read를 전환한다

### 시나리오 2: old billing engine에서 new rating engine으로 전환

문제:

- 두 엔진에 동시에 쓰면 금액 계산 차이와 중복 청구가 위험하다

해결:

- old engine을 authority로 유지한다
- new engine은 shadow rating만 수행한다
- 차이 보고서를 충분히 쌓은 뒤 authority transfer를 계획한다

### 시나리오 3: write authority 이전 후 rollback 필요

문제:

- new store write cutover 후 일부 invariant가 깨진다

해결:

- rollback boundary 이전이면 old authority로 되돌린다
- 이후면 full rollback 대신 correction + replay 경로를 쓴다
- cleanup을 늦게 했기 때문에 최소한의 fallback이 가능하다

## 코드로 보기

```pseudo
function handleWrite(cmd):
  authority = authorityConfig.current()
  if authority == "OLD":
    result = oldSystem.write(cmd)
    outbox.emit(buildChangeEvent(result))
    return result
  else:
    result = newSystem.write(cmd)
    compatibilityFeed.emit(buildLegacyProjection(result))
    return result

function cutoverWrites():
  ensureDualReadHealthy()
  ensureProjectionLagBelowThreshold()
  authorityConfig.switchTo("NEW")
```

```java
public WriteResult write(Command command) {
    if (authoritySelector.isLegacy()) {
        WriteResult result = legacyWriter.write(command);
        bridgeOutbox.publish(result);
        return result;
    }
    return newWriter.write(command);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Direct dual write | 구현이 빨라 보인다 | divergence risk가 크다 | 거의 권장되지 않음 |
| Single writer + projection bridge | 안전하다 | bridge 구축이 필요하다 | 대부분의 migration |
| Read cutover first | blast radius가 작다 | write authority 이동은 나중에 남는다 | 조회 경로 변경이 큰 경우 |
| Write authority early switch | 전환이 빠르다 | rollback이 어려워진다 | 아주 강한 검증 후 |

핵심은 dual-write avoidance가 패턴 하나가 아니라 **source of truth를 하나로 유지하면서 old/new 시스템을 다리로 연결하는 migration 운영 원칙**이라는 점이다.

## 꼬리질문

> Q: dual write를 잘 하면 괜찮지 않나요?
> 의도: 이론적 가능성과 운영 현실 구분 확인
> 핵심: 일부 환경에선 가능하지만, 대부분의 실서비스에서는 validation, ordering, rollback 문제 때문에 운영 리스크가 너무 크다.

> Q: read cutover를 write보다 먼저 하는 이유는?
> 의도: blast radius 축소 전략 이해 확인
> 핵심: read는 비교와 fallback이 상대적으로 쉽지만, write authority는 진실의 출처를 바꾸므로 훨씬 위험하다.

> Q: shadow write가 왜 위험한가요?
> 의도: side effect와 hidden divergence 이해 확인
> 핵심: candidate path가 외부 효과를 만들거나 validation 차이로 오염 상태를 남길 수 있기 때문이다.

> Q: authority transfer 후 rollback이 어려운 이유는?
> 의도: rollback boundary 개념 확인
> 핵심: 새 시스템에만 기록된 진실이 생기면 old path로 단순 복귀할 수 없고 correction / replay가 필요해지기 때문이다.

## 한 줄 정리

Dual-write avoidance / migration bridge 설계는 old/new 시스템 전환 중 source of truth를 하나로 유지하고, 브리지와 change feed로 다른 쪽을 따라가게 만들어 상태 오염과 rollback 혼란을 줄이는 마이그레이션 운영 설계다.
