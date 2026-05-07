---
schema_version: 3
title: Foreign Key Cascade Lock Surprises
concept_id: database/foreign-key-cascade-lock-surprises
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- foreign-key-cascade-lock-amplification
- parent-delete-child-lock-storm
- cascade-vs-soft-delete
aliases:
- foreign key cascade lock
- ON DELETE CASCADE lock
- ON UPDATE CASCADE cost
- cascade lock amplification
- parent delete child lock storm
- child table lock propagation
- foreign key delete blocking
- FK cascade 락
- cascade update cost
- 부모 삭제 자식 락
symptoms:
- 부모 row 하나 삭제했는데 child table 수천 row의 lock과 IO가 같이 터지고 있어
- ON DELETE CASCADE를 편의 기능으로만 보고 대량 삭제 배치의 lock amplification을 놓치고 있어
- cascade, soft delete, async cleanup 중 어떤 삭제 전략을 고를지 운영 비용 기준이 필요해
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- database/primary-foreign-key-basics
- database/transaction-isolation-locking
next_docs:
- database/metadata-lock-ddl-blocking
- database/deadlock-case-study
- database/soft-delete-uniqueness-indexing-lifecycle
- database/lock-wait-deadlock-latch-triage-playbook
linked_paths:
- contents/database/primary-foreign-key-basics.md
- contents/database/transaction-isolation-locking.md
- contents/database/metadata-lock-ddl-blocking.md
- contents/database/deadlock-case-study.md
- contents/database/soft-delete-uniqueness-indexing-lifecycle.md
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
confusable_with:
- database/primary-foreign-key-basics
- database/metadata-lock-ddl-blocking
- database/soft-delete-uniqueness-indexing-lifecycle
forbidden_neighbors: []
expected_queries:
- ON DELETE CASCADE가 부모 row 하나 삭제인데 왜 child table lock storm을 만들 수 있어?
- foreign key cascade와 soft delete는 대량 삭제 운영에서 어떤 tradeoff가 있어?
- FK cascade가 lock amplification을 만들 때 어떤 child index와 transaction length를 봐야 해?
- 부모 키 변경이 ON UPDATE CASCADE로 자식 갱신 폭탄이 되는 이유는 뭐야?
- cascade delete 배치를 chunking이나 async cleanup으로 바꿔야 하는 기준을 알려줘
contextual_chunk_prefix: |
  이 문서는 foreign key cascade가 parent delete/update를 child table lock, IO, transaction length로 증폭시키는 운영 위험을 설명하는 advanced deep dive다.
  ON DELETE CASCADE, cascade lock, parent delete child lock storm, soft delete tradeoff 같은 자연어 질문이 본 문서에 매핑된다.
---
# Foreign Key Cascade Lock Surprises

> 한 줄 요약: ON DELETE/UPDATE CASCADE는 편하지만, 부모 한 줄이 자식 수천 줄의 락과 IO를 함께 끌고 갈 수 있다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md), [Deadlock Case Study](./deadlock-case-study.md), [Soft Delete, Uniqueness, and Data Lifecycle Design](./soft-delete-uniqueness-indexing-lifecycle.md)
retrieval-anchor-keywords: foreign key cascade, ON DELETE CASCADE, ON UPDATE CASCADE, cascade lock, lock amplification, referential integrity, parent delete child lock storm, child table lock propagation, foreign key delete blocking, cascade update cost

## 핵심 개념

Foreign key cascade는 부모 row를 지우거나 바꿀 때 자식 row도 함께 수정하는 기능이다.  
하지만 이 편리함은 종종 락 증폭과 예기치 않은 대기라는 대가를 만든다.

왜 중요한가:

- 부모 한 건 삭제가 자식 테이블 전체의 락 폭발로 이어질 수 있다
- cascade는 눈에 보이지 않게 여러 테이블을 함께 건드린다
- 대량 정리 작업이 서비스 트래픽을 막을 수 있다

즉 FK cascade는 무결성 장치이면서 동시에 **잠금 전파 장치**다.

