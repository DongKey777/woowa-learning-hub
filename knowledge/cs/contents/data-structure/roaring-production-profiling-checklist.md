---
schema_version: 3
title: Roaring Production Profiling Checklist
concept_id: data-structure/roaring-production-profiling-checklist
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- roaring-production-profiling
- chunk-local-shape-drift
- container-churn-hotspot
aliases:
- Roaring production profiling
- chunk-local cardinality histogram
- run count profiling
- container churn hotspot
- repairAfterLazy profiling
- active chunk heatmap
- 4096 boundary hotspot
symptoms:
- Roaring 성능 문제를 전체 bitmap cardinality나 평균 density로만 보고 hot high_key chunk와 phase별 churn을 놓친다
- build, update, query_result, repair phase를 섞어 array/bitmap/run transition의 원인을 잘못 해석한다
- 4096 boundary pressure, run fragmentation, repairAfterLazy debt, active chunk spread를 함께 계측하지 않는다
intents:
- troubleshooting
- design
prerequisites:
- data-structure/roaring-bitmap
- data-structure/roaring-container-transition-heuristics
next_docs:
- data-structure/roaring-run-churn-observability-guide
- data-structure/bitmap-locality-remediation
- data-structure/roaring-instrumentation-schema-examples
- data-structure/row-ordering-and-bitmap-compression-playbook
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/roaring-container-transition-heuristics.md
- contents/data-structure/roaring-set-op-result-heuristics.md
- contents/data-structure/roaring-intermediate-repair-path-guide.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/bitmap-locality-remediation-playbook.md
- contents/data-structure/roaring-instrumentation-schema-examples.md
- contents/data-structure/roaring-bitmap-selection-playbook.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/compressed-bitmap-families-wah-ewah-concise.md
- contents/data-structure/bit-sliced-bitmap-index.md
confusable_with:
- data-structure/roaring-run-churn-observability-guide
- data-structure/roaring-instrumentation-schema-examples
- data-structure/bitmap-locality-remediation
- data-structure/roaring-container-transition-heuristics
forbidden_neighbors: []
expected_queries:
- Roaring Bitmap production profiling에서 전체 cardinality보다 chunk-local histogram을 봐야 하는 이유는?
- array bitmap run transition counter와 run count profiling을 어떤 tag로 남겨야 해?
- build update query_result repair phase를 분리해 Roaring hotspot을 찾는 체크리스트가 필요해
- 4096 boundary pressure와 repairAfterLazy hotspot을 production에서 어떻게 관측해?
- Roaring workload observability에서 active chunk heatmap과 sampled hotspot event를 어떻게 설계해?
contextual_chunk_prefix: |
  이 문서는 production Roaring Bitmap profiling에서 전체 cardinality가 아니라
  chunk-local cardinality histogram, run count, container transition frequency,
  phase/op/high_key tags를 함께 계측하는 checklist다.
---
# Roaring Production Profiling Checklist

> 한 줄 요약: Roaring 운영 이슈는 전체 cardinality보다 `chunk-local cardinality histogram`, `run 수`, `container 전환 빈도`가 더 직접적으로 드러내므로, 실제 workload 경로에서 이 세 축을 함께 계측해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Bitmap Locality Remediation Playbook](./bitmap-locality-remediation-playbook.md)
> - [Roaring Instrumentation Schema Examples](./roaring-instrumentation-schema-examples.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)

> retrieval-anchor-keywords: roaring production profiling, roaring profiling checklist, chunk-local cardinality histogram, roaring run count profiling, container churn hotspot, roaring transition counter, array bitmap flip, bitmap run fragmentation, roaring workload observability, active chunk heatmap, real workload bitmap profiling, roaring intermediate result profiling, repairAfterLazy hotspot, run optimize profiling, 4096 boundary hotspot, cardinality band histogram, container flip rate, bitmap locality diagnostics, roaring ops guide, roaring performance checklist, roaring run churn observability, boundary pressure roaring, repair debt roaring, temporary container hotspot, ingest churn vs repair churn

## 핵심 개념

Roaring을 운영에서 느리다고 말할 때, 원인은 대개 전체 bitmap cardinality가 아니다.

