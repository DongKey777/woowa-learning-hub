---
schema_version: 3
title: Bit-Sliced Bitmap Sort-Key Sensitivity
concept_id: data-structure/bit-sliced-bitmap-sort-key-sensitivity
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- bsi-sort-key-locality
- bitmap-prefix-locality
- warehouse-row-ordering
aliases:
- bit sliced bitmap sort key
- BSI sort key sensitivity
- bit slice prefix locality
- upper slice run length
- segment boundary bitmap
- numeric prefix clustering
- bitmap sort order sensitivity
symptoms:
- 숫자 컬럼을 정렬하면 모든 bit slice가 똑같이 압축될 것이라고 오해한다
- 평균 bitmap compression만 보고 upper slice locality와 lower slice noise 차이를 놓친다
- segment boundary나 late-arriving rows가 slice run을 끊는 영향을 query 성능과 연결하지 못한다
intents:
- troubleshooting
- deep_dive
prerequisites:
- data-structure/bit-sliced-bitmap-index
- data-structure/row-ordering-and-bitmap-compression-playbook
next_docs:
- data-structure/warehouse-sort-key-co-design-for-bitmap-indexes
- data-structure/roaring-run-formation-and-row-ordering
- data-structure/late-arriving-rows-and-bitmap-maintenance
linked_paths:
- contents/data-structure/bit-sliced-bitmap-index.md
- contents/data-structure/row-ordering-and-bitmap-compression-playbook.md
- contents/data-structure/warehouse-sort-key-co-design-for-bitmap-indexes.md
- contents/data-structure/roaring-run-formation-and-row-ordering.md
- contents/data-structure/compressed-bitmap-families-wah-ewah-concise.md
- contents/data-structure/late-arriving-rows-and-bitmap-maintenance.md
confusable_with:
- data-structure/bit-sliced-bitmap-index
- data-structure/row-ordering-and-bitmap-compression-playbook
- data-structure/warehouse-sort-key-co-design-for-bitmap-indexes
- data-structure/roaring-run-formation-and-row-ordering
forbidden_neighbors: []
expected_queries:
- Bit-Sliced Bitmap에서 sort key가 slice별 compression에 다르게 작용하는 이유는?
- 숫자 컬럼 정렬이 상위 bit slice와 하위 bit slice에 왜 다르게 보이나?
- BSI compression을 평균값만 보면 안 되고 prefix locality를 봐야 하는 이유를 알려줘
- segment boundary가 bit slice run을 끊으면 range predicate 성능에 어떤 영향이 있어?
- warehouse sort key를 BSI와 같이 설계할 때 무엇을 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Bit-Sliced Bitmap Index의 압축 효율이 숫자 정렬 여부 하나가
  아니라 bit position별 prefix locality와 segment boundary에 좌우된다는
  점을 다룬다. upper slice run length, lower slice noise, warehouse sort
  key, late-arriving rows, row ordering을 함께 판단한다.
---
# Bit-Sliced Bitmap Sort-Key Sensitivity

> 한 줄 요약: Bit-Sliced Bitmap Index의 압축 효율은 "숫자 컬럼을 정렬했는가" 하나로 설명되지 않고, 각 bit slice가 어떤 prefix locality를 얻는지, 그 locality가 segment boundary를 넘어 유지되는지에 따라 다르게 갈린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Late-Arriving Rows and Bitmap Maintenance](./late-arriving-rows-and-bitmap-maintenance.md)

> retrieval-anchor-keywords: bit sliced bitmap sort key, bsi sort key sensitivity, bit slice compression locality, prefix locality bitmap, upper slice run length, lower slice noise, numeric prefix stability, segment boundary bit slice, row group boundary bitmap, roaring locality bit slice, active chunk per slice, warehouse numeric sort key, range predicate slice locality, bit sliced row ordering, bitmap prefix clustering

## 핵심 개념

BSI에서 sort key가 만드는 clustering 단위는 "같은 값"보다 **같은 상위 prefix가 얼마나 오래 유지되는가**에 더 가깝다.

