---
schema_version: 3
title: "MTU, Fragmentation, MSS, Blackhole"
concept_id: network/mtu-fragmentation-mss-blackhole
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- mtu
- fragmentation
- pmtud-blackhole
aliases:
- MTU
- fragmentation
- MSS
- PMTUD
- MTU blackhole
- ICMP fragmentation needed
- MSS clamping
- tunnel overhead
symptoms:
- 특정 큰 요청만 느리거나 멈추는데 서버 CPU와 짧은 API는 정상이다
- ICMP fragmentation needed가 막혀 PMTUD가 실패하는 blackhole을 놓친다
- VPN 터널 오버헤드로 실제 path MTU가 줄어드는 문제를 앱 timeout으로 본다
- fragmentation이 가능하다는 이유로 운영에서 안전하다고 가정한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/tcp-congestion-control
- network/timeout-retry-backoff-practical
next_docs:
- network/mtu-pmtud-icmp-blackhole-path-diagnostics
- network/udp-fragmentation-quic-packetization
- network/http3-quic-practical-tradeoffs
- network/tls-record-sizing-flush-streaming-latency
linked_paths:
- contents/network/tcp-congestion-control.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/http3-quic-practical-tradeoffs.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
- contents/network/mtu-pmtud-icmp-blackhole-path-diagnostics.md
confusable_with:
- network/mtu-pmtud-icmp-blackhole-path-diagnostics
- network/udp-fragmentation-quic-packetization
- network/packet-loss-jitter-reordering-diagnostics
- network/http3-quic-practical-tradeoffs
forbidden_neighbors: []
expected_queries:
- "MTU fragmentation MSS blackhole 문제를 어떻게 설명해?"
- "ICMP fragmentation needed가 막히면 PMTUD가 왜 실패해?"
- "VPN 터널 뒤에서 큰 요청만 멈추는 MTU blackhole 패턴은?"
- "MSS clamping이 MTU 문제에서 왜 실무적으로 유용해?"
- "fragmentation은 가능하지만 운영에서 피하려는 이유는?"
contextual_chunk_prefix: |
  이 문서는 MTU, MSS, fragmentation, PMTUD, ICMP fragmentation needed,
  MTU blackhole, tunnel overhead, MSS clamping을 다루는 advanced playbook이다.
---
# MTU, Fragmentation, MSS, Blackhole

> 한 줄 요약: MTU 문제는 "패킷이 크다"가 아니라, 경로 중간 장비가 조용히 버려서 연결이 느려지거나 멈추는 운영 문제로 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)

