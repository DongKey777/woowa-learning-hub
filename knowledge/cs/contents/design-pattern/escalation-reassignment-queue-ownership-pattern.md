# Escalation, Reassignment, and Queue Ownership Pattern

> 한 줄 요약: human approval workflow의 진짜 난점은 승인 버튼이 아니라, 어떤 work item이 어느 큐에 들어가고 누가 lease를 잡아 처리하며 SLA 위반·권한 부족·교대 시 누가 재할당과 에스컬레이션을 실행할지 설명 가능한 operator contract를 만드는 일이다.

**난이도: 🔴 Expert**

> 관련 문서:
> - [Human Approval and Manual Review Workflow Pattern](./human-approval-manual-review-workflow-pattern.md)
> - [Workflow Owner vs Participant Context](./workflow-owner-vs-participant-context.md)
> - [Process Manager Deadlines and Timeouts](./process-manager-deadlines-timeouts.md)
> - [Process Manager State Store and Recovery Pattern](./process-manager-state-store-recovery.md)
> - [Semantic Lock and Pending State Pattern](./semantic-lock-pending-state-pattern.md)
> - [Process Manager vs Saga Coordinator](./process-manager-vs-saga-coordinator.md)
> - [Compensation vs Reconciliation Pattern](./compensation-vs-reconciliation-pattern.md)

---

## 핵심 개념

manual review를 넣고 나면 문제는 "누가 승인하나"에서 끝나지 않는다.

- 어떤 기준으로 어떤 queue에 들어가나
- 누가 claim하고 얼마나 오래 잡고 있을 수 있나
- reviewer가 자리를 비우면 언제 자동 반환되나
- SLA를 넘기면 어느 팀이나 권한 계층으로 escalate하나
- queue 운영자와 최종 approver의 권한은 어디서 갈리나

즉 `UNDER_REVIEW`라는 상태 하나만으로는 부족하고, **queue ownership, reassignment, escalation, human approval authority, workflow operator contract**가 함께 필요하다.

### Retrieval Anchors

- `workflow queue ownership`
- `queue ownership`
- `review reassignment`
- `manual review escalation`
- `approval queue routing`
- `sla breach escalation`
- `review work claiming`
- `review lease timeout`
- `workflow operator contract`
- `queue owner vs approver`
- `manual review handoff`
- `queue ownership audit`

---

## 깊이 들어가기

### 1. queue ownership, workflow ownership, approval authority는 서로 다른 질문이다

manual review workflow에서는 적어도 세 층의 ownership을 구분해야 한다.

- workflow owner: 전체 상태, timeout, reminder, 다음 participant 호출을 해석한다
- queue owner: 어떤 큐가 어떤 아이템을 받아야 하는지, capacity와 routing을 운영한다
- decision authority: approve/reject/override를 실제로 결정할 권한을 가진다

이 셋을 섞으면 흔히 이런 문제가 생긴다.

- queue 운영자가 최종 승인까지 해 버린다
- workflow owner가 각 팀의 근무표와 capacity까지 떠안는다
- approver가 assignment 변경까지 직접 하며 audit 의미가 흐려진다

핵심은 `누가 work item을 본다`와 `누가 business decision을 확정한다`를 분리하는 것이다.

### 2. assignment는 영구 소유권보다 lease에 가깝다

queue item을 한 번 잡았다고 영구히 개인 소유가 되는 모델은 운영 drift를 만든다.  
실무에서는 claim을 보통 lease처럼 다루는 편이 안전하다.

- claim 시작 시각
- lease 만료 시각
- 연장 heartbeat 여부
- release reason
- abandoned work recovery 규칙

push assignment든 pull/claim이든 다음 계약이 없다면 곧 중복 처리나 방치가 생긴다.

- claim timeout이 지나면 자동 반납되는가
- 이미 claim된 아이템을 다른 운영자가 볼 수 있는가
- 오랫동안 inactivity면 team queue로 되돌리는가
- 동일 아이템의 duplicate claim을 어떻게 막는가

즉 ownership은 "사람에게 붙였다"보다 **언제까지 유효한 작업 점유권인가**로 보는 편이 낫다.

### 3. reassignment는 장애 복구가 아니라 정상 운영 루프다

리뷰어 부재, 교대, 휴가, overload, skill mismatch, 이해상충은 예외가 아니라 흔한 운영 현실이다.

- 개인 inbox -> 팀 queue 복귀
- 팀 queue -> specialist queue 이동
- shift 종료 -> 다음 shift queue handoff
- conflict of interest 탐지 -> 다른 reviewer로 교체
- overload 감지 -> parallel queue로 spillover

그래서 reassignment는 error handling 부속물이 아니라 **처리 용량을 유지하기 위한 기본 control loop**다.

중요한 점은 reassignment가 바꾸는 것은 대개 assignment metadata이지 business decision 자체가 아니라는 점이다.  
즉 "누가 처리하나"가 바뀌었다고 "무엇을 승인했나"가 바뀌면 안 된다.

