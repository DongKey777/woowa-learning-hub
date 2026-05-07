---
schema_version: 3
title: Override Burn-Down Review Cadence and Scorecards
concept_id: software-engineering/override-burndown-scorecards
canonical: true
category: software-engineering
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- override
- scorecard
- burn-down
- governance
aliases:
- Override Burn-Down Review Cadence and Scorecards
- override review cadence
- override scorecard
- exemption review scorecard
- age bucket repeated owner exit blocker
- override debt review cadence
symptoms:
- override registry는 있지만 age bucket, repeated owner, same-policy concentration, blocked exit condition을 보는 scorecard와 review cadence가 없어 실제 burn-down이 안 돼
- override count는 줄었지만 manual path ratio, shadow candidate count, recurrence_after_closure가 그대로라 비공식 경로가 계속 살아 있어
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- software-engineering/override-burndown-exemption-debt
- software-engineering/manual-path-ratio-instrumentation
next_docs:
- software-engineering/shadow-process-detection-signals
- software-engineering/shadow-process-catalog-entry-schema
- software-engineering/platform-policy-override-governance
linked_paths:
- contents/software-engineering/override-burn-down-and-exemption-debt.md
- contents/software-engineering/platform-policy-ownership-override-governance.md
- contents/software-engineering/consumer-exception-state-machine-review-cadence.md
- contents/software-engineering/architecture-council-domain-stewardship-cadence.md
- contents/software-engineering/migration-stop-loss-scope-reduction-governance.md
- contents/software-engineering/manual-path-ratio-instrumentation.md
- contents/software-engineering/break-glass-path-segmentation.md
- contents/software-engineering/shadow-process-detection-signals.md
- contents/software-engineering/shadow-process-catalog-entry-schema.md
- contents/software-engineering/shadow-process-officialization-absorption-criteria.md
- contents/software-engineering/shadow-process-catalog-and-retirement.md
confusable_with:
- software-engineering/override-burndown-exemption-debt
- software-engineering/manual-path-ratio-instrumentation
- software-engineering/platform-scorecards
forbidden_neighbors: []
expected_queries:
- override burn-down scorecard에서 stock, flow, structure를 age bucket과 repeated owner로 어떻게 나눠 봐?
- weekly local review, monthly portfolio review, quarterly governance review는 각각 어떤 override 결정을 다뤄야 해?
- same-policy concentration과 blocked exit condition이 policy redesign이나 governance escalation 신호가 되는 이유가 뭐야?
- override 수는 줄었는데 manual_path_ratio가 그대로면 왜 shadow process retirement 실패로 봐야 해?
- shadow_candidate_count와 recurrence_after_closure를 override scorecard에 넣어야 하는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 override debt를 age bucket, repeated owner, same-policy concentration, blocked exit condition, manual path ratio로 보는 scorecard와 layered review cadence를 설계하는 advanced playbook이다.
---
# Override Burn-Down Review Cadence and Scorecards

> 한 줄 요약: override debt를 줄이려면 registry만 있어서는 부족하고, age bucket, repeated owner, blocked exit condition, same-policy concentration을 보는 scorecard와 정기 review cadence가 함께 있어야 실제 burn-down이 진행된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Architecture Council and Domain Stewardship Cadence](./architecture-council-domain-stewardship-cadence.md)
> - [Migration Stop-Loss and Scope Reduction Governance](./migration-stop-loss-scope-reduction-governance.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)

