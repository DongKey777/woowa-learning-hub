# Java Deep Dive Catalog

**난이도: 🔴 Advanced**

> 이 README는 `knowledge/cs/contents/language/java/` 하위 문서의 Java 세부 navigator다.
> beginner가 `List`/`Set`/`Map`/`Queue`에서 막혔을 때는 아래의 컬렉션 빠른 탐색부터 보고, 더 큰 학습 순서는 [language 카테고리 인덱스](../README.md)로 돌아간다.

## 시작점 한 줄 분기

- "`같은 객체예요, 같은 값이에요?`, `String 같은데 왜 false예요`처럼 같은 객체 vs 같은 값 증상부터 막히면" [Java Equality and Identity Basics](./java-equality-identity-basics.md)에서 `==`/`equals()` route를 먼저 탄다

## 컬렉션 빠른 탐색

- "`List`/`Set`/`Map` 큰 그림이 아직 헷갈린다"면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- "`요구 문장을 보고 List/Set/Map 중 무엇을 골라야 할지`부터 막힌다"면 [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- "`HashMap`/`LinkedHashMap`/`TreeMap` 중 무엇을 먼저 골라야 하는지`가 헷갈린다"면 [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- "`Map.get()`이 `null`인데 key가 없는 건지 value가 `null`인 건지`부터 헷갈린다"면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- "`조회만 했는데 순서가 바뀐다`와 `정렬된 key 범위 조회`를 자꾸 같은 문제로 읽는다"면 [LinkedHashMap access-order vs TreeMap navigable API 미니 드릴](./linkedhashmap-access-order-vs-treemap-navigable-mini-drill.md)
- "`Set`에서 중복 제거와 순서 유지가 같이 필요하다"면 [`LinkedHashSet` 순서 유지 vs `TreeSet` 정렬 유지 브리지](./linkedhashset-order-dedup-mini-bridge.md)
- "`queue`가 컬렉션인지, 알고리즘 도구인지, 서비스 handoff 도구인지`가 헷갈린다"면 [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md)

## beginner-safe bridge ladder

이 README는 deep dive catalog지만, 아래 세 문장은 beginner가 자주 여기까지 바로 뛰어와서 막히는 지점이다. 이때는 advanced doc을 더 내려가지 말고 primer 사다리로 한 칸만 내려가면 된다.

| 지금 보이는 증상 문장 | 여기서 첫 클릭 | 안전한 다음 한 걸음 | deep dive로 다시 올라오는 시점 |
|---|---|---|---|
| `처음이라 List/Set/Map부터 다시 잡고 싶어요`, `what is java collections basics` | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) | `lookup / dedupe / FIFO`를 말할 수 있을 때 |
| `queue가 왜 컬렉션에도 나오고 BFS에도 나와요`, `왜 service 코드에도 queue가 있죠?` | [Backend Data-Structure Starter Pack](../../data-structure/backend-data-structure-starter-pack.md) | `최소 이동`이면 [Backend Algorithm Starter Pack](../../algorithm/backend-algorithm-starter-pack.md), `worker 순서`면 [Service 계층 기초](../../software-engineering/service-layer-basics.md) | `queue`가 도구인지 handoff인지 한 줄로 구분할 수 있을 때 |
| `TreeMap`, `ordered map`, `floor/ceiling`을 바로 읽으려니 너무 점프 같아요` | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) | [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md) | `정렬/범위 조회`가 실제 요구라고 말할 수 있을 때 |

짧게 외우면 `Java 컬렉션 primer -> 자료구조 starter -> 알고리즘 또는 Service primer -> Java deep dive` 순서다.

## Map null -> TreeMap -> ordered map 빠른 경로

- "`Map`에서 왜 `null`이 나오는지`부터 정리하고 싶다"면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- "`null` 해석을 한 뒤 `HashMap`과 `TreeMap`이 언제 갈리는지`를 바로 붙이고 싶다"면 [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)
- "`TreeMap`은 왜 `null` key를 막는데 comparator로 `null` 필드는 정렬되나요?`처럼 ordered map 들어가기 직전의 `null` 질문이 남아 있다"면 [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- "`TreeMap`을 ordered map으로 읽으면서 `floor`/`ceiling`이 왜 `null`이 되는지`까지 이어 가고 싶다"면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)

## Ordered Map / Set follow-up

- "`floor`/`ceiling`/`lower`/`higher`가 자꾸 섞인다"면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- "`ordered map에서 왜 null이 나오는지`를 경계 예제로 먼저 붙이고 싶다"면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- "`exact match인데 ceiling은 자기 자신이고 higher는 왜 다음 key로 가죠?`가 헷갈린다"면 [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- "`subMap`/`headMap` 경계 포함 여부가 헷갈린다"면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- "`HashMap`과 `TreeMap`의 조회/덮어쓰기 기준 차이`를 더 짧게 다시 보고 싶다"면 [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)

## DTO / 값 객체 경계 빠른 탐색

- "`DTO에서 값 객체로 올릴지부터 헷갈려요`, `request DTO의 String을 service까지 그대로 넘겨도 되나요?`처럼 beginner 경계 질문이 먼저 나오면" [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)으로 바로 들어간다
- "`PATCH`에서 필드가 안 온 것과 `null`을 보낸 것을 왜 다르게 읽는지`부터 막힌다"면 [PATCH DTO에서 `missing` / `null` / 값 있음 을 구분하는 첫 입문](./patch-tri-state-field-primer.md)
- "`값 객체로 올리면 equals/hashCode, Set key 판단이 왜 같이 쉬워지는지`를 먼저 묶고 싶다"면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- "`돈`, `이메일`, `상품코드`처럼 규칙 있는 값을 언제 작은 타입으로 감싸야 하는지`가 궁금하다"면 [Money Value Object Basics](./money-value-object-basics.md)
- "`enum`, `record`, 값 객체 중 무엇을 먼저 고를지`가 막힌다"면 [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)

## 복귀 경로

- Java primer 묶음 전체로 돌아가려면 [language 카테고리 인덱스](../README.md#java-primer)
- 자료구조 관점으로 다시 번역하고 싶다면 [data-structure 카테고리 인덱스](../../data-structure/README.md)
