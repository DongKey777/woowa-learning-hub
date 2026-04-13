# Online Backfill Consistency와 워터마크 전략

> 한 줄 요약: 백필은 “한 번 복사하면 끝”이 아니라, 복사 중에 들어오는 변경까지 포함해 정합성을 맞추는 절차다.

관련 문서: [온라인 스키마 변경 전략](./online-schema-change-strategies.md), [CDC, Debezium, Outbox, Binlog](./cdc-debezium-outbox-binlog.md), [Idempotency Key and Deduplication](./idempotency-key-and-deduplication.md)
Retrieval anchors: `backfill watermark`, `chunk copy`, `dual write`, `catch-up`, `validation`

## 핵심 개념

Online backfill은 운영 중인 테이블이나 새 구조에 기존 데이터를 채워 넣는 작업이다.  
문제는 복사가 시작된 뒤에도 원본 데이터는 계속 바뀐다는 점이다.

왜 중요한가:

- 컬럼 추가 후 기존 데이터를 새 컬럼에 채워야 한다
- denormalized summary table을 만들 때 과거 데이터까지 맞춰야 한다
- CDC 없이 큰 테이블을 옮기면 누락과 중복이 쉽게 생긴다

백필의 핵심은 속도가 아니라 **복사 시점과 변경 시점의 경계**를 설계하는 것이다.

## 깊이 들어가기

### 1. 백필이 틀어지는 이유

백필을 단순히 `INSERT INTO new SELECT FROM old`로 생각하면 안 된다.

- 복사 중에 원본 row가 업데이트될 수 있다
- 복사 후에 delete가 발생할 수 있다
- 같은 row가 여러 번 재시도되며 중복될 수 있다
- 일부 chunk는 성공하고 일부는 실패할 수 있다

즉 backfill은 상태 전송이 아니라 **상태 동기화**다.

### 2. 워터마크가 필요한 이유

안전한 백필은 보통 기준점을 하나 둔다.

- `created_at` 또는 `updated_at`
- 증가하는 PK 범위
- binlog position / LSN / GTID

이 기준점 이전의 데이터를 먼저 복사하고, 이후 변경분은 catch-up 단계에서 다시 반영한다.

이렇게 해야 “복사 중간에 바뀐 row”를 빠뜨리지 않는다.

### 3. idempotent하게 만들어야 하는 이유

백필 작업은 실패와 재시도가 기본값이다.

- chunk 17이 두 번 실행될 수 있다
- 네트워크 문제로 중간 결과를 다시 넣어야 할 수 있다
- validation 후 일부 구간만 재처리할 수 있다

그래서 `INSERT ... ON DUPLICATE KEY UPDATE`처럼 재실행해도 결과가 같아야 한다.

### 4. validation은 어디서 해야 하나

검증은 단순 row count로 끝나지 않는다.

- row count 비교
- checksum 비교
- sample diff
- late write 재동기화

특히 count가 같아도 값이 다른 경우가 많으므로, 중요한 컬럼은 별도 검증이 필요하다.

## 실전 시나리오

### 시나리오 1: 새 요약 테이블을 만드는 동안 주문이 계속 들어옴

과거 주문을 복사하는 동안 신규 주문이 계속 쌓인다.  
이때 watermark 없이 복사만 하면 일부 주문은 새 테이블에 안 들어간다.

### 시나리오 2: 컬럼 백필이 재시도되면서 일부 row가 덮임

`NULL -> 값` 채우기 작업이 chunk 재시도로 두 번 실행되면, idempotent하지 않은 쿼리는 결과를 망친다.

### 시나리오 3: cutover 직전에 늦게 도착한 write가 빠짐

복사와 live write를 분리하지 않으면 마지막 순간의 변경이 유실될 수 있다.  
그래서 cutover 전 catch-up 단계가 필요하다.

## 코드로 보기

```sql
-- chunk copy: PK 범위로 끊어서 복사
INSERT INTO user_profile_new (id, name, tier, updated_at)
SELECT id, name, tier, updated_at
FROM user_profile
WHERE id BETWEEN 100000 AND 110000
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  tier = VALUES(tier),
  updated_at = VALUES(updated_at);
```

```sql
-- catch-up: 워터마크 이후의 변경 재반영
UPDATE user_profile_new n
JOIN user_profile o ON o.id = n.id
SET n.name = o.name,
    n.tier = o.tier,
    n.updated_at = o.updated_at
WHERE o.updated_at > '2026-04-09 12:00:00';
```

```sql
-- 검증
SELECT COUNT(*) FROM user_profile;
SELECT COUNT(*) FROM user_profile_new;
```

실무에서는 여기에 checksum, sample query, tombstone 처리까지 붙여야 안정적이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| snapshot copy only | 구현이 단순하다 | 변경 누락 위험이 있다 | 짧은 점검용 작업 |
| snapshot + catch-up | 정합성이 높다 | 워터마크 관리가 필요하다 | 대부분의 온라인 백필 |
| dual write | 즉시 반영에 가깝다 | 애플리케이션 복잡도가 높다 | 새 구조를 바로 써야 할 때 |
| CDC replay | 자동화가 좋다 | 운영 파이프라인이 필요하다 | 대규모 마이그레이션 |

## 꼬리질문

> Q: 백필을 단순 `INSERT ... SELECT`로 끝내면 왜 안 되나요?
> 의도: 복사 중에 발생하는 write를 놓치는 문제를 아는지 확인
> 핵심: 복사와 변경이 동시에 일어나므로 catch-up이 필요하다

> Q: 왜 워터마크가 필요한가요?
> 의도: 정합성 경계를 이해하는지 확인
> 핵심: 어느 시점까지 복사했는지 기준이 있어야 누락을 막는다

> Q: 백필 작업을 재시도 가능하게 만들려면 무엇이 중요하나요?
> 의도: idempotent 설계 감각 확인
> 핵심: 중복 실행해도 최종 결과가 같아야 한다

## 한 줄 정리

온라인 백필은 대량 복사가 아니라, 워터마크·catch-up·idempotent 재시도로 원본 변경까지 포함해 맞추는 동기화 작업이다.
