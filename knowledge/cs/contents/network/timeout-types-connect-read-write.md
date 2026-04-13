# Timeout 타입: connect, read, write

> 한 줄 요약: 타임아웃은 하나로 뭉개면 진단이 안 된다. 연결 실패, 응답 지연, 전송 정체를 분리해서 봐야 장애를 빠르게 잘라낼 수 있다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [System Design](../system-design/README.md)

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

### 2. read timeout

read timeout은 "연결은 열렸는데, 읽을 데이터가 일정 시간 안에 안 온다"에 가깝다.

이건 다음 상황에서 중요하다.

- downstream이 계산 중이다
- 프록시 뒤에서 응답이 지연된다
- 스트리밍 응답이 끊겼다

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
