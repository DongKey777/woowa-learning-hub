# Roaring Bitmap Selection Playbook

> 한 줄 요약: Roaring Bitmap은 exact set algebra에 강하지만, 모든 압축 표현의 기본값은 아니며 BitSet, Elias-Fano, succinct bitvector, approximate filter와 질문이 다르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Elias-Fano Encoded Posting List](./elias-fano-encoded-posting-list.md)
> - [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [Sketch and Filter Selection Playbook](./sketch-filter-selection-playbook.md)

> retrieval-anchor-keywords: roaring bitmap selection, roaring vs bitset, roaring vs elias fano, roaring vs approximate filter, bitmap choice, exact set algebra, compressed bitmap decision guide, posting list representation, bitmap selection playbook, analytics set structure, roaring vs WAH, run-heavy bitmap, bitmap family selection, roaring run container, roaring container churn, mixed density bitmap, row ordering sensitive bitmap, exact bitmap workload, segment boundary bitmap, warehouse bitmap sort key, roaring set op result, lazy cardinality repair, sorted ingest roaring, bitmap id locality, roaring vs ewah break even

## 핵심 개념

Roaring Bitmap은 훌륭한 exact set structure지만,  
"압축 표현 = 무조건 roaring"으로 보면 선택이 거칠어진다.

질문을 먼저 나눠야 한다.

- exact set algebra가 핵심인가
- sparse sorted list가 핵심인가
- rank/select가 핵심인가
- membership prefilter만 필요하나

즉 Roaring의 장점은 분명하지만,  
질문이 달라지면 Elias-Fano나 succinct bitvector, filter가 더 맞을 수 있다.

## 비교 프레임

### 1. Roaring vs BitSet

- BitSet:
  - dense하고 id 공간이 작을 때 단순하고 빠름
  - 메모리 낭비가 커질 수 있음
- Roaring:
  - sparse/dense가 섞여도 적응적
  - set algebra가 강함

즉 id 공간이 넓고 density가 들쭉날쭉하면 Roaring 쪽이 더 실전적이다.

### 2. Roaring vs WAH/EWAH/CONCISE

- Roaring:
  - chunk별 array/bitmap/run 적응이 가능하다
  - mixed density와 repeated set operation에 강하다
- WAH/EWAH/CONCISE:
  - word-aligned run compression에 집중한다
  - 긴 clean run이 이어지는 analytic bitmap scan에 강하다

여기서 `적응`이 공짜는 아니다. chunk가 `4096` 경계나 run 수 경계를 자주 넘나들면 container churn이 생기므로, 그 내부 비용 모델은 [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)에서 따로 보는 편이 정확하다.
입력 container보다 결과 container가 더 헷갈린다면, `AND/OR/XOR` 경로를 따로 정리한 [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)를 이어서 보면 좋다.

즉 mixed-density exact set algebra는 Roaring,  
row ordering 덕분에 긴 run이 이어지는 warehouse bitmap은 WAH family가 더 자연스러울 수 있다.

정렬, clustering, row group 경계가 이 선택을 어떻게 뒤집는지는  
[Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)에 정리해 두었다.  
특히 Roaring 쪽 run 수와 active chunk 수가 줄면서도 왜 아주 강한 전역 ordering에서는 WAH/EWAH break-even이 앞으로 당겨지는지는 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)을 같이 보면 더 분명하다.

### 3. Roaring의 run container가 있다고 해서 WAH family와 같아지진 않는다

둘 다 "run"을 다루지만 최적화 단위가 다르다.

- Roaring: 16-bit chunk 안에서 container를 바꾼다
- WAH/EWAH/CONCISE: bitmap 전체를 word-aligned run scan 모델로 압축한다

그래서 Roaring에 run container가 있어도:

- chunk 경계를 넘어 매우 긴 clean run이 이어지는 analytic bitmap
- row ordering 덕분에 전체 column이 크게 뭉쳐 있는 데이터

에서는 WAH family 쪽 scan model이 더 자연스러울 수 있다.

반대로 chunk마다 밀도가 크게 달라지면  
Roaring의 adaptive container가 더 강하다.

### 4. Roaring vs Elias-Fano

- Roaring:
  - exact AND/OR/XOR가 빠름
  - membership/set algebra 중심
- Elias-Fano:
  - sorted sparse list를 매우 작게 저장
  - skip / predecessor / merge에 유리

즉 "집합 연산"이 핵심이면 Roaring,  
"정렬된 sparse posting list"가 핵심이면 Elias-Fano가 더 자연스러울 수 있다.

### 5. Roaring vs Succinct Bitvector

- Roaring:
  - exact set structure
  - container 적응과 set algebra
- Succinct bitvector:
  - rank/select primitive
  - compressed index의 기반 부품

즉 Roaring은 사용자가 직접 다루는 set structure고,  
succinct bitvector는 더 아래 레벨의 압축 탐색 primitive에 가깝다.

### 6. Roaring vs approximate filter

- Roaring:
  - exact membership
  - exact set algebra
