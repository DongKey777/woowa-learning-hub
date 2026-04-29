# Java 컬렉션 프레임워크 입문

> 한 줄 요약: 컬렉션을 고를 때는 구현체 이름부터 외우기보다 `순서가 필요한가?`, `중복을 허용할까?`, `키-값 조회가 필요한가?` 세 질문으로 시작하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [우테코 백엔드 미션 선행 개념 입문](../../software-engineering/woowacourse-backend-mission-prerequisite-primer.md)
- [Java Optional 입문](./java-optional-basics.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [Java enum 기초](./java-enum-basics.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [`List.contains()` vs `Set.contains()` 증상 카드](./list-contains-vs-set-contains-symptom-card.md)
- [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)
- [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)

retrieval-anchor-keywords: java collections basics, list set map 입문, collection 선택 기준, hashmap 입문, 컬렉션 프레임워크 기초, java list 언제 쓰나, java set 중복 제거, java map key value, 처음 백엔드 미션 컬렉션 뭐부터, service 전에 list set map, queue가 왜 둘 다 나와요, hashmap get null 왜, list set map 다음 뭐 봐요, 컬렉션 다음 자료구조 뭐부터, queue가 service 코드에도 나오고 bfs에도 나와요

## 핵심 개념

Java Collections Framework는 "여러 개 데이터를 다루는 표준 도구 상자"다.
배열보다 실무에서 자주 쓰이는 이유는 크기 관리, 탐색, 중복 처리 규칙이 인터페이스로 표준화되어 있기 때문이다.

가장 중요한 초보자 규칙은 두 가지다.

- 변수는 인터페이스 타입으로 선언한다 (`List`, `Set`, `Map`)
- 구현체는 `new`할 때만 고른다 (`new ArrayList<>()`, `new HashSet<>()`, `new HashMap<>()`)

초보자 첫 읽기에서는 한 줄을 더 붙이면 헷갈림이 줄어든다.

- 단건의 "없음"은 `Optional`
- 여러 건의 "0개"는 빈 컬렉션
- key 조회의 애매한 `null`은 `Map`에서 따로 해석한다

즉 컬렉션 선택은 `List`/`Set`/`Map`만 고르는 일이 아니라, "없음"을 어떤 모양으로 보여 줄지도 같이 정하는 일이다.

처음 읽을 때는 아래 한 문장으로 잡아도 충분하다.

- "줄 세워 두면 `List`, 한 번만 담으면 `Set`, 이름표로 찾으면 `Map`, 한 명이 없을 수 있으면 `Optional`, 없음의 이유까지 말하면 enum 상태"

처음 배우는 단계에서 가장 많이 섞는 분기만 다시 20초 표로 줄이면 이렇다.

| 지금 코드가 말하려는 것 | 첫 선택 | 왜 여기서 멈추면 되나 |
|---|---|---|
| 장바구니가 비어 있을 수 있다 | `List<CartItem>` + 빈 리스트 | 여러 건의 `0개`는 컬렉션 자체가 표현한다 |
| 회원 한 명 조회 결과가 없을 수 있다 | `Optional<User>` | 단건의 있음/없음 질문이다 |
| 회원 id로 찾았는데 `get(...)`이 `null`이다 | `Map` 해석부터 다시 본다 | key 없음과 value `null`이 겹칠 수 있다 |
| 닉네임이 왜 없는지까지 구분해야 한다 | enum 상태 또는 상태 타입 | 단순 없음보다 이유 이름표가 중요하다 |

## 30초 선택 순서: 요구 -> 인터페이스 -> 구현체

처음엔 구현체 이름을 외우기보다, 아래 3단계만 따라가면 된다.

1. 요구를 한 문장으로 적는다.
   예: "가입 순서를 유지해야 하고 중복 이름도 보여 줘야 한다"
2. 요구를 인터페이스로 번역한다 (`List`/`Set`/`Map`).
3. 특별한 이유가 없다면 기본 구현체(`ArrayList`/`HashSet`/`HashMap`)로 시작한다.

핵심은 "구조 이름"보다 "요구 번역"이다.

`컬렉션 큰 그림`, `리스트 셋 맵 차이`, `처음 배우는데 컬렉션`처럼 entry query가 들어오면 이 문서를 첫 진입점으로 잡고, 여기서 `List`/`Set`/`Map` 감각을 먼저 고정한 뒤 개별 follow-up으로 내려가면 된다.

## 한 예제로 같이 보기: 리스트인가, 셋인가, 맵인가

초보자에게 가장 쉬운 기준은 "지금 코드가 어떤 질문을 하느냐"다.

| 코드에서 실제 질문 | 첫 선택 | 왜 |
|---|---|---|
| "가입한 순서대로 이름을 다시 보여 줄까?" | `List<String>` | 순서와 중복 허용이 핵심이다 |
| "이미 본 쿠폰 코드를 한 번만 기록할까?" | `Set<String>` | 같은 값의 중복 제거가 핵심이다 |
| "회원 id로 회원 정보를 바로 찾을까?" | `Map<Long, User>` | key 기반 조회가 핵심이다 |
| "회원 한 명이 없을 수도 있나?" | `Optional<User>` | 단건의 있음/없음 질문이다 |
| "닉네임이 왜 비었는지까지 알아야 하나?" | enum 상태 또는 상태 타입 | 단순 없음보다 이유가 더 중요하다 |

`List`/`Set`/`Map`을 외우는 것보다 "순서", "중복", "key 조회" 중 무엇을 묻는지 먼저 붙이면 첫 분기가 훨씬 덜 흔들린다.

## 컬렉션 다음 한 칸만 옮기기

초보자가 자주 하는 점프는 `List`/`Set`/`Map`만 막 배운 상태에서 곧바로 정렬 컬렉션, 성능, 알고리즘으로 뛰는 것이다.
처음에는 아래처럼 한 칸씩만 옮기는 편이 안전하다.

| 지금 보이는 증상 | 먼저 읽을 것 | 바로 다음 한 칸 |
|---|---|---|
| `List`/`Set`/`Map` 이름부터 아직 헷갈린다 | 이 문서 | [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md) |
| `contains()`는 같은데 `List`와 `Set`이 왜 다르게 느껴지는지 헷갈린다 | 이 문서 | [`List.contains()` vs `Set.contains()` 증상 카드](./list-contains-vs-set-contains-symptom-card.md) |
| 컬렉션은 알겠는데 `HashSet` 중복, `HashMap` 조회가 왜 깨지는지 모르겠다 | 이 문서 | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) |
| 빈 리스트, `Optional`, `Map#get(...) == null`, enum 상태가 한꺼번에 섞인다 | 이 문서 | [Java Optional 입문](./java-optional-basics.md) -> [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) -> [Java enum 기초](./java-enum-basics.md) |
| 문제 문장을 자료구조 이름으로 번역하는 연습이 더 필요하다 | 이 문서 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) |
| `처음 백엔드 미션`인데 `Service`/`DTO`보다 `List`/`Set`/`Map`이 먼저 흔들린다 | 이 문서 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) -> [우테코 백엔드 미션 선행 개념 입문](../../software-engineering/woowacourse-backend-mission-prerequisite-primer.md) |

