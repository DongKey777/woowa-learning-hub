---
schema_version: 3
title: Accept Queue, SYN Backlog, Listen Overflow
concept_id: network/accept-queue-syn-backlog-listen-overflow
canonical: false
category: network
difficulty: advanced
doc_role: symptom_router
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- tcp-backlog
- accept-queue-overflow
- connection-storm
aliases:
- accept queue
- SYN backlog
- listen overflow
- somaxconn
- tcp_max_syn_backlog
- tcp_abort_on_overflow
- connection storm backlog
symptoms:
- connect timeout이나 SYN retransmission을 네트워크 경로 문제로만 보고 SYN backlog와 accept queue saturation을 분리하지 못한다
- CPU가 낮고 health check가 통과하므로 신규 연결 수용도 정상이라고 결론 내린다
- listen backlog 값만 키우면 끝난다고 생각해 somaxconn, tcp_max_syn_backlog, accept loop 처리 속도, LB 신규 연결 burst를 같이 보지 않는다
intents:
- symptom
- troubleshooting
prerequisites:
- network/http-request-response-basics-url-dns-tcp-tls-keepalive
- network/timeout-types-connect-read-write
next_docs:
- network/syn-retransmission-handshake-timeout
- network/load-balancer-healthcheck-failure-patterns
- network/nat-conntrack-ephemeral-port-exhaustion
linked_paths:
- contents/network/syn-retransmission-handshake-timeout.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/nat-conntrack-ephemeral-port-exhaustion.md
- contents/network/timeout-types-connect-read-write.md
confusable_with:
- network/syn-retransmission-handshake-timeout
- network/load-balancer-healthcheck-failure-patterns
- network/nat-conntrack-ephemeral-port-exhaustion
- network/timeout-types-connect-read-write
forbidden_neighbors: []
expected_queries:
- CPU는 낮은데 connect timeout과 SYN retransmission이 늘면 accept queue와 SYN backlog를 어떻게 봐?
- SYN backlog와 accept queue는 TCP handshake 단계에서 각각 무엇을 의미해?
- listen overflow에서 somaxconn tcp_max_syn_backlog tcp_abort_on_overflow를 같이 봐야 하는 이유는?
- LB health check는 정상인데 사용자 신규 연결만 간헐적으로 timeout 나는 원인은?
- keep-alive를 끄자 신규 handshake가 늘어 backlog pressure가 커지는 과정을 설명해줘
contextual_chunk_prefix: |
  이 문서는 TCP connection storm에서 SYN backlog와 accept queue를 분리해 connect timeout,
  SYN retransmission, listen overflow, intermittent RST를 진단하는 symptom router다.
  somaxconn, tcp_max_syn_backlog, accept loop, LB burst와 keep-alive 정책을 함께 본다.
---
# Accept Queue, SYN Backlog, Listen Overflow

> 한 줄 요약: 연결 폭주 때 `SYN backlog`와 `accept queue`를 구분하지 못하면 CPU는 멀쩡한데도 `connect timeout`, `SYN retransmission`, 간헐적 `RST`를 설명하지 못한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SYN Retransmission, Handshake Timeout Behavior](./syn-retransmission-handshake-timeout.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)

retrieval-anchor-keywords: accept queue, syn backlog, listen overflow, somaxconn, tcp_max_syn_backlog, listen queue, tcp_abort_on_overflow, SYN cookie, connection storm, backlog saturation

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

TCP 서버 앞에는 "연결 대기열"이 하나만 있는 것이 아니라, 보통 서로 다른 단계의 큐가 있다.

- `SYN backlog`: 아직 handshake가 끝나지 않은 연결 후보를 잠시 들고 있는 곳
- `accept queue`: handshake는 끝났지만 애플리케이션이 `accept()`로 아직 가져가지 않은 연결

즉, 연결 폭주는 "포트가 열려 있는가"보다 **어느 단계의 큐가 먼저 막히는가**로 봐야 한다.

### Retrieval Anchors

- `accept queue`
- `SYN backlog`
- `listen overflow`
- `somaxconn`
- `tcp_max_syn_backlog`
- `tcp_abort_on_overflow`
- `SYN cookie`
- `connection storm`

## 깊이 들어가기

### 1. backlog는 하나가 아니라 두 단계에 걸쳐 보인다

보통 서버는 `listen(fd, backlog)` 호출 뒤에 들어오는 연결을 바로 애플리케이션으로 넘기지 않는다.

- 첫 단계에서는 SYN을 받아 handshake 진행 상태를 들고 있다
- 마지막 ACK까지 오면 established 상태가 된다
- 그 뒤에야 accept queue에서 애플리케이션이 꺼내 간다

그래서 `connect timeout`이 나도 원인이 항상 네트워크 경로에 있는 것은 아니다.

- SYN 자체가 밀린 것일 수 있다
- 마지막 ACK 이후 accept queue가 꽉 찬 것일 수 있다
- 애플리케이션이 느려서 `accept()`를 늦게 하는 것일 수 있다

### 2. SYN backlog가 차면 handshake 초입에서 밀린다

이 경우 흔히 보이는 증상은 다음과 같다.

- 클라이언트 쪽 `SYN retransmission` 증가
- `SYN-SENT` 또는 `SYN-RECV` 상태 증가
- health check는 가끔 통과하지만 실제 사용자 연결은 간헐적으로 느림

서버가 바쁘지 않아 보여도 다음 요소가 초입을 막을 수 있다.

- burst traffic
- 방화벽이나 conntrack 포화
- SYN cookie 진입
- LB가 짧은 시간에 새 연결을 몰아넣는 상황

### 3. accept queue가 차면 handshake는 끝났는데 앱이 못 받는다

accept queue saturation은 더 헷갈리기 쉽다.

- TCP handshake 자체는 어느 정도 진행된다
- 하지만 애플리케이션이 연결을 받아 처리하기 전 대기열이 찬다
- 클라이언트는 간헐적으로 느린 connect, reset, timeout으로 느낄 수 있다

이 상황은 특히 다음에서 잘 나온다.

- 배포 직후 cold start 인스턴스
- TLS termination 이후 worker가 부족한 프록시
- GC pause나 event loop stall이 있는 서버
- thread pool 또는 file descriptor 여유는 있지만 accept loop가 늦는 경우

즉 "CPU가 낮다"와 "연결 수용 여력이 충분하다"는 같은 말이 아니다.

### 4. `listen(backlog)` 숫자만 키운다고 끝나지 않는다

실무에서 자주 오해하는 지점이다.

- 앱이 `backlog=4096`을 줘도 커널 `somaxconn`이 더 낮으면 상한이 잘릴 수 있다
- half-open 연결은 `tcp_max_syn_backlog` 영향을 따로 받는다
- `tcp_abort_on_overflow` 정책에 따라 overflow 시 동작이 달라진다

즉 튜닝 축은 보통 여러 개다.

- 애플리케이션 `listen()` backlog
- `net.core.somaxconn`
- `net.ipv4.tcp_max_syn_backlog`
- accept loop 처리 속도
- LB가 신규 연결을 보내는 속도

### 5. 왜 health check는 통과하는데 사용자만 실패하나

health check는 대개 조건이 훨씬 단순하다.

- 연결 빈도가 낮다
- 요청 본문이 거의 없다
- warm connection을 재사용할 수도 있다
- 전용 health endpoint가 싸다

반면 실제 트래픽은 다음이 겹친다.

- bursty 신규 연결
- TLS handshake
- auth / routing / header parsing
- request body upload

그래서 health check success만 보고 "연결도 문제없다"라고 결론 내리면 놓치는 경우가 많다.

### 6. 연결 폭주 때는 queue만이 아니라 정책도 함께 본다

queue saturation은 대개 증폭기와 함께 온다.

- retry가 신규 연결 수를 늘린다
- keep-alive가 짧으면 매 요청이 새 handshake를 만든다
- 드레인 중인 인스턴스에도 새 연결이 들어간다
- autoscaling 직후 warm-up 전 노드가 대량 연결을 받는다

그래서 backlog 조정만으로 끝내기보다, 연결 생성률과 드레인 정책을 함께 줄여야 한다.

## 실전 시나리오

### 시나리오 1: 배포 직후 `connect timeout`이 몇 분만 튄다

가능한 원인:

- 새 인스턴스가 traffic은 받는데 accept loop가 아직 안정화되지 않았다
- TLS session cache가 비어 있어 handshake 비용이 급증했다
- readiness는 통과했지만 실제 동시 연결 burst를 아직 못 버틴다

### 시나리오 2: LB health check는 초록인데 사용자만 간헐적으로 실패한다

이 경우는 backlog 또는 accept loop 병목을 먼저 의심할 만하다.

- health check는 소수의 짧은 요청이다
- 실제 요청은 긴 body, auth, upstream fan-out이 붙는다
- queue는 순간 burst에 약하다

### 시나리오 3: `SYN retransmission`과 `ECONNRESET`가 같이 보인다

보통 하나의 지점만 문제가 아니다.

- 일부 연결은 SYN 단계에서 밀린다
- 일부는 accept queue 또는 proxy worker 부족으로 reset 된다
- retry가 다시 신규 연결을 만들어 증상을 키운다

### 시나리오 4: keep-alive를 끄자 장애가 커졌다

문제를 stale connection으로 오해하고 keep-alive를 줄였는데, 오히려 신규 handshake가 폭증해 backlog pressure가 커진 패턴이다.

## 코드로 보기

### listen 상태와 큐 길이 감각 보기

```bash
ss -ltn
ss -ltn sport = :443
```

### 커널 backlog 관련 값 확인

```bash
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
sysctl net.ipv4.tcp_abort_on_overflow
```

### overflow 관련 통계 힌트 보기

```bash
netstat -s | rg -i 'listen|SYNs to LISTEN|overflow|drop'
```

### 관찰 포인트

```text
- SYN-SENT / SYN-RECV / ESTAB / CLOSE-WAIT 분포
- accept queue saturation 시점과 deploy/autoscale 시점의 상관관계
- 신규 연결 수와 keep-alive reuse ratio
- LB health check 성공률과 실제 connect latency 차이
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| backlog 상향 | 순간 burst를 더 흡수한다 | 근본적으로 느린 accept loop를 숨길 수 있다 | 짧은 연결 폭주가 있을 때 |
| aggressive keep-alive | 신규 handshake 수를 줄인다 | stale connection 관리가 필요하다 | steady traffic가 많을 때 |
| 빠른 드레인과 slow start | 배포/스케일 이벤트를 완화한다 | 설정이 복잡하다 | LB 앞 다중 인스턴스 |
| overflow 즉시 reset | 빠르게 실패를 드러낸다 | 사용자 실패율이 더 직접적으로 보인다 | fail-fast가 중요한 경로 |

핵심은 backlog를 키우는 것보다 **연결 생성률, accept 처리 속도, 드레인 정책을 함께 맞추는 것**이다.

## 꼬리질문

> Q: SYN backlog와 accept queue의 차이는 무엇인가요?
> 핵심: SYN backlog는 handshake 중, accept queue는 handshake 완료 후 앱이 아직 받지 않은 연결이다.

> Q: health check가 통과하는데 connect timeout이 나는 이유는 무엇인가요?
> 핵심: health check는 burst와 실제 request path를 충분히 대표하지 못할 수 있다.

> Q: backlog를 늘리면 항상 해결되나요?
> 핵심: 아니다. accept loop가 느리거나 신규 연결 생성률이 과하면 큐만 더 길어질 수 있다.

## 한 줄 정리

연결 폭주를 볼 때는 "포트가 열려 있다"보다 `SYN backlog`와 `accept queue` 중 어디가 먼저 막히는지 봐야 connect timeout과 reset의 원인을 좁힐 수 있다.
