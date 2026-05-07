---
schema_version: 3
title: Roaring Query Result Ordering Guide
concept_id: data-structure/roaring-query-result-ordering-guide
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- roaring-query-planner
- predicate-ordering
- repair-debt-reduction
aliases:
- Roaring query result ordering
- Roaring predicate ordering
- repairAfterLazy debt reduction
- shared bitmap intermediate
- selective AND before OR
- bitmap-wide repair avoidance
- query planner fan-in
symptoms:
- OR가 많다는 사실만 보고 repairAfterLazy debt를 판단하고, intermediate를 얼마나 일찍 넓혔는지와 몇 번 finalize했는지를 계산하지 않는다
- selective tenant/time/segment predicate를 나중에 걸어 넓은 OR intermediate를 먼저 만들고 대부분을 버린다
- sibling branch마다 같은 wide OR를 다시 만들어 shared intermediate reuse와 finalization boundary 최적화를 놓친다
intents:
- design
- troubleshooting
prerequisites:
- data-structure/roaring-lazy-union-and-repair-costs
- data-structure/roaring-bitmap-wide-lazy-union-pipeline
next_docs:
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-run-churn-observability-guide
- data-structure/bitmap-locality-remediation
- data-structure/roaring-run-optimize-timing-guide
linked_paths:
- contents/data-structure/roaring-bitmap-wide-lazy-union-pipeline.md
- contents/data-structure/roaring-lazy-union-and-repair-costs.md
- contents/data-structure/roaring-intermediate-repair-path-guide.md
- contents/data-structure/roaring-set-op-result-heuristics.md
- contents/data-structure/roaring-run-churn-observability-guide.md
- contents/data-structure/roaring-production-profiling-checklist.md
- contents/data-structure/bitmap-locality-remediation-playbook.md
- contents/data-structure/roaring-run-optimize-timing-guide.md
confusable_with:
- data-structure/roaring-lazy-union-and-repair-costs
- data-structure/roaring-intermediate-repair-path-guide
- data-structure/roaring-bitmap-wide-lazy-union-pipeline
- data-structure/roaring-production-profiling-checklist
forbidden_neighbors: []
expected_queries:
- Roaring query planner에서 selective AND를 wide OR보다 먼저 걸면 repairAfterLazy debt가 줄어드는 이유는?
- 같은 wide OR intermediate를 branch마다 다시 만들지 않고 reuse해야 하는 이유는?
- bitmap-wide repair debt를 active high key spread와 finalization 횟수로 보는 공식은?
- getCardinality serialize cache publish를 Roaring query 중간에 넣으면 왜 repair cost가 커져?
- Roaring-heavy query result ordering을 predicate selectivity 기준으로 설계하는 방법은?
contextual_chunk_prefix: |
  이 문서는 Roaring-heavy query planner에서 selective predicate를 먼저 적용하고
  shared intermediate를 재사용하며 exactness boundary를 늦춰 repairAfterLazy debt를
  줄이는 playbook이다. active high key spread, wide OR fan-in, finalization 횟수를 다룬다.
---
# Roaring Query Result Ordering Guide

> 한 줄 요약: Roaring-heavy query plan에서 `repairAfterLazy()` debt는 "`OR`가 많다"보다 **얼마나 일찍 intermediate를 넓히고, 같은 lazy 결과를 몇 번 다시 finalize하는가**에 더 가깝기 때문에, selective predicate를 먼저 묶고 shared intermediate를 재사용하는 쪽이 bitmap-wide repair를 훨씬 덜 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)
> - [Roaring Lazy Union And Repair Costs](./roaring-lazy-union-and-repair-costs.md)
> - [Roaring Intermediate Repair Path Guide](./roaring-intermediate-repair-path-guide.md)
> - [Roaring Set-Op Result Heuristics](./roaring-set-op-result-heuristics.md)
> - [Roaring Run-Churn Observability Guide](./roaring-run-churn-observability-guide.md)
> - [Roaring Production Profiling Checklist](./roaring-production-profiling-checklist.md)
> - [Bitmap Locality Remediation Playbook](./bitmap-locality-remediation-playbook.md)
> - [Roaring runOptimize Timing Guide](./roaring-run-optimize-timing-guide.md)

> retrieval-anchor-keywords: roaring query result ordering, roaring predicate ordering, filter ordering roaring bitmap, roaring query plan ordering, repairAfterLazy debt reduction, roaring intermediate result reuse, shared bitmap base reuse, roaring common subexpression cache, roaring wide or repair debt, roaring selective and before or, bitmap-wide repair avoidance, roaring query planner fan-in, horizontalOrCardinality planner, reusable intermediate roaring, query result handoff roaring, roaring repair scope reduction, roaring active high key spread, roaring result reuse guide

