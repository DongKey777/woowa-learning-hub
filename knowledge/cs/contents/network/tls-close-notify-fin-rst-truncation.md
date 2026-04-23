# TLS close_notify, FIN/RST, Truncation

> 한 줄 요약: TCP의 `FIN`과 `RST`는 연결 종료를 말할 뿐이고, TLS의 `close_notify`는 암호화된 바이트 스트림이 정상적으로 끝났다는 신호라서 둘을 혼동하면 truncation과 EOF 해석이 흔들린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [mTLS Handshake Failure Diagnosis](./mtls-handshake-failure-diagnosis.md)
> - [TLS Certificate Chain, OCSP Stapling Failure Modes](./tls-certificate-chain-ocsp-stapling-failure-modes.md)
> - [Connection Draining vs FIN/RST Graceful Close](./connection-draining-vs-fin-rst-graceful-close.md)

retrieval-anchor-keywords: TLS close_notify, truncation, FIN, RST, EOF, TLS shutdown, SSL_ERROR_ZERO_RETURN, SSL_ERROR_SYSCALL, graceful close, encrypted stream end, truncation attack

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

TLS는 TCP 위에 올라가지만, 종료 의미는 TCP와 완전히 같지 않다.

- TCP `FIN`: 더 이상 보낼 바이트가 없다는 뜻
- TCP `RST`: 연결 상태를 즉시 버리라는 뜻
- TLS `close_notify`: 암호화된 레코드 스트림이 정상적으로 끝났다는 뜻

따라서 애플리케이션은 "소켓이 닫혔다"만 보지 말고, **TLS 계층이 정상 종료를 확인했는지**도 같이 봐야 한다.

### Retrieval Anchors

- `TLS close_notify`
- `truncation`
- `FIN`
- `RST`
- `EOF`
- `TLS shutdown`
- `SSL_ERROR_ZERO_RETURN`
- `SSL_ERROR_SYSCALL`

## 깊이 들어가기

### 1. 왜 TLS는 별도 종료 신호가 필요한가

TLS는 평문 바이트가 아니라 암호화된 record를 주고받는다.

- 마지막 record가 정상적으로 끝났는지
- 중간에서 잘려 나간 것은 아닌지
- peer가 의도적으로 종료했는지

를 알기 위해 `close_notify` alert를 쓴다.

즉 TCP FIN만으로는 "전송이 끝났다"를 말할 수 있어도, **TLS record가 온전하게 끝났다**를 충분히 말해 주지 못한다.

### 2. `close_notify` 없이 FIN만 오면 왜 애매한가

이 경우 라이브러리와 프로토콜에 따라 해석이 달라질 수 있다.

- 일부는 그냥 EOF처럼 본다
- 일부는 truncation 가능성이 있다고 경고한다
- HTTP처럼 Content-Length나 framing이 있는 상위 프로토콜은 덜 위험할 수 있다

하지만 framing이 약하거나 application-level integrity가 약하면 문제를 놓칠 수 있다.

### 3. proxy와 TLS termination 지점이 많을수록 더 헷갈린다

다음 경로를 생각해 보자.

- client <-> edge LB TLS
- edge LB <-> ingress TLS
- ingress <-> app plain TCP 또는 TLS

한 홉에서 `close_notify`가 잘 갔더라도 다른 홉에서는 그냥 FIN/RST로 끝날 수 있다.  
그래서 "TLS는 정상 종료"와 "소켓은 정상 종료"가 홉마다 다를 수 있다.

### 4. truncation은 "중간까지만 읽고 성공처럼 보이는" 상황이다

예를 들어:

- response body가 아직 남았는데 연결이 닫혔다
- app이 EOF를 성공으로 처리했다
- 상위 프로토콜 framing 검증이 약했다

그러면 부분 응답을 완전한 응답처럼 오해할 수 있다.

특히 프록시나 라이브러리가 EOF를 너무 관대하게 다루면, 실제 원인인 RST 또는 비정상 종료가 묻힐 수 있다.

### 5. graceful drain에서도 TLS shutdown 순서가 중요하다

배포나 drain 중에는 보통:

- 새 요청은 받지 않게 하고
- 진행 중 응답을 마무리하고
- 가능하면 TLS `close_notify` 후 TCP FIN으로 닫는 편이 안전하다

