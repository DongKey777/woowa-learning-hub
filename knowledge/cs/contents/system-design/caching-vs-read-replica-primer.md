# Caching vs Read Replica Primer

> 한 줄 요약: cache는 같은 읽기를 아예 줄이는 전략이고 read replica는 DB 읽기 처리량을 늘리는 전략이며, 둘 다 stale 문제가 있지만 원인과 대응이 다르다는 점을 설명하는 입문 문서다.

retrieval-anchor-keywords: caching vs read replica, cache vs replica, read scaling primer, cache invalidation basics, stale read basics, stale-if-error, cache-first read scaling, read replica basics, cache-aside vs read replica, read-after-write basics, read-after-write routing primer, replica lag basics, primary fallback, session pinning primer, read-only downgrade

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
- [Cache와 Replica가 갈라질 때의 Read Inconsistency](../database/cache-replica-split-read-inconsistency.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)

---

## 핵심 개념

초보자가 cache와 read replica를 자주 헷갈리는 이유는 둘 다 겉으로는 "DB 읽기를 줄여 준다"처럼 보이기 때문이다.
하지만 실제로 하는 일은 다르다.

- cache는 **같은 읽기를 재사용**해서 DB 요청 자체를 줄인다
- read replica는 **DB 서버를 더 두어 읽기를 분산**한다

즉, cache는 "읽기 일을 없애는" 쪽에 가깝고, replica는 "읽기 일을 더 많은 DB가 나눠 받는" 쪽에 가깝다.

아주 단순하게 그리면 아래처럼 볼 수 있다.

```text
1) Cache-first
Client -> App -> Cache hit -> 응답
              -> Cache miss -> DB

2) Read replica
Client -> App -> Replica
Write  -> App -> Primary -> replicate -> Replica
```

핵심 차이 하나만 먼저 잡자.

| 질문 | Cache | Read replica |
|---|---|---|
| 무엇을 줄이나 | DB로 가는 요청 수 | 한 DB가 받는 읽기 부하 |
| stale 원인은 무엇인가 | invalidation 지연, TTL, race | replication lag, read routing |
| 느린 쿼리를 없애 주나 | 일부 반복 조회는 숨길 수 있음 | 아니다. 비싼 쿼리는 replica에서도 비쌈 |
| 잘 맞는 패턴 | 같은 key를 자주 읽는 hot read | 다양한 read query가 많아 DB read capacity가 부족한 경우 |

---

## 깊이 들어가기

### 1. 둘 다 읽기 확장이지만 푸는 문제는 다르다

예를 들어 상품 상세 페이지처럼 같은 `product:123`을 수없이 읽는 상황을 보자.
이때는 cache가 특히 잘 맞는다.

- 같은 결과를 반복 재사용할 수 있다
- DB에 가지 않아도 되는 요청이 많아진다
- hot key를 잘 흡수하면 latency도 크게 줄어든다

반대로 검색 목록, 관리자 조회, 리포트처럼 요청마다 조건이 꽤 다르면 cache hit율이 낮을 수 있다.
이런 경우에는 replica가 더 자연스러울 수 있다.

- 다양한 SELECT를 replica 여러 대가 나눠 받는다
- app 입장에서는 "읽을 DB 풀"이 넓어진다
- 단, query 비용 자체가 사라지는 것은 아니다

즉, cache는 **재사용 가능한 읽기**에 강하고, replica는 **DB가 직접 처리해야 하는 읽기량**을 분산하는 데 강하다.

### 2. Cache의 핵심 문제는 invalidation이다

cache를 붙이면 가장 먼저 따라오는 질문은 "언제 지우거나 갱신할 것인가"다.

대표 방식:

- TTL로 자연 만료시킨다
- write 직후 해당 key를 삭제한다
- 새 값을 cache에도 같이 쓴다
- version key를 올려서 옛 값을 우회한다

여기서 stale read가 생기는 전형적인 이유:

- write는 성공했지만 cache 삭제가 늦었다
- TTL이 남아 있어 예전 값이 계속 응답된다
- 삭제 후 첫 read가 DB에서 옛 값을 다시 채웠다
- 여러 related key를 다 지우지 못해 화면마다 값이 달라진다

즉, cache stale 문제는 보통 "복제가 늦다"보다 **app이 캐시 수명을 어떻게 관리했는가**의 문제다.

### 3. Read replica의 핵심 문제는 lag와 routing이다

