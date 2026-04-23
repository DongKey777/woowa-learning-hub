# Read / Write Quorum & Staleness Budget 설계

> 한 줄 요약: read/write quorum과 staleness budget 설계는 분산 저장소에서 읽기·쓰기 응답성과 정합성, 장애 허용성을 균형 있게 맞추기 위해 quorum 크기와 허용 stale 범위를 명시하는 consistency management 설계다.

retrieval-anchor-keywords: read quorum, write quorum, staleness budget, bounded staleness, read repair, hinted handoff, leaderless replication, consistency level, quorum tradeoff, read your writes budget

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Consensus Membership Reconfiguration 설계](./consensus-membership-reconfiguration-design.md)

## 핵심 개념

분산 저장소에서는 "항상 최신을 읽는다"와 "항상 빠르게 읽는다"를 동시에 100% 보장하기 어렵다.
그래서 실전 설계는 다음을 숫자로 정한다.

- 쓰기를 몇 개 replica에 확인받을 것인가
- 읽기를 몇 개 replica에서 확인할 것인가
- 얼마나 stale한 결과를 허용할 것인가
- 어떤 경로는 read-your-writes가 필요한가
- drift를 나중에 어떻게 repair할 것인가

즉, consistency는 추상 철학이 아니라 **quorum과 staleness budget을 운영 계약으로 명시하는 일**이다.

## 깊이 들어가기

### 1. 왜 staleness budget이 중요한가

많은 시스템이 "eventual consistency"라고만 말하고 끝난다.
하지만 실전에서는 이 질문이 더 중요하다.

- 500ms stale은 괜찮은가
- 5초 stale은 괜찮은가
- tenant 설정은 1분 stale이 허용되는가
- 결제 상태는 stale이 전혀 안 되는가

즉, eventual이라는 단어 대신 **허용 가능한 stale 범위**를 정해야 한다.

### 2. Capacity Estimation

예:

- replica 3개
- 각 replica p95 read 8ms
- cross-zone read 25ms
- 쓰기 QPS 5만
- read-your-writes 요구는 전체 요청의 2%

이때 봐야 할 숫자:

- quorum latency
- replica lag
- stale read ratio
- repair backlog
- tail latency increase

정합성을 올릴수록 대부분 latency와 availability 비용이 따라온다.

### 3. Quorum 직관

단순화하면 다음을 생각한다.

- `N`: replica 수
- `W`: write quorum
- `R`: read quorum

`R + W > N`이면 겹치는 replica가 생겨 최신 데이터를 읽을 가능성이 높아진다.
하지만 현실은 이것만으로 끝나지 않는다.

- replica lag
- clock skew
- failed write의 partial ack
- read repair 지연

즉, 수식은 시작점이고 운영 현실이 더 중요하다.

### 4. Leader-based vs leaderless

둘은 consistency 관리 방식이 다르다.

- leader-based: write ordering이 비교적 명확
- leaderless: quorum과 repair가 더 중요

leaderless 환경에서는 특히 다음이 중요하다.

- read repair
- hinted handoff
- conflict resolution
- stale replica selection

### 5. Session guarantees

모든 요청에 강한 consistency를 강요하지 않아도,
특정 사용자 세션에는 더 강한 보장을 줄 수 있다.

대표 예:

- read-your-writes
- monotonic reads
- sticky routing
- recent-write pinning

이건 전체 cluster policy와 사용자 경험 policy를 분리하는 좋은 예다.

### 6. Bounded staleness와 fallback policy

실전에서는 "최신이 아니어도 된다"보다 "얼마까지 늦어도 된다"가 중요하다.

예:

- feature flag snapshot은 30초 stale 허용
- profile count는 5초 stale 허용
- inventory available count는 거의 stale 불가

그리고 stale 허용을 넘으면 어떻게 할지도 정해야 한다.

- stricter read quorum으로 상승
- same-region sticky read
- blocking refresh
- fail closed / fail open

### 7. Repair and observability

quorum과 stale 허용은 나중에 repair 체계와 같이 봐야 한다.

