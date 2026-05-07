---
schema_version: 3
title: IDENTITY vs SEQUENCE Batch Verification Example
concept_id: software-engineering/identity-sequence-batch-verification
canonical: true
category: software-engineering
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- jpa
- batch
- identity
- sequence
aliases:
- IDENTITY vs SEQUENCE Batch Verification Example
- identity sequence batch verification
- GenerationType IDENTITY SEQUENCE batching
- JPA identity sequence insert test
- batchExecutionCount identity sequence
- identity 먼저 넣고 sequence 키 먼저
symptoms: []
intents:
- comparison
- troubleshooting
- definition
prerequisites:
- software-engineering/jpa-batch-config-pitfalls
- software-engineering/datajpatest-flush-clear
next_docs:
- software-engineering/datasource-proxy-vs-statistics
- software-engineering/jpa-batch-config-pitfalls
- software-engineering/persistence-follow-up-question-guide
linked_paths:
- contents/software-engineering/jpa-batch-config-pitfalls.md
- contents/software-engineering/datajpatest-flush-clear-batch-checklist.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/persistence-follow-up-question-guide.md
- contents/software-engineering/datasource-proxy-vs-hibernate-statistics-query-count-batch-primer.md
confusable_with:
- software-engineering/jpa-batch-config-pitfalls
- software-engineering/datajpatest-flush-clear
- software-engineering/datasource-proxy-vs-statistics
forbidden_neighbors: []
expected_queries:
- JPA IDENTITY와 SEQUENCE 전략이 insert batching 검증에서 다르게 보이는 이유를 초심자에게 설명해줘
- GenerationType.IDENTITY는 왜 insert 전에 PK를 몰라 batchExecutionCount가 0으로 보일 수 있어?
- SEQUENCE allocationSize를 쓰면 같은 save 루프에서 batch 실행 흔적이 더 잘 보이는 이유가 뭐야?
- count() 테스트와 batchExecutionCount 테스트가 서로 다른 것을 검증한다는 점을 알려줘
- DataJpaTest에서 IDENTITY와 SEQUENCE를 비교해 batch 적용 여부를 확인하는 예시가 필요해
contextual_chunk_prefix: |
  이 문서는 software-engineering 카테고리에서 IDENTITY vs SEQUENCE Batch Verification Example를 다루는 chooser 문서다. IDENTITY vs SEQUENCE Batch Verification Example, identity sequence batch verification, GenerationType IDENTITY SEQUENCE batching, JPA identity sequence insert test, batchExecutionCount identity sequence 같은 lexical 표현과 JPA IDENTITY와 SEQUENCE 전략이 insert batching 검증에서 다르게 보이는 이유를 초심자에게 설명해줘, GenerationType.IDENTITY는 왜 insert 전에 PK를 몰라 batchExecutionCount가 0으로 보일 수 있어? 같은 자연어 질문을 같은 개념으로 묶어, 학습자가 증상, 비교, 설계 판단, 코드리뷰 맥락 중 어디에서 들어오더라도 본문의 핵심 분기와 다음 문서로 안정적으로 이어지게 한다.
---
# IDENTITY vs SEQUENCE Batch Verification Example

> 한 줄 요약: 같은 insert 테스트라도 `IDENTITY`는 "먼저 넣고 키를 받는 흐름"이라 batch 검증이 약해지기 쉽고, `SEQUENCE`는 "키를 먼저 확보하고 모아 넣는 흐름"이라 같은 테스트에서 batch 실행 흔적이 더 잘 드러난다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../spring/spring-request-pipeline-bean-container-foundations-primer.md)


retrieval-anchor-keywords: identity vs sequence batch verification example basics, identity vs sequence batch verification example beginner, identity vs sequence batch verification example intro, software engineering basics, beginner software engineering, 처음 배우는데 identity vs sequence batch verification example, identity vs sequence batch verification example 입문, identity vs sequence batch verification example 기초, what is identity vs sequence batch verification example, how to identity vs sequence batch verification example
<details>
<summary>Table of Contents</summary>

