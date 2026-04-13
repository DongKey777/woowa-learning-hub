# Buffer Pool Read-Ahead and Eviction Interaction

> 한 줄 요약: read-ahead는 다음 page를 미리 가져오지만, eviction과 충돌하면 핫 페이지를 밀어내서 오히려 성능을 망칠 수 있다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: buffer pool eviction, read ahead interaction, LRU eviction, buffer pool pollution, prefetch, hot page, sequential scan, random lookup

## 핵심 개념

- 관련 문서:
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Read Ahead and Sequential Scan Behavior](./read-ahead-sequential-scan-behavior.md)
  - [Clustered Index Locality](./clustered-index-locality.md)
  - [Flush Neighbors, Adaptive Flushing, and IO Capacity](./flush-neighbors-adaptive-flushing-io-capacity.md)

read-ahead는 순차 접근을 미리 예측해 page를 선제적으로 가져오는 최적화다.  
하지만 이 최적화는 buffer pool eviction과 같이 봐야 한다.

핵심은 다음이다.

- 미리 가져온 page가 실제로 곧 사용되면 이득이다
- 미리 가져온 page가 hot page를 밀어내면 손해다
- read-ahead와 eviction은 같은 buffer pool 자원을 두고 경쟁한다

## 깊이 들어가기

### 1. read-ahead는 왜 eviction과 충돌하나

buffer pool은 한정된 공간이다.  
read-ahead가 대량으로 page를 가져오면, LRU에서 덜 쓰이는 page가 밀려날 수 있다.

문제는 그 "덜 쓰이는 page"가 실제로는 OLTP 핫셋일 수 있다는 점이다.

- 순차 scan은 넓은 범위를 읽는다
- OLTP는 작은 hot set을 반복한다
- 둘이 같은 캐시를 공유하면 충돌이 난다

### 2. 선제 로딩이 항상 이득이 아닌 이유

read-ahead가 성공하려면 다음이 맞아야 한다.

- 접근 패턴이 충분히 순차적이다
- 가져온 page를 곧 읽는다
- buffer pool이 그 page를 수용할 여유가 있다

이 조건이 하나라도 깨지면, prefetch는 캐시 오염이 된다.

### 3. hot page와 cold page의 경쟁

hot page는 자주 쓰이는 page다.  
cold page는 일시적으로 읽히는 scan page다.

read-ahead가 지나치면:

- cold page가 hot page를 밀어낸다
- 이후 OLTP miss가 늘어난다
- 디스크 I/O가 다시 커진다

### 4. buffer pool locality와의 관계

read-ahead는 locality가 좋은 범위 조회에서만 잘 맞는다.  
즉 clustered index 순차 스캔이나 정렬된 range scan에서 특히 유리하다.

반대로 랜덤 lookup이 많으면 read-ahead보다 eviction 방지가 더 중요하다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `buffer pool eviction`
- `read ahead interaction`
- `LRU eviction`
- `buffer pool pollution`
- `hot page`
- `prefetch`

## 실전 시나리오

### 시나리오 1. 보고서 쿼리 뒤에 API가 느려진다

대용량 scan이 read-ahead로 buffer pool을 채우고 hot page를 밀어낼 수 있다.  
그 다음 OLTP API는 같은 page를 다시 디스크에서 읽어야 한다.

### 시나리오 2. 순차 조회는 빠른데 전체 시스템은 더 불안정하다

read-ahead 자체는 빨라도 eviction이 함께 일어나면 시스템 전체 latency는 흔들릴 수 있다.  
로컬 최적화가 전체 최적화를 해칠 수 있다.

### 시나리오 3. buffer pool이 작은 환경에서 더 심해진다

여유 공간이 적으면 read-ahead의 부작용이 더 빨리 드러난다.  
작은 메모리에서는 prefetch가 더 쉽게 pollution이 된다.

## 코드로 보기

### read-ahead 관련 설정 확인

```sql
SHOW VARIABLES LIKE 'innodb_read_ahead_threshold';
SHOW VARIABLES LIKE 'innodb_random_read_ahead';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
```

### 상태 관찰

```sql
SHOW ENGINE INNODB STATUS\G
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
```

### 순차 scan 예시

```sql
EXPLAIN
SELECT id, created_at
FROM orders
WHERE created_at >= '2026-04-01'
  AND created_at <  '2026-05-01'
ORDER BY created_at;
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| read-ahead 적극 활용 | 순차 scan이 빨라질 수 있다 | hot page를 밀 수 있다 | 범위 조회가 크고 안정적일 때 |
| read-ahead 보수화 | buffer pool 오염을 줄인다 | scan 이득이 줄 수 있다 | OLTP 중심 |
| buffer pool 확대 | eviction 충돌을 줄인다 | 메모리 비용이 든다 | 핫셋이 크고 여유 메모리가 있을 때 |

핵심은 read-ahead를 독립 최적화로 보지 말고, **eviction과 한 쌍으로 보는 것**이다.

## 꼬리질문

> Q: read-ahead가 왜 buffer pool에 악영향을 줄 수 있나요?
> 의도: prefetch와 eviction 충돌을 아는지 확인
> 핵심: 미리 읽은 page가 hot page를 밀어낼 수 있기 때문이다

> Q: read-ahead와 eviction 중 무엇을 먼저 봐야 하나요?
> 의도: 캐시 오염과 locality를 함께 보는지 확인
> 핵심: 접근 패턴과 buffer pool 여유를 같이 봐야 한다

> Q: 순차 scan이 항상 안전한가요?
> 의도: scan이 다른 워크로드에 주는 영향을 아는지 확인
> 핵심: 아니고, hot set을 밀어낼 수 있다

## 한 줄 정리

read-ahead는 순차성을 이용해 page를 미리 가져오지만, eviction과 충돌하면 buffer pool locality를 깨서 전체 성능을 악화시킬 수 있다.
