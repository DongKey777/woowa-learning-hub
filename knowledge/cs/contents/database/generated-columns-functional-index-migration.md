---
schema_version: 3
title: Generated Columns, Functional Indexes, and Query-Safe Migration
concept_id: database/generated-columns-functional-index-migration
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- generated-column-functional-index
- sargable-predicate-migration
- query-safe-rollout
aliases:
- generated column functional index migration
- generated column
- functional index
- expression index
- sargable predicate
- query-safe migration
- lower email index
- derived key index
- online backfill generated column
- 함수 조건 인덱스
symptoms:
- LOWER, DATE, JSON_EXTRACT 같은 함수 조건 때문에 기존 인덱스를 못 타는 쿼리를 안전하게 바꾸고 싶어
- generated column과 functional index 중 운영 가독성, backfill, 배포 순서를 기준으로 선택해야 해
- 새 파생 키 인덱스를 만들기 전후로 old query와 new query가 같이 살아야 하는 migration 순서를 짜야 해
intents:
- troubleshooting
- design
prerequisites:
- database/index-and-explain
- database/query-tuning-checklist
next_docs:
- database/online-schema-change-strategies
- database/online-backfill-consistency
- database/functional-index-vs-lower-duplicate-check-bridge
- system-design/zero-downtime-schema-migration-platform-design
linked_paths:
- contents/database/index-and-explain.md
- contents/database/query-tuning-checklist.md
- contents/database/covering-index-composite-ordering.md
- contents/database/online-schema-change-strategies.md
- contents/database/online-backfill-consistency.md
- contents/database/functional-index-vs-lower-duplicate-check-bridge.md
- contents/system-design/zero-downtime-schema-migration-platform-design.md
confusable_with:
- database/query-tuning-checklist
- database/functional-index-vs-lower-duplicate-check-bridge
- database/online-schema-change-strategies
forbidden_neighbors: []
expected_queries:
- LOWER(email), DATE(created_at), JSON_EXTRACT 조건을 sargable하게 만들려면 generated column과 functional index 중 무엇을 써야 해?
- generated column을 추가하고 읽기 경로를 전환하는 query-safe migration 순서를 알려줘
- expression index는 좋은데 팀 가독성이 떨어질 때 generated column이 더 나은 이유는 뭐야?
- functional index 도입 전 기존 쿼리와 새 인덱스가 같이 살아남게 하려면 어떤 배포 순서가 안전해?
- 파생 키 규칙이 바뀔 수 있으면 generated column backfill과 검증을 어떻게 설계해?
contextual_chunk_prefix: |
  이 문서는 함수가 걸린 non-sargable predicate를 generated column, functional index, expression index, online backfill, query-safe rollout로 전환하는 advanced playbook이다.
  generated column, functional index, expression index, sargable predicate, lower email index 같은 자연어 설계 질문이 본 문서에 매핑된다.
---
# Generated Columns, Functional Indexes, and Query-Safe Migration

> 한 줄 요약: 함수가 걸린 조건을 빠르게 만들고 싶을 때는 "쿼리를 바꾸자"로 끝나지 않고, generated column·functional index·배포 순서를 함께 설계해야 한다.

**난이도: 🔴 Advanced**

관련 문서:

