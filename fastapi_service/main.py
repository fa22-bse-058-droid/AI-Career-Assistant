"""
FastAPI microservice for AI inference.
Provides endpoints for CV analysis and job matching using preloaded models.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
