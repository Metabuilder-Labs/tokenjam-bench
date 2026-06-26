# Statistics

## Overview

The `stats.py` module provides pure-math statistical primitives for evaluating proof results. No scipy or numpy — all implemented with standard library math.

## Methods

### Wilson Interval

```python
def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.
    
    Returns (lower, upper) confidence bounds for the true pass rate
    given k successes out of n trials.
    """
```

Used to compute confidence intervals for original and candidate pass rates.

**Properties verified by tests:**
- CI always brackets the point estimate (k/n)
- Perfect score (k=n) still has CI < 1 (not a point)
- Zero trials (n=0) returns [0, 1] (fully uncertain)

### McNemar Exact Test

```python
def mcnemar_exact(b: int, c: int) -> tuple[float, bool]:
    """Exact two-sided McNemar test on discordant pairs.
    
    b = original passes, candidate fails
    c = original fails, candidate passes
    
    Returns (p_value, is_significant_at_0.05).
    """
```

Tests whether the difference between original and candidate pass rates is statistically significant.

**Properties verified by tests:**
- Lopsided discordance (e.g., b=5, c=0) → significant
- Balanced discordance (e.g., b=2, c=2) → not significant
- No discordance (b=0, c=0) → p=1.0
- Small n cannot reach significance (e.g., n=5 total wipeout cannot reach p<0.05)

### Paired Delta CI

```python
def paired_delta_ci(b: int, c: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Confidence interval on the paired pass-rate delta.
    
    delta = (candidate_pass_rate - original_pass_rate)
    """
```

Computes the confidence interval for the difference in pass rates between original and candidate.

**Properties verified by tests:**
- CI always spans the point estimate
- Symmetric around the observed delta for large n

### Pass@k Estimator

```python
def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al. 2021).
    
    n = total tasks
    c = number of tasks with at least one pass in k samples
    k = samples per task
    """
```

Estimates the probability that at least one of k independent samples passes, given the observed data.

## How Statistics Are Used in Proofs

```
ProofResult
├── original_pass_rate: k_orig / n
│   └── wilson_interval(k_orig, n) → [lower, upper]
├── candidate_pass_rate: k_cand / n
│   └── wilson_interval(k_cand, n) → [lower, upper]
├── mcnemar_exact(b, c)
│   └── b = original passes, candidate fails
│   └── c = original fails, candidate passes
│   └── p_value, significant?
├── paired_delta_ci(b, c, n)
│   └── delta = candidate_rate - original_rate
│   └── [delta_lower, delta_upper]
└── verdict
    └── Based on: n, significant?, delta sign
```

## Verdict Logic

Computed by `_verdict(n_tasks, significant, delta_pp)` in `pipeline.py`, where
`delta_pp = candidate_pass_rate − original_pass_rate` and `significant` is the
McNemar result at alpha. The gate is `MIN_TASKS_FOR_VERDICT = 10`.

| Condition | Verdict | Meaning |
|-----------|---------|---------|
| n < 10 | `insufficient_evidence` | Too few paired observations for McNemar to mean anything |
| n ≥ 10, significant **and** delta < 0 | `significant_regression` | Candidate is significantly worse on this suite |
| n ≥ 10, otherwise | `no_significant_regression` | No statistically significant regression detected |

There are exactly three verdicts — `no_significant_regression`,
`significant_regression`, `insufficient_evidence` — and never `SAFE` (which would
assert equivalence the test cannot prove). A significant *improvement* still maps
to `no_significant_regression`: the bench reports the absence of a regression, not
a positive quality claim.

## Honesty Discipline

- **Small samples are flagged**: n < 10 → `insufficient_evidence` regardless of observed rates
- **No p-hacking**: Fixed alpha = 0.05, no multiple comparison correction needed (single test)
- **CIs are reported**: Always show Wilson intervals, not just point estimates
- **No equivalence claim**: the verdict is the absence of a detected regression, never a positive "preserved" / "SAFE" assertion

## Related Documentation

- [Pipelines](pipelines.md) — How stats are used in assemble_proof
- [Report](api-reference.md#reportpy) — ProofResult, ProofStats
- [TokenJam's Evaluation Subsystem](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/eval/) — TokenJam's own quality evaluation
