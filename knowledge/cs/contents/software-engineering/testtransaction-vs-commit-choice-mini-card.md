# `TestTransaction.end()` vs `@Commit` 선택 미니 카드

> 한 줄 요약: commit-visible 테스트가 필요할 때는 "한 테스트 안에서 commit 전/후를 이어서 볼 것인가"를 먼저 묻고, 그렇다면 `TestTransaction.end()`, 아니라면 `@Commit`을 먼저 고르면 초심자 판단이 가장 덜 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [`flush()` vs commit: `AFTER_COMMIT` 초심자 브리지 카드](./transactional-test-rollback-vs-commit-boundary-card.md)
- [왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요](./after-commit-listener-rollback-test-beginner-bridge.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
- [Spring Mini Card: 왜 rollback 기반 slice test만으로 `AFTER_COMMIT`를 끝까지 믿기 어려운가](../spring/spring-after-commit-rollback-slice-test-mini-card.md)
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: testtransaction vs @commit, testtransaction.end 뭐예요, @commit 테스트 언제 써요, commit visible test choice, spring transactional test commit choice, rollback test commit path, commit 전후 비교 테스트, 한 테스트 안에서 commit 보고 싶어요, 처음 testtransaction 헷갈려요, beginner commit visible spring test, what is testtransaction, @rollback false vs @commit

## 핵심 개념

두 도구는 둘 다 "rollback 기본 테스트에서 commit 순간을 일부러 열기" 위해 쓴다.
하지만 초심자 판단 기준은 기능 이름보다 **질문 모양**이 더 중요하다.

- 한 테스트 안에서 `commit 전 상태 -> commit -> commit 후 상태`를 이어서 비교하고 싶다
  - `TestTransaction.end()`
- 테스트 메서드 전체를 그냥 commit 기준으로 한 번 끝내면 된다
  - `@Commit`

짧게 외우면 `중간에 commit 버튼이 필요하면 TestTransaction`, `끝에서 commit이면 @Commit`이다.

## 한눈에 보기

| 지금 묻는 질문 | 먼저 고를 선택 | 이유 |
|---|---|---|
| "한 테스트 안에서 commit 전/후를 둘 다 보고 싶다" | `TestTransaction.end()` | 테스트 중간에 실제 commit 시점을 만들 수 있다 |
| "이 테스트는 마지막 결과만 commit 기준으로 보면 된다" | `@Commit` | 메서드 종료 시 rollback 대신 commit되게 바꾸면 충분하다 |
| "commit 뒤 다시 새 트랜잭션에서 조회까지 이어 가고 싶다" | `TestTransaction.end()` | commit 후 흐름을 이어서 적기 쉽다 |
| "데이터 정리가 부담되니 commit 범위를 가능한 좁히고 싶다" | 보통 `TestTransaction.end()` | 필요한 순간만 commit시키고 이후 정리 전략을 더 세밀하게 잡을 수 있다 |
| "의도만 분명히 적고 싶은 짧은 검증이다" | `@Commit` | annotation 한 줄로 의도가 드러난다 |

- Spring TestContext의 트랜잭션 테스트라는 전제가 있어야 이 판단표가 그대로 맞는다.
- 테스트가 원래 비트랜잭션이면 `TestTransaction`보다 테스트 구조 자체를 먼저 다시 골라야 한다.

## 상세 분해

### 1. 테스트 중간에 멈춰야 하는가

`TestTransaction.end()`는 "지금 여기서 commit하고 다음 줄을 계속 읽는다"에 가깝다.
그래서 commit 전과 후를 같은 테스트 메서드 안에서 비교할 때 유리하다.

반대로 `@Commit`은 테스트가 끝날 때 commit된다.
중간 비교가 필요 없다면 더 단순하다.

### 2. commit 뒤에 무엇을 이어서 볼 것인가

commit 뒤에 바로 repository 재조회, `AFTER_COMMIT` 후속 처리, outbox row 확인을 같은 테스트 안에서 이어서 적고 싶으면 `TestTransaction.end()`가 읽기 쉽다.

결과만 최종적으로 남는지 확인하면 되는 테스트라면 `@Commit`으로 충분한 경우가 많다.

### 3. 정리 비용을 얼마나 감당할 것인가

`@Commit`은 테스트 메서드 끝에서 실제 commit이 일어나므로 데이터 정리 부담이 눈에 잘 보인다.
`TestTransaction.end()`도 결국 commit을 만들 수 있으므로 오염이 0은 아니지만, 보통은 필요한 순간만 열어 범위를 더 의식적으로 다루게 된다.

여기서 비유는 "스위치" 정도까지만 맞다.
실제 오염 범위는 DB 격리, fixture 전략, 테스트 재시작 여부에 따라 달라지므로 무조건 더 안전하다고 단정하면 안 된다.

## 흔한 오해와 함정

- "`@Commit`은 항상 더 큰 통합 테스트다"
  - 아니다. Spring 테스트에서 rollback 기본값만 바꿔 commit 질문을 드러내는 선택일 수 있다.
- "`TestTransaction.end()`가 있으면 모든 경우에 더 낫다"
  - 아니다. 중간 commit이 필요 없는 테스트라면 `@Commit`이 더 짧고 의도가 분명하다.
- "`flush()`까지 했으니 둘 다 필요 없다"
  - 아니다. `flush`는 commit이 아니므로 다른 트랜잭션 가시성이나 `AFTER_COMMIT` 질문은 그대로 남는다.
- "`@Rollback(false)`와 `@Commit`은 완전히 다른 기능이다"
  - 보통 Spring 테스트에서는 비슷한 목적을 가지지만, 초심자 의도 표시는 `@Commit`이 더 읽기 쉽다.
- "`TestTransaction`만 쓰면 DB 정리가 자동이다"
  - 아니다. 실제 commit을 만들었다면 fixture 정리 책임은 여전히 남을 수 있다.

## 실무에서 쓰는 모습

### 장면 A. commit 전/후를 한 메서드에서 비교

```java
@SpringBootTest
@Transactional
class OrderCommitVisibilityTest {

    @Test
    void commit_전후를_같은_테스트에서_이어본다() {
        orderService.placeOrder();

        TestTransaction.flagForCommit();
        TestTransaction.end();

        assertThat(outboxRepository.findAll()).hasSize(1);
    }
}
```

이 장면의 질문은 "`중간 commit 뒤 바로 무엇이 보이나`"다.
그래서 `TestTransaction.end()`가 자연스럽다.

### 장면 B. 테스트 전체를 commit 기준으로 끝내기

```java
@SpringBootTest
@Commit
class OrderCommitTest {

    @Test
    void outbox_row가_commit_뒤에도_남는다() {
        orderService.placeOrder();
    }
}
```

이 장면의 질문은 "`최종 결과만 commit 기준으로 보면 되는가`"다.
그래서 `@Commit`이 더 짧다.

## 더 깊이 가려면

- [`flush()` vs commit: `AFTER_COMMIT` 초심자 브리지 카드](./transactional-test-rollback-vs-commit-boundary-card.md): 왜 commit-visible 테스트가 필요한지 경계부터 다시 잡을 때
- [왜 rollback 테스트에서 `AFTER_COMMIT` listener가 안 보이나요](./after-commit-listener-rollback-test-beginner-bridge.md): 증상 문장부터 해석하고 싶을 때
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md): Spring 테스트 rollback 함정을 더 자세히 볼 때
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md): commit-visible 검증이 outbox 테스트 전략으로 이어질 때

## 한 줄 정리

한 테스트 안에서 commit 전/후를 이어 봐야 하면 `TestTransaction.end()`, 테스트 전체를 commit 기준으로 한 번 확인하면 되면 `@Commit`을 먼저 고르는 것이 초심자용 가장 안전한 판단표다.
