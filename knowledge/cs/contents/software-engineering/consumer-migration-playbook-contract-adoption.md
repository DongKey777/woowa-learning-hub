# Consumer Migration Playbook and Contract Adoption

> 한 줄 요약: consumer migration은 새 API를 만드는 일이 아니라, 소비자별 전환 순서와 실패 복구를 설계해 계약 adoption을 안전하게 끝내는 일이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Versioning, Contract Testing, Anti-Corruption Layer](./api-versioning-contract-testing-anti-corruption-layer.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)

> retrieval-anchor-keywords:
> - consumer migration
> - contract adoption
> - migration playbook
> - consumer registry
> - rollout order
> - deprecation notice
> - dual run
> - migration verification

## 핵심 개념

API나 이벤트 계약을 바꿔도, 소비자가 바로 따라오지 않는 경우가 많다.
그래서 중요한 것은 새로운 계약을 만드는 것보다 **소비자들을 순서대로 옮기는 운영 계획**이다.

consumer migration playbook은 다음을 정의한다.

- 누가 먼저 바꾸는가
- 어떤 소비자는 뒤로 미루는가
- 어떤 검증을 통과해야 하는가
- 실패하면 무엇을 되돌리는가

즉 계약 채택은 기술 배포가 아니라 **조정된 이전 작업**이다.

---

## 깊이 들어가기

### 1. 소비자마다 migration 난이도가 다르다

모든 소비자를 같은 순서로 옮기면 안 된다.

낮은 난이도 소비자:

- 내부 서비스
- 짧은 릴리스 주기
- 테스트 자동화가 있는 팀

높은 난이도 소비자:

- 외부 파트너
- 배포 주기가 긴 앱
- 계약 검증이 약한 시스템

그래서 consumer registry와 우선순위가 필요하다.

### 2. dual run은 migration 검증의 핵심이다

이전 계약과 새 계약을 한동안 같이 돌려 보면 채택 리스크를 줄일 수 있다.

예:

- 구 API와 신 API를 동시에 유지
- 이벤트의 old/new consumer를 병행
- response diff와 contract test를 같이 사용

dual run은 중복 비용이 들지만, 대규모 전환에서는 안전장치가 된다.

### 3. migration playbook은 소통 계획도 포함해야 한다

소비자 이전은 코드가 아니라 협업의 문제이기도 하다.

필요한 것:

- 공지 시점
- 마감일
- 문의 채널
- 회귀 테스트 가이드
- fallback 조건

즉 migration은 릴리스 노트보다 더 구체적인 운영 약속이 필요하다.

### 4. adoption gate를 정의해야 한다

새 계약으로 옮겼다고 해서 곧바로 old contract를 끊으면 안 된다.

보통 확인해야 할 것:

- 소비자 전환률
- 에러율
- 누락/형식 오류
- 재시도 증가
- business KPI 영향

이 gate가 있어야 무리한 강제 전환을 막을 수 있다.

### 5. migration 실패는 되돌림과 재시도를 분리해야 한다

소비자 migration이 실패했다고 해서 항상 계약 자체를 되돌려야 하는 것은 아니다.

경우에 따라:

- 소비자만 다시 old contract 사용
- 특정 소비자만 rollout pause
- 계약은 유지하되 사용량만 줄임

즉 실패 대응은 계약과 소비자 흐름을 분리해서 봐야 한다.

---

## 실전 시나리오

### 시나리오 1: 내부 앱부터 새 API로 옮긴다

내부 소비자는 릴리스가 빠르므로 먼저 옮기고, 파트너 API는 뒤로 미룬다.

### 시나리오 2: 이벤트 consumer를 새 schema로 바꾼다

새 consumer를 병행 실행하고, replay와 shadow compare로 결과를 확인한 뒤 old consumer를 줄인다.

### 시나리오 3: 외부 파트너가 늦게 반응한다

이 경우 deprecation timeline을 연장하거나, old contract를 장기 유지하는 정책 판단이 필요하다.

---

## 코드로 보기

```yaml
migration_plan:
  phase_1:
    consumers: [internal-web, internal-admin]
    mode: dual_run
  phase_2:
    consumers: [mobile]
    mode: canary
  phase_3:
    consumers: [partner-a]
    mode: negotiated
```

소비자 migration은 기술 상태가 아니라 운영 단계로 관리해야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 일괄 전환 | 빠르다 | 실패 반경이 크다 | 소비자 수가 적을 때 |
| 순차 migration | 안전하다 | 오래 걸린다 | 소비자가 많을 때 |
| dual run | 검증이 강하다 | 비용이 든다 | 계약 리스크가 클 때 |

consumer migration의 핵심은 "새 계약을 공개했다"가 아니라 **소비자가 안전하게 채택했는가**다.

---

## 꼬리질문

- 어떤 소비자를 먼저 옮길 것인가?
- migration success를 어떤 지표로 판단할 것인가?
- 실패 시 계약을 되돌릴지 소비자를 되돌릴지?
- deprecation schedule과 consumer readiness를 어떻게 맞출 것인가?

## 한 줄 정리

Consumer migration playbook은 계약 adoption의 순서, 검증, 복구를 정해 소비자 전환을 안전하게 끝내는 운영 설계다.
