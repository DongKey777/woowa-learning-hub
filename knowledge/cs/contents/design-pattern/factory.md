---
schema_version: 3
title: 팩토리 디자인 패턴
concept_id: design-pattern/factory-deep-dive
canonical: false
category: design-pattern
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- factory-creation-responsibility
- factory-vs-static-factory-builder-registry
- factory-overuse-smell
aliases:
- factory pattern deep dive
- 팩토리 디자인 패턴
- Factory pattern
- object creation boundary
- factory vs constructor
- factory vs static factory method
- factory vs builder
- switch factory smell
symptoms:
- new를 보면 무조건 Factory로 감싸야 한다고 생각하고 있어
- 정적 팩토리 메서드와 Factory 패턴, Builder, Registry를 같은 생성 패턴으로 뭉뚱그리고 있어
- 생성 책임보다 선택/정책 판단이 핵심인 코드를 Factory라는 이름에 몰아넣고 있어
intents:
- definition
- comparison
- design
prerequisites:
- design-pattern/factory
- software-engineering/oop-design-basics
next_docs:
- design-pattern/constructor-vs-static-factory-vs-factory-pattern
- design-pattern/factory-misnaming-checklist
- design-pattern/factory-vs-abstract-factory-vs-builder
- design-pattern/bridge-strategy-vs-factory-runtime-selection
linked_paths:
- contents/design-pattern/factory-basics.md
- contents/design-pattern/strategy-pattern.md
- contents/design-pattern/constructor-vs-static-factory-vs-factory-pattern.md
- contents/design-pattern/factory-misnaming-checklist.md
- contents/design-pattern/bridge-strategy-vs-factory-runtime-selection.md
- contents/design-pattern/factory-vs-abstract-factory-vs-builder.md
- contents/design-pattern/builder-pattern.md
- contents/design-pattern/registry-pattern.md
- contents/design-pattern/policy-object-pattern.md
confusable_with:
- design-pattern/factory
- design-pattern/constructor-vs-static-factory-vs-factory-pattern
- design-pattern/factory-vs-abstract-factory-vs-builder
- design-pattern/bridge-strategy-vs-factory-runtime-selection
forbidden_neighbors: []
expected_queries:
- Factory 패턴은 단순히 new를 없애는 게 아니라 어떤 생성 책임을 숨기는 거야?
- 정적 팩토리 메서드와 Factory 패턴은 역할이 어떻게 달라?
- Builder, Registry, DI container가 Factory보다 더 맞는 상황은 언제야?
- switch 기반 Factory가 커질 때 Strategy나 Registry로 나눠야 하는 신호는 뭐야?
- 단순 DTO 생성까지 Factory로 감싸면 왜 구조만 늘어날 수 있어?
contextual_chunk_prefix: |
  이 문서는 Factory pattern follow-up bridge로, creation responsibility, constructor vs static factory method, Factory vs Builder/Registry/DI container, switch factory smell, creation vs selection responsibility를 설명한다.
  팩토리 패턴, new 대신 factory, static factory method 차이, Builder와 Factory, Factory 과용 같은 자연어 질문이 본 문서에 매핑된다.
---
# 팩토리 (Factory) 디자인 패턴

> 작성자 : [서그림](https://github.com/Seogeurim)

> 한 줄 요약: Factory는 객체를 어디서 어떻게 만들지 호출부에서 숨겨, 생성 규칙과 구현 선택을 한 곳에 모으는 패턴이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)
- [전략 패턴이란 무엇인가: 런타임에 구현을 바꾸는 방법](./strategy-pattern.md)
- [생성자 vs 정적 팩토리 메서드 vs Factory 패턴](./constructor-vs-static-factory-vs-factory-pattern.md)
- [Factory Misnaming Checklist: create 없는 `*Factory`를 리뷰에서 빨리 가르기](./factory-misnaming-checklist.md)
- [런타임 선택에서 Bridge vs Strategy vs Factory: 행동 축과 생성 축을 헷갈리지 않기](./bridge-strategy-vs-factory-runtime-selection.md)
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- [빌더 패턴](./builder-pattern.md)

