# TCP 3-way handshake 기초

> 한 줄 요약: TCP 연결은 SYN → SYN-ACK → ACK 세 번의 패킷 교환으로 맺어지고, 이 과정이 끝나야 데이터를 주고받을 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [TCP 혼잡 제어](./tcp-congestion-control.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
- [network 카테고리 인덱스](./README.md)
- [로드밸런서 기초](../system-design/load-balancer-basics.md)

retrieval-anchor-keywords: tcp three way handshake, syn syn-ack ack, tcp 연결 맺기, 3-way handshake 뭔가요, tcp handshake 순서, 왜 3번 교환하나요, tcp 연결 확립, handshake latency, tcp 세션 수립, beginner tcp connection, tcp three way handshake basics basics, tcp three way handshake basics beginner, tcp three way handshake basics intro, network basics, beginner network

## 핵심 개념

TCP는 데이터를 보내기 전에 반드시 **연결을 먼저 확립**한다. 이 연결 과정을 3-way handshake라 부른다. 총 세 번의 패킷을 교환해서 양쪽이 서로 준비됐음을 확인한다. 입문자가 헷갈리는 지점은 "왜 2번이 아니라 3번이냐"인데, 한쪽만 보내도 됐다는 확인을 상대방이 받았음을 확인하는 단계가 별도로 필요하기 때문이다.

## 한눈에 보기

SYN, SYN-ACK, ACK 세 단계를 거쳐야 양방향 연결이 확립된다.

```
클라이언트                       서버
    |--- SYN (seq=x) ---------->|   클라이언트: "연결하고 싶어"
    |<-- SYN-ACK (seq=y, ack=x+1)|   서버: "알겠어, 나도 준비됐어"
    |--- ACK (ack=y+1) -------->|   클라이언트: "확인했어, 시작하자"
    |===== 데이터 전송 =========|
```

세 번의 교환이 끝난 뒤에야 데이터 전송이 시작된다.

## 상세 분해

### 1단계: SYN (클라이언트 → 서버)

클라이언트가 서버에 연결 요청 패킷을 보낸다. 이때 **SYN 플래그**를 세우고, 자신의 초기 순서 번호(sequence number, seq)를 함께 전송한다. seq는 임의로 정해진 숫자다.

### 2단계: SYN-ACK (서버 → 클라이언트)

서버가 요청을 받고 수락한다. **SYN 플래그**와 **ACK 플래그**를 둘 다 세워서 응답한다. ack 값은 클라이언트의 seq+1, 즉 "그다음 패킷을 기대한다"는 의미다. 서버도 자신의 seq를 포함해 전송한다.

### 3단계: ACK (클라이언트 → 서버)

클라이언트가 서버의 SYN-ACK를 받고 확인 응답을 보낸다. ack 값은 서버의 seq+1이다. 이 패킷이 도달하면 양쪽 모두 연결이 확립됐다는 상태가 된다.

### 왜 3번이어야 하나

2번(SYN + SYN-ACK)만으로는 클라이언트가 서버의 SYN-ACK를 잘 받았는지 서버가 확인할 수 없다. 3단계 ACK를 통해 비로소 양방향 통신이 가능하다는 것을 서버가 확신한다.

## 흔한 오해와 함정

- "handshake는 HTTPS에서만 일어난다"가 아니다. TCP 연결은 HTTP든 HTTPS든 항상 먼저 일어난다. HTTPS는 TCP handshake 이후 TLS handshake가 추가로 이어진다.
- SYN 패킷 하나로 연결이 맺어진다고 생각하는 경우가 있다. 실제로는 3번의 왕복이 모두 완료돼야 데이터를 보낼 수 있다.
- handshake는 네트워크 왕복 지연(RTT)을 최소 1번 소비한다. 서버가 같은 데이터센터라면 거의 무시되지만, 원거리 API 호출에서는 초기 연결 지연의 주요 원인이 된다.

## 실무에서 쓰는 모습

Spring Boot 애플리케이션이 외부 API를 호출할 때, 첫 번째 요청은 TCP handshake 시간이 포함돼 느리게 올 수 있다. 이후 같은 연결을 재사용하는 keep-alive 설정이 켜져 있으면, 두 번째 요청부터는 handshake 없이 바로 보낸다. 커넥션 풀을 쓰는 이유가 여기 있다.

## 더 깊이 가려면

- [TCP 혼잡 제어](./tcp-congestion-control.md) — 연결 이후 데이터 전송 속도를 TCP가 어떻게 조율하는지
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md) — TCP 연결 재사용이 어떻게 handshake 비용을 아끼는지

## 면접/시니어 질문 미리보기

**Q. TCP 3-way handshake를 설명해 주세요.**
클라이언트가 SYN을 보내고, 서버가 SYN-ACK로 응답하며, 클라이언트가 ACK로 확인한다. 3번 교환 후 양방향 연결이 확립된다.

**Q. 왜 2번이 아니라 3번을 교환하나요?**
2번이면 서버가 클라이언트에게 보낸 SYN-ACK가 실제로 도달했는지 서버가 확인하지 못한다. 3번째 ACK로 서버도 양방향 연결이 성립됐음을 확인한다.

**Q. SYN 없이 바로 데이터를 보내면 어떻게 되나요?**
TCP는 이를 거부한다. 연결 상태가 ESTABLISHED가 아닌 경우 RST(Reset) 패킷으로 응답하고 연결을 거부한다.

## 한 줄 정리

SYN → SYN-ACK → ACK 세 단계로 양쪽이 서로 준비됐음을 확인해야 TCP 데이터 전송이 시작된다.
