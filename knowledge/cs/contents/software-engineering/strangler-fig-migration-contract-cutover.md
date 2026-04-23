# Strangler Fig Migration, Contract, Cutover

> 한 줄 요약: 레거시를 한 번에 갈아엎지 말고, 기존 시스템을 감싸듯이 점진적으로 잘라내면서 계약과 롤백 경로를 유지해야 안전하게 전환할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Monolith to MSA Failure Patterns](./monolith-to-msa-failure-patterns.md)
> - [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)
> - [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)
> - [Migration Wave Governance and Decision Rights](./migration-wave-governance-decision-rights.md)
> - [CDC, Debezium, Outbox, Binlog](../database/cdc-debezium-outbox-binlog.md)
> - [Workflow Orchestration + Saga 설계](../system-design/workflow-orchestration-saga-design.md)

> retrieval-anchor-keywords:
> - strangler fig
> - cutover
> - dual write
> - shadow traffic
> - canary
> - contract testing
> - rollback
> - migration

---

## 핵심 개념

Strangler Fig 패턴은 레거시 시스템을 한 번에 대체하지 않고, 새 시스템이 기존 기능을 둘러싸며 점점 더 많은 트래픽과 책임을 가져가게 만드는 전환 방식이다.

중요한 점은 "새 시스템을 만든다"가 아니라 **기존 시스템을 안전하게 줄여 나간다**는 것이다. 이 방식이 필요한 이유는 명확하다.

- 레거시는 기능은 많지만 변경 리스크가 크다
- 빅뱅 교체는 실패하면 전체가 같이 무너진다
- 데이터, API, 배치, 운영 도구가 동시에 얽혀 있어 단순 리라이트가 불가능한 경우가 많다

즉 이 주제의 핵심은 코드 재작성보다 **cutover 설계**다.

---

## 깊이 들어가기

### 1. Strangler Fig는 "대체"가 아니라 "우회와 흡수"다

좋은 전환은 새 시스템이 바로 모든 책임을 가지지 않는다.

처음에는 한두 개의 엔드포인트만 새 시스템으로 보낸다.
그다음 읽기 경로를 옮기고, 마지막에 쓰기 경로를 옮긴다.

전형적인 순서는 다음과 같다.

```text
Client -> Gateway/Router -> New Service -> Legacy Service
                         -> Legacy Service (fallback)
```

핵심은 라우팅 레이어를 두고, 기능 단위로 하나씩 잘라내는 것이다.

### 2. cutover는 스위치가 아니라 상태 전이다

cutover를 "트래픽 100% 전환"으로만 생각하면 위험하다.
여러 consumer와 배치가 얽히면 cutover는 보통 migration wave governance의 마지막 단계 중 하나가 된다.

실제 cutover에는 보통 아래가 포함된다.

- 라우팅 비율 조정
- 데이터 쓰기 경로 전환
- 읽기 경로 전환
- 캐시 무효화
- 배치/정산/후처리 전환
- 롤백 시 역전 경로 확인

즉 cutover는 배포 이벤트가 아니라 **운영 상태를 바꾸는 과정**이다.

### 3. dual write는 가장 위험한 전환 단계다

레거시와 신규에 동시에 쓰는 dual write는 매우 매력적이지만, 정합성 문제를 쉽게 만든다.

예를 들면:

1. 신규 DB 저장 성공
2. 레거시 DB 저장 실패
3. 두 시스템의 상태가 달라짐

이 문제를 줄이려면 다음 중 하나가 필요하다.

- outbox + CDC로 단일 쓰기 후 비동기 복제
- write-through adapter로 실패를 명확히 처리
- 보상 작업과 재처리 도구

아무 장치 없이 "둘 다 써요"는 전환이 아니라 **정합성 빚**을 쌓는 일이다.

### 4. shadow traffic은 읽기 전 검증 도구다

shadow traffic은 실제 사용자 요청을 신규 시스템에도 보내되, 응답은 사용자에게 돌려주지 않는 방식이다.

이 방식의 장점:

- 실제 요청 패턴을 검증할 수 있다
- 운영 데이터를 기반으로 성능과 오류를 볼 수 있다
- 사용자 영향 없이 새 로직을 관찰할 수 있다

주의할 점:

- 개인정보와 민감 데이터 마스킹이 필요하다
- 부작용이 있는 요청은 그대로 복제하면 안 된다
- 외부 결제, 메일 발송 같은 side effect는 반드시 차단해야 한다

### 5. contract testing이 없으면 cutover는 도박이 된다

레거시와 신규가 공존하는 동안에는 API 의미가 조금만 달라져도 깨진다.

예:

- 필드명이 바뀜
- enum 값이 달라짐
- null 허용 규칙이 달라짐
- pagination 정렬이 달라짐

그래서 소비자-제공자 계약 테스트가 필요하다.

계약 테스트는 "응답이 온다"를 넘어서, **전환 중에도 소비자가 기대하는 의미가 유지되는지** 확인한다.

이 부분은 [API Contract Testing, Consumer-Driven](./api-contract-testing-consumer-driven.md)과 직접 연결된다.

### 6. rollback은 코드 되돌리기보다 경로 되돌리기다

전환이 잘 설계되면 rollback은 대개 다음 순서로 간다.

1. 라우터를 레거시로 되돌린다
2. 신규 write를 끊는다
3. 신규 read를 끊는다
4. 동기화 잡과 CDC를 중지한다
5. 필요하면 데이터 보정/재처리를 실행한다

중요한 건, rollback이 가능하려면 전환 중에도 레거시가 살아 있어야 한다는 점이다.

즉 괜찮은 migration은 "새 시스템을 빨리 세우는 것"이 아니라 **되돌릴 수 있게 세우는 것**이다.

---

## 실전 시나리오

### 시나리오 1: 주문 조회부터 먼저 옮긴다

가장 안전한 출발점은 읽기 전환이다.

- 주문 생성은 레거시에 둔다
- 주문 조회만 신규 서비스로 보낸다
- shadow traffic으로 응답 차이를 비교한다
- 계약 테스트로 필드 호환성을 고정한다

이때 읽기 전환은 사용자 영향이 적고, 실패 시 즉시 원복하기 쉽다.

### 시나리오 2: write는 outbox로 천천히 옮긴다

주문 생성이 레거시에 남아 있다면, 이벤트만 신규로 복제할 수 있다.

```sql
INSERT INTO orders(id, status) VALUES (1001, 'CREATED');
INSERT INTO outbox(id, aggregate_id, event_type, payload, created_at)
VALUES (9001, 1001, 'ORDER_CREATED', '{...}', NOW());
```

그다음 CDC나 worker가 신규 저장소에 반영한다.
이렇게 하면 dual write를 직접 하지 않고도 데이터 흐름을 분리할 수 있다.

### 시나리오 3: canary cutover로 일부 사용자만 먼저 보낸다

새 주문 상세 페이지를 5% 트래픽에만 노출한다.

```text
if (request.path == "/orders/{id}") {
  route 5% -> new-service
  route 95% -> legacy
}
```

관찰할 것:

- 5xx 비율
- p95 응답 시간
- 필드 누락 비율
- 재시도 증가

이 방식은 [Deployment Rollout, Rollback, Canary, Blue-Green](./deployment-rollout-rollback-canary-blue-green.md)과 같은 운영 전략을 migration에 적용한 예다.

### 시나리오 4: workflow는 새 시스템에서, 실행은 점진적으로

레거시에서 주문 처리 순서가 복잡했다면, 신규 시스템에 Saga 오케스트레이터를 두고 한 단계씩 책임을 옮길 수 있다.

- 주문 접수는 신규
- 결제 승인만 레거시
- 재고 예약은 신규
- 알림은 신규

이런 방식은 기능 단위 cutover를 가능하게 하지만, 각 단계의 보상과 상태 추적이 필요하다.

---

## 코드로 보기

### 1. 라우팅 기반 strangler

```pseudo
if featureFlag("new_order_detail") and request.user in canaryGroup:
    response = newOrderService.handle(request)
    shadowCompare(response, legacyOrderService.handle(request))
else:
    response = legacyOrderService.handle(request)
return response
```

