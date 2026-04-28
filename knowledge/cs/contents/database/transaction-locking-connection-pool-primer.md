# 트랜잭션, 락, 커넥션 풀 첫 그림

> 한 줄 요약: 요청 하나는 보통 커넥션 풀에서 연결 하나를 빌려 트랜잭션을 열고, 필요한 격리 수준과 락/제약을 거쳐 `commit`한 뒤 연결을 반환한다.

**난이도: 🟢 Beginner**

관련 문서:

- [트랜잭션 기초](./transaction-basics.md)
- [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
- [락 기초](./lock-basics.md)
- [커넥션 풀 기초](./connection-pool-basics.md)
- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
- [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)
- [Deadlock Case Study](./deadlock-case-study.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)
- [database 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: transaction locking connection pool primer, transaction boundary beginner, isolation locking uniqueness beginner, deadlock intuition beginner, connection pool before jdbc jpa, request to db flow beginner, unique vs lock beginner, long transaction connection pool exhaustion, lock wait to pool timeout bridge, transactional external api call pitfall, external api inside transaction pool timeout, hikaricp active pending connection bridge, transaction locking connection pool primer basics, transaction locking connection pool primer beginner, transaction locking connection pool primer intro

## 처음 막히는 질문별 1분 라우트

`트랜잭션`, `락`, `커넥션 풀`은 한 장에 같이 나오지만, 초보자 질문은 보통 아래 셋 중 하나로 먼저 잘라야 한다.

| 지금 떠오르는 말 | 이 문서에서 먼저 답하나? | 바로 다음 문서 |
|---|---|---|
| "`왜 connection timeout이 lock 문제처럼 번져요?`" | 예 | [커넥션 풀 기초](./connection-pool-basics.md) |
| "`언제 UNIQUE고 언제 lock이에요?`" | 예 | [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md) |
| "`save()`는 보이는데 SQL은 어디 있죠?`" | 아니오 | [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md) |
| "`왜 마지막 재고가 또 팔려요?`" | 일부만 | [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md) |

## 먼저 큰 그림

초보자는 용어를 따로 외우기보다 **요청 하나가 DB를 다녀오는 흐름**을 먼저 잡는 편이 덜 헷갈린다.

```text
요청 시작
  -> 커넥션 풀에서 연결 1개 빌림
  -> 트랜잭션 시작
  -> SQL 실행
     -> 같은 데이터를 두 요청이 건드리면 락 대기 또는 UNIQUE 충돌 가능
     -> 격리 수준은 "남이 commit한 것을 언제 보나"를 정함
  -> commit 또는 rollback
  -> 커넥션 풀에 연결 반환
요청 종료
```

JDBC, JPA, MyBatis, Spring은 이 흐름을 감싸는 **이름과 편의 기능**이 다를 뿐이다.
밑바닥에서는 여전히 "커넥션 하나 위에서 트랜잭션이 열리고 닫힌다"는 같은 그림이 돌아간다.

## 한눈에 보는 역할 분담

| 지금 답해야 하는 질문 | 주로 보는 도구 | 입문 단계 기억법 | 흔한 실패 신호 |
|---|---|---|---|
| 무엇을 같이 성공/실패시킬까 | 트랜잭션 경계 | "같이 rollback되어야 하나?" | 중간 상태가 남음 |
| 동시에 실행될 때 무엇이 보일까 | 격리 수준 | "내가 보는 화면이 언제 바뀌나?" | 재조회 값 변화, retry |
| 같은 row를 누가 먼저 만질까 | 락, 버전 컬럼 | "기다릴까, 나중에 충돌로 실패할까?" | lock wait, deadlock, version conflict |
| exact key 중복을 누가 막을까 | `UNIQUE` 제약 | "둘 중 한 명은 바로 탈락" | `duplicate key` |
| 동시에 몇 요청이 DB와 대화할까 | 커넥션 풀 | "입장 가능한 창구 수" | connection timeout, pool exhaustion |

핵심은 이 다섯 가지가 **같은 말이 아니라는 점**이다.

- 트랜잭션 경계는 "실패 단위"
- 격리 수준은 "읽기 시야"
- 락은 "대기 순서"
- `UNIQUE`는 "존재 규칙"
- 커넥션 풀은 "연결 수용량"

## 증상을 보면 먼저 번역할 한 줄

초보자는 에러 이름을 보면 원인을 바로 확정하기 쉽다. 여기서는 "어디가 막혔는지"만 먼저 번역하면 충분하다.

| 먼저 보인 말 | 첫 번역 | 바로 다음 문서 |
|---|---|---|
| `connection timeout`, `pool exhausted` | DB 연결 자체를 오래 쥔 요청이 있을 수 있다 | [커넥션 풀 기초](./connection-pool-basics.md) |
| `lock wait timeout`, `deadlock detected` | 연결은 빌렸지만 row 순서나 대기열에서 막혔을 수 있다 | [락 기초](./lock-basics.md) |
| `duplicate key`, `already exists` | 기다림보다 exact key 규칙 충돌일 수 있다 | [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md) |

이 표의 목적은 진단 완료가 아니다. "`pool인가요? lock인가요? unique인가요?`" 세 갈래만 먼저 고르면 뒤 문서가 훨씬 짧게 읽힌다.

## 1. 트랜잭션 경계: 무엇을 같이 rollback할까

트랜잭션 boundary는 가장 먼저 정한다.
질문은 단순하다.

> 이 작업들 중 무엇이 "같이 성공하거나 같이 실패"해야 하는가?

예를 들어 주문 생성에서:

- 주문 row 저장
- 재고 차감

은 보통 같은 트랜잭션에 묶는다. 반면:

- 메일 발송
- 외부 결제 승인 대기
- 이미지 업로드

는 같은 트랜잭션 안에 오래 들고 있으면 안 된다.

| 좋은 경계 예시 | 나쁜 경계 예시 |
|---|---|
| 주문 row 저장 + 재고 차감 | 주문 row 저장 + 재고 차감 + 외부 API 2초 대기 |
| 쿠폰 발급 row 저장 + 사용 이력 row 저장 | 쿠폰 발급 row 저장 + 슬랙 알림 전송 |

왜냐하면 트랜잭션이 길어질수록 보통 두 가지를 더 오래 붙잡기 때문이다.

- 커넥션
- 락

즉 "경계를 크게 잡으면 더 안전하다"가 아니라, **짧고 결정적인 DB 상태 변화만 안에 넣는 쪽이 더 안전**하다.

## 2. 격리 수준: 동시에 돌 때 무엇이 보이나

격리 수준(isolation level)은 "다른 트랜잭션이 commit한 내용을 내가 언제 보느냐"를 정한다.
초보자에게는 **읽기 규칙**으로 기억하는 것이 가장 쉽다.

| 격리 수준 | 초보자용 그림 | 먼저 기억할 포인트 |
|---|---|---|
| `READ COMMITTED` | 매 쿼리가 그 시점 최신 commit 결과를 봄 | 같은 트랜잭션에서도 재조회 결과가 바뀔 수 있다 |
| `REPEATABLE READ` | 한 트랜잭션 안에서 읽은 기준이 더 잘 유지됨 | 같은 row를 다시 읽을 때 흔들림이 줄어든다 |
| `SERIALIZABLE` | 동시에 해도 순서대로 한 것처럼 보이게 시도 | 강하지만 대기나 retry 비용이 커질 수 있다 |

입문 단계에서 특히 구분해야 하는 오해:

- 격리 수준은 트랜잭션 경계 자체를 정하는 옵션이 아니다
- 격리 수준이 높다고 `UNIQUE` 제약이 필요 없어지는 것은 아니다
- exact duplicate, range absence, hot row 경합은 격리 수준만으로 끝나지 않는 경우가 많다

즉 격리 수준은 "무슨 데이터를 보느냐"에 가깝고,
`UNIQUE`와 락은 "충돌이 나면 어떻게 막느냐"에 가깝다.

## 3. 락 vs `UNIQUE`: 기다리게 할까, 바로 탈락시킬까

초보자가 가장 많이 섞는 두 개가 여기다.

- 락: 누군가 먼저 처리 중이면 **기다리게 하거나**, 나중에 deadlock/timeout으로 실패시킨다
- `UNIQUE`: exact key가 이미 있으면 **바로 패배시킨다**

짧게 외우면 이렇다.

> `UNIQUE`는 "한 명만 통과", 락은 "한 명은 잠깐 기다림"이다.

| 상황 | 먼저 떠올릴 기본 도구 | 이유 |
|---|---|---|
| 같은 `(coupon_id, member_id)`를 한 번만 발급 | `UNIQUE` | exact key 중복 금지 규칙이기 때문 |
| 이미 존재하는 주문 row 상태를 한 명씩만 바꾸기 | row lock 또는 version column | existing row의 순서를 정해야 하기 때문 |
| "없으면 insert"인데 row가 아직 없음 | `UNIQUE` 또는 다른 제약/설계 | 없는 row는 락만으로 안전하게 표현되지 않을 수 있기 때문 |

예를 들어 쿠폰 발급에서:

```sql
ALTER TABLE coupon_issue
ADD CONSTRAINT uq_coupon_issue UNIQUE (coupon_id, member_id);
```

이 제약이 있으면 두 요청이 동시에 와도 DB가 마지막 승자를 정한다.
뒤늦게 온 요청은 보통 `duplicate key`를 받는다.

반대로 `SELECT ... FOR UPDATE`는 **이미 있는 row를 순서대로 다루는 데** 더 잘 맞는다.
row가 아직 없다면, "미리 잠가 두었으니 중복이 안 나겠지"라는 감각이 쉽게 틀린다.

입문 단계 첫 기준:

- exact duplicate correctness -> `UNIQUE`
- existing row state transition -> lock 또는 version
- 범위/부재 규칙 -> `UNIQUE` 외 다른 설계가 더 필요할 수 있음

## 4. 데드락 직관: 락을 많이 잡아서가 아니라 순서가 엇갈려서 생긴다

deadlock은 "DB가 고장 났다"가 아니라 **서로가 서로를 기다리는 원형 대기**다.

| 시점 | 트랜잭션 A | 트랜잭션 B |
|---|---|---|
| 1 | 계좌 1 lock 획득 |  |
| 2 |  | 계좌 2 lock 획득 |
| 3 | 계좌 2를 기다림 |  |
| 4 |  | 계좌 1을 기다림 |

이제 둘 다 앞으로 못 간다. DB는 보통 둘 중 하나를 희생시켜 deadlock을 푼다.

초보자용 예방 원칙은 세 줄이면 충분하다.

1. 같은 종류의 row는 항상 같은 순서로 잠근다.
2. 트랜잭션을 짧게 유지한다.
3. 트랜잭션 안에 외부 API 호출을 넣지 않는다.

그래서 deadlock은 "락을 썼으니 실패"가 아니라, **락 순서 설계가 흔들렸다는 신호**로 보는 편이 맞다.

## 5. 커넥션 풀이 왜 먼저 필요한가

DB 커넥션은 무료가 아니다.

- TCP 연결
- 인증
- 세션 초기화

같은 준비 비용이 있기 때문에, 요청마다 새 연결을 만들면 느리고 DB도 힘들어진다.
그래서 애플리케이션은 보통 커넥션 풀에서 미리 만든 연결을 빌려 쓴다.

여기서 중요한 연결점은:

> 트랜잭션이 길수록 커넥션도 오래 점유된다.

즉 pool 문제는 단순히 "DB 연결 숫자" 문제가 아니라, **트랜잭션 길이와 락 대기가 pool까지 전파된 결과**일 때가 많다.

| 증상 | 초보자가 먼저 떠올릴 해석 |
|---|---|
| `Connection is not available` | 풀의 연결이 다 사용 중일 수 있다 |
| lock wait timeout | 커넥션은 빌렸지만, 데이터 락 때문에 막혔을 수 있다 |
| deadlock error | 연결은 있었지만 락 순서가 꼬였을 수 있다 |

그래서 pool size를 늘리는 것만으로는 모든 문제가 해결되지 않는다.

- 긴 트랜잭션이면 -> 연결을 더 오래 잡는다
- 느린 쿼리면 -> 연결과 락을 더 오래 점유한다
- deadlock이면 -> 풀 크기보다 락 순서가 우선 문제다

짧게 기억하면 아래처럼 이어진다.

```text
긴 트랜잭션
  -> 락/쿼리 대기 증가
  -> 커넥션 반환 지연
  -> 새 요청은 pool timeout으로 보일 수 있음
```

## 5-1. hot row 경합이 pool exhaustion으로 번지는 한 장 그림

입문자가 놓치기 쉬운 핵심은 **같은 row 경합이 DB 안에서만 끝나지 않고 커넥션 풀까지 번질 수 있다**는 점이다.

```text
요청 A                  요청 B                  요청 C..N
borrow conn 1           borrow conn 2           borrow conn 3..10
begin tx                begin tx                begin tx
update product=42       update product=42       update product=42
lock 획득               A의 lock 해제 대기       앞선 대기열 뒤로 계속 대기
외부 API 2초 대기       conn 2를 쥔 채 대기      conn 3..10을 쥔 채 대기
commit                  lock 획득 후 진행        풀 여유 0
return conn 1           commit                  새 요청은 conn 자체를 못 빌림
                        return conn 2           -> connection timeout
```

한 줄로 줄이면 이 흐름이다.

`hot row -> lock wait 증가 -> 대기 요청도 커넥션을 계속 점유 -> active connection 증가 -> pool exhaustion`

즉 첫 실패 원인은 row 경합인데, 애플리케이션의 마지막 증상은 `Connection is not available`로 보일 수 있다.

## 5-2. 코드 경계 예시: 연쇄를 어디서 끊나

가장 자주 보이는 원인은 "외부 I/O를 트랜잭션 안에 둔 상태에서 hot row를 같이 건드리는 코드"다.

```java
@Transactional
public void placeOrder(PlaceOrderCommand cmd) {
    inventoryRepository.decrease(cmd.productId(), cmd.qty());
    paymentClient.authorize(cmd.paymentToken()); // lock과 connection을 쥔 채 대기
}
```

| 경계 방식 | 락 점유 시간 | 커넥션 점유 시간 | 초보자용 해석 |
|---|---|---|---|
| 외부 API를 트랜잭션 안에 둠 | 길어짐 | 길어짐 | lock wait가 pool 대기로 번지기 쉽다 |
| DB 상태 변경만 트랜잭션에 둠 | 짧아짐 | 짧아짐 | 같은 hot row여도 전파 범위가 줄어든다 |

아래처럼 외부 호출을 경계 밖으로 빼면, 같은 row 경합이 있어도 커넥션 반환이 빨라져 연쇄가 약해진다.

```java
public void placeOrder(PlaceOrderCommand cmd) {
    PaymentResult payment = paymentClient.authorize(cmd.paymentToken());
    createPaidOrder(cmd, payment);
}
```

## 5-3. 증상에서 코드 경계로 바로 가는 브리지

입문자는 로그를 보면 에러 이름만 붙잡고 끝내기 쉽다.
아래처럼 "증상 -> 보통의 직전 원인 -> 먼저 볼 코드 경계"로 바로 연결하면 길을 잃지 않는다.

| 먼저 보인 증상 | 보통의 직전 원인 | 코드에서 첫 확인 지점 |
|---|---|---|
| `Connection is not available`, `timeout after ...ms` | 트랜잭션이 오래 열려 커넥션 반환이 늦음 | `@Transactional` 메서드 안에 외부 API/파일 I/O/원격 호출이 섞였는지 |
| lock wait timeout | 락 경합 + 긴 트랜잭션으로 대기열 증가 | 갱신 순서가 고정되어 있는지, 느린 쿼리가 트랜잭션 안에 있는지 |
| deadlock detected | 락 획득 순서가 요청마다 달라짐 | 같은 종류 row를 항상 같은 순서로 잠그는지 |

한 줄 체크 순서:

1. timeout 종류를 먼저 분류한다 (`connection wait` vs `lock wait`).
2. 해당 요청의 트랜잭션 길이와 외부 호출 포함 여부를 본다.
3. pool size 조정보다 먼저 경계를 줄여 점유 시간을 줄인다.

## 6. JDBC/JPA 전에 이 그림이 필요한 이유

프레임워크 이름이 달라져도 같은 이야기를 다른 레이어에서 하는 것이다.

| 코드에서 보이는 이름 | 실제로 무슨 뜻인가 |
|---|---|
| JDBC `Connection` | 풀에서 빌린 DB 연결 |
| `setAutoCommit(false)` | 명시적으로 트랜잭션 경계를 잡기 시작 |
| `commit()` / `rollback()` | 트랜잭션 종료 |
| Spring `@Transactional` | begin/commit/rollback을 프레임워크가 대신 관리 |
| JPA `@Version` | optimistic locking 도구 |
| JPA `PESSIMISTIC_WRITE` | row locking read 쪽 개념 |
| HikariCP 설정 | 커넥션 풀 크기와 대기 시간 정책 |

이 mental model 없이 JDBC/JPA를 먼저 보면:

- `@Transactional`이 왜 pool과 연결되는지
- `duplicate key`와 deadlock을 왜 다르게 처리해야 하는지
- pool exhaustion이 왜 느린 쿼리/긴 트랜잭션과 묶여 보이는지

가 전부 따로따로 보인다.

## 자주 하는 혼동

- "트랜잭션을 길게 잡으면 더 안전하다"
  - 보통은 락과 커넥션 점유 시간이 늘어 더 위험해진다.
- "격리 수준을 올리면 중복 insert도 자동으로 막힌다"
  - exact key 중복은 대개 `UNIQUE`가 더 직접적인 도구다.
- "lock timeout이 났으니 이미 다른 요청이 성공했다"
  - 꼭 그렇지 않다. 단지 오래 기다렸거나 deadlock이 있었을 수 있다.
- "커넥션 풀만 키우면 병목이 해결된다"
  - 긴 트랜잭션, 느린 쿼리, 락 경합을 그대로 두면 DB만 더 힘들어진다.
- "JPA를 쓰면 이런 내부 그림은 몰라도 된다"
  - JPA도 결국 JDBC 커넥션과 DB 트랜잭션 위에서 동작한다.

## 다음에 이렇게 읽으면 덜 헷갈린다

1. 트랜잭션의 commit/rollback 감각 먼저 -> [트랜잭션 기초](./transaction-basics.md)
2. 동시에 돌 때 무엇이 보이는지 -> [트랜잭션 격리 수준 기초](./transaction-isolation-basics.md)
3. 누가 기다리고 누가 실패하는지 -> [락 기초](./lock-basics.md)
4. exact duplicate에서 `UNIQUE`와 locking read를 구분 -> [UNIQUE vs Locking-Read Duplicate Primer](./unique-vs-locking-read-duplicate-primer.md)
5. 왜 연결이 모자라 보이는지 -> [커넥션 풀 기초](./connection-pool-basics.md)
6. 트랜잭션 경계와 풀 고갈 전파를 코드에서 확인 -> [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
7. 그 위에서 JDBC/JPA/MyBatis 이름을 얹기 -> [JDBC · JPA · MyBatis 기초](./jdbc-jpa-mybatis-basics.md)

## 한 줄 정리

요청 하나는 보통 "커넥션 풀에서 연결을 빌려 트랜잭션을 열고, 격리 수준에 따라 읽고, 락이나 `UNIQUE`로 충돌을 처리한 뒤, `commit`하고 연결을 반환하는 흐름"으로 이해하면 JDBC와 JPA 앞단의 개념들이 한 장으로 정리된다.
