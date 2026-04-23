# Chunk-Boundary Pathologies In Roaring

> 한 줄 요약: Roaring은 16-bit container 경계마다 압축이 다시 시작되므로, 전역적으로는 몇 개 안 되는 interval이나 긴 run도 경계를 많이 가로지르면 interval list나 whole-bitmap run codec보다 header와 run 수가 훨씬 빨리 늘 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Disjoint Interval Set](./disjoint-interval-set.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)

> retrieval-anchor-keywords: chunk boundary roaring, 16-bit container boundary, high key header overhead, cross-chunk run split, interval list vs roaring, disjoint interval set vs roaring, whole bitmap run codec vs roaring, WAH EWAH vs roaring boundary, global interval split, boundary pressure roaring, straddling range roaring, active chunk header cost, run restart per container, run container boundary pathology, long range bitmap footprint, container seam overhead, full chunk tail pathology, cross-chunk interval explosion

## 핵심 개념

Roaring은 `0..65535` 단위 chunk마다 container를 하나씩 붙인다.  
이 구조 덕분에 mixed-density workload에서는 유연하지만, **논리적으로는 하나의 긴 구간**이라도 16-bit 경계를 넘는 순간 여러 개의 local object로 쪼개진다.

그래서 footprint를 볼 때는 global cardinality나 global interval 수만 보면 자주 틀린다.  
숨은 변수는 아래 두 개다.

- 몇 개의 `high key`를 건드리는가
- 각 chunk에서 run이 몇 번 다시 시작되는가

비교 감각을 식으로 적으면 다음이 더 가깝다.

- interval list: `O(global intervals)`
- whole-bitmap run codec: `O(global runs)`
- Roaring: `O(active chunks)` header/index + `Σ container_cost(i)`
- runOptimize 이후 Roaring run 수: `Σ runs_i ~= global runs + boundary crossings`

즉 Roaring에서는 `interval이 몇 개인가`보다 `interval이 65536 경계를 몇 번 넘는가`가 더 직접적인 비용 신호가 된다.

## 깊이 들어가기

### 1. 왜 같은 exact set인데 interval list나 WAH/EWAH와 모양이 달라지나

세 표현은 모두 exact semantics를 줄 수 있지만, 압축 단위가 다르다.

| 표현 | 기본 압축 단위 | 경계가 만드는 비용 |
|---|---|---|
| Disjoint Interval Set / interval list | 전역 interval | interval이 경계를 넘어도 레코드 수는 그대로일 수 있다 |
| WAH/EWAH/CONCISE | bitmap 전체 word stream의 global run | chunk seam이 없어서 긴 clean run을 그대로 유지할 수 있다 |
| Roaring | 16-bit chunk별 container | 경계를 넘을 때마다 새 high-key entry와 새 container가 필요하다 |

핵심은 Roaring의 container heuristic이 `chunk 내부`에서만 최적화된다는 점이다.  
각 chunk가 locally는 array/run/bitmap 중 최선일 수 있어도, 전역적으로는 "같은 구간이 너무 많은 chunk로 잘렸다"는 병목을 막아주지 못한다.

### 2. pathology A: 아주 짧은 interval도 seam 하나만 넘으면 container가 둘이 된다

예를 들어 전역 구간이 `[65530, 65540]`이라면 논리적으로는 interval 하나다.  
하지만 Roaring은 아래처럼 나눠 저장해야 한다.

| 표현 | 저장 조각 수 | 감각 |
|---|---|---|
| interval list | interval 1개 | 경계 자체는 보이지 않는다 |
| Roaring array | container 2개 | `65530..65535`, `65536..65540`가 다른 high key에 들어간다 |
| Roaring run | 1-run container 2개 | `runOptimize()`를 해도 seam을 넘어 run을 합칠 수 없다 |
| WAH/EWAH/CONCISE | global run 1개 | 전체 bit stream에서 한 번만 켜진 구간으로 본다 |

중요한 점은 cardinality가 겨우 `11`이어도 Roaring은 이미 active chunk가 `2`라는 것이다.  
이 경우 surprise는 "값 수가 너무 적은데 왜 metadata가 벌써 두 배로 붙지?"라는 형태로 나타난다.

### 3. pathology B: 하나의 긴 band가 여러 chunk를 가로지르면 run도 chunk마다 다시 시작된다

전역 interval `[100, 1_000_000]`을 생각해 보자.  
interval list 관점에서는 여전히 interval 1개고, whole-bitmap run codec도 전역 run 1개에 가깝게 본다.

하지만 Roaring은 대략 `16`개의 active chunk를 만든다.  
여기서 `runOptimize()`가 도와줄 수 있는 것은 각 chunk를 "1 run"이나 "full bitmap"으로 줄이는 것뿐이다.  
**16개의 chunk를 1개의 전역 run으로 합치는 일은 하지 못한다.**

그래서 긴 연속 band에서는 다음 비용이 같이 붙는다.

