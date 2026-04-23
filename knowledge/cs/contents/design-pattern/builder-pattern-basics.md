# 빌더 패턴 기초 (Builder Pattern Basics)

> 한 줄 요약: 빌더 패턴은 생성자 인자가 많거나 선택적 필드가 섞일 때, 메서드 체이닝으로 읽기 쉽고 실수 없는 객체 생성 흐름을 만들어준다.

**난이도: 🟢 Beginner**

관련 문서:

- [빌더 패턴 심화](./builder-pattern.md)
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Java 제네릭 기초](../language/java/java-generics-basics.md)

retrieval-anchor-keywords: builder pattern basics, 빌더 패턴 기초, 빌더 패턴이 뭔가요, builder pattern beginner, 생성자 인자 많을 때, 생성자 대신 빌더, lombok builder, 빌더 패턴 언제 쓰나, 객체 생성 빌더, telescoping constructor 문제, beginner builder, 빌더 패턴 예시

---

## 핵심 개념

빌더 패턴은 **인자가 많은 객체를 단계적으로 조립**하는 방식이다. 생성자에 인자를 나열하는 것보다 각 필드를 이름과 함께 설정하므로 코드 가독성이 높아지고 실수가 줄어든다.

입문자가 자주 겪는 상황: 생성자 인자가 5개 이상이 되면 어떤 위치에 무슨 값을 넣는지 파악하기 어렵다. 이때 빌더를 쓰면 `new Order(true, false, null, 3, "CARD")` 같은 코드가 `Order.builder().paid(true).quantity(3).payMethod("CARD").build()` 처럼 바뀐다.

## 한눈에 보기

```
Order.builder()
     .customerId(1L)
     .quantity(2)
     .payMethod("CARD")
     .build()   ──→  Order 객체 완성
```

| 항목 | 설명 |
|------|------|
| 목적 | 복잡한 객체를 단계별로 조립 |
| 핵심 메서드 | `build()` — 최종 객체 반환 |
| 대표 도구 | Lombok `@Builder`, Java record 패턴 |
| 주의점 | `build()` 전 필수 필드 누락 검증 |

## 상세 분해

빌더는 네 가지 역할로 이뤄진다.

- **Builder 클래스** — 설정 메서드(setter-like)들을 갖고 있으며 자신을 반환해 체이닝을 지원한다.
- **`build()` 메서드** — 지금까지 설정한 값으로 실제 객체를 만들어 반환한다.
- **불변 객체 보장** — `build()` 시점에 필수 필드를 검증하고, 완성된 객체는 수정하지 못하게 만들 수 있다.
- **선택적 필드 처리** — 설정하지 않은 필드는 기본값으로 채워진다.

Lombok을 쓰면 `@Builder` 어노테이션 하나로 위 구조를 자동 생성할 수 있다. 단, Lombok 없이도 내부 정적 클래스로 직접 구현할 수 있다.

## 흔한 오해와 함정

- **"빌더는 항상 더 좋다"** — 필드가 2~3개라면 생성자가 더 간결하다. 빌더는 필드가 많거나 선택적 조합이 다양할 때 빛을 발한다.
- **"빌더를 쓰면 불변 객체가 된다"** — 빌더가 불변을 강제하지는 않는다. `build()` 이후 객체에 setter가 있으면 여전히 변경 가능하다.
- **"`build()` 호출 전에 실패한다"** — 검증 로직을 `build()` 안에 넣어야 한다. 검증 없이 쓰면 필수 필드가 null인 채 객체가 만들어질 수 있다.

## 실무에서 쓰는 모습

HTTP 요청 객체, 쿼리 조건 객체, 복잡한 도메인 엔티티를 테스트 픽스처로 만들 때 자주 쓴다. 테스트 코드에서 `Order.builder().quantity(1).build()` 처럼 필요한 필드만 지정하면 나머지는 기본값으로 채워져 테스트 준비 코드가 짧아진다.

Spring에서는 `UriComponentsBuilder.fromHttpUrl(...).queryParam(...).build()` 처럼 빌더를 체이닝으로 URL을 조립하는 API가 흔하다.

## 더 깊이 가려면

- [빌더 패턴 심화](./builder-pattern.md) — Director 역할, Step Builder, 불변 객체 설계와의 연결
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md) — 팩토리와 빌더의 선택 기준 비교

## 면접/시니어 질문 미리보기

> Q: 빌더 패턴을 사용하는 이유는?
> 의도: 단순 암기인지 트레이드오프를 아는지 확인한다.
> 핵심: 인자 순서 실수를 방지하고, 선택적 필드가 많은 객체의 가독성을 높인다.

> Q: Lombok `@Builder`와 직접 구현 빌더의 차이는?
> 의도: 도구 선택 기준을 생각하는지 확인한다.
> 핵심: `@Builder`는 코드를 줄여주지만, 검증 로직이나 상속 구조에서는 직접 구현이 필요한 경우가 있다.

> Q: 빌더 패턴이 팩토리 패턴과 다른 점은?
> 의도: 생성 패턴 간 차이를 설명하는지 확인한다.
> 핵심: 팩토리는 어떤 타입을 만들지 결정하고, 빌더는 복잡한 객체를 단계별로 조립하는 데 집중한다.

## 한 줄 정리

빌더 패턴은 인자가 많은 객체 생성에서 순서 실수를 없애고, 이름 있는 메서드 체이닝으로 의도를 명확하게 드러내는 생성 패턴이다.
