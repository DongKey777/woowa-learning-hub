# Request Path Failure Modes Primer

> 한 줄 요약: cache, queue, app instance, database가 고장 났을 때 요청 경로가 어디서 먼저 흔들리고 어느 레이어가 충격을 먼저 흡수하는지 설명하는 입문 문서다.

retrieval-anchor-keywords: request path failure modes, cache outage primer, queue outage primer, app instance failure primer, database outage primer, failure absorption order, graceful degradation basics, read-only mode basics, stale-if-error basics, partial feature disablement, cache miss storm, queue backlog basics, app failover basics, database failover basics, timeout budget basics

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
- [분산 캐시 설계](./distributed-cache-design.md)
- [Job Queue 설계](./job-queue-design.md)
- [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
- [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
- [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)

---

## 핵심 개념

초보자가 request path를 볼 때 자주 놓치는 점은, 시스템이 모든 장애를 같은 방식으로 다루지 않는다는 것이다.
어떤 장애는 다른 레이어가 잠깐 흡수할 수 있지만, 어떤 장애는 거의 바로 사용자 오류로 드러난다.

대표 경로를 다시 그리면 아래와 같다.

```text
Client
  -> Load Balancer
      -> App
           -> Cache
           -> Database
           -> Queue -> Worker
```

여기서 `흡수한다`는 뜻은 "완전히 고친다"가 아니다.
보통 아래 셋 중 하나를 뜻한다.

- reroute: 다른 인스턴스나 경로로 우회한다
- buffer: 잠깐 쌓아 두고 나중에 처리한다
- degrade: stale read, read-only, low-priority drop처럼 기능을 줄여 버틴다

핵심은 **고장 난 레이어 바로 위나 옆에 있는 레이어가 먼저 반응한다**는 점이다.
다만 실제로 추가 부하를 떠안는 레이어와, fallback 결정을 내리는 레이어가 같지는 않을 수 있다.

### 한눈에 보는 failure absorption map

| 고장 난 레이어 | 가장 먼저 반응하는 레이어 | 실제로 추가 충격을 주로 떠안는 레이어 | 보통 보이는 첫 증상 |
|---|---|---|---|
| cache | app | database read path | latency 상승, DB QPS 상승 |
| queue | producer app 또는 DB outbox | outbox table 또는 app boundary | async 처리 지연, backlog 증가 |
| app instance | load balancer / service discovery | 남은 app instances | 일부 inflight 실패, 이후 자동 우회 |
| database | app boundary, 일부 read cache | cached read만 cache가 흡수, write는 거의 아무도 못 흡수 | write 실패, cache miss 경로 장애 |

이 표에서 가장 중요한 감각은 이것이다.

- cache 장애는 보통 DB 압박으로 번진다
- queue 장애는 보통 async SLA 문제로 먼저 보인다
- app instance 장애는 load balancer가 먼저 가린다
- database 장애는 일부 cached read를 빼면 가장 숨기기 어렵다

---

## 깊이 들어가기

### 1. Cache가 죽으면 app이 fallback을 결정하고 DB가 부하를 맞는다

cache는 평소에는 DB read를 줄이는 완충 장치다.
반대로 cache 자체가 죽으면 app은 cache를 건너뛰고 DB로 가야 한다.

```text
평소:
Client -> LB -> App -> Cache hit -> 응답

cache 장애:
Client -> LB -> App -> Cache timeout/error
                     -> DB 조회
```

이때 first reaction은 app에서 일어난다.

- cache timeout을 짧게 끊는다
- stale entry가 있으면 잠깐 쓴다
- single-flight나 request coalescing으로 같은 miss를 묶는다

하지만 **실제 충격을 맞는 레이어는 DB**다.

- 평소 cache가 막아 주던 read가 DB로 쏟아진다
- hot key가 있으면 특정 query가 바로 튄다
- p95가 올라가고, DB CPU/connection이 먼저 흔들린다

그래서 cache 장애는 "cache만 느리다"로 끝나지 않고, 자주 **DB read amplification incident**로 커진다.

핵심 정리:

- cache는 DB failure absorber가 아니라 DB load reducer다
- cache가 죽으면 app은 우회하고, DB가 실제 비용을 낸다
- DB가 그 비용을 못 버티면 그다음은 load shedding이나 partial outage로 번진다

### 2. Queue 장애는 두 갈래로 봐야 한다

queue는 원래 worker 느림이나 burst를 흡수하는 레이어다.
하지만 "queue가 고장 났다"는 말은 두 경우로 나뉜다.

#### 2-1. Worker가 느리거나 죽었는데 queue는 살아 있다

이 경우에는 queue가 제 역할을 한다.

- producer는 계속 enqueue한다
- queue depth가 쌓인다
- worker가 복구되면 backlog를 따라잡는다

즉, **worker failure는 queue가 먼저 흡수**한다.

#### 2-2. Queue broker 자체가 죽었다

이 경우에는 queue가 더 이상 absorber가 아니다.
이제 producer 쪽이 결정해야 한다.

대표 선택지는 아래와 같다.

- app이 request를 실패시킨다
- app이 DB outbox에 intent를 저장하고 나중에 relay한다
- low-priority async는 드롭하거나 degrade한다

```text
Client -> LB -> App -> DB(order row + outbox row)
                     X queue publish 실패

later:
outbox relay -> Queue -> Worker
```

## 깊이 들어가기 (계속 2)

이 패턴에서는 **DB outbox가 queue outage를 먼저 흡수**한다.
반대로 outbox가 없고 enqueue가 필수라면, app boundary가 바로 실패를 사용자에게 드러낸다.

핵심 정리:

- queue는 worker slowdown을 흡수할 수 있다
- 하지만 queue 자체 장애는 queue가 흡수하지 못한다
- 그때는 app 또는 DB outbox가 다음 absorber가 된다

### 3. App instance가 죽으면 load balancer와 다른 replicas가 먼저 받쳐 준다

app instance failure는 네 가지 중 가장 잘 숨겨지는 편이다.
이유는 app tier가 보통 stateless하고 복제가 쉽기 때문이다.

```text
Client -> LB -> App A (dead)
       -> LB health check fail
       -> App B / App C 로 우회
```

이때 가장 먼저 반응하는 레이어는 load balancer나 service discovery다.

- health check가 죽은 인스턴스를 제외한다
- retry 가능한 요청은 다른 replica로 보낸다
- autoscaling이나 self-healing이 새 인스턴스를 띄운다

실제 트래픽을 떠안는 것은 남은 app replicas다.

- 남은 인스턴스 CPU가 오른다
- connection pool 사용량이 증가한다
- 일부 inflight request는 실패할 수 있다

그래도 stateless app이면 대체로 전체 장애로 바로 이어지지 않는다.
반대로 app 메모리에 session이나 local state가 깊게 묶여 있으면 흡수가 급격히 어려워진다.

핵심 정리:

- app instance 장애의 first absorber는 load balancer다
- app tier가 stateless할수록 다른 replicas가 자연스럽게 이어받는다
- sticky session, local-only state가 많으면 같은 장애도 훨씬 아프다

### 4. Database가 죽으면 일부 cached read만 버티고 authoritative write는 거의 바로 멈춘다

database failure가 가장 무서운 이유는 source of truth이기 때문이다.
다른 레이어는 DB를 완전히 대체하지 못한다.

```text
Client -> LB -> App -> Cache hit      -> 잠깐 성공 가능
Client -> LB -> App -> Cache miss     -> DB 실패
Client -> LB -> App -> Write request  -> DB 실패
```

여기서 살아남는 경로는 제한적이다.

## 깊이 들어가기 (계속 3)

- 이미 cache에 있는 read는 잠깐 버틸 수 있다
- read replica가 살아 있고 stale read 허용 범위가 있으면 일부 조회는 가능하다
- queue에 이미 들어간 작업 중 DB를 다시 치지 않는 side effect 일부만 잠시 계속 처리될 수 있다

하지만 아래는 대체로 바로 막힌다.

- 새로운 write
- cache miss 뒤 원본 조회
- 강한 일관성이 필요한 read

즉, database failure의 흡수는 매우 부분적이다.
정확히 말하면 **cache가 일부 read만 잠깐 흡수**하고, 나머지는 app이 fail-fast, read-only, maintenance mode로 내려야 한다.

그래서 DB 장애는 다른 장애보다 훨씬 빨리 사용자 오류로 드러난다.

핵심 정리:

- DB가 죽으면 cache는 cached read만 살려 준다
- queue는 이미 적재된 일만 처리할 뿐, 새로운 authoritative write를 대신하지 못한다
- DB 장애는 "우회"보다 "축소 운영"과 "빠른 failover"가 핵심이다

### 5. 결국 어떤 레이어가 어떤 실패를 흡수하도록 설계하는가가 중요하다

같은 아키텍처 그림이라도 장애 모드는 다르게 설계할 수 있다.
면접이나 실무 설명에서는 아래 구분이 특히 중요하다.

| 질문 | 좋은 설명의 방향 |
|---|---|
| cache 장애를 누가 받나 | app은 fallback을 결정하고 DB가 read spike를 받는다 |
| queue 장애를 누가 받나 | worker 지연은 queue가, queue broker outage는 outbox/app이 받는다 |
| app instance 장애를 누가 받나 | load balancer와 다른 replicas가 받는다 |
| DB 장애를 누가 받나 | 일부 cached read만 버티고 대부분은 fail-fast 또는 read-only다 |

이 표를 말할 수 있으면 "컴포넌트 이름 나열"에서 끝나지 않고, 실제 운영 감각이 있는 설명으로 넘어간다.

### 6. 흔한 오해

`cache가 있으니 DB가 죽어도 괜찮다`

- 아니다. cache hit만 잠깐 버틸 뿐, miss와 write는 여전히 DB가 필요하다

`queue가 있으니 장애를 다 흡수한다`

- 아니다. queue는 worker 지연에는 강하지만, queue broker 자체 장애는 별도 durable path가 있어야 버틴다

`app instance는 여러 대니까 신경 안 써도 된다`

- 아니다. health check, drain, retry budget, connection pool까지 같이 설계해야 한다

`DB failover만 있으면 애플리케이션은 그대로다`

- 아니다. failover 동안 timeout, stale read, retry amplification, read-only downgrade가 같이 따라온다

---

## 면접 답변 골격

짧게 답하면 아래 순서가 안전하다.

> app instance 장애는 load balancer와 다른 replicas가 먼저 흡수합니다.
> cache 장애는 app이 DB fallback으로 우회하고 DB read path가 충격을 받습니다.
> queue 장애는 worker slowdown이면 queue가 backlog로 흡수하고, broker outage면 app이나 DB outbox가 대신 받아야 합니다.
> database 장애는 일부 cached read만 버티고, 새로운 write와 cache miss는 거의 바로 실패하므로 가장 숨기기 어렵습니다.

## 꼬리질문

> Q: cache 장애 때 app이 아니라 DB가 absorber라고 말하는 이유는 무엇인가요?
> 의도: control plane reaction과 실제 load absorber를 구분하는지 확인
> 핵심: app이 fallback을 결정하지만, 추가 read 비용은 결국 DB가 떠안기 때문이다.

> Q: queue는 버퍼인데 왜 queue outage에서 바로 못 버티나요?
> 의도: worker slowdown과 broker outage를 구분하는지 확인
> 핵심: queue가 살아 있을 때만 버퍼 역할을 하고, queue 자체가 죽으면 producer 쪽 durable fallback이 필요하다.

> Q: app instance 장애가 비교적 쉬운 이유는 무엇인가요?
> 의도: stateless replica의 의미를 이해하는지 확인
> 핵심: load balancer가 죽은 노드를 빼고 다른 replica가 같은 요청을 처리할 수 있기 때문이다.

> Q: DB 장애를 cache로 완전히 가릴 수 없나요?
> 의도: source of truth와 cached snapshot의 차이를 구분하는지 확인
> 핵심: 이미 cache된 read만 잠깐 가능할 뿐, miss와 write는 여전히 authoritative DB가 필요하다.

## 한 줄 정리

request path 장애는 "무엇이 고장 났나"보다 **그 고장을 바로 위에서 누가 reroute, buffer, degrade로 먼저 흡수하느냐**를 함께 봐야 이해가 선명해진다.
