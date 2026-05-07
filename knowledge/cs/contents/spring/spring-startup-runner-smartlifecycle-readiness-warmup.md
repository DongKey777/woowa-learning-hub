---
schema_version: 3
title: Spring Startup Runner SmartLifecycle Readiness Warmup
concept_id: spring/startup-runner-smartlifecycle-readiness-warmup
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
review_feedback_tags:
- startup-runner-smartlifecycle
- readiness-warmup
- commandlinerunner-applicationrunner-smartlifecycle
- startup-warmup-readiness
aliases:
- CommandLineRunner ApplicationRunner SmartLifecycle
- Spring startup warmup readiness
- startup hook selection
- application context refresh phases
- readiness before traffic
- graceful shutdown lifecycle
intents:
- comparison
- design
- troubleshooting
linked_paths:
- contents/spring/spring-application-context-refresh-phases.md
- contents/spring/spring-boot-autoconfiguration.md
- contents/spring/spring-actuator-exposure-security.md
- contents/spring/spring-observability-micrometer-tracing.md
- contents/spring/spring-scheduler-async-boundaries.md
- contents/spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md
symptoms:
- startup hook에서 외부 API나 cache warmup을 실행했더니 readiness 전에 traffic이 들어온다.
- CommandLineRunner에 오래 걸리는 작업을 넣어 boot가 멈춘 것처럼 보인다.
- shutdown 때 background lifecycle bean 정리가 startup 순서와 맞지 않는다.
expected_queries:
- CommandLineRunner ApplicationRunner SmartLifecycle은 언제 골라야 해?
- Spring readiness 이전 warmup 작업은 어디에 둬야 해?
- startup hook이 boot를 막아도 되는 작업과 비동기로 돌릴 작업은 어떻게 나눠?
- SmartLifecycle은 startup과 shutdown 순서에서 어떤 장점이 있어?
contextual_chunk_prefix: |
  이 문서는 Spring startup hook 선택을 취향이 아니라 boot blocking 여부, readiness before
  traffic, warmup completion, lifecycle phase, shutdown reverse ordering 기준으로 설명하는
  playbook이다.
---
# Spring Startup Hooks: `CommandLineRunner`, `ApplicationRunner`, `SmartLifecycle`, and Readiness Warmup

> 한 줄 요약: Spring startup hook 선택은 단순 취향이 아니라, 어떤 작업이 부팅을 막아야 하는지, readiness 이전에 끝나야 하는지, shutdown 때 역순 정리가 필요한지를 정하는 운영 설계다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Actuator Exposure and Security](./spring-actuator-exposure-security.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Spring Scheduler와 Async 경계](./spring-scheduler-async-boundaries.md)

retrieval-anchor-keywords: CommandLineRunner, ApplicationRunner, SmartLifecycle, ApplicationReadyEvent, ApplicationStartedEvent, readiness warmup, startup hook, application availability, cache preload, startup ordering

## 핵심 개념

Spring 애플리케이션이 "시작됐다"는 말은 한 시점을 뜻하지 않는다.

실제로는 여러 단계가 있다.

- Bean이 초기화되는 시점
- 컨텍스트 refresh가 끝나는 시점
- background component가 시작되는 시점
- runner가 실행되는 시점
- readiness가 열려서 실제 트래픽을 받는 시점

그래서 startup hook을 고를 때 질문은 "어디에 코드 넣을까?"가 아니다.

- 이 작업이 실패하면 부팅을 중단해야 하는가
- 이 작업이 끝날 때까지 readiness를 열면 안 되는가
- 시작뿐 아니라 종료 순서도 제어해야 하는가
- 프록시/트랜잭션/관측이 다 준비된 뒤에 실행돼야 하는가

이 질문을 먼저 분리해야 한다.

## 깊이 들어가기

### 1. startup hook은 생명주기 위치가 다르다

감각적으로 정리하면 아래와 같다.

- `@PostConstruct`: 개별 Bean 초기화 시점
- `SmartLifecycle.start()`: 컨텍스트 refresh 막바지에 start/stop 관리 대상 컴포넌트 시작
- `ApplicationStartedEvent`: 컨텍스트는 올랐지만 runner 전
- `CommandLineRunner` / `ApplicationRunner`: started 이후, ready 이전
- `ApplicationReadyEvent`: runner까지 모두 끝난 뒤

