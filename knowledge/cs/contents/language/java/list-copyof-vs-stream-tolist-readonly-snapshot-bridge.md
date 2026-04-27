# `List.copyOf(...)` vs `stream.toList()` 읽기 전용 스냅샷 브리지

> 한 줄 요약: 둘 다 "구조를 못 바꾸는 리스트 snapshot"을 만들 때 쓰지만, `List.copyOf(...)`는 이미 가진 컬렉션을 경계에서 복사할 때, `stream.toList()`는 stream 파이프라인 결과를 바로 받을 때 더 자연스럽다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [`List.copyOf(...)` vs `Collections.unmodifiableList(...)` vs `List.of(...)` beginner bridge](./list-copyof-listof-unmodifiablelist-beginner-bridge.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)

retrieval-anchor-keywords: list.copyof vs stream.tolist, java list copyof vs stream tolist beginner, java readonly snapshot list, java unmodifiable list snapshot, java collection boundary copyof, java stream pipeline tolist, list copyof null elements, stream tolist null elements, 처음 배우는데 list.copyof, 자바 list.copyof tolist 차이, 자바 읽기 전용 리스트 스냅샷, 자바 copyof 방어적 복사, 자바 stream tolist 결과

## 먼저 잡을 mental model

이 둘은 경쟁 관계라기보다 **출발점이 다른 같은 방향 도구**에 가깝다.

- `List.copyOf(source)`: 이미 있는 컬렉션을 읽기 전용 snapshot으로 복사한다
- `stream.toList()`: stream 파이프라인 결과를 읽기 전용 리스트로 받는다

초보자 기준으로는 먼저 이렇게 기억하면 된다.

> 둘 다 "이 리스트 구조는 나중에 `add/remove/sort` 하지 않겠다"는 뜻에 가깝다.
> 다만 **컬렉션에서 시작하면 `List.copyOf(...)`**, **stream에서 시작하면 `toList()`**가 더 자연스럽다.

## 10초 비교 표

| 코드 | 초보자용 한 줄 해석 | 언제 더 자연스러운가 |
|---|---|---|
| `List.copyOf(source)` | 기존 컬렉션을 읽기 전용 복사본으로 만든다 | 생성자, setter, 반환 경계에서 snapshot이 필요할 때 |
| `users.stream().filter(...).toList()` | stream 결과를 읽기 전용 리스트로 받는다 | filter/map/sorted 뒤 결과를 바로 리스트로 받고 싶을 때 |

둘 다 결과 리스트 구조를 수정하려 하면 예외가 날 수 있다.

## 가장 큰 구분: 입력이 다르다

### `List.copyOf(...)`는 "이미 가진 컬렉션"에서 시작한다

```java
List<String> names = new ArrayList<>();
names.add("pobi");
names.add("june");

List<String> snapshot = List.copyOf(names);
```

이 코드는 보통 이런 상황에서 나온다.

- 생성자에서 외부 리스트를 안전하게 저장하고 싶다
- getter/반환값으로 원본과 분리된 읽기 전용 리스트를 주고 싶다
- "지금 이 시점 내용"을 snapshot으로 고정하고 싶다

즉 `List.copyOf(...)`는 **방어적 복사나 경계 보호** 맥락에서 자주 등장한다.

### `stream.toList()`는 "가공 중인 흐름"에서 끝난다

```java
List<String> activeNames = users.stream()
        .filter(User::isActive)
        .map(User::name)
        .toList();
```

이 코드는 보통 이런 상황에서 나온다.

- `filter`, `map`, `sorted` 결과를 바로 받고 싶다
- 중간에 임시 `ArrayList`를 직접 만들고 싶지 않다
- stream pipeline의 끝을 "읽기 전용 결과"로 닫고 싶다

즉 `toList()`는 **stream 결과 수집** 맥락에서 읽는 것이 가장 자연스럽다.

## 둘 다 snapshot이지만, 요소까지 immutable이 되는 것은 아니다

여기서 가장 흔한 오해를 먼저 끊어야 한다.

- `List.copyOf(...)`가 읽기 전용 리스트를 만들어도, 안의 요소 객체가 mutable이면 그 요소 상태는 바뀔 수 있다
- `stream.toList()`도 마찬가지다

```java
class User {
    private String name;

    User(String name) {
        this.name = name;
    }

    public void rename(String newName) {
        this.name = newName;
    }

    public String getName() {
        return name;
    }
}

List<User> users = new ArrayList<>();
users.add(new User("pobi"));

List<User> copied = List.copyOf(users);
List<User> collected = users.stream().toList();

users.get(0).rename("jason");

System.out.println(copied.get(0).getName());    // jason
System.out.println(collected.get(0).getName()); // jason
```

바뀌지 않는 것은 **리스트 구조**다.
자동으로 불변이 되는 것은 **요소 객체 내부 상태**가 아니다.

