---
schema_version: 3
title: Virtual Threads(Project Loom)
concept_id: language/virtual-threads-project-loom
canonical: true
category: language
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- virtual-thread-is-not-async
- carrier-thread-pinning
- loom-vs-reactive-boundary
aliases:
- virtual thread
- project loom
- java virtual threads
- loom carrier thread
- loom pinning
- mount unmount
- blocking io with loom
- virtual thread vs platform thread
- thread per request loom
- virtual thread reactive 비교
symptoms:
- blocking 코드는 그대로인데 virtual thread를 왜 쓰는지 감이 안 와
- reactive로 가야 할지 loom으로도 충분한지 비교 기준이 필요해
- carrier thread랑 pinning 얘기가 나오면 어디까지가 핵심인지 헷갈려
intents:
- definition
- comparison
- deep_dive
prerequisites:
- language/java-thread-basics
- language/java-concurrency-utilities
- operating-system/io-models-and-event-loop
next_docs:
- language/virtual-thread-migration-pinning
- language/virtual-thread-framework-integration
- language/mvc-async-executor-boundaries
linked_paths:
- contents/language/java/java-thread-basics.md
- contents/language/java/java-concurrency-utilities.md
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/virtual-thread-mvc-async-executor-boundaries.md
- contents/language/java/jvm-gc-jmm-overview.md
- contents/operating-system/io-models-and-event-loop.md
- contents/operating-system/syscall-user-kernel-boundary.md
- contents/spring/spring-mvc-request-lifecycle.md
confusable_with:
- language/virtual-thread-migration-pinning
- language/virtual-thread-framework-integration
- language/virtual-thread-reactive-db
forbidden_neighbors:
- contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/virtual-thread-mvc-async-executor-boundaries.md
expected_queries:
- Java virtual thread가 platform thread랑 어떻게 다른지 전체 그림부터 설명해줘
- Project Loom이 blocking 코드를 유지한 채 동시성을 늘린다는 말이 무슨 뜻이야
- virtual thread와 reactive 중 언제 무엇을 먼저 떠올려야 하는지 알고 싶어
- carrier thread, mount, pinning을 입문자가 헷갈리지 않게 정리한 문서가 필요해
- thread per request 모델이 Loom에서 왜 다시 가능해졌는지 설명해줘
- JDBC나 HTTP 호출이 많은 서버에서 Loom이 어디까지 도움 되는지 큰 그림을 보고 싶어
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 Virtual Thread를 기존 platform thread와
  비교하며 Project Loom이 blocking 스타일 코드를 유지한 채 어떤 종류의
  동시성 이득을 주는지 전체 그림부터 잡는 canonical primer다. carrier
  thread, mount/unmount, pinning, thread-per-request 복귀, reactive와
  Loom 비교, DB나 HTTP 대기 시간이 많은 서버에서 어느 병목이 줄고 어느
  자원 제약은 그대로 남는지 같은 자연어 paraphrase가 본 문서의 핵심
  개념에 매핑된다.
---
# Virtual Threads(Project Loom)

