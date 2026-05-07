---
schema_version: 3
title: Compressed Bitmap Families WAH EWAH CONCISE
concept_id: data-structure/compressed-bitmap-families-wah-ewah-concise
canonical: false
category: data-structure
difficulty: advanced
doc_role: chooser
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- compressed-bitmap-family
- wah-ewah-concise
- run-heavy-bitmap
aliases:
- compressed bitmap families
- WAH EWAH CONCISE bitmap
- word aligned hybrid bitmap
- word-aligned RLE bitmap
- run length bitmap
- clean word dirty word bitmap
- Roaring vs EWAH break even
symptoms:
- bitmap compression을 모두 Roaring으로만 생각해 word-aligned run codec 계열의 장단점을 놓친다
- 긴 0 run이나 1 run이 많은 exact bitmap에서 raw BitSet과 compressed bitmap의 scan cost 차이를 설명하지 못한다
- Roaring의 16-bit container boundary와 WAH/EWAH의 whole word stream run 감각을 구분하지 못한다
intents:
- comparison
- deep_dive
prerequisites:
- data-structure/roaring-bitmap
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
next_docs:
- data-structure/chunk-boundary-pathologies-in-roaring
- data-structure/row-ordering-and-bitmap-compression-playbook
- data-structure/bit-sliced-bitmap-index
- data-structure/succinct-bitvector-rank-select
linked_paths:
- contents/data-structure/roaring-bitmap.md
- contents/data-structure/chunk-boundary-pathologies-in-roaring.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/roaring-bitmap-selection-playbook.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/succinct-bitvector-rank-select.md
- contents/data-structure/bit-sliced-bitmap-index.md
confusable_with:
- data-structure/roaring-bitmap
- data-structure/plain-bitset-vs-compressed-bitmap-decision-card
- data-structure/chunk-boundary-pathologies-in-roaring
- data-structure/succinct-bitvector-rank-select
forbidden_neighbors: []
expected_queries:
- WAH EWAH CONCISE compressed bitmap은 Roaring Bitmap과 무엇이 달라?
- run-heavy bitmap에서 word-aligned compression이 왜 유리한지 설명해줘
- clean word dirty word literal word fill word가 compressed bitmap에서 무슨 뜻이야?
- Roaring의 chunk boundary와 EWAH 같은 whole bitmap run codec을 비교해줘
- exact bitwise set algebra를 유지하면서 bitmap을 압축하는 계열을 알려줘
contextual_chunk_prefix: |
  이 문서는 WAH, EWAH, CONCISE 같은 word-aligned compressed bitmap
  family를 Roaring Bitmap과 비교한다. run-heavy bitmap, clean word, dirty
  word, literal/fill word, exact bitwise set algebra, whole bitmap run codec과
  16-bit chunk boundary 차이를 다룬다.
---
# Compressed Bitmap Families: WAH, EWAH, CONCISE

> 한 줄 요약: WAH/EWAH/CONCISE는 긴 run이 많은 bitmap을 word-aligned 방식으로 압축해, exact bitwise set algebra를 유지하면서 저장 공간과 scan 비용을 줄이려는 compressed bitmap 계열이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Chunk-Boundary Pathologies In Roaring](./chunk-boundary-pathologies-in-roaring.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Succinct Bitvector Rank/Select](./succinct-bitvector-rank-select.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)

> retrieval-anchor-keywords: compressed bitmap families, WAH, EWAH, CONCISE bitmap, word aligned hybrid, bitmap compression, exact set algebra, run length bitmap, roaring bitmap comparison, compressed bitset, analytic bitmap index, word-aligned RLE, fill word, clean word, dirty word, run-heavy bitmap, append friendly bitmap, row ordering sensitive bitmap, literal word, clean run skipping, segment boundary bitmap, warehouse bitmap sorting, row clustering bitmap, sorted ingest bitmap, roaring vs ewah break even, bitmap id locality, whole bitmap run codec, chunk boundary roaring, 16-bit container boundary, global run vs chunk local run

## 핵심 개념

bitmap을 압축한다고 해서 모두 같은 방식은 아니다.  
WAH/EWAH/CONCISE는 비트 하나하나를 다루기보다 **word 단위 run**을 압축한다.

핵심 아이디어:

- 0이나 1이 길게 반복되는 word 구간을 압축
- exact bitwise AND/OR/XOR는 계속 지원
- 스캔은 word-aligned 형태로 유지

