# Idempotency Keys and Safe HTTP Retries

> 한 줄 요약: Java `HttpClient`에서 `POST`/side effect 호출 재시도는 "실패했으니 한 번 더"가 아니라, body replay 가능성, redirect/transport 재전송 경계, `Idempotency-Key` + dedup 계약을 같이 고정했을 때만 안전하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Structured Fan-out With `HttpClient`](./structured-fanout-httpclient.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
> - [HTTP 메서드, REST, 멱등성](../../network/http-methods-rest-idempotency.md)
> - [Timeout, Retry, Backoff 실전](../../network/timeout-retry-backoff-practical.md)
> - [멱등성 키와 중복 방지](../../database/idempotency-key-and-deduplication.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [Spring Delivery Reliability: `@Retryable`, Resilience4j, and Outbox Relay Worker Design](../../spring/spring-delivery-reliability-retryable-resilience4j-outbox-relay.md)

> retrieval-anchor-keywords: java HttpClient POST retry, HttpClient safe retry, Idempotency-Key, idempotency key, duplicate suppression, dedup contract, dedup window, request fingerprint, response replay cache, body publisher replay, repeatable request body, jdk.httpclient.enableAllMethodRetry, jdk.httpclient.disableRetryConnect, jdk.httpclient.redirects.retrylimit, expectContinue, 100-continue, 307 redirect POST replay, 308 redirect POST replay, REFUSED_STREAM, replay-safe retry, side-effecting POST

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [언제 POST 재시도가 안전한가](#언제-post-재시도가-안전한가)
- [JDK `HttpClient`가 자동으로 다시 보내는 경계](#jdk-httpclient가-자동으로-다시-보내는-경계)
- [Body Replayability와 요청 구성](#body-replayability와-요청-구성)
- [Idempotency Key와 Dedup 계약](#idempotency-key와-dedup-계약)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [관측 체크리스트](#관측-체크리스트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`POST`가 자동으로 unsafe인 것도 아니고, retry library를 붙였다고 자동으로 safe해지는 것도 아니다.  
안전성은 보통 아래 세 질문을 동시에 통과해야 나온다.

- 이전 시도가 **정말 처리되지 않았다고** 클라이언트가 알 수 있는가
- 같은 logical operation을 다시 보내도 **같은 효과로 수렴**하는가
- retry/redirect 시 request body가 **같은 의미로 재생산**되는가

하나라도 no면 "`POST` 재시도"가 아니라 "`중복 side effect`를 만들 가능성이 있는 재전송"이 된다.

특히 Java `HttpClient`에선 이 문제가 더 구체적이다.

- redirect가 method/body를 다시 보낼 수 있다
- transport 계층이 "peer가 처리하지 않았다"는 신호를 주면 내부 재전송이 일어날 수 있다
- custom retry loop가 `BodyPublisher`를 다시 소비하면서 다른 payload를 만들 수 있다

그래서 safe retry는 "`POST`를 몇 번까지 retry하나"보다 **누가 duplicate를 흡수하고, 무엇을 같은 요청으로 판단하나**를 먼저 정해야 한다.

## 언제 POST 재시도가 안전한가

| 상황 | 판단 | 이유 |
|---|---|---|
| 같은 `Idempotency-Key` + 같은 fingerprint면 서버가 원래 결과를 replay한다 | 안전 | duplicate가 새 side effect가 아니라 기존 operation의 재조회로 흡수된다 |
| `expectContinue(true)`로 body 전송 전 거절되었거나, transport가 "peer unprocessed"를 증명한다 | 대체로 안전 | 서버가 실제 side effect를 시작하지 않았다고 볼 근거가 있다 |
| `POST`지만 실제로는 side effect 없는 search/report 생성 요청이다 | 문서화돼 있으면 안전 | method가 아니라 domain semantics가 조회 성격이기 때문이다 |
| 결제 승인, 주문 생성, 이메일 발송처럼 side effect가 있고 dedup 저장소가 없다 | 위험 | timeout 뒤 성공/실패가 애매한 순간 blind retry가 중복 실행이 된다 |
| 같은 key를 재사용하지만 payload가 달라진다 | 위험 | duplicate가 아니라 잘못된 key 재사용이므로 conflict로 막아야 한다 |
| retry 때 body bytes가 달라지거나 한 번만 읽을 수 있는 stream을 다시 쓴다 | 위험 | 같은 logical operation조차 재현되지 않는다 |

핵심은 "`POST`도 safe해질 수 있다"가 아니라,  
**client retry policy와 server dedup contract가 같은 logical operation boundary를 공유해야 한다**는 점이다.

## JDK `HttpClient`가 자동으로 다시 보내는 경계

`HttpClient`는 Resilience4j 같은 정책 엔진은 아니지만,  
redirect와 일부 connection/transport failure에 대해 내부적으로 request를 다시 보낼 수 있다.

현재 OpenJDK 구현을 읽을 때 먼저 눈에 들어오는 경계는 이 셋이다.

- `jdk.httpclient.disableRetryConnect=false`
  - connect failure 자동 retry가 기본적으로 열려 있다
- `jdk.httpclient.enableAllMethodRetry=false`
  - non-idempotent method 자동 retry는 기본적으로 허용되지 않는다
- `jdk.httpclient.redirects.retrylimit=5`
  - redirect나 특정 failure를 거치며 request를 다시 보내는 총 시도 수 상한이다

여기서 중요한 nuance가 하나 더 있다.  
현재 OpenJDK의 기본 automatic retry gate는 `GET`, `HEAD`만 auto-retryable method로 본다.

- HTTP spec 차원의 generic idempotency와
- JDK implementation이 "자동 재전송해도 되겠다"고 보는 기본 판단

은 완전히 같은 개념이 아니다.

즉 `PUT`, `DELETE`, business-idempotent `POST`라도  
"서버 semantics상 괜찮다"는 이유만으로 JDK가 알아서 안전하게 retry해 주리라 기대하면 안 된다.

redirect도 별도 경계다.

- `307`, `308`
  - method와 body를 유지한 채 다시 보낼 수 있다
- `301`, `302`
  - `POST`가 `GET`으로 바뀔 수 있다
- `303`
  - `GET`으로 바뀐다

그래서 side-effecting `POST`에서 `followRedirects(...)`를 켜면,  
**retry 코드를 안 썼어도 body replay 경계가 생긴다**고 보는 편이 안전하다.

transport가 "peer가 이 request를 처리하지 않았다"는 신호를 줄 때도 있다.  
예를 들어 HTTP/2 `REFUSED_STREAM` 같은 경우는 "request not processed by peer" 취급으로 새 connection에서 재시도가 가능하다.

이건 blind retry보다 훨씬 좁고 안전한 경우지만,  
여전히 **business dedup을 대체하는 근거는 아니다**.  
애플리케이션은 "timeout 났으니 아마 안 됐겠지"와 "peer가 분명 처리 안 했다"를 구분해야 한다.

마지막으로 `expectContinue(true)`는 Java 쪽에서 `100-continue`를 쓰는 정식 방법이다.

- 큰 body를 보내기 전 인증/조건 실패를 빨리 보고 싶을 때 유용하다
- body가 아직 안 나갔다면 불필요한 재전송 위험을 줄일 수 있다
- 하지만 body가 이미 나간 뒤의 timeout/disconnect ambiguity를 해결해 주진 않는다

즉 `expectContinue(true)`는 **body 전송 전 경계 최적화**이지,  
idempotency key를 지우는 마법이 아니다.

## Body Replayability와 요청 구성

`HttpRequest`를 retry/redirect로 다시 보내려면 body가 다시 만들어져야 한다.  
이때 가장 흔한 함정은 "request object는 immutable인데 body source는 one-shot"인 경우다.

retry-safe한 기본 선택은 대체로 이쪽이다.

- `BodyPublishers.ofString(...)`
- `BodyPublishers.ofByteArray(...)`
- `BodyPublishers.ofFile(...)`
- `BodyPublishers.ofInputStream(() -> freshStream)`

주의가 필요한 패턴은 이쪽이다.

- 이미 읽기 시작한 `InputStream`을 감싼 custom `BodyPublisher`
- subscribe 시점마다 boundary, nonce, timestamp를 다시 뽑는 multipart builder
- attempt마다 JSON field order나 canonicalization이 바뀌는 serializer
- retry 때마다 서명 헤더는 바뀌는데 서버 fingerprint가 그 값을 포함하는 경우

정리하면 request 구성 요소는 역할을 분리해서 보는 편이 좋다.

| 구성 요소 | retry-safe 기본값 | 주의점 |
|---|---|---|
| body bytes | 미리 canonicalize한 `byte[]`/file | attempt마다 payload가 달라지면 같은 key라도 conflict 난다 |
| `Idempotency-Key` | logical operation당 1개 | retry마다 새로 만들면 dedup이 무너진다 |
| fingerprint | method/path/body의 canonical hash | `Date`, attempt 수, trace header 같은 휘발성 값은 보통 빼는 편이 낫다 |
| attempt metadata | `X-Attempt`처럼 가변 header 허용 | dedup 판단에 쓰면 안 된다 |

즉 retry-safe body는 "다시 읽을 수 있다"에서 끝나지 않는다.  
**같은 key로 다시 보냈을 때 서버가 같은 의미로 해석할 수 있어야 한다**.

## Idempotency Key와 Dedup 계약

safe retry는 결국 서버가 duplicate를 어떻게 흡수하느냐의 문제다.  
최소 계약은 보통 아래 네 축으로 잡는다.

| 축 | 최소 계약 | 빠지면 생기는 문제 |
|---|---|---|
| scope | `tenant + operation + idempotency key` | 다른 API나 다른 caller가 같은 key space를 공유해 충돌한다 |
| fingerprint | canonical method/path/body hash | 같은 key에 다른 payload가 섞여 잘못된 replay가 생긴다 |
| state | `PROCESSING`, `COMPLETED`, `UNKNOWN`, `EXPIRED` 정도의 상태 모델 | timeout 뒤 애매한 요청을 blind retry하게 된다 |
| replay | 같은 key + 같은 fingerprint면 이전 결과나 pending 상태를 재현 | 성공했는데 응답만 유실된 경우 duplicate side effect가 생긴다 |

여기서 특히 중요한 규칙은 둘이다.

### 1. 같은 key + 다른 payload는 retry가 아니라 conflict다

이 경우는 보통 `409 Conflict`나 명시적 domain error로 막아야 한다.  
"기존 key가 있으니 그냥 예전 응답을 돌려주자"는 더 위험하다.

### 2. dedup window는 retry horizon보다 길어야 한다

클라이언트 retry만 보는 게 아니라 아래를 같이 합산해야 한다.

- mobile/web client 재시도
- gateway/proxy retry
- background repair/replay
- 운영자 수동 재실행

window가 이보다 짧으면 "늦게 온 duplicate"가 신규 요청으로 통과할 수 있다.

애매한 failure도 구분해야 한다.

- provider timeout 이후 실제 side effect가 반영됐는지 모를 때
- 내부 commit과 외부 호출 사이에서 상태가 흔들릴 때

이때는 재실행보다 **recover-first**가 우선이다.

- provider reference 조회
- status poll
- reconciliation/outbox 확인
- 기존 idempotency record replay

즉 idempotency key store는 단순 캐시가 아니라  
**애매한 실패를 중복 실행보다 복구 중심으로 몰아주는 제어 계층**이다.

## 실전 시나리오

### 시나리오 1: 결제 승인 `POST`가 timeout으로 끝난다

가장 위험한 케이스다.  
클라이언트는 실패처럼 봤지만 provider는 이미 charge를 끝냈을 수 있다.

이때 안전한 흐름은:

- 같은 `Idempotency-Key`를 유지한다
- 서버는 기존 processing/completed record를 먼저 본다
- 애매하면 provider charge id나 reconciliation key로 recover-first를 한다
- 결과가 확인되면 기존 응답을 replay한다

"한 번 더 승인 요청"은 마지막 수단이어야 한다.

### 시나리오 2: `307` redirect가 걸린 upload `POST`

`followRedirects(...)`가 켜져 있고 body publisher가 repeatable이면  
JDK는 method/body를 유지한 채 다른 URI로 request를 다시 보낼 수 있다.

이때 필요한 것은:

- redirect 대상이 같은 logical endpoint인지
- auth/signature가 redirect 후에도 유효한지
- upload registration이 idempotent한지

즉 redirect도 retry처럼 읽어야 한다.

### 시나리오 3: 플랫폼 전체에 `-Djdk.httpclient.enableAllMethodRetry=true`를 건다

겉보기엔 transient failure 흡수가 좋아지지만,  
실제로는 webhook 등록, 메일 발송, 주문 생성 같은 non-idempotent `POST`도 automatic resend 후보가 된다.

이 옵션은 "모든 non-GET method가 safe해진다"는 뜻이 아니다.  
**감사된 endpoint 집합 + repeatable body + dedup contract**가 이미 있을 때만 검토할 수 있다.

### 시나리오 4: retry loop는 맞는데 body source가 한 번만 읽힌다

첫 시도는 정상인데 두 번째 시도는 empty body거나 partial body가 된다.  
서버는 같은 key에 다른 fingerprint가 왔다고 보고 conflict를 낼 수 있다.

이 문제는 retry policy보다 body construction bug에 가깝다.  
logical operation을 한 번 정했으면 body bytes도 그 시점에 같이 고정하는 편이 안전하다.

## 코드로 보기

아래 예시는 "같은 logical operation이면 같은 key와 같은 body를 유지한다"는 점만 보여 주기 위한 최소 예시다.

```java
import java.io.IOException;
import java.net.ConnectException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.HexFormat;
import java.util.UUID;

record ChargeResponse(int statusCode, String body) {}

final class IdempotentChargeClient {
    private static final int MAX_ATTEMPTS = 3;
    private static final Duration CONNECT_TIMEOUT = Duration.ofMillis(300);
    private static final Duration MAX_PER_ATTEMPT = Duration.ofMillis(800);

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(CONNECT_TIMEOUT)
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();

    ChargeResponse charge(URI uri, byte[] canonicalJson, UUID idempotencyKey, Instant deadline)
            throws IOException, InterruptedException {
        String fingerprint = sha256Hex(canonicalJson);
        IOException lastRetryable = null;

        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            Duration remaining = Duration.between(Instant.now(), deadline);
            if (remaining.isZero() || remaining.isNegative()) {
                throw new HttpTimeoutException("deadline exceeded");
            }

            Duration attemptTimeout =
                    remaining.compareTo(MAX_PER_ATTEMPT) < 0 ? remaining : MAX_PER_ATTEMPT;

            HttpRequest request = HttpRequest.newBuilder(uri)
                    .timeout(attemptTimeout)
                    .expectContinue(true)
                    .header("Content-Type", "application/json")
                    .header("Idempotency-Key", idempotencyKey.toString())
                    .header("X-Request-Fingerprint", fingerprint)
                    .header("X-Attempt", Integer.toString(attempt))
                    .POST(HttpRequest.BodyPublishers.ofByteArray(canonicalJson))
                    .build();

            try {
                HttpResponse<String> response =
                        httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

                if (response.statusCode() == 409) {
                    throw new IOException("idempotency conflict: same key, different fingerprint");
                }
                if (isRetryableStatus(response.statusCode()) && attempt < MAX_ATTEMPTS) {
                    backoff(attempt, deadline);
                    continue;
                }

                return new ChargeResponse(response.statusCode(), response.body());
            } catch (ConnectException | HttpTimeoutException e) {
                lastRetryable = e;
                if (attempt == MAX_ATTEMPTS) {
                    throw e;
                }
                backoff(attempt, deadline);
            }
        }

        throw lastRetryable == null ? new IOException("retry exhausted") : lastRetryable;
    }

    private static boolean isRetryableStatus(int statusCode) {
        return statusCode == 429 || statusCode == 502 || statusCode == 503 || statusCode == 504;
    }

    private static void backoff(int attempt, Instant deadline) throws InterruptedException {
        long sleepMillis = Math.min(200L * attempt, 600L);
        long remainingMillis = Duration.between(Instant.now(), deadline).toMillis();
        if (remainingMillis > sleepMillis) {
            Thread.sleep(sleepMillis);
        }
    }

    private static String sha256Hex(byte[] body) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(body));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
```

이 예시에서 중요한 부분은 다음 넷이다.

- retry마다 `Idempotency-Key`를 새로 만들지 않는다
- payload를 `byte[]`로 미리 고정해 body replayability를 확보한다
- `followRedirects(HttpClient.Redirect.NEVER)`를 기본값으로 둬 side-effecting `POST`의 암묵적 재전송을 줄인다
- `409` 같은 key misuse signal은 retry가 아니라 stop signal로 취급한다

실전에서는 여기에 server-side record replay나 `202 PROCESSING` 합류 계약이 더 붙는 경우가 많다.

## 관측 체크리스트

- logical operation id와 attempt id를 분리해서 로그/trace에 남기는가
- `Idempotency-Key` replay hit/miss/conflict 비율을 본 적이 있는가
- `same key + different fingerprint` 충돌 건수를 따로 집계하는가
- transport retry, redirect, `REFUSED_STREAM`, connect retry를 같은 retry 지표로 뭉개지 않는가
- ambiguous timeout 뒤 recover-first lookup 비율을 본 적이 있는가
- dedup window 만료 후 들어온 late duplicate를 따로 관측하는가

이 지표가 없으면 "재시도 성공률"만 좋아 보여도, 실제론 duplicate suppression 비용과 late duplicate를 놓치기 쉽다.

## 트레이드오프

| 패턴 | 장점 | 한계 |
|---|---|---|
| blind `POST` retry | 구현이 가장 단순하다 | 성공-응답 유실 구간에서 duplicate side effect를 막지 못한다 |
| `Idempotency-Key` + fingerprint + response replay | sync create/charge API를 가장 현실적으로 안정화한다 | 저장소, canonicalization, TTL, conflict 처리 비용이 든다 |
| `expectContinue(true)` | body 전송 전 거절을 빨리 감지한다 | body 전송 후 ambiguity나 business duplicate는 해결하지 못한다 |
| outbox / async relay로 side effect 분리 | commit 이후 전달 신뢰성을 운영적으로 다루기 쉽다 | 동기 응답을 즉시 확정하기 어렵고 async 복구 루프가 필요하다 |

## 꼬리질문

> Q: `-Djdk.httpclient.enableAllMethodRetry=true`를 켜면 `POST`도 안전해지나요?

아니다. 그 옵션은 non-idempotent method의 automatic resend를 **허용**할 뿐,  
server-side dedup contract와 body replayability를 대신 보장하지 않는다.

> Q: `expectContinue(true)`를 쓰면 idempotency key 없이도 되나요?

아니다. `100 Continue`는 body를 아직 안 보냈을 때만 유리하다.  
body가 나간 뒤의 timeout, partial success, 응답 유실은 여전히 dedup 계약이 필요하다.

> Q: HTTP에선 `PUT`, `DELETE`도 idempotent라는데 JDK가 자동 retry해 주지 않나요?

generic HTTP semantics와 현재 OpenJDK implementation의 automatic retry gate는 같은 층이 아니다.  
기본 구현은 더 보수적으로 보는 편이므로, vendor/version별 동작을 확인하고 application-level policy를 별도로 두는 편이 안전하다.

## 한 줄 정리

Java `HttpClient`에서 side-effecting `POST` 재시도 안전성은 method 이름이 아니라 **repeatable body + stable `Idempotency-Key` + same fingerprint => same result** 계약으로 확보해야 하며, `enableAllMethodRetry`나 `expectContinue(true)`는 그 계약을 대체하지 못한다.
