---
schema_version: 3
title: Support Operating Models: Self-Service, Office Hours, On-Call
concept_id: software-engineering/support-operating-models
canonical: true
category: software-engineering
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- support-model
- office-hours
- on-call
- handoff
aliases:
- support operating model
- self service office hours on-call
- support lane handoff
- temporary surge support
- support mode selection
- 지원 운영 모델 선택
symptoms: []
intents:
- comparison
- design
- troubleshooting
prerequisites:
- software-engineering/support-sla-escalation-contracts
- software-engineering/support-contract-request-type-severity-matrix
next_docs:
- software-engineering/on-call-ownership-boundaries
- software-engineering/service-criticality-tiering
- software-engineering/change-ownership-handoff
linked_paths:
- contents/software-engineering/support-sla-escalation-contracts.md
- contents/software-engineering/support-contract-request-type-severity-matrix.md
- contents/software-engineering/change-ownership-handoff-boundaries.md
- contents/software-engineering/team-apis-interaction-modes-architecture.md
- contents/software-engineering/on-call-ownership-boundaries.md
- contents/software-engineering/service-criticality-tiering-control-intensity.md
confusable_with:
- software-engineering/support-contract-request-type-severity-matrix
- software-engineering/support-sla-escalation-contracts
- software-engineering/on-call-ownership-boundaries
forbidden_neighbors: []
expected_queries:
- self-service, office hours, business-hours support, on-call escalation은 request type과 service criticality에 따라 어떻게 고르면 돼?
- office hours가 migration이나 deprecation 질문을 묶어 처리하는 lane이지만 urgent blocker를 숨기면 안 되는 이유는?
- on-call lane은 active incident와 after-hours blocker에 집중하고 planned work 우회를 막으려면 어떤 entry condition이 필요해?
- temporary surge support profile은 대규모 migration cutover나 sunset 직전에 어떻게 시작일과 종료일을 둬야 해?
- support lane handoff에서 transfer packet, receiving owner acceptance, SLA clock reset 여부가 왜 중요해?
contextual_chunk_prefix: |
  이 문서는 self-service, office hours, business-hours support, on-call escalation, temporary surge lane을 request type, criticality, handoff rule 기준으로 고르는 advanced chooser이다.
---
# Support Operating Models: Self-Service, Office Hours, On-Call

