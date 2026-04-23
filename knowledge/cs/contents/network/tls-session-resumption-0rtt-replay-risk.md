# TLS Session Resumption, 0-RTT, Replay Risk

> 한 줄 요약: TLS 세션 재개는 handshake 비용을 줄이고, 0-RTT는 한 번 더 RTT를 아끼지만, 그만큼 replay 위험과 운영 복잡도를 같이 가져온다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)

retrieval-anchor-keywords: TLS session resumption, session ticket, session cache, PSK, TLS 1.3, 0-RTT, early data, replay risk, handshake RTT

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

TLS의 비싼 부분은 암호화 자체보다도 **처음 연결을 맺는 절차**에 있다.

- 인증서를 검증해야 한다
- 키 교환을 해야 한다
- 서로 같은 세션 키를 만들어야 한다

`session resumption`은 이전에 성공했던 TLS 연결의 상태를 재활용해서 이 비용을 줄이는 방식이다.  
`0-RTT`는 TLS 1.3에서 가능한 더 공격적인 최적화로, 재개된 연결에서 클라이언트가 handshake 완료를 기다리지 않고 early data를 먼저 보낼 수 있다.

이 문서의 핵심은 단순하다.

- resumption은 **latency와 CPU를 줄이는 기술**이다
- 0-RTT는 **추가 RTT를 줄이는 기술**이다
- 하지만 0-RTT는 **재전송이 아니라 replay**라는 다른 문제를 만든다

### Retrieval Anchors

- `session resumption`
- `session ticket`
- `PSK`
- `0-RTT early data`
- `replay attack`
- `handshake RTT`
- `TLS 1.3`
- `resumed connection`

## 깊이 들어가기

### 1. resumption이 실제로 줄여 주는 것

full handshake에서는 매 연결마다 인증과 키 합의 비용이 들어간다.

- 서버 CPU 사용량이 늘어난다
- 모바일/무선 환경에서 연결 체감이 느려진다
- 짧은 연결이 많을수록 비효율이 커진다

resumption은 이전 handshake에서 얻은 상태를 바탕으로 다시 연결을 열기 때문에, 보통 다음 이득을 얻는다.

- round trip 수 감소
- 서버 공개키 연산 감소
- 연결 재개 속도 향상

여기서 중요한 건 **TLS가 덜 안전해지는 게 아니라, 이미 검증된 관계를 다시 쓰는 것**이라는 점이다.

### 2. session cache와 session ticket은 다르다

resumption을 구현하는 방식은 크게 두 가지 감각으로 이해하면 좋다.

- `session cache`: 서버가 재개에 필요한 상태를 기억한다
- `session ticket`: 서버가 상태 일부를 암호화해서 클라이언트에게 주고, 다음 연결에서 다시 읽는다

운영 관점에서는 session ticket이 더 확장성이 좋다.

- 여러 인스턴스가 같은 ticket key를 공유하면 load balancer 뒤에서도 재개가 잘 된다
- 반대로 인스턴스마다 키가 다르면 resumption hit rate가 떨어진다

즉, resumption이 안 되는 경우를 보더라도 "TLS가 느리다"라고만 보면 안 되고, **LB 뒤에서 재개 키를 어떻게 공유하는지**를 봐야 한다.

### 3. 0-RTT는 왜 위험한가

0-RTT의 핵심 문제는 **early data가 네트워크상에서 다시 보일 수 있다**는 점이다.

- 클라이언트가 같은 early data를 재전송할 수 있다
- 공격자가 관찰한 패킷을 다른 시점에 replay할 수 있다
- 서버는 handshake가 완전히 끝나기 전에 그 데이터를 받아 처리할 수 있다

그래서 0-RTT는 다음에만 쓰는 편이 안전하다.

- idempotent한 요청
- replay되어도 부작용이 없는 요청
- 캐시 히트 판정 같은 가벼운 작업

반대로 아래는 조심해야 한다.

- 결제 승인
- 재고 차감
- 비밀 토큰 교환
- 단발성 상태 변경

### 4. LB와 프록시가 resumption을 깨뜨리는 지점

resumption은 네트워크 경로가 예쁘게 유지될 때만 잘 보인다.

- TLS 종료 지점이 여러 개인데 ticket key를 공유하지 않는다
- 세션 캐시가 너무 작아서 자주 evict된다
- 스케일아웃 직후 hit rate가 떨어진다
- 워커가 재시작되면서 ticket key가 바뀐다

