# TreeSet Range View Mini Drill

> 한 줄 요약: `TreeSet`의 `subSet`, `headSet`, `tailSet`은 exact-match shortcut인 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음`을 `앞쪽 창 / 시작 포함 뒤쪽 창 / 가운데 창`으로 넓혀 읽으면 자연스럽게 이어지고, 이 `시작 포함, 끝 제외` 감각은 `TreeMap subMap`으로 거의 그대로 넘어간다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- [Navigable Range API 미니 드릴](../language/java/navigable-range-api-mini-drill.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: treeset range view mini drill, treeset subset headset tailset beginner, navigableset range slice basics, treeset range query 처음, treeset 범위 조회 헷갈림, subset headset tailset 뭐예요, treeset range window practice, sorted set range beginner, treeset exact match next step, exact match shortcut to range view, what is treeset subset, treeset headset tailset why, beginner treeset range drill, treeset subset treemap submap bridge, 시작 포함 끝 제외 treeset treemap

## 핵심 개념

`TreeSet` exact match 드릴에서 `lower/floor/ceiling/higher`를 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음` shortcut으로 읽었다면, 이번엔 같은 문장을 range view 쪽 표현으로만 바꿔 붙이면 된다.

- `headSet(x)`: `x` 앞쪽 창
- `tailSet(x)`: `x`부터 뒤쪽 창
- `subSet(a, b)`: `a`부터 `b` 전까지의 가운데 창

처음엔 이렇게만 잡으면 충분하다.

- `바로 이전`과 `같거나 이전`이 왼쪽을 읽는 shortcut이었다면 `headSet(x)`는 "`x` 앞쪽 전체 창"으로 이어진다.
- `같거나 다음`과 `바로 다음`이 오른쪽을 읽는 shortcut이었다면 `tailSet(x)`는 "`x`부터 뒤쪽 전체 창"으로 이어진다.
- `subSet(a, b)`는 "`a`부터 시작해서 `b` 직전에서 멈추는 가운데 창"으로 읽는다.

| exact-match shortcut | range view로 넓힌 말 |
|---|---|
| `바로 이전`, `같거나 이전` | `x` 앞쪽 창 |
| `같거나 다음`, `바로 다음` | `x`부터 뒤쪽 창 |
| 왼쪽 시작 + 오른쪽 멈춤을 같이 보기 | `a`부터 `b` 전까지 가운데 창 |

> `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음`에서 `앞쪽 창 / 뒤쪽 창 / 가운데 창`으로만 넓힌다고 생각하면 된다. beginner에게는 이 exact-match shortcut bridge가 용어 점프를 가장 적게 만든다. 기본형은 `시작 포함, 끝 제외` 쪽으로 읽는다.

이 기본형은 다음 단계에서도 거의 안 바뀐다.

| 여기서 익히는 것 | 바로 다음에 옮길 곳 | 그대로 유지되는 읽는 법 |
|---|---|---|
| `subSet(20, 50)` | `subMap(09:00, true, 12:00, false)` | 왼쪽 경계는 포함, 오른쪽 경계는 제외 |
| 값 줄에서 range slicing | key 줄에서 range slicing | 창 안에 들어오는 기준은 여전히 경계 포함 여부다 |

그래서 `TreeSet`에서 `20 이상 50 미만`이 손에 붙었다면, `TreeMap`에서도 먼저 "`09:00` 이상 `12:00` 미만인 key만 보자"로 번역하면 된다.

이 문서의 목표는 live view 성질을 깊게 파는 것이 아니라, "`30` 주변 한 칸"에서 "`20~40` 구간"으로 손추적 범위를 넓히는 것이다.

## 한눈에 보기

같은 숫자 줄을 계속 쓴다.

```text
[10, 20, 30, 40, 50]
```

| 질문 | 먼저 떠올릴 호출 | 손으로 읽는 답 |
|---|---|---|
| `30`보다 앞쪽만 보고 싶다 | `headSet(30)` | `[10, 20]` |
| `30`부터 뒤쪽만 보고 싶다 | `tailSet(30)` | `[30, 40, 50]` |
| `20` 이상 `50` 미만만 보고 싶다 | `subSet(20, 50)` | `[20, 30, 40]` |
| `30`도 앞쪽 창에 포함하고 싶다 | `headSet(30, true)` | `[10, 20, 30]` |
| `30`은 빼고 뒤쪽만 보고 싶다 | `tailSet(30, false)` | `[40, 50]` |

짧게 번역하면 이렇다.

- `headSet`: 앞쪽 range slicing
- `tailSet`: 뒤쪽 range slicing
- `subSet`: 두 경계 사이 range slicing

## 상세 분해

### 1. exact-match 이웃에서 range view로 확장하기

`lower(30)`을 `30 바로 왼쪽 한 칸`, `floor(30)`을 `30 같거나 왼쪽 한 칸`으로 읽었다면 둘 다 `headSet(30)`의 "`30` 앞쪽 창" 감각으로 이어진다.
`ceiling(30)`을 `30 자신 또는 그 오른쪽 첫 값`, `higher(30)`를 `30 바로 오른쪽 한 칸`으로 읽었다면 둘 다 `tailSet(30)`의 "`30`부터 뒤쪽 창" 감각으로 이어진다.

