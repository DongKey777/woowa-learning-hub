# Race Condition과 Locking

## 개념

여러 요청이 동시에 같은 데이터를 바꾸면 경쟁 상태(race condition)가 생긴다.

예:
- 같은 orderId를 두 번 적립
- 같은 코인을 동시에 차감
- 같은 reservation을 중복 refund

## 사주다방에서의 위험

### 1. 중복 적립

해결:
- `order_id` unique 성격 활용
- `ON CONFLICT DO NOTHING`

### 2. reservation refund 경쟁

reserve 상태에서:
- 하나는 capture
- 다른 하나는 refund

같은 transaction을 두 흐름이 동시에 만질 수 있다.

### 3. processing queue 회수 경쟁

worker가 stale job을 되돌리는 동안 다른 worker가 잡을 수 있다.

## 코드 연결

- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/server/src/main/java/com/sajudabang/billing/infra/persistence/BillingJdbcRepository.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/RedisReliableQueue.java`

## 핵심 포인트

동시성 문제를 해결하는 방법은 보통:

1. DB 제약조건
2. 상태 전이 조건
3. 멱등성 키
4. 큐 lease

를 함께 쓰는 것이다.

## 면접 포인트

“race condition을 코드로 막으려면 단순 synchronized보다 DB 제약, 상태 전이, idempotency, lease를 조합해야 한다.”
