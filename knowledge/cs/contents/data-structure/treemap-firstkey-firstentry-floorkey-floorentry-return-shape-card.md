# TreeMap `firstKey` vs `firstEntry`, `floorKey` vs `floorEntry` Return-Shape Card

> 한 줄 요약: `firstKey()`와 `floorKey()`는 key만 돌려주고, `firstEntry()`와 `floorEntry()`는 key+value를 함께 돌려준다. 다만 empty/경계 실패 방식은 `first` 쌍과 `floor` 쌍이 다르다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap `ceilingKey` vs `ceilingEntry` Return-Shape Twin Card](./treemap-ceilingkey-ceilingentry-return-shape-twin-card.md)
- [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](../language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: treemap firstkey firstentry beginner, treemap floorkey floorentry beginner, firstkey firstentry 차이, floorkey floorentry 차이, key entry 반환 shape, firstentry null 왜, floorkey floorentry 헷갈려요, treemap ordered map basics, treemap 처음 뭐예요, firstkey 예외 firstentry null, floorentry value 같이 반환, what is treemap entry

## 핵심 개념

처음에는 메서드 네 개를 따로 외우기보다 질문을 두 축으로 자르면 된다.

- `Key` 계열인가, `Entry` 계열인가
- `맨 앞 하나`를 읽는가, `기준 이하 가장 가까운 하나`를 읽는가

초보자용으로 줄이면 이렇게 읽으면 된다.

> `...Key()`는 key만, `...Entry()`는 key와 value를 같이 준다.

여기서 pair별 차이는 아래 한 줄이다.

- `firstKey()` vs `firstEntry()`는 "맨 앞 하나"를 읽지만 empty behavior가 다르다.
- `floorKey(x)` vs `floorEntry(x)`는 "x 이하에서 가장 가까운 하나"를 읽지만 반환 shape가 다르다.

즉 이 문서는 `strict/inclusive` 전체를 다시 설명하는 카드가 아니라, "`key만 받는가`, `entry를 받는가`, `없으면 어떻게 표현하나`"를 한 장으로 붙이는 beginner bridge다.

## 한눈에 보기

`TreeMap<start, end>` 예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
```

| 질문 | 호출 | 결과 모양 | 값 예시 |
|---|---|---|---|
| 맨 앞 시작 시각만 보고 싶다 | `firstKey()` | `K` | `09:00` |
| 맨 앞 예약의 시작/끝을 같이 보고 싶다 | `firstEntry()` | `Map.Entry<K, V>` | `09:00 -> 10:00` |
| `11:00` 이하 가장 가까운 시작 시각만 보고 싶다 | `floorKey(11:00)` | `K` | `10:30` |
| `11:00` 이하 가장 가까운 예약의 시작/끝을 같이 보고 싶다 | `floorEntry(11:00)` | `Map.Entry<K, V>` | `10:30 -> 11:00` |

핵심은 "`같은 자리`를 찾더라도 반환 shape가 다르다"는 점이다.

- `firstKey()`와 `firstEntry()`는 둘 다 맨 앞 예약을 가리킨다.
- `floorKey(11:00)`와 `floorEntry(11:00)`도 둘 다 `10:30` 줄을 가리킨다.
- 차이는 `Entry` 쪽만 그 줄의 value까지 바로 읽을 수 있다는 것이다.

## 두 쌍을 같이 보면 덜 헷갈린다

입문자가 자주 섞어 말하는 질문을 표로 다시 고정하면 이렇다.

| 헷갈리는 질문 | 먼저 떠올릴 pair | 초보자 번역 |
|---|---|---|
| `맨 앞 key만 필요해요, 아니면 value도 같이 필요해요?` | `firstKey()` vs `firstEntry()` | 맨 앞 줄 번호만 볼지, 줄 전체를 볼지 |
| `x 이하 가장 가까운 key만 필요해요, 아니면 value도 같이 필요해요?` | `floorKey(x)` vs `floorEntry(x)` | 기준 이하에서 찾은 줄 번호만 볼지, 줄 전체를 볼지 |
| `왜 firstEntry는 null인데 firstKey는 예외예요?` | `first` pair | empty map 표현 방식이 다르다 |
| `왜 floorEntry는 value까지 오는데 floorKey는 안 와요?` | `floor` pair | 둘 다 같은 위치를 찾지만 반환 shape가 다르다 |

이 네 줄만 먼저 붙이면 된다.

- `firstKey()` -> key만, empty면 예외
- `firstEntry()` -> entry, empty면 `null`
- `floorKey(x)` -> key만, 후보 없으면 `null`
- `floorEntry(x)` -> entry, 후보 없으면 `null`

## 빈 map과 경계 바깥에서 어떻게 읽나

beginner가 가장 많이 막히는 지점은 "반환 shape"와 "실패 방식"을 한꺼번에 섞는 순간이다.

| 호출 | 비어 있을 때 | 경계 예시 |
|---|---|---|
| `firstKey()` | `NoSuchElementException` | 기준값 개념 없음 |
| `firstEntry()` | `null` | 기준값 개념 없음 |
| `floorKey(08:00)` | `null` | 첫 key보다 더 이르면 왼쪽 후보가 없다 |
| `floorEntry(08:00)` | `null` | 첫 key보다 더 이르면 entry 후보도 없다 |

그래서 초보자 기준으로는 아래처럼 읽는 편이 안전하다.

- `first...`는 "맨 앞이 반드시 있나?"를 먼저 본다.
- `floor...`는 "`x` 이하 후보가 있나?"를 먼저 본다.
- 그다음에 `Key`인지 `Entry`인지 고른다.

이 순서로 읽으면 "`왜 firstEntry는 null인데 floorEntry도 null이죠?`" 같은 혼동이 줄어든다. 둘 다 `Entry`라서 같은 것이 아니라, "후보가 없으면 nullable하게 표현하는 계열"이기 때문이다.

## 실무에서 쓰는 모습

새 예약 시작 시각이 `11:00`일 때, 초보자가 처음 쓰기 쉬운 비교는 이 정도면 충분하다.

```java
LocalTime prevStart = reservations.floorKey(start);
Map.Entry<LocalTime, LocalTime> prevSlot = reservations.floorEntry(start);
```

이 두 줄은 같은 예약 줄을 가리킬 수 있다.
차이는 아래뿐이다.

- `prevStart`는 `10:30`만 받는다.
- `prevSlot`은 `10:30 -> 11:00` 전체를 받는다.

그래서 질문이 "`이전 예약이 언제 시작했지?`"면 `floorKey()`로 끝난다.
질문이 "`이전 예약이 언제 끝났지?`"까지 커지면 `floorEntry()`가 바로 필요해진다.

반대로 예약표가 비어 있을 수 있다면:

```java
Map.Entry<LocalTime, LocalTime> first = reservations.firstEntry();
if (first == null) {
    return "예약 없음";
}
```

이 흐름은 beginner에게 `firstKey()`보다 안전하게 읽힌다. `firstKey()`는 empty check를 빼먹으면 바로 예외로 이어지기 때문이다.

## 흔한 오해와 함정

- `firstEntry()`가 `firstKey()`보다 다른 위치를 찾는 것은 아니다. 같은 맨 앞 줄을 가리키고 반환 shape만 다르다.
- `floorEntry(x)`가 `floorKey(x)`보다 더 넓게 찾는 것은 아니다. 같은 후보를 찾고 value를 같이 줄 뿐이다.
- `Entry`를 받았다고 해서 항상 non-null인 것은 아니다. `firstEntry()`는 empty map에서 `null`, `floorEntry(x)`는 후보가 없으면 `null`이다.
- `firstKey()`와 `floorKey(x)`를 둘 다 key 반환이라고 해서 실패 방식까지 같다고 묶으면 안 된다. `firstKey()`는 empty에서 예외지만 `floorKey(x)`는 `null`이다.

## 더 깊이 가려면

- 오른쪽 lookup을 같은 방식으로 짝지어 보고 싶다면 [TreeMap `ceilingKey` vs `ceilingEntry` Return-Shape Twin Card](./treemap-ceilingkey-ceilingentry-return-shape-twin-card.md)
- `firstKey()`/`firstEntry()` empty behavior만 더 짧게 고정하고 싶다면 [`firstEntry()`/`lastEntry()` vs `firstKey()`/`lastKey()` Beginner Bridge](../language/java/firstentry-lastentry-vs-firstkey-lastkey-bridge.md)
- `floorKey()`/`floorEntry()`에서 strict/inclusive 감각까지 같이 붙이고 싶다면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- `floorEntry()`에서 `getValue()`를 꺼내 예약 종료 시각까지 읽는 연습을 하려면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- broader한 null/예외 경계표가 먼저 필요하면 [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)

## 한 줄 정리

`firstKey`/`floorKey`는 key만, `firstEntry`/`floorEntry`는 key+value를 주며, 초보자는 여기에 `first`는 empty 예외 가능, `floor`는 후보 없으면 `null`이라는 실패 방식까지 같이 묶어 기억하면 된다.
