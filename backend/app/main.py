import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, StringConstraints

from app.agent.agent import run_agent
from app.agent.schema import FinalAnswer

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "logs"

logger = logging.getLogger(__name__)

# session_id -> messages list. Kept in memory, so it is lost when the server restarts.
SESSIONS = {}


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"api_{datetime.now():%Y-%m-%d_%H-%M-%S}.log"
    logging.basicConfig(
        filename=log_path,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # The SDK's HTTP library logs every request at INFO; keep only its warnings.
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    return log_path


@asynccontextmanager
async def lifespan(app):
    # Runs once when the server starts (not when tests import this file).
    load_dotenv(ROOT / ".env")
    setup_logging()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    # Empty or whitespace-only messages fail validation, so FastAPI returns 422.
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    session_id: str | None = None


class ChatResponse(FinalAnswer):
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id
    if session_id not in SESSIONS:
        session_id = str(uuid4())

    # A new list, so a failed run does not leave half a turn in the stored history.
    messages = SESSIONS.get(session_id, []) + [{"role": "user", "content": request.message}]
    try:
        final, messages = run_agent(messages)
    except Exception as error:
        logger.error("Agent failed for session %s: %s", session_id, error)
        raise HTTPException(status_code=502, detail="The agent could not answer this question.")

    SESSIONS[session_id] = messages
    return ChatResponse(session_id=session_id, **final)
