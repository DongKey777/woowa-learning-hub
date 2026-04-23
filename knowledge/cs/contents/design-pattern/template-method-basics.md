# 템플릿 메소드 패턴 기초 (Template Method Pattern Basics)

> 한 줄 요약: 템플릿 메소드 패턴은 알고리즘의 뼈대를 부모 클래스에 고정하고, 세부 단계만 서브클래스에서 채우게 해서 공통 흐름을 재사용한다.

**난이도: 🟢 Beginner**

관련 문서:

- [템플릿 메소드 (Template Method) 심화](./template-method.md)
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
- [전략 패턴 기초](./strategy-pattern-basics.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [Spring AOP 기초](../spring/spring-aop-basics.md)

retrieval-anchor-keywords: template method basics, 템플릿 메소드 패턴 기초, 템플릿 메소드 패턴이 뭔가요, template method beginner, abstract class template, 추상 메서드 패턴 입문, hook method beginner, abstract step beginner, hook method vs abstract step beginner, hook method vs abstract method beginner, 훅 메서드 기초, 추상 단계 기초, 추상 메서드 기초, 처음 배우는데 hook method, 처음 배우는데 훅 메서드, 처음 배우는데 abstract step, 처음 배우는데 추상 단계, hook method가 뭔가요, abstract step이 뭔가요, 추상 단계와 훅 메서드 차이, hook은 선택 빈칸, abstract step은 필수 빈칸, 뼈대 알고리즘 패턴, 상속 기반 흐름 고정, 공통 흐름 재사용, beginner template method, 템플릿 메소드 예시, inheritance vs composition template method, 상속으로 할까 조합으로 할까, 부모 클래스에 흐름 고정, 부모 클래스 vs 전략 객체, abstract class vs strategy, subclass skeleton, fixed workflow inheritance vs runtime composition, 처음 배우는데 템플릿 메소드, 템플릿 메소드 큰 그림, 템플릿 메소드 기초, 템플릿 메소드 언제 쓰는지, 부모가 흐름을 쥔다, 호출자가 전략을 고른다, 부모가 흐름을 쥔다 vs 호출자가 전략을 고른다, caller chooses strategy vs parent controls flow, parent owns workflow template method

---

## 핵심 개념

처음 배우는데는 두 문장으로 먼저 자르면 된다.

- 템플릿 메소드: **부모가 흐름을 쥔다**
- 전략: **호출자가 전략을 고른다**

템플릿 메소드 패턴은 **알고리즘의 전체 흐름(뼈대)을 부모 클래스에 정의**하고, 흐름 안의 특정 단계만 서브클래스가 구현하게 하는 패턴이다.

입문자가 헷갈리는 지점은 "왜 상속을 쓰냐"다. 공통 흐름이 명확하게 고정돼 있고, 변하는 것은 일부 단계뿐일 때 상속을 쓰면 코드 중복 없이 흐름을 공유할 수 있다. 반면 흐름 자체를 바꿔야 한다면 전략 패턴이 더 적합하다.

| 큰 그림 질문 | 템플릿 메소드 | 전략 |
|---|---|---|
| 누가 흐름/선택권을 쥐는가 | 부모 클래스가 공통 순서를 고정한다 | 호출자, 설정, DI가 전략 객체를 고른다 |
| 무엇을 바꾸는가 | 고정된 흐름 안의 일부 단계 | 교체 가능한 규칙/알고리즘 |
| 언제 쓰는지 | 순서를 흔들리면 안 되는 기초 파이프라인 | 요청마다 방법을 바꿔 끼워야 하는 문제 |

## 먼저 자를 질문

패턴 이름보다 "상속을 써도 되나?"가 먼저 떠오르면 이렇게 본다.

- 부모 클래스가 공통 순서를 끝까지 고정해야 한다. 즉 **부모가 흐름을 쥐어야 한다**: 템플릿 메소드
- 호출자, 설정, DI가 이번 구현을 골라 넣는 게 자연스럽다. 즉 **호출자가 전략을 고른다**: 전략 + 조합
- 아직 둘 다 흐리다: [상속보다 조합 기초](./composition-over-inheritance-basics.md) -> [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) 순서로 읽는다

## hook / abstract step을 처음 보면

처음 배우는데 `hook method`, `abstract step`이라는 말이 먼저 보이면 용어보다 빈칸의 성격을 먼저 본다.

| 처음 보는 용어 | 쉬운 뜻 | 서브클래스가 해야 하는 일 |
|---|---|---|
| abstract step | 없으면 흐름이 완성되지 않는 **필수 빈칸** | 반드시 구현한다 |
| hook method | 기본 흐름에 가끔 덧붙이는 **선택 빈칸** | 필요할 때만 오버라이드한다 |

즉 `convert()`처럼 없으면 보고서 내보내기가 끝나지 않는 단계는 abstract step이고, `afterExport()`처럼 기본은 아무 일도 안 해도 되는 후처리는 hook이다.
훅이 많아지는 냄새나 프레임워크별 예시는 나중에 보고, 첫 질문은 여기서 **부모가 흐름을 쥔다**는 큰 그림부터 잡는다.

## 한눈에 보기

부모 클래스 `AbstractReport`가 전체 흐름을 고정한다.

- `templateMethod()` — 흐름 전체를 담은 `final` 메서드
- `fetchData()` — 서브클래스가 구현하는 단계 (데이터 소스가 다름)
- `formatData()` — 서브클래스가 구현하는 단계 (포맷이 다름)
- `exportResult()` — 부모에 공통 로직으로 고정

`PdfReport`는 DB에서 조회 + PDF 변환, `CsvReport`는 파일 읽기 + CSV 변환을 구현한다. 흐름 순서는 두 서브클래스 모두 동일하다.

```
templateMethod() { fetchData(); formatData(); exportResult(); }
```

## 상세 분해

템플릿 메소드 패턴은 세 가지 요소로 이뤄진다.

- **템플릿 메소드** — 전체 흐름을 `final`로 정의한다. 서브클래스가 이 흐름을 바꾸지 못하게 막는다.
- **추상 메서드(abstract step)** — 서브클래스가 반드시 구현해야 하는 단계다. 부모는 선언만 한다.
- **훅 메서드(hook)** — 서브클래스가 원할 때만 오버라이드하는 선택적 단계다. 기본 구현이 있거나 빈 메서드로 둔다.

## 흔한 오해와 함정

- **"훅 메서드를 많이 만들수록 좋다"** — 훅이 늘어날수록 서브클래스가 어디를 오버라이드해야 하는지 파악하기 어려워진다. 꼭 필요한 경우만 추가한다.
- **"전략 패턴과 같다"** — 템플릿 메소드는 **부모가 흐름을 쥐는 상속 구조**고, 전략 패턴은 **호출자가 전략 객체를 고르는 조합 구조**다. 흐름이 고정인지 교체 가능한지가 핵심 차이다.
- **"추상 클래스는 항상 템플릿 메소드 패턴이다"** — 추상 클래스를 쓴다고 해서 모두 템플릿 메소드 패턴은 아니다. 흐름 고정 + 단계 위임 구조가 있어야 패턴이다.

## 실무에서 쓰는 모습

데이터 처리 파이프라인에서 "데이터 로드 → 변환 → 저장"이라는 흐름이 고정돼 있고 각 단계만 다를 때 쓴다. `AbstractDataProcessor`에 흐름을 고정하고, 각 구현체가 데이터 소스와 변환 로직을 채운다.

Spring의 `JdbcTemplate`, `RestTemplate`도 이 패턴을 활용한다. 커넥션 열기·닫기, 예외 처리 같은 공통 흐름은 내부에 고정하고, 실제 쿼리나 요청 부분만 사용자가 람다로 넘긴다.

## 더 깊이 가려면

- [템플릿 메소드 (Template Method) 심화](./template-method.md) — abstract step vs hook method 경계, 언제 쓰지 말아야 하는지
- [템플릿 메소드 vs 전략](./template-method-vs-strategy.md) — 상속 기반 vs 주입 기반 선택 기준
- [상속보다 조합 기초](./composition-over-inheritance-basics.md) — 템플릿 메소드가 허용되는 예외와, 조합을 기본으로 보는 큰 그림

## 면접/시니어 질문 미리보기

> Q: 템플릿 메소드 패턴에서 `final` 키워드가 중요한 이유는?
> 의도: 패턴의 핵심 제약을 이해하는지 확인한다.
> 핵심: 흐름(뼈대)을 서브클래스가 바꾸지 못하게 보호한다.

> Q: 템플릿 메소드와 전략 패턴 중 어느 것을 선택하는가?
> 의도: 두 패턴의 트레이드오프를 설명하는지 확인한다.
> 핵심: 흐름이 고정이면 템플릿 메소드, 흐름 자체를 runtime에 교체해야 하면 전략 패턴이다.

> Q: 훅 메서드와 추상 메서드의 차이는?
> 의도: 패턴 구성 요소를 아는지 확인한다.
> 핵심: 추상 메서드는 서브클래스가 반드시 구현해야 하고, 훅 메서드는 선택적으로 오버라이드한다.

## 한 줄 정리

템플릿 메소드 패턴은 알고리즘 흐름을 부모에 고정하고 변하는 단계만 서브클래스에 위임해, 코드 중복 없이 공통 흐름을 여러 구현체가 공유하게 한다.
