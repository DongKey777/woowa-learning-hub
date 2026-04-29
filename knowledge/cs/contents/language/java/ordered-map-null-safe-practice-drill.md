# Ordered Map Null-Safe Practice Drill

> 한 줄 요약: `TreeMap`/`NavigableMap`에서 `floorEntry`/`ceilingEntry`/`lowerEntry`/`higherEntry`가 언제 `null`이 되고 언제 non-null이 되는지, 왼쪽 경계와 오른쪽 경계를 분리해서 먼저 손으로 예측해 보는 초급 연습 카드다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

retrieval-anchor-keywords: ordered map null safe practice drill, treemap null safe drill, navigablemap null vs non null boundary examples, floorentry null when, ceilingentry null when, higherentry null when, ceilingentry null right boundary, higherentry null max key, ordered map boundary card beginner, boundary null vs null key treemap, floorentry null does not mean null key, 왜 ceilingentry null 이 나와요, 왜 higherentry null 이 나와요, 처음 treemap null 헷갈림, what is boundary null in ordered map

## 먼저 잡을 mental model

이 카드에서는 복잡한 정렬 이론보다 이것 하나만 기억하면 된다.

> ordered map lookup은 "정렬된 key 줄에서 왼쪽이나 오른쪽 이웃이 실제로 있으면 non-null, 없으면 null"이다.

여기서 나오는 `null`은 "경계 밖이라 이웃이 없음"이라는 **조회 결과**다.
`TreeMap`이 `null` key를 보통 막는 규칙과는 다른 이야기이므로, 그 감각이 섞이면 먼저 [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)를 한 번 같이 보는 편이 안전하다.

짧게 번역하면:

- `floorEntry(x)`: `x`와 같거나 왼쪽에 이웃이 있나?
- `ceilingEntry(x)`: `x`와 같거나 오른쪽에 이웃이 있나?
- `lowerEntry(x)`: `x`보다 strict하게 왼쪽 이웃이 있나?
- `higherEntry(x)`: `x`보다 strict하게 오른쪽 이웃이 있나?

## 연습에 쓸 key 줄

```java
TreeMap<Integer, String> gradeByMinimumScore = new TreeMap<>();
gradeByMinimumScore.put(60, "D");
gradeByMinimumScore.put(70, "C");
gradeByMinimumScore.put(80, "B");
gradeByMinimumScore.put(90, "A");
```

정렬된 key 줄은 이렇게 읽으면 된다.

```text
60   70   80   90
```

아래 4문항은 정답을 보기 전에 먼저 `null` / `non-null`만 예측해 보자.

## 경계 예제 1: 빈 map

```java
TreeMap<Integer, String> empty = new TreeMap<>();
System.out.println(empty.ceilingEntry(80));
```

| 호출 | 내 예측 |
|---|---|
| `empty.ceilingEntry(80)` |  |

정답:

- `empty.ceilingEntry(80)` -> `null`

이유:

- 오른쪽 이웃을 찾으려 해도 map 자체가 비어 있다
- 그래서 줄 위에 후보가 하나도 없어서 `null`이다

## 경계 예제 2: 첫 key보다 더 왼쪽

```java
System.out.println(gradeByMinimumScore.floorEntry(59));
```

| 호출 | 내 예측 |
|---|---|
| `gradeByMinimumScore.floorEntry(59)` |  |

정답:

- `gradeByMinimumScore.floorEntry(59)` -> `null`

이유:

- `floorEntry`는 같거나 왼쪽 이웃을 찾는다
- 그런데 `59`의 왼쪽에는 key가 없다
- 첫 key `60`은 오른쪽에 있으므로 후보가 아니다

## 경계 예제 3: key 사이 값

```java
System.out.println(gradeByMinimumScore.ceilingEntry(87));
System.out.println(gradeByMinimumScore.floorEntry(87));
```

| 호출 | 내 예측 |
|---|---|
| `gradeByMinimumScore.ceilingEntry(87)` |  |
| `gradeByMinimumScore.floorEntry(87)` |  |

정답:

- `gradeByMinimumScore.ceilingEntry(87)` -> `90=A`
- `gradeByMinimumScore.floorEntry(87)` -> `80=B`