즉 exact set algebra를 유지하면서  
**run-heavy bitmap을 더 compact하게 저장**하려는 계열이다.

## 깊이 들어가기

### 1. 왜 run-heavy bitmap에 강한가

bitmap에서 긴 0 구간이나 긴 1 구간이 많으면  
raw BitSet은 그걸 그대로 저장한다.

WAH/EWAH류는:

- literal word
- fill word

같은 표현을 두어 반복 구간을 줄인다.

그래서 sparse한데 cluster/run이 긴 데이터에서 효율적일 수 있다.

### 2. family 내부에서도 초점이 조금씩 다르다

세 이름을 한 덩어리로 묶어 읽어도 되지만, 구현 감각은 약간 다르다.

| 계열 | 초점 | 운영 감각 | 주의점 |
|---|---|---|---|
| WAH | fill word와 literal word 구분이 단순하다 | reasoning과 scan model이 비교적 직선적이다 | mixed literal 구간이 많아지면 이득이 빨리 줄 수 있다 |
| EWAH | clean/dirty word 묶음을 다루기 쉽게 만든다 | append와 streaming scan을 현실적으로 다루기 좋다 | 절대 압축률만 보면 CONCISE보다 덜 공격적일 수 있다 |
| CONCISE | 짧은 run과 예외 패턴까지 더 아껴 담으려는 변형이다 | footprint 절감 쪽으로 더 공격적일 수 있다 | decode/구현 reasoning이 더 복잡해질 수 있다 |

세부 marker encoding은 다르지만 공통점은 같다.  
모두 word-aligned exact bitmap scan을 유지하면서 run을 줄이려는 계열이다.

### 3. Roaring과 감각 차이는 무엇인가

Roaring은 container를 적응적으로 바꾼다.

- array
- bitmap
- run

반면 WAH/EWAH/CONCISE는 더 전통적인 word-aligned run compression 쪽에 가깝다.

즉 비교 관점은 이렇다.

- Roaring: mixed density 적응
- WAH family: run-heavy bitmap scan

특히 "전역적으로는 몇 개 안 되는 긴 interval"이 `16-bit` seam을 많이 넘는 workload라면, Roaring의 per-container restart가 footprint surprise로 이어질 수 있는데 이 케이스는 [Chunk-Boundary Pathologies In Roaring](./chunk-boundary-pathologies-in-roaring.md)에서 따로 본다.

### 4. exact set algebra는 그대로 유지된다

이 계열의 중요한 장점은 approximate가 아니라 exact라는 점이다.

- AND
- OR
- XOR

를 압축 상태에서 word 단위로 비교적 자연스럽게 수행할 수 있다.  
그래서 analytic bitmap index에서 오랫동안 쓰였다.

여기서 핵심은 단순한 "압축률"보다  
**clean run을 얼마나 많이 건너뛸 수 있느냐**다.

- `AND`: 긴 zero fill이 있으면 반대편 큰 구간을 빠르게 소거할 수 있다
- `OR`: 긴 one fill이 있으면 결과를 크게 확정해 나가기 쉽다
- `XOR`: 양쪽 literal 구간이 많아질수록 skip 이점이 줄어든다

즉 run-heavy workload일수록 scan cost까지 같이 줄고,  
dirty literal이 많아질수록 raw word scan과 차이가 줄어든다.

### 5. row ordering이 이 계열의 성패를 크게 좌우한다

같은 cardinality라도 row를 어떻게 정렬했는지에 따라 bitmap 모양이 완전히 달라진다.

- 값별 row가 길게 몰려 있으면 clean run이 길어진다
- 날짜/파티션/차원 기준으로 clustering이 되어 있으면 fill word가 잘 생긴다
- 반대로 row가 랜덤하게 섞이면 dirty literal 비중이 급격히 늘어난다

그래서 WAH/EWAH/CONCISE는 "희소하다"보다  
**run이 구조적으로 길게 이어지는가**를 먼저 보는 것이 맞다.

이 관점에서:

- warehouse/columnar bitmap처럼 정렬 축이 분명한 데이터엔 매우 잘 맞고
- mixed-density online set workload엔 Roaring이 더 실용적일 수 있다

row ordering, clustering, segment boundary가 실제로 run을 어떻게 쪼개거나 늘리는지는  
[Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)에서 따로 보면 좋다.
Roaring 쪽 active chunk 수와 run 수가 같이 줄어도, 왜 전역 clean run이 길어질수록 WAH/EWAH break-even이 앞으로 당겨질 수 있는지는 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)에서 이어서 다룬다.

