---
schema_version: 3
title: Robin Hood Hashing
concept_id: data-structure/robin-hood-hashing
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- robin-hood-hashing
- open-addressing-probe-distance
- hash-table-tail-latency
aliases:
- Robin Hood Hashing
- open addressing
- probe distance
- displacement hashing
- backward shift deletion
- cache-friendly hash table
- tail latency lookup
symptoms:
- open addressing hash table에서 평균 probe count만 보고 긴 probe chain이 만든 lookup tail latency를 놓친다
- Robin Hood Hashing이 probe distance가 더 큰 key에게 우선권을 주어 variance를 줄이는 전략이라는 점을 이해하지 못한다
- deletion을 tombstone으로만 처리해 cluster 품질이 나빠지는 문제와 backward shift deletion 필요성을 고려하지 않는다
intents:
- definition
- deep_dive
prerequisites:
- data-structure/hashmap-internals
- data-structure/cache-aware-data-structure-layouts
next_docs:
- data-structure/cuckoo-hashing
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
linked_paths:
- contents/data-structure/hashmap-internals.md
- contents/data-structure/cache-aware-data-structure-layouts.md
- contents/data-structure/cuckoo-hashing.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
confusable_with:
- data-structure/hashmap-internals
- data-structure/cuckoo-hashing
- data-structure/cache-aware-data-structure-layouts
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
forbidden_neighbors: []
expected_queries:
- Robin Hood Hashing은 probe distance variance를 줄여 lookup tail latency를 어떻게 낮춰?
- open addressing에서 displacement가 큰 key에게 우선권을 주는 삽입 규칙은?
- backward shift deletion이 Robin Hood Hashing에서 중요한 이유는?
- linear probing, Robin Hood, Cuckoo Hashing, chaining을 cache locality와 tail latency로 비교해줘
- read-heavy hash table에서 load factor와 probe chain을 어떻게 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Robin Hood Hashing을 open addressing hash table에서 probe distance
  variance를 줄여 lookup tail latency를 낮추는 collision strategy로 설명한다.
  displacement, linear probing, backward shift deletion, cuckoo hashing과 비교한다.
---
# Robin Hood Hashing

> 한 줄 요약: Robin Hood Hashing은 probe sequence 길이를 평탄화해 open addressing 해시 테이블의 tail latency를 줄이려는 충돌 해결 전략이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Cache-Aware Data Structure Layouts](./cache-aware-data-structure-layouts.md)
> - [Cuckoo Hashing](./cuckoo-hashing.md)
> - [Treemap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)

> retrieval-anchor-keywords: robin hood hashing, open addressing, probe distance, displacement, linear probing, hash table variance, cache-friendly hash table, tail latency lookup, load factor hashing, backward shift deletion

## 핵심 개념

open addressing 해시 테이블에서는 충돌이 나면 다른 빈 slot을 찾는다.  
문제는 어떤 key는 probe가 매우 길어지고, 어떤 key는 짧아져 편차가 커진다는 점이다.

Robin Hood Hashing은 이 편차를 줄이려 한다.

- probe distance가 더 큰 원소가 우선권을 가진다
- 새 원소가 더 "가난한" slot 상황이면 기존 원소를 밀어낸다

즉 평균만이 아니라 **lookup probe 길이의 분산**을 줄이는 전략이다.

## 깊이 들어가기

### 1. 이름의 의미

Robin Hood라는 이름은 "부자에게서 뺏어 가난한 자에게 준다"는 비유다.

- 이미 home bucket에서 멀지 않은 원소
- home bucket에서 멀리 밀려난 원소

충돌 시 후자가 더 우선권을 갖는다.  
그래서 전체적으로 probe distance가 평탄화된다.

### 2. 왜 tail latency에 유리한가

단순 linear probing은 cache locality는 좋지만, 긴 cluster tail이 생길 수 있다.

Robin Hood는 삽입 과정에서 displacement를 균등화해  
극단적으로 긴 probe chain을 줄이는 데 도움을 준다.

즉 평균적인 한두 번 차이보다  
**최악에 가까운 lookup 길이를 눌러주는 효과**가 더 중요하다.

### 3. deletion이 구현의 핵심 난점이다

삭제를 단순 tombstone으로 처리하면 cluster 품질이 서서히 나빠질 수 있다.  
그래서 Robin Hood 구현은 자주 다음을 쓴다.

- backward shift deletion
- periodic rehash
- tombstone 관리

즉 삽입 논리보다 삭제 후 cluster를 어떻게 유지하느냐가 실전 품질을 좌우한다.

