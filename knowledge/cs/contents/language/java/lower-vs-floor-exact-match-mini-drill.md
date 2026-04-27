# `lower` vs `floor` Exact Match 미니 드릴

> 한 줄 요약: `TreeSet`/`TreeMap`에서 exact match를 물었을 때 `lower`는 한 칸 왼쪽으로 가고 `floor`는 현재 자리에 멈춘다는 차이만 따로 떼어 짧게 손예측해 보는 1페이지 드릴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [Heap vs PriorityQueue vs Ordered Map Beginner Bridge](../../data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

retrieval-anchor-keywords: lower vs floor exact match drill, treemap lower floor exact key, treeset lower floor same value, navigablemap exact match worksheet, java lower floor beginner, java floor lower confusion, exact match lower floor difference, ordered map exact match drill, 자바 lower floor 차이, 자바 exact match 워크시트, 처음 배우는데 lower floor, 왜 lower는 자기 자신이 아닌가

## 먼저 잡을 mental model

이번 드릴은 이것 하나만 고정하면 된다.

- `floor(x)`: `x`와 같으면 그 자리에 멈춘다
- `lower(x)`: `x`와 같아도 그 자리는 건너뛰고 바로 앞 칸으로 간다

짧게 외우면:

> exact match에서는 `floor`는 포함, `lower`는 제외다.

## 10초 비교표

정렬된 줄이 `10   20   30   40`일 때:

| 질문 | 결과 | 한 줄 이유 |
|---|---|---|
| `floor(30)` | `30` | exact match 포함 |
| `lower(30)` | `20` | exact match 제외 |
| `floor(25)` | `20` | `25` 이하 중 가장 가까움 |
| `lower(25)` | `20` | `25`보다 작은 값 중 가장 가까움 |

초보자 포인트는 한 줄이다.

- exact match가 아닐 때는 `floor`와 `lower`가 같을 수 있다
- exact match일 때만 둘이 갈라진다

## 드릴 1: `TreeSet`

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40));

System.out.println(numbers.floor(30));
System.out.println(numbers.lower(30));
System.out.println(numbers.floor(25));
System.out.println(numbers.lower(25));
```

실행 전에 먼저 적어 보자.

| 호출 | 내 답 |
|---|---|
| `floor(30)` |  |
| `lower(30)` |  |
| `floor(25)` |  |
| `lower(25)` |  |

정답:

- `floor(30) -> 30`
- `lower(30) -> 20`
- `floor(25) -> 20`
- `lower(25) -> 20`

## 드릴 2: `TreeMap`

이번에는 key 줄만 본다.

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByMinimumScore = new TreeMap<>();
gradeByMinimumScore.put(0, "F");
gradeByMinimumScore.put(60, "D");
gradeByMinimumScore.put(70, "C");
gradeByMinimumScore.put(80, "B");
gradeByMinimumScore.put(90, "A");

System.out.println(gradeByMinimumScore.floorEntry(80));
System.out.println(gradeByMinimumScore.lowerEntry(80));
System.out.println(gradeByMinimumScore.floorEntry(87));
System.out.println(gradeByMinimumScore.lowerEntry(87));
```

| 호출 | 결과 | 읽는 법 |
|---|---|---|
| `floorEntry(80)` | `80=B` | exact match 포함 |
| `lowerEntry(80)` | `70=C` | exact match 제외 |
| `floorEntry(87)` | `80=B` | `87` 이하 중 가장 가까운 key |
| `lowerEntry(87)` | `80=B` | `87`보다 작은 key 중 가장 가까운 key |

여기서도 exact match가 아닌 `87`에서는 둘이 같아진다.

## 자주 헷갈리는 순간

- "`lower`도 아래쪽이니까 exact match면 자기 자신이겠지"라고 읽기 쉽다.
- "`floor`는 무조건 더 작은 값"이라고 외우면 `floor(30)`에서 틀리기 쉽다.
- `TreeMap`에서 value를 비교한다고 생각하면 `80=B`와 `70=C` 차이를 잘못 읽기 쉽다.

안전한 읽기 순서:

1. key 또는 원소를 comparator 줄에 놓는다.
2. exact match인지 먼저 본다.
3. exact match면 `floor`는 멈추고 `lower`는 한 칸 더 왼쪽으로 간다.

## 다음 읽기

- 전체 네 쌍을 같이 묶고 싶으면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- reverse order에서 왜 더 헷갈리는지 보려면: [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)
- range API와 같이 섞일 때 경계 감각을 고정하려면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

## 한 줄 정리

`lower`와 `floor`는 exact match가 아닌 값에서는 같게 보일 수 있지만, exact match 순간에는 `floor`만 현재 자리를 포함하고 `lower`는 바로 앞 칸으로 이동한다.
