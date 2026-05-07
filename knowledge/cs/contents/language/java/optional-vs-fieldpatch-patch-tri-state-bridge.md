---
schema_version: 3
title: Optional vs FieldPatch PATCH Tri State Bridge
concept_id: language/optional-vs-fieldpatch-patch-tri-state-bridge
canonical: true
category: language
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 91
mission_ids:
- missions/spring-roomescape
- missions/lotto
review_feedback_tags:
- patch
- optional
- dto
aliases:
- Optional vs FieldPatch PATCH tri-state bridge
- PATCH Optional tri-state misunderstanding
- missing null present FieldPatch
- partial update null missing difference
- Optional two state vs tri state
- PATCH DTO Optional FieldPatch 차이
symptoms:
- PATCH DTO에서 field missing, explicit null, value present 세 상태를 Optional.empty 하나로 눌러 기존 값 유지와 값 삭제를 구분하지 못해
- 조회 결과의 있음 없음 문제와 partial update의 유지 삭제 변경 의도 문제를 모두 Optional로 처리하려 해 service 적용 의미가 흐려져
- JSON binding이나 custom deserializer 설정 없이 Optional<T>만 두면 PATCH tri-state가 자동 표현된다고 오해해
intents:
- comparison
- design
- troubleshooting
prerequisites:
- language/patch-tri-state-field-primer
- language/java-optional-basics
- language/optional-field-parameter-antipattern-card
next_docs:
- language/json-null-missing-unknown-field-schema-evolution
- language/primitive-vs-wrapper-fields-json-payload-semantics
- software-engineering/dto-vo-entity-basics
linked_paths:
- contents/language/java/patch-tri-state-field-primer.md
- contents/language/java/java-optional-basics.md
- contents/language/java/optional-field-parameter-antipattern-card.md
- contents/language/java/json-null-missing-unknown-field-schema-evolution.md
- contents/language/java/primitive-vs-wrapper-fields-json-payload-semantics.md
- contents/software-engineering/dto-vo-entity-basics.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
confusable_with:
- language/patch-tri-state-field-primer
- language/optional-field-parameter-antipattern-card
- language/json-null-missing-unknown-field-schema-evolution
forbidden_neighbors: []
expected_queries:
- PATCH DTO에서 Optional과 FieldPatch는 missing null present 세 상태 때문에 어떻게 갈라져?
- Optional.empty와 요청 필드 missing은 왜 같은 의미가 아닐 수 있어?
- PATCH에서 nickname 유지 삭제 변경을 FieldPatch tri-state로 모델링하는 이유를 설명해줘
- Optional은 조회 결과의 있음 없음에는 맞지만 partial update에는 부족할 수 있다는 뜻이 뭐야?
- JSON null missing present를 Optional 단독으로 구분할 수 있는지 beginner 다음 단계로 알려줘
contextual_chunk_prefix: |
  이 문서는 Optional의 two-state absence와 PATCH DTO의 missing/null/present tri-state를 FieldPatch 모델로 구분하는 intermediate chooser다.
  Optional vs FieldPatch, PATCH tri-state, missing null present, partial update 질문이 본 문서에 매핑된다.
---
# `Optional` vs `FieldPatch`: PATCH tri-state에서 왜 갈라지나

> 한 줄 요약: `Optional`은 보통 "값 있음 / 없음" 2칸을 드러내는 데 잘 맞지만, PATCH DTO는 자주 `missing` / explicit `null` / 값 있음 3칸이 필요해서 `FieldPatch` 같은 tri-state 모델로 한 단계 올라간다.

**난이도: 🟡 Intermediate**

관련 문서:

- [PATCH DTO에서 `missing` / explicit `null` / 값 있음 결정 카드](./patch-tri-state-field-primer.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
- [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- [Spring Controller에서 Entity를 바로 반환하지 않고 DTO를 두는 이유](../../spring/spring-controller-entity-return-vs-dto-return-primer.md)
- [Java Deep Dive Catalog](./README.md)

retrieval-anchor-keywords: optional vs fieldpatch, patch optional 왜 안 되나, patch tri-state bridge, optional tri-state misunderstanding, missing null present java, fieldpatch vs optional patch dto, optional로 patch 되나요, patch dto optional bridge, partial update null missing difference, fieldpatch 뭐예요, optional two state vs tri state, patch beginner next step, optional explicit null 왜 부족해, json patch missing keep clear, what is fieldpatch

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "PATCH DTO에 `Optional`을 쓰면 필드 유지/삭제/변경이 다 표현되나요?" | roomescape 회원 정보 수정이나 lotto 설정 변경에서 missing/null/value를 구분해야 하는 요청 | 조회 결과의 있음/없음과 부분 수정 의도의 3상태를 분리한다 |
| "`Optional.empty()`랑 JSON 필드 누락이 같은 뜻 아닌가요?" | nickname을 안 보낸 경우와 `null`로 지우려는 경우가 같은 service 분기로 들어가는 코드 | missing은 유지, explicit null은 삭제일 수 있다는 적용 의미를 잡는다 |
| "custom deserializer 없이도 tri-state가 자동으로 되나요?" | Jackson 바인딩 기본값만 믿고 PATCH 의미를 service에서 복원하려는 구현 | JSON binding 설정과 DTO 모델이 실제로 세 상태를 보존하는지 확인한다 |

## 핵심 개념

이 브리지는 beginner primer 다음 칸이다.

- `Optional<T>`는 보통 "값이 있나, 없나"를 말한다
- PATCH DTO는 자주 "그 필드를 안 보냈나, `null`로 비우려 하나, 새 값을 보냈나"를 말해야 한다

즉 둘 다 "없음" 주변 문제를 다루지만, 질문의 칸 수가 다르다.

짧게 외우면 이렇게 자르면 된다.

> 조회 결과의 있음/없음은 `Optional`, 부분 수정 의도의 유지/삭제/변경은 `FieldPatch` 쪽 질문이다.

여기서 중요한 caveat도 하나 있다.
JSON 바인더 설정이나 custom deserializer를 붙이면 다른 모델을 만들 수는 있다.
하지만 beginner가 `Optional<T>` 단독만 보고 PATCH tri-state가 자동으로 표현된다고 읽는 것은 보통 오해다.

## 한눈에 보기

| 지금 표현하려는 것 | `Optional<T>`가 잘 맞는가 | `FieldPatch<T>`가 잘 맞는가 | 이유 |
|---|---|---|---|
| 회원 한 명 조회 결과가 없을 수 있다 | 예 | 보통 과하다 | 단건 결과의 있음/없음 2칸이면 충분하다 |
| PATCH에서 닉네임을 유지할지, 지울지, 바꿀지 보낸다 | 보통 부족하다 | 예 | `missing` / `null` / 값 있음 3칸을 구분해야 할 수 있다 |
| 선택 필드가 있는 생성 요청이다 | 상황에 따라 다르다 | 보통 아니다 | create는 PATCH처럼 "안 건드림" 상태가 필요 없을 때가 많다 |
| "왜 없는지"까지 중요하다 | 부족할 수 있다 | 부족할 수 있다 | `enum`이나 상태 타입이 더 직접적일 수 있다 |

한 줄 차이는 이것이다.

- `Optional.empty()`는 보통 "값이 없다"
- `Missing`은 보통 "이번 요청에서 그 필드를 안 건드린다"

둘은 비슷해 보여도 서비스 적용 의미가 다르다.

## 왜 `Optional`이 PATCH tri-state를 끝내지 못하나

PATCH에서 초보자가 자주 놓치는 질문은 "값이 있나 없나"보다 "이번 요청이 기존 값을 어떻게 다루라고 말하나"다.

예를 들어 `nickname` 필드 하나만 봐도 보통 세 요청이 갈린다.

- `{}`: 기존 닉네임 유지
- `{"nickname": null}`: 닉네임 비우기
- `{"nickname": "neo"}`: 닉네임 변경

그런데 `Optional<String>`은 보통 아래 둘만 직접 말한다.

- 값이 있다
- 값이 없다

그래서 `Optional.empty()` 하나에 아래 둘이 같이 눌러 들어갈 수 있다.

- 필드를 안 보냄
- `null`을 명시적으로 보냄

PATCH에서는 이 둘이 같은 뜻이 아닐 수 있으므로, `Optional`만으로는 의도가 평평해질 수 있다.

## 코드로 비교하면 차이가 더 선명하다

`Optional`로 PATCH를 읽으려 하면 보통 이렇게 된다.

```java
public record UpdateProfileRequest(Optional<String> nickname) {}
```

이 타입만 보면 service는 `nickname`이 비어 있을 때 아래 둘을 구분하기 어렵다.

- 요청에 필드가 없었는가
- 요청이 `nickname: null`을 보냈는가

반면 tri-state 모델은 이름부터 갈라 둔다.

```java
public sealed interface FieldPatch<T> permits Missing, NullValue, Present {}

public record Missing<T>() implements FieldPatch<T> {}

public record NullValue<T>() implements FieldPatch<T> {}

public record Present<T>(T value) implements FieldPatch<T> {}
```

```java
public record UpdateProfileRequest(FieldPatch<String> nickname) {}
```

service는 그제야 "없다"가 아니라 "유지 / 비우기 / 변경"으로 읽을 수 있다.

```java
return switch (request.nickname()) {
    case Missing<String> ignored -> profile;
    case NullValue<String> ignored -> profile.clearNickname();
    case Present<String> present -> profile.changeNickname(present.value());
};
```

핵심은 문법이 아니라 branch 이름이다.
`Optional.empty()`는 absence를 말하지만, `Missing`은 update intent를 말한다.

## 흔한 오해와 함정

- "`Optional<String>`도 비어 있으면 유지, 값 있으면 변경으로 읽으면 되지 않나요?"
  그러면 explicit `null`로 비우려는 요청이 사라질 수 있다.
- "`Optional<Optional<String>>`로 한 칸 더 감싸면 되지 않나요?"
  이론적으로 상태 수는 늘지만, beginner와 intermediate 단계에서는 읽기 비용이 너무 커지고 DTO contract가 더 흐려지기 쉽다.
- "`FieldPatch`를 모든 DTO에 써야 하나요?"
  아니다. create나 replace 성격 요청은 보통 plain field나 value object가 더 자연스럽다. PATCH 같은 partial update 경계에서만 주로 쓴다.
- "`Optional`이 무조건 나쁜가요?"
  아니다. repository 조회 결과나 계산 결과처럼 단건 없음 표현에는 여전히 좋은 도구다.
- "Jackson이 `Optional`을 잘 처리하니까 PATCH도 괜찮지 않나요?"
  라이브러리 지원과 비즈니스 의미는 다르다. 바인딩이 된다는 사실만으로 `missing`과 explicit `null` 의미가 저절로 분리되지는 않는다.

## 다음에 이렇게 고르면 덜 헷갈린다

1. "조회 결과가 없을 수 있는가?"를 묻는 중이면 `Optional`을 먼저 본다.
2. "이번 수정 요청이 유지/삭제/변경 중 무엇인가?"를 묻는 중이면 `FieldPatch` 같은 tri-state 모델을 먼저 본다.
3. "없음의 이유가 무엇인가?"까지 중요하면 `Optional`이나 `FieldPatch`보다 상태 타입을 검토한다.

이렇게 자르면 `Optional`과 `FieldPatch`가 경쟁 관계가 아니라 서로 다른 경계에서 쓰는 도구라는 점이 보인다.

## 더 깊이 가려면

- PATCH tri-state의 첫 멘탈 모델부터 다시 붙이려면 [PATCH DTO에서 `missing` / explicit `null` / 값 있음 결정 카드](./patch-tri-state-field-primer.md)
- `Optional` 자체의 기본 용도와 anti-pattern을 다시 묶으려면 [Java Optional 입문](./java-optional-basics.md)과 [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- JSON 경계에서 `null`, missing, unknown field가 왜 달라지는지 더 깊게 보려면 [JSON `null`, Missing Field, Unknown Property, and Schema Evolution](./json-null-missing-unknown-field-schema-evolution.md)
- wrapper/primitive 선택이 PATCH 의미와 어떻게 이어지는지 보려면 [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
- DTO와 도메인 역할 분리를 다시 고정하려면 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)

## 한 줄 정리

`Optional`은 보통 단건 값의 있음/없음을 말하고, `FieldPatch`는 PATCH에서 필드를 유지할지 비울지 바꿀지를 말하므로, 둘은 비슷해 보여도 해결하는 질문이 다르다.
