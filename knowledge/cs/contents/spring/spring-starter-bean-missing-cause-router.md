---
schema_version: 3
title: Starter 넣었는데 Bean이 안 떠요 원인 라우터
concept_id: spring/starter-bean-missing-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
  - starter-bean-missing
  - condition-report-triage
  - auto-configuration-backoff
aliases:
  - starter 넣었는데 bean 안 뜸
  - spring starter bean missing
  - starter 추가했는데 bean 없음
  - auto configuration bean 안 생김
  - starter 넣었는데 빈 등록 안 됨
  - starter bean not created
symptoms:
  - starter를 추가했는데 기대한 Bean이 생성되지 않아요
  - 로컬에서는 되는데 test나 prod에서만 starter 기본 Bean이 안 보여요
  - ObjectMapper나 WebClient Builder 기본 Bean이 갑자기 사라진 것 같아요
  - starter dependency는 있는데 condition report를 보면 auto-configuration이 negative match예요
intents:
  - symptom
  - troubleshooting
prerequisites:
  - spring/boot-autoconfiguration-basics
next_docs:
  - spring/boot-condition-evaluation-report-first-debug-checklist
  - spring/conditionalonclass-classpath-scope-optional-test-slice-primer
  - spring/conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer
  - spring/conditionalonmissingbean-vs-primary-primer
linked_paths:
  - contents/spring/spring-starter-added-but-bean-missing-faq.md
  - contents/spring/spring-boot-condition-evaluation-report-first-debug-checklist.md
  - contents/spring/spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md
  - contents/spring/spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md
  - contents/spring/spring-conditionalonmissingbean-vs-primary-primer.md
  - contents/spring/spring-bean-registration-path-decision-guide.md
  - contents/spring/spring-component-scan-failure-patterns.md
  - contents/spring/spring-test-slice-scan-boundaries.md
confusable_with:
  - spring/bean-not-found-cause-router
  - spring/bean-registration-path-decision-guide
  - spring/conditionalonmissingbean-vs-primary-primer
forbidden_neighbors:
  - contents/spring/spring-bean-not-found-cause-router.md
expected_queries:
  - Spring Boot에서 starter를 넣었는데 왜 기본 Bean이 안 만들어져?
  - starter dependency는 추가했는데 특정 환경에서만 auto-configuration이 빠질 때 어디부터 봐야 해?
  - condition report에 negative match가 보이면 classpath 문제인지 property 문제인지 어떻게 나눠?
  - ObjectMapper를 조금 건드린 뒤 starter 기본 Bean이 사라진 것처럼 보일 때 먼저 무엇을 의심해?
  - @WebMvcTest나 CI에서만 starter Bean이 없으면 scan 문제랑 자동 구성 조건을 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Spring Boot에서 "starter를 넣었는데 bean이 안 떠요",
  "starter dependency는 있는데 auto-configuration이 안 붙어요", "condition
  report가 negative match예요", "로컬은 되는데 test나 prod에서만 기본 bean이
  사라져요", "ObjectMapper나 WebClient 기본 bean이 갑자기 안 보여요" 같은
  학습자 증상을 classpath 조건 실패 / property 조건 불일치 / 사용자 bean 선점
  back-off / test slice와 scan 경계 혼동으로 나누는 symptom_router다.
---

# Starter 넣었는데 Bean이 안 떠요 원인 라우터

## 한 줄 요약

> starter 추가는 "후보를 올렸다"에 가깝고, 실제 Bean 생성은 classpath, property, 기존 Bean, 테스트 경계가 모두 맞아야 일어난다.

## 가능한 원인

1. **필요한 classpath 조건이 빠졌다.** starter는 들어왔지만 auto-configuration이 찾는 SDK, driver, 구현 라이브러리가 현재 실행 classpath에 없으면 `@ConditionalOnClass`에서 바로 빠진다. 이 갈래는 [Spring `@ConditionalOnClass` classpath 함정 입문](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)으로 이어서 negative match 한 줄을 읽는 법부터 잡는 편이 빠르다.
2. **property 조건이 현재 환경과 맞지 않는다.** 로컬은 되는데 test, CI, prod에서만 Bean이 사라지면 `@ConditionalOnProperty`, profile, env var 이름 변환 때문에 조건이 꺼진 경우가 많다. 이때는 [Spring `@ConditionalOnProperty` 기본값 함정](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)으로 가서 `havingValue`, `matchIfMissing`, relaxed binding 차이를 먼저 본다.
3. **내가 만든 Bean이 기본 Bean을 밀어냈다.** `ObjectMapper`, `WebClient.Builder`처럼 같은 역할 Bean을 직접 등록하면 Boot 기본값은 `@ConditionalOnMissingBean` 때문에 정상적으로 back-off할 수 있다. 이런 장면은 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리](./spring-conditionalonmissingbean-vs-primary-primer.md)에서 "생성 실패"가 아니라 "기본값 철수"로 읽어야 한다.
4. **test slice나 scan 경계를 runtime 문제로 읽고 있다.** `@WebMvcTest`에서는 원래 전체 auto-configuration이 다 뜨지 않을 수 있고, package 경계가 달라지면 starter 문제처럼 보여도 실제로는 scan/import 범위 문제일 수 있다. 이 경우는 [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)나 [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)으로 분기하는 편이 낫다.

## 빠른 자기 진단

1. condition report에 `did not find required class`가 보이면 property보다 classpath 갈래를 먼저 본다.
2. 환경마다 결과가 달라지고 report에 property 조건 문구가 보이면 env/profile 차이를 먼저 비교한다.
3. 최근에 같은 타입의 `@Bean`을 직접 추가했다면 "왜 안 생기지?"보다 "내 Bean 때문에 기본값이 물러났나?"를 먼저 묻는다.
4. 앱 실행은 되는데 특정 slice test에서만 Bean이 없으면 starter 자체 고장보다 테스트가 어떤 auto-configuration을 로드하는지 확인한다.
5. Bean 자체가 아예 안 보이는지, 아니면 여러 개가 떠서 주입이 모호한지부터 나누면 `bean not found`와 `ambiguous bean`을 섞어 읽는 실수를 줄일 수 있다.

## 다음 학습

- 실제 첫 디버그 순서를 짧게 잡으려면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 간다.
- starter와 classpath 관계가 헷갈리면 [Spring `@ConditionalOnClass` classpath 함정 입문](./spring-conditionalonclass-classpath-scope-optional-test-slice-primer.md)을 바로 잇는다.
- property가 환경마다 다르게 먹는 장면이면 [Spring `@ConditionalOnProperty` 기본값 함정](./spring-conditionalonproperty-havingvalue-matchifmissing-pitfalls-primer.md)을 본다.
- 기본 Bean이 물러난 상황과 주입 우선순위를 구분하려면 [Spring `@ConditionalOnMissingBean` vs `@Primary` 오해 분리](./spring-conditionalonmissingbean-vs-primary-primer.md)로 이동한다.
- 더 넓은 beginner FAQ 흐름이 필요하면 [Spring Starter 넣었는데 Bean이 안 뜰 때 FAQ](./spring-starter-added-but-bean-missing-faq.md)를 이어서 읽는다.
