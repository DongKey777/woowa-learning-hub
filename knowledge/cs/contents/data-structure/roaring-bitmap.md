---
schema_version: 3
title: Roaring Bitmap
concept_id: data-structure/roaring-bitmap
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- roaring-bitmap
- compressed-integer-set
- exact-set-algebra
aliases:
- Roaring Bitmap
- compressed bitmap
- array bitmap run container
- exact integer set algebra
- bitmap index
- mixed density bitmap
- 16-bit container bitmap
symptoms:
- 넓은 integer id space에서 BitSet은 너무 크고 HashSet은 boxing/hash overhead가 큰 상황을 보고도 compressed exact set 구조를 고려하지 않는다
- Roaring이 상위 16-bit chunk와 하위 container로 나누어 sparse/dense/run 구간을 다르게 저장한다는 핵심을 놓친다
- container threshold, chunk boundary, lazy repair, runOptimize 같은 운영 비용을 모른 채 Roaring을 단순 압축 BitSet으로만 본다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
next_docs:
- data-structure/roaring-bitmap-selection-playbook
- data-structure/roaring-container-transition-heuristics
- data-structure/roaring-set-op-result-heuristics
- data-structure/roaring-run-formation-and-row-ordering
linked_paths:
- contents/data-structure/bloom-filter.md
- contents/data-structure/roaring-container-transition-heuristics.md
- contents/data-structure/chunk-boundary-pathologies-in-roaring.md
- contents/data-structure/roaring-set-op-result-heuristics.md
- contents/data-structure/roaring-bitmap-wide-lazy-union-pipeline.md
- contents/data-structure/roaring-andnot-result-heuristics.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/roaring-bitmap-selection-playbook.md
- contents/data-structure/compressed-bitmap-families-wah-ewah-concise.md
- contents/data-structure/bit-sliced-bitmap-index.md
- contents/data-structure/elias-fano-encoded-posting-list.md
- contents/data-structure/succinct-bitvector-rank-select.md
- contents/data-structure/hashmap-internals.md
- contents/data-structure/hyperloglog.md
confusable_with:
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
- data-structure/roaring-bitmap-selection-playbook
- data-structure/compressed-bitmap-families-wah-ewah-concise
- data-structure/elias-fano-encoded-posting-list
- data-structure/bloom-filter
forbidden_neighbors: []
expected_queries:
- Roaring Bitmap은 BitSet이나 HashSet보다 어떤 integer set workload에 맞아?
- Roaring의 상위 16-bit chunk와 array bitmap run container 구조를 설명해줘
- sparse dense mixed id 집합에서 Roaring이 exact set algebra를 빠르게 하는 이유는?
- Roaring container threshold와 chunk boundary가 운영 성능에 미치는 영향은?
- compressed bitmap을 처음 배우는데 Roaring Bitmap의 핵심 개념을 알려줘
contextual_chunk_prefix: |
  이 문서는 Roaring Bitmap을 32-bit integer set을 high-key chunk와 array/bitmap/run
  container로 나누어 저장하는 exact compressed bitmap primer로 설명한다.
  BitSet, HashSet, Bloom Filter, Elias-Fano, WAH/EWAH, container transition과
  set operation 비용을 연결한다.
---
# Roaring Bitmap

