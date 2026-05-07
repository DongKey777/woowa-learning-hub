---
schema_version: 3
title: Roaring Lazy Union And Repair Costs
concept_id: data-structure/roaring-lazy-union-and-repair-costs
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- roaring-lazy-union-repair-cost
- repair-debt
- warehouse-bitmap-or
aliases:
- Roaring lazy union repair cost
- lazy OR materialization cost
- repairAfterLazy cost
- result materialization Roaring
- wide OR warehouse bitmap
- lazy union finalize debt
- cached bitmap materialization
symptoms:
- lazy OR가 중간 exactness 계산을 미루는 이득과 최종 result를 serialize/cache publish 가능한 artifact로 만드는 비용을 같은 것으로 본다
- run-heavy input bitmap이면 OR 결과도 자동으로 압축 이득이 유지된다고 보고 provisional container와 repair debt를 계산하지 않는다
- getCardinality, serialize, runOptimize, cache publish 경계를 너무 일찍 밟아 lazy fan-in savings를 반복 materialization 비용으로 지운다
intents:
- troubleshooting
- deep_dive
prerequisites:
- data-structure/roaring-bitmap-wide-lazy-union-pipeline
next_docs:
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-query-result-ordering-guide
- data-structure/roaring-run-optimize-timing-guide
- data-structure/warehouse-sort-key-co-design-for-bitmap-indexes
linked_paths:
- contents/data-structure/roaring-bitmap-wide-lazy-union-pipeline.md
- contents/data-structure/roaring-set-op-result-heuristics.md
- contents/data-structure/roaring-intermediate-repair-path-guide.md
- contents/data-structure/roaring-query-result-ordering-guide.md
- contents/data-structure/roaring-run-optimize-timing-guide.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/warehouse-sort-key-co-design-for-bitmap-indexes.md
- contents/data-structure/late-arriving-rows-and-bitmap-maintenance.md
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/compressed-bitmap-families-wah-ewah-concise.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
confusable_with:
- data-structure/roaring-bitmap-wide-lazy-union-pipeline
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-query-result-ordering-guide
- data-structure/roaring-run-optimize-timing-guide
forbidden_neighbors: []
expected_queries:
- Roaring lazy OR는 wide fan-in 동안 이득이 있지만 getCardinality serialize에서 repairAfterLazy 비용이 붙는 이유는?
- run-heavy warehouse bitmap에서 lazy union compression win이 materialization으로 지워지는 경우는?
- repair debt와 finalize debt를 Roaring query result cache publish 전에 어떻게 계산해?
- lazy OR 결과를 언제 exact count serialize 가능한 bitmap으로 만들지 결정하는 기준은?
- Roaring lazy union and repair costs를 warehouse bitmap OR fan-in 기준으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 Roaring lazy OR가 wide fan-in 중 exact cardinality 계산을 미루는
  이득과, getCardinality/serialize/cache publish/runOptimize 경계에서
  repairAfterLazy와 materialization pass로 되돌아오는 비용을 분리하는 playbook이다.
---
# Roaring Lazy Union And Repair Costs

> 한 줄 요약: run-heavy warehouse bitmap에서 lazy OR는 wide fan-in 동안 exact count와 최종 표현 선택을 미뤄 이득을 주지만, 결과가 `getCardinality()`·`serialize()`·cache publish·`runOptimize()` 경계로 올라가면 `repairAfterLazy()`와 materialization pass가 곧바로 붙어 기대한 압축 이득을 쉽게 지워 버릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)
> - [Roaring Query Result Ordering Guide](./roaring-query-result-ordering-guide.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)
> - [Late-Arriving Rows and Bitmap Maintenance](./late-arriving-rows-and-bitmap-maintenance.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)

> retrieval-anchor-keywords: roaring lazy union repair cost, roaring lazy or repair cost, lazy OR materialization cost, cardinality repair roaring, repairAfterLazy cost, result materialization roaring bitmap, run-heavy warehouse bitmap, warehouse bitmap lazy union, wide OR warehouse bitmap, lazy union compression win erased, roaring serialize after lazy union, cached bitmap materialization, query result materialization bitmap, roaring repair debt, active chunk repair debt, row-group boundary repair cost, runOptimize after lazy OR, sorted ingest lazy OR, provisional container warehouse, lazy union finalize debt, warehouse bitmap OR fan-in, run-heavy result cache bitmap, temporary container rewrite roaring, repairAfterLazy hotspot profiling

## 핵심 개념

lazy OR가 아껴 주는 것은 **중간 exactness 계산의 반복**이지, 최종 결과를 안전하고 재사용 가능한 artifact로 바꾸는 비용 자체가 아니다.

