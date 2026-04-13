# JFR Event Interpretation

> 한 줄 요약: JFR은 단순히 켜는 도구가 아니라 event category, stack trace, duration, thread state, allocation context를 함께 읽어야 진짜 병목을 좁힐 수 있는 관측 시스템이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)

> retrieval-anchor-keywords: JFR, event interpretation, event type, duration, stack trace, allocation context, thread state, lock profile, gc pause, socket read, safepoint, JMC

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

JFR은 JVM 내부 이벤트를 기록한다.  
하지만 파일을 얻는 것만으로는 부족하고, 어떤 event가 무슨 의미인지 해석해야 한다.

보통 같이 읽어야 하는 축:

- duration
- timestamp
- thread
- stack trace
- allocation context
- event category

## 깊이 들어가기

### 1. duration만 보면 안 된다

길게 걸린 이벤트가 항상 문제의 원인은 아니다.  
중요한 것은 어떤 thread에서 어떤 context로 반복되었는지다.

### 2. stack trace는 원인 후보를 좁힌다

JFR은 핫스팟의 호출 경로를 보여준다.  
같은 이벤트라도 어떤 stack에서 나왔는지에 따라 해석이 달라진다.

### 3. allocation 이벤트는 맥락이 필요하다

allocation이 많다고 항상 나쁜 것은 아니다.  
하지만 burst 형태인지, 특정 path에서 몰리는지 봐야 한다.

### 4. thread state는 병목을 분리한다

`RUNNABLE`, `BLOCKED`, `PARKED`, `NATIVE` 같은 상태는 원인 후보를 바로 줄여 준다.  
JFR은 이걸 시간축으로 연결해 준다.

### 5. JFR event는 증상 레이어다

JFR은 "무슨 일이 있었는가"를 보여주고, 코드 수정은 그 다음이다.  
즉 증상과 원인을 섞지 않는 것이 중요하다.

## 실전 시나리오

### 시나리오 1: GC pause가 길다

JFR에서 GC event의 duration, heap pressure, allocation rate를 같이 본다.  
그 뒤 safepoint 구간과 맞물리는지 확인한다.

### 시나리오 2: lock contention이 있다

blocked thread, monitor owner, contention duration을 함께 본다.  
락 자체보다 임계영역의 길이와 공유 범위가 중요할 수 있다.

### 시나리오 3: native call이 느리다

JFR에서 native frame이나 socket I/O, JNI 경로를 보면 JVM 바깥에서 지연이 생기는지 감을 잡을 수 있다.

## 코드로 보기

### 1. JFR 파일을 여는 기본 감각

```bash
jfr summary /tmp/app.jfr
jfr print /tmp/app.jfr
```

### 2. 특정 event를 좁혀 본다

```bash
jfr print --events jdk.GarbageCollection,jdk.SafepointBegin,jdk.SafepointEnd /tmp/app.jfr
```

### 3. 코드로 event를 남기는 감각

```java
import jdk.jfr.Event;

public class MyEvent extends Event {}
```

### 4. JMC와 함께 읽는다

```java
// JFR은 raw fact를 주고,
// JMC는 그 fact를 읽기 좋게 보여준다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| JFR summary | 빠르게 전체 그림을 본다 | 세부 원인 파악은 약하다 |
| event filtering | 신호를 좁힐 수 있다 | 해석 기준이 필요하다 |
| stack trace 포함 | 원인 후보가 선명해진다 | overhead와 파일 크기가 늘 수 있다 |
| JMC 분석 | 읽기 쉽다 | 도구 사용 경험이 필요하다 |

핵심은 JFR 이벤트를 "로그"가 아니라 "JVM 증상의 구조화된 기록"으로 읽는 것이다.

## 꼬리질문

> Q: JFR에서 가장 먼저 볼 것은 무엇인가요?
> 핵심: duration, thread state, stack trace, event category를 먼저 본다.

> Q: allocation이 많으면 무조건 나쁜가요?
> 핵심: 아니다. burst, 반복 경로, GC pressure와 함께 봐야 한다.

> Q: JFR이 JMC 없이도 유용한가요?
> 핵심: 유용하다. 다만 JMC가 있으면 해석 속도가 더 빨라진다.

## 한 줄 정리

JFR event는 JVM 증상을 구조화해서 보여주므로, duration과 stack trace만 보지 말고 thread state와 allocation 맥락까지 함께 읽어야 한다.
