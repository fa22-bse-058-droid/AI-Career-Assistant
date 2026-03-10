from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import cv_analyzer, chatbot, mock_interview

app = FastAPI(
    title="AI Career Assistant – ML Service",
    description="FastAPI service for AI/ML features: CV analysis, chatbot, mock interviews.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cv_analyzer.router, prefix="/cv", tags=["CV Analyzer"])
app.include_router(chatbot.router, prefix="/chat", tags=["Chatbot"])
app.include_router(mock_interview.router, prefix="/interview", tags=["Mock Interview"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
