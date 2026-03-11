"""
Mock Interview serializers.
"""
from rest_framework import serializers
from .models import InterviewQuestion, InterviewSession, InterviewResponse


class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = ["id", "domain", "difficulty", "question_text", "follow_up_questions"]


class InterviewResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text", read_only=True)

    class Meta:
        model = InterviewResponse
        fields = [
            "id", "question", "question_text", "user_response",
            "score", "feedback", "is_follow_up", "created_at",
        ]
        read_only_fields = ["id", "score", "feedback", "created_at"]


class InterviewSessionSerializer(serializers.ModelSerializer):
    responses = InterviewResponseSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            "id", "domain", "difficulty", "total_score", "grade",
            "status", "started_at", "completed_at", "responses",
        ]
        read_only_fields = ["id", "total_score", "grade", "status", "started_at", "completed_at"]


class SubmitResponseSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    user_response = serializers.CharField(min_length=10, max_length=5000)
