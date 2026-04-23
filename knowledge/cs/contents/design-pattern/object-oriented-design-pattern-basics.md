# 객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버

> 한 줄 요약: 초보자가 가장 자주 헷갈리는 다섯 패턴을 "무엇이 바뀌는가" 기준으로 나눠서 빠르게 고르는 입문 가이드다.

**난이도: 🟢 Beginner**

관련 문서:

- [전략 패턴](./strategy-pattern.md)
- [템플릿 메소드 패턴](./template-method.md)
- [팩토리 (Factory)](./factory.md)
- [빌더 (Builder)](./builder-pattern.md)
- [옵저버 (Observer)](./observer.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [OOP 설계 원칙 기초](../software-engineering/oop-design-basics.md)

retrieval-anchor-keywords: object oriented design pattern basics, beginner design pattern guide, 디자인 패턴이 뭐예요, 패턴 처음 배우는데, when to use strategy, when to use factory, when to use observer, design pattern cheat sheet, 상속보다 조합, how to choose design pattern, why use design patterns, strategy vs template method

---

## 이 문서는 언제 읽으면 좋은가

아래처럼 패턴 이름은 들어봤는데 선택 기준이 흐릴 때 먼저 읽으면 된다.

- `if-else`가 커지는데 전략인지 팩토리인지 헷갈릴 때
- 상속을 써야 하는지, 객체를 주입해야 하는지 감이 안 올 때
- `new`가 많아서 생성 구조를 정리하고 싶은데 빌더와 팩토리를 구분 못 할 때
- "이벤트로 빼자"는 말이 나왔는데 옵저버인지 Pub/Sub인지 직접 호출인지 정리가 안 될 때

핵심 질문은 하나다.  
**무엇이 가장 자주 바뀌는가?**

---

## 먼저 세 가지 질문부터

### 1. 바뀌는 것이 알고리즘인가

- 같은 일을 하지만 방식이 여러 개라면 `전략`
- 공통 순서는 고정이고 단계 일부만 달라진다면 `템플릿 메소드`

### 2. 바뀌는 것이 객체 생성 방식인가

- 어떤 구현체를 만들지 숨기고 싶다면 `팩토리`
- 한 객체를 여러 단계로 읽기 좋게 조립하고 싶다면 `빌더`

### 3. 바뀌는 것이 반응 주체의 개수인가

- 상태 변화가 여러 후속 동작으로 퍼져야 한다면 `옵저버`

이렇게 보면 다섯 패턴은 "유명한 이름 모음"이 아니라 서로 다른 문제 축을 다루는 도구다.

---

## 이 다섯 개 다음에 자주 이어지는 질문

이 문서는 다섯 패턴만 다루지만, 초보자가 바로 다음 단계에서 자주 부딪히는 갈림길은 따로 있다.

- 외부 SDK나 레거시 인터페이스를 우리 코드 형태로 맞춰야 하면 [Adapter (어댑터)](./adapter.md)로 내려간다.
- "상속을 유지할까, 객체를 주입해 조합할까"가 계속 남으면 [Composition over Inheritance](./composition-over-inheritance-practical.md)와 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)을 같이 본다.
- 실행 요청을 나중에 처리하거나 undo/redo 대상으로 남겨야 하면 [Command Pattern Undo Queue](./command-pattern-undo-queue.md)로 이어진다.

---

## 다섯 패턴 한눈에 보기

| 패턴 | 핵심 질문 | 구조 중심 | 잘 맞는 상황 | 피해야 할 상황 |
|---|---|---|---|---|
| 전략 | "같은 목적의 규칙이 여러 개인가?" | 인터페이스 + 교체 가능한 구현 | 할인 정책, 결제 수단, 정렬 기준 | 분기가 거의 안 바뀌는 작은 로직 |
| 템플릿 메소드 | "순서는 고정이고 단계만 다른가?" | 상위 클래스 뼈대 + 하위 클래스 단계 구현 | 배치 파이프라인, 파서, 공통 처리 순서 | 런타임 교체가 중요하거나 상속 계층이 깊어질 때 |
| 팩토리 | "생성 책임을 숨겨야 하는가?" | 생성 전용 메서드/객체 | 환경별 구현 선택, 외부 SDK 클라이언트 생성 | `new` 한 줄이면 끝나는 단순 생성 |
| 빌더 | "한 객체를 단계적으로 읽기 좋게 만들고 싶은가?" | builder + `build()` | 옵션 많은 DTO, 불변 객체, 테스트 픽스처 | 필드가 적고 필수값만 있는 단순 객체 |
| 옵저버 | "상태 변화에 여러 객체가 반응해야 하는가?" | subject + listener/observer | 알림, 후속 부가 작업, 내부 이벤트 | 핵심 성공 경로를 반드시 함께 처리해야 하는 경우 |

