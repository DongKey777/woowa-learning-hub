# PostgreSQL `55P03`에서 `NOWAIT`와 `lock_timeout`을 어떻게 나눠 읽을까?

> 한 줄 요약: PostgreSQL `55P03`는 초보자에게 "락을 못 얻었다"는 공통 신호이지만, `NOWAIT`는 **바로 포기한 fail-fast**, `lock_timeout`은 **조금 기다리다 예산을 다 쓴 대기 실패**로 나눠 읽어야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)
- [`NOWAIT`와 짧은 `lock timeout`은 왜 자동 retry보다 `busy`에 더 가깝게 볼까?](./nowait-vs-short-lock-timeout-busy-guide.md)
- [Spring/JPA에서 PostgreSQL `55P03`를 `NOWAIT`와 `lock_timeout`으로 나눠 읽는 Retry Policy Bridge](./spring-jpa-postgresql-55p03-retry-policy-bridge.md)
- [Timeout 에러코드 매핑 미니카드](./timeout-errorcode-mapping-mini-card.md)
- [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- [Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드](./spring-cannotacquirelockexception-root-sql-code-card.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: postgresql 55p03 nowait vs lock_timeout, 55p03 beginner split card, 55p03 why immediate failure, 55p03 always blocker or not, postgres lock_not_available nowait, postgres lock_timeout vs nowait, nowait fail fast basics, lock timeout waits first, 55p03 헷갈려요, 55p03 왜 바로 실패해요, 처음 postgres 55p03 뭐예요, postgresql 55p03 not always long blocker, what is 55p03 basics, nowait vs lock timeout difference

## 핵심 개념

초보자는 `55P03`를 보면 곧바로 "누가 오래 막았다"로 과하게 읽기 쉽다.
하지만 PostgreSQL에서는 같은 `55P03`라도 **왜 락을 못 얻었는지**를 한 번 더 나눠야 한다.

- `NOWAIT`: 기다리지 않겠다고 정해 둔 시도가 **즉시 실패**
- `lock_timeout`: 잠깐은 기다렸지만 **대기 예산 안에 락을 못 얻음**

둘 다 "락 획득 실패"라는 큰 분류는 같지만, 시간축 해석은 다르다.

## 한눈에 보기

| 질문 | `NOWAIT` | `lock_timeout` |
|---|---|---|
| 기다렸나? | 거의 안 기다린다 | 조금이라도 기다린다 |
| 실패가 말하는 것 | "막혀 있으면 바로 돌아선다" | "기다려 봤지만 예산 안에 안 풀렸다" |
| 초보자 첫 해석 | fail-fast probe | wait budget 초과 |
| blocker를 얼마나 강하게 의심하나? | "지금 잠겨 있네" 정도 | "실제로 대기열이 있었네" 쪽이 더 강하다 |
| `55P03`를 읽는 한 줄 | 즉시 포기 정책도 포함 | 실제 대기 실패도 포함 |

짧게 외우면 이렇다.

> `55P03`는 하나지만, `NOWAIT`는 "안 기다림", `lock_timeout`은 "기다렸지만 실패"다.

## 가장 작은 예시

같은 좌석 row를 잡으려는 두 SQL이 있다고 하자.

```sql
SELECT * FROM seats WHERE id = 7 FOR UPDATE NOWAIT;
```

이 경우 다른 트랜잭션이 이미 row를 잡고 있으면, 이 SQL은 거의 바로 `55P03`를 낼 수 있다.
여기서 초보자 첫 해석은 "`오래 기다렸다`"가 아니라 "`기다리지 않기로 한 경로가 바로 막혔다`"다.

반대로:

```sql
SET LOCAL lock_timeout = '200ms';
SELECT * FROM seats WHERE id = 7 FOR UPDATE;
```

이 경우는 최대 200ms 정도 기다려 본 뒤, 락이 안 풀리면 `55P03`가 날 수 있다.
즉 같은 `55P03`라도 두 번째는 **실제 대기 시간이 있었다**는 뜻이 더 강하다.

## 초보자 분리 질문 4개

`55P03`를 봤을 때 아래 순서로 물으면 과잉 해석이 줄어든다.

1. SQL에 `NOWAIT`가 직접 붙어 있었나?
2. 세션이나 트랜잭션에서 `lock_timeout`을 짧게 둔 상태였나?
3. 로그에 wait ms, blocker, lock wait 흔적이 있었나?
4. 이 경로가 애초에 "막혀 있으면 빨리 실패"하도록 설계된 경로였나?

읽는 법:

- `NOWAIT`가 보이면: "긴 blocker"를 단정하지 말고 **fail-fast 설계**부터 본다.
- `lock_timeout`이 보이면: **실제 대기**가 있었을 가능성이 커서 blocker를 더 적극적으로 본다.
- 둘 다 안 보이면: PostgreSQL 드라이버/프레임워크가 어떤 SQL을 만들었는지 한 단계 더 내려가 확인한다.

## 흔한 오해와 함정

- "`55P03`면 항상 오래 막힌 blocker가 있었다"
  - 아니다. `NOWAIT`면 거의 즉시 실패할 수 있다.
- "`55P03`면 전부 같은 retry 규칙으로 보면 된다"
  - 아니다. 둘 다 보통 `busy` 축이지만, `NOWAIT`는 "안 기다림" 정책을 더 강하게 담고 있다.
- "`NOWAIT`도 lock timeout의 한 종류니까 기다린 것으로 봐도 된다"
  - 아니다. 초보자용 분리선은 "기다렸는가"다.
- "`lock_timeout`이 짧으면 `NOWAIT`와 완전히 같다"
  - 비슷한 운영 의도는 있을 수 있지만, `lock_timeout`은 그래도 **약간의 대기**를 허용한다는 점이 다르다.

비유로는 `NOWAIT`가 "줄이 있으면 바로 다른 가게로 간다", `lock_timeout`이 "10초만 기다려 보고 안 되면 간다"에 가깝다.
하지만 실제 DB는 row lock, key lock, metadata lock 등 잠금 대상이 다르므로, 비유만으로 락 종류까지 일반화하면 안 된다.

## 실무에서 쓰는 모습

| 로그/설정 단서 | 초보자 첫 해석 | 바로 할 일 |
|---|---|---|
| SQL에 `FOR UPDATE NOWAIT`가 보인다 | 이 경로는 애초에 대기를 원하지 않는다 | blind retry보다 `busy`/fail-fast 정책을 먼저 본다 |
| `SET LOCAL lock_timeout = '100ms'` 뒤에 `55P03`가 난다 | 잠깐 기다리다 실패했다 | blocker, hot row, 긴 트랜잭션을 본다 |
| Spring에서 `CannotAcquireLockException`만 보인다 | 표면 이름만으로는 부족하다 | root `SQLSTATE`와 실제 SQL 힌트를 함께 본다 |

PostgreSQL 기준으로 `55P03`라는 SQLSTATE 자체는 같을 수 있지만, 학습자가 가져가야 할 첫 질문은 다르다.

- `NOWAIT` 쪽: "이 경로는 왜 대기를 0에 가깝게 설계했지?"
- `lock_timeout` 쪽: "누가 얼마나 오래 막았지?"

## 더 깊이 가려면

- blocker를 먼저 찾는 흐름은 [Lock Timeout 났을 때 blocker 먼저 보는 미니카드](./lock-timeout-blocker-first-check-mini-card.md)
- `NOWAIT`와 짧은 락 예산을 `busy` 정책으로 읽는 이유는 [`NOWAIT`와 짧은 `lock timeout`은 왜 자동 retry보다 `busy`에 더 가깝게 볼까?](./nowait-vs-short-lock-timeout-busy-guide.md)
- 같은 요청 안에서 `57014`와 `55P03`가 섞일 때는 [Statement Timeout vs Lock Timeout 비교 카드](./statement-timeout-vs-lock-timeout-card.md)
- Spring 예외 표면에서 root code를 다시 읽는 순서는 [Spring `CannotAcquireLockException`에서 root SQL 코드 먼저 읽는 초간단 카드](./spring-cannotacquirelockexception-root-sql-code-card.md)
- Spring/JPA surface와 retry 정책까지 한 번에 묶어 보고 싶으면 [Spring/JPA에서 PostgreSQL `55P03`를 `NOWAIT`와 `lock_timeout`으로 나눠 읽는 Retry Policy Bridge](./spring-jpa-postgresql-55p03-retry-policy-bridge.md)

## 한 줄 정리

PostgreSQL `55P03`는 "락을 못 얻었다"는 공통 신호이지만, `NOWAIT`는 **안 기다린 fail-fast**, `lock_timeout`은 **기다리다 실패한 wait budget 초과**로 나눠 읽어야 초보자가 blocker를 과하게 단정하지 않는다.
