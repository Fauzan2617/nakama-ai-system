import os
import uuid  # Untuk generate ID unik saat menyimpan dokumen ke ChromaDB
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# SDK baru Google Generative AI (menggantikan google-generativeai)
from google import genai

# --- IMPORT CHROMADB ---
import chromadb
# Documents  → tipe data list of string yang akan di-embed
# EmbeddingFunction → base class yang harus di-inherit untuk custom embedding
# Embeddings → tipe data hasil vektor (list of list of float)
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# ============================================================
# KONFIGURASI ENVIRONMENT & API KEY
# ============================================================

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan.")

# ============================================================
# INISIALISASI CLIENT GEMINI
# ============================================================

# Membuat satu client yang akan dipakai untuk semua request ke Gemini
# (generate teks maupun embedding)
client = genai.Client(api_key=GEMINI_API_KEY)

# ============================================================
# SETUP CHROMADB & CUSTOM EMBEDDING FUNCTION
# ============================================================

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function yang menghubungkan ChromaDB dengan Gemini.
    ChromaDB butuh fungsi ini untuk mengubah teks menjadi vektor angka
    sebelum disimpan atau dicari di database.
    """

    def __call__(self, input: Documents) -> Embeddings:
        # Memanggil Gemini Embedding API untuk mengubah teks jadi vektor
        # model "text-embedding-004" → model embedding terbaru dari Google
        response = client.models.embed_content(
            model="text-embedding-004", # <--- Hapus tulisan "models/"
            contents=input
        )
        # Ambil nilai vektor dari setiap embedding yang dikembalikan
        return [e.values for e in response.embeddings]

# Membuat koneksi ke ChromaDB dengan mode persistent (data tersimpan ke disk)
# path="./chroma_db" → folder penyimpanan database ada di dalam folder backend
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Mengambil collection yang sudah ada, atau membuat baru jika belum ada
# Collection di ChromaDB = seperti "tabel" di database biasa
collection = chroma_client.get_or_create_collection(
    name="nakama_knowledge_base",
    embedding_function=GeminiEmbeddingFunction()
)

# ============================================================
# INISIALISASI APLIKASI FASTAPI
# ============================================================

app = FastAPI(title="Nakama AI Core System")

# Konfigurasi CORS agar frontend bisa mengakses API dari browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Izinkan semua origin (ganti spesifik di production)
    allow_credentials=True,
    allow_methods=["*"],       # Izinkan semua HTTP method
    allow_headers=["*"],       # Izinkan semua header
)

# ============================================================
# SKEMA DATA
# ============================================================

# Validasi body request untuk endpoint chat
class ChatRequest(BaseModel):
    message: str  # Pesan teks dari user

# Validasi body request untuk endpoint ingest dokumen
class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}  # Opsional — bisa diisi sumber, tanggal, dll

# ============================================================
# ENDPOINT: CHAT BIASA (tanpa RAG)
# ============================================================

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Menerima pesan user → kirim langsung ke Gemini → kembalikan respons.
    Tidak membaca knowledge base, cocok untuk pertanyaan umum.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.message
        )
        return {"status": "success", "ai_response": response.text}
    except Exception as e:
        # Tangkap semua error (quota habis, koneksi gagal, dll)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINT: HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():
    """
    Mengecek apakah server berjalan normal.
    Bisa dipakai untuk monitoring atau ping awal dari frontend.
    """
    return {"status": "Server AI Berjalan Optimal!"}

# ============================================================
# ENDPOINT: INGEST DOKUMEN KE KNOWLEDGE BASE (RAG)
# ============================================================

@app.post("/api/rag/ingest")
async def ingest_document(request: IngestRequest):
    """
    Menyimpan teks ke ChromaDB sebagai bagian dari knowledge base.
    Teks akan otomatis diubah menjadi vektor oleh GeminiEmbeddingFunction.
    """
    try:
        # Membuat ID unik untuk setiap dokumen agar tidak tabrakan
        doc_id = str(uuid.uuid4())

        # Memasukkan teks ke dalam ChromaDB
        collection.add(
            documents=[request.text],
            metadatas=[request.metadata],
            ids=[doc_id]
        )
        return {
            "status": "success",
            "message": "Dokumen berhasil disimpan ke Knowledge Base",
            "doc_id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINT: CHAT RAG (Baca knowledge base dulu, baru jawab)
# ============================================================

@app.post("/api/rag/chat")
async def chat_with_rag(request: ChatRequest):
    """
    Alur RAG (Retrieval-Augmented Generation):
    1. Cari dokumen relevan di ChromaDB
    2. Gabungkan sebagai konteks
    3. Kirim ke Gemini bersama pertanyaan user
    4. Kembalikan jawaban yang berbasis dokumen internal
    """
    try:
        # 1. Mencari dokumen paling relevan di ChromaDB (Top 2 hasil)
        results = collection.query(
            query_texts=[request.message],
            n_results=2
        )

        # 2. Menggabungkan dokumen yang ditemukan menjadi satu konteks teks
        retrieved_docs = results['documents'][0]
        context = "\n\n".join(retrieved_docs) if retrieved_docs else "Tidak ada dokumen relevan."

        # 3. Merakit Prompt (Instruksi sistem + Konteks + Pertanyaan User)
        prompt = f"""
        Kamu adalah Asisten AI Internal Nakama Creative Lab. 
        Jawablah pertanyaan berikut HANYA berdasarkan konteks yang diberikan. 
        Jika jawaban tidak ada di dalam konteks, bilang saja "Saya tidak menemukan informasi tersebut di dokumen internal".

        KONTEKS DOKUMEN:
        {context}

        PERTANYAAN:
        {request.message}
        """

        # 4. Meminta Gemini menjawab berdasarkan Prompt yang sudah diperkaya konteks
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "status": "success",
            "ai_response": response.text,
            "retrieved_context": context  # Ditampilkan agar kita tahu apa yang dibaca AI
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))