---
schema_version: 3
title: PATCH Tri State Field Primer
concept_id: language/patch-tri-state-field-primer
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 92
mission_ids:
- missions/spring-roomescape
- missions/lotto
review_feedback_tags:
- patch
- dto
- null-handling
aliases:
- PATCH tri state field primer
- PATCH missing explicit null value beginner
- JSON patch null missing present
- FieldPatch primer
- partial update 유지 비우기 변경
- PATCH DTO tri-state 결정 카드
symptoms:
- PATCH 요청에서 missing과 explicit null을 모두 값 없음으로 읽어 기존 값 유지와 값 비우기를 같은 동작으로 처리해
- Java DTO의 String field 하나로 missing, null, present 세 상태를 모두 표현하려다 JSON binding 경계에서 의도를 잃어
- create request와 PATCH request를 같은 DTO 의미로 보아 partial update의 유지 삭제 변경 contract를 분리하지 못해
intents:
- definition
- design
- troubleshooting
prerequisites:
- language/json-null-missing-unknown-field-schema-evolution
- software-engineering/dto-vo-entity-basics
next_docs:
- language/optional-vs-fieldpatch-patch-tri-state-bridge
- language/request-dto-to-value-object-boundary-primer
- spring/controller-entity-return-vs-dto-return-primer
linked_paths:
- contents/language/java/optional-vs-fieldpatch-patch-tri-state-bridge.md
- contents/language/java/request-dto-to-value-object-boundary-primer.md
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/java-equality-identity-basics.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
confusable_with:
- language/optional-vs-fieldpatch-patch-tri-state-bridge
- language/json-null-missing-unknown-field-schema-evolution
- language/primitive-vs-wrapper-fields-json-payload-semantics
forbidden_neighbors: []
expected_queries:
- PATCH DTO에서 missing explicit null value 세 상태를 beginner 기준으로 설명해줘
- PATCH에서 필드가 없으면 유지하고 null이면 비우고 값이 있으면 변경한다는 표를 보고 싶어
- JSON payload가 Java DTO로 바인딩될 때 missing과 explicit null이 왜 섞일 수 있어?
- partial update에서 String field 하나만으로 tri-state를 표현하면 어떤 위험이 있어?
- FieldPatch Missing NullValue Present 모델은 PATCH 서비스 적용 의미를 어떻게 분리해?
contextual_chunk_prefix: |
  이 문서는 PATCH DTO의 missing, explicit null, present value 세 상태를 유지, 비우기, 변경 의도로 읽는 beginner primer다.
  PATCH tri-state, missing vs null, FieldPatch, partial update, DTO boundary 질문이 본 문서에 매핑된다.
---
# PATCH DTO에서 `missing` / explicit `null` / 값 있음 결정 카드

