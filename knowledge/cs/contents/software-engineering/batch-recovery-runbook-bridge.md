# Batch Recovery Runbook Bridge

> 한 줄 요약: batch 실패 정책은 코드 안의 retry 규칙으로 끝나지 않고, 운영자가 어떤 상태를 확인하고 언제 멈추며 어떤 조건에서 다시 실행해도 되는지까지 runbook 언어로 연결돼야 한다.

**난이도: 🟢 Beginner**

[Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)에서 per-item retry, retry queue, checkpoint를 구분했다면, 이 문서는 그다음 질문인 "그 정책을 운영자가 따라 할 runbook으로 어떻게 바꿀까"만 좁혀서 본다.
실패 reason code를 `retryable`, `manual-review`, `permanent` 세 묶음으로 먼저 단순화하고 싶다면 [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)를 같이 보면 runbook의 분기 문장을 더 짧게 적기 쉽다.
실제 결과 타입 이름이 필요하면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 먼저 보고, 재실행 중복 부작용이 걱정되면 [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)를 같이 보면 된다.
beginner 기준으로는 [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)에서 retryable/manual-review/terminal 분기부터 잠그고, 이어서 [Batch Result Testing Checklist](./batch-result-testing-checklist.md)에서 duplicate run start, chunk timeout retry, item dedup recovery까지 넓히면 정책 -> runbook -> 테스트 루프가 짧게 이어진다.
runbook, playbook, automation의 일반 경계는 [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)로 이어서 보면 된다.

<details>
<summary>Table of Contents</summary>

