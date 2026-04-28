# Adapter Bulk Optimization Without Port Leakage

> 한 줄 요약: `saveAll`, JDBC batch, HTTP bulk endpoint는 adapter 안에서 사용할 수 있지만, application port는 여전히 "한 주문 저장", "한 알림 전송"처럼 item 단위와 도메인 언어를 유지해야 한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [Ports and Adapters Beginner Primer](./ports-and-adapters-beginner-primer.md)
- [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
- [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: adapter bulk optimization without port leakage, saveall port smell, jdbc batch inside adapter, http bulk endpoint mapping, per-item port contract, domain-shaped port, bulk contract promotion, beginner hexagonal boundary, batch optimization without leakage, named bulk contract, partial failure mapping, adapter coalescing, 처음 saveall 왜 안 되나요, bulk port 언제 올리나요, what is bulk port
<details>
<summary>Table of Contents</summary>

- [먼저 떠올릴 그림](#먼저-떠올릴-그림)
- [port에는 무엇을 남기고 adapter에는 무엇을 숨기나](#port에는-무엇을-남기고-adapter에는-무엇을-숨기나)
- [한 번에 감 잡는 3건 예시](#한-번에-감-잡는-3건-예시)
- [누수 신호: 기술 bulk API가 port 이름이 된다](#누수-신호-기술-bulk-api가-port-이름이-된다)
- [안전한 모양 1: JPA/Hibernate batch는 persistence adapter 세부다](#안전한-모양-1-jpahibernate-batch는-persistence-adapter-세부다)
- [안전한 모양 2: JDBC batch는 transaction 안의 adapter 구현이다](#안전한-모양-2-jdbc-batch는-transaction-안의-adapter-구현이다)
- [안전한 모양 3: HTTP bulk endpoint는 adapter가 per-item 결과로 번역한다](#안전한-모양-3-http-bulk-endpoint는-adapter가-per-item-결과로-번역한다)
- [짧은 결정 표](#짧은-결정-표)
- [언제 bulk port로 올려야 하나](#언제-bulk-port로-올려야-하나)
- [처음 적용할 때 3단계](#처음-적용할-때-3단계)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)
- [다음에 이어서 볼 문서](#다음에-이어서-볼-문서)

</details>

## 먼저 떠올릴 그림

초심자에게는 이 그림 하나로 시작하면 된다.

- 안쪽 application은 "이 주문을 저장해 줘"라고 말한다
- 바깥 persistence adapter는 "INSERT를 한 번씩 보낼지, JDBC batch로 묶을지"를 정한다

즉 port는 **무슨 일을 약속하는지**를 말하고, adapter는 **그 일을 어떤 기술 API로 빠르게 처리할지**를 맡는다.

그래서 성능 때문에 아래 기술이 필요해도:

- Spring Data JPA `saveAll`
- Hibernate JDBC batching
- `PreparedStatement.addBatch`
- 파트너사의 `/bulk-send` HTTP endpoint

그 이름이 곧바로 application port로 올라올 필요는 없다.

짧게 외우면:

- port는 "무슨 일을 약속하나"를 말한다
- adapter는 "그 약속을 어떤 기술로 빠르게 처리하나"를 말한다

## 이런 문장에서 막히면 이 문서가 맞다

| 지금 떠오르는 말 | 먼저 잡을 기준 |
|---|---|
| "`saveAll`이 더 빠르니 port도 `saveAll`이어야 하나?" | 기술 API 이름과 application 계약 이름을 분리한다 |
| "외부가 `/bulk-send`만 주는데 단건 port는 거짓말 아닌가?" | 호출 방식보다 per-item 결과를 보존할 수 있는지 본다 |
| "batch를 숨기면 실패 원인을 못 찾지 않나?" | item 실패를 다시 설명할 수 있으면 숨길 수 있다 |
| "운영자가 chunk 단위로 다시 돌린다면?" | 그때는 bulk 자체가 업무 단위인지 다시 판단한다 |

## port에는 무엇을 남기고 adapter에는 무엇을 숨기나

가장 중요한 분리는 아래와 같다.

| 구분 | port에 남길 것 | adapter 안에 둘 것 |
|---|---|---|
| 이름 | `save(Order)`, `send(WelcomeMail)`, `fetch(CarrierTrackingNo)` | `saveAll`, `executeBatch`, `POST /bulk-status` |
| 타입 | `Order`, `OrderId`, `DeliveryReceipt` 같은 도메인 타입 | JPA entity, SQL row, 외부 API request/response DTO |
| 실패 의미 | "이 item이 실패했다" 혹은 port가 약속한 예외 | vendor error code, batch index, HTTP bulk response parsing |
| 성능 선택 | 호출자가 몰라도 되는 상태 | batch size, flush timing, chunk size, retryable status mapping |

짧게 말하면:

- application은 **item 단위 의미**를 잃지 않는다
- adapter는 **기술 bulk API**를 마음껏 바꿀 수 있어야 한다

나중에 JPA에서 JDBC로 바꾸거나, HTTP bulk endpoint 대신 message queue로 바꿔도 port 이름이 그대로면 경계가 잘 지켜진 것이다.

## 한 번에 감 잡는 3건 예시

동일한 주문 저장 3건을 처리할 때, 바깥 최적화와 안쪽 계약은 이렇게 분리된다.

| 단계 | application이 보는 것 | adapter가 실제로 하는 것 |
|---|---|---|
| 1건째 저장 | `orderRepository.save(order-1)` | row 변환 후 batch 버퍼에 추가 |
| 2건째 저장 | `orderRepository.save(order-2)` | row 변환 후 같은 트랜잭션 버퍼에 추가 |
| 3건째 저장 | `orderRepository.save(order-3)` | 커밋 직전 `executeBatch` 또는 `saveAll`로 묶어 전송 |

핵심은 호출 3번이 "의미 3건"이라는 점이다.
전송 1번/3번은 adapter 최적화 선택일 뿐, port 계약을 바꾸는 이유가 되지 않는다.

## 누수 신호: 기술 bulk API가 port 이름이 된다

아래 코드는 성능 의도가 port 계약으로 새어 나온 예다.

```java
public interface OrderPersistencePort {
    void saveAllJpaEntities(List<OrderJpaEntity> entities);
}

public interface PartnerMailPort {
    BulkHttpResponse sendBulk(BulkHttpRequest request);
}
```

이런 이름은 초반에는 편해 보이지만, application이 바깥 기술을 알아야 한다.

- `OrderJpaEntity`가 안쪽으로 들어온다
- 외부 HTTP request/response DTO가 use case 테스트에 등장한다
- 일부 실패, 재시도, idempotency가 vendor bulk 응답 형식에 끌려간다
- 나중에 저장 방식을 바꾸면 port까지 같이 흔들린다

bulk 자체가 나쁜 것이 아니다.
문제는 **도메인 일이 아니라 기술 호출 모양이 port 이름이 되는 것**이다.

## 안전한 모양 1: JPA/Hibernate batch는 persistence adapter 세부다

주문 저장의 application port가 아래처럼 단건 계약이라고 하자.

```java
public interface OrderRepository {
    void save(Order order);
}
```

persistence adapter는 도메인을 JPA entity로 바꾼 뒤 저장한다.

```java
@Component
class JpaOrderRepositoryAdapter implements OrderRepository {
    private final SpringDataOrderJpaRepository jpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public void save(Order order) {
        OrderJpaEntity entity = mapper.toEntity(order);
        jpaRepository.save(entity);
    }
}
```

여기서 성능 최적화는 adapter와 ORM 설정 쪽에 둔다.

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

application 입장에서는 여전히 `save(order)`다.
하지만 persistence adapter와 Hibernate는 같은 transaction 안에서 flush될 SQL을 batch로 묶을 수 있다.

핵심은:

- port가 `saveAll(List<OrderJpaEntity>)`로 바뀌지 않는다
- domain object와 JPA entity 매핑은 adapter가 담당한다
- batch size, flush timing, entity identity 같은 ORM 세부는 use case가 모른다

만약 adapter 내부에서 Spring Data `saveAll(...)`을 쓰는 편이 더 낫다면, 그것도 **adapter private helper**로 남기면 된다.
application port가 그 메서드를 직접 보지 않는 한 경계는 유지된다.

## 안전한 모양 2: JDBC batch는 transaction 안의 adapter 구현이다

JDBC batch도 같은 원리다.
port는 "쿠폰 발급 이력을 저장한다"는 도메인 의미만 말한다.

```java
public interface CouponIssueRepository {
    void save(CouponIssue issue);
}
```

adapter는 이 호출을 row로 바꾼 뒤, 같은 transaction 안에서 batch 실행을 선택할 수 있다.

```java
class JdbcCouponIssueRepositoryAdapter implements CouponIssueRepository {
    private final TransactionScopedCouponIssueBatch batch;
    private final CouponIssueRowMapper mapper;

    @Override
    public void save(CouponIssue issue) {
        batch.add(mapper.toRow(issue));
    }
}
```

`TransactionScopedCouponIssueBatch` 같은 adapter 내부 도구는 transaction이 끝나기 전에 모인 row를 JDBC batch로 보낸다.

```java
class TransactionScopedCouponIssueBatch {
    void add(CouponIssueRow row) {
        currentTransactionRows().add(row);
    }

    void beforeCommit(List<CouponIssueRow> rows) {
        jdbcTemplate.batchUpdate(
                "insert into coupon_issue (...) values (...)",
                rows,
                100,
                (ps, row) -> bind(ps, row)
        );
    }
}
```

이 예시에서 중요한 것은 batch helper의 구현 방식이 아니라 경계다.

- application은 `CouponIssueRepository.save(issue)`만 안다
- SQL row, batch size, `PreparedStatement` binding은 adapter 안에 있다
- 실패를 port가 약속한 item 실패나 저장 실패로 다시 번역할 수 있어야 한다

주의할 점도 있다.
adapter가 전역 `List`에 몰래 쌓아 두거나, transaction 밖에서 임의로 flush하면 더 위험해진다.
그럴 바에는 단건 `jdbcTemplate.update(...)`를 유지하거나, 묶음 자체가 업무 단위인지 다시 판단하는 편이 낫다.

## 안전한 모양 3: HTTP bulk endpoint는 adapter가 per-item 결과로 번역한다

외부 HTTP API도 마찬가지다.
파트너사가 bulk endpoint만 제공하더라도, application port가 꼭 `BulkHttpRequest`를 받을 필요는 없다.
bulk partial response를 `batch receipt`, `per-item receipt`, `retry decision`으로 다시 펴는 구체 예시는 [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)에서 이어서 볼 수 있다.

```java
public interface WelcomeMailSender {
    DeliveryReceipt send(WelcomeMail mail);
}
```

adapter는 내부에서 bulk endpoint를 호출하고, 결과를 다시 item 결과로 바꾼다.

```java
class PartnerWelcomeMailAdapter implements WelcomeMailSender {
    private final PartnerBulkMailClient bulkClient;
    private final PartnerMailMapper mapper;

    @Override
    public DeliveryReceipt send(WelcomeMail mail) {
        PartnerBulkResult result = bulkClient.sendBulk(List.of(mapper.toRequest(mail)));
        return mapper.toReceipt(result.resultOf(mail.id()));
    }
}
```

더 나아가 scheduled job나 message consumer가 짧은 시간 안에 여러 건을 호출한다면, adapter 내부 coalescing으로 묶을 수도 있다.

```java
class PartnerWelcomeMailAdapter implements WelcomeMailSender {
    @Override
    public DeliveryReceipt send(WelcomeMail mail) {
        return coalescer.enqueue(
                mail,
                mails -> bulkClient.sendBulk(mapper.toBulkRequest(mails)),
                result -> mapper.toReceipt(result.resultOf(mail.id()))
        );
    }
}
```

초심자 기준으로는 coalescing 구현보다 아래 조건이 더 중요하다.

- 호출자는 여전히 한 mail의 전송 결과를 받는다
- 외부 bulk 응답을 item id 기준으로 정확히 매핑할 수 있다
- 한 item 실패가 다른 item의 성공 의미를 흐리지 않는다
- retry와 idempotency key가 port의 per-item 약속과 맞는다

## bulk를 숨기기 어려운 신호

이 조건을 지킬 수 없으면 adapter 최적화로 숨기기 어렵다.
그때는 bulk를 application 계약으로 올릴지 검토해야 한다.

## 짧은 결정 표

| 질문 | adapter 안에 bulk를 숨겨도 좋은 신호 | port로 올려야 하는 신호 |
|---|---|---|
| application이 설명하는 일은? | 한 주문 저장, 한 알림 전송, 한 상태 조회 | 한 정산 chunk 전송, 한 업로드 파일 처리 |
| 실패를 어떻게 말하나? | item id 기준으로 성공/실패를 설명할 수 있다 | chunk receipt, partial failure summary가 핵심 결과다 |
| bulk API를 빼도 port가 유지되나? | JPA/JDBC/HTTP 구현만 바꾸면 된다 | use case 입력과 운영 재개 방식도 바뀐다 |
| idempotency는 어디에 있나? | item key가 중심이다 | run id, chunk id, file id가 중심이다 |
| 테스트는 무엇을 봐야 하나? | use case는 fake port로 item 의미를 본다 | batch policy, checkpoint, partial failure를 application test에서 본다 |

이 표에서 왼쪽이면 adapter 내부 최적화로 시작하는 편이 안전하다.
오른쪽이면 [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)와 [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)를 같이 봐야 한다.

## 언제 bulk port로 올려야 하나

아래 상황이면 "bulk를 숨긴다"보다 "bulk를 이름 있는 계약으로 올린다"가 더 정직하다.

- 운영자가 "3번 chunk만 다시 실행"처럼 묶음 단위로 말한다
- 외부 시스템이 batch receipt id만 주고 item 결과를 충분히 주지 않는다
- 실패 정책이 "전체 실패", "일부 성공", "retry queue 이동"처럼 batch policy가 된다
- checkpoint, cutoff time, run id가 application 입력으로 필요하다
- bulk 호출을 없애면 기능 의미 자체가 달라진다

이때도 `saveAll(List<T>)` 같은 기술 이름보다 `SettlementChunk`, `BulkSubmitResult`, `RetryBacklog`처럼 업무 의미가 있는 타입을 쓰는 편이 낫다.

## 처음 적용할 때 3단계

초심자라면 아래 순서로 시작하면 실수가 줄어든다.

1. 기존 port를 item 단위(`save`, `send`)로 먼저 고정한다.
2. adapter 내부에서만 `saveAll`/batch/coalescing을 도입해 측정한다.
3. per-item 결과/실패/idempotency가 깨지면 그때 bulk 계약 승격을 검토한다.

이 순서는 "성능 최적화는 하되, 계약 확장은 늦게"라는 안전장치다.

## 자주 하는 오해

- "`saveAll`을 port에 두지 말라면 batch 성능을 못 쓰는 것 아닌가"
  - 아니다. Hibernate batch, JDBC batch, adapter private helper, HTTP coalescing처럼 adapter 내부에서 쓸 수 있다.
- "port가 단건이면 adapter도 반드시 단건 네트워크 호출만 해야 하나"
  - 아니다. adapter가 per-item 결과와 실패 의미를 보존할 수 있다면 내부 호출 방식은 바꿀 수 있다.
- "JPA `saveAll`을 쓰면 무조건 나쁜 설계인가"
  - 아니다. 문제는 `saveAll`이 application port 이름과 타입으로 새는 것이다.
- "adapter가 bulk를 숨기면 실패 분석이 어려워지지 않나"
  - 숨긴 bulk가 item 결과로 설명되지 않는다면 숨기면 안 된다. 그 경우는 batch 계약을 올려야 한다.
- "batch job는 항상 bulk port가 필요한가"
  - 아니다. scheduled job가 per-item use case를 반복 호출하고, adapter만 내부 최적화를 할 수도 있다.

## 기억할 기준

초심자용으로는 네 문장만 기억하면 충분하다.

1. port는 기술 API 이름이 아니라 application이 약속하는 일의 이름이다.
2. `saveAll`, JDBC batch, HTTP bulk endpoint는 adapter 안에 둘 수 있다.
3. adapter bulk가 안전하려면 per-item 결과, 실패, idempotency를 보존해야 한다.
4. 묶음 자체가 운영과 도메인의 단위가 되면, 그때는 이름 있는 bulk 계약으로 올린다.

## 다음에 이어서 볼 문서

- per-item과 bulk 계약 승격 기준을 더 비교하려면: [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md)
- 부분 실패 결과 타입을 계약으로 설계하려면: [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
- 이름 붙인 bulk 계약을 어떤 테스트 축으로 고정할지 보려면: [Testing Named Bulk Contracts](./testing-named-bulk-contracts.md)
- HTTP bulk 응답을 item 결과로 매핑하려면: [HTTP Coalescing Failure Mapping](./http-coalescing-failure-mapping.md)
- persistence 경계 점검을 같이 하려면: [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)

## 한 줄 정리

`saveAll`, JDBC batch, HTTP bulk endpoint는 adapter 안에서 사용할 수 있지만, application port는 여전히 "한 주문 저장", "한 알림 전송"처럼 item 단위와 도메인 언어를 유지해야 한다.
