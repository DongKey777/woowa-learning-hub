# Reservation Interval Half-Open Boundary Card

> 한 줄 요약: 예약 충돌 검사에서 `[start, end)`를 쓰면 "`끝 시각과 다음 시작 시각이 같을 때는 안 겹친다`"를 한 줄로 고정할 수 있어 `TreeMap` 이웃 검사 조건을 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [Disjoint Interval Set](./disjoint-interval-set.md)
- [Interval Greedy Patterns](../algorithm/interval-greedy-patterns.md)
- [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

retrieval-anchor-keywords: reservation half open interval, start end boundary card, reservation overlap boundary beginner, start end inclusive confusion, start end half open basics, tree map reservation boundary, booking conflict exact boundary, 예약 구간 처음, start end 왜 헷갈려요, [start end) 뭐예요, interval boundary basics, reservation end equals next start

## 핵심 개념

예약표를 beginner가 읽을 때 가장 많이 막히는 문장은 사실 복잡하지 않다.

- `10:00~10:30` 예약 뒤에 `10:30~11:00`을 넣어도 되나요?
- 끝 시각이 같으면 겹친 건가요?
- `prev.end <= start`가 왜 맞는 조건이죠?

이 문서에서는 먼저 아래 한 줄만 고정한다.

> 예약 구간을 `[start, end)`로 읽으면 `start`는 포함하고 `end`는 포함하지 않는다.

그래서 `10:00~10:30` 뒤에 `10:30~11:00`은 서로 맞닿아 있을 뿐 겹치지 않는다.
`TreeMap` 예약 충돌 검사에서 자주 보이는 `prev.end <= start`와 `end <= next.start`도 이 규칙 위에서 읽어야 맞다.

## 한눈에 보기

같은 시각 표현이라도 경계 해석이 다르면 판단이 달라진다.

| 표기 | 초보자용 읽는 법 | `10:00~10:30` 뒤에 `10:30~11:00` 가능? |
|---|---|---|
| `[start, end)` | 시작 포함, 끝 제외 | 가능 |
| `[start, end]` | 시작 포함, 끝 포함 | 불가능 |

예약 문제에서는 보통 아래처럼 생각하면 된다.

```text
[10:00, 10:30)  -> 10:00은 쓰고, 10:30은 다음 예약이 써도 된다
[10:30, 11:00)  -> 바로 이어 붙을 수 있다
```

즉 beginner 메모는 이것 하나면 충분하다.

- 반열린 구간 `[start, end)` = 끝 시각은 "이미 비워 둔 자리"

## 왜 `[start, end)`를 많이 쓰나

예약표, 캘린더, `TreeMap<start, end>` 예제에서 `[start, end)`를 많이 쓰는 이유는 경계 규칙이 단순해지기 때문이다.

| learner 질문 | `[start, end)`에서 답 | 왜 쉬워지나 |
|---|---|---|
| 끝과 다음 시작이 같으면? | 안 겹친다 | 맞닿음과 겹침이 분리된다 |
| 길이는 어떻게 계산하나? | `end - start` | 별도 `+1` 감각이 필요 없다 |
| overlap 조건은? | `prev.end <= start`, `end <= next.start` | `<=` 두 개로 읽기 쉽다 |

inclusive endpoint `[start, end]`를 쓰면 beginner가 곧바로 "`10:30`이 두 예약에 동시에 들어가나?"에서 멈춘다.
반대로 `[start, end)`는 "`끝 시각은 다음 예약이 써도 된다`"로 바로 번역된다.

## 손으로 바로 비교해 보기

기존 예약이 `[09:00, 10:00)` 하나 있다고 하자.

| 새 예약 | `[start, end)` 기준 | `[start, end]` 기준 |
|---|---|---|
| `[10:00, 10:30)` | 가능 | 불가능 |
| `[09:30, 10:00)` | 충돌 | 충돌 |
| `[08:30, 09:00)` | 가능 | 불가능 |
| `[09:59, 10:30)` | 충돌 | 충돌 |

초보자에게 중요한 포인트는 두 개다.

- 경계점 하나만 맞닿는 경우를 비충돌로 보고 싶다면 `[start, end)`가 자연스럽다.
- 회의실 예약, 룸 예약, `My Calendar` 류 문제는 이 규칙을 거의 기본값처럼 쓴다.

## TreeMap 충돌 검사 문장으로 번역하기

[TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)에서 쓰는 규칙을 경계 관점으로 다시 읽으면 아래와 같다.

```java
boolean noLeftOverlap = prev == null || !prev.getValue().isAfter(start);
boolean noRightOverlap = next == null || !end.isAfter(next.getKey());
```

이 코드는 사실 아래 두 문장의 Java 버전이다.

- 왼쪽 예약 끝이 새 시작보다 늦지 않다. `prev.end <= start`
- 새 끝이 오른쪽 예약 시작보다 늦지 않다. `end <= next.start`

왜 `<=`가 되냐고 묻는다면 답은 간단하다.

- `[start, end)`에서는 끝 시각이 다음 시작과 같아도 괜찮기 때문이다.

예를 들어 기존 예약이 `[09:00, 10:00)`이고 새 예약이 `[10:00, 10:30)`이면:

- `prev.end <= start` -> `10:00 <= 10:00` 참
- 두 예약은 맞닿지만 겹치지 않는다

## 흔한 오해와 함정

- 화면에 `10:00~10:30`처럼 보인다고 자동으로 inclusive endpoint는 아니다. 표시 형식과 내부 interval 규칙은 따로 봐야 한다.
- `prev.end < start`로 외우면 맞닿는 예약까지 막아 버린다. 반열린 구간 기준이라면 `<=`가 맞다.
- `[start, end)`와 `[start, end]` 예시를 같은 노트에서 섞어 쓰면 조건식이 바로 흔들린다.
- DB 쿼리, UI 문구, 테스트 픽스처가 서로 다른 규칙을 쓰면 "`분명 안 겹치는데 실패해요`" 같은 증상이 나온다. 이때 먼저 interval 규칙을 한 줄로 통일해야 한다.

## 더 깊이 가려면

- `TreeMap` 양옆 예약 자체를 찾는 단계가 먼저 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- 실제 `floorEntry(start)` / `ceilingEntry(start)`로 충돌 검사하는 흐름은 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- interval insert와 merge를 더 일반화한 구조는 [Disjoint Interval Set](./disjoint-interval-set.md)
- 메모리 안 충돌 검사와 DB 저장 시점 보장을 구분하려면 [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

## 한 줄 정리

예약 충돌 검사에서 `[start, end)`를 쓰면 "`끝 시각 = 다음 시작 시각`은 허용"으로 고정되고, 그래서 `prev.end <= start`와 `end <= next.start`를 자신 있게 읽을 수 있다.
