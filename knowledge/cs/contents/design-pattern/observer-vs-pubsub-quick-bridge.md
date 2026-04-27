# 옵저버 vs Pub-Sub: 처음 읽을 때 바로 잡는 짧은 다리

> 한 줄 요약: 옵저버는 보통 **같은 프로세스 안에서 바로 알리는 구조**이고, Pub-Sub는 **브로커나 bus를 사이에 두고 나중에 퍼뜨리는 구조**로 먼저 이해하면 첫 혼동을 크게 줄일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [옵저버 패턴 기초](./observer-basics.md)
> - [옵저버 (Observer)](./observer.md)
> - [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
> - [Mediator vs Observer vs Pub/Sub](./mediator-vs-observer-vs-pubsub.md)
> - [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
> - [Outbox Relay and Idempotent Publisher](./outbox-relay-idempotent-publisher.md)

retrieval-anchor-keywords: observer vs pubsub quick bridge, observer vs pub-sub beginner, same process notification vs broker async propagation, 옵저버 vs pubsub 차이, 같은 프로세스 알림 vs 브로커 비동기 전파, observer same process fan-out, pubsub broker topic queue beginner, spring application event vs kafka beginner, observer not async, pubsub not same as observer, beginner event pattern comparison, observer vs pubsub quick bridge basics, observer vs pubsub quick bridge beginner, observer vs pubsub quick bridge intro, design pattern basics

---

## 먼저 잡는 멘탈 모델

- 옵저버: 한 방 안에서 누군가 소리치면, 그 방 안의 등록된 사람들이 바로 듣는다.
- Pub-Sub: 게시판이나 메신저 방에 글을 올리면, 중간 시스템이 구독자들에게 나중에 전달한다.

처음에는 이 정도로만 잡아도 충분하다.

- **같은 프로세스 안에서 바로 알림 fan-out**이면 옵저버 쪽
- **브로커, topic, queue, event bus가 중간에 있으면** Pub-Sub 쪽

용어보다 먼저 봐야 할 것은 "중간 전달자가 있는가"와 "지금 바로 같이 실행되는가"다.

## 30초 비교표

| 질문 | 옵저버 | Pub-Sub |
|---|---|---|
| 보통 어디서 쓰나 | 같은 프로세스 내부 | 프로세스/서비스 경계, 또는 bus가 있는 내부 시스템 |
| 전달 방식 | 발행 쪽이 등록된 listener를 직접 fan-out | 브로커나 bus가 구독자에게 전달 |
| 실행 시점 감각 | 보통 즉시, 보통 동기 | 대개 비동기, 지연 가능 |
| 실패 경계 | listener 예외가 발행 흐름에 붙기 쉽다 | 발행 성공과 소비 성공을 분리하기 쉽다 |
| 대표 예시 | UI listener, domain object listener, Spring 내부 이벤트 | Kafka, RabbitMQ, Redis Pub/Sub, internal event bus |

## 1분 예시

주문 완료 후 이메일 알림을 생각해 보자.

- 옵저버: `OrderService`가 주문 완료 직후 등록된 `EmailListener`, `MetricsListener`를 같은 프로세스 안에서 바로 호출한다.
- Pub-Sub: `OrderCompleted`를 Kafka topic에 발행하고, 이메일 서비스와 분석 서비스가 각자 나중에 소비한다.

둘 다 "주문 완료를 알린다"는 점은 같지만, 실행 의미는 꽤 다르다.

- 옵저버는 주문 처리 코드와 후속 반응이 같은 실행 흐름에 묶이기 쉽다.
- Pub-Sub는 발행 후 소비가 늦게 일어나거나 재시도될 수 있다.

## 자주 헷갈리는 포인트

- `event`라는 단어를 쓴다고 다 Pub-Sub는 아니다. 같은 프로세스의 listener 호출이면 옵저버에 더 가깝다.
- 옵저버라고 해서 자동으로 느린 시스템에 강해지지 않는다. 기본은 그냥 메서드 호출 fan-out이다.
- Pub-Sub라고 해서 꼭 다른 서버여야 하는 것은 아니다. 같은 프로세스여도 topic/bus가 중간 라우팅을 맡으면 Pub-Sub처럼 보는 편이 맞다.

## 이렇게 고르면 덜 헷갈린다

1. 이 반응들이 **지금 바로 같이 실행**돼도 되는가
2. 발행 쪽이 **listener 목록을 직접 관리**하는가
3. 아니면 **브로커나 bus가 전달 책임**을 가져가는가

짧게 자르면:

- `바로 알림 + 직접 listener fan-out`이면 옵저버
- `중간 bus/broker + 구독 전달`이면 Pub-Sub

## 다음에 어디로 읽을까

- Spring `ApplicationEvent`가 옵저버인지 Pub-Sub인지 더 헷갈리면 [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
- 같은 프로세스 안의 ordering/failure 경계를 더 보고 싶으면 [옵저버 (Observer)](./observer.md)
- 브로커 기반 전파에서 domain event와 integration event를 나누고 싶으면 [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)

## 한 줄 정리

옵저버는 보통 **같은 프로세스 안의 즉시 알림**, Pub-Sub는 보통 **브로커나 bus를 둔 비동기 전파**로 먼저 구분하면 초반 혼동을 크게 줄일 수 있다.
