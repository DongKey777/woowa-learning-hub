---
schema_version: 3
title: Incident Review and Learning Loop Architecture
concept_id: software-engineering/incident-review-learning-loop
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- incident-review
- postmortem
- learning-loop
- recovery
aliases:
- Incident Review and Learning Loop Architecture
- blameless postmortem learning loop
- incident action item hygiene
- detection recovery prevention loop
- operational feedback loop
- 인시던트 리뷰 학습 루프
symptoms:
- postmortem은 작성하지만 모니터링, alert threshold, rollback rule, kill switch, runbook, test case로 돌아가지 않아 같은 장애가 반복돼
- action item이 조심하자 같은 추상 문구로 끝나 owner, due date, verification, metric이 없어 실제 학습 루프가 닫히지 않아
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/deployment-rollout-strategy
- software-engineering/feature-flag-dependency-management
next_docs:
- software-engineering/incident-feedback-policy-ownership-closure
- software-engineering/lead-time-change-failure-recovery
- software-engineering/configuration-governance
linked_paths:
- contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md
- contents/software-engineering/feature-flags-rollout-dependency-management.md
- contents/software-engineering/kill-switch-fast-fail-ops.md
- contents/software-engineering/strangler-verification-shadow-traffic-metrics.md
- contents/software-engineering/technical-debt-refactoring-timing.md
- contents/software-engineering/lead-time-change-failure-recovery-loop.md
- contents/software-engineering/configuration-governance-runtime-safety.md
- contents/software-engineering/incident-feedback-policy-ownership-closure.md
confusable_with:
- software-engineering/incident-feedback-policy-ownership-closure
- software-engineering/lead-time-change-failure-recovery
- software-engineering/kill-switch-fast-fail
forbidden_neighbors: []
expected_queries:
- incident review가 누가 잘못했는지 찾는 회의가 아니라 learning loop가 되어야 하는 이유를 설명해줘
- postmortem action item을 코드, 테스트, 알림, runbook, rollback gate로 연결하려면 어떻게 해야 해?
- timeline reconstruction과 system cause 분석이 blameless review에서 왜 중요한가?
- 사고 리뷰 결과가 canary 기준, rollback 조건, kill switch scope로 반영되는 예시를 알려줘
- incident review의 학습 효과를 detection time, recovery time, recurrence rate로 어떻게 측정해?
contextual_chunk_prefix: |
  이 문서는 incident review를 timeline, system cause, action item verification, monitoring/runbook/rollback 개선으로 연결하는 advanced learning loop playbook이다.
---
# Incident Review and Learning Loop Architecture

> 한 줄 요약: 인시던트 리뷰는 사고를 평가하는 회의가 아니라, 탐지부터 복구, 재발 방지까지 학습이 코드와 운영 절차로 돌아가게 만드는 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Strangler Verification, Shadow Traffic Metrics](./strangler-verification-shadow-traffic-metrics.md)
> - [Technical Debt Refactoring Timing](./technical-debt-refactoring-timing.md)
> - [Lead Time, Change Failure, and Recovery Loop](./lead-time-change-failure-recovery-loop.md)
> - [Configuration Governance and Runtime Safety](./configuration-governance-runtime-safety.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)

> retrieval-anchor-keywords:
> - incident review
> - blameless postmortem
> - learning loop
> - action item hygiene
> - recurrence prevention
> - detection to recovery
> - runbook update
> - operational feedback loop

## 핵심 개념

인시던트 리뷰는 누가 잘못했는지 찾는 자리가 아니다.
좋은 리뷰는 사고를 다음 개선으로 연결하는 **학습 루프**를 만든다.

중요한 건 보고서 자체보다, 리뷰 결과가 다음을 바꾸는지다.

- 모니터링 신호
- 알림 기준
- 롤백 절차
- kill switch 조건
- runbook 내용
- 테스트 케이스
- 배포/변경 메트릭

즉 인시던트 리뷰는 문서가 아니라 **운영 시스템의 입력**이어야 한다.

---

## 깊이 들어가기

### 1. 시간순 재구성이 먼저다

