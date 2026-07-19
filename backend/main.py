from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Inisialisasi Aplikasi FastAPI
app = FastAPI(title="Nakama AI Core System")

# Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint Health Check
@app.get("/health")
async def health_check():
    return {"status": "Server AI Berjalan Optimal!"}