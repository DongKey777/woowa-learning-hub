# List-Detail Monotonicity Bridge

> 한 줄 요약: 목록, 상세, 검색 화면이 서로 다른 cache/replica/search index를 읽더라도 세션이 본 `min-version` floor를 함께 들고 다니면 `PAID -> PENDING`처럼 값이 뒤로 가는 경험을 막을 수 있다.

retrieval-anchor-keywords: list detail monotonicity bridge, list detail search min-version floor, list detail search min version, min-version floor, min_version floor, value regression across pages, list detail mismatch, search detail consistency, search result stale after detail, detail newer than list, order list detail search monotonic reads, per entity freshness floor, session min version bridge, seen version floor, row version floor, beginner monotonic screens, cache replica search read path consistency, system-design-00056

**난이도: 🟢 Beginner**

관련 문서:

- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)

---

## 핵심 개념

먼저 용어보다 화면 경험으로 생각하자.

> 사용자가 한 화면에서 더 새 값을 봤다면, 다음 화면은 그 값보다 오래된 값을 보여 주면 안 된다.

`min-version floor`는 이 약속을 위한 작은 메모다.
예를 들어 사용자가 주문 상세에서 `order:123 version=42, status=PAID`를 봤다면 세션은 이렇게 기억한다.

```text
min_version(order:123) = 42
last_seen_snapshot(order:123) = status=PAID
```

이 값은 "모든 주문이 version 42 이상이어야 한다"는 뜻이 아니다.
**이미 본 주문 `123`만 최소 42 아래로 내려가지 말자**는 per-entity floor다.

---

## 왜 목록, 상세, 검색에서 자주 깨지나

세 화면은 같은 주문을 보여 주지만 보통 읽는 저장소가 다르다.

| 화면 | 흔한 빠른 read path | 오래된 값이 나오는 이유 |
|---|---|---|
| 상세 | primary fallback 또는 detail replica | 상세는 비교적 fresh하게 읽도록 보호하기 쉽다 |
| 목록 | summary cache 또는 list replica | row summary cache가 아직 `PENDING`일 수 있다 |
| 검색 | search index | indexing lag 때문에 document가 늦게 갱신될 수 있다 |

그래서 이런 일이 생긴다.

```text
1. GET /orders/123
   -> detail reads fresh value
   -> order:123 version=42, status=PAID

2. GET /orders
   -> list cache still has old row
   -> order:123 version=40, status=PENDING

3. GET /orders/search?q=123
   -> search index still has old document
   -> order:123 version=39, status=PENDING
```

사용자 입장에서는 결제가 완료됐다가 다시 대기 상태로 되돌아간 것처럼 보인다.
이것이 list-detail-search 사이의 value regression이다.

---

## 같은 floor를 세 화면에 싣기

해결의 시작점은 세 화면이 같은 freshness context를 받는 것이다.

```text
freshness context
- min_version(order:123) = 42
- last_seen_snapshot(order:123) = status=PAID
```

이 context를 받은 각 화면은 후보 값을 바로 렌더링하지 않고, 먼저 floor와 비교한다.

| 화면 | 후보 값 | floor 비교 | floor보다 낮으면 |
|---|---|---|---|
| 상세 | detail row/cache entry | `detail.version >= 42` | primary/source-of-truth로 fallback |
| 목록 | list row summary | `row.version >= 42` | row를 fresh source로 patch하거나 last-seen snapshot 유지 |
| 검색 | search hit document | `hit.version >= 42` | stale hit을 바로 렌더링하지 않고 refresh/overlay/suppress |

핵심은 상세 화면에서 만든 floor가 목록과 검색으로도 넘어간다는 점이다.
상세만 fresh하고 목록/검색은 각자 오래된 경로를 그대로 쓰면 monotonic reads는 깨진다.

---

## 주문 하나로 보는 concrete example

### 1. 상세 화면이 floor를 올린다

상세 화면이 신선한 값을 읽었다.

```text
GET /orders/123

response row
- id = 123
- status = PAID
- version = 42
```

응답을 렌더링한 뒤 세션 context를 올린다.

```text
ctx.raise_min_version(order:123, 42)
ctx.remember_snapshot(order:123, status=PAID)
```

여기서 `raise`라는 말이 중요하다.
floor는 낮추지 않는다.
이미 `42`를 봤는데 나중에 `40`을 봤다고 `40`으로 덮으면 보장이 사라진다.

### 2. 목록 화면이 오래된 row를 거절한다

목록 cache에는 아직 예전 row가 있다.

```text
list cache candidate
- id = 123
- status = PENDING
- version = 40
```

목록은 이 row를 바로 보여 주지 않는다.

```text
required floor = min_version(order:123) = 42
candidate version = 40

40 < 42 이므로 stale candidate
```

beginner 단계에서 가장 단순한 처리는 둘 중 하나다.

| 선택 | 의미 | 언제 적당한가 |
|---|---|---|
| row patch | 주문 `123`만 primary/detail read로 다시 읽어 목록 row를 고친다 | row 수가 적고 정확한 상태가 중요한 목록 |
| last-seen 유지 | 세션이 기억한 `PAID` snapshot으로 그 row를 유지한다 | 잠깐의 index/cache lag를 UX에서 부드럽게 흡수할 때 |

