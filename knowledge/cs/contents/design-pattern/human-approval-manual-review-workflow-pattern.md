---
schema_version: 3
title: Human Approval and Manual Review Workflow Pattern
concept_id: design-pattern/human-approval-manual-review-workflow-pattern
canonical: true
category: design-pattern
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- human-approval
- manual-review-workflow
- review-queue-audit
aliases:
- manual review workflow
- human approval step
- review queue pattern
- human in the loop workflow
- approval sla
- review override audit
- escalation policy
- reassignment policy
- manual review step
- 수동 검토 workflow
symptoms:
- manual review를 관리자 화면 예외 처리로만 붙이고 workflow status, SLA, timeout, audit를 모델링하지 않는다
- queue assignment와 business decision semantics를 한 필드로 섞어 누가 보고 어떤 결정을 했는지 추적하기 어렵다
- 사람이 검토 중인 상태에서 자동 취소나 자동 환불이 동시에 진행되어 semantic lock이 깨진다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- design-pattern/workflow-owner-vs-participant-context
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/semantic-lock-pending-state-pattern
next_docs:
- design-pattern/escalation-reassignment-queue-ownership-pattern
- design-pattern/process-manager-state-store-recovery
- design-pattern/compensation-vs-reconciliation-pattern
linked_paths:
- contents/design-pattern/workflow-owner-vs-participant-context.md
- contents/design-pattern/process-manager-deadlines-timeouts.md
- contents/design-pattern/process-manager-state-store-recovery.md
- contents/design-pattern/escalation-reassignment-queue-ownership-pattern.md
- contents/design-pattern/semantic-lock-pending-state-pattern.md
- contents/design-pattern/compensation-vs-reconciliation-pattern.md
confusable_with:
- design-pattern/semantic-lock-pending-state-pattern
- design-pattern/escalation-reassignment-queue-ownership-pattern
- design-pattern/process-manager-deadlines-timeouts
- design-pattern/workflow-owner-vs-participant-context
forbidden_neighbors: []
expected_queries:
- Human approval이나 manual review는 관리자 화면이 아니라 first-class workflow step으로 왜 모델링해야 해?
- manual review에는 queue assignment, decision semantics, SLA, timeout, override audit가 왜 함께 필요해?
- UNDER_REVIEW 같은 상태는 semantic lock과 함께 어떤 자동 전이를 막아야 해?
- reviewer가 SLA를 넘기면 auto reject, escalate, reassignment 같은 deadline policy를 어떻게 설계해?
- human override는 자동 rule과 어떻게 공존하고 audit record에는 무엇을 남겨야 해?
contextual_chunk_prefix: |
  이 문서는 Human Approval and Manual Review Workflow Pattern playbook으로, 사람이
  들어오는 고위험/규제 workflow를 예외 UI가 아니라 UNDER_REVIEW/PENDING_APPROVAL 같은 상태,
  queue assignment, decision semantics, SLA/deadline, semantic lock, override audit, escalation/reassignment를
  가진 first-class workflow step으로 모델링하는 방법을 설명한다.
---
# Human Approval and Manual Review Workflow Pattern

