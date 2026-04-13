"""Woowa learning-hub: CS RAG + 4-dim scoring + drill subsystem.

This package is imported lazily by scripts/workbench/core/coach_run.py so
that missing ML dependencies (sentence-transformers, torch) degrade to
cs_readiness.state="missing" instead of crashing the whole pipeline.
"""
