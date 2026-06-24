# Cost & Pricing

## Overview

Cost computation in tokenjam-bench uses **TokenJam's own pricing table** — the same rates TokenJam reports. This ensures the dollars in our proofs match the dollars in TokenJam's analysis.

## Integration Point

[`cost.py`](../cost.py) imports [`tokenjam.core.pricing.get_rates`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/pricing.py):

```python
from tokenjam.core.pricing import get_rates
```

## `price_completion()`

```python
def price_completion(
    provider: str,
    model: str,
    completion: Completion,
) -> float:
    """Compute USD cost for a completion using TokenJam's pricing table.
    
    Falls back to $0.50 input / $2.00 output per MTok defaults
    and flags when that happens.
    """
```

### Pricing Lookup Order

1. Exact match in TokenJam's [`models.toml`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/pricing/models.toml)
2. Strip date suffix (e.g., `claude-sonnet-4-20250514` → `claude-sonnet-4`)
3. Model-keyed override from user config
4. Provider table fallback
5. **Default**: $0.50 input / $2.00 output per MTok (flagged in report)

### Cost Formula

```
cost = (input_tokens / 1_000_000) * input_rate
     + (output_tokens / 1_000_000) * output_rate
     + (cache_read_tokens / 1_000_000) * cache_read_rate
     + (cache_write_tokens / 1_000_000) * cache_write_rate
```

## Token Inflation Detection

[`report.py`](../report.py) flags "token inflation" when the candidate uses significantly more output tokens than the original:

```python
@property
def token_inflation(self) -> bool:
    """True if candidate output tokens > 1.5x original output tokens."""
```

This catches cases where a cheaper model compensates for lower quality by being more verbose.

## Cost Comparison in Reports

Each `ProofResult` includes:

| Field | Description |
|-------|-------------|
| `original_cost` | Total USD for original model |
| `candidate_cost` | Total USD for candidate model |
| `cost_delta` | candidate_cost - original_cost (negative = savings) |
| `cost_delta_percent` | (cost_delta / original_cost) * 100 |
| `token_inflation` | True if candidate is significantly more verbose |

## Plan-Tier Awareness

TokenJam's [`framing.py`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/framing.py) handles plan-tier-aware cost display:

- **API billing**: Show raw dollars
- **Subscription**: Show token share (not dollars)
- **Local inference**: Tokens only (no marginal cost)
- **Unknown**: Suppressed with qualifier

tokenjam-bench always reports raw dollars since we're measuring the *potential* cost of API usage, not the user's actual billing.

## Mock Mode Costs

In `--mock` mode, costs are computed from mock token counts (which are deterministic/illustrative). The cost numbers are flagged as illustrative in reports.

## Related Documentation

- [TokenJam Pricing](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/pricing/models.toml) — Static pricing table
- [TokenJam Pricing Engine](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/pricing.py) — Rate lookup logic
- [TokenJam Cost Calculation](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/cost.py) — Cost engine
- [TokenJam Framing](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/framing.py) — Plan-tier display logic
- [Pipelines](pipelines.md) — How cost is computed in proofs
- [Report](api-reference.md#reportpy) — Cost fields in ProofResult
