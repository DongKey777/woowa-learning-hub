---
schema_version: 3
title: Generic Type Erasure Workarounds
concept_id: language/generic-type-erasure-workarounds
canonical: true
category: language
difficulty: intermediate
doc_role: primer
level: intermediate
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- generics
- type-erasure
- runtime-type-info
aliases:
- generic type erasure workarounds
- Java type erasure workaround
- TypeReference super type token
- Class<T> parameter
- runtime generic type info
- List<User> deserialization
- 제네릭 타입 소거 우회
symptoms:
- Java generics가 runtime에 대부분 소거되어 new T, T[], instanceof List<String>이 안 되는 이유를 설명하지 못해
- 역직렬화나 registry에서 List<User> 같은 중첩 타입 정보가 필요할 때 Class<T>만으로 충분하다고 생각해
- super type token, TypeReference, Class<T> 주입, parser registry 같은 우회 패턴의 적용 경계를 구분하지 못해
intents:
- definition
- design
- comparison
prerequisites:
- language/java-generics-basics
next_docs:
- language/reflection-generics-annotations
- language/reflection-cost-and-alternatives
- language/classloader-exception-object-contracts
linked_paths:
- contents/language/java/reflection-generics-annotations.md
- contents/language/java/reflection-cost-and-alternatives.md
- contents/language/java/classloader-exception-boundaries-object-contracts.md
- contents/language/java/collections-performance.md
- contents/language/java/java-generics-basics.md
confusable_with:
- language/reflection-generics-annotations
- language/reflection-cost-and-alternatives
- language/classloader-exception-object-contracts
forbidden_neighbors: []
expected_queries:
- Java generic type erasure 때문에 List<String>과 List<Integer>를 runtime에 구분하기 어려운 이유가 뭐야?
- Class<T> parameter와 TypeReference super type token을 언제 나눠 써야 해?
- List<User> JSON deserialization에서 runtime generic type info를 보존하는 방법을 알려줘
- new T나 T[] 생성이 안 되는 type erasure 제약을 우회하는 패턴을 설명해줘
- ParserRegistry처럼 타입별 handler를 generic erasure와 충돌하지 않게 설계하려면 어떻게 해?
contextual_chunk_prefix: |
  이 문서는 Java generic type erasure를 runtime type information, Class<T>, TypeReference/super type token, generic factory, parser registry, PECS boundary 관점으로 설명하는 intermediate primer다.
  generic type erasure, TypeReference, Class<T>, List<User> deserialization, runtime generic type info 질문이 본 문서에 매핑된다.
---
# Generic Type Erasure Workarounds

> 한 줄 요약: Java Generics는 런타임에 지워지기 때문에, 타입 정보가 꼭 필요하면 별도 보관 구조와 API 설계를 써야 한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)

> 관련 문서:
> - [Reflection, Generics, Annotations](./reflection-generics-annotations.md)
> - [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)
> - [ClassLoader, Exception 경계, 객체 계약](./classloader-exception-boundaries-object-contracts.md)
> - [Java Collections 성능 감각](./collections-performance.md)

<details>
<summary>Table of Contents</summary>

