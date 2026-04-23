# Cache와 Replica가 갈라질 때의 Read Inconsistency

> 한 줄 요약: 캐시와 replica가 서로 다른 시점을 들고 있으면, 둘 중 어느 쪽을 읽어도 맞는 것 같지만 둘 다 틀릴 수 있다.

**난이도: 🔴 Advanced**

관련 문서: [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md), [Caching vs Read Replica Primer](../system-design/caching-vs-read-replica-primer.md), [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)
retrieval-anchor-keywords: cache replica split, cache vs replica stale, cache invalidation vs replica lag, mixed stale source, mixed stale read, stale source disambiguation, cache miss stale replica, cache miss then old replica, stale cache after write, updated but old value from cache or replica, list detail mismatch after write, cache and replica disagree, cache replica freshness routing, mixed source of truth, read inconsistency, cache invalidation, stale cache, old data after write cache or replica, save succeeded but old value via cache miss, 캐시 미스 후 리플리카 옛값, 캐시 무효화 vs 리플리카 지연, 캐시와 리플리카 값 다름, 목록과 상세가 서로 다른 상태, 방금 저장했는데 캐시인지 리플리카인지 모르겠음

## 증상별 바로 가기

- `cache hit 때는 최신인데 miss 때는 옛값`, `cache miss then old replica`, `목록과 상세가 서로 다른 상태`처럼 cache와 replica가 서로 다른 시점을 들고 있는지 먼저 가려야 하면 이 문서에서 stale source split부터 본다.
- `write는 성공했는데 어디서 읽어도 바로 옛값`, `save succeeded but old value returned`처럼 write 직후 freshness budget 자체가 핵심이면 [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md)로 바로 간다.
- `lag metric은 낮은데 일부 endpoint나 cache miss path에서만 옛값`, `freshness alert은 조용한데 사용자만 stale read를 본다`처럼 관측과 체감이 어긋나면 [Replica Lag Observability와 Routing SLO](./replica-lag-observability-routing-slo.md)와 함께 읽는다.
- `내가 방금 바꾼 값이 내 세션에서만 유지돼야 한다`처럼 세션 보장이 핵심이면 [Read-Your-Writes와 Session Pinning 전략](./read-your-writes-session-pinning.md)으로 먼저 이동한다.

## 핵심 개념

캐시는 빠르지만 오래된 값을 줄 수 있고, replica는 최신성이 더 좋을 수 있지만 lag가 있다.  
둘이 동시에 쓰이면 사용자는 같은 화면에서 서로 다른 진실을 볼 수 있다.

왜 중요한가:

- 캐시와 DB replica가 서로 다른 시간축에 있을 수 있다
- 어떤 요청은 캐시, 어떤 요청은 replica를 타면 결과가 뒤집힌다
- invalidation만으로는 항상 해결되지 않는다

즉 문제는 캐시가 있느냐가 아니라, **어느 소스가 최신인지 라우팅이 알고 있느냐**다.

중요한 점은 `stale read`라는 같은 표면 증상 아래에 서로 다른 root cause가 숨어 있다는 것이다.
cache invalidation이 늦어도 옛값이 보이고, replica lag가 있어도 옛값이 보인다.
둘을 함께 쓰는 구조에서는 `cache miss 뒤 stale replica 재사용` 같은 혼합 incident가 생긴다.

## 깊이 들어가기

### 1. split source of truth가 생기는 이유

전형적으로 다음 조합에서 생긴다.

- write는 primary
- read는 cache 또는 replica
- 캐시 invalidation은 비동기
- replica lag도 존재

이때 cache와 replica가 서로 다른 최신값을 가리킨다.

### 2. 왜 캐시만 보면 안 되는가

캐시는 보통 TTL이나 eviction으로 인해 오래된 값을 남길 수 있다.  
replica도 lag 때문에 최신 값이 아닐 수 있다.

둘 중 하나만 믿고 라우팅하면 오판이 생긴다.

### 3. stale source를 먼저 가르는 질문