## 깊이 들어가기

### 1. cascade가 편한 이유

애플리케이션이 직접 자식 row를 찾지 않아도 된다.

- 부모 삭제 시 자식도 자동 삭제
- 부모 키 변경 시 자식도 자동 갱신

모델링은 단순해지고, 누락 위험도 줄어든다.

### 2. 그런데 왜 락이 커지나

부모 하나를 바꾸는 동작이 자식 여러 row에 대한 작업으로 확장되기 때문이다.

- 자식 row를 찾기 위한 인덱스 접근
- 여러 child table로의 연쇄 작업
- 중간 상태를 유지하는 동안 락 보유 시간 증가

결과적으로 “부모 row 하나”가 아니라 **관계 전체**가 잠긴다.

### 3. 대량 삭제가 특히 위험한 이유

예를 들어 오래된 account를 지울 때 관련 order, payment, audit가 cascade면,

- 잠금 범위가 넓어지고
- 트랜잭션이 길어지고
- 다른 쓰기 요청이 밀린다

이 경우 cascade는 단순한 편의 기능이 아니라 배치 장애의 원인이 된다.

### 4. 설계 시 확인할 것

- 자식 row 수가 얼마나 되는가
- cascade가 정말 자동이어야 하는가
- soft delete나 비동기 정리가 더 나은가
- 삭제 작업을 chunk로 나눌 수 있는가

## 실전 시나리오

### 시나리오 1: 고객 탈퇴가 서비스 전체를 막음

계정 하나를 지우는데 연결된 주문/정산/로그 row가 너무 많으면 락이 오래 간다.  
사용자는 계정 삭제가 아닌 “서비스 느려짐”으로 경험한다.

### 시나리오 2: 부모 키 변경이 자식 갱신 폭탄이 됨

기본키를 자연키처럼 쓰고 변경할 수 있게 만들면, cascade update가 대규모 갱신이 될 수 있다.

### 시나리오 3: 자식 인덱스가 부족해 더 느려짐

FK 컬럼 인덱스가 적절하지 않으면 cascade가 자식 row를 찾는 데 더 오래 걸린다.  
이건 논리 기능이 물리 성능과 맞물리는 대표 사례다.

## 코드로 보기

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  customer_id BIGINT NOT NULL
);

CREATE TABLE payments (
  id BIGINT PRIMARY KEY,
  order_id BIGINT NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

DELETE FROM orders WHERE id = 1001;
```

위 한 줄은 payments row까지 함께 건드릴 수 있다.  
작아 보이지만 실제로는 다중 테이블 잠금 작업이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| ON DELETE CASCADE | 구현이 단순하다 | 락 전파가 크다 | 자식이 적고 명확할 때 |
| 수동 batched delete | 제어가 쉽다 | 코드가 복잡하다 | 대량 삭제 |
| soft delete | 안전하다 | 데이터가 남는다 | 복구 가능성이 필요할 때 |
| async cleanup | 트래픽 분산이 된다 | 최종 일관성이다 | 즉시 삭제가 아니어도 될 때 |

## 꼬리질문

> Q: FK cascade가 왜 락 문제를 만들 수 있나요?
> 의도: 관계형 제약이 여러 row로 확장되는 점을 아는지 확인
> 핵심: 부모 한 건의 작업이 자식 다수의 작업으로 커진다

> Q: cascade와 soft delete 중 무엇을 선택해야 하나요?
> 의도: 운영과 정합성의 trade-off를 이해하는지 확인
> 핵심: 대량 삭제와 복구 필요성을 기준으로 판단한다

> Q: 부모 row 하나 삭제가 왜 전체 서비스에 영향을 주나요?
> 의도: lock amplification을 이해하는지 확인
> 핵심: cascade는 보이지 않는 다중 테이블 작업이기 때문이다

## 한 줄 정리

Foreign key cascade는 무결성을 자동으로 지켜주지만, 동시에 잠금을 여러 테이블로 전파하므로 대량 작업에서는 더 조심해야 한다.
