# Map 구현체 선택 미니 드릴

> 한 줄 요약: 짧은 요구 문장을 보고 `HashMap`/`LinkedHashMap`/`TreeMap` 중 무엇을 먼저 골라야 하는지 손으로 빠르게 분류하는 1페이지 beginner 워크시트다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: map implementation selection mini drill, hashmap linkedhashmap treemap worksheet, java map implementation practice, java ordered map choice beginner, hashmap linkedhashmap treemap difference drill, 자바 map 구현체 선택 연습, 자바 hashmap linkedhashmap treemap 고르기, 순서 유지 map 뭐 써야 해, 정렬된 map 뭐 써야 해, 처음 배우는데 map 구현체 선택, beginner map choice worksheet

## 먼저 잡는 멘탈 모델

이 드릴은 복잡한 성능 비교보다 "순서를 요구하느냐"만 먼저 본다.

- 순서 요구가 없으면 `HashMap`
- 넣은 순서를 유지해야 하면 `LinkedHashMap`
- key 정렬 순서가 필요하면 `TreeMap`

짧게 외우면 "`순서 없음 / 넣은 순서 / 정렬 순서`" 3칸 표다.

## 10초 비교표

| 요구 문장 신호 | 첫 선택 | 이유 |
|---|---|---|
| "조회만 빨리", "순서는 상관없다" | `HashMap` | 순서 계약이 필요 없다 |
| "입력한 순서대로 보여 준다" | `LinkedHashMap` | 삽입 순서를 유지한다 |
| "이름순", "점수순", "날짜순" | `TreeMap` | key 기준 정렬 순서가 필요하다 |

초보자 기준에서는 이 표만 정확히 읽어도 첫 선택 실수 대부분을 줄일 수 있다.

## 미니 워크시트

아래 요구 문장을 읽고 `HashMap` / `LinkedHashMap` / `TreeMap` 중 하나를 적어 보자.

| 번호 | 요구 문장 | 내 답 |
|---|---|---|
| 1 | 회원 id로 프로필을 찾기만 하면 되고, 출력 순서는 중요하지 않다. |  |
| 2 | 사용자가 추가한 북마크를 추가한 순서대로 보여 줘야 한다. |  |
| 3 | 상품 코드를 이름순으로 출력해야 한다. |  |
| 4 | 캐시 내부 저장은 하되 순서 자체는 비즈니스 규칙이 아니다. |  |
| 5 | 설문 응답을 입력된 순서대로 관리자 화면에 보여 준다. |  |
| 6 | 시험 점수를 작은 점수부터 큰 점수 순으로 보고 싶다. |  |
| 7 | 에러 코드로 메시지를 찾기만 하면 된다. |  |
| 8 | 최근 등록된 FAQ를 등록한 순서대로 그대로 나열한다. |  |
| 9 | 주문을 주문번호 오름차순으로 확인해야 한다. |  |

## 정답과 한 줄 이유

| 번호 | 정답 | 이유 |
|---|---|---|
| 1 | `HashMap` | key 조회가 핵심이고 순서 요구가 없다 |
| 2 | `LinkedHashMap` | 입력한 순서를 유지해야 한다 |
| 3 | `TreeMap` | 이름순은 key 정렬 요구다 |
| 4 | `HashMap` | 순서가 규칙이 아니면 기본 선택이 된다 |
| 5 | `LinkedHashMap` | 삽입 순서 보존이 필요하다 |
| 6 | `TreeMap` | 점수순 정렬이 핵심이다 |
| 7 | `HashMap` | 코드로 찾기만 하면 된다 |
| 8 | `LinkedHashMap` | 등록한 순서 그대로 보여 줘야 한다 |
| 9 | `TreeMap` | 주문번호 오름차순은 정렬 순서다 |

## 자주 헷갈리는 포인트

- `HashMap`이 내 환경에서 우연히 일정한 순서로 보여도 그 순서를 계약처럼 믿으면 안 된다.
- `LinkedHashMap`은 "정렬 map"이 아니다. key를 정렬하지 않고 넣은 순서를 유지한다.
- `TreeMap`은 value가 아니라 key 기준으로 정렬한다.
- 문장에 "순서대로 보여 준다"가 있으면 `HashMap`보다 `LinkedHashMap` 쪽을 먼저 의심한다.
- 문장에 "`~순`", "`오름차순`", "`이름순`"이 있으면 `TreeMap` 신호로 읽는다.

## 다음 읽기

- 구현체별 순서 감각을 예제로 다시 보고 싶다면 [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- 먼저 `List`/`Set`/`Map` 큰 분류가 헷갈리면 [List/Set/Map Requirement-to-Type Drill](./list-set-map-requirement-to-type-drill.md)
- `TreeMap` 탐색 API까지 이어서 보려면 [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

## 한 줄 정리

`HashMap`은 순서 없음, `LinkedHashMap`은 넣은 순서, `TreeMap`은 key 정렬 순서라고 먼저 번역하면 짧은 요구 문장에서도 구현체 선택이 훨씬 빨라진다.