즉 exact-match 이웃 조회는 한 칸, range view는 같은 방향의 여러 칸이라고 보면 된다.

### 2. 기본형은 경계 하나만 먼저 기억하기

기본형 세 개는 아래처럼 외우면 초반 실수가 줄어든다.

| 호출 | 기본 읽기 |
|---|---|
| `headSet(30)` | `30` 미만 |
| `tailSet(30)` | `30` 이상 |
| `subSet(20, 50)` | `20` 이상 `50` 미만 |

`subSet`만 따로 외우기보다 `tailSet`의 시작 포함 감각과 `headSet`의 끝 제외 감각을 합친다고 생각하면 더 쉽다.

### 3. 4문항 미니 드릴

정렬된 줄:

```text
[10, 20, 30, 40, 50]
```

질문과 정답:

| 호출 | 답 | 왜 그렇게 읽나 |
|---|---|---|
| `headSet(40)` | `[10, 20, 30]` | `40` 앞쪽만, 기본은 `40` 제외 |
| `tailSet(20)` | `[20, 30, 40, 50]` | 시작 경계 `20`은 기본 포함 |
| `subSet(20, 40)` | `[20, 30]` | 왼쪽 포함, 오른쪽 제외 |
| `subSet(20, false, 40, true)` | `[30, 40]` | `20`은 빼고 `40`은 포함 |

이 정도를 손으로 먼저 맞히면 `subMap`이나 live view 문서로 넘어갈 때 부담이 훨씬 줄어든다.

### 4. simple range slicing을 코드로 보면

```java
import java.util.List;
import java.util.NavigableSet;
import java.util.TreeSet;

NavigableSet<Integer> numbers = new TreeSet<>(List.of(10, 20, 30, 40, 50));

System.out.println(numbers.headSet(30));          // [10, 20]
System.out.println(numbers.tailSet(30));          // [30, 40, 50]
System.out.println(numbers.subSet(20, 50));       // [20, 30, 40]
System.out.println(numbers.subSet(20, false, 50, true)); // [30, 40, 50]
```

핵심은 코드 문법보다, 호출을 보기 전에 먼저 "어느 창을 자르는가"를 머릿속에 그리는 것이다.

## 흔한 오해와 함정

- `subSet(20, 50)`을 보면 `50`도 들어갈 것처럼 느끼기 쉽다. 기본형의 오른쪽 경계는 제외다.
- `headSet(30)`을 "`30`까지"로 읽으면 exact match에서 틀린다. 기본형은 `30` 앞까지만이다.
- `tailSet(30)`을 "`30` 뒤"로만 읽으면 `30`이 빠질 것 같지만, 기본형은 시작 포함이다.
- range view를 보면 곧바로 live view, 구조적 수정 예외까지 같이 떠올리기 쉽다. 초급 단계에서는 먼저 "어떤 값들이 창 안에 들어오나"만 맞히는 편이 안전하다.
- `TreeSet`인데도 map처럼 key/value를 찾으려 하면 헷갈린다. 이 문서는 값 줄만 자른다.

## 실무에서 쓰는 모습

예약 시각 집합이나 점수 구간 같은 장면에서는 "`현재 시각 이전 슬롯만 보자`", "`합격권 점수대만 보자`"처럼 정확히 range slicing 질문이 나온다.

이때 초급자는 먼저 요구를 이렇게 번역하면 된다.

- 특정 값 앞쪽 전체 -> `headSet`
- 특정 값부터 뒤쪽 전체 -> `tailSet`
- 두 경계 사이 값들만 -> `subSet`

예를 들어 `TreeSet<LocalTime>`으로 예약 시작 시각만 관리한다면, 오전 슬롯만 자를 때 `headSet(12:00)`, 점심 이후만 볼 때 `tailSet(12:00, false)`처럼 바로 연결된다.

## 더 깊이 가려면

- 아직 exact match 이웃 조회가 손에 안 붙었다면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- 값을 자르는 감각을 `key -> value` 일정표로 옮기고 싶다면 [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- `TreeSet`/`TreeMap` range API를 한 장에서 같이 비교하고 싶다면 [Navigable Range API 미니 드릴](../language/java/navigable-range-api-mini-drill.md)
- 결과가 독립 복사본이 아니라 view라는 점까지 이어서 보고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 면접/시니어 질문 미리보기

1. `lower(30)`과 `headSet(30)`은 어떻게 다른가요?
   전자는 가장 가까운 한 값, 후자는 그 경계 앞쪽 전체 view다.
2. `subSet(20, 50)`에서 왜 `50`이 빠지나요?
   기본형은 왼쪽 포함, 오른쪽 제외이기 때문이다.
3. `TreeSet`만으로 충분한 순간과 `TreeMap`으로 넘어가는 순간은 언제인가요?
   값 자체의 범위만 보면 `TreeSet`, 값에 설명이나 메타데이터를 함께 읽어야 하면 `TreeMap`이다.

## 한 줄 정리

`TreeSet`의 `subSet/headSet/tailSet`은 exact-match 이웃 조회를 "한 칸"에서 "구간 창"으로 넓힌 것으로 읽으면 beginner도 simple range slicing을 손으로 먼저 맞힐 수 있다.
