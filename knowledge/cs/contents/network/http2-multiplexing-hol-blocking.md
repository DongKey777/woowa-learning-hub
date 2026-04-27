# HTTP/2 멀티플렉싱과 HOL blocking

> 한 줄 요약: HTTP/2는 애플리케이션 레벨의 순차 병목을 줄이지만, 같은 TCP 연결 위에 올라가는 이상 전송 계층의 HOL blocking은 그대로 남는다.

**난이도: 🔴 Advanced**

관련 문서:
- [HTTP 버전 비교 시작 가이드 (3분 브리지)](./http-versions-beginner-overview.md) (overview bridge)
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md) (main comparison primer)
- [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md) (beginner first-check)
- [gRPC vs REST](./grpc-vs-rest.md)
- [TCP 혼잡 제어](./tcp-congestion-control.md)
- [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
- [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
- [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
- [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
- [System Design](../system-design/README.md)

retrieval-anchor-keywords: http/2 multiplexing, hol blocking, stream multiplexing, tcp hol, shared connection, packet loss, grpc transport, connection reuse, http/2 hol beginner bridge, http/2가 뭐예요, 처음 배우는데 h2 hol, http-level hol vs tcp-level hol

## 먼저 읽는 브리지 (입문 -> 이 문서)

### 30초 멘탈 모델

- `HTTP/2 multiplexing`: 한 차선(TCP 연결) 위에 여러 차량(stream)을 번갈아 태우는 방식
- 좋아지는 점: HTTP/1.1 때처럼 "앞 응답이 끝나야 뒤 응답이 가는" 앱 레벨 대기는 줄어든다
- 남는 점: 차선 자체(TCP)에서 사고(패킷 손실)가 나면 그 차선 위 차량들이 같이 늦어진다

즉, 이 문서는 **"HTTP/2가 무엇을 고쳤고(HTTP 레벨), 무엇은 못 고쳤는지(TCP 레벨)"**를 구분하는 브리지다.

### 입문 문서와 이 문서의 역할 차이

| 질문 | 입문 비교 문서에서 얻는 답 | 이 문서에서 추가로 보는 답 |
|---|---|---|
| HTTP/2는 왜 빠르다고 하나요? | 요청을 stream으로 섞어 보내기 때문 | 손실 구간에서는 stream들이 함께 느려질 수 있음 |
| HTTP/2면 HOL이 사라졌나요? | HTTP/1.1 대비 크게 완화됨 | TCP HOL은 그대로 남음 |
| 언제 체감 이득이 큰가요? | 짧은 요청이 많을 때 | 대용량/손실 경로를 섞으면 tail latency가 다시 커질 수 있음 |

### 흔한 혼동 3가지

- "stream 독립" = "네트워크도 독립"이 아니다
- p99 급등이 애플리케이션 코드 문제만은 아니다(TCP 손실/재전송도 후보)
- "H2 연결 하나로 통일"이 항상 최적은 아니다(큰 업로드와 짧은 RPC 분리 검토 필요)

## 작은 손실 미니 비교 상자

> 상황: 같은 화면에서 아주 작은 요청 3개를 거의 동시에 보낸다.
> `A=/feed`, `B=/badge`, `C=/profile` 이고, `B` 응답 조각 하나가 중간에 손실됐다.

| 버전 | 브라우저/클라이언트 입장에서 보이는 모습 | 초급자용 해석 |
|---|---|---|
| HTTP/2 over TCP | `B`의 빠진 TCP 조각이 다시 와야 연결 위의 뒤 데이터도 정렬된다. `A`, `C`가 이미 일부 도착했어도 함께 늦어질 수 있다. | 차선은 여러 줄(stream)처럼 보여도 바닥 도로는 한 줄(TCP)이라, 도로에서 멈추면 뒤 차들도 같이 기다린다. |
| HTTP/3 over QUIC | `B`가 속한 stream 조각만 다시 받으면 된다. `A`, `C` stream은 이미 받은 데이터 기준으로 계속 진행될 수 있다. | 차선별로 따로 움직여서, `B` 차선 사고가 `A`, `C` 차선까지 같은 방식으로 막지는 않는다. |

작은 요청 1개 손실인데도 HTTP/2에서 여러 요청이 같이 버벅여 보일 수 있는 이유가 여기 있다.
HTTP/3가 말하는 "stream 분리"는 바로 이 **손실 전파 범위를 stream 단위로 더 잘 가른다**는 뜻에 가깝다.

### 안전한 다음 한 걸음

- 버전 비교를 먼저 복습해야 하면: [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
- 아직 `HOL blocking`과 `flow-control stall`을 헷갈리면: [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md)
- 이 문서 뒤 QUIC 관점까지 이어 보려면: [HTTP/3와 QUIC 실전 트레이드오프](./http3-quic-practical-tradeoffs.md)

---

## 핵심 개념

HTTP/1.1에서는 하나의 연결에서 응답 순서가 꼬이기 쉬웠다. `pipelining`을 써도 응답 순서를 맞추는 과정에서 HOL blocking이 생기기 쉬웠다.

HTTP/2는 이 문제를 **stream multiplexing**으로 줄인다.

- 하나의 TCP 연결 위에 여러 stream을 올린다
- 각 stream은 독립적인 프레임으로 쪼개진다
- 응답이 큰 요청 하나가 다른 요청을 애플리케이션 레벨에서 막지 않는다

하지만 중요한 함정이 있다.

**HTTP/2가 없앤 건 HTTP 레벨의 HOL blocking이고, TCP 레벨의 HOL blocking은 아직 남아 있다.**

즉, 같은 TCP 연결에서 패킷 손실이 나면 그 연결 위의 모든 stream이 영향을 받는다.

---

## 깊이 들어가기

### 1. HTTP/1.1과 HTTP/2의 차이

HTTP/1.1:

- 요청-응답이 상대적으로 순차적이다
- 큰 응답이 앞에 오면 뒤 요청도 늦어진다
- 연결 수를 늘려 우회하곤 했다

HTTP/2:

- 하나의 연결에 여러 stream을 넣는다
- 프레임 단위로 interleave 된다
- 헤더를 압축하고 연결을 재사용한다

HTTP/2의 핵심은 "더 빠른 HTTP"라기보다 **동시에 여러 요청을 더 잘 섞는 것**이다.

### 2. 남아 있는 TCP HOL blocking

같은 TCP 연결 위에서 하나의 패킷이 유실되면, 이후 패킷이 도착해도 재정렬이 끝날 때까지 사용자에게 전달되지 않는다.

이게 의미하는 바:

- 작은 RPC 여러 개를 하나의 H2 연결로 몰아도
- 네트워크 손실이 발생하면
- 연결 위의 모든 stream이 같이 지연될 수 있다

짧게 말해 HTTP/2의 stream은 **프레임을 섞어 보내는 단위**이고, HTTP/3의 stream은 **손실 영향도 더 잘 분리하려는 전송 단위**까지 포함한다고 보면 초반 이해가 쉽다.

### Retrieval Anchors

- `HTTP/2 multiplexing`
- `HOL blocking`
- `stream multiplexing`
- `TCP HOL`
- `shared connection`
- `packet loss`
- `gRPC transport`
- `connection reuse`

그래서 HTTP/2는 "stream이 독립"이라는 말만 믿으면 안 된다.
독립성은 **애플리케이션 프레이밍 수준**이고, 실제 전송은 여전히 TCP다.

### 3. multiplexing이 좋은 상황

- 짧은 요청이 많을 때
- 연결 수를 줄이고 싶을 때
- gRPC처럼 스트리밍이 필요할 때
- 프록시와 keep-alive 비용을 줄이고 싶을 때

### 4. multiplexing이 생각보다 안 좋을 수 있는 상황

- 패킷 손실이 잦은 네트워크 경로
- 대용량 업로드와 짧은 API 요청이 같은 연결을 공유할 때
- 프록시나 LB가 H2를 완전히 잘 이해하지 못할 때
- 하나의 연결에 너무 많은 중요한 요청을 몰아넣을 때

---

## 실전 시나리오

### 시나리오 1: 작은 RPC가 많다

서비스 A가 서비스 B를 초당 수십 번 호출한다.

이때 HTTP/1.1은 커넥션 수를 늘려야 하고, HTTP/2는 하나의 연결로 많은 요청을 섞어 보낼 수 있다.

효과:

- handshake 감소
- 소켓 수 감소
- 헤더 중복 감소

### 시나리오 2: 네트워크 손실이 갑자기 늘었다

대역폭은 충분해 보이는데 p99가 튄다.

원인은 서버 애플리케이션이 아니라, 같은 TCP 연결에서 손실이 발생해 여러 stream이 함께 대기하는 것일 수 있다.

이때는:

1. `ss -ti`로 재전송과 RTT를 확인한다
2. 패킷 손실률을 본다
3. H2 연결 재사용 정책을 검토한다
4. 필요하면 큰 업로드와 작은 API를 분리한다

### 시나리오 3: gRPC 호출이 갑자기 느려졌다

gRPC는 H2를 기반으로 하므로, 네트워크 혼잡이나 손실이 생기면 stream 전체가 영향을 받는다.

이 문제는 [TCP 혼잡 제어](./tcp-congestion-control.md)와 함께 봐야 한다.

---

## 코드로 보기

### curl로 HTTP/2 확인

```bash
curl --http2 -I https://example.com
```

### HTTP/2 연결 특성 확인

```bash
nghttp -nv https://example.com
```

### 감각을 잡는 비교

```text
HTTP/1.1:
  연결 수 증가 -> 병렬성 확보

HTTP/2:
  연결 수는 적게, stream은 많이
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| HTTP/1.1 다중 연결 | 구현 단순 | 연결 수와 handshake 비용 증가 | 호환성과 단순성이 중요할 때 |
| HTTP/2 multiplexing | 연결 효율 높음 | TCP HOL blocking은 남음 | 작은 요청이 많을 때 |
| HTTP/2 + 프록시 최적화 | 운영 효율 좋음 | 프록시 설정 복잡도 증가 | 내부 서비스 호출 |
| 스트리밍 분리 | 큰 요청과 작은 요청 분리 가능 | 엔드포인트 설계가 복잡해짐 | 업로드/다운로드가 큰 서비스 |

핵심은 "H2가 항상 정답"이 아니라, **같은 연결에 무엇을 섞을지**를 제어하는 것이다.

---

## 꼬리질문

> Q: HTTP/2가 있는데 왜 TCP HOL blocking이 여전히 문제인가?
> 의도: 전송 계층과 애플리케이션 계층의 HOL blocking 차이를 아는지 확인
> 핵심: stream은 독립이지만 전송은 TCP 위에서 일어난다

> Q: 큰 업로드와 작은 API를 같은 H2 연결에 넣으면 왜 문제가 될 수 있나?
> 의도: 실제 서비스에서 multiplexing의 부작용을 이해하는지 확인
> 핵심: 손실, 버퍼, 혼잡 제어가 함께 작은 요청 지연을 키울 수 있다

## 한 줄 정리

HTTP/2는 요청들을 더 잘 섞어 보내는 기술이지, TCP 위에 올라가는 한 모든 HOL blocking을 없애는 기술은 아니다.
