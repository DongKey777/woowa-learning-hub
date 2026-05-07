---
schema_version: 3
title: Bitmap Locality Remediation Playbook
concept_id: data-structure/bitmap-locality-remediation
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- bitmap-locality-remediation
- roaring-hotspot-action
- row-ordering-compaction-remap
aliases:
- bitmap locality remediation
- roaring hotspot remediation
- bitmap hotspot playbook
- row ordering fix bitmap
- ID remapping bitmap
- runOptimize scheduling
- bitmap compaction remediation
symptoms:
- profiling에서 bitmap hotspot은 보였지만 row ordering, compaction, ID remapping, runOptimize 중 무엇부터 바꿀지 모른다
- container threshold나 runOptimize만 조정하면 locality 문제가 해결될 것이라고 보고 row-ID 배치 구조를 놓친다
- late-arriving rows와 tombstone이 만든 drift인지 전체 ID layout 문제인지 분리하지 못한다
intents:
- troubleshooting
- design
prerequisites:
- data-structure/roaring-production-profiling-checklist
- data-structure/roaring-run-churn-observability-guide
next_docs:
- data-structure/row-ordering-and-bitmap-compression-playbook
- data-structure/late-arriving-rows-and-bitmap-maintenance
- data-structure/warehouse-sort-key-co-design-for-bitmap-indexes
- data-structure/roaring-run-optimize-timing-guide
linked_paths:
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/late-arriving-rows-and-bitmap-maintenance.md
- contents/data-structure/warehouse-sort-key-co-design-for-bitmap-indexes.md
- contents/data-structure/roaring-run-optimize-timing-guide.md
- contents/data-structure/bit-sliced-bitmap-sort-key-sensitivity.md
confusable_with:
- data-structure/roaring-production-profiling-checklist
- data-structure/roaring-run-churn-observability-guide
- data-structure/row-ordering-and-bitmap-compression-playbook
- data-structure/roaring-run-optimize-timing-guide
forbidden_neighbors: []
expected_queries:
- Roaring bitmap hotspot이 잡힌 뒤 row ordering compaction remapping runOptimize 중 무엇부터 봐야 해?
- bitmap locality 문제에서 container threshold보다 row-ID 배치를 먼저 봐야 하는 이유는?
- late arriving rows와 tombstone이 bitmap run을 깨뜨릴 때 어떻게 remediation 해?
- runOptimize를 hot path에서 바로 호출하면 왜 위험할 수 있어?
- profiling 신호를 bitmap layout 변경 액션으로 번역하는 방법을 알려줘
contextual_chunk_prefix: |
  이 문서는 bitmap hotspot profiling 이후 실제 remediation 액션을 고르는
  playbook이다. row ordering, batch compaction, ID remapping, runOptimize
  scheduling을 같은 튜닝으로 보지 않고, row-ID 배치 구조와 lifecycle
  boundary를 먼저 바로잡는 순서를 설명한다.
---
# Bitmap Locality Remediation Playbook

> 한 줄 요약: profiling으로 bitmap hotspot이 잡힌 뒤에는 container 임계값보다 먼저 `row ordering`, `batch compaction`, `ID remapping`, `runOptimize()` handoff 시점을 workload lifecycle에 맞게 바로잡아야 locality가 실제로 회복된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Late-Arriving Rows and Bitmap Maintenance](./late-arriving-rows-and-bitmap-maintenance.md)
> - [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Bit-Sliced Bitmap Sort-Key Sensitivity](./bit-sliced-bitmap-sort-key-sensitivity.md)

> retrieval-anchor-keywords: bitmap locality remediation, bitmap hotspot remediation, roaring hotspot remediation, profiling to action bitmap, bitmap locality playbook, row ordering fix bitmap, batch compaction bitmap, bitmap recluster playbook, id remapping bitmap, surrogate id remap roaring, active chunk spread remediation, high key spread fix, run fragmentation remediation, runOptimize scheduling tradeoff, query result runOptimize scheduling, cold path optimize bitmap, hot tier bitmap compaction, sorted ingest recovery, bitmap performance tuning, roaring locality recovery, bitmap maintenance remediation

