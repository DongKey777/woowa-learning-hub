# Java Memory Model, Happens-Before, `volatile`, `final`

> 한 줄 요약: `happens-before`는 "언제 보이는가"를 정하는 JMM의 핵심 규칙이고, `volatile`은 가시성/순서 보장, `final`은 생성 이후 안전한 게시(safe publication)의 기초가 된다.  

**난이도: 🟡 Intermediate**
> retrieval-anchor-keywords: happens-before, JMM, visibility, ordering, safe publication, volatile semantics, final field semantics, memory barrier, reordering, publication safety, data race, cache coherence

## 핵심 개념

자바 동시성에서 자주 헷갈리는 지점은 세 가지다.

- `값을 썼다`
- `다른 스레드가 그 값을 본다`
- `그 값이 어떤 순서로 보인다`

이 셋은 같지 않다.  
Java Memory Model(JMM)은 바로 이 차이를 정의한다.

### happens-before는 무엇인가

`happens-before`는 두 동작 사이의 **가시성 + 순서 보장 관계**다.  
앞선 동작이 뒤의 동작보다 먼저 발생하고, 뒤의 동작은 앞선 결과를 볼 수 있어야 한다는 의미다.

중요한 점은 "실제로 CPU가 먼저 실행했다"와 "다른 스레드가 그렇게 관찰한다"는 다르다는 것이다.  
JMM은 관찰 가능한 순서를 규정한다.

### `volatile`은 무엇을 보장하는가

`volatile`은 단순한 "최신값 읽기"가 아니다.  
쓰기와 읽기 사이에 happens-before 관계를 만들어서 다음을 돕는다.

- 다른 스레드가 최신 값을 볼 가능성을 높인다
- 읽기/쓰기 재정렬을 제한한다
- 상태 플래그, 종료 신호, one-writer-many-reader 패턴에 적합하다

하지만 `volatile`은 복합 연산을 원자적으로 만들지 않는다.  
즉 `count++`는 여전히 깨질 수 있다.

### `final`은 왜 중요한가

`final` 필드는 생성자에서 안전하게 세팅되면, 객체가 외부에 노출된 뒤에도 그 값이 더 안정적으로 보이도록 돕는다.  
즉 `final`은 "불변 객체를 만들 때 좋다" 수준이 아니라, **안전한 게시(safe publication)의 기반**이다.

다만 `final`은 깊은 불변성을 자동으로 보장하지 않는다.

- `final List<String> names`는 참조가 바뀌지 않는다는 뜻이지
- 리스트 내부 원소가 바뀌지 않는다는 뜻은 아니다

## 깊이 들어가기

### 1. 왜 재정렬이 문제인가

컴파일러와 CPU는 성능을 위해 명령을 재정렬할 수 있다.  
그래서 코드상으로는

1. 데이터를 쓰고
2. 준비 완료 플래그를 세운다

처럼 보이더라도, 다른 스레드에서는 플래그를 먼저 보고 데이터를 늦게 볼 수 있다.

이 차이가 바로 JMM을 공부해야 하는 이유다.  
`volatile`과 배리어는 이 재정렬을 제어하는 도구다.

### 2. safe publication이 왜 필요한가

객체를 생성한 뒤 다른 스레드가 그 객체를 볼 때, 생성 과정의 상태가 온전히 보장되지 않으면 문제가 생긴다.  
대표적인 경우는:

- 생성 중인 객체를 `this` escape 시키는 경우
- 초기화가 끝나기 전에 공유 컬렉션에 넣는 경우
- 락 없이 상태 플래그만 바꾸는 경우

`final` 필드는 이런 위험을 줄이는 데 큰 역할을 한다.  
특히 생성자 안에서 완전히 세팅된 `final` 필드는 안전한 게시의 기준을 만들기 쉽다.

### 3. `volatile`과 `synchronized`의 관계

둘 다 가시성에 관여하지만 성격이 다르다.

- `volatile`은 가벼운 신호 전달에 좋다
- `synchronized`는 상호배제와 가시성을 함께 제공한다

즉 `volatile`은 "상태 플래그"에 가깝고, `synchronized`는 "임계영역"에 가깝다.

### 4. JMM과 OS 캐시 계층은 어떻게 이어지는가