리뷰는 먼저 타임라인을 세워야 한다.

- 언제 최초 징후가 있었는가
- 언제 탐지되었는가
- 누구가 어떤 판단을 했는가
- 어떤 완화 조치가 있었는가
- 언제 복구되었는가

이 흐름이 없으면 원인 분석이 감정 싸움으로 흐른다.

### 2. 근본 원인보다 시스템 원인에 집중한다

사람의 실수로 끝내면 재발 방지가 약하다.

좋은 질문:

- 왜 실수가 탐지되지 않았는가
- 왜 자동 완화가 없었는가
- 왜 runbook이 최신이 아니었는가
- 왜 지표가 경고를 못 했는가

이 질문은 개인이 아니라 시스템을 고친다.

### 3. action item은 코드와 운영으로 나뉘어야 한다

리뷰가 실패하는 이유 중 하나는 액션이 너무 추상적이기 때문이다.

좋은 액션 아이템은 다음 중 하나여야 한다.

- 코드 수정
- 테스트 추가
- 대시보드 개선
- 알림 임계값 조정
- runbook 보완
- ownership 재배치

"조심하자"는 액션이 아니다.

### 4. learning loop는 관측 가능해야 한다

리뷰 후에 실제로 좋아졌는지 봐야 한다.

필요한 지표:

- 탐지 시간
- 복구 시간
- 재발률
- 알림 정밀도
- runbook 사용률
- 자동화 비율

즉 리뷰의 결과도 측정 대상이다.

### 5. 리뷰와 배포 안전장치는 분리되면 안 된다

리뷰는 사고 후 학습이지만, 그 결과는 배포 전략에 반영돼야 한다.

예:

- canary 기준 수정
- rollback 조건 변경
- kill switch scope 조정
- shadow compare 강화

이 연결이 없으면 리뷰는 읽고 끝나는 문서가 된다.

---

## 실전 시나리오

### 시나리오 1: 잘못된 배치가 대량 실행됐다

리뷰에서 봐야 할 것:

- 왜 배치 승인 단계가 없었는가
- 왜 dry-run이 없었는가
- 왜 모니터링이 늦었는가
- 왜 kill switch가 없었는가

### 시나리오 2: 서비스 간 계약 불일치로 장애가 났다

이때 리뷰 결과는 계약 테스트, schema versioning, ACL drift 점검으로 이어져야 한다.

### 시나리오 3: 복구는 빨랐지만 재발했다

빠른 복구만으로는 부족하다.
재발했다면 다음을 다시 봐야 한다.

- root cause가 아닌 contributing factors
- 운영 절차의 누락
- 감시 포인트의 공백
- 책임 소유권의 모호함

---

## 코드로 보기

```markdown
## Incident Action Item
- Owner: platform-team
- Due: 2026-05-01
- Change: add rollback gate for batch jobs
- Verification: runbook drill + canary drill
- Metric: reduce mean detection time by 30%
```

행동 가능하고 검증 가능해야 한다.
리뷰는 설명이 아니라 **개선의 입구**여야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| blameless review | 학습이 잘 된다 | 피상적일 수 있다 | 반복 장애를 줄이고 싶을 때 |
| 강한 책임 추적 | 원인 규명이 빠를 수 있다 | 심리적 위축이 생긴다 | 규제/감사 문맥이 강할 때 |
| learning loop 중심 | 개선이 지속된다 | 운영 체계가 필요하다 | 성숙한 조직 운영 |

리뷰의 목적은 기록이 아니라 **재발 방지 능력의 누적**이다.

---

## 꼬리질문

- 리뷰 결과가 실제 runbook과 대시보드에 반영되는가?
- action item을 누가 소유하고 닫는가?
- 반복 장애를 측정하는 지표가 있는가?
- 사고 이후 운영 장치를 바꾸는 루프가 있는가?

## 한 줄 정리

인시던트 리뷰는 사고 분석 문서가 아니라, 탐지와 복구와 예방이 서로 이어지는 학습 루프를 시스템에 다시 주입하는 장치다.
