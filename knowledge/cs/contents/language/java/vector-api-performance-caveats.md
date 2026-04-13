# Vector API Performance Caveats

> 한 줄 요약: Vector API는 SIMD 표현을 Java로 끌어오지만, 항상 빠른 것은 아니며 shape, masking, alignment, fallback, input size, benchmark design이 성능을 좌우한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Vector API Basics](./vector-api-basics.md)
> - [JMH Benchmarking Pitfalls](./jmh-benchmarking-pitfalls.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)

> retrieval-anchor-keywords: Vector API performance caveats, SIMD, alignment, masking, fallback, shape, lane, vectorization, throughput, benchmark size, scalar fallback, hardware dependency

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

Vector API는 성능을 낼 수 있지만, 조건이 맞아야 한다.

- 충분히 큰 입력
- 단순하고 반복적인 연산
- 알맞은 alignment
- JIT가 유리하게 볼 수 있는 코드 형태
- 지원하는 hardware shape

작은 입력이나 분기 많은 코드에서는 오히려 비용이 커질 수 있다.

## 깊이 들어가기

### 1. shape가 맞지 않으면 효과가 줄어든다

지원하는 vector shape와 데이터 크기가 잘 맞지 않으면 tail 처리와 masking 비용이 늘 수 있다.

### 2. masking은 공짜가 아니다

lane 일부만 처리하는 경우 mask가 들어가고, 이는 순수 scalar보다 복잡할 수 있다.

### 3. alignment와 memory layout이 중요하다

데이터가 잘 정렬되어 있지 않거나 접근 패턴이 불규칙하면 벡터화 이득이 줄어든다.

### 4. fallback 경로를 늘 봐야 한다

Vector API는 hardware 지원이 약한 플랫폼에서도 동작하지만, 그 경우 특별한 성능 이득이 없을 수 있다.

### 5. microbenchmark가 자주 틀린다

JMH 없이 벡터화 성능을 이야기하면 warmup, DCE, constant folding, cache effects를 놓치기 쉽다.

## 실전 시나리오

### 시나리오 1: 숫자 배열 처리

합산, 곱셈, 필터링 같은 규칙적인 연산에서만 성능 이득이 뚜렷해질 수 있다.

### 시나리오 2: 입력이 너무 작다

Vector API 오버헤드가 더 커질 수 있다.  
작은 데이터는 scalar loop가 더 유리할 수 있다.

### 시나리오 3: 분기가 많다

lane-wise operation을 해도 branch가 많으면 SIMD 이득이 줄어든다.

## 코드로 보기

### 1. 벡터 API 후보

```java
// 동일 연산을 큰 배열 전체에 반복하는 형태가 좋다.
```

### 2. benchmark 대상

```java
// 작은 입력, 큰 입력, 정렬된 입력, 비정렬 입력을 모두 비교한다.
```

### 3. fallback 감각

```java
// CPU/플랫폼에 따라 vectorization 이득이 크게 달라질 수 있다.
```

### 4. scalar가 더 나을 수 있는 예

```java
for (int i = 0; i < n; i++) {
    data[i] = data[i] * 2 + 1;
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| Vector API | SIMD를 명시적으로 노릴 수 있다 | shape/alignment/fallback을 신경 써야 한다 |
| scalar loop | 단순하다 | SIMD 이득을 못 볼 수 있다 |
| JNI SIMD | 특정 플랫폼에서 강할 수 있다 | 경계 비용과 유지보수 비용이 크다 |
| JIT 자동 벡터화 | 코드가 자연스럽다 | 항상 성공하지는 않는다 |

핵심은 Vector API가 "항상 빠름"이 아니라 조건부 최적화라는 점이다.

## 꼬리질문

> Q: Vector API가 느려질 수 있는 이유는 무엇인가요?
> 핵심: 입력이 작거나, masking/alignment 비용이 크거나, fallback 경로가 타기 때문이다.

> Q: 벡터화 성능은 어떻게 확인하나요?
> 핵심: JMH와 JFR로 입력 크기와 steady-state를 함께 본다.

> Q: Vector API가 모든 CPU에서 이득인가요?
> 핵심: 아니다. hardware support와 구현 상태에 따라 달라진다.

## 한 줄 정리

Vector API는 SIMD 성능을 노릴 수 있지만, 입력 크기와 alignment, masking, fallback, benchmark design을 잘못 다루면 기대만큼 빠르지 않다.
