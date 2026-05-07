---
schema_version: 3
title: Phantom Weak and Soft References
concept_id: language/phantom-weak-soft-references
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
- gc
- reference
- memory-leak
aliases:
- Phantom Weak and Soft References
- Java weak soft phantom reference
- ReferenceQueue reachability
- weakly softly phantom reachable
- soft reference cache eviction myth
- 자바 Weak Soft Phantom Reference
symptoms:
- WeakReference SoftReference PhantomReference를 모두 GC가 알아서 메모리를 줄여주는 캐시 도구로 오해해 reachability 의미 차이를 놓쳐
- SoftReference를 운영 캐시로 쓰면 메모리 압박과 GC 정책에 eviction이 묶여 예측 가능성이 낮아질 수 있다는 점을 고려하지 않아
- PhantomReference에서 referent를 get으로 다시 꺼낼 수 있다고 생각하거나 ReferenceQueue cleanup이 즉시 실행된다고 오해해
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/oom-heap-dump-playbook
- language/classloader-memory-leak-playbook
- language/direct-buffer-offheap-memory-troubleshooting
next_docs:
- language/reachability-fences
- language/cleaner-vs-finalize-deprecation
- language/try-with-resources-suppressed-exceptions
linked_paths:
- contents/language/java/oom-heap-dump-playbook.md
- contents/language/java/classloader-memory-leak-playbook.md
- contents/language/java/direct-buffer-offheap-memory-troubleshooting.md
- contents/language/java/try-with-resources-suppressed-exceptions.md
confusable_with:
- language/reachability-fences
- language/cleaner-vs-finalize-deprecation
- language/direct-buffer-offheap-memory-troubleshooting
forbidden_neighbors: []
expected_queries:
- WeakReference SoftReference PhantomReference는 GC reachability 관점에서 어떻게 달라?
- SoftReference를 cache로 쓰는 것이 왜 size TTL eviction policy보다 예측 가능성이 낮을 수 있어?
- PhantomReference와 ReferenceQueue는 post-mortem cleanup에 어떻게 쓰이고 referent를 왜 직접 얻을 수 없어?
- weak reference를 썼는데도 강한 참조가 남아 있으면 왜 객체가 회수되지 않아?
- finalization 대신 reference 기반 cleanup을 쓰더라도 try-with-resources가 더 나은 경우를 설명해줘
contextual_chunk_prefix: |
  이 문서는 Java WeakReference, SoftReference, PhantomReference를 reachability, ReferenceQueue, cache, cleanup 관점에서 비교하는 advanced deep dive다.
  weak reference, soft reference, phantom reference, ReferenceQueue, reachability, GC cleanup 질문이 본 문서에 매핑된다.
---
# Phantom, Weak, and Soft References

> 한 줄 요약: weak, soft, phantom references는 모두 GC reachability를 조절하지만, 의미가 다르므로 캐시, cleanup, 메모리 회수 타이밍을 같은 도구로 보면 안 된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [Try-With-Resources and Suppressed Exceptions](./try-with-resources-suppressed-exceptions.md)

> retrieval-anchor-keywords: soft reference, weak reference, phantom reference, ReferenceQueue, reachability, GC, cache eviction, post-mortem cleanup, finalization, memory pressure, referent, weakly reachable, softly reachable, phantom reachable

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

Java reference 객체는 GC가 객체를 언제 어떻게 회수할지와 관련된 reachability 레벨을 표현한다.

- `WeakReference`: 강한 참조가 사라지면 빠르게 회수 후보가 된다
- `SoftReference`: 메모리 압박이 생길 때까지 좀 더 버틴다
- `PhantomReference`: referent를 직접 얻을 수 없고, 사후 정리용에 가깝다

이 셋은 서로 대체재가 아니다.

## 깊이 들어가기

### 1. weak reference는 언제 유용한가

weak reference는 canonical map이나 observer-style 구조에서 도움이 될 수 있다.  
강한 참조가 사라지면 객체가 더 쉽게 회수된다.

### 2. soft reference는 캐시로 자주 오해된다

soft reference는 한때 "메모리 아낄 때 좋은 캐시"로 자주 쓰였지만, GC 정책과 메모리 압박 해석이 복잡하다.  
그래서 실무에서는 명시적 TTL/size-based cache가 더 예측 가능하다.

### 3. phantom reference는 cleanup 타이밍을 위한 도구다

phantom reference는 referent를 다시 꺼낼 수 없다.  
대신 `ReferenceQueue`와 함께 post-mortem cleanup이나 네이티브 자원 정리에 쓰인다.

### 4. finalization보다 낫지만 여전히 신중해야 한다

finalization은 오래된 메커니즘이고, reference 기반 cleanup도 타이밍이 즉시적이지 않다.  
중요한 자원은 가능하면 try-with-resources로 직접 닫는 편이 좋다.

## 실전 시나리오

### 시나리오 1: 캐시를 만들고 싶은데 메모리 압박을 자동으로 따르고 싶다

soft reference가 떠오르지만, 운영 예측 가능성은 낮을 수 있다.  
실무에서는 size bound, TTL, eviction policy가 더 낫다.

### 시나리오 2: 객체가 사라질 때 후처리를 하고 싶다

phantom reference + `ReferenceQueue`를 고려한다.  
다만 cleanup은 즉시성보다 eventual cleanup에 가깝다.

### 시나리오 3: 참조 타입을 잘못 써서 누수가 난다

reference를 썼다고 메모리 문제가 자동 해결되지는 않는다.  
참조를 잡는 쪽에 강한 참조가 남아 있으면 회수되지 않는다.

## 코드로 보기

### 1. weak reference 예

```java
import java.lang.ref.WeakReference;

WeakReference<Object> ref = new WeakReference<>(new Object());
Object value = ref.get();
```

### 2. soft reference 예

```java
import java.lang.ref.SoftReference;

SoftReference<byte[]> cache = new SoftReference<>(new byte[1024]);
```

### 3. phantom reference 예

```java
import java.lang.ref.PhantomReference;
import java.lang.ref.ReferenceQueue;

ReferenceQueue<Object> queue = new ReferenceQueue<>();
PhantomReference<Object> ref = new PhantomReference<>(new Object(), queue);
```

### 4. 명시적 cleanup이 더 낫다

```java
try (var resource = openResource()) {
    use(resource);
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| weak reference | 강한 참조가 사라지면 빨리 회수된다 | 캐시가 흔들릴 수 있다 |
| soft reference | 메모리 압박을 더 버틴다 | 정책이 예측하기 어렵다 |
| phantom reference | 사후 cleanup에 적합하다 | 직접 값을 꺼낼 수 없다 |
| 명시적 lifecycle | 가장 예측 가능하다 | 코드가 더 필요하다 |

핵심은 참조 타입을 기능으로만 보지 말고 reachability 설계로 보는 것이다.

## 꼬리질문

> Q: weak reference는 언제 쓰나요?
> 핵심: 강한 참조가 없어지면 함께 사라져도 되는 canonical/observer 구조에서 쓴다.

> Q: soft reference가 캐시에 좋은가요?
> 핵심: 예측 가능성이 낮아서 보통 명시적 eviction cache가 더 낫다.

> Q: phantom reference는 왜 필요한가요?
> 핵심: 객체 사후에 네이티브 자원 정리나 cleanup queue 처리를 하기 위해서다.

## 한 줄 정리

weak, soft, phantom reference는 GC reachability를 다루는 서로 다른 도구이고, 실무에서는 캐시와 cleanup을 명시적 lifecycle로 푸는 편이 더 안정적이다.
