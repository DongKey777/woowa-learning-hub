# Bounded Context와 Port/Adapter

## 사주다방의 핵심 경계

- auth
- billing
- reading
- worker

## Port 예시

- `BillingPort`

왜 필요한가?
- reading이 billing 내부 구현에 직접 의존하지 않게 하기 위해

## 관련 코드

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/application/port/BillingPort.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/reading/application/ReadingReservationApplicationService.java`

## 실제 코드 스니펫

### Port

```java
public interface BillingPort {
  ReservationResult reserveBalance(
    String userId,
    String category,
    int cost,
    ReservationReferenceId reservationReferenceId
  );

  void captureTransaction(String transactionId, String jobId, String readingId);
  void refundTransaction(String transactionId, String jobId);
}
```

### Port를 사용하는 쪽

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

이 구조의 핵심:

- reading은 billing “구현체”를 모름
- reading은 `BillingPort`라는 약속만 앎
- 실제 구현은 billing 쪽 repository/service에 숨김

즉 DIP와 port-adapter를 실코드로 적용한 예다.

## 면접 포인트

“bounded context를 나누고 포트를 둔 이유는 결합도를 낮추고 교체 가능성을 높이기 위해서다.”

## 꼬리질문

### Q. 그냥 service끼리 직접 주입하면 안 되나요?

A. 작은 프로젝트에서는 가능하지만, 도메인 경계가 흐려진다. 특히 reading과 billing처럼 서로 다른 책임을 가진 영역은 포트를 사이에 두는 게 유지보수에 유리하다.

### Q. 이 구조가 왜 테스트에 유리하죠?

A. application service는 port 기준으로 생각할 수 있어서, 구현체를 바꿔끼우거나 mocking하기 쉽다. 즉 “무엇을 해야 하는지”와 “어떻게 하는지”가 분리된다.

### Q. port를 너무 많이 만들면 오히려 과한 거 아닌가요?

A. 맞다. 그래서 사주다방도 모든 걸 port로 쪼개지 않고, 실제로 경계가 중요한 billing 같은 곳에만 의미 있게 사용했다.
