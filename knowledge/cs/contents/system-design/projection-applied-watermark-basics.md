---
schema_version: 3
title: Projection Applied Watermark Basics
concept_id: system-design/projection-applied-watermark-basics
canonical: true
category: system-design
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
review_feedback_tags:
- projection-applied-watermark
- applied-watermark
- projection-watermark
- required-watermark-vs
aliases:
- applied watermark
- projection watermark
- required watermark vs applied watermark
- read model checkpoint
- projection checkpoint
intents:
- definition
linked_paths:
- contents/system-design/read-after-write-routing-primer.md
- contents/design-pattern/read-model-staleness-read-your-writes.md
- contents/system-design/watermark-metadata-persistence-basics.md
- contents/system-design/outbox-watermark-token-primer.md
- contents/system-design/shard-aware-watermark-scope-primer.md
forbidden_neighbors:
- contents/security/session-cookie-jwt-basics.md
expected_queries:
- applied_watermark가 뭐야?
- required watermark랑 applied watermark는 어떻게 달라?
- read model이 어디까지 반영됐는지 어떻게 판단해?
- 방금 저장했는데 read model이 stale인지 watermark로 어떻게 봐?
contextual_chunk_prefix: |
  이 문서는 학습자가 원본이 어디까지 처리됐는지 표식만 두고 화면 데이터를
  갱신하는 방식 — applied watermark와 required watermark — 을 처음 잡는
  primer다. 어디까지 처리됐는지 표식, watermark 기반 갱신, read model
  checkpoint, projection 진행 기록 같은 자연어 paraphrase가 본 문서의
  표식 메커니즘에 매핑된다.
---
# Projection Applied Watermark Basics

