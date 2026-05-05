# Spring `@DataJpaTest` Bulk Update Stale-State Mini Guide

> 한 줄 요약: JPQL bulk update는 DB를 바로 바꾸지만 현재 persistence context 안의 엔티티는 그대로일 수 있어서, `@DataJpaTest`에서는 `clear()`나 재조회 경계를 의도적으로 드러내야 "왜 값이 안 바뀐 것처럼 보이지?" 착시를 줄일 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)
- [Spring `@DataJpaTest` Mental-Model Bridge: 런타임 트랜잭션 감각을 테스트에 그대로 옮기기](./spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)
- [Spring Persistence Context Flush / Clear / Detach Boundaries](./spring-persistence-context-flush-clear-detach-boundaries.md)
- [Spring Data JPA `save`, JPA `persist`, and `merge` State Transitions](./spring-data-jpa-save-persist-merge-state-transitions.md)

retrieval-anchor-keywords: datajpatest bulk update stale state, jpql bulk update clear, persistence context stale entity test, datajpatest clear reload beginner, testentitymanager clear bulk update, @modifying clearautomatically beginner, bulk update old value after findbyid, jpa bulk update persistence context bypass, bulk update 했는데 값이 안 바뀌어요, 왜 다시 조회해도 옛값이에요, datajpatest bulk update 처음, datajpatest bulk update 헷갈려요, spring basics, beginner spring, 처음 배우는데 bulk update stale state

## 먼저 mental model 한 줄

초급자는 이 한 문장부터 잡으면 된다.

**bulk update는 DB를 직접 바꾸지만, 내가 이미 들고 있던 엔티티 객체까지 자동으로 새로고침해 주지는 않는다.**

그래서 `@DataJpaTest`에서 아래 두 결과가 동시에 나올 수 있다.

- bulk update count는 `1`이다
- 그런데 `member.getStatus()`나 바로 이어진 조회 결과는 `"ACTIVE"`처럼 옛값 같다

이건 DB update 실패가 아니라, **같은 persistence context가 예전 managed 상태를 계속 보여 주는 상황**일 수 있다.

## 왜 초급자가 특히 헷갈리나

`@DataJpaTest`는 기본적으로 트랜잭션 안에서 돈다.
그 안에서 이미 읽어 둔 엔티티가 있으면 JPA는 그 managed 엔티티를 계속 재사용할 수 있다.

즉 초급자 눈에는 이렇게 보인다.

```text
1. 엔티티 저장
2. 엔티티 조회
3. bulk update 실행
4. 다시 조회
5. 어? 왜 옛값이지?
```

하지만 JPA 입장에서는 이렇게 해석될 수 있다.

```text
1. 같은 persistence context 안에서 Member(id=1)를 이미 관리 중
2. bulk update는 DB에 직접 SQL 실행
3. 그런데 현재 메모리의 managed Member(id=1)는 그대로 둠
4. 다시 조회해도 같은 managed 객체를 돌려줌
```

핵심은 **"다시 조회했다"와 "새로 DB에서 읽었다"가 항상 같은 뜻은 아니라는 점**이다.

## 가장 작은 예제로 보기

### repository

```java
public interface MemberRepository extends JpaRepository<Member, Long> {

    @Modifying
    @Query("update Member m set m.status = :status where m.id = :id")
    int bulkUpdateStatus(@Param("id") Long id, @Param("status") String status);
}
```

### 착시가 생기는 테스트

```java
@DataJpaTest
class MemberRepositoryTest {

    @Autowired MemberRepository memberRepository;

    @Test
    void bulk_update_can_look_stale() {
        Member member = memberRepository.save(new Member("ACTIVE"));

        int updated = memberRepository.bulkUpdateStatus(member.getId(), "INACTIVE");

        Member found = memberRepository.findById(member.getId()).orElseThrow();

        assertThat(updated).isEqualTo(1);
        assertThat(found.getStatus()).isEqualTo("INACTIVE");
    }
}
```

이 테스트는 초급자에게 "당연히 통과할 것 같은데?"처럼 보인다.
하지만 상황에 따라 `found.getStatus()`가 아직 `"ACTIVE"`처럼 보여서 놀랄 수 있다.

왜냐하면 `found`가 완전히 새로 읽힌 결과가 아니라, **이미 persistence context가 들고 있던 같은 엔티티 인스턴스**일 수 있기 때문이다.

## 해결은 어렵지 않다

### 방법 1. `clear()` 후 다시 조회

```java
@DataJpaTest
class MemberRepositoryTest {

    @Autowired MemberRepository memberRepository;
    @Autowired TestEntityManager testEntityManager;

    @Test
    void bulk_update_after_clear_reads_fresh_state() {
        Member member = memberRepository.save(new Member("ACTIVE"));

        int updated = memberRepository.bulkUpdateStatus(member.getId(), "INACTIVE");

        testEntityManager.clear();

        Member found = memberRepository.findById(member.getId()).orElseThrow();

        assertThat(updated).isEqualTo(1);
        assertThat(found.getStatus()).isEqualTo("INACTIVE");
    }
}
```

초급자용 해석:

- bulk update는 DB를 바꿨다
- `clear()`는 지금 메모리에 들고 있던 managed 상태를 내려놓는다
- 그 다음 조회는 "옛 객체 재사용"이 아니라 "다시 읽기" 의미가 더 강해진다

### 방법 2. 처음 들고 있던 객체를 버리고, 필요한 시점에 다시 로드

`clear()`가 부담스럽다면, 적어도 **bulk update 전후에 같은 엔티티 객체를 그대로 믿지 않는다**는 습관이 중요하다.