- [왜 필요한가](#왜-필요한가)
- [타입 소거가 남기는 것](#타입-소거가-남기는-것)
- [실전 우회 방법](#실전-우회-방법)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

retrieval-anchor-keywords: generic type erasure, typereference, super type token, class<t> parameter, runtime generic type info, java type erasure workaround, list<user> deserialization, type token pattern, generic factory limitation, pecs boundary, generic type erasure workarounds basics, generic type erasure workarounds beginner, generic type erasure workarounds intro, java basics, beginner java

## 왜 필요한가

제네릭은 타입 안정성을 높이지만, Java는 런타임에서 대부분의 제네릭 정보를 지운다. 그래서 다음이 막힌다.

- `new T()` 불가
- `T[]` 생성 불가
- `List<String>`과 `List<Integer>`를 런타임에 구분하기 어려움
- `instanceof List<String>` 불가

문제는 프레임워크와 직렬화, 리플렉션, 메시지 처리에서 **런타임 타입 정보가 꼭 필요**하다는 점이다.
그래서 우회 패턴을 알아야 한다.

## 타입 소거가 남기는 것

Java는 컴파일 타임에 제네릭을 검증하고, 바이트코드에서는 raw type에 가깝게 바꾼다.

```java
List<String> names = new ArrayList<>();
names.add("kim");
String first = names.get(0);
```

실제로는 `Object` 경로와 캐스팅이 섞인다.
그래서 타입 정보가 필요한 API는 별도로 넘겨야 한다.

### 자주 막히는 지점

- 역직렬화 시 `List<User>` 복원
- 제네릭 팩토리에서 객체 생성
- 공통 저장소/레지스트리 설계
- 타입별 핸들러 매핑

## 실전 우회 방법

### 1. `Class<T>`를 직접 받기

단일 타입이면 가장 단순하다.

```java
public final class JsonReader<T> {
    private final Class<T> type;

    public JsonReader(Class<T> type) {
        this.type = type;
    }

    public T read(String json) {
        // type 기반으로 역직렬화
        return null;
    }
}
```

### 2. `Type` 또는 super type token 사용

컬렉션처럼 중첩 타입이 필요하면 `Class<T>`로는 부족하다.

```java
TypeReference<List<User>> ref = new TypeReference<List<User>>() {};
Type type = ref.getType();
```

익명 클래스의 상위 타입 정보는 `Signature` 메타데이터에 남기 때문에 복구할 수 있다.

### 3. 타입을 API 입력으로 고정하지 말고 생성 시점에 주입

```java
public interface Parser<T> {
    T parse(String text);
}

public final class ParserRegistry {
    private final Map<Class<?>, Parser<?>> parsers = new HashMap<>();
}
```

이렇게 하면 런타임에 타입을 다시 유추하지 않아도 된다.

### 4. PECS로 읽기/쓰기 경계를 분리

```java
public void copy(List<? extends Number> src, List<? super Number> dest) {
    for (Number n : src) {
        dest.add(n);
    }
}
```

타입 소거로 복잡해질수록, 읽기/쓰기 분리를 더 명확히 해야 한다.

## 실전 시나리오

### 시나리오 1: Jackson이 `List<User>`를 잘못 복원함

```java
List<User> users = objectMapper.readValue(json, List.class);
```

이 코드는 `List<LinkedHashMap>`이 될 수 있다.
해결은 `TypeReference<List<User>>`를 넘기는 것이다.

### 시나리오 2: 제네릭 팩토리에서 캐스팅이 흩어짐

캐스팅을 여러 곳에 두면, 실패가 늦게 터지고 원인이 분산된다.
가능하면 경계에서 한 번만 복구하고, 내부는 강타입으로 유지한다.

### 시나리오 3: 공통 저장소가 타입을 잃음

`Map<String, Object>`는 편하지만, 결국 downcast 지옥이 온다.
타입별 서브맵이나 `Class<T>` 키를 함께 두는 편이 낫다.

## 코드로 보기

### Type token 구현

```java
public abstract class TypeToken<T> {
    private final Type type;

    protected TypeToken() {
        Type superType = getClass().getGenericSuperclass();
        ParameterizedType pt = (ParameterizedType) superType;
        this.type = pt.getActualTypeArguments()[0];
    }

    public Type getType() {
        return type;
    }
}
```

### 사용 예시

```java
TypeToken<List<User>> token = new TypeToken<List<User>>() {};
Type type = token.getType();
```

### 단일 타입 API

```java
public final class CacheEntry<T> {
    private final Class<T> type;
    private final T value;

    public CacheEntry(Class<T> type, T value) {
        this.type = type;
        this.value = value;
    }
}
```

## 트레이드오프

| 방법 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `Class<T>` 주입 | 단순하고 명시적이다 | 중첩 제네릭에 약하다 | 단일 DTO/서비스 |
| `TypeReference`/token | 중첩 타입까지 복구 가능 | 구현이 복잡하다 | JSON/메시지 역직렬화 |
| API에 타입 정보 명시 | 실패가 빠르다 | 호출부가 장황해진다 | 프레임워크/라이브러리 |
| raw type + cast | 빨리 만든다 | 유지보수성이 나쁘다 | 피해야 한다 |

핵심은 **런타임에 꼭 필요한 타입만 따로 보관**하는 것이다.

## 꼬리질문

> Q: Java에서 `List<String>`과 `List<Integer>`를 런타임에 구분하기 어려운 이유는 무엇인가요?
> 의도: 타입 소거의 본질 이해 여부 확인
> 핵심: 컴파일 타임 검증 후 바이트코드에서 타입 파라미터가 지워진다

> Q: `TypeReference` 같은 패턴이 왜 동작하나요?
> 의도: 제네릭 메타데이터가 어디에 남는지 확인
> 핵심: 익명 클래스의 상위 타입 정보는 `.class` 메타데이터에 보존된다

> Q: raw type 대신 우회 패턴을 써야 하는 이유는 무엇인가요?
> 의도: 타입 안정성 유지 여부 확인
> 핵심: 캐스팅 실패를 늦게 터뜨리지 않기 위해서다

## 한 줄 정리

제네릭은 런타임에 사라지므로, 타입 정보가 필요하면 `Class<T>`, `Type`, type token, PECS 같은 우회 장치를 명시적으로 써야 한다.
