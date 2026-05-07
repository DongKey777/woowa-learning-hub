---
schema_version: 3
title: Collectors.toMap Duplicate Key Primer
concept_id: language/collectors-tomap-duplicate-key-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- java-stream
- duplicate-key
- map-collector
aliases:
- Collectors.toMap duplicate key
- Java stream toMap duplicate key
- duplicate key while collecting map
- toMap merge function
- groupingBy vs toMap
- 자바 Collectors.toMap 중복 키
symptoms:
- Collectors.toMap 기본형이 duplicate key를 어떻게 합칠지 몰라 IllegalStateException을 낸다는 점을 놓쳐
- List 수집과 Map 수집을 같은 모으기 작업으로 보고 key 충돌 정책을 명시하지 않아
- 중복 key를 하나의 value로 합칠지 groupingBy로 여러 value를 유지할지 결정하지 않고 collector만 바꾸려 해
intents:
- troubleshooting
- definition
- comparison
prerequisites:
- language/java-stream-lambda-basics
- language/java-collections-basics
next_docs:
- language/map-get-null-containskey-getordefault-primer
- language/map-of-copyof-unmodifiablemap-readonly-bridge
- language/java-stream-lambda-basics
linked_paths:
- contents/language/java/java-stream-lambda-basics.md
- contents/language/java/java-collections-basics.md
- contents/language/java/map-get-null-containskey-getordefault-primer.md
- contents/language/java/map-of-copyof-unmodifiablemap-readonly-bridge.md
confusable_with:
- language/java-stream-lambda-basics
- language/map-get-null-containskey-getordefault-primer
- language/map-of-copyof-unmodifiablemap-readonly-bridge
forbidden_neighbors: []
expected_queries:
- Collectors.toMap에서 duplicate key IllegalStateException이 나는 이유와 merge function을 알려줘
- Java stream toMap으로 같은 이름 key가 두 번 나오면 기본 collector가 왜 실패해?
- toMap merge function과 groupingBy를 언제 나눠 써야 해?
- 중복 key가 있을 때 첫 값 유지, 마지막 값 유지, 합치기 정책을 collector로 어떻게 표현해?
- List로 collect하는 것과 Map으로 collect하는 것이 key 충돌 때문에 어떻게 달라?
contextual_chunk_prefix: |
  이 문서는 Java Stream Collectors.toMap duplicate key 문제를 map key collision, merge function, groupingBy, IllegalStateException 관점으로 설명하는 beginner primer다.
  toMap duplicate key, stream collect map, merge function, groupingBy vs toMap, duplicate key while collecting 질문이 본 문서에 매핑된다.
---
# `Collectors.toMap(...)` Duplicate Key Primer

> 한 줄 요약: `Collectors.toMap(...)`은 "하나의 key에 하나의 value"를 만들려는 collector라서, stream 안에서 같은 key가 두 번 나오면 기본형은 실패한다. 중복을 허용해서 하나로 합칠 의도가 있으면 merge function을 직접 써야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)

retrieval-anchor-keywords: language-java-00099, collectors.tomap duplicate key beginner, java stream tomap duplicate key, java tomap illegalstateexception duplicate key, collect to map duplicate keys primer, java merge function beginner, stream tomap when use merge function, duplicate key while collecting map, java stream map collector duplicate handling, groupingby vs tomap beginner, 자바 collectors.tomap 중복 키, 자바 tomap duplicate key, 자바 stream map 수집 중복 키, 자바 merge function 언제 쓰나, 자바 groupingby tomap 차이

## 먼저 잡는 멘탈 모델

`toMap(...)`은 stream 결과를 그냥 "모으는" 것이 아니라, **사전 형태로 압축하는 과정**이다.

- `List`로 모으면 같은 값이 여러 번 있어도 큰 문제가 없다
- `Map`으로 모으면 같은 key가 두 번 나오면 충돌이 난다

초보자 기준 핵심 문장은 이것 하나면 된다.

> `Collectors.toMap(...)` 기본형은 "중복 key를 어떻게 합칠지"를 모르기 때문에 같은 key가 두 번 나오면 실패한다.

## 왜 duplicate key 예외가 나는가

예를 들어 학생 목록을 "이름 -> 점수" 맵으로 만들고 싶다고 하자.

