# Adapter vs Facade vs Decorator: 처음 배우는 래퍼 패턴 큰 그림

> 한 줄 요약: 처음 배우는데 wrapper처럼 다 비슷해 보이면, Adapter는 "형태를 맞추는 번역", Facade는 "복잡한 사용법을 줄이는 창구", Decorator는 "같은 인터페이스에 기능을 덧붙이는 래퍼"로 먼저 나누면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [어댑터 패턴 기초](./adapter-basics.md)
- [데코레이터와 프록시 기초](./decorator-proxy-basics.md)
- [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [AOP와 프록시 메커니즘](../spring/aop-proxy-mechanism.md)

retrieval-anchor-keywords: adapter facade decorator beginner, wrapper pattern confusion, adapter vs facade vs decorator, 처음 배우는데 wrapper, 큰 그림 wrapper pattern, adapter facade decorator 차이, 언제 쓰는지 adapter facade decorator, 번역 vs 단순화 vs 기능추가, adapter냐 facade냐 decorator냐, facade adapter decorator quick check, wrapper 패턴 헷갈림, beginner wrapper router

## 핵심 개념

세 패턴은 모두 "중간에 하나 더 감싼다"는 공통점이 있어서 처음 보면 다 비슷해 보인다.

하지만 초보자 기준으로는 "무엇을 바꾸려는가"만 먼저 보면 된다.

- Adapter: 바깥 API와 우리 API의 **형태 차이**를 맞춘다.
- Facade: 여러 단계의 **사용 순서**를 한 창구로 단순화한다.
- Decorator: 같은 인터페이스 위에 **기능을 하나 더 얹는다**.

이 문서는 정의를 깊게 파기보다, 처음 검색했을 때 어느 문서로 들어가야 하는지 빨리 고르는 entrypoint다.

## 한눈에 보기

처음 배우는데 10초 안에 가르려면 아래 질문 하나씩만 본다.

| 지금 보이는 문제 | 먼저 떠올릴 패턴 | 한 줄 기준 |
|---|---|---|
| 외부 SDK 메서드 이름, 타입, 단위가 우리 코드와 안 맞는다 | Adapter | "형태를 맞춰 붙인다" |
| 여러 서비스 호출 순서를 한 메서드로 감추고 싶다 | Facade | "복잡한 사용법을 줄인다" |
| 원래 기능은 두고 로그, 캐시, 압축 같은 기능을 더하고 싶다 | Decorator | "같은 인터페이스에 기능을 덧붙인다" |

한 줄로 줄이면 이렇다.

```text
안 맞아서 번역하면 Adapter
복잡해서 입구를 줄이면 Facade
같은 틀에 기능을 더하면 Decorator
```

## 상세 분해

### Adapter

결제 SDK의 `charge(double dollar)`를 우리 서비스의 `pay(int won)`로 바꾸는 장면처럼, 인터페이스 불일치가 핵심이면 Adapter 쪽이다.

- 메서드 이름이 다르다
- 타입이나 단위가 다르다
- 외부 응답 코드를 우리 enum으로 바꿔야 한다

### Facade

`orderFacade.placeOrder()` 하나가 재고 확인, 결제, 배송 준비를 순서대로 묶는 장면이면 Facade에 가깝다.

- 외부 호출자는 내부 순서를 몰라도 된다
- 번역보다 사용 순서 정리가 중심이다
- "입구를 하나로 줄였다"는 감각이 강하다

### Decorator

기존 `OrderService`는 그대로 두고, 그 앞뒤에 로깅이나 메트릭을 붙이는 장면이면 Decorator를 먼저 본다.

- 원본과 같은 인터페이스를 유지한다
- 원본 기능을 없애지 않고 더 얹는다
- 기능을 여러 겹으로 쌓을 수도 있다

## 흔한 오해와 함정

- "감싸기만 하면 다 Adapter 아닌가요?" 아니다. 번역이 없고 사용 순서만 감추면 Facade일 수 있다.
- "Facade도 결국 메서드 하나로 감싸니까 Decorator 아닌가요?" 아니다. Facade는 같은 인터페이스에 기능을 추가하는 패턴이 아니라, 복잡한 하위 시스템의 입구를 단순화하는 패턴이다.
- "로그를 붙였는데 외부 SDK도 같이 감쌌다. 그럼 Adapter인가요?" 핵심 책임을 본다. 번역이 중심이면 Adapter, 기능 추가가 중심이면 Decorator다.
- "DTO 바꾸는 코드는 전부 Adapter인가요?" 단순 값 복사만 하면 mapper/helper일 수도 있다. 외부 인터페이스 경계를 고정하는지 봐야 한다.

## 실무에서 쓰는 모습

가장 흔한 beginner 예시는 아래 세 장면이다.

| 장면 | 자연스러운 선택 | 이유 |
|---|---|---|
| PG사 응답 `"OK"`를 `PaymentStatus.SUCCESS`로 바꾼다 | Adapter | 외부 표현을 우리 표준으로 번역한다 |
| 주문 생성 흐름을 `placeOrder()` 하나로 묶는다 | Facade | 여러 단계를 한 창구로 감춘다 |
| 파일 저장 서비스 앞에 압축/로깅 래퍼를 붙인다 | Decorator | 같은 인터페이스에 부가 기능을 더한다 |

처음에는 패턴 이름보다 "번역", "단순화", "기능 추가" 세 단어가 더 중요하다.

## 더 깊이 가려면

- Adapter 쪽이 더 가깝다면 [어댑터 패턴 기초](./adapter-basics.md)에서 `Target / Adapter / Adaptee` 그림부터 본다.
- Decorator 쪽이 더 가깝다면 [데코레이터와 프록시 기초](./decorator-proxy-basics.md)에서 기능 추가와 접근 제어를 먼저 나눈다.
- Proxy까지 같이 섞여 헷갈리면 [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)로 넘어가 wrapper 비교를 마무리한다.

## 면접/시니어 질문 미리보기

> Q: Adapter와 Facade를 한 문장으로 구분해 보라.
> 의도: 인터페이스 번역과 사용성 단순화를 분리해서 설명하는지 본다.
> 핵심: Adapter는 안 맞는 인터페이스를 맞추고, Facade는 복잡한 하위 시스템의 입구를 줄인다.

> Q: Decorator가 Facade와 다른 이유는 무엇인가?
> 의도: 같은 "wrapper" 모양과 패턴 의도를 구분하는지 본다.
> 핵심: Decorator는 같은 인터페이스에 기능을 더하고, Facade는 복잡한 사용법을 감춘다.

## 한 줄 정리

처음 배우는데 wrapper 패턴이 헷갈리면 "번역이면 Adapter, 복잡한 입구 정리면 Facade, 같은 인터페이스에 기능 추가면 Decorator" 순서로 먼저 자르면 된다.
