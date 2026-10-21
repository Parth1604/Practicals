"""DeepEval tests for the LangGraph RAG pipeline (same golden set and metrics as ../rag-app).

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
from config import EVAL_MODEL, GOLDEN_PATH  # noqa: E402
from graph import ask  # noqa: E402

GOLDEN = json.loads(GOLDEN_PATH.read_text())

metrics = [
    AnswerRelevancyMetric(threshold=0.7, model=EVAL_MODEL),
    FaithfulnessMetric(threshold=0.7, model=EVAL_MODEL),
    ContextualPrecisionMetric(threshold=0.7, model=EVAL_MODEL),
    ContextualRecallMetric(threshold=0.7, model=EVAL_MODEL),
]


@pytest.mark.parametrize("golden", GOLDEN, ids=[g["input"][:40] for g in GOLDEN])
def test_rag(golden):
    result = ask(golden["input"])
    test_case = LLMTestCase(
        input=golden["input"],
        actual_output=result["answer"],
        expected_output=golden["expected_output"],
        # The graded documents are exactly what the generator saw.
        retrieval_context=[d.page_content for d in result["documents"]],
    )
    assert_test(test_case, metrics)
