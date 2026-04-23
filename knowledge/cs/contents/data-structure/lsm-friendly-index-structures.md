# LSM-Friendly Index Structures

> 한 줄 요약: LSM 계열 저장소는 하나의 거대한 트리보다 memtable, sparse block index, fence pointer, Bloom filter 같은 작은 구조를 조합해 write path와 read path를 나눈다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Skip List](./skip-list.md)
> - [Bloom Filter](./bloom-filter.md)
> - [Finite State Transducer](./finite-state-transducer.md)
> - [Adaptive Radix Tree](./adaptive-radix-tree.md)

> retrieval-anchor-keywords: lsm friendly index structures, memtable skip list, sstable block index, fence pointer, bloom filter per sstable, index summary, prefix compressed block, lsm read path, write optimized index, sparse index

## 핵심 개념

LSM 계열 저장소는 "한 자료구조로 모든 걸 해결"하지 않는다.  
쓰기와 읽기의 위치가 다르기 때문에, 각 단계에 다른 구조를 붙인다.

- memtable: 쓰기 흡수
- SSTable data block: 정렬된 불변 블록
- sparse block index / fence pointer: 블록 탐색
- Bloom filter: negative lookup 절약

즉 LSM-friendly index는 단일 트리 이름이 아니라  
**write path와 read path에 맞는 작은 구조들의 조합**이다.

## 깊이 들어가기

### 1. memtable은 mutable ordered structure가 필요하다

쓰기 경로에서는 계속 insert가 일어난다.  
그래서 memtable은 보통 mutable ordered structure를 쓴다.

- Skip List
- balanced tree
- ART-like in-memory ordered index

요구사항:

- range scan 가능
- flush 시 정렬 순서 유지
- concurrent insert가 비교적 쉬울 것

즉 exact point lookup만이 아니라,  
나중에 SSTable로 정렬 flush하기 쉬운 구조가 중요하다.

### 2. SSTable 내부는 sparse index가 더 중요하다

불변 파일로 내려가면 모든 key를 메모리에 둘 필요가 없다.  
대신 block 단위 탐색 포인트만 들고 있으면 된다.

- fence pointer
- sparse block index
- restart point
- prefix-compressed key block

즉 read path는:

1. 어떤 block에 key가 있을지 좁히고
2. 그 block 안에서만 더 세밀히 찾는다

이 단계형 탐색이 핵심이다.

### 3. Bloom filter는 read amplification 완화 장치다

LSM은 여러 level / SSTable을 볼 수 있으므로 negative lookup이 비싸다.  
그래서 파일별/level별 Bloom filter가 자주 붙는다.

- 이 파일엔 아예 없음을 빨리 말함
- disk/page read를 줄임

즉 Bloom filter는 주 인덱스가 아니라  
**read path 비용을 깎는 보조 구조**다.

### 4. index summary와 page cache 관점이 중요하다

아주 큰 SSTable에서는 sparse index조차 전부 메모리에 올리기 부담될 수 있다.  
그래서 상위 요약(summary)을 한 층 더 두기도 한다.

- top-level summary
- sampled key directory
- cache-aware block index

즉 "정확히 찾는 구조"보다  
"어느 정도만 메모리에 두고 disk/page 접근을 줄일 것인가"가 더 중요해진다.

### 5. backend에서 어디에 맞나

LSM-friendly index 구조는 write-heavy 저장소 전반에 적용되는 사고방식이다.

- 로그성 이벤트 저장
- 시계열 ingest
- 대규모 key-value store
- immutable segment 기반 analytics

핵심은 point lookup뿐 아니라  
flush, compaction, read amplification, cache residency를 함께 보는 것이다.

## 실전 시나리오

### 시나리오 1: write-heavy key-value store

memtable은 skip list로 삽입을 받고,  
flush 후엔 sparse block index + Bloom filter로 read path를 줄이는 구성이 자연스럽다.

### 시나리오 2: immutable analytics segment

segment는 prefix-compressed block과 fence pointer를 두고,  
term dictionary는 FST로 줄이는 식의 조합이 가능하다.

### 시나리오 3: cache 예산이 타이트한 read path

full index 대신 summary + sparse index + Bloom filter 조합으로  
메모리 예산 안에서 read amplification을 통제할 수 있다.

### 시나리오 4: 부적합한 경우

OLTP 한 건 업데이트와 즉시 in-place mutation이 핵심이면  
page-oriented B-Tree 계열이 더 자연스러울 수 있다.

## 선택 프레임

| 단계 | 더 잘 맞는 구조 | 이유 |
|---|---|---|
| mutable write buffer | Skip List / ART / ordered map | flush를 위한 정렬 유지 |
| immutable data file | prefix-compressed sorted block | 순차 저장과 압축 |
| block location | sparse index / fence pointer | 메모리 적게 쓰는 탐색 포인트 |
| negative lookup skip | Bloom Filter | 파일 접근을 빠르게 배제 |
| term/key dictionary | FST 등 compressed dictionary | 대규모 문자열 key 압축 |

## 꼬리질문

> Q: LSM에서 왜 memtable과 SSTable이 다른 자료구조를 쓰나요?
> 의도: write path와 read path 요구가 다르다는 점 이해 확인
> 핵심: memtable은 mutation-friendly해야 하고, SSTable은 immutable/sparse index가 더 효율적이기 때문이다.

> Q: Bloom filter는 주 인덱스인가요?
> 의도: 보조 구조와 주 구조를 구분하는지 확인
> 핵심: 아니다. negative lookup을 빠르게 줄이는 보조 구조다.

> Q: fence pointer가 왜 중요한가요?
> 의도: sparse index 설계 감각 확인
> 핵심: 전체 key를 다 메모리에 두지 않고도 어떤 block을 열어야 할지 빠르게 좁힐 수 있기 때문이다.

## 한 줄 정리

LSM-friendly index 구조는 하나의 트리가 아니라, mutable memtable과 immutable sparse block index, Bloom filter, dictionary 압축을 조합해 write path와 read path를 분리 최적화하는 설계다.
