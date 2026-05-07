---
schema_version: 3
title: 클린 코드 기초
concept_id: software-engineering/clean-code-basics
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids:
- missions/baseball
- missions/blackjack
- missions/lotto
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- readable-naming-small-functions
- abstraction-level-layering
- clean-code-vs-refactoring
aliases:
- clean code basics
- 클린 코드 기초
- 읽기 좋은 코드
- 변수명 짓는 법
- 함수 하나의 일
- 매직 넘버 제거
- 주석보다 코드
- 코드 가독성
symptoms:
- 클린 코드를 예쁘게 짧게 쓰는 문제로만 이해하고 의도 전달과 수정 비용을 놓치고 있어
- temp, data, result 같은 이름으로 역할을 감춰 코드 리뷰에서 의미 질문을 받고 있어
- 메서드 추출로 읽기는 나아졌지만 레이어 책임 분리는 여전히 흐린 상태를 구분하지 못하고 있어
intents:
- definition
- design
- troubleshooting
prerequisites:
- software-engineering/oop-design-basics
- software-engineering/readable-code-layering-test-feedback-loop-primer
next_docs:
- software-engineering/refactoring-basics
- software-engineering/layered-architecture-basics
- software-engineering/test-strategy-basics
- software-engineering/solid-principles-basics
linked_paths:
- contents/software-engineering/readable-code-layering-test-feedback-loop-primer.md
- contents/software-engineering/refactoring-basics.md
- contents/software-engineering/layered-architecture-basics.md
- contents/software-engineering/test-strategy-basics.md
- contents/software-engineering/solid-principles-basics.md
confusable_with:
- software-engineering/refactoring-basics
- software-engineering/layered-architecture-basics
- software-engineering/test-strategy-basics
forbidden_neighbors: []
expected_queries:
- 클린 코드는 왜 동작하는 코드보다 읽고 수정하기 쉬운 코드에 초점을 둬?
- 변수명과 메서드명은 어떤 기준으로 의도를 드러내야 해?
- 메서드가 너무 길 때 단계 이름을 드러내는 추출은 어떻게 시작해?
- 주석보다 코드로 의도를 표현한다는 말은 언제 맞고 언제 주석이 필요해?
- 클린 코드 문제와 레이어 책임 문제를 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Clean Code beginner primer로, intent-revealing names, small functions, abstraction level, magic number removal, comments for why, readability vs layering vs refactoring을 분리한다.
  클린 코드, 변수명, 함수 분리, 매직 넘버, 주석, readable code, Controller가 너무 많은 책임 같은 자연어 질문이 본 문서에 매핑된다.
---
# 클린 코드 기초 (Clean Code Basics)

> 한 줄 요약: 클린 코드는 의도를 드러내는 이름, 작은 함수, 일관된 추상화 수준으로 다음 사람이 바로 읽고 수정할 수 있는 코드다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "`data`, `result`, `temp`가 많다는 리뷰를 받았어요" | lotto 당첨 통계나 roomescape 예약 결과를 임시 변수명으로만 전달하는 코드 | 이름이 역할과 의도를 드러내는지 먼저 본다 |
| "메서드가 긴데 어디서 나눠야 할지 모르겠어요" | baseball 한 턴 처리나 shopping-cart checkout이 한 method 안에서 단계별로 길어지는 구조 | 단계 이름이 보이는 단위로 한 번만 추출한다 |
| "Controller가 너무 많은 걸 아는 것도 클린 코드 문제인가요?" | request parsing, domain rule, repository call, response mapping이 controller에 모인 코드 | 표현 문제와 layer responsibility 문제를 구분한다 |

**난이도: 🟢 Beginner**

관련 문서:

- [읽기 좋은 코드, 레이어 분리, 테스트 피드백 루프 입문](./readable-code-layering-test-feedback-loop-primer.md)
- [리팩토링 기초](./refactoring-basics.md)
- [계층형 아키텍처 기초](./layered-architecture-basics.md)
- [테스트 전략 기초](./test-strategy-basics.md)
- [SOLID 원칙 기초](./solid-principles-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)
- [design-pattern 카테고리 인덱스](../design-pattern/README.md)

retrieval-anchor-keywords: clean code basics, 클린 코드 입문, 네이밍 규칙, 함수 크기 기준, 가독성 기초, 코드 가독성 뭐예요, 변수명 짓는 법, 매직 넘버 없애기, 클린 코드 처음 배우는데, 주석 쓰는 법, beginner clean code, 함수 하나의 일, clean code basics basics, clean code basics beginner, clean code basics intro