> 한 줄 요약: `applied_watermark`는 "이 read model이 안전하게 반영을 끝낸 마지막 기준선"이고, projection은 이 값을 저장하고 조금씩 전진시키며, read path는 이 값을 밖으로 꺼내 `required_watermark`와 비교해 stale 여부를 단순하게 판단한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
- [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)
- [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)
- [Watermark Mismatch Fallback UX Primer](./watermark-mismatch-fallback-ux-primer.md)
- [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
- [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
- [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
- [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
- [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
- [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
- [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)
- [system design 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: projection applied watermark basics, applied watermark 뭐예요, read model watermark 뭐예요, required watermark vs applied watermark, read model 어디까지 반영됐나, 처음 배우는데 watermark, 처음 read model freshness 헷갈려요, 왜 방금 쓴 값이 stale 인가요, projection checkpoint 큰 그림, read model checkpoint basics, watermark 비교는 언제 쓰나요, cache hit 전에 watermark 왜 봐요, read-after-write watermark 기초, what is applied watermark, beginner watermark primer

---

## 먼저 잡을 mental model

초보자는 `applied_watermark`를 어렵게 생각하기 쉽다.
하지만 실제 뜻은 단순하다.

질문이 "`applied_watermark`가 뭐예요?", "왜 방금 저장했는데 read model은 아직 예전 값이죠?"라면 이 문서를 먼저 읽는 편이 맞다. cache refill 때 어떤 metadata를 같이 저장해야 하는지는 [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)로 바로 이어진다.

> "이 projection은 여기까지는 반영을 끝냈다"라고 적어 두는 체크포인트다.

예를 들어 주문 상세 read model이 있다고 하자.

- 방금 source transaction이 `required_watermark=9001`을 만들었다
- projector는 이벤트를 처리해서 read row를 갱신했다
- 그 뒤 `applied_watermark=9001`도 같이 저장했다

그러면 read path는 아래 한 줄만 보면 된다.

- `applied_watermark < required_watermark`면 아직 덜 따라왔다
- `applied_watermark >= required_watermark`면 최소 그 변경 이후 상태다

즉 `required_watermark`가 "어디까지 와야 하나"라면,
`applied_watermark`는 "지금 어디까지 왔나"다.

## 한눈에 보기

| 단계 | 누가 갖고 있나 | 값 예시 | 초보자용 질문 |
|---|---|---|---|
| source commit | outbox/event | `required_watermark=9001` | "read model이 최소 어디까지 와야 하나?" |
| projection apply 전 | projector | `current applied_watermark=8998` | "아직 모자란가?" |
| projection apply 후 | read model | `applied_watermark=9001` | "이제 그 변경을 반영했나?" |
| read request | API/BFF/cache gate | `9001 <= 9001` | "이 결과를 그대로 보여 줘도 되나?" |

```text
source commit -> required_watermark=9001
projection catches up -> applied_watermark=8998 -> 9001
read request compares -> required <= applied ?
```

## 왜 read model이 이 값을 직접 저장해야 하나

`required_watermark`만 있고 read model 쪽 기록이 없으면 비교가 끝나지 않는다.

예를 들어 event payload에 `required_watermark=9001`이 있어도,
주문 상세 projection이 지금 `8998`인지 `9001`인지 모르면 read path는 stale 여부를 알 수 없다.

그래서 read side에는 보통 아래 둘이 같이 필요하다.

- event/source가 주는 `required_watermark`
- projection이 남기는 `applied_watermark`

둘을 붙이면 복잡한 질문이 단순해진다.

- "이 row가 최신인가?" 대신
- "이 projection이 9001까지 따라왔는가?"를 묻는다

## 어디에 저장하나

beginner 단계에서는 저장 위치를 너무 복잡하게 잡지 않는 편이 낫다.

| 저장 위치 | 예시 | 언제 쉬운가 | 주의할 점 |
|---|---|---|---|
| projection row 안 | `orders_read.applied_watermark=9001` | 단건 상세 row가 분명할 때 | row마다 갱신해야 한다 |
| projection metadata table | `projection_checkpoint(order_detail)=9001` | projection 전체 tail을 볼 때 | 전체 checkpoint와 개별 row freshness를 혼동하지 말아야 한다 |
| partition별 checkpoint | `order_detail:p3 -> 9001` | shard/partition 단위 projector일 때 | 다른 partition 값끼리 직접 비교하면 안 된다 |

처음에는 이렇게 기억하면 된다.

- "이 row가 직접 최신선이 필요한가?" 그러면 row 안에 둔다
- "projection consumer가 어디까지 먹었는지 보면 되나?" 그러면 checkpoint table도 괜찮다
- shard나 partition마다 숫자 범위가 따로 돈다면, `applied_watermark`도 숫자만 저장하지 말고 scope와 같이 저장해야 한다. 이 비교 범위를 따로 설명한 문서는 [Shard-Aware Watermark Scope Primer](./shard-aware-watermark-scope-primer.md)다.

## 어떻게 전진하나

핵심은 `applied_watermark`가 **반영이 끝난 뒤에만** 올라가야 한다는 점이다.

나쁜 순서:

1. watermark부터 `9001`로 올린다
2. read row 저장은 아직 안 끝났다
3. 읽는 쪽은 이미 반영된 줄 안다

좋은 순서:

1. 이벤트를 적용해 read row를 갱신한다
2. 같은 원자적 경계 안에서 `applied_watermark=9001`을 저장한다
3. 그다음부터 read path가 `9001`을 믿는다

짧게 말하면:

> "적용 완료 표시"여야지 "곧 적용 예정 표시"가 아니어야 한다.

## 가장 작은 예시

주문 상세 projection을 단순화하면 이런 흐름이다.

```text
event:
- order_id=123
- status=PAID
- required_watermark=9001

before apply:
- orders_read[123].status=PENDING
- orders_read[123].applied_watermark=8998

after apply:
- orders_read[123].status=PAID
- orders_read[123].applied_watermark=9001
```

그 뒤 API는 이렇게 판단할 수 있다.

```pseudo
row = orderReadRepository.find(orderId)

if row.appliedWatermark < requiredWatermark:
  return fallback_or_wait()

return row
```

초보자에게 중요한 점은, status 값을 눈으로 비교하지 않아도
`8998 < 9001` 한 줄이면 stale 가능성을 먼저 분리할 수 있다는 것이다.

## `ack position`과 `applied_watermark`를 섞지 말자

여기서 흔한 혼동이 나온다.

| 값 | 뜻 | 왜 다른가 |
|---|---|---|
| broker ack / consumer offset | "메시지를 받았다고 표시한 위치" | 처리 완료 전에 움직일 수 있다 |
| `applied_watermark` | "read model 반영까지 끝낸 위치" | 읽기 결과를 믿는 기준선이다 |

즉 consumer가 어떤 offset을 commit했다고 해서,
사용자에게 보여 주는 projection도 그만큼 최신이라고 바로 말할 수는 없다.

beginner 문장으로 줄이면 이렇다.

- `ack`: "받았다"
- `applied_watermark`: "반영 끝났다"

## 밖으로 어떻게 노출하나

`applied_watermark`는 DB 안에만 있으면 반쪽짜리다.
읽는 쪽이 비교할 수 있게 surface에도 나와야 한다.
특히 safe read 뒤 cache refill이 있다면, 이 값을 cache entry metadata로 같이 저장해야 다음 hit에서 causal accept 검사를 다시 할 수 있다. 이 연결을 beginner 관점으로 푼 문서는 [Watermark Metadata Persistence Basics](./watermark-metadata-persistence-basics.md)다.

가장 단순한 노출 위치는 아래 셋이다.

| 노출 위치 | 예시 | 용도 |
|---|---|---|
| API response metadata | `observed_watermark=9001` | BFF/client가 다음 판단에 사용 |
| cache entry metadata | `cache.applied_watermark=9001` | stale cache hit reject |
| observability/log | `required=9001, applied=8998` | 왜 fallback됐는지 설명 |

이 값을 무조건 사용자 화면에 직접 보여 주라는 뜻은 아니다.
핵심은 **시스템 경계 밖으로 비교 가능한 형태로 꺼내 둔다**는 점이다.

## 초보자가 먼저 기억할 운영 질문

운영에서는 이 세 질문이 가장 먼저 나온다.

1. projector가 지금 어디까지 따라왔나
2. fallback된 요청은 `required > applied`였나
3. watermark mismatch가 특정 projection, partition, cache path에 몰리나

그래서 최소한 아래 신호는 있으면 좋다.

- `required_watermark`
- `applied_watermark`
- `fallback_reason=watermark`
- `projection_name`
- `partition_key` 또는 `aggregate_key`

이 정도만 있어도 "왜 stale했나"를 말로가 아니라 숫자로 설명하기 쉬워진다.

## 자주 나오는 오해

- `applied_watermark`가 있으면 값 전체가 완벽히 최신이다
  - 과장이다. 이 값은 최소 기준선 비교를 단순하게 해 주는 장치다.
- projection 전체 checkpoint 하나만 있으면 모든 row freshness를 설명할 수 있다
  - 단건 row freshness와 consumer tail checkpoint는 다를 수 있다.
- watermark는 timestamp로만 만들면 된다
  - clock 기준은 ordering 설명력이 약할 수 있다. 가능한 monotonic sequence 쪽이 낫다.
- `applied_watermark`는 이벤트를 읽자마자 올려도 된다
  - 안 된다. read model 반영 완료 후에 올라가야 한다.
- offset commit과 `applied_watermark`는 같은 뜻이다
  - 다르다. 하나는 소비 위치, 다른 하나는 projection 반영 완료 위치다.

## 30초 체크리스트

- source/event가 `required_watermark`를 주는가
- projection이 자기 `applied_watermark`를 저장하는가
- watermark는 반영 완료 뒤에만 전진하는가
- read path가 `required <= applied`를 실제로 검사하는가
- mismatch 시 fallback, wait, placeholder 중 하나가 정해져 있는가
- log/metric에 `required`와 `applied`가 같이 남는가

## 한 줄 정리

`applied_watermark`는 read model이 "여기까지는 안전하게 반영했다"라고 선언하는 체크포인트이고, 이 값을 저장하고 전진시키고 노출해야 `required_watermark`와의 비교로 stale read를 초보자도 단순하게 설명할 수 있다.