JMM은 언어 규칙이고, 실제 원인은 하드웨어 계층과 연결된다.

- CPU 캐시가 코어마다 다르게 보일 수 있다
- 캐시 coherence는 최신성의 문제다
- memory barrier는 순서의 문제다

이 관계를 이해하면, `volatile`이 단순 문법이 아니라 **캐시와 배리어를 통한 관찰 순서 제어**라는 점이 보인다.

관련해서 [CPU Cache, Coherence, Memory Barrier](../operating-system/cpu-cache-coherence-memory-barrier.md)와 [false sharing](../operating-system/false-sharing-cache-line.md)을 같이 보면 좋다.

### 5. 실전에서 자주 헷갈리는 경계

- `volatile`은 최신값을 볼 가능성을 높이지만, 원자적 증가를 보장하지 않는다
- `final`은 참조 고정과 초기화 가시성에 도움이 되지만, 객체 그래프 전체를 불변으로 바꾸지는 않는다
- `happens-before`는 "우연히 잘 되는 것"이 아니라, 관찰 가능한 순서를 설계하는 기준이다

## 실전 시나리오

### 시나리오 1: 종료 신호를 전달하고 싶다

백그라운드 스레드를 멈추는 가장 흔한 방법은 `volatile boolean stop`이다.

- 한 스레드가 `stop = true`를 쓴다
- 다른 스레드가 루프에서 그 값을 읽는다

이때 `volatile`이 없으면 루프가 종료 신호를 끝까지 못 볼 수 있다.  
그래서 단순 플래그에는 `volatile`이 자주 맞는다.

### 시나리오 2: 설정 객체를 여러 스레드에 안전하게 넘기고 싶다

설정 값이 생성 후 바뀌지 않는다면 `final` 필드로 묶는 게 좋다.

- 생성 시점에 값을 모두 세팅
- 생성이 끝난 뒤 외부로 노출

이런 패턴은 안전한 게시와 잘 맞는다.  
`final`은 "한 번 정해지면 바뀌지 않는다"는 의도를 코드에 드러내는 가장 좋은 수단 중 하나다.

### 시나리오 3: `count++`가 왜 틀리는지 설명해야 한다

`count++`는 읽기 -> 수정 -> 쓰기라서 원자적이지 않다.  
즉 `volatile`을 붙여도 lost update는 여전히 생길 수 있다.

이런 경우는 `AtomicInteger`, `synchronized`, `VarHandle` 중 하나를 선택해야 한다.  
관련 문서는 [VarHandle, Unsafe, Atomics](./java/varhandle-unsafe-atomics.md)를 참고하면 좋다.

### 시나리오 4: double-checked locking을 안전하게 쓰고 싶다

싱글턴 지연 초기화는 JMM 이해가 없으면 위험하다.  
객체 생성이 끝나기 전에 참조가 보이면 부분 초기화 상태가 노출될 수 있기 때문이다.

이때는 `volatile`과 올바른 초기화 패턴이 필요하다.  
동시성 검증은 [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)로 확인하는 게 가장 설득력 있다.

### 시나리오 5: 성능 문제를 동기화 탓으로만 보면 안 된다

느린 이유가 항상 락은 아니다.

- false sharing
- cache line bouncing
- 잘못된 publication
- 불필요한 volatile 읽기 과다

같은 원인도 많다.  
그래서 Java 코드만 보지 말고 OS 관점 문서도 함께 봐야 한다.

## 코드로 보기

### 1. `volatile`은 종료 신호에 적합하다

```java
public class Worker {
    private volatile boolean stop;

    public void requestStop() {
        stop = true;
    }

    public void run() {
        while (!stop) {
            doWork();
        }
    }

    private void doWork() {
        // 실제 작업
    }
}
```

이 코드는 "상태 플래그" 용도로는 좋다.  
하지만 `stop`이 아니라 `count`였다면 `volatile`만으로는 부족하다.

### 2. `final` 필드는 안전한 게시의 기초다

```java
public final class AppConfig {
    private final String baseUrl;
    private final int timeoutMillis;

    public AppConfig(String baseUrl, int timeoutMillis) {
        this.baseUrl = baseUrl;
        this.timeoutMillis = timeoutMillis;
    }

    public String baseUrl() {
        return baseUrl;
    }

    public int timeoutMillis() {
        return timeoutMillis;
    }
}
```

