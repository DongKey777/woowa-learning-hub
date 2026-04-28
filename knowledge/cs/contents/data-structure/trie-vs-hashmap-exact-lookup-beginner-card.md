# Trie vs HashMap: exact lookup이냐 prefix search냐

> 한 줄 요약: 문자열을 찾는다고 해서 항상 `Trie`가 필요한 것은 아니다. `"이 key 하나의 값"`을 찾으면 `HashMap`, `"이 prefix로 시작하는 후보들"`을 찾으면 `Trie`로 먼저 자르면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)
- [해시 테이블 기초](./hash-table-basics.md)
- [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- [Map vs Set vs Queue vs Priority Queue vs Trie vs Bitmap 선택 프라이머](./map-set-queue-priorityqueue-trie-bitmap-selection-primer.md)
- [Search 시스템 설계](../system-design/search-system-design.md)

retrieval-anchor-keywords: trie vs hashmap beginner, exact lookup vs prefix search, hashmap or trie choice, string lookup basics, autocomplete basics, startswith search beginner, 문자열 lookup 처음, trie hashmap 헷갈림, 왜 trie가 아니고 hashmap, what is prefix search, exact string match map, beginner autocomplete primer

## 핵심 개념

입문자가 가장 자주 섞는 문장은 둘이다.

- `apple`이라는 key의 값이 있나?
- `app`으로 시작하는 후보가 뭐가 있나?

둘 다 문자열을 다루지만 질문이 다르다.

- **exact lookup**이면 `HashMap`
- **prefix search**면 `Trie`

즉 "문자열을 저장한다"가 아니라 "**문자열에 어떤 질문을 반복하느냐**"가 구조 선택 기준이다.
문자열 key라고 해서 바로 `Trie`로 가면 과한 경우가 많고, 자동완성 문제를 `HashMap`으로만 밀면 매번 전체 key를 훑게 되기 쉽다.

## 한눈에 보기

| 지금 필요한 답 | 먼저 떠올릴 구조 | 왜 이쪽이 맞나 |
|---|---|---|
| `"apple"` 사용자의 프로필 값 | `HashMap<String, User>` | key 하나의 value를 바로 찾으면 된다 |
| `"app"`으로 시작하는 검색어 후보들 | `Trie` | prefix 경로 자체를 따라 내려갈 수 있다 |
| `"spring"`이 정확히 사전에 있나? | `HashMap` 또는 `Trie.search()` | exact match만 보면 보통 map이 더 단순하다 |
| `"spr"` 입력 때 자동완성 5개 | `Trie` | prefix 기준 후보 수집이 자연스럽다 |

짧게 외우면 이렇다.

- `한 단어 정확히 찾기` -> `HashMap`
- `앞부분이 같은 단어 묶기` -> `Trie`

## 같은 문자열도 질문이 달라지면 구조가 달라진다

검색창 예시로 보면 차이가 바로 보인다.

| 같은 문자열 데이터 | 질문 | 첫 구조 |
|---|---|---|
| `spring`, `spring boot`, `spring batch` | `"spring boot"가 사전에 있나?` | `HashMap` |
| `spring`, `spring boot`, `spring batch` | `"spr"로 시작하는 후보가 뭐가 있나?` | `Trie` |
| `kim`, `lee`, `park` 사용자 id | `"kim" 사용자의 정보가 뭐지?` | `HashMap` |
| `kim`, `lee`, `park` 사용자 id | `"ki"로 시작하는 사용자 id 후보를 보여 줄까?` | `Trie` |

여기서 초급자가 놓치기 쉬운 포인트는 이것이다.

> 데이터가 같아도, 질문이 `exact`에서 `prefix`로 바뀌는 순간 구조 선택도 바뀐다.

`HashMap`은 `"apple"` 같은 **완전한 key**를 넣고 꺼내는 데 강하다.
반대로 `Trie`는 `a -> p -> p`처럼 **문자 경로를 공유**하므로 `"app"` 아래 후보를 모으는 데 강하다.

## 흔한 오해와 함정

- `문자열이면 Trie가 더 전문 구조 아닌가요?`
  아니다. exact lookup만 하면 `HashMap`이 더 단순한 기본값이다.
- `HashMap으로도 startsWith를 쓰면 되지 않나요?`
  key 개수가 작으면 가능하다. 하지만 prefix 질의가 반복되면 전체 key를 자주 훑게 된다.
- `Trie면 exact lookup도 되니까 무조건 Trie가 상위호환인가요?`
  아니다. exact lookup만 필요한데 Trie를 쓰면 구현과 메모리 비용이 커질 수 있다.
- `자동완성은 무조건 Trie 하나로 끝나나요?`
  아니다. 후보를 모으는 구조는 `Trie`가 잘 맞지만, 정렬 점수나 최신성은 별도 로직이 붙는다.
- `HashMap`은 문자열 prefix를 전혀 못하나요?
  못 하는 건 아니다. 다만 prefix가 구조에 녹아 있지 않아서 보통 효율이 떨어진다.

## 실무에서 쓰는 모습

로그인 캐시, `couponCode -> Coupon`, `userId -> User`처럼 `"이 key 하나의 값"`을 바로 꺼내는 장면은 보통 `HashMap`으로 충분하다.

반대로 검색창 자동완성, 명령어 추천, 사전 후보 제안처럼 `"이 prefix로 시작하는 후보들"`을 빠르게 모아야 하는 장면은 `Trie`가 더 자연스럽다.
만약 여기서 질문이 `"이 prefix로 시작하는 후보들"`이 아니라 `"이 문자열 다음 사전순 key"`나 `"이 구간의 문자열 key"`라면 `HashMap` 대신 `TreeMap`과 비교해야 하므로 [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)로 이어 보는 편이 맞다.

실무에서 첫 분기를 짧게 적으면 이렇게 된다.

| 장면 | 첫 선택 |
|---|---|
| 주문 id로 주문 상태 조회 | `HashMap` |
| `spr` 입력 때 검색어 자동완성 | `Trie` |
| API key 문자열의 exact match 인증 | `HashMap` |
| `/api/or` prefix로 route 후보 찾기 | `Trie` |

## 더 깊이 가려면

- `HashMap` 기본 감각을 먼저 고정하려면 [해시 테이블 기초](./hash-table-basics.md)
- `map` 구현체를 더 나누려면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- 문자열 key에서 prefix search와 ordered map range/neighbor를 바로 자르려면 [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)
- `Trie`의 autocomplete, top-k, 메모리 trade-off를 더 보려면 [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- 검색 시스템 전체에서 autocomplete가 어디에 놓이는지 보려면 [Search 시스템 설계](../system-design/search-system-design.md)

## 면접/시니어 질문 미리보기

1. exact lookup만 있으면 왜 `Trie`보다 `HashMap`을 먼저 떠올리나요?
   prefix 경로를 저장할 필요가 없고, 구현과 메모리 면에서 더 단순한 기본값이기 때문이다.
2. `HashMap`으로 prefix 검색을 구현하면 왜 불편해지나요?
   prefix가 구조에 반영되지 않아 보통 여러 key를 훑거나 별도 인덱스를 붙여야 하기 때문이다.
3. autocomplete가 `Trie`만으로 끝나지 않는 이유는 무엇인가요?
   후보 생성 이후에 랭킹, 최신성, 클릭률 같은 추가 기준이 붙기 때문이다.

## 한 줄 정리

문자열 key를 다룬다고 `Trie`부터 고르지 말고, `exact key -> value`면 `HashMap`, `"이 prefix로 시작하는 후보"`면 `Trie`라고 먼저 자르면 된다.
