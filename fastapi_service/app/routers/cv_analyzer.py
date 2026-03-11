from fastapi import APIRouter, UploadFile, File

router = APIRouter()


@router.post("/analyze")
async def analyze_cv(file: UploadFile = File(...)):
    """Analyze an uploaded CV file and return structured feedback."""
    return {
        "message": "CV analysis endpoint – integrate OpenAI here",
        "filename": file.filename,
    }
