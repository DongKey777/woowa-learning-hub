---
schema_version: 3
title: Backward Compatibility Test Gates
concept_id: software-engineering/backward-compatibility-gates
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 91
mission_ids:
- missions/payment
review_feedback_tags:
- backward-compatibility
- release-gate
- consumer-contract
aliases:
- Backward Compatibility Test Gates
- backward compatibility gate
- compatibility release gate
- provider consumer compatibility matrix
- semantic compatibility gate
- 호환성 테스트 게이트
symptoms:
- backward compatibility를 문서상 약속으로만 두고 PR, CI, release 단계에서 실제 gate로 막지 않아
- schema parse 가능성만 보고 enum 의미 변경, default value, strict parser 같은 semantic compatibility 문제를 놓쳐
- consumer matrix와 rollback/feature-flag 대응 없이 compatibility failure를 단순 테스트 실패로만 처리해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- software-engineering/api-contract-testing
- software-engineering/schema-contract-evolution-cross-service
next_docs:
- software-engineering/compatibility-waiver-governance
- software-engineering/consumer-migration-playbook
- software-engineering/contract-drift-governance
linked_paths:
- contents/software-engineering/schema-contract-evolution-cross-service.md
- contents/software-engineering/event-schema-versioning-compatibility.md
- contents/software-engineering/architectural-fitness-functions.md
- contents/software-engineering/api-contract-testing-consumer-driven.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/contract-drift-detection-rollout-governance.md
- contents/software-engineering/backward-compatibility-waiver-consumer-exception-governance.md
confusable_with:
- software-engineering/api-contract-testing
- software-engineering/schema-contract-evolution-cross-service
- software-engineering/compatibility-waiver-governance
forbidden_neighbors: []
expected_queries:
- backward compatibility test gate는 contract test와 schema compatibility check를 release policy로 어떻게 강제해?
- PR CI release 단계에 각각 어떤 compatibility gate를 두면 좋아?
- 형식상 parse는 되지만 enum 의미나 default value 때문에 semantic compatibility가 깨지는 사례를 알려줘
- consumer matrix에는 consumer version parser strictness last successful contract 같은 정보를 왜 넣어야 해?
- compatibility gate 실패 시 rollback feature flag old schema migration pause를 어떻게 연결해?
contextual_chunk_prefix: |
  이 문서는 backward compatibility test gate를 provider contract, schema check, replay compatibility, semantic rule, consumer matrix, release gate와 연결하는 advanced playbook이다.
---
# Backward Compatibility Test Gates

> 한 줄 요약: backward compatibility test gate는 새 코드가 이전 소비자와 계약을 깨지 않는지를 배포 전에 강제하는 안전선이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Schema Contract Evolution Across Services](./schema-contract-evolution-cross-service.md)
> - [Event Schema Versioning and Compatibility](./event-schema-versioning-compatibility.md)
> - [Architectural Fitness Functions](./architectural-fitness-functions.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Contract Drift Detection and Rollout Governance](./contract-drift-detection-rollout-governance.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)

> retrieval-anchor-keywords:
> - backward compatibility
> - compatibility gate
> - contract gate
> - provider test
> - consumer test
> - release gate
> - regression guard
> - semantic compatibility
> - consumer matrix
> - runtime drift signal
> - compatibility waiver
> - lagging consumer

## 핵심 개념

backward compatibility는 문서로 선언하는 것만으로는 부족하다.
실제로 배포 전에 검증해야 한다.

compatibility gate는 다음을 보장한다.

- 새 producer가 옛 consumer를 깨지 않는다
- 새 schema가 이전 parser에서 버틸 수 있다
- API 응답 변화가 기존 기대를 뒤엎지 않는다

즉 gate는 호환성의 **실행 버전**이다.

---

## 깊이 들어가기

### 1. gate는 테스트 모음이 아니라 release policy다

compatibility test가 통과하지 않으면 배포를 멈춰야 한다.

그래서 gate에는 다음이 포함된다.

- provider contract test
- schema compatibility check
- replay compatibility check
- breaking change detection

### 2. 형식 호환성과 의미 호환성을 같이 봐야 한다

형식이 맞아도 의미가 깨질 수 있다.

예:

- 필드는 존재하지만 기본값이 잘못됨
- enum은 유효하지만 이전 소비자가 의미를 오해함
- optional 추가인데 downstream business rule이 깨짐

그래서 gate는 parse 가능성뿐 아니라 semantic compatibility도 본다.

### 3. gate는 CI와 release pipeline 모두에 있어야 한다

좋은 위치:

- PR 단계: 빠른 contract/smoke gate
- CI 단계: 전체 compatibility matrix
- release 단계: canary 후 최종 확인

한 곳에만 두면 누락이 생긴다.

### 4. consumer matrix가 필요하다

모든 소비자를 동일하게 볼 수 없다.

matrix에는 다음이 들어가야 한다.

- consumer 이름
- 버전
- last successful contract
- supported fields
- parser strictness

이 정보가 있어야 gate가 현실적이다.

### 5. gate 실패는 즉시 복구 경로와 연결되어야 한다

호환성 실패는 단지 에러가 아니다.

대응:

- rollback
- feature flag off
- old schema 유지
- migration pause

즉 gate는 막는 역할뿐 아니라, **안전한 대체 경로를 안내**해야 한다.

---

## 실전 시나리오

### 시나리오 1: 새 필드 추가 후 소비자 파손

필드가 optional이어도 일부 소비자가 strict parser라면 실패할 수 있다.
gate는 이 consumer를 잡아내야 한다.

### 시나리오 2: 이벤트 replay가 실패한다

과거 payload를 다시 읽을 수 있어야 하므로, replay compatibility를 별도 gate로 둔다.

### 시나리오 3: contract test는 통과했는데 운영에서 깨진다

이 경우 semantic gap를 의미한다.
형식 테스트만이 아니라 business-invariant gate가 필요하다.

---

## 코드로 보기

```yaml
compatibility_gate:
  provider_contract: pass
  schema_check: pass
  replay_check: pass
  semantic_rules: pass
```

gate는 체크리스트가 아니라 release의 통과 조건이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 문서만 호환성 선언 | 쉽다 | 깨지기 쉽다 | 아주 작은 시스템 |
| 테스트만 호환성 확인 | 자동화된다 | 정책이 약하다 | 단일 소비자 |
| compatibility gate | 안전하다 | 파이프라인이 복잡하다 | 여러 소비자와 버전이 있을 때 |

backward compatibility는 "할 수 있으면 좋다"가 아니라, **배포 전에 증명해야 하는 조건**이다.

---

## 꼬리질문

- 어떤 호환성 검사를 PR에서, 어떤 검사를 release에서 할 것인가?
- semantic compatibility는 어떻게 정의할 것인가?
- consumer matrix는 최신인가?
- gate 실패 시 누가 복구 결정을 내리는가?

## 한 줄 정리

Backward compatibility test gates는 새 변경이 기존 소비자와 계약을 깨지 않는지를 release 전에 자동으로 증명하는 안전 장치다.
