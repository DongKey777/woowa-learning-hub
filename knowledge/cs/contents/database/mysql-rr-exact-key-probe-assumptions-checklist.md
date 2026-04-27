# MySQL RR exact-key probe assumptions checklist

> 한 줄 요약: MySQL `REPEATABLE READ`에서 "같은 key면 줄이 선다"는 감각은 **같은 index path**와 **같은 write protocol**이 유지될 때만 맞다. 이 문서는 그 가정이 깨졌는지 빠르게 점검하는 beginner checklist다.

**난이도: 🟢 Beginner**

관련 문서:

- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)
- [MySQL REPEATABLE READ Safe-Range Checklist](./mysql-repeatable-read-safe-range-checklist.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mysql rr exact key probe assumptions checklist, same key queue intuition breaks, index path drift duplicate check, mixed write path duplicate check, mysql repeatable read same key not queued, exact key probe checklist beginner, explain checklist same key path, duplicate precheck mixed writer, full unique key equality checklist, mysql rr path drift checklist, 왜 같은 키인데 안 막혀요, rr exact key 가정 체크리스트, 같은 key queue 착시, mixed write path locking read

## 핵심 개념

먼저 아주 단순하게 보면 된다.

- RR exact-key probe는 "`같은 business key`를 잠근다"가 아니라 "`같은 index slot`을 먼저 건드리면 잠깐 줄이 설 수 있다"에 가깝다.
- 그래서 두 요청이 정말 같은 slot을 만지는지, 둘 다 같은 절차로 들어오는지가 중요하다.
- 마지막 안전장치는 여전히 `UNIQUE`다.

초보자 기억법은 이 한 줄이면 충분하다.

> "`같은 key`처럼 보여도 실제로는 다른 길로 들어오면 RR queue 직관은 바로 깨진다."

## 30초 체크리스트

| 질문 | 예 / 아니오 판단 | 아니오면 무슨 뜻인가 |
|---|---|---|
| 1. probe query가 full `UNIQUE` key equality인가 | `coupon_id = ? AND member_id = ?`처럼 full key를 그대로 쓴다 | exact-key가 아니라 prefix/range일 수 있다 |
| 2. `EXPLAIN key`가 intended `UNIQUE` index인가 | 기대한 인덱스 이름이 그대로 보인다 | index-path drift가 났을 수 있다 |
| 3. `EXPLAIN rows`가 거의 `1` 근처인가 | 거의 한 칸만 보는 lookup이다 | 이미 넓은 scan이라 same-key intuition이 과장일 수 있다 |
| 4. 다른 writer도 같은 probe를 먼저 타는가 | API, batch, admin tool이 같은 arbitration surface를 쓴다 | mixed write path라 queue surface를 우회한다 |
| 5. 격리수준이 정말 RR인가 | 해당 경로가 `REPEATABLE READ`로 돈다 | RC나 다른 경로에서는 same-key queue가 약해진다 |
| 6. correctness backstop으로 `UNIQUE`가 있는가 | duplicate write를 DB가 끝까지 막는다 | probe가 흔들리면 바로 중복 위험으로 이어진다 |

위 표에서 하나라도 `아니오`면 "`RR이라 같은 key는 줄이 선다`"는 설명을 멈추는 편이 맞다.

## 언제 특히 잘 깨지나

### 1. index-path drift가 났을 때

겉으로는 같은 duplicate check처럼 보여도 실제 접근 경로가 달라지면 lock footprint도 달라진다.

- 함수가 끼었다: `LOWER(email) = LOWER(?)`
- full composite key 대신 일부만 쓴다
- 새 인덱스 추가 뒤 optimizer가 다른 `key`를 골랐다
- 정렬, 조인, 추가 조건 때문에 probe 전용 query가 아니게 됐다

이때 beginner가 바로 할 일은 추측이 아니라 `EXPLAIN` 확인이다.

- `key`가 intended `UNIQUE` 인덱스인지 본다
- `rows`가 거의 한 칸인지 본다
- 어긋나면 exact-key queue 가정을 중지한다

### 2. mixed write path가 있을 때

한 경로는 probe 후 insert하고, 다른 경로는 바로 insert하면 같은 key queue surface가 깨진다.

대표 장면은 이렇다.

- 사용자 API: `SELECT ... FOR SHARE` 후 `INSERT`
- 운영 배치: probe 없이 바로 `INSERT`
- 관리 도구: 다른 predicate로 기존 row를 먼저 조회

이 경우 RR exact-key probe는 일부 경로에서만 보조 queue가 되고, 시스템 전체 규칙은 아니다.

초보자용 질문은 하나다.

> "모든 writer가 정말 같은 문 앞에서 줄을 서나?"

대답이 `아니오`면 `UNIQUE`와 retry/fresh-read 설계가 주인공이어야 한다.

## 가장 흔한 착시 3개

| 착시 | 실제 해석 |
|---|---|
| 같은 SQL 텍스트니까 같은 잠금이다 | lock footprint는 chosen index path를 따른다 |
| 테스트에서 한 번 막혔으니 앞으로도 막힌다 | plan drift, RC 전환, writer 추가가 오면 바로 달라진다 |
| probe가 있으니 duplicate correctness도 끝났다 | correctness backstop은 `UNIQUE`다 |

## 작은 예시

### 예시 A. 직관이 비교적 맞는 경우

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR SHARE;
```

- `UNIQUE(coupon_id, member_id)`가 있다
- `EXPLAIN key = uq_coupon_member`
- 모든 writer가 이 probe 뒤에 insert한다

이 장면에서는 RR에서 같은 key insert가 잠시 대기하는 체감이 나올 수 있다.

### 예시 B. 직관이 깨지는 경우

```sql
SELECT 1
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND LOWER(member_email) = LOWER(:email)
FOR SHARE;
```

- 함수 때문에 intended unique-key path가 깨질 수 있다
- 어떤 배치는 probe 없이 바로 insert한다
- 그러면 "같은 key면 줄이 선다"는 설명이 더 이상 시스템 전체에 맞지 않는다

이 장면에서는 probe를 보조 장치로만 보고, `UNIQUE` + duplicate handling을 중심에 둬야 한다.

## 실무에서 바로 남길 메모

코드 리뷰나 운영 문서에 아래 네 줄만 적어도 초보자 혼란이 많이 줄어든다.

1. intended `UNIQUE` index 이름
2. `EXPLAIN key/type/rows`
3. 이 경로를 타는 writer 목록
4. "`queueing 보조일 뿐, correctness는 `UNIQUE`가 맡는다`"는 문장

## 다음에 어디로 가면 좋은가

- "`정말 같은 index path를 타는지`"를 바로 확인하려면 [EXPLAIN Checklist for Exact-Key Locking Reads](./explain-checklist-exact-key-locking-reads.md)
- RR exact-key probe가 왜 same-key queue처럼 보이는지 그림으로 다시 보려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- duplicate correctness와 queueing 보조를 분리해서 잡으려면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- RC로 내리면 왜 이 직관이 더 빨리 깨지는지 보려면 [MySQL RC Duplicate-Check Pitfall Note](./mysql-rc-duplicate-check-pitfall-note.md)
