# 상속보다 조합 기초 (Composition over Inheritance Basics)

> 한 줄 요약: 처음 배우는 사람이 "상속 vs 조합을 언제 쓰는지" 큰 그림부터 잡도록, 상속은 부모의 구현까지 물려받아 변경 영향이 크고 조합은 원하는 역할만 골라서 가져오므로 더 유연하다는 기준을 기초 질문형으로 정리한 primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [자바 언어의 구조와 기본 문법](../language/java/java-language-basics.md)
- [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md)
- [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md)
- [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md)
- [Language README - Java primer](../language/README.md#java-primer)
- [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md)
- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [Composition over Inheritance — 심화](./composition-over-inheritance-practical.md)
- [전략 패턴 기초](./strategy-pattern-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [소프트웨어 공학 카테고리 인덱스](../software-engineering/README.md)

retrieval-anchor-keywords: composition over inheritance, 상속보다 조합, 상속은 언제 써요, 상속 언제 쓰는지, 상속 vs 조합 언제 쓰는지, 처음 배우는데 부모 클래스 만들어야 하나요, 부모 클래스냐 전략 객체냐, 공통 헬퍼 재사용만 필요하면, 조합이 뭔가요, 왜 조합을 선택하나요, has-a vs is-a, 고정 흐름이면 템플릿 메소드, 교체 규칙이면 전략, composition over inheritance basics basics, composition over inheritance basics beginner

---

## Quick check

- 부모 구현 전체를 물려받으면 상속
- 필요한 역할만 필드로 들고 쓰면 조합
- 흐름을 부모가 고정해야 하면 템플릿 메소드 쪽
- 규칙을 갈아끼워야 하면 조합 + 전략 쪽

처음 배우는데는 "`extends`를 쓸까?"보다 "**상속을 언제 쓰는지, 조합을 언제 쓰는지**"를 먼저 자르는 질문으로 시작한 뒤, "**부모가 흐름을 쥐나, 아니면 역할을 주입받나**"를 보면 된다.

처음 검색할 때는 아래 질문으로 들어오면 된다.

- 처음 배우는데 상속은 언제 써요?
- 부모 클래스를 만들어야 하나요, 아니면 객체로 넣어야 하나요?
- 코드 재사용하려면 상속이 맞나요?
- 상속 vs 조합은 큰 그림에서 어떻게 나눠요?

## 먼저 10초 기준

상속 질문이 나오면 아래 두 줄부터 본다.

- 공통 순서를 부모가 끝까지 고정해야 한다 -> 상속 / 템플릿 메소드 후보
- 규칙이나 기능을 상황에 따라 바꿔 끼워야 한다 -> 조합 / 전략 후보

즉 **고정 흐름이면 상속 쪽, 교체 규칙이면 조합 쪽**이 beginner 기준의 첫 판별이다.

## 30초 비교표: 부모 클래스냐 전략 객체냐

처음 배우는데 상속 질문이 나오면, 용어부터 파지 말고 이 질문부터 던진다.

| 먼저 고를 질문 | 예라고 답하면 | 다음 문서 |
|---|---|---|
| 부모가 `검증 -> 변환 -> 저장` 같은 **고정 순서**를 끝까지 쥐어야 하나? | 부모 클래스 + 템플릿 메소드 쪽 | [템플릿 메소드 패턴 기초](./template-method-basics.md) |
| 규칙(할인/결제/정렬)을 상황에 따라 **갈아끼워야** 하나? | 전략 객체를 주입하는 조합 쪽 | [전략 패턴 기초](./strategy-pattern-basics.md) |
| 둘 다 헷갈리나? | "흐름 고정 vs 규칙 교체"로 비교해서 자른다 | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) |

짧게 말해 **부모가 흐름을 쥐면 템플릿 메소드**, **호출자가 전략을 고르면 조합+전략**이다. 이 카드로 먼저 자르고 나면 상속 질문이 비교 문서로 자연스럽게 넘어간다.

## 길을 잃었을 때: Java 기초로 되돌아가기

이 문서가 갑자기 추상적이면, 더 앞으로 돌아가는 편이 빠르다. 조합을 보려면 **클래스/객체 -> 상속 -> 추상 클래스/인터페이스** 큰 그림이 먼저 잡혀 있어야 한다.

| 지금 막히는 지점 | 먼저 돌아갈 문서 | 왜 여기로 돌아가나 |
|---|---|---|
| `class`, `object`, `reference`가 아직 낯설다 | [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md) | 조합도 결국 "객체를 필드로 가진다"는 말이라서 객체 감각이 먼저다 |
| `extends`가 그냥 코드 재사용처럼 보인다 | [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) | 상속이 타입 관계라는 감각이 잡혀야 조합과 비교가 된다 |
| 추상 클래스와 인터페이스가 같은 말처럼 느껴진다 | [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) | 부모가 흐름을 쥐는 경우와 계약을 조합으로 주입하는 경우를 여기서 먼저 자른다 |
| 객체지향 큰 그림 자체가 흐리다 | [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) | 캡슐화, 상속, 다형성, 추상화를 한 장으로 다시 맞춘다 |
| Java 문법이 아직 불안하다 | [자바 언어의 구조와 기본 문법](../language/java/java-language-basics.md) | 클래스와 객체가 보이기 전에 문법/타입/실행 흐름부터 다시 잡는다 |

상속/추상클래스/조합 primer끼리 route를 맞춰 보면 기준선은 이렇다.
**[객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) -> 이 문서**

## 길을 잃었을 때: Java 기초로 되돌아가기 (계속 2)

문법이 아직 더 앞에서 막히면 그때만 아래처럼 한 단계 더 뒤로 돌아간다.
**[자바 언어의 구조와 기본 문법](../language/java/java-language-basics.md) -> [Java 타입, 클래스, 객체, OOP 입문](../language/java/java-types-class-object-oop-basics.md) -> [객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) -> 이 문서**

---

## 핵심 개념

상속(`extends`)은 부모 클래스의 모든 구현을 자식이 물려받는다. 직관적이고 코드를 줄일 수 있지만, 부모가 바뀌면 자식도 영향을 받는다는 문제("깨지기 쉬운 기반 클래스")가 있다.

조합은 여러 객체를 **필드로 가져다 쓰는** 방식이다. "내가 알림을 보낼 줄 안다"고 상속받는 게 아니라, "알림 서비스를 가지고 있어서 호출한다"는 구조다. 원하는 기능만 가져올 수 있고, 나중에 다른 구현으로 교체하기도 쉽다.

## 큰 그림: 조합 -> 템플릿 메소드 / 전략

처음 배우는데는 세 문서를 따로 외우기보다, 이 문서를 입구로 삼아 한 번에 자르는 편이 빠르다.

- 조합: 기본값이다. 기능을 객체로 들고 와서 쓴다.
- 템플릿 메소드: 상속을 써도 되는 **좁은 예외**다. 부모가 공통 순서를 끝까지 고정해야 할 때만 간다.
- 전략: 조합이 실전에서 가장 자주 패턴으로 드러난 모습이다. 바뀌는 규칙을 객체로 분리해 갈아끼울 때 간다.

| 먼저 드는 질문 | 어디로 가나 | 짧은 기준 |
|---|---|---|
| 코드 재사용 때문에 부모 클래스를 만들고 싶다 | 이 문서에서 한 번 멈춘다 | 기본값이 상속인지 말고, 조합으로 풀 수 있는지 먼저 본다 |
| `검증 -> 변환 -> 저장` 같은 순서를 부모가 지켜야 한다 | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 부모가 흐름을 쥔다 |
| 할인/결제/정렬처럼 규칙을 바꿔 끼워야 한다 | [전략 패턴 기초](./strategy-pattern-basics.md) | 호출자가 전략을 고른다 |
| 둘 다 섞여 보인다 | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) | 고정 흐름 vs 교체 규칙으로 자른다 |

