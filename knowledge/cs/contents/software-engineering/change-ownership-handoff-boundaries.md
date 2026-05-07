---
schema_version: 3
title: Change Ownership Handoff Boundaries
concept_id: software-engineering/change-ownership-handoff
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- ownership
- handoff
- support-boundary
aliases:
- Change Ownership Handoff Boundaries
- ownership handoff
- responsibility transfer
- support handoff
- warm transfer
- service stewardship handoff
symptoms:
- 코드 소유만 넘기고 배포, 운영, 온콜, business-hours support, 고객 커뮤니케이션, escalation decision 권한은 모호하게 남겨
- 문서 링크만 전달하는 cold transfer로 handoff를 끝내 old support lane과 new owner가 동시에 살아 split-brain ownership이 생겨
- handoff exit criteria를 승인 체크로만 보고 새 owner가 실제 support 요청이나 drill을 처리했다는 운영 증거 없이 종료해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/support-sla-escalation-contracts
next_docs:
- software-engineering/on-call-ownership-boundaries
- software-engineering/incident-feedback-policy-ownership-closure
- software-engineering/service-portfolio-lifecycle-governance
linked_paths:
- contents/software-engineering/service-ownership-catalog-boundaries.md
- contents/software-engineering/support-sla-escalation-contracts.md
- contents/software-engineering/support-operating-models-self-service-office-hours-oncall.md
- contents/software-engineering/on-call-ownership-boundaries.md
- contents/software-engineering/platform-team-product-team-capability-boundaries.md
- contents/software-engineering/incident-review-learning-loop-architecture.md
- contents/software-engineering/adr-decision-records-at-scale.md
- contents/software-engineering/runbook-playbook-automation-boundaries.md
- contents/software-engineering/service-portfolio-lifecycle-governance.md
- contents/software-engineering/incident-feedback-policy-ownership-closure.md
confusable_with:
- software-engineering/service-ownership-catalog-boundaries
- software-engineering/on-call-ownership-boundaries
- software-engineering/support-sla-escalation-contracts
forbidden_neighbors: []
expected_queries:
- change ownership handoff에서 코드 소유, 배포 소유, 운영 소유, 온콜 소유, support 소유를 왜 따로 봐야 해?
- handoff를 문서 링크 전달이 아니라 warm transfer로 하려면 어떤 packet과 transition period가 필요해?
- old support lane retire와 new lane publish를 하지 않으면 어떤 split-brain ownership이 생겨?
- handoff exit criteria는 새 owner가 support 요청이나 drill을 처리한 운영 증거로 어떻게 닫아야 해?
- escalation SLA clock이 팀 transfer마다 reset되지 않게 handoff boundary를 어떻게 설계해?
contextual_chunk_prefix: |
  이 문서는 change ownership handoff를 code, deploy, operations, on-call, business-hours support, customer communication, escalation decision 책임의 warm transfer로 설계하는 advanced playbook이다.
---
# Change Ownership Handoff Boundaries

> 한 줄 요약: change ownership handoff는 업무를 넘기는 것이 아니라, 설계·운영·support·온콜 책임을 어떤 경계에서 누구에게 넘길지 명확히 정하는 절차다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [ADRs and Decision Records at Scale](./adr-decision-records-at-scale.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)

> retrieval-anchor-keywords:
> - change ownership
> - handoff
> - responsibility transfer
> - operator handoff
> - service stewardship
> - release ownership
> - support boundary
> - support handoff
> - warm transfer
> - cold transfer
> - transition checklist

## 핵심 개념

기능이나 서비스가 바뀔 때, 일을 "넘긴다"는 표현은 너무 넓다.

실제로는 다음 책임이 따로 움직인다.

- 코드 소유
- 배포 소유
- 운영 소유
- 온콜 소유
- business-hours support 소유
- 문서 소유
- 고객 커뮤니케이션 소유
- escalation decision 권한

change ownership handoff는 이 책임 경계를 안전하게 이동시키는 일이다.

---

## 깊이 들어가기

### 1. handoff는 단일 이벤트가 아니라 단계다

좋은 handoff에는 보통 다음이 있다.

- 사전 공지
- 공동 운영 기간
- 권한/접근 이관
- runbook 업데이트
- 모니터링 확인
- support alias / intake lane 전환
- 최종 승인

즉 갑작스러운 책임 이동은 사고 확률을 높인다.

특히 support 관점에서는 다음 두 단계가 빠지기 쉽다.

- old lane retire: 예전 개인 DM, 채널, alias를 종료하거나 만료시킨다
- new lane publish: 카탈로그, runbook, escalation path에 새 owner를 노출한다

### 2. ownership은 코드보다 먼저 합의되어야 한다

새 팀이 코드만 받고 운영은 옛 팀이 계속 맡으면 경계가 깨진다.

모든 handoff는 다음 질문에 답해야 한다.

- 누가 배포를 승인하는가?
- 누가 장애를 받는가?
- 누가 보정 작업을 수행하는가?
- 누가 고객과 소통하는가?
- 누가 business-hours support queue를 받는가?
- 누가 after-hours escalation을 수락하는가?

### 3. handoff 전에 observability를 확인해야 한다

