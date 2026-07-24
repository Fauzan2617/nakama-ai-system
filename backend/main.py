import os
import uuid
import traceback
import glob

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import chromadb
from google import genai

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

from database import engine, Base, get_db
import models
from models import ChatHistory

# Buat tabel di PostgreSQL jika belum ada
models.Base.metadata.create_all(bind=engine)

# ============================================================
# LOAD ENV
# ============================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY tidak ditemukan pada file .env")

# Satu client untuk semua request ke Gemini
client = genai.Client(api_key=API_KEY)

# ============================================================
# KONSTANTA MODEL
# ============================================================

CHAT_MODEL = "gemini-flash-latest"
EMBEDDING_MODEL = "gemini-embedding-001"

# ============================================================
# HELPER: EMBEDDING MANUAL
# ============================================================

def get_embedding(text: str) -> list:
    """
    Mengubah satu teks menjadi vektor menggunakan Gemini Embedding API.
    Dipanggil manual (tidak lewat ChromaDB EmbeddingFunction) untuk
    menghindari konflik versi API v1beta yang dipakai ChromaDB secara internal.
    """
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return response.embeddings[0].values

# ============================================================
# CHROMADB (tanpa embedding_function)
# ============================================================

chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Collection dibuat TANPA embedding_function — kita kirim vektor secara manual
# Jika ada chroma_db lama dari versi sebelumnya, hapus foldernya dulu
# lalu ingest ulang data
collection = chroma_client.get_or_create_collection(
    name="nakama_knowledge_base"
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
# REQUEST SCHEMAS
# ============================================================

class ChatRequest(BaseModel):
    message: str

class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "success",
        "message": "Backend berjalan dengan baik."
    }

# ============================================================
# SINKRONISASI DATA FOLDER
# ============================================================

@app.post("/api/rag/sync-folder")
async def sync_folder():
    """
    Baca semua file .txt di folder 'data/', pecah per paragraf (chunking),
    embed manual, lalu simpan ke ChromaDB.
    """
    try:
        folder_path = "./data"

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return {
                "status": "info",
                "message": "Folder 'data/' baru saja dibuat. Silakan isi dengan file .txt dan jalankan ulang API ini."
            }

        txt_files = glob.glob(f"{folder_path}/*.txt")

        if not txt_files:
            return {
                "status": "info",
                "message": "Tidak ada file .txt yang ditemukan di dalam folder 'data/'."
            }

        count = 0
        for file_path in txt_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

                # Chunking sederhana: pecah per paragraf kosong
                chunks = text.split('\n\n')

                for chunk in chunks:
                    chunk = chunk.strip()
                    if chunk:
                        doc_id = str(uuid.uuid4())

                        # Embed chunk secara manual sebelum dikirim ke ChromaDB
                        embedding = get_embedding(chunk)

                        collection.add(
                            ids=[doc_id],
                            documents=[chunk],
                            embeddings=[embedding],
                            metadatas=[{"source": os.path.basename(file_path)}]
                        )
                        count += 1

        return {
            "status": "success",
            "message": f"Selesai! Berhasil memasukkan {count} potongan informasi dari {len(txt_files)} file teks ke dalam knowledge base."
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# INGEST DOKUMEN (SATUAN)
# ============================================================

@app.post("/api/rag/ingest")
async def ingest(request: IngestRequest):
    try:
        doc_id = str(uuid.uuid4())

        # Embed teks secara manual
        embedding = get_embedding(request.text)

        collection.add(
            ids=[doc_id],
            documents=[request.text],
            embeddings=[embedding],
            metadatas=[request.metadata]
        )

        return {
            "status": "success",
            "message": "Dokumen satuan berhasil disimpan.",
            "doc_id": doc_id
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# CHAT RAG (DENGAN POSTGRESQL MEMORY & DOKTRIN)
# ============================================================

@app.post("/api/rag/chat")
async def rag_chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. Embed pertanyaan user secara manual
        query_embedding = get_embedding(request.message)

        # 2. Cari dokumen relevan di ChromaDB menggunakan vektor
        #    query_embeddings (bukan query_texts) agar tidak trigger EmbeddingFunction
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        documents = results.get("documents", [])

        # 3. Cek apakah knowledge base kosong
        if len(documents) == 0 or len(documents[0]) == 0:
            final_response = "Maaf, knowledge base Nakama saat ini masih kosong. Tolong minta admin untuk memasukkan data terlebih dahulu."
            context = "Tidak ada dokumen."

        else:
            # 4. Gabungkan dokumen yang ditemukan menjadi satu blok konteks
            context = "\n\n".join(documents[0])

            # 5. Rakit prompt dengan doktrin Nakama AI
            prompt = f"""
Kamu adalah Nakama AI, asisten virtual cerdas, profesional, dan ramah yang diciptakan khusus untuk membantu tim internal Nakama Creative Lab. 
Tugas utamamu adalah memberikan informasi yang akurat secara eksklusif berdasarkan dokumen perusahaan.

Aturan ketat yang WAJIB kamu patuhi:
1. Jawablah SELALU menggunakan bahasa Indonesia yang ramah, asik, dan mudah dipahami selayaknya rekan kerja.
2. Gunakan HANYA informasi dari [KONTEKS] di bawah ini untuk menjawab pertanyaan.
3. Jika [KONTEKS] tidak membahas jawaban dari pertanyaan, JANGAN MENGARANG JAWABAN ATAU MENGAMBIL DARI INTERNET. Cukup balas: "Maaf, informasi tersebut belum ada di knowledge base Nakama saat ini."
4. Jika pengguna hanya menyapa (contoh: "halo", "hai"), balaslah dengan ramah dan tanyakan apa yang bisa dibantu hari ini.

================================
[KONTEKS]
{context}
================================

Pertanyaan dari tim: {request.message}
Jawaban Nakama AI:
"""
            # 6. Generate jawaban dari Gemini berdasarkan prompt doktrin
            response = client.models.generate_content(
                model=CHAT_MODEL,
                contents=prompt
            )
            final_response = response.text

        # 7. Simpan riwayat chat ke PostgreSQL
        new_chat = ChatHistory(
            session_id="test-session-001",
            user_message=request.message,
            ai_response=final_response
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)

        return {
            "status": "success",
            "response": final_response,
            "context": context
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
# ============================================================
# CEK MODEL YANG TERSEDIA
# ============================================================

@app.get("/api/models")
async def get_available_models():
    """
    Endpoint ini digunakan untuk mengecek nama-nama model Gemini 
    apa saja yang tersedia dan didukung oleh API Key kamu saat ini.
    """
    try:
        # Mengambil daftar semua model dari Google GenAI
        models_list = client.models.list()
        
        # Mengekstrak namanya saja agar mudah dibaca
        available_models = [m.name for m in models_list]
        
        return {
            "status": "success",
            "total_models": len(available_models),
            "models": available_models
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))