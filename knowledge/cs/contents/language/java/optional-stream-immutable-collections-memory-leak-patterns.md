---
schema_version: 3
title: Optional Stream Immutable Collections Memory Leak Patterns
concept_id: language/optional-stream-immutable-collections-memory-leak-patterns
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- optional
- stream
- memory-leak
aliases:
- Optional Stream Immutable Collections Memory Leak Patterns
- Java Optional Stream immutable collection pitfalls
- Optional field parameter Stream boxing overhead
- unmodifiableList List.copyOf read only view
- Java memory leak pattern API intent cost
- 자바 Optional Stream 불변 컬렉션 메모리 누수
symptoms:
- Optional, Stream, unmodifiable collection을 문법 축약 도구로만 써서 API 의도, boxing 비용, lazy evaluation, read-only view 차이를 놓쳐
- Optional field나 parameter, Optional collection, Stream side effect가 섞이며 코드가 짧아졌지만 의미와 비용이 더 불분명해져
- Collections.unmodifiableList를 immutable copy로 오해하거나 List.copyOf와 view wrapper 차이를 구분하지 못해 외부 mutation이 비쳐
- static collection, listener, ThreadLocal, cache key 같은 Java memory leak pattern을 GC가 알아서 해결할 문제로만 오해해
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/java-optional-basics
- language/java-stream-lambda-basics
- language/immutable-objects-and-defensive-copying
next_docs:
- language/optional-field-parameter-antipattern-card
- language/list-copyof-listof-unmodifiablelist-beginner-bridge
- language/threadlocal-leaks-context-propagation
linked_paths:
- contents/language/java/immutable-objects-and-defensive-copying.md
- contents/language/java/autoboxing-integercache-null-unboxing-pitfalls.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
- contents/language/java/collections-performance.md
- contents/language/java/java-optional-basics.md
- contents/language/java/java-stream-lambda-basics.md
confusable_with:
- language/optional-field-parameter-antipattern-card
- language/list-copyof-listof-unmodifiablelist-beginner-bridge
- language/collections-performance
forbidden_neighbors: []
expected_queries:
- Optional Stream immutable collections를 쓸 때 문법보다 의도와 비용을 어떻게 봐야 해?
- Optional field parameter와 Stream side effect가 Java API design에서 왜 문제가 될 수 있어?
- unmodifiableList와 List.copyOf의 read only view와 immutable snapshot 차이를 설명해줘
- Java memory leak pattern에서 static collection listener ThreadLocal cache key를 어떻게 점검해?
- Stream boxing overhead와 Optional 남용을 성능과 가독성 관점에서 비교해줘
contextual_chunk_prefix: |
  이 문서는 Optional, Stream, immutable/read-only collections, Java memory leak pattern을 API intent와 runtime cost 관점에서 점검하는 advanced playbook이다.
  Optional pitfalls, Stream overhead, immutable collection, unmodifiableList, memory leak 질문이 본 문서에 매핑된다.
---
# Optional, Stream, Immutable Collections, Memory Leak Patterns

**난이도: 🔴 Advanced**

> Java 8 이후 API를 쓸 때 "문법"보다 "의도와 비용"을 먼저 보게 만드는 실전 정리

