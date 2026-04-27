# Stable ID as Map Key Primer

> 한 줄 요약: 상태가 바뀌는 도메인 객체를 `Map` key로 직접 쓰기보다, 변하지 않는 ID를 key로 두고 객체는 value로 두면 조회 규칙과 도메인 변경을 더 안전하게 분리할 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Stable ID vs Natural Key Bridge](./stable-id-vs-natural-key-bridge.md)
- [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Map Value-Shape Drill](./map-value-shape-drill.md)

- [카테고리 README](../README.md)

retrieval-anchor-keywords: language-java-00111, stable id as map key primer, immutable id mutable entity map, java map key stable id beginner, mutable entity as map key bug, entity as map value id as key, map memberid member beginner, stable identifier hashmap design, immutable key mutable value java, java domain object map key design, map key should be immutable id, entity vs value object map key, mutable domain object lookup safe pattern, surrogate id map key beginner, natural key vs stable id java

## 먼저 잡을 멘탈 모델

`Map`은 "어떤 서랍 이름으로 찾을까"와 "그 서랍 안에 무엇을 넣을까"를 같이 정하는 구조다.

- key는 서랍 이름이다
- value는 서랍 안 내용물이다

초보자 기본 규칙은 이 한 줄이면 충분하다.

> 바뀌는 객체는 value 쪽에 두고, 찾는 기준은 변하지 않는 ID로 key를 둔다.

즉 "회원" 자체를 key로 두기보다, `회원 ID -> 회원 객체` 구조로 생각하는 편이 안전하다.

## 왜 entity 전체를 key로 두면 흔들리나

도메인 객체는 보통 시간이 지나면서 상태가 바뀐다.

- 회원 이름이 바뀐다
- 주문 상태가 바뀐다
- 세션 만료 시간이 바뀐다

그런데 이런 mutable 객체를 key로 직접 쓰고, 그 mutable 필드가 `equals()`/`hashCode()`에 들어가면 조회 기준도 같이 흔들린다.

```java
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

final class Member {
    private final long id;
    private String name;

    Member(long id, String name) {
        this.id = id;
        this.name = name;
    }

    void rename(String name) {
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Member other)) return false;
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }
}

Map<Member, String> teamByMember = new HashMap<>();
Member member = new Member(1L, "mina");

teamByMember.put(member, "backend");
member.rename("momo");

System.out.println(teamByMember.containsKey(member)); // false가 될 수 있다
```

문제의 핵심은 `Member`가 나쁜 객체라서가 아니다.
`Member`는 원래 바뀌는 대상인데, 그 바뀌는 대상을 "조회 기준" 자리인 key에 앉혔기 때문에 설계가 흔들리는 것이다.

## 더 안전한 기본 패턴: ID를 key, 객체를 value

먼저 ID를 별도 타입으로 분리한다.

```java
record MemberId(long value) {}
```

그다음 mutable 객체는 value로 둔다.

```java
import java.util.HashMap;
import java.util.Map;

record MemberId(long value) {}

final class Member {
    private final MemberId id;
    private String name;
    private String team;

    Member(MemberId id, String name, String team) {
        this.id = id;
        this.name = name;
        this.team = team;
    }

    MemberId id() {
        return id;
    }

    String name() {
        return name;
    }

    String team() {
        return team;
    }

    void rename(String name) {
        this.name = name;
    }

    void changeTeam(String team) {
        this.team = team;
    }
}

Map<MemberId, Member> membersById = new HashMap<>();

Member member = new Member(new MemberId(1L), "mina", "backend");
membersById.put(member.id(), member);

member.rename("momo");
member.changeTeam("platform");

Member loaded = membersById.get(new MemberId(1L));
System.out.println(loaded.name()); // momo
System.out.println(loaded.team()); // platform
```

이 구조에서는 `Member` 내부 상태가 바뀌어도 조회 기준은 `MemberId`라서 흔들리지 않는다.

## 한 장 비교표

| 설계 | key에 무엇을 두나 | 상태 변경 뒤 조회 안정성 | 초보자 추천도 |
|---|---|---|---|
| `Map<Member, ...>` | mutable entity 전체 | 낮음 | 낮음 |
| `Map<MemberId, Member>` | immutable ID | 높음 | 높음 |
| `Map<String, Member>` | 문자열 ID | 상황에 따라 높음 | 중간 |

