# HashSet Mutable Element Removal Drill

> 한 줄 요약: `HashSet`에 넣은 원소의 `equals()`/`hashCode()` 기준 필드를 바꾸면, `contains()`와 `remove()`가 둘 다 같은 이유로 실패할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: hashset mutable element removal drill basics, hashset mutable element removal drill beginner, hashset mutable element removal drill intro, java basics, beginner java, 처음 배우는데 hashset mutable element removal drill, hashset mutable element removal drill 입문, hashset mutable element removal drill 기초, what is hashset mutable element removal drill, how to hashset mutable element removal drill
> 관련 문서:
> - [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
> - [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

> retrieval-anchor-keywords: language-java-00121, hashset mutable element removal drill, hashset contains remove both fail after mutation, hashset mutable equals hashcode field worksheet, hashset remove false after mutating equals hashCode, hashset contains false remove false same object, java hashset mutable element prediction drill, equals hashCode mutation remove failure beginner, same reference hashset remove false, 자바 hashset remove 실패 연습, 자바 hashset contains remove 둘 다 실패, equals hashCode 필드 변경 remove 버그, hashset 가변 원소 워크시트

## 먼저 잡을 mental model

이번 드릴은 이 두 줄만 먼저 기억하면 된다.

- `HashSet`은 현재 `hashCode()`로 bucket을 찾고, 그 안에서 `equals()`를 본다
- 원소를 넣은 뒤 필드가 바뀌어도 `HashSet`은 그 원소를 새 bucket으로 옮겨 주지 않는다

그래서 초보자용 결론은 한 줄이다.

> `contains()`가 현재 bucket을 못 찾으면 `remove()`도 같은 이유로 같이 실패하기 쉽다.

## 10초 예측표

| 상황 | 결과 예측 |
|---|---|
| `add(user)` 직후 `contains(user)` | `true` |
| `equals()`/`hashCode()` 기준 필드 변경 후 `contains(user)` | `false` 가능 |
| 같은 상태에서 `remove(user)` | `false` 가능 |

## 드릴 코드

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

final class User {
    private String login;

    User(String login) {
        this.login = login;
    }

    void rename(String login) {
        this.login = login;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User other)) return false;
        return Objects.equals(login, other.login);
    }

    @Override
    public int hashCode() {
        return Objects.hash(login);
    }

    @Override
    public String toString() {
        return "User{login=" + login + "}";
    }
}

Set<User> users = new HashSet<>();
User user = new User("mina");
users.add(user);

user.rename("momo");

System.out.println(users.contains(user));
System.out.println(users.remove(user));
System.out.println(users.size());
System.out.println(users);
```

## 실행 전 워크시트

| 질문 | 내 답 |
|---|---|
| `users.contains(user)` |  |
| `users.remove(user)` |  |
| `users.size()` |  |
| `users` 출력 |  |

## 정답

- `users.contains(user)` -> `false`
- `users.remove(user)` -> `false`
- `users.size()` -> `1`
- `users` 출력 -> `[User{login=momo}]`처럼 보일 수 있다

## 왜 `contains()`와 `remove()`가 둘 다 실패하나

순서는 짧게 이렇게 보면 된다.

1. `add(user)` 할 때는 `"mina"` 기준 `hashCode()`로 bucket을 정했다
2. `user.rename("momo")` 뒤에도 원소는 옛 bucket에 그대로 남아 있다
3. 이제 `contains(user)`는 `"momo"` 기준 `hashCode()`로 현재 bucket을 찾는다
4. `remove(user)`도 거의 같은 lookup 경로를 따라간다
5. 그래서 둘 다 bucket을 잘못 찾아 `false`가 될 수 있다

핵심은 이것이다.

- 같은 객체 reference라는 사실만으로는 부족하다
- 현재 `hashCode()`가 삽입 당시 bucket과 맞아야 `contains()`와 `remove()`가 작동한다

## 초보자 혼동 포인트

- "`contains()`만 조회라서 실패하고 `remove()`는 지울 수 있지 않나?" -> 둘 다 같은 lookup 규칙을 쓴다
- "출력에 원소가 보이는데 왜 `remove()`가 안 되지?" -> 보이는 것과 현재 bucket으로 찾는 것은 다르다
- "같은 객체를 넘겼는데 왜 못 찾지?" -> `HashSet`은 reference보다 먼저 현재 `hashCode()` 경로를 본다

## 다음 읽기

- hash 컬렉션 함정을 map까지 넓히기: [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
- `TreeSet`까지 같이 비교하기: [Mutable Elements in HashSet and TreeSet Primer](./mutable-elements-hashset-treeset-primer.md)
- equality 감각 다시 잡기: [Java Equality and Identity Basics](./java-equality-identity-basics.md)

## 한 줄 정리

`HashSet`에 들어간 뒤 `equals()`/`hashCode()` 기준 필드를 바꾸면, `contains()`와 `remove()`는 둘 다 현재 bucket을 잘못 찾아 함께 실패할 수 있다.
