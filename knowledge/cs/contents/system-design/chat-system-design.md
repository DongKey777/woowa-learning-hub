---
schema_version: 3
title: 채팅 시스템 설계
concept_id: system-design/chat-system-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- chat system design
- 채팅 시스템 설계
- 채팅 서버 뭐예요
- 처음 배우는데 채팅 설계
aliases:
- chat system design
- 채팅 시스템 설계
- 채팅 서버 뭐예요
- 처음 배우는데 채팅 설계
- websocket chat architecture
- message ordering chat
- offline message delivery
- chat ack retry
- chat idempotency
- group chat fanout
- 채팅 순서 보장
- 채팅 읽음 표시 설계
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/network/websocket-basics.md
- contents/network/sse-websocket-polling.md
- contents/network/websocket-heartbeat-backpressure-reconnect.md
- contents/network/grpc-vs-rest.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/system-design/message-queue-basics.md
- contents/database/mvcc-replication-sharding.md
- contents/database/index-and-explain.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- 채팅 시스템 설계 설계 핵심을 설명해줘
- chat system design가 왜 필요한지 알려줘
- 채팅 시스템 설계 실무 트레이드오프는 뭐야?
- chat system design 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 채팅 시스템 설계를 다루는 deep_dive 문서다. 실시간 연결, 메시지 순서, 오프라인 전달, 중복 방지를 동시에 만족시키는 메시징 시스템의 설계다. 검색 질의가 chat system design, 채팅 시스템 설계, 채팅 서버 뭐예요, 처음 배우는데 채팅 설계처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# 채팅 시스템 설계

> 한 줄 요약: 실시간 연결, 메시지 순서, 오프라인 전달, 중복 방지를 동시에 만족시키는 메시징 시스템의 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [WebSocket 기초](../network/websocket-basics.md)
> - [SSE, WebSocket, Polling](../network/sse-websocket-polling.md)
> - [WebSocket heartbeat, backpressure, reconnect](../network/websocket-heartbeat-backpressure-reconnect.md)
> - [gRPC vs REST](../network/grpc-vs-rest.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](../network/connection-keepalive-loadbalancing-circuit-breaker.md)
> - [메시지 큐 기초](./message-queue-basics.md)
> - [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)

retrieval-anchor-keywords: chat system design, 채팅 시스템 설계, 채팅 서버 뭐예요, 처음 배우는데 채팅 설계, websocket chat architecture, message ordering chat, offline message delivery, chat ack retry, chat idempotency, group chat fanout, 채팅 순서 보장, 채팅 읽음 표시 설계, chat system basics, real-time messaging design, 채팅 설계 헷갈리는 포인트

---

## 핵심 개념

채팅 시스템은 "문자열을 보내는 API"가 아니다.  
실제로는 다음 요구를 함께 만족해야 한다.

- 연결을 오래 유지해야 한다.
- 메시지를 가능한 한 빨리 전달해야 한다.
- 순서가 깨지지 않게 해야 한다.
- 수신자가 오프라인이어도 보관해야 한다.
- 중복 전송과 재시도를 견뎌야 한다.
- 읽음 표시, 전달 상태, 타이핑 표시 같은 부가 상태를 다뤄야 한다.

가장 먼저 범위를 고정해야 한다.

- 1:1 채팅인가
- 그룹 채팅인가
- 사진/파일 첨부가 있는가
- 읽음 표시가 필요한가
- 멀티 디바이스 동기화가 필요한가
- 검색과 보관 정책까지 포함하는가

---

## 깊이 들어가기

### 1. 통신 모델

실시간 채팅의 기본은 WebSocket이다.  
하지만 모든 기능이 WebSocket 하나로 끝나는 것은 아니다.

| 방법 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| WebSocket | 양방향, 지연이 낮다 | 연결 관리가 필요하다 | 실시간 채팅 |
| SSE | 서버 푸시가 단순하다 | 단방향이다 | 알림, 읽기 위주 스트림 |
| Polling | 구현이 쉽다 | 비효율적이다 | 레거시, 저빈도 갱신 |

채팅은 보통 연결 유지가 핵심이라 WebSocket이 기본이다.  
다만 인증 갱신, 파일 업로드, 메시지 검색 같은 기능은 별도 HTTP API로 분리하는 경우가 많다.

### 2. 메시지 순서

채팅에서 순서는 생각보다 어렵다.  
네트워크는 지연과 재전송이 있고, 서버도 여러 대일 수 있다.

순서 보장의 기준은 보통 채널 단위다.

- `conversationId` 단위로 순서를 보장한다.
- 각 메시지에 monotonic sequence 또는 timestamp를 부여한다.
- 서버가 수신 시점에 정렬 기준을 결정한다.

중요한 점은 "전역 순서"가 아니라 **conversation 단위 순서**만 보장해도 대부분의 제품 요구를 만족한다는 것이다.

### 3. 전달 보장

메시지 전달은 보통 다음 상태를 가진다.

- sent
- delivered
- read
- failed

이 상태는 사용자 경험에는 중요하지만, 저장 방식은 별도로 설계해야 한다.

기본 패턴:

1. sender가 메시지를 보낸다.
2. 서버는 메시지를 저장한다.
3. 서버는 수신자에게 push한다.
4. 수신자가 ack를 보내면 delivered로 바꾼다.
5. 클라이언트가 읽으면 read로 바꾼다.

여기서 ack가 없으면 재전송이 필요하지만, 재전송은 중복을 만든다.  
그래서 message idempotency가 중요하다.

### 4. 오프라인 전달

상대가 오프라인이면 서버는 메시지를 큐처럼 보관해야 한다.

핵심은 두 계층이다.

