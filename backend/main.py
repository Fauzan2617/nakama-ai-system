import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# ============================================================
# KONFIGURASI ENVIRONMENT & API KEY
# ============================================================

# Membaca file .env dan memuat variabel ke os.environ
load_dotenv()

# Mengambil API key Gemini dari environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validasi awal — hentikan server jika API key tidak ditemukan
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan. Pastikan file .env sudah diisi.")

# ============================================================
# INISIALISASI MODEL AI (GEMINI)
# ============================================================

# Menghubungkan SDK Google Generative AI dengan API key yang sudah dimuat
genai.configure(api_key=GEMINI_API_KEY)

# Memilih model Gemini yang akan digunakan sebagai AI engine
# gemini-1.5-flash → versi cepat dan ringan, cocok untuk chat real-time
model = genai.GenerativeModel('gemini-1.5-flash')

# ============================================================
# INISIALISASI APLIKASI FASTAPI
# ============================================================

# Membuat instance aplikasi FastAPI dengan nama/title untuk dokumentasi Swagger
app = FastAPI(title="Nakama AI Core System")

# ============================================================
# KONFIGURASI CORS (Cross-Origin Resource Sharing)
# ============================================================

# Mengizinkan frontend (browser) dari domain mana pun mengakses API ini
# allow_origins=["*"]      → semua domain diizinkan (ubah ke domain spesifik di production)
# allow_credentials=True   → mengizinkan pengiriman cookie/auth header lintas domain
# allow_methods=["*"]      → semua HTTP method diizinkan (GET, POST, PUT, DELETE, dll)
# allow_headers=["*"]      → semua request header diizinkan
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SKEMA DATA (REQUEST BODY)
# ============================================================

# Model Pydantic untuk validasi body request POST /api/chat
# FastAPI akan otomatis return 422 jika field 'message' tidak ada atau bukan string
class ChatRequest(BaseModel):
    message: str  # Pesan teks yang dikirim user ke AI

# ============================================================
# ENDPOINT: CHAT DENGAN AI
# ============================================================

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Menerima pesan dari user, meneruskannya ke Gemini AI,
    lalu mengembalikan respons AI ke client.
    """
    try:
        # Kirim pesan user ke model Gemini dan tunggu responsnya
        response = model.generate_content(request.message)

        # Kembalikan respons dalam format JSON terstruktur
        return {
            "status": "success",
            "user_message": request.message,   # Echo balik pesan user
            "ai_response": response.text        # Teks respons dari Gemini
        }
    except Exception as e:
        # Jika terjadi error (misal: API key invalid, quota habis, dll),
        # kembalikan HTTP 500 dengan detail errornya
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ENDPOINT: HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():
    """
    Endpoint sederhana untuk mengecek apakah server berjalan dengan baik.
    Biasa dipakai oleh load balancer, monitoring tools, atau saat awal development.
    """
    return {"status": "Server AI Berjalan Optimal!"}