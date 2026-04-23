# Shadow Process Officialization and Absorption Criteria

> 한 줄 요약: shadow process를 발견했다고 모두 없애야 하는 것은 아니며, 실제로 가치가 있는 경로는 officialize 또는 control plane/runbook으로 absorb하고, 위험만 큰 경로는 retire하는 기준이 있어야 shadow catalog가 cleanup으로 이어진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Process Detection Signals](./shadow-process-detection-signals.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Platform Control Plane and Delegation Boundaries](./platform-control-plane-delegation-boundaries.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md)
> - [Consumer Exception Operating Model](./consumer-exception-operating-model.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - shadow process officialization
> - process absorption
> - officialize workaround
> - absorb into control plane
> - retire shadow process
> - workaround criteria
> - process promotion
> - shadow process decision
> - officialization threshold
> - control plane fit
> - shadow retirement gate
> - target state review forum
> - retire vs absorb vs officialize
> - rollout exception decision
> - deprecation waiver retirement
> - migration cutover runbook officialize
> - retirement exit criteria examples
> - shadow catalog state machine
> - temporary hold exit criteria
> - hold escalate absorb officialize

## 핵심 개념

shadow process를 발견하면 보통 instinct는 "없애자"다.
하지만 어떤 shadow path는 실제로 유효한 운영 요구를 드러낸다.

그래서 가능한 다음 상태를 구분해야 한다.

- retire
- officialize
- absorb
- temporary hold

즉 shadow process governance의 핵심은 발견보다 **다음 상태 결정 기준**이다.

---

## 깊이 들어가기

### 1. officialize와 absorb는 다르다

- officialize: 현재 과정을 공식 문서/운영 절차로 승격
- absorb: 기존 공식 control plane/runbook/tool에 통합

예:

- useful office-hour triage ritual -> official support process
- manual override spreadsheet -> absorb into override registry

### 2. 가치와 위험을 같이 봐야 한다

평가 질문:

- 이 과정은 실제로 반복 가치가 있는가
- single person dependency가 큰가
- auditability가 필요한가
- 공식 경로가 왜 못 담고 있는가
- 자동화/템플릿화가 가능한가

즉 useful-but-unofficial과 unsafe-and-unofficial을 구분해야 한다.

### 3. absorb 후보는 보통 control plane 또는 catalog deficiency를 드러낸다

다음 shadow path는 absorb 대상일 가능성이 높다.

- 수동 allowlist
- 비공식 metadata list
- 개인 노트에 있는 rollout 예외
- ad-hoc migration tracking sheet

이는 "하지 말자"보다, 공식 시스템이 빠진 기능을 보강해야 한다는 신호다.

### 4. officialize는 support contract와 owner가 있어야 한다

비공식 프로세스를 공식 절차로 승격할 때는:

- owner
- SLA
- entry/exit criteria
- runbook or playbook
- training path

가 함께 와야 한다. 아니면 다시 tribal process가 된다.

### 5. retirement는 shadow process를 없애는 것이 아니라 기능을 대체하는 일이다

retire하려면:

- replacement path
- communication
- cutoff date
- fallback if replacement fails

가 필요하다. 그렇지 않으면 같은 shadow path가 다른 이름으로 다시 생긴다.

### 6. state 결정 전에 적합성 테스트를 돌려야 한다

officialize/absorb/retire를 직감으로 고르면 대부분 문서만 늘거나, 반대로 필요한 프로세스를 억지로 지워 버린다.
판단 전에 최소 세 가지 적합성 테스트를 보는 편이 좋다.

- repeatability test: 다른 사람이 같은 입력으로 같은 절차를 재현할 수 있는가
- control test: audit trail, approval record, owner traceability가 필요한가
- structure fit test: 이 과정의 핵심이 structured data/decision인가, 아니면 사람 판단/훈련인가

보통 structured data와 반복 예외가 핵심이면 absorb가 맞고, 판단 순서와 역할 분담이 핵심이면 officialize 쪽이 맞다.
반대로 가치가 낮고 위험만 크면 retire가 맞다.

### 7. officialize, absorb, retire, hold를 나누는 판정표가 필요하다

| 관찰된 패턴 | 더 맞는 다음 상태 | 이유 | 같이 붙여야 할 guardrail |
|---|---|---|---|
| 반복적이고 데이터가 구조화돼 있다 | absorb | control plane/registry로 옮기기 쉽다 | schema, owner, audit log |
| 드물지만 고위험이며 사람 판단 순서가 중요하다 | officialize | runbook/playbook/SLA가 핵심이다 | owner, training path, drill |
| 가치가 낮고 우회 비용이 더 크다 | retire | replacement가 더 안전하다 | cutoff date, communication |
| migration 중 잠깐 필요하다 | temporary hold | 즉시 제거 시 delivery가 막힌다 | expires_at, exit condition |

실무에서는 이 판정 결과를 [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)의 `target_state`, `review`, `retirement_tracking` 필드에 바로 반영해 decision과 follow-up을 끊지 않는 편이 좋다.
또한 decision이 났다고 entry가 곧바로 끝나는 것은 아니므로, 실제 운영 상태는 [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)처럼 `decision_pending`, `*_in_progress`, `temporary_hold`, `blocked`, `verification_pending`으로 따로 추적해야 한다.
특히 `temporary_hold`는 "일단 보류"로 끝내면 거의 항상 장기 정체로 흐르므로, hold 종료, bounded extension, absorb/officialize escalation의 concrete example은 [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)처럼 별도 문서로 고정해 두는 편이 좋다.

좋은 판단은 "이 과정이 존재해도 되는가"보다 "어떤 통제 장치 아래에 두어야 하는가"를 먼저 묻는다.

### 8. officialization은 면책이 아니라 burn-down 계획을 요구한다

shadow process를 officialize했다고 해서 영구 면책을 준 것은 아니다.
특히 repeated override와 같이 예외 부채를 동반한 경로라면 다음을 같이 정의해야 한다.

- 왜 이 경로가 필요한지에 대한 explicit scope
- 어떤 조건이 되면 absorb 또는 retire로 이동하는지
- 어떤 scorecard로 수동 사용량과 override concentration을 줄일지
- owner forum이 언제 구조 문제로 escalation할지

즉 officialize는 "이 경로를 인정한다"가 아니라, "지금은 필요하지만 관리 가능한 형태로 올리고 다음 전환까지 추적한다"에 가깝다.

### 9. worked example로 보면 판정 기준이 더 선명해진다

판정표만 보면 세 상태가 모두 그럴듯해 보여 헷갈리기 쉽다.
그래서 rollout, deprecation, migration에서 자주 나오는 사례를 "왜 이 상태가 맞고 다른 상태는 아닌지"까지 같이 본다.

#### 예시 A. rollout 중 수동 예외 스프레드시트가 계속 쓰인다 -> absorb

상황:

- release manager가 서비스별 canary 배치 크기, 모니터 mute 예외, 수동 resume 사유를 스프레드시트로 관리한다
- 배포마다 같은 컬럼을 채우고, 여러 팀이 같은 시트를 참조한다
- 감사 시점에는 누가 왜 예외를 넣었는지 재구성하기 어렵다

판정:

- **absorb**가 맞다

왜 absorb인가:

- 핵심 자산이 사람의 암묵지보다 **반복되는 구조화 데이터**다
- 이미 [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)와 rollout control plane이 있는 상황이라, 빠진 것은 예외 필드와 audit trail이다
- officialize로 문서만 승격하면 스프레드시트라는 off-plane 상태 저장소가 그대로 남는다
- retire를 선택하면 실제 배포 예외 수요를 못 담아 또 다른 비공식 시트가 생긴다

exit criteria:

- rollout control plane에 예외 사유, 만료일, 승인자 필드가 생긴다
- `manual_sheet_usage_ratio`가 2개 연속 release cycle 동안 0에 가깝다
- pause/resume 이력과 예외 사유가 공식 audit log에서 조회된다

#### 예시 B. deprecation 연장 승인이 슬랙 DM으로만 처리된다 -> retire

상황:

- 종료 예정 API의 소비자들이 마감 연장을 슬랙 DM으로 요청한다
- PM/운영자 개인 메시지에 "이번 분기까지만 봐주자" 같은 약속이 흩어져 있다
- 이미 deprecation notice, exception registry, sunset policy는 존재한다

판정:

- **retire**가 맞다

왜 retire인가:

- 공식 대체 경로가 이미 있는데, DM은 그 경로를 우회하는 hidden bypass일 뿐이다
- 필요한 것은 새 도구가 아니라 [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)와 [Consumer Exception Operating Model](./consumer-exception-operating-model.md)로의 복귀다
- absorb가 아닌 이유는 기능 결손보다 **운영 discipline 결손**이 더 크기 때문이다
- officialize가 아닌 이유는 이 DM 절차가 재사용 가능한 고위험 판단 프로세스가 아니라, 만료 조건 없는 비가시적 약속이기 때문이다

exit criteria:

- 활성 연장 건이 모두 공식 registry로 옮겨지고 `expires_at`, owner, replacement path를 가진다
- DM 요청에는 템플릿 응답으로 공식 신청 경로만 안내한다
- deprecated endpoint의 consumer count와 연장 건수가 review cadence에서 함께 추적된다

#### 예시 C. migration cutover 체크리스트를 소수만 안다 -> officialize

상황:

- 데이터 migration cutover 때 DBA, app owner, SRE가 replication lag와 reconciliation delta를 보며 순서를 맞춘다
- 자동화는 일부 있지만, 최종 전환 여부는 사람 판단과 역할 handoff가 좌우한다
- 지금 이 절차를 없애면 cutover 자체가 위험해진다

판정:

- **officialize**가 맞다

왜 officialize인가:

- 핵심은 구조화 데이터 저장보다 **희귀하지만 고위험인 판단 순서와 역할 choreography**다
- absorb를 바로 택하기에는 아직 decision input이 충분히 안정적이지 않아 자동화가 거짓 안전감을 줄 수 있다
- retire는 replacement path가 준비되지 않았으므로 불가능하다
- 그래서 먼저 [Consumer Migration Playbook and Contract Adoption](./consumer-migration-playbook-contract-adoption.md) 또는 cutover runbook으로 올리고 rehearsal, rollback gate, owner를 붙이는 편이 안전하다

exit criteria:

- cutover runbook에 owner, 단계별 go/no-go 조건, rollback 기준, drill 기록이 포함된다
- 서로 다른 담당자가 같은 리허설을 재현할 수 있다
- 2~3개 migration wave 동안 decision input이 안정되면 absorb 후보로 재검토한다

### 10. 빠른 기억법: 무엇이 부족한지 먼저 본다

- 반복 예외와 구조화 데이터가 빠져 있으면: **absorb**
- 공식 경로는 있는데 사람들이 우회만 하고 있으면: **retire**
- 공식 경로가 아직 없고 사람 판단 choreography가 핵심이면: **officialize**

이 질문 순서로 보면 "이 과정이 존재해도 되는가?"보다 "공식 시스템에서 지금 무엇이 빠졌는가?"를 더 빨리 잡아낼 수 있다.

---

## 실전 시나리오

### 시나리오 1: 운영자가 수동으로 deprecation allowlist를 관리한다

반복 가치가 있고 auditability도 필요하므로 retire보다 absorb가 맞다.

### 시나리오 2: 특정 엔지니어만 아는 rollback 절차가 있다

이건 높은 위험을 가진 useful process다.
runbook으로 officialize하거나 자동화로 absorb해야 한다.

### 시나리오 3: 슬랙 DM 승인 절차가 계속 쓰인다

공식 override path가 있는데도 DM이 더 많이 쓰인다면, officialize가 아니라 공식 경로 UX 개선과 shadow retirement가 필요하다.

### 시나리오 4: 수동 allowlist 시트가 사실상 모든 예외 승인 근거가 된다

반복성이 높고 structured data도 많으므로 officialize보다 absorb가 맞다.
다만 absorb만 선언하고 override burn-down scorecard를 붙이지 않으면, 새 registry가 생겨도 수동 시트가 병행 사용될 가능성이 높다.

---

## 코드로 보기

```yaml
shadow_process_review:
  process: manual_deprecation_allowlist_sheet
  value: high
  risk: medium
  next_state: absorb
  target_system: exception_registry
  decision_basis:
    - repeatability_high
    - auditability_required
    - structured_data_present
  burn_down_metric: manual_sheet_usage_ratio
```

좋은 review는 shadow path를 도덕 평가가 아니라 구조 결정으로 다룬다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 무조건 retire | 단순하다 | 유효한 운영 요구를 놓친다 | 드문 경우 |
| officialize | 현실을 빨리 반영한다 | 문서만 늘어날 수 있다 | 반복 가치가 큰 process |
| absorb | 공식 경로가 강해진다 | tool/control-plane 투자 필요 | structured data/process인 경우 |

shadow process officialization and absorption criteria의 목적은 우회를 감추는 것이 아니라, **유효한 우회는 공식 경로로 끌어올리고 위험한 우회는 종료하게 만드는 것**이다.

---

## 꼬리질문

- 이 shadow path는 단순히 나쁜가, 아니면 공식 경로의 부족함을 보여 주는가?
- officialize와 absorb 중 어느 쪽이 더 지속 가능한가?
- retirement 전에 replacement path가 준비되어 있는가?
- officialize 뒤에 어떤 scorecard로 수동 사용을 줄일 것인가?
- 같은 shadow process가 다시 생기지 않게 공식 경로 UX를 고쳤는가?

## 한 줄 정리

Shadow process officialization and absorption criteria는 발견된 우회를 retire/officialize/absorb 중 어디로 보낼지 정해, shadow catalog를 실제 운영 개선으로 이어 주는 판단 프레임이다.