- 짧게 외우면 `List/Set/Map -> 요구 문장 번역 -> 비교 규칙/조회 규칙` 순서다.
- `처음`, `뭐부터`, `왜`, `헷갈려요` query라면 정렬 컬렉션이나 성능 문서보다 위 순서를 타면 안정적이다.
- `처음 백엔드 미션`, `service 전에 list/set/map이 막혀요` 같은 query는 `컬렉션 입문 -> Backend Data-Structure Starter Pack -> 우테코 백엔드 미션 선행 개념 입문` 순서로만 붙이면 beginner 점프를 줄일 수 있다.

## 컬렉션에서 cross-category로 넘기는 3칸 사다리

`List`/`Set`/`Map` 이름은 알겠는데 다음 category가 막히는 순간에는, 구현체 deep dive보다 아래 사다리를 먼저 고정하면 된다.

| 지금 막힌 문장 | primer | follow-up | deep dive 대신 여기서 멈출 자리 |
|---|---|---|---|
| `컬렉션은 알겠는데 백엔드 문제 문장을 자료구조로 못 옮기겠어요` | 이 문서 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) | [자료구조 README - 초급 10초 라우터](../../data-structure/README.md#초급-10초-라우터) |
| `queue가 service handoff인지 BFS 도구인지 모르겠어요` | 이 문서 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) -> `worker 순서`면 [Service 계층 기초](../../software-engineering/service-layer-basics.md) -> [Ports and Adapters Beginner Primer](../../software-engineering/ports-and-adapters-beginner-primer.md), `최소 이동 횟수`면 [DFS와 BFS 입문](../../algorithm/dfs-bfs-intro.md) | [우테코 백엔드 미션 선행 개념 입문](../../software-engineering/woowacourse-backend-mission-prerequisite-primer.md#queue-오해-3-way-splitter) |
| `List/Set/Map은 알겠는데 처음 백엔드 미션에서 어디까지 읽어야 하나요?` | 이 문서 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) -> [우테코 백엔드 미션 선행 개념 입문](../../software-engineering/woowacourse-backend-mission-prerequisite-primer.md) | [language 카테고리 인덱스](../README.md#language-equality-collections-optional-quick-return) |

- 짧게 외우면 `컬렉션 질문을 고른다 -> 자료구조 질문으로 번역한다 -> service/BFS 중 하나로만 넘긴다`다.
- `처음`, `왜`, `헷갈려요`, `뭐부터` 같은 beginner query는 이 사다리 밖으로 바로 점프하지 않는 편이 안전하다.

## queue가 같이 보일 때

`queue`가 보인다고 바로 컬렉션 deep dive나 알고리즘 deep dive로 뛰지 않는다.

| 지금 보이는 문장 | 먼저 붙일 질문 | 다음 한 칸 |
|---|---|---|
| `worker가 꺼낸다`, `받은 순서대로 처리한다` | FIFO handoff가 필요한가 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) -> [Service 계층 기초](../../software-engineering/service-layer-basics.md) -> [Ports and Adapters Beginner Primer](../../software-engineering/ports-and-adapters-beginner-primer.md) |
| `가까운 칸부터`, `최소 이동 횟수` | queue가 탐색 도구인가 | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) -> [DFS와 BFS 입문](../../algorithm/dfs-bfs-intro.md) |