read replica 구조에서는 write는 primary가 받고, replica는 나중에 그 변경을 따라간다.

```text
write -> primary commit
      -> replicate
      -> replica apply
      -> replica read sees new value
```

그래서 아래 같은 일이 생긴다.

- 방금 저장했는데 replica 조회에는 아직 안 보인다
- 새로고침할 때마다 어떤 replica를 읽느냐에 따라 값이 달라진다
- failover 직후 topology cache가 늦어 엉뚱한 노드로 읽는다

이때 stale read는 cache invalidation 문제가 아니라 **replica가 아직 해당 write를 따라오지 못한 것**이다.

대표 대응:

- 최근 write가 있었던 요청은 잠시 primary로 보낸다
- 사용자 세션을 짧게 primary에 pinning한다
- 최신성이 중요한 화면만 primary fallback을 둔다
- stale 허용 범위를 제품 요구사항으로 명시한다

### 4. 둘 다 stale read가 있지만 질문이 다르다

겉보기 증상은 비슷하다.

## 깊이 들어가기 (계속 2)

- 저장 직후 예전 값이 보인다
- 새로고침할 때 값이 뒤집힌다
- 목록과 상세가 서로 다른 상태를 보여 준다

하지만 진단 질문은 다르다.

| 증상 확인 질문 | Cache 쪽 질문 | Replica 쪽 질문 |
|---|---|---|
| 왜 옛 값이 보였나 | invalidation이 늦었나? TTL이 남았나? | replication lag가 있었나? |
| 왜 요청마다 값이 달랐나 | 서로 다른 key가 섞였나? local cache가 남았나? | 다른 replica로 라우팅됐나? |
| write 직후 왜 안 보였나 | delete/update cache 순서가 꼬였나? | read-after-write를 replica로 보냈나? |

그래서 stale read는 한 단어로 끝내면 안 되고,
"**cache stale인지 replica stale인지**"를 먼저 가르는 게 중요하다.

### 5. 언제 cache-first를 먼저 보고, 언제 replica를 먼저 보나

아래처럼 생각하면 초보자 기준에서 덜 헷갈린다.

| 상황 | 먼저 보는 선택지 | 이유 |
|---|---|---|
| 같은 상세 조회가 너무 많다 | cache | 같은 결과를 반복 재사용할 수 있다 |
| 읽기 QPS가 높고 query 종류도 다양하다 | read replica | 여러 DB가 SELECT를 나눠 받을 수 있다 |
| 특정 쿼리 하나가 너무 느리다 | index / query tuning | replica를 붙여도 비싼 쿼리는 계속 비싸다 |
| write 직후 최신값이 꼭 보여야 한다 | primary fallback | cache와 replica 둘 다 stale 가능성이 있다 |
| 목록은 약간 stale해도 되지만 상세는 최신이어야 한다 | 혼합 전략 | 경로별 freshness 요구가 다르다 |

중요한 실전 감각은 이것이다.

- "반복 read" 문제면 cache를 먼저 본다
- "DB read capacity" 문제면 replica를 먼저 본다
- "느린 query" 문제면 둘 다 전에 query/index를 먼저 본다

### 6. 같이 쓰는 경우가 많지만, 비용도 같이 따라온다

실무에서는 cache와 replica를 같이 쓰는 경우가 많다.
하지만 이때는 단순히 성능이 두 배 좋아지는 게 아니라 stale source가 두 개가 된다.

```text
read path:
  App -> Cache
      -> miss면 Replica
      -> recent write면 Primary fallback
```

이 구조의 장점:

- hot read는 cache가 대부분 흡수한다
- cache miss나 다양한 조회는 replica가 분산한다

이 구조의 단점:

- cache invalidation도 봐야 한다
- replica lag도 봐야 한다
- source selection 규칙이 없으면 화면마다 값이 갈라질 수 있다

## 깊이 들어가기 (계속 3)

그래서 둘을 같이 둘수록 "무엇을 어디서 읽을지"를 더 엄격히 정해야 한다.
이 mixed read path의 request-carried freshness context, hit/miss/refill bridge는 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)에서, rejected hit/fallback/no-fill 관측성은 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)에서, dual stale source와 source-selection/observability pitfall은 [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)에서 이어서 본다.

### 7. 초보자가 자주 하는 오해

`read replica를 붙이면 stale read는 없어지고 invalidation도 신경 안 써도 된다`

