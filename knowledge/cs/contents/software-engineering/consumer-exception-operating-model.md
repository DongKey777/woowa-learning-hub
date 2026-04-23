# Consumer Exception Operating Model

> 한 줄 요약: consumer exception을 운영 가능한 backlog로 유지하려면 registry schema, state machine, review cadence, automation quality gate가 끊기지 않는 하나의 operating model이어야 하며, 각 예외는 owner, evidence, expiry, closure verification을 계속 갱신해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consumer Exception Registry Templates](./consumer-exception-registry-templates.md)
> - [Consumer Exception State Machine and Review Cadence](./consumer-exception-state-machine-review-cadence.md)
> - [Consumer Exception Registry Quality and Automation](./consumer-exception-registry-quality-automation.md)
> - [Backward Compatibility Waivers and Consumer Exception Governance](./backward-compatibility-waiver-consumer-exception-governance.md)
> - [Override Burn-Down and Exemption Debt](./override-burn-down-and-exemption-debt.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)
> - [Support SLA and Escalation Contracts](./support-sla-escalation-contracts.md)
> - [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)
> - [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)
> - [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)

> retrieval-anchor-keywords:
> - consumer exception operating model
> - exception operating rhythm
> - registry state machine cadence
> - exception review forum
> - exception quality gate
> - closure verification
> - repeated extension governance
> - consumer waiver operating model
> - retire exception bypass
> - absorb exception data path
> - sunset extension governance
> - waiver control plane absorb

## 핵심 개념

consumer exception 운영이 무너지는 방식은 대개 비슷하다.

- registry는 있는데 owner와 expiry가 낡는다
- state는 있는데 transition 기준이 약하다
- review 회의는 있는데 expiring/blocked item이 먼저 안 보인다
- automation은 있는데 입력 validation만 하고 closure verification은 못 한다

그래서 consumer exception은 문서 몇 장이 아니라 **record, decision, review, verification을 묶은 operating model**로 다뤄야 한다.

---

## 깊이 들어가기

### 1. registry는 static catalog가 아니라 운영 레코드여야 한다

좋은 registry record는 최소한 네 묶음으로 보인다.

- identity: exception id, consumer, contract/api, exception type
- responsibility: owner, escalation owner, support contact, producer counterpart
- timebox: created_at, expires_at, next_review_at, max_extension_count
- evidence: current workaround, old path usage, replacement readiness, last_verified_at

이렇게 구분해야 review가 "이 예외가 존재하는가"가 아니라 **누가 언제 어떤 근거로 계속 들고 있는가**를 바로 본다.

특히 `next_review_at`, `last_verified_at`, `max_extension_count` 같은 운영 필드가 없으면 registry는 state machine과 automation으로 연결되기 어렵다.

### 2. state machine은 label이 아니라 decision checkpoint다

자주 쓰는 상태는 비슷해도 entry/exit 기준이 명확해야 한다.

- proposed: 필수 필드와 종료 조건이 아직 완성되지 않았거나 승인 전인 상태
- approved: time-box와 compensating control은 승인됐지만 운영 경로에 아직 반영되지 않은 상태
- active: 예외가 실제 트래픽 또는 운영 경로에서 사용 중인 상태
- expiring: 만료가 임박했거나 extension budget을 거의 다 쓴 상태
- blocked: consumer, producer, platform 중 하나의 선행 작업이 막혀 종료가 멈춘 상태
- closed: traffic, allowlist, support contract, follow-up task까지 검증돼 종료된 상태

중요한 것은 상태 이름보다 **허용 전이**다.

- `proposed -> active`를 승인 없이 열지 않는다
- `active -> closed`는 usage 0, allowlist 제거, closure evidence 없이는 막는다
- `expiring -> active` 재연장은 sponsor sign-off나 escalation 없이 허용하지 않는다
- `blocked`는 "그냥 늦음"이 아니라 escalation owner와 next action이 필수다

### 3. review cadence는 단일 회의가 아니라 layered forum이어야 한다

consumer exception review는 cadence를 한 줄로 정하면 잘 안 굴러간다.
결정 종류가 다르기 때문이다.

| forum | cadence | 보는 항목 | 출력 |
|---|---|---|---|
| intake review | weekly | proposed, incomplete record, reject/approve 판단 | approved 전환, missing data fix |
| exception working review | weekly | expiring, blocked, repeated extension | escalation, support action, extension decision |
| portfolio scorecard review | monthly | age bucket, repeated owner, same contract concentration | burn-down target, migration reprioritization |
| policy or architecture forum | quarterly | repeated pattern, permanent carve-out 후보 | policy redesign, funding, sunset date 조정 |

이렇게 나누면 weekly review는 당장 움직여야 할 예외에 집중하고, monthly/quarterly review는 구조 문제를 다룰 수 있다.

### 4. automation quality gate는 write-time, drift-time, closure-time으로 나눠야 한다

좋은 자동화는 입력 validation 하나로 끝나지 않는다.

write-time gate 예:

- required field missing
- invalid owner/team/contract id
- expires_at 없음 또는 정책 허용 범위 초과
- invalid state transition
- support path 미등록

drift-time gate 예:

- next_review_at missed
- expires_at 14일 이내
- owner metadata stale
- blocked인데 escalation owner 없음
- closed인데 old path traffic 존재
- extension count가 상한 초과

closure-time gate 예:

- replacement path usage verified
- old path usage 0 for N days
- allowlist or producer flag removed
- open support playbook/ticket 없음
- deprecation or migration follow-up task done

