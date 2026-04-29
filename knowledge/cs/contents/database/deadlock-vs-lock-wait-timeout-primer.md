# Deadlock vs Lock Wait Timeout 입문 프라이머

> 한 줄 요약: `deadlock`은 서로가 서로를 막아 DB가 희생자 하나를 고른 경우이고, `lock wait timeout`은 줄이 안 빠져 이번 시도가 기다리다 끝난 경우다.

**난이도: 🟢 Beginner**

관련 문서:

- [락 기초](./lock-basics.md)
- [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- [Duplicate Key vs Lock Timeout vs Deadlock 입문 브리지](./db-error-signal-beginner-result-language-mini-card.md)
- [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Spring `@Transactional` 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: deadlock vs lock wait timeout, deadlock vs lock timeout basics, lock wait timeout vs deadlock beginner, deadlock 뭐예요, lock timeout 뭐예요, deadlock retry 왜 해요, lock wait timeout 왜 재시도 조심해요, 처음 deadlock lock timeout 차이, deadlock lock timeout 헷갈려요, waiting for lock basics, deadlock victim beginner, busy vs retryable lock primer

## 핵심 개념

초보자는 둘 다 "락 때문에 실패했다"로 묶어 버리기 쉽다.

하지만 질문이 다르다.

- `deadlock`: 서로가 서로를 기다리는 **원형 대기**가 생겼나?
- `lock wait timeout`: 누가 락을 오래 쥐고 있어 **기다림 예산**을 다 썼나?

한 줄 기억법은 이렇다.

> `deadlock` = 서로 맞물려 DB가 한 명을 내보냄, `lock wait timeout` = 줄이 안 빠져 이번 시도가 포기됨

## 한눈에 보기

| 질문 | `deadlock` | `lock wait timeout` |
|---|---|---|
| DB 안에서 무슨 일이 났나 | 서로가 서로 락을 기다리는 cycle이 생겼다 | 한쪽이 락을 오래 쥐고 있어 대기 시간이 limit를 넘었다 |
| DB가 희생자를 고르나 | 그렇다. 보통 한 트랜잭션을 abort한다 | 보통 아니다. 기다리던 쪽이 timeout으로 끝난다 |
| "이미 다른 요청이 이겼다"를 뜻하나 | 아니다 | 아니다 |
| 초보자 결과 언어 | `이번 시도만 다시` | `지금 막힘` |
| 첫 기본 동작 | **트랜잭션 전체** bounded retry | blocker, 긴 트랜잭션, 혼잡을 먼저 확인 |

둘 다 `already exists` 신호는 아니라는 점이 가장 중요하다.

## 상세 분해

### `deadlock`은 왜 retryable에 가깝나

DB가 cycle을 풀려고 희생자 하나를 고르면, 그 transaction attempt는 이미 끝난 셈이다.
그래서 보통 같은 SQL 한 줄이 아니라 **트랜잭션 전체를 새로 시작**해야 한다.

### `lock wait timeout`은 왜 바로 retryable로 묶기 어렵나

이 경우는 "누가 오래 쥐고 있는지"가 핵심이다.

- 긴 트랜잭션
- 트랜잭션 안의 외부 I/O
- hot row / hot key
- 너무 공격적인 짧은 lock timeout 설정

이 원인을 안 본 채 retry만 늘리면 같은 줄에서 다시 막힐 수 있다.

### 둘 다 winner 확정 신호는 아니다

`duplicate key`는 보통 winner가 이미 있다는 뜻이지만, `deadlock`과 `lock wait timeout`은 둘 다 **최종 상태를 아직 확정하지 못한 락 경합 신호**다.

## 흔한 오해와 함정

- "`lock wait timeout`이면 이미 다른 요청이 성공했겠지" -> 아니다. 아직 winner를 못 봤을 수 있다.
- "`deadlock`도 timeout이니까 timeout만 늘리면 되겠지" -> 아니다. 보통 lock ordering 문제를 같이 봐야 한다.
- "둘 다 `CannotAcquireLockException`으로 보이면 같은 정책이면 되겠지" -> 위험하다. root `SQLSTATE/errno`를 다시 봐야 한다.
- "`deadlock`은 SQL 한 줄만 다시 치면 되겠지" -> 보통 안전하지 않다. transaction attempt 전체를 다시 시작해야 한다.

## 실무에서 쓰는 모습

쿠폰 발급에서 두 요청 A, B가 동시에 들어온다고 하자.

| 장면 | 보이는 신호 | 먼저 읽는 법 |
|---|---|---|
| A가 `coupon_row`를 오래 잡고 있고 B가 기다리다 50ms를 넘김 | `lock wait timeout` | "지금은 줄이 안 빠진다"로 읽고 blocker와 timeout budget을 본다 |
| A는 `coupon_row -> audit_row`, B는 `audit_row -> coupon_row` 순서로 잠금을 잡음 | `deadlock` | "잠금 순서가 엇갈려 희생자가 뽑혔다"로 읽고 whole-transaction retry와 ordering 통일을 본다 |

즉 timeout은 **한 줄이 안 빠지는 문제**, deadlock은 **줄이 서로 맞물린 문제**라고 보면 초반 분류가 빨라진다.

## 더 깊이 가려면

- `lock timeout`을 왜 `already exists`로 보면 안 되는지 먼저 굳히려면 [`lock timeout` != `already exists` 공통 오해 카드](./lock-timeout-not-already-exists-common-confusion-card.md)
- `deadlock` / `lock timeout` / `duplicate key`를 서비스 결과 3버킷으로 같이 묶으려면 [Duplicate Key vs Lock Timeout vs Deadlock 입문 브리지](./db-error-signal-beginner-result-language-mini-card.md)
- Spring/JPA에서 같은 현상이 다른 예외 이름으로 보이는 이유까지 보려면 [MySQL/PostgreSQL Lock Timeout과 Deadlock의 Spring/JPA 예외 매핑](./spring-jpa-lock-timeout-deadlock-exception-mapping.md)
- deadlock 로그와 lock ordering을 실제 incident 관점에서 보려면 [Deadlock Case Study](./deadlock-case-study.md)

## 면접/시니어 질문 미리보기

- 왜 `deadlock` retry는 SQL 한 줄이 아니라 transaction 전체여야 할까?
- 왜 `lock wait timeout`을 무조건 retry하면 혼잡을 더 키울 수 있을까?
- lock ordering을 통일하면 deadlock은 줄어도 lock wait timeout은 왜 남을 수 있을까?

## 한 줄 정리

`deadlock`은 **서로 맞물려 희생자가 뽑힌 충돌**, `lock wait timeout`은 **줄이 안 빠져 기다리다 끝난 충돌**로 먼저 구분하면 beginner 분류가 훨씬 쉬워진다.
