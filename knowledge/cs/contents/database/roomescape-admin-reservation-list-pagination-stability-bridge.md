---
schema_version: 3
title: roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지
concept_id: database/roomescape-admin-reservation-list-pagination-stability-bridge
canonical: false
category: database
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: ko
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- reservation-list-pagination
- stable-ordering
- offset-window-drift
aliases:
- roomescape 관리자 예약 목록 pagination
- roomescape 예약 목록 정렬 안정성
- roomescape 예약 목록 offset drift
- 룸이스케이프 관리자 목록 페이지 중복
- roomescape list stable order
symptoms:
- roomescape 관리자 예약 목록에서 1페이지 끝과 2페이지 시작이 자꾸 겹쳐 보여요
- created_at으로만 정렬했더니 예약 목록 새로고침마다 순서가 조금씩 달라져요
- 리뷰어가 관리자 목록에는 tie-breaker 정렬이 필요하다고 했는데 이유를 모르겠어요
intents:
- mission_bridge
- design
- troubleshooting
prerequisites:
- database/pagination-offset-vs-seek
- database/covering-index-composite-ordering
next_docs:
- database/pagination-duplicates-missing-symptom-router
- database/covering-index-composite-ordering
- software-engineering/pageable-service-contract-vs-query-model-pagination-bridge
linked_paths:
- contents/database/pagination-offset-vs-seek.md
- contents/database/pagination-duplicates-missing-symptom-router.md
- contents/database/covering-index-composite-ordering.md
- contents/spring/roomescape-admin-reservation-list-fetch-plan-bridge.md
- contents/software-engineering/pageable-service-contract-vs-query-model-pagination-bridge.md
confusable_with:
- database/pagination-duplicates-missing-symptom-router
- database/pagination-offset-vs-seek
- database/roomescape-reservation-create-read-after-write-bridge
- spring/roomescape-admin-reservation-list-fetch-plan-bridge
forbidden_neighbors: []
expected_queries:
- roomescape 관리자 예약 목록을 페이지로 나누면 같은 예약이 다음 페이지에 또 나오는 이유가 뭐야?
- reviewer가 created_at만 말고 id까지 같이 정렬하라고 한 뜻을 roomescape 목록 예시로 설명해줘
- roomescape admin 예약 목록에서 OFFSET pagination이 중간 insert 때문에 흔들린다는 말이 무슨 뜻이야?
- 관리자 예약 목록 쿼리에 stable order가 없으면 왜 새로고침마다 순서가 바뀌어 보여?
- roomescape 목록 조회에서 fetch plan 말고 정렬 계약도 따로 봐야 하는 이유가 뭐야?
- roomescape에서 방금 만든 예약이 관리자 목록 첫 조회에만 안 보일 때 pagination drift인지 stale read인지 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Woowa roomescape 미션에서 관리자 예약 목록을 페이지로 자를 때 왜 같은
  예약이 다음 페이지에 다시 보이거나 새 예약 때문에 경계가 밀리는지, created_at만
  으로는 왜 순서가 안 고정되는지 mission_bridge로 연결한다. 관리자 목록 잘랐더니
  중복됨, 새로고침할 때마다 순서가 흔들림, 동률 깨는 기준이 필요함, OFFSET 경계가
  밀림, 느린 쿼리보다 정렬 규약이 문제임 같은 자연어 paraphrase가 stable order와
  window drift 개념에 매핑된다.
---

# roomescape 관리자 예약 목록 페이지네이션 ↔ 안정 정렬과 window drift 브릿지

## 한 줄 요약

roomescape 관리자 예약 목록에서 pagination 문제는 "쿼리가 느리다"보다 "목록을 어떤 순서의 진실로 자를 것인가"에 가깝다. 그래서 리뷰에서 `created_at`만 정렬하지 말고 `id`까지 묶으라거나, `OFFSET`이 흔들릴 수 있다고 말하는 것은 모두 stable order를 먼저 고정하라는 뜻이다.

다만 "방금 만든 예약이 첫 조회에만 잠깐 안 보인다"면 stable order보다 [roomescape 예약 생성 직후 재조회 ↔ Read-After-Write 브릿지](./roomescape-reservation-create-read-after-write-bridge.md) 쪽이 더 직접적인 원인일 수 있다. 이 문서는 같은 데이터셋을 자를 때 경계가 흔들리는 문제를 다룬다.

