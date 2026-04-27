# List/Set/Map Requirement-to-Type Drill

> 한 줄 요약: 문제 문장을 보고 `List`, `Set`, `Map` 중 무엇을 먼저 떠올려야 하는지 짧게 훈련하는 초급 분류 드릴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)

retrieval-anchor-keywords: list set map requirement drill, java list set map practice, requirement to type classification, java collection selection exercise, list set map worksheet beginner, list set map decision habit, 처음 배우는데 list set map 고르기, 자바 컬렉션 요구사항 분류 연습, 자바 list set map 문제, 순서 중복 키값 판단 연습, list set map first read practice, linkedhashset beginner, 중복 제거 순서 유지 linkedhashset, list set linkedhashset 선택 기준, collection choice faq

## 먼저 잡는 멘탈 모델

컬렉션 선택이 막힐 때는 구현체 이름부터 외우지 않는다.
먼저 요구 문장을 아래 3가지로 번역한다.

- 순서/인덱스가 중요하면 `List`
- 자동 중복 제거가 필요하면 `Set`
- key로 조회/갱신이 중심이면 `Map`

## 10초 비교표

| 요구 신호 | 먼저 고를 타입 |
|---|---|
| "작성 순서", "N번째", "최근 10개" | `List` |
| "중복 없이", "유일한 값만" | `Set` |
| "id로 찾기", "코드별 값", "key-value" | `Map` |

## 분류 드릴

아래 문장을 읽고 `List`/`Set`/`Map` 중 하나를 적어 보자.
실행 코드보다 "요구를 타입으로 번역하는 습관"이 목표다.

| 번호 | 요구 문장 | 내 답 |
|---|---|---|
| 1 | 채팅 메시지를 도착한 순서대로 보여줘야 한다. |  |
| 2 | 이미 처리한 주문 번호는 중복 처리되면 안 된다. |  |
| 3 | 회원 id를 넣으면 회원 프로필을 바로 찾아야 한다. |  |
| 4 | 사용자가 선택한 관심사 태그를 보여 주되 같은 태그는 한 번만 유지한다. |  |
| 5 | 최근 검색어 20개를 최신순으로 유지하고 싶다. |  |
| 6 | 국가 코드(`KR`, `US`)로 통화 심볼을 조회한다. |  |
| 7 | 업로드된 파일 이름 목록을 업로드 순서대로 보여 준다. |  |
| 8 | 수강생 이메일 목록에서 중복 이메일은 제거해야 한다. |  |
| 9 | 상품 코드별 현재 재고 수량을 관리한다. |  |
| 10 | 할 일 항목을 사용자가 추가한 순서대로 렌더링한다. |  |
| 11 | 이미 본 공지 id는 다시 알림 보내지 않도록 기록한다. |  |
| 12 | 사용자명으로 마지막 로그인 시각을 조회한다. |  |

## 정답

| 번호 | 정답 | 이유(한 줄) |
|---|---|---|
| 1 | `List` | 순서 보존이 핵심 |
| 2 | `Set` | 중복 방지가 핵심 |
| 3 | `Map` | id(key) 기반 조회가 핵심 |
| 4 | `Set` | 태그 중복 제거가 핵심 |
| 5 | `List` | 최신순/개수 제한 목록 관리 |
| 6 | `Map` | 코드 -> 값 매핑 |
| 7 | `List` | 업로드 순서 유지 |
| 8 | `Set` | 유일한 이메일 집합 |
| 9 | `Map` | 상품 코드별 수량 조회/갱신 |
| 10 | `List` | 추가 순서대로 렌더링 |
| 11 | `Set` | 본 id의 존재 여부 기록 |
| 12 | `Map` | 사용자명 key로 시각 조회 |

## 초보자가 자주 헷갈리는 포인트

- "중복 제거 + 순서"가 동시에 필요하면 기본 답을 하나만 고르기 어렵다.
- 첫 읽기에서는 핵심 요구 하나를 먼저 고른다.
- 예: "중복 제거"가 본질이면 `Set` 먼저, "순서 출력"이 본질이면 `List` 먼저.
- 그런데 "중복 제거 + 입력 순서 유지"가 요구 자체라면 `LinkedHashSet`을 바로 떠올리는 편이 더 정확하다. 이 감각은 [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)에서 짧게 이어서 보면 된다.
- `Map`은 `Collection` 하위 타입이 아니므로 반복할 때 `entrySet()` 같은 전용 API를 쓴다.

## 자주 틀리는 문장 패턴 FAQ

문장에 `순서`, `중복`, `key`라는 단어가 안 보여도 요구가 숨어 있는 경우가 많다.
초보자 오답은 보통 "자료구조 이름"을 찾으려다가 생기고, 정답은 "동작 신호"를 읽으면 더 빨리 보인다.

