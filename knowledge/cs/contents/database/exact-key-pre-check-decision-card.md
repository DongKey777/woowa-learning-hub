# Exact-Key Pre-Check Decision Card

> 한 줄 요약: beginner 기준으로 exact-key insert-if-absent는 먼저 `UNIQUE`를 두고, "기존 row를 읽어 바로 이어 처리해야 하는가"가 있을 때만 locking pre-check를 더하며, 그조차 없다면 pre-check는 아예 생략하는 편이 더 단순하고 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- [FOR SHARE vs FOR UPDATE Duplicate Check Note](./for-share-vs-for-update-duplicate-check-note.md)
- [UNIQUE vs Slot Row vs Guard Row 빠른 선택 가이드](./unique-vs-slot-row-vs-guard-row-quick-chooser.md)
- [PostgreSQL Exact-Key Pre-Check Contrast Card](./postgresql-exact-key-precheck-contrast-card.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: exact key pre check decision card, unique only vs locking precheck vs skip precheck, mysql duplicate precheck chooser, exact key insert if absent chooser, when to skip precheck, when to add locking read precheck, unique only beginner, select for update before insert beginner, duplicate precheck decision table, exact key duplicate check card, mysql unique locking primer, 중복 사전조회 결정 카드, unique만 쓰는 경우, pre-check 생략 기준, locking pre-check 추가 기준, exact key 없으면 insert 판단표, mysql duplicate check chooser

## 먼저 잡을 그림

exact-key 문제에서는 문이 세 개 있다고 생각하면 쉽다.

- `UNIQUE`: 마지막 문이다. 같은 key에 **승자 1명**만 통과시킨다.
- locking pre-check: 앞 복도다. 어떤 장면에서는 contender를 잠깐 줄 세운다.
- pre-check 생략: 복도 자체를 없애고 바로 문으로 간다.

초급자 기본 원칙은 이렇다.

> correctness는 `UNIQUE`가 맡고, pre-check는 꼭 필요할 때만 붙인다.

즉 질문 순서는 "`FOR UPDATE`를 넣을까?"가 아니라 아래 순서가 더 낫다.

1. exact key를 `UNIQUE`로 정확히 표현할 수 있는가
2. insert 전에 **기존 row를 읽어 이어 처리할 이유**가 있는가
3. 그 이유가 없다면 pre-check를 빼는 편이 더 단순한가

## 30초 선택표

| 지금 상황 | 기본 선택 | 이유 |
|---|---|---|
| 목표가 "같은 key 하나만 막기"다 | `UNIQUE` only | 승패는 write 시점에 제일 정확하게 난다 |
| existing row를 읽어 상태/결과를 바로 재사용해야 한다 | `UNIQUE` + locking pre-check | pre-check가 duplicate 방지의 주인공은 아니지만, 기존 row 관찰과 queueing 보조에는 쓸모가 있다 |
| insert 전에 읽을 가치가 거의 없고 loser는 `duplicate key` 후 fresh read로 충분하다 | pre-check 생략 | 쿼리 수와 오해를 줄이고, backstop을 `UNIQUE` 하나로 고정할 수 있다 |

핵심 기억법:

- "한 명만 성공"이면 언제나 `UNIQUE`가 먼저다
- "먼저 읽을 row가 실제로 필요하다"면 그때만 pre-check를 생각한다
- "어차피 insert 후 loser 처리로 끝난다"면 pre-check를 빼는 편이 낫다

## 언제 `UNIQUE` only가 맞나

이 장면이 beginner의 기본값이다.

- `idempotency_key`
- `(user_id, coupon_id)`
- `email`
- 외부 주문 번호처럼 exact key가 이미 선명한 경우

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue_coupon_member
UNIQUE (coupon_id, member_id);
```

```sql
INSERT INTO coupon_issue(coupon_id, member_id)
VALUES (:coupon_id, :member_id);
```

이때 loser는 보통 `duplicate key`를 받는다.
애플리케이션은 이를 `already exists` 같은 정상 경쟁 결과로 번역하면 된다.

이 선택이 특히 좋은 이유:

- 설명이 가장 짧다
- 엔진 차이에 덜 흔들린다
- "`0 row FOR UPDATE`가 정말 보호되나?" 같은 혼란을 많이 줄인다

## 언제 locking pre-check를 추가하나

pre-check는 "`UNIQUE`가 약해서" 추가하는 것이 아니다.
보통 아래 이유가 있을 때만 붙인다.

| 추가 이유 | pre-check가 주는 것 | 그래도 남는 사실 |
|---|---|---|
| 기존 row가 있으면 그 결과를 바로 보여 주고 싶다 | insert 전 existing row 확인 | 최종 승자는 여전히 `UNIQUE`가 정한다 |
| 같은 key 경합에서 앞단 queue를 조금 만들고 싶다 | MySQL `REPEATABLE READ`에서 제한적 보조 가능 | isolation/path가 바뀌면 체감이 바로 흔들린다 |
| existing row를 읽은 뒤 상태 전이를 이어 처리해야 한다 | 읽은 row에 대한 lock ownership 확보 | `0 row` 장면까지 완전히 보호된다는 뜻은 아니다 |

예를 들면 이런 흐름이다.

```sql
SELECT status
FROM coupon_issue
WHERE coupon_id = :coupon_id
  AND member_id = :member_id
FOR UPDATE;
```

여기서 row를 찾았다면, 그 row의 상태를 보고 "이미 발급됨", "처리 중", "재사용 가능" 같은 분기가 가능하다.

하지만 `0 row`였다고 해서 pre-check가 duplicate correctness를 끝내 주는 것은 아니다.
insert 경쟁의 마지막 판정은 여전히 `UNIQUE`가 한다.

## 언제 pre-check를 아예 생략하나

아래 셋 중 둘 이상이 맞으면 beginner는 pre-check를 빼는 편이 보통 낫다.

- existing row를 insert 전에 읽어도 바로 쓸 정보가 거의 없다
- loser가 `duplicate key`를 받은 뒤 fresh read 해도 UX가 충분하다
- MySQL `REPEATABLE READ` queueing 보조에 강하게 기대고 싶지 않다

짧은 예시는 이렇다.

```java
try {
    couponIssueRepository.insert(couponId, memberId);
    return IssueResult.issued();
} catch (DuplicateKeyException e) {
    return couponIssueRepository.findByCouponIdAndMemberId(couponId, memberId)
        .map(IssueResult::alreadyIssued)
        .orElse(IssueResult.busy());
}
```

이 방식은 "먼저 조회 -> 없네 -> insert"를 줄여서 다음 장점이 있다.

- read/write race 설명이 단순해진다
- pre-check path drift를 덜 걱정해도 된다
- PostgreSQL/MySQL 차이를 덜 안고 간다

## 자주 하는 오해

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 나은 기억법 |
|---|---|---|
| "`FOR UPDATE`를 넣으면 `UNIQUE`가 거의 필요 없다" | empty-result exact-key 장면은 엔진과 isolation 영향을 크게 받는다 | `UNIQUE`는 마지막 문, pre-check는 앞 복도다 |
| "pre-check가 있으면 더 안전하니 무조건 넣자" | 쿼리 수만 늘고 correctness 설명은 오히려 흐려질 수 있다 | 이유가 없으면 생략이 더 낫다 |
| "`duplicate key`는 실패니까 먼저 막아야 한다" | exact-key 경합에서는 정상 loser signal일 때가 많다 | duplicate를 제어 흐름으로 번역한다 |

## 아주 짧은 선택 순서

1. exact key를 `UNIQUE`로 닫는다.
2. insert 전에 읽을 existing row가 정말 필요한지 묻는다.
3. 필요하면 locking pre-check를 추가한다.
4. 필요 없으면 pre-check를 생략하고 `duplicate key -> fresh read` 경로로 끝낸다.

## 바로 옆으로 이어 읽기

- "왜 기본값이 `UNIQUE`인가?"를 먼저 굳히려면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- MySQL RR에서 pre-check가 왜 가끔 queue처럼 보이는지 보려면 [MySQL RR exact-key probe visual guide](./mysql-rr-exact-key-probe-visual-guide.md)
- `0 row FOR UPDATE` 직관이 왜 위험한지 보려면 [Empty-Result Locking Cheat Sheet for PostgreSQL and MySQL](./empty-result-locking-cheat-sheet-postgresql-mysql.md)
- PostgreSQL에서는 같은 chooser를 어떻게 더 보수적으로 읽어야 하는지 보려면 [PostgreSQL Exact-Key Pre-Check Contrast Card](./postgresql-exact-key-precheck-contrast-card.md)

## 한 줄 정리

exact-key beginner 기본값은 `UNIQUE` only이고, insert 전에 읽을 existing row가 실제로 필요할 때만 locking pre-check를 더하며, 그 이유가 없다면 pre-check를 아예 생략하는 편이 더 단순하고 덜 헷갈린다.
