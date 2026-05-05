---
schema_version: 3
title: Load Balancer Drain and Affinity Primer
concept_id: system-design/load-balancer-drain-and-affinity-primer
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- drain-vs-readiness
- sticky-session-rollout-tail
- deregistration-delay-tuning
aliases:
- load balancer drain and affinity primer
- load balancer health check
- readiness vs liveness
- active health check
- passive health check
- connection draining
- deregistration delay
- sticky session
- session affinity
- cookie affinity
- ip hash routing
- keepalive drain
- http2 goaway
- affinity rebalance basics
symptoms:
- 배포할 때 인스턴스를 내렸는데 왜 기존 요청이 중간에 끊기는지 모르겠어
- sticky session 때문에 새 인스턴스를 올려도 트래픽이 안 옮겨와
- readiness는 내렸는데도 old version tail이 길게 남아
intents:
- definition
- design
- troubleshooting
prerequisites:
- system-design/load-balancer-basics
- system-design/stateless-sessions-primer
next_docs:
- system-design/service-discovery-health-routing-design
- system-design/global-traffic-failover-control-plane-design
- system-design/session-store-design-at-scale
linked_paths:
- contents/system-design/load-balancer-basics.md
- contents/system-design/request-path-failure-modes-primer.md
- contents/system-design/stateless-sessions-primer.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/global-traffic-failover-control-plane-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
confusable_with:
- system-design/service-discovery-health-routing-design
- system-design/stateless-sessions-primer
- network/connection-keepalive-loadbalancing-circuit-breaker
forbidden_neighbors: []
expected_queries:
- connection draining을 왜 안 하면 배포 중 502가 나?
- readiness를 내렸는데도 old version 요청이 남는 이유를 설명해줘
- sticky session이 rolling deploy를 느리게 만드는 이유가 뭐야?
- deregistration delay를 너무 짧게 잡으면 어떤 문제가 생겨?
- health check, drain, affinity를 한 그림으로 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 학습자가 load balancer를 단순 분산기가 아니라 health check,
  draining, affinity를 동시에 다루는 운영 장치로 이해하게 돕는 beginner
  primer다. 배포 중 연결이 왜 끊기나, readiness를 내렸는데 old version
  tail이 왜 남나, sticky session이 왜 교체를 늦추나 같은 자연어 질문이
  본 문서의 drain/affinity 설명으로 매핑된다.
---
# Load Balancer Drain and Affinity Primer

> 한 줄 요약: health check, connection draining, sticky affinity를 함께 봐야 load balancer가 왜 배포와 failover의 안정성을 좌우하는지 이해할 수 있고, "배포할 때 왜 옛 서버 트래픽이 안 빠지지?" 같은 질문도 설명된다.

retrieval-anchor-keywords: load balancer drain and affinity primer, load balancer health check, readiness vs liveness, active health check, passive health check, connection draining, deregistration delay, sticky session, session affinity, cookie affinity, keepalive drain, 배포할 때 왜 옛 서버 트래픽이 안 빠져요, drain이 뭐예요, sticky session 때문에 왜 failover가 느려요, load balancer failover basics

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Stateless Sessions Primer](./stateless-sessions-primer.md)
- [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
- [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md)
- [Session Store Design at Scale](./session-store-design-at-scale.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)

---

## 핵심 개념

초보자가 load balancer를 "여러 서버에 요청을 나눠 주는 박스" 정도로만 이해하면 deploy와 failover 설명이 자꾸 얕아진다.
특히 `배포할 때 왜 old version 연결이 안 빠지죠?`, `health check는 통과했는데 왜 502가 나죠?` 같은 질문은 drain과 affinity를 같이 보지 않으면 풀리지 않는다.
실전에서 load balancer는 계속 세 가지를 결정한다.

- 어떤 backend가 **새 요청을 받을 자격이 있는가**
- 어떤 backend는 **새 요청은 막고 기존 연결만 정리해야 하는가**
- 어떤 client나 key를 **같은 backend에 붙여 둘 것인가**

이 세 질문이 각각 아래와 연결된다.

- health check: 새 요청을 받을 자격 판단
- connection draining: 종료 전 정리 절차
- affinity: 같은 client/key를 같은 backend로 보내는 편향

아주 단순하게 그리면 아래와 같다.

```text
Client
  -> Load Balancer
      -> App A (ready)
      -> App B (draining)
      -> App C (unhealthy)
```

이때 load balancer의 기대 동작은 다음과 같다.

- App A: 새 요청과 기존 연결을 계속 받는다
- App B: 새 요청은 막고, 기존 in-flight 요청과 연결만 정리한다
- App C: 새 요청도 기존 재시도도 붙이지 않는다

핵심은 load balancer가 단순 분산기가 아니라 **배포, 장애, 세션 편향을 함께 다루는 admission controller**라는 점이다.

## 깊이 들어가기

### 1. Health check는 프로세스 생존 확인보다 넓다

health check를 "프로세스가 안 죽었는지 확인" 정도로만 보면 부족하다.
트래픽 관점에서는 보통 아래를 구분해야 한다.

- liveness: 프로세스가 살아 있는가
- readiness: 지금 새 요청을 받아도 되는가
- passive health: 실제 요청 실패율이나 timeout이 나빠졌는가

예를 들어 이런 상황은 흔하다.

- 프로세스는 살아 있지만 DB pool이 꽉 찼다
- pod는 떴지만 캐시 warm-up이 끝나지 않았다
- 종료 직전이라 더 이상 새 요청을 받으면 안 된다

즉, health는 `UP/DOWN` 한 비트보다 **ready / warming / draining / unhealthy** 같은 운영 상태에 더 가깝다.
이 감각을 놓치면 "health check는 붙어 있는데 배포할 때 왜 502가 나지?" 같은 질문이 생긴다.

### 2. Drain은 죽이기 전에 신규 유입을 끊는 절차다

connection draining의 목적은 단순하다.
`이 인스턴스는 곧 내려갈 것이니 새 요청은 받지 말고, 이미 처리 중인 일만 마저 끝내자`는 것이다.

보통 흐름은 이렇다.

1. 인스턴스를 `draining` 상태로 바꾼다
2. load balancer가 새 요청 선택 대상에서 제외한다
3. 기존 in-flight 요청과 keep-alive 연결을 일정 시간 허용한다
4. timeout이 지나면 남은 연결을 강제로 닫고 종료한다

```text
ready -> draining -> removed
```

이때 중요한 값이 `deregistration delay`나 drain timeout이다.
이 값이 너무 짧으면 정상 요청도 중간에 끊기고,
너무 길면 배포가 끝없이 늘어진다.

그래서 보통은 아래를 기준으로 잡는다.

- 일반 HTTP API: p99 응답 시간보다 충분히 길게
- file upload / long polling: 별도 경로 정책 적용
- gRPC / WebSocket: 요청 단위가 아니라 연결 단위 drain 전략 필요

### 3. Keep-Alive와 장수 연결은 drain을 어렵게 만든다

짧은 HTTP 요청만 있으면 drain은 비교적 단순하다.
하지만 실제 서비스는 아래 때문에 tail이 길어진다.

- HTTP keep-alive로 같은 TCP 연결에서 여러 요청이 이어짐
- HTTP/2, gRPC처럼 한 연결에 여러 stream이 동시에 열림
- WebSocket, SSE처럼 연결이 오래 유지됨

그래서 "새 요청만 막으면 끝"이 아니다.

- 기존 keep-alive 연결에서 새 요청이 또 들어오지 않게 해야 한다
- HTTP/2, gRPC는 새 stream 생성 중단 신호가 필요하다
- WebSocket은 재연결 유도나 max session age 같은 별도 장치가 필요하다

## 깊이 들어가기 (계속 2)

이 부분을 놓치면 배포 스크립트는 `ready=false`로 바꿨는데도,
실제론 오래된 연결이 계속 살아 있어 old version tail이 길게 남는다.

### 4. Affinity는 여러 형태가 있고, 모두 같은 비용을 낸다

affinity는 "이 요청을 가능한 같은 backend로 보내자"는 정책이다.
대표 방식은 아래와 같다.

- cookie affinity: 같은 브라우저를 같은 app 인스턴스로 보냄
- source IP hash: 같은 IP 대역을 같은 backend로 보냄
- key-based hash: 같은 tenant나 shard key를 같은 backend에 붙임

affinity가 유용한 경우도 있다.

- app 메모리에 세션이 있을 때
- local cache locality를 살리고 싶을 때
- 특정 owner/shard와 가까운 worker로 보내고 싶을 때

하지만 공짜는 아니다.

- load가 고르게 퍼지지 않을 수 있다
- 새 인스턴스를 추가해도 기존 client가 잘 옮겨 오지 않는다
- deploy 중 old instance tail이 길어진다
- failover 시 state와 affinity mapping을 같이 잃을 수 있다

여기서 특히 헷갈리기 쉬운 점:
`sticky session`처럼 app 메모리 상태 때문에 붙이는 affinity와,
cache locality를 위한 key hash는 목적이 다르다.
하지만 둘 다 **재분산과 failover를 느리게 만든다**는 운영 비용은 공유한다.

### 5. 왜 affinity가 rolling deploy를 꼬이게 만드나

rolling deploy는 보통 "새 인스턴스를 올리고, 옛 인스턴스를 drain하고, 천천히 교체"하는 과정이다.
affinity가 강할수록 이 과정이 잘 안 풀린다.

예를 들면:

- old App A에 이미 sticky client가 많이 붙어 있다
- new App D를 추가해도 기존 client는 계속 App A만 친다
- App A를 drain하려면 sticky binding이 풀릴 때까지 오래 기다려야 한다
- timeout을 짧게 잡으면 일부 사용자가 끊기고, 길게 잡으면 deploy가 늘어진다

특히 app 메모리에 세션을 둔 구조라면 더 어렵다.

- drain 중에 사용자를 다른 인스턴스로 보내면 로그인 상태가 사라질 수 있다
- 그래서 배포가 사실상 "세션 만료를 기다리는 작업"처럼 변한다

즉, affinity는 새 버전 승격을 느리게 만들고,
local-only state는 그 문제를 구조적 제약으로 바꾼다.
이 지점이 [Stateless Sessions Primer](./stateless-sessions-primer.md)와 바로 이어진다.

### 6. 왜 affinity가 failover를 완전히 해결해 주지 못하나

많은 초보자가 이렇게 생각한다.

`health check가 죽은 인스턴스를 빼 주니까 failover는 자동으로 끝난다`

## 깊이 들어가기 (계속 3)

절반만 맞다.
새 요청 라우팅은 바뀔 수 있지만, 아래는 별도 문제다.

- 이미 죽은 인스턴스 메모리에 있던 세션/state는 사라진다
- client cookie나 NAT 특성 때문에 같은 경로로 재시도하다가 tail latency가 길어질 수 있다
- long-lived connection은 재연결 과정에서 오류를 볼 수 있다

즉, health check는 **새 경로 선택**을 고쳐 주지만,
affinity가 기대하던 **상태 연속성**까지 복구해 주지는 않는다.

그래서 진짜 failover 설계는 보통 아래 방향으로 간다.

- critical state를 인스턴스 밖으로 빼기
- affinity TTL과 범위를 줄이기
- retry budget과 reconnect 동작을 별도 설계하기
- region pinning이 있다면 failback/re-entry까지 같이 설계하기

### 7. 실무에서는 상태 전이를 관측해야 한다

좋은 운영은 "인스턴스 수"보다 상태 전이를 잘 본다.
특히 아래 지표가 중요하다.

- `healthy_backends`
- `draining_backends`
- `backend_open_connections`
- `inflight_requests`
- `forced_connection_close_total`
- `affinity_skew_ratio`
- `retry_after_drain_total`

이런 지표가 없으면 다음 상황을 헷갈리기 쉽다.

- health check는 통과했는데 warm-up이 덜 됐는가
- drain이 끝나지 않았는가
- sticky affinity 때문에 old fleet에 요청이 남는가
- forced close 때문에 사용자 오류가 나는가

## 실전 시나리오

### 시나리오 1: 롤링 배포인데 old version 트래픽이 안 줄어든다

문제:

- 새 인스턴스는 늘었는데 old 인스턴스 연결 수가 거의 줄지 않는다

원인 후보:

- keep-alive tail이 길다
- cookie affinity가 오래 유지된다
- WebSocket/gRPC 장수 연결이 재연결되지 않는다

해결:

- drain timeout과 keep-alive 정책을 같이 조정한다
- affinity TTL을 줄이거나 재바인딩 조건을 둔다
- 장수 연결 경로는 별도 재연결/GOAWAY 정책을 둔다

### 시나리오 2: 인스턴스 장애 후 로그인 사용자가 튕긴다

문제:

- load balancer는 다른 인스턴스로 우회했는데 일부 사용자가 다시 로그인해야 한다

원인:

- 세션이 죽은 인스턴스 메모리에만 있었다

해결:

- health check만 믿지 말고 세션 상태를 external session store나 token 기반으로 외부화한다
- affinity는 편의 기능으로만 두고, state continuity의 유일한 기반으로 두지 않는다

### 시나리오 3: region evacuation 중 특정 tenant만 tail latency가 길다

문제:

- global shift는 시작됐는데 일부 tenant의 연결 재배치가 늦다

원인 후보:

- tenant key affinity가 강해 같은 backend 집합에 남아 있다
- drain보다 background reconnect 주기가 더 길다

해결:

- tenant-level affinity와 evacuation 정책을 함께 점검한다
- background caller, worker, streaming client까지 drain inventory에 넣는다

## 면접 답변 골격

짧게 답하면 이렇게 정리할 수 있다.

> load balancer는 단순 분산기가 아니라 health check로 신규 유입 대상을 고르고, drain으로 종료 중 인스턴스의 in-flight 요청을 정리하며, 필요하면 affinity로 같은 client를 같은 backend에 붙이는 운영 제어 장치입니다. 문제는 affinity가 강할수록 rolling deploy와 failover가 어려워진다는 점입니다. 그래서 실전에서는 readiness와 draining을 분리하고, critical session state를 인스턴스 밖으로 빼서 sticky routing 의존도를 줄이는 방향으로 설계합니다.

## 꼬리질문

> Q: readiness와 liveness를 왜 따로 보나요?
> 의도: 프로세스 생존과 트래픽 수용 가능성을 구분하는지 확인
> 핵심: 살아 있어도 warm-up 중이거나 drain 중이면 새 요청을 받으면 안 되기 때문이다.

> Q: drain은 health check 실패와 같은 뜻인가요?
> 의도: planned drain과 unplanned failure를 구분하는지 확인
> 핵심: 아니다. drain은 의도적으로 신규 유입을 막고 기존 요청을 정리하는 상태다.

> Q: sticky affinity가 왜 autoscaling과 배포를 느리게 만드나요?
> 의도: rebalance cost를 이해하는지 확인
> 핵심: 기존 client가 old instance에 계속 남아서 새 instance로 부하가 잘 옮겨 가지 않기 때문이다.

> Q: health check만 빠르면 failover 문제는 끝나나요?
> 의도: 라우팅 복구와 상태 복구를 분리하는지 확인
> 핵심: 아니다. 인스턴스 메모리에 있던 세션이나 장수 연결 상태는 별도 설계가 필요하다.

## 한 줄 정리

load balancer 운영의 핵심은 **누가 새 요청을 받을지, 누가 조용히 빠질지, 무엇이 같은 backend에 남을지**를 제어하는 것이고, sticky affinity가 강할수록 deploy와 failover는 어려워진다.
