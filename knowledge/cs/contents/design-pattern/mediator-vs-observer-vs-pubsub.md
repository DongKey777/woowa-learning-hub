---
schema_version: 3
title: Mediator vs Observer vs Pub/Sub
concept_id: design-pattern/mediator-vs-observer-vs-pubsub
canonical: false
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
  - coordination-vs-notification
  - event-bus-overuse
  - workflow-coordinator-boundary
aliases:
  - mediator vs observer vs pubsub
  - coordination vs notification
  - same process event bus
  - brokered messaging in process
  - mediator workflow coordination
  - observer state change notification
  - in process pubsub
  - application event vs mediator
  - event bus topic subscriber
  - checkout coordination pattern
symptoms:
  - 중앙 coordinator를 둘지 이벤트로 풀지 판단이 안 서
  - 같은 프로세스 event bus를 쓰면 observer인지 pubsub인지 계속 헷갈려
  - workflow 조정 로직과 상태 변화 알림을 한 구조로 묶어 버리고 있어
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - design-pattern/observer-pubsub-application-events
  - design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
next_docs:
  - design-pattern/saga-coordinator-pattern-language
  - design-pattern/coordinator-vs-manager-object-smell
  - design-pattern/orchestration-vs-choreography-pattern-language
linked_paths:
  - contents/design-pattern/observer-pubsub-application-events.md
  - contents/design-pattern/observer.md
  - contents/design-pattern/observer-lifecycle-hygiene.md
  - contents/design-pattern/state-pattern-workflow-payment.md
  - contents/design-pattern/saga-coordinator-pattern-language.md
  - contents/design-pattern/coordinator-vs-manager-object-smell.md
  - contents/design-pattern/orchestration-vs-choreography-pattern-language.md
confusable_with:
  - design-pattern/observer-pubsub-application-events
  - design-pattern/observer-vs-pubsub-vs-domain-event-decision-guide
  - design-pattern/saga-coordinator-pattern-language
forbidden_neighbors: []
expected_queries:
  - 화면 단계 조정 로직은 mediator로 봐야 해 아니면 event listener로 풀어야 해?
  - 같은 프로세스에서 topic bus를 쓰면 observer와 뭐가 달라?
  - checkout coordinator, application event, pubsub를 한 번에 구분하는 기준이 뭐야?
  - 상태 변경 통지와 다음 행동 결정이 왜 다른 패턴인지 예시로 설명해줘
  - 리스너가 많아졌을 때 mediator로 올릴지 pubsub로 갈지 판단이 안 돼
contextual_chunk_prefix: |
  이 문서는 advanced 학습자가 workflow coordination, state-change
  notification, same-process pubsub를 구분하도록 돕는 chooser다.
  mediator가 다음 행동을 결정하는지, observer가 이미 일어난 변화를
  전파하는지, bus/topic이 publisher와 subscriber 사이를 중개하는지
  묻는 자연어 질문이 이 문서의 비교 기준에 매핑된다.
---
# Mediator vs Observer vs Pub/Sub

> 한 줄 요약: Mediator는 **같은 유스케이스 안에서 다음 행동을 결정**하고, Observer는 **이미 일어난 상태 변화를 통지**하며, Pub/Sub는 **같은 프로세스 안에서도 bus/topic으로 발행자와 구독자를 brokered messaging으로 분리**한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [옵저버 (Observer)](./observer.md)
> - [Observer Lifecycle Hygiene](./observer-lifecycle-hygiene.md)
> - [상태 패턴: 워크플로와 결제 상태를 코드로 모델링하기](./state-pattern-workflow-payment.md)
> - [Saga / Coordinator](./saga-coordinator-pattern-language.md)
> - [Coordinator vs Manager Object Smell](./coordinator-vs-manager-object-smell.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)

retrieval-anchor-keywords: mediator vs observer vs pubsub, coordination vs notification, same-process event bus, brokered messaging in process, mediator workflow coordination, observer state change notification, in-process pubsub, application event vs mediator, event bus topic subscriber, checkout coordination pattern, plugin event bus, same process broker

---

## 이 문서는 언제 읽으면 좋은가

