---
schema_version: 3
title: "gRPC `DEADLINE_EXCEEDED`가 뜰 때 첫 분류 카드"
concept_id: network/grpc-deadline-exceeded-first-triage-card
canonical: true
category: network
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 87
mission_ids: []
review_feedback_tags:
- grpc-deadline-exceeded-triage
- flow-control-vs-backpressure-vs-loss
- beginner-grpc-timeout
aliases:
- grpc deadline exceeded triage
- grpc timeout first check
- grpc flow control stall
- grpc app backpressure
- grpc network loss
- grpc deadline beginner
symptoms:
- DEADLINE_EXCEEDED를 무조건 서버가 느린 것으로만 해석한다
- flow control stall, app backpressure, network loss를 모두 timeout 한 단어로 묶는다
- retry하면 풀린다고 보고 backpressure 상황에서 retry storm을 키운다
- headers를 받았으니 body trailers 지연은 서버 처리가 끝난 것이라고 오해한다
intents:
- troubleshooting
- symptom
- comparison
prerequisites:
- network/grpc-vs-rest
- network/grpc-deadlines-cancellation-propagation
next_docs:
- network/http2-flow-control-window-update-stalls
- network/grpc-status-trailers-transport-error-mapping
- network/packet-loss-jitter-reordering-diagnostics
- system-design/request-deadline-timeout-budget-primer
linked_paths:
- contents/network/grpc-deadlines-cancellation-propagation.md
- contents/network/grpc-status-trailers-transport-error-mapping.md
- contents/network/http2-flow-control-window-update-stalls.md
- contents/network/packet-loss-jitter-reordering-diagnostics.md
- contents/network/queue-saturation-attribution-metrics-runbook.md
- contents/system-design/request-deadline-timeout-budget-primer.md
confusable_with:
- network/grpc-deadlines-cancellation-propagation
- network/grpc-status-trailers-transport-error-mapping
- network/http2-flow-control-window-update-stalls
- network/packet-loss-jitter-reordering-diagnostics
- system-design/request-deadline-timeout-budget-primer
forbidden_neighbors: []
expected_queries:
- "gRPC DEADLINE_EXCEEDED가 뜨면 flow control stall app backpressure network loss 중 무엇부터 봐?"
- "grpc deadline exceeded가 서버가 느린 것만 뜻하지 않는 이유를 설명해줘"
- "HTTP/2 WINDOW_UPDATE 지연과 gRPC deadline exceeded를 어떻게 연결해?"
- "queue pool wait가 먼저 튀는 app backpressure와 packet loss를 구분하는 법은?"
- "DEADLINE_EXCEEDED와 CANCELLED 차이를 초급 기준으로 알려줘"
contextual_chunk_prefix: |
  이 문서는 gRPC DEADLINE_EXCEEDED를 flow control stall, app backpressure,
  network loss 세 갈래로 처음 분류하고 HTTP/2 WINDOW_UPDATE, trailers,
  queue saturation, packet loss 신호로 라우팅하는 beginner symptom router다.
---
# gRPC `DEADLINE_EXCEEDED`가 뜰 때 첫 분류 카드

> 한 줄 요약: "`gRPC deadline exceeded`가 왜 나요?"라는 질문에는 먼저 "못 보낸 쪽인가, 못 처리한 쪽인가, 중간에서 잃어버린 쪽인가"를 나눠 답해야 다음 확인이 빨라진다.

**난이도: 🟢 Beginner**

이 문서는 "gRPC `DEADLINE_EXCEEDED`가 떴는데 서버가 느린 건가요?", "처음 보면 timeout이랑 뭐가 다른지 모르겠어요", "network 문제인지 app backpressure인지 어디서 갈라야 해요?" 같은 **초급 첫 분류 질문**에 바로 답하려는 트리아지 카드다.

관련 문서:

