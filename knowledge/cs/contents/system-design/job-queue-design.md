---
schema_version: 3
title: Job Queue 설계
concept_id: system-design/job-queue-design
canonical: true
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 87
mission_ids: []
review_feedback_tags:
- async-worker-queue-design
- retry-dlq-idempotency
- backpressure-worker-pool
aliases:
- job queue design
- 작업 큐 설계
- durable job queue
- worker pool retry DLQ
- visibility timeout
- at-least-once processing
- delayed job
- redrive queue
symptoms:
- 큐를 단순히 나중에 처리하는 저장소로만 보고 retry, ack, visibility timeout을 놓치고 있어
- at-least-once 전달에서 중복 처리가 왜 필수인지 헷갈려
- backlog가 쌓일 때 worker만 늘리면 된다고 생각하고 producer rate limit과 backpressure를 놓치고 있어
intents:
- design
- deep_dive
- troubleshooting
prerequisites:
- system-design/message-queue-basics
- system-design/back-of-envelope-estimation
- network/timeout-retry-backoff-practical
next_docs:
- system-design/workflow-orchestration-saga-design
- system-design/replay-repair-orchestration-control-plane-design
- system-design/rate-limiter-design
- system-design/notification-system-design
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/network/timeout-retry-backoff-practical.md
- contents/system-design/workflow-orchestration-saga-design.md
- contents/system-design/notification-system-design.md
- contents/system-design/rate-limiter-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
confusable_with:
- system-design/message-queue-basics
- system-design/workflow-orchestration-saga-design
- system-design/rate-limiter-design
- network/timeout-retry-backoff-practical
forbidden_neighbors: []
expected_queries:
- Job Queue를 설계할 때 producer, queue, worker, ack 흐름을 어떻게 잡아?
- at-least-once queue에서 왜 idempotency와 dedup key가 필요해?
- visibility timeout과 retry, DLQ는 worker crash를 어떻게 다뤄?
- backlog가 쌓이면 worker 수만 늘리는 게 위험한 이유는 뭐야?
- 순서가 중요한 job은 partition key를 어떻게 골라야 해?
contextual_chunk_prefix: |
  이 문서는 job queue design deep dive로, producer enqueue, worker pool, ack, visibility timeout, retry/backoff, DLQ, at-least-once, idempotency, backlog/backpressure를 다룬다.
  작업 큐 설계, durable delivery, worker crash retry, visibility timeout, dead letter queue, backlog, delayed job 같은 자연어 질문이 본 문서에 매핑된다.
---
# Job Queue 설계

> 한 줄 요약: 느린 작업을 요청 경로에서 분리하고, 버퍼링과 재시도로 시스템을 안정화하는 비동기 작업 처리 설계다.

retrieval-anchor-keywords: job queue, durable delivery, worker pool, retry, dead letter queue, visibility timeout, at-least-once, backpressure, priority queue, delayed job, redrive queue, replay campaign

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Workflow Orchestration + Saga 설계](./workflow-orchestration-saga-design.md)
> - [Notification 시스템 설계](./notification-system-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)

## 핵심 개념

Job Queue는 단순한 "나중에 처리" 기능이 아니다.  
실전에서는 아래를 동시에 해결한다.

- 요청 경로와 느린 작업 분리
- burst 트래픽 흡수
- worker 수평 확장
- 재시도와 실패 격리
- 순서와 중복 처리 제어

즉, 큐는 저장소이면서 흐름 제어 장치다.

## 깊이 들어가기

### 1. 어떤 작업을 큐로 보내는가

큐에 넣을 만한 작업은 보통 아래 중 하나다.

- 느리지만 즉시 응답이 필요 없는 작업
- 외부 API 호출
- 대량 fan-out 작업
- 이미지/비디오 처리
- 리포트 생성
- 이메일, 푸시, 웹훅 발송

반대로 큐에 넣기 어려운 작업도 있다.

- 즉시 일관성이 필요한 결제 핵심 경로
- 매우 짧은 지연이 중요한 사용자 인터랙션
- 큐 지연이 곧 장애가 되는 동기 API

### 2. Capacity Estimation

큐는 생산 속도와 소비 속도의 차이를 봐야 한다.

예:

- 평균 유입: 2,000 jobs/sec
- worker 1개 처리 속도: 100 jobs/sec
- worker 30개 배치 시 총 처리 속도: 3,000 jobs/sec

이 경우 평균적으로는 버틸 수 있지만, burst가 오면 backlog가 쌓인다.  
그래서 다음이 중요하다.

- peak arrival rate
- 평균 처리 시간
- p95 처리 시간
- retry amplification factor
- queue depth 한계

간단한 근사식:

```text
required_workers = peak_jobs_per_sec / jobs_per_worker_sec
```

### 3. Delivery semantics

메시지 전달 보장은 보통 아래 셋 중 하나다.

| 방식 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| At-most-once | 중복이 적다 | 유실 가능 | 로그성 작업, 허용 가능한 유실 |
| At-least-once | 유실이 적다 | 중복 가능 | 대부분의 업무 큐 |
| Exactly-once | 이상적이다 | 구현/운영이 매우 어렵다 | 제한된 환경에서만 |

