# Connection Keep-Alive, Load Balancing, Circuit Breaker

**난이도: 🔴 Advanced**

> 연결 재사용, 분산, 차단은 따로 보는 개념처럼 보이지만 실제 장애는 이 셋이 엮여서 난다

> 관련 문서:
> - [HTTP Keep-Alive Timeout Mismatch: Deeper Cases](./http-keepalive-timeout-mismatch-deeper-cases.md)
> - [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)
> - [Accept Queue, SYN Backlog, Listen Overflow](./accept-queue-syn-backlog-listen-overflow.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [Spring RestClient vs WebClient Lifecycle Boundaries](../spring/spring-restclient-vs-webclient-lifecycle-boundaries.md)
> - [Spring WebClient Connection Pool and Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

retrieval-anchor-keywords: connection keep-alive, load balancing, circuit breaker, connection pool, keepalive timeout, connection draining, retry amplification, stale socket, unhealthy upstream

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [Keep-Alive와 연결 재사용](#keep-alive와-연결-재사용)
- [Load Balancing 실전 포인트](#load-balancing-실전-포인트)
- [Circuit Breaker 관점](#circuit-breaker-관점)
- [세 가지를 함께 볼 때](#세-가지를-함께-볼-때)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제가 중요한가

서버가 느려질 때는 한 가지 원인만 있는 경우가 드물다.

- 연결을 너무 자주 맺어서 느린 경우
- 특정 서버로만 트래픽이 몰린 경우
- 재시도와 로드밸런싱이 겹쳐 장애가 커진 경우
- 장애 난 서버를 계속 호출해서 전체 자원을 소모한 경우

그래서 keep-alive, load balancing, circuit breaker는 따로 외우기보다 **서로의 부작용을 줄이는 장치**로 보는 편이 좋다.

### Retrieval Anchors

- `connection keep-alive`
- `load balancing`
- `circuit breaker`
- `connection pool`
- `keepalive timeout`
- `connection draining`
- `retry amplification`
- `stale socket`

---

## Keep-Alive와 연결 재사용

### HTTP keep-alive

HTTP keep-alive는 요청마다 새 TCP 연결을 만들지 않고, **한 번 맺은 연결을 재사용**하는 방식이다.

장점:

- TCP handshake 비용을 줄인다
- 지연을 줄인다
- 서버와 클라이언트의 socket 사용량을 낮춘다

단점:

- 오래 열린 연결이 자원을 잡아먹는다
- 죽은 upstream에 붙어 있는 오래된 연결이 남을 수 있다
- 연결 수는 적어도 실제 처리량이 좋아지는 것은 아닐 수 있다

### TCP keep-alive와는 다르다

비슷한 이름이지만 의미가 다르다.

- HTTP keep-alive: 애플리케이션 레벨에서 연결을 재사용하는 개념
- TCP keepalive: 연결이 살아 있는지 프로브하는 OS/소켓 레벨 옵션

면접에서는 이 둘을 혼동하지 않는 것이 중요하다.

### 운영에서 보는 포인트

- 프록시와 upstream 사이의 커넥션 풀 크기
- idle timeout
- connection draining 여부
- HTTP/1.1 persistent connection과 HTTP/2 multiplexing 차이

HTTP/2는 하나의 연결 위에 여러 스트림을 올릴 수 있어서 연결 수를 줄이기 쉽지만, 그렇다고 연결 관리가 사라지는 것은 아니다.

---

## Load Balancing 실전 포인트

### 대표 알고리즘

- Round Robin: 단순하고 예측 가능하다
- Least Connections: 현재 연결이 적은 서버로 보낸다
- Weighted Round Robin: 성능이 다른 서버를 다르게 취급한다
- IP Hash / Consistent Hash: 같은 클라이언트를 같은 서버로 보내고 싶을 때 쓴다

### 알고리즘보다 중요한 것

실전에서는 알고리즘보다 운영 조건이 더 중요하다.

- keep-alive 때문에 실제 요청 수와 연결 수가 다를 수 있다
- long-lived connection이 있으면 Least Connections가 왜곡될 수 있다
- 특정 서버만 느려도 알고리즘이 자동으로 알아서 해결하지는 못한다

### 자주 생기는 장애

- sticky session 의존도가 높아서 서버 한 대가 죽으면 세션이 깨진다
- health check가 느려서 죽은 서버로 트래픽이 계속 간다
- 배포 중인 서버로 새 연결이 들어가 실패한다
- NAT나 프록시를 거치며 소스 IP 분포가 왜곡된다

### 운영에서 함께 보는 기능

- health check
- slow start
- connection draining
- failover
- zone awareness

로컬에서는 단순히 "분산된다"로 끝나지만, 실제 운영은 **정상 서버만 골라서, 천천히, 끊김 없이 넘기는 것**이 핵심이다.

---

## Circuit Breaker 관점

### 왜 필요한가

장애 난 외부 시스템을 계속 호출하면 실패가 쌓이고, 실패가 쌓이면 스레드와 커넥션이 묶이고, 묶인 자원이 다시 전체 장애를 만든다.

Circuit breaker는 이런 연쇄를 막기 위해 **일정 수준 이상 실패하면 호출을 잠시 중단**한다.

### 상태 변화

- Closed: 평소처럼 요청을 보낸다
- Open: 실패가 누적되어 요청을 차단한다
- Half-open: 일부 요청만 보내서 복구 여부를 확인한다

### 관찰 지표

- 실패율
- 연속 실패 횟수
- latency 증가
- timeout 비율

즉, circuit breaker는 "에러가 났는가"만 보는 게 아니라 **느려져서 사실상 장애가 된 상태**도 본다.

### Retry와의 관계

Retry는 일시적 실패를 흡수하지만, 잘못 쓰면 장애를 증폭시킨다.

- retry가 늘면 upstream 호출량이 더 증가한다
- circuit breaker가 없으면 실패한 의존성을 계속 두드린다
- circuit breaker가 있으면 최악의 구간에서 호출을 멈출 수 있다

그래서 retry와 circuit breaker는 같이 설계해야 한다.

---

## 세 가지를 함께 볼 때

### 시나리오 1: keep-alive만 과하게 길다

- 오래된 연결이 남는다
- 죽은 upstream이 재사용된다
- 장애가 느리게 감지된다

### 시나리오 2: load balancing은 있는데 circuit breaker가 없다

- 죽은 서버로도 계속 트래픽이 간다
- 실패 요청이 누적된다
- 사용자 체감 장애가 길어진다

### 시나리오 3: retry가 강하고 circuit breaker가 약하다

- 실패한 요청이 재시도되며 트래픽이 증가한다
- healthy server까지 밀린다
- 장애가 전체 시스템으로 번진다

### 실전 조합

1. 짧고 명확한 timeout을 둔다
2. 멱등한 요청만 제한적으로 retry한다
3. backoff와 jitter를 넣는다
4. 실패가 누적되면 circuit breaker를 연다
5. load balancer가 정상 서버에만 보낸다
6. 연결 재사용은 하되 draining과 health check를 같이 둔다

---

## 면접에서 자주 나오는 질문

### Q. keep-alive를 쓰는 이유는 무엇인가요?

- 매 요청마다 연결을 새로 맺는 비용을 줄여 latency와 자원 사용량을 낮추기 위해서다.

### Q. load balancer가 있다고 해서 무조건 고르게 분산되나요?

- 아니다. long-lived connection, sticky session, health check 지연, 서버 성능 차이 때문에 실제 분포는 쉽게 왜곡된다.

### Q. circuit breaker는 retry와 어떤 관계인가요?

- retry는 실패를 다시 시도하는 장치이고, circuit breaker는 실패가 계속될 때 아예 호출을 멈추는 장치다. 같이 써야 장애 증폭을 막을 수 있다.

### Q. HTTP/2가 있으면 connection keep-alive는 의미가 없나요?

- 아니다. HTTP/2는 연결 재사용의 효율을 높이지만, 연결 자체의 생명주기와 upstream 관리 문제는 여전히 남는다.
