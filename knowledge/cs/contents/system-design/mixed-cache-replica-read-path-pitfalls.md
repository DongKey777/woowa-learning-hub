# Mixed Cache+Replica Read Path Pitfalls

> 한 줄 요약: cache hit path와 replica miss path가 각각 다른 stale window를 가지면 `cache miss == fresh read`가 깨지므로, source-selection 규칙과 by-source observability를 같이 설계해야 한다.

retrieval-anchor-keywords: mixed cache replica read path, mixed cache+replica read path pitfalls, dual stale sources, dual stale source, cache miss stale replica, stale refill from replica, cache and replica both stale, cache hit newer than miss, invalidation exposes stale replica, mixed read path source selection, source selection rules, freshness routing rules, recent-write pinning with cache, cache boundary pinning, read path source tagging, cache replica observability, rejected hit observability, cache hit reject reason, replica fallback reason, refill no-fill reason, by-source freshness metrics, cache age vs replica lag, post-write stale read ratio, list detail source mismatch, miss path observability, version tagged cache fill, cache replica routing policy, recent write min version causal token, freshness bridge, intermediate freshness design

**난이도: 🟡 Intermediate**

관련 문서:

- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Cache와 Replica가 갈라질 때의 Read Inconsistency](../database/cache-replica-split-read-inconsistency.md)
- [Replica Lag Observability와 Routing SLO](../database/replica-lag-observability-routing-slo.md)

---

## 핵심 개념

cache와 replica를 같이 둔 읽기 경로는 "더 빠른 읽기 경로가 두 개 있다"가 아니라, **독립적인 stale source가 두 개 있다**는 뜻에 더 가깝다.

가장 흔한 형태는 아래다.

```text
Client
  -> App
      -> cache hit ? return cache
      -> cache miss ? replica read
      -> recent write / unsafe endpoint ? primary fallback
      -> chosen source result may fill cache
```

이 구조에서 놓치기 쉬운 점은 세 가지다.

- cache miss는 최신성 보장이 아니다
- invalidation은 stale cache를 지울 뿐, stale replica를 최신으로 만들지 않는다
- lagging replica 값을 다시 cache에 채우면 stale window가 더 길어진다

즉 mixed path의 핵심 문제는 "cache냐 replica냐"보다 **이번 요청이 어떤 freshness contract를 갖고 있고, 그 계약을 만족하는 source를 골랐는가**다.

초보자라면 `recent-write`, `min-version`, `causal token`이 hit/miss/refill 전체에 어떻게 이어져야 하는지 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)부터 보고 오는 편이 덜 헷갈린다.

---

## 깊이 들어가기

### 1. mixed path에서는 stale 시간이 두 개다

cache는 보통 `TTL`, invalidation 지연, local cache 잔존 시간 때문에 stale해진다.
replica는 replication lag, read routing, topology cache 지연 때문에 stale해진다.

둘을 같이 쓰면 같은 entity에 대해 두 개의 시간이 동시에 존재한다.

- `cache_age_ms`: cache 값이 마지막으로 채워진 뒤 지난 시간
- `replica_visible_lag_ms`: replica가 primary commit을 따라오지 못한 시간

문제는 이 둘이 서로 독립적이라는 점이다.

- cache는 최신인데 replica는 늦을 수 있다
- cache는 옛값인데 replica는 이미 최신일 수 있다
- 둘 다 stale인데 stale 이유가 다를 수 있다

그래서 `cache miss -> replica`를 단순 fallback으로 생각하면 안 된다.
mixed path에서는 miss path 자체가 별도의 freshness decision이다.

### 2. 초보자가 가장 자주 놓치는 pitfall

| pitfall | 실제로 벌어지는 일 | 사용자 증상 | 왜 오래 숨어 있나 |
|---|---|---|---|
| cache miss를 fresh read로 착각 | miss가 나도 replica가 lagging이면 옛값을 읽는다 | hit 때는 최신인데 miss 때는 예전 값이 나온다 | hit ratio가 높을 때는 miss path가 자주 안 보여서 늦게 드러난다 |
| invalidate가 stale replica를 노출 | delete-on-write 후 첫 read가 replica로 가서 옛값을 다시 채운다 | 저장 직후 값이 잠깐 사라졌다가 오래된 값으로 고정된다 | invalidation 자체는 성공했기 때문에 cache 지표만 보면 정상처럼 보인다 |
| recent-write pinning이 cache boundary에서 끊김 | write 직후 세션이어도 cache miss 시 아무 replica로 보낸다 | POST 후 redirect 화면에서만 stale이 난다 | 세션 pinning metric과 cache metric이 분리돼 있으면 연관이 안 보인다 |
| 화면마다 source가 갈라짐 | 상세는 cache, 목록은 replica, 검색은 다른 replica를 읽는다 | 같은 주문을 상세에서는 `PAID`, 목록에서는 `PENDING`으로 본다 | 각 endpoint는 개별적으로는 "정상"이라 aggregate lag만 보면 조용하다 |
| warm cache가 replica 문제를 가림 | 평소에는 cache hit로 가려지다가 eviction/failover 뒤 miss path가 드러난다 | 배포, failover, cache flush 뒤에만 stale complaint가 급증한다 | steady-state 대시보드에는 안 보이고 cold-path에서만 드러난다 |

