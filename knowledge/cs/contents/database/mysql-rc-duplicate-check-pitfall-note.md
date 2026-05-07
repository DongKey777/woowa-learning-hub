---
schema_version: 3
title: MySQL RC Duplicate-Check Pitfall Note
concept_id: database/mysql-rc-duplicate-check-pitfall-note
canonical: true
category: database
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- read-committed
- duplicate-check
- unique-backstop
- exact-key-probe
aliases:
- mysql rc duplicate check pitfall
- mysql read committed duplicate race
- rr downgrade duplicate error surge
- read committed exact key precheck
- duplicate precheck under RC
- why duplicate errors increase after read committed
- 왜 RC로 내리니 duplicate 늘어남
- MySQL duplicate precheck beginner
- RR에서만 duplicate check가 막혀요
symptoms:
- MySQL REPEATABLE READ에서 조용하던 exact-key pre-check가 READ COMMITTED 전환 뒤 duplicate-key error를 더 많이 드러내
- UNIQUE는 그대로인데 SELECT FOR SHARE pre-check가 missing key queue를 덜 만들어 둘 다 INSERT까지 달려
- duplicate correctness를 pre-check가 아니라 UNIQUE와 duplicate handling 중심으로 다시 정리해야 해
intents:
- troubleshooting
- definition
prerequisites:
- database/mysql-rr-exact-key-probe-visual-guide
- database/empty-result-locking-cheat-sheet-postgresql-mysql
next_docs:
- database/mysql-gap-lock-blind-spots-read-committed
- database/upsert-contention-unique-index-locking
- database/mysql-duplicate-key-retry-handling-cheat-sheet
linked_paths:
- contents/database/mysql-rr-exact-key-probe-visual-guide.md
- contents/database/empty-result-locking-cheat-sheet-postgresql-mysql.md
- contents/database/mysql-gap-lock-blind-spots-read-committed.md
- contents/database/upsert-contention-unique-index-locking.md
- contents/database/mysql-duplicate-key-retry-handling-cheat-sheet.md
- contents/database/unique-vs-locking-read-duplicate-primer.md
confusable_with:
- database/mysql-rr-exact-key-probe-visual-guide
- database/mysql-gap-lock-blind-spots-read-committed
- database/unique-vs-locking-read-duplicate-primer
forbidden_neighbors: []
expected_queries:
- MySQL에서 READ COMMITTED로 내리니 duplicate key error가 늘어난 이유가 뭐야?
- RR exact-key pre-check가 RC에서 missing key queue를 못 만드는 흐름을 초보자용으로 설명해줘
- UNIQUE는 그대로인데 duplicate race가 INSERT 지점으로 더 많이 올라오는 이유를 알려줘
- SELECT FOR SHARE pre-check를 correctness가 아니라 조기 감지로 봐야 하는 이유가 뭐야?
- RC duplicate check pitfall을 upsert나 duplicate handling 중심으로 어떻게 고쳐?
contextual_chunk_prefix: |
  이 문서는 MySQL REPEATABLE READ exact-key pre-check가 READ COMMITTED에서 약해져 duplicate-key error가 INSERT 시점으로 더 많이 드러나는 beginner primer다.
  RC로 내리니 duplicate 늘어남, read committed duplicate race, UNIQUE backstop 질문이 본 문서에 매핑된다.
---
# MySQL RC Duplicate-Check Pitfall Note

> 한 줄 요약: MySQL `REPEATABLE READ`에서 exact-key duplicate pre-check가 잠깐 줄을 세워 주던 느낌은 `READ COMMITTED`로 내리면 크게 사라진다. 그래서 `UNIQUE`는 그대로인데도 duplicate race와 duplicate-key error가 더 자주 눈에 띈다.

**난이도: 🟢 Beginner**

관련 문서:

- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [database 카테고리 인덱스](./README.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: mysql rc duplicate check pitfall, mysql read committed duplicate race, rr downgrade duplicate error surge, read committed exact key precheck, mysql unique duplicate check beginner, why duplicate errors increase after read committed, mysql rr exact key rc downgrade, duplicate check felt safe under rr, read committed duplicate key retry increase, mysql exact-key duplicate check primer, 왜 rc로 내리니 duplicate 늘어남, mysql duplicate precheck beginner, mysql rc duplicate check pitfall note basics, mysql rc duplicate check pitfall note beginner, mysql rc duplicate check pitfall note intro

## 핵심 개념

초보자용으로 가장 단순하게 기억하면 이렇다.

- `REPEATABLE READ`의 exact-key pre-check는 가끔 "먼저 줄을 세우는 안내선"처럼 보인다
- `READ COMMITTED`로 내리면 그 안내선이 약해져서 더 많은 요청이 `INSERT` 지점까지 같이 도착한다
- correctness의 마지막 문은 여전히 pre-check가 아니라 `UNIQUE`다

즉 RC 전환 뒤 duplicate 관련 로그가 늘었다면, 보통은 **`UNIQUE`가 약해진 것**이 아니라 **RR이 앞단에서 조금 숨겨 주던 경쟁이 `INSERT` 시점으로 더 많이 올라온 것**이다.

## 한눈에 보기

| 장면 | 실제로 달라진 것 | 운영에서 보이는 현상 | 기억할 점 |
|---|---|---|---|
| RR + exact-key pre-check + `UNIQUE` | pre-check가 같은 key slot 주변을 잠깐 줄 세울 수 있다 | duplicate race가 앞단에서 조금 덜 보인다 | "안전"보다 "완충"에 가깝다 |
| RC + exact-key pre-check + `UNIQUE` | search gap 보호를 기대하기 어렵다 | duplicate-key error, retry, 재조회가 더 자주 보인다 | `UNIQUE`는 그대로지만 queue가 줄었다 |
| RC + exact-key pre-check + no `UNIQUE` | 마지막 backstop이 없다 | 진짜 duplicate row가 생길 수 있다 | pre-check만으로는 부족하다 |
| RR/RC + one-statement insert/upsert + `UNIQUE` | arbitration이 write 시점으로 모인다 | 결과 해석이 더 단순해진다 | duplicate safety를 SQL write path에 둔다 |

## 왜 RR에서는 "꽤 안전해 보였나"

보통 문제의 코드는 이런 모양이다.

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR SHARE;

INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (:coupon_id, :member_id);
```

`UNIQUE(coupon_id, member_id)`가 있고, pre-check도 같은 full key를 그대로 타면 RR에서는 exact-key probe가 그 key slot 주변을 잠깐 붙잡는 장면이 나올 수 있다.

그래서 팀은 흔히 이렇게 느낀다.

1. 먼저 조회한 트랜잭션이 "`(coupon_id, member_id)` 자리를 예약했다"
2. 뒤늦은 트랜잭션은 앞단에서 기다릴 것이다
3. 그래서 duplicate race가 거의 없는 것처럼 보인다

이 체감은 완전히 틀린 것은 아니지만, **항상 맞는 계약**은 아니다. RR이 만들어 주는 것은 비즈니스 의미 전체 보호라기보다 **같은 index slot을 먼저 건드린 세션 사이의 임시 queue**에 더 가깝다.

## RC로 내리면 무엇이 바뀌나

RC에서는 locking read가 보통 **찾은 index record** 위주로 잠그고, search gap 보호는 기대하기 어렵다. 그래서 exact-key pre-check가 `0 row`를 보면, 두 세션이 모두 "없다"고 판단한 뒤 `INSERT`까지 달릴 수 있다.

여기서 많이 헷갈리는 포인트가 하나 있다.

- 문서에서 RC에서도 duplicate-key checking 때문에 일부 gap lock 예외가 남는다고 설명한다
- 하지만 그 예외는 보통 **`INSERT`가 실제로 unique 충돌을 검사하는 순간** 쪽 이야기다
- 즉, **앞단의 `SELECT ... FOR SHARE/UPDATE`가 missing key를 예약해 준다는 뜻은 아니다**

초보자 기준으로는 이렇게 외우는 편이 덜 틀린다.

> RR에서는 pre-check가 queue를 조금 만들어 줄 수 있지만, RC에서는 그 queue를 `SELECT`가 거의 만들어 주지 못한다. 대신 `UNIQUE`가 `INSERT` 순간 최종 승자를 고른다.

## 같은 코드가 RR과 RC에서 어떻게 다르게 보이나

### RR에서 자주 보이는 흐름

1. 트랜잭션 A가 exact-key pre-check를 한다
2. A가 같은 key slot 주변 경쟁을 먼저 잡는다
3. 트랜잭션 B는 pre-check나 insert 단계에서 기다리거나, 나중에 duplicate를 본다
4. 애플리케이션은 "pre-check가 꽤 잘 막아 준다"고 느낀다

### RC에서 더 자주 보이는 흐름

1. 트랜잭션 A가 pre-check를 하고 `0 row`를 본다
2. 트랜잭션 B도 거의 동시에 같은 `0 row`를 본다
3. 둘 다 `INSERT`를 시도한다
4. `UNIQUE`가 있으면 한쪽이 duplicate-key error를 맞는다
5. `UNIQUE`가 없으면 둘 다 들어가서 실제 duplicate가 된다

즉 RC 전환 뒤 흔히 늘어나는 것은 "`없으면 insert` 경쟁" 그 자체다.
RR에서는 이 경쟁이 안 보였던 것이 아니라, **조금 더 앞 단계에서 완충되고 있었을 뿐**이다.

## 흔한 오해

- "`READ COMMITTED`가 `UNIQUE`를 약하게 만든다"
  - 아니다. `UNIQUE`는 그대로다. 약해진 것은 pre-check가 만드는 앞단 queue다.
- "duplicate-key error가 늘었으니 RC가 더 위험하다"
  - `UNIQUE`가 있으면 오히려 race가 더 명확하게 surface된 것일 수 있다.
- "`FOR UPDATE`로 바꾸면 다시 RR처럼 된다"
  - missing exact key를 RC에서 읽을 때는 lock 세기보다 isolation과 index path가 더 중요하다.
- "그럼 pre-check는 다 지워야 하나"
  - 사용자 친화적인 빠른 안내나 로그용 early check로는 남길 수 있다. 다만 correctness를 맡기면 안 된다.

## 실무에서 이렇게 정리하면 덜 흔들린다

1. `UNIQUE`를 duplicate safety의 진짜 기준선으로 둔다.
2. exact-key pre-check는 "조기 감지"나 "친절한 메시지" 용도로만 해석한다.
3. 가능하면 `INSERT`/`upsert` 한 문장 또는 duplicate-key handling을 중심 write path로 둔다.
4. RR에서 RC로 내릴 때는 exact-key 경로의 `EXPLAIN`과 동시성 재현 테스트를 다시 돌린다.

짧게 말하면, RR에서 안전해 보이던 duplicate check는 종종 **`SELECT`가 안전해서**가 아니라 **RR이 잠깐 queue를 만들어 줘서** 그랬다. RC로 내리면 그 queue가 줄고, 그 결과 duplicate race가 더 눈에 띄게 올라온다.

## 더 이어서 보면 좋은 문서

- RR exact-key queue 직관을 그림처럼 먼저 잡으려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- `0 row` locking read를 exact duplicate와 overlap으로 같이 비교하려면 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- RC에서 gap/next-key blind spot을 더 깊게 보려면 [MySQL Gap-Lock Blind Spots Under READ COMMITTED](./mysql-gap-lock-blind-spots-read-committed.md)
- duplicate handling을 read-before-write 대신 write path 중심으로 옮기려면 [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)

## 한 줄 정리

MySQL에서 RR exact-key duplicate pre-check는 가끔 앞단 queue처럼 보이지만, RC로 내리면 그 queue가 약해져 duplicate race가 `INSERT` 지점으로 더 많이 올라오고, 최종 안전성은 결국 `UNIQUE`가 책임진다.
