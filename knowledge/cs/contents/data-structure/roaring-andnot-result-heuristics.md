# Roaring ANDNOT Result Heuristics

> 한 줄 요약: Java `RoaringBitmap` 계열의 `ANDNOT`/difference는 결과가 줄어드는 연산이라 `OR/XOR`처럼 lazy bitmap repair를 거의 만들지 않고, 대개 exact cardinality를 유지한 채 `array` 또는 `bitmap`으로 바로 끝난다. run 결과가 적극적으로 경쟁하는 경로는 주로 `Run - small Array`와 `Run - Run`뿐이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)

> retrieval-anchor-keywords: roaring andnot result, roaring difference heuristic, roaring set difference result, roaring minus container heuristic, roaring andnot array bitmap run, roaring subtract output container, roaring shrinkage bypass lazy repair, roaring difference repairAfterLazy, roaring difference exact cardinality, roaring bitmap andnot array demotion, roaring bitmap andnot run demotion, roaring run andnot array threshold 32, lazyandNot runcontainer, toEfficientContainer difference, roaring run minus bitmap no run output, roaring run minus run heuristic, roaring difference observability, roaring remove result container

## 핵심 개념

`ANDNOT`는 `AND/OR/XOR`와 달리 **방향성이 있는 연산**이다.  
즉 `left.andNot(right)`에서 heuristic은 "왼쪽 container를 어떤 작업 형식으로 풀 것인가"에 더 크게 좌우된다.

여기서 중요한 차이가 하나 더 있다.

- `OR/XOR`는 결과가 커지거나 토글되므로 lazy bitmap을 먼저 만들고 나중에 `repairAfterLazy()`로 cardinality를 복구하는 경로가 있다
- `ANDNOT`는 비트를 추가하지 않고 지우기만 하므로, 구현이 exact cardinality를 유지하거나 exact bitcount를 먼저 계산하기 쉽다

그래서 Java `RoaringBitmap`의 difference 경로는 대체로:

- array면 그냥 array로 끝나고
- bitmap이면 지우면서 exact cardinality를 업데이트한 뒤 바로 `array/bitmap`을 결정하고
- run-native 경로여도 `repairAfterLazy()`가 아니라 `toEfficientContainer()`로 `run/array/bitmap`을 비교한다

즉 difference의 핵심은 **lazy repair debt보다 shrink-driven direct demotion**이다.

## 빠른 판단표

| 입력 조합 | 먼저 가정하는 결과 | 최종 표현 규칙 | `repairAfterLazy()` |
|---|---|---|---|
| `Array - Array` | Array | Array | 없음 |
| `Array - Bitmap` | Array | Array | 없음 |
| `Array - Run` | Array | Array | 없음 |
| `Bitmap - Array` | Bitmap | `<= 4096`면 Array, 아니면 Bitmap | 없음 |
| `Bitmap - Bitmap` | exact cardinality 계산 후 Array/Bitmap | `<= 4096`면 Array, 아니면 Bitmap | 없음 |
| `Bitmap - Run` | Bitmap | `<= 4096`면 Array, 아니면 Bitmap | 없음 |
| `Run - small Array` | Run | `toEfficientContainer()`로 Run/Array/Bitmap 선택 | 없음. run size 비교만 한다 |
| `Run - large Array` | `lhs.cardinality <= 4096`면 Array, 아니면 Bitmap/Array path | Array 또는 Bitmap | 없음 |
| `Run - Bitmap` | `lhs.cardinality <= 4096`면 Array, 아니면 Bitmap | `<= 4096`면 Array, 아니면 Bitmap | 없음 |
| `Run - Run` | Run | `toEfficientContainer()`로 Run/Array/Bitmap 선택 | 없음. run size 비교만 한다 |

여기서 `small Array`는 Java 구현 기준으로 대략 `rhs.cardinality < 32`인 shortcut을 뜻한다.

## 1. 왜 difference는 lazy repair를 거의 만들지 않나

`repairAfterLazy()`가 query-time 비용으로 부각되는 대표 경로는 보통 `OR/XOR` 쪽이다.  
즉 "invalid cardinality를 가진 임시 bitmap을 나중에 고친다"는 패턴은 difference보다 union/toggle 계열에서 훨씬 자주 나타난다.

반면 `ANDNOT`는 shrink-only 연산이라 다음 세 방식으로 exactness를 바로 확보한다.

- `Bitmap - Array`: 지우는 비트마다 cardinality를 즉시 감소시킨다
- `Bitmap - Bitmap`: `bitcount(left & ~right)`로 `newCardinality`를 먼저 정확히 계산한다
- `Bitmap - Run`: reset한 구간의 기존 1-bit 수를 세고 그만큼 cardinality를 즉시 갱신한다

결과적으로 difference에서 중요한 비용은:

