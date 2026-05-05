---
schema_version: 3
title: Decorator vs Proxy 결정 가이드
concept_id: design-pattern/decorator-vs-proxy-decision-guide
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - aop-proxy-vs-decorator
  - wrapper-intent-separation
  - cache-wrapper-call-control
aliases:
  - decorator vs proxy decision guide
  - decorator proxy chooser
  - 기능 추가 래퍼 vs 호출 제어 대리자
  - 로깅 래퍼와 트랜잭션 프록시 구분
  - wrapper인데 decorator인지 proxy인지
  - 같은 인터페이스로 감싸도 목적이 다름
  - aop proxy와 decorator 차이 빠른 판단
symptoms:
  - 로그를 붙였는데 decorator라고 해야 할지 proxy라고 해야 할지 모르겠어
  - Spring AOP를 wrapper 패턴으로 설명하다가 decorator랑 proxy를 섞어 말하고 있어
  - 캐시나 권한 체크를 넣은 래퍼를 기능 추가 패턴으로만 이해하고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/object-oriented-design-pattern-basics
  - design-pattern/composition-over-inheritance-basics
next_docs:
  - design-pattern/decorator-proxy-basics
  - design-pattern/decorator-vs-proxy
  - spring/aop-proxy-mechanism
linked_paths:
  - contents/design-pattern/decorator-proxy-basics.md
  - contents/design-pattern/decorator-vs-proxy.md
  - contents/spring/aop-proxy-mechanism.md
  - contents/design-pattern/adapter-vs-facade-vs-decorator-beginner-router.md
confusable_with:
  - design-pattern/decorator-proxy-basics
  - design-pattern/decorator-vs-proxy
  - spring/aop-proxy-mechanism
forbidden_neighbors:
  - contents/design-pattern/adapter-vs-facade-vs-decorator-beginner-router.md
  - contents/spring/aop-proxy-mechanism.md
expected_queries:
  - 같은 인터페이스를 감싸는데 어떤 때는 decorator고 어떤 때는 proxy라고 부르는 거야?
  - 로그 추가 래퍼와 권한 체크 래퍼를 구분하는 기준을 한 번에 설명해줘
  - Spring의 transactional 동작을 decorator가 아니라 proxy로 보는 이유가 뭐야?
  - 캐시를 감싼 객체가 기능 조합인지 접근 제어인지 어떻게 판단해?
  - wrapper 클래스가 여러 겹일 때 decorator와 proxy를 어디서 갈라야 해?
contextual_chunk_prefix: |
  이 문서는 같은 인터페이스를 감싸는 래퍼가 나왔을 때 Decorator와 Proxy를
  빠르게 가르게 돕는 chooser다. 기능을 겹쳐 얹는 조합인지, 호출 전에 권한과
  캐시와 트랜잭션 경계를 통제하는 대리인지, 로그 래퍼인지 접근 제어인지,
  AOP wrapper를 뭐로 봐야 하는지 같은 자연어 paraphrase가 본 문서의 판단
  기준에 매핑된다.
---

# Decorator vs Proxy 결정 가이드

## 한 줄 요약

> 원본 기능에 부가 기능을 겹겹이 얹으면 Decorator, 원본 호출 전에 권한·캐시·트랜잭션 같은 경계를 통제하면 Proxy다.

## 결정 매트릭스

| 지금 코드가 푸는 질문 | 먼저 볼 패턴 | 왜 그쪽이 맞는가 |
|---|---|---|
| 기존 기능은 그대로 두고 로그나 압축을 더 얹고 싶은가? | Decorator | 같은 인터페이스 위에 기능을 누적해서 조합하는 문제다. |
| 실제 객체를 바로 부르지 않고 먼저 검사하거나 가로채야 하는가? | Proxy | 호출 경계 앞에서 접근 여부와 실행 시점을 통제한다. |
| 래퍼를 여러 겹 쌓아도 의미가 선명한가? | Decorator | 기능 조합이 핵심이면 체인 구성이 자연스럽다. |
| 원본인지 대리 객체인지 호출자가 몰라도 되는가? | Proxy | 투명한 대리 수행과 제어가 의도다. |
| `@Transactional`, 권한 검사, `lazy loading`처럼 호출 타이밍이 중요하나? | Proxy | 부가 기능보다 interception 경계가 먼저다. |

`BufferedInputStream`처럼 기능을 덧붙이면 Decorator 쪽 감각이고, Spring AOP처럼 메서드 호출을 먼저 가로채면 Proxy 쪽 감각이다.

## 흔한 오선택

`@Transactional`이나 AOP를 Decorator로 설명하는 경우:
겉모양은 래퍼지만 핵심은 "기능을 더한다"보다 "프록시를 지나야 부가기능이 적용된다"는 호출 제어다. self-invocation 문제가 보이면 Proxy 신호가 강하다.

`캐시 래퍼`를 무조건 Decorator로 부르는 경우:
캐시가 단순한 출력 가공이 아니라 원본 호출 자체를 생략하거나 지연시키면 Proxy에 더 가깝다. 호출 전에 판단하는지 먼저 보자.

`로깅 래퍼`를 전부 Proxy로 부르는 경우:
권한, 접근 제어, 지연 로딩 없이 순수하게 기능을 겹쳐 붙이는 목적이면 Decorator가 더 읽힌다. "대신 받아 통제"보다 "옆에 기능 추가"가 중심인지 확인하면 된다.

## 다음 학습

- wrapper 패턴 입문 설명이 더 필요하면 [데코레이터와 프록시 기초](./decorator-proxy-basics.md)
- 구조와 트레이드오프를 더 깊게 보려면 [데코레이터 vs 프록시](./decorator-vs-proxy.md)
- Spring `@Transactional`과 AOP를 프록시 관점으로 연결하려면 [AOP와 프록시 메커니즘](../spring/aop-proxy-mechanism.md)
- 다른 래퍼 패턴까지 함께 자르려면 [Adapter vs Facade vs Decorator: 처음 배우는 래퍼 패턴 큰 그림](./adapter-vs-facade-vs-decorator-beginner-router.md)
