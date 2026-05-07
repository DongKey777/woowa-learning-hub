---
schema_version: 3
title: Java enum 기초
concept_id: language/java-enum-basics
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- java-enum-state-model
- enum-vs-optional
- enum-string-boundary
aliases:
- java enum basics
- enum 입문
- 열거형 기초
- enum why use
- enum vs int constants
- java enum switch
- enum ordinal name
- java 상태값 enum
- enum vs optional
- 없음의 이유 enum
- enum object state behavior
symptoms:
- enum을 단순 문자열이나 정수 상수 대체로만 보고 객체 상태 field와 behavior 연결을 놓친다
- Optional의 없음과 enum의 상태 후보를 섞어 없음의 이유가 필요한 상황을 표현하지 못한다
- ordinal을 저장하거나 외부 문자열 payload를 enum 상수와 바로 비교하는 경계 실수를 한다
intents:
- definition
- comparison
prerequisites:
- language/java-types-class-object-oop-basics
- language/java-optional-basics
next_docs:
- language/enum-string-boundary-bridge
- language/enum-equality-quick-bridge
- language/enum-to-state-transition-beginner-bridge
- language/enummap-status-policy-lookup-primer
linked_paths:
- contents/language/java/java-optional-basics.md
- contents/language/java/optional-collections-domain-null-handling-bridge.md
- contents/language/java/enum-to-state-transition-beginner-bridge.md
- contents/language/java/enummap-status-policy-lookup-primer.md
- contents/language/java/enum-equality-quick-bridge.md
- contents/language/java/enum-string-boundary-bridge.md
- contents/language/java/java-types-class-object-oop-basics.md
- contents/language/java/java-exception-handling-basics.md
confusable_with:
- language/java-optional-basics
- language/enum-string-boundary-bridge
- language/enum-equality-quick-bridge
forbidden_neighbors: []
expected_queries:
- Java enum은 정수 상수나 문자열 상태값 대신 언제 쓰는지 beginner 기준으로 설명해줘
- Optional의 없음과 enum의 상태 후보는 어떤 질문이 달라서 서로 대체재가 아닌지 알려줘
- enum field가 객체 상태가 되고 behavior가 그 상태를 읽는 흐름을 ReservationStatus 예시로 보고 싶어
- enum ordinal을 DB에 저장하면 왜 위험하고 name이나 별도 code를 어떻게 봐야 해?
- DTO에서 받은 상태 문자열을 enum 상수와 바로 비교하지 말고 boundary에서 변환해야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Java enum을 고정된 상태 후보와 객체 상태 field로 이해하는 beginner primer다.
  enum vs int constants, enum switch, name vs ordinal, enum equality, enum vs Optional, 없음의 이유, DTO string payload to enum boundary, state transition, EnumMap lookup을 다룬다.
---
# Java enum 기초

> 한 줄 요약: enum은 미리 정의한 상수 집합을 타입으로 만들어서, 정수 상수 대신 이름 있는 값으로 컴파일 시점에 안전하게 사용하는 기능이다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- [EnumMap으로 상태별 라벨/요금/정책 lookup 붙이기](./enummap-status-policy-lookup-primer.md)
- [Enum equality quick bridge](./enum-equality-quick-bridge.md)
- [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./enum-string-boundary-bridge.md)
- [Java 타입, 클래스, 객체, OOP 입문](./java-types-class-object-oop-basics.md)
- [Java 예외 처리 기초](./java-exception-handling-basics.md)

retrieval-anchor-keywords: java enum basics, enum 입문, 열거형 기초, enum 왜 쓰나요, enum vs int constants, java enum switch, enum ordinal name, beginner enum java, java 상태값 enum, enum 처음 배우는데, enum vs optional, enum null 상태 표현, 없음의 이유 enum, enum field object state behavior, enum이 객체 상태인가요

## 핵심 개념

`enum`은 고정된 상수 집합을 하나의 타입으로 선언하는 방법이다. 예를 들어 요일, 주문 상태, 방향 같이 미리 정해진 값들만 쓸 수 있는 경우에 쓴다.

정수 상수(`static final int MONDAY = 0`)로 대체할 수 있지만, 정수는 컴파일러가 의미를 모른다. `setDay(0)` 대신 `setDay(Day.MONDAY)`로 쓰면 잘못된 값 전달을 컴파일 시점에 막을 수 있다.

입문자가 헷갈리는 지점은 enum도 클래스처럼 메서드와 필드를 가질 수 있다는 것이다. 다만 beginner 첫 읽기에서는 "상태 후보를 고정하는 타입"으로 먼저 이해하면 충분하다.

여기서 용어를 한 줄 더 붙이면 `enum`, field, 객체 상태, behavior가 따로 놀지 않는다.

- `field`: 객체 안에 저장된 칸
- `object state`: 그 field 값들이 모인 현재 상태
- `behavior`: 그 상태를 읽거나 바꾸는 메서드

