# Quickstart

## Prerequisites

- Python 3.10+
- Git

## Install

```bash
cd tokenjam-bench
pip install -e .
```

For live provider support (optional):
```bash
pip install -e ".[providers,datasets]"
```

## Verify Installation

```bash
tjb version
```

This shows both the bench version and the installed TokenJam version that proofs will be stamped with.

## Run Your First Proof (Offline, No Keys)

Just run `tjb run` — no flags. It defaults to the `samples` benchmark and
`anthropic:claude-opus-4-7`, and with no provider key in the environment it goes
offline (mock) automatically: no provider SDKs, no keys, no spend.

```bash
tjb run
```

Output (abridged):
```
[MOCK — illustrative] samples (n=5, k=1) · tokenjam 0.5.2:
anthropic:claude-opus-4-7 → anthropic:claude-haiku-4-5 · Δcost -84.0% (measured)
· Δpass-rate +0.0pp [95% CI +0.0, +0.0] · McNemar p=1.000 → insufficient_evidence

┃ Metric               ┃                  Original ┃                 Candidate ┃
│ Pass rate (95% CI)   │             5/5 [57–100%] │             5/5 [57–100%] │
│ Cost (USD, measured) │                 $0.001750 │                 $0.000280 │
│ Output tokens        │                        44 │                        44 │

verdict: insufficient_evidence  (n=5 < 10 — too few tasks for a significance verdict)
```

> **Note**: offline (mock) numbers are illustrative — for plumbing verification, not actual proofs. With only n=5 sample tasks the verdict is `insufficient_evidence` (the gate is `MIN_TASKS_FOR_VERDICT = 10`); raise `--limit` on a real suite for a defensible result. See [Honesty](#honesty) below.

## View the Evidence Dashboard

```bash
tjb serve
```

With no `--dir`, `tjb serve` opens your populated `results/` if present, otherwise
the **bundled real evidence** (`docs/evidence/live/2026-06-26-multipair`), so the
dashboard is never blank on a fresh checkout.

## Check What TokenJam Recommends

```bash
tjb recommend --original anthropic:claude-opus-4-7
```

This queries [`tokenjam.core.optimize.DOWNGRADE_CANDIDATES`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/analyzers/model_downgrade.py) and shows the cheaper model TokenJam would route to.

## Run a Real Proof (Live, Requires API Key)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
tjb run --benchmark humaneval --original anthropic:claude-opus-4-7 --limit 50
```

This runs HumanEval on Opus and on TokenJam's recommended downgrade (Haiku), executes both against hidden tests, and reports the cost saved and the pass-rate delta — stamped to the installed TokenJam version.

## Run an Agent Proof (Multi-Turn, Tool-Use)

```bash
tjb agent --benchmark sample-agent --original anthropic:claude-opus-4-7 --mock
```

This exercises the [agent pipeline](pipelines.md#agent-proof-pipeline) with tool-calling, safety validation, and multi-turn scoring.

## Update TokenJam and Re-Run

```bash
make update-tokenjam     # pip install -U tokenjam
tjb version              # confirm new version
tjb run                  # re-run the offline proof on the new version
```

Compare `results/` artifacts across versions to see how TokenJam changes affect recommendations.

## Available Benchmarks

| name | ground truth | needs | docs |
|------|-------------|-------|------|
| `samples` | tiny built-in code + math tasks | nothing (offline) | [Benchmarks](benchmarks.md#samples) |
| `humaneval` | unit-test pass/fail | `[datasets]` | [Benchmarks](benchmarks.md#humaneval) |
| `gsm8k` | numeric exact-match | `[datasets]` | [Benchmarks](benchmarks.md#gsm8k) |
| `sample-agent` | tool-use + safety validation | nothing (offline) | [Benchmarks](benchmarks.md#sample-agent) |

## Honesty

- **Offline (mock) runs** are flagged as illustrative in reports
- **Small samples** (fewer than 10 tasks) cannot reach a significance verdict — reports will say `insufficient_evidence`
- **Cost fallback**: If TokenJam's pricing table lacks a model, we use `$0.50/$2.00` per MTok defaults and flag it
- **Accuracy is suite-specific**: Pass-rate on HumanEval ≠ general coding ability

## Next Steps

- [CLI Reference](cli-reference.md) — Full command documentation
- [Architecture](architecture.md) — System design
- [Pipelines](pipelines.md) — How proofs work under the hood
- [Development Guide](development.md) — Contributing and extending

## Related TokenJam Docs

- [TokenJam Installation](https://github.com/HoomanDigital/tokenjam/blob/main/docs/installation.md)
- [TokenJam Python SDK](https://github.com/HoomanDigital/tokenjam/blob/main/docs/python-sdk.md)
- [TokenJam Quickstart](https://github.com/HoomanDigital/tokenjam/blob/main/README.md)
