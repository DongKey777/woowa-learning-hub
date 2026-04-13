# TLAB and PLAB Allocation Intuition

> 한 줄 요약: TLAB는 thread별 빠른 allocation 통로이고 PLAB는 GC copy/evacuation 경로의 per-thread buffer라서, "할당이 빠르다"는 말은 결국 buffer refill과 GC survivor 이동 비용까지 포함해 읽어야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Escape Analysis and Scalar Replacement](./escape-analysis-scalar-replacement.md)
> - [Object Pooling Myths in the Modern JVM](./object-pooling-myths-modern-jvm.md)
> - [JFR Event Interpretation](./jfr-event-interpretation.md)
> - [Compressed Oops and Class Pointers](./compressed-oops-class-pointers.md)

> retrieval-anchor-keywords: TLAB, thread-local allocation buffer, PLAB, promotion local allocation buffer, bump pointer, refill, allocation fast path, GC evacuation, survivor copy, allocation pressure, Eden, HotSpot GC

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

HotSpot은 많은 객체 할당을 thread별 TLAB에서 처리해 contention을 줄인다.  
즉 객체 생성은 보통 GC와 상관없이 빠른 bump-pointer 스타일로 끝난다.

GC 측면에서는 PLAB가 등장한다.  
PLAB는 evacuation/promotion 과정에서 thread별로 복사 버퍼를 빠르게 쓰게 하는 장치다.

## 깊이 들어가기

### 1. TLAB는 왜 빠른가

TLAB는 각 thread가 자기만의 작은 allocation chunk를 가진다고 생각하면 된다.

- lock 경합이 적다
- pointer bump로 빠르게 할당한다
- chunk가 다 차면 refill한다

그래서 "작은 객체 생성이 빠르다"는 말은 사실 TLAB 덕분인 경우가 많다.

### 2. refill이 진짜 비용이다

할당 자체는 빠르더라도 TLAB refill은 비용이 있다.

- Eden에서 새 TLAB를 받아오거나
- GC 시점과 맞물려 refill 경로가 달라질 수 있다

즉 할당 latency를 읽을 때는 refill 빈도와 object size 분포를 같이 봐야 한다.

### 3. PLAB는 GC copy 경로의 친척이다

GC가 객체를 옮길 때도 thread별 copy buffer가 있으면 throughput이 좋다.  
PLAB는 이 evacuation/promotion 복사 비용을 줄이는 쪽으로 이해하면 된다.

### 4. 작은 객체가 많을수록 이득이 커질 수 있다

객체가 많고 짧게 산다면 TLAB/PLAB의 장점이 잘 드러난다.  
반대로 큰 객체, direct buffer, off-heap 구조는 다른 경로를 본다.

## 실전 시나리오

### 시나리오 1: allocation은 많은데 생각보다 빠르다

TLAB fast path 덕분일 수 있다.  
이 경우 allocation 자체보다 GC pressure와 object lifetime이 더 중요하다.

### 시나리오 2: allocation burst 후 pause가 길어진다

TLAB가 빠르다고 해서 GC가 사라지는 것은 아니다.  
많은 짧은 객체가 survivor로 몰리면 evacuation과 promotion 비용이 커질 수 있다.

### 시나리오 3: thread 수가 늘수록 메모리 감각이 달라진다

thread별 TLAB와 stack, GC 보조 버퍼가 함께 움직일 수 있다.  
그래서 thread count 변화는 allocation 성능과 메모리 footprint 둘 다에 영향을 줄 수 있다.

## 코드로 보기

### 1. 작은 객체 다발 예

```java
public class EventBuilder {
    public String build(int id, String type) {
        return new StringBuilder()
            .append(id)
            .append(':')
            .append(type)
            .toString();
    }
}
```

### 2. allocation 관찰 명령

```bash
java -XX:+PrintTLAB -jar app.jar
```

### 3. JFR과 같이 본다

```bash
jcmd <pid> JFR.start name=alloc settings=profile duration=60s filename=/tmp/alloc.jfr
```

### 4. 객체 재사용과 비교

```java
// TLAB가 잘 먹는 경우에는
// 작은 객체를 억지로 재사용하는 것보다 단순 생성이 더 나을 수 있다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| TLAB fast path | 작은 객체 할당이 매우 빠르다 | refill과 GC 연동 비용이 있다 |
| PLAB/evacuation buffer | GC copy throughput이 좋아진다 | GC phase에 의존한다 |
| object reuse | churn을 줄일 수 있다 | 코드 복잡도와 contention이 늘 수 있다 |
| 큰 객체 직접 관리 | 할당 수를 줄인다 | 설계가 더 어려워진다 |

핵심은 "객체 생성 = 느림"이 아니라, 대부분의 작은 객체는 TLAB 덕분에 싸게 보인다는 점이다.

## 꼬리질문

> Q: TLAB는 왜 필요한가요?
> 핵심: thread별로 빠른 bump-pointer allocation을 제공해 경합을 줄이기 위해서다.

> Q: PLAB는 무엇과 관련 있나요?
> 핵심: GC evacuation/promotion 시 thread별 copy buffer로 throughput을 높이는 데 관련된다.

> Q: allocation이 빠른데 왜 GC는 여전히 중요한가요?
> 핵심: allocation과 lifetime은 별개라서, 짧은 객체가 많으면 evacuation/promotion 비용이 커질 수 있다.

## 한 줄 정리

TLAB와 PLAB는 할당과 복사 경로를 빠르게 만드는 buffer 전략이고, 객체 생성 비용을 읽을 때는 refill과 GC evacuation까지 같이 봐야 한다.
