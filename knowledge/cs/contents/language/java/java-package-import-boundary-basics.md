---
schema_version: 3
title: Java package와 import 경계 입문
concept_id: language/java-package-import-boundary-basics
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- import-does-not-change-access
- top-level-file-name-rule
- package-private-boundary
aliases:
- java package import basics
- java package import beginner
- package랑 import 차이
- 자바 package 왜 쓰는지
- 자바 import 왜 쓰는지
- 자바 파일 두 개로 나눌 때
- 처음 배우는데 package import
- 처음 자바 package 헷갈림
- 자바 package 큰 그림
- package 선언 꼭 써야 하나요
- public class 파일명 왜 같아야 해
- 같은 패키지 import 안 해도 되나요
- default package 왜 피하나요
- beginner java package structure
- what is java package import
symptoms:
- package랑 import가 각각 뭘 담당하는지 섞여
- 같은 패키지인데 왜 import를 안 써도 되는지 모르겠어
- public class 파일명 규칙이 package 개념이랑 따로 노는 것 같아
intents:
- definition
prerequisites:
- language/java-language-basics
- language/java-types-class-object-oop-basics
next_docs:
- language/java-package-boundary-quickcheck-card
- language/java-default-package-avoid-bridge
- language/top-level-type-access-modifier-bridge
- language/java-access-modifiers-member-model-basics
linked_paths:
- contents/language/java/java-language-basics.md
- contents/language/java/java-types-class-object-oop-basics.md
- contents/language/java/java-methods-constructors-practice-primer.md
- contents/language/java/java-package-boundary-quickcheck-card.md
- contents/language/java/java-default-package-avoid-bridge.md
- contents/language/java/java-access-modifiers-member-model-basics.md
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-module-system-runtime-boundaries.md
confusable_with:
- language/top-level-type-access-modifier-bridge
- language/java-package-boundary-quickcheck-card
forbidden_neighbors:
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-package-boundary-quickcheck-card.md
- contents/language/java/java-access-modifiers-member-model-basics.md
expected_queries:
- Java에서 package와 import를 처음 배울 때 큰 그림부터 설명해줘
- 같은 패키지 클래스는 왜 import 없이도 참조되는지 예제로 보고 싶어
- public top-level 타입 파일 이름 규칙이 package 구조와 어떻게 연결되는지 궁금해
- default package를 피하라는 얘기 전에 package 경계 개념부터 잡고 싶어
- import가 접근 권한까지 바꾸는 건지 초보자 기준으로 정리해줘
contextual_chunk_prefix: |
  이 문서는 Java 입문자가 package를 단순 폴더 이름이 아니라
  이름공간과 공개 경계로 보고, import는 이름을 줄여도 접근 권한은
  바꾸지 않는다는 흐름을 처음 잡는 primer다. 파일을 둘로 나누는
  순간부터, 같은 패키지는 왜 바로 보이나, import가 문을 열어 주는
  건 아닌가, public 타입과 파일명은 왜 묶이나, helper를 어디에 둘까
  같은 자연어 paraphrase가 본 문서의 큰 그림에 매핑된다.
---
# Java package와 import 경계 입문

> 한 줄 요약: Java 입문자가 package를 단순 폴더 이름이 아니라 클래스 공개 범위를 나누는 경계로 이해하고, import와 top-level class/file 규칙까지 한 흐름으로 잡도록 돕는 primer다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java package import basics, java package import beginner, package랑 import 차이, 자바 package 왜 쓰는지, 자바 import 왜 쓰는지, 자바 파일 두 개로 나눌 때, 처음 배우는데 package import, 처음 자바 package 헷갈림, 자바 package 큰 그림, package 선언 꼭 써야 하나요, public class 파일명 왜 같아야 해, 같은 패키지 import 안 해도 되나요, default package 왜 피하나요, beginner java package structure, what is java package import
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)
> - [Java default package 회피 브리지](./java-default-package-avoid-bridge.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Java module system runtime boundaries](./java-module-system-runtime-boundaries.md)

