# Pipeline vs Chain of Responsibility

> 한 줄 요약: Pipeline은 단계별로 결과를 흘려보내는 데이터 처리 구조이고, Chain of Responsibility는 요청을 처리할 책임자에게 넘기며 중단 가능성을 가진다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [템플릿 메소드](./template-method.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Pipeline과 Chain of Responsibility는 비슷해 보이지만 의도가 다르다.

- Pipeline: 입력이 단계별 변환을 거쳐 최종 결과로 흐른다
- Chain of Responsibility: 요청이 각 처리자를 거치며 책임 여부에 따라 중단된다

backend에서는 데이터 정제와 요청 통제에서 차이가 중요하다.

### Retrieval Anchors

- `pipeline pattern`
- `chain of responsibility`
- `stage processing`
- `request short circuit`
- `transform stream`

---

## 깊이 들어가기

### 1. Pipeline은 데이터 변환에 가깝다

Pipeline은 전 단계 결과가 다음 단계 입력이 된다.

- 입력 검증
- 정규화
- 변환
- 저장

데이터 엔지니어링이나 batch processing에 잘 맞는다.

### 2. Chain은 책임 위임에 가깝다

Chain은 다음 단계로 넘길지, 중단할지 판단한다.

- 인증 실패 시 중단
- rate limit 초과 시 중단
- 조건 통과 시 다음으로 전달

### 3. 한 메서드에 둘을 섞으면 추적이 어려워진다

변환과 차단을 섞으면 무엇이 pipeline이고 무엇이 chain인지 흐려진다.

---

## 실전 시나리오

### 시나리오 1: 주문 데이터 정제

CSV나 외부 API 응답을 정제하는 건 Pipeline이 더 자연스럽다.

### 시나리오 2: 보안 필터

인증/인가/차단은 Chain이 더 맞다.

### 시나리오 3: 배치 후처리

여러 변환 단계를 순차 적용하는 곳은 Pipeline이 깔끔하다.

---

## 코드로 보기

### Pipeline

```java
public interface Stage<I, O> {
    O process(I input);
}

public class NormalizeStage implements Stage<String, String> {
    @Override
    public String process(String input) {
        return input.trim().toLowerCase();
    }
}
```

### Chain

```java
public interface Handler {
    boolean handle(RequestContext context);
}

public class AuthHandler implements Handler {
    @Override
    public boolean handle(RequestContext context) {
        return context.hasValidToken();
    }
}
```

### 차이

```java
// Pipeline: output of one stage becomes input of next stage
// Chain: handler may stop propagation
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Pipeline | 데이터 변환이 명확하다 | 중단 조건 표현은 약하다 | 정제/변환 |
| Chain | 차단과 위임이 쉽다 | 결과 흐름이 숨겨질 수 있다 | 인증/인가 |
| Template Method | 순서 보장이 쉽다 | 유연성은 낮다 | 고정 절차 |

판단 기준은 다음과 같다.

- 입력을 단계적으로 바꾸면 Pipeline
- 요청을 넘기다 끊을 수 있으면 Chain
- 순서를 프레임워크가 고정하면 Template Method

---

## 꼬리질문

> Q: Pipeline과 Chain을 같은 것으로 보면 왜 안 되나요?
> 의도: 변환과 책임 위임의 차이를 아는지 확인한다.
> 핵심: Pipeline은 결과 흐름, Chain은 책임 중단이 핵심이다.

> Q: Filter chain은 Pipeline인가요, Chain인가요?
> 의도: 실제 프레임워크 구조를 분류할 수 있는지 확인한다.
> 핵심: 둘의 성격이 섞이지만, 책임 연쇄가 더 가깝다.

> Q: 배치 처리에 왜 Pipeline이 잘 맞나요?
> 의도: 단계형 변환에 대한 감각을 보는지 확인한다.
> 핵심: 각 단계의 출력이 다음 단계 입력이 되기 때문이다.

## 한 줄 정리

Pipeline은 데이터를 단계적으로 변환하고, Chain of Responsibility는 요청을 넘기며 책임을 중단할 수 있다.

