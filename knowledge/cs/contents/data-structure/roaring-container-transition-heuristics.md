---
schema_version: 3
title: Roaring Container Transition Heuristics
concept_id: data-structure/roaring-container-transition-heuristics
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 86
mission_ids: []
review_feedback_tags:
- roaring-container-transition
- array-bitmap-run-churn
- runoptimize-threshold
aliases:
- Roaring container transition
- array bitmap run transition
- 4096 threshold
- runOptimize timing
- container churn
- bitmap promotion demotion
- run container heuristic
symptoms:
- Roaring 성능을 전체 cardinality로만 보고 16-bit chunk별 array/bitmap/run 표현과 transition churn을 관측하지 않는다
- cardinality 4096 근처 chunk에서 array bitmap promotion/demotion이 반복되는 hotspot을 놓친다
- run container는 cardinality보다 run 수와 serialized-size 비교로 결정된다는 점을 이해하지 못한다
intents:
- troubleshooting
- deep_dive
prerequisites:
- data-structure/roaring-bitmap
next_docs:
- data-structure/roaring-set-op-result-heuristics
- data-structure/roaring-run-optimize-timing-guide
- data-structure/roaring-production-profiling-checklist
- data-structure/row-ordering-and-bitmap-compression-playbook
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/chunk-boundary-pathologies-in-roaring.md
- contents/data-structure/roaring-set-op-result-heuristics.md
- contents/data-structure/roaring-run-optimize-timing-guide.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/roaring-bitmap-selection-playbook.md
- contents/data-structure/compressed-bitmap-families-wah-ewah-concise.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/bit-sliced-bitmap-index.md
confusable_with:
- data-structure/roaring-bitmap
- data-structure/roaring-set-op-result-heuristics
- data-structure/roaring-run-optimize-timing-guide
- data-structure/chunk-boundary-pathologies-in-roaring
forbidden_neighbors: []
expected_queries:
- Roaring Bitmap에서 array container와 bitmap container는 왜 4096 cardinality 근처에서 전환돼?
- array bitmap run container transition churn을 production에서 어떻게 의심해?
- run container는 cardinality보다 run count와 serialized size가 중요하다는 뜻은?
- Roaring runOptimize를 언제 하면 좋고 hot path에서 왜 조심해야 해?
- container별 cardinality histogram과 transition counter로 Roaring 성능을 분석하는 방법은?
contextual_chunk_prefix: |
  이 문서는 Roaring Bitmap의 array/bitmap/run container transition heuristic을
  다루는 playbook이다. 4096 cardinality threshold, run count serialized-size
  comparison, runOptimize timing, container churn, production profiling을 설명한다.
---
# Roaring Container Transition Heuristics

> 한 줄 요약: Roaring의 실전 성능은 container 종류 자체보다, `array <-> bitmap <-> run` 전환이 언제 일어나고 그 재구성이 workload에 의해 얼마나 자주 반복되는지에 크게 좌우된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Chunk-Boundary Pathologies In Roaring](./chunk-boundary-pathologies-in-roaring.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)

> retrieval-anchor-keywords: roaring container transition, roaring heuristic, array container, bitmap container, run container, 4096 threshold, 2047 runs, run optimize, runOptimize timing, bulk built bitmap runOptimize, query result runOptimize, container churn, sparse dense transition, bitmap promotion, bitmap demotion, run compression, mixed density workload, serialized size heuristic, per-container cardinality, row ordering roaring, segment boundary roaring, chunk locality bitmap, roaring set op result, lazy cardinality repair, repairAfterLazy, output container heuristic, sorted ingest roaring, bitmap id locality, run count locality, roaring chunk boundary pathology, 16-bit container boundary, cross-chunk interval split, active chunk header cost, roaring production profiling, roaring run churn observability, boundary pressure, transition cpu share, cardinality histogram hotspot, transition counter

## 핵심 개념

Roaring은 전체 bitmap 하나를 압축하는 대신, 상위 16비트마다 container 하나를 붙인다.  
그래서 실제 비용은 "전체 cardinality"보다 **각 16-bit chunk가 어느 표현으로 남는가**에 따라 갈린다.

전형적인 Java Roaring / CRoaring 계열 구현 기준으로 보면:

- `Array Container`: 정렬된 16-bit 값 목록
- `Bitmap Container`: 65536비트 고정 비트셋
- `Run Container`: `(start, length)` 쌍의 run-length 표현