실무에서는 대부분 at-least-once를 받아들이고, 소비자 쪽에서 idempotency를 만든다.

### 4. Ack, visibility timeout, retry

대표 흐름은 다음과 같다.

1. producer가 job을 enqueue한다.
2. worker가 job을 lease 또는 reserve 한다.
3. worker가 처리 후 ack한다.
4. ack가 없으면 visibility timeout 이후 재노출된다.

이 구조는 worker crash를 견디는 데 유리하지만, 동일 job이 두 번 처리될 수 있다.  
그래서 job key 또는 dedup key가 필요하다.

### 5. Retry와 backoff

모든 실패를 즉시 재시도하면 더 망가진다.

권장 패턴:

- 일시적 실패는 exponential backoff
- 영구 실패는 DLQ로 보낸다
- 외부 API 장애 시 circuit breaker를 건다
- 재시도 횟수를 제한한다

이 부분은 [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)과 강하게 연결된다.

### 6. Ordering과 partitioning

순서가 중요한 작업은 partition key를 잘 골라야 한다.

- user_id 기준 순서
- order_id 기준 순서
- tenant_id 기준 순서

전역 순서는 비싸다. 그래서 "무엇의 순서가 중요한가"를 좁혀야 한다.  
예를 들어 같은 주문에 대한 작업은 순서를 유지하지만, 서로 다른 주문은 병렬화할 수 있다.

### 7. Backpressure와 격리

큐는 쌓이기만 하면 안 된다.  
backlog가 커지면 다음 조치가 필요하다.

- 우선순위 큐 분리
- tenant별 queue 분리
- producer rate limit
- worker pool bulkhead
- 오래된 job 드랍 또는 degrade

이건 [Rate Limiter 설계](./rate-limiter-design.md)와 같이 설계해야 한다.

## 실전 시나리오

### 시나리오 1: 이메일 발송

문제:

- 가입 직후 이메일이 한꺼번에 몰린다
- 외부 메일 API가 느리다

해결:

- 발송 요청은 queue에 넣는다
- worker pool로 병렬 처리한다
- 실패한 메일은 retry 후 DLQ로 보낸다

### 시나리오 2: 이미지 리사이즈

문제:

- 업로드 직후 썸네일 생성이 오래 걸린다
- 여러 해상도를 동시에 만들어야 한다

해결:

- 업로드는 즉시 응답
- 변환 작업은 queue로 분리
- 동일 파일의 중복 처리 방지를 위해 job key를 둔다

### 시나리오 3: 리포트 생성 폭주

문제:

- 월말에 대용량 집계 작업이 한꺼번에 들어온다
- DB와 저장소가 흔들린다

해결:

- tenant별 quota를 둔다
- 낮은 우선순위 job은 지연시킨다
- batch worker를 별도 풀로 분리한다

## 코드로 보기

```pseudo
function enqueue(job):
  if exists(job.dedupKey):
    return existingJobId
  save(job, status="READY")
  publish(job.id)

function workerLoop():
  job = reserveNext()
  try:
    process(job)
    ack(job)
  catch transientError:
    retryWithBackoff(job)
  catch permanentError:
    moveToDLQ(job)
```

```java
public void handle(Job job) {
    if (jobRepository.isDuplicate(job.dedupKey())) {
        return;
    }
    processor.process(job);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| FIFO queue | 단순하다 | 우선순위 제어가 약하다 | 작은 시스템 |
| Priority queue | 중요한 작업을 먼저 처리한다 | starvation 위험 | 운영 알림, 결제 보조 작업 |
| Partitioned queue | 순서와 확장이 좋다 | hot partition 가능 | tenant/order 단위 처리 |
| Stream 기반 | 재처리와 replay가 쉽다 | 소비 모델이 복잡하다 | 이벤트 중심 플랫폼 |
| Queue + DLQ | 장애 격리가 쉽다 | 운영이 늘어난다 | 실서비스 대부분 |

핵심은 "큐를 넣느냐 마느냐"가 아니라 **어떤 실패를 큐가 흡수하고, 어떤 실패를 소비자가 책임지는가**다.

## 꼬리질문

> Q: 왜 exactly-once를 기본으로 만들지 않나요?
> 의도: 전달 보장의 비용을 이해하는지 확인
> 핵심: 분산 환경에서 완전한 exactly-once는 비용이 크고 운영 난이도가 높다.

> Q: visibility timeout은 왜 필요한가요?
> 의도: worker crash와 메시지 회복 이해 확인
> 핵심: ack가 없을 때 job을 다시 노출시켜 유실을 줄이기 위해서다.

> Q: poison message는 어떻게 처리하나요?
> 의도: 반복 실패 격리 능력 확인
> 핵심: 재시도 제한 후 DLQ로 보내고, 운영자가 원인을 확인한다.

> Q: job dedup은 어디서 해야 하나요?
> 의도: 중복 처리 방어층 이해 확인
> 핵심: producer와 consumer 둘 다에서 방어하는 편이 안전하다.

## 한 줄 정리

Job Queue는 느린 작업을 버퍼링하고 재시도와 격리를 담당해, 요청 경로를 보호하는 비동기 처리의 핵심 인프라다.
