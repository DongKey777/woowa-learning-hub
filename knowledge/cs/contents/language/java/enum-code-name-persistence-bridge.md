---
schema_version: 3
title: enum 내부 이름과 외부 code 저장 계약 브리지
concept_id: language/enum-code-name-persistence-bridge
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- enum-boundary
- persistence-contract
- json-contract
aliases:
- enum code name persistence bridge
- enum name vs code beginner
- JPA EnumType STRING vs code
- Jackson enum JSON code field
- internal enum name external code
- enum code 필드 저장 계약
symptoms:
- enum에 code 필드를 추가하면 DB/JSON이 자동으로 code를 저장하거나 전송한다고 기대해
- Java 내부 비교 기준인 enum 상수와 외부 저장/전송 계약인 code/name 선택을 분리하지 못해
- DB converter와 JSON serializer/DTO mapper가 서로 다른 adapter라 각각 값을 고른다는 점을 놓쳐
intents:
- definition
- design
- troubleshooting
prerequisites:
- language/enum-string-boundary-bridge
- language/java-enum-basics
next_docs:
- language/enum-persistence-json-unknown-value-evolution
- language/request-dto-to-value-object-boundary-primer
- database/jdbc-jpa-mybatis-basics
linked_paths:
- contents/language/java/enum-string-boundary-bridge.md
- contents/language/java/enum-persistence-json-unknown-value-evolution.md
- contents/language/java/request-dto-to-value-object-boundary-primer.md
- contents/database/jdbc-jpa-mybatis-basics.md
confusable_with:
- language/enum-string-boundary-bridge
- language/enum-persistence-json-unknown-value-evolution
- database/jdbc-jpa-mybatis-basics
forbidden_neighbors: []
expected_queries:
- enum에 code 필드를 넣으면 DB나 JSON이 자동으로 code 값을 저장하는지 알려줘
- JPA EnumType.STRING은 enum name을 저장하는지 code 필드를 저장하는지 비교해줘
- enum 내부 상수 이름과 외부 code 계약을 DB JSON에서 어떻게 나눠야 해?
- Jackson JSON에서 enum code를 내보내려면 serializer나 DTO mapper가 필요한 이유가 뭐야?
- enum fromCode와 DB converter를 beginner 기준으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 Java enum의 internal name과 external code field를 DB persistence, JSON serialization, JPA converter, DTO mapper boundary로 분리하는 beginner primer다.
  enum code field, EnumType.STRING, JSON enum code, fromCode, enum persistence contract 질문이 본 문서에 매핑된다.
---
# enum 내부 이름과 외부 code를 나누면 왜 DB/JSON 저장 계약도 같이 갈라질까

