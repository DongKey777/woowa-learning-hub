# Radix Heap

> 한 줄 요약: Radix Heap은 key가 단조 증가하는 priority queue 상황에서 bucket 간격을 비트 길이 기준으로 나눠, 일반 binary heap보다 더 싼 monotone priority queue를 노리는 자료구조다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Heap Variants](./heap-variants.md)
> - [Calendar Queue](./calendar-queue.md)
> - [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)
> - [Timing Wheel Variants and Selection](./timing-wheel-variants-and-selection.md)

> retrieval-anchor-keywords: radix heap, monotone priority queue, integer priority queue, bucketed heap, dijkstra priority queue, monotonic scheduler, nondecreasing key queue, deadline queue, integer key bucket queue, shortest path heap

## 핵심 개념

일반 priority queue는 "어떤 key든 들어오고, 어떤 순서로든 나올 수 있다"는 가정 위에 있다.  
하지만 실제 workload 중에는 훨씬 강한 성질이 있는 경우가 있다.

- dequeue된 key는 점점 커진다
- 새로 들어오는 key는 현재 최소값보다 작지 않다

이런 monotone 상황에서는 binary heap의 일반성이 과할 수 있다.  
Radix Heap은 정수 key의 비트 차이를 이용해 bucket을 나누고,  
현재 최소값 근처 bucket만 세밀하게 다루는 monotone priority queue다.

## 깊이 들어가기

### 1. monotone priority queue라는 제약이 핵심이다

Radix Heap은 모든 priority queue를 대체하려는 구조가 아니다.  
대신 다음 가정이 있을 때 힘을 발휘한다.

- pop되는 최소 key는 nondecreasing
- push되는 key도 그보다 작지 않다

대표적으로 Dijkstra의 nonnegative edge 상황에서 이런 성질이 성립한다.  
일부 scheduler/deadline queue도 현재 시각 이후 task만 넣는다면 비슷한 감각이 된다.

### 2. bucket은 "마지막으로 꺼낸 값과의 최상위 차이 비트"로 결정된다

Radix Heap은 보통 `lastDeleted`를 기억한다.

- key == lastDeleted 이면 bucket 0
- 그 외에는 `msb(key XOR lastDeleted)`에 따라 bucket 결정

즉 값 자체 절대 구간보다,  
**현재 최소값과 얼마나 멀리 떨어져 있는가**를 비트 길이로 본다.

이 발상 덕분에 가까운 값은 세밀하게, 먼 값은 거칠게 묶을 수 있다.

### 3. 재분배(redistribution)가 동작의 핵심이다

가장 앞 bucket이 비어 있으면 다음 non-empty bucket을 꺼내고,  
그 안의 최소 key를 새 `lastDeleted`로 삼은 뒤 원소들을 다시 bucket에 분배한다.

이 과정 때문에:

- 개별 push는 매우 단순해질 수 있고
- bucket 수는 word size 수준으로 고정할 수 있다

하지만 한 번의 redistribution은 큰 비용처럼 보일 수 있다.  
실제로는 monotone 성질 덕분에 amortized하게 감당하는 쪽이다.

### 4. heap / calendar queue / timing wheel과 어디서 갈리나

세 구조 모두 bucket 또는 ordering 최적화를 하지만 전제가 다르다.

- binary heap: 범용 priority queue
- calendar queue: deadline 분포가 bucket tuning에 맞을 때 유리
- timing wheel: tick 기반 timeout 관리
- radix heap: monotone integer key에 특화

즉 radix heap은 "분포"보다 **단조 증가하는 key 계약**을 더 강하게 활용한다.

### 5. backend에서 어디에 맞나

실무 backend에서 radix heap은 흔히 숨어 있는 구조다.

- monotone deadline scheduler
- event time가 되돌아가지 않는 queue
- shortest-path / routing / graph processing
- batch replay의 next offset queue

특히 key가 integer이고 현재 시점 이후로만 들어오는 작업이라면  
일반 heap보다 더 작은 상수와 간단한 bucket 재분배가 이점이 될 수 있다.

## 실전 시나리오

### 시나리오 1: monotone deadline queue

현재 시각 이후 task만 enqueue하는 지연 작업 처리기라면  
radix heap이 binary heap보다 더 잘 맞을 수 있다.

