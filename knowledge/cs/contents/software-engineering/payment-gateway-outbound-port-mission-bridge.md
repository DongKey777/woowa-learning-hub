---
schema_version: 3
title: Payment Gateway Outbound Port Mission Bridge
concept_id: software-engineering/payment-gateway-outbound-port-mission-bridge
canonical: false
category: software-engineering
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/payment
- missions/shopping-cart
review_feedback_tags:
- payment-gateway
- outbound-port
- anti-corruption
- retry-timeout
aliases:
- payment gateway outbound port bridge
- PG client outbound port mission bridge
- 결제 게이트웨이 포트 브리지
- payment client anti corruption bridge
- payment retry timeout port boundary
symptoms:
- service가 PG SDK 응답 객체와 에러 코드를 그대로 안쪽으로 끌고 들어온다
- 결제 client timeout과 재시도를 controller 예외 처리처럼만 다룬다
- paymentGateway 인터페이스가 approve, cancel 의도보다 HTTP 세부를 노출한다
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/api-design-error-handling
next_docs:
- spring/payment-approval-db-failure-compensation-idempotency-primer
- software-engineering/idempotency-retry-consistency-boundaries
- software-engineering/module-api-dto-patterns
linked_paths:
- contents/software-engineering/ports-and-adapters-beginner-primer.md
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/module-api-dto-patterns.md
- contents/software-engineering/idempotency-retry-consistency-boundaries.md
- contents/spring/spring-payment-approval-db-failure-compensation-idempotency-primer.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
confusable_with:
- software-engineering/ports-and-adapters-beginner-primer
- software-engineering/api-design-error-handling
- software-engineering/module-api-dto-patterns
forbidden_neighbors:
- contents/spring/spring-wrong-bean-injected-cause-router.md
expected_queries:
- payment 미션에서 PG SDK를 service 안에 바로 쓰면 왜 outbound port가 필요해?
- 결제 gateway interface를 HTTP client 세부가 아니라 approve cancel 의도로 잡는 법을 알려줘
- PG timeout retry 에러 코드를 우리 도메인 결과로 번역하는 bridge가 필요해
- payment client anti corruption boundary를 미션 리뷰 문장으로 설명해줘
- 결제 API 연동에서 outbound adapter와 idempotency retry 경계가 어떻게 이어져?
contextual_chunk_prefix: |
  이 문서는 payment gateway outbound port mission_bridge다. PG SDK,
  payment client, approve/cancel port, timeout retry, provider error code,
  anti-corruption mapping, service boundary 같은 결제 미션 리뷰 문장을
  ports and adapters와 API error handling으로 매핑한다.
---
# Payment Gateway Outbound Port Mission Bridge

> 한 줄 요약: 결제 미션에서 PG 연동은 "HTTP client 호출"이 아니라, 안쪽 유스케이스가 필요한 `approve/cancel/status` 의도를 바깥 adapter가 번역하는 outbound port 문제다.

**난이도: Intermediate**

## 미션 진입 증상

| payment 장면 | 먼저 볼 경계 |
|---|---|
| service가 PG SDK DTO를 그대로 받는다 | provider 언어가 도메인 안쪽으로 새는가 |
| timeout이면 다시 approve를 호출한다 | 같은 시도인지 멱등 키로 판정하는가 |
| PG 에러 코드가 controller까지 올라간다 | 우리 실패 타입으로 번역했는가 |
| approve/cancel/status HTTP path가 interface 이름이 된다 | 유스케이스 의도로 port를 열었는가 |

## CS concept 매핑

payment gateway port는 "PG API를 감추는 wrapper"가 아니라, 결제 유스케이스가 바깥 세부를 모른 채 필요한 의도를 말하게 하는 계약이다.

```java
public interface PaymentGateway {
    PaymentApproval approve(PaymentApprovalRequest request);
    PaymentCancellation cancel(PaymentCancellationRequest request);
    PaymentStatusView fetchStatus(PaymentStatusQuery query);
}
```

여기서 중요한 것은 메서드 이름이 HTTP endpoint와 1:1로 붙지 않아도 된다는 점이다.
안쪽은 `approve`, `cancel`, `fetchStatus` 같은 의도를 말하고, adapter는 provider token, header, retryable error, timeout, raw code를 번역한다.

## 리뷰 신호

- "SDK 응답이 service를 오염시켜요"는 anti-corruption mapping이 필요하다는 신호다.
- "timeout이면 그냥 재시도하면 되나요?"는 idempotency key와 status 조회를 먼저 보라는 뜻이다.
- "PG 에러 코드별로 if가 늘어요"는 provider error를 우리 실패 타입으로 접는 adapter 책임을 보라는 말이다.
- "결제 취소도 같은 client로 호출하면 되죠?"는 cancel도 approve처럼 멱등성과 보상 경계를 가진 별도 의도인지 확인하라는 신호다.

## 판단 순서

1. 안쪽 service가 알아야 할 결제 의도를 `approve/cancel/status`로 줄인다.
2. provider token, raw status code, retryable/non-retryable error를 adapter에서 번역한다.
3. timeout 뒤에는 새 approve보다 기존 attempt/status 조회를 먼저 고려한다.
4. 승인 성공 뒤 DB 실패는 port 문제가 아니라 compensation/idempotency 문서로 넘긴다.

이렇게 나누면 payment 미션의 PG 연동 리뷰가 "client 클래스 위치" 논쟁에서 벗어나 outbound boundary와 실패 의미로 정리된다.