## 핵심 개념

profiling은 "어디가 느린가"를 알려 주지만,  
바로 다음 질문은 늘 "무엇을 바꿔야 하는가"다.

bitmap locality 문제는 보통 아래 네 레버 중 하나로 고친다.

- `row ordering`: bit가 어느 row ID band에 놓이는지 바꾼다
- `batch compaction`: 최근 delta와 tombstone이 만든 drift를 다시 접는다
- `ID remapping`: 내부 row ID 기하 자체가 틀어진 경우 재배치한다
- `runOptimize()` scheduling: shape가 굳은 뒤에만 압축 비용을 낸다

중요한 점은 이 네 가지가 같은 층위의 튜닝이 아니라는 것이다.

- row ordering과 ID remapping은 **ID 배치 구조**를 바꾼다
- batch compaction은 **최근 손상**을 복구한다
- `runOptimize()`는 이미 좋아진 shape에서 **압축 이득을 회수**한다

즉 hotspot 대응 순서는 대개 "`shape를 먼저 고치고`, `압축은 나중에 굳힌다`"가 맞다.

## 1. profiling 신호를 액션으로 번역한다

먼저 [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)와 [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)에서 본 신호를 구조 변경으로 번역해야 한다.

| profiling 신호 | 실제로 깨진 것 | 먼저 바꿀 것 | 그다음 판단 |
|---|---|---|---|
| `active_chunks`, `distinct_high_keys_touched`는 오르는데 global cardinality는 비슷하다 | hit가 더 넓은 row-ID band로 퍼졌다 | row ordering, sort key, ingest 정렬 | 손상이 최신 구간만이면 compaction, 역사 전반이면 remap/rebuild |
| `3584..4608` bucket과 `array <-> bitmap` flip이 같은 chunk에 몰린다 | 경계 근처 chunk가 작은 batch에 흔들린다 | update/delete batching, mutable tier compact | hot path `runOptimize()` 제거 여부 확인 |
| `runs p95`는 오르고 `avg_run_length`와 optimize payoff는 떨어진다 | delete/revoke가 run을 잘게 쪼갠다 | batch compaction, tombstone fold-in | 반복 compact에도 회복이 없으면 ID 배치 구조 재검토 |
| `phase=query_result|repair`에서만 CPU가 오른다 | persisted bitmap보다 intermediate result가 churn한다 | filter ordering, reusable result cache, materialize 경계만 optimize | storage layout보다 query plan 문제인지 분리 |
| 같은 `high_key` band가 오랫동안 top hotspot으로 남고 compact 이득이 작다 | 내부 ID 배치 자체가 workload와 안 맞다 | ID remapping 또는 rebuild | 새 sort/order 전략 없이 remap만 하면 재발하기 쉽다 |

핵심은 "`threshold를 더 잘 고르면 되나?`"를 마지막에 묻는 것이다.  
대부분의 운영 hotspot은 threshold보다 **row-ID 배치 구조**와 **lifecycle boundary**에서 먼저 갈린다.

## 2. spread 문제면 row ordering부터 고친다

profiling에서 제일 먼저 봐야 할 것은 "hit 수"보다 "**더 많은 chunk를 만지기 시작했는가**"다.

아래 패턴이면 row ordering drift를 먼저 의심하는 편이 맞다.

- global cardinality는 비슷한데 active chunk 수만 오른다
- full chunk 비중은 줄고 near-full/medium chunk가 늘어난다
- query가 더 많은 segment와 row group을 건드린다
- run 수 tail과 `distinct_high_keys_touched`가 같이 오른다

이 경우 `array/bitmap/run` heuristic을 만지는 것보다,  
[Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)와 [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md) 관점에서 **입력 배치 순서**를 바로잡는 쪽이 먼저다.

