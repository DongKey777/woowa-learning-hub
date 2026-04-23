# Change Buffer, Purge, History List Length

> 한 줄 요약: 쓰기 성능을 살리는 지연 장치와 과거 버전을 치우는 정리 작업은 한 몸이고, 둘이 밀리면 결국 undo debt로 돌아온다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: change buffer, insert buffer, purge, history list length, undo log, secondary index merge, long transaction, MVCC cleanup, innodb_change_buffering

## 핵심 개념

- 관련 문서:
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [트랜잭션 격리수준과 락](./transaction-isolation-locking.md)
  - [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md)
  - [MVCC, Replication, Sharding](./mvcc-replication-sharding.md)
  - [Vacuum / Purge Debt Forensics and Symptom Map](./vacuum-purge-debt-forensics-symptom-map.md)

InnoDB에서 쓰기와 정리는 서로 반대 방향으로 움직이지 않는다.  
오히려 쓰기를 빠르게 하려고 미뤄 둔 일이, 나중에 purge와 merge 비용으로 돌아온다.

이 문서의 핵심은 두 가지다.

- `change buffer`는 디스크에 없는 secondary index 페이지의 수정을 나중으로 미룬다
- `purge`는 MVCC에서 더 이상 필요 없는 과거 버전을 정리한다

둘 다 "지금 당장 덜 아프게" 만드는 장치지만, 미뤄진 일이 쌓이면 더 큰 지연으로 되돌아온다.

## 깊이 들어가기

### 1. change buffer는 왜 필요한가

secondary index 페이지가 버퍼 풀에 없을 때마다 즉시 디스크를 읽어 와서 고치면, 작은 쓰기가 너무 비싸진다.  
그래서 InnoDB는 일부 변경을 change buffer에 기록해 두었다가 나중에 합친다.

이 방식은 특히 다음 상황에서 도움이 된다.

- 랜덤 secondary index 쓰기가 많다
- 페이지가 버퍼 풀에 자주 없었다
- write amplification을 조금이라도 줄여야 한다

하지만 모든 인덱스에 적용되는 것은 아니다.

- 보통 secondary index에 적용된다
- unique index는 즉시 검증이 필요해서 제한적이다
- 페이지를 결국 읽게 되면 merge 비용이 한 번에 터질 수 있다

### 2. purge는 MVCC의 뒷정리다

트랜잭션이 업데이트한 과거 버전은 바로 버릴 수 없다.  
다른 트랜잭션이 그 스냅샷을 아직 보고 있을 수 있기 때문이다.

그래서 InnoDB는 undo log에 쌓인 오래된 버전을 나중에 purge한다.

- 커밋된 변경은 보이지만
- 더 이상 참조되지 않는 과거 버전은 purge 대상이 된다

이 작업이 밀리면 `history list length`가 길어진다.  
즉 정리해야 할 과거 버전이 쌓여 있다는 뜻이다.

### 3. 긴 트랜잭션이 purge를 막는다

가장 흔한 원인은 오래 열린 트랜잭션이다.

- 리포트성 SELECT를 오래 유지함
- 커넥션을 잡고 중간에 외부 API 호출을 함
- 배치가 불필요하게 큰 범위를 한 번에 처리함

이런 트랜잭션이 있으면 purge가 과거 버전을 마음대로 지우지 못한다.  
결과적으로 undo가 쌓이고, 히스토리 길이가 늘고, 읽기와 쓰기 모두 부담을 받는다.

### 4. change buffer와 purge는 따로 움직이는 것 같지만 같이 터진다

change buffer는 쓰기 경로를 가볍게 만들고, purge는 오래된 버전을 치워 공간을 회수한다.  
둘 중 하나만 밀려도 시스템은 버티지만, 둘이 동시에 밀리면 부하가 증폭된다.

예를 들면:

- secondary index가 많은 테이블에 대량 insert
- 동시에 오래 열린 트랜잭션이 존재
- 버퍼 풀은 바쁘고, purge는 뒤처지고, change buffer merge도 밀림

이 조합은 운영에서 꽤 위험하다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `change buffer`
- `insert buffer`
- `purge`
- `history list length`
- `undo log`
- `innodb_change_buffering`
- `innodb_purge_threads`
- `secondary index merge`

## 실전 시나리오

