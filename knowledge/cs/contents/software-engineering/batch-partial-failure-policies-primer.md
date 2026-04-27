# Batch Partial Failure Policies Primer

> 한 줄 요약: batch가 "실패한 item만 다시 돌리면 끝"을 넘는 순간, chunk summary, retry queue, checkpoint를 따로 설계해야 run 의미와 운영 설명이 맞아진다.

**난이도: 🟢 Beginner**

[Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)에서 "언제 batch run 자체가 별도 application capability가 되는가"를 봤다면, 이 문서는 그다음 질문인 "실패 정책은 어디까지 batch 의미로 끌어올려야 하는가"만 좁혀서 본다.
outbound port를 `List` 기반 bulk 계약으로 올릴지 고민 중이라면 [Bulk Port vs Per-Item Use Case Tradeoffs](./bulk-port-vs-per-item-use-case-tradeoffs.md), [saveAll/sendAll Port Smells and Safer Alternatives](./saveall-sendall-port-smells-safer-alternatives.md)를 같이 보면 경계가 더 선명해진다.
bulk가 실제 업무 단위라서 run/chunk/file 입력 타입과 partial failure result 타입을 설계해야 한다면 [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)를 follow-up으로 보면 된다.
`RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`처럼 결과 모델 이름을 어떻게 나눌지 예시가 필요하면 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 같이 보면 된다.
실패 후 재시도할 때 item/chunk/run idempotency key를 어디에 둘지 헷갈리면 [Batch Idempotency Key Boundaries](./batch-idempotency-key-boundaries.md)를 이어서 보면 된다.
정책을 읽은 뒤 바로 테스트로 옮기고 싶다면 [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)에서 실패 분류를 작은 assertion으로 잠그고, 이어서 [Batch Result Testing Checklist](./batch-result-testing-checklist.md)에서 run/chunk/retry/checkpoint 전체를 확인하는 순서가 beginner practice loop로 가장 짧다.
이 정책 결정을 실제 operator runbook 단계, stop condition, safe rerun checklist로 옮기는 후속 문서는 [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)다.
멱등성, exactly-once 착시, 저장 경계까지 깊게 들어가려면 [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)로 내려가면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 잡는 한 줄 멘탈 모델](#먼저-잡는-한-줄-멘탈-모델)
- [before / after 한눈 비교](#before--after-한눈-비교)
- [세 가지 정책 레벨](#세-가지-정책-레벨)
- [1. pure per-item retry면 충분한 경우](#1-pure-per-item-retry면-충분한-경우)
- [2. chunk summary와 retry queue가 필요한 경우](#2-chunk-summary와-retry-queue가-필요한-경우)
- [3. checkpoint까지 필요한 경우](#3-checkpoint까지-필요한-경우)
- [짧은 비교 표](#짧은-비교-표)
- [예시: 같은 batch가 어떻게 커지는가](#예시-같은-batch가-어떻게-커지는가)
- [beginner practice loop](#beginner-practice-loop)
- [흔한 오해와 함정](#흔한-오해와-함정)
- [기억할 기준](#기억할-기준)
- [한 줄 정리](#한-줄-정리)

</details>

관련 문서:

- [Software Engineering README: Batch Partial Failure Policies Primer](./README.md#batch-partial-failure-policies-primer)
- [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
- [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
- [Batch Result Testing Checklist](./batch-result-testing-checklist.md)
- [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
- [Runbook, Playbook, Automation Boundaries](./runbook-playbook-automation-boundaries.md)
- [System Design: Job Queue 설계](../system-design/job-queue-design.md)

retrieval-anchor-keywords: batch partial failure policy, batch retry queue primer, chunk summary retry queue checkpoint, per-item retry vs checkpoint resume, batch checkpoint resume beginner, batch failure recovery policy, run summary retry policy, batch result testing checklist, batch recovery runbook bridge, batch idempotency key boundaries, true bulk contract, item failure result, batch partial failure 뭐예요, 처음 배우는데 batch retry queue, batch partial failure policies primer basics

## 왜 이 primer가 필요한가

초심자 batch 코드는 보통 이렇게 시작한다.

- 대상 목록을 읽는다
- `for` loop로 한 건씩 처리한다
- 실패한 item id만 모아 다시 재시도한다

처음에는 충분하다.
그런데 batch가 커지면 운영 질문이 달라진다.

- "이번 run에서 어디까지 끝났나?"
- "실패한 12건은 바로 재시도해도 되는가, 아니면 데이터 수정 후 따로 봐야 하는가?"
- "서버가 중간에 죽었는데 처음부터 다시 돌려도 안전한가?"

이 질문이 생기면 더 이상 per-item retry만으로는 설명이 부족하다.
이때 필요한 것이 chunk summary, retry queue, checkpoint다.

## 먼저 잡는 한 줄 멘탈 모델

가장 쉬운 판단 기준은 이것이다.

- **장애 후에 무엇을 기억해야 다시 안전하게 이어 갈 수 있는가**

| 장애 후에 꼭 남아 있어야 하는 것 | 보통 필요한 정책 |
|---|---|
| 실패한 item 목록 정도면 충분하다 | pure per-item retry |
| "어느 chunk에서 몇 건이 왜 실패했는지"가 필요하다 | chunk summary |
| 실패 item을 main run과 분리해 나중에 다시 처리해야 한다 | retry queue |
| "여기까지는 끝났다"는 안전한 진행 지점이 필요하다 | checkpoint |

즉 세 용어는 비슷해 보여도 역할이 다르다.

- chunk summary는 **이번 chunk에서 무슨 일이 있었는지 남기는 영수증**
- retry queue는 **main run에서 빼낸 실패 item의 다음 경로**
- checkpoint는 **main run을 어디서 다시 시작할지 정하는 저장 지점**

## before / after 한눈 비교

| 상태 | 운영 질문 | 결과 |
|---|---|---|
| before: 실패 item만 다시 돌리면 된다고 봄 | "실패한 id만 모으면 충분하지 않나?" | run 진행률, 실패 분류, 안전한 재개 지점 설명이 비어 운영 대화가 꼬인다 |
| after: run/chunk/item 경계를 나눔 | "이번 run 영수증, 실패 backlog, 재개 지점 중 무엇이 필요한가?" | summary, retry queue, checkpoint를 상황별로 골라 batch 의미를 명확히 말할 수 있다 |

## 세 가지 정책 레벨

이 주제는 "retry를 할까 말까"가 아니라 보통 세 단계로 커진다.

| 레벨 | 중심 질문 | 핵심 산출물 |
|---|---|---|
| pure per-item retry | 실패 item만 다시 돌리면 끝나는가 | failed item ids |
| chunk summary + retry queue | 실패를 분류하고 main run과 분리해야 하는가 | chunk result, retry candidates |
| checkpoint + retry queue + summary | run 자체를 이어서 재개해야 하는가 | progress cursor, run/chunk summary, retry backlog |

처음부터 가장 무거운 정책을 넣을 필요는 없다.
하지만 run 의미가 생겼는데도 계속 per-item retry만 고집하면 운영 설명이 깨진다.

## 1. pure per-item retry면 충분한 경우

아래 조건이 맞으면 복잡한 batch 상태를 따로 저장하지 않아도 된다.

### item 간 결합이 약하다

- 한 건 실패가 다른 건 정합성을 바꾸지 않는다
- 처리 순서가 correctness를 크게 바꾸지 않는다
- 다시 실행해도 같은 item만 안전하게 재처리할 수 있다

### 전체를 다시 훑는 비용이 작다

- 대상 재조회가 싸다
- 실패 item만 다시 뽑아도 충분하다
- 처음부터 다시 돌아도 중복 부작용 위험이 낮다

### 운영자 설명도 item 단위로 끝난다

- "37번 메일만 다시 보내자" 정도면 충분하다
- run 전체의 공식 summary나 receipt가 필요 없다
- 실패 분류도 transient/permanent로 굳이 나누지 않아도 된다

예를 들면:

- 야간 안내 메일 재전송
- 만료 예정 쿠폰 알림
- 독립적인 캐시 warm-up 요청

이 경우 batch는 사실상 **같은 단건 작업을 많이 반복하는 편의 진입 채널**에 가깝다.

## 2. chunk summary와 retry queue가 필요한 경우

아래 신호가 보이면 "실패 item 재시도"만으로는 부족하다.

### chunk summary가 필요한 신호

- 운영자가 "이번 3번째 chunk는 500건 중 12건 실패"처럼 설명해야 한다
- downstream이나 감사 로그에 run/chunk 단위 집계가 남아야 한다
- 실패 원인을 transient, validation, partner-side rejection처럼 나눠야 한다

이때 summary는 관측성 부가 정보가 아니라 **운영 계약의 일부**가 된다.

### retry queue가 필요한 신호

- 실패 item을 바로 다시 돌리면 안 된다
- 데이터 보정이나 사람 검토 후 다시 처리해야 한다
- main run은 계속 끝내고, 실패분만 별도 backlog로 넘겨야 한다

즉 retry queue는 "실패했다"를 기록하는 곳이 아니라, **실패 item의 다음 처리 경로를 분리하는 곳**이다.

### 왜 둘이 같이 붙는가

chunk summary만 있고 retry queue가 없으면 실패분을 나중에 무엇으로 다시 볼지 약하다.
retry queue만 있고 summary가 없으면 이번 run이 어디서 얼마나 깨졌는지 설명이 약하다.

보통은 이렇게 같이 간다.

1. chunk 처리 후 성공/실패 집계를 summary로 남긴다.
2. 재시도 가능한 실패와 수동 확인이 필요한 실패를 나눈다.
3. main run 밖에서 다시 볼 item만 retry queue로 보낸다.

## 3. checkpoint까지 필요한 경우

checkpoint는 "실패 item만 다시 처리"와 다른 문제를 푼다.
핵심은 **main run 자체를 어디서 이어서 재개할 수 있는가**다.

아래 상황이면 checkpoint를 별도 정책으로 보는 편이 맞다.

### run 재시작 비용이 크다

- 대상이 수만~수십만 건이라 처음부터 재실행이 비싸다
- 외부 API rate limit이나 파일 생성 비용 때문에 전체 재시작이 부담스럽다
- 같은 run을 다시 처음부터 돌리면 중복 전송/중복 집계 위험이 커진다

### 진행 순서나 cursor가 correctness에 들어온다

- cutoff time 기준으로 고정한 대상 snapshot이 있다
- chunk 순서나 cursor 위치를 잃으면 누락/중복이 생긴다
- "4월 23일 오전 run의 7번째 chunk 이후부터" 같은 재개가 필요하다

### checkpoint가 retry queue를 대체하지는 않는다

이 부분을 많이 헷갈린다.

- checkpoint는 **main run의 진행 위치**
- retry queue는 **main run에서 분리된 실패 item backlog**

즉 checkpoint가 있어도, 일부 실패 item은 여전히 retry queue로 보내야 할 수 있다.
반대로 retry queue가 있어도, 긴 run은 checkpoint 없이 재개가 어렵다.

## 짧은 비교 표

| 질문 | pure per-item retry | chunk summary + retry queue | checkpoint까지 필요 |
|---|---|---|---|
| 운영자가 무엇을 설명하나 | 실패 item 몇 개 | chunk별 성공/실패와 후속 경로 | run 재개 지점과 남은 범위 |
| 장애 후 무엇을 저장하나 | failed item ids | chunk result, failed item classification | progress cursor, run snapshot, chunk result |
| 다시 실행 단위는 무엇인가 | item | item 또는 retry queue backlog | run cursor + selected retry items |
| 전체 재실행이 안전한가 | 대체로 예 | 점점 애매해진다 | 대체로 아니오 |
| 대표 예시 | 메일 재전송 | 파트너 동기화 실패 backlog | 월말 정산, 대용량 export/import |

## 예시: 같은 batch가 어떻게 커지는가

같은 종류의 batch도 규모와 운영 요구가 커지면 정책이 달라진다.

### 1단계: 실패 메일 재전송

- 사용자별 발송이 독립적이다
- 실패한 사용자만 다시 보내면 된다
- run summary나 checkpoint가 없어도 운영 설명이 된다

이 단계에서는 pure per-item retry면 충분하다.

### 2단계: 파트너 상품 동기화

- 500건씩 chunk로 묶어 외부 API를 호출한다
- 일부 item은 일시 장애, 일부는 잘못된 상품 코드 때문에 실패한다
- main run은 끝내고 잘못된 상품만 별도 재처리 backlog로 보내고 싶다

이 단계에서는 chunk summary와 retry queue가 필요하다.

### 3단계: 월말 정산 batch

- 대상이 매우 많고, cutoff 시점이 correctness에 들어온다
- 중간에 죽으면 처음부터 다시 돌리기 어렵다
- chunk 진행 위치와 실패 backlog를 분리해서 저장해야 한다

이 단계에서는 checkpoint까지 필요하다.

짧게 요약하면:

- 작고 독립적이면 per-item retry
- 실패 분류와 후속 경로가 필요하면 summary + queue
- run 자체를 이어 가야 하면 checkpoint 추가

## beginner practice loop

정책 문서를 읽고 바로 손을 움직이려면 아래 순서가 가장 짧다.

| 순서 | 먼저 볼 것 | 왜 이 순서가 beginner에게 쉬운가 |
|---|---|---|
| 1 | 이 문서에서 `per-item retry`, `retry queue`, `checkpoint`를 구분한다 | 어떤 실패를 어디로 보낼지 말로 설명할 수 있어야 한다 |
| 2 | [Primer On Retry Queue Assertions](./retry-queue-assertions-primer.md)에서 `retryable`, `manual review`, `terminal failure` assertion을 잠근다 | 실패 분류가 실제 테스트에서 어디로 보이는지 바로 확인할 수 있다 |
| 3 | [Batch Result Testing Checklist](./batch-result-testing-checklist.md)에서 `RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`를 함께 검증한다 | item 분류 테스트를 run/chunk 결과 검증으로 자연스럽게 넓힐 수 있다 |

짧게 기억하면 이렇다.

- 정책 primer는 "무엇을 나눌지"를 정한다.
- retry queue primer는 "실패를 어디로 보낼지"를 잠근다.
- batch result checklist는 "run 전체 영수증이 맞는지"를 확인한다.

## 흔한 오해와 함정

- "retry queue가 있으면 checkpoint는 필요 없다"
  - 아니다. retry queue는 실패 item의 후속 경로이고, checkpoint는 main run 재개 지점이다.
- "chunk summary는 로그만 잘 남기면 된다"
  - 아니다. 운영자와 downstream이 그 summary로 의사결정을 하면 이미 계약 일부다.
- "batch면 무조건 checkpoint를 둬야 한다"
  - 아니다. 전체 재실행이 싸고 안전하면 pure per-item retry가 더 단순하다.
- "checkpoint를 두면 멱등성은 덜 중요하다"
  - 아니다. 재개 중 중복 실행 가능성은 여전히 있으므로 item/run 단위 멱등성 설계가 필요하다.
- "복잡해 보이니 일단 `saveAll`이나 bulk SQL로 빨리 처리하면 된다"
  - 아니다. 실패 정책이 복잡해질수록 오히려 run/chunk/item 경계를 더 명시해야 한다.

## 기억할 기준

초심자용으로는 네 문장만 먼저 기억하면 된다.

1. **실패한 item만 다시 돌리면 설명이 끝난다면 pure per-item retry가 기본이다.**
2. **이번 chunk에서 무슨 일이 있었는지 남겨야 하면 chunk summary가 필요하다.**
3. **실패 item을 main run과 다른 속도로 다뤄야 하면 retry queue가 필요하다.**
4. **중간부터 안전하게 이어서 시작해야 하면 checkpoint가 필요하다.**

## 한 줄 정리

Batch partial failure 정책의 핵심은 "재시도 로직을 늘리는 것"이 아니라, run 영수증과 실패 backlog와 재개 지점을 언제 분리해야 하는지 먼저 구분하는 것이다.
