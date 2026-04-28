# `@Transactional` 테스트 rollback vs commit 경계 카드

> 한 줄 요약: `@Transactional` 테스트가 끝날 때 자동 rollback된다고 해서 실제 서비스의 commit 경로까지 검증된 것은 아니며, 초심자는 먼저 "지금 보는 게 같은 테스트 트랜잭션 안 결과인가, commit 뒤에 보이는 결과인가"를 나눠야 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [테스트 전략 기초](./test-strategy-basics.md)
- [Service 계층 기초](./service-layer-basics.md)
- [DataJpaTest DB 차이 가이드](./datajpatest-db-difference-checklist.md)
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md)
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transactional test rollback vs commit, transactional test commit path beginner, spring test rollback commit boundary, datajpatest commit path beginner, rollback test real commit behavior, 처음 transactional 테스트 헷갈려요, 왜 rollback 테스트는 초록인데 운영은 다르지, 언제 commit 테스트 따로, what is commit path test, beginner transaction test boundary

## 핵심 개념

초심자가 자주 하는 착시는 "`@Transactional` 테스트가 초록이면 commit 뒤 동작도 맞겠지"라고 느끼는 것이다.
하지만 기본 rollback 테스트가 강하게 확인하는 것은 보통 **같은 테스트 트랜잭션 안에서의 저장, 조회, 예외 전파**다.

반대로 실제 서비스에서 자주 문제 되는 것은 commit이 끝난 뒤 드러나는 경로다.
예를 들면 다른 트랜잭션에서 다시 읽힐 때, `AFTER_COMMIT` 후속 작업이 돌 때, outbox row가 남을 때 같은 장면이다.

## 한눈에 보기

| 지금 확인하는 질문 | rollback 기반 테스트가 잘 보는 것 | commit 경로 테스트가 더 맞는 것 |
|---|---|---|
| 저장/조회, 매핑, 제약 조건이 맞는가 | 예 | 경우에 따라 과하다 |
| 예외가 나면 같은 트랜잭션 안 작업이 취소되는가 | 예 | 굳이 먼저 갈 필요는 적다 |
| commit 뒤 다른 조회 지점에서도 결과가 보이는가 | 약함 | 예 |
| `AFTER_COMMIT`, outbox, 후속 알림이 실제로 이어지는가 | 약함 | 예 |

- 짧게 외우면 `rollback 테스트 = 트랜잭션 안`, `commit 테스트 = 트랜잭션 밖까지`다.

## 언제 rollback 테스트로 충분한가

아래처럼 질문이 아직 **같은 트랜잭션 안**에 머물러 있으면 rollback 기반 테스트가 좋은 첫 선택이다.

| 장면 | 먼저 쓰기 좋은 테스트 |
|---|---|
| Repository 쿼리, 매핑, 저장/조회 확인 | `@DataJpaTest` |
| Service 규칙에서 예외가 나면 전체 저장이 취소되는지 확인 | `@SpringBootTest` + rollback 기본값 |
| `flush()` 시점에 unique/FK 제약이 터지는지 확인 | `@DataJpaTest` + `flush()` |

핵심은 "`지금 검증하려는 결과가 테스트 메서드가 끝나기 전에 이미 판단 가능한가?`"다.
그렇다면 commit까지 일부러 만들지 않아도 되는 경우가 많다.

## 언제 commit 경로 테스트를 따로 두나

질문이 **commit 뒤 세계**를 가리키면 rollback 테스트 1개만으로는 부족할 수 있다.

| 이런 질문이면 | 왜 별도 테스트가 필요한가 |
|---|---|
| "`flush()`는 했는데 다른 트랜잭션에서 안 보여요" | `flush`와 `commit`은 다르다 |
| "`AFTER_COMMIT` listener가 안 돌아요" | 이름 그대로 commit이 있어야 뜻이 살아난다 |
| "outbox row가 실제로 남는지 보고 싶어요" | rollback이면 테스트 끝에 지워질 수 있다 |
| "`@Transactional` 테스트는 초록인데 운영에서는 커밋 후 알림이 안 가요" | 같은 트랜잭션 안 검증과 후속 부작용 검증이 섞여 있다 |

초심자 기준 안전한 규칙은 하나면 충분하다.

**commit 뒤 관찰해야 답이 나오는 질문이면, rollback 테스트와 별도 commit-visible 테스트를 나눈다.**

## 흔한 오해와 함정

- "`flush()`까지 했으니 거의 commit을 본 셈이다"
  - 아니다. `flush`는 SQL을 보내는 쪽에 가깝고, commit은 최종 확정이다.
- "`@Transactional` 테스트가 초록이면 운영도 같다"
  - 아니다. 테스트가 본 범위가 트랜잭션 안인지 밖인지 먼저 봐야 한다.
- "그럼 모든 테스트를 `@Commit`으로 바꿔야 하나"
  - 아니다. 대부분은 rollback 테스트가 더 싸고, commit 경로만 얇게 보강하면 된다.
- "rollback 테스트에서 후속 알림이 안 갔으니 버그다"
  - commit이 없어서 원래 안 간 것인지 먼저 가려야 한다.

## 실무에서 쓰는 모습

주문 생성 후 outbox 이벤트를 남기는 코드를 예로 들면, 초심자는 보통 테스트 1개에 아래 두 질문을 같이 넣으려 한다.

1. 주문 저장이 되는가
2. commit 뒤 outbox row가 남는가

이 둘을 한 테스트에 억지로 넣기보다 보통 이렇게 나누는 편이 읽기 쉽다.

| 테스트 역할 | 먼저 확인할 것 |
|---|---|
| rollback 기반 통합 테스트 | 주문 저장, 예외 시 롤백, 트랜잭션 안 규칙 |
| commit-visible 테스트 | commit 뒤 outbox row, `AFTER_COMMIT` 후속 처리 |

즉 초심자에게 필요한 감각은 "테스트를 크게 만드는 것"이 아니라 **질문 경계를 트랜잭션 안/밖으로 자르는 것**이다.

## 더 깊이 가려면

- [테스트 전략 기초](./test-strategy-basics.md): 첫 테스트를 unit/`@DataJpaTest`/`@SpringBootTest` 중 어디에 둘지 다시 고를 때
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md): `flush()`와 `clear()`가 어디까지 보여 주는지 짧게 복습할 때
- [Outbox and Message Adapter Test Matrix](./outbox-message-adapter-test-matrix.md): commit 뒤 메시지/아웃박스 검증을 더 넓게 나눌 때
- [Spring Transactional Test Rollback Misconceptions](../spring/spring-transactional-test-rollback-misconceptions.md): Spring 테스트 rollback의 고급 함정을 더 자세히 볼 때

## 한 줄 정리

`@Transactional` 테스트의 기본 rollback은 좋은 출발점이지만, commit 뒤에만 드러나는 행동을 묻는 순간에는 별도 commit-visible 테스트로 경계를 나눠야 실제 서비스 감각과 덜 어긋난다.
