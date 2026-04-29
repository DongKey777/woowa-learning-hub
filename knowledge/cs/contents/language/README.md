# Language

**난이도: 🔴 Advanced**

> 이 README는 language category `navigator`다. 언어별 `primer`와 Java 중심 `deep dive catalog`를 묶고, 학습 순서용 `survey`는 루트 roadmap으로 보낸다.

> 길을 잃으면 [빠른 탐색](#빠른-탐색)으로 돌아오고, Java 밖 다음 카테고리 순서가 필요하면 [루트 README](../../README.md)에서 다시 안전 사다리를 고른다.

> retrieval-anchor-keywords: language readme, language navigator, java readme, java primer route, java category navigator, java 처음 뭐부터, java 처음 어디부터, new 했는데 뭐가 생기지, student student 객체가 생긴 거 아닌가요, class object instance 헷갈려요, equals hashcode 헷갈려요, java == vs equals, 자바 == equals 차이, same object vs same value, identity vs equality java, 같은 객체와 같은 값 차이, hashset 왜 하나로 보여요, hashmap get null 왜, optional enum null 언제 갈라요, int integer 언제 나눠요, primitive wrapper 헷갈려요, save 보이는데 sql 안 보여요, controller service repository 어디서부터, language database bridge, java spring database handoff, ordered map null safe, floor ceiling null 왜, treemap null practice, hashmap vs treemap 처음 선택, map ordered follow-up

> beginner 빠른 진입:
> - 첫 10분은 primer 5개 축만 본다: `실행 모델 -> 객체 모델 -> equality -> collections basics -> optional/enum/null`
> - 지금 막힌 증상 하나만 고르고, 문서는 한 번에 한 장씩만 읽는다
> - 첫 분기만 기억하면 된다: "`new`/객체 생성" 질문이면 실행 모델, "`==`/`equals()`/`같은 값`" 질문이면 equality, "`HashSet`/`HashMap#get(...)`/`List`/`Set`/`Map` 선택" 질문이면 collections
> - "`new` 했는데 뭐가 생기지?"면 [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md)
> - "`Student student;`만 썼는데 객체가 생긴 거 아닌가요?", "`new`는 언제 진짜 객체를 만들죠?`"면 [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) -> [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md)
> - "`class`/객체/인스턴스/OOP가 한꺼번에 섞인다"면 [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md)
> - "`new`는 한 번인데 왜 둘 다 같이 바뀌죠?", "`같은 객체를 보는 건지`부터 헷갈려요"면 [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) -> [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)
> - "`==`/`equals()`/`hashCode()`가 섞인다"면 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)
> - "`==`는 언제 쓰고 `equals()`는 언제 써요?`, `같은 객체`와 `같은 값`이 뭐가 달라요?`처럼 첫 비교 질문이 나오면 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md)로 바로 들어간다
> - "`==`는 false인데 `equals()`는 true예요`, `HashSet`은 왜 하나로 보죠?`"면 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) -> [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md)
> - "`List`/`Set`/`Map` 자체가 아직 안 잡혔다"면 [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md)
> - "`HashMap`/`TreeMap` 중 무엇을 먼저 골라야 하는지`, `정렬된 map이 왜 필요한지`가 헷갈리면 [HashMap vs TreeMap 초급 선택 브리지](./java/hashmap-vs-treemap-beginner-selection-bridge.md)
> - "`TreeMap`의 `floor`/`ceiling`이 왜 어떤 때는 `null`이고 어떤 때는 값인지`부터 막히면 [Ordered Map Null-Safe Practice Drill](./java/ordered-map-null-safe-practice-drill.md)
> - "`한 명 없음`/`여러 개 0개`/`Map#get(...) == null`/`없음의 이유`가 한꺼번에 섞인다"면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md)부터 보고 `Optional -> 빈 컬렉션 -> Map 조회 null -> enum 상태` 4갈래로 먼저 자른다
> - "`컬렉션은 알겠는데 백엔드 문제 문장을 자료구조로 못 옮기겠다`"면 [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md)
> - "`queue`가 service 코드에 왜 나와요?`, `BFS랑 같은 queue예요?`면 [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md)
> - "`Optional`이랑 `null`, 빈 리스트, enum 상태가 언제 갈리는지 모르겠다"면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) -> [Java Optional 입문](./java/java-optional-basics.md)
> - "`int`/`Integer`, `boolean`/`Boolean`을 언제 나눠야 하는지 모르겠다"면 [Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`](./java/primitive-wrapper-choice-primer.md)
> - "`Optional`보다 enum 상태가 더 맞는 순간이 언제인지 모르겠다"면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) -> [Java enum 기초](./java/java-enum-basics.md)
> - "`enum`이랑 `"PAID"` 같은 문자열 payload를 왜 바로 비교하면 안 되는지 헷갈린다"면 [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md)
> - "`enum` 정렬인데 `null`은 어디로 가죠?`, `문자열 순서랑 왜 다르죠?`면 [`null` 가능한 enum, 어떻게 정렬할까 beginner bridge](./java/nullable-enum-comparator-bridge.md)
> - "`HashSet` 중복, `HashMap` 조회, mutable key까지 같이 흔들린다"면 [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md)
> - "`객체는 분명 있는데 set/map에서 왜 못 찾죠?`, `HashSet`은 하나인데 `HashMap#get(...)`은 왜 null이죠?`"면 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) -> [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) -> [Stable ID as Map Key Primer](./java/stable-id-map-key-primer.md)
> - "`HashMap#get(...)`이 왜 `null`인지부터 헷갈린다"면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md)
> - 구현체 암기보다 `무엇이 만들어지는가 / 같은 값 기준은 무엇인가 / key로 다시 찾는가 / 넣은 뒤 바꾸는가` 네 질문을 먼저 붙인다
> - `처음`, `왜`, `언제`, `뭐예요`, `헷갈려요`가 붙는 beginner 질문이면 deep dive보다 primer 한 장으로 먼저 자른다
> - `save()`, `@Transactional`, `controller/service/repository`가 같이 보이면 language 안에서 다 해결하려 하지 말고 [Spring README: 빠른 탐색](../spring/README.md#빠른-탐색) 또는 [Database README의 빠른 탐색](../database/README.md#빠른-탐색)으로 한 칸만 건넌 뒤, 막히면 다시 이 README의 [빠른 탐색](#빠른-탐색)으로 돌아온다
> - `record`, sorted collection, comparator, BigDecimal key 같은 follow-up은 위 primer를 지난 뒤 붙인다
> - "`record`가 왜 `equals()`를 자동으로 만들죠?`, `record`를 value object로 써도 되나요?`"면 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) 다음에 [Record and Value Object Equality](./java/record-value-object-equality-basics.md)
> - JFR, safepoint, Loom, JDBC cancel 같은 운영/진단 주제도 위 5장을 지난 뒤 아래 deep dive cluster로 넘긴다

위 primer들은 모두 문서 상단의 `language 카테고리 인덱스` 링크로 다시 이 README에 복귀할 수 있다. 한 장 읽고도 질문이 `save()`, `Repository`, `@Transactional` 쪽으로 넓어지면 [Database README의 빠른 탐색](../database/README.md#빠른-탐색)이나 [Spring README: 빠른 탐색](../spring/README.md#빠른-탐색)으로 한 칸만 건넌 뒤, Java 문법 질문으로 다시 줄어들면 이 README의 [빠른 탐색](#빠른-탐색)으로 되돌아온다.

처음엔 "문서를 다 읽어야 이해된다"보다 "지금 코드가 무슨 질문을 하고 있나"를 먼저 자르는 편이 낫다.

## Java beginner 첫 루트

처음 들어온 학습자가 가장 자주 묻는 건 구현체 이름보다 "지금 이 버그가 어느 층 질문이냐"다. 아래 4줄만 기억하면 language README가 glossary가 아니라 입구 역할을 한다.

| 지금 코드에서 먼저 자를 한 가지 | 스스로 먼저 붙일 질문 | 첫 primer |
|---|---|---|
| `new`, 변수 선언, 같이 바뀜 | 객체가 생긴 줄인지, 같은 객체를 같이 보는 줄인지 | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) |
| `==`, `equals()`, `String`, 같은 값 | 같은 객체 질문인지, 같은 값 질문인지 | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) |
| `HashSet`, `HashMap#get(...)`, `contains(...)` | 같은 원소 질문인지, 같은 key 조회 질문인지 | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) |
| `Optional`, 빈 리스트, enum 상태 | 단건의 없음인지, 여러 건의 0개인지, 이유까지 필요한지 | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) |

| 지금 보이는 증상 | 먼저 가는 primer | 다음 한 걸음 |
|---|---|---|
| "`new` 했는데 뭐가 생기죠?", "`Student student;`만 썼는데 객체가 생긴 건가요?" | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) |
| "`new`는 한 번인데 왜 둘 다 같이 바뀌죠?" | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) |
| "`==`는 언제 쓰고 `equals()`는 언제 써요?", "`String` 같은데 왜 false예요?" | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | 문자열이면 [Java String 기초](./java/java-string-basics.md), 해시 컬렉션이면 [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) |
| "`HashSet`은 하나인데 `HashMap#get(...)`은 왜 null이죠?", "`List`/`Set`/`Map` 중 뭘 골라요?" | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 큰 그림이면 [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) |

이 표의 목적은 "한 번에 한 장만 읽고, 바로 다음 한 칸만 붙인다"는 안전한 진입 순서를 눈에 보이게 만드는 것이다.

