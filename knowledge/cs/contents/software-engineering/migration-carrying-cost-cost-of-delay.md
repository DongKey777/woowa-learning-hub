---
schema_version: 3
title: Migration Carrying Cost and Cost of Delay
concept_id: software-engineering/migration-carrying-cost-delay
canonical: true
category: software-engineering
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- migration
- cost-of-delay
- carrying-cost
- modernization
aliases:
- Migration Carrying Cost and Cost of Delay
- migration carrying cost
- cost of delay migration
- dual-run cost legacy tax
- modernization carrying cost
- transition tax economics
symptoms:
- migration 구현 비용만 비교하고 dual-run infra, legacy on-call, roadmap drag, support burden처럼 미루는 동안 누적되는 비용을 계산하지 않아
- lagging consumer나 repeated exception 때문에 dual-run이 계속되는데 유지 1개월의 carrying cost와 wave별 절감 효과를 숫자로 보지 않아
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- software-engineering/migration-funding-model
- software-engineering/architectural-debt-interest
next_docs:
- software-engineering/migration-stop-loss-governance
- software-engineering/migration-wave-governance
- software-engineering/build-vs-buy-governance
linked_paths:
- contents/software-engineering/migration-funding-model.md
- contents/software-engineering/migration-wave-governance-decision-rights.md
- contents/software-engineering/architectural-debt-interest-model.md
- contents/software-engineering/consumer-migration-playbook-contract-adoption.md
- contents/software-engineering/build-vs-buy-exit-cost-governance.md
- contents/software-engineering/migration-stop-loss-scope-reduction-governance.md
- contents/software-engineering/migration-scorecards.md
confusable_with:
- software-engineering/migration-funding-model
- software-engineering/migration-stop-loss-governance
- software-engineering/architectural-debt-interest
forbidden_neighbors: []
expected_queries:
- migration carrying cost와 cost of delay를 dual-run, legacy tax, roadmap drag 관점에서 계산하는 방법을 알려줘
- 전환을 미루는 비용이 단순 구현 비용보다 의사결정에 더 중요한 이유는 뭐야?
- lagging consumer 한 팀 때문에 dual-run을 3개월 더 유지할 가치가 있는지 어떻게 판단해?
- migration wave가 끝날 때 carrying cost가 실제로 얼마나 줄었는지 어떤 항목으로 봐야 해?
- migration economics를 product roadmap flexibility와 incident reduction까지 포함해 설명해줘
contextual_chunk_prefix: |
  이 문서는 migration을 미룰 때 누적되는 dual-run, legacy tax, roadmap drag, cost of delay를 wave decision과 stop-loss 판단에 연결하는 advanced bridge이다.
---
# Migration Carrying Cost and Cost of Delay

