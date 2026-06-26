"""Production Workflow suites — offline (mock model + MockJudge), reusing the
same proof stats (Wilson CI + McNemar + cost) as every other benchmark."""
from __future__ import annotations

from tjbench.benchmarks import get_benchmark
from tjbench.pipeline import run_proof
from tjbench.workflows import WORKFLOW_NAMES, get_workflow, workflow_label


def test_customer_support_dataset_loads():
    wf = get_workflow("customer-support")
    tasks = wf.tasks()
    assert wf.name == "customer-support"
    assert len(tasks) >= 12
    t = tasks[0]
    assert t.kind == "workflow"
    assert t.metadata["intent"] and t.metadata["category"]
    assert t.metadata["expected"] and t.metadata["context"]
    assert workflow_label("customer-support") == "Customer Support"


def test_every_workflow_registered_in_the_benchmark_dispatch():
    # A workflow is "just another benchmark" — get_benchmark must resolve it.
    for name in WORKFLOW_NAMES:
        assert get_benchmark(name).name == name


def test_customer_support_full_accuracy_holds_and_is_cheaper():
    # Mock model echoes the reference → MockJudge passes; candidate at full
    # accuracy holds the original's pass-rate at lower cost (tokenjam downgrade).
    result = run_proof(
        benchmark_name="customer-support",
        original_spec="anthropic:claude-opus-4-7",
        mock=True, mock_candidate_accuracy=1.0,
    )
    assert result.benchmark == "customer-support"
    assert result.candidate_model == "anthropic:claude-haiku-4-5"
    assert result.n_tasks == len(get_workflow("customer-support").tasks())
    assert result.original_pass == result.n_tasks
    assert result.candidate_pass == result.n_tasks
    assert result.accuracy_delta_pp == 0.0
    assert result.cost_delta_pct < 0
    assert result.tokenjam_version


def test_customer_support_regression_is_detected():
    # Candidate that fails the judge on everything → -100pp, all flagged.
    result = run_proof(
        benchmark_name="customer-support",
        original_spec="anthropic:claude-opus-4-7",
        mock=True, mock_candidate_accuracy=0.0,
    )
    assert result.candidate_pass == 0
    assert result.accuracy_delta_pp == -100.0
    assert result.regressions == result.original_pass