- hit가 몇 개의 16-bit chunk에 퍼졌는가
- 각 chunk 안에서 run이 몇 번 끊기는가
- 같은 chunk가 `array <-> bitmap <-> run`을 얼마나 자주 왕복하는가

즉 production profiling은 "bitmap 하나의 평균 density"가 아니라  
**chunk-local shape drift를 시간축으로 잡아내는 일**에 가깝다.

특히 아래 세 경우를 분리해서 봐야 한다.

- bulk build / compaction 단계
- online add / remove / revoke 단계
- query-time `AND/OR/XOR` intermediate 결과 단계

이 셋을 섞어 평균을 내면 hotspot이 희석된다.

특히 lazy `OR`의 temporary bitmap demotion과 run-native `XOR` finalize를 ingest churn bucket에 합치면 원인이 흐려지므로, `repairAfterLazy` 전용 tag 설계는 [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)로 이어서 보면 좋다.

## 먼저 고정할 측정 단위

운영 계측은 아래 tag가 빠지면 해석이 거의 불가능해진다.

| 측정 축 | 최소 tag | 이유 |
|---|---|---|
| bitmap 정체성 | `bitmap_id`, `predicate`, `segment_id` | 어떤 대상군/포스팅 리스트가 문제인지 분리해야 한다 |
| 실행 단계 | `build`, `update`, `query_result`, `repair` | ingest 문제와 query intermediate 문제를 분리한다 |
| 연산 종류 | `add`, `remove`, `and`, `or`, `xor`, `runOptimize` | 같은 chunk라도 어떤 연산이 churn을 만드는지 다르다 |
| chunk 위치 | `high_key` | hotspot은 전체 bitmap이 아니라 특정 chunk에 몰린다 |
| container 상태 | `before_type`, `after_type` | array/bitmap/run 왕복 여부를 바로 확인한다 |

최소 샘플 payload는 아래 정도면 충분하다.

```json
{
  "bitmap_id": "country=KR",
  "segment_id": "seg-0421",
  "phase": "query_result",
  "op": "or",
  "high_key": 183,
  "before_type": "array",
  "after_type": "bitmap",
  "cardinality": 4178,
  "runs": 31,
  "serialized_bytes": 8192,
  "cpu_ns": 18200
}
```

핵심은 모든 chunk를 영구 저장하는 것이 아니라,  
**상위 hotspot chunk와 histogram bucket을 남길 수 있을 만큼만 샘플링**하는 것이다.
Java `RoaringBitmap` bridge와 CRoaring wrapper를 어디에 두고, sampled event와 rollup schema를 어떤 필드로 고정할지는 [Roaring Instrumentation Schema Examples](./roaring-instrumentation-schema-examples.md)에서 이어서 볼 수 있다.

## 체크리스트 1. Chunk-Local Cardinality Histogram

첫 번째로 볼 것은 전체 bitmap cardinality가 아니라 **active chunk별 cardinality 분포**다.

운영에서는 아래 bucket이 실용적이다.

- `1..64`
- `65..512`
- `513..2048`
- `2049..3583`
- `3584..4096`
- `4097..4608`
- `4609..16384`
- `16385..65536`

여기서 핵심은 `3584..4608` 같은 **경계 집중 bucket**을 따로 두는 것이다.  
`4096` 근처를 넓게 잡아야 array/bitmap 왕복 후보군을 바로 찾을 수 있다.

같이 남길 값은 아래 네 가지다.

- active chunk 수
- bucket별 chunk 개수
- `4096` 경계 근처 chunk의 상위 N개 `high_key`
- chunk별 update/query hit 횟수

이 histogram은 아래 해석에 바로 연결된다.

| 관찰 신호 | 의미 |
|---|---|
| global cardinality는 비슷한데 active chunk 수가 늘어난다 | row ordering 또는 ID locality가 나빠져 hit가 퍼지고 있다 |
| `3584..4608` bucket 비중이 높다 | `array <-> bitmap` churn 후보가 많다 |
| 작은 bucket이 긴 꼬리를 만든다 | sparse chunk가 너무 많아 header/container overhead가 커질 수 있다 |
| 상위 hotspot이 몇 개 chunk에 집중된다 | 구조 전체 문제가 아니라 특정 shard 또는 key band 문제일 가능성이 크다 |