> 한 줄 요약: Virtual Thread는 "스레드를 더 싸게 많이 쓰는 방법"이 아니라, blocking 코드를 유지한 채 더 많은 동시성을 다루게 해주는 실행 모델이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
> - [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [I/O 모델과 이벤트 루프](../../operating-system/io-models-and-event-loop.md)
> - [시스템 콜과 User-Kernel Boundary](../../operating-system/syscall-user-kernel-boundary.md)
> - [Spring MVC 요청 생명주기](../../spring/spring-mvc-request-lifecycle.md)

> retrieval-anchor-keywords: virtual thread, Loom, carrier thread, pinning, mount unmount, blocking I/O, virtual thread migration, ThreadLocal, ScopedValue, per task executor, pool boundary, Spring, JDBC, HttpClient

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [Platform Thread와 무엇이 다른가](#platform-thread와-무엇이-다른가)
- [Scheduler, Mount, Pinning](#scheduler-mount-pinning)
- [Blocking I/O와의 관계](#blocking-io와의-관계)
- [Servlet, Reactive와의 비교](#servlet-reactive와의-비교)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [추천 공식 자료](#추천-공식-자료)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

retrieval-anchor-keywords: Java virtual threads, Project Loom, carrier thread, pinning, mount unmount, blocking I/O with virtual threads, thread per request with loom, virtual thread scheduler, synchronized pinning, servlet vs reactive vs virtual threads

## 왜 중요한가

백엔드 서버는 결국 "동시에 들어오는 요청을 얼마나 안정적으로 버티는가"의 문제를 푼다.

기존의 Platform Thread 모델은 단순하고 직관적이지만, 요청마다 스레드를 하나씩 붙이면 다음 비용이 따라온다.

- 스레드 생성/전환 비용
- 메모리 스택 비용
- 스레드 풀 고갈
- blocking I/O 대기 중 자원 낭비

Virtual Thread는 이 문제를 **코드를 크게 바꾸지 않고** 줄이려는 시도다.  
즉, 비동기 콜백 지옥으로 넘어가기 전에 "blocking 코드를 그대로 유지한 채 확장성"을 얻는 선택지다.

---

## Platform Thread와 무엇이 다른가

Platform Thread는 OS 커널 스레드에 거의 1:1로 대응한다.  
Virtual Thread는 JVM이 관리하는 더 가벼운 실행 단위다.

핵심 차이:

- Platform Thread는 비싸다
- Virtual Thread는 더 많이 만들 수 있다
- Platform Thread는 OS 스케줄러가 직접 관리한다
- Virtual Thread는 JVM이 carrier thread 위에 올려서 관리한다

중요한 건 Virtual Thread가 "CPU를 더 빨리 만드는 기술"은 아니라는 점이다.  
대신 **대기하는 동안의 낭비를 줄이는 기술**에 가깝다.

### 언제 이점이 큰가

- DB/HTTP 호출처럼 blocking I/O가 많은 서비스
- 요청이 많고, 각 요청이 짧게 기다렸다가 끝나는 서비스
- 기존 Servlet 기반 코드를 크게 바꾸고 싶지 않은 경우

### 언제 이점이 작나

- CPU 연산이 대부분인 작업
- 이미 완전한 reactive/non-blocking 파이프라인을 가진 경우
- synchronized/native 호출 때문에 pinning이 잦은 경우

---

## Scheduler, Mount, Pinning

Virtual Thread는 내부적으로 carrier thread에 올라타 실행된다.

개념적으로 보면:

1. Virtual Thread가 실행된다
2. JVM이 carrier thread에 mount한다
3. blocking I/O를 만나면, 가능하면 unmount하고 다른 Virtual Thread가 carrier를 사용한다
4. 작업이 재개되면 다시 mount된다

이 구조 덕분에 Platform Thread를 많이 붙잡아 둘 필요가 줄어든다.

### Pinning이란

문제는 모든 blocking이 다 예쁘게 빠져나오는 것은 아니라는 점이다.  
Virtual Thread가 carrier thread에 **고정(pin)** 된 채로 빠져나오지 못하는 상황이 있다.

대표 원인:

- `synchronized` 블록 안에서 blocking I/O 수행
- 일부 native call
- JVM이 언마운트할 수 없는 구간

Pinning이 많으면 Virtual Thread의 장점이 줄어든다.  
즉, "가볍게 많이 쓴다"는 장점이 **잠금 구간** 때문에 깨질 수 있다.

### 왜 이걸 봐야 하나

Virtual Thread를 도입했는데 기대만큼 스레드 수가 안 줄거나, latency가 흔들리면 보통 pinning부터 의심한다.  
성능 문제가 "스레드가 많아서"가 아니라 "스레드가 잘 못 내려와서"일 수 있다.

---

## Blocking I/O와의 관계

Virtual Thread의 핵심 가치는 **blocking I/O를 나쁜 것으로 취급하지 않아도 된다**는 점이다.

기존에는 blocking I/O가 많으면:

- thread pool을 크게 잡아야 하고
- 그러다 고갈될 수 있고
- 결국 non-blocking 구조로 바꾸자는 압력이 생겼다

Virtual Thread는 이 압력을 완화한다.

하지만 다음은 여전히 중요하다.

- DB 커넥션 풀 크기
- 외부 API timeout
- backpressure
- 동시 요청 제한

즉, 스레드가 싸졌다고 해서 **모든 병목이 사라지는 건 아니다**.  
대기 비용은 줄어도, DB나 외부 시스템의 처리량은 그대로다.

---

## Servlet, Reactive와의 비교

### Servlet + Platform Thread

- 요청당 스레드 모델이 직관적이다
- blocking 코드를 그대로 쓴다
- 스레드 수가 많아지면 메모리/컨텍스트 스위칭 비용이 커진다

### Servlet + Virtual Thread

- 코드는 거의 그대로 두고 동시성을 늘리기 좋다
- blocking 스타일을 유지할 수 있다
- OS 스레드 수보다 훨씬 많은 요청을 버티기 쉽다

### Reactive

- event loop와 non-blocking I/O를 중심으로 설계한다
- 스레드 수를 줄이고 자원을 효율적으로 쓴다
- 대신 사고방식과 디버깅 모델이 더 복잡하다

결론적으로:

- 기존 Servlet 코드를 살리고 싶으면 Virtual Thread가 현실적이다
- 완전한 비동기 파이프라인이 필요하면 Reactive가 맞을 수 있다
- CPU-bound 문제를 풀려면 둘 다 큰 차이는 없다

> 이벤트 루프 관점은 [I/O 모델과 이벤트 루프](../../operating-system/io-models-and-event-loop.md)를 함께 보면 좋다.

---

## 실전 시나리오

### 시나리오 1: thread pool exhaustion

기존 서비스가 요청마다 blocking DB 호출을 하고 있는데, 트래픽이 증가하면서 thread pool이 꽉 차는 경우가 있다.

Virtual Thread를 쓰면:

- 작업 대기 중 carrier thread를 덜 점유한다
- thread pool sizing 부담이 줄어든다
- 응답 지연이 완만해질 수 있다

하지만 DB 커넥션 풀 자체가 작으면, 결국 그 지점에서 막힌다.

### 시나리오 2: `synchronized` 안에서 I/O

```java
public synchronized void refresh() {
    client.callSlowApi(); // 여기서 pinning이 발생할 수 있다
}
```

이 패턴은 Virtual Thread의 장점을 깎아먹을 수 있다.  
잠금 구간을 좁히거나, blocking I/O를 lock 밖으로 빼는 쪽이 낫다.

### 시나리오 3: 운영에서 "스레드는 많은데 CPU는 놀고 있다"

이럴 때 원인이 항상 스레드 부족은 아니다.

- 외부 API timeout 대기
- DB 커넥션 대기
- pinning
- GC pause

같은 원인이 있을 수 있다. Virtual Thread는 도구일 뿐, 병목 분석을 대체하지 않는다.

---

## 코드로 보기

### 1. Virtual Thread로 작업 실행

```java
var httpClient = java.net.http.HttpClient.newHttpClient();

try (var executor = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 1_000; i++) {
        int taskId = i;
        executor.submit(() -> {
            var request = java.net.http.HttpRequest.newBuilder(
                    java.net.URI.create("https://example.com/users/" + taskId))
                .GET()
                .build();

            String body = httpClient
                .send(request, java.net.http.HttpResponse.BodyHandlers.ofString())
                .body();

            System.out.println(taskId + ": " + body);
            return null;
        });
    }
}
```

이 코드는 "스레드를 직접 많이 만든다"기보다, **작업당 가벼운 실행 단위**를 쓰는 쪽에 가깝다.  
`HttpClient`의 blocking `send()`를 그대로 두고도 확장성을 얻는 점이 핵심이다.

### 2. pinning을 유발할 수 있는 형태

```java
public class CacheService {
    public synchronized String load(String key) {
        return slowClient.fetch(key);
    }
}
```

이런 구조는 lock 안에서 blocking I/O를 수행한다.  
Virtual Thread를 쓴다고 해도 carrier thread가 묶일 수 있다.

### 3. Servlet 스타일과 비교

```java
@GetMapping("/users/{id}")
public UserDto getUser(@PathVariable long id) {
    return userService.findById(id);
}
```

이 코드는 Servlet 기반 blocking 스타일의 전형이다.  
Virtual Thread 환경에서는 이런 코드를 크게 바꾸지 않아도 동시성 확장 이점을 얻기 쉽다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Platform Thread + Servlet | 단순하고 익숙하다 | blocking I/O에 약하다 | 트래픽이 작고 구조 단순할 때 |
| Virtual Thread + Servlet | 기존 코드를 거의 그대로 유지 가능 | pinning, 커넥션 풀 병목은 남는다 | blocking 코드가 많고 점진적 개선이 필요할 때 |
| Reactive | 높은 자원 효율성과 backpressure 모델 | 학습/디버깅 비용이 크다 | end-to-end non-blocking이 중요한 경우 |

판단 기준은 명확하다.

- 팀이 빠르게 도입해야 하면 Virtual Thread가 현실적이다
- 전체 파이프라인을 비동기로 재구성할 계획이면 Reactive를 검토한다
- CPU 병목이면 스레드 모델보다 알고리즘/캐시/DB를 먼저 본다

---

## 추천 공식 자료

- JEP 444: Virtual Threads
  - https://openjdk.org/jeps/444
- JDK `Executors` API
  - https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/concurrent/Executors.html
- JDK `Thread` API
  - https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/lang/Thread.html

---

## 꼬리질문

> Q: Virtual Thread를 쓰면 thread pool 튜닝은 이제 필요 없나요?
> 의도: 스레드 비용과 downstream 병목을 구분하는지 확인
> 핵심: 스레드는 싸졌어도 DB 커넥션 풀, 외부 API, rate limit은 여전히 병목이다

> Q: pinning이 왜 문제인가요?
> 의도: carrier thread와 mount/unmount 모델 이해 확인
> 핵심: Virtual Thread가 carrier를 놓지 못하면 스케줄링 이점이 사라진다

> Q: Reactive가 있는데 왜 Loom이 필요한가요?
> 의도: 모델 선택 기준 이해 확인
> 핵심: Reactive는 강력하지만 복잡하다. Loom은 blocking 코드를 크게 바꾸지 않고 동시성을 개선한다

> Q: Virtual Thread가 CPU-bound 작업도 빨라지나요?
> 의도: 오해 방지
> 핵심: 아니다. Virtual Thread는 대기 시간을 효율화하는 기술이지 계산 자체를 빠르게 하지 않는다

---

## 한 줄 정리

Virtual Thread는 blocking 코드를 유지하면서 더 많은 동시성을 다루게 해주는 JVM 실행 모델이고, 실제 성능은 pinning과 downstream 병목을 같이 봐야 한다.
