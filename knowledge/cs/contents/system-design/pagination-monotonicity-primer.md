# Pagination Monotonicity Primer

> 한 줄 요약: 페이지네이션에서 `min-version` floor는 "이미 본 row가 뒤로 가지 않게" 쓰는 장치이지, 현재 페이지 후보를 무작정 필터링해 page boundary를 깨뜨리는 장치가 아니다.

retrieval-anchor-keywords: pagination monotonicity primer, pagination min-version floor, pagination min version floor, cursor pagination monotonic reads, page to page monotonicity, list pagination stale row reject, pagination hidden rows bug, pagination ordering with min-version, seek pagination min-version, page boundary monotonic guard, stable cursor with freshness floor, stale row suppress pagination, pagination floor candidate reject, page shrink because floor, offset pagination monotonicity, replica lag pagination list, cache pagination monotonic guard, beginner pagination consistency, page to page ordering floor, seen row version floor pagination, entity floor not page filter, pagination overlay patch suppress, system-design-00069

**난이도: 🟢 Beginner**

관련 문서:

- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Search Hit Overlay Pattern](./search-hit-overlay-pattern.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)

---

## 핵심 개념

먼저 용어보다 화면 경험으로 생각하자.

> 1페이지에서 본 주문이 2페이지나 새로고침 후에 더 오래된 상태로 다시 나오면 안 된다.
> 그렇다고 오래된 후보를 그냥 빼 버려서 row가 사라진 것처럼 보여도 안 된다.

페이지네이션에서 `min-version` floor를 다룰 때 핵심은 두 줄이다.

- 정렬과 cursor 경계는 **안정적으로 유지**한다.
- floor는 "이 후보를 그대로 채택해도 되나"를 판단하는 **accept rule**로 쓴다.

즉 floor는 정렬 규칙을 대신하지 않는다.
정렬은 `created_at desc, id desc` 같은 stable order가 담당하고, floor는 그 위에서 stale candidate를 reject/patch/suppress하는 얇은 보호층이다.

---

## 초보자 mental model: cursor는 책갈피, floor는 하한선

- cursor는 "다음 페이지를 어디서 이어 읽을까"를 기억하는 책갈피다.
- `min-version` floor는 "이미 본 row는 이 버전 아래로 내려가지 마"라는 하한선이다.
- 둘을 섞어 "floor보다 낮은 row는 다 건너뛰자"로 구현하면 ordering과 page size가 같이 깨진다.

예를 들어 1페이지에서 아래를 봤다고 하자.

```text
page 1
- order:110 version=8
- order:109 version=12
- order:108 version=5

next_cursor = after(created_at=10:00:01, id=108)
floors
- min_version(order:110)=8
- min_version(order:109)=12
- min_version(order:108)=5
```

다음 요청의 관심사는 두 개다.

- `next_cursor` 뒤에서 이어 읽기
- 이미 본 `110, 109, 108`이 더 낮은 version으로 다시 나오지 않기

이 둘은 다른 문제다.

## 왜 "floor로 필터링"하면 숨은 row가 생기나

가장 흔한 오답은 이렇다.

1. DB/cache/search에서 page size만큼 후보를 읽는다.
2. `candidate.version < floor`인 row를 버린다.
3. page가 비면 "원래 결과가 적은가 보다"라고 생각한다.

이렇게 하면 두 가지가 깨진다.

| 깨지는 점 | 왜 생기나 | 사용자에게 보이는 증상 |
|---|---|---|
| page shrink | stale candidate를 버렸는데 대체 row를 더 읽지 않는다 | 20개 페이지가 갑자기 17개만 보인다 |
| hidden rows / cursor skip | 버려진 row도 cursor는 이미 지나갔다 | 다음 페이지에서 채워졌어야 할 row가 영영 안 나온다 |

즉 floor를 "filter"로만 다루면 monotonicity는 지킬 수 있어도 pagination correctness가 깨진다.

---

## 안전한 기본 원칙 4개

| 원칙 | 의미 | 초보자용 이유 |
|---|---|---|
| stable seek order 먼저 | `created_at desc, id desc` 같은 안정적 정렬을 먼저 고정 | 같은 row를 page 간에 예측 가능하게 다룰 수 있다 |
| floor는 seen row에만 적용 | 이미 본 entity의 하한선만 비교 | 새 row까지 막아서 page가 비는 일을 줄인다 |
| reject 후에는 계속 스캔 | stale row를 버렸으면 replacement를 더 읽는다 | page size와 hidden row 문제를 줄인다 |
| repair 전략을 하나 정해 둠 | `patch`, `overlay`, `suppress` 중 하나 | stale candidate 처리 방식이 매번 달라지지 않는다 |

