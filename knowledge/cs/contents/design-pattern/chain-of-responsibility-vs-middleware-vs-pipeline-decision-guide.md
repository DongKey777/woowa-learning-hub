---
schema_version: 3
title: Chain of Responsibility vs Middleware vs Pipeline 결정 가이드
concept_id: design-pattern/chain-of-responsibility-vs-middleware-vs-pipeline-decision-guide
canonical: false
category: design-pattern
difficulty: intermediate
doc_role: chooser
level: intermediate
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - request-flow-pattern-boundary
  - short-circuit-vs-stage-transform
  - middleware-chain-confusion
aliases:
  - chain of responsibility vs middleware vs pipeline
  - 책임 연쇄 미들웨어 파이프라인 구분
  - 요청 처리 스택이냐 단계 변환 흐름이냐
  - filter interceptor middleware pipeline 차이
  - short circuit 체인이랑 stage 변환을 어떻게 나눠
  - 요청 앞단 공통 처리와 데이터 변환 단계를 헷갈림
symptoms:
  - 필터 체인을 pipeline이라고 부르는데 뭔가 설명이 안 맞아
  - middleware랑 chain of responsibility를 같은 말처럼 쓰고 있어
  - 검증 단계와 요청 차단 단계를 한 패턴으로 묶어서 헷갈려
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/chain-of-responsibility-filters-interceptors
  - design-pattern/middleware-pattern-language
next_docs:
  - design-pattern/chain-of-responsibility-filters-interceptors
  - design-pattern/middleware-pattern-language
  - design-pattern/pipeline-vs-chain-of-responsibility
linked_paths:
  - contents/design-pattern/chain-of-responsibility-filters-interceptors.md
  - contents/design-pattern/middleware-pattern-language.md
  - contents/design-pattern/pipeline-vs-chain-of-responsibility.md
  - contents/design-pattern/template-method-vs-filter-interceptor-chain.md
confusable_with:
  - design-pattern/chain-of-responsibility-filters-interceptors
  - design-pattern/middleware-pattern-language
  - design-pattern/pipeline-vs-chain-of-responsibility
forbidden_neighbors:
  - contents/design-pattern/chain-of-responsibility-filters-interceptors.md
  - contents/design-pattern/pipeline-vs-chain-of-responsibility.md
expected_queries:
  - 요청을 여러 단계로 처리할 때 middleware, 책임 연쇄, pipeline을 어떤 기준으로 골라야 해?
  - 인증이나 로깅처럼 앞에서 끊을 수 있는 흐름과 데이터 변환 단계를 한 번에 구분해줘
  - filter interceptor 스택을 pipeline이라고 설명해도 되는지 판단 기준이 필요해
  - 배치 정제 단계와 HTTP 공통 처리 스택은 왜 같은 구조처럼 보여도 다르게 불러?
  - 다음 단계로 넘길지 중단할지가 중요한데 이건 middleware보다 chain 쪽이 맞아?
contextual_chunk_prefix: |
  이 문서는 요청 처리 흐름을 설명할 때 Chain of Responsibility, Middleware,
  Pipeline을 한 번에 헷갈리는 학습자를 위한 chooser다. 인증과 로깅 같은
  공통 관심사 스택, filter와 interceptor, short-circuit, 다음 단계로 전달,
  batch 정제처럼 stage별 변환, request pipeline이라고 불렀는데 설명이
  어색한 상황을 어떤 기준으로 가를지 묻는 검색에 매핑된다.
---

# Chain of Responsibility vs Middleware vs Pipeline 결정 가이드

## 한 줄 요약

> 요청을 중간에서 끊거나 넘길 책임 분리가 핵심이면 Chain of Responsibility, 요청/응답 공통 관심사를 순서대로 꽂아 조합하면 Middleware, 입력이 단계별로 변환돼 최종 산출물로 흐르면 Pipeline이다.

## 결정 매트릭스

| 지금 코드가 푸는 질문 | 먼저 볼 패턴 | 왜 그쪽이 맞는가 |
|---|---|---|
| 각 단계가 요청을 계속 넘길지 여기서 끝낼지 결정하는가? | Chain of Responsibility | 제어권 이동과 short-circuit가 구조의 핵심이다. |
| 인증, 로깅, 추적처럼 요청 전후 공통 관심사를 스택으로 조합하는가? | Middleware | 요청/응답 경계에 끼는 조합 순서가 정책이 된다. |
| 한 단계의 출력이 다음 단계 입력이 되어 데이터가 계속 가공되는가? | Pipeline | 책임 위임보다 단계별 변환 흐름이 중심이다. |
| HTTP 프레임워크에서 `next()`나 `doFilter()` 같은 관용구가 보이는가? | Middleware | 프레임워크가 제공하는 요청 스택 모델에 기대고 있다. |
| 배치 정제, 포맷 변환, 점수 계산처럼 최종 산출물을 만드는 과정인가? | Pipeline | 중단보다 누적 변환 결과가 더 중요하다. |

`인증 실패면 바로 401`은 Chain of Responsibility 쪽 감각이고, Express나 Nest의 요청 스택처럼 공통 처리를 꽂아 넣는 건 Middleware 감각이다. CSV 정제나 이벤트 필드 변환처럼 단계별 산출물이 이어지면 Pipeline으로 보는 편이 정확하다.

## 흔한 오선택

`Filter`나 `Interceptor` 흐름을 전부 Pipeline이라고 부르는 경우:
단계가 여러 개라는 사실만 보고 이름을 붙이면 short-circuit 의미가 사라진다. 인증 실패, 권한 부족, rate limit처럼 "여기서 끊는다"가 중요하면 먼저 Chain of Responsibility로 읽어야 한다.

`Middleware`를 그냥 Chain of Responsibility의 동의어로 쓰는 경우:
개념적으로 겹치지만 학습자가 보는 코드는 대개 프레임워크가 제공한 요청 스택이다. `next()` 순서, 바깥쪽 에러 핸들러, 요청/응답 wrapping이 핵심이면 Middleware라는 실행 문맥을 드러내는 편이 설명력이 높다.

`배치 검증 단계`를 Middleware라고 부르는 경우:
HTTP 요청 경계도 없고 공통 관심사 조합보다 데이터 가공 결과가 중요하면 Middleware보다 Pipeline이 자연스럽다. `입력 -> 정규화 -> 변환 -> 저장`처럼 산출물이 이어지면 Pipeline 신호다.

## 다음 학습

- Filter와 Interceptor 예시로 책임 연쇄를 먼저 굳히려면 [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
- 요청/응답 공통 관심사 스택 언어를 더 읽으려면 [Middleware Pattern Language: 요청과 응답 사이에 끼는 공통 관심사](./middleware-pattern-language.md)
- 데이터 변환 흐름과 short-circuit 차이를 더 깊게 보려면 [Pipeline vs Chain of Responsibility](./pipeline-vs-chain-of-responsibility.md)
- Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter` 경계까지 붙여서 보려면 [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