- lazy repair CPU가 아니라
- `bitmap -> array` direct demotion
- `run -> bitmap/array` direct conversion
- `toEfficientContainer()`가 일으키는 final representation 선택

이다.

즉 운영에서 `ANDNOT`가 느릴 때는 `repairAfterLazy()` counter보다  
container 재작성과 exact bitcount path를 먼저 의심하는 편이 맞다.

## 2. 왼쪽이 Array면 결과는 항상 Array다

이 부분은 가장 단순하다.

- `Array - Array`
- `Array - Bitmap`
- `Array - Run`

모두 결과 cardinality가 원래 array 크기를 넘을 수 없다.  
그리고 array container는 애초에 `<= 4096` invariant를 가진다.

그래서 difference 이후 결과가 bitmap이나 run으로 승격될 이유가 없다.  
이 경로들은 모두 **lazy repair 없이 exact array**로 끝난다.

## 3. 왼쪽이 Bitmap이면 결과는 Array/Bitmap만 본다

bitmap-left difference는 Java 구현에서 가장 "정확하고 단순한" 편이다.

### `Bitmap - Array`

- bitmap을 clone한 뒤 array 원소를 하나씩 clear한다
- clear된 비트 수만큼 cardinality를 즉시 줄인다
- 마지막 cardinality가 `<= 4096`면 Array로 내리고, 아니면 Bitmap으로 유지한다

즉 결과가 많이 줄어든 경우에도 **즉시 array demotion**이 일어나며, lazy bitmap repair가 끼지 않는다.

### `Bitmap - Bitmap`

이 경로는 먼저 `left & ~right`의 exact cardinality를 전부 센다.  
그다음:

- `> 4096`면 Bitmap materialization
- `<= 4096`면 `fillArrayANDNOT(...)`로 바로 Array 생성

이 된다.

중요한 포인트는 difference 결과가 run-heavy shape여도, bitmap-left path는 보통 **run을 다시 경쟁시키지 않는다**는 점이다.

### `Bitmap - Run`

run 구간을 bitmap에서 reset하면서 지운 1-bit 개수만큼 cardinality를 즉시 갱신한다.  
그리고 마지막에:

- `> 4096`면 Bitmap
- `<= 4096`면 Array

로 끝난다.

즉 길게 이어진 구간을 통째로 빼서 결과가 "두세 개 큰 interval"처럼 보여도,  
이 경로는 대개 non-full `RunContainer`를 자동 선택하지 않는다.

## 4. 왼쪽이 Run일 때만 run 경쟁이 일부 살아 있다

difference에서 run 결과가 자연스럽게 나오는 경로는 사실 많지 않다.  
하지만 왼쪽이 이미 run이면 두 군데에서 run 경쟁이 남아 있다.

### `Run - small Array`: 작은 hole punching이면 run-first

Java 구현은 `rhs.cardinality < 32`일 때만 먼저 `lazyandNot(x)`로 provisional run을 만든다.  
그다음 `repairAfterLazy()`가 아니라 `toEfficientContainer()`를 호출해:

- run serialized size
- array serialized size
- bitmap serialized size

를 비교한다.

즉 작은 point delete 몇 개로 run을 조금만 깨뜨리는 상황은:

- 그대로 Run에 남을 수도 있고
- cardinality가 작으면 Array가 될 수도 있고
- run 수가 늘면 Bitmap으로 갈 수도 있다

핵심은 **메서드 이름에 `lazy`가 있어도 invalid cardinality repair debt를 남기진 않는다**는 점이다.

### `Run - large Array`: array 크기가 커지면 run-first를 포기한다

오른쪽 array가 `32` 이상이면 구현은 "run을 미리 가정할 가치가 낮다"고 본다.

- 왼쪽 run cardinality가 이미 `<= 4096`면 exact Array difference를 바로 만든다
- 그보다 크면 왼쪽 run을 먼저 `Bitmap/Array`로 풀고, 그 컨테이너에 `iandNot(array)`를 적용한다

이 말은 곧:

- 결과가 여전히 interval-heavy여도
- large-array subtraction 경로에서는
- non-full run이 다시 선택되지 않을 수 있다

는 뜻이다.

즉 difference의 shrink-only 성질이 있어도, **run 경쟁은 rhs type과 threshold에 의해 일찍 끊길 수 있다**.

### `Run - Bitmap`: run-friendly shape여도 결과는 대개 Array/Bitmap

이 경로는 더 보수적이다.

- 왼쪽 run cardinality가 `<= 4096`면 exact Array를 만든다
- 그보다 크면 bitmap 결과를 기대하고 계산한다
- 마지막 cardinality가 `<= 4096`면 Array로 내리고, 아니면 Bitmap으로 유지한다

