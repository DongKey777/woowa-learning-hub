---
schema_version: 3
title: Transactional Claim-Check and Job Leasing
concept_id: database/transactional-claim-check-job-leasing
canonical: true
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- claim-check
- job-lease
- queue
- fencing
- idempotency
aliases:
- transactional claim-check
- job leasing
- claim-check
- payload reference
- work claim
- lease row
- skip locked
- job ownership
- payload ref worker
- claim row takeover
symptoms:
- 큰 payload를 queue에 직접 넣지 않고 DB나 object storage에 저장한 뒤 참조만 넘기고 싶어
- 여러 worker가 같은 job을 동시에 처리하지 않도록 lease row와 ownership을 관리해야 해
- lease 만료 후 takeover가 가능하지만 stale worker write를 막기 위해 fencing이 필요해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- database/db-lease-fencing-coordination
- database/transactional-inbox-dedup-design
next_docs:
- database/stale-lease-renewal-failure-fencing
- database/queue-claim-skip-locked-fairness
- database/exactly-once-myths-db-queue
linked_paths:
- contents/database/db-lease-fencing-coordination.md
- contents/database/transactional-inbox-dedup-design.md
- contents/database/exactly-once-myths-db-queue.md
- contents/database/queue-claim-skip-locked-fairness.md
- contents/database/stale-lease-renewal-failure-fencing.md
confusable_with:
- database/transactional-inbox-dedup-design
- database/db-lease-fencing-coordination
- database/queue-claim-skip-locked-fairness
forbidden_neighbors: []
expected_queries:
- claim-check와 job leasing은 각각 payload 분리와 worker ownership 문제를 어떻게 나눠 해결해?
- 큰 메시지 본문을 queue에 직접 넣지 않고 payload_ref만 넘기는 transactional claim-check 패턴을 설명해줘
- lease row를 선점한 worker만 job을 처리하게 하려면 어떤 컬럼과 상태 전이가 필요해?
- lease가 만료되어 다른 worker가 takeover할 때 stale worker write를 fencing으로 어떻게 막아?
- claim-check를 쓰면 큐 중복이 사라지는 것이 아니라 leasing과 inbox dedup이 추가로 필요한 이유는?
contextual_chunk_prefix: |
  이 문서는 transactional claim-check와 job leasing을 payload reference, lease row, work claim, worker ownership, takeover/fencing 관점으로 설명하는 advanced playbook이다.
  claim-check, job leasing, payload_ref, skip locked claim, stale worker 질문이 본 문서에 매핑된다.
---
# Transactional Claim-Check와 Job Leasing

> 한 줄 요약: claim-check는 큰 작업 본문을 안전하게 분리해 두고, job leasing은 그 작업을 한 worker만 처리하게 만든다.

**난이도: 🔴 Advanced**

관련 문서: [DB Lease와 Fencing Token](./db-lease-fencing-coordination.md), [Transactional Inbox와 Dedup Design](./transactional-inbox-dedup-design.md), [Exactly-Once 신화와 DB + Queue 경계](./exactly-once-myths-db-queue.md), [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md)
retrieval-anchor-keywords: claim-check, job leasing, payload reference, work claim, lease row, skip locked, job ownership

## 핵심 개념

Transactional claim-check는 큰 payload를 직접 전달하지 않고, DB나 object storage에 저장한 뒤 참조만 넘기는 방식이다.  
Job leasing은 그 참조를 가진 작업을 한 worker가 일정 기간 독점하도록 만드는 패턴이다.

왜 중요한가:

- 큰 payload를 큐에 그대로 넣으면 중복 전송과 비용이 커진다
- 동시에 여러 worker가 같은 작업을 집는 것을 막아야 한다
- 작업 본문과 처리 소유권을 분리하면 복구가 쉬워진다

claim-check는 “무엇을 처리할지”를 분리하고, leasing은 “누가 처리할지”를 정한다.

## 깊이 들어가기

### 1. claim-check가 필요한 이유

메시지에 본문을 다 넣는 대신:

- payload를 DB나 storage에 저장
- queue에는 참조 키만 전달
- worker는 해당 키로 본문을 가져옴

이렇게 하면 큐가 가벼워지고, 본문을 재처리하기 쉬워진다.

### 2. job leasing이 필요한 이유

claim-check만 있으면 여러 worker가 같은 payload를 동시에 집을 수 있다.

- 같은 job이 두 번 실행될 수 있다
- 처리 순서가 꼬일 수 있다
- 중복 side effect가 생길 수 있다

job leasing은 claim row를 선점하고 lease를 갱신하는 방식으로 이를 방지한다.

### 3. claim-check와 inbox의 차이

- claim-check: 작업 본문을 분리하고 참조만 전달
- inbox: 받은 메시지를 dedup하고 처리 여부를 기록

둘은 함께 쓸 수 있지만 목적이 다르다.

### 4. 실패 처리

- lease 만료 후 다른 worker가 takeover
- claim row는 처리 상태에 따라 다시 실행 가능
- payload는 immutable하게 두는 것이 안전하다

## 실전 시나리오

### 시나리오 1: 대용량 리포트 생성

리포트 본문이 크면 큐에 직접 싣기보다 claim-check로 저장하고 job leasing으로 한 worker만 처리하게 한다.

### 시나리오 2: 첨부 파일 처리

파일 참조만 큐에 넘기고, worker가 storage에서 가져와 처리한다.  
동시에 두 worker가 같은 파일을 만지지 않게 lease가 필요하다.

### 시나리오 3: 재시도 중 중복 작업

작업이 timeout되면 다른 worker가 이어받을 수 있어야 한다.  
lease와 claim row가 있으면 takeover가 가능하다.

## 코드로 보기

```sql
CREATE TABLE job_claims (
  job_id VARCHAR(100) PRIMARY KEY,
  payload_ref VARCHAR(200) NOT NULL,
  owner_id VARCHAR(100) NULL,
  lease_expires_at DATETIME NULL,
  status VARCHAR(20) NOT NULL
);
```

```java
if (claimRepository.tryAcquire(jobId, workerId)) {
    Payload payload = payloadStore.load(payloadRef);
    process(payload);
    claimRepository.markDone(jobId);
}
```

claim-check는 payload를 분리하고, leasing은 **같은 작업을 한 번만 처리하게 만드는 소유권 제어**다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| direct queue payload | 단순하다 | 크기와 중복 비용이 크다 | 작은 메시지 |
| claim-check | 큐가 가벼워진다 | storage 조회가 필요하다 | 대용량 payload |
| claim-check + lease | 중복 처리 방지 | 구현이 복잡하다 | 중요한 job |
| in-memory worker lock | 빠르다 | 장애 복구가 약하다 | 단일 프로세스 |

## 꼬리질문

> Q: claim-check와 job leasing은 왜 같이 쓰나요?
> 의도: payload 분리와 소유권 제어를 구분하는지 확인
> 핵심: 본문을 분리하고, 처리권을 한 worker로 제한하기 위해서다

> Q: lease가 만료되면 어떤 일이 일어나나요?
> 의도: takeover와 중복 위험을 아는지 확인
> 핵심: 다른 worker가 이어받을 수 있지만 fencing이 필요하다

> Q: claim-check를 쓰면 큐 중복이 사라지나요?
> 의도: claim-check의 역할을 정확히 아는지 확인
> 핵심: 아니다, 중복 방지와는 다른 문제다

## 한 줄 정리

Transactional claim-check는 큰 작업 본문을 분리하고, job leasing으로 그 작업을 한 worker만 안전하게 처리하게 만드는 패턴이다.
