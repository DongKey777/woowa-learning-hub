# MySQL Duplicate-Key Retry Handling Cheat Sheet

> 한 줄 요약: MySQL `duplicate key` (`1062`)는 보통 "같은 exact key의 승자가 이미 정해졌다"는 뜻이라서, 같은 `INSERT`를 계속 재시도하기보다 **승자 row를 fresh read로 확인해 `already exists` / `busy` 버킷으로 먼저 맞추고, `already exists` 안에서 idem replay와 `409 conflict`를 가르는 쪽**이 맞다.

**난이도: 🟢 Beginner**

관련 문서:

- [Insert-if-Absent 로그 읽기 예시 프라이머](./insert-if-absent-log-reading-examples-primer.md)
- [Spring Insert-if-Absent SQLSTATE Cheat Sheet](./spring-insert-if-absent-sqlstate-cheat-sheet.md)
- [MySQL `1062` 후 Fresh-Read 경로 미니 시퀀스 다이어그램](./mysql-1062-fresh-read-mini-sequence-diagram.md)
- [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)
- [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md)
- [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: mysql duplicate key retry cheat sheet, mysql 1062 handling, duplicate key already exists, same insert retried, same insert retried duplicate key, same payload replay, different payload conflict, duplicate key fresh read, duplicate key retry or read, already exists vs serialization failure, duplicate key 뭐예요, duplicate key basics, idempotency key replay, mysql unique key create once, beginner duplicate key primer

`1062 -> primary/fresh read -> replay|busy|conflict` 흐름을 한 장 시퀀스로 먼저 보고 싶다면 [MySQL `1062` 후 Fresh-Read 경로 미니 시퀀스 다이어그램](./mysql-1062-fresh-read-mini-sequence-diagram.md)부터, 같은 내용을 표와 코드로 더 짧게 보고 싶다면 [DuplicateKeyException 이후 Fresh-Read 재분류 미니 카드](./duplicate-key-fresh-read-classifier-mini-card.md)부터 보면 된다.

## Beginner 연결표 (경계/재시도 카드로 확장)

`1062` 분류를 끝낸 뒤 다음 질문으로 바로 이어갈 수 있게 최소 동선을 표로 정리한다.

| 다음 질문 | 바로 볼 카드 | 연결 이유 |
|---|---|---|
| "경계가 길어서 timeout/중복 해석이 더 꼬이는 건 아닐까?" | [트랜잭션 경계 체크리스트 카드](./transaction-boundary-external-io-checklist-card.md) | 외부 I/O가 경계 안에 있으면 busy/재시도 신호가 급격히 늘어난다 |
| "duplicate/timeout/deadlock/serialization을 한 표로 보고 싶다" | [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md) | 서비스 결과 3버킷(`already exists`/`busy`/`retryable`)으로 고정해 준다 |
| "PostgreSQL `40001`은 왜 트랜잭션 전체 재시도인가?" | [PostgreSQL SERIALIZABLE Retry Playbook for Beginners](./postgresql-serializable-retry-playbook.md) | MySQL duplicate와 다른 retry 단위를 비교해 헷갈림을 줄여 준다 |

## 핵심 개념

용어 뜻을 먼저 한 장으로 맞추고 싶으면 [3버킷 공통 용어 카드](./three-bucket-terms-common-card.md)를 먼저 보고 오면 된다.

초보자 기준으로는 `UNIQUE`를 개찰구로 떠올리면 된다.

- 내가 먼저 통과하면 `INSERT` 성공이다.
- 다른 요청이 먼저 통과했는데 내가 같은 key로 들어오면 MySQL `1062`를 받는다.
- 그 순간 DB는 "누가 이겼는지 아직 모른다"가 아니라 **"승자는 이미 있다"** 쪽에 더 가깝게 말하고 있다.

그래서 `duplicate key`를 받았을 때의 기본 질문은 "`INSERT`를 또 던질까?"가 아니다.

> "이 winner가 내 요청과 같은 의미인가, 아직 처리 중인가, 아니면 다른 payload라서 충돌인가?"

이 질문에 답한 뒤 결과를 **3버킷 용어에 먼저 맞춘다**.

- winner가 완료된 같은 요청이면 `already exists`
- winner가 아직 끝나지 않았으면 `busy`
- 같은 key를 다른 의미로 재사용한 것이면 `already exists`로 분류한 뒤 서비스 계약에서 `409 conflict`로 응답한다

초급자 기준으로는 "`already exists`와 `409 conflict`는 같은 말이 아니다"를 먼저 분리해 두면 덜 헷갈린다.

- `already exists`는 DB가 말하는 상태 버킷이다
- `409 conflict`는 그 버킷 안에서 서비스가 고르는 응답 형태 중 하나다

## 가장 작은 예시로 먼저 보기

가장 작은 mental model은 "`사물함 번호`와 `사물함 내용물`"이다.

- `idempotency_key`는 사물함 번호다.
- payload/hash는 그 사물함에 넣으려는 내용물이다.
- `duplicate key`는 "그 번호의 사물함은 이미 누가 썼다"는 뜻이다.

그다음에는 내용물이 같은지만 보면 된다.

| 장면 | winner read에서 보는 것 | 초급자 해석 | 서비스 응답 |
|---|---|---|---|
| 같은 key + 같은 payload | 이미 같은 내용물이 들어 있다 | 아까 요청을 다시 보냈다 | 이전 성공 응답 replay |
| 같은 key + 다른 payload | 같은 번호 사물함에 다른 내용물을 넣으려 한다 | key 재사용 충돌이다 | `409 conflict` |

아주 작은 HTTP 예시로 보면 더 분명하다.

```http
POST /payments
Idempotency-Key: pay-101

{ "amount": 1000, "orderId": "A-1" }
```

첫 요청이 성공해 winner row를 만들었다고 하자.

같은 요청을 네트워크 재전송으로 한 번 더 보내면:

```http
POST /payments
Idempotency-Key: pay-101

{ "amount": 1000, "orderId": "A-1" }
```

- DB 관점: same key winner already exists
- 서비스 관점: same meaning이므로 replay

그런데 같은 key로 payload를 바꿔 보내면:

```http
POST /payments
Idempotency-Key: pay-101

{ "amount": 9000, "orderId": "A-9" }
```

- DB 관점: 여전히 same key winner already exists
- 서비스 관점: 다른 meaning이므로 `409 conflict`

핵심은 둘 다 DB에서는 먼저 "`already exists`" 쪽인데, **winner row를 읽고 나서야** replay와 `409 conflict`가 갈린다는 점이다.

## 3버킷 표기로 먼저 맞추기

이 문서는 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)와 같은 축을 쓰기 위해 outcome 라벨을 아래처럼 맞춘다.

