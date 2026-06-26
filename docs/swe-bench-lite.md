# SWE-Bench Lite — Experimental Scaffold

> ## ⚠️ Status: experimental scaffold — NOT a working benchmark
>
> `swe-bench-lite` does **not** verify bug fixes and **cannot produce a
> SWE-bench pass-rate**. Fix-verification (running each task's `FAIL_TO_PASS` /
> `PASS_TO_PASS` tests against the agent's edits) is **not implemented**.
> `score()` is intentionally disabled — it raises `NotImplementedError` — so no
> result is ever emitted. **Do not present any number from this module as a
> SWE-bench result.**

## What exists today

This module is a starting point for a future real SWE-bench integration. The
parts that are genuinely implemented and tested:

- **`SWEBenchTask`** — a dataclass carrying the SWE-bench fields (repo, base
  commit, `FAIL_TO_PASS`, `PASS_TO_PASS`, problem statement, …).
- **Dataset loader** (`tasks()`) — reads `princeton-nlp/SWE-bench_Lite` via the
  `datasets` extra (when installed).
- **Prompt construction** — builds an agent prompt from the problem statement
  and the files named in the patch.
- **Developer tool registry** (`tools()`) — `view`, `view_range`, `str_replace`,
  `create`, `insert`, `bash`.
- **`SWEBenchToolSet`** (`agents/swe_bench_tools.py`) — real workspace-bound
  implementations of those tools (path-traversal guarded, exact-match edits,
  timed `bash`). Currently tested in isolation and **not wired** into the
  benchmark run path.

## What is NOT implemented (why scoring is disabled)

A real SWE-bench score is defined entirely by test execution:

1. Check out the repository at the task's base commit.
2. Set up the environment (install dependencies).
3. Apply the agent's edits to the working tree.
4. Run `FAIL_TO_PASS` tests — must pass (the bug is fixed).
5. Run `PASS_TO_PASS` tests — must still pass (no regression).

None of steps 1–5 are done here. An earlier version of this benchmark "passed" a
task whenever the agent merely **made an edit and ran `bash`** — a tool-usage
check that says nothing about whether the bug was actually fixed. That number
looked like a pass-rate but was not one, so it has been removed: `score()` now
raises rather than returning a misleading result.

## Behaviour

```python
from tjbench.benchmarks.swe_bench_lite import SWEBenchLiteBenchmark, EXPERIMENTAL_NOTICE

bench = SWEBenchLiteBenchmark()
bench.tools()                 # OK — returns the developer tool registry
bench._build_prompt(example)  # OK — prompt construction
bench.score(task, trace)      # raises NotImplementedError(EXPERIMENTAL_NOTICE)
```

Running it through the agent proof pipeline (`tjbench agent --benchmark
swe-bench-lite …`) will therefore fail loudly during scoring with the
experimental notice, instead of emitting a fake pass-rate.

## Roadmap to a real benchmark

To turn this scaffold into a real benchmark, an implementer would wire
`SWEBenchToolSet` into the run path and implement steps 1–5 above (repo
checkout, env setup, patch application, test execution), then replace the
`score()` gate with a verdict derived from `FAIL_TO_PASS` / `PASS_TO_PASS`
results. Until then it stays disabled.

## Related Documentation

- [Agents](agents.md) — AgentRunner, ToolRegistry, safety gate, `SWEBenchToolSet`
- [Benchmarks](benchmarks.md) — Benchmark protocols and registry
- [SWE-Bench Official Repo](https://github.com/princeton-nlp/SWE-bench) — the real benchmark this scaffold aims at
