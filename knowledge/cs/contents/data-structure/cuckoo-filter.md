---
schema_version: 3
title: Cuckoo Filter
concept_id: data-structure/cuckoo-filter
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- cuckoo-filter
- approximate-membership
- deletion-friendly-filter
aliases:
- Cuckoo Filter
- approximate membership filter
- fingerprint bucket filter
- deletion-friendly membership filter
- cuckoo filter false positive
- alternate bucket fingerprint
- cache admission filter
symptoms:
- 삭제가 가능하다는 이유로 Cuckoo Filter를 exact set처럼 보고 false positive가 있는 prefilter라는 사실을 놓친다
- fingerprint만 저장하는 공간 절약과 false positive trade-off를 HashSet membership과 비교하지 못한다
- bucket relocation과 alternate index 계산이 Cuckoo Hashing에서 온다는 연결을 이해하지 못한다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/bloom-filter-vs-cuckoo-filter
- data-structure/cuckoo-hashing
next_docs:
- data-structure/bloom-filter
- data-structure/bloom-filter-vs-cuckoo-filter
- data-structure/quotient-filter
- data-structure/xor-filter
- data-structure/cuckoo-hashing
linked_paths:
- contents/data-structure/hash-table-basics.md
- contents/data-structure/applied-data-structures-overview.md
- contents/data-structure/bloom-filter.md
- contents/data-structure/bloom-filter-vs-cuckoo-filter.md
- contents/data-structure/quotient-filter.md
- contents/data-structure/xor-filter.md
- contents/data-structure/sketch-filter-selection-playbook.md
- contents/data-structure/cuckoo-hashing.md
confusable_with:
- data-structure/bloom-filter
- data-structure/bloom-filter-vs-cuckoo-filter
- data-structure/cuckoo-hashing
- data-structure/quotient-filter
- data-structure/xor-filter
forbidden_neighbors: []
expected_queries:
- Cuckoo Filter는 Bloom Filter와 달리 왜 삭제가 더 자연스러워?
- fingerprint만 저장하는 Cuckoo Filter가 false positive를 가질 수밖에 없는 이유는?
- Cuckoo Filter에서 alternate bucket과 relocation은 어떻게 동작해?
- 삭제 가능한 membership prefilter를 exact HashSet처럼 쓰면 왜 위험해?
- Cuckoo Hashing과 Cuckoo Filter의 관계를 설명해줘
contextual_chunk_prefix: |
  이 문서는 Cuckoo Filter를 fingerprint bucket과 alternate bucket relocation을
  쓰는 approximate membership prefilter로 설명한다. 삭제 가능성, false
  positive, exact path 필요성, Cuckoo Hashing과의 관계를 다룬다.
---
# Cuckoo Filter

> 한 줄 요약: Cuckoo Filter는 짧은 fingerprint를 bucket에 저장하는 approximate membership 구조로, Bloom Filter보다 복잡하지만 삭제와 높은 적재율을 더 자연스럽게 지원한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [해시 테이블 기초](./hash-table-basics.md)
> - [응용 자료 구조 개요](./applied-data-structures-overview.md)
> - [Bloom Filter](./bloom-filter.md)
> - [Bloom Filter vs Cuckoo Filter](./bloom-filter-vs-cuckoo-filter.md)
> - [Quotient Filter](./quotient-filter.md)
> - [Xor Filter](./xor-filter.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)
> - [Cuckoo Hashing](./cuckoo-hashing.md)

> retrieval-anchor-keywords: cuckoo filter, approximate membership, exact membership, exact vs approximate membership, exact path vs prefilter, 정답 경로, 선필터, fingerprint bucket, deletion, cuckoo hashing, false positive, load factor, eviction chain, cache admission, idempotency key filter

## 먼저 고르는 법

> `decision box`
> - 정답이 바로 필요하면 Cuckoo Filter가 아니라 `HashSet/HashMap` 같은 exact 경로로 간다.
> - Cuckoo Filter도 Bloom Filter와 마찬가지로 "정답기"가 아니라 앞단 선필터다.
> - `mightContain=true`면 통과 후보일 뿐이고, 최종 판단은 DB·캐시·exact set이 맡는다.
> - 삭제나 만료가 자주 필요하면 Bloom보다 Cuckoo Filter 쪽이 자연스럽다.
> - 결제, 권한, 중복 차단처럼 false positive도 비용이 큰 경로에는 단독 사용하지 않는다.