### 4. escalation은 queue escalation, decision escalation, override를 분리해야 한다

human approval 흐름에서는 "에스컬레이션"이 하나가 아니다.

- queue escalation: 더 빠르거나 더 숙련된 팀 큐로 이동
- decision escalation: 더 높은 승인 권한자에게 결정을 넘김
- override / break-glass: 정상 정책 밖의 예외 결정을 감사 가능하게 실행

예를 들어:

- 사기 의심 건을 일반 심사 큐에서 fraud-specialist 큐로 보내는 것은 queue escalation
- 고액 환불의 최종 결정을 senior approver에게 넘기는 것은 decision escalation
- 장애 상황에서 긴급 승인으로 정책을 우회하는 것은 override

이 셋을 한 이벤트 이름으로 뭉개면 나중에 audit에서 "처리 지연 때문에 넘긴 것"과 "권한 부족 때문에 넘긴 것"을 구분할 수 없게 된다.

### 5. operator contract는 사람 역할별로 허용 동작을 고정해야 한다

manual review에서 가장 자주 빠지는 부분은 UI 버튼보다 **역할별 허용 동작 계약**이다.

| 역할 | 주로 소유하는 것 | 할 수 있는 것 | 하면 안 되는 것 |
|---|---|---|---|
| workflow owner / process manager | 상태 해석, deadline, timeout | enqueue, SLA breach 해석, escalation trigger | queue 운영자의 근무/용량을 직접 흉내 내기 |
| queue owner / dispatcher | routing, reassignment, queue health | assign, release, requeue, queue escalation | business approve/reject를 암묵적으로 확정하기 |
| reviewer / operator | 근거 수집, 1차 판단, 추가 정보 요청 | claim, 메모 남기기, escalate 요청, release | 권한 없는 최종 승인 |
| approver / supervisor | 최종 decision authority | approve, reject, exception authorize | queue aging을 숨기기 위해 임의 승인하기 |

이 계약을 명시하지 않으면 다음이 자주 생긴다.

- "담당자 바꿨으니 승인된 줄 알았다" 같은 의미 혼선
- queue owner가 병목 해소를 위해 권한 밖 결정을 내려 버림
- reviewer가 메모만 남겼는데 workflow가 승인된 것으로 오해됨

### 6. ownership drift를 막으려면 queue metadata와 audit trail이 필요하다

누가 이 일을 잡고 있었는지, 왜 다른 큐로 갔는지, 누가 어떤 권한으로 승인했는지 남기지 않으면 운영 설명 가능성이 사라진다.

최소한 다음 메타데이터를 남길 가치가 있다.

- work item id / workflow id
- current queue / current assignee
- claimed at / leased until
- sla due at / next escalation at
- required approval authority
- reassignment count
- escalation level / escalation reason
- last operator action / acted by / acted at
- policy version

이 정보가 있어야 다음 질문에 답할 수 있다.

- 왜 이 건이 4시간 동안 멈췄는가
- 왜 개인 inbox에서 팀 queue로 돌아갔는가
- 왜 reviewer가 아니라 supervisor가 최종 승인했는가
- 이 override가 정상 정책인지 비상 조치인지

### 7. human approval workflow는 queue 계약과 상태 계약을 둘 다 가져야 한다

manual review step을 workflow 상태로 승격했다면, 이제 상태 계약과 queue 계약을 같이 봐야 한다.

- 상태 계약: `UNDER_REVIEW`, `ESCALATED`, `APPROVED`, `REJECTED`
- queue 계약: `queued`, `claimed`, `lease expired`, `reassigned`, `decision escalated`

상태 계약만 있으면 "검토 중"이라는 사실만 남고 운영 병목은 안 보인다.  
반대로 queue 계약만 있으면 누가 무엇을 승인해야 하는지 business 의미가 흐려진다.

실무에서는 둘을 분리해 두는 편이 좋다.

- workflow state는 business truth를 표현
- queue state/metadata는 operator activity를 표현

---

## 실전 시나리오

### 시나리오 1: 고액 환불 심사

주문은 `UNDER_REFUND_REVIEW` 상태로 진입한다.  
1차 reviewer는 20분 lease로 claim할 수 있고, 응답이 없으면 자동으로 team queue로 복귀한다.  
금액이 특정 threshold를 넘으면 reviewer가 바로 승인하지 않고 senior approver에게 decision escalation을 요청한다.

### 시나리오 2: 사기 심사 야간 교대

fraud analyst가 야간 shift 종료 전에 아이템을 release하지 못하면 lease가 만료되고, 미처리 건은 다음 shift queue로 reassignment된다.  
이때 workflow는 계속 `UNDER_REVIEW`지만, queue metadata는 `night-fraud`에서 `day-fraud`로 바뀐다.

### 시나리오 3: 권한 승격 승인

