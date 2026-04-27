# BatchExecutionCount Assertion Boundaries Primer

> 한 줄 요약: 초심자 batch 테스트는 `저장이 됐는가`와 `batch가 완전히 죽지는 않았는가` 정도만 느슨하게 확인하는 편이 안전하고, `정확히 몇 번 executeBatch가 호출됐는가`까지 잠그면 provider와 DB 차이에 너무 쉽게 흔들린다.

**난이도: 🟢 Beginner**

관련 문서:

- [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- [SQL Log vs Hibernate Statistics Verification Boundaries](./sql-log-vs-hibernate-statistics-verification-boundaries.md)
- [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)
- [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- [Test Strategy Basics](./test-strategy-basics.md)
- [Spring DataJpaTest Flush/Clear/Rollback Visibility Pitfalls](../spring/spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

retrieval-anchor-keywords: batchexecutioncount assertion boundaries, batch execution count beginner, hibernate statistics batch test, batchexecutioncount stable assertion, executebatch count provider sensitive, jpa batch test what to assert, beginner batch verification primer, batch count exact number brittle, hibernate batch execution count primer, sql log vs statistics batch assertion, identity sequence batch assertion difference, datajpatest batch stats assertion

## 핵심 개념

초심자는 `batchExecutionCount`를 "배치가 살아 있는지 보는 계기판" 정도로 이해하면 충분하다.
이 숫자는 **업무 결과**를 말하는 것이 아니라, Hibernate가 내부적으로 JDBC batch를 몇 번 실행했는지 요약한 값이다.

그래서 먼저 질문을 둘로 나눠야 한다.

- 업무 질문: 120건이 저장됐는가, 실패 건은 분리됐는가, 상태가 바뀌었는가
- provider 질문: Hibernate/JDBC/DB 조합에서 SQL이 몇 묶음으로 나갔는가

초심자 테스트는 보통 첫 번째 질문을 강하게, 두 번째 질문은 느슨하게 잡는 편이 안전하다.

## 한눈에 보기

| assertion 대상 | beginner 테스트에서 안정적인가 | 이유 |
|---|---|---|
| `entityInsertCount == 120` | 비교적 예 | 저장 결과 자체는 업무 관찰값에 가깝다 |
| `repository.count() == 120` after `flush/clear` | 비교적 예 | DB 재조회 결과를 확인하는 쪽이라 provider 내부 묶음 수와 덜 엮인다 |
| `batchExecutionCount > 0` | 조건부로 예 | "batch가 완전히 0은 아니다" 정도의 느슨한 신호로는 쓸 수 있다 |
| `batchExecutionCount == 3` | 대체로 아니오 | flush 타이밍, ID 전략, driver, provider 버전에 따라 쉽게 변한다 |
| `각 batch가 정확히 50/50/20` | 아니오 | 내부 grouping 정책과 logging/driver 구현에 너무 민감하다 |
| `executeBatch()` 호출 순서까지 고정 | 아니오 | 초심자 테스트가 저장 기술 내부 구현에 과하게 묶인다 |

짧게 외우면 이렇다.

- **업무 결과 숫자**는 강하게 잠가도 된다.
- **provider 내부 batch 묶음 수**는 "0이냐 아니냐" 정도까지만 보는 편이 낫다.

## 무엇을 먼저 잠그면 안전한가

초심자용 batch 테스트는 아래 순서가 가장 덜 깨진다.

| 먼저 잠글 것 | 왜 안전한가 | 예시 |
|---|---|---|
| 저장/수정 결과 | 비즈니스 결과를 직접 본다 | `count == 120`, `status == EXPIRED` |
| `flush()` 후 예외/제약 조건 | SQL이 실제로 나갔는지 본다 | unique 위반, FK 위반 |
| `clear()` 후 재조회 결과 | 같은 영속성 컨텍스트 착시를 줄인다 | bulk update 뒤 상태 재조회 |
| `batchExecutionCount > 0` 같은 느슨한 신호 | "완전히 한 건씩만 간 것은 아닌가" 정도를 본다 | sequence 기반 insert |

예를 들어 아래 정도는 beginner 테스트로 무난하다.

```java
assertThat(statistics.getEntityInsertCount()).isEqualTo(120);
assertThat(statistics.getBatchExecutionCount()).isGreaterThan(0);
```

이 assertion이 말하는 것은 딱 두 가지다.

- 120건 insert는 일어났다
- batch 실행이 아예 0은 아니었다

반대로 이 두 줄만으로 "`정확히 50개씩 묶였다`"까지 말한다고 해석하면 과하다.

## 무엇이 provider-sensitive한가

`batchExecutionCount` 관련 assertion이 잘 깨지는 이유는 초심자 코드가 틀려서가 아니라, 질문 자체가 저장 기술 내부 정책에 가까워지기 때문이다.

| 민감한 요소 | 왜 흔들리나 | 흔한 착시 |
|---|---|---|
| `GenerationType.IDENTITY` vs `SEQUENCE` | insert 전에 PK를 아는지 달라 batch 가능성이 달라진다 | "`saveAll`이면 항상 같은 count가 나와야 한다" |
| 중간 `flush()` 유무 | flush 지점이 달라지면 batch 실행 횟수도 달라진다 | "비즈니스 결과가 같으니 batch count도 같아야 한다" |
| `order_inserts`, `order_updates` 설정 | SQL 재정렬 여부가 달라진다 | "코드 루프 수와 batch 수가 1:1이다" |
| Hibernate/driver/DB 차이 | 내부 batching 지원 방식이 다르다 | "로컬에서 3이면 어디서나 3이다" |
| insert/update 혼합 | 같은 모양 SQL이 깨져 묶음 수가 달라진다 | "총 120건이면 무조건 3번이다" |

그래서 아래 같은 assertion은 초심자 테스트에선 너무 빡빡한 편이다.

```java
assertThat(statistics.getBatchExecutionCount()).isEqualTo(3);
assertThat(loggedBatchSizes).containsExactly(50, 50, 20);
```

이런 테스트는 로직 회귀보다도 provider 세부 구현 변화에 더 자주 깨진다.

## before / after로 보는 더 안전한 assertion

같은 의도를 더 안정적으로 표현하는 방법은 있다.

| before: 깨지기 쉬운 assertion | after: beginner에게 더 안전한 assertion | 왜 더 낫나 |
|---|---|---|
| `batchExecutionCount == 3` | `batchExecutionCount > 0` | exact grouping 대신 "batch가 살아 있나"만 본다 |
| `loggedBatchSizes == [50, 50, 20]` | `entityInsertCount == 120` | 내부 묶음보다 결과 수를 본다 |
| `executeBatch called exactly 3 times` | `repository.count() == 120` after `flush/clear` | provider 내부 호출보다 DB 관찰 결과를 본다 |
| `IDENTITY`에서도 항상 batch count 기대 | `IDENTITY` 테스트는 저장 성공 중심, `SEQUENCE` 테스트는 batch 흔적 중심 | ID 전략 차이를 억지로 숨기지 않는다 |

초심자 기준으로는 역할을 분리하는 것이 핵심이다.

- `IDENTITY` 예시: "저장은 맞게 됐는가"를 본다
- `SEQUENCE` 예시: "batch 흔적이 보이는가"를 추가로 본다

이 분리가 더 필요하면 [IDENTITY vs SEQUENCE Batch Verification Example](./identity-vs-sequence-batch-verification-example.md)을 바로 이어 읽으면 된다.

## 흔한 오해와 함정

- `batchExecutionCount == 0`이면 저장도 실패한 것이다
  - 아니다. 저장은 성공했지만 batch 적용은 약했을 수 있다.
- `batchExecutionCount > 0`이면 성능 최적화가 끝난 것이다
  - 아니다. "완전히 죽지는 않았다"는 첫 신호에 가깝다.
- 정확한 batch 수를 잠가야 회귀 테스트가 강하다
  - 초심자 테스트에선 내부 구현 상세를 잠가서 오히려 노이즈가 커질 수 있다.
- SQL 로그에서 `insert`가 여러 줄 보이면 batch가 없었다
  - 로그 포맷만으로는 batch 묶음 수를 정확히 읽기 어려울 수 있다.
- `saveAll()`을 썼으니 어느 DB에서나 비슷한 batch count가 나와야 한다
  - 메서드 이름보다 ID 전략, flush, provider 설정이 더 크게 흔든다.

## 실무에서 쓰는 모습

배치 저장 테스트를 하나만 빠르게 고른다면 보통 아래 두 층으로 나누면 된다.

1. 결과 테스트
   `flush()`와 `clear()` 뒤에 `count`, `status`, 재조회 결과를 본다.
2. 관찰 신호 테스트
   Hibernate statistics를 켜고 `batchExecutionCount > 0` 같은 느슨한 assertion만 둔다.

이렇게 나누면 장점이 있다.

- 비즈니스 결과 회귀와 provider 최적화 신호를 서로 다른 실패로 읽을 수 있다
- DB나 Hibernate 세부 차이 때문에 테스트가 불필요하게 붉어지는 일을 줄인다

로그와 statistics 중 무엇을 먼저 볼지 아직 헷갈리면 [SQL Log vs Hibernate Statistics Verification Boundaries](./sql-log-vs-hibernate-statistics-verification-boundaries.md)를 같이 보면 된다.

## 더 깊이 가려면

- batch 설정, `IDENTITY`, `flush` 주기까지 한 번에 정리하려면 [JPA Batch Config Pitfalls](./jpa-batch-config-pitfalls.md)
- `flush()`와 `clear()`가 테스트 의미를 어떻게 바꾸는지 보려면 [DataJpaTest Flush/Clear Batch Checklist](./datajpatest-flush-clear-batch-checklist.md)
- Spring 쪽에서 rollback/visibility 착시까지 같이 보려면 [Spring DataJpaTest Flush/Clear/Rollback Visibility Pitfalls](../spring/spring-datajpatest-flush-clear-rollback-visibility-pitfalls.md)

## 면접/시니어 질문 미리보기

| 질문 | 초심자용 첫 답 |
|---|---|
| 왜 `batchExecutionCount == 3`은 brittle한가 | flush, ID 전략, provider/driver 차이로 내부 grouping이 바뀔 수 있어서 |
| 어떤 assertion을 남겨야 초심자 테스트가 덜 흔들리나 | 결과 수, 재조회 상태, `batchExecutionCount > 0` 같은 느슨한 신호 |
| 언제 exact count를 볼 수 있나 | provider나 환경을 고정한 성능 실험 또는 더 낮은 레벨의 기술 검증에서 |

## 한 줄 정리

초심자 batch 테스트는 `정확한 executeBatch 횟수`보다 `업무 결과`와 `batch가 완전히 0은 아닌가`를 먼저 잠그는 편이 훨씬 안정적이다.
