# Java `equals`, `hashCode`, `Comparable` 계약

> 한 줄 요약: 같은 객체를 같은 객체로 인정하는 기준과 정렬 기준을 제대로 설계해야 `HashMap`, `HashSet`, `TreeMap`, `TreeSet`이 예측 가능하게 동작한다.

**난이도: 🔴 Advanced**

## 핵심 개념

이 주제는 단순히 "오버라이딩 규칙"을 외우는 문제가 아니다.  
백엔드 코드에서는 **중복 제거**, **캐시 키**, **컬렉션 조회**, **정렬**, **도메인 식별자 비교**가 전부 여기서 갈린다.

### 먼저 구분해야 할 세 가지

- `equals`
  - 두 객체가 논리적으로 같은지 판단한다.
  - 예: 같은 사용자 ID를 가리키는 두 객체를 같은 것으로 볼지
- `hashCode`
  - 해시 기반 컬렉션에서 버킷을 찾기 위한 숫자다.
  - `HashMap`, `HashSet`에서 필수다.
- `Comparable.compareTo`
  - 객체의 자연 순서(natural ordering)를 정의한다.
  - `TreeSet`, `TreeMap`, 정렬 API에서 중요하다.

### 반드시 기억할 계약

- `equals()`가 `true`면 `hashCode()`도 같아야 한다.
- `compareTo()`가 `0`인 객체는, 가능하면 `equals()`와도 일관되어야 한다.
- `hashCode()`가 같다고 해서 `equals()`까지 같다는 뜻은 아니다.
- 정렬 기준과 동등성 기준은 같은 개념이 아니다.

### 왜 백엔드에서 중요하나

- 캐시 키가 잘못되면 같은 요청이 캐시 미스를 낸다.
- DTO나 엔티티를 `Set`에 넣었을 때 중복 제거가 깨질 수 있다.
- `TreeSet`에서 `compareTo()`가 부정확하면 데이터가 "사라진 것처럼" 보인다.
- JPA 엔티티의 `id`가 생성 전후로 달라지면 `hashCode()`가 바뀌는 버그가 난다.

### retrieval anchors

이 문서는 다음 키워드로 회수되도록 설계하면 좋다.

- `equals`
- `hashCode`
- `Comparable`
- `Comparator`
- `HashMap`
- `HashSet`
- `TreeMap`
- `TreeSet`
- `mutable key`
- `BigDecimal`
- `BigDecimal scale`
- `scale-sensitive equality`
- `money equality`
- `JPA entity identity`
- `natural ordering`
- `comparison consistency`
- `canonical representation`
- `IntegerCache`
- `wrapper equality`
- `autoboxing`

### 관련 문서

