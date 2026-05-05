---
schema_version: 3
title: 설정값이 안 바뀌어요 원인 라우터
concept_id: spring/config-value-not-changing-cause-router
canonical: false
category: spring
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- property-source-precedence
- profile-vs-override
- env-var-name-mismatch
aliases:
- 스프링 설정값이 안 바뀌어요
- application yml 바꿨는데 값이 그대로예요
- 환경변수 넣었는데 설정 반영이 안 돼요
- test에서만 프로퍼티가 이상해요
- spring config 값이 왜 안 먹어요
symptoms:
- application.yml 값을 바꿨는데 실행하면 예전 값이 그대로 보여요
- 로컬에서는 되는데 test나 prod에서는 같은 설정 key가 다르게 읽혀요
- 환경변수로 값을 넣었다고 생각했는데 Spring이 기본값만 보는 것 같아요
- application-test.yml이나 profile 파일을 만들었는데 기대한 값으로 안 바뀌어요
intents:
- symptom
- troubleshooting
prerequisites: []
next_docs:
- spring/property-source-precedence-quick-guide
- spring/activeprofiles-vs-test-overrides-primer
- spring/relaxed-binding-env-var-cheatsheet
- spring/config-additional-location-primer
linked_paths:
- contents/spring/spring-property-source-precedence-quick-guide.md
- contents/spring/spring-activeprofiles-vs-test-overrides-primer.md
- contents/spring/spring-relaxed-binding-env-var-cheatsheet.md
- contents/spring/spring-config-additional-location-primer.md
- contents/spring/spring-spring-application-json-primer.md
confusable_with:
- spring/starter-bean-missing-cause-router
- spring/bean-not-found-cause-router
- spring/test-profile-vs-property-override-decision-guide
forbidden_neighbors: []
expected_queries:
- Spring Boot에서 application.yml 값을 바꿨는데 왜 실행 결과는 예전 값처럼 보여?
- prod에서만 설정이 다르게 먹을 때 우선순위 문제인지 profile 선택 문제인지 어디부터 나눠 봐야 해?
- APP_PAYMENT_BASE_URL 같은 env var를 넣었는데 바인딩이 안 되면 이름 규칙을 어떻게 확인해?
- '@ActiveProfiles(\"test\")를 붙였는데도 테스트 값이 안 바뀌면 어떤 문서부터 보는 게 맞아?'
- spring.config.additional-location이나 external file 때문에 기본 설정이 가려졌는지 빠르게 확인하는 방법이 있을까?
contextual_chunk_prefix: |
  이 문서는 학습자가 Spring에서 "설정값이 안 바뀌어요", "application.yml을
  고쳤는데 예전 값이 보여요", "환경변수를 넣었는데 기본값만 읽어요",
  "test와 prod에서 같은 key가 다르게 보여요", "profile 파일을 만들었는데
  값이 안 바뀌어요" 같은 증상을 property source 우선순위 / profile 선택과
  test override 혼동 / env var 이름 변환 실수 / 외부 config location 탐색
  착시로 나누는 symptom_router다.
---

# 설정값이 안 바뀌어요 원인 라우터

## 한 줄 요약

> 설정값이 안 바뀐다는 장면은 대개 "Spring이 파일을 안 읽었다"보다 같은 key를 더 높은 source가 이미 덮고 있거나, profile과 env var 이름을 다른 축으로 섞어 본 경우다.

## 가능한 원인

1. **더 높은 property source가 이미 같은 key를 덮고 있다.** `application.yml`을 고쳤는데도 값이 그대로면 env var, command-line, test property가 위에서 가리고 있을 수 있다. 이 갈래는 [Spring Property Source 우선순위 빠른 판별](./spring-property-source-precedence-quick-guide.md)로 가서 지금 실행에서 누가 가장 위인지 먼저 본다.
2. **profile을 켜는 문제와 값을 덮는 문제를 섞었다.** `application-test.yml`을 만들었는데 안 바뀌거나 `@ActiveProfiles("test")`를 붙였는데 기대가 어긋나면, active profile 선택과 test override 도구를 다른 역할로 봐야 한다. 이 경우는 [Spring `@ActiveProfiles` vs test override primer](./spring-activeprofiles-vs-test-overrides-primer.md)로 이어서 "무슨 profile이 켜졌는가"와 "값은 어디서 들어오는가"를 분리한다.
3. **환경 변수 이름은 넣었지만 Spring key로 매핑되지 않았다.** `APP_PUSH_NOTIFICATION_ENABLED`처럼 써서 맞다고 생각했는데 실제 key가 `app.push-notification.enabled`라면 dash 제거 규칙 때문에 다른 경로로 읽힐 수 있다. 이런 장면은 [Spring Relaxed Binding Env Var Cheatsheet](./spring-relaxed-binding-env-var-cheatsheet.md)로 가서 dotted, dashed, list key를 env var로 바꾸는 규칙을 확인한다.
4. **외부 config 위치를 추가한 줄 알았는데 기본 탐색을 바꿔 버렸다.** 배포 파일을 얹으려다 `spring.config.location`과 `spring.config.additional-location`을 섞으면 jar 안 기본값이 사라진 것처럼 느껴질 수 있다. 이 갈래는 [Spring `spring.config.additional-location` Primer](./spring-config-additional-location-primer.md)와 [Spring `SPRING_APPLICATION_JSON` Primer](./spring-spring-application-json-primer.md)로 이어서 "어디서 읽는가" 자체를 다시 본다.

## 빠른 자기 진단

1. 바꾼 key가 `application.yml`에만 있는지, env var나 test annotation `properties`에도 같은 key가 있는지 먼저 확인한다.
2. 문제가 test에서만 재현되면 `@ActiveProfiles`, `@TestPropertySource`, `@SpringBootTest(properties = ...)` 중 무엇이 실제로 값을 올렸는지 분리한다.
3. env var로 넣었다면 property key를 segment로 쪼갠 뒤 대문자와 underscore 규칙으로 다시 써 본다. dash를 underscore로 바꿨다고 당연히 맞는 것은 아니다.
4. 외부 파일 경로나 실행 옵션을 최근에 건드렸다면 `location`이 기본 탐색을 대체했는지, `additional-location`처럼 추가한 것인지부터 본다.

## 다음 학습

- 가장 먼저 우선순위 감각을 다시 잡으려면 [Spring Property Source 우선순위 빠른 판별](./spring-property-source-precedence-quick-guide.md)을 본다.
- 테스트에서만 값이 이상하면 [Spring `@ActiveProfiles` vs test override primer](./spring-activeprofiles-vs-test-overrides-primer.md)와 [Spring 테스트 설정 입력 결정 가이드](./spring-test-profile-vs-property-override-decision-guide.md)를 같이 읽는다.
- env var 이름이 맞는지 확신이 없으면 [Spring Relaxed Binding Env Var Cheatsheet](./spring-relaxed-binding-env-var-cheatsheet.md)로 바로 내려간다.
- 배포 설정 파일을 붙이는 방식이 헷갈리면 [Spring `spring.config.additional-location` Primer](./spring-config-additional-location-primer.md)와 [Spring `SPRING_APPLICATION_JSON` Primer](./spring-spring-application-json-primer.md)를 잇는다.