---

## 전략 패턴

### 무엇을 해결하나

같은 목적의 알고리즘이 여러 개인데, 어떤 구현을 쓸지 실행 시점에 바꿔야 할 때 쓴다.

- VIP 할인과 일반 할인
- 카드 결제와 간편결제
- 길이순 정렬과 사전순 정렬

핵심은 `if-else`를 없애는 게 아니라 **변화하는 규칙을 따로 빼는 것**이다.

### 머릿속 그림

- `Context`: 전략을 사용하는 쪽
- `Strategy`: 공통 인터페이스
- `ConcreteStrategy`: 실제 규칙 구현

```java
public interface DiscountPolicy {
    int discount(int price);
}

public class VipDiscountPolicy implements DiscountPolicy {
    @Override
    public int discount(int price) {
        return (int) (price * 0.8);
    }
}

public class OrderService {
    private final DiscountPolicy discountPolicy;

    public OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = discountPolicy;
    }
}
```

### 언제 쓰나

- 같은 역할의 구현이 2개 이상이고 계속 늘어날 수 있을 때
- 정책별 테스트를 따로 쓰고 싶을 때
- 런타임에 구현을 바꿔 끼워야 할 때

### 언제 과한가

- 분기가 1~2개뿐이고 앞으로도 잘 안 바뀔 때
- 함수 하나로 충분한 작은 계산식일 때
- 공통 순서를 강하게 보장해야 할 때

한 문장 규칙:  
**"규칙을 갈아끼우는 문제"면 전략을 먼저 본다.**

---

## 템플릿 메소드 패턴

### 무엇을 해결하나

알고리즘의 전체 순서는 고정하고, 일부 단계만 바꾸고 싶을 때 쓴다.

- 파일을 읽고, 변환하고, 저장하는 흐름
- 공통 인증 절차 뒤에 채널별 후처리가 붙는 흐름
- 공통 배치 처리 뼈대 안에서 입력/출력만 바뀌는 경우

핵심은 **"순서를 지키게 만드는 것"**이다.

### 머릿속 그림

- 상위 클래스가 전체 흐름을 가진다
- 하위 클래스가 일부 단계를 구현한다
- 필요하면 hook 메서드로 선택적 확장을 둔다

```java
public abstract class ReportExporter {
    public final void export() {
        load();
        transform();
        save();
    }

    protected abstract void load();
    protected abstract void transform();
    protected abstract void save();
}
```

### 언제 쓰나

- 순서를 실수로 바꾸면 안 되는 공통 흐름이 있을 때
- 단계 이름과 책임이 안정적일 때
- 여러 구현이 같은 뼈대를 공유할 때

### 언제 과한가

- 구현을 런타임에 바꿔야 할 때
- 상속 계층이 계속 늘어날 때
- 단계마다 필요한 협력 객체가 달라 조합이 더 자연스러울 때

한 문장 규칙:  
**"순서는 고정, 단계만 다름"이면 템플릿 메소드가 맞다.**

---

## 팩토리 패턴

### 무엇을 해결하나

객체를 만드는 책임을 호출부에서 떼어내고 싶을 때 쓴다.

- 운영 환경에 따라 `S3Client`와 `LocalStorageClient` 중 하나를 만든다
- 외부 SDK 생성 규칙이 복잡하다
- 테스트에서는 가짜 구현을 쉽게 바꿔 끼우고 싶다

핵심은 **"어떻게 만들지"를 숨기는 것**이다.

### 머릿속 그림

- 호출부는 구체 클래스 대신 factory에 요청한다
- factory는 입력/설정에 따라 알맞은 구현을 만든다

```java
public class PaymentClientFactory {
    public PaymentClient create(String provider) {
        return switch (provider) {
            case "kakao" -> new KakaoPaymentClient();
            case "tosspay" -> new TossPaymentClient();
            default -> throw new IllegalArgumentException("unknown provider");
        };
    }
}
```

### 언제 쓰나

- 생성 규칙이 여러 군데로 흩어지는 걸 막고 싶을 때
- 환경, 설정, 외부 조건에 따라 구현을 선택할 때
- 생성 과정에서 검증, 초기화, 외부 의존성 연결이 필요할 때

### 언제 과한가

- `new` 한 번이면 끝나는 단순 생성일 때
- 팩토리 안에 비즈니스 규칙이 계속 들어와 비대해질 때
- 사실상 "찾아오기"가 핵심이라 registry가 더 자연스러울 때

한 문장 규칙:  
**"만드는 책임을 호출부에서 숨기고 싶다"면 팩토리를 본다.**

---

## 빌더 패턴

### 무엇을 해결하나

필드가 많거나 선택값이 많아서 한 객체를 단계적으로 읽기 좋게 만들고 싶을 때 쓴다.