즉 histogram은 "밀집한가"보다  
"어디가 애매하게 밀집해졌는가"를 잡아내는 데 쓴다.

## 체크리스트 2. Run Count와 Fragmentation

두 번째 축은 chunk별 run 수다.  
run container 적합성은 cardinality만으로 보이지 않고, **run이 몇 번 끊기는지**로 드러난다.

최소 계측 항목은 아래가 좋다.

- chunk별 `runs`
- active chunk 기준 `runs`의 `p50/p95/p99`
- `avg_run_length = cardinality / max(runs, 1)`
- `runOptimize` 전후 `serialized_bytes`
- full chunk 비중과 near-full chunk 비중

운영에서 자주 보는 패턴은 아래와 같다.

| 관찰 신호 | 해석 |
|---|---|
| cardinality는 낮은데 runs가 높다 | run container는 이득이 작고 array가 더 자연스러울 수 있다 |
| cardinality는 비슷한데 runs만 계속 오른다 | late delete, revoke, hole punching으로 run fragmentation이 진행 중이다 |
| bulk build 직후엔 runs가 낮지만 온라인 경로에서 급격히 오른다 | 정렬 ingest 이득이 유지되지 못하고 있다 |
| `runOptimize`가 저장 공간은 줄이지만 CPU를 크게 올린다 | hot update path에서 optimize를 너무 자주 돌리는 신호다 |

여기서는 평균보다 **tail**이 중요하다.  
평균 run 수가 낮아도 일부 hot chunk에서 `runs`가 급증하면 그쪽이 바로 hotspot이 된다.

## 체크리스트 3. Container Churn Hotspot

세 번째 축은 실제 전환 빈도다.  
Roaring의 운영 비용은 현재 container 타입보다 **같은 chunk가 몇 번 재작성되는가**에 더 크게 좌우된다.

꼭 세야 할 카운터는 아래 여섯 가지다.

- `array -> bitmap`
- `bitmap -> array`
- `array -> run`
- `bitmap -> run`
- `run -> array`
- `run -> bitmap`

여기에 아래 두 값을 붙이면 해석이 빨라진다.

- transition당 재작성 바이트
- transition당 CPU 시간

운영에서는 특히 아래를 분리해서 본다.

| hotspot 유형 | 무엇을 봐야 하나 |
|---|---|
| ingest hotspot | 같은 `high_key`가 add/remove에 의해 `4096` 경계를 왕복하는지 |
| query hotspot | `AND/OR/XOR` intermediate 결과가 repair 단계에서 타입을 바꾸는지 |
| optimize hotspot | `runOptimize`가 같은 chunk를 반복해서 run으로 올렸다가 다시 내리는지 |

핵심 지표는 단순 전환 총합보다 **chunk별 flip rate**다.

- `transitions_per_chunk_per_minute`
- `distinct_high_keys_with_transition`
- `top_n_chunks_by_transition_cpu`

이 세 값을 같이 보면:

- 문제 chunk가 좁게 몰려 있는지
- 전체 workload가 넓게 불안정한지
- CPU는 전환 횟수 때문인지, 몇 번 안 되는 큰 재작성 때문인지

를 구분할 수 있다.

## 체크리스트 4. Intermediate Result를 따로 본다

실제 서비스에서는 저장된 원본 bitmap보다 **질의 중간 결과**가 더 큰 churn을 만들 때가 많다.

예를 들면:

- `bitmap ∩ bitmap` 결과가 매번 sparse array로 식는다
- `array ∪ array`가 합쳐질 때만 bitmap으로 승격된다
- `OR/XOR` 이후 lazy repair가 결과 타입을 다시 바꾼다

그래서 profiling도 원본 bitmap과 intermediate 결과를 나눠야 한다.

- persisted bitmap profile
- query intermediate profile
- repair profile

이 분리를 하지 않으면, ingest를 고쳐도 실제 latency spike가 남는 상황을 자주 겪는다.

## 체크리스트 5. Workload 상관관계를 붙인다

숫자만 보고 끝내면 "왜 여기서만 나쁘지?"를 설명하지 못한다.  
아래 축과 꼭 묶어야 한다.

- shard / segment / partition
- predicate 종류
- batch size
- sorted ingest 여부
- late update / revoke 비율
- 시간대별 workload shape

