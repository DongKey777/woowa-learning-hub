---
schema_version: 3
title: Lock Timeout 났을 때 blocker 먼저 보는 미니카드
concept_id: database/lock-timeout-blocker-first-check
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
review_feedback_tags:
- lock-timeout-blocker
- first-check
- who-is-blocking
- lock-timeout
aliases:
- lock timeout blocker first check
- who is blocking lock timeout
- blocker 먼저 보는 미니카드
- lock wait blocker
- 갑자기 lock timeout
- 누구를 기다렸나
symptoms:
- 갑자기 트랜잭션이 다 lock timeout으로 떨어지고 있다
- "'Lock wait timeout exceeded' 에러가 특정 시간대에 자주 뜬다"
- lock timeout이 떨어지는데 그 SQL은 평소엔 빠르다
- pg_blocking_pids에 다른 트랜잭션이 보인다
intents:
- symptom
- troubleshooting
linked_paths:
- contents/database/db-timeout-first-splitter.md
- contents/database/deadlock-vs-lock-wait-timeout-primer.md
- contents/database/postgresql-55p03-nowait-vs-lock-timeout-beginner-card.md
- contents/database/connection-timeout-vs-lock-timeout-card.md
- contents/database/statement-timeout-vs-lock-timeout-card.md
- contents/database/pool-metrics-lock-wait-timeout-mini-bridge.md
- contents/database/spring-jpa-lock-timeout-deadlock-exception-mapping.md
- contents/database/lock-wait-deadlock-latch-triage-playbook.md
confusable_with:
- database/db-timeout-first-splitter
- database/deadlock-vs-lock-wait-timeout-primer
expected_queries:
- lock timeout이 났을 때 뭐부터 봐야 해?
- blocker가 누군지 어떻게 찾아?
- pg_blocking_pids로 lock timeout 원인을 어떻게 추적해?
- waiter와 blocker는 어떻게 구분해?
- connection timeout이나 statement timeout이 아니라 진짜 lock timeout인지 어떻게 먼저 가려?
contextual_chunk_prefix: |
  이 문서는 학습자가 lock timeout 또는 'Lock wait timeout exceeded' 에러를
  처음 만났을 때 SQL 자체보다 누가 막고 있었는지(blocker)를 먼저 찾는
  triage 순서를 잡는 symptom_router 미니카드다. 갑자기 lock timeout으로
  떨어진다, 트랜잭션이 다 막힌다, 특정 시간대 lock timeout, 누구를
  기다렸나, blocker first check 같은 자연어 paraphrase가 본 문서의 진단
  순서에 매핑된다.
---
# Lock Timeout 났을 때 blocker 먼저 보는 미니카드

> 한 줄 요약: `lock timeout`이 났다면 초보자 첫 질문은 "이 SQL이 느렸나?"보다 **"지금 누구를 기다렸나?"** 에 가깝다.

**난이도: 🟢 Beginner**

관련 문서:

- [PostgreSQL `55P03`에서 `NOWAIT`와 `lock_timeout`을 어떻게 나눠 읽을까?](./postgresql-55p03-nowait-vs-lock-timeout-beginner-card.md)
- [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- [Pool 지표 읽기 미니 브리지](./pool-metrics-lock-wait-timeout-mini-bridge.md)
- [Spring/JPA Lock Timeout vs Deadlock 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: lock timeout blocker first check, who is blocking lock timeout, lock wait timeout blocker beginner, blocker 먼저 어떻게 봐요, lock timeout 났을 때 뭐부터, lock timeout first checklist, pg_blocking_pids lock timeout basics, mysql 1205 blocker check, innodb blocker first look, postgres 55p03 blocker first look, who holds the row lock, lock timeout timeline checklist, why lock timeout who blocks, beginner lock timeout card

## 핵심 개념

`lock timeout`은 보통 "내 SQL이 혼자 느렸다"보다 **다른 트랜잭션이 먼저 잡은 row/range를 기다리다 예산이 끝났다**는 뜻에 가깝다.

그래서 초보자 첫 확인 순서는 이렇게 잡으면 된다.

1. 기다린 쪽이 누구인가
2. 막은 쪽(blocker)이 아직 살아 있나
3. blocker가 왜 오래 끝나지 않나

짧게 외우면:

- waiter = timeout 난 쪽
- blocker = 길을 안 비켜 준 쪽

비유로는 "한 줄 계산대"에 가깝지만, 실제 DB는 row lock, range lock, metadata lock처럼 잠그는 대상이 제품마다 다르다. 그래서 **blocker를 찾는 방법은 vendor/version별로 다를 수 있다**.

## 한눈에 보기

| 시각 | 무슨 일 | 초보자 해석 |
|---|---|---|
| `10:00:00` | 트랜잭션 A가 row를 갱신하고 아직 commit 안 함 | A가 blocker 후보 |
| `10:00:01` | 트랜잭션 B가 같은 row를 갱신 시도 | B가 waiter 후보 |
| `10:00:04` | B에서 `lock timeout` 발생 | "B가 느렸다"보다 "A를 기다리다 포기했다"에 가깝다 |
| `10:00:05` | A가 아직 실행 중 | 먼저 볼 대상은 B 쿼리 튜닝보다 A의 긴 트랜잭션 이유 |

한 줄 체크리스트:

1. timeout 난 SQL과 key를 적는다.
2. 같은 시각에 살아 있는 blocker 세션이 있는지 본다.
3. blocker가 잡은 채 오래 있는 이유를 본다.
4. 그다음에만 retry/timeout 값을 논한다.

## blocker 먼저 보는 4단계

### 1. timeout 난 SQL이 무엇을 기다렸는지 좁힌다

초보자는 에러 문장만 보고 끝내기 쉽다. 먼저 아래 둘을 적어 두면 blocker 추적이 쉬워진다.

- 어떤 SQL이 timeout 났나
- 어떤 row/key/table 근처에서 났나

예:

- `update inventory ... where sku_id = 44551`
- `select ... for update where seat_id = 12`

같은 `sku_id`, `seat_id`, 주문 번호가 반복되면 hot row 가능성이 높다.

### 2. blocker가 "지금도 살아 있는지"부터 본다

초보자 첫 질문은 "`EXPLAIN` 볼까요?"가 아니라 보통 아래가 더 맞다.

> "아직 끝나지 않은 선행 트랜잭션이 있나?"

이유:

- blocker가 이미 끝났다면 현재 화면만으로는 못 잡을 수 있다.
- blocker가 아직 열려 있으면, 긴 트랜잭션/외부 I/O/미완료 commit 같은 더 직접적인 원인을 바로 따라갈 수 있다.

즉 `lock timeout` 직후에는 **waiter보다 blocker 생존 여부**를 먼저 확인하는 편이 낭비가 적다.

### 3. blocker가 왜 긴지 본다

초보자 첫 원인 후보는 보통 이 셋이면 충분하다.

| blocker가 길어지는 흔한 이유 | 왜 오래 잡히나 | 첫 확인 포인트 |
|---|---|---|
| 긴 트랜잭션 | commit/rollback 전까지 락이 유지될 수 있다 | 한 요청이 몇 초 동안 transaction을 여는가 |
| 트랜잭션 안 외부 I/O | DB 작업이 끝나도 외부 호출이 끝날 때까지 락을 들고 있을 수 있다 | HTTP/API/파일 호출이 transaction 안에 있는가 |
| 같은 key 반복 경합 | 같은 row로 요청이 몰려 뒤 요청이 줄 선다 | `sku_id`, `seat_id`, `order_id`가 반복되는가 |

### 4. vendor별로 "무엇을 보면 blocker를 볼 수 있는지"만 짧게 기억한다

| DB/vendor | 초보자 첫 확인 포인트 | caveat |
|---|---|---|
| PostgreSQL | 보통 `pg_stat_activity`, `pg_blocking_pids()` 계열로 blocker 후보를 본다 | `55P03`는 lock timeout뿐 아니라 `NOWAIT` 실패도 같은 코드로 보일 수 있다 |
| MySQL/InnoDB | 보통 MySQL 8.0에서는 `performance_schema.data_lock_waits`/`data_locks`, 환경에 따라 `SHOW ENGINE INNODB STATUS`를 같이 본다 | 버전과 설정에 따라 보이는 뷰가 다르다. 오래된 가이드는 `information_schema.innodb_trx` 중심일 수 있다 |
| 공통 주의 | row lock만 보지 말고 transaction이 아직 열려 있는지 같이 본다 | metadata lock/DDL blocking은 row-lock 화면에 바로 안 보일 수 있다 |

핵심은 명령 암기가 아니라 **"blocker를 보는 관찰면이 제품마다 다르다"**는 점이다.

## 흔한 오해와 함정

- "`lock timeout`이면 timeout 난 SQL 자체가 느린 거다" -> 아닐 수 있다. 원래 빠른 SQL도 blocker를 오래 기다리면 timeout 난다.
- "waiter 로그만 보면 충분하다" -> 아니다. 원인은 blocker 쪽 긴 transaction에 있을 수 있다.
- "blocker가 안 보이면 lock 원인이 아니었다" -> 아니다. 이미 commit/rollback돼서 놓쳤을 수 있다.
- "PostgreSQL과 MySQL은 같은 화면만 보면 된다" -> 아니다. blocker 조회 뷰와 에러 코드 문맥이 다르다.
- "`55P03`면 항상 일반 lock timeout이다" -> 아니다. PostgreSQL에서는 `NOWAIT` 같은 fail-fast 락 시도도 같은 코드로 보일 수 있으니, blocker를 길게 기다렸다고 바로 단정하면 안 된다.

## 실무에서 쓰는 모습

```text
10:00:00 tx-A  update inventory set reserved = reserved + 1 where sku_id = 44551
10:00:01 tx-B  update inventory set reserved = reserved + 1 where sku_id = 44551
10:00:04 tx-B  lock timeout
10:00:05 tx-A  external coupon API still waiting
```

이 타임라인에서 초보자 첫 결론은 이렇다.

- 느려진 쪽은 `tx-B`지만
- 먼저 봐야 하는 쪽은 아직 끝나지 않은 `tx-A`다

즉 대응 시작점은:

1. `sku_id = 44551` 같은 key 반복 여부 확인
2. `tx-A`가 왜 아직 commit 안 했는지 확인
3. 외부 I/O를 transaction 밖으로 뺄 수 있는지 확인

이후에야 retry 정책이나 lock timeout 숫자를 조정할지 검토한다.

## 더 깊이 가려면

- blocker가 row lock인지 pool 연쇄인지 먼저 떼려면 [Connection Timeout vs Lock Timeout 비교 카드](./connection-timeout-vs-lock-timeout-card.md)
- 실행 지연과 락 대기를 다시 나누려면 [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- PostgreSQL `55P03`를 `NOWAIT`와 `lock_timeout`으로 먼저 분리하려면 [PostgreSQL `55P03`에서 `NOWAIT`와 `lock_timeout`을 어떻게 나눠 읽을까?](./postgresql-55p03-nowait-vs-lock-timeout-beginner-card.md)
- Spring 예외 이름 하나로 뭉개져 보일 때는 [Spring/JPA Lock Timeout vs Deadlock 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)

## 면접/시니어 질문 미리보기

> Q: blocker를 찾았는데 SQL이 빠른데도 왜 오래 잠그나요?
> 핵심: SQL 자체보다 transaction 범위, 외부 I/O, commit 지연 때문에 락 보유 시간이 길 수 있다.

> Q: blocker가 안 보이면 lock timeout 원인을 부정할 수 있나요?
> 핵심: 아니다. timeout 뒤 이미 끝난 blocker를 놓쳤을 수 있고, vendor별 관찰면도 다르다.

## 한 줄 정리

`lock timeout`이 나면 초보자 첫 액션은 쿼리 튜닝보다 **"지금 누구를 기다렸고, 그 blocker가 왜 오래 살아 있나?"** 를 먼저 보는 것이다.
