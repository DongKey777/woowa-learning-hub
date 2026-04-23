# Row-Ordering and Bitmap Compression Playbook

> 한 줄 요약: bitmap 압축 효율은 cardinality만으로 결정되지 않고, row를 어떤 순서로 배치하고 어느 segment 경계에서 끊는지에 따라 WAH/EWAH/CONCISE의 fill run과 Roaring의 container shape가 크게 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap](./roaring-bitmap.md)
> - [Roaring Container Transition Heuristics](./roaring-container-transition-heuristics.md)
> - [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)
> - [Roaring Bitmap Selection Playbook](./roaring-bitmap-selection-playbook.md)
> - [Compressed Bitmap Families: WAH, EWAH, CONCISE](./compressed-bitmap-families-wah-ewah-concise.md)
> - [Bit-Sliced Bitmap Index](./bit-sliced-bitmap-index.md)
> - [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)

> retrieval-anchor-keywords: row ordering bitmap compression, bitmap compression playbook, clustering bitmap index, sorted bitmap warehouse, segment boundary bitmap, row group bitmap compression, WAH EWAH CONCISE vs Roaring, run formation, clean run, dirty literal, bitmap row clustering, warehouse bitmap index, columnar bitmap sorting, roaring container locality, bitmap segment split, micro partition bitmap, row ordering sensitive bitmap, sorted ingest roaring, bitmap id locality, roaring vs ewah break even

## 핵심 개념

같은 row 집합이라도 **row ID 배치**가 달라지면 bitmap 모양이 달라진다.

- 값이 몰려 배치되면 긴 run이 생긴다
- 값이 랜덤하게 섞이면 짧은 run과 dirty literal이 늘어난다
- segment나 row group 경계가 자주 끊기면 원래 길게 이어질 run도 여러 조각으로 쪼개진다

즉 bitmap compression은 "몇 개가 1인가"보다  
"1과 0이 **어떤 순서로 이어지는가**"를 먼저 봐야 한다.

이 차이는 구현마다 다르게 나타난다.

- WAH/EWAH/CONCISE: 긴 clean word run이 생길수록 유리하다
- Roaring: 16-bit chunk 안에서 cardinality와 run 수가 안정적일수록 유리하다

## 깊이 들어가기

### 1. row ordering은 compression 이전의 shape control이다

bitmap codec은 마지막 단계다.  
그 전에 정렬과 clustering이 bitmap의 원재료를 만든다.

같은 predicate bitmap도 아래처럼 완전히 다른 모양이 된다.

| row 배치 | bitmap 모양 | 압축 결과 감각 |
|---|---|---|
| 랜덤 삽입 순서 | `1010010110...`처럼 자주 끊긴다 | WAH 계열은 literal 비중이 커지고, Roaring은 sparse array container가 많이 남는다 |
| 단일 low-cardinality 컬럼 기준 정렬 | `00001111110000`처럼 값별 덩어리가 생긴다 | WAH 계열 fill run이 길어지고, Roaring은 dense/run container가 늘 수 있다 |
| `(country, date)` 같은 복합 정렬 | 국가별 큰 덩어리 안에서 시간 지역성까지 생긴다 | 값별 bitmap뿐 아니라 slice bitmap도 segment-local run이 길어질 수 있다 |
| 시간만 정렬했지만 질의는 국가 필터 중심 | 동일 국가 row가 멀리 흩어진다 | warehouse row group이 있어도 country bitmap은 잘 압축되지 않는다 |

핵심은 sorting key가 **자주 필터되는 차원과 상관관계가 있는가**다.

### 2. clustering은 run 길이뿐 아니라 run 안정성도 바꾼다

초기 bulk load에서는 잘 정렬돼 있었더라도, 이후 late-arriving row나 작은 upsert가 누적되면 run이 쉽게 깨진다.

- append-only fact table에서 날짜 정렬은 유지되기 쉽다
- 하지만 `country`, `device_type`, `campaign_id` 같은 차원 필터는 시간이 지나며 섞일 수 있다
- compaction 없이 micro-batch만 쌓이면 "논리적으로는 clustered"인데 물리적으로는 segment별 fragmented 상태가 된다

따라서 warehouse bitmap은 처음 sort order만 볼 게 아니라:

- 신규 ingest가 기존 sort order를 얼마나 깨는지
- compaction/reclustering가 있는지
- query가 최신 hot segment에 얼마나 편중되는지

를 같이 봐야 한다.

### 3. segment boundary는 run을 리셋하는 비용이다

물리 segment, row group, micro-partition 경계는 자주 "압축 reset point"처럼 작동한다.

예를 들어 `status = ACTIVE` row가 전체 테이블 기준으로는 긴 구간을 이루더라도:

- row group이 너무 작으면 같은 값 덩어리가 여러 segment에 분산된다
- segment마다 bitmap을 따로 만들면 fill run도 segment마다 다시 시작한다
- dictionary/page 경계가 자주 바뀌면 slice-local locality도 약해진다

