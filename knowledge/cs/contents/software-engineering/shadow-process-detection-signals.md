# Shadow Process Detection Signals

> 한 줄 요약: shadow process는 누군가 신고해 주기를 기다리기보다, override pattern, 개인 DM 승인, stale 문서 우회, 수동 파일 관리 같은 detection signal을 정해 주기적으로 탐지해야 catalog와 retirement가 실제로 굴러간다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Mirror Lag SLA Calibration](./mirror-lag-sla-calibration.md)
> - [Team APIs and Interaction Modes in Architecture](./team-apis-interaction-modes-architecture.md)
> - [Platform Policy Ownership and Override Governance](./platform-policy-ownership-override-governance.md)
> - [Incident Feedback to Policy and Ownership Closure](./incident-feedback-policy-ownership-closure.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)

> retrieval-anchor-keywords:
> - shadow process detection
> - hidden workflow signal
> - workaround signal
> - unofficial process detection
> - process dark matter
> - dm approval pattern
> - stale doc bypass
> - shadow path signal
> - shadow process confidence
> - override concentration trigger
> - manual path instrumentation
> - mirror lag breach signal
> - shadow retirement candidate
> - catalog intake template

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Process Detection Signals](./README.md#shadow-process-detection-signals)
> - 다음 단계: [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)

## 핵심 개념

shadow process는 스스로 "저는 shadow입니다"라고 드러나지 않는다.
그래서 detection signal이 없으면 catalog와 retirement도 안 돌아간다.

대표 signal:

- 특정 개인에게만 반복되는 승인 요청
- 공식 시스템 밖 파일/시트로 관리되는 allowlist
- 문서엔 없는데 incident 때만 등장하는 수동 절차
- override가 특정 타입에서 반복 증가

즉 shadow process 관리는 inventory보다 먼저 **탐지 프레임**이 있어야 한다.

---

## 깊이 들어가기

### 1. 사람 의존 경로는 가장 강한 signal이다

예:

- "A님이 있어야 배포 가능"
- "이건 B님한테 DM하면 된다"
- "원래 이 값은 C님이 수동으로 바꾼다"

이런 경로는 ownership concentration과 hidden operational dependency를 의미한다.

### 2. 공식 control plane 밖의 data store도 signal이다

예:

- 로컬 스크립트
- 개인 spreadsheet
- 수동 allowlist 문서
- 비공식 노션 페이지

공식 시스템 밖에 중요한 운영 상태가 있으면 거의 항상 shadow process가 따라온다.

### 3. repeated exception pattern은 shadow process를 암시한다

같은 rule에 override가 계속 생기면:

- 공식 경로가 불편하거나
- 실제로 비공식 절차가 더 잘 작동하거나
- 문서와 현실이 어긋나고 있을 수 있다

즉 exception telemetry 자체가 detection input이 된다.

### 4. incident timeline에는 shadow clue가 많이 남는다

postmortem을 읽을 때 다음 표현은 signal이다.

- "원래는 이렇게 한다"
- "문서엔 없지만"
- "특정 사람이 수동으로"
- "급해서 별도 채널에서"

incident review parser나 human checklist에 이런 clue를 포함시키는 것도 유용하다.

### 5. detection signal은 burn-down과 연결돼야 한다

탐지만 하고 끝나면 backlog가 쌓인다.
signal은 다음으로 이어져야 한다.

- shadow process catalog entry 생성
- owner 지정
- risk score
- target state 지정
- review cadence 추가

### 6. signal은 source와 confidence를 함께 남겨야 한다

shadow process detection이 noisy해지는 가장 흔한 이유는 "의심"만 남기고, 왜 의심했는지와 얼마나 강한 근거인지 남기지 않는 것이다.

최소한 다음 필드는 같이 기록하는 편이 좋다.

- signal family: people dependency / off-plane data / repeated override / incident-only procedure
- source: incident review, support thread, exception registry, audit finding
- evidence window: 최근 30일, 최근 2개 incident, 최근 분기
- repeat count: 같은 패턴이 몇 번 나왔는가
- confidence: low / medium / high

예를 들어 "한 번 DM으로 승인받음"은 low confidence다.
반면 "최근 30일간 같은 policy override 8건 + 같은 운영자 DM 승인 5건 + 공식 runbook 부재"는 high confidence shadow candidate다.

### 7. override scorecard는 shadow process detection의 입력면이다

override가 많다는 사실만으로 shadow process가 확정되지는 않는다.
하지만 다음 패턴은 shadow path 후보를 매우 강하게 시사한다.

- 같은 policy에 override가 반복 집중된다
- 같은 owner/team이 같은 이유로 예외를 계속 요청한다
- registry엔 override가 닫히는데 실제 운영은 매번 DM/수동 파일로 반복된다
- blocked exit condition이 오래 남아 replacement path가 생기지 않는다

즉 override scorecard는 debt burn-down 도구이기도 하지만, 동시에 "공식 경로가 흡수하지 못한 현실"을 찾는 detection surface다.
이때 DM, spreadsheet, off-plane artifact를 message 수가 아니라 request 수로 정규화해 둬야 `manual_path_ratio`와 `shadow_candidate_count`가 noisy hint가 아니라 계산 가능한 signal이 된다.
구체적인 event model과 dedupe 규칙은 [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)을 따른다.

### 8. detection에서 catalog intake로 넘기는 기준을 정해 둬야 한다

아무 signal이나 전부 catalog에 넣으면 shadow backlog가 금방 noise가 된다.
보통은 다음 중 하나를 만족할 때 catalog entry로 승격시키면 균형이 맞는다.

- 서로 다른 signal family가 2개 이상 동시에 관찰된다
- 같은 workaround가 2번 이상 review cadence를 건너 반복된다
- auditability가 필요한 운영 상태가 공식 control plane 밖에서 관리된다
- incident/postmortem에서 "문서엔 없지만 실제론 이렇게 한다"가 재등장한다

catalog intake에는 suspicion만 적지 말고 다음 action까지 같이 적어야 한다.

- 임시 owner
- 다음 review forum
- tentative target state: retire / officialize / absorb / hold
- override scorecard와의 연결 여부

이때 intake 형식은 [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)처럼 evidence row와 review/retirement field가 함께 들어가는 형태가 가장 안정적이다.
반복 manual-path bundle을 어떤 tier와 confidence에서 실제 catalog intake로 승격할지는 [Shadow Candidate Promotion Thresholds](./shadow-candidate-promotion-thresholds.md)의 `observe / watchlist / promote / fast_track` 기본 계약을 같이 따르는 편이 좋다.

---

## 실전 시나리오

### 시나리오 1: deprecation allowlist가 운영자 노트북에만 있다

이건 control plane 밖 data store signal이다.

### 시나리오 2: 특정 팀만 항상 개인 DM으로 override를 받는다

지원 모델과 policy override 공식 경로가 부족한 signal일 수 있다.

### 시나리오 3: incident 때만 등장하는 수동 rollback 순서가 있다

runbook이 현실을 못 따라간다는 뜻이므로 shadow process detection에서 바로 잡아야 한다.

### 시나리오 4: override는 닫히는데 같은 DM 승인 이유가 계속 반복된다

이건 개별 예외 cleanup은 되고 있지만 shadow process는 여전히 살아 있다는 뜻이다.
override registry만 보지 말고, shadow catalog 후보로 승격해 officialization/absorption review로 넘겨야 한다.

---

## 코드로 보기

```yaml
shadow_signal:
  signal: repeated_dm_approval
  source: incident_review
  confidence: high
  evidence_window: last_30_days
  repeat_count: 5
  suspected_process: manual_release_override
  next_action: catalog_entry_create
  tentative_target_state: absorb
```

좋은 detection 모델은 vague suspicion을 actionable backlog로 바꾼다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 신고 | 운영 부담이 적다 | 많이 놓친다 | 초기 |
| signal checklist | 탐지가 쉬워진다 | 완전하진 않다 | 일반적인 조직 |
| telemetry + review 기반 detection | 가장 강하다 | 운영 투자 필요 | 성숙한 운영 조직 |

shadow process detection signal의 목적은 우회를 비난하는 것이 아니라, **공식 경로가 놓친 현실을 더 빨리 발견하는 것**이다.

---

## 꼬리질문

- 특정 개인이 single point of process가 된 곳은 없는가?
- 중요한 운영 상태가 공식 시스템 밖 파일에 남아 있지는 않은가?
- repeated override와 incident clue를 detection signal로 쓰고 있는가?
- signal family와 confidence를 같이 기록하고 있는가?
- detection된 shadow process가 catalog entry와 review cadence로 이어지는가?

## 한 줄 정리

Shadow process detection signals는 hidden workflow를 사람 기억에 기대지 않고 패턴과 telemetry와 incident clue로 찾아내, catalog와 retirement를 실질적으로 가능하게 만드는 운영 장치다.