| 질문 | 먼저 고를 축 |
|---|---|
| "정말 존재하나요?" | exact membership: `HashSet/HashMap`, DB unique/index |
| "삭제 가능한 선필터가 필요한가요?" | approximate prefilter: `Cuckoo Filter` |

## 핵심 개념

Cuckoo Filter는 "원소 전체"를 저장하지 않고, 짧은 fingerprint만 bucket에 저장한다.
각 원소는 두 후보 bucket 중 하나에 들어가고, 자리가 없으면 기존 fingerprint를 밀어내며 재배치한다.

핵심 감각은 이렇다.

- Bloom Filter처럼 approximate membership이다
- fingerprint를 저장하므로 삭제가 가능하다
- cuckoo hashing처럼 relocation이 있다

따라서 아주 단순한 구조는 아니지만, **삭제 가능한 membership filter**가 필요할 때 매력적이다.

자주 생기는 오해는 "삭제가 되니까 exact set 비슷하다"라고 보는 것이다.
삭제 가능성은 좋아졌지만, 여전히 역할은 **정답 경로 앞의 approximate filter**다.

## 깊이 들어가기

### 1. 왜 fingerprint만 저장하나

전체 key를 저장하면 HashSet에 가까워져 메모리 이점이 줄어든다.
그래서 보통 해시값의 일부 비트만 떼어 fingerprint로 둔다.

- 공간을 아낀다
- false positive를 감수한다
- false negative는 피하려고 설계한다

즉 Cuckoo Filter는 "정확한 set"이 아니라 **작은 흔적만 남기는 membership 구조**다.

### 2. bucket 두 개와 alternate index가 핵심이다

보통 원소는 두 bucket 후보를 가진다.

- `i1 = hash(key)`
- `i2 = i1 XOR hash(fingerprint)`

fingerprint만 있더라도 다른 후보 위치를 다시 계산할 수 있다.
이 성질 덕분에 bucket에서 fingerprint를 하나 뽑아 다른 후보 bucket으로 밀어내는 relocation이 가능하다.

### 3. 삭제가 왜 자연스러운가

Bloom Filter는 비트 하나를 여러 원소가 공유해 삭제가 어렵다.
Cuckoo Filter는 bucket 안에 fingerprint "항목"이 따로 있으므로, 찾은 fingerprint를 지우면 된다.

물론 완전히 정확한 삭제는 아니다.
동일 fingerprint 충돌 가능성은 있지만, 실무적으로는 삭제 가능한 approximate set이라는 장점이 크다.

### 4. 삽입 실패와 rehash를 받아들여야 한다

load factor가 높아질수록 relocation chain이 길어질 수 있다.
정해진 횟수 안에 자리를 못 찾으면 삽입 실패로 보고 재구성(rebuild)이나 확장을 해야 한다.

즉 Cuckoo Filter는 다음을 관리해야 한다.

- bucket 크기
- fingerprint 길이
- 최대 eviction 횟수
- table resize / rebuild 전략

이 운영 복잡도 때문에 "항상 Bloom보다 낫다"가 아니라, **삭제 필요성과 공간 이점을 위해 복잡도를 사는 구조**라고 보는 편이 맞다.

## 실전 시나리오

### 시나리오 1: 만료되는 idempotency key 전방 필터

짧은 기간 동안 중복 요청을 걸러내되, 기간이 지나면 제거해야 한다면
Cuckoo Filter가 Bloom Filter보다 더 자연스럽다.

### 시나리오 2: cache admission / negative cache 보호

잠깐 등장했다 사라지는 key를 전방 필터링할 때는
삭제와 재구성이 쉬운 쪽이 운영상 편하다.

### 시나리오 3: rolling window replay protection

최근 N분간 본 token이나 request key를 approximate하게 기억하고,
window 만료 시 제거하고 싶다면 Cuckoo Filter가 잘 맞는다.

### 시나리오 4: 부적합한 경우

정확 membership이 필요하거나, 삽입 실패 처리 자체가 부담이면
HashSet이나 Bloom Filter + 다른 만료 전략이 더 단순할 수 있다.

## 코드로 보기

