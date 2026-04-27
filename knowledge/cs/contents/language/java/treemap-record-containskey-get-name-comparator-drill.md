# TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator

> 한 줄 요약: `TreeMap`이 `record` key를 찾을 때는 `equals()`가 아니라 comparator의 `compare(...) == 0` 기준으로 같은 key 자리를 찾기 때문에, `id`가 달라도 `name`만 같으면 `containsKey()`와 `get()`이 예상과 다르게 동작할 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)

> retrieval-anchor-keywords: treemap record containskey get drill, treemap record comparator lookup worksheet, record key name only comparator containsKey get, java treemap containsKey get surprise record, compare zero same key lookup drill, record equals comparator mismatch lookup, treemap get different record same name, treemap containskey different id same name, java beginner treemap record key worksheet, 자바 treemap record 조회 워크시트, 자바 containsKey get comparator surprise, 자바 record key name comparator 조회, 자바 treemap 같은 key 자리 compare zero

## 먼저 잡을 mental model

이번 문서는 저장보다 조회만 본다.

- `record`의 자동 `equals()`는 component 전체를 본다
- 하지만 `TreeMap` 조회는 comparator가 만든 길을 따라간다
- 그래서 `TreeMap`에서는 "`equals()`가 같은가?"보다 "`compare(...) == 0`인가?"가 더 직접적인 조회 기준이 된다

초보자용으로 줄이면 이 문장 하나면 된다.

> `TreeMap.containsKey()`와 `get()`은 "같은 객체인가?"보다 "comparator가 같은 key 자리라고 보나?"를 먼저 본다.

## 15초 비교표

`record Student(long id, String name)`와 `Comparator.comparing(Student::name)`를 같이 쓸 때:

| 조회 키 | record `equals()` 관점 | `TreeMap` 조회 관점 |
|---|---|---|
| `new Student(1, "Mina")` | 원래 key와 같을 수 있음 | 찾음 |
| `new Student(99, "Mina")` | 원래 key와 다름 | 그래도 찾을 수 있음 |
| `new Student(1, "Ria")` | 원래 key와 다름 | 못 찾음 |

핵심은 `TreeMap`이 `id`가 아니라 `name`만 보고 길을 찾는다는 점이다.

## 드릴 코드

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

record Student(long id, String name) {}

Comparator<Student> byNameOnly =
        Comparator.comparing(Student::name);

Map<Student, String> seat = new TreeMap<>(byNameOnly);
seat.put(new Student(1L, "Mina"), "front");

System.out.println(seat.containsKey(new Student(1L, "Mina")));
System.out.println(seat.containsKey(new Student(99L, "Mina")));
System.out.println(seat.containsKey(new Student(1L, "Ria")));

System.out.println(seat.get(new Student(1L, "Mina")));
System.out.println(seat.get(new Student(99L, "Mina")));
System.out.println(seat.get(new Student(1L, "Ria")));
```

## 실행 전 워크시트

| 질문 | 내 답 |
|---|---|
| `containsKey(new Student(1L, "Mina"))` |  |
| `containsKey(new Student(99L, "Mina"))` |  |
| `containsKey(new Student(1L, "Ria"))` |  |
| `get(new Student(1L, "Mina"))` |  |
| `get(new Student(99L, "Mina"))` |  |
| `get(new Student(1L, "Ria"))` |  |

## 정답

- `containsKey(new Student(1L, "Mina"))` -> `true`
- `containsKey(new Student(99L, "Mina"))` -> `true`
- `containsKey(new Student(1L, "Ria"))` -> `false`
- `get(new Student(1L, "Mina"))` -> `"front"`
- `get(new Student(99L, "Mina"))` -> `"front"`
- `get(new Student(1L, "Ria"))` -> `null`

## 왜 이렇게 나오나

### 1. `record` 기준으로는 다른 객체다

- `Student(1, "Mina")`와 `Student(99, "Mina")`는 `id`가 다르다
- 그래서 record의 자동 `equals()` 기준으로는 서로 다르다

여기까지만 보면 초보자는 `containsKey(...)`가 `false`일 거라고 예상하기 쉽다.

### 2. 그런데 `TreeMap`은 comparator로 조회한다

- 지금 comparator는 `name`만 본다
- `"Mina"`와 `"Mina"`를 비교하면 `compare(...) == 0`이다
- `TreeMap`은 이 둘을 같은 key 자리로 본다

그래서 `new Student(99L, "Mina")`로도 조회가 된다.

### 3. 이름이 달라지면 길이 달라진다

- `"Mina"`와 `"Ria"`는 `compare(...) == 0`이 아니다
- 그래서 `TreeMap`은 같은 key 자리가 아니라고 판단한다
- 그 결과 `containsKey(...)`는 `false`, `get(...)`은 `null`이 된다

## 자주 하는 오해

- "`record`니까 조회도 자동 `equals()`로 하겠지"
  - `HashMap` 계열에서는 더 가깝지만, `TreeMap`은 comparator가 더 직접적이다.
- "`containsKey(new Student(99, \"Mina\")) == true`면 record가 이름만 비교하나 보다"
  - 아니다. record `equals()`는 그대로 전체 component를 본다. 조회 기준만 comparator가 바꾼 것이다.
- "`get(...)`이 값을 주면 원래 key 객체와 완전히 같은 것이다"
  - 아니다. 여기서는 "같은 key 자리로 판정됐다"가 더 정확하다.

## 20초 체크리스트

- `TreeMap` key 조회 기준이 `equals()`인지 `Comparator`인지 먼저 적었나?
- comparator가 `name`만 보는지, `id`까지 보는지 확인했나?
- "같은 객체"와 "같은 key 자리"를 같은 말로 섞어 쓰고 있지 않나?

서로 다른 학생을 모두 따로 구분하고 싶다면:

```java
Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);
```

이렇게 tie-breaker를 넣어 `compare(...) == 0`이 더 쉽게 나오지 않게 해야 한다.

## 다음 읽기

- 저장까지 같이 보고 싶으면: [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
- `compare == 0`이 왜 같은 key 자리인지 다시 잡고 싶으면: [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- 조회 실패 디버깅 순서를 더 넓게 보려면: [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)

## 한 줄 정리

`TreeMap`에서 `record` key 조회가 헷갈릴 때는 "`equals()`가 같은가?"보다 "이 comparator가 `compare(...) == 0`으로 같은 key 자리를 만들었는가?"를 먼저 보면 된다.
