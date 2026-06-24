# TokenJam Integration

## Overview

tokenjam-bench is a **black-box consumer** of the published `tokenjam` package. We import it as a pip dependency, never vendor it. This design means: **when TokenJam changes its downgrade map or pricing, the bench automatically tests the new recommendation and reports the new cost — with full version provenance.**

## Three Integration Points

### 1. Candidate Recommendation

**Module**: [`recommend.py`](../recommend.py)

**TokenJam API**: [`tokenjam.core.optimize.DOWNGRADE_CANDIDATES`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/analyzers/model_downgrade.py)

```python
from tokenjam.core.optimize import DOWNGRADE_CANDIDATES

def resolve_candidate(original_spec: str) -> str:
    """Look up the cheaper model TokenJam recommends."""
    provider, model = parse_spec(original_spec)
    # Tolerates dated model suffixes
    return DOWNGRADE_CANDIDATES.get(f"{provider}:{model}") or \
           DOWNGRADE_CANDIDATES.get(f"{provider}:{strip_suffix(model)}")
```

**How it works**: TokenJam's downsize analyzer flags sessions with "small input, small output, few tools" as candidates for cheaper models. The `DOWNGRADE_CANDIDATES` dict maps expensive models to their recommended cheaper alternatives in the same family.

**Examples**:
- `anthropic:claude-opus-4-7` → `anthropic:claude-haiku-4-5`
- `openai:gpt-4o` → `openai:gpt-4o-mini`

### 2. Cost Pricing

**Module**: [`cost.py`](../cost.py)

**TokenJam API**: [`tokenjam.core.pricing.get_rates`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/pricing.py)

```python
from tokenjam.core.pricing import get_rates

def price_completion(provider: str, model: str, completion: Completion) -> float:
    rates = get_rates(provider, model)
    if rates is None:
        # Fall back to defaults, flag in report
        rates = DEFAULT_RATES
    # Compute cost from rates and token counts
```

**How it works**: TokenJam maintains a pricing table (`models.toml`) with USD-per-million-token rates for known models. We use the same lookup logic so our cost numbers match TokenJam's exactly.

**Fallback**: If TokenJam doesn't have a rate for a model, we use `$0.50` input / `$2.00` output per MTok and flag it in the report.

### 3. Version Stamp

**Module**: [`version.py`](../version.py)

**TokenJam API**: [`importlib.metadata.version("tokenjam")`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/models.py)

```python
import importlib.metadata

def resolve_tokenjam_build() -> tuple[str, str]:
    """Returns (version_string, location_string)."""
    version = importlib.metadata.version("tokenjam")
    location = str(Path(tokenjam.__file__).parent)
    return version, location
```

**How it works**: Every proof artifact records the exact TokenJam version and installation location. This enables:
- Reproducibility: "This proof was run against TokenJam 0.4.2"
- Cross-version comparison: Re-run the same benchmark after `make update-tokenjam`
- Debugging: Know exactly which build produced a given result

## Version Stamping in Artifacts

Every `ProofResult` includes:

```json
{
  "tokenjam_version": "0.4.2",
  "tokenjam_location": "/Users/.../site-packages/tokenjam",
  "bench_version": "0.1.0",
  "timestamp": "2025-06-24T21:46:06Z"
}
```

## Update Workflow

```bash
# 1. Check current version
tjbench version
# tokenjam-bench 0.1.0
# tokenjam 0.4.2

# 2. Update TokenJam
make update-tokenjam
# pip install -U tokenjam
# → tokenjam 0.4.3 installed

# 3. Verify new version
tjbench version
# tokenjam-bench 0.1.0
# tokenjam 0.4.3

# 4. Re-run benchmark
tjbench run --benchmark samples --original anthropic:claude-opus-4-7 --mock

# 5. Compare results/ artifacts
# proof_samples_claude-opus-4-7_0.4.2_20250624T214000.json
# proof_samples_claude-opus-4-7_0.4.3_20250624T215000.json
```

## TokenJam's Downsize Analyzer

The downsize analyzer ([`model_downgrade.py`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/analyzers/model_downgrade.py)) flags sessions matching this heuristic:

- Input tokens < 5,000
- Output tokens < 500
- Tool calls ≤ 5

These are considered "lightweight" sessions that might work fine on a cheaper model.

**Important caveat**: TokenJam never claims quality equivalence. The downgrade map is a *candidate* for review, not a guarantee. tokenjam-bench measures whether the candidate actually works.

## TokenJam's Pricing Table

TokenJam's [`models.toml`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/pricing/models.toml) includes rates for:

- Anthropic (Claude family)
- OpenAI (GPT family)
- Google (Gemini family)
- Third-party providers (Groq, xAI, HUD)
- Deprecated models (with suffix stripping for dated variants)

Users can override rates via:
- `~/.config/tj/pricing.toml` (standalone file)
- `[pricing]` section in `~/.config/tj/config.toml`

See [TokenJam Configuration](https://github.com/HoomanDigital/tokenjam/blob/main/docs/configuration.md) for details.

## Related Documentation

- [TokenJam's Downsize Analyzer](https://github.com/HoomanDigital/tokenjam/blob/main/docs/optimize/downsize.md)
- [TokenJam's Pricing](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/pricing/models.toml)
- [TokenJam's Optimize Runner](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/runner.py)
- [TokenJam's Evaluation Subsystem](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/eval/)
- [Pipelines](pipelines.md) — How integration points are used in proofs
- [Cost & Pricing](cost-pricing.md) — Cost computation details
