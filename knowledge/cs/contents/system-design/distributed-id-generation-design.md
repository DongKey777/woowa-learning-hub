---
schema_version: 3
title: 분산 ID 생성 설계
concept_id: system-design/distributed-id-generation-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- distributed id generation
- snowflake
- uuidv7
- ulid
aliases:
- distributed id generation
- snowflake
- uuidv7
- ulid
- monotonic id
- shard key
- hot partition
- sequence
- clock skew
- base62
- 분산 ID 생성 설계
- distributed id generation design
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/consistent-hashing-hot-key-strategies.md
- contents/system-design/url-shortener-design.md
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- 분산 ID 생성 설계 설계 핵심을 설명해줘
- distributed id generation가 왜 필요한지 알려줘
- 분산 ID 생성 설계 실무 트레이드오프는 뭐야?
- distributed id generation 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 분산 ID 생성 설계를 다루는 deep_dive 문서다. 분산 환경에서 충돌 없이, 정렬 가능하고, 샤드 친화적인 ID를 생성하는 방법을 설계한다. 검색 질의가 distributed id generation, snowflake, uuidv7, ulid처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# 분산 ID 생성 설계

> 한 줄 요약: 분산 환경에서 충돌 없이, 정렬 가능하고, 샤드 친화적인 ID를 생성하는 방법을 설계한다.

retrieval-anchor-keywords: distributed id generation, snowflake, uuidv7, ulid, monotonic id, shard key, hot partition, sequence, clock skew, base62

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [URL 단축기 설계](./url-shortener-design.md)
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)

## 핵심 개념

ID 생성은 "유일하면 끝"이 아니다. 실무에서는 아래 성질을 같이 봐야 한다.

- 전역 유일성
- 시간 정렬 가능성
- 샤드/파티션 친화성
- 추측 가능성 낮음
- 너무 길지 않은 표현
- 장애와 시계 오차에 대한 내성

즉, ID는 단순 식별자가 아니라 저장, 조회, 디버깅, 샤딩, 보안까지 영향을 주는 인프라 선택이다.

## 깊이 들어가기

### 1. 요구사항을 먼저 나눈다

ID가 필요한 이유를 먼저 분리한다.

- 내부 조인용 숫자 키가 필요한가
- 외부에 노출되는 공개 ID가 필요한가
- 생성 순서가 보장되어야 하는가
- 리전/서비스/노드를 역추적해야 하는가
- 정렬 가능한 문자열이 필요한가

하나의 ID로 모든 요구를 만족시키려 하면 오히려 복잡해진다. 실무에서는 내부 PK와 외부 공개 ID를 분리하는 경우가 많다.

### 2. Capacity Estimation

숫자 감각이 있어야 어떤 방식이 터질지 보인다.

예를 들어:

- 서비스 20개
- 서비스당 초당 5,000개 ID 생성
- 전체 생성량: 100,000 IDs/sec

이 정도면 단일 DB sequence나 동기 중앙 발급기는 쉽게 병목이 된다.  
반대로 각 노드가 독립적으로 생성하면 충돌 회피와 시계 관리가 중요해진다.

계산할 때는 다음도 함께 본다.

- 1일 생성량
- 저장 시 인덱스 크기
- ID를 문자열로 노출할 때의 길이
- hot shard 가능성

### 3. 대표적인 생성 방식

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| DB auto-increment | 단순하고 작다 | 단일 병목, 분산에 약하다 | 작은 서비스, 단일 DB |
| 중앙 ID 서버 | 관리가 쉽다 | SPOF와 latency가 생긴다 | 내부 시스템, 낮은 QPS |
| Hi/Lo 또는 segment | 발급량이 높다 | 세그먼트 관리가 필요하다 | 높은 처리량 |
| Snowflake 계열 | 분산 생성에 강하다 | 시계와 node id가 중요하다 | 대규모 분산 시스템 |
| ULID / UUIDv7 | 정렬성과 분산성을 함께 노린다 | 구현/표준 이해가 필요하다 | 공개 ID, 이벤트 ID |
| 랜덤 UUID | 충돌이 매우 낮다 | 길고 정렬이 안 된다 | 단순 식별, 보안 우선 |

실무에서는 내부 저장용 숫자 키와, 외부 공개용 정렬 문자열을 분리하는 설계도 흔하다.

### 4. 시계 문제와 노드 문제

분산 ID의 핵심 사고는 거의 항상 시계에서 시작한다.

- NTP 보정으로 시간이 뒤로 갈 수 있다
- 리전별 clock skew가 다를 수 있다
- node id가 중복되면 충돌한다
- timestamp 비트가 부족하면 수명이 짧아진다

대응책:

1. clock rollback을 감지하고 발급을 잠시 멈춘다.
2. sequence overflow 시 다음 밀리초로 넘긴다.
3. node id는 중앙 할당하거나 lease 기반으로 관리한다.
4. 리전별 prefix를 넣어 충돌 범위를 줄인다.

### 5. 샤딩과 hot partition

