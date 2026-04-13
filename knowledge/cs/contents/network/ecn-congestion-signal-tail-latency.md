# ECN, Congestion Signal, Tail Latency

> 한 줄 요약: ECN은 패킷을 버리기 전에 혼잡을 먼저 알리는 신호라서, 손실보다 부드럽게 지연 악화를 줄이는 데 쓰인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)

retrieval-anchor-keywords: ECN, Explicit Congestion Notification, CWR, ECE, congestion signal, queue buildup, tail latency, AQM, RED, lossless signal

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

ECN(Explicit Congestion Notification)은 네트워크가 혼잡할 때 패킷을 버리는 대신 **마킹으로 알리는 방식**이다.

- 패킷 손실 전에 혼잡 신호를 보낸다
- 송신자는 이 신호를 보고 전송률을 줄일 수 있다
- tail latency가 나빠지기 전에 완화할 수 있다

### Retrieval Anchors

- `ECN`
- `Explicit Congestion Notification`
- `CWR`
- `ECE`
- `congestion signal`
- `queue buildup`
- `tail latency`
- `AQM`
- `RED`

## 깊이 들어가기

### 1. 왜 loss보다 먼저 알려주나

혼잡이 심해지면 가장 단순한 신호는 packet loss다. 하지만 loss는 너무 늦다.

- 큐가 이미 가득 찼다는 뜻이다
- 재전송이 발생한다
- latency spike가 커진다

ECN은 loss 전에 알려서, 송신자가 조금 더 부드럽게 속도를 줄이게 한다.

### 2. tail latency와 어떤 관계가 있나

혼잡이 커질 때 평균보다 꼬리가 먼저 나빠진다.

- 일부 요청이 큐에 오래 쌓인다
- 재전송이 생기기 전에 지연이 먼저 늘어난다
- p95/p99가 흔들린다

ECN은 이런 queue buildup을 더 빨리 드러내는 역할을 한다.

### 3. ECN은 만능이 아니다

ECN이 잘 동작하려면 경로 전체가 이를 지원해야 한다.

- OS가 ECN을 켜야 한다
- 중간 장비가 ECN 마킹을 해석해야 한다
- 정책이 손실 기반 전제에만 묶여 있지 않아야 한다

### 4. 어디서 의미가 큰가

- 대역폭이 빡빡한 데이터센터
- queue oscillation이 자주 나는 환경
- loss를 만들기 전에 부드럽게 제어하고 싶은 경로

무선이나 공용 인터넷처럼 변동성이 큰 경로에서는 ECN만으로 끝내기 어렵다.

### 5. ECN 신호는 어떻게 읽나

TCP 관점에서는 송신자가 ECE/CWR 플래그를 통해 혼잡 신호를 주고받는다.

- 수신자는 마킹을 보고 ECE를 알린다
- 송신자는 CWR로 반응한다
- 혼잡 제어는 손실보다 먼저 조정될 수 있다

## 실전 시나리오

### 시나리오 1: 손실은 적은데 p99가 계속 튄다

queue buildup이 누적되는 상황일 수 있다.

- loss는 아직 적다
- 지연은 점점 증가한다
- ECN이 있으면 더 빨리 줄일 수 있다

### 시나리오 2: 데이터센터 내부 트래픽이 갑자기 불안정하다

혼잡 신호가 loss로만 드러나면 재전송이 폭증할 수 있다.

### 시나리오 3: QUIC/TCP 혼합 경로에서 체감이 다르다

전송 계층과 혼잡 신호 처리 방식이 다르면 같은 네트워크도 다르게 보일 수 있다.

## 코드로 보기

### ECN 관련 설정 확인

```bash
sysctl net.ipv4.tcp_ecn
ss -ti dst api.example.com
```

### 혼잡 관찰

```bash
tcpdump -i eth0 host api.example.com
```

### 지표로 볼 때

```text
- retransmission이 늘기 전에 latency가 오르는가
- queue가 짧아지는 방향으로 반응하는가
- loss 없이도 혼잡 신호를 볼 수 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| loss 기반 혼잡 제어 | 보편적이다 | 늦게 반응한다 | 일반 인터넷 |
| ECN 기반 신호 | 손실 전에 완화한다 | 경로/장비 지원이 필요하다 | 제어 가능한 네트워크 |
| AQM/RED 조합 | 큐를 부드럽게 관리한다 | 튜닝이 복잡하다 | 운영 네트워크 |

핵심은 손실이 나기 전에 **혼잡을 드러내는 신호를 얼마나 빨리 보느냐**다.

## 꼬리질문

> Q: ECN은 무엇을 해결하나요?
> 핵심: 패킷 손실 전에 혼잡을 알려 더 부드럽게 전송률을 낮추게 한다.

> Q: ECN이 항상 적용되나요?
> 핵심: 아니다. OS와 경로 장비가 모두 지원해야 한다.

> Q: 왜 tail latency에 중요하죠?
> 핵심: 큐가 커질 때 손실보다 먼저 지연 꼬리가 망가지기 때문이다.

## 한 줄 정리

ECN은 손실 대신 혼잡 신호를 먼저 주는 장치라서, p99가 튀기 전에 전송을 부드럽게 줄이는 데 의미가 있다.
