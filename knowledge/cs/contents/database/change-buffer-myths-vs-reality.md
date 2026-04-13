# Change Buffer Myths vs Reality

> 한 줄 요약: change buffer는 "쓰기 최적화의 만능 열쇠"가 아니라, 특정 secondary index 변경을 뒤로 미루는 지연 메커니즘이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: change buffer myths, insert buffer, secondary index change buffering, merge cost, buffer pool miss, innodb_change_buffering, unique index, delayed merge

## 핵심 개념

- 관련 문서:
  - [Change Buffer, Purge, History List Length](./change-buffer-purge-history-length.md)
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

change buffer는 종종 "insert buffer"라는 옛 이름으로도 불린다.  
하지만 실무에서는 이름보다 동작을 정확히 아는 게 더 중요하다.

- 즉시 읽지 않아도 되는 secondary index 페이지에 대한 변경을 미룬다
- 랜덤 I/O를 줄여 쓰기 비용을 완화한다
- 대신 나중에 merge 비용이 돌아온다

따라서 change buffer는 제거되는 비용이 아니라 **시점이 바뀌는 비용**이다.

## 깊이 들어가기

### 1. 왜 이 기능이 생겼는가

secondary index 페이지가 버퍼 풀에 없으면, 모든 수정마다 디스크에서 그 페이지를 읽어 오기 비싸다.  
change buffer는 이 상황에서 "지금 고치지 말고 메모해 두자"는 전략을 쓴다.

이건 다음 환경에서 특히 의미가 있다.

- 랜덤 secondary index write가 많다
- 버퍼 풀에 핫하지 않은 secondary page가 많다
- 쓰기 폭주를 최대한 완화해야 한다

### 2. 흔한 오해 1: change buffer가 쓰기를 항상 빠르게 해준다

아니다.  
change buffer는 쓰기 경로의 일부를 늦출 뿐이고, 나중에 merge가 필요하다.

즉:

- 지금의 write latency는 줄 수 있다
- 미래의 read latency나 background merge 비용은 늘 수 있다

### 3. 흔한 오해 2: secondary index면 무조건 change buffer가 먹힌다

그렇지 않다.

- unique index는 즉시 검증이 필요해 제한적이다
- 페이지가 이미 버퍼 풀에 있으면 바로 갱신하는 편이 더 낫다
- 워크로드에 따라 이득이 거의 없을 수 있다

### 4. 흔한 오해 3: insert buffer는 별도의 신비한 최적화다

오늘날의 관점에서는 insert buffer를 change buffer의 옛 이름처럼 이해하는 편이 낫다.  
핵심은 이름이 아니라, **secondary index 변경을 지연 합산하는 메커니즘**이다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `change buffer`
- `insert buffer`
- `secondary index change buffering`
- `merge cost`
- `delayed merge`
- `innodb_change_buffering`

## 실전 시나리오

### 시나리오 1. 쓰기 폭주를 줄였는데 읽기가 늦어진다

배치나 대량 적재를 보호하려고 change buffer에 기대면, 이후 해당 secondary index가 read path에서 병합 비용을 치를 수 있다.  
즉 작업이 끝난 것처럼 보여도 부하가 뒤로 밀린 것뿐이다.

### 시나리오 2. change buffer를 믿고 인덱스를 많이 달았다

secondary index를 많이 추가하면 쓸 때마다 누적 비용이 늘어난다.  
change buffer가 그 비용을 숨겨 주는 것처럼 보여도, 전체 시스템의 쓰기/읽기 균형은 나빠질 수 있다.

### 시나리오 3. change buffer가 있어서 unique index도 싸다고 생각했다

unique 검사에는 즉시성 요구가 붙는다.  
그래서 비유니크 secondary index와 같은 감각으로 보면 설계를 잘못하게 된다.

## 코드로 보기

### 상태 확인

```sql
SHOW VARIABLES LIKE 'innodb_change_buffering';
SHOW STATUS LIKE 'Innodb_ibuf_size';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_dirty';
```

### insert-heavy 재현

```sql
INSERT INTO event_log (id, user_id, event_type, created_at)
VALUES (1, 1001, 'CLICK', NOW());
```

secondary index가 많으면 이 한 줄이 여러 내부 갱신을 촉발한다.

### 관찰

```sql
SHOW ENGINE INNODB STATUS\G
```

`Ibuf`와 merge 관련 상태를 같이 본다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| change buffer 활용 | 랜덤 secondary write를 완화한다 | merge 비용이 나중에 돌아온다 | write-heavy OLTP |
| change buffer 의존 축소 | read path 예측이 쉬워진다 | 즉시 I/O가 늘 수 있다 | 읽기 안정성이 중요할 때 |
| secondary index 최소화 | 쓰기 비용이 줄어든다 | 일부 조회가 느려질 수 있다 | write 집중 테이블 |

핵심은 change buffer를 "공짜 최적화"로 보는 착각을 버리는 것이다.

## 꼬리질문

> Q: insert buffer와 change buffer는 같은 건가요?
> 의도: 용어와 동작을 구분하는지 확인
> 핵심: 현재 관점에서는 change buffer로 이해하는 게 맞다

> Q: change buffer가 항상 성능을 올리나요?
> 의도: 지연 메커니즘의 비용을 이해하는지 확인
> 핵심: write를 늦출 뿐 merge 비용이 나중에 온다

> Q: unique index에는 왜 똑같이 적용되지 않나요?
> 의도: 즉시 검증이 필요한 경로를 이해하는지 확인
> 핵심: 중복 여부를 바로 확인해야 하기 때문이다

## 한 줄 정리

change buffer는 secondary index 변경의 시점을 미루는 장치이지, 비용을 없애는 장치가 아니며 merge 비용을 어디서 치를지 결정하는 메커니즘이다.
