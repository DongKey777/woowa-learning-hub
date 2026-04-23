# JCStress Concurrency Testing

> 한 줄 요약: JCStress는 "동시성 버그가 있는지"를 묻는 테스트가 아니라, **JMM과 실제 스케줄링 아래에서 가능한 결과를 열거**하는 테스트 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)

retrieval-anchor-keywords: JCStress, concurrency testing harness, JMM outcome testing, race condition test, publication safety test, acceptable interesting forbidden outcome, atomicity visibility ordering, lost update concurrency test, OpenJDK jcstress, stress test memory model

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [왜 일반 테스트로는 부족한가](#왜-일반-테스트로는-부족한가)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

JCStress는 OpenJDK의 stress-testing harness다.  
주 목적은 다음을 검증하는 것이다.

- 원자성이 깨지는가
- 가시성 문제가 있는가
- 순서 보장이 무너지는가
- 특정 구현이 JMM 하에서 허용되지 않는 결과를 내는가

일반 단위 테스트는 보통 "한 번 실행해서 통과했는가"만 본다.  
JCStress는 **수십만 번의 경쟁 실행에서 어떤 결과가 가능한지** 본다.

---

## 왜 일반 테스트로는 부족한가

동시성 버그는 재현이 어렵다.

- 실행 순서가 매번 다르다
- JIT 최적화가 결과를 바꿀 수 있다
- CPU 코어 수와 부하에 따라 관찰 결과가 달라진다
- 테스트가 지나치게 결정론적이면 문제가 숨어 버린다

즉, "한 번 통과"는 아무 의미가 없다.  
특히 `volatile`, `synchronized`, atomics, publication, reordering 같은 문제는 일반 JUnit으로는 놓치기 쉽다.

---

## 깊이 들어가기

### 1. JCStress가 보는 단위

JCStress 테스트는 보통 다음 구성으로 만든다.

- `@State`: 공유 객체 상태
- `@Actor`: 경쟁하는 실행 경로
- `@Arbiter`: 마지막 관찰
- `@Outcome`: 허용/금지 결과 정의

핵심은 "정답 하나"를 적는 게 아니라 **허용 가능한 결과 집합**을 선언하는 점이다.

### 2. 무엇을 증명하는가

JCStress는 구현이 다음을 만족하는지 확인하는 데 강하다.

- atomic increment가 진짜 원자적인가
- double-checked locking이 안전한가
- publication이 안전한가
- memory barrier가 기대대로 작동하는가

이건 기능 테스트라기보다 **메모리 모델 테스트**다.

### 3. 왜 JMM 문맥이 필요한가

JMM(Java Memory Model)을 모르면 결과 해석이 흔들린다.  
예를 들어 "한 스레드가 쓴 값이 다른 스레드에 왜 안 보이지?"는 버그일 수도 있고, **허용된 reordering 결과**일 수도 있다.

따라서 JCStress는 [JVM, GC, JMM](./jvm-gc-jmm-overview.md)와 같이 봐야 한다.

### 4. 관측 가능한 결과를 정의한다

테스트는 "이 결과만 나오면 성공"이 아니다.  
오히려 다음처럼 나눠 적는다.

- `ACCEPTABLE`
- `ACCEPTABLE_INTERESTING`
- `FORBIDDEN`

이렇게 하면 스케줄링 편차가 있어도 의미 있는 결과 해석이 가능하다.

---

## 실전 시나리오

### 시나리오 1: `volatile` 없이도 되는 줄 알았다

어떤 값이 한 번만 초기화되면 된다고 해서 `volatile`을 빼면, 다른 스레드가 부분적으로 초기화된 상태를 볼 수 있다.  
JCStress는 이런 publication 오류를 드러내기 좋다.

### 시나리오 2: `AtomicInteger`와 `int++` 차이를 증명하고 싶다

단순 증분은 읽기-수정-쓰기라 경쟁 상태가 생긴다.  
JCStress는 lost update를 반복 실행으로 잡아낸다.

### 시나리오 3: lock-free 코드가 정말 lock-free인지 확인하고 싶다

VarHandle이나 CAS 기반 코드는 한 번 성공한다고 끝이 아니다.  
경쟁이 강한 상황에서 금지된 결과가 나오는지 봐야 한다.

---

## 코드로 보기

### 1. 두 스레드가 같은 값을 만지는 가장 단순한 예

```java
import org.openjdk.jcstress.annotations.Actor;
import org.openjdk.jcstress.annotations.Arbiter;
import org.openjdk.jcstress.annotations.Expect;
import org.openjdk.jcstress.annotations.JCStressTest;
import org.openjdk.jcstress.annotations.Outcome;
import org.openjdk.jcstress.annotations.State;
import org.openjdk.jcstress.infra.results.I_Result;

@JCStressTest
@Outcome(id = "1", expect = Expect.ACCEPTABLE, desc = "One update observed")
@Outcome(id = "2", expect = Expect.ACCEPTABLE, desc = "Both updates observed")
@Outcome(expect = Expect.FORBIDDEN, desc = "Lost update or broken synchronization")
@State
public class CounterTest {
    int value;

    @Actor
    public void actor1() {
        value++;
    }

    @Actor
    public void actor2() {
        value++;
    }

    @Arbiter
    public void arbiter(I_Result r) {
        r.r1 = value;
    }
}
```

이 예시는 의도적으로 단순하다.  
실무에서는 결과의 허용 범위를 더 정교하게 나눠서 본다.

### 2. `volatile` publication 확인

```java
import org.openjdk.jcstress.annotations.*;
import org.openjdk.jcstress.infra.results.I_Result;

@JCStressTest
@Outcome(id = "1", expect = Expect.ACCEPTABLE, desc = "Published value is visible")
@Outcome(id = "0", expect = Expect.FORBIDDEN, desc = "Stale read")
@State
public class PublicationTest {
    volatile int ready;
    int data;

    @Actor
    public void writer() {
        data = 1;
        ready = 1;
    }

    @Actor
    public void reader(I_Result r) {
        if (ready == 1) {
            r.r1 = data;
        }
    }
}
```

이런 테스트는 "보이는 순서"가 왜 중요한지 보여준다.

### 3. 실행 예시

보통은 빌드 도구와 함께 돌린다.

```bash
./gradlew jcstress
```

또는 프로젝트에 맞는 task로 실행한다.  
결과는 통과/실패만 보는 게 아니라, 어떤 outcome이 얼마나 자주 나왔는지까지 본다.

---

## 트레이드오프

| 관점 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| JCStress | 경쟁 조건을 재현하기 좋다 | 작성/해석 비용이 높다 | JMM, atomics, lock-free 검증 |
| JUnit | 빠르고 익숙하다 | 스케줄링 버그를 놓치기 쉽다 | 일반 기능 검증 |
| 반복 stress test | 간단하다 | 결과 해석이 약하다 | 임시 확인 |

JCStress는 모든 테스트를 대체하지 않는다.  
하지만 동시성 API를 설계하거나 수정할 때는 가장 신뢰할 만한 도구 중 하나다.

---

## 꼬리질문

> Q: JCStress는 왜 결과를 여러 개 허용하나요?
> 의도: JMM의 허용 결과를 이해하는지 확인
> 핵심: 동시성 코드는 하나의 실행 결과만 존재하지 않을 수 있다.

> Q: JUnit으로는 왜 안 되나요?
> 의도: 스케줄링 비결정성을 이해하는지 확인
> 핵심: 일반 테스트는 race를 충분히 압박하지 못한다.

> Q: 무엇을 먼저 의심해야 하나요?
> 의도: 동시성 버그의 전형을 아는지 확인
> 핵심: 안전한 publication, atomicity, visibility, ordering 순으로 본다.

## 한 줄 정리

JCStress는 동시성 코드가 실제 경쟁 환경에서 어떤 결과를 낼 수 있는지 JMM 관점으로 검증하는 도구다.
