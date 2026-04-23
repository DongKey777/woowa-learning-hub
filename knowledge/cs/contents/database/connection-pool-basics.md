# 커넥션 풀 기초 (Connection Pool Basics)

> 한 줄 요약: 커넥션 풀은 DB 연결을 미리 만들어 재사용하는 캐시이고, 풀 크기가 너무 작으면 대기가, 너무 크면 DB 과부하가 생긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)
- [database 카테고리 인덱스](./README.md)
- [Spring @Transactional 기초](../spring/spring-transactional-basics.md)

retrieval-anchor-keywords: connection pool basics, 커넥션 풀이란, hikari cp 입문, db connection reuse, pool size 설정, 커넥션 고갈, connection timeout beginner, jdbc connection pool, 스프링 커넥션 풀, 커넥션 풀 왜 필요해요

## 핵심 개념

커넥션 풀(connection pool)은 **미리 여러 개의 DB 연결(connection)을 만들어두고, 요청이 올 때 빌려주었다가 반환받아 재사용하는 연결 캐시**다.

DB 연결은 TCP 핸드셰이크, 인증, 세션 초기화를 거쳐야 해서 매번 새로 만들면 수십~수백 ms가 소비된다. 트래픽이 높은 서비스에서 요청마다 새 연결을 만들면 응답 시간이 크게 늘어난다. 커넥션 풀은 이 연결 생성 비용을 요청 경로에서 제거한다.

입문자가 자주 헷갈리는 지점:

- 커넥션 풀은 "더 많이 = 더 좋다"가 아니다. DB는 연결 하나마다 메모리·스레드 자원을 쓰므로 풀이 너무 크면 오히려 DB가 과부하된다.
- 커넥션을 빌리고 반환하지 않으면 **커넥션 고갈(pool exhaustion)**이 발생해 이후 요청이 모두 대기 상태에 빠진다.

## 한눈에 보기

커넥션 풀의 흐름을 단순화하면 이렇다.

- 스레드가 요청 → 풀에서 유휴 커넥션 빌림 → SQL 실행 → 반환
- 풀에 여유 커넥션이 없으면 `connectionTimeout`까지 대기
- 타임아웃 초과 시 예외 발생

```
Thread A ──▶ 커넥션 빌림 ──▶ SQL 실행 ──▶ 반환
Thread C ──▶ 풀이 비면 대기
```

## 상세 분해

**풀 크기 (pool size)**

- `maximumPoolSize`: 최대로 유지할 커넥션 수. 보통 CPU 코어 수 × 2 + 디스크 스핀들 수 공식이 출발점이다.
- `minimumIdle`: 유휴 상태에서도 유지할 최소 커넥션 수. 갑작스러운 트래픽에 즉시 대응하기 위해 설정한다.

**대기 타임아웃 (connectionTimeout)**

- 풀에 여유 커넥션이 없을 때 스레드가 기다리는 최대 시간이다.
- 초과하면 예외가 발생한다. 기본값이 30초로 길게 설정된 경우가 많은데, 서비스 응답 시간 SLO에 맞게 줄여야 한다.

**반환 (close / return)**

- JDBC에서 `connection.close()`를 호출하면 풀에 반환된다(연결이 실제로 끊어지는 것이 아니다).
- try-with-resources나 Spring의 트랜잭션 관리가 자동으로 반환을 처리한다.

**HikariCP**

- Spring Boot의 기본 커넥션 풀이다. 가볍고 빠른 구현으로 널리 쓰인다.
- `spring.datasource.hikari.maximum-pool-size` 설정으로 제어한다.

## 흔한 오해와 함정

| 자주 하는 말 | 왜 틀리기 쉬운가 | 더 맞는 첫 대응 |
|---|---|---|
| "풀 크기를 크게 잡으면 안전하다" | DB는 연결마다 자원을 소비하므로 과도한 풀은 DB 장애를 유발할 수 있다 | DB 스펙과 실제 부하를 측정해서 적정 크기를 결정한다 |
| "커넥션을 오래 잡고 있어도 괜찮다" | 트랜잭션 안에서 외부 API 호출이나 긴 작업을 하면 그 시간만큼 커넥션을 독점한다 | 트랜잭션 범위를 짧게 유지하고, 외부 I/O는 트랜잭션 밖으로 꺼낸다 |
| "커넥션 고갈은 서버가 죽어야 생긴다" | 트래픽이 갑자기 몰리거나 느린 쿼리가 커넥션을 점유하면 평시에도 발생한다 | 모니터링으로 활성 커넥션 수와 대기 시간을 상시 관측한다 |

## 실무에서 쓰는 모습

**(1) Spring Boot 기본 설정** — `application.yml`에 `spring.datasource.hikari.maximum-pool-size: 10` 한 줄로 최대 풀 크기를 지정한다. 기본값은 10이다.

**(2) 커넥션 고갈 진단** — HikariCP는 풀 고갈 시 로그에 `HikariPool-1 - Connection is not available, request timed out after 30000ms` 메시지를 남긴다. 이 메시지가 보이면 풀 크기, 쿼리 성능, 트랜잭션 길이를 순서대로 확인한다.

## 더 깊이 가려면

- 커넥션 풀과 트랜잭션 전파, 벌크 쓰기 패턴 → [Connection Pool, Transaction Propagation, Bulk Write](./connection-pool-transaction-propagation-bulk-write.md)
- JDBC·JPA·MyBatis에서 커넥션 풀이 어떻게 사용되는지 → [JDBC, JPA, MyBatis](./jdbc-jpa-mybatis.md)

cross-category bridge:

- Spring의 `@Transactional`이 커넥션 풀에서 커넥션을 언제 빌리고 반환하는지는 spring 카테고리의 transactional-deep-dive 참고

## 면접/시니어 질문 미리보기

> Q: 커넥션 풀이 없으면 어떤 문제가 생기나요?
> 의도: 연결 생성 비용과 재사용의 필요성을 이해하는지 확인
> 핵심: 요청마다 새 DB 연결을 만들면 TCP 핸드셰이크·인증 비용이 매번 발생해 응답 시간이 느려지고, 동시 요청이 많으면 DB가 과부하된다.

> Q: 커넥션 풀 크기를 어떻게 결정하나요?
> 의도: "크면 클수록 좋다"는 오해를 극복했는지 확인
> 핵심: DB가 연결마다 자원을 소비하므로 서버 코어 수·DB 스펙·실제 쿼리 지연을 측정해 결정하고, 부하 테스트로 검증한다.

## 한 줄 정리

커넥션 풀은 DB 연결을 미리 만들어 재사용하는 캐시이고, 풀 크기는 너무 작으면 대기 장애, 너무 크면 DB 과부하가 생기므로 측정 기반으로 설정해야 한다.
