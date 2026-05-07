---
schema_version: 3
title: Savepoint Rollback, Lock Retention, and Escalation Edge Cases
concept_id: database/savepoint-lock-retention-edge-cases
canonical: true
category: database
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- savepoint
- lock-retention
- partial-rollback
- gap-lock
- lock-wait
aliases:
- savepoint lock retention
- rollback to savepoint locks
- partial rollback edge case
- gap lock after rollback
- lock footprint persistence
- savepoint lock wait
- escalation misconception
- partial retry transaction
- rollback did not release lock
- savepoint 이후 락 유지
symptoms:
- ROLLBACK TO SAVEPOINT 이후에도 lock wait timeout이나 blocker가 계속 남아 있어
- 부분 롤백했으니 gap lock이나 range lock도 풀렸다고 오해하고 있어
- queue claim이나 range FOR UPDATE를 savepoint로 되돌린 뒤 insert starvation이 계속 발생해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- database/savepoint-partial-rollback
- database/gap-lock-next-key-lock
next_docs:
- database/savepoint-lock-retention-incidents
- database/lock-wait-deadlock-latch-triage-playbook
- database/lock-escalation-misconceptions
linked_paths:
- contents/database/savepoint-partial-rollback.md
- contents/database/lock-escalation-misconceptions.md
- contents/database/gap-lock-next-key-lock.md
- contents/database/transaction-timeout-vs-lock-timeout.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
- contents/database/savepoint-lock-retention-incident-scenarios.md
confusable_with:
- database/savepoint-partial-rollback
- database/savepoint-lock-retention-incidents
- database/lock-escalation-misconceptions
forbidden_neighbors: []
expected_queries:
- ROLLBACK TO SAVEPOINT를 했는데 왜 lock wait timeout이 계속 발생할 수 있어?
- savepoint partial rollback이 데이터 변경은 되돌려도 lock footprint를 줄이지 못하는 이유가 뭐야?
- gap lock이나 next-key lock이 있는 range query를 savepoint로 되돌리면 insert starvation이 바로 풀려?
- lock escalation처럼 보이지만 실제로는 넓은 range lock과 장기 transaction일 수 있다는 뜻이 뭐야?
- savepoint를 쓰는 partial retry 패턴에서 transaction을 짧게 끝내야 하는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 savepoint rollback, lock retention, partial rollback, gap/next-key lock, lock footprint persistence를 advanced edge case로 설명하는 deep dive다.
  ROLLBACK TO SAVEPOINT 이후 lock wait, blocker 유지, partial retry transaction, escalation misconception 질문이 본 문서에 매핑된다.
---
# Savepoint Rollback, Lock Retention, and Escalation Edge Cases

> 한 줄 요약: savepoint로 부분 롤백해도 이미 잡은 락과 넓어진 잠금 범위가 자동으로 줄어들지 않는 경우가 많아서, "부분 실패만 되돌렸으니 경합도 사라졌겠지"라고 생각하면 운영 판단이 틀어진다.

**난이도: 🔴 Advanced**

관련 문서:

