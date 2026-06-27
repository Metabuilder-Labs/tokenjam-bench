# Replay validation (P0)

Benchmarks (HumanEval, GSM8K, …) measure a model's *capability* against
objective ground truth. **Replay measures something narrower and more honest:
agreement with your own history.** It re-runs your actual historical prompts on
the cheaper candidate and checks whether the answers agree with what the original
model produced on those same prompts.

> **What replay does NOT measure.** The reference is the *original model's own
> historical output*, which has no gold answer attached — so replay measures
> **agreement-with-your-history, not correctness and not safety**. A candidate
> that disagrees with the original may be right or wrong; replay only tells you it
> diverged. This is an offline measurement, **never a runtime safety
> certification** and never "SAFE".

```
TokenJam telemetry (exported, READ-ONLY)
  → reconstruct each historical LLM call (prompt + original output)
  → run the CANDIDATE model on the same prompt
  → judge candidate vs the ORIGINAL output (DeepEval / MockJudge)
  → Wilson CI · McNemar · pass@k · cost      (same rigor as every benchmark)
  → replay report (JSON + HTML) → dashboard
```

Replay **never modifies TokenJam**. It only consumes exported telemetry, exactly
like any external user.

## What it measures

Real sessions have no gold answer, so the **original model's historical output is
the agreement reference**. The question replay answers is:

> *On your real prompts, does the cheaper model agree with what the original model
> already produced?*

That is **agreement-with-your-history** — not correctness (the reference is not a
verified answer) and not safety (no production behaviour is observed). The verdict
is evidence-based — **"no statistically significant divergence from the original's
historical output"** — never "SAFE" and never a certification.

## Telemetry input

Two read-only sources (dispatched by extension):

**Portable export (recommended)** — `.jsonl` (one LLM call per line) or a JSON
array. Liberal field names:

```json
{"session_id":"s1","prompt":"...","output":"...","provider":"anthropic","model":"claude-opus-4-7","input_tokens":1200,"output_tokens":300}
```
(`output`/`completion`/`response` and `prompt`/`input` are all accepted.)

**TokenJam DuckDB** — point `--telemetry` at a `*.duckdb` store; replay opens it
**read-only** and reads spans that captured prompt + completion content (needs
TokenJam `[capture] prompts` / `completions` on). Uses TokenJam's own public
semconv constants.

## Run it

```bash
# candidate defaults to TokenJam's own downgrade for the original model
python3 run.py replay --telemetry sessions.jsonl --html

# explicit candidate, DeepSeek judge, real run
export DEEPSEEK_API_KEY=...
TJBENCH_JUDGE=deepseek python3 run.py replay \
  --telemetry ~/.config/tj/tj.duckdb \
  --candidate deepseek:deepseek-chat --judge deepseek --limit 50 --html

# offline smoke (no keys/spend)
python3 run.py replay --telemetry sessions.jsonl --mock --mock-candidate-accuracy 0.9
```

## Modes

- **default** — the original output is the reference (passes trivially); the
  candidate's *agreement rate* (with that historical output) gets a Wilson CI, and
  McNemar tests whether its divergences are significant.
- **`--control`** — also re-runs the original model and judges it against its own
  history, so McNemar compares the candidate against the original's run-to-run /
  judge noise (the most rigorous form). Doubles model calls.

## Output

A `ProofResult` artifact (`benchmark=replay`) — identical shape to every other
proof, so it shows up in the **dashboard** (`run.py serve`), renders an **HTML
report**, and participates in **`tjb matrix`** cross-version tracking with no
extra work. Cost is the historical original spend vs the candidate's measured
spend, priced by TokenJam.

## Limitations (v1)

- **Per-call replay**: each captured LLM call is replayed independently with its
  reconstructed prompt. Full multi-turn conversation reconstruction is a later
  milestone.
- Agreement is judged against the original output, which is itself a model output
  (not a verified gold answer) — `--control` quantifies that reference's own noise.
