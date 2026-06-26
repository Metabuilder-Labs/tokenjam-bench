# Real-world test — DeepSeek `reasoner → chat`, live (2026-06-26)

End-to-end live benchmark of a real cost-saving migration: replacing the
expensive **`deepseek-reasoner`** (R1) with the cheaper **`deepseek-chat`** (V3)
on three benchmark families. Every number below was produced by the real
pipeline against the live DeepSeek API — no mock models, no hand-written
figures. CIs / p-values / verdicts come from `tjbench.pipeline.assemble_proof`
(Wilson interval + exact McNemar); costs are measured from token usage.

- **Date:** 2026-06-26, 08:47–08:50 IST
- **TokenJam under test:** 0.5.1
- **Original → Candidate:** `deepseek:deepseek-reasoner` → `deepseek:deepseek-chat`
- **Judge (judged suite):** DeepEval, DeepSeek-backed, metric = correctness
- **Sampling:** `k=1`, temperature `0.0` (deterministic)

## Headline

On **gsm8k** and **humaneval** the cheaper model **matched or beat** the
reasoner while using far fewer tokens — verdict *no_significant_regression*. On
the small **judged** suite (only 5 tasks) the harness correctly refuses to draw
a conclusion: *insufficient_evidence*. This is the intended behaviour — the
product **never overstates**; it hedges when the evidence is thin.

## Results

| Benchmark | n | reasoner pass | chat pass | Δ pass-rate | 95% CI (Δ) | McNemar (b/c, p) | Verdict | Δ cost (measured)¹ | Δ cost (real rates)² |
|-----------|---|---------------|-----------|-------------|------------|------------------|---------|--------------------|----------------------|
| **gsm8k**     | 12 | 12/12 (100%) | 12/12 (100%) | +0.0 pp | [+0.0, +0.0] | 0 / 0, p=1.000 | `no_significant_regression` | −57.0% | **−78.5%** |
| **humaneval** | 10 | 9/10 (90%)   | 10/10 (100%) | +10.0 pp | [−8.6, +28.6] | 0 / 1, p=1.000 | `no_significant_regression` | −43.9% | **−71.9%** |
| **judged**    | 5  | 2/5 (40%)    | 3/5 (60%)    | +20.0 pp | [−15.1, +55.1] | 0 / 1, p=1.000 | `insufficient_evidence` | −47.6% | **−73.7%** |

Output-token reduction (reasoner → chat), the primary cost driver — the reasoner
spends heavily on chain-of-thought the chat model doesn't:

| Benchmark | reasoner out-tok | chat out-tok | reduction |
|-----------|------------------|--------------|-----------|
| gsm8k     | 3,693 | 1,440 | −61% |
| humaneval | 2,594 | 1,312 | −49% |
| judged    | 524   | 267   | −49% |

¹ **Measured (placeholder pricing).** DeepSeek isn't in TokenJam's packaged
`models.toml`, so the harness priced both sides at the `$0.50 / $2.00` per-MTok
default and printed the caveat itself. Because both sides use the same rate,
this figure reflects only the **token reduction** — it understates the true
saving.

² **Real DeepSeek list rates** — `reasoner $0.55/$2.19`, `chat $0.27/$1.10` per
MTok. Recomputed from the measured token counts (input inferred from the
placeholder cost + measured output tokens). The cheaper model is cheaper *both*
per token *and* in token count, so the real saving is substantially larger:

| Benchmark | reasoner cost (real) | chat cost (real) | Δ cost |
|-----------|----------------------|------------------|--------|
| gsm8k     | $0.00865 | $0.00186 | **−78.5%** |
| humaneval | $0.00641 | $0.00180 | **−71.9%** |
| judged    | $0.00118 | $0.00031 | **−73.7%** |

## Interpretation

- **gsm8k / humaneval** (n ≥ 10): the migration is supported by evidence —
  identical-or-better pass-rate, no statistically significant regression
  (McNemar p = 1.000, the candidate broke **0** tasks the original passed), at
  ~72–79% lower cost. A reviewer can act on this with the CI + p-value in hand.
- **judged** (n = 5): the candidate scored higher (+20 pp), but the harness
  reports `insufficient_evidence` — 5 paired observations are too few for a
  significance claim. The honest answer is "run more tasks," and the product
  says exactly that.

## Caveats (read before acting)

- **Accuracy = pass-rate on these suites**, not a general "quality preserved"
  claim. Confidence is the CI + p-value, never a single "safe %".
- **Small n.** gsm8k (12) and humaneval (10) clear the n ≥ 10 threshold for a
  verdict but remain small samples; the CIs are wide. The judged suite ships
  only 5 tasks today (a v1 limitation), hence the hedge.
- **Pricing.** Dollar figures from the harness used the placeholder rate; the
  real-rate column above is the defensible cost number. Token reduction is
  measured directly and is not affected.

## Reproduce

```bash
export DEEPSEEK_API_KEY=sk-...          # read from env only; never committed
python run.py run --benchmark gsm8k     --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat --limit 12 --html
python run.py run --benchmark humaneval --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat --limit 10 --html
TJBENCH_JUDGE=deepseek TJBENCH_JUDGE_METRIC=correctness \
python run.py run --benchmark judged    --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat --limit 10 --html
```

## Artifacts

Version-stamped proof JSON + rendered HTML reports for each run are committed
under [`live/`](live/):

- `tjbench_gsm8k_tj0.5.1_1782443915.{json,html}`
- `tjbench_humaneval_tj0.5.1_1782443963.{json,html}`
- `tjbench_judged_tj0.5.1_1782444012.{json,html}`
