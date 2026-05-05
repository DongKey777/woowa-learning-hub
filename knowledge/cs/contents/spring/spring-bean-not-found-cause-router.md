---
schema_version: 3
title: Bean을 못 찾아요 원인 라우터
concept_id: spring/bean-not-found-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
  - bean-not-found-triage
  - test-slice-bean-missing
  - profile-conditional-bean-drop
aliases:
- bean not found
- no such bean
- no qualifying bean
- bean candidate missing
- constructor injection bean missing
- service bean missing
- webmvctest bean missing
- profile specific bean missing
- conditional bean drop
symptoms:
- startup 로그에 Parameter 0 of constructor required a bean of type ... that could not be found가 뜬다
- '@Service를 붙였는데도 no qualifying bean of type available이 보인다'
- 로컬에서는 되는데 test나 prod profile에서만 bean이 사라진다
- '@WebMvcTest에서는 service bean not found가 뜨는데 앱 실행은 된다'
intents:
- symptom
- troubleshooting
prerequisites:
- spring/bean-di-basics
next_docs:
- spring/component-scan-failure-patterns
- spring/bean-di-basics
- spring/ioc-di-basics
linked_paths:
- contents/spring/spring-component-scan-failure-patterns.md
- contents/spring/spring-di-exception-quick-triage.md
- contents/spring/spring-test-slice-scan-boundaries.md
- contents/spring/spring-boot-condition-evaluation-report-first-debug-checklist.md
- contents/spring/spring-bean-naming-qualifier-rename-pitfalls-primer.md
- contents/spring/spring-jpa-entityscan-enablejparepositories-boundaries.md
confusable_with:
- spring/component-scan-failure-patterns
- spring/same-type-bean-injection-failure-cause-router
- spring/bean-di-basics
forbidden_neighbors:
- contents/spring/spring-same-type-bean-injection-failure-cause-router.md
expected_queries:
- Spring에서 Parameter 0 of constructor required a bean of type이 뜨면 어디부터 봐야 해?
- '@Service 붙였는데도 bean could not be found가 나오면 원인을 어떻게 나눠?'
- '@WebMvcTest에서만 service bean not found가 뜰 때 scan 문제랑 어떻게 구분해?'
- 로컬은 되는데 prod나 test profile에서만 bean이 사라질 때 무엇을 먼저 의심해?
- qualifier 이름을 바꾼 뒤 no qualifying bean이 뜨면 scan 말고 무엇을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Spring에서 생성자 주입이 시작도 못 하고 후보가 0개라고 나올
  때 왜 빈이 안 보이는지 증상에서 원인으로 이어주는 symptom_router다.
  애노테이션을 붙였는데도 등록이 안 된다, 테스트에서만 서비스가 사라진다,
  프로필을 바꾸면 연결이 끊긴다, 조건부 설정 때문에 빠진 것 같다, 이름을
  바꾼 뒤 주입이 깨졌다 같은 표현을 scan 경계, test slice, profile·
  conditional, bean 이름 계약 갈래로 라우팅한다.
---

# Bean을 못 찾아요 원인 라우터

> 한 줄 요약: `bean not found`는 대개 Spring 전체 고장보다 "후보가 0개가 된 이유"를 못 나눈 상태라서, scan 경계인지 test slice인지 조건 탈락인지부터 자르는 편이 빠르다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)
- [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)
- [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)
- [Spring Bean 이름 규칙과 rename 함정 입문](./spring-bean-naming-qualifier-rename-pitfalls-primer.md)
- [Spring DI 예외 빠른 판별](./spring-di-exception-quick-triage.md)
- [Dependency Injection Basics](../software-engineering/dependency-injection-basics.md)

retrieval-anchor-keywords: bean not found, nosuchbeandefinitionexception 원인, service bean 못 찾음, required a bean of type that could not be found, spring bean missing basics, 왜 bean 이 없어요, test 에서만 bean 없음, profile 에서만 bean 사라짐, component scan 처음, what is no qualifying bean

## 핵심 개념

`bean not found`는 보통 "Spring이 못 찾았다"보다 "현재 실행 조건에서 후보가 0개다"에 가깝다. 초급 단계에서는 원인을 네 갈래로 먼저 나누면 된다. `component scan` 경계가 틀렸는지, test slice가 원래 보지 않는 Bean을 기대했는지, profile이나 conditional이 현재 환경에서 Bean을 껐는지, 이름 계약이나 JPA 전용 scan 축을 다른 문제로 읽고 있는지다.

## 한눈에 보기

| 지금 보이는 장면 | 먼저 의심할 축 | 다음 문서 |
| --- | --- | --- |
| 앱 전체에서 계속 `could not be found` | component scan 경계 | [Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md) |
| `@WebMvcTest`에서만 Bean이 없음 | test slice 경계 | [Test Slice Scan Boundary](./spring-test-slice-scan-boundaries.md) |
| 로컬은 되는데 test, CI, prod에서만 사라짐 | profile, conditional 탈락 | [Condition Evaluation Report 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md) |
| rename 직후, qualifier 문자열 변경 직후 깨짐 | 이름 계약 흔들림 | [Bean 이름 규칙과 rename 함정](./spring-bean-naming-qualifier-rename-pitfalls-primer.md) |

## 빠른 분기

1. 로그가 `found 2 beans`가 아니라 `could not be found`, `no qualifying bean`이면 이 라우터가 맞다.
2. 특정 테스트에서만 깨지면 scan 전체 고장보다 test slice 경계를 먼저 본다.
3. 환경에 따라 결과가 달라지면 package 구조보다 `@Profile`, `@Conditional...` 축이 더 유력하다.
4. rename, qualifier, entity scan 변경 직후라면 단순 scan 문제로 단정하지 않는다.

## 흔한 오해와 함정

- `@Service`를 붙였으니 무조건 등록됐다고 생각하기 쉽다. 하지만 scan 시작 package 밖이면 annotation이 있어도 후보가 0개다.
- test에서만 실패하는데 운영 scan 문제로 몰아가면 원인 찾는 시간이 길어진다. `@WebMvcTest`, `@DataJpaTest`는 원래 보는 Bean 범위가 좁다.
- 로컬과 prod 결과가 다르면 코드보다 설정 차이를 먼저 봐야 한다. 이때는 package 구조를 아무리 봐도 답이 안 나올 수 있다.
- rename 직후 `bean not found`가 나오면 scan보다 qualifier 문자열 계약이 흔들린 경우가 많다.

## 다음 행동

- component scan 경계가 의심되면 [Spring Component Scan 실패 패턴](./spring-component-scan-failure-patterns.md)부터 읽는다.
- 테스트에서만 Bean이 없으면 [Spring Test Slice Scan Boundary 오해](./spring-test-slice-scan-boundaries.md)로 이동한다.
- 환경별 차이가 핵심이면 [Spring Boot Condition Evaluation Report 첫 디버그 체크리스트](./spring-boot-condition-evaluation-report-first-debug-checklist.md)로 간다.
- DI 큰 그림을 다시 잡고 싶으면 [Spring Bean과 DI 기초](./spring-bean-di-basics.md)와 [IoC와 DI 기초](./spring-ioc-di-basics.md)를 본다.

## 한 줄 정리

`bean not found`를 보면 바로 설정을 다 건드리기보다 "scan 경계, test slice, 조건 탈락, 이름 계약" 중 어느 축인지 먼저 잘라야 빠르게 해결된다.
