# 옵저버 패턴 기초 (Observer Pattern Basics)

> 한 줄 요약: 옵저버 패턴은 상태 변화를 관찰자(Observer)에게 자동으로 알려줘서, 이벤트를 발생시키는 쪽과 반응하는 쪽의 결합을 끊어준다.

**난이도: 🟢 Beginner**

관련 문서:

- [옵저버 (Observer) 심화](./observer.md)
- [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Spring AOP 기초](../spring/spring-aop-basics.md)

retrieval-anchor-keywords: observer pattern basics, 옵저버 패턴 기초, 옵저버 패턴이 뭔가요, observer pattern beginner, 이벤트 알림 패턴, 상태 변화 알리기, subscribe notify pattern, subject observer, 옵저버 리스너 차이, event listener beginner, 옵저버 패턴 예시, beginner observer

---

## 핵심 개념

옵저버 패턴은 **한 객체(Subject)가 상태가 바뀌면 자신에게 등록된 여러 관찰자(Observer)에게 자동으로 통보**하는 구조다. Subject는 "누가 나를 보고 있는지" 목록만 유지하고, Observer는 각자 알림을 받아 원하는 작업을 수행한다.

입문자가 헷갈리는 점은 Subject가 Observer를 직접 호출하는 것처럼 보이지만, Subject는 Observer의 구체적인 타입을 몰라도 된다는 것이다. 인터페이스를 통해 호출하므로 새 Observer를 추가해도 Subject 코드를 바꾸지 않아도 된다.

## 한눈에 보기

```
OrderService (Subject)
    │ notifyObservers(event)
    ├──→ EmailNotifier (Observer)
    ├──→ SlackNotifier (Observer)
    └──→ AuditLogger (Observer)
```

| 역할 | 책임 |
|------|------|
| Subject | Observer 목록 관리, 변경 시 `notify()` 호출 |
| Observer | `update(event)` 메서드 구현, 알림 수신 처리 |
| 등록/해제 | `subscribe()` / `unsubscribe()` |

## 상세 분해

옵저버 패턴의 흐름은 세 단계다.

- **등록(Subscribe)** — Observer가 Subject에 자신을 등록한다. Subject는 Observer 목록에 추가한다.
- **이벤트 발생** — Subject의 상태가 바뀌면 `notifyAll()`을 호출한다.
- **알림 수신(Update)** — Subject는 목록의 모든 Observer에게 `update(event)`를 호출한다. 각 Observer가 독립적으로 반응한다.

Subject와 Observer는 공통 인터페이스로만 연결되므로, 새 Observer를 추가하는 것은 기존 코드를 건드리지 않는다.

## 흔한 오해와 함정

- **"Observer는 알림을 받을 때까지 기다린다"** — 기본 옵저버 패턴은 동기 호출이다. Subject가 `notify()`를 부르면 Observer가 즉시 `update()`를 실행한다. 비동기 처리가 필요하면 이벤트 큐를 별도로 두어야 한다.
- **"등록만 하면 된다"** — Observer를 등록하면 반드시 해제(unsubscribe)도 관리해야 한다. 해제하지 않으면 객체가 메모리에 남아 메모리 누수가 생긴다.
- **"Pub/Sub과 같다"** — 옵저버 패턴은 같은 프로세스 안에서 직접 호출한다. Pub/Sub은 브로커를 통해 비동기로 메시지를 전달한다는 점에서 다르다.

## 실무에서 쓰는 모습

주문이 완료됐을 때 이메일 알림, Slack 알림, 감사 로그를 각각 독립적으로 처리하고 싶다면, 주문 완료 이벤트를 하나만 발행하고 각 Observer가 받아 처리하게 한다. 새 알림 채널을 추가할 때는 Observer 하나만 더 만들어 등록하면 된다.

Spring에서는 `ApplicationEventPublisher.publishEvent()`와 `@EventListener`가 옵저버 패턴을 Spring 방식으로 구현한 것이다.

## 더 깊이 가려면

- [옵저버 (Observer) 심화](./observer.md) — ordering/failure boundary, observer vs direct call 비교
- [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md) — Spring 이벤트와 메시지 브로커의 차이

## 면접/시니어 질문 미리보기

> Q: 옵저버 패턴에서 Subject와 Observer의 결합도는 어느 수준인가?
> 의도: 패턴의 결합도 특성을 이해하는지 확인한다.
> 핵심: Subject는 Observer 인터페이스에만 의존하므로 구체 클래스를 몰라도 된다.

> Q: Observer를 해제하지 않으면 어떤 문제가 생기나?
> 의도: 리소스 관리 감각이 있는지 확인한다.
> 핵심: Subject가 Observer 참조를 유지해 GC 대상이 되지 않아 메모리 누수가 발생한다.

> Q: 옵저버 패턴과 Spring `@EventListener`의 관계는?
> 의도: 패턴과 프레임워크를 연결하는지 확인한다.
> 핵심: `@EventListener`가 옵저버 패턴의 Observer 역할을 하고, `ApplicationEventPublisher`가 Subject 역할을 한다.

## 한 줄 정리

옵저버 패턴은 Subject가 Observer 목록에 변경을 알려 결합을 끊어주며, 새 Observer 추가 시 Subject 코드를 수정하지 않아도 된다.
