# Change Data Capture / Outbox Relay 설계

> 한 줄 요약: CDC와 outbox relay는 source of truth의 변경을 downstream으로 안전하게 흘려 보내기 위해 dual write를 끊고, 순서와 재처리 규칙을 명시하는 데이터 이동 파이프라인이다.
>
> 문서 역할: 이 문서는 migration / replay / cutover cluster 안에서 **데이터 이동과 relay 경계**를 맡는 deep dive다.

retrieval-anchor-keywords: change data capture, cdc, outbox relay, dual write, binlog tailing, outbox table, relay worker, ordering key, snapshot catchup, idempotent consumer, exactly-once illusion, single writer migration bridge, outbox watermark token, commit metadata consistency token, downstream read watermark

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
> - [Event Bus Control Plane 설계](./event-bus-control-plane-design.md)
> - [Search Indexing Pipeline 설계](./search-indexing-pipeline-design.md)
> - [Billing Usage Metering System 설계](./billing-usage-metering-system-design.md)
> - [Audit Log Pipeline 설계](./audit-log-pipeline-design.md)
> - [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Outbox Relay and Idempotent Publisher](../design-pattern/outbox-relay-idempotent-publisher.md)
> - [CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md)

## 이 문서 다음에 보면 좋은 설계

- outbox row의 commit metadata를 downstream read consistency token으로 넘기는 가장 단순한 입문 연결은 [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)에서 먼저 잡을 수 있다.
- bootstrap / 재처리 운영은 [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)로 이어진다.
- schema 호환성과 계약 phase는 [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)와 같이 보는 편이 좋다.
- dual-write 회피와 authority transfer는 [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)로 이어진다.

## 핵심 개념

많은 시스템이 "DB에 쓰고, 메시지 버스에도 publish"를 한 트랜잭션처럼 다루려다 망가진다.
실전에서 문제는 다음처럼 나타난다.

- DB write는 성공했는데 event publish는 실패
- 메시지는 나갔는데 DB commit은 롤백
- 재시도 과정에서 같은 변경이 여러 번 publish
- 대량 bootstrap이나 backfill 시 순서가 뒤섞임

CDC와 outbox relay의 목적은 이 dual write 위험을 줄이는 것이다.

- **CDC**는 로그 기반으로 source DB의 변경을 읽는다
- **Outbox relay**는 애플리케이션 트랜잭션 안에서 outbox row를 만들고, 별도 relay가 이를 발행한다

즉, 핵심은 "업무 write"와 "전파 delivery"를 분리하되, 나중에 다시 따라잡을 수 있게 만드는 것이다.

## 깊이 들어가기

### 1. 왜 dual write가 위험한가

예를 들어 주문 서비스가 `orders` 테이블에 insert하고, 바로 Kafka에 `OrderCreated`를 publish한다고 하자.
다음 네 가지 경우만 봐도 위험하다.

1. DB commit 성공, publish 실패
2. publish 성공, DB rollback
3. publish timeout 후 실제로는 성공, 그래서 중복 publish
4. 운영자가 수동 재처리하면서 순서를 깨뜨림

결국 문제는 "한 번의 비즈니스 상태 변경"을 여러 시스템에 동기적으로 복제하려 하기 때문이다.
그래서 대부분의 실전 설계는 다음 둘 중 하나로 수렴한다.

- DB 변경 로그를 읽는 CDC
- 애플리케이션이 outbox에 쓰고 relay가 꺼내는 outbox pattern

### 2. Capacity Estimation

예:

- 초당 주문/결제/상태변경 이벤트 2만 건
- 평균 payload 1 KB
- 피크 배수 5x
- downstream fan-out 6개 시스템

이때 단순 publish QPS보다 더 중요한 숫자는 다음이다.

- source commit TPS
- relay lag
- catch-up throughput
- partition skew
- poison event 비율
- bootstrap 소요 시간

CDC 파이프라인은 평상시 throughput보다 장애 후 catch-up 속도가 더 중요할 때가 많다.

### 3. Log-based CDC와 outbox의 차이

둘 다 맞는 해법이지만 적용 지점이 다르다.

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Log-based CDC | 앱 수정이 적다 | DB 로그 형식에 강하게 묶인다 | 기존 서비스가 많을 때 |
| Outbox relay | 비즈니스 이벤트를 명시적으로 정의하기 쉽다 | 애플리케이션 쓰기 경로 수정이 필요하다 | 신규 서비스나 도메인 이벤트가 중요할 때 |
| CDC + Outbox 병행 | 운영 유연성이 높다 | 시스템 수가 늘어난다 | 원시 변경과 의미 이벤트를 분리하고 싶을 때 |

중요한 구분:

- raw row change를 그대로 흘릴 것인가
- 비즈니스 의미가 있는 event로 정규화할 것인가

검색 인덱싱, 알림, 과금처럼 downstream이 많아질수록 두 번째가 더 유지보수하기 쉽다.

### 4. 순서와 파티션 키

CDC가 있다고 전체 순서가 보장되는 것은 아니다.
보통 보장 가능한 것은 "같은 key 안에서의 순서"다.

예:

- `order_id` 기준 순서 보장
- `tenant_id` 기준 순서 보장
- 전체 글로벌 순서는 보장하지 않음

실무에서 가장 흔한 실수는 파티션 키를 바꾸면서 기존 consumer가 기대하던 순서 가정을 깨뜨리는 것이다.
그래서 설계 문서에는 항상 다음을 적어야 한다.

- ordering scope
- dedup key
- replay 시 재사용할 offset 또는 cursor
- rebalancing 시 허용 가능한 out-of-order 범위

### 5. Snapshot bootstrap과 catch-up

