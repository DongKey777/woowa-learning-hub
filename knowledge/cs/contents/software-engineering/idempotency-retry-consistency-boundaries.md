---
schema_version: 3
title: Idempotency, Retry, Consistency Boundaries
concept_id: software-engineering/idempotency-retry-consistency-boundaries
canonical: true
category: software-engineering
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- idempotency
- retry
- consistency-boundary
- outbox
aliases:
- Idempotency Retry Consistency Boundaries
- retry consistency boundary
- idempotency key boundary
- duplicate request suppression
- exactly once myth
- 멱등성 재시도 일관성 경계
symptoms:
- timeout 후 같은 쓰기 요청을 재시도하는데 idempotency key와 저장 경계가 없어 주문, 결제, 알림 같은 side effect가 중복돼
- 부분 성공을 구분하지 못해 retry가 안전한 item과 manual review가 필요한 item을 같은 방식으로 다시 보내
intents:
- deep_dive
- design
- troubleshooting
prerequisites:
- software-engineering/api-design-error-handling
- software-engineering/batch-idempotency-keys
next_docs:
- software-engineering/outbox-inbox-domain-events
- software-engineering/batch-partial-failure
- software-engineering/http-coalescing-failure-mapping
linked_paths:
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/batch-idempotency-key-boundaries.md
- contents/software-engineering/outbox-inbox-domain-events.md
- contents/software-engineering/cache-message-observability.md
- contents/software-engineering/http-coalescing-failure-mapping.md
- contents/software-engineering/batch-partial-failure-policies-primer.md
confusable_with:
- software-engineering/batch-idempotency-keys
- software-engineering/outbox-inbox-domain-events
- software-engineering/http-coalescing-failure-mapping
forbidden_neighbors: []
expected_queries:
- retry와 idempotency key를 consistency boundary 관점에서 같이 설계해야 하는 이유가 뭐야?
- timeout 후 같은 주문 생성 요청을 다시 보낼 때 중복 생성을 막는 멱등성 저장 경계는 어떻게 잡아?
- exactly once와 idempotency를 같은 말로 쓰면 왜 위험한지 설명해줘
- 부분 성공이 있는 batch나 bulk API에서 item-level idempotency key가 필요한 이유가 뭐야?
- DB commit과 message publish 사이에 outbox가 retry consistency를 어떻게 보완해?
contextual_chunk_prefix: |
  이 문서는 retry, idempotency key, duplicate suppression, consistency boundary, outbox를 함께 설계해야 하는 이유를 설명하는 advanced bridge이다.
---
# Idempotency, Retry, Consistency Boundaries

> 한 줄 요약: 재시도와 멱등성은 분리할 수 없고, 둘 다 결국 "어디까지를 같은 결과로 볼 것인가"라는 일관성 경계 문제다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API 설계와 예외 처리](./api-design-error-handling.md)
> - [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Cache, Messaging, Observability](./cache-message-observability.md)
> - [System Design](../system-design/README.md)

retrieval-anchor-keywords: idempotency retry boundary, retry consistency boundary, idempotency key, duplicate request suppression, timeout retry safety, partial success retry, consistency boundary, outbox with retry, exactly once myth, retry side effect control, batch idempotency key boundaries, item-level idempotency key, chunk-level idempotency key, run-level idempotency key, retry-safe batch recovery

## 핵심 개념

재시도는 네트워크와 장애 현실을 받아들이는 방식이다.
멱등성은 재시도가 결과를 망치지 않게 하는 방식이다.
일관성 경계는 어떤 연산을 같은 결과로 볼지 정하는 기준이다.

이 셋은 따로 설계하면 안 된다.

- 재시도 정책이 있으면 멱등성 키가 필요할 수 있다
- 멱등성 키가 있으면 저장 경계가 필요하다
- 저장 경계가 있으면 eventual consistency와 강한 일관성의 분리가 필요하다

## 깊이 들어가기

### 1. 멱등성은 응답이 아니라 상태 기준이다

같은 요청을 두 번 보냈을 때 응답이 완전히 같지 않아도 된다.
중요한 것은 최종 상태가 같아야 한다는 점이다.

예를 들어 주문 생성은:

- 첫 번째 요청이 주문을 만들고
- 두 번째 요청은 같은 주문을 재생성하면 안 된다

### 2. retry가 문제를 키우는 경우

재시도는 보통 좋은 전략이지만, 다음 조건이 맞지 않으면 문제를 키운다.

- 부작용이 있는 API
- 중복 방지 키가 없는 저장 경로
- 부분 성공을 구분하지 못하는 클라이언트

### 3. consistency boundary

모든 연산을 같은 트랜잭션으로 묶으면 단순하지만 느리다.
반대로 너무 잘게 나누면 사용자 관점에서 이상한 중간 상태가 보인다.

그래서 경계를 정해야 한다.

- 결제 승인과 잔액 차감은 강한 일관성이 필요할 수 있다
- 알림 발송과 감사 로그는 eventual consistency로 충분할 수 있다

## 실전 시나리오

### 시나리오 1: 네트워크 타임아웃 후 재시도

클라이언트는 응답을 못 받았다고 생각하고 다시 보낸다.
서버는 이미 처리했는데, 멱등성이 없으면 주문이 두 번 생긴다.

### 시나리오 2: Outbox 없이 비동기 이벤트 발행

DB는 커밋됐는데 메시지는 유실되면 상태와 후속 작업이 어긋난다.
이건 retry가 아니라 저장 경계 문제다.

### 시나리오 3: 멱등성 키의 범위가 너무 넓다

유저 전체를 키로 잡으면 서로 다른 요청이 같은 것으로 취급된다.
범위가 너무 좁으면 중복 방지가 안 된다.

## 코드로 보기

```java
public class PaymentFacade {
    private final IdempotencyStore idempotencyStore;

    public PaymentResult pay(String key, PaymentRequest request) {
        if (idempotencyStore.exists(key)) {
            return idempotencyStore.findResult(key);
        }

        PaymentResult result = doPay(request);
        idempotencyStore.save(key, result);
        return result;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| Retry only | 단순하다 | 중복 위험이 높다 | 읽기 API |
| Idempotency key only | 중복 방지에 강하다 | 저장 경계가 필요하다 | 결제/주문 |
| Retry + Idempotency + Outbox | 장애 복원력 높다 | 구현 복잡도 높다 | 중요한 쓰기 경로 |
| No retry | 단순하다 | 실패 체감이 크다 | 강한 부작용 경로 |

## 꼬리질문

- 멱등성과 정확히 한 번 처리를 왜 같은 말로 쓰면 안 되는가?
- retry가 안전한 API와 위험한 API의 차이는 무엇인가?
- consistency boundary를 잘못 잡으면 사용자에게 어떤 중간 상태가 보이는가?
- 멱등성 키 저장소가 장애나면 어떤 복구 전략이 필요한가?

## 한 줄 정리

재시도는 현실이고, 멱등성은 그 현실을 안전하게 만들기 위한 경계 설계다.
