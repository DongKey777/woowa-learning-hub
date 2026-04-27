# MySQL `ON DUPLICATE KEY UPDATE` Safety Primer

> 한 줄 요약: `INSERT ... ON DUPLICATE KEY UPDATE`는 "같은 key면 한 줄만 남긴다"는 점에서는 편하지만, **같은 요청의 재시도**를 흡수할 때만 멱등성에 가깝고 **같은 key에 다른 payload가 들어온 충돌**까지 안전하게 해결해 주지는 않는다.

**난이도: 🟢 Beginner**

관련 문서:

- [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [Duplicate Key vs Busy Response Mapping](./duplicate-key-vs-busy-response-mapping.md)
- [Unique Claim 이후 Existing Row 재사용 Primer](./unique-claim-existing-row-reuse-primer.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: mysql on duplicate key update primer, mysql upsert safety, on duplicate key update idempotency, same key different payload conflict, mysql idempotency key beginner, mysql upsert overwrite risk, duplicate key hides conflict, upsert no-op update, request hash conflict detection, mysql upsert beginner primer, mysql same request retry safe, mysql same key different value unsafe, mysql insert on duplicate key update payment example, mysql on duplicate key update safety primer basics, mysql on duplicate key update safety primer beginner

## 먼저 멘탈모델

이 문장을 먼저 고정하면 덜 헷갈린다.

- `ON DUPLICATE KEY UPDATE`는 **같은 unique key 충돌을 SQL 한 문장 안에서 처리**하는 문법이다
- 하지만 그 문법이 **비즈니스 의미까지 판단**해 주지는 않는다

즉 MySQL은 보통 이렇게만 안다.

- "이 key는 이미 있다"
- "그러면 insert 대신 update 하겠다"

MySQL은 보통 이것까지는 모른다.

- "이번 요청이 지난번과 완전히 같은 재시도인가?"
- "아니면 같은 key를 다른 뜻으로 다시 쓴 충돌인가?"

그래서 초보자는 `upsert = 멱등성 해결`로 외우면 안 된다.

> 안전한 경우: 같은 요청을 다시 보냈고, update가 결과를 바꾸지 않는다
> 위험한 경우: 같은 key인데 payload가 달라졌는데도 update가 조용히 덮어쓴다

## 30초 판단표

| 장면 | 멱등성 관점 | 왜 그런가 |
|---|---|---|
| 같은 key, 같은 payload 재시도, update가 사실상 no-op | 대체로 안전 | 첫 결과를 다시 확인한 것과 비슷하다 |
| 같은 key, 같은 payload 재시도, `updated_at`만 갱신 | 보통 안전 | 핵심 비즈니스 값은 안 바뀐다 |
| 같은 key, 다른 payload인데 `amount = new.amount`로 덮어씀 | 위험 | 충돌을 에러로 드러내지 않고 마지막 값으로 바꿔 버린다 |
| 같은 key, 다른 payload인데 `request_hash` 비교 후 거절 | 더 안전 | "재시도"와 "충돌"을 구분한다 |
| 같은 key, 누적식 update (`count = count + 1`) | 멱등하지 않다 | 재시도만으로도 결과가 달라진다 |

핵심은 하나다.

> `same key`와 `same request`는 같은 말이 아니다.

## 가장 단순한 예시

결제 요청을 저장한다고 하자.

```sql
CREATE TABLE payment_request (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  idempotency_key VARCHAR(64) NOT NULL,
  request_hash CHAR(64) NOT NULL,
  amount BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  UNIQUE KEY uk_payment_request_idem (idempotency_key)
);
```

이제 초보자가 흔히 쓰는 SQL은 이런 모양이다.

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  amount,
  status,
  created_at,
  updated_at
) VALUES (
  :idempotency_key,
  :request_hash,
  :amount,
  'SUCCEEDED',
  NOW(),
  NOW()
)
ON DUPLICATE KEY UPDATE
  request_hash = VALUES(request_hash),
  amount = VALUES(amount),
  status = VALUES(status),
  updated_at = NOW();
```

겉보기에는 편하다.
하지만 이 SQL은 **같은 key에 다른 금액이 와도 조용히 덮어쓸 수 있다.**

예를 들어:

1. 첫 요청: `idempotency_key='pay-1'`, `amount=10000`
2. 재전송 버그 또는 잘못된 재사용: `idempotency_key='pay-1'`, `amount=50000`

이때 MySQL은 "같은 key네"까지만 보고 update path로 간다.
비즈니스 관점의 질문인 "같은 요청인가?"는 앱이 직접 답해야 한다.

## 언제 멱등성에 가깝게 동작하나

### 1. duplicate 경로가 사실상 no-op일 때

예:

```sql
INSERT INTO payment_request (
  idempotency_key,
  request_hash,
  amount,
  status,
  created_at,
  updated_at
) VALUES (
  :idempotency_key,
  :request_hash,
  :amount,
  'SUCCEEDED',
  NOW(),
  NOW()
)
ON DUPLICATE KEY UPDATE
  updated_at = updated_at;
```

이 경우 duplicate path는 row를 실질적으로 바꾸지 않는다.
같은 요청 재시도라면 "이미 있던 결과를 유지"하는 쪽에 가깝다.

단, 이것만으로 충분하지는 않다.
같은 key에 다른 payload가 들어왔는지는 여전히 따로 확인해야 한다.

### 2. 처음 값만 보존하겠다는 정책이 분명할 때

예:

```sql
ON DUPLICATE KEY UPDATE
  updated_at = NOW();
```

핵심 컬럼인 `amount`, `request_hash`, `status`는 안 바꾸고 시간만 기록한다면
"첫 승자의 값 보존"이라는 정책이 비교적 분명하다.

이 패턴은 이런 경우에 잘 맞는다.

- 같은 API 요청의 네트워크 재시도
- 이미 성공한 결과를 다시 replay해야 하는 멱등성 경로
- "새 요청이 기존 값을 덮으면 안 된다"가 중요한 경로

### 3. 앱에서 hash 비교로 재시도와 충돌을 나눌 때

가장 많이 권장되는 초급자 패턴은 이것이다.

1. `idempotency_key` unique로 한 줄만 잡는다
2. duplicate가 나면 기존 row를 읽는다
3. `request_hash`가 같으면 같은 요청 재시도로 본다
4. `request_hash`가 다르면 conflict로 본다

짧게 말하면:

- key는 "같은 자리인가?"
- hash는 "정말 같은 요청인가?"

둘 다 있어야 안전성이 올라간다.

## 언제 조용히 충돌을 숨기나

### 1. 마지막 요청이 이긴다고 착각하게 만들 때

아래 SQL은 가장 위험한 입문형 예시다.

```sql
ON DUPLICATE KEY UPDATE
  amount = VALUES(amount),
  status = VALUES(status);
```

문제는 이것이다.

- DB는 에러를 내지 않는다
- 서비스는 성공처럼 보일 수 있다
- 하지만 실제로는 **같은 key를 다른 payload가 덮어쓴 충돌**일 수 있다

즉 duplicate를 "중복 재시도 흡수"가 아니라
"같은 키면 마지막 값으로 갱신"으로 써 버리면 멱등성이 깨진다.

### 2. 누적식 update를 duplicate path에 넣을 때

예:

```sql
ON DUPLICATE KEY UPDATE
  retry_count = retry_count + 1;
```

이 패턴은 재시도 횟수 기록용 보조 컬럼이라면 괜찮을 수 있다.
하지만 핵심 비즈니스 값이 이런 식이면 멱등하지 않다.

예:

```sql
ON DUPLICATE KEY UPDATE
  quantity = quantity + VALUES(quantity);
```

같은 요청을 한 번 더 보냈을 뿐인데 수량이 두 번 반영될 수 있다.
이건 "중복 흡수"가 아니라 "재시도 증폭"에 가깝다.

### 3. 상태 전이 규칙 없이 status를 덮어쓸 때

예를 들어 첫 요청은 이미 `SUCCEEDED`인데,
늦게 도착한 다른 요청이 duplicate path에서 `FAILED`나 `CANCELED`로 덮어쓰면 문제가 된다.

그래서 status를 update할 때는 보통 이런 질문이 필요하다.

- 정말 허용된 상태 전이인가?
- 첫 성공 이후에는 더 이상 바꾸면 안 되는가?
- duplicate 재시도라면 기존 결과를 돌려줘야 하는가?

초보자 관점에서는 **status를 아무 조건 없이 덮어쓰지 않는다**부터 기억하면 충분하다.

## 초보자용 안전한 기본 흐름

| 단계 | 추천 기본 동작 | 이유 |
|---|---|---|
| 1 | `idempotency_key`에 unique key를 둔다 | 같은 key 경합을 DB 한 곳으로 모은다 |
| 2 | 첫 insert는 요청 hash와 함께 저장한다 | 나중에 진짜 같은 요청인지 비교할 수 있다 |
| 3 | duplicate가 나면 기존 row를 다시 읽는다 | 바로 성공 처리하지 말고 winner 의미를 확인한다 |
| 4 | hash가 같으면 기존 결과 replay | 같은 요청 재시도이므로 멱등성에 가깝다 |
| 5 | hash가 다르면 conflict로 거절 | 같은 key 재사용 버그를 숨기지 않는다 |

애플리케이션에서 보면 이런 흐름이다.

```text
insert 시도
-> 성공: 새 요청 처리
-> duplicate 발생: 기존 row read
   -> hash 같음: 기존 결과 반환
   -> hash 다름: 충돌로 거절
```

이 흐름이 중요한 이유는 `ON DUPLICATE KEY UPDATE`만으로는
"같은 요청"과 "같은 key를 잘못 재사용한 다른 요청"을 구분할 수 없기 때문이다.

## 자주 하는 오해

- "`ON DUPLICATE KEY UPDATE`면 멱등성이 보장된다"
  - 아니다. 같은 key 충돌을 처리할 뿐, payload 충돌을 판별하지는 않는다.
- "duplicate path에서 최신 값으로 덮으면 더 편하다"
  - 편하지만 재시도와 충돌이 섞여 버린다.
- "에러가 안 났으니 안전하다"
  - 아니다. 가장 위험한 경우는 충돌이 조용히 성공처럼 지나가는 경우다.
- "같은 key면 같은 요청이다"
  - 아니다. key 재사용 버그, 클라이언트 버그, 잘못된 retry 구현이 있으면 다른 요청일 수 있다.

## 한 줄 규칙 4개

1. `same key`는 `same request`가 아니다.
2. duplicate path가 핵심 값을 바꾸지 않을수록 멱등성에 가깝다.
3. 다른 payload를 조용히 덮어쓰면 conflict를 숨긴다.
4. 초보자 기본형은 `unique key + request hash + duplicate 후 재조회`다.

## 다음에 이어서 볼 문서

- 멱등성 키 저장소 전체 설계를 보려면 [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
- duplicate 이후 기존 row를 어떻게 재사용하는지 보려면 [Unique Claim 이후 Existing Row 재사용 Primer](./unique-claim-existing-row-reuse-primer.md)
- lock 경합까지 포함한 upsert의 더 깊은 설명은 [Upsert Contention, Unique Index Arbitration, and Locking](./upsert-contention-unique-index-locking.md)

## 한 줄 정리

`INSERT ... ON DUPLICATE KEY UPDATE`는 "같은 key면 한 줄만 남긴다"는 점에서는 편하지만, **같은 요청의 재시도**를 흡수할 때만 멱등성에 가깝고 **같은 key에 다른 payload가 들어온 충돌**까지 안전하게 해결해 주지는 않는다.
