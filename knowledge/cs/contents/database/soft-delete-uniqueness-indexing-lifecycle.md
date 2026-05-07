---
schema_version: 3
title: Soft Delete, Uniqueness, and Data Lifecycle Design
concept_id: database/soft-delete-uniqueness-indexing-lifecycle
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- soft-delete
- uniqueness
- lifecycle
- indexing
- tombstone
aliases:
- soft delete
- deleted_at
- tombstone lifecycle
- unique constraint with soft delete
- partial unique index
- restore conflict
- purge archive strategy
- active row index
- released_at vs deleted_at
- live archive split
symptoms:
- soft delete 후 같은 email이나 business key를 다시 허용하려면 active row 기준 uniqueness를 설계해야 해
- deleted row가 모든 read path와 JOIN, 통계, histogram을 오염시키는 문제를 설명해야 해
- restore가 단순 deleted_at null 복원이 아니라 uniqueness와 reference 검증이 필요한 상태 전이라는 점을 놓치고 있어
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- database/active-hold-table-split-pattern
- database/normalization-denormalization-tradeoffs
next_docs:
- database/hold-expiration-predicate-drift
- database/foreign-key-cascade-lock-surprises
- database/online-backfill-consistency
linked_paths:
- contents/database/hold-expiration-predicate-drift.md
- contents/database/active-hold-table-split-pattern.md
- contents/database/foreign-key-cascade-lock-surprises.md
- contents/database/normalization-denormalization-tradeoffs.md
- contents/database/online-schema-change-strategies.md
- contents/database/online-backfill-consistency.md
confusable_with:
- database/active-hold-table-split-pattern
- database/hold-expiration-predicate-drift
- database/foreign-key-cascade-lock-surprises
forbidden_neighbors: []
expected_queries:
- soft delete를 쓰면 uniqueness, active row index, restore conflict를 어떻게 설계해야 해?
- PostgreSQL partial unique index와 MySQL generated column으로 deleted_at IS NULL 기준 uniqueness를 표현하는 차이는?
- soft delete row가 read path, join condition, statistics, histogram을 계속 오염시키는 이유가 뭐야?
- restore는 왜 플래그 복구가 아니라 현재 active row와 충돌 검증이 필요한 상태 전이야?
- soft delete lifecycle에서 archive, hard delete, active/history split을 언제 고려해야 해?
contextual_chunk_prefix: |
  이 문서는 soft delete를 deleted_at, active row uniqueness, partial unique index, restore conflict, purge/archive lifecycle 관점으로 설명하는 advanced deep dive다.
  unique constraint with soft delete, tombstone lifecycle, live archive split, active row index 질문이 본 문서에 매핑된다.
---
# Soft Delete, Uniqueness, and Data Lifecycle Design

> 한 줄 요약: soft delete는 복구 가능성을 사는 대신, uniqueness·조회 조건·보관 정책을 계속 지불하는 설계다.

**난이도: 🔴 Advanced**

관련 문서:

- [Hold Expiration Predicate Drift](./hold-expiration-predicate-drift.md)
- [Active Hold Table Split Pattern](./active-hold-table-split-pattern.md)
- [Foreign Key Cascade Lock Surprises](./foreign-key-cascade-lock-surprises.md)
- [정규화와 반정규화 트레이드오프](./normalization-denormalization-tradeoffs.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)

retrieval-anchor-keywords: soft delete, deleted_at, tombstone lifecycle, unique constraint with soft delete, partial unique index, restore conflict, purge archive strategy, active row index, hold expiration drift, released_at vs deleted_at, cleanup lag predicate, active hold split, live archive split

## 핵심 개념

soft delete는 row를 물리적으로 지우지 않고, `deleted_at`이나 `is_deleted` 같은 컬럼으로 비활성 상태를 표시하는 방식이다.

장점은 분명하다.

- 실수 복구가 쉽다
- 감사 추적에 유리하다
- 참조 무결성을 바로 끊지 않아도 된다

하지만 운영 비용도 명확하다.

