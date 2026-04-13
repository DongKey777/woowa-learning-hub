# InnoDB Buffer Pool Internals

> 한 줄 요약: 버퍼 풀은 "메모리 캐시"가 아니라, InnoDB가 랜덤 I/O를 줄이고 dirty page를 조절하며 읽기 지연을 안정화하는 핵심 작업 공간이다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: buffer pool, LRU, free list, flush list, dirty page, adaptive hash index, buffer pool instances, page cleaner, hot pages, page miss

## 핵심 개념

- 관련 문서:
  - [Redo Log, Undo Log, Checkpoint, Crash Recovery](./redo-log-undo-log-checkpoint-crash-recovery.md)
  - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
  - [인덱스와 실행 계획](./index-and-explain.md)
  - [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)

InnoDB 버퍼 풀은 디스크 페이지를 그대로 올려 두는 거대한 캐시다.  
하지만 운영에서 더 중요한 역할은 단순 캐시가 아니라 다음 3가지를 동시에 책임지는 점이다.

- 자주 읽는 페이지를 메모리에 붙잡아 두기
- 더티 페이지를 제어해서 flush 압력을 분산하기
- checkpoint와 crash recovery의 부담을 줄이기

즉 버퍼 풀이 흔들리면 읽기 성능만 떨어지는 게 아니라, 쓰기 지연과 복구 시간까지 같이 흔들린다.

## 깊이 들어가기

### 1. InnoDB는 페이지 단위로 일한다

InnoDB는 레코드를 직접 가져오는 게 아니라 보통 16KB 페이지 단위로 읽는다.  
그래서 한 row 조회도 실제로는 "어느 페이지가 버퍼 풀에 있느냐"의 문제로 바뀐다.

페이지를 찾는 대략적인 흐름은 이렇다.

1. 버퍼 풀에서 페이지를 찾는다.
2. 있으면 바로 읽는다.
3. 없으면 디스크에서 읽어 온다.
4. 읽어 온 페이지를 free list에서 할당해 올린 뒤 LRU에 넣는다.

이때 인덱스가 좋아도 버퍼 풀이 차가우면 초반 지연이 크게 튈 수 있다.

### 2. LRU는 단순히 "최근 사용"만 보지 않는다

InnoDB 버퍼 풀은 LRU를 조금 변형해서 쓴다.

- 새로 읽은 페이지가 곧바로 핫 영역을 망치지 않도록 중간 지점에 넣는다
- 자주 재사용되는 페이지는 오래 살아남는다
- 한 번 훑는 대용량 스캔이 전체 캐시를 오염시키지 않도록 방어한다

이게 중요한 이유는 명확하다.

- OLTP는 작은 핫셋을 반복해서 읽는다
- 대량 배치나 보고서 쿼리는 넓은 범위를 스캔한다
- 둘이 같은 LRU를 공유하면 핫 페이지가 밀려난다

### 3. dirty page와 flush list가 성능을 좌우한다

버퍼 풀에서 페이지가 수정되면 그 페이지는 dirty page가 된다.  
dirty page는 메모리 안에만 바뀐 상태이므로, 결국 디스크로 내려가야 한다.

이 dirty page들을 관리하는 축이 flush list다.

- dirty page가 쌓이면 flush pressure가 커진다
- checkpoint age가 커지면 로그와 페이지의 간극이 커진다
- page cleaner가 몰아서 flush하면 지연이 튄다

즉 버퍼 풀은 읽기 캐시이면서 동시에 쓰기 흡수층이다.

### 4. buffer pool instance는 경합을 줄이지만, 조각화도 만든다

버퍼 풀을 여러 instance로 나누면 내부 mutex 경합이 줄어들 수 있다.  
하지만 모든 상황에서 좋은 것은 아니다.

- 인스턴스가 많으면 관리 오버헤드가 늘어난다
- 작은 워크로드에서는 페이지가 조각날 수 있다
- 한쪽 instance만 뜨거우면 균형이 깨질 수 있다

그래서 "무조건 많게"가 아니라, 동시성과 워크로드 크기에 맞춰 봐야 한다.

### 5. adaptive hash index는 만능이 아니다

AHI는 자주 반복되는 탐색을 더 빠르게 해 줄 수 있다.  
하지만 경합이 심하면 오히려 병목이 될 수 있다.

운영 감각은 이렇다.

- point lookup이 많고 패턴이 반복되면 이득
- 스캔과 쓰기 비중이 크면 효과가 적거나 불안정할 수 있다

