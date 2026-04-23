# Shadow Catalog Reopen and Successor Rules

> 한 줄 요약: shadow recurrence가 보였다고 매번 새 catalog entry를 만드는 것도, 반대로 같은 entry를 무조건 재사용하는 것도 위험하므로, **같은 shadow identity와 같은 replacement path의 실패**라면 reopen하고, **scope/path/owner/replacement가 구조적으로 달라졌다면 successor entry**를 만들어 lineage와 history를 남겨야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shadow Catalog Lifecycle States](./shadow-catalog-lifecycle-states.md)
> - [Shadow Process Catalog Entry Schema](./shadow-process-catalog-entry-schema.md)
> - [Shadow Review Packet Template](./shadow-review-packet-template.md)
> - [Shadow Review Outcome Template](./shadow-review-outcome-template.md)
> - [Shadow Retirement Proof Metrics](./shadow-retirement-proof-metrics.md)
> - [Shadow Retirement Scorecard Schema](./shadow-retirement-scorecard-schema.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)
> - [Shadow Catalog Review Cadence Profiles](./shadow-catalog-review-cadence-profiles.md)
> - [Manual Path Ratio Instrumentation](./manual-path-ratio-instrumentation.md)
> - [Service Split, Merge, and Absorb Evolution Framework](./service-split-merge-absorb-evolution-framework.md)
> - [Decision Revalidation and Supersession Lifecycle](./decision-revalidation-supersession-lifecycle.md)

> retrieval-anchor-keywords:
> - shadow catalog reopen rules
> - shadow successor entry
> - reopen vs successor
> - shadow recurrence lineage
> - predecessor successor link
> - lineage root id
> - reopen same catalog entry
> - create successor catalog entry
> - recurrence decision rule
> - shadow history preservation
> - retired entry reopened
> - new catalog id successor
> - shadow recurrence audit trail
> - replacement path continuity
> - recurrence lineage block
> - shadow catalog history rules
> - same path same replacement reopen
> - new baseline snapshot successor
> - append only retirement attempts
> - predecessor successor cross link
> - recurrence write contract
> - active shadow entry recurrence
> - verification pending rollback
> - lineage adjacency rules
> - split successor lineage
> - merge successor lineage
> - transitive lineage preservation

## 핵심 개념

shadow catalog에서 recurrence를 다루는 핵심 질문은 하나다.

`이 recurrence는 과거 retirement proof가 실패한 같은 shadow process인가, 아니면 과거 항목과 혈통은 이어지지만 별도 backlog로 관리해야 할 후속 변종인가?`

이 질문에 대한 답이 다음 둘을 가른다.

- `reopen same entry`: 같은 shadow identity와 같은 공식 replacement를 계속 추적할 수 있다
- `create successor entry`: 과거 entry는 역사로 남겨 두고, 새 shadow cycle을 별도 row로 관리해야 한다

잘못 고르면 두 가지 실패가 생긴다.

- 무조건 reopen: 과거의 종료 증빙과 현재 recurrence가 뒤섞여 history가 흐려진다
- 무조건 successor: 사실상 같은 문제를 매번 새로 발견한 것처럼 보이게 만들어 recurrence learning이 사라진다

즉 reopen/successor 규칙의 목적은 row 개수를 예쁘게 맞추는 것이 아니라, **운영 연속성과 historical auditability를 동시에 지키는 것**이다.

---

## 깊이 들어가기

### 1. 가장 강한 판별 질문은 `같은 exit condition으로 계속 볼 수 있는가`다

recurrence를 봤을 때 가장 먼저 확인할 것은 날짜나 owner가 아니라 다음 두 가지다.

- 같은 `current_path` 또는 같은 off-plane authoritative artifact가 다시 살아났는가
- 같은 `replacement_path`, 같은 `exit_condition`, 같은 proof metric으로 다시 닫을 수 있는가

둘 다 `yes`라면 reopen 쪽이 맞다.
반대로 둘 중 하나라도 `no`라면 successor를 더 강하게 검토해야 한다.

예:

- 같은 Slack DM 승인 우회가 다시 나타나고, 여전히 `override_registry`로 흡수하는 문제가 남아 있다면 reopen이 맞다
- DM은 사라졌지만 이번에는 spreadsheet allowlist가 authoritative source가 되었고, replacement도 `registry`가 아니라 `policy_control_plane`으로 바뀌었다면 successor가 맞다

