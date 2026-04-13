# `jcmd` Diagnostic Command Cheat Sheet

> 한 줄 요약: `jcmd`는 실행 중인 JVM에 진단 명령을 보내는 범용 도구이고, thread, GC, heap, native memory, JFR, classloader, code cache를 한 곳에서 다룰 수 있는 운영용 칼이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)

> retrieval-anchor-keywords: jcmd, GC.class_histogram, Thread.print, VM.flags, VM.native_memory, GC.heap_info, GC.heap_dump, JFR.start, JFR.check, JFR.stop, Compiler.codecache, VM.classloader_stats, diagnostic command

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

`jcmd`는 살아 있는 JVM에 diagnostic command를 실행한다.  
즉 "로그만 보는 도구"가 아니라 JVM 내부 상태를 직접 조회하는 운영 도구다.

자주 쓰는 명령:

- `Thread.print`
- `GC.class_histogram`
- `GC.heap_info`
- `GC.heap_dump`
- `VM.flags`
- `VM.native_memory`
- `VM.classloader_stats`
- `Compiler.codecache`
- `JFR.start` / `JFR.check` / `JFR.stop`

## 깊이 들어가기

### 1. Thread.print는 thread dump의 기본형이다

blocked thread와 lock owner를 보기 좋다.  
thread dump 해석은 [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)와 같이 보면 좋다.

### 2. GC.class_histogram은 살아 있는 객체 감시용이다

heap dump까지 가지 않고도 클래스별 힙 분포를 빠르게 볼 수 있다.  
누수가 의심될 때 첫 관찰 도구로 유용하다.

### 3. VM.native_memory는 heap 밖을 본다

direct buffer, thread stack, code cache, metaspace 같은 native memory를 볼 때 유용하다.  
heap 문제와 native 문제를 분리하는 데 좋다.

### 4. JFR 명령은 운영 친화적이다

JFR은 JVM 증상을 시간축으로 남기게 해 주고, `jcmd`로 시작/중지/체크를 제어할 수 있다.

### 5. classloader와 code cache도 볼 수 있다

배포 후 메모리나 startup이 이상하면 `VM.classloader_stats`와 `Compiler.codecache`가 힌트가 된다.

## 실전 시나리오

### 시나리오 1: 서비스가 느려졌는데 어디서 시작할지 모르겠다

`Thread.print`, `GC.heap_info`, `VM.flags`, `JFR.start`를 먼저 본다.  
빠르게 상태를 좁힐 수 있다.

### 시나리오 2: heap은 멀쩡한데 RSS가 오른다

`VM.native_memory`와 thread 수, code cache, class metadata를 본다.

### 시나리오 3: classloader leak이 의심된다

`VM.classloader_stats`와 `GC.class_histogram`을 함께 본다.

## 코드로 보기

### 1. 기본 사용

```bash
jcmd <pid> Thread.print
jcmd <pid> GC.class_histogram
jcmd <pid> VM.flags
```

### 2. native memory 확인

```bash
jcmd <pid> VM.native_memory summary
jcmd <pid> VM.native_memory detail
```

### 3. JFR 제어

```bash
jcmd <pid> JFR.start name=profile settings=profile duration=60s filename=/tmp/app.jfr
jcmd <pid> JFR.check
jcmd <pid> JFR.stop name=profile
```

### 4. heap dump / classloader 통계

```bash
jcmd <pid> GC.heap_dump /tmp/heap.hprof
jcmd <pid> VM.classloader_stats
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `jcmd` | JVM 내부를 직접 본다 | 명령을 알아야 한다 |
| GUI tool | 읽기 쉽다 | 원격/자동화가 약할 수 있다 |
| heap dump | 강력한 정밀 분석 가능 | 무겁고 늦다 |
| JFR | 시간축 관찰이 좋다 | 명령과 해석이 필요하다 |

핵심은 `jcmd`를 "명령어 모음"이 아니라 "JVM 운영 기본 인터페이스"로 보는 것이다.

## 꼬리질문

> Q: `jcmd`로 가장 먼저 볼 것은 무엇인가요?
> 핵심: 상황에 따라 다르지만 보통 `Thread.print`, `GC.class_histogram`, `VM.flags`, `VM.native_memory`부터 본다.

> Q: heap이 아닌 문제도 `jcmd`로 볼 수 있나요?
> 핵심: 그렇다. native memory, code cache, classloader, JFR까지 볼 수 있다.

> Q: `jcmd`와 JFR은 어떤 관계인가요?
> 핵심: `jcmd`는 제어와 즉시 진단, JFR은 시간축 기록에 강하다.

## 한 줄 정리

`jcmd`는 JVM 운영 중 상태를 직접 조회하는 범용 진단 도구이고, thread, heap, native memory, classloader, JFR을 한 번에 연결해 볼 수 있다.
