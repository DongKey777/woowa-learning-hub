---
schema_version: 3
title: Singleton vs DI Container Scope
concept_id: design-pattern/singleton-vs-di-container-scope
canonical: false
category: design-pattern
difficulty: advanced
doc_role: chooser
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
  - singleton-vs-bean-scope
  - global-state-smell
  - lifecycle-owner-boundary
aliases:
  - singleton vs di container scope
  - bean scope vs singleton pattern
  - container managed singleton
  - dependency injection scope
  - request scope vs request object
  - spring request scoped bean vs dto
  - hand rolled singleton vs bean
  - singleton pattern and bean scope difference
symptoms:
  - 싱글톤 패턴이랑 스프링 singleton bean을 같은 말로 써도 되는지 모르겠어
  - request 상태를 singleton bean에 넣어도 되는지 헷갈려
  - 전역 객체 하나 두는 것과 컨테이너가 관리하는 생명주기 차이가 잘 안 잡혀
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - design-pattern/singleton-basics
  - spring/spring-bean-di-basics
next_docs:
  - design-pattern/request-scope-vs-plain-request-objects
  - design-pattern/service-locator-antipattern
  - spring/ioc-di-container
linked_paths:
  - contents/design-pattern/singleton-basics.md
  - contents/design-pattern/singleton-java.md
  - contents/design-pattern/request-scope-vs-plain-request-objects.md
  - contents/design-pattern/service-locator-antipattern.md
  - contents/design-pattern/request-object-creation-vs-di-container.md
  - contents/spring/spring-bean-di-basics.md
  - contents/spring/ioc-di-container.md
confusable_with:
  - design-pattern/singleton-java
  - design-pattern/request-scope-vs-plain-request-objects
  - spring/spring-bean-di-basics
forbidden_neighbors:
expected_queries:
  - 스프링 singleton bean이랑 고전 singleton 패턴을 같은 걸로 이해하면 왜 위험해?
  - 객체를 하나만 쓰고 싶은데 직접 싱글톤으로 만들지 컨테이너에 맡길지 어떻게 판단해?
  - request별 상태가 있는데 singleton scope에 두면 왜 꼬여?
  - bean scope 이야기와 singleton 패턴 설명이 자꾸 섞이는데 경계를 잡아줘
  - 테스트 대역 교체 관점에서 hand-rolled singleton과 DI bean이 어떻게 다른지 알고 싶어
contextual_chunk_prefix: |
  이 문서는 advanced 학습자가 hand-rolled singleton pattern과 DI
  container singleton scope를 구분하도록 돕는 chooser다. bean scope,
  lifecycle owner, global state, request-bound state, test double 교체,
  컨테이너가 하나를 관리하는 것과 코드가 하나를 고정하는 것의 차이를 묻는
  자연어 질문이 이 문서의 판단 기준에 매핑된다.
---
# Singleton vs DI Container Scope

> 한 줄 요약: 디자인 패턴 singleton은 전역 상태를 직접 통제하는 것이고, DI container singleton scope는 객체 생명주기를 컨테이너가 관리하는 것이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [싱글톤 (Singleton) Java 구현 방법](./singleton-java.md)
> - [Request Scope vs Plain Request Objects](./request-scope-vs-plain-request-objects.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

싱글톤 패턴과 DI 컨테이너의 singleton scope는 비슷해 보이지만 같은 말이 아니다.

- singleton pattern: 코드가 직접 하나를 만든다
- singleton scope: 컨테이너가 하나를 제공한다

backend에서는 대부분 후자가 더 자연스럽다.

### Retrieval Anchors

- `singleton vs di container scope`
- `bean scope`
- `container managed singleton`
- `application lifecycle`
- `dependency injection scope`
- `request scope vs request object`
- `spring request scoped bean vs dto`

---

## 깊이 들어가기

### 1. 관리 주체가 다르다

패턴 singleton은 클래스가 책임진다.  
DI singleton scope는 컨테이너가 책임진다.

### 2. 테스트와 교체성이 다르다

컨테이너 관리 객체는 테스트에서 다른 scope나 mock으로 교체하기 쉽다.  
반면 hand-rolled singleton은 전역 상태가 고정되어 바꾸기 어렵다.

### 3. scope는 singleton만 있는 게 아니다

backend에서는 singleton scope 말고도 요청, 세션, 프로토타입 scope를 고려할 수 있다.  
즉 "하나만 있어야 한다"보다 "어느 생명주기여야 하는가"가 더 중요하다.

---

## 실전 시나리오

### 시나리오 1: stateless service

상태가 없는 service bean은 컨테이너 singleton scope로 두는 게 일반적이다.

### 시나리오 2: request-bound state

요청별 상태가 필요하면 singleton이 아니라 request scope나 method-local state를 본다.
다만 request DTO와 command까지 bean으로 올리는 문제는 아니므로, 이 경계는 [Request Scope vs Plain Request Objects](./request-scope-vs-plain-request-objects.md)에서 따로 본다.

### 시나리오 3: heavy resource

비용이 큰 client는 컨테이너가 한 번만 만들고 주입하는 편이 낫다.

---

## 코드로 보기

### design pattern singleton

```java
public final class AppConfig {
    private static final AppConfig INSTANCE = new AppConfig();

    private AppConfig() {}

    public static AppConfig getInstance() {
        return INSTANCE;
    }
}
```

### DI container singleton scope

```java
@Service
public class PaymentService {
    private final PaymentPort paymentPort;

    public PaymentService(PaymentPort paymentPort) {
        this.paymentPort = paymentPort;
    }
}
```

### Why it matters

```java
// 컨테이너 singleton은 테스트 시 다른 bean으로 교체하기 쉽다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| hand-rolled singleton | 단순하다 | 전역 상태가 강하다 | 아주 작은 유틸 |
| DI singleton scope | 관리가 쉽다 | 컨테이너 의존이 생긴다 | 일반적인 backend |
| 다른 scope | 상태를 분리한다 | 생명주기 복잡성이 늘어난다 | 요청/세션 상태 |

판단 기준은 다음과 같다.

- 객체 생명주기를 누가 관리해야 하는지 본다
- 전역 상태를 코드로 직접 만들 필요가 있는지 재검토한다
- 테스트 교체 가능성을 먼저 생각한다

---

## 꼬리질문

> Q: singleton pattern과 singleton scope는 왜 구분해야 하나요?
> 의도: 구현 방식과 생명주기 관리를 구분하는지 확인한다.
> 핵심: 하나를 직접 만드는 것과 컨테이너가 하나를 관리하는 것은 다르다.

> Q: DI container singleton이 항상 좋은가요?
> 의도: scope 선택을 절대 규칙으로 보지 않는지 확인한다.
> 핵심: 상태가 있으면 오히려 위험할 수 있다.

> Q: request state를 singleton에 넣으면 안 되나요?
> 의도: 상태 경계를 아는지 확인한다.
> 핵심: 요청 간 오염이 생긴다.

## 한 줄 정리

디자인 패턴 singleton은 전역 객체를 직접 통제하는 방식이고, DI container singleton scope는 컨테이너가 생명주기를 관리하는 방식이다.
