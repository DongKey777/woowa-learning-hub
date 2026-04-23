# Cuckoo Hashing

> 한 줄 요약: Cuckoo Hashing은 두 개 이상의 후보 위치를 두고 원소를 계속 밀어내며 저장하는 고성능 해시 테이블 기법이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Cuckoo Filter](./cuckoo-filter.md)
> - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
> - [Consistent Hashing Ring](./consistent-hashing-ring.md)

> retrieval-anchor-keywords: cuckoo hashing, multiple hash functions, relocation, eviction chain, hash table, load factor, rehash, worst-case lookup, constant lookup, cache-friendly hash

## 핵심 개념

Cuckoo Hashing은 각 key가 여러 후보 버킷 중 하나에 들어가도록 설계한다.  
삽입이 충돌하면 기존 원소를 다른 후보 위치로 "쫓아낸다"는 점에서 이름이 왔다.

핵심 장점:

- lookup이 빠르다
- 후보 버킷만 보면 된다

핵심 어려움:

- 삽입 시 재배치가 연쇄적으로 일어날 수 있다
- cycle이 생기면 rehash가 필요할 수 있다

## 깊이 들어가기

### 1. 왜 lookup이 빠른가

key는 미리 정해진 후보 위치만 확인하면 된다.

- 위치가 적다
- 버킷 내부 탐색이 짧다
- 조건이 맞으면 거의 상수 시간에 가깝다

### 2. eviction chain

새 key가 들어갈 자리가 없으면 기존 key를 다른 후보 버킷으로 옮긴다.

이 과정이 반복되면 하나의 삽입이 여러 개의 이동을 유발할 수 있다.

### 3. rehash가 필요한 이유

재배치가 무한히 돌 수 있는 cycle 구조가 생기면, 기존 해시 함수 조합으로는 더 이상 깔끔하게 넣을 수 없다.

이때는 새 hash seed로 테이블 전체를 다시 짜는 rehash를 한다.

### 4. backend에서의 감각

Cuckoo Hashing은 빠른 membership과 lookup이 중요한 상황에서 유용하다.

- cache index
- dedup set
- routing table
- high-throughput key lookup

## 실전 시나리오

### 시나리오 1: 빠른 조회

lookup 경로가 짧아야 하는 고속 시스템에서 유용하다.

### 시나리오 2: 쓰기 폭주 주의

삽입이 많으면 eviction chain과 rehash 비용이 문제될 수 있다.

### 시나리오 3: 오판

삽입이 빈번하고 테이블이 자주 가득 차는 환경에서는 운영이 까다롭다.

### 시나리오 4: 필터와의 연결

Cuckoo Filter의 기반 아이디어가 cuckoo hashing이므로, 둘은 자연스럽게 연결된다.

## 코드로 보기

```java
public class CuckooHashing {
    private final Integer[] table1;
    private final Integer[] table2;

    public CuckooHashing(int capacity) {
        this.table1 = new Integer[capacity];
        this.table2 = new Integer[capacity];
    }

    public boolean insert(int key) {
        int cur = key;
        for (int i = 0; i < table1.length * 2; i++) {
            int h1 = h1(cur);
            if (table1[h1] == null) {
                table1[h1] = cur;
                return true;
            }
            int tmp = table1[h1];
            table1[h1] = cur;
            cur = tmp;

            int h2 = h2(cur);
            if (table2[h2] == null) {
                table2[h2] = cur;
                return true;
            }
            tmp = table2[h2];
            table2[h2] = cur;
            cur = tmp;
        }
        return false; // rehash 필요 가능
    }

    public boolean contains(int key) {
        return table1[h1(key)] != null && table1[h1(key)] == key
            || table2[h2(key)] != null && table2[h2(key)] == key;
    }

    private int h1(int key) {
        return Math.floorMod(Integer.hashCode(key), table1.length);
    }

    private int h2(int key) {
        return Math.floorMod(Integer.rotateLeft(key, 16), table2.length);
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Cuckoo Hashing | lookup이 빠르고 후보가 명확하다 | 삽입이 복잡하고 rehash가 필요할 수 있다 | 읽기 중심, 고속 조회 |
| Linear Probing | 구현이 쉽다 | clustering 문제가 생긴다 | 단순한 해시 테이블 |
| Separate Chaining | 삽입이 편하다 | 버킷 내부 길이가 길어질 수 있다 | 일반 범용 테이블 |

## 꼬리질문

> Q: 왜 cuckoo hashing이라고 부르나?
> 의도: eviction 개념을 기억하는지 확인
> 핵심: 새 원소가 기존 원소를 밀어내는 방식이 뻐꾸기처럼 보이기 때문이다.

> Q: rehash는 언제 필요한가?
> 의도: cycle과 삽입 실패를 이해하는지 확인
> 핵심: 계속 밀어내도 자리가 안 나는 경우다.

> Q: lookup이 왜 빠른가?
> 의도: 후보 버킷 제한 구조를 이해하는지 확인
> 핵심: 확인할 위치가 소수로 제한되기 때문이다.

## 한 줄 정리

Cuckoo Hashing은 여러 후보 위치 사이에서 원소를 밀어내며 저장해 빠른 조회를 확보하는 해시 테이블 기법이다.
