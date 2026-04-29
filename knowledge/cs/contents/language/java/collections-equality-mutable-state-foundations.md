# Collections, Equality, and Mutable-State Foundations

> 한 줄 요약: `List`/`Set`/`Map`을 고른 뒤 바로 따라오는 `equals()`/`hashCode()`와 mutable key 위험만 먼저 묶고, sorted collection/comparator 세부는 관련 문서로 미루게 돕는 primer다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)
- [`List.contains()` vs `Set.contains()` 증상 카드](./list-contains-vs-set-contains-symptom-card.md)
- [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)
- [Stable ID as Map Key Primer](./stable-id-map-key-primer.md)
- [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)
- [Mutable Hash Keys Bridge](./mutable-hash-keys-hashset-hashmap-bridge.md)
- [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)

retrieval-anchor-keywords: collections equality mutable state foundations, java collection hierarchy basics, java list set map hashmap basics, java list set map equals hashcode comparable, beginner collection equality contract, java set duplicate rule beginner, java map key mutation bug beginner, hashmap hashset equals hashcode why, comparable treeset treemap basics, map is not collection beginner, what is collection hierarchy java, 처음 배우는데 list set map 뭐예요, hashset 중복 제거 왜 안 됨, hashmap get null 왜 나옴

## 처음 2분 route

이 문서는 컬렉션 구현체 이름을 많이 외우게 하려는 문서가 아니다. 초보자 첫 읽기에서는 "`지금 내가 묻는 게 목록인가, 중복인가, key 조회인가`"만 먼저 자르면 된다.

| 지금 막힌 질문 | 먼저 떠올릴 타입 | 바로 같이 볼 규칙 |
|---|---|---|
| "순서대로 담고 다시 꺼내고 싶어요" | `List` | `contains(...)`는 결국 `equals()`를 본다 |
| "같은 값은 한 번만 담고 싶어요" | `Set` | `HashSet`이면 `hashCode()` + `equals()` |
| "id로 바로 찾고 싶어요" | `Map` | key 비교 기준과 key 불변 여부 |
| "`HashSet`은 하나인데 `HashMap#get(...)`은 null이에요" | 해시 컬렉션 공통 규칙 | 비교 기준 필드를 넣은 뒤 바꿨는지 |

즉 첫 route는 `컬렉션 선택 -> 무엇을 같은 값으로 볼지 -> 넣은 뒤 바꿔도 되는지` 세 칸이다.

## 컬렉션 문제처럼 보여도 먼저 다른 축을 의심할 때

초보자는 `List`/`Set`/`Map` 버그처럼 보이는 장면을 전부 컬렉션 문서 안에서 해결하려고 하기 쉽다. 하지만 첫 증상이 아래라면 출발 문서를 잘라서 보는 편이 더 빠르다.

| 지금 보이는 말 | 사실 먼저 의심할 축 | 왜 먼저 그쪽으로 가나 | 다음 문서 |
|---|---|---|---|
| "`new`는 한 번인데 왜 둘 다 같이 바뀌죠?" | 실행 모델 / 별칭 | 아직 컬렉션보다 같은 객체 공유가 먼저다 | [Java 실행 모델과 객체 메모리 mental model 입문](./java-execution-object-memory-mental-model-primer.md) |
| "`==`는 false인데 눈으로 보면 같아요" | equality | "같은 객체"와 "같은 값"을 먼저 자르지 않으면 `Set`/`Map`도 계속 흔들린다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "`HashSet`은 하나인데 `HashMap#get(...)`은 null이에요" | 컬렉션 + equality | 여기서부터 이 문서 축이 맞다 | 이 문서 계속 |

한 줄로 줄이면 "`같이 바뀐다`는 실행 모델, `같아 보이는데 비교가 다르다`는 equality, `중복/조회가 깨진다`는 collections" 순서다.

## 먼저 잡는 멘탈 모델

컬렉션 문제를 읽을 때는 "자료구조 이름"보다 아래 3가지를 먼저 본다.

