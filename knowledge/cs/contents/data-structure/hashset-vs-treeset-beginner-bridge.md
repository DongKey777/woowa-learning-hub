# HashSet vs TreeSet Beginner Bridge

> 한 줄 요약: `Set`을 고를 때는 "중복만 막으면 되나"와 "정렬된 순서, 이웃 값, 범위까지 필요하나"를 먼저 나누면 `HashSet`과 `TreeSet` 선택이 훨씬 쉬워진다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: hashset vs treeset beginner, hashset treeset choice basics, set selection primer, dedupe only vs sorted set, sorted set beginner, set range query beginner, hashset when to use, treeset when to use, 해시셋 트리셋 차이, set 처음 고르기, 중복 제거만 필요할 때, floor ceiling set 뭐예요, why treeset, what is sorted set

## 핵심 개념

`HashSet`과 `TreeSet`은 둘 다 "`중복 없는 값 모음`"을 만들지만, 먼저 지키는 약속이 다르다.

- `HashSet`: "이 값이 있나?"를 빠르게 확인하는 기본 set
- `TreeSet`: 중복도 막고 값을 정렬된 상태로 유지하는 set

처음엔 이렇게 기억하면 충분하다.

- `HashSet`은 출입 명단
- `TreeSet`은 출입 명단 + 정렬된 번호표

초급자가 먼저 물어야 할 질문은 이것이다.

> 나는 정말 `있다/없다`만 알면 되나, 아니면 `가장 가까운 값`, `정렬된 순서`, `범위`까지 필요하나?

이 질문으로 자르면 `HashSet`과 `TreeSet`을 이름이 아니라 요구사항으로 고르게 된다.

## 한눈에 보기

| 지금 필요한 것 | 먼저 볼 구조 | 왜 이 구조가 맞나 |
|---|---|---|
| 중복 제거, membership 확인 | `HashSet` | 질문이 `"이미 봤나?"`에서 끝난다 |
| 항상 정렬된 순서로 순회 | `TreeSet` | 넣을 때부터 정렬 상태를 유지한다 |
| 기준값 바로 앞/뒤 찾기 | `TreeSet` | `floor`, `ceiling`, `lower`, `higher`가 자연스럽다 |
| 범위 안의 값만 보기 | `TreeSet` | sorted set의 range view가 맞다 |

같은 `Set`이라도 실제 질문 문장을 붙이면 차이가 더 또렷하다.

| 질문 문장 | `HashSet` 신호 | `TreeSet` 신호 |
|---|---|---|
| `이미 처리한 ID인가?` | 강함 | 약함 |
| `가장 가까운 다음 예약 시각은?` | 약함 | 강함 |
| `사전순으로 태그를 보여 줘야 하나?` | 약함 | 강함 |
| `중복만 막으면 끝인가?` | 강함 | 약함 |

## 먼저 자르는 질문

처음엔 아래 세 질문만 순서대로 보면 된다.

1. 답이 `있다/없다`면 충분한가?
2. 항상 정렬된 순서로 보여 주거나 꺼내야 하는가?
3. 기준값 주변(`바로 이전`, `바로 다음`)이나 범위(`10~20`)를 자주 묻는가?

분기 기준은 단순하다.

- 1번만 `예`면 `HashSet`
- 2번이나 3번이 `예`면 `TreeSet`

입문자가 자주 놓치는 포인트는 "`정렬된 출력 한 번`"과 "`정렬된 구조를 계속 유지`"가 다르다는 점이다.
마지막에 한 번만 정렬해서 보여 주면 `HashSet`으로 충분할 수 있지만, 매번 이웃 값과 범위를 묻는다면 `TreeSet` 쪽이 더 직접적이다.

## 같은 도메인도 요구가 달라지면 갈린다

주문/예약 서비스에서도 문장에 따라 선택이 달라진다.

| 같은 서비스 장면 | 먼저 고를 구조 | 이유 |
|---|---|---|
| `이 주문번호를 이미 처리했나?` | `HashSet<String>` | membership만 확인한다 |
| `활성 쿠폰 코드를 사전순으로 보여 주기` | `TreeSet<String>` | 정렬된 순회가 기능 요구다 |
| `12:00 이후 첫 예약 시각 찾기` | `TreeSet<LocalTime>` | 이웃 탐색이 필요하다 |
| `이번 배치에서 이미 본 회원 ID 막기` | `HashSet<Long>` | 중복 방지가 핵심이다 |

