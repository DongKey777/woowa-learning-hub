# Async-profiler vs JFR

> 한 줄 요약: async-profiler는 CPU/alloc/native stack에 강하고, JFR은 JVM 이벤트와 시간축 관측에 강해서 둘은 경쟁 도구라기보다 병행해서 쓰는 도구에 가깝다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)

> retrieval-anchor-keywords: async-profiler, JFR, sampling profiler, native frames, CPU profiling, allocation profiling, flamegraph, JVM events, lock profiling, wall-clock, safepoint, comparison

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로 보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

async-profiler와 JFR은 모두 JVM 성능 분석에 쓰이지만 초점이 다르다.

- async-profiler: sampling 기반의 CPU/alloc/native stack 분석에 강함
- JFR: JVM 이벤트, lock, GC, allocation, thread state, safepoint를 시간축으로 읽기에 강함

둘은 대체재라기보다 보완재다.

## 깊이 들어가기

### 1. async-profiler의 강점

async-profiler는 샘플링 기반으로 CPU와 allocation hotspot을 보기 좋다.  
native frame과 kernel/GC/JIT 관련 스택도 읽는 데 강하다.

### 2. JFR의 강점

JFR은 JVM 내부 이벤트를 구조적으로 기록한다.

- GC pause
- lock contention
- allocation burst
- thread state
- safepoint

즉 시간축과 이벤트 분류에 강하다.

### 3. 무엇을 먼저 쓸까

- CPU hotspot이 궁금하면 async-profiler부터 볼 수 있다
- "언제 무엇이 있었나"를 보려면 JFR이 좋다
- thread state/GC/safepoint가 섞이면 JFR이 더 자연스럽다

### 4. 같이 쓰면 더 좋다

한쪽은 샘플링과 flamegraph, 다른 한쪽은 JVM 이벤트와 시간축이다.  
문제 성격에 따라 둘을 교차 검증하는 것이 좋다.

## 실전 시나리오

### 시나리오 1: CPU가 높은데 어디서 쓰는지 모르겠다

async-profiler가 빠르게 hotspot을 찾는 데 도움을 줄 수 있다.

### 시나리오 2: latency spike가 있다

JFR로 GC, safepoint, lock contention, thread parking을 먼저 본다.

### 시나리오 3: native frames가 의심된다

async-profiler가 native stack을 읽는 데 유리하다.  
JNI, C library, kernel path를 볼 때 특히 유용하다.

## 코드로 보기

### 1. JFR 실행 예

```bash
java -XX:StartFlightRecording=name=app,settings=profile,filename=/tmp/app.jfr -jar app.jar
```

### 2. async-profiler 실행 감각

```bash
./profiler.sh -d 30 -f /tmp/profile.svg <pid>
```

### 3. 비교 포인트

```java
// CPU hotspot -> async-profiler
// JVM event timeline -> JFR
// native frame -> async-profiler
// GC/safepoint/lock timing -> JFR
```

### 4. 둘 다 필요한 경우

```java
// 프로파일링 결과를 상호 보완적으로 본다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| async-profiler | CPU/native hotspot에 강하다 | JVM 이벤트 전체를 구조적으로 보지 못할 수 있다 |
| JFR | 이벤트와 시간축이 강하다 | 샘플링 프로파일만큼 바로 직관적이지 않을 수 있다 |
| 둘 다 사용 | 상호 검증이 가능하다 | 도구가 늘어난다 |
| 한 도구만 사용 | 단순하다 | 놓치는 신호가 생길 수 있다 |

핵심은 async-profiler와 JFR을 "누가 이기나"가 아니라 "어떤 질문에 어떤 도구가 더 맞나"로 보는 것이다.

## 꼬리질문

> Q: async-profiler와 JFR의 가장 큰 차이는 무엇인가요?
> 핵심: async-profiler는 샘플링 기반 hotspot 분석에 강하고 JFR은 JVM 이벤트와 시간축 관측에 강하다.

> Q: native stack을 보고 싶으면 무엇이 좋나요?
> 핵심: async-profiler가 유리한 경우가 많다.

> Q: JFR만으로 충분한가요?
> 핵심: 많은 경우 충분하지만, CPU hotspot이나 native frame 분석은 async-profiler가 더 편할 수 있다.

## 한 줄 정리

async-profiler는 hotspot 탐색에, JFR은 JVM 이벤트와 시간축 분석에 강해서 둘을 상황에 맞게 병행하는 것이 가장 실용적이다.
