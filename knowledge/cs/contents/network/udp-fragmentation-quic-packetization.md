# UDP Fragmentation, QUIC Packetization

> 한 줄 요약: UDP는 조각난 패킷의 손실을 TCP처럼 흡수하지 못하므로, QUIC은 packetization과 MTU를 훨씬 더 신중하게 다뤄야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [MTU, PMTUD, ICMP Blackhole Path Diagnostics](./mtu-pmtud-icmp-blackhole-path-diagnostics.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [QUIC Connection Migration, Path Change](./quic-connection-migration-path-change.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [TCP Fast Open Trade-offs](./tcp-fast-open-tradeoffs.md)

retrieval-anchor-keywords: UDP fragmentation, QUIC packetization, PMTU, datagram, loss, reassembly, MTU, crypto overhead, path MTU

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

UDP는 TCP처럼 세그먼트 재전송과 순서 보장을 제공하지 않는다.

- 조각난 UDP fragment가 하나만 빠져도 전체 datagram이 죽을 수 있다
- QUIC은 이를 피하려고 packetization과 PMTU를 매우 중요하게 다룬다
- 큰 payload를 무심코 쪼개지 않도록 설계해야 한다

### Retrieval Anchors

- `UDP fragmentation`
- `QUIC packetization`
- `PMTU`
- `datagram`
- `loss`
- `reassembly`
- `MTU`
- `crypto overhead`
- `path MTU`

## 깊이 들어가기

### 1. UDP fragmentation이 왜 위험한가

UDP는 메시지 경계가 있지만, 네트워크는 여전히 MTU 제약을 받는다.

- 패킷이 너무 크면 fragment로 쪼개질 수 있다
- fragment 하나만 잃어도 전체 datagram이 실패한다
- 재조립은 TCP보다 훨씬 취약하게 보일 수 있다

### 2. QUIC이 packetization을 조심하는 이유

QUIC은 UDP 위에서 동작하지만, 안정성은 스스로 챙겨야 한다.

- MTU를 고려해 packet size를 제한한다
- 암호화 오버헤드까지 감안해야 한다
- path change와 손실 환경에서 깨지지 않게 해야 한다

### 3. PMTU가 왜 중요하나

QUIC은 경로 MTU가 얼마인지 잘못 추정하면 손실이 커질 수 있다.

- 큰 packet은 blackhole에 걸릴 수 있다
- 작은 packet은 오버헤드가 커진다
- 적절한 균형이 필요하다

### 4. 왜 TCP보다 더 민감해 보이나

TCP는 재전송과 흐름 제어가 내장돼 있다.

- UDP는 그런 보호가 약하다
- QUIC이 이를 메우지만, packetization 실수는 그대로 체감된다
- 손실과 지터를 packet 크기로 더 민감하게 느낄 수 있다

### 5. 운영에서 보는 신호

- path MTU보다 큰 packet을 보내는가
- 특정 네트워크에서만 loss가 커지는가
- QUIC packet size가 지나치게 큰가

## 실전 시나리오

### 시나리오 1: HTTP/3는 되는데 특정 네트워크에서만 끊긴다

UDP fragmentation, PMTU, middlebox 문제일 수 있다.

### 시나리오 2: 큰 스트림이 작은 요청까지 느리게 만든다

packetization과 loss 복구가 연결 전체 체감을 흔들 수 있다.

### 시나리오 3: VPN이나 터널 뒤에서만 QUIC이 불안정하다

MTU blackhole과 조각화 문제가 겹쳤을 수 있다.

## 코드로 보기

### 관찰

```bash
tcpdump -i any udp port 443
ss -tunap
```

### 감각

```text
small QUIC packets
-> fewer fragmentation risks
-> more overhead

large QUIC packets
-> better efficiency
-> more MTU risk
```

### 체크 포인트

```text
- packet size under path MTU
- fragmentation avoided
- loss under specific networks
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 큰 packet | 오버헤드가 적다 | MTU/fragmentation 위험이 크다 | 안정 경로 |
| 작은 packet | 손실/blackhole에 강하다 | 오버헤드가 늘어난다 | 변동성 큰 경로 |
| adaptive packetization | 균형이 좋다 | 구현/튜닝이 복잡하다 | QUIC 운영 |

핵심은 UDP 위에서는 packet 크기 자체가 운영 안정성의 일부라는 점이다.

## 꼬리질문

> Q: UDP fragmentation이 왜 위험한가요?
> 핵심: fragment 하나만 사라져도 전체 datagram이 실패하기 때문이다.

> Q: QUIC packetization이 왜 중요한가요?
> 핵심: UDP 위에서 MTU와 loss를 직접 다뤄야 하기 때문이다.

> Q: 큰 packet과 작은 packet의 trade-off는?
> 핵심: 효율과 안정성의 균형이다.

## 한 줄 정리

UDP fragmentation은 손실에 취약하므로, QUIC은 packetization과 MTU를 조심스럽게 맞춰야 안정적으로 동작한다.
