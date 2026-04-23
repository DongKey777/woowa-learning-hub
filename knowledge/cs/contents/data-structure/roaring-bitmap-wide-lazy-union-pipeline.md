# Roaring Bitmap-Wide Lazy Union Pipeline

> 한 줄 요약: Roaring의 lazy union은 먼저 **같은 `high key` 안에서 container별 비트 패턴만 정확히 합치고 cardinality/최종 표현 선택을 미루는** 방식으로 진행되며, 그 결과가 bitmap 전체로 쌓인 뒤에는 `repairAfterLazy()` 경계를 지나야 `getCardinality`, `rank`, `select`, `serialize` 같은 bitmap-level 소비자가 안전해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Lazy Union And Repair Costs](./roaring-lazy-union-and-repair-costs.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Roaring ANDNOT Result Heuristics](./roaring-andnot-result-heuristics.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)

> retrieval-anchor-keywords: roaring lazy union pipeline, roaring bitmap-wide lazy union, roaring whole-bitmap repair, roaring per-container lazy result, roaring lazyor, roaring naivelazyor, roaring lazyorfromlazyinputs, repairAfterLazy bitmap level, repairAfterLazy vs runOptimize, lazy union finalize timing, query result runOptimize, roaring highlowcontainer merge, roaring horizontal_or, roaring priorityqueue_or, roaring or cardinality pipeline, invalid cardinality roaring, lazy bitmap repair boundary, rank select lazy union, serialize lazy bitmap, cardinality-sensitive roaring consumer, fan-in bitmap union roaring, provisional bitmap container roaring

## 핵심 개념

Roaring의 lazy union을 이해할 때 가장 중요한 구분은 두 층이다.

- **container 층**: 같은 `high key`를 공유하는 두 container를 OR 해서 비트 패턴은 바로 만든다.
- **bitmap 층**: 어떤 `high key`가 겹쳤는지 정렬 merge로 맞춰 전체 `highLowContainer`를 조립한다.

여기서 lazy라는 말은 "비트가 틀리다"가 아니다.

- 비트 패턴 자체는 이미 union 결과다.
- 늦춰지는 것은 `cardinality`와 최종 container 표현(`array/bitmap/full run`)이다.

즉 lazy union 뒤 bitmap 전체는 보통 **정확한 비트 패턴 + 일부 invalid cardinality를 가진 container들의 모음**이다.

## 1. 실제로 lazy해지는 것은 무엇인가

Java `RoaringBitmap` 계열에서 `BitmapContainer.lazyOR(...)`나 `lazyIOR(...)`는 대개 아래처럼 동작한다.

1. word-by-word OR로 16-bit chunk의 bit pattern을 만든다.
2. `cardinality = -1` 같은 invalid 표식을 남긴다.
3. `array`로 내릴지, full chunk를 `RunContainer.full()`로 바꿀지는 나중으로 미룬다.

중요한 건 lazy해지는 범위가 **겹친 key의 결과 container만**이라는 점이다.

- 왼쪽에만 있는 container는 그대로 복사된다.
- 오른쪽에만 있는 container도 그대로 복사된다.
- 같은 key에서 실제 union을 수행한 container만 provisional 상태가 될 수 있다.

그래서 lazy union 결과 bitmap은 처음부터 끝까지 전부 invalid한 것이 아니라, `exact container`와 `lazy container`가 섞인 mixed 상태로 굴러간다.

## 2. bitmap-level로 어떻게 roll up 되나

`RoaringBitmap.lazyor(x1, x2)` 계열은 `highLowContainer`를 key-sorted merge로 훑는다.

- `key`가 같으면: 두 container에 `lazyOR`를 적용해 결과를 append한다.
- 한쪽에만 있는 `key`면: 그 container를 exact 상태로 append/copy 한다.
- bitmap-level에서는 global cardinality를 즉시 계산하지 않는다.

감각은 아래 파이프라인으로 잡으면 된다.

```text
same-key container pair
  -> lazyOR / lazyIOR
  -> provisional container(cardinality invalid 가능)
  -> highLowContainer에 append
  -> 다른 key들과 함께 bitmap 전체 결과 형성
  -> 필요 시 repair boundary 통과
```

