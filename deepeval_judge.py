"""DeepEval-backed judge (the metric your boss asked for).

Wraps DeepEval metrics as the bench's `Judge` so semantic scores
(correctness / answer-relevancy / faithfulness / task-completion) feed the same
Wilson/McNemar stats as executable pass/fail.

Key-gated and lazy: DeepEval and its judge model are only imported/constructed
when a real run asks for them. The judge model needs an API key (OpenAI by
default, or pass model=...). There's no offline test for this adapter — the
MockJudge is the tested path — so it's kept thin and close to DeepEval's API.

  pip install deepeval
  export OPENAI_API_KEY=...
  TJBENCH_JUDGE=deepeval TJBENCH_JUDGE_METRIC=correctness \
      tjbench run --benchmark judged --original anthropic:claude-opus-4-7
"""
from __future__ import annotations

from judge import JUDGE_METRICS, JudgeCase, JudgeResult


class DeepEvalJudge:
    name = "deepeval"

    def __init__(self, metric: str = "correctness", threshold: float = 0.5,
                 model: str = "gpt-4o") -> None:
        if metric not in JUDGE_METRICS:
            raise ValueError(f"Unknown metric '{metric}'. Available: {JUDGE_METRICS}")
        self.metric = metric
        self.threshold = threshold
        self.model = model

    def _build_metric(self):
        """Construct the DeepEval metric for this judge. Lazy-imported."""
        try:
            from deepeval.metrics import (
                AnswerRelevancyMetric,
                FaithfulnessMetric,
                GEval,
            )
            from deepeval.test_case import LLMTestCaseParams
        except ImportError as exc:  # pragma: no cover - exercised only without the dep
            raise RuntimeError(
                "DeepEval is not installed. Run `pip install deepeval` and set a "
                "judge-model API key (e.g. OPENAI_API_KEY)."
            ) from exc

        if self.metric == "answer-relevancy":
            return AnswerRelevancyMetric(threshold=self.threshold, model=self.model)
        if self.metric == "faithfulness":
            return FaithfulnessMetric(threshold=self.threshold, model=self.model)
        if self.metric == "task-completion":
            return GEval(
                name="TaskCompletion",
                criteria="Whether the actual output fully completes the task asked "
                         "for in the input.",
                evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
                threshold=self.threshold, model=self.model,
            )
        # default: correctness
        return GEval(
            name="Correctness",
            criteria="Whether the actual output is factually correct and "
                     "semantically equivalent to the expected output.",
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            threshold=self.threshold, model=self.model,
        )

    def evaluate(self, case: JudgeCase) -> JudgeResult:  # pragma: no cover - needs a key
        from deepeval.test_case import LLMTestCase

        metric = self._build_metric()
        tc = LLMTestCase(
            input=case.input,
            actual_output=case.actual_output,
            expected_output=case.expected_output,
            retrieval_context=case.context,
        )
        metric.measure(tc)
        score = float(metric.score or 0.0)
        return JudgeResult(
            metric=self.metric, score=round(score, 4), threshold=self.threshold,
            passed=bool(getattr(metric, "is_successful", lambda: score >= self.threshold)()),
            reason=str(getattr(metric, "reason", "") or ""),
        )
