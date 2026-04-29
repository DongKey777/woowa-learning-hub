# Map vs Set Requirement Bridge

> 한 줄 요약: `Map`과 `Set`은 둘 다 해시 계열로 시작하는 경우가 많지만, 초보자에게 더 중요한 분기점은 "값까지 붙잡아야 하나"와 "있는지만 알면 되나"를 먼저 가르는 것이다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [해시 테이블 기초](./hash-table-basics.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: map vs set beginner, map set primer, map set 큰 그림, map vs set 뭐예요, map이랑 set 차이 뭐예요, 처음 배우는데 map set 차이, 자료구조 map set 큰 그림, map or set choice, dedupe vs key value lookup, key value vs membership, set으로 충분한가, map이 필요한가, 값까지 저장해야 하나, 언제 map 쓰고 언제 set 써요, 왜 set 말고 map 써요

## 핵심 개념

`Map`과 `Set`을 처음 배울 때 이름으로 외우면 자주 막힌다.
이 문서는 `map이랑 set 차이 뭐예요?`, `처음 배우는데 언제 map이고 언제 set이에요?` 같은 첫 질문이 들어왔을 때 가장 먼저 닿아야 하는 entry primer를 목표로 한다.
더 쉬운 출발점은 "내 질문이 어디서 끝나는가"다.

- `"이 값 이미 있나?"`에서 끝나면 `Set`
- `"이 key의 값이 뭐지?"`까지 가면 `Map`

즉 둘 다 "빨리 찾는다"는 공통점은 있지만, `Map`은 `key -> value`를 저장하고 `Set`은 값의 존재 여부를 저장한다.

초보자에게는 이렇게 외우면 충분하다.

- `Set`: 출입 명단
- `Map`: 사번표 + 상세 정보

여기서 한 번 더만 나누면 실제 구현체 선택까지 바로 이어진다.

- `Set` 안에서는 `HashSet` vs `TreeSet`
- `Map` 안에서는 `HashMap` vs `LinkedHashMap` vs `TreeMap`

## 한눈에 보기

| 지금 필요한 것 | 먼저 볼 구조 | 왜 이쪽이 먼저인가 |
|---|---|---|
| 중복 제거, membership 확인 | `Set` | 질문이 `"있나?"`에서 끝난다 |
| ID로 객체/상태/개수를 꺼내기 | `Map` | key에 연결된 value가 필요하다 |
| 존재 여부는 물론 count도 같이 쌓기 | `Map` | 값 칸이 있어야 누적할 수 있다 |
| 방문 여부만 기록하기 | `Set` | `visited=true/false`만 알면 된다 |

짧은 비교표로 보면 더 분명하다.

| 질문 문장 | `Set` 신호 | `Map` 신호 |
|---|---|---|
| `이미 처리했나?` | 강함 | 약함 |
| `이 id의 현재 상태는?` | 약함 | 강함 |
| `중복만 막으면 되나?` | 강함 | 약함 |
| `count/timestamp/status도 같이 보관하나?` | 약함 | 강함 |

한 번 더 구현체 수준으로 내려가면 이렇게 붙는다.

| 지금 필요한 요구 | 첫 구조 | 다음 문서 |
|---|---|---|
| 중복만 제거 | `HashSet`부터 생각 | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) |
| 중복 제거 + 정렬/이웃/범위 | `TreeSet`부터 생각 | [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md) |
| key로 값만 바로 찾기 | `HashMap`부터 생각 | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |
| key의 정렬/범위/바로 다음 값 | `TreeMap`부터 생각 | [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md) |

## 먼저 자르는 질문

처음엔 아래 세 질문만 순서대로 보면 된다.

1. 답이 `있다/없다`면 충분한가?
2. 같은 key에 count, 상태, 시간 같은 값을 붙여야 하는가?
3. 나중에 `"그 값 뭐였지?"`를 다시 꺼내야 하는가?

이 질문에 답하면 대부분 바로 갈린다.

- 1번이 `예`이고 2, 3번이 `아니오`면 `Set`
- 2번이나 3번이 `예`면 `Map`

입문자가 자주 놓치는 포인트는 "지금은 dedupe 같아 보여도 곧 value가 따라붙는지"다.
예를 들어 `requestId`를 중복만 막는다면 `Set`이 맞지만, `requestId -> 처리 시각`을 남기기 시작하면 이미 `Map` 문제다.

그리고 `Set`으로 정리된 뒤에도 질문이 하나 더 남는다.

- `중복만 막나?` -> 보통 `HashSet`
- `정렬된 순서나 주변 값도 보나?` -> 보통 `TreeSet`

`Map`으로 정리된 뒤에도 마찬가지다.

- `그냥 key lookup인가?` -> 보통 `HashMap`
- `삽입 순서를 보여 줘야 하나?` -> `LinkedHashMap`
- `바로 이전/다음 key, 범위가 필요한가?` -> `TreeMap`

## 같은 도메인도 요구가 달라지면 갈린다

주문 서비스만 봐도 문장에 따라 선택이 달라진다.

