# Structured Fan-out With `HttpClient`

> 한 줄 요약: 여러 원격 호출이 같은 요청 수명 안에서 함께 성공하거나 함께 포기되어야 할 때는 virtual thread 위의 blocking `HttpClient.send()`를 `StructuredTaskScope`-style fan-out으로 묶고, parent deadline, retry 상한, cancellation, remote concurrency cap을 같은 budget으로 설계한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Structured Concurrency and `ScopedValue`](./structured-concurrency-scopedvalue.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Partial Success Fan-in Patterns](./partial-success-fan-in-patterns.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Idempotency Keys and Safe HTTP Retries](./httpclient-idempotency-keys-safe-http-retries.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [Remote Bulkhead Metrics Under Virtual Threads](./remote-bulkhead-metrics-under-virtual-threads.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
> - [`CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards](./completablefuture-allof-join-timeout-exception-handling-hazards.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: structured fan-out HttpClient, StructuredTaskScope HttpClient, virtual thread HttpClient fan-out, blocking send with virtual threads, request scoped fan-out, fail-fast remote calls, parent deadline budget, retry cap, remote concurrency cap, semaphore bulkhead, per-upstream semaphore sizing, bulkhead metrics, permit contention, cancellation propagation, interrupt-aware HttpClient, fan-out retry storm, retry storm metrics, idempotency key, safe POST retry, 307 308 redirect replay, partial success fan-in, degradation tier, aggregate error report, optional downstream result, structured cancellation, remote rate limit budget, servlet async timeout outbound HTTP, request deadline propagation, request timeout to HttpRequest.timeout, connection budget alignment after loom, datasource pool vs HTTP bulkhead

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [언제 이 조합을 쓰는가](#언제-이-조합을-쓰는가)
- [예산 모델: deadline, retry, concurrency](#예산-모델-deadline-retry-concurrency)
- [실패와 취소 의미 정리](#실패와-취소-의미-정리)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [관측 체크리스트](#관측-체크리스트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

virtual thread는 blocking I/O를 싸게 만든다.  
하지만 fan-out 설계의 핵심은 thread 수가 아니라 **부모 요청이 자식 원격 호출들을 어떻게 소유하느냐**다.

`StructuredTaskScope`-style fan-out이 필요한 순간은 보통 이렇다.

- 여러 원격 호출이 같은 request/operation deadline을 공유한다
- 한 하위 호출이 실패하거나 deadline을 넘기면 나머지도 같이 포기하는 편이 낫다
- 결과가 "이 요청의 응답"으로만 의미가 있고, 요청 종료 뒤까지 살아남으면 안 된다
- fan-out 폭, retry 횟수, upstream rate limit을 요청 단위로 같이 묶어야 한다

반대로 virtual thread만 있다고 해서 모든 outbound HTTP를 fan-out으로 바꿀 이유는 없다.  
독립 호출이 한두 개뿐이면 caller virtual thread에서 straight-line `send()`가 더 단순하다.

## 언제 이 조합을 쓰는가

| 상황 | 권장 패턴 | 이유 |
|---|---|---|
| 요청 안에서 원격 호출 1~2개를 순차적으로 부른다 | caller virtual thread에서 blocking `send()` | 취소와 로그 흐름이 단순하고 extra fan-out budget이 필요 없다 |
| 서로 독립적인 원격 호출 여러 개를 같은 요청 deadline 안에서 병렬화한다 | virtual thread + `StructuredTaskScope`-style fan-out + blocking `send()` | parent lifetime, fail-fast, cancellation을 한 scope로 묶기 쉽다 |
| 일부 결과만 있어도 응답이 가능하다 | structured fan-out은 유지하되, subtask가 예외 대신 typed result를 반환 | 요청 수명은 묶되 partial success semantics를 명시할 수 있다 |
| 요청이 끝나도 계속 살아야 하는 재시도/보상 작업이다 | queue/outbox/scheduler로 분리 | request-scoped fan-out에 넣으면 orphan work와 shutdown ownership이 흐려진다 |
| 고밀도 streaming, 장시간 subscription, callback 조합이 핵심이다 | 별도 async/reactive model 검토 | structured request fan-out보다 connection/session lifetime이 더 중요하다 |

판단 기준은 "비동기가 필요하냐"가 아니라 다음 두 질문이다.

- 이 작업은 부모 요청이 끝나면 같이 끝나야 하는가
- retry와 concurrency를 부모 scope budget으로 함께 조여야 하는가

둘 다 yes면 structured fan-out 후보로 보는 편이 맞다.

## 예산 모델: deadline, retry, concurrency

fan-out에서 가장 흔한 사고는 virtual thread를 병렬도 제어로 착각하는 것이다.  
실제 부하는 대개 아래 식에 더 가깝다.

`실제 원격 시도 수 ~= 동시 요청 수 x fan-out 폭 x 시도 횟수`

즉 `fan-out 8`에 `최대 2회 재시도`면, 한 요청은 최대 `24`번의 원격 시도를 만들 수 있다.  
여기서 request 수가 겹치면 upstream은 금방 saturation에 닿는다.

그래서 budget은 네 층으로 나눈다.

| budget | 어디에 둬야 하나 | 이유 |
|---|---|---|
| parent deadline | request 또는 상위 operation scope | 모든 하위 호출이 공유하는 최종 포기 시점이 필요하다 |
| per-attempt timeout | 각 `HttpRequest.timeout(...)` 또는 client timeout | interrupt/cancel만 믿지 말고 네트워크 대기를 잘라야 한다 |
| retry cap | subtask 내부에서 작은 정수로 제한 | retry storm를 막고 fan-out 폭과 곱해진 총 시도 수를 예측 가능하게 만든다 |
| remote concurrency cap | upstream별 `Semaphore`/bulkhead | virtual thread 수와 별개로 실제 upstream 동시 진입을 제한한다 |

추가 규칙도 같이 둔다.

- retry는 `429`, 일부 `5xx`, connect timeout 같이 명확히 transient인 경우에만 건다
- `POST`/side effect 호출은 idempotency key나 중복 방지 계약 없이 자동 retry하지 않는다
- backoff를 넣더라도 parent deadline을 넘기지 않게 remaining budget 안에서만 잔다
- remote concurrency cap은 전역 하나보다 upstream/route 그룹별 permit이 더 안전한 경우가 많다

핵심은 "subtask를 몇 개 fork했나"보다 "한 요청이 upstream에 몇 번, 몇 개까지 동시에 들어가나"다.

## 실패와 취소 의미 정리

structured fan-out을 쓸 때 먼저 고를 것은 task API가 아니라 실패 의미다.

### 1. 모두 필요하면 fail-fast로 간다

대시보드 조합처럼 `A`, `B`, `C`가 모두 있어야 응답이 의미 있다면,  
한 subtask 실패 시 sibling을 같이 취소하는 `ShutdownOnFailure` 감각이 맞다.

이 모델에서는 다음이 같이 움직여야 한다.

- parent deadline 도달
- child failure
- scope shutdown
- sibling interrupt/cancel

### 2. 일부만 필요하면 예외를 값으로 바꾼다

추천 영역, 부가 카드, optional widget처럼 partial success가 허용된다면  
subtask가 곧바로 예외를 던지기보다 `Success/Failure/TimedOut` 같은 결과 variant를 반환하는 편이 낫다.

이 경우에도 request lifetime은 같이 묶되, 실패를 "즉시 전체 중단"으로 해석하지 않는 것이다.

### 3. interrupt는 필요하지만 충분하지 않다

scope가 닫히면 자식 task는 보통 interrupt/cancel 신호를 받게 된다.  
하지만 네트워크 경계에서는 이것만으로 충분하다고 보면 안 된다.

- `HttpRequest.timeout(...)`으로 각 시도를 자른다
- connect timeout도 따로 둔다
- `InterruptedException`을 삼키지 않고 상위 scope로 올린다

즉 structured cancellation은 parent ownership을 만들어 주지만,  
실제 대기 시간을 줄이는 것은 timeout과 retry 상한이다.

## 실전 시나리오

### 시나리오 1: virtual thread로 바꾸자 원격 fan-out이 무제한처럼 늘어난다

요청당 6개 partner API를 병렬 호출하고, 각 호출이 `429/5xx`에서 3번 재시도하면  
한 요청이 최악 `24`개의 추가 원격 시도를 만들 수 있다.

여기서 필요한 것은 더 많은 virtual thread가 아니라:

- fan-out 폭 제한
- 재시도 횟수 축소
- upstream별 semaphore/bulkhead
- parent deadline 안쪽의 작은 per-attempt timeout

### 시나리오 2: 요청 timeout은 끝났는데 `sendAsync()` 재시도 체인이 계속 돈다

future graph가 request lifetime과 분리되어 있으면 orphan work가 생긴다.  
같은 요청 수명 안에서만 의미 있는 fan-out이라면, detached retry chain보다 structured scope 안에서 끝내는 편이 안전하다.

### 시나리오 3: DB transaction 안에서 원격 fan-out을 돌린다

virtual thread여도 transaction과 connection hold time은 그대로 남는다.  
structured fan-out의 도입 기준은 "병렬화 가능"이 아니라 "transaction 밖에서 request-scoped remote wait를 묶을 수 있는가"다.

즉 JDBC transaction 안 fan-out은 보통 피하고:

- DB read/write 구간을 짧게 자르고
- 원격 fan-out은 transaction 밖에서 수행하고
- 커밋 후 side effect는 outbox/after-commit로 분리한다

## 코드로 보기

아래 코드는 JDK preview level에 따라 정확한 type/method 이름이 조금 달라질 수 있지만,  
중요한 것은 **parent-owned scope + shared deadline + bounded retry + semaphore cap** 구조다.

```java
import java.io.IOException;
import java.net.ConnectException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.Semaphore;
import java.util.concurrent.StructuredTaskScope;

record Downstream(String name, URI uri) {}
record DownstreamResult(String name, int status, String body) {}

final class AggregatorGateway {
    private static final int MAX_ATTEMPTS = 2;
    private static final Duration CONNECT_TIMEOUT = Duration.ofMillis(200);
    private static final Duration MAX_PER_ATTEMPT = Duration.ofMillis(400);

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(CONNECT_TIMEOUT)
            .build();

    // upstream별 permit을 따로 두는 편이 더 안전할 때가 많다.
    private final Semaphore partnerBulkhead = new Semaphore(24, true);

    List<DownstreamResult> fetchAll(List<Downstream> downstreams, Instant deadline) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var subtasks = downstreams.stream()
                    .map(target -> scope.fork(() -> invokeWithinBudget(target, deadline)))
                    .toList();

            scope.joinUntil(deadline);
            scope.throwIfFailed();

            return subtasks.stream()
                    .map(StructuredTaskScope.Subtask::get)
                    .toList();
        }
    }

    private DownstreamResult invokeWithinBudget(Downstream target, Instant deadline) throws Exception {
        IOException lastRetryable = null;

        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            Duration remaining = Duration.between(Instant.now(), deadline);
            if (remaining.isZero() || remaining.isNegative()) {
                throw new HttpTimeoutException("parent deadline exceeded");
            }

            Duration attemptBudget =
                    remaining.compareTo(MAX_PER_ATTEMPT) < 0 ? remaining : MAX_PER_ATTEMPT;

            partnerBulkhead.acquire();
            try {
                HttpRequest request = HttpRequest.newBuilder(target.uri())
                        .timeout(attemptBudget)
                        .header("X-Attempt", Integer.toString(attempt))
                        .build();

                HttpResponse<String> response =
                        httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                if (isRetryableStatus(response.statusCode()) && attempt < MAX_ATTEMPTS) {
                    lastRetryable = new IOException("retryable status=" + response.statusCode());
                    continue;
                }

                return new DownstreamResult(target.name(), response.statusCode(), response.body());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw e;
            } catch (HttpTimeoutException | ConnectException e) {
                if (attempt == MAX_ATTEMPTS) {
                    throw e;
                }
                lastRetryable = new IOException("transient failure", e);
            } finally {
                partnerBulkhead.release();
            }
        }

        throw lastRetryable == null ? new IOException("remote call failed") : lastRetryable;
    }

    private boolean isRetryableStatus(int status) {
        return status == 429 || status >= 500;
    }
}
```

이 구조에서 읽어야 할 포인트는 다음이다.

- 각 child는 blocking `send()`를 쓰지만, caller가 virtual thread라면 callback graph보다 reasoning이 단순하다
- retry는 child 내부에서 작게 제한되고, parent deadline이 남아 있을 때만 계속된다
- semaphore permit은 "virtual thread 수"가 아니라 "upstream 동시 진입 수"를 제한한다
- `InterruptedException`은 복구 후 다시 던져 scope cancellation을 흐리지 않는다

partial success가 목표라면 `ShutdownOnFailure` 대신 subtask가 `DownstreamResult`와 별도의 failure variant를 반환하게 바꾸면 된다.  
중요한 것은 API 이름보다 부모가 자식 수명과 budget을 소유한다는 점이다.

## 관측 체크리스트

structured fan-out을 production에 넣었다면 최소한 아래를 같이 봐야 한다.

- 요청당 fan-out 폭과 실제 평균/최대 시도 횟수
- upstream별 `in_flight` permit 사용량과 permit 획득 대기 시간
- `429`, `5xx`, connect timeout, read timeout 비율
- request timeout 후 취소된 child 수와 늦게 끝난 child 수
- retry 이후 성공률과 retry가 만든 추가 호출 비율

이 지표가 없으면 "virtual thread가 빠르다"는 체감만 남고, 실제로는 retry storm와 upstream saturation을 놓치기 쉽다.

per-upstream permit sizing과 `acquire wait`/`attempt latency` 분리 관측은 [Remote Bulkhead Metrics Under Virtual Threads](./remote-bulkhead-metrics-under-virtual-threads.md) 쪽을 같이 보면 더 선명하다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| caller virtual thread에서 straight-line `send()` | 단순한 cancellation과 로그 흐름 | fan-out 조합은 직접 표현해야 한다 |
| structured fan-out + blocking `send()` | parent lifetime, fail-fast, retry/cancel budget을 한 scope에 묶기 쉽다 | preview API 의존성 또는 별도 abstraction이 필요할 수 있다 |
| `sendAsync()` 중심 fan-out | callback 조합과 detached pipeline에 유연하다 | request lifetime, context, orphan retry를 따로 설계해야 한다 |
| retry를 공격적으로 늘리기 | 순간 성공률을 올릴 수 있다 | fan-out 폭과 곱해져 upstream saturation을 빠르게 부른다 |
| virtual thread만 믿고 concurrency cap 생략 | 코드가 단순해 보인다 | 실제 upstream 보호 장치가 없어 장애가 전염된다 |

핵심 trade-off는 "blocking vs async"보다 "누가 자식 호출들의 lifetime과 budget을 소유하느냐"다.

## 꼬리질문

> Q: virtual thread가 있으면 `HttpClient.sendAsync()` 대신 항상 `send()`로 바꾸면 되나요?
> 핵심: 항상은 아니다. 다만 요청 수명 안에서 끝나는 fan-out이라면 blocking `send()`가 cancellation reasoning을 단순하게 만드는 경우가 많다.

> Q: `StructuredTaskScope`를 쓰면 별도 timeout이 없어도 되나요?
> 핵심: 아니다. parent deadline은 전체 포기 시점이고, 각 시도의 네트워크 대기는 `HttpRequest.timeout(...)`처럼 따로 자르는 편이 안전하다.

> Q: retry는 어디서 제한해야 하나요?
> 핵심: child task 내부에서 작은 상한으로 제한하고, parent deadline이 남아 있을 때만 허용해야 한다.

> Q: virtual thread를 쓰는데 왜 semaphore가 또 필요한가요?
> 핵심: virtual thread는 blocking 비용을 낮출 뿐 upstream의 동시 진입 한도나 rate limit을 대신 지켜주지 않는다.

## 한 줄 정리

`HttpClient` fan-out은 virtual thread만으로 안전해지지 않으므로, 같은 요청 안에서 함께 끝나야 하는 원격 호출만 `StructuredTaskScope`-style scope로 묶고 deadline, retry, cancellation, remote concurrency를 부모 budget으로 같이 제한해야 한다.
