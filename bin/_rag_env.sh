# Production R3 RAG env defaults — sourced by bin/* wrappers.
#
# Why a shared file: AI sessions that forget the AGENTS.md contract
# would otherwise hit silent degradation (95.5% Pilot baseline →
# 90.5% raw, or worse). Setting these defaults at every wrapper
# entry point makes the contract failure-resistant. Override in the
# calling shell when you intentionally want a different mode.
#
# Don't change these defaults without re-running cohort_eval — they
# are the runtime config the closing report measured 95.5% under.
export WOOWA_RAG_R3_ENABLED="${WOOWA_RAG_R3_ENABLED:-1}"
export WOOWA_RAG_R3_RERANK_POLICY="${WOOWA_RAG_R3_RERANK_POLICY:-always}"
export WOOWA_RAG_R3_FORBIDDEN_FILTER="${WOOWA_RAG_R3_FORBIDDEN_FILTER:-1}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"

# Phase 9.3 — refusal sentinel threshold. The 2026-05-05 recalibration
# now treats learner safety as the shipping gate: only a 0.05-grid
# threshold that preserves every paraphrase_human positive and still
# catches at least half of corpus_gap_probe negatives can become the
# runtime default. The latest scored report did not meet that bar, so
# the wrapper stays on the production-safe disabled default.
# The calibration artifact still records the raw F1-optimal boundary,
# the zero-spurious numeric candidate, cross-encoder coverage, and this
# wrapper's parsed default so future reruns can re-enable the sentinel
# without manual shell inspection drift. Threshold semantics remain
# strict (`score < threshold`) when operators override this locally.
# See reports/rag_eval/refusal_threshold_calibration.json.
# Override: WOOWA_RAG_REFUSAL_THRESHOLD=<float> to opt in, or `off`.
export WOOWA_RAG_REFUSAL_THRESHOLD="${WOOWA_RAG_REFUSAL_THRESHOLD:-off}"

# Phase 9.2 — personalization-aware ranking. Activates concept_id-based
# score adjustment (mastered_concepts demote -0.15, uncertain/underexplored
# boost +0.10) in R3 fusion before reranker. Originally default off because
# v3 corpus migration was sparse (~3% concept_id coverage). After 2026-05-07
# corpus cycle (commit c12a0f5 + index-v1.0.0-corpus@c12a0f5 release),
# concept_id coverage = 99% (2547/2560 docs), comfortably above the ≥30%
# activation threshold the original Phase 9.2 spec required. Personalization
# now adds measurable retrieval lift on the learner-profile-aware path.
# Override: WOOWA_RAG_PERSONALIZATION_ENABLED=0 to disable.
export WOOWA_RAG_PERSONALIZATION_ENABLED="${WOOWA_RAG_PERSONALIZATION_ENABLED:-1}"
