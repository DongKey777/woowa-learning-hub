---
schema_version: 3
title: "gRPC vs REST"
concept_id: network/grpc-vs-rest
canonical: true
category: network
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- grpc-rest-choice
- protocol-buffers-vs-http-semantics
- service-communication-design
aliases:
- gRPC vs REST
- Protocol Buffers vs JSON REST
- unary streaming RPC
- schema contract HTTP semantics
- browser compatibility gRPC
- API design grpc rest
symptoms:
- gRPC를 REST보다 무조건 빠른 대체재로만 보고 browser/tooling/observability 비용을 놓친다
- REST를 느슨한 JSON 형식으로만 보고 HTTP semantics, cache, proxy compatibility 장점을 놓친다
- 내부 service-to-service와 외부/public/browser API 경계를 같은 선택 기준으로 본다
intents:
- comparison
- design
- deep_dive
prerequisites:
- network/http-methods-rest-idempotency
- network/http1-http2-http3-beginner-comparison
next_docs:
- network/grpc-web-vs-bff-vs-rest-browser-boundary-bridge
- network/grpc-status-trailers-transport-error-mapping
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/h2c-cleartext-upgrade-prior-knowledge-routing
- network/h2c-operational-traps-proxy-chain-dev-prod
linked_paths:
- contents/network/http-methods-rest-idempotency.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/sse-websocket-polling.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/grpc-status-trailers-transport-error-mapping.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
- contents/network/h2c-cleartext-upgrade-prior-knowledge-routing.md
- contents/network/h2c-operational-traps-proxy-chain-dev-prod.md
confusable_with:
- network/grpc-web-vs-bff-vs-rest-browser-boundary-bridge
- network/http-methods-rest-idempotency
- network/grpc-status-trailers-transport-error-mapping
- network/rest-websocket-sse-grpc-http2-http3-choice-primer
forbidden_neighbors: []
expected_queries:
- "gRPC와 REST를 서비스 간 통신, 공개 API, 브라우저 호환성 기준으로 비교해줘"
- "gRPC는 왜 HTTP/2와 protobuf schema contract가 핵심이고 REST는 HTTP semantics가 핵심이야?"
- "내부 서비스는 gRPC, 외부 공개 API는 REST가 더 나을 수 있는 이유는?"
- "gRPC streaming과 REST SSE WebSocket polling 선택지를 어떻게 나눠?"
- "gRPC는 운영 관측성에서 trailers status mapping과 protobuf decode 비용이 있다는 점을 설명해줘"
contextual_chunk_prefix: |
  이 문서는 gRPC와 REST를 Protocol Buffers schema contract, HTTP/2
  transport, streaming RPC, browser/public API compatibility, HTTP semantics,
  observability/tooling 기준으로 비교하는 advanced chooser다.
---
# gRPC vs REST

