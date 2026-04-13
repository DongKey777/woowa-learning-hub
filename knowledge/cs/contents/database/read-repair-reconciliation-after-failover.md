# Read Repair와 Failover Reconciliation

> 한 줄 요약: failover가 끝난 뒤에는 읽기 경로를 바로잡는 것만큼, 이미 갈라진 데이터를 다시 맞추는 작업이 중요하다.

관련 문서: [Failover Promotion과 Read Divergence](./failover-promotion-read-divergence.md), [Replication Failover and Split Brain](./replication-failover-split-brain.md), [Replica Read Routing Anomalies와 세션 일관성](./replica-read-routing-anomalies.md)
Retrieval anchors: `read repair`, `reconciliation`, `failover recovery`, `divergence scan`, `version check`

## 핵심 개념

Read repair는 읽을 때 divergence를 발견하고 바로잡는 패턴이다.  
Failover reconciliation은 failover 이후 이미 생긴 불일치를 배치나 검사로 정리하는 작업이다.

왜 중요한가:

- failover 직후 일부 데이터가 old primary, new primary, cache, search index 사이에 갈라질 수 있다
- 읽기 경로만 고쳐도 과거에 이미 생긴 불일치는 남을 수 있다
- 운영자는 “지금은 정상”과 “이미 틀어진 데이터가 남음”을 분리해서 봐야 한다

즉 failover 복구는 라우팅 전환으로 끝나지 않고, **잔여 불일치 정리**까지 포함한다.

## 깊이 들어가기

### 1. read repair가 필요한 이유

혼합 라우팅이나 lag 때문에 어떤 요청은 오래된 값을 보았을 수 있다.

- 캐시가 옛 버전을 저장
- 검색 인덱스가 늦게 갱신
- replica가 잠깐 뒤처진 값을 읽음

이때 읽기 시점에 버전 비교를 하고, 더 새로운 값으로 고치는 작업이 read repair다.

### 2. reconciliation이 왜 별도인가

read repair는 보통 요청 경로에서 일부 문제를 바로 잡는 반면, reconciliation은 시스템 전체를 훑는다.

- primary와 replica의 version 비교
- cache와 DB 비교
- read model과 write model 비교

failover 직후에는 한 번의 read repair로는 부족할 수 있다.

### 3. 어떤 데이터를 재검증해야 하나

우선순위는 보통 다음과 같다.

- 결제 상태
- 주문 상태
- 권한/멤버십
- 재고/예약

정합성이 중요한 데이터부터 version 기반 재검증을 수행해야 한다.

### 4. repair의 위험

- 옛 값이 authoritative source를 덮을 수 있다
- repair job 자체가 대량 트래픽을 일으킬 수 있다
- version 비교 없이 덮어쓰면 데이터 손상이 더 커질 수 있다

그래서 repair는 반드시 **버전 비교 + 단일 진실원**을 기준으로 해야 한다.

## 실전 시나리오

### 시나리오 1: failover 후 검색 결과와 DB 상태가 다름

DB는 정상인데 검색 인덱스가 옛 상태면, 사용자는 데이터가 사라진 것으로 느낀다.  
이때 reconciliation job으로 search index를 다시 맞춰야 한다.

### 시나리오 2: 캐시가 오래된 주문 상태를 품고 있음

failover 전 읽은 캐시가 살아있으면, 새 primary와 다른 상태를 보여준다.  
read repair가 필요하다.

### 시나리오 3: 일부 레코드만 옛 primary에 남아 있음

잘못된 failover 또는 지연된 write로 일부 row가 갈라졌다면, version diff scan으로 재동기화해야 한다.

## 코드로 보기

```sql
-- 버전 비교 후 더 새로운 쪽을 authoritative source로 선택
SELECT id, status, version
FROM orders
WHERE id = 9001;
```

```java
if (cacheVersion < dbVersion) {
    cache.put(orderId, dbValue);
}
```

```text
repair flow:
  detect divergence -> choose source of truth -> update stale projection
```

read repair는 “읽다가 고친다”이고, reconciliation은 “한 번 훑고 정리한다”다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| read repair | 즉시성 좋음 | 요청 경로가 무거워질 수 있다 | 자주 읽는 핵심 데이터 |
| reconciliation job | 전체 정리가 가능 | 배치 지연이 있다 | failover 이후 정리 |
| full rebuild | 단순하다 | 비용이 크다 | 불일치가 광범위할 때 |
| 버전 기반 부분 repair | 효율적이다 | 버전 관리가 필요하다 | 대부분의 운영 케이스 |

## 꼬리질문

> Q: failover 뒤에 왜 read repair가 필요한가요?
> 의도: 라우팅 전환만으로는 오래된 projection이 남을 수 있음을 아는지 확인
> 핵심: 읽기 경로와 저장된 파생 데이터는 따로 틀어질 수 있다

> Q: reconciliation과 read repair의 차이는 무엇인가요?
> 의도: 즉시 수정과 전체 스캔 정리를 구분하는지 확인
> 핵심: read repair는 요청 경로, reconciliation은 배치/점검 경로다

> Q: repair할 때 가장 중요한 안전장치는 무엇인가요?
> 의도: 덮어쓰기 손상을 막는 기준을 아는지 확인
> 핵심: 단일 진실원과 version 비교다

## 한 줄 정리

Failover 이후에는 읽기 라우팅을 고치는 것뿐 아니라, 이미 갈라진 캐시와 projection을 version 기반으로 다시 맞추는 reconciliation이 필요하다.
