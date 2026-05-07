---
schema_version: 3
title: Facade vs Adapter vs Proxy 결정 가이드
concept_id: design-pattern/facade-vs-adapter-vs-proxy-decision-guide
canonical: false
category: design-pattern
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids: []
review_feedback_tags:
  - wrapper-intent-separation
  - boundary-translation-vs-call-control
  - facade-entrypoint-confusion
aliases:
  - facade vs adapter vs proxy decision guide
  - facade adapter proxy chooser
  - 번역 창구 대리자 구분
  - 외부 api 번역이냐 호출 제어냐
  - facade adapter proxy 차이 빠른 판단
  - 복잡한 흐름 단순화와 인터페이스 변환 차이
  - spring aop proxy와 facade adapter 구분
symptoms:
  - 외부 SDK를 감쌌는데 facade인지 adapter인지 proxy인지 모르겠어
  - 메서드 하나로 묶은 클래스와 호출을 가로채는 클래스를 같은 패턴으로 설명하고 있어
  - 트랜잭션이나 캐시 래퍼를 facade처럼 이해하고 있어
intents:
  - comparison
  - design
  - definition
prerequisites:
  - design-pattern/object-oriented-design-pattern-basics
  - design-pattern/composition-over-inheritance-basics
next_docs:
  - design-pattern/adapter-vs-facade-vs-decorator-beginner-router
  - design-pattern/decorator-vs-proxy-decision-guide
  - design-pattern/facade-vs-adapter-vs-proxy
linked_paths:
  - contents/design-pattern/adapter-vs-facade-vs-decorator-beginner-router.md
  - contents/design-pattern/facade-vs-adapter-vs-proxy.md
  - contents/design-pattern/adapter.md
  - contents/design-pattern/facade-anti-corruption-seam.md
  - contents/spring/aop-proxy-mechanism.md
confusable_with:
  - design-pattern/adapter-vs-facade-vs-decorator-beginner-router
  - design-pattern/facade-vs-adapter-vs-proxy
  - spring/aop-proxy-mechanism
forbidden_neighbors: []
expected_queries:
  - 외부 API를 감싼 클래스가 facade인지 adapter인지 proxy인지 어떻게 구분해?
  - 호출 순서를 숨기는 것과 인터페이스를 맞추는 것을 한 번에 비교해줘
  - Spring AOP 같은 호출 가로채기는 왜 facade가 아니라 proxy야?
  - 결제 SDK wrapper가 번역기인지 단순 창구인지 대리자인지 판단 기준이 뭐야?
  - facade, adapter, proxy를 래퍼 목적 기준으로 빨리 가르는 표가 필요해
contextual_chunk_prefix: |
  이 문서는 Facade, Adapter, Proxy를 한 번에 헷갈리는 학습자를 위한 chooser다.
  외부 API 번역인지, 복잡한 호출 순서를 한 창구로 줄이는지, 실제 객체 호출 전에
  권한·캐시·트랜잭션 같은 제어를 넣는지 목적 기준으로 빠르게 가르는 문맥에서 검색된다.
---

# Facade vs Adapter vs Proxy 결정 가이드

> 한 줄 요약: 인터페이스를 우리 쪽 말로 번역하면 Adapter, 여러 단계를 한 입구로 단순화하면 Facade, 실제 호출 전후를 통제하면 Proxy다.

**난이도: 🟢 Beginner**

관련 문서:

- [Adapter vs Facade vs Decorator: 처음 배우는 래퍼 패턴 큰 그림](./adapter-vs-facade-vs-decorator-beginner-router.md)
- [Facade vs Adapter vs Proxy](./facade-vs-adapter-vs-proxy.md)
- [Adapter Pattern 기초](./adapter.md)
- [Facade as Anti-Corruption Seam: 복잡한 외부 세계를 내부로 번지지 않게 막기](./facade-anti-corruption-seam.md)
- [AOP와 프록시 메커니즘](../spring/aop-proxy-mechanism.md)

retrieval-anchor-keywords: facade vs adapter vs proxy, facade adapter proxy chooser, adapter facade proxy difference, wrapper intent separation, interface translation vs simplified entrypoint, proxy call control basics, spring aop proxy not facade, 외부 sdk wrapper 뭐예요, facade adapter proxy 헷갈려요, 번역 창구 대리자 구분, 언제 facade 언제 adapter, 호출 가로채기 proxy 왜

---

## 이 문서는 언제 읽으면 좋은가

아래처럼 "감싼 클래스는 있는데 이름을 못 붙이겠다"는 순간에 이 문서를 먼저 보면 된다.

