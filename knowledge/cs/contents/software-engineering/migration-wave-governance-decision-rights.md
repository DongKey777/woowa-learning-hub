# Migration Wave Governance and Decision Rights

> 한 줄 요약: migration은 기술 작업의 묶음이 아니라, wave별 목표와 중단 기준과 decision right를 분명히 둬야 하는 프로그램이며, 누가 다음 wave로 넘어가고 누가 멈출 수 있는지 명확해야 오래 가도 무너지지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Migration Wave Governance and Decision Rights](./README.md#migration-wave-governance-and-decision-rights)
> - [Migration Scorecards](./migration-scorecards.md)
> - [Migration Funding Model](./migration-funding-model.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Data Migration Rehearsal, Reconciliation, Cutover](./data-migration-rehearsal-reconciliation-cutover.md)
> - [Strangler Fig Migration, Contract, Cutover](./strangler-fig-migration-contract-cutover.md)
> - [Migration Carrying Cost and Cost of Delay](./migration-carrying-cost-cost-of-delay.md)
> - [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md)

> retrieval-anchor-keywords:
> - migration wave governance
> - migration program governance
> - wave planning
> - cutover board
> - decision rights
> - pause authority
> - adoption wave
> - migration steering
> - carrying cost

## 핵심 개념

큰 migration은 한 번의 cutover가 아니라 여러 wave를 거친다.
문제는 기술 경로보다 governance가 먼저 무너지는 경우가 많다는 점이다.

흔한 실패:

- wave 목표가 모호함
- lagging consumer를 누가 설득할지 불명확함
- pause 권한이 없어 위험한 rollout이 계속됨
- funding과 staffing이 wave마다 흔들림

그래서 migration governance는 보통 다음을 명시해야 한다.

- wave의 범위
- entry / exit criteria
- exception 처리 방식
- pause / resume 권한
- 최종 cutover 판단 주체

즉 migration은 프로젝트가 아니라 **decision right가 있는 장기 프로그램**으로 운영해야 한다.

---

## 깊이 들어가기

### 1. wave는 일정 단위가 아니라 위험 단위다

좋은 wave는 "이번 분기 할 일"보다 더 명확해야 한다.

예:

- wave 1: read-only shadow verification
- wave 2: low-risk consumer adoption
- wave 3: write authority transition
- wave 4: legacy dependency retirement

이렇게 나누면 각 wave마다 다른 성공 기준과 위험 기준을 둘 수 있다.

### 2. migration에서 가장 중요한 governance 질문은 "누가 멈출 수 있는가"다

진행 책임만 있고 중단 권한이 없으면 governance가 작동하지 않는다.

보통 필요한 역할:

- migration sponsor: 우선순위와 자원 보장
- producer owner: 변경 실행
- consumer owner: adoption 책임
- operational owner / on-call: runtime risk 판단
- contract/data steward: compatibility와 정합성 판단

특히 pause 권한은 producer owner 혼자 가지면 안 되는 경우가 많다.

### 3. entry / exit criteria는 측정 가능해야 한다

wave가 오래 끌리는 이유는 "거의 다 됐다" 상태가 계속되기 때문이다.

좋은 exit criteria 예:

- adoption coverage >= 90%
- reconciliation diff rate < 0.05%
- rollback or fallback path validated
- support readiness confirmed
- unregistered consumer 탐지 결과 없음

즉 wave 종료는 분위기가 아니라 **계측 가능한 기준**으로 판단해야 한다.

### 4. 예외는 migration debt로 계산해야 한다

항상 몇몇 팀은 따라오지 못한다.
문제는 예외를 그냥 허용하면 wave가 닫히지 않는다는 점이다.

그래서 예외에는 보통 다음을 붙인다.

- owner
- expiry date
- compensating control
- next review
- 영향 범위

예외가 쌓이면 migration은 진행 중처럼 보이지만 실제로는 legacy를 계속 들고 간다.

### 5. governance는 scorecard, funding, deprecation과 묶여야 한다

migration steering이 문서 회의로 끝나면 효과가 없다.
다음과 연결돼야 한다.

- scorecard: 상태 측정
- funding model: 병행 운영 비용 보장
- rollout workflow: wave별 승인
- deprecation plan: legacy 종료 일정

즉 migration governance는 status meeting이 아니라 **진행과 중단과 종료를 묶는 운영 회로**다.

---

## 실전 시나리오

### 시나리오 1: API v1에서 v2로 소비자를 옮긴다

모든 consumer를 한 번에 밀지 말고, low-risk consumer부터 wave를 나눈다.
각 wave마다 adoption coverage와 runtime error를 보고 다음 wave 진입을 결정한다.

### 시나리오 2: 데이터 저장소 전환이 길어진다

backfill은 끝났지만 일부 정산 배치가 아직 legacy를 읽고 있다면, write authority cutover wave를 닫으면 안 된다.
hidden dependency를 제거할 때까지 governance가 계속 살아 있어야 한다.

### 시나리오 3: 한 팀이 계속 migration을 미룬다

이 경우 문제는 기술만이 아니라 decision right와 funding이다.
sponsor가 우선순위를 조정하고, exception을 time-boxed로 관리해야 한다.

---

## 코드로 보기

```yaml
migration_wave:
  id: wave-3-write-cutover
  owner: order-platform
  entry_criteria:
    - adoption_coverage >= 85%
    - reconciliation_diff_rate < 0.05%
  exit_criteria:
    - write_authority_switched
    - rollback_path_validated
    - lagging_consumers_exception_approved
  decision_rights:
    pause: [service_owner, oncall, data_steward]
    advance: [migration_sponsor, service_owner]
```

좋은 governance는 회의 안건보다 누가 어떤 조건에서 결정하는지가 먼저 보인다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ad-hoc migration | 빠르게 시작한다 | 길어질수록 무너진다 | 아주 작은 전환 |
| wave governance | 진행 상태가 분명하다 | 관리가 필요하다 | 중대형 migration |
| steering + explicit decision rights | pause와 priority가 명확하다 | 조직 합의가 필요하다 | 여러 팀이 얽힌 migration |

migration wave governance의 핵심은 더 많은 회의가 아니라, **누가 어떤 근거로 다음 단계로 가고 멈추는지 분명하게 만드는 것**이다.

---

## 꼬리질문

- 다음 wave로 넘어가는 기준은 숫자로 정의되어 있는가?
- lagging consumer 예외는 누가 승인하고 언제 닫는가?
- pause 권한은 실제 운영 리스크를 보는 사람에게도 있는가?
- migration governance가 funding과 deprecation 일정과 연결되어 있는가?

## 한 줄 정리

Migration wave governance and decision rights는 전환을 기술 일정이 아니라 wave별 기준과 권한이 있는 장기 프로그램으로 운영해, 멈출 때 멈추고 끝낼 때 끝낼 수 있게 만드는 방식이다.