- 아니다. invalidation 문제는 줄지만 replication lag 문제가 생긴다

`cache를 붙이면 replica가 필요 없다`

- 아니다. hot read는 cache로 줄여도, 다양한 ad-hoc read는 여전히 DB가 처리해야 할 수 있다

`replica를 붙이면 느린 query가 해결된다`

- 아니다. 비싼 query를 여러 대에 복제할 뿐이다

`TTL을 짧게 두면 최신성 문제는 거의 해결된다`

- 아니다. 짧은 TTL도 stale window를 없애지 못하고 miss storm만 늘릴 수 있다

---

## 실전 시나리오

### 시나리오 1: 상품 상세 페이지

- 같은 상품 상세를 매우 자주 읽는다
- 상품 수정은 상대적으로 적다

이때는 cache-first가 잘 맞는다.
다만 가격 변경 직후에는 invalidation이 제대로 되었는지 확인해야 한다.

### 시나리오 2: 관리자 목록 / 검색 / 리포트

- 조회 조건이 자주 바뀐다
- 캐시 key가 잘게 쪼개져 hit율이 낮다

이때는 read replica가 더 자연스럽다.
다만 정산 상태나 주문 상태처럼 최신성이 중요한 칼럼은 replica lag를 조심해야 한다.

### 시나리오 3: 결제 직후 주문 상세

- 사용자는 "방금 결제한 주문"을 바로 본다
- stale read가 UX와 CS 이슈로 직결된다

이 경로는 cache나 replica보다 primary fallback이 더 중요하다.
초보자가 가장 많이 하는 실수는 "읽기 확장 구조를 넣었으니 모든 GET이 replica여도 된다"고 생각하는 것이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 잘 맞는 경우 |
|---|---|---|---|
| Cache-first | DB 요청 수와 latency를 크게 줄일 수 있다 | invalidation, stampede, hot key 대응이 필요하다 | 같은 데이터를 반복 조회할 때 |
| Read replica | DB read capacity를 비교적 직관적으로 늘릴 수 있다 | lag, failover, read-after-write routing이 필요하다 | 다양한 read query가 많을 때 |
| Cache + replica | hot read와 broad read를 함께 분산할 수 있다 | stale source가 둘이 되어 운영 규칙이 더 복잡해진다 | 규모가 커지고 경로별 정책이 분리될 때 |
| Primary fallback 포함 | 최신성이 중요한 경로를 보호할 수 있다 | primary 부하가 늘 수 있다 | write 직후 확인, 금전/상태 변경 직후 조회 |

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> cache와 read replica는 둘 다 읽기 확장 수단이지만, cache는 같은 읽기를 재사용해 DB 요청 자체를 줄이고, read replica는 DB 복제본을 늘려 읽기 부하를 분산합니다.
> cache의 핵심 문제는 invalidation이고, read replica의 핵심 문제는 replication lag와 read-after-write입니다.
> 그래서 hot read에는 cache가, 다양한 조회량 분산에는 replica가 잘 맞고, 최신성이 중요한 경로는 둘 다 맹신하지 말고 primary fallback을 둬야 합니다.

## 꼬리질문

> Q: cache와 read replica는 둘 다 stale read를 만들 수 있는데 뭐가 다른가요?
> 의도: 같은 증상이라도 원인과 대응이 다름을 구분하는지 확인
> 핵심: cache는 invalidation 문제, replica는 lag와 routing 문제다.

> Q: read replica를 붙이면 캐시가 필요 없나요?
> 의도: read capacity와 repeated read elimination을 구분하는지 확인
> 핵심: 아니다. hot read를 없애는 데는 cache가 더 직접적일 수 있다.

> Q: cache miss면 replica로 바로 보내면 되나요?
> 의도: miss를 최신성 보장으로 오해하지 않는지 확인
> 핵심: 최근 write 경로라면 primary fallback이 더 안전할 수 있다.

> Q: 느린 SELECT가 많으면 cache와 replica 중 무엇부터 보나요?
> 의도: read scaling과 query tuning의 순서를 아는지 확인
> 핵심: 먼저 query/index를 보고, 그다음 반복 read면 cache, broad read capacity면 replica를 본다.

## 한 줄 정리

Cache는 읽기를 재사용해서 DB 일을 줄이고, read replica는 DB 읽기 일을 여러 대가 나눠 받게 하며, stale 문제는 둘 다 있지만 cache는 invalidation, replica는 lag가 본질이다.