이유:

- `87`은 `80`과 `90` 사이에 있다
- 왼쪽 이웃은 `80`, 오른쪽 이웃은 `90`이므로 둘 다 non-null이다
- exact match가 아니어도 양쪽에 이웃이 있으면 `floorEntry`와 `ceilingEntry`가 모두 값을 줄 수 있다

## 경계 예제 4: 마지막 key보다 더 오른쪽

```java
System.out.println(gradeByMinimumScore.ceilingEntry(95));
System.out.println(gradeByMinimumScore.higherEntry(90));
```

| 호출 | 내 예측 |
|---|---|
| `gradeByMinimumScore.ceilingEntry(95)` |  |
| `gradeByMinimumScore.higherEntry(90)` |  |

정답:

- `gradeByMinimumScore.ceilingEntry(95)` -> `null`
- `gradeByMinimumScore.higherEntry(90)` -> `null`

이유:

- `95`의 오른쪽에는 key가 없다
- `higherEntry(90)`도 `90` 자신은 제외하고 더 오른쪽만 찾는데, `90`이 마지막 key라 후보가 없다
- 여기서의 `null`도 `null` key 허용이나 `null` value 저장과는 무관하고, 단지 **오른쪽 경계 밖이라 이웃이 없음**을 뜻한다

## 10초 정리표

| 경계 상황 | 대표 호출 | 결과 감각 |
|---|---|---|
| map이 비어 있음 | `ceilingEntry(x)` | 항상 `null` |
| query가 첫 key보다 작음 | `floorEntry(x)` | 왼쪽 이웃이 없어서 `null` |
| query가 key 사이에 있음 | `floorEntry(x)`, `ceilingEntry(x)` | 양옆 이웃이 있으면 둘 다 non-null 가능 |
| query가 마지막 key보다 큼 | `ceilingEntry(x)` | 오른쪽 이웃이 없어서 `null` |
| query가 마지막 key와 exact match | `higherEntry(x)` | strict하게 오른쪽만 보므로 `null` 가능 |

## 자주 헷갈리는 지점

- `floorEntry`가 "`작은 값 하나는 주겠지`"라고 느껴져도, 첫 key보다 더 왼쪽이면 바로 `null`이다.
- `ceilingEntry`가 non-null이라고 해서 exact match라는 뜻은 아니다. 오른쪽 이웃만 있어도 non-null이다.
- `ceilingEntry(95) == null`이나 `higherEntry(90) == null`은 "`TreeMap`이 `null`을 저장했다"는 뜻이 아니다.
  오른쪽 경계 밖이라 더 볼 key가 없다는 boundary result다.
- 여기서 `null`이 나왔다고 해서 "`TreeMap`은 `null` key를 허용하나?"로 점프하면 안 된다.
  이 카드의 `null`은 "반환 결과가 비었다"는 뜻이고, `null` key 규칙은 "애초에 어떤 key를 map에 넣을 수 있나?" 문제다.
- `get(key)`의 `null`과 `floorEntry`의 `null`은 이유가 다르다.
  `get(key)`는 "없는 key"와 "null value"가 섞일 수 있지만, `floorEntry`/`ceilingEntry`의 `null`은 "그 방향 이웃이 없음"으로 읽는 편이 안전하다.

## 다음 읽기

- "`boundary null`과 `null` key 규칙이 자꾸 섞인다"면: [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- 네 메서드 전체 그림을 다시 고정하려면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- exact match에서 `lower`와 `floor` 차이만 더 짧게 보고 싶다면: [`lower` vs `floor` Exact Match 미니 드릴](./lower-vs-floor-exact-match-mini-drill.md)
- exact match에서 `ceiling`과 `higher` 차이만 더 짧게 보고 싶다면: [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- range 경계와 연결해서 읽고 싶다면: [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)

## 한 줄 정리

ordered map에서 `null` 안전하게 읽으려면 "왼쪽/오른쪽 이웃이 실제로 존재하나?"만 먼저 보고, 이웃이 없으면 `null`, 있으면 non-null이라고 판단하되 이 결과를 `null` key 규칙과 섞지 않는 것이 핵심이다.