### 먼저 시도할 변화

| 변화 | 언제 효과가 큰가 | 주의점 |
|---|---|---|
| 자주 필터되는 low-cardinality 차원 기준으로 micro-batch를 정렬 | hotspot이 최신 ingest 구간에 몰릴 때 | freshness 지연과 ingest CPU를 같이 본다 |
| compaction window 안에서 `(dimension, time)` 같은 복합 키로 재정렬 | query가 차원 필터와 시간 필터를 함께 쓸 때 | 시간 pruning만 보던 설계가 흔들릴 수 있다 |
| row-group/segment 크기를 키워 band reset을 줄임 | 같은 값이 작은 segment에 잘게 흩어질 때 | pruning granularity가 너무 거칠어질 수 있다 |
| hot mutable tail과 cold sorted base를 분리 | 최신 delta만 locality를 깨뜨릴 때 | merge-on-read 비용 상한을 같이 둬야 한다 |

여기서 중요한 trade-off는 단순하지 않다.

- 시간 우선 정렬이 append엔 편해도 bitmap locality엔 불리할 수 있다
- 너무 작은 segment는 pruning은 좋아도 bitmap run을 계속 리셋한다
- BSI까지 쓰는 시스템이면 sort key가 exact bitmap band뿐 아니라 bit-slice prefix locality도 같이 흔든다

즉 row ordering 변경은 "압축률 상승"만이 아니라,  
**어떤 predicate가 같은 ID band를 오래 점유하도록 만들 것인가**를 다시 정하는 작업이다.

## 3. batch compaction은 최근 drift를 접는 수단이다

[Late-Arriving Rows and Bitmap Maintenance](./late-arriving-rows-and-bitmap-maintenance.md)에서 보듯, compact는 bytes 회수보다 **delta/tombstone이 만든 locality 손상을 다시 접는 작업**에 가깝다.

아래 상황에서는 compaction이 첫 번째 remedial action이 되기 쉽다.

- late-arriving row나 revoke가 최신 partition에 집중된다
- delete bitmap이 hot query path에서 계속 `AND NOT` 비용을 만든다
- build 직후에는 좋았지만 운영 몇 시간/며칠 안에만 빠르게 나빠진다
- compact 직후 `active_chunks`, `runs`, bytes가 다시 좋아진 경험이 있다

### compaction이 실제로 해야 할 일

- delta row를 base ordering 근처로 다시 붙인다
- tombstone/delete 예외층을 base bitmap에 접어 넣는다
- 작은 segment를 합쳐 row-group reset 횟수를 줄인다
- compact 후 seal되는 시점에만 `runOptimize()` 후보를 만든다

### compaction 주기 trade-off

| 주기/범위 | 장점 | 위험 |
|---|---|---|
| 너무 잦은 소형 compact | hotspot을 빨리 누른다 | 같은 chunk를 반복 재작성하고 optimize 비용도 중복된다 |
| 적당한 batch compact | 최신 drift를 hot tier 바깥으로 밀어낸다 | window 설정이 workload와 어긋나면 이득이 약해진다 |
| 너무 드문 대형 compact | write path는 가볍다 | delta가 query 본체가 되어 locality 손실이 오래 지속된다 |

compact가 잘 먹는다는 뜻은 "`현재 정렬 전략은 여전히 맞다`"는 뜻이다.  
반대로 compact를 반복해도 `active chunk spread`가 역사 구간 전반에 남는다면, 문제는 유지보수 주기보다 **ID 배치 구조**일 가능성이 크다.

## 4. ID remapping은 ID 배치 구조가 틀렸을 때만 쓴다

ID remapping은 가장 비싸지만 가장 구조적인 레버다.  
이것이 필요한 상황은 보통 "hotspot이 최근 drift가 아니라, 기존 surrogate ID 배치 자체에 새겨져 있다"일 때다.

아래 패턴이면 remap 검토 가치가 높다.

