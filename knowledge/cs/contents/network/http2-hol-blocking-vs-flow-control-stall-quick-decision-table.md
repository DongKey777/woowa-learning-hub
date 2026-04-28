# HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table

> 한 줄 요약: `HOL blocking`은 보통 "같은 전송 경로에서 손실 때문에 모두 같이 기다리는 문제"이고, `flow-control stall`은 "상대가 더 읽었다는 credit를 안 돌려줘서 조용히 멈추는 문제"다.

**난이도: 🟢 Beginner**

관련 문서:
- [HTTP/1.1 vs HTTP/2 vs HTTP/3 입문 비교](./http1-http2-http3-beginner-comparison.md)
- [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
- [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
- [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md)
- [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
- [Request Deadline / Timeout Budget Primer](../system-design/request-deadline-timeout-budget-primer.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: http/2 hol vs flow-control stall, http/2 quick decision table, hol blocking vs window_update, packet loss vs credit starvation, tcp hol vs h2 flow control, h2 stall routing beginner, stream stalled but connection alive, max_concurrent_streams vs window_update, stream slot vs window credit, http/2가 느려져요, 처음 배우는데 h2 stall, http2 hol blocking vs flow control stall quick decision table beginner, http2 hol blocking vs flow control stall quick decision table intro, network basics, beginner network

## 먼저 잡는 그림

초급자는 이렇게 나누면 된다.

- `HOL blocking`: 길 하나(TCP 연결)에서 앞쪽 손실 복구가 끝날 때까지 뒤쪽도 같이 기다린다
- `flow-control stall`: 길은 열려 있지만 "더 보내도 된다"는 예산(`WINDOW_UPDATE`)이 안 돌아와서 멈춘다

즉 둘 다 "응답이 멈춘 것처럼" 보이지만, 멈춘 이유가 다르다.

## 30초 Quick Decision Table

| 먼저 보이는 신호 | HOL blocking 쪽에 더 가깝다 | flow-control stall 쪽에 더 가깝다 |
|---|---|---|
| 핵심 질문 | "패킷 손실이나 재전송 때문에 같은 TCP 연결 전체가 같이 기다리나?" | "연결은 살아 있는데 credit가 안 돌아와 DATA가 못 가나?" |
| 어디서 막히나 | 전송 경로(TCP) | HTTP/2 계층의 stream/connection window |
| 흔한 단서 | 재전송, RTT 상승, 손실 이후 여러 stream이 같이 흔들림 | `WINDOW_UPDATE` 지연, window 고갈, stream은 열려 있는데 DATA 정체 |
| 작은 요청도 같이 느려지나 | 자주 그렇다. 같은 TCP 연결이면 같이 영향 받기 쉽다 | connection window가 막히면 그렇고, stream window만 막히면 아닐 수 있다 |
| 손실이 꼭 있어야 하나 | 대체로 손실/재정렬/전송 지연 후보를 먼저 본다 | 아니다. 손실이 없어도 receiver가 천천히 읽으면 생긴다 |
| 첫 다음 문서 | [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md) | [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md) |

## 먼저 자르는 오해: stream slot 부족 vs window credit 부족

여기서 초급자가 한 번 더 헷갈린다. 둘 다 "HTTP/2에서 뭔가 막혔다"로 보이지만 질문 자체가 다르다.

| 구분 | stream slot 부족 | window credit 부족 |
|---|---|---|
| 먼저 떠올릴 말 | `MAX_CONCURRENT_STREAMS` | `WINDOW_UPDATE`, `stream window`, `connection window` |
| 막히는 순간 | 새 stream을 더 열려고 할 때 | stream은 이미 열렸는데 DATA를 더 보내려 할 때 |
| 눈에 보이는 증상 | 요청 시작 자체가 늦다, pending queue가 생긴다 | 시작은 했는데 중간에 조용히 멈춘다 |
| 비유 | 계산대 자리가 다 차서 새 손님이 줄을 선다 | 계산대 자리는 있는데 결제 한도가 0원이라 더 못 산다 |
| 먼저 볼 문서 | [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md) | [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md) |

짧게 기억하면 된다.

- `slot 문제`는 "새 요청이 아직 출발도 못 함"
- `credit 문제`는 "출발은 했는데 중간에 더 못 감"

둘을 섞으면 "stream이 안 열렸다"와 "stream은 열렸는데 DATA가 안 간다"를 같은 장애처럼 읽게 된다.

## 헷갈릴 때 바로 쓰는 4문장 판별

1. `재전송/손실` 이야기가 먼저 나오면 HOL blocking 쪽이다.
2. `WINDOW_UPDATE`, `window=0 근처`, `credit 반환 지연`이 보이면 flow-control stall 쪽이다.
3. "연결은 멀쩡히 살아 있고 stream도 열렸는데 DATA만 안 온다"면 flow-control stall 후보가 더 크다.
4. "손실 한 번 이후 같은 TCP 연결의 여러 stream p99가 같이 튄다"면 HOL blocking 후보가 더 크다.

## 프레임 로그 없이 보는 짧은 타임라인

둘 다 "중간에 멈춘다"로 보이지만, 시간 순서로 읽으면 차이가 더 잘 보인다.

| 상황 | 짧은 타임라인 | 초보자용 해석 |
|---|---|---|
| 손실 기반 지연 | `t1` 작은 RPC 3개 시작 -> `t2` 한 패킷 손실 -> `t3` 재전송이 올 때까지 3개가 같이 답답함 -> `t4` 재전송 뒤 다시 함께 진행 | 길 하나(TCP)에서 사고가 나서 뒤 차량도 같이 기다린 그림이다. |
| credit starvation | `t1` 큰 stream이 오래 내려옴 -> `t2` receiver가 천천히 읽어 credit 반환이 늦음 -> `t3` 작은 RPC는 연결은 살아 있지만 DATA를 못 받음 -> `t4` `WINDOW_UPDATE`가 오자 다시 진행 | 길은 열려 있는데 "더 보내도 됨" 표지가 늦게 돌아와 멈춘 그림이다. |

핵심은 `손실 기반 지연`은 "재전송이 끝나야 다시 움직임", `credit starvation`은 "`WINDOW_UPDATE`가 와야 다시 움직임"으로 기억하면 된다.

## 같은 증상을 다르게 읽는 예시

상황:

- 모바일 네트워크에서 gRPC 호출 5개가 같은 H2 연결을 쓴다
- 그중 하나는 큰 응답, 나머지는 작은 unary RPC다

두 갈래로 나눠 보자.

| 관찰 | 더 그럴듯한 해석 | 이유 |
|---|---|---|
| 손실 직후 5개가 거의 같이 느려진다 | HOL blocking | 같은 TCP 연결 위 stream들이 손실 복구를 함께 기다릴 수 있다 |
| 손실은 안 보이는데 큰 stream 뒤로 작은 RPC가 조용히 멈춘다 | flow-control stall | 큰 stream이 connection window를 오래 점유하거나 receiver consume이 늦을 수 있다 |
| 작은 RPC만 느리고 큰 stream은 계속 간다 | stream-level flow-control stall 가능성 | 그 stream 개인 window나 app-level consume 문제가 더 의심된다 |

## 초보자가 자주 헷갈리는 포인트

- "HTTP/2는 멀티플렉싱이니까 HOL이 없다"는 절반만 맞다. HTTP 레벨 HOL은 줄지만 TCP HOL은 남는다.
- "stall이면 네트워크 장애다"도 틀릴 수 있다. H2 flow control stall은 애플리케이션이 천천히 읽어도 생긴다.
- "`MAX_CONCURRENT_STREAMS`에 걸린 것과 flow-control stall은 같다"도 틀리다. 하나는 새 stream 개수 제한이고, 다른 하나는 열린 stream의 전송 예산 문제다.
- "작은 요청도 같이 느리면 무조건 HOL blocking"도 성급하다. connection window가 바닥나면 작은 요청도 함께 멈출 수 있다.

## 안전한 다음 한 걸음

- `손실/재전송/TCP HOL` 쪽 용어가 더 많이 보였으면: [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
- `WINDOW_UPDATE/window/credit` 쪽 용어가 더 많이 보였으면: [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- `새 stream이 아예 늦게 열리는지`가 더 의심되면: [HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation](./http2-max-concurrent-streams-pending-queue-saturation.md)
- `receiver가 못 읽는 쪽`까지 같이 헷갈리면: [TCP Zero Window, Persist Probe, Receiver Backpressure](./tcp-zero-window-persist-probe-receiver-backpressure.md)

## 한 줄 정리

HTTP/2에서 "다 같이 기다림"이 핵심이면 HOL blocking을, "연결은 살아 있는데 보내도 된다는 예산이 안 돌아옴"이 핵심이면 flow-control stall을 먼저 의심하면 된다.
