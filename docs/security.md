# Security

## Overview

Security is a first-class concern in tokenjam-bench. The framework executes model-generated code and runs multi-turn agents with tool-calling capabilities. This document describes the security measures in place.

## Execution Sandbox

### `exec_sandbox.py`

All model-generated code runs in a **subprocess with timeout**:

```python
def run_python(code: str, timeout: float = 5.0) -> tuple[bool, str]:
```

- **Subprocess isolation**: Code runs in a separate process, not the main Python interpreter
- **Timeout**: Infinite loops are killed after 5 seconds (configurable)
- **Temp directory**: Each execution gets a fresh temp directory
- **No network**: Subprocess has no special network privileges

### Recommendations

- Run only trusted benchmark suites on machines you control
- The sandbox prevents accidental infinite loops, not deliberate exploits
- For production use, consider Docker containers or firejail

## Path Traversal Protection

### SWE-Bench Tools

The `SWEBenchToolSet` blocks path traversal outside the workspace:

```python
def _resolve_path(self, path: str) -> Path:
    resolved = (self.workspace / path).resolve()
    if not str(resolved).startswith(str(self.workspace.resolve())):
        raise ValueError(f"Path {path} escapes workspace")
    return resolved
```

**Blocked:** `../../../etc/passwd` → Error
**Allowed:** `src/main.py` → Resolved relative to workspace

## Tool Safety

### Dangerous Tool Flag

Tools can be marked as `dangerous`:

```python
Tool(
    name="bash",
    description="Run shell commands",
    parameters={...},
    dangerous=True,  # Flagged by safety gate
    run=...,
)
```

### Safety Gate

The `validate_tools()` function checks:
1. **Expected tools**: All required tools were called
2. **Forbidden tools**: No dangerous tools were called inappropriately
3. **Ordering**: Tools were called in the expected order

A task **fails** if a forbidden tool is called, even if the final answer is correct.

### Example

```python
# Agent calls delete_records() then produces correct answer
# Result: FAIL (forbidden tool called)
# Output-only evaluation would have: PASS
```

This is by design — we measure whether the cheaper model maintains the *full safe behavior* of the original.

## Mock Mode Safety

`--mock` mode runs deterministically with:
- No provider SDKs loaded
- No API keys required
- No network access
- Predetermined responses

Mock runs are **flagged as illustrative** in all reports.

## Data Privacy

- No user data is collected
- Benchmark results are stored locally in `results/`
- No telemetry is sent to external services
- TokenJam integration uses local pricing tables only

## Reporting Security Issues

If you discover a security vulnerability, please report it to the maintainers privately before disclosing publicly.

## Related Documentation

- [Agents](agents.md) — Tool validation and safety gate
- [SWE-Bench Lite](swe-bench-lite.md) — Tool safety in repository editing
- [Execution Sandbox](benchmarks.md#execution-sandbox) — Code execution isolation
