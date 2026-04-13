# Metadata Lock and DDL Blocking

> 한 줄 요약: 테이블이 "잠긴 것처럼 보이는" 현상은 보통 row lock이 아니라 metadata lock 때문에 생기고, 그 차이를 알아야 배포가 멈추지 않는다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: metadata lock, MDL, performance_schema.metadata_locks, ALTER TABLE waiting, DDL blocking, long transaction, schema change lock, lock wait

## 핵심 개념

- 관련 문서:
  - [온라인 스키마 변경 전략](./online-schema-change-strategies.md)
  - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
  - [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
  - [Replication Failover and Split Brain](./replication-failover-split-brain.md)

Metadata Lock(MDL)은 테이블 정의를 보호하는 락이다.  
row를 보호하는 InnoDB 락과 목적이 다르다.

그래서 운영에서 "행 락은 없는데 ALTER TABLE이 안 끝난다"거나  
"SELECT 하나가 DDL을 막고 있다"는 상황이 나온다.

핵심은 다음이다.

- MDL은 테이블 구조가 바뀌는 동안 사용 중인 객체를 보호한다
- DDL은 보통 더 강한 MDL이 필요하다
- 오래 열린 트랜잭션은 MDL을 잡고 있어서 DDL을 대기시킨다

## 깊이 들어가기

### 1. MDL은 row lock이 아니다

InnoDB row lock은 레코드 단위 동시성을 다룬다.  
MDL은 테이블 정의에 대한 동시성을 다룬다.

즉 다음은 서로 다른 계층이다.

- `SELECT ... FOR UPDATE`는 row lock 관점
- `ALTER TABLE` 대기는 MDL 관점

이 차이를 모르면 "락은 없는데 왜 막히지?"가 된다.

### 2. MDL은 statement와 transaction 경계에 묶인다

autocommit 단일 statement는 보통 빨리 끝나지만, explicit transaction 안에서 실행한 statement는 그 트랜잭션이 끝날 때까지 MDL을 오래 잡을 수 있다.

예를 들면:

- `BEGIN; SELECT ...;` 를 열어 둔 상태
- 같은 테이블에 `ALTER TABLE`

이 조합은 DDL을 기다리게 만들 수 있다.

### 3. DDL이 기다리면 이후 요청도 밀릴 수 있다

MySQL은 DDL starvation을 피하려고 큐를 조정한다.  
즉 이미 대기 중인 DDL이 있으면, 그 뒤의 새 요청들이 영향을 받을 수 있다.

그래서 한 명의 장기 트랜잭션이 단순히 자기 쿼리만 느리게 하는 게 아니라,  
테이블 전체의 변경 작업과 배포를 막는 형태로 번질 수 있다.

### 4. 온라인 스키마 변경이 MDL에 민감한 이유

`pt-online-schema-change`나 `gh-ost`는 대부분 작업 자체보다 cutover 순간의 MDL이 위험하다.  
복사와 동기화가 잘 돼도 마지막 rename/교체 시점에 오래 기다리면 배포가 길어진다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `metadata lock`
- `MDL`
- `performance_schema.metadata_locks`
- `ALTER TABLE waiting`
- `DDL blocking`
- `long transaction`
- `schema change lock`

## 실전 시나리오

### 시나리오 1. 배포 중 ALTER가 멈춘다

증상:

- `ALTER TABLE`이 끝나지 않음
- CPU는 낮은데 세션은 오래 대기
- 애플리케이션 트래픽이 갑자기 밀림

원인:

- 누군가 같은 테이블을 오래 읽고 있다
- explicit transaction이 열려 있다

### 시나리오 2. SELECT는 정상인데 DDL만 유난히 늦다

읽기 트래픽 자체는 정상일 수 있다.  
문제는 long-running read transaction이 MDL을 유지한다는 점이다.

운영에서 자주 보이는 패턴:

- 리포트 쿼리
- 백필 작업
- 배치가 트랜잭션을 늦게 닫음

### 시나리오 3. cutover가 가장 오래 걸린다

온라인 스키마 변경에서 데이터 복사보다 마지막 전환이 더 길어질 수 있다.  
이때 확인해야 하는 건 데이터량이 아니라 MDL 대기다.

## 코드로 보기

### 두 세션으로 재현

```sql
-- session 1
BEGIN;
SELECT * FROM orders WHERE id = 1;
-- 여기서 트랜잭션을 열어 둔다

-- session 2
ALTER TABLE orders ADD COLUMN campaign_id BIGINT NULL;
```

### MDL 상태 확인

```sql
SELECT OBJECT_SCHEMA, OBJECT_NAME, LOCK_TYPE, LOCK_DURATION, LOCK_STATUS, OWNER_THREAD_ID
FROM performance_schema.metadata_locks
WHERE OBJECT_SCHEMA = 'mydb'
  AND OBJECT_NAME = 'orders';
```

### 현재 대기 세션 확인

```sql
SHOW PROCESSLIST;
```

여기서 `Waiting for table metadata lock` 같은 상태가 보이면 MDL 대기다.

### 운영 진단용 짧은 점검

```bash
mysql -e "SELECT * FROM performance_schema.metadata_locks WHERE LOCK_STATUS='PENDING'\G"
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 짧은 트랜잭션 유지 | MDL 점유 시간이 짧다 | 코드가 더 세심해야 한다 | 일반 OLTP |
| direct DDL | 단순하다 | 큰 테이블에서 위험하다 | 작은 테이블 |
| 온라인 스키마 변경 도구 | cutover를 통제할 수 있다 | 절차가 복잡하다 | 운영 중 대형 테이블 |
| 낮은 lock wait timeout | 오래 기다리지 않는다 | 실패가 늘 수 있다 | 빠른 실패가 더 나을 때 |

핵심은 락을 피하는 게 아니라, **테이블 정의를 바꾸는 순간을 얼마나 짧고 예측 가능하게 만드느냐**다.

## 꼬리질문

> Q: row lock과 metadata lock은 어떻게 다른가요?
> 의도: 락 계층 구분 이해 여부 확인
> 핵심: row lock은 데이터 행, MDL은 테이블 정의를 보호한다

> Q: 왜 장기 트랜잭션이 DDL을 막나요?
> 의도: 트랜잭션 경계와 MDL 유지 시간 이해 확인
> 핵심: 테이블 사용이 끝났다고 보지 않기 때문이다

> Q: `Waiting for table metadata lock`이 보이면 무엇부터 보나요?
> 의도: 운영 디버깅 순서 확인
> 핵심: 오래 열린 세션, 트랜잭션, cutover 작업을 먼저 찾는다

## 한 줄 정리

Metadata lock은 테이블 구조를 지키는 락이고, 장기 트랜잭션이 하나만 있어도 DDL과 배포 전체를 멈출 수 있다.