짧게 외우면:

- cursor는 순서
- floor는 채택 판단
- stale row를 버렸으면 다음 후보를 더 읽어 page를 채운다

## offset보다 seek/cursor가 먼저인 이유

`OFFSET 20 LIMIT 20` 같은 offset pagination은 freshness가 섞일 때 더 쉽게 흔들린다.

| 방식 | floor가 섞일 때 생기기 쉬운 문제 | beginner 추천도 |
|---|---|---|
| offset pagination | 앞쪽 row가 사라지거나 patch되면 뒷페이지 경계가 밀린다 | 낮음 |
| seek/cursor pagination | "마지막으로 본 정렬 키 다음부터"로 이어 읽기 쉽다 | 높음 |

특히 cache나 replica가 늦을 때 offset은 "앞 페이지에서 뺀 row 수"의 영향을 크게 받는다.
그래서 beginner 설계에서는 **seek/cursor + stable sort key**를 기본값으로 두는 편이 안전하다.

---

## 한 페이지를 만드는 안전한 흐름

가장 단순한 구현은 아래 순서다.

```text
1. cursor 기준으로 후보를 읽는다
2. 각 후보에 대해 floor 비교를 한다
3. floor 미달이면 reject + repair 정책 적용
4. 화면에 실제로 넣을 row 수가 page size에 찰 때까지 계속 읽는다
5. next_cursor는 "마지막으로 페이지에 포함한 row의 정렬 경계"를 기준으로 만든다
```

여기서 중요한 점은 `candidate < floor`인 row를 만났다고 전체 페이지를 실패로 돌리지 않는 것이다.
대부분은 그 row만 보정하거나 건너뛰고 계속 채우면 된다.

## 잘못된 구현 vs 안전한 구현

| 구현 | 동작 | 문제 |
|---|---|---|
| 잘못된 구현 | `LIMIT 20` 조회 후 floor 미달 row 삭제 | page shrink, hidden rows, cursor skip |
| 안전한 구현 | stale row를 reject하고 replacement를 더 스캔 | ordering 유지, page size 유지 가능 |

의사코드로 보면 차이가 더 분명하다.

```pseudo
function loadPage(cursor, pageSize, ctx):
  accepted = []
  scanCursor = cursor
  lastAcceptedSortKey = cursor

  while accepted.size < pageSize:
    batch = store.scanAfter(scanCursor, limit=pageSize)
    if batch.isEmpty():
      break

    for candidate in batch:
      scanCursor = candidate.sortKey

      if violatesFloor(candidate, ctx):
        repaired = tryRepair(candidate, ctx)
        if repaired != null:
          accepted.add(repaired)
          lastAcceptedSortKey = candidate.sortKey
        continue

      accepted.add(candidate)
      lastAcceptedSortKey = candidate.sortKey
      ctx.raiseMinVersion(candidate.id, candidate.version)

      if accepted.size == pageSize:
        break

  return Page(
    rows = accepted,
    nextCursor = encode(lastAcceptedSortKey)
  )
```

이 흐름의 포인트는 두 개다.

- stale row를 버려도 계속 스캔한다
- floor는 accept/reject 판단에만 관여하고 sort key는 그대로 유지한다

---

## `min-version`은 전체 페이지 필터가 아니다

초보자가 자주 하는 또 다른 오해는 "`page floor = 12`면 이 페이지의 모든 row가 12 이상이어야 한다"는 생각이다.
대부분의 목록에서는 그 해석이 틀리다.

| 올바른 해석 | 틀린 해석 |
|---|---|
| `order:109`를 이미 `version 12`로 봤으니 그 row만 12 아래로 내려가면 안 된다 | 2페이지의 모든 주문이 `version 12` 이상이어야 한다 |

왜냐하면 floor는 보통 **per-entity seen floor**이기 때문이다.
새로 처음 보는 `order:107 version=3`은 아무 문제 없다.
문제는 이미 `order:107 version=7`을 본 적이 있는데 다시 `version=3`으로 내려오는 경우다.

이 차이를 놓치면 page 대부분을 불필요하게 필터링해 버린다.

## concrete example: page 2에서 row가 사라지는 버그