run-heavy warehouse bitmap에서는 이 차이가 특히 자주 가려진다.

- 입력 bitmap은 정렬된 row ordering 덕분에 매우 잘 압축돼 보인다
- 그래서 `OR`도 압축 이득을 거의 그대로 가져갈 것처럼 느껴진다
- 하지만 Roaring lazy OR는 global run artifact를 바로 만드는 대신, `high key`별 provisional container를 쌓아 둔다
- 결과를 실제로 읽거나 내보내는 순간에는 그 provisional debt가 `repairAfterLazy()`와 materialization pass로 되돌아온다

즉 질문은 "입력이 run-heavy인가?" 하나로 끝나지 않는다.  
실전 질문은 아래 두 개를 함께 봐야 한다.

1. lazy OR savings가 **몇 단계의 fan-in** 동안 유지되는가
2. 그 결과를 exact count 가능하고 serialize 가능한 bitmap으로 만들기 위해 **몇 번의 전체 pass**를 다시 내야 하는가

감각은 아래 파이프라인으로 잡으면 된다.

```text
run-heavy input bitmaps
  -> key-sorted lazy OR fan-in
  -> provisional containers (bit pattern exact, cardinality invalid 가능)
  -> 더 합칠 OR가 있으면 계속 lazy 유지
  -> exact count / rank-select / serialize / cache publish가 필요해지면
  -> repairAfterLazy
  -> materialize / serialize
  -> reusable cold artifact면 상황에 따라 runOptimize
```

압축 이득이 지워지는 순간은 대개 **lazy fan-in savings보다 finalize debt가 더 커지는 지점**이다.

이 provisional debt가 실제로 어떤 temporary bitmap/run rewrite로 나타나고, 운영 계측에서 ingest churn과 어떻게 분리되는지는 [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)에서 이어서 볼 수 있다.  
그리고 planner가 selective predicate ordering과 shared intermediate reuse로 그 debt 자체를 어떻게 줄일지는 [Roaring Query Result Ordering Guide](./roaring-query-result-ordering-guide.md)에서 이어서 보면 된다.

## 1. 왜 run-heavy warehouse bitmap은 OR가 싸 보이나

warehouse가 `(country, status, event_date)`처럼 정렬돼 있으면 개별 predicate bitmap은 대개 아래 특징을 가진다.

- 긴 값 band 덕분에 run 수가 낮다
- active chunk 수가 작다
- serialize footprint가 작고 scan locality도 좋다

그래서 `country IN (KR, JP, TW)` 같은 OR를 보면 직관적으로는 "긴 band 몇 개를 이어 붙이는 일"처럼 보인다.

하지만 Roaring이 실제로 보는 것은 global band 하나가 아니라 **여러 `high key`에 분산된 container 집합**이다.

- 긴 연속 구간도 16-bit container 경계마다 최소 한 번은 다시 나타난다
- bitmap-native OR 경로는 non-full run을 바로 확정하지 않을 수 있다
- OR 결과가 넓어질수록 개별 입력보다 active chunk spread가 커질 수 있다

즉 입력이 run-heavy라는 사실은 중요하지만,  
최종 lazy OR 결과가 **얼마나 많은 container를 provisional 상태로 남기는가**와는 별개의 문제다.

WAH/EWAH 같은 whole-bitmap run codec과 감각이 어긋나는 지점도 여기다.

- global clean run이 길면 word-aligned codec은 skip 이득이 바로 커진다
- Roaring lazy OR는 그 전역 run을 곧바로 materialized run artifact로 굳히지 않는다

그래서 "입력 압축률이 높다"와 "lazy OR 후 finalize 비용이 작다"를 같은 문장으로 묶으면 자주 틀린다.

## 2. lazy OR가 실제로 아끼는 비용

lazy OR가 강한 이유는 repeated fan-in 동안 **exact cardinality bitcount**를 뒤로 미루기 때문이다.

대표적으로 이득이 나는 경우는 아래와 같다.

- 같은 query 안에서 bitmap 여러 개를 계속 OR 해야 한다
- intermediate result에 아직 다른 OR/AND 조합이 더 붙는다
- exact cardinality 숫자보다 "비트 패턴이 맞는 provisional result"만 있으면 다음 단계로 갈 수 있다
- key-local cardinality만 합산하고 whole bitmap artifact는 남기지 않아도 된다

이때 lazy OR는 아래 비용을 줄인다.

