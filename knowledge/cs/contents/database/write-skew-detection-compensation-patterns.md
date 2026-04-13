# Write Skew Detection과 Compensation Patterns

> 한 줄 요약: write skew는 “충돌이 없어서” 더 위험하고, 막는 것만큼 나중에 감지해서 보상하는 설계가 중요하다.

관련 문서: [Write Skew and Phantom Read Case Studies](./write-skew-phantom-read-case-studies.md), [트랜잭션 격리수준과 락](./transaction-isolation-locking.md), [Outbox, Saga, Eventual Consistency](./outbox-saga-eventual-consistency.md)
Retrieval anchors: `write skew`, `invariant check`, `compensation`, `post-commit validation`, `saga repair`

## 핵심 개념

Write skew는 서로 다른 row를 읽고 각각 다른 row를 수정했지만, 전체 불변식이 깨지는 현상이다.  
문제는 row-level 충돌이 아니라 **집합 수준의 규칙**이 깨진다는 점이다.

왜 중요한가:

- 당직 스케줄, 좌석 수 제한, 재고 배분처럼 “전체 합”이 중요한 규칙에서 자주 생긴다
- 비관적 락만으로도 막기 어렵고, 제약조건 없이 방치하면 조용히 망가진다
- 사전 방지와 사후 보상 둘 다 필요할 수 있다

write skew는 “실패가 안 났다”는 점 때문에 더 위험하다.  
응답은 성공인데, 비즈니스 규칙은 이미 깨졌을 수 있다.

## 깊이 들어가기

### 1. write skew를 감지하는 방법

가장 좋은 방법은 애초에 불변식을 코드가 아닌 **제약조건이나 원자적 구조**로 옮기는 것이다.

그래도 애플리케이션 레벨 감지가 필요하면 다음을 쓴다.

- 커밋 전 재검증
- 커밋 후 검증 job
- 상태 전이 이벤트를 받은 뒤 invariants scan
- version token 기반 대조

즉 감지는 “잘못된 write를 완전히 막지 못해도, 빨리 알아채는 것”이다.

### 2. 왜 사후 보상이 필요한가

분산 워크플로우에서는 모든 불변식을 사전 차단으로 해결할 수 없다.

- 외부 시스템이 끼어 있다
- 여러 서비스가 상태를 나눠 가진다
- 한 번의 커밋으로 전체 규칙을 표현하기 어렵다

이때는 감지 후 보상으로 되돌리는 전략이 필요하다.

### 3. 보상 설계의 핵심

보상은 “원상복구”가 아니라 “규칙을 다시 만족시키는 조정”이다.

- 초과 예약을 취소
- 초과 배정을 회수
- 과잉 상태를 수동 정리 큐에 넣음

보상은 늦어질 수 있고 실패할 수도 있으므로, 반드시 idempotent해야 한다.

### 4. 어디에 검증을 넣을까

대개 다음 지점이 현실적이다.

- 저장 전: 로컬 invariant 확인
- 저장 직후: 커밋 결과 재검증
- 배포 후: 배치 기반 reconciliation

감지와 보상을 둘 다 넣으면 write skew를 다층적으로 다룰 수 있다.

## 실전 시나리오

### 시나리오 1: 당직자 수가 0명이 됨

각자 다른 row만 수정했지만, 전체 당직 수가 최소 1명이어야 한다는 규칙은 깨졌다.  
이 경우 사후 검증 job이 감지하고 보상 변경을 걸어야 한다.

### 시나리오 2: 재고 분산 배분 후 합계가 초과됨

서비스별로 재고를 나눠 들고 있다가, 합산 기준을 넘겨버릴 수 있다.  
감지 후 초과분 회수 또는 추가 주문 취소가 필요하다.

### 시나리오 3: 예약 제한을 넘겼는데 모든 요청이 성공

각 요청은 독립적으로 성공했지만, 전체 제한은 깨졌다.  
이때는 사전 제약과 사후 보상이 같이 필요하다.

## 코드로 보기

```sql
-- 사후 검증용 스캔
SELECT COUNT(*)
FROM doctors
WHERE on_call = true;
```

```java
if (activeCount < 1) {
    compensationService.restoreOneDoctor();
}
```

```text
pattern:
  detect invariant violation -> emit repair task -> apply idempotent compensation
```

write skew는 막는 것도 중요하지만, **감지 후 어디까지 되돌릴지**가 더 어려운 경우가 많다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 사전 제약조건 | 가장 강하다 | 모델링이 필요하다 | 불변식이 명확할 때 |
| 비관적 락 | 즉시 차단 가능 | 경합이 커진다 | 충돌이 잦을 때 |
| 사후 감지 + 보상 | 현실적이다 | 늦게 발견할 수 있다 | 분산 워크플로우 |
| reconciliation batch | 전체를 볼 수 있다 | 지연이 있다 | 운영 정리 |

## 꼬리질문

> Q: write skew는 왜 row lock만으로 안 막히나요?
> 의도: row-level 충돌과 집합 불변식의 차이를 아는지 확인
> 핵심: 서로 다른 row를 수정하면 락이 겹치지 않아도 규칙이 깨질 수 있다

> Q: 감지와 보상 중 무엇이 더 중요하나요?
> 의도: 둘 중 하나만으로는 부족하다는 걸 아는지 확인
> 핵심: 사전 차단이 최선이지만, 사후 감지와 보상이 운영에서는 필요하다

> Q: 보상 작업이 실패하면 어떻게 하나요?
> 의도: 운영 복구까지 생각하는지 확인
> 핵심: 재시도, 수동 정리, reconciliation 큐가 필요할 수 있다

## 한 줄 정리

Write skew는 집합 불변식이 깨지는 문제라서, 사전 제약으로 막고 사후 감지와 idempotent compensation으로 회복해야 한다.
