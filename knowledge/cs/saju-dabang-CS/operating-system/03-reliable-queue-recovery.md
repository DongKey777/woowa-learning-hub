# Reliable Queue와 복구

## 개념

worker queue는 단순 pop이 아니라 **유실 방지**가 중요하다.

## 사주다방 구현

관련 코드:
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/RedisReliableQueue.java`
- `/Users/idonghun/IdeaProjects/saju-dabang/server-java/worker/src/main/java/com/sajudabang/worker/queue/WorkerQueueLifecycle.java`

핵심:
- execution queue
- processing queue
- lease key
- ack
- requeue
- stale processing recovery

## 실제 코드 스니펫

`claimNext()`의 핵심은 execution queue에서 processing queue로 옮기고 lease를 거는 것이다.

```java
String raw = blocking.brpoplpush(
  timeoutSeconds,
  QueueKeys.EXECUTION_QUEUE_KEY,
  QueueKeys.PROCESSING_QUEUE_KEY
);

String leaseKey = QueueKeys.buildLeaseKey(jobId);
Runnable renew = () -> commands.setex(
  leaseKey,
  QueueKeys.PROCESSING_LEASE_SECONDS,
  "{\"startedAt\":%d}".formatted(System.currentTimeMillis())
);
renew.run();
```

stale recovery는 이렇게 처리한다.

```java
if (startedAt <= 0L || System.currentTimeMillis() - startedAt > QueueKeys.STALE_PROCESSING_MS) {
  commands.del(QueueKeys.buildLeaseKey(jobId));
  commands.lrem(QueueKeys.PROCESSING_QUEUE_KEY, 1, raw);
  commands.rpush(QueueKeys.EXECUTION_QUEUE_KEY, raw);
  requeued++;
}
```

이 코드가 의미하는 것:

1. 작업을 가져가는 순간 processing queue로 이동
2. lease를 남겨 “누가 잡고 있는지” 기록
3. 오래된 lease면 다시 execution queue로 복원

즉 단순 queue가 아니라 **복구 가능한 queue**다.

## 왜 필요한가

worker가 작업을 잡고 죽어도 유실되면 안 되기 때문

## 면접 답변 포인트

“이건 producer-consumer 문제를 실서비스 환경에서 복구 가능하게 구현한 사례다.”

## 꼬리질문

### Q. 그냥 `BLPOP`만 쓰면 안 되나요?

A. 안 된다. worker가 pop 후 죽으면 작업이 유실될 수 있다. processing queue와 lease가 있어야 다시 복구할 수 있다.

### Q. exactly-once 보장인가요?

A. 완전한 exactly-once라고 보기보다 at-least-once에 가깝다. 대신 멱등성과 상태 전이 조건을 같이 둬서 중복 부작용을 줄인다.

### Q. 왜 lease가 필요한가요?

A. processing queue에만 넣어두면 “정상 처리 중인지, 죽은 worker가 잡고 있던 건지” 구분이 어렵다. lease는 살아 있는 처리인지 판단하는 단서가 된다.