- [HashMap 내부 구조](../data-structure/hashmap-internals.md)
- [Java Collections 성능 감각](./java/collections-performance.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./java/bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
- [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./java/autoboxing-integercache-null-unboxing-pitfalls.md)
- [TreeMap, HashMap, LinkedHashMap 비교](../data-structure/treemap-vs-hashmap-vs-linkedhashmap.md)
- [ClassLoader, Exception 경계, 객체 계약](./java/classloader-exception-boundaries-object-contracts.md)

## 깊이 들어가기

### 1. `equals`는 "값"을, `==`는 "참조"를 본다

`==`는 객체가 같은 메모리 주소를 가리키는지 본다.  
반면 `equals`는 도메인 관점에서 같은 값인지 판단한다.

예를 들어 주문 번호가 같은 두 `Order` 객체는, 서로 다른 인스턴스여도 같은 주문으로 볼 수 있다.

이 차이는 wrapper type에서 더 자주 함정이 된다.  
`Integer`나 `Long`의 `==`는 cache와 reference semantics 때문에 더 헷갈릴 수 있다.

### 2. `hashCode`는 왜 `equals`와 묶여 있나

`HashMap`은 먼저 해시값으로 버킷을 찾고, 그 다음 `equals()`로 정확히 같은 키인지 확인한다.  
그래서 `equals`만 맞고 `hashCode`가 다르면, 같은 객체인데도 다른 버킷으로 흩어진다.

즉 해시 기반 컬렉션의 흐름은 이렇다.

1. `hashCode()`로 후보 버킷을 찾는다.
2. 충돌이 있으면 같은 버킷 안에서 `equals()`로 비교한다.
3. 같은 키면 덮어쓰고, 아니면 새 노드를 추가한다.

이 구조 때문에 `hashCode`는 "빠른 탐색용", `equals`는 "정확성용"이다.

### 3. `Comparable`은 자연 순서를 정의한다

`Comparable`은 객체 내부에 "정렬 기준"을 심는 방식이다.

- 나이순 사용자 정렬
- 점수순 순위 정렬
- 생성일순 정렬

같은 도메인에서도 정렬 기준은 여러 개일 수 있으므로, 모든 경우를 `Comparable`로 해결하려고 하면 오히려 설계가 뻣뻣해진다.

### 4. `Comparator`는 외부 정렬 전략이다

`Comparator`는 객체 자체의 자연 순서가 아니라, 상황별 정렬 규칙을 바꿔 끼울 때 쓴다.

- 이름순으로 볼 때
- 최신순으로 볼 때
- 점수 내림차순으로 볼 때

이 차이는 면접에서 자주 나온다.  
`Comparable`은 객체가 "스스로" 순서를 가진 것이고, `Comparator`는 "외부에서" 순서를 주입하는 것이다.

### 5. 가장 위험한 지점은 mutable key다

`equals`와 `hashCode`가 아무리 맞아도, key의 필드가 바뀌면 해시 기반 컬렉션은 깨진다.

- `email`이 바뀐 `UserKey`
- `id`가 생성 전후로 달라진 JPA 엔티티
- `status`를 key로 넣어놓고 상태를 바꿔버린 객체

이런 경우 `map.get(key)`가 갑자기 `null`처럼 보인다.  
문제는 컬렉션이 아니라 **키가 불변이어야 하는 설계 원칙**을 놓친 것이다.

### 6. `compareTo == 0`와 `equals == true`가 충돌하면 왜 위험한가

정렬 컬렉션은 `equals`보다 `compareTo`를 우선한다.  
그래서 `compareTo == 0`인 두 객체가 `equals == false`여도, `TreeSet`에서는 같은 값처럼 취급되어 하나가 사라질 수 있다.

대표 예가 `BigDecimal`이다.

- `new BigDecimal("1.0").equals(new BigDecimal("1.00"))` -> `false`
- `new BigDecimal("1.0").compareTo(new BigDecimal("1.00"))` -> `0`

이 차이를 모르고 `Set`이나 `Map` 정렬 로직을 짜면, "왜 하나가 안 들어가지?" 같은 버그가 생긴다.
여기에 `stripTrailingZeros()`, `toPlainString()`, `MathContext` 같은 표현 정책까지 섞이면 더 헷갈려진다. 자세한 함정은 [BigDecimal MathContext, stripTrailingZeros(), and Canonicalization Traps](./java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)에서 이어서 볼 수 있다.

## 실전 시나리오

### 시나리오 1: HashMap key를 수정해서 값을 잃은 것처럼 보인다

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

class UserKey {
    private String email;

    UserKey(String email) {
        this.email = email;
    }

    void changeEmail(String email) {
        this.email = email;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserKey userKey)) return false;
        return Objects.equals(email, userKey.email);
    }

    @Override
    public int hashCode() {
        return Objects.hash(email);
    }
}

Map<UserKey, String> map = new HashMap<>();
UserKey key = new UserKey("a@site.com");
map.put(key, "member");

key.changeEmail("b@site.com");
System.out.println(map.get(key)); // null처럼 보일 수 있다
```

이 버그는 "HashMap이 이상하다"가 아니라, 키의 해시 기준이 중간에 바뀐 것이다.

### 시나리오 2: TreeSet에서 데이터가 하나 사라진다

```java
import java.math.BigDecimal;
import java.util.Set;
import java.util.TreeSet;

Set<BigDecimal> prices = new TreeSet<>();
prices.add(new BigDecimal("1.0"));
prices.add(new BigDecimal("1.00"));

System.out.println(prices.size()); // 1
```

`compareTo()` 기준으로는 둘이 같은 값이므로, `TreeSet`은 하나만 남긴다.  
금액, 수량, 순위 같은 도메인에서 이런 차이를 모르면 데이터 누락처럼 보이는 장애가 난다.

### 시나리오 3: JPA 엔티티를 Set key로 썼다가 persist 후 조회가 깨진다

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

class Member {
    Long id;
    final String email;

    Member(Long id, String email) {
        this.id = id;
        this.email = email;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Member member)) return false;
        return Objects.equals(id, member.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}

Set<Member> members = new HashSet<>();
Member member = new Member(null, "user@site.com");
members.add(member);

member.id = 10L; // persist 후 ID가 생김
System.out.println(members.contains(member)); // 예상과 다르게 동작할 수 있다
```

엔티티의 식별자를 `hashCode()`에 직접 쓰면, 영속화 전후로 키가 변한다.  
이럴 땐 key로 둘 객체를 따로 두거나, 불변 식별자를 기준으로 설계해야 한다.

## 코드로 보기

### 1. 안전한 값 객체 예시

```java
public final class UserId implements Comparable<UserId> {
    private final long value;

    public UserId(long value) {
        this.value = value;
    }

    public long value() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof UserId userId)) return false;
        return value == userId.value;
    }

    @Override
    public int hashCode() {
        return Long.hashCode(value);
    }

    @Override
    public int compareTo(UserId other) {
        return Long.compare(this.value, other.value);
    }
}
```

이 패턴은 백엔드에서 가장 안전한 기본형이다.  
식별자는 불변으로 두고, `equals`, `hashCode`, `compareTo`를 일관되게 맞춘다.

### 2. Comparator로 정렬 전략을 분리하는 예시

