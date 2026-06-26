"""SWE-Bench Lite — EXPERIMENTAL SCAFFOLD (fix-verification NOT implemented).

⚠️  This is an *experimental scaffold*, not a working SWE-bench benchmark. It
does NOT verify bug fixes and CANNOT produce a SWE-bench pass-rate. Do not
present any number derived from this module as a SWE-bench result.

What real SWE-bench scoring requires — and what this scaffold does NOT do:

- Check out the repository at the base commit, apply the agent's edits, and run
  the task's ``FAIL_TO_PASS`` tests (must pass = bug fixed) and ``PASS_TO_PASS``
  tests (must still pass = no regression).

None of that is wired up. The only thing the previous implementation checked was
*tool usage* — i.e. "the agent made an edit and ran bash" — which says nothing
about whether the bug was actually fixed. Because that check could be mistaken
for a real pass-rate, scoring is now intentionally disabled: ``score()`` raises
``NotImplementedError`` (see ``EXPERIMENTAL_NOTICE``).

The pieces that ARE real and inspectable are kept so a future implementer can
build on them: the dataset-task dataclass, the developer tool registry
(``tools()``), prompt construction, and patch parsing. The actual workspace
tooling lives in ``tjbench.agents.swe_bench_tools.SWEBenchToolSet`` and is also
an unwired scaffold today.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tjbench.benchmarks.agent_base import AgentBenchmark, AgentTask
from tjbench.benchmarks.base import ScoreResult
from tjbench.agents.tools import Tool, ToolRegistry
from tjbench.agents.trace import AgentTrace

# The single source of truth for "this benchmark cannot produce a real result".
# Raised by score() so no ScoreResult — and therefore no pass-rate — is ever
# emitted from this scaffold.
EXPERIMENTAL_NOTICE = (
    "swe-bench-lite is an EXPERIMENTAL SCAFFOLD: fix-verification "
    "(FAIL_TO_PASS / PASS_TO_PASS test execution) is NOT implemented, so it "
    "cannot produce a SWE-bench pass-rate. The earlier behaviour only checked "
    "tool usage (an edit was made + bash was run), which must never be read as a "
    "real result. Scoring is intentionally disabled until real test-based "
    "verification is wired in."
)


@dataclass
class SWEBenchTask(AgentTask):
    """A SWE-Bench Lite task with repository context."""
    repo: str = ""
    base_commit: str = ""
    test_patch: str = ""
    fail_to_pass: list[str] = field(default_factory=list)
    pass_to_pass: list[str] = field(default_factory=list)
    problem_statement: str = ""
    hints_text: str = ""
    environment_setup_commit: str = ""


@dataclass
class SWEBenchState:
    """Mutable state for a SWE-Bench task session."""
    repo_dir: Path
    files: dict[str, str]  # filepath -> content
    test_results: dict[str, Any]  # test_name -> result


class SWEBenchLiteBenchmark(AgentBenchmark):
    """SWE-Bench Lite — EXPERIMENTAL SCAFFOLD; fix-verification NOT implemented.

    This class can build prompts and expose developer tools, but it does NOT
    verify bug fixes: ``score()`` raises ``NotImplementedError`` so no pass-rate
    can be produced. See the module docstring and ``EXPERIMENTAL_NOTICE`` for
    why, and what real scoring would need (repo checkout + FAIL_TO_PASS /
    PASS_TO_PASS test execution).
    """

    def __init__(self, limit: int | None = None, mock: bool = False) -> None:
        self._limit = limit
        self._mock = mock
        self._tasks: list[SWEBenchTask] | None = None

    def _load_tasks(self) -> list[SWEBenchTask]:
        """Load SWE-Bench Lite tasks from the datasets library."""
        if self._tasks is not None:
            return self._tasks

        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError(
                "SWE-Bench Lite requires 'datasets'. Install with: "
                "pip install -e '.[datasets]'"
            )

        ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
        tasks = []
        for i, ex in enumerate(ds):
            if self._limit is not None and i >= self._limit:
                break

            task = SWEBenchTask(
                task_id=ex["instance_id"],
                prompt=self._build_prompt(ex),
                expected_answer="bug_fixed",
                expected_tools=["view", "str_replace", "bash"],
                forbidden_tools=["submit"],  # Must not submit until tests pass
                repo=ex["repo"],
                base_commit=ex.get("base_commit", ""),
                test_patch=ex.get("test_patch", ""),
                fail_to_pass=json.loads(ex.get("FAIL_TO_PASS", "[]")),
                pass_to_pass=json.loads(ex.get("PASS_TO_PASS", "[]")),
                problem_statement=ex.get("problem_statement", ""),
                hints_text=ex.get("hints_text", ""),
                environment_setup_commit=ex.get("environment_setup_commit", ""),
            )
            tasks.append(task)

        self._tasks = tasks
        return tasks

    def _build_prompt(self, ex: dict) -> str:
        """Build the agent prompt from a SWE-Bench example."""
        problem = ex.get("problem_statement", "")
        repo = ex.get("repo", "")
        instance_id = ex.get("instance_id", "")
        
        # Extract file paths from the patch
        patch = ex.get("patch", "")
        files_changed = self._extract_files_from_patch(patch)
        
        prompt = f"""You are fixing a bug in {repo}.