핵심은 recurrence의 표면 증상보다 **같은 구조 문제를 같은 종료 규칙으로 설명할 수 있는가**다.

### 2. 다음 조건이면 같은 entry를 reopen하는 편이 맞다

아래 조건이 대부분 유지되면 same-entry reopen이 기본값이다.

| 판단 질문 | reopen 신호 |
|---|---|
| 같은 `process_family`인가 | 같은 shadow candidate key 또는 같은 운영 우회 family다 |
| 같은 shadow path인가 | 같은 DM, 같은 sheet, 같은 local script, 같은 구두 절차가 다시 나타난다 |
| 같은 replacement path인가 | 여전히 같은 control plane, runbook, 공식 workflow로 수렴시킬 수 있다 |
| 같은 review forum인가 | forum과 owner가 바뀌더라도 책임 구조가 본질적으로 같다 |
| 같은 proof rule인가 | 과거 `verification_metric`, `threshold_rule`, `verification_window`를 계속 쓸 수 있다 |

보통 reopen이 맞는 상황:

- `retired` 직후 같은 path recurrence가 다시 보였다
- `retired` closeout outcome이 승인된 직후 recurrence가 잡혀 종료를 되돌려야 한다
- 조직 개편이나 담당자 교체는 있었지만 shadow path와 replacement design은 그대로다
- 과거 proof가 telemetry gap, premature close, incomplete adoption 때문에 무너진 것이다

이 경우 중요한 점은 "새 이슈처럼 보이게 다시 등록"하는 것이 아니라, **같은 항목이 실제로 끝나지 않았음을 기록하는 것**이다.

### 3. 다음 조건이면 successor entry를 만드는 편이 맞다

아래 중 하나라도 구조적으로 바뀌면 successor entry가 더 안전하다.

| 구조 변화 | 왜 successor가 필요한가 |
|---|---|
| shadow path가 바뀌었다 | old path proof와 새 path evidence를 같은 row에 섞으면 무엇을 retire하는지 흐려진다 |
| replacement path가 바뀌었다 | 다른 control plane, 다른 runbook, 다른 exit condition을 쓰면 fresh baseline이 필요하다 |
| scope가 split/merge됐다 | 한 row로는 owner, risk, due date를 정직하게 표현할 수 없다 |
| risk model이나 signal family가 달라졌다 | 예전 recurrence threshold와 현재 recurrence threshold가 같은 의미가 아니다 |
| governance venue가 달라졌다 | 다른 domain, 다른 forum, 다른 escalation chain이면 별도 backlog가 더 정확하다 |

보통 successor가 맞는 상황:

- DM 우회는 사라졌지만 spreadsheet가 새 authoritative source가 됐다
- 한 global shadow process가 조직 개편 뒤 두 서비스별 shadow path로 갈라졌다
- old replacement는 runbook officialization이었지만, 이번 recurrence는 policy-as-code 흡수 문제로 바뀌었다
- 오래 안정적으로 retired된 뒤 전혀 다른 owner와 path에서 비슷한 workaround가 새로 생겼다

중요한 점은 `시간이 오래 지났음`만으로 successor를 만들지 않는 것이다.
long quiet gap은 참고 신호일 뿐이고, **path/replacement/scope의 연속성이 끊겼는가**가 결정 기준이다.

### 4. 애매할 때는 `history를 덮어쓰지 않는 쪽`이 더 안전하다

reopen과 successor가 정말 애매할 수 있다.
이때는 다음 보수 규칙이 유용하다.

- 과거 `retired_at`과 proof snapshot을 그대로 current row에 덮어써야 한다면 successor가 더 안전하다
- 과거 `exit_condition`을 그대로 유지할 수 없다면 successor가 더 안전하다
- predecessor를 남겨 두지 않으면 "왜 이번엔 다른 backlog가 필요한가"를 설명하기 어렵다면 successor가 더 안전하다

반대로 다음이 명확하면 reopen이 더 낫다.

- 같은 shadow path라는 direct evidence가 있다
- 같은 replacement backlog가 이미 열려 있다
- review forum이 "지난번에 닫았던 그 항목이 다시 열렸다"라고 이해하는 편이 더 정확하다

