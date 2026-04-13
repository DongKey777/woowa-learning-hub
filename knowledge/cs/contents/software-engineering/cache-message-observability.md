# 캐시, 메시징, 관측성 🟡 Intermediate

> 시스템이 커지면 CRUD만으로 설명이 안 된다 -- 캐시는 성능, 메시징은 결합도, 관측성은 생존의 문제다.

## 핵심 개념

백엔드 시스템이 성장하면 세 가지 축이 필수가 된다.

- **캐시**: 비싼 계산이나 조회 결과를 재사용해 응답 속도를 높인다
- **메시징**: 직접 호출 대신 메시지로 작업을 전달해 결합도를 낮춘다
- **관측성**: 시스템 내부 상태를 외부에서 이해할 수 있게 만든다

세 가지 모두 "없어도 동작하지만, 없으면 운영할 수 없는" 영역이다.

## 깊이 들어가기

### 캐시

#### 캐시 전략

| 전략 | 읽기 | 쓰기 | 적합한 상황 |
|------|------|------|------------|
| Cache-Aside (Lazy) | 캐시 미스 시 DB 조회 후 캐시 적재 | 쓰기 시 DB만 갱신, 캐시 무효화 | 읽기 빈도 높고 쓰기 적은 경우 |
| Read-Through | 캐시가 DB를 대신 조회 | - | 캐시 라이브러리가 지원할 때 |
| Write-Through | - | 쓰기 시 캐시와 DB 동시 갱신 | 쓰기 후 즉시 읽기가 많을 때 |
| Write-Behind | - | 쓰기를 캐시에만, 비동기로 DB 반영 | 쓰기 성능이 중요할 때 (데이터 유실 위험) |

#### 캐시 무효화: 가장 어려운 문제

```
"컴퓨터 과학에서 어려운 문제는 두 가지다: 캐시 무효화와 이름 짓기."
-- Phil Karlton
```

실무에서 흔한 무효화 실수:

1. **TTL만 설정하고 끝**: 데이터 변경 후 TTL 만료 전까지 오래된 값을 반환
2. **쓰기 시 삭제만**: 동시 요청이 들어오면 stale 값이 다시 캐싱됨 (race condition)
3. **모든 것을 캐싱**: 거의 안 읽히는 데이터까지 캐싱하면 메모리만 낭비

#### 캐시를 어디에 둘 것인가

```
[클라이언트] → HTTP 캐시 (Cache-Control)
     ↓
[CDN/리버스 프록시] → 정적 리소스, 공개 API 응답
     ↓
[애플리케이션] → Local Cache (HashMap, Caffeine)
     ↓
[분산 캐시] → Redis, Memcached
     ↓
[DB 캐시] → Query Cache, Buffer Pool
```

**Local Cache vs 분산 Cache**:
- Local: 빠르지만 인스턴스 간 불일치 가능
- 분산: 일관성 확보 쉬우나 네트워크 비용 발생

### 메시징

#### 동기 호출 vs 비동기 메시징

```java
// 동기: 주문 서비스가 알림 서비스를 직접 호출
public void placeOrder(Order order) {
    orderRepository.save(order);
    notificationService.sendOrderConfirm(order);  // 알림 실패 → 주문도 실패?
}

// 비동기: 이벤트를 발행하고 끝
public void placeOrder(Order order) {
    orderRepository.save(order);
    eventPublisher.publish(new OrderPlaced(order.getId()));  // 알림은 구독자가 알아서
}
```

동기 호출의 문제:
- 알림 서비스 장애가 주문 서비스 장애로 전파
- 후속 처리가 추가될 때마다 `placeOrder`를 수정해야 함

#### 메시징에서 반드시 고려할 것

| 문제 | 설명 | 대응 |
|------|------|------|
| 메시지 유실 | 브로커 장애, 네트워크 단절 | Outbox 패턴, at-least-once 보장 |
| 중복 수신 | 재전송, ack 실패 | 멱등성 처리, Inbox 패턴 |
| 순서 역전 | 파티션, 재시도로 순서 꼬임 | 이벤트 내 시간 정보, 순서 무관한 설계 |
| 포이즌 메시지 | 처리 불가한 메시지가 반복 재시도 | Dead Letter Queue |

#### At-least-once vs At-most-once vs Exactly-once

- **At-most-once**: 유실 가능, 중복 없음 (fire-and-forget)
- **At-least-once**: 유실 없음, 중복 가능 (가장 흔한 선택)
- **Exactly-once**: 이론적 이상, 실무에서는 "at-least-once + 멱등성"으로 근사

### 관측성 (Observability)

관측성은 "로그를 많이 남기는 것"이 아니다. **시스템 내부 상태를 외부에서 추론할 수 있는 능력**이다.

