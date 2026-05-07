---
schema_version: 3
title: Change Buffer Merge Debt
concept_id: database/change-buffer-merge-debt
canonical: true
category: database
difficulty: advanced
doc_role: symptom_router
level: advanced
language: ko
source_priority: 81
mission_ids: []
review_feedback_tags:
- change-buffer
- merge-debt
- secondary-index
- write-debt
aliases:
- change buffer merge debt
- delayed merge
- secondary index merge
- write debt
- buffer pool miss
- I/O spike
- innodb_change_buffering
- change buffer backlog
- merge debt
- 변경 버퍼 merge debt
symptoms:
- write-heavy batch 뒤에는 쓰기 latency가 괜찮았는데 이후 read latency와 I/O spike가 튄다
- secondary index 변경을 change buffer에 미뤄 둔 비용이 나중에 page read/merge 시점에 몰린다
- change buffer를 write 최적화로만 보고 merge debt와 buffer pool miss를 함께 보지 않는다
intents:
- symptom
- troubleshooting
- deep_dive
prerequisites:
- database/change-buffer-myths-vs-reality
- database/secondary-index-change-propagation
- database/innodb-buffer-pool-internals
next_docs:
- database/change-buffer-purge-history-length
- database/slow-query-analysis-playbook
- database/query-tuning-checklist
linked_paths:
- contents/database/change-buffer-myths-vs-reality.md
- contents/database/change-buffer-purge-history-length.md
- contents/database/secondary-index-change-propagation-path.md
- contents/database/innodb-buffer-pool-internals.md
confusable_with:
- database/change-buffer-myths-vs-reality
- database/change-buffer-purge-history-length
- database/secondary-index-change-propagation
- database/buffer-pool-read-ahead-eviction-interaction
forbidden_neighbors: []
expected_queries:
- change buffer merge debt는 secondary index 변경을 나중에 merge하면서 read latency와 I/O spike로 돌아오는 현상이야?
- write-heavy 배치 직후 조회가 느려지는 것을 change buffer backlog와 merge debt로 어떻게 설명해?
- change buffer는 write path를 가볍게 보이게 하지만 나중에 비용을 치르는 구조라는 말이 무슨 뜻이야?
- secondary index가 많고 buffer pool miss가 많으면 change buffer merge debt가 커지는 이유가 뭐야?
- innodb_change_buffering을 볼 때 write latency뿐 아니라 read path merge 비용도 같이 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Change Buffer Merge Debt symptom router로, InnoDB change buffer가 secondary index changes를
  지연 반영해 write path 비용을 나중의 page read/merge, buffer pool miss, I/O spike, read latency로 이동시키는
  증상을 설명한다.
---
# Change Buffer Merge Debt

> 한 줄 요약: change buffer merge debt는 쓰기를 미뤄 둔 비용이 한꺼번에 터질 때 생기는 뒤늦은 정산이며, 읽기 병목으로 돌아올 수 있다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: change buffer merge debt, delayed merge, secondary index merge, write debt, buffer pool miss, I/O spike, innodb_change_buffering

## 핵심 개념

