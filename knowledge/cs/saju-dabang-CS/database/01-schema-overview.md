# 스키마를 사주다방으로 이해하기

## 핵심 테이블

- `users`
- `auth_sessions`
- `transactions`
- `purchase_orders`
- `coin_ledger`
- `reading_jobs`
- `reading_results`
- `llm_logs`

## 각 테이블 역할

### users
- 사용자 식별
- 코인 잔액
- 토스 계정 정보

### auth_sessions
- 로그인 세션 durable store

### transactions
- 실제 거래 흐름
- reserve / completed / refunded 상태

### purchase_orders
- IAP 주문 상태

### coin_ledger
- 회계/감사 기록
- 중복 방지 키 포함

### reading_jobs
- 운세 생성 진행 상태

### reading_results
- 최종 결과

### llm_logs
- LLM 처리 이력

## 실제 코드 스니펫

스키마는 코드에서 다음처럼 사용된다.

```java
jdbcClient.sql(
    """
      INSERT INTO reading_jobs (
        id, user_id, category, saju_hash, request_hash, status, reading_id,
        requested_at, dispatch_payload_json, progress_json, updated_at
      )
      VALUES (
        :id, :userId, :category, :sajuHash, :requestHash, 'queued', NULL,
        :requestedAt, CAST(:dispatchPayloadJson AS jsonb), CAST(:progressJson AS jsonb), NOW()
      )
      """
  )
  .param("id", jobId)
  .param("userId", userId)
  .param("category", category)
  .param("sajuHash", sajuHash)
  .param("requestHash", requestHash)
  .update();
```

```java
jdbcClient.sql(
    """
      INSERT INTO coin_ledger (
        id, user_id, type, amount, balance_after, order_id, idempotency_key, metadata
      ) VALUES (
        :id, :userId, :type, :amount, :balanceAfter, :orderId, :idempotencyKey, CAST(:metadata AS jsonb)
      )
      ON CONFLICT (idempotency_key) DO NOTHING
      """
  )
  .param("id", uuid())
  .param("userId", userId)
  .param("type", type)
  .param("amount", amount)
  .param("balanceAfter", coins)
  .param("orderId", orderId)
  .param("idempotencyKey", "%s:%s".formatted(type, orderId))
  .update();
```

관련 원본:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingReservationApplicationService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`

## 왜 이런 테이블 구성이 필요한가

### `users` 하나만으로는 부족하다

잔액과 사용자 기본 정보는 `users`에 있지만,
그것만으로는 다음을 설명할 수 없다.

- 어떤 결제로 적립됐는지
- 어떤 job이 reserve됐는지
- 환불이 있었는지
- 어떤 운세 결과가 생성됐는지

그래서 거래와 결과 테이블이 별도로 필요하다.

### `reading_jobs`와 `reading_results`가 분리되는 이유

- `reading_jobs`는 진행 상태
- `reading_results`는 최종 결과

즉 “진행 중인 것”과 “완료된 것”의 책임이 다르다.

## 면접 포인트

“왜 테이블이 이렇게 많냐?”  
- 역할을 분리해서 정합성과 추적성을 높이기 위해

## 꼬리질문

### Q. `reading_jobs`와 `reading_results`를 한 테이블에 합치면 안 되나요?

A. 가능은 하지만, 진행 상태와 완료 결과의 성격이 다르다. 진행 중에는 `error_code`, `progress_json`, `dispatch_payload_json`이 중요하고, 완료 후에는 sections와 snapshot이 중요하다. 분리하면 모델이 더 명확해진다.

### Q. `users.coins`가 있는데 왜 `transactions`, `coin_ledger`도 필요한가요?

A. 현재 잔액만으로는 “어떻게 이 값이 만들어졌는지”를 알 수 없다. 돈/포인트 성격의 데이터는 현재 상태와 이력을 둘 다 가져야 한다.

### Q. 테이블을 많이 나누면 조인이 늘어나서 느리지 않나요?

A. 맞다. 하지만 사주다방처럼 결제/복구/이력 추적이 중요한 서비스는 성능만큼 정합성과 설명 가능성도 중요하다. 그래서 적절한 분리가 필요하다.