```java
import java.util.Comparator;
import java.util.List;

record User(String name, int score, long createdAt) {}

List<User> users = List.of(
    new User("min", 90, 3L),
    new User("jun", 90, 1L),
    new User("ana", 80, 2L)
);

users.stream()
    .sorted(Comparator.comparingInt(User::score).reversed()
        .thenComparingLong(User::createdAt))
    .forEach(System.out::println);
```

같은 `User`라도 "점수순", "최신순", "이름순"은 모두 다른 요구다.  
이럴 때 `Comparable` 하나에 억지로 몰아넣기보다 `Comparator`를 쓰는 편이 더 유연하다.

### 3. `compareTo`와 `equals` 충돌을 의식한 설계

```java
import java.math.BigDecimal;
import java.util.Comparator;
import java.util.TreeSet;

TreeSet<BigDecimal> prices = new TreeSet<>(
    Comparator.comparing(BigDecimal::stripTrailingZeros)
              .thenComparing(BigDecimal::toPlainString)
);
```

이처럼 도메인 요구에 따라 "정렬 시 같은 값"의 정의를 명시해야 한다.  
단순한 자연 순서만 믿지 말고, 실제 비즈니스 의미를 먼저 확인해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `equals` + `hashCode`만 구현 | `HashMap`, `HashSet`에서 안전하게 동작 | 정렬 기준은 별도 필요 | ID 기반 조회, 중복 제거 |
| `Comparable` 구현 | 객체가 자연 순서를 가짐 | 순서 기준이 하나로 고정됨 | 한 가지 정렬이 사실상 표준일 때 |
| `Comparator` 사용 | 정렬 전략을 유연하게 바꿀 수 있음 | 호출 지점에서 매번 규칙을 넘겨야 함 | 화면/요청마다 정렬이 다를 때 |
| `equals/hashCode`와 `compareTo`를 동일 기준으로 맞춤 | 컬렉션 간 일관성이 좋아짐 | 도메인에 따라 표현력이 부족할 수 있음 | 값 객체, 순서가 곧 동일성일 때 |
| `Comparator`에 tie-breaker 추가 | `TreeSet`/`TreeMap` 중복 손실 방지 | 규칙이 길어지고 복잡해짐 | 동일 점수, 동일 날짜 같은 동률이 많은 도메인 |

실무 판단 기준은 단순하다.

- 해시 기반 조회가 핵심이면 `equals/hashCode`
- 정렬이 핵심이면 `Comparable` 또는 `Comparator`
- 둘 다 필요하면, 정렬 기준과 동일성 기준이 충돌하지 않는지 먼저 본다

## 꼬리질문

> Q: `equals()`가 같으면 왜 `hashCode()`도 같아야 하나요?

의도: 해시 기반 컬렉션의 버킷 탐색 과정을 이해하는지 확인한다.  
핵심: `HashMap`은 해시로 후보를 찾고, `equals`로 최종 판단한다. 해시가 다르면 같은 객체를 못 찾는다.

> Q: `compareTo() == 0`인데 `equals()`가 `false`면 왜 문제가 되나요?

의도: `TreeSet`, `TreeMap`이 `compareTo`를 기준으로 중복을 판단한다는 점을 아는지 확인한다.  
핵심: 정렬 컬렉션에서 데이터가 하나로 합쳐지거나 덮어써질 수 있다.

> Q: `hashCode()`가 같으면 같은 객체인가요?

의도: 해시 충돌과 동등성을 구분하는지 본다.  
핵심: 아니다. 같은 해시값은 충돌일 뿐이고, 진짜 동등성은 `equals()`가 판단한다.

> Q: 왜 key 객체는 보통 immutable이어야 하나요?

의도: 컬렉션 버그를 설계 단계에서 예방할 수 있는지 본다.  
핵심: key의 상태가 바뀌면 해시값이나 비교 결과가 바뀌어 조회가 깨진다.

> Q: `BigDecimal`은 왜 `compareTo()`와 `equals()`가 다르게 동작하나요?

의도: 실무에서 자주 터지는 정렬/중복 버그를 아는지 확인한다.  
핵심: 값의 숫자 의미와 scale을 같은 개념으로 볼지 여부가 다르기 때문이다.

> Q: `Comparator`를 쓰면 `Comparable`은 없어도 되나요?

의도: 자연 순서와 외부 정렬 전략의 역할을 구분하는지 본다.  
핵심: 대부분의 경우 가능하지만, 객체가 공통적으로 가져야 할 기본 정렬이 있다면 `Comparable`이 더 자연스럽다.

## 한 줄 정리

`equals`는 논리적 동등성, `hashCode`는 해시 기반 조회, `Comparable`과 `Comparator`는 정렬 기준이다.  
백엔드에서는 이 셋을 일관되게 설계해야 `HashMap`, `HashSet`, `TreeMap`, `TreeSet`에서 데이터가 안 사라지고, 조회와 정렬이 예측 가능하게 동작한다.