- 화면 컴포넌트나 workflow step들이 서로 영향을 주는데, 중앙 coordinator로 묶어야 할지 이벤트로 풀어야 할지 헷갈릴 때
- "같은 프로세스인데 event bus/topic을 쓰면 이건 Observer인가 Pub/Sub인가?"가 계속 애매할 때
- `CheckoutManager`, `WorkflowCoordinator`, `ApplicationEventPublisher`가 한 문서 안에서 섞여 보일 때

핵심은 "느슨한 결합"이 아니라 **누가 다음 행동을 결정하는가**, **상태 변화인지 메시지 라우팅인지**, **bus가 중간 경계로 존재하는가**다.

---

## 30초 선택 가이드

질문을 세 개로 쪼개면 대부분 바로 갈린다.

1. **여러 참가자의 다음 행동을 중앙에서 결정해야 하는가?**
   배송비 재계산, 버튼 활성화, 다음 단계 진입처럼 한 유스케이스의 흐름을 정해야 하면 Mediator 쪽이다.
2. **이미 일어난 상태 변화에 여러 리스너가 반응하면 되는가?**
   주문 완료 후 알림, 메트릭, 캐시 무효화라면 Observer 쪽이다.
3. **발행자가 구독자 목록을 몰라야 하고, topic/bus가 라우팅을 맡아야 하는가?**
   plugin host, internal event bus, module extension point처럼 brokered messaging이 필요하면 Pub/Sub 쪽이다.

짧게 외우면 다음과 같다.

- Mediator: **조정**
- Observer: **통지**
- Pub/Sub: **브로커를 둔 전파**

같은 프로세스 안에서도 bus/topic이 있으면 Pub/Sub로 보는 편이 실전 판단에 더 도움이 된다.
"분산 시스템이냐 아니냐"는 Pub/Sub의 정의보다 **운영 복잡도를 얼마나 더 감수하느냐**에 가깝다.

---

## 한눈에 구분

| 질문 | Mediator | Observer | Pub/Sub (same-process bus 포함) |
|---|---|---|---|
| 출발점 | "누가 다음에 무엇을 해야 하지?" | "상태가 바뀌었으니 누가 반응하지?" | "이 메시지를 누가 구독 중이지?" |
| 중심 객체 | 조율자(mediator) | 주체(subject) + listener | bus / broker / topic |
| 발신자가 아는 것 | mediator만 안다 | 대개 listener 목록 또는 프레임워크 등록점 | bus와 topic만 안다 |
| 흐름 소유권 | mediator가 순서와 조건을 결정 | 주체는 통지만 하고 반응은 listener가 맡음 | publisher는 발행만 하고 라우팅은 bus가 맡음 |
| 반환값 / 즉답 상호작용 | 자연스럽다 | 보통 부자연스럽다 | 더 부자연스럽다 |
| 순서 의미 | mediator 코드에 드러내기 쉽다 | listener 등록 순서에 기대기 쉽다 | bus 정책이나 subscriber 구현에 의존 |
| 실패 경계 | coordinator 정책으로 통제 가능 | listener 예외가 호출 흐름에 남기 쉽다 | publish 성공과 subscriber 처리 성공을 분리하기 쉽다 |
| 잘 맞는 예시 | checkout form, wizard, approval flow | 알림, 감사 로그, 캐시 무효화 | plugin extension, internal module bus, telemetry fan-out |
| 냄새 신호 | mediator가 모든 도메인 규칙을 빨아들임 | listener 순서가 비즈니스 규칙이 됨 | request/response를 event bus로 흉내 냄 |

표를 한 문장으로 줄이면:

- **흐름 결정을 중앙에 모으면 Mediator**
- **확정된 변화의 후속 반응이면 Observer**
- **발행자와 구독자를 bus/topic으로 떼어 놓으면 Pub/Sub**

---

## 같은 프로세스 결정 매트릭스

아래 표는 "coordination vs notification vs brokered messaging"을 같은 프로세스 기준으로 더 빡빡하게 고르는 표다.

