# Support SLA and Escalation Contracts

> 한 줄 요약: 팀 간 지원은 선의에 기대면 오래 못 가므로, 어떤 요청에 얼마나 빨리 반응하고 언제 어떤 경로로 escalation되는지 명시한 support SLA와 escalation contract가 team API의 일부로 필요하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Service Ownership and Catalog Boundaries](./service-ownership-catalog-boundaries.md)
> - [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)
> - [Support Contract Request Type and Severity Matrix](./support-contract-request-type-severity-matrix.md)
> - [Support Operating Models: Self-Service, Office Hours, On-Call](./support-operating-models-self-service-office-hours-oncall.md)

> retrieval-anchor-keywords:
> - support SLA
> - escalation contract
> - support boundary
> - first response SLA
> - next update SLA
> - support model
> - producer consumer support
> - team support contract
> - escalation ladder
> - support handoff
> - escalation timer

## 핵심 개념

서비스 간 협업에서 가장 자주 숨는 문제 중 하나는 "누가 언제 도와줘야 하는가"가 불명확하다는 점이다.

특히 다음은 암묵적이면 오래 못 간다.

- 일반 문의 first response
- ownership acceptance 시간
- next update cadence
- incident escalation path
- deprecation/sunset during support
- business-hours vs after-hours support
- handoff 후 clock과 owner 유지 방식

즉 support SLA와 escalation contract는 운영 부가사항이 아니라 **team API의 일부인 clock bundle + decision rights + handoff rule**이다.

---

## 깊이 들어가기

### 1. support SLA는 availability SLA와 다르다

서비스가 99.9% 살아 있다는 것과, producer team이 consumer 질문에 1영업일 안에 답한다는 것은 다른 문제다.

좋은 support SLA는 보통 하나의 숫자가 아니라 여러 시계를 가진다.

- first response: 접수 확인과 triage 시작
- ownership acceptance: 누가 실제 owner인지 확정
- next update: 진행 중일 때 얼마나 자주 상태를 주는가
- mitigation target: 우회책이나 임시 조치를 언제 제시할 것인가
- closure expectation: 언제 끝났다고 말할 수 있는가

support SLA가 다루는 것:

- response time
- support hours
- supported request types
- ownership boundary
- expected turnaround

이 시계를 분리하지 않으면 "답은 빨랐는데 아무도 안 맡는다"거나 "ack는 됐는데 다음 업데이트가 없다"는 지원 실패가 생긴다.

### 2. escalation contract는 "언제, 누가, 어떤 권한으로 누굴 깨우는가"를 명시해야 한다

보통 다음이 필요하다.

- primary path
- secondary escalation
- severity 조건
- timeout before escalate
- vendor/platform escalation 여부
- severity 선언 권한
- incident commander 또는 decision owner

이게 없으면 incident 때 개인 DM, 추측, 정치가 들어온다.

좋은 escalation contract는 "문제가 커지면 알아서 누군가 나타난다"를 기대하지 않고,
누가 severity uplift를 할 수 있고 누가 이를 수락하며 언제 다른 팀이나 벤더를 부를지까지 적는다.

### 3. handoff contract는 escalation contract 안에 포함돼야 한다

지원 구조가 무너지는 핵심 지점은 escalation 자체보다 handoff다.

필요한 최소 규칙:

- transfer packet: 현상, 영향 범위, 재현 정보, 관련 로그/대시보드
- receiving owner must acknowledge
- SLA clock reset 여부
- 다음 업데이트 시각
- old owner가 언제까지 backup으로 남는가

이게 없으면 다음 anti-pattern이 반복된다.

- 티켓/채널을 옮길 때마다 같은 설명을 다시 요구하는 ping-pong
- "제가 담당은 아닌데 전달할게요"로 끝나는 silent forwarding
- after-hours에 임시로 도와준 팀이 영구 support owner처럼 남는 sticky escalation
- handoff 때마다 clock을 리셋해 체감 대기 시간을 숨기는 구조

### 4. support model은 service criticality와 request type에 따라 달라야 한다

temporary experimental service에 24/7 support를 강요하면 과하고,
tier 3 shared service에 느슨한 support model을 두면 위험하다.

또한 같은 서비스 안에서도 request type이 다르면 profile이 달라져야 한다.

- normal question
- release blocker
- contract change request
- migration support
- active incident escalation

즉 support SLA도 criticality/stage-aware하고 request-type-aware해야 한다.

### 5. support contract는 deprecation과 migration에도 필요하다

지원 계약이 없으면 consumer는 deprecation notice를 받아도 실제로 어떻게 옮겨야 할지 모른다.

예:

- migration office hours
- support cut-off date
- replacement onboarding support
- final escalation owner
- cutover-week temporary severity uplift

특히 sunset 직전에는 평시 SLA를 그대로 두기보다,
temporary migration profile을 선언하는 편이 현실적이다.

- 어떤 기간에
- 어떤 요청 유형을
- 얼마나 빨리
- 누구 owner로
- 어디까지 지원할지

