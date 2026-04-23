# Warehouse Sort-Key Co-Design for Bitmap Indexes

> 한 줄 요약: columnar warehouse에서 sort key는 pruning용 정렬이 아니라, `dictionary encoding -> row-group 경계 -> bitmap 모양 -> 압축 codec 결과`를 함께 바꾸는 상위 설계 변수다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Row-Ordering and Bitmap Compression Playbook](./row-ordering-and-bitmap-compression-playbook.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [Roaring Bitmap](./roaring-bitmap.md)

> retrieval-anchor-keywords: warehouse sort key bitmap index, sort-key co design, dictionary encoding bitmap, row group sizing bitmap, columnar warehouse bitmap compression, micro partition bitmap, local dictionary cardinality, dictionary id run length, row ordering bitmap warehouse, predicate locality warehouse, bitmap index clustering, WAH EWAH CONCISE warehouse, roaring warehouse sort key, bit sliced warehouse index, row group boundary bitmap, dictionary page compression, columnar sort order analytics

## 핵심 개념

columnar warehouse에서 bitmap index 성능은 codec만 골라서 끝나지 않는다.  
실제 결과는 아래 네 층이 연쇄적으로 묶여 있다.

1. sort key가 row를 어떤 band로 모으는가
2. 각 row group 안 local dictionary가 얼마나 작아지고, dictionary code가 얼마나 반복되는가
3. predicate hit가 몇 개 row group과 몇 개 bitmap chunk에 퍼지는가
4. 그 결과가 WAH/EWAH/CONCISE의 clean run, Roaring의 active chunk/run 수를 어떻게 바꾸는가

즉 warehouse에서는 `sort key`, `dictionary encoding`, `row-group sizing`, `bitmap compression`을 따로 최적화하면 자주 엇갈린다.

## 비교 프레임

### 1. sort key는 pruning 변수이기 전에 encoding 표면을 만든다

많은 columnar engine은 page, row group, micro-partition 단위로 local dictionary를 만든다.  
그래서 sort key가 바뀌면 단순히 "어떤 row group을 건너뛸 수 있나"뿐 아니라:

- row group 안 distinct value 수
- dictionary id의 반복 길이
- secondary compression(RLE, bit-packing, delta)의 유리함
- 값별 bitmap이나 bit-sliced slice의 연속성

이 함께 달라진다.

예를 들어 `country, status, event_date` 순으로 정렬하면:

- `country`, `status` 필터는 같은 값이 더 길게 붙는다
- 상관된 다른 low-cardinality 컬럼도 row group 안 local distinct가 줄 수 있다
- dictionary code가 긴 run으로 반복돼 page 압축이 좋아지기 쉽다
- 값별 bitmap은 긴 run, Roaring은 적은 active chunk를 기대할 수 있다

반대로 `event_time`만 앞에 둔 append-friendly 정렬은 time pruning엔 좋지만:

- `country`, `status`, `device_type` 같은 반복 필터는 시간축 전체에 퍼지고
- row group마다 local dictionary가 비슷하게 커진 채 반복되고
- bitmap은 짧은 run과 많은 chunk로 쪼개지기 쉽다

### 2. dictionary encoding과 bitmap locality는 같은 방향으로 좋아질 때가 많다

둘은 다른 레이어지만, 좋은 sort key는 보통 둘 다 동시에 밀어 준다.

| sort-key 패턴 | dictionary encoding 쪽 효과 | bitmap compression 쪽 효과 |
|---|---|---|
| low-cardinality filter 컬럼 우선 | row group당 local distinct가 줄고 code run이 길어진다 | 값별 bitmap long run, Roaring dense/run locality 증가 |
| `(country, status, event_date)` 같은 coarse-to-fine 복합 정렬 | 앞쪽 차원 dictionary가 작고, 뒤쪽 시간 컬럼도 segment-local 단조성을 얻기 쉽다 | dimension bitmap과 일부 numeric slice가 함께 안정된다 |
| `event_time` 우선, 차원 필터는 후순위 | time 계열 column은 정렬 이득을 보지만 다른 차원 dictionary/run은 흩어진다 | 차원 bitmap이 잘게 깨지고 WAH 계열 fill 이득이 약해진다 |
| high-cardinality id 우선 | 정렬 컬럼 자체 dictionary는 커지기 쉽고, 상관 없는 차원 code run이 끊긴다 | bitmap이 랜덤 membership에 가까워져 run 수가 늘어난다 |

중요한 점은 "정렬한 컬럼 하나"만 보는 게 아니라,  
**그 정렬이 다른 컬럼들의 local distinct와 code 반복성까지 같이 바꾸는가**다.

### 3. row-group 크기는 dictionary reset 비용과 bitmap reset 비용을 같이 만든다

row group이 너무 작으면 pruning granularity는 좋아져도 reset이 늘어난다.

- local dictionary가 row group마다 반복 생성된다
- 같은 값 band가 여러 row group에 걸쳐 쪼개진다
- WAH/EWAH/CONCISE clean run이 group 경계마다 다시 시작한다
- Roaring도 group마다 작은 active chunk 묶음이 생겨 header/container 수가 늘 수 있다

반대로 row group이 너무 크면:

- dictionary 중복은 줄고 bitmap run도 길어지기 쉽지만
- pruning 단위가 거칠어져 불필요한 scan row가 늘고
- hot/cold data가 한 group에 섞여 운영 유연성이 떨어질 수 있다

즉 row-group sizing은 "`작을수록 pruning 좋음`"으로 끝나지 않는다.  
sort key가 만든 값 band를 **몇 번 끊어 먹는지**까지 같이 봐야 한다.

### 4. 같은 sort key라도 codec별로 받는 이득이 다르다

| 물리 배치 신호 | dictionary 쪽 신호 | WAH/EWAH/CONCISE | Roaring |
|---|---|---|---|
| 전역적으로 강한 clustering + 큰 row group | local dictionary 작음, code run 김 | clean fill이 길게 이어져 크게 유리 | active chunk/run 수가 줄지만 chunk 경계 비용은 남음 |
| row group 내부만 정렬되고 group 경계가 많음 | group 내부 dict는 좋지만 reset 잦음 | fill run이 group마다 끊겨 이득이 제한됨 | local locality를 chunk 단위로 흡수해 상대적으로 덜 손해 |
| time-first append, 차원 필터는 보조 | 시간 컬럼 외엔 local distinct 개선이 작음 | dirty literal 증가, global fill 이득 약함 | sparse/dense 혼합을 적응적으로 흡수하기 쉬움 |
| high-cardinality-first 또는 랜덤 삽입 | dict footprint와 code run 모두 불리 | run-heavy 전제가 무너져 압축/scan 모두 약화 | 기본값으론 버틸 수 있지만 container churn을 감수 |

여기서 핵심은:

- WAH/EWAH/CONCISE는 `전역 clean run 지속성`에 민감하고
- Roaring은 `chunk-local density와 run 수 안정성`에 더 민감하다

그래서 warehouse sort key가 아주 강한 band locality를 만들고 row group도 그 band를 거의 자르지 않으면, WAH family 쪽 break-even이 훨씬 빨리 당겨진다.  
반대로 locality가 group-local 수준에 머물면 Roaring의 적응성이 계속 유리할 수 있다.

### 5. dictionary encoding이 좋아졌다고 bitmap도 자동으로 좋아지는 것은 아니다

둘이 자주 같은 방향으로 움직이긴 하지만, 완전히 같은 지표는 아니다.

- local dictionary가 작아도 predicate hit가 여러 row group에 조금씩 퍼지면 bitmap run은 짧을 수 있다
- 반대로 특정 값 bitmap은 길게 이어져도, 다른 high-cardinality 컬럼 dictionary는 여전히 클 수 있다

따라서 warehouse 설계에서는 아래 네 개를 따로 재야 한다.

1. row group당 local distinct count
2. encoded page의 RLE/bit-pack 효율
3. predicate별 row-group hit spread
4. bitmap 쪽 평균 run 길이 또는 active chunk 수

한 지표만 좋아졌다고 나머지가 따라온다고 가정하면 판단이 흔들린다.

### 6. 값별 bitmap과 bit-sliced bitmap은 sort key를 조금 다르게 소비한다

값별 bitmap은 low-cardinality 차원이 앞쪽 sort key에 있을 때 가장 직접적인 이득을 본다.

- `status = ACTIVE`
- `country = KR`
- `device_type = MOBILE`

같은 값 band가 길게 이어질수록 long run이 생기기 때문이다.

bit-sliced bitmap index는 numeric 값을 bit slice로 쪼개 저장하므로,  
정렬 이득이 조금 더 간접적이다.

- 숫자 컬럼의 상위 prefix가 row group 안에서 오래 유지되면 slice-local run이 길어진다
- 해당 숫자 컬럼과 상관된 차원이 앞쪽 sort key에 오면 slice density가 안정될 수 있다
- 하지만 숫자 분포와 무관한 sort key를 잡으면 slice마다 거의 비슷한 잡음 패턴이 반복될 수 있다

즉 BSI에서도 row group 경계와 sort key는 중요하지만,  
이득을 보는 단위가 "값 하나의 band"가 아니라 "bit prefix의 안정성"이라는 차이가 있다.

## 실전 선택 패턴

### 패턴 1: 대시보드 필터가 `country`, `status`, `event_date`

추천 방향은 보통 `country, status, event_date` 또는 `status, country, event_date` 같은 coarse-to-fine 정렬이다.

- 앞쪽 차원 dictionary/local distinct가 줄기 쉽다
- 값별 bitmap은 긴 run을 만든다
- 날짜는 band 내부에서 여전히 pruning 축으로 남는다

단, 날짜 범위 질의가 압도적으로 많다면 `event_date`를 완전히 뒤로 미루면 안 된다.

### 패턴 2: 로그 warehouse에서 freshness와 append 비용이 더 중요

`event_time` 우선 정렬이 운영상 맞을 수 있다.

- 최신 데이터 append/reclustering 비용이 낮다
- time pruning은 강하다
- 대신 차원 bitmap 압축 기대는 낮게 잡아야 한다

이 경우는 WAH family 극대화보다, Roaring이나 scan-friendly dictionary page 압축 쪽이 더 현실적인 기본값이 될 수 있다.

### 패턴 3: 사용자 ID 중심 정렬

lookup이나 merge join에는 편할 수 있지만 bitmap index 입장에서는 자주 불리하다.

- user id가 거의 unique면 dictionary footprint 절감이 작다
- `country/status` 같은 반복 필터가 랜덤하게 섞이기 쉽다
- row group을 키워도 value band가 잘 안 생긴다

bitmap warehouse 설계가 목적이라면 high-cardinality key를 맨 앞에 두는 결정은 신중해야 한다.

## 운영 체크리스트

sort key 후보를 비교할 때는 아래를 한 표로 같이 본다.

| 체크 항목 | 왜 같이 봐야 하나 |
|---|---|
| row group당 local distinct count | dictionary 크기와 code width를 바로 흔든다 |
| encoded page에서 RLE/bit-pack 비율 | sort key가 dictionary code 반복성으로 번역됐는지 보여 준다 |
| predicate별 row-group hit 개수 | pruning granularity와 spread를 보여 준다 |
| bitmap 평균 run 길이 또는 active chunk 수 | codec이 실제로 이득을 보는지 확인한다 |
| late ingest 후 locality 악화 속도 | 초기 bulk build와 운영 상태의 차이를 드러낸다 |

즉 좋은 sort key는 "정렬 직후 예쁜 분포"가 아니라,  
**운영 중에도 dictionary reset과 bitmap fragmentation을 천천히 만드는 키**다.

## 꼬리질문

> Q: low-cardinality 컬럼을 sort key 앞에 두면 왜 dictionary encoding도 좋아질 수 있나요?
> 의도: pruning과 local encoding을 분리해 이해하는지 확인
> 핵심: row group 안 distinct value 수와 dictionary code 반복 길이가 함께 줄어들 수 있기 때문이다.

> Q: row group을 작게 하면 pruning은 좋아지는데 왜 bitmap 압축은 나빠질 수 있나요?
> 의도: pruning granularity와 compression continuity를 분리하는지 확인
> 핵심: dictionary와 bitmap run이 group 경계마다 반복 리셋되기 때문이다.

> Q: time-first 정렬은 항상 나쁜가요?
> 의도: 운영 편의와 bitmap 압축을 균형 있게 보는지 확인
> 핵심: 아니다. freshness, append 비용, time pruning이 압도적이면 올바른 선택일 수 있지만 차원 bitmap 압축 기대는 낮춰야 한다.

## 한 줄 정리

warehouse bitmap index 설계에서 sort key는 pruning용 힌트가 아니라, local dictionary 크기와 row-group reset 빈도, 그리고 WAH/EWAH/CONCISE·Roaring의 실제 압축 결과를 함께 결정하는 상위 구조 선택이다.