그래서 운영 감각은 이렇다.

| 경계 설계 | WAH/EWAH/CONCISE 영향 | Roaring 영향 |
|---|---|---|
| 큰 row group, 안정적 clustering | fill word가 길게 이어져 좋다 | 같은 chunk 안에서 dense/run container가 안정되기 쉽다 |
| 지나치게 작은 segment | long run이 여러 개의 짧은 run으로 분해된다 | high key 수와 작은 container 수가 늘어 header/lookup 오버헤드가 늘 수 있다 |
| 정렬과 무관한 파티션 절단 | clean run이 segment 시작점마다 재시작된다 | predicate hit가 많은 chunk가 여러 segment에 흩어져 sparse array가 많아질 수 있다 |

중요한 구분이 하나 더 있다.

- warehouse의 `segment boundary`: 물리 파일/row group 경계
- Roaring의 `chunk boundary`: 상위 16비트 기준 logical container 경계

둘은 다른 경계지만, 둘 다 "연속성 단절"을 만들 수 있다는 점에서 함께 봐야 한다.

### 4. WAH/EWAH/CONCISE는 정렬 이득을 더 직접적으로 받는다

WAH/EWAH/CONCISE는 bitmap 전체를 word-aligned run scan 모델로 압축한다.  
그래서 정렬이 좋아져 clean word가 길어지면 압축률과 scan cost가 같이 좋아진다.

- **WAH**: 긴 fill word가 뚜렷하게 생길수록 단순한 비용 모델이 잘 맞는다
- **EWAH**: clean/dirty word 묶음 관리가 좋아 append와 segment scan에 실용적이다
- **CONCISE**: 짧은 hole이 섞여 있어도 더 공격적으로 줄일 여지가 있다

반대로 아래 패턴에서는 이득이 급격히 줄어든다.

- row가 랜덤 섞여 dirty literal이 많을 때
- 같은 값 군집이 segment 경계마다 잘릴 때
- low-cardinality 컬럼이라도 sort key와 상관이 약해 row가 넓게 퍼질 때

즉 WAH family에서 좋은 질문은 "`1`이 몇 개인가?"가 아니라  
"word 경계를 넘어 **clean run이 얼마나 오래 유지되나?**"다.

### 5. Roaring은 row ordering을 chunk-local density 문제로 받는다

Roaring은 whole-bitmap run codec이 아니라, 각 16-bit chunk를 array/bitmap/run 중 하나로 둔다.  
그래서 row ordering 효과도 "전체 run"보다 **chunk별 shape**로 나타난다.

정렬과 clustering이 좋으면:

- hit row가 일부 chunk에 몰려 dense bitmap container가 생길 수 있다
- 연속 row ID가 유지되면 run container가 유리해진다
- chunk별 cardinality가 안정돼 `array <-> bitmap` churn이 줄어든다

정렬과 경계 설계가 나쁘면:

- 같은 predicate hit가 많은 chunk 수를 늘려 container 개수가 증가한다
- chunk마다 애매한 cardinality가 생겨 `4096` 근처 churn hotspot이 많아진다
- bulk build 직후엔 run-friendly였지만 segment merge 후 row ID 재배치가 바뀌어 runOptimize 이득이 줄 수 있다

즉 Roaring에서 보는 운영 지표는 아래가 더 직접적이다.

- chunk별 cardinality histogram
- chunk별 run 수
- `4096` 근처 container 개수
- segment별 active chunk 수

Roaring에서 sorted ingest와 ID locality가 이 지표들을 어떻게 바꾸고, 그 결과 `Roaring vs WAH/EWAH` break-even이 어디로 움직이는지는 [Roaring Run Formation and Row Ordering](./roaring-run-formation-and-row-ordering.md)에서 한 단계 더 구체적으로 정리했다.

### 6. warehouse에서 sorting key를 고르는 실전 질문

bitmap compression을 노린다면 sort key는 단순히 "시간순 ingest가 편한가"만으로 정하면 안 된다.

정렬 키를 dictionary encoding, row-group sizing, bitmap codec과 한 프레임에서 같이 비교하려면 [Warehouse Sort-Key Co-Design for Bitmap Indexes](./warehouse-sort-key-co-design-for-bitmap-indexes.md)를 이어서 보면 좋다.

1. 가장 자주 필터되는 low-cardinality 차원이 있는가
2. 그 차원이 현재 sort key 앞부분에 있는가
3. segment 크기가 그 차원의 군집을 유지할 만큼 충분히 큰가
4. late row와 update가 그 군집을 얼마나 빨리 깨는가

빠른 판단표는 아래와 같다.

