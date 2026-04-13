# TreeMap, HashMap, LinkedHashMap 비교

> 한 줄 요약: `HashMap`은 빠른 조회, `TreeMap`은 정렬과 범위 질의, `LinkedHashMap`은 순서와 LRU 캐시를 위해 선택한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [응용 자료 구조](./advanced.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Java Collections 성능 감각](../language/java/collections-performance.md)

---

## 핵심 개념

`Map` 계열은 모두 `key -> value`를 저장하지만, 무엇을 우선순위로 둘지는 다르다.

| 자료구조 | 강점 | 평균 복잡도 | 순서 보장 |
|------|------|------|------|
| `HashMap` | 빠른 조회/삽입 | `O(1)` | 없음 |
| `TreeMap` | 정렬, 범위 탐색 | `O(log n)` | key 기준 정렬 |
| `LinkedHashMap` | 삽입/접근 순서 | `O(1)` | 있음 |

여기서 중요한 건 "무조건 빠른 Map"은 없다는 점이다.

- 데이터가 많고 조회만 빠르면 `HashMap`
- 정렬된 순회나 `floor/ceiling/subMap`이 필요하면 `TreeMap`
- 캐시처럼 최근 사용 순서가 중요하면 `LinkedHashMap`

이 문서는 `HashMap 내부 구조`를 이미 안다고 가정하고, 언제 어떤 Map을 써야 하는지에 집중한다.

---

## 깊이 들어가기

### 1. `HashMap`은 왜 가장 기본이 되나

`HashMap`은 평균적으로 가장 단순하고 빠르다.  
키를 해시로 바꿔 버킷을 찾기 때문에, 대부분의 단건 조회는 `O(1)`에 가깝다.

하지만 순서를 보장하지 않고, 범위 질의도 어렵다.  
그래서 "단순한 key lookup"이 아니라면 다른 Map을 먼저 떠올려야 한다.

### 2. `TreeMap`은 왜 정렬된 Map인가

`TreeMap`은 해시 테이블이 아니라 **레드-블랙 트리** 기반이다.  
그래서 key를 정렬 기준으로 유지하며 `O(log n)`으로 균형 있게 동작한다.

쓸모가 분명한 API가 많다.

- `firstKey()`, `lastKey()`
- `floorKey()`, `ceilingKey()`
- `subMap()`, `headMap()`, `tailMap()`

즉 `TreeMap`은 "정렬이 필요해서" 쓰는 게 아니라, **범위 질의와 인접 key 탐색이 필요해서** 쓴다.

### 3. `LinkedHashMap`은 왜 캐시에 자주 쓰나

`LinkedHashMap`은 내부적으로 `HashMap`에 **이중 연결 리스트**를 붙여 순서를 기억한다.

순서는 두 가지로 쓸 수 있다.

- 삽입 순서 유지
- 접근 순서 유지

특히 접근 순서 모드는 LRU 캐시에 아주 잘 맞는다.

```java
Map<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 100;
    }
};
```

이 패턴은 "최근에 안 쓴 것부터 제거"가 필요한 상황에서 자주 쓴다.

### 4. key 설계가 Map 선택보다 더 중요할 때도 있다

어떤 Map을 쓰든 key가 흔들리면 결과가 이상해진다.

- `HashMap`은 `hashCode()`와 `equals()` 계약이 중요하다
- `TreeMap`은 `Comparator`가 `equals()`와 충돌하지 않아야 한다
- `LinkedHashMap`은 순서는 지키지만, key 자체 문제는 못 막는다
- `HashMap`은 null key를 허용하지만, `TreeMap`은 자연 정렬 기준에서는 null key를 사실상 허용하지 않는다

특히 `TreeMap`에서 `compareTo()`가 0인데 `equals()`는 false인 객체를 넣으면, "같은 key처럼" 덮어써질 수 있다.

---

## 실전 시나리오

### 시나리오 1: 단순 조회 캐시

```java
Map<Long, User> users = new HashMap<>();
users.put(1L, new User(1L, "donghun"));
```

사용 패턴이 "id로 바로 찾기"라면 `HashMap`이 가장 단순하다.  
정렬도, 접근 순서도 필요 없으면 다른 선택은 오버헤드만 늘린다.

