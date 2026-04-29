# HTTP keep-alive vs TCP keepalive vs idle timeout vs heartbeat

> 한 줄 요약: `keepalive`라는 단어는 보통 네 가지를 섞어 부르지만, 초급자는 먼저 "재사용", "생존 확인", "가만히 있으면 닫는 시간", "주기적 신호"를 분리해서 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
- [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
- [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [Spring WebClient Connection Pool / Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: http keep-alive vs tcp keepalive, keepalive 차이, keepalive 뭐예요, keepalive 큰 그림, keepalive 처음 배우는데, http keep-alive basics, tcp keepalive basics, idle timeout basics, heartbeat basics, connection reuse vs liveness, keep-alive timeout 헷갈림, keepalive랑 timeout 차이 뭐예요, 왜 keepalive인데 끊겨요, 언제 http keep-alive고 언제 tcp keepalive예요, 처음 네트워크 keepalive

## 핵심 개념

`keepalive`는 한 가지 기능 이름처럼 들리지만, 실제로는 서로 다른 층의 말이 섞여 있다. 초급자가 가장 먼저 고정해야 할 질문은 "지금 말하는 keepalive가 연결을 다시 쓰는 이야기인가, 죽었는지 확인하는 이야기인가?"다.

이 문서는 "`keepalive가 뭐예요?`", "`왜 keepalive인데 가끔 끊겨요?`", "`idle timeout이랑 heartbeat는 또 뭐가 달라요?`" 같은 첫 질문에서 먼저 잡아야 할 primer다. 운영 튜닝보다 먼저 용어를 네 칸으로 분리하는 데 집중한다.

아주 짧게 나누면 이렇다.

- HTTP keep-alive: 한 번 만든 HTTP 연결을 다음 요청에도 재사용
- TCP keepalive: 아주 조용한 TCP 연결이 아직 살아 있는지 OS가 확인
- idle timeout: 아무 데이터가 없으면 연결을 닫는 기준 시간
- heartbeat: 애플리케이션이 주기적으로 보내는 "나 아직 살아 있어" 신호

## 한눈에 보기

| 용어 | 가장 짧은 뜻 | 주로 보는 층 | 초급자용 기억법 |
|---|---|---|---|
| HTTP keep-alive | 요청마다 새 연결을 만들지 않고 재사용 | HTTP/브라우저/클라이언트 풀 | "같은 창구를 계속 쓴다" |
| TCP keepalive | idle TCP 연결의 생존 여부를 OS가 probe로 확인 | TCP/커널 | "창구가 아직 열려 있나 확인" |
| idle timeout | 너무 오래 조용하면 연결을 닫음 | LB, proxy, app, client pool | "몇 초 동안 조용하면 정리" |
| heartbeat | 앱이 일부러 주기적 신호를 보냄 | WebSocket, SSE, gRPC, 앱 프로토콜 | "조용하지 않게 만들어 끊기지 않게 함" |

헷갈릴 때는 먼저 이 한 줄로 자르면 된다.

- HTTP keep-alive는 "재사용"
- TCP keepalive는 "생존 확인"
- idle timeout은 "정리 기준"
- heartbeat는 "정리되지 않도록 보내는 신호"

## 상세 분해

### 1. HTTP keep-alive는 재사용 이야기다

브라우저나 HTTP 클라이언트는 요청 하나가 끝났다고 TCP 연결을 바로 버리지 않을 수 있다. 다음 요청을 같은 연결에 태우면 handshake 비용을 줄일 수 있다. 그래서 HTTP keep-alive를 보면 초점은 보통 "성능"과 "재사용"이다.

### 2. TCP keepalive는 죽었는지 확인하는 이야기다

TCP keepalive는 오랫동안 조용한 소켓에 작은 probe를 보내서 반대편이 이미 사라졌는지 확인한다. 이건 애플리케이션 메시지가 아니라 커널 수준 기능이다. 그래서 로그인 상태나 비즈니스 세션 상태를 직접 표현하지 못한다.

### 3. idle timeout은 누가 먼저 포기하느냐를 정한다

LB, reverse proxy, app server, client pool은 각자 "이 연결을 얼마나 조용히 둘까"를 따로 정한다. 이 값이 짧으면 연결이 더 빨리 닫힌다. 그래서 "keep-alive를 켰는데 왜 끊기지?"라는 질문은 종종 keepalive 문제가 아니라 idle timeout 문제다.

### 4. heartbeat는 앱이 일부러 silence를 깨는 장치다

WebSocket ping/pong, SSE comment, gRPC ping 같은 것은 연결이 완전히 idle 상태로 오래 머물지 않게 만든다. 즉 heartbeat는 "살아 있는 연결을 중간 장비가 idle로 착각하지 않게" 하려는 장치다.

## 흔한 오해와 함정

- "`keepalive`를 켰다"만으로는 의미가 부족하다. HTTP keep-alive인지 TCP keepalive인지 먼저 구분해야 한다.
- HTTP keep-alive는 로그인 유지가 아니다. 로그인 유지는 cookie/session 쪽 이야기다.
- TCP keepalive를 켰다고 idle timeout이 사라지지 않는다. LB나 proxy가 더 먼저 닫을 수 있다.
- heartbeat는 TCP keepalive의 동의어가 아니다. heartbeat는 앱이 보내는 신호고, TCP keepalive는 OS가 보내는 probe다.
- "아무 일도 없는데 첫 요청만 가끔 실패한다"면 HTTP keep-alive 자체보다 stale idle connection 재사용과 idle timeout mismatch를 먼저 의심하는 편이 맞다.

## 실무에서 쓰는 모습

가장 흔한 초급자 시나리오는 아래 셋이다.

| 상황 | 먼저 떠올릴 단어 | 이유 |
|---|---|---|
| 같은 서버 호출이 두 번째부터 더 빠르다 | HTTP keep-alive | 기존 연결 재사용으로 handshake 비용이 줄었을 수 있다 |
| 한참 쉬었다가 다시 보낸 첫 요청이 가끔 `connection reset`으로 실패한다 | idle timeout | 중간 어딘가가 먼저 연결을 닫았는데 클라이언트는 재사용하려 했을 수 있다 |
| WebSocket/SSE가 가만히 있으면 중간에 끊긴다 | heartbeat | 중간 장비가 idle로 판단하지 않게 주기적 신호가 필요할 수 있다 |

짧은 판별 순서도는 이렇게 잡으면 된다.

1. 질문이 "왜 매번 새 연결을 안 만드나?"면 HTTP keep-alive다.
2. 질문이 "상대가 죽었는지 어떻게 아나?"면 TCP keepalive 가능성이 크다.
3. 질문이 "몇 초 조용하면 왜 끊기나?"면 idle timeout이다.
4. 질문이 "안 끊기게 주기적으로 뭘 보내나?"면 heartbeat다.

## 더 깊이 가려면

- HTTP 연결 재사용부터 다시 잡으려면 [HTTP Keep-Alive와 커넥션 재사용 기초](./keepalive-connection-reuse-basics.md)
- TCP keepalive와 앱 heartbeat를 더 정확히 나누려면 [TCP Keepalive vs App Heartbeat](./tcp-keepalive-vs-app-heartbeat.md)
- stale idle socket과 간헐적 reset 패턴을 보려면 [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
- 브라우저 요청 전체 흐름에서 keep-alive가 어디쯤인지 보려면 [HTTP 요청-응답 기본 흐름: URL, DNS, TCP/TLS, 상태 코드, Keep-Alive](./http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- Spring 클라이언트 풀 설정으로 이어 보려면 [Spring WebClient Connection Pool / Timeout Tuning](../spring/spring-webclient-connection-pool-timeout-tuning.md)

## 면접/시니어 질문 미리보기

**Q. HTTP keep-alive와 TCP keepalive의 차이는 무엇인가요?**  
HTTP keep-alive는 연결 재사용이고, TCP keepalive는 idle한 TCP 연결의 생존 확인이다.

**Q. keepalive를 켰는데도 왜 idle timeout으로 끊길 수 있나요?**  
keepalive와 idle timeout은 같은 설정이 아니기 때문이다. 중간 LB나 proxy가 더 짧은 idle timeout을 가지면 먼저 연결을 닫을 수 있다.

**Q. heartbeat는 언제 필요한가요?**  
WebSocket, SSE, gRPC처럼 오래 열어 두는 연결에서 중간 장비가 idle close하지 않게 하거나, 앱 레벨에서 더 빠르게 끊김을 감지하고 싶을 때 필요하다.

## 한 줄 정리

`keepalive`가 나오면 먼저 "재사용인가, 생존 확인인가, idle 정리 시간인가, 앱 heartbeat인가"를 나눠서 읽어야 용어가 한 덩어리로 뭉개지지 않는다.
