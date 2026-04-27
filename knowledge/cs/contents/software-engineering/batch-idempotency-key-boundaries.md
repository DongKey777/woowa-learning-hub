# Batch Idempotency Key Boundaries

> 한 줄 요약: retry-safe batch recovery는 "한 item의 중복", "한 chunk의 중복", "한 run의 중복"을 같은 key 하나로 뭉치지 않고 서로 다른 idempotency 경계로 나눌 때 안전해진다.

**난이도: 🟢 Beginner**

[Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)에서 retry queue, chunk summary, checkpoint를 봤다면, 이 문서는 그다음 질문인 "재시도할 때 어떤 idempotency key를 써야 하는가"만 좁혀서 본다.
`RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint` 같은 결과 이름은 [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)를 같이 보면 된다.
이 key 경계를 operator의 rerun 판단과 runbook 절차로 연결해 보고 싶다면 [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)를 이어서 보면 된다.
멱등성과 consistency boundary 자체를 깊게 보려면 [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)로 이어서 내려가면 된다.

<details>
<summary>Table of Contents</summary>

- [왜 이 primer가 필요한가](#왜-이-primer가-필요한가)
- [먼저 한 장면으로 이해하기](#먼저-한-장면으로-이해하기)
- [세 key는 서로 다른 질문에 답한다](#세-key는-서로-다른-질문에-답한다)
- [예시: 상품 동기화 batch](#예시-상품-동기화-batch)
- [retry 흐름에서 함께 쓰는 방법](#retry-흐름에서-함께-쓰는-방법)
- [자주 하는 오해](#자주-하는-오해)
- [PR 전 체크리스트](#pr-전-체크리스트)
- [기억할 기준](#기억할-기준)

</details>

> 관련 문서:
> - [Software Engineering README: Batch Idempotency Key Boundaries](./README.md#batch-idempotency-key-boundaries)
> - [Batch Partial Failure Policies Primer](./batch-partial-failure-policies-primer.md)
> - [Batch Run Result Modeling Examples](./batch-run-result-modeling-examples.md)
> - [Batch Recovery Runbook Bridge](./batch-recovery-runbook-bridge.md)
> - [True Bulk Contracts and Partial Failure Results](./true-bulk-contracts-partial-failure-results.md)
> - [Batch Job Scope In Hexagonal Architecture](./batch-job-scope-hexagonal-architecture.md)
> - [Idempotency, Retry, Consistency Boundaries](./idempotency-retry-consistency-boundaries.md)
> - [Domain Events, Outbox, Inbox](./outbox-inbox-domain-events.md)
> - [Webhook and Broker Boundary Primer](./webhook-and-broker-boundary-primer.md)
>
> retrieval-anchor-keywords:
> - batch idempotency key boundaries
> - item-level idempotency key
> - chunk-level idempotency key
> - run-level idempotency key
> - retry-safe batch recovery
> - duplicate-safe batch rerun
> - batch idempotency key beginner
> - run id vs chunk id vs item id
> - checkpoint resume idempotency
> - chunk retry idempotency
> - per-item retry idempotency key
> - batch recovery dedup boundary
> - idempotency key scope beginner
> - partial failure idempotency
> - batch run duplicate suppression
> - batch recovery runbook bridge

## 왜 이 primer가 필요한가

batch는 실패 후 다시 실행되는 일이 많다.
서버가 죽고, 외부 API가 timeout되고, operator가 같은 run을 다시 누르고, 실패 item만 retry queue에서 다시 소비될 수 있다.

이때 필요한 질문은 하나다.

- **이 요청은 이미 처리한 같은 일인가, 아니면 새 일인가?**

문제는 "같은 일"의 범위가 하나가 아니라는 점이다.
상품 1,200개를 동기화하는 batch에서 같은 말은 세 수준으로 갈라진다.

- 같은 상품 한 건을 다시 보내는가
- 같은 300건 chunk를 다시 보내는가
- 같은 09:00 snapshot run을 다시 시작하는가

이 세 질문을 key 하나로 해결하려고 하면 너무 넓거나 너무 좁아진다.
그래서 beginner batch 설계에서는 item-level, chunk-level, run-level key를 먼저 분리해서 생각하는 편이 안전하다.

## 먼저 한 장면으로 이해하기

idempotency key는 "다시 왔을 때 같은 일인지 판단하는 이름표"다.
batch에서는 이름표를 붙이는 상자가 세 개 있다.

| 상자 | 쉬운 말 | key가 막아 주는 중복 |
|---|---|---|
| item | 한 건의 부작용 | 같은 주문 생성, 같은 알림 발송, 같은 상품 전송이 두 번 일어나는 것 |
| chunk | 작은 묶음 하나 | 같은 300건 묶음을 timeout 때문에 다시 제출하면서 chunk receipt가 두 번 생기는 것 |
| run | 전체 실행 | 같은 snapshot batch를 operator나 scheduler가 두 번 시작하는 것 |

핵심은 "상위 key가 하위 key를 자동으로 대신하지 않는다"는 점이다.
run key는 같은 run을 두 번 시작하지 않게 도와주지만, 이미 시작된 run 안에서 item 491번이 두 번 전송되는 문제까지 자동으로 막지는 않는다.
chunk key도 chunk receipt를 보호하지만, chunk 중간에서 150건만 성공한 뒤 죽은 경우에는 item key가 있어야 나머지를 안전하게 이어 갈 수 있다.

## 세 key는 서로 다른 질문에 답한다

| key 수준 | 답하는 질문 | 보통 key에 들어가는 것 | 저장하는 결과 | 못 답하는 질문 |
|---|---|---|---|---|
| item-level | "이 item의 이 부작용은 이미 끝났나?" | job name, tenant/partner, item id, version 또는 snapshot 기준 | 성공 결과, 외부 receipt, 실패 분류 | chunk 전체가 어디까지 끝났는가 |
| chunk-level | "이 묶음은 이미 제출/완료됐나?" | run key, chunk number, cursor range 또는 chunk hash | `ChunkResult`, accepted receipt, chunk status | chunk 안의 각 item이 모두 안전한가 |
| run-level | "이 batch 실행은 이미 시작/완료됐나?" | job name, tenant/partner, snapshot time, backfill range | `RunSummary`, run status, latest checkpoint | 특정 item 중복 부작용이 막혔는가 |

item key는 가장 작은 부작용을 지킨다.
chunk key는 묶음 단위 receipt와 checkpoint를 지킨다.
run key는 전체 실행의 중복 시작과 운영 보고를 지킨다.

서로 겹쳐 보이지만 보호하는 실패가 다르다.
그래서 중요한 batch에서는 보통 세 key가 같이 나온다.

## 예시: 상품 동기화 batch

상황을 하나로 고정해 보자.

- job: partner product sync
- 대상: 2026-04-23 09:00 snapshot의 상품 1,200개
- chunk size: 300개
- 외부 시스템: partner catalog API

이때 key는 이런 식으로 나눌 수 있다.

```text
runKey
- product-sync:partner-a:2026-04-23T09:00Z

chunkKey
- product-sync:partner-a:2026-04-23T09:00Z:chunk:002

itemKey
- product-sync:partner-a:product-491:version-17
```

항상 이 문자열 모양을 써야 한다는 뜻은 아니다.
중요한 것은 key가 "같은 일"을 정확히 설명해야 한다는 점이다.

예를 들어 `product-491`만 item key로 쓰면 나중에 상품이 수정된 뒤 새 버전을 동기화해야 할 때도 중복으로 오해할 수 있다.
반대로 매 retry마다 random UUID를 새로 만들면 같은 요청인지 알 수 없어 중복 전송을 막지 못한다.
같은 의도의 retry는 같은 key를 써야 하고, 다른 의도의 새 처리는 다른 key가 되어야 한다.

## retry 흐름에서 함께 쓰는 방법

안전한 recovery 흐름은 보통 아래 순서로 읽으면 된다.

1. run을 시작할 때 run-level key로 같은 snapshot run이 이미 있는지 확인한다.
2. candidate snapshot을 고정하고 chunk를 나눈 뒤 chunk-level key를 만든다.
3. chunk 안에서는 각 item 처리 전에 item-level key로 이미 처리된 부작용인지 확인한다.
4. item 결과를 durable하게 남긴 뒤 `ChunkResult`와 checkpoint를 갱신한다.
5. 실패 item을 retry queue로 보낼 때는 같은 item-level key와 실패 이유를 같이 넘긴다.
6. 같은 run을 resume하면 run key와 checkpoint로 위치를 찾고, chunk/item key로 중복 부작용을 피한다.

중간 장애를 예로 들면 더 선명하다.

| 장애 장면 | 필요한 key | 이유 |
|---|---|---|
| operator가 같은 09:00 run을 다시 누름 | run-level | 같은 snapshot run의 중복 시작을 막는다 |
| partner API timeout 후 chunk 2를 다시 제출함 | chunk-level + item-level | chunk receipt 중복과 item 부작용 중복을 같이 막아야 한다 |
| chunk 2에서 150건 성공 후 서버가 죽음 | item-level + checkpoint | 이미 성공한 150건은 건너뛰고 남은 위치를 이어야 한다 |
| 실패 item 9건만 retry queue에서 재처리함 | item-level | main run 밖 retry도 같은 부작용인지 판단해야 한다 |

chunk key만 믿고 chunk를 너무 일찍 `completed`로 표시하면 위험하다.
반대로 item key만 있고 checkpoint가 없으면 중복 부작용은 줄어도 "run을 어디서 이어야 하는가"를 설명하기 어렵다.

## 자주 하는 오해

| 오해 | 더 안전한 판단 |
|---|---|
| run id가 있으면 item idempotency는 필요 없다 | run 중간 partial success는 item key 없이는 안전하게 복구하기 어렵다 |
| chunk key가 있으면 chunk 안 item은 자동으로 안전하다 | chunk가 부분 성공했을 때는 item별 완료 기록이 필요하다 |
| item id 자체가 항상 idempotency key다 | 같은 item이라도 version, snapshot, operation이 다르면 새 일일 수 있다 |
| retry할 때마다 key를 새로 만들면 충돌이 없다 | 새 key는 duplicate suppression을 깨뜨린다 |
| idempotency key는 로그에만 남기면 된다 | 재시도 판단에 쓰려면 durable store나 inbox처럼 조회 가능한 경계에 남아야 한다 |
| 모든 key를 영원히 보관해야 한다 | retry window와 감사 요구에 맞춰 보관 기간을 정하되, 너무 빨리 지우면 늦은 retry가 중복을 만든다 |

## PR 전 체크리스트

- run key가 job name, tenant/partner, snapshot time, backfill range처럼 "같은 실행"을 구분할 정보를 담는가?
- chunk key가 run key와 chunk number 또는 cursor range를 포함해 "같은 묶음"을 설명하는가?
- item key가 item id뿐 아니라 operation, version, snapshot 중 필요한 축을 포함하는가?
- 같은 retry는 같은 key를 재사용하고, 새 business intent는 새 key가 되는가?
- key 저장과 실제 부작용 결과가 함께 설명되어 timeout 후 재시도해도 이전 결과를 찾을 수 있는가?
- `RunSummary`, `ChunkResult`, `RetryCandidate`, `Checkpoint`가 서로 다른 질문을 섞지 않는가?

## 기억할 기준

batch idempotency key를 고를 때는 먼저 key 이름을 짓지 말고 질문을 나눠야 한다.

- item-level key: "이 한 건의 부작용은 이미 끝났나?"
- chunk-level key: "이 묶음의 제출/결과는 이미 기록됐나?"
- run-level key: "이 전체 실행은 이미 시작됐거나 완료됐나?"

retry-safe batch recovery는 세 질문을 같은 저장소나 같은 타입으로 구현하라는 뜻이 아니다.
세 질문을 **서로 다른 경계로 설명할 수 있어야 한다**는 뜻이다.