| 요구사항 | 1차 선택 | 이유 | 이 선택을 피해야 하는 신호 |
|---|---|---|---|
| 여러 입력 상태를 함께 보고 다음 UI/워크플로 액션을 결정해야 한다 | Mediator | 여러 동료 객체의 상호작용 규칙을 한곳에 둔다 | mediator가 단순 전달자일 뿐이면 과한 추상화다 |
| 상태 변경 뒤에 여러 내부 반응이 따라붙는다 | Observer | subject가 상태 변화를 fan-out하기 가장 단순하다 | listener 순서나 재시도가 핵심 정책이면 단순 observer로는 부족하다 |
| 발행자는 확장 모듈이 무엇인지 모르고 topic 기반으로만 내보내야 한다 | Pub/Sub | brokered messaging으로 module/plugin 결합을 낮춘다 | subscriber 결과를 모아 즉시 의사결정해야 하면 bus가 맞지 않는다 |
| 핵심 정합성이 한 트랜잭션 안에서 반드시 같이 성공해야 한다 | 직접 호출 또는 명시적 orchestration | 성공/실패와 순서를 코드에 솔직하게 드러낸다 | 이벤트로 숨기면 실패 경계가 흐려진다 |
| listener를 런타임에 붙였다 떼거나 서드파티 plugin을 허용해야 한다 | Pub/Sub | subscriber 등록/해제를 publisher와 분리하기 쉽다 | subscriber 수가 적고 고정이면 observer가 더 단순하다 |

같은 프로세스에서 자주 하는 오해는 이렇다.

- `ApplicationEventPublisher`를 쓴다고 자동으로 비동기/분산 메시징이 되는 것은 아니다.
- bus가 있다고 해서 mediator가 필요 없는 것도 아니다.
- observer로 시작했는데 listener 사이의 순서와 조건이 중요해지면 mediator나 명시적 orchestrator로 되돌아가는 편이 낫다.

---

## 깊이 들어가기

### 1. Mediator는 반응을 모으는 패턴이 아니라 "결정권"을 모으는 패턴이다

Mediator의 핵심은 "누가 누구에게 알려준다"가 아니다.
**서로 영향을 주는 참가자들의 다음 행동을 한곳에서 결정한다**는 점이 핵심이다.

예를 들어 checkout 화면에서:

- 배송지 변경이 배송비 계산을 바꾸고
- 쿠폰 선택이 결제 수단 가능 여부를 바꾸고
- 결제 수단 선택이 할부 노출을 바꾸는 경우

이 관계를 각 컴포넌트가 서로 직접 알면 곧바로 spaghetti가 된다.
Mediator는 이 얽힘을 중앙의 정책 객체로 끌어온다.

그래서 Mediator가 맞는 질문은 "누가 이벤트를 듣지?"가 아니라:

- 어떤 입력 조합에서 다음 버튼을 열지
- 어떤 순서로 검증과 재계산을 할지
- 어떤 참가자에게 어떤 command를 보낼지

같은 **조정 질문**이다.

반대로 mediator가 단순히 `onXChanged -> bus.publish("x.changed")`만 한다면 조정이 아니라 중계일 가능성이 높다.

### 2. Observer는 의사결정이 끝난 뒤의 notification fan-out이다

Observer는 **상태 변화가 이미 결정된 뒤**에 반응을 퍼뜨리는 패턴이다.

- 주문이 완료되었다
- 회원 등급이 변경되었다
- 캐시 무효화가 필요해졌다

이 시점의 질문은 "다음 핵심 행동을 무엇으로 정할까?"가 아니라
"이 사실을 알고 반응해야 하는 내부 리스너가 누구인가?"다.

즉 Observer는 흐름의 중심을 잡는 패턴이 아니라 **후속 반응을 분리하는 패턴**이다.

여기서 중요한 경계는 두 가지다.

1. listener의 성공 여부가 주 흐름 성공과 어떻게 연결되는가
2. listener 실행 순서가 정책인가, 그냥 구현 우연인가

이 두 가지가 중요해지는 순간 단순 observer 설명만으로는 부족하고,
[옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md) 같은 실행 의미 문서까지 같이 봐야 한다.

### 3. Pub/Sub는 같은 프로세스 안에서도 "brokered messaging"이라는 점이 본질이다

