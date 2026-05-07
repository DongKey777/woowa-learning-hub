---
schema_version: 3
title: Cleaner vs finalize Deprecation
concept_id: language/cleaner-vs-finalize-deprecation
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- resource-cleanup
- finalize-deprecation
- autocloseable
aliases:
- Cleaner vs finalize
- finalize deprecation
- Java Cleaner
- AutoCloseable cleanup
- finalization removal
- phantom reference cleanup
- Cleaner는 즉시 닫기가 아니다
symptoms:
- finalize에 자원 해제 로직을 넣어 GC 타이밍과 finalization 지연에 의존해
- Cleaner가 있으니 close를 호출하지 않아도 된다고 오해하고 native/off-heap 자원 해제를 늦춰
- AutoCloseable과 try-with-resources가 1차 해법이고 Cleaner는 fallback이라는 경계를 놓쳐
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- language/try-with-resources-suppressed-exceptions
next_docs:
- language/direct-buffer-offheap-memory-troubleshooting
- language/phantom-weak-soft-references
- language/classloader-memory-leak-playbook
linked_paths:
- contents/language/java/try-with-resources-suppressed-exceptions.md
- contents/language/java/phantom-weak-soft-references.md
- contents/language/java/direct-buffer-offheap-memory-troubleshooting.md
- contents/language/java/classloader-memory-leak-playbook.md
confusable_with:
- language/try-with-resources-suppressed-exceptions
- language/phantom-weak-soft-references
- language/direct-buffer-offheap-memory-troubleshooting
forbidden_neighbors: []
expected_queries:
- Java finalize가 deprecated 된 이유와 Cleaner가 바꾼 점을 설명해줘
- Cleaner가 있어도 파일 socket native memory를 명시적으로 close해야 하는 이유가 뭐야?
- AutoCloseable try-with-resources와 Cleaner fallback의 역할을 어떻게 나눠?
- finalization은 왜 실행 시점이 예측 불가능하고 성능 문제가 있어?
- off-heap resource cleanup에서 Cleaner를 안전장치로만 봐야 하는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 Java finalize deprecation과 Cleaner를 AutoCloseable, try-with-resources, GC timing, reference processing, off-heap resource cleanup 관점으로 설명하는 advanced deep dive다.
  finalize deprecated, Cleaner, AutoCloseable, explicit close, native memory cleanup, finalization 질문이 본 문서에 매핑된다.
---
# Cleaner vs `finalize()` Deprecation

> 한 줄 요약: `finalize()`는 예측 불가능성과 성능 문제 때문에 deprecated 되었고, Cleaner는 더 나은 대안이지만 여전히 즉시성 보장이 없어서 자원 관리는 기본적으로 명시적으로 닫는 것이 맞다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Try-With-Resources and Suppressed Exceptions](./try-with-resources-suppressed-exceptions.md)
> - [Phantom, Weak, and Soft References](./phantom-weak-soft-references.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)

> retrieval-anchor-keywords: Cleaner, finalize, finalization, deprecation, reachability, cleanup, post-mortem, resource release, AutoCloseable, GC timing, reference processing

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

`finalize()`는 객체가 GC되기 전에 마지막 정리를 시도하는 오래된 메커니즘이다.  
하지만 언제 실행될지 보장하기 어렵고, 성능과 안정성 문제가 많다.

Cleaner는 더 현대적인 대안이다.  
그러나 Cleaner도 "언젠가 정리된다"에 가깝지 "즉시 닫힌다"는 뜻은 아니다.

## 깊이 들어가기

### 1. finalize가 문제가 된 이유

finalization은 다음 문제를 만들었다.

- 실행 시점이 예측 불가하다
- 종료 시점에 객체를 오래 붙잡을 수 있다
- 의존성 때문에 꼬일 수 있다
- 예외나 재진입이 복잡해질 수 있다

그래서 자원 관리 도구로 쓰기엔 너무 불안정하다.

### 2. Cleaner는 무엇을 바꿨나

Cleaner는 객체가 unreachable 된 뒤 cleanup action을 등록하는 방식이다.  
즉 finalize보다 제어가 명시적이다.

하지만 여전히 중요한 제한이 있다.

- GC와 reference processing 타이밍에 의존한다
- cleanup이 즉시 실행된다고 기대하면 안 된다
- 핵심 자원 해제는 여전히 직접 닫는 것이 우선이다

### 3. AutoCloseable이 여전히 기본 해법이다

파일, socket, DB connection, buffer 같은 자원은 명시적으로 닫는 것이 맞다.  
Cleaner는 실패 시 안전장치에 가깝다.

### 4. off-heap 자원에서 특히 중요하다

native memory, direct buffer, file mapping은 GC만 믿으면 위험하다.  
따라서 cleanup path를 명확히 설계해야 한다.

## 실전 시나리오

### 시나리오 1: finalize에 cleanup 로직이 있다

이제는 제거하거나 Cleaner/AutoCloseable로 옮겨야 한다.  
finalize에 의존하면 release 타이밍이 흔들린다.

### 시나리오 2: Cleaner가 있으니 닫지 않아도 된다고 생각한다

이건 위험하다.  
Cleaner는 보조 안전장치이지 주 제어 수단이 아니다.

### 시나리오 3: 네이티브 자원이 새고 있다

try-with-resources와 explicit close가 1차 해법이고, Cleaner는 누락 대응용으로 두는 것이 좋다.

## 코드로 보기

### 1. AutoCloseable 중심

```java
public final class ManagedResource implements AutoCloseable {
    @Override
    public void close() {
        // explicit cleanup
    }
}
```

### 2. Cleaner 등록 감각

```java
import java.lang.ref.Cleaner;

public final class NativeHolder {
    private static final Cleaner CLEANER = Cleaner.create();
    private final Cleaner.Cleanable cleanable;

    public NativeHolder() {
        this.cleanable = CLEANER.register(this, this::cleanup);
    }

    private void cleanup() {
        // fallback cleanup
    }
}
```

### 3. finalize는 피해야 한다

```java
// finalize() 기반 cleanup은 deprecated 경로로 보는 편이 안전하다.
```

### 4. 실무 우선순위

```java
// 1) try-with-resources
// 2) explicit close
// 3) Cleaner fallback
// 4) finalize는 회피
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `finalize()` | 오래된 코드와 호환될 수 있다 | 비예측적이고 비권장이다 |
| Cleaner | finalize보다 명시적이다 | 즉시성 보장이 없다 |
| AutoCloseable | 가장 예측 가능하다 | 호출 책임이 있다 |
| try-with-resources | cleanup과 예외 처리가 안정적이다 | 자원 타입을 잘 설계해야 한다 |

핵심은 GC 기반 cleanup은 "보조"이고, 자원 관리는 명시적 lifecycle이 우선이라는 점이다.

## 꼬리질문

> Q: finalize가 왜 deprecated 되었나요?
> 핵심: 실행 시점이 예측 불가능하고 성능/안정성 문제가 컸기 때문이다.

> Q: Cleaner는 finalize의 완전한 대체인가요?
> 핵심: 더 나은 대안이지만, cleanup 타이밍이 여전히 비동기적이라 완전한 대체는 아니다.

> Q: 자원 관리는 어떻게 하는 게 좋나요?
> 핵심: try-with-resources와 explicit close를 우선하고, Cleaner는 안전망으로만 둔다.

## 한 줄 정리

`finalize()`는 버려야 할 오래된 cleanup 메커니즘이고, Cleaner는 보조 안전장치일 뿐이며, 자원 관리는 항상 명시적으로 닫는 것이 기본이다.
