# `volatile` `long`/`double` Atomicity and Memory Visibility

> 한 줄 요약: non-`volatile` `long`/`double`의 원자성은 역사적으로 구현 의존이었지만, 현재 JMM에서는 `volatile long`/`volatile double`의 읽기와 쓰기가 항상 atomic이고, 진짜 문제는 atomicity와 visibility를 섞어 생각하는 데 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)
> - [Java Concurrent Utility Notes](./5.md)

> retrieval-anchor-keywords: volatile long, volatile double, atomicity, torn read, torn write, 64-bit atomic, JMM, visibility, ordering, data race, word tearing, happens-before

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

`long`과 `double`은 64비트 값이다.  
역사적으로 일부 JVM/플랫폼에서는 non-`volatile` 64비트 값을 두 번에 나눠 읽고 쓸 수 있었다.

중요한 점은 두 가지다.

- atomicity는 "한 번에 읽히는가/써지는가"의 문제다
- visibility는 "다른 thread가 그 값을 볼 수 있는가"의 문제다

이 둘은 다르다.  
`volatile`은 둘 다와 관련 있지만, 같은 뜻은 아니다.

## 깊이 들어가기

### 1. 64비트 값의 역사적 배경

옛 JVM 규격에서는 non-`volatile` `long`/`double`이 32비트 단위로 쪼개져 보일 수 있었다.  
그래서 다른 thread가 value의 절반씩 다른 시점의 값을 보는 torn read가 가능했다.

현재 JLS에서는 `volatile long`과 `volatile double`의 읽기와 쓰기가 atomic이라고 명시한다.  
즉 shared 64-bit state를 다룰 때는 `volatile` 또는 다른 동기화 수단을 쓰는 것이 기본 안전선이다.

### 2. atomicity와 visibility를 혼동하면 생기는 버그

예를 들어 다음 두 문제는 다르다.

- 한 thread가 쓴 값을 다른 thread가 아직 못 본다
- 다른 thread가 값을 보긴 했지만 값이 반쯤 찢겨 있다

첫 번째는 visibility/ordering 문제이고, 두 번째는 atomicity 문제다.  
둘을 섞어서 "아마 volatile이면 되겠지"라고 생각하면 진단이 틀어진다.

### 3. 64비트 숫자를 volatile로 둘 때의 의미

`volatile long` 또는 `volatile double`은 다음을 도와준다.

- torn read/write 방지
- 최신 값 관찰 가능성 증가
- happens-before 연결

하지만 복합 연산은 여전히 원자적이지 않다.

```java
value++;
```

이런 연산은 여전히 read-modify-write라서 경쟁 조건이 생길 수 있다.

### 4. float/double은 비트 표현도 함께 봐야 한다

`double`은 부동소수점 값이라 비교와 누적이 수치 오차의 영향을 받는다.  
그래서 concurrency 버그를 볼 때는 atomicity만이 아니라 "같은 값처럼 보이는가"도 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 상태 플래그와 숫자 카운터를 같은 방식으로 다룬다

`volatile boolean`과 `volatile long`은 둘 다 visibility에 도움을 주지만, 숫자 카운터는 증감 연산이 추가된다.  
즉 플래그처럼 써서는 안 된다.

### 시나리오 2: 64비트 값을 읽는데 가끔 이상한 값이 나온다

이론적으로는 torn read를 의심할 수 있지만, 실무에서는 대부분 다른 이유가 많다.

- race condition
- 잘못된 publication
- 가시성 부족
- 잘못된 캐시

그래도 64비트 값은 애초에 `volatile`, `AtomicLong`, lock으로 다루는 편이 낫다.

### 시나리오 3: 숫자 값을 여러 thread가 갱신한다

이 경우 `volatile`만으로는 부족하다.  
증가 자체가 원자적이지 않기 때문이다.

## 코드로 보기

### 1. 안전한 64비트 상태 읽기

```java
public class Metrics {
    private volatile long requests;

    public void increment() {
        requests++;
    }

    public long getRequests() {
        return requests;
    }
}
```

읽기 가시성에는 도움이 되지만, `increment()`는 여전히 경쟁에서 깨질 수 있다.

### 2. 원자적 증가가 필요할 때

```java
import java.util.concurrent.atomic.AtomicLong;

public class SafeMetrics {
    private final AtomicLong requests = new AtomicLong();

    public long increment() {
        return requests.incrementAndGet();
    }
}
```

### 3. 64비트 값을 비트 단위로 볼 때

```java
long bits = Double.doubleToRawLongBits(123.45);
double value = Double.longBitsToDouble(bits);
```

비트 패턴이 중요할 때는 숫자 의미와 저장 의미를 분리해서 봐야 한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| plain `long`/`double` | 단순하다 | race와 visibility 문제가 생길 수 있다 |
| `volatile long`/`volatile double` | atomic read/write와 visibility를 돕는다 | 복합 연산은 해결 못 한다 |
| `AtomicLong` | 원자적 갱신이 가능하다 | 더 무겁고 복잡하다 |
| lock | 복합 상태를 함께 보호한다 | 경합이 생길 수 있다 |

핵심은 64비트 값을 "크니까 안전하겠지"가 아니라 "어떤 동기화 의미가 필요한가"로 보는 것이다.

## 꼬리질문

> Q: `volatile long`은 왜 특별한가요?
> 핵심: 64비트 값의 atomic read/write와 visibility를 함께 다루기 때문이다.

> Q: `volatile`이면 `value++`도 안전한가요?
> 핵심: 아니다. read-modify-write는 여전히 경쟁 조건이 있다.

> Q: torn read는 지금도 걱정해야 하나요?
> 핵심: 구현과 플랫폼에 의존하지만, 실무에서는 아예 atomic/volatile/lock으로 명확하게 막는 편이 낫다.

## 한 줄 정리

`volatile long`/`volatile double`은 64비트 값의 atomic read/write와 visibility를 돕지만, 증가 같은 복합 연산은 여전히 별도 원자화가 필요하다.
