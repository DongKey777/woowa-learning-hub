---
schema_version: 3
title: "QUIC Connection Migration, Path Change"
concept_id: network/quic-connection-migration-path-change
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- quic
- connection-migration
- path-validation
aliases:
- QUIC connection migration
- QUIC path change
- connection ID
- NAT rebinding
- mobility
- path validation
- HTTP/3 migration
- UDP endpoint change
symptoms:
- QUIC connection migration을 IP가 바뀌어도 무조건 자동 유지되는 기능으로 본다
- path validation, LB UDP state, firewall policy가 맞아야 한다는 점을 놓친다
- 모바일 Wi-Fi LTE 전환 후 latency 증가를 migration success/failure와 연결하지 못한다
- NAT rebinding과 명시적 network migration을 같은 사건으로 뭉갠다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/http3-quic-practical-tradeoffs
- network/packet-loss-jitter-reordering-diagnostics
next_docs:
- network/quic-version-negotiation-fallback
- network/udp-fragmentation-quic-packetization
- network/happy-eyeballs-dual-stack-racing
- network/nat-keepalive-tuning-connection-lifetime
linked_paths:
- contents/network/http3-quic-practical-tradeoffs.md
- contents/network/dns-cdn-websocket-http2-http3.md
- contents/network/packet-loss-jitter-reordering-diagnostics.md
- contents/network/tls-session-resumption-0rtt-replay-risk.md
- contents/network/load-balancer-healthcheck-failure-patterns.md
confusable_with:
- network/quic-version-negotiation-fallback
- network/http3-quic-practical-tradeoffs
- network/happy-eyeballs-dual-stack-racing
- network/nat-keepalive-tuning-connection-lifetime
forbidden_neighbors: []
expected_queries:
- "QUIC connection migration은 IP와 port가 바뀌어도 어떻게 연결을 유지해?"
- "QUIC path validation이 migration에서 왜 필요해?"
- "Wi-Fi에서 LTE로 바뀐 뒤 HTTP/3 연결이 유지되거나 끊기는 이유는?"
- "NAT rebinding과 QUIC connection migration은 어떻게 달라?"
- "LB와 firewall이 QUIC migration을 막을 수 있는 지점은?"
contextual_chunk_prefix: |
  이 문서는 QUIC connection ID, NAT rebinding, path change, path validation,
  모바일 network migration, UDP LB/firewall 정책을 다루는 advanced playbook이다.
---
# QUIC Connection Migration, Path Change

> 한 줄 요약: QUIC의 connection migration은 IP가 바뀌어도 연결을 이어가게 하지만, 경로 검증과 LB/방화벽 정책이 맞아야 진짜 이득이 난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)

retrieval-anchor-keywords: QUIC connection migration, path change, connection ID, NAT rebinding, mobility, path validation, HTTP/3, UDP, endpoint change

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

QUIC은 Connection ID를 통해 IP와 포트가 바뀌어도 같은 연결로 계속 이어질 수 있다.

- Wi-Fi에서 LTE로 바뀌어도 유지 가능하다
- NAT rebinding에 상대적으로 강하다
- 이동성과 네트워크 변경에 유리하다

하지만 이 기능은 자동 마법이 아니라 **새 경로가 진짜 이 연결을 이어받을 수 있는지 검증하는 절차**와 함께 동작한다.

### Retrieval Anchors

- `QUIC connection migration`
- `path change`
- `connection ID`
- `NAT rebinding`
- `mobility`
- `path validation`
- `HTTP/3`
- `UDP`

## 깊이 들어가기

### 1. 왜 migration이 필요한가

모바일/무선 환경에서는 네트워크가 자주 바뀐다.

- Wi-Fi가 끊긴다
- 셀룰러로 넘어간다
- 공용망에서 private network로 바뀐다

TCP는 이런 변화에 매우 약하다.  
QUIC은 연결 ID를 써서 경로가 바뀌어도 세션을 이어가려 한다.

### 2. path validation이 왜 중요한가

새 경로가 생겼다고 무조건 기존 연결을 그대로 믿을 수는 없다.

- 패킷이 정말 도달하는지 확인해야 한다
- 재전송/손실 특성이 바뀌었는지 봐야 한다
- 중간 장비가 UDP를 허용하는지 확인해야 한다

즉, migration은 "주소 변경"이 아니라 **새 path로 이동한 연결 검증**이다.

### 3. NAT rebinding과 어떻게 다르나

NAT 뒤에서는 source IP/port가 바뀌는 일이 흔하다.

- TCP는 이 변화에 취약하다
- QUIC은 connection ID 덕분에 대응 여지가 크다

그래도 모든 변화가 자동으로 되는 건 아니며, path validation과 timeout이 여전히 중요하다.

### 4. LB와 방화벽이 왜 중요하나

QUIC은 UDP 위에서 움직인다.

- 일부 LB는 UDP 상태 추적에 민감하다
- 일부 방화벽은 migration path를 막을 수 있다
- observability가 TCP보다 더 까다롭다

### 5. migration이 항상 좋은가

아니다. 이동성이 필요하지 않은 환경에서는 복잡도만 늘 수 있다.

- 경로 변경이 드문 서버 간 통신
- 방화벽이 엄격한 기업망
- 운영 도구가 UDP에 약한 환경

## 실전 시나리오

### 시나리오 1: 모바일 앱이 네트워크를 바꿨는데 세션이 유지된다

QUIC migration의 강점이 드러나는 상황이다.

### 시나리오 2: UDP는 되는데 특정 경로에서만 갑자기 끊긴다

path validation이 실패했거나 방화벽이 바뀐 경로를 막았을 수 있다.

### 시나리오 3: 연결은 이어졌는데 지연이 커졌다

새 path의 loss/jitter가 더 나빠졌을 수 있다.  
이 경우는 [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)와 같이 봐야 한다.

## 코드로 보기

### 관찰 관점

```bash
tcpdump -i any udp port 443
ss -tunap
```

### 운영 체크

```text
- network switch 후에도 connection ID가 유지되는가
- 새 path validation이 성공하는가
- UDP 차단 경로가 없는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| QUIC migration 활용 | 이동성과 복원력이 좋다 | 운영/방화벽 복잡도가 커진다 | 모바일, 네트워크 변경 빈번 |
| migration 최소화 | 단순하다 | 이동성 이점을 못 얻는다 | 통제된 서버 환경 |
| 혼합 운영 | 점진 전환 가능 | 관측과 fallback이 복잡하다 | 대규모 서비스 |

핵심은 이동성 이점이 큰지, 아니면 운영 복잡도가 더 큰지다.

## 꼬리질문

> Q: QUIC connection migration은 왜 필요한가요?
> 핵심: IP나 포트가 바뀌는 모바일/무선 환경에서 연결을 이어가기 위해서다.

> Q: path validation은 무엇을 하나요?
> 핵심: 새 경로가 실제로 통신 가능한지 확인한다.

> Q: TCP가 왜 이걸 못하나요?
> 핵심: TCP는 연결이 4-tuple에 강하게 묶여 있고, 경로 변경에 취약하다.

## 한 줄 정리

QUIC connection migration은 네트워크 변경에도 세션을 이어주는 강력한 기능이지만, path validation과 UDP 운영 정책이 받쳐줘야 실전 가치가 나온다.