- compact 전후로 hotspot `high_key` 대역이 거의 그대로 남는다
- 새 sort key나 clustering 전략은 분명한데 과거 ID 배치가 이를 반영하지 못한다
- 같은 predicate band가 segment마다 엇갈린 ID 구간으로 퍼져 있다
- active chunk 수와 seam 수가 구조적으로 높고, 최근 batch만 고쳐도 회복되지 않는다

### remap이 주는 것

- 같은 predicate hit를 더 적은 `high_key` 대역으로 모을 수 있다
- chunk boundary seam과 active container 수를 함께 줄일 수 있다
- compaction만으로는 못 만들던 긴 band locality를 회복할 수 있다

### remap 전에 확인할 것

| 질문 | 이유 |
|---|---|
| 외부 식별자와 내부 posting ID를 분리할 수 있는가 | remap은 보통 internal ID 공간에서만 안전하다 |
| 캐시/머티리얼라이즈드 bitmap에 mapping version을 붙일 수 있는가 | cutover 중 stale bitmap 재사용을 막아야 한다 |
| segment 단위 순차 remap이 가능한가 | 전체 재작성보다 단계적 전환이 안전하다 |
| 새 ordering을 앞으로도 유지할 ingest 경로가 있는가 | upstream이 그대로면 remap 이득이 금방 깨진다 |

remap은 hot path fix가 아니다.  
보통은 rebuild, cold-tier rewrite, 큰 compact epoch 같은 **명확한 lifecycle 경계**에서만 한다.

## 5. `runOptimize()`는 치료제가 아니라 handoff 정책이다

[Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md) 관점에서, `runOptimize()`는 locality를 "만드는" 연산이 아니라 **이미 좋아진 locality를 serialize/cache handoff에서 회수하는 연산**이다.

그래서 profiling 뒤에 흔히 하는 실수는 두 가지다.

- hotspot을 보고 `runOptimize()` 호출을 everywhere로 늘린다
- optimize 이득이 줄었다고 locality 문제를 무시한다

둘 다 틀리기 쉽다.  
질문은 "`runOptimize()`가 hotspot을 고치나?"가 아니라,  
"**어느 경계에서 한번만 호출해야 CPU를 회수하나?**"다.

| 위치 | 보통 선택 | 이유 |
|---|---|---|
| mutable ingest batch마다 | 대개 아니오 | 다음 batch가 run shape를 다시 깰 가능성이 높다 |
| compact/recluster 후 cold segment seal 직전 | 자주 예 | shape가 굳고 serialize/mmap/caching 이득이 남는다 |
| ID remap/rebuild 완료 직후 | 예 | ID 배치 구조를 바꾼 뒤 최종 표현을 한번 정리할 가치가 크다 |
| one-shot query result 직후 | 대개 아니오 | 소비자가 하나뿐이면 optimize CPU를 회수하기 어렵다 |
| cache/materialize/spill할 query result handoff | 자주 예 | reusable artifact라면 compression 이득이 여러 번 재사용된다 |
| lazy OR 결과 | 먼저 `repairAfterLazy()`, 그다음 상황별 optimize | correctness 경계와 compression 경계를 섞으면 안 된다 |

실전 판단은 아래 두 값을 함께 보는 편이 좋다.

- `bytes_saved_by_runOptimize / cpu_ns`
- 동일 `high_key`가 optimize 직후 다시 `run -> bitmap`으로 돌아오는 빈도

즉 optimize hotspot이 보이면 "optimize를 아예 끈다"보다,  
**hot path에서 cold handoff로 옮긴다**가 더 자주 맞다.

## 6. 권장 remediation 순서

대부분의 bitmap locality 이슈는 아래 순서가 가장 덜 헛돈다.

