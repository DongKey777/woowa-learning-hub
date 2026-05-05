---
schema_version: 3
title: 'Spring `@ConditionalOnBean` vs `@ConditionalOnMissingBean` vs `@ConditionalOnSingleCandidate` 결정 가이드'
concept_id: spring/conditional-activation-annotation-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- conditional-activation-vs-injection
- auto-configuration-condition-choice
aliases:
- spring conditional annotation choice
- conditionalonbean missingbean singlecandidate 차이
- auto configuration 조건 뭐 붙여요
- starter bean 조건 선택
- boot 조건부 bean 등록 분기
- existing bean 있으면 어떤 조건
- spring activation annotation guide
symptoms:
- starter나 설정 bean을 만들 때 어떤 conditional annotation을 붙여야 할지 모르겠어요
- bean이 이미 있을 때 기본값을 물러나게 해야 하는지, 특정 선행 bean이 있어야 하는지 자꾸 섞여요
- 후보 bean이 여러 개인 상황에서 조건 통과와 실제 주입 선택을 같은 문제로 보고 있어요
intents:
- comparison
- design
- troubleshooting
prerequisites:
- spring/boot-autoconfiguration-basics
- spring/bean-registration-path-decision-guide
next_docs:
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
- spring/primary-qualifier-collection-injection
- spring/bean-registration-path-decision-guide
linked_paths:
- contents/spring/spring-conditionalonbean-activation-vs-di-candidate-selection-primer.md
- contents/spring/spring-conditionalonmissingbean-vs-primary-primer.md
- contents/spring/spring-conditionalonsinglecandidate-vs-primary-primer.md
- contents/spring/spring-primary-conditionalonmissingbean-bean-override-decision-guide.md
- contents/spring/spring-primary-qualifier-collection-injection-decision-guide.md
- contents/spring/spring-boot-condition-evaluation-report-first-debug-checklist.md
- contents/spring/spring-starter-added-but-bean-missing-faq.md
- contents/spring/spring-bean-registration-path-decision-guide.md
confusable_with:
- spring/primary-conditionalonmissingbean-bean-override-decision-guide
- spring/primary-qualifier-collection-injection
- spring/bean-registration-path-decision-guide
forbidden_neighbors: []
expected_queries:
- auto-configuration에서 기존 bean이 있으면 빠지고, 특정 bean이 있을 때만 켜지는 조건을 어떻게 나눠?
- '`@ConditionalOnSingleCandidate`는 bean이 하나만 있을 때만 쓰는 건지, `@Primary`랑 어떻게 다른지 표로 보고 싶어'
- 'starter 기본 bean을 만들 때 `@ConditionalOnBean`, `@ConditionalOnMissingBean`, `@ConditionalOnSingleCandidate` 중 무엇부터 고르면 돼?'
- 조건은 통과했는데 주입은 또 따로 실패할 수 있다는 말을 예시로 설명해줘
- DataSource 후보가 둘일 때 어떤 conditional annotation이 auto-configuration에 맞는지 결정 기준이 궁금해
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 Boot auto-configuration이나 설정 bean을 만들 때
  `@ConditionalOnBean`, `@ConditionalOnMissingBean`,
  `@ConditionalOnSingleCandidate` 중 무엇을 골라야 하는지 판단하게 돕는
  chooser다. 기존 bean이 있으면 기본값이 물러나야 하나, 특정 선행 bean이
  있을 때만 켜야 하나, 후보가 여러 개인데 하나로 결정 가능하면 되는가,
  condition 통과와 실제 주입 선택은 왜 다른가 같은 질문을 activation
  관점에서 세 갈래로 분리한다.
---

# Spring `@ConditionalOnBean` vs `@ConditionalOnMissingBean` vs `@ConditionalOnSingleCandidate` 결정 가이드

## 한 줄 요약

