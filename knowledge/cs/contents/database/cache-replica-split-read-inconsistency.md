# Cache와 Replica가 갈라질 때의 Read Inconsistency

> 한 줄 요약: 캐시와 replica가 서로 다른 시점을 들고 있으면, 둘 중 어느 쪽을 읽어도 맞는 것 같지만 둘 다 틀릴 수 있다.

관련 문서: [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md), [Replica Lag and Read-after-write Strategies](./replica-lag-read-after-write-strategies.md), [Read Repair와 Failover Reconciliation](./read-repair-reconciliation-after-failover.md)
Retrieval anchors: `cache replica split`, `stale cache`, `mixed source of truth`, `read inconsistency`, `cache invalidation`

## 핵심 개념

캐시는 빠르지만 오래된 값을 줄 수 있고, replica는 최신성이 더 좋을 수 있지만 lag가 있다.  
둘이 동시에 쓰이면 사용자는 같은 화면에서 서로 다른 진실을 볼 수 있다.

왜 중요한가:

- 캐시와 DB replica가 서로 다른 시간축에 있을 수 있다
- 어떤 요청은 캐시, 어떤 요청은 replica를 타면 결과가 뒤집힌다
- invalidation만으로는 항상 해결되지 않는다

즉 문제는 캐시가 있느냐가 아니라, **어느 소스가 최신인지 라우팅이 알고 있느냐**다.

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

### 3. 해결 방향

- 최근 write는 primary fallback
- cache miss 시 replica 직행이 아니라 freshness 확인
- version token으로 cache와 DB 버전 비교
- invalidate 후 바로 read가 필요한 경로는 primary pinning

핵심은 캐시와 replica를 **서로 다른 stale source**로 본다는 점이다.

### 4. read repair와의 차이

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
