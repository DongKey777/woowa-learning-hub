# JVM, GC, JMM

> 한 줄 요약: JVM은 바이트코드를 실행하는 런타임이고, GC는 힙 생명주기를 관리하며, JMM은 멀티스레드에서 값이 언제 어떻게 보이는지를 정의한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Language README](../README.md)
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [Safepoint Polling Mechanics](./safepoint-polling-mechanics.md)
> - [TLAB and PLAB Allocation Intuition](./tlab-plab-allocation-intuition.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [`volatile` `long`/`double` Atomicity and Memory Visibility](./volatile-long-double-atomicity-memory-visibility.md)
> - [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Compressed Oops and Class Pointers](./compressed-oops-class-pointers.md)
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [ClassLoader, Exception 경계, 객체 계약](./classloader-exception-boundaries-object-contracts.md)

> retrieval-anchor-keywords: JVM, GC, JMM, heap, stack, metaspace, safepoint, stop-the-world, TLAB, PLAB, visibility, ordering, happens-before, allocation pressure, card table, compressed oops, pause time

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [JVM이란](#jvm이란)
- [JVM 메모리 구조](#jvm-메모리-구조)
- [GC가 실제로 하는 일](#gc가-실제로-하는-일)
- [JMM이 왜 필요한가](#jmm이-왜-필요한가)
- [volatile과 synchronized](#volatile과-synchronized)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 중요한가

자바 백엔드는 결국 JVM 위에서 동작한다.  
그래서 단순히 "코드를 잘 짠다"를 넘어서 다음을 설명할 수 있어야 한다.

- 객체가 어디에 만들어지는가
- 그 객체가 언제 회수되는가
- 스레드 A의 변경이 스레드 B에 언제 보이는가
- GC pause와 safepoint가 왜 생기는가
- 작은 객체를 많이 만들 때 실제 비용은 어디서 나는가

이 문서를 이해하면 GC 튜닝, 동시성 버그, startup 지연, latency spike를 같은 프레임으로 읽을 수 있다.

## JVM이란

JVM(Java Virtual Machine)은 Java 바이트코드를 실행하는 런타임이다.  
소스 코드와 CPU 사이에 있는 실행 레이어라고 보면 된다.

흐름은 보통 다음과 같다.

1. `.java` 파일 작성
2. `javac`로 `.class` 바이트코드 생성
3. JVM이 바이트코드를 로딩하고 검증하고 실행
4. JIT가 hot path를 최적화

### 런타임 관점에서 보는 JVM

JVM은 단순 해석기가 아니다.

- class loading
- bytecode verification
- JIT compilation
- GC
- thread scheduling interaction
- safepoint coordination

이 모두가 런타임 동작이다.  
즉 "자바 실행"은 CPU만의 문제가 아니라 JVM 전체의 협업 문제다.

## JVM 메모리 구조

### Heap

- 객체가 주로 저장되는 공간
- GC의 중심 관리 대상
- TLAB/PLAB 같은 빠른 allocation 경로가 연결된다

### Stack

- thread마다 독립적이다
- method call frame, local variable, operand stack을 담는다
- 너무 깊으면 stack overflow가 난다

### Metaspace

- class metadata, method metadata, constant pool 관련 구조가 있다
- class loading과 unloading에 영향을 받는다

### Code Cache

- JIT가 만든 machine code가 들어간다
- warmup, deoptimization, inlining과 연결된다

### Native / Off-heap

- direct buffer, JNI, mmap, thread stack, JVM 내부 native 영역이 있다
- heap만 봐서는 안 될 때가 많다

### 참고: compressed oops

64-bit JVM에서는 reference 표현을 줄이는 최적화가 쓰일 수 있다.  
관련해서 [Compressed Oops and Class Pointers](./compressed-oops-class-pointers.md)와 [Object Layout and JOL Intuition](./object-layout-jol-intuition.md)을 같이 보면 heap footprint 감각이 더 빨리 잡힌다.

## GC가 실제로 하는 일

GC는 "안 쓰는 객체를 없앤다"로 끝나지 않는다.  
실제로는 다음을 함께 다룬다.

- root 탐색
- reachable object marking
- object copying / compaction
- survivor / promotion
- card table / remembered set update
- safepoint coordination

### 왜 필요하나

개발자가 직접 `free()`를 호출하지 않기 때문에 JVM이 생명주기를 관리한다.  
하지만 GC는 공짜가 아니다.

- allocation rate가 너무 높으면 자주 돈다
- 살아 있는 객체가 많으면 pause가 길어진다
- object graph가 복잡하면 tracing 비용이 커진다

### allocation은 어떻게 빠른가

많은 객체는 TLAB에서 bump-pointer 방식으로 빠르게 할당된다.  
할당 자체는 빠르지만, TLAB refill이나 이후 GC 비용은 별도다.

그래서 [TLAB and PLAB Allocation Intuition](./tlab-plab-allocation-intuition.md)을 같이 보면 "할당이 빠르다"는 말을 더 정확히 이해할 수 있다.

### pause는 왜 생기나

GC는 safepoint와 연결된다.  
즉 멈춤은 GC만의 문제가 아니라 JVM이 안전한 지점으로 모이는 과정에서 생긴다.

관련해서 [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)와 [Safepoint Polling Mechanics](./safepoint-polling-mechanics.md)를 함께 보면 좋다.

## JMM이 왜 필요한가

JMM(Java Memory Model)은 멀티스레드에서 **무엇이 언제 보이는가**를 정의한다.

핵심 질문은 이거다.

- 스레드 A가 값을 바꿨는데 스레드 B는 언제 볼 수 있는가
- CPU 캐시와 compiler reordering 때문에 어떤 일이 벌어질 수 있는가
- 원자성, 가시성, 순서를 어떻게 구분해야 하는가

### JMM이 다루는 세 가지

- atomicity: 값이 찢어지지 않고 읽히는가
- visibility: 다른 thread가 최신 값을 볼 수 있는가
- ordering: 실행 순서가 바뀌지 않는가

### 왜 실무에서 중요한가

동시성 버그는 종종 코드가 틀려서가 아니라 **관찰 규칙을 잘못 가정해서** 생긴다.

예:

- 종료 플래그는 보이는데 데이터는 안 보인다
- count++는 괜찮아 보이지만 lost update가 난다
- 싱글턴 초기화가 반쯤 된 상태로 보인다

이런 문제는 [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md), [`volatile` `long`/`double` Atomicity and Memory Visibility](./volatile-long-double-atomicity-memory-visibility.md), [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)에서 이어진다.

## volatile과 synchronized

### `volatile`

- 최신 값을 보려는 신호 플래그에 적합하다
- read/write에 ordering과 visibility 의미를 준다
- 복합 연산을 원자적으로 만들지는 않는다

### `synchronized`

- 상호배제와 가시성을 함께 제공한다
- 임계영역을 명확히 만든다
- 경쟁이 커지면 병목이 될 수 있다

### 둘의 차이

`volatile`은 "상태 전달"에 가깝고, `synchronized`는 "상태 보호"에 가깝다.  
실제 문제는 두 개를 섞어 쓰면서 경계를 모호하게 만드는 것이다.

## 실전 시나리오

### 시나리오 1: 객체는 많은데 메모리는 빨리 안 찬다

이건 TLAB fast path나 EA/Scalar replacement 때문일 수 있다.  
관련해서 [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)와 [Object Pooling Myths in the Modern JVM](./object-pooling-myths-modern-jvm.md)를 같이 보면 좋다.

### 시나리오 2: p99 latency가 튄다

GC pause, safepoint, lock contention, thread parking, native call을 같이 봐야 한다.  
JFR로 먼저 증상을 읽고, thread dump로 상태를 좁히는 게 좋다.

### 시나리오 3: 멀티스레드 값이 이상하다

순서 문제인지, visibility 문제인지, atomicity 문제인지 분리해야 한다.  
이 차이를 안 나누면 `volatile`만 붙이고 끝내는 잘못을 하기 쉽다.

### 시나리오 4: startup 직후만 느리다

class loading, JIT warmup, CDS/AppCDS, code cache 압박을 같이 봐야 한다.  
관련해서 [Class Data Sharing and AppCDS](./class-data-sharing-appcds.md)와 [CDS Startup Profiling](./cds-startup-profiling.md)을 참고하면 된다.

## 코드로 보기

### 1. `volatile` 종료 플래그

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
        // work
    }
}
```

### 2. `volatile`만으로는 부족한 카운터

```java
public class Counter {
    private volatile int value;

    public void increment() {
        value++;
    }
}
```

이 코드는 visibility는 일부 도움을 주지만 atomicity는 보장하지 않는다.

### 3. `synchronized`로 상태 보호

```java
public class SafeCounter {
    private int value;

    public synchronized int increment() {
        return ++value;
    }
}
```

### 4. JFR과 함께 보는 관측

```bash
jcmd <pid> JFR.start name=app settings=profile duration=60s filename=/tmp/app.jfr
```

```bash
jcmd <pid> Thread.print -l
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| GC에 맡김 | 개발이 단순해진다 | pause와 allocation pressure를 관리해야 한다 |
| `volatile` | 상태 전달이 쉽다 | 복합 상태는 못 지킨다 |
| `synchronized` | 상태 보호가 명확하다 | contention이 커질 수 있다 |
| lock-free / VarHandle | 세밀한 제어가 가능하다 | 이해와 검증이 어렵다 |

핵심은 JVM, GC, JMM을 따로 외우는 것이 아니라 하나의 실행 시스템으로 같이 읽는 것이다.

## 꼬리질문

> Q: JVM과 JDK, JRE 차이는 무엇인가요?
> 핵심: JVM은 실행 엔진, JRE는 실행 환경, JDK는 개발 도구까지 포함한 배포판이다.

> Q: GC는 왜 필요한가요?
> 핵심: 개발자가 직접 해제하지 않는 객체 생명주기를 자동으로 관리하기 위해서다.

> Q: `volatile`과 `synchronized`는 어떻게 다르나요?
> 핵심: `volatile`은 visibility와 ordering 중심이고, `synchronized`는 상호배제와 visibility를 함께 제공한다.

> Q: JMM이 왜 중요한가요?
> 핵심: 스레드 간 값의 관찰 순서와 최신성에 대한 규칙이기 때문이다.

## 한 줄 정리

JVM은 실행, GC는 생명주기, JMM은 스레드 간 관찰 규칙을 담당하며, 실무에서는 이 셋을 같이 봐야 성능과 동시성 버그를 제대로 읽을 수 있다.
