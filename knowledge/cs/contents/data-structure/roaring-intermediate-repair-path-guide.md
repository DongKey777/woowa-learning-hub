# Roaring Intermediate Repair Path Guide

> 한 줄 요약: Roaring의 lazy `OR`와 일부 run-native `XOR`/`OR` 경로는 결과를 곧바로 final container로 확정하지 않고 `lazy bitmap`이나 provisional `run` 같은 임시 container를 만든 뒤 `repairAfterLazy()` 또는 `toEfficientContainer()`에서 다시 고치므로, profiling도 ingest churn과 `query_result -> repair` 재작성 비용을 분리해서 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Lazy Union And Repair Costs](./roaring-lazy-union-and-repair-costs.md)
> - [Roaring Query Result Ordering Guide](./roaring-query-result-ordering-guide.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Roaring ANDNOT Result Heuristics](./roaring-andnot-result-heuristics.md)

> retrieval-anchor-keywords: roaring intermediate repair path, roaring temporary container, lazy OR temporary bitmap, roaring lazy xor temporary run, repairAfterLazy hotspot profiling, ingest churn vs repair churn, query result repair phase, roaring repair demotion, temporary bitmap to array roaring, bitmap wide repairAfterLazy, key local repair roaring, run native xor finalize, toEfficientContainer profiling, priorityqueue_or repair hotspot, array array overlap lazy bitmap, roaring intermediate result rewrite, roaring repair scope, repair kind roaring, roaring lazy repair temporary container

## 핵심 개념

`repairAfterLazy()` hotspot은 단순히 "`OR`가 많다"가 아니라,  
**임시 container를 final container로 다시 쓰는 rewrite가 몇 번 붙는가**에 더 가깝다.

Roaring set-op에서는 아래 두 층을 분리해서 보는 편이 정확하다.

- set-op fast path: merge를 빨리 끝내기 위해 임시 `lazy bitmap` 또는 provisional `run`을 만든다
- finalize path: exact cardinality, `array` demotion, full normalization, `run/array/bitmap` 재선택을 수행한다

중요한 점은 이 rewrite가 보통 **persisted bitmap mutation이 아니라 request-scoped intermediate churn**이라는 점이다.  
그래서 ingest/update churn과 한 bucket에 섞으면 원인을 거의 항상 잘못 읽게 된다.

## 1. 어떤 경로가 temporary container를 만드는가

빠르게 보면 아래 표로 충분하다.

| 경로 | 먼저 생기는 임시 container | finalize 경계 | 흔한 최종 결과 |
|---|---|---|---|
| `Array ∪ Array` (`sum > 4096`) | `lazy bitmap` | `repairAfterLazy()` | `array` 또는 `bitmap` |
| `Bitmap ∪ Bitmap`, wide lazy `OR` | `high key`별 `lazy bitmap` | bitmap-wide `repairAfterLazy()` | `array`, `bitmap`, full `run` |
| `Run ∪ Array` | provisional `run`, 경우에 따라 `lazy bitmap` fallback | `toEfficientContainer()` 또는 `repairAfterLazy()` | `run`, `array`, `bitmap` |
| `Run ⊕ small Array` | provisional `run` | `toEfficientContainer()` | `run`, `array`, `bitmap` |

여기서 주의할 점이 있다.

- bitmap-native `Bitmap ⊕ Bitmap`, `Bitmap ⊕ Array`는 자주 **exact cardinality path**로 끝난다
- 그래서 `XOR`가 느리다고 해서 항상 `repairAfterLazy()` debt를 의심하면 틀릴 수 있다
- 반대로 `OR`는 `array -> lazy bitmap -> array`처럼 최종 타입보다 중간 작업 형식이 더 많이 바뀐다

즉 "`XOR`도 repair path가 있다"와 "`모든 `XOR`가 `repairAfterLazy()` hotspot을 만든다`"는 다른 문장이다.

