---
schema_version: 3
title: Object Layout and JOL Intuition
concept_id: language/object-layout-jol-intuition
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/racingcar
- missions/payment
review_feedback_tags:
- jvm-memory
- object-layout
- jol
aliases:
- Object Layout and JOL Intuition
- Java Object Layout JOL header padding
- mark word compressed oops alignment
- object footprint field packing
- JVM object header memory footprint
- 자바 객체 레이아웃 JOL
symptoms:
- Java 객체 메모리 사용량을 필드 크기의 단순 합으로 계산해 object header, alignment, padding, compressed pointer 효과를 놓쳐
- 작은 객체를 많이 만들 때 footprint가 예상보다 큰 원인을 GC나 컬렉션만으로 오진하고 JOL로 layout을 확인하지 않아
- false sharing이나 lock state 이야기를 object header와 cache line 관점 없이 추상적인 성능 문제로만 해석해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/compressed-oops-class-pointers
- language/stack-vs-heap-escape-intuition
- operating-system/cpu-cache-coherence-memory-barrier
next_docs:
- language/tlab-plab-allocation-intuition
- language/escape-analysis-scalar-replacement
- language/object-pooling-myths-modern-jvm
linked_paths:
- contents/language/java/compressed-oops-class-pointers.md
- contents/language/java/stack-vs-heap-escape-intuition.md
- contents/language/java/memory-barriers-varhandle-fences.md
- contents/language/java/biased-locking-removal-lock-states.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
confusable_with:
- language/compressed-oops-class-pointers
- language/stack-vs-heap-escape-intuition
- language/tlab-plab-allocation-intuition
forbidden_neighbors: []
expected_queries:
- Java 객체 메모리 크기는 필드 크기 합보다 왜 커지고 JOL로 무엇을 확인할 수 있어?
- object header mark word klass pointer alignment padding compressed oops를 beginner 이후 단계로 설명해줘
- 작은 객체를 많이 만들 때 padding과 alignment가 footprint에 어떤 영향을 줘?
- JOL 출력은 JVM 옵션과 구현에 따라 달라질 수 있다는 뜻을 어떻게 해석해?
- object layout과 false sharing cache line lock state는 어떤 관계가 있어?
contextual_chunk_prefix: |
  이 문서는 Java Object Layout과 JOL을 통해 object header, mark word, alignment, padding, compressed oops, footprint를 읽는 advanced deep dive다.
  object layout, JOL, mark word, padding, compressed oops, object footprint 질문이 본 문서에 매핑된다.
---
# Object Layout and JOL Intuition

> 한 줄 요약: object layout은 필드 순서보다 훨씬 더 많은 것을 포함하며, JOL은 header, alignment, padding, compressed pointer effect를 눈으로 확인하는 데 유용하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Compressed Oops and Class Pointers](./compressed-oops-class-pointers.md)
> - [Stack vs Heap Escape Intuition](./stack-vs-heap-escape-intuition.md)
> - [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)
> - [Biased Locking Removal and Lock States](./biased-locking-removal-lock-states.md)

> retrieval-anchor-keywords: object layout, JOL, Java Object Layout, mark word, alignment, padding, field packing, header size, compressed oops, false sharing intuition, object footprint

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

Java 객체는 필드만 있는 것이 아니다.

- object header
- mark word
- klass pointer
- field alignment
- padding

이 전부가 실제 footprint를 만든다.  
JOL(Java Object Layout)은 이런 구조를 보기 쉽게 만들어 주는 도구다.

## 깊이 들어가기

### 1. 왜 layout이 중요한가

layout은 단순 호기심이 아니라 성능과 메모리의 출발점이다.

- 객체 하나당 몇 바이트를 쓰는가
- 필드 순서가 padding에 영향을 주는가
- compressed oops가 footprint에 어떤 차이를 만드는가
- locking이 header에 어떤 흔적을 남기는가

### 2. padding과 alignment는 생각보다 크다

필드 몇 개를 추가했는데 메모리 사용량이 눈에 띄게 늘 수 있다.  
그 이유는 실제로는 field 자체보다 alignment와 padding이 더 큰 비용이 될 수 있기 때문이다.

### 3. header는 lock과 identity의 접점이다

mark word에는 locking 관련 정보와 identity hash code 같은 것이 얽힌다.  
그래서 object header를 이해하면 locking과 hashCode 동작이 더 잘 보인다.

### 4. JOL은 정답이 아니라 관측 도구다

JOL 출력은 JVM 구현과 옵션에 영향을 받는다.  
즉 layout을 "외워야 하는 값"이 아니라 "현재 환경을 읽는 창"으로 보는 편이 좋다.

## 실전 시나리오

### 시나리오 1: 작은 class를 많이 만들었는데 메모리가 많이 든다

필드 수보다 layout overhead와 padding을 먼저 확인해야 한다.  
필드 순서 조정만으로도 달라질 수 있다.

### 시나리오 2: false sharing을 의심한다

인접 필드가 같은 cache line에 있으면 충돌이 날 수 있다.  
layout과 cache line을 같이 보는 감각이 필요하다.

### 시나리오 3: synchronized가 흔적을 남기는지 보고 싶다

lock 상태는 object header에 반영될 수 있다.  
layout을 보면 단순히 "객체가 크다"보다 더 많은 것을 읽을 수 있다.

## 코드로 보기

### 1. layout 감각 예시

```java
public class CounterState {
    int a;
    long b;
    boolean c;
}
```

### 2. JOL을 쓰는 예

```java
// JOL로 object header, field offset, padding을 관찰한다.
```

### 3. field packing을 생각하는 예

```java
// 같은 타입끼리 몰아두면 padding이 줄어들 수 있다.
```

### 4. layout 해석 시 주의

```java
// layout 결과는 JVM 옵션, architecture, compression 설정에 따라 달라질 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| layout 관찰 | 메모리/캐시 문제를 읽기 쉽다 | JVM 세부를 알아야 한다 |
| field packing | footprint를 줄일 수 있다 | 도메인 모델 가독성이 떨어질 수 있다 |
| padding 의도화 | false sharing을 완화할 수 있다 | 메모리를 더 쓴다 |
| 단순 class 설계 | 읽기 쉽다 | layout 최적화를 놓칠 수 있다 |

핵심은 JOL을 "메모리 계측 현미경"으로 보고, layout을 통해 padding과 header 비용을 읽는 것이다.

## 꼬리질문

> Q: JOL은 무엇을 보여주나요?
> 핵심: object header, field offset, alignment, padding, compressed pointer 효과를 보여준다.

> Q: object layout이 왜 중요한가요?
> 핵심: 실제 footprint와 cache behavior가 layout에 크게 좌우되기 때문이다.

> Q: field 순서만 바꾸면 성능이 바뀔 수 있나요?
> 핵심: padding과 alignment가 바뀌면 footprint와 cache locality가 달라질 수 있다.

## 한 줄 정리

JOL은 Java 객체의 실제 layout을 읽는 도구이고, header와 padding까지 봐야 footprint와 cache behavior를 제대로 이해할 수 있다.