### 6. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `buffer pool`
- `LRU`
- `free list`
- `flush list`
- `dirty page`
- `adaptive hash index`
- `page cleaner`
- `Innodb_buffer_pool_reads`
- `Innodb_buffer_pool_pages_dirty`

## 실전 시나리오

### 시나리오 1. 재시작 직후 응답 시간이 뚝 떨어진다

DB를 재기동하면 버퍼 풀이 비어 있다.  
그 순간에는 같은 쿼리도 디스크에서 페이지를 다시 읽어야 해서 지연이 커진다.

운영에서 흔한 패턴:

- 재기동 직후 read latency 급증
- 몇 분 뒤 점차 회복
- warm-up이 없으면 p95가 오래 흔들림

### 시나리오 2. 배치 하나가 핫 페이지를 밀어낸다

대용량 리포트 쿼리가 테이블을 넓게 훑으면, 자주 쓰는 페이지가 LRU에서 밀려날 수 있다.  
그 다음부터는 일반 API가 같은 페이지를 다시 디스크에서 읽는다.

이 문제는 인덱스 설계만으로 끝나지 않고, 워크로드 분리와 쿼리 시간대 제어까지 같이 봐야 한다.

### 시나리오 3. 쓰기량이 늘자 읽기까지 같이 느려진다

dirty page가 많이 쌓이면 flush가 몰리고, 그 와중에 디스크 I/O가 읽기와 쓰기를 함께 압박한다.  
결국 읽기 쿼리도 버퍼 풀 miss와 flush 경쟁의 영향을 받는다.

## 코드로 보기

### 버퍼 풀 상태 확인

```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';

SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_dirty';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_free';
```

### 페이지 단위 관찰

```sql
SELECT POOL_ID, SPACE, PAGE_NUMBER, PAGE_TYPE, IS_DIRTY
FROM INFORMATION_SCHEMA.INNODB_BUFFER_PAGE
WHERE SPACE IS NOT NULL
LIMIT 10;
```

### 디버깅 관점의 체크

```sql
SHOW ENGINE INNODB STATUS\G
```

볼 포인트:

- LRU 리스트가 과도하게 흔들리는지
- dirty page가 계속 쌓이는지
- flush가 따라가지 못하는지

### 워밍업 감각

```bash
mysql -e "SELECT id, user_id, status FROM orders WHERE user_id BETWEEN 1 AND 10000"
```

핫셋을 미리 읽어 두면 재기동 직후의 급격한 miss를 조금 완화할 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 버퍼 풀 크게 유지 | hit ratio가 높아진다 | 메모리를 많이 먹고 OS 캐시를 압박한다 | OLTP 핫셋이 명확할 때 |
| 버퍼 풀 인스턴스 늘리기 | 경합이 줄 수 있다 | 조각화와 관리 오버헤드가 생긴다 | 동시성이 높을 때 |
| AHI 활성화 | 반복 조회가 빨라질 수 있다 | 경합과 예측 불안정이 생길 수 있다 | 반복 point lookup이 많을 때 |
| 대용량 스캔 분리 | 핫셋 오염을 줄인다 | 운영과 쿼리 구조가 복잡해진다 | 분석성 쿼리가 섞여 있을 때 |

핵심은 메모리를 많이 주는 게 아니라, **핫 페이지가 계속 핫하게 유지되도록 워크로드를 정리하는 것**이다.

## 꼬리질문

> Q: 버퍼 풀 hit ratio가 높으면 항상 좋은가요?
> 의도: 캐시 지표를 절대화하는지 확인
> 핵심: hit ratio만 보면 안 되고, flush 지연과 dirty page 압력도 같이 봐야 한다

> Q: buffer pool instance를 늘리면 왜 빨라질 수 있나요?
> 의도: 내부 경합 구조 이해 여부 확인
> 핵심: mutex 경합을 줄이지만, 무조건 많을수록 좋은 것은 아니다

> Q: 대량 조회 쿼리가 왜 OLTP를 느리게 만드나요?
> 의도: LRU 오염과 워크로드 간섭 이해 여부 확인
> 핵심: 핫 페이지를 밀어내서 이후 miss와 I/O를 늘리기 때문이다

## 한 줄 정리

버퍼 풀은 InnoDB 성능의 심장이고, 읽기 캐시, dirty page 완충, flush 압력 조절을 동시에 이해해야 운영 병목을 설명할 수 있다.
