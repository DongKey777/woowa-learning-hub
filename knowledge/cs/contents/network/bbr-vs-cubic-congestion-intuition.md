# BBR vs CUBIC Congestion Intuition

> 한 줄 요약: CUBIC은 손실을 보고 속도를 조절하고, BBR은 대역폭과 RTT 모델을 보고 보내는 양을 정하므로, 네트워크 성질에 따라 체감이 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [ECN, Congestion Signal, Tail Latency](./ecn-congestion-signal-tail-latency.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)

retrieval-anchor-keywords: BBR, CUBIC, congestion control, bandwidth delay product, queue, pacing, RTT, loss-based, model-based

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

TCP 혼잡 제어의 대표적인 두 감각은 CUBIC과 BBR이다.

- `CUBIC`: 손실 기반으로 window를 키우고 줄인다
- `BBR`: bottleneck bandwidth와 RTT를 추정해서 pacing한다

둘은 "네트워크가 감당할 수 있는 속도"를 찾는다는 목적은 같지만, 접근 방식이 다르다.

### Retrieval Anchors

- `BBR`
- `CUBIC`
- `congestion control`
- `bandwidth delay product`
- `queue`
- `pacing`
- `RTT`
- `loss-based`
- `model-based`

## 깊이 들어가기

### 1. CUBIC은 무엇을 보고 조절하나

CUBIC은 손실을 중요한 신호로 본다.

- 손실이 적으면 더 보낸다
- 손실이 나면 줄인다
- 네트워크가 혼잡하다고 판단하면 보수적으로 움직인다

이 방식은 단순하고 널리 쓰이지만, 손실이 생긴 뒤에 반응한다는 한계가 있다.

### 2. BBR은 무엇이 다른가

BBR은 손실만 보지 않고, 전송 가능 대역폭과 RTT를 기반으로 동작한다.

- 얼마나 빨리 보낼 수 있는지 추정한다
- 큐를 불필요하게 키우지 않도록 pacing한다
- 손실이 없어도 과도한 큐잉을 줄이려 한다

즉 BBR은 "버티다가 줄이는" 느낌보다 **미리 맞춰 보내는** 느낌이 강하다.

### 3. 왜 체감이 다르나

네트워크 특성이 다르면 두 알고리즘의 성격 차이가 커진다.

- loss가 적고 RTT가 안정적이면 BBR이 매끄럽게 보일 수 있다
- 손실과 지터가 많은 경로에서는 CUBIC이 익숙하게 동작할 수 있다
- 대역폭이 넉넉해도 큐가 생기면 지연이 커질 수 있다

### 4. 어떤 현상이 보이나

- BBR은 throughput은 괜찮은데 큐 패턴이 다르게 보일 수 있다
- CUBIC은 손실이 나오기 전까지 좀 더 보수적일 수 있다
- 어떤 경로에서는 둘 중 하나가 tail latency를 더 좋게 만들 수 있다

### 5. 운영에서 왜 알아야 하나

클라이언트와 서버의 TCP 스택이 어떤 알고리즘을 쓰는지에 따라:

- retry 빈도
- p99 latency
- bulk transfer 체감
- long-lived connection behavior

가 달라질 수 있다.

## 실전 시나리오

### 시나리오 1: 대역폭은 충분한데 지연이 이상하다

큐가 과도하게 쌓였는지, pacing이 달라졌는지 봐야 한다.

### 시나리오 2: 한 리전은 괜찮고 다른 리전만 느리다

RTT와 loss profile이 다르면 알고리즘 체감도 달라질 수 있다.

### 시나리오 3: bulk upload는 빠른데 작은 RPC가 느리다

혼잡 제어와 [Nagle 알고리즘과 Delayed ACK](./nagle-delayed-ack-small-packet-latency.md), [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)을 함께 봐야 한다.

## 코드로 보기

### 현재 설정 확인

```bash
sysctl net.ipv4.tcp_congestion_control
ss -ti dst api.example.com
```

### 지표로 보기

```text
- pacing_rate
- cwnd
- rtt
- retrans
```

### 실험 감각

```text
CUBIC: loss-based, familiar, conservative after loss
BBR: model-based, pacing-oriented, queue-aware
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| CUBIC | 단순하고 검증됐다 | 손실 이후 반응한다 | 일반 인터넷 |
| BBR | 큐를 덜 키우며 매끄럽다 | 경로별 체감 편차가 있다 | RTT/대역폭이 중요한 경로 |
| 혼합 운영 | 환경별 최적화 가능 | 분석이 복잡하다 | 대규모 서비스 |

핵심은 어떤 알고리즘이 "더 좋다"가 아니라 **우리 경로가 어떤 혼잡 신호를 잘 받아들이는가**다.

## 꼬리질문

> Q: CUBIC과 BBR의 차이는 무엇인가요?
> 핵심: CUBIC은 손실 기반, BBR은 대역폭/RTT 모델 기반이다.

> Q: 왜 BBR이 더 매끄럽게 느껴질 수 있나요?
> 핵심: 손실을 기다리기보다 pacing으로 큐를 덜 키우려 하기 때문이다.

> Q: 어떤 환경에서 차이가 커지나요?
> 핵심: RTT, loss, queueing 특성이 다를 때 체감 차이가 커진다.

## 한 줄 정리

BBR과 CUBIC은 둘 다 혼잡 제어지만, 손실 기반이냐 모델 기반이냐의 차이 때문에 네트워크 경로별 체감 latency와 throughput이 다르게 나타난다.