> 한 줄 요약: enum에 `name`과 `code`를 둘 다 두는 순간 Java 내부 비교 기준과 DB/JSON 저장 기준이 자동으로 같지 않다. 내부에서는 enum 상수 이름을 쓰고, 외부 저장/전송에서는 어떤 값을 계약으로 쓸지 명시적으로 골라야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./enum-string-boundary-bridge.md)
- [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
- [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- [JDBC/JPA/MyBatis 기초](../../database/jdbc-jpa-mybatis-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: enum code name persistence, enum code field json db, enum name vs code beginner, jpa enumtype string vs code, jackson enum json code field, 왜 enum name 저장돼요, enum code value persistence bridge, 처음 enum db json contract, internal enum name external code, beginner enum persistence, what is enum code field, enum code 필드 헷갈려요

## 핵심 개념

처음 enum을 배울 때는 보통 이렇게 본다.

- 코드 안에서는 `OrderStatus.PAID`처럼 상수 이름으로 비교한다
- DB나 JSON에도 그 이름이 그대로 나갈 것처럼 느껴진다

그런데 실무에서는 enum 이름과 외부 code를 나누는 순간이 자주 온다.

```java
public enum OrderStatus {
    PAYMENT_WAITING("PW"),
    PAID("PD"),
    CANCELLED("CN");

    private final String code;

    OrderStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }
}
```

이제 한 타입 안에 값이 두 종류가 생긴다.

- 내부 이름: `PAYMENT_WAITING`, `PAID`, `CANCELLED`
- 외부 code: `"PW"`, `"PD"`, `"CN"`

핵심은 이것이다.

> enum 상수 이름은 Java 코드가 읽는 값이고, `code` 필드는 DB/JSON 같은 외부 경계가 읽는 값 후보다.

즉 `code` 필드를 추가했다고 해서 DB와 JSON이 자동으로 `"PW"`를 저장하는 것은 아니다.

## 한눈에 보기

| 보고 있는 자리 | 기본적으로 쓰이는 값 | 초보자가 자주 착각하는 점 |
|---|---|---|
| Java 코드의 `switch`, `==` 비교 | enum 상수 자체 | `code` 필드를 만들면 내부 비교도 코드값 기준으로 바뀐다고 생각함 |
| JPA `EnumType.STRING` 저장 | 보통 `name()` | `"PW"` 같은 `code`가 저장될 거라고 기대함 |
| Jackson 기본 JSON 직렬화 | 보통 enum 이름 | `code()` getter가 있으니 자동으로 `code`가 나갈 거라고 기대함 |
| 직접 만든 converter/mapper | 팀이 명시한 값 | 한 번 정하면 DB와 JSON이 항상 같은 규칙일 거라고 생각함 |

짧게 정리하면 이렇다.

- 내부 비교 계약: enum 상수 이름 중심
- 외부 저장 계약: DB/JSON에서 무엇을 내보낼지 별도 선택

두 계약은 같은 값일 수도 있지만, 분리하기로 한 순간부터는 의식적으로 맞춰 줘야 한다.

## 왜 DB 계약과 JSON 계약이 같이 달라지지 않을까

초보자 눈에는 DB 저장과 JSON 직렬화가 둘 다 "밖으로 내보내는 일"이라서 같은 규칙처럼 보인다.
하지만 실제로는 출구가 다르다.

- DB는 JPA converter, `EnumType.STRING`, JDBC 매핑 규칙을 탄다
- JSON은 Jackson 직렬화 규칙이나 DTO mapper를 탄다

즉 둘 다 enum을 밖으로 보내지만, **서로 다른 어댑터**가 값을 고른다.

예를 들어 `OrderStatus.PAYMENT_WAITING`을 저장할 때:

| 레이어 | 아무 설정이 없으면 나가기 쉬운 값 | 외부 계약이 `"PW"`라면 필요한 것 |
|---|---|---|
| DB | `PAYMENT_WAITING` | `code`를 저장하는 converter |
| JSON | `PAYMENT_WAITING` | `code`를 내보내는 serializer 또는 DTO 매핑 |

여기서 beginner가 꼭 잡아야 할 감각은 이것이다.

> enum 안에 `code` 필드가 있다는 사실과, 저장 도구가 그 필드를 실제로 사용한다는 사실은 별개다.

그래서 내부 이름과 외부 code를 분리하면 "이제 더 안전해졌다"가 아니라, 정확히는 "이제 저장/전송 어댑터를 명시해야 한다"가 된다.

## 코드로 보는 가장 작은 브리지

가장 먼저 필요한 것은 `fromCode(...)` 같은 해석 함수다.

```java
public enum OrderStatus {
    PAYMENT_WAITING("PW"),
    PAID("PD"),
    CANCELLED("CN");

    private final String code;

    OrderStatus(String code) {
        this.code = code;
    }

    public String code() {
        return code;
    }

    public static OrderStatus fromCode(String rawCode) {
        for (OrderStatus status : values()) {
            if (status.code.equals(rawCode)) {
                return status;
            }
        }
        throw new IllegalArgumentException("Unknown code: " + rawCode);
    }
}
```

이제 역할을 두 줄로 나눠 읽는다.

- 내부 Java 로직: `if (status == OrderStatus.PAID)`
- 외부 입력/저장 경계: `"PD"` <-> `OrderStatus.PAID`

DB 저장은 보통 이런 방향이다.

```java
@Converter(autoApply = true)
public class OrderStatusConverter implements AttributeConverter<OrderStatus, String> {
    @Override
    public String convertToDatabaseColumn(OrderStatus attribute) {
        return attribute == null ? null : attribute.code();
    }

    @Override
    public OrderStatus convertToEntityAttribute(String dbData) {
        return dbData == null ? null : OrderStatus.fromCode(dbData);
    }
}
```

JSON도 같은 생각으로 본다.

- 응답이 `"PD"`를 내보내야 하면 JSON 쪽도 `code` 기준으로 매핑한다
- 응답이 `"PAID"`를 내보내야 하면 JSON 계약은 이름 기준이고, DB 계약과 다를 수 있다

즉 "enum 하나"가 아니라 "DB용 출구"와 "JSON용 출구"를 따로 본다.

## 자주 헷갈리는 포인트

| 헷갈리는 말 | 실제로는 무엇을 뜻하나 |
|---|---|
| "`EnumType.STRING`이면 문자열이니까 `code`겠지?" | 아니다. 보통은 enum의 `name()` 문자열이다 |
| "`getCode()`가 있으니 JSON도 `code`로 나가겠지?" | 기본 직렬화는 보통 enum 자체 규칙을 따른다. 명시가 필요할 수 있다 |
| "`code`를 두면 rename이 완전히 자유롭겠네?" | DB/JSON이 정말 `code`만 쓰도록 맞춘 경우에만 그렇다 |
| "DB도 JSON도 둘 다 문자열이니 같은 계약이다" | 둘 다 문자열일 수는 있지만, 어떤 문자열을 쓰는지는 별도 계약이다 |

특히 아래 상황이 beginner에게 자주 함정이 된다.

1. enum에 `code` 필드를 추가한다
2. 내부 비교는 잘 동작한다
3. 그런데 DB에는 `PAYMENT_WAITING`이 저장되고 JSON도 `PAYMENT_WAITING`으로 나간다

여기서 문제는 enum 설계보다 "저장/직렬화 어댑터를 아직 안 붙였다"에 가깝다.

## 언제 어떤 선택을 하면 덜 헷갈릴까

| 상황 | beginner 기본 선택 |
|---|---|
| DB와 JSON 둘 다 내부 enum 이름을 외부 계약으로 써도 된다 | `name()` 기반 계약을 유지해도 된다 |
| 내부 이름은 길고, 외부는 `"PW"` 같은 짧은 code가 이미 정해져 있다 | `code`를 별도 필드로 두고 DB/JSON 매핑을 명시한다 |
| DB는 내부 이름으로 저장해도 되지만 외부 API는 code를 써야 한다 | DB 계약과 JSON 계약을 분리해서 문서화한다 |
| 나중에 enum 이름을 리팩터링할 가능성이 크다 | 외부 계약을 `code`로 고정하고, 저장/직렬화 어댑터가 그 값을 쓰는지 확인한다 |

초급자 기준 안전한 순서는 이렇다.

1. 내부에서 무엇을 비교할지 정한다
2. DB에 어떤 값을 남길지 정한다
3. JSON에 어떤 값을 내보낼지 정한다
4. 셋이 같다고 가정하지 말고, 같게 만들 것인지 따로 둘 것인지 선택한다

## 다음에 이어서 보면 좋은 질문

- "`EnumType.STRING`이 왜 `code`가 아니라 `name()` 쪽으로 읽히는가?"
- "DB는 `code`, JSON은 `name`으로 다르게 가져가도 괜찮은가?"
- "`fromCode(...)`에서 unknown value를 실패로 둘지 `UNKNOWN`으로 흡수할지 어떻게 정하나?"

이 질문은 각각 다음 문서로 이어진다.

- [Enum Persistence, JSON, and Unknown Value Evolution](./enum-persistence-json-unknown-value-evolution.md)
- [Enum 상수 비교와 문자열 payload 비교를 언제 나눌까](./enum-string-boundary-bridge.md)
- [JDBC/JPA/MyBatis 기초](../../database/jdbc-jpa-mybatis-basics.md)

## 한 줄 정리

enum 내부 이름과 외부 `code`를 분리했다면, Java 비교 규칙과 DB/JSON 저장 규칙도 자동으로 같지 않다. 어떤 값을 외부 계약으로 쓸지 DB와 JSON 출구마다 명시해야 덜 헷갈린다.
