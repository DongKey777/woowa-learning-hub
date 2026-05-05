---
schema_version: 3
title: Spring 요청 공통 처리 위치 결정 가이드
concept_id: spring/request-cross-cutting-hook-decision-guide
canonical: false
category: spring
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
- filter-vs-interceptor-choice
- exception-response-ownership
- request-cross-cutting-boundary
aliases:
- spring 공통 처리 위치
- filter interceptor controlleradvice 어디에
- 요청 로깅 어디에 넣지
- 인증 검사 어디에 두지
- 예외 응답 포맷 어디서 통일해
- 공통 관심사 레이어 선택
- spring 훅 선택 기준
symptoms:
- 로깅을 필터에 넣어야 하는지 인터셉터에 넣어야 하는지 매번 바뀌어요
- 인증 검사와 예외 응답 포맷을 같은 레이어에서 처리하려다가 꼬여요
- 컨트롤러 전 공통 처리와 실패 응답 통일을 어디서 나눠야 할지 모르겠어요
intents:
- comparison
- design
- troubleshooting
prerequisites:
- spring/spring-mvc-controller-basics
- spring/spring-security-architecture
next_docs:
- spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge
- spring/spring-onceperrequestfilter-vs-filter-beginner-primer
- spring/spring-mvc-exception-resolver-chain-contract
linked_paths:
- contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md
- contents/spring/spring-onceperrequestfilter-vs-filter-beginner-primer.md
- contents/spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md
- contents/spring/spring-mvc-filter-interceptor-controlleradvice-boundaries.md
- contents/spring/spring-mvc-exception-resolver-chain-contract.md
- contents/spring/spring-security-exceptiontranslation-entrypoint-accessdeniedhandler.md
confusable_with:
- spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge
- spring/spring-filter-security-chain-interceptor-admin-auth-beginner-bridge
- spring/cors-security-vs-mvc-ownership
forbidden_neighbors: []
expected_queries:
- Spring에서 공통 로직을 넣으려는데 필터, 인터셉터, ControllerAdvice 중 무엇부터 골라야 해?
- 인증 체크와 예외 응답 JSON 통일을 왜 같은 곳에 두면 안 되는지 결정 기준으로 설명해줘
- 요청 시간 측정은 어디에 두고, 도메인 예외를 400이나 404로 바꾸는 일은 어디서 맡겨야 해?
- 컨트롤러에 들어가기 전 검사와 컨트롤러에서 나온 예외 처리의 경계를 한 표로 보고 싶어
- 로그인 안 된 사용자를 막는 일과 실패 응답 포맷 표준화를 서로 다른 훅으로 나누는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring 학습자가 요청 공통 처리를 넣을 때 filter,
  HandlerInterceptor, ControllerAdvice 중 어디에 둬야 하는지 고르게
  돕는 chooser다. 요청 로깅은 어디에 넣지, 인증 검사는 어느 레이어가
  주인이지, 예외 응답 JSON은 누가 통일하지, 컨트롤러 전 처리와 실패 응답
  번역이 왜 같은 축이 아닌지 같은 질문을 책임 경계 기준으로 분리한다.
---

# Spring 요청 공통 처리 위치 결정 가이드

## 한 줄 요약

> 요청 자체를 초입에서 걸러야 하면 `Filter`, 컨트롤러 전후 공통 작업이면 `HandlerInterceptor`, 예외를 HTTP 응답으로 번역해야 하면 `ControllerAdvice`부터 고른다.

## 결정 매트릭스

| 지금 하려는 일 | 먼저 볼 위치 | 이유 |
| --- | --- | --- |
| 인증 헤더 확인, CORS, trace id 같은 입구 처리 | `Filter` | 컨트롤러에 들어가기 전에 요청 자체를 다룬다 |
| 요청 시간 측정, 로그인 사용자 정보 메타데이터 기록 | `HandlerInterceptor` | 어떤 컨트롤러가 실행되는지 아는 MVC 경계에서 전후 훅을 건다 |
| `IllegalArgumentException`을 400 JSON으로 통일 | `ControllerAdvice` | 이미 발생한 예외를 응답 계약으로 번역하는 책임이다 |
| `@RequestBody` 전에 바디를 읽거나 감싸기 | `Filter` 쪽부터 검토 | 서블릿 요청 객체를 가장 앞단에서 만진다 |
| 특정 컨트롤러 묶음에만 공통 검사 추가 | `HandlerInterceptor` | 경로 패턴과 핸들러 문맥을 같이 보기 쉽다 |

## 흔한 오선택

`Filter`에 도메인 예외 응답 포맷까지 몰아넣으면 인증 실패와 비즈니스 예외 번역이 뒤섞인다. 학습자는 보통 "어차피 전역 처리니까 한 군데면 되지 않나요?"라고 말하지만, 입구 차단과 예외 번역은 책임이 다르다.

`HandlerInterceptor`에서 인증의 중심을 잡으려 하면 Security filter chain과 역할이 충돌한다. "컨트롤러 전에 실행되니까 로그인 검사도 인터셉터면 되지 않나요?"라는 표현이 나오면 보안 레이어와 MVC 레이어를 섞고 있는 경우가 많다.

`ControllerAdvice`를 요청 전 검사용으로 떠올리면 시점이 어긋난다. "잘못된 요청을 advice에서 먼저 막고 싶어요"라고 생각하기 쉽지만, advice는 요청을 미리 차단하는 훅이 아니라 이미 나온 예외를 응답으로 바꾸는 쪽에 가깝다.

로깅을 무조건 `Filter`에만 넣으면 컨트롤러 정보가 필요한 경우 답이 흐려진다. "메서드 이름까지 같이 남기고 싶은데 왜 필터에서는 답답하죠?"라는 반응이 나오면 인터셉터가 더 자연스러운 경우가 많다.

## 다음 학습

`Filter`를 커스텀 구현할 때 일반 `Filter`와 `OncePerRequestFilter` 중 무엇이 출발점인지 보려면 [Spring `OncePerRequestFilter` vs 일반 `Filter` 입문: 언제 상속부터 시작할까](./spring-onceperrequestfilter-vs-filter-beginner-primer.md)로 간다.

인터셉터가 MVC 흐름 어디에 걸리는지 큰 그림부터 잡으려면 [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)를 잇는다.

예외를 어떤 상태 코드와 JSON으로 번역하는지가 궁금하면 [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)를 본다.

인증 필터와 MVC 인터셉터를 관리자 로그인 흐름으로 비교하고 싶으면 [Spring `Filter` vs Spring Security Filter Chain vs `HandlerInterceptor`: 관리자 인증 입문 브리지](./spring-filter-security-chain-interceptor-admin-auth-beginner-bridge.md)로 내려간다.
