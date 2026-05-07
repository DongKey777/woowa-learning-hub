---
schema_version: 3
title: Java Agent and Instrumentation Basics
concept_id: language/java-agent-instrumentation-basics
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
- java-agent
- instrumentation
- jvm-diagnostics
aliases:
- Java agent instrumentation basics
- javaagent premain agentmain
- ClassFileTransformer bytecode transformation
- Java instrumentation API retransform redefine
- APM tracing agent JVM cost
- 자바 에이전트 계측 기초
symptoms:
- javaagent를 단순 로깅 라이브러리처럼 이해해 class loading, transformer, safepoint 비용이 생기는 이유를 설명하지 못해
- premain과 agentmain의 차이를 몰라 startup instrumentation과 runtime attach의 권한/안정성 경계를 혼동해
- bytecode transformation이 전부 안전하게 재정의 가능하다고 생각해 loaded class, final 제약, classloader 경계를 놓쳐
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- language/class-initialization-ordering
- language/classloader-delegation-edge-cases
- language/safepoint-stop-the-world-diagnostics
next_docs:
- language/jfr-jmc-performance-playbook
- language/classloader-memory-leak-playbook
- language/hidden-classes-lambdametafactory-basics
linked_paths:
- contents/language/java/safepoint-stop-the-world-diagnostics.md
- contents/language/java/jfr-jmc-performance-playbook.md
- contents/language/java/class-initialization-ordering.md
- contents/language/java/jit-warmup-deoptimization.md
- contents/language/java/classloader-memory-leak-playbook.md
- contents/language/java/classloader-delegation-edge-cases.md
- contents/language/java/hidden-classes-lambdametafactory-basics.md
confusable_with:
- language/jfr-jmc-performance-playbook
- language/safepoint-stop-the-world-diagnostics
- language/classloader-memory-leak-playbook
forbidden_neighbors: []
expected_queries:
- Java agent의 premain과 agentmain 차이를 instrumentation 관점에서 설명해줘
- ClassFileTransformer가 bytecode를 바꾸면 JVM 성능과 class loading에 어떤 영향이 있어?
- APM tracing agent를 붙인 뒤 startup이나 latency가 느려지는 원인을 어떻게 봐야 해?
- retransform redefine attach API가 운영에서 위험할 수 있는 이유가 뭐야?
- javaagent와 JFR 같은 built-in tooling을 언제 구분해서 써야 해?
contextual_chunk_prefix: |
  이 문서는 Java agent, Instrumentation API, premain, agentmain, ClassFileTransformer를 JVM diagnostics와 runtime cost 관점에서 설명하는 advanced deep dive다.
  javaagent, bytecode transformation, APM tracing agent, runtime attach, class loading overhead 질문이 본 문서에 매핑된다.
---
# Java Agent and Instrumentation Basics

