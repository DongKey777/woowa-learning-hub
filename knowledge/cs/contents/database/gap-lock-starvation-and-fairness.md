# Gap Lock Starvation과 Fairness

> 한 줄 요약: gap lock은 범위를 보호하지만, 같은 범위를 오래 또는 자주 잡으면 새 insert가 계속 굶는 starvation이 생긴다.

관련 문서: [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md), [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Deadlock Case Study](./deadlock-case-study.md)
Retrieval anchors: `gap lock starvation`, `next-key lock fairness`, `insert intention lock`, `range lock`, `hot range`

## 핵심 개념

Gap lock은 row 사이의 빈 구간을 잠가 범위 무결성을 지킨다.  
하지만 같은 범위를 계속 잠그는 워크로드에서는 새 insert가 계속 대기하게 된다.

왜 중요한가:

- 큐 테이블이나 대기열 테이블이 특정 범위에 몰릴 수 있다
- 범위 lock이 길어지면 새 데이터 입력이 밀린다
- “충돌은 없는데 왜 계속 막히지?”라는 starvation이 생긴다

여기서 문제는 데드락이 아니라 **우선순위와 공정성**이다.

## 깊이 들어가기

### 1. starvation이란

starvation은 충돌이 해결되지 않는 게 아니라, 특정 요청이 계속 뒤로 밀리는 현상이다.

- insert는 계속 들어오지만 gap이 계속 잠겨 있다
- 짧은 조회/갱신이 반복되면서 대기열이 풀리지 않는다
- 특정 핫 range만 끝없이 지연된다

즉 lock 자체가 틀린 것이 아니라, **같은 구간에 경쟁이 집중**된 것이 문제다.

### 2. 왜 gap lock에서 특히 보이는가

next-key lock은 범위를 함께 보호한다.  
이 구조는 phantom을 줄이는 대신, 범위 내부의 새로운 insert를 오래 막을 수 있다.

핫 range가 아래와 같으면 문제가 커진다.

- `status = 'WAITING'`
- `created_at BETWEEN ...`
- 특정 seat section / ticket batch

### 3. fairness를 보장하기 어려운 이유

DB는 보통 “먼저 온 요청”보다 “정합성”을 우선한다.

- 현재 트랜잭션이 락을 오래 잡으면 뒤 요청이 밀린다
- insert-intention lock이 있어도 gap이 풀려야 한다
- 재시도는 공정성을 보장하지 않는다

그래서 starvation은 “락이 틀렸다”가 아니라 **워크로드가 특정 범위를 너무 오래 쓰고 있다**는 신호다.

### 4. 완화 전략

- 범위를 더 잘게 쪼갠다
- 핫 range를 시간/샤드로 분산한다
- 트랜잭션을 짧게 유지한다
- 대기열 조회를 `SKIP LOCKED` 같은 패턴으로 바꾼다

## 실전 시나리오

### 시나리오 1: 대기열 삽입이 계속 막힌다

소비자가 오래 range lock을 잡고 있으면, 신규 작업이 계속 밀린다.  
이건 데드락보다 더 조용하게 망가진다.

### 시나리오 2: 인기 구간만 insert가 늦다

같은 시간대/같은 status에 요청이 몰리면 특정 gap만 계속 잠긴다.  
서비스는 전체적으로는 살아 있지만 일부 구간만 굶는다.

### 시나리오 3: 재시도가 오히려 starvation을 키운다

재시도 루프가 같은 range를 즉시 다시 두드리면, 경쟁을 더 키울 수 있다.

## 코드로 보기

```sql
START TRANSACTION;
SELECT id
FROM queue_items
WHERE queue_name = 'billing'
  AND status = 'READY'
ORDER BY id
LIMIT 10
FOR UPDATE;
```

```sql
INSERT INTO queue_items(queue_name, status, payload)
VALUES ('billing', 'READY', '{}');
```

핫 range에서는 위 insert가 오래 막힐 수 있다.  
이럴 때는 queue partitioning이나 더 작은 잠금 단위가 필요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 큰 range lock | 정합성이 쉽다 | starvation이 생기기 쉽다 | 매우 보수적 제어 |
| 작은 range / 샤딩 | 경합이 줄어든다 | 설계가 복잡하다 | 핫 range가 존재할 때 |
| `SKIP LOCKED` | 대기 감소 | 공정성이 약해질 수 있다 | worker queue |
| 짧은 트랜잭션 | 락 점유가 줄어든다 | 코드가 까다롭다 | 대부분의 OLTP |

## 꼬리질문

> Q: gap lock은 데드락과 어떤 차이가 있나요?
> 의도: starvation과 deadlock을 구분하는지 확인
> 핵심: 데드락은 서로 막히는 것이고, starvation은 한쪽이 계속 밀리는 것이다

> Q: insert가 막히는데 데드락은 아니면 무엇을 의심하나요?
> 의도: 장기 gap lock과 hot range를 의심하는지 확인
> 핵심: 같은 범위가 오래 잠겨 있는지 본다

> Q: fairness를 DB가 보장해주지 않나요?
> 의도: DB 스케줄링의 한계를 아는지 확인
> 핵심: 정합성이 우선이라 공정성은 자동 보장되지 않는다

## 한 줄 정리

Gap lock starvation은 범위 보호가 성공했는데도 새 insert가 계속 밀리는 현상이며, 해결은 락을 빨리 풀거나 핫 range를 분산하는 것이다.
