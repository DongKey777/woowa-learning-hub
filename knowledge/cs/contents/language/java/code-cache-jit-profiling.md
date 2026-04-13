# Code Cache and JIT Profiling

> 한 줄 요약: code cache는 JIT가 생성한 machine code를 담는 영역이고, 코드 캐시 압박이나 재컴파일이 잦으면 warmup 이후에도 latency와 throughput이 흔들릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [Method Inlining Heuristics and Deoptimization Triggers](./method-inlining-heuristics-deopt-triggers.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [Jcmd Diagnostic Command Cheat Sheet](./jcmd-diagnostic-command-cheatsheet.md)

> retrieval-anchor-keywords: code cache, JIT profiling, compilation, recompilation, nmethod, code cache pressure, C1, C2, tiered compilation, compiler queue, inline cache, deopt, hot methods

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

HotSpot은 hot method를 JIT로 컴파일해 machine code로 바꾼다.  
그 코드가 들어가는 공간이 code cache다.

code cache는 단순 저장소가 아니라 JIT 성능과 밀접하게 연결된다.

- 컴파일이 많으면 커진다
- 코드가 너무 많으면 압박이 생긴다
- 재컴파일과 deoptimization이 반복되면 흔들림이 생긴다

## 깊이 들어가기

### 1. code cache에 뭐가 들어가나

JIT가 만든 nmethod와 관련 메타데이터가 들어간다고 보면 된다.  
즉 실행 중 생성된 machine code의 보관소다.

### 2. code cache pressure가 왜 문제인가

code cache가 압박을 받으면 다음이 함께 일어날 수 있다.

- 컴파일 지연
- 재컴파일 증가
- deoptimization 후 복구 지연
- hot path 안정성 저하

### 3. tiered compilation과 함께 봐야 한다

HotSpot은 보통 여러 tier를 거쳐 컴파일한다.

- interpreter
- C1
- C2

이 경로가 안정화되기 전에는 프로파일이 흔들릴 수 있다.

### 4. inlining과 code cache는 연결된다

Inlining이 많아지면 성능은 좋아질 수 있지만 code size가 커져 cache pressure가 늘 수 있다.  
그래서 [Method Inlining Heuristics and Deoptimization Triggers](./method-inlining-heuristics-deopt-triggers.md)와 같이 봐야 한다.

### 5. JFR과 jcmd가 유용하다

JFR은 컴파일 이벤트와 latency spike를 같이 볼 수 있고, `jcmd`는 code cache 상태를 빠르게 확인할 수 있다.  
관련해서 [JFR Event Interpretation](./jfr-event-interpretation.md)와 [Jcmd Diagnostic Command Cheat Sheet](./jcmd-diagnostic-command-cheatsheet.md)을 참고하면 좋다.

## 실전 시나리오

### 시나리오 1: warmup은 끝난 것 같은데 여전히 느리다

재컴파일, deopt, code cache pressure를 의심한다.  
단순히 "JIT가 아직 덜 됐다"로 끝내면 안 된다.

### 시나리오 2: 컴파일 로그가 많다

hot method가 자주 바뀌거나 profile이 흔들릴 수 있다.  
call target instability와 code cache 성장도 함께 본다.

### 시나리오 3: 배포 후만 이상하다

startup phase에서 code cache가 안정화되기 전에 traffic이 몰렸을 수 있다.  
JFR로 startup과 steady state를 구분해서 보자.

## 코드로 보기

### 1. 컴파일 로그 감각

```bash
java -XX:+UnlockDiagnosticVMOptions -XX:+PrintCompilation -XX:+PrintInlining -jar app.jar
```

### 2. code cache 확인

```bash
jcmd <pid> Compiler.codecache
```

### 3. JFR 이벤트 확인

```bash
jcmd <pid> JFR.start name=jit settings=profile duration=60s filename=/tmp/jit.jfr
```

### 4. hot path 관찰 감각

```java
// hot method가 자주 바뀌면 재컴파일과 code cache 압박이 함께 나타날 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| aggressive compilation | steady-state 성능이 좋다 | code cache와 compile 비용이 늘 수 있다 |
| conservative compilation | 안정적이다 | peak 성능을 놓칠 수 있다 |
| inlining 확대 | call overhead를 줄인다 | code size가 커질 수 있다 |
| profile 기반 최적화 | 실제 패턴에 맞춘다 | profile이 흔들리면 재컴파일이 늘 수 있다 |

핵심은 code cache를 JIT 결과를 담는 저장소가 아니라 runtime performance stability의 핵심 자원으로 보는 것이다.

## 꼬리질문

> Q: code cache는 왜 중요한가요?
> 핵심: JIT가 만든 machine code가 들어가고, 압박이 생기면 성능이 흔들릴 수 있기 때문이다.

> Q: inlining과 code cache는 어떤 관계인가요?
> 핵심: inlining이 많아지면 code size가 커져 cache pressure를 높일 수 있다.

> Q: 어떻게 진단하나요?
> 핵심: `PrintCompilation`, `PrintInlining`, `Compiler.codecache`, JFR을 같이 본다.

## 한 줄 정리

code cache는 JIT 성능의 결과물이자 제약 조건이므로, warmup 이후에도 재컴파일과 압박 징후를 함께 봐야 한다.
