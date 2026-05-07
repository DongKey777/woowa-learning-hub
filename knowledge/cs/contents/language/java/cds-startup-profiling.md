---
schema_version: 3
title: CDS Startup Profiling
concept_id: language/cds-startup-profiling
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- jvm-startup
- class-data-sharing
- profiling
aliases:
- CDS startup profiling
- AppCDS cold start profiling
- Java class loading startup
- shared archive reuse
- JFR startup profiling
- JVM cold start
symptoms:
- CDS나 AppCDS를 적용했다는 사실만 보고 archive가 실제로 재사용됐는지 측정하지 않아
- class loading, static initialization, JIT warmup, first request latency를 하나의 startup 문제로 섞어 진단해
- cold start 개선과 warmup 개선을 구분하지 못해 CDS 효과를 과대평가해
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- language/class-data-sharing-appcds
next_docs:
- language/jfr-jmc-performance-playbook
- language/jit-warmup-deoptimization
- language/classloader-memory-leak-playbook
linked_paths:
- contents/language/java/class-data-sharing-appcds.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/jit-warmup-deoptimization.md
- contents/language/java/classloader-memory-leak-playbook.md
confusable_with:
- language/class-data-sharing-appcds
- language/jit-warmup-deoptimization
- language/jfr-jmc-performance-playbook
forbidden_neighbors: []
expected_queries:
- Java CDS AppCDS startup profiling에서 archive reuse 여부를 왜 확인해야 해?
- CDS가 class loading startup은 줄여도 첫 요청 warmup은 그대로 느릴 수 있는 이유가 뭐야?
- JFR로 JVM cold start에서 class loading JIT warmup을 어떻게 분리해?
- AppCDS 적용 효과를 startup latency와 RSS로 측정하는 방법을 알려줘
- Java startup profiling에서 cold start와 first request latency를 구분해줘
contextual_chunk_prefix: |
  이 문서는 JVM CDS/AppCDS startup profiling을 class loading, shared archive reuse, cold start, JIT warmup, JFR measurement 관점으로 설명하는 advanced deep dive다.
  CDS profiling, AppCDS, startup latency, class loading time, archive reuse, first request latency 질문이 본 문서에 매핑된다.
---
# CDS Startup Profiling

> 한 줄 요약: CDS/AppCDS는 startup profiling에서 class loading과 metadata 비용을 줄이는 수단이며, 진짜 개선 효과를 보려면 cold start와 archive 재사용 여부를 같이 측정해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Class Data Sharing and AppCDS](./class-data-sharing-appcds.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)

> retrieval-anchor-keywords: CDS profiling, startup profiling, cold start, AppCDS, class loading, shared archive, startup latency, footprint, archive reuse, class loading time

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

startup profiling은 "왜 처음이 느린가"를 보는 일이다.  
CDS/AppCDS는 그중 class loading 비용을 줄이는 대표적 도구다.

핵심은 다음 질문들이다.

- 어떤 class가 처음에 많이 로딩되는가
- 아카이브가 실제로 재사용되는가
- JIT warmup과 class loading을 분리해서 보고 있는가

## 깊이 들어가기

### 1. startup 문제는 여러 층이 섞인다

startup이 느린 이유는 class loading뿐만이 아니다.

- class loading
- verification
- static initialization
- JIT warmup
- first request path

CDS는 이 중 class loading에 주로 영향을 준다.

### 2. archive reuse를 확인해야 한다

AppCDS를 써도 아카이브가 실제로 reuse되지 않으면 효과가 없다.  
그래서 startup profiling은 archive 생성 여부와 런타임 옵션을 같이 봐야 한다.

### 3. JFR로 startup phase를 쪼개 본다

JFR은 class loading, compilation, allocation, GC, thread state를 시간축으로 볼 수 있다.  
startup profiling과 잘 맞는다.

### 4. warmup과 startup은 다르다

CDS가 좋아져도 warmup이 길면 첫 요청은 여전히 느릴 수 있다.  
둘을 혼동하면 진단이 틀어진다.

## 실전 시나리오

### 시나리오 1: cold start만 느리다

AppCDS를 적용하고 startup time과 RSS 변화를 함께 본다.  
class loading에서 줄어든 시간이 실제 사용자 경험 개선으로 이어지는지 확인한다.

### 시나리오 2: startup은 빨라졌지만 첫 요청이 느리다

이건 JIT warmup이나 lazy init 문제일 수 있다.  
CDS로 모든 startup 문제를 해결하려 하면 안 된다.

### 시나리오 3: startup profiling 결과가 들쭉날쭉하다

filesystem cache, container pressure, JVM flags, classpath size가 원인일 수 있다.  
반복 측정이 필요하다.

## 코드로 보기

### 1. startup 측정 흐름 감각

```bash
java -Xshare:on -XX:SharedArchiveFile=app-cds.jsa -jar app.jar
```

### 2. class loading과 JFR 같이 보기

```bash
java -XX:StartFlightRecording=name=startup,settings=profile,filename=/tmp/startup.jfr -jar app.jar
```

### 3. 측정 포인트

```java
// startup latency
// first request latency
// class loading count
// archive reuse 여부
```

### 4. 운영 체크

```java
// AppCDS는 "적용했다"보다 "실제로 재사용됐다"가 중요하다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| CDS/AppCDS | class loading startup을 줄인다 | archive 관리가 필요하다 |
| plain startup | 단순하다 | cold start가 느릴 수 있다 |
| JFR startup profiling | 원인 분리가 쉽다 | 측정 습관이 필요하다 |
| lazy init | 초기 비용을 늦춘다 | 첫 요청이 느려질 수 있다 |

핵심은 CDS를 startup profiling의 한 축으로 보고, class loading과 warmup을 분리해서 측정하는 것이다.

## 꼬리질문

> Q: CDS는 어떤 비용을 줄이나요?
> 핵심: class loading과 metadata 생성 비용의 일부를 줄인다.

> Q: startup profiling에서 가장 중요한 것은 무엇인가요?
> 핵심: class loading, initialization, JIT warmup을 분리해서 보는 것이다.

> Q: AppCDS가 있는데도 첫 요청이 느릴 수 있나요?
> 핵심: 그렇다. CDS는 warmup과 downstream I/O 병목을 해결하지 못한다.

## 한 줄 정리

CDS/AppCDS는 startup profiling에서 class loading 비용을 줄이는 수단이고, 효과는 archive 재사용과 warmup 분리를 같이 봐야 제대로 판단할 수 있다.
