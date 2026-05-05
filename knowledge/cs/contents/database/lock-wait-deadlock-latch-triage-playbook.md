---
schema_version: 3
title: Lock Wait, Deadlock, and Latch Contention Triage Playbook
concept_id: database/lock-wait-deadlock-latch-triage-playbook
canonical: false
category: database
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- lock-wait-vs-deadlock
- metadata-lock-misdiagnosis
- latch-vs-lock
aliases:
- lock wait triage
- deadlock debugging
- metadata lock
- latch contention
- hot page contention
symptoms:
- DB가 잠겨서 요청이 계속 멈추는데 row lock인지 deadlock인지 구분이 안 된다
- deadlock error와 lock timeout이 섞여 보여서 retry 정책을 못 정하겠다
- DDL 배포 중 suddenly 멈췄는데 metadata lock인지 모르겠다
- TPS가 plateau인데 blocker SQL은 안 보여서 latch contention이 의심된다
intents:
- troubleshooting
- design
prerequisites:
- database/transaction-timeout-vs-lock-timeout
- database/deadlock-case-study
next_docs:
- database/metadata-lock-ddl-blocking
- database/btree-latch-contention-hot-pages
- database/slow-query-analysis-playbook
linked_paths:
- contents/database/hibernate-lock-sql-log-to-deadlock-triage-bridge.md
- contents/database/deadlock-case-study.md
- contents/database/metadata-lock-ddl-blocking.md
- contents/database/slow-query-analysis-playbook.md
- contents/spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md
confusable_with:
- database/deadlock-vs-lock-wait-timeout-primer
- spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix
forbidden_neighbors:
- contents/database/connection-pool-basics.md
expected_queries:
- lock wait, deadlock, latch contention은 어떻게 구분해?
- metadata lock이랑 row lock은 뭐가 달라?
- deadlock error가 날 때 먼저 어떤 질문으로 분기해?
- DB가 잠겨 보일 때 triage 순서를 한 번에 보고 싶어
- blocker SQL 이 안 보여도 DB 내부 경합을 의심해야 하는 경우가 뭐야?
contextual_chunk_prefix: |
  이 문서는 운영에서 "DB가 잠겼다"는 한 문장 안에 row lock wait, deadlock,
  metadata lock, page latch contention이 섞여 있을 때 어떤 질문으로 분기하고
  어떤 완화책을 먼저 쓰는지 정리한 playbook이다. deadlock debugging,
  metadata lock vs row lock, hot page contention, db lock triage 같은 incident
  phrasing이 본 문서의 분류표와 대응된다.
---

# Lock Wait, Deadlock, and Latch Contention Triage Playbook

> 한 줄 요약: DB가 "잠겨서 느리다"는 증상은 row lock wait, deadlock, metadata lock, page latch contention이 섞여 보이는 경우가 많고, 해결책은 각기 다르다.

**난이도: 🔴 Advanced**

관련 문서:

- [Hibernate Lock SQL Log to Deadlock Triage Bridge](./hibernate-lock-sql-log-to-deadlock-triage-bridge.md)
- [DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표](../spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Metadata Lock and DDL Blocking](./metadata-lock-ddl-blocking.md)
- [B-Tree Latch Contention and Hot Pages](./btree-latch-contention-hot-pages.md)
- [Transaction Timeout vs Lock Timeout](./transaction-timeout-vs-lock-timeout.md)
- [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)

retrieval-anchor-keywords: lock wait triage, deadlock debugging, metadata lock, latch contention, hot page, lock timeout, wait graph, backend db incident response, deadlock vs self invocation, lock wait vs rollback-only, db lock vs spring proxy confusion

## 핵심 개념

운영에서 자주 듣는 표현은 비슷하다.

- "DB가 잠겼다"
- "쿼리가 멈춘다"
- "timeout이 난다"

하지만 실제 원인은 크게 다를 수 있다.

- row lock wait
- deadlock
- metadata lock
- page latch contention

이 넷은 모두 "기다린다"는 증상으로 보이지만, 진단 질문과 해결책은 다르다.
그래서 첫 대응은 튜닝이 아니라 **대기 유형 분류**다.

초급자라면 이 문서로 바로 들어오기보다, 애플리케이션 Hibernate 로그에서 blocker query나 deadlock 상대 SQL까지 연결하는 [Hibernate Lock SQL Log to Deadlock Triage Bridge](./hibernate-lock-sql-log-to-deadlock-triage-bridge.md)를 먼저 보고 오는 편이 덜 헷갈린다.

## 깊이 들어가기

### 1. row lock wait는 "누가 누구를 막고 있는가"가 핵심이다

전형적인 형태:

- 트랜잭션 A가 row를 잡고 오래 유지
- 트랜잭션 B가 같은 row/범위를 기다림

이 경우는 wait graph를 보면:

- blocker transaction
- waiting transaction
- 잡힌 row/인덱스 범위

가 비교적 명확하다.

주요 원인:

- 긴 transaction
- 외부 API가 transaction 안에 있음
- 범위가 큰 `FOR UPDATE`
- 배치와 실시간 요청 충돌

### 2. deadlock은 "기다림"이 아니라 "순환"이다

lock wait가 단순 직선 대기라면, deadlock은 원형 대기다.

- A가 B를 기다리고
- B가 A를 기다린다

