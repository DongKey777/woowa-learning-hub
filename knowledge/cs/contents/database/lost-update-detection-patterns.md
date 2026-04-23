# Lost Update Detection Patterns

> 한 줄 요약: lost update는 “마지막 저장이 앞선 변경을 덮어버리는” 문제이고, 버전 검증이나 원자적 갱신으로 막아야 한다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Lost Update vs Write Skew vs Phantom Timeline Guide](./lost-update-vs-write-skew-vs-phantom-timeline-guide.md), [Transaction Retry와 Serialization Failure 패턴](./transaction-retry-serialization-failure-patterns.md), [멱등성 키와 중복 방지](./idempotency-key-and-deduplication.md)
retrieval-anchor-keywords: lost update, version check, optimistic locking, compare and swap, atomic update, same row overwrite, lost update vs write skew

## 핵심 개념

Lost update는 두 트랜잭션이 같은 초기 값을 읽고 각각 변경한 뒤, 뒤늦은 저장이 앞선 저장을 덮어쓰는 현상이다.

왜 중요한가:

- 재고, 포인트, 프로필, 설정값이 조용히 망가질 수 있다
- 에러가 아니라 정상 응답으로 보이기 때문에 더 위험하다
- DB가 실패를 알려주지 않으면 애플리케이션이 놓치기 쉽다

문제는 “충돌이 났다”가 아니라, **충돌이 조용히 사라진다**는 점이다.

## 깊이 들어가기

### 1. lost update가 생기는 전형적인 흐름

1. A가 balance=100을 읽는다
2. B도 balance=100을 읽는다
3. A가 90으로 저장한다
4. B가 80으로 저장한다

결과적으로 A의 10 차감이 사라진다.  
이런 문제는 읽기-수정-쓰기 패턴에서 가장 자주 나타난다.

### 2. 어떻게 감지하는가

대표적인 감지 방법은 다음과 같다.

- version column 비교
- updated_at 비교
- DB의 optimistic lock 에러 처리
- 조건부 update 결과 row count 확인

핵심은 저장 시점에 “내가 읽은 버전이 아직 맞는가”를 검사하는 것이다.

### 3. 어떻게 막는가

막는 방식도 여러 가지다.

- `SELECT ... FOR UPDATE`
- `UPDATE ... WHERE version = ?`
- 원자적 `UPDATE value = value + 1`
- 비즈니스 제약 + 재시도

정답은 하나가 아니라, 충돌 빈도와 비용에 따라 달라진다.

### 4. 감지와 재시도의 조합

낙관적 락은 감지 후 재시도를 전제로 한다.  
하지만 재시도하려면 작업이 멱등해야 하고, 외부 side effect를 분리해야 한다.

## 실전 시나리오

### 시나리오 1: 프로필 닉네임이 덮여쓴다

두 화면이 같은 사용자 정보를 읽고 서로 다른 변경을 저장하면, 마지막 저장만 남는다.  
이건 에러가 아니라 정합성 누락이다.

### 시나리오 2: 재고 차감이 사라진다

주문이 늘어나면서 재고를 읽고 저장하는 코드가 동시 실행되면 lost update가 흔하다.

### 시나리오 3: 설정 저장이 간헐적으로 원복된다

관리 화면에서 설정을 바꿨는데, 다른 배치가 오래된 값을 다시 저장하면 사용자에게는 “원래대로 돌아감”처럼 보인다.

## 코드로 보기

```sql
-- 버전 기반 낙관적 락
UPDATE inventory
SET stock = stock - 1,
    version = version + 1
WHERE sku = 'SKU-1'
  AND version = 7
  AND stock > 0;
```

```java
int updated = jdbcTemplate.update(
    "UPDATE profile SET nickname = ?, version = version + 1 WHERE id = ? AND version = ?",
    nickname, userId, version
);
if (updated == 0) {
    throw new ConcurrentModificationException();
}
```

lost update는 읽기 단계가 아니라, **저장 시점에 충돌을 확인하는 구조**가 있어야 잡을 수 있다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 비관적 락 | 단순하고 안전하다 | 경합이 크다 | 충돌이 잦을 때 |
| 버전 체크 | 확장성이 좋다 | 재시도 로직이 필요하다 | 읽기 비중이 높을 때 |
| 원자적 update | 가장 짧다 | 로직을 SQL로 옮겨야 한다 | 카운터/재고 |
| 충돌 후 merge | 유연하다 | 도메인 규칙이 복잡하다 | 협업 편집류 데이터 |

## 꼬리질문

> Q: lost update와 dirty read는 같은 문제인가요?
> 의도: 동시성 이상 현상을 구분하는지 확인
> 핵심: dirty read는 커밋 전 데이터를 보는 것이고, lost update는 저장이 덮이는 것이다

> Q: 버전 컬럼이 왜 도움이 되나요?
> 의도: 충돌 감지 원리를 아는지 확인
> 핵심: 내가 읽은 상태와 저장 시점의 상태가 같은지 확인할 수 있다

> Q: 원자적 update가 왜 강한가요?
> 의도: 읽고 쓰는 사이의 경쟁을 줄이는 방식을 아는지 확인
> 핵심: 읽기-수정-쓰기를 한 문장으로 묶기 때문이다

## 한 줄 정리

Lost update는 조용히 덮어쓰는 동시성 버그이고, 버전 검증이나 원자적 update로 저장 시점에 충돌을 잡아야 한다.