> 한 줄 요약: PATCH의 JSON이 Java DTO로 들어올 때 beginner가 먼저 잡아야 할 표는 `missing = 유지`, `explicit null = 비우기`, `value = 변경`이다. 이 3칸을 구분하지 못하면 부분 수정 의도가 DTO 경계에서 바로 섞인다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java Deep Dive Catalog](./README.md)
- [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)
- [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- [Spring Controller에서 Entity를 바로 반환하지 않고 DTO를 두는 이유](../../spring/spring-controller-entity-return-vs-dto-return-primer.md)

retrieval-anchor-keywords: patch dto tri-state, patch missing explicit null value beginner, missing vs explicit null patch, partial update beginner java, json to java patch boundary, fieldpatch primer, patch dto 뭐예요, patch null 왜 구분해, patch missing keep value, patch beginner basics, dto partial update 처음, json patch null missing beginner, update dto clear field, present value patch primer, what is patch tri-state

## 핵심 개념

처음에는 PATCH를 이렇게 번역하면 된다.

- 필드가 아예 없음: 기존 값을 그대로 둔다
- 필드가 `null`: 값을 비우려는 의도일 수 있다
- 필드에 새 값이 있음: 그 값으로 바꾸려는 의도다

즉 PATCH는 "새 객체 전체를 보내는 요청"보다
"기존 객체에서 어느 칸을 어떻게 만질지 보내는 요청"에 가깝다.

초보자가 가장 많이 섞는 지점도 여기다.
`null`과 missing을 둘 다 "값이 없네"로 읽어 버리면,
유지와 삭제가 같은 뜻이 되어 버린다.

짧게 외우면 이 한 줄이면 충분하다.

> PATCH의 첫 질문은 "값이 뭐냐"보다 "건드리지 말라는 건지, 지우라는 건지, 바꾸라는 건지"다.

## 결정 카드

PATCH에서는 JSON 모양과 Java에서 읽는 뜻을 같이 봐야 덜 헷갈린다.

| JSON payload | Java 쪽에서 먼저 읽을 뜻 | 서비스에서 보통 하는 일 |
|---|---|---|
| `{}` | `nickname`이 이번 요청에 아예 없음 | 기존 값 유지 |
| `{"nickname": null}` | `nickname`을 명시적으로 비우려는 요청일 수 있음 | clear 또는 remove |
| `{"nickname": "neo"}` | 새 값이 실제로 들어옴 | change |

위 세 요청은 "값이 없네"로 한 번에 묶으면 안 된다.
PATCH beginner의 첫 질문은 "값이 뭐냐"보다 "유지냐, 비우기냐, 변경이냐"다.

## 왜 JSON -> Java 경계에서 바로 섞일까

beginner가 흔히 처음 쓰는 DTO는 이런 모양이다.

```java
public record UpdateProfileRequest(String nickname) {}
```

문제는 `String nickname` 하나만 보면 아래 둘이 Java 안에서 비슷하게 보여질 수 있다는 점이다.

- 클라이언트가 `nickname` 필드를 아예 안 보냈다
- 클라이언트가 `nickname: null`을 명시적으로 보냈다

JSON 바인딩 방식이나 DTO 설계에 따라 둘 다 결국 `null`처럼 취급되면 service는 의도를 잃는다.

- "기존 닉네임 유지"를 원했는데 지워 버릴 수 있다
- "명시적으로 비우기"를 원했는데 그냥 무시할 수 있다

즉 문제의 핵심은 `String`이 나쁜 타입이라는 뜻이 아니라,
PATCH가 필요한 표현 공간이 `String 하나`보다 넓다는 데 있다.

## beginner는 tri-state를 이렇게 읽으면 된다

처음부터 복잡한 직렬화 구현을 외울 필요는 없다.
먼저 "한 필드에 상태가 3개 있다"는 감각만 잡으면 된다.

| 상태 | 뜻 | 서비스 적용 감각 |
|---|---|---|
| `Missing` | 안 보냄 | 그대로 둔다 |
| `NullValue` | 명시적 `null` | 비운다 |
| `Present("neo")` | 값 보냄 | 바꾼다 |

코드 모양은 아래 정도로만 읽어도 충분하다.

```java
public sealed interface FieldPatch<T> permits Missing, NullValue, Present {}

public record Missing<T>() implements FieldPatch<T> {}

public record NullValue<T>() implements FieldPatch<T> {}

public record Present<T>(T value) implements FieldPatch<T> {}
```

핵심은 문법이 아니라 이름이다.

- `Missing`은 "값이 없다"가 아니라 "이번엔 안 건드림"이다
- `NullValue`는 "실수로 비었다"가 아니라 "명시적으로 비우기"일 수 있다
- `Present`는 "새 값이 실제로 왔다"는 뜻이다

## DTO 결정 카드를 코드로 옮기면

프로필 수정 요청을 아주 작게 보면 이런 흐름이다.

```java
public record UpdateProfileRequest(FieldPatch<String> nickname) {}
```

```java
public Profile apply(UpdateProfileRequest request, Profile profile) {
    return switch (request.nickname()) {
        case Missing<String> ignored -> profile;
        case NullValue<String> ignored -> profile.clearNickname();
        case Present<String> present -> profile.changeNickname(present.value());
    };
}
```

여기서 beginner가 봐야 할 포인트는 세 가지다.

- `Missing`이면 기존 객체를 그대로 둔다
- `NullValue`면 clear 메서드처럼 "삭제 의도"를 따로 읽는다
- `Present`면 그때만 새 값을 검증하고 바꾼다

이후에 `Present<String>`을 바로 domain으로 넘기지 않고 `new Nickname(...)` 같은 값 객체로 올리면,
공백 문자열 처리나 같은 값 판단을 한곳에 모을 수 있다.
즉 PATCH 결정 카드와 value object 경계는 따로 노는 이야기가 아니다.

## 흔한 오해와 함정

- "`null`이면 그냥 값이 없는 거 아닌가요?"
  PATCH에서는 아니다. 안 보낸 것과 지우려는 것은 다른 요청일 수 있다.
- "그럼 모든 DTO를 다 `FieldPatch`로 감싸야 하나요?"
  아니다. 전체 생성(create) 요청처럼 필드가 항상 와야 하는 모델은 보통 필요 없다.
- "`Optional<String>`이면 되지 않나요?"
  beginner 관점에선 보통 부족하다. `Optional`은 "있음/없음" 2칸에 더 가깝고, PATCH는 missing과 explicit `null`을 둘 다 구분해야 할 수 있다. 바로 다음 단계 비교는 [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)에서 보면 된다.
- "문자열 하나 바꾸는데 너무 복잡한 것 아닌가요?"
  필드를 적게 바꾸는 PATCH일수록 유지/삭제/변경이 더 중요해져서 오히려 작은 tri-state가 도움이 된다.

## 더 깊이 가려면

- raw DTO를 값 객체로 넘기는 감각은 [Request DTO에서 raw string을 값 객체로 올리는 경계 입문](./request-dto-to-value-object-boundary-primer.md)
- `Optional`이 왜 PATCH tri-state를 완전히 대체하지 못하는지 짧게 이어 보려면 [`Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나](./optional-vs-fieldpatch-patch-tri-state-bridge.md)
- 값 객체가 왜 `equals()`/`hashCode()`와 이어지는지는 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- `==`와 `equals()`를 먼저 분리하고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- primitive/wrapper가 JSON 의도를 얼마나 보존하는지는 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- `""`, blank, `null`, missing을 더 촘촘히 나누고 싶다면 [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
- DTO와 도메인 역할 분리는 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- Spring 요청/응답 DTO 감각은 [Spring Controller에서 Entity를 바로 반환하지 않고 DTO를 두는 이유](../../spring/spring-controller-entity-return-vs-dto-return-primer.md)

## 한 줄 정리

PATCH beginner의 첫 멘탈 모델은 `missing = 유지`, `explicit null = 비우기`, `value = 변경`이고, 이 3칸을 JSON -> Java DTO 경계에서 잃지 않아야 부분 수정 의도를 안전하게 읽을 수 있다.
