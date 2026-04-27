# HashSet vs TreeSet Beginner Bridge

> 한 줄 요약: backend 코드에서 "중복만 막으면 되는가"와 "중복도 막고 정렬된 순서/범위도 필요하나"를 먼저 나눠 보면 `HashSet`과 `TreeSet` 선택이 훨씬 쉬워진다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Hash Table Basics](./hash-table-basics.md)
> - [Tree Basics](./tree-basics.md)
> - [Balanced BST vs Unbalanced BST Primer](./balanced-bst-vs-unbalanced-bst-primer.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)
> - [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
>
> retrieval-anchor-keywords: hashset vs treeset beginner bridge, dedupe only vs sorted set, hash-backed set vs sorted set, backend dedup set selection, hashset when to use, treeset when to use, set ordering backend, dedupe without sort, dedupe with sorted order, range query set beginner, floor ceiling set beginner, hashset treeset selection table, 해시셋 트리셋 차이, 중복 제거만 필요할 때 set, 정렬된 set 필요할 때, backend set 선택 기준, hash backed set semantics, sorted set semantics, beginner set primer

## 먼저 감각부터 잡기

초급자에게는 이렇게 외우는 편이 가장 안전하다.

- `HashSet`: "이미 본 값인지"만 빠르게 확인하는 상자
- `TreeSet`: "이미 본 값인지"도 확인하면서 정렬된 줄까지 유지하는 상자

즉 질문이 이거다.

> 나는 정말 **중복 제거만** 필요할까, 아니면 **정렬된 순서/가장 가까운 값/범위 조회**까지 필요할까?

이 한 줄로 대부분 갈린다.

## 10초 선택표

| 지금 필요한 것 | 먼저 떠올릴 구조 | 이유 | 백엔드 예시 |
|---|---|---|---|
| 중복만 제거 | `HashSet` | membership 체크가 본업 | 이미 처리한 주문 ID 걸러내기 |
| 중복 제거 + 정렬된 순회 | `TreeSet` | 넣을 때부터 정렬 상태 유지 | 활성 태그를 사전순으로 응답 |
| 중복 제거 + 가장 작은/큰 값 확인 | `TreeSet` | `first/last`가 자연스럽다 | 가장 이른 예약 시각 확인 |
| 중복 제거 + 기준값 주변 찾기 | `TreeSet` | `floor/ceiling/higher/lower`가 자연스럽다 | 직전 배포 버전, 다음 쿠폰 경계 찾기 |

한 줄로 줄이면:

- "봤는지"만 중요하면 `HashSet`
- "정렬된 채로 다루는지"가 중요하면 `TreeSet`

## 왜 `HashSet`이 dedupe-only에 잘 맞나

`HashSet`은 순서를 유지하려고 애쓰지 않는다.
대신 "이 값이 이미 있는가?"를 빠르게 확인하는 데 집중한다.

그래서 이런 코드에 잘 맞는다.

```java
Set<String> seenOrderIds = new HashSet<>();

if (!seenOrderIds.add(orderId)) {
    return; // 이미 처리한 주문
}
```

이 상황에서 중요한 질문은 하나뿐이다.

- 이 `orderId`를 전에 본 적이 있는가?

정렬, 범위, 가장 가까운 값은 필요 없다.
이럴 때 `TreeSet`까지 쓰면 기능은 늘지만, 문제는 더 단순하게 풀 수 있다.

## 왜 `TreeSet`은 sorted-set 쪽에 맞나

`TreeSet`은 중복도 막지만, 동시에 원소를 **정렬된 상태로 유지**한다.
그래서 "중복 제거만"이 아니라 "정렬된 의미"가 함께 있는 문제에 어울린다.

예를 들어 이런 경우다.

```java
NavigableSet<Integer> activeDiscountRates = new TreeSet<>();
activeDiscountRates.add(5);
activeDiscountRates.add(10);
activeDiscountRates.add(20);

Integer nextRate = activeDiscountRates.ceiling(12); // 20
```

여기서 필요한 것은 단순 dedupe가 아니다.

- 정렬된 순서
- 기준값 이상에서 가장 가까운 값

이건 hash-backed set보다 sorted set이 더 직접적으로 풀린다.

## 같은 "중복 제거"라도 질문이 다르면 선택이 달라진다

| 상황 | `HashSet`으로 충분한가 | `TreeSet`이 더 자연스러운가 | 이유 |
|---|---|---|---|
| 이벤트 ID 중복 소비 방지 | 예 | 아니오 | "이미 봤나"만 보면 된다 |
| 사용자 입력 태그를 중복 없이 저장 | 예 | 경우에 따라 예 | 응답에서 항상 정렬된 태그 목록이 필요하면 `TreeSet` |
| 예약 시각 중복 방지 | 경우에 따라 예 | 보통 예 | 중복 방지 뒤에 "가장 이른 예약"이나 "다음 예약"을 자주 묻는다 |
| 점수 구간 경계 관리 | 아니오 | 예 | 범위와 인접 원소 탐색이 중요하다 |

핵심은 이거다.

- `HashSet`은 "중복 제거" 자체가 목표일 때 강하다
- `TreeSet`은 "중복 제거"가 아니라 "정렬된 기준으로 다루기"가 목표일 때 강하다

## 백엔드에서 자주 보는 장면

### 1. 중복 요청 차단

- 예: 메시지 ID, 이벤트 ID, 주문 ID dedupe
- 추천: `HashSet`
- 이유: 보통 "처리했는지 여부"만 알면 된다

### 2. 정렬된 정책 집합

- 예: 허용 포인트 구간, 할인율 구간, 버전 경계
- 추천: `TreeSet`
- 이유: 직전 값, 다음 값, 전체 정렬 순회가 자주 나온다

### 3. 응답용 보기 좋은 순서

- 예: 화면에 태그를 항상 사전순으로 노출
- 추천: `TreeSet`
- 이유: dedupe 후 매번 따로 정렬하지 않아도 된다

### 4. 순서는 상관없고 메모리 내 중복만 막기

- 예: 현재 배치 실행 동안 본 사용자 ID
- 추천: `HashSet`
- 이유: 가장 단순하고 의도가 분명하다

## 초보자 혼동 포인트

- `TreeSet`이 더 "좋은 Set"은 아니다. 질문이 다를 뿐이다.
- dedupe-only인데 정렬이 필요 없으면 `HashSet`이 보통 더 자연스럽다.
- `TreeSet`을 고르는 이유는 "중복 제거도 된다"가 아니라 "정렬된 set 기능이 필요하다"여야 한다.
- "나중에 필요할 수도 있어서" 정렬 구조를 미리 고르면 코드 의도가 흐려질 수 있다.

## 아주 짧은 결정 순서

1. 먼저 "이미 본 값인지"만 확인하면 되는지 본다.
2. 맞으면 `HashSet`부터 생각한다.
3. 아니라면 정렬 순회, 최소/최대, 주변 값, 범위 조회가 필요한지 본다.
4. 이 요구가 있으면 `TreeSet`을 고른다.

## 다음에 읽으면 좋은 문서

- 해시 기반 membership 감각을 먼저 다지고 싶으면 [Hash Table Basics](./hash-table-basics.md)
- 트리 기반 정렬 구조의 큰 그림이 필요하면 [Tree Basics](./tree-basics.md)
- `TreeSet`이 왜 정렬/인접 조회에 강한지 더 보고 싶으면 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- Java에서 `HashSet`과 `TreeSet`의 실제 중복 판정 기준 차이를 보고 싶으면 [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)

## 한 줄 정리

중복 제거만 필요하면 hash-backed set인 `HashSet`이 맞고, 중복 제거에 더해 정렬된 순서나 범위 의미가 필요하면 sorted set인 `TreeSet`이 맞다.