| 먼저 확인할 질문 | cache stale 쪽 신호 | replica stale 쪽 신호 | mixed stale-source 쪽 신호 |
|---|---|---|---|
| cache hit과 miss 결과가 다른가 | hit일 때만 옛값이 남는다 | hit/miss와 무관하게 replica read가 늦다 | miss 뒤 replica가 더 옛값이라 결과가 뒤집힌다 |
| lag metric이 실제로 높나 | 대체로 낮거나 무관하다 | 높다 | 낮거나 경계선인데 cache miss path에서만 증상이 커진다 |
| 어떤 화면/endpoint가 특히 흔들리나 | 같은 entity라도 cache key 묶음이 다르다 | replica selection, read routing 정책 전체가 흔들린다 | 상세는 cache, 목록은 replica처럼 source가 화면별로 갈라진다 |
| recent write 직후만 문제인가 | invalidation race가 있으면 그렇다 | read-after-write 경로에서 자주 터진다 | invalidate 후 replica fallback이 겹칠 때 특히 심해진다 |

즉 `cache stale인지`, `replica stale인지`, `둘이 동시에 stale인지`를 먼저 나눠야 root cause가 빨리 좁혀진다.

### 4. 해결 방향

- 최근 write는 primary fallback
- cache miss 시 replica 직행이 아니라 freshness 확인
- version token으로 cache와 DB 버전 비교
- invalidate 후 바로 read가 필요한 경로는 primary pinning
- lag metric이 낮아도 cache miss -> replica fallback 경로는 별도 추적

핵심은 캐시와 replica를 **서로 다른 stale source**로 본다는 점이다.

### 5. read repair와의 차이

read repair는 읽은 뒤 고치는 것이고, 이 문서의 핵심은 읽기 전에 소스를 선택하는 것이다.  
둘은 같이 써야 한다.

## 실전 시나리오

### 시나리오 1: 캐시는 새 값, replica는 옛 값

서로 다른 요청이 캐시와 replica를 각각 읽으면 페이지마다 값이 달라진다.

### 시나리오 2: 캐시 만료 직후 replica lag가 심함

캐시 miss가 나면 replica로 갔는데, 아직 최신 write가 적용되지 않았다.  
사용자는 업데이트가 사라진 것처럼 느낀다.

### 시나리오 3: invalidation 순서가 뒤집힘

write 후 invalidation이 늦게 도착하면, 캐시가 옛 값을 다시 살아나게 보일 수 있다.

## 코드로 보기

```java
if (ctx.hasRecentWrite()) {
    return primaryDataSource;
}

User cached = cache.get(userId);
if (cached != null && cached.getVersion() >= minAcceptedVersion) {
    return cached;
}

return replicaDataSource.query(userId);
```

```text
bad:
  cache -> stale
  replica -> stale
  app chooses randomly

good:
  app chooses source by freshness rule
```

캐시와 replica는 둘 다 최종 진실원이 아니므로, **버전과 최근 write 신호로 같이 다뤄야 한다**.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| cache only | 빠르다 | stale 가능성 높다 | 읽기 우선 |
| replica only | 캐시보다 신뢰적일 수 있다 | lag가 있다 | 정합성 중간 |
| cache + replica with version check | 안전하다 | 복잡하다 | 중요한 조회 |
| primary fallback | 가장 안전하다 | 부하가 늘어난다 | 최신성 민감 경로 |

## 꼬리질문

> Q: cache와 replica가 동시에 있으면 왜 더 위험한가요?
> 의도: 서로 다른 stale source가 생기는 문제를 아는지 확인
> 핵심: 둘 다 옛 값을 가질 수 있고, 서로 다른 시점이 섞인다

> Q: invalidation만으로 충분한가요?
> 의도: 비동기 invalidation과 lag의 한계를 아는지 확인
> 핵심: 아니다, freshness 라우팅과 version 확인이 필요하다

> Q: 캐시 miss면 무조건 replica로 가면 되나요?
> 의도: miss를 최신성 보장으로 오해하지 않는지 확인
> 핵심: 최근 write가 있으면 primary fallback이 더 안전하다

## 한 줄 정리

Cache와 replica가 갈라지면 둘 다 stale source가 될 수 있어서, 최근 write와 version 기준으로 읽기 소스를 선택해야 한다.