즉 ambiguity의 핵심은 entry count가 아니라 **evidence continuity를 current row에 정직하게 유지할 수 있는가**다.

### 5. 결정 순서는 `identity 연속성 -> 종료 규칙 연속성 -> backlog shape` 순으로 고정하는 편이 좋다

recurrence를 볼 때 forum이 owner 변경이나 quiet gap부터 붙잡으면 reopen/successor 판단이 흔들린다.
실무에서는 다음 순서로 자르는 편이 가장 덜 헷갈린다.

1. `identity continuity`: 같은 `process_family`, 같은 `current_path`, 같은 off-plane artifact인가
2. `replacement continuity`: 같은 `replacement_path`, 같은 `exit_condition`, 같은 proof metric으로 닫을 수 있는가
3. `backlog shape`: 같은 row가 current scope/owner/due date를 정직하게 표현하는가

판단 규칙은 보통 이렇게 단순화할 수 있다.

- 1, 2가 모두 `yes`이고 3도 무리 없으면 reopen
- 1은 비슷해 보여도 2가 `no`면 successor
- 1, 2가 애매하더라도 3 때문에 one-to-many 또는 many-to-one 관리가 필요하면 successor

즉 reopen/successor는 "얼마나 닮았는가"보다 **같은 종료 계약으로 같은 backlog를 계속 운영할 수 있는가**로 정하는 편이 맞다.

### 6. active state에서 잡힌 recurrence는 먼저 `same-entry continue`인지 본다

reopen/successor 논의는 주로 `retired` 이후 recurrence를 전제로 하지만, 현실에서는 아직 열려 있는 entry에서도 recurrence signal이 자주 잡힌다.
이때는 새 항목을 만들기 전에 "애초에 같은 row가 아직 살아 있는가"를 먼저 봐야 한다.

기본 규칙은 이렇다.

- `cataloged`, `decision_pending`, `*_in_progress`, `blocked`, `temporary_hold`에서 같은 path recurrence가 잡히면 보통 successor를 만들지 않는다
- `verification_pending`에서 same-path recurrence가 잡히면 closeout 실패로 보고 같은 row를 rollback하는 편이 맞다
- 아직 retire되지 않은 entry는 보통 `reopen`도 아니다. 그냥 **같은 row의 미해결 상태가 계속 드러난 것**이다
- 다만 active entry라도 scope/path/replacement/backlog shape가 구조적으로 바뀌면 successor를 검토한다

| recurrence가 잡힌 시점 | 기본 동작 | successor를 검토하는 신호 |
|---|---|---|
| `cataloged`, `decision_pending` | 같은 row에 evidence를 append하고 decision을 다시 연다 | review forum/owner map이 달라져 별도 backlog가 더 정직하다 |
| `*_in_progress` | 같은 row를 유지하고 blocker 또는 execution plan을 수정한다 | replacement path가 바뀌어 새 baseline이 필요하다 |
| `blocked`, `temporary_hold` | hold/blocker 평가를 갱신하고 same row를 유지한다 | split/merge로 one-row 운영이 깨진다 |
| `verification_pending` | 같은 row를 `cataloged` 또는 `decision_pending`으로 rollback한다 | recurrence 원인이 다른 shadow path/다른 replacement failure다 |
| `retired` | reopen 또는 successor를 정식 판정한다 | 현재 문서의 핵심 분기다 |

이 규칙을 먼저 두면 "아직 안 닫힌 문제"와 "닫혔다가 다시 열린 문제"를 섞지 않게 된다.

### 7. reopen은 `catalog_id`를 유지하되, 과거 종료 기록을 절대 지우지 않는다

같은 entry를 reopen한다면 운영 규칙은 단순해야 한다.

- 기존 `catalog_id`는 유지한다
- 현재 상태는 `retired`를 그대로 둔 채 서술하지 말고, canonical state로 되돌린다
- past closeout evidence는 append-only history로 남긴다
- 새로운 recurrence evidence window는 별도 event로 추가한다

권장 흐름:

1. `retired -> cataloged`로 전이한다
2. `reopen_reason`, `reopened_at`, `recurrence_evidence_ref`를 history에 추가한다
3. 과거 `retired_at`, `proof_ref`, `baseline_snapshot_ref`는 `history.retirement_attempts[]`로 보존한다
4. 다음 forum에서 `decision_pending` 또는 적절한 `*_in_progress`로 다시 보낸다