순차 ID는 삽입이 빠를 수 있지만, 샤딩 기준으로 쓰면 마지막 샤드에 트래픽이 몰릴 수 있다.  
반대로 무작위 ID는 쓰기는 고르게 퍼지지만, range query와 디버깅이 불편해진다.

예:

- `order_id`를 그대로 shard key로 쓰면 최신 row가 한쪽 끝에 몰릴 수 있다.
- `user_id`와 `created_at` 조합으로 설계하면 조회 패턴에 맞출 수 있다.

이 문제는 [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)과 같이 생각해야 한다.

### 6. 공개 ID와 내부 ID를 분리한다

공개 ID는 추측하기 어렵고 외부 노출에 안전해야 한다.

- 내부 ID: 숫자형, 조인과 인덱스에 유리
- 공개 ID: 짧거나 정렬 가능한 문자열, 외부 API와 URL에 유리

예를 들어 URL 단축기나 주문 조회 API는 내부 PK를 그대로 노출하지 않는 편이 안전하다.

### 7. 운영 관점 체크리스트

- 중복 생성은 얼마나 빨리 감지되는가
- 시계 오차가 발생하면 fail-open인지 fail-close인지
- node id 할당이 재시작 후에도 안전한지
- 리전 장애 때 ID prefix가 충돌하지 않는지
- 로그와 메트릭으로 생성량을 추적할 수 있는지

## 실전 시나리오

### 시나리오 1: 주문 번호를 외부에 노출해야 한다

문제:

- 주문 번호는 고객에게 보여야 한다
- 너무 예측 가능하면 안 된다

해결:

- 내부 PK와 별도로 공개용 order code를 둔다
- 공개용은 ULID/UUIDv7/Base62 조합을 고려한다
- 조회 API는 공개 ID만 받는다

### 시나리오 2: 이벤트 ID가 시간 순으로 정렬돼야 한다

문제:

- 로그/이벤트를 생성 순서대로 보고 싶다
- 분산 환경이라도 대략적인 시간 정렬이 필요하다

해결:

- Snowflake 또는 UUIDv7처럼 k-sortable한 포맷을 쓴다
- 리전 prefix와 sequence overflow 처리를 넣는다

### 시나리오 3: 핫 키 회피가 중요하다

문제:

- 최신 ID가 하나의 shard로 쏠린다
- 쓰기 병목이 생긴다

해결:

- shard key를 ID와 분리한다
- write path는 분산시키고 read path는 별도 인덱스로 찾는다

## 코드로 보기

```pseudo
function nextId():
  now = currentMillis()
  if now < lastTimestamp:
    waitOrFail()
  if now == lastTimestamp:
    sequence = (sequence + 1) % MAX_SEQUENCE
    if sequence == 0:
      now = waitNextMillis(lastTimestamp)
  else:
    sequence = 0
  lastTimestamp = now
  return encode(now, regionId, nodeId, sequence)
```

```java
public String publicOrderCode(long internalId) {
    return Base62.encode(internalId);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DB sequence | 단순하고 짧다 | 중앙 병목 | 단일 DB, 낮은 복잡도 |
| Snowflake | 고처리량, 정렬 가능 | 시계/노드 관리 필요 | 대규모 분산 시스템 |
| UUIDv7/ULID | 분산성과 정렬성 균형 | 포맷이 길다 | 공개 ID, 이벤트 ID |
| 랜덤 UUID | 충돌 걱정이 적다 | 조회/정렬이 불편 | 외부 노출만 중요한 경우 |
| 내부 ID + 외부 ID 분리 | 유연하다 | 저장과 관리가 늘어난다 | 대부분의 실서비스 |

핵심은 "어떤 ID가 가장 멋진가"가 아니라 **조회, 샤딩, 보안, 운영까지 같이 보면 무엇이 가장 덜 아픈가**다.

## 꼬리질문

> Q: UUIDv4 대신 UUIDv7을 쓰는 이유는 무엇인가요?
> 의도: 정렬성과 분산성의 균형을 이해하는지 확인
> 핵심: UUIDv7은 시간 순 정렬에 유리해서 인덱스와 조회 패턴에 더 잘 맞는다.

> Q: Snowflake에서 시간이 뒤로 가면 어떻게 하나요?
> 의도: clock skew와 failover 감각 확인
> 핵심: 발급 중단, sequence 조정, node 재할당 같은 보호 장치가 필요하다.

> Q: DB auto-increment는 왜 분산에 불리한가요?
> 의도: 중앙 병목과 샤딩 문제 이해 확인
> 핵심: 중앙 발급 의존도가 높아지고, scale-out 시 발급 지점이 병목이 된다.

> Q: 공개 ID를 내부 ID와 분리하는 이유는 무엇인가요?
> 의도: 보안과 운영 관점 확인
> 핵심: 추측 가능성, URL 노출, 마이그레이션 유연성을 같이 확보할 수 있다.

## 한 줄 정리

분산 ID 설계는 유일성만 맞추는 문제가 아니라, 정렬, 샤딩, 보안, 시계 오차, 운영 난이도까지 함께 최적화하는 문제다.