- [인덱스와 실행 계획](./index-and-explain.md)
- [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
- [커버링 인덱스와 복합 인덱스 컬럼 순서](./covering-index-composite-ordering.md)
- [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
- [Online Backfill Consistency와 워터마크 전략](./online-backfill-consistency.md)
- [Zero-Downtime Schema Migration Platform 설계](../system-design/zero-downtime-schema-migration-platform-design.md)

retrieval-anchor-keywords: generated column, functional index, expression index, sargable predicate, query-safe migration, lower email index, derived key index, online backfill

## 핵심 개념

운영 쿼리가 느린데 조건이 다음처럼 생기는 경우가 많다.

- `LOWER(email) = ?`
- `DATE(created_at) = ?`
- `JSON_EXTRACT(payload, '$.status') = 'READY'`
- `phone_normalized = normalize(phone)`

이런 조건은 비즈니스 관점에서는 자연스럽지만, 인덱스 관점에서는 비-sargable 해지기 쉽다.  
즉 컬럼 원본이 아니라 **표현식 결과**에 접근하므로, 일반 인덱스만으로는 효율이 안 난다.

이때 선택지는 보통 세 가지다.

- 쿼리 자체를 sargable 하게 다시 쓴다
- functional/expression index를 만든다
- generated column을 만들어 그 컬럼에 인덱스를 건다

중요한 것은 "어떤 문법이 되느냐"가 아니라, **배포 중 기존 쿼리와 새 인덱스가 함께 살아남는 순서**를 짜는 일이다.

## 깊이 들어가기

### 1. 먼저 쿼리를 바꿀 수 있는지 본다

예를 들어:

- `DATE(created_at) = '2026-04-14'`
- `created_at >= '2026-04-14 00:00:00' AND created_at < '2026-04-15 00:00:00'`

같은 의미라도 후자는 기존 인덱스를 더 잘 탈 수 있다.  
그래서 expression index를 만들기 전에 먼저 확인할 질문은 다음이다.

- 단순 범위 조건으로 바꿀 수 있는가
- normalization을 쓰기 시점에 미리 계산할 수 있는가
- 표현식 계산이 deterministic 한가

functional index는 강력하지만, "쿼리를 바꿔도 되는 문제"에 바로 쓰면 index maintenance만 늘어난다.

### 2. generated column은 파생 키를 명시적으로 저장하는 방법이다

generated column은 원본 컬럼에서 파생된 값을 컬럼 형태로 드러낸다.

예:

- `email_normalized`
- `order_date`
- `tenant_active_key`
- `payload_status`

장점:

- 인덱스 대상이 명확하다
- 애플리케이션 쿼리가 단순해진다
- uniqueness, filtering, ordering 규칙을 재사용하기 쉽다

단점:

- 컬럼 추가와 backfill/online DDL 비용이 든다
- 파생 규칙이 바뀌면 재계산이 필요하다

### 3. functional index는 빠르지만 애플리케이션 가독성이 떨어질 수 있다

PostgreSQL의 expression index나 MySQL의 functional index는 컬럼을 추가하지 않고도 표현식 결과에 인덱스를 걸 수 있다.

장점:

- 스키마 노출이 적다
- 특정 조건을 빠르게 최적화할 수 있다

주의점:

- 쿼리 표현식이 인덱스 정의와 충분히 맞아야 한다
- 함수가 deterministic 하지 않으면 문제가 생긴다
- 팀원이 "왜 이 조건만 인덱스를 타는지" 이해하기 어렵다

즉 functional index는 좋은 도구지만, 운영 팀 지식이 약하면 generated column보다 투명성이 떨어질 수 있다.

### 4. 배포 순서는 "스키마 먼저, 읽기 전환 나중"이 보통 안전하다

새 파생 키를 도입할 때는 다음 순서가 안전하다.

1. generated column 또는 functional index를 추가한다
2. backfill 또는 계산 일관성을 검증한다
3. 기존 쿼리와 새 쿼리를 이중 검증한다
4. 애플리케이션 읽기 경로를 점진 전환한다
5. 필요하면 옛 인덱스를 제거한다

이 순서를 거꾸로 하면, 새 쿼리가 아직 준비되지 않은 replica나 오래된 스키마와 충돌할 수 있다.

### 5. JSON, 문자열 정규화, soft delete active key에서 특히 자주 쓴다

generated column/functional index가 특히 빛나는 경우:

- JSON 필드에서 자주 조회하는 파생 값
- 대소문자 무시 email 검색
- 전화번호/사업자번호 normalized key
- soft delete active uniqueness key
- 날짜 버킷, 상태 파생 값

반대로 값이 자주 바뀌고 표현식 계산이 무거우면 쓰기 비용이 커질 수 있다.

### 6. 파생 키는 비즈니스 규칙이 바뀔 때 가장 위험하다

예를 들어 phone normalization 규칙이 바뀌면:

- 기존 row 재계산이 필요하다
- unique key 충돌이 새로 생길 수 있다
- old/new 규칙이 혼재하면 조회와 쓰기 결과가 갈라질 수 있다

그래서 파생 키는 단순 최적화가 아니라, **규칙 버전 관리 대상**으로 보는 편이 좋다.

## 실전 시나리오

### 시나리오 1. 이메일 대소문자 무시 로그인

`LOWER(email)` 검색이 느려져 기능성 인덱스를 고려한다.

선택 기준:

- DB가 expression index를 안정적으로 지원하면 functional index
- 팀이 쿼리 가시성을 더 원하면 `email_normalized` generated column

핵심은 write 시점과 read 시점이 같은 normalization 규칙을 쓰도록 보장하는 것이다.

### 시나리오 2. JSON payload 안 상태값 조회

이벤트 테이블에서 `payload.status = 'FAILED'` 조건 조회가 잦다.

이때는:

- 자주 보는 JSON path만 generated column으로 승격
- 해당 컬럼에 인덱스 생성
- 나머지 드문 분석성 JSON 질의는 원본으로 유지

모든 JSON path를 컬럼화하면 스키마와 쓰기 비용만 늘어난다.

### 시나리오 3. soft delete active uniqueness 구현

`deleted_at IS NULL THEN email ELSE NULL` 같은 generated column을 두면 active row만 unique key를 갖게 할 수 있다.

이 패턴은 query optimization이 아니라 **제약조건 표현**에도 유용하다.

## 코드로 보기

```sql
-- MySQL 예시: generated column + index
ALTER TABLE users
  ADD COLUMN email_normalized VARCHAR(255)
    GENERATED ALWAYS AS (LOWER(email)) STORED,
  ADD INDEX idx_users_email_normalized (email_normalized);
```

```sql
SELECT id, email, status
FROM users
WHERE email_normalized = LOWER(?);
```

```sql
-- PostgreSQL 예시: expression index
CREATE INDEX idx_users_lower_email
ON users ((lower(email)));
```

```sql
-- 날짜 함수 대신 범위 조건으로 rewrite 가능한 경우
SELECT *
FROM orders
WHERE created_at >= '2026-04-14 00:00:00'
  AND created_at < '2026-04-15 00:00:00';
```

핵심은 expression을 인덱싱하는 방법보다, 그 표현식이 **write/read 양쪽에서 같은 의미를 유지하는가**를 검증하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 쿼리 rewrite | 가장 단순하고 유지보수가 쉽다 | 모든 조건에 적용되지는 않는다 | 범위 조건으로 치환 가능할 때 |
| functional index | 스키마 노출이 적다 | 쿼리-표현식 일치에 민감하다 | 엔진 지원이 좋고 팀 이해도가 높을 때 |
| generated column + index | 재사용성과 가시성이 좋다 | DDL과 backfill 비용이 든다 | 파생 키를 여러 쿼리/제약조건에서 쓸 때 |
| 애플리케이션 정규화만 사용 | 구현이 빠르다 | DB가 규칙을 모른다 | 일시적 우회, 낮은 정합성 요구 |

## 꼬리질문

> Q: 함수가 들어간 조건이 왜 느려지나요?
> 의도: sargable predicate 감각 확인
> 핵심: 원본 컬럼 인덱스를 그대로 활용하기 어려워 full scan이나 비효율 스캔이 생기기 쉽다

> Q: functional index와 generated column 중 무엇을 고르나요?
> 의도: 기술보다 운영 맥락으로 판단하는지 확인
> 핵심: 재사용성과 가시성, DDL 비용, 팀 이해도를 함께 봐야 한다

> Q: generated column 도입에서 가장 위험한 순간은 언제인가요?
> 의도: 배포 순서와 규칙 변경 리스크를 아는지 확인
> 핵심: old/new 쿼리와 스키마가 섞이는 전환 구간, 그리고 규칙 재계산 시점이다

## 한 줄 정리

generated column과 functional index의 핵심은 "함수 조건도 인덱스 친화적으로 만든다"가 아니라, 파생 규칙을 스키마와 배포 절차까지 포함해 안전하게 운영하는 것이다.