- high-key header/index가 chunk 수만큼 증가
- run metadata도 chunk마다 다시 시작
- full chunk가 길게 이어져도 per-container object 수는 줄지 않음

이것이 [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)가 전역 clean run에서 더 가파르게 유리해지는 이유다.

### 4. pathology C: full chunk가 길게 이어져도 "tiny tail 둘 + full middle"이 공짜가 아니다

사람은 `[65000, 400000]` 같은 범위를 보면 보통 "거의 하나의 range"로 인식한다.  
interval list도 실제로는 interval 1개면 끝난다.

Roaring에서는 다르다.

- 앞쪽 partial chunk 1개
- 뒤쪽 partial chunk 1개
- 그 사이의 full chunk 여러 개

중간 chunk가 전부 꽉 차 있어도 chunk 수만큼 container가 계속 필요하다.  
즉 "head/tail만 조금 있고 중간은 전부 full"인 모양은 Roaring에선 작아지긴 해도 **전역 range 한 개처럼 작아지지는 않는다.**

이 패턴은 range mask를 질의 중간 결과로 materialize하거나, 정렬된 row ID band를 cache/serialize할 때 footprint surprise로 자주 보인다.

### 5. pathology D: local heuristic은 맞는데 global footprint는 틀릴 수 있다

`4096` 기준과 run-size 비교식은 모두 chunk 내부의 로컬 의사결정이다.  
그래서 아래 상황이 생긴다.

- 각 chunk tail은 `300`개 값뿐이라 array가 local optimum
- 그런데 interval `200`개가 전부 boundary를 한 번씩 넘음
- 결과적으로 Roaring에는 작은 array container가 `400`개 생김

interval list는 여전히 interval `200`개면 끝난다.  
즉 **local optimum container choice != global minimum footprint**다.

같은 현상은 run container에도 생긴다.

- 전역적으로는 run `10`개뿐인 workload
- 하지만 각 run이 chunk seam을 여러 번 넘어서 `Σ runs_i`가 `10`보다 훨씬 커짐

이때 `runOptimize()`는 각 chunk 안에서는 최선이어도, seam 때문에 늘어난 run restart 자체는 없애지 못한다.

### 6. 언제 interval list나 whole-bitmap run codec 쪽이 더 자연스러워지나

아래 신호가 강하면 Roaring의 적응성보다 boundary tax가 더 중요해진다.

| 관찰 신호 | 더 자연스러운 후보 |
|---|---|
| 구간 수는 적은데 거의 모두 긴 range다 | [Disjoint Interval Set](./disjoint-interval-set.md) 같은 interval 표현 |
| read-mostly이며 global clean run이 길다 | [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md) |
| 정렬이 좋아 full chunk streak가 길지만 update는 드물다 | whole-bitmap run codec 쪽 break-even 검토 |
| sparse/dense/random set-op가 섞여 있다 | Roaring 유지가 대개 더 실용적 |

중요한 건 "Roaring이 나쁘다"가 아니다.  
Roaring은 mixed-density set algebra에 강하다.  
다만 workload가 사실상 **global interval algebra**에 더 가까우면, 16-bit seam은 구조적인 tax가 된다.

## 빠른 판단표

| 신호 | 해석 |
|---|---|
| global interval 수는 작은데 active chunk 수가 비정상적으로 크다 | boundary crossing이 footprint를 지배하고 있다 |
| runOptimize 이후에도 container 수가 거의 안 줄어든다 | 문제는 run body보다 high-key seam 수일 가능성이 높다 |
| full chunk가 길게 이어지는데 serialized size가 기대보다 크다 | whole-bitmap run codec이 더 잘 맞을 수 있다 |
| range mask/ACL band/materialized shard band가 많다 | interval 표현과의 비교를 먼저 해야 한다 |

## 꼬리질문

> Q: `runOptimize()`를 하면 긴 전역 interval도 결국 하나의 run으로 합쳐지나요?
> 의도: chunk-local 최적화와 global run codec을 구분하는지 확인
> 핵심: 아니다. `runOptimize()`는 chunk 안에서만 run container를 만들 뿐, 16-bit 경계를 넘어 run을 합치지 못한다.

> Q: 왜 cardinality가 작아도 Roaring이 의외로 커질 수 있나요?
> 의도: 값 개수와 active chunk 수를 분리해 보는지 확인
> 핵심: 값이 적어도 boundary를 많이 straddle하면 작은 container와 header가 여러 개 생기기 때문이다.

> Q: interval list와 Roaring의 가장 큰 차이는 무엇인가요?
> 의도: exact set semantics가 같아도 압축 단위가 다름을 설명할 수 있는지 확인
> 핵심: interval list는 전역 range 자체를 저장하고, Roaring은 16-bit chunk별 local representation을 저장한다.

## 한 줄 정리

Roaring의 16-bit chunking은 mixed-density workload엔 강점이지만, 긴 range나 적은 global interval이 chunk seam을 많이 넘는 workload에서는 extra header와 extra run restart 때문에 interval list나 whole-bitmap run codec보다 훨씬 비싸게 보일 수 있다.
