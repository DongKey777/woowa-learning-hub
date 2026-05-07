---
schema_version: 3
title: JIT Warmup and Deoptimization
concept_id: language/jit-warmup-deoptimization
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 88
mission_ids:
- missions/racingcar
- missions/payment
review_feedback_tags:
- jit
- performance
- deoptimization
aliases:
- JIT Warmup and Deoptimization
- HotSpot tiered compilation warmup
- Java deoptimization uncommon trap
- JIT profile pollution latency spike
- PrintCompilation PrintInlining JFR compilation
- 자바 JIT warmup deopt
symptoms:
- 서버 시작 직후 latency가 높다가 안정되는 현상을 cache 문제로만 보고 interpreter, C1/C2, tiered compilation warmup을 놓쳐
- benchmark 결과를 warmup 없이 읽어 JIT 최적화 전후 구간과 deoptimization spike를 평균에 섞어 해석해
- polymorphic call site, class loading, profile change로 JIT 가정이 깨져 deopt가 나는 상황을 단순 GC나 네트워크 지연으로 오진해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/jvm-gc-jmm-overview
- language/method-inlining-heuristics-deopt-triggers
- language/code-cache-jit-profiling
next_docs:
- language/jmh-benchmarking-pitfalls
- language/escape-analysis-scalar-replacement
- language/jfr-jmc-performance-playbook
linked_paths:
- contents/language/java/jvm-gc-jmm-overview.md
- contents/language/java/virtual-threads-project-loom.md
- contents/language/java/g1-vs-zgc.md
- contents/language/java/reflection-cost-and-alternatives.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
- contents/language/java/code-cache-jit-profiling.md
- contents/language/java/method-inlining-heuristics-deopt-triggers.md
- contents/language/java/jmh-benchmarking-pitfalls.md
confusable_with:
- language/jmh-benchmarking-pitfalls
- language/code-cache-jit-profiling
- language/method-inlining-heuristics-deopt-triggers
forbidden_neighbors: []
expected_queries:
- Java JIT warmup은 왜 필요하고 서버 시작 직후 latency가 높은 이유를 설명해줘
- deoptimization은 어떤 JIT 가정이 깨질 때 발생하는지 예제로 알려줘
- PrintCompilation PrintInlining이나 JFR compilation event로 JIT 문제를 어떻게 관측해?
- polymorphic call site나 class loading이 JIT profile을 바꿔 latency spike를 만들 수 있어?
- microbenchmark와 운영 성능이 JIT warmup 때문에 달라지는 이유를 설명해줘
contextual_chunk_prefix: |
  이 문서는 HotSpot JIT warmup, tiered compilation, inlining, type profile, deoptimization을 Java 성능 관측 관점에서 설명하는 advanced deep dive다.
  JIT warmup, deoptimization, PrintCompilation, C1 C2, latency spike, benchmark trap 질문이 본 문서에 매핑된다.
---
# JIT Warmup and Deoptimization

> 한 줄 요약: JIT는 실행 데이터를 바탕으로 코드를 최적화하지만, 그 가정이 깨지면 deoptimization이 발생한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [G1 GC vs ZGC](./g1-vs-zgc.md)
> - [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)
> - [CPU Cache, Coherence, Memory Barrier](../../operating-system/cpu-cache-coherence-memory-barrier.md)

retrieval-anchor-keywords: JIT warmup, deoptimization, tiered compilation, method inlining for jit warmup, code cache jit warmup, profile pollution, deopt trigger, jit warmup tiered compilation inlining code cache profile pollution deopt trigger, HotSpot compilation, PrintCompilation, JFR compilation event, C1 C2, warmup latency spike, uncommon trap, polymorphic call site, JIT benchmark trap

<details>
<summary>Table of Contents</summary>

