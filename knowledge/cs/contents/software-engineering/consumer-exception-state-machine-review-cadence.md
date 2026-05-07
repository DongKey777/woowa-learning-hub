---
schema_version: 3
title: Consumer Exception State Machine and Review Cadence
concept_id: software-engineering/consumer-exception-state-machine
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- consumer-exception
- state-machine
- review-cadence
aliases:
- Consumer Exception State Machine and Review Cadence
- consumer exception state machine
- exception lifecycle
- exception review cadence
- expiring consumer
- blocked exception
- waiver review cadence
symptoms:
- exception registry에 row는 있지만 proposed, approved, active, expiring, blocked, closed 상태 전이와 entry/exit 기준이 없어 예외가 움직이지 않아
- expiring 상태를 별도 queue로 보지 않아 만료 직전에야 연장 요청이 나오고 repeated extension이 active에 묻혀
- closed 조건을 티켓 종료로만 보고 replacement path verified, old path usage 0, allowlist removed, support contract ended 증거 없이 닫아
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- software-engineering/consumer-exception-registry
- software-engineering/compatibility-waiver-governance
next_docs:
- software-engineering/consumer-exception-registry-quality
- software-engineering/migration-wave-governance
- software-engineering/support-sla-escalation-contracts
linked_paths:
- contents/software-engineering/consumer-exception-registry-templates.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
- contents/software-engineering/migration-wave-governance-decision-rights.md
- contents/software-engineering/support-sla-escalation-contracts.md
- contents/software-engineering/consumer-exception-registry-quality-automation.md
- contents/software-engineering/consumer-exception-operating-model.md
confusable_with:
- software-engineering/consumer-exception-registry
- software-engineering/consumer-exception-registry-quality
- software-engineering/consumer-exception-model
forbidden_neighbors: []
expected_queries:
- consumer exception state machine에서 proposed, approved, active, expiring, blocked, closed는 어떤 entry exit 기준을 가져야 해?
- proposed 요청을 바로 active로 열면 왜 승인 없는 exception 더미가 생겨?
- expiring 상태를 weekly escalation review에서 우선 처리해야 하는 이유가 뭐야?
- blocked exception은 단순 지연이 아니라 migration ownership policy problem의 신호라는 말을 설명해줘
- closed state는 old path usage 0, replacement verified, allowlist removed 같은 verified closure로 닫아야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 consumer exception registry를 proposed, approved, active, expiring, blocked, closed 상태와 differentiated review cadence로 움직이게 만드는 advanced playbook이다.
---
# Consumer Exception State Machine and Review Cadence

> 한 줄 요약: consumer exception registry가 살아 있으려면 proposed, active, expiring, blocked, closed 같은 상태 전이와 review cadence가 명확해야 하며, 예외를 기록하는 것보다 상태를 움직이게 만드는 운영 리듬이 더 중요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

> retrieval-anchor-keywords:
> - consumer exception state machine
> - exception lifecycle
> - exception review cadence
> - expiring consumer
> - blocked exception
> - waiver review
> - exception state transition
> - registry cadence

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Consumer Exception State Machine and Review Cadence](./README.md#consumer-exception-state-machine-and-review-cadence)
> - 다음 단계: [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

## 핵심 개념

registry가 있어도 상태 변화가 없으면 예외는 그냥 쌓인다.
그래서 consumer exception은 문서가 아니라 state machine으로 보는 편이 좋다.

예:

- proposed
- approved
- active
- expiring
- blocked
- closed

즉 exception governance의 핵심은 템플릿보다 **상태 전이와 review cadence**다.

---

## 깊이 들어가기

### 1. proposed와 active를 분리해야 한다

예외 요청이 들어왔다고 바로 active가 되면 안 된다.

proposed 단계에서 확인할 것:

- 정당한 이유가 있는가
- owner가 있는가
- support path가 있는가
- exit condition이 있는가

이걸 건너뛰면 registry가 승인 로그 없이 active exception 더미가 된다.

### 2. expiring 상태는 가장 중요한 운영 신호다

만료가 가까워진 exception이 보이지 않으면 항상 마지막 순간에 연장 요청이 나온다.

expiring 조건 예:

- expires_at 14일 이내
- replacement 준비 미완료
- support cut-off 임박

이 상태는 governance forum에서 우선 처리되어야 한다.

### 3. blocked 상태는 예외 자체보다 구조 문제를 말한다

blocked 예:

- consumer가 migration을 못 끝냄
- producer가 fallback path를 제거 못 함
- support owner가 없음

blocked는 그냥 지연이 아니라, migration or ownership or policy problem의 신호다.

### 4. cadence는 stage별로 달라도 된다

예:

- proposed: weekly review
- active: biweekly or monthly
- expiring/blocked: weekly escalation review

모든 상태를 같은 cadence로 보면 중요한 예외가 묻힌다.

### 5. close 조건은 verified closure여야 한다

closed의 기준 예:

- replacement path verified
- old path usage 0
- support contract 종료
- allowlist 제거

ticket 닫힘만으로 close 처리하면 registry가 곧 신뢰를 잃는다.

---

## 실전 시나리오

### 시나리오 1: mobile consumer exception이 세 번 연장된다

이 경우 active 상태로 방치하지 말고 blocked 또는 expiring escalation 상태로 올려야 한다.

### 시나리오 2: deprecation waiver가 만료 직전까지 안 보인다

cadence 문제다.
expiring queue를 별도로 보여 줘야 한다.

### 시나리오 3: closed 처리했는데 old traffic이 남아 있다

close criterion이 너무 약한 상태다.
verified usage check가 필요하다.

---

## 코드로 보기

```yaml
consumer_exception_state:
  id: ex-mobile-v5
  status: expiring
  review_every: weekly
  escalate_if:
    - expires_in < 14d
    - old_path_usage > 0
```

좋은 state machine은 예외가 언제 위험 상태로 바뀌는지 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| registry only | 가시성은 있다 | 움직이지 않는다 | 초기 |
| state machine | 운영이 선명해진다 | 상태 정의가 필요하다 | 예외가 많아질 때 |
| state machine + differentiated cadence | 현실적이다 | 운영 discipline이 필요하다 | 성숙한 consumer governance |

consumer exception state machine의 목적은 예외를 더 많이 관리하는 것이 아니라, **예외가 언제 위험과 지연의 신호가 되는지 더 빨리 드러내는 것**이다.

---

## 꼬리질문

- proposed, active, expiring, blocked, closed가 실제로 구분되는가?
- expiring exception이 governance review에서 우선 보이는가?
- blocked 상태는 누구에게 escalation되는가?
- close 기준이 verified change인가, 단순 티켓 종료인가?

## 한 줄 정리

Consumer exception state machine and review cadence는 예외를 정적인 레코드가 아니라 상태 전이와 우선순위가 있는 backlog로 다뤄, 종료와 escalation을 더 실제적으로 만드는 운영 모델이다.
