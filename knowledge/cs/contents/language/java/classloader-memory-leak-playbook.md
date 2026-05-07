---
schema_version: 3
title: ClassLoader Memory Leak Playbook
concept_id: language/classloader-memory-leak-playbook
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- classloader-leak
- memory-leak
- redeploy
aliases:
- ClassLoader memory leak
- redeploy memory leak
- webapp classloader retention
- ThreadLocal classloader leak
- metaspace leak
- VM.classloader_stats
- old ClassLoader not collected
symptoms:
- redeploy 후 메모리가 줄지 않고 old ClassLoader가 살아 있어 heap과 metaspace가 함께 늘어나
- ThreadLocal, background thread, static cache, JDBC driver가 webapp classloader를 붙잡는 경로를 끊지 못해
- heap leak만 보고 ClassLoader 자체가 GC되지 않는 누수 유형을 놓쳐
intents:
- troubleshooting
- deep_dive
prerequisites:
- language/classloader-delegation-edge-cases
next_docs:
- language/jcmd-diagnostic-command-cheatsheet
- language/oom-heap-dump-playbook
- language/threadlocal-leaks-context-propagation
linked_paths:
- contents/language/java/jvm-gc-jmm-overview.md
- contents/language/java/reflection-cost-and-alternatives.md
- contents/language/java/oom-heap-dump-playbook.md
- contents/language/java/classloader-delegation-edge-cases.md
- contents/language/java/jcmd-diagnostic-command-cheatsheet.md
confusable_with:
- language/classloader-delegation-edge-cases
- language/oom-heap-dump-playbook
- language/jvm-gc-jmm-overview
forbidden_neighbors: []
expected_queries:
- Java redeploy 후 old ClassLoader가 살아남아 memory leak이 나는 원인을 어떻게 찾지?
- ThreadLocal이 webapp classloader leak을 만드는 이유와 remove 패턴을 설명해줘
- jcmd VM.classloader_stats와 GC.class_histogram으로 classloader leak을 어떻게 본다?
- heap leak과 ClassLoader leak은 어떻게 다르고 metaspace leak과 어떻게 연결돼?
- static cache background thread JDBC driver가 classloader를 붙잡는 경로를 알려줘
contextual_chunk_prefix: |
  이 문서는 Java ClassLoader memory leak을 redeploy, ThreadLocal, static cache, background thread, JDBC driver, VM.classloader_stats, heap dump 관점으로 진단하는 advanced playbook이다.
  ClassLoader leak, redeploy memory leak, old ClassLoader not collected, metaspace leak, ThreadLocal cleanup 질문이 본 문서에 매핑된다.
---
# ClassLoader Memory Leak Playbook

> 한 줄 요약: Java 메모리 누수는 heap에만 생기지 않고, ClassLoader를 붙잡으면 redeploy 후에도 살아남는다.

**난이도: 🔴 Expert**

> 관련 문서: [JVM, GC, JMM](./jvm-gc-jmm-overview.md), [Reflection 비용과 대안](./reflection-cost-and-alternatives.md), [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)

retrieval-anchor-keywords: ClassLoader leak, classloader memory leak, redeploy memory leak, ThreadLocal classloader leak, metaspace leak, webapp classloader retention, VM.classloader_stats, old ClassLoader not collected, dynamic proxy leak, application redeploy heap leak

## 핵심 개념

ClassLoader leak은 클래스 자체가 아니라, 그 ClassLoader가 회수되지 못해서 생기는 누수다.

왜 중요한가:

- application redeploy 후 메모리가 줄지 않는다
- JSP, dynamic proxy, thread context class loader가 누수를 만들 수 있다
- heap dump에서 old gen이 줄지 않는 원인이 된다

## 깊이 들어가기

### 1. 왜 ClassLoader가 누수되는가

ClassLoader는 자신이 로드한 class와 static reference가 모두 끊겨야 회수될 수 있다.

문제 패턴:

- static cache가 ClassLoader를 참조
- ThreadLocal이 정리되지 않음
- background thread가 webapp class를 붙잡음
- JDBC driver / logging handler가 정리되지 않음

### 2. redeploy가 위험한 이유

새 버전을 올려도 이전 ClassLoader가 남아 있으면:

- old class 메타데이터가 남음
- heap object graph가 끊기지 않음
- PermGen/Metaspace 압박이 생김

## 실전 시나리오

### 시나리오 1: 배포할수록 메모리가 늘어난다

old ClassLoader가 살아 있으면 GC가 다 회수하지 못한다.

진단:

```bash
jcmd <pid> GC.class_histogram
jcmd <pid> VM.classloader_stats
```

### 시나리오 2: 스레드 풀에서 ThreadLocal을 쓰고 누수된다

thread pool은 thread가 재사용되므로, ThreadLocal 정리가 필수다.

## 코드로 보기

```java
ThreadLocal<MyContext> context = new ThreadLocal<>();

try {
    context.set(value);
    // work
} finally {
    context.remove();
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| ThreadLocal | 빠르고 편함 | 누수 위험 | 요청 범위 컨텍스트 |
| Static cache | 접근 쉬움 | ClassLoader leak 위험 | 매우 신중하게만 |
| Explicit context passing | 안전 | 코드가 길어짐 | 장기 운영 코드 |

## 꼬리질문

> Q: Java heap leak과 ClassLoader leak의 차이는 무엇인가?
> 의도: 메모리 누수 유형 구분 여부 확인
> 핵심: heap 객체뿐 아니라 로더 자체가 남을 수 있다.

> Q: ThreadLocal이 왜 webapp에서 위험한가?
> 의도: thread reuse와 누수 이해 여부 확인
> 핵심: thread pool 재사용 때문에 값이 남는다.

## 한 줄 정리

ClassLoader leak은 "클래스가 안 지워진다"가 아니라 "로더가 회수되지 않는다"는 문제이고, redeploy 메모리 누수의 대표 원인이다.
