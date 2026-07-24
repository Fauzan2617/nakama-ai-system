# 🚀 Nakama AI Assistant

> An End-to-End Retrieval-Augmented Generation (RAG) Chatbot System built for team collaboration and operational support, powered by FastAPI, PostgreSQL, ChromaDB, and Google Gemini AI.

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, SQLAlchemy, Uvicorn, Google GenAI SDK
* **Database:** PostgreSQL
* **Vector Store:** ChromaDB
* **Frontend:** Modern Web UI (Containerized)
* **Infrastructure:** Docker & Docker Compose

---

## ✨ Features

* **Intelligent RAG Chat:** Context-aware responses built upon custom internal documents and standard operational guidelines.
* **RESTful API Architecture:** Fully documented endpoints via FastAPI Swagger UI.
* **Database Persistence:** Robust relational data storage managed with PostgreSQL and SQLAlchemy.
* **Containerized Environment:** Seamless multi-container deployment using Docker Compose for zero-friction setup.

---

## 📂 Project Structure

```text
nakama-ai-system/
├── backend/
│   ├── database.py       # PostgreSQL SQLAlchemy connection setup
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # Database models
│   └── ...               # Routers, schemas, and RAG logic
├── frontend/             # Frontend UI service
├── docker-compose.yml    # Multi-container orchestration setup
└── README.md
⚙️ Prerequisites
Pastikan di komputermu sudah terinstal:

Docker & Docker Compose

Git

🚀 Installation & Running Locally
Ikuti langkah-langkah di bawah ini untuk menjalankan proyek secara lokal di komputermu:

Clone repository ini:

Bash
git clone [https://github.com/username/nakama-ai-system.git](https://github.com/username/nakama-ai-system.git)
cd nakama-ai-system
Konfigurasi Environment Variables:
Buat file .env di dalam folder backend/ atau sesuaikan variabel lingkungan di dalam docker-compose.yml (seperti konfigurasi database dan API Key Gemini).

Jalankan aplikasi menggunakan Docker Compose:

Bash
docker-compose up -d --build
Akses Aplikasi:

Frontend UI: Buka browser dan akses http://localhost:7860

Backend API Docs (Swagger): Buka http://localhost:8000/docs

🔍 API Health Check
Kamu bisa memverifikasi kesehatan server backend secara langsung dengan mengakses endpoint berikut melalui browser atau tool API:

GET /health -> Memastikan layanan backend berjalan dengan baik.
