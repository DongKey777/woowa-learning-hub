# HashMap 내부 구조

> 한 줄 요약: `HashMap`은 평균적으로 빠르지만, 키 설계와 충돌 처리, 리사이즈 비용을 모르면 쉽게 느려지고 심지어 값을 잃은 것처럼 보일 수 있는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [응용 자료 구조](./advanced.md)
> - [Java Collections 성능 감각](../language/java/collections-performance.md)

---

## 핵심 개념

`HashMap`은 `key -> value`를 저장하는 해시 테이블이다. 핵심은 **키를 바로 찾는 것**이 아니라, 키를 해시값으로 바꿔 **버킷(bucket)** 을 빠르게 찾는 데 있다.

Java 8+ `HashMap`은 기본적으로 다음 흐름으로 동작한다.

1. `key.hashCode()`로 해시값을 구한다.
2. 해시를 한 번 섞어 분포를 고르게 만든다.
3. 현재 테이블 크기에 맞춰 버킷 인덱스를 계산한다.
4. 해당 버킷에서 충돌을 처리한다.

중요한 사실은 `HashMap`의 성능이 단순히 "해시를 쓰니까 빠르다"로 끝나지 않는다는 점이다.

- 키의 `hashCode()`가 잘 분산되어야 한다.
- `equals()`와 `hashCode()` 계약이 맞아야 한다.
- 테이블이 너무 작으면 리사이즈가 자주 발생한다.
- 충돌이 많으면 버킷 내부 구조가 길어진다.

---

## 깊이 들어가기

### 1. 버킷 인덱스는 어떻게 정해지나

`HashMap`은 보통 배열 기반이다. 해시값을 그대로 인덱스로 쓰지 않고, 배열 크기 `n`에 맞춰 다음처럼 위치를 계산한다.

```text
index = (n - 1) & hash
```

배열 크기가 2의 거듭제곱이기 때문에 `%` 연산보다 빠르고, 비트 마스킹으로 인덱스를 구할 수 있다.

또 `HashMap`은 해시 분포를 조금 더 고르게 만들기 위해 상위 비트를 아래로 섞는 과정을 거친다.

```java
static final int spread(int h) {
    return h ^ (h >>> 16);
}
```

이 단계는 같은 하위 비트만 반복되는 해시를 어느 정도 완화한다.

### 2. 충돌은 어떻게 처리하나

다른 키가 같은 버킷으로 들어오면 충돌이 발생한다. `HashMap`은 충돌을 다음 방식으로 다룬다.

- 기본적으로 버킷 내부를 연결 리스트처럼 이어 붙인다.
- 충돌이 너무 많아지면 레드-블랙 트리로 바꾼다.

JDK 8 기준 대표 임계값은 다음과 같다.

| 항목 | 값 | 의미 |
|------|----|------|
| `TREEIFY_THRESHOLD` | 8 | 버킷 내 노드 수가 이 이상이면 트리화를 고려 |
| `UNTREEIFY_THRESHOLD` | 6 | 트리 노드 수가 이 이하로 줄면 다시 리스트화 |
| `MIN_TREEIFY_CAPACITY` | 64 | 테이블이 이보다 작으면 트리화 대신 resize 우선 |

즉, 충돌이 많다고 무조건 트리로 바뀌는 건 아니다. 테이블이 너무 작으면 먼저 크게 늘린다.

### 3. resize는 왜 비싼가

`HashMap`은 원소 수가 임계치를 넘으면 테이블 크기를 보통 2배로 늘린다.

```text
threshold = capacity x loadFactor
```

기본 `loadFactor`는 `0.75`다.  
예를 들어 capacity가 16이면 threshold는 12이고, 13번째 삽입에서 resize가 발생한다.

resize는 단순히 배열만 키우는 게 아니다.

- 새 배열을 할당한다.
- 기존 노드들을 새 인덱스로 옮긴다.
- 충돌 체인을 다시 배치한다.