이 구조 덕분에 Roaring은 bitmap 전체를 한 번에 32-bit BitSet처럼 materialize하지 않고도, key별로 필요한 부분만 lazy하게 합칠 수 있다.

## 3. repair 시점은 aggregation 전략에 따라 다르다

### `horizontal_or`: key-local repair

`FastAggregation.horizontal_or(...)`는 여러 bitmap에서 **같은 key의 container들만 모아** lazy OR를 누적한 뒤, 그 `newc` 하나에만 `repairAfterLazy()`를 호출하고 결과 bitmap에 append한다.

즉 repair 범위가:

- bitmap 전체가 아니라
- 지금 막 완성한 key 하나

다.

이 경로는 "container fan-in을 key 단위로 끝내고 바로 확정"하는 방식이라, 최종 bitmap에 들어가는 container는 이미 repaired 상태다.

### `naive_or` / `priorityqueue_or`: whole-bitmap repair

반면 아래 경로는 여러 provisional container를 bitmap 전체에 들고 다닌다.

- `FastAggregation.naive_or(...)`
- `FastAggregation.priorityqueue_or(...)`
- `RoaringBitmap.lazyor(...)`
- `RoaringBitmap.lazyorfromlazyinputs(...)`

특히 `priorityqueue_or(...)`는 임시 결과들끼리도 다시 lazy merge한다.  
그래서 중간 bitmap은 "이미 lazy였던 container + 새로 lazy가 된 container"를 함께 품은 채 여러 라운드를 지난다.

이때는 마지막에 한 번:

```text
for each container in bitmap:
  c = c.repairAfterLazy()
```

형태의 bitmap-wide pass를 돌려야 한다.

즉 per-container lazy 결과가 bitmap-level로 roll up 된다는 말은, **lazy 상태가 key별로 흩어져 bitmap 전체에 누적될 수 있다**는 뜻이다.

## 4. whole-bitmap repair가 꼭 필요한 경계

lazy union 결과 bitmap을 계속 lazy union에 재투입하는 것은 괜찮다.  
비트 패턴은 이미 맞기 때문이다.

문제가 되는 것은 **bitmap-level consumer가 container cardinality를 믿는 순간**이다.

### repair가 필요한 대표 작업

- `getCardinality()` / `getLongCardinality()`
- `cardinalityExceeds(...)`
- `rank(...)` / `rangeCardinality(...)`
- `select(...)`
- `limit(...)`
- `serialize(...)`

이 메서드들은 bitmap 전체를 돌며:

- container cardinality를 누적하거나
- prefix cardinality를 기준으로 어느 container에 답이 있는지 고르거나
- serialization header에 container cardinality를 기록한다.

lazy union 직후에는 일부 container가 `cardinality = -1` 상태일 수 있으므로, 이 경계 전에 whole-bitmap `repairAfterLazy()`가 필요하다.

### repair 없이도 이어갈 수 있는 작업

- 추가 lazy union fan-in
- `high key` 정렬 merge 자체
- 대략적인 메모리 추정 기반 merge ordering
- membership/iterator처럼 bit pattern만 직접 읽는 소비

즉 lazy union의 안전 경계는 "읽기"와 "counting/order-aware reading" 사이에 있다.

## 5. 왜 `rank`/`select`가 특히 bitmap-level repair를 요구하나

container 내부만 보면 lazy bitmap도 비트 패턴은 정확하다.  
그래서 container 하나만 놓고 보면 `select`나 iterator가 돌아갈 여지는 있다.

하지만 bitmap-level `rank`/`select`는 먼저:

- 앞선 container들의 cardinality를 누적하고
- 어느 `high key` container에 답이 들어 있는지 결정한 뒤
- 그 container 안으로 내려간다.

즉 깨지는 지점은 container 내부가 아니라 **container 경계 사이의 prefix sum**이다.

이 차이를 놓치면 "비트는 맞는데 왜 `select`가 위험하지?"가 헷갈린다.

## 6. OR cardinality만 필요하면 whole-bitmap repair를 피할 수도 있다

`FastAggregation.horizontalOrCardinality(...)` 같은 경로는 bitmap 전체 결과를 오래 들고 있지 않고:

1. key 하나에 대한 lazy union을 만든다.
2. 그 key의 container만 `repairAfterLazy()` 한다.
3. `getCardinality()`를 더한다.
4. 다음 key로 넘어간다.