retrieval-anchor-keywords: factory pattern, object creation boundary, runtime implementation selection, factory overuse, when not to use factory, factory vs constructor, factory vs static factory method, factory vs builder, factory vs registry, switch factory smell, beginner factory pattern, constructor vs static factory vs factory pattern, java static factory naming, of from valueof parse getinstance newinstance, factory basics

---

## 핵심 개념

팩토리 패턴의 핵심은 `new`를 없애는 것이 아니라 **생성 책임을 호출부에서 분리**하는 데 있다.

- 호출부는 "무엇을 쓸지"만 안다
- 팩토리는 "어떻게 만들지"를 안다
- 생성 규칙이 바뀌어도 사용 코드는 덜 흔들린다

이 패턴이 특히 유용한 순간은 다음과 같다.

- 환경, 설정, provider에 따라 구현을 바꿔야 할 때
- 생성 과정에 검증, 초기화, 외부 의존성 연결이 섞일 때
- 생성 규칙이 여러 곳에 흩어지면 변경이 퍼질 때

반대로 이런 경우에는 팩토리가 과하다.

- 객체 하나를 `new` 한 번으로 만들면 끝날 때
- 같은 타입의 이름 있는 생성만 필요할 때
- 사실상 "찾기"가 핵심이라 Registry가 더 자연스러울 때
- 옵션이 많은 한 객체를 읽기 좋게 조립해야 해서 Builder가 맞을 때

한 문장 규칙:
**"생성 규칙이 바뀌는가?"가 핵심이면 Factory를 보고, 아니면 더 단순한 대안을 먼저 본다.**

---

## 이 문서는 언제 읽으면 좋은가

아래처럼 생성 패턴이 헷갈릴 때 읽으면 된다.

- `new`가 퍼져 있는데 정말 팩토리가 필요한지 확신이 없을 때
- 정적 팩토리 메서드와 패턴으로서의 Factory를 같은 것으로 느낄 때
- switch 기반 생성기가 계속 커져서 Registry나 Strategy로 갈라야 하는지 고민될 때
- Builder, DI 컨테이너, Factory 중 어디에 생성 책임을 둬야 할지 애매할 때

반대로 질문이 "런타임에 고른다고 다 factory인가?" 쪽이면 [Bridge vs Strategy vs Factory](./bridge-strategy-vs-factory-runtime-selection.md)로 먼저 가는 편이 빠르고, "`PaymentPolicyFactory`처럼 이름이 과한가?"가 핵심이면 [Factory Misnaming Checklist](./factory-misnaming-checklist.md)에서 바로 자르는 편이 낫다.

---

## 깊이 들어가기

### 1. Factory는 "모든 생성"이 아니라 "바뀌는 생성"을 숨긴다

초보자가 가장 많이 하는 오해는 `new`가 보이면 전부 Factory로 감싸야 한다고 생각하는 것이다.
하지만 아래 코드는 굳이 팩토리가 필요 없다.

```java
Money money = new Money("KRW", 1000);
```

값 객체가 단순하고 생성 규칙이 안정적이면 직접 생성이 가장 읽기 쉽다.
Factory는 "그냥 생성"이 아니라 **생성 규칙이 퍼지면 아픈 곳**에 둬야 한다.

### 2. Factory보다 단순한 대안이 먼저일 때가 많다

| 선택지 | 더 잘 맞는 상황 | Factory보다 단순한 이유 |
|---|---|---|
| 직접 `new` / 생성자 | 필드가 적고 규칙이 단순할 때 | 호출부에서 바로 의도가 보인다 |
| 정적 팩토리 메서드 | 같은 타입의 이름 있는 생성만 필요할 때 | 클래스 하나를 더 만들지 않아도 된다 |
| Builder | 한 객체의 옵션이 많고 조립 과정을 드러내야 할 때 | "무엇을 만들지"보다 "어떻게 채울지"가 중요하다 |
| Registry | 이미 만들어진 구현을 키로 찾아 쓸 때 | 생성보다 lookup이 핵심이다 |
| DI 컨테이너 | 애플리케이션 wiring이 핵심일 때 | 수동 팩토리보다 조립 책임이 선명하다 |