- [먼저 한 장면으로 이해하기](#먼저-한-장면으로-이해하기)
- [정책 결정을 runbook 단계로 바꾸기](#정책-결정을-runbook-단계로-바꾸기)
- [operator가 처음 확인할 것](#operator가-처음-확인할-것)
- [stop condition은 실패를 키우지 않는 안전장치다](#stop-condition은-실패를-키우지-않는-안전장치다)
- [safe rerun checklist](#safe-rerun-checklist)
- [rerun 뒤 확인할 completion check](#rerun-뒤-확인할-completion-check)
- [runbook에 바로 붙일 템플릿](#runbook에-바로-붙일-템플릿)
- [짧은 예시: 상품 동기화 batch](#짧은-예시-상품-동기화-batch)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: Batch Recovery Runbook Bridge](./README.md#batch-recovery-runbook-bridge)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Primer On Retry Reason Taxonomy](./retry-reason-taxonomy-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)
> - [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
> - [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
>
> retrieval-anchor-keywords:
> - batch recovery runbook bridge
> - batch failure runbook
> - batch rerun checklist
> - safe batch rerun
> - duplicate safe batch rerun
> - batch stop condition
> - operator batch recovery
> - batch recovery operator steps
> - batch runbook primer
> - batch failure policy to runbook
> - batch runbook to retry queue assertions
> - batch runbook to batch result testing
> - checkpoint resume runbook
> - retry queue operator action
> - run summary manual review
> - batch safe rerun checks beginner
> - partial failure operations bridge
> - batch rerun preflight checklist
> - batch rerun completion check
> - batch resume vs new run
> - operator batch runbook template
> - batch stop or rerun decision

## 먼저 한 장면으로 이해하기

초심자 batch 복구에서 가장 흔한 위험은 "실패했으니 한 번 더 돌리자"로 바로 가는 것이다.
하지만 운영자에게 필요한 첫 질문은 실행 버튼이 아니다.

- **지금 더 돌리면 피해가 커지는가**
- **어디까지 끝났는가**
- **무엇을 고친 뒤 다시 돌려야 하는가**
- **같은 일을 두 번 하지 않는다는 근거가 있는가**

batch 실패 정책은 이 질문에 답하는 코드 쪽 언어다.
runbook은 같은 결정을 사람이 따라 할 수 있게 바꾼 운영 쪽 언어다.

간단히 말하면:

- policy는 "어떤 실패를 retry/resume/manual review로 보낼까"를 정한다
- runbook은 "operator가 어떤 증거를 보고 어떤 버튼을 눌러도 되는가"를 정한다

둘이 연결되지 않으면 코드에는 retry queue가 있어도 운영자는 전체 재실행을 눌러 버릴 수 있다.
반대로 runbook에 "재실행"만 있으면 checkpoint와 idempotency가 준비됐는지 확인하지 못한다.

## 정책 결정을 runbook 단계로 바꾸기

먼저 실패 정책을 운영자 행동으로 번역해 보자.
beginner runbook에서는 아래 다섯 칸만 연결되면 된다.

| 정책 판단 | operator가 runbook에서 먼저 하는 말 | stop condition | safe rerun 근거 | 다시 실행 단위 |
|---|---|---|---|---|
| pure per-item retry | 실패 item 목록과 `reasonCode`를 보고 retryable만 고른다 | 같은 item이 반복 실패하거나 downstream이 계속 불안정하다 | 같은 item-level key로 재처리 가능하다 | item ids |
| chunk summary 필요 | 실패 chunk의 성공/실패 수와 원인 분류를 먼저 확인한다 | 실패 분류가 섞여 있어 retryable/manual-review 경계가 흐리다 | retry 대상 chunk와 성공한 chunk가 구분돼 있다 | chunk 또는 chunk 안 retryable items |
| retry queue 필요 | main run을 닫고 backlog owner와 수동 확인 대상을 분리한다 | manual-review 대상이 retry queue에 섞여 있다 | queue entry가 같은 item key와 다음 액션을 같이 가진다 | retry queue backlog |
| checkpoint resume 필요 | `latestCheckpoint`, `snapshotTime`, `runId`가 같은지 확인하고 이어 간다 | checkpoint가 없거나 snapshot 기준이 달라졌다 | 같은 run key와 durable checkpoint가 남아 있다 | same run + next cursor |
| unsafe failure | kill switch, write stop, escalation을 먼저 실행한다 | receipt 불일치, 중복 write 의심, 데이터 오염 신호가 있다 | reconciliation과 owner 확인 전에는 rerun하지 않는다 | rerun 금지 |

이 표의 핵심은 "재실행"이 하나가 아니라는 점이다.
item만 다시 돌리는 것, chunk를 다시 제출하는 것, 같은 run을 checkpoint부터 이어 가는 것, 새 run을 시작하는 것은 서로 다른 행동이다.

runbook이 초심자에게 쉬우려면 정책 이름보다 문장이 바로 보여야 한다.

- `retryable timeout`이면 "같은 item key로 backlog만 다시 넣는다"
- `manual-review validation`이면 "자동 rerun하지 말고 backlog를 분리한다"
- `checkpoint resume`이면 "같은 snapshot인지 먼저 본다"
- `unsafe mismatch`이면 "멈추고 reconcile한다"

## operator가 처음 확인할 것

runbook 첫 페이지는 긴 설명보다 확인 순서가 중요하다.
아래 네 가지를 먼저 보게 만들면 beginner도 위험한 재실행을 줄일 수 있다.

| 확인 항목 | 보는 증거 | 왜 필요한가 |
|---|---|---|
| 영향 범위 | alert, error rate, failed item count, affected tenant | 계속 실행하면 피해가 커지는지 판단한다 |
| 진행 지점 | `RunSummary.latestCheckpoint`, completed chunk | 어디서 이어야 하는지 확인한다 |
| 실패 분류 | `RetryCandidate.reasonCode`, transient/permanent/manual-review | 바로 재시도할 대상과 사람이 봐야 할 대상을 나눈다 |
| 중복 방지 근거 | run/chunk/item idempotency key, external receipt | 재실행이 같은 부작용을 두 번 만들지 않는지 확인한다 |

이 증거가 없다면 runbook은 "복구 절차"가 아니라 추측 순서가 된다.
특히 결제, 정산, 알림, 외부 API write처럼 부작용이 큰 batch에서는 확인 항목 없이 rerun 버튼부터 누르면 안 된다.

## stop condition은 실패를 키우지 않는 안전장치다

stop condition은 "실패하면 멈춘다"라는 막연한 문장이 아니다.
operator가 더 이상 retry/resume하지 말아야 하는 구체적인 조건이다.

예:

- 같은 item에서 idempotency key 조회가 실패한다
- 실패 원인이 transient timeout이 아니라 validation 또는 data corruption이다
- 실패율이 정해진 임계값을 넘고, downstream도 오류를 내고 있다
- checkpoint가 없거나 snapshot 기준이 달라졌다
- 외부 시스템 receipt와 내부 성공 기록이 서로 맞지 않는다
- write path가 잘못된 데이터를 계속 만들고 있다

이 조건에 걸리면 runbook은 재실행이 아니라 stop path로 이동해야 한다.

| stop path | 언제 쓰는가 | 다음 행동 |
|---|---|---|
| pause scheduler | 다음 batch가 피해를 키울 수 있다 | 같은 job의 자동 실행을 잠시 막는다 |
| kill switch | write, payment, notification 같은 부작용 확산이 있다 | 위험한 side effect를 즉시 차단한다 |
| manual review | 데이터 오류나 policy 판단이 필요하다 | retry queue에서 사람이 볼 backlog로 넘긴다 |
| escalation | operator가 판단할 권한이나 정보가 부족하다 | owner/on-call에게 run summary와 증거를 전달한다 |

좋은 runbook은 성공 절차만 적지 않는다.
"여기서 멈춰야 한다"를 명확히 적어야 초심자도 안전하게 운영할 수 있다.

## safe rerun checklist

재실행 전에는 아래 질문에 모두 답해야 한다.
한 항목이라도 애매하면 바로 전체 rerun으로 가지 말고 stop path나 manual review로 넘긴다.

- 같은 run을 이어 가는가, 실패 item만 다시 처리하는가, 새 run을 시작하는가?
- 대상 snapshot, cutoff time, backfill range가 원래 run과 같은가?
- 마지막 completed checkpoint가 durable하게 저장돼 있는가?
- 이미 성공한 item의 idempotency key나 receipt를 조회할 수 있는가?
- 실패 item이 retryable, manual-review, permanent-failure로 분류돼 있는가?
- retry queue에 넣을 때 같은 item-level idempotency key를 재사용하는가?
- 외부 API나 downstream이 회복됐다는 확인 근거가 있는가?
- 재실행 후 확인할 성공 기준과 중단 기준이 runbook에 있는가?

짧게 줄이면 safe rerun은 세 가지를 확인하는 일이다.

1. **같은 대상인지** 확인한다.
2. **이미 끝난 일을 건너뛸 수 있는지** 확인한다.
3. **다시 실패하면 어디서 멈출지** 확인한다.

## rerun 뒤 확인할 completion check

safe rerun은 "다시 시작해도 되는가"에서 끝나지 않는다.
rerun 뒤에 무엇을 확인할지도 runbook에 있어야 한다.

| rerun 뒤 확인 질문 | 왜 필요한가 | 이상하면 어디로 가야 하나 |
|---|---|---|
| 성공 수와 실패 수가 예상 범위로 돌아왔는가 | 겉보기 성공인데 일부 누락이 남을 수 있다 | summary 재검토 후 checkpoint/resume 판단 |
| manual-review backlog가 줄었는가, 아니면 그대로 남았는가 | retry가 사람 검토 대상을 몰래 삼키면 안 된다 | backlog 분리 상태 재확인 |
| 중복 receipt, 중복 전송, 중복 write가 생기지 않았는가 | rerun이 새 장애를 만들었는지 확인한다 | kill switch 또는 reconciliation |
| stop condition 임계값이 다시 올라가지 않았는가 | rerun 중 재발을 놓치지 않게 한다 | pause scheduler 후 escalation |

즉 runbook은 `rerun preflight`와 `rerun after-check`가 한 세트여야 한다.
앞쪽만 있고 뒤쪽이 없으면 "돌리긴 했는데 정말 복구됐는가"를 설명하지 못한다.

## runbook에 바로 붙일 템플릿

아래처럼 다섯 줄만 채워도 초심자용 runbook 뼈대가 생긴다.

```markdown
## Batch Failure Recovery
- Trigger: 어떤 alert/run summary를 보고 이 runbook을 시작하는가
- First checks: runId, snapshotTime, latestCheckpoint, failed item/chunk, reasonCode
- Stop now if: receipt 불일치, checkpoint 없음, snapshot drift, write 오염 징후
- Safe rerun only if: 같은 대상 확인, 같은 idempotency key/receipt 조회 가능, downstream 회복 확인
- After rerun confirm: success/failure count, manual-review backlog, duplicate side effect 없음
```

좋은 runbook 문장은 추상적이지 않다.

| 약한 문장 | 더 안전한 문장 |
|---|---|
| 실패하면 다시 실행한다 | `snapshotTime`이 같고 `latestCheckpoint`가 있으면 chunk 3부터 resume한다 |
| 계속 실패하면 담당자에게 문의한다 | receipt 조회 실패나 duplicate 의심이 있으면 scheduler를 pause하고 owner에게 escalate한다 |
| timeout은 재시도한다 | `partner-timeout`만 retry queue로 보내고 validation 오류는 manual review로 남긴다 |

## 짧은 예시: 상품 동기화 batch

상황:

- 오전 9시 snapshot 상품 1,200개를 300개씩 네 chunk로 partner API에 동기화한다
- chunk 2에서 timeout 9건, validation 오류 3건이 발생했다
- chunk 3 처리 중 서버가 죽었다

나쁜 runbook은 이렇게 끝난다.

```text
1. 실패하면 batch를 다시 실행한다.
2. 계속 실패하면 담당자에게 문의한다.
```

이 문서는 빠르지만 위험하다.
어떤 대상부터 다시 돌릴지, validation 오류 3건을 어떻게 분리할지, 이미 partner에 반영된 item을 어떻게 피할지 말하지 않는다.

더 안전한 beginner runbook은 이렇게 쓴다.

```text
1. RunSummary에서 runId와 snapshotTime이 product-sync:09:00인지 확인한다.
2. latestCheckpoint가 after chunk 2인지 확인한다.
3. chunk 2의 timeout 9건은 RetryCandidate로 retry queue에 넣는다.
4. validation 오류 3건은 manual review 상태로 두고 자동 retry하지 않는다.
5. chunk 3부터 resume하되 같은 run-level key와 chunk/item idempotency key를 사용한다.
6. 실패율이 5%를 넘거나 partner receipt 조회가 실패하면 scheduler를 pause하고 escalate한다.
```

여기서 중요한 것은 명령어 모양이 아니다.
정책 판단이 operator 행동으로 바뀌었다는 점이다.

- timeout은 retry queue
- validation 오류는 manual review
- 서버 crash는 checkpoint resume
- receipt 불일치는 stop condition

## 자주 하는 오해

| 오해 | 더 안전한 판단 |
|---|---|
| runbook은 "다시 실행하는 방법"만 있으면 된다 | 언제 멈출지와 무엇을 확인할지도 있어야 한다 |
| retry queue가 있으면 operator는 볼 것이 없다 | 어떤 실패를 queue로 보냈는지, manual review가 남았는지 확인해야 한다 |
| checkpoint가 있으면 전체 rerun도 안전하다 | checkpoint resume과 new run은 다르며 idempotency 근거가 필요하다 |
| transient timeout은 무조건 자동 retry해도 된다 | downstream 장애가 진행 중이면 retry가 피해를 키울 수 있다 |
| stop condition은 advanced 운영에서만 필요하다 | beginner runbook일수록 멈춤 기준이 명확해야 실수를 줄인다 |

## 기억할 기준

batch recovery runbook은 code policy를 사람이 따라 할 수 있게 바꾼 문서다.

- failure policy가 "무엇을 retry/resume/manual review로 보낼까"를 정한다
- result model이 "operator가 무엇을 보고 판단할까"를 남긴다
- idempotency key가 "다시 실행해도 중복 부작용이 없을까"를 증명한다
- stop condition이 "지금은 더 돌리면 안 된다"를 알려 준다

따라서 beginner에게는 한 문장만 먼저 잡아 주면 된다.

**batch 복구는 rerun 버튼을 찾는 일이 아니라, 증거를 보고 안전한 다음 행동을 고르는 일이다.**