- 관련 문서:
  - [Change Buffer Myths vs Reality](./change-buffer-myths-vs-reality.md)
  - [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
  - [Secondary Index Change Propagation Path](./secondary-index-change-propagation-path.md)

change buffer merge debt는 secondary index 변경을 뒤로 미루다 보니, 나중에 merge가 몰려서 비용이 폭발하는 현상이다.  
즉 지금 낸 쓰기 비용을 나중에 치르는 구조다.

핵심은 다음이다.

- write path는 가벼워 보일 수 있다
- 나중에 merge와 read path가 무거워질 수 있다
- merge debt가 커지면 latency spike가 생긴다

## 깊이 들어가기

### 1. 왜 debt라고 부르나

change buffer는 즉시 반영 대신 변경을 저장한다.  
그렇기 때문에 아직 치르지 않은 비용이 쌓인다.

이 미지급 비용이 merge debt다.

- 디스크에 아직 반영되지 않은 secondary change
- 나중에 page가 읽힐 때 합쳐야 하는 작업
- backlog가 늘수록 비용도 커짐

### 2. merge debt가 커지는 조건

- secondary index가 많다
- 해당 page가 버퍼 풀에 자주 없다
- write-heavy workload가 지속된다
- read path가 나중으로 밀린다

즉 "쓰기만 많고 읽기는 나중"인 시스템에서 잘 커진다.

### 3. merge debt가 터질 때 보이는 증상

- 갑자기 read latency가 튄다
- buffer pool miss가 늘어난다
- 백그라운드 I/O가 늘어난다
- 특정 시점에 page merge가 몰린다

### 4. debt를 줄이는 방법

- secondary index 수를 줄인다
- 버퍼 풀 핫셋을 늘린다
- 대량 적재와 일반 트래픽을 시간적으로 분리한다
- read/write 워크로드를 분리한다

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `change buffer merge debt`
- `delayed merge`
- `secondary index merge`
- `write debt`
- `buffer pool miss`
- `I/O spike`

## 실전 시나리오

### 시나리오 1. 배치 직후 조회가 느려진다

배치가 change buffer에 많은 변경을 쌓아 두면, 뒤이어 오는 조회가 merge debt를 치르게 된다.  
그래서 배치 성공과 서비스 안정성은 별개다.

### 시나리오 2. 쓰기 지연을 줄였는데 반대편이 터진다

write latency만 보고 change buffer를 좋아하면, 나중에 read path가 무거워질 수 있다.  
이건 성능을 시간 이동한 것뿐이다.

### 시나리오 3. 핫 페이지와 merge debt가 겹친다

자주 읽히는 page에 미뤄 둔 merge가 몰리면, read path가 더 불안정해진다.  
그래서 merge debt는 단순 백그라운드 작업이 아니다.

## 코드로 보기

### 상태 확인

```sql
SHOW VARIABLES LIKE 'innodb_change_buffering';
SHOW STATUS LIKE 'Innodb_ibuf_size';
SHOW ENGINE INNODB STATUS\G
```

### write-heavy 예시

```sql
INSERT INTO event_log (id, user_id, event_type, created_at)
VALUES (1, 1001, 'CLICK', NOW());
```

### 배치와 조회 분리

```sql
-- 배치 시간대 분리 예시
UPDATE orders
SET status = 'DONE'
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-04-08';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| change buffer 활용 | write path를 늦출 수 있다 | merge debt가 생긴다 | write-heavy OLTP |
| change buffer 의존 축소 | read path 안정성이 좋아진다 | 즉시 I/O가 늘 수 있다 | 읽기 SLA가 중요할 때 |
| secondary index 축소 | debt 생성 자체를 줄인다 | 일부 조회가 느려질 수 있다 | write 비용이 민감할 때 |

핵심은 merge debt를 "백그라운드 비용"으로만 보지 말고, **미뤄진 읽기/쓰기 비용의 합계**로 보는 것이다.

## 꼬리질문

> Q: change buffer merge debt는 왜 생기나요?
> 의도: 지연 반영의 비용 구조를 이해하는지 확인
> 핵심: 즉시 반영하지 않은 secondary index 변경이 쌓이기 때문이다

> Q: merge debt가 터지면 무엇이 느려지나요?
> 의도: read path 영향까지 아는지 확인
> 핵심: 나중에 읽기와 I/O가 같이 흔들린다

> Q: debt를 줄이는 가장 좋은 방법은 무엇인가요?
> 의도: 근본 원인 제거를 생각하는지 확인
> 핵심: secondary index와 워크로드 분리를 줄이는 것이다

## 한 줄 정리

change buffer merge debt는 미뤄 둔 secondary index 변경의 비용이 나중에 몰려오는 현상이며, 결국 read latency와 I/O spike로 돌아올 수 있다.
