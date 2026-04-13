# reserve -> capture -> refund 상태 전이

## 개념

사주다방은 운세 생성 전에 코인을 바로 확정 차감하지 않고, 먼저 **reserve** 한다.

상태:
- `reserved`
- `completed`
- `refunded`

## 관련 코드

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingReservationApplicationService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingFinalizationApplicationService.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingRefundApplicationService.java`

## 왜 이렇게 하나

운세 생성은 실패할 수 있다.

그래서:
- 시작 전에 reserve
- 성공하면 capture
- 실패하면 refund

이 구조가 필요하다.

## 실제 코드 스니펫

### reserve

```java
ReservationResult reservation = billingPort.reserveBalance(
  userId,
  category,
  cost,
  new ReservationReferenceId(reservationReferenceId)
);
if (!reservation.reserved()) {
  return new ReservationOutcome(false, null, reservation.coinsRemaining());
}

insertReservedLog(reservationReferenceId, userId, jobId, category, sajuHash);
```

### capture

```java
markLogSuccess(logId, sectionsJson, readingMetaJson);
billingPort.captureTransaction(transactionId, jobId, readingId);
redisJobEventPublisher.publish(jobId, "completed", Map.of(
  "jobId", jobId,
  "readingId", readingId,
  "createdAt", completedAt.toEpochMilli()
));
```

### refund

```java
billingPort.refundTransaction(transactionId, jobId);

jdbcClient.sql(
    """
      UPDATE llm_logs
      SET status = 'error',
          error_message = :errorMessage,
          latency_ms = :latencyMs
      WHERE id = :id AND status = 'reserved'
      """
  )
  .param("errorMessage", errorMessage)
  .param("latencyMs", latencyMs)
  .param("id", logId)
  .update();
```

## CS 포인트

이건 데이터베이스 관점에서 **상태 전이 모델**이고,  
비즈니스 관점에선 **보상 트랜잭션(compensation)** 과 비슷하다.

## 왜 “즉시 차감”보다 나은가

만약 바로 최종 차감만 해버리면:
- 생성 실패 시 복구가 어려움
- 어느 단계에서 실패했는지 추적 어려움

reserve 모델은 중간 실패를 설명하기 좋다.

## 면접 포인트

“긴 비동기 작업에서 돈이 걸린 자원을 다룰 때는 즉시 확정보다 reserve/capture/refund 모델이 더 안전하다.”

## 꼬리질문

### Q. 이건 분산 트랜잭션인가요?

A. 완전한 분산 트랜잭션이라고 보긴 어렵다. 대신 비동기 작업의 성공/실패에 따라 reserve 후 capture 또는 refund로 보상하는 모델에 가깝다.

### Q. refund는 언제 발생하나요?

A. worker 실패, 처리 예외, stale recovery, 외부 API 실패 등으로 최종 결과를 만들지 못했을 때 발생할 수 있다.

### Q. 왜 `transactions.status`를 두나요?

A. 단순 금액 기록만으로는 현재 단계가 reserve인지 완료인지 환불인지 설명이 안 되기 때문이다. 상태 전이를 명시적으로 모델링하기 위해서다.
