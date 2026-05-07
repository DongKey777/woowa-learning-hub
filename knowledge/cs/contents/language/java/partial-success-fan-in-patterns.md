---
schema_version: 3
title: Partial Success Fan In Patterns
concept_id: language/partial-success-fan-in-patterns
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/payment
- missions/spring-roomescape
review_feedback_tags:
- structured-concurrency
- fanout
- degradation
aliases:
- Partial Success Fan-in Patterns
- structured concurrency partial success
- request scoped fan-out fan-in
- degradation tier aggregate error report
- required optional fallbackable downstream slot
- partial success degraded response
symptoms:
- 여러 downstream 병렬 호출 중 일부 실패를 null이나 빈 리스트로 숨겨 원래 데이터 없음과 장애로 인한 omission을 구분하지 못해
- required, optional, fallbackable slot policy를 정하지 않고 fan-in DTO shape부터 만들어 degraded response 의미가 흐려져
- request scope가 끝난 뒤에도 child task retry나 background work가 살아 있는 orphan work를 structured fan-out 내부에 섞어
intents:
- design
- troubleshooting
- deep_dive
prerequisites:
- language/structured-fanout-httpclient
- language/structured-concurrency-scopedvalue
- language/thread-interruption-cooperative-cancellation-playbook
next_docs:
- language/completablefuture-allof-join-timeout-exception-handling-hazards
- language/completablefuture-cancellation-semantics
- language/connection-budget-alignment-after-loom
linked_paths:
- contents/language/java/structured-fanout-httpclient.md
- contents/language/java/structured-concurrency-scopedvalue.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/completablefuture-allof-join-timeout-exception-handling-hazards.md
- contents/language/java/completablefuture-cancellation-semantics.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/connection-budget-alignment-after-loom.md
- contents/language/java/empty-string-blank-null-missing-payload-semantics.md
confusable_with:
- language/structured-fanout-httpclient
- language/completablefuture-allof-join-timeout-exception-handling-hazards
- language/connection-budget-alignment-after-loom
forbidden_neighbors: []
expected_queries:
- partial success fan-in에서 required optional fallbackable downstream slot을 어떻게 모델링해야 해?
- fan-out 일부 실패를 null이나 빈 리스트로 숨기면 degraded response 의미가 왜 사라져?
- structured concurrency request scope 안에서 partial success와 aggregate error report를 어떻게 설계해?
- fallback cache stale payload를 정상 성공처럼 숨기지 않고 degradation tier로 표현하는 방법을 알려줘
- request 종료 뒤에도 살아야 하는 재시도 작업은 fan-in이 아니라 queue outbox로 분리해야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 structured fan-out 결과를 required, optional, fallbackable slot outcome으로 fan-in하여 partial success와 degraded response를 설명 가능하게 만드는 advanced playbook이다.
  partial success, fan-in, structured concurrency, degradation tier, aggregate error report 질문이 본 문서에 매핑된다.
---
# Partial Success Fan-in Patterns