즉 똑같이 "앱 시작 시 실행"처럼 보여도, **프록시 준비 상태와 readiness에 미치는 영향이 다르다**.

### 2. `@PostConstruct`는 운영 부트스트랩 훅으로 남용하기 쉽다

`@PostConstruct`는 Bean 단위 초기화에 적합하다.

하지만 아래 같은 작업을 넣으면 위험하다.

- 외부 API 호출
- 긴 캐시 워밍
- 메시지 컨슈머 기동
- `@Transactional`을 기대하는 자기 자신 메서드 호출

이 시점은 아직 전체 애플리케이션이 안정적으로 준비됐다고 보기 어렵다.

특히 프록시 경계와 lifecycle ordering을 제대로 의식하지 않으면, "초기화는 됐는데 왜 트랜잭션/관측/보안이 기대와 다르지?"라는 문제가 나온다.

### 3. runner는 readiness를 지연시키는 훅이다

`CommandLineRunner`와 `ApplicationRunner`는 보통 부팅 끝무렵, ready 직전에 실행된다.

따라서 이 안에서 오래 걸리는 작업을 하면 다음이 벌어진다.

- 앱 프로세스는 떠 있다
- 하지만 ready 상태는 늦어진다
- Kubernetes나 load balancer 입장에서는 아직 트래픽을 받지 못할 수 있다

즉 runner는 "시작 후 백그라운드 작업"보다, **ready 전에 반드시 끝나야 하는 작업**에 더 가깝다.

`ApplicationRunner`는 인자를 구조적으로 다루기 쉽고, `CommandLineRunner`는 단순 문자열 배열이면 충분할 때 쓰면 된다.

### 4. `SmartLifecycle`은 start/stop 순서 제어용이다

`SmartLifecycle`은 단순 한 번 실행되는 hook이 아니라, 시작과 종료를 함께 관리하는 계약이다.

장점은 아래와 같다.

- phase로 순서를 제어할 수 있다
- shutdown 때 `stop()`도 함께 제어할 수 있다
- 메시지 consumer, relay worker, polling loop처럼 장기 실행 컴포넌트에 맞다

즉 warmup 코드보다, **오래 살아 있는 background component의 생명주기 제어**에 더 잘 맞는다.

### 5. readiness는 "프로세스가 떴다"보다 더 강한 계약이다

운영에서 중요한 것은 JVM이 살아 있느냐보다, 실제로 트래픽을 받아도 되느냐다.

그래서 startup 설계는 readiness와 붙어 생각해야 한다.

- 마이그레이션 확인 전에는 준비 안 됨
- 핵심 캐시 로딩 전에는 준비 안 됨
- 필수 downstream dependency가 아직 불안정하면 준비 안 됨

반대로 비필수 워밍 작업은 readiness 이후 백그라운드로 돌릴 수 있다.

핵심은 모든 warmup을 부팅 경로에 넣는 게 아니라, **필수 warmup과 선택적 warmup을 나누는 것**이다.

### 6. 무엇을 block하고 무엇을 background로 밀지 결정해야 한다

판단 기준은 보통 아래와 같다.

- 이 작업이 없으면 첫 요청이 실패하는가 -> ready 전에 끝내는 쪽
- 늦어도 되지만 성능만 좋아지는가 -> ready 후 background 가능
- shutdown 때도 반대로 정리해야 하는가 -> `SmartLifecycle` 고려
- 외부 시스템 불안정이 앱 전체 부팅 실패로 이어져야 하는가 -> runner에서 fail fast 여부 결정

즉 startup hook 선택은 코드 취향이 아니라 **서비스 가용성 계약**이다.

## 실전 시나리오

### 시나리오 1: 캐시 preload를 runner에 넣었더니 pod가 오래 Ready가 안 된다

이건 runner가 느린 것이지 Spring이 이상한 게 아니다.

질문은 다음이다.

- 캐시가 없으면 첫 요청이 정말 실패하는가
- 아니면 첫 몇 번의 요청만 느린가

후자라면 background warmup으로 분리하는 편이 낫다.

### 시나리오 2: `@PostConstruct`에서 외부 API를 부르다 startup 장애가 난다

개별 Bean 초기화에 외부 의존성을 넣으면, 애플리케이션 전체 startup 경로가 쉽게 깨진다.