| 문장 패턴 | 먼저 떠올릴 타입 | 왜 그렇게 읽나 |
|---|---|---|
| "회원 id를 넣으면 회원 정보를 찾는다" | `Map` | `id -> 정보` 매핑이다. `key`라는 단어가 없어도 조회 기준이 하나 정해져 있다. |
| "상품 코드별 재고 수량을 관리한다" | `Map` | `코드별`, `~별`은 초보자에게 가장 자주 나오는 `Map` 신호다. |
| "이미 처리한 주문 번호는 다시 처리되면 안 된다" | `Set` | 핵심은 순서가 아니라 "이미 봤는지" 여부다. |
| "최근 본 상품을 보여 준다" | `List` | `순서`라는 단어가 없어도 최근/최신/이전은 순서 신호다. |
| "태그를 한 번만 남기되 처음 넣은 순서는 유지한다" | `LinkedHashSet` | `Set` 하나로 끝나지 않고, 중복 제거와 입력 순서를 같이 요구한다. |

### FAQ 1. 문장에 `key`가 없는데 왜 `Map`인가요?

`Map` 신호는 `key`라는 단어보다 "무엇으로 찾느냐"에 숨어 있다.

- `id를 넣으면 프로필을 찾는다`
- `사용자명으로 마지막 로그인 시각을 조회한다`
- `국가 코드별 통화 심볼을 관리한다`

이 문장들은 모두 "하나의 기준값으로 다른 값을 꺼낸다"는 뜻이다.
즉 `id`, `사용자명`, `국가 코드`가 사실상 `Map`의 key 역할을 한다.

### FAQ 2. 문장에 `중복`이 없는데 왜 `Set`인가요?

`Set` 신호는 `중복 제거`라는 단어 대신 아래 표현으로 자주 나온다.

- `이미 본`
- `다시 처리되면 안 된다`
- `한 번만 기록`
- `중복 알림 방지`

예를 들어 "이미 본 공지 id를 기록한다"는 문장은 목록 출력이 아니라 **존재 여부 확인**이 핵심이다.
그래서 `List`보다 `Set`이 먼저다.

### FAQ 3. 문장에 `순서`가 없는데 왜 `List`인가요?

`List` 신호는 `순서`라는 단어 대신 시간 흐름이나 위치 표현으로 자주 나온다.

- `최근 10개`
- `최신순`
- `첫 번째`
- `도착한 메시지`

이 표현들은 결국 "앞뒤 관계를 유지해야 한다"는 뜻이므로 `List` 쪽으로 읽는다.

### FAQ 4. `Set`이면 다 `HashSet`, `Map`이면 다 `HashMap` 아닌가요?

첫 선택은 보통 맞지만, 문장에 추가 신호가 있으면 구현체도 같이 바뀐다.

| 추가 신호 | 더 맞는 선택 |
|---|---|
| "입력한 순서를 유지" | `LinkedHashSet`, `LinkedHashMap` |
| "정렬해서 보여 준다" | `TreeSet`, `TreeMap` |
| "순서는 중요하지 않다" | `HashSet`, `HashMap` |

## 자주 틀리는 문장 패턴 FAQ (계속 2)

즉 인터페이스는 `List`/`Set`/`Map`으로 먼저 고르고,
순서 보장 방식까지 요구되면 그다음 구현체를 고른다.

## 오답노트: 먼저 읽을 신호어

문장을 빠르게 번역할 때는 아래 신호어부터 찾으면 된다.

| 신호어 | 먼저 의심할 타입 |
|---|---|
| `~별`, `~로 찾기`, `조회`, `매핑` | `Map` |
| `이미`, `중복 방지`, `한 번만`, `본 적 있는지` | `Set` |
| `최근`, `최신순`, `N번째`, `도착 순서` | `List` |

이 표를 "정답표"라기보다 첫 번째 질문표로 보면 된다.
헷갈리면 인터페이스를 먼저 정하고, 순서 유지 방식은 관련 문서로 이어서 좁혀 가면 된다.

## 다음 단계

- 타입 고르는 기준을 먼저 정리하려면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- "중복 제거 + 순서 유지" 조합을 바로 고르려면 [`LinkedHashSet` 순서+중복 제거 미니 브리지](./linkedhashset-order-dedup-mini-bridge.md)
- `Map`인데 출력 순서도 중요해졌다면 [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- `Map`의 `get()`/`containsKey()` 선택이 헷갈리면 [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- `Map` 반복 습관을 바로 교정하려면 [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- `Iterable`/`Collection`/`Map` 관계가 헷갈리면 [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)

## 한 줄 정리

문제 문장을 보고 `List`, `Set`, `Map` 중 무엇을 먼저 떠올려야 하는지 짧게 훈련하는 초급 분류 드릴이다.