- [Savepoint와 Partial Rollback](./savepoint-partial-rollback.md)
- [Lock Escalation Misconceptions](./lock-escalation-misconceptions.md)
- [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
- [Transaction Timeout과 Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./lock-wait-deadlock-latch-triage-playbook.md)
- [Savepoint + Lock Retention Incident Scenarios and Recovery Patterns](./savepoint-lock-retention-incident-scenarios.md)

retrieval-anchor-keywords: savepoint lock retention, rollback to savepoint locks, partial rollback edge case, gap lock after rollback, lock footprint persistence, escalation misconception, backend transaction edge case

## 핵심 개념

savepoint는 데이터 변경을 일부 되돌릴 수 있게 해 준다.  
하지만 "되돌린다"는 말이 곧 다음을 뜻하는 것은 아니다.

- lock footprint 축소
- gap/next-key lock 해제
- metadata lock 해제
- wait graph 해소

즉 savepoint rollback은 **데이터 상태 복구 도구**이지, 이미 형성된 경합 표면을 자동으로 줄이는 장치로 보면 위험하다.

## 깊이 들어가기

### 1. savepoint가 되돌리는 것과 못 되돌리는 것을 분리해야 한다

보통 `ROLLBACK TO SAVEPOINT`가 잘하는 일:

- 해당 시점 이후 INSERT/UPDATE/DELETE undo
- 부분적인 비즈니스 흐름 재시도

하지만 여전히 남을 수 있는 것:

- 그 트랜잭션이 획득한 lock footprint
- 범위 조회가 만들어낸 gap/next-key lock 영향
- transaction 자체가 유지되는 한 남는 metadata usage

즉 "데이터는 되돌렸지만 트랜잭션은 아직 살아 있다"는 점이 핵심이다.

### 2. savepoint rollback이 lock wait 문제를 바로 풀어 준다고 기대하면 안 된다

자주 생기는 오해:

1. 트랜잭션이 넓은 범위를 잡음
2. 일부 단계 실패
3. savepoint로 되돌림
4. 이제 다른 세션도 안 막힐 거라 기대

실제로는 같은 트랜잭션이 계속 열려 있으면:

- 다른 세션 입장에서는 blocker가 여전히 살아 있고
- 범위 잠금/사용 흔적이 유지될 수 있으며
- timeout과 starvation이 계속 보일 수 있다

즉 savepoint는 "부분 복구"일 뿐, **트랜잭션 전체 종료와 동일하지 않다**.

### 3. gap/next-key lock이 있는 워크로드에서 특히 오해가 커진다

범위 조회와 `FOR UPDATE`가 섞이면 잠금 범위는 row보다 넓다.

예:

- `status='READY'` 범위 조회
- `id BETWEEN ... FOR UPDATE`
- queue claim range

이 상태에서 일부 row 변경만 되돌려도:

- 범위를 보호하려던 lock 의미는 여전히 남고
- insert starvation이나 hot range wait가 계속될 수 있다

즉 savepoint rollback은 phantom 방지용 잠금 의미를 쉽게 "없던 일"로 만들지 못한다.

### 4. lock escalation 오해와 섞이면 진단이 더 어려워진다

운영에서는 종종:

- "부분 롤백했는데 왜 계속 막히지?"
- "이제 row를 되돌렸으니 table lock도 사라졌겠지?"

같은 착각이 생긴다.

하지만 실제로는:

- 진짜 escalation이 아니라 넓은 range lock일 수 있고
- MDL 대기일 수 있고
- long-running transaction이 계속 metadata usage를 유지할 수 있다

즉 savepoint 이후 대기 지속은 "rollback 실패"가 아니라, **락 계층을 잘못 이해한 결과**일 수 있다.

### 5. partial retry 패턴은 lock footprint를 줄이도록 설계해야 한다

savepoint를 쓸 때 현실적인 원칙:

- 부분 롤백 후에도 같은 큰 트랜잭션을 오래 끌지 않는다
- 재시도 대상 범위를 더 작게 자른다
- 가능하면 외부 I/O 이전의 짧은 단계에만 savepoint를 둔다
- lock-heavy range step은 별도 transaction으로 분리할지 검토한다

즉 savepoint 사용 자체보다, **savepoint 이후 얼마나 빨리 트랜잭션을 끝내는가**가 중요하다.

### 6. forensic 관점에서는 "savepoint를 썼다"보다 "blocker가 아직 살아 있나"를 먼저 봐야 한다

운영 체크 질문:

- blocker transaction이 아직 open인가
- gap/next-key lock 범위가 남아 있나
- 대기 세션이 줄었나
- rollback to savepoint 이후 실제 latency가 내려갔나

코드 의도보다 wait graph 현실을 먼저 보는 편이 안전하다.

## 실전 시나리오

### 시나리오 1. queue claim 후 일부 처리 실패

worker가 range claim을 하고 일부 row 처리를 savepoint로 되돌린다.

문제:

- claim range를 잡은 트랜잭션이 그대로 살아 있어
- 신규 insert/claim이 계속 밀릴 수 있다

### 시나리오 2. 부분 실패는 복구됐는데 `lock wait timeout`이 계속 남

원인은 savepoint 이후에도 큰 transaction이 열린 채 외부 호출을 기다리는 것이다.

교훈:

- partial rollback과 lock release를 같은 것으로 보면 안 된다

### 시나리오 3. 운영자는 "lock escalation"이라고 오해

실제로는 table lock으로 승격된 게 아니라, 넓은 range lock + 장기 transaction 조합일 수 있다.

## 코드로 보기

```sql
START TRANSACTION;

SELECT id
FROM job_queue
WHERE status = 'READY'
ORDER BY available_at
LIMIT 10
FOR UPDATE;

SAVEPOINT claimed_batch;

UPDATE job_queue
SET status = 'CLAIMED'
WHERE id IN (101, 102, 103);

ROLLBACK TO SAVEPOINT claimed_batch;
-- 데이터는 일부 되돌렸지만,
-- 트랜잭션과 관련 범위 잠금 의미는 여전히 남을 수 있다.
```

```text
triage questions
1. rollback to savepoint 이후 transaction still open?
2. waiting sessions actually decreased?
3. blocker holds range/metadata lock?
4. should this step be split into a smaller transaction?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| savepoint partial rollback | 전체 rollback을 피할 수 있다 | lock footprint가 그대로 남을 수 있다 | 일부 단계만 복구할 때 |
| 전체 rollback + 재시작 | lock surface를 깨끗하게 비운다 | 앞선 작업도 다시 해야 한다 | 경합이 더 치명적일 때 |
| 단계 분리 transaction | 락 범위를 줄이기 쉽다 | 중간 상태 관리가 필요하다 | lock-heavy workflow |
| 큰 transaction 유지 | 코드가 단순해 보인다 | timeout/starvation이 커진다 | 가능하면 피해야 함 |

## 꼬리질문

> Q: savepoint로 되돌리면 잡았던 락도 자동으로 다 풀리나요?
> 의도: 데이터 rollback과 lock footprint를 분리하는지 확인
> 핵심: 아니다. 부분 롤백이 곧 transaction 종료나 범위 잠금 해제를 뜻하지는 않는다

> Q: savepoint 이후에도 insert가 막히면 무엇을 의심하나요?
> 의도: gap/range lock과 long transaction을 떠올리는지 확인
> 핵심: 같은 트랜잭션이 여전히 범위 잠금을 유지하고 있을 수 있다

> Q: savepoint와 lock escalation 오해가 왜 같이 나오나요?
> 의도: 관측상 "계속 막힘"의 원인 분류를 하는지 확인
> 핵심: 실제론 escalation이 아니라 range lock/MDL/장기 transaction일 수 있기 때문이다

## 한 줄 정리

savepoint partial rollback은 데이터를 일부 되돌리는 기능이지, 이미 형성된 잠금 범위와 대기 관계를 자동으로 정리해 주는 기능으로 보면 안 된다.
