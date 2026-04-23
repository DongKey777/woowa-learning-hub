# Advisory Locks와 Row Locks

> 한 줄 요약: row lock은 데이터 자체를 보호하고, advisory lock은 데이터 밖의 “작업 순서”를 보호한다.

**난이도: 🔴 Advanced**

관련 문서: [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Gap Lock과 Next-Key Lock](./gap-lock-next-key-lock.md), [Deadlock Case Study](./deadlock-case-study.md)
retrieval-anchor-keywords: advisory lock, row lock, coarse-grained lock, job serialization, metadata lock

## 핵심 개념

Row lock은 특정 row의 읽기/쓰기를 보호한다.  
Advisory lock은 DB가 직접 관리하는 “협의된 잠금”으로, 같은 키를 쓰는 작업끼리만 서로를 막는다.

왜 중요한가:

- 데이터 row가 아니라 배치 job, 리더 선출, 멀티스텝 워크플로우를 직렬화하고 싶을 때가 있다
- row lock만으로는 “같은 작업”을 표현하기 어려울 수 있다
- 반대로 advisory lock을 남용하면 데이터 정합성을 못 지킨다

이 둘은 대체재가 아니라, **보호 대상이 다르다**.

## 깊이 들어가기

### 1. row lock이 적합한 경우

row lock은 실제 데이터 충돌을 막는 데 강하다.

- 계좌 잔액 차감
- 재고 차감
- 상태 전이

예를 들어 같은 주문 row를 동시에 갱신하는 상황이라면 row lock이 맞다.

### 2. advisory lock이 적합한 경우

advisory lock은 데이터가 아니라 작업 단위를 직렬화하고 싶을 때 유용하다.

- 같은 `report-2026-04-09` 작업은 한 번만 실행
- 같은 테넌트의 마이그레이션은 동시에 돌지 않게 제어
- 외부 API 호출을 포함한 긴 워크플로우의 진입점을 하나로 제한

즉 advisory lock은 “이 작업 이름으로만 경쟁하자”는 장치다.

### 3. 왜 advisory lock이 위험할 수 있는가

- 키 설계가 나쁘면 서로 다른 작업이 같은 락을 공유한다
- 락을 오래 잡으면 장애 감지가 늦어진다
- DB 세션이 끊기면 락이 사라져 재진입이 필요하다
- row lock처럼 데이터 변경을 보장하지는 않는다

그래서 advisory lock은 단독 정합성 수단이 아니라, **중복 실행 방지용 게이트**에 가깝다.

### 4. metadata lock과의 혼동을 피해야 한다

metadata lock은 테이블 구조나 DDL과 연관된다.  
advisory lock은 애플리케이션이 정한 키를 기반으로 한다.

둘은 모두 “잠긴다”는 점은 같지만, 목적과 실패 양상이 다르다.

## 실전 시나리오

### 시나리오 1: 야간 배치가 두 인스턴스에서 동시에 시작

row가 없거나, 여러 테이블을 건드리는 배치라면 row lock만으로 막기 어렵다.  
이때 advisory lock으로 job entry를 한 곳에서만 통과시킨다.

### 시나리오 2: 테넌트별 리포트 생성이 겹침

같은 테넌트의 리포트가 두 번 도는 것을 막고 싶다.  
이런 작업은 row lock보다 advisory lock이 더 자연스럽다.

### 시나리오 3: 주문 row를 잠그지 않고 외부 결제 API를 기다림

이 경우 row lock을 오래 잡는 것보다, 짧은 row lock + 작업 수준 advisory lock 조합이 더 낫다.  
다만 외부 호출을 락 안에 넣으면 대기 시간이 길어질 수 있다.

## 코드로 보기

```sql
-- PostgreSQL 스타일의 advisory lock 예시
SELECT pg_try_advisory_lock(hashtext('tenant-42-report'));

-- 작업 종료 후 해제
SELECT pg_advisory_unlock(hashtext('tenant-42-report'));
```

```sql
-- row lock 예시
START TRANSACTION;
SELECT *
FROM orders
WHERE id = 9001
FOR UPDATE;
UPDATE orders
SET status = 'PAID'
WHERE id = 9001;
COMMIT;
```

advisory lock은 “누가 이 작업을 해도 되는가”를 정하고, row lock은 “어떤 데이터를 바꿀 수 있는가”를 지킨다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| row lock | 정합성이 직접적이다 | 경합이 크고 데드락 위험이 있다 | 실제 row 충돌이 있을 때 |
| advisory lock | 작업 단위를 표현하기 쉽다 | 데이터 자체를 보호하지 못한다 | 배치/워크플로우 직렬화 |
| unique constraint | 강하고 단순하다 | 모델링이 필요하다 | 중복이 명확히 금지될 때 |
| application lock | 유연하다 | 분산 인스턴스에서 취약하다 | 단일 프로세스 환경 |

## 꼬리질문

> Q: advisory lock으로 재고 차감을 대신할 수 있나요?
> 의도: 작업 직렬화와 데이터 정합성을 구분하는지 확인
> 핵심: 작업은 막을 수 있어도 row 정합성을 직접 보장하진 못한다

> Q: row lock보다 advisory lock이 나은 경우는 언제인가요?
> 의도: 작업 단위 잠금의 사용처를 아는지 확인
> 핵심: 배치, 리포트, 리더 역할처럼 데이터 row가 아닌 단위를 제어할 때다

> Q: advisory lock을 오래 잡으면 어떤 문제가 생기나요?
> 의도: 운영상 실패 모드를 이해하는지 확인
> 핵심: 장애 감지 지연, 대기 증가, 재시도 폭증이 생긴다

## 한 줄 정리

Row lock은 데이터 충돌을 막고, advisory lock은 작업 중복을 막는다. 둘은 비슷해 보이지만 보호하는 대상이 다르다.
