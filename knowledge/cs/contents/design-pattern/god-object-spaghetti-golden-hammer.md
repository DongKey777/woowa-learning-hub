# God Object / Spaghetti / Golden Hammer

> 한 줄 요약: 디자인 패턴을 몰라서 실패하는 것보다, 패턴을 과하게 믿어서 구조가 망가지는 경우가 더 흔하다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [안티 패턴](./anti-pattern.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)
> - [전략 패턴](./strategy-pattern.md)
> - [전략 폭발 냄새](./strategy-explosion-smell.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [Template Hook Smells](./template-hook-smells.md)

retrieval-anchor-keywords: god object, god class, god service, 거대 클래스, 비대한 서비스, manager object smell, blob anti pattern, spaghetti code smell, 스파게티 코드, golden hammer smell, 황금 망치, big ball of mud, pattern abuse, god object spaghetti golden hammer basics, god object spaghetti golden hammer beginner

---

## 핵심 개념

이 문서는 안티패턴을 세 가지 냄새로 묶는다.

- God Object: 한 객체가 너무 많은 책임을 가진 상태
- Spaghetti Code: 흐름이 뒤엉켜 추적하기 어려운 코드
- Golden Hammer: 하나의 해결책을 모든 문제에 두드리는 습관

셋은 서로 연결된다.
God Object는 보통 Spaghetti Code를 낳고, Golden Hammer는 그 상태를 더 악화시킨다.

## 냄새-first 분기

- 큰 서비스나 매니저 객체가 모든 흐름과 책임을 흡수한다면 이 문서를 먼저 본다.
- 분기를 없앤다고 전략 클래스를 케이스별로 늘리기 시작했다면 [전략 폭발 냄새](./strategy-explosion-smell.md)로 바로 이어간다.
- 공통 상위 클래스에 `beforeX`, `afterX`, `onError` 같은 훅이 계속 붙는다면 [Template Hook Smells](./template-hook-smells.md)로 이동한다.

---

## 깊이 들어가기

### 1. God Object가 생기는 이유

기능이 추가될 때마다 "여기에 조금만 더 넣자"가 반복되면 생긴다.

증상:

- 서비스 하나가 너무 많은 일을 한다
- 테스트가 어렵다
- 변경 이유가 여러 개다
- 작은 수정도 회귀를 일으킨다

### 2. Spaghetti Code의 본질

문제는 줄 수가 아니라 **제어 흐름**이다.
if-else, 중첩 반복, 전역 상태, 숨은 부수 효과가 얽히면 코드를 읽는 사람이 "이게 어디서 끝나는지"를 추적해야 한다.

### 3. Golden Hammer는 패턴 과사용의 출발점

한 번 성공한 패턴을 다른 문제에 그대로 들이밀면 안 된다.

- Strategy를 모든 분기에 쓰기
- Proxy를 모든 호출에 씌우기
- Builder를 단순 DTO 생성에까지 쓰기

패턴은 문제 해결 도구이지, 정답 템플릿이 아니다.

---

## 실전 시나리오

### 시나리오 1: 주문 서비스가 God Object가 된다

주문, 결제, 할인, 포인트, 알림, 통계가 한 서비스에 쌓인다.
처음에는 빠르지만 나중에는 수정 이유가 모든 기능과 섞여 버린다.

해결 기준:

- 변경 이유가 다른 책임은 분리한다
- 도메인 경계를 먼저 나눈다
- "서비스 하나에 다 넣자"는 습관을 의심한다

### 시나리오 2: 황금 망치로 전략만 계속 쓴다

작은 계산 로직에도 전략 클래스를 10개씩 만든다.
유연해 보이지만 실제론 읽기 비용만 높다.

### 시나리오 3: spaghetti를 단순 리팩토링으로만 못 푼다

코드 포맷팅만으로는 해결되지 않는다.
책임 분리, 데이터 흐름 재설계, 인터페이스 축소가 필요하다.

---

## 코드로 보기

### 1. God Object 예시

```java
public class OrderManager {
    public void placeOrder() {}
    public void pay() {}
    public void cancel() {}
    public void calculateDiscount() {}
    public void sendNotification() {}
    public void updateAnalytics() {}
}
```

이 객체는 "관리"라는 이름으로 너무 많은 책임을 흡수한다.

### 2. 분리 후

```java
public class OrderService { }
public class PaymentService { }
public class DiscountPolicy { }
public class NotificationPublisher { }
```

책임이 분리되면 테스트와 변경 이유가 줄어든다.

### 3. Golden Hammer 예시

```java
public class PricingContext {
    private final PricingStrategy strategy;
    public PricingContext(PricingStrategy strategy) {
        this.strategy = strategy;
    }
}
```

이 구조는 나쁘지 않지만, 단순 계산인데도 전략과 팩토리와 프록시를 함께 얹으면 과설계가 된다.

---

## 트레이드오프

| 냄새 | 장점처럼 보이는 것 | 실제 비용 | 치료 방향 |
|---|---|---|---|
| God Object | 진입점이 하나라 편해 보인다 | 변경 이유가 뒤섞인다 | 책임 분리 |
| Spaghetti Code | 빨리 고칠 수 있어 보인다 | 추적과 테스트가 어렵다 | 흐름 단순화 |
| Golden Hammer | 재사용성이 높아 보인다 | 과한 추상화가 늘어난다 | 문제에 맞는 도구 선택 |

핵심은 "객체 수"가 아니라 "변경 이유의 개수"다.
책임이 늘수록 코드가 강해지는 게 아니라, 먼저 망가지기 쉬워진다.

---

## 꼬리질문

> Q: God Object와 Service 하나가 커진 것을 어떻게 구분하나요?
> 의도: 단순 큰 클래스와 책임 붕괴를 구분하는지 확인
> 핵심: 변경 이유가 여러 개인지 본다

> Q: 패턴 과사용은 왜 실무에서 더 위험한가요?
> 의도: 코드 복잡도보다 팀 이해 비용을 보는지 확인
> 핵심: 이해 가능한 단순 코드가 더 오래 간다

## 한 줄 정리

God Object, Spaghetti Code, Golden Hammer는 모두 "문제를 푸는 방식"이 아니라 "복잡도를 숨기는 방식"이 될 때 생기는 실패 패턴이다.