즉 enum은 보통 **객체 안의 field에 들어가서 object state를 읽기 좋은 이름으로 만드는 타입**이다.

## 한눈에 보기

- `java enum basics`의 첫 기준은 정의, 사용 시점, 흔한 오해를 분리해서 읽는 것이다.
- 코드 예시는 바로 아래 섹션에서 보고, 여기서는 판단 기준만 먼저 잡는다.
- 입문 단계에서는 API 이름보다 어떤 문제를 줄이는지부터 확인한다.

## 15초 비교표: `enum`은 언제 나오나

초보자가 자주 섞는 선택지를 한 장으로 놓고 보면 enum 자리가 더 선명해진다.

| 지금 표현하려는 것 | 첫 선택 | 왜 |
|---|---|---|
| 주문 상태가 `WAIT`, `ACTIVE`, `DONE` 중 하나여야 한다 | `enum` | 가능한 값 후보를 고정한다 |
| 회원 한 명을 찾았는데 없을 수도 있다 | `Optional<User>` | 단건 결과의 있음/없음이 핵심이다 |
| 주문 항목이 0개일 수 있다 | `List<OrderLine>` + 빈 리스트 | 여러 건 자료의 0개는 컬렉션이 표현한다 |
| 닉네임이 없음 / 비공개 / 미입력처럼 이유가 갈린다 | `enum`을 포함한 상태 타입 | "왜 없는지"를 이름 붙여서 전달한다 |

짧게 말하면 enum은 "가능한 상태 이름표"다. `Optional`이 단건의 없음에 답한다면, enum은 "어떤 상태들 중 하나인가"에 답한다.

`enum field -> object state -> behavior` 순서로 읽으면, enum 자체와 객체 상태 모델을 따로 외우지 않아도 된다.

## 처음 `enum`과 `null`이 같이 헷갈릴 때

초보자 질문은 보통 "`null` 대신 enum 하나 더 만들면 끝 아닌가요?"로 나온다. 이때는 "질문의 종류"를 먼저 나누면 된다.

| 지금 코드가 묻는 질문 | 첫 선택 | 이유 |
|---|---|---|
| 값이 있나 없나 | `Optional<T>` | 단건의 존재 여부가 핵심이다 |
| 상태 후보가 `WAIT`, `ACTIVE`, `DONE`처럼 닫혀 있나 | `enum` | 가능한 값 집합을 고정한다 |
| 없음 / 비공개 / 미입력처럼 이유도 갈라야 하나 | enum을 포함한 상태 타입 | 이유 이름표가 필요하다 |

즉 enum은 `null`을 기계적으로 치환하는 도구가 아니라, "도메인 상태 이름이 미리 정해져 있는가"를 드러내는 도구다.

객체 관점으로 다시 번역하면 흐름은 같다.

- enum은 상태 후보 이름을 만든다
- 그 enum이 객체의 상태 field에 들어간다
- 메서드는 그 field를 읽어 행동을 결정한다

그래서 "상태를 enum으로 본다"와 "객체가 상태 field를 가진다"는 서로 다른 모델이 아니라 같은 코드를 읽는 두 표현이다.

## 코드로 보는 예시

```java
// 정수 상수 방식 (오류 가능성 있음)
static final int STATUS_WAIT   = 0;
static final int STATUS_ACTIVE = 1;
void process(int status) { ... }  // process(999) 컴파일 통과

// enum 방식 (타입 안전)
enum OrderStatus { WAIT, ACTIVE, DONE }
void process(OrderStatus status) { ... }  // process(OrderStatus.WAIT)만 가능
```

없음의 이유를 같이 표현할 때도 enum이 잘 맞는다.

```java
enum NicknameStatus {
    PRESENT,
    NOT_ENTERED,
    PRIVATE
}

record NicknameInfo(NicknameStatus status, String value) {
}
```

이 예제는 `Optional<String>` 하나로는 부족한 순간을 보여 준다.

- 값이 없을 수 있다는 사실만 중요하면 `Optional<String>`
- 값이 없는 이유까지 갈라야 하면 `NicknameStatus` 같은 enum 상태

반대로 이유 구분이 전혀 없고 "있다/없다"만 중요하다면 enum보다 `Optional`이 더 단순하다. beginner 첫 읽기에서는 이 둘을 경쟁 관계로 보기보다, "질문이 다르다"로 받아들이는 편이 안전하다.

## 같은 예시를 `field -> object state -> behavior`로 다시 읽기

enum이 실제 코드에서 어디에 놓이는지 감이 약하면, 타입 선언만 보지 말고 객체 안으로 넣어서 읽어 보면 된다.

```java
enum ReservationStatus {
    REQUESTED,
    CONFIRMED,
    CANCELLED
}

class Reservation {
    private ReservationStatus status = ReservationStatus.REQUESTED;

    public void confirm() {
        if (status != ReservationStatus.REQUESTED) {
            throw new IllegalStateException("요청 상태에서만 확정할 수 있다.");
        }
        status = ReservationStatus.CONFIRMED;
    }
}
```

