import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# SWITCH TO LOCAL EMBEDDINGS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

def ingest_documents():
    print("🔄 Starting Knowledge Base Update...")

    # 1. SETUP PATHS
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    db_path = os.path.join(base_dir, "chroma_db")

    # 2. INITIALIZE EMBEDDINGS & DB CONNECTION
    print("   (Using local HuggingFace embeddings)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Connect to the existing DB (or create if missing)
    vector_db = Chroma(
        persist_directory=db_path, 
        embedding_function=embeddings
    )

    # --- WINDOWS SAFE WIPE ---
    # Instead of deleting the folder (which causes crashes), we just delete the data.
    try:
        print("🧹 Clearing old data...")
        # Get all existing IDs in the database
        existing_ids = vector_db.get()['ids']
        if existing_ids:
            vector_db.delete(ids=existing_ids)
            print("   (Old memory wiped successfully)")
        else:
            print("   (Database was already empty)")
    except Exception as e:
        print(f"⚠️ Minor warning during cleanup: {e}")
    # -------------------------

    # 3. SCAN FOR ALL PDFs
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    
    if not pdf_files:
        print("⚠️ No PDF files found in the data directory.")
        return

    all_splits = []
    
    print(f"🔍 Found {len(pdf_files)} PDF(s) to process.")

    # 4. LOOP THROUGH FILES
    for file_path in pdf_files:
        try:
            print(f"📖 Reading: {os.path.basename(file_path)}")
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            # Split text
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            all_splits.extend(splits)
            
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(file_path)}: {e}")

    # 5. ADD NEW CONTENT
    if all_splits:
        print(f"💾 Saving {len(all_splits)} chunks to the Vector Database...")
        vector_db.add_documents(documents=all_splits)
        print("✅ Success! The agent's brain has been FRESHLY updated.")
    else:
        print("⚠️ No content extracted to save.")

if __name__ == "__main__":
    ingest_documents()