또한 프록시/관측/보안 경계가 완전히 안정되기 전일 수 있다.

### 시나리오 3: 메시지 컨슈머가 DB 마이그레이션보다 먼저 살아난다

이 경우는 background component의 시작 순서가 문제다.

`SmartLifecycle` phase, readiness gate, 초기화 순서를 함께 조정해야 한다.

### 시나리오 4: 앱은 Ready인데 첫 실제 요청에서만 터진다

비필수처럼 보였던 warmup이 사실은 필수 초기화였을 수 있다.

즉 readiness 기준이 너무 느슨했던 것이다.

## 코드로 보기

### ready 전에 끝내야 하는 작업은 `ApplicationRunner`

```java
@Component
public class ReferenceDataWarmup implements ApplicationRunner {

    private final ReferenceDataService referenceDataService;

    public ReferenceDataWarmup(ReferenceDataService referenceDataService) {
        this.referenceDataService = referenceDataService;
    }

    @Override
    public void run(ApplicationArguments args) {
        referenceDataService.loadRequiredData();
    }
}
```

### start/stop 순서를 관리하는 `SmartLifecycle`

```java
@Component
public class RelayWorkerLifecycle implements SmartLifecycle {

    private volatile boolean running;

    @Override
    public void start() {
        running = true;
    }

    @Override
    public void stop() {
        running = false;
    }

    @Override
    public boolean isRunning() {
        return running;
    }

    @Override
    public int getPhase() {
        return 100;
    }
}
```

### ready 이후 비필수 warmup

```java
@Component
public class NonCriticalWarmupListener {

    private final TaskExecutor taskExecutor;
    private final RecommendationCache recommendationCache;

    public NonCriticalWarmupListener(TaskExecutor taskExecutor,
                                     RecommendationCache recommendationCache) {
        this.taskExecutor = taskExecutor;
        this.recommendationCache = recommendationCache;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void warmupAfterReady() {
        taskExecutor.execute(recommendationCache::preload);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `@PostConstruct` | 개별 Bean 초기화가 단순하다 | 외부 의존성, 프록시, 순서 제어에 약하다 | 가벼운 내부 초기화 |
| `CommandLineRunner` / `ApplicationRunner` | ready 이전 필수 작업을 명확히 걸 수 있다 | 오래 걸리면 startup 전체가 느려진다 | 필수 preload, fail-fast 검증 |
| `SmartLifecycle` | start/stop과 phase를 제어할 수 있다 | 단순 일회성 코드에는 과하다 | 장기 실행 background component |
| `ApplicationReadyEvent` | ready 이후 후속 작업에 적합하다 | 필수 warmup에는 늦다 | 비필수 캐시 워밍, 알림, 초기 신호 |

핵심은 "앱 시작 시 실행"이라는 공통점보다, **traffic admission과 shutdown ordering까지 포함한 책임 차이**를 보는 것이다.

## 꼬리질문

> Q: `ApplicationRunner`와 `ApplicationReadyEvent`의 가장 큰 차이는 무엇인가?
> 의도: readiness 영향 이해 확인
> 핵심: 전자는 ready 전에 실행되어 readiness를 지연시킬 수 있고, 후자는 ready 이후 실행된다.

> Q: `SmartLifecycle`이 runner보다 적합한 경우는 언제인가?
> 의도: 장기 실행 컴포넌트 lifecycle 이해 확인
> 핵심: start/stop 순서와 phase 제어가 필요한 background component일 때다.

> Q: `@PostConstruct`에 외부 호출을 넣으면 왜 위험한가?
> 의도: Bean 초기화와 운영 bootstrap 구분 확인
> 핵심: 전체 컨텍스트 준비 전이며 실패 전파와 프록시 경계가 예민하다.

> Q: warmup을 모두 ready 전에 끝내면 왜 나쁠 수 있는가?
> 의도: 가용성과 startup latency 균형 확인
> 핵심: 비필수 작업까지 boot critical path에 넣으면 rollout과 복구가 느려진다.

## 한 줄 정리

Spring startup hook 선택은 "코드를 어디에 둘까"가 아니라, 어떤 작업이 readiness 이전 필수인지와 어떤 컴포넌트가 start/stop 순서를 가져야 하는지를 정하는 운영 설계다.