정렬 기준이 `created_at desc, id desc`, page size가 3이라고 하자.

### 잘못된 흐름

```text
page 1 accepted
- order:110 version=8
- order:109 version=12
- order:108 version=5

request page 2 with cursor after 108

store returns candidates
- order:107 version=4
- order:106 version=2
- order:105 version=6
```

그런데 `order:106`은 이전 상세 화면에서 이미 `version=3`을 본 적이 있었다.

```text
floor
- min_version(order:106)=3
```

이제 `order:106 version=2`는 stale candidate다.
여기서 단순 삭제만 하면 결과는 이렇게 된다.

```text
page 2 rendered
- order:107 version=4
- order:105 version=6
```

사용자는 "원래 2개뿐인가?"라고 느끼지만, 실제로는 `order:104`가 다음 후보였을 수 있다.
그런데 cursor는 이미 `105` 뒤로 가 버려 `104`가 숨는다.

### 안전한 흐름

stale row를 버린 뒤 추가 후보를 더 읽는다.

```text
extra candidate
- order:104 version=1

page 2 rendered
- order:107 version=4
- order:105 version=6
- order:104 version=1
```

여기서는 `order:104`를 처음 보는 것이므로 floor 위반이 아니다.
page size도 유지되고, `order:106`이 오래된 값으로 다시 나오는 일도 막는다.

---

## repair 전략은 3개 중 하나로 고정하기

floor 미달 row를 만났을 때는 보통 아래 셋 중 하나를 쓴다.

| 전략 | 어떻게 보이나 | 잘 맞는 경우 |
|---|---|---|
| `patch` | 그 row만 fresher source로 다시 읽어 넣음 | page size가 작고 정확도가 중요할 때 |
| `overlay` | last-seen snapshot이나 fresher fields만 덮어씀 | cache/search lag가 짧고 표면 필드만 바꾸면 될 때 |
| `suppress` | stale row를 숨기고 replacement를 더 읽음 | 대량 목록에서 per-row repair가 비쌀 때 |

핵심은 무엇을 고르든 `candidate.version < floor`를 그대로 통과시키지 않는 것이다.

## cache/replica가 낀 경우에도 규칙은 같다

페이지네이션이라고 해서 freshness 규칙이 달라지지 않는다.

| 단계 | 같은 질문 |
|---|---|
| cache hit | 이 page row가 `min-version` floor를 만족하나 |
| cache miss 뒤 replica 선택 | 이 replica가 seen floor를 만족하는 row를 줄 수 있나 |
| refill | 이 값을 다음 page에서도 안전하게 재사용할 수 있나 |

즉 page 1, page 2 문제도 결국 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)에서 말하는 hit/miss/refill 규칙의 연장선이다.

---

## common confusion

- `min-version floor가 있으니 stale row는 그냥 빼면 된다`
  - 아니다. replacement를 더 읽지 않으면 hidden rows와 page shrink가 생긴다.
- `floor가 ordering까지 결정한다`
  - 아니다. ordering은 stable sort key가 담당하고, floor는 candidate accept/reject만 담당한다.
- `새 row도 floor보다 낮으면 숨겨야 한다`
  - 보통 아니다. floor는 이미 본 entity의 하한선이다.
- `offset pagination도 같은 방식으로 쉽게 된다`
  - 할 수는 있지만 page boundary drift가 커서 beginner 단계에서는 seek/cursor가 더 안전하다.
- `다음 cursor는 마지막으로 본 candidate 기준이면 된다`
  - stale candidate를 많이 버렸다면 hidden rows를 만들 수 있다. accepted row를 기준으로 안정적으로 이어 가는 쪽이 낫다.

## 빠른 체크리스트

- 정렬이 `updated_at` 단독처럼 불안정하지 않고 tie-breaker까지 포함하는가
- `min-version` floor가 page 전체가 아니라 seen entity별로 저장되는가
- stale row를 reject한 뒤 replacement를 더 스캔하는가
- page size가 줄어든 이유를 `suppressed_due_to_floor` 같은 신호로 구분할 수 있는가
- cache/replica/search hit도 동일한 floor 비교를 거치는가

## 한 줄 정리

페이지네이션에서 monotonicity를 지키는 핵심은 `min-version` floor를 전체 페이지 필터로 쓰지 않고, stable cursor 위에서 stale candidate만 reject/repair하면서 replacement를 계속 읽어 ordering과 page completeness를 함께 지키는 것이다.
