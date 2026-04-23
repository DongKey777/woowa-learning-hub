# JFR and JMC Performance Playbook

> 한 줄 요약: JFR은 JVM 내부에서 무슨 일이 일어나는지 기록하는 장치이고, JMC는 그 기록을 읽어 병목을 찾는 도구다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [G1 GC vs ZGC](./g1-vs-zgc.md)
> - [Reflection 비용과 대안](./reflection-cost-and-alternatives.md)
> - [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./locksupport-park-unpark-permit-semantics.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)

> retrieval-anchor-keywords: JFR, JMC, Java Flight Recorder, Mission Control, lock contention, allocation rate, thread parking, park, blocker, socket read, GC pause, profiling, runtime event

## 핵심 개념

JFR(Java Flight Recorder)은 JVM 이벤트를 저비용으로 기록하는 기능이다.  
JMC(Java Mission Control)는 그 기록을 분석하는 GUI 도구다.

이 조합이 중요한 이유는 성능 문제의 대부분이 "느리다"가 아니라 다음 중 하나이기 때문이다.

- GC pause
- lock contention
- allocation burst
- thread scheduling
- I/O 대기
- class loading

JFR은 이런 현상을 시간 축으로 남기고, JMC는 그 패턴을 읽어 병목을 좁힌다.

## 깊이 들어가기

### 1. JFR이 좋은 이유

프로파일러는 많이 있지만 JFR은 운영 친화적이다.

| 항목 | 의미 |
|---|---|
| 저오버헤드 | 상시 켜도 되는 수준으로 설계됨 |
| 이벤트 기반 | GC, lock, allocation, thread, socket 등을 기록 |
| 시간 축 | "언제" 느려졌는지 본다 |
| JVM 내부 | 애플리케이션 코드만이 아니라 런타임도 본다 |

### 2. JMC로 보는 것

JMC에서는 보통 다음을 본다.

- latency spike 구간
- allocation rate
- thread dump와 lock graph
- GC pause와 heap pressure
- hot methods

### 3. 어디서 시작하나

운영 환경에서 시작은 보통 간단하다.

```bash
jcmd <pid> JFR.start name=profile settings=profile duration=5m filename=/tmp/app.jfr
```

그 다음 JMC에서 열어 본다.

성능 문제는 "코드만" 보지 말고, JFR로 JVM 레벨 증상을 먼저 잡는 편이 빠르다.

## 실전 시나리오

### 시나리오 1: p99가 튀는데 CPU는 한가하다

이 경우는 흔히 다음 중 하나다.

- GC pause
- lock contention
- socket wait
- thread parking

JFR의 장점은 이들을 분리해서 보여준다는 점이다.

### 시나리오 2: 배포 후만 느려진다

이때는 warmup, class loading, JIT deopt, cache miss가 얽혀 있을 수 있다.  
JFR은 "배포 직후와 안정화 후"를 비교하는 데 유용하다.

### 시나리오 3: Virtual Threads를 넣고도 병목이 그대로다

스레드 모델이 바뀌어도 allocation이나 DB wait가 해결되는 것은 아니다.  
JFR로 보면 virtual thread count보다 `socket read`, `park`, `pinning`, `allocation pressure`를 봐야 한다.

## 코드로 보기

### 1. JFR 이벤트를 켠 채 실행

```bash
java \
  -XX:StartFlightRecording=name=app,settings=profile,filename=/tmp/app.jfr \
  -jar app.jar
```

### 2. 프로그램적으로 JFR 시작

```java
import jdk.jfr.Recording;

try (Recording recording = new Recording()) {
    recording.start();
    // workload
    recording.stop();
    recording.dump(java.nio.file.Path.of("/tmp/app.jfr"));
}
```

### 3. 간단한 핫스팟 코드

```java
public class AllocationService {
    public String build(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(i).append(',');
        }
        return sb.toString();
    }
}
```

이런 코드는 JFR에서 allocation burst나 hot method로 잡히기 쉽다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| JFR 상시 | 운영 친화적 | GUI 분석이 필요하다 | 지속 관찰 |
| JMC 중심 | 원인 파악이 빠르다 | 파일 분석 숙련이 필요하다 | 장애 후 분석 |
| async-profiler | CPU/alloc에 강하다 | JVM 이벤트 전반은 약하다 | 핫스팟 추적 |
| VisualVM | 가볍고 익숙하다 | 심층 분석은 제한적 | 개발/간단 점검 |

## 꼬리질문

> Q: JFR을 왜 프로파일링에 유리하다고 보나요?
> 의도: 저비용 관측과 런타임 이벤트 이해 여부 확인
> 핵심: JVM 내부 이벤트를 저오버헤드로 시간 축에 남길 수 있다.

> Q: JMC에서 제일 먼저 봐야 할 것은 무엇인가요?
> 의도: 문제를 무작정 코드로만 보지 않는지 확인
> 핵심: GC pause, allocation, lock contention, thread state부터 본다.

> Q: JFR이 있어도 heap dump가 필요한가요?
> 의도: 도구의 역할 분리를 아는지 확인
> 핵심: JFR은 증상, heap dump는 잔존 객체와 참조 경로 분석에 강하다.

## 한 줄 정리

JFR은 JVM의 증상을 기록하고, JMC는 그 기록을 읽어 병목의 원인을 좁히는 운영용 프로파일링 도구다.