- [먼저 잡을 멘탈 모델](#먼저-잡을-멘탈-모델)
- [왜 같은 insert 테스트가 다르게 보이나](#왜-같은-insert-테스트가-다르게-보이나)
- [한 장 비교표](#한-장-비교표)
- [같은 테스트 준비: 바뀌는 것은 ID 전략뿐](#같은-테스트-준비-바뀌는-것은-id-전략뿐)
- [예시 1: `IDENTITY`일 때](#예시-1-identity일-때)
- [예시 2: `SEQUENCE`일 때](#예시-2-sequence일-때)
- [결과를 어떻게 읽어야 하나](#결과를-어떻게-읽어야-하나)
- [초심자가 자주 헷갈리는 지점](#초심자가-자주-헷갈리는-지점)
- [practice loop](#practice-loop)
- [관련 문서](#관련-문서)

</details>

> 관련 문서:
> - [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
> - [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
> - [Test Strategy Basics](./test-strategy-basics.md)
> - [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)
>
> retrieval-anchor-keywords: identity vs sequence batch verification, identity sequence insert test example, generationtype identity sequence batch primer, same insert test different result, jpa identity batching example, jpa sequence batching example, hibernate batch execution count example, datajpatest identity sequence comparison, identity 먼저 넣고 키 받기, sequence 키 먼저 받고 넣기, batch verification beginner, batchExecutionCount identity sequence, identity vs sequence statistics test, insert batching mental model, jpa beginner batch comparison, sequence allocationSize beginner, same writer different id strategy

## 먼저 잡을 멘탈 모델

초심자는 이 두 문장만 먼저 잡으면 된다.

- `IDENTITY`는 "row를 먼저 넣고 DB가 준 키를 받는다"에 가깝다.
- `SEQUENCE`는 "키를 먼저 확보하고 row를 넣는다"에 가깝다.

그래서 같은 `save()` 루프라도 batch 관점에서는 출발점이 다르다.

| 전략 | 초심자용 기억 문장 | batch insert에 미치는 첫 영향 |
|---|---|---|
| `IDENTITY` | 먼저 넣고 번호를 받는다 | insert를 길게 모아 두기 어려워질 수 있다 |
| `SEQUENCE` | 번호를 먼저 받고 넣는다 | insert를 모아 flush 시점에 보내기 쉬워진다 |

핵심은 "`SEQUENCE`면 무조건 빠르다"가 아니다.
**같은 테스트를 돌렸을 때 batch 흔적이 보이기 쉬운 출발 조건이 다르다**가 핵심이다.

## 왜 같은 insert 테스트가 다르게 보이나

초심자는 아래처럼 생각하기 쉽다.

- "둘 다 `save()`를 100번 했으니 테스트도 비슷하게 통과하겠지."

하지만 실제로는 assertion 종류에 따라 체감이 달라진다.

| 어떤 assertion인가 | `IDENTITY`와 `SEQUENCE`가 둘 다 통과하기 쉬운가 | 무엇을 놓칠 수 있나 |
|---|---|---|
| `count() == 100` | 대체로 예 | "저장은 됐지만 batch는 안 됨" 상태 |
| `flush()` 후 재조회 결과 확인 | 대체로 예 | batch 실행이 있었는지 자체는 약하다 |
| `batchExecutionCount > 0` 확인 | `SEQUENCE` 쪽이 더 유리 | `IDENTITY`에서는 0이 나와도 저장 자체는 성공할 수 있다 |

즉 이 문서의 포인트는 "무엇이 저장되었나"보다 **"같은 저장 테스트가 batch 적용 여부를 얼마나 잘 드러내나"**를 보는 것이다.

## 한 장 비교표

| 비교 질문 | `IDENTITY` | `SEQUENCE` |
|---|---|---|
| insert 전에 PK를 아는가 | 보통 어렵다 | 대체로 가능하다 |
| 같은 insert를 잠깐 모아 둘 수 있나 | 제약이 크다 | 상대적으로 쉽다 |
| `count()==N` 테스트 | 보통 통과 가능 | 보통 통과 가능 |
| `batchExecutionCount > 0` 테스트 | 실패하거나 약한 신호가 되기 쉽다 | 성공 신호가 더 잘 나온다 |
| 초심자용 결론 | 저장 성공과 batch 성공을 분리해서 봐야 한다 | batch 검증용 기준 예시로 쓰기 좋다 |

## 같은 테스트 준비: 바뀌는 것은 ID 전략뿐

아래 예시는 의도적으로 entity의 ID 전략만 바꾸고, writer와 test 구조는 최대한 같게 둔다.

```java
@DataJpaTest
@TestPropertySource(properties = {
        "spring.jpa.properties.hibernate.jdbc.batch_size=50",
        "spring.jpa.properties.hibernate.order_inserts=true",
        "spring.jpa.properties.hibernate.generate_statistics=true"
})
class CouponBatchVerificationTest {

    @Autowired
    EntityManagerFactory entityManagerFactory;

    @Autowired
    CouponWriter writer;

    Statistics statistics() {
        SessionFactory sessionFactory = entityManagerFactory.unwrap(SessionFactory.class);
        Statistics statistics = sessionFactory.getStatistics();
        statistics.clear();
        return statistics;
    }
}
```

writer도 똑같이 둔다.

```java
@Component
class CouponWriter {
    @PersistenceContext
    private EntityManager em;

    void write(List<String> codes) {
        for (String code : codes) {
            em.persist(new Coupon(code));
        }
        em.flush();
        em.clear();
    }
}
```

이제 바뀌는 것은 `Coupon`의 ID 전략뿐이다.

## 예시 1: `IDENTITY`일 때

```java
@Entity
class Coupon {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String code;

    protected Coupon() {
    }

    Coupon(String code) {
        this.code = code;
    }
}
```

테스트는 이렇게 쓸 수 있다.

```java
@Test
void identity_strategy_may_not_show_batch_execution() {
    Statistics statistics = statistics();

    writer.write(IntStream.range(0, 120)
            .mapToObj(i -> "code-" + i)
            .toList());

    assertThat(statistics.getEntityInsertCount()).isEqualTo(120);
    assertThat(statistics.getBatchExecutionCount()).isEqualTo(0);
}
```

초심자용 해석은 단순하다.

- 120건 insert 자체는 성공할 수 있다
- 하지만 batch 실행 흔적은 0일 수 있다
- 그래서 "`저장 성공`과 `batch 적용 성공`은 같은 말이 아니다"를 바로 보여 준다

여기서 숫자 `0`은 provider/DB 조합에 따라 표현이 달라질 수 있다.
중요한 것은 "`IDENTITY`에서는 같은 구조 테스트가 batch 성공 예시로는 약하다"는 점이다.

## 예시 2: `SEQUENCE`일 때

```java
@Entity
@SequenceGenerator(
        name = "coupon_seq",
        sequenceName = "coupon_seq",
        allocationSize = 50
)
class Coupon {
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "coupon_seq")
    private Long id;

    private String code;

    protected Coupon() {
    }

    Coupon(String code) {
        this.code = code;
    }
}
```

같은 writer, 같은 테스트 모양을 그대로 둔다.

```java
@Test
void sequence_strategy_can_surface_batch_execution() {
    Statistics statistics = statistics();

    writer.write(IntStream.range(0, 120)
            .mapToObj(i -> "code-" + i)
            .toList());

    assertThat(statistics.getEntityInsertCount()).isEqualTo(120);
    assertThat(statistics.getBatchExecutionCount()).isGreaterThan(0);
}
```

이 테스트는 초심자에게 두 가지를 보여 준다.

- insert 수는 `IDENTITY`와 똑같이 120이다
- 하지만 이번에는 batch 실행 흔적이 0보다 클 가능성이 높다

즉 **테스트 코드가 좋아진 것이 아니라, 같은 테스트가 batch를 드러내기 좋은 조건으로 바뀐 것**이다.

## 결과를 어떻게 읽어야 하나

같은 120건 insert 테스트를 읽을 때는 아래처럼 해석하면 된다.

| 관찰 결과 | 초심자용 해석 | 다음 질문 |
|---|---|---|
| 두 전략 모두 `count()==120` | 저장 자체는 된다 | batch까지 확인한 것은 맞나 |
| `IDENTITY`에서 `batchExecutionCount == 0` | 저장 성공과 batch 성공을 분리해서 봐야 한다 | 이 테스트 목표가 "저장"인가 "batch 검증"인가 |
| `SEQUENCE`에서 `batchExecutionCount > 0` | batch 실행이 아예 사라지지는 않았다 | flush 주기와 SQL 로그도 같이 볼까 |
| `SEQUENCE`인데도 batch가 0 | ID 전략 말고 다른 조건도 막고 있을 수 있다 | 중간 flush, SQL 모양 혼합, 설정 누락을 볼까 |

짧게 정리하면 이렇다.

- `IDENTITY`는 "왜 batch 검증 테스트가 기대처럼 안 보이지?"를 설명하는 예시다.
- `SEQUENCE`는 "같은 테스트에서 batch 흔적이 이렇게 보일 수 있다"를 설명하는 예시다.

## 초심자가 자주 헷갈리는 지점

| 흔한 오해 | 더 안전한 첫 판단 |
|---|---|
| `IDENTITY` 테스트가 초록이면 batch도 잘 됐다 | 저장 성공만 확인했을 수 있다 |
| `SEQUENCE`로 바꾸면 무조건 성능 문제가 해결된다 | batch를 가로막는 큰 조건 하나를 줄였을 뿐이다 |
| `batchExecutionCount > 0`이면 세부 최적화까지 끝났다 | "아예 0은 아니다"를 확인한 첫 단계에 가깝다 |
| `allocationSize=50`이면 항상 50개씩 정확히 묶인다 | provider와 flush 타이밍에 따라 실제 묶임은 달라질 수 있다 |
| 둘의 차이는 SQL 로그를 몰라도 감으로 알 수 있다 | statistics나 SQL 로그 같은 관찰 기준이 있어야 덜 헷갈린다 |

## practice loop

입문자는 아래 순서로 직접 비교해 보면 된다.

1. `count()==120`만 검증하는 insert 테스트를 먼저 만든다.
2. 같은 테스트에 statistics 확인을 추가해 "`저장 성공`과 `batch 성공`"을 분리한다.
3. entity의 ID 전략만 `IDENTITY`와 `SEQUENCE`로 바꿔 본다.
4. `SEQUENCE`에서도 batch가 0이면 `flush()` 위치와 설정을 다시 본다.

이 순서가 좋은 이유는 초심자가 성능 이야기부터 시작하지 않고, **"같은 테스트가 무엇을 보여 주는지"**부터 분리해서 볼 수 있기 때문이다.

## 관련 문서

- ID 전략 때문에 batch insert 기대치가 왜 달라지는지 먼저 이어 보고 싶다면: [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- `flush()`와 `clear()`가 테스트 의미를 어떻게 바꾸는지 같이 보고 싶다면: [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- 이 테스트를 `@DataJpaTest`로 시작할지, 더 큰 통합 테스트로 올릴지 고르고 싶다면: [Test Strategy Basics](./test-strategy-basics.md)
- JPA/영속성 주제에서 다음 질문을 어떻게 좁혀 갈지 보고 싶다면: [Persistence Follow-up Question Guide](./persistence-follow-up-question-guide.md)

## 한 줄 정리

같은 insert 테스트라도 `IDENTITY`는 "먼저 넣고 키를 받는 흐름"이라 batch 검증이 약해지기 쉽고, `SEQUENCE`는 "키를 먼저 확보하고 모아 넣는 흐름"이라 같은 테스트에서 batch 실행 흔적이 더 잘 드러난다.