```java
record Student(String name, int score) {}

List<Student> students = List.of(
        new Student("kim", 90),
        new Student("lee", 85),
        new Student("kim", 95)
);
```

아래 코드는 처음 보면 자연스러워 보인다.

```java
Map<String, Integer> scoreByName = students.stream()
        .collect(Collectors.toMap(
                Student::name,
                Student::score
        ));
```

그런데 이 코드는 실패할 수 있다.
이유는 stream 안에 `"kim"`이 두 번 나오기 때문이다.

`Map` 입장에서는 같은 key 자리에

- 먼저 `("kim" -> 90)`
- 나중에 `("kim" -> 95)`

둘 중 무엇을 남겨야 할지 자동으로 결정할 수 없다.
그래서 기본형 `toMap(keyMapper, valueMapper)`는 `IllegalStateException`으로 멈춘다.

## 여기서 말하는 "중복"은 값이 아니라 key다

초보자가 자주 섞는 포인트는 이것이다.

- value가 같다고 해서 문제인 것은 아니다
- **keyMapper 결과가 같으면** duplicate key다

예를 들어:

```java
List<String> emails = List.of(
        "kim@example.com",
        "kim@work.com",
        "lee@example.com"
);

Map<String, String> emailById = emails.stream()
        .collect(Collectors.toMap(
                email -> email.substring(0, 3),
                email -> email
        ));
```

여기서는 원본 문자열이 서로 달라도, key로 뽑은 앞 3글자가 같으면 충돌할 수 있다.
즉 duplicate key는 "원본 요소가 중복인가?"보다 **"map key로 변환한 결과가 중복인가?"**를 봐야 한다.

## 가장 먼저 떠올릴 3가지 선택지

| 지금 의도 | 추천 | 이유 |
|---|---|---|
| key가 정말 유일해야 한다 | 기본형 `toMap(...)` | 중복이 나오면 바로 실패해서 데이터 문제를 빨리 발견한다 |
| 같은 key를 하나로 합쳐도 된다 | `toMap(..., mergeFunction)` | 충돌 시 어떤 값을 남길지 직접 정할 수 있다 |
| 같은 key 아래 여러 값을 모으고 싶다 | `groupingBy(...)` | 애초에 "하나의 key에 여러 값" 구조가 목적이다 |

중요한 판단 기준은 "중복이 버그인가, 정상 데이터인가"다.

## merge function은 "충돌 해결 규칙"이다

중복 key가 정상일 수 있고, 그럴 때 하나만 남기는 정책이 필요하면 merge function을 쓴다.

예를 들어 "같은 이름이 나오면 마지막 점수를 남긴다"는 규칙이라면:

```java
Map<String, Integer> scoreByName = students.stream()
        .collect(Collectors.toMap(
                Student::name,
                Student::score,
                (oldValue, newValue) -> newValue
        ));
```

이제 `"kim"`이 두 번 나와도 실패하지 않고, 마지막 값 `95`가 남는다.

반대로 "처음 값 유지" 정책이면:

```java
Map<String, Integer> scoreByName = students.stream()
        .collect(Collectors.toMap(
                Student::name,
                Student::score,
                (oldValue, newValue) -> oldValue
        ));
```

이 코드는 `"kim"`에 대해 `90`을 유지한다.

초보자 기준으로 merge function은 이렇게 읽으면 된다.

> `(oldValue, newValue) -> ...` 는 "같은 key가 다시 나오면 둘 중 무엇을 남길까?"를 적는 자리다.

## "합친다"가 꼭 하나를 버린다는 뜻은 아니다

merge function은 둘 중 하나를 선택하는 데만 쓰는 것이 아니다.
두 값을 합쳐 새 값을 만들 수도 있다.

예를 들어 같은 상품의 주문 수량을 합산하려면:

```java
record Order(String product, int quantity) {}

Map<String, Integer> totalQuantityByProduct = orders.stream()
        .collect(Collectors.toMap(
                Order::product,
                Order::quantity,
                Integer::sum
        ));
```

이 코드는 같은 상품 key가 다시 나오면 수량을 더한다.

즉 merge function은 다음 셋 중 하나라고 생각하면 쉽다.