## 2. `OR` repair path는 왜 임시 bitmap을 많이 남기나

가장 전형적인 예는 `Array ∪ Array`다.

- 왼쪽 array `3500`
- 오른쪽 array `3500`
- 상한 `sum = 7000`이라 처음엔 bitmap 경로를 탄다
- 실제 union은 겹침이 커서 `3600`일 수 있다
- 이 경우 repair 후 최종 결과는 다시 `array`다

즉 관측상으로는 아래처럼 보인다.

```text
array + array
  -> temporary lazy bitmap allocate
  -> repairAfterLazy bitcount
  -> final array demotion
```

이때 보이는 `array -> bitmap -> array`는 ingest 경로의 승격/강등이 아니라,  
**query intermediate가 잠깐 bitmap 작업 형식을 빌린 뒤 다시 내려온 것**이다.

wide `OR`에서는 이 패턴이 `high key`마다 반복될 수 있다.

- `priorityqueue_or(...)`, `naive_or(...)`, `lazyorfromlazyinputs(...)`
- 같은 key에서 만들어진 provisional bitmap이 bitmap 전체 결과에 누적된다
- 마지막 consumer가 `getCardinality()`, `serialize()`, cache publish를 요구하면 bitmap-wide `repairAfterLazy()`가 붙는다

그래서 운영에서 비싼 것은 "union 결과가 bitmap이었다"보다:

- 몇 개의 active `high key`가 provisional 상태였는지
- 그중 얼마나 많이 `array`로 다시 내려왔는지
- repair가 key-local이었는지, bitmap-wide였는지

다.

이 점은 [Roaring Lazy Union And Repair Costs](./roaring-lazy-union-and-repair-costs.md)의 finalize debt 설명과 이어지지만, 여기서는 **temporary container rewrite 자체**를 따로 보는 데 초점을 둔다.

## 3. `XOR`는 repair bucket을 더 잘게 쪼개서 봐야 한다

`XOR`는 이름만 보면 `OR`처럼 lazy bitmap repair가 많을 것 같지만, 실제로는 경로가 더 갈린다.

### `repairAfterLazy()`가 주역인 경우

- `OR` 기반 intermediate bitmap을 다시 합치는 wide query
- 일부 run-based path가 fragmentation guardrail 때문에 `lazy bitmap`으로 갈아탄 경우

### `toEfficientContainer()`가 더 중요한 경우

- `Run ⊕ small Array`
- `Run ⊕ Run`
- `Run ∪ Array`가 provisional `run`으로 시작한 경우

특히 `Run ⊕ small Array`는 "긴 run에 hole 몇 개만 토글"하는 상황이라 처음엔 run을 유지해도 좋아 보인다.  
하지만 토글 수가 늘어 run 수가 급증하면 finalization에서:

```text
provisional run
  -> toEfficientContainer()
  -> final array or bitmap
```

으로 바뀐다.

이 rewrite도 temporary container churn이지만,  
**`repairAfterLazy()` 전용 hotspot과는 다른 bucket**으로 보는 편이 맞다.

운영에서 구분이 필요한 이유는 명확하다.

- `repairAfterLazy()` 급증: lazy bitmap debt가 query finalization에서 돌아온다
- `toEfficientContainer()` 급증: run-native toggle/fragmentation이 문제다
- 둘 다 낮은데 `XOR`만 느리다: exact bitmap XOR 자체나 filter ordering을 먼저 봐야 한다

즉 `XOR`까지 같은 대시보드에 넣더라도 최소한 `repair_kind`는 나눠야 한다.

## 4. ingest churn과 intermediate repair churn은 어떻게 다른가

둘 다 `before_type`, `after_type`, `bytes_rewritten`, `cpu_ns`를 만들기 때문에 표면적으로는 매우 비슷하다.  
하지만 아래 축이 다르면 해석도 완전히 달라진다.