짧은 코드로 보면 차이가 더 잘 보인다.

```java
Set<String> processedOrderIds = new HashSet<>();
NavigableSet<Integer> activeScores = new TreeSet<>();
```

첫 줄은 `"봤나?"`를 답하는 용도다.
둘째 줄은 `"정렬된 상태에서 가장 가까운 점수는?"` 같은 질문까지 답할 수 있다.

## 흔한 오해와 함정

- "`TreeSet`이 더 많은 기능이 있으니 항상 더 좋은가요?"
  아니다. 중복만 막으면 되는 문제에 `TreeSet`을 쓰면 의도보다 구조가 무거워질 수 있다.
- "`HashSet`도 나중에 정렬하면 되니 `TreeSet`은 필요 없나요?"
  마지막 한 번 정렬은 가능하지만, 매 조회마다 `floor/ceiling/range`를 묻는 상황은 `TreeSet`이 더 자연스럽다.
- "`TreeSet`은 value를 저장하는 map 비슷한 구조인가요?"
  아니다. 여전히 `Set`이다. 값 하나만 저장하고, 그 값의 정렬 규칙이 중요할 뿐이다.
- "`visited`는 항상 `HashSet`인가요?"
  방문 여부만 체크하면 보통 `HashSet`이다. 하지만 거리나 부모 정보까지 저장하면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)로 넘어가 `Map`을 보는 편이 맞다.
- "`TreeSet`을 고르면 자동으로 삽입 순서도 유지되나요?"
  아니다. 삽입 순서가 아니라 정렬 순서다. 삽입 순서가 필요하면 set보다 map/linked 계열 요구를 다시 봐야 한다.

## 실무에서 쓰는 모습

`HashSet`은 중복 요청 차단, 이미 본 ID 기록, 배치 중복 제거처럼 "`있는가`만 답하면 끝"인 장면에 잘 맞는다.

`TreeSet`은 예약 시각 집합, 정책 구간 경계, 정렬된 태그 목록처럼 "`정렬된 채로 다뤄야 하는가`"가 중요한 장면에 잘 맞는다.

특히 아래처럼 요구가 바뀌는 순간을 주의하면 좋다.

- `중복만 막기` -> `HashSet`
- `중복도 막고 항상 정렬된 목록 보여 주기` -> `TreeSet`
- `중복도 막고 다음 값/이전 값 찾기` -> `TreeSet`

## 더 깊이 가려면

- `Set`과 `Map` 자체가 아직 헷갈리면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- `TreeSet`과 `TreeMap`의 정렬/이웃 탐색 감각을 같이 잡고 싶으면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- `TreeSet`의 `floor/ceiling` 감각을 예약 예제로 보고 싶으면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- 값만 있는 `TreeSet`에서 `lower/floor/ceiling/higher` exact match를 먼저 손으로 맞히고 싶다면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- Java에서 `HashSet`과 `TreeSet`의 실제 중복 판정 차이를 보려면 [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)
- `visited set`이 BFS에서 어떻게 쓰이는지 복습하려면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

## 면접/시니어 질문 미리보기

1. 왜 `HashSet` 대신 항상 `TreeSet`을 쓰지 않나요?
   정렬, 이웃 값, 범위 조회가 필요 없으면 `HashSet`이 더 직접적이기 때문이다.
2. `HashSet`에서 마지막에 정렬하는 것과 `TreeSet`을 쓰는 것은 언제 갈리나요?
   한 번 보여 주기용 정렬이면 전자, 조회 중 계속 정렬된 탐색이 필요하면 후자다.
3. `TreeSet`을 보면 `TreeMap`도 같이 떠올려야 하나요?
   그렇다. 둘 다 정렬과 이웃 탐색이 핵심이어서 beginner 분기에서는 함께 이해하면 편하다.

## 한 줄 정리

`있나?`에서 끝나면 `HashSet`, `정렬된 순서나 주변 값까지 필요하면 TreeSet`이라고 먼저 자르면 beginner의 set 선택 실수가 크게 줄어든다.