1. 데이터를 어떤 모양으로 보관할까
2. 어떤 경우를 "같다"라고 볼까
3. 보관한 뒤 상태를 바꿔도 안전할까

이 3축이 같이 맞아야 컬렉션 코드가 덜 흔들린다.

- `List`: 순서가 핵심인 목록
- `Set`: 중복 판단 규칙이 핵심인 집합
- `Map`: key로 찾는 조회 규칙이 핵심인 사전

즉 컬렉션 선택은 자료를 담는 통만 고르는 일이 아니라,
"이 값의 동등성/변경 가능성"까지 같이 정하는 일이다. 정렬 계약은 여기서 길게 파지 않고 follow-up 문서로 넘긴다.

처음 배우는 단계에서는 아래 순서로 읽으면 덜 흔들린다.

1. 요구가 순서인지, 중복 제거인지, key 조회인지 먼저 고른다.
2. 그다음 "무엇을 같은 값으로 볼지"를 정한다.
3. 마지막으로 넣은 뒤 값을 바꿔도 되는지 확인한다.

## 처음엔 정렬 컬렉션을 잠깐 미뤄도 된다

beginner가 가장 자주 scope creep 되는 지점은 `HashSet`/`HashMap` 첫 버그를 보다가 곧바로 `TreeSet`, `TreeMap`, comparator tie-breaker까지 한 번에 붙드는 경우다.

- `HashSet` 중복/`HashMap#get(...)` 조회가 먼저 막혔다면 해시 규칙부터 본다.
- 정렬된 순서가 정말 요구사항 중심일 때만 sorted collection follow-up으로 간다.
- `compareTo()`/`Comparator`는 "다음 한 칸"이지, 이 primer의 중심이 아니다.

즉 처음엔 `List`/`Set`/`Map` 선택과 해시 컬렉션의 equality 규칙만 붙여도 충분하다.

## 왜 `HashSet`은 하나인데 `HashMap#get(...)`은 `null`일까

초보자에게 자주 보이는 증상은 "`같은 학생`인데 `Set`에서는 중복으로 막히고, `Map`에서는 방금 넣은 key를 못 찾는다"는 식으로 한 번에 섞여 나온다. 이때는 컬렉션을 따로따로 외우기보다 아래 한 줄로 먼저 자른다.

- `Set`은 "이미 같은 값이 있나?"를 묻는다.
- `Map`은 "같은 key로 다시 찾을 수 있나?"를 묻는다.
- 둘 다 해시 컬렉션이면 `equals()`/`hashCode()`와 mutable 상태를 같이 본다.

| 보이는 증상 | 먼저 볼 것 | 보통의 원인 |
|---|---|---|
| `HashSet` size가 기대보다 작다 | 중복 판단 규칙 | `equals()`/`hashCode()`가 같은 값으로 본다 |
| `HashMap#get(key)`가 `null`이다 | 조회 기준과 key 상태 | 넣은 뒤 key 필드가 바뀌었거나 같은 key 규칙이 어긋났다 |
| `contains(...)`는 되는데 `get(...)`가 흔들린다 | key로 쓰는 타입 설계 | 값 객체 경계보다 mutable key가 먼저 문제일 수 있다 |

한 번 더 줄이면 "`같은 값` 질문은 `Set`, `다시 찾기` 질문은 `Map`"이다. 요구 문장을 자료구조 말로 바꾸는 감각이 아직 약하면 [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)으로 한 칸 건너가도 된다.

## `Collection` 계층을 20초로 보면

초보자가 제일 많이 헷갈리는 지점은 `List`, `Set`, `Map`이 모두 같은 계층이라고 느끼는 순간이다.
실제로는 `List`와 `Set`은 `Collection` 쪽이고, `Map`은 key-value 사전이라 계층이 분리되어 있다.

```text
Iterable
└─ Collection
   ├─ List
   └─ Set

Map   // Collection 계층 밖
```

이 그림으로 먼저 잡으면 아래 오해를 줄일 수 있다.

