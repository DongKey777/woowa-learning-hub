# Quotient Filter

> 한 줄 요약: Quotient Filter는 fingerprint를 quotient/remainder로 나눠 저장하는 approximate membership 구조로, Bloom보다 locality가 좋고 일부 동적 운영도 가능한 compact filter다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bloom Filter](./bloom-filter.md)
> - [Cuckoo Filter](./cuckoo-filter.md)
> - [Xor Filter](./xor-filter.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)

> retrieval-anchor-keywords: quotient filter, approximate membership, quotient remainder filter, compact hash filter, probabilistic set, cache-friendly filter, dynamic membership filter, bloom alternative, fingerprint filter, compact prefilter

## 핵심 개념

Quotient Filter도 approximate membership filter다.  
전체 key 대신 hash fingerprint만 저장한다는 점은 Cuckoo Filter와 비슷하지만, 저장 방식은 다르다.

핵심 아이디어:

- 해시 fingerprint를 `quotient`와 `remainder`로 나눈다
- quotient는 bucket 위치를 뜻한다
- remainder는 bucket 근처에 압축 저장한다

즉 해시 테이블과 run-length/cluster 개념이 섞인 듯한 구조로,  
membership prefilter를 **메모리 지역성 좋게 저장**하려는 발상이다.

## 깊이 들어가기

### 1. quotient / remainder 분리가 왜 중요한가

fingerprint 전체를 그대로 위치 계산과 저장에 같이 쓰면 비효율이 생길 수 있다.  
Quotient Filter는 이를 두 부분으로 나눈다.

- quotient: "어느 버킷 그룹인가"
- remainder: "그 그룹 안에서 어떤 값인가"

이렇게 하면 비슷한 quotient를 가진 항목이 물리적으로 가까운 곳에 모인다.  
그래서 lookup과 scan이 cache-friendly해질 수 있다.

### 2. metadata bit가 구조를 유지한다

Quotient Filter는 remainder만 저장하는 것이 아니라,  
각 slot에 몇 개의 상태 bit를 두어 cluster/run 경계를 추적한다.

보통 이런 정보가 필요하다.

- 이 slot이 비어 있는가
- 원래 여기 속한 원소가 맞는가
- run이 이어지는 중인가

즉 단순 비트 배열보다 구조 유지 메타데이터가 중요하다.  
그래서 구현은 Bloom보다 복잡하지만 locality는 더 좋을 수 있다.

### 3. Bloom / Cuckoo / Xor와 어디서 갈리나

대략적인 선택 감각은 이렇다.

- Bloom: 가장 단순
- Cuckoo: deletion과 동적 운영
- Xor: 정적 집합에서 매우 compact
- Quotient: locality 좋은 fingerprint filter, 일부 동적 운영 가능

Quotient Filter는 특히 disk/page 친화 구조나  
순차 scan locality가 중요한 곳에서 매력적일 수 있다.

### 4. backend에서 어디에 맞나

다음처럼 memory page / cache line locality가 중요한 membership prefilter에서 어울린다.

- SSD-backed on-disk filter
- compact in-memory negative lookup filter
- snapshot 기반 membership index

Bloom처럼 여러 random bit를 건드리는 대신,  
상대적으로 좁은 영역을 검사하는 패턴을 만들기 쉽다는 점이 장점이다.

### 5. 한계와 운영 포인트

Quotient Filter도 만능은 아니다.

- cluster가 길어지면 lookup이 느려질 수 있다
- load factor 관리가 중요하다
- resize / rebuild 전략이 필요하다

즉 구조적 locality를 얻는 대신,  
metadata와 cluster maintenance 복잡도를 받아들여야 한다.

## 실전 시나리오

### 시나리오 1: on-disk membership prefilter

random bit 접근이 비싼 저장장치에서는  
좁은 구간 scan 중심 구조가 Bloom보다 더 매력적일 수 있다.

### 시나리오 2: compact negative lookup filter

메모리 예산이 타이트한 in-memory filter에서  
동적 업데이트도 어느 정도 필요하다면 검토해볼 수 있다.

### 시나리오 3: immutable snapshot filter

세그먼트나 snapshot 단위로 membership filter를 유지할 때  
cache locality가 중요한 경우 잘 맞는다.

### 시나리오 4: 부적합한 경우

가장 단순한 구현이 필요하면 Bloom,  
정적 집합에서 극한 압축이 중요하면 Xor Filter가 더 나을 수 있다.

## 코드로 보기

```java
public class QuotientFilterSketch {
    private final short[] remainders;
    private final boolean[] occupied;
    private final boolean[] shifted;

    public QuotientFilterSketch(int capacity) {
        this.remainders = new short[capacity];
        this.occupied = new boolean[capacity];
        this.shifted = new boolean[capacity];
    }

    public void add(String key) {
        int hash = key.hashCode();
        int quotient = Math.floorMod(hash >>> 8, remainders.length);
        short remainder = (short) (hash & 0xFF);

        occupied[quotient] = true;
        int slot = quotient;
        while (shifted[slot] && remainders[slot] != 0) {
            slot = (slot + 1) % remainders.length;
        }
        remainders[slot] = remainder;
        shifted[slot] = slot != quotient;
    }
}
```

이 코드는 quotient/remainder 감각만 보여준다.  
실제 Quotient Filter는 run boundary 추적과 lookup/delete가 훨씬 더 정교하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Quotient Filter | locality가 좋고 compact하며 일부 동적 운영이 가능하다 | metadata와 cluster 관리가 복잡하다 | cache-friendly membership prefilter |
| Bloom Filter | 단순하고 구현이 쉽다 | random bit 접근이 많다 | 일반적인 prefilter |
| Cuckoo Filter | deletion이 편하고 동적 운영이 가능하다 | relocation/insert failure 관리가 필요하다 | mutable membership filter |
| Xor Filter | 정적 집합에서 매우 compact하다 | 동적 업데이트가 어렵다 | immutable snapshot filter |

중요한 질문은 "필터를 얼마나 자주 바꾸는가"와 "memory locality가 얼마나 중요한가"다.

## 꼬리질문

> Q: Quotient Filter가 Bloom보다 나은 경우는 언제인가요?
> 의도: locality와 구현 단순성 trade-off 이해 확인
> 핵심: random bit access보다 좁은 범위 scan locality가 더 중요한 환경일 때다.

> Q: 왜 metadata bit가 중요한가요?
> 의도: remainder 배열만으로는 구조 복원이 안 된다는 점 이해 확인
> 핵심: cluster와 run 경계를 알아야 lookup과 delete가 가능하기 때문이다.

> Q: Xor Filter와 가장 큰 차이는 무엇인가요?
> 의도: 정적/동적 compact filter 구분 확인
> 핵심: Xor Filter는 정적 집합 지향이고, Quotient Filter는 더 동적인 운영과 locality 쪽에 가깝다.

## 한 줄 정리

Quotient Filter는 quotient/remainder 분리와 메타데이터를 이용해 locality 좋은 approximate membership을 제공하는 compact filter로, Bloom과 Xor 사이의 운영적 절충안에 가깝다.