핵심은 **cache 문제와 replica 문제를 따로 보는 순간, 혼합 incident를 놓친다**는 점이다.

### 3. source-selection 규칙은 endpoint, session, source 상태를 같이 봐야 한다

mixed path에서 가장 중요한 설계는 "어떤 source가 더 빠른가"가 아니라 "어떤 source가 이번 요청 계약을 만족하는가"다.

가장 단순한 규칙 ladder는 아래처럼 잡을 수 있다.

1. endpoint별 freshness class를 정한다.
2. request/session에 `recent write`, `min required version`, `unsafe after write` 같은 힌트를 붙인다.
3. cache hit이라도 freshness contract를 못 맞추면 버린다.
4. cache miss라도 replica가 contract를 못 맞추면 primary fallback한다.
5. replica 결과를 cache에 다시 채울 때도 동일한 contract를 만족하는지 확인한다.

아주 단순한 예시는 이렇다.

```pseudo
function readEntity(key, ctx):
  if ctx.endpoint.requiresPrimaryRead():
    return primary.read(key)

  cached = cache.get(key)
  if cached != null &&
     cached.version >= ctx.minVersion(key) &&
     cached.ageMs <= ctx.maxCacheAgeMs:
    return cached.withSource("cache")

  if ctx.hasRecentWrite(key) || replicaLagP99 > ctx.maxReplicaLagMs:
    fresh = primary.read(key)
    cache.fill(key, fresh)
    return fresh.withSource("primary")

  replicaValue = replica.read(key)
  if replicaValue.version >= ctx.minVersion(key):
    cache.fill(key, replicaValue)
    return replicaValue.withSource("replica")

  fresh = primary.read(key)
  cache.fill(key, fresh)
  return fresh.withSource("primary")
```

여기서 중요한 포인트는 네 가지다.

- `cache hit`는 accept rule이 있어야 한다
- `cache miss`는 routing rule이 있어야 한다
- `cache fill`은 write-back rule이 있어야 한다
- `recent write`와 `minVersion`은 redirect나 다음 화면으로 전달돼야 한다

버전이 없으면 `updated_at`, monotonically increasing sequence, LSN watermark 같은 대체 신호라도 둬야 한다.

### 4. cache와 replica 사이에 가장 먼저 명시할 운영 규칙

아래 규칙은 intermediate 수준에서 가장 효과가 크다.

| 운영 규칙 | 왜 필요한가 | 보통의 구현 |
|---|---|---|
| freshness class 분리 | 모든 GET을 같은 기준으로 읽으면 과하거나 약하다 | `strict`, `recent-write-sensitive`, `stale-ok` 같은 endpoint class |
| hit accept rule | hit를 무조건 정답으로 취급하면 stale cache가 contract를 깨뜨린다 | `maxAge`, `minVersion`, `cache source tier` 검사 |
| miss fallback rule | miss를 replica 직행으로 두면 stale replica가 바로 노출된다 | recent write, endpoint 위험도, current lag 기준으로 primary fallback |
| safe refill rule | lagging replica 결과를 cache에 재적재하면 stale가 증폭된다 | refill 전에 version/lag 체크, unsafe면 no-fill |
| source propagation | 다음 hop가 이전 freshness 힌트를 모르고 정책을 끊는다 | session flag, response token, request context header |

이 다섯 개가 없으면 mixed path는 성능 구조가 아니라 **랜덤한 freshness lottery**가 되기 쉽다.

### 5. observability는 hit ratio가 아니라 by-source freshness를 봐야 한다

mixed path에서 `cache hit ratio`와 `average replica lag`만 보는 것은 거의 항상 부족하다.

실제로 필요한 신호는 다음 쪽에 가깝다.

| 관측 신호 | 왜 필요한가 | 예시 태그/지표 |
|---|---|---|
| read source 분포 | 어떤 endpoint가 cache/replica/primary를 얼마나 탔는지 알아야 한다 | `read_source=cache|replica|primary`, `endpoint`, `entity_type` |
| stale hit ratio | hit가 많아도 stale hit가 많으면 의미가 없다 | `cache_stale_hit_ratio`, `cache_age_ms` histogram |
| miss-path stale ratio | 사용자가 느끼는 문제는 종종 miss path에서만 나온다 | `cache_miss_replica_stale_ratio`, `miss_to_primary_fallback_ratio` |
| refill safety 실패율 | stale replica가 cache를 다시 오염시키는지 봐야 한다 | `cache_refill_rejected_total`, `refill_source=replica`, `rejection_reason=min_version` |
| post-write stale read ratio | 제품 기준으로 직접 보이는 실패를 잡아야 한다 | `post_write_read_stale_total`, `endpoint`, `flow=redirect` |
| value flip rate | 같은 세션에서 `new -> old`가 보이는지 잡아야 한다 | `session_value_flip_total`, `detail_vs_list_mismatch_total` |
| primary fallback headroom | safety path가 늘 때 primary가 버틸지 알아야 한다 | `primary_fallback_qps`, `primary_cpu`, `fallback_reason=recent_write|lag` |