## 핵심 개념

Roaring query plan에서 `repairAfterLazy()` debt는 거칠게 보면 아래 두 항의 곱에 가깝다.

```text
repair debt ≈ provisional 결과가 넓힌 active high key 수
             × 같은 intermediate를 exact/materialized boundary로 끌어올린 횟수
```

즉 같은 predicate 집합이라도 planner가 아래를 어떻게 배치하느냐에 따라 debt가 크게 달라진다.

- selective `AND`, tenant/time/segment prune을 먼저 걸어 **넓어질 frontier를 줄이는가**
- 같은 wide `OR`를 sibling branch마다 다시 만들지 않고 **shared intermediate로 재사용하는가**
- exact count, `serialize`, cache publish를 중간에 여러 번 넣지 않고 **실제 handoff 직전 한 번만 finalize하는가**

핵심은 "`OR`를 없애라"가 아니다.  
**넓히기 전에 먼저 줄이고, 만든 intermediate는 다시 만들지 말고, exactness는 진짜 소비자 앞에서만 요구하라**가 더 정확하다.

## 1. predicate ordering이 왜 Roaring에서 특히 민감한가

Roaring에서는 같은 논리식도 intermediate shape가 다르면 `repairAfterLazy()` debt가 크게 달라진다.

| planner 선택 | intermediate shape | repair debt 영향 |
|---|---|---|
| selective `AND`/partition prune을 먼저 적용 | active `high key`와 chunk spread가 작아진다 | 내려간다 |
| wide `OR`를 먼저 합침 | provisional bitmap이 넓은 `high key` 대역에 퍼진다 | 올라간다 |
| 중간에 `getCardinality()`·`serialize()` 호출 | lazy 결과를 너무 일찍 finalize한다 | 올라간다 |
| shared intermediate를 한 번 만들어 재사용 | 같은 wide fan-in과 repair를 반복하지 않는다 | 내려간다 |

이 감각은 [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)과 [Roaring Lazy Union And Repair Costs](./roaring-lazy-union-and-repair-costs.md)에서 본 내용을 planner 관점으로 다시 읽은 것이다.

- lazy `OR`는 fan-in 동안엔 유리하다
- 하지만 결과를 넓힌 뒤 곧바로 selective filter가 따라오면 넓힌 provisional 상태 대부분이 버려진다
- 같은 넓은 intermediate를 branch마다 다시 만들면 savings보다 repeated repair가 더 커진다

따라서 "predicate ordering"의 본질은 SQL optimizer 일반론보다,  
**어느 시점에 Roaring intermediate를 넓히고 언제 exactness 경계를 밟게 하느냐**에 더 가깝다.

## 2. 나쁜 plan과 나은 plan

### 패턴 1. wide `OR`를 먼저 만들고 selective base를 나중에 건다

아래 모양은 Roaring에서 자주 비효율적이다.

```text
(country=KR OR country=JP OR country=TW)
  -> lazy OR over broad footprint
  -> exact count / threshold check
  -> AND tenant=42
  -> AND active_last_7d
```

문제는 단순하다.

- `country` bitmap 세 개를 먼저 합치며 provisional result가 넓은 `high key` 대역을 만진다
- 이후 `tenant=42`, `active_last_7d`가 대부분을 잘라내더라도 넓힌 fan-in과 repair debt는 이미 냈다
- planner threshold 확인 때문에 중간 `getCardinality()`가 들어가면 whole-bitmap `repairAfterLazy()`까지 붙는다

Roaring-heavy plan에서는 아래처럼 읽는 편이 더 낫다.

```text
base = tenant=42 AND active_last_7d
(country=KR AND base) OR (country=JP AND base) OR (country=TW AND base)
  -> narrower branch inputs
  -> smaller lazy OR frontier
  -> one final repair only if a whole result bitmap is truly needed
```

이 rewrite가 특히 잘 맞는 조건은 아래다.

- `base`가 분명히 selective하다
- `base`가 branch 사이에서 재사용된다
- branch 수가 너무 크지 않다

반대로 `base`가 거의 안 줄고 OR branch가 매우 많다면, 분배법칙 rewrite가 중복 `AND` 비용만 키울 수 있다.  
즉 규칙은 "항상 `AND` 먼저"가 아니라 **잘 줄어드는 shared base를 먼저**다.