이 패턴의 포인트는 신규 시스템이 먼저 응답을 내고, 레거시는 비교용으로만 쓰는 단계까지 갈 수 있다는 것이다.

### 2. dual write 대신 outbox 기반 전환

```java
@Transactional
public void placeOrder(CreateOrderCommand command) {
    Order order = orderRepository.save(command.toOrder());
    outboxRepository.save(new OutboxEvent(
        order.getId(),
        "ORDER_CREATED",
        jsonSerializer.serialize(order)
    ));
}
```

이후 CDC worker가 신규 시스템에 반영한다.
이렇게 하면 하나의 로컬 트랜잭션으로 저장과 이벤트 기록을 묶을 수 있다.

### 3. 계약 테스트로 전환 전 호환성 확인

```java
assertThat(response.body())
    .containsKey("id")
    .containsKey("status")
    .containsKey("totalAmount");
```

전환 중에는 "필드가 있느냐"보다 "소비자가 의존하는 의미가 깨지지 않았느냐"가 더 중요하다.

### 4. cutover 체크리스트 예시

```bash
./verify-contracts.sh
./run-shadow-compare.sh --sample-rate 0.1
./switch-route.sh --target new --percent 5
./monitor-metrics.sh --window 30m
./switch-route.sh --target new --percent 100
```

이런 식으로 전환 절차를 스크립트화하면, 사람의 기억 대신 반복 가능한 운영 절차가 된다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| 빅뱅 교체 | 빠르게 끝난다 | 실패 비용이 크다 | 매우 작고 단순한 시스템 |
| strangler fig | 실패 범위를 줄인다 | 오래 걸릴 수 있다 | 레거시가 크고 위험할 때 |
| dual write | 전환이 빨라 보인다 | 정합성 관리가 어렵다 | 임시로만, 통제된 구간에서 |
| shadow traffic | 실제 트래픽으로 검증 가능 | 부작용 차단이 필요하다 | 읽기/응답 검증 단계 |
| canary cutover | 일부만 먼저 보낸다 | 관측 체계가 필요하다 | 사용자 영향이 큰 전환 |
| contract testing | 호환성 깨짐을 빨리 잡는다 | 유지비가 든다 | 소비자 API가 많은 조직 |

핵심은 "가장 멋진 방법"이 아니라 **되돌릴 수 있고 관찰 가능한 방법**을 고르는 것이다.

---

## 꼬리질문

> Q: Strangler Fig와 빅뱅 리라이트의 가장 큰 차이는 무엇인가요?
> 의도: 전환 전략의 실패 비용을 이해하는지 확인
> 핵심: 빅뱅은 한 번에 모두 바꾸고, strangler fig는 경계와 트래픽을 단계적으로 옮긴다.

> Q: dual write를 왜 위험하다고 보나요?
> 의도: 정합성 분리를 아는지 확인
> 핵심: 두 저장소의 성공/실패가 어긋나기 쉬워서, 중간 불일치와 재처리 문제가 생긴다.

> Q: shadow traffic은 왜 유용한가요?
> 의도: 실제 운영 검증과 부작용 차단을 구분하는지 확인
> 핵심: 사용자 영향 없이 실제 요청 패턴으로 새 시스템을 검증할 수 있다.

> Q: contract testing이 migration에서 중요한 이유는 무엇인가요?
> 의도: API 의미 호환성을 보는지 확인
> 핵심: 전환 중에는 응답 형태의 미세한 변화도 downstream을 깨뜨릴 수 있기 때문이다.

> Q: rollback을 쉽게 하려면 무엇을 먼저 설계해야 하나요?
> 의도: 되돌림을 배포 후가 아니라 설계 단계로 보는지 확인
> 핵심: 라우팅 전환점, 데이터 복제 경로, 보정 절차, feature flag를 먼저 준비해야 한다.

## 한 줄 정리

Strangler Fig migration은 레거시를 한 번에 교체하는 대신, contract testing과 canary, shadow traffic, rollback 경로를 활용해 기능과 데이터를 점진적으로 신규 시스템으로 옮기는 전환 전략이다.
