# System Design Foundations

> 한 줄 요약: 로드밸런서, stateless app, cache, database, queue가 각각 어떤 병목을 줄이고 왜 함께 쓰이는지 설명하는 입문 문서다.

retrieval-anchor-keywords: system design foundations, load balancer basics, cache basics, database basics, queue basics, stateless app, stateless service, horizontal scaling intuition, vertical scaling, scale out, source of truth, primary replica, background worker, sticky session, external session store, token-based auth, stateless sessions primer, request path failure modes, failure absorption basics, cache outage basics, queue outage basics, app instance failure basics, database outage basics, cache hit miss, async processing, beginner system design

**난이도: 🟢 Beginner**

관련 문서:

- [시스템 설계 면접 프레임워크](./system-design-framework.md)
- [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Job Queue 설계](./job-queue-design.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
- [인덱스와 실행 계획](../database/index-and-explain.md)
- [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)

---

## 핵심 개념

초보자가 system design에서 가장 많이 헷갈리는 지점은 "왜 박스가 이렇게 많은가"다.  
대부분의 기본 구조는 아래 다섯 박스를 각자 다른 이유로 둔다.

- Load Balancer: 여러 앱 인스턴스로 요청을 나눈다.
- Stateless App: 앱 인스턴스를 쉽게 늘리고 교체할 수 있게 만든다.
- Cache: 반복 읽기를 빠르게 처리해 DB 부담을 줄인다.
- Database: 정답 데이터와 내구성을 책임진다.
- Queue: 느린 후처리를 요청 경로 밖으로 밀어낸다.

이 다섯 개는 서로 대체재가 아니라, **각기 다른 병목을 줄이는 역할 분담**에 가깝다.

대표 요청 경로를 아주 단순하게 그리면 아래와 같다.

```text
Client
  -> Load Balancer
      -> Stateless App
           -> Cache
           -> Database
           -> Queue -> Worker
```

여기서 핵심은 다음이다.

- 사용자 응답은 보통 `Load Balancer -> App -> Cache/DB` 경로에서 끝난다.
- 이메일 발송, 썸네일 생성, 웹훅 전송 같은 느린 일은 `Queue -> Worker`로 뺀다.
- 수평 확장은 보통 app과 worker부터 쉽고, database는 가장 신중하게 다뤄야 한다.

이 기본 경로에서 "cache가 죽으면 어디가 먼저 맞고, app instance가 죽으면 누가 먼저 가려 주는가"를 이어서 보고 싶다면 [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)로 넘어가면 된다.

---

## 깊이 들어가기

### 1. Vertical Scaling과 Horizontal Scaling

확장 방식은 크게 두 가지다.

| 방식 | 의미 | 장점 | 한계 |
|---|---|---|---|
| Vertical Scaling | 더 큰 서버 1대로 키운다 | 단순하고 빠르다 | 장비 한계와 단일 장애점이 있다 |
| Horizontal Scaling | 서버 수를 늘린다 | 탄력성과 가용성이 좋아진다 | 분산 설계가 필요하다 |

초기 서비스는 vertical scaling으로 버티는 경우가 많다.  
하지만 트래픽이 커질수록 "한 대를 더 크게"보다 "여러 대로 나누기"가 필요해진다.

그래서 system design의 기본 그림은 자연스럽게 수평 확장을 전제로 한다.

### 2. Load Balancer는 무엇을 해결하나

로드밸런서는 들어오는 요청을 건강한 앱 인스턴스들로 분산한다.

- 인스턴스 1대가 죽어도 다른 인스턴스로 우회할 수 있다.
- 앱 서버를 2대, 4대, 10대로 늘릴 수 있다.
- health check로 비정상 인스턴스를 제외할 수 있다.

즉, 앱을 여러 대 두겠다면 load balancer는 거의 필수다.

초보자 관점의 중요한 주의점은 `sticky session`이다.

- 세션을 앱 메모리에만 두면 요청이 항상 같은 인스턴스로 가야 한다.
- 그러면 인스턴스 추가, drain, failover가 불편해진다.
- 그래서 session을 외부 저장소로 빼거나, 토큰 기반으로 stateless하게 만드는 방향을 자주 택한다.
- 이 판단을 sticky session, external session store, token-based auth 관점에서 비교한 입문 정리는 [Stateless Sessions Primer](./stateless-sessions-primer.md)에서 이어진다.

health check, drain, sticky affinity가 deploy와 failover를 어떻게 꼬이게 만드는지 먼저 잡고 싶다면 [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)를 보고, control plane 관점의 심화는 [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)과 [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)를 이어서 보면 된다.

### 3. Stateless App은 왜 중요한가

stateless app은 "상태가 아예 없다"는 뜻이 아니다.  
정확히는 **특정 인스턴스 메모리에만 중요한 사용자 상태가 묶여 있지 않다**는 뜻이다.

예를 들면:

- 로그인 세션은 외부 session store나 signed token에 둔다.
- 업로드 파일은 로컬 디스크가 아니라 object storage에 둔다.
- 주문 상태는 앱 메모리가 아니라 database에 기록한다.

이렇게 해야 앱 인스턴스가 아래처럼 행동할 수 있다.

- 언제든 새 인스턴스를 추가한다.
- 장애 난 인스턴스를 버리고 새로 띄운다.
- 배포 중에 인스턴스를 순차 교체한다.

반대로 인스턴스 로컬 메모리에 중요한 상태를 오래 들고 있으면 app tier는 사실상 stateful에 가까워지고, horizontal scaling이 급격히 어려워진다.

세션을 어디까지 stateless하게 둘지 고민된다면 먼저 [Stateless Sessions Primer](./stateless-sessions-primer.md)로 기본 선택지를 잡고, 운영 심화는 [Session Store Design at Scale](./session-store-design-at-scale.md)로 이어서 보면 좋다.

### 4. Cache는 무엇을 줄여 주나

캐시는 "자주 읽는 데이터를 더 빨리 주는 임시 저장소"다.

가장 기본적인 흐름은 아래다.

1. app이 cache를 먼저 본다
2. 값이 있으면 바로 응답한다
3. 값이 없으면 DB에서 읽는다
4. 읽은 값을 cache에 채운다

여기서 cache hit와 miss가 갈린다.

- cache hit: 빠르고 DB를 안 친다
- cache miss: 느리고 DB 부하가 생긴다

캐시를 두는 가장 흔한 이유는 DB read 병목 완화다.

- 인기 상품 상세
- 사용자 프로필
- 설정값
- 랭킹 일부

하지만 캐시는 source of truth가 아니다.

- 값이 오래되었을 수 있다
- TTL이 지나면 사라질 수 있다
- 장애가 나면 원본 DB로 돌아가야 한다

즉, cache는 "정확함"보다 "빠른 재사용"을 담당한다.  
더 깊은 설계는 [분산 캐시 설계](./distributed-cache-design.md)에서 stampede, invalidation, hot key까지 이어진다.

### 5. Database는 왜 가장 신중하게 스케일하나

database는 대개 시스템의 source of truth다.

- 주문, 결제, 사용자, 재고 같은 핵심 상태를 저장한다
- transaction, durability, index를 제공한다
- 정합성과 복구 기준점을 만든다

초보자에게 중요한 감각은 이거다.

- app은 복제해서 늘리기 쉽다
- worker도 복제해서 늘리기 쉽다
- cache도 어느 정도는 복제와 분산이 쉽다
- database는 상태를 들고 있어서 가장 어렵다

그래서 DB가 힘들어질 때는 보통 이런 순서로 생각한다.

1. 불필요한 읽기를 cache로 줄일 수 있는가
2. read replica로 읽기를 분산할 수 있는가
3. index와 query를 먼저 고칠 수 있는가
4. 그래도 안 되면 partitioning이나 sharding이 필요한가

즉, DB 확장은 "서버만 더 붙이면 끝"이 아니라 데이터 모델과 정합성 비용을 같이 봐야 한다.

### 6. Queue는 어떤 문제에 쓰나

queue는 모든 작업을 빠르게 만드는 도구가 아니다.  
대신 **지금 바로 끝낼 필요 없는 느린 작업을 요청 경로에서 분리**하는 데 강하다.

대표 예시:

- 이메일 발송
- 이미지/비디오 후처리
- 웹훅 호출
- 검색 인덱싱
- 분석 이벤트 집계

기본 흐름:

1. 사용자의 요청은 DB에 핵심 상태만 저장한다
2. app은 "나중에 처리할 일"을 queue에 넣는다
3. worker가 queue에서 꺼내 비동기로 처리한다

이 구조의 장점은 다음과 같다.

- 사용자 응답 시간이 짧아진다
- burst를 buffer처럼 흡수할 수 있다
- 실패한 작업을 retry하기 쉽다
- 외부 API 지연이 요청 경로를 덜 오염시킨다

대신 queue를 넣는 순간 eventual consistency를 받아들여야 할 때가 많다.  
"주문 생성 후 확인 메일"은 늦어도 되지만, "결제 승인 결과"는 보통 요청 안에서 명확해야 한다.

이 흐름을 더 깊게 파고들면 [Job Queue 설계](./job-queue-design.md)로 이어진다.

### 7. 수평 확장 intuition: 어디부터 늘리나

트래픽이 증가했다고 해서 모든 박스를 동시에 키우지는 않는다.  
보통은 **먼저 터지는 병목에 맞는 레버**를 고른다.

| 증상 | 먼저 보는 레버 | 이유 |
|---|---|---|
| app CPU가 높다 | stateless app 인스턴스를 늘린다 | app tier는 복제가 가장 쉽다 |
| DB read가 많다 | cache, read replica를 본다 | 같은 읽기를 반복하지 않게 만든다 |
| 외부 API 때문에 p95가 느리다 | queue로 비동기화한다 | 느린 후처리를 요청 경로에서 뺀다 |
| 특정 인스턴스에 세션이 묶인다 | 상태를 외부화한다 | load balancer가 자유롭게 분산할 수 있어야 한다 |
| DB write가 한계다 | schema, index, partitioning을 검토한다 | stateful tier는 마지막이 제일 어렵다 |

이 표가 주는 감각은 단순하다.

- app scaling은 비교적 기계적이다
- cache는 DB read를 덜어 준다
- queue는 응답 경로를 가볍게 만든다
- DB scaling은 가장 비싸고 위험하다

그래서 많은 시스템이 "LB + stateless app + cache + DB + queue" 조합으로 시작한다.

### 8. 한 번에 그림으로 이해하기

예를 들어 상품 상세 페이지를 설계한다고 하자.

```text
사용자 요청
  -> Load Balancer
  -> App
      -> product cache 조회
      -> miss면 DB 조회
      -> 응답 반환
      -> 조회 로그/추천 이벤트는 queue 적재

Worker
  -> queue 소비
  -> 분석 적재, 추천 재계산, 알림 처리
```

이 구조에서 트래픽이 5배 늘면 보통 이렇게 움직인다.

1. app 인스턴스를 먼저 늘린다
2. cache hit ratio를 높여 DB read를 줄인다
3. queue worker를 늘려 비동기 backlog를 따라잡는다
4. 그래도 DB가 버거우면 replica, index, partition을 검토한다

즉, horizontal scaling은 "모든 것을 무작정 복제"가 아니라, **복제 가능한 tier부터 먼저 늘리고 stateful tier는 보호하는 전략**에 가깝다.

### 9. 초보자가 자주 하는 오해

- load balancer를 넣는다고 DB까지 자동으로 확장되지는 않는다
- cache는 빠르지만 틀릴 수 있고, DB는 느릴 수 있지만 기준 데이터다
- queue는 저장소 대체재가 아니라 흐름 제어 장치다
- stateless는 "state 없음"이 아니라 "인스턴스에 상태를 묶지 않음"이다
- horizontal scaling은 app tier에서 쉬워도 database tier에서는 훨씬 어렵다

---

## 면접에서 이렇게 설명하면 출발이 좋다

기본 구조를 아주 짧게 설명할 때는 아래 순서가 안전하다.

1. load balancer 뒤에 stateless app 여러 대를 둔다
2. 반복 읽기는 cache로 줄인다
3. 핵심 데이터는 DB가 source of truth가 된다
4. 느린 후처리는 queue와 worker로 뺀다
5. scale-out은 app과 worker부터 하고, DB는 replica와 data model까지 신중히 본다

이 다섯 줄만 분명해도 beginner 답변의 뼈대는 상당히 안정적이다.

## 꼬리질문

> Q: 왜 stateless app이 horizontal scaling에 유리한가요?
> 의도: app tier를 복제 가능한 구조로 만드는 이유 이해 확인
> 핵심: 특정 인스턴스에 사용자 상태가 묶이지 않아 인스턴스를 쉽게 추가/교체할 수 있기 때문이다.

> Q: cache가 있는데 왜 DB가 여전히 필요한가요?
> 의도: source of truth와 최적화 계층의 차이 이해 확인
> 핵심: cache는 빠른 임시 복사본이고, DB가 정합성과 내구성을 책임지기 때문이다.

> Q: queue는 언제 넣어야 하나요?
> 의도: 동기 처리와 비동기 처리 경계 이해 확인
> 핵심: 사용자 응답을 기다릴 필요가 없는 느린 작업을 분리할 때 넣는다.

> Q: DB를 앱처럼 그냥 여러 대 복제하면 안 되나요?
> 의도: stateful tier 확장 난이도 이해 확인
> 핵심: 데이터 정합성, write coordination, replication lag 때문에 app tier보다 훨씬 어렵다.

## 한 줄 정리

System design의 기초는 박스 이름을 외우는 것이 아니라, load balancer는 분산, stateless app은 복제 가능성, cache는 읽기 절감, DB는 정합성, queue는 비동기화를 담당한다는 역할 감각을 잡는 데 있다.
