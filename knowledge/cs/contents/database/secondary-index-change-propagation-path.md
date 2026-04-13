# Secondary Index Change Propagation Path

> 한 줄 요약: 한 row의 UPDATE는 row 하나만 바꾸는 일이 아니라, clustered index와 모든 secondary index에 변경을 전파하는 연쇄 작업이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: secondary index propagation, clustered index update, change buffer, undo log, redo log, page split, leaf page, secondary index maintenance

## 핵심 개념

- 관련 문서:
  - [Secondary Index Maintenance Cost and ANALYZE Statistics Skew](./secondary-index-maintenance-cost-analyze-skew.md)
  - [Change Buffer Myths vs Reality](./change-buffer-myths-vs-reality.md)
  - [Clustered Primary Key Update Cost](./clustered-primary-key-update-cost.md)
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)

secondary index는 읽기만 돕는 부가 자료구조처럼 보이지만, write path에서는 반드시 따라가야 하는 비용이 된다.  
그 이유는 row가 바뀔 때 secondary index entry도 같이 바뀌어야 하기 때문이다.

이 문서의 핵심은 다음이다.

- clustered index row가 먼저 바뀐다
- secondary index entry가 그 변경을 따라간다
- 페이지가 버퍼 풀에 없으면 change buffer가 개입할 수 있다
- undo/redo와 page split까지 함께 비용을 만든다

## 깊이 들어가기

### 1. UPDATE는 왜 여러 인덱스를 건드리나

테이블의 논리적 row 하나가 바뀌어도, 실제로는 여러 구조가 바뀐다.

1. clustered index의 row 본문이 갱신된다.
2. secondary index의 key 값이 바뀌면 기존 entry를 제거하고 새 entry를 넣어야 한다.
3. 유니크 인덱스면 중복 검증이 필요하다.
4. 변경 내용은 redo/undo에 기록된다.

즉 write path는 "row 수정"이 아니라 "인덱스 집합 수정"이다.

### 2. change buffer가 어디서 들어오는가

secondary index page가 버퍼 풀에 없으면, 즉시 디스크에서 읽어와 갱신하는 대신 change buffer로 일부 작업을 미룰 수 있다.

하지만 이것도 제한적이다.

- 비유니크 secondary index에 주로 유효하다
- page가 이미 메모리에 있으면 바로 갱신하는 편이 낫다
- 나중에 merge 비용이 결국 돌아온다

### 3. delete-mark와 purge로 이어지는 경로

DELETE나 PK 변경은 단순 삭제가 아니다.  
실제 엔진 내부에서는 delete-mark가 생기고, purge thread가 나중에 안전해졌을 때 정리한다.

그래서 secondary index propagation path는 다음과 같이 이어진다.

- 현재 row 변경
- secondary entry 수정 또는 delete-mark
- undo chain 보존
- purge 시점의 정리

### 4. 왜 write amplification으로 보이는가

한 번의 UPDATE가 여러 page write를 낳기 때문이다.

- clustered index page
- secondary index leaf page 여러 개
- redo log
- undo log

이게 누적되면 "쓰기 하나가 너무 무겁다"는 느낌으로 나타난다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `secondary index propagation`
- `clustered index update`
- `change buffer`
- `undo log`
- `redo log`
- `page split`
- `secondary index maintenance`

## 실전 시나리오

### 시나리오 1. status 컬럼 업데이트만 했는데 느려졌다

status가 secondary index에 포함되어 있으면, 값 하나 바뀌어도 인덱스 entry를 다시 써야 한다.  
읽기 최적화용 인덱스가 쓰기 경로를 더 무겁게 만들 수 있다.

### 시나리오 2. PK가 바뀌는 배치가 유난히 무겁다

PK 변경은 clustered index와 secondary index 모두를 흔든다.  
이때는 단순 UPDATE가 아니라 row relocation과 인덱스 전파 비용으로 봐야 한다.

### 시나리오 3. 적재는 빠른데 뒤에서 읽기가 흔들린다

change buffer로 미룬 secondary index 수정이 나중에 merge될 때, read path가 흔들릴 수 있다.  
쓰기와 읽기의 비용이 다른 시점에 나타나는 전형적인 사례다.

## 코드로 보기

### 인덱스 전파가 커지는 구조

```sql
CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at DATETIME NOT NULL,
  INDEX idx_orders_user_id (user_id),
  INDEX idx_orders_status_created_at (status, created_at)
);
```

```sql
UPDATE orders
SET status = 'DONE'
WHERE id = 1001;
```

### 상태 점검

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_dirty';
SHOW STATUS LIKE 'Innodb_history_list_length';
```

### secondary index 구조 확인

```sql
SHOW INDEX FROM orders;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| secondary index 많이 유지 | 읽기 성능이 좋아진다 | write propagation 비용이 커진다 | 조회가 우선일 때 |
| secondary index 최소화 | write path가 가벼워진다 | 일부 조회가 느려진다 | 쓰기 비중이 높을 때 |
| change buffer 활용 | 랜덤 secondary write를 늦출 수 있다 | merge 비용이 뒤로 밀린다 | 버퍼 풀 miss가 많을 때 |

핵심은 secondary index를 "읽기 보조"로만 보지 말고, **쓰기 전파 대상**으로 봐야 한다는 점이다.

## 꼬리질문

> Q: secondary index는 왜 write 비용을 늘리나요?
> 의도: 인덱스 유지가 read-only가 아니라는 점을 아는지 확인
> 핵심: row 변경이 모든 관련 index entry 수정으로 이어지기 때문이다

> Q: change buffer가 이 경로에서 하는 일은 무엇인가요?
> 의도: page miss 시 지연 합산 메커니즘을 이해하는지 확인
> 핵심: 바로 수정하지 않고 일부 변경을 뒤로 미룬다

> Q: PK를 바꾸면 왜 더 비싼가요?
> 의도: clustered index 전파 비용을 이해하는지 확인
> 핵심: 본문 위치와 secondary index 참조를 함께 흔들기 때문이다

## 한 줄 정리

secondary index change propagation path는 clustered row 수정, secondary entry 갱신, undo/redo, change buffer, purge가 함께 만드는 write cost의 실제 경로다.
