# Java Top-level 타입 접근 제한자 브리지

> 한 줄 요약: 파일 최상단에 두는 타입은 `class`든 `interface`든 `enum`이든 `record`든 똑같이 `public` 또는 package-private만 가능하다고 보면, 파일명 규칙까지 한 번에 정리된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [Java package와 import 경계 입문](./java-package-import-boundary-basics.md)
- [Java default package 회피 브리지](./java-default-package-avoid-bridge.md)
- [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- [접근 제한자 오해 미니 퀴즈: top-level vs member](./java-access-modifier-top-level-member-mini-quiz.md)
- [Java enum 기초](./java-enum-basics.md)
- [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
- [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)

retrieval-anchor-keywords: java top-level access modifier bridge, java top-level type public package-private, java top-level class interface enum record, java top-level protected private compile error, java one public top-level type per file, java public top-level type file name rule, java package-private top-level helper, java public interface enum record file name, java top-level type card, java top-level type quick card, java source file type rule, top-level type basics, top-level type beginner, java top-level vs member private protected, java top-level member mini quiz bridge

## 먼저 잡는 멘탈 모델

top-level 타입은 "패키지 입구에 세우는 간판"이라고 생각하면 쉽다.

- 다른 패키지에서도 보여야 하는 간판이면 `public`
- 같은 패키지 안에서만 쓰는 내부 간판이면 package-private(접근 제한자 생략)

여기서 중요한 점은 **타입의 종류가 바뀌어도 규칙이 안 바뀐다는 것**이다.

- `class`
- `interface`
- `enum`
- `record`

네 가지 모두 top-level이면 같은 접근 제한 규칙을 따른다.

## 한눈 카드

| top-level 타입 종류 | `public` 가능 | package-private 가능 | `protected` 가능 | `private` 가능 |
|---|---|---|---|---|
| `class` | 가능 | 가능 | 불가 | 불가 |
| `interface` | 가능 | 가능 | 불가 | 불가 |
| `enum` | 가능 | 가능 | 불가 | 불가 |
| `record` | 가능 | 가능 | 불가 | 불가 |

핵심 문장 하나로 줄이면 이렇다.

> 파일 최상단에 올라온 타입은 종류와 상관없이 `public` 아니면 package-private 둘 중 하나만 고른다.

## 10초 결정 카드

| 내가 만들려는 것 | top-level에 둘 수 있나 | 접근 제한자 선택 | 바로 떠올릴 규칙 |
|---|---|---|---|
| 다른 패키지에서도 써야 하는 `class` | 가능 | `public` | 파일명은 `ClassName.java` |
| 같은 패키지 안 helper `interface` | 가능 | package-private | 다른 패키지에서는 못 씀 |
| 상태 묶음용 `enum` | 가능 | `public` 또는 package-private | 규칙은 `class`와 동일 |
| 값 묶음용 `record` | 가능 | `public` 또는 package-private | 새 문법이어도 예외 없음 |

초보자용 판단 순서는 이것만 기억하면 충분하다.

1. 파일 최상단 타입인가?
2. 그러면 `public` 또는 package-private만 생각한다.
3. 외부 패키지 공개가 필요하면 `public`, 아니면 package-private로 둔다.

## 작은 예제로 한 번에 보기

```java
public class OrderService {}
interface OrderReader {}
enum OrderStatus { CREATED, PAID }
record OrderId(String value) {}
```

이 코드는 "어떤 타입이 top-level에 올 수 있나"를 보여 주지만, 파일 배치는 보통 이렇게 나눠서 생각하는 편이 이해하기 쉽다.

| 선언 | 의미 | 파일명 규칙 |
|---|---|---|
| `public class OrderService {}` | 외부 패키지에도 공개 | `OrderService.java` |
| `interface OrderReader {}` | 같은 패키지 내부 전용 | `OrderReader.java`처럼 맞추는 편이 읽기 쉽지만 `public` 파일명 강제 규칙은 아님 |
| `enum OrderStatus { ... }` | 같은 패키지 내부 전용 enum | 다른 패키지에서는 직접 사용 불가 |
| `record OrderId(String value) {}` | 같은 패키지 내부 전용 record | 다른 패키지에서는 import해도 사용 불가 |

초보자 기준 안전한 기본값은 이렇다.

1. 외부 패키지에서 직접 써야 하면 `public`
2. 아니면 일단 package-private
3. `public`으로 열었다면 타입명과 파일명을 같게 맞추기

## 같은 규칙이 실제로 어떻게 보이는지

```java
// api/OrderService.java
package api;
public class OrderService {}

// api/OrderType.java
package api;
public enum OrderType { NORMAL, GIFT }

// internal/OrderReader.java
package internal;
interface OrderReader {}

// internal/OrderId.java
package internal;
record OrderId(String value) {}
```

이때 다른 패키지에서 볼 수 있는 범위는 이렇게 갈린다.

| 선언 | 같은 패키지 | 다른 패키지 |
|---|---|---|
| `public class OrderService` | 사용 가능 | 사용 가능 |
| `public enum OrderType` | 사용 가능 | 사용 가능 |
| `interface OrderReader` | 사용 가능 | 사용 불가 |
| `record OrderId` | 사용 가능 | 사용 불가 |

## 파일명 규칙은 `class`만의 규칙이 아니다

많이 하는 오해가 "`public class`만 파일명을 맞추는 것 아닌가?"다. 아니다.

아래 네 선언은 모두 같은 규칙을 따른다.

```java
public class OrderService {}
public interface OrderUseCase {}
public enum OrderStatus { CREATED, PAID }
public record OrderId(String value) {}
```

- `public class OrderService`면 `OrderService.java`
- `public interface OrderUseCase`면 `OrderUseCase.java`
- `public enum OrderStatus`면 `OrderStatus.java`
- `public record OrderId`면 `OrderId.java`

즉 "**public top-level 타입**의 파일명 규칙"이지, "**public class만의 규칙**"이 아니다.

## 자주 헷갈리는 포인트

- `protected interface Foo {}`도 top-level에서는 컴파일 에러다.
- `private enum Status {}`도 top-level에서는 컴파일 에러다.
- `record`도 새 문법일 뿐, top-level 접근 제한 규칙은 예외가 아니다.
- `enum`과 `record`도 "파일 최상단 타입"이라는 점에서는 `class`와 같은 규칙을 따른다.
- import는 이름을 줄일 뿐 접근 권한을 바꾸지 않는다. package-private top-level 타입은 다른 패키지에서 import해도 못 쓴다.
- 멤버 중첩 타입은 별개다. `private static class Helper {}`는 클래스 "안"에 있을 때는 가능하지만, 파일 최상단 top-level에서는 불가다.

## top-level과 nested type을 섞어 헷갈릴 때

| 위치 | 예시 | `private`/`protected` 가능 여부 |
|---|---|---|
| top-level | `private record OrderId(...) {}` | 불가 |
| 클래스 내부 nested type | `private static record OrderId(...) {}` | 가능 |

많이 틀리는 이유는 "`private record`를 본 적이 있다"는 기억 때문이다. 그 코드는 보통 top-level이 아니라 다른 클래스 안에 들어 있던 nested type이다.

## 언제 package-private이 유용한가

초보자 코드는 helper 타입까지 전부 `public`으로 열기 쉽다. 하지만 아래처럼 구분하면 더 안전하다.

| 상황 | 추천 |
|---|---|
| 다른 패키지의 코드가 직접 써야 하는 API 타입 | `public` |
| 같은 패키지 안에서만 협력하는 validator, mapper, parser | package-private |
| 특정 클래스 내부 구현 조각 | top-level로 빼지 말고 nested type 또는 private 메서드 검토 |

즉 package-private은 "빼먹은 modifier"가 아니라 "패키지 내부 전용"을 의도적으로 표현하는 선택지다.

## 한 줄 정리

top-level 타입은 `class`/`interface`/`enum`/`record` 모두 똑같이 `public` 또는 package-private만 가능하고, `public`이면 타입명과 파일명을 반드시 맞춘다.

파일명 규칙 다음에 "`package` 선언은 왜 생략하면 안 되지?"가 이어서 헷갈린다면 [Java default package 회피 브리지](./java-default-package-avoid-bridge.md)로 바로 넘어가면 흐름이 자연스럽다.

짧게 손으로 예측해 보고 싶다면 [접근 제한자 오해 미니 퀴즈: top-level vs member](./java-access-modifier-top-level-member-mini-quiz.md)를 바로 이어서 보면 된다.
