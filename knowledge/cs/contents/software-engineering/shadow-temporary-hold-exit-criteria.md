# Temporary Hold Exit Criteria

> 한 줄 요약: `temporary_hold`는 "나중에 보자"가 아니라 bounded pause여야 하며, 각 review마다 hold를 종료해 `resume_state`로 복귀할지, 기한과 범위를 좁혀 한 번 더 연장할지, 아니면 shadow need가 굳어져 `absorb` 또는 `officialize`로 승격해야 할지를 concrete example로 판정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Break-Glass Path Segmentation](./break-glass-path-segmentation.md)

> retrieval-anchor-keywords:
> - temporary hold exit criteria
> - shadow temporary hold
> - temporary_hold review
> - hold expiration governance
> - hold extension criteria
> - hold expiry review cadence
> - hold expiry dashboard
> - hold escalate absorb
> - hold escalate officialize
> - bounded pause shadow path
> - repeated hold extension
> - expires_at resume_state review
> - rollout freeze hold example
> - migration spreadsheet absorb escalation
> - cutover checklist officialize escalation
> - parked shadow path
> - temporary hold governance

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Temporary Hold Exit Criteria](./README.md#temporary-hold-exit-criteria)
> - 다음 단계: [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

## 핵심 개념

`temporary_hold`는 결정 회피용 parking lot가 아니다.
좋은 hold review는 매번 아래 셋 중 하나를 강제로 선택한다.

- expire: hold 이유가 끝났으니 원래 `resume_state`로 돌아간다
- extend: 같은 이유가 아직 유효하지만, 더 좁은 기한과 증빙을 붙여 한 번 더 멈춘다
- escalate: "임시"라고 부르기 어려울 만큼 반복 가치가 생겨 `absorb` 또는 `officialize`로 재분류한다

즉 핵심 질문은 "hold를 유지할 것인가"가 아니라, **이 pause가 아직도 temporary인가**다.

---

## 깊이 들어가기

### 1. hold에는 시작 조건보다 exit 조건이 더 중요하다

`temporary_hold`에 들어갈 때 보통 다음은 이미 있다.

- `hold_reason`
- `expires_at`
- `resume_state`
- `resume_trigger`

하지만 실무에서는 이것만으로 부족한 경우가 많다.
hold가 parking lot로 변하지 않게 하려면 review packet이나 catalog entry에 다음 메모를 같이 남기는 편이 좋다.

- `extension_count`
- `last_extension_reason`
- `evidence_expected_at_review`

이 세 가지가 없으면 review forum은 "왜 또 미뤘는지"를 기억에 의존하게 된다.
그리고 review 주기와 missed-expiry escalation을 사람 기억에 맡기지 않으려면 [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)처럼 `temporary_hold` 전용 baseline cadence를 같이 고정해 두는 편이 좋다.
또 overdue hold와 repeated extension을 portfolio level에서 바로 보려면 [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)처럼 `hold_time_to_expiry`, `holds_expired_open_count`, `hold_extension_count_distribution`을 별도 패널로 고정해 두는 편이 좋다.

### 2. exit 판단은 세 단계로 자르는 편이 안정적이다

| review 질문 | 예라면 | 아니라면 |
|---|---|---|
| 원래 hold 이유가 끝났는가 | hold를 종료하고 `resume_state`로 복귀한다 | 다음 질문으로 간다 |
| 같은 이유가 짧게 더 이어지지만 여전히 bounded한가 | 새 `expires_at`과 같은 `resume_state`를 붙여 한 번 더 연장한다 | 다음 질문으로 간다 |
| 이 shadow path가 반복되고 구조화돼서 임시라고 보기 어려운가 | `absorb` 또는 `officialize`로 escalation한다 | `blocked` 또는 decision 재검토가 필요하다 |

여기서 중요한 것은 순서다.
원래 이유가 이미 끝났다면 연장을 검토할 필요가 없고, 같은 이유가 더 이상 bounded하지 않다면 extension보다 escalation이 먼저다.

### 3. expire는 "멈춤 이유가 끝났음"을 뜻한다

hold를 종료할 때는 "아무 문제 없어 보인다"보다, **hold를 정당화하던 외부 조건이 실제로 사라졌는가**를 본다.

#### 예시 A. 분기말 freeze 때문에 멈춘 rollout override registry 작업 -> expire

상황:

- release override spreadsheet를 registry로 옮기기로 이미 결정했고 `resume_state`는 `absorb_in_progress`다
- 다만 분기말 freeze 때문에 control plane schema 배포를 잠깐 멈췄다
- hold 이유는 "freeze 종료 전까지 schema 변경 금지" 하나뿐이다

expire 신호:

- freeze 종료일이 지났고 배포 창이 다시 열렸다
- registry backlog slot과 integration owner가 그대로 살아 있다
- hold 기간 동안 spreadsheet 컬럼이나 사용 팀이 새로 늘지 않았다

왜 expire인가:

- 멈춤 이유가 사라졌는데도 hold를 유지할 근거가 없다
- 이 상태에서 연장을 택하면 "risk control"이 아니라 단순 backlog 미루기가 된다

다음 상태:

- `lifecycle_state: absorb_in_progress`
- `next_review_at`은 implementation 진행 확인용으로 다시 잡는다

#### 예시 B. incident stabilization 때문에 잠깐 남겨 둔 수동 rollback 메모 -> expire

상황:

- incident 직후 2주 동안은 운영자가 개인 rollback 메모를 보조 안전장치로 쓴다
- 공식 rollback runbook은 이미 있고 shadow path의 장기 target은 `retire`다

expire 신호:

- 같은 incident family 재발 없이 stabilization window를 통과했다
- 공식 runbook으로 대응 drill을 한 번 더 수행해 절차가 재현됐다
- 개인 메모가 authoritative source 역할을 하지 않는다

왜 expire인가:

- 이제 필요한 것은 hold 유지가 아니라 retirement execution과 verification이다

다음 상태:

- 보통 `retire_in_progress`, replacement가 이미 live라면 `verification_pending`

### 4. extend는 같은 이유가 짧게 더 이어질 때만 허용된다

정당한 extension은 "아직 준비가 안 됐어요"가 아니라, **같은 외부 제약이 조금 더 이어질 뿐이며 path 가설은 그대로 맞다**는 경우다.

권장 guardrail:

- 새 `expires_at`이 있어야 한다
- `resume_state`가 그대로 유지돼야 한다
- extension 이유가 이전 이유와 연속적이어야 한다
- scope가 넓어지지 않아야 한다
- extension count가 누적되면 escalation 여부를 강제로 다시 묻는다

#### 예시 A. 규제 감사 freeze가 1주 연장된다 -> bounded extension

상황:

- consumer exception registry 필드 추가가 감사 freeze 때문에 멈췄다
- 감사 일정이 1주 연장됐지만, 승인과 설계는 이미 끝났다

extend가 맞는 이유:

- 막는 이유가 owner 부재나 우선순위 실종이 아니라 동일한 freeze다
- extension 후에도 `resume_state = absorb_in_progress`가 맞다
- 새 `expires_at`과 다음 review date를 명확히 적을 수 있다

필수 기록:

- `expires_at` 재설정
- `extension_count += 1`
- "감사 종료 후 바로 registry schema rollout" 같은 재개 메모

#### 연장이 아닌 경우

다음 패턴은 extension처럼 보이지만 사실 escalation 또는 blocker다.

- 매 review마다 이유가 바뀐다
- 새 팀이 계속 같은 shadow path를 채택한다
- off-plane artifact가 source of truth로 굳는다
- 언제 끝날지 말하지 못하고 "다음 달에 다시 보자"만 반복한다

이 경우 hold는 temporary가 아니라 장기 운영 모델이 되고 있으므로, absorb/officialize 재판정 또는 `blocked` 전이가 더 맞다.

### 5. repeated hold가 구조화된 data path를 드러내면 absorb로 올린다

어떤 shadow path는 처음엔 temporary처럼 보이지만, 몇 차례 review 뒤에는 사실상 control plane gap을 드러낸다.

#### 예시 A. migration 기간에만 쓰려던 예외 스프레드시트가 세 wave째 남아 있다 -> absorb

상황:

- 첫 migration wave 동안만 쓸 생각으로 서비스별 cutover 예외, 승인자, 만료일을 spreadsheet에 적었다
- 두 번째, 세 번째 wave에서도 같은 컬럼을 그대로 복사해 쓴다
- spreadsheet가 여러 팀의 사실상 source of truth가 됐다
- entry는 두 번 연속 `temporary_hold` 연장을 받았다

absorb escalation 신호:

- 반복 입력 필드가 안정적이다
- 서로 다른 팀이 같은 구조를 재사용한다
- `manual_path_ratio`가 줄지 않고 평평하다
- "임시 시트"가 없으면 운영이 막히지만, 필요한 것은 사람 판단보다 structured state 저장이다

왜 absorb인가:

- 문제의 중심이 판단 choreography가 아니라 **공식 plane에 없는 구조화 데이터**다
- 더 연장하면 shadow path를 인정하는 셈이고, retire는 실제 수요를 지우지 못한다

다음 상태:

- `decision: absorb`
- `lifecycle_state: absorb_in_progress`
- `target_system_or_process: override_registry` 같은 공식 흡수 경로를 명시한다

#### 예시 B. release freeze hold가 끝났는데도 sheet 사용이 늘어난다 -> absorb 재판정

freeze는 끝났지만 사람들은 계속 수동 sheet를 선호하고, sheet 컬럼이 배포 배치 크기, mute window, 승인 로그까지 담당한다면 이미 일회성 hold를 넘어섰다.
이 경우 "한 번 더 hold"가 아니라 control plane field 결손을 메우는 absorb backlog가 맞다.

### 6. repeated hold가 사람 판단 choreography를 드러내면 officialize로 올린다

structured data보다 역할 분담과 판단 순서가 핵심인 경우에는 absorb가 아니라 officialize가 맞다.

#### 예시 A. 임시 cutover hold가 결국 고위험 전환 runbook 필요성을 드러낸다 -> officialize

상황:

- 첫 두 번의 대형 cutover 동안만 쓰자는 의도로, DBA/SRE/app owner가 따로 가진 수동 체크리스트를 `temporary_hold`로 남겼다
- 하지만 각 wave마다 go/no-go 판단, rollback 호출 순서, communication handoff가 비슷하게 반복된다
- 자동화 입력은 아직 충분히 안정적이지 않다

officialize escalation 신호:

- shadow path의 핵심 산출물이 spreadsheet state보다 역할별 판단 순서다
- 새 담당자가 들어오면 구두 전수가 없이는 재현이 어렵다
- drill과 rehearsal 없이는 안전성을 보장할 수 없다
- 같은 high-risk choreography가 여러 wave에서 유지된다

왜 officialize인가:

- 지금 필요한 것은 control plane field 추가보다 **공식 runbook, owner, training path**다
- absorb를 서두르면 거짓 자동화가 들어가고, hold 연장을 반복하면 tribal process가 굳는다

다음 상태:

- `decision: officialize`
- `lifecycle_state: officialize_in_progress`
- runbook ref, drill owner, go/no-go 기준을 붙인다

#### 예시 B. emergency 승인 call tree가 여러 incident에서 반복된다 -> officialize

incident stabilization을 이유로 hold했던 emergency escalation phone tree가 여러 incident에서 같은 역할 순서로 반복된다면, 이건 임시 우회가 아니라 공식 emergency procedure 후보다.
shadow note로 더 묶어 두기보다 on-call runbook과 교육 체계로 승격하는 편이 낫다.

### 7. 한 장 표로 보면 exit 판단이 더 빨라진다

| 결과 | 언제 선택하는가 | concrete example | review output |
|---|---|---|---|
| expire | 원래 멈춤 이유가 끝났다 | quarter-end freeze 종료 후 registry 작업 재개 | `resume_state`로 복귀, due date 재확인 |
| extend | 같은 이유가 짧게 더 이어진다 | 감사 freeze 1주 연장 | 새 `expires_at`, `extension_count`, 다음 evidence |
| escalate to absorb | 구조화된 state와 반복 예외가 쌓인다 | migration 예외 sheet가 세 wave째 authoritative source다 | `absorb_in_progress`, integration owner, metric 연동 |
| escalate to officialize | 사람 판단 순서와 훈련이 핵심이다 | cutover call sequence가 매 wave 반복된다 | `officialize_in_progress`, runbook owner, drill plan |

표를 보면 `temporary_hold`는 outcome이 아니라 질문 묶음이라는 점이 선명해진다.

### 8. hold review output은 "유지"보다 "왜 이 결론인가"를 남겨야 한다

review packet이나 catalog note에는 최소한 아래 중 하나가 남아야 한다.

- hold expired because `<원래 이유 종료>`
- hold extended until `<새 expires_at>` because `<같은 제약 지속>`
- hold escalated to `absorb` because `<structured data gap>`
- hold escalated to `officialize` because `<human choreography / training need>`

좋은 기록은 상태 이름보다, 다음 review에서 재판단할 수 있는 이유를 남긴다.

---

## 코드로 보기

```yaml
temporary_hold_review:
  catalog_id: shadow-cutover-exception-003
  lifecycle_state: temporary_hold
  hold_reason: quarter_end_freeze
  expires_at: 2026-05-03
  resume_state: absorb_in_progress
  extension_count: 1
  evidence_at_review:
    manual_path_ratio: 0.42
    authoritative_off_plane_artifact_count: 1
    repeat_waves: 3
  decision_outcome: escalate_to_absorb
  decision_reason: spreadsheet_has_become_authoritative_structured_state
  next_actions:
    - add override registry fields for cutover exception
    - assign integration owner
    - keep sheet read-only during transition
```

핵심은 "hold를 유지했다"가 아니라, 왜 더 이상 temporary라고 부를 수 없는지를 evidence와 함께 남기는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| hold를 빨리 expire | backlog 정체를 줄인다 | 아직 제약이 남아 있으면 재작업이 생긴다 | hold 이유가 실제로 종료됐을 때 |
| hold를 bounded extension | 단기 충돌을 피한다 | 누적되면 parking lot가 된다 | 같은 외부 제약이 짧게 더 이어질 때 |
| absorb escalation | off-plane state를 공식 plane으로 회수한다 | control plane 투자와 migration이 필요하다 | repeated structured data path일 때 |
| officialize escalation | 고위험 사람 판단 절차를 안전하게 만든다 | 문서, 훈련, drill 운영이 필요하다 | repeated human choreography일 때 |

---

## 꼬리질문

- 이 hold는 정말 같은 이유로만 연장되고 있는가?
- `expires_at`이 지났는데도 hold가 남아 있다면, 사실상 backlog 방치 아닌가?
- repeated extension이 구조화된 data gap을 보여 주는가, 아니면 runbook gap을 보여 주는가?
- absorb와 officialize 중 무엇이 shadow need의 핵심 자산을 더 정확히 담는가?

## 한 줄 정리

Temporary hold exit criteria의 핵심은 hold를 유지할지 묻는 것이 아니라, 이 pause가 끝났는지, 한 번 더 bounded extension이 가능한지, 아니면 repeated shadow need가 absorb/officialize로 승격돼야 하는지를 evidence로 구분하는 것이다.