생성 시점에 끝내고, 이후에는 읽기만 하는 객체에 잘 맞는다.  
이런 객체는 여러 스레드에 넘겨도 해석이 단순하다.

### 3. `volatile`이 있어도 복합 연산은 깨진다

```java
public class Counter {
    private volatile int value;

    public void increment() {
        value++;
    }

    public int get() {
        return value;
    }
}
```

이 코드는 `value`를 최신으로 읽는 데는 도움이 되지만, `increment()`는 안전하지 않다.  
증가 연산은 읽기와 쓰기가 분리되므로 경합에서 값을 잃을 수 있다.

### 4. 이런 경우는 `AtomicInteger`나 `synchronized`를 쓴다

```java
import java.util.concurrent.atomic.AtomicInteger;

public class SafeCounter {
    private final AtomicInteger value = new AtomicInteger();

    public int increment() {
        return value.incrementAndGet();
    }
}
```

또는

```java
public class LockedCounter {
    private int value;

    public synchronized int increment() {
        return ++value;
    }
}
```

둘 중 무엇이 맞는지는 경합 수준과 복합 상태 여부에 따라 달라진다.

### 5. JCStress로 publication을 검증할 수 있다

```java
// 개념 예시:
// - writer가 데이터를 쓰고 ready를 true로 바꾼다
// - reader가 ready를 본 뒤 data를 읽는다
// - forbidden outcome이 나오지 않아야 한다
```

실전에서는 [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)처럼 가능한 결과를 열거해 검증한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `volatile` | 가볍고 직관적이다 | 원자성은 없다 | 종료 신호, 상태 플래그 |
| `final` | 안전한 게시와 가독성이 좋다 | 생성 후 변경 불가 | 불변 객체, 설정값 |
| `synchronized` | 가시성 + 상호배제를 함께 준다 | 경합이 크면 비용이 있다 | 복합 상태 변경 |
| `Atomic*` | 원자 연산을 쉽게 쓴다 | 복잡한 상태는 어렵다 | 단일 카운터, CAS |
| `VarHandle` | 저수준 제어가 가능하다 | 학습 비용이 높다 | 라이브러리, 런타임 |

판단 기준은 단순하다.

- 한 변수의 최신성만 필요하면 `volatile`
- 생성 후 바뀌지 않아야 하면 `final`
- 여러 상태를 함께 묶어 바꿔야 하면 `synchronized`
- 단일 값 경쟁만 풀면 `Atomic*`
- JMM/배리어까지 제어해야 하면 `VarHandle`

## 꼬리질문

> Q: `volatile`만 붙이면 `count++`가 안전해지나요?  
> 의도: 가시성과 원자성을 구분하는지 확인  
> 핵심: `volatile`은 최신값 보장이지, 복합 연산의 원자성을 보장하지 않는다.

> Q: `final` 필드는 왜 안전한 게시와 연결되나요?  
> 의도: 생성 시점의 초기화 가시성을 이해하는지 확인  
> 핵심: 생성자가 끝난 뒤 `final` 필드는 더 안정적으로 관찰되며, 객체 초기화의 가시성 문제를 줄인다.

> Q: happens-before는 그냥 "먼저 실행"과 같은 뜻인가요?  
> 의도: 실행 순서와 관찰 순서를 구분하는지 확인  
> 핵심: 실제 실행 순서가 아니라, 다른 스레드가 관찰해야 하는 순서를 규정한다.

> Q: `synchronized`와 `volatile` 중 무엇을 먼저 떠올려야 하나요?  
> 의도: 문제 유형별 도구 선택을 보는 질문  
> 핵심: 단순 플래그는 `volatile`, 복합 상태는 `synchronized`를 먼저 생각한다.

> Q: JMM 문제를 코드로 검증하려면 무엇을 써야 하나요?  
> 의도: 동시성 테스트 도구를 아는지 확인  
> 핵심: 일반 JUnit보다 [JCStress Concurrency Testing](./java/jcstress-concurrency-testing.md)이 훨씬 적합하다.

## 한 줄 정리

`happens-before`는 자바 동시성의 관찰 순서를 정의하고, `volatile`은 가시성과 순서를, `final`은 안전한 게시의 기반을 제공한다.