### 패턴 2. 같은 wide `OR`를 sibling branch마다 다시 만든다

아래 식은 논리적으로는 자연스럽지만 Roaring intermediate reuse 관점에서는 낭비가 크다.

```text
((country=KR OR country=JP OR country=TW) AND premium)
OR
((country=KR OR country=JP OR country=TW) AND opted_in)
```

이 경우 `country in (KR, JP, TW)` bundle이 두 번 만들어지고,  
planner가 공통 부분식을 잡지 못하면 wide fan-in과 repair debt도 두 번 생긴다.

더 나은 기본형은 아래다.

```text
apac = OR(country=KR, country=JP, country=TW)   # planner/common-subexpression cache
(apac AND premium) OR (apac AND opted_in)
```

중요한 포인트는 "`apac`를 무조건 cache에 영구 보관하라"가 아니다.

- 같은 query 안의 sibling branch가 재사용하면 query-local intermediate로 충분하다
- 여러 요청이 반복 재사용하면 handoff 경계에서 한 번 repair하고, 필요할 때만 `runOptimize()`를 붙인다
- one-shot result라면 wide `OR`를 매번 cache publish하는 편이 더 비싸다

즉 **가장 먼저 줄일 대상은 repeated fan-in**이지, cache layer의 유무 자체가 아니다.

### 패턴 3. count만 필요한데 whole result를 먼저 materialize한다

아래 모양은 planner가 가장 쉽게 과잉 finalize를 만드는 패턴이다.

```text
OR(base∧A, base∧B, base∧C)
  -> repairAfterLazy
  -> getCardinality()
```

count만 필요하면 [Roaring Bitmap-Wide Lazy Union Pipeline](./roaring-bitmap-wide-lazy-union-pipeline.md)에서 본 것처럼 key-local cardinality 경로가 더 자연스럽다.

```text
base = tenant=42 AND active_last_7d
horizontalOrCardinality(base∧A, base∧B, base∧C)
```

이 경로는:

- shared `base`를 한 번 만든 뒤 branch에 재사용하고
- whole result bitmap을 오래 들고 있지 않으며
- bitmap-wide `repairAfterLazy()` 대신 key-local repair 후 즉시 합산한다

즉 predicate ordering과 intermediate reuse가 맞물리면,  
`repairAfterLazy()` debt 자체를 **"whole result를 만들지 않는 방향"**으로 지울 수 있다.

## 3. 무엇을 재사용할지부터 정한다

query plan에서 가장 재사용 가치가 큰 intermediate는 종종 "가장 넓은 OR 결과"가 아니라,  
여러 branch를 동시에 줄여 주는 **shared selective base**다.

| 재사용 후보 | 보통 가치가 큰 경우 | finalize 원칙 |
|---|---|---|
| `tenant ∧ time_window ∧ active` 같은 selective base | 같은 query의 여러 branch가 공통으로 사용 | query-local이면 premature repair를 피한다 |
| `country in (...)` 같은 wide OR bundle | 같은 bundle이 sibling branch나 반복 요청에서 재등장 | 중복 fan-in을 막되, true handoff 전까진 materialize를 늦춘다 |
| cardinality-only partial | planner threshold, precheck, top-k gate만 필요 | whole bitmap 대신 숫자/partial만 재사용한다 |
| cached final result bitmap | 여러 요청이 같은 결과를 읽고 serialize/mmap한다 | repair 후 reuse가 충분할 때만 `runOptimize()`를 고려한다 |

실전에서는 아래 우선순위가 자주 맞다.

1. 먼저 shared selective base를 찾는다.
2. 그 base가 OR branch 수를 실질적으로 줄이면 branch 앞단으로 밀어 넣는다.
3. wide OR bundle이 여러 곳에서 반복되면 common subexpression으로 한 번만 만든다.
4. exact artifact가 진짜 필요한 경계에서만 repair/materialize한다.

이 순서는 [Bitmap Locality Remediation Playbook](./bitmap-locality-remediation-playbook.md)가 말하는 "storage layout을 바꾸기 전에 query plan과 handoff 정책부터 본다"는 판단과도 이어진다.

## 4. planner가 바로 쓸 휴리스틱

