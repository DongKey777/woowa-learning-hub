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
