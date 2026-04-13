# Hot Row Contention과 Counter Sharding

> 한 줄 요약: 하나의 카운터 row를 여러 요청이 동시에 두드리기 시작하면, DB는 저장소가 아니라 전역 mutex처럼 동작한다.

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Deadlock Case Study](./deadlock-case-study.md), [인덱스와 실행 계획](./index-and-explain.md)
Retrieval anchors: `hot row contention`, `counter hotspot`, `lock wait timeout`, `counter sharding`

## 핵심 개념

핫 로우 contention은 너무 많은 트랜잭션이 **같은 row** 또는 **같은 인덱스 경로**를 동시에 수정하면서 직렬화되는 현상이다.

왜 중요한가:

- 좋아요 수, 재고 수, 포인트 잔액, 시퀀스 발급처럼 “한 줄 숫자”가 자주 갱신되는 순간부터 병목이 생긴다
- 트래픽이 늘수록 응답 시간보다 먼저 락 대기 시간이 폭증한다
- 실패는 데이터 정합성보다 먼저 `lock wait timeout`이나 데드락 재시도로 드러난다

핫 로우 문제의 본질은 “DB가 느리다”가 아니라, **한 row에 모든 동시성이 몰린다**는 데 있다.

## 깊이 들어가기

### 1. 왜 카운터 하나가 병목이 되는가

`UPDATE counters SET value = value + 1 WHERE id = 1;` 같은 문장은 논리적으로는 단순하지만, 실제로는 같은 레코드에 대한 배타적 접근을 만든다.

동시 요청이 100개면:

- 100개가 같은 row lock을 기다린다
- 각 트랜잭션의 커밋이 앞선 트랜잭션 종료에 묶인다
- p95/p99가 급격히 튄다

이 문제는 row lock만의 이야기가 아니다.

- secondary index가 같이 갱신되면 인덱스 레벨 경합도 늘어난다
- auto-increment나 단일 sequence 테이블은 더 쉽게 핫스팟이 된다
- 작은 트랜잭션이라도 같은 row를 건드리면 결국 직렬화된다

### 2. 샤딩이 왜 효과적인가

핵심은 하나의 논리 카운터를 여러 물리 조각으로 나누는 것이다.

예:

- `post_like_count` 1개 대신 `post_like_count_shard` 16개
- 유저/주문/시간 버킷 해시로 shard를 분산
- 쓰기는 한 shard에만 기록하고, 읽기는 shard 합산

이 방식은 같은 총량을 유지하면서도 **동시 업데이트 경합을 분산**한다.

### 3. 언제 오히려 손해가 되는가

샤딩은 쓰기 경합을 낮추는 대신 읽기와 운영 복잡도를 올린다.

- 총합 조회가 비싸진다
- shard 불균형이 생기면 특정 조각만 다시 핫해진다
- shard 수를 나중에 바꾸면 backfill이 필요하다

즉 “쓰기 폭주를 읽기 비용으로 바꾸는 전략”이다.

## 실전 시나리오

### 시나리오 1: 좋아요 수가 급증하는 게시글

인기 글 하나에 요청이 몰리면 단일 카운터 row가 병목이 된다.  
정합성은 맞는데, 응답 시간은 락 대기 때문에 망가진다.

### 시나리오 2: 재고 1개를 두 사람이 동시에 예약

재고 row 하나를 두고 경쟁하면 안전하지만 느리다.  
이때는 row 하나를 지키는 방식보다, “예약 가능 수량”을 어떻게 분산할지 다시 설계해야 한다.

### 시나리오 3: 일별 시퀀스 발급이 트래픽 병목이 됨

`yyyyMMdd` 단위 sequence row 하나에 모든 요청이 몰리면, 날짜가 바뀌는 순간에도 같은 row가 뜨거워진다.  
이 경우 시간 버킷이나 분산 시퀀스가 더 낫다.

## 코드로 보기

```sql
-- 병목이 되는 단일 카운터
CREATE TABLE post_like_count (
  post_id BIGINT PRIMARY KEY,
  value BIGINT NOT NULL
);

START TRANSACTION;
UPDATE post_like_count
SET value = value + 1
WHERE post_id = 42;
COMMIT;
```

```sql
-- 샤딩된 카운터
CREATE TABLE post_like_count_shard (
  post_id BIGINT NOT NULL,
  shard_id INT NOT NULL,
  value BIGINT NOT NULL,
  PRIMARY KEY (post_id, shard_id)
);

-- 쓰기: shard 하나만 갱신
INSERT INTO post_like_count_shard (post_id, shard_id, value)
VALUES (42, MOD(CRC32(UUID()), 16), 1)
ON DUPLICATE KEY UPDATE value = value + 1;

-- 읽기: 합산
SELECT SUM(value)
FROM post_like_count_shard
WHERE post_id = 42;
```

샤드 개수는 “많을수록 좋다”가 아니라, 읽기 비용과 경합 분산의 균형으로 정한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 단일 카운터 row | 구현이 가장 쉽다 | 동시성 증가 시 병목이 심하다 | 트래픽이 작고 정확성이 최우선일 때 |
| 샤딩 카운터 | 쓰기 경합을 크게 줄인다 | 읽기와 운영이 복잡해진다 | 인기 글, 공용 시퀀스, 고빈도 집계 |
| append-only 이벤트 | 쓰기 확장성이 좋다 | 최종 합산 비용이 있다 | 집계가 비동기로 허용될 때 |
| 캐시 + 비동기 동기화 | 읽기가 빠르다 | 캐시 불일치 위험이 있다 | 정확도보다 응답성이 중요할 때 |

## 꼬리질문

> Q: 왜 카운터 row 하나가 전체 시스템 병목이 되나요?
> 의도: row lock 경합이 서비스 전체 latency를 직렬화하는 구조인지 확인
> 핵심: 같은 row에 쓰기가 집중되면 DB가 전역 락처럼 보인다

> Q: 샤딩 카운터는 왜 읽기 성능이 나빠질 수 있나요?
> 의도: 쓰기 분산과 조회 비용의 trade-off 이해 여부 확인
> 핵심: 총합을 구하려면 shard를 합쳐야 한다

> Q: `SELECT ... FOR UPDATE`로 해결하면 안 되나요?
> 의도: 비관적 락이 병목을 없애지 못한다는 점을 아는지 확인
> 핵심: 락은 안전성을 높이지만 경합 자체는 줄이지 못한다

## 한 줄 정리

핫 로우 contention은 “정합성 문제”가 아니라 “동시성이 한 row로 몰린 설계 문제”이고, 샤딩이나 append-only로 경합 지점을 분산해야 한다.
