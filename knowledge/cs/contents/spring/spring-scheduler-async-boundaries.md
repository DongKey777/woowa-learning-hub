# Spring Scheduler / Async Boundaries

> 한 줄 요약: `@Scheduled`와 `@Async`는 편하지만, 스레드 경계가 생기는 순간 트랜잭션, 보안, 로깅 전파를 같이 설계해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)
> - [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)
> - [Virtual Threads(Project Loom)](../language/java/virtual-threads-project-loom.md)
> - [컨텍스트 스위칭, 데드락, lock-free](../operating-system/context-switching-deadlock-lockfree.md)

## 핵심 개념

Spring에서 `@Scheduled`와 `@Async`는 둘 다 "나중에 다른 스레드에서 실행"한다는 점이 핵심이다.

- `@Scheduled`는 주기적 실행을 만든다.
- `@Async`는 메서드 호출을 즉시 끝내고, 실제 작업은 다른 스레드에 넘긴다.
- 둘 다 호출 스레드와 실행 스레드가 달라질 수 있다.

이 차이를 모르면 다음 문제가 생긴다.

- `@Transactional`이 안 이어진다.
- `SecurityContext`가 사라진다.
- `MDC` 로그가 섞이거나 비어 보인다.
- 예외가 호출자까지 안 올라온다.

핵심은 단순하다. 스레드 경계가 생기면 "자동으로 따라오던 것"은 대부분 사라진다.

## 깊이 들어가기

### 1. `@Scheduled`는 운영자 관점의 작업이다

스케줄러는 주로 배치, 정리 작업, 헬스 체크, 집계 작업에 쓰인다.

중요한 점은 실행이 한 번 밀리면 다음 실행도 영향을 받는다는 것이다.

- 작업이 오래 걸리면 다음 tick이 밀린다.
- 같은 작업이 중복 실행되면 데이터가 꼬일 수 있다.
- 단일 인스턴스에서만 돌리면 장애 시 작업이 끊긴다.

### 2. `@Async`는 호출자와 분리된다

`@Async` 메서드는 프록시를 통해 다른 executor로 넘겨진다.

즉 다음이 달라진다.

- 호출자 스레드
- 실제 실행 스레드
- 예외 전달 방식
- 트랜잭션 경계

### 3. 컨텍스트 전파는 자동이 아니다

스레드가 바뀌면 다음은 직접 처리해야 한다.

- `SecurityContext`
- `MDC`
- `TransactionSynchronizationManager`
- 요청 범위 객체

그래서 `@Async` 내부에서 DB 작업, 인증 정보, 로깅을 쓸 때는 전파 전략이 필요하다.

### 4. executor 크기는 기능이 아니라 운영 결정이다

executor를 너무 작게 잡으면 병목이 되고, 너무 크게 잡으면 컨텍스트 스위칭과 메모리 비용이 늘어난다.

이 판단은 [컨텍스트 스위칭, 데드락, lock-free](../operating-system/context-switching-deadlock-lockfree.md)와 [Virtual Threads(Project Loom)](../language/java/virtual-threads-project-loom.md)를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 주문 완료 후 이메일 발송을 `@Async`로 넘겼다

주문 저장은 성공했지만, 이메일 발송 예외가 누락되면 운영자는 실패를 늦게 안다.

대응 포인트:

- 호출자 성공과 보조 작업 성공을 분리할지 정한다.
- 실패 재시도와 dead letter 전략을 둔다.
- 중요한 작업이면 큐 기반 비동기로 넘긴다.

### 시나리오 2: 스케줄러가 두 대에서 동시에 돈다

인스턴스가 두 대 이상이면 같은 `@Scheduled` 작업이 중복 실행될 수 있다.

대응 포인트:

- 분산 락을 둔다.
- 리더 선출을 둔다.
- 아예 별도 작업 스케줄러를 둔다.

### 시나리오 3: `@Async` 안에서 `@Transactional`을 기대했다

비동기 스레드에서는 호출 스레드의 트랜잭션이 이어지지 않는다.

이 문제는 [Spring Transaction Debugging Playbook](./spring-transaction-debugging-playbook.md)에서 보는 프록시/경계 문제와 같이 본다.

## 코드로 보기

### executor 설정

```java
@Configuration
@EnableAsync
@EnableScheduling
public class AsyncConfig {

    @Bean(name = "applicationTaskExecutor")
    public ThreadPoolTaskExecutor applicationTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(8);
        executor.setMaxPoolSize(32);
        executor.setQueueCapacity(1000);
        executor.setThreadNamePrefix("app-async-");
        executor.initialize();
        return executor;
    }
}
```

### async 메서드

```java
@Service
public class MailService {

    @Async("applicationTaskExecutor")
    public CompletableFuture<Void> sendWelcomeMail(Long userId) {
        // SecurityContext, MDC, Transaction context는 자동 전파되지 않을 수 있다.
        return CompletableFuture.completedFuture(null);
    }
}
```

### scheduled 메서드

```java
@Component
public class MaintenanceJob {

    @Scheduled(cron = "0 0 * * * *")
    public void compactStatistics() {
        // 길어지면 다음 tick이 밀린다.
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@Async` | 구현이 쉽다 | 컨텍스트 전파와 예외 처리가 어렵다 | 단순 보조 작업 |
| `@Scheduled` | 반복 작업이 쉽다 | 중복 실행과 장애 복구를 따로 설계해야 한다 | 정기 작업 |
| 큐 기반 비동기 | 재시도와 분리가 쉽다 | 시스템이 하나 더 늘어난다 | 중요한 후처리 |
| Virtual Threads | blocking 코드를 덜 바꿔도 된다 | pinning과 운영 감시가 필요하다 | 동시 요청이 많고 코드 단순성이 중요할 때 |

## 꼬리질문

> Q: `@Async` 안에서 트랜잭션이 왜 이어지지 않는가?
> 의도: 스레드 경계와 프록시 경계 이해 확인
> 핵심: 호출 스레드와 실행 스레드가 다르다.

> Q: `@Scheduled` 작업이 두 인스턴스에서 중복 실행되면 어떻게 막는가?
> 의도: 운영 환경의 분산 실행 이해 확인
> 핵심: 분산 락, 리더 선출, 별도 작업기 중 하나가 필요하다.

> Q: executor를 무작정 크게 늘리면 왜 안 되는가?
> 의도: 컨텍스트 스위칭과 큐잉 비용 이해 확인
> 핵심: 더 많은 스레드가 더 빠른 것은 아니다.

## 한 줄 정리

`@Scheduled`와 `@Async`는 편한 대신, 스레드 경계를 기준으로 트랜잭션과 컨텍스트를 다시 설계해야 한다.
