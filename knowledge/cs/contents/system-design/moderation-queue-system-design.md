---
schema_version: 3
title: Moderation Queue System 설계
concept_id: system-design/moderation-queue-system-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- moderation queue
- content moderation
- report queue
- human review
aliases:
- moderation queue
- content moderation
- report queue
- human review
- policy engine
- escalation
- trust and safety
- triage
- review SLA
- harmful content
- Moderation Queue System 설계
- moderation queue system design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/fraud-risk-scoring-pipeline-design.md
- contents/system-design/fraud-case-management-workflow-design.md
- contents/system-design/job-queue-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/notification-system-design.md
- contents/system-design/rate-limiter-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Moderation Queue System 설계 설계 핵심을 설명해줘
- moderation queue가 왜 필요한지 알려줘
- Moderation Queue System 설계 실무 트레이드오프는 뭐야?
- moderation queue 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Moderation Queue System 설계를 다루는 deep_dive 문서다. moderation queue system은 신고, 자동 탐지, 인간 검토를 결합해 사용자 생성 콘텐츠를 안전하게 심사하는 운영 파이프라인이다. 검색 질의가 moderation queue, content moderation, report queue, human review처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Moderation Queue System 설계

> 한 줄 요약: moderation queue system은 신고, 자동 탐지, 인간 검토를 결합해 사용자 생성 콘텐츠를 안전하게 심사하는 운영 파이프라인이다.

retrieval-anchor-keywords: moderation queue, content moderation, report queue, human review, policy engine, escalation, trust and safety, triage, review SLA, harmful content

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Fraud / Risk Scoring Pipeline 설계](./fraud-risk-scoring-pipeline-design.md)
> - [Fraud Case Management Workflow 설계](./fraud-case-management-workflow-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Notification 시스템 설계](./notification-system-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)

## 핵심 개념

모더레이션은 "신고가 들어오면 삭제"가 아니다.  
실전에서는 아래를 함께 처리한다.

- 신고 수집
- 자동 분류
- 우선순위 triage
- human review
- policy action
- appeals

즉, moderation queue는 안전 정책을 운영 워크플로우로 바꾸는 시스템이다.

## 깊이 들어가기

### 1. 무엇을 검토하는가

대상:

- spam
- harassment
- NSFW
- impersonation
- scam
- illegal content

모든 콘텐츠를 같은 우선순위로 처리하면 안 된다.

### 2. Capacity Estimation

예:

- 하루 신고 100만 건
- 자동 필터 95% 처리
- 나머지 5% human review

이때 human queue와 automation path를 분리해야 한다.

봐야 할 숫자:

- report intake
- auto-action rate
- review SLA
- escalation rate
- appeal rate

### 3. Workflow

```text
REPORTED -> TRIAGED -> AUTO_ACTION / HUMAN_REVIEW -> APPEAL -> FINALIZED
```

각 상태는 증거와 정책 버전과 연결된다.

### 4. policy engine

정책은 단순 규칙이 아니라 버전이 있는 규정이다.

- policy version
- severity mapping
- locale-specific policy
- tenant/community policy

### 5. Human review

검토자 경험이 중요하다.

- evidence bundle
- previous history
- policy rationale
- one-click actions

운영자가 빨리 판단할 수 있어야 SLA를 지킬 수 있다.

### 6. Appeals

모더레이션은 반론 절차가 필요하다.

- appeal 제출
- secondary review
- decision audit

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결된다.

### 7. abuse and rate limiting

신고 시스템도 남용된다.

- mass report attack
- brigading
- bot spam

그래서 [Rate Limiter 설계](./rate-limiter-design.md)와 결합해야 한다.

## 실전 시나리오

### 시나리오 1: 신고 폭주

문제:

- 특정 게시물이 대량 신고된다

해결:

- 신고 dedup
- 우선순위 triage
- 자동 분류 강화

### 시나리오 2: 오탐으로 인한 사용자 불만

문제:

- 정상 게시물이 삭제된다

해결:

- appeal workflow
- policy version rollback

### 시나리오 3: human review backlog

문제:

- 검토 대기열이 쌓인다

해결:

- auto-action 확대
- priority queue 분리
- reviewer load balancing

## 코드로 보기

```pseudo
function submitReport(itemId, reason):
  if dedup.exists(itemId, reason):
    return
  case = triageEngine.create(itemId, reason)
  queue.publish(case)

function review(caseId, action):
  policyLog.write(caseId, action)
  applyAction(action)
```

```java
public ModerationCase open(Report report) {
    return moderationService.triage(report);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Auto-remove heavy | 빠르다 | 오탐 위험 | 확실한 위반 |
| Human-review heavy | 정확하다 | SLA가 느리다 | 민감한 케이스 |
| Hybrid triage | 실무적이다 | 운영 복잡도 | 대부분의 플랫폼 |
| Appeal enabled | 공정하다 | workflow 증가 | 사용자 신뢰 중요 |
| Policy-versioned actions | 감사가 쉽다 | 정책 관리 필요 | 장기 운영 |

핵심은 moderation이 단순 신고 처리기가 아니라 **정책, 증거, 인간 판단을 잇는 안전 운영 시스템**이라는 점이다.

## 꼬리질문

> Q: 왜 moderation에 human review가 필요한가요?
> 의도: 오탐과 설명 가능성 이해 확인
> 핵심: 자동 규칙만으로는 맥락을 다 못 본다.

> Q: appeals는 왜 중요하나요?
> 의도: 공정성과 운영 신뢰 이해 확인
> 핵심: 사용자에게 이의제기 절차가 있어야 한다.

> Q: 신고 시스템도 왜 rate limit이 필요한가요?
> 의도: abuse 방지 이해 확인
> 핵심: brigading과 봇 공격을 막아야 하기 때문이다.

> Q: policy version은 왜 남기나요?
> 의도: 판단 기준 재현성 이해 확인
> 핵심: 어떤 규정으로 조치했는지 추적해야 한다.

## 한 줄 정리

Moderation queue system은 신고와 자동 판별, 인간 검토, 이의제기를 합쳐 콘텐츠 안전 정책을 운영하는 워크플로우다.

