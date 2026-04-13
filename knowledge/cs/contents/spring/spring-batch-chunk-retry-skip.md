# Spring Batch Chunk Retry Skip

> 한 줄 요약: Spring Batch의 chunk 처리, retry, skip은 "실패를 무시하는 기능"이 아니라, 어디까지 다시 시도하고 어디서 멈출지 정하는 정교한 경계 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Spring Scheduler / Async Boundaries](./spring-scheduler-async-boundaries.md)
> - [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)
> - [트랜잭션 실전 시나리오](../database/transaction-case-studies.md)
> - [Outbox, Saga, Eventual Consistency](../software-engineering/outbox-inbox-domain-events.md)

## 핵심 개념

Spring Batch는 대량 데이터를 안전하게 처리하기 위한 프레임워크다.

핵심 구조는 보통 이렇다.

- `Job`: 전체 작업
- `Step`: 하나의 실행 단위
- `ItemReader`: 읽기
- `ItemProcessor`: 변환
- `ItemWriter`: 쓰기
- `Chunk`: 한 번에 커밋할 묶음

`chunk`는 단순 배치 크기가 아니라 트랜잭션 경계다.
즉 `chunk` 하나가 성공해야 커밋되고, 실패하면 그 범위로 되돌린다.

retry와 skip은 여기서 방향이 다르다.

- `retry`: 같은 아이템을 다시 시도한다.
- `skip`: 해당 아이템을 건너뛴다.

## 깊이 들어가기

### 1. chunk는 트랜잭션 경계다

예를 들어 100개씩 chunk를 잡으면, 100개 처리 후 커밋한다.

- 중간 실패 시 chunk 전체가 롤백될 수 있다.
- chunk를 너무 크게 잡으면 롤백 비용이 커진다.
- 너무 작게 잡으면 커밋 비용과 오버헤드가 커진다.

### 2. retry는 transient failure에 쓰고, skip은 data failure에 쓴다

retry가 적합한 경우:

- 네트워크 일시 장애
- DB deadlock
- 외부 API timeout

skip이 적합한 경우:

- 특정 레코드 데이터 오염
- 파싱 불가능한 형식
- 비즈니스 규칙 위반 레코드

### 3. idempotency가 없으면 배치가 두 번 쓰는 순간 문제가 된다

배치 재시작, retry, chunk rollback은 결국 같은 레코드를 다시 보게 만든다.
그래서 writer는 멱등하게 설계해야 한다.

이 관점은 [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md)와 같이 봐야 한다.

### 4. restartability는 JobRepository와 ExecutionContext에 달렸다

배치가 중간에 죽어도 어디까지 했는지 기억해야 한다.

- `JobRepository`: 실행 상태 저장
- `ExecutionContext`: 재시작 포인트 저장

이 둘이 없으면 "실패 후 재실행"이 아니라 "처음부터 다시"가 된다.

## 실전 시나리오

### 시나리오 1: 외부 API가 가끔 타임아웃 난다

이 경우 retry를 두고, backoff를 넣는다.

문제는 retry를 무한히 하면 배치 전체가 늦어진다는 점이다.

대응:

- retry limit을 둔다.
- 재시도 간격을 점진적으로 늘린다.
- 실패한 건 skip하거나 별도 보관한다.

### 시나리오 2: 한 레코드만 파싱이 깨진다

이 경우 skip이 적합하다.

하지만 skip을 남용하면 데이터 품질 문제가 숨는다.
그래서 skip된 레코드는 별도 테이블이나 파일로 남겨야 한다.

### 시나리오 3: writer가 같은 row를 다시 쓴다

재시작이나 retry 때 자주 생긴다.

대응:

- upsert로 바꾼다.
- natural key를 기준으로 중복 방지한다.
- writer를 멱등하게 만든다.

## 코드로 보기

### fault tolerant step

```java
@Bean
public Step importStep(JobRepository jobRepository, PlatformTransactionManager transactionManager) {
    return new StepBuilder("importStep", jobRepository)
        .<InputRow, OutputRow>chunk(100, transactionManager)
        .reader(reader())
        .processor(processor())
        .writer(writer())
        .faultTolerant()
        .retry(DeadlockLoserDataAccessException.class)
        .retryLimit(3)
        .skip(FlatFileParseException.class)
        .skipLimit(50)
        .build();
}
```

### skip listener

```java
@Component
public class SkipLogger extends SkipListenerSupport<InputRow, OutputRow> {
    @Override
    public void onSkipInProcess(InputRow item, Throwable t) {
        // skip된 레코드를 별도 저장소에 남긴다
    }
}
```

### writer 멱등성 예시

```java
public void write(List<? extends OutputRow> items) {
    for (OutputRow item : items) {
        jdbcTemplate.update(
            "INSERT INTO target(id, value) VALUES(?, ?) " +
            "ON DUPLICATE KEY UPDATE value = VALUES(value)",
            item.id(), item.value()
        );
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 큰 chunk | 커밋 수가 적다 | 롤백 비용이 크다 | 순수 읽기/쓰기 비용이 낮을 때 |
| 작은 chunk | 실패 복구가 빠르다 | 오버헤드가 커진다 | 실패율이 높고 재시작이 잦을 때 |
| retry 우선 | transient failure에 강하다 | 전체 지연이 커질 수 있다 | timeout/deadlock |
| skip 우선 | 진행률이 유지된다 | 데이터 품질 경보가 필요하다 | 일부 레코드 오염 |

## 꼬리질문

> Q: chunk 크기를 정하는 기준은 무엇인가?
> 의도: 트랜잭션 경계 이해 확인
> 핵심: 롤백 비용, 처리량, commit overhead를 함께 본다.

> Q: retry와 skip을 어떻게 구분하는가?
> 의도: 실패 원인 분류 능력 확인
> 핵심: transient failure는 retry, data failure는 skip이다.

> Q: 배치 writer는 왜 멱등해야 하는가?
> 의도: 재시작과 중복 처리 이해 확인
> 핵심: 배치는 같은 데이터를 여러 번 볼 수 있다.

## 한 줄 정리

Spring Batch의 retry/skip은 실패를 숨기는 기능이 아니라, 어디까지 다시 시도하고 어디서 멈출지 정하는 운영 정책이다.
