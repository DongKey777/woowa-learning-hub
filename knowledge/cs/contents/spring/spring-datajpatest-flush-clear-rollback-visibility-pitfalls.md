# Spring `@DataJpaTest` Flush / Clear / Rollback Visibility Pitfalls

> 한 줄 요약: `@DataJpaTest`는 빠르고 유용하지만 기본 트랜잭션과 persistence context가 DB 현실을 일부 가려 주므로, flush/clear 없이 쓰면 제약 조건·bulk update·매핑 오류를 늦게 보게 될 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Test Slices와 Context Caching](./spring-test-slices-context-caching.md)
> - [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md)
> - [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
> - [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)
> - [Spring Testcontainers Boundary Strategy](./spring-testcontainers-boundary-strategy.md)

retrieval-anchor-keywords: DataJpaTest, TestEntityManager, flush clear test, repository test visibility, transactional rollback test, JPA slice stale state, persistence context illusion, constraint violation test

## 핵심 개념

`@DataJpaTest`는 repository와 JPA 매핑을 빠르게 검증하기에 아주 좋다.

하지만 기본적으로 다음 전제를 가진다.

- 테스트 메서드가 트랜잭션 안에서 실행되기 쉽다
- 끝나면 롤백된다
- 같은 persistence context가 테스트 전체에 걸쳐 살아 있을 수 있다

그래서 자주 생기는 오해는 이렇다.

- "다시 조회했으니 DB까지 확인한 거겠지"
- "예외가 안 났으니 제약 조건도 문제 없겠지"
- "bulk update 결과를 바로 읽었으니 최신 상태겠지"

실제로는 그렇지 않을 수 있다.

`@DataJpaTest`의 핵심 함정은 느린 것이 아니라, **managed state가 DB 현실을 잠시 가려 줄 수 있다는 점**이다.

## 깊이 들어가기

### 1. repository 테스트에서도 메모리 상태와 DB 상태를 구분해야 한다

같은 트랜잭션 안에서 저장 후 곧바로 조회하면, DB를 새로 읽었다기보다 같은 persistence context의 managed 엔티티를 다시 본 것일 수 있다.

즉 다음 테스트는 의도보다 약할 수 있다.

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository orderRepository;

    @Test
    void saveAndFind() {
        Order order = orderRepository.save(new Order("PAID"));
        Order found = orderRepository.findById(order.getId()).orElseThrow();
        assertThat(found.getStatus()).isEqualTo("PAID");
    }
}
```

이 테스트는 기본 동작 확인에는 좋지만,

- 실제 flush 시 SQL이 잘 나가는지
- DB 제약 조건이 통과하는지
- clear 후에도 조회 결과가 맞는지

까지는 충분히 검증하지 못할 수 있다.

### 2. flush는 DB 제약과 SQL 타이밍을 앞당겨 드러낸다

`@DataJpaTest`에서 중요한 버그 중 일부는 commit 시점까지 숨어 있다.

- unique constraint 위반
- foreign key 위반
- not null 위반
- SQL 생성 문제

이런 경우 테스트 중간에 flush를 넣으면 문제를 더 빨리 드러낼 수 있다.

```java
orderRepository.save(order);
testEntityManager.flush();
```

핵심은 flush가 테스트를 "느리게 만드는 옵션"이 아니라, **실제 DB 상호작용을 더 명확하게 드러내는 장치**라는 점이다.

### 3. clear는 managed illusion을 걷어낸다

bulk update나 dirty checking이 얽히면, 같은 persistence context 안에서 다시 읽는 것만으로는 stale state를 발견하기 어렵다.

이때 clear가 유용하다.

```java
testEntityManager.flush();
testEntityManager.clear();
```

이후 조회는 현재 메모리의 managed 객체가 아니라, DB에서 다시 읽어 온 상태에 더 가까워진다.

즉 repository 테스트에서 clear는 "메모리 초기화"가 아니라, **진짜 DB 가시성을 보려는 의도적 경계 설정**이다.

### 4. bulk update와 native query는 특히 flush/clear 감각이 중요하다

JPQL bulk update나 native SQL은 current persistence context와 엇갈리기 쉽다.

테스트에서 이를 바로 읽으면 다음이 생길 수 있다.

- 업데이트 count는 맞는데 엔티티 상태는 예전처럼 보임
- native insert 후 조회가 기대와 다르게 보임

이 경우는 JPA가 틀린 게 아니라, 테스트가 아직 **같은 persistence context 안에 갇혀 있는 것**일 수 있다.

### 5. rollback 기본값은 편하지만 commit 기반 검증을 약하게 만든다

`@DataJpaTest`의 기본 롤백은 테스트 격리에 좋다.

하지만 commit 이후에만 드러나는 문제에는 약하다.

- DB trigger / commit hook
- after-commit side effect
- 실제 트랜잭션 경계 밖에서 보이는 결과

이런 종류는 `@DataJpaTest`만으로 충분하지 않을 수 있다.

즉 중요한 질문은 "`@DataJpaTest`가 되느냐"가 아니라, **검증하려는 현상이 rollback 이전에 드러나는 종류인가**다.

### 6. slice가 적합한 문제와 아닌 문제를 구분해야 한다

`@DataJpaTest`가 잘 맞는 것:

- repository query
- entity mapping
- cascade/orphan removal 일부
- flush 시 제약 조건

`@DataJpaTest`만으로는 약한 것:

- 실제 복제 지연/락 경합
- 여러 transaction manager 경계
- after-commit 비동기 후속 처리
- 운영 DB 전용 동작

이 경우는 Testcontainers나 더 넓은 integration test가 맞을 수 있다.

## 실전 시나리오

### 시나리오 1: 테스트는 통과하는데 운영에서 unique 제약이 터진다

테스트가 flush 없이 끝나 실제 SQL 시점을 충분히 보지 못했을 수 있다.

### 시나리오 2: bulk update 테스트가 이상하게 옛값을 읽는다

업데이트가 실패한 게 아니라, persistence context가 stale 상태일 수 있다.

flush/clear 후 다시 읽어 봐야 한다.

### 시나리오 3: repository 테스트에서 `save()`가 잘 되는 것 같은데 실제 update 의도는 잘못됐다

같은 persistence context 안에서 managed state만 보고 있어 merge/persist 경로 오해가 숨었을 수 있다.

### 시나리오 4: `@DataJpaTest`로 after-commit 동작까지 검증하려 한다

기본 rollback과 slice 경계 때문에 그 계약은 충분히 보지 못할 수 있다.

## 코드로 보기

### flush로 제약 조건 확인

```java
@DataJpaTest
class UserRepositoryTest {

