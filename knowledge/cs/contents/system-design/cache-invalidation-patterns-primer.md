# Cache Invalidation Patterns Primer

> 한 줄 요약: TTL, delete-on-write, write-through, versioned keys, stampede-safe refresh를 "언제 옛 값을 버리고 어떻게 다시 채울지" 관점에서 설명하는 입문 문서다.

retrieval-anchor-keywords: cache invalidation primer, cache invalidation patterns, cache ttl basics, ttl cache primer, delete on write cache, cache aside invalidation, write through cache basics, versioned keys cache, cache key versioning, cache stampede basics, single flight cache refresh, request coalescing cache, stale while revalidate basics, refresh ahead cache, ttl jitter basics

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Cache Admission Policy 설계](./cache-admission-policy-design.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 핵심 개념

캐시를 붙였다는 것은 "한 번 읽은 값을 잠깐 재사용한다"는 뜻이다.
그 순간부터 바로 따라오는 질문이 있다.

- 이 값은 언제까지 믿어도 되는가
- 원본 데이터가 바뀌면 캐시를 어떻게 멈출 것인가
- 캐시가 비는 순간 많은 요청이 몰리면 무엇이 원본을 보호하는가

이 세 질문을 다루는 것이 cache invalidation이다.

아주 단순한 예를 보자.

```text
DB
product:42 -> price=10000

Cache
product:42 -> price=10000
```

이제 운영자가 가격을 `12000`으로 바꾸면,
시스템은 더 이상 캐시에 남은 `10000`을 오래 내보내면 안 된다.

여기서 쓰는 대표 패턴이 오늘 문서의 다섯 가지다.

| 패턴 | 가장 단순한 생각 | 잘 맞는 상황 | 먼저 떠올려야 할 위험 |
|---|---|---|---|
| TTL | 오래되면 자동 만료 | 약간 stale해도 되는 읽기 | 만료 전까지 옛 값이 남는다 |
| delete-on-write | 쓰기 후 캐시를 지운다 | cache-aside 기본형 | 관련 key를 빼먹기 쉽다 |
| write-through | 쓰기와 함께 캐시도 새 값으로 맞춘다 | write 직후 read가 많은 흐름 | write path가 무거워진다 |
| versioned keys | key 이름을 새 버전으로 바꾼다 | fan-out invalidation이 복잡한 경우 | 오래된 key가 남는다 |
| stampede-safe refresh | 만료 순간을 안전하게 넘긴다 | hot key, 높은 QPS | 보호 장치가 없으면 DB에 몰린다 |

중요한 점은 보통 하나만 쓰지 않는다는 것이다.
실무에서는 `TTL + delete-on-write + single-flight`처럼 조합하는 경우가 많다.

---

## 먼저 잡는 mental model: 세 개의 시계

cache invalidation이 헷갈리는 이유는 보통 시계가 하나가 아니라 세 개이기 때문이다.

| 시계 | 실제로 진행되는 것 | 느릴 때 보이는 증상 |
|---|---|---|
| source 시계 | DB/원본 commit이 반영되는 시점 | write는 성공했는데 read가 옛값을 본다 |
| cache 시계 | TTL 만료, 삭제, 재적재, refresh 시점 | key마다 freshness가 들쭉날쭉하다 |
| user 시계 | 사용자가 다음 화면을 여는 시점 | "방금 본 값이 다음 화면에서 뒤로 간다" |

무효화 전략은 결국 이 세 시계를 완벽히 일치시키는 일이 아니라,
**사용자에게 보이는 역행(regression)을 줄이도록 시계 차이를 관리하는 일**이다.

---

## 초보자 1분 선택 순서

처음에는 패턴 이름보다 "지금 가장 아픈 실패가 무엇인지"부터 고르면 쉽다.

| 먼저 답할 질문 | 첫 선택 | 이유 |
|---|---|---|
| write 직후 바로 최신값이 꼭 필요한가 | `write-through` 또는 `delete-on-write + 짧은 TTL` | 저장 직후 read 흔들림을 먼저 줄일 수 있다 |
| stale를 몇 분 허용해도 서비스가 안전한가 | `TTL` | 구현 복잡도를 가장 낮게 시작할 수 있다 |
| key fan-out이 커서 삭제 누락이 자주 나나 | `versioned keys` | purge fan-out보다 새 key 전환이 단순하다 |
| hot key 만료 때 원본이 흔들리나 | `single-flight + jitter (+ stale-while-revalidate)` | 만료 순간 동시 miss를 완화한다 |

한 번에 완벽한 조합을 찾으려 하기보다, 먼저 가장 비싼 실패를 줄이는 조합으로 시작하면 된다.

## 한 번에 감 잡는 미니 비교: "프로필 저장 직후 조회"라면?

같은 상황을 패턴별로 짧게 비교하면 선택 기준이 더 빨리 잡힌다.

가정: 사용자가 `닉네임`을 저장하고 1초 안에 `내 프로필`을 다시 연다.

| 선택 | 사용자가 다음 조회에서 보기 쉬운 결과 | 초보자 관점 한 줄 판단 |
|---|---|---|
| `TTL`만 사용 | TTL 안에서는 옛 닉네임이 잠깐 남을 수 있음 | stale 허용이 가능할 때만 시작점으로 안전 |
| `delete-on-write + TTL` | 첫 재조회는 miss 후 새 값 재적재, 그다음은 안정 | 기본형으로 가장 무난하고 확장 쉽다 |
| `write-through + TTL` | 저장 직후 재조회에서 새 값을 볼 확률이 가장 높음 | write path 복잡도를 감당할 때 선택 |

핵심: 같은 "프로필 저장"이어도 **write 직후 UX를 얼마나 강하게 요구하는지**가 첫 분기다.

## 증상 기반 첫 대응 매트릭스

초보자에게는 "패턴 이름"보다 "지금 보이는 실패" 기준이 더 빠르다.

| 지금 보이는 증상 | 첫 대응(최소) | 바로 같이 볼 보조 장치 |
|---|---|---|
| 저장 직후 같은 화면에서 옛값이 자주 보임 | `delete-on-write` 또는 `write-through` | recent-write 라우팅 점검 |
| 특정 hot key 만료 시 지연/오류 급증 | `single-flight + TTL jitter` | 짧은 `stale-while-revalidate` |
| 목록/검색만 옛 상태로 되돌아감 | 관련 projection key invalidation 재점검 | [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md) |
| stale 감소를 위해 fallback했더니 primary 부담 급증 | post-write 구간만 fallback 범위 축소 | [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md) |

핵심은 "한 번에 완성형"이 아니라, 사용자에게 가장 먼저 보이는 실패를 줄이는 최소 조합으로 시작하는 것이다.

---

## 깊이 들어가기

### 1. TTL은 가장 단순하지만 "만료 전 stale"을 그대로 허용한다

TTL(Time To Live)은 캐시에 유효 기간을 붙이는 방법이다.

```text
SET product:42 value ttl=300s
```

의미는 간단하다.

- 300초 안에는 캐시 값을 그대로 쓴다
- 300초가 지나면 miss로 보고 원본에서 다시 읽는다

초보자에게 TTL이 매력적인 이유는 write path를 건드리지 않아도 되기 때문이다.
원본 시스템이 언제 바뀌는지 hook을 잡기 어려워도, 일단 "오래된 값은 언젠가 사라진다"는 보장이 생긴다.

간단한 시나리오:

- 상품 설명은 하루에 몇 번만 수정된다
- 사용자는 몇 분 정도 예전 설명을 봐도 큰 사고가 나지 않는다
- 이때 `TTL 5분` 같은 정책은 꽤 실용적이다

하지만 TTL의 한계도 분명하다.

- TTL이 남아 있는 동안에는 예전 값이 계속 나간다
- 여러 key가 같은 시각에 만료되면 miss가 한꺼번에 몰린다
- TTL을 너무 짧게 줄이면 최신성은 조금 좋아져도 miss storm가 커질 수 있다

즉, TTL은 "즉시 반영"이 아니라 **bounded staleness**를 사는 방법이다.

### 2. delete-on-write는 cache-aside에서 가장 흔한 기본형이다

delete-on-write는 원본 쓰기가 끝난 뒤 관련 cache key를 삭제하는 방식이다.

```text
PUT /profile
  -> DB update
  -> DEL user:123:profile

다음 GET /profile
  -> cache miss
  -> DB read
  -> cache repopulate
```

간단한 시나리오:

- 사용자가 닉네임을 바꾼다
- 시스템은 `user:123:profile` 캐시를 바로 지운다
- 다음 조회부터는 새 닉네임이 다시 채워진다

이 방식이 널리 쓰이는 이유:

- 구현이 단순하다
- cache가 source of truth가 아니라는 점이 분명하다
- 기존 cache-aside 패턴에 가장 잘 맞는다

하지만 초보자가 자주 놓치는 함정이 있다.

- 상세 key만 지우고 목록 key를 안 지우면 화면마다 값이 달라진다
- DB commit 전에 먼저 지우면 race가 생긴다
- 다음 read가 replica를 보고 예전 값을 다시 채워 넣을 수 있다

그래서 delete-on-write의 기본 규칙은 이렇다.

- **원본 commit 후에 지운다**
- **같이 보여 주는 related key를 묶어서 본다**
- **write 직후 read가 중요한 경로는 replica lag까지 같이 본다**

delete-on-write는 단순하지만,
"무슨 key들이 함께 무효화되어야 하는가"를 정확히 알아야 제대로 동작한다.

### 3. write-through는 "다음 read를 덜 흔들리게" 만드는 대신 write를 무겁게 만든다

## 깊이 들어가기 (계속 2)

write-through는 새 값을 저장할 때 cache도 바로 같은 값으로 갱신하는 방식이다.

```text
PUT /settings
  -> DB update
  -> SET user:123:settings = newValue ttl=300s
```

간단한 시나리오:

- 사용자가 알림 설정을 바꾼다
- 저장 직후 같은 설정 화면을 다시 연다
- 캐시가 이미 새 값으로 갱신되어 있으니 다음 read가 자연스럽다

write-through가 잘 맞는 경우:

- write 직후 같은 key를 다시 읽는 흐름이 많다
- key fan-out이 크지 않다
- write latency를 조금 더 써도 된다

대신 비용도 따라온다.

- write path가 길어진다
- DB는 성공했는데 cache set이 실패하면 후속 처리가 필요하다
- 여러 cache projection을 동시에 맞추려 들면 오히려 복잡해진다

초보자 기준으로는 이렇게 이해하면 충분하다.

- delete-on-write는 "일단 지우고 다음 read에 다시 채운다"
- write-through는 "지우지 말고 새 값을 바로 넣어 둔다"

둘 다 쓰지만, write-through는 **쓰기 순간에 freshness를 더 당겨오는 대신** write 쪽 복잡도를 더 낸다.

### 4. versioned keys는 "옛 key를 버리기"보다 "새 key로 우회하기"에 가깝다

versioned keys는 key 이름에 버전을 포함하는 방식이다.

```text
product:42:v17
product:42:v18
```

핵심 아이디어는 단순하다.

- 새 버전이 나오면 reader가 더 이상 `v17`을 보지 않게 한다
- 옛 key는 즉시 삭제하지 않아도 된다

간단한 시나리오:

- 상품 상세 페이지 HTML fragment를 캐시한다
- 가격, 할인 문구, 재고 배지가 한 묶음으로 렌더링된다
- 내용이 바뀌면 `product:42:v17` 대신 `product:42:v18`을 읽게 한다

이 패턴이 유리한 경우:

- 하나의 변경이 여러 캐시 계층에 퍼져 있다
- local cache, CDN, distributed cache가 함께 있어 즉시 삭제 fan-out이 어렵다
- "새 버전만 읽으면 된다"는 기준을 만들 수 있다

대신 꼭 기억할 점:

- 현재 버전 정보를 어디서 읽을지 정해야 한다
- 오래된 key는 TTL이나 cleanup job이 없으면 쌓인다
- 버전 bump와 원본 변경이 원자적으로 연결되지 않으면 엇갈릴 수 있다

즉, versioned keys는 "delete를 완전히 없애는" 마법이 아니라,
**fan-out invalidation을 단순화하는 우회 전략**이다.

### 5. hot key에서는 "어떻게 지울까"만큼 "만료 순간을 어떻게 넘길까"가 중요하다

캐시의 가장 흔한 운영 사고 중 하나가 stampede다.
많은 요청이 같은 key의 만료를 동시에 만나면서 원본 DB나 API로 몰리는 현상이다.

간단한 시나리오:

## 깊이 들어가기 (계속 3)

- `product:42` 상세 페이지가 초당 수천 번 읽힌다
- TTL이 60초다
- 60초가 되는 순간 수백 요청이 한꺼번에 miss를 본다
- DB가 같은 row를 수백 번 읽느라 흔들린다

이때 쓰는 것이 stampede-safe refresh 패턴이다.

#### Single-flight / request coalescing

동시에 miss가 나도 한 요청만 원본을 읽고, 나머지는 그 결과를 기다리게 한다.

- 장점: 원본 부하를 가장 직접적으로 줄인다
- 잘 맞는 경우: hot key, expensive lookup

#### Stale-while-revalidate

TTL이 막 지났더라도 아주 짧은 grace window에서는 예전 값을 잠깐 내보내고,
백그라운드에서 한 번만 새로고침한다.

- 장점: 사용자 latency가 안정적이다
- 잘 맞는 경우: 약간 stale해도 되는 카탈로그, 프로필, 설정 snapshot

#### TTL jitter

모든 key가 정확히 같은 시각에 만료되지 않게 TTL에 랜덤 값을 섞는다.

- 장점: 동시 만료를 분산한다
- 잘 맞는 경우: 비슷한 시점에 대량 적재되는 key 집합

#### Refresh-ahead

아주 뜨거운 key는 만료 직전에 백그라운드에서 미리 갱신한다.

- 장점: 사용자 요청이 refresh 비용을 직접 맞지 않는다
- 잘 맞는 경우: 홈 피드 상단, 인기 상품, 자주 보는 설정 snapshot

실무에서는 보통 이 넷 중 하나만 쓰지 않는다.

```text
TTL + jitter
single-flight on miss
stale-while-revalidate for short grace window
```

이 조합이 기본형이다.

### 6. 보통은 "무효화 방식"과 "refresh 보호 장치"를 같이 고른다

현실적인 선택은 아래처럼 묶어서 생각하면 쉽다.

| 상황 | 먼저 떠올릴 패턴 | 이유 |
|---|---|---|
| 약간 stale해도 되고 write hook이 약하다 | TTL | 가장 단순하다 |
| source of truth는 DB이고 cache-aside를 쓴다 | delete-on-write | 기본형으로 무난하다 |
| write 직후 같은 값을 자주 다시 읽는다 | write-through | 다음 read가 자연스럽다 |
| invalidation fan-out이 너무 크다 | versioned keys | 새 key 우회가 쉽다 |
| hot key가 많고 만료 순간이 위험하다 | stampede-safe refresh | 원본 보호가 먼저다 |

많은 서비스의 실제 조합 예시는 이렇다.

## 깊이 들어가기 (계속 4)

- 프로필/설정: `delete-on-write + TTL + single-flight`
- 관리자 설정 화면: `write-through + TTL`
- 렌더링 결과나 snapshot: `versioned keys + TTL`
- 바이럴 상품/게시글: `TTL + jitter + stale-while-revalidate + single-flight`

---

## 실전 시나리오

### 시나리오 1: 상품 상세 페이지

- 읽기 비중이 높다
- 가격/설명 수정은 가끔 있다
- write 직후 잠깐 stale이면 UX는 나쁘지만 대형 사고까지는 아니다

잘 맞는 기본 조합:

- `delete-on-write`
- `TTL 1~5분`
- `single-flight`

이 조합은 구현이 단순하면서도 hot key miss 폭주를 줄이기 쉽다.

### 시나리오 2: 사용자 설정 저장 직후 설정 화면 재조회

- 저장 직후 같은 값을 다시 읽는다
- 사용자는 "방금 저장한 값"을 바로 보고 싶어 한다

잘 맞는 선택:

- `write-through`
- 필요하면 짧은 `TTL`

이 경우 delete-on-write보다 write-through가 UX를 더 덜 흔들 수 있다.

### 시나리오 3: HTML fragment나 policy snapshot

- 여러 계층의 캐시에 퍼져 있다
- 일일이 삭제 fan-out하기가 번거롭다

잘 맞는 선택:

- `versioned keys`
- old key 자연 만료용 `TTL`

즉시 purge보다 "새 버전만 읽는다"가 더 단순할 때가 많다.

---

## 트레이드오프

| 패턴 | 장점 | 단점 | 잘 맞는 경우 |
|---|---|---|---|
| TTL | 가장 단순하고 write path를 안 건드린다 | 만료 전 stale이 남는다 | 약간 stale 허용 가능한 read |
| Delete-on-write | cache-aside와 잘 맞고 이해하기 쉽다 | key fan-out, race, replica stale 재적재를 조심해야 한다 | 일반적인 profile/detail 캐시 |
| Write-through | write 직후 read UX가 좋다 | write latency와 failure handling 부담이 있다 | 설정, 작은 metadata |
| Versioned keys | fan-out invalidation을 줄인다 | old key cleanup과 version source가 필요하다 | fragment cache, snapshot cache |
| Stampede-safe refresh | hot key 만료 사고를 막는다 | coordination과 grace 정책이 필요하다 | 고QPS key, 비싼 origin lookup |

핵심은 "무엇이 제일 단순한가"보다 "틀렸을 때 어디가 가장 아픈가"를 기준으로 고르는 것이다.

---

## 흔한 혼동

- TTL을 짧게만 두면 즉시 최신성이 보장된다고 오해하기 쉽다. TTL 안에서는 stale가 그대로 남는다.
- delete-on-write에서 상세 key만 지우고 목록/search projection key를 놓치면 화면 값이 갈린다.
- write-through를 쓰면 무효화가 필요 없다고 생각하기 쉽다. 실패 복구와 related key 정합은 여전히 남는다.
- versioned keys는 purge를 없애는 기법이 아니라, stale key cleanup을 뒤로 미루는 전략이다.
- stampede 보호는 대형 트래픽에서만 필요하다고 보기 쉽다. 작은 서비스도 hot key 하나면 같은 문제가 난다.
- 모든 key를 즉시 완전 동기화하려고 시작하면 구현/운영 복잡도만 급격히 커진다. 먼저 사용자 영향이 큰 read path부터 보호하고 확장해야 한다.
- invalidation을 넣었는데도 화면 역행이 남을 수 있다. 이 경우는 invalidation 문제라기보다 목록/상세/검색의 monotonicity 경계 문제일 수 있다.

---

## 다음으로 이어 읽기

지금 보이는 증상 기준으로 다음 문서를 고르면 초보자 동선이 짧아진다.

| 지금 보이는 증상 | 먼저 볼 문서 | 이유 |
|---|---|---|
| write 직후 옛값 노출이 핵심이다 | [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) | recent-write 요청을 어떤 source로 보낼지 먼저 고정할 수 있다 |
| cache와 replica가 섞여 stale 원인이 불분명하다 | [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md) | by-source stale 경로를 분리해 볼 수 있다 |
| stale hit 거절/우회 이유가 안 보인다 | [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) | reject/fallback reason을 지표와 로그로 남기는 기준을 잡는다 |
| incident 중 read downgrade 정책이 필요하다 | [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md) | freshness를 일부 양보할 때 지켜야 할 안전선을 본다 |
| 캐시 계층 설계를 넓혀 보고 싶다 | [분산 캐시 설계](./distributed-cache-design.md) | invalidation을 cluster topology와 운영 정책으로 확장한다 |

---

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> cache invalidation은 캐시된 값이 언제 더 이상 신뢰할 수 없는지 결정하는 문제입니다.
> 가장 단순한 방법은 TTL이고, cache-aside에서는 delete-on-write가 흔합니다. write 직후 read가 많으면 write-through가 유리하고, 관련 key fan-out이 크면 versioned keys로 새 버전만 읽게 만들 수 있습니다.
> 다만 invalidation만으로 끝나지 않고, hot key에서는 single-flight, stale-while-revalidate, TTL jitter 같은 stampede-safe refresh가 함께 있어야 origin을 보호할 수 있습니다.

## 꼬리질문

> Q: TTL만 짧게 두면 invalidation 문제가 거의 해결되나요?
> 의도: bounded stale와 instant freshness를 구분하는지 확인
> 핵심: 아니다. stale window는 남고, miss storm가 커질 수 있다.

> Q: delete-on-write와 write-through는 어떻게 다르나요?
> 의도: cache-aside 기본형과 eager update 차이를 아는지 확인
> 핵심: 전자는 지우고 다음 read에 재적재, 후자는 새 값을 즉시 캐시에 써 둔다.

> Q: versioned keys는 왜 쓰나요?
> 의도: fan-out invalidation 비용을 이해하는지 확인
> 핵심: 많은 cache layer를 즉시 purge하기보다 새 버전 key로 우회하는 편이 단순할 때가 있다.

> Q: stampede는 TTL만의 문제인가요?
> 의도: miss 동시성 문제를 이해하는지 확인
> 핵심: TTL expiry가 가장 흔한 원인이지만, 강제 삭제 직후에도 hot key면 같은 현상이 생길 수 있다.

## 한 줄 정리

Cache invalidation은 "언제 지울까" 하나가 아니라, TTL·삭제·즉시 갱신·버전 전환·stampede 보호를 함께 조합해 freshness와 origin 안전을 맞추는 설계다.