JDK 8의 구현은 모든 키를 다시 해시하는 대신, 기존 해시의 특정 비트를 보고 `기존 인덱스` 또는 `기존 인덱스 + oldCapacity`로 나눈다.  
이 최적화 덕분에 불필요한 계산을 줄인다.

### 4. 평균 O(1), 최악 O(n), 트리화 후 O(log n)

`HashMap`은 평균적으로 `get`, `put`이 `O(1)`에 가깝다.  
하지만 이것은 해시 분포가 좋고 충돌이 적다는 가정이 깔려 있다.

상황별로 보면:

- 평균적인 경우: `O(1)`
- 충돌이 심한 연결 리스트 버킷: `O(n)`
- 트리화된 버킷: `O(log n)`

그래서 `HashMap`은 예전보다 최악 케이스가 완화되었지만, 키 설계를 잘못하면 여전히 느려질 수 있다.

### 5. `equals()`와 `hashCode()`가 맞지 않으면

`HashMap`은 먼저 해시로 후보 버킷을 찾고, 그 다음 `equals()`로 실제 같은 키인지 판정한다.

따라서 다음 원칙이 깨지면 문제가 생긴다.

- `equals()`가 같으면 `hashCode()`도 같아야 한다.
- 키는 가능한 한 불변이어야 한다.
- `equals()` 비교 기준이 도메인 의미와 일치해야 한다.

이 계약이 깨지면, 같은 객체를 넣었는데 못 찾거나 중복 키처럼 보일 수 있다.

---

## 실전 시나리오

### 시나리오 1: mutable key 때문에 값이 사라진 것처럼 보임

```java
class UserKey {
    private String email;

    UserKey(String email) {
        this.email = email;
    }

    public void changeEmail(String email) {
        this.email = email;
    }

    @Override
    public int hashCode() {
        return email.hashCode();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserKey)) return false;
        UserKey userKey = (UserKey) o;
        return email.equals(userKey.email);
    }
}

Map<UserKey, String> map = new HashMap<>();
UserKey key = new UserKey("a@site.com");
map.put(key, "member");

key.changeEmail("b@site.com");
System.out.println(map.get(key)); // null처럼 보일 수 있다
```

문제는 `HashMap`이 아니라 **키를 바꿔버린 설계**다.  
해시값이 바뀌면 이전 버킷에서 더 이상 같은 키를 찾지 못한다.

### 시나리오 2: 해시 분포가 나빠서 충돌이 몰림

```java
class BadKey {
    private final int id;

    BadKey(int id) {
        this.id = id;
    }

    @Override
    public int hashCode() {
        return 1; // 일부러 최악의 충돌을 만든다
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof BadKey)) return false;
        return id == ((BadKey) o).id;
    }
}
```

이런 키가 많아지면 버킷 하나에 데이터가 몰리고, 결국 조회 성능이 급격히 떨어진다.

### 시나리오 3: 초기 용량을 너무 작게 잡아 resize 폭탄이 남

```java
Map<Long, String> map = new HashMap<>();
for (long i = 0; i < 1_000_000; i++) {
    map.put(i, "v" + i);
}
```

원소 수를 대략 알고 있다면 초기 용량을 미리 잡는 편이 낫다.  
아무 생각 없이 기본 생성자를 쓰면 여러 번 resize가 발생할 수 있다.

### 시나리오 4: 멀티스레드에서 HashMap을 공유함

`HashMap`은 thread-safe가 아니다.  
읽기만 하는 구간이 아니라면 외부 동기화나 `ConcurrentHashMap`을 검토해야 한다.

### 시나리오 5: HashMap의 순서를 믿고 로직을 작성함

```java
Map<String, Integer> map = new HashMap<>();
map.put("a", 1);
map.put("b", 2);
map.put("c", 3);
```

`HashMap`은 삽입 순서도, 정렬 순서도 보장하지 않는다.  
테이블이 리사이즈되거나 충돌 구조가 바뀌면 순회 결과가 달라질 수 있다.

