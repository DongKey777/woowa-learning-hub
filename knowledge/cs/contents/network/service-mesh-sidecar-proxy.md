---
schema_version: 3
title: "Service Mesh, Sidecar Proxy"
concept_id: network/service-mesh-sidecar-proxy
canonical: true
category: network
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- service-mesh
- sidecar-proxy
- platform-networking
aliases:
- service mesh
- sidecar proxy
- Envoy sidecar
- mTLS mesh
- traffic policy
- mesh observability
- service-to-service proxy
symptoms:
- sidecar를 app 내부 코드처럼 보고 local reply, timeout, retry 정책을 app 책임으로 오해한다
- mTLS, retry, circuit breaking, telemetry가 sidecar에서 처리되는 계층을 구분하지 못한다
- service mesh가 항상 성능과 안정성을 높인다고 보고 latency/operational overhead를 무시한다
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- network/api-gateway-reverse-proxy-operational-points
- network/proxy-local-reply-vs-upstream-error-attribution
next_docs:
- network/service-mesh-local-reply-timeout-reset-attribution
- network/mesh-adaptive-concurrency-local-reply-metrics-tuning
- network/mtls-handshake-failure-diagnosis
- security/service-to-service-auth-mtls-jwt-spiffe
linked_paths:
- contents/network/tls-loadbalancing-proxy.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/timeout-retry-backoff-practical.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
- contents/network/upstream-queueing-connection-pool-wait-tail-latency.md
- contents/network/service-mesh-local-reply-timeout-reset-attribution.md
- contents/network/adaptive-concurrency-limiter-latency-signal-gateway-mesh.md
- contents/spring/spring-security-architecture.md
confusable_with:
- network/api-gateway-reverse-proxy-operational-points
- network/service-mesh-local-reply-timeout-reset-attribution
- network/mesh-adaptive-concurrency-local-reply-metrics-tuning
- network/mtls-handshake-failure-diagnosis
forbidden_neighbors: []
expected_queries:
- "service mesh와 sidecar proxy는 무엇을 대신 처리해?"
- "Envoy sidecar local reply가 app 응답처럼 보일 수 있는 이유는?"
- "service mesh mTLS retry circuit breaker observability의 장단점은?"
- "sidecar proxy가 들어오면 timeout attribution이 왜 어려워져?"
- "service mesh는 API gateway나 reverse proxy와 어떻게 달라?"
contextual_chunk_prefix: |
  이 문서는 service mesh와 sidecar proxy가 service-to-service traffic,
  mTLS, retry, circuit breaking, telemetry, local reply를 처리하는 방식을 다루는
  advanced deep dive다.
---
# Service Mesh, Sidecar Proxy

> 한 줄 요약: 서비스 메시는 각 서비스 옆에 프록시를 붙여서, 통신 정책과 관측성을 애플리케이션 밖으로 분리하는 방식이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md)
> - [Adaptive Concurrency Limiter, Latency Signal, Gateway/Mesh](./adaptive-concurrency-limiter-latency-signal-gateway-mesh.md)
> - [Spring Security 아키텍처](../spring/spring-security-architecture.md)
> - [System Design](../system-design/README.md)

retrieval-anchor-keywords: service mesh, sidecar proxy, control plane, data plane, mTLS, traffic policy, local reply, retry policy, sidecar latency, observability

---

## 왜 중요한가

서비스 수가 늘어나면 통신 규칙도 함께 늘어난다.

- 서비스 간 인증
- mTLS
- retry / timeout / circuit breaker
- 트래픽 분기
- 관측성

이걸 애플리케이션 코드마다 직접 넣으면 규칙이 흩어진다.  
서비스 메시는 이 공통 통신 책임을 프록시 레이어로 옮긴다.

### Retrieval Anchors

- `service mesh`
- `sidecar proxy`
- `control plane`
- `data plane`
- `mTLS`
- `traffic policy`
- `local reply`
- `sidecar latency`

---

## 핵심 개념

### sidecar proxy

각 서비스 인스턴스 옆에 붙는 별도 프로세스다.

- 앱은 자기 로직만 신경 쓴다
- 네트워크 정책은 sidecar가 대신한다
- 서비스 간 호출은 보통 sidecar를 경유한다

### control plane / data plane

- `data plane`: 실제 패킷이 흐르는 경로
- `control plane`: 정책을 배포하고 라우팅 설정을 관리하는 경로

서비스 메시는 이 둘을 분리해서 운영한다.

### 무엇을 대신해 주나

- 서비스 간 TLS
- 인증서 관리
- retry / timeout / circuit breaker
- 트래픽 분할
- 지표 수집

즉 "앱이 네트워크 정책을 직접 구현하지 않게 하는 계층"이다.

---

## 깊이 들어가기

### 1. 왜 sidecar가 생겼나

마이크로서비스가 늘어나면 같은 문제가 반복된다.

- 서비스 A에서 B로 갈 때 매번 인증을 넣어야 한다
- 장애 감지를 매번 넣어야 한다
- 트래픽 전환을 코드 배포로만 하기 어렵다

Sidecar는 이 반복을 줄인다.

### 2. traffic policy를 밖으로 뺀다

예를 들면 이런 정책을 애플리케이션이 아니라 프록시가 담당할 수 있다.

