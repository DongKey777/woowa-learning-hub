# Specification Combinator Libraries: 조건식을 조립하는 작은 도구 상자

> 한 줄 요약: Specification combinator library는 and, or, not 같은 조합 연산을 제공해 조건식을 재사용 가능한 라이브러리로 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Specification Pattern](./specification-pattern.md)
> - [Composite Pattern: 쿼리 트리와 규칙 트리를 조립하는 방법](./composite-query-rule-trees.md)
> - [DSL Object Model Pattern](./dsl-object-model-pattern.md)
> - [Policy Object Pattern](./policy-object-pattern.md)

---

## 핵심 개념

Specification 패턴이 조건 객체의 개념이라면, combinator library는 그 객체를 **조합하는 표준 연산 세트**다.

- `and`
- `or`
- `not`
- `xor`
- `allOf`
- `anyOf`

조건이 많아질수록 라이브러리의 가치가 커진다.

### Retrieval Anchors

- `specification combinator`
- `predicate library`
- `condition algebra`
- `boolean combinators`
- `query predicate composition`

---

## 깊이 들어가기

### 1. 조건식을 라이브러리로 보면 중복이 줄어든다

여러 서비스에서 같은 조합 로직을 반복하면, 조합 연산을 라이브러리처럼 두는 편이 좋다.

### 2. 단순 predicate보다 한 단계 더 구조적이다

함수형 predicate도 좋지만, combinator library는 이름이 있는 조건 조합을 제공한다.

- `activeUser()`
- `vipMember()`
- `recentOrder()`

이런 이름을 조합하면 도메인 언어가 유지된다.

### 3. flatten과 short-circuit가 중요하다

조건이 깊게 중첩되면 읽기 어렵다.  
라이브러리는 중첩을 줄이고 평가를 빠르게 끝내야 한다.

---

## 실전 시나리오

### 시나리오 1: 검색 필터 조합

API 필터를 조합해 재사용하는 라이브러리에 적합하다.

### 시나리오 2: 승인 조건

다양한 승인을 표현하는 규칙 조합에 잘 맞는다.

### 시나리오 3: 정책 테스트

조합된 조건을 단위 테스트로 검증할 수 있다.

---

## 코드로 보기

### Combinator 인터페이스

```java
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);

    default Specification<T> and(Specification<T> other) {
        return candidate -> this.isSatisfiedBy(candidate) && other.isSatisfiedBy(candidate);
    }
}
```

### Library helpers

```java
public final class Specs {
    public static <T> Specification<T> anyOf(List<Specification<T>> specs) {
        return candidate -> specs.stream().anyMatch(spec -> spec.isSatisfiedBy(candidate));
    }
}
```

### Usage

```java
Specification<Member> vipActive = vip().and(active());
Specification<Member> target = Specs.anyOf(List.of(vipActive, premium()));
```

Combinator library는 조건식 조합을 표준 API처럼 만들어준다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 직접 `if` | 단순하다 | 중복이 많다 | 조건이 적을 때 |
| Specification combinators | 재사용이 좋다 | 추상화가 늘어난다 | 조건이 반복될 때 |
| DSL Object Model | 표현력이 높다 | 더 무겁다 | 규칙이 문법일 때 |

판단 기준은 다음과 같다.

- 같은 조합이 여러 곳에 반복되면 library화
- 이름 있는 조건을 조합하면 도메인 언어가 살아난다
- 너무 복잡하면 DSL로 넘어간다

---

## 꼬리질문

> Q: combinator library와 DSL Object Model은 어떻게 다르나요?
> 의도: 라이브러리와 모델의 차이를 확인한다.
> 핵심: library는 조합 API, object model은 규칙 구조다.

> Q: anyOf/allOf는 왜 유용한가요?
> 의도: 조합 연산의 재사용성을 아는지 확인한다.
> 핵심: 반복되는 boolean logic을 표준화할 수 있다.

> Q: combinator가 너무 많아지면 안 좋은가요?
> 의도: 추상화 폭발을 경계하는지 확인한다.
> 핵심: 꼭 필요한 연산만 남겨야 한다.

## 한 줄 정리

Specification combinator library는 조건 조합을 재사용 가능한 도구로 만들어 backend 규칙을 단순화한다.