1. hotspot이 `build`, `update`, `query_result`, `repair` 중 어디서 생기는지 다시 고정한다.
2. spread가 문제면 row ordering과 sort key를 먼저 본다.
3. 손상이 hot tail에 몰리면 batch compaction으로 delta/tombstone을 접는다.
4. compact 이득이 사라지고 역사 전반에 hotspot이 남으면 ID remap/rebuild를 검토한다.
5. shape가 굳은 handoff 경계에서만 `runOptimize()`를 건다.
6. 같은 dashboard에서 `active_chunks`, `runs`, boundary pressure, optimize payoff가 실제로 회복됐는지 다시 본다.

이 순서를 거꾸로 하면 흔히 아래처럼 된다.

- `runOptimize()`를 자주 호출하지만 active chunk spread는 그대로다
- compact는 계속 도는데 surrogate ID 배치 구조 문제는 남는다
- row ordering은 그대로인데 `4096` 경계 churn만 heuristic으로 누르려다 재발한다

## 실전 시나리오

### 시나리오 1: late revoke가 많은 audience bitmap

`run -> bitmap` churn과 `3584..4608` bucket이 최근 mutable tier에 몰린다면:

- revoke/delete를 band-aware batch로 묶고
- tombstone을 자주 compact해 cold base에 접어 넣고
- `runOptimize()`는 compact seal 이후에만 건다

hot update 경로마다 optimize를 넣는 것은 대개 역효과다.

### 시나리오 2: 시간 우선 warehouse에서 국가 필터가 느려진 경우

global cardinality는 비슷한데 `country=KR` bitmap의 active chunk 수와 row-group hit spread만 오른다면:

- `(country, event_date)` 또는 유사한 복합 정렬을 재검토하고
- 최신 delta만 우선 recluster하고
- historical spread가 남으면 remap/rebuild로 넘어간다

이 경우 문제는 container threshold보다 **정렬 축 불일치**다.

### 시나리오 3: wide OR 결과를 캐시에 넣는 분석 질의

persisted bitmap은 안정적인데 `phase=repair`와 `query_result` CPU만 높다면:

- filter ordering을 먼저 재조정하고
- reusable result만 materialize하며
- 그 handoff에서만 `repairAfterLazy()` 뒤 `runOptimize()`를 건다

storage layout을 갈아엎기 전에 query plan과 handoff 정책을 먼저 본다.

### 시나리오 4: 예전 랜덤 surrogate ID를 계속 물려받는 시스템

compact가 먹혀도 상위 hotspot `high_key` band가 안 바뀐다면:

- internal posting ID remap 전략을 세우고
- cache/materialized bitmap에 mapping version을 붙이고
- cold segment부터 순차 remap하거나 rebuild를 한다

이런 경우는 운영 compaction만으로는 ceiling이 낮다.

## 꼬리질문

> Q: profiling에서 `runOptimize()` hotspot이 보이면 먼저 호출 수를 줄이면 되나요?
> 의도: optimize 비용과 locality 원인을 분리하는지 확인
> 핵심: 무조건 줄이기보다, hot mutable path에서 cold handoff path로 옮기는 편이 맞다. locality가 나쁘면 optimize를 줄여도 근본 원인은 남는다.

> Q: compact가 잘 먹히면 ID remap은 필요 없나요?
> 의도: 최근 drift와 구조적 ID 배치 구조 문제를 구분하는지 확인
> 핵심: 대체로 그렇지만 절대적이진 않다. compact 이득이 빠르게 사라지거나 hotspot band가 고정돼 있으면 remap 가치가 남는다.

> Q: ID remap만 하면 row ordering 문제도 자동으로 해결되나요?
> 의도: one-shot rebuild와 지속 가능한 ingest 정책을 구분하는지 확인
> 핵심: 아니다. remap 뒤에도 upstream ingest/order가 locality를 유지하지 못하면 같은 문제가 다시 쌓인다.

## 한 줄 정리

bitmap hotspot remediation의 핵심은 `runOptimize()`를 더 자주 부르는 것이 아니라, profiling이 보여 준 spread와 fragmentation 원인을 기준으로 **row ordering -> batch compaction -> ID remapping -> cold-path optimize** 순서로 레버를 쓰는 것이다.