- 실시간 전달용 inbox
- 영속 저장소용 message store

오프라인 사용자가 다시 접속하면:

1. 마지막으로 확인한 offset을 보낸다.
2. 서버는 그 이후 메시지를 다시 내려준다.
3. 누락분을 보정한다.

이때 "어디까지 읽었는지"를 저장하지 않으면, 재접속마다 전체 히스토리를 다시 보내야 한다.

### 5. 방 개념과 fan-out

채팅은 1:1보다 그룹에서 어려워진다.

선택지는 두 가지다.

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| Fan-out on write | 수신자별 inbox를 미리 만든다 | 쓰기 비용이 크다 | 작은 그룹, 읽기 최적화 |
| Fan-out on read | 읽을 때 계산한다 | 읽기 비용이 크다 | 매우 큰 그룹, 쓰기 집중 |

그룹 크기, 읽기 빈도, 오프라인 비율에 따라 선택이 달라진다.

### 6. 세션과 연결 상태

WebSocket 연결은 사용자 세션과 얽힌다.

문제:

- 사용자가 여러 디바이스로 접속한다.
- 연결이 끊겼다가 다시 붙는다.
- 인증 토큰이 중간에 만료된다.

운영 포인트:

- connection registry가 필요하다.
- userId -> connectionId 매핑이 필요하다.
- 토큰 갱신과 연결 재수립 정책이 필요하다.
- 세션 스티키가 필요한지 판단해야 한다.

### 7. 샤딩과 저장소

메시지는 시간이 지날수록 계속 쌓인다.  
DB 단일 테이블로 끝내면 곧 한계가 온다.

보통 다음을 고려한다.

- conversationId 기준 샤딩
- 최근 메시지는 hot storage, 오래된 메시지는 cold storage
- 검색용 인덱스 분리
- 첨부 파일은 object storage 분리

DB 관점에서는 [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)와 [인덱스와 실행 계획](../database/index-and-explain.md)을 같이 봐야 한다.

---

## 실전 시나리오

### 시나리오 1: 1:1 채팅

구성:

- WebSocket으로 실시간 연결
- 메시지 저장 후 push
- ack 기반 delivered/read 상태 관리
- 오프라인이면 재접속 시 backlog 재전송

이 경우 순서와 idempotency가 가장 중요하다.

### 시나리오 2: 대형 그룹 채팅

문제:

- 한 메시지가 수천 명에게 가야 한다.
- 쓰기 비용이 급증한다.

대응:

- fan-out on read 고려
- 읽기 캐시와 inbox 분리
- 초대형 room은 별도 fan-out worker 사용

### 시나리오 3: 모바일 네트워크 불안정

문제:

- 연결이 자주 끊긴다.
- 메시지 재전송이 많다.

대응:

- message id를 클라이언트가 들고 재시도한다.
- 서버는 중복 수신을 idempotent하게 처리한다.
- 마지막 offset을 저장한다.

---

## 코드로 보기

### 1. 메시지 저장 의사코드

```pseudo
function sendMessage(conversationId, senderId, body, clientMessageId):
    if exists(clientMessageId):
        return loadResult(clientMessageId)

    seq = nextSequence(conversationId)
    message = save(conversationId, seq, senderId, body)
    enqueueDelivery(conversationId, message.id)
    return message
```

### 2. WebSocket handler 개요

```java
@Component
public class ChatHandler {
    public void onMessage(String userId, String conversationId, ChatRequest request) {
        ChatMessage message = chatService.send(
            conversationId,
            userId,
            request.body(),
            request.clientMessageId()
        );

        websocketBroadcaster.broadcast(conversationId, message);
    }
}
```

### 3. ack 처리

```java
public void ackDelivered(String userId, String messageId) {
    deliveryRepository.markDelivered(userId, messageId);
}
```

핵심은 ack를 신뢰하되, ack가 오지 않아도 재전송이 안전해야 한다는 점이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| WebSocket 중심 | 실시간성이 좋다 | 연결 관리가 어렵다 | 일반적인 채팅 |
| HTTP polling 중심 | 단순하다 | 비효율적이다 | 저빈도, 레거시 |
| Fan-out on write | 읽기 빠름 | 쓰기 비용 큼 | 중소 규모 room |
| Fan-out on read | 쓰기 단순 | 읽기 비용 큼 | 초대형 room |
| 강한 순서 보장 | UX가 안정적 | 지연과 복잡도 증가 | 금융/업무 메시지 |

채팅 시스템은 "최고의 실시간성"보다 "사용자가 체감하는 일관된 경험"을 목표로 잡는 편이 안전하다.

---

## 꼬리질문

> Q: 채팅에서 메시지 순서를 전역으로 보장해야 하나요?
> 의도: 과도한 일관성 요구를 거를 수 있는지 확인
> 핵심: 대부분 conversation 단위 순서면 충분하다

> Q: 오프라인 메시지는 어디에 저장하나요?
> 의도: 실시간과 영속 저장의 역할 분리를 아는지 확인
> 핵심: inbox와 message store를 분리해서 설계한다

> Q: 중복 전송은 어떻게 막나요?
> 의도: 네트워크 재시도와 idempotency 이해 확인
> 핵심: clientMessageId와 messageId를 통해 중복을 흡수한다

> Q: 그룹 채팅에서 fan-out on write를 항상 쓰면 안 되는 이유는?
> 의도: 확장 비용 감각 확인
> 핵심: 큰 room에서는 쓰기 증폭이 너무 커진다

---

## 한 줄 정리

채팅 시스템은 실시간 연결 위에 순서, 전달 보장, 오프라인 복구, 중복 방지를 얹어야 하는 복합 시스템이다.