| 어디를 읽나 | 코드에서 보이는 것 | 무슨 뜻인가 |
|---|---|---|
| field | `private ReservationStatus status` | 객체 안에 상태를 저장하는 칸 |
| object state | `REQUESTED`, `CONFIRMED`, `CANCELLED` 중 현재 값 | 이 예약 객체가 지금 어떤 상태인가 |
| behavior | `confirm()` | 현재 상태를 읽고 다음 행동 허용 여부를 결정 |

핵심은 enum이 혼자 떠다니는 것이 아니라는 점이다. enum은 field에 들어가 object state를 만들고, behavior는 그 state를 읽어 규칙을 적용한다.

## 상세 분해

### 기본 선언과 사용

```java
public enum Direction { NORTH, SOUTH, EAST, WEST }

Direction d = Direction.NORTH;
System.out.println(d.name());    // "NORTH"
System.out.println(d.ordinal()); // 0 (선언 순서 인덱스)
```

`name()`은 선언한 이름 문자열, `ordinal()`은 0부터 시작하는 순서 인덱스를 반환한다.

### switch에서 활용

```java
OrderStatus status = OrderStatus.WAIT;
switch (status) {
    case WAIT   -> System.out.println("대기 중");
    case ACTIVE -> System.out.println("처리 중");
    case DONE   -> System.out.println("완료");
}
```

switch 표현식과 잘 어울리며, 빠진 케이스를 IDE나 컴파일러가 경고해 준다.

### 필드와 메서드를 가진 enum

```java
public enum DeliveryStatus {
    READY("배송 준비"),
    SHIPPED("배송 중"),
    DONE("배송 완료");

    private final String label;

    DeliveryStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
```

enum 상수에 설명용 값을 붙이고 메서드를 정의할 수 있다. beginner 단계에서는 "상태 이름에 표시용 라벨을 같이 붙일 수 있다" 정도만 먼저 잡아도 충분하다.

## 흔한 오해와 함정

**오해 1: `ordinal()` 값을 DB에 저장하면 된다**
enum 순서가 바뀌거나 중간에 상수가 삽입되면 ordinal이 밀린다. DB에는 `name()`(문자열)을 저장하는 것이 안전하다.

**오해 2: `==`와 `equals()`가 다르게 동작한다**
enum 상수는 싱글턴이므로 `==`와 `equals()` 모두 같은 결과를 낸다. 관용적으로는 `==`를 쓰고, 왜 그런지와 null-safe 비교 감각은 [Enum equality quick bridge](./enum-equality-quick-bridge.md)에서 짧게 이어진다.

**오해 3: `Enum.values()`는 항상 선언 순서대로다**
맞다. 하지만 ordinal에 의존한 로직을 짜면 상수 추가 시 버그가 생긴다. 순서 의존을 피하고 필드로 순서를 관리하는 것이 낫다.

**오해 4: `null`이 보기 싫으면 enum 상수 하나를 무조건 추가하면 된다**
항상 그렇지는 않다. "값이 있나 없나"만 중요하면 `Optional`이 더 단순하고, "왜 없는가"가 중요할 때 enum 상태가 빛난다. enum 상수를 추가할지, `Optional`로 둘지는 도메인 질문이 무엇인지부터 보고 결정한다.

**오해 5: enum으로 상태를 모델링하면 field나 객체 상태 이야기는 별개다**
아니다. beginner 코드에서는 `OrderStatus status`처럼 enum이 field에 들어가고, 그 field 값이 곧 객체 상태의 일부가 된다. 그다음 `pay()`, `confirm()` 같은 메서드가 그 상태를 읽고 바꾼다.

## 다음 한 칸

enum 첫 읽기 뒤에는 "상태 이름표" 다음 단계만 한 칸씩 붙이는 편이 안전하다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`Optional.empty()`와 enum 상태를 언제 갈라야 하지?" | [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md) |
| "`==`로 비교해도 되는 이유가 더 궁금하다" | [Enum equality quick bridge](./enum-equality-quick-bridge.md) |
| "`PAID` 같은 문자열 payload는 enum과 어떻게 이어지지?" | [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./enum-string-boundary-bridge.md) |
| "상태별 라벨이나 정책 lookup을 붙이고 싶다" | [EnumMap으로 상태별 라벨/요금/정책 lookup 붙이기](./enummap-status-policy-lookup-primer.md) |
| "단순 상수 집합을 넘어 상태 전이까지 가고 싶다" | [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md) |

## 더 깊이 가려면

- enum에서 미션 스타일 도메인 상태 전이로 넘어가는 첫 단계: [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- JSON 직렬화·DB 저장 시 unknown 값 처리: [enum-persistence-json-unknown-value-evolution](./enum-persistence-json-unknown-value-evolution.md)

## 한 줄 정리

enum은 컴파일 시점에 안전한 상수 집합 타입이고, 정수 상수 대신 쓰면 잘못된 값 전달을 원천 차단할 수 있다.
