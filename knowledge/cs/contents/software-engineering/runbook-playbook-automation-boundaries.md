# Runbook, Playbook, Automation Boundaries

> 한 줄 요약: Runbook은 사람이 따라 하는 복구 절차이고, playbook은 판단 기준을 묶은 대응 프레임이며, automation은 그중 안전하게 기계가 대신할 수 있는 부분만 맡는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Incident Review and Learning Loop Architecture](./incident-review-learning-loop-architecture.md)
> - [Kill Switch Fast-Fail Ops](./kill-switch-fast-fail-ops.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Feature Flags, Rollout, Dependency Management](./feature-flags-rollout-dependency-management.md)
> - [Spring Transaction Debugging Playbook](../spring/spring-transaction-debugging-playbook.md)
> - [Operational Readiness Drills and Change Safety](./operational-readiness-drills-and-change-safety.md)
> - [Shadow Process Catalog and Retirement](./shadow-process-catalog-and-retirement.md)

> retrieval-anchor-keywords:
> - runbook
> - playbook
> - automation boundary
> - operational procedure
> - manual recovery
> - safe automation
> - response checklist
> - operator decision
> - readiness drill

## 핵심 개념

운영 문서를 다 runbook이라고 부르면 경계가 흐려진다.

- Runbook: 정해진 절차를 사람이 그대로 따라 실행하는 문서
- Playbook: 상황 판단 기준과 선택지를 정리한 대응 가이드
- Automation: 사람이 반복하는 안전한 절차를 기계로 옮긴 것

셋은 비슷해 보여도 역할이 다르다.

---

## 깊이 들어가기

### 1. runbook은 절차가 구체적이어야 한다

Runbook은 "무엇을 할지"보다 "어떻게 할지"가 중요하다.

좋은 runbook에는 다음이 있어야 한다.

- 선행 조건
- 명령어
- 기대 결과
- 실패 시 다음 단계
- rollback 또는 중단 조건

즉 runbook은 재현 가능한 절차서다.

### 2. playbook은 판단의 분기점을 담아야 한다

Playbook은 runbook보다 넓다.

예:

- 이 장애가 사용자 영향인지 내부 영향인지
- 지금 즉시 끌 것인지 관찰할 것인지
- kill switch를 먼저 쓸지, rollback을 먼저 할지

즉 playbook은 "무슨 상황에서 어떤 runbook으로 갈 것인가"를 정한다.

### 3. automation은 전부를 맡기면 안 된다

자동화가 유효한 영역:

- 반복적이고 결정이 적은 작업
- 안전장치가 있는 작업
- 되돌릴 수 있는 작업

자동화가 위험한 영역:

- 불완전한 정보로 판단해야 하는 작업
- 되돌리기 어려운 데이터 변경
- 외부 시스템 부작용이 큰 작업

따라서 automation은 "사람을 대체"가 아니라 **사람이 안전하게 맡길 수 있는 범위만 기계화**하는 것이다.

### 4. operator decision point는 남겨야 한다

자동화가 많아질수록 사람의 개입 지점이 사라질 수 있다.

하지만 다음은 사람이 최종 판단해야 할 수 있다.

- 대규모 write 중단 여부
- 외부 결제 중지 여부
- 데이터 보정 실행 여부
- 복구와 원복 순서

이 지점은 명확히 남겨야 한다.

### 5. 문서는 실행 로그와 연결돼야 한다

Runbook은 실제 실행 후 업데이트되어야 한다.

- 명령어가 바뀌면 문서를 바꾼다
- 실패 사례가 나오면 문서를 보강한다
- 자동화로 전환되면 사람 절차를 줄인다
- drill에서 막힌 지점이 있으면 readiness evidence를 갱신한다

문서와 운영이 따로 놀면 runbook은 금방 낡는다.

---

## 실전 시나리오

### 시나리오 1: 배치 실패 복구

Playbook은 먼저 배치 실패 유형을 나눈다.

- 일시적 네트워크 문제
- 데이터 오류
- 잘못된 입력

그다음 적절한 runbook으로 들어간다.

### 시나리오 2: kill switch 발동

자동화는 우선 영향을 멈추고, 그 다음 사람이 복구 계획을 판단하도록 설계한다.
여기서 자동화는 차단과 관측까지만 맡을 수 있다.

### 시나리오 3: 트랜잭션 문제 조사

운영자가 [Spring Transaction Debugging Playbook](../spring/spring-transaction-debugging-playbook.md)을 따라가며 proxy, rollback, isolation을 확인한다.
이런 문서는 자동화보다 판단 보조에 가깝다.

---

## 코드로 보기

```markdown
## Recovery Runbook
1. Check alert severity.
2. Disable write path if blast radius is growing.
3. Verify queue backlog.
4. Re-run idempotent replay job.
5. Confirm user-facing error rate is back to baseline.
```

이 정도로 구체적이어야 실제 현장에서 쓸 수 있다.

---

## 트레이드오프

| 선택 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 수동 runbook | 유연하다 | 느리고 실수 가능성이 있다 | 판단이 중요한 장애 |
| playbook 중심 | 대응 기준이 명확하다 | 세부 실행은 별도 필요하다 | 여러 유형의 장애가 있을 때 |
| automation 중심 | 빠르고 반복 가능하다 | 경계 설정이 어렵다 | 안전한 반복 작업 |

운영 문서는 절차 자동화보다 먼저 **경계 설계**가 되어야 한다.

---

## 꼬리질문

- 어떤 작업을 자동화해도 되는가?
- 어떤 판단은 반드시 사람 손에 남겨야 하는가?
- runbook과 playbook은 누가 유지보수하는가?
- 자동화가 실패했을 때 fallback runbook은 있는가?

## 한 줄 정리

Runbook, playbook, automation은 같은 운영 문서가 아니라 서로 다른 책임을 가지며, 안전한 자동화는 사람의 판단 경계를 먼저 정의할 때만 가능하다.