어느 쪽이든 사용자는 `PAID -> PENDING`으로 내려가는 화면을 보지 않는다.

### 3. 검색 화면도 같은 floor를 적용한다

검색 index도 늦을 수 있다.

```text
search hit candidate
- id = 123
- status = PENDING
- version = 39
```

검색 화면도 같은 비교를 한다.

```text
39 < min_version(order:123=42)
```

이 hit은 검색 결과에서 빠르게 나온 값이지만, 이 세션에는 너무 오래됐다.
그래서 검색 서비스나 BFF는 아래 중 하나를 고른다.

- source-of-truth에서 주문 `123`을 다시 읽어 hit을 overlay한다
- index가 따라올 때까지 그 hit의 오래된 status를 숨기거나 "갱신 중" 상태로 둔다
- 적어도 `PENDING`이라는 낮은 status를 그대로 보여 주지는 않는다

검색 전체를 항상 primary처럼 만들 필요는 없다.
**세션이 이미 본 몇 개의 entity만 floor로 보호**하면 된다.

---

## 가장 작은 구현 모양

처음부터 거대한 consistency framework를 만들 필요는 없다.
아래 세 가지 필드부터 시작할 수 있다.

| 필드 | 예시 | 역할 |
|---|---|---|
| entity key | `order:123` | 어떤 객체에 대한 floor인지 구분 |
| min version | `42` | 이 세션에서 이 객체가 내려가면 안 되는 최소 version |
| optional snapshot | `status=PAID` | patch 전까지 낮은 값을 보여 주지 않기 위한 임시 표시값 |

요청 흐름은 이렇게 단순화할 수 있다.

```pseudo
function acceptCandidate(entity, candidate, ctx):
  floor = ctx.minVersion(entity)

  if floor != null and candidate.version < floor:
    return repairOrUseLastSeen(entity, floor, ctx)

  ctx.raiseMinVersion(entity, candidate.version)
  ctx.rememberSnapshot(entity, candidate.visibleFields)
  return candidate
```

이 함수를 상세, 목록 row, 검색 hit에 모두 적용한다.
중요한 건 "상세용 규칙", "목록용 규칙", "검색용 규칙"을 따로 만들지 않고 같은 floor 비교를 공유하는 것이다.

---

## floor는 어디에 저장하나

beginner 설계에서는 아래 중 하나로 충분하다.

| 저장 위치 | 장점 | 주의점 |
|---|---|---|
| server-side session store | client가 조작하기 어렵고 여러 page에서 공유하기 쉽다 | session store 조회 비용과 TTL 필요 |
| signed response token | stateless하게 넘기기 쉽다 | 토큰 크기 제한, 서명/무결성 필요 |
| BFF memory/context | 화면 전환이 BFF를 지나갈 때 단순하다 | 탭/기기/재시작 경계가 약하다 |

보통은 최근에 본 entity 몇 개만 짧은 TTL로 유지한다.
모든 row의 version을 영원히 저장하려는 순간 이 문서는 beginner 범위를 넘어간다.

---

## 흔한 혼동

- `min-version=42`는 모든 목록 row가 42 이상이어야 한다는 뜻이 아니다. `order:123`처럼 이미 본 entity에만 적용하는 floor다.
- search index가 늦는다고 모든 검색을 primary로 보내야 하는 것은 아니다. 이미 본 entity의 stale hit만 guard하면 된다.
- 목록 정렬, 총 개수, facet count까지 완벽히 최신으로 맞추는 문제는 별도다. 여기서는 사용자가 이미 본 row의 값이 뒤로 가지 않는 것부터 막는다.
- read-after-write만으로는 충분하지 않을 수 있다. 사용자가 write하지 않았더라도 상세에서 더 새 값을 본 뒤 목록/검색에서 과거 값을 보면 regression이다.
- cache hit이나 search hit은 "빠른 후보"일 뿐이다. `min-version` floor를 못 맞추면 그 세션에서는 채택하면 안 된다.

---

## 빠른 체크리스트

- response row/detail/search hit에 비교 가능한 `version` 또는 commit marker가 있는가
- 화면이 값을 렌더링한 뒤 session/context의 `min_version(entity)`를 올리는가
- 목록 row와 검색 hit도 같은 `min_version` floor를 검사하는가
- floor 미달 후보를 그대로 렌더링하지 않고 patch, last-seen 유지, suppress 중 하나로 처리하는가
- `min_version`은 낮추지 않고 TTL/개수 제한으로만 정리하는가
- `rejected_candidate_reason=min_version` 같은 낮은 cardinality 관측 신호를 남기는가

더 깊게 들어가려면 cache/replica hit-miss-refill 전체에 freshness context를 이어 붙이는 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)와, 거절/우회 이유를 로그와 메트릭으로 남기는 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)를 보면 된다.

## 한 줄 정리

list-detail-search monotonicity는 세 화면을 모두 강한 읽기로 바꾸는 문제가 아니라, 사용자가 이미 본 entity의 `min-version` floor를 공유해서 오래된 후보가 화면에 채택되지 않게 하는 문제다.