- 모든 조회에 "active row만 본다"는 조건이 붙는다
- unique constraint가 예상대로 동작하지 않을 수 있다
- tombstone이 쌓이면 인덱스와 통계가 오염된다
- 복구 시점에 기존 active row와 충돌할 수 있다

그래서 soft delete는 단순한 삭제 방식이 아니라 **데이터 lifecycle 설계**로 다뤄야 한다.

## 깊이 들어가기

### 1. 가장 큰 함정은 uniqueness다

예를 들어 `users(email)`이 unique인데 기존 사용자를 soft delete 했다고 해보자.

- 물리 삭제가 아니므로 old row는 여전히 남아 있다
- 같은 email로 새 가입을 허용하려면 active row 기준 uniqueness가 필요하다

이때 전략은 엔진별로 다르다.

- PostgreSQL
  - partial unique index: `WHERE deleted_at IS NULL`
- MySQL
  - generated column으로 active key를 따로 만들거나
  - `(email, deleted_at)` 조합을 재설계하거나
  - 별도 active table / archive table로 분리

핵심은 "삭제된 row는 uniqueness 판단에서 제외한다"는 규칙을 **명시적 구조**로 표현해야 한다는 점이다.

### 2. soft delete는 모든 read path를 오염시킨다

soft delete를 도입하면 모든 쿼리는 사실상 다음 질문을 품는다.

- active row만 보나?
- 관리자 화면은 deleted row도 보나?
- join 대상에 삭제된 row를 포함하나?

문제는 일부 쿼리에서 이 조건을 빼먹는 순간, 복구된 것처럼 보이거나 통계가 틀어지거나 보안 이슈가 생길 수 있다는 점이다.

그래서 실무에서는:

- repository 계층에서 active scope를 기본값으로 강제하거나
- view / generated column / ORM global filter를 두거나
- 아예 active table과 archive table을 분리하는 편이 낫다

### 3. restore가 delete보다 더 어렵다

복구는 보통 "플래그만 원복"처럼 보이지만 실제로는 다음과 충돌한다.

- 같은 email로 이미 새 계정이 생성됨
- 참조 대상 일부는 이미 정리됨
- 비즈니스 상태가 현재 규칙과 맞지 않음

즉 restore는 상태 전이로 다뤄야 한다.

- 복구 가능 기간을 둔다
- restore 전에 uniqueness와 참조 무결성을 검증한다
- 필요한 경우 새 식별자로 복구한다

delete가 쉬워 보일수록 restore 정책을 먼저 적어두는 편이 안전하다.

### 4. tombstone은 스토리지와 통계를 계속 잡아먹는다

deleted row가 많아지면 다음 문제가 생긴다.

- active row 비율이 낮아져 index 효율이 떨어진다
- count, histogram, cardinality 추정이 어그러진다
- background purge가 늦으면 table bloat가 커진다
- "최근 데이터만 조회" 쿼리도 불필요한 dead row를 훑을 수 있다

그래서 soft delete를 선택했다면 purge/archival 정책이 따라와야 한다.

- N일 후 archive table로 이관
- 법적 보관 종료 후 hard delete
- active index와 history index를 분리

soft delete만 있고 lifecycle이 없으면, 결국 "삭제하지 못하는 시스템"이 된다.

### 5. foreign key와 cascade 설계도 다시 봐야 한다

soft delete를 쓰면 DB `ON DELETE CASCADE`는 잘 맞지 않을 때가 많다.  
부모 row는 남아 있고 자식 row도 함께 비활성화해야 할 수 있기 때문이다.

선택지는 보통 다음과 같다.

- 부모/자식 모두 soft delete 상태 전이
- 부모만 soft delete하고 자식은 active 유지
- active table과 history table을 나눠서 이관

여기서 중요한 것은 "삭제 의미"를 도메인 규칙으로 먼저 정하고, FK는 그 뒤에 맞추는 것이다.

### 6. soft delete는 장기 보관과 운영 테이블을 분리할 때 가장 건강하다

운영 OLTP 경로는 active row 위주로 가볍게 유지하고, 복구/감사 필요 데이터는 archive 경로로 보내는 방식이 가장 관리가 쉽다.

