# Migration Scorecards

> 한 줄 요약: migration scorecard는 전환이 잘 되고 있는지 감이 아니라 지표로 보여 주기 위해, 준비도와 위험도를 함께 점수화하는 운영 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Strangler Verification, Shadow Traffic Metrics](./strangler-verification-shadow-traffic-metrics.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Brownfield Strangler Org Model](./brownfield-strangler-org-model.md)
> - [Backwards Compatibility Test Gates](./backward-compatibility-test-gates.md)
> - [Data Migration Rehearsal, Reconciliation, Cutover](./data-migration-rehearsal-reconciliation-cutover.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)

> retrieval-anchor-keywords:
> - migration scorecard
> - migration readiness
> - cutover score
> - consumer readiness
> - shadow diff
> - rollback readiness
> - adoption progress
> - migration risk
> - migration wave
> - wave exit criteria

## 핵심 개념

전환 작업은 길고 복잡해서 "느낌상 괜찮다"로 판단하면 위험하다.
scorecard는 전환의 상태를 몇 개의 축으로 나눠, 준비도와 위험을 동시에 보여준다.

예:

- consumer adoption
- shadow diff rate
- contract test coverage
- rollback readiness
- observability readiness
- deprecated path usage
- reconciliation diff rate

즉 scorecard는 migration의 **건강검진표**다.

---

## 깊이 들어가기

### 1. scorecard는 전환의 진행과 안전을 동시에 본다

진행도만 보면 너무 낙관적일 수 있다.
안전만 보면 전환이 안 끝난다.

둘 다 봐야 한다.

### 2. 항목은 행동으로 연결돼야 한다

점수만 있고 다음 행동이 없으면 의미가 없다.

예:

- shadow diff 높음 -> fix and recompare
- consumer adoption 낮음 -> communication 강화
- rollback readiness 낮음 -> runbook 보강
- rehearsal 시간 초과 -> cutover plan 재설계

### 3. scorecard는 팀 간 공용 언어가 된다

전환은 여러 팀이 함께 움직인다.

scorecard가 있으면:

- 제품 팀은 채택률을 본다
- 플랫폼 팀은 안정성을 본다
- 운영 팀은 rollback과 observability를 본다

### 4. scorecard는 정적이어선 안 된다

초기와 후반 전환에서 보는 축이 다를 수 있다.

초기:

- readiness
- ownership
- shadow compare

후반:

- adoption
- deprecation progress
- retirement readiness

### 5. scorecard는 registry와 연동해야 한다

소비자, 계약, 서비스 소유권과 연결되지 않으면 scorecard는 숫자만 남는다.

---

## 실전 시나리오

### 시나리오 1: API를 새 버전으로 옮긴다

scorecard로 채택률과 실패율을 같이 본다.

### 시나리오 2: 레거시를 strangler로 잘라낸다

deprecation path 사용량과 shadow diff를 같이 본다.

### 시나리오 3: 전환이 오래 걸린다

scorecard가 없으면 어디가 막혔는지 모른다.

---

## 코드로 보기

```yaml
migration_scorecard:
  consumer_adoption: 72
  shadow_diff_rate: 0.4
  rollback_ready: true
  deprecation_usage: 18
```

scorecard는 현황판이 아니라 **의사결정 도구**여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 감 기반 판단 | 빠르다 | 오판하기 쉽다 | 매우 작은 전환 |
| scorecard | 상태가 보인다 | 설계가 필요하다 | 큰 전환 |
| scorecard + gates | 실행까지 연결된다 | 운영이 복잡하다 | 고위험 migration |

migration scorecard는 전환의 진척과 위험을 함께 보는 **정량화된 운영 표**다.

---

## 꼬리질문

- 어떤 지표가 전환 성공을 말하는가?
- 어떤 점수면 rollout을 멈춰야 하는가?
- scorecard는 누가 업데이트하는가?
- 후반 전환에 맞춰 항목을 바꿀 것인가?

## 한 줄 정리

Migration scorecards는 전환의 진행도와 안전성을 정량화해, cutover와 deprecation의 판단을 돕는 운영 도구다.
