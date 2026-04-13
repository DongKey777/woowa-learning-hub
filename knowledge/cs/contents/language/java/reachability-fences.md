# Reachability Fences

> 한 줄 요약: `Reference.reachabilityFence()`는 JIT가 객체를 너무 일찍 죽은 것으로 오해해 cleanup보다 먼저 회수하는 일을 막기 위한 최종 가시성 보장 장치다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Cleaner vs `finalize()` Deprecation](./cleaner-vs-finalize-deprecation.md)
> - [Phantom, Weak, and Soft References](./phantom-weak-soft-references.md)
> - [JNI Native Call Overhead](./jni-native-call-overhead.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)

> retrieval-anchor-keywords: reachabilityFence, strong reachability, premature reclamation, finalizer, cleanup, object lifetime, JIT, Reference API, off-heap resource, GC liveness, escape analysis, post-use fence

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

`Reference.reachabilityFence(Object)`는 지정한 객체가 메서드 호출 시점까지 강하게 reachable하도록 보장한다.  
주 목적은 JIT 최적화로 인해 객체가 너무 일찍 죽었다고 판단되는 문제를 막는 것이다.

이 기능은 `finalize()`나 Cleaner와는 다르다.  
cleanup 도구가 아니라 liveness 보장 장치다.

## 깊이 들어가기

### 1. 왜 필요했나

JIT는 객체가 더 이상 사용되지 않는다고 판단하면 최적화를 할 수 있다.  
그런데 native resource, cleaner action, close 이후 코드가 객체 생존에 의존하면 너무 이른 회수가 문제가 될 수 있다.

### 2. 언제 쓰는가

보통 이런 패턴에서 고려한다.

- native handle을 감싼 객체
- off-heap resource를 가진 객체
- cleanup이 객체의 마지막 사용에 의존하는 경우

### 3. 무엇을 하지 않는가

reachability fence는 자원을 닫아 주지 않는다.  
또한 일반적인 메모리 가시성 도구도 아니다.

### 4. JIT와 더 가까운 문제다

이 기능은 GC 구현이라기보다 프로그램 최적화와 객체 수명 추론의 경계에서 중요하다.  
즉 "코드상 마지막 사용"과 "JIT가 보는 마지막 사용"이 다를 수 있다.

## 실전 시나리오

### 시나리오 1: native resource wrapper가 너무 일찍 정리된다

cleanup 코드가 예상보다 먼저 실행되면 fence가 필요할 수 있다.  
하지만 먼저 설계를 점검하고, 정말 liveness issue인지 확인해야 한다.

### 시나리오 2: direct buffer 또는 off-heap handle을 감싼다

객체 wrapper가 마지막 native call 후에도 살아 있어야 할 때 fence가 도움이 된다.

### 시나리오 3: finalize/Cleaner에 기대고 있다

fence는 그 대체재가 아니다.  
자원 해제는 명시적 close가 우선이고 fence는 보조 안전장치다.

## 코드로 보기

### 1. 기본 사용

```java
import java.lang.ref.Reference;

Reference.reachabilityFence(this);
```

### 2. native wrapper 감각

```java
public void useNativeHandle() {
    nativeCall(handle);
    java.lang.ref.Reference.reachabilityFence(this);
}
```

### 3. cleanup과 구분

```java
// fence는 close가 아니라 liveness 보장용이다.
```

### 4. 마지막 사용 직후에 둔다

```java
// 객체가 더 이상 필요 없다고 JIT가 판단하기 전에
// 마지막 의미 있는 사용 뒤에 fence를 둔다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| reachabilityFence | premature reclamation을 막는다 | 쓰임새가 좁고 이해가 필요하다 |
| Cleaner | 비동기 cleanup이 가능하다 | 즉시성 보장이 없다 |
| explicit close | 가장 명확하다 | 호출 책임이 있다 |
| finalization | 자동처럼 보인다 | deprecated이고 위험하다 |

핵심은 fence를 cleanup 메커니즘으로 착각하지 않는 것이다.

## 꼬리질문

> Q: reachabilityFence는 왜 필요한가요?
> 핵심: JIT가 객체를 너무 일찍 죽은 것으로 보아 cleanup보다 먼저 회수하는 일을 막기 위해서다.

> Q: fence가 `close()`를 대신하나요?
> 핵심: 아니다. liveness 보장일 뿐 cleanup은 아니다.

> Q: 언제 가장 조심해야 하나요?
> 핵심: native resource wrapper, off-heap handle, 마지막 사용에 민감한 cleanup 경로다.

## 한 줄 정리

`reachabilityFence()`는 객체가 마지막 사용 지점까지 살아 있음을 보장하는 최종 안전장치이고, 자원 해제를 대신하지는 않는다.