> 관련 문서:
> - [Language README](../README.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
> - [Java Collections 성능 감각](./collections-performance.md)

> retrieval-anchor-keywords: Optional, Stream, immutable collections, unmodifiableList, List.copyOf, Optional field, Optional parameter, IntStream, boxing overhead, autoboxing, memory leak pattern, read-only view

<details>
<summary>Table of Contents</summary>

- [왜 이 주제를 알아야 하는가](#왜-이-주제를-알아야-하는가)
- [Optional의 정확한 역할](#optional의-정확한-역할)
- [Optional을 잘 쓰는 법](#optional을-잘-쓰는-법)
- [Stream의 장점과 한계](#stream의-장점과-한계)
- [Stream과 Optional을 같이 볼 때](#stream과-optional을-같이-볼-때)
- [불변 컬렉션과 읽기 전용 뷰](#불변-컬렉션과-읽기-전용-뷰)
- [Java 메모리 누수 패턴](#java-메모리-누수-패턴)
- [실전 선택 기준](#실전-선택-기준)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제를 알아야 하는가

Java 8 이후의 편의 API는 코드 길이를 줄여준다.
하지만 실제로는 다음 질문을 같이 봐야 한다.

- 이 API가 진짜 의도를 잘 드러내는가
- 숨은 비용이 없는가
- 예외나 null, 빈 컬렉션을 더 명확하게 다루는가
- 유지보수할 때 오해를 줄이는가

Optional, Stream, 불변 컬렉션은 모두 "더 안전하게 쓰기 위한 도구"처럼 보이지만, 잘못 쓰면 오히려 읽기 어려워진다.

---

## Optional의 정확한 역할

`Optional`은 **값이 없을 수 있음을 명시적으로 표현하는 컨테이너**다.

### 의도

- null 반환을 바로 드러내기 위해 사용한다
- 호출자가 "값 없음"을 처리하도록 유도한다

예:

```java
public Optional<User> findUser(long id) {
    return Optional.ofNullable(userRepository.findById(id));
}
```

### 잘 맞는 곳

- 조회 결과가 없을 수 있는 경우
- 반환값으로 "없음"을 명시하고 싶을 때

### 잘 맞지 않는 곳

- 필드 타입으로 남발하는 경우
- 메서드 파라미터로 자주 받는 경우
- 컬렉션 요소를 모두 Optional로 감싸는 경우

`Optional`은 "항상 써야 하는 만능 null 대체재"가 아니다.  
특히 DTO 필드나 엔티티 필드에까지 넣으면 오히려 직렬화, 바인딩, 가독성에서 손해를 볼 수 있다.

이 감각은 JSON PATCH나 schema evolution 경계에선 더 중요하다.  
필드에서 `Optional`이 missing과 explicit null을 대신해주지 않는다는 점은 [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)에서 이어서 볼 수 있다.

---

## Optional을 잘 쓰는 법

### `get()`보다 `orElse*` 계열을 우선한다

```java
User user = findUser(id).orElseThrow();
```

`get()`은 값이 없을 때 예외가 나지만, 의도가 드러나지 않는다.  
명시적으로 `orElseThrow()`를 쓰는 편이 읽기 쉽다.

### `orElse()`와 `orElseGet()`을 구분한다

```java
User user1 = optional.orElse(expensiveDefault());
User user2 = optional.orElseGet(() -> expensiveDefault());
```

- `orElse()`는 기본값 표현식을 먼저 평가할 수 있다
- `orElseGet()`은 값이 없을 때만 호출한다

즉 기본값 생성 비용이 크면 `orElseGet()`이 더 안전하다.

### `map`, `flatMap`, `filter`로 흐름을 유지한다

`Optional`은 조건 분기를 줄이고, 값이 있으면 처리한다는 흐름을 유지하는 데 유리하다.

```java
return findUser(id)
        .map(User::getName)
        .filter(name -> !name.isBlank())
        .orElse("anonymous");
```

---

## Stream의 장점과 한계

`Stream`은 **컬렉션을 선언적으로 처리하기 위한 도구**다.

### 장점

- "무엇을 할지"가 드러난다
- 필터, 변환, 집계를 연결하기 쉽다
- 반복문보다 의도를 압축해서 표현할 수 있다

예:

```java
List<String> names = users.stream()
        .filter(User::isActive)
        .map(User::getName)
        .sorted()
        .toList();
```

### 한계

- 디버깅이 어렵게 느껴질 수 있다
- 지나치게 중첩되면 오히려 읽기 힘들다
- 모든 루프를 Stream으로 바꾸는 것이 목적이 되면 안 된다

### 성능 감각

- Stream이 항상 느린 것은 아니지만, 항상 빠른 것도 아니다
- 단순 반복과 조건문은 일반 루프가 더 읽기 쉬운 경우가 많다
- 스트림 체인이 길어지면 중간 단계의 비용과 가독성을 함께 봐야 한다
- primitive를 wrapper stream으로 올리면 boxing 비용이 hot path에 숨어들 수 있다

---

## Stream과 Optional을 같이 볼 때

둘 다 "값이 없을 수 있음"을 다루지만 역할이 다르다.

- `Optional`: 단일 값의 존재 여부
- `Stream`: 여러 값의 처리 흐름

예를 들어:

- 단일 조회 결과는 `Optional<User>`
- 여러 사용자 목록 처리에는 `Stream<User>`

둘을 억지로 바꾸지 않는 것이 중요하다.  
특히 `Optional<List<T>>`처럼 "없음"과 "빈 리스트"를 동시에 표현해야 하는 상황은 설계를 다시 보는 편이 낫다.

---

## 불변 컬렉션과 읽기 전용 뷰

Java에는 비슷해 보이지만 성질이 다른 세 가지가 있다.

### `List.of`, `Set.of`, `Map.of`

- 진짜 불변 컬렉션을 만든다
- 구조 수정이 불가능하다
- `null`을 허용하지 않는다

### `List.copyOf`, `Set.copyOf`, `Map.copyOf`

- 원본을 복사해서 불변 컬렉션을 만든다
- 원본과 분리된 스냅샷이 된다

### `Collections.unmodifiableList`

- 원본을 감싸는 읽기 전용 뷰다
- 구조 수정은 막지만 원본 변경을 차단하지는 못한다

즉 "못 바꾸게 보이는가"와 "진짜로 분리되었는가"는 다르다.

### 실전 감각

- 외부에 노출할 값은 가능하면 불변 컬렉션으로 돌려준다
- 내부 상태 보호가 목적이면 뷰가 아니라 스냅샷이 더 안전하다
- 요소 객체까지 가변이면 컬렉션만 불변으로 만들어도 충분하지 않을 수 있다

---

## Java 메모리 누수 패턴

Java는 GC가 있으므로 C/C++식의 직접 해제 실수는 줄어든다.  
그렇다고 메모리 누수가 사라지는 것은 아니다.

### 1. static 컬렉션에 계속 쌓이는 객체

```java
private static final List<User> cache = new ArrayList<>();
```

- 참조가 살아 있어서 GC 대상이 되지 않는다
- 캐시 정책이 없으면 사실상 누수처럼 커진다

### 2. Listener / Callback 해제 누락

- 이벤트 등록만 하고 해제를 안 하면 오래 살아남는다
- UI나 서버 프레임워크에서 자주 문제가 된다

### 3. `ThreadLocal` 정리 누락

- 스레드 풀 환경에서 특히 위험하다
- 작업이 끝난 뒤 `remove()`를 하지 않으면 다음 작업까지 값이 남을 수 있다

### 4. 무한정 성장하는 캐시

- 실제로는 "의도된 보관"이지만 한도와 만료가 없으면 누수와 비슷한 증상을 만든다
- 크기 제한, TTL, eviction 정책이 필요하다

### 5. 외부 자원과 함께 남는 참조

- 파일 핸들, 네이티브 메모리, 직접 버퍼처럼 GC 바깥 자원이 섞이면 더 주의해야 한다
- 객체만 살아 있고 자원은 회수되지 않는 상태가 운영 장애로 이어질 수 있다

---

## 실전 선택 기준

### 값이 없을 수 있음을 명시해야 하나

- 반환값이면 `Optional`을 고려한다
- 필드와 파라미터에는 남발하지 않는다

### 단순 변환/필터/집계인가

- `Stream`이 잘 맞는다
- 너무 짧고 단순하면 일반 루프가 더 낫다

### 외부에 건네는 컬렉션인가

- 불변 컬렉션 또는 복사본을 우선한다
- 읽기 전용 뷰만으로는 내부 상태가 보호되지 않을 수 있다

### 오래 살아남는 참조가 있는가

- static, listener, thread-local, 캐시를 먼저 의심한다
- "GC가 있으니 괜찮다"는 가정은 틀릴 수 있다

---

## 면접에서 자주 나오는 질문

### Q. `Optional`은 어디에 쓰는 게 좋은가요?

- 반환값에서 값이 없을 수 있음을 명시할 때 적합하다.
- 필드나 파라미터에는 보통 남발하지 않는 편이 낫다.

### Q. `orElse()`와 `orElseGet()` 차이는 무엇인가요?

- `orElse()`는 기본값 표현식이 먼저 평가될 수 있고,
- `orElseGet()`은 값이 없을 때만 호출된다.

### Q. `Stream`을 항상 써야 하나요?

- 아니다.
- 간단한 반복은 일반 루프가 더 명확할 수 있고, Stream은 선언적 처리에 강점이 있다.

### Q. `List.of()`와 `Collections.unmodifiableList()` 차이는 무엇인가요?

- `List.of()`는 진짜 불변 컬렉션을 만들고,
- `unmodifiableList()`는 기존 리스트를 감싼 읽기 전용 뷰다.

### Q. Java에서 메모리 누수는 왜 생기나요?

- 참조가 계속 남아 GC 대상이 되지 않기 때문이다.
- static 컬렉션, listener, ThreadLocal, 무한 캐시가 대표적이다.