### 4. cuckoo / chaining과 어디서 갈리나

대략적인 감각:

- chaining: 구현이 단순하고 load factor 여유가 큼
- linear probing: locality 좋지만 cluster tail 위험
- robin hood: locality를 유지하며 probe variance를 줄임
- cuckoo: lookup bound가 짧지만 insert failure 관리 필요

즉 Robin Hood는 open addressing 진영 안에서  
locality와 예측성 사이의 균형점에 가깝다.

### 5. backend에서 어디에 맞나

read-heavy key lookup에서 cache locality와 probe variance가 모두 중요할 때 좋다.

- in-memory index
- dictionary table
- compact key/value cache
- read-mostly routing table

반대로 concurrent mutation이 많거나, delete-heavy workload라면  
다른 해시 전략이 더 편할 수 있다.

## 실전 시나리오

### 시나리오 1: compact in-memory dictionary

포인터 chasing이 많은 chaining hash보다  
contiguous array probing이 유리한 read-mostly 사전에 잘 맞는다.

### 시나리오 2: load factor를 높게 가져가고 싶은 경우

메모리가 타이트한 프로세스에서  
probe variance를 관리하며 높은 load factor를 노릴 때 검토할 수 있다.

### 시나리오 3: delete-heavy workload 함정

삭제가 많고 cleanup이 부실하면  
backward shift나 rebuild 없이는 품질이 빠르게 나빠질 수 있다.

### 시나리오 4: 부적합한 경우

삽입 실패를 받아들일 수 있으면 cuckoo,  
단순성과 thread-safe wrapping이 더 중요하면 다른 구조가 나을 수 있다.

## 코드로 보기

```java
public class RobinHoodHashing {
    private final Integer[] table;

    public RobinHoodHashing(int capacity) {
        this.table = new Integer[capacity];
    }

    public void put(int value) {
        int index = Math.floorMod(value, table.length);
        int distance = 0;

        while (true) {
            if (table[index] == null) {
                table[index] = value;
                return;
            }

            int occupant = table[index];
            int occupantDistance = probeDistance(index, occupant);
            if (occupantDistance < distance) {
                table[index] = value;
                value = occupant;
                distance = occupantDistance;
            }

            index = (index + 1) % table.length;
            distance++;
        }
    }

    private int probeDistance(int index, int value) {
        int home = Math.floorMod(value, table.length);
        return (index - home + table.length) % table.length;
    }
}
```

이 코드는 displacement 교환 감각만 보여준다.  
실전 구현은 resize, deletion, metadata 저장이 훨씬 중요하다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Robin Hood Hashing | probe variance를 줄여 예측성을 높인다 | deletion 관리가 복잡하다 | compact read-heavy open addressing table |
| Linear Probing | 매우 단순하고 locality가 좋다 | cluster tail이 길어질 수 있다 | 단순한 open addressing |
| Cuckoo Hashing | lookup bound가 짧다 | insert failure/rehash 관리가 필요하다 | bounded lookup path가 중요할 때 |
| Chaining Hash | 구현이 직관적이다 | pointer chasing과 메모리 locality가 약하다 | 범용성과 단순성이 더 중요할 때 |

중요한 질문은 "충돌을 어떻게 없앨까"보다  
"충돌이 생겼을 때 probe 길이 편차를 어떻게 줄일까"다.

## 꼬리질문

> Q: Robin Hood Hashing이 lookup tail latency를 줄이는 이유는 무엇인가요?
> 의도: 평균이 아니라 분산 제어를 이해하는지 확인
> 핵심: home bucket에서 멀리 밀려난 key를 우선시해 probe distance 분포를 평탄화하기 때문이다.

> Q: 왜 deletion이 핵심 난점인가요?
> 의도: open addressing에서 tombstone/cluster 유지 문제를 이해하는지 확인
> 핵심: 삭제 후 cluster continuity가 깨지면 probe 품질이 빠르게 나빠지기 때문이다.

> Q: Cuckoo Hashing과 감각 차이는 무엇인가요?
> 의도: open addressing 전략 간 trade-off를 구분하는지 확인
> 핵심: Robin Hood는 variance 완화, Cuckoo는 짧은 후보 경로 보장 쪽에 더 가깝다.

## 한 줄 정리

Robin Hood Hashing은 open addressing 해시 테이블에서 probe 길이의 편차를 줄여 cache-friendly lookup의 tail latency를 더 예측 가능하게 만드는 충돌 해결 전략이다.
