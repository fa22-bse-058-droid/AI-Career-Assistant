"""
Interview evaluation engine using keyword matching + MiniLM semantic similarity.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# Lazy singleton — loaded once on first use
_sentence_model = None


def _get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.error("Failed to load SentenceTransformer: %s", e)
    return _sentence_model


def evaluate_response(
    user_response: str,
    expected_keywords: List[str],
    model_answer: str,
    keyword_weight: float = 0.40,
    semantic_weight: float = 0.60,
) -> dict:
    """
    Score a user's interview response (0-100):
      - 40% keyword matching
      - 60% MiniLM semantic similarity vs model answer
    """
    # Keyword matching
    response_lower = user_response.lower()
    if expected_keywords:
        matched = sum(
            1 for kw in expected_keywords if kw.lower() in response_lower
        )
        keyword_score = min(100.0, (matched / len(expected_keywords)) * 100.0)
    else:
        keyword_score = 50.0

    # Semantic similarity
    try:
        model = _get_sentence_model()
        if model is None:
            raise RuntimeError("Sentence model not available")
        from sentence_transformers import util
        user_emb = model.encode(user_response, convert_to_tensor=True)
        answer_emb = model.encode(model_answer, convert_to_tensor=True)
        semantic_score = float(util.cos_sim(user_emb, answer_emb)[0][0]) * 100.0
    except Exception as e:
        logger.warning("Semantic scoring failed, using keyword only: %s", e)
        semantic_score = keyword_score

    total_score = keyword_weight * keyword_score + semantic_weight * semantic_score

    # Generate feedback
    grade = _compute_grade(total_score)
    feedback = _generate_feedback(total_score, grade, expected_keywords, response_lower)

    return {
        "score": round(total_score, 1),
        "keyword_score": round(keyword_score, 1),
        "semantic_score": round(semantic_score, 1),
        "grade": grade,
        "feedback": feedback,
    }


def _compute_grade(score: float) -> str:
    if score <= 40:
        return "poor"
    elif score <= 60:
        return "average"
    elif score <= 80:
        return "good"
    return "excellent"


def _generate_feedback(score: float, grade: str, expected_keywords: list, response_lower: str) -> str:
    missing = [kw for kw in expected_keywords if kw.lower() not in response_lower]
    feedback_parts = []

    if grade == "excellent":
        feedback_parts.append("Excellent answer! You covered the key concepts well.")
    elif grade == "good":
        feedback_parts.append("Good answer! A few more details would make it stronger.")
    elif grade == "average":
        feedback_parts.append("Average response. Try to be more specific and comprehensive.")
    else:
        feedback_parts.append("Your answer needs improvement. Review the topic carefully.")

    if missing:
        feedback_parts.append(
            f"Consider including these key points: {', '.join(missing[:5])}."
        )

    return " ".join(feedback_parts)