### 시나리오 2: Dijkstra / routing

nonnegative edge를 가진 shortest path에서 우선순위는 점점 증가하므로  
radix heap은 고전적인 integer priority queue 선택지다.

### 시나리오 3: replay / offset scheduler

offset이나 sequence number가 절대 뒤로 가지 않는 재생 파이프라인에서는  
monotone queue 구조가 자연스럽다.

### 시나리오 4: 부적합한 경우

임의의 작은 key가 나중에 들어올 수 있거나,  
priority가 자주 감소하는 일반 queue에는 맞지 않는다.

## 코드로 보기

```java
import java.util.ArrayList;
import java.util.List;

public class RadixHeap<V> {
    private final List<List<Entry<V>>> buckets = new ArrayList<>();
    private long lastDeleted = 0L;

    public RadixHeap() {
        for (int i = 0; i < 65; i++) {
            buckets.add(new ArrayList<>());
        }
    }

    public void offer(long key, V value) {
        if (key < lastDeleted) {
            throw new IllegalArgumentException("radix heap requires monotone keys");
        }
        buckets.get(bucketIndex(key)).add(new Entry<>(key, value));
    }

    public V poll() {
        if (buckets.get(0).isEmpty()) {
            int i = 1;
            while (i < buckets.size() && buckets.get(i).isEmpty()) {
                i++;
            }
            if (i == buckets.size()) {
                return null;
            }

            long newLast = buckets.get(i).stream().mapToLong(entry -> entry.key).min().orElseThrow();
            lastDeleted = newLast;
            List<Entry<V>> redistributed = new ArrayList<>(buckets.get(i));
            buckets.get(i).clear();
            for (Entry<V> entry : redistributed) {
                buckets.get(bucketIndex(entry.key)).add(entry);
            }
        }

        Entry<V> entry = buckets.get(0).remove(buckets.get(0).size() - 1);
        lastDeleted = entry.key;
        return entry.value;
    }

    private int bucketIndex(long key) {
        if (key == lastDeleted) {
            return 0;
        }
        return 64 - Long.numberOfLeadingZeros(key ^ lastDeleted);
    }

    private record Entry<V>(long key, V value) {}
}
```

이 코드는 monotone bucket 재분배 감각만 보여준다.  
실전 구현은 bucket 내부 자료구조, empty check, key 범위 최적화가 더 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Radix Heap | monotone integer key에서 매우 효율적일 수 있다 | 임의 key 감소를 허용하지 않는다 | Dijkstra, monotone deadline queue |
| Binary Heap | 범용적이고 구현이 단순하다 | monotone workload에서도 일반성 비용을 낸다 | 일반적인 priority queue |
| Calendar Queue | deadline 분포가 맞으면 평균 비용이 매우 좋다 | bucket tuning과 skew 대응이 어렵다 | distribution-friendly event scheduler |
| Hierarchical Timing Wheel | timeout churn에 강하다 | tick 기반 근사라는 제약이 있다 | 대량 timeout 관리 |

핵심 질문은 "priority가 단조 증가하나"다.  
그 답이 yes면 radix heap이 갑자기 매우 실용적이 된다.

## 꼬리질문

> Q: radix heap이 일반 heap보다 유리한 조건은 무엇인가요?
> 의도: 자료구조의 전제 조건을 성능과 연결하는지 확인
> 핵심: key가 정수이고 dequeue 최소값이 단조 증가하는 monotone priority queue일 때다.

> Q: bucket을 어떤 기준으로 나누나요?
> 의도: 절대 구간이 아닌 bit-difference 사고를 이해하는지 확인
> 핵심: 보통 현재 `lastDeleted`와 key의 xor에서 가장 높은 차이 비트 위치로 bucket을 정한다.

> Q: 왜 모든 scheduler에 radix heap을 쓰지 않나요?
> 의도: 적용 경계와 계약 위반 위험을 보는지 확인
> 핵심: 더 작은 key가 나중에 들어올 수 있는 일반 priority queue에는 구조 가정이 깨지기 때문이다.

## 한 줄 정리

Radix Heap은 monotone integer priority queue라는 강한 전제를 활용해, 현재 최소값과의 비트 차이 기반 bucket으로 일반 heap보다 더 싼 우선순위 처리를 노리는 자료구조다.
