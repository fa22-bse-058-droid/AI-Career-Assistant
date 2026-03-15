"""
FastAPI microservice for AI inference.
Provides endpoints for CV analysis and job matching using preloaded models.
"""
import logging
import re
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global model storage — loaded once at startup
_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI models at startup."""
    logger.info("Loading AI models...")
    try:
        from sentence_transformers import SentenceTransformer
        _models["sentence_transformer"] = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer loaded.")
    except Exception as e:
        logger.error("Failed to load SentenceTransformer: %s", e)

    try:
        from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
        model_name = "facebook/blenderbot-400M-distill"
        _models["chatbot_tokenizer"] = BlenderbotTokenizer.from_pretrained(model_name)
        _models["chatbot_model"] = BlenderbotForConditionalGeneration.from_pretrained(model_name)
        logger.info("BlenderBot loaded.")
    except Exception as e:
        logger.warning("BlenderBot not loaded (using fallback): %s", e)

    yield
    logger.info("Shutting down AI service.")


app = FastAPI(
    title="Career Platform AI Service",
    description="AI inference endpoints for CV analysis and job matching",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Request/Response Models ──────────────────────────────────────────────────

class EmbedRequest(BaseModel):
    texts: List[str]


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


class SimilarityRequest(BaseModel):
    text_a: str
    text_b: str


class SimilarityResponse(BaseModel):
    score: float


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    response: str


class CVDeepAnalysisRequest(BaseModel):
    cv_text: str


class CVDeepAnalysisResponse(BaseModel):
    ats_score: float
    keyword_score: float
    technical_depth_score: float
    impact_score: float
    readability_score: float
    overall_score: float
    grade: str
    ats_issues: List[str]
    missing_keywords: List[str]
    skill_gaps: List[str]
    strong_points: List[str]
    improvements: List[str]
    project_feedback: List[str]
    recruiter_verdict: str
    benchmark: str


# ── Deep CV Analysis Helpers ─────────────────────────────────────────────────

_ATS_SECTION_HEADERS = [
    "experience", "education", "skills", "projects", "certifications",
    "summary", "objective", "contact", "references", "publications",
    "awards", "languages", "volunteer", "work history", "employment",
]

_TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node", "django", "flask", "fastapi", "spring",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "linux",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "data analysis", "pandas", "numpy", "tableau", "power bi",
    "rest api", "graphql", "microservices", "ci/cd", "devops", "agile", "scrum",
    "html", "css", "sass", "tailwind", "bootstrap",
    "android", "ios", "flutter", "react native", "kotlin", "swift",
]

_IMPACT_VERBS = [
    "achieved", "built", "created", "designed", "developed", "delivered",
    "improved", "increased", "led", "managed", "optimized", "reduced",
    "launched", "implemented", "deployed", "architected", "engineered",
    "automated", "streamlined", "accelerated", "drove", "spearheaded",
]

_IMPORTANT_SKILLS = [
    "git", "docker", "sql", "rest api", "agile", "communication",
    "problem solving", "linux", "testing", "ci/cd", "aws",
    "python", "javascript", "java", "data structures", "algorithms",
]

_ATS_PROBLEMATIC = ["table", "<table", "column", "text box", "header:", "footer:"]


def _compute_ats_score(text: str) -> tuple[float, List[str]]:
    """Score ATS compatibility and return (score, issues list)."""
    lower = text.lower()
    issues: List[str] = []
    score = 100.0

    # Check standard sections
    found_sections = [h for h in _ATS_SECTION_HEADERS if h in lower]
    missing_critical = [h for h in ["experience", "education", "skills"] if h not in lower]
    if missing_critical:
        for sec in missing_critical:
            issues.append(f"Missing '{sec.title()}' section — required by ATS parsers")
            score -= 15

    # Check contact info
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.\w+", text))
    has_phone = bool(re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text))
    if not has_email:
        issues.append("No email address detected — ATS requires contact information")
        score -= 10
    if not has_phone:
        issues.append("No phone number detected — include a contact number")
        score -= 5

    # Check for dates
    has_dates = bool(re.search(r"\b(19|20)\d{2}\b", text))
    if not has_dates:
        issues.append("No employment dates found — ATS may not parse work history correctly")
        score -= 10

    # Warn about common ATS-breaking patterns
    ats_problematic_count = sum(1 for p in _ATS_PROBLEMATIC if p in lower)
    if ats_problematic_count:
        issues.append("Possible table/column layout detected — ATS parsers may misread columns")
        score -= 10

    if len(text) < 300:
        issues.append("CV text is very short — may not pass ATS keyword thresholds")
        score -= 20

    if len(text) > 8000:
        issues.append("CV may be too long — consider trimming to 1-2 pages for ATS")
        score -= 5

    return max(0.0, min(100.0, score)), issues


def _compute_keyword_score(text: str) -> tuple[float, List[str]]:
    """Score keyword density and return (score, missing_keywords)."""
    lower = text.lower()
    found = [kw for kw in _TECH_KEYWORDS if kw in lower]
    missing = [kw for kw in _TECH_KEYWORDS if kw not in lower]
    ratio = len(found) / len(_TECH_KEYWORDS)
    score = min(100.0, ratio * 200)  # generous scale
    return score, missing[:10]  # return top 10 missing


def _compute_technical_depth(text: str) -> float:
    """Score technical depth from 0-100."""
    lower = text.lower()
    score = 0.0

    # Count tech terms
    tech_count = sum(1 for kw in _TECH_KEYWORDS if kw in lower)
    score += min(50, tech_count * 2.5)

    # Years of experience mentions
    year_matches = re.findall(r"(\d+)\+?\s*years?", lower)
    total_years = sum(int(y) for y in year_matches if int(y) < 30)
    score += min(20, total_years * 3)

    # Presence of numbers/metrics in project/experience descriptions
    metrics = re.findall(r"\d+%|\d+x|\$\d+|\d+\s*users?|\d+\s*ms", lower)
    score += min(20, len(metrics) * 4)

    # Advanced concepts
    advanced = ["architecture", "scalab", "microservice", "distributed", "algorithm",
                "complexity", "optimization", "performance", "concurren", "async"]
    advanced_count = sum(1 for a in advanced if a in lower)
    score += min(10, advanced_count * 2)

    return min(100.0, score)


def _compute_impact_score(text: str) -> float:
    """Score impact/achievement language from 0-100."""
    lower = text.lower()
    score = 0.0

    # Action verbs
    verb_count = sum(1 for v in _IMPACT_VERBS if v in lower)
    score += min(50, verb_count * 5)

    # Quantifiable achievements
    numbers = re.findall(r"\b\d+[\d,.]*\s*(%|x|k|m|users?|clients?|ms|seconds?|hours?)\b", lower)
    score += min(30, len(numbers) * 6)

    # Result/outcome language
    result_words = ["result", "impact", "outcome", "saved", "increased", "reduced", "improved"]
    result_count = sum(1 for r in result_words if r in lower)
    score += min(20, result_count * 4)

    return min(100.0, score)


def _compute_readability_score(text: str) -> float:
    """Score readability/structure from 0-100."""
    score = 60.0  # base

    # Section organization — more sections = better structure
    lower = text.lower()
    section_count = sum(1 for h in _ATS_SECTION_HEADERS if h in lower)
    score += min(20, section_count * 3)

    # Bullet points
    bullet_count = text.count("•") + text.count("-") + text.count("*")
    if bullet_count >= 5:
        score += 10
    elif bullet_count == 0:
        score -= 10

    # Consistent line lengths (not walls of text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    long_lines = sum(1 for l in lines if len(l) > 200)
    if long_lines > 3:
        score -= 10

    return max(0.0, min(100.0, score))


def _detect_skill_gaps(text: str) -> List[str]:
    """Detect important missing skills."""
    lower = text.lower()
    return [s for s in _IMPORTANT_SKILLS if s not in lower]


def _detect_strong_points(text: str, keyword_score: float, impact_score: float) -> List[str]:
    """Identify strong points from the CV."""
    lower = text.lower()
    points: List[str] = []

    if keyword_score >= 50:
        points.append("Good range of technical skills and keywords")
    if impact_score >= 40:
        points.append("Uses achievement-oriented language with measurable outcomes")
    if re.search(r"[\w.+-]+@[\w-]+\.\w+", text):
        points.append("Contact information is clearly presented")
    if "project" in lower or "github" in lower or "portfolio" in lower:
        points.append("Includes projects section demonstrating practical experience")
    if re.search(r"(b\.?s\.?|m\.?s\.?|bachelor|master|phd|degree)", lower):
        points.append("Educational qualifications are mentioned")
    if any(cert in lower for cert in ["certified", "certification", "aws ", "google ", "microsoft "]):
        points.append("Has professional certifications which boosts credibility")
    if sum(1 for v in _IMPACT_VERBS if v in lower) >= 5:
        points.append("Strong use of action verbs throughout the CV")

    return points or ["CV submitted for analysis — add more detail for stronger points"]


def _generate_improvements(
    text: str, ats_score: float, keyword_score: float,
    impact_score: float, technical_score: float,
) -> List[str]:
    """Generate actionable improvement suggestions."""
    lower = text.lower()
    improvements: List[str] = []

    if ats_score < 70:
        improvements.append("Add clear section headers: Experience, Education, Skills, Projects")
    if keyword_score < 50:
        improvements.append("Incorporate more industry-specific keywords relevant to your target role")
    if impact_score < 40:
        improvements.append("Rewrite bullet points using action verbs: 'Developed', 'Reduced', 'Increased'")
        improvements.append("Quantify achievements with numbers (e.g., 'improved speed by 30%')")
    if technical_score < 40:
        improvements.append("Expand technical skills section with specific tools and technologies used")
    if "summary" not in lower and "objective" not in lower:
        improvements.append("Add a professional summary or objective at the top of the CV")
    if "github" not in lower and "portfolio" not in lower and "linkedin" not in lower:
        improvements.append("Include links to your GitHub, portfolio, or LinkedIn profile")
    if not re.search(r"(\d+)\s*years?", lower):
        improvements.append("Mention years of experience for each role to provide context")

    return improvements or ["Keep CV format clean and ensure all sections are up to date"]


def _generate_project_feedback(text: str) -> List[str]:
    """Provide feedback on the projects section."""
    lower = text.lower()
    feedback: List[str] = []

    has_projects = "project" in lower
    if not has_projects:
        feedback.append("No dedicated Projects section found — add personal or academic projects")
        feedback.append("Side projects on GitHub significantly improve your candidacy")
        return feedback

    if "github" not in lower and "gitlab" not in lower:
        feedback.append("Link project names to GitHub/GitLab repositories")
    if not re.search(r"\d+%|\d+x|\d+\s*users?", lower):
        feedback.append("Describe project scale/impact with metrics (e.g., '1000+ users', '50% faster')")
    if "stack" not in lower and "built with" not in lower:
        feedback.append("Mention the tech stack used in each project clearly")

    tech_count = sum(1 for kw in _TECH_KEYWORDS if kw in lower)
    if tech_count >= 5:
        feedback.append("Good variety of technologies mentioned across projects")

    return feedback or ["Projects section looks solid — consider adding deployment links"]


def _generate_verdict_and_benchmark(
    overall: float, grade: str, text: str
) -> tuple[str, str]:
    """Generate recruiter verdict and company benchmark."""
    lower = text.lower()
    name_guess = "the candidate"

    if grade == "Excellent":
        verdict = (
            f"This is a strong CV. {name_guess.title()} demonstrates relevant technical skills, "
            "quantified achievements, and a well-structured presentation. Likely to pass ATS "
            "filters and attract recruiter attention for mid-to-senior roles."
        )
        benchmark = (
            "Meets or exceeds the standards expected at top Pakistani tech companies such as "
            "Systems Ltd, Arbisoft, and 10Pearls. Competitive for multinational corporations "
            "operating in Pakistan."
        )
    elif grade == "Good":
        verdict = (
            "A solid CV with good technical coverage. Some improvements in quantifiable impact "
            "and keyword optimization would strengthen it further. Suitable for most mid-level "
            "roles at established Pakistani tech firms."
        )
        benchmark = (
            "Meets baseline requirements for companies like Systems Ltd and Arbisoft but may "
            "need refinement to stand out at highly competitive employers or multinationals."
        )
    elif grade == "Average":
        verdict = (
            "The CV has foundational elements but lacks depth in technical detail and measurable "
            "impact. Recruiters may pass over it without clearer evidence of experience and skills."
        )
        benchmark = (
            "Below the typical bar for Systems Ltd and Arbisoft's technical hiring. "
            "Significant improvements to keywords, structure, and achievement descriptions "
            "are recommended before applying to top-tier companies."
        )
    else:
        verdict = (
            "This CV needs substantial work. It is likely to be filtered out by ATS systems "
            "and would not attract recruiter attention in its current form."
        )
        benchmark = (
            "Does not yet meet the minimum standards expected at Systems Ltd, Arbisoft, or "
            "similar companies. A complete rewrite following modern CV best practices is advised."
        )

    return verdict, benchmark


def _analyze_cv(cv_text: str) -> dict:
    """
    Perform deep CV analysis using rule-based NLP.
    Returns a dict matching CVDeepAnalysisResponse schema.
    """
    ats_score, ats_issues = _compute_ats_score(cv_text)
    keyword_score, missing_keywords = _compute_keyword_score(cv_text)
    technical_depth_score = _compute_technical_depth(cv_text)
    impact_score = _compute_impact_score(cv_text)
    readability_score = _compute_readability_score(cv_text)

    overall_score = round(
        ats_score * 0.25
        + keyword_score * 0.25
        + technical_depth_score * 0.20
        + impact_score * 0.15
        + readability_score * 0.15,
        1,
    )

    if overall_score <= 40:
        grade = "Poor"
    elif overall_score <= 60:
        grade = "Average"
    elif overall_score <= 80:
        grade = "Good"
    else:
        grade = "Excellent"

    skill_gaps = _detect_skill_gaps(cv_text)
    strong_points = _detect_strong_points(cv_text, keyword_score, impact_score)
    improvements = _generate_improvements(
        cv_text, ats_score, keyword_score, impact_score, technical_depth_score
    )
    project_feedback = _generate_project_feedback(cv_text)
    recruiter_verdict, benchmark = _generate_verdict_and_benchmark(
        overall_score, grade, cv_text
    )

    return {
        "ats_score": round(ats_score, 1),
        "keyword_score": round(keyword_score, 1),
        "technical_depth_score": round(technical_depth_score, 1),
        "impact_score": round(impact_score, 1),
        "readability_score": round(readability_score, 1),
        "overall_score": overall_score,
        "grade": grade,
        "ats_issues": ats_issues,
        "missing_keywords": missing_keywords,
        "skill_gaps": skill_gaps,
        "strong_points": strong_points,
        "improvements": improvements,
        "project_feedback": project_feedback,
        "recruiter_verdict": recruiter_verdict,
        "benchmark": benchmark,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "models_loaded": list(_models.keys()),
    }


@app.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """Generate sentence embeddings for a list of texts."""
    model = _models.get("sentence_transformer")
    if not model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded.")
    try:
        embeddings = model.encode(request.texts).tolist()
        return EmbedResponse(embeddings=embeddings)
    except Exception as e:
        logger.error("Embedding failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity", response_model=SimilarityResponse)
async def compute_similarity(request: SimilarityRequest):
    """Compute cosine similarity between two texts."""
    model = _models.get("sentence_transformer")
    if not model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded.")
    try:
        from sentence_transformers import util
        emb_a = model.encode(request.text_a, convert_to_tensor=True)
        emb_b = model.encode(request.text_b, convert_to_tensor=True)
        score = float(util.cos_sim(emb_a, emb_b)[0][0])
        return SimilarityResponse(score=score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Generate a chatbot response."""
    tokenizer = _models.get("chatbot_tokenizer")
    model = _models.get("chatbot_model")

    if not tokenizer or not model:
        return ChatResponse(
            response=(
                "I'm CareerBot! I can help with job searching, CV tips, "
                "and interview preparation."
            )
        )

    try:
        import torch
        context = ""
        for turn in request.history[-5:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            context += f"{'Person' if role == 'user' else 'Bot'}: {content}\n"
        full_input = f"{context}Person: {request.message}\nBot:"

        inputs = tokenizer(
            [full_input[:512]], return_tensors="pt", truncation=True, max_length=512
        )
        with torch.no_grad():
            reply_ids = model.generate(**inputs, max_new_tokens=200)
        response_text = tokenizer.decode(reply_ids[0], skip_special_tokens=True)
        return ChatResponse(response=response_text.strip())
    except Exception as e:
        logger.error("Chat generation failed: %s", e)
        return ChatResponse(response="Sorry, I couldn't process that. Please try again.")


@app.post("/analyze-cv-deep", response_model=CVDeepAnalysisResponse)
async def analyze_cv_deep(request: CVDeepAnalysisRequest):
    """
    Deep ATS analysis of a CV.

    Accepts extracted CV text and returns a structured JSON report covering
    ATS compatibility, keyword coverage, technical depth, impact language,
    readability, skill gaps, and recruiter-level feedback.
    """
    if not request.cv_text or not request.cv_text.strip():
        raise HTTPException(status_code=400, detail="cv_text must not be empty.")
    try:
        result = _analyze_cv(request.cv_text)
        return CVDeepAnalysisResponse(**result)
    except Exception as e:
        logger.error("Deep CV analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
