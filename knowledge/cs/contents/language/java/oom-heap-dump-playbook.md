# OOM Heap Dump Playbook

> 한 줄 요약: OutOfMemoryError는 일단 덤프를 남기고, heap인지 native인지부터 구분한 뒤, 재현 가능한 증거를 모아야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [G1 GC vs ZGC](./g1-vs-zgc.md)
> - [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [시스템 콜과 User-Kernel Boundary](../../operating-system/syscall-user-kernel-boundary.md)

<details>
<summary>Table of Contents</summary>

- [왜 필요한가](#왜-필요한가)
- [OOM 유형 구분](#oom-유형-구분)
- [먼저 할 일](#먼저-할-일)
- [덤프 수집](#덤프-수집)
- [분석 순서](#분석-순서)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

retrieval-anchor-keywords: OutOfMemoryError playbook, heap dump analysis, Java heap space, GC overhead limit exceeded, direct buffer memory, native thread exhaustion, jcmd GC.heap_dump, class histogram, dominator tree, heap dump triage

## 왜 필요한가

OOM은 "메모리가 없다"로 끝나지 않는다.  
heap이 찬 것인지, metaspace가 찬 것인지, direct memory가 고갈된 것인지, native thread를 더 만들 수 없는 것인지부터 구분해야 한다.

heap dump는 그중 **heap 문제를 추적하는 핵심 증거**다.  
증거 없이 코드만 고치면 같은 문제가 다시 난다.

## OOM 유형 구분

| 증상 | 의미 | heap dump로 바로 보이나 |
|---|---|---|
| `Java heap space` | heap 객체가 너무 많다 | 예 |
| `GC overhead limit exceeded` | GC가 너무 자주 돈다 | 예 |
| `Metaspace` | 클래스 메타데이터가 많다 | 일부 |
| `Direct buffer memory` | off-heap direct buffer 고갈 | 아니오 |
| `unable to create new native thread` | OS 스레드 생성 실패 | 아니오 |

즉 heap dump는 만능이 아니다.  
하지만 heap OOM은 거의 항상 먼저 덤프를 남겨야 한다.

## 먼저 할 일

1. 증상을 확인한다
2. OOM 유형을 본다
3. 프로세스를 죽이기 전에 덤프 옵션이 켜져 있는지 본다
4. 가능하면 live 상태에서 histogram을 먼저 수집한다

### JVM 옵션

```bash
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/dumps
-XX:+ExitOnOutOfMemoryError
```

운영에서 덤프 경로 디스크 용량도 같이 봐야 한다.

## 덤프 수집

### 1. class histogram 먼저 보기

```bash
jcmd <pid> GC.class_histogram
```

무엇이 많이 쌓였는지 빠르게 보기 좋다.

### 2. heap dump 남기기

```bash
jcmd <pid> GC.heap_dump /var/dumps/heap.hprof
```

대안:

```bash
jmap -dump:format=b,file=/var/dumps/heap.hprof <pid>
```

### 3. 실행 중 상태 같이 남기기

```bash
jcmd <pid> Thread.print
jcmd <pid> VM.flags
jcmd <pid> GC.heap_info
```

### 4. JFR 같이 남기기

```bash
jcmd <pid> JFR.start name=oom settings=profile duration=120s filename=/var/dumps/oom.jfr
```

heap dump만 보면 원인 타임라인이 부족할 수 있다.  
JFR은 직전 행동을 함께 본다.

## 분석 순서

### 1. dominator tree부터 본다

누가 메모리를 지배하는지 본다.  
크게 잡아먹는 객체가 무엇인지 확인해야 한다.

### 2. 반복되는 객체 타입을 본다

- `byte[]`
- `char[]`
- `HashMap$Node`
- `ArrayList`
- DTO/Entity 누적

### 3. 강한 참조 경로를 찾는다

흔한 원인:

- static cache
- 무제한 Map
- ThreadLocal 누수
- listener 등록 해제 누락
- 큐 적체

### 4. 재현 가능한 입력을 만든다

덤프만 보고 끝내지 말고, 어떤 요청/배치가 메모리를 키웠는지 추적한다.

## 실전 시나리오

### 시나리오 1: 캐시가 무한히 커진다

```java
private static final Map<String, byte[]> CACHE = new ConcurrentHashMap<>();
```

이런 코드는 eviction이 없으면 결국 메모리를 잡아먹는다.  
heap dump에서 `ConcurrentHashMap`과 `byte[]`가 지배적이면 의심한다.

### 시나리오 2: ThreadLocal을 지우지 않는다

Virtual Thread든 Platform Thread든, ThreadLocal을 관리하지 않으면 누수가 생길 수 있다.

### 시나리오 3: 큐가 소비자를 못 따라간다

producer가 빠르고 consumer가 느리면, 메시지/작업 객체가 계속 적체된다.  
이 경우 heap dump에 대기 객체가 쌓인다.

### 시나리오 4: reflection 기반 프레임워크가 기동 중 메모리를 크게 쓴다

리플렉션/클래스 스캔 자체가 문제라기보다, 스캔한 결과를 무제한 캐싱하는 구조가 더 위험하다.  
이 문맥은 [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)과도 연결된다.

## 코드로 보기

### 누수 패턴 예시

```java
public final class RequestCache {
    private static final Map<String, String> CACHE = new ConcurrentHashMap<>();

    public String get(String key) {
        return CACHE.computeIfAbsent(key, this::load);
    }
}
```

키가 무한히 늘면 cache는 사실상 leak이 된다.

### 덤프 옵션과 함께 실행

```bash
java \
  -Xms2g -Xmx2g \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/var/dumps \
  -XX:+ExitOnOutOfMemoryError \
  -jar app.jar
```

### 현장 점검 커맨드

```bash
jcmd <pid> GC.heap_info
jcmd <pid> GC.class_histogram
jcmd <pid> VM.native_memory summary
```

`VM.native_memory summary`는 heap이 아닌 native 고갈도 구분하는 데 도움이 된다.

## 트레이드오프

| 방법 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| heap dump | 원인 분석에 가장 강하다 | 파일이 크고 수집이 무겁다 | heap OOM |
| class histogram | 빠르고 가볍다 | 참조 경로가 부족하다 | 첫 진단 |
| JFR | 타임라인이 보인다 | 사전 설정이 필요하다 | 원인 추적 |
| live attach | 빠르게 확인 가능 | 이미 느리거나 불안정할 수 있다 | 운영 초동 대응 |

핵심은 **histogram으로 방향을 잡고, dump로 증거를 확정하고, JFR로 타임라인을 보강**하는 것이다.

## 꼬리질문

> Q: heap dump가 도움이 안 되는 OOM은 무엇인가요?
> 의도: heap과 native OOM 구분 여부 확인
> 핵심: direct buffer, metaspace, native thread 고갈은 heap dump만으로 부족할 수 있다

> Q: OOM 직전에 가장 먼저 수집할 정보는 무엇인가요?
> 의도: 재현/증거 수집 습관 확인
> 핵심: histogram, dump, thread dump, flags, JFR

> Q: 왜 heap dump를 남기고 분석해야 하나요?
> 의도: 추측이 아니라 증거 기반 디버깅을 하는지 확인
> 핵심: 강한 참조 경로와 dominator를 봐야 원인을 특정할 수 있다

## 한 줄 정리

OOM 대응은 heap/native 구분부터 시작하고, heap 문제라면 histogram -> heap dump -> JFR 순서로 증거를 남겨서 원인을 좁혀야 한다.
