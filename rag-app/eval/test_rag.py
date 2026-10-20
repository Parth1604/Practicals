"""DeepEval tests for the Nimbus RAG pipeline.

Run with:  deepeval test run eval/test_rag.py
"""
import json
import sys
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import EVAL_MODEL  # noqa: E402
from rag import answer  # noqa: E402

GOLDEN = json.loads((Path(__file__).parent / "golden.json").read_text())

metrics = [
    AnswerRelevancyMetric(threshold=0.7, model=EVAL_MODEL),      # does the answer address the question?
    FaithfulnessMetric(threshold=0.7, model=EVAL_MODEL),         # is the answer grounded in retrieved context?
    ContextualPrecisionMetric(threshold=0.7, model=EVAL_MODEL),  # are relevant chunks ranked first?
    ContextualRecallMetric(threshold=0.7, model=EVAL_MODEL),     # does the context contain what's needed?
]


@pytest.mark.parametrize("golden", GOLDEN, ids=[g["input"][:40] for g in GOLDEN])
def test_rag(golden):
    result = answer(golden["input"])
    test_case = LLMTestCase(
        input=golden["input"],
        actual_output=result.answer,
        expected_output=golden["expected_output"],
        retrieval_context=[c.content for c in result.contexts],
    )
    assert_test(test_case, metrics)
