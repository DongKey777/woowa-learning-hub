# 빌더 패턴 기초 (Builder Pattern Basics)

> 한 줄 요약: 빌더 패턴은 생성자 인자가 많거나 선택적 필드가 섞일 때, 메서드 체이닝으로 읽기 쉽고 실수 없는 객체 생성 흐름을 만들어준다.

**난이도: 🟢 Beginner**

관련 문서:

- [빌더 패턴 심화](./builder-pattern.md)
- [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
- [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Java 제네릭 기초](../language/java/java-generics-basics.md)

retrieval-anchor-keywords: builder pattern basics, 빌더 패턴 기초, 빌더 패턴이 뭔가요, builder pattern beginner, 생성자 인자 많을 때, 생성자 대신 빌더, lombok builder, 빌더 패턴 언제 쓰나, 객체 생성 빌더, telescoping constructor 문제, beginner builder, 빌더 패턴 예시, request dto builder, command builder, builder quick check, 빌더 10초, 빌더 30초 비교표, 빌더 1분 예시, 빌더 자주 헷갈리는 포인트, builder confusion points beginner, builder vs static factory beginner, builder micro check, static factory confusion check

---

<a id="builder-quick-entry"></a>

## 빠른 진입: 10초/30초/1분

처음 읽을 때는 `10초 질문 -> 30초 비교표 -> 1분 예시`로 "빌더가 필요한 순간"만 먼저 잡는다.

### 10초 질문

- 생성자 인자가 많아 위치 실수를 자주 내는가?
- 선택 필드 조합이 늘어나서 생성자/정적 팩토리 오버로드가 복잡해졌는가?
- `build()`에서 필수값 검증을 한 번에 모아야 하는가?

### 30초 비교표: Constructor / Static Factory / Builder

| 선택지 | 핵심 질문 | 초보자용 한 줄 |
|---|---|---|
| Constructor | 필드가 적고 의미가 명확한가 | "짧고 단순하면 생성자가 제일 읽기 쉽다" |
| Static Factory | 이름 있는 생성 의도가 필요한가 | "`of/from` 같은 이름으로 의미를 드러낸다" |
| Builder | 필드가 많고 선택 조합이 많은가 | "초안 채우듯 단계적으로 조립한다" |

### 1분 예시: 주문 요청 조립

```java
OrderRequest req = OrderRequest.builder()
    .customerId(1L)
    .quantity(2)
    .payMethod("CARD")
    .build();
```

`new OrderRequest(1L, 2, "CARD", false, null, ...)`처럼 인자 위치를 기억할 필요가 없어서 첫 읽기와 리뷰가 쉬워진다.

### 자주 헷갈리는 포인트 3개

- 체이닝 문법이 있다고 다 빌더는 아니다. 핵심은 "복잡한 생성 조립 + `build()` 시점 검증"이다.
- 빌더를 쓴다고 자동으로 불변 객체가 되지 않는다. 완성 객체의 setter/가변 필드 여부를 따로 확인해야 한다.
- 필드가 2~3개인 단순 객체까지 빌더로 시작하면 오히려 노이즈가 늘 수 있다. 생성자/정적 팩토리가 더 읽기 쉬운지 먼저 본다.

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
- [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md) — 작은 request/query model을 굳이 builder로 시작하지 않아도 되는 기준을 먼저 본다
- [요청 객체 생성 vs DI 컨테이너](./request-object-creation-vs-di-container.md) — request DTO, command, value object를 builder로 조립할 때도 bean wiring과 섞지 않는 기준

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

## 3문항 미니 오해 점검

짧게 판단해 본다. 핵심은 "생성"이라는 공통점보다 "무엇을 편하게 만들려는가"를 보는 것이다.

| 문항 | 헷갈리는 포인트 | 한 줄 정답 기준 |
|---|---|---|
| 1 | Builder vs Static Factory | 이름 있는 한 번 생성이면 static factory, 단계적 조립이면 builder |
| 2 | Builder vs Constructor | 필드가 적고 단순하면 constructor, 선택 조합이 많으면 builder |
| 3 | Builder vs Fluent Setter | 체이닝 문법만으로는 builder가 아니다. `build()`로 완성하는 생성 흐름이 있어야 한다 |

### Q1. `Money.of(currency, amount)`도 Builder인가?

- 정답: 아니다. 보통 static factory다.
- 왜: 한 번의 호출로 완성 객체를 바로 반환하고, 중간 조립 단계가 없다.
- 기억법: `of/from/valueOf`처럼 "이름 있는 즉시 생성"이면 static factory 쪽이다.

### Q2. 필드 2~3개짜리 단순 DTO도 무조건 Builder가 더 좋은가?

- 정답: 아니다.
- 왜: 이런 경우는 생성자나 static factory가 더 짧고 읽기 쉽다. builder는 선택 필드와 조합이 늘어날 때 가치가 커진다.
- 같이 보면 좋은 문서: [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)

### Q3. `.name(...).age(...).save()`처럼 메서드 체이닝이면 Builder인가?

- 정답: 꼭 그렇지 않다.
- 왜: 체이닝은 문법 모양일 뿐이다. builder는 "초안을 모으고 `build()`에서 완성 객체를 만든다"가 핵심이다.
- 체크 질문: "이 체이닝의 끝이 완성 객체 생성인가, 아니면 그냥 상태 변경 API인가?"

## 한 줄 정리

빌더 패턴은 인자가 많은 객체 생성에서 순서 실수를 없애고, 이름 있는 메서드 체이닝으로 의도를 명확하게 드러내는 생성 패턴이다.
