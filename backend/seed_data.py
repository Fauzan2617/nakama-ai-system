import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load API Key dari .env
load_dotenv()

# Konfigurasi Path
DATA_DIR = "./data"
CHROMA_PATH = "./chroma_db"

def ingest_data():
    print("🤖 Memulai proses ingestion untuk Nakama AI...")
    
    # 1. Membaca semua file .txt di folder data
    loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()
    
    if not documents:
        print("❌ Tidak ada file dokumen yang ditemukan di folder 'data/'. Masukkan file .txt terlebih dahulu.")
        return

    print(f"✅ Ditemukan {len(documents)} dokumen. Memecah teks menjadi potongan kecil (chunking)...")
    
    # 2. Memecah teks agar mudah dicerna oleh AI
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    
    print(f"✅ Teks berhasil dipecah menjadi {len(chunks)} bagian. Menghitung embedding...")
    
    # 3. Mengubah teks menjadi vektor (menggunakan model embedding yang sudah kamu perbaiki sebelumnya)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # 4. Menyimpan ke ChromaDB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print("🎉 SUKSES! Data berhasil ditambahkan ke knowledge base Nakama AI.")

if __name__ == "__main__":
    ingest_data()