중요한 점은 세 container가 대칭적으로 자동 변환되는 게 아니라, **cardinality 경계와 serialized-size 비교식**으로 전환된다는 점이다.

## 깊이 들어가기

### 1. 왜 array와 bitmap의 경계가 4096인가

container 하나는 16-bit 공간, 즉 `0..65535`를 담당한다.

- array 크기: 값 하나당 2바이트이므로 `2 * cardinality`
- bitmap 크기: `65536 / 8 = 8192`바이트 고정

따라서:

- `2 * cardinality = 8192`
- `cardinality = 4096`

즉 4096개까지는 array가 bitmap과 같거나 더 작고, 4097개부터는 bitmap이 공간상 유리하다.

실전 감각은 다음처럼 잡으면 된다.

| chunk 상태 | 보통 남는 표현 | 이유 |
|---|---|---|
| `cardinality <= 4096` | Array | 2바이트씩 저장해도 8KB를 넘지 않는다 |
| `cardinality >= 4097` | Bitmap | 더 늘어날수록 array 삽입/교집합 비용보다 bitset 이점이 커진다 |

그래서 같은 chunk가:

- 값 추가로 `4096 -> 4097`을 넘으면 `array -> bitmap`
- 값 제거로 `4097 -> 4096` 아래로 내려오면 `bitmap -> array`

로 되돌아갈 수 있다.  
즉 **4096 근처는 원래 churn hotspot**이다.

### 2. run container는 cardinality보다 `run 수`가 더 중요하다

run container의 직렬화 크기는 대략 다음 식으로 본다.

- run 크기: `2 + 4 * runs` 바이트
  - run 개수용 2바이트
  - 각 run마다 `start`, `length` 2바이트씩

그래서 run은 "값이 몇 개인가"보다 "**몇 개의 연속 구간으로 묶이느냐**"로 결정된다.

비교식을 그대로 쓰면:

- run vs array: `2 + 4 * runs < 2 * cardinality`
- run vs bitmap: `2 + 4 * runs < 8192`

이 식이 주는 감각은 아래와 같다.

| 비교 대상 | run이 이기기 쉬운 조건 | 실전 해석 |
|---|---|---|
| Array | `runs`가 `cardinality / 2`보다 충분히 작다 | 값이 듬성듬성 흩어진 array는 run으로 바꿔도 이득이 없다 |
| Bitmap | `runs <= 2047` 수준 | 8KB bitset보다 작아지려면 run이 아주 많아지면 안 된다 |

그래서 논문/구현에서 자주 보이는 요약은 다음이다.

- `cardinality > 4096`인 run container는 대체로 `2047`개 이하 run이어야 의미가 있다
- `cardinality <= 4096`인 run container는 run 수가 값 수의 절반보다 충분히 작아야 한다

즉 run은 "희소"해서 좋은 게 아니라 **연속성 density가 높아야** 좋다.

### 3. 전환 비용은 한 번의 rebuild 비용으로 봐야 한다

steady-state lookup 비용만 보면 container 차이가 단순해 보이지만, 실제 운영에서는 전환 시 재구성이 더 비싸게 느껴질 수 있다.

| 전환 | 전형적 트리거 | 한 번의 전환 비용 | 이후 얻는 것 | churn 위험 |
|---|---|---|---|---|
| `array -> bitmap` | chunk cardinality가 4097 이상으로 증가 | 기존 값들을 비트셋에 다시 materialize | point add와 bitwise AND/OR가 빨라짐 | 4096 근처에서 add/remove가 왕복하면 rebuild 반복 |
| `bitmap -> array` | 삭제/차집합 후 cardinality가 4096 이하 | 비트셋을 스캔해 set bit를 다시 추출 | sparse chunk 메모리 절감 | dense였다가 빠르게 식는 hot shard |
| `array -> run` | `runOptimize` 또는 결과 container size 비교에서 run이 더 작음 | run 수 계산 + pair 재작성 | 작은 footprint와 interval형 access | 작은 hole이 많아지면 바로 이점이 사라짐 |
| `bitmap -> run` | 긴 연속 구간이 많고 run size가 8KB보다 작음 | run 수 하한/정확값 계산 + run 생성 | run-heavy chunk 압축 | range load 뒤 random delete가 누적되면 run fragmentation |
| `run -> array/bitmap` | run size가 더 이상 최저가 아님 | run을 풀어 다시 값/비트셋 생성 | random access나 set op에 더 맞는 표현 | run-optimize를 과하게 반복하면 왕복 |

