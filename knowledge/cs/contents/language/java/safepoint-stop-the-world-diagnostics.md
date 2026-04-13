# Safepoint and Stop-the-World Diagnostics

> 한 줄 요약: safepoint는 JVM이 전 스레드를 안전하게 멈추는 지점이고, stop-the-world(STW) 증상은 GC뿐 아니라 deoptimization, class unloading, JVMTI, thread dump 같은 여러 원인에서 나타난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JFR and JMC Performance Playbook](./jfr-jmc-performance-playbook.md)
> - [JIT Warmup and Deoptimization](./jit-warmup-deoptimization.md)
> - [G1 GC vs ZGC](./g1-vs-zgc.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)

> retrieval-anchor-keywords: safepoint, stop-the-world, STW, GC pause, deoptimization, class unloading, JVMTI, thread dump, `-Xlog:safepoint`, JFR, latency spike, safepoint poll, native call

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

JVM에서 safepoint는 "지금 멈춰도 상태가 안전한 지점"이다.  
GC만을 위한 장치처럼 보이지만 실제로는 더 넓다.

- GC
- deoptimization
- class unloading
- thread dump
- JVMTI 기반 작업
- code cache / VM 내부 작업

STW는 그 결과로 보이는 멈춤 증상이다.  
즉, safepoint는 메커니즘이고 STW는 관찰 결과다.

### 왜 이 구분이 중요한가

운영에서는 "GC가 없는데도 멈췄다"는 상황이 자주 나온다.  
이때 safepoint와 STW를 분리해서 보면 원인 후보가 훨씬 빨리 줄어든다.

## 깊이 들어가기

### 1. safepoint와 STW는 같은 말이 아니다

safepoint는 JVM이 모든 Java thread를 안전하게 멈추거나 관찰할 수 있는 지점이다.  
STW는 그 지점에 도달하거나 그 지점에서 수행되는 작업 때문에 서비스가 멈춘 것처럼 보이는 현상이다.

그래서 다음을 같이 봐야 한다.

- "멈추기 전까지" 얼마나 기다렸는가
- "멈춘 뒤" JVM이 무엇을 했는가
- 어떤 thread가 safepoint 진입을 늦췄는가

### 2. pause의 원인은 GC만이 아니다

대표 원인:

- young/old/full GC
- class unloading
- deoptimization
- biased locking 관련 작업의 역사적 영향
- thread dump 생성
- agent/JVMTI 훅
- 긴 native call 또는 JNI 구간

특히 native 구간은 중요하다.  
Java 코드 안에서는 safepoint poll이 들어가지만, native에 오래 머무르면 JVM이 전체 pause를 밀어낼 수 있다.

### 3. long-running loop도 체크가 필요하다

HotSpot은 일반적으로 루프와 메서드 경계에 safepoint poll을 둔다.  
그렇다고 모든 CPU-bound 코드가 자동으로 짧게 멈추는 것은 아니다.

다음 경우는 더 주의해야 한다.

- 네이티브 라이브러리 호출이 길다
- JNI 경유가 많다
- busy spin이 길다
- blocking I/O가 VM 밖에서 오래 돈다

### 4. 진단은 로그와 JFR을 함께 본다

`-Xlog:safepoint`는 safepoint가 언제, 얼마나 걸렸는지를 보여준다.  
JFR은 그 구간 전후의 thread state, GC, allocation, lock contention을 같이 묶어준다.

로그만 보면 "멈췄다"만 보이고, JFR을 붙이면 "왜 멈췄는지"가 보인다.

## 실전 시나리오

### 시나리오 1: p99만 튀는데 GC 로그는 조용하다

의심 순서:

1. safepoint log를 본다
2. JFR에서 `jdk.SafepointBegin`와 `jdk.SafepointEnd`를 확인한다
3. 같은 시간대 thread state를 본다
4. native call, class loading, deopt 흔적을 확인한다

이 상황은 GC 튜닝만으로 안 풀릴 수 있다.

### 시나리오 2: 배포 직후만 멈춘다

배포 직후에는 다음이 섞인다.

- class loading
- JIT warmup
- deoptimization
- code cache pressure

초기 구간에만 pause가 몰리면 성능 문제라기보다 "초기화 경로" 문제일 수 있다.

### 시나리오 3: thread dump를 뜨는 순간 서비스가 흔들린다

thread dump는 진단에는 좋지만, 그 자체가 safepoint를 유발할 수 있다.  
즉, 문제를 보기 위해 찍은 스냅샷이 추가 pause를 만들 수 있다.

운영에서는 "관측 비용"을 생각해야 한다.

## 코드로 보기

### 1. safepoint 로그를 켠 실행 예

```bash
java \
  -Xlog:gc,safepoint=info \
  -XX:StartFlightRecording=name=app,settings=profile,filename=/tmp/app.jfr \
  -jar app.jar
```

### 2. 문제 구간의 JFR를 확인하는 예

```bash
jfr summary /tmp/app.jfr
jfr print --events jdk.SafepointBegin,jdk.SafepointEnd /tmp/app.jfr
```

### 3. CPU-bound 루프에 협력적 체크를 넣는 예

```java
public class HotLoop {
    private volatile boolean stop;

    public void requestStop() {
        stop = true;
    }

    public long run(long limit) {
        long acc = 0;
        for (long i = 0; i < limit; i++) {
            acc += i;
            if ((i & 0xFFFFF) == 0 && stop) {
                break;
            }
        }
        return acc;
    }
}
```

이 코드는 safepoint를 직접 줄이지는 않지만, 작업 취소와 관찰을 더 예측 가능하게 만든다.

### 4. 런타임 관측 명령

```bash
jcmd <pid> Thread.print -l
jcmd <pid> JFR.start name=pauses settings=profile duration=60s filename=/tmp/pauses.jfr
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `-Xlog:safepoint` | pause 원인 확인이 빠르다 | 로그가 늘어난다 |
| JFR | 여러 증상을 시간축으로 묶어본다 | 해석하는 습관이 필요하다 |
| thread dump | 즉시 상태를 본다 | 추가 STW를 유발할 수 있다 |
| 협력적 체크 | 작업 취소가 쉬워진다 | 코드에 분기와 상태가 늘어난다 |

핵심은 "멈췄다"를 GC 하나로 환원하지 않는 것이다.

## 꼬리질문

> Q: safepoint와 GC pause는 같은 건가요?
> 핵심: 아니다. GC는 safepoint를 사용하는 대표 사례일 뿐이고, deoptimization이나 thread dump도 pause를 만들 수 있다.

> Q: GC 로그가 조용한데도 latency spike가 나는 이유는 무엇인가요?
> 핵심: safepoint 대기, native call, class loading, deoptimization, lock contention이 함께 있을 수 있다.

> Q: 왜 native code가 safepoint 진단에서 중요하나요?
> 핵심: Java thread가 VM의 poll 지점 바깥에 오래 머무르면 전체 pause가 길어질 수 있다.

## 한 줄 정리

safepoint는 JVM의 안전한 정지 지점이고, STW는 그 지점에서 드러나는 증상이므로 GC만 보지 말고 safepoint 로그와 JFR을 같이 봐야 한다.
