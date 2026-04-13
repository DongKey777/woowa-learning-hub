# 트랜잭션과 멱등성

## 트랜잭션

결제 적립은 여러 단계가 함께 성공해야 한다.

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`

흐름:

1. `transactions` insert
2. `users.coins` update
3. `purchase_orders` upsert
4. `coin_ledger` insert

이 중 하나만 실패하면 데이터 모순이 생긴다.

## 멱등성

같은 요청이 여러 번 와도 결과가 한 번만 반영되어야 한다.

예:
- 같은 `orderId`
- 같은 `idempotency_key`

핵심 SQL:

```sql
ON CONFLICT (order_id) DO NOTHING
```

## 실제 코드 스니펫

사주다방 Java 백엔드의 적립 코드 핵심은 아래와 같다.

```java
Integer inserted = jdbcClient.sql(
    """
      INSERT INTO transactions (id, user_id, type, amount, order_id, status)
      VALUES (:id, :userId, :type, :amount, :orderId, 'completed')
      ON CONFLICT (order_id) WHERE order_id IS NOT NULL DO NOTHING
      RETURNING 1
      """
  )
  .param("id", txnId)
  .param("userId", userId)
  .param("type", type)
  .param("amount", amount)
  .param("orderId", orderId)
  .query(Integer.class)
  .optional()
  .orElse(null);

if (inserted == null) {
  return new CreditApplyResult(balanceOf(userId), true);
}
```

관련 원본:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`

이 코드의 의미:

1. 같은 `orderId`로 이미 들어간 적 있으면 insert 안 함
2. 이미 처리된 주문이면 현재 잔액만 반환
3. 따라서 클라이언트 재시도에도 중복 적립이 안 됨

## 트랜잭션과 멱등성은 다른 개념

- 트랜잭션
  - 여러 작업을 묶어서 전부 성공/실패 보장
- 멱등성
  - 같은 요청을 여러 번 보내도 결과가 한 번과 같게 보장

사주다방 결제 적립에서는 둘 다 필요하다.

- 멱등성: 중복 적립 방지
- 트랜잭션: 거래 기록/잔액/주문상태/ledger 정합성 유지

## 왜 중요한가

- 네트워크 재시도
- 앱 재실행
- 클라이언트 중복 호출

이런 상황이 실제로 있기 때문

## 면접 답변 포인트

“사주다방에선 결제 중복 적립 방지를 위해 orderId 기반 멱등성과 ledger idempotency_key를 함께 사용했다.”

## 꼬리질문

### Q. `ON CONFLICT DO NOTHING`만 있으면 트랜잭션은 필요 없나요?

A. 아니다. 중복 적립은 막아도, 그 뒤의 `users.coins`, `purchase_orders`, `coin_ledger` 반영이 부분 성공하면 데이터가 깨질 수 있다. 그래서 멱등성과 트랜잭션은 별개로 같이 필요하다.

### Q. 애플리케이션 레벨 캐시로 중복 요청을 막으면 안 되나요?

A. 가능하지만 불완전하다. 프로세스 재시작, 멀티 인스턴스, 네트워크 재시도까지 고려하면 최종 보장은 DB 제약이나 idempotency key 같은 저장소 레벨에서 해야 한다.

### Q. `duplicate=true`를 응답에 넣는 이유는?

A. 클라이언트는 실패로 볼 필요가 없고, 이미 반영된 주문이라는 걸 이해하면 된다. 즉 중복 요청을 에러가 아니라 “이미 처리됨” 상태로 다루기 위한 API 설계다.