보통 다음 구조가 오래 간다.

1. 운영 테이블은 active row 중심으로 유지
2. 삭제 시 즉시 soft delete 또는 tombstone 기록
3. 비동기 job이 archive/history table로 이관
4. 일정 기간 후 hard delete

이렇게 해야 uniqueness와 조회 성능, 보관 요구를 동시에 관리할 수 있다.

## 실전 시나리오

### 시나리오 1. 탈퇴 회원 email 재가입 허용

회원 탈퇴는 soft delete로 남기고 싶지만, 같은 email 재가입은 허용해야 한다.

실무 선택:

- PostgreSQL이면 active row partial unique index
- MySQL이면 generated column 기반 active email key 또는 archive 분리

핵심은 "deleted row 때문에 재가입이 막히지 않게" 하면서도, audit trail은 보존하는 것이다.

### 시나리오 2. 상품 삭제 후 관리자 복구 요청

이미 같은 slug로 새 상품이 만들어졌다면 단순 restore는 실패해야 한다.

필요한 절차:

- slug uniqueness 재검사
- 참조 데이터 상태 점검
- 복구 대신 clone 또는 새 slug 부여 검토

### 시나리오 3. soft delete만 쌓여 목록 조회가 느려짐

`orders`의 90%가 deleted row라면, active 조회용 인덱스와 통계가 계속 나빠진다.

이때는:

- purge/archival 주기 도입
- active 조건에 맞는 복합 인덱스 재설계
- 긴 history 조회는 분리 테이블로 이동

## 코드로 보기

```sql
-- PostgreSQL 예시
CREATE UNIQUE INDEX ux_users_email_active
ON users (email)
WHERE deleted_at IS NULL;
```

```sql
-- MySQL 예시: active row에만 값이 생기는 generated column
ALTER TABLE users
  ADD COLUMN active_email VARCHAR(255)
    GENERATED ALWAYS AS (
      CASE
        WHEN deleted_at IS NULL THEN email
        ELSE NULL
      END
    ) STORED,
  ADD UNIQUE KEY ux_users_active_email (active_email);
```

```sql
-- active scope를 분명히 하는 조회
SELECT id, email, nickname
FROM users
WHERE deleted_at IS NULL
  AND email = ?;
```

generated column 방식의 핵심은 "active row만 unique index key를 갖게 한다"는 점이다.  
복구 시에는 `deleted_at`을 되돌리기 전에 `active_email` 충돌 가능성을 먼저 점검해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| soft delete only | 복구와 감사가 쉽다 | 조회/uniqueness/purge 비용이 계속 든다 | 단기 보관과 복구 요구가 있을 때 |
| soft delete + archive | 운영 경로를 가볍게 유지한다 | 파이프라인이 늘어난다 | 삭제량이 많고 장기 보관이 필요할 때 |
| immediate hard delete | 구조가 단순하다 | 복구와 감사가 어렵다 | 보관 요구가 거의 없을 때 |
| active/history table 분리 | active uniqueness 관리가 쉽다 | 이관 절차와 join이 복잡해진다 | 대규모 OLTP + 긴 보관 기간 |

## 꼬리질문

> Q: soft delete를 하면 unique email을 어떻게 처리하나요?
> 의도: active row 기준 uniqueness 표현 방식을 아는지 확인
> 핵심: partial unique index나 generated column 같은 구조가 필요하다

> Q: soft delete를 했으면 restore는 항상 가능한가요?
> 의도: 복구를 상태 전이로 이해하는지 확인
> 핵심: restore 시점에는 새 active row와 uniqueness, 참조 무결성 충돌이 생길 수 있다

> Q: soft delete가 성능에 왜 영향을 주나요?
> 의도: tombstone 축적의 비용을 아는지 확인
> 핵심: dead row가 index, 통계, scan 비용을 계속 오염시키기 때문이다

## 한 줄 정리

soft delete는 삭제를 미루는 기술이 아니라, active uniqueness·조회 기본값·archive/purge 정책까지 함께 설계해야 안전한 데이터 lifecycle 전략이다.
