# Panama Foreign Memory API Basics

> 한 줄 요약: Panama FFM API는 JNI보다 더 안전하고 읽기 쉬운 방식으로 off-heap memory와 native function을 다루게 해 주며, `MemorySegment`와 `Arena`의 lifetime 모델이 핵심이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)
> - [Reachability Fences](./reachability-fences.md)

> retrieval-anchor-keywords: Panama, FFM, Foreign Function and Memory API, MemorySegment, Arena, off-heap memory, native access, linker, memory layout, lifetime, cleanup, downcall, upcall

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로 보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

FFM API는 Java가 네이티브 메모리와 함수에 접근하는 현대적인 방식이다.  
핵심은 다음 두 가지다.

- `MemorySegment`: heap 밖/안의 contiguous memory를 표현
- `Arena`: segment lifetime을 관리

즉 "포인터를 직접 들고 다니는" 모델보다 수명이 더 안전하다.

## 깊이 들어가기

### 1. 왜 Panama가 중요한가

JNI는 강력하지만 경계 비용과 안전성 비용이 있다.  
FFM API는 더 직관적인 메모리 모델과 함수 호출 모델을 제공하려고 한다.

### 2. MemorySegment와 Arena가 핵심이다

`MemorySegment`는 메모리 덩어리다.  
`Arena`는 그 메모리의 lifetime을 관리한다.

즉 segment를 만들기만 하는 것이 아니라, 어떤 scope에서 해제될지도 함께 정한다.

### 3. layout으로 접근할 수 있다

memory layout을 사용하면 크기, offset, alignment를 명시적으로 다룰 수 있다.  
이 점은 off-heap 구조체 접근에 중요하다.

### 4. native access는 제한된 동작이다

FFM은 안전을 위해 restricted method와 native access 설정을 요구할 수 있다.  
즉 강력하지만 무제한은 아니다.

## 실전 시나리오

### 시나리오 1: JNI 대신 안전한 off-heap 접근이 필요하다

FFM은 native 메모리와 함수 호출을 더 읽기 쉽게 만들어 준다.  
새 프로젝트나 점진적 전환에 적합할 수 있다.

### 시나리오 2: 구조체 형태의 native 데이터를 다룬다

layout 기반 접근은 byte-level offset 계산보다 안전하고 명시적이다.

### 시나리오 3: lifetime 사고가 걱정된다

Arena를 통해 resource scope를 명확히 두면 use-after-free 위험을 크게 줄일 수 있다.

## 코드로 보기

### 1. off-heap memory 감각

```java
import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;

try (Arena arena = Arena.ofConfined()) {
    MemorySegment segment = arena.allocate(128);
}
```

### 2. layout 감각

```java
// memory layout은 size, offset, alignment를 명시적으로 표현한다.
```

### 3. native string 처리 감각

```java
// native memory에 문자열을 넣고 꺼내는 작업도 Arena lifetime 안에서 관리한다.
```

### 4. JNI 대비 관점

```java
// FFM은 JNI보다 더 안전하고 선언적인 경로를 제공하려는 방향이다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| FFM API | 안전하고 읽기 쉽다 | 새로운 API와 lifetime 모델을 배워야 한다 |
| JNI | 기존 native 자산을 그대로 쓸 수 있다 | 경계 비용과 위험이 크다 |
| direct buffer | 익숙한 off-heap 도구다 | memory ownership이 덜 명시적일 수 있다 |
| heap array | 가장 단순하다 | native interop 성능/기능이 제한된다 |

핵심은 Panama를 JNI 대체의 "더 안전한 off-heap 모델"로 보는 것이다.

## 꼬리질문

> Q: MemorySegment와 Arena는 각각 무엇인가요?
> 핵심: segment는 메모리 본체이고, arena는 그 lifetime을 관리한다.

> Q: Panama가 JNI보다 나은 점은 무엇인가요?
> 핵심: 더 안전하고 선언적이며 lifetime과 layout을 명시적으로 다룬다.

> Q: FFM도 unsafe한가요?
> 핵심: native 접근 자체는 강력하지만, API는 lifetime과 scope를 통해 훨씬 안전하게 만든다.

## 한 줄 정리

Panama FFM API는 `MemorySegment`와 `Arena`를 중심으로 off-heap memory와 native function을 더 안전하게 다루게 해 주는 현대적 interop 경로다.
