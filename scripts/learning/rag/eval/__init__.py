"""IR evaluation harness for the CS RAG retrieval pipeline.

Modules:
- metrics: graded nDCG, primary_nDCG, MRR, hit@k, recall@k, companion_coverage, forbidden_rate
- dataset: load and convert golden fixture into graded qrels
- buckets: bucket grouping + macro average
- manifest: run report schema and validation
- cache: model+device keyed embedder cache with fail-fast manifest checks
- split: tune/holdout deterministic split
- hard_regression: primary max_rank + forbidden_paths gates
- runner: orchestrates an A/B run, emits a report

Design contract: see plan §1.1 (P1.1 IR 평가 하네스).
"""
