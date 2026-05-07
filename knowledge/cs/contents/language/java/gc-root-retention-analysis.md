---
schema_version: 3
title: GC Root Retention Analysis
concept_id: language/gc-root-retention-analysis
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- heap-dump
- memory-leak
- gc-root
aliases:
- GC root retention analysis
- heap dump retention path
- dominator tree retained size
- GC root reference chain
- ThreadLocal retention
- static field leak
- classloader retention path
symptoms:
- heap dump에서 객체 수만 보고 어떤 GC root가 객체를 살려 두는지 reference chain과 retention path를 추적하지 않아
- shallow size와 retained size를 혼동해 실제 누수 원인을 지배하는 dominator를 놓쳐
- ThreadLocal, static cache, classloader, JNI global reference가 의도된 보관인지 leak인지 한도와 cleanup policy로 판단하지 못해
intents:
- troubleshooting
- deep_dive
prerequisites:
- language/oom-heap-dump-playbook
next_docs:
- language/classloader-memory-leak-playbook
- language/threadlocal-leaks-context-propagation
- language/phantom-weak-soft-references
linked_paths:
- contents/language/java/oom-heap-dump-playbook.md
- contents/language/java/classloader-memory-leak-playbook.md
- contents/language/java/phantom-weak-soft-references.md
- contents/language/java/threadlocal-leaks-context-propagation.md
confusable_with:
- language/oom-heap-dump-playbook
- language/classloader-memory-leak-playbook
- language/threadlocal-leaks-context-propagation
forbidden_neighbors: []
expected_queries:
- heap dump에서 GC root retention path를 따라 객체가 왜 살아 있는지 분석하는 방법을 알려줘
- shallow size와 retained size, dominator tree 차이를 memory leak 분석 관점으로 설명해줘
- static field ThreadLocal classloader JNI global reference가 GC root가 되는 경로를 알려줘
- 누수처럼 보이는 장기 보관과 진짜 leak을 cache TTL eviction cleanup policy로 어떻게 구분해?
- redeploy 후 old classloader가 root chain에 남는 문제를 heap dump에서 어떻게 찾지?
contextual_chunk_prefix: |
  이 문서는 GC root retention analysis를 heap dump, reference chain, dominator tree, retained size, ThreadLocal, static field, classloader, JNI global reference 관점으로 진단하는 advanced playbook이다.
  GC root, retention path, heap dump, dominator tree, retained size, memory leak analysis 질문이 본 문서에 매핑된다.
---
# GC Root Retention Analysis

> 한 줄 요약: GC root 분석은 "왜 객체가 아직 살아 있는가"를 묻는 일이고, heap dump에서 root chain과 retention path를 읽어야 진짜 누수와 단순 장기 보관을 구분할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [Phantom, Weak, and Soft References](./phantom-weak-soft-references.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)

> retrieval-anchor-keywords: GC root, retention path, reference chain, heap dump, dominator tree, retained size, leak analysis, thread local, static field, class loader, JNI global reference, local reference

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

GC root는 GC가 시작할 때 반드시 살아 있다고 보는 객체나 참조의 출발점이다.  
heap dump에서 중요한 것은 객체 자체보다 **어떤 root에서 이어져서 살아남는가**다.

대표 root 경로:

- thread stack local
- static field
- JNI global reference
- class loader
- running thread
- monitor / synchronization root

## 깊이 들어가기

### 1. retained size와 shallow size는 다르다

- shallow size: 객체 자기 자신이 차지하는 크기
- retained size: 그 객체가 유지시키는 전체 하위 그래프 크기

누수 분석에서는 retained size가 훨씬 중요하다.

### 2. dominator tree를 봐야 한다

같은 객체가 여러 경로로 참조될 수 있다.  
그중 실제로 retention을 지배하는 dominator를 찾아야 누수 원인을 좁힐 수 있다.

### 3. GC root는 반드시 나쁜 것은 아니다

thread local, cache, static registry는 의도된 보관일 수 있다.  
문제는 한도와 해제 규칙이 없을 때다.

### 4. classloader와 thread가 자주 root가 된다

webapp redeploy나 thread pool reuse가 있으면 root chain이 길어지고, 결국 메모리 회수 불능처럼 보일 수 있다.  
관련해서 [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)과 [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)을 같이 보면 좋다.

### 5. JNI root도 놓치기 쉽다

native code가 global reference를 잡으면 Java heap dump에서 원인이 흐릿해질 수 있다.  
이 경우 native 쪽 자원 모델까지 봐야 한다.

## 실전 시나리오

### 시나리오 1: heap이 계속 커지는데 어떤 객체가 잡고 있는지 모르겠다

heap dump에서 retained size가 큰 dominator부터 본다.  
static cache, thread local, listener, classloader를 우선 의심한다.

### 시나리오 2: 누수처럼 보이지만 사실은 장기 보관이다

cache, queue, buffer pool, preloaded registry는 의도된 retention일 수 있다.  
그럴 때는 한도, TTL, eviction 정책을 함께 봐야 한다.

### 시나리오 3: redeploy 후 메모리가 안 내려간다

old classloader가 GC root chain에 남아 있을 가능성이 높다.  
dominator tree와 thread dump를 같이 봐야 한다.

## 코드로 보기

### 1. static retention

```java
private static final List<Object> CACHE = new ArrayList<>();
```

### 2. ThreadLocal retention

```java
private static final ThreadLocal<Object> HOLDER = new ThreadLocal<>();
```

### 3. reference chain 감각

```java
// root -> cache -> service -> buffer -> payload
```

### 4. 진단 흐름

```bash
jcmd <pid> GC.heap_dump /tmp/heap.hprof
jcmd <pid> GC.class_histogram
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| heap dump 분석 | retention path를 정확히 볼 수 있다 | 무겁고 시간이 든다 |
| histogram | 빠른 초기 스캔이 가능하다 | root chain은 안 보인다 |
| JFR | 시간축까지 함께 볼 수 있다 | heap graph는 약하다 |
| runtime logging | 재현이 쉽다 | 장기 root chain 파악은 약하다 |

핵심은 "무슨 객체가 있나"보다 "무슨 root가 그 객체를 살리고 있나"를 보는 것이다.

## 꼬리질문

> Q: GC root는 무엇인가요?
> 핵심: GC가 시작할 때 살아 있다고 보는 참조의 출발점이다.

> Q: retained size가 왜 중요한가요?
> 핵심: 그 객체가 유지시키는 하위 그래프 전체 비용을 보여주기 때문이다.

> Q: 누수와 장기 보관은 어떻게 구분하나요?
> 핵심: 한도, eviction, TTL, 의도된 retention인지 여부를 함께 본다.

## 한 줄 정리

GC root 분석은 heap dump의 핵심이고, retained size와 dominator tree를 읽어야 실제 누수와 의도된 보관을 구분할 수 있다.
