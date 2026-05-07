---
schema_version: 3
title: 옵저버, Pub/Sub, ApplicationEvent
concept_id: design-pattern/observer-pubsub-application-events
canonical: true
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- observer-pubsub-boundary
- applicationevent-not-kafka
- event-failure-boundary
aliases:
- observer vs pubsub vs direct call
- direct call vs observer vs pubsub
- same process observer vs broker pubsub
- spring applicationevent same process
- applicationevent not kafka
- event listener ordering failure boundary
- event-driven decoupling basics
- when to use observer vs pubsub
- spring eventlistener sync or async
- broker pubsub retry durability
symptoms:
- Spring ApplicationEvent를 Kafka 같은 durable broker로 이해해 재시도, 적재, consumer lag가 자동 제공된다고 착각한다
- listener 하나 실패했는데 원래 주문 처리까지 실패하거나, 반대로 외부 side effect가 rollback 전에 나가 실패 경계가 흐려진다
- 핵심 정합성 경로까지 이벤트 fan out으로 숨겨 순서와 즉시 실패 전파가 코드에서 보이지 않는다
intents:
- comparison
- troubleshooting
- design
prerequisites:
- design-pattern/observer
- design-pattern/observer-vs-pubsub-quick-bridge
- design-pattern/mediator-vs-observer-vs-pubsub
next_docs:
- design-pattern/spring-eventlistener-vs-transactionaleventlistener-timing
- design-pattern/domain-events-vs-integration-events
- design-pattern/outbox-relay-idempotent-publisher
linked_paths:
- contents/design-pattern/observer.md
- contents/design-pattern/observer-vs-pubsub-quick-bridge.md
- contents/design-pattern/mediator-vs-observer-vs-pubsub.md
- contents/design-pattern/observer-lifecycle-hygiene.md
- contents/design-pattern/spring-eventlistener-vs-transactionaleventlistener-timing.md
- contents/design-pattern/domain-events-vs-integration-events.md
- contents/design-pattern/outbox-relay-idempotent-publisher.md
- contents/design-pattern/idempotent-consumer-projection-dedup-pattern.md
- contents/spring/spring-eventlistener-transaction-phase-outbox.md
- contents/spring/spring-eventlistener-ordering-async-traps.md
- contents/security/webhook-signature-verification-replay-defense.md
- contents/software-engineering/cache-message-observability.md
confusable_with:
- design-pattern/observer
- design-pattern/observer-vs-pubsub-quick-bridge
- design-pattern/domain-events-vs-integration-events
- spring/eventlistener-transaction-phase-outbox
forbidden_neighbors: []
expected_queries:
- Direct call, Observer, Pub/Sub는 이벤트라는 말이 같아도 실패 경계가 어떻게 달라?
- Spring ApplicationEvent는 왜 Kafka 같은 durable broker가 아니라 same process observer 쪽에서 먼저 이해해야 해?
- listener 실패가 주문 처리 트랜잭션에 붙는 증상이 보이면 어떤 경계를 다시 봐야 해?
- 핵심 정합성 경로는 느슨한 결합보다 direct call이나 명시적 orchestration이 더 안전한 이유가 뭐야?
- durable delivery, retry, 중복 제거가 필요하면 observer에서 outbox나 broker pubsub로 올라가야 하는 기준은 뭐야?
contextual_chunk_prefix: |
  이 문서는 옵저버, Pub/Sub, ApplicationEvent chooser로, direct call, same-process
  observer/ApplicationEvent, broker Pub/Sub를 실행 시점, 실패 전파, transaction timing,
  retry/durability, consumer 중복 처리 요구에 따라 구분하는 방법을 설명한다.
---
# 옵저버, Pub/Sub, ApplicationEvent

> 한 줄 요약: `이벤트`라는 단어가 같아도 direct call, 같은 프로세스 옵저버, broker Pub/Sub는 실패 경계와 실행 의미가 달라서 "패턴 이름"보다 "지금 어떤 증상이 보이냐"로 구분하는 편이 더 안전하다.

**난이도: 🟡 Intermediate**

관련 문서:

- [Observer(옵저버) 디자인 패턴](./observer.md)
- [옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리](./observer-vs-pubsub-quick-bridge.md)
- [Mediator vs Observer vs Pub/Sub](./mediator-vs-observer-vs-pubsub.md)
- [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)
- [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](./spring-eventlistener-vs-transactionaleventlistener-timing.md)
- [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
- [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
- [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)
- [Spring EventListener, TransactionalEventListener, and Outbox](../spring/spring-eventlistener-transaction-phase-outbox.md)
- [Spring `@EventListener` Ordering and Async Traps](../spring/spring-eventlistener-ordering-async-traps.md)
- [Webhook Signature Verification / Replay Defense](../security/webhook-signature-verification-replay-defense.md)
- [캐시, 메시징, 관측성](../software-engineering/cache-message-observability.md)
- [카테고리 README](./README.md)

retrieval-anchor-keywords: observer vs pubsub vs direct call, direct call vs observer vs pubsub, same process observer vs broker pubsub, spring applicationevent same process, applicationevent not kafka, event listener ordering failure boundary, event-driven decoupling basics, 직접 호출 옵저버 pubsub 차이, 이벤트라서 다 같은 건가요, 이벤트인데 왜 바로 실패하지, spring eventlistener sync or async, broker pubsub retry durability, what is application event, when to use observer vs pubsub, beginner event boundary

---

## 이 문서는 언제 읽으면 좋은가

- `이벤트로 빼자`는 말이 나왔는데 사실 direct call이어야 하는지 헷갈릴 때
- Spring `ApplicationEvent`를 Kafka 같은 Pub/Sub처럼 이해해도 되는지 막힐 때
- `왜 listener 하나 실패했는데 주문도 실패하지?`, `왜 발행은 됐는데 소비는 나중에 되지?` 같은 증상으로 경계를 다시 세우고 싶을 때

짧게 말하면 이 문서는 패턴 이름 사전보다 **증상별 선택 카드**에 가깝다.

## 핵심 개념

세 가지를 먼저 분리하면 retrieval 충돌이 많이 줄어든다.

- `direct call`: 호출자가 지금 이 자리에서 누구를 실행할지 안다.
- `in-process observer`: 같은 프로세스 안에서 등록된 listener들에게 fan-out한다.
- `broker pub/sub`: publisher는 broker/topic에만 발행하고, 소비자는 나중에 따로 처리한다.

`ApplicationEvent`는 보통 두 번째에 더 가깝다.
Spring 컨테이너 내부에서 listener를 찾는 same-process event bus로 보면 맞고, Kafka처럼 durable broker라고 보면 틀리다.

따라서 "이벤트로 뺐다"는 말만으로 비동기, 내구성, 재시도, 장애 격리가 생겼다고 판단하면 안 된다. 실제 경계는 dispatch 방식, transaction phase, broker/outbox 유무가 결정한다.

중요한 질문은 "이벤트인가 아닌가"가 아니라 아래 세 가지다.

1. 이 작업이 **지금 같은 호출 흐름에서 반드시 같이 성공**해야 하는가
2. 실패가 나면 **호출자에게 즉시 전파**되어야 하는가
3. 재시도, 적재, 소비 지연 같은 **메시징 운영 의미**가 필요한가

## 한눈에 보기

| 지금 보이는 증상 | 먼저 볼 선택 | 이유 |
|---|---|---|
| `이거 실패하면 원래 요청도 실패해야 해` | `direct call` | 성공/실패와 순서를 코드에 가장 솔직하게 드러낸다 |
| `주문 완료 후 알림, 메트릭, 캐시 무효화가 붙는다` | `in-process observer` | 같은 프로세스 안의 후속 fan-out에 맞다 |
| `발행은 끝났는데 소비는 나중에 해도 된다` | `broker pub/sub` | publish와 consume를 분리하는 메시징 의미가 필요하다 |
| `Spring event면 Kafka처럼 재시도되나요?` | `ApplicationEvent = observer 쪽부터 확인` | 기본 Spring 이벤트는 broker의 durable delivery를 주지 않는다 |
| `listener 순서가 비즈니스 규칙이다` | `direct call` 또는 명시적 orchestration | 등록 순서에 정책을 싣기 시작하면 observer가 취약해진다 |

## 증상으로 고르는 15초 선택 카드

| 질문 | direct call | in-process observer | broker pub/sub |
|---|---|---|---|
| 호출자가 대상을 아는가 | 예 | listener 인터페이스 목록 정도만 안다 | broker/topic만 안다 |
| 보통 언제 실행되나 | 지금 즉시 | 지금 즉시인 경우가 많다 | 나중, 비동기인 경우가 많다 |
| 실패가 어디로 가나 | 바로 호출자에게 간다 | 같은 호출 흐름으로 전파되기 쉽다 | broker 정책과 consumer 처리에 따라 분리된다 |
| 재시도/적재/중복 제거를 기본으로 기대하나 | 아니오 | 아니오 | 보통 예 |
| 대표 질문 | `왜 그냥 메서드 호출하면 안 되지?` | `왜 listener 하나 실패했는데 다 같이 실패하지?` | `왜 발행은 됐는데 소비가 안 보이지?` |

빠른 기준은 이렇다.

- **핵심 정합성**이면 `direct call`
- **같은 프로세스 부가 반응 fan-out**이면 `observer`
- **운영 격리와 durable delivery**가 필요하면 `broker pub/sub`

## 상세 분해

### 1. direct call은 "결합이 높다"보다 "의도를 숨기지 않는다"가 장점이다

`paymentService.capture()` 다음에 `inventoryService.reserve()`를 호출하는 코드는 단순하다.
대신 장점도 분명하다.

- 순서가 코드에 그대로 보인다.
- 예외가 어디로 전파되는지 숨지 않는다.
- 한 트랜잭션 안에서 같이 성공해야 하는 일을 설명하기 쉽다.

그래서 `핵심 성공 경로`를 이벤트로 감추기 전에 먼저 direct call 후보인지 본다.
초보자가 자주 하는 오해는 "느슨한 결합이면 항상 더 좋은 설계"라는 생각인데, 정합성 경로에서는 보통 아니다.

### 2. in-process observer는 "이벤트처럼 보이는 메서드 fan-out"이다

옵저버는 발행자가 listener 구현체를 직접 모르고도 후속 반응을 붙일 수 있게 해 준다.
하지만 고전 옵저버와 많은 프레임워크 이벤트는 기본적으로 **같은 프로세스 안 호출**이다.

그래서 이런 증상이 나온다.

- listener 예외가 발행자까지 올라온다
- listener 순서가 암묵적 정책이 된다
- tracing 없이 보면 누가 반응했는지 흐려진다

즉 observer는 "비동기 분산 시스템"보다 "후속 반응 분리"에 먼저 초점을 둔다.
UI/plugin처럼 등록과 해제가 중요한 구조라면 [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)로 이어서 보는 편이 맞다.

### 3. broker pub/sub는 토폴로지보다 운영 의미가 더 커진다

Kafka, RabbitMQ, Redis Pub/Sub, 또는 durable internal bus를 쓰기 시작하면 질문이 달라진다.

- 발행 성공과 소비 성공을 분리해도 되는가
- 재시도와 중복 소비를 받아들일 것인가
- offset, ack, dead letter, consumer lag 같은 운영 단어를 감수할 것인가

이 단계부터는 "이벤트라는 이름"보다 **메시징 시스템의 계약**이 더 중요하다.
브로커 제품마다 순서 보장, 보관, 재전달 의미는 다르므로 `Pub/Sub는 항상 안전하다`처럼 일반화하면 안 된다.

### 4. Spring `ApplicationEvent`는 보통 observer 쪽에서 시작해야 덜 헷갈린다

Spring `ApplicationEventPublisher`는 publisher가 listener 구현체를 모른다는 점에서는 Pub/Sub처럼 보인다.
하지만 기본 해석은 아래가 더 정확하다.

- 같은 컨테이너 내부에서 listener를 찾는다
- 기본은 동기 실행이다
- durable broker처럼 적재/재시도를 기본 제공하지 않는다

즉 `ApplicationEvent = Kafka 축소판`으로 이해하면 오해가 생긴다.
`@Async`, `@TransactionalEventListener`, outbox를 붙이면 경계가 달라질 수 있지만, 그건 **추가 설계**이지 기본값이 아니다.

## 실전 시나리오

### 시나리오 1: 주문 완료 후 알림 발송

주문 서비스는 주문만 끝내고, 알림/포인트/로그는 observer나 event listener로 분리할 수 있다.

장점:
- 주문 로직이 얇아진다
- 후속 처리를 독립적으로 바꿀 수 있다
- 기능 추가가 이벤트 리스너 추가로 끝난다

주의:
- 동기 listener면 알림 실패가 주문 흐름에 다시 얹힐 수 있다
- 브로커로 넘기면 주문은 끝났는데 알림은 나중에 실패할 수 있다
- 브로커 소비자는 중복 발송을 염두에 둬야 한다

### 시나리오 2: Spring Security 인증 성공 이벤트

인증 성공 후 감사 로그나 사용자 마지막 로그인 시간을 갱신하는 데 유용하다.
하지만 인증 흐름에 핵심적인 정합성은 이벤트에 맡기면 안 된다.

### 시나리오 3: 메트릭과 캐시 무효화

캐시 무효화나 메트릭 집계는 이벤트와 잘 맞는다.
실패해도 다시 계산 가능하고, 약간의 지연이 허용되기 때문이다.

## 코드로 보기

### 1. direct call

```java
public class CheckoutService {
    private final PaymentService paymentService;
    private final InventoryService inventoryService;

    public void complete(Order order) {
        paymentService.capture(order);
        inventoryService.reserve(order);
    }
}
```

핵심 순서와 실패 경계가 눈에 보인다.
`이 두 개는 같이 성공해야 한다`가 요구사항이면 이런 코드가 오히려 더 정직하다.

### 2. Spring ApplicationEvent

```java
public record OrderCompletedEvent(Long orderId, Long userId) {}

@Service
public class OrderService {
    private final ApplicationEventPublisher publisher;

    public OrderService(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }

    @Transactional
    public void completeOrder(Long orderId, Long userId) {
        // 주문 상태 변경
        publisher.publishEvent(new OrderCompletedEvent(orderId, userId));
    }
}

@Component
public class OrderNotificationListener {
    @EventListener
    public void handle(OrderCompletedEvent event) {
        // 알림 전송
    }
}
```

이 코드는 publisher가 listener 구현을 모른다는 점에서 observer/event bus 감각을 준다.
하지만 기본은 같은 프로세스 안 동기 실행이다.

### 3. 비동기 리스너 주의

```java
@Async
@EventListener
public void handle(OrderCompletedEvent event) {
    // 트랜잭션 스레드가 아니다
}
```

비동기로 바꾸는 순간:

- 실행 순서가 바뀔 수 있다
- 예외 전파 방식이 달라진다
- 트랜잭션 컨텍스트가 자동으로 따라오지 않는다

즉 `@Async`를 붙였다고 broker pub/sub가 되는 것은 아니다.

## 흔한 오해와 함정

| 오해 | 실제로는 |
|---|---|
| `event`라는 이름이 붙으면 다 Pub/Sub다 | 같은 프로세스 안의 listener fan-out이면 observer나 framework event에 더 가깝다 |
| Spring `ApplicationEvent`는 기본으로 재시도되고 durable하다 | 기본은 same-process dispatch다. durable delivery가 필요하면 outbox나 broker를 별도로 설계해야 한다 |
| 느슨한 결합이면 direct call보다 항상 낫다 | 핵심 정합성, 순서, 즉시 실패 전파가 요구되면 direct call이 더 안전할 수 있다 |
| Pub/Sub는 항상 비동기라서 무조건 서비스 확장에 좋다 | 제품과 설정에 따라 의미가 다르고, 중복 소비나 운영 복잡도를 함께 감수해야 한다 |

## 더 깊이 가려면

- Spring 내부 timing/rollback 경계가 궁금하면 [Spring `@EventListener` vs `@TransactionalEventListener`: Timing, Ordering, Rollback](./spring-eventlistener-vs-transactionaleventlistener-timing.md)
- domain event와 integration event를 나누고 싶으면 [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
- broker 기반 발행 안정성이 궁금하면 [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)
- consumer 중복 처리와 projection 안전성이 궁금하면 [Idempotent Consumer and Projection Dedup Pattern](./idempotent-consumer-projection-dedup-pattern.md)

## 면접/시니어 질문 미리보기

> Q: Spring 이벤트는 왜 발행자와 리스너를 느슨하게 분리하는데도 조심해서 써야 하나요?
> 의도: 이벤트를 구조 분리 도구로만 보고, 트랜잭션/순서/실패를 놓치지 않는지 확인
> 핵심: 결합도는 낮아져도 기본 실행 의미는 같은 프로세스 호출이므로 순서, 실패, 타이밍을 따져야 한다

> Q: `ApplicationEvent`를 Kafka처럼 설명하면 왜 위험한가요?
> 의도: framework event와 broker messaging의 경계를 아는지 확인
> 핵심: same-process dispatch와 durable broker는 실패 경계와 운영 의미가 다르다

## 한 줄 정리

`이벤트`라는 단어보다 먼저 "지금 같이 실패해야 하나, 같은 프로세스 fan-out인가, broker 운영 계약이 필요한가"를 보면 direct call, observer, Pub/Sub 경계가 훨씬 덜 섞인다.