| 구분 축 | ingest churn | intermediate repair churn |
|---|---|---|
| owner | persisted bitmap | request-scoped intermediate |
| phase | `build`, `update` | `query_result`, `repair` |
| 대표 op | `add`, `remove`, `revoke` | `or`, `xor` |
| lifetime | segment/bitmap 수명과 함께 간다 | query 종료 또는 cache publish 전까지만 산다 |
| rewrite 의미 | 실제 저장 상태가 바뀜 | 임시 작업 형식을 final 형식으로 정리함 |
| 먼저 볼 원인 | row ordering, late update, delete batching | fan-in 폭, overlap, finalize boundary, filter ordering |

최소 tag는 아래 정도면 충분하다.

- `phase=build|update|query_result|repair`
- `owner=persisted|intermediate`
- `op=or|xor|add|remove`
- `repair_kind=repairAfterLazy|toEfficientContainer|none`
- `repair_scope=key_local|bitmap_wide|run_native|none`
- `temp_type=lazy_bitmap|lazy_run|none`
- `before_type`, `after_type`, `high_key`

sampled event 예시는 아래처럼 잡을 수 있다.

```json
{
  "bitmap_id": "country in (KR,JP,TW)",
  "phase": "repair",
  "owner": "intermediate",
  "op": "or",
  "repair_kind": "repairAfterLazy",
  "repair_scope": "bitmap_wide",
  "temp_type": "lazy_bitmap",
  "before_type": "bitmap",
  "after_type": "array",
  "high_key": 183,
  "cpu_ns": 23100,
  "bytes_rewritten": 8192
}
```

반대로 ingest event라면 보통:

- `owner=persisted`
- `phase=update`
- `repair_kind=none`

이 된다.  
같은 `bitmap -> array`라도 두 이벤트는 원인이 전혀 다르다.

## 5. `repairAfterLazy` hotspot을 따로 profiling하는 실전 방법

항상 켜둘 metric은 아래처럼 나누는 편이 해석이 쉽다.

| metric group | 예시 metric | 왜 필요한가 |
|---|---|---|
| repair 전용 카운터 | `roaring_repair_after_lazy_total{op,repair_scope,temp_type,final_type}` | lazy bitmap debt가 어디서 finalization되는지 바로 보인다 |
| repair CPU | `roaring_repair_after_lazy_cpu_ns_total{op,repair_scope}` | fan-in cost와 finalize cost를 분리한다 |
| temporary rewrite 크기 | `roaring_repair_bytes_rewritten_total{op,final_type}` | demotion이 작은 copy인지 큰 bitmap rewrite인지 구분한다 |
| run-native finalize | `roaring_finalize_total{op,repair_kind=\"toEfficientContainer\"}` | `XOR`/run path를 `repairAfterLazy`와 섞지 않는다 |
| intermediate 결과 타입 | `roaring_intermediate_result_type_total{op,type}` | query template가 어떤 temp 형식을 많이 만드는지 본다 |
| ingest 분리 카운터 | `roaring_container_transition_cpu_ns_total{phase=\"update\",...}` | persisted churn과 비교 baseline을 유지한다 |

파생 지표는 아래 셋이 특히 유용하다.

| 파생 지표 | 계산 예시 | 의미 |
|---|---|---|
| repair CPU share | `repair_after_lazy_cpu_ns / (query_result_cpu_ns + repair_after_lazy_cpu_ns)` | lazy merge savings보다 finalize debt가 큰지 본다 |
| temp demotion ratio | `temp_type=lazy_bitmap, final_type=array / repair_after_lazy_total` | `Array ∪ Array` overlap overshoot가 많은지 본다 |
| bitmap-wide repair ratio | `repair_scope=bitmap_wide / repair_after_lazy_total` | key-local repair보다 whole-bitmap pass가 주원인인지 본다 |

해석은 보통 이렇게 붙인다.