일반 reviewer는 증빙 검토와 메모 추가만 가능하다.  
최종 grant는 security approver만 수행할 수 있고, reviewer가 누락 서류를 발견하면 reject가 아니라 `REQUEST_MORE_INFO` 또는 decision escalation을 선택한다.  
즉 queue 처리자와 승인 권한자는 같은 사람이 아닐 수 있다.

---

## 코드로 보기

### queue work item metadata

```java
public record ReviewWorkItem(
    String reviewId,
    String workflowId,
    String queueId,
    String assigneeId,
    Instant claimedAt,
    Instant leasedUntil,
    Instant slaDueAt,
    ApprovalAuthority requiredAuthority,
    int reassignmentCount,
    EscalationLevel escalationLevel
) {}
```

### escalation 구분

```java
public enum EscalationType {
    QUEUE_ESCALATION,
    DECISION_ESCALATION,
    OVERRIDE_AUTHORIZATION
}
```

### operator contract 감각

```java
public interface ReviewOperatorContract {
    ClaimResult claim(String reviewId, String operatorId, Instant now);
    void release(String reviewId, String operatorId, String reason);
    void reassign(String reviewId, String targetQueueId, String reason);
    void requestDecisionEscalation(String reviewId, ApprovalAuthority authority, String reason);
    void recordDecision(String reviewId, String approverId, ReviewDecision decision);
}
```

### lease expiry와 SLA breach 처리

```java
public void on(ReviewLeaseExpired event) {
    commandBus.dispatch(new ReturnReviewToQueue(
        event.reviewId(),
        "lease expired"
    ));
}

public void on(ReviewSlaBreached event) {
    commandBus.dispatch(new EscalateReview(
        event.reviewId(),
        EscalationType.QUEUE_ESCALATION,
        "senior-review-queue"
    ));
}
```

---

## 설계 체크리스트

- queue ownership과 workflow ownership을 정말 분리했는가
- claim을 영구 배정이 아니라 lease로 모델링했는가
- reassignment가 assignment metadata만 바꾸고 business decision은 유지하는가
- queue escalation과 decision escalation reason을 별도로 남기는가
- reviewer, queue owner, approver의 허용 동작이 명시되어 있는가
- shift handoff와 reviewer 부재가 운영 runbook이 아니라 시스템 규칙으로 표현되는가
- override가 있을 때 actor, reason, authority, timestamp가 감사 가능하게 남는가

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단일 reviewer 고정 | 단순하다 | 부재와 overload에 취약하다 | 아주 작은 팀, 중요도 낮은 내부 리뷰 |
| team queue + lease claim | 유연하고 운영 회복력이 높다 | queue metadata와 lease 관리가 필요하다 | 대부분의 manual review |
| 중앙 dispatcher가 강하게 라우팅 | 전문화된 routing이 쉽다 | dispatcher가 병목이나 single point가 될 수 있다 | skill routing, 규제/감사 요구가 큰 흐름 |
| escalation 없이 운영 | 구조는 단순하다 | SLA breach와 방치 건이 누적되기 쉽다 | 사실상 제한적 상황만 가능하다 |

판단 기준은 다음과 같다.

- queue ownership과 workflow ownership을 분리해서 본다
- reassignment는 예외 처리보다 정상 운영 루프로 설계한다
- queue escalation, decision escalation, override를 다른 의미로 다룬다
- operator contract가 모호하면 manual review는 곧 사람 의존 운영으로 무너진다

---

## 꼬리질문

> Q: workflow owner가 review queue도 다 가지면 안 되나요?
> 의도: 상태 ownership과 queue capacity ownership을 구분하는지 본다.
> 핵심: 아주 작은 조직은 가능하지만, 보통은 분리해야 timeout 정책과 운영 capacity가 서로 덜 오염된다.

> Q: reassignment는 reviewer가 없을 때만 필요한가요?
> 의도: reassignment를 정상 운영 루프로 보는지 확인한다.
> 핵심: 아니다. overload, shift change, skill routing, conflict of interest에도 자주 필요하다.

> Q: queue owner가 담당자를 바꿀 수 있으면 승인도 할 수 있는 것 아닌가요?
> 의도: assignment 권한과 decision authority를 분리하는지 본다.
> 핵심: 아니다. queue 운영 권한과 business approve/reject 권한은 별도 계약으로 두는 편이 안전하다.

> Q: escalation은 꼭 사람 hierarchy를 뜻하나요?
> 의도: queue escalation과 decision escalation, override를 구분하는지 본다.
> 핵심: 아니다. 더 적절한 팀 큐로의 이동일 수도 있고, 더 높은 승인 권한자에게 넘기는 것일 수도 있다.

## 한 줄 정리

Escalation, reassignment, queue ownership을 operator contract와 함께 설계하면 human approval workflow가 사람 의존 ad hoc 운영이 아니라, lease·권한·SLA가 설명 가능한 운영 시스템이 된다.
