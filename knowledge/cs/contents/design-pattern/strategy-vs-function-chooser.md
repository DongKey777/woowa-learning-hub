# Strategy vs Function: lambda로 충분한가, 전략 타입이 필요한가

> 한 줄 요약: 구현 차이가 짧고 stateless면 작은 함수나 `lambda`가 더 낫고, 이름 있는 규칙·협력 객체·테스트 경계가 커지면 Strategy 타입이 필요하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [전략 폭발 냄새](./strategy-explosion-smell.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [Composition over Inheritance](./composition-over-inheritance-practical.md)
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)

retrieval-anchor-keywords: strategy vs function, lambda vs strategy, function object vs strategy, strategy vs small function, when lambda is enough, when to use strategy type, beginner strategy chooser, java lambda or strategy pattern, stateless function vs strategy class, function map vs strategy object, lambda로 충분한가, 람다 vs 전략, 전략 vs 함수, 작은 함수 vs 전략, strategy 처음 배우는데 lambda

---

## 이 문서는 언제 읽으면 좋은가

아래 질문이 떠오르면 이 chooser를 먼저 보면 된다.

- "`if-else`를 줄이고 싶은데 클래스까지 만드는 건 과한가?"
- "`lambda`로 끝낼 수 있는지, 인터페이스와 구현 클래스를 만들어야 하는지 헷갈린다"
- 전략 패턴을 배웠는데 작은 계산식마다 클래스를 만들어야 할 것처럼 느껴진다
- "`Map<String, Function>` 정도면 충분한지, `Map<String, Strategy>`까지 올려야 하는지 판단이 안 선다"

핵심은 패턴 이름이 아니라 **변화의 크기와 협력의 무게**다.

---

## 30초 선택 가이드

먼저 아래 네 줄만 보면 대부분 정리된다.

- 구현 차이가 **1~3줄 계산식**이고 상태가 없으면 작은 함수가 먼저다.
- 같은 규칙이지만 **이름을 붙여 설명해야 할 정도로 의미가 크면** Strategy를 본다.
- 외부 서비스, 설정, 메트릭, fallback 같은 **협력 객체가 붙기 시작하면** Strategy 쪽이다.
- 호출 지점이 하나뿐이고 앞으로도 거의 안 바뀌면 함수나 단순 분기가 더 읽기 쉽다.

짧게 외우면 다음과 같다.

- **"짧은 계산식"**이면 함수
- **"이름 있는 규칙 묶음"**이면 Strategy

---

## function map 질문을 먼저 자르기

처음 배우는데 `Map`이 같이 나오면 질문이 두 종류로 섞이기 쉽다.

| 질문 모양 | 먼저 볼 문서 | 왜 그쪽이 맞는가 |
|---|---|---|
| `Map<String, Function>`이나 `Map<String, IntUnaryOperator>`로 충분한가 | 이 문서 | 값이 짧은 계산식인지, Strategy 타입까지 올려야 하는지 묻는 문제다 |
| `Map<String, DiscountStrategy>`가 너무 무거운가 | 이 문서 | 이름 있는 규칙 객체가 필요한지 판단하는 문제다 |
| Spring이 주입한 `Map<String, Handler>`가 registry인가 factory인가 | [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md) | 이미 있는 bean lookup인지, 새 객체 creation인지가 핵심이다 |
| `Map<Key, Creator>`를 찾은 뒤 `create()`까지 호출한다 | [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md) | function/strategy보다 registry/factory 경계가 핵심이다 |

짧게 자르면 다음 두 줄이다.

- **값이 짧은 규칙인가?** 그러면 함수 vs Strategy 질문이다.
- **이미 있는 후보를 찾는가, 새 객체를 만드는가?** 그러면 registry vs factory 질문이다.

---

## 한눈에 구분

