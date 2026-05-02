# Sparse Effect Analysis - 2026-05-01

## Verdict

Sparse produced no rank or headline quality movement on the 101-query holdout. Its measured direct rescore stage is small, but total p95 is higher/noisy enough that sparse should be treated as default-on pending one more focused gate, not as proven useful.

## Headline

| Run | primary nDCG | graded nDCG | MRR | hit | recall | p50 ms | p95 ms | hard failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fts,dense` | 0.913484 | 0.912562 | 0.930693 | 0.940594 | 0.919142 | 452.3 | 613.2 | 10 |
| `fts,dense,sparse` | 0.913484 | 0.912493 | 0.930693 | 0.940594 | 0.919142 | 450.5 | 586.3 | 10 |

## Delta

- `primary_ndcg_delta`: `0.0`
- `graded_ndcg_delta`: `-6.842091486447544e-05`
- `mrr_delta`: `0.0`
- `hit_delta`: `0.0`
- `recall_delta`: `0.0`
- `p50_latency_delta_ms`: `-1.7151670035673305`
- `p95_latency_delta_ms`: `-26.898500000243075`
- `hard_failure_delta`: `0`
- `top1_changed_count`: `1`
- `top10_changed_count`: `98`
- `primary_rank_improved_count`: `0`
- `primary_rank_worsened_count`: `0`

## Sparse Stage

- `lance_sparse_rescore`: p50 `3.622` ms, p95 `4.639` ms, mean `3.663` ms

## Bucket Deltas

### category
| bucket | n | primary_delta_mean | rank_delta_sum | top1_changed | top10_changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `database` | 12 | 0.000000 | 0 | 0 | 12 |
| `design-pattern` | 39 | 0.000000 | 0 | 1 | 36 |
| `language` | 6 | 0.000000 | 0 | 0 | 6 |
| `network` | 4 | 0.000000 | 0 | 0 | 4 |
| `operating-system` | 3 | 0.000000 | 0 | 0 | 3 |
| `security` | 6 | 0.000000 | 0 | 0 | 6 |
| `software-engineering` | 3 | 0.000000 | 0 | 0 | 3 |
| `spring` | 26 | 0.000000 | 0 | 0 | 26 |
| `system-design` | 2 | 0.000000 | 0 | 0 | 2 |

### language
| bucket | n | primary_delta_mean | rank_delta_sum | top1_changed | top10_changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `en` | 14 | 0.000000 | 0 | 0 | 14 |
| `ko` | 30 | 0.000000 | 0 | 1 | 27 |
| `mixed` | 57 | 0.000000 | 0 | 0 | 57 |

### difficulty
| bucket | n | primary_delta_mean | rank_delta_sum | top1_changed | top10_changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `beginner` | 76 | 0.000000 | 0 | 1 | 73 |
| `unknown` | 25 | 0.000000 | 0 | 0 | 25 |

### intent
| bucket | n | primary_delta_mean | rank_delta_sum | top1_changed | top10_changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparison` | 21 | 0.000000 | 0 | 0 | 19 |
| `deep-dive` | 3 | 0.000000 | 0 | 0 | 3 |
| `definition` | 22 | 0.000000 | 0 | 0 | 22 |
| `symptom` | 6 | 0.000000 | 0 | 0 | 6 |
| `unknown` | 49 | 0.000000 | 0 | 1 | 48 |

## Next Gate

1. Keep `fts,dense,sparse` as production default for now because that is the current product decision.
2. Do not add category-gating yet: this holdout shows no category/language bucket where sparse creates measurable lift.
3. If a second focused failure-cohort run also shows zero rank movement, reduce sparse to either category-gated sparse or lower sparse weight.

JSON artifact: `reports/rag_eval/sparse_effect_analysis_20260501T1455Z.json`
