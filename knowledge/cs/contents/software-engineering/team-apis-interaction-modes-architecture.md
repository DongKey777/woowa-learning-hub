# Team APIs and Interaction Modes in Architecture

> 한 줄 요약: 소프트웨어 경계는 코드 API만으로 유지되지 않고, 팀 사이의 요청 경로, 승인 방식, 지원 책임 같은 team API와 interaction mode가 맞아야 지속 가능하므로, architecture design은 기술 경계와 협업 경계를 함께 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Organizational Coupling and Conway Effects](./organizational-coupling-conway-effects.md)
> - [Team Cognitive Load and Boundary Design](./team-cognitive-load-boundary-design.md)
> - [Platform Team, Product Team, and Business Capability Boundaries](./platform-team-product-team-capability-boundaries.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)

> retrieval-anchor-keywords:
> - team api
> - interaction mode
> - collaboration mode
> - socio-technical interface
> - team boundary
> - service collaboration
> - request path between teams
> - coordination protocol

## 핵심 개념

시스템 간 API만 잘 만들면 협업 비용이 줄어드는 것처럼 보이지만, 실제로는 팀 간 상호작용 방식이 더 큰 영향을 줄 때가 많다.

예:

- 변경 요청은 어떤 경로로 들어오는가
- 긴급 이슈는 누구에게 어떻게 escalation되는가
- 계약 변경은 self-service인가, review가 필요한가
- 공통 capability는 플랫폼이 서비스처럼 제공하는가, 지원팀처럼 제공하는가

이런 협업 규칙을 team API 또는 interaction mode로 볼 수 있다.
즉 architecture는 코드 구조만이 아니라 **팀 간 요청과 책임의 프로토콜**도 설계해야 한다.

---

## 깊이 들어가기

### 1. 기술 API와 team API는 서로 영향을 준다

좋은 service API라도 team API가 나쁘면 결과는 느려진다.

예:

- API는 self-service인데 실제 승인자는 항상 특정 개인
- contract는 안정적이지만 consumer 질문이 전부 슬랙 DM에 의존
- platform capability는 문서상 공통인데 지원 모델은 ad-hoc

즉 loose coupling은 코드에서만 생기지 않는다.

### 2. interaction mode를 의도적으로 나눠야 한다

보통 팀 간 상호작용은 몇 가지 패턴으로 나눌 수 있다.

- self-service: catalog, docs, control plane, policy gate로 해결
- stewardship/review: 로컬 설계나 경계 점검
- collaboration: 특정 migration이나 공동 feature
- escalation: incident, policy exception, high-risk decision

이 구분이 없으면 모든 요청이 같은 무게로 흘러 병목이 생긴다.

### 3. team API는 interface contract처럼 명시돼야 한다

팀 사이의 기대도 문서화해야 한다.

예:

- response time expectation
- required metadata
- support hours
- escalation path
- override request flow

구두로만 유지하면 팀이 바뀔 때 interaction cost가 급증한다.

### 4. 잘못된 interaction mode는 shadow path를 만든다

공식 경로가 느리거나 불명확하면 비공식 경로가 생긴다.

예:

- 개인 DM 승인
- 회의실에서만 공유되는 운영 지식
- 특정 운영자만 아는 break-glass 절차
- 문서 없는 팀 간 workaround

이런 shadow interaction은 시스템 경계를 코드보다 먼저 무너뜨린다.

### 5. socio-technical design은 lifecycle과 함께 바뀌어야 한다

incubating 서비스와 critical 서비스는 같은 interaction mode를 쓰면 안 될 수 있다.
temporary 실험과 공통 플랫폼 capability도 지원 방식이 달라야 한다.

즉 team API는 service stage, criticality, ownership maturity와 같이 진화해야 한다.

---

## 실전 시나리오

### 시나리오 1: 플랫폼 문의가 특정 사람에게 몰린다

이는 기술 문제가 아니라 self-service team API가 약하다는 신호다.
catalog, docs, control plane, escalation route를 다시 설계해야 한다.

### 시나리오 2: migration 중 두 팀이 계속 충돌한다

contract만 맞춰선 부족하고, approval flow와 consumer support path까지 명시해야 한다.

### 시나리오 3: incident 때 항상 잘못된 팀이 먼저 호출된다

on-call matrix와 service ownership은 있어도 실제 escalation interaction mode가 잘못 설계된 것일 수 있다.

---

## 코드로 보기

```yaml
team_api:
  producer_team: commerce-platform
  consumer_team: growth-app
  interaction_modes:
    default: self_service
    contract_change: stewardship_review
    incident: escalation
  expectations:
    response_time: 2_business_days
    emergency_path: oncall_escalation
```

좋은 team API는 사람 사이의 협업도 인터페이스처럼 다룬다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ad-hoc interaction | 빠르게 움직일 수 있다 | 사람 의존성이 커진다 | 아주 작은 팀 |
| formal team API | 예측 가능하다 | 정의 비용이 든다 | 여러 팀이 얽힌 시스템 |
| mixed interaction mode | 현실적이다 | 운영 discipline이 필요하다 | 성장 조직 |

team APIs and interaction modes를 설계하면 협업을 느리게 만드는 것이 아니라, **암묵적 조율 비용을 줄여 구조와 조직이 같이 견디게 만드는 것**이다.

---

## 꼬리질문

- 이 경계는 코드 API는 있지만 team API는 없는 상태가 아닌가?
- self-service가 되어야 할 요청이 사람 승인에 묶여 있지는 않은가?
- incident와 override는 어떤 interaction mode로 처리되는가?
- 팀 구조가 바뀌어도 이 협업 프로토콜이 유지되는가?

## 한 줄 정리

Team APIs and interaction modes in architecture는 서비스 간 인터페이스뿐 아니라 팀 간 요청·승인·지원 프로토콜까지 설계해 socio-technical coupling을 줄이는 관점이다.