- Bloom/Cuckoo/Xor/Quotient:
  - false positive 허용
  - negative lookup prefilter

즉 "아예 없음을 빨리 말하는 것"만 필요하면 filter가 더 싸다.

### 7. selection은 데이터 모양과 다음 연산을 같이 봐야 한다

같은 cardinality라도 어떤 연산이 뒤따르느냐에 따라 선택이 달라진다.

| 질문 | Roaring 쪽으로 기우는 신호 | 다른 쪽으로 기우는 신호 |
|---|---|---|
| density가 chunk별로 섞여 있는가 | sparse/dense/run 구간이 뒤섞인다 | row ordering 덕분에 긴 clean run이 전체적으로 이어진다 |
| lookup 다음에 무엇을 하나 | exact AND/OR/XOR를 반복한다 | `lower_bound` 뒤 scan, posting merge, rank/select가 핵심이다 |
| update/append 성격은 어떤가 | chunk 내부 cardinality 변화가 잦다 | append-only analytic bitmap이고 run clustering이 강하다 |
| 메모리 절감보다 중요한 것은 무엇인가 | set algebra 처리량과 범용성 | posting list footprint, rank/select, negative lookup 비용 |

즉 Roaring은 "어느 한 축에서 최고"라기보다  
**mixed-density exact set algebra의 범용 기본값**에 가깝다.

### 8. 빠른 선택표

| 질문 | 우선 후보 |
|---|---|
| exact set algebra가 핵심이고 density가 뒤섞였는가 | Roaring Bitmap |
| row ordering 때문에 긴 run이 많이 생기는가 | WAH/EWAH/CONCISE |
| dense하고 id 공간이 작아 raw bitset이 단순한가 | BitSet |
| sparse sorted posting list를 작게 저장하고 skip/merge가 중요한가 | Elias-Fano |
| rank/select가 핵심 primitive인가 | Succinct Bitvector |
| negative lookup prefilter만 필요하나 | Bloom/Cuckoo/Xor/Quotient |

### 9. backend에서 고르는 기준

Roaring이 특히 빛나는 경우:

- 사용자 세그먼트 교집합
- 권한/타겟 대상 계산
- exact bitmap combine
- analytics candidate generation
- bit-sliced bitmap index의 exact candidate set

다른 구조가 더 나은 경우:

- globally run-heavy warehouse bitmap: WAH/EWAH/CONCISE
- posting list 자체 압축: Elias-Fano
- rank/select primitive: succinct bitvector
- negative lookup prefilter: approximate filter

## 실전 시나리오

### 시나리오 1: exact audience intersection

`premium ∩ active ∩ eligible` 같은 exact audience set combine이면  
Roaring이 매우 강하다.

### 시나리오 2: row group이 정렬된 warehouse bitmap

같은 값이 긴 run으로 이어지고 exact bitwise combine이 핵심이면  
WAH/EWAH/CONCISE 쪽이 더 자연스러울 수 있다.

### 시나리오 3: search posting list storage

정렬된 docID list를 compact하게 저장하고 skip/merge하려면  
Elias-Fano가 더 낫기도 하다.

### 시나리오 4: key not found precheck

segment에 키가 아예 없음을 빨리 알고 싶다면  
Roaring보다 Xor/Bloom 계열이 더 싸다.

### 시나리오 5: rank/select-heavy compressed index

파생 구조가 rank/select를 핵심 primitive로 쓰면  
succinct bitvector 쪽이 더 본질적이다.

## 꼬리질문

> Q: Roaring Bitmap이 Bloom Filter를 대체하나요?
> 의도: exact set과 approximate prefilter를 구분하는지 확인
> 핵심: 아니다. 질문 자체가 다르다. Roaring은 exact set, Bloom은 approximate membership prefilter다.

> Q: Roaring과 Elias-Fano 중 무엇을 고르나요?
> 의도: set algebra와 sorted list storage를 구분하는지 확인
> 핵심: exact 집합 연산이면 Roaring, sparse sorted posting list 압축이면 Elias-Fano 쪽이 더 자연스러울 수 있다.

> Q: succinct bitvector는 왜 Roaring과 다른 층위인가요?
> 의도: 최종 구조와 기반 primitive를 구분하는지 확인
> 핵심: succinct bitvector는 rank/select 기반 compressed index primitive이고, Roaring은 직접 쓰는 exact set structure이기 때문이다.

> Q: Roaring에 run container가 있는데 왜 WAH/EWAH/CONCISE를 따로 비교하나요?
> 의도: adaptive chunk 전략과 word-aligned run compression의 축을 분리하는지 확인
> 핵심: Roaring은 mixed-density 적응이 중심이고, WAH/EWAH/CONCISE는 긴 run scan 자체를 최적화하는 계열이기 때문이다.

## 한 줄 정리

Roaring Bitmap은 exact set algebra를 위한 강한 기본값이지만, posting list 압축·rank/select·negative lookup처럼 질문이 달라지면 다른 구조가 더 맞을 수 있다.
