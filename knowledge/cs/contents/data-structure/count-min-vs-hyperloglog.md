# Count-Min Sketch vs HyperLogLog

> 한 줄 요약: Count-Min Sketch는 빈도 추정, HyperLogLog는 고유 개수 추정에 쓰이며 둘 다 스트리밍 친화적이지만 질문 자체가 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Count-Min Sketch](./count-min-sketch.md)
> - [HyperLogLog](./hyperloglog.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)

> retrieval-anchor-keywords: count-min sketch vs hyperloglog, frequency vs cardinality, streaming sketch comparison, approximate analytics, hot keys, unique count, sketch tradeoff

## 핵심 개념

둘 다 작은 메모리로 대규모 스트림을 처리하는 sketch다.

- Count-Min Sketch: "이 항목이 얼마나 자주 나왔나"
- HyperLogLog: "서로 다른 항목이 몇 개나 있나"

즉 둘을 비교할 때 먼저 질문을 구분해야 한다.

## 깊이 들어가기

### 1. Count-Min Sketch가 답하는 것

빈도, 카운트, hot key를 다룬다.

- 과대 추정 가능
- 개별 항목 frequency 추적
- heavy hitters와 함께 쓰기 좋음

### 2. HyperLogLog가 답하는 것

고유 원소 수, distinct count, cardinality를 다룬다.

- 전체 원소를 저장하지 않음
- distinct visitor 수 추정
- 매우 적은 메모리로 큰 집합 크기 추정

### 3. backend에서의 선택 감각

어떤 메트릭을 보고 싶은가에 따라 다르다.

- "이 endpoint가 몇 번 호출됐나" -> Count-Min Sketch
- "이 테넌트가 몇 명이나 있나" -> HyperLogLog

질문이 frequency인지 cardinality인지가 핵심이다.

### 4. 오차 성향도 다르다

Count-Min Sketch는 충돌로 인한 과대 추정이 문제다.  
HyperLogLog는 통계적 근사 오차를 가진 cardinality 추정기다.

둘 다 정확한 값을 대체하는 것이 아니라 대략적인 운영 판단을 돕는다.

## 실전 시나리오

### 시나리오 1: 운영 대시보드

요청 수와 고유 사용자 수를 각각 다른 sketch로 집계할 수 있다.

### 시나리오 2: 캐시/샤드 관측

hot key는 Count-Min Sketch, distinct tenant 수는 HyperLogLog로 보는 식이다.

### 시나리오 3: 오판

unique count를 Count-Min Sketch로 해결하려 하면 질문이 잘못된 것이다.

### 시나리오 4: 비용 통제

둘 다 정확한 set/hash map보다 훨씬 메모리를 적게 쓴다.

## 코드로 보기

```java
public class SketchChoiceNotes {
    public static String choose(boolean frequency, boolean cardinality) {
        if (frequency) return "Count-Min Sketch";
        if (cardinality) return "HyperLogLog";
        return "Need a different tool";
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Count-Min Sketch | 빈도 추정이 빠르고 작다 | 과대 추정 가능 | hot key, counts |
| HyperLogLog | distinct count에 매우 효율적이다 | 정확하지 않다 | unique users, cardinality |
| HashMap/Set | 정확하다 | 메모리가 많이 든다 | 소규모 정확 집계 |

## 꼬리질문

> Q: 어떤 질문에 Count-Min이 맞나?
> 의도: frequency 문제 인식 확인
> 핵심: "얼마나 자주"를 묻는 문제다.

> Q: HyperLogLog는 무엇에 맞나?
> 의도: cardinality 문제 인식 확인
> 핵심: "서로 다른 개수"를 묻는 문제다.

> Q: 둘 중 하나를 고르기 전에 무엇을 확인해야 하나?
> 의도: 문제 정의 우선순위 확인
> 핵심: 질문이 frequency인지 cardinality인지다.

## 한 줄 정리

Count-Min Sketch와 HyperLogLog는 둘 다 스트리밍 sketch지만, 하나는 빈도 추정이고 다른 하나는 고유 개수 추정이다.