| duplicate 뒤 장면 | 3버킷 outcome | 서비스 응답 예시 | 초급자 기억법 |
|---|---|---|---|
| 같은 idempotency key + 같은 request hash + 완료된 winner row | `already exists` | 이전 성공 응답 재사용 (`200`/`201`) | 이미 끝난 승자를 다시 본다 |
| 같은 idempotency key + 같은 request hash + winner가 아직 `PROCESSING` | `busy` | `202 Accepted`, `409 in-progress`, `Retry-After` | 승자는 있지만 아직 끝나지 않았다 |
| 같은 unique key + 다른 payload/hash | `already exists` | `409 conflict` | key는 이미 쓰였고, 의미가 달라 충돌한다 |

여기서 `retryable`이 안 보이는 이유는 이 문서가 **`1062 duplicate key` 한정 치트시트**이기 때문이다.
`deadlock`/`serialization failure`처럼 새 트랜잭션으로 다시 가는 경우는 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)에서 `retryable`로 본다.

## 한눈에 보기

| duplicate 상황 | 3버킷 outcome | 권장 응답 | 무엇을 retry하나 |
|---|---|---|---|
| 같은 idempotency key + 같은 request hash + 완료된 winner row | `already exists` | 이전 성공 응답 재사용 (`200`/`201` 계약 유지) | 보통 retry 없음 |
| 같은 idempotency key + 같은 request hash + winner가 아직 `PROCESSING` | `busy` | `202 Accepted`, `409 in-progress`, `Retry-After` 중 계약에 맞는 값 | insert가 아니라 조회/폴링 |
| 같은 business unique key + 같은 도메인 의미 | `already exists` | 기존 resource 반환, 혹은 idem 응답 | 보통 retry 없음 |
| 같은 unique key + 다른 payload/hash | `already exists` | `409 conflict` | retry 없음 |
| `1062` 뒤 winner 조회가 안 보임 | `busy`로 재분류 전 확인 단계 | 짧은 fresh-read retry 후 재분류 | `INSERT`가 아니라 fresh read만 retry |

