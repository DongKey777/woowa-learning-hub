---
schema_version: 3
title: JOIN 결과 row 폭증 원인 라우터
concept_id: database/join-row-explosion-symptom-router
canonical: false
category: database
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids:
- missions/shopping-cart
- missions/roomescape
- missions/baseball
review_feedback_tags:
- join-cardinality-mismatch
- left-join-filter-placement
- distinct-hides-shape-bug
aliases:
- join row explosion router
- duplicated rows after join router
- join 결과가 갑자기 많아짐
- left join 후 row 폭증
- distinct로 가리기 전 원인 분기
- join 결과 폭발 원인
symptoms:
- JOIN만 붙였는데 결과 row 수가 갑자기 몇 배로 늘었다
- 고객 한 명만 기대했는데 같은 고객이 여러 줄로 반복돼 보인다
- LEFT JOIN 뒤에 결과가 중복처럼 보여서 DISTINCT를 바로 붙이고 싶다
- GROUP BY id로 줄이면 숫자는 맞는 것 같은데 왜 그런지 설명이 안 된다
intents:
- symptom
- troubleshooting
prerequisites:
- database/sql-relational-modeling-basics
- database/database-first-step-bridge
next_docs:
- database/sql-join-basics
- database/result-row-explosion-debugging-checklist
- database/distinct-vs-group-by-beginner-card
linked_paths:
- contents/database/sql-join-basics.md
- contents/database/result-row-explosion-debugging-checklist.md
- contents/database/join-row-increase-distinct-symptom-card.md
- contents/database/distinct-vs-group-by-beginner-card.md
- contents/database/left-join-filter-placement-primer.md
- contents/database/primary-foreign-key-basics.md
confusable_with:
- database/sql-join-basics
- database/distinct-vs-group-by-beginner-card
- database/result-row-explosion-debugging-checklist
forbidden_neighbors:
- contents/database/distinct-vs-group-by-beginner-card.md
expected_queries:
- JOIN 뒤에 결과가 갑자기 많아졌을 때 어디부터 의심해야 해?
- 같은 회원이 여러 줄로 보일 때 진짜 중복인지 조인 구조 때문인지 어떻게 나눠?
- LEFT JOIN 했더니 row가 늘어나는데 원인을 빠르게 분기하는 문서 있어?
- DISTINCT를 붙이기 전에 조인 결과 폭증 원인을 어떻게 진단해?
- GROUP BY id로 줄어들긴 하는데 왜 row가 늘었는지 먼저 알고 싶어
contextual_chunk_prefix: |
  이 문서는 학습자가 JOIN 뒤 결과 row가 갑자기 많아지거나 같은 부모가 여러 줄로
  반복돼 보여 당황할 때, 정상적인 1:N 관계인지, join key 유일성 가정이 깨졌는지,
  LEFT JOIN filter 위치가 잘못됐는지, 상세 결과를 요약 결과로 착각했는지 네 갈래로
  가르는 symptom_router다. join 결과 폭증, left join 뒤 중복처럼 보임, distinct를
  붙여야 하나, group by로 줄였는데 설명이 안 됨 같은 자연어 표현이 이 문서의
  원인 분기에 매핑된다.
---

# JOIN 결과 row 폭증 원인 라우터

## 한 줄 요약

> JOIN 뒤 row가 갑자기 늘었다고 해서 바로 DB가 중복을 만든 것은 아니다. 보통은 1:N 관계를 펼쳐 본 것인지, join key가 진짜 유일한지, LEFT JOIN 조건 위치가 맞는지, 내가 원하는 결과 단위가 상세인지 요약인지부터 갈라야 한다.

## 가능한 원인

1. 부모 1건에 자식 여러 건이 붙는 정상적인 1:N 또는 N:M 구조다. 고객 1명에 주문 여러 건, 주문 1건에 주문상품 여러 건이면 부모 row가 반복돼 보이는 것이 자연스럽다. 이 분기에서는 [SQL 조인 기초](./sql-join-basics.md)와 [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)를 먼저 본다.
2. join key가 유일하다고 믿었지만 실제 데이터나 제약이 그 보장을 하지 않는다. `email`, `code`, `name` 같은 일반 컬럼으로 JOIN하면 같은 값이 여러 건 붙어 row가 예상보다 더 커질 수 있다. 이때는 [기본 키와 외래 키 기초](./primary-foreign-key-basics.md)와 [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)로 가서 PK, FK, UNIQUE 가정을 다시 확인한다.
3. `LEFT JOIN`의 오른쪽 조건 위치가 어긋났다. 오른쪽 필터를 `ON`에 둘지 `WHERE`에 둘지에 따라 "오른쪽에서 어떤 row를 붙일지"와 "붙인 뒤 어떤 결과를 남길지"가 갈리는데, 이 차이를 놓치면 기대와 다른 row 수가 나온다. 이 분기에서는 [LEFT JOIN 필터 위치 입문서](./left-join-filter-placement-primer.md)로 바로 이어진다.
4. 사실 필요한 것은 고객별 한 줄 요약인데 고객-주문-주문상품 같은 상세 row를 펼쳐 보고 있다. 이 경우 `DISTINCT`나 `GROUP BY id`로 숫자만 줄이기 전에 결과 한 줄의 단위를 먼저 정해야 한다. 이 분기는 [JOIN 뒤 row가 늘었을 때 DISTINCT로 덮으면 안 되는 이유 카드](./join-row-increase-distinct-symptom-card.md)와 [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)로 이어진다.

## 빠른 자기 진단

1. 어떤 JOIN을 붙인 순간 row 수가 몇 배로 늘어났는지부터 본다. 고객, 주문, 주문상품처럼 각 관계가 1:1인지 1:N인지 말로 설명되지 않으면 cardinality 분기다.
2. join key가 PK, FK, UNIQUE로 실제 보장되는지 확인한다. "중복이 없을 것 같아서" 붙인 컬럼이면 uniqueness 가정 붕괴 분기를 먼저 의심한다.
3. `LEFT JOIN`이라면 오른쪽 조건이 `ON`에 있는지 `WHERE`에 있는지 확인한다. `WHERE`로 내려가면 NULL row가 탈락해 결과 의미와 row 수가 같이 바뀔 수 있다.
4. 마지막으로 내가 원하는 한 줄이 무엇인지 적어 본다. 고객 1명 단위 요약이 목적이면 `GROUP BY`나 사전 집계가 후보이고, 주문 상세가 목적이면 여러 줄이 정상일 수 있다.

## 다음 학습

- JOIN 자체의 포함 범위와 1:N mental model이 아직 흔들리면 [SQL 조인 기초](./sql-join-basics.md)로 가서 INNER, LEFT, cardinality부터 다시 고정한다.
- 어느 단계에서 몇 배가 붙는지 체크리스트 순서로 디버깅하고 싶다면 [Result-row Explosion Debugging Checklist](./result-row-explosion-debugging-checklist.md)를 이어서 본다.
- `DISTINCT`와 `GROUP BY` 중 무엇이 맞는지 결과 단위 관점에서 다시 나누려면 [DISTINCT vs GROUP BY 초보자 비교 카드](./distinct-vs-group-by-beginner-card.md)를 본다.