즉 "union 결과의 exact cardinality"가 필요하더라도, 항상 whole-bitmap repair가 필요한 것은 아니다.  
**이미 lazy bitmap 객체를 만들어 둔 뒤 그 객체를 cardinality-sensitive 하게 쓰려는 경우**에 whole-bitmap pass가 필요한 것이다.

다만 여기서 끝났다고 해서 non-full run까지 다시 검토한 것은 아니다.  
결과 bitmap을 cache/serialize할 final artifact로 넘길지 판단하는 시점의 `runOptimize()` 타이밍은 [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)에서 별도로 보면 덜 헷갈린다.

실전 감각은 이렇게 잡으면 된다.

- 결과 bitmap 자체를 재사용해야 한다: lazy aggregate 후 마지막에 bitmap-wide repair
- cardinality 숫자만 필요하다: key-local repair + sum 경로가 더 낫다

## 7. 운영에서 보이는 비용도 이 경계에 묶인다

관측상 lazy union 비용은 두 덩어리로 나뉜다.

- `query_result` 단계: key merge + lazy container OR
- `repair` 단계: invalid cardinality 복구 + `array/full run` 정규화

그래서 p95가 튈 때는 단순히 "OR가 느리다"보다:

- fan-in 자체가 비싼지
- 아니면 마지막 whole-bitmap repair가 비싼지

를 분리해서 봐야 한다.

이 운영 관점은 [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)와 [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)로 바로 이어진다.

## 빠른 판단표

| 지금 하려는 일 | whole-bitmap repair 필요? | 이유 |
|---|---|---|
| lazy union 결과에 bitmap 하나를 더 OR 한다 | 보통 불필요 | bit pattern만 있으면 다음 lazy merge를 이어갈 수 있다 |
| union 결과의 exact cardinality를 읽는다 | 필요 | bitmap-level 합산이 container cardinality를 신뢰한다 |
| `rank`나 `select`를 호출한다 | 필요 | prefix cardinality가 틀리면 container 선택이 깨진다 |
| 결과를 serialize 한다 | 필요 | header에 container cardinality를 기록해야 한다 |
| key별 OR cardinality만 합산한다 | whole-bitmap repair는 불필요 | key-local repair 후 즉시 합산하면 된다 |

## 꼬리질문

> Q: lazy union 뒤에도 비트 패턴은 맞는데 왜 `getCardinality()`는 바로 부르면 안 되나요?
> 의도: bit correctness와 cardinality metadata correctness를 분리하는지 확인
> 핵심: `getCardinality()`는 bitmap 전체를 돌며 container cardinality를 더하는데, lazy container는 그 값이 아직 invalid일 수 있다.

> Q: `horizontal_or`는 왜 마지막 whole-bitmap `repairAfterLazy()`가 없어도 되나요?
> 의도: key-local repair와 bitmap-wide repair를 구분하는지 확인
> 핵심: 같은 key의 fan-in이 끝날 때마다 그 container 하나를 바로 repair해서 append하므로, 결과 bitmap에는 provisional container가 남지 않는다.

> Q: `priorityqueue_or`는 왜 중간중간 repair하지 않고 끝까지 미루나요?
> 의도: lazy aggregate의 목적을 이해하는지 확인
> 핵심: merge tree 중간마다 exact cardinality와 표현 선택을 확정하면 repeated repair cost가 커지므로, 임시 bitmap끼리도 lazy 상태로 합친 뒤 마지막 한 번에 정리한다.

> Q: `serialize`도 cardinality-sensitive 작업으로 봐야 하나요?
> 의도: cardinality가 단순 count API에만 쓰이지 않는다는 점을 아는지 확인
> 핵심: 그렇다. Roaring serialization header는 container cardinality를 기록하므로 lazy 상태를 그대로 내보내면 메타데이터가 틀어진다.

## 한 줄 정리

Roaring의 bitmap-wide lazy union pipeline은 "key가 겹친 container들만 먼저 lazy하게 합치고, 그 provisional 결과들을 bitmap 전체에 누적한 뒤, exact count나 prefix-aware API를 만나기 직전에 `repairAfterLazy()` 경계를 한 번 지난다"로 이해하면 가장 덜 헷갈린다.