- [왜 필요한가](#왜-필요한가)
- [JIT가 하는 일](#jit가-하는-일)
- [Warmup이 필요한 이유](#warmup이-필요한-이유)
- [Deoptimization이 생기는 이유](#deoptimization이-생기는-이유)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 필요한가

Java 성능은 "바이트코드 실행"으로 끝나지 않는다.  
HotSpot JVM은 실행 중인 코드를 분석해서 더 빠른 기계어로 바꾼다.

그래서 다음을 알아야 한다.

- 왜 첫 실행이 느린가
- 왜 벤치마크가 흔들리는가
- 왜 최적화된 코드가 다시 느려질 수 있는가
- 왜 짧게 실행되는 배치가 서버와 다르게 보이는가

## JIT가 하는 일

HotSpot은 보통 interpreter로 시작해서, 충분히 뜨거워진 코드를 JIT가 컴파일한다.

대표 흐름:

1. 인터프리터가 먼저 실행한다
2. 프로파일이 쌓인다
3. C1/C2 같은 컴파일 단계가 개입한다
4. 타입 분포와 분기 패턴을 바탕으로 인라이닝/전개 최적화가 일어난다

핵심은 **실행 데이터가 있어야 더 나은 코드를 만들 수 있다**는 점이다.

### 최적화가 잘 먹는 조건

- 같은 메서드가 반복 호출된다
- 호출 대상 타입이 안정적이다
- 분기 패턴이 반복된다
- 메서드가 너무 크지 않다

## Warmup이 필요한 이유

JIT는 실행 중에 배우므로, 초반 구간은 아직 최적화가 덜 된 상태일 수 있다.

이 때문에 다음이 자주 일어난다.

- 첫 요청이 느리다
- 시작 직후 p99가 높다
- microbenchmark 결과가 실제와 다르다

### 벤치마크 함정

짧은 루프만 돌리고 평균을 보면 interpreter/C1/C2 전환 구간을 놓친다.  
실제 서비스는 warmup 이후 상태를 봐야 한다.

## Deoptimization이 생기는 이유

JIT는 "이 코드가 이렇게 생겼을 것"이라는 가정을 한다.  
그 가정이 깨지면 deopt로 되돌아간다.

자주 보는 원인:

- call site가 monomorphic에서 polymorphic으로 바뀜
- inlining한 메서드의 가정이 틀어짐
- class loading으로 새로운 구현이 등장함
- branch profile이 바뀜
- uncommon trap이 현실화됨

즉, **최적화가 틀렸을 때 안전하게 되돌아가는 메커니즘**이 있다.

## 실전 시나리오

### 시나리오 1: 시작 직후만 느리다

증상:

- 서버 부팅 직후 요청이 느림
- 몇 분 후 정상화

원인 후보:

- JIT warmup 전
- class loading
- cache 미스

대응:

- warmup 트래픽을 흘린다
- startup path를 분리한다
- 핵심 경로를 미리 태운다

### 시나리오 2: 갑자기 latency spike가 난다

최적화된 코드가 deopt되면 짧은 지연 스파이크가 생길 수 있다.

점검 순서:

1. `PrintCompilation`/JFR로 컴파일 이벤트를 본다
2. type profile이 바뀌었는지 확인한다
3. 호출 대상이 바뀌는 패턴이 있는지 본다
4. 메서드가 너무 자주 변경되는지 본다

### 시나리오 3: 벤치마크는 빠른데 운영은 느리다

벤치마크는 warmup을 제대로 못 했거나, 입력 분포가 실제와 다를 수 있다.  
JIT가 이득을 보는 구간을 포함하지 않으면 숫자가 과장되거나 왜곡된다.

## 코드로 보기

### warmup 루프 예시

```java
public long sum(int n) {
    long total = 0;
    for (int i = 0; i < n; i++) {
        total += i;
    }
    return total;
}
```

이런 단순 메서드도 반복 호출되면 JIT가 더 공격적으로 최적화할 수 있다.

### 타입이 바뀌면 가정이 깨질 수 있는 예시

```java
interface Formatter {
    String format(Object value);
}

final class FastFormatter implements Formatter {
    public String format(Object value) {
        return value.toString();
    }
}

final class SlowFormatter implements Formatter {
    public String format(Object value) {
        return "[" + value + "]";
    }
}
```

호출 지점이 한 구현체에만 노출되다가, 나중에 다른 구현체가 섞이면 프로파일이 달라질 수 있다.

### 관측 커맨드

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintCompilation -XX:+PrintInlining -jar app.jar
```

```bash
jcmd <pid> Compiler.codecache
jcmd <pid> JFR.start name=jit settings=profile duration=60s filename=jit.jfr
```

## 트레이드오프

| 관점 | 이득 | 비용 |
|---|---|---|
| Warmup 최적화 | steady-state 성능이 좋아진다 | 초반 지연이 존재한다 |
| 공격적 inlining | 호출 오버헤드가 줄어든다 | deopt 리스크가 생긴다 |
| 프로파일 기반 최적화 | 실제 패턴에 맞출 수 있다 | 입력 분포가 바뀌면 흔들린다 |
| 짧은 서비스 | 단순하다 | JIT 이득을 충분히 못 볼 수 있다 |

핵심은 **짧게 끝나는 작업은 JIT 이득을 덜 보고, 장수하는 워크로드는 JIT 이득을 더 크게 본다**는 점이다.

## 꼬리질문

> Q: JIT warmup이 왜 필요한가요?
> 의도: 인터프리터와 컴파일러 역할 분담 이해 여부 확인
> 핵심: 실행 데이터를 모아 더 나은 기계어를 만들기 때문이다

> Q: deoptimization이 왜 발생하나요?
> 의도: JIT 최적화의 가정과 안전장치 이해 여부 확인
> 핵심: 타입 분포나 분기 패턴 같은 가정이 깨지면 되돌아간다

> Q: 벤치마크와 운영 성능이 다른 이유는 무엇인가요?
> 의도: warmup과 입력 분포 차이를 보는지 확인
> 핵심: warmup, 캐시, GC, 프로파일 차이가 섞인다

## 한 줄 정리

JIT는 실행 데이터를 바탕으로 빨라지지만, 그 가정이 깨지면 deopt가 일어나므로 warmup과 프로파일 변화를 같이 봐야 한다.