- `Map`도 컬렉션처럼 보여서 `Collection` API가 바로 될 거라고 기대하기
- `List`/`Set`/`Map`이 모두 같은 방식으로 "같다"를 판단할 거라고 기대하기
- 정렬 컬렉션까지 한 번에 같은 규칙으로 이해하려고 하기

한 줄로 말하면 이렇다.

- `List`와 `Set`은 "원소 묶음" 질문
- `Map`은 "key로 value를 찾는 사전" 질문
- `TreeSet`/`TreeMap`은 여기에 "정렬 기준" 질문이 한 층 더 붙는다

## 여기서 먼저 멈출 것

이 문서에서 초보자가 먼저 가져갈 질문은 네 개면 충분하다.

1. 순서가 핵심인가
2. 중복 제거가 핵심인가
3. key 조회가 핵심인가
4. 넣은 뒤 비교 기준 필드를 바꿀 일은 없는가

`TreeSet`, `TreeMap`, comparator tie-breaker, 정렬 계약 충돌은 그다음 문서에서 따로 보는 편이 덜 헷갈린다. 이 문서의 중심은 "정렬 사고법"보다 `HashSet`/`HashMap`과 mutable key의 첫 사고 방지다.

## 한 장으로 보는 첫 판단표

| 질문 | 먼저 볼 것 | 보통의 첫 선택 |
|---|---|---|
| 순서/인덱스가 중요한가? | `List` | `ArrayList` |
| 중복을 자동으로 막아야 하나? | `Set` | `HashSet` |
| key로 바로 찾아야 하나? | `Map` | `HashMap` |
| 정렬된 순서가 핵심인가? | 우선 `List` 정렬인지 sorted collection인지 구분 | beginner 첫 읽기에서는 관련 문서로 넘김 |
| 해시 컬렉션에서 중복/조회가 이상한가? | `equals()`/`hashCode()` | 관련 필드 불변화 |
| 순회 중 삭제/추가가 필요한가? | 안전한 수정 통로 | `Iterator.remove()`, `removeIf(...)` |

표를 더 짧게 읽으면 아래처럼 정리할 수 있다.

| 지금 먼저 묻는 것 | 대표 타입 | 초보자 메모 |
|---|---|---|
| 순서를 유지한 목록인가 | `List` | 중복 허용이 기본 |
| 같은 값을 한 번만 담고 싶은가 | `Set` | `HashSet`이면 `equals()`/`hashCode()`가 핵심 |
| key로 바로 찾고 싶은가 | `Map` | `HashMap`이면 key의 `equals()`/`hashCode()`가 핵심 |
| 정렬된 순서가 규칙 자체인가 | sorted collection | `Comparable`/`Comparator` follow-up 주제 |

## 증상으로 먼저 읽기

처음부터 구현체 이름을 외우기보다 "지금 뭐가 이상한가"를 먼저 붙이면 선택 기준이 빨리 선다.

| 지금 보이는 증상 | 먼저 볼 축 | 가장 먼저 확인할 것 |
|---|---|---|
| `contains(...)`가 기대와 다르다 | equality | `equals()`가 같은 값을 제대로 정의했는지 |
| `HashSet` 중복 제거가 안 된다 | equality + hash | `hashCode()`를 같이 구현했는지 |
| `HashMap#get(...)`가 갑자기 `null`이다 | mutable state | key를 넣은 뒤 바꿨는지 |
| 이름순 정렬인데 결과가 예상과 다르다 | ordering follow-up | 여기서 오래 붙들지 말고 정렬 기준 문서로 넘겨도 되는 상황인지 |
| 순회 중 삭제하다 예외가 난다 | update path | `Iterator.remove()`나 `removeIf(...)`를 쓰는지 |

초보자용 첫 판단은 아래 네 줄이면 충분하다.

- `List`는 순서 질문
- `Set`은 중복 질문
- `Map`은 key 조회 질문
- 조회/중복이 이상하면 컬렉션 이름보다 비교 규칙과 mutable 상태를 먼저 본다

