---
schema_version: 3
title: Billing / Usage Metering System 설계
concept_id: system-design/billing-usage-metering-system-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- billing
- usage metering
- invoice
- proration
aliases:
- billing
- usage metering
- invoice
- proration
- rating
- ledger
- quota
- usage aggregation
- billing period
- metered events
- revenue recognition
- Billing / Usage Metering System 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/entitlement-quota-design.md
- contents/system-design/audit-log-pipeline-design.md
- contents/system-design/distributed-scheduler-design.md
- contents/system-design/job-queue-design.md
- contents/system-design/multi-tenant-saas-isolation-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Billing / Usage Metering System 설계 설계 핵심을 설명해줘
- billing가 왜 필요한지 알려줘
- Billing / Usage Metering System 설계 실무 트레이드오프는 뭐야?
- billing 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Billing / Usage Metering System 설계를 다루는 deep_dive 문서다. billing과 usage metering은 사용량을 정확히 집계하고, 과금과 한도를 안전하게 연결하는 재무-운영 결합 시스템이다. 검색 질의가 billing, usage metering, invoice, proration처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Billing / Usage Metering System 설계

> 한 줄 요약: billing과 usage metering은 사용량을 정확히 집계하고, 과금과 한도를 안전하게 연결하는 재무-운영 결합 시스템이다.

retrieval-anchor-keywords: billing, usage metering, invoice, proration, rating, ledger, quota, usage aggregation, billing period, metered events, revenue recognition

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Entitlement / Quota 설계](./entitlement-quota-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Multi-tenant SaaS 격리 설계](./multi-tenant-saas-isolation-design.md)

## 핵심 개념

billing은 단순히 카드에서 돈을 빼는 기능이 아니다.  
실전에서는 아래를 같이 다뤄야 한다.

- usage event 수집
- aggregation
- rate/rating
- invoice 생성
- proration
- refunds/credits
- revenue reconciliation

즉, billing은 정책, 계량, 회계가 만나는 시스템이다.

## 깊이 들어가기

### 1. Usage event와 ledger는 다르다

usage event는 "얼마나 썼는가"이고, ledger는 "무엇이 청구 가능한가"다.

예:

- API request
- storage GB-hours
- compute minutes
- active seat count
- outbound bandwidth

usage event는 많고 noisy하지만, billing ledger는 정제되어야 한다.

### 2. Capacity Estimation

예:

- 100만 tenant
- tenant당 하루 1만 usage event

하루 100억 이벤트까지도 갈 수 있다.  
그래서 실시간 청구보다는 event ingestion + batch aggregation이 많다.

봐야 할 숫자:

- ingestion lag
- aggregation lag
- invoice close duration
- rating QPS
- dispute rate

### 3. 파이프라인 구조

```text
Usage Event
  -> Durable Stream
  -> Normalize / Dedup
  -> Aggregate
  -> Rate / Price
  -> Billing Ledger
  -> Invoice / Credit / Alert
```

이 구조의 핵심은 event와 invoice를 분리하는 것이다.  
정확한 사용량과 청구 가능한 사용량은 항상 같지 않을 수 있다.

### 4. Metering과 dedup

사용량 집계는 중복 이벤트가 매우 위험하다.

- retry로 같은 event가 재전송됨
- worker crash 후 재처리됨
- upstream이 중복 발행함

따라서 event id와 idempotency key가 필요하다.

### 5. Proration과 billing period

월 중간 업그레이드/다운그레이드가 흔하다.

- 프로 플랜으로 중간 변경
- seat 수 변경
- 사용량 구간 변경

이 경우 proration이 필요하다.  
billing period와 effective date가 정확히 정의되지 않으면 분쟁이 생긴다.

### 6. Quota와 billing 연결

quota는 단순 제한이 아니라 과금 전 단계다.

- soft quota warning
- hard quota enforcement
- overage charge

이 부분은 [Entitlement / Quota 설계](./entitlement-quota-design.md)와 함께 봐야 한다.

### 7. Auditability

billing 시스템은 설명 가능해야 한다.

- 어떤 usage가 invoice에 반영됐는가
- 어떤 rate table이 사용됐는가
- 어떤 환불/크레딧이 적용됐는가

이런 이유로 audit trail과 reconciliation job이 필요하다.

## 실전 시나리오

### 시나리오 1: 월말 invoice 발행

문제:

- 월말에 수백만 건 usage를 마감해야 한다

해결:

- scheduler로 close job 실행
- aggregate snapshot을 freeze
- invoice line item 생성

### 시나리오 2: 사용량 중복 반영

문제:

- 같은 usage event가 두 번 들어왔다

해결:

- event id dedup
- aggregation checkpoint 저장

### 시나리오 3: 플랜 업그레이드

문제:

- 중간에 플랜이 바뀌었다

해결:

- effective date 기준으로 proration
- invoice correction entry 기록

## 코드로 보기

```pseudo
function ingestUsage(event):
  if dedup.exists(event.id):
    return
  normalized = normalize(event)
  aggregate.update(normalized)
  ledger.append(normalized)

function closeBillingPeriod(period):
  snapshot = aggregate.freeze(period)
  invoice = price(snapshot)
  emitInvoice(invoice)
```

```java
public Invoice closePeriod(BillingPeriod period) {
    UsageSnapshot snapshot = usageService.freeze(period);
    return invoiceService.generate(snapshot);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Real-time billing | 즉시성 높다 | 복잡하고 비싸다 | 초대형 overage |
| Batch billing | 단순하고 안정적 | 지연이 있다 | 대부분의 SaaS |
| Event-based metering | 재처리에 유리 | 중복 제어 필요 | usage-heavy service |
| Invoice snapshot | 감사가 쉽다 | 수정이 번거롭다 | 월말 청구 |
| Soft quota + overage | UX가 좋다 | 비용 통제가 약해질 수 있다 | 성장형 제품 |

핵심은 billing이 금액 계산이 아니라 **사용량, 정책, 정산, 감사의 연결 시스템**이라는 점이다.

## 꼬리질문

> Q: usage event와 invoice line item은 왜 분리하나요?
> 의도: 계량과 청구의 차이 이해 확인
> 핵심: raw usage는 noisy하고, invoice는 정제되어야 한다.

> Q: proration은 왜 어려운가요?
> 의도: 기간 계산과 정책 변경 이해 확인
> 핵심: 중간 변경, 취소, 환불이 동시에 들어오기 때문이다.

> Q: billing에서 dedup이 중요한 이유는 무엇인가요?
> 의도: 재전송과 재처리 영향 이해 확인
> 핵심: 중복 반영은 곧 금전 오류다.

> Q: quota와 billing을 왜 연결하나요?
> 의도: 보호와 과금의 결합 이해 확인
> 핵심: 사용량 초과는 제한뿐 아니라 과금 정책과도 연결되기 때문이다.

## 한 줄 정리

Billing / usage metering system은 대규모 사용량 이벤트를 정확히 집계하고, 청구와 한도, 정산을 일관된 ledger로 연결하는 시스템이다.

