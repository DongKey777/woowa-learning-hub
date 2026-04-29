# TreeMap Gap Detection Mini Drill

> 한 줄 요약: `floorEntry(start)`의 종료 시각과 `ceilingEntry(start)`의 시작 시각을 붙여 읽으면 "`30분 빈 시간 있나?`"를 예약표 전체 순회 없이 바로 판단할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md)
- [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

retrieval-anchor-keywords: treemap gap detection mini drill, 30분 빈 시간 있나, free slot length check, floorentry ceilingentry gap check, reservation gap beginner, room reservation empty slot, treemap 빈 시간 계산, reservation gap 뭐예요, gap length 처음 배우기, booking free slot basics, ordered map gap check, between reservations how many minutes, floorentry ceilingentry 언제 써요

## 핵심 개념

이 문서의 질문은 overlap보다 한 단계 더 구체적이다.

> "`지금 이 시각부터 30분 빈 시간 있나?`"

`TreeMap<start, end>` 예약표가 이미 비겹침 상태라면 먼저 양옆 예약 두 개만 읽는다.

- `prev = floorEntry(start)` -> 시작 시각 기준 왼쪽 예약
- `next = ceilingEntry(start)` -> 시작 시각 기준 오른쪽 예약

그다음 초보자용 질문은 두 줄뿐이다.

- 왼쪽 예약은 이미 끝났나
- 오른쪽 예약이 오기 전까지 원하는 길이가 남았나

즉 gap check는 "`양옆 이웃 찾기` + `길이 계산`"으로 읽으면 된다.

## 한눈에 보기

예약표가 아래처럼 있다고 하자.

```text
09:00 -> 10:00
10:30 -> 11:00
13:00 -> 14:00
15:30 -> 16:00
```

`11:00`부터 시작할 때는 이렇게 읽는다.

| 읽은 값 | 결과 | 초보자용 해석 |
|---|---|---|
| `floorEntry(11:00)` | `10:30 -> 11:00` | 왼쪽 예약은 `11:00`에 끝난다 |
| `ceilingEntry(11:00)` | `13:00 -> 14:00` | 오른쪽 예약은 `13:00`에 시작한다 |
| 사이 길이 | `13:00 - 11:00 = 120분` | 30분도 가능, 60분도 가능 |

짧게 외우면 이렇다.

- gap 시작점 = `max(start, prev.end)`
- gap 끝점 = `next.start`
- `gap 끝점 - gap 시작점 >= 원하는 길이`면 가능

## 4문항 미니 드릴

같은 예약표를 계속 쓴다.

### 문제 1. `11:00`부터 30분 빈 시간 있나

`prev.end = 11:00`, `next.start = 13:00`이므로 빈 구간은 `[11:00, 13:00)`다.
길이는 120분이라서 가능하다.

### 문제 2. `10:00`부터 30분 빈 시간 있나

`prev.end = 10:00`, `next.start = 10:30`이므로 빈 구간은 `[10:00, 10:30)`다.
길이는 정확히 30분이므로 가능하다.

### 문제 3. `12:45`부터 30분 빈 시간 있나

`prev.end = 11:00`, `next.start = 13:00`이다.
실제로 쓸 수 있는 빈 구간은 `[12:45, 13:00)`뿐이라 15분밖에 없다.
그래서 불가능하다.

### 문제 4. `15:45`부터 30분 빈 시간 있나

`floorEntry(15:45)`는 `15:30 -> 16:00`이다.
왼쪽 예약이 아직 안 끝났으므로 시작점 `15:45` 자체가 이미 막혀 있다.
길이 계산 전에 충돌로 탈락한다.

## 길이 계산을 한 줄로 번역하기

빈 시간 길이 계산은 "왼쪽 예약 끝부터 오른쪽 예약 시작까지"가 기본이다.
다만 요청 시작 시각이 그보다 더 늦으면 그 시각부터 다시 잰다.

| 상황 | 빈 시간 시작 | 빈 시간 끝 | 길이 판정 |
|---|---|---|---|
| 왼쪽 예약 없음 | `start` | `next.start` 또는 하루 끝 | `끝 - start` |
| 왼쪽 예약이 `start` 전에 끝남 | `start` | `next.start` | `next.start - start` |
| 왼쪽 예약이 `start` 뒤에 끝남 | 사용 불가 | 사용 불가 | 바로 충돌 |

예약표 질문으로 바꾸면 이렇게 읽으면 된다.

- "`30분 빈 시간 있나?`" -> 길이가 30분 이상인가
- "`정확히 30분만 비나?`" -> 길이가 30분인가
- "`최소 1시간 비나?`" -> 길이가 60분 이상인가

## 흔한 오해와 함정

- `next.start - prev.end`만 계산하면 항상 맞는다고 생각하기 쉽다. 요청 시작 시각이 `prev.end`보다 늦을 수 있으니 실제 시작점은 `max(start, prev.end)`로 읽어야 한다.
- `ceilingEntry(start)`의 `getValue()`까지 읽어야 gap 길이가 나온다고 느끼기 쉽다. gap 끝은 보통 오른쪽 예약의 시작 시각 `next.getKey()`다.
- `floorEntry(start)`가 있다는 사실만으로 곧바로 충돌은 아니다. `prev.end <= start`면 이미 끝난 예약일 수 있다.
- 경계가 맞닿는 경우를 막으면 안 된다. 이 문서는 `[start, end)` 기준이라 `10:00`에 끝나고 `10:00`에 시작하는 것은 허용한다.

## 실무에서 쓰는 모습

회의실 예약 API에서 자주 나오는 질문은 아래처럼 짧다.

- `11시부터 30분 비었나?`
- `지금 이후 가장 가까운 1시간 슬롯 있나?`

코드도 보통 이 흐름이다.

```java
Map.Entry<LocalTime, LocalTime> prev = bookings.floorEntry(start);
Map.Entry<LocalTime, LocalTime> next = bookings.ceilingEntry(start);

boolean leftClear = prev == null || !prev.getValue().isAfter(start);
LocalTime gapEnd = next == null ? closingTime : next.getKey();
boolean longEnough = Duration.between(start, gapEnd).toMinutes() >= 30;
```

입문자 기준으로는 "`충돌이 없나`를 먼저 보고, 그다음 `얼마나 비었나`를 잰다" 순서만 고정하면 충분하다.

## 더 깊이 가려면

- `entry.getValue()`로 종료 시각 읽기 자체가 아직 낯설면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- overlap 판정과 gap 판정을 한 장에서 같이 보고 싶다면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- 시간창 안에 시작한 예약 목록부터 보고 싶다면 [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- 반열린 구간 경계가 헷갈리면 [Reservation Interval Half-Open Boundary Card](./reservation-interval-half-open-boundary-card.md)
- 메모리 안 gap check와 DB 저장 시점 보장을 분리해서 보고 싶다면 [MySQL Overlap Fallback Beginner Bridge](../database/mysql-overlap-fallback-beginner-bridge.md)

## 한 줄 정리

`TreeMap` gap check 입문은 `floorEntry(start)`의 종료 시각과 `ceilingEntry(start)`의 시작 시각 사이 길이가 원하는 분 수 이상인지 읽는 연습으로 시작하면 된다.