> retrieval-anchor-keywords:
> - override review cadence
> - override scorecard
> - exemption review
> - override debt review
> - age bucket
> - repeated owner score
> - exception scorecard
> - burn down cadence
> - exit blocker rate
> - shadow candidate count
> - manual path ratio
> - dm approval ratio
> - spreadsheet usage metric
> - retirement verification metric
> - break glass scorecard panel

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Override Burn-Down Review Cadence and Scorecards](./README.md#override-burn-down-review-cadence-and-scorecards)
> - 다음 단계: [Shadow Process Detection Signals](./shadow-process-detection-signals.md)

## 핵심 개념

override burn-down은 "정리하자"라고 말하는 것으로는 잘 안 된다.
숫자와 cadence가 있어야 한다.

보기 좋은 scorecard 축:

- age bucket
- type distribution
- repeated owner
- same-policy concentration
- blocked exit condition

즉 burn-down review는 느낌이 아니라 **예외 부채 포트폴리오의 정기 점검**이다.

---

## 깊이 들어가기

### 1. age bucket은 cleanup 우선순위를 빠르게 보여 준다

예:

- 0-30d
- 31-90d
- 91-180d
- 180d+

오래된 override가 항상 더 나쁜 것은 아니지만, 보통 review 우선순위를 잡는 데 가장 좋은 첫 신호다.

### 2. repeated owner와 same-policy concentration이 구조 문제를 드러낸다

특정 팀이나 특정 정책에 예외가 몰리면:

- policy scope가 나쁜지
- platform UX가 부족한지
- migration runway가 없는지

를 의심해야 한다.

즉 burn-down review는 개별 예외보다 **집중 패턴**을 보는 데 강하다.

### 3. blocked exit condition은 escalation queue로 올려야 한다

다음은 단순 "오래됨"보다 더 강한 위험 신호다.

- replacement path 부재
- owner 없음
- support contract 없음
- policy stage 변경 대기

blocked exception은 일반 backlog가 아니라 governance escalation item이다.

### 4. cadence는 forum layer와 맞춰야 한다

예:

- weekly local review: expiring/blocked exception
- monthly portfolio review: age bucket, repeated owner, same-policy trend
- quarterly governance review: policy redesign or migration reprioritization

이렇게 해야 cleanup과 구조 개선이 분리된다.

### 5. scorecard는 burn-down만이 아니라 reclassification에도 쓰여야 한다

일부 override는 닫는 것이 아니라:

- policy redesign
- permanent carve-out explicitization
- service stage 변경
- stop-loss decision

으로 가야 할 수 있다.

즉 scorecard는 deletion list보다 **decision input**에 가깝다.

### 6. scorecard는 stock, flow, structure를 분리해서 봐야 한다

override 총량만 보면 상태를 자주 잘못 읽는다.
보통은 세 층으로 나눠 봐야 한다.

- stock: 현재 살아 있는 override 수, age bucket, blocked exit condition 수
- flow: 이번 주/월 생성 수, 종료 수, 재오픈 수, 만료 후 미종료 수
- structure: same-policy concentration, repeated owner, ownerless ratio, manual path ratio

이렇게 봐야 "오래된 예외가 문제인지", "새 예외 유입이 더 큰 문제인지", "공식 경로가 현실을 못 담는지"를 분리할 수 있다.

### 7. shadow process 후보를 표시하는 지표가 필요하다

override burn-down이 건강해 보여도 실제로는 shadow process가 커질 수 있다.
다음 지표를 scorecard에 넣어 두면 그 징후를 빨리 본다.

- shadow_candidate_count: repeated manual path를 동반한 override 묶음 수
- manual_path_ratio: DM 승인, 수동 시트, 비공식 노션 링크에 기대는 예외 비율
- recurrence_after_closure: 닫은 뒤 같은 이유로 다시 열린 override 비율

이 지표를 실제로 계산하려면 message 수가 아니라 request 단위 fact와 grouping key가 필요하다.
계산식과 dedupe 규칙은 [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)을 기준으로 맞추는 편이 안정적이다.

이 지표들은 [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)의 `signal_evidence`와 `retirement_tracking.verification_metric`에 바로 연결돼야 scorecard와 catalog가 서로 끊기지 않는다.
다만 incident와 drill에서 허용된 break-glass는 같은 분모에 섞지 말고, [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)처럼 별도 visibility panel로 분리해야 normal `manual_path_ratio` 해석이 유지된다.

이 값이 올라가면 cleanup만으로는 부족하고, shadow process catalog와 officialization/absorption review로 넘겨야 한다.

### 8. review cadence마다 action bucket을 분리해야 한다

같은 forum에서 모든 예외를 처리하려 하면 local cleanup과 구조 수정이 서로 섞여 버린다.

- weekly local review: expires_at 임박, owner 없음, exit condition 갱신 필요
- monthly portfolio review: same-policy concentration, repeated owner, shadow candidate 확인
- quarterly governance review: policy redesign, absorb/officialize 결정, stop-loss 재조정

cadence는 숫자를 읽는 회의가 아니라, 어떤 종류의 결정을 어디서 내릴지 분리하는 장치다.

### 9. 좋은 scorecard는 count 감소보다 replacement 채택을 본다

override 수가 줄어도 같은 수동 경로가 계속 쓰이면 burn-down이 아니라 분산 hiding일 수 있다.
그래서 결과 지표에는 다음도 같이 보는 편이 좋다.

- replacement adoption rate
- manual path usage trend
- closed override의 재발률
- 공식 control plane 전환 후 예외 처리 lead time

즉 burn-down 성공은 "예외가 적어졌다"보다 "예외를 만들던 비공식 경로가 약해졌다"에 더 가깝다.

---

## 실전 시나리오

### 시나리오 1: override 수는 적은데 다 오래됐다

count만 보면 괜찮아 보여도 governance 건강은 나쁠 수 있다.

### 시나리오 2: 특정 정책의 override가 계속 늘어난다

burn-down issue가 아니라 policy redesign issue일 가능성이 높다.

### 시나리오 3: migration exemption이 blocked 상태로 많다

migration steering forum으로 escalation해야 한다.

### 시나리오 4: override 수는 줄었지만 DM 승인 비율은 그대로다

이 경우 scorecard는 겉으로는 좋아 보여도 shadow process retirement는 실패한 것이다.
burn-down 결과를 shadow candidate backlog와 함께 읽어야 한다.

---

## 코드로 보기

```yaml
override_scorecard:
  age_buckets:
    over_90d: 12
  flow:
    created_last_30d: 7
    closed_last_30d: 5
  repeated_owner:
    mobile-platform: 5
  same_policy:
    deprecated_api_override: 8
  blocked_exit_conditions: 4
  shadow_candidate_count: 3
  manual_path_ratio: 0.42
```

좋은 scorecard는 예외 수보다 cleanup이 막힌 패턴을 더 잘 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| registry only | 존재는 보인다 | 우선순위가 흐리다 | 초기 |
| scorecard review | 경향이 보인다 | 지표 설계가 필요하다 | 예외가 늘어날 때 |
| layered cadence + scorecard | 구조 문제까지 연결된다 | 운영 discipline이 필요하다 | 성숙한 governance 조직 |

override burn-down review cadence의 목적은 예외를 세는 것이 아니라, **어떤 예외가 왜 안 닫히는지와 어디에 구조 수정이 필요한지 보이게 만드는 것**이다.

---

## 꼬리질문

- 가장 많은 override를 가진 policy는 무엇인가?
- blocked exit condition이 있는 예외는 어느 forum으로 escalate되는가?
- scorecard가 cleanup과 redesign 결정을 모두 지원하는가?
- count 감소 뒤에 manual path ratio도 같이 내려가고 있는가?
- age만 보고 중요한 패턴을 놓치고 있지는 않은가?

## 한 줄 정리

Override burn-down review cadence and scorecards는 예외 부채를 age와 집중 패턴과 blocked 상태로 측정해, cleanup과 policy redesign을 더 체계적으로 진행하게 만드는 운영 구조다.