## 원본과의 관계는 어떻게 읽으면 되나

초보자에게 필요한 감각은 이것이다.

- `List.copyOf(source)` 결과는 원본 리스트와 분리된 snapshot으로 읽는다
- `source.stream().toList()` 결과도 새 결과 리스트로 읽는다
- 둘 다 `Collections.unmodifiableList(source)`처럼 "원본 위에 씌운 창문"으로 읽으면 안 된다

짧게 비교하면:

| 코드 | 원본 구조 변경이 결과에 비치나? | 초보자 해석 |
|---|---|---|
| `List.copyOf(source)` | 아니오 | 분리된 읽기 전용 복사본 |
| `source.stream().toList()` | 아니오 | stream이 만든 새 읽기 전용 결과 |
| `Collections.unmodifiableList(source)` | 예 | 원본을 감싼 읽기 전용 뷰 |

## 언제 무엇을 고르면 덜 헷갈리나

| 지금 상황 | 더 자연스러운 선택 | 이유 |
|---|---|---|
| 생성자에서 받은 `List`를 필드에 안전하게 저장하고 싶다 | `List.copyOf(...)` | 경계에서 snapshot을 만든다는 의도가 바로 보인다 |
| 서비스에서 stream으로 가공한 결과를 반환한다 | `stream.toList()` | 파이프라인 끝에서 read-only 결과를 받는 흐름이 자연스럽다 |
| 원본 리스트를 읽기 전용으로만 보여 주고, 원본 변경은 그대로 반영해도 된다 | `Collections.unmodifiableList(...)` | snapshot이 아니라 view 목적에 맞다 |
| 결과를 나중에 수정해야 한다 | `new ArrayList<>(...)` 또는 `Collectors.toCollection(ArrayList::new)` | 읽기 전용 snapshot이 아니라 mutable 결과가 필요하다 |

## 초보자가 자주 놓치는 차이 하나

둘 다 읽기 전용 결과를 만든다는 큰 그림은 비슷하지만, 입력 데이터에 `null`이 섞일 수 있으면 동작이 달라질 수 있다.

- `List.copyOf(...)`는 `null` 요소를 허용하지 않는다
- `stream.toList()`는 stream에 흘러온 요소를 그대로 담을 수 있다

```java
List<String> raw = Arrays.asList("a", null, "b");

List<String> a = raw.stream().toList(); // 가능
List<String> b = List.copyOf(raw);      // NullPointerException
```

입문 단계에서는 이 차이를 이렇게 기억하면 충분하다.

> 외부 입력 컬렉션을 `List.copyOf(...)`로 잠글 때는 `null` 정책도 같이 확인한다.

## 헷갈리기 쉬운 문장 바로잡기

- "`toList()`는 immutable list를 만든다"
  정확히는 리스트 구조를 수정하지 못하는 read-only 결과로 이해하는 편이 안전하다.
- "`List.copyOf(...)`면 요소까지 복사된다"
  아니다. 보통 바깥 리스트 구조를 새로 받는 것이지, 가변 요소 내부까지 deep copy하는 것은 아니다.
- "`둘 다 결국 같으니 아무 데서나 아무거나 써도 된다"
  결과 성격은 비슷해도 코드가 시작되는 위치가 다르다. 컬렉션 경계에서는 `List.copyOf(...)`, stream 끝에서는 `toList()`가 읽기 쉽다.

## 한 장 결정 규칙

1. 지금 이미 `Collection`이나 `List`를 들고 있는가?
2. 아니면 `stream()` 파이프라인 안에 있는가?
3. 결과를 수정할 일은 없는가?
4. 요소 자체가 mutable이라면, "리스트를 못 바꾼다"와 "요소가 안 바뀐다"를 구분했는가?

이 질문에 답하면 대부분 바로 정리된다.

- 컬렉션 경계 snapshot이면 `List.copyOf(...)`
- stream 결과 snapshot이면 `toList()`
- mutable 결과가 필요하면 다른 선택지로 간다

## 다음에 어디로 이어 읽으면 좋은가

- `toList()`와 `Collectors.toList()` 차이까지 이어서 보고 싶다면 [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- 읽기 전용 컨테이너와 요소 불변성을 더 넓게 정리하고 싶다면 [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)
- `copyOf`와 read-only view 차이를 맵으로 먼저 다시 보고 싶다면 [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./map-of-copyof-unmodifiablemap-readonly-bridge.md)

## 한 줄 정리

`List.copyOf(...)`와 `stream.toList()`는 둘 다 읽기 전용 snapshot 쪽이지만, 전자는 기존 컬렉션을 경계에서 복사할 때, 후자는 stream 결과를 바로 닫을 때 더 자연스럽고, 둘 다 요소 객체까지 immutable로 만들어 주는 것은 아니다.
