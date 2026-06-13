"""
Backend API Server (server.py)
-----------------------------
Exposes REST HTTP endpoints for the React frontend dashboard.
Integrates directly with the validated IngestionOrchestrator pipeline.
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from pipeline.orchestrator import IngestionOrchestrator

load_dotenv()

app = FastAPI(title="NoteTaker AI Pipeline Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
LLM_KEY = os.getenv("GROQ_API_KEY", "")

orchestrator = IngestionOrchestrator(
    asset_dir="./assets",
    db_path="./notebooklm.db",
    chroma_dir="./chroma_db",
    gemini_api_key=GEMINI_KEY,
    llm_provider=LLM_PROVIDER,
    llm_api_key=LLM_KEY
)

os.makedirs("./assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="./assets"), name="assets")


@app.post("/api/ingest")
async def api_ingest(file: UploadFile = File(...)):
    """
    Receives incoming file drops from the frontend drag-and-drop workspace
    and feeds them directly into the processing workers pipeline.
    """
    os.makedirs("./temp_uploads", exist_ok=True)
    temp_path = os.path.join("./temp_uploads", file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        summary = orchestrator.ingest(temp_path)
        return summary
        
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


class GenerationRequest(BaseModel):
    query: str
    mode: str


@app.post("/api/generate")
async def api_generate(payload: GenerationRequest):
    """
    Triggers Chroma DB semantic index matching queries and routes
    context slices out to the generative inference providers.
    """
    try:
        if payload.mode == "quiz":
            result = orchestrator.generate_quiz(payload.query)
        else:
            result = orchestrator.generate_notes(payload.query)
            
        return {"result": result}
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))