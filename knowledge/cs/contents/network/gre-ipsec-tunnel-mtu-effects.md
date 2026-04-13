# GRE, IPsec Tunnel MTU Effects

> 한 줄 요약: GRE와 IPsec 터널은 헤더 오버헤드를 더해 실제 MTU를 줄이므로, PMTUD와 MSS clamp를 같이 보지 않으면 조용한 blackhole이 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [MTU, PMTUD, ICMP Blackhole Path Diagnostics](./mtu-pmtud-icmp-blackhole-path-diagnostics.md)
> - [MTU, Fragmentation, MSS, Blackhole](./mtu-fragmentation-mss-blackhole.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [NAT64, DNS64 Intuition](./nat64-dns64-operational-intuition.md)
> - [Anycast Routing Trade-offs, Edge Failover](./anycast-routing-tradeoffs-edge-failover.md)

retrieval-anchor-keywords: GRE, IPsec, tunnel MTU, encapsulation overhead, MSS clamp, PMTUD, blackhole, tunnel header, VPN path

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

GRE와 IPsec은 패킷을 또 한 번 감싸기 때문에 실제로 보낼 수 있는 payload가 줄어든다.

- tunnel header overhead가 생긴다
- 경로 MTU가 예상보다 작아진다
- PMTUD가 깨지면 blackhole이 된다

### Retrieval Anchors

- `GRE`
- `IPsec`
- `tunnel MTU`
- `encapsulation overhead`
- `MSS clamp`
- `PMTUD`
- `blackhole`
- `tunnel header`
- `VPN path`

## 깊이 들어가기

### 1. 왜 MTU가 줄어드나

터널은 원래 패킷을 다른 패킷에 넣는다.

- GRE 헤더가 추가된다
- IPsec이 암호화/인증 오버헤드를 더한다
- 실제로 남는 payload가 작아진다

### 2. 왜 조용히 실패하나

터널 뒤쪽의 경로 MTU가 작아도 ICMP가 막히면 송신자가 못 배운다.

- 작은 요청은 된다
- 큰 응답만 실패한다
- retry로도 잘 안 풀린다

### 3. GRE와 IPsec이 같이 쓰이면

오버헤드가 더 커진다.

- 패킷이 더 쉽게 fragment 된다
- PMTUD 의존도가 높아진다
- MSS clamp가 사실상 필요할 수 있다

### 4. 어디서 흔한가

- site-to-site VPN
- 사내망 연결
- 클라우드 간 터널
- edge to edge 보안 경로

### 5. 운영에서 보아야 할 것

- tunnel mode인지 transport mode인지
- 실제 경로 MTU
- ICMP 차단 여부
- MSS clamp 적용 여부

## 실전 시나리오

### 시나리오 1: 터널 안에서만 큰 응답이 실패한다

MTU blackhole 또는 MSS mismatch를 의심한다.

### 시나리오 2: IPsec을 붙인 뒤 느려졌다

packetization이 바뀌고 재전송이 늘었을 수 있다.

### 시나리오 3: 특정 VPN 사용자만 이상하다

client-side tunnel MTU가 다를 수 있다.

## 코드로 보기

### 확인 명령

```bash
ip link show
ip route get 203.0.113.10
tracepath 203.0.113.10
```

### 관찰 포인트

```text
- encapsulation overhead
- actual path MTU
- ICMP feedback
- MSS clamp present?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| GRE/IPsec tunnel | 보안과 연결성이 좋다 | MTU 오버헤드가 생긴다 | 사내/사이트 간 연결 |
| direct routing | 단순하다 | 보안과 경로 통제가 약하다 | 단순 경로 |
| tunnel + MSS clamp | blackhole 완화 | 근본 MTU를 바꾸진 않는다 | 운영 안정화 |

핵심은 터널을 넣을수록 경로 MTU를 다시 계산해야 한다는 점이다.

## 꼬리질문

> Q: GRE/IPsec이 왜 MTU를 줄이나요?
> 핵심: 패킷에 추가 헤더와 암호화 오버헤드가 붙기 때문이다.

> Q: 왜 blackhole이 생기나요?
> 핵심: PMTUD 피드백이 막히면 송신자가 큰 패킷을 계속 보내기 때문이다.

> Q: MSS clamp는 왜 쓰나요?
> 핵심: 터널 뒤의 실제 MTU에 맞춰 처음부터 작게 보내기 위해서다.

## 한 줄 정리

GRE와 IPsec 터널은 encapsulation overhead로 실제 MTU를 줄이므로, PMTUD와 MSS clamp를 함께 맞춰야 한다.