### 시나리오 1. 대량 insert는 빨라졌는데 나중에 시스템이 버벅인다

초반엔 change buffer 덕분에 쓰기가 빠르게 보일 수 있다.  
그런데 나중에 해당 secondary index 페이지를 읽는 순간 merge 비용이 몰린다.

증상:

- 배치 직후는 괜찮음
- 이후 읽기 쿼리 지연 증가
- buffer pool miss와 merge가 같이 보임

### 시나리오 2. 오래 열린 트랜잭션이 전체 시스템을 서서히 느리게 만든다

읽기 전용 리포트 작업이 트랜잭션을 오래 잡고 있으면 purge가 못 따라간다.  
그러면 undo가 쌓이고, 스토리지와 메모리 압력이 같이 커진다.

증상:

- `History list length` 증가
- 락 자체는 적은데 DB가 무거워짐
- 백그라운드 정리 작업이 계속 바쁨

### 시나리오 3. "쓰기 느림"으로 보였지만 사실은 정리 부채였다

인서트는 빨랐지만 purge가 밀린 상태에서는

- 결과적으로 read latency도 느려지고
- checkpoint와 flush도 악화되고
- 재시작 후 recovery도 무거워질 수 있다

즉 change buffer와 purge는 단순 성능 옵션이 아니라, 지연된 작업량을 관리하는 장치다.

## 코드로 보기

### change buffer와 purge 상태 확인

```sql
SHOW VARIABLES LIKE 'innodb_change_buffering';
SHOW VARIABLES LIKE 'innodb_purge_threads';
SHOW VARIABLES LIKE 'innodb_max_purge_lag';

SHOW STATUS LIKE 'Innodb_history_list_length';
SHOW STATUS LIKE 'Innodb_ibuf_size';
```

### InnoDB 상태에서 정리 압력 보기

```sql
SHOW ENGINE INNODB STATUS\G
```

확인 포인트:

- `Ibuf:` 관련 수치
- purge lag 징후
- history list length 증가

### 긴 트랜잭션 재현 예시

```sql
-- session 1
BEGIN;
SELECT * FROM orders WHERE user_id = 1001;
-- 이 상태를 오래 유지

-- session 2
UPDATE orders SET status = 'DONE' WHERE user_id = 1001;
```

이때 session 1이 오래 살아 있으면 session 2의 과거 버전 정리가 늦어진다.

### 운영 점검 예시

```bash
mysql -e "SHOW STATUS LIKE 'Innodb_history_list_length';"
mysql -e "SHOW ENGINE INNODB STATUS\G"
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| change buffering 활성화 | 랜덤 secondary index 쓰기를 완화한다 | 나중에 merge 비용이 몰릴 수 있다 | 쓰기 많은 OLTP |
| change buffering 축소/비활성화 | 지연 merge를 줄인다 | 즉시 디스크 I/O가 늘 수 있다 | 읽기 예측이 중요할 때 |
| purge threads 증가 | 정리 속도를 높일 수 있다 | 백그라운드 I/O와 CPU를 더 쓴다 | history list length가 계속 늘 때 |
| 긴 트랜잭션 허용 | 배치 코드는 단순해진다 | undo debt가 쌓인다 | 정말 필요한 리포트/일괄 작업일 때 |

핵심은 정답이 아니라, **지연한 비용을 언제 누가 치를지**를 정하는 것이다.

## 꼬리질문

> Q: change buffer는 왜 primary key에는 잘 적용되지 않나요?
> 의도: secondary index와 PK 처리 차이 이해 여부 확인
> 핵심: primary key는 행 자체의 위치와 직결되어 성격이 다르다

> Q: history list length가 길면 왜 위험한가요?
> 의도: purge lag와 undo debt 이해 여부 확인
> 핵심: 오래된 버전을 정리하지 못해 메모리와 I/O 부담이 커진다

> Q: 오래 열린 SELECT가 왜 쓰기까지 느리게 만드나요?
> 의도: MVCC와 purge 관계 확인
> 핵심: 과거 버전을 계속 보존해야 해서 purge가 멈추기 때문이다

## 한 줄 정리

change buffer는 쓰기 지연을 뒤로 미루고, purge는 그 지연의 뒷정리를 맡는다. 둘의 균형이 깨지면 history list length가 시스템 부채로 쌓인다.
