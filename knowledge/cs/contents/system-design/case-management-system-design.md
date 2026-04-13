# Case Management System 설계

> 한 줄 요약: case management system은 문제, 신고, 요청, 이슈를 케이스로 표준화해 할당, 추적, 승인, 해결을 운영하는 워크플로우 플랫폼이다.

retrieval-anchor-keywords: case management system, triage, assignment, SLA, notes, attachments, status workflow, escalation, approval, customer support case

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Fraud Case Management Workflow 설계](./fraud-case-management-workflow-design.md)
> - [Moderation Queue System 설계](./moderation-queue-system-design.md)
> - [Tenant Billing Dispute Workflow 설계](./tenant-billing-dispute-workflow-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Job Queue 설계](./job-queue-design.md)

## 핵심 개념

Case management는 "티켓"보다 넓다.  
실전에서는 다음을 함께 관리해야 한다.

- 사건 분류와 triage
- 담당자 할당
- 상태 전이와 SLA
- 첨부 증거와 메모
- 승격과 에스컬레이션
- 이력과 audit

즉, case management는 사람의 판단을 조직적으로 운영하는 플랫폼이다.

## 깊이 들어가기

### 1. case를 표준화해야 하는 이유

문제가 종류마다 다르면 운영이 흩어진다.

- support issue
- billing dispute
- fraud review
- compliance request
- moderation report

케이스로 표준화하면 공통 workflow를 재사용할 수 있다.

### 2. Capacity Estimation

예:

- 하루 10만 케이스
- 팀별 SLA 다름
- 첨부파일/메모 많음

핵심은 저장량보다 상태 전이와 assignment throughput이다.

봐야 할 숫자:

- open case count
- time to first response
- SLA breach rate
- reassignment rate
- escalation rate

### 3. workflow

```text
OPEN -> TRIAGED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
              \-> ESCALATED -> WAITING -> RESOLVED
```

상태는 단순하지만 각 상태에 책임과 타이머가 있어야 한다.

### 4. assignment and queue

케이스 할당은 단순 round-robin이 아니다.

- skill-based routing
- priority
- tenant plan
- workload balance
- language/region

이 부분은 [Job Queue 설계](./job-queue-design.md)와 연결된다.

### 5. notes, attachments, and audit

케이스는 증거와 커뮤니케이션의 집합이다.

- notes
- screenshots
- file attachments
- timeline events
- decision logs

이력은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 연결된다.

### 6. SLA and escalation

케이스 관리의 핵심은 시간이다.

- first response SLA
- resolve SLA
- escalated threshold
- auto-reminder

### 7. integration

케이스는 다른 시스템의 결과를 받아야 한다.

- fraud scoring
- billing disputes
- moderation
- support chat

## 실전 시나리오

### 시나리오 1: 고객 지원 케이스

문제:

- 같은 고객 문의가 여러 번 들어온다

해결:

- dedup
- thread merge
- status sync

### 시나리오 2: billing dispute

문제:

- 과금 이의 제기가 증거와 함께 올라온다

해결:

- evidence attachment
- specialist routing
- approval step

### 시나리오 3: 대량 에스컬레이션

문제:

- 특정 사건이 대량으로 쏟아진다

해결:

- priority queue
- triage automation
- workload balancing

## 코드로 보기

```pseudo
function createCase(type, payload):
  case = repo.create(type, payload)
  route = router.pick(case)
  queue.publish(route, case.id)
  return case

function resolveCase(caseId, decision):
  repo.updateStatus(caseId, decision)
  audit.log(caseId, decision)
```

```java
public Case create(CaseRequest req) {
    return caseService.open(req);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Simple ticket table | 단순하다 | workflow가 약하다 | 작은 조직 |
| Workflow engine | 상태 관리가 강하다 | 운영 복잡도 | 여러 팀 협업 |
| Skill-based routing | 처리 품질이 좋다 | 설정이 복잡하다 | 대규모 운영 |
| Event-sourced case | 감사와 재현이 쉽다 | 구현이 무겁다 | 규제/고신뢰 |
| SLA-driven queue | 시간 관리가 좋다 | priority starvation 위험 | 운영 센터 |

핵심은 case management가 단순 티켓이 아니라 **사람의 판단을 표준 workflow로 바꾸는 운영 시스템**이라는 점이다.

## 꼬리질문

> Q: case management와 workflow orchestration은 어떻게 다른가요?
> 의도: 운영 UI와 실행 엔진 구분 확인
> 핵심: case는 사람 중심, workflow는 자동 전이가 중심이다.

> Q: SLA를 왜 넣나요?
> 의도: 운영 우선순위 이해 확인
> 핵심: 처리 시간 관리가 조직 운영의 핵심이기 때문이다.

> Q: notes와 audit log는 무엇이 다른가요?
> 의도: 사용자 메모와 증거 기록 구분 확인
> 핵심: notes는 협업, audit는 증거다.

> Q: 자동 triage는 어디까지 가능한가요?
> 의도: 자동화와 인간 판단 경계 이해 확인
> 핵심: 분류는 자동화 가능하지만 최종 판단은 사람일 수 있다.

## 한 줄 정리

Case management system은 다양한 문제를 표준 케이스로 바꿔 할당, 추적, 에스컬레이션, 해결을 운영하는 사람 중심 워크플로우 플랫폼이다.