> 한 줄 요약: Java agent는 class loading 시점에 bytecode를 바꾸거나 관측을 넣는 도구이고, instrumentation은 강력하지만 초기화 순서, 성능, 호환성, safepoint 비용까지 같이 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [Class Initialization Ordering](./class-initialization-ordering.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [ClassLoader Memory Leak Playbook](./classloader-memory-leak-playbook.md)

> retrieval-anchor-keywords: javaagent, instrumentation, premain, agentmain, bytecode transformation, ClassFileTransformer, attach API, JVMTI, retransform, redefine, class loader, startup agent, runtime agent, bootstrap instrumentation

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

Java agent는 JVM 시작 시점이나 실행 중에 붙어서 class bytecode를 관찰하거나 변형할 수 있는 메커니즘이다.  
보통 `premain` 또는 `agentmain` 진입점을 가진다.

`Instrumentation` API는 다음 같은 일을 가능하게 한다.

- 클래스 bytecode transformation
- class redefinition / retransformation
- loaded class 관찰
- object size 조회

### 왜 중요한가

- APM, tracing, profiling 도구가 여기에 기대는 경우가 많다
- 테스트/실험용 관측 코드를 삽입하기 좋다
- 하지만 JVM 동작과 성능에 직접 영향을 준다

## 깊이 들어가기

### 1. premain과 agentmain

- `premain`: JVM 시작 시 agent가 먼저 실행된다
- `agentmain`: 실행 중 attach로 agent를 붙인다

시작 시 주입은 안정적이지만 실행 전 조건이 필요하고, runtime attach는 유연하지만 운영 리스크와 권한 이슈가 생길 수 있다.

### 2. ClassFileTransformer가 하는 일

`ClassFileTransformer`는 class bytecode를 받아 새 바이트 배열을 돌려줄 수 있다.  
이로써 다음 같은 계측이 가능하다.

- 메서드 진입/종료 로깅
- 예외 추적
- metrics 삽입
- trace context 전달

하지만 변환이 복잡할수록 호환성과 디버깅 난이도가 올라간다.

### 3. redefine과 retransform은 다르다

둘 다 이미 로드된 클래스를 다루지만, 허용 범위와 동작이 다를 수 있다.  
실무에서는 "지금 가능한가"보다 "이 변경이 기존 메서드/필드를 깨지 않는가"를 먼저 봐야 한다.

### 4. agent는 safepoint와도 만난다

클래스 변환, stack walking, thread 관찰은 JVM 내부 작업과 엮인다.  
그래서 agent가 늘어나면 STW나 latency spike의 원인 후보가 될 수 있다.

## 실전 시나리오

### 시나리오 1: 운영에서 tracing을 붙이고 싶다

agent는 비즈니스 코드 수정 없이 관측을 넣는 방법이 될 수 있다.  
하지만 transform 비용과 class loading 시점의 영향은 꼭 측정해야 한다.

### 시나리오 2: agent가 들어간 뒤 부팅이 느려졌다

원인 후보:

- 변환 대상 class가 많다
- bootstrap 단계에서 무거운 작업을 한다
- 초기화 순서가 꼬인다
- classloader 경계가 복잡하다

### 시나리오 3: attach는 되는데 일부 클래스만 안 바뀐다

이미 로드된 클래스, final 제약, JVM 제한, 보안 설정 등에 따라 변환 가능 범위가 달라질 수 있다.  
설계 단계에서 "전부 바꿀 수 있다"는 가정은 위험하다.

## 코드로 보기

### 1. 가장 단순한 `premain`

```java
import java.lang.instrument.Instrumentation;

public class DemoAgent {
    public static void premain(String agentArgs, Instrumentation inst) {
        // bootstrap-time setup
    }
}
```

### 2. transformer 등록

```java
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;

public class DemoAgent {
    public static void premain(String agentArgs, Instrumentation inst) {
        ClassFileTransformer transformer = (module, loader, name, classBeingRedefined,
                                           protectionDomain, classfileBuffer) -> classfileBuffer;
        inst.addTransformer(transformer, true);
    }
}
```

### 3. 동작을 바꾸기보다 관측부터 시작

```java
// 처음에는 bytecode를 바꾸기보다
// 클래스 로딩과 메서드 호출을 기록하는 수준에서 시작하는 편이 안전하다.
```

### 4. runtime attach의 감각

```java
// agentmain은 실행 중 프로세스에 붙는 경로다.
// 운영에서는 권한, 안정성, 관측 비용을 먼저 본다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| premain agent | 시작부터 일관되게 적용된다 | 배포/실행 옵션 관리가 필요하다 |
| agentmain attach | 운영 중 붙일 수 있다 | 보안과 호환성 리스크가 있다 |
| transformer | 강력한 계측이 가능하다 | bytecode 복잡도가 높다 |
| JFR / built-in tooling | JVM 친화적이다 | 원하는 세밀도는 부족할 수 있다 |

핵심은 agent를 만능 도구가 아니라 "비용이 있는 강력한 런타임 훅"으로 보는 것이다.

## 꼬리질문

> Q: Java agent는 언제 쓰나요?
> 핵심: 비즈니스 코드 수정 없이 관측, 로깅, 계측, bytecode 변환이 필요할 때 쓴다.

> Q: `premain`과 `agentmain`의 차이는 무엇인가요?
> 핵심: `premain`은 JVM 시작 시, `agentmain`은 실행 중 attach로 동작한다.

> Q: agent가 성능에 영향을 주는 이유는 무엇인가요?
> 핵심: class loading, transformation, safepoint 연관 작업, 추가 관측 비용이 생기기 때문이다.

## 한 줄 정리

Java agent는 강력한 계측 도구이지만, startup과 runtime attach 모두 class loading과 JVM pause 비용을 함께 고려해야 안전하다.
