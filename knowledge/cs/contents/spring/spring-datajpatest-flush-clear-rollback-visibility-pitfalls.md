# Spring `@DataJpaTest` Mental-Model Bridge: 런타임 트랜잭션 감각을 테스트에 그대로 옮기기

> 한 줄 요약: 런타임에서 "지금 메모리 상태를 보는가, DB에 실제 반영된 상태를 보는가"를 구분하듯, `@DataJpaTest`에서도 `flush`, `clear`, rollback 경계를 구분해야 save-and-find 착시에 덜 속는다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Persistence / Transaction Mental Model Primer: Web, Service, Repository를 한 장으로 묶기](./spring-persistence-transaction-web-service-repository-primer.md)
> - [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
> - [Spring `@DataJpaTest` Bulk Update Stale-State Mini Guide](./spring-datajpatest-bulk-update-stale-state-mini-guide.md)
> - [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](./spring-after-commit-rollback-slice-test-mini-card.md)
> - [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md)
> - [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)

retrieval-anchor-keywords: datajpatest beginner, datajpatest mental model bridge, datajpatest flush clear rollback, save and find illusion, persistence context test trap, testentitymanager beginner, repository test db visibility, transactional test rollback beginner, datajpatest stale state, bulk update clear test, junior jpa test primer, flush commit difference test, rollback test vs commit path, commit visible behavior test, datajpatest enough when

## 먼저 mental model 한 줄

초급자는 `@DataJpaTest`를 이렇게 보면 덜 헷갈린다.

```text
런타임 service 트랜잭션 안에서
엔티티 변경은 먼저 persistence context에 잡히고
필요할 때 flush로 SQL이 나가고
트랜잭션이 끝나면 commit 또는 rollback 된다

@DataJpaTest도 거의 같은 그림인데
기본값이 "테스트 끝나면 rollback"이라서
"다시 조회했으니 DB를 확인했다"는 착시가 더 쉽게 생긴다
```

핵심 문장은 이것 하나면 충분하다.

**`@DataJpaTest`는 운영과 다른 세계가 아니라, rollback이 붙은 작은 트랜잭션 실험실이다.**

## 런타임 감각을 테스트로 번역하면

| 런타임에서 보는 질문 | `@DataJpaTest`에서 같은 질문 |
|---|---|
| 지금 객체만 바뀐 건가, DB SQL까지 나간 건가? | `flush()` 전인가 후인가? |
| 지금 보는 값이 같은 persistence context의 managed 상태인가? | `clear()` 없이 다시 조회한 값인가? |
| 최종 commit 뒤 다른 곳에서 볼 수 있는 결과인가? | 테스트 종료 rollback 전에만 보이는 값인가? |

즉 `@DataJpaTest`에서 헷갈리는 이유는 새 개념이 많아서가 아니다.
런타임에서 이미 있던 트랜잭션 규칙을 테스트에서 잠깐 잊기 쉽기 때문이다.

## 가장 흔한 착시 3개

### 1. save 후 바로 find 했으니 DB 검증까지 끝났다고 느낀다

```java
Order order = orderRepository.save(new Order("PAID"));
Order found = orderRepository.findById(order.getId()).orElseThrow();
```

이 코드는 유효한 기본 테스트다. 다만 초급자가 여기서 곧바로 "DB까지 정상"이라고 결론 내리면 너무 빨리 간 것이다.

왜냐하면 `found`가 다음일 수 있기 때문이다.

- 같은 트랜잭션 안의 같은 persistence context가 들고 있던 managed 엔티티
- flush 전이라 아직 SQL로 강하게 검증되지 않은 상태

짧게 말하면, **다시 조회했어도 아직 "메모리 재확인"에 더 가까울 수 있다.**

### 2. 예외가 안 났으니 제약 조건도 괜찮다고 느낀다

unique, foreign key, not null 같은 제약은 보통 실제 SQL이 나갈 때 더 분명해진다.

그래서 아래 테스트는 의도보다 약할 수 있다.

```java
userRepository.save(new User("a@test.com"));
userRepository.save(new User("a@test.com"));
```

이 순간에 바로 예외가 안 났다고 해서, DB 제약이 안전하다고 단정하면 안 된다.
초급자 기준으로는 **"예외 검증을 하고 싶으면 flush로 SQL 시점을 앞으로 당긴다"**고 기억하면 된다.

### 3. bulk update 뒤 다시 읽었으니 최신 상태라고 느낀다

bulk update는 DB를 직접 건드렸는데, 현재 persistence context는 예전 엔티티를 계속 들고 있을 수 있다.

그래서 다음처럼 보일 수 있다.

- update count는 맞다
- 그런데 다시 읽은 엔티티 상태는 옛값 같다

이때 JPA가 틀린 게 아니라, **테스트가 아직 같은 persistence context 안에서만 돌고 있는 것**일 수 있다.

## `flush`, `clear`, rollback을 초급자 언어로 다시 묶기

| 개념 | 초급자용 해석 | `@DataJpaTest`에서 언제 떠올리나 |
|---|---|---|
| `flush()` | "이제 SQL 한번 보내 보자" | 제약 조건, insert/update SQL, DB 반응을 빨리 보고 싶을 때 |
| `clear()` | "지금 들고 있는 managed 상태를 내려놓자" | save-and-find 착시, bulk update stale state를 끊고 싶을 때 |
| rollback | "테스트가 끝나면 대부분 되돌린다" | commit 이후 효과까지 검증하는 테스트가 아니라는 점을 확인할 때 |

짧게 외우면 이렇다.

- `flush`는 DB와 동기화 타이밍을 당긴다.
- `clear`는 메모리 착시를 걷어낸다.
- rollback은 테스트 격리를 돕지만 commit 검증을 대신하지 않는다.

## 제일 작은 브리지 예제

### 1. save-and-find 기본형

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository orderRepository;

    @Test
    void save_and_find() {
        Order order = orderRepository.save(new Order("PAID"));

        Order found = orderRepository.findById(order.getId()).orElseThrow();

        assertThat(found.getStatus()).isEqualTo("PAID");
    }
}
```

이 테스트가 틀렸다는 뜻은 아니다.
이 테스트가 강하게 보장하는 것은 "repository 기본 흐름" 쪽이고, "DB 현실까지 충분히 드러냈다"는 쪽은 아니다.

### 2. flush를 넣어 DB 반응을 앞으로 당기기

```java
@DataJpaTest
class UserRepositoryTest {