| 같은 주문 서비스 장면 | 먼저 고를 구조 | 이유 |
|---|---|---|
| `이 주문번호를 이미 처리했나?` | `Set<String>` | 중복 여부만 확인한다 |
| `이 주문번호의 현재 상태는?` | `Map<String, OrderStatus>` | 상태 value가 필요하다 |
| `이 상품이 몇 번 나왔나?` | `Map<Long, Integer>` | 존재 여부가 아니라 count 누적이다 |
| `방문한 주문번호를 다시 막기` | `Set<String>` | visited 기록이면 충분하다 |

간단한 코드로 보면 차이가 더 바로 보인다.

```java
Set<String> processedRequestIds = new HashSet<>();
Map<String, Instant> processedAt = new HashMap<>();
Map<Long, Integer> itemCounts = new HashMap<>();
```

첫 줄은 `"봤나?"`만 답한다.
둘째, 셋째 줄은 `"언제 봤나?"`, `"몇 번 나왔나?"`까지 답해야 하므로 `Map`이 된다.

## 흔한 오해와 함정

- "`Set`이 더 단순하니 일단 `Set`으로 시작하고 나중에 바꾸면 되지 않나요?"
  value 요구가 이미 보이면 처음부터 `Map`이 더 의도가 분명하다.
- "`Map`이 있으면 `Set`은 필요 없나요?"
  아니다. 존재 여부만 묻는 문제에 `Map<Id, Boolean>`을 쓰면 의도가 흐려질 수 있다.
- "`visited`는 항상 `Map`으로 해야 하나요?"
  아니다. 방문 여부만 체크하면 `visited set`이면 충분하다. 거리나 부모 노드를 같이 저장할 때만 `Map`이 붙는다.
- "`Set`을 고른 뒤에도 구현체를 고민해야 하나요?"
  그렇다. `중복만`이 핵심이면 `HashSet`, `정렬된 채로 다뤄야 하면 TreeSet`이 자연스럽다.
- "`Map`을 고르면 기본값이 항상 `TreeMap`인가요?"
  아니다. 단건 lookup 중심이면 보통 `HashMap`이 기본이고, `TreeMap`은 정렬된 이웃/범위 요구가 있을 때 떠올리면 된다.
- "`중복 제거`와 `개수 세기`는 비슷하니 둘 다 `Set` 아닌가요?"
  아니다. 개수 세기는 값 누적이 필요하므로 `Map`이다.
- "`Map`과 `Set`은 알고리즘과 무관한가요?"
  아니다. BFS/DFS에서도 `visited set/map`을 쓴다. 다만 그때 핵심 질문이 `최소 이동 횟수`라면 출발점은 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)이다.
- "`queue`와 `set/map`이 같이 보이면 무엇부터 고르나요?"
  `먼저 처리 순서`가 핵심이면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)로, `조회/중복 관리`가 핵심이면 이 문서의 분기부터 잡는 편이 빠르다.

## 실무에서 쓰는 모습

중복 요청 방지, 이미 본 사용자 ID 기록, 배치 중복 제거처럼 답이 yes/no면 `Set`이 가장 읽기 쉽다.

반대로 캐시, 집계, 상태 테이블은 대부분 `Map`으로 간다.
`userId -> User`, `couponCode -> Coupon`, `productId -> count`처럼 value가 문제의 핵심이기 때문이다.

특히 `dedupe`에서 `counting`으로 요구가 살짝 바뀌는 순간을 주의하면 좋다.

- `중복만 막기` -> `Set`
- `중복도 막고 몇 번 나왔는지 세기` -> `Map`
- `중복도 막고 마지막 처리 시각 남기기` -> `Map`

## 더 깊이 가려면

- `Map` 내부에서 `HashMap`, `LinkedHashMap`, `TreeMap`을 더 나누려면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- `Set` 내부에서 `HashSet`과 `TreeSet`을 나누려면 [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- hash 기반 lookup의 공통 원리를 먼저 복습하려면 [해시 테이블 기초](./hash-table-basics.md)
- `queue`나 `bfs`와 섞이는 beginner 오진을 풀고 싶다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md), [Backend Data-Structure Starter Pack](./backend-data-structure-starter-pack.md), [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

## 면접/시니어 질문 미리보기

1. 왜 `Set` 대신 `Map<Id, Boolean>`을 안 쓰나요?
   의도 표현과 저장 정보가 다르기 때문이다. 존재 여부만 필요하면 `Set`이 더 직접적이다.
2. `visited`를 `Set`이 아니라 `Map`으로 두는 경우는 언제인가요?
   거리, 부모, depth 같은 추가 metadata를 함께 저장할 때다.
3. `Set`으로 시작한 요구가 언제 `Map`으로 커지나요?
   count, timestamp, status처럼 key에 붙는 value 요구가 생길 때다.

## 한 줄 정리

`있나?`에서 끝나면 `Set`, `그 값이 뭐지?`까지 가면 `Map`이라고 먼저 자르면 초급자의 `dedupe vs key-value lookup` 혼동이 크게 줄어든다.
