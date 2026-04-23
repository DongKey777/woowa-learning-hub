# Read-After-Write Routing Primer

> 한 줄 요약: read-after-write routing은 write 직후 읽기를 무심코 replica로 보내지 않고, primary fallback, session pinning, monotonic reads로 필요한 경로만 더 신선한 read path에 태우는 입문 설계 문서다.

retrieval-anchor-keywords: read-after-write routing primer, read your writes routing, primary fallback routing, session pinning primer, recent-write pinning, monotonic reads primer, monotonic read guarantee, replica unsafe after write, post-write replica read unsafe, write then read routing, freshness routing basics, read-after-write policy, session consistency routing, order confirmation stale read, permission change freshness, mixed cache replica routing, cache boundary pinning, cache hit miss refill bridge, freshness context routing, beginner consistency routing

**난이도: 🟢 Beginner**

관련 문서:

- [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
- [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
- [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- [Replica Lag and Read-after-write Strategies](../database/replica-lag-read-after-write-strategies.md)
- [Read-Your-Writes와 Session Pinning 전략](../database/read-your-writes-session-pinning.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)

---

## 핵심 개념

read-after-write 문제는 "replica가 있느냐"보다 **write 직후의 read를 어디로 보낼 것인가**의 문제다.

아래처럼 write는 primary에서 끝나고, 다음 read는 replica로 나간다고 해 보자.

```text
POST /orders        -> primary commit
302 redirect        -> /orders/123
GET  /orders/123    -> replica

primary commit은 끝났지만
replica apply가 아직 안 끝났다면
사용자는 방금 만든 주문을 못 본다
```

이때 초보자가 먼저 구분해야 할 단어는 네 개다.

- primary fallback: 최신성이 중요한 read만 잠깐 primary로 보내는 방식
- session pinning: 최근 write한 세션의 read를 일정 시간 더 신선한 경로에 붙이는 방식
- monotonic reads: 한 세션이 이미 본 최신 버전보다 더 오래된 결과로 다시 내려가지 않게 하는 보장
- unsafe replica read: write 직후 stale이 나왔을 때 UX를 넘어서 중복 행동, 금전 사고, 보안 공백으로 이어지는 경우

핵심은 이것이다.

- replica default 자체가 문제는 아니다
- 문제는 **write 직후에도 아무 정책 없이 replica를 읽게 두는 것**이다
- 그래서 실전에서는 경로별로 read routing 규칙을 둔다

---

## 깊이 들어가기

### 1. 왜 "쓰기 성공"과 "다음 읽기 최신"은 같은 말이 아닌가

사용자는 보통 이렇게 기대한다.

1. 저장 버튼을 눌렀다
2. 성공 응답을 받았다
3. 다음 화면에서 새 값이 보여야 한다

하지만 시스템 내부에서는 아래가 분리될 수 있다.

1. primary commit 완료
2. app이 성공 응답 반환
3. replica로 복제 전파
4. 다음 read가 어느 노드를 읽을지 결정

즉, write가 성공해도 다음 read가 random replica로 가면 stale이 보일 수 있다.
read-after-write 문제는 종종 DB 저장 실패가 아니라 **라우팅 실패**처럼 드러난다.

### 2. Primary fallback은 가장 단순한 보호 장치다

가장 쉬운 방법은 "모든 read를 primary로 보내자"가 아니라, **틀리면 안 되는 read만 primary로 보낸다**는 것이다.

대표 예:

- 주문 생성 직후 주문 상세
- 결제 완료 직후 영수증/확인 화면
- 재고 예약 직후 구매 가능 여부 재확인
- 권한 변경 직후 접근 제어 확인

장점:

- 이해하기 쉽다
- 빠르게 stale read를 줄일 수 있다
- endpoint 단위로 정책을 합의하기 쉽다

단점:

- primary read 부하가 늘어난다
- fallback 범위가 넓어지면 replica의 이점이 줄어든다
- "안전하게 보이니 다 primary로"가 되면 읽기 확장 구조가 무너진다

그래서 primary fallback은 보통 **짧고 좁게** 쓴다.

### 3. Session pinning은 "최근 writer만 잠깐 보호"하는 방식이다

모든 사용자를 primary로 보내지 않고, 최근 write한 세션만 일정 시간 더 신선한 경로에 태우는 전략이다.

예를 들면:

- 최근 3초 안에 write한 사용자만 primary read
- 특정 주문 ID를 만든 사용자만 그 주문 조회를 primary로 pinning
- 같은 leader/region에서 follow read가 가능한 동안 그 경로로 유지

여기서 중요한 점은 session pinning이 항상 "primary 고정"만 뜻하지는 않는다는 점이다.
의미는 **그 세션이 stale 가능성이 낮은 경로를 계속 읽게 하는 것**에 가깝다.

또 하나 자주 헷갈리는 점:

- load balancer sticky session: 같은 app 인스턴스로 보내는 것
- read-after-write session pinning: 더 신선한 DB read path로 보내는 것

둘은 목적이 다르다.
이 차이는 [Stateless Sessions Primer](./stateless-sessions-primer.md)와 함께 보면 덜 헷갈린다.

### 4. Monotonic reads는 "한 번 본 최신값보다 뒤로 가지 않기"다

read-your-writes와 monotonic reads는 비슷해 보이지만 질문이 다르다.

| 보장 | 질문 | 예시 |
|---|---|---|
| Read-your-writes | 내가 방금 쓴 값이 다음 읽기에서 보이는가 | 프로필 저장 후 새 닉네임 확인 |
| Monotonic reads | 내가 이미 본 최신값보다 나중 읽기가 더 오래된 값으로 내려가지 않는가 | 주문 상세에서 `PAID`를 봤는데 목록에서 다시 `PENDING`이 보이지 않게 함 |

monotonic reads가 필요한 이유는 세션이 여러 화면을 오갈 때 random replica를 읽으면 **값이 뒤집혀 보일 수 있기 때문**이다.

```text
GET /orders/123 (primary) -> status=PAID
GET /orders     (replica) -> status=PENDING
```

이 상황에서 사용자는 "결제가 취소됐나?"라고 오해할 수 있다.

실전에서는 보통 아래 중 하나로 단순화한다.

- 최근에 본 version/LSN/timestamp보다 뒤처진 replica는 피한다
- 추적이 어렵다면 해당 세션을 잠깐 primary에 pinning한다

즉, monotonic reads는 **세션 관점에서 시간이 거꾸로 흐르지 않게 하는 규칙**이다.

### 5. write 직후 replica read가 특히 위험한 구간이 있다

모든 stale read가 같은 비용을 만들지는 않는다.
초보자는 "얼마나 최신해야 하는가"보다 먼저 **틀렸을 때 어떤 사고가 나는가**를 봐야 한다.

| 구간 | replica stale 위험도 | 왜 위험한가 | 흔한 선택 |
|---|---|---|---|
| 결제 완료 직후 주문 확인 | 매우 높음 | 사용자가 중복 결제를 시도할 수 있다 | primary fallback |
| 재고 예약/좌석 선점 직후 확인 | 매우 높음 | oversell, double booking으로 이어질 수 있다 | source of truth read, strong path |
| 권한 제거/역할 변경 직후 검사 | 매우 높음 | 보안 경계가 잠깐 열릴 수 있다 | primary read, stricter check |
| 생성 직후 상세 페이지 redirect | 높음 | 사용자는 저장 실패로 오해하고 재시도한다 | endpoint fallback or pinning |
| 프로필/설정 저장 직후 내 화면 | 중간 | 금전 사고는 아니어도 UX 신뢰가 깨진다 | short session pinning |
| 피드/검색/통계 카운터 | 낮음 | 약간 stale해도 큰 사고로 잘 이어지지 않는다 | replica or cache default |

정리하면, "write 직후 replica read가 unsafe한가?"라는 질문은 결국 **이 stale이 사용자를 어떤 잘못된 행동으로 밀어 넣는가**를 보는 질문이다.

### 6. 가장 단순한 routing ladder는 이렇게 시작한다

복잡한 글로벌 consistency 설계 전에, 많은 팀은 아래 정도의 규칙부터 둔다.

```pseudo
function routeRead(endpoint, key, session):
  if endpoint.requiresFreshRead():
    return primary

  if session.hasRecentWrite(key, within=3 seconds):
    return primary

  if session.lastSeenVersion(key) > replica.visibleVersion(key):
    return primary

  return replica
```

이 정책이 담고 있는 뜻은 단순하다.

1. endpoint 자체가 위험하면 primary fallback
2. 방금 write한 세션이면 session pinning
3. 이미 본 최신값보다 뒤처질 수 있으면 monotonic 보호
4. 나머지는 replica default

여기서 `3초` 같은 숫자는 정답이 아니라 시작점이다.
실전에서는 replica lag 분포, endpoint 중요도, primary headroom을 같이 보고 조정한다.
앞단에 cache가 있으면 이 routing ladder가 cache miss 경계에서 끊기지 않아야 하고, miss 뒤 replica 결과를 다시 cache에 채울 때도 같은 freshness contract를 적용해야 한다. hit/miss/refill 전체에 `recent-write`, `min-version`, `causal token`을 어떻게 들고 가는지는 [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)에서, mixed path의 pitfall과 observability는 [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)에서 이어서 다룬다.

### 7. 흔한 실수

`read-after-write가 문제니 모든 GET을 primary로 보내자`

- 너무 넓다. 최신성이 중요한 경로만 보호해야 read scaling 이점이 남는다.

`session pinning이면 무조건 load balancer sticky session이다`

- 아니다. app 인스턴스 affinity와 DB freshness routing은 다른 문제다.

`평균 replica lag가 짧으니 괜찮다`

- 평균이 아니라 redirect 직후와 tail lag에서 제품 문제가 드러난다.

`monotonic reads는 read-your-writes가 있으면 자동으로 해결된다`

- 아니다. 내가 쓰지 않은 데이터라도 이미 본 더 최신 상태에서 다시 뒤로 가는 문제는 남는다.

---

## 실전 시나리오

### 시나리오 1: 주문 생성 직후 상세 페이지

- `POST /orders`는 primary에서 성공했다
- 바로 `GET /orders/{id}`가 replica로 가면 404나 오래된 상태가 나올 수 있다

이 구간은 endpoint-level primary fallback이 가장 단순하다.

### 시나리오 2: 프로필 저장 후 여러 화면 이동

- 상세 화면에서는 새 닉네임을 봤다
- 다음 목록 화면이 오래된 replica를 읽어 이전 닉네임을 보여 준다

이 구간은 read-your-writes만으로는 부족할 수 있고, monotonic reads나 짧은 session pinning이 잘 맞는다.

### 시나리오 3: 권한 제거 직후 접근 체크

- admin 권한을 제거했다
- 다음 권한 체크가 lagging replica를 읽으면 잠깐 예전 권한이 살아 있을 수 있다

이 구간은 일반 UX inconsistency가 아니라 보안 경계라서 replica default를 두기 어렵다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 잘 맞는 경우 |
|---|---|---|---|
| Replica default | 빠르고 확장성이 좋다 | write 직후 stale이 잘 드러난다 | 검색, 피드, 통계 |
| Primary fallback | 구현과 설명이 단순하다 | primary read 부하가 늘어난다 | 주문 확인, 권한 확인 |
| Session pinning | 최근 writer만 좁게 보호한다 | 세션 상태나 TTL 관리가 필요하다 | 저장 후 redirect UX |
| Monotonic reads | 값이 뒤집혀 보이는 경험을 줄인다 | version/LSN 추적이 필요할 수 있다 | 상세-목록 왕복, 다단계 확인 흐름 |

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> read-after-write routing은 write 직후 read를 아무 replica로나 보내지 않는 설계입니다.  
> 최신성이 중요한 endpoint는 primary fallback으로 보호하고, 최근 write한 세션은 짧게 pinning해서 read-your-writes를 맞춥니다.  
> 또 사용자가 이미 본 최신 상태보다 뒤로 가지 않게 하려면 monotonic reads도 같이 봐야 하고, 결제·재고·권한처럼 틀렸을 때 비용이 큰 경로는 write 직후 replica read를 unsafe로 취급하는 편이 맞습니다.

## 꼬리질문

> Q: session pinning과 monotonic reads는 같은 말인가요?  
> 의도: 라우팅 수단과 세션 보장을 구분하는지 확인  
> 핵심: session pinning은 구현 전략이고, monotonic reads는 세션이 이미 본 최신값보다 뒤로 가지 않게 하는 보장이다.

> Q: 왜 평균 replica lag가 짧아도 문제가 되나요?  
> 의도: 사용자 흐름 기준 tail risk를 보는지 확인  
> 핵심: redirect 직후 확인 화면은 작은 lag도 바로 노출하고, 결제/권한 흐름에서는 짧은 stale도 큰 사고가 될 수 있다.
