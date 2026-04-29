# Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩

> 한 줄 요약: 로드 밸런서가 stateless app 여러 대에 요청을 나누고, database는 정답을 보관하고, cache는 반복 읽기를 덜어 주고, queue는 느린 후처리를 뒤로 미루는 구조로 보면 백엔드 scale basics가 한 그림에 잡힌다.

retrieval-anchor-keywords: stateless backend scale basics, load balancer cache database queue primer, stateless app horizontal scaling intuition, backend box mental model, why load balancer with stateless app, source of truth vs cache, cache or queue first decision, scale out beginner, what is stateless backend, backend basics 처음, 왜 서버를 여러 대 두나요, load balancer cache db queue what is, request path mental model, sync vs async backend basics, beginner project architecture map

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Queue vs Cache vs DB Decision Drill](./queue-vs-cache-vs-db-decision-drill.md)
- [로드 밸런서 기초](./load-balancer-basics.md)
- [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md)
- [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md)
- [캐시 기초](./caching-basics.md)
- [메시지 큐 기초](./message-queue-basics.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Database Scaling Primer](./database-scaling-primer.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [system-design 카테고리 인덱스](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 먼저 잡을 그림

초보자는 용어보다 역할부터 외우는 편이 빠르다.

- **Stateless app**: 요청을 읽고, 어디에 저장하고, 무엇을 바로 답하고, 무엇을 나중으로 미룰지 결정한다.
- **Load Balancer**: 들어오는 요청을 건강한 app 인스턴스로 나눠 보낸다.
- **Database**: 주문, 회원, 결제 같은 핵심 상태를 오래 보관하는 정답 저장소다.
- **Cache**: 자주 읽는 값을 빠르게 꺼내기 위한 복사본이다.
- **Queue**: 지금 응답하지 않아도 되는 일을 줄 세워 두는 대기열이다.

짧게 외우면 이렇다.

- load balancer는 `나눈다`
- app은 `판단`한다
- database는 `기억`한다
- cache는 `아낀다`
- queue는 `미룬다`

대표 그림은 아래 정도로 보면 충분하다.

```text
Client
  -> Load Balancer
      -> Stateless App
           -> Cache
           -> Database
           -> Queue -> Worker
```

여기서 중요한 점은 박스가 많아서 복잡한 게 아니라, **한 박스가 모든 문제를 다 해결하지 못해서 역할을 나눠 둔 것**이라는 사실이다.

| 구성요소 | 초보자용 한 줄 역할 | 없으면 먼저 생기는 문제 |
|---|---|---|
| Load Balancer | 요청을 여러 app 인스턴스로 나눈다 | 한 서버에 트래픽이 몰리고 장애 우회가 어렵다 |
| Stateless App | 요청을 해석하고 다음 경로를 고른다 | 서버 교체와 수평 확장이 어려워진다 |
| Database | 핵심 상태를 저장한다 | 정답 기준점이 사라진다 |
| Cache | 반복 조회를 빠르게 재사용한다 | 같은 조회가 DB를 계속 두드린다 |
| Queue | 느린 후처리를 뒤로 민다 | 이메일/알림/외부 연동 때문에 응답이 느려진다 |

---

## 한눈에 보기

초보자 기준으로 요청은 크게 두 부류로 보면 된다.

| 질문 | 보통 가는 곳 | 예시 |
|---|---|---|
| 지금 바로 사용자에게 답해야 하나 | app -> cache / database | 상품 상세 조회, 주문 저장 결과 |
| 응답 뒤에 처리해도 되나 | app -> queue -> worker | 이메일 발송, 알림, 검색 인덱싱 |

핵심 감각은 아래다.

- 사용자가 기다리는 핵심 결과는 보통 `app + database` 쪽에서 결정된다.
- 같은 읽기가 너무 많으면 `cache`로 DB를 덜 친다.
- 느리지만 필수인 후처리는 `queue`로 보내 요청 경로를 가볍게 만든다.

처음 읽을 때 가장 자주 막히는 질문은 "이 문제를 cache로 풀어야 하나, queue로 풀어야 하나"다.

| 문제 상황 | 먼저 보는 박스 | 한 줄 기준 |
|---|---|---|
| 서버 1대로는 트래픽이 버겁다 | Load Balancer + Stateless App | 여러 대로 나누어 받을 수 있어야 scale-out이 시작된다 |
| 같은 조회가 너무 자주 반복된다 | Cache | 이미 있는 값을 빠르게 재사용하고 DB read를 줄인다 |
| 외부 API/후처리 때문에 응답이 느리다 | Queue | 지금 응답에 꼭 필요 없는 일을 요청 경로 밖으로 뺀다 |
| 사용자에게 지금 확답이 필요하다 | Database (+ App) | 핵심 상태는 먼저 저장/판정하고 응답한다 |

---

## 왜 load balancer와 stateless app이 항상 같이 나오나

초보자 질문을 가장 짧게 받으면 보통 이렇다. "왜 서버를 여러 대 두나요?" 답은 `한 대로는 언젠가 CPU, 메모리, 장애 복구 한계가 오기 때문`이다.

로드 밸런서는 여러 app 인스턴스 앞에서 교통정리를 맡고, stateless app은 그 분산을 받아도 어느 인스턴스가 처리하든 비슷한 결과를 내도록 만든다.

```text
Client
  -> Load Balancer
       -> App A
       -> App B
       -> App C
```

이때 load balancer만 있고 app이 stateful이면 scale-out 효과가 반쯤 사라진다. 예를 들어 로그인 상태를 App A 메모리에만 넣어 두면 다음 요청이 App B로 갔을 때 상태를 찾지 못한다. 그래서 상태를 DB, session store, token, object storage 같은 바깥 저장소로 빼서 app 인스턴스를 서로 바꿔 끼울 수 있게 만든다.

비유로 말하면 load balancer는 손님을 빈 창구로 보내는 안내원이고, stateless app은 어느 창구 직원이 받아도 같은 규칙으로 처리하는 창구다. 다만 실제 시스템은 직원이 서로 메모를 직접 공유하지 않으므로, 중요한 정보는 반드시 공용 저장소에 남겨야 한다는 점에서 비유가 멈춘다.

---

## 요청 두 개만 따라가 보면 이해가 빨라진다

### 1. 조회 요청: cache가 DB를 대신하는 게 아니라 앞에서 덜어 준다

예를 들어 상품 상세 페이지를 연다고 하자.

1. 사용자가 `GET /products/123`을 보낸다.
2. stateless app이 먼저 cache에서 `product:123`을 찾는다.
3. 값이 있으면 바로 응답한다.
4. 값이 없으면 database에서 읽고, cache를 채운 뒤 응답한다.

```text
Client -> App -> Cache 확인
                  |-- Hit  -> 바로 응답
                  |-- Miss -> DB 조회 -> Cache 저장 -> 응답
```

여기서 cache의 역할은 "정답 저장"이 아니라 "반복 읽기 절약"이다.
그래서 cache가 비어 있거나 오래됐을 때 최종 기준점은 여전히 database다.

### 2. 쓰기 요청: database에 핵심 상태를 남기고, queue로 후처리를 뺀다

이번에는 주문 생성 API를 보자.

1. 사용자가 주문 요청을 보낸다.
2. stateless app이 검증을 수행한다.
3. 주문 핵심 상태를 database에 저장한다.
4. 응답에 꼭 필요 없는 후처리만 queue에 넣는다.
5. worker가 queue에서 꺼내 이메일, 알림, 포인트 적립 같은 작업을 처리한다.

```text
Client -> App -> DB에 주문 저장 -> 201 Created
                   \
                    -> Queue(order.created) -> Worker -> 이메일/알림
```

이 구조가 흔한 이유는 간단하다.

- 주문 생성 성공 여부는 사용자가 바로 알아야 한다.
- 이메일 발송까지 기다리면 응답이 불필요하게 느려진다.
- 외부 연동이 느리거나 잠깐 실패해도 주문 자체는 먼저 받는 편이 낫다.

### 3. Stateless app은 "아무것도 저장하지 않는다"가 아니라 "인스턴스에 묶지 않는다"에 가깝다

초보자가 가장 많이 오해하는 부분이다.

- 주문 데이터는 database에 저장할 수 있다.
- 로그인 상태는 외부 세션 저장소나 토큰으로 다룰 수 있다.
- 업로드 파일은 object storage에 둘 수 있다.

즉, stateless app도 바깥 저장소를 적극적으로 쓴다.
다만 **특정 앱 인스턴스 메모리에만 중요한 상태를 가두지 않기 때문에** 어느 서버가 요청을 받아도 비슷하게 처리할 수 있다.

---

## 자주 헷갈리는 구분

| 헷갈리는 질문 | 짧은 답 | 왜 중요한가 |
|---|---|---|
| `Stateless면 DB도 안 쓰나요?` | 아니다 | stateless는 앱 인스턴스 상태 이야기이지, 영속 저장 금지가 아니다 |
| `로드 밸런서만 두면 바로 수평 확장 끝인가요?` | 아니다 | app이 stateless에 가깝고 상태가 외부화되어야 서버를 마음대로 늘리고 줄일 수 있다 |
| `Cache가 있으면 DB가 필요 없나요?` | 아니다 | cache는 복사본이라 비거나 오래될 수 있다 |
| `Queue에 넣었으니 저장 끝 아닌가요?` | 보통 아니다 | queue는 전달과 대기를 맡고, 핵심 비즈니스 상태의 기준점은 database인 경우가 많다 |
| `Queue를 쓰면 모든 처리가 비동기인가요?` | 아니다 | 결제 승인처럼 즉시 결과가 필요한 일은 요청 안에서 끝내야 한다 |

공통 혼동을 더 짧게 정리하면:

- **database는 기준점**이다
- **cache는 가속기**다
- **queue는 지연 허용 작업의 대기열**이다
- **stateless app은 이 셋을 조립하는 요청 처리 계층**이다
- **load balancer는 여러 app 인스턴스를 하나의 입구처럼 보이게 만든다**

---

## 병목이 보일 때 어디부터 떠올리나

| 증상 | 먼저 떠올릴 박스 | 이유 |
|---|---|---|
| 한 서버만 바빠서 p95가 튄다 | Load Balancer + Stateless App | 요청 분산과 인스턴스 추가가 가장 먼저 먹히는 경우가 많다 |
| 같은 조회 때문에 DB read가 많다 | Cache | 반복 읽기를 재사용할 수 있다 |
| 앱 서버 수를 빨리 늘려야 한다 | Stateless App | 복제가 쉬워 scale-out이 가장 단순하다 |
| 주문/회원 같은 핵심 상태가 사라지면 안 된다 | Database | source of truth와 내구성을 책임진다 |
| 외부 API 때문에 응답 시간이 흔들린다 | Queue | 느린 후처리를 요청 경로 밖으로 뺄 수 있다 |

이 표를 외우면 "왜 app, cache, DB, queue를 한 그림에 같이 그리느냐"가 훨씬 덜 추상적으로 느껴진다.

---

## 수평 확장 intuition은 이 순서로 잡으면 된다

처음에는 "서버를 여러 대 두면 다 빨라지나요?"처럼 생각하기 쉽다. 실제로는 병목마다 늘리는 레버가 다르다.

| 병목 | 먼저 늘리거나 바꾸는 것 | 이유 |
|---|---|---|
| app CPU가 높다 | load balancer 뒤 app 인스턴스 수 | stateless app tier가 가장 복제하기 쉽다 |
| DB read가 높다 | cache, read replica 검토 | 같은 조회를 원본 DB까지 매번 보내지 않기 위해서다 |
| 응답 뒤 외부 API가 오래 걸린다 | queue + worker 수 | 사용자가 기다리는 경로와 후처리 경로를 분리한다 |
| DB write가 한계다 | schema, query, partitioning 검토 | stateful tier는 단순히 대수만 늘리기 어렵다 |

초보자에게 중요한 감각은 "모든 박스를 동시에 키우는 게 아니라, 가장 싸고 안전한 레버부터 본다"는 점이다. 보통은 `app scale-out -> cache/read 최적화 -> queue로 분리 -> DB 구조 조정` 순서로 사고하는 경우가 많다. 다만 실제 순서는 서비스의 읽기/쓰기 비율과 일관성 요구에 따라 달라질 수 있다.

---

## 더 깊이 가려면

- 전체 박스 지도를 먼저 보고 싶다면 [System Design Foundations](./system-design-foundations.md)
- load balancer가 health check, drain, sticky session과 어떻게 이어지는지 보고 싶다면 [로드 밸런서 기초](./load-balancer-basics.md)
- scale up과 scale out을 따로 비교해 보고 싶다면 [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md)
- app이 왜 stateless여야 scale-out이 쉬운지 먼저 보고 싶다면 [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md)
- cache hit/miss와 TTL 감각을 따로 잡고 싶다면 [캐시 기초](./caching-basics.md)
- producer/consumer와 비동기 처리 감각을 따로 잡고 싶다면 [메시지 큐 기초](./message-queue-basics.md)
- sync/async 경계와 중복 흡수를 같이 잡고 싶다면 [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- DB가 느릴 때 왜 바로 sharding으로 뛰지 않는지 알고 싶다면 [Database Scaling Primer](./database-scaling-primer.md)
- cache, app, queue, DB 중 어디가 먼저 장애를 흡수하는지 보고 싶다면 [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)

DB와 queue 사이의 전달 보장을 더 엄격하게 다루는 심화는 [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)에서 이어진다.

---

## 면접/시니어 질문 미리보기

> Q: 왜 stateless app 앞에 cache를 두고, 뒤에 queue를 두나요?
> 의도: 읽기 가속과 비동기 후처리의 역할 분담 이해 확인
> 핵심: cache는 반복 조회를 빨리 처리해 DB read를 줄이고, queue는 응답에 꼭 필요 없는 느린 일을 뒤로 보내 app의 요청 경로를 가볍게 만든다.

> Q: 왜 load balancer와 stateless app을 같이 설명하나요?
> 의도: 수평 확장 시작 조건 이해 확인
> 핵심: load balancer는 여러 인스턴스로 요청을 나누고, stateless app은 어느 인스턴스가 받아도 처리 가능하게 만든다. 둘이 같이 있어야 scale-out 효과가 제대로 난다.

> Q: stateless app인데도 database가 필요한 이유는 무엇인가요?
> 의도: stateless와 영속 저장의 차이 이해 확인
> 핵심: stateless는 앱 인스턴스가 요청 간 상태를 들고 있지 않는다는 뜻이고, 주문/회원 같은 핵심 상태는 여전히 database 같은 외부 저장소에 남겨야 한다.

> Q: queue가 있으면 database 없이도 되나요?
> 의도: queue와 source of truth의 역할 구분 확인
> 핵심: queue는 메시지를 전달하고 대기시키는 도구다. 핵심 비즈니스 상태의 정답 저장소는 보통 database이고, queue는 후처리와 비동기 분리에 더 가깝다.

---

## 한 줄 정리

Load balancer는 요청을 여러 stateless app 인스턴스로 나누고, database는 정답을 보관하고, cache는 반복 읽기를 덜어 주고, queue는 늦게 처리해도 되는 일을 넘긴다고 잡으면 백엔드 scale basics가 한 장 그림으로 정리된다.