책임을 넘길 때는 상대 팀이 시스템을 읽을 수 있어야 한다.

필수:

- 대시보드
- 알림 채널
- runbook
- 서비스 카탈로그
- ADR 또는 변경 설명
- support ticket / chat history
- 최근 incident, recurring question, known workaround

관측이 없으면 책임만 넘겨지고 대응은 못 한다.

### 4. transition period는 안전망이다

공동 운영 기간이 있어야 새 owner가 실제로 문제를 경험하고 학습한다.

이 기간 동안:

- 옛 owner가 backup 역할
- 새 owner가 primary 역할
- 장애 대응을 함께 수행
- business-hours support를 실제로 새 owner가 먼저 받음
- escalation 시 old owner가 timeout-bound backup으로만 참여

이렇게 해야 handoff가 문서상 변경이 아니라 실제 운영 전환이 된다.

### 5. handoff exit criteria는 관찰 가능한 증거여야 한다

handoff가 끝났다고 말하려면 단순 승인보다 운영 증거가 필요하다.

예:

- 새 owner가 실제 support 요청 N건을 끝까지 처리했다
- 새 owner가 primary로 incident 또는 drill을 한 번 이상 수행했다
- runbook과 dashboard 링크가 새 팀 맥락으로 검증됐다
- catalog, support page, on-call matrix가 모두 갱신됐다
- old support alias가 retire되거나 명시적으로 forward expiry를 가졌다

이 기준이 없으면 transition period가 끝났는지 누구도 자신 있게 말하지 못한다.

### 6. support handoff anti-pattern은 ownership gap을 숨긴다

자주 보이는 실패는 비슷하다.

- documentation drop: 문서 링크만 넘기고 실제 support queue는 계속 옛 팀이 받는다
- cold transfer: active issue 한가운데에서 맥락 없이 새 팀으로 넘긴다
- split-brain ownership: 새 팀이 pager는 들고 옛 팀이 DM 문의를 계속 처리한다
- infinite shadow period: "아직 익숙하지 않아서"라는 이유로 공동 운영이 끝나지 않는다
- clock reset on transfer: 팀이 바뀔 때마다 SLA나 update 약속을 처음부터 다시 잡는다

이 anti-pattern은 handoff를 체크리스트 완료로만 보고,
support lane retire/publish와 escalation acceptance를 설계하지 않을 때 생긴다.

### 7. handoff 후에도 피드백 루프가 필요하다

이관 후에는 다음을 확인해야 한다.

- 문서가 충분했는가
- runbook이 실제로 쓸모 있었는가
- 온콜 경계가 명확했는가
- 책임이 중복되거나 비어 있지 않은가
- old lane이 실제로 닫혔는가
- support/escalation handoff에서 clock 손실이 있었는가

이 피드백은 다음 handoff를 개선한다.

---

## 실전 시나리오

### 시나리오 1: 기능이 플랫폼 팀으로 넘어간다

제품 팀에서 운영 공통 기능을 플랫폼 팀으로 이관할 때는, 코드만 넘기지 말고 알림, 배포, runbook, support alias, 온콜까지 함께 넘겨야 한다.

### 시나리오 2: 서비스가 다른 팀으로 편입된다

합병 후 소유권이 바뀌면 API 사용처, SLA, support page, 교대표까지 다시 정리해야 한다.

### 시나리오 3: 긴급 장애 대응 후 영구 책임을 재조정한다

임시 대응으로 다른 팀이 대신 맡던 기능을, 사고가 지나면 원래 소유 또는 새 소유로 명확히 돌려놔야 한다.
incident 때만 도와준 팀이 permanent shadow owner가 되면 handoff는 끝난 것이 아니다.

---

## 코드로 보기

```markdown
Handoff contract:
- Owner change announced
- Support page and service catalog updated
- Runbook updated
- Alerts transferred
- Dashboards verified
- Business-hours support switched
- Primary on-call switched
- Backup shadow period completed
- Old alias retirement date set
- New owner closed 3 real requests
```

handoff는 체크리스트가 없으면 쉽게 누락되고, **지원/에스컬레이션 경로가 없으면 완료된 것처럼 보여도 실제로는 끝나지 않는다**.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 즉시 이관 | 빠르다 | 누락이 많다 | 작은 변경 |
| 공동 운영 후 이관 | 안전하다 | 시간이 든다 | 핵심 서비스 |
| 단계적 이관 | 균형이 좋다 | 관리 포인트가 많다 | 조직이 큰 경우 |

ownership handoff의 본질은 책임을 옮기는 것이 아니라 **새 owner가 support와 escalation까지 실제로 수행 가능하게 만드는 것**이다.

---

## 꼬리질문

- 소유권 이관 후 누가 장애를 받는가?
- runbook과 대시보드는 언제 업데이트되는가?
- 공동 운영 기간은 얼마나 둘 것인가?
- 임시 책임과 영구 책임을 어떻게 구분할 것인가?
- business-hours support와 after-hours escalation은 언제 누구에게 바뀌는가?
- old support lane은 언제 retire되는가?

## 한 줄 정리

Change ownership handoff는 업무 전달이 아니라, 운영 책임과 support/escalation 권한을 안전하게 넘기고 old lane을 retire하는 전환 절차다.