핵심은 전환이 거의 항상 **O(container 크기)** 수준의 재작성 비용을 동반한다는 점이다.  
그래서 Roaring은 단순히 "현재 어떤 container인가"보다 "**얼마나 자주 표현을 갈아끼우는가**"를 봐야 한다.

### 4. 모든 전환이 point update에서만 생기진 않는다

Roaring의 container 교체는 삽입/삭제뿐 아니라 **집합 연산 결과 shape**에도 많이 좌우된다.

예를 들어:

- `bitmap ∩ bitmap` 결과가 갑자기 매우 sparse하면 결과 container는 array가 될 수 있다
- `array ∪ array`가 4096을 넘기면 결과는 bitmap이 될 수 있다
- range-heavy union 결과는 run이 더 작아질 수 있다

즉 원본 bitmap 둘은 안정적이어도, **중간 결과 container가 계속 다른 표현으로 튀는 것**이 흔하다.  
analytics 후보군 계산이나 bit-sliced filter 조합에서 이 churn이 두드러진다.

특히 `OR/XOR`는 lazy bitmap이나 lazy run을 먼저 만든 뒤 repair 단계에서 최종 타입이 바뀌는 경로가 있어, 입력 타입만 보고 결과 container를 예측하면 자주 틀린다. 이 부분은 [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)에서 연산별로 따로 풀어 두었다.

### 5. run optimize는 보통 "항상 자동"이라기보다 별도 최적화 단계에 가깝다

array와 bitmap 경계는 cardinality 때문에 연산 중 자연스럽게 자주 만난다.  
반면 run 전환은 보통 "run이 정말 더 작은가"를 따지는 별도 heuristic이 끼어든다.

이 차이는 중요하다.

- `array <-> bitmap`:
  - cardinality 경계가 명확하다
  - point update, AND/OR/XOR 결과에서 자주 일어난다
- `array/bitmap -> run`:
  - run 수를 세어봐야 한다
  - 보통 bulk build 후 `runOptimize` 같은 패스에서 이득이 커진다
  - tie면 기존 표현을 유지해 pointless churn을 줄이는 구현이 많다

특히 `bitmap -> run` 쪽은 8KB bitmap을 이길 가능성이 있는지 먼저 하한만 빠르게 세고, 가능성이 있을 때만 정확한 run 수를 다시 세는 식의 early-abandon heuristic이 자주 들어간다.  
즉 run 최적화도 "압축률 계산" 자체가 비용이어서, 그 계산을 끝까지 하지 않으려는 보호장치가 이미 들어가 있다.

bulk-built bitmap과 query result bitmap에서 이 비용을 **언제** 지불하는 편이 맞는지는 [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)에서 lifecycle boundary 기준으로 따로 정리했다.

즉 run container는 read-mostly나 bulk-built bitmap에서 특히 잘 맞고,  
**미세한 point toggle이 많은 hot chunk**에서는 오히려 자주 깨질 수 있다.

### 6. workload가 container churn을 만드는 전형적 패턴

#### 패턴 1: 4096 근처를 왕복하는 hot chunk

같은 16-bit chunk에서 활성 사용자 ID 수가 `4050~4150` 사이를 계속 오가면:

- 오전 배치에서 bitmap 승격
- 만료/삭제 배치에서 array 강등
- 다시 입력이 들어오며 bitmap 재승격

이런 왕복이 생긴다.  
이 경우 전체 bitmap cardinality는 커 보여도, 문제는 **특정 chunk의 local density 진동**이다.

#### 패턴 2: range ingest 뒤 random delete

처음에는 연속 범위를 많이 넣어서 run container가 아주 잘 맞는다.  
하지만 이후 tombstone이나 membership revoke가 랜덤하게 들어오면 run이 잘게 쪼개진다.

결과적으로:

- run 수가 늘어나 footprint 이점이 줄고
- 다음 optimize에서 array나 bitmap이 다시 더 싸질 수 있다

즉 run container는 "연속성이 생겼다"보다 "**연속성이 유지되느냐**"가 더 중요하다.