짧은 기억법:

- `1062`는 대개 **retry to win**이 아니라 **read to classify**다.
- retry가 필요해도 보통 다시 넣는 retry가 아니라 **winner를 다시 읽는 retry**다.

## same-key replay vs different-payload conflict

초급자가 가장 많이 헷갈리는 지점만 작은 표로 다시 고정하면 아래와 같다.

| 질문 | same-key replay | different-payload conflict |
|---|---|---|
| key는 같은가 | 같다 | 같다 |
| payload/hash는 같은가 | 같다 | 다르다 |
| DB가 먼저 말하는 것 | winner already exists | winner already exists |
| winner read 다음 결론 | "이미 처리된 같은 요청" | "같은 key를 다른 뜻으로 썼다" |
| 보통 응답 | 이전 결과 replay | `409 conflict` |

한 줄로 줄이면:

- same key + same payload = 재전송
- same key + different payload = 충돌

그래서 `409 conflict`는 "`duplicate key`가 났다"만으로 바로 정하지 않는다.
반드시 winner row의 `request_hash`나 canonical payload fingerprint를 읽고 정한다.

## `already exists` vs `40001` 빠른 분리

검색에서는 "`이미 있어서 다시 보는 경우`"와 "`이번 시도를 버리고 다시 시작하는 경우`"가 자주 섞인다. 초급자는 아래 표만 먼저 고정해 두면 된다.

| 질문 | MySQL `1062 duplicate key` | PostgreSQL `40001 serialization failure` |
|---|---|---|
| 지금 본 신호의 뜻 | winner가 이미 있다 | 이번 snapshot 판단이 깨졌다 |
| 먼저 할 일 | winner row fresh read | 새 transaction으로 전체 재시도 |
| 같은 insert를 그대로 다시 넣나 | 보통 아니오 | 새 시도 안에서 결과적으로 다시 실행될 수 있다 |
| 서비스 결과 라벨 | `already exists` 또는 `busy` 재분류 | `retryable` |
| 초급자 기억법 | 이미 결론 난 경쟁 | 결론을 다시 계산해야 하는 경쟁 |

한 줄로 줄이면 이렇다.

- `1062`는 "누가 이겼는지 이미 정해졌다"에 가깝다.
- `40001`은 "내 판단이 오래돼서 이번 시도를 통째로 다시 해야 한다"에 가깝다.

## duplicate key를 먼저 문장으로 번역하기

MySQL에서는 보통 `errno 1062`, `SQLSTATE 23000`이 `duplicate key` 축이다. beginner 기준으로 아래 세 신호만 분리해도 실수가 크게 줄어든다.

