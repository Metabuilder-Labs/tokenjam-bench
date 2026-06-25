# Proof Runbook — producing the first real evidence report

This is the exact procedure to produce a live, evidence-backed validation report
for TokenJam using real model evaluations, with **DeepSeek** as both a
model-under-test and the DeepEval judge.

> **Secrets.** API keys are read from the **environment only** — never hard-coded,
> committed, printed, or persisted. If you ever paste a key into a chat or
> terminal history, rotate it afterward. A CI test
> (`tests/test_deepseek.py::test_no_api_key_is_committed_in_the_repo`) fails the
> build if a key string lands in the repo.

## 0. Install

```bash
cd tokenjam-benchmark
pip install -e ".[providers,judge,datasets]"
# providers → openai SDK (also used for DeepSeek)
# judge     → deepeval
# datasets  → HumanEval / GSM8K / SWE-Bench loaders
```

## 1. Configure DeepSeek (env var only)

```bash
export DEEPSEEK_API_KEY=sk-...            # never written to disk by the tooling
```

DeepSeek is OpenAI-compatible. The bench already knows it as a provider
(`models/openai_compatible.py`): `base_url=https://api.deepseek.com`,
key env `DEEPSEEK_API_KEY`, default model `deepseek-chat`. Specs look like
`deepseek:deepseek-chat` and `deepseek:deepseek-reasoner`.

The "downsize" proof here is **`deepseek-reasoner` (premium) → `deepseek-chat`
(cheaper)**. TokenJam's downgrade map only covers anthropic/openai/google, so we
pass the candidate explicitly with `--candidate`.

## 2. (Optional but recommended) real DeepSeek pricing

TokenJam 0.5.1 ships no DeepSeek rates, so cost falls back to the $0.50/$2.00
placeholder (the report flags this as `priced_with_defaults`). For real cost
numbers, add a TokenJam pricing override (read from `~/.config/tj/pricing.toml`):

```toml
# ~/.config/tj/pricing.toml  — verify against current DeepSeek pricing
[models.deepseek-chat]
input_per_mtok  = 0.27
output_per_mtok = 1.10

[models.deepseek-reasoner]
input_per_mtok  = 0.55
output_per_mtok = 2.19
```

Restart is not needed for the bench (it loads pricing per run via the installed
`tokenjam`).

## 3. Verify the DeepEval judge works with DeepSeek

```bash
TJBENCH_JUDGE=deepseek python -c "
import sys; sys.path.insert(0, '.')
from judge import judge_from_env, JudgeCase
j = judge_from_env()
r = j.evaluate(JudgeCase(input='What is the capital of France?',
                         actual_output='Paris is the capital of France.',
                         expected_output='The capital of France is Paris.'))
print('judge:', j.name, j.metric, '-> score', r.score, 'passed', r.passed)
"
```

A score in `[0,1]` with no error confirms DeepEval is driving DeepSeek as the
judge model.

## 4. Run the real benchmarks

All write a version-stamped JSON + an HTML report into `results/`.

### a) Judged (QA/RAG/summarization, scored by the DeepSeek judge)

```bash
TJBENCH_JUDGE=deepseek TJBENCH_JUDGE_METRIC=correctness \
  tjbench run --benchmark judged \
    --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat \
    --html
```

### b) HumanEval (executable pass/fail; raise the limit for significance)

```bash
tjbench run --benchmark humaneval \
  --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat \
  --limit 30 --html
```

> Use **n ≥ ~30** so McNemar can actually reach significance — with small n the
> verdict is honestly `insufficient_evidence`.

### c) SWE-Bench Lite (multi-turn agent; heavier — see caveats)

```bash
tjbench agent --benchmark swe-bench-lite \
  --original deepseek:deepseek-reasoner --candidate deepseek:deepseek-chat \
  --limit 5 --html
```

SWE-Bench Lite is an **agent** benchmark (tool use via the OpenAI-compatible
tool-calling client, now wired for DeepSeek). Live scoring needs the SWE-bench
dataset (`[datasets]`) and is materially heavier than HumanEval (repo context,
multi-turn loops). If you only want the framework demonstrated end-to-end
without that weight, add `--mock` for deterministic scoring.

## 5. The report

Each `--html` run writes `results/tjbench_<benchmark>_tj<version>_<ts>.html`
containing:

- **Accuracy** — candidate pass-rate vs original, with **Wilson 95% CIs**
- **Cost comparison** — measured token usage priced via TokenJam (real rates if
  step 2 applied, else flagged placeholder)
- **McNemar** paired significance (p-value + b/c discordant counts)
- **DeepEval metrics** — for the `judged` benchmark, each task's per-row detail
  shows the judge metric + score (e.g. `deepeval:correctness@deepseek score=0.87`)
- **Final verdict** — `no_significant_regression` / `regression_suspected` /
  `insufficient_evidence` (never "SAFE")

Re-render any saved artifact: `tjbench report results/<file>.json --open`.

## 6. Cross-version regression (the daily-change guard)

```bash
make update-tokenjam        # pip install -U tokenjam (new release)
# re-run the same proof(s) above — artifacts are stamped with the new version
tjbench matrix              # flags accuracy/cost/recommendation regressions; exits 1 if any
```

## Caveats (be honest in the report)

- **Accuracy = benchmark pass-rate / judge score on the chosen suite** — not a
  general "quality preserved" claim.
- **Significance needs n.** Small runs report `insufficient_evidence` by design.
- **DeepSeek cost** uses placeholder rates unless step 2 is applied.
- **Benchmark contamination** — HumanEval/GSM8K are in pretraining; treat
  pass-rate as an upper bound on real-world preservation.
