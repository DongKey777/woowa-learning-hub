---
schema_version: 3
title: DB Timeout 첫 분류 결정 가이드
concept_id: database/db-timeout-first-splitter
canonical: false
category: database
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- timeout-bucket-first
- pool-vs-lock-vs-statement-timeout
- timeline-before-retry
aliases:
- db timeout first split
- connection timeout vs lock timeout vs statement timeout
- pool timeout vs lock timeout vs statement timeout
- 어떤 timeout을 먼저 봐야 하나
- timeout first failure chooser
- borrow timeout lock wait statement timeout
symptoms:
- timeout 이름은 많은데 어디서 막힌 건지 모르겠다
- Connection is not available와 Lock wait timeout exceeded를 같은 원인으로 보고 있다
- statement timeout이 보이면 무조건 느린 쿼리라고 생각한다
intents:
- comparison
- troubleshooting
prerequisites:
- database/connection-pool
- database/lock-basics
- database/transaction-basics
next_docs:
- database/connection-pool
- database/lock-timeout-blocker-first-check
- database/deadlock-vs-lock-wait-timeout-primer
linked_paths:
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/statement-timeout-vs-lock-timeout-card.md
- contents/database/timeout-log-timeline-first-failure-checklist-card.md
- contents/database/lock-timeout-blocker-first-check-mini-card.md
- contents/database/slow-query-analysis-playbook.md
- contents/database/connection-pool-basics.md
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
confusable_with:
- database/connection-pool
- database/lock-timeout-blocker-first-check
- database/deadlock-vs-lock-wait-timeout-primer
forbidden_neighbors:
- contents/database/connection-pool-basics.md
- contents/database/slow-query-analysis-playbook.md
expected_queries:
- 커넥션 풀 timeout이랑 lock timeout이랑 statement timeout 중에 어디부터 분류해?
- Connection is not available가 떴는데 느린 쿼리로 봐야 해?
- query canceled due to statement timeout이면 lock 문제는 아닌 거야?
- 같은 요청에서 57014랑 55P03이 같이 보이면 뭐부터 읽어?
- pool 대기와 DB 락 대기를 한 장으로 구분한 문서 있어?
contextual_chunk_prefix: |
  이 문서는 학습자가 connection timeout, lock timeout, statement timeout이
  한 요청 주변에서 섞여 보일 때 무엇이 첫 실패인지 분류하는 chooser다.
  Connection is not available, lock wait timeout exceeded, query canceled due
  to statement timeout, 55P03, 57014 같은 로그를 보고 어느 줄에서
  막혔는지 먼저 가르려는 질문이 본 문서의 결정 표와 오선택 패턴에 매핑된다.
---

# DB Timeout 첫 분류 결정 가이드

## 한 줄 요약

> `connection timeout`은 앱 풀 입구, `lock timeout`은 DB 락 줄, `statement timeout`은 SQL 실행 예산에서 실패한 신호라서 먼저 실패한 지점을 갈라야 한다.

## 결정 매트릭스

| 지금 먼저 보이는 신호 | 기다린 위치 | 초보자 첫 질문 | 바로 갈 문서 |
|---|---|---|---|
| `Connection is not available`, `waiting>0`, borrow timeout | 애플리케이션 커넥션 풀 | 커넥션이 왜 늦게 반환되지? | [커넥션 풀 기초](./connection-pool-basics.md) |
| `Lock wait timeout exceeded`, `55P03`, blocker 흔적 | DB 내부 row/key 락 대기 | 누가 같은 row나 key를 오래 잡고 있지? | [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md) |
| `query canceled due to statement timeout`, 큰 scan/sort 흔적 | SQL 실행 시간 예산 | 혼자 실행해도 이 쿼리가 느린가? | [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md) |
| 같은 요청에 둘 이상이 섞여 보임 | 시간축 재분류 필요 | 어떤 로그가 먼저 찍혔지? | [Timeout 로그 타임라인 체크리스트 카드](./timeout-log-timeline-first-failure-checklist-card.md) |

`deadlock`은 이 표의 세 timeout과 다르다. timeout이 아니라 순환 대기 해소 실패라서, `deadlock victim`이 먼저 보이면 [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md)로 분기하는 편이 맞다.

## 흔한 오선택

`statement timeout`이 보였다고 바로 "느린 쿼리 하나만 고치면 된다"로 닫기 쉽다. 하지만 앞줄에 `55P03`가 먼저 있으면 시작점은 락 대기일 수 있다. 이름보다 로그 순서를 먼저 읽어야 한다.

`Connection is not available`를 DB 락 문제와 같은 말로 섞는 경우도 많다. 이 신호는 DB 안까지 들어가기 전에 앱 풀 입구에서 커넥션을 못 빌린 상황일 수 있어서, 긴 트랜잭션이나 트랜잭션 안의 외부 I/O를 먼저 봐야 할 때가 많다.

`lock timeout`을 `deadlock`과 같은 retry 버킷으로 넣는 것도 흔한 오선택이다. `deadlock`은 순환 대기라 transaction 전체 retry가 후보가 되지만, `lock timeout`은 blocker가 그대로면 같은 자리에서 다시 막힐 수 있다.

## 다음 학습

세 갈래 중 풀 입구 대기가 먼저였으면 [커넥션 풀 기초](./connection-pool-basics.md)와 [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)로 이어서 본다.

DB 락 줄에서 막힌 쪽이면 [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)와 [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)를 같이 보면 재분류가 빨라진다.

실행 시간이 오래 걸린 쪽이면 [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)로 내려가고, `deadlock`까지 섞여 보이면 [Deadlock vs Lock Wait Timeout 입문 프라이머](./deadlock-vs-lock-wait-timeout-primer.md)로 따로 분리해서 본다.
