# Overview

## What is tokenjam-bench?

**tokenjam-bench** is a benchmarking and evaluation harness that **proves the effect of TokenJam's recommendations on cost AND accuracy**, using executable benchmarks as objective ground truth.

It answers the question TokenJam itself can't: *when TokenJam says "downsize this model," does the cheaper model still get the work right — and how much does it actually save?*

## How It's a Proof of TokenJam (Not Generic Model Comparison)

| Aspect | How We Use TokenJam |
|--------|---------------------|
| **Candidate model** | The cheaper model is whatever TokenJam's own [`downsize analyzer`](https://github.com/HoomanDigital/tokenjam/blob/main/docs/optimize/downsize.md) would route to — [`tokenjam.core.optimize.DOWNGRADE_CANDIDATES`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/analyzers/model_downgrade.py) |
| **Cost pricing** | Uses TokenJam's own pricing table via [`tokenjam.core.pricing.get_rates`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/pricing.py) — same dollars TokenJam reports |
| **Accuracy** | Pass-rate against real test suites — a *measurement*, not a judgment |
| **Version stamp** | Every result records the exact [`tokenjam` version](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/models.py) under test |

## The Proof Pipeline

```
Benchmark Tasks
       │
       ├──▶ Run on ORIGINAL model ──▶ Score (pass/fail) + Cost
       │
       ├──▶ Run on CANDIDATE model ──▶ Score (pass/fail) + Cost
       │
       └──▶ Proof: Δaccuracy (objective) + Δcost, stamped to tokenjam vX.Y.Z
```

## TokenJam Changes Every Day — That's the Design Center

TokenJam is consumed as a **published package**, never vendored. To test a new release:

```bash
make update-tokenjam     # pip install -U tokenjam ; prints the new version
tjbench version            # shows the exact tokenjam build proofs will stamp
tjbench run ...          # every artifact records tokenjam_version
```

Because each artifact in `results/` carries `tokenjam_version`, you can re-run the same benchmark across releases and diff the savings/accuracy — catching the day a TokenJam change moves the numbers.

## Key Design Principles

1. **Black-box consumer**: We import `tokenjam` as a pip dependency, never vendor it
2. **Offline-first**: All tests run without API keys using mock clients
3. **Objective ground truth**: Code execution and exact-match scoring, not LLM-as-judge
4. **Statistical honesty**: Wilson CIs, McNemar exact tests, never claim significance on small samples
5. **Safety-first**: Agent benchmarks include a safety gate for dangerous tool calls

## Related Documentation

- [Architecture](architecture.md) — System design and data flow
- [Quickstart](quickstart.md) — Get running in 5 minutes
- [TokenJam Integration](tokenjam-integration.md) — Deep dive on how we consume TokenJam
- [TokenJam's own docs](https://github.com/HoomanDigital/tokenjam/tree/main/docs) — The main project documentation

## Project Links

- **This repo**: [github.com/HoomanDigital/tokenjam-benchmark](https://github.com/HoomanDigital/tokenjam-benchmark)
- **Main TokenJam**: [github.com/HoomanDigital/tokenjam](https://github.com/HoomanDigital/tokenjam)
