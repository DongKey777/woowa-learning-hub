# Navigable Range API 미니 드릴

> 한 줄 요약: `TreeSet`/`TreeMap`의 `headSet`, `tailSet`, `subSet`, `headMap`, `tailMap`, `subMap` 결과를 실행 전에 먼저 손으로 예측해 보면서 "시작 포함, 끝 제외" 감각을 고정하는 1페이지 beginner drill이다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [`descendingSet()` / `descendingMap()` View Mental Model](./descending-view-mental-model.md)

retrieval-anchor-keywords: language-java-00118, navigable range api mini drill, headset tailset subset headmap tailmap submap worksheet, treeset treemap range prediction beginner, java range view predict output before run, java headset tailset subset beginner drill, java headmap tailmap submap beginner drill, sortedset sortedmap range worksheet, navigableset navigablemap boundary exercise, 시작 포함 끝 제외 연습, 자바 headset tailset subset 결과 예측, 자바 headmap tailmap submap 결과 예측, 트리셋 트리맵 range api 워크시트, 자바 정렬 컬렉션 범위 뷰 연습

## 먼저 잡을 멘탈 모델

이번 드릴은 아래 3줄만 고정하면 된다.

- `head...`: 앞쪽만 본다, 끝 경계는 기본 제외
- `tail...`: 뒤쪽만 본다, 시작 경계는 기본 포함
- `sub...`: 시작 포함, 끝 제외가 기본이다

짧게 읽으면 이렇게 된다.

| API | 기본 범위 읽기 |
|---|---|
| `headSet(30)` / `headMap(30)` | `(-inf, 30)` |
| `tailSet(30)` / `tailMap(30)` | `[30, +inf)` |
| `subSet(20, 50)` / `subMap(20, 50)` | `[20, 50)` |

초보자 포인트는 한 줄이다.

> range API는 복사가 아니라 "정렬된 줄에서 이 구간만 보는 창"이다.

## 드릴에 쓸 정렬된 줄

`TreeSet` 쪽 줄:

```text
10   20   30   40   50
```

`TreeMap` 쪽 key 줄:

```text
10=D   20=C   30=B   40=A   50=S
```

## 드릴 1: `TreeSet` range 예측

```java
import java.util.List;
import java.util.TreeSet;

TreeSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40, 50));

System.out.println(numbers.headSet(30));
System.out.println(numbers.tailSet(30));
System.out.println(numbers.subSet(20, 50));
System.out.println(numbers.headSet(30, true));
System.out.println(numbers.tailSet(30, false));
System.out.println(numbers.subSet(20, false, 50, true));
```

실행 전에 먼저 적어 보자.

| 호출 | 내 답 |
|---|---|
| `headSet(30)` |  |
| `tailSet(30)` |  |
| `subSet(20, 50)` |  |
| `headSet(30, true)` |  |
| `tailSet(30, false)` |  |
| `subSet(20, false, 50, true)` |  |

정답:

- `headSet(30)` -> `[10, 20]`
- `tailSet(30)` -> `[30, 40, 50]`
- `subSet(20, 50)` -> `[20, 30, 40]`
- `headSet(30, true)` -> `[10, 20, 30]`
- `tailSet(30, false)` -> `[40, 50]`
- `subSet(20, false, 50, true)` -> `[30, 40, 50]`

## 드릴 2: `TreeMap` range 예측

이번에는 value가 아니라 key 구간을 본다.

```java
import java.util.TreeMap;

TreeMap<Integer, String> gradeByScore = new TreeMap<>();
gradeByScore.put(10, "D");
gradeByScore.put(20, "C");
gradeByScore.put(30, "B");
gradeByScore.put(40, "A");
gradeByScore.put(50, "S");

System.out.println(gradeByScore.headMap(30));
System.out.println(gradeByScore.tailMap(30));
System.out.println(gradeByScore.subMap(20, 50));
System.out.println(gradeByScore.headMap(30, true));
System.out.println(gradeByScore.tailMap(30, false));
System.out.println(gradeByScore.subMap(20, false, 50, true));
```

| 호출 | 내 답 |
|---|---|
| `headMap(30)` |  |
| `tailMap(30)` |  |
| `subMap(20, 50)` |  |
| `headMap(30, true)` |  |
| `tailMap(30, false)` |  |
| `subMap(20, false, 50, true)` |  |

정답:

- `headMap(30)` -> `{10=D, 20=C}`
- `tailMap(30)` -> `{30=B, 40=A, 50=S}`
- `subMap(20, 50)` -> `{20=C, 30=B, 40=A}`
- `headMap(30, true)` -> `{10=D, 20=C, 30=B}`
- `tailMap(30, false)` -> `{40=A, 50=S}`
- `subMap(20, false, 50, true)` -> `{30=B, 40=A, 50=S}`

## 10초 체크표

| 질문 | 안전한 읽기 |
|---|---|
| `head...`가 헷갈린다 | "경계값 앞쪽만, 기본은 그 값 제외" |
| `tail...`가 헷갈린다 | "경계값부터 뒤쪽, 기본은 그 값 포함" |
| `sub...`가 헷갈린다 | "왼쪽은 포함, 오른쪽은 제외" |
| `TreeMap`이 헷갈린다 | value가 아니라 key 줄을 자른다 |

## 자주 헷갈리는 포인트

- `subSet(20, 50)`과 `subMap(20, 50)`에서 `50`도 들어갈 것처럼 읽기 쉽다.
- `headSet(30)`과 `headMap(30)`은 기본형에서 `30`을 포함하지 않는다.
- `TreeMap` 결과를 읽을 때 `"B"`나 `"A"`를 기준으로 자르는 것이 아니라 `30`, `40` 같은 key를 기준으로 자른다.
- boolean overload를 보면 복잡해 보이지만, 결국 "`from` exact match를 포함할까", "`to` exact match를 포함할까"만 정하는 것이다.

## 다음 읽기

- 개념 먼저 다시 묶고 싶다면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- 경계 포함/제외 설명을 한 장으로 다시 보려면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- exact match에서 `lower`/`floor` 감각까지 이어 가려면: [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)

## 한 줄 정리

`head...`는 끝 제외, `tail...`는 시작 포함, `sub...`는 시작 포함 끝 제외라고 읽으면 `TreeSet`과 `TreeMap` range API의 절반 이상은 손으로 먼저 맞힐 수 있다.
