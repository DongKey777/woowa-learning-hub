# G1 GC vs ZGC

> 한 줄 요약: G1은 균형 잡힌 기본 선택이고, ZGC는 짧은 멈춤 시간을 우선할 때 고려하는 저지연 GC다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [CPU Cache, Coherence, Memory Barrier](../../operating-system/cpu-cache-coherence-memory-barrier.md)
> - [Spring MVC vs WebFlux](../../spring/spring-webflux-vs-mvc.md)

retrieval-anchor-keywords: G1 vs ZGC, Java GC choice, low latency GC, tail latency GC pause, STW pause, large heap GC, G1 pause target, ZGC short pause, allocation rate and live set, GC tuning decision

---

## 핵심 개념

GC 선택은 "무엇이 최고냐"가 아니라, **어떤 지연 비용을 받아들일 수 있느냐**의 문제다.

- G1은 예측 가능한 평균 성능과 균형을 중시한다.
- ZGC는 매우 짧은 STW pause를 목표로 한다.
- 둘 다 "GC가 없다"는 뜻이 아니라, **pause를 어디까지 줄이고 어떤 비용을 분산할지**의 차이다.

백엔드에서는 보통 아래 질문으로 시작한다.

- 응답 지연의 tail latency가 중요한가
- heap이 큰가
- 객체 생성이 많은가
- throughput이 더 중요한가
- 운영자가 튜닝할 시간이 있는가

---

## 깊이 들어가기

### 1. G1은 왜 기본 선택이 되었나

G1은 힙을 region으로 나누고, 우선순위가 높은 region부터 수집해 pause를 예측 가능하게 만들려는 방향이다.

핵심 감각:

- "전체 힙을 한 번에"가 아니라 "일부 region씩" 수집한다
- pause time 목표를 기준으로 작업량을 조절한다
- 큰 heap에서도 상대적으로 다루기 쉽다

G1이 좋은 이유는, 특별한 요구가 없는 대부분의 서버에서 **성과 예측 가능성의 균형**이 좋기 때문이다.

### 2. ZGC는 왜 저지연을 노리나

ZGC는 짧은 pause를 유지하기 위해, mark/relocate 작업을 가능한 한 병렬화하고 pause 구간을 극단적으로 줄이려는 설계다.

핵심 감각:

- pause를 짧게 만드는 대신 구현과 운영 복잡도가 올라간다
- 큰 heap, latency-sensitive 서비스에서 의미가 커진다
- "평균 응답"보다 "최악 응답"이 중요한 서비스에서 가치가 있다

### 3. 선택 기준

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| G1 | 균형이 좋고 운영 경험이 많다 | 아주 짧은 pause는 어렵다 | 일반적인 웹/API 서버 |
| ZGC | pause가 매우 짧다 | 환경/관측/운영 복잡도가 높다 | tail latency가 중요한 대형 heap 서비스 |

실무 판단은 보통 이렇다.

1. 먼저 G1으로 시작한다
2. GC pause가 병목인지 확인한다
3. pause가 실제 사용자 경험을 해친다면 ZGC를 검토한다
4. GC만 바꿔도 안 풀리면 allocation rate와 object lifetime부터 본다

### 4. 튜닝은 GC 이름보다 더 중요하다

GC를 바꿔도 다음이 안 맞으면 효과가 없다.

- heap 크기
- young/old 비율
- allocation rate
- live set size
- thread pool 과다 사용

즉, GC는 "버튼 하나"가 아니라 **애플리케이션의 할당 패턴과 같이 봐야 하는 운영 파라미터**다.

---

## 실전 시나리오

### 시나리오 1: 평균은 빠른데 가끔 1초씩 멈춘다

증상:

- p99 latency가 튄다
- CPU는 여유 있는데 요청이 간헐적으로 밀린다
- 로그를 보면 GC pause와 겹친다

대응:

1. GC 로그로 pause 빈도와 길이를 본다
2. live object가 많은지 확인한다
3. G1의 pause target과 heap을 조정한다
4. 그래도 tail이 문제면 ZGC를 검토한다

### 시나리오 2: 큰 heap을 쓰는 서비스에서 배치 작업이 API를 방해한다

배치가 대량 객체를 만들면 young GC와 old GC가 모두 흔들릴 수 있다.

이때는 단순히 "GC를 빠르게"가 아니라:

- 배치와 API JVM 분리
- allocation을 줄이는 구조 변경
- thread pool과 buffer 크기 조정

까지 같이 본다.

### 시나리오 3: Virtual Threads를 붙였는데 pause는 그대로다

Virtual Threads는 스레드 모델을 바꾸지만 GC를 없애지 않는다.

즉:

- 요청 처리 구조는 단순해질 수 있다
- 하지만 객체 할당량이 많으면 GC 압력은 그대로다

이 문맥은 [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)와 함께 봐야 한다.

---

## 코드로 보기

### GC 로그를 먼저 보는 습관

```bash
java \
  -XX:+UseG1GC \
  -Xms2g -Xmx2g \
  -Xlog:gc*:stdout:time,level,tags \
  -jar app.jar
```

ZGC 검토 시에는:

```bash
java \
  -XX:+UseZGC \
  -Xms2g -Xmx2g \
  -Xlog:gc*:stdout:time,level,tags \
  -jar app.jar
```

### 힙 압박을 만드는 코드 예시

```java
public class PayloadService {
    public byte[] buildPayload(int sizeKb) {
        return new byte[sizeKb * 1024];
    }
}
```

이런 코드가 반복되면 GC 선택보다 먼저 아래를 본다.

- 큰 객체를 꼭 매 요청마다 만들어야 하는가
- 캐시/버퍼 재사용이 가능한가
- 직렬화 포맷을 줄일 수 있는가

---

## 트레이드오프

| 관점 | G1 | ZGC |
|---|---|---|
| 평균 처리량 | 좋다 | 보통 좋다 |
| 짧은 pause | 보통 | 매우 좋다 |
| 운영 복잡도 | 낮다 | 높다 |
| 기본값 적합성 | 높다 | 선택적 |
| tail latency | 보통 | 유리 |

핵심은 "무조건 ZGC가 더 좋다"가 아니라, **대부분의 서비스는 G1으로 충분하고, tail latency가 문제일 때 ZGC를 검토한다**는 점이다.

---

## 꼬리질문

> Q: G1을 쓰다가 ZGC로 바꿔야 하는 기준은 무엇인가요?
> 의도: GC 선택을 지연 시간 SLA와 연결해서 판단할 수 있는지 확인
> 핵심: 평균이 아니라 p95/p99 latency와 pause 원인을 먼저 본다

> Q: GC를 바꿨는데도 느리면 무엇부터 보나요?
> 의도: GC를 만능 해결책으로 보는지 확인
> 핵심: allocation rate, live set, heap size, thread pool, 직렬화 비용을 먼저 본다

> Q: Virtual Threads를 쓰면 GC 문제가 줄어드나요?
> 의도: 스레드 모델과 메모리 관리의 차이를 구분하는지 확인
> 핵심: 스레드 수는 줄일 수 있어도 객체 할당과 살아 있는 데이터는 그대로다

## 한 줄 정리

G1은 기본 균형점이고, ZGC는 tail latency가 중요한 서비스에서 pause를 줄이기 위한 선택이다.
