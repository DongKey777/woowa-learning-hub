# Bloom Filter

> 한 줄 요약: 메모리를 적게 쓰면서 "아마 없다"를 빠르게 걸러내는 확률적 집합 검사 구조다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [LRU Cache Design](./lru-cache-design.md)
> - [Cuckoo Filter](./cuckoo-filter.md)
> - [Quotient Filter](./quotient-filter.md)
> - [Xor Filter](./xor-filter.md)
> - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)

> retrieval-anchor-keywords: bloom filter, approximate membership, bitset filter, false positive, no false negative, counting bloom filter, cache admission, negative lookup, probabilistic set, idempotency key filter

## 핵심 개념

Bloom Filter는 원소가 집합에 `있을 수도 있다` 또는 `없다`를 판정하는 자료구조다.

특징은 다음과 같다.

- `false positive`는 있을 수 있다.
- `false negative`는 없다.
- 원소를 정확히 저장하지 않고 비트 배열만 사용한다.
- `membership check`가 매우 빠르다.

즉, "없음"을 빠르게 확정하는 데 강하고, "있음"은 한 번 더 확인해야 할 수 있다.

이 구조는 정확한 집합보다 더 적은 메모리로 필터링할 때 유리하다.

## 깊이 들어가기

### 1. 어떻게 동작하는가

원소를 여러 해시 함수에 통과시켜 나온 위치의 비트를 `1`로 만든다.
조회할 때는 같은 위치의 비트가 전부 `1`이면 `있을 수도 있다`라고 판단한다.

```text
insert(x):
  h1(x), h2(x), h3(x) -> bits set to 1

mightContain(x):
  h1(x), h2(x), h3(x) -> any bit = 0 ? definitely not present
```

비트 하나라도 `0`이면 그 원소는 절대 없다.

### 2. 왜 false positive가 생기는가

서로 다른 원소가 우연히 같은 비트 위치를 공유할 수 있기 때문이다.
충돌이 누적되면 `"있다"` 판정이 더 자주 나온다.

그래서 Bloom Filter는 다음 두 값의 균형이 중요하다.

- 비트 배열 크기
- 해시 함수 개수

### 3. 삭제가 왜 어려운가

단순 Bloom Filter는 삭제 시 해당 비트를 `0`으로 되돌리면 안 된다.
다른 원소도 그 비트를 사용하고 있을 수 있기 때문이다.

삭제가 필요하면 보통 `Counting Bloom Filter`를 쓴다.

---

## 실전 시나리오

### 시나리오 1: DB 조회 전에 빠르게 걸러내기

존재하지 않는 키를 자주 조회하는 서비스에서,
먼저 Bloom Filter로 `없음`을 확정하고 DB를 아낄 수 있다.

예:

- 해시 충돌이 많지 않은 idempotency key 검사
- 크롤러의 visited URL 필터
- 악성 요청의 사전 필터링

### 시나리오 2: 캐시 미스 전방 필터

대규모 읽기 시스템에서 "이 키는 절대 없다"를 빨리 판단하면 캐시/DB에 불필요한 요청을 줄일 수 있다.

다만 false positive가 있으면 결국 DB를 한 번 더 볼 수 있으므로,
Bloom Filter는 캐시를 대체하는 것이 아니라 앞단의 게이트로 보는 편이 맞다.

---

## 코드로 보기

```java
import java.util.BitSet;

public class BloomFilter {
    private final BitSet bits;
    private final int size;
    private final int hashCount;

    public BloomFilter(int size, int hashCount) {
        this.bits = new BitSet(size);
        this.size = size;
        this.hashCount = hashCount;
    }

    public void add(String value) {
        for (int i = 0; i < hashCount; i++) {
            bits.set(indexOf(value, i));
        }
    }

    public boolean mightContain(String value) {
        for (int i = 0; i < hashCount; i++) {
            if (!bits.get(indexOf(value, i))) {
                return false;
            }
        }
        return true;
    }

    private int indexOf(String value, int seed) {
        int hash = value.hashCode() ^ (seed * 0x9e3779b9);
        return Math.floorMod(hash, size);
    }
}
```

이 구현은 설명용이다.
실무에서는 해시 분포, 적정 비트 수, false positive 비율을 같이 계산해야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Bloom Filter | 메모리 효율이 좋고 조회가 빠름 | false positive가 있음 | "없음" 판정이 중요할 때 |
| HashSet | 정확하고 단순함 | 메모리를 더 씀 | 정확도가 최우선일 때 |
| Counting Bloom Filter | 삭제 가능 | 메모리와 구현 복잡도 증가 | 삭제가 필요한 필터링일 때 |
| Trie | prefix 탐색에 강함 | 공간을 많이 씀 | 문자열 prefix 패턴일 때 |

핵심 판단 기준은 "정확한 존재 확인"이 필요한가, 아니면 "없음만 빠르게 걸러도 되는가"다.

---

## 꼬리질문

> Q: false positive가 허용되는데 왜 실무에서 쓰는가?
> 의도: 확률적 자료구조의 비용 대비 효과를 이해하는지 확인
> 핵심: 정확도보다 메모리와 전방 필터링 효율이 더 중요한 구간이 있다.

> Q: 삭제가 필요하면 왜 그냥 비트를 내리면 안 되는가?
> 의도: 비트 공유 구조의 본질 이해 확인
> 핵심: 하나의 비트는 여러 원소가 공유할 수 있다.

> Q: 몇 개의 해시 함수를 쓰는 게 좋은가?
> 의도: 구현 암기가 아니라 false positive trade-off를 보는가
> 핵심: 비트 배열 크기와 예상 원소 수에 따라 최적점이 달라진다.

## 한 줄 정리

Bloom Filter는 정확한 집합이 아니라, `없음`을 빠르게 판정하기 위한 확률적 전방 필터다.
