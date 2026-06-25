# FAQ

## General

### What is tokenjam-bench?

A benchmarking and evaluation harness that **proves the effect of TokenJam's recommendations on cost AND accuracy**, using executable benchmarks as objective ground truth.

### How is this different from other LLM benchmarks?

Most benchmarks measure text quality. tokenjam-bench measures:
- **Cost** (using TokenJam's own pricing)
- **Accuracy** (pass-rate on executable tests)
- **Safety** (forbidden tool detection in agents)
- **Behavior** (tool usage, ordering, multi-turn reasoning)

### Do I need API keys?

No! All tests run offline with `--mock`. For live proofs, you need provider API keys.

## TokenJam Integration

### How does it use TokenJam?

Three integration points:
1. **Candidate recommendation** — `tokenjam.core.optimize.DOWNGRADE_CANDIDATES`
2. **Cost pricing** — `tokenjam.core.pricing.get_rates`
3. **Version stamp** — `importlib.metadata.version("tokenjam")`

### What if TokenJam doesn't have a candidate for my model?

Use `--candidate` to specify one manually:
```bash
tjbench run --original anthropic:claude-opus-4-7 --candidate anthropic:claude-haiku-4-5
```

### How do I test a new TokenJam release?
```bash
make update-tokenjam  # pip install -U tokenjam
tjbench version       # confirm new version
tjbench run ...       # re-run benchmarks
```

## Benchmarks

### What's the difference between single-shot and agent benchmarks?

**Single-shot**: One prompt → one completion → score
- `samples`, `humaneval`, `gsm8k`

**Agent**: Multi-turn with tool-calling → trace → score
- `sample-agent`, `swe-bench-lite`

### Can I add my own benchmark?

Yes! See [Development Guide](development.md#adding-a-new-benchmark).

### What is SWE-Bench Lite?

300 real GitHub issues from popular Python repositories. The agent must fix bugs by editing code and running tests.

## Mock Mode

### What does `--mock` do?

Runs deterministically with no API calls. Mock clients return predetermined responses based on task markers.

### Are mock numbers real?

No — they're illustrative. Mock runs are flagged in reports. Use `--mock` for CI and plumbing verification.

### How does mock agent behavior work?

Three modes:
- `ok`: Correct tools, correct answer
- `wrong`: Wrong answer (tests accuracy regression)
- `unsafe`: Calls dangerous tool (tests safety gate)

## Statistics

### What statistical tests are used?

- **Wilson interval** — Confidence interval for pass rate
- **McNemar exact test** — Significance of pass-rate difference
- **Paired delta CI** — Confidence interval for the difference

### Why can't small samples reach significance?

With n=5 tasks, even a total wipeout (0% vs 100%) cannot reach p<0.05. This is mathematically correct — we don't claim confidence without evidence.

### What's the verdict logic?

| Condition | Verdict |
|-----------|---------|
| n < 30, not significant | `insufficient_evidence` |
| Significant, delta ≈ 0 | `preserved` |
| Significant, candidate worse | `regression_detected` |
| Not significant, delta small | `likely_preserved` |

## Safety

### What is the safety gate?

A task fails if a forbidden/dangerous tool is called, even if the final answer is correct. This catches behavior that output-only evaluation misses.

### Can model-generated code harm my system?

Code runs in a subprocess with timeout. It's isolated but not sandboxed. Run only trusted benchmarks on machines you control.

### Is path traversal blocked?

Yes. SWE-Bench tools prevent escaping the workspace directory.

## Troubleshooting

### "No candidate found" error

TokenJam has no downgrade recommendation for your model. Use `--candidate` to specify one.

### "ModuleNotFoundError: No module named 'tokenjam'"

Install tokenjam: `pip install -e ".[dev]"`

### Tests fail with dataset errors

Install datasets: `pip install -e ".[datasets]"`

## Related Documentation

- [Quickstart](quickstart.md) — Get running in 5 minutes
- [CLI Reference](cli-reference.md) — All commands
- [Benchmarks](benchmarks.md) — Available benchmarks
- [Security](security.md) — Security considerations
