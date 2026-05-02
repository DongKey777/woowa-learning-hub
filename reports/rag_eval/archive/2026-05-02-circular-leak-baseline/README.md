# 2026-05-02 Circular-leak Baseline Reports — Archived

## 정의

이 폴더의 모든 측정 리포트는 **circular qrel validation leak 활성 상태**에서 생성됐다. retrieval quality 증거로 사용하면 안 된다.

## Leak 정의

`scripts/learning/rag/corpus_loader.py:_emit_chunks`가 frontmatter `expected_queries`를 다음 모든 indexing channel에 주입했었다:

1. `chunk.body` (anchor_suffix append) → dense vector / FTS / sidecar:body 모두 오염
2. `chunk.anchors` (document_aliases 의 일부) → lexical_sidecar:aliases 오염
3. (`chunk.embedding_body`는 fix 전에도 분리되어 있었음)

동시에 `r3_corpus_v2_qrels_*.json`은 같은 `expected_queries`를 qrel `prompt`로 자동 생성했다. 즉 query Q1에 대해 doc X가 정답이라는 qrel이 있고, *X의 alias로 Q1이 indexed*되어 있으니 **alias indexing만으로 자동 1.0 recall**이 보장된다.

→ 측정값은 *retrieval correctness*가 아닌 **alias indexing regression check**.

## Fix

`fix/r3-circular-leak-hotfix` branch (commit 32dc8f4, later main에 cherry-pick) 가 `frontmatter_expected_queries` parameter를 `_emit_chunks` signature에서 제거. expected_queries는 이제 *qrel seed only*, indexing 채널 진입 ❌.

## 본 archive 활용

| 용도 | OK? | 비고 |
|---|---|---|
| Retrieval quality 증거 | ❌ | circular validation, 측정값 신뢰 ❌ |
| Alias indexing regression check | ✅ | indexing path bug 회귀 시 측정값 변동 감지 |
| Historical reference (Phase 6 결과 비교) | ✅ | "leak 적용 시 1.0 → fix 후 0.X" 차이로 leak 영향력 감각 |
| System 설계 결정 근거 | ❌ | corpus-agnostic 원칙 — 이 측정값으로 architecture/model 결정 ❌ |

## 진짜 baseline은?

새 측정 시점:
1. fix branch main 통합 후 corpus_loader 갱신
2. Real qrel suite (`tests/fixtures/r3_qrels_real_v1.json`) human-curated 200q × 6 cohort 작성
3. Pilot 50 docs frontmatter v3 적용 후 R3 system spec-aligned 측정
4. → `reports/rag_eval/r3_pilot_baseline_<timestamp>.json` 가 진짜 ground truth

## File 분류

### holdout reports (101q split + 338q variants)
- `next_legacy_v2_holdout_*.json` — legacy v2 + MiniLM
- `next_lance_v3_holdout_*.json` — Lance v3 + BGE-M3
- `next_lance_modality_ablation_holdout_*.json` — modality ablation 3-run
- `next_failure14_top10_diagnosis_*.json` — 14 failure subset
- `next_lance_failure14_baseline_*.json`
- `next_improvement_decision_*.md` — cutover gate relaxation 결정 기록

### r3 backend compare iterations (208q gate × 5)
- `r3_backend_compare_208q_production_r3_auto_20260502T0845Z` (early)
- `r3_backend_compare_208q_production_r3_auto_20260502T0924Z`
- `r3_backend_compare_208q_production_r3_auto_20260502T1000Z`
- `r3_backend_compare_208q_production_r3_auto_20260502T1018Z`
- `r3_backend_compare_208q_production_r3_auto_20260502T1052Z` (final selected)
- 100q variants (sidecar / reranker / retrieval 기타)

### r3 local smoke
- `r3_0c8fd9f_local_smoke_20260502T0852Z.json` — 초기 artifact
- `r3_5730e6e_local_smoke_20260502T0932Z.json`
- `r3_61216f2_runtime_788ee99_local_smoke_20260502T1059Z.json` — production 직전 smoke

### legacy rollback smoke
- `r3_legacy_rollback_archive_smoke_*` — v2 archive smoke
- `r3_legacy_rollback_current_corpus_smoke_*` — current corpus + v2 backend smoke

### sparse effect
- `sparse_effect_analysis_20260501T1455Z.json/.md` — sparse on/off (delta 0.0, 단 alias 통한 측정)

## 참고

- 본 폴더 작성: 2026-05-02
- Archive 결정 plan: `/Users/idonghun/.claude/plans/abundant-humming-lovelace.md` Section 3.2
- Fix commit: `32dc8f4` `fix/r3-circular-leak-hotfix`
- Production lock 갱신 시점: Phase 6 Pilot 측정 통과 후