- merge tree 중간마다 `repairAfterLazy()`를 반복하는 비용
- 중간 bitmap마다 exact cardinality를 다시 세는 비용
- 아직 버릴 intermediate result를 매번 serialize-ready 상태로 만드는 비용

특히 count만 필요하면 `horizontalOrCardinality`처럼 **key-local repair 후 즉시 합산**하는 경로가 유리하다.  
이 경로는 "union 결과의 숫자"는 얻되, "whole bitmap artifact materialization"은 피한다.

핵심은 lazy OR의 승리가 **중간 단계 생략**에서 나온다는 점이다.  
결과를 오래 들고 재사용하는 artifact로 만들 때 얻는 자동 보너스가 아니다.

## 3. 비용이 다시 붙는 경계는 repair와 materialization이다

run-heavy 입력이라도 아래 소비자를 만나면 deferred debt가 바로 돌아온다.

| 경계 | 새로 내는 pass | run-heavy라고 자동으로 싸지지 않는 이유 |
|---|---|---|
| `getCardinality()`, `cardinalityExceeds()` | provisional container bitcount + cardinality 복구 | 긴 run도 active container마다 exact count를 다시 세야 한다 |
| `rank`, `select`, `rangeCardinality` | prefix cardinality가 맞도록 whole-bitmap repair | container 내부 비트는 맞아도 container 사이 prefix sum이 복구돼야 한다 |
| `serialize`, cache publish, spill | repaired metadata 확인 + bytes materialization/copy | 압축된 입력과 별개로 결과 artifact 전체를 한 번 써 내야 한다 |
| `runOptimize()` | run 수 재평가 + serialized size 비교 | bitmap-native OR가 남긴 non-full run을 찾으려면 별도 pass가 더 필요하다 |

여기서 중요한 건 `repairAfterLazy()`와 result materialization을 한 덩어리로 보지 않는 것이다.

- `repairAfterLazy()`는 correctness boundary다
- `serialize`/cache publish는 artifact boundary다
- `runOptimize()`는 compression boundary다

run-heavy warehouse 질의에서는 이 세 경계가 한 요청 안에 연달아 붙기 쉽다.

```text
lazy OR
  -> getLongCardinality()로 planner threshold 확인
  -> serialize해서 result cache publish
  -> cold reusable artifact라며 runOptimize
```

이 흐름이면 lazy OR가 아낀 exactness work를 곧바로 다시 지불한다.

## 4. 기대한 압축 wins가 지워지는 대표 패턴

### 패턴 1. wide OR 직후 exact count와 cache publish가 바로 따라온다

예를 들어 `(country=KR OR country=JP OR country=TW)` 결과를 대시보드 query cache에 넣는다고 하자.

- 입력 bitmap들은 정렬 덕분에 run-heavy다
- lazy OR fan-in 자체는 싸게 끝날 수 있다
- 하지만 cache key를 채우기 전에 exact cardinality를 읽고 serialize까지 하면 whole result를 다시 훑는다

즉 이 경우 이득은 "중간 repair를 안 했다"는 데서만 생기고,  
최종 artifact를 매 요청마다 만들면 압축 이득이 hot path latency로 잘 번역되지 않는다.

### 패턴 2. global band는 길지만 active `high key`가 많다

warehouse bitmap은 길게 모인 row band를 가지더라도, Roaring 내부에서는 container 경계를 계속 가진다.

- band가 row-group/segment 경계를 자주 넘는다
- OR 결과가 여러 차원 band를 합치며 폭이 넓어진다
- 입력은 압축됐어도 출력은 많은 active container를 품는다

이때 repair 비용은 "전역적으로 run이 길다"는 사실보다 **container 수**에 더 민감하다.  
그래서 run-heavy 입력이 곧 low repair cost를 뜻하지는 않는다.

### 패턴 3. bitmap-native OR 뒤 non-full run이 많이 남아 있는데 결과 수명이 짧다

bitmap-native OR는 full chunk만 특별 취급하고, 일반적인 non-full run은 종종 `runOptimize()` 전까지 남겨 둔다.

문제는 결과가:

- 곧 버릴 one-shot filter이거나
- 다음 mutation이나 다음 set-op로 다시 깨질 intermediate이거나
- cache hit가 낮은 ad-hoc artifact

라면, `runOptimize()`가 찾아낸 압축 이득을 회수할 소비자가 거의 없다는 점이다.

즉 "run-heavy result니까 optimize하자"가 아니라  
"이 result가 optimize 비용을 여러 소비자에게 나눠서 회수하나?"를 먼저 물어야 한다.

### 패턴 4. late-arriving row와 revoke가 run shape를 미리 깨뜨린다

