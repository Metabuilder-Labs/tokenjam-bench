"""Production Workflow Benchmark Suite.

Real enterprise workloads (customer support, RAG assistants, email, research,
…) modelled as *another benchmark family* — NOT a new pipeline. A workflow suite
is a dataset-driven, judge-scored `Benchmark`: it yields `Task`s from a JSON
dataset under `datasets/<suite>/` and scores the candidate's reply with the same
DeepEval/MockJudge seam as `JudgedBenchmark`. So every workflow run flows through
the identical proof machinery — Wilson CI + exact McNemar + measured cost +
report + dashboard + historical DB — with zero duplicated logic.

Offline determinism: each task embeds `# echo: <reference>` so the deterministic
mock model returns the reference answer (and a weaker candidate returns a wrong
string the judge then fails), exercising the judge seam with no keys.

Run:  tjb run --benchmark customer-support --original anthropic:claude-opus-4-7
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from tjbench.benchmarks.base import ScoreResult, Task
from tjbench.judge import Judge, JudgeCase, judge_from_env

# `datasets/` lives at the repo root (one level above the `tjbench/` package).
# Overridable for packaged installs that relocate the data.
DATASETS_DIR = Path(
    os.environ.get("TJBENCH_DATASETS_DIR")
    or Path(__file__).resolve().parents[2] / "datasets"
)

# Text (judge-scored) workflow suites. suite -> (subdir, file, label, list key).
WORKFLOW_SUITES: dict[str, tuple[str, str, str, str]] = {
    "customer-support": ("customer_support", "tickets.json", "Customer Support", "tickets"),
    "enterprise-rag": ("rag", "qa.json", "Enterprise RAG", "cases"),
    "email-assistant": ("email", "tasks.json", "Email Assistant", "tasks"),
    "research-assistant": ("research", "tasks.json", "Research Assistant", "tasks"),
}
WORKFLOW_NAMES = list(WORKFLOW_SUITES)

# How each suite frames its task prompt (system instruction before the request).
_PROMPTS = {
    "customer-support": (
        "You are a customer-support agent. Answer the ticket helpfully and stay "
        "grounded in the provided policy; do not invent policy."
    ),
    "enterprise-rag": (
        "You are an enterprise knowledge assistant. Answer strictly from the "
        "provided documents, cite them, and say so if the answer isn't present."
    ),
    "email-assistant": (
        "You are an email assistant. Complete the requested task (reply, "
        "summarize, triage, or extract) accurately and in a professional tone."
    ),
    "research-assistant": (
        "You are a research assistant. Synthesize the provided sources into a "
        "grounded, well-reasoned answer and do not fabricate citations."
    ),
}


def _load_cases(subdir: str, fname: str, list_key: str) -> list[dict]:
    path = DATASETS_DIR / subdir / fname
    if not path.is_file():
        raise FileNotFoundError(
            f"Workflow dataset not found: {path}. Set TJBENCH_DATASETS_DIR or run "
            "from a source checkout where datasets/ is present."
        )
    return json.loads(path.read_text()).get(list_key, [])


class WorkflowBenchmark:
    """A production-workflow suite scored by a judge, flowing through the same
    proof stats as every other benchmark."""

    def __init__(self, name: str, cases: list[dict], judge: Judge | None = None) -> None:
        self.name = name
        self._judge = judge or judge_from_env()
        self._system = _PROMPTS.get(name, "Answer the request accurately and completely.")
        self._tasks = [self._to_task(c) for c in cases]

    def _to_task(self, c: dict) -> Task:
        # Field-flexible so every suite is pure data: input/expected/context have
        # synonyms; all remaining dataset fields are carried through as metadata
        # for the report + dashboard (intent, category, citations, sources, …).
        question = c.get("question") or c.get("input") or c.get("prompt") or ""
        expected = c.get("expected_response") or c.get("expected") or ""
        context = c.get("knowledge_context") or c.get("context")
        # echo → offline mock returns the reference, so the suite runs with no keys.
        prompt = (
            f"{self._system}\n\nRequest: {question}\n"
            f"# task_key: {c['id']}\n# echo: {expected}\n"
        )
        meta = dict(c)
        meta.update({"question": question, "expected": expected, "context": context,
                     "intent": c.get("expected_intent")})
        return Task(task_id=c["id"], prompt=prompt, kind="workflow", metadata=meta)

    def tasks(self, limit: int | None = None) -> list[Task]:
        return self._tasks if limit is None else self._tasks[:limit]

    def score(self, task: Task, completion_text: str) -> ScoreResult:
        case = JudgeCase(
            input=task.metadata.get("question", task.prompt),
            actual_output=completion_text,
            expected_output=task.metadata.get("expected"),
            context=task.metadata.get("context"),
        )
        r = self._judge.evaluate(case)
        return ScoreResult(
            r.passed,
            f"{self._judge.name}:{r.metric} score={r.score:.2f} (>= {r.threshold}) — {r.reason[:80]}",
        )


def get_workflow(name: str, judge: Judge | None = None) -> WorkflowBenchmark:
    if name not in WORKFLOW_SUITES:
        raise ValueError(f"Unknown workflow '{name}'. Available: {WORKFLOW_NAMES}")
    subdir, fname, _label, list_key = WORKFLOW_SUITES[name]
    return WorkflowBenchmark(name, _load_cases(subdir, fname, list_key), judge=judge)


# Agentic (multi-turn, AgentRunner-scored) workflow suites. These run through
# the *agent* proof pipeline rather than the judge seam — same stats either way.
from tjbench.workflows.agentic import (  # noqa: E402  (after the text defs)
    AGENTIC_WORKFLOWS,
    get_agentic_workflow,
)

AGENTIC_WORKFLOW_NAMES = list(AGENTIC_WORKFLOWS)
_AGENTIC_LABELS = {"n8n": "n8n Automation", "coding-workflow": "Coding Workflow"}
# Every workflow suite (text + agentic), for the CLI and dashboard.
ALL_WORKFLOW_NAMES = WORKFLOW_NAMES + AGENTIC_WORKFLOW_NAMES


def is_agentic_workflow(name: str) -> bool:
    return name in AGENTIC_WORKFLOWS


def workflow_label(name: str) -> str:
    if name in WORKFLOW_SUITES:
        return WORKFLOW_SUITES[name][2]
    return _AGENTIC_LABELS.get(name, name)


__all__ = [
    "WorkflowBenchmark", "WORKFLOW_SUITES", "WORKFLOW_NAMES", "ALL_WORKFLOW_NAMES",
    "AGENTIC_WORKFLOWS", "AGENTIC_WORKFLOW_NAMES", "get_workflow",
    "get_agentic_workflow", "is_agentic_workflow", "workflow_label", "DATASETS_DIR",
]
