# System Design Foundations

> 한 줄 요약: load balancer, stateless app, cache, database, queue를 "어떤 병목을 줄이는 박스인가" 기준으로 묶고, 초심자가 다음에 읽을 scale basics와 consistency bridge까지 연결하는 입문 문서다.

retrieval-anchor-keywords: system design foundations, system design basics, 처음 system design, system design 뭐부터, why many boxes backend, scale basics, load balancer stateless app, cache database queue basics, horizontal scaling intuition, vertical vs horizontal scaling, stateless service basics, source of truth basics, queue worker what is, sticky session beginner, backend architecture what is

**난이도: 🟢 Beginner**

관련 문서:

- [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
- [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md)
- [로드 밸런서 기초](./load-balancer-basics.md)
- [캐시 기초](./caching-basics.md)
- [메시지 큐 기초](./message-queue-basics.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
- [인덱스와 실행 계획](../database/index-and-explain.md)

---

## 핵심 개념

초심자가 system design에서 가장 먼저 막히는 질문은 "왜 박스가 이렇게 많아요?"다.
이 문서는 박스 이름을 외우기보다, **각 박스가 줄이는 병목이 다르다**는 감각부터 잡게 하려는 entrypoint다.

- Load Balancer: 여러 app 인스턴스로 요청을 나눈다.
- Stateless App: 어느 인스턴스가 받아도 비슷하게 처리되게 만든다.
- Cache: 반복 읽기를 빠르게 재사용해 DB read를 줄인다.
- Database: 핵심 상태와 내구성의 기준점을 맡는다.
- Queue: 지금 바로 끝낼 필요 없는 후처리를 요청 경로 밖으로 뺀다.

이 다섯 박스는 대체재가 아니라 역할 분담이다.
그래서 기본 질문은 "무엇을 쓰지?"보다 "지금 줄이려는 병목이 무엇인가?"가 더 안전하다.

처음에는 아래 두 문장만 분리해도 읽기가 쉬워진다.

- `지금 바로 답해야 하는 일`은 보통 app과 database 쪽에서 끝난다.
- `조금 늦어도 되는 일`은 queue로 빼거나 cache로 반복 읽기를 줄인다.

## 한눈에 보기

대표 요청 경로를 아주 단순하게 그리면 아래 정도면 충분하다.

```text
Client
  -> Load Balancer
      -> Stateless App
           -> Cache
           -> Database
           -> Queue -> Worker
```

| 박스 | 제일 먼저 떠올릴 역할 | 없으면 먼저 생기는 문제 |
|---|---|---|
| Load Balancer | 요청 분산 | 서버 1대에 트래픽과 장애가 몰린다 |
| Stateless App | 복제 가능한 요청 처리 | 인스턴스를 늘리거나 교체하기 어렵다 |
| Cache | 반복 읽기 절감 | 같은 조회가 DB를 계속 친다 |
| Database | source of truth | 정답 기준점과 복구 기준이 약해진다 |
| Queue | 느린 후처리 분리 | 이메일, 웹훅, 외부 API 때문에 응답이 늘어진다 |

짧게 외우면 `나눈다 -> 판단한다 -> 아낀다 -> 기억한다 -> 미룬다`다.
다만 이 비유는 입문용이다. 실제 시스템에서는 각 박스가 완전히 독립적이지 않고, 특히 database와 queue는 일관성 비용을 함께 만든다.

## 처음 20분 압축 라우트

이번 문서의 목표는 모든 primer를 다 읽게 하는 것이 아니라, **초심자 1회차 경로를 짧게 압축하는 것**이다.

| 단계 | 먼저 읽을 문서 | 여기서 얻는 감각 | 바로 다음 bridge |
|---|---|---|---|
| 1 | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md) | app/cache/db/queue가 한 요청 안에서 어떻게 갈리는지 | [Queue vs Cache vs DB Decision Drill](./queue-vs-cache-vs-db-decision-drill.md) |
| 2 | [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md) | scale up보다 scale out이 왜 자주 먼저 나오나 | [로드 밸런서 기초](./load-balancer-basics.md) |
| 3 | [로드 밸런서 기초](./load-balancer-basics.md) | load balancer와 stateless app이 왜 같이 설명되나 | [Stateless Sessions Primer](./stateless-sessions-primer.md) |

그다음부터는 막히는 증상 기준으로 갈라 읽는 편이 빠르다.

| 지금 막히는 질문 | 먼저 읽을 문서 | 후속 bridge |
|---|---|---|
| `cache는 왜 빠른데 위험하다고 하나요?` | [캐시 기초](./caching-basics.md) | [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md) |
| `queue를 넣으면 어디까지 끝난 건가요?` | [메시지 큐 기초](./message-queue-basics.md) | [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md) |
| `db는 왜 app처럼 그냥 늘리면 안 되나요?` | [Database Scaling Primer](./database-scaling-primer.md) | [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md) |
| `방금 쓴 값이 왜 바로 안 보여요?` | [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md) | [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md) |

## 1분 예시로 먼저 묶기

상품 상세와 주문 생성 두 개만 같이 보면, 박스 역할이 glossary보다 훨씬 덜 추상적이다.

| 장면 | 먼저 쓰는 박스 | 왜 이 선택이 자연스러운가 |
|---|---|---|
| 상품 상세 조회 | cache -> DB | 같은 읽기가 많고, cache miss여도 DB에서 다시 읽어 올 수 있다 |
| 주문 생성 | app -> DB -> queue | 주문 성공 여부는 지금 확정해야 하고, 이메일/알림은 뒤로 보내도 된다 |

```text
조회:
Client -> App -> Cache -> miss면 DB

쓰기:
Client -> App -> DB에 핵심 상태 저장 -> 응답
                  \
                   -> Queue -> Worker -> 후처리
```

이 그림에서 cache와 queue는 둘 다 `뒤에 붙은 박스`처럼 보이지만 역할이 다르다.

- cache는 `이미 있는 값을 빨리 다시 꺼내는 박스`
- queue는 `지금 안 끝내도 되는 일을 뒤로 미루는 박스`

이 차이를 먼저 잡아 두면 `cache를 둘까요, queue를 둘까요?` 같은 질문에서 훨씬 덜 헤맨다.

## 상세 분해

### 1. Load Balancer + Stateless App은 scale basics의 한 묶음이다

서버를 여러 대 둔다고 끝나지 않는다.
load balancer가 요청을 나눠도, 앱이 특정 인스턴스 메모리에 중요한 상태를 오래 들고 있으면 scale-out 이점이 줄어든다.

- 세션이 서버 메모리에만 있으면 sticky session 의존이 커진다.
- 업로드 파일이 로컬 디스크에만 있으면 서버 교체가 번거롭다.
- 주문 상태가 앱 메모리에만 있으면 failover 때 정답을 잃는다.

그래서 `load balancer -> stateless app`은 보통 함께 배운다.
여기서 말하는 stateless는 "아무것도 저장하지 않는다"가 아니라 "중요한 상태를 특정 인스턴스에 묶지 않는다"에 가깝다.

### 2. Cache는 DB를 없애는 박스가 아니라 DB read를 덜 때리는 박스다

가장 흔한 흐름은 이렇다.

1. app이 cache를 먼저 본다.
2. 값이 있으면 바로 응답한다.
3. 값이 없으면 DB에서 읽고 cache를 채운다.

즉, cache의 역할은 `정답 저장`이 아니라 `빠른 재사용`이다.
값이 오래됐을 수 있고 TTL이 지나면 사라질 수 있으므로, 기준점은 대개 database 쪽에 남는다.

### 3. Database는 source of truth라서 확장이 가장 신중하다

app과 worker는 복제해서 늘리기 쉽지만 database는 상태를 들고 있다.
그래서 DB가 힘들다고 바로 sharding으로 뛰기보다, 보통은 아래 순서가 먼저다.

1. query와 index를 고칠 수 있는가
2. cache로 read를 덜 수 있는가
3. replica로 읽기를 분산할 수 있는가
4. 그래도 단일 primary 한계가 남는가

이 순서는 제품, 트래픽 패턴, 사용하는 DB 엔진에 따라 달라질 수 있다.
다만 초심자에게는 "DB scaling은 마지막 레버일수록 비싸다"는 감각이 먼저 중요하다.

### 4. Queue는 모든 처리를 빠르게 만드는 것이 아니라 응답 경로를 가볍게 만든다

queue는 이메일 발송, 웹훅 호출, 검색 인덱싱처럼 지금 응답에 꼭 필요 없는 일을 뒤로 미루는 데 강하다.

```text
Client -> App -> DB에 핵심 상태 저장 -> 응답
                  \
                   -> Queue -> Worker -> 후처리
```

장점은 응답 시간 단축, burst 흡수, retry 분리다.
대신 queue를 넣는 순간에는 eventual consistency를 함께 검토해야 한다.
예를 들어 "주문 생성 확인 메일"은 늦어도 되지만, "결제 승인 여부"는 보통 요청 안에서 더 명확해야 한다.

## 흔한 오해와 함정

- `load balancer를 넣으면 DB도 자동으로 확장된다`는 오해가 흔하다. 분산은 주로 app tier부터 쉬워진다.
- `stateless면 상태가 아예 없다`는 표현은 부정확하다. 상태를 바깥 저장소로 옮긴다는 뜻에 더 가깝다.
- `cache가 있으면 DB가 필요 없다`는 말도 틀리다. cache는 복사본이어서 비거나 오래될 수 있다.
- `queue에 넣었으니 비즈니스 완료다`도 위험하다. 핵심 완료 기준은 보통 DB commit이나 명시적 성공 응답 쪽에 있다.
- `수평 확장은 무조건 싸다`도 단정할 수 없다. 운영 복잡도, session 외부화, read-after-write 같은 새 비용이 따라온다.

## 실무에서 쓰는 모습

상품 상세를 보여 주는 서비스라면 보통 이렇게 읽는다.

1. load balancer가 여러 app 인스턴스로 요청을 나눈다.
2. app이 상품 cache를 먼저 본다.
3. cache miss면 DB에서 읽고 응답한다.
4. 조회 로그나 추천 이벤트는 queue로 보낸다.
5. worker가 뒤에서 집계나 후처리를 수행한다.

트래픽이 5배 늘면 보통은 `app 인스턴스 증가 -> cache hit ratio 개선 -> worker 증설 -> DB read/write 병목 점검` 순으로 본다.
즉, "모든 박스를 같이 키운다"보다 **복제하기 쉬운 tier부터 늘리고 stateful tier는 보호한다**가 입문용 기본 전략이다.

## 더 깊이 가려면

- scale basics를 한 번 더 고정하고 싶다면 [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md)
- load balancer, health check, sticky session 연결이 헷갈리면 [로드 밸런서 기초](./load-balancer-basics.md)
- cache와 DB의 경계가 헷갈리면 [캐시 기초](./caching-basics.md)와 [Database Scaling Primer](./database-scaling-primer.md)
- queue를 넣었을 때 sync/async 경계가 흐려지면 [메시지 큐 기초](./message-queue-basics.md)와 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- 장애가 났을 때 어느 박스가 먼저 맞는지 보고 싶다면 [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)

여기까지 읽고도 `incident`, `outage`, `failover`, `playbook` 같은 단어가 더 궁금하면 그건 follow-up 문서 신호다.
처음 읽는 사람은 운영 사고 문서로 바로 내려가기보다 아래 둘 중 하나를 먼저 끝내는 편이 안전하다.

- `cache냐 queue냐`가 헷갈리면 [Queue vs Cache vs DB Decision Drill](./queue-vs-cache-vs-db-decision-drill.md)
- `방금 쓴 값이 왜 안 보이냐`가 헷갈리면 [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)

## 면접/시니어 질문 미리보기

> Q: 왜 stateless app이 horizontal scaling에 유리한가요?
> 의도: app tier 복제 가능성과 상태 외부화 연결을 보는 질문
> 핵심: 특정 인스턴스에 중요한 사용자 상태가 묶이지 않아 인스턴스를 쉽게 추가, 교체, 우회할 수 있기 때문이다.

> Q: cache가 있는데 왜 DB가 여전히 필요한가요?
> 의도: source of truth와 최적화 계층 차이를 보는 질문
> 핵심: cache는 빠른 복사본이고, DB가 정합성과 내구성의 기준점을 맡기 때문이다.

> Q: queue는 언제 넣어야 하나요?
> 의도: 동기 처리와 비동기 처리 경계를 구분하는지 확인
> 핵심: 사용자가 응답을 기다릴 필요가 없는 느린 후처리를 요청 경로 밖으로 빼고 싶을 때 넣는다.

> Q: DB를 app처럼 그냥 여러 대 복제하면 안 되나요?
> 의도: stateful tier 확장 난이도와 replica 한계를 구분하는지 확인
> 핵심: 데이터 정합성, write coordination, replication lag 비용 때문에 app tier보다 훨씬 신중하게 다뤄야 한다.

## 한 줄 정리

System design foundations의 핵심은 박스 이름 암기가 아니라, load balancer는 분산, stateless app은 복제 가능성, cache는 읽기 절감, database는 기준 데이터, queue는 후처리 분리라는 역할 감각과 그다음 bridge 문서를 바로 고를 수 있는 읽기 순서를 잡는 데 있다.
