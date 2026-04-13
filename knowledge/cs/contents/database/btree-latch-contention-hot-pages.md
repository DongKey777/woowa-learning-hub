# B-Tree Latch Contention and Hot Pages

> 한 줄 요약: B-Tree가 느려지는 순간은 키를 못 찾아서가 아니라, 같은 page와 같은 latch를 너무 많은 세션이 두드릴 때다.

**난이도: 🔴 Advanced**

retrieval-anchor-keywords: B-Tree latch contention, page latch, hot page, buffer pool latch, leaf page contention, insert hotspot, mutex, rw-lock

## 핵심 개념

- 관련 문서:
  - [InnoDB Buffer Pool Internals](./innodb-buffer-pool-internals.md)
  - [Adaptive Hash Index Trade-offs](./adaptive-hash-index-tradeoffs.md)
  - [Insert Hotspot Page Contention](./insert-hotspot-page-contention.md)
  - [Clustered Index Locality](./clustered-index-locality.md)

B-Tree 내부에는 페이지 자체를 보호하는 latch가 있다.  
이건 row lock과 다르다.

- row lock은 트랜잭션 정합성을 지킨다
- latch는 B-Tree 구조와 page 내용을 순간적으로 보호한다

핫 페이지가 생기면 같은 leaf page를 너무 많은 세션이 만지게 되고,  
그 결과 latch contention이 병목이 된다.

## 깊이 들어가기

### 1. latch는 왜 필요한가

B-Tree는 검색과 삽입 중에 노드 분할, 포인터 갱신, 페이지 연결을 한다.  
이때 구조가 깨지지 않도록 짧게 잡는 락이 latch다.

중요한 점:

- 매우 짧은 임계구역 보호
- 트랜잭션 락보다 훨씬 내부적
- hot page가 있으면 경합이 급증

### 2. hot page는 어떻게 생기는가

같은 범위에 쓰기나 읽기가 몰리면 특정 page만 계속 바뀐다.

- 시간순 PK 마지막 페이지
- 인기 사용자/카운터 row가 몰린 페이지
- 특정 tenant의 최근 데이터 페이지

이런 곳이 hot page가 된다.

### 3. latch contention과 row contention은 다르다

row lock이 없어도 latch contention은 생길 수 있다.  
반대로 row lock이 강해도 latch는 덜할 수 있다.

그래서 "락 대기"를 볼 때는 row-level만 보지 말고 page-level도 생각해야 한다.

### 4. read-mostly여도 경합이 생긴다

읽기라고 항상 안전한 게 아니다.  
같은 page를 동시에 읽고 구조를 보정하거나, AHI와 버퍼풀 경합이 섞이면 내부 latch가 바빠질 수 있다.

### 5. retrieval anchors

이 문서를 다시 찾을 때 유용한 키워드는 다음이다.

- `B-Tree latch contention`
- `page latch`
- `hot page`
- `leaf page contention`
- `mutex`
- `rw-lock`

## 실전 시나리오

### 시나리오 1. insert TPS가 특정 순간부터 안 늘어난다

모든 요청이 한쪽 끝 page에 몰리면, row lock보다 latch가 먼저 병목이 될 수 있다.  
이때는 PK 패턴과 page split, hot page를 같이 봐야 한다.

### 시나리오 2. AHI를 껐더니 일부 부하는 나아졌다

같은 hot path에서 AHI와 latch가 경쟁했다면, AHI를 끄는 것이 전체 경합을 줄이는 데 도움이 될 수 있다.  
하지만 이것은 근본 해결이 아니라 증상 완화일 수 있다.

### 시나리오 3. 특정 tenant만 유독 느리다

한 tenant의 최근 데이터가 같은 page에 몰려 있으면, 그 page가 hot page가 된다.  
멀티테넌트 구조에서는 이런 쏠림이 더 자주 드러난다.

## 코드로 보기

### insert hotspot 감각

```sql
INSERT INTO orders (id, user_id, status, created_at)
VALUES (900001, 1001, 'PAID', NOW());
```

### 상태 점검

```sql
SHOW ENGINE INNODB STATUS\G
```

### 경합 완화 힌트

```sql
SHOW VARIABLES LIKE 'innodb_buffer_pool_instances';
SHOW VARIABLES LIKE 'innodb_adaptive_hash_index';
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| latch 경합 감수 | 구현이 단순하다 | hot page에서 병목이 된다 | 트래픽이 적을 때 |
| page hotspot 분산 | 경합이 줄 수 있다 | PK/인덱스 설계가 복잡해진다 | 고빈도 insert/read |
| AHI 조절 | 경합을 줄일 수 있다 | read 성능이 흔들릴 수 있다 | 특정 hot path |

핵심은 latch contention을 row lock 문제로 오해하지 않고, **B-Tree page 자체의 병목**으로 보는 것이다.

## 꼬리질문

> Q: latch와 row lock은 어떻게 다른가요?
> 의도: 내부 구조 보호와 트랜잭션 보호를 구분하는지 확인
> 핵심: latch는 순간적 구조 보호, row lock은 정합성 보호다

> Q: hot page는 왜 생기나요?
> 의도: PK 패턴과 접근 쏠림을 아는지 확인
> 핵심: 같은 페이지로 읽기/쓰기가 몰리기 때문이다

> Q: latch contention을 줄이려면 무엇을 먼저 보나요?
> 의도: 구조적 병목을 찾는 순서를 아는지 확인
> 핵심: PK 순서, insert 패턴, hotspot 분산이다

## 한 줄 정리

B-Tree latch contention은 같은 page를 너무 많은 세션이 만질 때 생기는 내부 경합이고, PK와 access pattern을 바꾸지 않으면 반복된다.
