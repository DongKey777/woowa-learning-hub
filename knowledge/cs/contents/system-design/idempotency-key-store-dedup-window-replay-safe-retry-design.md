---
schema_version: 3
title: Idempotency Key Store, Dedup Window, Replay-Safe Retry 설계
concept_id: system-design/idempotency-key-store-dedup-window-replay-safe-retry-design
canonical: true
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids:
- missions/shopping-cart
review_feedback_tags:
- idempotency-key-store-design
- replay-safe-retry
- dedup-window-recovery
aliases:
- idempotency key store
- dedup window design
- replay safe retry
- request fingerprint
- response replay
- processing lease
- in flight dedup
- payload hash conflict
- duplicate suppression window
symptoms:
- idempotency key를 단순 key-value cache로 보고 payload fingerprint와 response replay 계약을 빠뜨린다
- 같은 key 다른 payload를 중복으로 흡수해도 된다고 오해해 conflict 처리를 놓친다
- 외부 side effect 이후 timeout이 난 요청을 recover-first 없이 재실행하려 한다
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- database/idempotency-key-and-deduplication
- network/timeout-retry-backoff-practical
- system-design/backpressure-and-load-shedding-design
next_docs:
- system-design/payment-system-ledger-idempotency-reconciliation-design
- system-design/webhook-consumer-platform-design
- database/idempotent-transaction-retry-envelopes
- security/replay-store-outage-degradation-recovery
linked_paths:
- contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md
- contents/system-design/webhook-consumer-platform-design.md
- contents/system-design/distributed-scheduler-design.md
- contents/system-design/backpressure-and-load-shedding-design.md
- contents/database/idempotency-key-and-deduplication.md
- contents/database/duplicate-suppression-windows.md
- contents/database/idempotent-transaction-retry-envelopes.md
- contents/security/replay-store-outage-degradation-recovery.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/proxy-retry-budget-discipline.md
confusable_with:
- database/idempotency-key-and-deduplication
- database/duplicate-suppression-windows
- database/idempotent-transaction-retry-envelopes
- network/timeout-retry-backoff-practical
- system-design/payment-system-ledger-idempotency-reconciliation-design
forbidden_neighbors: []
expected_queries:
- idempotency key store를 설계할 때 fingerprint와 response replay는 왜 필요해?
- 같은 idempotency key에 다른 payload가 오면 중복으로 처리해도 돼?
- timeout 후 재시도할 때 외부 side effect가 이미 발생했는지 모르면 어떻게 복구해?
- dedup window는 왜 영구 저장이 아니라 기간 정책으로 잡아야 해?
- processing lease와 in-flight dedup은 중복 worker 실행을 어떻게 줄여?
contextual_chunk_prefix: |
  이 문서는 idempotency key store를 단순 캐시가 아니라 request fingerprint,
  processing lease, response replay, dedup window, recover-first retry로 구성된
  재시도 안전성 제어 계층으로 설명하는 advanced deep dive다.
---
# Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계

> 한 줄 요약: idempotency subsystem은 요청 fingerprint, 처리 lease, 결과 replay cache, dedup window, recovery loop를 결합해 안전한 재시도와 중복 흡수를 제공하는 제어 계층이다.