처음엔 컬렉션 이름을 외우기보다 아래 세 문장을 바로 말할 수 있으면 된다.

- `contains(...)`가 이상하면 "같은 값" 규칙부터 본다.
- `add(...)`가 이상하면 "중복 판단" 규칙부터 본다.
- `get(...)`가 이상하면 "같은 key로 다시 찾을 수 있는가"와 key 변경 여부부터 본다.

컬렉션 이름이 먼저 보여도 아래처럼 한 번 돌아가면 빠르게 풀리는 경우가 많다.

| 지금 튀어나온 말 | 먼저 돌아갈 질문 | 먼저 볼 문서 |
|---|---|---|
| "한쪽만 바꿨는데 다른 변수도 같이 바뀐다" | 같은 객체를 같이 보고 있나 | [Java 실행 모델과 객체 메모리 mental model 입문](./java-execution-object-memory-mental-model-primer.md) |
| "`==`와 `equals()`가 자꾸 섞인다" | 같은 객체 질문인가, 같은 값 질문인가 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "`for-each`는 되는데 `Map`은 왜 바로 안 돌지?" | 지금 자료구조 질문인가, 비교 규칙 질문인가 | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |

## 컬렉션 선택과 비교 규칙은 붙어 있다

초보자는 보통 `List`/`Set`/`Map`만 고르면 끝났다고 생각하기 쉽다.
하지만 실제 동작은 "무엇을 같은 값으로 보느냐"에 따라 바로 달라진다.

| 컬렉션 | 무엇이 핵심 규칙인가 | 초보자 실수 |
|---|---|---|
| `List` | 순서와 위치 | 중복 제거가 자동일 거라고 기대 |
| `HashSet` / `HashMap` | `equals()` + `hashCode()` | `equals()`만 바꾸고 `hashCode()`를 안 맞춤 |
| 정렬 컬렉션 | 정렬 기준이 "같은 자리"를 결정 | 해시 컬렉션과 같은 규칙일 거라고 생각 |

예를 들어 `Set`이라고 해도 전부 같은 방식으로 중복을 판단하지 않는다. beginner 첫 읽기에서는 아래 두 줄만 먼저 잡으면 충분하다.

- `HashSet`: `equals()`와 `hashCode()` 기준
- 정렬 컬렉션: 정렬 기준이 따로 있고, 세부 규칙은 follow-up 문서에서 본다

## 같은 값처럼 보여도 컬렉션 질문은 다르다

아래 표는 beginner가 `contains`, 중복 제거, key 조회를 한 번에 섞어 생각하는 실수를 줄이기 위한 최소 비교표다. 정렬 컬렉션의 tie-breaker 설계는 여기서 깊게 파지 않고 관련 문서로 넘긴다.

| 보고 싶은 것 | 보통 쓰는 타입 | "같다"를 누가 판단하나 | 자주 하는 오해 |
|---|---|---|---|
| 같은 값이 목록 안에 있나 | `List.contains(...)` | `equals()` | `List`는 순서만 보고 `contains`는 대충 찾는다고 생각 |
| 중복을 자동으로 막나 | `HashSet` | `hashCode()` 후 `equals()` | `equals()`만 맞추면 충분하다고 생각 |
| 같은 key로 다시 찾을 수 있나 | `HashMap`/`TreeMap` | 해시 규칙 또는 정렬 규칙 | 넣을 때와 찾을 때 key 상태가 달라도 될 거라고 생각 |

한 줄로 줄이면 이렇다. `List`는 "찾기", `Set`은 "중복 판단", `Map`은 "key 조회"가 중심 질문이고, 그 질문마다 동등성 규칙이 조금씩 다르게 걸린다.

## 같은 학생 예제로 한 번에 묶기

초보자는 `List`, `Set`, `Map`에서 모두 "같은 학생인가?"만 묻는다고 생각하기 쉽다. 실제로는 컬렉션마다 질문이 조금씩 다르다.

