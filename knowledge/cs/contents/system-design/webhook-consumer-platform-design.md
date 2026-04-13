# Webhook Consumer Platform 설계

> 한 줄 요약: webhook consumer platform은 외부 벤더의 웹훅을 안정적으로 수신, 검증, 정렬, 재처리하는 역방향 이벤트 수집 시스템이다.

retrieval-anchor-keywords: webhook consumer, inbound webhook, signature verification, replay defense, deduplication, inbox, ordering, dead letter queue, retry, event intake

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)
> - [Job Queue 설계](./job-queue-design.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Notification 시스템 설계](./notification-system-design.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

## 핵심 개념

Webhook consumer는 단순 HTTP endpoint가 아니다.  
실전에서는 다음을 함께 처리해야 한다.

- 서명 검증
- replay 방지
- 중복 제거
- 순서 보정
- 멱등 처리
- 다운스트림 전파

즉, 수신 플랫폼은 외부 시스템의 불안정한 이벤트를 내부 이벤트로 정제하는 관문이다.

## 깊이 들어가기

### 1. 왜 consumer platform이 필요한가

외부 벤더의 webhook은 신뢰할 수 없다.

- 재시도 중복
- 순서 뒤바뀜
- 오래된 이벤트
- 서명 실패
- provider 장애

그래서 수신부는 "받는 즉시 처리"가 아니라, 먼저 안전한 inbox에 넣어야 한다.

### 2. Capacity Estimation

예:

- 수십 개 provider
- 초당 5,000 inbound webhook
- 재시도율 20%

이 경우 수신 응답은 매우 빨라야 하고, 실제 처리는 비동기여야 한다.

봐야 할 숫자:

- ingress QPS
- signature failure rate
- dedup hit rate
- queue depth
- processing lag

### 3. ingest flow

```text
Provider
  -> Public Endpoint
  -> Signature Verification
  -> Dedup Store
  -> Inbound Inbox / Queue
  -> Normalizer
  -> Downstream Event Bus
```

### 4. 서명과 replay

consumer는 반드시 다음을 확인해야 한다.

- raw body 기반 signature
- timestamp window
- event id dedup
- provider secret rotation

이 부분은 [Webhook Delivery Platform 설계](./webhook-delivery-platform-design.md)와 [Webhook signature verification replay defense](../security/webhook-signature-verification-replay-defense.md)와 연결된다.

### 5. ordering과 reconciliation

provider는 이벤트 순서를 보장하지 않을 수 있다.

대응:

- resource key 기준 정렬 버퍼
- last-seen version
- reconciliation job

### 6. downstream fan-out

webhook을 받은 뒤 곧바로 처리하지 말고 내부 이벤트로 바꿔야 한다.

- payments
- subscriptions
- CRM sync
- analytics

이렇게 해야 consumer 장애가 내부 핵심 경로로 번지지 않는다.

### 7. failure mode

consumer endpoint가 죽어도 provider는 계속 재시도한다.

- fast 2xx ack
- durable inbox
- replay API
- DLQ for poison events

## 실전 시나리오

### 시나리오 1: 결제사 webhook 수신

문제:

- 승인/취소 이벤트가 중복된다

해결:

- event id dedup
- signature verify
- inbox storage

### 시나리오 2: 구독 상태 sync

문제:

- 구독 상태가 순서 뒤집힘으로 꼬인다

해결:

- versioned state machine
- reorder buffer

### 시나리오 3: provider outage

문제:

- provider가 재시도를 폭발시킨다

해결:

- rate limit
- DLQ
- replay after recovery

## 코드로 보기

```pseudo
function receiveWebhook(request):
  verifySignature(request)
  if dedup.exists(request.eventId):
    return 200
  inbox.save(request.rawBody)
  return 200
```

```java
public void handle(InboundWebhook request) {
    signatureVerifier.verify(request.rawBody(), request.headers());
    inboxRepository.saveIfAbsent(request.eventId(), request.rawBody());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| sync process on receive | 단순하다 | endpoint가 느려진다 | 소규모 |
| durable inbox first | 안정적이다 | 저장 계층이 늘어난다 | 대부분의 실서비스 |
| strict ordering | 디버깅이 쉽다 | 처리량이 떨어진다 | 상태 전이 중심 |
| best-effort ordering | 빠르다 | 재조정 필요 | 이벤트 중심 |
| replay support | 복구가 쉽다 | 중복 위험 증가 | 중요한 연동 |

핵심은 webhook consumer가 단순 endpoint가 아니라 **외부 이벤트를 내부 이벤트로 정규화하는 수신 플랫폼**이라는 점이다.

## 꼬리질문

> Q: webhook consumer가 왜 inbox가 필요한가요?
> 의도: ingest와 processing 분리 이해 확인
> 핵심: 수신 응답과 후처리를 분리해야 provider 재시도 폭주를 막는다.

> Q: signature verification에서 중요한 것은 무엇인가요?
> 의도: raw body와 replay 방어 이해 확인
> 핵심: raw payload, timestamp window, secret rotation이 중요하다.

> Q: webhook 순서가 깨지면 어떻게 하나요?
> 의도: reorder와 reconciliation 이해 확인
> 핵심: versioned state와 재조정이 필요하다.

> Q: provider가 재시도 폭주를 일으키면?
> 의도: rate limit과 DLQ 이해 확인
> 핵심: fast ack, limit, quarantine가 필요하다.

## 한 줄 정리

Webhook consumer platform은 외부 webhook을 안전하게 수신해 내부 이벤트로 정규화하고, 중복과 순서 문제를 흡수하는 역방향 이벤트 관문이다.