여기서 가장 초보자 친화적인 기본값은 보통 `Map<MemberId, Member>`다.

- key 의미가 분명하다
- `equals()`/`hashCode()` 경계가 작다
- 이름, 상태, 팀 같은 mutable 필드를 조회 기준에서 분리할 수 있다

## 이 패턴이 실무 감각에도 맞는 이유

도메인에서 "같은 대상"을 추적할 때는 보통 현재 표시값보다 stable identity가 더 중요하다.

| 도메인 필드 | 바뀔 가능성 | key로 적합한가 |
|---|---|---|
| 회원 이름 | 높음 | 보통 아니다 |
| 이메일 | 중간 | 정책에 따라 바뀔 수 있어 신중 |
| DB primary key | 낮음 | 보통 적합 |
| 발급된 주문 번호 | 낮음 | 보통 적합 |

즉 key 후보를 고를 때는 "사람이 보기 좋은 값인가"보다 "시간이 지나도 같은 대상을 계속 가리키는가"를 먼저 본다.

## 자주 하는 오해

- "같은 객체 reference면 key로 써도 안전하지 않나요?"
  - `HashMap`은 reference보다 `hashCode()`/`equals()` 기준으로 조회한다.
- "value가 mutable이면 map도 위험한 것 아닌가요?"
  - 보통 key mutation과 value mutation은 다른 문제다. 조회 경로를 정하는 것은 key다.
- "그럼 entity 안에 `id` 필드가 있어도 entity 자체를 key로 쓰면 안 되나요?"
  - 가능은 하지만, `equals()`/`hashCode()`를 어디에 둘지 헷갈리기 쉬워 초보자에겐 `ID -> entity` 구조가 더 단순하다.
- "ID를 그냥 `Long`으로 써도 되나요?"
  - 작은 예제에서는 가능하다. 다만 `MemberId`, `OrderId`처럼 타입을 나누면 의미와 실수 방지가 더 좋아진다.
- "이메일이나 상품 코드 같은 business key는 언제 써도 되나요?"
  - 불변성, 유일성, canonicalization 정책이 분명할 때만 안전하다. 이 판단은 [Stable ID vs Natural Key Bridge](./stable-id-vs-natural-key-bridge.md)에서 이어서 보면 된다.

## 언제 특히 이 패턴을 먼저 떠올리면 좋나

- "id로 객체를 바로 찾아야 한다"는 요구가 있다
- 객체 내부 상태는 자주 바뀐다
- 이름, 상태, 우선순위 같은 표시 필드는 바뀔 수 있다
- 컬렉션 조회 버그를 미리 피하고 싶다

이런 신호가 보이면 초보자 기본값은 아래처럼 두면 된다.

```java
Map<OrderId, Order> ordersById = new HashMap<>();
Map<ProductId, Product> productsById = new HashMap<>();
Map<SessionId, Session> sessionsById = new HashMap<>();
```

## 빠른 체크리스트

- 이 객체는 시간이 지나며 상태가 바뀌는가?
- map에서 찾는 기준은 정말 그 객체 전체인가, 아니면 ID인가?
- key로 쓰려는 필드는 생성 후 안정적으로 유지되는가?
- mutable 필드가 `equals()`/`hashCode()`에 들어가 있지 않은가?
- 설계가 헷갈리면 `Map<StableId, MutableObject>`로 한 단계 단순화할 수 있는가?

## 다음에 읽으면 좋은 문서

- mutable key 버그가 실제로 어떻게 터지는지 보려면 [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- surrogate ID와 business key를 `email`/`code`/`name` 기준으로 비교하려면 [Stable ID vs Natural Key Bridge](./stable-id-vs-natural-key-bridge.md)
- value object와 entity 구분이 더 헷갈리면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- `Map<K, V>`에서 value를 어떤 모양으로 둬야 할지 막히면 [Map Value-Shape Drill](./map-value-shape-drill.md)

## 한 줄 정리

mutable domain object를 key로 붙잡기보다, stable ID로 찾고 객체는 value로 두면 `Map`의 조회 규칙과 도메인 상태 변경을 더 깔끔하게 분리할 수 있다.