retrieval-anchor-keywords: idempotency key store, dedup window, replay-safe retry, request fingerprint, response replay, processing lease, retry amplification, payload hash, duplicate suppression, in-flight dedup

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
> - [Webhook Consumer Platform 설계](./webhook-consumer-platform-design.md)
> - [Distributed Scheduler 설계](./distributed-scheduler-design.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [Duplicate Suppression Windows](../database/duplicate-suppression-windows.md)
> - [Idempotent Transaction Retry Envelopes](../database/idempotent-transaction-retry-envelopes.md)
> - [Replay Store Outage / Degradation Recovery](../security/replay-store-outage-degradation-recovery.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Proxy Retry Budget Discipline](../network/proxy-retry-budget-discipline.md)

## 핵심 개념

멱등성은 "같은 요청이면 두 번 실행하지 않는다"로 끝나지 않는다.  
실전에서는 아래를 함께 만족해야 한다.

- 같은 key + 같은 payload면 같은 효과를 한 번만 만든다
- 같은 key + 다른 payload면 충돌로 거부한다
- 첫 시도가 처리 중이면 중복 실행 대신 대기, 합류, 또는 pending 응답을 준다
- 첫 시도가 외부 side effect 이후 timeout으로 끝났다면 재실행 전에 복구 조회를 한다
- dedup을 얼마나 오래 기억할지 window를 명시적으로 정한다

즉 idempotency key store는 단순 key-value 캐시가 아니라, **재시도 안전성의 제어 평면**이다.

여기서 자주 헷갈리는 개념도 구분해야 한다.

- **business uniqueness**: 주문 번호, 결제 번호처럼 도메인 자체가 유일해야 하는 성질
- **idempotency key**: 같은 요청 재전송을 흡수하기 위한 호출 단위 키
- **dedup window**: 영원히 기억하지 않고 일정 기간만 중복을 억제하는 운영 정책
- **response replay**: 중복 요청에 "중복이었다"만 말하는 것이 아니라, 가능한 경우 원래 결과를 다시 돌려주는 동작

## 깊이 들어가기

### 1. 어떤 문제를 푸는가

중복 요청은 생각보다 여러 곳에서 생긴다.

- 모바일 앱이 timeout 후 재시도
- API gateway나 proxy의 자동 retry
- worker crash 후 queue redelivery
- 운영자의 replay 버튼
- 외부 provider callback 중복

문제는 대부분의 create 계열 API가 본질적으로 non-idempotent라는 점이다.

- 주문 생성
- 결제 승인
- 포인트 차감
- 티켓 발급
- 이메일 발송 요청 등록

그래서 시스템은 "한 번만 실행"을 약속하기보다, **같은 작업이면 같은 결과로 수렴**하게 만들어야 한다.

핵심 계약은 보통 이렇게 잡는다.

1. 같은 scope + 같은 fingerprint면 같은 operation으로 취급한다.
2. 같은 scope + 다른 fingerprint면 잘못된 재사용으로 취급한다.
3. 결과가 완료되면 최초 응답과 호환되는 replay를 제공한다.
4. 결과가 애매하면 재실행보다 recover-first를 수행한다.

완전한 exactly-once를 주는 것은 아니다.  
대신 **정의된 window 안에서 중복 side effect를 크게 줄이고, 애매한 실패를 재실행보다 복구 중심으로 다루는 것**이 목표다.

### 2. 계약부터 고정해야 한다

먼저 key의 범위를 정의해야 한다.

- tenant id
- caller or client id
- operation name
- idempotency key

이 넷 중 일부를 빼면 다른 요청이 같은 key space를 공유하게 된다.  
예를 들어 `create-order`와 `refund-order`가 같은 key를 재사용하면 아주 위험하다.

request fingerprint도 중요하다.

- HTTP method
- normalized path template
- canonicalized JSON body
- 중요한 query/header subset

같은 key를 보냈더라도 body가 다르면 보통 `409 Conflict`로 막아야 한다.  
그렇지 않으면 "실수로 다른 요청이 이전 응답을 받는" 더 나쁜 문제가 생긴다.

상태 모델은 최소한 다음 정도가 필요하다.

- `PROCESSING`
- `COMPLETED`
- `FAILED_FINAL`
- `UNKNOWN`
- `EXPIRED`

여기서 `UNKNOWN`이 실전형 상태다.

- 외부 provider 호출 후 timeout
- 내부 commit 결과를 확신할 수 없음
- worker가 죽어서 side effect 반영 여부가 애매함

이 상태를 따로 두지 않으면 시스템은 안전하지 않은 재실행으로 기울게 된다.

### 3. 일반적인 아키텍처

```text
Client / Worker
  -> Idempotency Middleware
  -> Idempotency Store
  -> Domain Service
  -> DB / Outbox / External Provider
  -> Result Snapshot Writer
  -> Replay Response

Background Recovery Scanner
  -> expired lease scan
  -> unknown state reconciliation
  -> TTL compaction / cleanup
```

흐름은 보통 이렇다.

1. 요청이 들어오면 middleware가 scope와 fingerprint를 만든다.
2. store에서 `claim-or-replay`를 수행한다.
3. 이미 완료된 요청이면 캐시된 응답 또는 resource pointer를 replay한다.
4. 처리 중인 요청이면 waiter로 합류시키거나 `202 Accepted`를 돌려준다.
5. 새로 선점한 요청만 domain service를 실행한다.
6. 결과를 durable하게 남긴 뒤 `COMPLETED`로 바꾼다.
7. 애매한 실패는 `UNKNOWN`으로 전환하고 recovery scanner가 후속 복구를 맡는다.

이 구조를 API 전용으로 생각하기 쉽지만, queue consumer에도 그대로 적용된다.

- API는 `Idempotency-Key` header 중심
- 메시지 소비자는 `event_id` 또는 `operation_id` 중심

즉 인터페이스는 달라도, 본질은 **중복된 재진입을 한 번의 작업으로 합치는 것**이다.

### 4. 데이터 모델과 상태 기계

idempotency record에는 보통 다음이 들어간다.

- `scope_key`
- `request_fingerprint`
- `status`
- `operation_id`
- `lease_owner`
- `lease_until`
- `resource_type`, `resource_id`
- `response_code`, `response_ref`
- `first_seen_at`, `last_seen_at`
- `dedup_until`
- `attempt_count`
- `last_error_code`

`operation_id`를 별도로 두는 이유가 중요하다.

같은 요청의 모든 downstream side effect를 이 `operation_id`에 묶어야 한다.

- DB row의 external reference
- outbox event id
- provider idempotency key
- audit trail correlation id

이렇게 해야 retry 시점에 "이미 어디까지 갔는가"를 복구할 수 있다.

상태 전이는 보통 이렇게 본다.

```text
NEW -> PROCESSING -> COMPLETED
                 -> FAILED_FINAL
                 -> UNKNOWN -> RECOVERING -> COMPLETED
                                        \-> FAILED_FINAL
```

여기서 `PROCESSING`은 영구 상태가 아니어야 한다.

- lease TTL
- heartbeat
- fencing token 또는 attempt version

이 셋이 없으면 crash 후 같은 key가 영원히 막히거나, 반대로 두 worker가 동시에 이어서 실행할 수 있다.

### 5. dedup window는 비용과 업무 의미의 타협점이다

모든 key를 영원히 저장하면 가장 안전해 보이지만, 비용과 개인정보 삭제 요구 때문에 금방 부딪힌다.

예를 들어:

- peak 5,000 idempotent requests/sec
- 평균 record metadata 350B
- 평균 replay payload pointer + status metadata 250B
- dedup window 24시간

이 경우 metadata만 계산해도 하루 약 259GB 수준까지 간다.  
여기에 full response body까지 넣으면 hot storage 비용이 급격히 커진다.

그래서 실전에서는 tier를 나눈다.

- **hot tier**: `PROCESSING`과 최근 완료 키를 저장하는 Redis/KV
- **warm tier**: 24시간~7일 metadata를 저장하는 SQL 또는 LSM KV
- **cold tier**: 감사 목적이 필요한 일부 고위험 operation만 별도 archive

window도 업무별로 다르게 가져간다.

- 결제 승인, 환불, 포인트 차감: 길거나 거의 영구
- webhook dedup, 이메일 발송 등록: 수분~수시간
- 배치 chunk replay: 실행 주기 기준으로 한정 window

중요한 것은 TTL이 기술 설정이 아니라 **업무 계약**이라는 점이다.

- 고객이 며칠 뒤 같은 key로 재시도할 수 있는가
- 같은 key의 재사용을 금지할 것인가
- 늦은 replay를 새 요청으로 볼 것인가

이 질문에 답하지 않으면 store만 만들어도 정책은 비게 된다.

### 6. replay-safe retry는 결과를 다시 돌려주는 것까지 포함한다

많은 팀이 멱등성을 "중복 실행만 막으면 된다"로 오해한다.  
하지만 사용자 경험과 운영성까지 보려면 replay도 같이 설계해야 한다.

가장 위험한 시나리오는 이것이다.

1. 요청 A가 side effect를 만들었다.
2. 응답이 오기 전에 timeout이 났다.
3. 클라이언트가 같은 key로 다시 보냈다.

이때 시스템이 해야 할 일은 재실행이 아니라 **recover-first**다.

권장 순서:

1. 첫 claim 시 `operation_id`를 발급한다.
2. 모든 downstream 호출에 같은 `operation_id` 또는 provider-side idempotency key를 전달한다.
3. timeout이 나면 즉시 재실행하지 말고 `operation_id` 기준 조회를 먼저 한다.
4. 이미 완료된 흔적이 있으면 record를 `COMPLETED`로 고치고 원래 결과를 replay한다.
5. 정말 미반영이 확인된 경우에만 재시도한다.

즉 replay-safe retry는 "retry가 안전한가"보다, **retry 전에 원래 결과를 복원할 수 있는가**가 더 중요하다.

응답 저장 방식도 선택이 필요하다.

- full HTTP response snapshot
- resource id + serializer version
- business status summary

public API에서 원래 `201 Created`와 body까지 재현해야 하면 snapshot이 유리하다.  
반면 내부 API라면 `resource_id`를 기준으로 현재 상태를 다시 직렬화해도 충분할 수 있다.

### 7. 운영에서 깨지는 지점

#### stuck `PROCESSING`

원인:

- worker crash
- GC pause
- 네트워크 분리

대응:

- short lease + heartbeat
- lease expiry 후 recover scan
- attempt version으로 오래된 writer 차단

#### hot key와 retry amplification

하나의 요청에 수십 개 재시도가 붙으면 store가 병목이 된다.

대응:

- same-key waiter coalescing
- client backoff 가이드
- `Retry-After`
- per-key rate limit

#### store outage

idempotency store가 죽었을 때의 정책은 업무별로 다르다.

- 금전 이동: fail closed가 안전하다
- 읽기/낮은 위험 생성: 제한적 fail open 가능

이 결정을 미리 안 해두면 장애 때 임의 판단이 들어간다.

#### payload mismatch

같은 key에 다른 payload가 들어오면 단순히 "새 요청"으로 보면 안 된다.

- 클라이언트 버그
- 재사용 공격
- 프론트 캐시 오염

보통은 fingerprint mismatch를 감사 로그와 함께 노출해야 한다.

#### multi-region 중복

active-active에서는 같은 key가 서로 다른 리전에 동시에 도착할 수 있다.

선택지는 보통 세 가지다.

- global strongly consistent store
- tenant home region routing
- regional acceptance + 사후 reconciliation

비가역 side effect가 있는 결제, 발권, 재고 차감은 보통 마지막 선택지가 위험하다.  
지연이 늘더라도 owner region 또는 강한 합의 계층이 더 안전하다.

### 8. 어떤 시스템에서 특히 가치가 큰가

이 패턴은 다음 영역에서 특히 효과가 크다.

- 결제, 환불, 정산 API
- 주문 생성, 예약 확정
- webhook consumer와 callback 처리
- workflow step executor
- batch replay와 operator rerun

반대로 읽기 전용 조회나 쉽게 되돌릴 수 있는 캐시 워밍에는 과할 수 있다.  
모든 endpoint에 같은 강도의 idempotency를 강제하면 비용이 불필요하게 커진다.

## 실전 시나리오

### 시나리오 1: 모바일 주문 생성 timeout

문제:

- `POST /orders`가 서버에서 실제 생성까지는 끝났지만 응답 직전에 timeout이 났다

해결:

- 첫 요청이 `operation_id`와 함께 record를 선점한다
- 주문 row와 outbox event에 같은 `operation_id`를 남긴다
- 재시도는 새 주문 생성 대신 기존 order를 조회해 `201` 응답을 replay한다

### 시나리오 2: 외부 결제사 호출 후 응답 유실

문제:

- provider는 승인 성공
- 우리 서비스는 timeout
- 사용자가 같은 key로 다시 요청

해결:

- provider 쪽에도 같은 idempotency key를 전달한다
- 재시도 시 provider transaction lookup을 먼저 한다
- 이미 승인된 거래면 내부 record를 `COMPLETED`로 보정하고 결과를 replay한다

### 시나리오 3: queue consumer redelivery

문제:

- 메시지 처리는 성공했지만 ack 전에 worker가 죽었다
- 브로커가 같은 이벤트를 다시 전달한다

해결:

- `event_id`를 scope key로 사용한다
- consumer inbox 또는 idempotency store에 `COMPLETED` 기록을 남긴다
- 재전달된 이벤트는 side effect를 재실행하지 않고 즉시 skip 또는 prior result를 반환한다

## 코드로 보기

```pseudo
function handleIdempotent(request):
  scope = buildScope(request.tenantId, request.operation, request.idempotencyKey)
  fingerprint = hash(normalize(request.method, request.path, request.body))

  claim = idemStore.claim(scope, fingerprint, leaseTtl=30s, dedupTtl=24h)

  if claim.status == COMPLETED:
    return claim.replayResponse

  if claim.status == FINGERPRINT_MISMATCH:
    throw Conflict("same key, different payload")

  if claim.status == IN_PROGRESS:
    return accepted(claim.operationId)

  operationId = claim.operationId

  try:
    result = domainService.execute(request, operationId)
    idemStore.markCompleted(scope, fingerprint, snapshot(result))
    return result
  catch AmbiguousTimeout:
    recovered = domainService.recoverByOperationId(operationId)
    if recovered.exists:
      idemStore.markCompleted(scope, fingerprint, snapshot(recovered))
      return recovered
    idemStore.markUnknown(scope, operationId)
    throw RetryablePending()
  catch FinalBusinessError as e:
    idemStore.markFailedFinal(scope, safeErrorResponse(e))
    throw e
```

```java
public HttpResponse handle(CreateOrderRequest request) {
    IdempotencyScope scope = IdempotencyScope.of(
        request.tenantId(),
        "create-order",
        request.idempotencyKey()
    );
    RequestFingerprint fingerprint = RequestFingerprint.from(request);

    ClaimResult claim = idempotencyStore.claim(
        scope,
        fingerprint,
        Duration.ofSeconds(30),
        Duration.ofHours(24)
    );

    if (claim.isCompleted()) {
        return claim.cachedResponse();
    }
    if (claim.isConflict()) {
        throw new IdempotencyConflictException();
    }
    if (claim.isInProgress()) {
        throw new RequestStillProcessingException(claim.operationId());
    }

    OrderResult result = orderService.create(request, claim.operationId());
    idempotencyStore.markCompleted(scope, fingerprint, CachedResponse.created(result));
    return CachedResponse.created(result);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| full response snapshot | 원래 응답을 정확히 replay하기 쉽다 | 저장 비용과 PII 부담이 크다 | 외부 공개 API |
| resource pointer replay | 저장 비용이 작다 | 최초 응답과 현재 상태가 달라질 수 있다 | 내부 서비스 API |
| 긴 TTL 또는 영구 key | 늦은 retry까지 막기 쉽다 | 비용, 삭제, 재사용 정책이 어렵다 | 결제, 환불, 발권 |
| 짧은 dedup window | 운영 비용이 낮다 | window 밖 중복은 못 막는다 | webhook, 배치 재실행 |
| global strong consistency | cross-region 중복에 강하다 | 지연과 비용이 높다 | 비가역 side effect |
| region-local store + routing | 지연이 낮다 | failover와 owner 이동이 복잡하다 | 지역 분리 SaaS |

핵심은 idempotency store가 "중복 key 테이블"이 아니라, **결과 replay와 recovery를 포함한 실행 제어 계층**이라는 점이다.

## 꼬리질문

> Q: idempotency key와 business unique key는 왜 따로 봐야 하나요?
> 의도: 도메인 유일성과 요청 재전송 흡수를 구분하는지 확인
> 핵심: business key는 엔터티의 정체성이고, idempotency key는 호출 안전성 계약이다.

> Q: 같은 key인데 payload가 다르면 왜 이전 결과를 그냥 주면 안 되나요?
> 의도: fingerprint mismatch의 위험 이해 확인
> 핵심: 잘못된 재사용, 공격, 클라이언트 버그를 숨기게 되기 때문이다.

> Q: `UNKNOWN` 상태를 따로 두는 이유는 무엇인가요?
> 의도: 애매한 side effect 이후 재실행 위험을 이해하는지 확인
> 핵심: 확실하지 않은 상태를 실패나 성공으로 뭉개면 중복 실행 또는 유실이 생긴다.

> Q: replay-safe retry에서 제일 중요한 것은 무엇인가요?
> 의도: 단순 retry보다 recover-first 사고를 보는 질문
> 핵심: 재실행 전에 원래 operation의 결과를 복구 조회할 수 있어야 한다.

## 한 줄 정리

Idempotency key store 설계의 핵심은 key 저장이 아니라, 요청 fingerprint, in-flight lease, bounded dedup window, recovery, response replay를 함께 묶어 재시도를 안전한 결과 재현으로 바꾸는 데 있다.