> 한 줄 요약: 자동화가 위험하거나 규제상 설명 가능성이 필요한 흐름은 human approval/manual review를 first-class workflow step으로 모델링해야 하며, queue, SLA, timeout, override, audit를 함께 설계해야 한다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)
> - [Escalation, Reassignment, and Queue Ownership Pattern](./escalation-reassignment-queue-ownership-pattern.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [Compensation vs Reconciliation Pattern](./compensation-vs-reconciliation-pattern.md)

---

## 핵심 개념

모든 workflow를 끝까지 자동화할 수는 없다.

- 고액 환불
- 사기 의심 결제
- 대출 심사
- 계정 복구/권한 승격

이런 흐름은 사람 검토가 들어가는 순간 architecture가 달라진다.  
단순 예외 처리로 넣으면 안 되고, **manual review step 자체를 workflow 상태로 승격**해야 한다.

### Retrieval Anchors

- `manual review workflow`
- `human approval step`
- `review queue pattern`
- `human in the loop workflow`
- `approval sla`
- `review override audit`
- `escalation policy`
- `reassignment policy`

---

## 깊이 들어가기

### 1. manual review는 실패 fallback이 아니라 정상 경로일 수 있다

많은 팀이 수동 검토를 "자동화 실패 시 예외 처리"처럼 넣는다.  
하지만 실무에서는 아예 정식 경로인 경우가 많다.

- rule engine이 review로 분기
- 사람이 승인/반려
- 그 결과로 다음 participant 호출

즉 review는 error path가 아니라 workflow branch다.

### 2. review 상태는 semantic lock과 함께 가야 한다

검토 중인 대상은 보통 다른 전이를 제한해야 한다.

- 중복 승인 금지
- 자동 취소 금지
- 값 수정 제한

그래서 `UNDER_REVIEW`, `PENDING_APPROVAL`, `WAITING_ANALYST_DECISION` 같은 상태가 필요하다.

### 3. queue와 decision은 분리해서 봐야 한다

manual review에는 두 층이 있다.

- queue assignment: 누가 보나
- decision semantics: 승인/반려/추가정보요청/에스컬레이션

둘을 한 필드에 우겨 넣으면 운영 가시성이 떨어진다.

### 4. human step에는 SLA와 timeout이 필요하다

사람이 들어오면 더더욱 시간 정책이 중요하다.

- 30분 내 1차 응답
- 24시간 내 최종 결정
- timeout 시 자동 반려 또는 escalate

즉 human approval도 process manager deadline 문제다.

### 5. override와 audit는 처음부터 같이 설계해야 한다

사람 결정은 설명 가능성과 추적 가능성이 중요하다.

- 누가 결정했는가
- 어떤 근거로 결정했는가
- override했는가
- 이전 자동 판단과 왜 달랐는가

이게 없으면 manual review는 운영 편의 기능이 아니라 감사 리스크가 된다.

---

## 실전 시나리오

### 시나리오 1: 고액 환불

자동 rule이 `UNDER_REFUND_REVIEW`로 보내고, reviewer가 승인/반려를 결정한다.  
결정 전까지 자동 환불 실행은 막아야 한다.

### 시나리오 2: 사기 의심 결제

결제는 일시 hold하고 analyst review queue로 보낸다.  
SLA 초과 시 자동 취소 또는 escalation이 필요할 수 있다.

### 시나리오 3: 계정 권한 승격

사람 승인 없이는 grant가 안 되지만, reviewer 부재 시 정체되면 안 되므로 timeout/escalation 정책이 필요하다.

---

## 코드로 보기

### review state

```java
public enum ReviewStatus {
    UNDER_REVIEW,
    APPROVED,
    REJECTED,
    ESCALATED
}
```

### decision record

```java
public record ReviewDecision(
    String reviewerId,
    ReviewStatus status,
    String reason,
    Instant decidedAt
) {}
```

### workflow handling

```java
public void on(FraudCheckFlagged event) {
    workflow.markUnderReview();
    commandBus.dispatch(new EnqueueManualReview(event.orderId()));
    commandBus.dispatch(new ScheduleReviewTimeout(event.orderId(), event.reviewDeadline()));
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 완전 자동화 | 빠르다 | 고위험/규제 케이스에 취약하다 | 저위험, reversible 흐름 |
| human approval step | 설명 가능성과 안전성이 높다 | SLA, 운영, audit 비용이 든다 | 고액/사기/권한/규제 워크플로 |
| manual review without workflow model | 빠르게 붙일 수 있다 | 상태/시간/감사 추적이 흐려진다 | 보통 피하는 편이 좋다 |

판단 기준은 다음과 같다.

- 사람이 들어오면 review를 정식 workflow step으로 모델링한다
- semantic lock, SLA, override audit를 함께 둔다
- queue assignment와 business decision을 구분한다

---

## 꼬리질문

> Q: manual review는 그냥 관리자 화면 하나면 되지 않나요?
> 의도: UI와 workflow state를 구분하는지 본다.
> 핵심: 아니다. review는 상태, timeout, decision semantics까지 가진 workflow step이다.

> Q: reviewer가 없어서 SLA를 넘기면 어떻게 하나요?
> 의도: human step도 deadline 설계가 필요함을 아는지 본다.
> 핵심: auto reject, escalate, reassignment 같은 정책이 필요하다.

> Q: 사람이 override하면 자동 rule은 의미 없나요?
> 의도: automation과 human override의 관계를 보는 질문이다.
> 핵심: 아니다. 자동 rule은 triage를 돕고, override는 감사 가능한 예외 경로가 된다.

## 한 줄 정리

Human approval/manual review는 예외 처리 화면이 아니라, 상태·SLA·decision audit를 가진 정식 workflow step으로 설계해야 안전하다.
