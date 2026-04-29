# Java Deep Dive Catalog

**난이도: 🔴 Advanced**

> 이 README는 `knowledge/cs/contents/language/java/` 하위 문서의 Java 세부 navigator다.
> beginner가 `List`/`Set`/`Map`/`Queue`에서 막혔을 때는 아래의 컬렉션 빠른 탐색부터 보고, 더 큰 학습 순서는 [language 카테고리 인덱스](../README.md)로 돌아간다.

> retrieval-anchor-keywords: java collections readme, java equality readme, java collection hierarchy readme, list set map route, equals hashcode route, same object same value java, hashset duplicate why, hashset 왜 하나로 보여요, hashset size 1 왜, hashmap get null why, map get이 왜 null이죠, 넣었는데 get이 null, map is not collection java, list set map 처음, equals hashcode 처음, java collections equality entrypoint

## Collections / Equality quick return

컬렉션 README를 찾으러 왔는데 실제로는 `==`/`equals()`나 `HashSet`/`HashMap` 규칙에서 막히는 경우가 많다. 특히 "`HashSet` 왜 하나로 보여요", "`Map get`이 왜 `null`이죠" 같은 질문은 컬렉션 이름보다 먼저 equality와 key 규칙을 같이 봐야 빨리 풀린다. 아래 entrypoint는 그 증상을 `equality -> hash collection -> map lookup` 순서로 짧게 route하기 위한 것이다.

| 지금 먼저 보이는 증상 | 첫 클릭 | 다음 한 칸 | 여기서 먼저 고정할 한 문장 |
|---|---|---|---|
| `처음이라 List/Set/Map hierarchy부터 다시 보고 싶어요`, `Map도 Collection인가요?` | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) | `List`와 `Set`은 `Collection` 쪽이고 `Map`은 key-value 사전이라 계층이 따로다 |
| `같은 객체예요, 같은 값이에요?`, `String 같은데 왜 false예요?` | [Java Equality and Identity Basics](./java-equality-identity-basics.md) | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) | 참조형 `==`는 보통 같은 객체 질문이고 `equals()`는 같은 값 질문이다 |
| "`List.remove(1)`이 왜 값 1이 아니라 두 번째 원소를 지우죠?`, `Set.remove()` 실패랑 같은 문제인가요?`" | [`List.indexOf()` / `List.remove()` vs `Set.remove()` 증상 브리지](./list-indexof-remove-vs-set-remove-symptom-bridge.md) | [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md) | `List`는 overload와 `equals()`를 먼저 보고, `Set`은 lookup 규칙과 mutation을 먼저 본다 |
| "`Map<Integer, V>`에서 `get(1)`은 되는데 `remove(1)`이나 `remove(1, value)`는 왜 감각이 다르죠?`" | [`Map<Integer, V>`에서 `get(1)`은 쉬운데 `remove(1)`은 왜 다르게 읽을까](./map-integer-get-remove-two-arg-remove-bridge.md) | [Map `put()` / `get()` / `remove()` / `containsKey()` 반환값 치트시트](./map-put-get-remove-containskey-return-cheat-sheet.md) | `Map`의 `1`은 index가 아니라 key이고, 분기점은 `remove(key)` vs `remove(key, value)` 계약이다 |
| "`Map<Integer, V>`에서 `containsKey(1)` / `get(1)` / `getOrDefault(1, ...)`를 언제 갈라 읽죠?`, `왜 getOrDefault(1, x)가 null이죠?`" | [`Map<Integer, V>`에서 `containsKey(1)` / `get(1)` / `getOrDefault(1, ...)`를 언제 갈라 읽을까](./map-integer-containskey-get-getordefault-bridge.md) | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) | 숫자 `1`은 세 API 모두 key이고, 차이는 index가 아니라 missing key / `null` value / fallback 정책을 어디서 분리하느냐다 |
| "`HashSet`은 왜 하나로 보이죠?", "`HashSet` 왜 하나로 보여요?", "`Set`에 두 개 넣었는데 size가 1이에요`" | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) | [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md) | 해시 컬렉션의 중복/조회 규칙은 `hashCode()`와 `equals()`를 같이 본다 |
| "`HashMap#get(...)`이 왜 null이죠?", "`Map get`이 왜 `null`이죠?", "`넣었는데 다시 못 찾아요`" | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) | `get() == null`은 null value 구분부터 하고, key가 객체면 equality와 mutable key도 같이 본다 |

