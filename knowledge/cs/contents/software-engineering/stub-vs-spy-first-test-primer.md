# Stub vs Spy 첫 테스트 프라이머

> 한 줄 요약: 첫 테스트에서 `고정된 반환값만 필요하면 stub`, `정말 호출됐는지 기록이 필요하면 spy`로 나누면 초심자도 `결과를 만드는 더블`과 `상호작용을 기록하는 더블`을 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [테스트 전략 기초](./test-strategy-basics.md)
- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md)
- [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md)
- [테스트 전략과 테스트 더블](./testing-strategy-and-test-doubles.md)
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md)
- [software-engineering 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: stub vs spy first test, stub spy beginner, stub return value basics, spy call recording basics, 처음 stub spy 헷갈려, 왜 stub 말고 spy, when to use stub, when to use spy, first test double choice, interaction recording double, fixed return double, what is stub vs spy

## 핵심 개념

이 문서의 질문은 "`fake`와 `mock`은 대충 알겠는데, `stub`과 `spy`는 첫 테스트에서 어떻게 구분하죠?`"다. 초심자가 가장 자주 섞는 장면은 "`값 하나만 돌려주면 되는데 spy를 붙이거나`, `호출 기록을 봐야 하는데 stub만 두는 경우`"다.

짧게 자르면 기준은 하나다.

- `이 테스트가 굴러가려면 고정된 답 하나만 있으면 된다`면 stub이다.
- `그 의존성이 실제로 호출됐는지, 몇 번 호출됐는지`가 질문이면 spy다.

즉 stub은 **결과를 만들어 주는 버튼**, spy는 **호출 흔적을 남기는 기록계**에 가깝다.

## 한눈에 보기

| 지금 확인하려는 질문 | 더 먼저 고를 것 | 이유 |
|---|---|---|
| "`회원 등급 조회가 GOLD를 돌려주면 할인되나?`" | stub | 분기 조건에 필요한 입력값만 고정하면 된다 |
| "`알림 전송이 정말 1번 일어났나?`" | spy | 호출 자체가 확인 대상이다 |
| "`결제 승인 결과가 APPROVED일 때 주문이 저장되나?`" | stub | 외부 응답 값을 고정하면 규칙 테스트가 된다 |
| "`실패 시 이벤트 발행이 일어나지 않았나?`" | spy | 호출 여부가 바로 답이다 |

- 처음엔 `값이 필요하냐, 기록이 필요하냐` 두 칸만 고르면 된다.
- 반환값도 필요하고 호출 기록도 필요하면, starter에서는 먼저 `핵심 질문이 어느 쪽인지`를 고르고 나머지는 후순위로 둔다.

## 첫 테스트에서 고르는 순서

| 순서 | 먼저 적을 질문 | 여기서 멈추는 기준 |
|---|---|---|
| 1 | 이 의존성이 테스트에 무엇을 제공해야 하나 | `값`인지 `호출 기록`인지 한 단어로 말할 수 있다 |
| 2 | 값만 있으면 규칙이 설명되는가 | 그렇다면 stub으로 시작한다 |
| 3 | 호출 여부가 요구사항 문장에 들어가는가 | 그렇다면 spy로 바꾼다 |
| 4 | 둘 다 필요해 보여도 첫 질문 1개만 남긴다 | 테스트 설명이 한 문장으로 읽히면 충분하다 |

이 순서를 쓰는 이유는 spy를 너무 빨리 꺼내면 테스트가 "`호출했다`"에 과하게 집중하기 쉽기 때문이다. 초심자 첫 테스트는 보통 "`어떤 값이 들어오면 어떤 결과가 나와야 하나`"가 먼저라서 stub이 먼저 등장하는 경우가 많다.

## 흔한 오해와 함정

- "`stub`은 그냥 덜 강한 `mock` 아닌가요?"
  그렇게 외우면 계속 헷갈린다. stub은 강약 문제가 아니라 `고정된 입력을 만드는 역할`에 더 가깝다.
- "`spy`는 항상 mock 프레임워크로만 만들어야 하나요?"
  아니다. 핵심은 기술보다 `호출 기록을 남기는 더블`이라는 역할이다.
- "`반환값도 주고 호출도 기록하면 spy 아닌가요?`"
  구현체에 따라 둘 다 할 수 있지만, beginner starter에서는 `이번 테스트의 핵심 질문`으로 먼저 이름을 붙이는 편이 읽기 쉽다.
- "`repository에도 spy를 써도 되나요?`"
  가능하다. 다만 중복 검사, 저장 결과처럼 결과 질문이 중심이면 [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md) 쪽 기준이 먼저다.

## 실무에서 쓰는 모습

주문 서비스가 외부 `MembershipClient`에서 회원 등급을 받아 할인율을 고른다고 해 보자. 첫 질문이 "`GOLD면 10% 할인되나?`"라면 고정된 등급만 있으면 충분하니 stub이 자연스럽다.

```java
MembershipClient client = stubMembership("GOLD");

DiscountService service = new DiscountService(client);

assertThat(service.discountFor("member-1")).isEqualTo(1000);
```

이 테스트가 먼저 말하는 것은 "`GOLD라는 입력이 들어오면 할인 결과가 이렇게 나온다`"다.

반대로 주문 완료 뒤 알림 전송이 일어났는지 보고 싶다면 spy가 더 직접적이다.

```java
OrderNotifierSpy notifier = new OrderNotifierSpy();

service.place(command("ORDER-001"));

assertThat(notifier.count()).isEqualTo(1);
assertThat(notifier.lastOrderNumber()).isEqualTo("ORDER-001");
```

여기서 핵심 문장은 "`주문이 성공하면 알림 요청이 기록된다`"다. 즉 같은 서비스 안에서도 할인 규칙 쪽은 stub, 알림 경계 쪽은 spy로 갈라질 수 있다.

## 언제 stub에서 spy로 올리나

| 신호 | stub으로 충분 | spy가 필요한 순간 |
|---|---|---|
| 테스트의 핵심 문장 | "`이 값을 받으면 결과가 이렇다`" | "`이 의존성을 호출했다/안 했다`" |
| 더블이 알려주는 것 | 고정된 입력 | 호출 횟수, 전달 인자, 마지막 호출 |
| 대표 예시 | 등급 조회, 환율 조회, 승인 결과 고정 | 알림 전송, 이벤트 발행, 재시도 호출 기록 |

짧게 말하면 stub은 **분기를 여는 열쇠**, spy는 **실행 흔적을 남기는 메모장**이다. 그래서 "`왜 spy 대신 stub이면 안 되죠?`"라는 질문에는 "`호출 여부가 요구사항 문장에 들어가느냐`"로 답하면 된다.

## 더 깊이 가려면

- [테스트 전략 기초](./test-strategy-basics.md): 첫 failing test를 unit, slice, integration 중 어디에 둘지 먼저 고를 때
- [Fake vs Mock 첫 테스트 프라이머](./fake-vs-mock-first-test-primer.md): 결과를 읽는 fake와 호출을 읽는 mock의 큰 축을 먼저 잡고 싶을 때
- [Outbound Notifier Mock Boundary Primer](./outbound-notifier-mock-boundary-primer.md): spy/mock이 outbound notifier 경계에서 왜 자연스러운지 더 좁게 볼 때
- [Spring 테스트 기초: `@SpringBootTest`부터 슬라이스 테스트까지](../spring/spring-testing-basics.md): 테스트 더블 선택 뒤 Spring 테스트 범위를 이어서 고를 때

## 면접/시니어 질문 미리보기

| 질문 | 왜 묻나 | 핵심 답변 |
|---|---|---|
| "stub과 spy를 첫 테스트에서 어떻게 구분하나요?" | 테스트 더블 선택 기준을 본다 | 고정된 반환값만 필요하면 stub, 호출 기록이 필요하면 spy다 |
| "왜 beginner starter에서 stub이 더 자주 먼저 나오나요?" | 결과 중심 테스트 감각을 본다 | 첫 테스트는 보통 규칙 결과를 잠그는 목적이라 입력값 고정만으로 충분한 경우가 많기 때문이다 |
| "spy를 남발하면 어떤 문제가 생기나요?" | 구현 결합도 감각을 본다 | 결과보다 호출 순서와 횟수에 과하게 묶여 리팩터링 내성이 떨어질 수 있다 |

## 한 줄 정리

첫 테스트에서 `값을 만들어 분기를 열면 stub`, `호출 흔적을 남겨 상호작용을 확인하면 spy`라고 자르면 beginner가 가장 많이 하는 혼동을 빠르게 줄일 수 있다.