## 상속 질문을 빠르게 자르는 기준

초보자가 자주 묻는 "그럼 상속은 언제 써도 되나요?"에 대한 짧은 답은 이렇다.

- 부모 클래스가 **공통 순서를 강하게 고정**해야 한다: 템플릿 메소드 쪽
- 규칙이나 정책을 **객체로 갈아끼워야** 한다: 조합 + 전략 쪽
- 단지 코드 재사용이 목적이다: 먼저 조합 쪽을 의심한다

즉 이 문서의 beginner route는 이렇다. **조합을 기본값으로 두고**, 안정된 skeleton이면 템플릿 메소드로, 교체 규칙이면 전략으로 간다.
템플릿 메소드는 조합 원칙의 반대편 대표 패턴이 아니라, **상속을 좁게 허용하는 예외**다. 전략은 조합을 실제 코드에서 가장 자주 보는 대표 패턴이다.
이 경계를 바로 비교하고 싶으면 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md), 템플릿 메소드 자체를 기초부터 다시 보고 싶으면 [템플릿 메소드 패턴 기초](./template-method-basics.md)를, 조합의 대표적인 쓰임을 바로 보고 싶으면 [전략 패턴 기초](./strategy-pattern-basics.md)를 이어서 보면 된다.

## 3문항 체크리스트: 공통 헬퍼 재사용만 필요하면?

부모 클래스를 만들기 전에 아래 3개만 먼저 묻는다. `예`가 많을수록 상속보다 조합 쪽이다.

