# Development Guide

## Setup

```bash
cd tokenjam-bench
pip install -e ".[dev]"
```

For live provider support:
```bash
pip install -e ".[providers,datasets]"
```

## Development Commands

The [`Makefile`](../Makefile) provides common tasks:

| Command | Description |
|---------|-------------|
| `make install` | Install in editable mode with dev dependencies |
| `make update-tokenjam` | Upgrade the `tokenjam` package and print version |
| `make test` | Run the full test suite (pytest, offline, ~5s) |
| `make lint` | Run ruff check and ruff format --check |
| `make bench-smoke` | Run a quick smoke benchmark with mock clients |

## Test Suite

All tests are **offline** (mock clients, no API keys, no network). Run with `pytest -q` or `make test`.

| Test File | What It Verifies |
|-----------|-----------------|
| `test_pipeline_offline.py` | End-to-end single-shot pipeline |
| `test_agent_pipeline_offline.py` | End-to-end agent pipeline |
| `test_agent_runner.py` | AgentRunner loop mechanics |
| `test_agent_validation.py` | Tool-call validation and safety gate |
| `test_scoring.py` | Code extraction and scoring |
| `test_stats.py` | Statistical correctness |
| `test_report.py` | Cost-validation and headline logic |
| `test_version_stamp.py` | TokenJam version resolution |

### Test Philosophy

- **100% offline**: All tests use `MockClient` / `MockAgentClient`
- **Deterministic**: Mock behavior is keyed by `# task_key:` markers
- **CI-ready**: No provider SDKs, no keys, no dataset downloads required
- **Honest about small samples**: Tests verify that `n=5` cannot produce a significant McNemar result

## Project Structure Rules

- **Flat layout**: Top-level `.py` files and subpackages at root (no `tokenjam_bench/` directory)
- **Pure domain logic**: `models/`, `benchmarks/`, `agents/` have no CLI or HTTP imports
- **Protocols over inheritance**: `ModelClient`, `Benchmark`, `AgentBenchmark` are protocols
- **Lazy imports**: Live clients lazy-import their SDKs

## Adding a New Benchmark

1. Create a new file in `benchmarks/`
2. Implement the `Benchmark` or `AgentBenchmark` protocol
3. Register it in `benchmarks/__init__.py`
4. Add tests in `tests/`

Example:

```python
# benchmarks/my_benchmark.py
from dataclasses import dataclass
from benchmarks.base import Benchmark, Task, ScoreResult

@dataclass
class MyBenchmark:
    def tasks(self, limit=None):
        return [Task(...), ...]
    
    def score(self, task, text):
        return ScoreResult(passed=..., detail=...)
```

## Adding a New Model Client

1. Create a new file in `models/`
2. Implement `ModelClient` or `ToolCallingClient` protocol
3. Register it in `models/registry.py`
4. Add tests in `tests/`

## Code Style

- **Ruff** for linting and formatting
- **Type hints** on all public functions
- **Docstrings** on all modules and public classes
- **No unicode bullets** in output — Rich handles formatting

## Related Documentation

- [TokenJam's Development Guide](https://github.com/HoomanDigital/tokenjam/blob/main/CLAUDE.md) — The main project's agent guide
- [TokenJam's Testing Architecture](https://github.com/HoomanDigital/tokenjam/blob/main/docs/architecture.md) — Test layers and factories
- [API Reference](api-reference.md) — Module-level API docs