핵심은 "Factory가 더 멋져 보이는가"가 아니라
**지금 문제를 가장 적은 구조로 풀 수 있는가**다.

### 3. 정적 팩토리 메서드와 Factory 패턴은 같은 말이 아니다

둘 다 이름에 factory가 들어가서 자주 헷갈린다.

| 구분 | 초점 | 예시 |
|---|---|---|
| 정적 팩토리 메서드 | 같은 타입을 더 읽기 좋게 만든다 | `Money.zero()`, `User.from(profile)` |
| Factory 패턴 | 어떤 구현을 만들지 선택 책임을 숨긴다 | `StorageClientFactory.create(provider)` |

즉 정적 팩토리는 **구현 방식**이고, Factory 패턴은 **역할과 책임**에 가깝다.

### 4. Factory가 비대해지면 다른 패턴 문제로 바뀐다

처음에는 작은 switch 하나였는데 아래 신호가 보이기 시작하면 이미 단순한 Factory가 아니다.

- `switch` / `if-else` case가 계속 늘어난다
- 문자열 키가 여러 군데로 퍼진다
- 생성 규칙 안에 비즈니스 정책 판단이 들어온다
- 객체를 만드는 것보다 "어떤 걸 고를지"가 더 복잡해진다
- 모든 의존성을 꺼내주는 service locator처럼 변한다

이때 보통 더 자연스러운 대안은 다음과 같다.

- 선택이 핵심이면 [Registry Pattern](./registry-pattern.md)
- 행동 교체가 핵심이면 [전략 패턴](./strategy-pattern.md)
- 애플리케이션 조립이 핵심이면 DI 컨테이너

## 깊이 들어가기 (계속 2)

즉 switch를 없애는 게 목적이 아니라
**생성, 선택, 행동의 책임을 다시 분리하는 것**이 목적이다.

---

## 실전 시나리오

### 시나리오 1: 잘 맞는 경우, 외부 provider 클라이언트 생성

운영 환경이나 설정에 따라 `S3`, `GCS`, `LocalStorage` 구현을 골라야 한다면 팩토리가 잘 맞는다.

- 호출부는 `StorageClient`만 안다
- 생성 시 인증 정보, region, timeout 초기화가 함께 묶인다
- provider 변경 시 호출부를 직접 고치지 않아도 된다

### 시나리오 2: 애매한 경우, 테스트 픽스처

테스트 데이터 생성 helper를 팩토리라고 부르기도 하지만, 실제 문제는 "복잡한 한 객체를 읽기 좋게 조립"하는 일일 수 있다.
이 경우는 [빌더 패턴](./builder-pattern.md)이나 fixture helper가 더 맞을 수 있다.

즉 이름이 Factory여도 패턴으로서의 Factory라고 단정하면 안 된다.

### 시나리오 3: 쓰지 않는 편이 나은 경우, 단순 DTO 생성

```java
UserSummary summary = new UserSummary(name, level);
```

이 정도를 아래처럼 감싸면 대개 이득보다 구조만 늘어난다.

```java
UserSummary summary = UserSummaryFactory.create(name, level);
```

생성 규칙이 없는 단순 DTO라면, 팩토리는 호출부를 더 읽기 쉽게 만들지 못한다.

### 시나리오 4: Factory가 틀린 문제인 경우, 결제 정책 판단

카드, 포인트, 쿠폰 조합에 따라 "어떤 정책을 적용할지"가 핵심이면 그건 생성 문제가 아니다.
이 경우 `PaymentPolicyFactory` 같은 이름으로 정책 판단을 몰아넣기보다 [전략 패턴](./strategy-pattern.md)이나 [Policy Object Pattern](./policy-object-pattern.md)이 더 자연스럽다.

---

## 코드로 보기

### 1. 단순한 생성은 직접 `new`가 더 낫다

```java
OrderLine line = new OrderLine(productId, quantity);
```

필드 수가 적고 규칙이 단순하면 이게 가장 명확하다.

### 2. 이름 있는 생성이면 정적 팩토리 메서드로 충분할 수 있다

```java
public final class Money {
    private final String currency;
    private final long amount;

    private Money(String currency, long amount) {
        this.currency = currency;
        this.amount = amount;
    }

    public static Money zero(String currency) {
        return new Money(currency, 0);
    }

    public static Money of(String currency, long amount) {
        return new Money(currency, amount);
    }
}
```

