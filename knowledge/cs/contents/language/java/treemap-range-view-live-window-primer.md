# `subMap()` / `headMap()` / `tailMap()` Live View Primer

> 한 줄 요약: `TreeMap`의 range API는 잘라낸 복사본이 아니라 **원본 위에 열린 실시간 창(view)** 이라서, 한쪽에서 바꾸면 다른 쪽에서도 바로 보인다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)

retrieval-anchor-keywords: language-java-00117, treemap range view live window, java treemap submap live view, java headmap tailmap not copy, treemap submap mutation reflected, backing map view beginner, treeMap subMap live view beginner, headMap tailMap same backing map, java range window primer, treemap live view caution, submap copy vs view java, new treemap from submap snapshot, beginner treemap view mutation, java navigablemap range view not snapshot, submap headmap tailmap live view primer

## 먼저 잡는 멘탈 모델

`subMap()` / `headMap()` / `tailMap()`은 "원본 map에서 일부만 떼어 낸 새 map"이 아니다.

초급자는 이렇게 기억하면 된다.

> range API는 **복사본(copy)** 이 아니라 **실시간 창(view)** 이다.

예를 들어 점수별 등급표가 이렇게 있다고 하자.

```text
10=D, 20=C, 30=B, 40=A, 50=S
```

여기서 `subMap(20, 40)`은 `{20=C, 30=B}`라는 **독립 사본**을 만드는 게 아니라,
원본에서 `20 <= key < 40` 구간만 보이는 창을 여는 것이다.

그래서 중요한 성질이 바로 따라온다.

- 원본을 바꾸면 view도 바로 바뀐다
- view를 바꾸면 원본도 바로 바뀐다

## 복사본과 무엇이 다른가

| 질문 | live view | 복사본 |
|---|---|---|
| backing data가 원본과 같은가 | 예 | 아니오 |
| 원본 수정이 반영되는가 | 예 | 아니오 |
| view 수정이 원본에 반영되는가 | 예 | 아니오 |
| 범위 밖 key를 넣을 수 있는가 | 아니오 | 복사본이면 가능 |

짧게 줄이면:

- `subMap()` / `headMap()` / `tailMap()` = 연결된 창
- `new TreeMap<>(...)` = 분리된 새 map

## 작은 mutation 예제로 바로 보기

```java
import java.util.NavigableMap;
import java.util.TreeMap;

TreeMap<Integer, String> grades = new TreeMap<>();
grades.put(10, "D");
grades.put(20, "C");
grades.put(30, "B");
grades.put(40, "A");

NavigableMap<Integer, String> window = grades.subMap(20, true, 40, false);

window.put(25, "C+");
System.out.println(window); // {20=C, 25=C+, 30=B}
System.out.println(grades); // {10=D, 20=C, 25=C+, 30=B, 40=A}

grades.remove(30);
System.out.println(window); // {20=C, 25=C+}
```

이 예제에서 꼭 봐야 할 장면은 두 군데다.

1. `window.put(25, "C+")`
- `window`만 바꿨는데 `grades`에도 `25=C+`가 생긴다

2. `grades.remove(30)`
- 이번에는 원본을 바꿨는데 `window`에서도 `30=B`가 사라진다

즉 `window`와 `grades`는 따로 노는 두 map이 아니라, 같은 데이터를 서로 다른 범위로 보고 있다.

## `headMap()` / `tailMap()`도 규칙은 같다

이 성질은 `subMap()`만의 예외가 아니다.

| API | 초급자용 해석 | live view인가 |
|---|---|---|
| `headMap(30)` | `30` 앞쪽만 보는 창 | 예 |
| `tailMap(30)` | `30`부터 뒤쪽을 보는 창 | 예 |
| `subMap(20, 40)` | `20`부터 `40` 전까지만 보는 창 | 예 |

즉 이름은 달라도 공통점은 하나다.

> `TreeMap` range API는 전부 "구간 복사"보다 "구간 view"로 읽는 편이 안전하다.

## 초급자용 주의점 3가지

### 1. 결과를 새 map으로 착각하지 말기

가장 흔한 첫 오해는 이것이다.

- "`subMap(...)` 했으니 이제 원본과 분리됐겠지"

아니다. 여전히 연결돼 있다.

원본과 완전히 분리된 결과가 필요하면 그때 복사해야 한다.

```java
TreeMap<Integer, String> snapshot = new TreeMap<>(grades.subMap(20, true, 40, false));
```

이제 `snapshot`은 독립 map이다.

### 2. view에 넣는 key도 범위 안이어야 한다

view는 "아무 key나 받는 작은 map"이 아니다. 자기 범위 규칙을 지킨다.

예를 들어 `subMap(20, true, 40, false)` view에 `40`이나 `10`을 넣으려 하면 안 된다.

초급자 기준 기억 문장:

- view는 연결돼 있지만
- **허용 범위도 같이 들고 있는 창**이다

### 3. 순회 중 수정은 여전히 조심하기

live view라고 해서 수정이 더 안전해지는 것은 아니다.

- 원본을 순회하면서 구조를 바꾸는 경우
- view를 순회하면서 구조를 바꾸는 경우

둘 다 순회/수정 규칙을 같이 생각해야 한다.
이 부분은 [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)로 이어서 보면 된다.

## 언제 view가 특히 유용한가

초급자에게는 "왜 굳이 복사본이 아니라 view지?"가 궁금할 수 있다.

이럴 때 유용하다.

- 점수 구간별 데이터만 잠깐 보고 싶을 때
- 예약 시간표에서 특정 시간대 창만 다루고 싶을 때
- 전체 ordered map은 유지한 채 일부 범위만 수정하고 싶을 때

즉 "전체 데이터 중 일부 구간만 연결된 상태로 다루기"가 목적이면 view가 잘 맞는다.

## 자주 헷갈리는 문장 바로잡기

- "`subMap()`은 map 일부를 복사한다" → 아니다. 일부 구간을 보는 live view다.
- "`view에 추가하면 원본은 안 바뀐다" → 아니다. 원본에도 반영된다.
- "`원본을 바꿔도 이미 받은 view는 그대로다" → 아니다. view도 함께 달라진다.
- "`headMap()` / `tailMap()`만 좀 다른가?" → 아니다. 둘도 같은 backing data를 본다.

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| 범위 경계 포함/제외가 헷갈린다 | [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md) |
| `floorKey`, `ceilingKey`, `higherKey`까지 같이 헷갈린다 | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
| descending view도 왜 live view인지 같이 보고 싶다 | [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md) |
| view 대신 복사 후 교체 전략이 언제 맞는지 보고 싶다 | [Collection Update Strategy Primer](./collection-update-strategy-primer.md) |

## 한 줄 정리

`TreeMap`의 `subMap()` / `headMap()` / `tailMap()`은 잘라낸 사본이 아니라 **원본 위에 열린 live view**라서, 한쪽 수정이 다른 쪽에 바로 보이고, 독립 결과가 필요할 때만 `new TreeMap<>(...)`으로 복사하면 된다.