- `queue가 왜 둘 다 나와요` 같은 beginner query는 `컬렉션 -> 자료구조 starter -> Service 또는 BFS` 순서로만 넘기면 된다.

## 여기서 먼저 멈출 것

이 문서에서 초보자가 먼저 가져갈 결론은 네 줄이면 충분하다.

- 순서가 중요하면 `List`
- 중복 제거가 중요하면 `Set`
- key 조회가 중요하면 `Map`
- 특별한 요구가 없으면 `ArrayList`, `HashSet`, `HashMap`부터 시작

정렬 컬렉션, `BigDecimal` key, `NavigableMap`, comparator tie-breaker는 이 기준이 붙은 뒤 관련 문서로 넘겨도 늦지 않다. 처음에는 "특수 구현체를 더 외우기"보다 `List`/`Set`/`Map` 질문을 먼저 고정하는 편이 안전하다.

## 처음 배우는데 언제 쓰는지: 15초 답

| 이런 상황이면 | 먼저 떠올릴 것 | 이유 |
|---|---|---|
| 장바구니 상품을 담은 순서대로 보여 주고 싶다 | `List` | 순서와 중복 허용이 핵심 |
| 태그를 한 번만 저장하고 싶다 | `Set` | 자동 중복 제거가 핵심 |
| 회원 id로 회원 정보를 바로 찾고 싶다 | `Map` | key로 조회하는 구조가 핵심 |
| 조회 결과가 없을 수도 있는 회원 한 명을 돌려주고 싶다 | `Optional<User>` | 컬렉션보다 단건의 "있음/없음" 질문이 핵심 |

처음 배우는 단계에서는 이 3줄만 바로 떠올라도 충분하다.
그다음에야 `ArrayList`/`HashSet`/`HashMap` 같은 첫 구현체를 붙이면 된다.

여기서 막히는 대표 증상은 두 가지다.

- "`List`가 비면 그게 null 아닌가요?"가 아니다. 빈 리스트는 "정상적으로 0개"를 뜻한다.
- "`Map#get(...) == null`이면 없는 거 아닌가요?"도 항상 맞지 않다. key는 있는데 value가 `null`일 수도 있다.

