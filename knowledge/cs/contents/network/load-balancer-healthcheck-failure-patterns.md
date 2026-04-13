# Load Balancer 헬스체크 실패 패턴

> 한 줄 요약: 헬스체크는 죽은 서버를 거르는 장치지만, 너무 단순하거나 너무 공격적으로 만들면 오히려 장애를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Service Mesh, Sidecar Proxy](./service-mesh-sidecar-proxy.md)
> - [System Design](../system-design/README.md)

---

## 핵심 개념

Load balancer의 헬스체크는 "이 서버에게 트래픽을 보내도 되는가"를 판단하는 장치다.

하지만 "프로세스가 살아 있다"와 "서비스가 건강하다"는 다르다.

헬스체크가 너무 약하면:

- 죽은 서버로 트래픽이 간다
- 장애 복구가 느려진다

헬스체크가 너무 강하면:

- 잠깐 느린 서버를 죽은 것으로 오인한다
- 플래핑(flapping)이 생긴다
- 정상 서버가 필요 이상으로 배제된다

---

## 깊이 들어가기

### 1. active vs passive

- `active health check`: LB가 주기적으로 직접 확인한다
- `passive health check`: 실제 트래픽 실패율을 보고 판단한다

대부분은 둘을 섞는다.

### 2. 무엇을 확인할 것인가

헬스체크는 계층에 따라 다르다.

- TCP check: 포트가 열려 있는지
- HTTP check: `/health`가 200을 주는지
- gRPC check: 서비스 상태 메시지를 주는지

문제는 `200 OK`가 곧 서비스 정상은 아니라는 점이다.

### 3. readiness와 liveness

Kubernetes나 LB에서 흔히 헷갈리는 지점이다.

- `liveness`: 프로세스가 죽었으면 재시작해도 되는가
- `readiness`: 지금 트래픽을 받아도 되는가

초기화 중인 앱을 liveness만 보고 통과시키면, 아직 준비되지 않은 서버로 트래픽이 간다.

### 4. false positive / false negative

false positive:

- 잠깐의 GC pause
- cold start
- 외부 DB 지연
- 순간적인 네트워크 흔들림

false negative:

- `/health`가 DB를 안 보고 있다
- 실제 비즈니스 기능은 죽었는데 health endpoint만 살아 있다
- dependency 하나가 망가졌지만 종합 상태를 못 본다

### 5. grace period와 slow start

새로 올라온 서버는 바로 풀 트래픽을 받지 말아야 한다.

- warmup 시간 필요
- 캐시 채움 필요
- connection pool 초기화 필요

이때 slow start 없이 바로 넣으면 배포 직후 장애처럼 보인다.

---

## 실전 시나리오

### 시나리오 1: 배포 직후 502가 튄다

원인:

- readiness가 너무 빨리 true가 됨
- 실제 초기화가 끝나지 않음
- LB가 새 서버로 트래픽을 보냄

### 시나리오 2: 헬스체크가 너무 자주 죽는다고 판단한다

원인 후보:

- timeout이 짧음
- timeout과 retry를 헬스체크에 잘못 섞음
- GC pause를 장애로 오인

### 시나리오 3: DB가 느려져서 앱이 죽은 것으로 보인다

health endpoint가 DB를 직접 확인하면, DB 지연이 곧바로 LB에서 서버 제외로 이어질 수 있다.

이게 항상 좋은 건 아니다.

- 일부 기능만 느릴 수 있다
- 전체 서버를 빼면 오히려 용량이 부족해질 수 있다

---

## 코드로 보기

### Kubernetes readiness/liveness 예시

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Nginx upstream 예시 감각

```nginx
upstream app {
    server 10.0.0.1 max_fails=3 fail_timeout=10s;
    server 10.0.0.2 max_fails=3 fail_timeout=10s;
}
```

### 운영 체크 명령

```bash
kubectl describe pod order-service
kubectl get endpoints
kubectl logs deploy/order-service
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 단순 TCP health check | 빠르고 단순하다 | 앱 수준 장애를 못 본다 | 기본적인 포트 생존 확인 |
| HTTP health check | 앱 상태를 더 잘 본다 | health endpoint 설계가 필요하다 | 일반적인 웹 서비스 |
| readiness/liveness 분리 | 운영 의도가 선명하다 | 설정이 늘어난다 | Kubernetes 기반 |
| dependency-aware health check | 실제 서비스 상태에 가깝다 | 외부 장애가 서비스 전체를 배제할 수 있다 | 신중하게 사용할 때 |

핵심은 헬스체크가 **진실한 상태의 일부만** 보여준다는 점이다.

---

## 꼬리질문

> Q: readiness와 liveness는 왜 나누나요?
> 의도: 배포 시점과 재시작 시점의 의미를 구분하는지 확인
> 핵심: 준비되지 않은 서버와 죽은 서버는 다르다

> Q: health check가 너무 강하면 왜 문제인가요?
> 의도: false negative가 운영에 미치는 영향을 아는지 확인
> 핵심: 잠깐 느린 서버를 잘못 제거하면 전체 용량이 줄어든다

## 한 줄 정리

헬스체크는 죽은 서버를 거르는 필터가 아니라, 준비 상태와 생존 상태를 분리해서 판단하는 운영 장치다.