- read repair가 얼마나 자주 일어나는가
- anti-entropy backlog가 쌓이는가
- replica lag가 budget 안에 있는가
- stale read가 어떤 tenant/region에서 많은가

즉, consistency는 write path 설정이 아니라 관측과 repair를 포함한 운영 체계다.

## 실전 시나리오

### 시나리오 1: 세션 직후 프로필 조회

문제:

- 사용자가 방금 프로필을 바꿨는데 다음 화면에서 옛값이 보이면 안 된다

해결:

- 최근 쓰기한 사용자만 sticky read를 적용한다
- 전체 시스템엔 강한 read quorum을 강요하지 않는다

### 시나리오 2: 글로벌 설정 조회

문제:

- 전 세계 edge에서 읽지만 약간 stale해도 괜찮다

해결:

- bounded staleness snapshot을 사용한다
- stale budget을 넘기면 stronger refresh path로 fallback한다

### 시나리오 3: leaderless cart store

문제:

- 일부 replica가 늦게 따라와 cart read가 뒤섞인다

해결:

- read quorum을 높이거나 recent-write 세션엔 stricter policy를 둔다
- read repair와 anti-entropy를 꾸준히 돌린다

## 코드로 보기

```pseudo
function read(key, policy):
  if policy.requiresReadYourWrites():
    return readFromPinnedReplica(key)
  replicas = pickReplicas(key, policy.readQuorum)
  result = reconcile(replicas.read())
  if result.staleness > policy.stalenessBudget:
    return refreshWithStrongerQuorum(key)
  return result

function write(key, value, policy):
  acks = replicas.write(key, value)
  if acks < policy.writeQuorum:
    fail()
```

```java
public ReadResult read(Key key, ConsistencyPolicy policy) {
    ReplicaSet replicas = replicaSelector.select(key, policy.readQuorum());
    return reconciler.readAndMerge(replicas, policy.stalenessBudget());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Low quorum / high stale tolerance | 빠르고 가용성이 좋다 | 오래된 값이 보일 수 있다 | 캐시성 읽기, analytics |
| Higher quorum | 최신성이 좋아진다 | latency와 cost가 오른다 | 중요한 상태 조회 |
| Session-level stronger consistency | UX를 지킨다 | routing 복잡도 증가 | profile, session, cart |
| Full strong consistency everywhere | 이해는 쉽다 | 성능과 가용성 비용이 크다 | 매우 제한된 핵심 경로 |

핵심은 read/write quorum과 staleness budget이 DB 옵션이 아니라 **도메인별 consistency 계약을 latency, availability, repair 비용과 함께 정하는 시스템 설계 문제**라는 점이다.

## 꼬리질문

> Q: `R + W > N`이면 항상 최신을 읽나요?
> 의도: quorum 공식의 한계 이해 확인
> 핵심: 이론적으로 겹침을 만들지만, replica lag나 partial failure, conflict resolution까지 고려해야 실제로 최신 보장이 된다.

> Q: eventual consistency와 bounded staleness는 어떻게 다른가요?
> 의도: 운영 계약 수준 차이 이해 확인
> 핵심: eventual은 방향성이고, bounded staleness는 허용 가능한 지연을 숫자로 제한한 더 구체적 계약이다.

> Q: 모든 사용자에게 stronger read를 주면 더 안전하지 않나요?
> 의도: selective consistency 감각 확인
> 핵심: 안전성은 높아질 수 있지만 latency와 availability 비용이 커져, 최근 쓰기한 세션만 강화하는 전략이 더 현실적일 수 있다.

> Q: consistency 문제를 repair 시스템과 같이 봐야 하는 이유는?
> 의도: 설정과 운영의 연결 이해 확인
> 핵심: stale read와 replica drift는 결국 read repair, anti-entropy, lag 관찰을 통해 운영에서 관리되기 때문이다.

## 한 줄 정리

Read/write quorum과 staleness budget 설계는 분산 저장소의 정합성 수준을 숫자로 명시하고, latency·availability·repair 비용과 균형 있게 맞추는 consistency management 문제다.