- exact value bitmap은 값 band가 길수록 직접 이득을 본다
- BSI는 bit position마다 반응이 다르다
- 상위 bit slice는 긴 prefix band를 따라 run이 길어지기 쉽다
- 하위 bit slice는 같은 정렬에서도 여전히 자주 뒤집힐 수 있다

즉 BSI 압축 가이드는 "정렬하면 좋아진다"가 아니라  
"어느 slice가 prefix locality를 얻고, 그 locality가 segment 경계에서 몇 번 끊기는가"까지 같이 봐야 정확하다.

## 깊이 들어가기

### 1. 같은 정렬이라도 slice마다 반응이 다르다

값을 오름차순으로 정렬했다고 가정하자.  
`8`비트 값을 `0..255` 순서로 배치하면 slice 모양은 균일하지 않다.

| slice | 정렬된 값에서 보이는 패턴 | run 감각 |
|---|---|---|
| 최상위 bit (`b7`) | `0000....1111....` | 거의 한 번만 뒤집혀 매우 길다 |
| 중간 bit (`b6`) | `00..0011..1100..0011..11` | 상위 bit보다 더 자주 끊긴다 |
| 하위 bit (`b0`) | `010101...` | 거의 매 row마다 뒤집혀 run 이득이 작다 |

핵심은 두 가지다.

- 숫자 정렬은 **모든 slice를 똑같이** 압축 친화적으로 만들지 않는다
- 정렬 이득은 보통 상위 slice부터 크게 나타나고, 하위 slice로 갈수록 빠르게 약해진다

이 점이 중요한 이유는 range predicate가 상위 bit부터 비교를 시작하기 때문이다.  
즉 `value >= threshold`나 `BETWEEN` 계열은 상위 slice locality가 좋아질수록 압축률뿐 아니라 candidate pruning도 같이 유리해진다.

### 2. BSI의 clustering 단위는 exact value locality가 아니라 prefix locality다

값별 bitmap은 `value = 700` row가 한 band로 모이면 바로 long run을 얻는다.  
반면 BSI는 `700` 그 자체보다 `10xx xxxx`, `101x xxxx` 같은 **공유 prefix**가 얼마나 오래 유지되는지에 반응한다.

예를 들어 `price`를 직접 sort key 앞에 두면:

- 상위 bit slice는 큰 가격 band를 따라 긴 run을 만들기 쉽다
- 중간 slice는 구간 내부에서 몇 번 더 토글되지만 여전히 국소 locality를 얻는다
- 최하위 slice는 거의 noise에 가깝게 남을 수 있다

반대로 `price`와 상관 없는 `event_time`만 앞에 둔 정렬이면:

- 전체 히스토그램이 같아도 각 slice는 훨씬 랜덤한 패턴을 본다
- 상위 slice조차 active row가 여러 band에 흩어진다
- "숫자 컬럼 분포가 괜찮다"는 사실만으로는 압축률을 예측하기 어렵다

따라서 BSI에서 좋은 sort key 질문은 "`같은 값`이 모이는가?"보다  
"자주 필터하는 numeric threshold가 의존하는 **상위 prefix**가 row ID상에서 오래 유지되는가?"다.

### 3. 상관된 차원 정렬은 직접 정렬보다 약하지만 여전히 의미가 있다

numeric 컬럼 자체를 앞에 두지 않아도, 상관된 차원이 먼저 오면 BSI slice는 간접적으로 이득을 볼 수 있다.

| sort-key 패턴 | BSI slice가 보는 모양 | 압축 가이드 |
|---|---|---|
| `price` 자체 정렬 | 상위 slice가 매우 안정적, 하위 slice는 점차 noisy | range-heavy read-mostly면 가장 직접적인 선택 |
| `country, price`처럼 상관된 차원 뒤 numeric | 국가 band 안에서 상위 prefix가 안정됨 | segment-local locality를 얻기 쉬워 Roaring에 잘 맞는다 |
| `event_time` 우선, numeric은 무관 | slice 전반이 넓게 퍼지고 경계가 잦다 | BSI 압축 기대를 낮추고 scan/rebuild 비용을 같이 본다 |
| micro-batch 내부만 `price` 정렬 | batch 안에서는 prefix locality가 있으나 전역 연속성은 짧다 | batch 수가 많을수록 boundary reset 비용이 커진다 |