Issue: {instance_id}

Problem Statement:
{problem}

Files that may need changes:
{chr(10).join(files_changed) if files_changed else "(unknown - explore the codebase)"}

Your task:
1. Read the relevant files to understand the bug
2. Make the minimal fix needed
3. Run tests to verify your fix works

You have access to tools: view, view_range, str_replace, create, insert, bash.

Start by reading the problem statement and exploring the codebase.
"""
        return prompt

    def _extract_files_from_patch(self, patch: str) -> list[str]:
        """Extract file paths from a git diff patch."""
        files = []
        for line in patch.split("\n"):
            if line.startswith("diff --git a/"):
                # Extract path after "diff --git a/"
                match = re.match(r"diff --git a/(.+?) b/", line)
                if match:
                    files.append(match.group(1))
        return files

    def tools(self) -> ToolRegistry:
        """Create the tool registry with SWE-Bench developer tools."""
        registry = ToolRegistry()
        
        # These tools will be bound to a specific task's state at runtime
        # The actual implementation is in the runner
        registry.register(Tool(
            name="view",
            description="View the contents of a file. Shows line numbers.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to view (relative to workspace)"},
                },
                "required": ["path"],
            },
            dangerous=False,
            run=lambda args: "",  # Placeholder - replaced at runtime
        ))
        
        registry.register(Tool(
            name="view_range",
            description="View a specific range of lines in a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start": {"type": "integer", "description": "Start line (1-indexed)"},
                    "end": {"type": "integer", "description": "End line (1-indexed)"},
                },
                "required": ["path", "start", "end"],
            },
            dangerous=False,
            run=lambda args: "",
        ))
        
        registry.register(Tool(
            name="str_replace",
            description="Replace an exact string in a file. The old_str must match exactly once.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {"type": "string", "description": "Exact text to replace (must match exactly once)"},
                    "new_str": {"type": "string", "description": "Replacement text"},
                },
                "required": ["path", "old_str", "new_str"],
            },
            dangerous=False,
            run=lambda args: "",
        ))
        
        registry.register(Tool(
            name="create",
            description="Create a new file with the given content.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            dangerous=False,
            run=lambda args: "",
        ))
        
        registry.register(Tool(
            name="insert",
            description="Insert text after a specific line in a file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "line": {"type": "integer", "description": "Line after which to insert (1-indexed)"},
                    "new_str": {"type": "string"},
                },
                "required": ["path", "line", "new_str"],
            },
            dangerous=False,
            run=lambda args: "",
        ))
        
        registry.register(Tool(
            name="bash",
            description="Run a shell command in the workspace. Use for running tests, git, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"},
                },
                "required": ["command"],
            },
            dangerous=True,  # Can run arbitrary commands
            run=lambda args: "",
        ))
        
        return registry

    def tasks(self, limit: int | None = None) -> list[SWEBenchTask]:
        """Return SWE-Bench Lite tasks."""
        all_tasks = self._load_tasks()
        if limit is not None:
            return all_tasks[:limit]
        return all_tasks

    def score(self, task: SWEBenchTask, trace: AgentTrace) -> ScoreResult:
        """Disabled: this scaffold cannot verify a fix, so it is not scored.

        Real SWE-bench scoring would apply the agent's edits to a checked-out
        repo and run the task's FAIL_TO_PASS / PASS_TO_PASS tests. None of that
        is implemented. The earlier code passed a task whenever the agent merely
        "made an edit and ran bash" — a tool-usage check that says nothing about
        whether the bug was fixed and could be mistaken for a real pass-rate.

        To make it impossible to read a fake SWE-bench pass-rate, scoring raises
        instead of returning a ``ScoreResult``.
        """
        raise NotImplementedError(EXPERIMENTAL_NOTICE)
