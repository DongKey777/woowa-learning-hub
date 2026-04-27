# Webhook and Broker Boundary Primer

> 한 줄 요약: webhook endpoint와 broker consumer는 둘 다 외부 이벤트를 유스케이스로 들이는 inbound adapter지만, retry 주도권, idempotency key, acknowledgment 의미가 다르다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: webhook and broker boundary primer basics, webhook and broker boundary primer beginner, webhook and broker boundary primer intro, software engineering basics, beginner software engineering, 처음 배우는데 webhook and broker boundary primer, webhook and broker boundary primer 입문, webhook and broker boundary primer 기초, what is webhook and broker boundary primer, how to webhook and broker boundary primer
채널 자체를 먼저 정리하고 싶다면 [Message-Driven Adapter Example](./message-driven-adapter-example.md), inbound adapter 테스트 경계를 같이 보고 싶다면 [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md), [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)부터 읽고 이 문서는 그다음에 "webhook endpoint와 broker consumer는 무엇이 같고, 운영 의미가 어디서 갈라지는가"만 좁혀 보면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 한 문장으로 이해하기](#먼저-한-문장으로-이해하기)
- [같은 유스케이스를 두 채널로 여는 예시](#같은-유스케이스를-두-채널로-여는-예시)
- [webhook adapter는 무엇을 맡나](#webhook-adapter는-무엇을-맡나)
- [broker consumer adapter는 무엇을 맡나](#broker-consumer-adapter는-무엇을-맡나)
- [retry는 누가 소유하나](#retry는-누가-소유하나)
- [idempotency key는 어디서 오나](#idempotency-key는-어디서-오나)
- [acknowledgment semantics는 왜 다르게 읽어야 하나](#acknowledgment-semantics는-왜-다르게-읽어야-하나)
- [한 표로 빠르게 비교하기](#한-표로-빠르게-비교하기)
- [자주 생기는 오해](#자주-생기는-오해)

</details>

> 관련 문서:
> - [Software Engineering README: Webhook and Broker Boundary Primer](./README.md#webhook-and-broker-boundary-primer)
> - [Message-Driven Adapter Example](./message-driven-adapter-example.md)
> - [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
> - [Inbound Adapter Test Slices Primer](./inbound-adapter-test-slices-primer.md)
> - [Inbound Adapter Testing Matrix](./inbound-adapter-testing-matrix.md)
> - [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [API 설계와 예외 처리](./api-design-error-handling.md)
> - [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
>
> retrieval-anchor-keywords:
> - webhook vs broker consumer
> - webhook inbound adapter
> - webhook boundary primer
> - http webhook idempotency
> - webhook retry semantics
> - webhook acknowledgment semantics
> - webhook 2xx retry meaning
> - http callback vs message broker consumer
> - broker consumer ack nack retry
> - message consumer delivery semantics
> - broker redelivery idempotency
> - delivery acknowledgement vs business success
> - ack after commit
> - dedup key for webhook
> - dedup key for message consumer
> - inbound adapter retry boundary
> - inbound adapter acknowledgment boundary

webhook가 "HTTP controller니까 그냥 request/response adapter"인지, broker consumer처럼 "at-least-once delivery ingress"로 읽어야 하는지 헷갈릴 때 이 문서를 보면 된다.
중복 제어와 저장 경계를 더 깊게 보고 싶다면 [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md), [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)를 이어서 보면 된다.

## 왜 이 primer가 필요한가

실무에서는 아래 오해가 자주 섞인다.

- webhook는 HTTP라서 일반 사용자 API와 같은 성격이라고 본다
- broker consumer는 메시징이니까 완전히 다른 구조라고 본다
- 두 채널 모두 성공 신호를 너무 일찍 보내고, duplicate delivery는 나중 문제라고 미룬다

하지만 수신자 입장에서 보면 둘 다 같다.

- 바깥 시스템이 이벤트를 밀어 넣는다
- 우리 서비스는 그 입력을 유스케이스 호출로 번역한다
- 같은 입력이 다시 올 수 있으므로 duplicate-safe 해야 한다

차이는 "hexagonal 안에서 다른 계층이다"가 아니라, **어떤 신호가 delivery acknowledgment 역할을 하며 retry를 누가 조종하는가**에 있다.

## 먼저 한 문장으로 이해하기

핵심은 이 세 줄이면 충분하다.

- **webhook**: `HTTP status`가 acknowledgment 역할을 하고, retry cadence는 외부 sender/provider가 잡는다
- **broker consumer**: `ack/nack/offset commit`이 acknowledgment 역할을 하고, retry/redelivery는 broker나 listener/container 정책이 크게 좌우한다
- **둘 다**: duplicate delivery를 전제로 해야 하므로, 유스케이스 앞단에는 durable idempotency 경계가 필요하다

즉 webhook는 wire protocol만 보면 HTTP지만, 운영 의미는 종종 "외부 이벤트 ingress"에 더 가깝다.
broker consumer는 메시징 전용 채널이지만, 결국 하는 일은 똑같이 **바깥 입력을 안쪽 유스케이스 호출로 번역하는 것**이다.

## 같은 유스케이스를 두 채널로 여는 예시

예를 들어 외부 결제 상태 변경을 반영하는 `ApplyPaymentNotificationUseCase`가 있다고 하자.
같은 유스케이스를 webhook와 broker consumer가 모두 열 수 있다.

```java
public interface ApplyPaymentNotificationUseCase {
    void apply(ApplyPaymentNotificationCommand command);
}

public record ApplyPaymentNotificationCommand(
    String source,
    String externalEventId,
    String paymentId,
    PaymentStatus status
) {}
```

```java
@RestController
class PaymentWebhookController {
    private final ApplyPaymentNotificationUseCase useCase;

    @PostMapping("/webhooks/payments")
    ResponseEntity<Void> receive(
        @RequestHeader("X-Provider-Event-Id") String eventId,
        @RequestBody PaymentWebhookRequest request
    ) {
        useCase.apply(new ApplyPaymentNotificationCommand(
            "payment-provider-webhook",
            eventId,
            request.paymentId(),
            request.status()
        ));
        return ResponseEntity.ok().build();
    }
}
```

```java
@KafkaListener(topics = "payment-status-changed")
class PaymentStatusChangedConsumer {
    private final ApplyPaymentNotificationUseCase useCase;

    void handle(PaymentStatusChangedEvent event) {
        useCase.apply(new ApplyPaymentNotificationCommand(
            "payment-status-topic",
            event.eventId(),
            event.paymentId(),
            event.status()
        ));
    }
}
```

둘 다 안쪽에서는 같은 command를 쓸 수 있다.
차이는 controller/consumer 바깥에서 끝나지 않고, **성공을 언제 선언할지**에서 커진다.

## webhook adapter는 무엇을 맡나

webhook adapter는 HTTP 요청을 받지만, 보통 일반 사용자 요청보다 delivery semantics를 더 강하게 의식해야 한다.

- signature, secret, source authenticity를 검증한다
- header/body를 command로 번역한다
- recoverable failure와 non-recoverable failure를 HTTP status로 번역한다
- `2xx`를 돌려도 되는 안전 시점을 정한다

많은 webhook provider는 `2xx`를 "전달 성공"으로 보고 retry를 멈춘다.
그래서 webhook에서 가장 위험한 실수는 **durable acceptance 전에 `200 OK`를 보내는 것**이다.

예를 들면 아래처럼 읽어야 한다.

| webhook 응답 | 외부 sender가 읽는 의미 | 우리 쪽에서 안전하게 뜻해야 하는 것 |
|---|---|---|
| `2xx` | 전달 성공, 보통 retry 중단 | raw event 저장, inbox 기록, 내부 queue 적재처럼 최소한 durable handoff 완료 |
| `4xx` | 요청 자체가 잘못됐거나 인증 실패 | retry해도 해결되지 않는 malformed payload, signature 오류, 지원하지 않는 schema |
| `5xx` 또는 timeout | 수신자가 아직 안전하게 받지 못함 | transient failure, 내부 장애, 저장 실패 |

provider별 세부 규약은 다를 수 있지만, 일반 원칙은 같다.
**성공 응답은 "비즈니스 처리가 끝났다"보다 "안전하게 받아 두었다"를 의미해야 한다.**

그래서 webhook는 자주 아래 패턴을 쓴다.

1. signature 검증
2. raw payload 또는 inbox row를 저장
3. 내부 command/event로 durable handoff
4. 그다음 `200` 또는 `202` 계열 응답

즉 webhook adapter는 겉으로는 HTTP지만, 운영 감각은 **외부 SaaS가 보내는 at-least-once 이벤트 ingress**에 가깝다.

## broker consumer adapter는 무엇을 맡나

broker consumer도 동일하게 외부 입력을 command로 번역한다.
다만 이 채널에서는 HTTP status 대신 broker protocol이 acknowledgment를 맡는다.

- payload와 header를 command로 번역한다
- retryable/non-retryable failure를 분류한다
- ack, nack, requeue, DLQ 격리 경로를 정한다
- ack 시점이 DB commit이나 dedup 기록과 어긋나지 않게 맞춘다

예를 들면 아래처럼 읽는다.

| consumer 결과 | broker가 읽는 의미 | 우리 쪽에서 안전하게 뜻해야 하는 것 |
|---|---|---|
| `ack` 또는 offset commit | 이 delivery는 다시 보낼 필요 없음 | side effect와 dedup 기록이 이미 안전하게 남음 |
| `nack`, exception, requeue | 나중에 다시 delivery 가능 | transient failure, 아직 안전하게 처리 완료 아님 |
| reject, DLQ 이동 | 일반 재시도로 해결되지 않음 | poison message, 수동 조사 필요 |

여기서도 가장 위험한 실수는 똑같다.
**DB commit이나 dedup 기록 전에 ack를 보내면, broker가 재전송하지 않아 복구 기회가 사라질 수 있다.**

반대로 commit 뒤 ack가 늦어지면 duplicate redelivery가 생길 수 있다.
그래서 broker consumer는 거의 항상 **ack-after-commit + idempotent consumer** 조합으로 읽는 편이 안전하다.

## retry는 누가 소유하나

두 채널의 가장 큰 차이는 retry 주도권이다.

| 질문 | webhook | broker consumer |
|---|---|---|
| 누가 다시 보내나 | 외부 provider/sender | broker, listener container, consumer runtime |
| 우리가 retry를 유도하는 방법 | HTTP status, timeout, 연결 종료 | ack/nack/throw, retry config, visibility timeout, DLQ 정책 |
| backoff를 어디서 바꾸나 | 대개 provider 계약 밖에 있음 | 플랫폼/consumer 설정으로 조정 가능 |
| retry 횟수 관찰 포인트 | provider dashboard, delivery log, ingress log | broker metric, consumer lag, retry topic/DLQ |
| 흔한 실수 | `200`을 너무 빨리 보내 재시도 기회를 없앰 | auto-ack 기본값을 믿고 commit 전에 ack됨 |

즉 webhook는 retry 스케줄을 우리가 직접 쥐지 못하는 경우가 많고, broker consumer는 비교적 더 많은 제어권을 가진다.
하지만 둘 다 본질은 같다.
**재시도는 duplicate delivery 가능성을 늘리고, 그 비용은 결국 idempotency 경계가 감당한다.**

## idempotency key는 어디서 오나

이 지점도 같은 듯 다르다.

- webhook dedup key는 보통 provider가 준 `event id`, `delivery id`, payload 안의 안정적인 외부 식별자에서 온다
- broker consumer dedup key는 producer가 넣은 `message id`, `event id`, `business id`에서 온다
- 둘 다 `source + stable external id` 조합으로 저장하면 안전하다

반대로 아래 값은 위험하다.

- webhook body hash만 단독으로 dedup key로 쓰는 것
- broker offset, receipt handle, delivery tag만 business dedup key처럼 쓰는 것
- signature 자체를 dedup key로 쓰는 것

signature는 authenticity를 증명하는 값이지, 같은 비즈니스 이벤트를 식별하는 키가 아닐 수 있다.
offset이나 delivery tag도 delivery 시도 단위 핸들일 뿐, replay나 topology 변경까지 견디는 business key가 아닐 수 있다.

보통은 아래처럼 읽으면 된다.

```java
public record InboundDeliveryId(
    String source,
    String externalEventId
) {}
```

그리고 중요한 점은 키를 찾는 것만으로 끝나지 않는다는 것이다.
**dedup 기록과 side effect가 같은 transaction 또는 같은 durable acceptance 경계 안에 있어야 한다.**
그렇지 않으면 "중복은 막았는데 실제 상태는 반영 안 됨" 같은 어정쩡한 실패가 생긴다.

## acknowledgment semantics는 왜 다르게 읽어야 하나

핵심 차이는 여기에 응축된다.

- webhook는 HTTP response가 곧 acknowledgment다
- broker consumer는 processing과 acknowledgment 사이에 별도 단계가 있다

이 차이 때문에 안전한 ack 시점도 다르게 표현된다.

| 채널 | 안전한 acknowledgment 시점 | 너무 이르면 생기는 문제 | 늦으면 생기는 문제 |
|---|---|---|---|
| webhook | inbox/raw event 저장 또는 내부 durable handoff 직후 | sender가 retry를 멈춰 event 유실 가능 | sender가 같은 event를 다시 보내 duplicate delivery 증가 |
| broker consumer | dedup 기록과 상태 변경 commit 직후 | broker가 redelivery를 안 해 lost processing 가능 | redelivery와 duplicate 처리 비용 증가 |

실무 감각으로는 이렇게 보면 된다.

- **이른 ack**는 유실을 만든다
- **늦은 ack**는 중복을 만든다
- 중복은 idempotency로 복구 가능하지만, 유실은 재전송 기회를 잃으면 복구가 더 어렵다

그래서 둘 다 공통 결론은 같다.
**성공 신호는 "처리를 시작했다"가 아니라 "최소한 안전하게 받아 두었다"를 뜻해야 한다.**

## 한 표로 빠르게 비교하기

| 항목 | webhook | broker consumer |
|---|---|---|
| wire protocol | HTTP push | queue/topic delivery |
| inbound adapter 형태 | controller-like web adapter | listener/message handler adapter |
| acknowledgment 신호 | HTTP status | ack/nack/offset commit |
| retry 주도권 | 외부 sender/provider | broker/runtime/operator |
| duplicate가 생기는 주된 이유 | timeout, non-2xx, sender retry | redelivery, rebalance, visibility timeout, retry topic |
| 대표 dedup key | provider event id, delivery id | producer message id, event id, business key |
| poison path | `4xx` 또는 별도 quarantine | DLQ, parking queue, manual replay |
| 테스트 우선순위 | signature 검증, status mapping, durable accept before `2xx` | ack-after-commit, redelivery, dedup, DLQ wiring |

요약하면 webhook는 "HTTP처럼 보이는 외부 이벤트 ingress"고, broker consumer는 "메시징처럼 보이는 외부 이벤트 ingress"다.
둘 다 결국은 **at-least-once 현실을 받아들이는 inbound adapter**로 읽는 편이 안전하다.

## 자주 생기는 오해

- webhook는 HTTP니까 일반 동기 API처럼 취급해도 된다고 본다. 하지만 수신자 입장에서는 비동기 재전송이 붙는 ingress일 수 있다.
- broker ack는 곧 비즈니스 성공이라고 본다. 실제로는 delivery channel에 대한 확인일 뿐이다.
- idempotency는 broker consumer에만 필요하다고 본다. webhook도 timeout과 sender retry 때문에 똑같이 필요하다.
- `4xx`면 provider가 절대 retry하지 않는다고 단정한다. 세부 정책은 provider 계약을 확인해야 한다.
- broker가 exactly-once를 말하니 애플리케이션 dedup은 필요 없다고 생각한다. side effect 경계에서는 여전히 idempotency가 필요할 수 있다.

## 한 줄 정리

webhook와 broker consumer는 둘 다 외부 이벤트를 유스케이스로 들이는 inbound adapter이며, 차이는 채널 종류보다 **retry를 누가 조종하는지, 어떤 신호가 acknowledgment인지, 그 신호를 보내기 전에 어디까지를 durable하게 받아 둬야 하는지**에 있다.