Pub/Sub를 "서비스 간 비동기 연동"으로만 좁히면 실무에서 자주 헷갈린다.
같은 프로세스 안에서도 아래 구조면 Pub/Sub 감각으로 보는 편이 정확하다.

- publisher가 subscriber 목록을 모른다
- topic이나 event type이 라우팅 키가 된다
- bus가 중간에 subscriber를 연결한다
- subscriber는 동적으로 추가/제거될 수 있다

예를 들면:

- monolith 내부 plugin extension point
- IDE/plugin host의 internal event bus
- module 간 telemetry/event fan-out
- framework가 제공하는 application event bus

이 구조는 observer와 실행 시점이 비슷할 수 있다.
하지만 **토폴로지와 확장 방식**은 bus 중심이므로 brokered messaging 쪽이다.

즉 "같은 프로세스 = observer"라고 단순화하면 안 된다.
같은 프로세스여도 bus/topic이 있으면 publisher와 subscriber 관계는 Pub/Sub처럼 설계해야 한다.

### 4. 같은 도구라도 질문이 다르면 분류가 달라진다

특히 Spring `ApplicationEventPublisher`나 사내 event bus는 자주 혼동된다.

| 메커니즘 | 더 가까운 사고방식 | 이유 |
|---|---|---|
| `listeners.forEach(listener -> listener.onX())` | Observer | subject가 listener fan-out을 직접 소유한다 |
| `publisher.publishEvent(new X())` | Pub/Sub에 가까운 same-process bus | publisher는 listener 목록을 모르고 bus에만 발행한다 |
| `checkoutMediator.onCouponSelected()` | Mediator | 중앙 객체가 다음 계산과 UI state를 결정한다 |

그래서 질문을 바꿔 보면 분류가 쉬워진다.

- **누가 다음 단계를 정하나?** → Mediator
- **누가 상태 변화를 듣나?** → Observer
- **누가 메시지를 라우팅하나?** → Pub/Sub

---

## 실전 시나리오

### 시나리오 1: 주문 생성 UI와 승인 버튼 활성화

배송지, 쿠폰, 결제 수단, 약관 동의가 서로 영향을 주면 Mediator가 자연스럽다.
여기서 필요한 것은 "누구에게 알릴까"보다 **어떤 조합에서 어떤 상태를 만들까**라는 조정 규칙이다.

### 시나리오 2: 주문 완료 후 메트릭과 감사 로그

주문 완료라는 상태 변화 뒤에 메트릭 적재, 감사 로그, 캐시 무효화가 따라붙는다면 Observer가 충분하다.
주문의 핵심 흐름은 이미 끝났고, 이제는 notification fan-out이 핵심이다.

### 시나리오 3: 같은 프로세스의 plugin host

editor core가 `"document.saved"` topic만 발행하고, lint plugin, analytics plugin, sync plugin이 각자 구독한다면 same-process Pub/Sub다.
publisher는 plugin 목록을 몰라야 하고, plugin은 나중에 동적으로 추가될 수 있다.

### 시나리오 4: observer로 시작했는데 listener 순서가 정책이 된 경우

`검증 -> 포인트 차감 -> 알림`이 정확한 순서로 묶여야 하고, 한 단계 실패 시 다음 단계를 막아야 한다면
Observer보다 명시적 orchestration이나 Mediator 쪽이 더 솔직하다.

---

## 코드로 보기

### Mediator

```java
public interface CheckoutMediator {
    void onCouponSelected(String couponId);
    void onShippingAddressChanged(Address address);
    void onPaymentMethodChanged(PaymentMethod paymentMethod);
}

public class DefaultCheckoutMediator implements CheckoutMediator {
    private final CheckoutForm form;
    private final PricingService pricingService;

    public DefaultCheckoutMediator(CheckoutForm form, PricingService pricingService) {
        this.form = form;
        this.pricingService = pricingService;
    }

    @Override
    public void onCouponSelected(String couponId) {
        form.applyCoupon(couponId);
        form.updateTotal(pricingService.calculate(form.snapshot()));
        form.refreshSubmitState();
    }

    @Override
    public void onShippingAddressChanged(Address address) {
        form.changeAddress(address);
        form.updateDeliveryOptions();
        form.updateTotal(pricingService.calculate(form.snapshot()));
    }

    @Override
    public void onPaymentMethodChanged(PaymentMethod paymentMethod) {
        form.changePaymentMethod(paymentMethod);
        form.refreshAvailableInstallments();
        form.refreshSubmitState();
    }
}
```

