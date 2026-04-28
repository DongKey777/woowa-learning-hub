# TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill

> 한 줄 요약: `floorKey()`/`ceilingKey()`로 양옆 시작 시각을 찾을 수 있다면, 다음 단계는 `floorEntry()`/`ceilingEntry()`에서 `value`를 꺼내 예약 종료 시각까지 바로 읽는 연습이다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)

retrieval-anchor-keywords: treemap floorentry ceilingentry value read drill, treemap reservation end time beginner, floorentry value reservation lookup, ceilingentry value next reservation end, treemap entry getvalue drill, treemap key to entry beginner, reservation gap check end time, floorentry getvalue null check, ceilingentry getvalue null check, floor key 찾았는데 종료 시각, treemap 종료 시각 읽기, ordered map reservation value read, calendar booking entry lookup, beginner treemap interval follow up, floorentry vs floorkey beginner

## 왜 key에서 entry로 한 단계 더 가나

이 문서는 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)에서 `floorKey()`/`ceilingKey()`로 "어느 시작 시각이 잡히는가"를 이미 본 다음 단계다.
네 쌍 전체를 `Key -> Entry`로 바꾸는 짧은 연결이 먼저 필요하면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)를 먼저 보고 와도 좋다.

이번에는 질문이 하나 더 붙는다.

> 시작 시각만 찾지 말고, 그 예약이 언제 끝나는지도 바로 읽을 수 있나?

그래서 key-only 버전과 entry 버전을 이렇게 나눠 보면 된다.

| 지금 필요한 것 | API | 읽는 법 |
|---|---|---|
| 시작 시각만 | `floorKey(t)`, `ceilingKey(t)` | 왼쪽/오른쪽 이웃 key |
| 시작 시각 + 종료 시각 | `floorEntry(t)`, `ceilingEntry(t)` | 왼쪽/오른쪽 이웃 entry |

초보자 기준으로는 이 차이만 먼저 붙이면 된다.

- `floorKey(11:00)` -> `10:30`
- `floorEntry(11:00)` -> `10:30 -> 11:00`

즉 `Key`는 "어느 줄인지"만 알려 주고, `Entry`는 "그 줄의 시작과 끝"을 같이 준다.

## 핵심 개념

`Entry`를 받으면 아래 두 칸을 같이 읽는다고 생각하면 된다.

- `entry.getKey()` = 예약 시작 시각
- `entry.getValue()` = 예약 종료 시각

예약 문제에서 초보자가 자주 막히는 지점은 "`floorKey`로 `10:30`을 찾았는데, 그 예약이 몇 시에 끝나는지는 또 어디서 읽지?"다.
이때 `floorEntry`/`ceilingEntry`를 쓰면 같은 질문 안에서 시작과 끝을 한 번에 붙일 수 있다.

## 한눈에 보기

예약표를 `TreeMap<start, end>`로 저장했다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

`11:00`을 기준으로 물으면:

| 호출 | 결과 | 초보자용 해석 |
|---|---|---|
| `floorKey(11:00)` | `10:30` | 왼쪽 시작 시각만 읽는다 |
| `floorEntry(11:00)` | `10:30 -> 11:00` | 왼쪽 예약의 시작과 끝을 같이 읽는다 |
| `ceilingKey(11:00)` | `13:00` | 오른쪽 시작 시각만 읽는다 |
| `ceilingEntry(11:00)` | `13:00 -> 14:00` | 오른쪽 예약의 시작과 끝을 같이 읽는다 |

즉 `Key`는 "시간표 줄 번호"만 주고, `Entry`는 "그 줄의 내용"까지 같이 준다고 보면 된다.

## 10초 코드 감각

초보자 기준으로는 긴 코드보다 아래 4줄 감각이 중요하다.

```java
Map.Entry<LocalTime, LocalTime> prev = reservations.floorEntry(requestStart);
if (prev != null) {
    LocalTime previousEnd = prev.getValue();
}
```

`floorKey()`를 먼저 읽고 다시 `map.get(...)`로 한 번 더 들어가는 대신, `floorEntry()` 하나에서 시작 시각과 종료 시각을 같이 꺼낸다고 생각하면 된다.

## 5문제 워크시트

같은 예약표를 계속 쓴다.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

### 문제 1. exact match에서 왼쪽 예약 끝 읽기

질문: `floorEntry(10:30)`의 `getValue()`는?

정답: `11:00`

왜냐하면 `floorEntry(10:30)`은 exact match인 `10:30 -> 11:00`을 돌려주기 때문이다.

### 문제 2. 두 예약 사이에서 바로 이전 예약 끝 읽기

질문: `floorEntry(11:00)`의 `getValue()`는?

정답: `11:00`

해석: `11:00`이라는 key는 없지만, 왼쪽 가장 가까운 예약은 `10:30 -> 11:00`이다.
그래서 "이 시각 직전 예약이 언제 끝나나?"를 바로 읽을 수 있다.

### 문제 3. 지금 이후 첫 예약이 언제 끝나는지 읽기

질문: `ceilingEntry(11:00)`의 `getValue()`는?

정답: `14:00`

