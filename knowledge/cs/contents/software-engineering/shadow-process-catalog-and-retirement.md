# Shadow Process Catalog and Retirement

> 한 줄 요약: 공식 문서와 제어면 밖에서 돌아가는 shadow process는 단기 생존에는 유용할 수 있지만 장기적으로는 governance와 ownership을 잠식하므로, 어떤 비공식 운영 절차가 존재하는지 catalog로 드러내고 retire/absorb/officialize 경로를 정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Service Portfolio Lifecycle Governance](./service-portfolio-lifecycle-governance.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - shadow process
> - hidden workflow
> - unofficial operation
> - shadow process catalog
> - process retirement
> - workaround registry
> - operational dark matter
> - process cleanup
> - shadow retirement pipeline
> - shadow process scorecard
> - shadow catalog entry schema
> - shadow catalog state machine
> - shadow lifecycle scorecard metrics
> - shadow retirement proof metrics
> - temporary hold shadow entry
> - temporary hold exit criteria
> - blocked shadow process

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Process Catalog and Retirement](./README.md#shadow-process-catalog-and-retirement)
> - 다음 단계: [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)

## 핵심 개념

시스템에 공식 문서, policy, runbook이 있어도 실제 운영은 종종 다른 곳에서 돌아간다.

예:

- 특정 운영자만 아는 수동 승인 순서
- 슬랙 DM으로만 전달되는 배포 예외
- 문서에 없는 rollback 커맨드
- 임시 스프레드시트로 관리되는 deprecation allowlist

이런 shadow process는 단기 대응에는 도움 되지만, 장기적으로는 governance의 blind spot이 된다.

그래서 필요한 것이 shadow process catalog다.

---

## 깊이 들어가기

### 1. shadow process는 실패한 조직이 아니라 적응한 조직의 부산물이다

대부분의 shadow path는 누군가 게으르기 때문이 아니라, 공식 경로가 느리거나 부족해서 생긴다.

그래서 catalog의 목적은 비난이 아니라:

- 무엇이 공식 경로에서 빠졌는지
- 왜 우회가 생겼는지
- 어떤 위험이 있는지

를 드러내는 데 있다.

### 2. catalog에는 process identity가 필요하다

좋은 항목:

- process name
- current owner
- where it is used
- why it exists
- risk if unavailable
- official replacement candidate

실제 운영에서는 [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)처럼 `signal evidence`, `target state`, `review forum`, `retirement tracking`까지 같은 entry에 묶어 두는 편이 좋다.

이 정보가 없으면 shadow process는 "다들 아는 것"처럼 남다가 실제론 아무도 전체를 모르게 된다.

### 3. 모든 shadow process를 즉시 제거할 필요는 없다

분류가 중요하다.

- retire: 불필요하고 위험함
- absorb: 공식 control plane/runbook에 흡수
- officialize: 충분히 유효하므로 표준 절차로 승격
- temporary hold: migration 중이라 당장 필요

즉 catalog는 inventory이면서 동시에 **retirement pipeline**이다.
다만 `temporary_hold`는 terminal outcome이 아니라 pause이므로, review마다 실제로 expire할지, bounded extension을 할지, absorb/officialize로 escalation할지는 [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)처럼 별도 기준을 두는 편이 좋다.

### 4. incident와 exception은 shadow process를 잘 드러낸다

반복 incident 뒤에 자주 나오는 말:

- "원래는 A님에게 먼저 물어봐야 해요"
- "그 값은 수동으로 따로 관리합니다"
- "문서엔 없지만 실제론 이 순서로 해야 해요"

이런 패턴이 보이면 incident closure에서 shadow process catalog로 올려야 한다.

### 5. shadow process를 줄이는 가장 좋은 방법은 공식 경로를 더 쓰기 좋게 만드는 것이다

막연한 금지는 잘 안 먹힌다.
대개 필요한 것은:

- self-service 강화
- policy rollout 개선
- support SLA 명시
- tombstone/override registry 공식화

즉 shadow process retirement는 UX와 governance를 같이 개선하는 작업이다.

### 6. retirement pipeline은 detection에서 끝나지 않고 scorecard까지 이어져야 한다

shadow process retirement를 실제로 굴리려면 흐름이 끊기지 않아야 한다.

1. detection signal이 포착된다
2. catalog entry로 승격된다
3. retire / officialize / absorb / hold 중 target state를 정한다
4. override scorecard와 review cadence에 연결해 재발과 병행 사용을 본다

이 연결이 없으면 shadow process catalog는 inventory로 남고, officialization은 면책으로 오해되며, retirement는 선언으로 끝난다.
특히 "closed"와 "retired"를 섞지 않으려면 [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)처럼 hard gate와 verification window를 별도 문서로 고정해 두는 편이 좋다.
그리고 포트폴리오 수준에서 어느 `lifecycle_state`가 aging하는지, 어떤 hold가 만료됐는지, 어떤 verification이 stale한지는 [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)처럼 별도 scorecard 문서로 분리해 두는 편이 review forum action을 더 빠르게 만든다.

실무에서는 이 흐름을 [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)처럼 `detected -> cataloged -> decision_pending -> *_in_progress -> verification_pending -> retired`로 고정하고, `temporary_hold`와 `blocked`를 별도 전이로 관리하는 편이 좋다.
그래야 "무엇을 하기로 했는가"와 "왜 지금 안 움직이는가"를 분리해서 볼 수 있다.
또 `retired` 뒤 recurrence가 보였을 때 same-entry reopen으로 되돌릴지 successor entry를 만들지, 그리고 predecessor/history를 어떻게 남길지는 [Shadow Catalog Reopen and Successor Rules](./shadow-catalog-reopen-and-successor-rules.md)처럼 별도 기준으로 고정해 두는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: 배포 승인 예외가 슬랙 DM으로만 처리된다

이건 shadow approval process다.
platform policy override registry나 rollout contract로 공식화해야 한다.

### 시나리오 2: 특정 allowlist가 엑셀 파일에서만 관리된다

sunset enforcement의 blind spot이 될 수 있으므로 catalog에 올리고 control plane으로 흡수해야 한다.

### 시나리오 3: 운영자는 문서보다 내부 구두 절차를 더 신뢰한다

공식 runbook이 현실을 못 따라가는 신호다.
retire할 것이 아니라 runbook/playbook과 통합해야 한다.

---

## 코드로 보기

```yaml
shadow_process:
  name: manual_rollout_exception_slack_dm
  owner: release-manager
  risk: high
  target_state: absorb_into_override_registry
  review_at: 2026-09-15
```

좋은 catalog는 hidden workaround를 visible backlog로 바꾼다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| shadow process 방치 | 단기 유연성이 있다 | 장기 위험이 크다 | 피해야 한다 |
| catalog only | 가시화된다 | 실제 정리가 안 될 수 있다 | 첫 단계 |
| catalog + retirement path | 구조 개선으로 이어진다 | 운영 discipline이 필요하다 | 성숙 조직 |

shadow process catalog and retirement의 목적은 모든 우회를 처벌하는 것이 아니라, **비공식 운영 절차를 보이는 구조로 끌어올려 공식 경로를 더 현실적으로 만드는 것**이다.

---

## 꼬리질문

- 지금 운영에서 문서보다 더 자주 쓰이는 hidden process는 무엇인가?
- 이 shadow process는 retire, absorb, officialize 중 어디로 가야 하는가?
- detection signal과 override scorecard가 이 항목의 재발 여부를 보여 주는가?
- 왜 공식 경로가 이 과정을 흡수하지 못했는가?
- repeated incident나 override 뒤에 shadow process가 숨어 있지는 않은가?

## 한 줄 정리

Shadow process catalog and retirement는 비공식 운영 절차를 드러내고, retire/absorb/officialize 경로로 관리해 governance blind spot을 줄이는 운영 방식이다.