즉 automation의 목적은 "오류를 보여 주기"보다 **review queue와 reopen 조건을 분명히 만드는 것**이다.

### 5. repeated exception path는 retire할지 absorb할지 review forum이 판정해야 한다

consumer exception backlog가 커지면 부수 경로도 생긴다.
슬랙 승인, 팀별 시트, 임시 allowlist 메모, producer 개인 노트 같은 것들이다.

이때 모든 반복 패턴을 productize하면 과잉 제어면이 생기고, 반대로 전부 정리만 하자고 하면 실제 운영 수요를 놓친다.
그래서 review forum은 다음 두 질문을 같은 언어로 써야 한다.

- 공식 registry/state machine/review cadence가 이미 있는데 사람들이 우회하는가 -> **retire**
- 반복되는 structured exception data가 공식 schema나 control plane에 못 들어가고 있는가 -> **absorb**

예를 들어 deprecation 연장 승인을 DM으로만 받는다면 그것은 [Service Deprecation and Sunset Lifecycle](./service-deprecation-sunset-lifecycle.md)과 [Deprecation Enforcement, Tombstone, and Sunset Guardrails](./deprecation-enforcement-tombstone-guardrails.md)로 돌아가야 할 **retire 대상 bypass**다.
반대로 여러 consumer가 같은 `allowlist_scope`, `replacement_path`, `extension_count`, `sunset_stage` 필드를 바깥 시트에 적고 있다면 그것은 registry schema와 automation에 넣어야 할 **absorb 대상 capability gap**이다.

이 판정 언어를 [Shadow Process Officialization and Absorption Criteria](./shadow-process-officialization-absorption-criteria.md)와 맞춰 두면 weekly review와 quarterly policy forum이 같은 현상을 다른 이름으로 중복 논의하지 않게 된다.

### 6. scorecard는 예외 건수보다 운영 건강을 보여 줘야 한다

운영 모델이 살아 있는지는 count보다 다음 지표로 더 잘 드러난다.

- missing expiry ratio
- expiring without review count
- blocked without escalation owner count
- repeated extension ratio
- closed-but-traffic-present count
- median days in `expiring` / `blocked`

이런 지표가 monthly review와 quarterly forum에 연결되지 않으면, review cadence는 회의 일정만 남고 operating model은 금방 형식화된다.

---

## 실전 시나리오

### 시나리오 1: 모바일 consumer가 네 번째 연장을 요청한다

이 예외는 단순 active가 아니라 `expiring -> blocked`로 재분류하고, weekly working review에서 sponsor escalation을 건다.
monthly review에서는 repeated extension consumer로 scorecard에 올려 migration sponsor 또는 compatibility shim 여부를 결정해야 한다.

### 시나리오 2: closed 처리한 예외에서 old traffic이 다시 보인다

closure-time gate가 reopen을 트리거해야 한다.
이 경우 바로 `closed -> blocked` 또는 `closed -> active`로 되돌리는 기준을 정해 두지 않으면 registry 신뢰가 급격히 떨어진다.

### 시나리오 3: 조직 개편 후 owner/team metadata가 깨진다

개별 문서 수정보다 drift-time automation이 먼저 stale owner queue를 만들어야 한다.
그 다음 weekly intake review에서 owner reassignment를 일괄 처리해야 review cadence가 회복된다.

---

## 코드로 보기

```yaml
consumer_exception:
  id: ex-mobile-v5-order-status
  type: compatibility_waiver
  consumer: mobile-app-v5
  contract: order-status-v4
  status: expiring
  owner: mobile-platform
  escalation_owner: migration-steering
  support_contact: "#mobile-api-support"
  expires_at: 2026-05-01
  next_review_at: 2026-04-18
  max_extension_count: 3
  extension_count: 4
  evidence:
    old_path_usage_qps: 12
    replacement_ready: false
    last_verified_at: 2026-04-14
  quality_gates:
    - rule: extension_count_exceeded
      action: escalate
    - rule: expiring_with_traffic
      action: weekly_review
    - rule: close_requires_zero_traffic_14d
      action: block_transition
```

좋은 operating model은 예외를 저장하는 것보다 **언제 queue로 올리고 언제 닫기를 막을지**를 더 명확히 보여 준다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| ticket + spreadsheet | 시작이 빠르다 | 상태, cadence, verification이 끊긴다 | 매우 초기 |
| registry + review meeting | 가시성은 생긴다 | stale data와 weak closure가 남는다 | 기본 운영 |
| integrated operating model | queue와 종료가 선명하다 | metadata, telemetry, forum 연결이 필요하다 | 예외가 누적되는 조직 |

consumer exception operating model의 목적은 예외를 많이 기록하는 것이 아니라, **예외가 언제 포트폴리오 리스크가 되고 언제 구조 수정으로 넘어가야 하는지 반복 가능하게 판단하는 것**이다.

---

## 꼬리질문

- registry record에 `next_review_at`, `last_verified_at`, `max_extension_count`가 있는가?
- expiring과 blocked 예외가 weekly review에서 가장 먼저 보이는가?
- close 전이가 telemetry와 allowlist 제거로 검증되는가?
- repeated extension pattern이 monthly or quarterly forum으로 올라가는가?
- 반복 예외 경로가 bypass라서 retire해야 하는지, capability gap이라서 absorb해야 하는지 구분되고 있는가?

## 한 줄 정리

Consumer exception operating model은 registry, state machine, review cadence, automation quality gate를 한 루프로 묶어 예외를 임시 메모가 아니라 종료와 escalation이 가능한 운영 backlog로 만드는 구조다.