이 다섯 가지가 보여야 consumer도 migration plan을 믿고 움직일 수 있다.

### 6. contract는 catalog와 runbook과 tooling에 연결돼야 한다

문서가 따로 놀면 현장에서 안 쓰인다.
최소한 다음과 연결돼야 한다.

- service catalog
- on-call matrix
- deprecation playbook
- incident escalation flow
- support intake form / ticket template
- chatops alias or team support page

즉 support SLA는 문서보다 **운영 표면에 노출**되어야 한다.

### 7. support SLA를 약하게 만드는 anti-pattern은 미리 막아야 한다

자주 보이는 실패는 비슷하다.

- 응답 시간만 적고 owner acceptance와 next update는 비워 둔다
- severity 정의가 모호해 모든 요청이 "긴급"이 된다
- support path는 있으나 after-hours path가 없다
- escalation은 정의돼 있지만 handoff acceptance가 없다
- 임시 migration desk가 종료되지 않아 permanent support debt가 된다

이런 anti-pattern은 문장을 더 예쁘게 써서 해결되지 않는다.
clock, owner, trigger, transfer를 각각 계약으로 분리해야 사라진다.

---

## 실전 시나리오

### 시나리오 1: 소비자 질문이 특정 엔지니어 개인에게만 간다

이는 support SLA가 없고 team API가 개인 DM에 의존하는 상태다.
service catalog와 team support page에 공식 intake lane이 노출되지 않으면, 실제 지원 계약은 항상 개인 평판이 된다.

### 시나리오 2: shared platform service에서 incident가 난다

누가 first responder고, 제품 팀은 언제 어디까지 도와야 하는지 escalation contract가 있어야 한다.
또한 platform on-call에서 product owner로 handoff될 때 transfer packet과 next update 책임이 끊기지 않아야 한다.

### 시나리오 3: sunset 기간 중 support가 끊긴다

replacement path는 열어뒀지만 support contract가 없으면 consumer migration이 실제로 늦어진다.
특히 final week에 temporary escalation owner와 support cut-off가 같이 없으면, producer와 consumer 모두 종료 시점을 믿지 못한다.

### 시나리오 4: 티켓은 여러 번 전달됐지만 누구도 owner가 아니다

handoff acceptance와 clock rule이 없는 상태다.
이 경우 "전달했다"는 기록은 있지만 support contract 관점에서는 아직 아무도 받은 적이 없는 것과 같다.

---

## 코드로 보기

```yaml
support_contract:
  service: contract-registry
  support_hours: business_hours
  request_profiles:
    normal_question:
      first_response: 2_business_days
      ownership_acceptance: 2_business_days
      next_update: 1_business_day
      owner: producer-team
    release_blocker:
      first_response: 30_minutes
      ownership_acceptance: 30_minutes
      mitigation_target: 4_hours
      escalate_after: 15_minutes_without_ack
      owner: producer-oncall
  escalation:
    sev1:
      declare_by:
        - consumer-oncall
        - producer-oncall
      primary: producer-oncall
      secondary_after: 10_minutes
      notify:
        - incident-commander
        - platform-sre
    sev2:
      primary: team-support-channel
  handoff:
    transfer_packet_required: true
    receiving_owner_must_ack: true
    sla_clock_resets: false
    old_owner_backup_until: "next update sent"
```

좋은 support contract는 요청 유형과 응답 기대치뿐 아니라, **clock과 escalation과 handoff 규칙**을 함께 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 암묵적 지원 | 초기엔 빠르다 | 사람 의존이 심해진다 | 아주 작은 팀 |
| single response SLA | 기대치 일부는 맞춰진다 | handoff와 update 공백이 생긴다 | 초기 formalization 단계 |
| clock bundle + escalation ladder | 현실적이다 | metadata 관리가 필요하다 | 여러 팀이 얽힌 시스템 |
| criticality-aware tiered contract | 가장 견고하다 | 설계와 훈련이 더 필요하다 | critical/shared service가 있을 때 |

support SLA와 escalation contract의 목적은 티켓 시스템을 만드는 것이 아니라, **도움을 요청하고 확대하고 넘기는 경로를 사람 대신 구조가 기억하게 만드는 것**이다.

---

## 꼬리질문

- 일반 문의와 incident escalation 경로가 분리돼 있는가?
- support hours와 response expectation이 catalog에서 보이는가?
- criticality가 높은 서비스에 느슨한 support 모델이 붙어 있지는 않은가?
- deprecation/migration 기간의 support cut-off가 정의돼 있는가?
- first response와 ownership acceptance와 next update clock이 분리돼 있는가?
- handoff 시 receiving owner acceptance와 clock reset rule이 있는가?

## 한 줄 정리

Support SLA and escalation contracts는 팀 간 지원과 확대 경로를 명시할 뿐 아니라, first response부터 handoff까지의 clock과 decision rights를 구조화해 개인 의존 지원 모델을 운영 계약으로 바꾸는 방식이다.
