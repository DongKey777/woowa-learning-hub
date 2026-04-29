# Retry Amplification and Backpressure Primer

> 한 줄 요약: client, app, worker가 각자 재시도를 시작하면 하나의 느린 장애가 여러 겹의 동시 시도로 증폭되고, bounded queue와 load shedding은 그 증폭을 잘라 blast radius를 제한한다.

retrieval-anchor-keywords: retry amplification primer, retry storm containment, client retry, app retry, worker retry, retry budget, bounded queue, queue backlog, queue age limit, load shedding, overload containment, blast radius control, deadline-aware retry, 처음 retry storm 뭐예요, 왜 재시도가 장애를 키워요

**난이도: 🟢 Beginner**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
- [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md)
- [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
- [Job Queue 설계](./job-queue-design.md)
- [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
- [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

---

## 막히면 여기로 돌아오기: Beginner 3단계 사다리

retry 문서를 읽다가 바로 queue 설계나 outage playbook으로 내려가기 전에, 먼저 `느린 요청 -> 남은 시간 -> 증폭 차단` 사다리를 한 번만 고정하는 편이 안전하다.

| 단계 | 문서 | 지금 확정할 것 |
|---|---|---|
| 1. primer | [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md) | cache/queue/app/db 중 어디서 장애가 시작돼 다른 레이어로 번지는지 |
| 2. primer bridge | [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md) | 첫 시도가 아직 살아 있을 때 새 시도를 열면 왜 겹치는지 |
| 3. primer bridge | [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md) | logical request 1개가 여러 attempt로 늘어나는 장면과 bounded queue의 필요성 |

- safe next step: `어떤 기능을 먼저 포기할지`가 궁금하면 [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md), `queue depth/age watermark와 shed 계약`이 궁금하면 [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)로 이어간다.
- cross-category bridge: `retry/backoff/jitter` HTTP 호출 규칙을 먼저 보고 싶다면 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), queue의 기본 역할이 먼저 헷갈리면 [메시지 큐 기초](./message-queue-basics.md)를 짧게 보고 다시 이 문서로 돌아온다.
- stop rule: 아직 `같은 logical request가 몇 개 attempt로 번졌는지` 계산이 안 되면 job queue, idempotency store, recovery deep dive로 바로 내려가지 않는다.

## 핵심 개념

retry 자체는 나쁜 것이 아니다.
문제는 **각 레이어가 서로를 모른 채 동시에 retry**할 때다.

- client는 timeout이 나서 다시 보낸다
- gateway나 proxy는 upstream error를 보고 다시 보낸다
- app은 내부 RPC나 DB query를 다시 시도한다
- worker는 외부 provider 실패 후 queue redelivery를 시작한다

그러면 "논리적으로 하나의 요청"이 시스템 안에서는 여러 개의 살아 있는 시도로 번진다.

```text
logical request 1개
  -> client 2회
  -> app 2회
  -> worker 3회
  = 최대 12개 시도
```

중요한 것은 총 횟수보다 **겹쳐서 살아 있는 시도 수**다.
첫 시도가 아직 끝나지 않았는데 다음 시도가 들어오면, 같은 장애가 더 큰 장애로 자란다.

즉 이 문서의 핵심은 두 가지다.

1. retry amplification은 partial failure를 outage로 키우는 대표 메커니즘이다.
2. bounded queue, retry budget, load shedding은 그 증폭을 끊는 containment 장치다.

처음 읽는다면 아래 그림으로 충분하다.

| 질문 | 초보자용 답 |
|---|---|
| retry amplification이 뭐예요? | 요청 1개가 시도 여러 개로 불어나는 것 |
| 왜 위험해요? | 첫 시도가 아직 살아 있는데 새 시도가 겹쳐 같은 장애를 더 누른다 |
| backpressure는 뭐예요? | 지금 더 받으면 핵심 경로까지 죽는다고 보고 속도를 줄이거나 거절하는 것 |
| bounded queue는 왜 써요? | 나중에 처리해도 의미 없는 일을 무한히 쌓지 않기 위해서 |

---

## 깊이 들어가기

### 1. retry amplification은 어디서 시작되나

같은 요청이 여러 번 실행되는 경로는 생각보다 많다.

| 레이어 | 재시도 이유 | 흔한 실수 | 결과 |
|---|---|---|---|
| client/mobile/browser | timeout, network reset, 사용자의 새로고침 | 이전 시도 취소 없이 새 요청 시작 | 같은 사용자 요청이 중복 유입 |
| gateway/proxy | upstream 502, connect timeout | app와 동시에 retry | 동일 hop에 중복 부하 |
| app/service | cache miss, DB timeout, downstream 5xx | 남은 budget 없이 blind retry | 오래된 시도와 새 시도가 겹침 |
| worker/queue | provider error, ack 누락, visibility timeout 만료 | 오래된 job을 무한 적재 | backlog와 redelivery storm |

즉 retry amplification은 "client가 많이 누른다" 정도가 아니라,
**각 레이어의 안전장치가 서로 합쳐져 폭주 경로가 되는 현상**이다.

### 2. 왜 느린 장애가 더 위험한가

완전 outage라면 많은 요청이 빠르게 실패한다.
반대로 부분 장애는 요청이 오래 살아남아서 더 위험하다.

예:

- 평소 DB p95: 40ms
- 장애 중 DB p95: 900ms
- client deadline: 1s
- client retry: 1회
- app retry: 1회

이때 첫 번째 query가 DB에서 아직 돌고 있는 상태에서 client와 app이 새 시도를 시작할 수 있다.
그러면 사용자 한 명의 읽기 요청이 최대 4개의 DB 시도로 늘어난다.

```text
1 logical read
  -> client attempts 2
  -> app attempts 2
  = max 4 DB executions
```

여기에 외부 webhook worker나 async notification worker까지 같은 DB, cache, provider를 바라보면
동기 경로에서 시작한 작은 지연이 **queue backlog + worker redelivery**까지 번진다.

그래서 outage 때는 단순 error rate보다 아래 신호가 더 중요하다.

- retry rate
- in-flight attempt 수
- queue depth
- oldest job age
- DB pool wait / lock wait

### 3. bounded queue가 왜 중요한가

queue는 burst를 흡수하는 도구지만, 무한 버퍼가 되면 장애 증폭기가 된다.
다만 모든 시스템이 같은 임계치를 쓰는 것은 아니다. `max_depth`, `max_age`, shed 정책은 제품 가치와 복구 목표에 따라 달라진다.

unbounded queue의 문제:

## 깊이 들어가기 (계속 2)

- 처리할 수 없는 low-value job이 계속 쌓인다
- 오래된 work가 최신 work보다 먼저 자원을 먹는다
- 복구 직후에도 backlog drain 때문에 장애 tail이 길어진다
- memory, disk, consumer lag가 새로운 incident를 만든다

bounded queue는 반대로 운영 계약을 분명하게 만든다.

- depth 상한을 둔다
- age 상한을 둔다
- high watermark를 넘으면 enqueue를 거부하거나 defer한다
- business deadline이 지난 job은 과감히 드롭한다

핵심은 "일단 받아 두자"가 아니라 **지금 받아도 나중에 의미 있게 처리할 수 있는가**다.

### 4. load shedding은 무엇을 살리기 위한 포기인가

shedding의 목적은 실패를 숨기는 것이 아니라 핵심 경로를 남기는 것이다.

보통 먼저 버리는 후보:

- analytics event
- 대량 export
- recommendation refresh
- thumbnail generation
- retry 가능한 webhook fan-out

끝까지 지키려는 후보:

- 로그인
- 결제 승인
- 재고 확인
- 핵심 read API

좋은 overload 대응은 아래 순서에 가깝다.

```text
fail-fast on low-value work
  -> bounded queue only for useful work
  -> stale/read-only/degrade for non-critical features
  -> core path만 보존
```

즉 shedding은 "아무거나 버린다"가 아니라
**핵심 경로를 살리기 위해 어떤 work를 포기할지 미리 정한 정책**이다.

### 5. retry budget의 owner를 하나로 줄여야 한다

가장 흔한 설계 실수는 모든 레이어가 retry를 가져가는 것이다.

좋은 방향은 retry owner를 명확히 두는 것이다.

| 레이어 | 해야 하는 것 | 피해야 하는 것 |
|---|---|---|
| client | 적은 횟수, jitter, 전체 deadline 존중 | 버튼 연타나 자동 refresh로 blind retry |
| app | 남은 budget이 있을 때만 retry, idempotent path 위주 | client와 동시에 같은 hop retry |
| worker | bounded retry, DLQ, expired job drop | provider 장애 동안 무한 redelivery |
| queue | depth/age watermark enforcement | 모든 작업을 무기한 적재 |

실전 규칙:

## 깊이 들어가기 (계속 3)

1. 같은 hop의 retry owner는 가능하면 한 군데만 둔다.
2. remaining budget이 full attempt cost보다 작으면 retry하지 않는다.
3. idempotency가 없는 write는 retry보다 recover-first를 우선한다.
4. worker는 "언젠가 성공하겠지" 대신 max attempts와 DLQ를 명시한다.

## 흔한 헷갈림

- "`retry를 끄면 더 안전한가요?`"라고 묻기 쉽다.
  - 아니다. 짧은 네트워크 흔들림에는 제한된 retry가 유용할 수 있다. 문제는 owner 없이 여러 레이어가 동시에 retry하는 경우다.
- `queue가 있으니 일단 다 받아 두자`고 생각하기 쉽다.
  - 위험하다. deadline이 지난 work까지 쌓이면 복구 뒤에도 tail latency와 backlog가 길어진다.
- `load shedding`을 실패 숨기기로 오해하기 쉽다.
  - 실제 목적은 저가치 작업을 먼저 포기해 로그인, 결제 같은 핵심 경로를 살리는 것이다.

### 6. queue는 depth만이 아니라 age로도 잘라야 한다

queue depth만 보면 "많이 쌓였는가"만 보게 된다.
하지만 outage containment에는 **oldest age**가 더 중요할 때가 많다.

이유:

- depth가 작아도 소비 속도가 느리면 이미 늦은 작업일 수 있다
- 복구 후에도 오래된 작업은 business value가 낮을 수 있다
- 사용자는 지금의 요청이 중요하지, 20분 전 analytics flush가 중요한 것은 아니다

그래서 실전에서는 보통 둘 다 둔다.

- `max_depth`
- `max_age`
- `high_watermark`
- `drop_if_deadline_expired`

예를 들어:

- OTP email은 30초가 지나면 의미가 거의 없다
- export job은 사용자에게 "나중에 다시 요청"이 더 나을 수 있다
- recommendation refresh는 최신 snapshot만 남기고 이전 batch는 버려도 된다

### 7. 관측도 logical request 기준으로 봐야 한다

retry storm 때는 HTTP request count만 보면 착시가 생긴다.
같은 논리 요청이 여러 attempt로 부풀어 있기 때문이다.

그래서 가능하면 `operation_id` 또는 trace 기준으로 본다.

- logical request 대비 total attempt ratio
- retry가 붙은 request 비율
- queue enqueue 대비 completed ratio
- shed/drop 비율
- DLQ 유입률
- dependency별 concurrent attempt 수

중요한 질문은 이것이다.

- 실패한 요청이 몇 개인가
- 가 아니라, **하나의 실패가 몇 개의 시도로 번졌는가**

---

## 실전 시나리오

### 시나리오 1: cache slowdown이 DB incident로 번진다

문제:

- cache p99가 급증한다
- app은 cache 후 DB fallback을 매번 시도한다
- client는 1초 timeout 뒤 새 요청을 보낸다

악화 경로:

- 첫 read는 cache wait 뒤 DB로 간다
- client는 첫 read가 끝나기 전에 second attempt를 보낸다
- DB에는 old query와 new query가 함께 살아 있다
- 비핵심 추천/집계 요청도 같이 들어와 DB를 더 누른다

완화:

- cache timeout을 짧게 줄인다
- 남은 budget이 작으면 DB fallback을 시작하지 않는다
- 추천/집계는 shed한다
- queue 기반 후처리는 bounded queue로 제한한다

## 여기서 다음으로 갈 것

처음이면 이 문서에서 "`왜 재시도가 장애를 키우는지`"까지만 잡으면 충분하다. 다음 질문이 생길 때만 아래로 내려가면 된다.

| 지금 질문 | 다음 문서 | 이유 |
|---|---|---|
| "`timeout budget이랑 같이 보면 어떤 순서로 끊어야 해요?`" | [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md) | retry 전에 남은 시간을 먼저 보는 감각을 붙인다 |
| "`queue에서 뭘 버리고 뭘 살리죠?`" | [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md) | watermark, shed 계약을 더 구체화한다 |
| "`중복 실행을 완전히 막으려면요?`" | [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md) | retry를 허용해도 부작용을 줄이는 저장소 설계로 이어진다 |

이 시나리오는 beginner 기준으로 `Request Path Failure Modes Primer -> Request Deadline and Timeout Budget Primer -> Retry Amplification and Backpressure Primer` 사다리를 그대로 다시 보여 준다.
처음 읽는 단계라면 여기서 `왜 DB가 맞는가`, `왜 남은 budget 없이 retry하면 겹치는가`까지만 설명할 수 있으면 충분하다.

### 시나리오 2: webhook provider outage가 worker storm를 만든다

문제:

- 외부 provider가 5xx를 반환한다
- worker가 즉시 retry한다
- queue가 무한히 쌓이면서 오래된 webhook도 계속 남는다

악화 경로:

- 같은 event가 여러 번 redelivery된다
- provider recovery 뒤에도 backlog drain이 길게 남는다
- core write path와 같은 DB/outbox를 공유하면 앞단까지 느려진다

완화:

- worker retry 횟수와 backoff를 제한한다
- queue age limit을 넘긴 job은 drop 또는 DLQ로 보낸다
- low-priority webhook은 provider outage 동안 shed한다
- provider별 bulkhead로 핵심 경로를 분리한다

---

## 코드로 보기

```pseudo
function shouldRetry(attempt, remainingBudget, queue, request):
  if !request.idempotent:
    return false
  if remainingBudget < MIN_ATTEMPT_BUDGET:
    return false
  if queue.depth > HIGH_WATERMARK:
    return false
  if queue.oldestAge > MAX_QUEUE_AGE:
    return false
  return attempt < MAX_ATTEMPTS

function enqueue(job):
  if job.deadlineExpired():
    drop(job)
    return
  if queue.depth > HIGH_WATERMARK and job.priority == LOW:
    shed(job)
    return
  queue.push(job)
```

```java
public boolean accept(Job job, OverloadSignal signal) {
    if (job.deadlineExpired()) {
        return false;
    }
    if (signal.queueDepth() > HIGH_WATERMARK && job.priority() == Priority.LOW) {
        return false;
    }
    return signal.retryBudgetRemaining(job.operationId()) > 0;
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 무조건 retry | 일시적 오류에 단순 대응 | outage amplification이 매우 크다 | 거의 권장되지 않음 |
| bounded retry + backoff | 작은 흔들림을 흡수 | latency가 늘 수 있다 | 일반적인 sync/async 처리 |
| bounded queue | blast radius를 제한 | 일부 요청을 거절해야 한다 | overload containment가 필요할 때 |
| load shedding | 핵심 경로를 보호 | 비핵심 기능이 사라진다 | partial failure가 번질 때 |
| DLQ / expired drop | backlog tail을 줄인다 | 운영 판단이 필요하다 | 늦은 작업 가치가 낮을 때 |

핵심은 retry를 많이 하는 것이 회복력이 아니라,
**언제 retry를 멈추고 언제 work를 버릴지 정하는 것이 회복력**이라는 점이다.

---

## 꼬리질문

> Q: retry amplification은 왜 완전 outage보다 partial failure에서 더 심해지나요?
> 의도: 느린 실패와 overlap 문제를 이해하는지 확인
> 핵심: 완전 outage는 빨리 실패하지만, partial failure는 첫 시도가 오래 살아남아 다음 시도와 겹치기 때문이다.

> Q: bounded queue에서 depth 말고 age를 왜 같이 보나요?
> 의도: backlog의 business value를 보는지 확인
> 핵심: 오래된 작업은 복구 후에도 가치가 낮을 수 있어서 depth만으로는 containment가 부족하다.

> Q: load shedding은 단순 rate limiting과 무엇이 다른가요?
> 의도: overload 대응과 일반 정책 제어를 구분하는지 확인
> 핵심: rate limit은 평상시 규칙이고, shedding은 포화 시 핵심 경로를 살리기 위한 동적 포기 정책이다.

> Q: retry owner를 한 군데만 두라고 하는 이유는 무엇인가요?
> 의도: 중복 retry와 곱셈 효과를 설명할 수 있는지 확인
> 핵심: 여러 레이어가 동시에 retry하면 한 요청이 여러 attempt로 증폭되어 장애를 키우기 때문이다.

## 한 줄 정리

retry amplification은 느린 장애를 여러 겹의 동시 시도로 키우고, bounded queue와 load shedding은 그 증폭을 초기에 잘라 시스템의 blast radius를 제한한다.
