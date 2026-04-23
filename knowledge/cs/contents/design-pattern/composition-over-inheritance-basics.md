# 상속보다 조합 기초 (Composition over Inheritance Basics)

> 한 줄 요약: 상속은 부모의 구현까지 물려받아 변경 영향이 크고, 조합은 원하는 역할만 골라서 가져오므로 변경에 더 유연한 구조를 만들 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [Composition over Inheritance — 심화](./composition-over-inheritance-practical.md)
- [전략 패턴 기초](./strategy-pattern-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [소프트웨어 공학 카테고리 인덱스](../software-engineering/README.md)

retrieval-anchor-keywords: composition over inheritance, 상속보다 조합, favor composition, 상속 단점, 조합이 뭔가요, 상속 vs 조합, fragile base class, inheritance problem, has-a vs is-a, composition beginner, 조합으로 리팩터링, 처음 배우는데 상속 언제 써요, 왜 조합을 선택하나요, template method vs composition, template method vs strategy, 상속으로 뼈대 잡아야 하나, 부모 클래스 vs 전략 객체, 부모 클래스 상속 vs 객체 주입, extends vs composition, subclass vs delegate, favor composition over inheritance beginner

---

## 핵심 개념

상속(`extends`)은 부모 클래스의 모든 구현을 자식이 물려받는다. 직관적이고 코드를 줄일 수 있지만, 부모가 바뀌면 자식도 영향을 받는다는 문제("깨지기 쉬운 기반 클래스")가 있다.

조합은 여러 객체를 **필드로 가져다 쓰는** 방식이다. "내가 알림을 보낼 줄 안다"고 상속받는 게 아니라, "알림 서비스를 가지고 있어서 호출한다"는 구조다. 원하는 기능만 가져올 수 있고, 나중에 다른 구현으로 교체하기도 쉽다.

## 상속 질문을 빠르게 자르는 기준

초보자가 자주 묻는 "그럼 상속은 언제 써도 되나요?"에 대한 짧은 답은 이렇다.

- 부모 클래스가 **공통 순서를 강하게 고정**해야 한다: 템플릿 메소드 쪽
- 규칙이나 정책을 **객체로 갈아끼워야** 한다: 조합 + 전략 쪽
- 단지 코드 재사용이 목적이다: 먼저 조합 쪽을 의심한다

즉 상속은 금지가 아니라, **안정된 skeleton이 있을 때만 좁게 허용**되는 선택이다.  
이 경계를 바로 비교하고 싶으면 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md), 템플릿 메소드 자체를 기초부터 다시 보고 싶으면 [템플릿 메소드 패턴 기초](./template-method-basics.md)를 이어서 보면 된다.

## 한눈에 보기

| 비교 항목 | 상속 | 조합 |
|---------|------|------|
| 연결 방식 | `extends` — 구현 전체 상속 | 필드로 참조 — 원하는 것만 위임 |
| 교체 유연성 | 런타임 교체 어렵다 | 의존성 교체가 쉽다 |
| 결합도 | 부모와 강하게 결합 | 인터페이스에만 의존 가능 |
| 재사용 방식 | is-a ("~이다") | has-a ("~를 가진다") |

## 상세 분해

### 상속을 쓰는 경우

`Animal → Dog`처럼 진짜로 "is-a" 관계이고, 부모의 행동을 그대로 확장할 때 상속이 자연스럽다.

### 조합을 쓰는 경우

`OrderService`가 알림 기능이 필요할 때 `NotificationService`를 상속받는 것은 어색하다. "주문 서비스는 알림 서비스이다"가 아니라 "주문 서비스는 알림 서비스를 가진다"가 맞다.

```java
// 상속 (어색)
public class OrderService extends NotificationService { ... }

// 조합 (자연스럽다)
public class OrderService {
    private final NotificationService notificationService;
    public OrderService(NotificationService notificationService) {
        this.notificationService = notificationService;
    }
}
```

조합에서는 `NotificationService`를 인터페이스로 만들면 테스트에서 가짜 구현을 주입하기도 쉽다.

## 흔한 오해와 함정

- **"상속은 나쁘다"** — 상속이 항상 나쁜 게 아니다. 진짜 is-a 관계이고 부모를 거의 바꾸지 않는다면 상속이 더 단순하다.
- **"조합이 항상 더 많은 코드다"** — 초기에는 조합이 코드가 많아 보이지만, 요구사항이 변해도 영향 범위가 작아서 총 비용이 적은 경우가 많다.
- **"코드 재사용은 상속이 더 낫다"** — 상속으로 재사용하면 부모의 내부 구현에 의존하게 된다. 조합은 공개 인터페이스에만 의존하므로 더 안전하다.

## 실무에서 쓰는 모습

**기능 추가 요청**: 주문 완료 후 포인트 적립 기능이 생겼을 때, `OrderService`에 상속 대신 `PointService`를 필드로 추가하고 완료 시 호출한다. 나중에 포인트 정책이 바뀌어도 `PointService` 구현만 교체하면 된다.

**테스트 용이성**: 조합으로 된 의존성은 생성자 주입으로 가짜를 넣어 테스트할 수 있다. 상속받은 부모 메서드는 그러기 더 어렵다.

## 더 깊이 가려면

- [템플릿 메소드 패턴 기초](./template-method-basics.md) — 상속이 허용되는 대표 예외인 template skeleton을 beginner 기준으로 다시 정리
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) — "부모 클래스가 순서를 쥐어야 하나, 전략 객체를 주입해야 하나"를 바로 비교
- [Composition over Inheritance — 심화](./composition-over-inheritance-practical.md) — 변경 축 분석, 조합 리팩터링 사례, 상속이 여전히 맞는 경우
- [전략 패턴 기초](./strategy-pattern-basics.md) — 조합의 가장 대표적인 패턴, 행동을 필드로 가져다 교체하는 구조

## 면접/시니어 질문 미리보기

> Q: 상속 대신 조합을 쓰면 어떤 이점이 있는가?
> 의도: 두 방식의 트레이드오프를 설명하는지 확인한다.
> 핵심: 결합도를 낮추고 교체와 테스트가 쉬워진다.

> Q: "깨지기 쉬운 기반 클래스" 문제가 무엇인가?
> 의도: 상속의 구체적 위험을 아는지 확인한다.
> 핵심: 부모 구현이 바뀌면 자식 동작이 예기치 않게 바뀔 수 있는 현상이다.

> Q: 언제는 상속이 조합보다 더 나은가?
> 의도: 극단적 결론을 피하고 상황별 판단을 하는지 확인한다.
> 핵심: 진짜 is-a 계층이고 부모가 안정적이며 구현 재사용이 자연스러울 때다.

## 한 줄 정리

상속은 강하게 묶이고 조합은 느슨하게 연결되므로, 기능이 진짜 "is-a"가 아니라면 조합으로 가져다 쓰는 편이 변경에 더 유연하다.