핵심은 "같은 row를 재활용한다"가 아니라, **같은 row 안에 cycle history를 누적한다**는 점이다.

### 8. successor는 새 `catalog_id`를 열고, predecessor는 append-only 링크만 남긴다

successor를 만들 때는 old row를 다시 현재형으로 바꾸지 않는다.
대신 lineage를 분명히 남긴다.

- successor는 새 `catalog_id`를 갖는다
- successor는 새 `signal_evidence`, `next_review_at`, `baseline_snapshot_ref`, `verification_window`를 가진다
- predecessor는 기존 lifecycle outcome을 유지하되, successor link만 append한다
- successor는 `lineage_root_id`와 `predecessor_catalog_ids[]`를 가진다

이 규칙의 장점은 분명하다.

- 과거 retirement proof는 당시의 사실로 남는다
- 새 recurrence는 fresh baseline으로 관리된다
- review forum이 "같은 혈통이지만 다른 운영 backlog"라는 점을 바로 이해할 수 있다

특히 split/merge가 생기면 successor model이 사실상 필수다.
한 predecessor에서 여러 successor가 나올 수도 있고, 여러 predecessor를 하나의 successor가 흡수할 수도 있다.

### 9. linkage write contract를 정해 두면 reopen/successor 판단이 row-level 변경으로 바로 이어진다

판단만 맞고 write contract가 없으면 실제 catalog는 쉽게 망가진다.
최소한 다음 표처럼 "어느 row에 무엇을 쓰는가"를 고정해 두는 편이 좋다.

| 경우 | 기존 row에서 하는 일 | 새 row에서 하는 일 | 절대 하지 말아야 할 일 |
|---|---|---|---|
| `same-entry reopen` | 같은 `catalog_id` 유지, `lifecycle_state` 복귀, `history.reopen_events[]` append, fresh `signal_evidence`/`next_review_at` 추가 | 없음 | 과거 `retired_at`과 `retirement_attempts[]`를 지우거나 덮어쓰기 |
| `successor` | predecessor의 lifecycle outcome 유지, `lineage.successor_catalog_ids[]` append | 새 `catalog_id`, 같은 `lineage_root_id`, `predecessor_catalog_ids[]`, fresh baseline/proof window | predecessor를 현재형으로 되돌리거나 old proof를 successor의 현재 상태처럼 복사 |
| `one-to-many split successor` | predecessor에 모든 successor id를 append | 각 successor가 같은 `lineage_root_id`와 동일 predecessor ref를 가짐 | predecessor 하나를 reopen해서 여러 owner/scope를 억지로 대표 |
| `many-to-one merge successor` | 각 predecessor가 공통 successor id를 append | successor가 `predecessor_catalog_ids[]`에 모든 입력 row를 가짐 | predecessor 하나만 남기고 나머지 lineage를 삭제 |

이 표의 요점은 간단하다.
reopen은 **같은 row의 새 cycle**, successor는 **다른 row의 새 baseline**이다.

### 10. lineage block은 history보다 먼저 설계해야 한다

schema에 최소한 다음 정도의 lineage/history 필드가 있으면 reopen과 successor를 일관되게 남길 수 있다.

```yaml
lineage:
  lineage_root_id: shadow-release-approval-001
  predecessor_catalog_ids:
    - shadow-release-approval-001
  successor_catalog_ids:
    - shadow-release-approval-001a
history:
  reopen_events:
    - reopened_at: 2026-07-14
      from_state: retired
      reopen_reason: same_slack_dm_path_recurred
      recurrence_evidence_ref: INC-912
  retirement_attempts:
    - retired_at: 2026-06-01
      proof_ref: shadow-proof-2026-06-01
      baseline_snapshot_ref: baseline-2026-05-01
      verification_window: 30d
```

필드 설계 원칙은 다음이 좋다.

- `lineage_root_id`: 같은 혈통의 첫 entry를 고정한다
- `predecessor_catalog_ids[]`: 이 entry가 어디에서 이어졌는지 보이게 한다
- `successor_catalog_ids[]`: old row에서 다음 row를 찾게 한다
- `history.reopen_events[]`: 같은 row 안에서 재개된 cycle을 남긴다
- `history.retirement_attempts[]`: 과거 closeout 증빙을 append-only로 남긴다

