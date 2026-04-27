# Command Handler Pattern: 검증을 어디에 두는가

> 한 줄 요약: Command Handler는 검증을 한곳에 몰아넣는 클래스가 아니라, request validator, policy object, aggregate invariant를 순서대로 연결하는 유스케이스 흐름이다.

**난이도: 🟢 Beginner**

관련 문서:
- [Layered Validation Pattern](./layered-validation-pattern.md)
- [Aggregate Invariant Guard Pattern](./aggregate-invariant-guard-pattern.md)
- [Policy Object Pattern](./policy-object-pattern.md)
- [Invariant-Preserving Command Model](./invariant-preserving-command-model.md)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)

retrieval-anchor-keywords: command handler validation flow, request validator in command handler, aggregate invariant in command handler, policy object in command handler, command handler validation placement, layered validation command handler, where to put validation in handler, command handler beginner, handler validation order, request validator aggregate invariant policy object, 처음 배우는데 command handler, command handler 뭐예요, command handler pattern basics, command handler pattern beginner, command handler pattern intro

---

## 처음 읽는다면 20초 멘탈 모델

Command Handler를 "검증을 다 하는 큰 서비스"로 보면 금방 헷갈린다.
더 쉬운 그림은 **세 문을 순서대로 지나가는 안내자**다.

| 문 | 맡는 질문 | 보통 두는 곳 |
|---|---|---|
| 입력 문 | 요청 모양이 맞는가 | request validator |
| 정책 문 | 지금 이 상황에서 허용되는가 | policy object |
| 도메인 문 | 이 상태 변화가 정말 가능한가 | aggregate 내부 invariant |

핵심은 "검증이 몇 개냐"가 아니라 **실패 의미가 다른 문을 섞지 않는 것**이다.

## 1페이지 배치 카드

| handler 흐름 | 여기 두는 것 | 이유 | 여기 두지 않는 것 |
|---|---|---|---|
| 1. command 받기 | request validator | 비어 있는 값, 형식, 범위 같은 입력 오류를 빨리 막는다 | 주문 상태 전이 규칙 |
| 2. aggregate 조회 | repository load | 정책 판단이나 상태 전이에 필요한 현재 상태를 가져온다 | dto 형식 검사 |
| 3. 실행 가능성 판단 | policy object | 회원 등급, 시간대, 한도처럼 외부 조건이 섞인 판정을 분리한다 | aggregate 내부 컬렉션 변경 |
| 4. 상태 변경 실행 | aggregate method + invariant guard | "이미 배송된 주문은 취소 불가" 같은 즉시 일관성을 aggregate가 직접 지킨다 | 외부 api 조회 로직 |
| 5. 저장/반환 | repository save, result mapping | 유스케이스를 마무리한다 | 새 비즈니스 규칙 추가 |

짧게 외우면 이 순서다.

`request validator -> policy object -> aggregate invariant`

## 1분 예시

```java
public record CancelOrderCommand(Long orderId, Long actorId, String reason) {}

public final class CancelOrderHandler {
    private final CancelOrderValidator validator;
    private final OrderRepository orderRepository;
    private final CancellationPolicy cancellationPolicy;

    public void handle(CancelOrderCommand command) {
        validator.validate(command);

        Order order = orderRepository.get(command.orderId());
        CancellationDecision decision =
            cancellationPolicy.evaluate(order, command.actorId());

        order.cancel(decision, command.reason());
        orderRepository.save(order);
    }
}
```

```java
public final class Order {
    public void cancel(CancellationDecision decision, String reason) {
        if (status == OrderStatus.SHIPPED) {
            throw new IllegalStateException("already shipped");
        }
        if (!decision.allowed()) {
            throw new PolicyViolationException(decision.reasonCode());
        }
        status = OrderStatus.CANCELLED;
        cancelReason = reason;
    }
}
```

여기서 역할은 이렇게 나뉜다.

- `validator`: `orderId`가 비었는지, `reason` 길이가 맞는지 본다.
- `cancellationPolicy`: 취소 가능 시간, 권한, 수수료 같은 운영 규칙을 계산한다.
- `order.cancel(...)`: 현재 주문 상태가 정말 취소 가능한지 마지막으로 지킨다.

## 자주 헷갈리는 포인트

- request validator가 있다고 aggregate invariant가 없어지는 것은 아니다. 입력이 정상이어도 현재 상태 전이는 실패할 수 있다.
- policy object가 있다고 handler가 비어야 하는 것은 아니다. handler는 여전히 순서를 조립한다.
- aggregate가 정책 객체 없이 모든 규칙을 다 알 필요는 없다. 외부 정보가 필요한 판정은 policy object 쪽이 더 자연스럽다.
- handler에서 `if`를 몇 줄 썼다는 이유만으로 나쁜 것은 아니다. **형식 검증, 정책 판정, 상태 전이 규칙이 한 덩어리로 섞일 때**가 더 위험하다.

## 한 줄 정리

Command Handler 안의 검증 배치는 "입력은 validator, 상황 판정은 policy, 상태 일관성은 aggregate"로 나누면 가장 덜 헷갈린다.
