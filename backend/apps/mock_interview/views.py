"""
Mock Interview views.
"""
import random
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InterviewQuestion, InterviewSession, InterviewResponse
from .serializers import (
    InterviewQuestionSerializer,
    InterviewSessionSerializer,
    InterviewResponseSerializer,
    SubmitResponseSerializer,
)
from .evaluator import evaluate_response


class StartSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        domain = request.data.get("domain")
        difficulty = request.data.get("difficulty", "medium")

        if domain not in [d.value for d in InterviewQuestion.Domain]:
            return Response({"detail": "Invalid domain."}, status=400)

        # Get 5 random questions for the domain/difficulty
        questions = list(
            InterviewQuestion.objects.filter(domain=domain, difficulty=difficulty)
        )
        if len(questions) < 5:
            questions = list(InterviewQuestion.objects.filter(domain=domain))

        if not questions:
            return Response({"detail": "No questions found for this domain."}, status=404)

        questions = random.sample(questions, min(5, len(questions)))

        session = InterviewSession.objects.create(
            user=request.user, domain=domain, difficulty=difficulty
        )

        return Response({
            "session": InterviewSessionSerializer(session).data,
            "questions": InterviewQuestionSerializer(questions, many=True).data,
        }, status=status.HTTP_201_CREATED)


class SubmitResponseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = InterviewSession.objects.get(
                pk=session_id, user=request.user, status="in_progress"
            )
        except InterviewSession.DoesNotExist:
            return Response({"detail": "Session not found or already completed."}, status=404)

        serializer = SubmitResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_id = serializer.validated_data["question_id"]
        user_response = serializer.validated_data["user_response"]

        try:
            question = InterviewQuestion.objects.get(pk=question_id)
        except InterviewQuestion.DoesNotExist:
            return Response({"detail": "Question not found."}, status=404)

        result = evaluate_response(
            user_response,
            question.expected_keywords,
            question.model_answer,
        )

        response_obj = InterviewResponse.objects.create(
            session=session,
            question=question,
            user_response=user_response,
            score=result["score"],
            feedback=result["feedback"],
        )

        # Check if score < 60% → trigger follow-up
        follow_up = None
        if result["score"] < 60 and question.follow_up_questions:
            follow_up_text = random.choice(question.follow_up_questions)
            follow_up = {
                "question_text": follow_up_text,
                "is_follow_up": True,
            }

        return Response({
            "response": InterviewResponseSerializer(response_obj).data,
            "follow_up": follow_up,
        })


class CompleteSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = InterviewSession.objects.get(
                pk=session_id, user=request.user, status="in_progress"
            )
        except InterviewSession.DoesNotExist:
            return Response({"detail": "Session not found."}, status=404)

        responses = session.responses.all()
        if responses.exists():
            avg_score = sum(r.score for r in responses) / responses.count()
        else:
            avg_score = 0.0

        grade = _grade(avg_score)
        session.total_score = round(avg_score, 1)
        session.grade = grade
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()

        return Response(InterviewSessionSerializer(session).data)


class SessionDetailView(generics.RetrieveAPIView):
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user).prefetch_related("responses__question")


class SessionListView(generics.ListAPIView):
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user)


class GeneratePDFReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        from io import BytesIO
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet

        try:
            session = InterviewSession.objects.get(
                pk=session_id, user=request.user, status="completed"
            )
        except InterviewSession.DoesNotExist:
            return Response({"detail": "Completed session not found."}, status=404)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AI Mock Interview Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Domain: {session.domain.replace('_', ' ').title()}", styles["Normal"]))
        story.append(Paragraph(f"Difficulty: {session.difficulty.title()}", styles["Normal"]))
        story.append(Paragraph(f"Overall Score: {session.total_score:.1f}/100 ({session.grade.upper()})", styles["Normal"]))
        story.append(Spacer(1, 20))

        for i, resp in enumerate(session.responses.select_related("question").all(), 1):
            story.append(Paragraph(f"Q{i}: {resp.question.question_text}", styles["Heading3"]))
            story.append(Paragraph(f"Your Answer: {resp.user_response}", styles["Normal"]))
            story.append(Paragraph(f"Score: {resp.score:.1f}/100", styles["Normal"]))
            story.append(Paragraph(f"Feedback: {resp.feedback}", styles["Normal"]))
            story.append(Spacer(1, 12))

        doc.build(story)
        buffer.seek(0)
        return HttpResponse(
            buffer,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="interview_report_{session_id}.pdf"'},
        )


def _grade(score: float) -> str:
    if score <= 40:
        return "poor"
    elif score <= 60:
        return "average"
    elif score <= 80:
        return "good"
    return "excellent"