- [gRPC Deadlines, Cancellation Propagation](./grpc-deadlines-cancellation-propagation.md)
- [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
- [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
- [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
- [Request Deadline / Timeout Budget Primer](../system-design/request-deadline-timeout-budget-primer.md)
- [network 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: grpc deadline exceeded triage, grpc timeout first check, grpc flow control stall, grpc app backpressure, grpc network loss, grpc deadline exceeded beginner, grpc deadline triage card, http2 window_update grpc, grpc trailers missing, grpc unary slow, deadline exceeded 뭐예요, grpc deadline exceeded 왜 나요, timeout 이랑 뭐가 달라요, 처음 배우는데 grpc deadline

## 먼저 잡는 멘탈 모델

`DEADLINE_EXCEEDED`는 보통 "시간 안에 끝내지 못했다"는 결과다.
하지만 초보자 첫 질문은 "왜 느렸나?"가 아니라 **어느 층에서 시간이 증발했나?**여야 한다.

세 갈래만 먼저 나누면 된다.

- `flow control stall`: 연결은 살아 있지만 `WINDOW_UPDATE`나 receive credit이 늦어 데이터가 못 흐른다.
- `app backpressure`: 서버나 다운스트림이 바빠 queue, worker, DB 대기에서 시간을 쓴다.
- `network loss`: 패킷 손실, 재전송, 경로 흔들림 때문에 같은 연결 전체가 느려진다.

짧게 비유하면 이렇다.

- `flow control stall` = 계산대는 열려 있는데 "더 담아도 됨" 표지가 안 돌아온 상태
- `app backpressure` = 가게 안쪽 조리대가 밀려 주문이 안 나오는 상태
- `network loss` = 배달 길 자체에서 사고가 나 지연되는 상태

## 30초 빠른 구분 표

| 먼저 보이는 신호 | flow control stall 쪽 | app backpressure 쪽 | network loss 쪽 |
|---|---|---|---|
| 연결 상태 | 연결은 살아 있고 stream도 열려 있음 | 연결은 정상일 수 있음 | 재연결, 재전송, RTT 상승이 같이 보이기 쉽다 |
| 데이터 흐름 | headers 뒤 DATA/trailers가 뜸해짐 | 서버 처리 완료 자체가 늦다 | 여러 요청이 같은 시점에 흔들린다 |
| 첫 확인 지표 | `WINDOW_UPDATE`, stream/connection window | queue depth, active worker, DB/pool wait | retransmission, packet loss, jitter, connection reset |
| 초보자 첫 문장 | "상대가 아직 못 읽는 쪽인가?" | "서버 안쪽 줄이 밀렸나?" | "길 자체가 흔들렸나?" |

## 1차 신호: 세 원인을 어떻게 가를까

### 1. flow control stall부터 의심할 신호

- gRPC stream은 열렸는데 응답 body나 trailers가 한동안 안 온다.
- 큰 streaming 응답 뒤에 같은 H2 connection의 작은 RPC도 같이 늦어진다.
- 손실 지표는 조용한데 `WINDOW_UPDATE` 지연, window 고갈, receiver slow-consume 이야기가 보인다.

첫 체크:

- 같은 연결의 다른 작은 요청도 같이 멈췄는가
- stream은 이미 시작됐는데 DATA만 안 흐르는가
- 프록시 버퍼링, 느린 소비자, 큰 메시지 chunk가 있는가

### 2. app backpressure부터 의심할 신호

- 서버 로그에서 handler 진입은 했지만 worker queue, DB pool wait, lock wait, downstream RPC 대기가 길다.
- `deadline exceeded`가 특정 피크 시간대, 배치 시간대, hot row 구간에서 몰린다.
- 서버 CPU보다 먼저 queue depth, active threads, pending acquire, pool waiting이 튄다.

첫 체크:

- 서버가 요청을 받긴 받았는가
- 처리 시작 전 queue에서 기다렸는가, 처리 중 DB/외부 호출에서 기다렸는가
- 같은 시각에 `busy`, `queue full`, `pending`, `pool timeout` 류 신호가 늘었는가

### 3. network loss부터 의심할 신호

- 특정 서버 로직보다 연결 단위 symptom이 먼저 보인다.
- 같은 시간대에 여러 RPC가 같이 흔들리고 RTT, 재전송, loss, reset도 같이 튄다.
- 앱이 trailers를 남기기 전에 transport close나 reconnect가 보인다.

첫 체크:

- 같은 zone, node, client network에서만 집중되는가
- retransmission, jitter, packet loss가 같이 늘었는가
- trailer 없는 종료, connection reset, GOAWAY/reconnect가 겹쳤는가

## 작은 예시 하나

| 관찰 | 더 먼저 의심할 쪽 | 이유 |
|---|---|---|
| 큰 server-streaming 하나가 오래 가는 동안 작은 unary RPC도 같이 `DEADLINE_EXCEEDED` | flow control stall | connection window가 막히면 작은 RPC도 같이 늦을 수 있다 |
| 점심 시간대마다 `pending acquire`, DB wait, queue depth가 먼저 증가한 뒤 deadline 초과 | app backpressure | 앱 안쪽 대기줄이 먼저 길어졌다는 뜻이다 |
| 배포 직후 특정 AZ에서만 재전송과 reset이 늘면서 deadline 초과 | network loss | 처리 로직보다 경로/연결 품질 이상 신호가 먼저 보인다 |

## 자주 헷갈리는 포인트

- "`DEADLINE_EXCEEDED`면 서버가 느리다" -> 항상 그렇지 않다. 흐름 제어나 네트워크 손실도 같은 결과를 만든다.
- "`CANCELLED`와 `DEADLINE_EXCEEDED`는 비슷한 timeout 이름이다" -> 다르다. 상위 호출자나 사용자가 먼저 끊으면 `CANCELLED`, 정해 둔 시간 안에 못 끝내면 `DEADLINE_EXCEEDED`다.
- "retry하면 풀린다" -> 원인이 `app backpressure`면 retry storm으로 더 나빠질 수 있다.
- "headers를 받았으니 서버 처리는 끝났다" -> 아니다. body/trailers가 막힌 `flow control stall`일 수 있다.
- "loss가 조금 보이니 무조건 network 원인" -> 같은 시각의 queue/pool wait가 더 먼저 튀었는지도 같이 봐야 한다.

## 안전한 다음 한 걸음

- `WINDOW_UPDATE`, `stream/connection window`, 큰 stream 동반이 먼저 보이면 [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
- queue, pool wait, worker saturation이 먼저 보이면 [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
- trailers 유실, reset, proxy/local reply 해석이 필요하면 [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
- packet loss, jitter, retransmission이 먼저 보이면 [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)

## 한 줄 정리

gRPC `DEADLINE_EXCEEDED`의 첫 분류는 "흐름 제어가 막혔나, 앱 안쪽 대기줄이 밀렸나, 네트워크 경로가 흔들렸나"를 가르는 일부터 시작하면 된다.