| 코드 상황 | 컬렉션이 묻는 질문 | 먼저 떠올릴 규칙 |
|---|---|---|
| `students.contains(member)` | 목록 안에 같은 값이 있나 | `equals()` |
| `studentSet.add(member)` | 이미 같은 원소가 있나 | `hashCode()` 후 `equals()` |
| `studentById.get(key)` | 같은 key로 다시 찾을 수 있나 | key의 `hashCode()` 후 `equals()` |
| `sortedStudents.add(member)` | 정렬 기준에서 같은 자리인가 | follow-up 정렬 규칙 |

그래서 "같은 학생인데 왜 여기선 들어가고 저기선 안 들어가지?"가 생긴다. 컬렉션 이름보다 먼저 "이 통이 무엇을 기준으로 같은지"를 묻는 습관이 중요하다.

아주 짧게 기억하면 이렇다.

- `List`는 "이 값이 있나"를 주로 묻는다.
- `Set`은 "이미 같은 값이 있나"를 주로 묻는다.
- `Map`은 "같은 key로 다시 찾을 수 있나"를 주로 묻는다.

`contains(...)`라는 이름은 같아도 `List`와 `Set`의 질문을 더 짧게 분리해서 잡고 싶다면 [`List.contains()` vs `Set.contains()` 증상 카드](./list-contains-vs-set-contains-symptom-card.md)로 먼저 들어가도 된다.

그래서 초보자 기준으로는 "컬렉션이 다르다"보다 "질문이 다르다"를 먼저 붙이는 편이 안전하다. 같은 `Student`를 넣어도 `contains`, `add`, `get`은 서로 다른 장면이라는 감각이 있어야 구현체 암기로 흐르지 않는다.

이 세 줄이 잘 안 붙으면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)로 잠깐 돌아가 `==`와 `equals()`를 다시 잡고 오는 편이 빠르다.

## 미션 코드에서 자주 나오는 4가지 선택

| 요구 문장 | 먼저 떠올릴 타입 | 같이 점검할 것 |
|---|---|---|
| 방문 순서대로 출력해야 한다 | `List` | 인덱스/순서만 중요하면 중복 허용 여부를 명시 |
| 이미 본 id는 다시 처리하면 안 된다 | `Set` | id 클래스의 `equals()`/`hashCode()` |
| id로 객체를 바로 찾는다 | `Map` | key 필드가 mutable인지 |
| 이름순으로 보여 준다 | 정렬된 `List`인지 sorted collection인지 먼저 분리 | 정렬 기준은 follow-up 문서로 넘김 |

중요한 포인트는 마지막 줄이 "이 문서의 중심"은 아니라는 점이다. "정렬해서 보여 준다"는 요구는 정렬 기준 문서로 넘기고, 여기서는 순서/중복/key 조회와 mutable key까지만 먼저 붙인다.

아예 한 문장으로 번역해 보면 더 쉽다.

| 요구 문장 | 초보자용 첫 해석 |
|---|---|
| "주문을 받은 순서대로 보여 줘" | 순서가 핵심이니 `List`부터 본다 |
| "같은 학번 학생은 한 번만 담아" | 중복 규칙이 핵심이니 `Set`과 `equals()`/`hashCode()`를 같이 본다 |
| "id로 회원을 바로 찾고 싶어" | key 조회가 핵심이니 `Map`과 key 불변 여부를 같이 본다 |

즉 초보자 첫 route는 "요구 문장을 타입으로 번역"하고, 바로 다음에 "무엇을 같은 값으로 볼지"를 붙이는 두 단계다.

## `equals()` / `hashCode()`를 언제 같이 보나

### 1. `HashSet`, `HashMap`을 쓸 때

해시 컬렉션은 대략 이렇게 동작한다.

1. `hashCode()`로 후보 위치를 찾는다
2. `equals()`로 정말 같은지 확인한다

그래서 초보자용 기본 규칙은 아래 한 줄이다.

- `equals()`를 오버라이드하면 `hashCode()`도 같은 필드로 같이 맞춘다