여기서는 구현 선택보다 **생성 의도를 이름으로 드러내는 것**이 중요하다.

### 3. 구현 선택이 생기면 Factory가 자연스러워진다

```java
public class StorageClientFactory {
    public StorageClient create(String provider) {
        return switch (provider) {
            case "S3" -> new S3StorageClient();
            case "GCS" -> new GcsStorageClient();
            case "LOCAL" -> new LocalStorageClient();
            default -> throw new IllegalArgumentException("unknown provider: " + provider);
        };
    }
}
```

호출부는 이렇게 단순해진다.

```java
StorageClient client = storageClientFactory.create(provider);
client.upload(file);
```

### 4. switch가 계속 커지면 Registry-backed factory를 본다

## 코드로 보기 (계속 2)

```java
public class StorageClientFactory {
    private final Map<String, Supplier<StorageClient>> suppliers;

    public StorageClientFactory(Map<String, Supplier<StorageClient>> suppliers) {
        this.suppliers = suppliers;
    }

    public StorageClient create(String provider) {
        Supplier<StorageClient> supplier = suppliers.get(provider);
        if (supplier == null) {
            throw new IllegalArgumentException("unknown provider: " + provider);
        }
        return supplier.get();
    }
}
```

이 구조도 계속 비대해지면, 생성과 선택을 더 분리해야 할 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 `new` / 생성자 | 가장 단순하고 바로 읽힌다 | 생성 규칙이 퍼지면 변경이 번진다 | 단순 값 객체, 작은 DTO |
| 정적 팩토리 메서드 | 이름 있는 생성이 가능하다 | 구현 선택 문제는 잘 표현하지 못한다 | 같은 타입 생성 variant |
| Factory | 생성 규칙과 구현 선택을 한곳에 모은다 | 클래스와 추상화가 하나 더 생긴다 | 환경별 구현, 외부 SDK, 초기화 규칙 |
| Builder | 옵션과 조립 과정이 드러난다 | 구현 선택 문제에는 맞지 않는다 | 복잡한 한 객체 생성 |
| Registry / DI | 선택과 조립 책임을 분리한다 | 구조가 더 무거워질 수 있다 | 구현 수가 많고 wiring이 중요할 때 |

### Factory를 쓰지 않는 편이 좋은 신호

- 호출부가 `new`보다 더 읽기 쉬워지지 않는다
- 생성 규칙보다 단순 포장 메서드가 많다
- `AFactory`, `BFactory`, `CFactory`가 기계적으로 늘어난다
- 팩토리 안에 정책 판단과 조회 책임이 같이 들어간다
- 테스트 helper 이름만 factory일 뿐 실제로는 builder 역할을 한다

---

## 꼬리질문

> Q: 팩토리와 정적 팩토리 메서드는 같은가요?
> 의도: 구현 방식과 패턴 책임을 구분하는지 확인한다.
> 핵심: 정적 팩토리는 생성 API 형태이고, Factory 패턴은 생성 책임 분리다.

> Q: `new`가 보이면 항상 팩토리로 감싸야 하나요?
> 의도: 과설계를 피하는 기준을 아는지 확인한다.
> 핵심: 아니다. 생성 규칙이 단순하면 직접 생성이 더 낫다.

> Q: factory switch가 계속 커지면 어떻게 하나요?
> 의도: 생성과 선택 책임 분리를 이해하는지 확인한다.
> 핵심: Registry, Strategy, DI 쪽으로 역할을 다시 나눈다.

> Q: Builder와 Factory 중 언제 Builder를 보나요?
> 의도: 생성 "선택"과 "조립"을 구분하는지 확인한다.
> 핵심: 구현 선택보다 옵션 많은 한 객체 조립이 중요하면 Builder가 맞다.

## 한 줄 정리

Factory는 생성 규칙과 구현 선택을 숨길 때 강하지만, 단순 생성까지 전부 감싸면 과설계가 된다. 먼저 `new`, 정적 팩토리, Builder, Registry 중 더 단순한 대안이 없는지 본다.