### Observer

```java
public class Order {
    private final List<OrderListener> listeners = new ArrayList<>();

    public void addListener(OrderListener listener) {
        listeners.add(listener);
    }

    public void complete() {
        this.status = OrderStatus.COMPLETED;
        listeners.forEach(listener -> listener.onCompleted(this));
    }
}
```

### Pub/Sub

```java
public interface EventBus {
    <T> void subscribe(String topic, Class<T> type, Consumer<T> handler);
    void publish(String topic, Object event);
}

public record DocumentSaved(Long documentId) {}

public class EditorCore {
    private final EventBus eventBus;

    public EditorCore(EventBus eventBus) {
        this.eventBus = eventBus;
    }

    public void save(Long documentId) {
        eventBus.publish("document.saved", new DocumentSaved(documentId));
    }
}

public class AnalyticsPlugin {
    public AnalyticsPlugin(EventBus eventBus) {
        eventBus.subscribe("document.saved", DocumentSaved.class, this::onSaved);
    }

    private void onSaved(DocumentSaved event) {
        // analytics fan-out
    }
}
```

세 예제의 차이는 단순하다.

- Mediator는 **publisher/participant가 응답을 기대하며 중앙 결정에 들어간다**
- Observer는 **subject가 자신의 상태 변화 사실을 listener에게 알린다**
- Pub/Sub는 **publisher가 bus에만 말하고 subscriber 연결은 broker가 맡는다**

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 참조 / 명시적 orchestration | 순서, 실패, 반환값이 가장 명확하다 | 결합도가 높아진다 | 핵심 정합성과 단계 순서가 중요한 유스케이스 |
| Mediator | 상호작용 규칙이 한곳에 모인다 | 중앙 조율자가 비대해질 수 있다 | 여러 참가자의 상태를 함께 보고 다음 행동을 결정할 때 |
| Observer | 상태 변화 뒤의 내부 반응을 분리하기 쉽다 | 순서와 실패 의미가 흐려지기 쉽다 | 같은 프로세스 안의 단순 notification fan-out |
| Pub/Sub | publisher와 subscriber를 bus로 강하게 분리할 수 있다 | request/response와 즉답 흐름에는 맞지 않는다 | 같은 프로세스 plugin/module 확장이나 더 큰 메시징 구조로 이어질 때 |

판단 기준은 다음 세 줄이면 충분하다.

- **대화 자체를 중앙에서 정리**하려면 Mediator
- **결정된 결과를 듣게** 하려면 Observer
- **broker가 전달 관계를 소유**해야 하면 Pub/Sub

---

## 꼬리질문

> Q: 같은 프로세스의 `ApplicationEventPublisher`는 Observer인가요, Pub/Sub인가요?
> 의도: 실행 시점과 토폴로지를 분리해서 설명할 수 있는지 확인한다.
> 핵심: 실행은 observer처럼 동기일 수 있지만, 발행자-구독자 관계는 same-process Pub/Sub처럼 bus가 중간에 선다.

> Q: Observer로 시작했는데 listener 순서가 중요해지면 어떻게 해야 하나요?
> 의도: notification과 orchestration 경계를 다시 잡는지 확인한다.
> 핵심: 순서와 실패가 정책이 되면 명시적 orchestration이나 Mediator로 되돌아가는 편이 낫다.

> Q: Mediator가 커지면 무엇을 의심해야 하나요?
> 의도: 중앙 조율자와 god object를 구분하는지 확인한다.
> 핵심: use case별 coordinator 분리, state machine, policy object 분해를 검토해야 한다.

## 한 줄 정리

Mediator는 **다음 행동을 정하는 중앙 조율자**, Observer는 **상태 변화의 후속 통지**, Pub/Sub는 **같은 프로세스 안에서도 bus/topic으로 라우팅되는 brokered messaging**이다.
