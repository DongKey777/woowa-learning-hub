# Template Hook Smells: 템플릿 메소드가 과해졌다는 신호

> 한 줄 요약: Template Hook는 흐름 고정에 유용하지만, 훅이 많아지면 상속 구조보다 조건 분기와 전략 조합이 더 낫다는 신호일 수 있다.

**난이도: 🟠 Advanced**

> 관련 문서:
> - [템플릿 메소드](./template-method.md)
> - [템플릿 메소드 vs 전략](./template-method-vs-strategy.md)
> - [전략 패턴](./strategy-pattern.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Template Method는 알고리즘의 골격을 상위 클래스가 고정하고, 일부 단계를 hook으로 열어두는 패턴이다.  
문제는 hook이 계속 늘어나는 순간이다.

- `beforeX`, `afterX`
- `validate`, `doExecute`, `cleanup`
- `onStart`, `onFinish`, `onError`

hook이 많아지면 상속 계층이 아니라 **분기와 우회로**가 된다.

### Retrieval Anchors

- `template hook smell`
- `hook method explosion`
- `inheritance rigidity`
- `algorithm skeleton`
- `subclass override risk`

---

## 깊이 들어가기

### 1. hook은 유연성처럼 보이지만 결합을 만든다

hook은 "조금만 바꿀 수 있다"는 장점이 있다.
하지만 실제로는 서브클래스가 상위 클래스의 내부 순서에 의존하게 된다.

이 구조는 다음 위험을 만든다.

- 순서 변경이 어렵다
- 일부 hook만 override되면 의도가 흐려진다
- 상위 클래스 수정이 하위 클래스 전체에 파급된다

### 2. 훅이 많으면 패턴이 아니라 정책이 된다

hook이 많다는 건 결국 여러 변화 지점이 있다는 뜻이다.

- 전처리
- 검증
- 후처리
- 에러 복구

이때는 template method를 유지하기보다 전략, 상태, 책임 연쇄로 분해하는 편이 더 자연스럽다.

### 3. backend에서 흔한 냄새

- 배치 프레임워크의 abstract job class가 너무 커진다
- 인증/인가/검증/로깅 hook이 한 클래스에 몰린다
- 서브클래스가 템플릿 내부 순서를 가정한다

---

## 실전 시나리오

### 시나리오 1: 배치 작업

입력 읽기, 정제, 저장, 알림 발송 같은 단계는 템플릿 메소드와 잘 맞는다.  
하지만 훅이 복잡해지면 각 단계가 별도 전략이나 체인으로 나뉘어야 한다.

### 시나리오 2: 외부 연동 작업

공통 흐름은 같지만 인증, 변환, 전송, 재시도가 모두 다르면 hook이 폭발하기 쉽다.

### 시나리오 3: 도메인 룰 처리

비즈니스 규칙이 자꾸 달라진다면 상속보다 정책 객체가 더 안전하다.

---

## 코드로 보기

### Template Method

```java
public abstract class AbstractJob {
    public final void run() {
        before();
        execute();
        after();
    }

    protected void before() {}
    protected abstract void execute();
    protected void after() {}
}
```

### Hook가 많아지는 냄새

```java
public abstract class AbstractJob {
    public final void run() {
        beforeValidate();
        beforeExecute();
        execute();
        afterExecute();
        afterCleanup();
    }

    protected void beforeValidate() {}
    protected void beforeExecute() {}
    protected abstract void execute();
    protected void afterExecute() {}
    protected void afterCleanup() {}
}
```

이쯤 되면 상위 클래스가 흐름을 고정하는 이점보다, 하위 클래스가 알아야 할 내부 규칙이 더 많아진다.

### 대안

```java
public class JobPipeline {
    private final List<JobStep> steps;

    public void run() {
        for (JobStep step : steps) {
            step.execute();
        }
    }
}
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Template Method | 흐름을 강하게 보장한다 | 훅이 많아지면 단단해진다 | 순서가 거의 고정일 때 |
| Strategy | 교체가 쉽다 | 클래스가 늘어날 수 있다 | 단계별 동작이 바뀔 때 |
| Chain/Pipeline | 단계 분리가 명확하다 | 순서 추적이 필요하다 | 전/후처리 조합이 많을 때 |

판단 기준은 다음과 같다.

- 훅이 2~3개면 템플릿이 자연스럽다
- 훅이 계속 늘어나면 냄새다
- 서브클래스가 상위 내부를 알아야 하면 구조를 다시 본다

---

## 꼬리질문

> Q: Template Method와 전략 패턴을 함께 써도 되나요?
> 의도: 패턴 조합을 이론적으로만 보지 않는지 확인한다.
> 핵심: 가능하지만, 먼저 훅이 정말 필요한지 봐야 한다.

> Q: hook이 많아지면 왜 문제가 되나요?
> 의도: 상속 기반 유연성이 오히려 약점이 되는 이유를 아는지 확인한다.
> 핵심: 내부 순서 의존성이 커지고 하위 클래스가 불안정해진다.

> Q: 템플릿 메소드가 과해졌다는 신호는 무엇인가요?
> 의도: 냄새를 조기에 감지할 수 있는지 확인한다.
> 핵심: before/after hook이 계속 늘어나면 분해를 고려해야 한다.

## 한 줄 정리

Template Hook가 많아지면 상속으로 흐름을 고정하는 장점보다, 구조가 단단해지는 비용이 더 커질 수 있다.

