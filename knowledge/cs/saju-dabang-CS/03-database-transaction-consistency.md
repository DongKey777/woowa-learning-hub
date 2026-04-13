# 03. 데이터베이스: 트랜잭션, 정합성, 멱등성

## CS-study와 연결

- 데이터베이스 기본: `/Users/idonghun/IdeaProjects/woowa-2026/knowledge/cs/CS-study/contents/database/README.md`

사주다방은 DB 이론이 실제로 중요한 프로젝트다.  
특히 **결제, 코인, 운세 생성 상태** 때문에 정합성이 핵심이다.

## 1. 왜 PostgreSQL이 중요한가

사주다방 서버는 다음 데이터를 DB에 저장한다.

- 사용자
- 로그인 세션
- 코인 거래
- IAP 주문
- 운세 생성 job
- 운세 결과
- LLM 로그

즉 DB는 단순 저장소가 아니라 서비스의 source of truth다.

## 2. 트랜잭션은 어디서 중요한가

### 코인 적립

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`

핵심 흐름:

1. `transactions` insert
2. `users.coins` update
3. `purchase_orders` upsert
4. `coin_ledger` insert

이게 한 흐름으로 묶여야:

- 거래는 기록됐는데 잔액이 안 바뀌는 문제
- 잔액은 바뀌었는데 주문 상태가 안 남는 문제

를 막을 수 있다.

### 운세 생성 reserve -> capture -> refund

사주다방은 운세 시작 전에 코인을 먼저 차감 예약한다.

- reserve: `transactions.status = 'reserved'`
- 성공 완료: `completed`
- 실패/환불: `refunded`

이건 전형적인 상태 전이 문제다.

관련 코드:

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingReservationApplicationService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingFinalizationApplicationService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingRefundApplicationService.java`

## 3. 멱등성(idempotency)은 어떻게 보장하나

결제/재시도는 네트워크 때문에 중복 요청이 흔하다.  
그래서 같은 요청이 여러 번 와도 결과가 한 번만 반영되어야 한다.

관련 코드:

- `transactions.order_id`
- `coin_ledger.idempotency_key`

예:

```sql
ON CONFLICT (order_id) DO NOTHING
```

의미:

- 같은 `orderId`로 결제 적립이 두 번 들어와도
- 실제 적립은 한 번만 됨

이게 면접에서 말하는 **멱등성 보장**이다.

## 4. `transactions`와 `coin_ledger`를 왜 둘 다 쓰나

이건 좋은 면접 포인트다.

- `transactions`
  - 실제 사용자 거래 흐름
  - reserve / completed / refunded 상태 전이
- `coin_ledger`
  - 회계/감사 trail
  - idempotency key 기반 중복 방지
  - `capture(amount=0)` 같은 감사 기록

즉 둘은 비슷해 보여도 역할이 다르다.

## 5. 정규화보다 중요한 것: 실서비스 정합성

이 프로젝트에선 정규화만으로 설명이 안 끝난다.

왜냐면:

- 돈(코인)이 걸려 있고
- 생성 상태가 중간 실패할 수 있고
- 재시도와 복구가 필요하기 때문

그래서 DB 설계는 “예쁘게 나누는 것”보다
**실패했을 때도 데이터가 모순되지 않게 만드는 것**이 더 중요하다.

## 6. 면접 답변 예시

**Q. 트랜잭션이 왜 필요한가요?**  
A. “사주다방에서는 코인 적립 시 거래 기록, 잔액 업데이트, 주문 상태 저장, ledger 기록이 함께 일어납니다. 이 중 일부만 반영되면 데이터가 깨지므로 트랜잭션으로 묶어야 합니다.”

**Q. 멱등성은 어떻게 보장했나요?**  
A. “같은 orderId가 여러 번 들어와도 중복 적립되지 않도록 `transactions.order_id`와 `coin_ledger.idempotency_key`를 사용해 한 번만 반영되게 만들었습니다.”
