from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class InterviewRequest(BaseModel):
    job_role: str
    difficulty: str = "medium"
    num_questions: int = 5


@router.post("/generate")
async def generate_questions(request: InterviewRequest):
    """Generate mock interview questions for a given job role."""
    return {
        "job_role": request.job_role,
        "difficulty": request.difficulty,
        "questions": ["Mock question endpoint – integrate OpenAI here"],
    }
