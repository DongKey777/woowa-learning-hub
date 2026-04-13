# XA와 Two-Phase Commit의 함정

> 한 줄 요약: 2PC는 “둘 다 커밋하거나 둘 다 롤백”을 약속하지만, 실제 운영에서는 준비 상태가 오히려 가장 위험한 상태가 된다.

관련 문서: [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md), [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md), [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)
Retrieval anchors: `XA`, `two-phase commit`, `prepare`, `heuristic outcome`, `in-doubt transaction`

## 핵심 개념

XA는 여러 resource manager(DB, message broker, 외부 시스템)를 하나의 분산 트랜잭션처럼 묶기 위한 표준 인터페이스다.  
Two-Phase Commit(2PC)은 그 대표적인 커밋 프로토콜이다.

왜 중요한가:

- DB 두 개를 동시에 갱신해야 할 때 “한쪽만 성공”을 막고 싶다
- 하지만 준비 단계가 길어지면 락이 오래 잡히고, 운영이 더 어려워진다
- 분산 정합성을 맞추려다 가용성을 잃는 전형적인 지점이다

## 깊이 들어가기

### 1. 2PC가 어떻게 동작하는가

2PC는 보통 두 단계로 진행된다.

1. Prepare: 각 participant가 “커밋할 준비가 되었다”고 답한다
2. Commit: coordinator가 최종 커밋 명령을 내린다

문제는 Prepare 시점부터다.

- participant는 자원을 잡은 채 결과를 기다린다
- coordinator가 죽으면 participant는 in-doubt 상태가 된다
- 롤백할지 커밋할지 스스로 결정하기 어렵다

### 2. 왜 XA가 운영에서 까다로운가

XA는 단순한 SQL 트랜잭션보다 훨씬 무겁다.

- 네트워크 왕복이 늘어난다
- prepare 이후 락이 오래 유지될 수 있다
- 장애 시 복구 절차가 복잡하다
- 한 쪽만 복구되면 heuristic mixed outcome이 생길 수 있다

즉 XA는 “정합성”을 주는 대신 “가용성, 단순성, 운영성”을 깎아 먹는다.

### 3. 어떤 실패가 치명적인가

- coordinator가 prepare 후 crash
- 한 participant만 commit, 다른 participant는 timeout
- 네트워크 분할로 participant 간 상태가 어긋남
- 재시도 로직이 XA 밖에서 또 한 번 중복 실행됨

이 순간 중요한 것은 “정답이 무엇인가”보다 “누가 최종 진실을 소유하는가”다.

### 4. 왜 대체 패턴을 쓰는가

실무에서는 보통 다음으로 방향을 튼다.

- outbox + CDC
- saga + compensation
- idempotent command 처리

이 방식들은 강한 즉시 정합성 대신, 운영 가능한 eventual consistency를 택한다.

## 실전 시나리오

### 시나리오 1: 주문 DB와 정산 DB를 동시에 갱신

두 DB를 XA로 묶으면 한쪽만 성공하는 문제를 줄일 수 있다.  
하지만 prepare 상태에서 락이 오래 남고, 장애 복구가 복잡해져서 오히려 운영 리스크가 커진다.

### 시나리오 2: 결제 승인과 재고 차감을 한 번에 맞추려다 멈춤

결제 승인 시스템과 재고 DB를 하나로 묶고 싶어도, 외부 시스템은 XA participant가 아니다.  
이때 XA를 억지로 확대하면 오히려 불안정해진다.

### 시나리오 3: 배포 중 in-doubt transaction이 남는다

장애 대응이 늦어지면 prepare된 트랜잭션이 수동 복구 대상이 된다.  
이건 데이터 정합성 이슈이면서 동시에 운영 부채다.

## 코드로 보기

```sql
-- XA transaction 기본 흐름
XA START 'order-123';
UPDATE accounts
SET balance = balance - 10000
WHERE id = 1;
XA END 'order-123';

XA PREPARE 'order-123';
-- 여기서 coordinator가 죽으면 in-doubt 상태가 된다

XA COMMIT 'order-123';
-- 또는 XA ROLLBACK 'order-123';
```

```sql
-- 복구 시 확인
XA RECOVER;
```

XA를 쓰면 “실패가 없다”가 아니라, **실패를 회수하는 절차가 생긴다**는 점을 기억해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| XA/2PC | 강한 원자성을 노릴 수 있다 | 락 유지, 복구 복잡성, 가용성 저하 | 정말로 둘 다 같은 시점에 커밋해야 할 때 |
| Saga | 운영이 유연하다 | 보상 로직이 필요하다 | 업무 단위가 분리되어 있을 때 |
| Outbox + CDC | 메시지와 DB 정합성이 좋다 | 최종 일관성이다 | 이벤트 발행이 핵심일 때 |
| Idempotent retry | 구현이 현실적이다 | 중복 처리 설계가 필요하다 | 재시도가 자연스러운 API일 때 |

## 꼬리질문

> Q: XA가 왜 운영에서 잘 안 쓰이나요?
> 의도: 2PC의 락 유지와 복구 복잡도를 아는지 확인
> 핵심: 준비 상태가 길어지고 장애 복구가 어렵다

> Q: coordinator가 prepare 후 죽으면 어떻게 되나요?
> 의도: in-doubt transaction과 복구 절차 이해 여부 확인
> 핵심: participant가 최종 결정을 기다리며 자원을 잡고 있을 수 있다

> Q: XA 대신 무엇을 많이 쓰나요?
> 의도: 실무 대안을 알고 있는지 확인
> 핵심: outbox, CDC, saga, idempotent retry가 더 많이 쓰인다

## 한 줄 정리

XA와 2PC는 분산 원자성을 제공하지만, prepare 이후의 락과 복구 복잡도 때문에 실무에서는 outbox나 saga로 우회하는 경우가 많다.
