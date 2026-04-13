# Read Ahead and Sequential Scan Behavior

> 한 줄 요약: read-ahead는 "미리 읽기"지만, 범위와 패턴이 맞을 때만 이득이고 틀리면 버퍼 풀 오염만 늘린다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: read ahead, linear read ahead, random read ahead, sequential scan, buffer pool pollution, innodb_read_ahead_threshold, prefetch, page access pattern

## 핵심 개념

- 관련 문서:
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Flush Neighbors, Adaptive Flushing, and IO Capacity](./flush-neighbors-adaptive-flushing-io-capacity.md)
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [B+Tree vs LSM-Tree](./bptree-vs-lsm-tree.md)

read-ahead는 필요한 페이지를 나중에 요청하기 전에 미리 가져오는 최적화다.  
하지만 이 최적화는 "미리 읽으면 무조건 빠르다"가 아니라, **접근 패턴이 예측 가능할 때만** 가치가 있다.

InnoDB에서 read-ahead를 잘 이해하면 다음을 설명할 수 있다.

- 왜 큰 범위 스캔이 갑자기 더 빠르게 보이는가
- 왜 잘못된 read-ahead가 버퍼 풀을 오염시키는가
- 왜 랜덤 접근이 많은 워크로드에서는 도움이 적은가

## 깊이 들어가기

### 1. read-ahead는 어떤 문제를 풀려는가

디스크 I/O는 요청 하나씩 기다리는 것보다, 다음에 필요할 페이지를 미리 가져오면 더 효율적일 수 있다.  
특히 순차적인 페이지 접근이 많으면 효과가 크다.

이건 다음 상황에서 잘 맞는다.

- range scan이 길다
- leaf page를 순서대로 훑는다
- 큰 테이블을 연속적으로 읽는다

### 2. 왜 랜덤 접근에는 잘 안 맞는가

접근 순서가 예측되지 않으면 미리 읽은 페이지가 곧바로 쓰이지 않을 수 있다.  
그럼 결국 버퍼 풀 공간만 차지하고 useful work는 없다.

즉:

- 맞는 패턴이면 latency를 줄인다
- 틀린 패턴이면 cache pollution이 늘어난다

### 3. linear read-ahead와 random read-ahead 감각

MySQL/InnoDB는 페이지 접근 패턴을 보고 read-ahead를 적용할 수 있다.  
운영자 입장에서는 이름보다 "순차성이 충분한가"가 핵심이다.

- clustered index 범위 조회
- 정렬된 PK scan
- 대량 배치 스캔

이런 패턴에서 더 잘 맞는다.

### 4. buffer pool과 같이 봐야 한다

read-ahead가 성공하면 buffer pool hit가 늘 수 있지만, 반대로 무의미한 페이지를 많이 넣으면 LRU를 밀어낼 수 있다.  
그래서 read-ahead는 buffer pool locality와 한 세트다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `read ahead`
- `linear read ahead`
- `random read ahead`
- `innodb_read_ahead_threshold`
- `sequential scan`
- `buffer pool pollution`
- `prefetch`

## 실전 시나리오

### 시나리오 1. 월별 리포트 쿼리가 생각보다 빠르다

연속된 범위를 읽는 쿼리는 read-ahead가 잘 먹으면 더 빨리 보일 수 있다.  
이때는 "인덱스가 좋아서"뿐 아니라, 접근 패턴 자체가 읽기 친화적이기 때문일 수 있다.

### 시나리오 2. 배치가 끝난 뒤 일반 API가 느려진다

대량 scan이 read-ahead를 통해 페이지를 많이 끌어오면, 이후 OLTP 핫셋이 밀려날 수 있다.  
읽기 최적화가 다른 읽기를 해칠 수 있다는 뜻이다.

### 시나리오 3. 랜덤 lookup이 많은데 read-ahead를 믿었다

point lookup 위주의 서비스는 read-ahead 이득이 작다.  
이 경우는 read-ahead보다 covering index, locality, buffer pool hot set이 더 중요하다.

## 코드로 보기

### 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_read_ahead_threshold';
SHOW VARIABLES LIKE 'innodb_random_read_ahead';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
```

### 범위 스캔 예시

```sql
EXPLAIN
SELECT id, created_at
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-05-01'
ORDER BY created_at;
```

### 순차 접근 감각

```sql
SELECT id
FROM orders
WHERE id BETWEEN 100000 AND 120000;
```

### 운영 관찰

```sql
SHOW ENGINE INNODB STATUS\G
```

페이지 접근과 LRU 변화가 함께 보이는지 확인한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| read-ahead 적극 활용 | 순차 scan이 빨라질 수 있다 | 잘못된 prefetch가 캐시를 오염시킨다 | 범위 조회가 클 때 |
| read-ahead 보수화 | buffer pool 오염을 줄인다 | scan 성능 이득을 놓칠 수 있다 | 랜덤 lookup 중심 |
| locality 중심 설계 | 예측 가능한 성능을 얻는다 | PK/인덱스 설계가 까다롭다 | OLTP와 range scan 혼재 |

핵심은 read-ahead를 켜고 끄는 문제가 아니라, **접근 패턴이 실제로 순차적인지**를 확인하는 것이다.

## 꼬리질문

> Q: read-ahead는 왜 순차 스캔에서 유리한가요?
> 의도: 미리 읽기의 본질을 이해하는지 확인
> 핵심: 다음 page를 예상할 수 있기 때문이다

> Q: read-ahead가 왜 캐시 오염을 만들 수 있나요?
> 의도: 잘못된 prefetch 비용을 아는지 확인
> 핵심: 곧바로 쓰지 않을 page를 버퍼 풀에 채울 수 있다

> Q: read-ahead보다 더 먼저 봐야 하는 건 무엇인가요?
> 의도: 인덱스와 locality를 먼저 보는지 확인
> 핵심: 접근 패턴과 인덱스 설계다

## 한 줄 정리

read-ahead는 순차성을 이용해 I/O를 앞당기는 최적화지만, 패턴이 틀리면 버퍼 풀 오염만 늘리므로 접근 패턴과 함께 봐야 한다.