> 한 줄 요약: 모든 지원을 같은 방식으로 처리하면 팀 피로와 대기 시간이 함께 커지므로, self-service, office hours, business-hours support, on-call escalation 같은 운영 모델을 request type과 service criticality에 따라 나눠 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Support Contract Request Type and Severity Matrix](./support-contract-request-type-severity-matrix.md)
> - [Change Ownership Handoff Boundaries](./change-ownership-handoff-boundaries.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [On-Call Ownership Boundaries](./on-call-ownership-boundaries.md)
> - [Service Criticality Tiering and Control Intensity](./service-criticality-tiering-control-intensity.md)

> retrieval-anchor-keywords:
> - support operating model
> - self service support
> - office hours support
> - business hours support
> - oncall support model
> - support tiering
> - support lane handoff
> - warm transfer
> - surge support model
> - support mode selection

## 핵심 개념

지원 운영 모델은 "문의 채널 몇 개를 둘까"가 아니라,
**어떤 요청이 어느 lane으로 들어와 누구 소유로 끝나며 언제 다른 lane으로 handoff되는가**를 정하는 설계다.

현실적으로는 다음 lane을 분리하는 편이 낫다.

- self-service
- office hours
- business-hours owned support
- on-call escalation
- temporary surge / cutover support

각 lane에는 최소한 다음이 세트로 붙어야 한다.

- entry condition
- owner
- response expectation
- exit condition
- handoff rule

즉 support contract는 SLA 숫자만이 아니라 **어떤 요청을 어떤 lane으로 보낼지와 lane 사이를 어떻게 넘길지를 정하는 운영 모델**이다.

---

## 깊이 들어가기

### 1. self-service는 가장 먼저 강화해야 하는 lane이다

self-service가 강하면 다음 부담이 줄어든다.

- 반복 질문
- 개인 DM
- low-severity support load
- onboarding friction

대표 수단:

- catalog
- docs
- FAQ
- templates
- control plane UI

하지만 self-service는 "사람이 안 도와준다"는 뜻이 아니다.
좋은 self-service lane은 다음을 함께 가진다.

- 검색 가능한 owner / support metadata
- 어떤 질문까지 self-service로 해결해야 하는지의 경계
- 실패 시 어느 assisted lane으로 넘어가는지의 기본 rule
- 반복 질문을 문서/자동화 backlog로 승격시키는 루프

같은 질문이 매주 office hours에 다시 나오면, 그건 consumer가 게으른 것이 아니라 self-service lane이 아직 약한 신호일 수 있다.

### 2. office hours는 migration/deprecation에 특히 잘 맞는다

항상 on-demand response가 필요하지는 않지만, 혼자 해결하기 어려운 설계형 질문에 유용하다.

예:

- migration clinic
- deprecation onboarding
- contract review slot
- complex onboarding Q&A

office hours는 support를 느리게 만드는 것이 아니라, **비슷한 질문을 묶어 처리하는 lane**이다.

대신 office hours를 잘 굴리려면 다음이 필요하다.

- 사전 질문 수집
- 재현 정보나 문맥을 미리 받는 intake form
- 세션 뒤 owner가 명시된 follow-up ticket
- office hours로 보낼 질문과 business-hours ticket로 보낼 질문의 경계

실패 패턴도 명확하다.

- 아무 준비 없이 "와서 물어보세요"만 남김
- 세션에서 답했지만 action owner가 남지 않음
- urgent blocker까지 office hours에 묶어 대기시킴

이 경우 office hours는 batching lane이 아니라 **queue hiding 장치**가 된다.

### 3. business-hours support와 on-call support는 경계가 달라야 한다

on-call은 active incident와 정말로 after-hours 대응이 필요한 blocker에 집중해야 한다.
평시 support가 on-call lane을 잠식하면 피로도가 빠르게 쌓이고, 진짜 incident가 왔을 때 품질이 떨어진다.

그래서 어떤 request type이 on-call로 갈 수 있는지 명시해야 한다.

예를 들면 다음 구분이 필요하다.

- 일반 문의: self-service 또는 business-hours
- migration blocker: 기본은 business-hours, 단 cutover window 동안만 임시 escalation 가능
- active sev incident: on-call
- policy / contract clarification: office hours 또는 business-hours

"금요일 밤 배포 직전이라 급하다"는 감정만으로 on-call로 보내기 시작하면, 실제로는 planned work를 pager lane으로 우회시키는 구조가 된다.

그래서 on-call 진입 조건에는 다음이 붙는 편이 좋다.

- 누가 severity를 올릴 수 있는가
- 어떤 evidence가 있어야 하는가
- on-call이 받지 않는 요청 유형은 무엇인가
- on-call 이후 business-hours owner에게 어떻게 넘기는가

### 4. service criticality와 lifecycle stage가 모델 선택에 영향을 준다

같은 팀이라도 서비스 성격에 따라 lane 구성이 달라진다.

예:

- internal beta / temporary service: self-service + explicit low-support statement
- shared platform critical service: self-service + business-hours + on-call
- tiered runtime dependency: severity matrix + clear escalation ladder
- deprecated service: migration office hours + sunset support cut-off + final escalation owner
- ownership handoff 중인 서비스: 공동 운영 기간 + transfer-specific support alias

같은 support contract라도 operating model은 다를 수 있다.

### 5. 모델 전환 기준도 있어야 한다

office-hours 모델에서 on-call 모델로 올려야 하는 시점:

- critical path 편입
- sev incident frequency 증가
- shared dependency centrality 증가

반대로 support intensity를 낮춰야 하는 시점도 있다.

또한 steady-state 모델과 별개로 **temporary surge profile**을 두는 편이 현실적인 경우가 많다.

- 대규모 migration cutover 주간
- sunset 직전 consumer 문의 급증 구간
- 신규 launch 직후
- ownership handoff 공동 운영 구간

이때는 일시적으로 다음을 추가할 수 있다.

- extended office hours
- temporary support alias
- dedicated escalation owner
- daily triage checkpoint

중요한 것은 이 임시 모델에 시작일과 종료일이 있어야 한다는 점이다.
종료 조건이 없으면 temporary lane이 상시 운영 debt로 굳는다.

### 6. lane 사이 handoff rule이 없으면 지원 구조가 개인 의존으로 돌아간다

좋은 lane 설계는 "어디로 보낸다"보다 "어떻게 넘긴 뒤 ownership을 확정하느냐"를 더 분명히 한다.

대표적인 handoff는 다음과 같다.

- self-service 실패 -> business-hours owned support
- office hours action item -> named ticket owner
- on-call mitigation 완료 -> next business-hours owner
- temporary surge desk -> steady-state support lane

각 handoff에는 최소한 다음이 필요하다.

- transfer packet: 요약, impact, 재현 정보, 관련 링크
- receiving owner acceptance
- SLA clock reset 여부
- next update 약속

anti-pattern도 자주 반복된다.

- 개인 DM으로 우회하는 shadow lane
- office hours에서 action owner 없이 끝나는 cold handoff
- on-call이 낮 시간 질문을 계속 붙잡아 owning team이 사라지는 구조
- lane을 옮길 때마다 "처음부터 설명해 주세요"가 반복되는 ping-pong

이런 패턴은 support tooling 문제가 아니라 **lane contract 부재** 문제다.

### 7. 운영 모델은 volume보다 misroute와 handoff 품질로 측정해야 한다

좋은 지표는 다음에 가깝다.

- lane misroute rate
- self-service bounce-back ratio
- office-hours 질문의 follow-up ticket completion rate
- on-call non-incident ratio
- handoff acceptance latency
- repeated question recurrence

문의 건수만 보면 "바쁘다"는 사실만 알 수 있다.
어느 lane이 잘못 설계됐는지는 misroute와 handoff 품질 지표가 더 잘 보여 준다.

---

## 실전 시나리오

### 시나리오 1: platform 서비스 문의가 전부 긴급처럼 온다

request type 구분과 self-service lane이 약한 상태다.
team support page에 severity 경계와 entry lane을 명시하지 않으면 on-call과 개인 DM이 shadow queue가 된다.

### 시나리오 2: deprecation 기간 중 문의가 많다

on-call보다 weekly office hours, temporary migration alias, support matrix를 붙이는 편이 더 현실적일 수 있다.
대신 cutover 주간에만 한시적으로 escalation profile을 높이고, 종료일을 명확히 둬야 한다.

### 시나리오 3: low-criticality tool에 24/7 support를 붙여놨다

과잉 지원 모델일 수 있다.
운영 강도는 서비스 중요도와 동일해야지, 요청자의 목소리 크기와 동일하면 안 된다.

### 시나리오 4: ownership handoff 이후 예전 팀 DM이 계속 온다

support alias, catalog, office hours owner, on-call escalation이 함께 바뀌지 않은 상태다.
이때는 새 팀 교육보다 **old lane retire + new lane publish**가 먼저다.

---

## 코드로 보기

```yaml
support_operating_model:
  service: contract-registry
  lanes:
    self_service:
      entry: "known question / documented workflow"
      owner: platform-docs
      exit: "consumer resolves without human intervention"
    office_hours:
      entry: "migration clinic / contract review"
      cadence: weekly
      prework_required: true
      fallback_handoff: "owned follow-up ticket"
    business_hours:
      entry: "named consumer blocker during support hours"
      first_response_sla: 4_business_hours
      owner: producer-team
    oncall:
      entry: "sev1 or approved after-hours cutover blocker"
      owner: producer-oncall
      forbidden_types:
        - general_question
        - planned_migration_help
  handoff_rules:
    office_hours_to_ticket:
      receiving_owner_must_ack: true
      sla_clock_resets: false
    oncall_to_business_hours:
      transfer_packet_required: true
      next_update_required: true
```

좋은 지원 모델은 요청을 같은 큐에 넣지 않고 lane을 분리할 뿐 아니라, **lane 사이 transfer contract까지 명시**한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| single support lane | 단순하다 | 피로와 지연이 같이 생긴다 | 아주 작은 팀 |
| lane-based support model | 현실적이다 | 설계가 필요하다 | 다양한 요청 유형이 있을 때 |
| criticality-aware lane model | 효율이 높다 | 운영 discipline이 필요하다 | shared/critical service |
| temporary surge profile | cutover에 강하다 | 상시화되면 피로가 커진다 | launch/migration/sunset 주간 |

support operating model의 목적은 더 많은 support를 제공하는 것이 아니라, **맞는 요청을 맞는 lane으로 보내고 handoff 손실을 줄여 피로와 대기 시간을 함께 낮추는 것**이다.

---

## 꼬리질문

- self-service로 흘러가야 할 요청이 사람 지원 lane에 묶여 있지는 않은가?
- office hours가 더 맞는 주제를 on-call로 처리하고 있지는 않은가?
- criticality/stage에 따라 support model이 실제로 달라지는가?
- lane 간 handoff rule이 명시돼 있는가?
- temporary surge lane에 종료 조건이 있는가?
- on-call에서 business-hours로 넘길 때 clock과 owner가 끊기지 않는가?

## 한 줄 정리

Support operating models: self-service, office hours, on-call은 지원 계약을 하나의 SLA가 아니라 여러 lane과 handoff contract의 조합으로 보고, 서비스 특성과 요청 유형에 맞는 운영 구조를 설계하는 관점이다.
