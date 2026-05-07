---
schema_version: 3
title: '접근 제한자 오해 미니 퀴즈: top-level vs member'
concept_id: language/java-access-modifier-top-level-member-mini-quiz
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- top-level-vs-member-scope
- nested-type-visibility
aliases:
- java access modifier top level member mini quiz basics
- java access modifier top level member mini quiz beginner
- java access modifier top level member mini quiz intro
- java basics
- beginner java
- 처음 배우는데 java access modifier top level member mini quiz
- java access modifier top level member mini quiz 입문
- java access modifier top level member mini quiz 기초
- what is java access modifier top level member mini quiz
- how to java access modifier top level member mini quiz
symptoms:
- top-level에서는 안 되는데 멤버에서는 되는 modifier가 자꾸 헷갈려
- private class를 본 기억이 있는데 왜 어떤 코드는 컴파일이 안 되는지 모르겠어
- 문제로 바로 확인하면서 접근 제한자 경계를 점검하고 싶어
intents:
- definition
prerequisites:
- language/java-access-modifiers-member-model-basics
- language/top-level-type-access-modifier-bridge
next_docs:
- language/java-access-modifier-boundary-lab
- language/java-package-import-boundary-basics
linked_paths:
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-access-modifiers-member-model-basics.md
- contents/language/java/java-access-modifier-boundary-lab.md
- contents/language/java/java-package-import-boundary-basics.md
- contents/data-structure/backend-data-structure-starter-pack.md
confusable_with:
- language/top-level-type-access-modifier-bridge
- language/java-access-modifier-boundary-lab
forbidden_neighbors:
- contents/language/java/top-level-type-access-modifier-bridge.md
- contents/language/java/java-package-boundary-quickcheck-card.md
- contents/language/java/java-access-modifier-boundary-lab.md
expected_queries:
- 접근 제한자 top-level이랑 member 구분 문제로 바로 확인하고 싶어
- private class가 되는 경우와 안 되는 경우를 퀴즈처럼 풀어보고 싶어
- protected interface가 왜 실패하는지 짧은 문제로 점검할 수 있을까
- nested record는 protected가 되는데 top-level record는 왜 안 되는지 연습하고 싶어
- 컴파일 성공 실패를 예측하는 접근 제한자 입문 문제를 찾고 있어
contextual_chunk_prefix: |
  이 문서는 Java 입문자가 파일 최상단 선언과 클래스 안쪽 선언을 구분하며
  top-level에서는 막히고 member나 nested type에서는 열리는 modifier 경계를
  예측형 문제로 처음 잡는 primer다. private class를 본 기억이 왜 맞기도
  틀리기도 한가, protected interface는 왜 실패하나, nested record는 왜
  허용되나, 컴파일 전에 위치만 보고 성공 실패를 가르고 싶다 같은 자연어
  paraphrase가 본 문서의 위치별 접근 제한자 판단에 매핑된다.
---
# 접근 제한자 오해 미니 퀴즈: top-level vs member