새 downstream을 붙일 때는 과거 데이터를 한 번에 보내야 한다.
이때 흔한 흐름은 다음과 같다.

1. bootstrap snapshot 시점 T를 고정한다
2. T 이전 데이터는 backfill worker가 읽는다
3. T 이후 변경은 CDC stream이 계속 받는다
4. 둘의 경계가 겹치는 구간은 dedup key로 흡수한다

즉, bootstrap은 단순 dump가 아니라 "과거 복사 + 실시간 추격"의 조합이다.
이 부분은 [Historical Backfill / Replay Platform 설계](./historical-backfill-replay-platform-design.md)와 같이 보면 더 선명하다.

### 6. 스키마 진화와 poison event

CDC payload는 결국 스키마에 묶인다.
필드 하나가 바뀌면 downstream이 깨질 수 있다.

대응 원칙:

- event schema version을 포함한다
- backward compatible 변경을 기본값으로 둔다
- unknown field는 무시 가능한 구조로 만든다
- poison event는 quarantine queue로 격리한다

DB schema migration과 event schema migration을 따로 보면 운영이 엇갈린다.
그래서 schema 변경은 [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)와 묶어서 보는 편이 안전하다.
특히 old/new 시스템 전환에서는 직접 dual write보다 migration bridge와 authority transfer 경계를 먼저 설계하는 편이 더 안전하다.

### 7. exactly-once 환상과 relay 상태 관리

대부분의 CDC/relay는 실제로는 at-least-once다.
그래서 다음이 더 중요하다.

- relay checkpoint 저장
- publish 전후 상태 전이 명시
- downstream dedup
- side effect suppression

핵심 질문은 "중복이 나오는가"가 아니라, "중복이 나왔을 때 안전한가"다.

## 실전 시나리오

### 시나리오 1: 주문 변경을 검색 인덱스에 반영

문제:

- 주문 DB가 source of truth다
- 검색 인덱스는 빠르게 최신 상태를 따라와야 한다

해결:

- outbox에 `OrderSearchProjectionUpdated`를 기록한다
- relay는 tenant-aware partition으로 event bus에 publish한다
- search worker는 idempotent upsert를 수행한다

### 시나리오 2: 사용량 과금 파이프라인

문제:

- API 호출량이 billing usage meter로 흘러가야 한다
- downstream 지연이 있어도 source write는 막히면 안 된다

해결:

- source 서비스는 사용량 row와 outbox row만 트랜잭션으로 기록한다
- relay lag는 별도 SLO로 모니터링한다
- billing 쪽은 consumer dedup key를 강제한다

### 시나리오 3: downstream 장애로 backlog 폭증

문제:

- 검색이나 분석 시스템이 몇 시간 동안 다운된다
- relay backlog가 커진다

해결:

- hot path와 cold catch-up worker를 분리한다
- consumer별 lag와 replay throughput을 따로 본다
- poison event는 전체 파이프라인을 멈추지 않게 격리한다

## 코드로 보기

```pseudo
function createOrder(cmd):
  tx.begin()
  order = orders.insert(cmd)
  outbox.insert({
    aggregateId: order.id,
    eventType: "OrderCreated",
    payload: buildEvent(order)
  })
  tx.commit()

function relay(batch):
  rows = outbox.fetchUnpublished(batch)
  for row in rows:
    bus.publish(row.partitionKey, row.payload)
    outbox.markPublished(row.id)
```

```java
public void relay(OutboxRecord record) {
    publisher.publish(record.partitionKey(), record.payload());
    outboxRepository.markPublished(record.id());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| App direct publish | 단순하다 | dual write 위험이 크다 | 아주 작은 시스템 |
| Outbox relay | 비즈니스 의미를 제어하기 쉽다 | outbox 정리와 relay 운영이 필요하다 | 도메인 이벤트 중심 서비스 |
| DB log CDC | 도입이 빠르다 | row change가 그대로 새어 나가기 쉽다 | 기존 모놀리스, 레거시 DB |
| Snapshot + stream catch-up | 신규 consumer onboarding이 쉽다 | 경계 dedup이 필요하다 | 검색, 분석, 캐시 재구축 |
| Strict ordering | 이해가 쉽다 | throughput이 낮아진다 | entity 단위 정합성 중요 |

핵심은 CDC가 "복제 도구"가 아니라 **데이터 이동의 실패 모델을 명시하는 운영 계약**이라는 점이다.

## 꼬리질문

> Q: outbox와 2PC는 어떻게 다른가요?
> 의도: 분산 트랜잭션 회피 전략 이해 확인
> 핵심: outbox는 원자적 로컬 write 후 비동기 전파를 택하고, 2PC는 여러 자원을 동기적으로 묶는다.

> Q: CDC가 있으면 exactly-once가 되나요?
> 의도: 전달 보장 모델 이해 확인
> 핵심: 보통은 at-least-once이며, dedup과 idempotent consumer가 같이 필요하다.

> Q: bootstrap과 replay를 왜 분리하나요?
> 의도: 신규 consumer onboarding과 장애 복구 차이 이해 확인
> 핵심: bootstrap은 초기 적재, replay는 기존 흐름 재처리라서 속도와 안전장치가 다르다.

> Q: row change를 그대로 흘리면 안 되나요?
> 의도: raw CDC와 domain event 차이 이해 확인
> 핵심: downstream이 source schema에 과하게 결합되고, 의미 있는 버전 관리가 어려워진다.

## 한 줄 정리

Change data capture와 outbox relay는 dual write를 끊고 재처리 가능한 이벤트 전달 경로를 만들어, source of truth 변경을 안전하게 downstream으로 복제하는 설계다.