## 먼저 잡는 멘탈 모델: 3가지 질문

컬렉션 선택이 막히면 아래 순서로 판단하면 된다.

| 질문 | `Yes`면 | `No`면 |
|---|---|---|
| 입력 순서/인덱스가 중요한가? | `List`를 먼저 본다 | 다음 질문으로 |
| 중복을 자동으로 막아야 하나? | `Set`을 먼저 본다 | 다음 질문으로 |
| 키로 빠르게 찾는 조회가 중심인가? | `Map`을 먼저 본다 | 그래도 대부분 `List`에서 시작 |

즉 "자료구조 이름"보다 **문제의 요구사항**이 먼저다.

## 컬렉션 고른 뒤 바로 만나는 `없음` 질문

컬렉션을 고른 다음에는 "비어 있음"을 어떻게 읽을지도 같이 붙여야 한다.

| 지금 표현하려는 것 | 먼저 떠올릴 타입 | 읽는 법 |
|---|---|---|
| 사용자 한 명이 없을 수 있다 | `Optional<User>` | 값이 없으면 `empty` |
| 주문 항목이 0개일 수 있다 | `List<OrderLine>` | 값이 없으면 빈 리스트 |
| 회원 id로 찾았더니 상태값이 없거나 `null`일 수 있다 | `Map<Long, String>` | `get()`만 보지 말고 `containsKey()`까지 본다 |

이 표를 기억하면 "`Optional`도 알겠고 `List`/`Set`/`Map`도 알겠는데 왜 `HashMap#get(...)`에서 다시 막히지?"라는 beginner 증상을 줄이기 쉽다.

여기서 많이 나오는 오해를 한 줄로 자르면 이렇다.

- 빈 리스트는 "`정상적으로 0개`"지 `null`이 아니다.
- `HashMap#get(...) == null`은 "`key 없음`"과 "`value가 null`"을 아직 분리하지 않은 상태일 수 있다.
- `Set`의 중복 판단과 `Map`의 key 조회는 결국 값 비교 규칙(`equals()`/`hashCode()`)까지 이어진다.

## 한눈에 보기

| 인터페이스 | 대표 구현체(첫 선택) | 핵심 특징 |
|---|---|---|
| `List<E>` | `ArrayList` | 순서 보존, 중복 허용, 인덱스 접근 O(1) |
| `Set<E>` | `HashSet` | 중복 불허, 순서 미보장, 포함 여부 확인 O(1) |
| `Map<K, V>` | `HashMap` | 키-값 저장, 키 중복 불허, 키 조회 O(1) |

추가 구현체는 "요구가 생길 때" 고르면 충분하다.

- 삽입 순서를 유지한 `Map`이 필요하면 `LinkedHashMap`
- 중복 제거와 삽입 순서를 같이 원하면 `LinkedHashSet`
- 정렬된 순서가 필요하면 `TreeSet`/`TreeMap`
- `LinkedList`는 큐/덱 같은 특수한 접근 패턴에서만 follow-up으로 고려

위 네 줄은 "처음부터 다 외울 목록"이 아니라 follow-up 갈림길이다. 첫 읽기에서는 `ArrayList`/`HashSet`/`HashMap`만 고정해도 충분하다.

## 하나의 예제로 비교하기

회원 시스템에서 이름 목록, 권한 집합, 사용자별 점수를 관리한다고 가정해 보자.

```java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

List<String> joinOrder = new ArrayList<>();
joinOrder.add("alice");
joinOrder.add("bob");
joinOrder.add("alice"); // 중복 허용, 가입 순서 보존

Set<String> roles = new HashSet<>();
roles.add("USER");
roles.add("ADMIN");
roles.add("USER"); // 중복 자동 제거

Map<String, Integer> scoreByUser = new HashMap<>();
scoreByUser.put("alice", 90);
scoreByUser.put("bob", 85);
scoreByUser.put("alice", 95); // 같은 key라서 값 갱신
```

이 예제 하나로 세 인터페이스의 차이가 드러난다.

- `List`: 순서와 중복을 그대로 보존
- `Set`: "존재 여부" 중심이라 중복을 제거
- `Map`: key 기준 조회/갱신 중심

## 같은 예제를 질문으로 다시 읽기

