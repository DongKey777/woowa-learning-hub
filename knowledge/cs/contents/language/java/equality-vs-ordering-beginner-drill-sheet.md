# Beginner Drill Sheet: Equality vs Ordering

> 한 줄 요약: `equals()`와 `compareTo()`를 "같은지 판단"과 "순서 판단"으로 분리해, `HashSet`/`TreeSet`/`TreeMap` 결과를 실행 전에 먼저 예측해 보는 초급 연습 시트다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Comparable and Comparator Basics](./java-comparable-comparator-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)

> retrieval-anchor-keywords: beginner drill equality vs ordering, java equals compareTo practice sheet, java hashset treeset prediction worksheet, equals vs compareTo beginner, java set map duplicate prediction, compareTo 0 duplicate rule, hashset equals hashCode rule, treeset compareTo rule, treemap compareTo key replacement, java collections before run prediction, 자바 equals compareTo 연습문제, 자바 hashset treeset 결과 예측, 자바 tree map put 덮어쓰기 예측, 초급 자바 컬렉션 중복 판단 연습, compareTo 0이면 같은 자리

<details>
<summary>Table of Contents</summary>

- [먼저 잡을 mental model](#먼저-잡을-mental-model)
- [한 장 비교표](#한-장-비교표)
- [드릴 1: `HashSet` vs `TreeSet` 결과 예측](#드릴-1-hashset-vs-treeset-결과-예측)
- [드릴 2: `TreeMap` `put` 결과 예측](#드릴-2-treemap-put-결과-예측)
- [드릴 3: tie-breaker 추가 후 결과 예측](#드릴-3-tie-breaker-추가-후-결과-예측)
- [실행 전 60초 워크시트](#실행-전-60초-워크시트)
- [초보자가 자주 헷갈리는 포인트](#초보자가-자주-헷갈리는-포인트)
- [다음 읽기](#다음-읽기)

</details>

## 먼저 잡을 mental model

처음엔 이 두 줄만 기억하면 된다.

- `equals()`는 "같은 객체인가?"를 판단한다
- `compareTo()`/`Comparator`는 "정렬할 때 같은 자리인가?"를 판단한다

그리고 컬렉션은 아래 기준을 쓴다.

- `HashSet`: 최종 중복 판단은 `equals()`/`hashCode()`
- `TreeSet`, `TreeMap`: 최종 중복(같은 key 자리) 판단은 `compare(...) == 0`

## 한 장 비교표

| 질문 | 주로 보는 메서드 | `HashSet` | `TreeSet`/`TreeMap` |
|---|---|---|---|
| "같은 값인가?" | `equals()` | 중요 | 직접 기준은 아님 |
| "같은 정렬 자리인가?" | `compareTo()`/`Comparator` | 직접 기준은 아님 | 중요 (`0`이면 같은 자리) |
| 결과 surprise | `equals()==false`인데 `compare==0` | 둘 다 저장될 수 있음 | 하나로 합쳐지거나 값이 덮어써짐 |

## 드릴 1: `HashSet` vs `TreeSet` 결과 예측

아래 코드를 실행하기 전에 먼저 답을 적어 보자.

```java
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Student a = new Student(1L, "Mina");
Student b = new Student(2L, "Mina");

Set<Student> hash = new HashSet<>();
hash.add(a);
hash.add(b);

Set<Student> tree = new TreeSet<>(Comparator.comparing(Student::name));
tree.add(a);
tree.add(b);

System.out.println(hash.size());
System.out.println(tree.size());
```

질문:

1. `hash.size()`는?
2. `tree.size()`는?

<details>
<summary>정답 보기</summary>

1. `hash.size() == 2`
`equals()` 기준으로 `a`와 `b`는 다르다(`id`가 다름).

2. `tree.size() == 1`
정렬 기준이 `name` 하나라서 `compare(...) == 0`이 된다.

</details>

## 드릴 2: `TreeMap` `put` 결과 예측

이번에는 `TreeMap`에서 key 자리를 예측해 보자.

```java
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;

record Student(long id, String name) {}

Map<Student, String> seat = new TreeMap<>(Comparator.comparing(Student::name));

String p1 = seat.put(new Student(1L, "Mina"), "front");
String p2 = seat.put(new Student(2L, "Mina"), "back");

System.out.println(p1);
System.out.println(p2);
System.out.println(seat.size());
System.out.println(seat.get(new Student(99L, "Mina")));
```

질문:

1. `p1`, `p2` 출력은?
2. `seat.size()`는?
3. 마지막 `get(...)` 결과는?

<details>
<summary>정답 보기</summary>

1. `p1 == null`, `p2 == "front"`
2. `seat.size() == 1`
3. `"back"`

이유: key 비교에서 `name`만 보므로 세 key가 모두 같은 자리(`compare == 0`)로 처리된다.

</details>

## 드릴 3: tie-breaker 추가 후 결과 예측

이제 정렬 기준을 `name` + `id`로 바꿔 보자.

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Comparator<Student> byNameThenId =
        Comparator.comparing(Student::name)
                .thenComparingLong(Student::id);

Set<Student> tree = new TreeSet<>(byNameThenId);
tree.add(new Student(1L, "Mina"));
tree.add(new Student(2L, "Mina"));

System.out.println(tree.size());
```

질문:

1. `tree.size()`는?

<details>
<summary>정답 보기</summary>

`tree.size() == 2`

`name`이 같아도 `id`에서 순서가 갈리므로 `compare(...) == 0`이 되지 않는다.

</details>

## 실행 전 60초 워크시트

아래 표를 복사해서, 코드 실행 전에 먼저 채워 보자.

| 체크 질문 | 내 답(실행 전) |
|---|---|
| 이번 컬렉션이 중복 판단에 쓰는 기준은? (`equals/hashCode` vs `compare == 0`) |  |
| `compare == 0`이 되는 조건을 한 줄로 쓰면? |  |
| `HashSet` 예상 `size()` |  |
| `TreeSet` 예상 `size()` |  |
| `TreeMap` 두 번째 `put` 반환값 예상 |  |
| `TreeMap` 최종 `size()` 예상 |  |

짧은 점검 순서:

1. "같은지"(`equals`)와 "같은 자리"(`compare == 0`)를 분리해서 적는다
2. sorted 컬렉션이면 tie-breaker 유무를 확인한다
3. `size()`와 `put` 반환값을 먼저 적고 실행해서 비교한다

## 초보자 혼동 포인트

- "`compareTo()==0`이면 `equals()==true`여야 한다"라고 항상 생각하기
- `hashCode()`가 같으면 무조건 중복이라고 생각하기
- `TreeMap.put`에서 key 객체 자체가 바뀌었다고 오해하기
- record라서 `equals()`가 자동 생성되면 `TreeSet`에서도 같은 기준으로 중복이 판단된다고 오해하기

안전한 습관:

- sorted 컬렉션에서는 "내 비교 규칙에서 `0`이 되는 조건"을 먼저 적는다
- 같은 이름 다른 사람을 모두 유지해야 하면 tie-breaker를 넣는다
- 코드 실행 전 `size()`/`put` 반환값을 먼저 예측하고 확인한다

## 다음 읽기

- 기초 정리: [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- 컬렉션별 중복 규칙: [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- natural ordering 확장: [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)
- comparator 설계 확장: [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
