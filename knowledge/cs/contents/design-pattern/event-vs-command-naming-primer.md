# Event vs Command Naming Primer

> 한 줄 요약: `OrderCompletedEvent`는 이미 끝난 사실을 알리는 이름이고, `CancelOrderCommand`는 이제 실행해 달라는 요청을 담은 이름이다.
> Primer Scope: `true-beginner-primer`

**난이도: 🟢 Beginner**

관련 문서:

- [옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지](./observer-vs-command-beginner-bridge.md)
- [커맨드 패턴 기초](./command-pattern-basics.md)
- [옵저버 패턴 기초](./observer-basics.md)
- [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: event vs command naming primer, OrderCompletedEvent CancelOrderCommand, event naming past fact, command naming future request, event vs command beginner naming, 이벤트 커맨드 네이밍, event command 이름 차이, 과거 사실 vs 미래 요청, event는 이미 일어난 일, command는 실행 요청, 주문 완료 이벤트 이름, 주문 취소 커맨드 이름, OrderCancelledEvent vs CancelOrderCommand, facts vs requests naming, happened vs do this naming, event suffix command suffix beginner, event command confusion naming

---

## 먼저 잡는 멘탈 모델

처음에는 클래스 이름보다 문장으로 읽는 편이 더 빠르다.

- `Event`: "이 일은 이미 일어났다."
- `Command`: "이 일을 이제 실행해 달라."

짧게 외우면 이것만 기억하면 된다.

**Event는 과거 사실, Command는 미래 요청이다.**

## 10초 질문

- 지금 이름이 "이미 끝난 사실"을 알리나?
- 아니면 "이제 수행할 작업"을 요청하나?
- 수신자가 이 메시지를 받고 이미 일어난 일에 반응하나, 아직 해야 할 일을 실행하나?

셋 중 앞쪽이면 `Event`, 뒤쪽이면 `Command` 쪽일 가능성이 크다.

## 30초 비교표: Event / Command

| 비교 질문 | Event | Command |
|---|---|---|
| 한 문장 | 이미 일어난 사실을 알린다 | 실행해 달라는 요청을 전달한다 |
| 시간 감각 | 과거 또는 완료된 현재 | 미래 또는 아직 미완료 |
| 자주 보이는 이름 | `OrderCompletedEvent`, `PaymentCapturedEvent` | `CancelOrderCommand`, `SendCouponCommand` |
| 수신자 기대 | "무슨 일이 있었지?"를 듣고 반응 | "무엇을 해야 하지?"를 받아 실행 |
| 자주 붙는 동사 느낌 | completed, created, paid, cancelled | create, cancel, send, approve |

이 표에서 가장 중요한 기준은 suffix보다 **문장 시제**다.
`Event`를 붙였어도 "취소해라"처럼 들리면 이름이 흔들리고, `Command`를 붙였어도 "이미 완료됐다"처럼 들리면 어색하다.

## Quick-Check

아래 3문항 중 2개 이상이 "예"면 이 문서를 먼저 읽으면 된다.

1. `OrderCompletedEvent`와 `CancelOrderCommand`처럼 이름은 비슷한데 무엇이 과거 사실이고 무엇이 실행 요청인지 바로 안 잡히는가?
2. 메시지 이름을 지을 때 `created`, `completed`, `cancelled` 같은 과거형과 `create`, `cancel`, `send` 같은 요청형이 왜 다른지 헷갈리는가?
3. 이벤트, 커맨드, 단순 DTO가 모두 "객체 하나 전달"처럼 보여서 네이밍 기준이 흐려지는가?

## Confusion Box

> 자주 헷갈리는 포인트
>
> - "`Event`를 붙였으니 다 이벤트 아닌가요?" -> 아니다. 이름이 "실행해라"처럼 들리면 사실보다 요청에 가깝다.
> - "`CancelOrderEvent`도 가능하지 않나요?" -> 가능은 하지만 "취소 요청"인지 "취소 완료 사실"인지 먼저 분리해야 한다. 완료 사실이면 `OrderCancelledEvent`처럼 읽히는 편이 더 선명하다.
> - "`Command`는 꼭 큐에 들어가야 하나요?" -> 아니다. 핵심은 비동기 여부보다 "실행 요청"이라는 의미다.
> - "`Event`면 무조건 비동기인가요?" -> 아니다. 동기 listener 호출이어도 이미 일어난 사실을 알리면 event naming이 맞다.

## 1분 예시: 주문 완료 vs 주문 취소

아래처럼 같은 주문 도메인에서도 이름의 질문이 다르다.

| 이름 | 읽는 문장 | 더 자연스러운 해석 |
|---|---|---|
| `OrderCompletedEvent` | "주문이 완료됐다" | 이미 끝난 사실 알림 |
| `CancelOrderCommand` | "주문을 취소해라" | 앞으로 실행할 요청 |
| `OrderCancelledEvent` | "주문이 취소됐다" | 취소가 끝난 뒤의 사실 알림 |
| `CancelOrderRequest` | "주문 취소 입력값" | 실행 책임 없는 요청 데이터일 수 있음 |

짧은 흐름으로 보면 더 쉽게 보인다.

```java
commandBus.dispatch(new CancelOrderCommand(orderId));

order.cancel();
eventPublisher.publish(new OrderCancelledEvent(orderId));
```

위 흐름에서 먼저 오는 것은 `CancelOrderCommand`다.
실행이 끝난 뒤에야 `OrderCancelledEvent`가 자연스럽다.

## 이름을 빨리 고르는 3단계

1. 이 메시지를 한 문장으로 읽는다.
2. "이미 일어난 일"인지 "이제 해야 할 일"인지 표시한다.
3. 완료 사실이면 `...Event`, 실행 요청이면 `...Command` 후보로 좁힌다.

예를 들면 이렇게 자른다.

- "결제가 완료됐다" -> `PaymentCompletedEvent`
- "결제를 승인해라" -> `ApprovePaymentCommand`
- "쿠폰이 발급됐다" -> `CouponIssuedEvent`
- "쿠폰을 발급해라" -> `IssueCouponCommand`

## 자주 틀리는 첫 네이밍

| 헷갈리는 이름 | 왜 흔들리는가 | 더 먼저 생각할 이름 |
|---|---|---|
| `CancelOrderEvent` | 취소 요청인지 취소 완료 사실인지 애매하다 | 요청이면 `CancelOrderCommand`, 완료면 `OrderCancelledEvent` |
| `OrderCompleteCommand` | 완료 사실처럼 들리는데 command suffix가 붙어 있다 | 요청이면 `CompleteOrderCommand`, 사실이면 `OrderCompletedEvent` |
| `PaymentCreatedCommand` | created는 이미 만들어진 느낌이다 | 요청이면 `CreatePaymentCommand` |
| `SendWelcomeCouponEvent` | send는 수행 요청처럼 들린다 | 요청이면 `SendWelcomeCouponCommand`, 완료 사실이면 `WelcomeCouponSentEvent` |

핵심은 영어 시제를 완벽히 외우는 것이 아니라, **읽자마자 사실인지 요청인지 드러나게 만드는 것**이다.

## 다음 읽기

- 패턴 큰 그림이 더 필요하면 [옵저버 vs 커맨드: 처음 선택을 줄이는 1페이지 브리지](./observer-vs-command-beginner-bridge.md)
- 실행 요청 구조를 더 보면 [커맨드 패턴 기초](./command-pattern-basics.md)
- 사실 알림 구조를 더 보면 [옵저버 패턴 기초](./observer-basics.md)
- event 안에서도 내부 사실과 외부 계약을 나누려면 [Domain Events vs Integration Events](./domain-events-vs-integration-events.md)

## 한 줄 정리

이름을 읽었을 때 "이미 일어났다"면 `Event`, "이제 실행해 달라"면 `Command`라고 먼저 자르면 초보자의 첫 네이밍 실수를 크게 줄일 수 있다.
