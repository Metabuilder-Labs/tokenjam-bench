# Real benchmark evidence — TokenJam Bench dashboard (2026-06-26)

Every number on the production dashboard (Overview / Benchmarks / Business
Impact) is generated from the runs below. **No seeded, mock, or synthetic
data** — `scan_runs()` skips any artifact marked `mock`/`demo`.

- **Provider:** DeepSeek (only key available)
- **Pair:** `deepseek-reasoner` (original) → `deepseek-chat` (candidate)
- **Judge:** DeepEval `correctness` (GEval, threshold 0.5) via `TJBENCH_JUDGE=deepseek`
- **Totals:** 77 tasks · spend $0.0390 → $0.0199 (**−49.0%**) · output tokens 18,193 → 8,631 (−52.6%)

| Suite | Pass (orig→cand) | Δcost | n | McNemar p | Verdict |
|---|---|---|---|---|---|
| `customer-support` | 8% → 8% | -47.2% | 12 | 1.000 | no_significant_regression |
| `email-assistant` | 83% → 83% | -50.0% | 12 | 1.000 | no_significant_regression |
| `enterprise-rag` | 8% → 8% | -42.8% | 12 | 1.000 | no_significant_regression |
| `gsm8k` | 100% → 100% | -54.5% | 12 | 1.000 | no_significant_regression |
| `humaneval` | 92% → 100% | -53.7% | 12 | 1.000 | no_significant_regression |
| `judged` | 40% → 60% | -58.6% | 5 | 1.000 | insufficient_evidence |
| `research-assistant` | 0% → 17% | -33.8% | 12 | 0.500 | no_significant_regression |

## Reproduce

```bash
export DEEPSEEK_API_KEY=sk-...        # env only; never committed
./scripts/run_real_benchmarks.sh
tjb serve
```

## Honest reading

- **Cost savings (−49%) and the `no_significant_regression` verdicts are the
  load-bearing results** — measured from real API token usage at list price.
- **High-coverage executable suites pass cleanly**: `gsm8k` 100%→100%,
  `humaneval` 92%→100% — the cheaper model held accuracy at roughly half the cost.
- **Low absolute pass-rates on `customer-support` / `enterprise-rag` /
  `research-assistant`** are genuine: under strict GEval correctness the models
  often ask clarifying questions or give generic replies instead of the grounded
  reference answer (verified in each task's `original_detail`/`candidate_detail`).
  Both models score similarly, so the *delta* (regression detection) is valid
  even where absolute quality is modest.
- **`judged` is `insufficient_evidence`** — only 5 built-in cases (n<10); honest,
  not hidden.
- **Agentic suites (n8n, coding-workflow) are absent**: they need function calling
  on both models, which `deepseek-reasoner` (R1) lacks. They carry no real
  evidence and do not appear on the dashboard.

_Raw JSON + HTML proof artifacts for each run are committed under `live/2026-06-26-real-dashboard/`._