# Pipelines

## Overview

tokenjam-bench has two proof pipelines:

1. **[Single-Shot Pipeline](#single-shot-pipeline)** — For completion-style benchmarks (code, math)
2. **[Agent Pipeline](#agent-proof-pipeline)** — For multi-turn agent benchmarks (tool-use, safety)

Both pipelines share the same [statistical machinery](statistics.md) and [cost pricing](cost-pricing.md). The only difference is how the model is invoked and how the response is scored.

## Single-Shot Pipeline

### Entry Point: `run_proof()`

Located in [`pipeline.py`](../pipeline.py).

```python
def run_proof(
    benchmark: Benchmark,
    original_spec: str,
    candidate_spec: str | None = None,
    *,
    mock: bool = False,
    mock_candidate_accuracy: float = 1.0,
    temperature: float = 0.0,
    max_tokens: int | None = None,
    samples: int = 1,
    limit: int | None = None,
) -> ProofResult:
```

### Flow

```
1. Resolve candidate (if not provided)
   └── Call [recommend.py](tokenjam-integration.md) → query tokenjam.core.optimize.DOWNGRADE_CANDIDATES

2. Get clients
   └── [get_client](models.md#registry)(original_spec, mock=...) → ModelClient
   └── [get_client](models.md#registry)(candidate_spec, mock=...) → ModelClient

3. Load benchmark tasks
   └── benchmark.tasks(limit=...) → list[Task]

4. For each task, run N samples on original:
   └── client.complete(prompt) → Completion
   └── benchmark.score(task, completion.text) → ScoreResult
   └── [price_completion](cost-pricing.md)(provider, model, completion) → cost

5. For each task, run N samples on candidate:
   └── Same as step 4

6. Collect TaskOutcome objects (one per task)

7. assemble_proof(outcomes, original_spec, candidate_spec, ...)
   └── Compute statistics, CIs, verdict
   └── Return ProofResult
```

### `assemble_proof()`

The shared assembler used by both pipelines.

```python
def assemble_proof(
    outcomes: list[TaskOutcome],
    original_spec: str,
    candidate_spec: str,
    *,
    benchmark_name: str,
    mock: bool = False,
    tokenjam_version: str = "",
    tokenjam_location: str = "",
) -> ProofResult:
```

What it does:
1. **Version stamp** — Records `tokenjam_version` and `tokenjam_location`
2. **Pass rates** — Computes original and candidate pass rates
3. **Wilson CIs** — [`wilson_interval`](statistics.md#wilson-interval) for each pass rate
4. **McNemar test** — [`mcnemar_exact`](statistics.md#mcnemar-exact-test) on discordant pairs
5. **Delta CI** — [`paired_delta_ci`](statistics.md#paired-delta-ci) for the pass-rate difference
6. **Verdict** — Based on significance, sample size, and delta magnitude
7. **Cost analysis** — Total cost, cost delta, token inflation flag
8. **Regressions** — Lists tasks where candidate failed but original passed

### Verdict Logic

Implemented by `_verdict(n_tasks, significant, delta_pp)`, gated at
`MIN_TASKS_FOR_VERDICT = 10` (`delta_pp = candidate_pass_rate − original_pass_rate`):

| Condition | Verdict |
|-----------|---------|
| n < 10 | `insufficient_evidence` |
| n ≥ 10, significant and delta < 0 | `significant_regression` |
| n ≥ 10, otherwise | `no_significant_regression` |

These three are the only verdicts (never `SAFE`). See
[statistics.md](statistics.md#verdict-logic) for the full rationale.

## Agent Proof Pipeline

### Entry Point: `run_agent_proof()`

Located in [`agent_pipeline.py`](../agent_pipeline.py).

```python
def run_agent_proof(
    benchmark: AgentBenchmark,
    original_spec: str,
    candidate_spec: str | None = None,
    *,
    mock: bool = False,
    candidate_behavior: str = "ok",
    temperature: float = 0.0,
    max_tokens: int | None = None,
    max_turns: int = 10,
    samples: int = 1,
    limit: int | None = None,
) -> ProofResult:
```

### Flow

```
1. Resolve candidate (same as single-shot)

2. Get tool-calling clients
   └── get_tool_calling_client(original_spec, mock=...) → ToolCallingClient
   └── get_tool_calling_client(candidate_spec, mock=...) → ToolCallingClient

3. Load benchmark
   └── benchmark.tools() → ToolRegistry
   └── benchmark.tasks(limit=...) → list[AgentTask]

4. For each task, run N samples on original:
   └── AgentRunner(client, registry, max_turns).run(task_id, prompt)
   │       └── Loop: chat → tool calls → execute → feed back → repeat or stop
   │       └── Returns AgentTrace (turns, final_text, token sums)
   └── benchmark.score(task, trace) → ScoreResult
   │       └── validate_tools(trace, registry, expected_tools, forbidden_tools, expected_order)
   │           → safety gate, ordering, tool errors
   └── price_completion(provider, model, trace.as_completion()) → cost

5. For each task, run N samples on candidate:
   └── Same as step 4

6. Collect TaskOutcome objects

7. assemble_proof(...) → ProofResult (same assembler!)
```

### Key Difference: Scoring

Agent scoring is more complex than single-shot:

- **Answer correctness** — Does the final text match the expected answer?
- **Tool validation** — Were the right tools called? In the right order?
- **Safety gate** — Were any forbidden/dangerous tools called?

A task can fail on **action** (wrong tools, unsafe tools) even if the final answer is correct. This is by design — we measure whether the cheaper model maintains the *full behavior* of the original, not just the final output.

## Token Summation in Agent Mode

In multi-turn agent runs, token usage is summed across all turns:

```python
total_input = sum(turn.input_tokens for turn in trace.turns)
total_output = sum(turn.output_tokens for turn in trace.turns)
```

This aggregated usage is passed to [`price_completion`](cost-pricing.md) to compute the total cost of the agent session.

## Mock Behavior

### Single-Shot Mock

[`MockClient`](models.md#mockclient) reads `# task_key:` markers from prompts and returns deterministic responses. The `mock_candidate_accuracy` parameter controls what fraction of tasks the mock candidate "passes."

### Agent Mock

[`MockAgentClient`](models.md#mockagentclient) simulates tool-calling behavior:
- `ok`: Correct tool calls, correct final answer
- `wrong`: Wrong final answer (may have correct or wrong tools)
- `unsafe`: Calls a dangerous tool (triggers safety gate)

## Output Artifacts

Both pipelines produce a `ProofResult` that can be:

1. **Rendered** — Rich table in the terminal
2. **Serialized** — JSON file in `results/` (filename includes TokenJam version and timestamp)
3. **Inspected programmatically** — `to_dict()` returns a JSON-serializable dict

Example artifact filename:
```
proof_samples_claude-opus-4-7_0.4.2_20250624T214606.json
```

## Related Documentation

- [Models](models.md) — ModelClient and ToolCallingClient protocols
- [Benchmarks](benchmarks.md) — Benchmark and AgentBenchmark protocols
- [Agents](agents.md) — AgentRunner, ToolRegistry, safety gate
- [Statistics](statistics.md) — Wilson, McNemar, delta CI
- [Cost & Pricing](cost-pricing.md) — How costs are computed
- [Report](api-reference.md#reportpy) — ProofResult, ProofStats, TaskOutcome
- [TokenJam Integration](tokenjam-integration.md) — How candidate resolution works
