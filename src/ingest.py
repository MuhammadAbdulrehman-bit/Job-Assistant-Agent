import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

def ingest_documents():
    # --- 1. SETUP PATHS ---
    # We go 'up one level' (..) because this script is in 'src/' 
    # but 'data/' is in the root folder.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "data", "Confidential.pdf")
    print(file_path)
    db_path = os.path.join(base_dir, "chroma_db")

    print(f"🔍 Looking for file at: {file_path}")

    if not os.path.exists(file_path):
        print("❌ Error: 'Confidential.pdf' not found. Please check the path.")
        return

    # --- 2. READ THE PDF ---
    print("📖 Reading the confidential PDF...")
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # --- 3. CHUNK THE TEXT ---
    print("✂️ Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # --- 4. EMBED & SAVE ---
    print(f"💾 Saving {len(splits)} chunks to the Vector Database at {db_path}...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    # This creates the folder "chroma_db" and fills it with searchable data
    vector_db = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=db_path
    )
    
    print("✅ Success! The agent has now memorized the Internship Policy.")

if __name__ == "__main__":
    ingest_documents()