    @Autowired UserRepository userRepository;
    @Autowired TestEntityManager testEntityManager;

    @Test
    void duplicate_email_fails_on_flush() {
        userRepository.save(new User("a@test.com"));
        userRepository.save(new User("a@test.com"));

        assertThatThrownBy(() -> testEntityManager.flush())
            .isInstanceOf(Exception.class);
    }
}
```

초급자 해석은 단순하다.

- `save()` 두 번은 아직 "변경을 모아 둔 상태"일 수 있다
- `flush()`는 "이제 DB에 물어보자"에 가깝다
- 그래서 제약 조건 예외를 더 이른 시점에 볼 수 있다

### 3. clear를 넣어 DB 재조회 의미를 분명하게 만들기

```java
testEntityManager.flush();
testEntityManager.clear();

Order reloaded = orderRepository.findById(orderId).orElseThrow();
```

초급자 기준으로 `clear()`는 "초기화 버튼"보다 아래 의미로 이해하는 편이 좋다.

**"이제부터는 방금 메모리에 들고 있던 객체 말고, 다시 읽은 결과를 보자."**

## 언제 어떤 패턴을 쓰면 되나

| 테스트 목적 | 추천 기본값 |
|---|---|
| repository 메서드가 대체로 동작하는지 빠르게 확인 | 기본 `@DataJpaTest` |
| unique / FK / not null 같은 제약을 테스트 중간에 확인 | `save` 후 `flush()` |
| bulk update 뒤 옛값 착시를 피하고 싶음 | `flush()` 후 `clear()` 또는 최소 `clear()` |
| commit 이후에만 보이는 효과를 확인 | `@DataJpaTest`만으로 충분한지 다시 점검 |

여기서 중요한 건 "무조건 flush/clear를 넣어라"가 아니다.
**무엇을 검증하려는지에 맞춰 경계를 하나씩 드러내라**는 것이다.

## 초급자용 비교 카드: 언제 `@DataJpaTest` rollback으로 충분하고, 언제 더 넓혀야 하나

먼저 아주 짧게 자르면 이렇다.

- "같은 트랜잭션 안에서 repository와 매핑이 맞는가?"를 보면 `@DataJpaTest`가 먼저다.
- "commit이 끝난 뒤 다른 경계에서 보이는 결과인가?"를 보면 더 넓은 테스트를 고려한다.

| 확인하려는 것 | 기본 선택 | 이유 |
|---|---|---|
| 엔티티 매핑, repository query, 제약 조건 flush 시점 | `@DataJpaTest` | 같은 트랜잭션 안 검증이면 충분한 경우가 많다 |
| save 후 재조회, bulk update 후 stale state 제거 | `@DataJpaTest` + 필요 시 `flush/clear` | persistence context 착시를 벗기면 목적에 맞다 |
| 서비스 메서드가 여러 repository를 함께 묶는지 | 더 넓은 서비스 통합 테스트 검토 | repository slice만으로는 유스케이스 경계가 다 안 보일 수 있다 |
| `afterCommit`, 이벤트 발행, outbox 적재 후 relay, 별도 트랜잭션 효과 | commit-visible 경로가 보이는 더 넓은 테스트 | rollback 기본값 테스트로는 "커밋 후 세계"를 직접 못 본다 |
| 다른 트랜잭션/다른 스레드/외부 소비자가 볼 결과 | commit-visible 경로가 보이는 더 넓은 테스트 | "테스트 안에서 보였다"와 "커밋 뒤 남는다"는 다르다 |

초급자는 아래 질문 두 개로 먼저 자르면 된다.

1. 지금 확인하려는 결과가 **테스트 트랜잭션 안에서만 보이면 충분한가?**
2. 아니면 **commit이 끝난 뒤 다른 경계에서도 보여야 정답인가?**

2번이면 `@DataJpaTest`를 버리라는 뜻이 아니다.
보통은 `@DataJpaTest`로 repository 감각을 먼저 검증하고, commit-visible 위험이 큰 경로만 더 넓은 테스트로 보강하면 된다.

### 빠른 예시

| 상황 | 어디까지면 충분한가 |
|---|---|
| 이메일 unique 제약이 flush 시점에 터지는지 확인 | `@DataJpaTest`로 충분한 경우가 많다 |
| 주문 저장 후 `AFTER_COMMIT` 이벤트로 메일 발송/아웃박스 릴레이가 이어지는지 확인 | commit-visible 경로를 보는 더 넓은 테스트가 필요하다 |
| JPQL bulk update 후 조회 착시를 없애고 싶은지 확인 | `@DataJpaTest`에서 `clear()`까지 보면 충분한 경우가 많다 |
| 서비스 유스케이스가 commit 후 다른 트랜잭션에서 바로 읽히는지 확인 | 더 넓은 테스트가 맞다 |

## 자주 하는 오해

- "`findById()`를 다시 했으니 무조건 DB를 새로 읽었다"가 아니다.
- "`flush()` 했으니 commit까지 끝났다"가 아니다.
- "`@DataJpaTest`는 rollback하니까 운영과 너무 달라서 쓸모없다"가 아니다.
- "`@DataJpaTest`가 통과했으니 after-commit 동작도 안전하다"가 아니다.

`@DataJpaTest`는 여전히 아주 유용하다.
다만 초급자는 이 테스트를 **"DB와 완전히 분리된 가짜 환경"**으로 보지 말고, **"rollback이 걸린 트랜잭션 안에서 persistence context 착시가 더 잘 보이는 환경"**으로 보는 편이 훨씬 정확하다.

## 어디로 이어서 보면 좋나

| 지금 막히는 질문 | 다음 문서 |
|---|---|
| "`flush`와 commit 차이를 더 정확히 알고 싶다" | [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md) |
| "bulk update 뒤에 왜 옛값처럼 보이는지 예제로 보고 싶다" | [Spring `@DataJpaTest` Bulk Update Stale-State Mini Guide](./spring-datajpatest-bulk-update-stale-state-mini-guide.md) |
| "`AFTER_COMMIT`은 왜 이 테스트만으로 다 못 보나" | [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](./spring-after-commit-rollback-slice-test-mini-card.md) |
| "`@Transactional` 큰 그림부터 다시 잡고 싶다" | [Spring Persistence / Transaction Mental Model Primer](./spring-persistence-transaction-web-service-repository-primer.md) |
| "테스트 rollback이 왜 만능이 아닌가" | [Spring Transactional Test Rollback Misconceptions](./spring-transactional-test-rollback-misconceptions.md) |
| "`save`, `persist`, `merge`가 헷갈린다" | [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md) |

## 꼬리질문

> Q: `@DataJpaTest`에서 save 후 바로 다시 조회한 값은 왜 DB 검증과 완전히 같지 않을 수 있는가?
> 의도: managed state와 DB state 구분 확인
> 핵심: 같은 persistence context가 들고 있던 managed 엔티티를 다시 본 것일 수 있기 때문이다.

> Q: repository 테스트에 `flush()`를 넣는 가장 실용적인 이유는 무엇인가?
> 의도: SQL 시점과 제약 조건 검증 이해 확인
> 핵심: 실제 DB 반응과 제약 조건 오류를 테스트 중간에 더 빨리 드러내기 위해서다.

> Q: `clear()`를 넣으면 무엇이 달라지나?
> 의도: persistence context 착시 제거 확인
> 핵심: 메모리에 남아 있던 managed 상태를 끊고, 다시 읽은 결과의 의미를 더 분명하게 만든다.

> Q: `@DataJpaTest`의 기본 rollback이 편리하면서도 한계가 있는 이유는 무엇인가?
> 의도: 테스트 격리와 commit 검증 한계 구분 확인
> 핵심: 테스트 격리에는 좋지만 commit 이후에만 드러나는 효과를 대신 검증해 주지는 않기 때문이다.

## 한 줄 정리

좋은 `@DataJpaTest`는 "save하고 다시 읽어도 맞네"에서 멈추지 않고, 필요할 때 `flush`, `clear`, rollback 경계를 드러내서 런타임 트랜잭션 감각과 테스트 해석을 연결해 주는 테스트다.
