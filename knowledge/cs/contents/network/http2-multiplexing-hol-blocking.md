# HTTP/2 멀티플렉싱과 HOL blocking

> 한 줄 요약: HTTP/2는 애플리케이션 레벨의 순차 병목을 줄이지만, 같은 TCP 연결 위에 올라가는 이상 전송 계층의 HOL blocking은 그대로 남는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [TCP 혼잡 제어](./tcp-congestion-control.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [System Design](../system-design/README.md)

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
