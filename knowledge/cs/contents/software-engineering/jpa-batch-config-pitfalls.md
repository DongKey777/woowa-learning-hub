# JPA Batch Config Pitfalls

> 한 줄 요약: `hibernate.jdbc.batch_size`를 켰다고 자동으로 대량 저장이 빨라지는 것은 아니며, `flush` 타이밍, `IDENTITY` 키 생성 방식, 그리고 "이게 배치 업무 계약인가 아니면 ORM 최적화인가"를 분리해서 봐야 초심자가 덜 헷갈린다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: jpa batch config pitfalls basics, jpa batch config pitfalls beginner, jpa batch config pitfalls intro, software engineering basics, beginner software engineering, 처음 배우는데 jpa batch config pitfalls, jpa batch config pitfalls 입문, jpa batch config pitfalls 기초, what is jpa batch config pitfalls, how to jpa batch config pitfalls
[30분 후속 분기표로 돌아가기](./common-confusion-wayfinding-notes.md#자주-헷갈리는-3개-케이스)

<details>
<summary>Table of Contents</summary>

- [먼저 그림부터 잡기](#먼저-그림부터-잡기)
- [주니어 체크리스트](#주니어-체크리스트)
- [증상으로 먼저 역추적하기](#증상으로-먼저-역추적하기)
- [설정이 해 주는 일과 안 해 주는 일](#설정이-해-주는-일과-안-해-주는-일)
- [flush 타이밍이 왜 중요한가](#flush-타이밍이-왜-중요한가)
- [`GenerationType.IDENTITY`가 왜 자주 걸림돌이 되나](#generationtypeidentity가-왜-자주-걸림돌이-되나)
- [같은 3건 insert를 머릿속으로 그려보기](#같은-3건-insert를-머릿속으로-그려보기)
- [왜 여전히 persistence adapter concern인가](#왜-여전히-persistence-adapter-concern인가)
- [`saveAll` 포트 승격 오해: before / after](#saveall-포트-승격-오해-before--after)
- [배치가 실제로 적용됐는지 어떻게 확인하나](#배치가-실제로-적용됐는지-어떻게-확인하나)
- [자주 하는 오해](#자주-하는-오해)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: JPA Batch Config Pitfalls](./README.md#jpa-batch-config-pitfalls)
> - [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)
> - [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
> - [Persistence Adapter Mapping Checklist](./persistence-adapter-mapping-checklist.md)
> - [Adapter Bulk Optimization Without Port Leakage](./adapter-bulk-optimization-without-port-leakage.md)
> - [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
> - [Repository, DAO, Entity](./repository-dao-entity.md)
> - [Aggregate Persistence Mapping Pitfalls](./aggregate-persistence-mapping-pitfalls.md)
>
> retrieval-anchor-keywords: jpa batch config pitfalls, hibernate batch settings, hibernate jdbc batch size, hibernate order_inserts, hibernate order_updates, jpa flush timing, entitymanager flush clear loop, flush commit clear difference, generationtype identity batching, identity strategy insert batching, sequence vs identity batch, identity vs sequence before after, identity sequence batching mental model, insert batching timeline, spring data saveAll batching misconception, saveAll port promotion misconception, saveAll port elevation mistake, persistence adapter concern, orm tuning boundary, jpa adapter boundary, jpa batch verification, hibernate statistics batch check, sql log batch 확인, datasource proxy batch 확인, datajpatest batch verification, integration test batch check, beginner jpa batch primer

## 먼저 그림부터 잡기

초심자는 먼저 이 그림 하나로 시작하면 된다.

- application service는 "주문 한 건을 저장한다" 같은 **일의 의미**를 말한다
- persistence adapter는 그 일을 JPA entity로 바꾸고, SQL을 언제 얼마나 묶을지 정한다
- Hibernate/JDBC batch는 **SQL 전송 최적화**이지, 애플리케이션이 갑자기 "진짜 bulk 업무"를 하게 만든 것은 아니다

즉 아래 두 문장은 같은 말이 아니다.

- "`save(order)`를 여러 번 호출했더니 adapter 안에서 SQL이 batch로 묶였다"
- "`saveAll(List<Order>)`가 우리 애플리케이션의 공식 계약이다"

첫 번째는 persistence 최적화다.
두 번째는 업무 계약 변경이다.

이 둘을 섞으면 `batch_size` 설정 하나 때문에 port 이름, 실패 의미, 재시도 설명까지 흔들리기 쉽다.

## 주니어 체크리스트

| 체크할 것 | 먼저 확인할 질문 | 위험 신호 |
|---|---|---|
| 업무 계약 | 지금 필요한 것이 진짜 `BatchRun`, `Chunk`, `FileImport` 같은 묶음 일인가 | 단순 성능 이유만으로 `saveAll(...)`이 port에 올라온다 |
| Hibernate 설정 | `hibernate.jdbc.batch_size`가 0보다 크고, `order_inserts`/`order_updates` 필요 여부를 검토했는가 | `saveAll()`만 쓰면 자동 batch라고 믿는다 |
| ID 생성 전략 | insert 시 PK를 미리 알 수 있는가 | `GenerationType.IDENTITY`인데 insert batch가 잘 될 거라고 기대한다 |
| flush/clear 주기 | 대량 루프에서 영속성 컨텍스트를 언제 비울지 정했는가 | 한 트랜잭션에 수천~수만 엔티티를 계속 붙잡는다 |
| 검증 방법 | SQL 로그나 Hibernate 통계로 실제 batch 여부를 확인했는가 | 코드 모양만 보고 "최적화됐다"고 결론낸다 |
| 책임 위치 | batch size, flush timing, ID 전략이 adapter/config에 머무는가 | service나 domain이 ORM 타이밍을 알아야 동작한다 |

짧게 외우면 이 순서다.

1. 먼저 "이게 진짜 batch 업무 계약인가"를 본다.
2. 아니라면 port는 그대로 두고 adapter 안에서만 JPA batch를 튜닝한다.
3. 그다음 `IDENTITY`, `flush`, 영속성 컨텍스트 크기를 점검한다.

## 증상으로 먼저 역추적하기

초심자에게는 설정 이름보다 "지금 눈앞에서 무슨 현상이 보이느냐"가 더 빠른 출발점일 때가 많다.

| 보이는 증상 | 먼저 확인할 것 | 보통의 해석 |
|---|---|---|
| `saveAll()`을 썼는데 insert가 한 건씩 바로 나간다 | `IDENTITY` 사용 여부, 중간 flush 발생, insert/update 혼합 여부 | 메서드 이름보다 ID 전략과 SQL 전송 타이밍이 batch 효과를 더 크게 흔든다 |
| 처리 건수가 커질수록 메모리 사용량과 속도가 같이 나빠진다 | `flush()`/`clear()` 주기, 한 번에 관리 중인 entity 수 | batch size만 올린 문제가 아니라 영속성 컨텍스트를 너무 오래 붙잡는 문제일 수 있다 |
| service 코드가 "`50건마다 flush`" 같은 규칙을 직접 안다 | flush 상수와 `EntityManager` 의존성의 위치 | 기술 타이밍 규칙이 application 쪽으로 새고 있다는 신호다 |
| 논의가 `Chunk`, `RetryCandidate`, `RunId`로 넘어간다 | 정말 batch 자체가 업무 단위인지 | 단순 ORM 최적화가 아니라 application batch 계약이 필요한 상황일 수 있다 |

짧은 진단 순서는 아래 정도면 충분하다.

1. SQL 로그나 통계로 실제로 batch가 묶이는지 본다.
2. insert batching이면 `IDENTITY`부터 의심한다.
3. 그다음 `flush()`/`clear()` 주기와 영속성 컨텍스트 크기를 본다.
4. 마지막으로 이 문제가 adapter 최적화인지, 진짜 batch 계약 승격인지 구분한다.

## 설정이 해 주는 일과 안 해 주는 일

가장 많이 보는 설정은 아래 셋이다.

```properties
spring.jpa.properties.hibernate.jdbc.batch_size=50
spring.jpa.properties.hibernate.order_inserts=true
spring.jpa.properties.hibernate.order_updates=true
```

각 설정은 이런 의미다.

| 설정 | 해 주는 일 | 해 주지 않는 일 |
|---|---|---|
| `hibernate.jdbc.batch_size` | 같은 종류의 SQL을 JDBC batch로 최대 N개까지 묶을 기회를 준다 | 애플리케이션 계약을 bulk로 바꾸지 않는다 |
| `hibernate.order_inserts` | insert를 엔티티/테이블 기준으로 재정렬해 batch 가능성을 높인다 | Java 코드의 처리 순서를 업무 의미로 보장하지 않는다 |
| `hibernate.order_updates` | update도 비슷하게 묶일 chance를 높인다 | 모든 update가 항상 한 번에 묶인다고 보장하지 않는다 |

초심자가 특히 놓치기 쉬운 점은 이것이다.

- batch는 보통 **같은 모양의 SQL**이 모여야 잘 된다
- insert와 update가 뒤섞이거나, 테이블이 자주 바뀌거나, 중간중간 flush가 발생하면 batch 효과가 줄어든다
- 그래서 `saveAll()` 호출 자체보다 **실제로 언제 flush가 일어나는지**가 더 중요할 때가 많다

## flush 타이밍이 왜 중요한가

JPA에서는 `persist()`나 `save()`를 호출했다고 매번 즉시 DB에 보내는 것이 아니다.
보통은 flush 시점에 SQL이 실제로 나간다.

이 말은 두 가지를 뜻한다.

- flush가 너무 늦으면 영속성 컨텍스트가 커져서 메모리와 dirty checking 비용이 커진다
- flush가 너무 잦으면 SQL이 잘게 끊겨 batch 이점이 줄어든다

초심자 기준으로는 "적당한 chunk마다 `flush()` + `clear()`"를 adapter 내부 배치 writer에서 다루는 쪽이 안전하다.

```java
class JpaCouponIssueBatchWriter {
    @PersistenceContext
    private EntityManager em;

    private final CouponIssueEntityMapper mapper;

    void writeChunk(List<CouponIssue> issues) {
        int i = 0;
        for (CouponIssue issue : issues) {
            em.persist(mapper.toEntity(issue));

            if (++i % 50 == 0) {
                em.flush();
                em.clear();
            }
        }

        em.flush();
        em.clear();
    }
}
```

여기서 역할을 분리해서 보면 더 덜 헷갈린다.

| 동작 | 하는 일 | 초심자 오해 바로잡기 |
|---|---|---|
| `flush()` | 아직 commit 전이어도 pending SQL을 DB로 보낸다 | commit과 같지 않다. 트랜잭션은 아직 끝나지 않았다 |
| `clear()` | 이미 관리 중이던 entity를 detach해서 영속성 컨텍스트를 비운다 | DB row를 지우는 것이 아니라 1차 캐시와 관리 상태를 정리하는 것이다 |
| `commit()` | 트랜잭션을 확정한다 | flush를 포함할 수 있지만, "몇 건마다 보낼지"를 설명하는 도구는 아니다 |

셋 다 "ORM이 메모리와 SQL 전송을 어떻게 관리할까"라는 persistence 관심사다.

즉 service가 "`50개마다 flush해야 해`"를 business rule처럼 알고 있으면 경계가 이미 무너진 신호다.

## `GenerationType.IDENTITY`가 왜 자주 걸림돌이 되나

초심자 실수 중 하나는 batch 설정만 맞추면 insert도 자연스럽게 묶일 거라고 생각하는 것이다.
하지만 PK 생성 전략이 그 기대를 깨는 경우가 많다.

핵심은 "insert 전에 ID를 미리 알 수 있느냐"다.

| 전략 | insert 전에 ID를 알 수 있나 | insert batch 친화도 | 초심자용 해석 |
|---|---|---|---|
| `GenerationType.IDENTITY` | 보통 어렵다 | 낮다 | DB가 insert를 먼저 해야 PK를 돌려주므로, insert를 바로 보내야 할 때가 많다 |
| `SEQUENCE` | 대체로 가능하다 | 높다 | 미리 ID를 확보하고 insert를 모아 보내기 쉽다 |
| 애플리케이션 할당 ID (`UUID` 등) | 가능하다 | 높다 | insert 전에 키가 이미 있어 batch 설계가 단순해진다 |

그래서 `IDENTITY`를 쓰면 특히 insert batch에서 이런 현상이 자주 보인다.

- `persist()` 직후 insert가 빨리 실행된다
- 기대한 만큼 JDBC batch로 안 묶인다
- "`batch_size`를 100으로 올렸는데도 체감이 없다"는 일이 생긴다

여기서 중요한 포인트는 "무조건 `IDENTITY`를 버려라"가 아니다.
ID 전략은 DB 표준, 운영 편의, 마이그레이션 방식과도 연결된 persistence 설계다.
다만 **insert batching이 목표라면 `IDENTITY`는 먼저 의심해야 하는 제한 조건**이라는 점을 기억하면 된다.

같은 insert 테스트가 `IDENTITY`와 `SEQUENCE`에서 왜 다르게 보이는지 아주 짧은 before/after 예시로 보고 싶다면, [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)로 바로 이어서 보면 된다.

## 같은 3건 insert를 머릿속으로 그려보기

초심자에게는 이 비유가 가장 빠르다.

- `IDENTITY`는 "계산대에 물건을 올린 뒤에야 번호표를 받는 방식"에 가깝다
- `SEQUENCE`는 "창구에 가기 전에 번호표를 미리 뽑아 두는 방식"에 가깝다

그래서 같은 3건 저장도 batching 관점에서는 흐름이 다르게 보인다.

| 전략 | 머릿속 흐름 | batching 관점에서 보이는 차이 |
|---|---|---|
| `IDENTITY` | `save A -> insert A 후 PK 수령 -> save B -> insert B 후 PK 수령 -> save C -> insert C 후 PK 수령` | 각 insert 직후 PK를 받아야 해서, insert를 길게 모아 두기 어렵다 |
| `SEQUENCE` | `A/B/C용 ID 미리 확보 -> save A/B/C를 영속성 컨텍스트에 모음 -> flush 시 insert A/B/C 전송` | insert 전에 PK를 알고 있어서 같은 모양 SQL을 batch로 모으기 쉽다 |

before / after처럼 더 짧게 보면 아래 한 줄로 정리된다.

| 비교 | `IDENTITY` | `SEQUENCE` |
|---|---|---|
| insert 전에 PK를 아는가 | 보통 모른다 | 대체로 안다 |
| "3건을 잠깐 모아 두었다가 한 번에 보낼 수 있나?" | 제약이 크다 | 상대적으로 쉽다 |
| 초심자용 기억 문장 | "먼저 넣고 번호를 받는다" | "번호를 받고 넣는다" |

이 표가 말하는 핵심은 "`SEQUENCE`면 무조건 빠르다"가 아니다.
초심자 관점에서 중요한 결론은 하나다.

- insert batching이 잘 안 먹을 때는 `saveAll()` 호출 수보다 **ID를 언제 얻는지**가 먼저 의심 포인트다

## 왜 여전히 persistence adapter concern인가

이 주제가 헷갈리는 이유는 "배치"라는 단어가 두 가지 뜻으로 쓰이기 때문이다.

- 업무 관점 batch: run, chunk, checkpoint, partial failure 같은 **애플리케이션 개념**
- ORM 관점 batch: SQL을 묶어서 보내는 **persistence 최적화**

둘을 나눠 보면 책임 위치가 선명해진다.

| 질문 | 주로 책임지는 곳 | 이유 |
|---|---|---|
| `batch_size`, `order_inserts`, `order_updates`를 어떻게 둘까 | persistence adapter / JPA 설정 | ORM과 JDBC가 SQL을 어떻게 묶을지 정하는 문제다 |
| `flush()`/`clear()`를 몇 건마다 할까 | persistence adapter 내부 writer/repository helper | 영속성 컨텍스트 크기와 SQL 전송 타이밍 문제다 |
| `IDENTITY` vs `SEQUENCE`를 쓸까 | persistence mapping / DB 설계 | 키 생성과 insert batching 가능성이 DB 기술 선택에 묶인다 |
| 이번 작업이 `SettlementChunk`처럼 이름 있는 batch 계약인가 | application service / batch use case | 실패 정책, 재시도, 운영 설명이 업무 개념이기 때문이다 |
| partial failure 결과를 어떻게 보여 줄까 | application/result model | 운영자와 호출자가 이해할 계약이 필요하기 때문이다 |

짧게 말하면:

- JPA batch 설정은 "저장 어댑터를 더 효율적으로 돌리는 법"이다
- `BatchRun`, `Chunk`, `RetryCandidate`는 "업무를 어떻게 설명할지"다
- JPA를 JDBC나 다른 저장 방식으로 바꿔도 service가 그대로여야 한다면, `batch_size`와 `flush` 규칙은 adapter concern으로 남아 있는 편이 맞다

성능 최적화를 했다는 이유만으로 port를 `saveAll`로 바꾸거나, 서비스가 `flush` 주기를 알아야 한다면 너무 안쪽 구현이 새어 나온 것이다.

## `saveAll` 포트 승격 오해: before / after

초심자가 많이 하는 착각은 이 흐름이다.

1. "`save()`를 여러 번 호출하니 느려 보인다."
2. "그럼 port를 `saveAll()`로 바꾸면 batch가 되겠지."
3. "이제 애플리케이션이 batch 저장 계약을 가진다."

하지만 대부분의 경우 필요한 것은 3번이 아니라 **2번의 구현 최적화**다.

| 구분 | before: 오해가 섞인 상태 | after: 경계를 지킨 상태 |
|---|---|---|
| port 의미 | "`List`로 받으면 더 빠르다"를 계약에 올린다 | "주문 한 건 저장"이라는 업무 의미를 유지한다 |
| service 책임 | JPA batch 기대 때문에 `saveAll()`을 호출한다 | 주문을 한 건씩 저장하고, 묶음 최적화는 모른다 |
| adapter 책임 | 거의 설명되지 않는다 | `flush()`/`clear()`, batch 설정, JPA writer가 내부에서 처리한다 |
| 초심자에게 남는 메시지 | bulk API가 곧 업무 계약처럼 보인다 | ORM 최적화와 업무 계약이 분리되어 보인다 |

### before

```java
public interface OrderRepository {
    void saveAll(List<Order> orders);
}

@Service
public class OrderImportService {
    private final OrderRepository orderRepository;

    public void importOrders(List<Order> orders) {
        orderRepository.saveAll(orders);
    }
}
```

이 코드는 얼핏 편해 보이지만, 초심자에게는 아래 오해를 남긴다.

- `saveAll()`이 곧 batch 업무 계약처럼 보인다
- 실제로는 JPA 설정 문제인데 application service가 성능 API를 고른 것처럼 보인다
- 나중에 partial failure, retry, chunk 의미가 필요해졌을 때도 이름이 설명을 못 한다

### after

## `saveAll` 포트 승격 오해: before / after (계속 2)

```java
public interface OrderRepository {
    void save(Order order);
}

@Service
public class OrderImportService {
    private final OrderRepository orderRepository;

    public void importOrders(List<Order> orders) {
        for (Order order : orders) {
            orderRepository.save(order);
        }
    }
}

@Repository
public class JpaOrderRepository implements OrderRepository {
    @PersistenceContext
    private EntityManager em;

    @Override
    public void save(Order order) {
        em.persist(OrderEntity.from(order));
    }

    void flushChunk() {
        em.flush();
        em.clear();
    }
}
```

이 after에서 핵심은 이것이다.

- service는 여전히 "주문 한 건 저장" 규칙만 안다
- adapter는 필요하면 내부 writer/helper에서 batch 설정과 `flush()` 주기를 쓴다
- 즉 `saveAll`은 공식 port가 아니라, 있어도 adapter 내부 최적화 도구로만 남는다

만약 정말로 `OrderImportChunk`, `ImportRunId`, `ImportResult`가 필요하다면 그때는 `saveAll(List<Order>)`가 아니라 **이름 있는 batch 계약**으로 승격하는 편이 맞다.

## 배치가 실제로 적용됐는지 어떻게 확인하나

초심자에게 가장 안전한 기준은 "코드 모양이 아니라 실행 흔적을 본다"이다.
즉 `saveAll()`이나 `for` 루프를 보고 판단하지 말고, SQL 로그나 Hibernate 통계에서 **정말 묶여서 나갔는지** 확인해야 한다.

먼저 머릿속 기준을 하나로 고정하면 덜 헷갈린다.

| 증거 단계 | 무엇을 보는가 | 초심자용 의미 |
|---|---|---|
| 1단계 | SQL 로그 | "insert는 나갔는가, batch 흔적도 같이 보이는가"를 본다 |
| 2단계 | Hibernate statistics | "한 번 실행된 배치가 몇 번 있었는가"를 숫자로 본다 |
| 3단계 | integration test | 다음 변경에서도 batch가 깨지지 않는지 자동으로 감시한다 |

실무에서도 보통 이 순서로 확인하면 충분하다.
로그로 감을 잡고, 통계 숫자로 재확인하고, 마지막에 테스트로 고정한다.

### 1. SQL 로그로 가장 먼저 확인하기

가장 짧게는 SQL 로그로 아래처럼 확인할 수 있다.

| 보고 싶은 것 | 예시 로그 | 초심자용 해석 |
|---|---|---|
| insert SQL가 반복된다 | `insert into coupon_issue ...` | 저장 시도 자체는 있었다 |
| 같은 구간에 batch 실행 로그가 보인다 | `executing batch size: 50` | Hibernate/JDBC가 여러 건을 묶어 보냈다는 뜻이다 |
| insert만 잔뜩 있고 batch 흔적이 없다 | `insert into ...`만 한 줄씩 계속 보인다 | 설정, `IDENTITY`, 중간 flush 때문에 기대한 batch가 안 걸렸을 수 있다 |

예를 들면 쿠폰 120건 저장에서 로그를 이렇게 읽는다.

```text
insert into coupon_issue ...
insert into coupon_issue ...
executing batch size: 50
...
executing batch size: 50
...
executing batch size: 20
```

이 경우 초심자 기준 해석은 충분히 단순하다.

- 120건이 `50 + 50 + 20`으로 나뉘어 batch 전송됐다
- 즉 `hibernate.jdbc.batch_size=50` 근처로 실제 적용된 흔적이 보인다
- 반대로 `insert` 로그만 120번 보이고 batch 실행 흔적이 없으면 "설정은 켰지만 적용은 안 됐을 수 있다" 쪽으로 다시 확인해야 한다

초심자에게 특히 유용한 포인트는 "무엇이 안 보이는지도 힌트"라는 점이다.

## 배치가 실제로 적용됐는지 어떻게 확인하나 (계속 2)

| 로그에서 본 장면 | 먼저 드는 의심 |
|---|---|
| `insert`만 길게 반복되고 batch 실행 흔적이 없다 | `IDENTITY`, 너무 잦은 `flush()`, batch 설정 누락 |
| insert와 update가 섞여 계속 번갈아 나온다 | 같은 모양 SQL이 모이지 못해 batch 효과가 줄었을 수 있다 |
| 기대보다 작은 크기로 여러 번 batch가 끊긴다 | 중간 flush, chunk 크기, cascade 타이밍을 다시 본다 |

배치 로그는 버전과 로깅 설정에 따라 문구가 조금 다를 수 있다.
중요한 것은 정확한 문자열 암기가 아니라, **"SQL이 한 건씩만 보이는지"와 "묶어서 보내는 흔적이 추가로 보이는지"**를 같이 읽는 습관이다.

### 2. Hibernate statistics로 숫자 확인하기

로그가 길거나 팀마다 로그 포맷이 다르면, Hibernate statistics가 더 안정적인 두 번째 근거가 된다.
초심자 기준으로는 모든 수치를 다 볼 필요 없이 아래 두 줄만 기억하면 된다.

- prepared statement 수: SQL이 얼마나 잘게 쪼개졌는지 보는 힌트
- batch execution 수: 실제 batch 실행이 있었는지 보는 힌트

예를 들어 테스트나 로컬 확인에서 statistics를 켜는 모양은 아래처럼 잡을 수 있다.

```properties
spring.jpa.properties.hibernate.generate_statistics=true
logging.level.org.hibernate.stat=debug
```

코드에서 직접 보는 경우에도 질문은 단순하다.

```java
SessionFactory sessionFactory = entityManagerFactory.unwrap(SessionFactory.class);
Statistics statistics = sessionFactory.getStatistics();
statistics.clear();

couponIssueWriter.writeChunk(issues120);

long batchExecutions = statistics.getBatchExecutionCount();
long preparedStatements = statistics.getPrepareStatementCount();
```

이 숫자는 이렇게 읽으면 된다.

| 숫자 | 초심자용 해석 |
|---|---|
| `batchExecutionCount > 0` | 적어도 batch가 한 번 이상 실제 실행됐다 |
| `batchExecutionCount == 0` | 설정은 있어도 실제 전송은 batch가 아닐 수 있다 |
| `prepareStatementCount`가 기대보다 너무 크다 | SQL이 잘게 나갔거나 같은 문장이 충분히 모이지 않았을 수 있다 |

## 배치가 실제로 적용됐는지 어떻게 확인하나 (계속 3)

여기서도 주의점은 같다.
`batchExecutionCount > 0`이 곧 "항상 최적"을 뜻하지는 않는다.
초심자에게 더 중요한 질문은 "아예 batch가 안 되는 상태는 아닌가"를 먼저 잡는 것이다.

### 3. 간단한 integration test로 회귀 막기

한 번 확인하고 끝내면 다음 리팩터링에서 쉽게 깨진다.
그래서 가장 작은 고정 장치로 integration test 하나를 두는 편이 좋다.

초심자용 테스트 목표는 거창하지 않아도 된다.

1. 여러 건 저장을 실제로 실행한다.
2. flush를 일으킨다.
3. statistics나 관찰 가능한 로그 기준으로 "batch가 0은 아니다"를 확인한다.

예시는 아래 정도면 충분하다.

```java
@DataJpaTest
@TestPropertySource(properties = {
        "spring.jpa.properties.hibernate.jdbc.batch_size=50",
        "spring.jpa.properties.hibernate.order_inserts=true",
        "spring.jpa.properties.hibernate.generate_statistics=true"
})
class CouponIssueBatchWriterTest {

    @Autowired
    private EntityManagerFactory entityManagerFactory;

    @Autowired
    private CouponIssueBatchWriter writer;

    @Test
    void batches_insert_when_writing_many_issues() {
        SessionFactory sessionFactory = entityManagerFactory.unwrap(SessionFactory.class);
        Statistics statistics = sessionFactory.getStatistics();
        statistics.clear();

        writer.writeChunk(issueFixtures(120));

        assertThat(statistics.getBatchExecutionCount()).isGreaterThan(0);
    }
}
```

이 테스트가 주는 장점은 단순하다.

- `saveAll()`을 썼는지보다 실제 실행 결과를 본다
- 누군가 `IDENTITY` 전략으로 바꾸거나 중간 `flush()`를 늘렸을 때 신호를 받을 수 있다
- "batch 설정은 있는데 진짜 적용은 안 됨" 상태를 초심자도 자동으로 잡기 쉽다

더 욕심내고 싶어도 첫 테스트는 아래 선에서 멈추는 편이 좋다.

## 배치가 실제로 적용됐는지 어떻게 확인하나 (계속 4)

| 첫 테스트에서 해도 되는 것 | 아직 굳이 안 해도 되는 것 |
|---|---|
| `batchExecutionCount > 0` 확인 | 배치 실행 횟수를 너무 빡빡하게 `== 3`으로 고정 |
| insert 위주의 한 경로 smoke 확인 | 로그 문구 전체를 문자열로 비교 |
| 120건, batch size 50처럼 이해하기 쉬운 숫자 사용 | provider 버전 차이에 민감한 세부 수치 모두 검증 |

즉 초심자용 integration test는 "정확한 내부 구현 복제"가 아니라, **batch가 완전히 사라졌는지 감시하는 얇은 안전망**이면 충분하다.

### 4. 가장 작은 실전 확인 루프

실제로 확인할 때는 아래 네 줄만 따라가면 된다.

1. `batch_size`와 ID 전략을 먼저 본다.
2. 100건 안팎의 단순 insert 시나리오를 만든다.
3. SQL 로그 또는 statistics에서 `batchExecutionCount > 0`인지 본다.
4. 그다음에만 flush 주기와 성능 수치를 조정한다.

이 순서를 건너뛰고 곧바로 service API를 `saveAll()`로 바꾸면, 초심자는 "계약 변경"과 "ORM 최적화"를 다시 섞기 쉽다.

## 자주 하는 오해

- "`saveAll()`만 쓰면 Hibernate batch가 된다"
  - 아니다. ID 전략, flush 시점, SQL 모양, provider 설정이 함께 맞아야 한다.
- "`saveAll`을 port로 올리면 batch 설계가 끝난다"
  - 아니다. 대부분은 ORM 최적화만 필요한 상태다. 진짜 batch 업무라면 `Chunk`, `RunId`, `Result` 같은 이름 있는 계약이 필요하다.
- "`flush()`는 commit이랑 같다"
  - 아니다. flush는 SQL 반영 시점이고, commit은 트랜잭션 확정 시점이다.
- "`IDENTITY`면 JPA batch를 전혀 못 쓴다"
  - 너무 강한 말이다. 특히 insert batching 기대가 크게 낮아진다고 이해하는 편이 정확하다.
- "batch size는 클수록 무조건 좋다"
  - 아니다. 메모리, lock 시간, flush 주기와 같이 봐야 한다.
- "성능 이슈가 보이면 port부터 bulk로 바꿔야 한다"
  - 아니다. 먼저 adapter 내부 최적화인지, 진짜 업무 계약 승격인지부터 구분해야 한다.

## 기억할 기준

- `hibernate.jdbc.batch_size`는 업무 계약이 아니라 ORM 속도 레버다
- `flush()`와 `clear()`는 영속성 컨텍스트 관리 규칙이지 도메인 규칙이 아니다
- insert batch를 보고 있다면 ID 생성 전략을 먼저 확인하는 편이 빠르다
- 진짜 batch 업무 개념이 없다면 port는 도메인 언어를 유지하고, JPA batch는 adapter 안에 숨기는 쪽이 안전하다

## 한 줄 정리

`hibernate.jdbc.batch_size`를 켰다고 자동으로 대량 저장이 빨라지는 것은 아니며, `flush` 타이밍, `IDENTITY` 키 생성 방식, 그리고 "이게 배치 업무 계약인가 아니면 ORM 최적화인가"를 분리해서 봐야 초심자가 덜 헷갈린다.