반대로 시간을 아끼려고 바로 RST를 보내면:

- client는 `connection reset`
- TLS 라이브러리는 비정상 종료
- 일부 응답은 truncation처럼 보일 수 있다

### 6. EOF와 TLS alert를 구분해서 관찰해야 한다

운영에서 다음 로그는 같은 말이 아니다.

- plain EOF
- `SSL_ERROR_ZERO_RETURN`
- `SSL_ERROR_SYSCALL`
- `connection reset by peer`

이 구분이 있어야 "정상 종료", "TCP 비정상 종료", "TLS 계층 비정상 종료"를 분리할 수 있다.

## 실전 시나리오

### 시나리오 1: 프록시 뒤에서만 응답 본문이 가끔 짧다

가능한 원인:

- drain 중 upstream이 `close_notify` 없이 FIN/RST를 보냈다
- proxy가 EOF를 성공처럼 전달했다
- 상위 응답 framing 검증이 약하다

### 시나리오 2: TLS handshake는 성공하는데 종료 단계에서만 에러가 난다

핸드셰이크가 아니라 shutdown 순서 문제일 수 있다.

- 응답 전송 후 즉시 프로세스 종료
- proxy가 linger 없이 소켓 정리
- LB drain timeout이 너무 짧다

### 시나리오 3: HTTP는 멀쩡한데 custom TLS 프로토콜에서 간헐적 데이터 누락이 보인다

상위 프로토콜 framing이 약하면 `close_notify` 부재의 위험이 더 직접적으로 드러난다.

### 시나리오 4: 앱 로그에는 EOF뿐인데 네트워크 팀은 reset을 본다

앱은 TLS 라이브러리 추상화만 보고, 네트워크는 TCP 레벨만 보고 있을 수 있다.  
두 관점을 합쳐야 shutdown 원인을 정확히 본다.

## 코드로 보기

### 종료 패킷 관찰 힌트

```bash
tcpdump -i eth0 'tcp[tcpflags] & (tcp-fin|tcp-rst) != 0'
```

### TLS 종료 동작 감각 보기

```bash
openssl s_client -connect api.example.com:443 -servername api.example.com
```

### 관찰 포인트

```text
- close_notify를 보낸 뒤 FIN으로 닫는가
- drain 중 RST가 늘어나는가
- EOF와 SSL shutdown error를 구분해 기록하는가
- partial body / content-length mismatch가 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| close_notify 후 graceful FIN | 종료 의미가 명확하다 | 종료 절차가 조금 더 길다 | 정상 drain, 민감한 프로토콜 |
| TCP FIN만 사용 | 단순하다 | TLS 계층 정상 종료 의미가 약하다 | 상위 framing이 강한 단순 경로 |
| 즉시 RST 종료 | 빨리 정리된다 | truncation과 reset 오류를 키운다 | 비정상 상황, 강제 종료 |
| strict shutdown 검증 | 이상 종료를 빨리 찾는다 | 일부 legacy peer와 호환성이 떨어질 수 있다 | 금융, 파일 전송, 엄격한 무결성 |

핵심은 TLS 종료를 단순 소켓 close로 다루지 않고 **암호화된 스트림의 완전성 문제**로 보는 것이다.

## 꼬리질문

> Q: TCP FIN과 TLS `close_notify`의 차이는 무엇인가요?
> 핵심: FIN은 바이트 스트림 종료, `close_notify`는 TLS record 스트림이 정상 종료됐다는 신호다.

> Q: `close_notify`가 없으면 항상 위험한가요?
> 핵심: 항상 즉시 취약한 것은 아니지만, EOF 해석과 truncation 검증이 약해질 수 있다.

> Q: 왜 프록시 체인에서 더 헷갈리나요?
> 핵심: 홉마다 TLS 종료 지점과 소켓 종료 방식이 달라서 한 곳의 정상 종료가 다른 홉에서는 비정상처럼 보일 수 있다.

## 한 줄 정리

TLS의 `close_notify`는 TCP FIN/RST와 다른 종료 의미를 가지므로, 배포 드레인이나 프록시 체인에서 이를 무시하면 truncation과 EOF 해석 오류가 숨어들 수 있다.
