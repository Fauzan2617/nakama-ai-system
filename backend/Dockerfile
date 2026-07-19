# ============================================================
# BASE IMAGE
# ============================================================

# Gunakan Python 3.10 versi slim (tanpa package OS yang tidak perlu)
# slim dipilih karena ukurannya jauh lebih kecil dari versi full (~50MB vs ~900MB)
# tapi tetap cukup untuk menjalankan aplikasi Python production
FROM python:3.10-slim

# ============================================================
# WORKING DIRECTORY
# ============================================================

# Set direktori kerja di dalam container
# Semua perintah berikutnya (COPY, RUN, CMD) akan dijalankan relatif dari /app
# Jika folder /app belum ada, Docker akan membuatnya otomatis
WORKDIR /app

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

# Install dependensi sistem yang dibutuhkan sebelum install library Python
# build-essential → menyediakan gcc dan tools kompilasi C/C++,
#   dibutuhkan oleh beberapa library Python yang punya ekstensi native
#   seperti ChromaDB, numpy, onnxruntime
#
# apt-get update         → refresh daftar package dari repository
# apt-get install -y     → install tanpa prompt konfirmasi (-y = yes to all)
# rm -rf /var/lib/apt/lists/* → hapus cache apt setelah install
#   ini penting untuk menjaga ukuran image tetap kecil
#   karena cache apt tidak dibutuhkan saat container berjalan
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

# Copy requirements.txt SEBELUM meng-copy seluruh kode
# Ini memanfaatkan Docker layer caching:
# → Jika requirements.txt tidak berubah, Docker akan skip langkah instalasi
#   dan langsung pakai layer yang sudah di-cache dari build sebelumnya
# → Proses build jadi jauh lebih cepat saat kode berubah tapi dependency tidak
COPY requirements.txt .

# Install semua library Python yang ada di requirements.txt
# --no-cache-dir → tidak menyimpan cache pip di dalam image
#   ini mengurangi ukuran image final secara signifikan
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# APPLICATION CODE
# ============================================================

# Copy seluruh isi folder backend (kode, .env, dll) ke dalam container
# Dilakukan SETELAH install dependency agar perubahan kode tidak
# membatalkan cache layer instalasi library di atas
# Catatan: tambahkan .dockerignore untuk mengecualikan folder
#   env/, __pycache__/, chroma_db/, .git/ agar tidak ikut ter-copy
COPY . .

# ============================================================
# PORT
# ============================================================

# Memberitahu Docker bahwa container ini akan mendengarkan koneksi di port 7860
# EXPOSE hanya bersifat dokumentasi — tidak secara otomatis membuka port ke host
# Port tetap perlu di-mapping saat menjalankan container:
#   docker run -p 7860:7860 <nama-image>
# Port 7860 adalah standar yang umum dipakai platform AI seperti Hugging Face Spaces
EXPOSE 7860

# ============================================================
# ENTRYPOINT
# ============================================================

# Perintah yang dijalankan saat container pertama kali start
# Menggunakan format JSON array (exec form) — lebih disarankan dari shell form
# karena sinyal shutdown (SIGTERM) langsung diterima oleh proses uvicorn, bukan shell
#
# main:app    → file main.py, variabel FastAPI bernama app