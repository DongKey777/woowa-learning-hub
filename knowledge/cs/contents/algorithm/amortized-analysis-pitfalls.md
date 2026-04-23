# Amortized Analysis Pitfalls

> 한 줄 요약: 상각 분석은 평균처럼 보이지만, 실제 서비스에서는 순간 비용과 꼬리 지연을 함께 봐야 한다.
>
> 문서 역할: 이 문서는 algorithm 카테고리 안에서 **복잡도 해석 함정과 성능 감각**을 다루는 pattern deep dive다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)
> - [Union-Find Amortized Proof Intuition](./union-find-amortized-proof-intuition.md)
> - [Monotone Deque Proof Intuition](./monotone-deque-proof-intuition.md)
> - [HashMap 내부 구조](../data-structure/hashmap-internals.md)
> - [LRU Cache Design](../data-structure/lru-cache-design.md)
>
> retrieval-anchor-keywords: amortized analysis, amortized O(1), average vs worst case, resize spike, rehash cost, dynamic array growth, tail latency, p99 latency, bursty cost, complexity pitfall

## 이 문서 다음에 보면 좋은 문서

- 기본 복잡도 primer는 [시간복잡도와 공간복잡도](./basic.md#시간복잡도와-공간복잡도)로 되돌아가면 좋다.
- 상각 증명이 실제로 왜 성립하는지 더 깊게 보려면 [Union-Find Amortized Proof Intuition](./union-find-amortized-proof-intuition.md)으로 이어지면 좋다.
- 단조 덱처럼 "각 원소는 많아야 한 번 들어오고 한 번 나간다"는 직관은 [Monotone Deque Proof Intuition](./monotone-deque-proof-intuition.md)에서 이어진다.
- 자료구조에서 실제 resize / rehash spike 사례를 보려면 [HashMap 내부 구조](../data-structure/hashmap-internals.md), [LRU Cache Design](../data-structure/lru-cache-design.md)으로 이어진다.

## 핵심 개념

상각 분석(amortized analysis)은 여러 연산을 묶어서 평균적인 비용을 보는 방법이다.

중요한 구분은 다음과 같다.

- `worst case`: 한 번의 최악 비용
- `average case`: 입력 분포 기준 평균
- `amortized`: 연산 묶음 전체의 평균 비용

상각 O(1)은 "매번 1"이 아니라 "여러 번 합치면 평균적으로 1"이라는 뜻이다.

## 깊이 들어가기

### 1. 왜 필요한가

어떤 자료구조는 대부분 빠르지만, 가끔 확장 비용이 크다.

예:

- 동적 배열의 resize
- `HashMap`의 rehash
- `ArrayDeque`의 확장
- 두 스택으로 구현한 큐의 전환 비용

이런 구조는 단발성 최악 비용만 보면 과하게 비싸 보일 수 있다.
하지만 전체 연산을 묶어서 보면 효율적이다.

### 2. 서비스에서는 왜 조심해야 하는가

상각 O(1)는 평균 처리량에는 좋지만, 단일 요청 지연 시간에는 spikes를 만들 수 있다.

즉:

- 배치 처리에는 잘 맞을 수 있다.
- p99 지연이 중요한 API에는 경계가 필요하다.

### 3. "상각"과 "평균"은 다르다

평균은 입력 분포에 기대고,
상각은 구조의 동작 자체를 기반으로 한다.

그래서 상각 분석은 더 강한 설명이지만, 곧바로 tail latency를 보장하지는 않는다.

---

## 실전 시나리오

### 시나리오 1: `HashMap` resize

대부분의 `put()`은 빠르지만, resize 시점에는 전체 엔트리를 옮긴다.
이 한 번의 비용 때문에 "HashMap은 항상 O(1)"이라고 말하면 틀린다.

### 시나리오 2: `ArrayList` add

대부분은 뒤에 넣기만 하면 되지만, 용량이 꽉 차면 더 큰 배열을 만들고 복사해야 한다.
그래도 전체적으로는 상각 O(1)이다.

### 시나리오 3: 지연 시간 민감 서비스

실시간 결제나 채팅의 핵심 경로에서 resize 같은 이벤트가 발생하면,
상각 분석이 맞아도 사용자 체감은 나빠질 수 있다.

---

## 코드로 보기

```java
public class DynamicArray {
    private int[] data = new int[4];
    private int size = 0;

    public void add(int value) {
        if (size == data.length) {
            resize();
        }
        data[size++] = value;
    }

    private void resize() {
        int[] next = new int[data.length * 2];
        for (int i = 0; i < data.length; i++) {
            next[i] = data[i];
        }
        data = next;
    }
}
```

`add()`는 대부분 빠르지만, resize 시점에만 복사 비용이 크게 든다.
이런 구조를 보고 상각 분석을 적용한다.

---

## 트레이드오프

| 관점 | 장점 | 단점 | 언제 보는가 |
|---|---|---|---|
| Worst-case | 최악을 명확히 본다 | 전체 효율을 과소평가할 수 있다 | 실시간성, SLA가 중요할 때 |
| Average-case | 실제 분포를 반영할 수 있다 | 입력 분포 가정이 깨질 수 있다 | 안정적인 데이터 분포가 있을 때 |
| Amortized | 구조 전체 효율을 설명한다 | 개별 spikes를 숨길 수 있다 | resize/rehash가 있는 자료구조 |

실무 판단 기준은 "평균 처리량"뿐 아니라 "한 번의 확장 비용이 허용 가능한가"다.

---

## 꼬리질문

> Q: 상각 O(1)인데 왜 느리다고 느껴지는가?
> 의도: 평균과 tail latency를 구분하는지 확인
> 핵심: 가끔 큰 비용이 몰리면 사용자 체감은 나빠진다.

> Q: 상각 분석은 언제 믿으면 안 되는가?
> 의도: 분석과 시스템 요구를 연결하는지 확인
> 핵심: p99, 실시간 경로, 짧은 timeout이 있는 API다.

> Q: 평균 O(1)과 상각 O(1)은 같은가?
> 의도: 용어 정확도 확인
> 핵심: 다르다. 상각은 구조적 보장이고 평균은 분포 의존이다.

## 한 줄 정리

상각 분석은 구조 전체 효율을 설명하는 도구지만, 실제 서비스에서는 resize나 rehash 같은 순간 비용까지 같이 봐야 한다.