즉 BSI는 "numeric 컬럼을 직접 정렬해야만" 작동하는 구조는 아니지만,  
정렬축이 numeric 분포와 얼마나 상관되는지에 따라 **상위 slice만 좋아지는지, 대부분 slice가 계속 noisy한지**가 갈린다.

### 4. segment boundary는 prefix run을 codec이 보기 전에 잘라 버린다

row group, micro-partition, shard, daily segment 경계는 BSI에도 압축 reset처럼 작동한다.

예를 들어 상위 prefix가 원래 `1024` row 동안 유지되더라도:

- `256` row짜리 row group이면 같은 prefix band가 최소 `4`조각으로 나뉜다
- segment별로 bitmap을 따로 저장하면 run/fill도 segment마다 다시 시작한다
- 작은 batch가 많을수록 slice마다 "짧은 좋은 run"이 반복될 뿐 전역 run으로 이어지지 않는다

이 구분은 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)의 locality 모델과 그대로 맞물린다.

- **Roaring**: 각 slice에서 active chunk 수와 chunk 안 run 수가 줄어들면 이득을 본다
- **WAH/EWAH/CONCISE**: slice bitstream이 segment 경계를 넘어 clean run으로 오래 유지될수록 더 크게 이득을 본다

즉 BSI에서도 `segment-local prefix locality`와 `global prefix locality`를 구분해야 한다.

### 5. BSI 압축 가이드는 Roaring locality 문서와 같은 계층으로 읽어야 한다

새로운 Roaring locality 감각을 BSI에 그대로 옮기면 판단이 훨씬 정확해진다.

| locality 상태 | BSI slice 관점 | codec 선택 감각 |
|---|---|---|
| prefix locality가 약하고 대부분 slice가 넓게 퍼짐 | 상위 slice조차 active chunk가 많고 run 수가 높다 | BSI 자체 이득이 제한적일 수 있어 plain scan/다른 인덱스와 비교해야 한다 |
| segment 내부에서만 prefix locality가 좋음 | 상위 slice는 chunk-local 안정성을 얻지만 boundary마다 다시 깨진다 | Roaring처럼 chunk-local 적응이 강한 표현이 기본값이 되기 쉽다 |
| 큰 segment와 read-mostly 운영으로 global prefix locality가 유지됨 | 상위/중간 slice가 긴 fill/run을 오래 유지한다 | WAH/EWAH/CONCISE나 run-heavy 표현의 break-even이 빨리 가까워진다 |
| late row, revoke, upsert로 band가 자주 깨짐 | 상위 slice부터 fragmentation이 누적되고 하위 slice는 원래 noisy하다 | 초기 bulk-build 결과보다 유지 비용과 rebuild 주기를 먼저 본다 |

특히 BSI는 모든 slice를 같은 표현으로 고정해 두더라도, 실제로는 **bit position별 locality 편차**가 매우 크다.  
그래서 "BSI는 정렬만 하면 압축이 잘 된다"는 식의 가이드는 Roaring locality 문서 기준으로 보면 너무 거칠다.

### 6. range query는 상위 slice locality에 더 민감하다

BSI 질의는 상위 bit부터 후보를 좁히는 경우가 많다.  
그래서 압축 관찰도 전체 평균보다 아래 두 지표를 먼저 봐야 한다.

1. threshold 비교에 자주 등장하는 상위 `4~8`개 slice의 run/active chunk 수
2. segment boundary가 그 상위 slice run을 몇 번 끊는지

하위 slice가 noisy하더라도 상위 slice가 안정적이면:

- 초기 후보 축소는 빠를 수 있고
- bitmap I/O도 상위 slice 위주로 먼저 줄일 수 있다

