# HikariCP 튜닝

> 한 줄 요약: HikariCP는 크게 잡는다고 빨라지지 않는다. DB 용량, 트랜잭션 길이, 커넥션 점유 시간을 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
> - [쿼리 튜닝 체크리스트](./query-tuning-checklist.md)
> - [느린 쿼리 분석 플레이북](./slow-query-analysis-playbook.md)
> - [Spring Bean 생명주기와 스코프 함정](../spring/spring-bean-lifecycle-scope-traps.md)

---

## 핵심 개념

HikariCP는 Java/Spring 백엔드에서 가장 흔한 DB connection pool이다. 핵심은 단순하다.

1. 커넥션 생성 비용을 줄인다
2. DB 연결 수를 통제한다
3. 커넥션을 오래 잡고 있는 병목을 드러낸다

많은 팀이 `maximumPoolSize`만 크게 조정하고 끝내는데, 그건 절반만 보는 것이다. 실제 병목은 트랜잭션 길이, 쿼리 시간, 외부 I/O, DB max connection 수와 같이 봐야 한다.

---

## 깊이 들어가기

### 1. 풀 크기는 DB와 함께 정한다

대략적인 출발점은 이런 사고다.

```text
app instance 수 x pool size <= DB가 감당 가능한 연결 수
```

여기서 중요한 것은 애플리케이션 인스턴스가 여러 개라는 점이다.

- instance 1개당 30 connection
- instance 8개면 240 connection

이렇게 쌓이면 DB `max_connections`를 쉽게 넘긴다.

### 2. 중요한 설정은 최대 크기만이 아니다

자주 보는 설정:

- `maximumPoolSize`
- `minimumIdle`
- `connectionTimeout`
- `idleTimeout`
- `maxLifetime`
- `leakDetectionThreshold`
- `keepaliveTime`

각 설정은 다른 문제를 푼다.

- `maximumPoolSize`: 동시 커넥션 상한
- `connectionTimeout`: 대기할 수 있는 최대 시간
- `maxLifetime`: 오래된 커넥션 교체
- `leakDetectionThreshold`: 커넥션 반환 누락 탐지

### 3. 커넥션은 오래 쥐고 있을수록 위험하다

다음 코드는 흔한 실수다.

```java
@Transactional
public void placeOrder() {
    orderRepository.save(order);
    paymentClient.pay(order); // 외부 호출
    shippingClient.reserve(order);
}
```

이 패턴은 DB 커넥션을 잡은 채 네트워크를 기다릴 수 있다. 그러면 쿼리가 느린 게 아니라, 커넥션이 묶이는 것이다.

### 4. HikariCP는 문제를 숨기기보다 드러낸다

풀 크기를 무작정 키우면 대기열은 잠깐 줄 수 있지만, DB가 버티지 못하면 전체 지연이 더 커진다.

즉 HikariCP는 다음을 보여준다.

- 요청이 커넥션을 얼마나 오래 잡는가
- DB가 실제로 처리 가능한 동시성이 얼마인가
- 긴 트랜잭션이 있는가

---

## 실전 시나리오

### 시나리오 1: `Connection is not available` 폭증

증상:

- 로그에 `Connection is not available, request timed out after ...`가 찍힘
- 앱 CPU는 낮은데 요청이 밀림
- DB는 바쁘지 않아 보여도 풀은 고갈됨

원인:

- 긴 트랜잭션
- 외부 API 호출을 DB 트랜잭션 안에 넣음
- 배치 작업이 너무 많은 커넥션을 점유함

대응:

- 트랜잭션 범위를 줄인다
- 외부 호출을 트랜잭션 밖으로 뺀다
- batch size를 조절한다
- Hikari metrics와 DB process list를 같이 본다

### 시나리오 2: 풀을 늘렸는데 더 느려짐

풀을 20에서 80으로 키웠더니 잠깐 좋아졌다가 전체 p99가 더 나빠질 수 있다. 이유는 DB 자체의 동시성 처리 능력을 넘어서기 때문이다.

교훈:

- 풀은 큐잉 지연을 숨길 수 있지만, 병목을 없애지 못한다
- DB가 한 번에 처리할 수 있는 작업 수는 무한하지 않다

### 시나리오 3: leak detection이 진짜 누수를 잡아냄

테스트 환경에서 `leakDetectionThreshold`를 낮춰두면 반환하지 않은 커넥션을 빨리 찾을 수 있다.

하지만 너무 낮으면 정상적인 긴 쿼리도 누수처럼 보일 수 있다.

---

## 코드로 보기

### Spring Boot 설정 예시

```yaml
spring:
  datasource:
    url: jdbc:mysql://db.example.com:3306/app
    username: app
    password: secret
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 3000
      idle-timeout: 600000
      max-lifetime: 1800000
      leak-detection-threshold: 2000
      keepalive-time: 300000
```

### 풀 크기 감각

```text
적정 pool size ≈ (DB가 처리 가능한 동시 작업 수) - (안전 여유)
```

정확한 숫자보다 중요한 것은, 여러 인스턴스와 배치 작업을 합산해서 보는 것이다.

### 트랜잭션 외부 호출 분리 예시

```java
@Transactional
public void placeOrder(OrderCommand command) {
    Order order = orderRepository.save(Order.from(command));
    outboxService.publishOrderCreated(order.getId());
}

public void sendPayment(Order order) {
    paymentClient.pay(order); // DB 트랜잭션 밖
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| 큰 pool | 순간 처리량이 늘어날 수 있다 | DB/락/스케줄링 비용이 커질 수 있다 | DB가 여유 있을 때만 |
| 작은 pool | DB를 보호한다 | 대기열이 커질 수 있다 | 안정성이 더 중요할 때 |
| 짧은 connectionTimeout | 장애를 빨리 드러낸다 | 일시적 burst에 민감하다 | SLA가 명확할 때 |
| leak detection 활성화 | 반환 누락을 빨리 찾는다 | 긴 쿼리와 혼동될 수 있다 | 테스트/스테이징 |
| keepalive 조정 | 유휴 커넥션 끊김을 줄인다 | 과하면 불필요한 트래픽이 늘어난다 | 네트워크가 불안정할 때 |

핵심은 풀 튜닝이 아니라 **점유 시간 튜닝**이다.

---

## 꼬리질문

> Q: pool size를 무작정 크게 하면 안 되는 이유는 뭔가요?
> 의도: 연결 수와 DB 처리량의 관계 이해 여부 확인
> 핵심: 풀은 대기열을 줄일 수 있지만 DB의 처리 한계를 넘기면 더 느려진다

> Q: HikariCP 설정 중 가장 먼저 봐야 하는 것은 무엇인가요?
> 의도: 단일 파라미터 집착 여부 확인
> 핵심: maximumPoolSize보다 커넥션 점유 시간과 트랜잭션 경계를 먼저 본다

> Q: leak detection은 왜 운영에 그대로 켜두기 어려운가요?
> 의도: 운영 비용 인식 확인
> 핵심: 긴 쿼리/배치가 누수처럼 오탐될 수 있다

---

## 한 줄 정리

HikariCP는 커넥션 수를 늘리는 도구가 아니라, DB 연결 점유를 통제해서 병목을 드러내는 도구다.
