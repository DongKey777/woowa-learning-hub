# FIN, RST, Half-Close, EOF

> 한 줄 요약: FIN은 "이제 더 안 보낸다"이고, RST는 "이 연결을 바로 버린다"에 가깝다. 둘을 구분해야 EOF와 에러를 정확히 해석할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)

retrieval-anchor-keywords: FIN, RST, half-close, EOF, shutdown(SHUT_WR), CLOSE_WAIT, TIME_WAIT, ECONNRESET, EPIPE, SO_LINGER

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

TCP 연결 종료는 단순히 "닫는다"가 아니다.

- `FIN`: 내가 더 보낼 데이터가 없다는 뜻이다
- `RST`: 이 연결 상태를 더 이상 믿지 말고 즉시 끊으라는 뜻에 가깝다
- `half-close`: 한 방향만 닫고 반대 방향은 계속 쓸 수 있는 상태다
- `EOF`: 상대가 FIN을 보내서 읽을 데이터가 끝났다는 의미다

이 차이를 모르면 로그에서 `EOF`, `connection reset by peer`, `broken pipe`가 각각 무슨 뜻인지 헷갈리기 쉽다.

### Retrieval Anchors

- `FIN`
- `RST`
- `half-close`
- `EOF`
- `CLOSE_WAIT`
- `TIME_WAIT`
- `ECONNRESET`
- `EPIPE`
- `SO_LINGER`

## 깊이 들어가기

### 1. FIN은 왜 4-way close로 보이나

TCP는 양방향 스트림이기 때문에, 각 방향이 독립적으로 닫힌다.

보통 연결 종료는 다음처럼 흐른다.

1. A가 FIN을 보낸다
2. B는 ACK로 확인한다
3. B도 자기 전송이 끝나면 FIN을 보낸다
4. A가 ACK로 마무리한다

즉, 한쪽이 닫았다고 해서 반대쪽 송수신이 즉시 사라지는 것은 아니다.

### 2. half-close는 언제 유용한가

half-close는 한쪽 방향의 전송이 끝났음을 먼저 알릴 때 유용하다.

- 업로드를 끝낸 뒤 서버 응답을 기다릴 때
- 스트리밍 요청에서 request body를 먼저 닫고 response를 계속 읽을 때
- 프로토콜이 "보내는 쪽"과 "받는 쪽"을 분리할 때

`shutdown(SHUT_WR)`가 대표적인 예다.  
이렇게 하면 상대는 "입력은 끝났구나"를 알 수 있지만, 아직 응답을 보낼 수 있다.

### 3. EOF와 에러는 같은 것이 아니다

애플리케이션이 read에서 0 바이트를 받으면 보통 EOF로 해석한다.

- 상대가 FIN을 보냈다
- 더 읽을 데이터가 없다
- 정상 종료 경로일 수 있다

반대로 에러는 보통 다른 의미다.

- `ECONNRESET`: 상대가 RST로 연결을 날렸다
- `EPIPE`: 닫힌 소켓에 write하려 했다

이 둘을 구분해야 "정상 종료"와 "비정상 종료"를 분리할 수 있다.

### 4. RST는 왜 위험한가

RST는 보통 다음 상황에서 나타난다.

- 프로토콜 위반이 발생했다
- peer가 더 이상 소켓 상태를 유지하지 않는다
- `SO_LINGER` 설정 때문에 닫는 즉시 강제 종료한다
- 중간 장비가 세션을 끊으며 기존 상태를 잃는다

문제는 RST가 오면 버퍼에 있던 데이터가 드러나지 않거나, 전송 중이던 작업이 갑자기 실패할 수 있다는 점이다.

### 5. CLOSE_WAIT가 길어지면 왜 문제인가

`CLOSE_WAIT`는 상대가 FIN을 보냈는데, 로컬 프로세스가 아직 자기 쪽 종료를 못 한 상태다.

- 애플리케이션이 socket close를 안 했다
- 리소스를 회수하지 못하고 있다
- 연결이 누적되면 fd가 새는 것처럼 보인다

운영에서 CLOSE_WAIT가 늘어나면 코드를 먼저 의심해야 한다.

### 6. TIME_WAIT은 왜 active closer에 남나