반대로 상위 slice부터 이미 잘게 깨져 있다면,  
BSI는 "비트 연산 구조"는 유지해도 compression과 execution 둘 다 기대치가 떨어진다.

### 7. 운영에서 바로 보는 체크포인트

BSI 압축 실험이나 운영 계측에서는 아래를 slice별로 나눠서 보는 편이 좋다.

| 체크 항목 | 왜 필요한가 |
|---|---|
| 상위 slice별 active chunk 수 | Roaring locality가 실제로 번역됐는지 보여 준다 |
| slice별 run 수 또는 fill/literal 비율 | WAH 계열과 run container 이득을 동시에 가늠할 수 있다 |
| 동일 상위 prefix의 segment spread | prefix locality가 전역인지 segment-local인지 구분해 준다 |
| 상위 slice 대비 하위 slice 압축 편차 | "정렬 이득이 어디까지 내려오는지"를 보여 준다 |
| late ingest 후 상위 slice fragmentation 증가 속도 | 초기 bulk build와 운영 steady-state 차이를 드러낸다 |

숫자 컬럼 하나만 보고 평균 압축률을 내면 이 차이가 잘 안 보인다.  
BSI는 **slice 간 비대칭성**이 큰 구조라, 평균보다 상위 slice 관찰이 더 중요하다.

## 실전 시나리오

### 시나리오 1: `price` 직접 정렬된 read-mostly fact table

상위 slice는 매우 긴 run을 만들고, 중간 slice도 큰 band 안에서 비교적 안정적이다.  
이 경우 BSI range predicate는 압축과 실행 모두 이득이 크다.

다만 최하위 slice까지 완전히 예뻐질 것이라고 기대하면 안 된다.  
정렬 이득은 bit position별로 감소한다.

### 시나리오 2: `country, price` 정렬된 warehouse

국가 band 안에서 price 범위가 비교적 좁다면 상위 prefix가 segment 내부에서 오래 유지된다.  
이 경우 BSI는 Roaring의 chunk-local locality 모델과 잘 맞는다.

반대로 국가별 가격 분산이 너무 크면 country 정렬만으로는 slice locality가 충분히 생기지 않을 수 있다.

### 시나리오 3: `event_time` append 우선 + 잦은 late update

시간축 운영은 편하지만 numeric prefix band가 자주 끊긴다.  
초기 build 직후엔 괜찮아 보여도 late row가 끼기 시작하면 상위 slice부터 fragmentation이 빨라질 수 있다.

이 경우는 BSI 도입보다:

- row-group 재조정
- compaction/reclustering
- BSI 유지 비용 대비 scan 비용 비교

를 먼저 보는 편이 낫다.

## 꼬리질문

> Q: 숫자 컬럼을 정렬하면 모든 BSI slice가 비슷하게 잘 압축되나요?
> 의도: bit position별 반응 차이를 이해하는지 확인
> 핵심: 아니다. 상위 slice는 긴 run을 얻기 쉽지만 하위 slice는 같은 정렬에서도 계속 noisy할 수 있다.

> Q: BSI에서 sort key가 만드는 locality 단위는 무엇인가요?
> 의도: exact value locality와 prefix locality를 구분하는지 확인
> 핵심: 값 하나의 band보다 상위 bit prefix가 얼마나 오래 유지되는지가 더 중요하다.

> Q: segment boundary를 왜 별도 변수로 봐야 하나요?
> 의도: 정렬과 저장 단위 reset을 분리하는지 확인
> 핵심: 좋은 prefix band도 row group이나 micro-partition 경계가 많으면 여러 짧은 run으로 쪼개져 codec 이득이 약해진다.

## 한 줄 정리

BSI 압축 가이드는 "숫자 정렬 여부"가 아니라, 각 bit slice의 상위 prefix locality가 row ordering과 segment boundary를 거치며 어디까지 유지되는지, 그리고 그 locality가 Roaring의 chunk-local 이득인지 WAH/EWAH의 global run 이득인지로 구분해서 봐야 정확하다.