#### 패턴 3: query result shape mismatch

저장된 원본 segment는 bitmap이 안정적일 수 있다.  
하지만 질의마다 결과는:

- 어떤 날은 sparse intersection
- 어떤 날은 dense union
- 어떤 날은 range-heavy mask

처럼 바뀐다.  
그러면 intermediate container가 array/bitmap/run 사이를 계속 바꾸며 CPU를 쓴다.

### 7. 운영에서 보는 체크포인트

Roaring을 실제로 튜닝할 때는 전체 bitmap cardinality보다 아래 항목이 더 유용하다.

- chunk별 cardinality histogram
- chunk별 run 수 분포
- `4096` 근처 chunk 개수
- bulk build 이후 `runOptimize` 적용 전후 크기 차이
- 질의 실행 중 intermediate container type 분포

실전 heuristics는 보통 이렇게 정리된다.

- point update가 매우 잦은 chunk면 run optimize를 매번 돌리지 않는다
- range load나 정렬된 ingest 뒤에만 run optimize를 건다
- chunk-local cardinality가 4096 근처에서 진동하면 churn 원인으로 먼저 의심한다
- ID ordering을 바꿀 수 있다면, 연속성이 생기도록 배치해 run 수를 낮춘다

이 체크포인트를 실제 production trace에서 어떤 histogram과 counter로 남길지는 [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)에 운영 관점으로 묶어 두었다.  
그다음 단계로, 어떤 파생 지표와 alert 조합이 `array/bitmap/run` churn을 가장 빨리 드러내는지는 [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)에서 이어서 볼 수 있다.

이때 "정렬된 ingest"가 왜 chunk shape를 바꾸는지, 그리고 warehouse segment 경계가 run locality를 어떻게 깨는지는  
[Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)에서 먼저 보고,  
Roaring 관점에서 active chunk 수와 run 수가 어떻게 break-even을 흔드는지는 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)으로 이어서 보면 자연스럽다.

즉 Roaring은 "압축 자료구조"이기도 하지만, 운영 감각상으로는  
**per-container state machine**에 더 가깝게 보는 편이 맞다.

## 실전 시나리오

### 시나리오 1: 광고/세그먼트 대상 계산

사용자 segment를 chunk별로 저장할 때 일부 shard만 유독 dense해질 수 있다.  
이때 전체 사용자 수가 아니라 **dense shard가 4096을 넘나드는지**가 latency spike 원인일 수 있다.

### 시나리오 2: 컬럼형 인덱스의 bulk build

row ID가 정렬된 상태로 들어오고 값 구간이 길게 모이면 run optimize 이후 footprint가 크게 줄 수 있다.  
이 경우 run은 online toggle보다 **build/compact 시점**에 더 잘 맞는다.

### 시나리오 3: range-heavy bitmap에 hole punching이 많은 경우

초기엔 run container가 매우 좋았지만, 이후 랜덤 revoke가 누적되면 run 수가 빠르게 증가한다.  
이때 "왜 suddenly 메모리가 늘고 CPU가 오르지?"를 보려면 global density가 아니라 **run fragmentation**을 봐야 한다.

## 꼬리질문

> Q: 왜 하필 4096이 기준인가요?
> 의도: array와 bitmap의 break-even을 바이트 단위로 설명할 수 있는지 확인
> 핵심: 16-bit chunk bitmap은 8KB 고정이고, array는 값당 2바이트라서 `2 * 4096 = 8192`가 된다.

> Q: run container는 값이 적으면 항상 좋은가요?
> 의도: 희소성과 연속성을 구분하는지 확인
> 핵심: 아니다. 값이 적어도 run이 많으면 pair metadata 때문에 array가 더 싸다.

> Q: runOptimize를 매 update마다 걸면 더 좋은가요?
> 의도: static 최적 압축과 dynamic churn 비용을 분리하는지 확인
> 핵심: 아니다. point toggle이 많으면 run 수 계산과 container 재작성 때문에 오히려 churn이 커질 수 있다.

## 한 줄 정리

Roaring의 container heuristic은 "희소면 array, 조밀하면 bitmap, 연속이면 run" 정도로 끝나지 않고, `4096` 경계와 `run 수` 비교식 때문에 **workload가 local chunk에서 어떤 churn을 만드는지**까지 봐야 제대로 이해된다.