초기 bulk build는 run-heavy였더라도 운영이 시작되면 아래가 생긴다.

- late-arriving row가 band 사이에 끼어든다
- revoke/delete가 긴 `1-run`에 hole을 낸다
- delta/tombstone layer가 query-time OR fan-in에 섞인다

이 상태에서는 lazy OR 후 repair 비용은 여전히 내는데,  
`runOptimize()`가 되찾아 줄 수 있는 non-full run payoff는 작아질 수 있다.

즉 repair debt는 유지되고 compression payoff만 약해지는 셈이다.

## 5. materialization을 언제 피하고 언제 감수할지

빠른 판단은 아래 표로 충분하다.

| 지금 필요한 것 | 권장 선택 | 이유 |
|---|---|---|
| exact cardinality 숫자만 필요하다 | key-local repair 경로 우선 | whole bitmap artifact를 materialize할 이유가 없다 |
| 결과가 아직 더 많은 set-op에 재투입된다 | lazy 유지 | 중간 finalize를 서두르면 repeated repair가 된다 |
| 결과를 한 번 읽고 버린다 | serialize와 runOptimize를 보수적으로 | artifact boundary 비용을 회수할 소비자가 없다 |
| 결과를 cache/materialized view로 오래 재사용한다 | repair 후 상황에 따라 runOptimize | 재사용이 있어야 finalize pass가 amortize된다 |
| hot mutable warehouse tier다 | query마다 optimize하지 말고 seal/compact 경계로 미룬다 | late row와 revoke가 곧 run shape를 다시 깨뜨릴 수 있다 |

한 줄로 줄이면 이렇다.

```text
lazy OR의 이득은 "나중에 고쳐도 되는 동안"만 유지된다.
결과를 바로 세고, 바로 쓰고, 바로 압축해 보관해야 하면 그 debt는 같은 요청 안에서 다시 돌아온다.
```

## 빠른 판단표

| 관찰 신호 | 해석 |
|---|---|
| `repair` CPU가 `query_result` CPU와 비슷하게 커진다 | lazy fan-in savings가 finalize debt에 거의 상쇄되고 있다 |
| OR 결과를 만든 직후 `serialize`와 cache publish가 항상 붙는다 | materialization이 hot path의 주비용일 수 있다 |
| `runOptimize()` 뒤 크기 감소가 미미하다 | run-heavy라고 기대한 결과 shape가 이미 깨졌거나, optimize를 걸 경계가 잘못됐다 |
| sorted ingest인데도 active chunk spread가 넓다 | OR 결과가 band를 넓히거나 row-group reset이 많아 container 수가 줄지 않는다 |
| late row/tombstone 비중이 높은데 materialized OR cache 수명이 짧다 | repair와 optimize 비용을 내고도 압축 이득을 회수하지 못한다 |

## 꼬리질문

> Q: 입력 bitmap이 매우 run-heavy면 lazy OR 뒤 `repairAfterLazy()`도 거의 공짜에 가깝나요?
> 의도: 입력 압축률과 finalize 비용을 분리하는지 확인
> 핵심: 아니다. Roaring repair 비용은 global run 길이보다 active container 수와 cardinality 복구 pass에 더 직접적으로 묶인다.

> Q: exact cardinality만 필요할 때 왜 whole bitmap materialization이 과한가요?
> 의도: 숫자 계산과 artifact 생성의 차이를 보는지 확인
> 핵심: key-local repair 후 합산하면 숫자는 얻되, serialize 가능한 whole result bitmap을 만들 필요가 없기 때문이다.

> Q: run-heavy warehouse result라면 `runOptimize()`를 항상 붙여야 하나요?
> 의도: run-friendly shape와 amortization 조건을 함께 보는지 확인
> 핵심: 아니다. 재사용 경계가 없거나 곧 다시 깨질 결과라면 optimize는 compression보다 extra pass 비용이 더 크게 남을 수 있다.

> Q: lazy OR가 아낀 비용이 왜 materialization에서 다시 사라지나요?
> 의도: deferred work의 정체를 설명할 수 있는지 확인
> 핵심: lazy OR는 cardinality와 표현 선택을 미뤘을 뿐 없앤 것이 아니므로, exact count·serialize·cache publish 경계에서 그 일을 다시 해야 한다.

## 한 줄 정리

run-heavy warehouse bitmap에서 lazy OR는 fan-in 동안에는 유효하지만, 결과를 바로 `repair -> materialize -> runOptimize` 경계로 끌어올리면 deferred exactness debt가 한 요청 안에 되돌아와 기대한 압축 이득과 latency 이득을 쉽게 상쇄한다.