trace나 structured log에도 최소한 아래는 남기는 편이 좋다.

- `selected_source`
- `cache_age_ms`
- `replica_lag_ms`
- `min_required_version`
- `recent_write=true/false`
- `fallback_reason`
- `cache_fill_source`

이 태그가 있어야 "왜 이 요청은 cache를 버리고 primary로 갔는가"를 나중에 설명할 수 있다.

### 6. 평균 lag가 조용해도 mixed path incident는 터질 수 있다

replica lag 평균이 낮다고 mixed path가 안전한 것은 아니다.

대표적인 이유:

- 최신성 민감 endpoint는 평균이 아니라 tail lag에 노출된다
- cache가 대부분의 요청을 흡수하면 miss path sample이 너무 작아 aggregate metric에 묻힌다
- 특정 key, 특정 shard, 특정 replica에서만 stale refill이 반복될 수 있다
- failover 직후 topology cache가 늦으면 warm cache 뒤에 숨어 있던 경로가 한꺼번에 드러난다

그래서 alert도 아래처럼 나누는 편이 좋다.

- steady-state lag alert
- post-write stale read alert
- cache miss stale refill alert
- value flip / list-detail mismatch alert

lag alert 하나로 mixed freshness incident를 다 잡으려 하면 거의 항상 늦다.

### 7. 실전 시나리오

#### 시나리오 1: delete-on-write가 오히려 옛값을 다시 살린다

```text
1. POST /profile -> primary update success
2. app deletes cache key
3. GET /profile -> cache miss
4. app reads lagging replica
5. old value is returned and refilled into cache
```

겉으로 보면 cache invalidation은 성공했지만, 실제 결과는 stale window가 늘어난다.
이 경우는 invalidation 성공률보다 `invalidate -> miss -> replica stale refill` 지표가 더 중요하다.

#### 시나리오 2: 상세는 새 값인데 목록은 옛값이다

- 상세 endpoint는 cache hit
- 목록 endpoint는 replica default
- 같은 세션이 두 화면을 오간다

이때 문제는 cache hit율이 낮아서가 아니라 **endpoint별 source-selection 규칙이 서로 다르고, session monotonicity를 안 맞춘 것**이다.

#### 시나리오 3: 평소엔 멀쩡하다가 failover 뒤에만 stale complaint가 폭증한다

- warm cache 동안에는 replica 문제를 못 본다
- failover나 cache flush 뒤 miss가 늘어난다
- topology cache가 아직 old replica set을 향한다

이 경우는 steady-state replica lag chart만 봐서는 늦다.
cold-path read source 분포와 failover 이후 fallback reason 변화를 함께 봐야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 잘 맞는 경우 |
|---|---|---|---|
| cache + replica, explicit policy 없음 | 구현이 가장 단순하다 | dual stale source incident를 거의 설명할 수 없다 | low-risk, stale-tolerant read only |
| endpoint freshness class + recent-write pinning | 안전성 대비 구현 비용이 낮다 | 세션/context 전달이 필요하다 | redirect UX, 상태 변경 직후 확인 |
| version-tagged hit accept + safe refill | stale refill을 강하게 줄인다 | version metadata와 비교 비용이 든다 | 주문/권한/정책 snapshot 같은 민감 read |
| 넓은 primary fallback | 설명이 단순하고 안전하다 | primary 부하와 비용이 급격히 오른다 | 소수의 high-risk endpoint |

---

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> cache와 replica가 둘 다 읽기 경로에 있으면 stale source가 두 개 생깁니다.
> 그래서 cache miss를 fresh read로 보면 안 되고, recent write, min version, replica lag를 보고 source-selection 규칙을 명시해야 합니다.
> 또 hit ratio나 평균 lag만 보지 말고 read source 분포, stale refill 비율, post-write stale read ratio, session value flip 같은 by-source observability를 같이 둬야 mixed read path incident를 설명할 수 있습니다.

## 꼬리질문

> Q: cache miss면 replica로 바로 보내면 되지 않나요?
> 의도: miss를 freshness 보장으로 오해하지 않는지 확인
> 핵심: 아니다. recent write나 lag threshold를 넘는 endpoint는 miss 뒤에도 primary fallback이 필요하다.

> Q: invalidation을 잘하면 mixed path 문제는 사라지지 않나요?
> 의도: invalidation과 replica freshness를 분리해서 보는지 확인
> 핵심: 아니다. stale cache는 지워도 stale replica가 남아 있으면 miss path가 옛값을 다시 채울 수 있다.

> Q: observability에서 제일 먼저 뭘 추가해야 하나요?
> 의도: 추상 metric이 아니라 설명 가능한 signal을 고르는지 확인
> 핵심: read source tagging, post-write stale ratio, miss-path stale refill ratio, fallback reason 태그부터 두는 편이 가장 효과가 크다.

## 한 줄 정리

Mixed cache+replica read path의 핵심은 "더 빠른 fallback"이 아니라 "독립적인 stale source 두 개를 freshness contract로 통제하고 관측하는 것"이다.