이 정도만 있어도 "이건 같은 entry를 다시 연 것인가, 새로운 successor인가"를 나중에 추적할 수 있다.

### 11. review packet에도 reopen/successor 판단 질문이 따로 있어야 한다

recurrence review에서 packet이 lifecycle 요약만 보여 주면, forum은 보통 감으로 reopen 또는 successor를 정한다.
그래서 packet에는 적어도 다음 projection이 있어야 한다.

- `same_path_assessment`
- `replacement_continuity_assessment`
- `lineage_action_proposed`
- `predecessor_catalog_ids`
- `prior_retirement_proof_ref`

이 다섯 가지가 있으면 forum은 다음 질문을 직접 다룰 수 있다.

- 같은 shadow path가 다시 나타난 것인가
- 예전 exit condition을 그대로 쓸 수 있는가
- 같은 row reopen이 맞는가, 새 row successor가 맞는가

즉 recurrence packet의 목적은 "재발했다"를 보여 주는 것이 아니라, **어떤 lineage action을 취할지 명확히 만드는 것**이다.

### 12. history rule의 핵심은 `과거 proof를 현재 truth처럼 덮지 않는 것`이다

reopen이든 successor든 공통 금지 규칙이 있다.

1. 과거 `retired_at`을 지우지 않는다
2. 과거 `proof_ref`, `baseline_snapshot_ref`, `verification_window`를 새 cycle 값으로 덮어쓰지 않는다
3. predecessor link 없이 successor를 만들지 않는다
4. recurrence evidence를 old verification window에 소급 삽입하지 않는다

이 네 가지를 어기면 review forum은 다음을 구분하지 못한다.

- 지난번 종료 판단이 왜 틀렸는가
- 이번 recurrence가 정말 같은 문제인가
- 어떤 지표와 어떤 owner로 다시 닫아야 하는가

즉 history rule의 목적은 감사를 위해 데이터만 남기는 것이 아니라, **다음 decision을 더 정확히 만들기 위해 과거 결정을 보존하는 것**이다.

### 13. successor history는 "복사"보다 "참조" 중심으로 남기는 편이 안전하다

successor를 만들 때 자주 생기는 실수는 predecessor의 closeout evidence를 새 row에 다시 적어 넣는 것이다.
하지만 그러면 두 row가 둘 다 같은 proof를 현재 사실처럼 말하게 된다.

그래서 successor history는 다음 원칙이 안전하다.

- predecessor의 `history.retirement_attempts[]`는 predecessor에만 남긴다
- successor는 `predecessor_catalog_ids[]`와 `prior_retirement_proof_ref` 같은 참조만 가진다
- successor의 현재 cycle 증빙은 새 `signal_evidence`, 새 `baseline_snapshot_ref`, 새 `verification_window`로 다시 시작한다
- predecessor proof를 successor의 `retired_at` 또는 current verification 근거처럼 재사용하지 않는다

즉 successor는 과거를 복제하는 row가 아니라, **과거 실패를 설명 가능한 상태로 참조하는 새 운영 row**다.

### 14. predecessor/successor link는 인접 edge만 append하고 `lineage_root_id`는 고정한다

lineage를 남긴다고 해서 모든 row에 전체 가계도를 매번 다시 써 넣을 필요는 없다.
오히려 local adjacency를 흐리면 "직전 무엇에서 이어졌는가"가 더 불분명해진다.

보존 규칙은 다음처럼 단순한 편이 좋다.

- `lineage_root_id`는 첫 entry id를 계속 유지한다
- `predecessor_catalog_ids[]`는 **직접 이어받은 바로 이전 row만** 적는다
- `successor_catalog_ids[]`는 **직접 갈라지거나 합쳐진 다음 row만** 적는다
- grandparent나 grandchild를 convenience 때문에 direct predecessor/successor로 복사하지 않는다
- split/merge가 생겨도 기존 edge를 지우지 않고 append-only로 남긴다

예를 들어 `A -> B -> C`로 successor chain이 이어지면 링크는 이렇게 유지하는 편이 맞다.