TCP는 늦게 도착한 패킷이 새 연결로 섞이지 않도록 잠깐 상태를 남긴다.

- active closer가 TIME_WAIT을 진다
- 짧은 연결이 많으면 TIME_WAIT이 쌓인다
- 재사용이 조급해지면 이상한 현상이 생긴다

이 부분은 [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)와 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 서버는 정상 종료했는데 클라이언트는 에러로 본다

서버가 요청을 다 받자마자 RST를 보내면, 클라이언트는 응답을 읽기 전에 연결이 깨졌다고 본다.

이때 원인은 보통:

- 응답을 다 쓰기 전에 프로세스가 종료됐다
- 프록시가 upstream 연결을 강제로 끊었다
- 잘못된 close 정책이 있다

### 시나리오 2: 업로드는 성공한 것처럼 보이는데 응답이 없다

클라이언트가 request body를 다 보낸 뒤 서버의 response를 기다리는데, 서버가 half-close를 기대하지 않고 먼저 연결을 닫아버리면 `EOF`와 `reset`이 섞여 보일 수 있다.

### 시나리오 3: `broken pipe`가 간헐적으로 난다

서버가 이미 FIN/RST를 받은 뒤에도 write를 계속 시도할 때 흔히 보인다.

- keep-alive가 끊겼다
- idle timeout이 먼저 닫았다
- client disconnect를 늦게 감지했다

### 시나리오 4: 프록시 뒤에서만 reset이 늘어난다

프록시나 LB가 upstream과 downstream의 종료 타이밍을 다르게 다루면, 앱은 직접 닫지 않았는데도 RST를 보는 경우가 있다.

이럴 때는 app 로그만 보지 말고 proxy access log와 tcpdump를 같이 봐야 한다.

## 코드로 보기

### 종료 상태를 보는 명령

```bash
ss -tan state close-wait
ss -tan state time-wait
tcpdump -i eth0 'tcp[tcpflags] & (tcp-fin|tcp-rst) != 0'
```

### half-close 예시

```python
import socket

s = socket.create_connection(("api.example.com", 443))
s.sendall(b"hello")
s.shutdown(socket.SHUT_WR)  # 더 이상 보내지 않음

while True:
    data = s.recv(4096)
    if not data:
        print("EOF")
        break
    print(data)
```

### 강제 종료를 유발할 수 있는 예시

```python
import socket
import struct

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
```

실무에서는 이런 옵션을 함부로 쓰지 않는다.  
연결을 "바로 끝내고 싶다"는 욕구가 오히려 데이터 유실을 만든다.

### Java에서 EOF와 예외를 나누어 보는 감각

```java
int read = inputStream.read(buf);
if (read == -1) {
    // peer FIN -> EOF
}
```

```text
read == -1: 정상적인 종료 신호일 수 있다
IOException: 연결 강제 종료나 네트워크 실패일 수 있다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| graceful close | 데이터 유실이 적다 | 종료가 느릴 수 있다 | 대부분의 정상 종료 |
| half-close | 송수신을 분리할 수 있다 | 구현이 복잡하다 | request/response 분리 프로토콜 |
| RST close | 빨리 끝난다 | 데이터 유실 위험이 크다 | 비정상 상황, 프로토콜 위반 |

핵심은 "빨리 닫기"보다 **무엇을 버리고 무엇을 지킬지**다.

## 꼬리질문

> Q: FIN과 RST의 차이는 무엇인가요?
> 핵심: FIN은 정상 종료 절차의 일부이고, RST는 연결 상태를 즉시 폐기하는 성격이 강하다.

> Q: EOF와 `connection reset by peer`는 왜 다르게 보이나요?
> 핵심: EOF는 peer FIN의 결과고, reset은 peer나 중간 장비가 RST로 세션을 끊은 결과다.

> Q: CLOSE_WAIT가 많으면 무엇을 의심해야 하나요?
> 핵심: 애플리케이션이 소켓을 닫지 않고 있는지, 종료 경로가 누락됐는지를 먼저 본다.

## 한 줄 정리

FIN은 데이터를 더 안 보내겠다는 정상 종료 신호이고, RST는 상태를 버리는 강제 종료라서 EOF와 reset을 구분해야 장애를 정확히 읽을 수 있다.
