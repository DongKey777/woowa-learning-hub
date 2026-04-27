# Comparator 변수명 짓기 초급 패턴

> 한 줄 요약: `Comparator<Student> byName`처럼 "무엇을 어떤 방향으로 비교하는지"를 변수명에 넣으면 정렬 의도와 재사용 지점이 한 줄에서 바로 읽힌다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- [`List.sort` vs `Stream.sorted` Comparator Bridge](./list-sort-vs-stream-sorted-comparator-bridge.md)
- [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- [Spring Bean Naming, Qualifier, and Rename Pitfalls Primer](../../spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md)

retrieval-anchor-keywords: comparator variable naming, java comparator name pattern, byname comparator, byscoredescthenname comparator, comparator readability beginner, named comparator reuse java, sort intent variable name, comparator desc then asc naming, comparator helper naming java, comparator extract variable beginner, 정렬 의도 변수명, comparator 이름 규칙 기초, comparator variable naming beginner primer basics, comparator variable naming beginner primer beginner, comparator variable naming beginner primer intro

## 핵심 개념

초급 단계에서는 comparator를 "익명 람다 한 줄"보다 "이름 있는 정렬 규칙"으로 읽는 편이 덜 헷갈린다.

핵심은 변수명에 정렬 의도를 그대로 적는 것이다.

- `byName`: 이름 기준 정렬
- `byScoreDesc`: 점수 내림차순 정렬
- `byScoreDescThenName`: 점수 내림차순, 같으면 이름순

즉 변수명은 "이 comparator가 무엇을 기준으로 줄 세우는가"를 설명하는 짧은 문장이다.

## 한눈에 보기

| 변수명 | 읽는 법 | 추천 상황 |
|---|---|---|
| `byName` | 이름순으로 정렬 | 기준이 하나일 때 |
| `byScoreDesc` | 점수 높은 순 정렬 | 방향까지 드러내야 할 때 |
| `byScoreDescThenName` | 점수 높은 순, 같으면 이름순 | tie-breaker가 있을 때 |
| `byCreatedAtAscThenId` | 생성시간 오름차순, 같으면 id순 | 안정적인 2차 기준이 필요할 때 |

짧은 기억법:

`by + 첫 기준 + 방향 + Then + 다음 기준`

## 바로 따라 쓰는 패턴

가장 안전한 출발점은 세 가지다.

```java
Comparator<Student> byName =
        Comparator.comparing(Student::name);

Comparator<Student> byScoreDesc =
        Comparator.comparingInt(Student::score).reversed();

Comparator<Student> byScoreDescThenName =
        Comparator.comparingInt(Student::score)
                .reversed()
                .thenComparing(Student::name);
```

여기서 중요한 점은 코드 길이가 아니라 이름이다.

- `students.sort(byScoreDescThenName)`는 의도가 바로 읽힌다
- `stream.sorted(byScoreDescThenName)`에도 같은 규칙을 재사용할 수 있다
- 테스트 이름이나 fixture 설명에도 같은 표현을 그대로 가져갈 수 있다

## 흔한 오해와 함정

- `studentComparator`, `sortComparator`처럼 너무 넓은 이름은 무엇을 비교하는지 안 보인다.
- `comparator1`, `tempComparator`는 일회용 메모에는 쓸 수 있어도 학습용 코드와 리뷰 코드에서는 의도를 숨긴다.
- `byScoreThenName`라고 써 놓고 실제 코드는 `reversed()`가 들어 있으면 이름과 동작이 어긋난다.
- `byNameThenId`처럼 tie-breaker를 이름에 썼다면, 코드도 정말 `thenComparing...`까지 붙었는지 같이 확인해야 한다.

이름을 고칠 때는 "이 변수명만 읽고도 정렬 결과를 대충 말할 수 있는가?"를 먼저 보면 된다.

## 실무에서 쓰는 모습

한 번만 정렬해도 이름 있는 comparator가 읽기 쉽지만, 재사용 지점이 둘 이상이면 효과가 더 커진다.

```java
students.sort(byScoreDescThenName);

List<Student> top10 = students.stream()
        .sorted(byScoreDescThenName)
        .limit(10)
        .toList();
```

여기서 두 호출은 "같은 정렬 정책"을 공유한다.
익명 comparator를 두 번 복붙하면 한쪽만 수정돼 정책이 갈리기 쉽다.
반대로 `byScoreDescThenName`처럼 이름을 붙여 두면 "정렬 규칙"이 값처럼 재사용된다.

## 더 깊이 가려면

- comparator 조립 자체가 아직 낯설면 [Comparator Utility Patterns](./java-comparator-utility-patterns.md)
- `reversed()`가 이름과 다른 방향을 만들기 쉬운 지점을 먼저 잡고 싶다면 [Comparator Reversed Scope Primer](./comparator-reversed-scope-primer.md)
- sorted collection에서 comparator 이름이 곧 "같은 키로 볼 기준"까지 바꾼다는 점은 [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- bean 이름도 의도 드러내기가 중요한 이유를 다른 카테고리 예제로 보려면 [Spring Bean Naming, Qualifier, and Rename Pitfalls Primer](../../spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md)

## 한 줄 정리

comparator 변수명은 `byName`, `byScoreDescThenName`처럼 "기준 + 방향 + tie-breaker"를 드러내게 짓는 편이 초급 코드에서 정렬 의도와 재사용성을 가장 빨리 읽히게 만든다.