> retrieval-anchor-keywords: java package basics, java import basics, java package import boundary basics, java package declaration, java import declaration, java source file structure, java public class file name rule, java top level class file convention, java one public class per file, java package private boundary basics, java default package avoid, java same package no import, java.lang no import, java wildcard import subpackage, java import does not change access, java package private beginner design, java helper class package private, java package naming basics, java beginner package structure, java package boundary quick check, java same package subclass non subclass, java protected package boundary, 자바 패키지 임포트 기초, 자바 package import 기초, 처음 배우는데 package import, 자바 package 왜 쓰는지, 자바 import 언제 쓰는지, import 언제 생략하는지, import 안 해도 되는 경우, 자바 public class 파일명 규칙, 자바 소스 파일 구조 기초, package private 경계 기초, package-private 언제 쓰는지 기초, default package 피하는 이유, 같은 패키지 import 생략, 자바 패키지 경계 퀵체크, package랑 import 차이 뭐예요, package가 폴더 이름인가요, 자바 클래스 파일 나눌 때 뭐부터, 자바 처음인데 package부터 막힘, why use package in java, when do I need import in java, same package no import beginner

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 보는 패키지 경계 퀵체크](#먼저-보는-패키지-경계-퀵체크)
- [package는 무엇을 나누나](#package는-무엇을-나누나)
- [파일, 디렉터리, top-level 클래스 규칙](#파일-디렉터리-top-level-클래스-규칙)
- [import는 이름을 줄여 주지만 접근 권한은 바꾸지 않는다](#import는-이름을-줄여-주지만-접근-권한은-바꾸지-않는다)
- [package-private 경계가 초보자 설계에 주는 영향](#package-private-경계가-초보자-설계에-주는-영향)
- [코드로 한 번에 보기](#코드로-한-번에-보기)
- [초보자가 자주 틀리는 포인트](#초보자가-자주-틀리는-포인트)
- [빠른 체크리스트](#빠른-체크리스트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

이 문서는 `"package랑 import 차이 뭐예요?"`, `"왜 package를 써요?"`, `"자바 파일을 두 개로 나누면 뭐가 달라져요?"` 같은 첫 질문이 들어왔을 때 deep dive보다 먼저 닿아야 하는 입문 primer를 목표로 한다.

Java 입문자는 클래스를 여러 파일로 나누기 시작하는 순간부터 이런 질문을 만나게 된다.

- `package`는 그냥 폴더 이름인가?
- 다른 파일의 클래스를 쓰려면 언제 `import`가 필요한가?
- 클래스 파일 이름은 왜 `public class` 이름과 같아야 하나?
- helper 클래스를 일단 `public`으로 열어 두는 게 편하지 않나?

이 질문들은 사실 따로 떨어져 있지 않다.
핵심은 **"어떤 이름공간에 두고, 어디까지 공개하며, 다른 패키지에서 무엇을 직접 보게 할 것인가"** 를 함께 정하는 데 있다.

## 먼저 보는 패키지 경계 퀵체크

처음엔 긴 규칙보다 아래 한 장으로 보면 된다.

| 보는 관점 | 먼저 물을 질문 | 초보자 기억법 |
|---|---|---|
| same package | package 선언이 정확히 같은가 | `private`만 아니면 대체로 된다 |
| different package + subclass | 같은 package는 아니지만 상속한 클래스 내부인가 | `protected`까지는 열릴 수 있다 |
| different package + non-subclass | 둘 다 아니면 | 사실상 `public`만 본다 |

이 카드가 익숙하지 않다면 [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)에서 10초 판단표와 예시를 먼저 보고 오는 편이 빠르다.

## package는 무엇을 나누나

`package`는 단순히 파일을 정리하는 폴더 이름이 아니다.
Java에서 package는 최소한 다음 두 역할을 동시에 가진다.

- 클래스 이름 충돌을 줄이는 이름공간(namespace)
- package-private 접근 범위를 정하는 경계

### package 선언은 소스 파일의 소속을 정한다

```java
package com.example.order;
```

이 선언은 "이 파일의 top-level 타입들은 `com.example.order` 소속이다"라는 뜻이다.
일반적인 프로젝트 구조에서는 디렉터리도 같은 구조로 맞춘다.

```text
src/main/java/com/example/order/OrderService.java
```

초보자 단계에서는 다음처럼 기억하면 충분하다.

| 질문 | 기본 규칙 |
|---|---|
| package 이름은 어떻게 짓나 | 보통 소문자, 점(`.`)으로 계층을 나눈다 |
| 파일은 어디에 두나 | package 경로와 같은 디렉터리에 둔다 |
| package 선언을 생략해도 되나 | technically 가능하지만, default package는 실제 프로젝트에서 피하는 편이 안전하다 |

### 같은 부모를 공유해도 다른 package일 수 있다

이 부분이 초보자가 자주 놓치는 포인트다.

- `com.example.order`
- `com.example.order.internal`

위 둘은 "비슷해 보이는 이름"일 뿐, **서로 다른 package**다.
즉 `com.example.order`의 package-private 타입은 `com.example.order.internal`에서 바로 쓸 수 없다.

package 경계는 "폴더가 비슷한가"가 아니라 **package 선언이 정확히 같은가**로 결정된다.

## 파일, 디렉터리, top-level 클래스 규칙

Java는 source file과 top-level 타입 사이에 비교적 강한 규칙을 둔다.

### 초보자가 먼저 기억해야 할 네 가지

| 규칙 | 의미 | 초보자 기본값 |
|---|---|---|
| `package` 선언은 `import`보다 먼저 나온다 | 파일 소속을 먼저 정하고 그다음 외부 타입을 들여온다 | 파일 상단에 `package`, 그 아래 `import` |
| top-level `public` 타입은 파일당 하나다 | `public class`, `public interface`, `public enum`, `public record` 모두 같은 규칙을 따른다 | 파일 하나에 `public` 타입 하나 |
| `public` 타입 이름과 파일 이름은 같아야 한다 | `public class OrderService`는 `OrderService.java`에 있어야 한다 | 타입명과 파일명 맞추기 |
| 여러 top-level package-private 타입은 technically 가능하다 | 하지만 읽기와 탐색이 어려워진다 | 입문 단계에서는 한 파일 한 top-level 타입으로 유지 |

예를 들면 아래는 자연스럽다.

```java
// OrderService.java
package com.example.order;

public class OrderService {
}
```

반대로 아래는 허용되지 않는다.

```java
// WrongFile.java
package com.example.order;

public class OrderService {
}
```

파일 이름이 `OrderService.java`가 아니기 때문이다.

### top-level 클래스에 쓸 수 있는 접근 수준은 제한적이다

top-level 타입은 `public` 또는 package-private만 가능하다.
즉 파일 최상단 클래스에 `private`나 `protected`를 붙일 수는 없다.

이 규칙은 초보자 설계에서 중요하다.

- 다른 package에서 직접 써야 하면 `public`
- 같은 package 안의 보조 타입이면 package-private

## import는 이름을 줄여 주지만 접근 권한은 바꾸지 않는다

`import`는 "다른 package의 타입을 짧은 이름으로 쓰게 해 주는 문법"이다.
중요한 점은 **가시성(visibility)을 넓혀 주는 기능이 아니라는 것**이다.

### 언제 import가 필요하고, 언제 필요하지 않은가

| 상황 | import 필요 여부 | 설명 |
|---|---|---|
| 같은 package 타입 사용 | 보통 불필요 | 같은 package 안에서는 simple name으로 바로 쓸 수 있다 |
| `java.lang` 타입 사용 | 불필요 | `String`, `Integer`, `System`은 자동으로 보인다 |
| 다른 package의 `public` 타입 사용 | 필요하거나 fully qualified name 사용 | 보통 `import`를 쓴다 |
| 다른 package의 package-private 타입 사용 | import로도 불가 | 접근 권한 자체가 없기 때문이다 |

예를 들어 `OrderService`와 `OrderValidator`가 같은 package라면 서로 import 없이 쓸 수 있다.

```java
package com.example.order;

public class OrderService {
    private final OrderValidator validator = new OrderValidator();
}
```

하지만 다른 package에서는 다르다.

```java
package com.example.app;

import com.example.order.OrderService; // 가능
// import com.example.order.OrderValidator; // 불가: package-private
```

### wildcard import는 subpackage까지 가져오지 않는다

```java
import java.util.*;
```

이 문장은 `java.util` 안의 타입 이름을 줄여 주는 것이지, 아래 둘을 한꺼번에 열어 주는 것이 아니다.

- `java.util.concurrent`
- `java.util.stream`

즉 `import java.util.*;`를 써도 `List`는 되지만 `ExecutorService`는 별도로 `java.util.concurrent` 쪽 import가 필요하다.

### 이름 충돌이 나면 fully qualified name이 필요할 수 있다

서로 다른 package에 같은 simple name이 있으면 import만으로는 모호해질 수 있다.
이럴 때는 한쪽을 fully qualified name으로 써서 구분한다.

### `import static`은 가능하지만 초보자 단계에서는 절제해서 쓴다

```java
import static java.lang.Math.max;
```

이 문법은 static 멤버를 클래스 이름 없이 쓰게 해 주지만, 처음에는 출처를 흐리기 쉽다.
입문 단계에서는 일반 `import`를 먼저 확실히 익히는 편이 낫다.

## package-private 경계가 초보자 설계에 주는 영향

초보자 코드는 종종 "일단 다 `public`으로 열어 두고 나중에 정리"로 흐른다.
하지만 Java에서는 처음부터 경계를 조금만 의식해도 클래스 구조가 훨씬 깔끔해진다.

### 기본 분리 기준

| 공개 범위 | 언제 쓰나 | 예시 |
|---|---|---|
| `public` | 다른 package에서도 알아야 하는 타입 | 서비스 entrypoint, 외부에 반환하는 타입 |
| package-private | 같은 package 안의 협력자만 알아야 하는 타입 | validator, mapper, parser, policy helper |
| `private` | 한 클래스 내부 구현 조각 | field, helper method, nested helper |

즉 package-private은 "modifier를 빼먹은 상태"가 아니라 **패키지 내부 협력자에게만 여는 설계 도구**다.

### 초보자에게 특히 유용한 이유

1. helper 클래스를 외부 API처럼 노출하지 않게 해 준다.
2. "같이 바뀌는 클래스들"을 작은 package 단위로 묶게 해 준다.
3. import가 된다고 해서 아무 클래스나 써도 된다는 착각을 막아 준다.

예를 들어 `OrderService`가 `OrderValidator`를 내부 구현으로만 쓰고 있다면, `OrderValidator`를 `public`으로 열 이유가 없다.

- 다른 package가 그 타입을 직접 쓸 필요가 없다.
- 나중에 구현을 바꾸거나 이름을 바꾸기 쉬워진다.
- 초보자가 "어떤 클래스가 진짜 외부 계약인가"를 구분하는 연습이 된다.

### 초보자용 package 설계 감각

처음부터 큰 아키텍처를 만들 필요는 없다.
대신 다음 질문으로 충분하다.

- 이 타입을 다른 package에서 직접 생성하거나 호출해야 하나?
- 아니면 같은 기능 묶음 안에서만 도와주는가?
- helper를 `public`으로 여는 이유를 한 문장으로 설명할 수 있는가?

설명할 수 없다면 package-private이 더 자연스러운 경우가 많다.

## 코드로 한 번에 보기

아래는 package 구조, import, file convention, package-private 협력자를 한 번에 보여 주는 최소 예시다.

```text
src/main/java/com/example/order/Order.java
src/main/java/com/example/order/OrderService.java
src/main/java/com/example/order/OrderValidator.java
src/main/java/com/example/app/Main.java
```

```java
// Order.java
package com.example.order;

public record Order(String id) {
}

// OrderService.java
package com.example.order;

public class OrderService {
    public Order create(String rawId) {
        OrderValidator.validate(rawId); // same package, no import needed
        return new Order(rawId.trim());
    }
}

// OrderValidator.java
package com.example.order;

final class OrderValidator {
    private OrderValidator() {
    }

    static void validate(String rawId) {
        if (rawId == null || rawId.isBlank()) {
            throw new IllegalArgumentException("id must not be blank");
        }
    }
}

// Main.java
package com.example.app;

import com.example.order.Order;
import com.example.order.OrderService;
// import com.example.order.OrderValidator; // 컴파일 에러

public class Main {
    public static void main(String[] args) {
        OrderService service = new OrderService();
        Order order = service.create(" A-1001 ");
        System.out.println(order.id());
    }
}
```

이 예시에서 초보자가 봐야 할 핵심은 다음이다.

## 코드로 한 번에 보기 (계속 2)

- `Order`, `OrderService`는 다른 package에서 써야 하므로 `public`이다.
- `OrderValidator`는 `com.example.order` 내부 구현이라 package-private이다.
- 같은 package 안에서는 `OrderService`가 `OrderValidator`를 import 없이 쓴다.
- `Main`은 다른 package이므로 `OrderValidator`를 직접 쓸 수 없다.
- 각 `public` top-level 타입은 자기 이름과 같은 파일에 있다.

## 초보자가 자주 틀리는 포인트

### package를 폴더 정리 용도만으로 본다

Java에서 package는 단순 정리 단위가 아니라 접근 경계다.
특히 package-private을 이해하려면 "같은 package인가"를 먼저 봐야 한다.

### subpackage도 같은 package라고 생각한다

`com.example.order`와 `com.example.order.internal`은 다른 package다.
이름이 길게 이어져 보여도 package-private 경계는 공유되지 않는다.

### `import`만 하면 아무 클래스나 쓸 수 있다고 생각한다

아니다. `import`는 이름을 줄여 줄 뿐이다.
`private`, package-private, `protected` 같은 접근 규칙을 우회하지 못한다.

### wildcard import가 하위 package까지 포함한다고 생각한다

`java.util.*`는 `java.util.concurrent.*`를 포함하지 않는다.

### helper 클래스를 습관적으로 `public`으로 만든다

외부 계약이 아닌 helper까지 전부 `public`으로 열면 패키지 바깥 코드가 내부 구현에 의존하기 쉬워진다.

### default package를 가볍게 쓴다

학습용 단일 파일 예제에서는 돌아갈 수 있지만, 실제 프로젝트로 가면 import와 구조화가 빠르게 불편해진다.
입문 단계부터 package 선언을 붙이는 습관이 더 낫다.
이 지점을 파일명 규칙 다음 단계 브리지로 짧게 이어 보고 싶다면 [Java default package 회피 브리지](./java-default-package-avoid-bridge.md)를 보면 된다.

## 빠른 체크리스트

- `package`는 이름공간이면서 package-private 경계다.
- 같은 package면 보통 import 없이 타입 이름을 바로 쓸 수 있다.
- `java.lang`은 import 없이 보인다.
- 다른 package의 package-private 타입은 import로도 접근할 수 없다.
- top-level `public` 타입은 파일당 하나, 파일명과 타입명이 같아야 한다.
- subpackage는 같은 package가 아니다.
- helper가 외부 계약이 아니라면 package-private부터 검토한다.

## 어떤 문서를 다음에 읽으면 좋은가

- Java 소스 파일 구조와 기본 문법을 더 넓게 다시 보고 싶다면 [자바 언어의 구조와 기본 문법](./java-language-basics.md)
- 클래스, 객체, 인터페이스 같은 기본 타입 모델과 연결해서 보고 싶다면 [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- same package / subclass / non-subclass를 10초 표로 먼저 판단하고 싶다면 [Java 패키지 경계 퀵체크 카드](./java-package-boundary-quickcheck-card.md)
- default package를 왜 실제 코드에서 빨리 벗어나야 하는지 짧게 잇고 싶다면 [Java default package 회피 브리지](./java-default-package-avoid-bridge.md)
- `public`/`private`/`protected`/package-private 차이를 멤버 모델까지 이어서 보고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 메서드와 생성자를 어떤 클래스를 외부에 노출할지라는 관점과 함께 연습하고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- package보다 한 단계 큰 런타임 경계인 module system까지 이어 보고 싶다면 [Java module system runtime boundaries](./java-module-system-runtime-boundaries.md)

## 한 줄 정리

Java의 `package`는 단순 폴더가 아니라 공개 범위를 나누는 경계이고, `import`는 그 경계를 넘게 해 주는 권한이 아니라 **이미 허용된 `public` 타입의 이름을 짧게 쓰게 해 주는 문법**이다.
