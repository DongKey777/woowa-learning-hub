# Outbound Notifier Mock Boundary Primer

> 한 줄 요약: `알림을 보냈다`, `이벤트를 발행했다`처럼 outbound notifier의 핵심 질문이 호출 자체일 때는, repository fake처럼 상태를 재현하기보다 mock/spy로 상호작용 경계를 먼저 잠그는 편이 초심자에게 더 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md)
- [Repository Fake Design Guide](./repository-fake-design-guide.md)
- [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)
- [옵저버, Pub/Sub, ApplicationEvent](../design-pattern/observer-pubsub-application-events.md)
- [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](../spring/spring-service-layer-external-io-after-commit-outbox-primer.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: outbound notifier mock boundary, notifier mock first, event publisher mock first, 알림 mock 왜 먼저, 이벤트 발행 mock 먼저, notifier fake vs mock, 처음 notifier 테스트, interaction verification beginner, outbound port side effect basics, notification boundary test, what is notifier mock, mock spy notifier basics

## 핵심 개념

이 문서의 질문은 "`repository는 fake를 권하던데, 왜 알림/notifier는 mock이 먼저예요?`"다.

핵심 차이는 경계가 돌려주는 것이 다르기 때문이다.

- repository는 보통 `저장 후 다시 읽었을 때 어떤 상태인가`를 묻는다.
- notifier, event publisher는 보통 `이 부작용을 실제로 요청했는가`를 묻는다.

그래서 repository 경계는 메모리 fake로 결과를 읽기 쉽고, notifier 경계는 mock/spy로 호출 자체를 읽기 쉽다.

## 한눈에 보기

| 지금 확인하려는 질문 | 더 먼저 고를 것 | 이유 |
|---|---|---|
| "`중복 주문번호면 실패하나?`" | fake repository | 저장/조회 결과가 질문의 중심이다 |
| "`주문 성공 시 알림을 1번 보냈나?`" | mock/spy notifier | 호출 자체가 비즈니스 결과다 |
| "`이벤트 payload에 주문 번호가 담겼나?`" | mock captor 또는 contract test | 발행 여부와 전달 값이 핵심이다 |
| "`알림이 유실되면 안 되나?`" | mock만으로 끝내지 말고 outbox/통합 테스트 | 내구성은 unit mock이 아니라 전달 설계 문제다 |

- 짧게 외우면 `상태를 다시 읽는 경계는 fake`, `부작용을 요청하는 경계는 mock`이다.
- notifier는 "`호출했는가`"가 먼저고, repository는 "`저장 결과가 맞는가`"가 먼저다.

## 왜 notifier와 event publisher는 mock이 먼저인가

notifier는 대개 `send()`, `publish()`, `notifyOrderPlaced()` 같은 메서드 하나가 일 자체다.
이 경계에서 초심자가 가장 먼저 확인하려는 것은 보통 아래 둘이다.

- 성공한 유스케이스에서 알림 요청이 발생했는가
- 실패한 유스케이스에서 알림 요청이 발생하지 않았는가

이 질문은 메모리 fake를 만들어 "`보낸 알림 목록`"을 읽어도 풀 수는 있다.
하지만 beginner starter에서는 fake가 곧 "`알림 저장소`"처럼 보이기 시작해, 실제 관심사인 상호작용 경계보다 구현물이 더 커지기 쉽다.

mock/spy는 질문을 더 직접적으로 남긴다.

```java
OrderNotifier notifier = mock(OrderNotifier.class);

service.place(command("ORDER-001"));

then(notifier).should().notifyOrderPlaced("ORDER-001");
```

이 테스트가 먼저 말하는 문장은 "`주문 성공 시 알림 요청이 간다`"다.
repository fake 문서처럼 저장 semantics를 재현할 필요가 없으니, 초심자에게는 이 편이 경계를 덜 흐린다.

## repository fake와 어디서 갈라지나

같은 service 안에서도 질문이 다르면 test double 선택이 달라진다.

| 같은 주문 service에서 | repository 경계 | notifier 경계 |
|---|---|---|
| 질문의 중심 | 저장/조회 결과 | 부작용 요청 여부 |
| 먼저 읽는 문장 | "`중복이면 실패한다`" | "`성공하면 알림을 보낸다`" |
| starter에 더 쉬운 선택 | fake | mock/spy |

즉 "`fake가 더 진짜 같으니 모든 outbound port에 fake를 쓰자`"가 아니다.
repository fake는 저장 계약을 읽기 위해 유리하고, notifier mock은 상호작용 계약을 읽기 위해 유리하다.

이 분리를 먼저 해 두면 [Repository Fake Design Guide](./repository-fake-design-guide.md)가 notifier 규칙까지 떠안지 않아도 된다.

## 흔한 오해와 함정

- "`알림도 fake로 모아 두면 더 자연스럽지 않나요?`"
  경우에 따라 가능하지만, beginner의 첫 질문이 호출 여부라면 mock이 더 짧고 직접적이다.
- "`event publisher니까 무조건 mock이면 끝인가요?`"
  아니다. payload 매핑, schema 호환성, outbox relay, consumer 계약은 별도 테스트 층이 필요하다.
- "`알림을 1번 보냈는지만 보면 충분한가요?`"
  아니다. `언제` 보내는지, 실패 시 보내지 말아야 하는지, commit 뒤로 미뤄야 하는지도 함께 봐야 한다.
- "`mock을 쓰면 구현 상세에 묶이지 않나요?`"
  `save()를 몇 번 불렀나` 같은 내부 저장 순서를 과하게 검증하면 그렇다. 하지만 notifier에서는 `보냈는가/안 보냈는가` 자체가 경계 계약일 때가 많다.

## 실무에서 쓰는 모습

주문 성공 뒤 고객에게 확인 알림을 보내는 service를 생각해 보자.

```java
void place(PlaceOrderCommand command) {
    Order order = orderRepository.save(Order.create(command));
    notifier.notifyOrderPlaced(order.number());
}
```

여기서 첫 beginner test를 두 갈래로 나누면 읽기가 쉬워진다.

| 확인 대상 | 추천 테스트 방향 | 이유 |
|---|---|---|
| 중복 주문번호면 실패 | fake repository | 결과 상태가 먼저다 |
| 성공 주문이면 알림 발송 | mock notifier | 호출 자체가 먼저다 |
| commit 뒤 발송 보장, 유실 방지 | integration/outbox 쪽 후속 테스트 | timing과 durability는 unit mock 범위를 넘는다 |

즉 unit test에서 notifier mock은 "`호출 경계`"만 잠근다.
전달 보장까지 묻는 순간에는 [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md)나 [Spring Service-Layer Primer: 외부 I/O는 트랜잭션 밖으로, 후속 부작용은 `AFTER_COMMIT` vs Outbox로 나누기](../spring/spring-service-layer-external-io-after-commit-outbox-primer.md)로 올라가야 한다.

## 더 깊이 가려면

- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md): `결과를 읽는가 / 호출을 읽는가` 기준을 먼저 짧게 잡고 싶을 때
- [Repository Fake Design Guide](./repository-fake-design-guide.md): repository fake를 어디까지 재현해야 하는지 이어서 볼 때
- [Domain Event, Outbox, Inbox](./outbox-inbox-domain-events.md): notifier mock 다음 단계인 전달 보장과 비동기 경계를 배우고 싶을 때
- [옵저버, Pub/Sub, ApplicationEvent](../design-pattern/observer-pubsub-application-events.md): 같은 프로세스 notification과 event-driven 분기를 더 넓게 비교하고 싶을 때

## 한 줄 정리

repository는 `저장 결과`를 읽으니 fake가 잘 맞고, outbound notifier는 `부작용 요청`을 읽으니 mock/spy가 먼저라는 기준만 잡아도 초심자 테스트 경계가 훨씬 덜 헷갈린다.
