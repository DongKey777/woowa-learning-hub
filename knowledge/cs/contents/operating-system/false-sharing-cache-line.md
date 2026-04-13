# False Sharing, Cache Line

> 한 줄 요약: 서로 다른 변수라도 같은 cache line에 있으면 코어 간 무효화 경쟁 때문에 성능이 급락한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [CPU 캐시, 코히어런시, 메모리 배리어](./cpu-cache-coherence-memory-barrier.md)
> - [컨텍스트 스위칭, 데드락, lock-free](./context-switching-deadlock-lockfree.md)
> - [Java 동시성 유틸리티](../language/java/5.md)

---

## 핵심 개념

CPU는 바이트 단위가 아니라 보통 `cache line` 단위로 메모리를 다룬다.  
한 코어가 한 라인을 수정하면 다른 코어의 같은 라인은 무효화된다.

`false sharing`은 **실제로는 공유하지 않는 변수들이 같은 cache line을 공유해서 생기는 성능 문제**다.

즉 코드 상으로는 서로 다른 필드인데, 하드웨어 관점에서는 같은 줄을 두고 싸우는 상황이다.

---

## 깊이 들어가기

### 1. 왜 느려지는가

코어 A가 `x`를 쓰고, 코어 B가 `y`를 쓴다고 해도 둘이 같은 cache line에 있으면:

- A의 쓰기로 라인이 수정됨
- B의 쓰기로 다시 라인이 수정됨
- 라인 소유권이 계속 오간다

이 과정에서 cache coherence traffic이 폭증한다.

### 2. 어디서 자주 터지는가

- 카운터 배열
- 스레드별 통계값
- 링버퍼 head/tail
- 객체 안의 자주 갱신되는 필드

특히 멀티스레드 서버에서 `volatile long` 필드를 여러 개 나란히 두면 자주 보인다.

### 3. Java에서의 감각

HotSpot은 객체 필드 배치를 보장하지 않는다.  
그래서 "필드 사이에 빈 칸을 넣었다"고 해서 항상 안전한 것은 아니다.

보통은:

- `@Contended` 사용
- padding 필드 추가
- 구조 자체를 분리

같은 방식으로 대응한다.

---

## 실전 시나리오

### 시나리오 1: 카운터를 늘렸더니 더 느려짐

워커별 요청 수를 각각 독립적으로 증가시켰는데, 배열이 한 줄에 몰려 있으면 무효화 비용이 커진다.

진단:

```bash
perf stat -e cache-references,cache-misses <command>
perf c2c record <command>
perf c2c report
```

### 시나리오 2: p99 지연이 이상하게 튐

애플리케이션 로직은 단순한데 CPU 사용률이 올라간다.  
이때는 락 경쟁만 보지 말고 cache line bouncing도 의심해야 한다.

### 시나리오 3: ThreadLocal 통계가 빠른 줄 알았는데 전체가 느림

각 스레드가 자기 변수만 건드리는데도 같은 line에 있으면 서로를 방해한다.

---

## 코드로 보기

### 문제 패턴

```java
public class Metrics {
    public volatile long requestCount;
    public volatile long errorCount;
}
```

두 값이 같은 cache line에 있으면 서로 다른 스레드가 갱신해도 라인 무효화가 반복될 수 있다.

### 완화 예시

```java
@jdk.internal.vm.annotation.Contended
public class Counter {
    public volatile long value;
}
```

주의:

- JDK 버전에 따라 제약이 있다
- `-XX:-RestrictContended` 같은 설정이 필요할 수 있다
- 메모리 사용량이 늘어난다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| padding | 단순하고 효과적 | 메모리 낭비 | hot counter, ring buffer |
| `@Contended` | JVM이 의도를 이해한다 | 설정 제약이 있다 | HotSpot에서 제어 가능할 때 |
| 구조 분리 | 가장 명시적이다 | 코드가 늘어난다 | 설계 수정이 가능할 때 |
| 그냥 둔다 | 추가 메모리 없음 | 성능이 흔들린다 | 거의 없음 |

---

## 꼬리질문

> Q: false sharing이 왜 생기나요?
> 의도: 캐시 라인 단위를 이해하는지 확인
> 핵심: 서로 다른 변수라도 같은 라인에 있으면 coherence traffic이 생긴다.

> Q: `volatile`을 쓰면 false sharing이 해결되나요?
> 의도: 메모리 가시성과 캐시 경쟁을 구분하는지 확인
> 핵심: `volatile`은 가시성을 돕지만 라인 경쟁 자체를 없애지 않는다.

> Q: `@Contended`는 무조건 쓰면 되나요?
> 의도: 도구를 만능으로 오해하지 않는지 확인
> 핵심: 메모리 비용과 JVM 설정 제약이 있다.

---

## 한 줄 정리

false sharing은 변수 공유가 아니라 cache line 공유의 문제다. 성능을 볼 때는 락만이 아니라 하드웨어 무효화 비용도 같이 봐야 한다.
