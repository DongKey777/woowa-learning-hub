---
schema_version: 3
title: Fraud Case Management Workflow 설계
concept_id: system-design/fraud-case-management-workflow-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- fraud case management
- investigation workflow
- review queue
- evidence collection
aliases:
- fraud case management
- investigation workflow
- review queue
- evidence collection
- analyst dashboard
- dispute
- chargeback
- case SLA
- hold
- escalation
- workflow orchestration
- Fraud Case Management Workflow 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/fraud-risk-scoring-pipeline-design.md
- contents/system-design/workflow-orchestration-saga-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/job-queue-design.md
- contents/system-design/metrics-pipeline-tsdb-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Fraud Case Management Workflow 설계 설계 핵심을 설명해줘
- fraud case management가 왜 필요한지 알려줘
- Fraud Case Management Workflow 설계 실무 트레이드오프는 뭐야?
- fraud case management 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Fraud Case Management Workflow 설계를 다루는 deep_dive 문서다. fraud case management workflow는 의심 거래를 케이스로 전환해 조사, 증거 수집, 판정, 보상을 체계화하는 운영 워크플로우다. 검색 질의가 fraud case management, investigation workflow, review queue, evidence collection처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Fraud Case Management Workflow 설계

> 한 줄 요약: fraud case management workflow는 의심 거래를 케이스로 전환해 조사, 증거 수집, 판정, 보상을 체계화하는 운영 워크플로우다.

retrieval-anchor-keywords: fraud case management, investigation workflow, review queue, evidence collection, analyst dashboard, dispute, chargeback, case SLA, hold, escalation, workflow orchestration

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Fraud / Risk Scoring Pipeline 설계](./fraud-risk-scoring-pipeline-design.md)
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Metrics Pipeline / TSDB 설계](./metrics-pipeline-tsdb-design.md)

## 핵심 개념

fraud case management는 자동 차단만으로 끝나지 않는다.  
실전에서는 아래를 함께 다룬다.

- risk pipeline의 고위험 결과를 케이스로 전환
- analyst review queue
- 증거 수집과 타임라인
- case SLA
- hold / release decision
- chargeback / dispute 후속

즉, 케이스 관리 워크플로우는 자동 탐지와 인간 판단을 연결하는 운영 시스템이다.

## 깊이 들어가기

### 1. 왜 케이스가 필요한가

모든 fraud 신호를 자동 차단하면 오탐 비용이 커진다.  
그래서 불확실한 경우는 케이스로 넘긴다.

- block
- allow
- review

### 2. Capacity Estimation

예:

- 하루 100만 거래
- 0.2%가 review 필요
- 하루 2,000 cases

케이스 수는 적어 보여도, 각 케이스에 필요한 증거와 SLA가 중요하다.

봐야 할 숫자:

- case creation rate
- review queue depth
- SLA breach rate
- hold duration
- analyst throughput

### 3. Workflow 상태

```text
NEW -> TRIAGED -> INVESTIGATING -> DECIDED -> RESOLVED
            \-> ESCALATED -> HOLD -> RELEASED
```

각 상태는 누가 책임지는지 명확해야 한다.

### 4. Evidence collection

케이스에는 판단 근거가 필요하다.

- transaction history
- device fingerprint
- IP reputation
- login timeline
- risk score snapshot
- audit log reference

증거가 없으면 reviewer는 같은 질문을 반복한다.

### 5. Human-in-the-loop

자동화가 완벽하지 않기 때문에 운영자가 개입한다.

- analyst queue
- supervisor override
- escalation path
- SLA timer

이 구조는 [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)와 닮아 있다.

### 6. Hold와 release

케이스는 거래나 계정을 잠시 멈출 수 있다.

- payment hold
- account freeze
- limit reduction
- release after review

hold는 최소화해야 하지만, 너무 약하면 손실이 커진다.

### 7. Feedback loop

케이스 결과는 fraud 모델에 다시 들어가야 한다.

- confirmed fraud
- false positive
- uncertain

이 피드백이 없으면 탐지와 운영이 분리된 채로 망가진다.

## 실전 시나리오

### 시나리오 1: 고위험 결제

문제:

- risk score가 높지만 확실하지 않다

해결:

- 케이스 생성
- 거래 hold
- analyst review

### 시나리오 2: 사용자 dispute

문제:

- 사용자가 부정 사용을 신고한다

해결:

- 증거 수집
- chargeback 처리
- 결과를 모델 학습에 반영

### 시나리오 3: SLA breach

문제:

- 케이스가 너무 오래 쌓인다

해결:

- priority queue
- auto-escalation
- analyst workload balancing

## 코드로 보기

```pseudo
function createCase(txn, risk):
  if risk.score < threshold:
    return allow
  caseId = caseStore.create(txn, risk.snapshot)
  queue.publish(caseId)
  return hold(caseId)

function resolveCase(caseId, decision):
  caseStore.update(caseId, decision)
  applyDecision(decision)
```

```java
public CaseDecision review(CaseId caseId, AnalystDecision decision) {
    return caseService.resolve(caseId, decision);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Auto block only | 단순하다 | 오탐 비용 큼 | 매우 확실한 사기 |
| Review queue | 유연하다 | 운영 비용 증가 | 불확실 케이스 |
| Hold then release | 손실을 줄인다 | UX 마찰 | 고가치 거래 |
| Strict SLA workflow | 운영이 명확하다 | 유연성 낮다 | 대규모 팀 |
| Evidence-rich cases | 설명 가능하다 | 저장/수집 비용 | 컴플라이언스 |

핵심은 fraud case management가 단순 큐가 아니라 **자동 탐지 결과를 사람의 판단과 증거로 연결하는 운영 워크플로우**라는 점이다.

## 꼬리질문

> Q: risk scoring과 case management는 어떻게 다른가요?
> 의도: 자동 판단과 운영 판단 구분 확인
> 핵심: scoring은 점수 산출, case management는 조사와 결정을 맡는다.

> Q: hold를 왜 쓰나요?
> 의도: 손실 방어와 UX 균형 이해 확인
> 핵심: 확실하지 않은 경우 임시로 위험을 멈추기 위해서다.

> Q: 케이스에 어떤 증거가 필요하나요?
> 의도: 조사 가능성 이해 확인
> 핵심: 트랜잭션, 디바이스, IP, risk snapshot, audit reference가 필요하다.

> Q: SLA breach는 어떻게 막나요?
> 의도: 운영 scaling 이해 확인
> 핵심: priority queue, auto escalation, workload balancing이 필요하다.

## 한 줄 정리

Fraud case management workflow는 자동 탐지의 불확실성을 케이스와 증거, 인간 검토로 연결해 손실과 오탐을 함께 관리하는 시스템이다.