```text
5% canary -> 20% -> 50% -> 100%
timeout 300ms
retry 2회
destination subset = v2
```

이렇게 하면 코드 변경 없이 라우팅을 조정할 수 있다.

### 3. mTLS와 서비스 간 신뢰

서비스 메시는 흔히 서비스 간 상호 인증을 위해 mTLS를 쓴다.

장점:

- 서비스 간 트래픽을 암호화한다
- 신원을 명시적으로 검증한다
- 네트워크 구간에서 가로채기가 어려워진다

이 부분은 [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)와 [Spring Security 아키텍처](../spring/spring-security-architecture.md)와 같이 봐야 한다.

### 4. 관측성

sidecar는 호출을 가로채기 때문에 다음을 쉽게 만든다.

- 분산 추적
- 성공률 / 지연 시간 지표
- 호출별 로그
- 서비스 간 상관관계 추적

즉 "문제가 생겼을 때 어디서 느려졌는가"를 보기 쉬워진다.

### 5. 제어 가능한 실패와 비싼 실패

서비스 메시는 실패를 숨겨 주는 도구가 아니다.

- 프록시가 죽으면 통신도 흔들릴 수 있다
- 설정이 꼬이면 모든 서비스에 영향을 준다
- 버전 불일치가 생기면 디버깅이 어려워진다

특히 sidecar가 만드는 local reply와 reset은 [Service Mesh Local Reply, Timeout, Reset Attribution](./service-mesh-local-reply-timeout-reset-attribution.md), [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)처럼 표면 증상 번역이 같이 있어야 해석이 빨라진다.

그래서 운영 복잡도가 확실히 올라간다.

---

## 실전 시나리오

### 시나리오 1: 점진적 롤아웃

새 버전이 조금 불안할 때 트래픽을 일부만 보내고 싶다.

- 1%만 v2로 보낸다
- 지표를 확인한다
- 10%, 50%, 100%로 올린다

이건 서비스 메시에 매우 잘 맞는다.

### 시나리오 2: 서비스 간 TLS를 일일이 넣기 힘들다

서비스가 많아질수록 각 서비스 팀이 개별 인증서를 관리하는 건 비효율적이다.

sidecar가 정책을 대신 처리하면 앱 코드는 덜 복잡해진다.

### 시나리오 3: retry가 폭주한다

모든 서비스가 자기 retry를 들고 있으면 장애 시 재시도가 겹친다.

이때 mesh에서 retry를 통제하면 정책을 한 군데서 조정할 수 있다.

하지만 잘못 설정하면 retry 폭풍을 중앙에서 더 강하게 만들 수도 있다.

---

## 코드로 보기

### Kubernetes sidecar 주입 예시

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  template:
    metadata:
      annotations:
        sidecar.istio.io/inject: "true"
    spec:
      containers:
        - name: app
          image: example/order-service:1.0.0
```

앱 컨테이너 옆에 프록시가 같이 붙는다는 감각만 잡으면 된다.

### 트래픽 분기 개념 예시

```text
destinationRule:
  stable: 95%
  canary: 5%
```

애플리케이션 코드 대신 정책으로 배포 비율을 조절할 수 있다.

### 운영 확인 명령

```bash
kubectl get pods
kubectl logs deploy/order-service -c istio-proxy
kubectl describe virtualservice order-service
```

문제는 대개 앱 로그만 보면 안 보이고, proxy 로그와 라우팅 정책을 같이 봐야 드러난다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 앱에 직접 구현 | 단순하고 명시적이다 | 서비스마다 중복된다 | 서비스 수가 적을 때 |
| 라이브러리 방식 | 언어 친화적이다 | 언어마다 중복될 수 있다 | 제한된 스택일 때 |
| sidecar mesh | 정책과 관측성을 분리한다 | 오버헤드와 복잡도가 크다 | 서비스 수가 많을 때 |
| gateway만 사용 | 경계가 단순하다 | 내부 서비스 간 정책이 약하다 | 외부 진입점 중심일 때 |

핵심 판단 기준은 이렇다.

- 서비스 수가 적으면 과하다
- 팀이 mesh 운영을 감당 못 하면 실패한다
- 통신 정책이 자주 바뀌면 유용하다

---

## 면접에서 자주 나오는 질문

### Q. 서비스 메시를 왜 쓰나요?

- 인증, retry, timeout, 관측성 같은 공통 통신 정책을 애플리케이션에서 분리하기 위해서다.

### Q. sidecar의 단점은?

- 호출 경로가 길어지고 운영 복잡도가 올라가며, 프록시 자체가 또 다른 장애 지점이 된다.

### Q. API gateway와 뭐가 다른가요?

- gateway는 보통 진입점 중심이고, service mesh는 서비스 간 내부 통신까지 넓게 다룬다.

### Q. 언제 쓰면 안 되나요?

- 서비스 수가 적고, 팀이 프록시/제어면 운영을 감당하기 어렵고, 정책 변경 빈도도 낮으면 과하다.

---

## 한 줄 정리

서비스 메시와 sidecar는 통신 정책을 앱 밖으로 빼서 일관성과 관측성을 높이지만, 그만큼 운영 복잡도와 장애 지점도 함께 늘린다.