즉 `Run - Bitmap`은 왼쪽이 run이라도 **run을 최종 후보로 다시 올리지 않는다**.  
긴 연속 구간 하나에서 bitmap mask를 빼서 결과가 interval 둘로 갈라져도, 최종 출력은 bitmap으로 남을 수 있다.

### `Run - Run`: difference에서 run이 가장 자연스러운 경로

양쪽이 모두 run이면 구현은 run 차집합을 직접 만든 뒤 `toEfficientContainer()`를 호출한다.

그래서:

- 연속 구간 몇 개로 깔끔하게 남으면 Run 유지
- cardinality가 작아지면 Array
- run 수가 폭증하면 Bitmap

으로 정리된다.

difference에서 "run 결과가 잘 살아남는" 경우를 찾는다면 보통 이 경로가 가장 대표적이다.

## 5. result shrinkage가 `repairAfterLazy()`를 우회하는 대표 상황

### 상황 1: `Bitmap - Bitmap`이 dense에서 sparse로 급감한다

- 왼쪽은 dense bitmap
- 오른쪽이 많은 비트를 지워 `newCardinality <= 4096`
- 구현은 exact bitcount를 이미 알고 있다
- 결과는 바로 Array로 materialize된다

즉 "일단 lazy bitmap으로 두고 나중에 repair"가 아니라  
**감소한 cardinality를 바로 확정하고 array로 내린다**.

### 상황 2: `Bitmap - Run`이 interval-heavy shape를 만들어도 run으로 안 간다

- dense bitmap에서 중간 구간 하나를 크게 제거한다
- 결과는 큰 interval 두 개처럼 보인다
- 하지만 bitmap-left difference 경로는 run을 재경쟁시키지 않는다
- cardinality가 `> 4096`면 Bitmap으로 끝난다

즉 shrinkage는 있었지만, 그 shrinkage가 run 재평가로 이어지지는 않는다.

### 상황 3: `Run - Array`에서 작은 hole batch만 run-native shortcut을 탄다

- 긴 run 하나에서 점 몇 개만 빼면 `rhs < 32` shortcut으로 run-first가 가능하다
- 점 삭제가 커져 `rhs >= 32`가 되면 run-first를 포기하고 bitmap/array path로 간다

즉 difference는 "줄어드는 연산"이지만,  
**run을 끝까지 지켜 주는 연산**은 아니다.

## 6. 실전에서 기억할 문장 세 개

- `ANDNOT`는 shrink-only라서 `repairAfterLazy()` debt보다 exact cardinality 기반 direct demotion이 더 중요하다.
- bitmap-left difference는 거의 항상 `array vs bitmap`만 보고 끝나며, 결과가 run-heavy여도 non-full run을 자동 선택하지 않을 수 있다.
- run 결과가 적극적으로 살아남는 path는 주로 `Run - small Array`와 `Run - Run`이다.

## 꼬리질문

> Q: 왜 `ANDNOT`는 `OR/XOR`보다 lazy repair 얘기가 덜 나오나요?
> 의도: shrink-only 성질과 exact cardinality path를 연결하는지 확인
> 핵심: difference는 비트를 지우기만 하므로 cardinality를 즉시 갱신하거나 exact bitcount를 먼저 계산하기 쉬워, invalid lazy bitmap을 오래 들고 갈 이유가 적다.

> Q: `Bitmap - Run` 결과가 큰 interval 두 개면 run이 더 자연스럽지 않나요?
> 의도: 경로별 후보 탐색 범위가 다르다는 점을 이해하는지 확인
> 핵심: shape만 보면 그럴 수 있지만, bitmap-left difference 경로는 보통 run을 재경쟁시키지 않고 `array/bitmap`만 결정한다.

> Q: `Run - Array`는 항상 run 결과를 먼저 가정하나요?
> 의도: 작은-array shortcut과 threshold를 기억하는지 확인
> 핵심: 아니다. Java 구현은 오른쪽 array가 아주 작을 때만 run-first shortcut을 쓰고, 그보다 크면 array/bitmap path로 빨리 내려간다.

> Q: `lazyandNot()`가 있으니 결국 `repairAfterLazy()`를 부르지 않나요?
> 의도: run-native lazy path와 bitmap lazy repair를 구분하는지 확인
> 핵심: 아니다. 이 경로는 invalid cardinality를 남기는 bitmap lazy repair가 아니라, provisional run 뒤 `toEfficientContainer()`로 size 비교를 수행한다.

## 한 줄 정리

Roaring의 `ANDNOT` 결과 타입은 "차집합도 set-op니까 lazy repair가 있겠지"라고 보면 자주 틀리고, 실제로는 shrink-only exact cardinality 경로가 대부분이라 `bitmap -> array` direct demotion과 `Run - small Array`/`Run - Run`의 제한적 run 경쟁을 같이 봐야 정확하다.
