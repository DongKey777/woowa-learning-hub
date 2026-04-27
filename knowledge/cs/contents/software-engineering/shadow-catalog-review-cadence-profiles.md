# Shadow Catalog Review Cadence Profiles

> 한 줄 요약: shadow catalog entry는 상태마다 위험 신호가 다르므로 `detected`, `temporary_hold`, `blocked`, `verification_pending`를 같은 회의 주기로 다루지 말고, 각각 다른 review frequency, owner expectation, escalation SLA를 가진 운영 프로파일로 관리해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)
> - [Temporary Hold Exit Criteria](./shadow-temporary-hold-exit-criteria.md)
> - [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Override Burn-Down Review Cadence and Scorecards](./override-burndown-review-cadence-scorecards.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)

> retrieval-anchor-keywords:
> - shadow catalog review cadence
> - shadow review cadence profiles
> - shadow state review frequency
> - detected temporary_hold blocked verification_pending
> - shadow escalation sla
> - shadow owner expectation
> - blocked escalation clock
> - shadow forum escalation rules
> - hold expiry review cadence
> - blocked duration dashboard
> - hold expiry dashboard
> - retirement verification health
> - verification pending metric freshness
> - detected intake triage
> - shadow review forum response time
> - next_review_at cadence profile

> 읽기 가이드:
> - 돌아가기: [Software Engineering README - Shadow Catalog Review Cadence Profiles](./README.md#shadow-catalog-review-cadence-profiles)
> - 다음 단계: [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)

## 핵심 개념

`next_review_at`은 단순 달력 메모가 아니다.
shadow catalog에서는 상태별 운영 약속을 뜻한다.

같은 shadow entry라도 상태가 바뀌면 review 질문이 달라진다.

- `detected`: 이 신호를 실제 catalog backlog로 올릴지 빠르게 triage해야 한다
- `temporary_hold`: bounded pause가 parking lot로 변하지 않았는지 확인해야 한다
- `blocked`: 누가 언제 blocker를 풀지 escalation clock으로 관리해야 한다
- `verification_pending`: proof metric이 충분히 최신이며 recurrence가 없는지 닫기 전 검증해야 한다

이 네 상태를 전부 monthly review에 태우면 네 가지가 생긴다.

- `detected`가 늦게 catalog되어 signal freshness가 사라진다
- `temporary_hold`가 기한 없는 연기로 변한다
- `blocked`가 구조 문제 대신 "오래된 항목"처럼 숨는다
- `verification_pending`이 증빙 없이 `retired`로 밀려간다

즉 review cadence는 회의 편의가 아니라 **state별 failure mode를 막는 제어 장치**다.

---

## 깊이 들어가기

### 1. 상태별 cadence는 다른 clock을 따라야 한다

| 상태 | 따라야 할 clock | 왜 같은 cadence로 다루면 안 되는가 |
|---|---|---|
| `detected` | signal freshness clock | evidence가 낡으면 anecdote와 반복 패턴이 섞인다 |
| `temporary_hold` | `expires_at` clock | bounded pause가 parking lot로 굳는다 |
| `blocked` | unblock / escalation clock | 구조 문제를 오래된 backlog처럼 오해한다 |
| `verification_pending` | proof freshness clock | closure 증빙 없이 retired 판단이 앞서간다 |

좋은 cadence profile은 "언제 다시 볼까"만 정하지 않는다.
동시에 다음도 고정한다.

- 누가 이번 상태의 update를 책임지는가
- 어떤 field가 review packet에 반드시 있어야 하는가
- 어떤 지연이 발생하면 상위 forum으로 올려야 하는가

### 2. baseline cadence profile은 상태별로 다르게 고정한다

아래 표는 shadow catalog용 기본 프로파일이다.
서비스 criticality가 높으면 한 단계 더 촘촘하게 가져갈 수 있지만, 이 baseline보다 느리게 풀지는 않는 편이 안전하다.

| 상태 | 기본 review frequency | owner expectation | escalation SLA |
|---|---|---|---|
| `detected` | 최초 triage `2 영업일` 이내, 이후 `주 1회` intake review | intake owner를 지정하고 `signal_evidence`, 중복 여부, catalog 승격 또는 drop 판단을 준비한다 | `5 영업일` 안에 owner 또는 disposition이 없으면 `1 영업일` 내 forum owner로 escalation, 고위험 signal이면 당일 escalation |
| `temporary_hold` | `주 1회` 또는 `expires_at 2 영업일 전` 중 더 이른 시점 | `hold_reason`, `expires_at`, `resume_state`, `extension_count`, 다음 review에서 확인할 증빙을 갱신한다 | expiry를 넘기거나 review를 놓치면 `1 영업일` 내 escalation, 두 번째 extension부터는 다음 review cycle 안에 decision forum 재판정 |
| `blocked` | 해소될 때까지 `3 영업일`마다 review | `blockers`, `blocker_owner`, `blocked_since`, unblock action, 복귀 상태를 명시한다 | `1 영업일` 안에 blocker owner 또는 ETA가 없으면 escalation, `5 영업일` 이상 지속되면 같은 주에 상위 forum으로 승격 |
| `verification_pending` | `격주` closeout review, metric freshness는 `주 1회` 확인 | `verification_metric`, `parallel_run_until`, `recurrence_check_at`, metric 최신 시각과 해석을 유지한다 | recurrence나 threshold breach는 당일 escalation, telemetry freshness가 `2 영업일` 넘게 깨지거나 close decision이 window를 넘기면 다음 forum에서 escalate |

핵심은 review frequency만 복사하지 않는 것이다.
각 상태는 **다른 owner 행동과 다른 escalation trigger**를 같이 가진다.

### 3. `detected`는 inventory 대기열이 아니라 빠른 intake queue다

`detected` 상태의 목적은 긴 분석이 아니다.
signal이 catalog 대상인지 아닌지 빠르게 가르는 것이다.

owner expectation:

- intake owner를 지정한다
- 같은 `process_family`의 기존 entry와 중복 여부를 확인한다
- 최소 evidence row를 붙인다
- `cataloged`로 승격할지 추가 evidence를 요청할지 결정한다

이 상태를 오래 두면 `repeat_count`와 `observed_at`은 남아도 실제 판단 맥락이 흐려진다.
그래서 `detected`는 "다음 달에 다시 보자"가 아니라 **이번 주 intake queue**로 관리하는 편이 맞다.

특히 같은 signal family가 같은 review cadence를 한 번 건너 다시 나타나면, owner의 준비 부족보다 catalog 지연이 더 큰 문제일 수 있다.
이때는 개별 entry 정리보다 forum triage capacity를 먼저 조정해야 한다.

### 4. `temporary_hold`는 expiry-driven cadence가 기본이다

`temporary_hold`는 implementation이 느린 상태가 아니라, 의도된 pause다.
그래서 review는 단순 weekly rhythm보다 `expires_at`에 더 민감해야 한다.

owner expectation:

- hold가 왜 temporary인지 매 review마다 다시 설명할 수 있어야 한다
- `resume_state`는 유지하되 extension 근거가 바뀌면 hold가 아니라 재분류를 검토한다
- `extension_count`와 `evidence_expected_at_review`를 남긴다
- hold가 끝나면 어느 forum에서 어떤 상태로 복귀할지 준비한다

좋은 `temporary_hold` escalation은 "오래됐으니 보고하자"가 아니다.
보통 아래 둘 중 하나일 때 올라간다.

- expiry를 넘겼는데 expire / extend / escalate 결정이 없다
- extension reason이 이전 hold와 연속적이지 않다

첫 번째는 운영 discipline 실패고, 두 번째는 상태 분류 실패다.
둘 다 같은 수준의 follow-up으로 처리하면 hold가 parking lot로 굳는다.

### 5. `blocked`는 backlog age가 아니라 unblock clock으로 관리한다

`blocked`는 진행이 멈췄다는 사실보다, 구조 문제를 뜻한다.
그래서 review frequency도 "얼마나 오래됐는가"보다 "누가 언제 푸는가"에 맞춰야 한다.

owner expectation:

- blocker를 리스트가 아니라 actionable item으로 바꾼다
- 각 blocker에 owner와 ETA를 붙인다
- `blocked_from_state`를 보존해 unblock 뒤 어디로 돌아갈지 고정한다
- local forum으로 풀 문제인지 상위 governance issue인지 분리한다

`blocked`에서 자주 생기는 실패는 두 가지다.

- blocker owner가 없어서 매 review가 같은 말만 반복된다
- escalation forum은 정해졌지만 실제 escalation clock이 없다

그래서 `blocked` entry는 최소한 `1 영업일` 안에 owner acknowledgement가 있어야 한다.
이 acknowledgement가 없으면 implementation팀의 느린 진행이 아니라 **governance orphan backlog**다.
그리고 `blocked_duration > 5 영업일`, `impacted_domains >= 2`, `affected_teams >= 3`, high-blast shared gate 같은 조건에서 local stewardship이 언제 architecture council로 ownership을 넘겨야 하는지는 [Shadow Forum Escalation Rules](./shadow-forum-escalation-rules.md)처럼 별도 threshold 문서로 고정해 두는 편이 좋다.

### 6. `verification_pending`은 대기 상태가 아니라 proof collection 상태다

replacement path가 live라고 해서 바로 retired가 되지 않는다.
이 상태의 핵심은 "얼마나 기다릴까"가 아니라 "증빙이 충분히 최신인가"다.

owner expectation:

- `verification_metric`의 freshness를 주 단위로 확인한다
- baseline 대비 감소 추세와 recurrence 여부를 같이 본다
- `parallel_run_until` 전에 retire / extend verification / reopen 중 어떤 출력이 필요한지 준비한다
- telemetry gap이 생기면 verification을 계속 밀지 말고 즉시 원인과 복구 ETA를 적는다

`verification_pending`을 monthly closeout으로만 다루면 흔히 두 가지가 생긴다.

- metric snapshot이 낡아 manual path recurrence를 놓친다
- close decision이 verification window보다 늦어져 사실상 `retired by timeout`이 된다

그래서 이 상태는 forum review는 `격주`로 두더라도, metric freshness check는 더 짧게 유지하는 편이 안전하다.

### 7. cadence profile은 schema와 packet에 같이 투영돼야 한다

상태별 cadence를 문서에만 적어 두면 운영에서는 쉽게 사라진다.
최소한 아래 field는 state별로 review packet에 바로 보이게 해야 한다.

| 상태 | packet에서 바로 보여야 할 필드 | 이유 |
|---|---|---|
| `detected` | `observed_at`, `repeat_count`, `confidence`, `triage_due_at` | signal freshness와 intake urgency를 보여 준다 |
| `temporary_hold` | `hold_reason`, `expires_at`, `resume_state`, `extension_count` | bounded pause 여부를 판단하게 한다 |
| `blocked` | `blocked_since`, `blockers`, `blocker_owner`, `escalation_forum` | unblock 책임과 escalation clock을 드러낸다 |
| `verification_pending` | `verification_metric`, `metric_fresh_at`, `parallel_run_until`, `recurrence_check_at` | proof freshness와 closeout window를 보이게 한다 |

이 projection이 없으면 `next_review_at`만 남고, 왜 그 날짜인지 아무도 설명하지 못한다.
그리고 이 상태별 clock을 dashboard에서 어떻게 보여 줄지는 [Shadow Lifecycle Scorecard Metrics](./shadow-lifecycle-scorecard-metrics.md)처럼 `lifecycle_state aging`, `blocked duration`, `hold expiry`, `retirement verification health` 패널로 따로 고정해 두는 편이 cadence drift를 빨리 찾게 해 준다.

### 8. criticality modifier는 cadence를 느리게 하는 장치가 아니라 더 빠르게 하는 장치다

다음 조건이 있으면 baseline보다 한 단계 더 촘촘한 cadence가 적절하다.

- auditability failure나 policy bypass가 큰 shadow path
- single-person dependency가 강한 shadow process
- 운영 중단이나 release block을 직접 일으키는 blocker
- verification 중 recurrence가 한 번이라도 다시 나타난 항목

반대로 low-risk라고 해서 baseline보다 느리게 보는 것은 추천하기 어렵다.
shadow catalog의 실패는 대개 항목이 너무 자주 review돼서가 아니라, **너무 늦게 회수돼서** 생긴다.

---

## 코드로 보기

```yaml
shadow_review_cadence_profiles:
  detected:
    first_triage_sla: 2bd
    review_every: weekly
    escalate_if:
      - owner_missing_for > 5bd
      - disposition_missing_for > 5bd
      - high_risk_signal_detected
  temporary_hold:
    review_every: min(weekly, expires_at_minus_2bd)
    owner_must_update:
      - hold_reason
      - expires_at
      - resume_state
      - extension_count
    escalate_if:
      - expires_at_passed
      - review_missed
      - extension_count >= 2
  blocked:
    review_every: every_3bd
    ack_sla: 1bd
    escalate_if:
      - blocker_owner_missing_for > 1bd
      - unblock_eta_missing_for > 1bd
      - blocked_age > 5bd
  verification_pending:
    review_every: biweekly
    metric_freshness_check: weekly
    escalate_if:
      - recurrence_detected
      - verification_metric_stale_for > 2bd
      - parallel_run_until_passed_without_decision
```

중요한 것은 state마다 `review_every`만 다르게 두는 것이 아니라, `ack_sla`, `metric_freshness_check`, `escalate_if`까지 함께 묶는 것이다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 단일 cadence | 운영이 단순하다 | 상태별 위험을 놓친다 | 권장하지 않는다 |
| 상태별 cadence만 분리 | 기본 우선순위는 잡힌다 | owner 행동과 escalation이 약해질 수 있다 | 중간 단계 |
| 상태별 cadence + owner expectation + escalation SLA | 정체와 가짜 종료를 줄인다 | forum discipline이 필요하다 | 권장 기본형 |

shadow catalog review cadence의 목적은 회의를 늘리는 것이 아니라, **상태별로 놓치면 안 되는 failure mode를 더 빨리 잡는 것**이다.

---

## 꼬리질문

- `detected` entry가 weekly intake queue를 넘어 방치되고 있지는 않은가?
- `temporary_hold`의 `expires_at`을 넘긴 항목이 자동으로 보이는가?
- `blocked` entry마다 blocker owner와 ETA가 실제로 붙어 있는가?
- `verification_pending`에서 metric freshness와 recurrence check가 분리돼 있는가?
- `next_review_at`이 상태 기반 규칙으로 계산되는가, 아니면 회의 편의로 적히는가?

## 한 줄 정리

Shadow catalog review cadence profiles는 `detected`, `temporary_hold`, `blocked`, `verification_pending`를 서로 다른 clock과 SLA로 다뤄, shadow backlog 정체와 가짜 retirement를 줄이는 운영 기준이다.