- 외부 SDK를 우리 서비스 인터페이스에 맞췄는데 이게 Adapter인지 Facade인지 모르겠다
- `placeOrder()`처럼 한 메서드로 절차를 숨겼는데 Proxy 같아 보이기도 한다
- Spring AOP, 캐시, 권한 체크 래퍼를 Facade처럼 설명하고 있다

핵심은 "래퍼가 있다"가 아니라 **무엇을 단순화하거나 통제하느냐**다.

## 30초 선택표

| 지금 코드가 푸는 질문 | 먼저 볼 패턴 | 왜 그쪽이 맞는가 |
|---|---|---|
| 외부 SDK 메서드 이름, 타입, 단위가 우리 코드와 안 맞는가? | Adapter | 호출 형태를 우리 쪽 인터페이스로 번역하는 문제다. |
| 여러 서비스 호출 순서를 `placeOrder()` 같은 한 메서드로 감추고 싶은가? | Facade | 사용자가 알아야 할 절차를 줄이는 입구가 목적이다. |
| 권한, 캐시, 트랜잭션처럼 실제 객체를 바로 부르지 않게 해야 하는가? | Proxy | 원본 호출 전후를 대신 통제하는 대리자가 필요하다. |
| 호출자는 내부 복잡도를 몰라도 되지만 새 인터페이스를 배울 필요는 없는가? | Facade | 번역보다 진입점 단순화가 중심이다. |
| 원본 호출 자체를 생략하거나 지연할 수 있는가? | Proxy | 호출 여부와 시점을 제어하고 있다. |

짧게 외우면 다음처럼 자를 수 있다.

- **말을 바꿔 주면** Adapter
- **절차를 줄여 주면** Facade
- **호출을 통제하면** Proxy

## 같은 예시를 세 패턴으로 나눠 보기

결제 SDK를 붙이는 상황을 떠올리면 구분이 쉬워진다.

| 코드 모양 | 더 가까운 패턴 | 이유 |
|---|---|---|
| `charge(double usd)`를 `pay(int won)`으로 감싼다 | Adapter | 외부 API를 우리 도메인 언어로 번역한다. |
| 결제, 재고, 배송 호출을 `orderFacade.placeOrder()` 하나로 묶는다 | Facade | 여러 단계를 한 입구로 정리한다. |
| `@Transactional`, 캐시, 권한 체크가 서비스 호출 앞에서 가로챈다 | Proxy | 실제 호출 전에 경계를 통제한다. |

비유로 보면 Adapter는 "통역사", Facade는 "종합 안내 데스크", Proxy는 "출입 통제 대리인"에 가깝다. 다만 비유는 입문용일 뿐이고, 실제 판단은 번역인지 단순화인지 호출 제어인지로 자르는 편이 안전하다.

## 자주 헷갈리는 오해

`외부 SDK wrapper`를 전부 Facade라고 부르는 경우:
메서드 이름과 데이터 모양을 우리 인터페이스에 맞추는 번역이 중심이면 Adapter가 더 정확하다. "달러를 원화로 바꾼다", "응답 JSON을 우리 DTO로 바꾼다"는 말이 나오면 Adapter 신호다.

`주문 흐름 정리 클래스`를 Proxy로 설명하는 경우:
원본 접근 통제보다 여러 단계를 한 진입점으로 묶는 게 핵심이면 Facade다. 실제 객체를 대신 감시하는 것이 아니라 사용 순서를 단순화하는 것이다.

`Spring AOP`나 캐시 래퍼를 Facade로 보는 경우:
겉으로는 서비스 앞에 하나 더 서 있지만 본질은 호출 경계 제어다. self-invocation, lazy loading, 권한 체크 같은 말이 나오면 Proxy 쪽으로 자르는 편이 맞다.

## 다음에 무엇을 보면 좋은가

- 래퍼 패턴 전체 큰 그림이 먼저 필요하면 [Adapter vs Facade vs Decorator: 처음 배우는 래퍼 패턴 큰 그림](./adapter-vs-facade-vs-decorator-beginner-router.md)
- Adapter와 Facade 경계를 외부 시스템 번역 관점으로 더 보고 싶으면 [Facade as Anti-Corruption Seam: 복잡한 외부 세계를 내부로 번지지 않게 막기](./facade-anti-corruption-seam.md)
- Proxy를 Spring 호출 제어와 연결해서 보려면 [AOP와 프록시 메커니즘](../spring/aop-proxy-mechanism.md)
- 세 패턴 비교를 더 길게 읽고 싶으면 [Facade vs Adapter vs Proxy](./facade-vs-adapter-vs-proxy.md)

## 한 줄 정리

외부 세계의 말을 우리 쪽으로 바꾸면 Adapter, 복잡한 절차를 한 입구로 줄이면 Facade, 원본 호출 전후를 대신 통제하면 Proxy다.