| 신호 | 먼저 읽어야 할 문장 | 기본 대응 |
|---|---|---|
| `1062 duplicate key` | "같은 exact key의 winner가 이미 있다" | fresh read로 winner 확인 후 `already exists`/`busy`로 먼저 맞추고, `already exists` 안에서 idem/conflict 분기 |
| `1205 lock wait timeout` | "누가 이길지 아직 못 본 채 기다림 예산이 끝났다" | busy 또는 짧은 whole-attempt retry |
| `1213 deadlock` | "이번 시도만 희생양이 됐다" | whole-transaction bounded retry |

즉 `1062`는 `1205`, `1213`과 같은 retry bucket에 넣으면 안 된다.

- `1205`, `1213`은 "다시 시도하면 이번엔 될 수도 있다" 쪽이다.
- `1062`는 "같은 key로 다시 넣어도 같은 winner가 다시 보일 가능성이 크다" 쪽이다.

그래서 exact-key write path에서는 **duplicate를 retry 정책이 아니라 응답 번역 정책**으로 먼저 본다.

## exact-key write path별 처리

### 1. idempotency key 테이블

가장 전형적인 구조는 `(idempotency_key)`에 `UNIQUE`를 두고, `request_hash`, `status`, `response_body`를 같이 저장하는 방식이다.

- 같은 key, 같은 hash면: 같은 요청 재전송으로 본다
- 같은 key, 다른 hash면: 같은 key를 다른 요청에 재사용한 것이므로 `409 conflict`
- 같은 key, 같은 hash인데 status가 `PROCESSING`이면: 먼저 들어온 요청이 아직 끝나지 않은 상태

즉 duplicate 이후 follow-up read에서 `request_hash`를 꼭 같이 봐야 한다.

### 2. business unique key

`(coupon_id, member_id)`, `external_order_id`, `email` 같은 business key도 exact-key write path다. 다만 해석은 idempotency key와 조금 다르다.

- "같은 key면 같은 성공" 계약이면: existing row를 canonical 결과로 재사용
- "같은 key 재사용은 오류" 계약이면: `409 conflict`

예를 들어 `external_order_id`는 idem 성공으로 번역하기 쉽지만, `email`은 "이미 다른 사용자가 쓰고 있다"는 conflict가 더 자연스럽다.

핵심은 `duplicate key` 자체가 `200`이나 `409`를 자동으로 결정해 주지 않는다는 점이다. **그 key가 도메인에서 무슨 의미인지**가 응답을 정한다.

### 3. `INSERT ... ON DUPLICATE KEY UPDATE`

이 문장은 편리하지만 beginner가 가장 쉽게 오해하는 축이기도 하다.

- 같은 payload를 안전하게 재적용하는 경우에는 괜찮다
- 다른 payload를 조용히 덮어쓰면 conflict를 숨길 수 있다

따라서 "duplicate면 그냥 update"는 idempotency와 conflict를 한 바구니에 섞을 위험이 있다. exact-key create API라면 먼저 **duplicate를 읽어서 계약대로 번역하는 흐름**이 더 안전하다.

## 실무에서 쓰는 모습

가장 단순한 service 흐름은 "write 시도"와 "duplicate 번역"을 분리하는 것이다.

```java
public CreatePaymentResponse create(CreatePaymentCommand cmd) {
    try {
        return paymentWriteTx.insertOnce(cmd);
    } catch (DuplicateKeyException e) {
        return duplicateTranslator.translate(cmd);
    }
}
```

```java
public CreatePaymentResponse translate(CreatePaymentCommand cmd) {
    PaymentRow row = primaryReadService.findByIdempotencyKey(cmd.idempotencyKey());

    if (row == null) {
        return retryPrimaryReadOnce(cmd);
    }
    if (!row.requestHash().equals(cmd.requestHash())) {
        throw new ConflictException("same key, different payload");
    }
    if (row.isProcessing()) {
        return CreatePaymentResponse.inProgress(row.retryAfterSeconds());
    }
    return CreatePaymentResponse.replay(row.responseBody());
}
```

이 흐름에서 중요한 점은 네 가지다.

