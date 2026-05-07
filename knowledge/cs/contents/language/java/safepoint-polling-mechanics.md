---
schema_version: 3
title: Safepoint Polling Mechanics
concept_id: language/safepoint-polling-mechanics
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 85
mission_ids:
- missions/payment
- missions/racingcar
review_feedback_tags:
- safepoint
- jit
- latency
aliases:
- Safepoint Polling Mechanics
- safepoint polling loop back-edge
- HotSpot poll page compiled code
- safepoint reachability poll density
- method exit poll safepoint
- 자바 safepoint polling
symptoms:
- GC pause가 긴데 실제로는 모든 thread가 safepoint에 도달하기까지 기다린 time-to-safepoint 문제일 수 있음을 구분하지 못해
- 긴 loop나 native call에서 safepoint polling density와 poll reachability가 낮아 진입 지연이 생길 수 있다는 점을 놓쳐
- safepoint poll과 deoptimization, runtime check, method exit의 관계를 모른 채 STW latency를 GC 원인으로만 해석해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/safepoint-stop-the-world-diagnostics
- language/jit-warmup-deoptimization
- language/thread-dump-state-interpretation
next_docs:
- language/jfr-jmc-performance-playbook
- language/java-agent-instrumentation-basics
- language/method-inlining-heuristics-deopt-triggers
linked_paths:
- contents/language/java/safepoint-stop-the-world-diagnostics.md
- contents/language/java/jit-warmup-deoptimization.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java/java-agent-instrumentation-basics.md
confusable_with:
- language/safepoint-stop-the-world-diagnostics
- language/jit-warmup-deoptimization
- language/thread-dump-state-interpretation
forbidden_neighbors: []
expected_queries:
- HotSpot safepoint polling은 loop back-edge와 method exit에서 JVM 정지 요청을 어떻게 확인해?
- GC pause처럼 보이지만 time-to-safepoint가 긴 경우를 어떻게 의심할 수 있어?
- 긴 CPU loop나 native call이 safepoint 진입 지연을 만들 수 있는 이유가 뭐야?
- safepoint poll density는 성능과 응답성 사이에 어떤 tradeoff를 만들어?
- safepoint polling과 deoptimization은 같은 현상은 아니지만 왜 같이 관측될 수 있어?
contextual_chunk_prefix: |
  이 문서는 HotSpot safepoint polling을 compiled code의 loop back-edge, method exit, runtime check, native call boundary에서 설명하는 advanced deep dive다.
  safepoint polling, loop back-edge, poll density, time-to-safepoint, HotSpot 질문이 본 문서에 매핑된다.
---
# Safepoint Polling Mechanics

> 한 줄 요약: safepoint polling은 compiled code가 JVM의 정지 요청을 감지하는 메커니즘이고, loop back-edge와 method exit에 들어가는 poll이 길어지면 safepoint 진입 지연으로 이어질 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)

> retrieval-anchor-keywords: safepoint polling, poll page, loop back-edge, method exit, compiled code, stop request, safepoint reachability, deoptimization, native call, runtime check, HotSpot, poll density

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

HotSpot은 safepoint가 필요할 때 모든 Java thread가 안전한 지점에 도달하기를 기다린다.  
compiled code는 이 요청을 알아차리기 위해 polling 지점을 가진다.

이 polling은 보통 다음 지점에 들어간다.

- loop back-edge
- method exit
- 특정 runtime check 경로

## 깊이 들어가기

### 1. poll은 "멈춰라" 신호를 확인하는 체크포인트다

compiled code가 계속 계산만 하고 있으면 JVM이 안전하게 멈추기 어렵다.  
그래서 주기적으로 poll을 하며 safepoint 요청을 본다.

### 2. loop back-edge가 중요한 이유

긴 루프는 back-edge마다 poll이 들어가야 safepoint 응답성이 유지된다.  
루프가 매우 길거나 polling density가 낮으면 진입 지연이 늘 수 있다.

### 3. method exit도 체크 지점이다

메서드가 끝나는 시점은 자연스러운 poll 지점이다.  
이것이 짧은 함수와 긴 함수에서 safepoint responsiveness 차이를 만든다.

### 4. native 구간은 poll이 약해질 수 있다

Java compiled code 밖으로 나가면 JVM이 직접 poll을 넣기 어려운 구간이 생길 수 있다.  
그래서 JNI/native call이 긴 경우 safepoint 지연과 연결해서 본다.

### 5. poll은 성능과 응답성의 trade-off다

poll을 많이 넣으면 safepoint 응답성은 좋아지지만 실행 오버헤드는 늘 수 있다.  
적게 넣으면 반대가 된다.

## 실전 시나리오

### 시나리오 1: 긴 계산 루프가 있다

루프 안에서 poll이 충분한지, JIT가 어떤 최적화를 했는지 본다.

### 시나리오 2: GC pause가 긴데 CPU는 한가하다

실제 원인이 poll 지연인지, native call인지, lock contention인지 구분해야 한다.

### 시나리오 3: deoptimization이 뒤따른다

poll과 deopt는 같은 현상이 아니지만 safepoint 진입과 재컴파일이 이어지며 pause처럼 보일 수 있다.

## 코드로 보기

### 1. poll이 중요해지는 루프

```java
public long sum(long limit) {
    long total = 0;
    for (long i = 0; i < limit; i++) {
        total += i;
    }
    return total;
}
```

### 2. cooperative check를 섞는 예

```java
for (long i = 0; i < limit; i++) {
    total += i;
    if ((i & 0xFFFFF) == 0 && stopRequested) {
        break;
    }
}
```

### 3. 관측 커맨드

```bash
java -Xlog:safepoint=info -jar app.jar
```

### 4. JFR로 확인

```bash
jcmd <pid> JFR.start name=safepoint settings=profile duration=60s filename=/tmp/safepoint.jfr
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| poll density 높임 | safepoint 응답성이 좋아진다 | 실행 오버헤드가 늘 수 있다 |
| poll density 낮춤 | 루프가 더 가볍다 | pause 진입이 늦어질 수 있다 |
| native offload | Java 루프를 줄일 수 있다 | JNI/native 비용이 생긴다 |
| cooperative stop flag | 제어 흐름이 예측 가능하다 | 코드가 복잡해진다 |

핵심은 safepoint가 "그냥 멈추는 기능"이 아니라 polling 지점의 설계 결과라는 점이다.

## 꼬리질문

> Q: safepoint poll은 어디에 들어가나요?
> 핵심: 보통 loop back-edge와 method exit 같은 지점에 들어간다.

> Q: poll이 너무 적으면 어떤 문제가 있나요?
> 핵심: safepoint 진입 지연이 길어질 수 있다.

> Q: poll과 GC pause는 같은 건가요?
> 핵심: 아니다. GC는 safepoint를 활용하는 경우가 많을 뿐이고 poll은 감지 메커니즘이다.

## 한 줄 정리

safepoint polling은 compiled code의 안전 정지 체크포인트이며, loop와 method exit의 poll 배치가 pause 응답성을 좌우한다.
