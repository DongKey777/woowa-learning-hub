---
schema_version: 3
title: 예외 처리 기초
concept_id: software-engineering/exception-handling-basics
canonical: true
category: software-engineering
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 89
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- exception-boundary
- business-vs-system-exception
- global-exception-handler
aliases:
- exception handling basics
- 예외 처리 입문
- checked unchecked exception
- custom exception
- 비즈니스 예외
- 시스템 예외
- global exception handler
- 예외 어디서 잡나요
- try catch 기초
- 409 vs 422
- 업무 규칙 위반 상태 코드
symptoms:
- try catch를 많이 넣으면 안전하다고 생각해 예외를 삼키거나 계층마다 응답을 제각각 만든다
- 비즈니스 규칙 위반, 입력 형식 오류, DB/외부 API 시스템 오류를 같은 예외 처리 방식으로 다룬다
- Service나 Domain에서 던질 예외와 ControllerAdvice 같은 공통 처리 경계를 구분하지 못한다
intents:
- definition
- troubleshooting
prerequisites:
- software-engineering/layered-architecture-basics
- software-engineering/service-layer-basics
next_docs:
- software-engineering/api-design-error-handling
- software-engineering/http-409-vs-422-selection-guide
- spring/aop-proxy-mechanism
- software-engineering/logging-strategy-basics
linked_paths:
- contents/software-engineering/api-design-error-handling.md
- contents/software-engineering/http-409-vs-422-selection-guide.md
- contents/software-engineering/architecture-layering-fundamentals.md
- contents/software-engineering/service-layer-basics.md
- contents/software-engineering/logging-strategy-basics.md
- contents/spring/ioc-di-container.md
- contents/spring/aop-proxy-mechanism.md
confusable_with:
- software-engineering/api-design-error-handling
- software-engineering/http-409-vs-422-selection-guide
- software-engineering/logging-strategy-basics
forbidden_neighbors: []
expected_queries:
- 예외 처리는 어디서 던지고 어디서 잡을지 계층별로 정하는 계약이라는 뜻을 설명해줘
- 비즈니스 예외와 시스템 예외, 입력 형식 예외를 Controller Service Repository 기준으로 어떻게 나눠야 해?
- @RestControllerAdvice 같은 global exception handler를 쓰면 왜 API 에러 응답 포맷이 일관돼?
- 예외를 catch해서 로그만 찍고 끝내면 호출자와 트랜잭션 관점에서 어떤 문제가 생겨?
- 409 Conflict와 422 Unprocessable Content는 업무 규칙 위반 상태 코드에서 어떻게 선택해?
contextual_chunk_prefix: |
  이 문서는 예외를 계층 경계와 API 에러 계약으로 다루는 beginner primer다.
  checked vs unchecked, business exception, system exception, input binding error, Service/Domain throw, Repository translate, global exception handler, 409 vs 422, logging and rollback boundaries를 다룬다.
---
# 예외 처리 기초 (Exception Handling Basics)

> 한 줄 요약: 예외는 "어디서 던지고 어디서 잡을지"를 명확히 정해야 하며, 비즈니스 예외와 시스템 예외를 분리하는 것이 첫 번째 기준이다.

**난이도: 🟢 Beginner**

관련 문서:

- [API 설계와 예외 처리](./api-design-error-handling.md)
- [409 vs 422 선택 기준 짧은 가이드](./http-409-vs-422-selection-guide.md)
- [Architecture and Layering Fundamentals](./architecture-layering-fundamentals.md)
- [Spring IoC 컨테이너와 DI](../spring/ioc-di-container.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: exception handling basics, 예외 처리 입문, checked unchecked exception, custom exception, 비즈니스 예외, 시스템 예외, 예외 어디서 잡나요, try catch 기초, global exception handler, 예외 계층 설계, runtime exception 차이, 예외 왜 쓰나요, 409 vs 422, conflict vs unprocessable content, 업무 규칙 위반 상태 코드

## 먼저 잡는 한 줄 멘탈 모델

예외 처리는 `많이 catch`가 아니라, **"어디서 던지고 어디서 공통 처리할지"를 계층별로 고정하는 계약 설계**다.

## before / after 한눈 비교

| 상태 | 코드 신호 | 결과 |
|---|---|---|
| before: 예외 처리 위치가 제각각 | Controller/Service/Repository마다 임의 `try-catch`와 응답 생성 | API 에러 포맷이 흔들리고 원인 추적이 어려워진다 |
| after: 처리 경계가 정해진 상태 | Service/Domain이 의미 있는 예외를 던지고 `@RestControllerAdvice`가 공통 처리 | 응답 일관성과 로깅 기준이 맞춰져 디버깅이 쉬워진다 |

## 핵심 개념

예외(Exception)는 정상 흐름에서 벗어난 상황을 코드로 표현하는 수단이다.

Java에서는 두 종류로 나뉜다.

- **Checked Exception** — 컴파일러가 처리를 강요한다. `IOException`, `SQLException` 등.
- **Unchecked Exception (RuntimeException)** — 컴파일러가 강요하지 않는다. `NullPointerException`, `IllegalArgumentException` 등.

입문자가 헷갈리는 지점은 "언제 어느 계층에서 예외를 잡아야 하는가"다. 예외를 잡는 곳이 제각각이면 에러 응답이 일관되지 않고, 비즈니스 오류와 시스템 오류를 구분하기 어려워진다.

## 한눈에 보기

```
요청
  └─ Controller           ← 여기서 잡으면 전체 API에 공통 포맷 적용 가능
       └─ Service          ← 비즈니스 예외를 던지는 층
            └─ Repository  ← DB 예외를 비즈니스 예외로 변환
```

| 예외 종류 | 발생 위치 | 처리 위치 |
|---|---|---|
| 비즈니스 예외 (입력 오류, 규칙 위반) | Service, Domain | Controller / Global Handler |
| 시스템 예외 (DB 연결 실패, 외부 API 오류) | Repository, Adapter | Global Handler + 로깅 |
| 입력 형식 예외 | Controller / Filter | Controller / Global Handler |

## 상세 분해

**비즈니스 예외를 직접 정의하기**

Spring 프로젝트에서는 `RuntimeException`을 상속해 도메인 언어로 예외를 만드는 것이 일반적이다.

```java
public class OrderNotFoundException extends RuntimeException {
    public OrderNotFoundException(OrderId id) {
        super("주문을 찾을 수 없습니다: " + id.value());
    }
}
```

**Global Exception Handler로 공통 처리**

`@RestControllerAdvice`를 사용하면 모든 컨트롤러의 예외를 한 곳에서 잡아 일관된 응답 형식으로 바꿀 수 있다.

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ErrorResponse> handle(OrderNotFoundException e) {
        return ResponseEntity.status(404).body(new ErrorResponse(e.getMessage()));
    }
}
```

**Repository 예외 변환**

DB 관련 예외(`DataAccessException`)는 인프라 세부가 서비스 계층으로 새지 않도록, Repository나 Adapter에서 비즈니스 예외로 변환하는 편이 좋다.

## 흔한 오해와 함정

- "`try-catch`를 많이 쓸수록 안전하다"는 오해가 있다. 잡을 계획 없는 예외를 무작정 catch해서 로그만 남기고 흘려보내면 오히려 근본 원인을 찾기 어렵다.
- Checked Exception을 쓰면 더 안전하다고 생각하지만, 비즈니스 레이어에서는 RuntimeException 기반 커스텀 예외가 더 관리하기 쉬운 경우가 많다.
- 예외 메시지를 직접 파싱해 분기 처리하는 코드는 취약하다. 예외 종류(클래스)로 분기해야 한다.

## 실무에서 쓰는 모습

가장 흔한 패턴은 세 단계다.

1. Service 계층에서 비즈니스 규칙 위반 시 커스텀 `RuntimeException`을 던진다.
2. `@RestControllerAdvice` 한 곳에서 예외 종류별로 HTTP 상태 코드와 에러 메시지를 결정한다.
3. Repository에서 발생하는 인프라 예외는 비즈니스 예외로 감싸서 서비스 계층에 전파한다.

이 구조를 잡으면 에러 응답 형식이 일관되고, 예외가 어느 계층에서 나왔는지 추적하기 쉬워진다.

## 더 깊이 가려면

- [API 설계와 예외 처리](./api-design-error-handling.md) — HTTP 상태 코드 선택, 에러 응답 포맷, 버전별 처리 전략
- [Spring AOP와 프록시](../spring/aop-proxy-mechanism.md) — `@Transactional`과 예외 처리가 맞닿는 지점

## 면접/시니어 질문 미리보기

- "Checked와 Unchecked 중 어느 것을 써야 하나요?" — 복구 가능성을 기준으로 한다. 호출자가 복구 동작을 해야 하면 Checked, 프로그래밍 오류나 비즈니스 규칙 위반이면 보통 Unchecked가 적합하다.
- "예외를 잡고 로그만 출력한 뒤 아무것도 안 하면 어떤 문제가 생기나요?" — 호출자가 실패를 알 수 없어 잘못된 상태로 계속 진행될 수 있다. 예외를 삼키는 패턴(exception swallowing)은 장애 원인 추적을 어렵게 만든다.
- "`@Transactional`이 있을 때 Checked Exception은 롤백이 안 된다는 게 무슨 뜻인가요?" — Spring은 기본적으로 RuntimeException만 자동 롤백한다. Checked Exception은 `rollbackFor` 옵션을 명시해야 한다.

## 한 줄 정리

예외는 비즈니스 오류와 시스템 오류를 분리하고, 던지는 곳(서비스/도메인)과 잡는 곳(글로벌 핸들러)을 명확히 정해두는 것이 출발점이다.