## 미션 시나리오

roomescape 관리자 예약 목록은 초반에는 몇 건 안 보여서 `ORDER BY created_at DESC LIMIT 10 OFFSET 10` 같은 쿼리로도 충분해 보인다. 학습자도 "그냥 최신 예약부터 보여 주면 되지"라고 생각하기 쉽다.

하지만 예약이 몰리는 시간대에는 여러 row가 거의 같은 시각에 저장되고, 운영자가 목록을 보는 사이 새 예약이 계속 들어온다. 그러면 1페이지 마지막에 있던 예약이 2페이지 첫 줄에 또 보이거나, 방금 본 예약이 새로고침마다 조금씩 다른 위치로 움직인다. PR에서 "정렬 tie-breaker가 없다", "`OFFSET` window drift를 설명해 보라"는 코멘트가 붙는 장면이 바로 여기다.

## CS concept 매핑

roomescape 관리자 목록 pagination은 CS 관점에서 "결과 집합을 안정적으로 절단하는 규약"이다. 핵심은 빠른 쿼리 한 줄보다, 같은 데이터 집합을 다시 읽었을 때도 페이지 경계가 같은 규칙으로 유지되는지다.

| roomescape 장면 | 더 가까운 DB 개념 | 왜 그 개념으로 읽나 |
| --- | --- | --- |
| `created_at DESC`만으로 최신 예약 목록을 자름 | stable order, tie-breaker | 동률 row의 상대 순서가 고정되지 않으면 페이지 경계가 흔들린다 |
| 1페이지를 본 뒤 새 예약이 들어오고 2페이지를 읽음 | `OFFSET` window drift | `OFFSET 10`은 "방금 본 10개 다음"이 아니라 "현재 시점의 앞 10개를 건너뜀"이다 |
| 예약 목록 성능은 괜찮은데 중복/누락이 보임 | correctness before performance | fetch plan이 아니라 정렬 계약이 먼저 틀렸을 수 있다 |
| 페이지 크기와 정렬 컬럼이 계속 늘어남 | composite index ordering | stable order를 지키려면 정렬 축과 인덱스 축을 같이 설계해야 한다 |

짧게 말해, roomescape 목록 API는 "`LIMIT/OFFSET`을 붙였는가"보다 "`어떤 key 순서로 결과를 자르는가`"가 더 중요하다. `created_at`만으로는 같은 시각에 생성된 예약끼리 순서가 떠다닐 수 있으니, 보통은 `created_at DESC, id DESC`처럼 tie-breaker를 함께 고정해야 학습자도 리뷰 코멘트의 의도를 이해할 수 있다.

## 미션 PR 코멘트 패턴

- "`created_at`만 정렬하면 같은 시각 row의 순서가 불안정합니다."라는 코멘트는 DB가 동률 묶음을 임의 순서로 돌려줄 수 있으니 stable order를 완성하라는 뜻이다.
- "관리자 목록은 `OFFSET` pagination이라 중간 insert가 들어오면 경계가 밀릴 수 있습니다."라는 코멘트는 page 2가 page 1의 연장이 아니라 현재 시점 재계산 결과라는 뜻이다.
- "N+1만 해결해도 목록 품질이 끝난 건 아닙니다."라는 코멘트는 fetch plan과 페이지 절단 규약을 별개로 보라는 뜻이다.
- "정렬 조건을 바꿨으면 그 순서를 받쳐 주는 인덱스도 같이 보세요."라는 코멘트는 correctness를 잡은 뒤 성능까지 같은 축으로 맞추라는 뜻이다.

## 다음 학습

- 중복/누락 증상부터 원인을 빠르게 가르고 싶다면 `페이지네이션 중복/누락 원인 라우터`를 본다.
- `OFFSET`과 seek를 언제 갈라야 하는지 더 일반화해 보려면 `Pagination: Offset vs Seek`로 이어간다.
- `created_at, id` 같은 정렬 축을 어떤 복합 인덱스로 받쳐야 하는지 보려면 `커버링 인덱스와 복합 인덱스 컬럼 순서`를 읽는다.
- roomescape 목록에서 fetch plan 문제와 pagination 계약 문제를 같이 보고 싶다면 `roomescape 관리자 예약 목록 조회 ↔ fetch plan과 N+1 브릿지`를 함께 본다.
