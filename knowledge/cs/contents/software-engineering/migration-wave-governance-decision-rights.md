---
schema_version: 3
title: Migration Wave Governance and Decision Rights
concept_id: software-engineering/migration-wave-governance
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- migration
- governance
- decision-rights
- wave-planning
aliases:
- Migration Wave Governance and Decision Rights
- migration wave governance
- migration decision rights
- pause authority migration
- wave planning cutover board
- 다음 wave 승인 권한
symptoms: []
intents:
- comparison
- design
- troubleshooting
prerequisites:
- software-engineering/migration-scorecards
- software-engineering/consumer-migration-playbook
next_docs:
- software-engineering/migration-stop-loss-governance
- software-engineering/migration-funding-model
- software-engineering/data-migration-cutover
linked_paths:
- contents/software-engineering/migration-scorecards.md
- contents/software-engineering/migration-funding-model.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md
- contents/software-engineering/strangler-fig-migration-contract-cutover.md
- contents/software-engineering/migration-carrying-cost-cost-of-delay.md
- contents/software-engineering/migration-stop-loss-scope-reduction-governance.md
confusable_with:
- software-engineering/migration-scorecards
- software-engineering/consumer-migration-playbook
- software-engineering/migration-stop-loss-governance
forbidden_neighbors: []
expected_queries:
- migration에서 누가 다음 wave로 넘어가고 누가 rollout을 멈출 수 있는지 decision rights를 어떻게 정해?
- wave governance와 migration scorecard와 consumer migration playbook과 stop-loss 문서는 각각 어떤 질문에 답해?
- migration wave를 일정 단위가 아니라 위험 단위로 나눠야 하는 이유를 설명해줘
- pause authority를 producer owner 혼자가 아니라 on-call, data steward, consumer owner와 나눠야 하는 경우는 언제야?
- lagging consumer exception에 owner, expiry, compensating control, next review를 붙여야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 migration을 wave별 entry/exit criteria, pause authority, advance decision rights, consumer exception으로 운영하게 돕는 advanced chooser이다.
---
# Migration Wave Governance and Decision Rights

> 한 줄 요약: `누가 다음 wave로 넘어가고, 누가 rollout을 멈출 수 있나요?`처럼 승인 권한과 pause 권한이 섞여 헷갈릴 때 먼저 보는 governance 문서로, migration을 기술 작업 묶음이 아니라 wave별 목표·중단 기준·decision right가 있는 프로그램으로 정리한다.

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

## 먼저 이 문서가 맞는 질문인지

아래처럼 `권한`, `승인`, `pause`, `다음 wave`가 섞여 있으면 이 문서가 맞다.

| 지금 묻는 질문 | 먼저 볼 문서 | 아직 과한 문서 |
|---|---|---|
| `누가 다음 wave로 올려요?`, `누가 멈출 수 있어요?` | 이 문서 | stop-loss, funding deep dive |
| `전환 상태를 어떤 숫자로 보죠?` | [Migration Scorecards](./migration-scorecards.md) | 이 문서를 scorecard 대용으로 읽기 |
| `consumer를 어떤 순서로 옮기죠?` | [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md) | decision-right 문서만 읽고 실행 계획 만들기 |
| `이 migration을 계속할지 줄일지 접을지` | [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md) | wave 승인 문서만으로 stop 판단하기 |

- 짧게 자르면 `누가 결정하나`는 이 문서, `무슨 숫자를 보나`는 scorecard, `누굴 먼저 옮기나`는 consumer playbook, `계속할 가치가 있나`는 stop-loss다.

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

## 다음 읽기

- [Migration Scorecards](./migration-scorecards.md): wave exit를 느낌이 아니라 어떤 수치로 닫을지 바로 이어서 본다.
- [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md): governance table을 실제 consumer rollout 순서로 옮기는 방법을 본다.
- [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md): `다음 wave로 갈지`가 아니라 `계속할지 줄일지`를 묻는 순간 넘어간다.

## 한 줄 정리

Migration wave governance and decision rights는 전환을 기술 일정이 아니라 wave별 기준과 권한이 있는 장기 프로그램으로 운영해, 멈출 때 멈추고 끝낼 때 끝낼 수 있게 만드는 방식이다.
