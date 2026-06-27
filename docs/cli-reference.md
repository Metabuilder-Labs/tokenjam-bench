# CLI Reference

The CLI is `tjb` (defined in `pyproject.toml` as `tjb = "tjbench.cli:cli"`).

Start with two commands: `tjb run` (a zero-flag offline proof) and `tjb serve`
(the dashboard over the bundled real evidence). Everything else — `agent`,
`replay`, `matrix`, `history` — is advanced and off the common path.

## Global Options

| Option | Description |
|--------|-------------|
| `--json` | Output raw JSON instead of Rich tables |
| `--out DIR` | Write result artifact to directory (default: `results/`) |

---

## `tjb version`

Shows bench version + resolved TokenJam version under test.

```bash
tjb version
```

Output:
```
tokenjam-bench 0.1.0
tokenjam 0.4.2  (/Users/.../site-packages/tokenjam)
```

The TokenJam version and location are stamped on every proof artifact.

---

## `tjb recommend`

Shows what TokenJam would downsize the model to.

```bash
tjb recommend --original SPEC
```

| Option | Required | Description |
|--------|----------|-------------|
| `--original` | Yes | Provider:model spec, e.g. `anthropic:claude-opus-4-7` |

Example:
```bash
tjb recommend --original anthropic:claude-opus-4-7
```

This queries [`tokenjam.core.optimize.DOWNGRADE_CANDIDATES`](https://github.com/HoomanDigital/tokenjam/blob/main/tokenjam/core/optimize/analyzers/model_downgrade.py) and prints the recommended cheaper model.

---

## `tjb run`

Single-shot proof: run original vs candidate, score, price, report. Runs with
**zero flags** — `tjb run` defaults to the `samples` benchmark and
`anthropic:claude-opus-4-7`, and goes offline (mock) automatically when no
provider API key is set.

The former `workflow` command is merged in here: pass a workflow suite to
`--benchmark` (`customer-support`, `enterprise-rag`, `email-assistant`,
`research-assistant`, and the agentic `n8n` / `coding-workflow`, which route
through the agent pipeline automatically).

```bash
tjb run [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--benchmark` | `samples` | Benchmark or workflow suite (`samples`, `humaneval`, `gsm8k`, `judged`, `customer-support`, …) |
| `--original` | `anthropic:claude-opus-4-7` | Original model spec |
| `--candidate` | (TokenJam) | Override candidate model (bypasses TokenJam recommendation) |
| `--limit` | all | Limit number of tasks |
| `--mock` | auto | Force offline run. Auto-enabled when the provider has no API key |
| `--out` | `results/` | Output directory for JSON artifacts |
| `--json` | false | Print JSON instead of Rich table |
| `--html` | false | Also write a self-contained HTML report |

**Advanced flags** (hidden from `--help`, kept for power users): `--samples N`
(pass@k / variance), `--temperature`, `--max-tokens`, `--mock-candidate-accuracy`.

### Examples

**Zero-flag offline proof:**
```bash
tjb run
```

**Workflow suite (judge-scored), offline:**
```bash
tjb run --benchmark customer-support --limit 16
```

**Live HumanEval with 50 tasks** (with `ANTHROPIC_API_KEY` set):
```bash
tjb run --benchmark humaneval --original anthropic:claude-opus-4-7 --limit 50
```

**Force a specific candidate:**
```bash
tjb run --benchmark gsm8k --original anthropic:claude-opus-4-7 --candidate anthropic:claude-haiku-4-5
```

**Multi-sample for pass@k (advanced flag):**
```bash
tjb run --mock --samples 5
```

---

## `tjb agent`

Multi-turn agent proof: tool use + safety validation.

```bash
tjb agent [OPTIONS]
```

Like `tjb run`, `agent` defaults `--original` to `anthropic:claude-opus-4-7` and
goes offline (mock) automatically when no provider key is set.

| Option | Default | Description |
|--------|---------|-------------|
| `--benchmark` | `sample-agent` | Agent benchmark: `sample-agent` (`swe-bench-lite` is an experimental scaffold — gated, scoring disabled) |
| `--original` | `anthropic:claude-opus-4-7` | Original model spec |
| `--candidate` | (TokenJam) | Override candidate model |
| `--limit` | all | Limit number of tasks |
| `--mock` | auto | Force offline run. Auto-enabled when the provider has no API key |
| `--out` | `results/` | Output directory |
| `--json` | false | Print JSON instead of Rich table |
| `--html` | false | Also write a self-contained HTML report |

**Advanced flags** (hidden from `--help`): `--samples`, `--temperature`,
`--max-turns`, `--max-tokens`, `--candidate-behavior` (`ok` / `wrong` / `unsafe`).

### Candidate Behavior Modes (Mock Only)

| Mode | Effect |
|------|--------|
| `ok` | Correct answer, correct tools |
| `wrong` | Wrong answer (tests accuracy regression) |
| `unsafe` | Calls dangerous tool (tests safety gate) |

### Examples

**Offline agent smoke test:**
```bash
tjb agent --benchmark sample-agent --original anthropic:claude-opus-4-7 --mock
```

**Test safety gate with mock:**
```bash
tjb agent --benchmark sample-agent --original anthropic:claude-opus-4-7 --mock --candidate-behavior unsafe
```

> ⚠️ `swe-bench-lite` is an **experimental scaffold** — fix-verification is not implemented and scoring is disabled, so it is gated out of `tjb agent` and does not produce a proof. See [SWE-Bench Lite](swe-bench-lite.md).

---

## `tjb serve`

Start the live proof dashboard (offline, auto-refreshing).

```bash
tjb serve [--dir DIR] [--open]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--dir` | auto | Artifacts dir. Defaults to a populated `results/`, else the bundled real evidence (`docs/evidence/live/2026-06-26-multipair`) so the dashboard is never blank |
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `7392` | Bind port |
| `--open` | false | Open the dashboard in a browser |

---

## Advanced commands

Present but off the common path: `replay` (replay exported TokenJam telemetry
against the candidate), `matrix` (diff proofs across TokenJam versions; exits
non-zero on regression), `history` (query the local run database), and
`scenarios` (list the Real Scenario Library suites).

---

## Key Flags Explained

### `--mock`

Runs the entire pipeline deterministically with no provider SDKs, no API keys, and no spend. Mock clients read `# task_key:` markers embedded in prompts and return predetermined responses.

- **Use for**: CI, testing, plumbing verification
- **Not for**: Actual proofs (numbers are illustrative)
- **Flagged in reports**: Every mock run is marked `mock: true`

### `--candidate-behavior` (Agent Only)

Simulates different candidate behaviors in mock mode:
- `ok`: Correct answer and correct tool calls
- `wrong`: Wrong final answer (exercises accuracy regression detection)
- `unsafe`: Calls a forbidden/dangerous tool (exercises safety gate)

### `--samples`

Runs each task N times. Used for:
- Pass@k estimation (how many of k attempts pass)
- Variance reduction on small benchmarks
- Statistical power

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (proof completed, report generated) |
| 1 | General error (bad args, missing keys, scoring failure) |
| 2 | No candidate found (TokenJam has no recommendation for this model) |

---

## Related Documentation

- [Pipelines](pipelines.md) — How `run` and `agent` work under the hood
- [Benchmarks](benchmarks.md) — Available benchmarks
- [Agents](agents.md) — Multi-turn agent execution
- [Statistics](statistics.md) — How proof stats are computed
- [TokenJam CLI Reference](https://github.com/HoomanDigital/tokenjam/blob/main/docs/cli-reference.md) — The main `tj` CLI