여기서 흔한 오해는 "`List.contains(...)`도 비교를 하니까 모든 컬렉션이 같은 규칙으로 움직이겠지"라고 생각하는 것이다. 실제로는 `List`는 값 찾기, `Set`은 중복 판단, `Map`은 key 조회라는 질문이 다르다.

### 2. 정렬 규칙은 여기서 이름만 걸어 둔다

`TreeSet`, `TreeMap`, `Comparable`, `Comparator`까지 한 번에 들어가면 초보자 첫 읽기에서는 중심이 흐려지기 쉽다.

- 이 문서에서는 해시 컬렉션의 동등성 규칙과 mutable state 위험만 먼저 잡는다
- 정렬 기준과 `compareTo()`/`Comparator`는 아래 관련 문서로 넘긴다

초보자 첫 판단을 더 줄이면 아래 세 줄이면 충분하다.

- `List`에서 막히면 우선 `equals()`를 본다
- `HashSet`/`HashMap`에서 막히면 `hashCode()`와 `equals()`를 같이 본다
- 정렬 컬렉션에서 막히면 "여긴 follow-up 주제"라고 보고 정렬 기준 문서로 넘긴다

여기서는 아래 한 줄만 기억하면 충분하다.

- 해시 컬렉션은 `equals()`/`hashCode()`를 보고, 정렬 컬렉션은 `compareTo()`/`Comparator`를 본다

정렬 컬렉션의 `compareTo() == 0`, tie-breaker, comparator 설계는 초보자 첫 읽기에서는 깊게 파지 말고 follow-up 문서로 넘긴다.

## 아주 작은 예제로 한 번에 보기

```java
import java.util.HashMap;
import java.util.Objects;
import java.util.Set;

final class MemberKey {
    private final long id;
    private String name;

    MemberKey(long id, String name) {
        this.id = id;
        this.name = name;
    }

    void rename(String name) {
        this.name = name;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof MemberKey other)) return false;
        return id == other.id && Objects.equals(name, other.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name);
    }

}

Set<MemberKey> members = new java.util.HashSet<>();
members.add(new MemberKey(1L, "mina"));
members.add(new MemberKey(1L, "mina"));
System.out.println(members.size()); // 1

HashMap<MemberKey, String> teamByMember = new HashMap<>();
MemberKey key = new MemberKey(2L, "momo");
teamByMember.put(key, "backend");
key.rename("luca");

System.out.println(teamByMember.containsKey(key)); // false가 될 수 있다
```

- `HashSet` 중복 제거는 `equals()`와 `hashCode()`를 함께 본다
- `HashMap` 조회는 key 필드를 바꾸면 깨질 수 있다

예제를 컬렉션 질문별로 다시 줄이면 이렇게 읽으면 된다.

| 코드 상황 | 컬렉션이 실제로 묻는 질문 | 기대 결과 |
|---|---|---|
| `members.add(new MemberKey(1L, "mina"))`를 두 번 호출 | "이미 같은 원소가 있나?" | `HashSet` size는 1 |
| `members.contains(new MemberKey(1L, "mina"))` | "같은 값으로 판단하나?" | `equals()`/`hashCode()`가 맞으면 `true` |
| `teamByMember.put(key, "backend")` 뒤 `key.rename("luca")` | "넣을 때와 찾을 때 같은 key인가?" | `containsKey(key)`가 깨질 수 있다 |

즉 `List`/`Set`/`Map`을 따로 외우기보다 "이 컬렉션이 지금 무슨 질문을 하고 있나"를 먼저 붙이면 초보자 실수가 많이 줄어든다.

## mutable key가 왜 특히 위험한가

멘탈 모델만 잡으면 어렵지 않다.

- `HashMap`은 key를 넣을 때 계산한 bucket을 기억한다
- key 필드가 바뀌어도 컬렉션이 자동으로 다시 자리 잡아 주지는 않는다

그래서 아래 패턴은 피하는 편이 안전하다.