순서가 필요하면 `LinkedHashMap`, 정렬이 필요하면 `TreeMap`을 봐야 한다.

---

## 코드로 보기

### 예상 크기를 기준으로 초기 용량 계산

`HashMap`은 load factor를 감안해 미리 넉넉하게 잡는 게 좋다.

```java
static int tableSizeFor(int expectedSize, float loadFactor) {
    int target = (int) Math.ceil(expectedSize / loadFactor);
    int n = 1;
    while (n < target) {
        n <<= 1;
    }
    return n;
}

int capacity = tableSizeFor(1_000_000, 0.75f);
Map<Long, String> map = new HashMap<>(capacity);
```

### 안전한 키 설계 예시

```java
final class UserId {
    private final long value;

    UserId(long value) {
        this.value = value;
    }

    @Override
    public int hashCode() {
        return Long.hashCode(value);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserId)) return false;
        return value == ((UserId) o).value;
    }
}
```

불변 키를 쓰면 버킷 위치가 실행 중에 바뀌지 않는다.

### 조회와 삽입에서 자주 쓰는 API

```java
Map<String, Integer> counts = new HashMap<>();

counts.put("java", 1);
counts.putIfAbsent("java", 10);
counts.computeIfAbsent("kotlin", key -> 0);
counts.merge("java", 1, Integer::sum);
```

중복 체크와 누적은 `containsKey()` 후 `put()`보다 이런 메서드가 더 명시적이다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|--------|------|------|----------------|
| 기본 `HashMap` | 단순하고 빠르다 | 크기 추정이 없으면 resize 비용이 늘 수 있다 | 일반적인 단건 조회/저장 |
| 초기 용량을 미리 잡은 `HashMap` | resize를 줄일 수 있다 | 예상 크기를 알아야 한다 | 대량 적재, 배치성 처리 |
| `LinkedHashMap` | 삽입/접근 순서 보장 | 약간의 메모리 오버헤드 | 캐시, 순서가 중요한 경우 |
| `TreeMap` | 정렬과 범위 탐색이 된다 | `O(log n)`이고 해시보다 느리다 | 정렬된 순회, 범위 질의 |
| `ConcurrentHashMap` | 멀티스레드에 안전하다 | 단일 스레드보다 무거울 수 있다 | 공유 캐시, 병렬 업데이트 |

핵심 판단은 다음과 같다.

- 순서가 필요하면 `HashMap`보다 다른 맵을 봐야 한다.
- 크기가 크고 미리 알 수 있으면 초기 용량을 잡아야 한다.
- 키가 변하면 안 된다.
- 동시에 여러 스레드가 접근하면 `HashMap`은 피해야 한다.

---

## 꼬리질문

> Q: `HashMap`은 왜 평균적으로 O(1)인가요?  
> 의도: 해시 분포, 버킷 구조, 충돌 처리 이해 여부 확인  
> 핵심: 인덱스를 바로 계산하고 대부분의 버킷이 짧기 때문이다.

> Q: 충돌이 많아지면 무조건 트리로 바뀌나요?  
> 의도: JDK 8 treeification 조건 이해 여부 확인  
> 핵심: 버킷이 8개를 넘고, 테이블 크기가 64 이상일 때 트리화를 고려한다.

> Q: `loadFactor`를 왜 0.75로 두나요?  
> 의도: 메모리와 성능의 균형 감각 확인  
> 핵심: 너무 높으면 충돌이 늘고, 너무 낮으면 메모리 낭비가 커진다.

> Q: 키 객체의 필드를 바꾸면 왜 문제가 되나요?  
> 의도: mutable key 버그 인지 여부 확인  
> 핵심: `hashCode()`가 바뀌면 버킷 위치가 달라져 기존 값을 찾지 못한다.

---

## 한 줄 정리

`HashMap`은 해시 분포와 충돌 처리 위에서 평균 O(1)을 제공하지만, 키를 불변으로 설계하고 크기와 용도를 맞춰 써야 실제로 빠르다.