> 한 줄 요약: `private`/`protected`가 "항상 안 된다"가 아니라, **파일 최상단(top-level)에서는 안 되고 클래스 멤버에서는 될 수 있다**는 경계를 5문항 예측형으로 짧게 점검하는 beginner drill이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java access modifier top level member mini quiz basics, java access modifier top level member mini quiz beginner, java access modifier top level member mini quiz intro, java basics, beginner java, 처음 배우는데 java access modifier top level member mini quiz, java access modifier top level member mini quiz 입문, java access modifier top level member mini quiz 기초, what is java access modifier top level member mini quiz, how to java access modifier top level member mini quiz
> 관련 문서:
> - [Language README: Java primer](../README.md#java-primer)
> - [Java Top-level 타입 접근 제한자 브리지](./top-level-type-access-modifier-bridge.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)

> retrieval-anchor-keywords: java access modifier top-level member mini quiz, java private protected top-level member practice, java top-level vs member private protected quiz, java top-level private protected compile error, java member private protected allowed, java access modifier prediction worksheet, java beginner access modifier drill, java top-level nested type confusion quiz, java private protected allowed where, 자바 접근 제한자 미니 퀴즈, 자바 top-level member private protected 가능 여부, 자바 top-level private protected 불가, 자바 멤버 private protected 가능, 자바 접근제한자 예측 문제

## 먼저 잡을 mental model

처음엔 문법 이름보다 위치만 먼저 자르면 된다.

- 파일 최상단 선언이면 top-level
- 클래스 안 선언이면 member

이때 초보자용 규칙은 2줄이면 충분하다.

- top-level 타입은 `public` 또는 package-private만 가능
- member는 `private`/`protected`도 가능

즉 `private`/`protected`를 보면 "이 modifier가 금지인가?"보다 먼저 **"지금 위치가 top-level인가, member인가?"** 를 묻는 습관이 중요하다.

## 10초 비교표

| 위치 | `private` | `protected` | 기억할 문장 |
|---|---|---|---|
| top-level 타입 | 불가 | 불가 | 파일 최상단은 둘 다 안 됨 |
| 필드/메서드/생성자 | 가능 | 가능 | 멤버는 둘 다 가능 |
| member class / nested type | 가능 | 가능 | 클래스 안이면 타입도 멤버 취급 |

## 5문항 예측형 미니 퀴즈

아래 각 선언이 **컴파일될지 먼저 예측**해 보자.

| 번호 | 선언 | 내 예측 |
|---|---|---|
| 1 | `private class User {}` |  |
| 2 | `protected interface Parser {}` |  |
| 3 | `class Outer { private class Helper {} }` |  |
| 4 | `class Outer { protected static record Id(String value) {} }` |  |
| 5 | `class Outer { protected int count; }` |  |

## 정답

| 번호 | 컴파일 결과 | 이유 |
|---|---|---|
| 1 | 실패 | `User`가 파일 최상단 top-level 타입이라 `private` 불가 |
| 2 | 실패 | `Parser`가 top-level 타입이라 `protected` 불가 |
| 3 | 성공 | `Helper`는 `Outer` 안의 member class라 `private` 가능 |
| 4 | 성공 | nested `record`도 member type이므로 `protected` 가능 |
| 5 | 성공 | 필드는 멤버라 `protected` 가능 |

## 왜 3번과 4번이 헷갈리나

많이 틀리는 이유는 "`private class`를 본 적 있다"와 "`private class`는 안 된다"가 서로 섞이기 때문이다.

| 선언 위치 | 예시 | 결과 |
|---|---|---|
| top-level | `private class User {}` | 컴파일 실패 |
| 클래스 내부 | `class Outer { private class User {} }` | 컴파일 성공 |

`record`도 같다.

| 선언 위치 | 예시 | 결과 |
|---|---|---|
| top-level | `protected record Id(String value) {}` | 컴파일 실패 |
| 클래스 내부 | `class Outer { protected record Id(String value) {} }` | 컴파일 성공 |

핵심은 타입 종류가 아니라 위치다.

## 초보자가 자주 하는 오해

- `private`나 `protected`는 "타입에는 원래 못 붙는다"라고 외워 버린다
- top-level 규칙을 member에도 그대로 적용한다
- nested `class`는 멤버라고 알면서 nested `record`는 예외라고 착각한다

안전한 기억법:

- 파일 최상단이면 `public`/package-private만 생각한다
- 클래스 안이면 `private`/`protected`도 후보에 넣는다
- 새 문법처럼 보여도 `record`/`enum`/`interface`가 클래스 안에 있으면 member type으로 본다

## 다음 읽기

- top-level 규칙만 다시 1페이지로 정리: [Java Top-level 타입 접근 제한자 브리지](./top-level-type-access-modifier-bridge.md)
- 멤버 접근 제한자 큰 그림 복습: [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 패키지/상속 경계까지 손검증: [Access Modifier Boundary Lab](./java-access-modifier-boundary-lab.md)

## 한 줄 정리

`private`/`protected`가 "항상 안 된다"가 아니라, **파일 최상단(top-level)에서는 안 되고 클래스 멤버에서는 될 수 있다**는 경계를 5문항 예측형으로 짧게 점검하는 beginner drill이다.