짧게 외우면 `equality basics -> collections foundations -> hash lookup bridge -> map null/key primer` 순서다.

## `HashSet` 하나로 보임 / `Map.get()` null 빠른 분기

두 증상은 따로 외우기보다 같은 뿌리로 읽는 편이 안전하다.

- "`HashSet`이 왜 하나로 보이지?"가 먼저면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)에서 "`무엇을 같은 값으로 보나`"를 먼저 고정하고, 바로 [`HashMap`/`HashSet` 조회 흐름 브리지: `hashCode()` 다음에 왜 `equals()`를 볼까](./hashmap-hashset-hashcode-equals-lookup-bridge.md)로 내려간다.
- "`Map.get()`이 왜 null이지?"가 먼저면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)에서 "`같은 key로 다시 찾을 수 있나`"를 먼저 붙인 뒤, [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)로 가서 `null value`와 `key 없음`을 분리한다.
- "`Map.get()`이 null이고 key도 객체라서 더 수상하다"면 primer 다음 칸으로 [Map 조회 디버깅 미니 브리지: `containsKey() == false` / `get() == null` 다음 순서](./map-lookup-debug-equals-hashcode-compareto-mini-bridge.md)를 붙여 `equals()`/`hashCode()`와 mutable key를 확인한다.

한 줄로 줄이면 `HashSet size 1`도, `Map get null`도 해시 컬렉션에서는 결국 "`같은 값/같은 key 규칙이 무엇인가`"를 먼저 묻는 증상이다.

## 시작점 한 줄 분기

- "`같은 객체예요, 같은 값이에요?`, `String 같은데 왜 false예요`처럼 같은 객체 vs 같은 값 증상부터 막히면" [Java Equality and Identity Basics](./java-equality-identity-basics.md)에서 `==`/`equals()` route를 먼저 탄다

## 컬렉션 빠른 탐색

- "`List`/`Set`/`Map` 큰 그림이 아직 헷갈린다"면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- "`요구 문장을 보고 List/Set/Map 중 무엇을 골라야 할지`부터 막힌다"면 [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- "`List.remove(1)`이 왜 인덱스를 지우는지`, `indexOf()`와 `Set.remove()` 실패를 어떻게 갈라 읽는지`가 헷갈린다"면 [`List.indexOf()` / `List.remove()` vs `Set.remove()` 증상 브리지](./list-indexof-remove-vs-set-remove-symptom-bridge.md)
- "`HashMap`/`LinkedHashMap`/`TreeMap` 중 무엇을 먼저 골라야 하는지`가 헷갈린다"면 [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- "`Map<Integer, V>`의 숫자 key 조회는 쉬운데 `remove(1)`과 `remove(1, value)`를 `List.remove(1)`이랑 자꾸 섞는다"면 [`Map<Integer, V>`에서 `get(1)`은 쉬운데 `remove(1)`은 왜 다르게 읽을까](./map-integer-get-remove-two-arg-remove-bridge.md)
- "`Map<Integer, V>`에서 `containsKey(1)` / `get(1)` / `getOrDefault(1, ...)`가 다 비슷해 보여서, missing key와 `null` value, fallback을 자꾸 섞는다"면 [`Map<Integer, V>`에서 `containsKey(1)` / `get(1)` / `getOrDefault(1, ...)`를 언제 갈라 읽을까](./map-integer-containskey-get-getordefault-bridge.md)
- "`기본 LinkedHashMap`과 `accessOrder=true`를 자꾸 같은 것으로 읽고, `get()`이나 기존 key `put()` 뒤 순서 변화만 짧게 다시 보고 싶다"면 [LinkedHashMap `get()` vs 기존 key `put()` access-order 미니 드릴](./linkedhashmap-get-put-existing-key-access-order-mini-drill.md)
- "`HashSet`이 하나로 보여서 equals/hashCode 쪽부터 다시 묶고 싶다"면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- "`Map.get()`이 `null`인데 key가 없는 건지 value가 `null`인 건지`, `넣었는데 get이 null`이 같이 보인다"면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) 다음 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
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

ordered-map 쪽은 여기서 한 칸 더 명시해 두는 편이 안전하다.

- `HashMap vs TreeMap 초급 선택 브리지 -> Ordered Map Null-Safe Practice Drill -> NavigableMap and NavigableSet Mental Model`

짧게 외우면 `Java 컬렉션 primer -> 자료구조 starter -> 알고리즘 또는 Service primer -> Java deep dive` 순서고, ordered map만 따로 막히면 위 3칸 사다리로 내려간다.

## Map null -> TreeMap -> ordered map 빠른 경로

- "`Map`에서 왜 `null`이 나오는지`부터 정리하고 싶다"면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- "`null` 해석을 한 뒤 `HashMap`과 `TreeMap`이 언제 갈리는지`를 바로 붙이고 싶다"면 [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)
- "`TreeMap`은 왜 `null` key를 막는데 comparator로 `null` 필드는 정렬되나요?`처럼 ordered map 들어가기 직전의 `null` 질문이 남아 있다"면 [TreeMap Null Key vs Nullable Field Primer](./treemap-null-key-vs-nullable-field-primer.md)
- "`TreeMap`을 ordered map으로 읽으면서 `floor`/`ceiling`이 왜 `null`이 되는지`까지 이어 가고 싶다"면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)