```yaml
shadow_catalog_entries:
  - catalog_id: shadow-release-approval-001
    lineage:
      lineage_root_id: shadow-release-approval-001
      predecessor_catalog_ids: []
      successor_catalog_ids:
        - shadow-release-approval-001a
  - catalog_id: shadow-release-approval-001a
    lineage:
      lineage_root_id: shadow-release-approval-001
      predecessor_catalog_ids:
        - shadow-release-approval-001
      successor_catalog_ids:
        - shadow-release-approval-001b
  - catalog_id: shadow-release-approval-001b
    lineage:
      lineage_root_id: shadow-release-approval-001
      predecessor_catalog_ids:
        - shadow-release-approval-001a
      successor_catalog_ids: []
```

중간에 `B`를 건너뛰고 `C.predecessor_catalog_ids[]`에 `A`를 직접 넣으면 lineage는 더 많아 보일 수 있어도, 실제 계승 관계는 덜 정확해진다.

split/merge에서도 같은 원칙을 적용한다.

- split: predecessor 하나가 `successor_catalog_ids[]`에 여러 id를 갖고, 각 successor는 같은 predecessor를 직접 가리킨다
- merge: 여러 predecessor가 같은 successor id를 `successor_catalog_ids[]`에 append하고, successor는 그 predecessor들을 모두 직접 가리킨다

그리고 review outcome에도 edge를 같은 방향으로 남기는 편이 좋다.

- predecessor를 닫는 outcome에는 `successor_catalog_id`
- successor를 여는 outcome에는 `predecessor_catalog_id`
- reopen outcome에는 successor link가 아니라 `reopen_reason`과 `history.reopen_events[]` append

이렇게 해야 entry schema, review outcome, lineage graph가 서로 다른 계승 관계를 말하지 않는다.

---

## 판단 표

| 질문 | `yes`면 어디에 가깝나 | 비고 |
|---|---|---|
| 같은 shadow path인가 | reopen | DM은 DM끼리, spreadsheet는 spreadsheet끼리 continuity를 본다 |
| 같은 replacement path와 exit condition인가 | reopen | 같은 proof metric을 계속 쓸 수 있어야 한다 |
| scope/owner/forum이 실질적으로 같나 | reopen | 단순 owner 교체만으로 successor를 만들지 않는다 |
| new baseline snapshot이 필요한가 | successor | 새로운 종료 규칙이 필요하다는 뜻이다 |
| split/merge가 생겼나 | successor | one-to-many, many-to-one lineage가 필요하다 |
| old proof를 남겨야 현재 truth가 정직한가 | successor | history overwrite 위험이 크면 successor가 안전하다 |

실무에서는 첫 세 질문이 모두 `yes`면 reopen, 뒤 세 질문 중 하나라도 강하게 `yes`면 successor가 맞는 경우가 많다.

### 빠른 운영 알고리즘

1. current state가 아직 active인지, 이미 `retired`였는지 먼저 본다.
2. active state면 같은 row update/rollback으로 충분한지 먼저 판단한다.
3. old row의 `retired_at`, `proof_ref`, `baseline_snapshot_ref`를 먼저 freeze한다.
4. 같은 `current_path`와 같은 `replacement_path`를 같은 proof rule로 다시 닫을 수 있으면 reopen 후보로 둔다.
5. 새 baseline, 새 owner map, split/merge backlog가 필요하면 successor로 전환한다.
6. reopen이면 `history.reopen_events[]`를 append하고, successor면 predecessor/successor 인접 링크를 append한다.
7. 둘 다 애매하면 old proof를 덮어쓰지 않는 쪽, 즉 successor를 기본값으로 둔다.

---

## 실전 시나리오

### 시나리오 1: 같은 DM 승인 우회가 두 달 뒤 다시 나타난다

- old path: `slack_dm`
- replacement: `override_registry`
- recurrence: 동일한 승인자와 동일한 DM 경로

이 경우는 successor보다 reopen이 맞다.
지난번 retirement proof가 durable하지 않았다는 뜻이므로 같은 `catalog_id`를 다시 열고, `history.reopen_events[]`에 이번 recurrence를 남기는 편이 정확하다.

### 시나리오 2: DM은 없어졌지만 spreadsheet allowlist가 새 source of truth가 된다