### 시나리오 2: 예약 시간대별 조회

```java
TreeMap<Long, Reservation> reservations = new TreeMap<>();
reservations.put(202604081000L, new Reservation(...));
reservations.put(202604081030L, new Reservation(...));

Long nextSlot = reservations.ceilingKey(202604081015L);
```

이런 경우는 `HashMap`보다 `TreeMap`이 맞다.  
가장 가까운 미래 시점이나 범위 안의 데이터를 찾는 API가 필요하기 때문이다.

### 시나리오 3: LRU 캐시

```java
Map<String, String> lru = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 3;
    }
};

lru.put("a", "1");
lru.put("b", "2");
lru.get("a");
lru.put("c", "3");
lru.put("d", "4");
```

접근 순서 기반 캐시는 `LinkedHashMap`이 가장 빨리 구현된다.  
캐시 정책을 직접 구현하기 전에 먼저 떠올려야 하는 도구다.

### 시나리오 4: 정렬 순회가 필요한 리더보드

점수가 바뀔 때마다 정렬된 상태를 유지해야 한다면 `TreeMap`이 유리하다.  
반면 단순히 빈도만 세면 `HashMap`이 더 싸다.

---

## 코드로 보기

### 비교 코드

```java
Map<String, Integer> hashMap = new HashMap<>();
Map<String, Integer> treeMap = new TreeMap<>();
Map<String, Integer> linkedHashMap = new LinkedHashMap<>();

hashMap.put("b", 2);
hashMap.put("a", 1);

treeMap.put("b", 2);
treeMap.put("a", 1);

linkedHashMap.put("b", 2);
linkedHashMap.put("a", 1);

System.out.println(hashMap);
System.out.println(treeMap);
System.out.println(linkedHashMap);
```

### 범위 조회 코드

```java
TreeMap<Integer, String> schedule = new TreeMap<>();
schedule.put(10, "standup");
schedule.put(13, "deploy");
schedule.put(16, "retro");

Map<Integer, String> afternoon = schedule.subMap(12, true, 18, false);
```

`TreeMap`은 이런 조회가 자연스럽다.  
해시 기반 Map으로는 범위 자체를 표현하기 어렵다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|------|
| `HashMap` | 가장 단순하고 평균적으로 빠름 | 순서/범위 질의 불가 | 기본 조회/저장 |
| `TreeMap` | 정렬, 범위, 인접 key 탐색 가능 | `O(log n)` | 일정표, 범위 조회, 정렬 순회 |
| `LinkedHashMap` | 순서 유지, LRU 구현이 쉬움 | 약간의 오버헤드 | 캐시, 순서가 중요한 로직 |

핵심 판단 기준은 아래처럼 정리할 수 있다.

- key로 정확히 찾기만 하면 `HashMap`
- 정렬된 view가 필요하면 `TreeMap`
- 최근 사용 순서나 삽입 순서가 필요하면 `LinkedHashMap`

---

## 꼬리질문

> Q: `TreeMap`이 `HashMap`보다 느린데도 쓰는 이유는 무엇인가요?  
> 의도: 단순 성능이 아니라 API 요구사항을 보고 있는지 확인
> 핵심: 정렬, 범위 질의, 인접 key 탐색이 필요하면 `O(log n)`을 감수할 가치가 있다.

> Q: `LinkedHashMap`으로 LRU 캐시를 만들면 충분한가요?  
> 의도: 구현 편의와 운영 한계를 구분하는지 확인
> 핵심: 단일 JVM 내부 캐시에는 좋지만, 분산 캐시나 일관성 요구가 있으면 Redis 같은 별도 저장소가 필요하다.

> Q: `TreeMap`의 `Comparator`가 왜 중요한가요?  
> 의도: 정렬 기준과 key 동등성의 차이를 아는지 확인
> 핵심: `compare` 결과가 key의 동등성 판단까지 좌우하므로, 정렬 기준을 잘못 잡으면 덮어쓰기 버그가 난다.

## 한 줄 정리

`HashMap`은 빠른 조회, `TreeMap`은 정렬/범위 질의, `LinkedHashMap`은 순서와 LRU 캐시를 위해 선택한다.