> 한 줄 요약: gRPC는 서비스 간 고성능 계약 기반 통신에 강하고, REST는 범용성과 운영 친화성이 좋아서 "어디서, 누구와, 어떤 방식으로" 통신하는지에 따라 선택이 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [SSE, WebSocket, Polling](./sse-websocket-polling.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [gRPC Status, Trailers, Transport Error Mapping](./grpc-status-trailers-transport-error-mapping.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [h2c, Cleartext Upgrade, Prior Knowledge, Routing](./h2c-cleartext-upgrade-prior-knowledge-routing.md)
> - [h2c Operational Traps: Proxy Chain, Dev/Prod Drift](./h2c-operational-traps-proxy-chain-dev-prod.md)

retrieval-anchor-keywords: gRPC vs REST, Protocol Buffers, unary RPC, streaming RPC, schema contract, HTTP/2 transport, browser compatibility, API design, metadata, observability

---

## 핵심 개념

REST와 gRPC는 둘 다 "서비스가 서로 통신하는 방식"이지만 철학이 다르다.

- REST는 HTTP의 의미를 최대한 살려 리소스를 다루는 방식이다.
- gRPC는 강한 계약(schema)을 바탕으로 메서드 호출처럼 통신하는 방식이다.

대표적으로 이렇게 구분하면 된다.

| 항목 | REST | gRPC |
|------|------|------|
| 기본 포맷 | JSON이 흔함 | Protocol Buffers |
| 전송 방식 | HTTP/1.1 또는 HTTP/2 | HTTP/2가 사실상 기본 |
| 계약 | 느슨함, 문서 중심 | 강함, `.proto` 중심 |
| 스트리밍 | 보통 별도 구현 | unary / server streaming / client streaming / bidirectional streaming |
| 브라우저 | 매우 좋음 | 직접 사용은 제약이 큼 |
| 운영 친화성 | 높음 | 성숙한 인프라가 필요 |

이 문서는 [HTTP 메서드, REST, 멱등성](./http-methods-rest-idempotency.md)에서 설명한 "HTTP 의미"를 한 단계 확장한 내용이다.

### Retrieval Anchors

- `gRPC vs REST`
- `Protocol Buffers`
- `unary RPC`
- `streaming RPC`
- `schema contract`
- `HTTP/2 transport`
- `browser compatibility`
- `metadata`

---

## 깊이 들어가기

### 1. gRPC는 왜 HTTP/2 위에 올라갔나

gRPC는 단순히 "REST보다 빠른 RPC"가 아니다. 핵심은 **하나의 연결을 효율적으로 재사용하면서, 강한 계약으로 서비스 간 호출을 표준화**하는 데 있다.

HTTP/2가 중요한 이유:

- multiplexing으로 하나의 TCP 연결에서 여러 요청을 동시에 흘릴 수 있다
- binary framing이라 텍스트 파싱 부담이 줄어든다
- header compression으로 반복 헤더 비용을 줄일 수 있다
- stream 단위 flow control을 제공한다

즉 gRPC의 성능은 "프로토콜이 마법이라서"가 아니라, **HTTP/2의 연결 재사용과 프레이밍 구조** 덕분이다.

### 2. REST는 왜 여전히 강한가

REST가 강한 이유는 성능보다 **범용성**이다.

- 브라우저, curl, 프록시, 캐시, 보안 장비와 궁합이 좋다
- 사람이 직접 읽고 디버깅하기 쉽다
- 공개 API에 적합하다
- HTTP semantics를 그대로 활용할 수 있다

특히 외부 공개 API에서는 REST가 실무적으로 더 편한 경우가 많다.

### 3. 스트리밍 모델 차이

gRPC는 스트리밍을 1급 기능으로 제공한다.

- Unary RPC: 요청 1개, 응답 1개
- Server streaming: 요청 1개, 응답 여러 개
- Client streaming: 요청 여러 개, 응답 1개
- Bidirectional streaming: 양쪽이 동시에 여러 메시지 주고받기

REST에서도 비슷한 효과를 낼 수는 있다.

- SSE로 서버 -> 클라이언트 스트리밍
- WebSocket으로 양방향 통신
- polling으로 주기적 조회

하지만 REST는 이런 기능이 "기본 호출 모델"이 아니라 **별도 선택지**라는 점이 다르다.  
실시간 이벤트가 핵심이면 [SSE, WebSocket, Polling](./sse-websocket-polling.md)와 함께 봐야 한다.

### 4. 계약과 스키마

gRPC는 `.proto`가 계약의 중심이다.

- 요청/응답 필드가 명시된다
- 타입이 엄격하다
- 코드 생성으로 클라이언트와 서버가 같은 계약을 본다
- 필드 번호를 유지하면 하위 호환을 관리하기 쉽다

REST는 보통 OpenAPI, 문서, 관례가 계약 역할을 한다.

- JSON 필드가 느슨하다
- 버전과 호환성은 팀 규율에 크게 의존한다
- 잘 관리하면 유연하지만, 방치하면 깨지기 쉽다

### 5. 관측성과 디버깅

REST는 네트워크 관측 도구와 매우 잘 맞는다.

- 브라우저 devtools
- curl
- nginx access log
- API gateway log

gRPC는 추가 도구가 필요하다.

- protobuf decode 도구
- gRPC interceptors
- metadata 로깅
- tracing span 정리

운영에서는 "성능"보다 **문제가 났을 때 추적이 쉬운가**가 더 중요하다.  
그래서 외부 고객 API는 REST, 내부 서비스 호출은 gRPC가 흔한 조합이다.

---

## 실전 시나리오

### 시나리오 1: 모바일 앱과 백엔드

모바일 앱이 직접 백엔드를 호출한다면 REST가 대체로 유리하다.

- HTTP 캐시와 프록시 지원이 좋다
- 디버깅이 쉽다
- 공개 API 문서화가 단순하다

하지만 내부 앱 SDK를 통해 강한 계약과 성능이 필요하다면 gRPC를 고려할 수 있다.

### 시나리오 2: 마이크로서비스 내부 호출

서비스 A가 서비스 B를 자주 호출하고, 호출 수가 많으며, payload가 작고, 타입이 자주 바뀐다면 gRPC가 유리하다.

이유:

- JSON 직렬화/역직렬화 비용이 줄어든다
- 계약이 명확해진다
- streaming이 필요한 작업에 맞다

예:

- 추천 엔진이 여러 후보를 스트리밍으로 내려주는 경우
- 결제 승인 후 후속 검증 결과를 연속적으로 받는 경우

### 시나리오 3: 브라우저 지원이 필요함

gRPC는 브라우저가 직접 쓰기 어렵다.  
이 경우 보통 다음 중 하나가 된다.

- REST로 노출한다
- gRPC-Web을 프록시 뒤에 둔다
- BFF가 gRPC를 받고 브라우저용 REST로 변환한다

브라우저가 주요 클라이언트면 REST 우선이 현실적이다.

### 시나리오 4: 롤아웃 중 계약이 깨짐

gRPC의 장점은 강한 계약이지만, 그만큼 배포 순서가 중요하다.

- 필드 제거를 먼저 하면 구버전 클라이언트가 깨질 수 있다
- 필드 번호를 재사용하면 데이터 해석이 꼬일 수 있다
- enum 값 변경도 조심해야 한다

REST도 깨지지만, gRPC는 코드 생성 때문에 깨짐이 더 빨리 드러나는 편이다.

---

## 코드로 보기

### REST 예시

```http
GET /users/42
Accept: application/json
```

```json
{
  "id": 42,
  "name": "donghun",
  "status": "ACTIVE"
}
```

### gRPC 예시

```proto
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (GetUserResponse);
  rpc StreamNotifications (NotificationRequest) returns (stream NotificationEvent);
}

message GetUserRequest {
  int64 user_id = 1;
}

message GetUserResponse {
  int64 user_id = 1;
  string name = 2;
  string status = 3;
}
```

```java
// Java client side
UserServiceGrpc.UserServiceBlockingStub stub = UserServiceGrpc.newBlockingStub(channel);
GetUserResponse response = stub.getUser(GetUserRequest.newBuilder()
    .setUserId(42L)
    .build());
```

### 인터셉터로 메타데이터를 다루는 예시

```java
public class TraceIdClientInterceptor implements ClientInterceptor {
    @Override
    public <ReqT, RespT> ClientCall<ReqT, RespT> interceptCall(
            MethodDescriptor<ReqT, RespT> method,
            CallOptions callOptions,
            Channel next) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(next.newCall(method, callOptions)) {
            @Override
            public void start(Listener<RespT> responseListener, Metadata headers) {
                headers.put(Metadata.Key.of("x-trace-id", Metadata.ASCII_STRING_MARSHALLER), "trace-123");
                super.start(responseListener, headers);
            }
        };
    }
}
```

이런 메타데이터는 REST에서 헤더로 보내는 것과 비슷하지만, gRPC에서는 호출 체인 전반에 같은 방식으로 붙일 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| REST | 범용성, 브라우저 친화성, 운영 용이성 | 느슨한 계약, 스트리밍이 기본은 아님 | 외부 공개 API, BFF, 단순 CRUD |
| gRPC | 강한 계약, 성능, 스트리밍, 코드 생성 | 브라우저 제약, 학습/운영 복잡도 | 내부 서비스 간 통신, 고성능 RPC |
| REST + SSE/WebSocket | 브라우저 실시간에 유리 | 프로토콜이 분리되어 복잡해질 수 있음 | 사용자-facing 실시간 화면 |
| gRPC-Web | gRPC 장점을 일부 유지 | 프록시와 브라우저 제약 | 조직 표준이 gRPC이고 웹도 필요할 때 |

실무 판단 기준은 단순하다.

1. 누가 호출하는가
2. 브라우저가 직접 호출하는가
3. 스트리밍이 필요한가
4. 계약을 얼마나 엄격하게 관리할 것인가
5. 장애 시 추적성과 디버깅이 얼마나 중요한가

---

## 꼬리질문

> Q: gRPC가 REST보다 무조건 빠른가?
> 의도: 성능을 단정하는지, 실제 병목이 직렬화인지 네트워크인지 구분하는지 확인
> 핵심: 보통은 내부 호출과 스트리밍에서 유리하지만, 네트워크 경로와 운영 비용까지 포함해야 판단할 수 있다

> Q: 브라우저가 있는데 왜 gRPC를 바로 못 쓰나?
> 의도: 브라우저 환경과 HTTP/2 제약, gRPC-Web 필요성을 이해하는지 확인
> 핵심: 브라우저의 직접적인 gRPC 지원 제약 때문에 보통 REST, BFF, gRPC-Web을 함께 고려한다

> Q: 계약이 강하면 왜 좋은가?
> 의도: schema-first 설계의 장점을 이해하는지 확인
> 핵심: 코드 생성과 명시적 타입 덕분에 변경 영향이 빨리 드러나고, 서비스 간 호환성 관리가 쉬워진다

> Q: gRPC에서 버전 업은 어떻게 해야 하나?
> 의도: 필드 번호, 하위 호환, 점진적 롤아웃 감각 확인
> 핵심: 필드 추가는 비교적 안전하지만, 필드 삭제와 번호 재사용은 위험하므로 점진적으로 바꿔야 한다

---

## 한 줄 정리

REST는 범용성과 운영 친화성이 강하고, gRPC는 내부 서비스 간 고성능 계약과 스트리밍에 강하다. 클라이언트 종류, 스트리밍 필요성, 관측성과 롤아웃 난이도를 함께 보고 선택해야 한다.
