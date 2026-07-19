import os
import uuid
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from google import genai

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
from database import engine, Base, get_db
import models
from models import ChatHistory

# Perintah untuk membuat tabel di PostgreSQL jika belum ada
models.Base.metadata.create_all(bind=engine)

# ============================================================
# LOAD ENV
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY tidak ditemukan pada file .env")

client = genai.Client(api_key=API_KEY)

# ============================================================
# MODEL
# ============================================================

CHAT_MODEL = "gemini-flash-latest"
EMBEDDING_MODEL = "gemini-embedding-001"

# ============================================================
# CHROMADB EMBEDDING
# ============================================================

class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

# ============================================================
# CHROMADB
# ============================================================

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name="nakama_knowledge_base",
    embedding_function=GeminiEmbeddingFunction()
)

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Nakama AI Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REQUEST
# ============================================================

class ChatRequest(BaseModel):
    message: str

class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}

# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "success",
        "message": "Backend berjalan."
    }

# ============================================================
# LIST MODEL
# ============================================================

@app.get("/models")
async def models():
    try:
        result = []
        for model in client.models.list():
            result.append(model.name)
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ============================================================
# CHAT BIASA
# ============================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=request.message
        )
        return {
            "status": "success",
            "response": response.text
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ============================================================
# INGEST DOKUMEN
# ============================================================

@app.post("/api/rag/ingest")
async def ingest(request: IngestRequest):
    try:
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            documents=[request.text],
            metadatas=[request.metadata]
        )
        return {
            "status": "success",
            "message": "Dokumen berhasil disimpan.",
            "doc_id": doc_id
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ============================================================
# CHAT RAG (DENGAN POSTGRESQL MEMORY)
# ============================================================

@app.post("/api/rag/chat")
async def rag_chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        results = collection.query(
            query_texts=[request.message],
            n_results=3
        )

        documents = results.get("documents", [])

        if len(documents) == 0 or len(documents[0]) == 0:
            context = "Tidak ada dokumen relevan."
        else:
            context = "\n\n".join(documents[0])

        prompt = f"""
Kamu adalah AI Assistant milik Nakama Creative Lab.

Jawab pertanyaan hanya berdasarkan konteks berikut.

Jika jawaban tidak ada pada konteks maka jawab:

"Saya tidak menemukan informasi tersebut pada knowledge base."

================================

KONTEKS

{context}

================================

PERTANYAAN

{request.message}
"""

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )
        
        # --- MENYIMPAN RIWAYAT KE POSTGRESQL ---
        new_chat = ChatHistory(
            session_id="test-session-001",
            user_message=request.message,
            ai_response=response.text
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        # ---------------------------------------

        return {
            "status": "success",
            "response": response.text,
            "context": context
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ============================================================
# AMBIL RIWAYAT CHAT (DARI POSTGRESQL)
# ============================================================

@app.get("/api/rag/history")
async def get_chat_history(db: Session = Depends(get_db)):
    try:
        histories = db.query(ChatHistory).all()
        return histories
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )