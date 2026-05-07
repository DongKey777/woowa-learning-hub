---
schema_version: 3
title: 'Timeout 타입: connect, read, write'
concept_id: network/timeout-types-connect-read-write
canonical: true
category: network
difficulty: intermediate
doc_role: primer
level: intermediate
language: ko
source_priority: 90
review_feedback_tags:
- timeout-types-connect
- read-write
- connect-timeout
- read-timeout
aliases:
- connect timeout
- read timeout
- write timeout
- timeout 종류
- connect read write timeout 차이
- response timeout
- pool acquisition timeout
- timeout budget
intents:
- definition
- comparison
- troubleshooting
linked_paths:
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md
- contents/network/upstream-queueing-connection-pool-wait-tail-latency.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
confusable_with:
- network/request-timing-decomposition
- network/timeout-budget-propagation-proxy-gateway-service-hop-chain
- network/upstream-queueing-connection-pool-wait-tail-latency
forbidden_neighbors: []
expected_queries:
- connect timeout과 read timeout과 write timeout은 어떻게 달라?
- 서버 로그가 없고 timeout이면 connect 단계부터 봐야 해?
- 연결은 됐는데 첫 바이트가 늦으면 어떤 timeout을 봐야 해?
- 업로드 중간에 멈추면 read timeout이야 write timeout이야?
- timeout budget과 per-hop timeout을 처음에 어떻게 나눠 봐야 해?
contextual_chunk_prefix: |
  이 문서는 timeout을 하나로 뭉개지 않고 connect timeout, read timeout,
  write timeout, DNS/TLS, pool acquisition, timeout budget으로 처음 분해하는
  network primer다. 서버 로그 없음, 연결은 됐는데 응답 첫 바이트 지연,
  업로드/streaming 전송 정체, proxy/service hop별 timeout 불일치 같은 query를
  request timing decomposition과 retry/backoff 학습으로 연결한다.
---
# Timeout 타입: connect, read, write

> 한 줄 요약: 타임아웃은 하나로 뭉개면 진단이 안 된다. 연결 실패, 응답 지연, 전송 정체를 분리해서 봐야 장애를 빠르게 잘라낼 수 있다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
- [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
- [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
- [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
- [Spring Request Lifecycle Timeout/Disconnect/Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
- [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)

retrieval-anchor-keywords: connect timeout basics, read timeout basics, write timeout basics, timeout 종류 뭐예요, connect read write timeout 차이, 왜 read timeout만 나요, 언제 write timeout 봐요, tls handshake timeout, pool acquisition timeout, timeout budget, per-hop timeout, 처음 timeout 헷갈려요, request timeout what is, connect timeout vs read timeout

---

## 핵심 개념

타임아웃은 "오래 기다리지 않기"가 아니라 **어디에서 멈출지 경계를 나누는 것**이다.

실무에서 자주 보는 구분:

- `connect timeout`: 소켓 연결이 맺어지기까지 기다리는 시간
- `read timeout`: 연결은 됐지만 응답 데이터가 안 오거나 너무 느릴 때의 대기 시간
- `write timeout`: 요청 바디를 보내는 중 상대가 너무 느려 전송이 막힐 때의 제한 시간

실제로는 여기에 더해:

- `DNS timeout`
- `TLS handshake timeout`
- `pool acquisition timeout`

도 따로 봐야 한다.

여기서 먼저 선을 그어 두면 헷갈림이 줄어든다.

- `connect timeout`은 "아직 연결도 못 맺었다" 쪽이다.
- `read timeout`은 "연결은 됐는데 응답이 안 온다" 쪽이다.
- `write timeout`은 "내가 보내는 중인데 상대가 못 받는다" 쪽이다.

단, 라이브러리마다 이름과 적용 구간은 조금씩 다를 수 있다. 어떤 클라이언트는 `response timeout`만 따로 두고, DNS/TLS를 별도 옵션이나 상위 request timeout으로 다루기도 한다. 그래서 용어를 외우기보다 "지금 막힌 단계가 연결 전/응답 대기/전송 중 중 어디인가"로 먼저 자르는 편이 안전하다.

## 처음 분리하는 1분 결정표

| 지금 보이는 증상 | 가장 먼저 의심할 timeout | 왜 그쪽부터 보나 |
|---|---|---|
| 서버 로그가 아예 없고 연결부터 실패한다 | `connect timeout` | 아직 TCP 연결이나 그 이전 단계에서 막혔을 가능성이 크다 |
| 연결은 됐는데 첫 바이트가 늦게 온다 | `read timeout` | 상대가 계산 중이거나 중간 hop에서 응답이 지연될 수 있다 |
| 업로드나 스트리밍 전송 중간에 멈춘다 | `write timeout` | 보내는 쪽 backpressure, 느린 소비자, 버퍼 정체를 먼저 봐야 한다 |
| 증상이 hop마다 다르고 proxy마다 timeout이 다르다 | `timeout budget` | 단일 앱 timeout보다 hop별 예산 불일치가 더 흔한 원인일 수 있다 |
| DB 커넥션을 못 빌려서 요청이 오래 선다 | `pool acquisition timeout` | 네트워크보다 풀 고갈이 먼저 막힌 상황일 수 있다 |

---

## 깊이 들어가기

### 1. connect timeout

connect timeout은 보통 TCP 연결 수립이 지연될 때 적용된다.

이 단계에서 느린 원인:

- 대상 서버 다운
- 방화벽 / 네트워크 경로 문제
- SYN 재전송
- DNS 문제는 별도 단계일 수 있음

주의할 점:

- connect timeout이 길다고 해서 응답이 느린 문제까지 해결되진 않는다
- 연결 수립 실패와 서버 응답 지연은 다른 문제다
- DNS lookup이나 TLS handshake를 connect timeout에 포함할지는 도구마다 다르다

### 2. read timeout

read timeout은 "연결은 열렸는데, 읽을 데이터가 일정 시간 안에 안 온다"에 가깝다.

이건 다음 상황에서 중요하다.

- downstream이 계산 중이다
- 프록시 뒤에서 응답이 지연된다
- 스트리밍 응답이 끊겼다
- connection pool 대기와 read timeout을 같은 증상으로 착각하기 쉽다

### 3. write timeout

write timeout은 요청 바디를 보내는 중 상대가 너무 느리거나 버퍼가 꽉 차는 경우를 막는다.

예:

- 대용량 업로드
- 느린 소비자에게 스트리밍 전송
- TCP 혼잡으로 전송률이 떨어짐

### 4. 하나로 뭉개면 생기는 문제

전체 요청 timeout 하나만 두면:

- 어디서 느린지 구분이 안 된다
- retry 기준을 세우기 어렵다
- 운영자가 장애 원인을 잘못 짚는다

그래서 클라이언트 라이브러리와 proxy 설정은 분리해서 보는 편이 좋다.
특히 `write timeout`은 [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md), `pool acquisition timeout`은 [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)와 같이 보면 진단이 빨라진다.

---

## 실전 시나리오

### 시나리오 1: connect timeout이 자주 난다

원인 후보:

- LB 죽음
- DNS 문제
- 네트워크 경로 문제
- 대상 서버 과부하로 연결 수락이 밀림

이때 read timeout만 늘려도 해결되지 않는다.

### 시나리오 2: read timeout만 난다

연결은 됐는데 응답이 늦다.

체크할 것:

1. downstream CPU/GC
2. DB 쿼리 지연
3. proxy buffering
4. HTTP/2 multiplexing과 TCP HOL blocking

### 시나리오 3: 업로드만 자꾸 끊긴다

write timeout 또는 proxy/body size 제한일 수 있다.

이 경우:

- chunk upload를 고려한다
- 업로드와 API 경로를 분리한다
- read timeout만 조정하는 건 효과가 없다
- proxy의 request body size, idle timeout도 같이 확인한다

---

## 코드로 보기

### Spring WebClient 예시

```java
HttpClient httpClient = HttpClient.create()
    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 1000)
    .responseTimeout(Duration.ofSeconds(2));

WebClient webClient = WebClient.builder()
    .clientConnector(new ReactorClientHttpConnector(httpClient))
    .build();
```

### OkHttp 예시

```java
OkHttpClient client = new OkHttpClient.Builder()
    .connectTimeout(Duration.ofSeconds(1))
    .readTimeout(Duration.ofSeconds(2))
    .writeTimeout(Duration.ofSeconds(2))
    .build();
```

### 감각을 잡는 기준

```text
connect timeout: "연결 자체가 안 되면 빨리 포기"
read timeout: "응답이 너무 늦으면 끊기"
write timeout: "보내는 중 막히면 끊기"
```

여기서 `request timeout`은 위 셋을 감싸는 상위 제한으로 구현되는 경우가 많다. 그래서 "request timeout만 늘렸는데 왜 upload는 계속 끊기지?" 같은 질문이 나오면 하위 timeout이 따로 있는지 먼저 본다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| connect/read/write 분리 | 진단이 쉽다 | 설정 포인트가 늘어난다 | 운영 안정성이 중요할 때 |
| 단일 timeout | 단순하다 | 병목 위치를 못 가른다 | 아주 단순한 내부 호출 |
| 짧은 timeout | 장애를 빨리 드러낸다 | 오탐이 늘 수 있다 | 외부 의존성이 많을 때 |
| 긴 timeout | 실패를 덜 본다 | 자원을 오래 잡아먹는다 | 거의 쓰지 말아야 할 선택 |

핵심은 **실패를 빨리 숨기지 말고, 정확히 분류하는 것**이다.

---

## 꼬리질문

> Q: connect timeout과 read timeout의 차이는?
> 의도: 연결 실패와 응답 지연을 분리해서 이해하는지 확인
> 핵심: connect는 연결 수립, read는 수립 이후 데이터 수신

> Q: write timeout이 왜 필요한가?
> 의도: 업로드/스트리밍/느린 상대와의 전송을 이해하는지 확인
> 핵심: 보내는 과정이 막히는 것도 장애다

## 한 줄 정리

타임아웃은 하나로 대충 잡는 값이 아니라, 연결과 전송의 어느 단계에서 실패할지 구분하는 진단 도구다.