### 6. backend에서 어디에 맞나

run이 긴 columnar/analytic bitmap에 잘 맞는다.

- low-cardinality column bitmap
- sparse segmented flags
- warehouse-style bitmap index
- row ordering이 잘 잡힌 segment bitmap

반면 매우 혼합된 density와 random membership 중심이면  
Roaring이 더 실용적일 때가 많다.

### 7. 왜 요즘은 Roaring이 더 자주 언급되나

실무 데이터는 density가 한 방향으로만 깨끗하지 않다.

- sparse한 chunk
- dense한 chunk
- run-heavy chunk

가 섞인 경우가 많아, container 적응형인 Roaring이 전반적으로 쓰기 편한 경우가 많다.  
그래도 run-heavy analytic workload에선 WAH 계열 감각이 여전히 유효하다.

## 실전 시나리오

### 시나리오 1: analytic bitmap index

정렬된 row group과 low-cardinality column bitmap이 길게 이어지면  
word-aligned run compression이 잘 먹을 수 있다.

### 시나리오 2: flag column set algebra

exact bitwise combine이 핵심인 warehouse-style 질의에 자연스럽다.

### 시나리오 3: mixed-density online workload

container 적응과 membership 편의가 중요하면  
Roaring이 더 실용적인 선택일 수 있다.

### 시나리오 4: 부적합한 경우

negative lookup prefilter만 필요하면  
compressed bitmap보다 Bloom/Xor 계열이 더 싸다.

## 비교 표

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| WAH | word-aligned run model이 단순하고 reasoning이 쉽다 | mixed literal 구간이 많아지면 이득이 빠르게 줄 수 있다 | run-heavy analytic bitmap을 직선적으로 다루고 싶을 때 |
| EWAH | append와 streaming scan에 현실적이고 practical하다 | 절대 footprint만 보면 가장 공격적이지는 않을 수 있다 | 실무형 analytic bitmap append/scan |
| CONCISE | 짧은 run과 예외 패턴까지 더 아껴 담을 수 있다 | 구현과 decode reasoning이 더 복잡하다 | 메모리 절감이 특히 중요한 run-heavy exact bitmap |
| Roaring Bitmap | sparse/dense/run 혼합 데이터에 적응적이다 | 구현과 container 개념이 더 복잡하다 | general exact set algebra, mixed-density workload |
| Plain BitSet | 단순하고 dense data에서 빠르다 | 긴 sparse/run 구간에서 메모리 낭비가 크다 | small/dense bitmap |
| Approximate Filter | negative lookup prefilter에 매우 싸다 | exact set algebra가 안 된다 | precheck only |

## 꼬리질문

> Q: WAH/EWAH류와 Roaring의 가장 큰 차이는 무엇인가요?
> 의도: run-based compression과 adaptive container의 차이를 이해하는지 확인
> 핵심: 전자는 word-aligned run compression 중심이고, 후자는 chunk density에 따라 container를 바꾸는 구조다.

> Q: 왜 analytic workload에서 bitmap family가 중요하나요?
> 의도: exact set algebra와 columnar 질의의 관계를 이해하는지 확인
> 핵심: 조건별 row 집합을 exact bitmap으로 두고 AND/OR를 빠르게 수행할 수 있기 때문이다.

> Q: 이 계열이 Bloom Filter와 같은 종류인가요?
> 의도: exact bitmap과 approximate filter를 구분하는지 확인
> 핵심: 아니다. WAH/EWAH/CONCISE는 exact bitmap compression이고 Bloom 계열은 approximate membership filter다.

> Q: Roaring에 run container가 있는데 왜 WAH/EWAH/CONCISE를 따로 구분하나요?
> 의도: adaptive chunk 구조와 word-aligned run scan의 철학 차이를 이해하는지 확인
> 핵심: Roaring은 chunk별 container 적응이 핵심이고, WAH/EWAH/CONCISE는 bitmap 전체를 word 단위 run compression으로 다루는 것이 핵심이기 때문이다.

## 한 줄 정리

WAH/EWAH/CONCISE는 run-heavy exact bitmap을 word-aligned 방식으로 압축하는 계열이고, Roaring과 함께 bitmap set algebra 설계를 비교할 때 꼭 알아야 하는 축이다.
