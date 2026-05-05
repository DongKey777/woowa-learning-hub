---
schema_version: 3
title: Plain SELECT vs Locking Read vs SERIALIZABLE 결정 가이드
concept_id: database/plain-select-vs-locking-read-vs-serializable-decision-guide
canonical: true
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- plain-select-vs-for-update
- serializable-overreach
- read-check-write-confusion
aliases:
- plain select vs locking read vs serializable
- plain SELECT FOR UPDATE SERIALIZABLE 차이
- snapshot read vs current read choice
- 그냥 select 랑 for update 랑 serializable 선택
- 읽기만 하면 되는지 locking read 가 필요한지
- select for update or serializable
- consistent read vs lock read beginner
symptoms:
- 조회가 안 흔들리면 되는지 아니면 다른 요청을 기다리게 해야 하는지 한 질문으로 섞여 있다
- SELECT FOR UPDATE를 붙일지 SERIALIZABLE로 올릴지 그냥 SELECT로 놔둘지 기준이 헷갈린다
- 방금 읽은 조건을 믿고 쓰려는데 MVCC 스냅샷과 락과 retry가 각각 어디서 필요한지 구분이 안 된다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/transaction-basics
- database/transaction-isolation-basics
- database/lock-basics
next_docs:
- database/mvcc-snapshot-vs-locking-read-portability
- database/read-committed-vs-repeatable-read-vs-serializable-decision-guide
- database/unique-vs-version-cas-vs-for-update-chooser
linked_paths:
- contents/database/transaction-isolation-basics.md
- contents/database/lock-basics.md
- contents/database/transaction-isolation-locking.md
- contents/database/mvcc-snapshot-vs-locking-read-portability-note.md
- contents/database/read-committed-vs-repeatable-read-vs-serializable-decision-guide.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
- contents/database/postgresql-serializable-retry-playbook.md
- contents/database/for-update-zero-row-duplicate-insert-symptom-router.md
confusable_with:
- database/mvcc-snapshot-vs-locking-read-portability
- database/read-committed-vs-repeatable-read-vs-serializable-decision-guide
- database/lock-basics
forbidden_neighbors: []
expected_queries:
- 같은 데이터를 읽는 코드에서 그냥 조회면 충분한지, FOR UPDATE가 필요한지, 아예 SERIALIZABLE로 감싸야 하는지 어떻게 먼저 가르지?
- 방금 본 값이 안 바뀌면 좋다는 요구와 다른 요청을 막아야 한다는 요구는 왜 같은 해결책이 아니야?
- 읽고 판단한 뒤 쓰는 로직에서 plain SELECT를 써도 되는 장면과 locking read가 필요한 장면을 빠르게 비교하고 싶어
- PostgreSQL SERIALIZABLE은 락을 더 세게 거는 모드라고 이해하면 왜 틀려?
- SELECT FOR UPDATE를 붙였는데도 범위 규칙이 새는 경우는 언제고, 그때는 무엇을 더 봐야 해?
- MVCC 스냅샷 읽기와 current row를 잡는 읽기와 whole-transaction retry가 각각 어느 층 문제인지 한 번에 정리해 줘
contextual_chunk_prefix: |
  이 문서는 학습자가 plain SELECT, locking read, SERIALIZABLE을 모두
  "더 안전한 읽기 옵션"처럼 한 줄로 외울 때, 가시성 확인, 현재 row 선점,
  query 기반 의사결정 race 차단을 먼저 갈라 주는 chooser다. 그냥 읽기면
  되나, FOR UPDATE로 줄 세워야 하나, retry 비용을 감수하고 SERIALIZABLE을
  써야 하나, 읽은 장면이 안 흔들리는 것과 다른 요청을 막는 것이 같은가 같은
  자연어 질문이 이 문서의 결정 기준에 매핑된다.
---

# Plain SELECT vs Locking Read vs SERIALIZABLE 결정 가이드

## 한 줄 요약

> 값을 보기만 하면 되면 plain `SELECT`, 이미 있는 row를 읽고 곧바로 상태를 바꿔야 하면 locking read, 조회-판단-쓰기 사이의 집합 규칙 경쟁 자체를 막아야 하면 `SERIALIZABLE`을 먼저 본다.

## 결정 매트릭스

| 지금 먼저 지키려는 것 | 1차 선택 | 왜 이렇게 고르나 |
|---|---|---|
| 목록 조회, 단건 상세, 단순 검증처럼 최신 committed 값을 보는 것이 목적 | plain `SELECT` | 가시성 문제이고, 다른 요청을 줄 세우는 비용까지 들일 이유가 없다 |
| 이미 존재하는 주문·재고·예약 row를 읽고 바로 수정해야 함 | locking read | 보호 대상이 current row라서 읽는 순간 ownership을 잡는 편이 맞다 |
| "없으면 insert", count 제한, overlap 판단처럼 query 결과를 믿고 결정을 내림 | `SERIALIZABLE` 또는 constraint 재모델링 | row 하나가 아니라 판단 자체가 경쟁하므로 plain read나 row lock만으로는 구멍이 남을 수 있다 |
| duplicate key winner 확인처럼 최종 승자는 `UNIQUE`가 정하고, 읽기는 후속 재조회일 뿐 | plain `SELECT` + fresh read | winner 판정은 write-time constraint가 맡고 `FOR UPDATE`가 주인공이 아니다 |

짧게 기억하면 plain `SELECT`는 **보는 도구**, locking read는 **existing row를 잡는 도구**, `SERIALIZABLE`은 **판단 경쟁을 실패시키는 도구**다.

## 흔한 오선택

가장 흔한 오선택은 "`안전해야 하니까 FOR UPDATE`"다.  
학습자 표현으로는 "읽고 나서 바로 저장하니까 일단 잠그면 끝 아닌가?"에 가깝다.  
하지만 잠글 row가 아예 없거나, 조건이 count·range·absence라면 row lock은 질문을 잘못 잡은 셈이다.

반대로 "`SERIALIZABLE`이면 락이 제일 세니까 다 해결된다"도 자주 틀린다.  
PostgreSQL 기준 `SERIALIZABLE`은 보통 모든 row를 먼저 잠그는 모드가 아니라, 위험한 동시성 조합을 `40001`로 밀어내고 새 트랜잭션 재시도를 요구하는 쪽에 가깝다.  
즉 blocking보다 retry envelope 설계가 먼저 따라온다.

"plain `SELECT`가 못 본 row면 `UPDATE`도 못 건드리겠지"라는 직관도 위험하다.  
MVCC snapshot으로 보는 plain read와 current row를 잡는 locking/DML path는 엔진마다 다르게 움직일 수 있다.  
그래서 snapshot 안정성과 row ownership을 같은 축으로 외우면 포팅과 디버깅에서 계속 섞인다.

## 다음 학습

plain `SELECT`와 locking read가 엔진별로 왜 다르게 보이는지 더 정확히 붙잡고 싶으면 [MVCC Snapshot vs Locking Read Portability Note](./mvcc-snapshot-vs-locking-read-portability-note.md)로 내려가면 된다.

격리 수준 이름까지 함께 비교해야 한다면 [Read Committed vs Repeatable Read vs Serializable 결정 가이드](./read-committed-vs-repeatable-read-vs-serializable-decision-guide.md)를 이어 보면 된다.

exact-key duplicate나 existing row 수정처럼 `SERIALIZABLE`보다 더 직접적인 해법이 궁금하면 [UNIQUE vs Version CAS vs FOR UPDATE 결정 가이드](./unique-vs-version-cas-vs-for-update-decision-guide.md)와 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)를 다음 문서로 잡는 편이 안전하다.
