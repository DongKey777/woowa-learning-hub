# TCP 혼잡 제어

> 한 줄 요약: TCP 혼잡 제어는 네트워크가 감당할 수 있는 속도로만 보내서, 재전송 폭풍과 지연 붕괴를 막는 장치다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [TCP 3-way-handshake & 4-way-handshake](./README.md#tcp-3-way-handshake--4-way-handshake)
> - [TCP 와 UDP](./README.md#tcp-와-udp)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md)
> - [BBR vs CUBIC, Congestion Intuition](./bbr-vs-cubic-congestion-intuition.md)

retrieval-anchor-keywords: TCP congestion control, cwnd, rwnd, slow start, AIMD, RTT, retransmission, queue buildup, bandwidth delay product, sender rate

---

## 왜 중요한가

TCP는 "안 끊기게 보내는 것"만이 아니라, **네트워크를 과하게 밀지 않는 것**도 책임진다.

서버가 느린 게 아니라 네트워크가 먼저 막히는 상황이 꽤 많다.

- 요청이 갑자기 몰리면 패킷 손실이 늘어난다
- 손실이 늘면 재전송이 늘어난다
- 재전송이 늘면 더 막힌다

이 악순환을 끊는 게 혼잡 제어다.

### Retrieval Anchors

- `TCP congestion control`
- `cwnd`
- `rwnd`
- `slow start`
- `AIMD`
- `RTT`
- `retransmission`
- `queue buildup`

---

## 핵심 개념

### 전송 제어와 혼잡 제어는 다르다

- `flow control`은 수신자가 감당할 수 있는 속도를 맞추는 것
- `congestion control`은 네트워크 전체가 감당할 수 있는 속도를 맞추는 것

TCP는 둘 다 고려한다.

### 중요한 변수

- `cwnd`(congestion window): 네트워크 혼잡을 고려한 송신 가능 양
- `rwnd`(receiver window): 수신자가 받을 수 있다고 광고한 양
- 실제 전송 가능량은 대체로 `min(cwnd, rwnd)`로 제한된다
- RTT가 길수록 같은 `cwnd`라도 처리량은 떨어진다

간단히 말하면:

```text
throughput ≈ cwnd / RTT
```

그래서 같은 네트워크라도 RTT가 큰 해외 API 호출은 체감 성능이 더 나빠진다.

---

## 깊이 들어가기

### 1. Slow Start

연결 초반에는 네트워크가 얼마나 버티는지 모르기 때문에 TCP는 조심스럽게 시작한다.

- 처음에는 `cwnd`를 작게 둔다
- ACK가 오면 `cwnd`를 빠르게 키운다
- 손실 신호가 오면 덜 공격적으로 바꾼다

초기 성장 속도는 빠르다. 그래서 작은 요청에서는 금방 성능이 올라간다.

하지만 초기부터 너무 공격적으로 보내면 손실과 재전송이 터질 수 있다.

### 2. AIMD

TCP의 대표적인 혼잡 제어 사고방식은 `AIMD(Additive Increase, Multiplicative Decrease)`다.

- 잘 되면 조금씩 늘린다
- 문제가 생기면 확 줄인다

이 방식은 무식해 보여도 네트워크 전체를 망가뜨리지 않기 위한 현실적인 절충이다.

### 3. 손실이 의미하는 것

TCP에서 패킷 손실은 단순한 "에러"가 아니라 혼잡 신호로 해석된다.

- 손실이 적으면 더 보낼 수 있다고 본다
- 손실이 늘면 지금 속도가 너무 빠르다고 본다

실무에서는 손실만이 아니라 지연 증가도 함께 본다.  
패킷이 사라지지 않아도 큐에 오래 쌓이면 사용자 체감은 이미 나빠진다.

### 4. 재전송과 애플리케이션 체감

TCP 재전송이 늘면 애플리케이션은 다음 현상을 겪는다.

- 응답 지연 증가
- 타임아웃 증가
- 상위 계층 retry 증가
- retry 폭풍 가능성 증가

즉 TCP 혼잡 제어는 네트워크 계층 문제 같지만, 결국 애플리케이션 SLA와 연결된다.

### 5. 커널과 관찰 포인트

Linux에서 확인할 때는 이런 도구가 유용하다.

```bash
sysctl net.ipv4.tcp_congestion_control
ss -ti
tcpdump -i eth0 host api.example.com
```

`ss -ti`는 연결별 RTT, 재전송, congestion window 상태를 보는데 도움이 된다.

---

## 실전 시나리오

### 시나리오 1: API 서버는 멀쩡한데 응답이 느리다

원인은 애플리케이션이 아니라 네트워크 혼잡일 수 있다.

- 해외 리전 호출
- 대역폭 포화
- 재전송 증가
- RTT 증가

이 경우 서버 CPU를 먼저 의심하면 시간을 낭비한다.

### 시나리오 2: 대용량 파일 업로드가 다른 요청까지 느리게 만든다

한 사용자의 큰 업로드가 연결과 대역폭을 오래 잡아먹으면 다른 요청의 처리량이 떨어질 수 있다.

대응은 보통:

1. 업로드와 API 트래픽 경로를 분리한다
2. 대용량 전송은 별도 엔드포인트로 보낸다
3. 필요하면 속도 제한이나 chunking을 둔다

### 시나리오 3: retry가 서버를 더 괴롭힌다

TCP 혼잡으로 느려졌는데 애플리케이션이 timeout을 짧게 잡고 retry를 반복하면 상황이 더 악화된다.

이건 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 바로 연결된다.

---

## 코드로 보기

### 혼잡 상태를 확인하는 명령

```bash
ss -ti dst 203.0.113.10
```

출력에서 주로 보는 것은:

- `cwnd`
- `rtt`
- `retrans`
- `pacing_rate`

### 처리량 감각을 보는 간단한 계산

```text
대략적인 처리량 = cwnd / RTT
```

예를 들어:

- `cwnd`가 120KB
- RTT가 30ms

이면 네트워크가 이상 없이 굴 때 대략적인 전송량은 다음처럼 감으로 볼 수 있다.

```text
120KB / 0.03s ≈ 4MB/s
```

이 수치는 정확한 벤치마크가 아니라, RTT와 `cwnd`가 같이 중요하다는 감각을 잡기 위한 것이다.

### 간단한 관찰 스크립트

```bash
while true; do
  ss -ti state established '( dport = :443 )'
  sleep 1
done
```

짧은 시간에 `cwnd`와 `retrans`가 흔들리면 네트워크 경로를 의심할 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 보는가 |
|--------|------|------|-------------|
| 느린 시작 | 손실을 줄인다 | 초반 성능이 보수적이다 | 혼잡을 잘 모를 때 |
| 공격적 증가 | 초반 처리량이 빠르다 | 손실과 재전송이 늘 수 있다 | 짧고 안정적인 경로일 때 |
| AIMD | 단순하고 안정적이다 | 급격한 회복은 느리다 | 일반적인 TCP 전송 |
| timeout만 길게 잡기 | 실패는 덜 보인다 | 사용자 체감이 나빠진다 | 잘못된 대응 |

핵심은 "빠르게 보내기"가 아니라 **망가지지 않을 속도를 찾는 것**이다.

---

## 면접에서 자주 나오는 질문

### Q. flow control과 congestion control의 차이는?

- flow control은 수신자가 받을 수 있는 양을 맞추는 것이고, congestion control은 네트워크 전체 혼잡을 고려해 보내는 양을 맞추는 것이다.

### Q. 왜 손실이 나면 전송 속도가 줄어드나요?

- 패킷 손실을 네트워크 혼잡의 신호로 보기 때문이다. 손실이 계속되면 더 보내는 것이 상황을 악화시킬 수 있다.

### Q. RTT가 길어지면 왜 느려지나요?

- 같은 `cwnd`라도 한 번에 왕복하는 속도가 느려져 처리량이 줄어들기 때문이다.

### Q. 애플리케이션 retry와 TCP 혼잡 제어는 어떻게 연결되나요?

- TCP가 이미 느려진 상태에서 앱이 재시도를 반복하면 네트워크와 서버 둘 다 더 바빠질 수 있다.

---

## 한 줄 정리

TCP 혼잡 제어는 네트워크가 감당할 수 있는 양을 자동으로 조절해서, 손실과 지연의 악순환을 막는 메커니즘이다.