| 상황 | 더 유리한 방향 |
|---|---|
| `country`, `status`, `device_type`처럼 값 종류가 작고 필터가 반복된다 | 해당 차원을 앞쪽 sort key로 두어 WAH 계열 clean run과 Roaring dense/run locality를 동시에 노린다 |
| 시간 범위 질의가 절대적이고 차원 필터는 보조적이다 | 시간 정렬을 유지하되, 차원 bitmap 압축 기대는 낮게 잡는다 |
| micro-partition이 지나치게 많아 같은 값이 매 segment마다 조금씩만 있다 | segment 수 축소나 compaction을 먼저 검토한다 |
| online update가 많아 clustering 유지가 어렵다 | WAH family보다 Roaring 쪽이 운영상 덜 민감할 수 있다 |

### 7. bit-sliced / 값별 bitmap에서도 동일한 원리가 반복된다

bit-sliced bitmap index나 값별 bitmap index도 결국 row ordering의 영향을 그대로 받는다.

- 값별 bitmap은 해당 값이 모여 있을수록 long run이 생긴다
- bit slice bitmap은 상위 비트가 비슷한 값이 모여 있을수록 slice-local run이 길어진다
- row group이 자주 바뀌면 slice마다 "거의 비슷하지만 조금 다른" pattern이 반복돼 압축 이득이 줄 수 있다

그래서 warehouse에서 숫자 컬럼을 BSI로 둘 때도:

- 값 범위 분포만 보지 말고
- 정렬 키와 값의 상관관계
- row group 경계가 동일 prefix 값을 얼마나 자주 쪼개는지

를 같이 봐야 한다.

## 실전 시나리오

### 시나리오 1: 국가별 사용자 세그먼트 warehouse

`country` 기준 정렬 후 row group을 크게 잡으면 `country = KR` bitmap은 긴 run을 만들기 쉽다.  
이 경우 WAH/EWAH/CONCISE는 fill run 이득이 커지고, Roaring도 일부 chunk가 dense/run-friendly해진다.

### 시나리오 2: 시간순 event table에서 국가 필터를 자주 거는 경우

최근 이벤트 append는 편하지만 `country` bitmap은 시간축 전체에 흩어진다.  
같은 cardinality여도 WAH 계열은 dirty literal이 늘고, Roaring은 많은 sparse container로 나뉠 수 있다.

### 시나리오 3: micro-partition이 과도한 columnar store

각 partition 안에서는 정렬이 괜찮아 보여도, 같은 값이 수백 개 segment에 조금씩 들어 있으면 long run이 segment마다 끊긴다.  
압축 문제처럼 보이지만 실제 원인은 segment granularity일 수 있다.

### 시나리오 4: bulk build 뒤 online revoke가 누적되는 대상군 bitmap

초기엔 정렬된 대상 ID 덕분에 Roaring run container나 WAH fill run이 잘 먹는다.  
하지만 revoke가 랜덤하게 박히면 run fragmentation이 빨라져, 정렬 이득이 점차 사라진다.

## 비교 표

| 관찰 포인트 | WAH/EWAH/CONCISE에서 중요하게 보는 것 | Roaring에서 중요하게 보는 것 |
|---|---|---|
| 정렬이 좋을 때 | clean word run 길이, fill 비중 | chunk-local dense/run container 비중 |
| 정렬이 나쁠 때 | dirty literal 증가, skip 이점 감소 | sparse array container 증가, container 수 증가 |
| segment가 작을 때 | run reset이 잦아짐 | active high-key 수와 작은 container 수가 늘어남 |
| late update가 많을 때 | run fragment가 빠르게 증가 | `array/bitmap/run` 전환 churn이 늘어남 |
| 튜닝 지표 | fill/literal 비율, 평균 run 길이 | chunk cardinality histogram, run 수, `4096` 근처 container 개수 |

## 꼬리질문

> Q: 같은 cardinality인데 왜 압축률이 달라지나요?
> 의도: 개수와 순서를 분리해 이해하는지 확인
> 핵심: bitmap compression은 1의 개수보다 1과 0이 어떤 run으로 이어지는지가 더 중요하기 때문이다.

> Q: row ordering이 좋으면 무조건 WAH/EWAH/CONCISE가 Roaring보다 좋은가요?
> 의도: whole-bitmap run compression과 chunk-local 적응을 구분하는지 확인
> 핵심: 아니다. ordering이 좋아도 update와 mixed-density가 크면 Roaring이 더 실용적일 수 있다.

> Q: segment boundary는 왜 별도 변수인가요?
> 의도: 정렬과 물리 저장 단위를 분리해 이해하는지 확인
> 핵심: 논리적으로는 한 덩어리인 run도 segment마다 따로 저장하면 여러 개의 짧은 run으로 끊기기 때문이다.

## 한 줄 정리

bitmap compression은 codec 선택만의 문제가 아니라, row ordering과 segment boundary가 run formation을 어떻게 바꾸는지까지 같이 설계해야 WAH/EWAH/CONCISE와 Roaring의 실제 이득을 제대로 얻을 수 있다.