| 질문 | 작은 함수 / `lambda` | Strategy 타입 |
|---|---|---|
| 구현 길이 | 짧고 바로 읽힌다 | 한 메서드 이상으로 의미가 커진다 |
| 상태 보관 | 거의 없다 | 설정, 캐시, 의존성, 보조 메서드를 가진다 |
| 협력 객체 | 없어도 된다 | 다른 객체와 협력이 자연스럽다 |
| 이름의 필요성 | "이 계산식" 정도면 충분하다 | "이 정책"이라고 불러야 이해된다 |
| 테스트 방식 | 입력-출력 표로 끝난다 | 구현체별 테스트 경계가 필요하다 |
| 확장 예상 | 2~3개 선택지에서 끝날 가능성이 높다 | 구현이 더 늘고 독립적으로 진화한다 |
| 대표 예시 | 배송비 계산식, 포맷 함수, 간단한 정렬 기준 | 결제 수단, 할인 정책, 재시도 정책, 라우팅 규칙 |

한 문장으로 다시 정리하면:

- 함수는 **동작 한 조각**
- Strategy는 **교체 가능한 역할**

---

## 왜 초보자가 여기서 자주 헷갈리는가

겉모양만 보면 함수도 "바꿔 끼우는 구현"이고 Strategy도 "바꿔 끼우는 구현"이다.
그래서 "`lambda`도 결국 전략 아닌가요?"라는 질문이 자주 나온다.

맞다. 작은 함수도 넓게 보면 전략처럼 쓸 수 있다.
하지만 설계 판단에서는 **표현 비용**을 같이 봐야 한다.

- 함수는 싸게 도입할 수 있다
- Strategy는 구조 비용이 있지만 의미와 경계를 더 또렷하게 만든다

즉 둘의 차이는 "객체지향이냐 아니냐"보다 **지금 문제 크기에 어떤 표현이 맞는가**다.

---

## 작은 함수로 끝내도 되는 경우

### 1. 구현 차이가 아주 짧다

배송 타입별 계산이 아래 정도면 함수 맵이 더 직관적이다.

```java
Map<String, IntUnaryOperator> feePolicies = Map.of(
    "STANDARD", distance -> 3000,
    "EXPRESS", distance -> 5000 + distance * 100
);
```

여기서 각 구현은 짧고, 읽는 사람이 클래스 이름보다 계산식을 직접 보는 편이 더 빠르다.

### 2. 상태가 없다

함수는 보통 입력만 받아 바로 결과를 낸다.

- 내부 캐시가 없다
- 외부 API 호출이 없다
- 생성자 주입할 의존성이 없다

이럴 때는 Strategy 타입을 만들면 구조만 무거워질 수 있다.

### 3. 테스트도 입력-출력 표면 충분하다

`grade -> discountRate` 같은 규칙은 테스트가 거의 표 형태다.
이 경우 구현체별 테스트 클래스를 나누는 것보다 케이스 테이블이 더 자연스럽다.

---

## Strategy 타입이 필요한 경우

### 1. 규칙에 이름이 필요하다

아래처럼 설명이 "10% 할인 함수"를 넘어서기 시작하면 Strategy가 읽기 쉬워진다.

- `WeekendPromotionDiscount`
- `PartnerCardInstallmentPolicy`
- `FastestHealthyEndpointRoutingStrategy`

즉 "무슨 계산을 하느냐"보다 **"무슨 역할을 맡았느냐"**가 중요해진다.

### 2. 협력 객체가 붙는다

아래 중 하나라도 붙으면 함수보다 Strategy 타입이 편해진다.

- 설정 객체
- 외부 클라이언트
- 메트릭/로깅
- fallback 규칙
- 보조 메서드

이 시점부터는 `lambda` 안에 로직을 우겨 넣기보다, 객체로 분리해서 책임을 드러내는 편이 낫다.

### 3. 구현이 독립적으로 진화한다

처음에는 할인 계산 한 줄이었는데 나중에 이런 요구가 붙을 수 있다.

- 테넌트별 다른 설정
- 특정 조건에서만 예외 처리
- 실패 시 다른 provider로 우회
- 구현체별 검증 규칙 차이

이런 변화는 "짧은 함수 여러 개"보다 **독립 배포 가능한 전략 역할**에 가깝다.

---

## 같은 예시를 두 단계로 보기