```java
Long memberId = memberRepository.save(new Member("ACTIVE")).getId();

memberRepository.bulkUpdateStatus(memberId, "INACTIVE");
testEntityManager.clear();

Member reloaded = memberRepository.findById(memberId).orElseThrow();
assertThat(reloaded.getStatus()).isEqualTo("INACTIVE");
```

초급자 기준으로는 이 패턴이 가장 읽기 쉽다.

- ID만 남긴다
- bulk update를 실행한다
- `clear()` 한다
- 다시 읽은 엔티티로 검증한다

## `flush()`는 언제 같이 떠올리나

이 주제에서는 `clear()`가 더 직접적이다.
다만 아래 상황이면 `flush()`도 같이 떠올릴 수 있다.

| 상황 | 왜 `flush()`를 같이 보나 |
|---|---|
| bulk update 전에 save한 엔티티가 아직 SQL로 안 나간 것 같음 | DB와 동기화 시점을 먼저 분명히 하고 싶어서 |
| 테스트에서 insert/update 순서를 더 분명히 드러내고 싶음 | "먼저 저장, 그다음 bulk update" 흐름을 명시하려고 |

그래도 초급자에게 먼저 필요한 기억은 이것이다.

- `flush()`는 SQL 동기화 타이밍을 당긴다
- `clear()`는 stale managed state 착시를 끊는다

## 한눈에 비교

| 질문 | `clear()` 없이 볼 때 | `clear()` 후 볼 때 |
|---|---|---|
| 지금 보는 객체는 무엇에 가깝나 | 기존 managed 엔티티 재사용 | 다시 읽은 결과 |
| bulk update 후 옛값 착시 가능성 | 높다 | 낮아진다 |
| 초급자 테스트 해석 난이도 | 높다 | 낮다 |

## 자주 하는 오해

- "bulk update count가 1이면 지금 손에 든 엔티티 필드도 바로 바뀌어 있다"가 아니다.
- "`findById()`를 다시 했으니 무조건 DB를 다시 읽었다"가 아니다.
- "`clear()`를 넣는 건 JPA 버그 회피"가 아니다.

`clear()`는 꼼수가 아니라, **영속성 컨텍스트와 DB 상태를 의도적으로 다시 맞춰 보는 확인 동작**에 가깝다.

## 한 단계 다음

Spring Data JPA에서는 아래처럼 자동 정리 옵션을 둘 수도 있다.

```java
@Modifying(clearAutomatically = true, flushAutomatically = true)
```

초급자는 이 옵션을 "bulk update 전후에 테스트 경계를 자동으로 조금 더 또렷하게 만드는 보조 버튼" 정도로 이해하면 충분하다.

| 옵션 | 초급자용 한 줄 해석 | repository 테스트에서 특히 도움 되는 순간 |
|---|---|---|
| `flushAutomatically = true` | bulk update 전에 pending 변경을 먼저 DB로 밀어 넣는다 | 같은 테스트에서 `save()`한 데이터가 아직 flush되지 않았을 수 있어서, "방금 저장한 행을 기준으로 bulk update가 도는가?"를 더 분명히 보고 싶을 때 |
| `clearAutomatically = true` | bulk update 뒤 현재 persistence context를 비워 stale state를 줄인다 | bulk update 직후 `findById()`나 필드 검증이 옛 managed 엔티티를 다시 보는 착시를 줄이고 싶을 때 |

짧게 외우면 이렇다.

- `flushAutomatically`는 "실행 전에 DB 기준선을 맞추는 버튼"에 가깝다.
- `clearAutomatically`는 "실행 후 메모리 착시를 걷어내는 버튼"에 가깝다.

둘을 같이 두는 경우가 많은 이유도 단순하다.
"DB에 반영할 것은 먼저 반영하고, bulk update 뒤에는 옛 엔티티를 계속 들고 있지 말자"는 의도를 한 줄에 묶기 쉽기 때문이다.

다만 초급자라면 옵션부터 외우기보다 먼저 이 흐름을 이해하는 편이 낫다.

1. bulk update는 persistence context를 우회할 수 있다
2. 그래서 stale state가 보일 수 있다
3. 테스트에서는 `clear()`나 재조회 경계로 의미를 분명하게 만든다

## 꼬리질문

> Q: bulk update count가 맞는데 조회 결과가 옛값처럼 보일 수 있는 이유는 무엇인가?
> 의도: persistence context stale state 이해 확인
> 핵심: DB는 바뀌었어도 현재 persistence context가 예전 managed 엔티티를 계속 들고 있을 수 있기 때문이다.

> Q: `@DataJpaTest`에서 bulk update 뒤 `clear()`를 넣는 가장 실용적인 이유는 무엇인가?
> 의도: 재조회 의미 분리 확인
> 핵심: 메모리에 남아 있던 managed 상태를 끊고, 다시 읽은 결과가 정말 fresh read에 가깝도록 만들기 위해서다.

> Q: 이 주제에서 `flush()`와 `clear()`의 역할 차이는 무엇인가?
> 의도: 동기화와 stale state 제거 구분 확인
> 핵심: `flush()`는 SQL 동기화 시점을 당기고, `clear()`는 영속성 컨텍스트의 옛 상태를 내려놓는다.

## 한 줄 정리

`@DataJpaTest`에서 bulk update 결과가 안 바뀐 것처럼 보이면, 먼저 DB 실패를 의심하기보다 같은 persistence context가 옛 managed 상태를 다시 보여 주는지부터 확인하고 `clear()`나 재조회 경계를 드러내자.