1. `DuplicateKeyException`이 나면 같은 `INSERT`를 바로 다시 던지지 않는다.
2. winner lookup은 가능하면 primary 또는 read-your-writes가 보장되는 경로로 읽는다.
3. 같은 트랜잭션의 오래된 snapshot이 winner를 못 볼 수 있으면 fresh read로 분리한다.
4. 분류 기준은 `request_hash`, `status`, business key 의미다.

## 흔한 오해와 함정

- "`1062`면 deadlock처럼 whole-transaction retry하면 된다"
  - 아니다. 같은 key가 남아 있으면 같은 `1062`만 반복될 가능성이 크다.
- "`duplicate key`면 무조건 `409 conflict`다"
  - 아니다. idempotency key 재전송은 오히려 성공 재사용이 맞는 경우가 많다.
- "`already exists`와 `409 conflict`는 같은 라벨이다"
  - 아니다. `already exists`는 3버킷 분류이고, `409 conflict`는 그 안에서 "같은 key지만 다른 의미"일 때 고르는 서비스 응답이다.
- "`already exists`면 무조건 이전 결과를 그대로 돌려주면 된다"
  - 아니다. same-key replay인지, same-key different-payload conflict인지 winner read로 한 번 더 갈라야 한다.
- "`409 conflict`는 DB가 바로 알려 준다"
  - 아니다. DB는 대개 "이미 같은 key가 있다"까지만 알려 준다. `409` 여부는 서비스가 winner payload를 읽고 정한다.
- "duplicate 뒤 조회가 안 보이면 row가 없는 것이다"
  - replica lag, stale snapshot, rollback-only transaction, 잘못된 read path일 수 있다. fresh read로 한 번 더 확인해야 한다.
- "`ON DUPLICATE KEY UPDATE`면 멱등성이 자동으로 끝난다"
  - 아니다. 같은 key에 다른 payload가 왔을 때도 update가 실행되면 conflict를 잃어버릴 수 있다.

## 더 깊이 가려면

- duplicate vs lock timeout vs deadlock 분류를 한 장으로 이어서 보려면 [Insert-if-Absent Retry Outcome Guide](./insert-if-absent-retry-outcome-guide.md)
- exact duplicate correctness에서 `UNIQUE`와 locking read 역할 차이를 먼저 다지려면 [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- duplicate 뒤 winner read가 왜 replica에서 흔들릴 수 있는지 보려면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)
- replay-safe idempotency 저장소 설계까지 넓히려면 [Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
- client retry budget과 `Retry-After`까지 붙여 보려면 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

## 면접/시니어 질문 미리보기

> Q. MySQL `1062`를 왜 deadlock retry bucket과 분리하나요?
> 의도: "winner already exists"와 "attempt can be retried"를 구분하는지 본다.
> 핵심: `1062`는 exact key 승자가 이미 정해졌다는 뜻이어서 응답 번역이 먼저다.

> Q. 같은 unique key인데 언제 `already exists` replay이고, 언제 `409 conflict`인가요?
> 의도: 3버킷 분류와 HTTP/API 응답을 같은 축으로 착각하지 않는지 본다.
> 핵심: 둘 다 DB 쪽에서는 `already exists`이지만, same key + same meaning이면 replay, same key + different meaning이면 conflict다.

> Q. duplicate 뒤 follow-up read는 왜 fresh read/primary read가 필요할 수 있나요?
> 의도: snapshot, replica lag, read-your-writes 문제를 같이 떠올리는지 본다.
> 핵심: 현재 attempt가 winner를 못 봐도 DB에 winner가 없는 것은 아닐 수 있다.

## 한 줄 정리

MySQL exact-key write path에서 `duplicate key`는 보통 "다시 insert해서 이겨라"가 아니라 "이미 생긴 winner를 fresh read로 확인해 `already exists` / `busy`로 먼저 분류하고, `already exists` 안에서 replay나 `409 conflict`를 고르라"는 신호다.
