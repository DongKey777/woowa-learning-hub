# Packet Loss, Jitter, Reordering Diagnostics

> 한 줄 요약: 패킷 손실, 지터, 재정렬은 같은 "느림"으로 보이지만 원인이 달라서, 재전송과 지연 분포를 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [MTU, Fragmentation, MSS, Blackhole](./mtu-fragmentation-mss-blackhole.md)
> - [Nagle 알고리즘과 Delayed ACK](./nagle-delayed-ack-small-packet-latency.md)

retrieval-anchor-keywords: packet loss, jitter, reordering, retransmission, out-of-order, tail latency, p95, p99, tc netem, tcpdump, ss -ti

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

네트워크가 "느리다"는 말에는 적어도 세 가지 다른 현상이 섞인다.

- `packet loss`: 패킷이 사라져 재전송이 필요하다
- `jitter`: 지연이 들쭉날쭉하다
- `reordering`: 패킷이 순서와 다르게 도착한다

이 셋은 모두 사용자 체감 지연을 올리지만, 관찰 지점은 조금 다르다.

### Retrieval Anchors

- `packet loss`
- `jitter`
- `reordering`
- `retransmission`
- `out-of-order`
- `tail latency`
- `p95`
- `p99`
- `tc netem`
- `tcpdump`

## 깊이 들어가기

### 1. packet loss는 왜 가장 먼저 의심하나

패킷이 사라지면 TCP는 재전송해야 한다.

- 처리량이 줄어든다
- RTT가 늘어난 것처럼 보인다
- application timeout이 터질 수 있다

손실은 단순히 "데이터 하나 잃음"이 아니라 **전송 알고리즘이 속도를 줄이는 신호**다.  
그래서 loss가 높아지면 tail latency가 먼저 흔들리는 경우가 많다.

### 2. jitter는 왜 더 다루기 어려운가

손실이 없더라도 지연이 들쭉날쭉하면 p95/p99가 튄다.

- 평균 latency는 정상처럼 보일 수 있다
- 일부 요청만 갑자기 늦어진다
- retry와 timeout을 더 자주 건드리게 된다

즉 jitter는 "평균이 아니라 분산의 문제"다.

### 3. reordering은 왜 혼란을 주나

패킷이 순서대로 오지 않으면 TCP는 재정렬을 기다린다.

- out-of-order segment가 생긴다
- fast retransmit이 발생할 수 있다
- 스트림이 멈춘 것처럼 보일 수 있다

특히 같은 연결에 작은 요청과 큰 응답이 섞여 있으면 reordering의 체감이 더 커질 수 있다.

### 4. 세 가지는 어떻게 구분하나

실무에서는 다음 신호를 같이 본다.

- `retransmission` 증가: loss 가능성
- RTT 분포 넓어짐: jitter 가능성
- `out-of-order` 증가: reordering 가능성
- `cwnd` 감소: 손실 또는 혼잡 가능성

패킷 수치 하나만 보면 오판하기 쉽다.  
그래서 tcpdump, ss, 애플리케이션 p95/p99를 같이 본다.

### 5. 왜 tail latency가 먼저 망가지나

평균은 작은 손실을 숨긴다.

- 대부분 요청은 빠르다
- 일부만 재전송이나 재정렬을 만난다
- 그 일부가 p99를 끌어올린다

운영에서 중요한 것은 평균이 아니라 **느린 꼬리 요청이 왜 생겼는가**다.

## 실전 시나리오

### 시나리오 1: 평균은 정상인데 p99만 튄다

가능한 원인:

- loss가 간헐적으로 난다
- 지터가 커졌다
- 특정 경로에서 reordering이 늘었다

이 경우 단순 capacity 증가보다 경로 진단이 먼저다.

### 시나리오 2: 모바일 네트워크에서만 느리다

무선망은 loss, jitter, handover가 섞여 있다.

- HTTP/2는 HOL blocking 영향이 커질 수 있다
- HTTP/3는 이런 환경에서 더 유리할 수 있다

### 시나리오 3: VPN 뒤에서만 가끔 멈춘다

터널링은 MTU와 reordering 문제를 함께 만들 수 있다.

- 큰 패킷이 깨지거나 드롭된다
- 재전송이 늘어난다
- 체감은 timeout처럼 보인다

### 시나리오 4: 재시도하니 더 느려진다

손실이나 jitter가 있는데 timeout과 retry가 공격적이면 네트워크가 더 바빠진다.

- 요청이 중복된다
- queue가 쌓인다
- tail latency가 더 나빠진다

이건 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 같이 봐야 한다.

## 코드로 보기

### 관찰 명령

```bash
ss -ti dst api.example.com
tcpdump -i eth0 host api.example.com
```

### Linux에서 네트워크 에뮬레이션

```bash
sudo tc qdisc add dev eth0 root netem loss 1% delay 40ms 10ms reorder 25% 50%
sudo tc qdisc del dev eth0 root
```

이런 실험은 실제 장애를 만들려는 게 아니라, 지표가 어떻게 흔들리는지 감각을 잡는 용도다.

### 수치로 볼 때

```text
loss: 재전송 증가
jitter: latency 분산 증가
reordering: out-of-order segment 증가
```

### 애플리케이션에서 봐야 할 것

```text
connect time
time to first byte
retries
p95 / p99
timeout ratio
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 평균 latency 중심 | 보기 쉽다 | tail 문제를 숨긴다 | 대략적 모니터링 |
| p95/p99 중심 | 꼬리 문제를 드러낸다 | 원인 추적이 어렵다 | 운영 장애 분석 |
| loss/jitter/reordering 분리 | 원인에 가깝게 본다 | 계측이 복잡하다 | 성능 문제 디버깅 |

핵심은 "느리다"를 수치로 해체하는 것이다.

## 꼬리질문

> Q: loss와 jitter는 어떻게 다르나요?
> 핵심: loss는 패킷이 사라지는 것이고, jitter는 지연이 일정하지 않은 것이다.

> Q: reordering이 왜 문제가 되나요?
> 핵심: TCP가 순서를 맞추기 위해 기다리면서 응답 전달이 늦어진다.

> Q: 평균 latency가 멀쩡한데 왜 p99가 튀나요?
> 핵심: 일부 요청만 loss, jitter, reordering을 만나기 때문이다.

## 한 줄 정리

패킷 손실, 지터, 재정렬은 모두 느림으로 보이지만, 재전송 수와 지연 분포를 함께 보면 원인을 더 정확히 분해할 수 있다.
