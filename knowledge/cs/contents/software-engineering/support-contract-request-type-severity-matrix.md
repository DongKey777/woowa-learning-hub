# Support Contract Request Type and Severity Matrix

> 한 줄 요약: support SLA가 실제로 작동하려면 normal question, migration help, contract change, incident escalation 같은 request type과 severity를 나눠 각각 다른 response expectation과 handoff path를 주는 matrix가 필요하다.

**난이도: 🔴 Advanced**

> related 문서:
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)
> - [Deprecation Communication Playbook](./deprecation-communication-playbook.md)
> - [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)

> retrieval-anchor-keywords:
> - support matrix
> - request type matrix
> - severity matrix
> - support contract template
> - escalation severity
> - migration support type
> - producer consumer support matrix
> - request classification

## 핵심 개념

같은 "지원 요청"이라도 성격이 완전히 다르다.

예:

- API 문의
- migration help
- deprecation 문의
- contract breaking issue
- sev1 incident escalation

이걸 모두 하나의 response SLA로 관리하면 현실과 맞지 않는다.
그래서 request type x severity matrix가 필요하다.

---

## 깊이 들어가기

### 1. request type을 먼저 나눠야 한다

보통 유용한 분류:

- information request
- migration support
- contract clarification
- rollout / release support
- incident escalation

이 분류가 있어야 어떤 경로는 business hours로 충분하고, 어떤 경로는 on-call이 필요한지 구분할 수 있다.

### 2. severity는 business/operational impact와 연결돼야 한다

같은 migration support라도:

- planned question
- release blocker
- active incident-related blocker

는 모두 다르다.

즉 severity는 감정의 크기가 아니라 **영향과 urgency**로 정의해야 한다.

### 3. matrix는 response expectation과 owner를 같이 적어야 한다

좋은 matrix는 최소한 다음을 준다.

- request type
- severity
- first response SLA
- owning team
- escalation path
- handoff rule

이게 없으면 요청자는 urgency를 모르고, 제공 팀은 무엇을 언제까지 해야 하는지 모른다.

### 4. deprecation/migration 기간에는 별도 matrix가 필요할 수 있다

sunset 직전에는 migration support volume이 급증할 수 있다.
평시 support model만으로는 부족할 수 있다.

예:

- office hour 확대
- temp support alias
- dedicated escalation owner
- final week sev uplift

### 5. matrix는 catalog와 support tooling에 노출돼야 한다

지원 계약이 문서에만 있으면 실제 요청은 여전히 개인 DM으로 간다.
그래서 matrix는:

- service catalog
- team support page
- deprecation notice
- tombstone response

와 연결되어야 한다.

---

## 실전 시나리오

### 시나리오 1: normal question이 incident channel로 들어온다

matrix가 없어서 request type 분류가 흐린 상태다.

### 시나리오 2: migration blocker인데 business-hours support만 제공된다

release 일정과 severity 기준이 맞지 않는 support contract일 수 있다.

### 시나리오 3: deprecation cut-off 전 주에 문의가 폭주한다

평시 matrix와 cutover-week matrix를 분리하는 편이 현실적일 수 있다.

---

## 코드로 보기

```yaml
support_matrix:
  - type: migration_support
    severity: blocker
    first_response: 4_hours
    owner: producer-team
    escalate_to: migration-sponsor
  - type: incident_escalation
    severity: sev1
    first_response: immediate
    owner: oncall
```

좋은 matrix는 support SLA를 실제 triage 구조로 바꾼다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 support SLA | 단순하다 | 현실을 못 담는다 | 아주 작은 팀 |
| request type matrix | 명확하다 | 설계가 필요하다 | 여러 요청 유형이 있을 때 |
| type + severity matrix | 가장 현실적이다 | 운영 discipline이 필요하다 | shared/critical service |

support contract matrix의 목적은 표를 늘리는 것이 아니라, **서로 다른 요청을 같은 통으로 처리해 생기는 오해와 escalation 혼선을 줄이는 것**이다.

---

## 꼬리질문

- request type이 충분히 구분돼 있는가?
- migration blocker와 normal question이 같은 SLA를 쓰고 있지는 않은가?
- deprecation/sunset 주간의 support profile이 별도로 필요한가?
- matrix가 catalog와 tombstone guidance에 실제로 노출되는가?

## 한 줄 정리

Support contract request type and severity matrix는 지원 요청을 유형과 심각도로 나눠 response expectation과 escalation path를 명확히 해, team API의 지원 면을 더 실행 가능하게 만드는 구조다.