예를 들어 같은 `country=KR` bitmap이라도:

- bulk build 직후엔 active chunk 수가 작고 runs도 낮다
- late revoke가 쌓이면 같은 cardinality에서도 runs만 올라간다
- 마케팅 질의 조합에서는 intermediate `OR` 결과가 bitmap으로 부풀 수 있다

즉 profiling 결과는 자료구조 자체보다  
**배치 방식, row ordering, query template**와 함께 읽어야 한다.

## 운영 대시보드에서 먼저 올릴 패널

대시보드 첫 버전은 복잡할 필요 없다. 아래 여섯 패널이면 대부분의 문제를 좁힐 수 있다.

1. active chunk 수 추이
2. chunk-local cardinality histogram
3. `4096` 근처 bucket 비중
4. chunk별 runs `p50/p95/p99`
5. transition rate by container pair
6. transition CPU 상위 `high_key` 목록

여기에 여유가 있으면 아래를 추가한다.

- `runOptimize` 전후 bytes delta
- query intermediate 결과 타입 비중
- shard/segment별 hotspot heatmap

이 체크리스트가 "무엇을 재야 하나"에 초점을 둔다면, [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)는 이 메트릭을 어떤 파생 지표와 debugging playbook으로 묶어 실제 churn hotspot을 좁힐지에 초점을 둔다.  
그리고 profiling 이후 row ordering, batch compaction, ID remapping, `runOptimize()` handoff를 어떤 순서로 바꿔야 하는지는 [Bitmap Locality Remediation Playbook](./bitmap-locality-remediation-playbook.md)에서 바로 이어서 보면 된다.

## 빠른 진단표

| 증상 | 가장 먼저 의심할 것 | 다음 확인 |
|---|---|---|
| p95 latency spike인데 global cardinality는 안정적이다 | `4096` 근처 chunk churn | boundary bucket과 `array <-> bitmap` flip rate |
| memory가 늦게 계속 증가한다 | run fragmentation | runs 분포와 `runOptimize` 전후 bytes |
| ingest는 빠른데 복합 질의만 느리다 | intermediate result churn | `query_result`와 `repair` phase 전환 분포 |
| bulk build benchmark는 좋은데 운영에선 나쁘다 | row ordering 유지 실패 | active chunk 수와 late update 비율 |
| hotspot이 몇 shard에만 몰린다 | local ID band skew | top `high_key`와 shard tag 상관관계 |

## 자주 하는 실수

- synthetic uniform random 데이터만 보고 production shape를 가정한다
- global cardinality와 전체 bitmap size만 기록한다
- `runOptimize` 전후 크기만 보고 run 수 분포를 보지 않는다
- ingest와 query intermediate를 같은 histogram으로 합친다
- transition 총합만 세고 어떤 `high_key`가 문제인지 남기지 않는다

Roaring 운영 튜닝은 "평균적인 bitmap"을 보는 작업이 아니라,  
**문제 chunk를 분리해 실제 workload path에서 관찰하는 작업**에 가깝다.

## 꼬리질문

> Q: 왜 global cardinality만 보면 안 되나요?
> 의도: 전체 크기와 chunk-local shape를 구분하는지 확인
> 핵심: Roaring 비용은 active chunk 수, chunk별 cardinality, run 수, 전환 빈도에 의해 결정되므로 같은 global cardinality라도 비용이 크게 다를 수 있다.

> Q: run count는 run container를 쓰는 경우에만 재면 되나요?
> 의도: run locality를 container type보다 상위 개념으로 보는지 확인
> 핵심: 아니다. bitmap이나 array 상태여도 run 수를 보면 향후 optimize 이득과 fragmentation 방향을 미리 읽을 수 있다.

> Q: transition 총합만 세면 충분하지 않나요?
> 의도: hotspot이 국소 chunk에 몰리는 특성을 이해하는지 확인
> 핵심: 아니다. 총합만 보면 몇 개 chunk의 반복 flip인지, 넓은 영역의 약한 churn인지 구분되지 않는다.

## 한 줄 정리

Roaring production profiling의 핵심은 전체 bitmap 통계가 아니라, 실제 workload 경로에서 **chunk-local cardinality histogram, run 수 분포, container churn hotspot**을 함께 잡아내는 것이다.
