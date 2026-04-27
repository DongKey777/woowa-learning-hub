# API Gateway, Reverse Proxy 운영 포인트


> 한 줄 요약: API Gateway, Reverse Proxy 운영 포인트는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../security/session-cookie-jwt-basics.md)

> 프록시를 "중간 서버"로만 이해하면 운영에서 자주 놓치는 지점들을 정리한 문서

> 관련 문서:
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Proxy Retry Budget Discipline](./proxy-retry-budget-discipline.md)
> - [Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
> - [h2c, Cleartext Upgrade, Prior Knowledge, Routing](./h2c-cleartext-upgrade-prior-knowledge-routing.md)
> - [TLS close_notify, FIN/RST, Truncation](./tls-close-notify-fin-rst-truncation.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

retrieval-anchor-keywords: api gateway, reverse proxy, proxy chain, timeout budget propagation, upstream timeout, rate limit, auth, forwarded headers, protocol bridge, request routing, api gateway reverse proxy operational points basics, api gateway reverse proxy operational points beginner, api gateway reverse proxy operational points intro, network basics, beginner network

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [API Gateway와 Reverse Proxy의 경계](#api-gateway와-reverse-proxy의-경계)
- [Reverse Proxy 운영 포인트](#reverse-proxy-운영-포인트)
- [API Gateway가 자주 맡는 역할](#api-gateway가-자주-맡는-역할)
- [실전 장애 패턴](#실전-장애-패턴)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제가 중요한가

실무에서 Nginx, Envoy, Kong, Apigee 같은 계층을 붙이는 이유는 단순히 "요청을 전달하기 위해서"가 아니다.

- 인증과 인가를 앞단으로 모으기 위해서
- TLS 종료 지점을 통일하기 위해서
- 서버 주소와 버전을 외부에 직접 노출하지 않기 위해서
- 로깅, 추적, rate limit, 라우팅 정책을 한 곳에서 다루기 위해서

즉, 프록시는 네트워크 장비가 아니라 **운영 정책을 구현하는 진입점**에 가깝다.

---

## API Gateway와 Reverse Proxy의 경계

둘은 겹치는 부분이 많지만 관점이 다르다.

### Reverse Proxy

- 클라이언트 요청을 받아 내부 서버로 전달한다
- 보통 경로 기반 라우팅, TLS 종료, 압축, 캐싱, 로깅을 담당한다
- "뒤에 있는 서버를 대신하는 프록시"라는 의미가 강하다

### API Gateway

- 여러 마이크로서비스 앞에서 **API 정책을 통합**하는 계층이다
- 인증, 인가, rate limit, quota, request/response 변환, 버전 라우팅을 붙인다
- 외부 고객용 API와 내부 서비스 간 경계를 관리한다

### 감각적으로 구분하면

- Reverse Proxy는 "트래픽을 어떻게 흘릴지"가 중심이다
- API Gateway는 "어떤 정책으로 API를 운영할지"가 중심이다

---

## Reverse Proxy 운영 포인트

### 1. 헤더를 어떻게 전달할지 정해야 한다

프록시는 보통 클라이언트 정보를 그대로 upstream에 넘기지 않는다. 대신 아래 헤더를 정리해 전달한다.

- `X-Forwarded-For`: 원래 클라이언트 IP
- `X-Forwarded-Proto`: `http`인지 `https`인지
- `X-Forwarded-Host`: 원래 요청 호스트
- `X-Request-Id`: 요청 추적용 식별자

이 값이 일관되지 않으면 서버 로그를 보고도 "누가 어디서 요청했는지" 추적이 어렵다.

### 2. timeout은 프록시와 upstream을 같이 봐야 한다

프록시 timeout이 너무 짧으면 정상 요청도 잘린다. upstream timeout이 더 짧으면 프록시는 끝까지 기다리다가 504를 반환한다.

- connect timeout: 서버 연결 자체가 안 될 때
- read timeout: 연결은 됐지만 응답이 늦을 때
- idle timeout: 한동안 데이터가 없을 때

중요한 건 timeout 숫자 하나가 아니라 **어느 구간에서 실패를 판단할지**다.

### 3. buffering이 필요한지 봐야 한다

프록시는 요청과 응답을 버퍼링할 수 있다.

- 큰 업로드를 먼저 다 받아서 upstream에 넘길지
- 응답을 받아서 클라이언트에 바로 흘려보낼지

버퍼링은 안정성을 높이지만 메모리 사용량과 지연을 늘릴 수 있다.
특히 대용량 업로드 API는 [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)처럼 auth와 body 업로드 순서를 따로 봐야 한다.
또 early reject를 쓸수록 [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)처럼 unread body 정리와 keep-alive 재사용 정책도 함께 설계해야 한다.
응답 경로에서는 [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)처럼 gzip/brotli가 chunk cadence를 바꾸는 점도 같이 봐야 한다.

### 4. keep-alive와 connection pool을 신경 써야 한다

프록시가 upstream과 매 요청마다 새 TCP 연결을 맺으면 비용이 커진다.

- TCP handshake 비용이 늘어난다
- 커넥션 수립 지연이 누적된다
- 서버와 프록시 모두 socket 자원을 더 많이 쓴다

그래서 보통 upstream 연결을 재사용한다. 다만 연결 재사용은 뒤쪽 서버가 바뀌었을 때 stale connection 문제가 생길 수 있어서 health check와 drain 정책이 같이 필요하다.

## Reverse Proxy 운영 포인트 (계속 2)

### 5. WebSocket, SSE, streaming은 별도로 다뤄야 한다

일반 HTTP와 달리 장시간 연결이 유지되므로 아래를 따로 봐야 한다.

- idle timeout을 너무 짧게 두면 연결이 끊긴다
- proxy buffering이 스트리밍을 막을 수 있다
- load balancer가 세션 지속성을 필요로 할 수 있다

### 6. 로깅과 추적이 없으면 장애 분석이 어렵다

운영 프록시는 라우팅만 하면 끝나지 않는다.

- access log
- upstream response time
- retry 횟수
- 4xx/5xx 비율
- request id 연동
- client disconnect / `499` 비율과 backend cancel 전파 지연

이 정보가 있어야 "어느 계층에서 늦었는지"를 구분할 수 있다.

---

## API Gateway가 자주 맡는 역할

### 인증과 인가

- JWT 검증
- OAuth 토큰 검증
- API key 인증
- 서비스별 접근 제어

이걸 각 서비스에 흩뿌리면 정책이 금방 달라진다. 게이트웨이에서 공통 처리하면 일관성을 유지하기 쉽다.

### Rate limit과 quota

- 초당 요청 수 제한
- 사용자별 일일 quota
- 특정 경로에 대한 burst 제어

이건 장애 대응뿐 아니라 과금과 abuse 방지에도 중요하다.

### 라우팅과 버전 관리

- `/v1`, `/v2` 같은 버전 분기
- 내부 마이크로서비스로 path 기반 분기
- canary release, blue-green 배포

외부 공개 API는 바뀌기 어렵기 때문에, 게이트웨이에서 점진적으로 트래픽을 나누는 방식이 자주 쓰인다.

### 요청/응답 변환

- header 추가/삭제
- body shaping
- 압축, gzip 처리
- legacy API와 신규 API 사이 변환

게이트웨이가 너무 많은 변환을 맡으면 비즈니스 로직이 새기 시작하므로, 경계는 적당히 유지해야 한다.

---

## 실전 장애 패턴

### 502 Bad Gateway

- 프록시가 upstream으로부터 유효한 응답을 받지 못했다
- upstream 프로세스가 죽었거나 연결이 끊겼을 가능성이 크다

### 503 Service Unavailable

- upstream이 과부하 상태이거나 일시적으로 서비스하지 못한다
- 배포 중 drain이 안 됐을 때도 자주 나온다

### 504 Gateway Timeout

- upstream이 제시간에 응답하지 않았다
- 프록시 timeout이 upstream보다 짧거나, reverse path가 막힌 경우가 있다

### 흔한 운영 실수

- client IP를 잃어버려 레이트리밋이 무력화된다
- retry 정책이 프록시와 애플리케이션 양쪽에 중복되어 폭증한다
- keep-alive를 너무 공격적으로 써서 오래된 연결을 재사용한다
- 로드밸런서 뒤에서 세션 의존 코드를 그대로 둔다

---

## 면접에서 자주 나오는 질문

### Q. API Gateway와 Reverse Proxy의 차이는 무엇인가요?

- Reverse Proxy는 요청 전달과 라우팅 중심이고, API Gateway는 인증, rate limit, 버전 관리 같은 API 정책 중심이다.

### Q. 프록시가 있어도 원본 클라이언트 IP를 알 수 있나요?

- `X-Forwarded-For` 같은 헤더를 통해 알 수 있다. 다만 신뢰 가능한 프록시 체인에서만 해석해야 한다.

### Q. 프록시 timeout은 왜 중요한가요?

- 프록시가 먼저 끊어도 장애이고, upstream이 너무 오래 붙잡아도 장애이기 때문이다. 구간별 timeout을 같이 설계해야 한다.

### Q. WebSocket을 프록시 뒤에서 운영할 때 주의점은 무엇인가요?

- 장시간 연결, idle timeout, 연결 업그레이드, sticky session 필요 여부를 따로 봐야 한다.

## 한 줄 정리

API Gateway, Reverse Proxy 운영 포인트는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