해석: 오른쪽 첫 예약은 `13:00 -> 14:00`이다.
`ceilingKey(11:00)`만 보면 `13:00`까지만 알지만, `ceilingEntry(11:00)`를 쓰면 종료 시각까지 바로 붙는다.

### 문제 4. 빈 틈이 30분 이상인지 읽기

질문: `11:00`부터 30분 예약을 넣고 싶다. 양옆 entry를 읽으면 가능 여부를 어떻게 보나?

정답 표:

| 읽은 값 | 결과 |
|---|---|
| `floorEntry(11:00)` | `10:30 -> 11:00` |
| `ceilingEntry(11:00)` | `13:00 -> 14:00` |

판단:

- 왼쪽 예약 끝 `11:00`은 새 예약 시작 `11:00`을 넘지 않는다
- 오른쪽 예약 시작 `13:00`은 새 예약 끝 `11:30`보다 늦다

그래서 `[11:00, 11:30)`은 넣을 수 있다.

### 문제 5. `null`이면 무엇을 먼저 확인하나

질문: `ceilingEntry(17:00)`은?

정답: `null`

해석: `17:00` 오른쪽에는 예약이 없다는 뜻이다.
이때 초보자는 "오류"로 읽기보다 "`다음 예약 없음`이라는 정상 결과"로 읽는 편이 안전하다.

## key-only에서 entry 읽기로 바꾸는 미니 변환표

같은 질문을 key-only 버전과 entry 버전으로 나란히 두면 차이가 더 또렷하다.

| 초보자가 실제로 하는 질문 | key-only로 끝나는 답 | entry로 확장한 답 |
|---|---|---|
| `11:00` 직전 예약은 언제 시작했나 | `floorKey(11:00)` -> `10:30` | `floorEntry(11:00)` -> `10:30 -> 11:00` |
| `11:00` 이후 첫 예약은 언제 시작하나 | `ceilingKey(11:00)` -> `13:00` | `ceilingEntry(11:00)` -> `13:00 -> 14:00` |
| `10:30` 예약이 몇 시에 끝나나 | `floorKey(10:30)`로는 시작 시각만 안다 | `floorEntry(10:30).getValue()` -> `11:00` |

이 표에서 핵심은 "`key를 찾는 단계`와 `종료 시각까지 읽는 단계`를 분리해서 연습한다"는 점이다.

## 상세 분해

`Entry`를 처음 읽을 때는 아래 3단계로 자르면 덜 헷갈린다.

1. `entry == null`인지 먼저 본다.
2. `entry.getKey()`로 예약 시작 시각을 읽는다.
3. `entry.getValue()`로 예약 종료 시각을 읽는다.

예약 문제에서는 2번에서 끝나지 않고 3번까지 가야 충돌 검사나 gap check가 시작된다.
그래서 이 문서는 key-only 드릴 다음에 붙는 브리지 역할을 한다.

## 흔한 오해와 함정

- `floorEntry(t)`가 value 기준으로 가까운 예약을 찾는다고 느끼기 쉽다. 실제 기준은 여전히 key인 시작 시각이다.
- `ceilingEntry(t).getValue()`를 읽을 수 있다고 해서 "다음 빈 시간"이 바로 계산되는 것은 아니다. 빈 시간은 왼쪽 종료 시각과 오른쪽 시작 시각을 같이 봐야 한다.
- `entry.getValue()`를 읽기 전에 `entry == null` 확인을 빼면 경계 시각에서 바로 NPE로 이어질 수 있다.
- `floorKey(t)`를 구한 뒤 `map.get(...)`를 다시 하는 방식도 가능하지만, 초보자 기준으로는 entry 한 번에서 시작/끝을 같이 읽는 편이 사고 흐름이 덜 끊긴다.
- `value`를 읽는 단계가 붙었다고 갑자기 복잡한 자료구조로 넘어간 것은 아니다. 여전히 "양옆 이웃 예약 두 개를 읽는다"가 핵심이다.

## 실무에서 쓰는 모습

예약 생성 로직에서는 보통 이렇게 질문이 이어진다.

1. `이 시각 바로 전 예약이 있나?`
2. `있다면 그 예약은 몇 시에 끝나나?`
3. `다음 예약은 몇 시에 시작하나?`

이 흐름에서는 `floorKey`/`ceilingKey`보다 `floorEntry`/`ceilingEntry`가 더 바로 쓰인다.
시작 시각을 찾고 다시 `get(key)`를 한 번 더 하는 대신, entry 하나에서 시작과 끝을 같이 읽을 수 있기 때문이다.

## 더 깊이 가려면

- 아직 `왼쪽 key`와 `오른쪽 key`가 먼저 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `lower/floor/ceiling/higher` 네 쌍을 `Entry`로 바꿔 읽는 compact 표가 먼저 필요하면 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)
- 이웃 entry를 이용해 `subMap`, gap check, 충돌 검사까지 이어서 보고 싶으면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- `lower`/`floor`/`ceiling`/`higher` 이름 전체를 한 표로 정리하려면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 한 줄 정리

`TreeMap` 예약 문제의 다음 단계는 "`floorKey`/`ceilingKey`로 자리만 찾기"에서 "`floorEntry`/`ceilingEntry`로 종료 시각까지 같이 읽기"로 넘어가는 것이다.
