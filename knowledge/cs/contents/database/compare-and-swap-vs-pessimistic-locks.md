# Compare-and-Swap과 Pessimistic Locks

> 한 줄 요약: CAS는 충돌을 나중에 감지하고, pessimistic lock은 충돌을 미리 막는다.

**난이도: 🔴 Advanced**

관련 문서: [Transaction Boundary, Isolation, and Locking Decision Framework](./transaction-boundary-isolation-locking-decision-framework.md), [Compare-and-Set와 Version Columns](./compare-and-set-version-columns.md), [Lost Update Detection Patterns](./lost-update-detection-patterns.md), [Advisory Locks와 Row Locks](./advisory-locks-vs-row-locks.md), [Queue Claim with `SKIP LOCKED`, Fairness, and Starvation Trade-offs](./queue-claim-skip-locked-fairness.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
retrieval-anchor-keywords: compare and swap, pessimistic lock, optimistic lock, version column, select for update, skip locked, CAS vs pessimistic locking, lost update prevention, retry on version conflict, lock first or retry later

## 핵심 개념

CAS와 pessimistic lock은 둘 다 동시성 충돌을 다루지만 철학이 다르다.

왜 중요한가:

- 충돌이 적은 작업과 많은 작업은 같은 해법이 아니다
- 락을 오래 잡으면 대기와 데드락이 늘고, CAS는 재시도가 늘 수 있다
- 어떤 문제는 빨리 실패하는 게 맞고, 어떤 문제는 먼저 막는 게 맞다

핵심은 “더 안전한 것”이 아니라, **작업 특성에 맞는 경합 제어 방식**을 고르는 것이다.

## 깊이 들어가기

### 1. CAS의 성격

CAS는 읽은 version이 맞을 때만 저장한다.

- 장점: 락을 오래 잡지 않는다
- 단점: 충돌 시 재시도 필요

읽기 비중이 높고 충돌이 낮을 때 강하다.

### 2. pessimistic lock의 성격

pessimistic lock은 `SELECT ... FOR UPDATE`처럼 먼저 잠근다.

- 장점: 충돌이 잦아도 안전하다
- 단점: 대기와 데드락 가능성이 커진다

충돌이 잦고, 한 번의 실패가 치명적일 때 적합하다.

### 3. 어떤 상황에서 CAS가 더 낫나

- 프로필 변경
- 설정값 수정
- 읽고 계산 후 저장하는 작업

이런 경우는 보통 재시도가 쉬워 CAS가 유리하다.

### 4. 어떤 상황에서 pessimistic lock이 더 낫나

- 재고 1개 구매
- 순서가 중요한 예약
- 다수 row를 읽고 일관된 결정을 내려야 하는 경우

이 경우는 충돌을 빨리 끝내는 것이 중요하다.

## 실전 시나리오

### 시나리오 1: 프로필 수정이 자주 겹침

충돌이 빈번하지 않고 재시도가 쉬우면 CAS가 더 낫다.

### 시나리오 2: 재고 차감이 몰림

충돌이 많고 한 번의 중복 차감이 치명적이면 pessimistic lock이 더 낫다.

### 시나리오 3: 긴 작업과 섞임

외부 호출이 섞인 긴 작업에 pessimistic lock을 쓰면 대기가 길어진다.  
이럴 때는 CAS + 짧은 검증이 더 안전할 수 있다.

## 코드로 보기

```sql
-- CAS
UPDATE inventory
SET stock = stock - 1, version = version + 1
WHERE sku = 'SKU-1' AND version = 7 AND stock > 0;

-- pessimistic lock
START TRANSACTION;
SELECT stock FROM inventory WHERE sku = 'SKU-1' FOR UPDATE;
UPDATE inventory SET stock = stock - 1 WHERE sku = 'SKU-1';
COMMIT;
```

```java
// 충돌이 많지 않으면 CAS, 충돌이 많으면 lock을 고려한다.
```

CAS는 충돌을 감지하고, pessimistic lock은 충돌을 피한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| CAS/version check | 확장성이 좋다 | 재시도가 필요하다 | 충돌이 낮을 때 |
| pessimistic lock | 결과가 안정적이다 | 경합이 커진다 | 충돌이 높을 때 |
| hybrid | 유연하다 | 정책이 복잡하다 | 상황별 선택 필요 |
| no lock | 단순하다 | lost update 위험 | 거의 없음 |

## 꼬리질문

> Q: CAS와 pessimistic lock의 차이는 무엇인가요?
> 의도: 충돌 감지와 충돌 예방의 차이를 아는지 확인
> 핵심: CAS는 나중에 확인하고, pessimistic lock은 미리 막는다

> Q: 언제 CAS가 더 적합한가요?
> 의도: 재시도 가능한 작업의 특성을 아는지 확인
> 핵심: 충돌이 적고 재시도 비용이 낮을 때다

> Q: 언제 pessimistic lock이 더 적합한가요?
> 의도: 충돌이 잦은 작업의 안정성을 아는지 확인
> 핵심: 중복이나 순서 꼬임이 치명적일 때다

## 한 줄 정리

CAS는 나중에 충돌을 감지하는 방식이고, pessimistic lock은 미리 충돌을 막는 방식이다.