- 이전 값 유지
- 새 값으로 덮어쓰기
- 둘을 합쳐 새 값 만들기

## `toMap`과 `groupingBy`를 헷갈리지 않기

초보자가 자주 하는 실수는 "중복이 있으니 merge function으로 억지로 하나만 남기는" 것이다.
그런데 실제 요구사항이 "같은 key 아래 전부 모아 보기"라면 `groupingBy(...)` 쪽이 더 자연스럽다.

```java
Map<String, List<Student>> studentsByName = students.stream()
        .collect(Collectors.groupingBy(Student::name));
```

이건 `"kim"` 아래에 학생 여러 명이 그대로 들어간다.

| 질문 | 더 자연스러운 선택 |
|---|---|
| 같은 key에서 최종 값 하나만 필요하다 | `toMap(..., mergeFunction)` |
| 같은 key에 속한 요소들을 전부 보고 싶다 | `groupingBy(...)` |

## 초보자가 자주 헷갈리는 지점

- `duplicate key`는 value 중복이 아니라 key 중복이다
- 원본 stream 요소가 서로 달라도 keyMapper 결과가 같으면 충돌한다
- 기본형 `toMap(keyMapper, valueMapper)`는 중복 key를 허용하지 않는다
- merge function을 쓰면 예외를 "숨긴다"기보다, 충돌 정책을 코드에 명시하는 것이다
- 요구사항이 "여러 개를 유지"라면 merge function보다 `groupingBy(...)`가 더 맞을 수 있다
- "마지막 값으로 덮어쓰기"는 편하지만, 데이터 손실이 괜찮은 정책인지 먼저 확인해야 한다

## 흔한 실수와 더 안전한 읽기

### "이름이 중복될 리 없으니까 괜찮다"라고 가정한다

테스트 데이터에서는 괜찮아 보여도, 실데이터에서는 같은 이름이나 같은 코드가 들어올 수 있다.
유일성이 진짜 보장되는 key인지 먼저 확인해야 한다.

### merge function을 습관적으로 `(a, b) -> b`로 쓴다

이렇게 쓰면 예외는 사라지지만, 나중 값이 조용히 덮어쓴다.
초보자에게는 "예외를 없앴다"보다 **"어떤 값을 버렸는가"**를 먼저 읽는 습관이 중요하다.

### 사실은 `Map<String, List<T>>`가 필요했는데 `toMap`으로 시작한다

같은 key 아래 여러 항목을 유지해야 하면 merge function으로 억지로 누르기보다 `groupingBy(...)`로 자료 구조부터 맞추는 편이 낫다.

## 빠른 비교 표

| 코드 | 충돌 시 동작 | 언제 쓰기 쉬운가 |
|---|---|---|
| `Collectors.toMap(k, v)` | 예외 발생 | key 유일성이 당연해야 할 때 |
| `Collectors.toMap(k, v, (oldV, newV) -> oldV)` | 첫 값 유지 | 최초 값이 대표값일 때 |
| `Collectors.toMap(k, v, (oldV, newV) -> newV)` | 마지막 값 유지 | 최신 값이 대표값일 때 |
| `Collectors.toMap(k, v, Integer::sum)` | 값 결합 | 숫자 누적처럼 합칠 규칙이 있을 때 |
| `Collectors.groupingBy(k)` | 리스트로 묶음 | 같은 key의 여러 요소를 모두 보관할 때 |

## 다음에 어디로 이어 읽으면 좋은가

| 지금 더 헷갈리는 질문 | 다음 문서 |
|---|---|
| stream pipeline 자체가 아직 낯설다 | [Java 스트림과 람다 입문](./java-stream-lambda-basics.md) |
| `Map`이 "하나의 key에 하나의 value"라는 감각부터 다시 잡고 싶다 | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| `Map` 조회와 기본값 처리가 계속 섞인다 | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) |
| 읽기 전용 맵과 복사본, wrapper 차이도 같이 헷갈린다 | [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md) |

## 한 줄 정리

`Collectors.toMap(...)` 기본형은 duplicate key를 자동으로 해결하지 않으므로, key가 유일해야 하는지 먼저 판단하고, 중복이 정상이라면 merge function이나 `groupingBy(...)`로 의도를 직접 표현하는 편이 초보자에게 가장 안전하다.
