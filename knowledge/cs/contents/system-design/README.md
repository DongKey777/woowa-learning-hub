# System Design

> 대규모 시스템 설계 면접 핵심 주제 모음

## 카테고리 목차

| # | 주제 | 난이도 | 파일 |
|---|------|--------|------|
| 1 | 시스템 설계 면접 프레임워크 | 🟢 Basic | [system-design-framework.md](system-design-framework.md) |
| 2 | Back-of-Envelope 추정법 | 🟢 Basic | [back-of-envelope-estimation.md](back-of-envelope-estimation.md) |
| 3 | URL 단축기 설계 | 🟡 Intermediate | [url-shortener-design.md](url-shortener-design.md) |
| 4 | Rate Limiter 설계 | 🟡 Intermediate | [rate-limiter-design.md](rate-limiter-design.md) |
| 5 | 분산 캐시 설계 | 🔴 Advanced | [distributed-cache-design.md](distributed-cache-design.md) |
| 6 | 채팅 시스템 설계 | 🔴 Advanced | [chat-system-design.md](chat-system-design.md) |
| 7 | Newsfeed 시스템 설계 | 🔴 Advanced | [newsfeed-system-design.md](newsfeed-system-design.md) |
| 8 | Notification 시스템 설계 | 🔴 Advanced | [notification-system-design.md](notification-system-design.md) |
| 9 | Consistent Hashing / Hot Key 전략 | 🔴 Advanced | [consistent-hashing-hot-key-strategies.md](consistent-hashing-hot-key-strategies.md) |
| 10 | Distributed Lock 설계 | 🔴 Advanced | [distributed-lock-design.md](distributed-lock-design.md) |
| 11 | Search 시스템 설계 | 🔴 Advanced | [search-system-design.md](search-system-design.md) |
| 12 | File Storage / Presigned URL / CDN | 🔴 Advanced | [file-storage-presigned-url-cdn-design.md](file-storage-presigned-url-cdn-design.md) |
| 13 | Workflow Orchestration / Saga | 🔴 Advanced | [workflow-orchestration-saga-design.md](workflow-orchestration-saga-design.md) |
| 14 | 멀티 테넌트 SaaS 격리 설계 | 🔴 Advanced | [multi-tenant-saas-isolation-design.md](multi-tenant-saas-isolation-design.md) |
| 15 | Payment System / Ledger / Idempotency / Reconciliation | 🔴 Advanced | [payment-system-ledger-idempotency-reconciliation-design.md](payment-system-ledger-idempotency-reconciliation-design.md) |

## 학습 순서 추천

```
프레임워크 → 추정법 → URL 단축기 → Rate Limiter → 분산 캐시 → Multi-tenant SaaS 격리 → Payment System / Ledger / Reconciliation → Consistent Hashing → Newsfeed → Notification → 채팅 시스템 → Distributed Lock → Search → File Storage → Workflow
```

## 참고

- DB 레벨의 Sharding, Replication, CQRS 등은 [database/](../database/) 카테고리 참조
- 실시간 전송 모델 비교는 [network/](../network/)의 SSE / WebSocket 문서와 함께 보면 좋다
- 멀티 테넌트 격리 문제는 [Security](../security/README.md), [Database](../database/README.md), [Software Engineering](../software-engineering/README.md) 문서와 함께 보면 더 잘 보인다
- 결제/정산/정합성은 [Database](../database/README.md)의 멱등성, redo/undo, reconciliation 관점과 함께 보면 좋다
- 이 카테고리는 **면접 관점의 상위 레벨 아키텍처 설계**에 집중한다