- old path: `slack_dm`
- new path: `personal_sheet`
- replacement: 기존 registry가 아니라 policy control plane 확장 필요

이 경우는 successor가 맞다.
표면적으로는 같은 release override family지만, 실제 shadow path와 replacement backlog가 모두 바뀌었다.

### 시나리오 3: 한 global shadow process가 조직 개편 뒤 두 service별 shadow path로 쪼개진다

- predecessor: global manual override sheet
- successors: payments override sheet, delivery override sheet

이 경우 same-entry reopen은 owner와 due date를 왜곡한다.
predecessor는 history로 남기고, 서비스별 successor 두 개를 만드는 편이 맞다.

### 시나리오 4: `verification_pending`에서 같은 DM path recurrence가 다시 잡힌다

- current state: `verification_pending`
- recurrence: 같은 승인자, 같은 `slack_dm`, 같은 `override_registry` 미정착
- closeout 여부: 아직 `retired` 판정 전

이 경우는 successor보다 same-entry rollback이 맞다.
새 혈통이 생긴 것이 아니라, 기존 closeout window가 실패한 것이므로 같은 `catalog_id`를 `cataloged` 또는 `decision_pending`으로 되돌리고 fresh `signal_evidence`와 rollback outcome을 append하는 편이 정확하다.

---

## 코드로 보기

```yaml
shadow_catalog_entry:
  catalog_id: shadow-release-approval-001
  title: manual_release_override_via_slack_dm
  lifecycle_state: cataloged
  decision: absorb
  replacement_path: override_registry
  lineage:
    lineage_root_id: shadow-release-approval-001
    predecessor_catalog_ids: []
    successor_catalog_ids: []
  history:
    reopen_events:
      - reopened_at: 2026-07-14
        from_state: retired
        reopen_reason: same_slack_dm_path_recurred
        recurrence_evidence_ref: INC-912
    retirement_attempts:
      - retired_at: 2026-06-01
        proof_ref: shadow-proof-2026-06-01
        baseline_snapshot_ref: baseline-2026-05-01
        verification_window: 30d
```

```yaml
shadow_catalog_entry:
  catalog_id: shadow-release-approval-001a
  title: release_override_allowlist_via_personal_sheet
  lifecycle_state: cataloged
  decision: absorb
  replacement_path: policy_control_plane_override_module
  lineage:
    lineage_root_id: shadow-release-approval-001
    predecessor_catalog_ids:
      - shadow-release-approval-001
    successor_catalog_ids: []
  history:
    reopen_events: []
    retirement_attempts: []
```

첫 번째는 reopen이다.
두 번째는 successor다.
둘의 차이는 이름이 아니라 **같은 종료 규칙을 계속 쓸 수 있는가**다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 무조건 reopen | recurrence trend가 한 row에 모인다 | history overwrite와 false continuity가 생긴다 | 권장하지 않는다 |
| 무조건 successor | audit trail이 보수적으로 남는다 | 사실상 같은 문제를 매번 새로 발견한 것처럼 보이게 한다 | 권장하지 않는다 |
| reopen/successor 규칙 분리 | continuity와 history를 같이 지킨다 | lineage field와 review discipline이 필요하다 | 권장 기본형 |

shadow catalog reopen and successor rules의 목적은 recurrence를 예쁘게 분류하는 것이 아니라, **같은 문제의 재발과 다른 변종의 계승을 구분해 learning loop를 보존하는 것**이다.

---

## 꼬리질문

- 이 recurrence를 같은 `replacement_path`와 같은 `exit_condition`으로 계속 관리할 수 있는가?
- 같은 shadow path가 다시 살아난 것인가, 아니면 새로운 off-plane state store가 등장한 것인가?
- predecessor를 그대로 두지 않으면 past retirement proof가 사라지지는 않는가?
- split/merge 때문에 한 row가 owner와 due date를 왜곡하고 있지는 않은가?
- review packet이 `lineage_action_proposed`를 직접 묻고 있는가?

## 한 줄 정리

Shadow Catalog Reopen and Successor Rules는 recurrence가 보였을 때 같은 shadow identity의 실패는 reopen으로, 구조적으로 달라진 후속 변종은 successor entry로 처리해 lineage와 history를 함께 보존하는 운영 기준이다.
