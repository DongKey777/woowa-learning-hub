# Contract Registry Governance

> 한 줄 요약: contract registry는 계약의 목록이 아니라, 계약의 상태, 소유권, 소비자, 변경 이력을 통제하는 운영 레지스트리다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Data Contract Ownership and Lifecycle](./data-contract-ownership-lifecycle.md)
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)
> - [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)

> retrieval-anchor-keywords:
> - contract registry
> - contract governance
> - consumer registry
> - ownership metadata
> - version policy
> - contract state
> - change history
> - governance workflow

## 핵심 개념

계약이 많아지면 "누가 어떤 계약을 쓰는지"를 사람이 기억할 수 없다.

contract registry는 이 문제를 풀기 위한 단일 기준점이다.

좋은 registry는 단순 목록이 아니라 다음을 포함한다.

- 계약 ID
- stage/status
- owner
- consumers
- supported versions
- last review date
- deprecation/sunset 정보

즉 registry는 **계약의 진실을 추적하는 시스템**이다.

---

## 깊이 들어가기

### 1. registry는 source of truth에 가까워야 한다

계약 정보가 문서, 코드, 메일, 슬랙에 흩어지면 오래 못 간다.

registry가 책임지는 것:

- 어떤 계약이 active인지
- 어떤 소비자가 연결되어 있는지
- 누가 변경 승인자인지
- 언제 폐기 예정인지

### 2. registry는 lifecycle-aware여야 한다

계약 상태는 시간이 지나며 바뀐다.

상태 예:

- draft
- active
- deprecated
- sunset
- retired

이 상태는 [API Lifecycle Stage Model](./api-lifecycle-stage-model.md)과 연결된다.

### 3. governance는 승인 경로를 포함해야 한다

registry는 단순 기록용이 아니다.

계약 변경 때 확인할 것:

- owner 승인
- consumer 영향 확인
- compatibility gate 통과
- communication 준비

### 4. registry는 stale entry를 잡아야 한다

관리되지 않으면 registry도 금방 낡는다.

따라서 다음 검사가 필요하다.

- 실제 존재하는 계약인지
- 소비자 목록이 최신인지
- deprecated 상태가 너무 오래 지속되지 않는지
- retired 계약이 아직 참조되지 않는지

### 5. registry는 review, release, deprecation과 연결돼야 한다

레지스트리가 실효성을 가지려면 다른 시스템과 묶여야 한다.

- release gate
- deprecation notice
- migration checklist
- ownership catalog

---

## 실전 시나리오

### 시나리오 1: consumer가 늘었는데 누가 쓰는지 모른다

registry가 없으면 영향 범위를 추적할 수 없다.

### 시나리오 2: deprecated 계약이 계속 남는다

registry 상태와 실제 사용량을 비교해 stale 계약을 정리해야 한다.

### 시나리오 3: 계약 변경 승인 책임이 불명확하다

owner와 steward를 분리해 승인 경로를 명시한다.

---

## 코드로 보기

```yaml
contract_registry:
  contract_id: payment-event-v3
  stage: active
  owner: payments-platform
  consumers:
    - settlement-service
    - reporting-service
```

registry는 검색용 메모가 아니라 운영 규칙의 기반이어야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 문서 흩어짐 | 빠르다 | 추적이 어렵다 | 아주 작은 팀 |
| registry 중심 | 추적성이 좋다 | 유지비가 든다 | 계약이 많을 때 |
| registry + policy gates | 안전하다 | 체계가 복잡하다 | 여러 팀이 함께 쓸 때 |

contract registry governance는 계약의 존재를 정리하는 것이 아니라 **계약 변경을 통제하는 체계**다.

---

## 꼬리질문

- registry는 누가 업데이트하는가?
- stale entry는 어떻게 찾는가?
- consumer 목록의 진실성은 어떻게 보장하는가?
- deprecated 계약은 언제 자동 경고할 것인가?

## 한 줄 정리

Contract registry governance는 계약의 상태와 소유권, 소비자, 변경 이력을 중앙에서 통제해 계약 운영을 가능하게 하는 체계다.
