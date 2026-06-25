# Continuous Benchmark Pipeline (P2)

Benchmarks shouldn't be run by hand. This pipeline runs them automatically on
every TokenJam release and surfaces regressions continuously.

## Two workflows

**`.github/workflows/ci.yml`** — the always-on gate. On every push / PR to
`main`: `ruff` + `pytest` (all offline) + an **offline proof smoke**
(`ci_benchmark.py` proves the proof pipeline still produces a valid,
version-stamped result). No keys, no spend.

**`.github/workflows/benchmark.yml`** — continuous benchmarking against the
**latest** TokenJam:

- triggers: **nightly cron** (06:00 UTC) + **manual dispatch**
- `pip install -U tokenjam` → every run tests the newest release, version-stamped
- runs `ci_benchmark.py`:
  - **offline (always)**: mock proofs (`samples`, `coding-assistant`)
  - **live (key-gated)**: a small HumanEval (`--limit 10`) + `judged` with the
    DeepSeek judge — **only if the `DEEPSEEK_API_KEY` secret is set**
- uploads `results/` (version-stamped JSON + HTML) as a workflow artifact
- writes a Markdown results table to the **Actions run summary**

```
push/PR ─▶ ci.yml ─▶ ruff + pytest + offline proof          (free gate)
nightly ─▶ benchmark.yml ─▶ pip install -U tokenjam
                          ─▶ ci_benchmark.py (offline + key-gated live)
                          ─▶ artifacts (results/) + run summary table
```

## Enabling live benchmarks (secret setup)

Live runs are **opt-in via a repo secret** — never a hardcoded key:

1. GitHub → repo **Settings → Secrets and variables → Actions → New secret**
2. Name `DEEPSEEK_API_KEY`, value = your key
3. The nightly run (or a manual dispatch) will then run the live proofs too.

Without the secret, the pipeline still runs the **offline** proofs every night
(a free regression gate on the framework + latest TokenJam).

Cost: the live set is intentionally tiny (HumanEval n=10 + judged n=5 on
DeepSeek) — a few cents per run. Raise `live_limit` in `ci_benchmark.py` for a
tighter CI.

## Run it locally

```bash
make ci-bench                 # offline only (no key)
DEEPSEEK_API_KEY=... make ci-bench   # adds the live proofs
```

Artifacts land in `results/` and show up in the dashboard (`run.py serve`) and in
`tjbench matrix` — so the nightly run builds your cross-version history over time.

## Honesty

The pipeline never claims "safe". Each row reports the evidence-based verdict
(`no_significant_regression` / `significant_regression` / `insufficient_evidence`)
from the same Wilson + McNemar machinery as every other proof.
