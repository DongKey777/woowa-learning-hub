# Bloom Filter vs Cuckoo Filter

> 한 줄 요약: Bloom Filter와 Cuckoo Filter는 둘 다 membership 검사용 확률적 구조지만, Cuckoo Filter는 삭제와 더 높은 공간 효율에서 강하고 Bloom Filter는 더 단순하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bloom Filter](./bloom-filter.md)
> - [Cuckoo Filter](./cuckoo-filter.md)
> - [Quotient Filter](./quotient-filter.md)
> - [Xor Filter](./xor-filter.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [LRU Cache Design](./lru-cache-design.md)

> retrieval-anchor-keywords: bloom filter, cuckoo filter, xor filter, membership filter, false positive, deletion, fingerprint, cuckoo hashing, approximate set, filter comparison, cache admission

## 핵심 개념

두 구조 모두 "원소가 집합에 있는가"를 빠르게 판정하는 전방 필터다.

- Bloom Filter: 비트 배열과 여러 해시
- Cuckoo Filter: 작은 fingerprint와 cuckoo hashing

둘 다 false positive는 있을 수 있지만 false negative는 피하려고 설계한다.

실무 선택은 보통 다음 기준으로 갈린다.

- 단순함이 중요하면 Bloom Filter
- 삭제가 필요하면 Cuckoo Filter
- 공간 효율과 높은 적재율이 중요하면 Cuckoo Filter를 검토

## 깊이 들어가기

### 1. Bloom Filter의 강점

Bloom Filter는 구현이 단순하다.

- 해시 여러 개를 계산한다.
- 비트만 세팅한다.
- 조회 시 모두 1이면 존재 가능성 있다고 본다.

빠르고, 작고, 이해하기 쉽다.

### 2. Cuckoo Filter의 핵심

Cuckoo Filter는 해시값의 짧은 fingerprint를 저장하고, cuckoo hashing처럼 두 후보 위치 사이를 재배치한다.

장점:

- 삭제가 쉽다
- 적재율이 상대적으로 높다
- false positive율을 잘 조절할 수 있다

단점:

- 재배치와 eviction 로직이 더 복잡하다
- 삽입 실패/재해시 처리가 필요하다

### 3. backend에서 어떤 차이가 생기나

캐시 전방 필터나 중복 요청 방지에서 삭제 가능성은 중요하다.

- 일시적 token
- 만료되는 idempotency key
- rolling window membership

이런 경우에는 삭제가 쉬운 Cuckoo Filter가 매력적이다.  
반면 단순 blacklist pre-check처럼 추가/조회 위주면 Bloom Filter가 충분하다.

### 4. 왜 둘 다 완전한 set이 아닌가

둘 다 "아마 없다"를 빨리 말해주려는 도구다.

- 정확한 membership이 필요하면 HashSet
- 빠른 전방 필터링이 필요하면 probabilistic filter

즉 목적 자체가 다르다.

## 실전 시나리오

### 시나리오 1: 캐시 admission

캐시에 넣을 가치가 있는 key인지 앞단에서 걸러낼 때 쓸 수 있다.

### 시나리오 2: 중복 요청 보호

짧은 기간 동안 같은 요청이 반복되는 것을 막을 때, 만료 정책이 있으면 Cuckoo Filter가 편하다.

### 시나리오 3: 크롤링/탐색

이미 본 URL을 빠르게 배제하고 싶다면 Bloom Filter가 단순하고 좋다.

### 시나리오 4: 오판

정확한 삭제와 정확한 membership이 함께 필요하면 probabilistic filter만으로는 부족하다.

## 코드로 보기

```java
import java.util.BitSet;

public class BloomVsCuckooNotes {
    // 설명용 스케치: 실제 Cuckoo Filter는 fingerprint와 재배치가 필요하다.
    static final class BloomFilter {
        private final BitSet bits;
        private final int size;

        BloomFilter(int size) {
            this.bits = new BitSet(size);
            this.size = size;
        }

        void add(String value) {
            bits.set(index(value, 0));
            bits.set(index(value, 1));
        }

        boolean mightContain(String value) {
            return bits.get(index(value, 0)) && bits.get(index(value, 1));
        }

        private int index(String value, int seed) {
            return Math.floorMod(value.hashCode() ^ (seed * 0x9e3779b9), size);
        }
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bloom Filter | 단순하고 널리 검증됐다 | 삭제가 어렵다 | 기본 membership 필터 |
| Cuckoo Filter | 삭제 가능, 적재율이 좋다 | 구현이 더 복잡하다 | 만료/삭제가 필요한 필터 |
| HashSet | 정확하다 | 메모리가 더 든다 | 소규모 정확 판정 |

실무는 보통 "단순한가"와 "삭제가 필요한가"로 갈린다.

## 꼬리질문

> Q: Cuckoo Filter가 Bloom보다 나은 경우는?
> 의도: 삭제와 적재율 관점 이해 확인
> 핵심: 삭제가 필요하거나 공간 효율이 더 중요할 때다.

> Q: Bloom Filter는 왜 여전히 많이 쓰나?
> 의도: 단순성과 운영 안정성 이해 확인
> 핵심: 구현이 단순하고 충분히 빠르기 때문이다.

> Q: 둘 다 false positive가 있는 이유는?
> 의도: 확률적 필터의 본질 이해 확인
> 핵심: 정보 일부를 압축해서 저장하기 때문이다.

## 한 줄 정리

Bloom Filter는 단순한 membership 필터이고, Cuckoo Filter는 삭제와 공간 효율을 더 고려한 membership 필터다.