### 1. 처음에는 함수면 충분하다

```java
Map<String, IntUnaryOperator> discountPolicies = Map.of(
    "VIP", price -> (int) (price * 0.8),
    "GOLD", price -> (int) (price * 0.9)
);
```

이 단계에서는:

- 계산이 짧다
- 상태가 없다
- 협력 객체가 없다

그래서 함수가 더 싸고 읽기 쉽다.

### 2. 요구가 커지면 Strategy로 올라간다

```java
public interface DiscountStrategy {
    int discount(Order order);
}

public class VipDiscountStrategy implements DiscountStrategy {
    private final PromotionPolicy promotionPolicy;

    public VipDiscountStrategy(PromotionPolicy promotionPolicy) {
        this.promotionPolicy = promotionPolicy;
    }

    @Override
    public int discount(Order order) {
        int baseDiscount = (int) (order.price() * 0.8);
        return promotionPolicy.applyExtraDiscount(order, baseDiscount);
    }
}
```

이제는:

- 협력 객체가 있다
- 구현 이름이 의미를 가진다
- 구현체별 테스트 경계가 필요하다

그래서 Strategy 타입이 자연스럽다.

핵심은 "처음부터 Strategy여야 했다"가 아니다.
**작게 시작했다가, 책임이 커질 때 Strategy로 올리는 것**도 좋은 설계다.

---

## 실수하기 쉬운 기준

### 1. `if-else`를 없애려고 무조건 Strategy로 가는 것

분기를 지운다고 설계가 좋아지는 것은 아니다.
분기 2개와 짧은 계산식이면 작은 함수가 더 나을 수 있다.

### 2. `lambda` 안에 협력과 예외 처리를 계속 쌓는 것

처음에는 간단했는데 아래가 붙기 시작하면 신호다.

- 내부 `if`가 다시 많아진다
- 로깅과 메트릭이 섞인다
- 외부 의존성 호출이 들어간다
- 함수 이름보다 변수 캡처가 더 중요해진다

이때는 함수가 아니라 Strategy가 되어야 할 시점일 가능성이 높다.

### 3. Strategy를 "클래스 수 늘리기"로만 이해하는 것

Strategy의 가치는 클래스 개수가 아니라 **역할 이름과 교체 경계**를 분명히 하는 데 있다.
그래서 정말로 역할 경계가 없다면 굳이 만들지 않아도 된다.

---

## 빠른 결정 순서

1. 구현 차이가 상수나 짧은 계산식뿐인가? 그러면 함수부터 시작한다.
2. 외부 협력, 상태, 보조 메서드가 붙는가? 그러면 Strategy를 검토한다.
3. 구현 이름 자체가 도메인 설명이 되는가? 그러면 Strategy가 읽기 쉽다.
4. 선택지가 작고 지역적인가? 그러면 함수나 단순 분기를 유지한다.
5. 구현이 독립적으로 늘고 테스트 경계를 따로 가져가야 하는가? 그때 Strategy로 올린다.

---

## 꼬리질문

> Q: `lambda`도 전략처럼 주입해서 쓰면 그게 Strategy 아닌가요?
> 의도: 개념과 표현 비용을 함께 보는지 확인한다.
> 핵심: 넓게 보면 맞지만, 구현이 작고 stateless면 함수 표현이 더 싸다.

> Q: 처음부터 Strategy로 만드는 게 더 미래 대비 아닌가요?
> 의도: 과한 일반화를 경계하는지 확인한다.
> 핵심: 미래 가능성만으로 구조를 키우기보다, 책임이 커질 때 올리는 편이 낫다.

> Q: 함수에서 Strategy로 바꾸는 시점은 언제인가요?
> 의도: 구조 승격 기준을 설명할 수 있는지 확인한다.
> 핵심: 이름 있는 역할, 협력 객체, 독립 테스트 경계가 필요해질 때다.

## 한 줄 정리

구현 차이가 짧고 stateless면 함수가 더 낫고, 규칙이 이름과 협력과 책임을 갖기 시작하면 그때 Strategy 타입이 값을 한다.