> 한 줄 요약: Roaring Bitmap은 정수 집합을 chunk와 container로 나눠 저장해, BitSet보다 훨씬 압축적이면서도 교집합 같은 집합 연산을 빠르게 수행하는 exact set 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bloom Filter](./bloom-filter.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Chunk-Boundary Pathologies In Roaring](./chunk-boundary-pathologies-in-roaring.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)
> - [Roaring ANDNOT Result Heuristics](./roaring-andnot-result-heuristics.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [Elias-Fano Encoded Posting List](./elias-fano-encoded-posting-list.md)
> - [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [HyperLogLog](./hyperloglog.md)

> retrieval-anchor-keywords: roaring bitmap, compressed bitmap, array container, bitmap container, run container, bitmap index, set intersection, inverted index, user segment, exact membership, compressed posting list, container threshold, container churn, mixed-density bitmap, run-heavy bitmap, integer set algebra, roaring transition heuristic, roaring chunk boundary pathology, 16-bit container boundary, interval list vs roaring, whole bitmap run codec vs roaring, roaring set operation result, roaring andnot result, roaring difference heuristic, lazy cardinality repair, repairAfterLazy, bitmap union heuristic, xor result container, sorted ingest roaring, roaring row ordering, bitmap id locality, run formation roaring, roaring production profiling, roaring run churn observability, boundary pressure roaring, repair debt roaring, chunk-local cardinality histogram, roaring run count profiling

## 핵심 개념

Roaring Bitmap은 "정수 ID 집합을 비트맵으로 다루고 싶지만, 전체 BitSet은 너무 큰" 상황을 위해 나온 구조다.

핵심 아이디어는 두 단계다.

- 상위 비트로 큰 구간을 나눈다
- 각 구간은 밀도에 따라 다른 container 표현을 쓴다

즉 희소한 구간은 배열처럼 저장하고, 빽빽한 구간은 비트맵처럼 저장한다.  
필요하면 연속 구간을 run container로 압축하기도 한다.

이 덕분에 Roaring Bitmap은 다음을 동시에 노린다.

- exact membership
- 빠른 교집합/합집합
- 희소/밀집 데이터 모두에서 괜찮은 공간 효율

## 깊이 들어가기

### 1. 왜 BitSet이나 HashSet만으로는 아쉽나

정수 집합을 다룰 때 단순 대안은 보통 두 가지다.

- `BitSet`: 연산이 빠르지만 id 공간이 넓으면 메모리를 너무 많이 먹음
- `HashSet<Integer>`: 희소한 집합엔 괜찮지만 boxing, pointer, hash cost가 큼

Roaring Bitmap은 "희소할 땐 배열처럼, 조밀할 땐 비트맵처럼" 행동해서 두 극단 사이를 메운다.

### 2. high bits로 chunk를 나누는 이유

보통 32비트 정수라면 상위 16비트를 key로 보고, 하위 16비트를 container 내부 값으로 저장한다.

- `userId >>> 16` : 어느 chunk인가
- `userId & 0xFFFF` : chunk 내부에서 어디인가

이렇게 하면 전체 거대한 BitSet 하나를 들고 있지 않아도 된다.  
비어 있는 구간은 container 자체가 없기 때문이다.
반대로 전역적으로는 하나의 interval이어도 `16-bit` 경계를 많이 넘으면 container header와 run restart가 누적될 수 있는데, 이 seam 비용은 [Chunk-Boundary Pathologies In Roaring](./chunk-boundary-pathologies-in-roaring.md)에서 따로 정리했다.

### 3. container 전환이 성능의 핵심이다

Roaring Bitmap 라이브러리는 보통 다음 container를 쓴다.

- Array Container: 값이 적을 때 정렬된 short 배열
- Bitmap Container: 값이 많을 때 65536비트 비트맵
- Run Container: 연속 구간이 길 때 run-length 압축

중요한 건 "한 번 정하면 끝"이 아니라 **밀도 변화에 따라 container를 바꾼다**는 점이다.  
그래서 삽입이 누적되며 sparse chunk가 dense chunk로 바뀌면 bitmap으로 승격할 수 있다.

`4096` 경계, run 수 기반 전환식, churn hotspot을 따로 보고 싶다면 [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)를 같이 읽으면 좋다.  
`AND/OR/XOR`가 결과를 어떤 container로 끝내는지, 그리고 lazy union 뒤에 왜 array로 다시 내려올 수 있는지는 [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)에서 따로 정리해 두었다.  
여러 bitmap fan-in에서 per-container lazy 결과가 `high key` merge를 거쳐 언제 whole-bitmap `repairAfterLazy()` 경계로 넘어가는지는 [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)으로 이어서 보면 된다.  
차집합 `ANDNOT`가 왜 대개 lazy repair 없이 `array/bitmap`으로 바로 끝나고, 어느 경우에만 run이 살아남는지는 [Roaring ANDNOT Result Heuristics](./roaring-andnot-result-heuristics.md)로 이어서 보면 된다.
실제 workload에서 `chunk-local cardinality histogram`, run 수, transition hotspot을 어떤 단위로 재야 하는지는 [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)로 바로 이어서 보면 된다.  
이 계측을 dashboard, alert, sampled hotspot event로 어떻게 묶어 `array/bitmap/run` churn을 잡을지는 [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)에서 따로 정리했다.

### 4. container별 비용 모델을 따로 봐야 한다

Roaring을 이해할 때는 "bitmap 하나"가 아니라  
"chunk마다 다른 자료구조가 붙는다"는 감각이 중요하다.

| container | 강한 경우 | 약한 경우 | 감각 |
|---|---|---|---|
| Array Container | 값 수가 적고 sparse한 chunk | cardinality가 커지면 binary search와 삽입 비용이 커진다 | 정렬된 short list |
| Bitmap Container | dense chunk, 반복 AND/OR, cardinality 계산 | sparse chunk에서는 65536비트 고정 공간이 부담일 수 있다 | chunk 내부 BitSet |
| Run Container | 연속 ID 구간이 길다 | 랜덤하게 끊긴 값에는 run metadata가 이득을 못 본다 | interval list에 가까운 bitmap |

즉 Roaring의 강점은 세 표현 중 하나가 최고라서가 아니라  
**chunk별로 다른 최적 표현을 고를 수 있다**는 데 있다.

### 5. Roaring과 WAH/EWAH/CONCISE의 선택축

Roaring과 WAH family는 모두 exact bitmap이지만,  
좋아하는 데이터 모양이 다르다.

- Roaring: sparse/dense/run-heavy chunk가 섞인 mixed-density workload
- WAH/EWAH/CONCISE: row ordering 덕분에 긴 clean run이 이어지는 analytic bitmap scan

즉 "run이 있다"만으로 WAH 계열을 고르는 것이 아니라,  
run이 **chunk 전반에 구조적으로 길게 이어지는가**를 봐야 한다.  
sorted ingest, row ordering, ID locality가 run 수와 active chunk 수를 어떻게 바꿔 이 경계를 이동시키는지는 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)에서 따로 이어서 보면 좋다.

### 6. backend에서 왜 많이 쓰이나

정수 ID 집합의 교집합/차집합을 자주 계산하는 시스템에서는 아주 강력하다.

- 사용자 세그먼트 교집합
- inverted index posting list
- feature flag 대상 집합
- 권한 그룹 멤버십

특히 "contains 한 번"보다 "**set operation 여러 번**"이 핵심인 경우 가치가 크다.

### 7. approximate filter와는 목적이 다르다

Bloom Filter나 Cuckoo Filter는 false positive를 허용하는 membership prefilter다.  
Roaring Bitmap은 **정확한 집합 그 자체**다.

따라서 질문이 다르다.

- Bloom/Cuckoo: "아마 없나?"
- Roaring: "정확히 누구 집합인가, 그리고 다른 집합과 얼마나 겹치나?"

## 실전 시나리오

### 시나리오 1: 사용자 세그먼트 교집합

`premium users`, `active users`, `coupon eligible users`를 각각 bitmap으로 들고 있으면  
교집합으로 즉시 대상군을 만들 수 있다.

### 시나리오 2: 검색/추천 inverted index

문서 ID 집합을 term별 posting list로 들고 있을 때,  
Roaring Bitmap은 AND/OR 조합을 빠르게 처리해 candidate generation을 줄이기 좋다.

### 시나리오 3: exact dedup / replay tracking

ID 공간이 integer로 정규화되어 있고 false positive를 허용할 수 없다면,  
approximate filter보다 roaring bitmap이 더 맞을 수 있다.

### 시나리오 4: 부적합한 경우

키가 문자열 위주이거나, 집합 연산보다 단순 key-value lookup만 중요하면  
HashMap이나 Trie 계열이 더 자연스럽다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.BitSet;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RoaringBitmapSketch {
    private static final int ARRAY_TO_BITMAP_THRESHOLD = 4096;
    private final Map<Integer, Container> containers = new HashMap<>();

    public void add(int value) {
        int high = value >>> 16;
        int low = value & 0xFFFF;

        Container container = containers.getOrDefault(high, new ArrayContainer());
        container = container.add(low);
        containers.put(high, container);
    }

    public boolean contains(int value) {
        int high = value >>> 16;
        int low = value & 0xFFFF;
        Container container = containers.get(high);
        return container != null && container.contains(low);
    }

    public int intersectionCount(RoaringBitmapSketch other) {
        int count = 0;
        for (Map.Entry<Integer, Container> entry : containers.entrySet()) {
            Container right = other.containers.get(entry.getKey());
            if (right == null) {
                continue;
            }
            BitSet leftBits = entry.getValue().toBitSet();
            leftBits.and(right.toBitSet());
            count += leftBits.cardinality();
        }
        return count;
    }

    private interface Container {
        Container add(int low);
        boolean contains(int low);
        BitSet toBitSet();
        int cardinality();
    }

    private static final class ArrayContainer implements Container {
        private final List<Integer> values = new ArrayList<>();

        @Override
        public Container add(int low) {
            int pos = Collections.binarySearch(values, low);
            if (pos < 0) {
                values.add(-pos - 1, low);
            }
            if (values.size() > ARRAY_TO_BITMAP_THRESHOLD) {
                BitmapContainer upgraded = new BitmapContainer();
                for (int value : values) {
                    upgraded.add(value);
                }
                return upgraded;
            }
            return this;
        }

        @Override
        public boolean contains(int low) {
            return Collections.binarySearch(values, low) >= 0;
        }

        @Override
        public BitSet toBitSet() {
            BitSet bitSet = new BitSet(1 << 16);
            for (int value : values) {
                bitSet.set(value);
            }
            return bitSet;
        }

        @Override
        public int cardinality() {
            return values.size();
        }
    }

    private static final class BitmapContainer implements Container {
        private final BitSet bitSet = new BitSet(1 << 16);

        @Override
        public Container add(int low) {
            bitSet.set(low);
            return this;
        }

        @Override
        public boolean contains(int low) {
            return bitSet.get(low);
        }

        @Override
        public BitSet toBitSet() {
            return (BitSet) bitSet.clone();
        }

        @Override
        public int cardinality() {
            return bitSet.cardinality();
        }
    }
}
```

이 코드는 핵심 발상만 보여준다.  
실제 Roaring Bitmap은 run container, SIMD 최적화, container 간 직접 연산 등으로 훨씬 더 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Roaring Bitmap | exact membership과 집합 연산이 빠르고 압축 효율이 좋다 | 정수 ID 정규화가 필요하고 구현 개념이 더 복잡하다 | 세그먼트, posting list, 집합 교집합이 중요할 때 |
| WAH/EWAH/CONCISE | 긴 run이 많은 bitmap scan과 exact bitwise combine에 강하다 | mixed-density 적응력과 random membership workload 적합성은 Roaring보다 떨어질 수 있다 | warehouse bitmap index, run-heavy flags |
| BitSet | 구현이 단순하고 dense 데이터에서 빠르다 | sparse하고 큰 ID 공간에서는 메모리 낭비가 크다 | ID 공간이 작고 조밀할 때 |
| HashSet<Integer> | 직관적이고 범용적이다 | boxing, 포인터, hash overhead가 크다 | 집합 연산보다 단순 membership이 중요할 때 |
| Bloom Filter | 메모리를 매우 적게 쓰는 prefilter다 | false positive가 있어 exact set이 아니다 | 없음을 빨리 걸러내는 전방 필터가 필요할 때 |

중요한 질문은 "이게 집합인지"보다 "이 집합들 사이의 연산이 핵심인지"다.

## 꼬리질문

> Q: Roaring Bitmap이 Bloom Filter를 대체하나요?
> 의도: exact set과 approximate filter를 구분하는지 확인
> 핵심: 아니다. Bloom은 전방 필터, Roaring은 정확한 집합 저장/연산 구조다.

> Q: 왜 container를 여러 타입으로 나누나요?
> 의도: 희소/밀집 데이터 적응 전략 이해 확인
> 핵심: sparse chunk와 dense chunk의 최적 표현이 다르기 때문이다.

> Q: HashSet보다 유리한 순간은 언제인가요?
> 의도: membership과 set operation의 차이를 보는지 확인
> 핵심: exact 교집합/합집합을 자주 계산하고, 정수 ID가 많을 때다.

> Q: run container가 있으면 WAH/EWAH류를 따로 볼 필요가 없나요?
> 의도: adaptive container와 word-aligned run compression의 층위를 구분하는지 확인
> 핵심: 아니다. Roaring의 run container는 chunk 단위 적응 전략의 일부이고, WAH/EWAH/CONCISE는 bitmap 전체를 word-aligned run compression 관점에서 스캔하는 계열이다.

## 한 줄 정리

Roaring Bitmap은 정수 집합을 chunk별로 적응형 압축해, exact membership과 대규모 집합 연산을 모두 실무적으로 빠르게 만드는 자료구조다.