> 한 줄 요약: partial success fan-in은 structured fan-out을 request scope에 묶은 채, 각 downstream slot을 required/optional/fallbackable 계약으로 모델링하고, degradation tier와 aggregate error report를 분리해 설명 가능한 degraded response를 만드는 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Structured Fan-out With `HttpClient`](./structured-fanout-httpclient.md)
> - [Structured Concurrency and `ScopedValue`](./structured-concurrency-scopedvalue.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [`CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards](./completablefuture-allof-join-timeout-exception-handling-hazards.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [Connection Budget Alignment After Loom](./connection-budget-alignment-after-loom.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)

> retrieval-anchor-keywords: partial success fan-in, structured concurrency partial success, HttpClient partial success, request scoped fan-out, request scoped fan-in, optional downstream result, degradation tier, degraded response contract, aggregate error report, downstream issue summary, StructuredTaskScope aggregation, virtual thread aggregator, ScopedValue request budget, required vs optional downstream, fallbackable slot, stale fallback payload, request-scoped retry budget, fail-open optional widget, fail-closed required dependency

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [언제 이 패턴이 필요한가](#언제-이-패턴이-필요한가)
- [설계 축](#설계-축)
- [응답 계약 모델](#응답-계약-모델)
- [코드로 보기](#코드로-보기)
- [실전 시나리오](#실전-시나리오)
- [관측 포인트](#관측-포인트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

partial success fan-in의 핵심은 "일부 downstream 실패를 허용한다"가 아니다.  
핵심은 **부모 요청이 자식 호출 수명을 끝까지 소유하면서도, 결과 의미를 success/fallback/omission/failure로 분리해 설명 가능하게 만드는 것**이다.

이 패턴이 필요한 순간은 보통 이렇다.

- 같은 요청 안에서 여러 downstream을 병렬 호출하지만, 모두가 필수는 아니다
- 일부 widget/card/보조 데이터는 빠져도 응답을 반환할 수 있다
- fallback cache/stale snapshot/default payload를 쓸 수 있지만, 그것을 "정상 성공"으로 숨기고 싶지는 않다
- 운영상 어떤 slot이 왜 degraded 되었는지 aggregate report로 남겨야 한다

즉 fan-out과 fan-in을 함께 설계할 때는 세 질문을 동시에 고른다.

- 어느 downstream이 `required`이고 어느 downstream이 `optional`인가
- optional 실패를 `omit`할지 `fallback`으로 대체할지 `전체 실패`로 올릴지
- 최종 응답이 degraded일 때 이를 payload, metric, log, trace 어디에 어떻게 노출할지

## 언제 이 패턴이 필요한가

| 상황 | 권장 패턴 | 이유 |
|---|---|---|
| 모든 downstream이 반드시 성공해야 한다 | `ShutdownOnFailure` 감각의 fail-fast fan-out | 한 곳 실패가 곧 전체 실패이므로 partial tier가 불필요하다 |
| 일부 결과가 없어도 응답이 가능하다 | request-scoped structured fan-out + typed slot result | 요청 수명은 묶되 개별 slot 의미를 구분할 수 있다 |
| fallback 값이 stale/cache/default인지 구분해야 한다 | slot별 degradation tier + aggregate issue list | 사용자 응답과 운영 관측을 동시에 설명할 수 있다 |
| 요청 종료 후에도 재시도/보상이 계속 살아야 한다 | queue/outbox/background workflow로 분리 | request-scoped fan-in에 넣으면 orphan work가 된다 |
| `null`이나 빈 컬렉션으로 그냥 숨겨도 된다고 생각한다 | payload contract 재설계 | "값이 원래 없음"과 "downstream 실패"를 구분해야 한다 |

판단 기준은 "병렬화할 수 있나"보다 다음에 가깝다.

- 이 fan-out은 parent request가 끝나면 반드시 같이 끝나야 하는가
- degraded response를 내더라도 어떤 slot이 왜 degraded 되었는지 설명해야 하는가

둘 다 yes면 partial success fan-in 패턴이 맞다.

## 설계 축

### 1. slot policy를 값 타입보다 먼저 고른다

fan-in에서 먼저 정해야 하는 것은 DTO shape가 아니라 slot policy다.

| slot policy | 의미 | 실패 시 기본 동작 |
|---|---|---|
| `REQUIRED` | 없으면 응답 의미가 무너진다 | 전체 실패로 승격 |
| `OPTIONAL` | 없어도 응답은 유효하다 | omit + issue 기록 |
| `FALLBACKABLE` | 대체 값이 있으면 degraded 응답이 가능하다 | fallback payload + issue 기록 |

이 분류가 없으면 실무에서는 금방 `null`, 빈 리스트, 기본값이 뒤섞인다.  
그 순간 "원래 데이터가 없음"과 "downstream 장애를 숨긴 것"을 구분할 수 없어진다.

### 2. `Optional`은 최종 projection이고, 내부 모델은 slot outcome이어야 한다

내부 fan-in 단계에서 `Optional<T>`만 쓰면 정보가 너무 빨리 사라진다.

- `Optional.empty()`가 genuinely absent인지
- timeout으로 빠진 것인지
- fallback cache를 쓴 것인지
- retryable 503인지

fan-in 내부에서는 `Success`, `Degraded`, `Unavailable` 같은 typed outcome을 유지하고,  
최종 API projection 단계에서만 `Optional<T>`나 omitted field로 바꾸는 편이 안전하다.

### 3. degradation tier를 "문구"가 아니라 계약으로 둔다

degradation은 자유 텍스트가 아니라 응답 계약이어야 한다.

| tier | 의미 | 흔한 응답 형태 |
|---|---|---|
| `FULL` | 모든 required/optional slot이 정상 성공 | `200 OK`, issue 없음 |
| `OPTIONAL_OMITTED` | required는 성공, 일부 optional slot이 빠짐 | `200 OK`, omitted slot 목록 + issue |
| `FALLBACK_USED` | required는 성공, 일부 slot은 stale/default/cache fallback 사용 | `200 OK`, tier 명시 + fallback source 노출 |
| `FAILED_REQUIRED` | required slot이 비거나 parent deadline이 끝남 | `502/504` 계열 + aggregate error report |

이 tier가 있어야:

- product/UX가 degraded banner를 조건부 노출할 수 있고
- observability에서 full success와 degraded success를 분리할 수 있고
- 같은 `200 OK`라도 "완전 성공"과 "제한적 성공"을 구분할 수 있다

### 4. aggregate error report는 payload와 분리한다

degraded response라고 해서 raw stack trace를 사용자 payload에 넣을 필요는 없다.  
대신 slot 단위 요약을 별도 구조로 둔다.

| 필드 | 왜 필요한가 |
|---|---|
| `slot` | 어느 downstream이 문제였는지 |
| `policy` | required/optional/fallbackable 중 무엇인지 |
| `reason_code` | timeout, 429, 503, decode_error 같은 운영 분류 |
| `retryable` | transient로 봐야 하는지 |
| `fallback_used` | 대체 값 사용 여부 |
| `upstream_status` | HTTP status나 내부 에러 코드 |

핵심은 "응답 payload"와 "운영 설명 자료"를 분리하는 것이다.

- payload는 사용자 계약을 지킨다
- aggregate issue list는 왜 degraded 되었는지 요약한다
- 상세 stack trace와 retry context는 log/trace span에 남긴다

### 5. request scope 밖으로 빠지는 fallback은 fan-in이 아니다

partial success를 핑계로 요청 종료 뒤에도 retry chain이나 cache warm-up이 계속 돌면,  
그건 request-scoped fan-in이 아니라 detached background work다.

이 경계를 넘는 순간:

- request deadline과 child lifetime이 분리되고
- 취소 ownership이 흐려지고
- 응답은 이미 나갔는데 upstream 부하는 계속 남는다

즉 "응답을 degraded로 내고, 나머지는 나중에 채우자"가 필요하면 queue/outbox/workflow로 승격해야 한다.  
fan-in scope 안에서는 **현재 요청에서 설명 가능한 결과만** 반환하는 편이 맞다.

## 응답 계약 모델

아래 형태가 partial success fan-in에서 자주 안정적이다.

```java
enum SlotPolicy { REQUIRED, OPTIONAL, FALLBACKABLE }

enum DegradationTier {
    FULL,
    OPTIONAL_OMITTED,
    FALLBACK_USED,
    FAILED_REQUIRED
}

record AggregateIssue(
        String slot,
        SlotPolicy policy,
        String reasonCode,
        boolean retryable,
        boolean fallbackUsed,
        Integer upstreamStatus) {}

sealed interface SlotResult<T> permits SlotSuccess, SlotDegraded, SlotUnavailable {
    String slot();
    SlotPolicy policy();
}

record SlotSuccess<T>(String slot, SlotPolicy policy, T value) implements SlotResult<T> {}

record SlotDegraded<T>(
        String slot,
        SlotPolicy policy,
        T fallbackValue,
        AggregateIssue issue) implements SlotResult<T> {}

record SlotUnavailable<T>(
        String slot,
        SlotPolicy policy,
        AggregateIssue issue) implements SlotResult<T> {}
```

이 모델의 의도는 단순하다.

- `SlotSuccess`는 정상 payload를 가진다
- `SlotDegraded`는 fallback payload와 issue를 함께 가진다
- `SlotUnavailable`은 값을 만들지 못했지만 slot 단위 설명은 남긴다

즉 "값"과 "장애 설명"을 동시에 운반한다.

## 코드로 보기

아래 코드는 JDK preview level에 따라 세부 API 이름이 조금 다를 수 있지만,  
중요한 것은 **request-scoped `StructuredTaskScope` + slot별 typed result + aggregate tier derivation** 구조다.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.StructuredTaskScope;

record RequestBudget(Instant deadline, String traceId) {}
record Profile(String id, String name) {}
record Recommendations(List<String> items) {}
record PromoBanner(String message) {}

record DashboardResponse(
        Profile profile,
        Optional<Recommendations> recommendations,
        PromoBanner banner,
        DegradationTier tier,
        List<AggregateIssue> issues) {}

final class DashboardAggregator {
    private static final ScopedValue<RequestBudget> REQUEST_BUDGET = ScopedValue.newInstance();
    private static final Duration MAX_PER_ATTEMPT = Duration.ofMillis(250);

    private final HttpClient httpClient = HttpClient.newHttpClient();

    DashboardResponse load(RequestBudget budget) throws Exception {
        return ScopedValue.where(REQUEST_BUDGET, budget).call(this::loadWithinScope);
    }

    private DashboardResponse loadWithinScope() throws Exception {
        RequestBudget budget = REQUEST_BUDGET.get();

        try (var scope = new StructuredTaskScope<SlotResult<?>>()) {
            var profileTask = scope.fork(this::fetchProfileRequired);
            var recommendationTask = scope.fork(this::fetchRecommendationsOptional);
            var bannerTask = scope.fork(this::fetchPromoBannerFallbackable);

            scope.joinUntil(budget.deadline());

            @SuppressWarnings("unchecked")
            SlotResult<Profile> profileResult = (SlotResult<Profile>) profileTask.get();
            @SuppressWarnings("unchecked")
            SlotResult<Recommendations> recommendationResult =
                    (SlotResult<Recommendations>) recommendationTask.get();
            @SuppressWarnings("unchecked")
            SlotResult<PromoBanner> bannerResult = (SlotResult<PromoBanner>) bannerTask.get();

            List<AggregateIssue> issues = collectIssues(
                    List.of(profileResult, recommendationResult, bannerResult));

            if (profileResult instanceof SlotUnavailable<Profile> unavailable) {
                throw new UpstreamAggregationException(502, DegradationTier.FAILED_REQUIRED, issues, unavailable.issue());
            }

            if (bannerResult instanceof SlotUnavailable<PromoBanner> unavailable) {
                throw new UpstreamAggregationException(502, DegradationTier.FAILED_REQUIRED, issues, unavailable.issue());
            }

            Profile profile = ((SlotSuccess<Profile>) profileResult).value();
            Optional<Recommendations> recommendations = switch (recommendationResult) {
                case SlotSuccess<Recommendations> success -> Optional.of(success.value());
                case SlotDegraded<Recommendations> degraded -> Optional.of(degraded.fallbackValue());
                case SlotUnavailable<Recommendations> ignored -> Optional.empty();
            };
            PromoBanner banner = switch (bannerResult) {
                case SlotSuccess<PromoBanner> success -> success.value();
                case SlotDegraded<PromoBanner> degraded -> degraded.fallbackValue();
                case SlotUnavailable<PromoBanner> ignored -> throw new IllegalStateException("required-by-policy");
            };

            return new DashboardResponse(
                    profile,
                    recommendations,
                    banner,
                    deriveTier(List.of(profileResult, recommendationResult, bannerResult)),
                    issues
            );
        }
    }

    private SlotResult<Profile> fetchProfileRequired() throws Exception {
        try {
            HttpResponse<String> response = sendWithinBudget(URI.create("https://partner/profile"));
            return new SlotSuccess<>("profile", SlotPolicy.REQUIRED, decodeProfile(response.body()));
        } catch (HttpTimeoutException e) {
            return new SlotUnavailable<>("profile", SlotPolicy.REQUIRED,
                    new AggregateIssue("profile", SlotPolicy.REQUIRED, "timeout", true, false, null));
        }
    }

    private SlotResult<Recommendations> fetchRecommendationsOptional() throws Exception {
        try {
            HttpResponse<String> response =
                    sendWithinBudget(URI.create("https://partner/recommendations"));
            return new SlotSuccess<>("recommendations", SlotPolicy.OPTIONAL, decodeRecommendations(response.body()));
        } catch (HttpTimeoutException e) {
            return new SlotUnavailable<>("recommendations", SlotPolicy.OPTIONAL,
                    new AggregateIssue("recommendations", SlotPolicy.OPTIONAL, "timeout", true, false, null));
        }
    }

    private SlotResult<PromoBanner> fetchPromoBannerFallbackable() throws Exception {
        try {
            HttpResponse<String> response = sendWithinBudget(URI.create("https://partner/banner"));
            return new SlotSuccess<>("banner", SlotPolicy.FALLBACKABLE, decodeBanner(response.body()));
        } catch (HttpTimeoutException e) {
            PromoBanner cached = loadCachedBanner();
            return new SlotDegraded<>("banner", SlotPolicy.FALLBACKABLE, cached,
                    new AggregateIssue("banner", SlotPolicy.FALLBACKABLE, "timeout", true, true, null));
        }
    }

    private HttpResponse<String> sendWithinBudget(URI uri) throws Exception {
        RequestBudget budget = REQUEST_BUDGET.get();
        Duration remaining = Duration.between(Instant.now(), budget.deadline());
        if (remaining.isZero() || remaining.isNegative()) {
            throw new HttpTimeoutException("parent deadline exceeded");
        }

        Duration attemptBudget =
                remaining.compareTo(MAX_PER_ATTEMPT) < 0 ? remaining : MAX_PER_ATTEMPT;

        HttpRequest request = HttpRequest.newBuilder(uri)
                .timeout(attemptBudget)
                .header("X-Trace-Id", budget.traceId())
                .build();

        return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private static List<AggregateIssue> collectIssues(List<SlotResult<?>> results) {
        List<AggregateIssue> issues = new ArrayList<>();
        for (SlotResult<?> result : results) {
            if (result instanceof SlotDegraded<?> degraded) {
                issues.add(degraded.issue());
            } else if (result instanceof SlotUnavailable<?> unavailable) {
                issues.add(unavailable.issue());
            }
        }
        return List.copyOf(issues);
    }

    private static DegradationTier deriveTier(List<SlotResult<?>> results) {
        boolean usedFallback = results.stream().anyMatch(SlotDegraded.class::isInstance);
        boolean missingOptional = results.stream()
                .anyMatch(result -> result instanceof SlotUnavailable<?> unavailable
                        && unavailable.policy() == SlotPolicy.OPTIONAL);

        if (usedFallback) {
            return DegradationTier.FALLBACK_USED;
        }
        if (missingOptional) {
            return DegradationTier.OPTIONAL_OMITTED;
        }
        return DegradationTier.FULL;
    }

    // decode/load helpers omitted
}
```

이 코드에서 중요한 점은 다음이다.

- subtask는 예외를 무조건 바깥으로 던지지 않고, slot policy에 맞는 결과 타입으로 변환한다
- `ScopedValue`는 request trace/deadline 같은 읽기 전용 budget을 child task에 전달한다
- `Optional`은 최종 response projection에서만 등장한다
- fallback payload를 썼어도 `AggregateIssue`를 남겨 degraded 사실을 숨기지 않는다
- scope를 닫고 응답을 만든 뒤에는 background retry가 남지 않는다

## 실전 시나리오

### 시나리오 1: 대시보드에서 추천 영역만 자주 빠진다

추천 downstream이 optional인데도 `CompletableFuture.allOf(...).join()` 한 곳에서 전부 실패로 올리면,  
사용자에게는 너무 비싼 실패가 되고 운영자는 어떤 slot이 원인인지 보기 어렵다.

이때는:

- profile, entitlement 같은 필수 slot은 `REQUIRED`
- recommendations, recent views 같은 보조 slot은 `OPTIONAL`
- banner, ranking seed 같이 stale cache 허용이 가능한 slot은 `FALLBACKABLE`

처럼 분리하는 편이 낫다.

### 시나리오 2: `null`로 내려보내니 장애가 숨겨진다

응답 필드가 `null`이면 소비자는 보통 "값이 없음"으로 읽는다.  
하지만 partial success 상황에서는:

- 원래 빈 값인지
- optional omission인지
- fallback 사용인지

를 구분해야 한다.  
즉 내부 fan-in에서는 `SlotResult`를 유지하고, 외부 projection에서만 `null`/field omission을 선택해야 한다.

### 시나리오 3: timeout 후 cache warm-up을 계속 돌린다

request deadline이 끝난 뒤에도 추천 데이터를 더 받아 cache를 갱신하려고 retry를 계속 돌리면,  
응답은 이미 끝났는데 upstream 부하는 계속 남는다.

이 경우는 partial success fan-in으로 퉁칠 문제가 아니라:

- 현재 요청 응답용 degraded result는 즉시 닫고
- cache refresh가 정말 필요하면 별도 queue/job로 분리하고
- ownership과 shutdown 정책을 새로 둬야 한다

## 관측 포인트

partial success fan-in을 넣었다면 최소한 아래는 같이 봐야 한다.

- `FULL` / `OPTIONAL_OMITTED` / `FALLBACK_USED` / `FAILED_REQUIRED` 비율
- slot별 timeout, 429, 5xx, decode error 비율
- fallback source hit ratio와 fallback 데이터 freshness
- parent deadline 초과로 scope가 닫힌 요청 수
- 응답 종료 뒤에도 child task가 남았는지 여부

이 지표가 없으면 degraded success가 그냥 `200 OK` 속으로 숨어버린다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| fail-fast only | 단순하다 | optional slot까지 과도하게 실패시킬 수 있다 |
| typed partial success fan-in | degraded semantics와 운영 설명력이 좋아진다 | result type과 response contract가 조금 더 복잡해진다 |
| `null`/empty로 단순화 | payload는 짧다 | 원래 빈 값과 장애를 구분하기 어렵다 |
| fallback 적극 사용 | 사용자 체감은 지킬 수 있다 | stale/default 응답을 정상 성공처럼 숨기기 쉽다 |

핵심 trade-off는 "코드가 짧은가"보다 "degraded response를 설명 가능하게 유지할 수 있는가"다.

## 꼬리질문

> Q: optional downstream이면 그냥 `Optional.empty()`만 반환해도 되나요?
> 핵심: fan-in 내부에서는 부족하다. 왜 비었는지 알 수 있도록 slot outcome과 issue를 먼저 유지해야 한다.

> Q: fallback을 썼으면 성공으로 봐도 되지 않나요?
> 핵심: 사용자 응답은 성공일 수 있지만 운영 의미까지 full success는 아니다. tier와 issue를 따로 남겨야 한다.

> Q: partial success인데 왜 scope를 닫고 끝내야 하나요?
> 핵심: request-scoped fan-in의 본질은 parent가 child lifetime을 소유하는 것이다. 요청 뒤까지 살아남는 작업은 별도 background ownership으로 분리해야 한다.

> Q: aggregate error report는 사용자에게 그대로 보여줘야 하나요?
> 핵심: 아니다. 사용자 계약용 요약과 운영 상세 원인은 분리하고, raw cause는 log/trace에 남기는 편이 안전하다.

## 한 줄 정리

partial success fan-in은 "일부 실패 허용"이 아니라 request-scoped structured fan-out 위에서 slot policy, degradation tier, aggregate issue reporting을 함께 설계해 degraded response를 설명 가능하게 만드는 패턴이다.