#### 세 기둥 (Three Pillars)

| 기둥 | 목적 | 예시 | 강점 |
|------|------|------|------|
| Logs | 특정 이벤트의 상세 기록 | "주문 123 결제 실패: 잔액 부족" | 디버깅, 감사 추적 |
| Metrics | 집계된 수치 | 초당 요청 수, p99 응답 시간, 에러율 | 트렌드 파악, 알림 기준 |
| Traces | 요청의 전체 경로 추적 | 주문→결제→재고→알림 호출 체인 | 병목 지점 발견, 분산 시스템 디버깅 |

#### 로그를 "잘" 남기는 것

```java
// 나쁜 로그: 맥락 없음
log.error("에러 발생");

// 나쁜 로그: 너무 많은 정보 (개인정보 포함)
log.error("사용자 " + user.getEmail() + "의 카드번호 " + card.getNumber() + " 결제 실패");

// 좋은 로그: 구조화, 맥락 있음, 민감정보 제외
log.error("Payment failed. orderId={}, userId={}, reason={}, amount={}",
          order.getId(), user.getId(), e.getErrorCode(), order.getAmount());
```

**구조화 로그 (Structured Logging)**:
- JSON 형태로 남기면 검색/필터가 쉬워진다
- `traceId`를 포함하면 분산 시스템에서 요청 추적이 가능하다

## 실전 시나리오

### 시나리오: 상품 상세 조회 캐싱

```
1. 사용자가 상품 상세 페이지 요청
2. Redis에서 먼저 조회 (Cache-Aside)
3. 캐시 미스 → DB 조회 → Redis에 적재 (TTL 5분)
4. 상품 정보 수정 시 → 해당 캐시 키 삭제
5. 다음 조회 시 DB에서 새로 읽어 캐싱
```

**문제**: 인기 상품의 캐시가 만료되는 순간 수백 요청이 동시에 DB를 때린다 (Cache Stampede)

**대응**:
- 캐시 갱신 시 분산 락 사용 (한 요청만 DB 조회)
- TTL에 랜덤 오프셋 추가 (일괄 만료 방지)
- 백그라운드 갱신 (캐시 만료 전에 미리 갱신)

## 코드로 보기

### Cache-Aside 패턴 구현

```java
@Service
public class ProductService {

    private final ProductRepository productRepository;
    private final RedisTemplate<String, Product> redisTemplate;

    public Product findById(Long id) {
        String key = "product:" + id;

        // 1. 캐시에서 조회
        Product cached = redisTemplate.opsForValue().get(key);
        if (cached != null) {
            return cached;
        }

        // 2. DB에서 조회
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));

        // 3. 캐시에 적재
        redisTemplate.opsForValue().set(key, product, Duration.ofMinutes(5));

        return product;
    }

    public void update(Long id, ProductUpdateRequest request) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));
        product.update(request);
        productRepository.save(product);

        // 4. 캐시 무효화 (갱신이 아니라 삭제)
        redisTemplate.delete("product:" + id);
    }
}
```

### 메트릭 기반 알림 설정 예시

```yaml
# Prometheus alert rule
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "5xx 에러율이 5%를 초과함"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 응답시간이 3초를 초과함"
```

## 트레이드오프

| 선택 | 장점 | 단점 |
|------|------|------|
| 공격적 캐싱 | 응답 빠름, DB 부하 감소 | 최신성 약화, 메모리 비용 |
| 보수적 캐싱 | 최신 데이터 보장 | 느린 응답, DB 부하 |
| 동기 호출 | 즉시 일관성, 디버깅 쉬움 | 결합도 높음, 장애 전파 |
| 비동기 메시징 | 결합도 낮음, 확장 쉬움 | 최종 일관성, 디버깅 어려움 |
| 로그 많이 | 디버깅 정보 풍부 | 저장 비용, 노이즈, 성능 영향 |
| 로그 적게 | 비용 절감, 핵심만 | 장애 시 정보 부족 |

## 꼬리질문

- 캐시 히트율이 낮은데 캐시를 유지해야 하는 경우는 언제인가?
- 메시징을 쓰면 트랜잭션 일관성을 어떻게 보장하는가? (Outbox 참고)
- 메트릭과 로그 중 장애 대응에서 먼저 보는 것은?
- 분산 트레이싱 없이 MSA를 디버깅할 수 있는가?
- 캐시 워밍업은 언제, 어떻게 해야 하는가?

## 한 줄 정리

캐시는 "빠르게"가 아니라 일관성과의 거래이고, 메시징은 "비동기"가 아니라 결합도와의 거래이며, 관측성은 "로그"가 아니라 장애 시 살아남는 능력이다.