> 한 줄 요약: migration economics의 핵심은 "얼마 들까"보다, 지금 전환하지 않을 때 legacy와 dual-run과 org drag가 매주 얼마씩 비용을 쌓는지 보이는 carrying cost와 cost of delay를 계산하는 것이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Software Engineering README: Migration Carrying Cost and Cost of Delay](./README.md#migration-carrying-cost-and-cost-of-delay)
> - [Migration Funding Model](./migration-funding-model.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)
> - [Architectural Debt Interest Model](./architectural-debt-interest-model.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Build vs Buy, Exit Cost, Integration Governance](./build-vs-buy-exit-cost-governance.md)
> - [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md)

> retrieval-anchor-keywords:
> - migration carrying cost
> - cost of delay
> - dual-run cost
> - legacy tax
> - transition tax
> - migration economics
> - postponement cost
> - modernization carrying cost
> - migration stop loss
> - scope reduction economics

## 핵심 개념

migration을 시작할 때는 보통 구현 비용만 계산하기 쉽다.
하지만 실제 의사결정에서 더 중요한 것은 "미루면 얼마가 쌓이는가"다.

미루는 비용 예:

- dual-run infra 비용
- 레거시 장애 대응 비용
- 전환 전담 인력의 context switching
- 표준 밖 스택 유지 비용
- product roadmap 제약

즉 migration economics는 CAPEX처럼 한 번 드는 돈이 아니라, **미루는 동안 계속 붙는 carrying cost**를 함께 봐야 한다.

---

## 깊이 들어가기

### 1. carrying cost는 눈에 잘 안 보이게 흩어진다

이 비용은 한 항목으로 안 잡히고 여러 팀에 퍼진다.

예:

- platform 팀은 두 가지 배포 경로를 유지
- 제품 팀은 신규 기능을 옛 계약과 새 계약 둘 다 맞춤
- 운영 팀은 두 시스템의 대시보드와 온콜 경계를 함께 봄
- finance는 vendor와 self-hosted 비용을 동시에 냄

그래서 migration이 길어질수록 조직 전체가 조금씩 느려진다.

### 2. cost of delay는 기술 부채의 시간 축이다

지금 안 하는 비용은 단순히 "나중에 더 오래 걸린다"가 아니다.

예:

- 팀 구조가 더 굳어짐
- 소비자 수가 늘어 migration 대상이 더 커짐
- hold/retire 기술의 인력 수급이 더 나빠짐
- 데이터 volume이 커져 backfill 난이도가 올라감

즉 지연은 선형이 아니라 종종 **복리처럼 커지는 리스크**를 만든다.

### 3. 모든 migration이 끝까지 갈 가치가 있는 것은 아니다

carrying cost를 계산하면 오히려 멈춰야 할 전환도 보인다.

예:

- business value가 낮고 소비자 수도 적다
- replacement가 operationally 더 복잡하다
- migration wave마다 exception만 늘어난다

좋은 economics review는 "계속할 것인가"뿐 아니라 **중단하거나 scope를 줄일 것인가**도 묻는다.

### 4. economics는 wave decision과 연결돼야 한다

큰 전환은 한 번 판단하고 끝나지 않는다.
wave마다 다시 봐야 한다.

질문 예:

- 이번 wave 이후 carrying cost가 실제로 얼마나 줄어드는가
- lagging consumer 한 팀 때문에 dual-run을 3개월 더 유지할 가치가 있는가
- deprecation deadline을 연장하면 어떤 비용이 새로 생기는가

숫자를 봐야 politics보다 economics로 대화할 수 있다.

### 5. migration economics는 product roadmap과 같이 봐야 한다

전환 비용을 기술팀 내부 비용으로만 보면 계속 밀린다.
하지만 실제로는 roadmap flexibility도 경제성이다.

예:

- 신규 기능 출시 lead time 감소
- 규제 대응 속도 개선
- incident reduction에 따른 support 비용 감소
- onboarding 속도 증가

즉 migration ROI는 "새 기능 하나"보다 **변화 가능성 자체의 가치**를 포함해야 한다.

---

## 실전 시나리오

### 시나리오 1: dual-run이 6개월째 계속된다

기술적으로는 안전해 보여도, 인프라와 운영과 cognitive load 비용이 계속 쌓인다.
이럴 때는 "더 안전하니까 유지"보다, 유지 1개월의 carrying cost를 숫자로 봐야 한다.

### 시나리오 2: hold 상태 기술을 계속 유지한다

표준 밖 기술을 쓰는 서비스가 적더라도, 담당자 이탈과 보안 패치 지연이 cost of delay를 키울 수 있다.

### 시나리오 3: migration scope가 너무 넓다

전체 전환보다 일부 capability만 옮기는 편이 carrying cost 대비 효과가 더 좋을 수도 있다.

---

## 코드로 보기

```yaml
migration_economics:
  legacy_tax_per_month:
    infra: 1200
    oncall: 800
    dual_run_ops: 1500
    roadmap_drag: 2000
  cost_of_delay_per_month: 5500
  wave_review:
    reduce_if_wave_3_complete: 3200
```

좋은 경제성 평가는 build cost뿐 아니라 delay cost를 같이 적는다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 구현 비용만 비교 | 계산이 쉽다 | 미루는 비용을 놓친다 | 작은 변경 |
| carrying cost 포함 | 현실적이다 | 추정이 필요하다 | 장기 migration |
| wave별 economics review | 지속 판단이 가능하다 | 운영 discipline이 필요하다 | 여러 팀이 얽힌 전환 |

migration carrying cost를 보면 전환은 취향이나 열정의 문제가 아니라, **계속 끌수록 조직 전체가 얼마나 느려지는지의 경제 문제**가 된다.

---

## 꼬리질문

- 이 migration을 미룰 때 한 달에 실제로 얼마가 추가로 드는가?
- dual-run 연장의 비용은 누구에게 분산되고 있는가?
- wave를 마칠 때 carrying cost가 얼마나 줄어드는가?
- 계속하는 것과 scope를 줄이는 것 중 어느 쪽이 경제적으로 더 타당한가?

## 한 줄 정리

Migration carrying cost and cost of delay는 전환 비용만이 아니라 미루는 동안 누적되는 legacy tax와 dual-run drag를 수치화해 migration 우선순위를 더 현실적으로 만드는 관점이다.
