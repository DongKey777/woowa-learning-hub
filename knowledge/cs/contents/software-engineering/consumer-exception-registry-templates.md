---
schema_version: 3
title: Consumer Exception Registry Templates
concept_id: software-engineering/consumer-exception-registry
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- consumer-exception
- registry-template
- deprecation-waiver
aliases:
- Consumer Exception Registry Templates
- consumer exception registry
- exception registry template
- lagging consumer registry
- waiver template
- allowlist template
- deprecation exemption registry
symptoms:
- lagging consumer, compatibility waiver, allowlist, deprecation exemption을 티켓/DM/스프레드시트에 흩어 두어 owner, expiry, exit condition이 추적되지 않아
- registry row, waiver request form, review packet, tombstone guidance가 서로 다른 필드명과 기준을 써 state machine과 automation이 연결되지 않아
- core fields와 type-specific fields를 나누지 않아 compatibility waiver, deprecation exemption, rollout exception을 같은 수준으로만 관리해
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/compatibility-waiver-governance
- software-engineering/consumer-migration-playbook
next_docs:
- software-engineering/consumer-exception-state-machine
- software-engineering/consumer-exception-registry-quality
- software-engineering/support-sla-escalation-contracts
linked_paths:
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
- contents/software-engineering/deprecation-enforcement-tombstone-guardrails.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/consumer-exception-operating-model.md
- contents/software-engineering/support-sla-escalation-contracts.md
- contents/software-engineering/support-contract-request-type-severity-matrix.md
- contents/software-engineering/consumer-exception-state-machine-review-cadence.md
- contents/software-engineering/consumer-exception-registry-quality-automation.md
confusable_with:
- software-engineering/compatibility-waiver-governance
- software-engineering/consumer-exception-state-machine
- software-engineering/consumer-exception-registry-quality
forbidden_neighbors: []
expected_queries:
- consumer exception registry template에는 consumer id, exception type, contract, owner, expires_at, exit condition, support contact가 왜 필요해?
- compatibility waiver, deprecation exemption, rollout exception은 core fields와 type-specific fields를 어떻게 나눠?
- registry row, waiver request form, review packet, tombstone guidance에 같은 필드를 반복 노출해야 하는 이유는 뭐야?
- allowlist-only tombstone 단계에서 어떤 consumer가 왜 남아 있는지 registry template로 어떻게 설명해?
- consumer exception registry가 예외를 정당화하는 문서가 아니라 종료 가능한 운영 기록이어야 하는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 lagging consumer, compatibility waiver, allowlist, deprecation exemption을 표준화된 consumer exception registry schema와 template로 관리하는 advanced playbook이다.
---
# Consumer Exception Registry Templates

> 한 줄 요약: lagging consumer, compatibility waiver, allowlist, deprecation exemption을 구두나 티켓에 흩어 두지 않으려면, consumer exception registry에 최소 필드와 상태와 종료 조건을 표준 템플릿으로 정리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Support Contract Request Type Severity Matrix](./support-contract-request-type-severity-matrix.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)