- 요청 DTO
- 테스트 픽스처
- 불변 설정 객체

핵심은 **"무엇을 넣는지 드러내면서 조립하는 것"**이다.

### 머릿속 그림

- builder에 값을 하나씩 넣는다
- 마지막에 `build()`로 완성 객체를 만든다

```java
OrderRequest request = OrderRequest.builder()
    .userId("u1")
    .itemId("i9")
    .quantity(2)
    .giftWrap(true)
    .memo("leave at door")
    .build();
```

### 언제 쓰나

- 필수값과 선택값이 섞여 있을 때
- 생성자 파라미터 순서를 자꾸 헷갈릴 때
- 불변 객체를 읽기 좋게 만들고 싶을 때

### 언제 과한가

- 필드가 2~3개뿐인 단순 객체일 때
- 항상 같은 세팅으로만 만들어지는 객체일 때
- `setter` 체이닝처럼 보이지만 실제로는 mutable 객체를 마구 수정하는 API일 때

한 문장 규칙:  
**"한 객체를 읽기 좋게 조립"하는 문제가 핵심이면 빌더다.**

---

## 옵저버 패턴

### 무엇을 해결하나

한 객체의 상태 변화에 여러 객체가 반응해야 하는데, 그 반응 주체들을 느슨하게 연결하고 싶을 때 쓴다.

- 주문 완료 후 알림 발송
- 캐시 무효화
- 로그/메트릭 수집

핵심은 **"변화 통지"를 분리하는 것**이다.

### 머릿속 그림

- `Subject`가 observer 목록을 가진다
- 상태 변화가 생기면 등록된 observer에게 알린다

```java
public interface OrderListener {
    void onCompleted(Long orderId);
}

public class OrderService {
    private final List<OrderListener> listeners;

    public void complete(Long orderId) {
        // 주문 완료
        for (OrderListener listener : listeners) {
            listener.onCompleted(orderId);
        }
    }
}
```

### 언제 쓰나

- 한 이벤트에서 여러 부가 작업이 파생될 때
- 발신자가 후속 처리 구현을 직접 몰라도 되게 하고 싶을 때
- 리스너를 쉽게 추가/제거하고 싶을 때

### 언제 과한가

- 핵심 정합성을 위해 반드시 같은 트랜잭션 안에서 처리해야 할 때
- 누가 무엇을 듣고 있는지 추적하기 너무 어려워질 때
- 브로커 기반 비동기 분산 전파가 필요한데 단순 옵저버로 뭉뚱그릴 때

한 문장 규칙:  
**"상태 변화에 여러 반응이 붙는다"면 옵저버를, "핵심 흐름"이면 직접 호출을 먼저 본다.**

---

## 가장 많이 헷갈리는 비교

### 전략 vs 템플릿 메소드

- 전략: 알고리즘 전체를 바꾼다
- 템플릿 메소드: 알고리즘 순서는 고정하고 일부 단계만 바꾼다

빠른 판별:

- 런타임 교체가 중요하면 `전략`
- 순서 보장이 중요하면 `템플릿 메소드`

### 팩토리 vs 빌더

- 팩토리: 무엇을 만들지 결정하는 문제
- 빌더: 하나의 객체를 어떻게 채울지 보여주는 문제

빠른 판별:

- 구현 선택이 핵심이면 `팩토리`
- 옵션 조립이 핵심이면 `빌더`

### 옵저버 vs 직접 호출

- 옵저버: 부가 작업 분리
- 직접 호출: 핵심 흐름 보장

빠른 판별:

- 실패하면 본 흐름도 같이 실패해야 하면 `직접 호출`
- 느슨하게 붙는 후속 반응이면 `옵저버`

---

## 초보자용 읽기 순서

1. 이 문서로 다섯 패턴의 문제 축을 먼저 잡는다.
2. [전략 패턴](./strategy-pattern.md)과 [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)로 행동 패턴 차이를 익힌다.
3. [팩토리 (Factory)](./factory.md), [빌더 (Builder)](./builder-pattern.md), [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)로 생성 축을 본다.
4. [옵저버 (Observer)](./observer.md)와 [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)로 통지 구조를 본다.
5. 마지막에 [실전 패턴 선택 가이드](./pattern-selection.md)로 넓은 비교표를 다시 읽는다.
6. 그다음 자주 갈라지는 세 갈래는 [Composition over Inheritance](./composition-over-inheritance-practical.md), [Adapter (어댑터)](./adapter.md), [Command Pattern Undo Queue](./command-pattern-undo-queue.md)다.

---

## 한 줄 정리

전략은 규칙 교체, 템플릿 메소드는 순서 고정, 팩토리는 생성 책임 분리, 빌더는 단계적 조립, 옵저버는 상태 변화 통지에 쓰는 패턴이다.