이때 사용자 체감은 "첫 요청만 느리고 다음 요청은 괜찮다"가 아니라, **가끔 갑자기 느린 연결이 섞이는 형태**로 나타난다.

### 5. 0-RTT는 성능 최적화이지 기본값이 아니다

0-RTT는 모든 API에 열어 두는 기능이 아니다.

- CDN edge
- 모바일 앱 재연결
- 읽기 전용 트래픽

같은 곳에서만 제한적으로 쓰는 편이 일반적이다.

결국 질문은 하나다.

> 이 요청이 replay되어도 시스템이 안전한가?

이 질문에 확답이 없으면 0-RTT는 성능 최적화가 아니라 장애 유발 옵션이 된다.

## 실전 시나리오

### 시나리오 1: 로그인 직후 첫 요청만 유독 느리다

가능한 원인:

- full handshake 비중이 높다
- ticket key가 인스턴스 간에 공유되지 않는다
- LB가 세션을 다른 백엔드로 보낸다

이 경우는 단순히 서버 CPU를 늘리기보다 resumption hit rate를 먼저 봐야 한다.

### 시나리오 2: 모바일 앱 재접속은 빠른데 가끔 중복 요청이 생긴다

0-RTT를 켠 뒤에 생길 수 있는 전형적인 문제다.

- 앱이 네트워크 복구 후 early data를 다시 보낸다
- 서버는 같은 요청을 두 번 본다
- 상태 변경 API가 idempotent하지 않으면 문제가 커진다

### 시나리오 3: edge는 빠른데 origin은 여전히 느리다

resumption은 handshake 비용만 줄여 준다.

- DB 쿼리가 느리면 전체 요청은 여전히 느리다
- 프록시 버퍼링이 길면 체감은 그대로다
- app timeout이 짧으면 재개해도 끊긴다

즉, TLS 최적화는 **전체 병목 중 한 조각**일 뿐이다.

## 코드로 보기

### resumption hit 여부를 보는 curl 감각

```bash
curl -w 'connect=%{time_connect} appconnect=%{time_appconnect} starttransfer=%{time_starttransfer}\n' \
  -o /dev/null -s https://api.example.com/health
```

`time_appconnect`가 줄면 TLS handshake 비용이 줄었다는 뜻으로 볼 수 있다.

### openssl로 재개 연결 확인

```bash
openssl s_client -connect api.example.com:443 -reconnect -tls1_3
```

출력에서 session reuse가 보이면 resumption이 동작하고 있다는 신호다.

### Nginx에서 session 재사용을 확인하는 감각

```nginx
log_format tls '$remote_addr $ssl_protocol $ssl_session_reused $request';
```

`$ssl_session_reused` 값으로 full handshake와 resumed handshake 비율을 관찰할 수 있다.

### early data는 정책과 같이 본다

```text
0-RTT 허용 조건:
- 읽기 전용
- replay되어도 안전
- 부작용 없는 요청

0-RTT 금지 조건:
- 상태 변경
- 결제
- 토큰 발급
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| full handshake | 가장 단순하고 안전하다 | RTT와 CPU 비용이 크다 | 기본값 |
| session resumption | 대부분의 비용을 줄인다 | ticket/key 관리가 필요하다 | 트래픽이 많고 재접속이 잦을 때 |
| 0-RTT | 첫 데이터까지 더 빨라진다 | replay 위험이 있다 | replay-tolerant한 읽기 트래픽 |

핵심은 "빠르게"가 아니라 **안전하게 빨라지는 경로인지**다.

## 꼬리질문

> Q: session resumption이 항상 full handshake보다 안전한가요?
> 핵심: 보안 수준이 낮아진다기보다, 재개용 상태와 키 관리가 추가된다.

> Q: 0-RTT를 왜 모든 API에 쓰지 않나요?
> 핵심: early data는 replay될 수 있어서 멱등하지 않은 요청에 위험하다.

> Q: LB 뒤에서 resumption hit rate가 떨어지는 이유는?
> 핵심: ticket key나 session cache가 인스턴스 간에 공유되지 않으면 재개를 못 한다.

## 한 줄 정리

TLS resumption은 handshake 비용을 줄이는 운영 최적화이고, 0-RTT는 그 위에 replay 위험을 얹는 선택지라서 요청 성격을 먼저 봐야 한다.
