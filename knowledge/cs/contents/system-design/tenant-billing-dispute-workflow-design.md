# Tenant Billing Dispute Workflow 설계

> 한 줄 요약: tenant billing dispute workflow는 청구 오류, 과금 이의 제기, 크레딧 조정, 조사 승인 절차를 체계화하는 재무 운영 워크플로우다.

retrieval-anchor-keywords: billing dispute, invoice challenge, credit adjustment, tenant billing, chargeback, case review, dispute workflow, prorated correction, approval, billing operations

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Billing / Usage Metering System 설계](./billing-usage-metering-system-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Fraud Case Management Workflow 설계](./fraud-case-management-workflow-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)

## 핵심 개념

billing dispute는 단순 CS 티켓이 아니다.  
실전에서는 아래를 함께 관리해야 한다.

- invoice challenge
- usage verification
- credit memo
- proration correction
- approval workflow
- customer communication

즉, dispute workflow는 청구와 정산을 되돌리거나 보정하는 재무 운영 시스템이다.

## 깊이 들어가기

### 1. dispute 유형

대표적으로 다음이 있다.

- 잘못된 사용량
- 중복 청구
- 계약 조건 불일치
- 세금/할인 계산 오류
- 서비스 장애 보상

분류가 먼저 되어야 올바른 팀과 절차로 간다.

### 2. Capacity Estimation

예:

- 월 10만 invoices
- dispute rate 0.5%
- 월 500건 케이스

숫자는 적어 보여도, 한 건당 영향 금액이 커서 워크플로우가 엄격해야 한다.

봐야 할 숫자:

- dispute intake rate
- resolution SLA
- credit issuance latency
- reopen rate
- approval queue depth

### 3. workflow stages

```text
OPEN -> TRIAGED -> INVESTIGATING -> PROPOSED -> APPROVED -> APPLIED -> CLOSED
```

각 단계마다 증거와 승인이 필요하다.

### 4. evidence and lineage

이의 제기를 처리하려면 근거가 있어야 한다.

- 원본 usage event
- invoice snapshot
- 계약/플랜 버전
- 담당자 메모
- audit log

이 부분은 [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)와 [Billing / Usage Metering System 설계](./billing-usage-metering-system-design.md)와 연결된다.

### 5. credit memo와 correction

단순히 금액을 수정하면 안 된다.

- credit memo
- adjustment entry
- next invoice offset
- refund if needed

정정은 원장에 남겨야 한다.

### 6. approval and segregation

재무 관련 수정은 단일 사람이 마음대로 하면 안 된다.

- maker/checker
- threshold-based approval
- finance ops signoff

### 7. communication

고객에게 무엇이 바뀌었는지 설명할 수 있어야 한다.

- disputed amount
- adjustment reason
- effective period
- next invoice impact

## 실전 시나리오

### 시나리오 1: 중복 청구

문제:

- 같은 usage가 두 번 들어갔다

해결:

- 원본 이벤트 대사
- credit memo 발행
- 다음 청구 반영

### 시나리오 2: 계약 조건 불일치

문제:

- 영업 계약과 실제 청구가 다르다

해결:

- contract override 확인
- price book 재평가
- 승인 후 correction

### 시나리오 3: 장애 보상

문제:

- 다운타임 보상 크레딧을 지급해야 한다

해결:

- SLA 기준 계산
- 승인 workflow
- invoice offset

## 코드로 보기

```pseudo
function openDispute(invoiceId, reason):
  case = createCase(invoiceId, reason)
  evidence = collectEvidence(invoiceId)
  queue.publish(case, evidence)

function applyCredit(caseId):
  memo = createCreditMemo(caseId)
  ledger.post(memo)
```

```java
public DisputeCase create(InvoiceId invoiceId, String reason) {
    return disputeRepository.open(invoiceId, reason);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| manual CS handling | 단순하다 | 추적이 어렵다 | 소규모 |
| workflow-based dispute | 추적이 쉽다 | 운영 절차가 늘어난다 | SaaS billing |
| auto credit small amounts | 빠르다 | 오탐 위험 | 저액 분쟁 |
| maker-checker approval | 안전하다 | 지연이 생긴다 | 고액 조정 |
| ledger correction only | 감사가 쉽다 | UX가 복잡할 수 있다 | 재무 시스템 |

핵심은 billing dispute가 단순 환불 요청이 아니라 **청구, 증거, 승인, 원장 수정을 잇는 운영 워크플로우**라는 점이다.

## 꼬리질문

> Q: dispute와 refund는 어떻게 다른가요?
> 의도: 청구 보정과 환불 구분 확인
> 핵심: dispute는 청구 오류를 다루고, refund는 결제 금액을 되돌린다.

> Q: 왜 evidence가 필요한가요?
> 의도: 재무 운영의 설명 가능성 이해 확인
> 핵심: 어떤 청구가 왜 틀렸는지 증명해야 하기 때문이다.

> Q: credit memo는 왜 원장에 남기나요?
> 의도: 회계 추적성 이해 확인
> 핵심: 수정도 거래로 남겨야 나중에 대사할 수 있다.

> Q: maker/checker가 왜 필요한가요?
> 의도: 승인 분리 이해 확인
> 핵심: 금전 수정은 단일 담당자 실수로부터 보호해야 한다.

## 한 줄 정리

Tenant billing dispute workflow는 청구 분쟁을 증거 수집, 승인, 원장 정정으로 풀어내는 재무 운영 시스템이다.