| 상황 | 왜 위험한가 |
|---|---|
| `HashMap` key의 `equals()`/`hashCode()` 기준 필드를 변경 | 조회 bucket 계산이 달라진다 |
| `HashSet` 원소의 `equals()`/`hashCode()` 기준 필드를 변경 | 포함 여부 확인과 제거가 흔들린다 |

초보자 기본값은 단순하다.

- key와 set 원소는 가능하면 불변으로 둔다
- 바꿔야 한다면 컬렉션 밖에서 새 객체를 만들고 다시 넣는 쪽이 안전하다

## 순회하면서 수정할 때의 기본 선택

컬렉션을 순회할 때는 "지금 보고 있는 목록"과 "구조를 바꾸는 통로"를 분리해서 생각해야 한다.

| 하고 싶은 일 | 더 안전한 선택 | 피할 것 |
|---|---|---|
| `Map`을 돌며 조건에 맞는 항목 삭제 | `entrySet().removeIf(...)` | `for-each` 안에서 `map.remove(...)` |
| while 순회 중 한 칸씩 삭제 | `Iterator.remove()` | 외부 컬렉션에 직접 `remove(...)` |
| 값만 바꾸기 | `entry.setValue(...)` 또는 명시적 갱신 | 구조 변경과 같은 감각으로 섞어 이해 |

특히 초보자가 자주 헷갈리는 지점은 이거다.

- `ConcurrentModificationException`은 멀티스레드에서만 나는 예외가 아니다
- 같은 스레드에서도 순회 중 구조를 바꾸면 터질 수 있다

## 자주 하는 오해 6가지

- `Set`이면 전부 같은 방식으로 중복을 판단한다고 생각한다
- `List.contains(...)`, `Set.contains(...)`, `Map.containsKey(...)`가 전부 같은 비교 규칙으로 돈다고 생각한다
- `equals()`만 구현하면 `HashSet`/`HashMap`이 잘 동작할 거라고 생각한다
- 정렬 컬렉션도 해시 컬렉션과 같은 규칙으로 중복을 막는다고 생각한다
- map 안에 들어간 key 객체를 바꿔도 같은 reference니까 조회될 거라고 생각한다
- `HashMap` 출력에 key가 보이면 `get()`도 반드시 될 거라고 생각한다
- `for-each` 안의 `remove(...)`를 단순한 문법 차이 정도로 본다

## 30초 점검표

- 순서가 핵심이면 `List`
- 중복 제거가 핵심이면 `Set`
- key 조회가 핵심이면 `Map`
- 해시 컬렉션이면 `equals()`와 `hashCode()`를 같이 본다
- sorted collection이면 "여긴 정렬 규칙 follow-up"이라고 먼저 분리한다
- key/원소의 비교 기준 필드는 넣은 뒤 바꾸지 않는다
- 순회 중 삭제는 `Iterator.remove()`나 `removeIf(...)`로 한다

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`List`/`Set`/`Map` 자체가 아직 헷갈린다" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "요구 문장을 타입으로 번역하는 연습이 더 필요하다" | [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md) |
| "`==`/`equals()`/`hashCode()` 감각이 약하다" | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| "mutable key 조회 실패를 더 자세히 보고 싶다" | [Mutable Keys in HashMap and TreeMap](./hashmap-treemap-mutable-key-lookup-primer.md) |
| "순회 중 수정 패턴만 따로 익히고 싶다" | [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md) |
| "정렬 기준과 `Comparable`/`Comparator`를 따로 배우고 싶다" | [Comparable and Comparator Basics](./java-comparable-comparator-basics.md) |
| "`HashSet`와 `TreeSet`의 중복 판단 차이만 따로 보고 싶다" | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |

## 한 줄 정리

Java 컬렉션 첫 읽기에서는 `List`/`Set`/`Map` 선택, `equals()`/`hashCode()` 기준, mutable key 금지, 순회 중 안전한 수정 통로를 먼저 한 세트로 묶고, 정렬 계약은 다음 문서로 넘기는 편이 덜 헷갈린다.