```java
import java.util.concurrent.ThreadLocalRandom;

public class CuckooFilter {
    private static final int BUCKET_SIZE = 4;
    private static final int MAX_KICKS = 32;

    private final short[][] table;
    private final int bucketCount;

    public CuckooFilter(int bucketCount) {
        this.bucketCount = bucketCount;
        this.table = new short[bucketCount][BUCKET_SIZE];
    }

    public boolean add(String key) {
        short fp = fingerprint(key);
        int i1 = index(hash(key));
        int i2 = alternateIndex(i1, fp);

        if (insertIntoBucket(i1, fp) || insertIntoBucket(i2, fp)) {
            return true;
        }

        int index = ThreadLocalRandom.current().nextBoolean() ? i1 : i2;
        short current = fp;
        for (int kick = 0; kick < MAX_KICKS; kick++) {
            int slot = ThreadLocalRandom.current().nextInt(BUCKET_SIZE);
            short evicted = table[index][slot];
            table[index][slot] = current;
            current = evicted;
            index = alternateIndex(index, current);
            if (insertIntoBucket(index, current)) {
                return true;
            }
        }
        return false;
    }

    public boolean mightContain(String key) {
        short fp = fingerprint(key);
        int i1 = index(hash(key));
        int i2 = alternateIndex(i1, fp);
        return contains(i1, fp) || contains(i2, fp);
    }

    public boolean delete(String key) {
        short fp = fingerprint(key);
        int i1 = index(hash(key));
        int i2 = alternateIndex(i1, fp);
        return remove(i1, fp) || remove(i2, fp);
    }

    private boolean insertIntoBucket(int index, short fp) {
        for (int i = 0; i < BUCKET_SIZE; i++) {
            if (table[index][i] == 0) {
                table[index][i] = fp;
                return true;
            }
        }
        return false;
    }

    private boolean contains(int index, short fp) {
        for (int i = 0; i < BUCKET_SIZE; i++) {
            if (table[index][i] == fp) {
                return true;
            }
        }
        return false;
    }

    private boolean remove(int index, short fp) {
        for (int i = 0; i < BUCKET_SIZE; i++) {
            if (table[index][i] == fp) {
                table[index][i] = 0;
                return true;
            }
        }
        return false;
    }

    private int alternateIndex(int index, short fp) {
        return index(hash(index ^ fp));
    }

    private int index(int hash) {
        return Math.floorMod(hash, bucketCount);
    }

    private int hash(Object value) {
        return value.hashCode() * 0x9e3779b9;
    }

    private short fingerprint(String key) {
        short fp = (short) (hash(key) & 0xFFFF);
        return fp == 0 ? 1 : fp;
    }
}
```

이 구현은 개념 설명용이다.
실전에서는 resize, stash, hash 품질, load factor 임계치까지 함께 설계해야 한다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Cuckoo Filter | 삭제가 가능하고 공간 효율이 좋다 | 삽입 실패와 relocation 관리가 필요하다 | 만료/삭제가 필요한 membership filter |
| Bloom Filter | 단순하고 구현 리스크가 낮다 | 삭제가 어렵다 | 추가/조회 위주 전방 필터 |
| Counting Bloom Filter | 삭제 가능하다 | counter 메모리와 업데이트 비용이 늘어난다 | 삭제가 필요하지만 cuckoo 복잡도는 피하고 싶을 때 |
| HashSet | 정확하다 | 메모리 사용량이 크다 | 정확 membership이 절대적일 때 |

질문은 "필터가 필요한가" 다음에 "삭제가 필요한가"다.

## 꼬리질문

> Q: Cuckoo Filter가 Bloom Filter보다 유리한 가장 큰 이유는?
> 의도: 구조적 차이를 운영 관점으로 연결하는지 확인
> 핵심: fingerprint 항목을 개별적으로 저장해 삭제가 가능하다는 점이다.

> Q: 왜 삽입 실패가 생기나요?
> 의도: relocation 기반 구조 이해 확인
> 핵심: 두 후보 bucket 사이에서 재배치를 반복해도 빈 자리를 못 찾을 수 있기 때문이다.

> Q: false positive는 왜 생기나요?
> 의도: fingerprint 저장의 본질 이해 확인
> 핵심: 전체 key가 아니라 짧은 fingerprint만 저장하기 때문이다.

## 한 줄 정리

Cuckoo Filter는 fingerprint와 relocation을 이용해, 삭제 가능한 approximate membership을 작은 메모리로 제공하는 실전형 확률 자료구조다.