> 선행 bean이 있어야 열리는 문이면 `@ConditionalOnBean`, 기본 bean이 비어 있을 때만 채우는 문이면 `@ConditionalOnMissingBean`, 여러 후보여도 하나로 결정 가능할 때만 여는 문이면 `@ConditionalOnSingleCandidate`로 먼저 자른다.

## 결정 매트릭스

| 지금 만들려는 조건 | 먼저 고를 annotation | 왜 이쪽이 기본값인가 |
| --- | --- | --- |
| 특정 타입이나 이름의 bean이 이미 있어야 보조 bean을 켜고 싶다 | `@ConditionalOnBean` | 선행 bean 존재 여부가 activation gate이기 때문이다 |
| 사용자가 같은 역할의 bean을 직접 만들었으면 Boot 기본 bean은 물러나야 한다 | `@ConditionalOnMissingBean` | 기존 bean이 있으면 back-off하는 기본값 제공 패턴에 맞다 |
| 같은 타입 후보가 여러 개여도 지금 시점에 하나로 결정 가능할 때만 자동 구성을 켜고 싶다 | `@ConditionalOnSingleCandidate` | "정확히 1개"보다 "단일 후보 결정 가능"을 보는 조건이기 때문이다 |
| 이미 등록된 후보 중 무엇을 주입할지 정하는 문제다 | conditional annotation이 아니라 `@Primary`/`@Qualifier` 쪽 | activation과 injection-time 선택은 질문 자체가 다르다 |
| bean이 안 떠서 원인이 조건 실패인지 classpath/property 문제인지 모르겠다 | annotation 추가보다 condition report 확인 | 조건식보다 먼저 왜 매치가 안 됐는지 보는 편이 빠르다 |

## 흔한 오선택

### 1. `@ConditionalOnBean`으로 주입 후보까지 고르려 한다

학습자 표현으로는 "`name = \"mainDataSource\"`면 그 bean이 바로 주입되는 거 아닌가요?"가 자주 나온다.  
하지만 이 annotation은 등록 경로를 여는 문이지, 생성자 파라미터에 무엇을 꽂을지 정하는 장치가 아니다.

### 2. `@ConditionalOnMissingBean`을 "`@Primary`의 대체품"처럼 쓴다

"기본 bean을 이쪽으로 쓰고 싶으니 missing bean 대신 primary 붙이면 되겠죠?"라는 식이다.  
`@ConditionalOnMissingBean`은 기본값을 만들지 말지, `@Primary`는 이미 등록된 후보 중 무엇을 기본 주입 대상으로 둘지의 문제라 시간축이 다르다.

### 3. `@ConditionalOnSingleCandidate`를 "무조건 bean이 1개"로만 읽는다

"DataSource가 두 개면 이 조건은 절대 못 쓰는 거죠?"라는 오해가 반복된다.  
실제 기준은 하나로 결정 가능한가이며, `@Primary` 같은 규칙 덕분에 단일 후보가 정해지면 조건이 통과할 수 있다.

### 4. condition 실패와 starter 미동작을 전부 annotation 탓으로 돌린다

"bean이 안 떴으니 conditional annotation을 바꾸면 되겠지"라고 바로 가기 쉽다.  
하지만 classpath, property, scan boundary 문제면 annotation 선택보다 condition report와 FAQ 문서가 먼저다.

## 다음 학습

- 기본 bean back-off와 주입 후보 선택을 한 표에서 더 자르고 싶다면 [Spring `@Primary` vs `@ConditionalOnMissingBean` vs Bean Override 결정 가이드](./spring-primary-conditionalonmissingbean-bean-override-decision-guide.md)로 이어간다.
- activation이 아니라 실제 주입 시점 선택 규칙이 헷갈리면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)를 본다.
- 조건은 맞는 것 같은데 bean이 안 뜬다면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)와 [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md)로 바로 이동한다.
- 이 조건들을 어느 등록 경로에서 쓰는지부터 다시 잡고 싶다면 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)와 세 primer 문서를 순서대로 잇는다.