## 먼저 보는 20초 기준

처음에는 "예쁘게 쓰기"보다 아래 한 줄로 잡으면 된다.

**클린 코드 = 다음 사람이 `왜 이 줄이 필요한지`를 바로 읽을 수 있는 코드**

| 들리는 말 | 먼저 붙일 이름 | 첫 행동 |
|---|---|---|
| "이름이 안 읽혀요" | 표현 문제 | `temp`, `data` 같은 이름을 역할이 드러나는 이름으로 바꾼다 |
| "메서드가 너무 길어요" | 읽기 문제 | 단계 이름이 보이도록 한 번만 추출한다 |
| "Controller가 너무 많은 걸 알아요" | 레이어 문제도 섞인 상태 | 이름 정리 전에 입력, 규칙, 저장 자리를 먼저 가른다 |

- 짧게 외우면 `이름 -> 표현`, `길이 -> 단계`, `많이 안다 -> 레이어`다.

## 핵심 개념

클린 코드(Clean Code)란 다른 사람이 수정하기 쉬운 코드를 뜻한다. 동작하는 코드와 좋은 코드는 다르다. 코드는 한 번 작성되지만 수십 번 읽힌다. 즉, **읽는 비용**이 쓰는 비용보다 훨씬 크다.

입문자가 가장 많이 헷갈리는 것은 "좋은 이름이 무엇인가"다. 좋은 이름은 선언 위치를 찾지 않아도 무엇인지, 왜 쓰이는지 알 수 있는 이름이다.

## 한눈에 보기

| 원칙 | 나쁜 예 | 좋은 예 |
|---|---|---|
| 의도 드러내는 이름 | `int d` | `int elapsedDays` |
| 매직 넘버 제거 | `if (age > 19)` | `if (age > ADULT_AGE)` |
| 함수는 한 가지 일 | `saveAndSendEmail()` | `save()` + `sendEmail()` |
| 짧은 함수 | 100줄짜리 메서드 | 10줄 이하, 단일 목적 |
| 의미 있는 주석 | `// i 증가` | 이름 자체가 설명이 되도록 |

## 같은 주문 생성 예시로 보는 첫 pass

처음부터 구조를 다 뜯지 말고, **이름 1개와 단계 1개만 읽히게 만드는 pass**로 보면 안전하다.

| 코드에서 보이는 장면 | 바로 할 수 있는 클린 코드 pass | 아직 같이 하지 않을 것 |
|---|---|---|
| `temp`, `data`, `result`가 섞여 있다 | `orderRequest`, `savedOrder`, `createdOrderId`처럼 역할이 보이는 이름으로 바꾼다 | 응답 필드를 새로 추가하기 |
| `create()` 안에 검증, 저장, 응답 조립이 다 있다 | `validateOrder()`, `saveOrder()`, `toResponse()`처럼 단계 이름을 드러낸다 | 재고 정책 자체를 바꾸기 |
| 주석으로 `// 검증`, `// 저장`을 나눠 둔다 | 주석 대신 메서드/변수 이름으로 단계를 드러낸다 | Controller에서 하던 규칙을 아무 기준 없이 Service로 옮기기 |

- 이 문서의 초점은 "읽히게 만들기"다.
- 책임 위치까지 바뀌기 시작하면 [계층형 아키텍처 기초](./layered-architecture-basics.md)로 이어서 본다.
- 정리 전에 동작을 고정할 테스트가 필요하면 [테스트 전략 기초](./test-strategy-basics.md), 작은 정리 순서를 보고 싶으면 [리팩토링 기초](./refactoring-basics.md)로 넘어간다.

## 상세 분해

**이름 짓기**

변수명, 메서드명, 클래스명은 맥락을 담아야 한다. `getList()`보다 `getActiveMemberList()`가 낫다. 불린 변수는 `isValid`, `hasPermission`처럼 질문 형태로 짓는다.

**함수는 작게**

함수가 길어질수록 "이 함수가 하는 일이 뭔가"를 파악하는 시간이 늘어난다. 한 함수가 하는 일은 하나여야 한다. 함수 이름에 `and`가 필요하다면 두 개로 나눌 신호다.

**추상화 수준 통일**

