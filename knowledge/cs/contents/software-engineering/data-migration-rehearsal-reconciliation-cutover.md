# Data Migration Rehearsal, Reconciliation, Cutover

> 한 줄 요약: 데이터 마이그레이션은 트래픽 전환보다 어렵기 때문에, rehearsal로 시간과 실패 모드를 확인하고 reconciliation으로 두 시스템의 차이를 설명한 뒤 cutover를 해야 실제 전환이 안전해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Data Migration Rehearsal, Reconciliation, Cutover](./README.md#data-migration-rehearsal-reconciliation-cutover)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Migration Scorecards](./migration-scorecards.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)

> retrieval-anchor-keywords:
> - data migration rehearsal
> - reconciliation
> - cutover
> - backfill
> - dual write
> - migration validation
> - data correctness
> - cutover readiness

## 핵심 개념

서비스 전환은 라우팅만 바꾸면 끝나는 경우가 있지만, 데이터 전환은 그렇지 않다.
이미 저장된 데이터와 앞으로 쌓일 데이터를 어떻게 옮기고 검증할지까지 봐야 한다.

핵심 단계는 보통 다음과 같다.

- rehearsal: 실제와 비슷한 조건에서 리허설
- reconciliation: source와 target의 차이를 설명
- cutover: 권한과 트래픽, 쓰기 기준 전환

즉 데이터 마이그레이션은 배포 이벤트가 아니라 **정합성 중심의 운영 프로그램**이다.

---

## 깊이 들어가기

### 1. rehearsal은 성능보다 실패 모드를 먼저 찾는다

리허설은 단순히 "몇 시간 걸리는가"를 재는 작업이 아니다.

확인해야 하는 것:

- 누락 데이터 유형
- 변환 예외
- 재실행 가능성
- 중간 실패 후 resume 방법
- 다운스트림 영향

실전에서 처음 겪는 예외를 줄이려면 rehearsal이 꼭 필요하다.

### 2. reconciliation은 같음/다름을 설명하는 계약이다

source와 target이 완전히 똑같지 않을 수 있다.
중요한 건 어떤 차이가 허용되고 어떤 차이는 장애인지 정의하는 것이다.

예:

- 정렬 순서는 달라도 됨
- timestamp precision 차이는 허용
- 금액 합계 차이는 허용 안 됨
- 상태 전이 누락은 허용 안 됨

즉 reconciliation은 숫자 맞추기가 아니라 **정합성 기준 정의**다.

### 3. cutover 기준은 트래픽보다 쓰기 권한이 더 중요할 수 있다

많은 팀이 read path만 보고 전환 시점을 잡는다.
하지만 실제 위험은 write authority에 있다.

질문 예:

- 최종 source of truth는 언제 바꾸는가
- dual write를 언제 끊는가
- rollback 시 어떤 데이터가 유실되는가
- cutover window 동안 freeze가 필요한가

이 답이 없으면 cutover는 배포보다 더 위험해진다.

### 4. rollback은 항상 가능하지 않다

데이터 마이그레이션은 어떤 지점 이후 rollback이 비현실적일 수 있다.
그래서 cutover 전에 다음을 알아야 한다.

- reversible window가 얼마나 되는가
- fallback read가 가능한가
- 보정 배치가 필요한가
- manual reconciliation이 필요한가

즉 "문제 생기면 롤백"은 데이터 전환에서 종종 성립하지 않는다.

### 5. cutover 이후 cleanup까지 포함해야 진짜 종료다

전환이 끝나도 다음을 남겨두면 부채가 된다.

- dual write 코드
- 임시 매핑 테이블
- compare job
- 오래된 backfill 스크립트
- 해석이 끝난 reconciliation 예외 목록

마이그레이션은 cutover 순간이 아니라, **옛 진실을 완전히 내려놓을 때** 끝난다.

---

## 실전 시나리오

### 시나리오 1: 주문 이력을 새 스토리지로 옮긴다

읽기 성능만 보면 전환할 수 있어 보여도, 주문 상태 전이와 정산 합계가 어긋나면 cutover하면 안 된다.

### 시나리오 2: 모놀리스 테이블을 도메인별로 분리한다

백필만 끝내고 dual write를 오래 끌면 drift가 쌓인다.
reconciliation 기준과 종료 조건이 필요하다.

### 시나리오 3: 검색 인덱스를 새 구조로 바꾼다

샘플 검증만으로는 부족하고, 대량 backfill 속도와 reindex 실패 시 복구 시나리오를 rehearsal해야 한다.

---

## 코드로 보기

```yaml
data_migration:
  source: legacy_order_db
  target: order_event_store
  rehearsal:
    sample_window: 14d
    restartable: true
  reconciliation:
    strict_fields: [order_status, total_amount]
    tolerated_fields: [updated_at_precision]
  cutover:
    write_authority: target
    rollback_window_minutes: 30
```

좋은 계획은 데이터 이동과 검증과 권한 전환을 한 흐름으로 묶는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 빠른 일괄 전환 | 일정이 짧다 | 실패 비용이 크다 | 데이터가 작고 영향이 작을 때 |
| rehearsal + reconciliation | 안전하다 | 준비 시간이 든다 | 대부분의 중요 전환 |
| 장기 dual write | rollback 여지가 있다 | drift와 복잡도가 쌓인다 | 불가피하게 단계 전환이 길 때 |

data migration의 핵심은 속도가 아니라, **어떤 차이를 허용하고 언제 진실의 기준을 바꿀지 명확히 하는 것**이다.

---

## 꼬리질문

- rehearsal에서 반드시 찾아야 할 실패 모드는 무엇인가?
- reconciliation 기준은 누가 승인하는가?
- cutover 이후 rollback이 정말 가능한가?
- dual write와 compare job을 언제 제거할 것인가?

## 한 줄 정리

Data migration rehearsal, reconciliation, cutover는 데이터 전환을 단순 배포가 아니라 정합성 검증과 권한 전환이 포함된 운영 프로그램으로 다루는 관점이다.

## 다음 읽기

- 다음 한 걸음: [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md) - rehearsal과 reconciliation 결과를 누가 어떤 기준으로 승인할지 이어서 정리할 수 있다.
- README로 돌아가기: [Software Engineering README](./README.md#data-migration-rehearsal-reconciliation-cutover) - migration scorecard, consumer adoption 같은 후속 문서를 다시 고르기 쉽다.
