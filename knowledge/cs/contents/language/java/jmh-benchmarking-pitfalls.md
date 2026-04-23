# JMH Benchmarking Pitfalls

> 한 줄 요약: JMH는 microbenchmark를 덜 틀리게 만들지만, warmup, dead-code elimination, constant folding, false sharing, allocation effects를 잘못 다루면 여전히 잘못된 결론을 낼 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [Escape Analysis, Stack Allocation, Benchmarking, and Object Reuse Misconceptions](./escape-analysis-stack-allocation-benchmark-misconceptions.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)

> retrieval-anchor-keywords: JMH, warmup, measurement iteration, dead-code elimination, constant folding, false sharing, Blackhole, fork, benchmark bias, microbenchmark, steady state, profiler interference, escape analysis misconception

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

JMH는 JVM microbenchmark의 표준 도구에 가깝다.  
그렇다고 "JMH만 쓰면 자동으로 옳다"는 뜻은 아니다.

benchmark는 JIT, GC, CPU cache, branch prediction, allocation, inlining 영향을 모두 받는다.  
그래서 JMH를 쓸 때는 tool보다 실험 설계를 먼저 봐야 한다.

## 깊이 들어가기

### 1. warmup이 없는 benchmark는 위험하다

JIT는 실행 데이터를 보고 최적화한다.  
warmup이 부족하면 interpreter/C1/C2 전환과 최적화 완료 전 구간을 측정할 수 있다.

### 2. dead-code elimination을 조심해야 한다

측정하려는 결과가 실제로 쓰이지 않으면 JIT가 일을 지워버릴 수 있다.  
이때는 `Blackhole` 같은 도구를 써서 관찰 가능한 사용을 유지해야 한다.

### 3. constant folding과 hoisting도 함정이다

입력이 고정적이면 컴파일러가 결과를 상수처럼 접어버릴 수 있다.  
그럴 경우 "계산이 빠르다"가 아니라 "계산이 사라졌다"일 수 있다.

### 4. fork는 왜 중요한가

JMH는 forked JVM을 사용해 외부 상태의 오염을 줄인다.  
fork가 너무 적으면 이전 benchmark의 영향을 받을 수 있고, 너무 많으면 비용이 커진다.

### 5. 측정 대상이 너무 작으면 noise가 지배한다

매우 짧은 연산은 다음 영향을 강하게 받는다.

- call overhead
- timer resolution
- OS scheduling
- cache warm state
- GC timing

즉 microbenchmark는 코드가 아니라 환경을 함께 재는 경우가 많다.

## 실전 시나리오

### 시나리오 1: 로컬에서는 빠른데 CI에서는 느리다

CI와 로컬의 CPU, load, JVM 옵션, throttling, container limit이 다를 수 있다.  
benchmark 환경은 되도록 고정해야 한다.

### 시나리오 2: 벤치마크 숫자가 말이 안 된다

일정 시간마다 숫자가 튀거나 너무 좋아 보이면 constant folding, DCE, false sharing, allocation elimination을 의심해야 한다.

### 시나리오 3: JMH 결과를 production 성능으로 오해한다

JMH는 해당 메서드/경로의 상대 비교에 강하고, 전체 시스템 지연이나 contention을 완전히 대표하지는 못한다.

## 코드로 보기

### 1. 기본적인 benchmark 골격

```java
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Warmup;

@Warmup(iterations = 5)
@Measurement(iterations = 5)
@Fork(2)
@BenchmarkMode(org.openjdk.jmh.annotations.Mode.Throughput)
public class SampleBenchmark {
    @Benchmark
    public int work() {
        return 1 + 2 + 3;
    }
}
```

### 2. 결과를 소비해야 한다

```java
// Blackhole을 써서 결과가 최적화로 지워지지 않게 한다.
```

### 3. 입력을 변화시켜야 한다

```java
// 고정 상수 대신 다양한 입력을 써서 folding을 피한다.
```

### 4. false sharing도 테스트해야 한다

```java
// 인접한 필드가 서로 다른 thread에서 자주 바뀌면 cache line 충돌이 생길 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| JMH 사용 | JVM benchmark의 표준에 가깝다 | 실험 설계 실수는 여전히 가능하다 |
| fork 증가 | 오염을 줄인다 | 실행 시간이 길어진다 |
| warmup 증가 | steady state를 더 잘 본다 | 측정 비용이 늘어난다 |
| 수동 benchmark | 빠르게 만들 수 있다 | 결과 신뢰도가 낮다 |

핵심은 JMH를 "정답 생성기"가 아니라 "실수 감소 장치"로 보는 것이다.

## 꼬리질문

> Q: warmup이 왜 중요한가요?
> 핵심: JIT 최적화가 완료되기 전 구간을 측정하면 결과가 왜곡되기 때문이다.

> Q: JMH가 있는데도 왜 잘못 측정하나요?
> 핵심: 결과를 안 쓰거나 입력을 고정하면 JIT가 일을 지워버릴 수 있다.

> Q: benchmark와 production이 다른 이유는 무엇인가요?
> 핵심: cache, contention, GC, JIT, scheduling, load pattern이 다르기 때문이다.

## 한 줄 정리

JMH는 benchmark를 더 믿을 수 있게 만들지만, warmup과 input design을 잘못하면 여전히 틀린 결론을 낼 수 있다.
