"""
Tests for Mock Interview evaluator.
"""
import pytest
from apps.mock_interview.evaluator import evaluate_response, _compute_grade, _generate_feedback


class TestEvaluateResponse:
    def test_score_in_range(self):
        result = evaluate_response(
            user_response="Python is a high-level programming language used for web development and data science",
            expected_keywords=["Python", "high-level", "web", "data"],
            model_answer="Python is a high-level, interpreted programming language known for its simplicity",
        )
        assert 0 <= result["score"] <= 100
        assert 0 <= result["keyword_score"] <= 100
        assert "grade" in result
        assert "feedback" in result

    def test_keyword_matching(self):
        result = evaluate_response(
            user_response="Python Django React AWS",
            expected_keywords=["Python", "Django", "React", "AWS"],
            model_answer="These are popular technologies",
        )
        assert result["keyword_score"] == 100.0

    def test_poor_response_gives_poor_grade(self):
        result = evaluate_response(
            user_response="I don't know",
            expected_keywords=["algorithm", "complexity", "recursion", "data structure"],
            model_answer="Big O notation measures algorithm efficiency in terms of time and space complexity",
        )
        assert result["keyword_score"] < 50

    def test_empty_keywords_uses_default(self):
        result = evaluate_response(
            user_response="Some response",
            expected_keywords=[],
            model_answer="Some model answer",
        )
        assert result["keyword_score"] == 50.0


class TestComputeGrade:
    def test_poor(self):
        assert _compute_grade(0) == "poor"
        assert _compute_grade(40) == "poor"

    def test_average(self):
        assert _compute_grade(41) == "average"
        assert _compute_grade(60) == "average"

    def test_good(self):
        assert _compute_grade(61) == "good"
        assert _compute_grade(80) == "good"

    def test_excellent(self):
        assert _compute_grade(81) == "excellent"
        assert _compute_grade(100) == "excellent"
