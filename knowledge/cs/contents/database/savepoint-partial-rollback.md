# Savepoint와 Partial Rollback

> 한 줄 요약: savepoint는 트랜잭션 전체를 포기하지 않고, 실패한 중간 지점만 되감아 다시 시도하게 해 준다.

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [트랜잭션 실전 시나리오](./transaction-case-studies.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md)
Retrieval anchors: `savepoint`, `partial rollback`, `nested transaction`, `retry substep`, `compensating step`

## 핵심 개념

Savepoint는 하나의 트랜잭션 안에서 중간 복구 지점을 만드는 기능이다.  
전체를 롤백하지 않고, 특정 단계까지만 되돌릴 수 있다.

왜 중요한가:

- 긴 업무 흐름에서 일부 단계만 실패해도 전체를 포기하지 않을 수 있다
- 외부 호출 이전의 DB 작업과 이후의 DB 작업을 나눠 다룰 수 있다
- 한 트랜잭션 안에서 “부분 실패”를 다루는 가장 실용적인 도구 중 하나다

savepoint는 nested transaction과 비슷하게 보이지만, 실제로는 **한 트랜잭션 내부의 체크포인트**다.

## 깊이 들어가기

### 1. savepoint가 필요한 이유

실무 흐름은 보통 한 줄로 끝나지 않는다.

- 주문 생성
- 쿠폰 차감
- 포인트 차감
- 로그 기록

여기서 마지막 로그 기록만 실패했다면 전체를 다 되돌리는 것이 오히려 손해일 수 있다.  
이럴 때 savepoint를 두면 실패한 단계만 롤백하고 앞선 단계는 유지할 수 있다.

### 2. 어디까지가 안전한가

savepoint는 DB 내부 변경에는 유용하지만, 외부 부작용은 되돌리지 못한다.

- DB insert/update는 되돌릴 수 있다
- 외부 결제 API 호출은 되돌릴 수 없다
- 이미 보낸 메시지는 자동으로 취소되지 않는다

즉 savepoint는 **DB 내부의 부분 롤백 도구**이지, 전체 업무 취소 장치가 아니다.

### 3. savepoint를 잘못 쓰면 생기는 문제

- 예외를 삼키고 다음 단계로 넘어가 정합성이 깨진다
- 외부 호출과 DB 변경을 같은 savepoint 범위로 오해한다
- 너무 작은 단위로 쪼개서 코드가 읽기 어려워진다

savepoint는 “실패를 숨기는 기능”이 아니라, **실패를 국소화하는 기능**이다.

### 4. 애플리케이션에서 흔한 사용처

- 배치 중 일부 row 실패를 건너뛸 때
- 옵션 단계가 있는 주문/정산 흐름
- validation 실패 시 중간 작업만 되돌릴 때

## 실전 시나리오

### 시나리오 1: 여러 자식 row를 저장하다 일부만 실패

부모 row는 이미 저장됐고, 자식 row 중 하나만 검증 실패했다면 savepoint로 자식 단계만 되돌릴 수 있다.  
부모까지 다시 만들 필요는 없다.

### 시나리오 2: 배치 중 한 건만 잘못된 데이터

100건을 처리하는 동안 1건만 오류가 나면, 전체 롤백 대신 해당 건만 skip하거나 되돌리는 쪽이 낫다.

### 시나리오 3: 트랜잭션은 유지하되 중간 검증에 실패

중간 검증이 실패했다고 전체 업무를 포기할지, 일부만 되돌릴지는 비즈니스 정책의 문제다.  
savepoint는 그 정책을 구현하는 기술적 수단이다.

## 코드로 보기

```sql
START TRANSACTION;

INSERT INTO orders(id, user_id, status) VALUES (1001, 7, 'PENDING');
SAVEPOINT after_order;

INSERT INTO order_items(order_id, sku, qty) VALUES (1001, 'SKU-1', 1);
-- 두 번째 아이템이 실패했다고 가정
ROLLBACK TO SAVEPOINT after_order;

INSERT INTO order_audit(order_id, action) VALUES (1001, 'ORDER_CREATED');
COMMIT;
```

```java
try {
    createOrder();
    em.createNativeQuery("SAVEPOINT after_order").executeUpdate();
    createItems();
} catch (Exception e) {
    em.createNativeQuery("ROLLBACK TO SAVEPOINT after_order").executeUpdate();
    addAuditOnly();
}
```

savepoint는 “다시 시작”이 아니라, **정해진 지점으로 돌아가 다시 진행**하는 장치다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 전체 롤백 | 단순하다 | 작은 실패도 전부 날린다 | 원자성이 최우선일 때 |
| savepoint partial rollback | 실패를 국소화한다 | 흐름이 복잡해진다 | 일부 단계만 되돌려도 될 때 |
| 단계별 별도 트랜잭션 | 경계가 명확하다 | 중간 상태가 남는다 | 업무를 분리할 수 있을 때 |
| 보상 작업 | 외부 부작용도 다룬다 | 설계 난이도가 높다 | Saga 패턴과 함께 쓸 때 |

## 꼬리질문

> Q: savepoint와 nested transaction은 같은 건가요?
> 의도: 용어 혼동을 구분하는지 확인
> 핵심: savepoint는 한 트랜잭션 내부의 체크포인트이고, 실제 nested transaction은 DB마다 의미가 다르다

> Q: savepoint가 외부 API 호출도 되돌리나요?
> 의도: DB 내부 롤백과 외부 부작용의 경계를 아는지 확인
> 핵심: 외부 부작용은 자동으로 되돌아가지 않는다

> Q: savepoint를 쓰면 전체 롤백보다 항상 좋은가요?
> 의도: 복잡도와 원자성 trade-off를 이해하는지 확인
> 핵심: 부분 복구가 필요할 때만 이득이 있다

## 한 줄 정리

Savepoint는 트랜잭션을 통째로 버리지 않고 실패한 중간 지점만 되감아 부분 복구하는 기능이다.