ordered map follow-up이 구현체 선택에서 끊기지 않게, beginner-safe route는 아래 한 줄로 고정해 두면 된다.

- [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md) -> [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md) -> [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

## Ordered Map / Set follow-up

- "`floor`/`ceiling`/`lower`/`higher`가 자꾸 섞인다"면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- "`ordered map에서 왜 null이 나오는지`를 경계 예제로 먼저 붙이고 싶다"면 [Ordered Map Null-Safe Practice Drill](./ordered-map-null-safe-practice-drill.md)
- "`exact match인데 ceiling은 자기 자신이고 higher는 왜 다음 key로 가죠?`가 헷갈린다"면 [`ceiling` vs `higher` Exact Match 미니 드릴](./ceiling-vs-higher-exact-match-mini-drill.md)
- "`subMap`/`headMap` 경계 포함 여부가 헷갈린다"면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](./submap-boundaries-primer.md)
- "`HashMap`과 `TreeMap`의 조회/덮어쓰기 기준 차이`를 더 짧게 다시 보고 싶다"면 [HashMap vs TreeMap 초급 선택 브리지](./hashmap-vs-treemap-beginner-selection-bridge.md)

## DTO / 값 객체 경계 빠른 탐색

- "`DTO에서 값 객체로 올릴지부터 헷갈려요`, `request DTO의 String을 service까지 그대로 넘겨도 되나요?`처럼 beginner 경계 질문이 먼저 나오면" [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)으로 바로 들어간다
- "`PATCH`에서 필드가 안 온 것과 `null`을 보낸 것을 왜 다르게 읽는지`부터 막힌다"면 [PATCH DTO에서 `missing` / `null` / 값 있음 을 구분하는 첫 입문](./patch-tri-state-field-primer.md)
- "`PATCH`에서 `Optional`이면 될 것 같은데 왜 `FieldPatch`를 또 두는지`가 헷갈리면" [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)
- "`값 객체로 올리면 equals/hashCode, Set key 판단이 왜 같이 쉬워지는지`를 먼저 묶고 싶다"면 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- "`돈`, `이메일`, `상품코드`처럼 규칙 있는 값을 언제 작은 타입으로 감싸야 하는지`가 궁금하다"면 [Money Value Object Basics](./money-value-object-basics.md)
- "`enum`, `record`, 값 객체 중 무엇을 먼저 고를지`가 막힌다"면 [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)

## 상속 / hook 설계 빠른 탐색

- "`beforeX`, `afterX`, `shouldX` 같은 이름이 자꾸 늘어나는데 이게 괜찮은지`부터 짧게 확인하고 싶다"면 [`beforeX`/`afterX`/`shouldX`가 늘어날 때: Template Method Hook Mini Smell Card](./template-method-hook-explosion-mini-smell-card.md)
- "`템플릿 메소드냐 전략이냐`를 먼저 15초로 자르고 싶다"면 [Template Method vs Strategy Quick Check Card](./template-method-vs-strategy-quick-check-card.md)
- "`상속이 맞는지, 조합으로 빼야 하는지` 큰 방향부터 다시 보고 싶다"면 [추상 클래스 vs 인터페이스 입문](./java-abstract-class-vs-interface-basics.md) 다음 [상속보다 조합 기초](../../design-pattern/composition-over-inheritance-basics.md)

## 복귀 경로

- Java primer 묶음 전체로 돌아가려면 [language 카테고리 인덱스](../README.md#java-primer)
- 자료구조 관점으로 다시 번역하고 싶다면 [data-structure 카테고리 인덱스](../../data-structure/README.md)