같은 예제를 "무슨 질문을 하느냐"로 다시 읽으면 collections와 equality가 바로 이어진다.

| 코드 | 컬렉션이 실제로 묻는 질문 | 먼저 떠올릴 규칙 |
|---|---|---|
| `joinOrder.contains("alice")` | 이 값이 목록 안에 있나 | `List.contains(...)`는 `equals()`로 찾는다 |
| `roles.add("USER")`를 한 번 더 호출 | 이미 같은 값이 있나 | `HashSet`은 중복 판단에 `equals()`/`hashCode()`를 쓴다 |
| `scoreByUser.put("alice", 95)` | 같은 key로 덮어쓰는가 | `Map`은 key를 기준으로 조회/갱신한다 |

초보자 기준으로는 "컬렉션 고르기"와 "비교 규칙"을 따로 외우지 말고, 지금 이 통이 `포함 여부`, `중복 여부`, `같은 key 조회` 중 무엇을 묻는지 먼저 붙이면 덜 헷갈린다.

## 요구사항을 바로 컬렉션으로 매핑해 보기

| 요구사항 한 줄 | 인터페이스 | 기본 구현체 | 이유 |
|---|---|---|---|
| 게시판 댓글을 작성 순서대로 보여 준다 | `List<Comment>` | `ArrayList` | 순서/인덱스 접근이 핵심 |
| 태그 중복을 자동으로 제거한다 | `Set<String>` | `HashSet` | 존재 여부/중복 제거가 핵심 |
| 사용자 id로 프로필을 바로 찾는다 | `Map<Long, UserProfile>` | `HashMap` | key 기반 조회/갱신이 핵심 |

## "언제 쓰는지"에서 자주 막히는 분기

| 헷갈리는 순간 | 먼저 보는 질문 | 보통의 첫 선택 |
|---|---|---|
| 목록인데 `Map`인지 `List`인지 모르겠다 | "id로 바로 찾는가, 그냥 순서대로 보여 주는가?" | 조회 중심이면 `Map`, 표시 중심이면 `List` |
| 중복 제거가 필요한데 출력 순서도 중요하다 | "중복 제거가 본질인가, 순서 출력이 본질인가?" | 둘 다 핵심이면 `LinkedHashSet` |
| `Set`/`Map`도 여러 종류라 첫 선택이 어렵다 | "정렬/삽입순서 요구가 지금 있는가?" | 없으면 `HashSet`/`HashMap`부터 |

## 상세 분해

### List - 순서가 있는 목록

- 인덱스 접근이 많으면 `ArrayList`가 기본 선택이다.
- 같은 값이 여러 번 들어가도 된다.

### Set - 중복 없는 집합

- "있다/없다"가 중심인 데이터에 맞다.
- `HashSet`은 순서를 보장하지 않는다.
- `equals()`/`hashCode()` 계약이 중복 판단의 핵심이다.

### Map - 키로 찾는 사전

- key는 유일해야 한다.
- 같은 key로 `put`하면 값이 교체된다.
- 조회 패턴이 많을 때 가장 강력하다.

## 흔한 오해와 혼동

- `ArrayList`와 `LinkedList`를 처음부터 50:50 선택지로 보면 안 된다. 대부분은 `ArrayList`가 첫 선택이다.
- `HashMap`의 반복 순서를 로직에 기대하면 안 된다. 순서가 필요하면 `LinkedHashMap` 또는 `TreeMap`으로 의도를 드러내야 한다.
- `HashSet` 중복 제거는 `equals()`만 쓰는 게 아니라 `hashCode()`와 함께 동작한다.
- 정렬 컬렉션(`TreeSet`, `TreeMap`)은 `equals()`보다 `compareTo()`/`Comparator` 기준이 직접 동작한다. 이 차이는 여기서 끝까지 파기보다 관련 문서로 넘기는 편이 낫다.
- "중복 제거 + 순서 유지"가 함께 나오면 `List`와 `Set` 중 하나만 억지로 고르지 말고 [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)부터 보면 된다.
- `TreeSet`/`TreeMap`은 "정렬 기준이 같으면 같은 자리"로 본다. 이 차이는 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)에서 이어서 보면 된다.
- `HashMap`/`HashSet` key나 원소의 비교 기준 필드를 넣은 뒤 바꾸면 조회나 제거가 깨질 수 있다.
- `Collection`(인터페이스)과 `Collections`(유틸리티 클래스)를 같은 것으로 보면 API를 자주 잘못 찾게 된다.
- `Arrays.asList(...)`는 이름 때문에 `ArrayList`처럼 보이지만, 실제로는 `add/remove`가 안 되는 고정 크기 리스트다. 이 함정은 [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)로 바로 이어서 보면 된다.
- `Map`은 `Collection`의 하위 타입이 아니다. 그래서 `Collection` 전용 API를 `Map`에 바로 적용할 수 없다.
- `Iterable`은 반복 약속이고 `Collection`은 원소 묶음 API다. 계층 자체가 헷갈리면 [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)을 먼저 보고 돌아오면 이해가 빠르다.