| 관찰 신호 | 권장 ordering/reuse | 이유 |
|---|---|---|
| selective predicate가 active chunk 수를 크게 줄인다 | 그 predicate를 shared base로 먼저 계산 | wide `OR`가 넓힐 frontier를 미리 줄인다 |
| 같은 `IN (...)` 또는 wide `OR`가 여러 branch에 반복된다 | common subexpression으로 한 번만 만든다 | 같은 lazy fan-in과 repair debt를 두 번 내지 않는다 |
| exact count만 필요하다 | whole bitmap materialization보다 key-local cardinality 경로를 우선 | bitmap-wide repair를 피할 수 있다 |
| result가 한 번 쓰고 버리는 intermediate다 | cache publish와 `runOptimize()`를 늦춘다 | amortize되지 않는 finalize debt를 피한다 |
| base selectivity가 약하고 OR branch가 매우 많다 | 무리한 분배법칙 rewrite는 피한다 | duplicated `AND` cost가 savings를 먹을 수 있다 |

planner가 이 휴리스틱을 적용할 때 가장 흔한 실수는 두 가지다.

- selective predicate를 "나중에도 어차피 걸 것"이라며 wide `OR` 뒤로 미루는 것
- same template 안의 repeated OR bundle을 logical tree 그대로 두어 intermediate reuse를 놓치는 것

## 5. 효과는 어떻게 검증하나

rewrite가 맞았는지는 쿼리 템플릿 전후를 아래 축으로 비교하면 된다.

| 확인할 지표 | 기대 변화 | 의미 |
|---|---|---|
| `repair_scope=bitmap_wide` 비중 | 감소 | wide provisional result를 덜 남긴다 |
| `repair_cpu_ns / query_result_cpu_ns` | 감소 | fan-in savings보다 finalize debt가 작아진다 |
| `distinct_high_keys_touched`, `query_result_active_chunks` | 감소 | selective base가 OR frontier를 실제로 좁혔다 |
| `intermediate_result_type_total{op="or",type="bitmap"}` | 감소 또는 더 늦게 발생 | eager widening이 줄었다 |
| planner/common-subexpression cache hit | 증가 | 같은 OR bundle을 다시 만들지 않는다 |

특히 `repairAfterLazy()`가 cache publish 직전에만 남고, 그 cache hit가 충분히 높다면 그 debt는 감수할 만하다.  
반대로 one-shot query인데도 publish 직전 repair가 매번 반복되면, reuse 없는 handoff가 hot path를 오염시키고 있다는 뜻이다.

## 빠른 판단 문장

- selective `AND`가 뒤에 붙는 wide `OR`는 먼저 planner ordering부터 의심한다.
- 같은 `IN (...)` bundle이 sibling branch마다 반복되면 common subexpression reuse부터 본다.
- count만 필요한 경로는 whole result bitmap을 만들지 않는 쪽이 보통 더 낫다.
- `repairAfterLazy()`가 cache publish에 몰려 있어도 reuse hit가 낮으면 좋은 최적화가 아니다.

## 꼬리질문

> Q: selective `AND`를 항상 `OR` 앞에 두면 되나요?
> 의도: 분배법칙 rewrite의 조건을 아는지 확인
> 핵심: 아니다. shared base가 충분히 selective하거나 재사용될 때 유리하다. base가 약하고 branch 수가 많으면 duplicated `AND`가 더 비쌀 수 있다.

> Q: 왜 넓은 OR 결과보다 shared base를 먼저 재사용 대상으로 보나요?
> 의도: 어떤 intermediate가 frontier를 줄이는지 보는지 확인
> 핵심: shared base는 여러 branch의 active `high key`를 동시에 줄이지만, wide OR 결과는 이미 넓어진 provisional state일 수 있기 때문이다.

> Q: `repairAfterLazy()`를 cache publish 직전으로만 미루면 해결된 건가요?
> 의도: handoff 지연과 amortization을 구분하는지 확인
> 핵심: 아니다. 그 artifact가 실제로 여러 번 재사용돼야 의미가 있다. one-shot publish면 debt를 늦췄을 뿐 여전히 hot path 비용이다.

> Q: planner rewrite가 효과 있었는지는 무엇으로 확인하나요?
> 의도: shape 지표와 repair 지표를 같이 보는지 확인
> 핵심: `bitmap-wide repair`, `repair CPU share`, `distinct_high_keys_touched`, repeated OR build 수를 함께 비교해야 한다.

## 한 줄 정리

Roaring-heavy query plan에서 `repairAfterLazy()` debt를 줄이는 가장 실용적인 방법은 **shared selective predicate로 먼저 좁히고, repeated wide `OR`를 재사용하며, exact/materialized handoff는 진짜 소비자 앞에서 한 번만 밟는 것**이다.
