# Java 컬렉션 프레임워크 입문

> 한 줄 요약: 컬렉션을 고를 때는 구현체 이름부터 외우기보다 `순서가 필요한가?`, `중복을 허용할까?`, `키-값 조회가 필요한가?` 세 질문으로 시작하면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 제네릭 입문](./java-generics-basics.md)
- [Java Optional 입문](./java-optional-basics.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)
- [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Java Collections 성능 감각](./collections-performance.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: java collections basics, list set map 입문, collection 선택 기준, list set map decision table, list set map requirement drill, requirement to type, arraylist linkedlist 차이, hashmap 입문, 컬렉션 프레임워크 기초, java collection framework beginner, java list 언제 쓰나, java set 중복 제거, java map key value, 컬렉션 어떤 걸 써야 하나요, collection interface beginner, java iterable basics, hashset equals hashCode beginner, treeset natural ordering, treemap compareTo key slot, navigablemap navigableset basics, java collection vs collections difference, java map is not collection, beginner collection selection flow, 처음 배우는데 List Set Map 차이, List Set Map 큰 그림, 자바 컬렉션 기초, ArrayList HashSet HashMap 언제 쓰는지, 컬렉션 처음 배우는데 뭐부터, Collection과 Collections 차이 기초, Map은 Collection인가요, 중복 제거는 Set, 순서 보장은 List, 키값 조회는 Map, linkedhashset beginner, java linkedhashset 언제 쓰나, 중복 제거 순서 유지 linkedhashset, list set linkedhashset 차이, 컬렉션 큰 그림, 자바 컬렉션 큰 그림, 처음 배우는데 컬렉션, 컬렉션 기초, 컬렉션 언제 쓰는지, 리스트 셋 맵 차이, list set map 차이, list set map 큰 그림, list set map 처음 배우는데, collection first reading, collection beginner route, beginner collection primer, list set map safe next step, java collections equality primer, java mutable key beginner, java collection update tradeoff beginner, 처음 배우는데 List Set Map 언제 쓰는지, 처음 배우는데 ArrayList HashSet HashMap 언제 쓰는지, List Set Map 언제 써야 하나, List Set Map 처음 선택, 처음 배우는데 리스트 셋 맵 언제 쓰는지, 자바 리스트 셋 맵 언제 쓰는지, list set map when to use beginner, arraylist hashset hashmap first choice, 자바 컬렉션 흔한 오해, 컬렉션 다음 단계, list set map confusion, collection confusion checklist, beginner collection next step, map은 collection인가요, collection vs collections confusion, arrays aslist fixed size confusion

## 핵심 개념

Java Collections Framework는 "여러 개 데이터를 다루는 표준 도구 상자"다.
배열보다 실무에서 자주 쓰이는 이유는 크기 관리, 탐색, 중복 처리 규칙이 인터페이스로 표준화되어 있기 때문이다.

가장 중요한 초보자 규칙은 두 가지다.

- 변수는 인터페이스 타입으로 선언한다 (`List`, `Set`, `Map`)
- 구현체는 `new`할 때만 고른다 (`new ArrayList<>()`, `new HashSet<>()`, `new HashMap<>()`)

## 30초 선택 순서: 요구 -> 인터페이스 -> 구현체

처음엔 구현체 이름을 외우기보다, 아래 3단계만 따라가면 된다.

1. 요구를 한 문장으로 적는다.
   예: "가입 순서를 유지해야 하고 중복 이름도 보여 줘야 한다"
2. 요구를 인터페이스로 번역한다 (`List`/`Set`/`Map`).
3. 특별한 이유가 없다면 기본 구현체(`ArrayList`/`HashSet`/`HashMap`)로 시작한다.

핵심은 "구조 이름"보다 "요구 번역"이다.

`컬렉션 큰 그림`, `리스트 셋 맵 차이`, `처음 배우는데 컬렉션`처럼 entry query가 들어오면 이 문서를 첫 진입점으로 잡고, 여기서 `List`/`Set`/`Map` 감각을 먼저 고정한 뒤 개별 follow-up으로 내려가면 된다.

## 처음 배우는데 언제 쓰는지: 15초 답

| 이런 상황이면 | 먼저 떠올릴 것 | 이유 |
|---|---|---|
| 장바구니 상품을 담은 순서대로 보여 주고 싶다 | `List` | 순서와 중복 허용이 핵심 |
| 태그를 한 번만 저장하고 싶다 | `Set` | 자동 중복 제거가 핵심 |
| 회원 id로 회원 정보를 바로 찾고 싶다 | `Map` | key로 조회하는 구조가 핵심 |

처음 배우는 단계에서는 이 3줄만 바로 떠올라도 충분하다.
그다음에야 `ArrayList`/`HashSet`/`HashMap` 같은 첫 구현체를 붙이면 된다.

## 먼저 잡는 멘탈 모델: 3가지 질문

컬렉션 선택이 막히면 아래 순서로 판단하면 된다.

| 질문 | `Yes`면 | `No`면 |
|---|---|---|
| 입력 순서/인덱스가 중요한가? | `List`를 먼저 본다 | 다음 질문으로 |
| 중복을 자동으로 막아야 하나? | `Set`을 먼저 본다 | 다음 질문으로 |
| 키로 빠르게 찾는 조회가 중심인가? | `Map`을 먼저 본다 | 그래도 대부분 `List`에서 시작 |

즉 "자료구조 이름"보다 **문제의 요구사항**이 먼저다.

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
- `LinkedList`는 큐/덱 같은 특수한 접근 패턴에서만 고려

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

### 요구사항을 바로 컬렉션으로 매핑해 보기

| 요구사항 한 줄 | 인터페이스 | 기본 구현체 | 이유 |
|---|---|---|---|
| 게시판 댓글을 작성 순서대로 보여 준다 | `List<Comment>` | `ArrayList` | 순서/인덱스 접근이 핵심 |
| 태그 중복을 자동으로 제거한다 | `Set<String>` | `HashSet` | 존재 여부/중복 제거가 핵심 |
| 사용자 id로 프로필을 바로 찾는다 | `Map<Long, UserProfile>` | `HashMap` | key 기반 조회/갱신이 핵심 |

### "언제 쓰는지"에서 자주 막히는 분기

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

- `ArrayList`와 `LinkedList`를 항상 50:50 선택지로 보면 안 된다. 대부분은 `ArrayList`가 더 단순하고 빠르다.
- `HashMap`의 반복 순서를 로직에 기대하면 안 된다. 순서가 필요하면 `LinkedHashMap` 또는 `TreeMap`으로 의도를 드러내야 한다.
- `HashSet` 중복 제거는 `equals()`만 쓰는 게 아니라 `hashCode()`와 함께 동작한다.
- 정렬 컬렉션(`TreeSet`, `TreeMap`)은 `equals()`보다 `compareTo()`/`Comparator` 기준이 직접 동작한다.
- "중복 제거 + 순서 유지"가 함께 나오면 `List`와 `Set` 중 하나만 억지로 고르지 말고 [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)부터 보면 된다.
- `TreeSet`/`TreeMap`은 "정렬 기준이 같으면 같은 자리"로 본다. 이 차이는 [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)에서 이어서 보면 된다.
- `HashMap`/`HashSet` key나 원소의 비교 기준 필드를 넣은 뒤 바꾸면 조회나 제거가 깨질 수 있다.
- `Collection`(인터페이스)과 `Collections`(유틸리티 클래스)를 같은 것으로 보면 API를 자주 잘못 찾게 된다.
- `Arrays.asList(...)`는 이름 때문에 `ArrayList`처럼 보이지만, 실제로는 `add/remove`가 안 되는 고정 크기 리스트다. 이 함정은 [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./arrays-aslist-fixed-size-list-checklist.md)로 바로 이어서 보면 된다.
- `Map`은 `Collection`의 하위 타입이 아니다. 그래서 `Collection` 전용 API를 `Map`에 바로 적용할 수 없다.
- `Iterable`은 반복 약속이고 `Collection`은 원소 묶음 API다. 계층 자체가 헷갈리면 [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)을 먼저 보고 돌아오면 이해가 빠르다.

헷갈릴 때는 아래처럼 먼저 분류하면 다음 문서로 덜 헤맨다.

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

- 컬렉션 선택, 비교 규칙, mutable key, 순회 중 수정까지 한 장으로 묶어 보고 싶다면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- `first`/`floor`/`ceiling` 탐색까지 보고 싶다면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- 성능 감각을 먼저 보강하고 싶다면 [Java Collections 성능 감각](./collections-performance.md)

## 한 줄 정리

컬렉션 선택은 구현체 이름 암기가 아니라 `순서`, `중복`, `키-값 조회` 세 질문으로 시작하고, 첫 선택은 보통 `ArrayList`, `HashSet`, `HashMap`이다.