| 관찰 신호 | 우선 해석 | 다음 확인 |
|---|---|---|
| `repairAfterLazy` CPU만 높고 `update` churn은 안정적 | query intermediate 문제다 | wide `OR`, cache publish, `serialize` 경계, predicate ordering |
| `lazy_bitmap -> array` 비중이 높다 | overlap이 큰 array union이 bitmap 작업 형식을 과도하게 탄다 | query template, prefilter, `AND` 선행 여부 |
| `repairAfterLazy`는 낮은데 `toEfficientContainer`가 높다 | `XOR`/run-native finalize가 원인이다 | toggle batch 크기, run fragmentation |
| `repairAfterLazy`는 cache publish 직전에만 급증한다 | deferred debt가 artifact boundary에서 돌아온다 | result cache 수명, serialize 빈도 |

핵심은 "`repair`가 많다"로 끝내지 않는 것이다.  
**`repairAfterLazy`인지, run-native finalize인지, persisted ingest churn인지**를 나눠야 조치가 달라진다.

여기서 `repairAfterLazy()`가 query template 문제로 보인다면, storage layout을 만지기 전에 [Roaring Query Result Ordering Guide](./roaring-query-result-ordering-guide.md)처럼 selective base 선행과 shared intermediate reuse부터 검토하는 편이 빠르다.

## 6. 빠른 판단 문장

- `array -> bitmap -> array`가 보이면 먼저 intermediate temp bitmap 경로를 의심하고, ingest 승격 실패라고 단정하지 않는다.
- `OR`가 느릴 때는 `repair_scope=bitmap_wide` 비중을 먼저 보고, key-local repair와 섞지 않는다.
- `XOR`가 느릴 때는 `repairAfterLazy`보다 `toEfficientContainer`와 exact bitmap path를 먼저 분리한다.
- persisted bitmap이 안정적인데 p95만 튄다면 `owner=intermediate`, `phase=repair` 이벤트를 따로 본다.

## 꼬리질문

> Q: `array -> bitmap -> array` 전환이 보이면 ingest 경로에서 잘못 승격된 건가요?
> 의도: persisted churn과 temporary rewrite를 구분하는지 확인
> 핵심: 아니다. `Array ∪ Array` upper-bound overshoot처럼 query intermediate가 잠깐 bitmap 작업 형식을 빌렸다가 repair 후 다시 array로 내려오는 경우가 많다.

> Q: `XOR`가 느린데 `repairAfterLazy` counter는 낮습니다. 계측이 잘못된 건가요?
> 의도: `XOR`의 exact path와 run-native finalize를 구분하는지 확인
> 핵심: 그럴 수도 있지만, 더 흔한 이유는 `Bitmap ⊕ Bitmap` exact path나 `toEfficientContainer()` 비용이 원인이기 때문이다.

> Q: `phase=repair`만 따로 두면 충분하지 않나요?
> 의도: repair 내부 bucket을 더 나눠야 하는 이유를 아는지 확인
> 핵심: 아니다. `repairAfterLazy`와 `toEfficientContainer`를 합치면 lazy bitmap debt와 run fragmentation을 같은 문제처럼 보게 된다.

> Q: 왜 bitmap-wide repair와 key-local repair를 나눠 보나요?
> 의도: repair scope가 fan-in 구조를 드러낸다는 점을 이해하는지 확인
> 핵심: 같은 `repairAfterLazy()`라도 key-local repair는 cardinality 합산용 fast path일 수 있고, bitmap-wide repair는 wide lazy union debt가 한 번에 돌아오는 경로이기 때문이다.

## 한 줄 정리

Roaring의 intermediate repair path는 "임시 `lazy bitmap`/provisional `run`을 만들고 나중에 final container로 다시 쓴다"로 이해해야 하며, 운영 계측도 `repairAfterLazy`, `toEfficientContainer`, persisted ingest churn을 분리해서 봐야 실제 hotspot이 보인다.
