# 상속보다 조합 기초 (Composition over Inheritance Basics)

> 한 줄 요약: 처음 배우는 단계에서는 "코드 재사용이 보이면 일단 상속"보다, "이 객체가 정말 부모의 한 종류인가?"를 먼저 묻고 아니면 조합을 기본값으로 두는 편이 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)
- [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md)
- [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [전략 패턴 기초](./strategy-pattern-basics.md)
- [Composition over Inheritance — 심화](./composition-over-inheritance-practical.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: composition over inheritance, 상속보다 조합, 상속 vs 조합 언제 쓰는지, 상속은 언제 써요, 조합이 뭐예요, 처음 배우는데 부모 클래스 만들어야 하나요, 왜 조합을 선택하나요, has-a vs is-a, 코드 재사용만 필요하면, 템플릿 메소드냐 전략이냐, beginner composition over inheritance, what is composition over inheritance, 상속 헷갈려요, 조합 basics, inheritance vs composition beginner

---

## Quick Check

- 부모 구현 전체를 물려받으면 상속이다.
- 필요한 역할만 필드로 받아 쓰면 조합이다.
- 공통 순서를 부모가 고정해야 하면 템플릿 메소드 쪽이다.
- 규칙을 상황마다 바꿔 끼워야 하면 조합 + 전략 쪽이다.

처음 읽을 때는 "`extends`를 써도 되나?"보다 "`is-a`인가, `has-a`인가?"를 먼저 본다.

## 먼저 멘탈 모델

상속은 "자식이 부모의 한 종류다"라는 약속이다. 그래서 부모의 메서드, 기본 구현, 변경 영향까지 함께 받는다.

조합은 "이 객체가 다른 역할을 가진 객체를 데리고 쓴다"는 구조다. 필요한 협력만 가져오고, 구현은 나중에 다른 것으로 바꾸기 쉽다.

비유로 보면 이렇다.

- 상속: 부모 도구 상자를 통째로 물려받는다.
- 조합: 필요한 도구만 가방에 골라 담는다.

이 비유는 입문용이다. 실제 코드에서는 "도구를 골라 담는다"가 곧 의존성을 필드나 생성자로 받는다는 뜻이다.

## 30초 비교표

| 지금 보이는 상황 | 먼저 떠올릴 쪽 | 이유 |
|---|---|---|
| `OrderService`가 알림 기능을 쓰기만 한다 | 조합 | 주문 서비스는 알림 서비스의 한 종류가 아니다 |
| 부모가 `검증 -> 변환 -> 저장` 순서를 끝까지 고정해야 한다 | 상속 + 템플릿 메소드 | 공통 흐름을 부모가 쥔다 |
| 할인, 정렬, 결제 정책을 상황마다 바꿔야 한다 | 조합 + 전략 | 규칙을 객체로 갈아끼우는 문제다 |
| 단지 공통 헬퍼 메서드 몇 개 재사용하고 싶다 | 먼저 조합 의심 | 재사용만으로 `is-a`가 되지는 않는다 |

짧게 외우면 "고정 흐름은 상속 쪽, 교체 규칙은 조합 쪽"이다.

## 1분 예시

주문 완료 후 알림을 보내야 한다고 하자.

```java
// 상속: OrderService가 NotificationService의 구현까지 함께 물려받는다
public class OrderService extends NotificationService {
    public void completeOrder(Order order) {
        send(order);
    }
}

// 조합: OrderService는 알림 역할을 가진 객체를 받아서 쓴다
public class OrderService {
    private final NotificationSender notificationSender;

    public OrderService(NotificationSender notificationSender) {
        this.notificationSender = notificationSender;
    }

    public void completeOrder(Order order) {
        notificationSender.send(order);
    }
}
```

처음 배우는 사람에게는 아래 한 줄이 핵심이다.

- `OrderService is-a NotificationService`가 아니면 상속이 어색하다.
- `OrderService has-a NotificationSender`가 자연스러우면 조합이 맞다.

조합 쪽은 테스트에서 `FakeNotificationSender`로 바꾸기도 쉽다. 그래서 "역할 협력"이 중심인 코드에서는 조합이 기본값이 된다.

## 자주 헷갈리는 포인트

- "상속은 나쁜가요?"
  - 아니다. 진짜 `is-a` 관계이고 부모가 안정적이면 상속이 더 단순할 수 있다.
- "코드 재사용이면 상속이 더 빠르지 않나요?"
  - 처음엔 빨라 보여도 부모 변경 영향까지 같이 묶인다. 재사용만 필요하면 협력 객체로 빼는 편이 안전한 경우가 많다.
- "조합은 코드가 더 길어 보여요."
  - 맞다. 대신 교체, 테스트, 책임 분리가 쉬워진다. 길이가 아니라 변경 비용으로 판단한다.
- "그럼 상속은 언제 쓰나요?"
  - 부모가 공통 순서를 강하게 고정해야 할 때다. 이 경우는 [템플릿 메소드 패턴 기초](./template-method-basics.md)로 바로 이어서 보면 된다.

## 다음 학습 경로

지금 막히는 지점에 따라 다음 문서를 고르면 된다.

| 막히는 질문 | 바로 볼 문서 | 왜 이 문서로 가나 |
|---|---|---|
| `extends` 자체가 아직 낯설다 | [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) | 상속이 타입 관계라는 감각부터 다시 잡는다 |
| 인터페이스와 추상 클래스 차이도 함께 헷갈린다 | [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) | 부모 구현 상속과 계약 조합을 분리해 본다 |
| 부모가 흐름을 쥐는 예외가 궁금하다 | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 상속을 좁게 허용하는 대표 장면이다 |
| 바뀌는 규칙을 객체로 빼는 쪽이 궁금하다 | [전략 패턴 기초](./strategy-pattern-basics.md) | 조합이 패턴으로 드러나는 가장 흔한 모습이다 |
| 둘이 계속 섞여 보인다 | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) | 고정 흐름과 교체 규칙을 한 번에 비교한다 |

## 실무에서 쓰는 모습

실무에서는 "서비스가 여러 역할을 협력 객체로 가진다"는 형태가 더 자주 나온다. 주문 서비스가 알림, 포인트, 결제 정책을 각각 필드로 받아 쓰는 식이다.

반대로 상속은 프레임워크 확장 포인트나 안정된 템플릿 흐름처럼 "부모가 뼈대를 쥐는 구조"에서 더 자연스럽다. 그래서 beginner 입장에서는 "조합을 기본값으로 두고, 상속은 예외적으로 채택한다"는 감각이 안전한 출발점이다.

## 한 줄 정리

코드 재사용이 보인다고 바로 base class를 만들기보다, 진짜 `is-a` 관계인지 먼저 묻고 아니라면 조합으로 역할을 나누는 편이 초보자에게도 실무에도 더 안전한 기본값이다.
