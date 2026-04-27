# 템플릿 메소드 첫 질문 라우터: `hook method`, `abstract step`, `template method vs strategy`

> 한 줄 요약: 처음 배우는데 `hook method`, `abstract step`, `template method vs strategy`가 한꺼번에 헷갈리면, 먼저 "부모가 흐름을 쥔다 vs 호출자가 전략을 고른다" 큰 그림으로 자르고 다음 primer로 보내는 작은 엔트리포인트다.

**난이도: 🟢 Beginner**

> Beginner Route: `[entrypoint]` 이 문서 -> `[bridge]` [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) -> `[deep dive]` [템플릿 메소드 패턴](./template-method.md)

관련 문서:

- [템플릿 메소드 패턴 기초](./template-method-basics.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지](./abstract-class-vs-interface-injection-bridge.md)
- [추상 클래스 vs 인터페이스 입문](../language/java/java-abstract-class-vs-interface-basics.md)
- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
- [템플릿 메소드 패턴](./template-method.md)
- [Template Hook Smells](./template-hook-smells.md)
- [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: template method beginner route, hook method primer, abstract step primer, template method vs strategy beginner, abstract step vs hook, hook vs abstract step, required step vs optional hook, 필수 빈칸 선택 빈칸, 처음 배우는데 hook abstract step 차이, 추상 클래스면 다 템플릿 메소드인가, 부모가 흐름을 쥔다, 호출자가 전략을 고른다, hook은 선택 빈칸, abstract step은 필수 빈칸, onceperrequestfilter beginner route

---

## 큰 그림 먼저

처음 배우는데는 아래 두 문장만 먼저 잡으면 된다.

- 템플릿 메소드: **부모가 흐름을 쥔다**
- 전략: **호출자가 전략을 고른다**

`hook method`와 `abstract step`은 이 큰 그림 안에서 보는 빈칸 종류다.

| 용어 | 처음 보는 사람용 뜻 | 바로 이어질 질문 |
|---|---|---|
| `abstract step` | 없으면 흐름이 완성되지 않는 **필수 빈칸** | "어떤 단계가 꼭 달라져야 하지?" |
| `hook method` | 기본값으로도 흐름은 돌고, 필요할 때만 여는 **선택 빈칸** | "조금만 덧붙이면 되나?" |
| `strategy` | 아예 다른 규칙 객체를 **호출자가 골라 끼우는 방식** | "요청마다 바뀌나?" |

## 초미니 회상 카드: `abstract step` vs `hook`

처음 배우는데 용어가 바로 안 붙으면, 큰 그림보다 이 카드부터 짧게 떠올리면 된다.

| 질문 | `abstract step` | `hook method` |
|---|---|---|
| 이 단계가 없으면 흐름이 끝나나 | 예. 그래서 **필수**다 | 아니오. 기본 구현으로도 돈다 |
| 자식이 꼭 구현해야 하나 | 보통 예 | 아니오. 필요할 때만 덧붙인다 |
| 한 줄 기억법 | `없으면 흐름이 비는 칸` | `있으면 좋지만 없어도 도는 칸` |

- `validate()`가 빠지면 처리 자체가 안 끝난다 -> `abstract step`
- `afterSend()`를 안 바꿔도 전송은 끝난다 -> `hook method`

## 30초 라우팅

| 지금 질문 | 먼저 볼 문서 | 이유 |
|---|---|---|
| `hook method가 뭐예요`, `abstract step이 뭐예요` | [템플릿 메소드 패턴 기초](./template-method-basics.md) | 기초, 큰 그림, 필수 빈칸 vs 선택 빈칸부터 잡는 게 가장 빠르다 |
| `template method vs strategy가 뭐가 달라요` | [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) | 상속 vs 객체 주입, 부모 vs 호출자 선택권을 바로 비교한다 |
| `추상 클래스면 다 템플릿 메소드 아닌가요` | [추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지](./abstract-class-vs-interface-injection-bridge.md) | base class 재사용과 템플릿 메소드 오해를 짧은 반례로 먼저 끊는다 |
| `OncePerRequestFilter`, `HttpServlet`이 왜 템플릿 메소드 예시예요` | [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md) | framework 이름이 먼저 보여도 primer 다음 단계에서 읽는 편이 덜 헷갈린다 |
| `hook가 너무 많아졌는데 이게 맞나요` | [Template Hook Smells](./template-hook-smells.md) | 이건 기초보다 smell 점검 질문이다 |

## 오해 컷: 추상 클래스면 다 템플릿 메소드인가?

아니다. 추상 클래스는 그냥 공통 필드나 도우미 메서드를 묶는 base class일 수도 있다.
템플릿 메소드라고 부르려면 부모가 `run()` 같은 **고정 순서**를 쥐고, 하위 클래스는 그 안의 일부 단계만 채워야 한다.
이 반례를 먼저 보고 싶으면 [추상 클래스냐 인터페이스+주입이냐: 템플릿 메소드·전략·조합 브리지](./abstract-class-vs-interface-injection-bridge.md)로 가면 된다.

## 처음 배우는데 헷갈리는 이유

초보자는 보통 용어를 먼저 듣고 구조를 나중에 본다.
그래서 아래 세 가지가 한꺼번에 섞인다.

1. `hook method`와 `abstract step`이 둘 다 override처럼 보인다.
2. `template method`와 `strategy`가 둘 다 "뭔가 바꾸는 패턴"처럼 보인다.
3. 추상 클래스만 보여도 템플릿 메소드라고 부르고 싶어진다.
4. `OncePerRequestFilter` 같은 프레임워크 예시가 먼저 보여서 기초보다 API 이름이 더 크게 보인다.

이때는 용어를 외우기보다 질문을 이렇게 다시 자르면 된다.

- 순서를 부모가 끝까지 고정해야 하나?
- 없으면 흐름이 깨지는 필수 단계인가?
- 요청마다 구현을 바꿔 끼워야 하나?

## 한 줄 기준표

| 질문 | 템플릿 메소드 쪽 신호 | 전략 쪽 신호 |
|---|---|---|
| 누가 순서를 쥐나 | 부모 클래스 | 호출자/설정/DI |
| 바뀌는 범위가 어디까지인가 | 고정된 흐름 안의 일부 단계 | 규칙/알고리즘 전체 |
| `hook`이 맞는가 | 기본 구현으로도 전체 흐름이 완료된다 | 아니다. 아예 다른 구현을 골라야 한다 |

## 추천 읽기 순서

1. [템플릿 메소드 패턴 기초](./template-method-basics.md)
2. [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
3. 질문이 프레임워크 예시라면 [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
4. 기초를 잡은 뒤 더 깊게 보면 [템플릿 메소드 패턴](./template-method.md)
5. 훅이 과하게 늘어난 상황만 따로 보고 싶을 때 [Template Hook Smells](./template-hook-smells.md)

## 한 줄 정리

처음 배우는데는 `hook method`, `abstract step`, `template method vs strategy`를 따로 외우기보다, 먼저 **"부모가 흐름을 쥔다 vs 호출자가 전략을 고른다"**를 잡고 `필수 빈칸 vs 선택 빈칸`으로 내려오면 된다.
