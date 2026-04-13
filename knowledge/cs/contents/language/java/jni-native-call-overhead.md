# JNI Native Call Overhead

> 한 줄 요약: JNI는 Java와 native 사이의 강한 경계를 넘는 도구라 기능은 넓지만, 호출 비용, pinning, copying, safepoint interaction, debugging 난이도를 함께 감수해야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Safepoint and Stop-the-World Diagnostics](./safepoint-stop-the-world-diagnostics.md)
> - [Direct Buffer Off-Heap Memory Troubleshooting](./direct-buffer-offheap-memory-troubleshooting.md)
> - [Java Agent and Instrumentation Basics](./java-agent-instrumentation-basics.md)
> - [Memory Barriers and VarHandle Fences](./memory-barriers-varhandle-fences.md)

> retrieval-anchor-keywords: JNI, native call, Java Native Interface, crossing overhead, pinning, copying, safepoint, GC interaction, native boundary, hot path, FFI, array critical

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

JNI는 Java 코드가 native 라이브러리와 직접 통신하게 하는 인터페이스다.  
강력하지만, Java 경계 밖으로 나가는 순간 JVM 최적화와 관측이 약해질 수 있다.

주요 비용:

- native transition overhead
- pinning 또는 copying
- GC/safepoint 협조 비용
- 디버깅과 크래시 원인 추적 난이도

## 깊이 들어가기

### 1. 왜 JNI가 무거워질 수 있나

JNI 호출은 단순 Java method call보다 경계가 많다.

- type marshaling
- thread state 전환
- exception 처리
- GC 협조

짧은 계산을 자주 넘기면 오히려 손해가 커진다.

### 2. 배열과 버퍼를 넘길 때의 비용

native 쪽이 Java 배열을 직접 만지려 하면 pinning이나 copy 경로가 생길 수 있다.  
그 결과:

- GC가 덜 자유로워질 수 있다
- 메모리 복사 비용이 생길 수 있다
- 장시간 native 구간에서 pause가 길어질 수 있다

### 3. hot path에는 특히 조심해야 한다

JNI는 장기적으로 꼭 필요할 수 있지만, 요청마다 호출되는 hot path에 두면 비용이 누적된다.  
가능하면 배치 처리, batching, offload를 고려해야 한다.

### 4. 디버깅이 어려운 이유

Java stack만 봐서는 native 내부가 안 보인다.  
문제가 다음처럼 보일 수 있다.

- GC는 조용한데 latency가 튄다
- thread dump에서 native frame만 길다
- crash log가 JVM 밖에서 난 것처럼 보인다

## 실전 시나리오

### 시나리오 1: 이미지 처리나 압축을 native로 넘긴다

대량 데이터 처리에는 도움이 될 수 있지만, call frequency가 높으면 boundary cost가 부담이 된다.

### 시나리오 2: 대형 배열을 자주 넘긴다

copy 비용과 pinning 비용을 먼저 의심해야 한다.  
직접 mutable buffer를 shared해서 넘길지, chunking할지 설계가 중요하다.

### 시나리오 3: native library가 느려서가 아니라 경계가 느리다

실제 병목은 native 알고리즘이 아니라 JNI crossing 자체일 수 있다.  
그래서 call count를 먼저 줄여야 한다.

## 코드로 보기

### 1. JNI 진입점 감각

```java
public class NativeBridge {
    static {
        System.loadLibrary("native-lib");
    }

    private native int sum(int a, int b);
}
```

### 2. 비용이 큰 패턴

```java
for (int i = 0; i < 1_000_000; i++) {
    nativeCall(i);
}
```

작은 호출을 너무 많이 반복하면 경계 비용이 눈에 띈다.

### 3. batching이 더 나을 수 있다

```java
// 여러 작은 호출 대신 한 번에 묶어서 native로 넘기는 편이 유리할 수 있다.
```

### 4. 관측 명령

```bash
jcmd <pid> Thread.print -l
jcmd <pid> JFR.start name=native settings=profile duration=60s filename=/tmp/native.jfr
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| JNI | 강력하고 기존 native 자산을 쓸 수 있다 | boundary 비용과 안전성 비용이 있다 |
| pure Java | JVM 최적화를 잘 탄다 | native 기능이 필요하면 한계가 있다 |
| batching | crossing 횟수를 줄인다 | 인터페이스가 복잡해진다 |
| offload thread | blocking 영향이 줄 수 있다 | 스케줄링 복잡도가 늘어난다 |

핵심은 JNI를 "한 번 호출하면 끝"이 아니라 "경계 비용이 있는 시스템 통합"으로 보는 것이다.

## 꼬리질문

> Q: JNI가 느린 이유는 무엇인가요?
> 핵심: Java-native 경계 전환, type marshaling, GC 협조, 호출 빈도 때문이다.

> Q: native call이 safepoint와 어떻게 연결되나요?
> 핵심: 긴 native 구간은 JVM이 전체 pause를 조율하는 데 영향을 줄 수 있다.

> Q: JNI를 언제 쓰는 것이 합리적인가요?
> 핵심: 꼭 필요한 native capability가 있고 호출 빈도가 낮거나 batching이 가능한 경우다.

## 한 줄 정리

JNI는 필요한 순간엔 유용하지만, 경계 자체가 비용이므로 hot path에서는 호출 횟수와 데이터 이동을 먼저 줄여야 한다.
