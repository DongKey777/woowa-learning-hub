# Java 컬렉션 프레임워크 입문

> 한 줄 요약: 컬렉션 프레임워크는 List·Set·Map이라는 세 가지 인터페이스로 데이터를 저장·조회·순회하는 표준 구조를 제공하고, 구현체를 교체해도 코드가 바뀌지 않도록 인터페이스로 선언한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java Collections 성능 감각](./collections-performance.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [language 카테고리 인덱스](../README.md)
- [Java 제네릭 입문](./java-generics-basics.md)

retrieval-anchor-keywords: java collections basics, list set map 입문, arraylist linkedlist 차이, hashmap 입문, 컬렉션 프레임워크 기초, java collection framework beginner, java list 언제 쓰나, java set 중복 제거, java map key value, 컬렉션 어떤 걸 써야 하나요, collection interface beginner, java iterable basics, treeset natural ordering, treemap compareTo key slot, treeset floor ceiling lower higher, treemap floorEntry ceilingEntry beginner, navigablemap navigableset basics

## 핵심 개념

Java 컬렉션 프레임워크(Java Collections Framework)는 여러 개의 객체를 담는 표준 자료구조 모음이다. 배열(`array`)과 달리 크기가 동적으로 늘어나며, 삽입·삭제·조회에 필요한 메서드가 이미 구현되어 있다.

입문자가 헷갈리는 지점은 "어떤 구현체를 골라야 하나"다. 핵심 원칙은 하나다: **변수를 인터페이스 타입으로 선언**하고 구현체는 `new`할 때만 고른다. `List<String> list = new ArrayList<>()`가 맞는 패턴이다.

## 한눈에 보기

```
인터페이스     대표 구현체         특징
List<E>       ArrayList           순서 있음, 중복 허용, 인덱스 접근 O(1)
              LinkedList          순서 있음, 중복 허용, 중간 삽입/삭제 유리
Set<E>        HashSet             순서 없음, 중복 불허, 검색 O(1)
              TreeSet             정렬 순서, 중복 불허, 검색 O(log n)
Map<K,V>      HashMap             키-값 쌍, 키 중복 불허, 검색 O(1)
              TreeMap             키 정렬, 검색 O(log n)
```

## 상세 분해

### List — 순서가 있는 목록

```java
List<String> names = new ArrayList<>();
names.add("Alice");
names.add("Bob");
names.add("Alice");        // 중복 허용
System.out.println(names.get(0)); // "Alice"
```

순서가 보존되고 인덱스로 접근한다. 중복을 허용하므로 같은 이름이 두 번 들어갈 수 있다.

### Set — 중복 없는 집합

```java
Set<String> tags = new HashSet<>();
tags.add("java");
tags.add("backend");
tags.add("java");          // 무시됨
System.out.println(tags.size()); // 2
```

같은 값을 두 번 넣어도 하나만 유지된다. 순서는 보장되지 않는다.

### Map — 키-값 쌍

```java
Map<String, Integer> scores = new HashMap<>();
scores.put("Alice", 90);
scores.put("Bob", 85);
scores.put("Alice", 95);   // 기존 값 덮어씀
System.out.println(scores.get("Alice")); // 95
```

키는 고유하다. 같은 키로 `put`하면 값이 덮어써진다.

## 흔한 오해와 함정

**오해 1: `ArrayList`와 `LinkedList`는 아무거나 써도 된다**
대부분의 경우 `ArrayList`가 빠르다. `LinkedList`는 양 끝에서의 삽입/삭제가 O(1)이지만, 인덱스 접근이 O(n)이라 무작위 접근이 많으면 느리다. 거의 `ArrayList`가 정답이다.

**오해 2: `HashMap`은 순서가 없어도 상관없다**
삽입 순서를 유지하려면 `LinkedHashMap`을, 키를 정렬 순서로 유지하려면 `TreeMap`을 써야 한다. `HashMap`에서 꺼낸 순서는 실행마다 달라질 수 있다.

**오해 3: `Set`에 중복 체크를 `equals`만으로 한다**
`HashSet`은 `hashCode()`로 버킷을 찾고, `equals()`로 동일 여부를 확인한다. `hashCode()`를 재정의하지 않으면 같은 값이라도 다른 객체로 취급될 수 있다.

## 실무에서 쓰는 모습

1. 게시글 목록을 반환할 때 → `List<Post>` (순서 보존, 인덱스 접근)
2. 권한 태그 집합 관리 → `Set<String>` (중복 없이 "ADMIN", "USER" 저장)
3. 사용자 ID → 이름 캐싱 → `Map<Long, String>` (빠른 키 조회)

인터페이스 타입으로 선언해 두면 나중에 `ArrayList` → `LinkedList` 교체 시 코드가 바뀌지 않는다.

## 더 깊이 가려면

- 성능 감각을 키우려면: [Java Collections 성능 감각](./collections-performance.md)
- Set 중복 판단 규칙 세부 사항: [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- `TreeSet`/`TreeMap`이 `Comparator` 없이 `compareTo()`로 중복과 key 자리를 판단하는 흐름: [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- `TreeSet`/`TreeMap`에서 `first`/`last`/`floor`/`ceiling`/`lower`/`higher`가 comparator 순서 위에서 어떻게 동작하는지 보려면: [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

## 면접/시니어 질문 미리보기

**Q. `ArrayList`와 `LinkedList`의 시간 복잡도 차이는?**
`ArrayList`는 인덱스 접근 O(1), 중간 삽입/삭제 O(n). `LinkedList`는 인덱스 접근 O(n), 맨 앞/뒤 삽입/삭제 O(1). 대부분은 `ArrayList`가 유리하다.

**Q. `HashMap`에서 키로 사용할 객체에 필요한 계약은?**
`hashCode()`와 `equals()`를 일관되게 재정의해야 한다. `hashCode()`가 같아야 같은 버킷에 들어가고, `equals()`가 같아야 동일 키로 인식된다.

**Q. `null` 키를 허용하는 Map 구현체는?**
`HashMap`은 `null` 키를 하나 허용한다. `TreeMap`은 `null` 키를 허용하지 않는다(비교 시 NPE). `Hashtable`도 `null` 키를 허용하지 않는다.

## 한 줄 정리

List는 순서·중복 허용, Set은 중복 불허, Map은 키-값 쌍이며, 변수는 인터페이스 타입으로 선언하고 구현체는 `new`할 때만 고른다.
