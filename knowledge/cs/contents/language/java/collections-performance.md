# Java Collections 성능 감각

**난이도: 🔴 Advanced**

> 자료구조를 외우는 것보다, "언제 어떤 구현체가 느려지는가"를 빠르게 판단하기 위한 정리

> 관련 문서:
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
> - [`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs](./concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs.md)
> - [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
> - [`CopyOnWriteArrayList` Snapshot Iteration and Write Amplification](./copyonwritearraylist-snapshot-iteration-write-amplification.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [Object Pooling Myths in the Modern JVM](./object-pooling-myths-modern-jvm.md)

> retrieval-anchor-keywords: Java collections, HashMap, LinkedHashMap, TreeMap, ArrayList, LinkedList, collection performance, lookup pattern, insertion pattern, ordering, compareTo, equals, ConcurrentHashMap, hot key, ConcurrentSkipListMap, ConcurrentLinkedQueue, CopyOnWriteArraySet, BlockingQueue, TransferQueue, ConcurrentSkipListSet, CopyOnWriteArrayList, snapshot iteration, autoboxing, boxing overhead, wrapper collection

<details>
<summary>Table of Contents</summary>

- [왜 성능 감각이 필요한가](#왜-성능-감각이-필요한가)
- [컬렉션 선택 기준](#컬렉션-선택-기준)
- [Hash 기반 컬렉션의 핵심](#hash-기반-컬렉션의-핵심)
- [Tree 기반 컬렉션의 핵심](#tree-기반-컬렉션의-핵심)
- [List에서 자주 헷갈리는 지점](#list에서-자주-헷갈리는-지점)
- [실전 선택 예시](#실전-선택-예시)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 성능 감각이 필요한가

Collections은 API 사용법보다 **접근 패턴**이 중요하다.

- 조회가 많은지
- 삽입/삭제가 많은지
- 정렬이 필요한지
- 순서 보장이 필요한지
- 동시 접근이 있는지

이 다섯 가지에 따라 자료구조 선택이 달라진다.

---

## 컬렉션 선택 기준

### 먼저 물어볼 것

- 키로 빠르게 찾는가?
- 순서가 중요한가?
- 중복을 허용하는가?
- 정렬이 필요한가?

### 기본 감각

- `HashMap`, `HashSet`
  - 평균적으로 빠른 조회
  - 순서 보장 없음
- `LinkedHashMap`, `LinkedHashSet`
  - 삽입 순서 보장
  - 해시 기반 특성은 유지
- `TreeMap`, `TreeSet`
  - 정렬 보장
  - 해시보다 보통 느리지만 정렬 요구를 만족
- `ArrayList`
  - 인덱스 기반 조회가 빠름
  - 중간 삽입/삭제는 비용이 큼
- `LinkedList`
  - 노드 연결 구조
  - 임의 접근이 잦으면 불리함

---

## Hash 기반 컬렉션의 핵심

`HashMap`과 `HashSet`은 해시값을 이용해 버킷을 찾는다.

### 장점

- 평균적으로 `put`, `get`, `contains`가 빠르다
- 대량 조회에 강하다

### 주의할 점

- 해시 충돌이 많아지면 성능이 떨어진다
- `hashCode()`와 `equals()` 구현이 중요하다
- 키 객체가 mutable하면 조회 실패나 중복 문제가 생길 수 있다

### 실전 포인트

- 키는 가능하면 불변 객체를 사용한다
- `equals()`만 맞고 `hashCode()`가 틀리면 Hash 컬렉션이 깨진다
- `HashMap`의 성능은 키 분포와 해시 품질에 크게 좌우된다

---

## Tree 기반 컬렉션의 핵심

`TreeMap`과 `TreeSet`은 정렬된 상태를 유지한다.

### 장점

- 정렬된 순서로 순회 가능
- 범위 검색에 유리하다

예:

- 특정 값 이상만 조회
- 최소/최대값 자주 조회
- 정렬된 결과가 바로 필요한 경우

### 주의할 점

- 해시 기반보다 일반적으로 느리다
- 비교 기준이 일관되어야 한다
- `compareTo()`와 `equals()`의 일관성이 중요하다

---

## List에서 자주 헷갈리는 지점

### `ArrayList`

- 내부적으로 연속된 배열을 사용한다
- 인덱스 접근이 빠르다
- 뒤에 추가하는 작업에 강하다
- 중간 삽입/삭제는 뒤 요소 이동 비용이 든다

### `LinkedList`

- 각 원소가 이전/다음 노드와 연결된다
- 중간 위치를 이미 알고 있으면 삽입/삭제는 상대적으로 편하다
- 하지만 임의 접근이 많으면 탐색 비용 때문에 불리하다

### 실전 감각

- 대부분의 서비스 코드에서는 `ArrayList`가 기본값이다
- `LinkedList`는 "연결되어 있으니 무조건 빠르다"가 아니다
- 실제 병목은 탐색 방식과 접근 패턴에서 결정된다

---

## 실전 선택 예시

### 1. 사용자 ID로 회원 정보를 빠르게 찾고 싶다

- 후보: `HashMap<Long, User>`
- 이유: 키 기반 조회가 핵심이기 때문

### 2. 최근 방문 순서까지 유지하며 캐시처럼 쓰고 싶다

- 후보: `LinkedHashMap`
- 이유: 순서 보장과 해시 조회를 같이 얻을 수 있기 때문

### 3. 점수순으로 항상 정렬된 상태가 필요하다

- 후보: `TreeMap`, `TreeSet`
- 이유: 정렬된 결과가 자료구조의 본질이기 때문

### 4. 응답 목록을 인덱스로 자주 읽는다

- 후보: `ArrayList`
- 이유: 읽기 접근이 빠르기 때문

---

## 면접에서 자주 나오는 질문

### Q. `LinkedList`가 `ArrayList`보다 항상 빠른가요?

- 아니다. 임의 접근이 많으면 `ArrayList`가 더 유리한 경우가 많다.

### Q. `HashMap`이 빠른 이유는 무엇인가요?

- 해시를 통해 버킷을 바로 찾기 때문에 평균적으로 빠르다.

### Q. `TreeMap`을 쓰는 이유는 무엇인가요?

- 정렬된 순서와 범위 검색이 필요할 때 적합하기 때문이다.

### Q. 컬렉션 선택의 핵심 기준은 무엇인가요?

- 조회, 삽입/삭제, 정렬, 순서, 중복 허용 여부다.
