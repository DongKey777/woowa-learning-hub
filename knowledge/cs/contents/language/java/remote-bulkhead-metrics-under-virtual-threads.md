# Remote Bulkhead Metrics Under Virtual Threads

> 한 줄 요약: virtual thread는 remote wait를 싸게 만들 뿐 upstream permit을 대신 설계해 주지 않는다. upstream별 semaphore/bulkhead는 safe in-flight share에서 역산하고, permit wait를 HTTP latency와 분리해서 찍어야 permit contention, retry storm, upstream saturation을 구분할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Structured Fan-out With `HttpClient`](./structured-fanout-httpclient.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Idempotency Keys and Safe HTTP Retries](./httpclient-idempotency-keys-safe-http-retries.md)
> - [JFR Loom Incident Signal Map](./jfr-loom-incident-signal-map.md)
> - [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
> - [Timeout, Retry, Backoff 실전](../../network/timeout-retry-backoff-practical.md)
> - [Backpressure and Load Shedding Design](../../system-design/backpressure-and-load-shedding-design.md)

> retrieval-anchor-keywords: remote bulkhead metrics under virtual threads, virtual thread remote bulkhead, per-upstream semaphore sizing, bulkhead observability, permit contention, semaphore acquire wait, remote concurrency cap telemetry, retry storm metrics, upstream saturation telemetry, 429 retry amplification, per-route bulkhead, bulkhead wait ratio, bulkhead saturation ratio, logical request vs attempt metrics, Little's law remote concurrency, thread park semaphore acquire, structured fan-out bulkhead metrics, virtual thread HTTP bulkhead

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [per-upstream bulkhead를 어떻게 나누나](#per-upstream-bulkhead를-어떻게-나누나)
- [sizing 출발점: safe share에서 역산한다](#sizing-출발점-safe-share에서-역산한다)
- [어떤 telemetry를 분리해서 찍어야 하나](#어떤-telemetry를-분리해서-찍어야-하나)
- [신호 해석: permit contention vs retry storm vs upstream saturation](#신호-해석-permit-contention-vs-retry-storm-vs-upstream-saturation)
- [코드로 보기](#코드로-보기)
- [관측 체크리스트](#관측-체크리스트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

Loom 이후 outbound HTTP에서 가장 흔한 착시는 "virtual thread가 많으니 remote 동시성도 thread 수에 맞춰 열어도 된다"는 생각이다.  
실제로 upstream을 보호하는 숫자는 여전히 permit 수, retry 수, parent deadline이다.

remote bulkhead 설계에서 먼저 고정해야 하는 사실은 세 가지다.

- virtual thread 수는 cheap wait의 상한일 뿐이고, upstream safe concurrency의 상한이 아니다
- semaphore 하나를 전체 partner 호출에 공유하면 noisy neighbor가 생기고, 어느 upstream이 permit을 잡아먹는지 보이지 않는다
- logical request 수와 실제 attempt 수를 분리해서 보지 않으면 retry storm가 permit 사용량 안에 숨어 버린다

즉 virtual thread 환경에서 remote wait가 늘어날 때 질문은 "thread가 왜 많지?"가 아니라 아래 순서가 된다.

1. 어떤 upstream/route group이 permit을 오래 잡고 있는가
2. permit을 못 얻어 기다리는가, 아니면 permit을 얻은 뒤 upstream 자체가 느린가
3. logical request는 비슷한데 retry 때문에 attempt가 폭증한 것 아닌가

## per-upstream bulkhead를 어떻게 나누나

bulkhead 단위는 host 이름보다 **같은 실패 도메인과 rate-limit 도메인을 공유하는가**로 나누는 편이 안전하다.

| 나누는 기준 | 같이 묶어도 되는 경우 | 분리하는 편이 나은 경우 |
|---|---|---|
| upstream 시스템 | 같은 partner, 같은 인증 주체, 같은 rate limit | partner는 같아도 제품군별 quota나 key가 다를 때 |
| route cost | read-only 조회 두세 개가 latency/에러 양상이 비슷할 때 | 같은 host라도 write API, search API, batch API처럼 cost가 크게 다를 때 |
| criticality | 모두 optional widget이고 fail-open 전략이 같을 때 | checkout/payment처럼 required path와 optional path가 섞일 때 |
| caller population | request path끼리만 share할 때 | request path와 backfill/batch/scheduler가 같은 permit을 먹을 때 |

보통 시작점은 이렇다.

- upstream이 다르면 semaphore도 다르게 둔다
- 같은 upstream이라도 rate limit, timeout, retry policy가 다르면 route group을 분리한다
- required path와 optional path는 같은 partner라도 reserve를 따로 주거나 bulkhead를 나눈다
- request path와 background job은 같은 partner라도 share를 분리한다

전역 semaphore 하나가 단순해 보여도 운영에서는 아래 질문에 답하기 어려워진다.

- permit을 누가 다 쓰는가
- `429`가 어느 route group에서 먼저 시작됐는가
- wait가 보호 동작인지 noisy neighbor starvation인지

## sizing 출발점: safe share에서 역산한다

permit 수는 thread 수나 CPU core 수가 아니라 **upstream이 SLA 안에서 감당하는 safe in-flight share**에서 출발해야 한다.

먼저 cluster-wide safe share를 잡는다.

```text
cluster_safe_inflight[upstream] =
  min(
    partner_documented_limit,
    observed_knee_before_p95_or_429_spike,
    internal_error_budget_cap
  )
```

그다음 reserve를 뺀 뒤 인스턴스 share로 나눈다.

```text
instance_share[upstream] =
  floor((cluster_safe_inflight - failover_reserve - other_caller_reserve) / active_instances)
```

이제 target throughput이 이 share 안에서 가능한지 역산한다.

```text
required_attempt_concurrency =
  ceil(
    target_logical_rps
    * max_parallel_attempts_per_request
    * p95_remote_attempt_seconds
    * retry_multiplier
  )

initial_permits = min(instance_share, required_attempt_concurrency)
```

여기서 중요한 해석은 다음과 같다.

- `max_parallel_attempts_per_request`는 request 하나가 같은 upstream에 동시에 거는 call 수다
- `p95_remote_attempt_seconds`는 permit을 잡은 뒤 release할 때까지의 wall-clock이다
- `retry_multiplier`는 `총 attempt 수 / logical request 수`다. `maxAttempts` 설정값보다 운영 현실을 더 잘 반영한다
- `required_attempt_concurrency > instance_share`라면 목표 throughput이 upstream 예산을 초과한 것이다. 이때 permit을 더 늘리는 것은 sizing이 아니라 overload 전파다

### 짧은 예시

가정:

- partner A의 cluster-safe in-flight는 96
- failover/batch reserve 16을 남긴다
- active instance 4개
- checkout 요청 하나가 partner A에 최대 2개 병렬 호출을 건다
- attempt wall-clock p95는 180ms
- 실제 retry multiplier는 1.15다
- 목표 logical throughput은 instance당 45 RPS다

그러면:

```text
instance_share = floor((96 - 16) / 4) = 20
required_attempt_concurrency = ceil(45 * 2 * 0.180 * 1.15) = 19
initial_permits = min(20, 19) = 19
```

이 수치는 "19면 맞다"가 아니라 "20 share 안에서 19가 현재 목표와 p95에 맞는 출발점"이라는 뜻이다.  
나중에 retry multiplier가 1.50으로 올라 required concurrency가 25가 되면, 문제는 permit이 작아서가 아니라 retry/latency/throughput 목표가 upstream share를 넘어선 것이다.

## 어떤 telemetry를 분리해서 찍어야 하나

virtual thread 환경에서는 많은 task가 `Semaphore.acquire()`에서 조용히 park될 수 있다.  
그래서 thread 수만 보면 permit contention과 upstream slowness가 섞여 보인다. 최소한 아래 계열은 분리해서 찍는 편이 낫다.

| metric family | 왜 필요한가 | 주의점 |
|---|---|---|
| `logical_requests_total{upstream,route_group}` | business demand 기준 분모다 | raw HTTP attempt 수와 섞지 않는다 |
| `remote_attempts_total{upstream,route_group,attempt_kind,outcome}` | retry amplification을 잡는다 | `attempt_kind=initial|retry`, `outcome=success|429|5xx|connect_timeout|read_timeout|cancelled` 정도로 낮은 cardinality 유지 |
| `remote_bulkhead_in_flight{upstream,route_group}` | 현재 permit 점유량을 본다 | `max_permits` gauge도 같이 찍어 saturation ratio를 계산한다 |
| `remote_bulkhead_waiters{upstream,route_group}` | 지금 permit을 기다리는 수를 본다 | `Semaphore.getQueueLength()`는 대략값이라 trace/latency와 같이 읽는다 |
| `remote_bulkhead_acquire_seconds` timer | permit contention 시간을 본다 | HTTP latency와 합치지 말고 별도 timer로 둔다 |
| `remote_bulkhead_acquire_timeout_total` 또는 reject counter | 보호 장치가 fail-fast로 바뀌는 순간을 본다 | wait 후 timeout과 즉시 reject를 구분하면 더 좋다 |
| `remote_attempt_latency_seconds{upstream,route_group}` | permit을 얻은 뒤 upstream 자체가 느린지 본다 | acquire wait를 제외한 pure attempt wall-clock으로 유지한다 |
| `http_client_errors_total{upstream,route_group,class}` | `429`, `503`, connect/read timeout, TLS error를 분리한다 | "실패" 한 버킷으로 뭉개면 saturation fingerprint가 흐려진다 |

여기서 특히 중요한 규칙은 하나다.

**permit wait와 remote attempt latency를 같은 timer에 넣지 않는다.**

둘을 합치면 이런 해석이 불가능해진다.

- upstream은 빠른데 permit이 꽉 차서 local wait만 늘어난 것인가
- permit은 바로 얻는데 upstream 자체가 느린 것인가
- retry가 추가 attempt를 만들며 둘 다 악화시키는가

### 꼭 계산해 둘 파생 지표

원시 metric 위에 아래 파생값을 같이 보면 triage 속도가 빨라진다.

```text
retry_extra_factor = remote_attempts_total / logical_requests_total
bulkhead_saturation_ratio = in_flight / max_permits
wait_ratio = waited_acquisitions / total_acquisitions
```

운영 해석에서 자주 유용한 질문은 다음과 같다.

- logical request는 그대로인데 `retry_extra_factor`만 오르는가
- `bulkhead_saturation_ratio`가 1.0 근처에 붙는데 `429`/timeout도 같이 오르는가
- `wait_ratio`는 높은데 remote attempt latency는 안정적인가

### virtual thread에서 같이 볼 보조 증거

incident 때는 metric만 보지 말고 아래도 같은 시간창에 맞춘다.

- thread dump / JFR의 `Semaphore.acquire()` 또는 `AbstractQueuedSynchronizer` park stack
- `jdk.ThreadPark`와 `jdk.SocketRead`/`jdk.SocketWrite` 조합
- request trace의 `bulkheadWaitMs`, `attemptMs`, `attemptNo`, `upstream`, `routeGroup`

virtual thread가 많이 park된다고 곧바로 Loom 문제는 아니다.  
`Semaphore.acquire()` stack에 park가 몰리고 carrier pinning이 없다면, 그것은 종종 의도된 backpressure이거나 upstream share 초과 신호다.

## 신호 해석: permit contention vs retry storm vs upstream saturation

| 신호 조합 | 더 그럴듯한 해석 | 먼저 취할 액션 |
|---|---|---|
| `bulkhead_saturation_ratio` 높음 + `wait_ratio` 높음 + remote latency 안정 + `429` 낮음 | permit contention은 있지만 현재 bulkhead가 upstream을 보호하고 있다 | 목표 throughput이 share 안인지, route group 분리가 필요한지 확인한다 |
| `retry_extra_factor` 상승 + logical request 정체/하락 + `waiters` 급증 + `429`/timeout 동반 | retry storm가 permit을 먹고 있다 | retry cap 축소, jitter/backoff 재점검, attempt마다 permit 재획득하도록 확인 |
| `in_flight ~= max_permits` + remote latency 상승 + `429`/`503`/read timeout 상승 | upstream saturation이 먼저다 | bulkhead를 키우지 말고 admission/retry/fallback을 줄인다 |
| thread dump에서 `Semaphore.acquire()` park는 많지만 `in_flight`가 낮다 | permit 누수, route skew, 잘못된 metric, 너무 긴 permit hold 구간 가능성 | release 경로, per-route grouping, hold span 계측을 점검한다 |
| `wait_ratio`는 낮은데 `429`가 높다 | local bulkhead보다 upstream의 더 작은 quota/key limit이 먼저다 | route/key별 split이 필요한지, 외부 다른 caller가 share를 쓰는지 확인한다 |

여기서 중요한 역질문도 있다.

- wait가 있다는 사실만으로 bulkhead를 키워야 하는가: 아니다. wait는 보호 장치가 실제로 작동 중이라는 뜻일 수도 있다
- `429`가 보인다는 이유만으로 permit을 줄여야 하는가: 꼭 그렇진 않다. retry가 문제인지, 다른 caller share 충돌인지, route grouping이 거칠어서 그런지 먼저 분리해야 한다

## 코드로 보기

아래 예시는 permit wait와 remote attempt latency를 분리해서 계측하는 최소 골격이다.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;

final class PartnerBulkheadClient {
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final Semaphore permits = new Semaphore(19, true);
    private final AtomicInteger inFlight = new AtomicInteger();
    private final AtomicInteger waiters = new AtomicInteger();

    HttpResponse<String> fetch(URI uri, Duration acquireTimeout) throws Exception {
        long waitStarted = System.nanoTime();
        waiters.incrementAndGet();
        boolean acquired;
        try {
            acquired = permits.tryAcquire(acquireTimeout.toNanos(), TimeUnit.NANOSECONDS);
        } finally {
            waiters.decrementAndGet();
        }

        long acquiredAt = System.nanoTime();
        recordBulkheadAcquire(acquiredAt - waitStarted);

        if (!acquired) {
            incrementAcquireTimeout();
            throw new TimeoutException("bulkhead acquire timed out");
        }

        inFlight.incrementAndGet();
        long attemptStarted = System.nanoTime();
        try {
            HttpRequest request = HttpRequest.newBuilder(uri)
                    .timeout(Duration.ofMillis(300))
                    .GET()
                    .build();
            return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (java.net.http.HttpTimeoutException e) {
            incrementAttemptOutcome("timeout");
            throw e;
        } finally {
            recordAttemptLatency(System.nanoTime() - attemptStarted);
            inFlight.decrementAndGet();
            permits.release();
        }
    }

    private void recordBulkheadAcquire(long nanos) {
        // remote_bulkhead_acquire_seconds{upstream="partner-a", route_group="search"}
    }

    private void recordAttemptLatency(long nanos) {
        // remote_attempt_latency_seconds{upstream="partner-a", route_group="search"}
    }

    private void incrementAcquireTimeout() {
        // remote_bulkhead_acquire_timeout_total{upstream="partner-a", route_group="search"}
    }

    private void incrementAttemptOutcome(String outcome) {
        // remote_attempts_total{upstream="partner-a", route_group="search", attempt_kind="initial|retry", outcome=...}
    }
}
```

이 예시에서 읽어야 할 핵심은 네 가지다.

- `waiters`와 `inFlight`는 현재 pressure를 보여 주는 gauge다
- `recordBulkheadAcquire(...)`는 remote latency와 별개로 permit contention만 측정한다
- retry를 건다면 caller 쪽에서 `attempt_kind=retry`를 올리고, retry도 다시 permit을 얻어야 한다
- permit은 network wait 동안만 쥐고, backoff sleep 동안 쥐지 않는 편이 관측과 보호 양쪽에 더 낫다

## 관측 체크리스트

- upstream/route group별로 `logical_requests`와 `attempts`를 분리해서 본다
- `bulkhead_acquire`와 `remote_attempt_latency`가 별도 타이머인지 확인한다
- `in_flight`, `waiters`, `max_permits`, `acquire_timeout`을 같이 본다
- `429`, `5xx`, connect timeout, read timeout, cancel을 다른 outcome으로 남긴다
- request trace에 `bulkheadWaitMs`, `attemptMs`, `attemptNo`, `routeGroup`를 남긴다
- incident 때 JFR/thread dump에서 `Semaphore.acquire()` park와 `SocketRead`를 같은 시간창에 맞춘다
- retry multiplier가 올라갈 때 logical request 증가 때문인지, 오류 회복 실패 때문인지 분리해서 본다

## 트레이드오프

| 선택 | 장점 | 리스크 |
|---|---|---|
| upstream 하나당 bulkhead 하나 | 운영이 단순하다 | route별 cost 차이, noisy neighbor를 숨길 수 있다 |
| route group까지 쪼갠다 | `429`/latency 편차를 더 빨리 분리한다 | permit 운영과 metric 차원이 늘어난다 |
| wait 후 acquire | burst를 흡수하고 protect-first가 가능하다 | wait budget이 request timeout을 잠식할 수 있다 |
| 즉시 reject/fail-fast | overload를 빨리 surface한다 | 순간적인 회복 여지를 덜 준다 |
| retry를 permit 안에서 다시 acquire | 실제 attempt pressure를 정직하게 반영한다 | 순간 성공률이 더 낮아 보일 수 있다 |

## 꼬리질문

> Q: virtual thread가 많으니 semaphore permit도 넉넉하게 두면 되지 않나요?
> 핵심: 아니다. permit은 thread 비용이 아니라 upstream safe concurrency를 표현하는 숫자다.

> Q: permit wait가 늘면 바로 bulkhead를 키워야 하나요?
> 핵심: 아니다. remote latency와 `429`가 안정적이면 건강한 보호 동작일 수 있고, retry storm나 route skew일 수도 있다.

> Q: 왜 logical request와 retry attempt를 따로 세야 하나요?
> 핵심: retry storm는 business demand 증가 없이도 permit 사용량을 폭증시키므로, attempt만 보면 원인을 오해하기 쉽다.

> Q: bulkhead wait를 그냥 HTTP client latency에 합치면 안 되나요?
> 핵심: 안 된다. local contention과 upstream slowness를 분리하지 못하면 sizing과 incident 대응이 둘 다 틀어지기 쉽다.

## 한 줄 정리

virtual thread 이후 remote bulkhead의 핵심은 "몇 개의 thread가 기다리나"가 아니라 `safe in-flight share -> per-instance permit -> permit wait / retry / upstream latency`를 한 세트로 관측해 permit contention, retry storm, upstream saturation을 서로 다른 신호로 읽는 것이다.
