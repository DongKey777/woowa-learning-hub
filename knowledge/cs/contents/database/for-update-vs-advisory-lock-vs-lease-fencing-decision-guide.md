---
schema_version: 3
title: FOR UPDATE Row Lock vs Advisory Lock vs Lease/Fencing 결정 가이드
concept_id: database/for-update-vs-advisory-lock-vs-lease-fencing-decision-guide
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- row-lock-vs-job-ownership
- advisory-lock-vs-lease
- stale-worker-fencing
aliases:
- row lock vs advisory lock vs lease
- for update advisory lock lease choice
- distributed lock vs row lock beginner
- 작업 중복 실행 방지 락 선택
- job ownership vs data row lock
- advisory lock or lease fencing
- 포업데이트 advisory lease 차이
- 긴 작업 락 뭐 써야 해
- stale worker 막는 락
- 배치 한 번만 실행 락 선택
symptoms:
- 한 번만 실행되게 하고 싶은데 FOR UPDATE와 advisory lock과 lease를 같은 도구로 보고 있다
- 긴 배치를 DB row lock으로 잡아 두려다가 어디까지 잠가야 하는지 헷갈린다
- worker takeover가 필요한 작업인데 advisory lock만으로 충분한지 모르겠다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- database/transaction-basics
- database/lock-basics
next_docs:
- database/advisory-locks-vs-row-locks
- database/db-lease-fencing-coordination
- database/queue-claim-skip-locked-fairness
linked_paths:
- contents/database/advisory-locks-vs-row-locks.md
- contents/database/db-lease-fencing-coordination.md
- contents/database/queue-claim-skip-locked-fairness.md
- contents/database/transactional-claim-check-job-leasing.md
- contents/database/lock-basics.md
confusable_with:
- database/advisory-locks-vs-row-locks
- database/db-lease-fencing-coordination
- database/queue-claim-skip-locked-fairness
forbidden_neighbors:
- contents/database/lock-basics.md
- contents/database/transaction-basics.md
expected_queries:
- 같은 작업을 한 번만 실행시키려면 SELECT FOR UPDATE, advisory lock, lease 중 무엇부터 골라야 해?
- 배치가 몇 분씩 도는데 row lock으로 버티면 안 되는 이유가 뭐야?
- worker가 죽으면 다른 worker가 이어받아야 할 때 advisory lock 말고 lease가 필요한가?
- 기존 row 수정이 아니라 job ownership 문제인데 FOR UPDATE를 쓰면 어디서 어긋나?
- stale worker가 늦게 돌아와 덮어쓰는 상황까지 막으려면 어떤 패턴을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 한 번만 실행되게 하고 싶다는 요구를 기존 데이터 충돌 보호, 짧은
  진입 통제, 긴 작업 소유권 유지로 나눠서 무엇을 골라야 하는지 결정하게 돕는
  chooser다. 배치를 오래 붙잡아도 되나, 작업 이름만 잠그면 되나, 다른 worker가
  이어받아야 하나, 늦게 돌아온 worker 덮어쓰기를 어떻게 막나 같은 자연어 표현이
  이 문서의 선택 기준에 매핑된다.
---

# FOR UPDATE Row Lock vs Advisory Lock vs Lease/Fencing 결정 가이드

## 한 줄 요약

> existing row를 안전하게 바꿀 일이면 `FOR UPDATE` row lock, 짧은 작업 진입 게이트면 advisory lock, 긴 실행과 takeover 및 stale write 방지까지 필요하면 lease/fencing을 먼저 본다.

## 결정 매트릭스

| 지금 지키려는 것 | 1차 선택 | 이유 |
|---|---|---|
| 이미 존재하는 주문·재고 row를 한 트랜잭션 안에서 읽고 곧바로 수정 | `FOR UPDATE` row lock | 보호 대상이 데이터 row 자체라서 DB가 가장 직접적으로 중재한다 |
| 같은 리포트 생성 버튼이나 같은 테넌트 배치 진입을 짧게 한 명만 통과 | advisory lock | row가 아니라 "작업 이름"을 잠그는 게 자연스럽고 세션 단위 게이트로 쓰기 쉽다 |
| 몇 분 이상 도는 worker 작업에서 소유권 유지와 takeover가 필요 | lease + fencing | 락을 오래 쥐기보다 owner 교체와 stale worker 차단을 별도 규칙으로 다뤄야 한다 |
| queue claim은 빨라야 하지만 실행 ownership은 오래 유지돼야 함 | claim은 `SKIP LOCKED`, ownership은 lease | 선점과 장기 실행 책임은 다른 문제라 분리해야 안전하다 |

짧게 기억하면 `FOR UPDATE`는 데이터 충돌, advisory lock은 진입 통제, lease/fencing은 장기 소유권과 늦은 쓰기 차단에 맞는다.

## 흔한 오선택

가장 흔한 오선택은 긴 배치를 `FOR UPDATE`로 붙잡아 두는 것이다. 학습자 표현으로는 "어차피 한 명만 돌면 되니까 row 하나 잠그고 끝 아닌가?"에 가깝다. row lock은 트랜잭션 안의 데이터 충돌에는 강하지만, 몇 분짜리 외부 호출이나 worker 재시작까지 품기 시작하면 커넥션 점유와 timeout만 커지고 takeover 규칙은 비어 있게 된다.

advisory lock을 lease 대체재로 보는 것도 자주 틀린다. "DB에서 락 하나만 잡으면 다른 worker가 못 들어오니까 충분한 것 아닌가?"처럼 들리지만, 세션이 끊겼다가 늦게 살아난 worker의 stale write까지 막으려면 단조 증가 token 같은 fencing 규칙이 필요하다. advisory lock만으로는 "누가 최신 owner인가"를 후속 write 경로까지 밀어 넣기 어렵다.

반대로 기존 row 수정인데 lease부터 떠올리는 것도 과하다. 주문 상태 변경이나 재고 차감처럼 충돌 surface가 이미 row라면, 먼저 row lock이나 원자적 update로 닫는 편이 더 직접적이다. 이 장면에서 lease를 먼저 들고 오면 보호 대상보다 coordination 레이어가 더 커져 설계가 불필요하게 복잡해진다.

## 다음 학습

row lock과 작업 게이트의 차이를 더 짧게 붙잡고 싶으면 [Advisory Locks와 Row Locks](./advisory-locks-vs-row-locks.md)를 먼저 본다.

stale worker, heartbeat 지연, fencing token이 왜 필요한지 이어서 보려면 [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md)으로 내려가면 된다.

queue claim과 긴 job ownership을 분리하는 장면이 궁금하면 [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)와 [Transactional Claim-Check와 Job Leasing](./transactional-claim-check-job-leasing.md)을 다음 문서로 잡으면 된다.
