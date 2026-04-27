# BigDecimal Key 정책 30초 체크리스트

> 한 줄 요약: `BigDecimal`을 key로 쓸 때는 "`1.0`과 `1`을 같은 key로 볼지"를 먼저 정하고, 정규화 위치와 테스트 케이스를 PR 전에 같이 점검해야 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
> - [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./bigdecimal-hashset-treeset-contains-mini-drill.md)
> - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)

> retrieval-anchor-keywords: bigdecimal key policy checklist, bigdecimal 1.0 vs 1 key policy, bigdecimal normalize key before map, bigdecimal map key rule, bigdecimal pr checklist, bigdecimal equals compareTo key policy, bigdecimal stripTrailingZeros key normalization, bigdecimal test cases 1.0 1 1.00, java bigdecimal map key beginner, 자바 bigdecimal key 정책, 자바 bigdecimal 1.0 1 동등성 정책, 자바 bigdecimal map key 체크리스트, 자바 bigdecimal 정규화 정책, 자바 bigdecimal 테스트 항목

## 먼저 잡을 mental model

초급자 기준으로는 이 한 줄이 제일 중요하다.

> `BigDecimal` key 문제는 "숫자 계산" 문제가 아니라 "같은 key를 무엇으로 볼지"를 정하는 문제다.

- `new BigDecimal("1.0").equals(new BigDecimal("1"))`는 `false`다
- `new BigDecimal("1.0").compareTo(new BigDecimal("1")) == 0`는 `true`다
- 그래서 `Map`/`Set`에 넣는 순간 정책이 없으면 조회와 중복 결과가 갈릴 수 있다

## 10초 비교표

| 질문 | 정규화 안 함 | 입력 경계에서 한 번 정규화 |
|---|---|---|
| `HashMap`에 `"1.0"` 저장 후 `"1"`로 조회 | 못 찾을 수 있음 | 같은 key로 맞추기 쉬움 |
| `HashSet`에 `"1.0"`, `"1"` 추가 | 둘 다 남을 수 있음 | 하나로 모으기 쉬움 |
| PR 리뷰 포인트 | 호출자마다 해석이 달라짐 | 생성/입력 지점 한 곳만 보면 됨 |

여기서 핵심은 "무조건 정규화"가 아니라 "정규화할 거면 한 곳에서만"이다.

## PR 전 30초 체크리스트

### 1. 동등성 정책을 문장으로 적었나

아래 둘 중 하나는 PR 설명이나 코드 주석에 바로 적을 수 있어야 한다.

- "`1.0`, `1.00`, `1`을 같은 key로 본다"
- "`1.0`과 `1`의 scale 차이도 의미가 있으므로 다른 key로 본다"

이 문장이 없으면 리뷰어마다 기대하는 `Map` 동작이 달라진다.

### 2. 정규화 여부를 한 곳에서만 처리하나

| 선택 | 초급자용 규칙 |
|---|---|
| 정규화한다 | 입력 경계/팩토리/생성 함수 한 곳에서만 처리 |
| 정규화하지 않는다 | raw `BigDecimal`을 그대로 key로 쓴다는 점을 테스트와 문서에 명시 |

여기서 `stripTrailingZeros()`는 "아무 데서나 호출하는 편의 함수"가 아니라 "입구에서 표현을 맞출지"를 정하는 정책 도구에 가깝다.

## map key 사용 규칙

초급자 기준으로는 아래 3줄이면 충분하다.

1. `BigDecimal`을 `HashMap` key로 쓰면 `equals()`/`hashCode()` 기준이다.
2. `BigDecimal`을 `TreeMap` key로 쓰면 `compareTo() == 0` 기준이다.
3. 팀 정책이 없다면 `1`, `1.0`, `1.00` 조회/중복 결과가 서로 다를 수 있다.

짧은 예제로 보면 더 분명하다.

```java
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

Map<BigDecimal, String> raw = new HashMap<>();
raw.put(new BigDecimal("1.0"), "saved");

System.out.println(raw.get(new BigDecimal("1"))); // null 가능
```

반대로 입력 경계에서 정책을 통일하면 읽기가 쉬워진다.

```java
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

static BigDecimal normalizeKey(String raw) {
    return new BigDecimal(raw).stripTrailingZeros();
}

Map<BigDecimal, String> normalized = new HashMap<>();
normalized.put(normalizeKey("1.0"), "saved");

System.out.println(normalized.get(normalizeKey("1"))); // "saved"
```

## 테스트 항목 최소 세트

PR 전에 아래 3가지는 거의 항상 넣는 편이 안전하다.

| 테스트 질문 | 왜 필요한가 |
|---|---|
| 저장은 `"1.0"`인데 조회는 `"1"`일 때 어떻게 되나 | lookup 버그를 가장 빨리 잡는다 |
| `"1.0"`와 `"1.00"`를 둘 다 넣으면 size/value가 어떻게 되나 | dedupe/overwrite 정책을 확인한다 |
| 정규화 함수가 있다면 `"1"`, `"1.0"`, `"1.00"`을 같은 결과로 만드나 | 정책이 경계에서 실제로 고정되는지 확인한다 |

예시 테스트 이름도 초급자에게는 이 정도면 충분하다.

- `raw_key_map_does_not_find_1_when_saved_as_1_0()`
- `normalized_key_map_finds_1_when_saved_as_1_0()`
- `normalizer_collapses_1_1_0_1_00_to_same_key()`

## 자주 헷갈리는 포인트

- `compareTo() == 0`이면 `HashMap` 조회도 성공할 거라고 생각하기 쉽다.
- `stripTrailingZeros()`를 여러 서비스 메서드에서 제각각 호출해도 괜찮다고 생각하기 쉽다.
- `TreeMap` 조회 성공을 보고 "`HashMap`도 비슷하겠지"라고 넘기기 쉽다.
- scale이 의미 있는 도메인인데 습관적으로 정규화하면 오히려 정보를 잃을 수 있다.

## 한 번에 끝내는 PR 질문

리뷰 직전에 아래 3문장만 확인하면 된다.

- "우리 코드는 `1.0`과 `1`을 같은 key로 보나?"
- "그 정책은 입력 경계 한 곳에서만 적용되나?"
- "조회/중복/정규화 테스트가 각각 하나씩 있나?"

세 질문에 바로 답할 수 있으면 초급자용 PR 점검으로는 충분하다.

## 다음 읽기

- 개념 먼저: [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- 정규화 경계: [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- 조회 손예측: [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)

## 한 줄 정리

`BigDecimal` key PR 리뷰는 "정규화할까 말까"보다 먼저 "`1.0`과 `1`을 같은 key로 볼지"를 적고, 그 정책이 코드 한 곳과 테스트 세트에 묶여 있는지 확인하는 일이다.
