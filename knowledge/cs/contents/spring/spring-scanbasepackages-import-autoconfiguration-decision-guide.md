---
schema_version: 3
title: "Spring shared module 연결 결정 가이드: `scanBasePackages` vs `@Import` vs Boot Auto-configuration"
concept_id: spring/scanbasepackages-import-autoconfiguration-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags: []
aliases:
  - spring shared module registration choice
  - scanbasepackages vs import vs auto configuration
  - shared config module import choice
  - multi module bean registration
  - spring shared module bean 연결
  - starter로 뺄지 import로 붙일지
  - scan 넓힐지 import 할지
symptoms:
  - 멀티모듈에서 bean이 안 보여서 scan 범위를 넓혀야 하는지 import 해야 하는지 모르겠어요
  - 공통 설정 모듈을 여러 앱에서 쓰는데 starter로 뺄지 그냥 설정 클래스를 가져올지 헷갈려요
  - shared module 하나 붙이려고 scanBasePackages를 크게 열고 있는데 이게 맞는지 확신이 없어요
intents:
  - comparison
  - design
  - troubleshooting
prerequisites:
  - spring/bean-registration-path-decision-guide
  - spring/boot-autoconfiguration-basics
next_docs:
  - spring/componentscan-entityscan-enablejparepositories-decision-guide
  - spring/boot-autoconfiguration-basics
  - spring/bean-registration-path-decision-guide
linked_paths:
  - contents/spring/spring-scanbasepackages-vs-import-autoconfiguration-selection.md
  - contents/spring/spring-bean-registration-path-decision-guide.md
  - contents/spring/spring-componentscan-entityscan-enablejparepositories-decision-guide.md
  - contents/spring/spring-boot-autoconfiguration-basics.md
  - contents/spring/spring-boot-autoconfiguration.md
  - contents/spring/spring-component-scan-failure-patterns.md
  - contents/spring/spring-jpa-entityscan-enablejparepositories-boundaries.md
confusable_with:
  - spring/bean-registration-path-decision-guide
  - spring/componentscan-entityscan-enablejparepositories-decision-guide
  - spring/boot-autoconfiguration-basics
forbidden_neighbors: []
expected_queries:
  - "Spring 멀티모듈에서 공통 설정을 붙일 때 `scanBasePackages`, `@Import`, auto-configuration 중 무엇부터 고르면 돼?"
  - "shared module 하나 때문에 package scan을 크게 열어도 되는지 판단 기준이 궁금해요"
  - "여러 앱이 같이 쓰는 설정 모듈을 starter로 뺄지 단순 import로 둘지 표로 보고 싶어요"
  - "`scanBasePackageClasses`로 해결할 문제와 Boot starter로 가야 할 문제를 어떻게 나눠요?"
  - "JPA scan 문제랑 shared module 등록 문제를 같은 축으로 보면 왜 헷갈리는지 설명해줘"
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 멀티모듈이나 shared module을 붙일 때
  `scanBasePackages`, `@Import`, Boot auto-configuration 중 무엇을
  선택해야 하는지 빠르게 가르는 chooser다. bean이 안 보여서 scan을 넓힐지,
  공통 설정 묶음을 명시적으로 import할지, 여러 앱이 쓰는 starter처럼
  조건부 기본값을 줄지, JPA scan 문제와 shared module 등록 문제를 같은
  축으로 착각하는 질문을 세 갈래 결정표로 연결한다.
---

# Spring shared module 연결 결정 가이드: `scanBasePackages` vs `@Import` vs Boot Auto-configuration

## 한 줄 요약

> 같은 앱이 함께 소유하는 코드면 좁은 scan, 몇 개 설정을 의도적으로 붙일 거면 `@Import`, 여러 앱에 기본값을 배포할 거면 Boot auto-configuration부터 고른다.

## 결정 매트릭스

| 지금 붙이려는 대상 | 먼저 고를 방식 | 왜 이쪽이 기본값인가 |
| --- | --- | --- |
| 같은 애플리케이션 안에서 함께 배포되는 내부 module | `scanBasePackageClasses` 중심의 좁은 scan | 이 경우는 library 연결보다 앱 소유 코드를 발견시키는 문제가 더 가깝다 |
| 공통 설정 클래스 몇 개를 이 앱이 명시적으로 채택하고 싶다 | `@Import` | 어떤 설정을 가져오는지 코드에 드러나고 scan 오염을 막기 쉽다 |
| 여러 애플리케이션에 starter처럼 배포하면서 classpath, property, 기존 bean에 따라 켜고 꺼야 한다 | Boot auto-configuration | 조건부 기본값 제공과 back-off 계약이 필요하므로 scan이나 import보다 역할이 크다 |
| `scanBasePackages`를 넓혔는데 entity나 repository만 계속 안 잡힌다 | shared module 선택이 아니라 JPA scan 문서로 이동 | 이 신호는 `@EntityScan`, `@EnableJpaRepositories` 경계 문제일 가능성이 더 높다 |
| module 하나 때문에 회사 공통 package 전체를 열고 싶다 | scan 확대보다 `@Import` 또는 auto-configuration 재검토 | 지금 문제는 bean 발견보다 module 계약을 너무 넓게 잡은 경우가 많다 |

## 흔한 오선택

- shared module 하나를 붙이려고 `scanBasePackages = "com.company"`처럼 크게 열면 학습자 표현으로는 "일단 보이게는 했는데 왜 어디서 왔는지 모르겠어요"가 된다. 이 경우는 같은 앱 내부 코드인지, 명시적 설정 묶음인지부터 다시 자르는 편이 낫다.
- 공통 HTTP client 설정 몇 개만 가져오면 되는데 starter와 조건부 bean까지 먼저 설계하면 "`@ConditionalOnMissingBean`까지 다 붙여야 하나요?" 같은 과설계가 생기기 쉽다. 이런 장면은 보통 `@Import`가 더 짧다.
- 반대로 여러 앱이 재사용하는 infra module인데 매 앱마다 `@Import`를 복붙하기 시작하면 "앱마다 붙이는 조합이 달라서 관리가 어렵다"는 문제가 나온다. 이때는 명시 import보다 auto-configuration 계약이 더 맞을 수 있다.
- `scanBasePackages`를 넓혔는데 `Not a managed type`가 그대로라고 해서 scan 선택이 틀렸다고 보면 shared module 문제와 JPA 경계 문제를 섞게 된다. 이 신호는 chooser를 끝내고 JPA scan 분기 문서로 내려가야 한다.

## 다음 학습

- bean 등록 경로 자체가 헷갈리면 [Spring Bean 등록 경로 결정 가이드](./spring-bean-registration-path-decision-guide.md)에서 component scan, `@Bean`, Boot 기본값의 큰 그림을 먼저 정리한다.
- `scanBasePackages`를 넓혀도 entity나 repository가 안 잡히는 경우는 [Spring `@ComponentScan` vs `@EntityScan` vs `@EnableJpaRepositories` 결정 가이드](./spring-componentscan-entityscan-enablejparepositories-decision-guide.md)로 바로 내려간다.
- starter를 넣으면 왜 bean이 자동으로 생기는지 감각이 먼저 필요하면 [Spring Boot 자동 구성 기초](./spring-boot-autoconfiguration-basics.md)를 본다.
- shared module 선택 기준을 더 길게 읽고 registry 단계 확장까지 보고 싶다면 [Spring `scanBasePackages` vs `@Import` vs Boot Auto-configuration 선택 기준](./spring-scanbasepackages-vs-import-autoconfiguration-selection.md)으로 이어간다.
