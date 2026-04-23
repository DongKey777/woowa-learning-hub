# SYN Retransmission, Handshake Timeout Behavior

> 한 줄 요약: SYN 재전송은 네트워크가 연결 수립에 실패했다는 신호이고, handshake timeout은 그 실패를 앱이 언제 포기할지 정하는 운영 경계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Accept Queue, SYN Backlog, Listen Overflow](./accept-queue-syn-backlog-listen-overflow.md)

retrieval-anchor-keywords: SYN retransmission, handshake timeout, SYN-SENT, SYN-ACK, connect timeout, tcp_syn_retries, retransmission timeout, SYN cookie, three-way handshake

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

TCP 연결은 3-way handshake로 시작한다.

- SYN: 연결을 시작하고 싶다
- SYN-ACK: 알겠다, 나도 준비됐다
- ACK: 좋다, 연결을 확정하자

이 과정에서 SYN이 되돌아오지 않으면 커널은 재전송을 시도한다.  
애플리케이션은 이를 보통 `connect timeout`이나 handshake timeout으로 본다.

### Retrieval Anchors

- `SYN retransmission`
- `handshake timeout`
- `SYN-SENT`
- `SYN-ACK`
- `connect timeout`
- `tcp_syn_retries`
- `retransmission timeout`
- `SYN cookie`

## 깊이 들어가기

### 1. SYN retransmission이 의미하는 것

SYN을 보냈는데 응답이 없으면 보통 아래 중 하나다.

- 대상 호스트가 죽었다
- 경로 중간에 차단이 있다
- 방화벽이 SYN을 드롭한다
- LB가 과부하라서 연결을 받지 못한다

이때 커널은 바로 포기하지 않고 몇 번 더 시도한다.

- 일시적 패킷 손실일 수도 있기 때문이다
- 첫 패킷만 사라졌을 수도 있기 때문이다

### 2. handshake timeout은 왜 따로 봐야 하나

connect timeout을 너무 길게 잡으면:

- 사용자가 오래 기다린다
- worker thread가 묶인다
- retry가 늦게 시작된다

너무 짧게 잡으면:

- 잠깐의 혼잡도 실패로 보인다
- 불필요한 retry가 늘 수 있다

즉 handshake timeout은 네트워크 불안정과 사용자 체감 사이의 균형점이다.

### 3. SYN-SENT 상태는 무엇을 말하나

클라이언트가 SYN을 보냈고 아직 연결이 성사되지 않은 상태다.

- `ss -tan state syn-sent`로 볼 수 있다
- 이 상태가 많으면 connect path가 막혔을 수 있다
- NAT, firewall, LB, backend 과부하를 의심한다

### 4. 왜 LB나 프록시 문제처럼 보이나

SYN 단계에서 막히면 앱은 응답을 받지 못한다.

- 서버 코드가 아니라 네트워크 앞단일 수 있다
- health check는 멀쩡한데 실제 connect만 실패할 수 있다
- 특정 포트만 막힐 수도 있다

### 5. 재전송이 늘면 무엇을 의심하나

SYN 재전송은 손실, drop, overload의 합성 결과일 수 있다.

- 방화벽 정책
- conntrack 포화
- backend accept backlog 부족
- SYN cookie 사용 여부

이 문서는 [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)와 함께 보면 좋다.

## 실전 시나리오

### 시나리오 1: connect timeout만 간헐적으로 난다

원인 후보:

- LB 건강 상태가 불안정하다
- 경로 일부에서 SYN이 드롭된다
- NAT 포트가 부족하다

### 시나리오 2: 배포 직후 connection storm이 생긴다

대량의 새 연결이 동시에 붙으면 SYN backlog가 밀릴 수 있다.

- 신규 인스턴스가 아직 warm하지 않다
- health check는 통과하지만 실제 accept는 늦다
- retry가 더 많은 SYN을 만든다

### 시나리오 3: 특정 환경에서만 접속이 아예 안 된다

기업망, VPN, 클라우드 경로에서 SYN 차단이 흔하다.

- DNS는 되는데 connect가 안 된다
- ping은 되는데 TCP만 안 된다
- 방화벽이 첫 패킷을 드롭한다

### 시나리오 4: timeout을 늘렸는데 해결이 안 된다

문제는 단순한 대기 시간이 아니라, handshake가 끝나지 않는 경로일 수 있다.

- 잘못된 목적지
- blackhole
- NAT exhaustion
- middlebox 정책

## 코드로 보기

### 커널 상태 확인

```bash
ss -tan state syn-sent
ss -tan state syn-recv
sysctl net.ipv4.tcp_syn_retries
```

### connect timeout 감각

```java
HttpClient client = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(1))
    .build();
```

### SYN 재전송 관찰

```bash
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'
```

### 현장 체크 포인트

```text
- SYN-SENT 수가 급증하는가
- connect timeout이 특정 대역에서만 나는가
- LB health check와 실제 connect 경로가 같은가
- NAT / conntrack limit이 찼는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 짧은 connect timeout | 빨리 실패한다 | 일시적 흔들림에도 민감하다 | 외부 의존성이 많을 때 |
| 긴 connect timeout | 순간 장애를 흡수한다 | thread와 retry가 묶인다 | 내부 안정망이 있을 때 |
| SYN 재전송 허용 | 일시적 손실을 견딘다 | 연결 성립이 늦어진다 | 기본 TCP 동작 |

핵심은 connect timeout을 "충분히 길게"가 아니라 **실패 경로를 드러낼 만큼만** 두는 것이다.

## 꼬리질문

> Q: SYN 재전송이 보이면 무엇을 의심하나요?
> 핵심: 네트워크 드롭, 방화벽, LB 과부하, NAT 포트 고갈을 먼저 본다.

> Q: handshake timeout과 read timeout의 차이는 무엇인가요?
> 핵심: handshake timeout은 연결 수립 전, read timeout은 연결 이후 응답 대기다.

> Q: SYN-SENT가 많으면 항상 서버 문제인가요?
> 핵심: 아니다. 경로 중간 장비, NAT, 방화벽 문제일 수 있다.

## 한 줄 정리

SYN 재전송은 연결 수립 실패의 신호이고, handshake timeout은 그 실패를 앱이 언제 포기할지 정하는 경계라서 connect 경로를 따로 봐야 한다.