retrieval-anchor-keywords: MTU, fragmentation, MSS, PMTUD, blackhole, ICMP fragmentation needed, DF bit, tunnel overhead, path MTU, packet too big

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [MTU와 Fragmentation](#mtu와-fragmentation)
- [MSS와 Path MTU Discovery](#mss와-path-mtu-discovery)
- [Blackhole이 생기는 이유](#blackhole이-생기는-이유)
- [실전 장애 패턴](#실전-장애-패턴)
- [코드로 보기](#코드로-보기)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제가 중요한가

MTU 이슈는 평소에는 티가 잘 안 난다.

- 짧은 API 요청은 정상처럼 보인다
- 특정 요청만 유독 느리다
- 재시도하면 가끔 된다
- 운영자가 보면 서버 CPU는 멀쩡하다

그래서 MTU 문제는 종종 애플리케이션 문제, TLS 문제, 네트워크 불안정으로 오해된다.

핵심은 **경로 중간에 있는 장비가 더 큰 패킷을 처리하지 못할 때 어떤 일이 벌어지는가**다.

### Retrieval Anchors

- `MTU`
- `fragmentation`
- `MSS`
- `PMTUD`
- `blackhole`
- `ICMP fragmentation needed`
- `tunnel overhead`
- `path MTU`

---

## MTU와 Fragmentation

### MTU란

`MTU(Maximum Transmission Unit)`는 한 번에 전송할 수 있는 패킷의 최대 크기다.

- 이더넷은 흔히 1500 bytes를 기본으로 본다
- VPN, 터널, 클라우드 오버레이를 타면 더 줄어들 수 있다
- MTU는 링크별 특성이고, 경로 전체는 그보다 더 보수적으로 봐야 한다

### Fragmentation이란

패킷이 MTU보다 크면 쪼개서 보내야 한다.

- IP 계층에서 조각나면 `fragmentation`이 발생한다
- 조각이 중간에 하나라도 빠지면 원본 복원이 실패한다
- 조각이 많아질수록 손실과 재조립 비용이 늘어난다

실무에서는 fragmentation 자체를 적극적으로 쓰기보다, 애초에 **작게 보내는 방향**을 선호한다.

### 왜 피하려고 하나

- 중간 장비가 fragment를 다루기 싫어한다
- 방화벽이 fragment를 드롭하기도 한다
- 추적과 디버깅이 어려워진다

즉 fragmentation은 "이론적으로 가능"과 "운영에서 안전"이 다르다.

---

## MSS와 Path MTU Discovery

### MSS란

`MSS(Maximum Segment Size)`는 TCP payload가 한 세그먼트에 담길 수 있는 최대 크기다.

- MTU에서 IP/TCP 헤더를 뺀 값으로 생각하면 된다
- 실제로는 이 값을 기준으로 TCP가 보내는 덩어리를 맞춘다
- 그래서 TCP에서는 MTU보다 MSS를 더 자주 조정한다

### Path MTU Discovery

경로 상에서 가장 작은 MTU를 찾아, 그 크기에 맞춰 보내려는 방식이다.

- 보통은 큰 패킷을 보내보고
- 중간 장비가 `ICMP Fragmentation Needed` 같은 신호를 돌려주면
- 그보다 작은 크기로 조정한다

문제는 이 신호가 막히면 경로 탐지가 실패한다는 점이다.

### MSS clamping

VPN, NAT, LB, 터널 구간에서는 MSS를 강제로 낮추는 방식이 자주 쓰인다.

- 경로를 완벽히 알기 어렵다
- 중간에서 ICMP가 막힐 수 있다
- 그래서 최초부터 안전한 MSS로 제한한다

운영 관점에서는 이게 가장 단순하고 덜 아픈 해결책인 경우가 많다.

---

## Blackhole이 생기는 이유

`MTU blackhole`은 패킷이 너무 커서 중간에서 버려지는데, 송신자가 그 사실을 제대로 못 알아채는 상황이다.

### 대표 원인

- ICMP 메시지가 방화벽에서 차단된다
- PMTUD가 작동하지 않는다
- 터널/VPN 헤더 때문에 실제 경로 MTU가 생각보다 작다
- 일부 장비가 fragment 또는 oversized packet을 조용히 드롭한다

### 왜 조용히 고장 나나

TCP는 손실을 재전송으로 흡수하려고 한다.

- 작은 패킷은 정상적으로 흐른다
- 큰 패킷만 계속 실패한다
- retry를 해도 같은 크기라면 계속 실패한다

그래서 사용자는 "가끔 느림"으로 느끼고, 운영자는 "원인 불명 timeout"으로 본다.

### 특히 많이 보이는 환경

- VPN 접속 뒤의 사내 시스템
- 클라우드 VPC 피어링
- 로드밸런서 뒤의 서비스 체인
- TLS가 붙은 큰 응답, 특히 헤더가 많은 경우

---

## 실전 장애 패턴

### 1. 로그인은 되는데 특정 API만 timeout이 난다

원인 후보:

- 요청 바디가 크다
- 응답 헤더가 크다
- MTU가 작은 경로를 지나고 있다
- ICMP 차단으로 PMTUD가 깨졌다

### 2. 작은 요청은 괜찮고, 큰 응답만 실패한다

이건 MTU blackhole의 전형적인 신호다.

- 리스트 API는 정상
- 파일 다운로드나 대형 JSON 응답만 실패
- gzip 여부에 따라 증상이 달라지기도 한다

### 3. VPN 뒤에서만 느리다

터널 헤더가 추가되면 실제 payload가 줄어든다.

- 기본 MTU를 그대로 쓰면 패킷이 커진다
- 중간에서 잘리거나 드롭된다
- MSS clamp나 MTU 조정이 필요하다

### 4. TLS 붙인 뒤부터 문제가 보인다

TLS 자체가 MTU를 깨는 건 아니지만,

- 헤더와 레코드 경계
- 프록시 체인
- HTTP/2, 쿠키, 인증 헤더 증가

같은 이유로 실제 패킷 크기가 커질 수 있다.

---

## 코드로 보기

### MTU 확인

```bash
ip link show
ip route get 203.0.113.10
```

### 경로 MTU 감지

```bash
tracepath api.example.com
```

### 패킷 크기 테스트

```bash
ping -M do -s 1472 api.example.com
```

이 테스트는 MTU 1500 환경에서 헤더를 뺀 payload를 기준으로 맞추는 감각을 보는 데 유용하다.

### TCP 세그먼트 관찰

```bash
tcpdump -i eth0 host api.example.com
ss -ti dst api.example.com
```

관찰 포인트:

- retransmission이 늘어나는지
- MSS가 의도한 값으로 잡히는지
- 특정 경로에서만 손실이 반복되는지

### 운영에서 볼 설정 감각

```nginx
proxy_buffering off;
proxy_http_version 1.1;
```

버퍼링이나 연결 재사용 자체가 MTU 문제를 해결하지는 않지만, 증상을 숨기거나 더 잘 드러나게 만들 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| fragmentation 허용 | 큰 패킷도 전달 가능 | 손실과 디버깅 비용 증가 | 제한적으로만 |
| MSS clamping | 운영이 단순하다 | 전 구간 최적화는 아니다 | VPN, 터널, LB |
| PMTUD 의존 | 경로에 맞게 자동 조정 | ICMP 차단에 취약하다 | 네트워크가 정상적일 때 |
| 패킷을 작게 설계 | 가장 안전하다 | 프로토콜 설계 제약이 생긴다 | API, 메시징, 업로드 |

핵심은 **MTU는 성능 최적화보다 장애 회피 관점에서 먼저 다뤄야 한다**는 점이다.

---

## 면접에서 자주 나오는 질문

### Q. MTU와 MSS의 차이는 무엇인가요?

- MTU는 링크 계층 기준의 최대 전송 단위이고, MSS는 TCP 세그먼트의 payload 최대 크기다.

### Q. Path MTU Discovery는 왜 필요한가요?

- 경로 중 가장 작은 MTU에 맞춰 패킷 크기를 조정해 fragmentation과 손실을 줄이기 위해서다.

### Q. MTU blackhole은 왜 생기나요?

- 큰 패킷이 중간에서 드롭되는데, 그 사실을 알려주는 ICMP가 막혀서 송신자가 크기를 줄이지 못하기 때문이다.

### Q. 실무에서는 어떻게 막나요?

- MSS clamping, MTU 조정, ICMP 허용, 터널 구간 재설계처럼 경로 전체를 기준으로 보수적으로 맞춘다.

---

## 한 줄 정리

MTU 문제는 "패킷이 안 간다"가 아니라, **경로 상의 작은 MTU와 ICMP 차단 때문에 조용히 실패하는 운영 장애**다.