함수 내부에서 고수준(비즈니스 로직)과 저수준(루프, IO)이 섞이면 읽기 어려워진다. 같은 함수 안에서는 같은 수준의 추상화를 유지한다.

**주석보다 코드**

주석은 코드가 말하지 못하는 '왜(why)'를 설명할 때 쓴다. '무엇을(what)' 하는지는 좋은 이름과 구조로 표현한다. 코드가 바뀔 때 주석이 따라가지 못하면 오히려 혼란을 준다.

## 자주 헷갈리는 말 빠르게 구분하기

초심자는 가독성 문제와 레이어 문제, 리팩토링 문제를 한 번에 묶어 듣기 쉽다. 아래처럼 먼저 분리하면 다음 문서가 바로 정해진다.

| 지금 하려는 일 | 이 문서에서 붙일 이름 | 바로 다음 문서 |
|---|---|---|
| `temp`, `data` 같은 이름을 읽히게 바꾸고 싶다 | 클린 코드 | [리팩토링 기초](./refactoring-basics.md) |
| 메서드를 잘라 `검증 -> 저장 -> 응답` 단계를 드러내고 싶다 | 클린 코드 + 리팩토링 | [리팩토링 기초](./refactoring-basics.md) |
| Controller가 중복 검사, 저장, 응답 조립을 다 한다 | 레이어 문제 | [계층형 아키텍처 기초](./layered-architecture-basics.md) |
| 이름 정리 전에 테스트부터 잠그고 싶다 | 안전망 문제 | [테스트 전략 기초](./test-strategy-basics.md) |

- stop rule도 단순하다: `다음에 읽을 문서 1개`가 정해졌다면 이 문서의 입문 역할은 끝이다.

## 흔한 오해와 함정

- "주석이 많으면 좋은 코드다"라는 오해가 있다. 주석이 많다는 것은 코드가 스스로 의도를 드러내지 못한다는 신호일 수 있다. 이름과 구조를 먼저 개선하고, 불가피한 경우에만 주석을 쓴다.
- "짧은 코드가 클린 코드다"라고 오해하기도 한다. 한 줄에 모든 것을 압축한 코드는 읽기 어렵다. 읽는 비용이 낮은 코드가 클린 코드다.
- "이름은 길수록 좋다"도 아니다. 불필요하게 긴 이름은 오히려 가독성을 낮춘다. 맥락이 충분히 드러나는 가장 짧은 이름이 최선이다.
- "메서드만 잘게 쪼개면 레이어 문제도 해결된다"는 오해가 있다. 이름은 읽히더라도 Controller가 규칙과 저장을 함께 알면 구조 문제는 그대로 남는다.

## 실무에서 쓰는 모습

우아한형제들 코드 리뷰에서 자주 나오는 피드백 중 하나가 "이 변수명이 무엇을 의미하는지 알 수 없어요"다. `result`, `temp`, `data` 같은 이름은 컨텍스트 없이는 의미를 알 수 없다. 코드 리뷰를 받기 전에 스스로 "이 이름을 처음 보는 팀원이 이해할 수 있는가"를 확인해보는 것이 좋다.

## 더 깊이 가려면

- [리팩토링 기초](./refactoring-basics.md) — 클린 코드 원칙을 기존 코드에 적용하는 절차
- [SOLID 원칙 기초](./solid-principles-basics.md) — 함수/클래스 분리 원칙의 이론적 기반

## 면접/시니어 질문 미리보기

- "주석이 필요한 상황은 언제인가요?" — 비즈니스 규칙의 배경(왜 이렇게 결정했는지), 서드파티 제약, 알고리즘의 비직관적인 이유 등 코드로 표현하기 어려운 '왜'를 설명할 때 주석이 가치 있다.
- "함수를 얼마나 작게 나눠야 하나요?" — 절대적 기준은 없지만, "이 함수 이름이 내부 구현을 정확히 설명하는가"를 질문해보면 된다. 함수 이름과 구현이 불일치하면 분리 신호다.
- "클린 코드와 성능은 항상 트레이드오프인가요?" — 대부분의 경우 클린 코드가 성능과 충돌하지 않는다. 성능 최적화가 필요한 경우에만 가독성을 의도적으로 희생하고 반드시 주석으로 이유를 남긴다.

## 한 줄 정리

클린 코드는 동작하는 코드가 아니라 다음 사람이 바로 이해하고 수정할 수 있는 코드이며, 이름과 함수 크기가 그 시작점이다.
