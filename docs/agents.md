# Agents

## Overview

The `agents/` package implements multi-turn agent execution with tool-calling. It is the core of the [agent proof pipeline](pipelines.md#agent-proof-pipeline).

## Architecture

```
agents/
├── runner.py     # AgentRunner — the multi-turn loop (keystone)
├── tools.py      # Tool, ToolResult, ToolRegistry
├── trace.py      # AgentTrace, TurnRecord, ToolCallRecord
└── validation.py # validate_tools, ToolValidation (safety gate)
```

## AgentRunner

[`agents/runner.py`](../agents/runner.py)

The keystone component. Drives a [`ToolCallingClient`](models.md#toolcallingclient) against a [`ToolRegistry`](#toolregistry) for up to `max_turns`, recording every turn into an [`AgentTrace`](#agenttrace).

```python
class AgentRunner:
    def __init__(
        self,
        client: ToolCallingClient,
        registry: ToolRegistry,
        max_turns: int = 10,
    ): ...

    def run(self, task_id: str, prompt: str) -> AgentTrace:
        """Run the agent loop. Returns the full trace."""
```

### Loop Behavior

```python
for turn in range(max_turns):
    turn = client.chat(messages, tools)
    
    if turn.wants_tools:
        # Execute each tool call
        for tool_call in turn.tool_calls:
            result = registry.execute(tool_call.name, tool_call.arguments)
            messages.append(tool_result_message)
    else:
        # Final answer — stop
        trace.final_text = turn.text
        trace.stopped_reason = "completed"
        break
else:
    # Hit max_turns
    trace.stopped_reason = "max_turns"
```

### Safety

- **Max turns guard**: Prevents infinite loops (configurable via `--max-turns`)
- **Tool errors**: Caught and reported as error results, loop continues
- **No state sharing**: Each task gets a fresh runner instance

## ToolRegistry

[`agents/tools.py`](../agents/tools.py)

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None: ...
    def execute(self, name: str, arguments: dict) -> ToolResult: ...
    def specs(self) -> list[dict]: ...
```

### Tool Dataclass

```python
@dataclass
class Tool:
    name: str
    schema: dict          # JSON schema for the tool's parameters
    dangerous: bool       # True if this tool is dangerous (e.g., delete)
    run: Callable[[dict], str]  # The actual implementation
```

### ToolResult Dataclass

```python
@dataclass
class ToolResult:
    output: str
    is_error: bool = False
```

## AgentTrace

[`agents/trace.py`](../agents/trace.py)

The observable record of a multi-turn agent run.

```python
@dataclass
class AgentTrace:
    task_id: str
    turns: list[TurnRecord]
    final_text: str
    stopped_reason: str  # "completed" or "max_turns"

    @property
    def input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.turns)

    @property
    def output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.turns)

    def as_completion(self) -> Completion:
        """Convert to Completion for pricing."""
```

### TurnRecord

```python
@dataclass
class TurnRecord:
    index: int
    assistant_text: str
    tool_calls: list[ToolCallRecord]
    input_tokens: int
    output_tokens: int
```

### ToolCallRecord

```python
@dataclass
class ToolCallRecord:
    name: str
    arguments: dict
    result: str
    is_error: bool
```

## Tool Validation

[`agents/validation.py`](../agents/validation.py)

The safety gate. Validates tool usage against expectations.

```python
def validate_tools(
    trace: AgentTrace,
    registry: ToolRegistry,
    expected_tools: list[str],
    forbidden_tools: list[str],
    expected_order: list[str] | None = None,
) -> ToolValidation:
```

### ToolValidation Dataclass

```python
@dataclass
class ToolValidation:
    called_tools: list[str]
    expected_tools_called: bool
    forbidden_called: bool
    ordering_ok: bool
    safe: bool           # True if no forbidden tools called
```

### Validation Rules

1. **Expected tools**: All tools in `expected_tools` must be called at least once
2. **Forbidden tools**: No tool in `forbidden_tools` may be called (safety gate)
3. **Ordering**: If `expected_order` is provided, tools must be called in that exact order
4. **Safety**: `safe = not forbidden_called`

### Safety Gate Behavior

A task **fails** if:
- A forbidden tool is called (even if the final answer is correct)
- An expected tool is missing (even if the final answer is correct)
- Tools are called out of order (if order is specified)

This is by design — we measure whether the cheaper model maintains the *full behavior* of the original, not just the final output.

## SWE-Bench Tools

[`agents/swe_bench_tools.py`](../agents/swe_bench_tools.py)

Developer tools for repository editing and testing, intended for the [SWE-Bench Lite benchmark](benchmarks.md#swe-bench-lite).

> ⚠️ **Experimental scaffold.** `SWEBenchToolSet` is not yet wired into the benchmark's run path — `swe-bench-lite` scoring is disabled (fix-verification is not implemented). These tool implementations are tested in isolation and kept for a future real integration.

### SWEBenchToolSet

```python
class SWEBenchToolSet:
    def __init__(self, workspace: Path): ...
```

All tools operate within a specific workspace directory. Path traversal outside the workspace is blocked.

### `view()`

```python
def view(self, args: {"path": str}) -> ToolResult
```

Read a file with line numbers. Returns error if file doesn't exist.

### `view_range()`

```python
def view_range(self, args: {"path": str, "start": int, "end": int}) -> ToolResult
```

Read specific line range (1-indexed). Clamps to valid range.

### `str_replace()`

```python
def str_replace(self, args: {"path": str, "old_str": str, "new_str": str}) -> ToolResult
```

Replace exact string in file. Requirements:
- `old_str` must exist in the file
- `old_str` must appear exactly once (prevents accidental mass-replace)
- Returns error otherwise

### `create()`

```python
def create(self, args: {"path": str, "content": str}) -> ToolResult
```

Create a new file. Returns error if file already exists.

### `insert()`

```python
def insert(self, args: {"path": str, "line": int, "new_str": str}) -> ToolResult
```

Insert text after a specific line (1-indexed).

### `bash()`

```python
def bash(self, args: {"command": str, "timeout": int}) -> ToolResult
```

Run a shell command in the workspace. Has a configurable timeout (default 30s). Marked as **dangerous** for safety gate purposes.

### Safety Features

| Feature | Implementation |
|---------|---------------|
| Path traversal | Blocked — paths resolving outside workspace are rejected |
| Exact-match replace | Multiple occurrences → error |
| Bash timeout | Long-running commands timeout safely |
| Dangerous flag | `bash` marked dangerous for safety gate |

### Tool Specifications

```python
toolset.get_tool_specs() -> list[dict]
```

Returns all 6 tool definitions in provider-agnostic format for model advertisement.

---

[`models/mock_agent_client.py`](../models/mock_agent_client.py)

The mock agent client simulates three behaviors for testing:

| Mode | Tool Calls | Final Answer | Safety Gate |
|------|-----------|--------------|-------------|
| `ok` | Correct tools, correct order | Correct | Passes |
| `wrong` | May be correct or wrong | Wrong | May fail |
| `unsafe` | Calls forbidden tool | (any) | Fails |

## Related Documentation

- [Pipelines](pipelines.md#agent-proof-pipeline) — How agents fit into the proof pipeline
- [Models](models.md#toolcallingclient) — ToolCallingClient protocol
- [Benchmarks](benchmarks.md#agent-benchmarks) — AgentBenchmark and AgentTask
- [CLI Reference](cli-reference.md#tjbench-agent) — `tjbench agent` command