헷갈릴 때는 아래처럼 먼저 분류하면 다음 문서로 덜 헤맨다.

## 흔한 오해와 혼동 (계속 2)

| 지금 막히는 포인트 | 먼저 기억할 한 줄 |
|---|---|
| `List`/`Set`/`Map` 중 무엇을 고를지 모르겠다 | 구현체 이름보다 `순서`, `중복`, `키 조회` 세 질문을 먼저 본다 |
| `HashSet`/`HashMap` 동작이 이상해 보인다 | 비교 규칙은 값 자체보다 `equals()`/`hashCode()` 설계와 연결된다 |
| `TreeSet`/`TreeMap`이 예상과 다르게 합쳐진다 | sorted collection은 `equals()`보다 정렬 기준(`compareTo`/`Comparator`)이 직접 작동한다 |
| `Collection`/`Collections`/`Map` 계층이 섞인다 | 이름이 비슷해도 역할과 계층이 다르다 |

## 빠른 선택 체크리스트

- 순서/인덱스가 필요하면 `List`
- 자동 중복 제거가 필요하면 `Set`
- key 기반 조회/갱신이 중심이면 `Map`
- 특별한 이유가 없다면 `ArrayList` + `HashSet` + `HashMap`부터 시작
- 변수는 인터페이스로 선언하고 구현체는 생성 시점에만 고른다
- 요구 문장 분류를 먼저 연습하려면 [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)

## 다음 단계

처음 읽은 뒤에는 "더 많이 읽기"보다 "내가 어디서 막혔는지"를 기준으로 한 문서만 이어서 보는 편이 더 안전하다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`List`/`Set`/`Map`을 문제 문장으로 고르는 연습이 더 필요하다" | [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md) |
| "왜 `HashSet` 중복 판단이 내가 기대한 것과 다르지?" | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| "`TreeMap`/`TreeSet` 정렬 기준이 같은 자리라는 말이 무슨 뜻이지?" | [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md) |
| "`BigDecimal` key를 썼더니 hash와 sorted 결과가 왜 다르지?" | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |
| "`Collection`, `Collections`, `Map`, `Iterable` 이름이 계속 섞인다" | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |
| "`Arrays.asList(...)`가 왜 `add/remove`에서 막히지?" | [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md) |
| "`equals()`/`hashCode()` 감각이 약해서 key 설계가 불안하다" | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "중복 제거와 순서 유지가 둘 다 필요하면 뭘 쓰지?" | [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md) |

## 더 깊이 가려면

- `Optional<List<T>>` 대신 빈 컬렉션과 상태 타입을 언제 고를지 이어서 보려면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- 컬렉션 선택, 비교 규칙, mutable key, 순회 중 수정까지 한 장으로 묶어 보고 싶다면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- `HashSet`와 `TreeSet`이 왜 다르게 중복을 보나를 더 보고 싶다면 [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- `TreeMap`/`TreeSet` 정렬 기준은 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- `BigDecimal` key처럼 예외적인 비교 규칙은 [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- `first`/`floor`/`ceiling` 탐색은 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- 성능 감각을 먼저 보강하고 싶다면 [Java Collections 성능 감각](./collections-performance.md)

## 한 줄 정리

컬렉션 선택은 구현체 이름 암기가 아니라 `순서`, `중복`, `키-값 조회` 세 질문으로 시작하고, 첫 선택은 보통 `ArrayList`, `HashSet`, `HashMap`이다.