| 지금 보이는 증상 | 먼저 갈 primer | 읽고 나서 붙일 다음 한 칸 | 막히면 돌아올 자리 |
|---|---|---|---|
| "`new`를 안 했는데 왜 같이 바뀌지?" | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| "`Student student`만 써도 객체가 생긴 거 아닌가?" | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| "`==`와 `equals()`가 계속 섞인다" | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`==`는 false인데 `equals()`는 true예요`, `HashSet`은 왜 하나죠?`" | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`HashSet` 중복이 왜 안 맞죠?`, `HashMap#get(...)`이 왜 null이죠?`" | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | [Stable ID as Map Key Primer](./java/stable-id-map-key-primer.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`List`/`Set`/`Map`이 아직 구조부터 안 잡힌다" | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`queue`가 service handoff인지 BFS 도구인지 모르겠다" | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | [Service 계층 기초](../software-engineering/service-layer-basics.md) 또는 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`Optional`이 왜 필요한지, 빈 리스트랑 뭐가 다른지 모르겠다" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) | [Java Optional 입문](./java/java-optional-basics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`int`/`Integer`, `boolean`/`Boolean`을 언제 나누죠?`" | [Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`](./java/primitive-wrapper-choice-primer.md) | [Primitive vs Wrapper Fields in JSON Payload Semantics](./java/primitive-vs-wrapper-fields-json-payload-semantics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`없음`을 `Optional`로 볼지 enum 상태로 볼지 모르겠다" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) | [Java enum 기초](./java/java-enum-basics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`enum`이랑 문자열 `"PAID"`를 왜 바로 비교하면 안 되지?" | [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md) | [Enum equality quick bridge](./java/enum-equality-quick-bridge.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`enum` 정렬인데 `null`은 어디로 가죠?`, `왜 문자열 순서처럼 안 보이죠?`" | [`null` 가능한 enum, 어떻게 정렬할까 beginner bridge](./java/nullable-enum-comparator-bridge.md) | [Comparator Null Reversal Primer](./java/comparator-null-reversal-primer.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`HashMap#get(...)`이 왜 `null`이지?" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md) | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`List`/`Set`/`Map` basics는 알겠는데 구현체 한 칸만 더 고르고 싶어요" | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | [Java Deep Dive Catalog의 컬렉션 빠른 탐색](./java/README.md#컬렉션-빠른-탐색) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |

초보자 첫 진입은 한 문서로 막힌 증상 하나만 자르고, 다음 문서도 한 칸만 옮기는 편이 안전하다. 한 장 읽고도 "`다음 뭐 읽어요?`"가 남으면 primer 상단의 `language 카테고리 인덱스` 링크로 다시 돌아와 방금 읽은 행의 `다음 한 칸`만 붙이면 된다.

각 primer 상단의 `language 카테고리 인덱스` 링크는 다시 이 README로 돌아오는 safe return path다. 한 장 읽고도 여전히 막히면 `실행 모델`, `객체 모델`, `equality`, `collections`, `optional/enum/null` 중 어느 축이었는지만 다시 고르고 다음 한 칸만 붙인다. Java 문법 밖 질문으로 번지면 [루트 README](../../README.md)의 `Java / OOP basics` 줄이나 `MVC`, `DB handoff / transactions` 줄로 올라가 한 카테고리만 더 건넌다.

beginner exit sign도 같이 기억하면 길을 덜 잃는다.

- `controller`, `service`, bean, `@Transactional`이 같이 보이면 language 문법만의 질문이 아닐 수 있으니 [Spring README: 빠른 탐색](../spring/README.md#빠른-탐색)으로 한 칸 건넌다.
- `save()`, `Repository`, SQL 위치가 같이 궁금해지면 [Database First-Step Bridge](../database/database-first-step-bridge.md)로 건너가고, 다시 Java 문법 축으로 돌아올 때는 이 README의 [빠른 탐색](#빠른-탐색)으로 복귀한다.
- `왜 저장은 되는데 rollback 범위나 SQL 위치가 헷갈리지?`, `처음인데 controller 다음이 안 보여요`처럼 handoff 질문이 되면 [Database README의 빠른 탐색](../database/README.md#빠른-탐색)에서 `트랜잭션 기초`와 `JDBC · JPA · MyBatis 기초` 중 한 칸만 다시 고른다.
- database 쪽 primer를 한 장 읽고도 질문이 다시 `new`, `객체`, `equals()`, `HashMap#get(...)`, `Optional` 축으로 줄어들면 deep dive로 더 내려가지 말고 이 README의 [빠른 탐색](#빠른-탐색)이나 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return)로 바로 되돌아온다.

문법 primer를 읽은 뒤 `controller`, `service`, `repository`, `save()`, `@Transactional`이 한 화면에 같이 보여 language만으로는 답이 안 잡히면 아래 cross-category 브리지로 한 칸만 건넌다.

| 지금 남은 beginner 질문 | language 다음 첫 다리 | 바로 다음 1걸음 | 막히면 돌아올 자리 |
|---|---|---|---|
| "`new`, 객체, 메서드는 알겠는데 controller/service/repository가 같이 보여요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Database First-Step Bridge](../database/database-first-step-bridge.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| "`List`/`Map`은 아는데 백엔드 문제 문장을 자료구조로 못 옮기겠어요" | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`queue`가 service handoff인지 BFS 도구인지 모르겠어요" | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | `worker 순서`면 [Service 계층 기초](../software-engineering/service-layer-basics.md), `최소 이동 횟수`면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`Optional`/enum으로 상태는 나눴는데 저장 단위와 rollback 범위가 헷갈려요" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | [트랜잭션 기초](../database/transaction-basics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`왜 저장은 되는데 rollback 범위나 SQL 위치가 아직 헷갈리죠?`" | [Database README의 빠른 탐색](../database/README.md#빠른-탐색) | [트랜잭션 기초](../database/transaction-basics.md) 또는 [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| "`save()`는 보이는데 `HashMap#get(...)`도 같이 흔들려서 어디부터 복구할지 모르겠어요" | [Database README의 빠른 탐색](../database/README.md#빠른-탐색) | [JDBC · JPA · MyBatis 기초](../database/jdbc-jpa-mybatis-basics.md)로 SQL 위치를 먼저 자른 뒤 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md)로 되돌아온다 | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| "`new`/`equals()`는 알겠는데 `controller -> service -> save()`부터는 어디로 가요?" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | [Database First-Step Bridge](../database/database-first-step-bridge.md) | 이 README의 [빠른 탐색](#빠른-탐색) |

language에서 database로 건넌 뒤 길을 잃으면 [Database README의 빠른 탐색](../database/README.md#빠른-탐색)으로 돌아가 `Database First-Step Bridge -> 트랜잭션 기초 -> JDBC · JPA · MyBatis 기초` 3칸 중 하나만 다시 고르면 된다. 반대로 database 문서를 읽다가도 질문이 아직 `new`, `객체`, `equals()`, `HashMap#get()` 축이면 [이 README의 빠른 탐색](#빠른-탐색)으로 되돌아와 Java primer 한 장만 먼저 복구한다.

왕복 복귀 루프는 이 한 줄만 기억하면 된다.

`이 README의 빠른 탐색 -> Database README 빠른 탐색 -> DB primer 1장 -> 이 README의 빠른 탐색 또는 equality / collections / optional 복귀 표`

반대로 Java primer를 한 장 읽고 "`Map 구현체만 한 번 더 고르고 싶어요`", "`DTO에서 값 객체로 올릴지부터 헷갈려요`"처럼 language 안의 다음 한 칸만 남았다면 큰 catalog보다 [Java Deep Dive Catalog의 컬렉션 빠른 탐색](./java/README.md#컬렉션-빠른-탐색)이나 [DTO / 값 객체 경계 빠른 탐색](./java/README.md#dto--값-객체-경계-빠른-탐색)으로 짧게 건너간다. 그 뒤 질문이 다시 넓어지면 이 README의 [빠른 탐색](#빠른-탐색)으로 돌아와 축부터 다시 고른다.

DB handoff 뒤 복귀 경로도 짧게 고정하면 안전하다.

`Database README 빠른 탐색 -> Database First-Step Bridge -> JDBC · JPA · MyBatis 기초 -> 이 README의 빠른 탐색 또는 equality / collections / optional 복귀 표`

Java primer를 읽고 다른 카테고리로 건널 때도, deep dive가 아니라 beginner 다음 1걸음만 고르면 길을 덜 잃는다.

| 방금 읽은 primer | 아직 남은 beginner 질문 | 바로 다음 1걸음 | 막히면 돌아올 자리 |
|---|---|---|---|
| [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | "`controller`/`service`/`repository`가 왜 나뉘는지 모르겠어요" | [Spring 요청 파이프라인과 Bean Container 기초](../spring/spring-request-pipeline-bean-container-foundations-primer.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | "`HashSet`/`HashMap`에서 왜 중복과 조회가 같이 흔들리죠?" | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| [Java Optional 입문](./java/java-optional-basics.md) 또는 [Java enum 기초](./java/java-enum-basics.md) | "`없음`을 구분했는데 저장 단위와 rollback 범위가 여전히 헷갈려요" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | 이 README의 [빠른 탐색](#빠른-탐색) |

### queue가 보일 때 3칸만 자르기

`queue`라는 단어 하나 때문에 language primer에서 executor, scheduler, 운영형 queue deep dive로 바로 뛰지 않도록 아래 3칸만 먼저 자른다.

| 지금 보이는 문장 | 먼저 붙일 질문 | beginner-safe 다음 한 칸 |
|---|---|---|
| `먼저 들어온 작업부터 처리해요` | 자료구조 handoff인가 | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) -> [Service 계층 기초](../software-engineering/service-layer-basics.md) |
| `가까운 칸부터`, `최소 이동 횟수` | 알고리즘 거리 계산인가 | [Backend Algorithm Starter Pack](../algorithm/backend-algorithm-starter-pack.md) -> [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md) |
| `왜 queue가 둘 다 나오죠?`, `처음이라 헷갈려요` | 도구와 규칙을 섞었는가 | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md)로 돌아가 `queue는 도구`부터 다시 자른다 |

- 짧게 외우면 `queue는 도구`, `BFS는 규칙`, `Service는 책임 위치`다.
- 위 3칸이 정리되기 전에는 concurrency, executor, operator 문서를 첫 follow-up으로 열지 않는다.

빠른 왕복 루트를 5축으로 줄이면 아래 표를 먼저 보면 된다.

| 지금 고른 축 | 첫 primer | 바로 다음 한 칸 | 막히면 돌아올 자리 |
|---|---|---|---|
| 실행 모델 | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| 객체 모델 | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | [객체지향 핵심 원리](./java/object-oriented-core-principles.md) | 이 README의 [빠른 탐색](#빠른-탐색) |
| equality | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| collections | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | [Backend Data-Structure Starter Pack](../data-structure/backend-data-structure-starter-pack.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |
| optional/enum/null | [Java Optional 입문](./java/java-optional-basics.md) 또는 [Java enum 기초](./java/java-enum-basics.md) | [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md) | 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return) |

<a id="language-equality-collections-optional-quick-return"></a>
### Equality / Collections / Optional 복귀 표

primer에서 한 칸 읽고 돌아왔을 때는 이 구간을 safe return path로 써서 `비교 규칙`, `컬렉션 선택`, `Optional/enum/null` 중 아직 남은 질문 하나만 다시 고른다.

`collections -> optional/null -> enum 상태`를 한 줄로 붙이면 이렇다.

- 순서/중복/key 조회를 먼저 고른다 -> 단건의 없음이면 `Optional` -> 없음의 이유가 중요해지면 enum 상태나 상태 타입으로 올린다

| 지금 가장 헷갈리는 한 문장 | 먼저 갈 문서 | 20초 판단 기준 |
|---|---|---|
| "`List`가 비어 있으면 그게 `null` 아닌가요?" | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | 여러 건의 `0개`는 빈 컬렉션이 정상 상태다 |
| "`Optional`이랑 빈 리스트를 언제 갈라요?" | [Java Optional 입문](./java/java-optional-basics.md) | 단건의 없음은 `Optional`, 여러 건의 `0개`는 컬렉션이다 |
| "`HashMap#get(...) == null`이면 없는 거죠?" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md) | key 없음과 value `null`을 분리해서 읽는다 |
| "`없음`의 이유까지 말해야 하면 `Optional`이면 충분한가요?" | [Java enum 기초](./java/java-enum-basics.md) | 이유 이름표가 중요하면 enum 상태나 상태 타입으로 올린다 |
| "`enum` 정렬인데 `null` 위치와 선언 순서가 같이 헷갈려요" | [`null` 가능한 enum, 어떻게 정렬할까 beginner bridge](./java/nullable-enum-comparator-bridge.md) | `null` 위치 정책과 enum 값 비교 기준을 분리해서 읽는다 |
| "`save()`와 `HashMap#get(...)`이 같이 흔들려서 Java인지 DB인지 모르겠어요" | [Database First-Step Bridge](../database/database-first-step-bridge.md) | SQL 위치를 먼저 자른 뒤 남은 Java 질문은 이 README의 [빠른 탐색](#빠른-탐색)이나 이 표로 돌아와 다시 고른다 |

database로 한 칸 건너간 뒤에도 `new`, `equals()`, `HashMap#get(...)`, `Optional` 같은 문법 질문이 남으면 deep dive로 더 내려가지 말고 이 표나 이 README의 [빠른 탐색](#빠른-탐색)으로 바로 복귀한다.

| 지금 보이는 증상 | 먼저 갈 문서 | 바로 잡을 한 줄 | 다음 한 칸 |
|---|---|---|---|
| "`new`를 했는데 뭐가 생기는지 모르겠다" | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | 변수와 객체, `static`과 instance를 분리해서 본다 | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) |
| "한쪽만 바꿨는데 왜 다른 변수도 같이 바뀌지?" | [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) | `=`가 값 복사인지, 같은 객체 별칭인지 먼저 자른다 | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) |
| "`class`/객체/인스턴스가 같은 말처럼 보인다" | [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) | 설계도, 실행 중 실체, 그 실체를 가리키는 손잡이를 나눈다 | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) |
| "`==`와 `equals()`를 언제 써야 할지 모르겠다" | [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) | `==`는 같은 객체, `equals()`는 같은 값 질문이다 | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) |
| "`List`/`Set`/`Map`부터 고르기 어렵다" | [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) | 순서, 중복, key 조회 세 질문으로 먼저 자른다 | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) |
| "`Optional`, 빈 리스트, enum 상태 중 뭘 써야 할지 모르겠다" | [Java Optional 입문](./java/java-optional-basics.md) | 단건의 없음은 `Optional`, 다건의 0개는 빈 컬렉션, 없음의 이유는 상태 타입으로 본다 | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) |
| "`enum`을 상태 이름표로만 써야 하나, 없음의 이유까지 담아도 되나?" | [Java enum 기초](./java/java-enum-basics.md) | enum은 가능한 상태 후보를 고정하고, 이유가 중요해지면 상태 타입 entrypoint가 된다 | [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./java/enum-to-state-transition-beginner-bridge.md) |
| "`Set`은 왜 중복이 안 들어가고 `Map`은 왜 조회가 깨지지?" | [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) | 컬렉션 선택 뒤에는 동등성 규칙과 mutable key 위험을 같이 본다 | [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md) |

초보자 첫 route를 더 줄이면 이렇다. 실행 흐름이 흔들리면 1번, "같이 바뀐다" 같은 별칭 증상이 보이면 1번 다음 3번, 객체 용어가 흔들리면 2번, 비교 규칙이 흔들리면 3번, 자료구조 이름부터 안 잡히면 4번, 컬렉션 버그처럼 보여도 사실 비교 규칙 문제면 foundations로 간다.

운영/진단 문서는 beginner route의 중심이 아니다. primer 4장으로 질문을 먼저 자른 뒤 아래 cluster로 넘어가면 된다.

- runtime/diagnostics는 [Java Runtime and Diagnostics](#java-runtime-and-diagnostics)
- concurrency/async는 [Java Concurrency and Async](#java-concurrency-and-async)
- serialization/payload는 [Java Serialization and Payload Contracts](#java-serialization-and-payload-contracts)
- boundary/language 설계는 [Java Language and Boundary Design](#java-language-and-boundary-design)

특히 beginner가 많이 틀리는 지점은 "`List`/`Set`/`Map` 버그처럼 보여도 실제 원인은 참조 공유나 `equals()`/`hashCode()`"인 경우다. 자료구조 이름이 먼저 보여도 비교 규칙 문서로 한 칸 돌아가면 더 빨리 풀리는 경우가 많다.

자주 섞이는 오해도 아래 네 줄로 먼저 끊어 두면 route가 빨라진다.

- "`Student student`를 쓰면 학생 객체가 바로 생긴다"가 아니다. 변수 선언과 객체 생성은 다른 단계다.
- "`a = b`면 객체가 복사된다"가 아니다. 참조형에서는 같은 객체 별칭일 수 있다.
- "`==`면 다 값 비교다"가 아니다. 참조형에서는 보통 같은 객체 질문이다.
- "`HashSet`/`HashMap` 문제는 컬렉션 구현체만 바꾸면 된다"가 아니다. 동등성 규칙과 mutable key를 같이 본다.

두 문서를 연달아 보면 더 빨리 풀리는 흔한 조합도 있다.

| 이런 말이 먼저 나온다 | 읽는 순서 | 이유 |
|---|---|---|
| "한쪽만 바꿨는데 왜 다른 변수도 같이 바뀌지?" | 실행 모델 -> equality | 먼저 같은 객체를 같이 보고 있는지 분리해야 `==`/`equals()`도 덜 꼬인다 |
| "`HashSet` 중복이 안 막히거나 `HashMap#get()`이 깨진다" | equality -> collections | 값 비교 규칙을 먼저 잡고, 그 규칙이 컬렉션 조회에 어떻게 붙는지 이어서 본다 |
| "`List`/`Set`/`Map`부터 헷갈리는데 비교도 자꾸 틀린다" | foundations -> equality -> collections basics | 순서/중복/key 조회 질문을 먼저 자르고, 값 비교 규칙을 다시 붙인 뒤, 마지막에 구현체 목록을 정리하면 덜 과부하다 |

> retrieval-anchor-keywords: language readme, language navigator, language primer, language deep dive catalog, language survey, language roadmap, language playbook, java playbook, java runtime playbook, java diagnostics, java troubleshooting guide, java basics, 자바 처음 공부, 자바 처음 시작, 자바 처음인데 뭐부터, 자바 처음 배우는데 뭐부터, 자바 기초 뭐부터, java internals, java runtime catalog, java concurrency catalog, java async catalog, async quick links, concurrency quick links, executor cluster, executor common pool, common-pool cluster, completablefuture, cancellation propagation, cancellation context propagation, context propagation cluster, thread dump interpretation, jcmd cheat sheet, async-profiler vs JFR, flamegraph, safepoint diagnostics, jcstress, happens-before verification, common pool, executor sizing, structured concurrency, structured concurrency cluster, virtual threads, loom cluster, scoped value, threadlocal propagation, partial success fan-in, remote bulkhead metrics, bulkhead observability, permit contention, retry storm, upstream saturation, degraded response contract, aggregate error report, java serialization catalog, java boundary design, jvm primer, JFR Loom incident map, virtual thread diagnostics, JDBC cancel confirmation, DB-side cancel verification, java beginner oop, java class object primer, java oop first reading path, java data type primer, java type conversion primer, java scope primer, java casting primer, 자바 데이터타입 기초, 자바 형변환 기초, 자바 스코프 기초, 자바 캐스팅 기초, 데이터타입 형변환 스코프, 기본형 vs 참조형, 자바 기본형 참조형 어디로, 필드 vs 지역 변수, 자바 필드 지역 변수 어디로, length vs length(), 배열 length string length 차이, 객체지향 입문, 객체지향 큰 그림, 객체지향 처음 배우는데, 처음 배우는데 객체지향, 객체지향 기초 읽는 순서, 객체지향 언제 쓰는지, OOP 큰 그림, OOP 기초, OOP 읽는 순서, 클래스 객체 인스턴스 차이, 클래스랑 객체 차이, 인스턴스가 뭐예요, 객체지향 4대 원칙 기초, 캡슐화 상속 다형성 추상화 기초, 객체지향 설계 기초, 처음 배우는데 객체지향 설계, 객체지향 설계 큰 그림, java basics to oop design handoff, oop design basics handoff, 객체지향 디자인 패턴 기초, 처음 배우는데 디자인 패턴 큰 그림, 객체지향 패턴 입문 순서, java basics to design pattern handoff, design pattern beginner handoff, java package basics, java import basics, java package import boundary basics, 자바 package import 기초, 자바 package import 큰 그림, 처음 배우는데 package import, 자바 package는 왜 쓰는지, 자바 import는 언제 쓰는지, import 안 해도 되는 경우, 패키지랑 import 차이, 자바 public class 파일명 규칙, public class 왜 파일명이랑 같아야 해, java source file structure basics, java one public class per file, java public class file name rule, java top level class file convention, java top-level access modifier bridge, java top-level public package-private only, java top-level protected private compile error, java package private boundary basics, java same package no import, java default package avoid, java wildcard import subpackage, java access modifier basics, java member model basics, instance vs static member basics, java instance vs static methods, 인스턴스 메서드 static 메서드 차이, 처음 배우는데 static 언제 쓰는지, static 메서드 언제 쓰는지 기초, static이 뭐예요, 객체 없이 메서드 호출 왜 돼요, java static utility method basics, java static factory method basics, static factory 언제 쓰는지, new 대신 of from valueOf, java factory method basics, java of from valueOf basics, final field method class basics, java method basics, 메서드 생성자 차이 기초, 처음 배우는데 생성자 언제 쓰는지, 생성자 오버로딩 기초, this와 super 차이 기초, 생성자는 왜 필요해요, java constructor basics, java constructor chaining basics, java initialization order basics, java this super basics, java instance initializer block basics, java static initializer block basics, java parameter return type basics, java parameter passing basics, java pass by value basics, java reference type pass by value, java parameter reassignment basics, java side effect basics, java object state tracking, java aliasing basics, java method overloading basics, java inheritance basics, java extends basics, java overriding basics, java @Override basics, java dynamic dispatch basics, java overloading vs overriding, java overload override difference, 오버로딩 오버라이딩 차이, java compile time vs runtime method selection, java parent reference child object method call, java object state change basics, interface vs abstract class basics, java abstract class vs interface beginner, 추상 클래스 인터페이스 큰 그림, 처음 배우는데 추상 클래스 인터페이스 차이, 처음 배우는데 상속 언제 쓰는지, 상속 언제 쓰는지, 상속 언제 써야 하는지, 기초 상속 언제 쓰는지, 상속 vs 조합, 상속보다 조합 기초, 추상 클래스 인터페이스 상속 조합 순서, 추상 클래스 인터페이스 다음 조합 템플릿 전략, 추상 클래스 인터페이스 조합 템플릿 전략 읽는 순서, 상속 다음 추상 클래스 인터페이스, 추상 클래스 템플릿 메소드 언제 쓰는지, 템플릿 메소드 언제 쓰는지, 템플릿 메소드 기초, template method, template method beginner, abstract class template method beginner, hook method beginner, abstract step beginner, hook method primer, abstract step primer, 처음 배우는데 hook method, 처음 배우는데 훅 메서드, 처음 배우는데 abstract step, 처음 배우는데 추상 단계, 훅 메서드 기초, 추상 단계 기초, hook은 선택 빈칸, abstract step은 필수 빈칸, 템플릿 메소드 기초 먼저, 인터페이스와 조합, inheritance vs composition java beginner, inheritance vs composition beginner, java equality basics, java identity basics, java string comparison basics, java hashCode basics, java mutable key, hashmap mutable key, hashmap key mutation lookup, mutable key equals hashCode bug, java record equality basics, java record equals hashCode, record component equality, record value object equality, immutable value object basics, mutable entity equality hazard, java array equality basics, java arrays equals, java arrays deepEquals, java nested array comparison, java multidimensional array equality, java array debug printing basics, java array print weird output, 배열 출력 왜 이상해요, java array toString basics, java array deepToString basics, java nested array reference-like output, java array default toString, java `[I@` output meaning, java `[Ljava.lang.String;@` output meaning, java array copy basics, java array clone basics, java Arrays.copyOf basics, java shallow copy deep copy array, java nested array copy, java multidimensional array copy, java Arrays.sort basics, java Arrays.binarySearch basics, java array sorting basics, java array searching basics, java binarySearch insertion point, java binarySearch same comparator, java comparable basics, java comparator basics, java comparator comparing, java comparator thenComparing, java comparator reversed, java comparator reversed placement, java mixed direction comparator chain, java primitive descending tie breaker, java thenComparingInt reversed placement, java thenComparingLong reversed placement, java thenComparingDouble reversed placement, java comparator nullsFirst, java comparator nullsLast, java nullsLast reversed descending, java descending nullsLast comparator, wrapper number descending null last, comparator utility patterns, java list sort vs stream sorted, java list sort comparator, java stream sorted comparator, same comparator list sort stream sorted, stream toList vs collectors toList, java Stream.toList beginner, java Collectors.toList mutability, stream result mutability bridge, sorted toList unmodifiable, collectors toList no guarantees, toCollection ArrayList, natural ordering basics, custom comparator basics, compareTo basics, TreeSet natural ordering duplicate, TreeMap natural ordering replace value, treemap mutable key, treemap key mutation lookup, no comparator treeset treemap compareTo, compareTo same key slot, HashSet duplicate rule, TreeSet duplicate rule, HashSet vs TreeSet duplicate semantics, equals hashCode vs compare == 0, TreeSet compareTo 0 duplicate, TreeSet comparator equals consistency, TreeMap comparator equals consistency, TreeSet TreeMap comparator tie breaker, TreeMap compare 0 same key, sorted map duplicate surprise, compare zero replaces value, sorted set duplicate surprise, navigablemap mental model, navigableset mental model, java treeset first last floor ceiling lower higher, java treemap firstKey lastKey floorKey ceilingKey lowerKey higherKey, java treemap floorEntry ceilingEntry lowerEntry higherEntry, comparator order drives lookup behavior, floor ceiling comparator order, descending comparator floor ceiling surprise, java exception basics, 자바 예외처리 기초, 예외 처리 처음 배우는데, 예외 처리 큰 그림, throw catch 언제 쓰는지, checked unchecked 차이 기초, 처음 배우는데 try catch, try catch 기초, 언제 throws 쓰는지, 예외 처리 primer, checked unchecked 큰 그림, java generics basics, 자바 제네릭 입문, 제네릭 처음 배우는데, 제네릭 큰 그림, 제네릭 언제 쓰는지, List Object와 List String 차이, List<Object> vs List<String>, List<Object>와 List<String> 차이, 왜 List<String>은 List<Object>가 아닌가, 처음 배우는데 List Object vs List String, 제네릭 왜 쓰는지 쉽게, java enum basics, 자바 enum 기초, enum 처음 배우는데, enum 언제 쓰는지, 상태값 int 대신 enum, ordinal 쓰면 안되는 이유, java collections basics, 자바 컬렉션 기초, 컬렉션 큰 그림, 자바 컬렉션 큰 그림, 처음 배우는데 컬렉션, 컬렉션 처음 배우는데 뭐부터, 리스트 셋 맵 차이, list set map 차이, list set map 큰 그림, ArrayList HashSet HashMap 언제 쓰는지, 처음 배우는데 List Set Map 언제 쓰는지, List Set Map 언제 써야 하나, collection beginner route, collection first reading, beginner collection primer, coroutine basics, c++ basics, language index, what to read next
> retrieval-anchor-keywords: language readme, language navigator, language primer, language deep dive catalog, language survey, language roadmap, language playbook, java playbook, java runtime playbook, java diagnostics, java troubleshooting guide, java basics, 자바 처음 공부, 자바 처음 시작, 자바 처음인데 뭐부터, 자바 처음 배우는데 뭐부터, 자바 기초 뭐부터, java internals, java runtime catalog, java concurrency catalog, java async catalog, async quick links, concurrency quick links, executor cluster, executor common pool, common-pool cluster, completablefuture, cancellation propagation, cancellation context propagation, context propagation cluster, thread dump interpretation, jcmd cheat sheet, async-profiler vs JFR, flamegraph, safepoint diagnostics, jcstress, happens-before verification, common pool, executor sizing, structured concurrency, structured concurrency cluster, virtual threads, loom cluster, scoped value, threadlocal propagation, partial success fan-in, remote bulkhead metrics, bulkhead observability, permit contention, retry storm, upstream saturation, degraded response contract, aggregate error report, java serialization catalog, java boundary design, jvm primer, JFR Loom incident map, virtual thread diagnostics, JDBC cancel confirmation, DB-side cancel verification, java beginner oop, java class object primer, java oop first reading path, java data type primer, java type conversion primer, java scope primer, java casting primer, 자바 데이터타입 기초, 자바 형변환 기초, 자바 스코프 기초, 자바 캐스팅 기초, 데이터타입 형변환 스코프, 기본형 vs 참조형, 자바 기본형 참조형 어디로, 필드 vs 지역 변수, 자바 필드 지역 변수 어디로, length vs length(), 배열 length string length 차이, 객체지향 입문, 객체지향 큰 그림, 객체지향 처음 배우는데, 처음 배우는데 객체지향, 객체지향 기초 읽는 순서, 객체지향 언제 쓰는지, OOP 큰 그림, OOP 기초, OOP 읽는 순서, 클래스 객체 인스턴스 차이, 클래스랑 객체 차이, 인스턴스가 뭐예요, 객체지향 4대 원칙 기초, 캡슐화 상속 다형성 추상화 기초, 객체지향 설계 기초, 처음 배우는데 객체지향 설계, 객체지향 설계 큰 그림, java basics to oop design handoff, oop design basics handoff, 객체지향 디자인 패턴 기초, 처음 배우는데 디자인 패턴 큰 그림, 객체지향 패턴 입문 순서, java basics to design pattern handoff, design pattern beginner handoff, java package basics, java import basics, java package import boundary basics, 자바 package import 기초, 자바 package import 큰 그림, 처음 배우는데 package import, 자바 package는 왜 쓰는지, 자바 import는 언제 쓰는지, import 안 해도 되는 경우, 패키지랑 import 차이, 자바 public class 파일명 규칙, public class 왜 파일명이랑 같아야 해, java source file structure basics, java one public class per file, java public class file name rule, java top level class file convention, java top-level access modifier bridge, java top-level public package-private only, java top-level protected private compile error, java package private boundary basics, java same package no import, java default package avoid, java wildcard import subpackage, java access modifier basics, java member model basics, instance vs static member basics, java instance vs static methods, 인스턴스 메서드 static 메서드 차이, 처음 배우는데 static 언제 쓰는지, static 메서드 언제 쓰는지 기초, static이 뭐예요, 객체 없이 메서드 호출 왜 돼요, java static utility method basics, java static factory method basics, static factory 언제 쓰는지, new 대신 of from valueOf, java factory method basics, java of from valueOf basics, final field method class basics, java method basics, 메서드 생성자 차이 기초, 처음 배우는데 생성자 언제 쓰는지, 생성자 오버로딩 기초, this와 super 차이 기초, 생성자는 왜 필요해요, java constructor basics, java constructor chaining basics, java initialization order basics, java this super basics, java instance initializer block basics, java static initializer block basics, java parameter return type basics, java parameter passing basics, java pass by value basics, java reference type pass by value, java parameter reassignment basics, java side effect basics, java object state tracking, java aliasing basics, java method overloading basics, java inheritance basics, java extends basics, java overriding basics, java @Override basics, java dynamic dispatch basics, java overloading vs overriding, java overload override difference, 오버로딩 오버라이딩 차이, java compile time vs runtime method selection, java parent reference child object method call, java object state change basics, interface vs abstract class basics, java abstract class vs interface beginner, 추상 클래스 인터페이스 큰 그림, 처음 배우는데 추상 클래스 인터페이스 차이, 처음 배우는데 상속 언제 쓰는지, 상속 언제 쓰는지, 상속 언제 써야 하는지, 기초 상속 언제 쓰는지, 상속 vs 조합, 상속보다 조합 기초, 추상 클래스 인터페이스 상속 조합 순서, 추상 클래스 인터페이스 다음 조합 템플릿 전략, 추상 클래스 인터페이스 조합 템플릿 전략 읽는 순서, 상속 다음 추상 클래스 인터페이스, 추상 클래스 템플릿 메소드 언제 쓰는지, 템플릿 메소드 언제 쓰는지, 템플릿 메소드 기초, template method, template method beginner, abstract class template method beginner, hook method beginner, abstract step beginner, hook method primer, abstract step primer, 처음 배우는데 hook method, 처음 배우는데 훅 메서드, 처음 배우는데 abstract step, 처음 배우는데 추상 단계, 훅 메서드 기초, 추상 단계 기초, hook은 선택 빈칸, abstract step은 필수 빈칸, 템플릿 메소드 기초 먼저, 인터페이스와 조합, inheritance vs composition java beginner, inheritance vs composition beginner, java equality basics, java identity basics, java string comparison basics, java hashCode basics, java mutable key, hashmap mutable key, hashmap key mutation lookup, mutable key equals hashCode bug, java record equality basics, java record equals hashCode, record component equality, record value object equality, immutable value object basics, mutable entity equality hazard, java array equality basics, java arrays equals, java arrays deepEquals, java nested array comparison, java multidimensional array equality, java array debug printing basics, java array print weird output, 배열 출력 왜 이상해요, java array toString basics, java array deepToString basics, java nested array reference-like output, java array default toString, java `[I@` output meaning, java `[Ljava.lang.String;@` output meaning, java array copy basics, java array clone basics, java Arrays.copyOf basics, java shallow copy deep copy array, java nested array copy, java multidimensional array copy, java Arrays.sort basics, java Arrays.binarySearch basics, java array sorting basics, java array searching basics, java binarySearch insertion point, java binarySearch same comparator, java comparable basics, java comparator basics, java comparator comparing, java comparator thenComparing, java comparator reversed, java comparator reversed placement, java mixed direction comparator chain, java primitive descending tie breaker, java thenComparingInt reversed placement, java thenComparingLong reversed placement, java thenComparingDouble reversed placement, java comparator nullsFirst, java comparator nullsLast, java nullsLast reversed descending, java descending nullsLast comparator, wrapper number descending null last, comparator utility patterns, java list sort vs stream sorted, java list sort comparator, java stream sorted comparator, same comparator list sort stream sorted, stream toList vs collectors toList, java Stream.toList beginner, java Collectors.toList mutability, stream result mutability bridge, sorted toList unmodifiable, collectors toList no guarantees, toCollection ArrayList, natural ordering basics, custom comparator basics, compareTo basics, TreeSet natural ordering duplicate, TreeMap natural ordering replace value, treemap mutable key, treemap key mutation lookup, no comparator treeset treemap compareTo, compareTo same key slot, HashSet duplicate rule, TreeSet duplicate rule, HashSet vs TreeSet duplicate semantics, equals hashCode vs compare == 0, TreeSet compareTo 0 duplicate, TreeSet comparator equals consistency, TreeMap comparator equals consistency, TreeSet TreeMap comparator tie breaker, TreeMap compare 0 same key, sorted map duplicate surprise, compare zero replaces value, sorted set duplicate surprise, navigablemap mental model, navigableset mental model, java treeset first last floor ceiling lower higher, java treemap firstKey lastKey floorKey ceilingKey lowerKey higherKey, java treemap floorEntry ceilingEntry lowerEntry higherEntry, comparator order drives lookup behavior, floor ceiling comparator order, descending comparator floor ceiling surprise, java exception basics, 자바 예외처리 기초, 예외 처리 처음 배우는데, 예외 처리 큰 그림, throw catch 언제 쓰는지, checked unchecked 차이 기초, 처음 배우는데 try catch, try catch 기초, 언제 throws 쓰는지, 예외 처리 primer, checked unchecked 큰 그림, java generics basics, 자바 제네릭 입문, 제네릭 처음 배우는데, 제네릭 큰 그림, 제네릭 언제 쓰는지, List Object와 List String 차이, List<Object> vs List<String>, List<Object>와 List<String> 차이, 왜 List<String>은 List<Object>가 아닌가, 처음 배우는데 List Object vs List String, 제네릭 왜 쓰는지 쉽게, java enum basics, 자바 enum 기초, enum 처음 배우는데, enum 언제 쓰는지, 상태값 int 대신 enum, ordinal 쓰면 안되는 이유, enum string bridge, enum vs string compare, enum 문자열 비교 헷갈, enum valueOf null blank lowercase unknown, java enum payload string, status string payload, enum incoming payload basics, enum == string 왜 안돼요, java collections basics, 자바 컬렉션 기초, 컬렉션 큰 그림, 자바 컬렉션 큰 그림, 처음 배우는데 컬렉션, 컬렉션 처음 배우는데 뭐부터, 리스트 셋 맵 차이, list set map 차이, list set map 큰 그림, ArrayList HashSet HashMap 언제 쓰는지, 처음 배우는데 List Set Map 언제 쓰는지, List Set Map 언제 써야 하나, collection beginner route, collection first reading, beginner collection primer, coroutine basics, c++ basics, language index, what to read next
> retrieval-anchor-keywords: queue가 service 코드에 왜 나와요, BFS랑 같은 queue예요, queue handoff vs bfs, service queue beginner bridge, java collections to service bridge, 컬렉션 다음 자료구조 뭐부터

## 빠른 탐색

- 학습 순서 `survey`가 먼저 필요하면:
  - [루트 README](../../README.md)
  - [Advanced Backend Roadmap](../../ADVANCED-BACKEND-ROADMAP.md)
- cross-category handoff가 먼저 필요하면:
  - `save()`, `Repository`, SQL 위치가 같이 헷갈리면 [Database README의 빠른 탐색](../database/README.md#빠른-탐색)
  - `controller`, `service`, bean, `@Transactional`이 같이 보이면 [Spring README: 빠른 탐색](../spring/README.md#빠른-탐색)
- 길을 잃었을 때 safe return path:
  - Java primer 한 장을 읽고도 `처음`, `왜`, `헷갈려요`가 남으면 이 README의 [equality / collections / optional 복귀 표](#language-equality-collections-optional-quick-return)나 [빠른 탐색](#빠른-탐색)으로 돌아온다
  - database primer를 한 장 읽고도 질문이 다시 `new`, `객체`, `equals()`, `HashMap#get(...)` 축이면 [빠른 탐색](#빠른-탐색)으로 바로 복귀한다
- Java `primer`부터 읽고 싶다면:
  - [자바 언어의 구조와 기본 문법](./java/java-language-basics.md) - 처음 배우는데 `source -> bytecode -> JVM` 실행 큰 그림부터 `데이터타입(기본형 vs 참조형)`/자동 형변환과 casting/지역 변수와 블록 scope, 배열/제어문 기초까지 한 번에 잡는 primer
  - 자주 묻는 초급 라우팅만 빨리 고르면: `기본형 vs 참조형`, `필드 vs 지역 변수`, `arr.length` vs `str.length()`는 모두 먼저 [자바 언어의 구조와 기본 문법](./java/java-language-basics.md)으로 들어가면 된다.
  - 메서드 호출 뒤 값이 왜 바뀌어 보이는지까지 이어지면 [Java parameter 전달, pass-by-value, side effect 입문](./java/java-parameter-passing-pass-by-value-side-effects-primer.md)으로 옮겨 `기본형 vs 참조형` 다음 단계인 "무엇이 복사되는가"를 이어서 본다.
  - `필드 vs 지역 변수`를 객체 상태와 멤버 관점으로 다시 보고 싶으면 [Java 접근 제한자와 멤버 모델 입문](./java/java-access-modifiers-member-model-basics.md)으로 이어서 본다.
  - [Java 반복문과 스코프 follow-up 입문](./java/java-loop-control-scope-follow-up-primer.md) - 제어문 첫 읽기 다음 단계에서 `반복 횟수가 정해지면 for, 조건이 유지되는 동안 돌면 while` 선택 기준과 `for`/`while`/`break`/`continue`/scope 비교표를 같이 묶고, `코드 손으로 추적하는 법`, `루프 표로 푸는 법`, `for문 안에서 선언한 변수 밖에서 왜 안 보임`, `break는 가장 가까운 반복문만 끝남`, `while 무한 루프 왜 생김` 같은 scope/loop 초급 혼동을 짧은 예제와 trace table로 바로 교정하는 beginner primer
  - [Java package와 import 경계 입문](./java/java-package-import-boundary-basics.md) - 처음 배우는데 `package`가 왜 필요한지, `import`를 언제 쓰고 언제 생략하는지, `public class` 파일명 규칙과 `package-private` 경계를 큰 그림으로 잡는 기초 primer
  - [Java 패키지 경계 퀵체크 카드](./java/java-package-boundary-quickcheck-card.md) - `same package / subclass / non-subclass`를 10초 표로 먼저 자르고, `public`/`protected`/package-private 접근 가능 여부를 빠르게 판단하게 돕는 beginner quick card
  - [Java Top-level 타입 접근 제한자 브리지](./java/top-level-type-access-modifier-bridge.md) - `class`/`interface`/`enum`/`record`가 top-level에서 모두 같은 접근 제한 규칙(`public`/package-private)과 같은 `public` 파일명 규칙을 따른다는 점을 한 화면 표 + 예제로 묶은 beginner bridge
  - [Java default package 회피 브리지](./java/java-default-package-avoid-bridge.md) - top-level 파일명 규칙을 배운 직후, `package` 선언을 생략한 default package가 왜 금방 import/구조화 문제로 이어지는지 짧은 예제로 연결하는 beginner bridge
  - [접근 제한자 오해 미니 퀴즈: top-level vs member](./java/java-access-modifier-top-level-member-mini-quiz.md) - `private`/`protected`가 "항상 안 된다"가 아니라 top-level에서는 안 되고 member에서는 될 수 있다는 핵심 경계를 5문항 예측형으로 빠르게 교정하는 beginner drill
  - [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) - 클래스 선언/참조 변수 선언/객체 생성을 3단계로 끊어 보고, `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> 상속보다 조합` route의 첫 출발점이 되는 beginner bridge
  - [객체지향 설계 기초](../software-engineering/oop-design-basics.md) - 처음 배우는데 클래스/객체 문법 다음에 역할, 책임, 협력 큰 그림을 잡고, 그다음 `상속 언제 쓰는지` primer로 넘어가게 돕는 handoff primer
  - [Java 메서드와 생성자 실전 입문](./java/java-methods-constructors-practice-primer.md) - 처음 배우는데 메서드/생성자 차이, `parameter`/`return`/`this`/`super` 흐름, 메서드/생성자를 각각 언제 쓰는지까지 묶어 정리한 기초 primer
  - [Java parameter 전달, pass-by-value, side effect 입문](./java/java-parameter-passing-pass-by-value-side-effects-primer.md) - 처음 배우는데 "기본형은 안 바뀌는데 객체는 왜 바뀌어 보여요?"가 헷갈릴 때 값 복사/참조값 복사/mutation vs reassignment 큰 그림으로 정리하는 기초 primer
  - [Java 오버로딩 vs 오버라이딩 입문](./java/java-overloading-vs-overriding-beginner-primer.md) - 처음 배우는데 같은 이름 메서드가 왜 다르게 동작하는지 막힐 때, 컴파일 시그니처 선택 vs 런타임 구현 선택으로 구분하는 primer
  - [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md) - 처음 배우는데 `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> 상속보다 조합` route에서 `상속 언제 쓰는지` 지점을 붙잡아 주는 handoff primer
  - [객체지향 디자인 패턴 기초](../design-pattern/object-oriented-design-pattern-basics.md) - 처음 배우는데 OOP 기초 다음에 `상속 vs 조합`, `템플릿 메소드`, `전략`, `팩토리`가 언제 쓰는지 큰 그림으로 이어 주는 handoff primer
  - 처음 배우는데 클래스/객체 큰 그림 뒤에 `상속 언제 쓰는지`, `추상 클래스와 인터페이스를 어디서 나누는지`, `상속 vs 조합`, `hook method`, `abstract step`, `템플릿 메소드가 예외인지`, `객체지향 설계 기초`, `객체지향 디자인 패턴 기초`가 궁금하면 먼저 `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> quick check -> 상속보다 조합` route를 [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) -> [객체지향 핵심 원리](./java/object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md) -> [추상 클래스 vs 인터페이스 Follow-up Quick Check](./java/abstract-class-vs-interface-follow-up-drill.md) -> [상속보다 조합 기초](../design-pattern/composition-over-inheritance-basics.md) 순서로 먼저 고정하고, 그다음 [객체지향 설계 기초](../software-engineering/oop-design-basics.md) -> [객체지향 디자인 패턴 기초](../design-pattern/object-oriented-design-pattern-basics.md) -> [템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md) -> [템플릿 메소드 vs 전략](../design-pattern/template-method-vs-strategy.md)로 넓히면 된다
  - [Java 생성자와 초기화 순서 입문](./java/java-constructors-initialization-order-basics.md)
  - [Java 접근 제한자와 멤버 모델 입문](./java/java-access-modifiers-member-model-basics.md) - 접근/소유/변경 3축 + 새 멤버 30초 결정표에 더해, `protected`의 메서드 호출 규칙과 필드 참조 규칙이 같다는 common confusion을 `this`/`childRef`/`baseRef` 3문항 follow-up과 `import`/유사 패키지명/`protected` 범위 오답노트로 묶어 하위 클래스 문맥 오개념을 더 빨리 교정하는 beginner member-model primer
  - [Access Modifier Boundary Lab](./java/java-access-modifier-boundary-lab.md) - `private`/package-private/`protected` 경계를 같은 패키지/다른 패키지/하위 클래스 문맥으로 나눠 보고, `this.protectedPin` vs `childRef.protectedPin` vs `baseRef.protectedPin` 3문항 follow-up으로 `protected` 참조 규칙을 바로 손검증하게 만드는 beginner 실습
  - [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java/java-instance-static-factory-methods-primer.md) - 인스턴스/`static` 메서드를 언제 쓰는지, `new` 대신 `of`/`from`/`valueOf`를 고르는 기준을 큰 그림으로 잡는 beginner primer
  - [생성자에서 값 객체 팩터리로 넘어가는 첫 브리지](./java/constructor-to-value-object-factory-bridge.md) - `new`는 익숙한데 `of()`/`fromInput()`이 왜 필요한지, raw input 검증/정규화와 value object 입구 이름 붙이기를 beginner 질문 흐름으로 연결하는 bridge
  - 처음 배우는데 `생성자로 충분한지`, `값 객체로 올려야 하는지`, `왜 of를 쓰나요?`가 같이 섞이면 [Java 메서드와 생성자 실전 입문](./java/java-methods-constructors-practice-primer.md) -> [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java/java-instance-static-factory-methods-primer.md) -> [생성자에서 값 객체 팩터리로 넘어가는 첫 브리지](./java/constructor-to-value-object-factory-bridge.md) 순서로 한 칸씩 붙이면 beginner retrieval이 related-doc 의존 없이도 더 안정적이다.
  - [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) - 처음 배우는데 `==`와 `equals()`를 언제 쓰는지, 문자열 비교와 `hashCode()`를 왜 같이 보아야 하는지 큰 그림으로 잡는 primer
  - [Record and Value Object Equality](./java/record-value-object-equality-basics.md) - `record`를 "값 경계를 적는 문법"으로 먼저 이해하고, array/list component와 mutable key 위험만 초급 기준으로 먼저 자르는 equality follow-up primer
  - [Record component로 `BigDecimal`을 써도 되나요?](./java/record-bigdecimal-component-faq.md) - `1.0` vs `1.00`, canonicalization, `HashSet`/`TreeSet` 갈림을 record value object 문맥으로 다시 묶은 beginner FAQ primer
  - [Java Array Equality Basics](./java/java-array-equality-basics.md) - "내용이 같은데 왜 `==`가 false지?"가 막힐 때: reference 비교와 값 비교를 분리해 `==`/`Arrays.equals`/`Arrays.deepEquals` 선택 기준을 잡는 primer
  - [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md) - "`[I@...`처럼 출력이 이상한가?"를 먼저 가르고, `Arrays.toString()`/`Arrays.deepToString()` 다음에 비교 문제인지 복사 문제인지 30초 선택표로 넘겨 주는 primer
  - [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md) - "`copied = original`인데 왜 같이 바뀌지?"가 막힐 때: 대입 alias vs `clone()`/`Arrays.copyOf()`와 shallow/deep copy를 비교하는 primer
  - [Comparable and Comparator Basics](./java/java-comparable-comparator-basics.md) - 처음 배우는데 `compareTo()`와 `Comparator`를 언제 쓰는지, 정렬 기준을 어디에 두는지 기초부터 정리하는 primer
  - [Beginner Drill Sheet: Equality vs Ordering](./java/equality-vs-ordering-beginner-drill-sheet.md) - `equals()`/`compareTo()`를 분리해 `HashSet`/`TreeSet`/`TreeMap` 결과를 실행 전에 먼저 예측하고, 60초 빈칸 워크시트로 답을 기록해 보는 초급 실습 시트
  - [Record-Comparator 60초 미니 드릴](./java/record-comparator-60-second-mini-drill.md) - `record` 자동 `equals()`와 name-only comparator를 일부러 어긋나게 두고, 같은 워크시트에서 `thenComparingLong(Student::id)` 하나로 collapse가 separation으로 바뀌는 순간까지 붙여 보는 beginner worksheet
  - [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./java/treemap-record-containskey-get-name-comparator-drill.md) - `TreeMap` 조회를 `containsKey()`/`get()`만으로 좁혀, `record` key와 name-only comparator에서 왜 다른 `id`로도 조회가 되는지 손예측하게 만드는 beginner follow-up drill
  - [Natural Ordering in TreeSet and TreeMap](./java/treeset-treemap-natural-ordering-compareto-bridge.md) - `Comparator` 없이 `compareTo()`만으로 생기는 `TreeSet` 중복과 `TreeMap` 값 덮어쓰기 surprise 보기
  - [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./java/treemap-put-return-value-overwrite-bridge.md) - `put` 반환값을 "새 값"으로 오해하는 초급 혼동을 짧은 표와 예제로 바로 교정하는 beginner bridge
  - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./java/bigdecimal-sorted-collection-bridge.md) - `1.0` vs `1.00` 갈림을 재현하고, 도메인 "같음" 기준을 먼저 고르는 15초 선택 흐름까지 포함한 beginner bridge
  - [BigDecimal 생성 정책 입문 브리지](./java/bigdecimal-construction-policy-beginner-bridge.md) - `new BigDecimal(double)` 대신 문자열 생성자와 `BigDecimal.valueOf(...)`를 언제 고를지, 초급자 기준 입력 안정성 순서를 짧은 표와 예제로 붙이는 beginner bridge
  - [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./java/bigdecimal-setscale-unnecessary-validation-primer.md) - `setScale(..., UNNECESSARY)`를 반올림 트릭이 아니라 "반올림 없이 정해진 소수 자릿수 안에 들어와야 통과"라는 입력 검증 정책으로 설명하는 beginner primer
  - [BigDecimal Key 정책 30초 체크리스트](./java/bigdecimal-key-policy-30-second-checklist.md) - `1.0` vs `1`을 같은 key로 볼지, 정규화는 어디서 한 번만 할지, 조회/중복/정규화 테스트 3종을 PR 전에 점검하는 beginner checklist
  - [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./java/bigdecimal-striptrailingzeros-input-boundary-bridge.md) - `stripTrailingZeros`를 고급 함정보다 먼저 "입구에서 한 번만 정규화할지, `setScale`/출력 정책과 무엇이 다른지"를 연결하는 beginner bridge
  - [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./java/bigdecimal-1-0-vs-1-00-collections-mini-drill.md) - `size()`/`put` 반환값/`get` 조회 결과를 실행 전에 적어 보는 1페이지 워크시트
  - [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./java/bigdecimal-hashset-treeset-contains-mini-drill.md) - `add("1.0")` 뒤 `contains("1")`와 `contains("1.00")`가 왜 `HashSet`과 `TreeSet`에서 갈리는지 조회 기준만 따로 고정하는 1페이지 drill
  - [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./java/bigdecimal-hashmap-treemap-lookup-mini-drill.md) - `put("1.0")` 뒤 `containsKey/get("1")`가 `HashMap`과 `TreeMap`에서 왜 갈리는지 조회만 분리해 손예측하는 1페이지 drill
  - [Comparator Utility Patterns](./java/java-comparator-utility-patterns.md) - `comparingInt`/`thenComparingInt` 계열, `reversed()` 위치, mixed-direction primitive tie-breaker 조립 감각까지 이어서 보기
  - [Comparator 변수명 짓기 초급 패턴](./java/comparator-variable-naming-beginner-primer.md) - `byName`, `byScoreDescThenName`처럼 comparator 이름만 읽어도 정렬 의도와 재사용 지점을 바로 파악하게 돕는 beginner primer
  - [Comparator Reversed Scope Primer](./java/comparator-reversed-scope-primer.md) - `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()`의 범위 차이를 작은 예제로 정리하고, `TreeSet` distinctness는 왜 그대로인지까지 짚는 beginner primer
  - [`List.sort` vs `Collections.sort` 미니 브리지](./java/list-sort-vs-collections-sort-mini-bridge.md) - 둘 다 `List` 제자리 정렬일 때, 초급 기준으로 어떤 호출 형태를 먼저 고르면 읽기 쉬운지와 comparator 재사용 감각을 짧게 정리한 beginner bridge
  - [`List.sort` vs `Stream.sorted` Comparator Bridge](./java/list-sort-vs-stream-sorted-comparator-bridge.md) - 같은 comparator chain을 mutable list 정렬과 stream 정렬 결과에 재사용하는 감각 잡기
  - [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./java/stream-tolist-vs-collectors-tolist-mutability-bridge.md) - `sorted(...)` 뒤에서 읽기 전용 결과와 수정 가능한 결과를 어떻게 구분할지, `Collectors.toList()`에 mutability를 기대하지 말아야 하는 이유를 정리한 beginner bridge
  - [Nullable Wrapper Comparator Bridge](./java/nullable-wrapper-comparator-bridge.md) - primitive tie-breaker 감각에서 nullable `Integer`/`Long`/`Double` follow-up로 넘어갈 때 `nullsFirst`/`nullsLast`가 먼저 붙는 이유와 `rank == null`끼리 `TreeSet`/`TreeMap`에서 같은 자리처럼 보일 수 있다는 점까지 보기
  - [Comparator in TreeSet and TreeMap](./java/treeset-treemap-comparator-tie-breaker-basics.md) - `compare == 0`, tie-breaker, 값 덮어쓰기 surprise를 같이 정리
  - [Mutable Fields Inside Sorted Collections](./java/treeset-treemap-mutable-comparator-fields-primer.md) - `TreeSet`/`TreeMap` 안에서 comparator가 보는 mutable 필드를 바꾸면 조회와 정렬이 왜 깨지는지 보기
  - [Mutable Keys in HashMap and TreeMap](./java/hashmap-treemap-mutable-key-lookup-primer.md) - `equals()`/`hashCode()`/`compareTo()`가 보는 key 필드를 `put(...)` 뒤에 바꾸면 왜 `get`/`containsKey`/`remove`가 길을 잃는지 비교하는 beginner primer
  - [NavigableMap and NavigableSet Mental Model](./java/navigablemap-navigableset-mental-model.md) - `first`/`last`/`floor`/`ceiling`/`lower`/`higher`를 comparator order 이웃 찾기로 이해하고, reverse order에서 `floor`/`ceiling`이 왜 직관과 어긋나는지까지 2행 미니 워크시트로 손검증하는 primer
  - [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./java/submap-boundaries-primer.md) - `TreeSet`/`TreeMap` range API를 "정렬된 줄의 구간 창"으로 읽게 만들고, `head = 끝 제외`, `tail = 시작 포함`, `sub = [from, to)`를 짧은 표와 예제로 고정하는 beginner primer
  - [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md) - `Set`을 처음 배울 때 "왜 하나는 2개고 하나는 1개지?"를 한 화면 비교표로 바로 예측하게 만들며, `equals/hashCode` vs `compare == 0` 기준을 beginner 눈높이로 나눠 주는 primer
  - [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md) - "`sort` 뒤 원본이 바뀌고 `binarySearch`가 이상할 때": `Arrays.sort()` 제자리 정렬과 `binarySearch()` 전제를 함께 잡는 primer
  - [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](./java/arrays-sort-binarysearch-precondition-bridge.md) - "정렬은 했는데 왜 검색 결과가 이상해요?"처럼 처음 헷갈리는 질문에서, 정렬 기준과 검색 기준이 같은지 먼저 확인하게 만드는 beginner bridge
  - [BinarySearch Duplicate Boundary Primer](./java/binarysearch-duplicate-boundary-primer.md) - "`binarySearch()`가 맞는 값을 찾았는데 첫 위치가 왜 아니죠?"처럼 중복값 경계가 처음 헷갈릴 때, hit 뒤 좌우 확장으로 first/last를 읽게 만드는 primer
  - [BinarySearch With Nullable Wrapper Sort Keys](./java/binarysearch-nullable-wrapper-sort-keys.md) - nullable `Integer`/`Long`/`Double` sort key에서 같은 comparator를 `Arrays.sort(...)`와 `Arrays.binarySearch(...)`에 같이 재사용하는 beginner bridge
- [객체지향 핵심 원리](./java/object-oriented-core-principles.md) - 처음 배우는데 OOP 큰 그림을 먼저 잡고, `클래스 선언/참조 변수 선언/객체 생성` 1분 브리지로 헷갈림을 푼 뒤 `상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> 상속보다 조합` 순서로 이어지게 만드는 primer
  - [불변 객체와 방어적 복사 입문](./java/java-immutable-object-basics.md) - `record` 생성자에서 `List.copyOf(...)`, 배열 복사, `Collections.unmodifiableList(...)`를 어떻게 나눠 써야 하는지 한 장으로 먼저 잡는 beginner primer
  - [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md) - 처음 배우는데 `객체지향 큰 그림 -> 상속 언제 쓰는지` 다음에 `abstract class`와 `interface`를 어디서 나누는지 이어 붙이는 beginner handoff primer
  - [인터페이스 `default method` vs `static` method 프라이머](./java/interface-default-vs-static-method-primer.md) - 처음 배우는데 인터페이스 안의 메서드 몸체 둘을 빠르게 구분하려고, "구현체가 물려받는 기본 동작"과 "인터페이스 이름으로만 부르는 도우미"를 한 장으로 정리한 primer
  - [인터페이스 default method 기초: 계약 vs evolution](./java/interface-default-method-contract-evolution-primer.md) - 처음 배우는데 `default method`가 인터페이스의 핵심 계약인지, 기존 구현체를 살리기 위한 evolution용 기본값인지 헷갈릴 때 보는 beginner primer
  - [Java `default method` diamond conflict 기초](./java/interface-default-method-diamond-conflict-basics.md) - 다중 인터페이스 구현에서 같은 `default method`가 부딪힐 때, `클래스 우선 -> 더 구체적인 인터페이스 우선 -> 동률이면 override` 큰 그림과 `InterfaceName.super` 예제를 먼저 잡는 beginner primer
  - [Java 예외 처리 기초](./java/java-exception-handling-basics.md) - 처음 배우는데 `try-catch`를 왜 쓰는지부터 시작해, checked/unchecked를 언제 쓰는지와 `throw`/`throws`/`catch`를 어디서 나누는지까지 큰 그림과 30초 분기표로 잡는 기초 primer
  - [Java 제네릭 입문](./java/java-generics-basics.md) - 처음 배우는데 `<T>`가 왜 필요한지, `List<Object> vs List<String>` 같은 초급 혼동과 와일드카드 첫 분기까지 큰 그림으로 정리하는 기초 primer
- [Java 스트림과 람다 입문](./java/java-stream-lambda-basics.md) - 처음 배우는데 `for` 루프와 `stream` 파이프라인을 언제 나눠 쓰는지, 람다를 왜 쓰는지 큰 그림부터 시작하는 primer
- [`filter` vs `map` 결정 미니 카드](./java/stream-filter-vs-map-decision-mini-card.md) - `조건에 맞는 것만 남기기`와 `남긴 값을 다른 값으로 바꾸기`를 한 페이지 표와 예제로 끊어, 초보자가 `filter`/`map`을 문장 단위로 바로 구분하게 돕는 mini card
  - [Java String 기초](./java/java-string-basics.md)
  - [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md) - `status == OrderStatus.PAID`와 `"PAID"` 같은 외부 문자열 payload를 같은 층위로 섞지 않도록, `문자열 -> enum 변환 -> enum 비교` 순서를 짧은 표와 예제로 고정하는 beginner bridge
  - [Java enum 기초](./java/java-enum-basics.md) - 처음 배우는데 상태값을 `int` 대신 enum으로 언제 바꾸는지, `ordinal`보다 `name` 중심으로 설계하는 이유를 잡는 beginner primer
  - [Enum 키라면 언제 `HashMap`에서 `EnumMap`으로 옮길까](./java/enummap-status-policy-lookup-primer.md) - key 후보가 enum으로 닫힌 순간을 신호로 읽고, 상태별 라벨 같은 작은 lookup table을 `HashMap`에서 `EnumMap`으로 옮기는 기준을 한 예제로 잡아 주는 beginner bridge
  - [Enum equality quick bridge](./java/enum-equality-quick-bridge.md) - enum에서 `==`와 `equals()`가 왜 둘 다 맞는지, 그래도 왜 `==`를 관용적으로 쓰는지 null-safe 비교 감각까지 짧게 잇는 beginner bridge
  - [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./java/enum-to-state-transition-beginner-bridge.md) - `setStatus(...)`가 규칙을 흩뿌리는 이유와, `confirm()`/`cancel()` 같은 도메인 행동 안에서 허용된 전이를 검증해야 미션 코드가 읽히는 이유를 함께 잇는 beginner bridge
  - 컬렉션 beginner route는 `처음 배우는데 언제 쓰는지` -> `리스트 셋 맵 차이` -> requirement drill -> foundations primer 순서로 따라가면 된다.
  - [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) - 처음 배우는데 `List`/`Set`/`Map`을 언제 쓰는지, `컬렉션 큰 그림`, `리스트 셋 맵 차이`, `Collection` vs `Collections`, `ArrayList`/`HashSet`/`HashMap` 첫 선택을 `요구 -> 인터페이스 -> 구현체` 30초 순서로 묶어 주는 primer
  - [List/Set/Map Requirement-to-Type Drill](./java/list-set-map-requirement-to-type-drill.md) - 요구 문장을 `List`/`Set`/`Map`으로 먼저 번역하는 1페이지 초급 드릴에 더해, `순서` 단어가 없거나 `id로 찾기`처럼 key가 암시된 문장 패턴 FAQ/오답노트까지 묶은 primer
  - [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) - `List`/`Set`/`Map` 선택 뒤에 바로 따라오는 `equals()`/`hashCode()`/`Comparable`, mutable key, 순회 중 수정 trade-off를 한 장에 묶어 초보자 실수를 줄이는 primer
  - [Map Value-Shape Drill](./java/map-value-shape-drill.md) - `Map<K,V>`에서 key는 정했는데 value를 `단일값`/`리스트`/`집계객체` 중 무엇으로 둘지 막히는 초보자를 위해, `Integer`/`List<T>`/`record` 같은 첫 Java 타입으로 바로 잇는 후속 미니 드릴
  - [`LinkedHashSet` 순서 유지 vs `TreeSet` 정렬 유지 브리지](./java/linkedhashset-order-dedup-mini-bridge.md) - `순서 유지`와 `정렬 유지`를 같은 뜻으로 오해하지 않도록, `LinkedHashSet`의 삽입 순서와 `TreeSet`의 정렬 순서를 1페이지 비교표로 갈라 주는 beginner bridge
  - [Collection vs Collections vs Arrays 유틸리티 미니 브리지](./java/collection-vs-collections-vs-arrays-utility-mini-bridge.md) - 컬렉션 입문 다음에 가장 많이 섞어 쓰는 `Collection` API, `Collections` helper, `Arrays` helper를 5가지 공통 작업으로 빠르게 구분하는 beginner bridge
  - [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./java/arrays-aslist-fixed-size-list-checklist.md) - `Arrays.asList(...)`에서 `add/remove`가 왜 실패하는지, `new ArrayList<>(...)`와 `List.of(...)`를 언제 고를지 1페이지로 잇는 beginner checklist
  - [Iterable vs Collection vs Map 브리지 입문](./java/iterable-collection-map-iteration-bridge.md) - 컬렉션 입문 직후 가장 자주 헷갈리는 `Iterable`/`Collection`/`Map` 계층 차이와 `for-each`/`entrySet` 반복 API 선택을 짧게 연결하는 beginner bridge
  - [Map Iteration Patterns Cheat Sheet](./java/map-iteration-patterns-cheat-sheet.md) - `entrySet()`/`keySet()`/`values()`를 "key+value / key only / value only" 기준으로 바로 고르고, `keySet()+get()` 첫 시도 실수를 Do/Don't 예시로 빠르게 교정하는 1페이지 beginner 치트시트
  - [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md) - `get()`의 `null`이 "key 없음"인지 "value가 null"인지 헷갈릴 때, `containsKey()`와 `getOrDefault()`를 어떤 질문에서 꺼내야 하는지 짧은 표와 예제로 정리한 beginner primer
  - [Java Optional 입문](./java/java-optional-basics.md) - 처음 배우는데 `Optional`을 언제 쓰는지, `null`과 차이, `orElse`/`orElseGet` 선택 기준, `get()` 남용을 피하는 기초를 정리한 primer
  - [`Optional` 필드/파라미터 anti-pattern 30초 카드](./java/optional-field-parameter-antipattern-card.md) - `Optional`을 반환값 대신 필드나 파라미터에 넣을 때 왜 상태가 두 겹으로 꼬이는지, 그리고 plain 값/오버로딩/빈 컬렉션/상태 타입으로 무엇을 대신 고를지 빠르게 정리한 beginner card
  - [`Optional.empty()` 비교와 값 꺼내기 전 equality 판단 프라이머](./java/optional-empty-equals-before-unwrapping-primer.md) - `Optional.empty()`를 `null`처럼 읽지 않고, 값을 꺼내기 전 `isEmpty()`/`equals()`/`filter(...).isPresent()` 중 무엇을 고를지 초급자용 표로 정리한 primer
  - [Java 스레드와 동기화 기초](./java/java-thread-basics.md)
  - [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md)
- Java `deep dive catalog`에서 bucket을 바로 고르려면:
  - [Java Runtime and Diagnostics](#java-runtime-and-diagnostics)
  - [Java Concurrency and Async](#java-concurrency-and-async)
  - [Java Serialization and Payload Contracts](#java-serialization-and-payload-contracts)
  - [Java Language and Boundary Design](#java-language-and-boundary-design)
- Java concurrency / async `subcluster`로 바로 들어가려면:
  - [Executor / Common Pool Cluster](#java-concurrency-executor--common-pool-cluster)
  - [Cancellation / Context Propagation Cluster](#java-concurrency-cancellation--context-propagation-cluster)
  - [Loom / Structured Concurrency Cluster](#java-concurrency-loom--structured-concurrency-cluster)
- 운영/진단 절차가 먼저 필요한 `[playbook]`으로 가려면:
  - `[playbook]` [JFR, JMC Performance Playbook](./java/jfr-jmc-performance-playbook.md)
  - `[playbook]` [OOM Heap Dump Playbook](./java/oom-heap-dump-playbook.md)
  - `[playbook]` [ClassLoader Memory Leak Playbook](./java/classloader-memory-leak-playbook.md)
  - `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- Java runtime symptom으로 바로 들어가려면:
  - [Thread Dump State Interpretation](./java/thread-dump-state-interpretation.md)
  - [`jcmd` Diagnostic Command Cheat Sheet](./java/jcmd-diagnostic-command-cheatsheet.md)
  - [Async-profiler vs JFR](./java/async-profiler-vs-jfr-comparison.md)
  - [Safepoint and Stop-the-World Diagnostics](./java/safepoint-stop-the-world-diagnostics.md)
- JMM / concurrency 검증 도구로 바로 들어가려면:
  - [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)
- coroutine / other-language `primer` entrypoint로 가려면:
  - [코루틴](./coroutine.md)
  - 아래 `C++ primer` 구간
- cross-category bridge로 확장하려면:
  - 아래 `교차 카테고리 브리지` 구간
- 문서 역할이 헷갈리면:
  - [Navigation Taxonomy](../../rag/navigation-taxonomy.md)
  - [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)

## Java

Java 구간은 `primer -> deep dive catalog -> cross-category bridge` 순서로 읽도록 정리했다.

### Java primer

- primer에서 한 칸 읽고 다음 문서가 막히면 [빠른 탐색](#빠른-탐색)으로 돌아가고, Java 밖으로 넘어가야 하면 [교차 카테고리 브리지](#교차-카테고리-브리지)에서 다음 카테고리를 고른다.
- [자바 언어의 구조와 기본 문법](./java/java-language-basics.md) - 처음 배우는데 `source -> bytecode -> JVM` 실행 큰 그림부터 타입/형변환/변수 스코프, 배열/제어문 기초까지 한 번에 잡는 primer
- Java 첫 입구는 문서를 넓게 훑기보다 아래 5개 축만 먼저 잡는 편이 덜 흔들린다.
  [Java 실행 모델과 객체 메모리 mental model 입문](./java/java-execution-object-memory-mental-model-primer.md) -> [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) -> [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) -> [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) -> [Java Optional 입문](./java/java-optional-basics.md)
- 초급자용 빠른 번역표는 이 네 줄로 먼저 붙인다. `한 명 없음 -> Optional`, `여러 개 0개 -> 빈 컬렉션`, `Map#get(...) == null -> containsKey()/getOrDefault()`, `없음의 이유 -> enum 상태`
- `List`/`Set`/`Map`은 알겠는데 `빈 리스트`, `Optional`, `Map#get(...) == null`, enum 상태가 같이 섞이면 이 짧은 우회로로 자른다.
  [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) -> [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md) -> [Java Optional 입문](./java/java-optional-basics.md) -> [Java enum 기초](./java/java-enum-basics.md) -> [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md)
- `mutable key`, comparator, `Map#get(...) == null`, enum 상태 같은 follow-up은 위 5개 축 중 어디가 흔들리는지 먼저 고른 뒤 옆 가지로 붙인다.
- [Java 반복문과 스코프 follow-up 입문](./java/java-loop-control-scope-follow-up-primer.md) - 제어문 첫 읽기 다음 단계에서 `반복 횟수가 정해지면 for, 조건이 유지되는 동안 돌면 while` 선택 기준과 `for`/`while`/`break`/`continue`/scope 비교표를 같이 묶고, `코드 손으로 추적하는 법`, `루프 표로 푸는 법`, `for문 안에서 선언한 변수 밖에서 왜 안 보임`, `break는 가장 가까운 반복문만 끝남`, `while 무한 루프 왜 생김` 같은 scope/loop 초급 혼동을 짧은 예제와 trace table로 바로 교정하는 beginner primer
- [Java package와 import 경계 입문](./java/java-package-import-boundary-basics.md) - 처음 배우는데 `package`가 왜 필요한지, `import`를 언제 쓰고 언제 생략하는지, `public class` 파일명 규칙과 `package-private` 경계를 큰 그림으로 잡는 기초 primer
- [Java 패키지 경계 퀵체크 카드](./java/java-package-boundary-quickcheck-card.md) - `same package / subclass / non-subclass`를 10초 표로 먼저 자르고, `public`/`protected`/package-private 접근 가능 여부를 빠르게 판단하게 돕는 beginner quick card
- [Java Top-level 타입 접근 제한자 브리지](./java/top-level-type-access-modifier-bridge.md) - `class`/`interface`/`enum`/`record`가 top-level에서 모두 같은 접근 제한 규칙(`public`/package-private)을 따르고, `public` 파일명 규칙과 top-level vs nested type 혼동까지 한눈 카드로 정리한 beginner bridge
- [Java default package 회피 브리지](./java/java-default-package-avoid-bridge.md) - top-level 파일명 규칙 바로 다음 단계에서, `package` 선언을 생략한 default package가 왜 실제 코드에서는 금방 import/구조화 문제를 만든다고 보는지 짧은 표와 예제로 잇는 beginner bridge
- [접근 제한자 오해 미니 퀴즈: top-level vs member](./java/java-access-modifier-top-level-member-mini-quiz.md) - `private`/`protected`가 top-level에서는 왜 안 되고 member에서는 왜 가능한지 5문항 예측형으로 바로 점검하게 만드는 beginner drill
- [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) - 클래스/객체 기초에서 `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스` beginner route를 여는 첫 primer
- 처음 배우는데 `기본형 vs 참조형`, `클래스 vs 객체`, `인터페이스 vs 추상 클래스`가 한꺼번에 섞이면 위 primer 하나에서 먼저 큰 그림을 잡고, 그다음 [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) -> [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) -> [Java Optional 입문](./java/java-optional-basics.md) -> [Java enum 기초](./java/java-enum-basics.md) 순서로 한 칸씩 붙이면 초급 동선이 덜 흔들린다.
- [Java 메서드와 생성자 실전 입문](./java/java-methods-constructors-practice-primer.md) - 처음 배우는데 메서드/생성자 차이, `parameter`/`return`/`this`/`super` 흐름, 메서드/생성자를 각각 언제 쓰는지까지 묶어 정리한 기초 primer
- [Java parameter 전달, pass-by-value, side effect 입문](./java/java-parameter-passing-pass-by-value-side-effects-primer.md) - 처음 배우는데 "기본형은 안 바뀌는데 객체는 왜 바뀌어 보여요?"를 값 복사/참조값 복사/mutation vs reassignment로 끊어 이해하는 beginner primer
- [Java 오버로딩 vs 오버라이딩 입문](./java/java-overloading-vs-overriding-beginner-primer.md) - 같은 이름 메서드에서 처음 배우는 사람이 가장 헷갈리는 overloading/overriding을 컴파일 시그니처 선택과 런타임 dispatch로 나눠 잡는 기초 primer
- [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md) - 처음 배우는데 `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> 상속보다 조합` route에서 `상속 언제 쓰는지`를 묻는 질의(예: `처음 배우는데 상속 언제 쓰는지`)를 직접 받는 handoff primer
- [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md) - `공통 상태를 부모가 쥐는가`와 `계약만 필요한가`를 먼저 자르고, 상속 다음 분기점에서 템플릿 메소드/전략으로 넘어가기 전 큰 그림을 잡는 primer
- [Template Method vs Strategy Quick Check Card](./java/template-method-vs-strategy-quick-check-card.md) - 추상 클래스 vs 인터페이스 다음에 `부모가 흐름을 쥔다 vs 밖에서 구현을 넣는다`를 4개 짧은 사례로 바로 판별하는 quick card
- [Java 생성자와 초기화 순서 입문](./java/java-constructors-initialization-order-basics.md)
- [Java 접근 제한자와 멤버 모델 입문](./java/java-access-modifiers-member-model-basics.md) - 접근/소유/변경 3축 + 새 멤버 30초 결정표에 더해, `protected`의 메서드 호출 규칙과 필드 참조 규칙이 같다는 common confusion을 `this`/`childRef`/`baseRef` 3문항 follow-up과 `import`/유사 패키지명/`protected` 범위 오답노트로 묶어 하위 클래스 문맥 오개념을 더 빨리 교정하는 beginner member-model primer
- [Access Modifier Boundary Lab](./java/java-access-modifier-boundary-lab.md) - `private`/package-private/`protected` 경계를 같은 패키지/다른 패키지/하위 클래스 문맥으로 나눠 보고, `this.protectedPin` vs `childRef.protectedPin` vs `baseRef.protectedPin` 3문항 follow-up으로 `protected` 참조 규칙을 바로 손검증하게 만드는 beginner 실습
- [Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문](./java/java-instance-static-factory-methods-primer.md) - 인스턴스/`static` 메서드를 언제 쓰는지, `new` 대신 `of`/`from`/`valueOf`를 고르는 기준을 큰 그림으로 잡는 beginner primer
- [생성자에서 값 객체 팩터리로 넘어가는 첫 브리지](./java/constructor-to-value-object-factory-bridge.md) - `new`는 익숙한데 `of()`/`fromInput()`이 왜 필요한지, raw string 검증/정규화와 value object 입구 이름 붙이기를 beginner 질문에 맞춰 연결하는 bridge
- [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) - 처음 배우는데 `==` vs `equals()`가 왜 갈리는지, 문자열 비교와 `equals()`/`hashCode()`를 언제 같이 봐야 하는지 큰 그림으로 정리하는 beginner primer
- [Record and Value Object Equality](./java/record-value-object-equality-basics.md) - record vs entity 선택 경계에 더해 배열/가변 컬렉션 component FAQ와 `record equals` vs comparator confusion 표까지 묶은 beginner primer
- [Record component로 `BigDecimal`을 써도 되나요?](./java/record-bigdecimal-component-faq.md) - `BigDecimal` component가 `record` equality와 컬렉션 동작에 어떻게 들어오는지, `1.0` vs `1.00`와 생성 시 정규화를 초급자 FAQ로 분리한 primer
- [Java 배열 입문 공통 confusion 체크리스트](./java/java-array-common-confusion-checklist.md) - 배열 primer를 다시 펼칠 때 `출력/비교/공유/정렬` 네 갈래를 먼저 나눠 `==` vs 값 비교, alias, `Arrays.sort()` 원본 변경 혼동을 한 장에서 다시 잡는 beginner bridge
- [Java Array Equality Basics](./java/java-array-equality-basics.md) - "내용이 같은데 왜 `==`가 false지?"가 막힐 때: reference 비교와 값 비교를 분리해 `==`/`Arrays.equals`/`Arrays.deepEquals` 선택 기준을 잡는 primer
- [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md) - "`[I@...`처럼 출력이 이상한가?"를 먼저 가르고, `Arrays.toString()`/`Arrays.deepToString()` 다음에 비교 문제인지 복사 문제인지 30초 선택표로 넘겨 주는 primer
- [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md) - "`copied = original`인데 왜 같이 바뀌지?"가 막힐 때: 대입 alias vs `clone()`/`Arrays.copyOf()`와 shallow/deep copy를 비교하는 primer
- [Comparable and Comparator Basics](./java/java-comparable-comparator-basics.md) - 처음 배우는데 `Comparable`/`Comparator`를 언제 쓰는지, 기본 정렬(`compareTo`)과 상황별 정렬(`Comparator`) 경계를 비교하고 `equals()` vs `compare == 0` 불일치 체크 카드를 바로 적용해 보는 beginner primer
- [Beginner Drill Sheet: Equality vs Ordering](./java/equality-vs-ordering-beginner-drill-sheet.md) - `equals()`/`compareTo()`를 분리해 `HashSet`/`TreeSet`/`TreeMap` 결과를 실행 전에 먼저 예측하고, 60초 빈칸 워크시트로 답을 기록해 보는 초급 실습 시트
- [Record-Comparator 60초 미니 드릴](./java/record-comparator-60-second-mini-drill.md) - `record`의 자동 `equals()`와 name-only comparator가 왜 다른 결과를 만드는지 `HashSet`/`TreeSet`/`TreeMap` 한 페이지 예제로 바로 손예측하는 beginner worksheet
- [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./java/treemap-record-containskey-get-name-comparator-drill.md) - `containsKey()`/`get()`만 따로 떼어, `record` key와 name-only comparator가 만드는 조회 surprise를 한 페이지로 손예측하는 beginner follow-up drill
- [Natural Ordering in TreeSet and TreeMap](./java/treeset-treemap-natural-ordering-compareto-bridge.md) - `Comparator` 없이 `compareTo()`만으로 생기는 `TreeSet` 중복과 `TreeMap` 값 덮어쓰기 surprise 보기
- [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./java/treemap-put-return-value-overwrite-bridge.md) - `put` 반환값을 "새 값"으로 오해하는 초급 혼동을 짧은 표와 예제로 바로 교정하는 beginner bridge
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./java/bigdecimal-sorted-collection-bridge.md) - `1.0` vs `1.00` 갈림을 재현하고, 도메인 "같음" 기준을 먼저 고르는 15초 선택 흐름까지 포함한 beginner bridge
- [BigDecimal 생성 정책 입문 브리지](./java/bigdecimal-construction-policy-beginner-bridge.md) - `new BigDecimal(double)` 대신 문자열 생성자와 `BigDecimal.valueOf(...)`를 언제 고를지, 초급자 기준 입력 안정성 순서를 짧은 표와 예제로 붙이는 beginner bridge
- [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./java/bigdecimal-setscale-unnecessary-validation-primer.md) - `setScale(..., UNNECESSARY)`를 반올림 트릭이 아니라 "반올림 없이 정해진 소수 자릿수 안에 들어와야 통과"라는 입력 검증 정책으로 설명하는 beginner primer
- [BigDecimal Key 정책 30초 체크리스트](./java/bigdecimal-key-policy-30-second-checklist.md) - `1.0` vs `1`을 같은 key로 볼지, 정규화는 어디서 한 번만 할지, 조회/중복/정규화 테스트 3종을 PR 전에 점검하는 beginner checklist
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./java/bigdecimal-striptrailingzeros-input-boundary-bridge.md) - `stripTrailingZeros`를 고급 함정보다 먼저 "입구에서 같은 값을 같은 표현으로 맞출지, `setScale`/출력 정책과 무엇이 다른지"를 정하는 beginner bridge
- [BigDecimal 출력 정책 미니 브리지: `toString()` vs `toPlainString()`](./java/bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge.md) - 로그/JSON/UI에서 사람이 읽는 문자열과 serializer 계약을 분리해, 지수 표기 혼동을 줄이는 beginner bridge
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./java/bigdecimal-1-0-vs-1-00-collections-mini-drill.md) - `size()`/`put` 반환값/`get` 조회 결과를 실행 전에 적어 보는 1페이지 워크시트
- [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./java/bigdecimal-hashset-treeset-contains-mini-drill.md) - `add("1.0")` 뒤 `contains("1")`와 `contains("1.00")`가 왜 `HashSet`과 `TreeSet`에서 갈리는지 조회 기준만 따로 고정하는 1페이지 drill
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./java/bigdecimal-hashmap-treemap-lookup-mini-drill.md) - `put("1.0")` 뒤 `containsKey/get("1")`가 `HashMap`과 `TreeMap`에서 왜 갈리는지 조회만 분리해 손예측하는 1페이지 drill
- [Comparator Utility Patterns](./java/java-comparator-utility-patterns.md) - `comparingInt`/`thenComparingInt` 계열, `reversed()` 위치, mixed-direction primitive tie-breaker 조립 감각까지 이어서 보기
- [Comparator 변수명 짓기 초급 패턴](./java/comparator-variable-naming-beginner-primer.md) - `byName`, `byScoreDescThenName`처럼 comparator 이름만 읽어도 정렬 의도와 재사용 지점을 바로 파악하게 돕는 beginner primer
- [Comparator Reversed Scope Primer](./java/comparator-reversed-scope-primer.md) - `a.reversed().thenComparing(b)`와 `a.thenComparing(b).reversed()`의 범위 차이를 작은 예제로 정리하고, `TreeSet` distinctness는 왜 그대로인지까지 짚는 beginner primer
- [`List.sort` vs `Collections.sort` 미니 브리지](./java/list-sort-vs-collections-sort-mini-bridge.md) - 둘 다 `List` 제자리 정렬일 때, 초급 기준으로 어떤 호출 형태를 먼저 고르면 읽기 쉬운지와 comparator 재사용 감각을 짧게 정리한 beginner bridge
- [`List.sort` vs `Stream.sorted` Comparator Bridge](./java/list-sort-vs-stream-sorted-comparator-bridge.md) - 같은 comparator chain을 mutable list 정렬과 stream 정렬 결과에 재사용하는 감각 잡기
- [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./java/stream-tolist-vs-collectors-tolist-mutability-bridge.md) - `sorted(...)` 뒤에서 `toList()`를 읽기 전용 결과로 이해하고, 수정 가능한 결과가 필요하면 `toCollection(ArrayList::new)`처럼 명시적으로 고르는 beginner bridge
- [Nullable Wrapper Comparator Bridge](./java/nullable-wrapper-comparator-bridge.md) - primitive tie-breaker 감각에서 nullable `Integer`/`Long`/`Double` follow-up로 넘어갈 때 `nullsFirst`/`nullsLast`가 먼저 붙는 이유와 `rank == null`끼리 `TreeSet`/`TreeMap`에서 같은 자리처럼 보일 수 있다는 점까지 보기
- [Comparator in TreeSet and TreeMap](./java/treeset-treemap-comparator-tie-breaker-basics.md) - `compare == 0`이 sorted collection에서 "같은 자리"라는 뜻으로 어떻게 작동하는지, business key에서 멈출지 `id`를 안전 tie-breaker로 붙일지까지 한 번에 잡는 beginner primer
- [Mutable Fields Inside Sorted Collections](./java/treeset-treemap-mutable-comparator-fields-primer.md) - `TreeSet`/`TreeMap` 안에서 comparator가 보는 mutable 필드를 바꾸면 조회와 정렬이 왜 깨지는지 보는 beginner primer
- [NavigableMap and NavigableSet Mental Model](./java/navigablemap-navigableset-mental-model.md) - `first`/`last`/`floor`/`ceiling`/`lower`/`higher`를 comparator order 이웃 찾기로 보고, reverse order `floor`/`ceiling` 2행 미니 워크시트까지 확인하는 primer
- [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md) - 처음 배우는데 `HashSet`과 `TreeSet` 중복 결과가 왜 다른지, `equals/hashCode`와 `compare == 0`을 한 화면 예측 표로 비교해 `size()` 오해를 줄이는 primer
- [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md) - "`sort` 뒤 원본이 바뀌고 `binarySearch`가 이상할 때": `Arrays.sort()` 제자리 정렬과 `binarySearch()` 전제를 함께 잡는 primer
- [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](./java/arrays-sort-binarysearch-precondition-bridge.md) - 정렬만 했다고 끝이 아니라, 검색도 같은 규칙을 써야 한다는 첫 함정을 짧은 체크리스트로 정리한 beginner bridge
- [BinarySearch Duplicate Boundary Primer](./java/binarysearch-duplicate-boundary-primer.md) - 중복값에서 "왜 첫 위치가 아니라 아무 위치가 나오죠?"를 바로 풀고, 다음 단계 lower/upper bound로 넘어가기 전에 좌우 확장 mental model을 먼저 붙이는 primer
- [BinarySearch With Nullable Wrapper Sort Keys](./java/binarysearch-nullable-wrapper-sort-keys.md) - nullable `Integer`/`Long`/`Double` sort key에서 같은 comparator를 `Arrays.sort(...)`와 `Arrays.binarySearch(...)`에 같이 재사용하는 beginner bridge
- [객체지향 핵심 원리](./java/object-oriented-core-principles.md) - 처음 배우는데 OOP 큰 그림, 객체지향 4대 원칙, 그리고 `클래스 선언/참조 변수 선언/객체 생성` 혼동을 짧게 풀어 준 뒤 `상속 언제 쓰는지`와 `추상 클래스/인터페이스`로 이어지는 beginner route primer
- object model 쪽 beginner route는 `실행 모델 -> 클래스/객체 -> OOP 큰 그림` 순서로 고정하고, 접근 제한자/초기화 순서/패턴 비교는 그다음 follow-up으로 내려 보낸다.
- [불변 객체와 방어적 복사 입문](./java/java-immutable-object-basics.md) - `record`가 `final`이라도 `List`와 배열은 왜 생성자에서 다시 복사해야 하는지, snapshot과 read-only view 차이를 짧은 표로 묶은 beginner primer
- [불변 객체와 방어적 복사](./java/immutable-objects-and-defensive-copying.md)
- [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md) - 공통 상태/흐름은 추상 클래스, 바꿔 끼울 계약은 인터페이스+조합으로 나누고 beginner 첫 읽기 bridge를 `추상 클래스/인터페이스 -> 상속보다 조합 -> 템플릿 메소드 패턴 기초 -> 템플릿 메소드 vs 전략` 순서로 고정하는 entrypoint primer
- [추상 클래스 vs 인터페이스 Follow-up Quick Check](./java/abstract-class-vs-interface-follow-up-drill.md) - `공통 상태가 필요하면 추상 클래스, 계약만 필요하면 인터페이스` 판단을 5개 짧은 예제로 다시 확인하고, `default method`와 조합까지 함께 가르는 beginner quick-check drill
- [상속보다 조합 기초](../design-pattern/composition-over-inheritance-basics.md) - 추상 클래스/인터페이스를 읽은 직후 "기본값은 왜 조합인가"를 같은 beginner route에서 바로 이어 주는 primer
- [템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md) - 조합을 먼저 본 뒤에도 부모가 흐름을 쥐어야 하는 예외적 좁은 경우를 연결하는 follow-up primer
- [템플릿 메소드 vs 전략](../design-pattern/template-method-vs-strategy.md) - 템플릿 메소드 다음 단계에서 상속 skeleton과 전략 주입을 한 축으로 비교하게 만드는 follow-up primer
- [Marker Interface vs Capability Method 브리지](./java/marker-interface-vs-capability-method-bridge.md) - 처음 배우는데 marker interface와 `supportsX()` 같은 capability-style method를 어디서 나누는지, 타입 표지와 런타임 질문을 짧은 표와 예제로 연결하는 interface 설계 첫 진입점
- [인터페이스 `default method` vs `static` method 프라이머](./java/interface-default-vs-static-method-primer.md) - 인터페이스 안의 두 "몸체 있는 메서드"를 처음 배울 때, 구현체에 내려가는 기본 동작과 인터페이스 이름으로만 부르는 정적 helper를 빠르게 가르는 beginner primer
- [인터페이스 default method 기초: 계약 vs evolution](./java/interface-default-method-contract-evolution-primer.md) - `default method`를 인터페이스 계약 자체와 같은 층위로 보지 않고, 기존 구현체와 함께 진화시키는 기본값/편의 메서드로 읽는 beginner primer
- [Java `default method` diamond conflict 기초](./java/interface-default-method-diamond-conflict-basics.md) - 다중 인터페이스에서 같은 `default method` 충돌이 났을 때 자동 선택이 아니라 구현 클래스의 override가 필요하다는 점을 짧은 규칙표와 예제로 먼저 정리하는 beginner primer
- [추상 클래스 vs 인터페이스](./java/abstract-class-vs-interface.md) - beginner first-hit은 바로 위 [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md)으로 보내고, 그다음도 `상속보다 조합 -> 템플릿 메소드 패턴 기초 -> 템플릿 메소드 vs 전략` handoff를 먼저 유지한 뒤에 `default method`, sealed interface, binary compatibility 같은 intermediate guardrail로 내려가는 deep dive
- [Java 예외 처리 기초](./java/java-exception-handling-basics.md) - 처음 배우는데 `try-catch`를 왜 쓰는지부터 시작해, checked/unchecked를 언제 쓰는지와 `throw`/`throws`/`catch`를 어디서 나누는지까지 큰 그림과 30초 분기표로 잡는 기초 primer
- [Java 제네릭 입문](./java/java-generics-basics.md) - 처음 배우는데 `<T>`가 왜 필요한지, `List<Object> vs List<String>` 같은 초급 혼동과 와일드카드 첫 분기까지 큰 그림으로 정리하는 기초 primer
- [Java 스트림과 람다 입문](./java/java-stream-lambda-basics.md) - 처음 배우는데 람다와 스트림을 언제 쓰는지, 같은 문제를 `for`와 `stream`으로 나란히 보고 `filter`/`map`/`collect`로 안전하게 옮기는 감각까지 잡는 primer
- [`for` vs `stream` 중단 신호 프라이머](./java/for-vs-stream-stop-sign-primer.md) - `break`, 복합 누적, checked exception 번역처럼 `stream`으로 과하게 밀어 넣기 쉬운 순간을 짧은 stop-sign note로 분리해, 초보자가 "언제 그냥 `for`로 두는지" 먼저 판단하게 돕는 primer
- [`filter` vs `map` 결정 미니 카드](./java/stream-filter-vs-map-decision-mini-card.md) - `OO만 골라라`와 `OO로 바꿔라`를 구분하는 10초 표와 주문 예제로, 초보자가 `filter`와 `map`의 역할을 바로 가르는 stream follow-up card
  - [Java String 기초](./java/java-string-basics.md)
  - [Java enum 기초](./java/java-enum-basics.md) - 처음 배우는데 상태값을 `int` 대신 enum으로 언제 바꾸는지, `ordinal`보다 `name` 중심으로 설계하는 이유를 잡는 beginner primer
  - [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./java/enum-string-boundary-bridge.md) - `status == OrderStatus.PAID`와 `"PAID"` 같은 외부 문자열 payload를 같은 층위로 섞지 않도록, `문자열 -> enum 변환 -> enum 비교` 순서를 짧은 표와 예제로 고정하는 beginner bridge
  - [Enum 키라면 언제 `HashMap`에서 `EnumMap`으로 옮길까](./java/enummap-status-policy-lookup-primer.md) - key 후보가 enum으로 닫힌 순간을 신호로 읽고, 상태별 라벨 같은 작은 lookup table을 `HashMap`에서 `EnumMap`으로 옮기는 기준을 한 예제로 잡아 주는 beginner bridge
- [Enum equality quick bridge](./java/enum-equality-quick-bridge.md) - enum에서 `==`와 `equals()`가 왜 둘 다 맞는지, 그래도 왜 `==`를 관용적으로 쓰는지 null-safe 비교 감각까지 짧게 잇는 beginner bridge
- 컬렉션 beginner route는 `컬렉션 기본 구분` -> `리스트 셋 맵 차이` -> requirement drill -> ordered-map follow-up -> foundations primer 순서로 묶고, 정렬 계약이나 mutable key incident는 foundations 뒤 관련 문서로 넘긴다.
- [Java 컬렉션 프레임워크 입문](./java/java-collections-basics.md) - 처음 배우는데 `List`/`Set`/`Map`을 언제 쓰는지, `컬렉션 큰 그림`, `리스트 셋 맵 차이`, `Collection` vs `Collections`, `ArrayList`/`HashSet`/`HashMap` 첫 선택을 `요구 -> 인터페이스 -> 구현체` 30초 순서로 묶어 주는 primer
- [List/Set/Map Requirement-to-Type Drill](./java/list-set-map-requirement-to-type-drill.md) - 요구 문장을 `List`/`Set`/`Map`으로 먼저 번역하는 1페이지 초급 드릴에 더해, `순서` 단어가 없거나 `id로 찾기`처럼 key가 암시된 문장 패턴 FAQ/오답노트까지 묶은 primer
- [HashMap vs TreeMap 초급 선택 브리지](./java/hashmap-vs-treemap-beginner-selection-bridge.md) - `Map`은 알겠는데 `HashMap`과 `TreeMap` 중 무엇을 먼저 고를지 막히는 초보자를 위해, `정렬 없음` vs `key 정렬/범위 조회`를 한 표와 한 예제로 끊어 주는 ordered-map follow-up bridge
- [Ordered Map Null-Safe Practice Drill](./java/ordered-map-null-safe-practice-drill.md) - `TreeMap`을 고른 뒤 `floorEntry`/`ceilingEntry`가 왜 `null`이 되는지 경계 예제로 바로 손예측하게 만들어, ordered map null-safe 감각을 collections beginner route 바로 다음에 붙이는 practice drill
- [Collections, Equality, and Mutable-State Foundations](./java/collections-equality-mutable-state-foundations.md) - `List`/`Set`/`Map` 선택 뒤에 바로 따라오는 `equals()`/`hashCode()`/`Comparable`, mutable key, 순회 중 수정 trade-off를 한 장에 묶어 초보자 실수를 줄이는 primer
- [Map Value-Shape Drill](./java/map-value-shape-drill.md) - `Map<K,V>`에서 key는 정했는데 value를 `단일값`/`리스트`/`집계객체` 중 무엇으로 둘지 막히는 초보자를 위해, 요구 문장을 value 모양으로 번역하는 후속 미니 드릴
- [`LinkedHashSet` 순서 유지 vs `TreeSet` 정렬 유지 브리지](./java/linkedhashset-order-dedup-mini-bridge.md) - `중복 제거 + 순서` 요구를 볼 때 `입력 순서 유지`와 `정렬 유지`를 분리해 읽게 만들고, "`HashSet`인데 왜 중복이 남지?" 같은 follow-up을 `equals()`/`hashCode()` 기준으로 바로 연결해 주는 beginner bridge
- [Collection vs Collections vs Arrays 유틸리티 미니 브리지](./java/collection-vs-collections-vs-arrays-utility-mini-bridge.md) - 컬렉션 입문 다음에 가장 많이 섞어 쓰는 `Collection` API, `Collections` helper, `Arrays` helper를 5가지 공통 작업으로 빠르게 구분하는 beginner bridge
- [`Arrays.asList()` 고정 크기 리스트 함정 체크리스트](./java/arrays-aslist-fixed-size-list-checklist.md) - `Arrays.asList(...)`에서 `add/remove`가 왜 실패하는지, `new ArrayList<>(...)`와 `List.of(...)`를 언제 고를지 1페이지로 잇는 beginner checklist
- [`Map.of` vs `Map.copyOf` vs `Collections.unmodifiableMap` 읽기 전용 브리지](./java/map-of-copyof-unmodifiablemap-readonly-bridge.md) - `읽기 전용`이라는 말만 보고 셋을 같은 것으로 오해하지 않도록, 상수 맵 / 복사본 / 원본 뷰 차이를 짧은 표와 예제로 정리한 beginner bridge
- [Iterable vs Collection vs Map 브리지 입문](./java/iterable-collection-map-iteration-bridge.md) - 컬렉션 입문 다음 단계에서 `Iterable`/`Collection`/`Map` 계층과 반복 API (`for-each`, `entrySet`)를 혼동 없이 이어 주는 beginner bridge
- [Map Iteration Patterns Cheat Sheet](./java/map-iteration-patterns-cheat-sheet.md) - `entrySet()`/`keySet()`/`values()` 선택을 10초 표와 Do/Don't 예시로 묶어, 초보자의 비효율적인 `keySet()+get()` 습관을 빠르게 교정하는 1페이지 primer
- [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./java/map-put-get-remove-containskey-return-cheat-sheet.md) - `Map`의 대표 메서드 4개가 각각 이전 값/현재 값/삭제된 값/존재 여부를 돌려준다는 점을 한 표와 한 예제로 묶어, beginner가 반환값을 성공 신호로 오해하는 실수를 줄이는 미니 카드
- [Map 조회/갱신 API 미니 브리지: `put()` vs `putIfAbsent()` vs `computeIfAbsent()` vs `merge()`](./java/map-put-putifabsent-computeifabsent-merge-overwrite-bridge.md) - `Map` 갱신 API 네 개를 "값이 있으면 덮어쓰나, 없을 때만 채우나, 기존 값과 합치나" 축으로 묶고, `Map<K, List<V>>` 누적에서 `computeIfAbsent(...).add(...)`를 왜 쓰는지까지 초보자 관점으로 연결하는 beginner bridge
- [Map 값 변환 프라이머: `replaceAll()` vs `entrySet()` 수정 vs 새 맵 만들기](./java/map-entry-setvalue-vs-put-remove-structural-change-bridge.md) - `Map`을 돌며 value를 바꿔야 할 때 `replaceAll()`을 기본값으로 잡고, 조건부 수정은 `entrySet().setValue(...)`, 원본 보존은 새 맵 만들기로 나누어 초보자용 안전성/가독성 기준을 잡아 주는 primer
- [Map `put()`이 `null`을 돌려줄 때: 새 key vs 기존 `null` value 구분 브리지](./java/map-put-null-containskey-distinction-bridge.md) - `put() == null`을 곧바로 "새 key"로 읽는 beginner 혼동을 줄이기 위해, `containsKey()`를 저장 전에 함께 보는 패턴을 짧은 표와 예제로 정리한 bridge
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./java/map-get-null-containskey-getordefault-primer.md) - `Optional.empty()`와 빈 컬렉션 다음 단계에서 `Map.get()`의 `null`이 왜 다시 애매해지는지부터 연결하고, "key 없음" vs "value가 null" 분기와 `containsKey()`/`getOrDefault()` 선택을 짧은 표와 예제로 묶는 beginner primer
- [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./java/hashmap-hashset-hashcode-equals-lookup-bridge.md) - `equals()`/`hashCode()` 입문 다음 단계에서, `HashMap`/`HashSet`이 `hashCode()`로 후보 bucket을 찾고 `equals()`로 마지막 확인을 한다는 lookup 흐름을 한 장으로 이어 주는 beginner bridge
- [HashSet Mutable Element Removal Drill](./java/hashset-mutable-element-removal-drill.md) - `equals()`/`hashCode()` 기준 필드를 바꾼 뒤 `contains()`와 `remove()`가 왜 함께 실패하는지 bucket lookup 관점으로 바로 손예측하게 만드는 beginner drill
- [Map null 허용 여부 구현체 브리지: `HashMap` vs `Hashtable` vs `ConcurrentHashMap` vs `Map.of`](./java/map-null-policy-hashmap-hashtable-concurrenthashmap-mapof-bridge.md) - `HashMap`은 왜 `null`을 받고 `ConcurrentHashMap`과 `Map.of(...)`는 왜 막는지, `get() == null` 해석 차이까지 초보자용 비교표로 바로 이어 주는 beginner bridge
- [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./java/map-lookup-debug-equals-hashcode-compareto-mini-bridge.md) - 조회 실패가 나오면 먼저 `HashMap` 계열과 `TreeMap` 계열을 나누고, `equals()`/`hashCode()` vs `compareTo()` 확인 순서를 10초 표와 짧은 예제로 잡아 주는 beginner debug bridge
- [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./java/treemap-record-containskey-get-name-comparator-drill.md) - `record Student(id, name)`와 name-only comparator에서 `containsKey(new Student(99, "Mina"))`가 왜 `true`인지 조회만 분리해 손예측하는 1페이지 drill
- [Map 구현체별 반복 순서 치트시트](./java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md) - `HashMap`/`LinkedHashMap`/`TreeMap`의 순서 미보장, 삽입 순서, access-order 기반 LRU 느낌 예제, key 정렬 순서를 한 표와 짧은 예제로 비교해 beginner의 출력 순서 오해를 줄이는 primer
- [Map 구현체 선택 미니 드릴](./java/map-implementation-selection-mini-drill.md) - 짧은 요구 문장을 `순서 없음`/`삽입 순서`/`key 정렬` 신호로 번역해 `HashMap`/`LinkedHashMap`/`TreeMap` 첫 선택을 손으로 분류하게 만드는 1페이지 beginner worksheet
- [Map 수정 중 순회 안전 가이드](./java/map-remove-during-iteration-safety-primer.md) - `for-each` 안의 `map.remove(...)`가 왜 깨지는지, `Iterator.remove()`/`removeIf(...)`를 언제 쓰는지, `ConcurrentModificationException`을 멀티스레드 문제로만 오해하지 않도록 Do/Don't 중심으로 정리한 beginner primer
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./java/submap-boundaries-primer.md) - `TreeSet`/`TreeMap` range API를 "정렬된 줄의 구간 창"으로 읽게 만들고, `head = 끝 제외`, `tail = 시작 포함`, `sub = [from, to)`를 짧은 표와 예제로 고정하는 beginner primer
- [`lower` vs `floor` Exact Match 미니 드릴](./java/lower-vs-floor-exact-match-mini-drill.md) - `TreeSet`/`TreeMap`에서 exact match일 때만 `lower`와 `floor`가 갈라진다는 점을 짧은 표와 손예측 문제로 분리해, ordered-map 초급 혼동을 빠르게 줄이는 1페이지 drill
- [Java Optional 입문](./java/java-optional-basics.md) - 처음 배우는데 `Optional`을 언제 쓰는지, `null`과 차이, `orElse`/`orElseGet` 선택 기준, `get()` 남용을 피하는 기초를 정리한 primer
- [Primitive-wrapper choice primer: `int`/`long`/`boolean` vs `Integer`/`Long`/`Boolean`](./java/primitive-wrapper-choice-primer.md) - 필드, 파라미터, 반환값에서 "값이 반드시 있다"와 "`null`도 상태다"를 어떻게 나눌지 한 표와 update DTO 예제로 먼저 잡아 주는 beginner primer
- [`Optional` 필드/파라미터 anti-pattern 30초 카드](./java/optional-field-parameter-antipattern-card.md) - `Optional`을 필드나 파라미터에 둘 때 생기는 이중 상태와 호출 복잡도를 짧은 판단표로 정리하고, plain 값/오버로딩/빈 컬렉션/상태 타입 대안을 바로 이어 주는 beginner card
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./java/optional-collections-domain-null-handling-bridge.md) - 단건의 없음은 `Optional`, 다건의 0개는 빈 컬렉션, key 조회의 애매한 없음은 `Map` null-vs-missing으로 이어지고, 없음의 이유가 중요해지면 `enum`/도메인 타입으로 올린다는 판단 기준을 짧은 표와 예제로 잇는 beginner bridge
- [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./java/domain-state-type-primer-enum-record-value-object.md) - `true/false`와 `null`이 도메인 의미를 숨기기 시작할 때, 상태 이름은 `enum`, 값 묶음은 `record`, 규칙까지 가진 값은 값 객체로 올리는 기준을 초급자용 표와 예제로 정리한 primer
- [Java 스레드와 동기화 기초](./java/java-thread-basics.md)
- [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md)
- [Java 동시성 유틸리티](./java/java-concurrency-utilities.md)
- [ClassLoader, Exception 경계, 객체 계약](./java/classloader-exception-boundaries-object-contracts.md)
- [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./java/optional-stream-immutable-collections-memory-leak-patterns.md)

### Java deep dive catalog

긴 목록은 아래 네 bucket으로 쪼개서 찾기 쉽게 유지한다.
mixed catalog에서 `[playbook]` 라벨은 step-oriented diagnostics / troubleshooting entrypoint라는 뜻이고, 라벨이 없는 항목은 개념/경계 중심 `deep dive`다.

#### Java Runtime and Diagnostics

- [G1 GC vs ZGC](./java/g1-vs-zgc.md)
- [JIT Warmup and Deoptimization](./java/jit-warmup-deoptimization.md)
- `[playbook]` [JFR, JMC Performance Playbook](./java/jfr-jmc-performance-playbook.md)
- [JFR Event Interpretation](./java/jfr-event-interpretation.md)
- [Thread Dump State Interpretation](./java/thread-dump-state-interpretation.md)
- [`jcmd` Diagnostic Command Cheat Sheet](./java/jcmd-diagnostic-command-cheatsheet.md)
- [Async-profiler vs JFR](./java/async-profiler-vs-jfr-comparison.md)
- [Safepoint and Stop-the-World Diagnostics](./java/safepoint-stop-the-world-diagnostics.md)
- [Safepoint Polling Mechanics](./java/safepoint-polling-mechanics.md)
- `[playbook]` [OOM Heap Dump Playbook](./java/oom-heap-dump-playbook.md)
- [Direct Buffer, Off-Heap, Native Memory Troubleshooting](./java/direct-buffer-offheap-memory-troubleshooting.md)
- `[playbook]` [ClassLoader Memory Leak Playbook](./java/classloader-memory-leak-playbook.md)
- [Java Binary Compatibility and Runtime Linkage Errors](./java/java-binary-compatibility-linkage-errors.md)
- [Escape Analysis, Stack Allocation, Benchmarking, and Object Reuse Misconceptions](./java/escape-analysis-stack-allocation-benchmark-misconceptions.md)
- [Java Collections 성능 감각](./java/collections-performance.md)

#### Java Concurrency and Async

긴 bucket이므로 아래 세 `subcluster` quick link를 먼저 둔다. executor saturation / common pool 공유, cancellation / context handoff, Loom migration / structured fan-out처럼 질문 모양이 갈릴 때 바로 내려가기 위한 entrypoint다.

<a id="java-concurrency-executor--common-pool-cluster"></a>
##### Executor / Common Pool Cluster

executor saturation, `ForkJoinPool` 공유, `CompletableFuture` default executor, scheduler hop, partial fan-in backlog를 같이 따라갈 때 쓰는 subcluster다.

- [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md)
- [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md)
- [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md)
- [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
- [Partial Success Fan-in Patterns](./java/partial-success-fan-in-patterns.md)

<a id="java-concurrency-cancellation--context-propagation-cluster"></a>
##### Cancellation / Context Propagation Cluster

interrupt, cooperative cancellation, `ThreadLocal` leakage, `ScopedValue` handoff, timeout-to-deadline propagation과 async cleanup ownership을 함께 볼 때 쓰는 subcluster다.

- `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md)
- [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)
- [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
- [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md)
- [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md)

<a id="java-concurrency-loom--structured-concurrency-cluster"></a>
##### Loom / Structured Concurrency Cluster

virtual-thread adoption, pinning, `ScopedValue`, structured fan-out, framework boundary, Loom incident signal을 묶어 찾을 때 쓰는 subcluster다.

- [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md)
- [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
- [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md)
- [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md)
- [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md)
- [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md)

- [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./java/inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
- [Java Memory Model, happens-before, volatile, final](./java-memory-model-happens-before-volatile-final.md)
- [VarHandle, Unsafe, Atomics](./java/varhandle-unsafe-atomics.md)
- [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)
- [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./java/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
- `[playbook]` [Thread Interruption and Cooperative Cancellation Playbook](./java/thread-interruption-cooperative-cancellation-playbook.md)
- [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./java/concurrenthashmap-compound-actions-hot-key-contention.md)
- [`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs](./java/concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs.md)
- [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
- [ABA Problem, `AtomicStampedReference`, and `AtomicMarkableReference`](./java/aba-problem-atomicstampedreference-markable-reference.md)
- [`CopyOnWriteArrayList` Snapshot Iteration and Write Amplification](./java/copyonwritearraylist-snapshot-iteration-write-amplification.md)
- [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./java/wait-notify-condition-spurious-wakeup-lost-signal.md)
- [`StampedLock` Optimistic Read and Conversion Pitfalls](./java/stampedlock-optimistic-read-conversion-pitfalls.md)
- [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./java/locksupport-park-unpark-permit-semantics.md)
- [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md)
- [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)
- [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md)
- [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md)
- [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md)
- [`CompletableFuture` `allOf`, `join`, Timeout, and Exception Handling Hazards](./java/completablefuture-allof-join-timeout-exception-handling-hazards.md)
- [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md)
- [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md)
- [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)
- [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md)
- [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md)
- [Idempotency Keys and Safe HTTP Retries](./java/httpclient-idempotency-keys-safe-http-retries.md)
- [Partial Success Fan-in Patterns](./java/partial-success-fan-in-patterns.md)
- [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md)
- [Virtual-Thread MVC Async Executor Boundaries](./java/virtual-thread-mvc-async-executor-boundaries.md)
- [Connection Budget Alignment After Loom](./java/connection-budget-alignment-after-loom.md)
- [Remote Bulkhead Metrics Under Virtual Threads](./java/remote-bulkhead-metrics-under-virtual-threads.md)
- [Virtual-Thread JDBC Cancel Semantics](./java/virtual-thread-jdbc-cancel-semantics.md)
- `[playbook]` [DB-Side Cancel Confirmation Playbook](./java/jdbc-db-side-cancel-confirmation-playbook.md)
- [Spring JDBC Timeout Propagation Boundaries](./java/spring-jdbc-timeout-propagation-boundaries.md)
- [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md)
- [JDBC Observability Under Virtual Threads](./java/jdbc-observability-under-virtual-threads.md)
- [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md)
- [Virtual Thread vs Reactive DB Observability](./java/virtual-thread-vs-reactive-db-observability.md)
- [Servlet `REQUEST` / `ASYNC` / `ERROR` Redispatch Ordering for Filters and Interceptors](./java/servlet-async-redispatch-filter-interceptor-ordering.md)
- [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
- [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md)
- [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./java/streaming-response-abort-surfaces-servlet-virtual-threads.md)
- [JDBC Cursor Cleanup on Download Abort](./java/jdbc-cursor-cleanup-download-abort.md)
- [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
- [SSE `Last-Event-ID`, Replay Window, and Reconnect Ownership With `SseEmitter`](./java/sse-last-event-id-replay-reconnect-ownership.md)
- [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md)

#### Java Serialization and Payload Contracts

- [Primitive vs Wrapper Fields in JSON Payload Semantics](./java/primitive-vs-wrapper-fields-json-payload-semantics.md)
- [Empty String, Blank, `null`, and Missing Payload Semantics](./java/empty-string-blank-null-missing-payload-semantics.md)
- [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./java/floating-point-precision-nan-infinity-serialization-pitfalls.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./java/bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [Java IO, NIO, Serialization, JSON Mapping](./java/io-nio-serialization.md)
- [Charset, UTF-8 BOM, Malformed Input, and Decoder Policy](./java/charset-utf8-bom-malformed-input-decoder-policy.md)
- [Serialization Compatibility, `serialVersionUID`, and Evolution Strategy](./java/serialization-compatibility-serial-version-uid.md)
- [Serialization Proxy Pattern and Invariant Preservation](./java/serialization-proxy-pattern-invariant-preservation.md)
- [`serialPersistentFields`, `readObjectNoData`, and Native Serialization Evolution Escape Hatches](./java/serialpersistentfields-readobjectnodata-evolution-escape-hatches.md)
- [Enum Persistence, JSON, and Unknown Value Evolution](./java/enum-persistence-json-unknown-value-evolution.md)
- [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./java/json-null-missing-unknown-field-schema-evolution.md)
- [Record Serialization Evolution](./java/record-serialization-evolution.md)
- [Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility](./java/record-sealed-hierarchy-evolution-pattern-matching-compatibility.md)

#### Java Language and Boundary Design

- [Value Object Invariants, Canonicalization, and Boundary Design](./java/value-object-invariants-canonicalization-boundary-design.md)
- [생성자에서 값 객체 팩터리로 넘어가는 첫 브리지](./java/constructor-to-value-object-factory-bridge.md) - beginner가 `constructor vs of/from`, raw input 정규화, 값 객체 entrypoint naming을 한 장에서 고르는 입구
- [Java Equality and Identity Basics](./java/java-equality-identity-basics.md) - `==` vs `equals()`, 같은 객체 vs 같은 값, `hashCode()`가 왜 `HashSet`/`HashMap`과 같이 따라오는지 처음 질문에 바로 답하는 entrypoint primer
- [HashSet vs TreeSet Duplicate Semantics](./java/hashset-vs-treeset-duplicate-semantics.md)
- [Natural Ordering in TreeSet and TreeMap](./java/treeset-treemap-natural-ordering-compareto-bridge.md)
- [TreeMap `put` 반환값 브리지: `null` vs 이전 값](./java/treemap-put-return-value-overwrite-bridge.md) - 초급자가 `compare == 0`과 `put`의 이전 값 반환/덮어쓰기/`size()` 유지까지 한 번에 연결해 읽도록 정리한 bridge
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./java/bigdecimal-sorted-collection-bridge.md) - `equals()` 기준 hash 계열과 `compareTo()` 기준 sorted 계열 갈림 + 도메인 같음 기준 선택 흐름을 함께 보여 주는 bridge
- [BigDecimal 생성 정책 입문 브리지](./java/bigdecimal-construction-policy-beginner-bridge.md) - `new BigDecimal(double)`을 기본 선택지에서 빼고, 문자열 생성자와 `BigDecimal.valueOf(...)`를 입력 경계 기준으로 고르는 beginner bridge
- [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./java/bigdecimal-setscale-unnecessary-validation-primer.md) - `setScale(..., UNNECESSARY)`를 반올림 트릭이 아니라 "반올림 없이 정해진 소수 자릿수 안에 들어와야 통과"라는 입력 검증 정책으로 설명하는 beginner primer
- [BigDecimal Key 정책 30초 체크리스트](./java/bigdecimal-key-policy-30-second-checklist.md) - `1.0` vs `1` 동등성 정책, map key 정규화 위치, 조회/중복/정규화 테스트 최소 세트를 PR 전 체크리스트로 묶은 beginner primer
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./java/bigdecimal-striptrailingzeros-input-boundary-bridge.md) - `stripTrailingZeros`를 고급 함정 전에 입력 정규화 정책, `setScale`/출력 정책과의 차이, 체크리스트 관점으로 먼저 붙이는 beginner bridge
- [BigDecimal 출력 정책 미니 브리지: `toString()` vs `toPlainString()`](./java/bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge.md) - 로그/JSON/UI에서 사람이 읽는 문자열과 serializer 계약을 분리해, 지수 표기 혼동을 줄이는 beginner bridge
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./java/bigdecimal-1-0-vs-1-00-collections-mini-drill.md) - `BigDecimal` 전용으로 `HashSet`/`TreeSet`/`TreeMap` 결과를 짧게 손예측하는 beginner worksheet
- [BigDecimal Comparator Tie-Breaker 미니 드릴](./java/bigdecimal-comparator-tie-breaker-mini-drill.md) - `1.0`과 `1.00`을 sorted collection에서 둘 다 남기고 싶을 때 `compareTo()` 뒤에 `scale()` tie-breaker를 왜 붙이는지 손예측과 조회 예제로 묶은 beginner drill
- [BigDecimal 조회 전용 미니 드릴: `contains` in `HashSet` vs `TreeSet`](./java/bigdecimal-hashset-treeset-contains-mini-drill.md) - `add("1.0")` 뒤 `contains("1")`와 `contains("1.00")`가 왜 `HashSet`과 `TreeSet`에서 갈리는지 조회 기준만 따로 고정하는 1페이지 drill
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./java/bigdecimal-hashmap-treemap-lookup-mini-drill.md) - `put("1.0")` 뒤 `containsKey/get("1")`가 `HashMap`과 `TreeMap`에서 왜 갈리는지 조회만 분리해 손예측하는 1페이지 drill
- [Record-Comparator 60초 미니 드릴](./java/record-comparator-60-second-mini-drill.md) - `record Student(id, name)`와 name-only comparator를 함께 두고 `HashSet`/`TreeSet`/`TreeMap` 결과를 60초 안에 예측한 뒤, `thenComparingLong(Student::id)` 하나로 collapse가 separation으로 바뀌는 후속 비교까지 보는 beginner worksheet
- [TreeMap 조회 전용 미니 드릴: `containsKey()` / `get()` with `record` key and name-only comparator](./java/treemap-record-containskey-get-name-comparator-drill.md) - `TreeMap` 조회만 따로 떼어 `new Student(99, "Mina")`가 왜 같은 key 자리로 보이는지 확인하는 beginner follow-up worksheet
- [Comparator in TreeSet and TreeMap](./java/treeset-treemap-comparator-tie-breaker-basics.md) - name-only comparator가 언제 의도된 collapse이고, 언제 `thenComparingLong(...id)`가 필요한지 sorted collection 기준으로 설명하는 beginner primer
- [Comparator Consistency With `equals()` Bridge](./java/comparator-consistency-with-equals-bridge.md) - `HashSet`의 `equals()` 기준과 `TreeSet`/`TreeMap`의 `compare(...) == 0` 기준이 왜 갈리는지, 같은 `record` 예제로 바로 비교하는 beginner bridge
- [Comparator 변수명 짓기 초급 패턴](./java/comparator-variable-naming-beginner-primer.md) - `byName`, `byScoreDescThenName`처럼 comparator 이름에 기준과 방향을 담아 정렬 의도와 재사용성을 더 잘 읽히게 만드는 beginner primer
- [Record and Value Object Equality](./java/record-value-object-equality-basics.md) - value object vs entity 경계, 배열/가변 컬렉션 component FAQ, `record equals` vs comparator confusion 표를 묶은 primer
- [Record component로 `BigDecimal`을 써도 되나요?](./java/record-bigdecimal-component-faq.md) - `record Price(BigDecimal amount)`에서 `1.0` vs `1.00`, canonicalization, hash/sorted 컬렉션 기준 차이를 바로 확인하는 beginner FAQ primer
- [Java 배열 입문 공통 confusion 체크리스트](./java/java-array-common-confusion-checklist.md) - 배열 입문 문서들을 다시 열 때 먼저 `출력/비교/공유/정렬`로 갈라 `==`, alias, 제자리 정렬 혼동을 줄이는 1페이지 beginner entrypoint
- [Java Array Equality Basics](./java/java-array-equality-basics.md) - "값 비교가 막혔나?"를 먼저 확인할 때: 배열 비교 기준(`==`/`equals`/`Arrays.equals`/`Arrays.deepEquals`)을 초급 관점으로 정리한 bridge
- [Java Array Debug Printing Basics](./java/java-array-debug-printing-basics.md) - "출력부터 막혔나?"를 먼저 확인할 때: 배열 출력과 equality/copy 분기 기준을 한 장으로 정리한 beginner bridge
- [Java Array Copy and Clone Basics](./java/java-array-copy-clone-basics.md) - "복사 분리가 막혔나?"를 먼저 확인할 때: 배열 대입/`clone`/`copyOf`와 shallow/deep copy를 연결하는 beginner bridge
- [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md) - "정렬-검색 전제가 막혔나?"를 먼저 확인할 때: beginner array 정렬/검색에서 comparator chain 다음 단계로 넘어가는 bridge
- [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](./java/arrays-sort-binarysearch-precondition-bridge.md) - "왜 결과가 이상해요?"를 물을 때 정렬 기준과 검색 기준 mismatch부터 빠르게 확인하는 entry
- [BinarySearch Duplicate Boundary Primer](./java/binarysearch-duplicate-boundary-primer.md) - 정렬은 맞는데 첫/마지막 위치가 막힐 때 좌우 확장 패턴으로 이어 주는 follow-up
- [BinarySearch With Nullable Wrapper Sort Keys](./java/binarysearch-nullable-wrapper-sort-keys.md)
- [equals, hashCode, Comparable 계약](./java-equals-hashcode-comparable-contracts.md)
- [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./java/autoboxing-integercache-null-unboxing-pitfalls.md)
- [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
- [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./java/biginteger-unsigned-parsing-boundaries.md)
- [`BigInteger` Parser Radix, Leading Zero, Sign, and Boundary Contracts](./java/biginteger-radix-leading-zero-sign-policies.md)
- [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./java/parser-overflow-boundaries-parseint-parselong-tointexact.md)
- [Saturating Arithmetic, Clamping, and Domain Contracts](./java/saturating-arithmetic-clamping-domain-contracts.md)
- [`BigDecimal` `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
- [Reflection, Generics, Annotations](./java/reflection-generics-annotations.md)
- [Generic Type Erasure Workarounds](./java/generic-type-erasure-workarounds.md)
- [Reflection 비용과 대안](./java/reflection-cost-and-alternatives.md)
- [Records, Sealed Classes, Pattern Matching](./java/records-sealed-pattern-matching.md)
- [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](./java/java-time-instant-localdatetime-boundaries.md)
- [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./java/locale-root-case-mapping-unicode-normalization.md)
- [Annotation Processing](./java/annotation-processing.md)

### 교차 카테고리 브리지

- 이벤트 계약 진화와 replay 호환성은 [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./java/json-null-missing-unknown-field-schema-evolution.md), [Design Pattern: Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md), [System Design: Historical Backfill / Replay Platform](../system-design/historical-backfill-replay-platform-design.md)을 묶어 보면 좋다.
- Java 배열 정렬/검색에서 알고리즘 이분 탐색으로 넘어갈 때는 [Sorting and Searching Arrays Basics](./java/java-array-sorting-searching-basics.md) -> [`Arrays.sort(...)` 뒤 `binarySearch(...)` 전제 브리지](./java/arrays-sort-binarysearch-precondition-bridge.md) -> [이분 탐색 입문](../algorithm/binary-search-intro.md) -> [이분 탐색 패턴](../algorithm/binary-search-patterns.md) 순서가 beginner에게 가장 안전하다. "`정렬은 했는데 왜 검색 결과가 이상해요?`", "`처음 이분 탐색 뭐부터 봐요?`" 같은 질문을 Java 라이브러리 전제와 알고리즘 경계로 나눠서 올려 보낼 수 있다.
- 객체 계약과 경계 설계는 [ClassLoader, Exception 경계, 객체 계약](./java/classloader-exception-boundaries-object-contracts.md), [Design Pattern: Repository Boundary: Aggregate Persistence vs Read Model](../design-pattern/repository-boundary-aggregate-vs-read-model.md), [Database: Transaction Boundary, Isolation, and Locking Decision Framework](../database/transaction-boundary-isolation-locking-decision-framework.md)으로 이어 보면 더 선명하다.
- JVM/동시성 감각은 [JVM, GC, JMM](./java/jvm-gc-jmm-overview.md), [Java 동시성 유틸리티](./java/java-concurrency-utilities.md), `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)의 장애 해석 감각과도 연결된다.
- 숫자 parsing/canonicalization 경계는 [`BigInteger` Parser Radix, Leading Zero, Sign, and Boundary Contracts](./java/biginteger-radix-leading-zero-sign-policies.md), [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./java/parser-overflow-boundaries-parseint-parselong-tointexact.md), [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./java/biginteger-unsigned-parsing-boundaries.md), [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)를 함께 보면 `문자열 문법 -> parse -> exact/narrowing -> domain max` 흐름이 한 번에 연결된다.
- 비동기 orchestration 감각은 [ForkJoinPool Work-Stealing](./java/forkjoinpool-work-stealing.md), [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md), [CompletableFuture Execution Model and Common Pool Pitfalls](./java/completablefuture-execution-model-common-pool-pitfalls.md), [CompletableFuture Cancellation Semantics](./java/completablefuture-cancellation-semantics.md), [`CompletableFuture.delayedExecutor`, Scheduler Hop, and Timer-Thread Hazards](./java/completablefuture-delayedexecutor-scheduler-hop-timer-thread-hazards.md), [ThreadLocal Leaks and Context Propagation](./java/threadlocal-leaks-context-propagation.md)를 함께 보면 common pool 공유, timer hop, retry/backoff, cancellation, `CallerRunsPolicy`, context 전파가 한 그림으로 묶인다.
- outbound `POST` retry와 duplicate suppression 감각은 [Idempotency Keys and Safe HTTP Retries](./java/httpclient-idempotency-keys-safe-http-retries.md), [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md), [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md), [멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md), [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md)를 함께 보면 `transport retry 가능성 -> request fingerprint -> dedup window -> response replay` 흐름이 한 번에 연결된다.
- virtual thread 도입 감각은 [Virtual Threads(Project Loom)](./java/virtual-threads-project-loom.md), [Structured Concurrency and `ScopedValue`](./java/structured-concurrency-scopedvalue.md), [Structured Fan-out With `HttpClient`](./java/structured-fanout-httpclient.md), [Remote Bulkhead Metrics Under Virtual Threads](./java/remote-bulkhead-metrics-under-virtual-threads.md), [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./java/virtual-thread-spring-jdbc-httpclient-framework-integration.md), [Virtual-Thread MVC Async Executor Boundaries](./java/virtual-thread-mvc-async-executor-boundaries.md), [Virtual-Thread JDBC Cancel Semantics](./java/virtual-thread-jdbc-cancel-semantics.md), [JFR Loom Incident Signal Map](./java/jfr-loom-incident-signal-map.md), [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md), [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./java/servlet-async-timeout-downstream-deadline-propagation.md), [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./java/servlet-asynclistener-cleanup-patterns.md), [Spring `@Transactional` and `@Async` Composition Traps](../spring/spring-transactional-async-composition-traps.md), [Spring `@Async` Context Propagation and RestClient / HTTP Interface Clients](../spring/spring-async-context-propagation-restclient-http-interface-clients.md)를 함께 보면 request thread, MVC async executor, direct emitter producer, servlet request lifetime, detached task, structured task scope, transaction `ThreadLocal`, async timeout을 parent deadline으로 삼는 방법, outbound HTTP cancel ownership, JDBC query cancel ownership, remote fan-out budget과 permit contention 관측이 같은 경계 문제로 묶인다.
- 스트리밍 abort와 late write failure 해석은 [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./java/streaming-response-abort-surfaces-servlet-virtual-threads.md), [JDBC Cursor Cleanup on Download Abort](./java/jdbc-cursor-cleanup-download-abort.md), [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md), [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md), [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md), [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)을 함께 보면 `first byte commit -> 다음 write/flush에서 disconnect 관측 -> fetch-size cursor ownership -> statement cancel/rollback -> late write suppression` 흐름이 한 번에 연결된다.
- SSE resume/reconnect ownership 감각은 [SSE `Last-Event-ID`, Replay Window, and Reconnect Ownership With `SseEmitter`](./java/sse-last-event-id-replay-reconnect-ownership.md), [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](../spring/spring-sse-replay-buffer-last-event-id-recovery-patterns.md), [Spring SSE Disconnect Observability Patterns](../spring/spring-sse-disconnect-observability-patterns.md), [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)을 함께 보면 `logical stream cursor -> replay window -> high-water-mark handoff -> reconnect storm -> old emitter cleanup ownership` 흐름이 한 번에 연결된다.
- virtual thread 이후 JDBC 병목 관측은 [JDBC Observability Under Virtual Threads](./java/jdbc-observability-under-virtual-threads.md), [JDBC `setNetworkTimeout`, Driver `socketTimeout`, and Pool Eviction Under Virtual Threads](./java/jdbc-network-timeout-driver-socket-timeout-pool-eviction.md), [HikariCP 튜닝](../database/hikari-connection-pool-tuning.md), `[playbook]` [Lock Wait, Deadlock, and Latch Contention Triage Playbook](../database/lock-wait-deadlock-latch-triage-playbook.md)를 함께 보면 `pool wait -> stuck socket/read -> connection churn -> DB lock wait` 흐름까지 한 번에 연결된다.
- virtual thread JDBC와 reactive DB의 장애 해석 차이는 [Virtual Thread vs Reactive DB Observability](./java/virtual-thread-vs-reactive-db-observability.md), [Spring WebFlux vs MVC](../spring/spring-webflux-vs-mvc.md), [Spring Reactive-Blocking Bridge: `block()`, `boundedElastic`, and Boundary Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)를 함께 보면 `thread timeline vs signal timeline`, `pool wait vs operator backlog`, `caller 예외 vs stream cancel` 차이가 한 그림으로 연결된다.
- 큐 포화와 handoff 계약은 [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md), [Executor Sizing, Queue, Rejection Policy](./java/executor-sizing-queue-rejection-policy.md), [Bounded MPMC Queue](../data-structure/bounded-mpmc-queue.md)를 함께 보면 `offer`/`put`/`transfer`, `SynchronousQueue`, bounded ring backpressure가 같은 축으로 연결된다.
- 상속을 처음 배우는데 "언제 쓰는지"나 `hook method`/`abstract step` 큰 그림이 막히면 먼저 `객체지향 큰 그림 -> 상속 언제 쓰는지 -> 추상 클래스/인터페이스 -> 상속보다 조합 -> 템플릿 메소드 패턴 기초 -> 템플릿 메소드 vs 전략` route를 [Java 타입, 클래스, 객체, OOP 입문](./java/java-types-class-object-oop-basics.md) -> [객체지향 핵심 원리](./java/object-oriented-core-principles.md) -> [Java 상속과 오버라이딩 기초](./java/java-inheritance-overriding-basics.md) -> [추상 클래스 vs 인터페이스 입문](./java/java-abstract-class-vs-interface-basics.md) -> [상속보다 조합 기초](../design-pattern/composition-over-inheritance-basics.md) -> [템플릿 메소드 패턴 기초](../design-pattern/template-method-basics.md) -> [템플릿 메소드 vs 전략](../design-pattern/template-method-vs-strategy.md) 순서로 잡으면 beginner 첫 읽기 동선이 흔들리지 않는다. 그다음 [객체지향 설계 기초](../software-engineering/oop-design-basics.md), [객체지향 디자인 패턴 기초](../design-pattern/object-oriented-design-pattern-basics.md)으로 넓히면 문법 질문이 설계 선택 질문으로 자연스럽게 이어진다. 초급 golden query는 `처음 배우는데 상속 언제 쓰는지`, `기초 상속 vs 조합`, `추상 클래스 인터페이스 다음 뭐 읽지`, `템플릿 메소드 언제 쓰는지`처럼 conversational phrasing으로도 이 same beginner handoff 체인을 먼저 잡도록 유지한다.

## C++ primer

이 구간은 C++ 기초/중급 `primer` entrypoint다. 세부 구현 trade-off는 다른 카테고리 deep dive와 함께 확장해서 읽는 편이 좋다.

- [C++ STL](./c++/STL.md)
- [Modern C++](./c++/moderncpp.md)
- [멀티스레드 프로그래밍](./c++/multithread-programming.md)