| 질문 | `예`면 보통 | 왜 이렇게 보나 |
|---|---|---|
| 공통 헬퍼 메서드 몇 개만 재사용하면 끝나나? | 조합 또는 작은 유틸/협력 객체 | 헬퍼 재사용만으로는 `is-a` 관계가 생기지 않는다 |
| 나중에 구현을 테스트용 가짜나 다른 정책으로 바꿔 끼울 수 있나? | 조합 + 인터페이스 주입 | 교체 가능성이 보이면 부모 구현 상속보다 의존성 분리가 낫다 |
| 부모가 전체 순서를 끝까지 통제하지 않아도 되나? | 상속 대신 조합 | 흐름 고정이 약하면 base class를 둘 이유도 약하다 |

짧게 외우면 이렇다. **헬퍼 재사용**, **교체 가능성**, **흐름 고정 없음**이 보이면 먼저 조합을 본다.
반대로 부모가 공통 순서를 강하게 지켜야 할 때만 상속/템플릿 메소드 쪽으로 좁혀 간다.

## 한눈에 보기

| 비교 항목 | 상속 | 조합 |
|---------|------|------|
| 연결 방식 | `extends` — 구현 전체 상속 | 필드로 참조 — 원하는 것만 위임 |
| 교체 유연성 | 런타임 교체 어렵다 | 의존성 교체가 쉽다 |
| 결합도 | 부모와 강하게 결합 | 인터페이스에만 의존 가능 |
| 재사용 방식 | is-a ("~이다") | has-a ("~를 가진다") |

## 1분 예시: 주문 서비스에 알림 붙이기

처음 배우는 입장에서는 "상속하면 더 빨라 보이는데 왜 조합을 말하지?"가 가장 흔한 질문이다. 아래 예시 하나로 보면 차이가 바로 드러난다.

```java
// 상속: 주문 서비스가 알림 서비스의 구현까지 함께 물려받는다
public class OrderService extends NotificationService { ... }

// 조합: 주문 서비스는 알림 서비스를 필드로 받아 필요한 순간에만 호출한다
public class OrderService {
    private final NotificationService notificationService;

    public OrderService(NotificationService notificationService) {
        this.notificationService = notificationService;
    }
}
```

이 예시에서 핵심은 간단하다.

- 상속은 `OrderService`가 부모 구현 변경에 같이 묶인다
- 조합은 `NotificationService` 구현을 바꾸거나 테스트 대역으로 교체하기 쉽다

즉 주문 서비스가 "알림 서비스이다"가 아니라 "알림 서비스를 가진다"면 조합이 더 자연스럽다.

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

- related primer 기준 기본 next-read 순서는 **[객체지향 핵심 원리](../language/java/object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](../language/java/java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md) -> 이 문서**다. 조합 문서부터 검색에 걸렸더라도, 처음 배우는데 큰 그림을 다시 붙일 때는 이 순서로 거슬러 올라가면 된다.
- [템플릿 메소드 패턴 기초](./template-method-basics.md) — 부모가 흐름을 끝까지 쥐어야 할 때만 상속을 허용하는 좁은 예외를 다시 정리
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) — "부모 클래스가 순서를 쥐어야 하나, 전략 객체를 주입해야 하나"를 beginner 기준으로 바로 비교
- [Composition over Inheritance — 심화](./composition-over-inheritance-practical.md) — 변경 축 분석, 조합 리팩터링 사례, 상속이 여전히 맞는 경우
- [전략 패턴 기초](./strategy-pattern-basics.md) — 조합이 패턴으로 드러나는 가장 흔한 모습, 행동을 필드로 가져다 교체하는 구조

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

## 마지막 10초 Exit Card: 템플릿 메소드로 갈까, 전략으로 갈까

문서를 덮기 전에 아래 카드만 다시 보면 다음 읽기가 바로 정해진다.

> `검증 -> 변환 -> 저장`처럼 **공통 순서를 부모가 끝까지 고정**해야 하면
> -> [템플릿 메소드 패턴 기초](./template-method-basics.md)
>
> 할인/결제/정렬처럼 **규칙을 객체로 갈아끼워야** 하면
> -> [전략 패턴 기초](./strategy-pattern-basics.md)
>
> 둘 다 섞여 보이면
> -> [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)

| 마지막 확인 질문 | 바로 가는 문서 | 10초 기준 |
|---|---|---|
| 부모가 순서를 끝까지 쥐나? | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 흐름 고정 |
| 호출자가 규칙을 갈아끼우나? | [전략 패턴 기초](./strategy-pattern-basics.md) | 규칙 교체 |
| 아직 둘이 한 덩어리처럼 보이나? | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) | 비교로 다시 자르기 |

짧게 외우면 **"흐름 고정이면 템플릿 메소드, 규칙 교체면 전략"**이다.

## 한 줄 정리

공통 헬퍼 재사용만 필요하다면 base class부터 만들지 말고, 기능이 진짜 "is-a"인지 먼저 확인한 뒤 조합으로 역할을 나누는 편이 더 유연하다.
