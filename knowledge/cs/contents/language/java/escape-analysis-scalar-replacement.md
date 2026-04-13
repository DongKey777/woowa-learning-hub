# Escape Analysis and Scalar Replacement

> 한 줄 요약: escape analysis는 객체가 method/thread 밖으로 새는지 판단하고, no-escape로 판정되면 HotSpot은 allocation과 일부 lock을 없애거나 scalar replacement로 바꿀 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: escape analysis, scalar replacement, object allocation elimination, lock elision, NoEscape, ArgEscape, GlobalEscape, HotSpot, JIT, allocation pressure, GC pressure, defensive copy

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

Escape analysis(EA)는 새로 만든 객체가 어디까지 도달하는지 분석한다.  
핵심 질문은 두 가지다.

- 객체가 method 밖으로 나가는가
- 객체가 현재 thread 밖으로 나가는가

HotSpot은 이 결과를 바탕으로 다음 최적화를 할 수 있다.

- allocation 제거
- lock 제거
- scalar replacement

중요한 점은 "no escape = 무조건 stack allocation"이 아니라는 것이다.  
Oracle 문서도 HotSpot이 heap allocation을 stack allocation으로 항상 바꾸는 것은 아니라고 설명한다.

## 깊이 들어가기

### 1. escape state를 어떻게 이해할까

실무에서 볼 만한 상태는 이렇다.

- GlobalEscape: static field, 반환값, 공유 객체를 통해 밖으로 퍼진다
- ArgEscape: 호출 인자로 전달되지만 그 호출 안에서만 쓰인다
- NoEscape: method/thread를 벗어나지 않는다

이 구분이 중요한 이유는 EA가 보수적으로 동작하기 때문이다.  
한 경로라도 밖으로 새면 그 객체는 더 이상 "안전하게 지워도 되는 대상"이 아니라고 본다.

### 2. scalar replacement는 무엇을 바꾸나

scalar replacement는 객체를 통째로 다루지 않고 필드를 독립적인 local value처럼 다루는 최적화다.  
예를 들어 `Point(x, y)`가 사실상 `x`와 `y`만 필요하면, JIT는 객체 자체를 만들지 않을 수 있다.

즉, 코드에서는 객체를 만들었지만 실행 시점에는 그 객체가 사라질 수 있다.

### 3. 어떤 코드가 EA를 막나

EA가 잘 안 먹는 흔한 패턴:

- 객체를 반환한다
- static field에 넣는다
- 다른 thread로 넘긴다
- 복잡한 control flow에서 한 경로라도 escape한다
- reflection/JVMTI 같은 관찰 경로가 강하다
- 예외와 재할당이 섞여 분석이 복잡해진다

### 4. 왜 microbenchmark가 헷갈리나

EA는 warmup 이후에 더 잘 드러난다.  
그래서 allocation 카운트나 GC 횟수만 보고 "이 코드는 항상 무할당이다"라고 말하면 위험하다.

또한 JIT 버전, 분기 구조, 호출 형태가 조금만 바뀌어도 결과가 달라질 수 있다.

## 실전 시나리오

### 시나리오 1: 작은 객체를 많이 만드는 코드가 생각보다 빠르다

이는 allocation이 실제로 남아도 비용이 매우 작거나, EA가 일부를 제거했기 때문일 수 있다.  
즉 "객체 생성 = 무조건 느림"은 아니다.

### 시나리오 2: `StringBuilder`나 DTO가 많아 보이는데 GC가 적다

HotSpot이 중간 객체를 제거했을 가능성이 있다.  
특히 계산용 임시 객체, copy-on-write 스타일의 중간값, defensive copy 일부에서 흔하다.

### 시나리오 3: synchronized 블록이 생각보다 싸다

그 락 객체가 method 밖으로 새지 않으면 lock elision이 가능하다.  
그래서 "락이 들어갔으니 무조건 비용이 있다"는 직관도 항상 맞지 않는다.

## 코드로 보기

### 1. 임시 객체가 사라질 수 있는 예

```java
public final class PointCalc {
    public int sum(int x, int y) {
        Point p = new Point(x, y);
        return p.x() + p.y();
    }

    record Point(int x, int y) {}
}
```

코드상으로는 `Point` 객체를 만들지만, JIT는 필드를 쪼개서 다룰 수 있다.

### 2. EA가 잘 깨지는 예

```java
public class EscapingBox {
    private Object value;

    public Object publish(Object input) {
        this.value = input;
        return input;
    }
}
```

여기서는 객체가 외부로 새기 쉬워서 최적화 여지가 줄어든다.

### 3. defensive copy도 최적화될 수 있다

```java
public final class NameHolder {
    private final String first;
    private final String last;

    public NameHolder(String first, String last) {
        this.first = first;
        this.last = last;
    }

    public String fullName() {
        return new StringBuilder()
            .append(first)
            .append(' ')
            .append(last)
            .toString();
    }
}
```

이런 코드는 JIT가 중간 `StringBuilder`를 더 공격적으로 최적화할 수 있다.

### 4. 관측 커맨드

```bash
java \
  -XX:+UnlockDiagnosticVMOptions \
  -XX:+PrintCompilation \
  -XX:+PrintInlining \
  -jar app.jar
```

```bash
jcmd <pid> JFR.start name=alloc settings=profile duration=60s filename=/tmp/alloc.jfr
```

JFR에서 allocation burst와 hot method를 같이 보면 EA 효과를 간접적으로 읽기 좋다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 임시 객체를 분리해서 쓰기 | 코드가 읽기 쉽다 | JIT 최적화에 의존할 수 있다 |
| 객체 재사용 | allocation을 줄인다 | 상태 오염과 동시성 문제가 생길 수 있다 |
| 명시적 primitive 계산 | 빠를 수 있다 | 도메인 표현력이 떨어질 수 있다 |
| EA에 맡기기 | 코드는 자연스럽다 | JIT 버전과 패턴에 따라 결과가 달라진다 |

핵심은 "할당을 없애려고 코드를 먼저 망치지 말고, 먼저 읽기 쉬운 코드를 쓰고 JIT가 지우도록 허용하는 것"이다.

## 꼬리질문

> Q: escape analysis는 stack allocation과 같은 말인가요?
> 핵심: 아니다. EA는 escape 여부를 판단하는 분석이고, HotSpot은 그 결과로 allocation 제거와 scalar replacement를 할 수 있지만 항상 stack allocation을 하는 것은 아니다.

> Q: scalar replacement가 왜 성능에 도움이 되나요?
> 핵심: 객체 전체를 만들지 않고 필드값만 다루면 allocation, GC pressure, 일부 lock 비용이 줄어든다.

> Q: 왜 `final`이나 불변 설계가 EA에도 도움되나요?
> 핵심: 상태가 단순하면 escape 경로와 alias가 줄어들어 JIT가 추론하기 쉬워진다.

## 한 줄 정리

escape analysis는 객체가 밖으로 새는지 판단해 HotSpot이 allocation과 lock을 줄일 기회를 주고, scalar replacement는 그 결과를 실제 코드에서 드러내는 대표적인 최적화다.
