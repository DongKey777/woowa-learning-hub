---
schema_version: 3
title: Active Hold Table Split Pattern
concept_id: database/active-hold-table-split-pattern
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids:
- missions/roomescape
review_feedback_tags:
- active-hold-table
- reservation-hold
- soft-delete-drift
- capacity-arbitration
aliases:
- active hold table split pattern
- live hold archive split
- hold history table
- active hold row presence
- reservation hold archive
- active table uniqueness
- live row arbitration
- deleted_at blocking truth
- active hold 분리
- 예약 hold active history 분리
symptoms:
- 만료된 hold가 deleted_at이나 archive batch 지연 때문에 계속 좌석이나 slot을 막는다
- UI는 expires_at 기준으로 비었다고 보이는데 write path는 soft delete predicate 때문에 실패한다
- active set은 작고 history는 긴데 한 테이블에 섞여 active index와 cleanup predicate가 비대해진다
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- database/hold-expiration-predicate-drift
- database/soft-delete-uniqueness-indexing-lifecycle
- database/exclusion-constraint-overlap-case-studies
next_docs:
- database/expired-unreleased-drift-runbook
- database/slotization-migration-backfill-playbook
- database/online-backfill-verification-cutover-gates
linked_paths:
- contents/database/hold-expiration-predicate-drift.md
- contents/database/expired-unreleased-drift-runbook.md
- contents/database/soft-delete-uniqueness-indexing-lifecycle.md
- contents/database/exclusion-constraint-overlap-case-studies.md
- contents/database/slotization-migration-backfill-playbook.md
- contents/database/online-backfill-verification-cutover-gates.md
confusable_with:
- database/hold-expiration-predicate-drift
- database/soft-delete-uniqueness-indexing-lifecycle
- database/active-predicate-alignment-capacity-guards
- database/active-predicate-drift-reservation-arbitration
forbidden_neighbors: []
expected_queries:
- active hold table과 hold history table을 분리해 deleted_at이 blocking truth가 되지 않게 하는 기준은 뭐야?
- 예약 hold가 만료됐는데 archive나 soft delete 지연 때문에 계속 막는 문제를 active row presence로 어떻게 풀어?
- expires_at, released_at, deleted_at을 한 테이블에 섞으면 active membership drift가 생기는 이유가 뭐야?
- hold_active에서 row가 사라지는 것을 release truth로 보고 history는 audit으로만 쓰는 설계를 설명해줘
- reservation hold split migration에서 live truth 전환과 history backfill은 어떤 순서로 해야 해?
contextual_chunk_prefix: |
  이 문서는 Active Hold Table Split Pattern deep dive로, expirable reservation hold에서
  active relation row presence를 blocking truth로 삼고 released/expired/canceled rows를 history로 이동해
  deleted_at, archive lag, cleanup truth가 live arbitration을 오염시키지 않게 하는 설계를 설명한다.
---
# Active Hold Table Split Pattern

> 한 줄 요약: hold가 자원을 막는 truth를 `deleted_at`에 매달지 말고, 지금 blocking 중인 row만 `active_hold`에 남기고 종료된 hold는 `history`로 옮겨 active membership를 row 존재 여부로 고정하는 패턴이다.

**난이도: 🔴 Advanced**

관련 문서:

- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Expired-Unreleased Drift Runbook](./expired-unreleased-drift-runbook.md)
- [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
- [Exclusion Constraint Case Studies for Overlap and Range Invariants](./exclusion-constraint-overlap-case-studies.md)
- [Slotization Migration and Backfill Playbook](./slotization-migration-backfill-playbook.md)
- [Online Backfill Verification, Drift Checks, and Cutover Gates](./online-backfill-verification-cutover-gates.md)

retrieval-anchor-keywords: active hold table split pattern, live hold archive split, hold history table, deleted_at blocking truth, active hold row presence, hold lifecycle separation, released_at vs deleted_at, reservation hold archive, active table uniqueness, hold archive migration, live row arbitration

## 핵심 개념

single-table hold lifecycle은 보통 아래 세 요구를 한 row에 몰아넣는다.

- 지금 이 row가 새 예약/점유를 막는가
- 만료/취소/확정 이후 audit trail을 얼마나 오래 보관할 것인가
- cleanup worker가 언제 purge나 archive를 끝낼 것인가

문제는 이 세 질문의 답이 보통 같은 시각에 바뀌지 않는다는 점이다.

- 비즈니스적으로는 이미 hold가 끝났는데
- `deleted_at`이 늦게 찍혀서 unique/exclusion이 계속 막거나
- 반대로 화면은 `expires_at`만 보고 비었다고 보여주는데 write는 계속 실패한다

이 패턴의 핵심은 간단하다.

1. **active table에는 지금 blocking truth인 row만 둔다.**
2. **종료된 hold는 history/archive table로 이동한다.**
3. **`deleted_at`은 history 보관 metadata일 뿐, active membership를 정의하지 않는다.**

즉 "현재 막고 있느냐"는 `deleted_at IS NULL`이 아니라 **active relation에 row가 남아 있느냐**로 판단한다.

## 깊이 들어가기

### 1. 언제 split을 고려해야 하나

아래 신호가 반복되면 `released_at`만 추가하는 single-table 설계보다 active/history split이 더 단순해질 가능성이 높다.

| 신호 | 왜 split이 유리한가 | 흔한 증상 |
|---|---|---|
| `deleted_at`이나 `archived_at`이 blocking predicate에 들어간다 | active truth와 archive truth를 구조적으로 분리할 수 있다 | "만료됐는데 여전히 못 잡는다" |
| active set은 작고 history는 매우 길게 보관한다 | hot index와 cold retention을 분리해 active path를 가볍게 유지한다 | active query가 tombstone과 history bloat에 끌려간다 |
| expiry worker backlog가 길어 active predicate drift가 운영 문제로 보인다 | row 이동 자체가 release가 되므로 cleanup lag가 arbitration truth를 오염시키지 않는다 | expired-but-still-blocking row 누적 |
| restore/audit 요구 때문에 hard delete를 못 하지만 live uniqueness는 엄격해야 한다 | history는 보존하고 active uniqueness는 단순 key/exclusion으로 유지할 수 있다 | generated column, partial index, soft delete scope가 계속 복잡해진다 |
| hold 종료 이벤트가 많고 상태 전이가 길다 | open state와 terminal state를 다른 relation으로 나눠 운영 지표를 분리할 수 있다 | `HELD/EXPIRED/CANCELED/CONFIRMED/ARCHIVED`가 한 테이블에서 뒤엉킨다 |

반대로 아래라면 split이 과할 수 있다.

- hold volume이 작고 retention도 짧다
- expiry와 release가 동기적으로 처리되어 cleanup lag가 거의 없다
- `released_at` 하나만으로 reads/constraints/workers를 충분히 맞출 수 있다

핵심 판단 기준은 "컬럼 하나를 더 넣으면 해결되는가"가 아니라 **active membership를 row presence로 바꾸는 편이 더 안전한가**다.

### 2. split 이후 lifecycle contract는 더 엄격해야 한다

active/history split은 단순 보관 분리가 아니라 lifecycle contract 재정의다.

- `hold_active`
  - 오직 지금 새 write를 막을 수 있는 row만 존재
  - active uniqueness / exclusion / guard row 대상은 이 테이블만 본다
- `hold_history`
  - `EXPIRED`, `CANCELED`, `RELEASED` 같은 terminal row만 존재
  - 감사 추적, 운영 분석, 사후 재현은 여기서 한다

중요한 예외도 있다.

- `CONFIRMED`가 여전히 이후 예약을 막는 도메인이라면 `history`가 아니라 별도 active relation에 있어야 한다
- 예를 들어 좌석 예약이면 `booking_active`나 canonical allocation table이 blocking truth를 이어받아야 한다

즉 split의 기준은 "오래된 row"가 아니라 **"지금도 막는 row인가"**다.

### 3. `deleted_at`을 active table에서 지우면 오해가 줄어든다

가능하면 active hold table에는 `deleted_at` 자체를 두지 않는 편이 낫다.

- active table은 row가 있으면 active, 없으면 inactive라는 뜻이 명확해진다
- 개발자가 무심코 `deleted_at IS NULL`을 active scope로 재사용할 여지가 줄어든다
- hot path 인덱스가 terminal lifecycle 컬럼에 끌려가지 않는다

history table에는 오히려 metadata를 충분히 두는 편이 좋다.

- `released_at`
- `final_state`
- `release_reason`
- `archived_at`
- `source_transition` (`expiry_worker`, `cancel_api`, `payment_timeout`, `manual_release`)

이렇게 해야 active truth는 단순해지고, audit truth는 history에서 풍부해진다.

### 4. 전이는 "active에서 지우고 history에 넣는" 하나의 원자 동작이어야 한다

이 패턴이 안전하려면 release/expire/cancel 전이가 idempotent하고 fenced되어야 한다.

가장 흔한 형태는 다음 둘 중 하나다.

1. 같은 트랜잭션 안에서 `DELETE ... RETURNING` 후 history insert
2. active row를 terminal status로 먼저 바꾸지 않고, move 자체를 canonical transition으로 사용

중요한 점:

- active row를 terminal status로 오래 남겨 두면 다시 single-table drift가 돌아온다
- worker가 느리더라도 "release truth"는 move 시점에 결정돼야 한다
- retry가 생겨도 같은 hold가 active와 history 양쪽에 동시에 살아 있지 않게 해야 한다

### 5. split 패턴이 특히 맞는 도메인

아래 도메인에서는 split이 설명력을 크게 높인다.

- 짧은 TTL hold + 긴 감사 보관
  - 공연/항공/숙소 예약처럼 hold는 수분 단위지만 보관은 수개월 이상
- overlap arbitration이 중요한 예약
  - interval overlap, exclusion constraint, slot claim으로 blocking truth를 엄격히 다뤄야 함
- soft delete backlog가 잦은 시스템
  - 야간 archive나 batch purge가 밀려도 live arbitration은 흔들리면 안 됨
- 다단계 상태 전이가 많은 결제/예약 흐름
  - `HELD -> CONFIRMING -> CONFIRMED/EXPIRED/CANCELED` 전이가 길어 terminal row 보관 요구가 큼

반대로 단순 CRUD성 draft 데이터처럼 "지금 막고 있느냐"가 핵심이 아니면 split보다 single table이 낫다.

### 6. migration은 live truth 전환이 먼저고 history 풍부화는 그다음이다

single-table에서 split으로 갈 때 흔한 실수는 history backfill부터 크게 시작하는 것이다.  
더 안전한 순서는 live truth 전환을 먼저 고정하는 것이다.

1. `hold_history`를 추가한다
2. 새 terminal transition부터 active -> history move를 이중 기록한다
3. availability / uniqueness / overlap probe를 active table만 보게 바꾼다
4. 오래된 terminal row를 watermark 기반으로 backfill한다
5. 마지막에 기존 `deleted_at` 기반 predicate와 인덱스를 제거한다

즉 cutover의 본질은 "history를 다 채웠는가"보다 **새 write가 어느 relation을 truth로 보느냐**다.

## 실전 시나리오

### 시나리오 1. 만료 hold가 야간 archive 전까지 좌석을 계속 막는다

현재 상태:

- `reservation_hold` 한 테이블에 `status`, `expires_at`, `deleted_at`이 함께 있다
- UI는 `expires_at > now()`로 빈 좌석을 보여준다
- unique/exclusion은 `deleted_at IS NULL` row를 계속 본다
- archive batch는 야간에만 돈다

이 경우 split 신호는 명확하다.

- blocking truth가 `deleted_at`에 매달려 있다
- active row보다 ended row가 훨씬 많다
- cleanup backlog가 곧 예약 실패율로 번진다

`reservation_hold_active`와 `reservation_hold_history`로 나누면, 좌석을 막는 truth는 active table row 존재로 단순해진다.

### 시나리오 2. 확정 booking과 만료 hold를 같은 테이블에 섞어 둬 인덱스가 비대해진다

현재 상태:

- `HELD`, `CONFIRMED`, `EXPIRED`, `CANCELED`가 한 테이블에 모두 쌓인다
- overlap probe는 active subset만 필요하지만 history volume 때문에 통계와 index fanout이 나빠진다

이 경우 split 이후 구조는 보통 셋으로 분리된다.

- `hold_active`: 아직 결제/확정 전인 live hold
- `booking_active`: 이미 확정되어 계속 자원을 막는 allocation
- `hold_history`: 더 이상 blocking truth가 아닌 종료 이력

중요한 점은 `CONFIRMED`를 history로 보내지 않는다는 것이다.  
지금도 자원을 막는 상태라면 이름이 hold가 아니더라도 active arbitration relation에 남아 있어야 한다.

### 시나리오 3. soft delete 복구 요구는 있지만 live uniqueness는 단순해야 한다

감사팀은 취소된 hold를 오래 보관하길 원하지만, 운영팀은 "현재 active hold는 seat당 하나"라는 규칙을 단순하게 강제하고 싶어 한다.

이때 split은 양쪽 요구를 분리한다.

- history는 오래 보관하고 필요하면 `deleted_at`이나 `archived_at`을 둔다
- live uniqueness는 active table의 key/exclusion만 본다
- restore는 history에서 active로 재삽입하는 상태 전이로 다룬다

즉 복구 가능성과 live arbitration을 서로 다른 relation으로 분리한다.

## 코드로 보기

```sql
CREATE TABLE reservation_hold_active (
  hold_id BIGINT PRIMARY KEY,
  resource_id BIGINT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reservation_hold_history (
  hold_id BIGINT PRIMARY KEY,
  resource_id BIGINT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  final_state TEXT NOT NULL,
  released_at TIMESTAMPTZ NOT NULL,
  archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  release_reason TEXT NOT NULL,
  source_transition TEXT NOT NULL
);
```

```sql
-- 예시: 만료/취소 시 active membership를 같은 트랜잭션에서 제거
WITH moved AS (
  DELETE FROM reservation_hold_active
  WHERE hold_id = :hold_id
    AND version = :version
  RETURNING hold_id, resource_id, starts_at, ends_at, expires_at, now() AS released_at
)
INSERT INTO reservation_hold_history (
  hold_id,
  resource_id,
  starts_at,
  ends_at,
  expires_at,
  final_state,
  released_at,
  release_reason,
  source_transition
)
SELECT hold_id,
       resource_id,
       starts_at,
       ends_at,
       expires_at,
       'EXPIRED',
       released_at,
       'ttl_elapsed',
       'expiry_worker'
FROM moved;
```

```sql
-- availability / conflict probe는 active table만 본다
SELECT 1
FROM reservation_hold_active
WHERE resource_id = :resource_id
  AND starts_at < :requested_end
  AND ends_at > :requested_start
FOR UPDATE;
```

위 예시의 핵심은 history table이 아니라 active table이 arbitration truth라는 점이다.  
`deleted_at`이 없어도 "지금 막고 있는가"를 판단할 수 있어야 split 패턴이 성공한다.

## 운영 guardrail 체크리스트

- active table row 수와 history row 수를 분리 모니터링한다
- `expires_at <= now()`인데 아직 active table에 남아 있는 row 수를 본다
- 같은 `hold_id`가 active와 history 양쪽에 동시에 존재하지 않도록 uniqueness/검증 쿼리를 둔다
- history 이동 실패율과 retry backlog를 별도로 본다
- active uniqueness / exclusion / slot claim이 history table을 절대 참조하지 않게 리뷰 규칙을 둔다
- restore는 history row의 `deleted_at` 복구가 아니라 active table 재삽입 전이로 취급한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| single table + `deleted_at` | 구현이 가장 빠르다 | cleanup lag가 blocking truth를 오염시키기 쉽다 | low-stakes 내부 도구 |
| single table + `released_at` | split 없이도 predicate drift를 줄일 수 있다 | history bloat와 hot/cold 혼재는 남는다 | hold volume은 크지 않지만 active truth 분리가 필요한 경우 |
| active hold / history split | blocking truth가 row presence로 단순해진다 | 이관 전이와 복구 절차를 설계해야 한다 | live arbitration이 중요하고 retention이 긴 경우 |
| active hold + active booking + history 분리 | hold와 confirmed allocation을 더 명확히 나눈다 | relation 수와 cutover 복잡도가 커진다 | 예약/결제 lifecycle이 길고 상태가 많은 경우 |

## 꼬리질문

> Q: 왜 `deleted_at`이 찍히기 전까지 hold를 막게 두면 안 되나요?
> 의도: archive truth와 blocking truth를 분리하는지 확인
> 핵심: `deleted_at`은 cleanup 완료 시각일 뿐이고, backlog가 생기면 그 지연이 곧 availability 오류로 번지기 때문이다

> Q: `CONFIRMED`도 같은 자원을 계속 막는다면 history table로 옮기면 되나요?
> 의도: split 기준이 "오래됐는가"가 아니라 "지금도 막는가"인지 확인
> 핵심: 아니다. 계속 blocking 중이면 booking_active 같은 active relation에 남아 있어야 한다

> Q: split 도입 전 어떤 지표를 먼저 봐야 하나요?
> 의도: 구조 변경 전에 운영 신호를 읽는지 확인
> 핵심: expired-but-active 수, cleanup lag, active/history row 비율, `deleted_at` 기반 conflict 비율을 먼저 본다

## 한 줄 정리

active hold table split의 본질은 history 보관이 아니라 "지금 막는 truth를 live relation의 row 존재로 고정해 `deleted_at`이 arbitration 규칙을 정의하지 못하게 만드는 것"이다.
