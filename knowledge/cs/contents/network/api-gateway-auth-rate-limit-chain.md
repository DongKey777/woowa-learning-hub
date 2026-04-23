# API Gateway Auth Rate Limit Chain

> 한 줄 요약: API Gateway의 인증과 rate limit은 따로 붙이는 기능이 아니라, 어떤 순서로 검사하고 어떤 실패를 돌려줄지까지 포함한 운영 체인이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [Expect 100-continue, Proxy Request Buffering](./expect-100-continue-proxy-request-buffering.md)
> - [Gateway Buffering vs Spring Early Reject](./gateway-buffering-vs-spring-early-reject.md)
> - [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)

retrieval-anchor-keywords: API gateway auth, rate limit chain, early reject, JWT validation, token bucket, tenant quota, request buffering, 401 vs 403 vs 429, gateway policy, auth before body, upload auth before body, spring early reject bridge

<details>
<summary>Table of Contents</summary>

- [왜 이 주제가 중요한가](#왜-이-주제가-중요한가)
- [체인의 기본 순서](#체인의-기본-순서)
- [Auth 설계 포인트](#auth-설계-포인트)
- [Rate Limit 설계 포인트](#rate-limit-설계-포인트)
- [실전 장애 패턴](#실전-장애-패턴)
- [코드로 보기](#코드로-보기)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 이 주제가 중요한가

게이트웨이에서 인증과 rate limit은 자주 같은 요청 흐름에 붙는다.

- 누가 보냈는지 먼저 확인한다
- 그 사용자가 얼마만큼 쓸 수 있는지 본다
- 이상하면 바로 막는다
- 통과한 요청만 백엔드로 넘긴다

이때 순서가 어긋나면:

- 인증 안 된 요청이 rate limit 자원을 소모한다
- 인증된 사용자도 잘못 차단된다
- 에러 코드가 모호해져서 운영이 어려워진다

즉 이건 단순한 미들웨어 조합이 아니라 **정책 체인**이다.

### Retrieval Anchors

- `API gateway auth`
- `rate limit chain`
- `early reject`
- `JWT validation`
- `token bucket`
- `tenant quota`
- `request buffering`
- `401 vs 403 vs 429`

---

## 체인의 기본 순서

실무에서 자주 쓰는 흐름은 대체로 이렇다.

1. TLS 종료와 기본 헤더 정리
2. 인증 정보 추출
3. 토큰/키 검증
4. 권한과 scope 확인
5. rate limit 확인
6. 로깅과 추적 ID 부여
7. upstream 라우팅

### 왜 이 순서인가

- 먼저 누구인지 알아야 개별 quota를 적용할 수 있다
- 인증이 실패한 요청에 비싼 rate limit 카운터를 쓰면 낭비다
- 반대로 rate limit을 먼저 두면 익명 트래픽 폭주를 먼저 막을 수 있다

그래서 실제 순서는 시스템 목적에 따라 조금 달라진다.
대용량 업로드 API라면 auth를 빨리 끝내는 것만큼 [HTTP Request Body Drain, Early Reject, Keep-Alive Reuse](./http-request-body-drain-early-reject-keepalive-reuse.md)처럼 남은 body를 어떻게 정리할지도 중요하다.

### 중요한 건 일관성이다

- 인증 실패는 보통 `401`
- 권한 부족은 보통 `403`
- 제한 초과는 보통 `429`

이 구분이 흔들리면 클라이언트도, 운영자도 헷갈린다.

---

## Auth 설계 포인트

### 어떤 인증 수단을 지원할지 정해야 한다

- JWT
- API key
- OAuth access token
- mTLS

게이트웨이가 너무 많은 인증 방식을 다 떠안으면 정책이 복잡해진다.

### 토큰 검증의 현실

- 서명 검증은 로컬에서 가능하다
- 공개키 회전은 별도 캐시가 필요하다
- exp, aud, iss, scope를 꼼꼼히 봐야 한다

토큰이 "형식상 유효"한 것과 "이 API를 호출해도 되는 것"은 다르다.

### 헤더 신뢰 문제

프록시 뒤에서는 클라이언트가 `X-Forwarded-*`를 임의로 넣을 수 있다.

- 신뢰 가능한 프록시 체인인지 확인해야 한다
- 인증 정보는 외부 헤더보다 검증된 토큰을 우선해야 한다
- 내부 서비스용 헤더는 게이트웨이에서 재작성하는 편이 안전하다

### 인증 실패 응답

- `401 Unauthorized`는 인증 자체가 실패한 경우에 쓴다
- `403 Forbidden`은 인증은 됐지만 권한이 없는 경우에 쓴다

이 차이는 클라이언트 구현과 장애 분석에 직접 영향을 준다.

---

## Rate Limit 설계 포인트

### 무엇을 기준으로 제한할지

- IP 기준
- 사용자 기준
- API key 기준
- 조직/테넌트 기준
- 엔드포인트 기준

실무에서는 하나만 쓰기보다 여러 키를 섞는다.

### 어떤 알고리즘을 쓸지

- Fixed window: 단순하다
- Sliding window: 더 부드럽다
- Token bucket: burst를 허용하면서 평균 속도를 제한한다
- Leaky bucket: 일정한 배출을 강제한다

운영에서는 token bucket이 자주 보인다.

### 분산 환경에서 어려운 점

게이트웨이가 여러 대면 카운터를 어떻게 공유할지 정해야 한다.

- Redis 같은 외부 저장소를 쓴다
- 로컬 캐시는 짧게만 쓴다
- eventual consistency를 받아들일지 정한다

여기서 중요한 건 정확도와 지연의 균형이다.

### 429를 어떻게 다룰지

- `Retry-After`를 줄지
- 사용자별로 다른 한도를 줄지
- burst와 steady-state를 분리할지

rate limit은 단순 차단이 아니라 **사용량 제어 인터페이스**다.

---

## 실전 장애 패턴

### 1. 인증 서버가 느려서 전체 API가 막힌다

원인:

- 게이트웨이가 매 요청마다 원격 introspection을 한다
- auth 서비스가 병목이 된다
- timeout이 길어져 대기열이 늘어난다

대응:

- 서명 검증 가능한 토큰은 로컬 검증으로 바꾼다
- auth 결과를 짧게 캐시한다
- auth timeout을 백엔드 timeout보다 짧게 둔다

### 2. rate limit이 로그인 직후부터 이상하다

원인:

- 사용자 식별자가 아직 확정되지 않았다
- 익명 구간과 로그인 구간의 키가 다르다
- 여러 프록시가 client IP를 잘못 전달한다

이 경우 IP 기준과 사용자 기준 한도를 분리해야 한다.

### 3. 프록시 여러 단을 거치면 차단이 흔들린다

원인:

- trust proxy 설정이 잘못됐다
- `X-Forwarded-For` 체인을 잘못 해석한다
- 내부망 IP를 클라이언트 IP로 착각한다

이 문제는 rate limit만이 아니라 감사 로그, 보안 정책까지 망가뜨린다.

### 4. retry가 rate limit을 더 악화시킨다

원인:

- 클라이언트가 429나 401에도 재시도한다
- 게이트웨이와 앱이 둘 다 retry한다
- 한 번 막힌 요청이 폭발적으로 반복된다

이건 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 바로 연결된다.

---

## 코드로 보기

### 게이트웨이 체인 감각

```text
request ->
  tls terminate ->
  auth check ->
  quota / rate limit ->
  route upstream ->
  log / trace
```

### Nginx 감각 예시

```nginx
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_set_header X-Request-Id $request_id;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass http://backend;
}
```

### 운영에서 확인할 것

```bash
curl -i https://api.example.com/v1/me
curl -i -H "Authorization: Bearer <token>" https://api.example.com/v1/me
kubectl logs deploy/api-gateway
```

중요한 관찰 포인트:

- 401, 403, 429 비율
- auth latency
- rate limit hit ratio
- 특정 사용자나 IP에 편중되는지

### 토큰 캐시 감각

```text
검증 비용이 큰 auth는 짧게 캐시하고,
권한이 자주 바뀌는 구간은 캐시를 짧게 둔다.
```

캐시를 길게 두면 성능은 좋아지지만, 권한 회수 반영이 늦어진다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 인증 먼저, rate limit 나중 | 사용자별 정책이 명확하다 | 익명 트래픽 차단이 늦을 수 있다 | 로그인 기반 API |
| rate limit 먼저, 인증 나중 | 공격 트래픽을 빨리 줄인다 | 사용자별 정확도가 낮다 | 공개 API |
| 원격 auth introspection | 중앙 정책 관리가 쉽다 | 지연과 병목이 생긴다 | 보안 중심 시스템 |
| 로컬 JWT 검증 | 빠르고 독립적이다 | 키 회전과 폐기 처리가 필요하다 | 일반적인 게이트웨이 |

핵심은 "기능을 붙이는 것"이 아니라 **어떤 실패를 먼저 차단할지 정하는 것**이다.

---

## 면접에서 자주 나오는 질문

### Q. 인증과 인가는 무엇이 다른가요?

- 인증은 누구인지 확인하는 것이고, 인가는 그 사용자가 무엇을 할 수 있는지 확인하는 것이다.

### Q. rate limit은 왜 게이트웨이에 두나요?

- 백엔드로 들어가기 전에 트래픽을 제어해 비용과 장애 확산을 줄이기 위해서다.

### Q. 왜 401, 403, 429를 구분하나요?

- 실패 이유가 다르기 때문이다. 인증 실패, 권한 부족, 요청 제한 초과를 구분해야 클라이언트와 운영이 올바르게 대응할 수 있다.

### Q. rate limit을 인증보다 먼저 두면 안 되나요?

- 가능은 하지만, 사용자별 quota가 필요한 경우엔 부정확해진다. 공개 API처럼 익명 트래픽 방어가 중요한 경우에 더 적합하다.

---

## 한 줄 정리

API Gateway의 auth와 rate limit은 개별 기능이 아니라, **검증 순서와 실패 응답까지 설계해야 하는 운영 체인**이다.
