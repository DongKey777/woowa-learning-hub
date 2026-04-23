# Compare-and-Set와 Version Columns

> 한 줄 요약: version column은 DB에서 가장 실용적인 compare-and-set 도구이고, 읽기-수정-쓰기의 마지막 경합을 저장 시점에 잡아준다.

**난이도: 🔴 Advanced**

관련 문서: [Lost Update Detection Patterns](./lost-update-detection-patterns.md), [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Version Column Retry Walkthrough](./version-column-retry-walkthrough.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [Spring/JPA 락킹 예제 가이드](./spring-jpa-locking-example-guide.md)
retrieval-anchor-keywords: compare and set, version column, optimistic lock, conditional update, write conflict, optimistic lock failure, update count 0, version mismatch

## 핵심 개념

Compare-and-set(CAS)는 “내가 읽은 값이 아직 그 값일 때만 바꾸겠다”는 원자적 갱신 방식이다.  
DB에서는 보통 version column으로 구현한다.

왜 중요한가:

- lost update를 막는 가장 흔한 패턴이다
- 락을 오래 잡지 않고도 충돌을 감지할 수 있다
- 재시도와 잘 결합되며 분산 시스템에서 매우 실용적이다

version column은 단순 카운터가 아니라, **동시 수정의 합의 표식**이다.

## 깊이 들어가기

### 1. CAS가 왜 필요한가

읽고 나서 계산한 다음 저장하는 구조는 항상 경합에 노출된다.

- 누군가 먼저 바꿀 수 있다
- 내가 읽은 상태가 더 이상 최신이 아닐 수 있다
- 저장 시점에 충돌을 알아야 한다

CAS는 이 충돌을 저장 문장 하나로 밀어 넣는다.

### 2. version column 설계

보통 다음처럼 둔다.

- `version BIGINT NOT NULL`
- update 시 `version = version + 1`
- where 절에 `version = ?`를 넣음

이 구조의 핵심은 row count다.

- 1이면 성공
- 0이면 누군가 먼저 바꿨다

### 3. 낙관적 락과의 관계

낙관적 락은 개념이고, version column CAS는 구현이다.  
실무에서는 둘을 거의 같은 뜻으로 쓰지만, 엄밀히는 version check가 구체적 방식이다.

### 4. 언제 실패를 재시도할까

CAS 실패는 대개 재시도 가능한 실패다.

- 다른 사용자가 먼저 저장했다
- 최신 값을 다시 읽어야 한다
- 다시 계산해서 저장해야 한다

하지만 재시도 전에, 같은 요청이 중복 부작용을 만들지 않도록 멱등성도 함께 봐야 한다.

## 실전 시나리오

### 시나리오 1: 프로필 닉네임 변경 충돌

두 화면이 같은 프로필을 열어둔 채 각각 수정하면, 뒤늦은 저장이 덮어쓸 수 있다.  
version CAS로 이를 막고 재시도한다.

### 시나리오 2: 재고 차감이 경합함

`stock > 0` 조건과 version CAS를 같이 쓰면 안전하다.  
단순 조회 후 저장보다 훨씬 낫다.

### 시나리오 3: 설정값이 원복됨

배치와 운영자가 같은 설정을 동시에 바꾸는 경우, CAS가 없으면 마지막 저장이 이긴다.

## 코드로 보기

```sql
UPDATE profile
SET nickname = 'new-name',
    version = version + 1
WHERE id = 10
  AND version = 7;
```

```java
int updated = jdbcTemplate.update(
    """
    UPDATE inventory
    SET stock = stock - 1, version = version + 1
    WHERE sku = ? AND version = ? AND stock > 0
    """,
    sku, version
);
if (updated == 0) {
    throw new ConcurrentModificationException();
}
```

CAS는 읽기와 쓰기를 분리하되, **저장 시점에만 충돌을 원자적으로 판정**한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| version CAS | 빠르고 단순하다 | 재시도 코드가 필요하다 | 대부분의 업데이트 |
| 비관적 락 | 즉시 충돌을 막는다 | 경합이 크다 | 충돌이 잦을 때 |
| 원자적 수식 업데이트 | 짧고 강하다 | SQL로 로직을 옮겨야 한다 | 카운터/재고 |
| DB constraint | 가장 강하다 | 모델링이 필요하다 | 불변식이 명확할 때 |

## 꼬리질문

> Q: version column이 왜 CAS 역할을 하나요?
> 의도: 저장 시점 조건부 갱신의 원리를 아는지 확인
> 핵심: 내가 읽은 version이 아직 맞을 때만 업데이트되기 때문이다

> Q: CAS 실패 시 무조건 retry하면 되나요?
> 의도: 재시도와 멱등성의 결합을 아는지 확인
> 핵심: 재시도는 가능하지만 중복 부작용을 막아야 한다

> Q: version을 int로 두면 충분한가요?
> 의도: 오버플로와 운영 수명을 생각하는지 확인
> 핵심: 장수 테이블은 bigint가 더 안전하다

## 한 줄 정리

Version column CAS는 저장 시점에 충돌을 판정하는 가장 실용적인 방식이고, lost update 방지와 재시도의 출발점이다.