DB는 보통 한쪽을 죽여 풀어 준다.
따라서 운영에서는 "느리다"보다 "갑자기 deadlock error가 튄다"로 보이는 경우가 많다.

핵심 대응은:

- 동일 순서 lock 획득
- transaction 축소
- 재시도 정책

이지, 단순 timeout 증가가 아니다.

### 3. metadata lock은 row가 아니라 schema를 둘러싼 대기다

DDL, long-running transaction, 일부 metadata read가 겹치면 metadata lock 대기가 생길 수 있다.

특징:

- `ALTER TABLE`이 갑자기 멈춘다
- row lock 정보만 봐서는 원인이 안 보인다
- 작은 DDL도 장시간 대기로 이어질 수 있다

즉 MDL은 "데이터 충돌"이 아니라 **스키마 가시성 충돌**에 가깝다.

### 4. latch contention은 logical lock이 아니라 내부 구조 경합이다

page latch나 internal mutex contention은:

- 특정 hot page에 insert/update가 몰리거나
- adaptive hash / buffer structure가 경합하거나
- 동일 index prefix가 뜨거울 때

주로 나타난다.

특징:

- lock wait graph에 blocker가 뚜렷하지 않을 수 있다
- timeout보다 CPU/throughput plateau로 보이기 쉽다
- row lock을 줄여도 해결되지 않을 수 있다

즉 latch contention은 transaction 설계보다 **키 분포와 index 구조**를 먼저 봐야 한다.

### 5. triage는 "대기 유형 -> 대표 질문 -> 즉시 완화책" 순서가 좋다

빠른 분류 기준:

| 증상 | 먼저 의심할 것 | 대표 질문 | 즉시 완화 |
|------|------|------|------|
| 특정 요청만 오래 멈춤 | row lock wait | 누가 blocker인가 | blocker 종료, tx 축소 |
| 에러가 간헐적으로 튐 | deadlock | lock 순서가 엇갈리나 | retry/backoff, 순서 통일 |
| DDL/배포 중 갑자기 멈춤 | metadata lock | long tx가 schema를 잡고 있나 | blocker 종료, 배포 재조정 |
| TPS가 특정 지점에서 평평 | latch contention | hot page/index prefix가 있나 | key 분산, index 구조 수정 |

### 6. timeout 숫자만 조정하면 원인을 더 가린다

흔한 대응 실수:

- lock wait timeout 증가
- transaction timeout 증가
- pool size 확장

이건 일부 증상을 늦출 수는 있지만:

- deadlock은 그대로
- MDL은 더 오래 막힘
- latch contention은 전혀 안 풀림

오히려 대기 시간을 늘려 blast radius를 키울 수 있다.

## 실전 시나리오

### 시나리오 1. 주문 API p99 급증

관찰:

- 몇 요청은 10초 이상 멈춤
- deadlock error는 없음

우선 의심:

- row lock wait
- 긴 transaction 또는 배치 충돌

### 시나리오 2. 배포 중 `ALTER TABLE`이 멈춤

관찰:

- 평소 트래픽은 큰 변화 없음
- DDL만 오래 걸림

우선 의심:

- metadata lock
- 오래 열린 read/write transaction

### 시나리오 3. insert TPS가 더 이상 안 올라감

관찰:

- timeout은 적음
- CPU는 높음
- throughput이 평평해짐

우선 의심:

- last-page hotspot
- page latch contention

## 코드로 보기

```sql
-- MySQL 계열 예시
SHOW ENGINE INNODB STATUS\G
SHOW FULL PROCESSLIST;
```

```sql
-- metadata lock 관찰 예시
SELECT *
FROM performance_schema.metadata_locks;
```

```text
관찰 체크리스트
- blocker transaction id
- waiting SQL shape
- timeout vs deadlock error 여부
- DDL 진행 여부
- hot index / hot page 징후
```

핵심은 "대기한다"는 사실보다, **무엇 때문에 기다리는지 분류**하는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| blocker kill | 즉시 완화가 쉽다 | 원인 해결은 아니다 | 운영 장애 완화 |
| timeout 증가 | 일시적 완화처럼 보인다 | 원인을 숨긴다 | 거의 신중해야 함 |
| transaction 축소 | lock wait를 줄인다 | 코드 변경이 필요하다 | row lock 중심 병목 |
| key/index 분산 | latch contention을 줄인다 | 구조 변경 비용이 크다 | hot page 병목 |

## 꼬리질문

> Q: lock wait와 deadlock의 차이는 무엇인가요?
> 의도: 단순 대기와 순환 대기를 구분하는지 확인
> 핵심: lock wait는 직선 대기이고, deadlock은 순환 대기여서 DB가 희생자를 고른다

> Q: metadata lock은 왜 row lock 디버깅으로 안 잡히나요?
> 의도: 스키마 가시성 대기의 성격을 이해하는지 확인
> 핵심: 보호 대상이 row가 아니라 metadata/DDL 가시성이기 때문이다

> Q: latch contention은 왜 timeout을 늘려도 해결되지 않나요?
> 의도: logical wait와 internal structure contention을 구분하는지 확인
> 핵심: 문제는 대기 정책이 아니라 hot page/index 구조 자체에 있기 때문이다

## 한 줄 정리

잠금 장애의 첫 단계는 "무슨 lock을 썼나"가 아니라, row wait·deadlock·metadata lock·latch contention 중 무엇이 실제 병목인지 분류하는 것이다.