    @Autowired UserRepository userRepository;
    @Autowired TestEntityManager testEntityManager;

    @Test
    void duplicateEmailFailsOnFlush() {
        userRepository.save(new User("a@test.com"));
        userRepository.save(new User("a@test.com"));

        assertThatThrownBy(() -> testEntityManager.flush())
            .isInstanceOf(Exception.class);
    }
}
```

### clear 후 재조회

```java
testEntityManager.flush();
testEntityManager.clear();

Order reloaded = orderRepository.findById(orderId).orElseThrow();
```

### bulk update 후 stale state 제거

```java
orderRepository.bulkExpire(today);
testEntityManager.clear();
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 기본 `@DataJpaTest`만 사용 | 빠르고 단순하다 | DB 현실이 일부 가려질 수 있다 | 기본 repository 계약 |
| flush 추가 | 제약 조건과 SQL 시점을 빨리 본다 | 테스트가 조금 더 장황해진다 | insert/update 검증 |
| flush + clear 추가 | DB 재조회 의미가 분명해진다 | 보일러플레이트가 늘어난다 | stale state, bulk update 검증 |
| 더 넓은 통합 테스트 | 실제와 가깝다 | 느리고 비용이 크다 | commit 이후 효과나 운영 DB 특성이 중요할 때 |

핵심은 `@DataJpaTest`를 믿지 말라는 게 아니라, **무엇이 persistence context 착시이고 무엇이 실제 DB 검증인지 의식적으로 분리하라**는 것이다.

## 꼬리질문

> Q: `@DataJpaTest`에서 save 후 바로 조회한 값이 왜 DB 검증과 같지 않을 수 있는가?
> 의도: managed state vs DB state 구분 확인
> 핵심: 같은 persistence context의 managed 엔티티를 다시 본 것일 수 있기 때문이다.

> Q: repository 테스트에 flush를 넣는 이유는 무엇인가?
> 의도: SQL 시점과 제약 조건 검증 이해 확인
> 핵심: 실제 DB 상호작용과 제약 조건 오류를 더 이른 시점에 드러내기 위해서다.

> Q: clear는 어떤 착시를 걷어내는가?
> 의도: stale state 인식 확인
> 핵심: 메모리에 남아 있는 managed 상태를 끊고 DB 재조회 의미를 분명하게 만든다.

> Q: `@DataJpaTest`만으로 after-commit 동작을 충분히 보기 어려운 이유는 무엇인가?
> 의도: slice 한계 이해 확인
> 핵심: 기본 트랜잭션/롤백 경계가 commit 이후 계약을 약하게 만들 수 있기 때문이다.

## 한 줄 정리

좋은 `@DataJpaTest`는 save-and-find가 아니라, 필요한 순간 flush/clear를 써서 persistence context 착시와 실제 DB 검증을 분리해 내는 테스트다.