> retrieval-anchor-keywords:
> - consumer exception registry
> - exception registry template
> - lagging consumer registry
> - exception register row
> - waiver template
> - allowlist template
> - deprecation exemption
> - expires_at
> - exit condition
> - next review
> - support channel
> - waiver registry
> - consumer support registry
> - exception record

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Consumer Exception Registry Templates](./README.md#consumer-exception-registry-templates)
> - 다음 단계: [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)

## 핵심 개념

consumer exception은 대부분 "임시"로 시작하지만, 표준 기록이 없으면 permanent tribal knowledge가 된다.

registry 템플릿이 필요한 이유:

- 누가 예외 owner인지 분명히 하기 위해
- 어떤 consumer가 실제 blocker인지 보이게 하기 위해
- expiry와 exit condition을 강제하기 위해
- support contract와 escalation path를 연결하기 위해

즉 consumer exception registry는 예외를 정당화하는 문서가 아니라 **종료 가능한 운영 기록**이다.

---

## Template Insertion Points

registry template는 "한 번 쓰는 양식"이 아니라 여러 운영 지점에 같은 필드를 반복 노출해야 효과가 난다.

- registry row/schema: `owner`, `expires_at`, `exit_condition`, `support_contact` 같은 core field를 둔다.
- waiver / allowlist request form: 왜 예외가 필요한지와 대체 경로를 같은 필드명으로 받는다.
- review packet / governance agenda: `next_review_at`, blocked reason, escalation owner를 그대로 끌어온다.
- tombstone and support guidance: 남은 consumer를 설명할 때 registry id와 replacement path를 연결한다.

삽입 지점을 맞춰 두면 template, state machine, automation이 서로 다른 말을 하지 않는다.

---

## 깊이 들어가기

### 1. 기본 템플릿은 최소 필드가 있어야 한다

권장 필드:

- consumer id / team
- exception type
- affected contract or API
- created_at / expires_at
- owner
- current workaround
- exit condition
- support contact

이 정보가 빠지면 burn-down과 escalation이 모두 어려워진다.

### 2. type별 확장 필드를 두는 편이 좋다

예:

- compatibility waiver:
  old version / parser strictness / producer fallback
- deprecation exemption:
  replacement path / tombstone schedule / allowlist scope
- rollout exception:
  guardrail profile bypass / required manual checks

즉 registry는 one-size-fits-all보다 **core fields + type fields**가 현실적이다.

### 3. 상태(status)는 lifecycle을 보여 줘야 한다

예:

- proposed
- approved
- active
- expiring
- blocked
- closed

특히 expiring / blocked 상태가 보여야 governance forum에서 바로 다룰 수 있다.

### 4. registry는 support contract와 붙어 있어야 한다

consumer exception은 기술 이슈이면서 지원 이슈다.
그래서 다음도 함께 보이는 편이 좋다.

- support model
- escalation owner
- office hours / critical path
- final cut-off date

registry만 있고 지원 경로가 없으면 consumer는 예외를 해결할 방법을 모른다.

### 5. template는 automation-friendly해야 한다

future automation을 위해:

- enum-like field
- date field
- owner id
- contract id
- stage field

형태를 정규화해 두는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: mobile consumer가 deprecated endpoint를 계속 쓴다

단순 "모바일팀 아직 안 끝남"이 아니라, replacement path, owner, expires_at, support path가 registry에 보여야 한다.

### 시나리오 2: allowlist-only tombstone 단계가 복잡해진다

어떤 consumer가 왜 allowlist에 남아 있는지 template가 없으면 곧 혼란이 생긴다.

### 시나리오 3: migration exception review가 길어진다

type별 field가 없다면 compatibility waiver와 rollout exception을 같은 관점으로 보게 되어 governance 품질이 떨어진다.

---

## 코드로 보기

```yaml
consumer_exception:
  consumer: mobile-app-v5
  type: compatibility_waiver
  contract: order-status-v4
  owner: mobile-platform
  expires_at: 2026-10-01
  support_contact: "#mobile-api-support"
  exit_condition: release_v6_complete
```

좋은 template는 나중에 조회와 burn-down과 escalation이 가능해야 한다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 티켓 기반 임시 관리 | 시작은 쉽다 | 전체 상황이 안 보인다 | 초반 |
| 단일 registry template | 가시성이 높다 | type별 nuance가 부족할 수 있다 | 기본 모델 |
| core + type-specific template | 현실적이다 | 설계가 필요하다 | 성숙한 consumer governance |

consumer exception registry template의 목적은 문서를 늘리는 것이 아니라, **누가 왜 아직 old path에 남아 있는지와 언제 빠질지를 구조적으로 보이게 만드는 것**이다.

---

## 꼬리질문

- registry에 expires_at, exit_condition, support contact가 모두 있는가?
- compatibility waiver와 deprecation exemption을 같은 템플릿으로 무리하게 다루고 있지는 않은가?
- expiring/blocked consumer가 governance forum에서 바로 보이는가?
- registry가 burn-down과 support contract와 연결되는가?

## 한 줄 정리

Consumer exception registry templates는 lagging consumer와 waiver를 표준 필드와 상태와 종료 조건으로 관리해 예외를 숨은 기억이 아닌 운영 가능한 backlog로 바꾸는 구조다.
