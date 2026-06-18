from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import load_environment
from app.api.chat import router as chat_router

load_environment()

app = FastAPI(title="MentorFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "mentorflow"}
